"""GAPI and OAuth Token related errors methods."""

from enum import Enum
import json

import controlflow
import display  # TODO: Change to relative import when gam is setup as a package
from var import UTF8


class GapiAbortedError(Exception):
  pass


class GapiAuthErrorError(Exception):
  pass


class GapiBadGatewayError(Exception):
  pass


class GapiBadRequestError(Exception):
  pass


class GapiConditionNotMetError(Exception):
  pass


class GapiCyclicMembershipsNotAllowedError(Exception):
  pass


class GapiDomainCannotUseApisError(Exception):
  pass


class GapiDomainNotFoundError(Exception):
  pass


class GapiDuplicateError(Exception):
  pass


class GapiFailedPreconditionError(Exception):
  pass


class GapiForbiddenError(Exception):
  pass


class GapiGatewayTimeoutError(Exception):
  pass


class GapiGroupNotFoundError(Exception):
  pass


class GapiInvalidError(Exception):
  pass


class GapiInvalidArgumentError(Exception):
  pass


class GapiInvalidMemberError(Exception):
  pass


class GapiMemberNotFoundError(Exception):
  pass


class GapiNotFoundError(Exception):
  pass


class GapiNotImplementedError(Exception):
  pass


class GapiPermissionDeniedError(Exception):
  pass


class GapiResourceNotFoundError(Exception):
  pass


class GapiServiceNotAvailableError(Exception):
  pass


class GapiUserNotFoundError(Exception):
  pass


# GAPI Error Reasons
class ErrorReason(Enum):
  """The reason why a non-200 HTTP response was returned from a GAPI."""
  ABORTED = 'aborted'
  AUTH_ERROR = 'authError'
  BACKEND_ERROR = 'backendError'
  BAD_GATEWAY = 'badGateway'
  BAD_REQUEST = 'badRequest'
  CONDITION_NOT_MET = 'conditionNotMet'
  CYCLIC_MEMBERSHIPS_NOT_ALLOWED = 'cyclicMembershipsNotAllowed'
  DOMAIN_CANNOT_USE_APIS = 'domainCannotUseApis'
  DOMAIN_NOT_FOUND = 'domainNotFound'
  DUPLICATE = 'duplicate'
  FAILED_PRECONDITION = 'failedPrecondition'
  FORBIDDEN = 'forbidden'
  FOUR_O_THREE = '403'
  GATEWAY_TIMEOUT = 'gatewayTimeout'
  GROUP_NOT_FOUND = 'groupNotFound'
  INTERNAL_ERROR = 'internalError'
  INVALID = 'invalid'
  INVALID_ARGUMENT = 'invalidArgument'
  INVALID_MEMBER = 'invalidMember'
  MEMBER_NOT_FOUND = 'memberNotFound'
  NOT_FOUND = 'notFound'
  NOT_IMPLEMENTED = 'notImplemented'
  PERMISSION_DENIED = 'permissionDenied'
  QUOTA_EXCEEDED = 'quotaExceeded'
  RATE_LIMIT_EXCEEDED = 'rateLimitExceeded'
  RESOURCE_NOT_FOUND = 'resourceNotFound'
  SERVICE_NOT_AVAILABLE = 'serviceNotAvailable'
  SERVICE_LIMIT = 'serviceLimit'
  SYSTEM_ERROR = 'systemError'
  USER_NOT_FOUND = 'userNotFound'
  USER_RATE_LIMIT_EXCEEDED = 'userRateLimitExceeded'
  FOUR_TWO_NINE = '429'
  DAILY_LIMIT_EXCEEDED = 'dailyLimitExceeded'

  def __str__(self):
    return str(self.value)


# Common sets of GAPI error reasons
DEFAULT_RETRY_REASONS = [
  ErrorReason.QUOTA_EXCEEDED, ErrorReason.RATE_LIMIT_EXCEEDED,
  ErrorReason.USER_RATE_LIMIT_EXCEEDED, ErrorReason.BACKEND_ERROR,
  ErrorReason.BAD_GATEWAY, ErrorReason.GATEWAY_TIMEOUT,
  ErrorReason.INTERNAL_ERROR, ErrorReason.FOUR_TWO_NINE,
  ]
GMAIL_THROW_REASONS = [ErrorReason.SERVICE_NOT_AVAILABLE]
GROUP_GET_THROW_REASONS = [
  ErrorReason.GROUP_NOT_FOUND, ErrorReason.DOMAIN_NOT_FOUND,
  ErrorReason.DOMAIN_CANNOT_USE_APIS, ErrorReason.FORBIDDEN,
  ErrorReason.BAD_REQUEST
  ]
GROUP_GET_RETRY_REASONS = [ErrorReason.INVALID, ErrorReason.SYSTEM_ERROR]
MEMBERS_THROW_REASONS = [
  ErrorReason.GROUP_NOT_FOUND, ErrorReason.DOMAIN_NOT_FOUND,
  ErrorReason.DOMAIN_CANNOT_USE_APIS, ErrorReason.INVALID,
  ErrorReason.FORBIDDEN
  ]
MEMBERS_RETRY_REASONS = [ErrorReason.SYSTEM_ERROR]

# A map of GAPI error reasons to the corresponding GAM Python Exception
ERROR_REASON_TO_EXCEPTION = {
  ErrorReason.ABORTED:
    GapiAbortedError,
  ErrorReason.AUTH_ERROR:
    GapiAuthErrorError,
  ErrorReason.BAD_GATEWAY:
    GapiBadGatewayError,
  ErrorReason.BAD_REQUEST:
    GapiBadRequestError,
  ErrorReason.CONDITION_NOT_MET:
    GapiConditionNotMetError,
  ErrorReason.CYCLIC_MEMBERSHIPS_NOT_ALLOWED:
    GapiCyclicMembershipsNotAllowedError,
  ErrorReason.DOMAIN_CANNOT_USE_APIS:
    GapiDomainCannotUseApisError,
  ErrorReason.DOMAIN_NOT_FOUND:
    GapiDomainNotFoundError,
  ErrorReason.DUPLICATE:
    GapiDuplicateError,
  ErrorReason.FAILED_PRECONDITION:
    GapiFailedPreconditionError,
  ErrorReason.FORBIDDEN:
    GapiForbiddenError,
  ErrorReason.GATEWAY_TIMEOUT:
    GapiGatewayTimeoutError,
  ErrorReason.GROUP_NOT_FOUND:
    GapiGroupNotFoundError,
  ErrorReason.INVALID:
    GapiInvalidError,
  ErrorReason.INVALID_ARGUMENT:
    GapiInvalidArgumentError,
  ErrorReason.INVALID_MEMBER:
    GapiInvalidMemberError,
  ErrorReason.MEMBER_NOT_FOUND:
    GapiMemberNotFoundError,
  ErrorReason.NOT_FOUND:
    GapiNotFoundError,
  ErrorReason.NOT_IMPLEMENTED:
    GapiNotImplementedError,
  ErrorReason.PERMISSION_DENIED:
    GapiPermissionDeniedError,
  ErrorReason.RESOURCE_NOT_FOUND:
    GapiResourceNotFoundError,
  ErrorReason.SERVICE_NOT_AVAILABLE:
    GapiServiceNotAvailableError,
  ErrorReason.USER_NOT_FOUND:
    GapiUserNotFoundError,
  }

# OAuth Token Errors
OAUTH2_TOKEN_ERRORS = [
  'access_denied',
  'access_denied: Requested client not authorized',
  'internal_failure: Backend Error',
  'internal_failure: None',
  'invalid_grant',
  'invalid_grant: Bad Request',
  'invalid_grant: Invalid email or User ID',
  'invalid_grant: Not a valid email',
  'invalid_grant: Invalid JWT: No valid verifier found for issuer',
  'invalid_request: Invalid impersonation prn email address',
  'unauthorized_client: Client is unauthorized to retrieve access tokens '
  'using this method',
  'unauthorized_client: Client is unauthorized to retrieve access tokens '
  'using this method, or client not authorized for any of the scopes '
  'requested',
  'unauthorized_client: Unauthorized client or scope in request',
  ]


def _create_http_error_dict(status_code, reason, message):
  """Creates a basic error dict similar to most Google API Errors.

  Args:
    status_code: Int, the error's HTTP response status code.
    reason: String, a camelCase reason for the HttpError being given.
    message: String, a general error message describing the error that occurred.

  Returns:
    dict
  """
  return {
    'error': {
      'code': status_code,
      'errors': [{
        'reason': str(reason),
        'message': message,
        }]
      }
  }


def get_gapi_error_detail(e,
                          soft_errors=False,
                          silent_errors=False,
                          retry_on_http_error=False):
  """Extracts error detail from a non-200 GAPI Response.

  Args:
    e: googleapiclient.HttpError, The HTTP Error received.
    soft_errors: Boolean, If true, causes error messages to be surpressed,
      rather than sending them to stderr.
    silent_errors: Boolean, If true, suppresses and ignores any errors from
      being displayed
    retry_on_http_error: Boolean, If true, will return -1 as the HTTP Response
      code, indicating that the request can be retried. TODO: Remove this param,
        as it seems to be outside the scope of this method.

  Returns:
    A tuple containing the HTTP Response code, GAPI error reason, and error
        message.
  """
  try:
    error = json.loads(e.content.decode(UTF8))
  except ValueError:
    error_content = e.content.decode(UTF8) if isinstance(e.content,
                                                         bytes) else e.content
    if (e.resp['status'] == '503') and (
        error_content == 'Quota exceeded for the current request'):
      return (e.resp['status'], ErrorReason.QUOTA_EXCEEDED.value, error_content)
    if (e.resp['status'] == '403') and (
        error_content.startswith('Request rate higher than configured')):
      return (e.resp['status'], ErrorReason.QUOTA_EXCEEDED.value, error_content)
    if (e.resp['status'] == '502') and ('Bad Gateway' in error_content):
      return (e.resp['status'], ErrorReason.BAD_GATEWAY.value, error_content)
    if (e.resp['status'] == '504') and ('Gateway Timeout' in error_content):
      return (e.resp['status'], ErrorReason.GATEWAY_TIMEOUT.value, error_content)
    if (e.resp['status'] == '403') and ('Invalid domain.' in error_content):
      error = _create_http_error_dict(403, ErrorReason.NOT_FOUND.value,
                                      'Domain not found')
    elif (e.resp['status'] == '400') and (
        'InvalidSsoSigningKey' in error_content):
      error = _create_http_error_dict(400, ErrorReason.INVALID.value,
                                      'InvalidSsoSigningKey')
    elif (e.resp['status'] == '400') and ('UnknownError' in error_content):
      error = _create_http_error_dict(400, ErrorReason.INVALID.value,
                                      'UnknownError')
    elif retry_on_http_error:
      return (-1, None, None)
    elif soft_errors:
      if not silent_errors:
        display.print_error(error_content)
      return (0, None, None)
    else:
      controlflow.system_error_exit(5, error_content)
    # END: ValueError catch

  if 'error' in error:
    http_status = error['error']['code']
    try:
      message = error['error']['errors'][0]['message']
    except KeyError:
      message = error['error']['message']
  else:
    if 'error_description' in error:
      if error['error_description'] == 'Invalid Value':
        message = error['error_description']
        http_status = 400
        error = _create_http_error_dict(400, ErrorReason.INVALID.value, message)
      else:
        controlflow.system_error_exit(4, str(error))
    else:
      controlflow.system_error_exit(4, str(error))

  # Extract the error reason
  try:
    reason = error['error']['errors'][0]['reason']
    if reason == 'notFound':
      if 'userKey' in message:
        reason = ErrorReason.USER_NOT_FOUND.value
      elif 'groupKey' in message:
        reason = ErrorReason.GROUP_NOT_FOUND.value
      elif 'memberKey' in message:
        reason = ErrorReason.MEMBER_NOT_FOUND.value
      elif 'Domain not found' in message:
        reason = ErrorReason.DOMAIN_NOT_FOUND.value
      elif 'Resource Not Found' in message:
        reason = ErrorReason.RESOURCE_NOT_FOUND.value
    elif reason == 'invalid':
      if 'userId' in message:
        reason = ErrorReason.USER_NOT_FOUND.value
      elif 'memberKey' in message:
        reason = ErrorReason.INVALID_MEMBER.value
    elif reason == 'failedPrecondition':
      if 'Bad Request' in message:
        reason = ErrorReason.BAD_REQUEST.value
      elif 'Mail service not enabled' in message:
        reason = ErrorReason.SERVICE_NOT_AVAILABLE.value
    elif reason == 'required':
      if 'memberKey' in message:
        reason = ErrorReason.MEMBER_NOT_FOUND.value
    elif reason == 'conditionNotMet':
      if 'Cyclic memberships not allowed' in message:
        reason = ErrorReason.CYCLIC_MEMBERSHIPS_NOT_ALLOWED.value
  except KeyError:
    reason = f'{http_status}'
  return (http_status, reason, message)
