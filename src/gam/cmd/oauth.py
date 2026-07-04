"""GAM OAuth flows and credential management.

OAuth2 authentication flows and credential
creation/deletion/info/update/refresh/export commands.
"""

import ipaddress
import json
import multiprocessing
import os
import re
import socket
import sys
import datetime
import time
import webbrowser
import wsgiref.simple_server

import arrow
import google.oauth2.credentials
import google_auth_oauthlib.flow

from filelock import FileLock
from urllib.parse import urlparse, parse_qs, urlencode

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import (
    buildGAPIObject,
    callGAPI,
    getClientCredentials,
    getHttpObj,
    getOauth2TxtCredentials,
    shortenURL,
    writeClientCredentials,
)
from gam.util.args import (
    ISOformatTimeStamp,
    UTF8,
    YYYYMMDDTHHMMSSZ_FORMAT,
    checkForExtraneousArguments,
    getArgument,
    getEmailAddress,
    getString,
)
from gam.util.display import (
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityModifierNewValueActionPerformed,
    printBlankLine,
    printEntity,
    printKeyValueList,
)
from gam.util.errors import (
    CLIENT_SECRETS_JSON_REQUIRED_RC,
    Cmd,
    entityActionFailedExit,
    invalidChoiceExit,
    invalidClientSecretsJsonExit,
    invalidOauth2TxtExit,
    unknownArgumentExit,
)
from gam.util.fileio import DEFAULT_FILE_READ_MODE, deleteFile, readFile
from gam.util.output import (
    Ind,
    readStdin,
    stderrErrorMsg,
    systemErrorExit,
    writeStdout,
)
from gam.constants import GAM, INVALID_TOKEN_RC, SYSTEM_ERROR_RC


ERROR_PREFIX = 'ERROR: '


VALIDEMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

def _getValidateLoginHint(login_hint, projectId=None):
  while True:
    if not login_hint:
      if not projectId:
        login_hint = readStdin(Msg.ENTER_GSUITE_ADMIN_EMAIL_ADDRESS).strip()
      else:
        login_hint = readStdin(Msg.ENTER_MANAGE_GCP_PROJECT_EMAIL_ADDRESS.format(projectId)).strip()
    if login_hint.find('@') == -1 and GC.Values[GC.DOMAIN]:
      login_hint = f'{login_hint}@{GC.Values[GC.DOMAIN]}'
    if VALIDEMAIL_PATTERN.match(login_hint):
      return login_hint
    sys.stdout.write(f'{ERROR_PREFIX}Invalid email address: {login_hint}\n')
    login_hint = None

def getOAuthClientIDAndSecret():
  cs_data = readFile(GC.Values[GC.CLIENT_SECRETS_JSON], continueOnError=True, displayError=True)
  if not cs_data:
    invalidClientSecretsJsonExit(Msg.NO_DATA)
  try:
    cs_json = json.loads(cs_data)
    if not cs_json:
      systemErrorExit(CLIENT_SECRETS_JSON_REQUIRED_RC, Msg.NO_CLIENT_ACCESS_CREATE_UPDATE_ALLOWED)
    return (cs_json['installed']['client_id'], cs_json['installed']['client_secret'])
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    invalidClientSecretsJsonExit(str(e))

def getScopesFromUser(scopesList, clientAccess, currentScopes=None):
  OAUTH2_CMDS = ['s', 'u', 'e', 'c']
  oauth2_menu = ''
  numScopes = len(scopesList)
  for a_scope in scopesList:
    oauth2_menu += f"[%%s] %2d)  {a_scope['name']}"
    if a_scope.get('subscopes'):
      oauth2_menu += f' (supports {" and ".join(a_scope["subscopes"])})'
    oauth2_menu += '\n'
  oauth2_menu += '''
Select an unselected scope [ ] by entering a number; yields [*]
For scopes that optionally support readonly, enter a number and an 'r' to grant readonly access; yields [R]
For scopes that optionally support actiononly, enter a number and an 'a' to grant actiononly access; yields [A]
Clear readonly access [R] or actiononly access [A] from a scope by entering a number; yields [*]
Unselect a selected scope [*] by entering a number; yields [ ]
Select all default scopes by entering an 's'; yields [*] for default scopes, [ ] for others
Unselect all scopes by entering a 'u'; yields [ ] for all scopes
Exit without changes/authorization by entering an 'e'
Continue to authorization by entering a 'c'
'''
  menu = oauth2_menu % tuple(range(numScopes))
  selectedScopes = ['*'] * numScopes
  if currentScopes is None and clientAccess:
    lock = FileLock(GM.Globals[GM.OAUTH2_TXT_LOCK], mode=GC.Values[GC.OAUTH2_TXT_LOCK_MODE])
    with lock:
      _, credentials = getOauth2TxtCredentials(exitOnError=False)
      if credentials and credentials.scopes is not None:
        currentScopes = sorted(credentials.scopes)
  if currentScopes is not None:
    if clientAccess:
      i = 0
      for a_scope in scopesList:
        selectedScopes[i] = ' '
        possibleScope = a_scope['scope']
        subScopes = a_scope.get('subscopes', [])
        for currentScope in currentScopes:
          if currentScope == possibleScope:
            selectedScopes[i] = '*'
            break
          if 'readonly' in subScopes:
            if currentScope == possibleScope+'.readonly':
              selectedScopes[i] = 'R'
              break
          if 'actiononly' in subScopes:
            if currentScope == possibleScope+'.action':
              selectedScopes[i] = 'A'
              break
        i += 1
    else:
      i = 0
      for a_scope in scopesList:
        selectedScopes[i] = ' '
        api = a_scope['api']
        possibleScope = a_scope['scope']
        subScopes = a_scope.get('subscopes', [])
        if api in currentScopes:
          if not isinstance(possibleScope, list):
            for scope in currentScopes[api]:
              if scope == possibleScope:
                selectedScopes[i] = '*'
                break
              if 'readonly' in subScopes:
                if (scope == possibleScope+'.readonly') or (scope == a_scope.get('roscope')):
                  selectedScopes[i] = 'R'
                  break
          else:
            for scope in possibleScope:
              if scope not in currentScopes[api]:
                break
            else:
              selectedScopes[i] = '*'
        i += 1
  else:
    i = 0
    for a_scope in scopesList:
      if a_scope.get('offByDefault'):
        selectedScopes[i] = ' '
      elif a_scope.get('roByDefault'):
        selectedScopes[i] = 'R'
      else:
        selectedScopes[i] = '*'
      i += 1
  prompt = f'\nPlease enter 0-{numScopes-1}[a|r] or {"|".join(OAUTH2_CMDS)}: '
  while True:
    os.system(['clear', 'cls'][sys.platform.startswith('win')])
    sys.stdout.write(menu % tuple(selectedScopes))
    while True:
      choice = readStdin(prompt)
      if choice:
        selection = choice.lower()
        if selection.find('r') >= 0:
          mode = 'R'
          selection = selection.replace('r', '')
        elif selection.find('a') >= 0:
          mode = 'A'
          selection = selection.replace('a', '')
        else:
          mode = ' '
        if selection and selection.isdigit():
          selection = int(selection)
        if isinstance(selection, int) and selection < numScopes:
          if mode == 'R':
            if 'readonly' not in scopesList[selection].get('subscopes',[]):
              sys.stdout.write(f'{ERROR_PREFIX}Scope {selection} does not support readonly mode!\n')
              continue
          elif mode == 'A':
            if 'actiononly' not in scopesList[selection].get('subscopes', []):
              sys.stdout.write(f'{ERROR_PREFIX}Scope {selection} does not support actiononly mode!\n')
              continue
          elif selectedScopes[selection] != '*':
            mode = '*'
          else:
            mode = ' '
          selectedScopes[selection] = mode
          break
        if isinstance(selection, str) and selection in OAUTH2_CMDS:
          if selection == 's':
            i = 0
            for a_scope in scopesList:
              selectedScopes[i] = ' ' if a_scope.get('offByDefault', False) else '*'
              i += 1
          elif selection == 'u':
            for i in range(numScopes):
              selectedScopes[i] = ' '
          elif selection == 'e':
            return None
          break
        sys.stdout.write(f'{ERROR_PREFIX}Invalid input "{choice}"\n')
    if selection == 'c':
      if clientAccess:
        numSelectedScopes = 0
        i = 0
        for a_scope in scopesList:
          if selectedScopes[i] == '*':
            if a_scope['scope']:
              numSelectedScopes += 1
          elif selectedScopes[i] != ' ':
            numSelectedScopes += 1
          i += 1
        if numSelectedScopes <= API.NUM_CLIENT_SCOPES_ERROR_LIMIT:
          break
# If number of scopes is > 48 we'll probably get an error
        writeStdout(Msg.NUM_SELECTED_CLIENT_SCOPES.format(numSelectedScopes, API.NUM_CLIENT_SCOPES_ERROR_LIMIT))
        choice = readStdin('\nPlease enter c to continue to authorization or any other key to amend selection: ')
        if choice and choice.lower() == 'c':
          break
      else:
        break
  return selectedScopes

def _localhost_to_ip():
  '''returns IPv4 or IPv6 loopback address which localhost resolves to.
     If localhost does not resolve to valid loopback IP address then returns
     127.0.0.1'''
  # TODO gethostbyname() will only ever return ipv4
  # find a way to support IPv6 here and get preferred IP
  # note that IPv6 may be broken on some systems also :-(
  # for now IPv4 should do.
  local_ip = socket.gethostbyname('localhost')
#  local_ip = socket.getaddrinfo('localhost', None)[0][-1][0] # works with ipv6, makes wsgiref fail
  if not ipaddress.ip_address(local_ip).is_loopback:
    local_ip = '127.0.0.1'
  return local_ip

def _waitForHttpClient(d):
  wsgi_app = google_auth_oauthlib.flow._RedirectWSGIApp(Msg.AUTHENTICATION_FLOW_COMPLETE_CLOSE_BROWSER.format(GAM))
  wsgiref.simple_server.WSGIServer.allow_reuse_address = False
  # Convert hostname to IP since apparently binding to the IP
  # reduces odds of firewall blocking us
  local_ip = _localhost_to_ip()
  for port in range(8080, 8099):
    try:
      local_server = wsgiref.simple_server.make_server(
        local_ip,
        port,
        wsgi_app,
        handler_class=wsgiref.simple_server.WSGIRequestHandler
        )
      break
    except OSError:
      pass
  redirect_uri_format = "http://{}:{}/" if d['trailing_slash'] else "http://{}:{}"
  # provide redirect_uri to main process so it can formulate auth_url
  d['redirect_uri'] = redirect_uri_format.format(*local_server.server_address)
  # wait until main process provides auth_url
  # so we can open it in web browser.
  while 'auth_url' not in d:
    time.sleep(0.1)
  if d['open_browser']:
    webbrowser.open(d['auth_url'], new=1, autoraise=True)
  try:
    local_server.handle_request()
    authorization_response = wsgi_app.last_request_uri.replace("http", "https")
    d['code'] = authorization_response
  except:
    pass
  local_server.server_close()

def _waitForUserInput(d):
  sys.stdin = open(0, DEFAULT_FILE_READ_MODE, encoding=UTF8)
  d['code'] = readStdin(Msg.ENTER_VERIFICATION_CODE_OR_URL)

class _GamOauthFlow(google_auth_oauthlib.flow.InstalledAppFlow):
  def run_dual(self, **kwargs):
    mgr = multiprocessing.Manager()
    d = mgr.dict()
    d['trailing_slash'] = True
    d['open_browser'] = not GC.Values[GC.NO_BROWSER]
    httpClientProcess = multiprocessing.Process(target=_waitForHttpClient, args=(d,))
    userInputProcess = multiprocessing.Process(target=_waitForUserInput, args=(d,))
    httpClientProcess.start()
    # we need to wait until web server starts on avail port
    # so we know redirect_uri to use
    while 'redirect_uri' not in d:
      time.sleep(0.1)
    self.redirect_uri = d['redirect_uri']
    d['auth_url'], _ = super().authorization_url(**kwargs)
    d['auth_url'] = shortenURL(d['auth_url'])
    print(Msg.OAUTH2_GO_TO_LINK_MESSAGE.format(url=d['auth_url']))
    userInputProcess.start()
    userInput = False
    checkHttp = checkUser = True
    alive = 2
    while alive > 0:
      time.sleep(0.1)
      if checkHttp and not httpClientProcess.is_alive():
        if 'code' in d:
          if checkUser:
            userInputProcess.terminate()
          break
        checkHttp = False
        alive -= 1
      if checkUser and not userInputProcess.is_alive():
        userInput = True
        if 'code' in d:
          if checkHttp:
            httpClientProcess.terminate()
          break
        checkUser = False
        alive -= 1
    if 'code' not in d:
      systemErrorExit(SYSTEM_ERROR_RC, Msg.AUTHENTICATION_FLOW_FAILED)
    while True:
      code = d['code']
      if code.startswith('http'):
        parsed_url = urlparse(code)
        parsed_params = parse_qs(parsed_url.query)
        code = parsed_params.get('code', [None])[0]
      try:
        fetch_args = {'code': code}
        if GC.Values[GC.CACERTS_PEM]:
          fetch_args['verify'] = GC.Values[GC.CACERTS_PEM]
        self.fetch_token(**fetch_args)
        break
      except Exception as e:
        if not userInput:
          systemErrorExit(INVALID_TOKEN_RC, str(e))
        stderrErrorMsg(str(e))
        _waitForUserInput(d)
    print(Msg.AUTHENTICATION_FLOW_COMPLETE)
    return self.credentials

class Credentials(google.oauth2.credentials.Credentials):
  """Google OAuth2.0 Credentials with GAM-specific properties and methods."""

  def __init__(self,
               token,
               refresh_token=None,
               id_token=None,
               token_uri=None,
               client_id=None,
               client_secret=None,
               scopes=None,
               quota_project_id=None,
               expiry=None,
               id_token_data=None,
               filename=None):
    """A thread-safe OAuth2.0 credentials object.

    Credentials adds additional utility properties and methods to a
    standard OAuth2.0 credentials object. When used to store credentials on
    disk, it implements a file lock to avoid collision during writes.

    Args:
      token: Optional String, The OAuth 2.0 access token. Can be None if refresh
        information is provided.
      refresh_token: String, The OAuth 2.0 refresh token. If specified,
        credentials can be refreshed.
      id_token: String, The Open ID Connect ID Token.
      token_uri: String, The OAuth 2.0 authorization server's token endpoint
        URI. Must be specified for refresh, can be left as None if the token can
        not be refreshed.
      client_id: String, The OAuth 2.0 client ID. Must be specified for refresh,
        can be left as None if the token can not be refreshed.
      client_secret: String, The OAuth 2.0 client secret. Must be specified for
        refresh, can be left as None if the token can not be refreshed.
      scopes: Sequence[str], The scopes used to obtain authorization.
        This parameter is used by :meth:`has_scopes`. OAuth 2.0 credentials can
          not request additional scopes after authorization. The scopes must be
          derivable from the refresh token if refresh information is provided
          (e.g. The refresh token scopes are a superset of this or contain a
          wild card scope like
            'https://www.googleapis.com/auth/any-api').
      quota_project_id: String, The project ID used for quota and billing. This
        project may be different from the project used to create the
        credentials.
      expiry: datetime.datetime, The time at which the provided token will
        expire.
      id_token_data: Oauth2.0 ID Token data which was previously fetched for
        this access token against the google.oauth2.id_token library.
      filename: String, Path to a file that will be used to store the
        credentials. If provided, a lock file of the same name and a ".lock"
          extension will be created for concurrency controls. Note: New
            credentials are not saved to disk until write() or refresh() are
            called.

    Raises:
      TypeError: If id_token_data is not the required dict type.
    """
    super().__init__(token=token,
                     refresh_token=refresh_token,
                     id_token=id_token,
                     token_uri=token_uri,
                     client_id=client_id,
                     client_secret=client_secret,
                     scopes=scopes,
                     quota_project_id=quota_project_id)

    # Load data not restored by the super class
    self.expiry = expiry
    if id_token_data and not isinstance(id_token_data, dict):
      raise TypeError(f'Expected type id_token_data dict but received {type(id_token_data)}')
    self._id_token_data = id_token_data.copy() if id_token_data else None

    # If a filename is provided, use a lock file to control concurrent access
    # to the resource. If no filename is provided, use a thread lock that has
    # the same interface as FileLock in order to simplify the implementation.
    if filename:
      # Convert relative paths into absolute
      self._filename = os.path.abspath(filename)
    else:
      self._filename = None

  # Use a property to prevent external mutation of the filename.
  @property
  def filename(self):
    return self._filename

  @classmethod
  def from_authorized_user_info_gam(cls, info, filename=None):
    """Generates Credentials from JSON containing authorized user info.

    Args:
      info: Dict, authorized user info in Google format.
      filename: String, the filename used to store these credentials on disk. If
        no filename is provided, the credentials will not be saved to disk.

    Raises:
      ValueError: If missing fields are detected in the info.
    """
    # We need all of these keys
    keys_needed = {'client_id', 'client_secret'}
    # We need 1 or more of these keys
    keys_need_one_of = {'refresh_token', 'auth_token', 'token'}
    missing = keys_needed.difference(info.keys())
    has_one_of = set(info) & keys_need_one_of
    if missing or not has_one_of:
      raise ValueError(
        'Authorized user info was not in the expected format, missing '
        f'fields {", ".join(missing)} and one of {", ".join(keys_need_one_of)}.')

    expiry = info.get('token_expiry')
    if expiry:
      # Convert the raw expiry to datetime
      expiry = arrow.Arrow.strptime(expiry, YYYYMMDDTHHMMSSZ_FORMAT, tzinfo='UTC').naive
    id_token_data = info.get('decoded_id_token')

    # Provide backwards compatibility with field names when loading from JSON.
    # Some field names may be different, depending on when/how the credentials
    # were pickled.
    return cls(token=info.get('token', info.get('auth_token', '')),
               refresh_token=info.get('refresh_token', ''),
               id_token=info.get('id_token_jwt', info.get('id_token')),
               token_uri=info.get('token_uri'),
               client_id=info['client_id'],
               client_secret=info['client_secret'],
               scopes=info.get('scopes'),
               quota_project_id=info.get('quota_project_id'),
               expiry=expiry,
               id_token_data=id_token_data,
               filename=filename)

  @classmethod
  def from_google_oauth2_credentials(cls, credentials, filename=None):
    """Generates Credentials from a google.oauth2.Credentials object."""
    info = json.loads(credentials.to_json())
    # Add properties which are not exported with the native to_json() output.
    info['id_token'] = credentials.id_token
    if credentials.expiry:
      info['token_expiry'] = credentials.expiry.strftime(YYYYMMDDTHHMMSSZ_FORMAT)
    info['quota_project_id'] = credentials.quota_project_id

    return cls.from_authorized_user_info_gam(info, filename=filename)

  @classmethod
  def from_client_secrets(cls,
                          client_id,
                          client_secret,
                          scopes,
                          access_type='offline',
                          login_hint=None,
                          filename=None,
                          open_browser=True):
    """Runs an OAuth Flow from client secrets to generate credentials.

    Args:
      client_id: String, The OAuth2.0 Client ID.
      client_secret: String, The OAuth2.0 Client Secret.
      scopes: Sequence[str], A list of scopes to include in the credentials.
      access_type: String, 'offline' or 'online'.  Indicates whether your
        application can refresh access tokens when the user is not present at
        the browser. Valid parameter values are online, which is the default
        value, and offline.  Set the value to offline if your application needs
        to refresh access tokens when the user is not present at the browser.
        This is the method of refreshing access tokens described later in this
        document. This value instructs the Google authorization server to return
        a refresh token and an access token the first time that your application
        exchanges an authorization code for tokens.
      login_hint: String, The email address that will be displayed on the Google
        login page as a hint for the user to login to the correct account.
      filename: String, the path to a file to use to save the credentials.
      open_browser: Boolean: whether or not GAM should try to open the browser
        automatically.

    Returns:
      Credentials
    """
    client_config = {
      'installed': {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uris': ['http://localhost'],
        'auth_uri': API.GOOGLE_OAUTH2_ENDPOINT,
        'token_uri': API.GOOGLE_OAUTH2_TOKEN_ENDPOINT,
        }
    }

    flow = _GamOauthFlow.from_client_config(client_config,
                                            scopes,
                                            autogenerate_code_verifier=True)
    flow_kwargs = {'access_type': access_type,
                   'open_browser': open_browser}
    if login_hint:
      flow_kwargs['login_hint'] = login_hint
    flow.run_dual(**flow_kwargs)
    return cls.from_google_oauth2_credentials(flow.credentials, filename=filename)

  def to_json(self, strip=None):
    """Creates a JSON representation of a Credentials.

    Args:
        strip: Sequence[str], Optional list of members to exclude from the
          generated JSON.

    Returns:
        str: A JSON representation of this instance, suitable to pass to
             from_json().
    """
    expiry = self.expiry.strftime(YYYYMMDDTHHMMSSZ_FORMAT) if self.expiry else None
    prep = {
      'token': self.token,
      'refresh_token': self.refresh_token,
      'token_uri': self.token_uri,
      'client_id': self.client_id,
      'client_secret': self.client_secret,
      'id_token': self.id_token,
      # Google auth doesn't currently give us scopes back on refresh.
      # 'scopes': sorted(self.scopes),
      'token_expiry': expiry,
      'decoded_id_token': self._id_token_data,
      }

    # Remove empty entries
    prep = {k: v for k, v in prep.items() if v is not None}

    # Remove entries that explicitly need to be removed
    if strip is not None:
      prep = {k: v for k, v in prep.items() if k not in strip}

    return json.dumps(prep, indent=2, sort_keys=True)

def doOAuthRequest(currentScopes, login_hint, verifyScopes=False):
  client_id, client_secret = getOAuthClientIDAndSecret()
  scopesList = API.getClientScopesList(GC.Values[GC.COMMANDDATA_CLIENTACCESS], GC.Values[GC.TODRIVE_CLIENTACCESS])
  if not currentScopes or verifyScopes:
    selectedScopes = getScopesFromUser(scopesList, True, currentScopes)
    if selectedScopes is None:
      return False
    scopes = set(API.REQUIRED_SCOPES)
    i = 0
    for scope in scopesList:
      if selectedScopes[i] == '*':
        if scope['scope']:
          if not isinstance(scope['scope'], list):
            scopes.add(scope['scope'])
          else:
            scopes.update(scope['scope'])
      elif selectedScopes[i] == 'R':
        scopes.add(f'{scope["scope"]}.readonly')
      elif selectedScopes[i] == 'A':
        scopes.add(f'{scope["scope"]}.action')
      i += 1
  else:
    scopes = set(currentScopes+API.REQUIRED_SCOPES)
  if API.STORAGE_READWRITE_SCOPE in scopes:
    scopes.discard(API.STORAGE_READONLY_SCOPE)
  login_hint = _getValidateLoginHint(login_hint)
# Needs to be set so oauthlib doesn't puke when Google changes our scopes
  os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'true'
  credentials = Credentials.from_client_secrets(
    client_id,
    client_secret,
    scopes=list(scopes),
    access_type='offline',
    login_hint=login_hint,
    open_browser=not GC.Values[GC.NO_BROWSER])
  lock = FileLock(GM.Globals[GM.OAUTH2_TXT_LOCK], mode=GC.Values[GC.OAUTH2_TXT_LOCK_MODE])
  with lock:
    writeClientCredentials(credentials, GC.Values[GC.OAUTH2_TXT])
  entityActionPerformed([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]])
  return True

# gam oauth|oauth2 create|request [<EmailAddress>]
# gam oauth|oauth2 create|request [admin <EmailAddress>] [scope|scopes <APIScopeURLList>]
def doOAuthCreate():
  if not Cmd.PeekArgumentPresent(['admin', 'scope', 'scopes']):
    login_hint = getEmailAddress(noUid=True, optional=True)
    scopes = None
    checkForExtraneousArguments()
  else:
    login_hint = None
    scopes = []
    scopesList = API.getClientScopesList(GC.Values[GC.COMMANDDATA_CLIENTACCESS], GC.Values[GC.TODRIVE_CLIENTACCESS])
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'admin':
        login_hint = getEmailAddress(noUid=True)
      elif myarg in {'scope', 'scopes'}:
        for uscope in getString(Cmd.OB_API_SCOPE_URL_LIST).lower().replace(',', ' ').split():
          if uscope in {'openid', 'email', API.USERINFO_EMAIL_SCOPE, 'profile', API.USERINFO_PROFILE_SCOPE}:
            continue
          for scope in scopesList:
            subScopes = scope.get('subscopes', [])
            if ((uscope == scope['scope']) or
                (uscope.endswith('.action') and 'actiononly' in subScopes) or
                (uscope.endswith('.readonly') and 'readonly' in subScopes)):
              scopes.append(uscope)
              break
          else:
            invalidChoiceExit(uscope,
                              API.getClientScopesURLs(GC.Values[GC.COMMANDDATA_CLIENTACCESS], GC.Values[GC.TODRIVE_CLIENTACCESS]),
                              True)
      else:
        unknownArgumentExit()
    if len(scopes) == 0:
      scopes = None
  doOAuthRequest(scopes, login_hint)

def exitIfNoOauth2Txt():
  if not os.path.isfile(GC.Values[GC.OAUTH2_TXT]):
    entityActionNotPerformedWarning([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]], Msg.DOES_NOT_EXIST)
    sys.exit(GM.Globals[GM.SYSEXITRC])

# gam oauth|oauth2 delete|revoke
def doOAuthDelete():
  checkForExtraneousArguments()
  exitIfNoOauth2Txt()
  lock = FileLock(GM.Globals[GM.OAUTH2_TXT_LOCK], mode=GC.Values[GC.OAUTH2_TXT_LOCK_MODE], timeout=10)
  with lock:
    _, credentials = getOauth2TxtCredentials(noScopes=True)
    if not credentials:
      return
    entityType = Ent.OAUTH2_TXT_FILE
    entityName = GC.Values[GC.OAUTH2_TXT]
    sys.stdout.write(f'{Ent.Singular(entityType)}: {entityName}, will be Deleted in 3...')
    sys.stdout.flush()
    time.sleep(1)
    sys.stdout.write('2...')
    sys.stdout.flush()
    time.sleep(1)
    sys.stdout.write('1...')
    sys.stdout.flush()
    time.sleep(1)
    sys.stdout.write('boom!\n')
    sys.stdout.flush()
    httpObj = getHttpObj()
    params = {'token': credentials.refresh_token}
    revoke_uri = f'https://accounts.google.com/o/oauth2/revoke?{urlencode(params)}'
    httpObj.request(revoke_uri, 'GET')
    deleteFile(GC.Values[GC.OAUTH2_TXT], continueOnError=True)
    entityActionPerformed([entityType, entityName])

# gam oauth|oauth2 info|verify [showsecret] [accesstoken <AccessToken> idtoken <IDToken>] [showdetails]
def doOAuthInfo():
  credentials = access_token = id_token = None
  showDetails = showSecret = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'accesstoken':
      access_token = getString(Cmd.OB_ACCESS_TOKEN)
    elif myarg == 'idtoken':
      id_token = getString(Cmd.OB_ID_TOKEN)
    elif myarg == 'showdetails':
      showDetails = True
    elif myarg == 'showsecret':
      showSecret = True
    else:
      unknownArgumentExit()
  exitIfNoOauth2Txt()
  if not access_token and not id_token:
    credentials = getClientCredentials(noScopes=True)
    access_token = credentials.token
    printEntity([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]])
  oa2 = buildGAPIObject(API.OAUTH2)
  try:
    token_info = callGAPI(oa2, 'tokeninfo',
                          throwReasons=[GAPI.INVALID],
                          access_token=access_token, id_token=id_token)
  except GAPI.invalid as e:
    entityActionFailedExit([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]], str(e))
  if 'issued_to' in token_info:
    printKeyValueList(['Client ID', token_info['issued_to']])
  if credentials is not None and showSecret:
    printKeyValueList(['Secret', credentials.client_secret])
  if 'scope' in token_info:
    scopes = token_info['scope'].split(' ')
    printKeyValueList(['Scopes', len(scopes)])
    Ind.Increment()
    for scope in sorted(scopes):
      printKeyValueList([scope])
    Ind.Decrement()
  if 'email' in token_info:
    printKeyValueList(['Google Workspace Admin', f'{token_info["email"]}'])
  if 'expires_in' in token_info:
    printKeyValueList(['Expires', ISOformatTimeStamp(arrow.now(GC.Values[GC.TIMEZONE]).shift(seconds=token_info['expires_in']))])
  if showDetails:
    for k, v in sorted(token_info.items()):
      if k not in  ['email', 'expires_in', 'issued_to', 'scope']:
        printKeyValueList([k, v])
  printBlankLine()

# gam oauth|oauth2 update [<EmailAddress>]
# gam oauth|oauth2 update [admin <EmailAddress>]
def doOAuthUpdate():
  if Cmd.PeekArgumentPresent(['admin']):
    Cmd.Advance()
    login_hint = getEmailAddress(noUid=True)
  else:
    login_hint = getEmailAddress(noUid=True, optional=True)
  checkForExtraneousArguments()
  exitIfNoOauth2Txt()
  lock = FileLock(GM.Globals[GM.OAUTH2_TXT_LOCK], mode=GC.Values[GC.OAUTH2_TXT_LOCK_MODE])
  with lock:
    jsonData = readFile(GC.Values[GC.OAUTH2_TXT], continueOnError=True, displayError=False)
  if not jsonData:
    invalidOauth2TxtExit(Msg.NO_DATA)
  try:
    jsonDict = json.loads(jsonData)
    if 'client_id' in jsonDict:
      if 'scopes' in jsonDict:
        currentScopes = jsonDict['scopes']
      else:
        currentScopes = API.getClientScopesURLs(GC.Values[GC.COMMANDDATA_CLIENTACCESS], GC.Values[GC.TODRIVE_CLIENTACCESS])
    else:
      currentScopes = []
  except (AttributeError, IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    invalidOauth2TxtExit(str(e))
  if not doOAuthRequest(currentScopes, login_hint, verifyScopes=True):
    entityActionNotPerformedWarning([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]], Msg.USER_CANCELLED)
    sys.exit(GM.Globals[GM.SYSEXITRC])

# gam oauth|oauth2 refresh
def doOAuthRefresh():
  checkForExtraneousArguments()
  exitIfNoOauth2Txt()
  getClientCredentials(forceRefresh=True, forceWrite=True, filename=GC.Values[GC.OAUTH2_TXT], refreshOnly=True)
  entityActionPerformed([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]])

# gam oauth|oauth2 export [<FileName>]
def doOAuthExport():
  if Cmd.ArgumentsRemaining():
    filename = getString(Cmd.OB_FILE_NAME)
    checkForExtraneousArguments()
  else:
    filename = GC.Values[GC.OAUTH2_TXT]
  getClientCredentials(forceRefresh=True, forceWrite=True, filename=filename, refreshOnly=True)
  if filename != '-':
    entityModifierNewValueActionPerformed([Ent.OAUTH2_TXT_FILE, GC.Values[GC.OAUTH2_TXT]], Act.MODIFIER_TO, filename)

# Dispatch tables and routing (moved from __init__.py)
# Additional imports for dispatch
from gam.util.args import getChoice
from gam.constants import CMD_ACTION, CMD_FUNCTION, USAGE_ERROR_RC

# Oauth command sub-commands
OAUTH2_SUBCOMMANDS = {
  'create': 			(Act.CREATE, doOAuthCreate),
  'delete': 			(Act.DELETE, doOAuthDelete),
  'export': 			(Act.EXPORT, doOAuthExport),
  'info': 			(Act.INFO, doOAuthInfo),
  'refresh': 			(Act.REFRESH, doOAuthRefresh),
  'update': 			(Act.UPDATE, doOAuthUpdate),
  }

# Oauth sub-command aliases
OAUTH2_SUBCOMMAND_ALIASES = {
  'request':			'create',
  'revoke':			'delete',
  'verify':			'info',
  }

def processOauthCommands():
  CL_subCommand = getChoice(OAUTH2_SUBCOMMANDS, choiceAliases=OAUTH2_SUBCOMMAND_ALIASES)
  Act.Set(OAUTH2_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  if GC.Values[GC.ENABLE_DASA]:
    systemErrorExit(USAGE_ERROR_RC, Msg.COMMAND_NOT_COMPATIBLE_WITH_ENABLE_DASA.format('oauth', CL_subCommand))
  OAUTH2_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION]()

