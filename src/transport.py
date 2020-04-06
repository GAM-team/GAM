"""Methods related to network transport."""

import google_auth_httplib2
import httplib2

from var import GAM_INFO
from var import GC_CA_FILE
from var import GC_TLS_MAX_VERSION
from var import GC_TLS_MIN_VERSION
from var import GC_Values


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
  tls_minimum_version = override_min_tls if override_min_tls else GC_Values.get(
      GC_TLS_MIN_VERSION)
  tls_maximum_version = override_max_tls if override_max_tls else GC_Values.get(
      GC_TLS_MAX_VERSION)
  httpObj = httplib2.Http(
      ca_certs=GC_Values.get(GC_CA_FILE),
      tls_maximum_version=tls_maximum_version,
      tls_minimum_version=tls_minimum_version,
      cache=cache,
      timeout=timeout)
  httpObj.redirect_codes = set(httpObj.redirect_codes) - {308}
  return httpObj


def create_request(http=None):
  """Creates a uniform Request object with a default http, if not provided.

  Args:
    http: Optional httplib2.Http compatible object to be used with the request.
      If not provided, a default HTTP will be used.

  Returns:
    Request: A google_auth_httplib2.Request compatible Request.
  """
  if not http:
    http = create_http()
  return Request(http)


GAM_USER_AGENT = GAM_INFO


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
            kwargs['headers']['user-agent'] = (
                f'{user_agent} '
                f'{kwargs["headers"]["user-agent"]}')
        else:
          kwargs['headers']['user-agent'] = user_agent
      else:
        kwargs['headers'] = {'user-agent': user_agent}
      return request_method(*args, **kwargs)

    return wrapped_request_method

  return decorator


class Request(google_auth_httplib2.Request):
  """A Request which forces a user agent."""

  @_force_user_agent(GAM_USER_AGENT)
  def __call__(self, *args, **kwargs):
    """Inserts the GAM user-agent header in requests."""
    return super(Request, self).__call__(*args, **kwargs)


class AuthorizedHttp(google_auth_httplib2.AuthorizedHttp):
  """An AuthorizedHttp which forces a user agent during requests."""

  @_force_user_agent(GAM_USER_AGENT)
  def request(self, *args, **kwargs):
    """Inserts the GAM user-agent header in requests."""
    return super(AuthorizedHttp, self).request(*args, **kwargs)
