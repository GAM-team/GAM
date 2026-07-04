"""Low-level Google API call wrappers with retry logic.

Contains callGAPI/callGAPIpages/callGData and their error-checking
helpers. Separated from api.py (which handles auth/credentials/service
construction) to break the api<->uid circular dependency.
"""

import http.client
import json
import re
import ssl
import sys
import time

import googleapiclient.errors
import httplib2

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import gdata as GDATA
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Ent
from gam.constants import GOOGLE_API_ERROR_RC, HTTP_ERROR_RC, NETWORK_ERROR_RC, SOCKET_ERROR_RC, SYSTEM_ERROR_RC
from util.api import APIAccessDeniedExit, clearServiceCache, getGDataOAuthToken, getHttpObj, handleOAuthTokenError, handleServerError, transportCreateRequest, waitOnFailure
from util.args import UTF8, formatHTTPError
from util.display import FIRST_ITEM_MARKER, LAST_ITEM_MARKER, SERVICE_NOT_APPLICABLE_RC, TOTAL_ITEMS_MARKER, entityActionFailedWarning, printKeyValueList, userServiceNotEnabledWarning
from util.errors import INVALID_JSON_RC
from util.fileio import checkAPICallsRate, incrAPICallsRetryData
from util.output import ERROR_PREFIX, flushStderr, setSysExitRC, stderrErrorMsg, systemErrorExit, writeStderr, writeStdout

HTML_TITLE_PATTERN = re.compile(r'.*<title>(.+)</title>')

def checkGDataError(e, service):
  error = e.args
  reason = error[0].get('reason', '')
  body = error[0].get('body', '').decode(UTF8)
  # First check for errors that need special handling
  if reason in ['Token invalid - Invalid token: Stateless token expired', 'Token invalid - Invalid token: Token not found', 'gone']:
    keep_domain = service.domain
    getGDataOAuthToken(service)
    service.domain = keep_domain
    return (GDATA.TOKEN_EXPIRED, reason)
  error_code = getattr(e, 'error_code', 600)
  if GC.Values[GC.DEBUG_LEVEL] > 0:
    writeStdout(f'{ERROR_PREFIX} {error_code}: {reason}, {body}\n')
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
  if throwErrors is None:
    throwErrors = []
  if retryErrors is None:
    retryErrors = []
  if triesLimit == 0:
    triesLimit = GC.Values[GC.API_CALLS_TRIES_LIMIT]
  allRetryErrors = GDATA.NON_TERMINATING_ERRORS+retryErrors
  method = getattr(service, function)
  if GC.Values[GC.API_CALLS_RATE_CHECK]:
    checkAPICallsRate()
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
        stderrErrorMsg(f'{error_code} - {error_message}{["", ": Giving up."][n > 1]}')
        return None
      if error_code == GDATA.INSUFFICIENT_PERMISSIONS:
        APIAccessDeniedExit()
      systemErrorExit(GOOGLE_API_ERROR_RC, f'{error_code} - {error_message}')
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
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
        waitOnFailure(n, triesLimit, SOCKET_ERROR_RC, errMsg)
        continue
      if softErrors:
        writeStderr(f'\n{ERROR_PREFIX}{errMsg} - Giving up.\n')
        return None
      systemErrorExit(SOCKET_ERROR_RC, errMsg)

def writeGotMessage(msg):
  if GC.Values[GC.SHOW_GETTINGS_GOT_NL]:
    writeStderr(msg)
  else:
    writeStderr('\r')
    msgLen = len(msg)
    if msgLen < GM.Globals[GM.LAST_GOT_MSG_LEN]:
      writeStderr(msg+' '*(GM.Globals[GM.LAST_GOT_MSG_LEN]-msgLen))
    else:
      writeStderr(msg)
    GM.Globals[GM.LAST_GOT_MSG_LEN] = msgLen
  flushStderr()

def callGDataPages(service, function,
                   pageMessage=None,
                   softErrors=False, throwErrors=None, retryErrors=None,
                   uri=None,
                   **kwargs):
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
      show_message = pageMessage.replace(TOTAL_ITEMS_MARKER, str(totalItems))
      writeGotMessage(show_message.format(Ent.ChooseGetting(totalItems)))
    if nextLink is None:
      if pageMessage and (pageMessage[-1] != '\n'):
        writeStderr('\r\n')
        flushStderr()
      return allResults
    uri = nextLink.href
    if 'url_params' in kwargs:
      kwargs['url_params'].pop('start-index', None)

def checkGAPIError(e, softErrors=False, retryOnHttpError=False, mapNotFound=True):
  def makeErrorDict(code, reason, message):
    return {'error': {'code': code, 'errors': [{'reason': reason, 'message': message}]}}

  try:
    error = json.loads(e.content.decode(UTF8))
    if GC.Values[GC.DEBUG_LEVEL] > 0:
      writeStdout(f'{ERROR_PREFIX} JSON: {str(error)}\n')
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
    eContent = e.content.decode(UTF8) if isinstance(e.content, bytes) else e.content
    lContent = eContent.lower()
    if GC.Values[GC.DEBUG_LEVEL] > 0:
      writeStdout(f'{ERROR_PREFIX} HTTP: {str(eContent)}\n')
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
      tg = HTML_TITLE_PATTERN.match(lContent)
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
      stderrErrorMsg(eContent)
      return (0, None, None)
    else:
      systemErrorExit(HTTP_ERROR_RC, eContent)
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
        systemErrorExit(GOOGLE_API_ERROR_RC, str(error))
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, str(error))
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
    checkAPICallsRate()
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
          systemErrorExit(HTTP_ERROR_RC, message)
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
        stderrErrorMsg(f'{http_status}: {reason} - {message}{["", ": Giving up."][n > 1]}')
        return None
      if reason == GAPI.INSUFFICIENT_PERMISSIONS:
        APIAccessDeniedExit()
      systemErrorExit(HTTP_ERROR_RC, formatHTTPError(http_status, reason, message))
    except googleapiclient.errors.MediaUploadSizeError as e:
      raise e
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        service._http.connections = {}
        waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
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
        waitOnFailure(n, triesLimit, SOCKET_ERROR_RC, errMsg)
        continue
      if softErrors:
        writeStderr(f'\n{ERROR_PREFIX}{errMsg} - Giving up.\n')
        return None
      systemErrorExit(SOCKET_ERROR_RC, errMsg)
    except ValueError as e:
      if clearServiceCache(service):
        continue
      systemErrorExit(GOOGLE_API_ERROR_RC, str(e))
    except TypeError as e:
      systemErrorExit(GOOGLE_API_ERROR_RC, str(e))

def _showGAPIpagesResult(results, pageItems, totalItems, pageMessage, messageAttribute, entityType):
  showMessage = pageMessage.replace(TOTAL_ITEMS_MARKER, str(totalItems))
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
      showMessage = showMessage.replace(FIRST_ITEM_MARKER, firstItem)
      showMessage = showMessage.replace(LAST_ITEM_MARKER, lastItem)
  else:
    showMessage = showMessage.replace(FIRST_ITEM_MARKER, '')
    showMessage = showMessage.replace(LAST_ITEM_MARKER, '')
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
  if pageMessage and (pageMessage[-1] != '\n'):
    writeStderr('\r\n')
    flushStderr()

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
