"""Methods related to execution of GAPI requests."""

import controlflow
import display
from gapi import errors
import googleapiclient.errors
import httplib2
from var import (GC_CA_FILE, GC_Values, GC_TLS_MIN_VERSION, GC_TLS_MAX_VERSION,
                 GM_Globals, GM_CURRENT_API_SCOPES, GM_CURRENT_API_USER,
                 GM_EXTRA_ARGS_DICT, GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID,
                 MESSAGE_API_ACCESS_CONFIG, MESSAGE_API_ACCESS_DENIED,
                 MESSAGE_SERVICE_NOT_APPLICABLE)
import google.auth.exceptions


def create_http(cache=None,
                timeout=None,
                override_min_tls=None,
                override_max_tls=None):
  """Creates a uniform HTTP transport object.

  Args:
    cache: The HTTP cache to use.
    timeout: The cache timeout, in seconds.
    override_min_tls: The minimum TLS version to require. If not provided, the
      default is used.
    override_max_tls: The maximum TLS version to require. If not provided, the
      default is used.

  Returns:
    httplib2.Http with the specified options.
  """
  tls_minimum_version = override_min_tls if override_min_tls else GC_Values[
      GC_TLS_MIN_VERSION]
  tls_maximum_version = override_max_tls if override_max_tls else GC_Values[
      GC_TLS_MAX_VERSION]
  return httplib2.Http(
      ca_certs=GC_Values[GC_CA_FILE],
      tls_maximum_version=tls_maximum_version,
      tls_minimum_version=tls_minimum_version,
      cache=cache,
      timeout=timeout)


def call(service,
         function,
         silent_errors=False,
         soft_errors=False,
         throw_reasons=None,
         retry_reasons=None,
         **kwargs):
  """Executes a single request on a Google service function.

  Args:
    service: A Google service object for the desired API.
    function: String, The name of a service request method to execute.
    silent_errors: Bool, If True, error messages are suppressed when
      encountered.
    soft_errors: Bool, If True, writes non-fatal errors to stderr.
    throw_reasons: A list of Google HTTP error reason strings indicating the
      errors generated by this request should be re-thrown. All other HTTP
      errors are consumed.
    retry_reasons: A list of Google HTTP error reason strings indicating which
      error should be retried, using exponential backoff techniques, when the
      error reason is encountered.
    **kwargs: Additional params to pass to the request method.

  Returns:
    A response object for the corresponding Google API call.
  """
  if throw_reasons is None:
    throw_reasons = []
  if retry_reasons is None:
    retry_reasons = []

  method = getattr(service, function)
  retries = 10
  parameters = dict(
      list(kwargs.items()) + list(GM_Globals[GM_EXTRA_ARGS_DICT].items()))
  for n in range(1, retries + 1):
    try:
      return method(**parameters).execute()
    except googleapiclient.errors.HttpError as e:
      http_status, reason, message = errors.get_gapi_error_detail(
          e,
          soft_errors=soft_errors,
          silent_errors=silent_errors,
          retry_on_http_error=n < 3)
      if http_status == -1:
        # The error detail indicated that we should retry this request
        # We'll refresh credentials and make another pass
        service._http.request.credentials.refresh(create_http())
        continue
      if http_status == 0:
        return None

      is_known_error_reason = reason in [r.value for r in errors.ErrorReason]
      if is_known_error_reason and errors.ErrorReason(reason) in throw_reasons:
        if errors.ErrorReason(reason) in errors.ERROR_REASON_TO_EXCEPTION:
          raise errors.ERROR_REASON_TO_EXCEPTION[errors.ErrorReason(reason)](
              message)
        else:
          raise e
      if (n != retries) and (is_known_error_reason and errors.ErrorReason(
          reason) in errors.DEFAULT_RETRY_REASONS + retry_reasons):
        controlflow.wait_on_failure(n, retries, reason)
        continue
      if soft_errors:
        display.print_error('{0}: {1} - {2}{3}'.format(http_status, message,
                                                       reason,
                                                       ['',
                                                        ': Giving up.'][n > 1]))
        return None
      controlflow.system_error_exit(
          int(http_status), '{0}: {1} - {2}'.format(http_status, message,
                                                    reason))
    except google.auth.exceptions.RefreshError as e:
      handle_oauth_token_error(
          e, soft_errors or
          errors.ErrorReason.SERVICE_NOT_AVAILABLE in throw_reasons)
      if errors.ErrorReason.SERVICE_NOT_AVAILABLE in throw_reasons:
        raise errors.GapiServiceNotAvailableError(str(e))
      display.print_error('User {0}: {1}'.format(
          GM_Globals[GM_CURRENT_API_USER], str(e)))
      return None
    except ValueError as e:
      if service._http.cache is not None:
        service._http.cache = None
        continue
      controlflow.system_error_exit(4, str(e))
    except (httplib2.ServerNotFoundError, RuntimeError) as e:
      if n != retries:
        service._http.connections = {}
        controlflow.wait_on_failure(n, retries, str(e))
        continue
      controlflow.system_error_exit(4, str(e))
    except TypeError as e:
      controlflow.system_error_exit(4, str(e))


def get_first_page(service,
                   function,
                   items='items',
                   throw_reasons=None,
                   retry_reasons=None,
                   **kwargs):
  """Gets a single page of items from a Google service function that is paged.

  Args:
    service: A Google service object for the desired API.
    function: String, The name of a service request method to execute.
    items: String, the name of the resulting "items" field within the service
      method's response object.
    throw_reasons: A list of Google HTTP error reason strings indicating the
      errors generated by this request should be re-thrown. All other HTTP
      errors are consumed.
    retry_reasons: A list of Google HTTP error reason strings indicating which
      error should be retried, using exponential backoff techniques, when the
      error reason is encountered.
    **kwargs: Additional params to pass to the request method.

  Returns:
    The list of items in the first page of a response.
  """
  results = call(
      service,
      function,
      throw_reasons=throw_reasons,
      retry_reasons=retry_reasons,
      **kwargs)
  if results:
    return results.get(items, [])
  return []


# TODO: Make this private once all execution related items that use this method
# have been brought into this file
def handle_oauth_token_error(e, soft_errors):
  """On a token error, exits the application and writes a message to stderr.

  Args:
    e: google.auth.exceptions.RefreshError, The error to handle.
    soft_errors: Boolean, if True, suppresses any applicable errors and instead
      returns to the caller.
  """
  token_error = str(e).replace('.', '')
  if token_error in errors.OAUTH2_TOKEN_ERRORS or e.startswith(
      'Invalid response'):
    if soft_errors:
      return
    if not GM_Globals[GM_CURRENT_API_USER]:
      display.print_error(
          MESSAGE_API_ACCESS_DENIED.format(
              GM_Globals[GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID],
              ','.join(GM_Globals[GM_CURRENT_API_SCOPES])))
      controlflow.system_error_exit(12, MESSAGE_API_ACCESS_CONFIG)
    else:
      controlflow.system_error_exit(
          19,
          MESSAGE_SERVICE_NOT_APPLICABLE.format(
              GM_Globals[GM_CURRENT_API_USER]))
  controlflow.system_error_exit(18,
                                'Authentication Token Error - {0}'.format(e))
