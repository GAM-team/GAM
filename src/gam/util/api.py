"""GAM API utility functions.

HTTP transport, OAuth credential management, Google API service
construction, and GAPI/GData call wrappers with retry logic.
"""

import http.client
import json
import os
import random
import re
import sqlite3
import ssl
import subprocess
import sys
import time

import arrow
import google.auth
import google.auth._helpers
import google.auth.compute_engine._metadata as gce_metadata
import google.auth.crypt
import google.auth.exceptions
import google.auth.jwt
import google.auth.transport.requests
import google.oauth2.credentials
import google.oauth2.id_token
import google.oauth2.service_account
import google_auth_httplib2
import googleapiclient.discovery
import googleapiclient.errors
import httplib2
from filelock import FileLock
from google.auth.jwt import Credentials as JWTCredentials

try:
  import gdata.apps.audit.service
  import gdata.apps.contacts.service
  import gdata.service
except ImportError:
  pass

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glgdata as GDATA
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg
from gamlib import yubikey


# Constants only used in this module
URL_SHORTENER_ENDPOINT = 'https://gam-shortn.appspot.com/create'
DISCOVERY_URIS = [googleapiclient.discovery.V1_DISCOVERY_URI, googleapiclient.discovery.V2_DISCOVERY_URI]
DEVELOPER_PREVIEW_DISCOVERY_URI = "https://{api}.googleapis.com/$discovery/rest?labels=DEVELOPER_PREVIEW&version={apiVersion}"
_DEFAULT_TOKEN_LIFETIME_SECS = 3600  # 1 hour in seconds


def _getMain():
  return sys.modules['gam']

def _getEnt():
  return sys.modules['gam'].Ent

def _getInd():
  return sys.modules['gam'].Ind


def handleServerError(e):
  m = _getMain()
  errMsg = str(e)
  if 'setting tls' not in errMsg:
    m.systemErrorExit(m.NETWORK_ERROR_RC, errMsg)
  m.stderrErrorMsg(errMsg)
  m.writeStderr(Msg.DISABLE_TLS_MIN_MAX)
  m.systemErrorExit(m.NETWORK_ERROR_RC, None)

def getHttpObj(cache=None, timeout=None, override_min_tls=None, override_max_tls=None):
  tls_minimum_version = override_min_tls if override_min_tls else GC.Values[GC.TLS_MIN_VERSION] if GC.Values[GC.TLS_MIN_VERSION] else None
  tls_maximum_version = override_max_tls if override_max_tls else GC.Values[GC.TLS_MAX_VERSION] if GC.Values[GC.TLS_MAX_VERSION] else None
  httpObj = httplib2.Http(cache=cache,
                          timeout=timeout,
                          ca_certs=GC.Values[GC.CACERTS_PEM],
                          disable_ssl_certificate_validation=GC.Values[GC.NO_VERIFY_SSL],
                          tls_maximum_version=tls_maximum_version,
                          tls_minimum_version=tls_minimum_version)
  httpObj.redirect_codes = set(httpObj.redirect_codes) - {308}
  return httpObj

def _force_user_agent(user_agent):
  """Creates a decorator which can force a user agent in HTTP headers."""

  def decorator(request_method):
    """Wraps a request method to insert a user-agent in HTTP headers."""

    def wrapped_request_method(*args, **kwargs):
      """Modifies HTTP headers to include a specified user-agent."""
      if kwargs.get('headers') is not None:
        if kwargs['headers'].get('user-agent'):
          if user_agent not in kwargs['headers']['user-agent']:
            # Save the existing user-agent header and tack on our own.
            kwargs['headers']['user-agent'] = f'{user_agent} {kwargs["headers"]["user-agent"]}'
        else:
          kwargs['headers']['user-agent'] = user_agent
      else:
        kwargs['headers'] = {'user-agent': user_agent}
      return request_method(*args, **kwargs)

    return wrapped_request_method

  return decorator

def _lazy_force_user_agent(request_method):
  """Wraps a request method to lazily insert GAM_USER_AGENT at call time."""
  def wrapped_request_method(*args, **kwargs):
    user_agent = _getMain().GAM_USER_AGENT
    if kwargs.get('headers') is not None:
      if kwargs['headers'].get('user-agent'):
        if user_agent not in kwargs['headers']['user-agent']:
          kwargs['headers']['user-agent'] = f'{user_agent} {kwargs["headers"]["user-agent"]}'
      else:
        kwargs['headers']['user-agent'] = user_agent
    else:
      kwargs['headers'] = {'user-agent': user_agent}
    return request_method(*args, **kwargs)
  return wrapped_request_method

class transportAgentRequest(google_auth_httplib2.Request):
  """A Request which forces a user agent."""

  @_lazy_force_user_agent
  def __call__(self, *args, **kwargs): #pylint: disable=arguments-differ
    """Inserts the GAM user-agent header in requests."""
    return super().__call__(*args, **kwargs)

class transportAuthorizedHttp(google_auth_httplib2.AuthorizedHttp):
  """An AuthorizedHttp which forces a user agent during requests."""

  @_lazy_force_user_agent
  def request(self, *args, **kwargs): #pylint: disable=arguments-differ
    """Inserts the GAM user-agent header in requests."""
    return super().request(*args, **kwargs)


def transportCreateRequest(httpObj=None):
  """Creates a uniform Request object with a default http, if not provided.

  Args:
    httpObj: Optional httplib2.Http compatible object to be used with the request.
      If not provided, a default HTTP will be used.

  Returns:
    Request: A google_auth_httplib2.Request compatible Request.
  """
  if not httpObj:
    httpObj = getHttpObj()
  return transportAgentRequest(httpObj)

def doGAMCheckForUpdates(forceCheck):
  m = _getMain()
  Ind = _getInd()
  def _gamLatestVersionNotAvailable():
    if forceCheck:
      m.systemErrorExit(m.NETWORK_ERROR_RC, Msg.GAM_LATEST_VERSION_NOT_AVAILABLE)

  try:
    _, c = getHttpObj(timeout=10).request(m.GAM_LATEST_RELEASE, 'GET', headers={'Accept': 'application/vnd.github.v3.text+json'})
    try:
      release_data = json.loads(c)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
      _gamLatestVersionNotAvailable()
      return
    if not isinstance(release_data, dict) or 'tag_name' not in release_data:
      _gamLatestVersionNotAvailable()
      return
    current_version = m.__version__
    latest_version = release_data['tag_name']
    if latest_version[0].lower() == 'v':
      latest_version = latest_version[1:]
      m.printKeyValueList(['Version Check', None])
      Ind.Increment()
      m.printKeyValueList(['Current', current_version])
      m.printKeyValueList([' Latest', latest_version])
      Ind.Decrement()
    if forceCheck < 0:
      m.setSysExitRC(1 if latest_version > current_version else 0)
      return
  except (httplib2.HttpLib2Error, httplib2.ServerNotFoundError,
          google.auth.exceptions.TransportError,
          RuntimeError, ConnectionError, OSError) as e:
    if forceCheck:
      handleServerError(e)

class signjwtJWTCredentials(google.auth.jwt.Credentials):
  ''' Class used for DASA '''
  def _make_jwt(self):
    now = arrow.utcnow()
    expiry = now.shift(seconds=self._token_lifetime)
    payload = {
      "iat": now.int_timestamp,
      "exp": expiry.int_timestamp,
      "iss": self._issuer,
      "sub": self._subject,
    }
    if self._audience:
      payload["aud"] = self._audience
    payload.update(self._additional_claims)
    jwt = self._signer.sign(payload)
    return jwt, expiry.naive

class signjwtCredentials(google.oauth2.service_account.Credentials):
  ''' Class used for DwD '''

  def _make_authorization_grant_assertion(self):
    now = arrow.utcnow()
    expiry = now.shift(seconds=_DEFAULT_TOKEN_LIFETIME_SECS)
    payload = {
      "iat": now.int_timestamp,
      "exp": expiry.int_timestamp,
      "iss": self._service_account_email,
      "aud": API.GOOGLE_OAUTH2_TOKEN_ENDPOINT,
      "scope": google.auth._helpers.scopes_to_string(self._scopes or ()),
    }
    payload.update(self._additional_claims)
    # The subject can be a user email for domain-wide delegation.
    if self._subject:
      payload.setdefault("sub", self._subject)
    token = self._signer(payload)
    return token

def get_adc_request():
  request = google.auth.transport.requests.Request()
  if GM.Globals[GM.IS_ON_GCE]:
    return request
  if gce_metadata.is_on_gce(request):
    GM.Globals[GM.IS_ON_GCE] = True
    return request
  return transportCreateRequest()

class signjwtSignJwt(google.auth.crypt.Signer):
  ''' Signer class for SignJWT '''
  def __init__(self, service_account_info):
    self.service_account_email = service_account_info['client_email']
    self.name = f'projects/-/serviceAccounts/{self.service_account_email}'
    self._key_id = None

  @property  # type: ignore
  def key_id(self):
    return self._key_id

  def sign(self, message):
    ''' Call IAM Credentials SignJWT API to get our signed JWT '''
    m = _getMain()
    request = get_adc_request()
    try:
      credentials, _ = google.auth.default(scopes=[API.IAM_SCOPE],
                                           request=request)
    except (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError) as e:
      m.systemErrorExit(m.API_ACCESS_DENIED_RC, str(e))
    httpObj = transportAuthorizedHttp(credentials, http=getHttpObj())
    # refresh here so we can use the proper request from above
    httpObj.credentials.refresh(request)
    iamc = getService(API.IAM_CREDENTIALS, httpObj)
    response = callGAPI(iamc.projects().serviceAccounts(), 'signJwt',
                        name=self.name, body={'payload': json.dumps(message)})
    signed_jwt = response.get('signedJwt')
    return signed_jwt

def handleOAuthTokenError(e, softErrors, displayError=False, i=0, count=0):
  m = _getMain()
  Ent = _getEnt()
  errMsg = str(e).replace('.', '')
  if ((errMsg in API.OAUTH2_TOKEN_ERRORS) or
      errMsg.startswith('Invalid response') or
      errMsg.startswith('invalid_request: Invalid impersonation &quot;sub&quot; field')):
    if not GM.Globals[GM.CURRENT_SVCACCT_USER]:
      m.ClientAPIAccessDeniedExit()
    # 403 Forbidden, API disabled, user not enabled
    # 400 Bad Request, user not defined
    if softErrors:
      m.entityActionFailedWarning([Ent.USER, GM.Globals[GM.CURRENT_SVCACCT_USER], Ent.USER, None], errMsg, i, count)
      return None
    m.systemErrorExit(m.SERVICE_NOT_APPLICABLE_RC, Msg.SERVICE_NOT_APPLICABLE_THIS_ADDRESS.format(GM.Globals[GM.CURRENT_SVCACCT_USER]))
  if errMsg in API.OAUTH2_UNAUTHORIZED_ERRORS:
    if not GM.Globals[GM.CURRENT_SVCACCT_USER]:
      m.ClientAPIAccessDeniedExit()
    # 401 Unauthorized, API disabled, user enabled
    if softErrors:
      if displayError:
        apiOrScopes = API.getAPIName(GM.Globals[GM.CURRENT_SVCACCT_API]) if GM.Globals[GM.CURRENT_SVCACCT_API] else ','.join(sorted(GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES]))
        m.userServiceNotEnabledWarning(GM.Globals[GM.CURRENT_SVCACCT_USER], apiOrScopes, i, count)
      return None
    m.SvcAcctAPIAccessDeniedExit()
  if errMsg in API.REFRESH_PERM_ERRORS:
    if softErrors:
      return None
    if not GM.Globals[GM.CURRENT_SVCACCT_USER]:
      m.expiredRevokedOauth2TxtExit()
  m.stderrErrorMsg(f'Authentication Token Error - {errMsg}')
  m.APIAccessDeniedExit()

def getOauth2TxtCredentials(exitOnError=True, api=None, noDASA=False, refreshOnly=False, noScopes=False):
  m = _getMain()
  if not noDASA and GC.Values[GC.ENABLE_DASA]:
    jsonData = m.readFile(GC.Values[GC.OAUTH2SERVICE_JSON], continueOnError=True, displayError=False)
    if jsonData:
      try:
        if api in API.APIS_NEEDING_ACCESS_TOKEN:
          return (False, getSvcAcctCredentials(API.APIS_NEEDING_ACCESS_TOKEN[api], userEmail=None, forceOauth=True))
        jsonDict = json.loads(jsonData)
        api, _, _ = API.getVersion(api)
        audience = f'https://{api}.googleapis.com/'
        key_type = jsonDict.get('key_type', 'default')
        if key_type == 'default':
          return (True, JWTCredentials.from_service_account_info(jsonDict, audience=audience))
        if key_type == 'yubikey':
          yksigner = yubikey.YubiKey(jsonDict)
          return (True, JWTCredentials._from_signer_and_info(yksigner, jsonDict, audience=audience))
        if key_type == 'signjwt':
          sjsigner = signjwtSignJwt(jsonDict)
          return (True, signjwtJWTCredentials._from_signer_and_info(sjsigner, jsonDict, audience=audience))
      except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
        m.invalidOauth2serviceJsonExit(str(e))
    m.invalidOauth2serviceJsonExit(Msg.NO_DATA)
  jsonData = m.readFile(GC.Values[GC.OAUTH2_TXT], continueOnError=True, displayError=False)
  if jsonData:
    try:
      jsonDict = json.loads(jsonData)
      if noScopes:
        jsonDict['scopes'] = []
      if 'client_id' in jsonDict:
        if not refreshOnly:
          if set(jsonDict.get('scopes', API.REQUIRED_SCOPES)) == API.REQUIRED_SCOPES_SET:
            if exitOnError:
              m.systemErrorExit(m.OAUTH2_TXT_REQUIRED_RC, Msg.NO_CLIENT_ACCESS_ALLOWED)
            return (False, None)
        else:
          GM.Globals[GM.CREDENTIALS_SCOPES] = set(jsonDict.pop('scopes', API.REQUIRED_SCOPES))
        token_expiry = jsonDict.get('token_expiry', m.REFRESH_EXPIRY)
        if GC.Values[GC.TRUNCATE_CLIENT_ID]:
          # chop off .apps.googleusercontent.com suffix as it's not needed and we need to keep things short for the Auth URL.
          jsonDict['client_id'] = re.sub(r'\.apps\.googleusercontent\.com$', '', jsonDict['client_id'])
        creds = google.oauth2.credentials.Credentials.from_authorized_user_info(jsonDict)
        if 'id_token_jwt' not in jsonDict:
          creds.token = jsonDict['token']
          creds._id_token = jsonDict['id_token']
          GM.Globals[GM.DECODED_ID_TOKEN] = jsonDict['decoded_id_token']
        else:
          creds.token = jsonDict['access_token']
          creds._id_token = jsonDict['id_token_jwt']
          GM.Globals[GM.DECODED_ID_TOKEN] = jsonDict['id_token']
        creds.expiry = arrow.Arrow.strptime(token_expiry, m.YYYYMMDDTHHMMSSZ_FORMAT, tzinfo='UTC').naive
        return (not noScopes, creds)
      if jsonDict and exitOnError:
        m.invalidOauth2TxtExit(Msg.INVALID)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      if exitOnError:
        m.invalidOauth2TxtExit(str(e))
  if exitOnError:
    m.systemErrorExit(m.OAUTH2_TXT_REQUIRED_RC, Msg.NO_CLIENT_ACCESS_ALLOWED)
  return (False, None)

def _getValueFromOAuth(field, credentials=None):
  m = _getMain()
  if not GM.Globals[GM.DECODED_ID_TOKEN]:
    request = transportCreateRequest()
    if credentials is None:
      credentials = getClientCredentials(refreshOnly=True)
    elif credentials.expired:
      credentials.refresh(request)
    try:
      GM.Globals[GM.DECODED_ID_TOKEN] = google.oauth2.id_token.verify_oauth2_token(credentials.id_token, request,
                                                                                    clock_skew_in_seconds=GC.Values[GC.CLOCK_SKEW_IN_SECONDS])
    except ValueError as e:
      if 'Token used too early' in str(e):
        m.stderrErrorMsg(Msg.PLEASE_CORRECT_YOUR_SYSTEM_TIME)
      m.systemErrorExit(m.SYSTEM_ERROR_RC, str(e))
  return GM.Globals[GM.DECODED_ID_TOKEN].get(field, m.UNKNOWN)

def _getAdminEmail():
  if GC.Values[GC.ADMIN_EMAIL]:
    return GC.Values[GC.ADMIN_EMAIL]
  return _getValueFromOAuth('email')

def writeClientCredentials(creds, filename):
  m = _getMain()
  creds_data = {
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'id_token': creds.id_token,
    'refresh_token': creds.refresh_token,
    'scopes': sorted(creds.scopes or GM.Globals[GM.CREDENTIALS_SCOPES]),
    'token': creds.token,
    'token_expiry': creds.expiry.strftime(m.YYYYMMDDTHHMMSSZ_FORMAT),
    'token_uri': creds.token_uri,
    }
  expected_iss = ['https://accounts.google.com', 'accounts.google.com']
  if _getValueFromOAuth('iss', creds) not in expected_iss:
    m.systemErrorExit(m.OAUTH2_TXT_REQUIRED_RC, f'Wrong OAuth 2.0 credentials issuer. Got {_getValueFromOAuth("iss", creds)} expected one of {", ".join(expected_iss)}')
  request = transportCreateRequest()
  try:
    creds_data['decoded_id_token'] = google.oauth2.id_token.verify_oauth2_token(creds.id_token, request,
                                                                                 clock_skew_in_seconds=GC.Values[GC.CLOCK_SKEW_IN_SECONDS])
  except ValueError as e:
    if 'Token used too early' in str(e):
      m.stderrErrorMsg(Msg.PLEASE_CORRECT_YOUR_SYSTEM_TIME)
    m.systemErrorExit(m.SYSTEM_ERROR_RC, str(e))
  GM.Globals[GM.DECODED_ID_TOKEN] = creds_data['decoded_id_token']
  if filename != '-':
    m.writeFile(filename, json.dumps(creds_data, indent=2, sort_keys=True)+'\n')
  else:
    m.writeStdout(json.dumps(creds_data, ensure_ascii=False, indent=2, sort_keys=True)+'\n')

def shortenURL(long_url):
  m = _getMain()
  if GC.Values[GC.NO_SHORT_URLS]:
    return long_url
  httpObj = getHttpObj(timeout=10)
  try:
    payload = json.dumps({'long_url': long_url})
    resp, content = httpObj.request(URL_SHORTENER_ENDPOINT, 'POST',
                                    payload,
                                    headers={'Content-Type': 'application/json',
                                             'User-Agent': m.GAM_USER_AGENT})
  except:
    return long_url
  if resp.status != 200:
    return long_url
  try:
    if isinstance(content, bytes):
      content = content.decode()
    return json.loads(content).get('short_url', long_url)
  except:
    return long_url

def runSqliteQuery(db_file, query):
  conn = sqlite3.connect(db_file)
  curr = conn.cursor()
  curr.execute(query)
  return curr.fetchone()[0]

def refreshCredentialsWithReauth(credentials):
  m = _getMain()
  def gcloudError():
    m.writeStderr(f'Failed to run gcloud as {admin_email}. Please make sure it\'s setup')
    e = Msg.REAUTHENTICATION_IS_NEEDED
    handleOAuthTokenError(e, False)

  m.writeStderr(Msg.CALLING_GCLOUD_FOR_REAUTH)
  if 'termios' in sys.modules:
    import termios
    old_settings = termios.tcgetattr(sys.stdin)
  admin_email = _getAdminEmail()
  # First makes sure gcloud has a valid access token and thus
  # should also have a valid RAPT token
  try:
    devnull = open(os.devnull, 'w', encoding=m.UTF8)
    subprocess.run(['gcloud',
                    'auth',
                    'print-identity-token',
                    '--no-user-output-enabled'],
                   stderr=devnull,
                   check=False)
    devnull.close()
    # now determine gcloud's config path and token file
    gcloud_path_result = subprocess.run(['gcloud',
                                         'info',
                                         '--format=value(config.paths.global_config_dir)'],
            capture_output=True, check=False)
  except KeyboardInterrupt as e:
    # avoids loss of terminal echo on *nix
    if 'termios' in sys.modules:
      import termios
      termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    m.printBlankLine()
    raise KeyboardInterrupt from e
  token_path = gcloud_path_result.stdout.decode().strip()
  if not token_path:
    gcloudError()
  token_file = f'{token_path}/access_tokens.db'
  try:
    credentials._rapt_token = runSqliteQuery(token_file,
            f'SELECT rapt_token FROM access_tokens WHERE account_id = "{admin_email}"')
  except TypeError:
    gcloudError()
  if not credentials._rapt_token:
    m.systemErrorExit(m.SYSTEM_ERROR_RC,
            'Failed to retrieve reauth token from gcloud. You may need to wait until gcloud is also prompted for reauth.')

def getClientCredentials(forceRefresh=False, forceWrite=False, filename=None, api=None, noDASA=False, refreshOnly=False, noScopes=False):
  """Gets OAuth2 credentials which are guaranteed to be fresh and valid.
     Locks during read and possible write so that only one process will
     attempt refresh/write when running in parallel. """
  m = _getMain()
  lock = FileLock(GM.Globals[GM.OAUTH2_TXT_LOCK], mode=GC.Values[GC.OAUTH2_TXT_LOCK_MODE])
  with lock:
    writeCreds, credentials = getOauth2TxtCredentials(api=api, noDASA=noDASA, refreshOnly=refreshOnly, noScopes=noScopes)
    if not credentials:
      m.invalidOauth2TxtExit('')
    if credentials.expired or forceRefresh:
      triesLimit = 3
      for n in range(1, triesLimit+1):
        try:
          credentials.refresh(transportCreateRequest())
          if writeCreds or forceWrite:
            writeClientCredentials(credentials, filename or GC.Values[GC.OAUTH2_TXT])
          break
        except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
          if n != triesLimit:
            waitOnFailure(n, triesLimit, m.NETWORK_ERROR_RC, str(e))
            continue
          handleServerError(e)
        except google.auth.exceptions.RefreshError as e:
          if isinstance(e.args, tuple):
            e = e.args[0]
          if 'Reauthentication is needed' in str(e):
            if GC.Values[GC.ENABLE_GCLOUD_REAUTH]:
              refreshCredentialsWithReauth(credentials)
              continue
            e = Msg.REAUTHENTICATION_IS_NEEDED
          handleOAuthTokenError(e, False)
  return credentials

def waitOnFailure(n, triesLimit, error_code, error_message):
  m = _getMain()
  delta = min(2 ** n, 60)+float(random.randint(1, 1000))/1000
  if n > 3:
    m.writeStderr(f'Temporary error: {error_code} - {error_message}, Backing off: {int(delta)} seconds, Retry: {n}/{triesLimit}\n')
    m.flushStderr()
  time.sleep(delta)
  if GC.Values[GC.SHOW_API_CALLS_RETRY_DATA]:
    m.incrAPICallsRetryData(error_message, delta)

def clearServiceCache(service):
  if hasattr(service._http, 'http') and hasattr(service._http.http, 'cache'):
    if service._http.http.cache is None:
      return False
    service._http.http.cache = None
    return True
  if hasattr(service._http, 'cache'):
    if service._http.cache is None:
      return False
    service._http.cache = None
    return True
  return False

# Used for API.CLOUDRESOURCEMANAGER, API.SERVICEUSAGE, API.IAM
def getAPIService(api, httpObj):
  api, version, v2discovery = API.getVersion(api)
  return googleapiclient.discovery.build(api, version, http=httpObj, cache_discovery=False,
                                         discoveryServiceUrl=DISCOVERY_URIS[v2discovery], static_discovery=False)

def getService(api, httpObj):
  m = _getMain()
  hasLocalJSON = API.hasLocalJSON(api)
  api, version, v2discovery = API.getVersion(api)
  if api in GM.Globals[GM.CURRENT_API_SERVICES] and version in GM.Globals[GM.CURRENT_API_SERVICES][api]:
    service = googleapiclient.discovery.build_from_document(GM.Globals[GM.CURRENT_API_SERVICES][api][version], http=httpObj)
    if GM.Globals[GM.CACHE_DISCOVERY_ONLY]:
      clearServiceCache(service)
    return service
  if not hasLocalJSON:
    triesLimit = 3
    for n in range(1, triesLimit+1):
      try:
        if api not in GM.Globals[GM.DEVELOPER_PREVIEW_APIS] or not GC.Values[GC.DEVELOPER_PREVIEW_API_KEY]:
          discoveryServiceUrl = DISCOVERY_URIS[v2discovery]
          developerKey = ''
        else:
          discoveryServiceUrl = DEVELOPER_PREVIEW_DISCOVERY_URI
          developerKey = GC.Values[GC.DEVELOPER_PREVIEW_API_KEY]
        service = googleapiclient.discovery.build(api, version, http=httpObj, cache_discovery=False,
                                                  discoveryServiceUrl=discoveryServiceUrl, developerKey=developerKey, static_discovery=False)
        GM.Globals[GM.CURRENT_API_SERVICES].setdefault(api, {})
        GM.Globals[GM.CURRENT_API_SERVICES][api][version] = service._rootDesc.copy()
        if GM.Globals[GM.CACHE_DISCOVERY_ONLY]:
          clearServiceCache(service)
        return service
      except googleapiclient.errors.UnknownApiNameOrVersion as e:
        m.systemErrorExit(m.GOOGLE_API_ERROR_RC, Msg.UNKNOWN_API_OR_VERSION.format(str(e), m.__author__))
      except (googleapiclient.errors.InvalidJsonError, KeyError, ValueError) as e:
        if n != triesLimit:
          waitOnFailure(n, triesLimit, m.INVALID_JSON_RC, str(e))
          continue
        m.systemErrorExit(m.INVALID_JSON_RC, str(e))
      except (http.client.ResponseNotReady, OSError, googleapiclient.errors.HttpError) as e:
        errMsg = f'Connection error: {str(e) or repr(e)}'
        if n != triesLimit:
          waitOnFailure(n, triesLimit, m.SOCKET_ERROR_RC, errMsg)
          continue
        m.systemErrorExit(m.SOCKET_ERROR_RC, errMsg)
      except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
        if n != triesLimit:
          httpObj.connections = {}
          waitOnFailure(n, triesLimit, m.NETWORK_ERROR_RC, str(e))
          continue
        handleServerError(e)
  disc_file, discovery = readDiscoveryFile(f'{api}-{version}')
  try:
    service = googleapiclient.discovery.build_from_document(discovery, http=httpObj)
    GM.Globals[GM.CURRENT_API_SERVICES].setdefault(api, {})
    GM.Globals[GM.CURRENT_API_SERVICES][api][version] = service._rootDesc.copy()
    if GM.Globals[GM.CACHE_DISCOVERY_ONLY]:
      clearServiceCache(service)
    return service
  except (googleapiclient.errors.InvalidJsonError, KeyError, ValueError) as e:
    m.invalidDiscoveryJsonExit(disc_file, str(e))
  except IOError as e:
    m.systemErrorExit(m.FILE_ERROR_RC, str(e))

def defaultSvcAcctScopes():
  scopesList = API.getSvcAcctScopesList(GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY], False)
  saScopes = {}
  for scope in scopesList:
    if not scope.get('offByDefault'):
      saScopes.setdefault(scope['api'], [])
      if not isinstance(scope['scope'], list):
        saScopes[scope['api']].append(scope['scope'])
      else:
        saScopes[scope['api']].extend(scope['scope'])
  saScopes[API.DRIVE2] = saScopes[API.DRIVE3]
  return saScopes

def _getSvcAcctData():
  m = _getMain()
  if not GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
    jsonData = m.readFile(GC.Values[GC.OAUTH2SERVICE_JSON], continueOnError=True, displayError=True)
    if not jsonData:
      m.invalidOauth2serviceJsonExit(Msg.NO_DATA)
    try:
      GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = json.loads(jsonData)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      m.invalidOauth2serviceJsonExit(str(e))
    if not GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
      m.systemErrorExit(m.OAUTH2SERVICE_JSON_REQUIRED_RC, Msg.NO_SVCACCT_ACCESS_ALLOWED)
    requiredFields = ['client_email', 'client_id', 'project_id', 'token_uri']
    key_type = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].get('key_type', 'default')
    if key_type == 'default':
      requiredFields.extend(['private_key', 'private_key_id'])
    missingFields = []
    for field in requiredFields:
      if field not in GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
        missingFields.append(field)
    if missingFields:
      m.invalidOauth2serviceJsonExit(Msg.MISSING_FIELDS.format(','.join(missingFields)))
# Some old oauth2service.json files have: 'https://accounts.google.com/o/oauth2/auth' which no longer works
    if GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['token_uri'] == 'https://accounts.google.com/o/oauth2/auth':
      GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['token_uri'] = API.GOOGLE_OAUTH2_TOKEN_ENDPOINT
    if API.OAUTH2SA_SCOPES not in GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
      GM.Globals[GM.SVCACCT_SCOPES_DEFINED] = False
      GM.Globals[GM.SVCACCT_SCOPES] = defaultSvcAcctScopes()
    else:
      GM.Globals[GM.SVCACCT_SCOPES_DEFINED] = True
      GM.Globals[GM.SVCACCT_SCOPES] = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].pop(API.OAUTH2SA_SCOPES)

def getSvcAcctCredentials(scopesOrAPI, userEmail, softErrors=False, forceOauth=False):
  m = _getMain()
  _getSvcAcctData()
  if isinstance(scopesOrAPI, str):
    GM.Globals[GM.CURRENT_SVCACCT_API] = scopesOrAPI
    if scopesOrAPI not in API.JWT_APIS:
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES] = GM.Globals[GM.SVCACCT_SCOPES].get(scopesOrAPI, [])
    else:
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES] = API.JWT_APIS[scopesOrAPI]
    if scopesOrAPI != API.CHAT_EVENTS and not GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES]:
      if softErrors:
        return None
      m.SvcAcctAPIAccessDeniedExit()
    if scopesOrAPI in {API.PEOPLE, API.PEOPLE_DIRECTORY, API.PEOPLE_OTHERCONTACTS}:
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES].append(API.USERINFO_PROFILE_SCOPE)
      if scopesOrAPI in {API.PEOPLE_OTHERCONTACTS}:
        GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES].append(API.PEOPLE_SCOPE)
    elif scopesOrAPI == API.CHAT_EVENTS:
      for chatAPI in [API.CHAT_SPACES, API.CHAT_MEMBERSHIPS, API.CHAT_MESSAGES]:
        GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES].extend(GM.Globals[GM.SVCACCT_SCOPES].get(chatAPI, []))
  else:
    GM.Globals[GM.CURRENT_SVCACCT_API] = ''
    GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES] = scopesOrAPI
  key_type = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].get('key_type', 'default')
  if not GM.Globals[GM.CURRENT_SVCACCT_API] or scopesOrAPI not in API.JWT_APIS or forceOauth:
    try:
      if key_type == 'default':
        credentials = google.oauth2.service_account.Credentials.from_service_account_info(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
      elif key_type == 'yubikey':
        yksigner = yubikey.YubiKey(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
        credentials = google.oauth2.service_account.Credentials._from_signer_and_info(yksigner,
                                                                                       GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
      elif key_type == 'signjwt':
        sjsigner = signjwtSignJwt(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
        credentials = signjwtCredentials._from_signer_and_info(sjsigner.sign,
                                                               GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
    except (ValueError, IndexError, KeyError) as e:
      if softErrors:
        return None
      m.invalidOauth2serviceJsonExit(str(e))
    credentials = credentials.with_scopes(GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES])
  else:
    audience = f'https://{scopesOrAPI}.googleapis.com/'
    try:
      if key_type == 'default':
        credentials = JWTCredentials.from_service_account_info(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA],
                                                               audience=audience)
      elif key_type == 'yubikey':
        yksigner = yubikey.YubiKey(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
        credentials = JWTCredentials._from_signer_and_info(yksigner,
                                                           GM.Globals[GM.OAUTH2SERVICE_JSON_DATA],
                                                           audience=audience)
      elif key_type == 'signjwt':
        sjsigner = signjwtSignJwt(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
        credentials = signjwtJWTCredentials._from_signer_and_info(sjsigner,
                                                                   GM.Globals[GM.OAUTH2SERVICE_JSON_DATA],
                                                                   audience=audience)
      credentials.project_id = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id']
    except (ValueError, IndexError, KeyError) as e:
      if softErrors:
        return None
      m.invalidOauth2serviceJsonExit(str(e))
  GM.Globals[GM.CURRENT_SVCACCT_USER] = userEmail
  if userEmail:
    credentials = credentials.with_subject(userEmail)
  GM.Globals[GM.ADMIN] = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']
  GM.Globals[GM.OAUTH2SERVICE_CLIENT_ID] = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_id']
  return credentials

def getGDataOAuthToken(gdataObj, credentials=None):
  m = _getMain()
  if not credentials:
    credentials = getClientCredentials(refreshOnly=True)
  try:
    credentials.refresh(transportCreateRequest())
  except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
    handleServerError(e)
  except google.auth.exceptions.RefreshError as e:
    if isinstance(e.args, tuple):
      e = e.args[0]
    handleOAuthTokenError(e, False)
  gdataObj.additional_headers['Authorization'] = f'Bearer {credentials.token}'
  if not GC.Values[GC.DOMAIN]:
    GC.Values[GC.DOMAIN] = GM.Globals[GM.DECODED_ID_TOKEN].get('hd', 'UNKNOWN').lower()
  if not GC.Values[GC.CUSTOMER_ID]:
    GC.Values[GC.CUSTOMER_ID] = GC.MY_CUSTOMER
  GM.Globals[GM.ADMIN] = GM.Globals[GM.DECODED_ID_TOKEN].get('email', 'UNKNOWN').lower()
  GM.Globals[GM.OAUTH2_CLIENT_ID] = credentials.client_id
  gdataObj.domain = GC.Values[GC.DOMAIN]
  gdataObj.source = m.GAM_USER_AGENT
  return True

def checkGDataError(e, service):
  m = _getMain()
  error = e.args
  reason = error[0].get('reason', '')
  body = error[0].get('body', '').decode(m.UTF8)
  # First check for errors that need special handling
  if reason in ['Token invalid - Invalid token: Stateless token expired', 'Token invalid - Invalid token: Token not found', 'gone']:
    keep_domain = service.domain
    getGDataOAuthToken(service)
    service.domain = keep_domain
    return (GDATA.TOKEN_EXPIRED, reason)
  error_code = getattr(e, 'error_code', 600)
  if GC.Values[GC.DEBUG_LEVEL] > 0:
    m.writeStdout(f'{m.ERROR_PREFIX} {error_code}: {reason}, {body}\n')
  if error_code == 600:
    if (body.startswith('Quota exceeded for the current request') or
        body.startswith('Quota exceeded for quota metric') or
        body.startswith('Request rate higher than configured')):
      return (GDATA.QUOTA_EXCEEDED, body)
    if (body.startswith('Photo delete failed') or
        body.startswith('Upload photo failed') or
        body.startswith('Photo query failed')):
      return (GDATA.NOT_FOUND, body)
    if body.startswith(GDATA.API_DEPRECATED_MSG):
      return (GDATA.API_DEPRECATED, body)
    if reason == 'Too Many Requests':
      return (GDATA.QUOTA_EXCEEDED, reason)
    if reason == 'Bad Gateway':
      return (GDATA.BAD_GATEWAY, reason)
    if reason == 'Gateway Timeout':
      return (GDATA.GATEWAY_TIMEOUT, reason)
    if reason == 'Service Unavailable':
      return (GDATA.SERVICE_UNAVAILABLE, reason)
    if reason == 'Service <jotspot> disabled by G Suite admin.':
      return (GDATA.FORBIDDEN, reason)
    if reason == 'Internal Server Error':
      return (GDATA.INTERNAL_SERVER_ERROR, reason)
    if reason == 'Token invalid - Invalid token: Token disabled, revoked, or expired.':
      return (GDATA.TOKEN_INVALID, 'Token disabled, revoked, or expired. Please delete and re-create oauth.txt')
    if reason == 'Token invalid - AuthSub token has wrong scope':
      return (GDATA.INSUFFICIENT_PERMISSIONS, reason)
    if reason.startswith('Only administrators can request entries belonging to'):
      return (GDATA.INSUFFICIENT_PERMISSIONS, reason)
    if reason == 'You are not authorized to access this API':
      return (GDATA.INSUFFICIENT_PERMISSIONS, reason)
    if reason == 'Invalid domain.':
      return (GDATA.INVALID_DOMAIN, reason)
    if reason.startswith('You are not authorized to perform operations on the domain'):
      return (GDATA.INVALID_DOMAIN, reason)
    if reason == 'Bad Request':
      if 'already exists' in body:
        return (GDATA.ENTITY_EXISTS, Msg.DUPLICATE)
      return (GDATA.BAD_REQUEST, body)
    if reason == 'Forbidden':
      return (GDATA.FORBIDDEN, body)
    if reason == 'Not Found':
      return (GDATA.NOT_FOUND, Msg.DOES_NOT_EXIST)
    if reason == 'Not Implemented':
      return (GDATA.NOT_IMPLEMENTED, body)
    if reason == 'Precondition Failed':
      return (GDATA.PRECONDITION_FAILED, reason)
  elif error_code == 602:
    if body.startswith(GDATA.API_DEPRECATED_MSG):
      return (GDATA.API_DEPRECATED, body)
    if reason == 'Bad Request':
      return (GDATA.BAD_REQUEST, body)
  elif error_code == 610:
    if reason == 'Service <jotspot> disabled by G Suite admin.':
      return (GDATA.FORBIDDEN, reason)

  # We got a "normal" error, define the mapping below
  error_code_map = {
    1000: reason,
    1001: reason,
    1002: 'Unauthorized and forbidden',
    1100: 'User deleted recently',
    1200: 'Domain user limit exceeded',
    1201: 'Domain alias limit exceeded',
    1202: 'Domain suspended',
    1203: 'Domain feature unavailable',
    1300: f'Entity {getattr(e, "invalidInput", "<unknown>")} exists',
    1301: f'Entity {getattr(e, "invalidInput", "<unknown>")} Does Not Exist',
    1302: 'Entity Name Is Reserved',
    1303: f'Entity {getattr(e, "invalidInput", "<unknown>")} name not valid',
    1306: f'{getattr(e, "invalidInput", "<unknown>")} has members. Cannot delete.',
    1317: f'Invalid input {getattr(e, "invalidInput", "<unknown>")}, reason {getattr(e, "reason", "<unknown>")}',
    1400: 'Invalid Given Name',
    1401: 'Invalid Family Name',
    1402: 'Invalid Password',
    1403: 'Invalid Username',
    1404: 'Invalid Hash Function Name',
    1405: 'Invalid Hash Digest Length',
    1406: 'Invalid Email Address',
    1407: 'Invalid Query Parameter Value',
    1408: 'Invalid SSO Signing Key',
    1409: 'Invalid Encryption Public Key',
    1410: 'Feature Unavailable For User',
    1411: 'Invalid Encryption Public Key Format',
    1500: 'Too Many Recipients On Email List',
    1501: 'Too Many Aliases For User',
    1502: 'Too Many Delegates For User',
    1601: 'Duplicate Destinations',
    1602: 'Too Many Destinations',
    1603: 'Invalid Route Address',
    1700: 'Group Cannot Contain Cycle',
    1800: 'Group Cannot Contain Cycle',
    1801: f'Invalid value {getattr(e, "invalidInput", "<unknown>")}',
  }
  return (error_code, error_code_map.get(error_code, f'Unknown Error: {str(e)}'))

def callGData(service, function,
              bailOnInternalServerError=False, softErrors=False,
              throwErrors=None, retryErrors=None, triesLimit=0,
              **kwargs):
  m = _getMain()
  if throwErrors is None:
    throwErrors = []
  if retryErrors is None:
    retryErrors = []
  if triesLimit == 0:
    triesLimit = GC.Values[GC.API_CALLS_TRIES_LIMIT]
  allRetryErrors = GDATA.NON_TERMINATING_ERRORS+retryErrors
  method = getattr(service, function)
  if GC.Values[GC.API_CALLS_RATE_CHECK]:
    m.checkAPICallsRate()
  for n in range(1, triesLimit+1):
    try:
      return method(**kwargs)
    except (gdata.service.RequestError, gdata.apps.service.AppsForYourDomainException) as e:
      error_code, error_message = checkGDataError(e, service)
      if (n != triesLimit) and (error_code in allRetryErrors):
        if (error_code == GDATA.INTERNAL_SERVER_ERROR and
            bailOnInternalServerError and n == GC.Values[GC.BAIL_ON_INTERNAL_ERROR_TRIES]):
          raise GDATA.ERROR_CODE_EXCEPTION_MAP[error_code](error_message)
        waitOnFailure(n, triesLimit, error_code, error_message)
        continue
      if error_code in throwErrors:
        if error_code in GDATA.ERROR_CODE_EXCEPTION_MAP:
          raise GDATA.ERROR_CODE_EXCEPTION_MAP[error_code](error_message)
        raise
      if softErrors:
        m.stderrErrorMsg(f'{error_code} - {error_message}{["", ": Giving up."][n > 1]}')
        return None
      if error_code == GDATA.INSUFFICIENT_PERMISSIONS:
        m.APIAccessDeniedExit()
      m.systemErrorExit(m.GOOGLE_API_ERROR_RC, f'{error_code} - {error_message}')
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        waitOnFailure(n, triesLimit, m.NETWORK_ERROR_RC, str(e))
        continue
      handleServerError(e)
    except google.auth.exceptions.RefreshError as e:
      if isinstance(e.args, tuple):
        e = e.args[0]
      handleOAuthTokenError(e, GDATA.SERVICE_NOT_APPLICABLE in throwErrors)
      raise GDATA.ERROR_CODE_EXCEPTION_MAP[GDATA.SERVICE_NOT_APPLICABLE](str(e))
    except (http.client.ResponseNotReady, OSError) as e:
      errMsg = f'Connection error: {str(e) or repr(e)}'
      if n != triesLimit:
        waitOnFailure(n, triesLimit, m.SOCKET_ERROR_RC, errMsg)
        continue
      if softErrors:
        m.writeStderr(f'\n{m.ERROR_PREFIX}{errMsg} - Giving up.\n')
        return None
      m.systemErrorExit(m.SOCKET_ERROR_RC, errMsg)

def writeGotMessage(msg):
  m = _getMain()
  if GC.Values[GC.SHOW_GETTINGS_GOT_NL]:
    m.writeStderr(msg)
  else:
    m.writeStderr('\r')
    msgLen = len(msg)
    if msgLen < GM.Globals[GM.LAST_GOT_MSG_LEN]:
      m.writeStderr(msg+' '*(GM.Globals[GM.LAST_GOT_MSG_LEN]-msgLen))
    else:
      m.writeStderr(msg)
    GM.Globals[GM.LAST_GOT_MSG_LEN] = msgLen
  m.flushStderr()

def callGDataPages(service, function,
                   pageMessage=None,
                   softErrors=False, throwErrors=None, retryErrors=None,
                   uri=None,
                   **kwargs):
  m = _getMain()
  Ent = _getEnt()
  if throwErrors is None:
    throwErrors = []
  if retryErrors is None:
    retryErrors = []
  nextLink = None
  allResults = []
  totalItems = 0
  while True:
    this_page = callGData(service, function,
                          softErrors=softErrors, throwErrors=throwErrors, retryErrors=retryErrors,
                          uri=uri,
                          **kwargs)
    if this_page:
      nextLink = this_page.GetNextLink()
      pageItems = len(this_page.entry)
      if pageItems == 0:
        nextLink = None
      totalItems += pageItems
      allResults.extend(this_page.entry)
    else:
      nextLink = None
      pageItems = 0
    if pageMessage:
      show_message = pageMessage.replace(m.TOTAL_ITEMS_MARKER, str(totalItems))
      writeGotMessage(show_message.format(Ent.ChooseGetting(totalItems)))
    if nextLink is None:
      if pageMessage and (pageMessage[-1] != '\n'):
        m.writeStderr('\r\n')
        m.flushStderr()
      return allResults
    uri = nextLink.href
    if 'url_params' in kwargs:
      kwargs['url_params'].pop('start-index', None)

def checkGAPIError(e, softErrors=False, retryOnHttpError=False, mapNotFound=True):
  m = _getMain()

  def makeErrorDict(code, reason, message):
    return {'error': {'code': code, 'errors': [{'reason': reason, 'message': message}]}}

  try:
    error = json.loads(e.content.decode(m.UTF8))
    if GC.Values[GC.DEBUG_LEVEL] > 0:
      m.writeStdout(f'{m.ERROR_PREFIX} JSON: {str(error)}\n')
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
    eContent = e.content.decode(m.UTF8) if isinstance(e.content, bytes) else e.content
    lContent = eContent.lower()
    if GC.Values[GC.DEBUG_LEVEL] > 0:
      m.writeStdout(f'{m.ERROR_PREFIX} HTTP: {str(eContent)}\n')
    if eContent[0:15] != '<!DOCTYPE html>':
      if (e.resp['status'] == '403') and (lContent.startswith('request rate higher than configured')):
        return (e.resp['status'], GAPI.QUOTA_EXCEEDED, eContent)
      if (e.resp['status'] == '429') and (lContent.startswith('quota exceeded for quota metric')):
        return (e.resp['status'], GAPI.QUOTA_EXCEEDED, eContent)
      if (e.resp['status'] == '502') and ('bad gateway' in lContent):
        return (e.resp['status'], GAPI.BAD_GATEWAY, eContent)
      if (e.resp['status'] == '503') and (lContent.startswith('quota exceeded for the current request')):
        return (e.resp['status'], GAPI.QUOTA_EXCEEDED, eContent)
      if (e.resp['status'] == '504') and ('gateway timeout' in lContent):
        return (e.resp['status'], GAPI.GATEWAY_TIMEOUT, eContent)
    else:
      tg = m.HTML_TITLE_PATTERN.match(lContent)
      lContent = tg.group(1) if tg else 'bad request'
    if (e.resp['status'] == '403') and ('invalid domain.' in lContent):
      error = makeErrorDict(403, GAPI.NOT_FOUND, 'Domain not found')
    elif (e.resp['status'] == '403') and ('domain cannot use apis.' in lContent):
      error = makeErrorDict(403, GAPI.DOMAIN_CANNOT_USE_APIS, 'Domain cannot use apis')
    elif (e.resp['status'] == '400') and ('invalidssosigningkey' in lContent):
      error = makeErrorDict(400, GAPI.INVALID, 'InvalidSsoSigningKey')
    elif (e.resp['status'] == '400') and ('unknownerror' in lContent):
      error = makeErrorDict(400, GAPI.INVALID, 'UnknownError')
    elif (e.resp['status'] == '400') and ('featureunavailableforuser' in lContent):
      error = makeErrorDict(400, GAPI.SERVICE_NOT_AVAILABLE, 'Feature Unavailable For User')
    elif (e.resp['status'] == '400') and ('entitydoesnotexist' in lContent):
      error = makeErrorDict(400, GAPI.NOT_FOUND, 'Entity Does Not Exist')
    elif (e.resp['status'] == '400') and ('entitynamenotvalid' in lContent):
      error = makeErrorDict(400, GAPI.INVALID_INPUT, 'Entity Name Not Valid')
    elif (e.resp['status'] == '400') and ('failed to parse Content-Range header' in lContent):
      error = makeErrorDict(400, GAPI.BAD_REQUEST, 'Failed to parse Content-Range header')
    elif (e.resp['status'] == '400') and ('request contains an invalid argument' in lContent):
      error = makeErrorDict(400, GAPI.INVALID_ARGUMENT, 'Request contains an invalid argument')
    elif (e.resp['status'] == '404') and ('not found' in lContent):
      error = makeErrorDict(404, GAPI.NOT_FOUND, lContent)
    elif (e.resp['status'] == '404') and ('bad request' in lContent):
      error = makeErrorDict(404, GAPI.BAD_REQUEST, lContent)
    elif retryOnHttpError:
      return (-1, None, eContent)
    elif softErrors:
      m.stderrErrorMsg(eContent)
      return (0, None, None)
    else:
      m.systemErrorExit(m.HTTP_ERROR_RC, eContent)
  requiredScopes = ''
  wwwAuthenticate = e.resp.get('www-authenticate', '')
  if 'insufficient_scope' in wwwAuthenticate:
    mg = re.match(r'.+scope="(.+)"', wwwAuthenticate)
    if mg:
      requiredScopes = mg.group(1).split(' ')
  if 'error' in error:
    http_status = error['error']['code']
    reason = ''
    if 'errors' in error['error'] and 'message' in error['error']['errors'][0]:
      message = error['error']['errors'][0]['message']
      if 'reason' in error['error']['errors'][0]:
        reason = error['error']['errors'][0]['reason']
    elif 'errors' in error['error'] and 'Unknown Error' in error['error']['message'] and 'reason' in error['error']['errors'][0]:
      message = error['error']['errors'][0]['reason']
    else:
      message = error['error']['message']
    status = error['error'].get('status', '')
    lmessage = message.lower() if message is not None else ''
    if http_status == 500:
      if not lmessage or status == 'UNKNOWN':
        if not lmessage:
          message = Msg.UNKNOWN
        error = makeErrorDict(http_status, GAPI.UNKNOWN_ERROR, message)
      elif 'backend error' in lmessage:
        error = makeErrorDict(http_status, GAPI.BACKEND_ERROR, message)
      elif 'internal error encountered' in lmessage:
        error = makeErrorDict(http_status, GAPI.INTERNAL_ERROR, message)
      elif 'role assignment exists: roleassignment' in lmessage:
        error = makeErrorDict(http_status, GAPI.DUPLICATE, message)
      elif 'role assignment exists: roleid' in lmessage:
        error = makeErrorDict(http_status, GAPI.DUPLICATE, message)
      elif 'operation not supported' in lmessage:
        error = makeErrorDict(http_status, GAPI.OPERATION_NOT_SUPPORTED, message)
      elif 'failed status in update settings response' in lmessage:
        error = makeErrorDict(http_status, GAPI.INVALID_INPUT, message)
      elif 'cannot delete a field in use.resource.fields' in lmessage:
        error = makeErrorDict(http_status, GAPI.FIELD_IN_USE, message)
      elif status == 'INTERNAL':
        error = makeErrorDict(http_status, GAPI.INTERNAL_ERROR, message)
    elif http_status == 501:
      if status == 'UNIMPLEMENTED':
        error = makeErrorDict(http_status, GAPI.UNIMPLEMENTED_ERROR, message)
    elif http_status == 502:
      if 'bad gateway' in lmessage:
        error = makeErrorDict(http_status, GAPI.BAD_GATEWAY, message)
    elif http_status == 503:
      if message.startswith('quota exceeded for the current request'):
        error = makeErrorDict(http_status, GAPI.QUOTA_EXCEEDED, message)
      elif status == 'UNAVAILABLE' or 'the service is currently unavailable' in lmessage:
        error = makeErrorDict(http_status, GAPI.SERVICE_NOT_AVAILABLE, message)
    elif http_status == 504:
      if 'gateway timeout' in lmessage:
        error = makeErrorDict(http_status, GAPI.GATEWAY_TIMEOUT, message)
    elif http_status == 400:
      if '@attachmentnotvisible' in lmessage:
        error = makeErrorDict(http_status, GAPI.BAD_REQUEST, message)
      elif status == 'INVALID_ARGUMENT':
        error = makeErrorDict(http_status, GAPI.INVALID_ARGUMENT, message)
      elif status == 'FAILED_PRECONDITION' or 'precondition check failed' in lmessage:
        error = makeErrorDict(http_status, GAPI.FAILED_PRECONDITION, message)
      elif 'does not match' in lmessage or 'invalid' in lmessage:
        error = makeErrorDict(http_status, GAPI.INVALID, message)
    elif http_status == 401:
      if 'active session is invalid' in lmessage and reason == 'authError':
#        message += ' Drive SDK API access disabled'
#        message = Msg.SERVICE_NOT_ENABLED.format('Drive')
        error = makeErrorDict(http_status, GAPI.AUTH_ERROR, message)
      elif status == 'PERMISSION_DENIED':
        error = makeErrorDict(http_status, GAPI.PERMISSION_DENIED, message)
      elif status == 'UNAUTHENTICATED':
        error = makeErrorDict(http_status, GAPI.AUTH_ERROR, message)
    elif http_status == 403:
      if 'quota exceeded for quota metric' in lmessage:
        error = makeErrorDict(http_status, GAPI.QUOTA_EXCEEDED, message)
      elif 'the authenticated user cannot access this service' in lmessage:
        error = makeErrorDict(http_status, GAPI.SERVICE_NOT_AVAILABLE, message)
      elif status == 'PERMISSION_DENIED' or 'the caller does not have permission' in lmessage or 'permission iam.serviceaccountkeys' in lmessage:
        if requiredScopes:
          message += f', {Msg.NO_SCOPES_FOR_API.format(API.findAPIforScope(requiredScopes))}'
        error = makeErrorDict(http_status, GAPI.PERMISSION_DENIED, message)
    elif http_status == 404:
      if status == 'NOT_FOUND' or 'requested entity was not found' in lmessage or 'does not exist' in lmessage:
        error = makeErrorDict(http_status, GAPI.NOT_FOUND, message)
    elif http_status == 409:
      if status == 'ALREADY_EXISTS' or 'requested entity already exists' in lmessage:
        error = makeErrorDict(http_status, GAPI.ALREADY_EXISTS, message)
      elif status == 'ABORTED' or 'the operation was aborted' in lmessage:
        error = makeErrorDict(http_status, GAPI.ABORTED, message)
    elif http_status == 412:
      if 'insufficient archived user licenses' in lmessage:
        error = makeErrorDict(http_status, GAPI.INSUFFICIENT_ARCHIVED_USER_LICENSES, message)
    elif http_status == 413:
      if 'request too large' in lmessage:
        error = makeErrorDict(http_status, GAPI.UPLOAD_TOO_LARGE, message)
    elif http_status == 429:
      if status == 'RESOURCE_EXHAUSTED' or 'quota exceeded' in lmessage or 'insufficient quota' in lmessage:
        error = makeErrorDict(http_status, GAPI.QUOTA_EXCEEDED, message)
  else:
    if 'error_description' in error:
      if error['error_description'] == 'Invalid Value':
        message = error['error_description']
        http_status = 400
        error = makeErrorDict(http_status, GAPI.INVALID, message)
      else:
        m.systemErrorExit(m.GOOGLE_API_ERROR_RC, str(error))
    else:
      m.systemErrorExit(m.GOOGLE_API_ERROR_RC, str(error))
  try:
    reason = error['error']['errors'][0]['reason']
    for messageItem in GAPI.REASON_MESSAGE_MAP.get(reason, []):
      if messageItem[0] in message:
        if reason in [GAPI.NOT_FOUND, GAPI.RESOURCE_NOT_FOUND] and mapNotFound:
          message = Msg.DOES_NOT_EXIST
        reason = messageItem[1]
        break
    if reason == GAPI.INVALID_SHARING_REQUEST:
      loc = message.find('User message: ')
      if loc != -1:
        message = message[loc+15:]
    else:
      loc = message.find('User message: ""')
      if loc != -1:
        message = message[:loc+14]+f'"{reason}"'
  except KeyError:
    reason = f'{http_status}'
  return (http_status, reason, message)

def callGAPI(service, function,
             bailOnInternalError=False, bailOnTransientError=False, bailOnInvalidError=False,
             softErrors=False, mapNotFound=True,
             throwReasons=None, retryReasons=None, triesLimit=0,
             **kwargs):
  m = _getMain()
  if throwReasons is None:
    throwReasons = []
  if retryReasons is None:
    retryReasons = []
  if triesLimit == 0:
    triesLimit = GC.Values[GC.API_CALLS_TRIES_LIMIT]
  allRetryReasons = GAPI.DEFAULT_RETRY_REASONS+retryReasons
  method = getattr(service, function)
  svcparms = dict(list(kwargs.items())+GM.Globals[GM.EXTRA_ARGS_LIST])
  if GC.Values[GC.API_CALLS_RATE_CHECK]:
    m.checkAPICallsRate()
  for n in range(1, triesLimit+1):
    try:
      return method(**svcparms).execute()
    except googleapiclient.errors.HttpError as e:
      http_status, reason, message = checkGAPIError(e, softErrors=softErrors, retryOnHttpError=n < 3, mapNotFound=mapNotFound)
      if http_status == -1:
        # The error detail indicated that we should retry this request
        # We'll refresh credentials and make another pass
        try:
#          service._http.credentials.refresh(getHttpObj())
          service._http.credentials.refresh(transportCreateRequest())
        except TypeError:
          m.systemErrorExit(m.HTTP_ERROR_RC, message)
        continue
      if http_status == 0:
        return None
      if (n != triesLimit) and ((reason in allRetryReasons) or
                             (GC.Values[GC.RETRY_API_SERVICE_NOT_AVAILABLE] and (reason == GAPI.SERVICE_NOT_AVAILABLE))):
        if (reason in [GAPI.INTERNAL_ERROR, GAPI.BACKEND_ERROR] and
            bailOnInternalError and n == GC.Values[GC.BAIL_ON_INTERNAL_ERROR_TRIES]):
          raise GAPI.REASON_EXCEPTION_MAP[reason](message)
        if (reason in [GAPI.INVALID] and
            bailOnInvalidError and n == GC.Values[GC.BAIL_ON_INTERNAL_ERROR_TRIES]):
          raise GAPI.REASON_EXCEPTION_MAP[reason](message)
        waitOnFailure(n, triesLimit, reason, message)
        if reason == GAPI.TRANSIENT_ERROR and bailOnTransientError:
          raise GAPI.REASON_EXCEPTION_MAP[reason](message)
        continue
      if reason in throwReasons:
        if reason in GAPI.REASON_EXCEPTION_MAP:
          raise GAPI.REASON_EXCEPTION_MAP[reason](message)
        raise e
      if softErrors:
        m.stderrErrorMsg(f'{http_status}: {reason} - {message}{["", ": Giving up."][n > 1]}')
        return None
      if reason == GAPI.INSUFFICIENT_PERMISSIONS:
        m.APIAccessDeniedExit()
      m.systemErrorExit(m.HTTP_ERROR_RC, m.formatHTTPError(http_status, reason, message))
    except googleapiclient.errors.MediaUploadSizeError as e:
      raise e
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        service._http.connections = {}
        waitOnFailure(n, triesLimit, m.NETWORK_ERROR_RC, str(e))
        continue
      handleServerError(e)
    except google.auth.exceptions.RefreshError as e:
      if isinstance(e.args, tuple):
        e = e.args[0]
      handleOAuthTokenError(e, GAPI.SERVICE_NOT_AVAILABLE in throwReasons)
      raise GAPI.REASON_EXCEPTION_MAP[GAPI.SERVICE_NOT_AVAILABLE](str(e))
    except (http.client.ResponseNotReady, OSError) as e:
      errMsg = f'Connection error: {str(e) or repr(e)}'
      if n != triesLimit:
        waitOnFailure(n, triesLimit, m.SOCKET_ERROR_RC, errMsg)
        continue
      if softErrors:
        m.writeStderr(f'\n{m.ERROR_PREFIX}{errMsg} - Giving up.\n')
        return None
      m.systemErrorExit(m.SOCKET_ERROR_RC, errMsg)
    except ValueError as e:
      if clearServiceCache(service):
        continue
      m.systemErrorExit(m.GOOGLE_API_ERROR_RC, str(e))
    except TypeError as e:
      m.systemErrorExit(m.GOOGLE_API_ERROR_RC, str(e))

def _showGAPIpagesResult(results, pageItems, totalItems, pageMessage, messageAttribute, entityType):
  m = _getMain()
  Ent = _getEnt()
  showMessage = pageMessage.replace(m.TOTAL_ITEMS_MARKER, str(totalItems))
  if pageItems:
    if messageAttribute:
      firstItem = results[0] if pageItems > 0 else {}
      lastItem = results[-1] if pageItems > 1 else firstItem
      if isinstance(messageAttribute, str):
        firstItem = str(firstItem.get(messageAttribute, ''))
        lastItem = str(lastItem.get(messageAttribute, ''))
      else:
        for attr in messageAttribute:
          firstItem = firstItem.get(attr, {})
          lastItem = lastItem.get(attr, {})
        firstItem = str(firstItem)
        lastItem = str(lastItem)
      showMessage = showMessage.replace(m.FIRST_ITEM_MARKER, firstItem)
      showMessage = showMessage.replace(m.LAST_ITEM_MARKER, lastItem)
  else:
    showMessage = showMessage.replace(m.FIRST_ITEM_MARKER, '')
    showMessage = showMessage.replace(m.LAST_ITEM_MARKER, '')
  writeGotMessage(showMessage.replace('{0}', str(Ent.Choose(entityType, totalItems))))

def _processGAPIpagesResult(results, items, allResults, totalItems, pageMessage, messageAttribute, entityType):
  if results:
    pageToken = results.get('nextPageToken')
    if items in results:
      pageItems = len(results[items])
      totalItems += pageItems
      if allResults is not None:
        allResults.extend(results[items])
    else:
      results = {items: []}
      pageItems = 0
  else:
    pageToken = None
    results = {items: []}
    pageItems = 0
  if pageMessage:
    _showGAPIpagesResult(results[items], pageItems, totalItems, pageMessage, messageAttribute, entityType)
  return (pageToken, totalItems)

def _finalizeGAPIpagesResult(pageMessage):
  m = _getMain()
  if pageMessage and (pageMessage[-1] != '\n'):
    m.writeStderr('\r\n')
    m.flushStderr()

def _setMaxArgResults(maxItems, pageArgsInBody, kwargs):
  if pageArgsInBody:
    kwargs.setdefault('body', {})
  maxArg = ''
  maxResults = 0
  if maxItems:
    if not pageArgsInBody:
      maxResults = kwargs.get('maxResults', 0)
      if maxResults:
        maxArg = 'maxResults'
      else:
        maxResults = kwargs.get('pageSize', 0)
        if maxResults:
          maxArg = 'pageSize'
    else:
      maxResults = kwargs['body'].get('maxResults', 0)
      if maxResults:
        maxArg = 'maxResults'
      else:
        maxResults = kwargs['body'].get('pageSize', 0)
        if maxResults:
          maxArg = 'pageSize'
  return (maxArg, maxResults)

def callGAPIpages(service, function, items,
                  pageMessage=None, messageAttribute=None, maxItems=0, noFinalize=False,
                  throwReasons=None, retryReasons=None,
                  pageArgsInBody=False,
                  **kwargs):
  Ent = _getEnt()
  if throwReasons is None:
    throwReasons = []
  if retryReasons is None:
    retryReasons = []
  allResults = []
  totalItems = 0
  maxArg, maxResults = _setMaxArgResults(maxItems, pageArgsInBody, kwargs)
  entityType = Ent.Getting() if pageMessage else None
  while True:
    if maxArg and maxItems-totalItems < maxResults:
      if not pageArgsInBody:
        kwargs[maxArg] = maxItems-totalItems
      else:
        kwargs['body'][maxArg] = maxItems-totalItems
    results = callGAPI(service, function,
                       throwReasons=throwReasons, retryReasons=retryReasons,
                       **kwargs)
    pageToken, totalItems = _processGAPIpagesResult(results, items, allResults, totalItems, pageMessage, messageAttribute, entityType)
    if not pageToken or (maxItems and totalItems >= maxItems):
      if not noFinalize:
        _finalizeGAPIpagesResult(pageMessage)
      return allResults
    if not pageArgsInBody:
      kwargs['pageToken'] = pageToken
    else:
      kwargs['body']['pageToken'] = pageToken

def yieldGAPIpages(service, function, items,
                   pageMessage=None, messageAttribute=None, maxItems=0, noFinalize=False,
                   throwReasons=None, retryReasons=None,
                   pageArgsInBody=False,
                   **kwargs):
  Ent = _getEnt()
  if throwReasons is None:
    throwReasons = []
  if retryReasons is None:
    retryReasons = []
  totalItems = 0
  maxArg, maxResults = _setMaxArgResults(maxItems, pageArgsInBody, kwargs)
  entityType = Ent.Getting() if pageMessage else None
  while True:
    if maxArg and maxItems-totalItems < maxResults:
      if not pageArgsInBody:
        kwargs[maxArg] = maxItems-totalItems
      else:
        kwargs['body'][maxArg] = maxItems-totalItems
    results = callGAPI(service, function,
                       throwReasons=throwReasons, retryReasons=retryReasons,
                       **kwargs)
    if results:
      pageToken = results.get('nextPageToken')
      if items in results:
        pageItems = len(results[items])
        totalItems += pageItems
      else:
        results = {items: []}
        pageItems = 0
    else:
      pageToken = None
      results = {items: []}
      pageItems = 0
    if pageMessage:
      _showGAPIpagesResult(results[items], pageItems, totalItems, pageMessage, messageAttribute, entityType)
    yield results[items]
    if not pageToken or (maxItems and totalItems >= maxItems):
      if not noFinalize:
        _finalizeGAPIpagesResult(pageMessage)
      return
    if not pageArgsInBody:
      kwargs['pageToken'] = pageToken
    else:
      kwargs['body']['pageToken'] = pageToken

def callGAPIitems(service, function, items,
                  throwReasons=None, retryReasons=None,
                  **kwargs):
  if throwReasons is None:
    throwReasons = []
  if retryReasons is None:
    retryReasons = []
  results = callGAPI(service, function,
                     throwReasons=throwReasons, retryReasons=retryReasons,
                     **kwargs)
  if results:
    return results.get(items, [])
  return []

def readDiscoveryFile(api_version):
  m = _getMain()
  disc_filename = f'{api_version}.json'
  disc_file = os.path.join(GM.Globals[GM.GAM_PATH], disc_filename)
  if hasattr(sys, '_MEIPASS'):
    json_string = m.readFile(os.path.join(sys._MEIPASS, disc_filename), continueOnError=True, displayError=True) #pylint: disable=no-member
  elif os.path.isfile(disc_file):
    json_string = m.readFile(disc_file, continueOnError=True, displayError=True)
  else:
    json_string = None
  if not json_string:
    m.invalidDiscoveryJsonExit(disc_file, Msg.NO_DATA)
  try:
    discovery = json.loads(json_string)
    return (disc_file, discovery)
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    m.invalidDiscoveryJsonExit(disc_file, str(e))

def buildGAPIObject(api, credentials=None):
  m = _getMain()
  if credentials is None:
    credentials = getClientCredentials(api=api, refreshOnly=True)
  httpObj = transportAuthorizedHttp(credentials, http=getHttpObj(cache=GM.Globals[GM.CACHE_DIR]))
  service = getService(api, httpObj)
  if not GC.Values[GC.ENABLE_DASA]:
    discovery_scopes = list(service._rootDesc.get('auth', {}).get('oauth2', {}).get('scopes', {}).keys())
    extra_scopes = API.EXTRA_SCOPES.get(api, [])
    API_Scopes = set(discovery_scopes + extra_scopes)
    GM.Globals[GM.CURRENT_CLIENT_API] = api
    GM.Globals[GM.CURRENT_CLIENT_API_SCOPES] = API_Scopes.intersection(GM.Globals[GM.CREDENTIALS_SCOPES])
    if api not in API.SCOPELESS_APIS and not GM.Globals[GM.CURRENT_CLIENT_API_SCOPES]:
      m.systemErrorExit(m.NO_SCOPES_FOR_API_RC, Msg.NO_SCOPES_FOR_API.format(API.getAPIName(api)))
    if not GC.Values[GC.DOMAIN]:
      GC.Values[GC.DOMAIN] = GM.Globals[GM.DECODED_ID_TOKEN].get('hd', 'UNKNOWN').lower()
    if not GC.Values[GC.CUSTOMER_ID]:
      GC.Values[GC.CUSTOMER_ID] = GC.MY_CUSTOMER
    GM.Globals[GM.ADMIN] = GM.Globals[GM.DECODED_ID_TOKEN].get('email', 'UNKNOWN').lower()
    GM.Globals[GM.OAUTH2_CLIENT_ID] = credentials.client_id
  return service

def getSaUser(user):
  m = _getMain()
  currentClientAPI = GM.Globals[GM.CURRENT_CLIENT_API]
  currentClientAPIScopes = GM.Globals[GM.CURRENT_CLIENT_API_SCOPES]
  userEmail = m.convertUIDtoEmailAddress(user) if user else None
  GM.Globals[GM.CURRENT_CLIENT_API] = currentClientAPI
  GM.Globals[GM.CURRENT_CLIENT_API_SCOPES] = currentClientAPIScopes
  return userEmail

def chooseSaAPI(api1, api2):
  _getSvcAcctData()
  if api1 in GM.Globals[GM.SVCACCT_SCOPES]:
    return api1
  return api2

def buildGAPIServiceObject(api, user, i=0, count=0, displayError=True):
  m = _getMain()
  userEmail = getSaUser(user)
  if GM.Globals[GM.HTTP_OBJECT] is None:
    GM.Globals[GM.HTTP_OBJECT] = getHttpObj(cache=GM.Globals[GM.CACHE_DIR])
  httpObj = GM.Globals[GM.HTTP_OBJECT]
  service = getService(api, httpObj)
  credentials = getSvcAcctCredentials(api, userEmail)
  request = transportCreateRequest(httpObj)
  triesLimit = 3
  for n in range(1, triesLimit+1):
    try:
      credentials.refresh(request)
      service._http = transportAuthorizedHttp(credentials, http=httpObj)
      return (userEmail, service)
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        httpObj.connections = {}
        waitOnFailure(n, triesLimit, m.NETWORK_ERROR_RC, str(e))
        continue
      handleServerError(e)
    except google.auth.exceptions.RefreshError as e:
      if isinstance(e.args, tuple):
        e = e.args[0]
      if n < triesLimit:
        if isinstance(e, str):
          eContent = e
        else:
          eContent = e.content.decode(m.UTF8) if isinstance(e.content, bytes) else e.content
        if eContent[0:15] == '<!DOCTYPE html>':
          if GC.Values[GC.DEBUG_LEVEL] > 0:
            m.writeStdout(f'{m.ERROR_PREFIX} HTTP: {str(eContent)}\n')
          lContent = eContent.lower()
          tg = m.HTML_TITLE_PATTERN.match(lContent)
          lContent = tg.group(1) if tg else ''
          if lContent.startswith('Error 502 (Server Error)'):
            time.sleep(30)
            continue
      handleOAuthTokenError(e, True, displayError, i, count)
      return (userEmail, None)

def buildGAPIObjectNoAuthentication(api):
  httpObj = getHttpObj(cache=GM.Globals[GM.CACHE_DIR])
  service = getService(api, httpObj)
  return service

def initGDataObject(gdataObj, api):
  m = _getMain()
  GM.Globals[GM.CURRENT_CLIENT_API] = api
  credentials = getClientCredentials(noDASA=True, refreshOnly=True)
  GM.Globals[GM.CURRENT_CLIENT_API_SCOPES] = API.getClientScopesSet(api).intersection(GM.Globals[GM.CREDENTIALS_SCOPES])
  if not GM.Globals[GM.CURRENT_CLIENT_API_SCOPES]:
    m.systemErrorExit(m.NO_SCOPES_FOR_API_RC, Msg.NO_SCOPES_FOR_API.format(API.getAPIName(api)))
  getGDataOAuthToken(gdataObj, credentials)
  if GC.Values[GC.DEBUG_LEVEL] > 0:
    gdataObj.debug = True
  return gdataObj

def getGDataUserCredentials(api, user, i, count):
  userEmail = getSaUser(user)
  credentials = getSvcAcctCredentials(api, userEmail)
  request = transportCreateRequest()
  try:
    credentials.refresh(request)
    return (userEmail, credentials)
  except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
    handleServerError(e)
  except google.auth.exceptions.RefreshError as e:
    if isinstance(e.args, tuple):
      e = e.args[0]
    handleOAuthTokenError(e, True, True, i, count)
    return (userEmail, None)

def getContactsObject():
  contactsObject = initGDataObject(gdata.apps.contacts.service.ContactsService(contactFeed=True),
                                   API.CONTACTS)
  return (GC.Values[GC.DOMAIN], contactsObject)

def getContactsQuery(**kwargs):
  if GC.Values[GC.NO_VERIFY_SSL]:
    ssl._create_default_https_context = ssl._create_unverified_context
  return gdata.apps.contacts.service.ContactsQuery(**kwargs)

def getEmailAuditObject():
  return initGDataObject(gdata.apps.audit.service.AuditService(), API.EMAIL_AUDIT)
