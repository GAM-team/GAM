"""GAM API utility functions.

HTTP transport, OAuth credential management, Google API service
construction, and GAPI call wrappers with retry logic.
"""

import http.client
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import time

try:
  import termios
except ImportError:
  termios = None  # Not available on Windows

import arrow
import google.auth
import google.auth._helpers
import google.auth.compute_engine._metadata as gce_metadata
import google.auth.crypt
import google.auth.iam
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



from gamlib import api as API
from gamlib import settings as GC
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Ent
from gam.constants import API_ACCESS_DENIED_RC, GOOGLE_API_ERROR_RC, NETWORK_ERROR_RC, NO_SCOPES_FOR_API_RC, REFRESH_EXPIRY, SOCKET_ERROR_RC, SYSTEM_ERROR_RC
from gam.util.args import UTF8, YYYYMMDDTHHMMSSZ_FORMAT
from gam.util.display import SERVICE_NOT_APPLICABLE_RC, entityActionFailedWarning, printBlankLine, userServiceNotEnabledWarning
from gam.util.errors import INVALID_JSON_RC, OAUTH2SERVICE_JSON_REQUIRED_RC, OAUTH2_TXT_REQUIRED_RC, expiredRevokedOauth2TxtExit, invalidDiscoveryJsonExit, invalidOauth2TxtExit, invalidOauth2serviceJsonExit
from gam.util.fileio import FILE_ERROR_RC, UNKNOWN, incrAPICallsRetryData, readFile, writeFile
from gam.util.output import flushStderr, stderrErrorMsg, systemErrorExit, writeStderr, writeStdout


HTML_TITLE_PATTERN = re.compile(r'.*<title>(.+)</title>')
from gam.constants import GAM_USER_AGENT, __author__


# Constants only used in this module
URL_SHORTENER_ENDPOINT = 'https://gam-shortn.appspot.com/create'
DISCOVERY_URIS = [googleapiclient.discovery.V1_DISCOVERY_URI, googleapiclient.discovery.V2_DISCOVERY_URI]
DEVELOPER_PREVIEW_DISCOVERY_URI = "https://{api}.googleapis.com/$discovery/rest?labels=DEVELOPER_PREVIEW&version={apiVersion}"
_DEFAULT_TOKEN_LIFETIME_SECS = 3600  # 1 hour in seconds



def handleServerError(e):
  errMsg = str(e)
  if 'setting tls' not in errMsg:
    systemErrorExit(NETWORK_ERROR_RC, errMsg)
  stderrErrorMsg(errMsg)
  writeStderr(Msg.DISABLE_TLS_MIN_MAX)
  systemErrorExit(NETWORK_ERROR_RC, None)

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
    user_agent = GAM_USER_AGENT
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

def get_adc_request():
  request = google.auth.transport.requests.Request()
  if GM.Globals[GM.IS_ON_GCE]:
    return request
  if gce_metadata.is_on_gce(request):
    GM.Globals[GM.IS_ON_GCE] = True
    return request
  return transportCreateRequest()

def _getIAMSigner(service_account_info):
  '''Create an IAM-based signer using Application Default Credentials.

  Returns a google.auth.iam.Signer that signs bytes via the IAM signBlob
  API. This replaces the need for a local private key — signing is
  delegated to Google\'s IAM service using ADC for authentication.
  '''
  request = get_adc_request()
  try:
    credentials, _ = google.auth.default(scopes=[API.IAM_SCOPE],
                                         request=request)
  except (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError) as e:
    systemErrorExit(API_ACCESS_DENIED_RC, str(e))
  triesLimit = 3
  for n in range(1, triesLimit+1):
    try:
      credentials.refresh(request)
      break
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
        continue
      handleServerError(e)
    except google.auth.exceptions.RefreshError as e:
      systemErrorExit(API_ACCESS_DENIED_RC, f'signjwt credentials refresh failed: {e}')
  return google.auth.iam.Signer(request, credentials,
                                service_account_info['client_email'])

# Registry for custom signer factories. Modules register themselves at import
# time (e.g. gam.cmd.yubikey registers a 'yubikey' factory). This eliminates
# the util→cmd dependency that a deferred import would create.
_SIGNER_FACTORIES = {}

def register_signer_factory(key_type, factory):
  """Register a callable that creates a signer for the given key_type.

  The factory signature must be: factory(service_account_info) -> signer
  """
  _SIGNER_FACTORIES[key_type] = factory

def _getSigner(service_account_info):
  '''Return a signer for the given key_type, or None for default keys.

  key_type is read from service_account_info:
    - "default": Returns None (caller should use from_service_account_info)
    - "yubikey": Returns a YubiKey hardware signer (registered by cmd.yubikey)
    - "signjwt": Returns an IAM signBlob signer via ADC
  '''
  key_type = service_account_info.get('key_type', 'default')
  if key_type == 'default':
    return None
  if key_type in _SIGNER_FACTORIES:
    return _SIGNER_FACTORIES[key_type](service_account_info)
  if key_type == 'signjwt':
    return _getIAMSigner(service_account_info)
  return None

def handleOAuthTokenError(e, softErrors, displayError=False, i=0, count=0):
  errMsg = str(e).replace('.', '')
  if ((errMsg in API.OAUTH2_TOKEN_ERRORS) or
      errMsg.startswith('Invalid response') or
      errMsg.startswith('invalid_request: Invalid impersonation &quot;sub&quot; field')):
    if not GM.Globals[GM.CURRENT_SVCACCT_USER]:
      ClientAPIAccessDeniedExit()
    # 403 Forbidden, API disabled, user not enabled
    # 400 Bad Request, user not defined
    if softErrors:
      entityActionFailedWarning([Ent.USER, GM.Globals[GM.CURRENT_SVCACCT_USER], Ent.USER, None], errMsg, i, count)
      return None
    systemErrorExit(SERVICE_NOT_APPLICABLE_RC, Msg.SERVICE_NOT_APPLICABLE_THIS_ADDRESS.format(GM.Globals[GM.CURRENT_SVCACCT_USER]))
  if errMsg in API.OAUTH2_UNAUTHORIZED_ERRORS:
    if not GM.Globals[GM.CURRENT_SVCACCT_USER]:
      ClientAPIAccessDeniedExit()
    # 401 Unauthorized, API disabled, user enabled
    if softErrors:
      if displayError:
        apiOrScopes = API.getAPIName(GM.Globals[GM.CURRENT_SVCACCT_API]) if GM.Globals[GM.CURRENT_SVCACCT_API] else ','.join(sorted(GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES]))
        userServiceNotEnabledWarning(GM.Globals[GM.CURRENT_SVCACCT_USER], apiOrScopes, i, count)
      return None
    SvcAcctAPIAccessDeniedExit()
  if errMsg in API.REFRESH_PERM_ERRORS:
    if softErrors:
      return None
    if not GM.Globals[GM.CURRENT_SVCACCT_USER]:
      expiredRevokedOauth2TxtExit()
  stderrErrorMsg(f'Authentication Token Error - {errMsg}')
  APIAccessDeniedExit()

def getOauth2TxtCredentials(exitOnError=True, api=None, noDASA=False, refreshOnly=False, noScopes=False):
  if not noDASA and GC.Values[GC.ENABLE_DASA]:
    jsonData = readFile(GC.Values[GC.OAUTH2SERVICE_JSON], continueOnError=True, displayError=False)
    if jsonData:
      try:
        if api in API.APIS_NEEDING_ACCESS_TOKEN:
          return (False, getSvcAcctCredentials(API.APIS_NEEDING_ACCESS_TOKEN[api], userEmail=None, forceOauth=True))
        jsonDict = json.loads(jsonData)
        api, _, _ = API.getVersion(api)
        audience = f'https://{api}.googleapis.com/'
        signer = _getSigner(jsonDict)
        if signer is None:
          return (True, JWTCredentials.from_service_account_info(jsonDict, audience=audience))
        return (True, JWTCredentials._from_signer_and_info(signer, jsonDict, audience=audience))
      except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
        invalidOauth2serviceJsonExit(str(e))
    invalidOauth2serviceJsonExit(Msg.NO_DATA)
  jsonData = readFile(GC.Values[GC.OAUTH2_TXT], continueOnError=True, displayError=False)
  if jsonData:
    try:
      jsonDict = json.loads(jsonData)
      if noScopes:
        jsonDict['scopes'] = []
      if 'client_id' in jsonDict:
        if not refreshOnly:
          if set(jsonDict.get('scopes', API.REQUIRED_SCOPES)) == API.REQUIRED_SCOPES_SET:
            if exitOnError:
              systemErrorExit(OAUTH2_TXT_REQUIRED_RC, Msg.NO_CLIENT_ACCESS_ALLOWED)
            return (False, None)
        else:
          GM.Globals[GM.CREDENTIALS_SCOPES] = set(jsonDict.pop('scopes', API.REQUIRED_SCOPES))
        token_expiry = jsonDict.get('token_expiry', REFRESH_EXPIRY)
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
        creds.expiry = arrow.Arrow.strptime(token_expiry, YYYYMMDDTHHMMSSZ_FORMAT, tzinfo='UTC').naive
        return (not noScopes, creds)
      if jsonDict and exitOnError:
        invalidOauth2TxtExit(Msg.INVALID)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      if exitOnError:
        invalidOauth2TxtExit(str(e))
  if exitOnError:
    systemErrorExit(OAUTH2_TXT_REQUIRED_RC, Msg.NO_CLIENT_ACCESS_ALLOWED)
  return (False, None)

def _getValueFromOAuth(field, credentials=None):
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
        stderrErrorMsg(Msg.PLEASE_CORRECT_YOUR_SYSTEM_TIME)
      systemErrorExit(SYSTEM_ERROR_RC, str(e))
  return GM.Globals[GM.DECODED_ID_TOKEN].get(field, UNKNOWN)

def _getAdminEmail():
  if GC.Values[GC.ADMIN_EMAIL]:
    return GC.Values[GC.ADMIN_EMAIL]
  return _getValueFromOAuth('email')

def writeClientCredentials(creds, filename):
  creds_data = {
    'client_id': creds.client_id,
    'client_secret': creds.client_secret,
    'id_token': creds.id_token,
    'refresh_token': creds.refresh_token,
    'scopes': sorted(creds.scopes or GM.Globals[GM.CREDENTIALS_SCOPES]),
    'token': creds.token,
    'token_expiry': creds.expiry.strftime(YYYYMMDDTHHMMSSZ_FORMAT),
    'token_uri': creds.token_uri,
    }
  expected_iss = ['https://accounts.google.com', 'accounts.google.com']
  if _getValueFromOAuth('iss', creds) not in expected_iss:
    systemErrorExit(OAUTH2_TXT_REQUIRED_RC, f'Wrong OAuth 2.0 credentials issuer. Got {_getValueFromOAuth("iss", creds)} expected one of {", ".join(expected_iss)}')
  request = transportCreateRequest()
  try:
    creds_data['decoded_id_token'] = google.oauth2.id_token.verify_oauth2_token(creds.id_token, request,
                                                                                 clock_skew_in_seconds=GC.Values[GC.CLOCK_SKEW_IN_SECONDS])
  except ValueError as e:
    if 'Token used too early' in str(e):
      stderrErrorMsg(Msg.PLEASE_CORRECT_YOUR_SYSTEM_TIME)
    systemErrorExit(SYSTEM_ERROR_RC, str(e))
  GM.Globals[GM.DECODED_ID_TOKEN] = creds_data['decoded_id_token']
  if filename != '-':
    writeFile(filename, json.dumps(creds_data, indent=2, sort_keys=True)+'\n')
  else:
    writeStdout(json.dumps(creds_data, ensure_ascii=False, indent=2, sort_keys=True)+'\n')

def shortenURL(long_url):
  if GC.Values[GC.NO_SHORT_URLS]:
    return long_url
  httpObj = getHttpObj(timeout=10)
  try:
    payload = json.dumps({'long_url': long_url})
    resp, content = httpObj.request(URL_SHORTENER_ENDPOINT, 'POST',
                                    payload,
                                    headers={'Content-Type': 'application/json',
                                             'User-Agent': GAM_USER_AGENT})
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
  def gcloudError():
    writeStderr(f'Failed to run gcloud as {admin_email}. Please make sure it\'s setup')
    e = Msg.REAUTHENTICATION_IS_NEEDED
    handleOAuthTokenError(e, False)

  writeStderr(Msg.CALLING_GCLOUD_FOR_REAUTH)
  if termios is not None:
    old_settings = termios.tcgetattr(sys.stdin)
  admin_email = _getAdminEmail()
  # First makes sure gcloud has a valid access token and thus
  # should also have a valid RAPT token
  try:
    devnull = open(os.devnull, 'w', encoding=UTF8)
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
    if termios is not None:
      termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    printBlankLine()
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
    systemErrorExit(SYSTEM_ERROR_RC,
            'Failed to retrieve reauth token from gcloud. You may need to wait until gcloud is also prompted for reauth.')

def getClientCredentials(forceRefresh=False, forceWrite=False, filename=None, api=None, noDASA=False, refreshOnly=False, noScopes=False):
  """Gets OAuth2 credentials which are guaranteed to be fresh and valid.
     Locks during read and possible write so that only one process will
     attempt refresh/write when running in parallel. """
  lock = FileLock(GM.Globals[GM.OAUTH2_TXT_LOCK], mode=GC.Values[GC.OAUTH2_TXT_LOCK_MODE])
  with lock:
    writeCreds, credentials = getOauth2TxtCredentials(api=api, noDASA=noDASA, refreshOnly=refreshOnly, noScopes=noScopes)
    if not credentials:
      invalidOauth2TxtExit('')
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
            waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
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
  delta = min(2 ** n, 60)+float(random.randint(1, 1000))/1000
  if n > 3:
    writeStderr(f'Temporary error: {error_code} - {error_message}, Backing off: {int(delta)} seconds, Retry: {n}/{triesLimit}\n')
    flushStderr()
  time.sleep(delta)
  if GC.Values[GC.SHOW_API_CALLS_RETRY_DATA]:
    incrAPICallsRetryData(error_message, delta)

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
        systemErrorExit(GOOGLE_API_ERROR_RC, Msg.UNKNOWN_API_OR_VERSION.format(str(e), __author__))
      except (googleapiclient.errors.InvalidJsonError, KeyError, ValueError) as e:
        if n != triesLimit:
          waitOnFailure(n, triesLimit, INVALID_JSON_RC, str(e))
          continue
        systemErrorExit(INVALID_JSON_RC, str(e))
      except (http.client.HTTPException, OSError, googleapiclient.errors.HttpError) as e:
        errMsg = f'Connection error: {str(e) or repr(e)}'
        if n != triesLimit:
          waitOnFailure(n, triesLimit, SOCKET_ERROR_RC, errMsg)
          continue
        systemErrorExit(SOCKET_ERROR_RC, errMsg)
      except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
        if n != triesLimit:
          httpObj.connections = {}
          waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
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
    invalidDiscoveryJsonExit(disc_file, str(e))
  except IOError as e:
    systemErrorExit(FILE_ERROR_RC, str(e))

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
  if not GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
    jsonData = readFile(GC.Values[GC.OAUTH2SERVICE_JSON], continueOnError=True, displayError=True)
    if not jsonData:
      invalidOauth2serviceJsonExit(Msg.NO_DATA)
    try:
      GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = json.loads(jsonData)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      invalidOauth2serviceJsonExit(str(e))
    if not GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
      systemErrorExit(OAUTH2SERVICE_JSON_REQUIRED_RC, Msg.NO_SVCACCT_ACCESS_ALLOWED)
    requiredFields = ['client_email', 'client_id', 'project_id', 'token_uri']
    key_type = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].get('key_type', 'default')
    if key_type == 'default':
      requiredFields.extend(['private_key', 'private_key_id'])
    missingFields = []
    for field in requiredFields:
      if field not in GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]:
        missingFields.append(field)
    if missingFields:
      invalidOauth2serviceJsonExit(Msg.MISSING_FIELDS.format(','.join(missingFields)))
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
      SvcAcctAPIAccessDeniedExit()
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
  svcacct_info = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]
  signer = _getSigner(svcacct_info)
  if not GM.Globals[GM.CURRENT_SVCACCT_API] or scopesOrAPI not in API.JWT_APIS or forceOauth:
    try:
      if signer is None:
        credentials = google.oauth2.service_account.Credentials.from_service_account_info(svcacct_info)
      else:
        credentials = google.oauth2.service_account.Credentials._from_signer_and_info(signer, svcacct_info)
    except (ValueError, IndexError, KeyError) as e:
      if softErrors:
        return None
      invalidOauth2serviceJsonExit(str(e))
    credentials = credentials.with_scopes(GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES])
  else:
    audience = f'https://{scopesOrAPI}.googleapis.com/'
    try:
      if signer is None:
        credentials = JWTCredentials.from_service_account_info(svcacct_info, audience=audience)
      else:
        credentials = JWTCredentials._from_signer_and_info(signer, svcacct_info, audience=audience)
      credentials.project_id = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id']
    except (ValueError, IndexError, KeyError) as e:
      if softErrors:
        return None
      invalidOauth2serviceJsonExit(str(e))
  GM.Globals[GM.CURRENT_SVCACCT_USER] = userEmail
  if userEmail:
    credentials = credentials.with_subject(userEmail)
  GM.Globals[GM.ADMIN] = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']
  GM.Globals[GM.OAUTH2SERVICE_CLIENT_ID] = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_id']
  return credentials




def readDiscoveryFile(api_version):
  disc_filename = f'{api_version}.json'
  disc_file = os.path.join(GM.Globals[GM.GAM_PATH], disc_filename)
  if hasattr(sys, '_MEIPASS'):
    json_string = readFile(os.path.join(sys._MEIPASS, disc_filename), continueOnError=True, displayError=True) #pylint: disable=no-member
  elif os.path.isfile(disc_file):
    json_string = readFile(disc_file, continueOnError=True, displayError=True)
  else:
    json_string = None
  if not json_string:
    invalidDiscoveryJsonExit(disc_file, Msg.NO_DATA)
  try:
    discovery = json.loads(json_string)
    return (disc_file, discovery)
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    invalidDiscoveryJsonExit(disc_file, str(e))

def buildGAPIObject(api, credentials=None):
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
      systemErrorExit(NO_SCOPES_FOR_API_RC, Msg.NO_SCOPES_FOR_API.format(API.getAPIName(api)))
    if not GC.Values[GC.DOMAIN]:
      GC.Values[GC.DOMAIN] = GM.Globals[GM.DECODED_ID_TOKEN].get('hd', 'UNKNOWN').lower()
    if not GC.Values[GC.CUSTOMER_ID]:
      GC.Values[GC.CUSTOMER_ID] = GC.MY_CUSTOMER
    GM.Globals[GM.ADMIN] = GM.Globals[GM.DECODED_ID_TOKEN].get('email', 'UNKNOWN').lower()
    GM.Globals[GM.OAUTH2_CLIENT_ID] = credentials.client_id
  return service

def buildGAPIObjectNoAuthentication(api):
  httpObj = getHttpObj(cache=GM.Globals[GM.CACHE_DIR])
  service = getService(api, httpObj)
  return service


# API access denied handlers (moved from access.py to break cycle)
def ClientAPIAccessDeniedExit(errMsg=None):
  if errMsg is None:
    stderrErrorMsg(Msg.API_ACCESS_DENIED)
    missingScopes = API.getClientScopesSet(GM.Globals[GM.CURRENT_CLIENT_API])-GM.Globals[GM.CURRENT_CLIENT_API_SCOPES]
    if missingScopes:
      writeStderr(Msg.API_CHECK_CLIENT_AUTHORIZATION.format(GM.Globals[GM.OAUTH2_CLIENT_ID],
                                                            ','.join(sorted(missingScopes))))
    systemErrorExit(API_ACCESS_DENIED_RC, None)
  else:
    stderrErrorMsg(errMsg)
    systemErrorExit(API_ACCESS_DENIED_RC, Msg.REAUTHENTICATION_IS_NEEDED)


def SvcAcctAPIAccessDenied():
  _getSvcAcctData()
  if (GM.Globals[GM.CURRENT_SVCACCT_API] == API.GMAIL and
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES] and
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES][0] == API.GMAIL_SEND_SCOPE):
    systemErrorExit(OAUTH2SERVICE_JSON_REQUIRED_RC, Msg.NO_SVCACCT_ACCESS_ALLOWED)
  stderrErrorMsg(Msg.API_ACCESS_DENIED)
  apiOrScopes = API.getAPIName(GM.Globals[GM.CURRENT_SVCACCT_API]) if GM.Globals[GM.CURRENT_SVCACCT_API] else ','.join(sorted(GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES]))
  writeStderr(Msg.API_CHECK_SVCACCT_AUTHORIZATION.format(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_id'],
                                                         apiOrScopes,
                                                         GM.Globals[GM.CURRENT_SVCACCT_USER] or _getAdminEmail()))

def SvcAcctAPIAccessDeniedExit():
  SvcAcctAPIAccessDenied()
  systemErrorExit(API_ACCESS_DENIED_RC, None)


def SvcAcctAPIDisabledExit():
  if not GM.Globals[GM.CURRENT_SVCACCT_USER] and GM.Globals[GM.CURRENT_CLIENT_API]:
    ClientAPIAccessDeniedExit()
  if GM.Globals[GM.CURRENT_SVCACCT_API]:
    stderrErrorMsg(Msg.SERVICE_ACCOUNT_API_DISABLED.format(API.getAPIName(GM.Globals[GM.CURRENT_SVCACCT_API])))
    systemErrorExit(API_ACCESS_DENIED_RC, None)
  systemErrorExit(API_ACCESS_DENIED_RC, Msg.API_ACCESS_DENIED)


def APIAccessDeniedExit():
  if not GM.Globals[GM.CURRENT_SVCACCT_USER] and GM.Globals[GM.CURRENT_CLIENT_API]:
    ClientAPIAccessDeniedExit()
  if GM.Globals[GM.CURRENT_SVCACCT_API]:
    SvcAcctAPIAccessDeniedExit()
  systemErrorExit(API_ACCESS_DENIED_RC, Msg.API_ACCESS_DENIED)


