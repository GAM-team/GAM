#!/usr/bin/python
#
# Copyright (C) 2006,2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""GDataService provides CRUD ops. and programmatic login for GData services.

  Error: A base exception class for all exceptions in the gdata_client
         module.

  CaptchaRequired: This exception is thrown when a login attempt results in a
                   captcha challenge from the ClientLogin service. When this
                   exception is thrown, the captcha_token and captcha_url are
                   set to the values provided in the server's response.

  BadAuthentication: Raised when a login attempt is made with an incorrect
                     username or password.

  NotAuthenticated: Raised if an operation requiring authentication is called
                    before a user has authenticated.

  NonAuthSubToken: Raised if a method to modify an AuthSub token is used when
                   the user is either not authenticated or is authenticated
                   through another authentication mechanism.

  NonOAuthToken: Raised if a method to modify an OAuth token is used when the
                 user is either not authenticated or is authenticated through
                 another authentication mechanism.

  RequestError: Raised if a CRUD request returned a non-success code.

  UnexpectedReturnType: Raised if the response from the server was not of the
                        desired type. For example, this would be raised if the
                        server sent a feed when the client requested an entry.

  GDataService: Encapsulates user credentials needed to perform insert, update
                and delete operations with the GData API. An instance can
                perform user authentication, query, insertion, deletion, and 
                update.

  Query: Eases query URI creation by allowing URI parameters to be set as 
         dictionary attributes. For example a query with a feed of 
         '/base/feeds/snippets' and ['bq'] set to 'digital camera' will 
         produce '/base/feeds/snippets?bq=digital+camera' when .ToUri() is 
         called on it.
"""


__author__ = 'api.jscudder (Jeffrey Scudder)'

import re
import urllib
import urlparse
try:
  from xml.etree import cElementTree as ElementTree
except ImportError:
  try:
    import cElementTree as ElementTree
  except ImportError:
    try:
      from xml.etree import ElementTree
    except ImportError:
      from elementtree import ElementTree
import atom.service
import gdata
import atom
import atom.http_interface
import atom.token_store
import gdata.auth
import gdata.gauth


AUTH_SERVER_HOST = 'https://www.google.com'


# When requesting an AuthSub token, it is often helpful to track the scope
# which is being requested. One way to accomplish this is to add a URL 
# parameter to the 'next' URL which contains the requested scope. This
# constant is the default name (AKA key) for the URL parameter.
SCOPE_URL_PARAM_NAME = 'authsub_token_scope'
# When requesting an OAuth access token or authorization of an existing OAuth
# request token, it is often helpful to track the scope(s) which is/are being
# requested. One way to accomplish this is to add a URL parameter to the
# 'callback' URL which contains the requested scope. This constant is the
# default name (AKA key) for the URL parameter.
OAUTH_SCOPE_URL_PARAM_NAME = 'oauth_token_scope'
# Maps the service names used in ClientLogin to scope URLs.
CLIENT_LOGIN_SCOPES = gdata.gauth.AUTH_SCOPES
# Default parameters for GDataService.GetWithRetries method
DEFAULT_NUM_RETRIES = 3
DEFAULT_DELAY = 1
DEFAULT_BACKOFF = 2


def lookup_scopes(service_name):
  """Finds the scope URLs for the desired service.

  In some cases, an unknown service may be used, and in those cases this
  function will return None.
  """
  if service_name in CLIENT_LOGIN_SCOPES:
    return CLIENT_LOGIN_SCOPES[service_name]
  return None


# Module level variable specifies which module should be used by GDataService
# objects to make HttpRequests. This setting can be overridden on each 
# instance of GDataService.
# This module level variable is deprecated. Reassign the http_client member
# of a GDataService object instead.
http_request_handler = atom.service


class Error(Exception):
  pass


class CaptchaRequired(Error):
  pass


class BadAuthentication(Error):
  pass


class NotAuthenticated(Error):
  pass


class NonAuthSubToken(Error):
  pass


class NonOAuthToken(Error):
  pass


class RequestError(Error):
  pass


class UnexpectedReturnType(Error):
  pass


class BadAuthenticationServiceURL(Error):
  pass


class FetchingOAuthRequestTokenFailed(RequestError):
  pass


class TokenUpgradeFailed(RequestError):
  pass


class RevokingOAuthTokenFailed(RequestError):
  pass


class AuthorizationRequired(Error):
  pass


class TokenHadNoScope(Error):
  pass


class RanOutOfTries(Error):
  pass


class GDataService(atom.service.AtomService):
  """Contains elements needed for GData login and CRUD request headers.

  Maintains additional headers (tokens for example) needed for the GData 
  services to allow a user to perform inserts, updates, and deletes.
  """
  # The hander member is deprecated, use http_client instead.
  handler = None
  # The auth_token member is deprecated, use the token_store instead.
  auth_token = None
  # The tokens dict is deprecated in favor of the token_store.
  tokens = None

  def __init__(self, email=None, password=None, account_type='HOSTED_OR_GOOGLE',
               service=None, auth_service_url=None, source=None, server=None, 
               additional_headers=None, handler=None, tokens=None,
               http_client=None, token_store=None):
    """Creates an object of type GDataService.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      account_type: string (optional) The type of account to use. Use
          'GOOGLE' for regular Google accounts or 'HOSTED' for Google
          Apps accounts, or 'HOSTED_OR_GOOGLE' to try finding a HOSTED
          account first and, if it doesn't exist, try finding a regular
          GOOGLE account. Default value: 'HOSTED_OR_GOOGLE'.
      service: string (optional) The desired service for which credentials
          will be obtained.
      auth_service_url: string (optional) User-defined auth token request URL
          allows users to explicitly specify where to send auth token requests.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'base.google.com'.
      additional_headers: dictionary (optional) Any additional headers which 
          should be included with CRUD operations.
      handler: module (optional) This parameter is deprecated and has been
          replaced by http_client.
      tokens: This parameter is deprecated, calls should be made to 
          token_store instead.
      http_client: An object responsible for making HTTP requests using a
          request method. If none is provided, a new instance of
          atom.http.ProxiedHttpClient will be used.
      token_store: Keeps a collection of authorization tokens which can be
          applied to requests for a specific URLs. Critical methods are
          find_token based on a URL (atom.url.Url or a string), add_token,
          and remove_token.
    """
    atom.service.AtomService.__init__(self, http_client=http_client, 
        token_store=token_store)
    self.email = email
    self.password = password
    self.account_type = account_type
    self.service = service
    self.auth_service_url = auth_service_url
    self.server = server
    self.additional_headers = additional_headers or {}
    self._oauth_input_params = None
    self.__SetSource(source)
    self.__captcha_token = None
    self.__captcha_url = None
    self.__gsessionid = None

    if http_request_handler.__name__ == 'gdata.urlfetch':
      import gdata.alt.appengine
      self.http_client = gdata.alt.appengine.AppEngineHttpClient()

  def _SetSessionId(self, session_id):
    """Used in unit tests to simulate a 302 which sets a gsessionid."""
    self.__gsessionid = session_id
 
  # Define properties for GDataService
  def _SetAuthSubToken(self, auth_token, scopes=None):
    """Deprecated, use SetAuthSubToken instead."""
    self.SetAuthSubToken(auth_token, scopes=scopes)

  def __SetAuthSubToken(self, auth_token, scopes=None):
    """Deprecated, use SetAuthSubToken instead."""
    self._SetAuthSubToken(auth_token, scopes=scopes)

  def _GetAuthToken(self):
    """Returns the auth token used for authenticating requests.

    Returns:
      string
    """
    current_scopes = lookup_scopes(self.service)
    if current_scopes:
      token = self.token_store.find_token(current_scopes[0])
      if hasattr(token, 'auth_header'):
        return token.auth_header
    return None

  def _GetCaptchaToken(self):
    """Returns a captcha token if the most recent login attempt generated one.

    The captcha token is only set if the Programmatic Login attempt failed 
    because the Google service issued a captcha challenge.

    Returns:
      string
    """
    return self.__captcha_token

  def __GetCaptchaToken(self):
    return self._GetCaptchaToken()

  captcha_token = property(__GetCaptchaToken,
      doc="""Get the captcha token for a login request.""")

  def _GetCaptchaURL(self):
    """Returns the URL of the captcha image if a login attempt generated one.

    The captcha URL is only set if the Programmatic Login attempt failed
    because the Google service issued a captcha challenge.

    Returns:
      string
    """
    return self.__captcha_url

  def __GetCaptchaURL(self):
    return self._GetCaptchaURL()

  captcha_url = property(__GetCaptchaURL,
      doc="""Get the captcha URL for a login request.""")

  def GetGeneratorFromLinkFinder(self, link_finder, func, 
                                 num_retries=DEFAULT_NUM_RETRIES,
                                 delay=DEFAULT_DELAY,
                                 backoff=DEFAULT_BACKOFF):
    """returns a generator for pagination"""
    yield link_finder
    next = link_finder.GetNextLink()
    while next is not None:
      next_feed = func(str(self.GetWithRetries(
            next.href, num_retries=num_retries, delay=delay, backoff=backoff)))
      yield next_feed
      next = next_feed.GetNextLink()

  def _GetElementGeneratorFromLinkFinder(self, link_finder, func,
                                        num_retries=DEFAULT_NUM_RETRIES,
                                        delay=DEFAULT_DELAY,
                                        backoff=DEFAULT_BACKOFF):
    for element in self.GetGeneratorFromLinkFinder(link_finder, func,
                                                   num_retries=num_retries,
                                                   delay=delay,
                                                   backoff=backoff).entry:
      yield element

  def GetOAuthInputParameters(self):
    return self._oauth_input_params

  def SetOAuthInputParameters(self, signature_method, consumer_key,
                              consumer_secret=None, rsa_key=None,
                              two_legged_oauth=False, requestor_id=None):
    """Sets parameters required for using OAuth authentication mechanism.

    NOTE: Though consumer_secret and rsa_key are optional, either of the two
    is required depending on the value of the signature_method.

    Args:
      signature_method: class which provides implementation for strategy class
          oauth.oauth.OAuthSignatureMethod. Signature method to be used for
          signing each request. Valid implementations are provided as the
          constants defined by gdata.auth.OAuthSignatureMethod. Currently
          they are gdata.auth.OAuthSignatureMethod.RSA_SHA1 and
          gdata.auth.OAuthSignatureMethod.HMAC_SHA1
      consumer_key: string Domain identifying third_party web application.
      consumer_secret: string (optional) Secret generated during registration.
          Required only for HMAC_SHA1 signature method.
      rsa_key: string (optional) Private key required for RSA_SHA1 signature
          method.
      two_legged_oauth: boolean (optional) Enables two-legged OAuth process.
      requestor_id: string (optional) User email adress to make requests on
          their behalf.  This parameter should only be set when two_legged_oauth
          is True.
    """
    self._oauth_input_params = gdata.auth.OAuthInputParams(
        signature_method, consumer_key, consumer_secret=consumer_secret,
        rsa_key=rsa_key, requestor_id=requestor_id)
    if two_legged_oauth:
      oauth_token = gdata.auth.OAuthToken(
          oauth_input_params=self._oauth_input_params)
      self.SetOAuthToken(oauth_token)

  def FetchOAuthRequestToken(self, scopes=None, extra_parameters=None,
                             request_url='%s/accounts/OAuthGetRequestToken' % \
                             AUTH_SERVER_HOST, oauth_callback=None):
    """Fetches and sets the OAuth request token and returns it.

    Args:
      scopes: string or list of string base URL(s) of the service(s) to be
          accessed. If None, then this method tries to determine the
          scope(s) from the current service.
      extra_parameters: dict (optional) key-value pairs as any additional
          parameters to be included in the URL and signature while making a
          request for fetching an OAuth request token. All the OAuth parameters
          are added by default. But if provided through this argument, any
          default parameters will be overwritten. For e.g. a default parameter
          oauth_version 1.0 can be overwritten if
          extra_parameters = {'oauth_version': '2.0'}
      request_url: Request token URL. The default is
          'https://www.google.com/accounts/OAuthGetRequestToken'.
      oauth_callback: str (optional) If set, it is assume the client is using
          the OAuth v1.0a protocol where the callback url is sent in the
          request token step.  If the oauth_callback is also set in
          extra_params, this value will override that one.

    Returns:
      The fetched request token as a gdata.auth.OAuthToken object.

    Raises:
      FetchingOAuthRequestTokenFailed if the server responded to the request
      with an error.
    """
    if scopes is None:
      scopes = lookup_scopes(self.service)
    if not isinstance(scopes, (list, tuple)):
      scopes = [scopes,]
    if oauth_callback:
      if extra_parameters is not None:
        extra_parameters['oauth_callback'] = oauth_callback
      else:
        extra_parameters = {'oauth_callback': oauth_callback}
    request_token_url = gdata.auth.GenerateOAuthRequestTokenUrl(
        self._oauth_input_params, scopes,
        request_token_url=request_url,
        extra_parameters=extra_parameters)
    response = self.http_client.request('GET', str(request_token_url))
    if response.status == 200:
      token = gdata.auth.OAuthToken()
      token.set_token_string(response.read())
      token.scopes = scopes
      token.oauth_input_params = self._oauth_input_params
      self.SetOAuthToken(token)
      return token
    error = {
        'status': response.status,
        'reason': 'Non 200 response on fetch request token',
        'body': response.read()
        }
    raise FetchingOAuthRequestTokenFailed(error)    
  
  def SetOAuthToken(self, oauth_token):
    """Attempts to set the current token and add it to the token store.
    
    The oauth_token can be any OAuth token i.e. unauthorized request token,
    authorized request token or access token.
    This method also attempts to add the token to the token store.
    Use this method any time you want the current token to point to the
    oauth_token passed. For e.g. call this method with the request token
    you receive from FetchOAuthRequestToken.
    
    Args:
      request_token: gdata.auth.OAuthToken OAuth request token.
    """
    if self.auto_set_current_token:
      self.current_token = oauth_token
    if self.auto_store_tokens:
      self.token_store.add_token(oauth_token)
    
  def GenerateOAuthAuthorizationURL(
      self, request_token=None, callback_url=None, extra_params=None,
      include_scopes_in_callback=False,
      scopes_param_prefix=OAUTH_SCOPE_URL_PARAM_NAME,
      request_url='%s/accounts/OAuthAuthorizeToken' % AUTH_SERVER_HOST):
    """Generates URL at which user will login to authorize the request token.
    
    Args:
      request_token: gdata.auth.OAuthToken (optional) OAuth request token.
          If not specified, then the current token will be used if it is of
          type <gdata.auth.OAuthToken>, else it is found by looking in the
          token_store by looking for a token for the current scope.    
      callback_url: string (optional) The URL user will be sent to after
          logging in and granting access.
      extra_params: dict (optional) Additional parameters to be sent.
      include_scopes_in_callback: Boolean (default=False) if set to True, and
          if 'callback_url' is present, the 'callback_url' will be modified to
          include the scope(s) from the request token as a URL parameter. The
          key for the 'callback' URL's scope parameter will be
          OAUTH_SCOPE_URL_PARAM_NAME. The benefit of including the scope URL as
          a parameter to the 'callback' URL, is that the page which receives
          the OAuth token will be able to tell which URLs the token grants
          access to.
      scopes_param_prefix: string (default='oauth_token_scope') The URL
          parameter key which maps to the list of valid scopes for the token.
          This URL parameter will be included in the callback URL along with
          the scopes of the token as value if include_scopes_in_callback=True.
      request_url: Authorization URL. The default is
          'https://www.google.com/accounts/OAuthAuthorizeToken'.
    Returns:
      A string URL at which the user is required to login.
    
    Raises:
      NonOAuthToken if the user's request token is not an OAuth token or if a
      request token was not available.
    """
    if request_token and not isinstance(request_token, gdata.auth.OAuthToken):
      raise NonOAuthToken
    if not request_token:
      if isinstance(self.current_token, gdata.auth.OAuthToken):
        request_token = self.current_token
      else:
        current_scopes = lookup_scopes(self.service)
        if current_scopes:
          token = self.token_store.find_token(current_scopes[0])
          if isinstance(token, gdata.auth.OAuthToken):
            request_token = token
    if not request_token:
      raise NonOAuthToken
    return str(gdata.auth.GenerateOAuthAuthorizationUrl(
        request_token,
        authorization_url=request_url,
        callback_url=callback_url, extra_params=extra_params,
        include_scopes_in_callback=include_scopes_in_callback,
        scopes_param_prefix=scopes_param_prefix))   
  
  def UpgradeToOAuthAccessToken(self, authorized_request_token=None,
                                request_url='%s/accounts/OAuthGetAccessToken' \
                                % AUTH_SERVER_HOST, oauth_version='1.0',
                                oauth_verifier=None):
    """Upgrades the authorized request token to an access token and returns it
    
    Args:
      authorized_request_token: gdata.auth.OAuthToken (optional) OAuth request
          token. If not specified, then the current token will be used if it is
          of type <gdata.auth.OAuthToken>, else it is found by looking in the
          token_store by looking for a token for the current scope.
      request_url: Access token URL. The default is
          'https://www.google.com/accounts/OAuthGetAccessToken'.
      oauth_version: str (default='1.0') oauth_version parameter. All other
          'oauth_' parameters are added by default. This parameter too, is
          added by default but here you can override it's value.
      oauth_verifier: str (optional) If present, it is assumed that the client
        will use the OAuth v1.0a protocol which includes passing the
        oauth_verifier (as returned by the SP) in the access token step.
    
    Returns:
      Access token
          
    Raises:
      NonOAuthToken if the user's authorized request token is not an OAuth
      token or if an authorized request token was not available.
      TokenUpgradeFailed if the server responded to the request with an 
      error.
    """
    if (authorized_request_token and
        not isinstance(authorized_request_token, gdata.auth.OAuthToken)):
      raise NonOAuthToken
    if not authorized_request_token:
      if isinstance(self.current_token, gdata.auth.OAuthToken):
        authorized_request_token = self.current_token
      else:
        current_scopes = lookup_scopes(self.service)
        if current_scopes:
          token = self.token_store.find_token(current_scopes[0])
          if isinstance(token, gdata.auth.OAuthToken):
            authorized_request_token = token
    if not authorized_request_token:
      raise NonOAuthToken
    access_token_url = gdata.auth.GenerateOAuthAccessTokenUrl(
        authorized_request_token,
        self._oauth_input_params,
        access_token_url=request_url,
        oauth_version=oauth_version,
        oauth_verifier=oauth_verifier)
    response = self.http_client.request('GET', str(access_token_url))
    if response.status == 200:
      token = gdata.auth.OAuthTokenFromHttpBody(response.read())
      token.scopes = authorized_request_token.scopes
      token.oauth_input_params = authorized_request_token.oauth_input_params
      self.SetOAuthToken(token)
      return token
    else:
      raise TokenUpgradeFailed({'status': response.status,
                                'reason': 'Non 200 response on upgrade',
                                'body': response.read()})      
  
  def RevokeOAuthToken(self, request_url='%s/accounts/AuthSubRevokeToken' % \
                       AUTH_SERVER_HOST):
    """Revokes an existing OAuth token.

    request_url: Token revoke URL. The default is
          'https://www.google.com/accounts/AuthSubRevokeToken'.
    Raises:
      NonOAuthToken if the user's auth token is not an OAuth token.
      RevokingOAuthTokenFailed if request for revoking an OAuth token failed.
    """
    scopes = lookup_scopes(self.service)
    token = self.token_store.find_token(scopes[0])
    if not isinstance(token, gdata.auth.OAuthToken):
      raise NonOAuthToken

    response = token.perform_request(self.http_client, 'GET', request_url,
        headers={'Content-Type':'application/x-www-form-urlencoded'})
    if response.status == 200:
      self.token_store.remove_token(token)
    else:
      raise RevokingOAuthTokenFailed
  
  def GetAuthSubToken(self):
    """Returns the AuthSub token as a string.
     
    If the token is an gdta.auth.AuthSubToken, the Authorization Label
    ("AuthSub token") is removed.

    This method examines the current_token to see if it is an AuthSubToken
    or SecureAuthSubToken. If not, it searches the token_store for a token
    which matches the current scope.
    
    The current scope is determined by the service name string member.
    
    Returns:
      If the current_token is set to an AuthSubToken/SecureAuthSubToken,
      return the token string. If there is no current_token, a token string
      for a token which matches the service object's default scope is returned.
      If there are no tokens valid for the scope, returns None.
    """
    if isinstance(self.current_token, gdata.auth.AuthSubToken):
      return self.current_token.get_token_string()
    current_scopes = lookup_scopes(self.service)
    if current_scopes:
      token = self.token_store.find_token(current_scopes[0])
      if isinstance(token, gdata.auth.AuthSubToken):
        return token.get_token_string()
    else:
      token = self.token_store.find_token(atom.token_store.SCOPE_ALL)
      if isinstance(token, gdata.auth.ClientLoginToken):
        return token.get_token_string()
      return None

  def SetAuthSubToken(self, token, scopes=None, rsa_key=None):
    """Sets the token sent in requests to an AuthSub token.

    Sets the current_token and attempts to add the token to the token_store.
    
    Only use this method if you have received a token from the AuthSub
    service. The auth token is set automatically when UpgradeToSessionToken()
    is used. See documentation for Google AuthSub here:
    http://code.google.com/apis/accounts/AuthForWebApps.html 

    Args:
     token: gdata.auth.AuthSubToken or gdata.auth.SecureAuthSubToken or string
            The token returned by the AuthSub service. If the token is an
            AuthSubToken or SecureAuthSubToken, the scope information stored in
            the token is used. If the token is a string, the scopes parameter is
            used to determine the valid scopes.
     scopes: list of URLs for which the token is valid. This is only used
             if the token parameter is a string.
     rsa_key: string (optional) Private key required for RSA_SHA1 signature
              method.  This parameter is necessary if the token is a string
              representing a secure token.
    """
    if not isinstance(token, gdata.auth.AuthSubToken):
      token_string = token
      if rsa_key:
        token = gdata.auth.SecureAuthSubToken(rsa_key)
      else:
        token = gdata.auth.AuthSubToken()

      token.set_token_string(token_string)
        
    # If no scopes were set for the token, use the scopes passed in, or
    # try to determine the scopes based on the current service name. If
    # all else fails, set the token to match all requests.
    if not token.scopes:
      if scopes is None:
        scopes = lookup_scopes(self.service)
        if scopes is None:
          scopes = [atom.token_store.SCOPE_ALL]
      token.scopes = scopes
    if self.auto_set_current_token:
      self.current_token = token
    if self.auto_store_tokens:
      self.token_store.add_token(token)

  def GetClientLoginToken(self):
    """Returns the token string for the current token or a token matching the 
    service scope.

    If the current_token is a ClientLoginToken, the token string for 
    the current token is returned. If the current_token is not set, this method
    searches for a token in the token_store which is valid for the service 
    object's current scope.

    The current scope is determined by the service name string member.
    The token string is the end of the Authorization header, it doesn not
    include the ClientLogin label.
    """
    if isinstance(self.current_token, gdata.auth.ClientLoginToken):
      return self.current_token.get_token_string()
    current_scopes = lookup_scopes(self.service)
    if current_scopes:
      token = self.token_store.find_token(current_scopes[0])
      if isinstance(token, gdata.auth.ClientLoginToken):
        return token.get_token_string()
    else:
      token = self.token_store.find_token(atom.token_store.SCOPE_ALL)
      if isinstance(token, gdata.auth.ClientLoginToken):
        return token.get_token_string()
      return None

  def SetClientLoginToken(self, token, scopes=None):
    """Sets the token sent in requests to a ClientLogin token.

    This method sets the current_token to a new ClientLoginToken and it 
    also attempts to add the ClientLoginToken to the token_store.
    
    Only use this method if you have received a token from the ClientLogin
    service. The auth_token is set automatically when ProgrammaticLogin()
    is used. See documentation for Google ClientLogin here:
    http://code.google.com/apis/accounts/docs/AuthForInstalledApps.html

    Args:
      token: string or instance of a ClientLoginToken. 
    """
    if not isinstance(token, gdata.auth.ClientLoginToken):
      token_string = token
      token = gdata.auth.ClientLoginToken()
      token.set_token_string(token_string)

    if not token.scopes:
      if scopes is None:
        scopes = lookup_scopes(self.service)
        if scopes is None:
          scopes = [atom.token_store.SCOPE_ALL]
      token.scopes = scopes
    if self.auto_set_current_token:
      self.current_token = token
    if self.auto_store_tokens:
      self.token_store.add_token(token)

  # Private methods to create the source property.
  def __GetSource(self):
    return self.__source

  def __SetSource(self, new_source):
    self.__source = new_source
    # Update the UserAgent header to include the new application name.
    self.additional_headers['User-Agent'] = atom.http_interface.USER_AGENT % (
        self.__source,)

  source = property(__GetSource, __SetSource, 
      doc="""The source is the name of the application making the request. 
             It should be in the form company_id-app_name-app_version""")

  # Authentication operations

  def ProgrammaticLogin(self, captcha_token=None, captcha_response=None):
    """Authenticates the user and sets the GData Auth token.

    Login retreives a temporary auth token which must be used with all
    requests to GData services. The auth token is stored in the GData client
    object.

    Login is also used to respond to a captcha challenge. If the user's login
    attempt failed with a CaptchaRequired error, the user can respond by
    calling Login with the captcha token and the answer to the challenge.

    Args:
      captcha_token: string (optional) The identifier for the captcha challenge
                     which was presented to the user.
      captcha_response: string (optional) The user's answer to the captch 
                        challenge.

    Raises:
      CaptchaRequired if the login service will require a captcha response
      BadAuthentication if the login service rejected the username or password
      Error if the login service responded with a 403 different from the above
    """
    request_body = gdata.auth.generate_client_login_request_body(self.email,
        self.password, self.service, self.source, self.account_type,
        captcha_token, captcha_response)

    # If the user has defined their own authentication service URL, 
    # send the ClientLogin requests to this URL:
    if not self.auth_service_url:
        auth_request_url = AUTH_SERVER_HOST + '/accounts/ClientLogin' 
    else:
        auth_request_url = self.auth_service_url

    auth_response = self.http_client.request('POST', auth_request_url,
        data=request_body, 
        headers={'Content-Type':'application/x-www-form-urlencoded'})
    response_body = auth_response.read()

    if auth_response.status == 200:
      # TODO: insert the token into the token_store directly.
      self.SetClientLoginToken(
          gdata.auth.get_client_login_token(response_body))
      self.__captcha_token = None
      self.__captcha_url = None

    elif auth_response.status == 403:
      # Examine each line to find the error type and the captcha token and
      # captch URL if they are present.
      captcha_parameters = gdata.auth.get_captcha_challenge(response_body,
          captcha_base_url='%s/accounts/' % AUTH_SERVER_HOST)
      if captcha_parameters:
        self.__captcha_token = captcha_parameters['token']
        self.__captcha_url = captcha_parameters['url']
        raise CaptchaRequired, 'Captcha Required'
      elif response_body.splitlines()[0] == 'Error=BadAuthentication':
        self.__captcha_token = None
        self.__captcha_url = None
        raise BadAuthentication, 'Incorrect username or password'
      else:
        self.__captcha_token = None
        self.__captcha_url = None
        raise Error, 'Server responded with a 403 code'
    elif auth_response.status == 302:
      self.__captcha_token = None
      self.__captcha_url = None
      # Google tries to redirect all bad URLs back to 
      # http://www.google.<locale>. If a redirect
      # attempt is made, assume the user has supplied an incorrect authentication URL
      raise BadAuthenticationServiceURL, 'Server responded with a 302 code.'

  def ClientLogin(self, username, password, account_type=None, service=None,
      auth_service_url=None, source=None, captcha_token=None, 
      captcha_response=None):
    """Convenience method for authenticating using ProgrammaticLogin. 
    
    Sets values for email, password, and other optional members.

    Args:
      username:
      password:
      account_type: string (optional)
      service: string (optional)
      auth_service_url: string (optional)
      captcha_token: string (optional)
      captcha_response: string (optional)
    """
    self.email = username
    self.password = password

    if account_type:
      self.account_type = account_type
    if service:
      self.service = service
    if source:
      self.source = source
    if auth_service_url:
      self.auth_service_url = auth_service_url

    self.ProgrammaticLogin(captcha_token, captcha_response)

  def GenerateAuthSubURL(self, next, scope, secure=False, session=True, 
      domain='default'):
    """Generate a URL at which the user will login and be redirected back.

    Users enter their credentials on a Google login page and a token is sent
    to the URL specified in next. See documentation for AuthSub login at:
    http://code.google.com/apis/accounts/docs/AuthSub.html

    Args:
      next: string The URL user will be sent to after logging in.
      scope: string or list of strings. The URLs of the services to be 
             accessed.
      secure: boolean (optional) Determines whether or not the issued token
              is a secure token.
      session: boolean (optional) Determines whether or not the issued token
               can be upgraded to a session token.
    """
    if not isinstance(scope, (list, tuple)):
      scope = (scope,)
    return gdata.auth.generate_auth_sub_url(next, scope, secure=secure, 
        session=session, 
        request_url='%s/accounts/AuthSubRequest' % AUTH_SERVER_HOST, 
        domain=domain)

  def UpgradeToSessionToken(self, token=None):
    """Upgrades a single use AuthSub token to a session token.

    Args:
      token: A gdata.auth.AuthSubToken or gdata.auth.SecureAuthSubToken
             (optional) which is good for a single use but can be upgraded
             to a session token. If no token is passed in, the token
             is found by looking in the token_store by looking for a token
             for the current scope.

    Raises:
      NonAuthSubToken if the user's auth token is not an AuthSub token
      TokenUpgradeFailed if the server responded to the request with an 
      error.
    """
    if token is None:
      scopes = lookup_scopes(self.service)
      if scopes:
        token = self.token_store.find_token(scopes[0])
      else:
        token = self.token_store.find_token(atom.token_store.SCOPE_ALL)
    if not isinstance(token, gdata.auth.AuthSubToken):
      raise NonAuthSubToken

    self.SetAuthSubToken(self.upgrade_to_session_token(token))

  def upgrade_to_session_token(self, token):
    """Upgrades a single use AuthSub token to a session token.

    Args:
      token: A gdata.auth.AuthSubToken or gdata.auth.SecureAuthSubToken
             which is good for a single use but can be upgraded to a
             session token.

    Returns:
      The upgraded token as a gdata.auth.AuthSubToken object.

    Raises:
      TokenUpgradeFailed if the server responded to the request with an 
      error.
    """
    response = token.perform_request(self.http_client, 'GET', 
        AUTH_SERVER_HOST + '/accounts/AuthSubSessionToken', 
        headers={'Content-Type':'application/x-www-form-urlencoded'})
    response_body = response.read()
    if response.status == 200:
      token.set_token_string(
          gdata.auth.token_from_http_body(response_body))
      return token
    else:
      raise TokenUpgradeFailed({'status': response.status,
                                'reason': 'Non 200 response on upgrade',
                                'body': response_body})

  def RevokeAuthSubToken(self):
    """Revokes an existing AuthSub token.

    Raises:
      NonAuthSubToken if the user's auth token is not an AuthSub token
    """
    scopes = lookup_scopes(self.service)
    token = self.token_store.find_token(scopes[0])
    if not isinstance(token, gdata.auth.AuthSubToken):
      raise NonAuthSubToken

    response = token.perform_request(self.http_client, 'GET', 
        AUTH_SERVER_HOST + '/accounts/AuthSubRevokeToken', 
        headers={'Content-Type':'application/x-www-form-urlencoded'})
    if response.status == 200:
      self.token_store.remove_token(token)

  def AuthSubTokenInfo(self):
    """Fetches the AuthSub token's metadata from the server.

    Raises:
      NonAuthSubToken if the user's auth token is not an AuthSub token
    """
    scopes = lookup_scopes(self.service)
    token = self.token_store.find_token(scopes[0])
    if not isinstance(token, gdata.auth.AuthSubToken):
      raise NonAuthSubToken

    response = token.perform_request(self.http_client, 'GET', 
        AUTH_SERVER_HOST + '/accounts/AuthSubTokenInfo', 
        headers={'Content-Type':'application/x-www-form-urlencoded'})
    result_body = response.read()
    if response.status == 200:
      return result_body
    else:
      raise RequestError, {'status': response.status,
          'body': result_body}

  def GetWithRetries(self, uri, extra_headers=None, redirects_remaining=4, 
      encoding='UTF-8', converter=None, num_retries=DEFAULT_NUM_RETRIES,
      delay=DEFAULT_DELAY, backoff=DEFAULT_BACKOFF, logger=None):
    """This is a wrapper method for Get with retrying capability.

    To avoid various errors while retrieving bulk entities by retrying
    specified times.

    Note this method relies on the time module and so may not be usable
    by default in Python2.2.

    Args:
      num_retries: Integer; the retry count.
      delay: Integer; the initial delay for retrying.
      backoff: Integer; how much the delay should lengthen after each failure.
      logger: An object which has a debug(str) method to receive logging
              messages. Recommended that you pass in the logging module.
    Raises:
      ValueError if any of the parameters has an invalid value.
      RanOutOfTries on failure after number of retries.
    """
    # Moved import for time module inside this method since time is not a
    # default module in Python2.2. This method will not be usable in
    # Python2.2.
    import time
    if backoff <= 1:
      raise ValueError("backoff must be greater than 1")
    num_retries = int(num_retries)

    if num_retries < 0:
      raise ValueError("num_retries must be 0 or greater")

    if delay <= 0:
      raise ValueError("delay must be greater than 0")

    # Let's start
    mtries, mdelay = num_retries, delay
    while mtries > 0:
      if mtries != num_retries:
        if logger:
          logger.debug("Retrying: %s" % uri)
      try:
        rv = self.Get(uri, extra_headers=extra_headers,
                      redirects_remaining=redirects_remaining,
                      encoding=encoding, converter=converter)
      except SystemExit:
        # Allow this error
        raise
      except RequestError, e:
        # Error 500 is 'internal server error' and warrants a retry
        # Error 503 is 'service unavailable' and warrants a retry
        if e[0]['status'] not in [500, 503]:
          raise e
        # Else, fall through to the retry code...
      except Exception, e:
        if logger:
          logger.debug(e)
        # Fall through to the retry code...
      else:
        # This is the right path.
        return rv
      mtries -= 1
      time.sleep(mdelay)
      mdelay *= backoff
    raise RanOutOfTries('Ran out of tries.')

  # CRUD operations
  def Get(self, uri, extra_headers=None, redirects_remaining=4, 
      encoding='UTF-8', converter=None):
    """Query the GData API with the given URI

    The uri is the portion of the URI after the server value 
    (ex: www.google.com).

    To perform a query against Google Base, set the server to 
    'base.google.com' and set the uri to '/base/feeds/...', where ... is 
    your query. For example, to find snippets for all digital cameras uri 
    should be set to: '/base/feeds/snippets?bq=digital+camera'

    Args:
      uri: string The query in the form of a URI. Example:
           '/base/feeds/snippets?bq=digital+camera'.
      extra_headers: dictionary (optional) Extra HTTP headers to be included
                     in the GET request. These headers are in addition to 
                     those stored in the client's additional_headers property.
                     The client automatically sets the Content-Type and 
                     Authorization headers.
      redirects_remaining: int (optional) Tracks the number of additional
          redirects this method will allow. If the service object receives
          a redirect and remaining is 0, it will not follow the redirect. 
          This was added to avoid infinite redirect loops.
      encoding: string (optional) The character encoding for the server's
          response. Default is UTF-8
      converter: func (optional) A function which will transform
          the server's results before it is returned. Example: use 
          GDataFeedFromString to parse the server response as if it
          were a GDataFeed.

    Returns:
      If there is no ResultsTransformer specified in the call, a GDataFeed 
      or GDataEntry depending on which is sent from the server. If the 
      response is niether a feed or entry and there is no ResultsTransformer,
      return a string. If there is a ResultsTransformer, the returned value 
      will be that of the ResultsTransformer function.
    """

    if extra_headers is None:
      extra_headers = {}

    if self.__gsessionid is not None:
      if uri.find('gsessionid=') < 0:
        if uri.find('?') > -1:
          uri += '&gsessionid=%s' % (self.__gsessionid,)
        else:
          uri += '?gsessionid=%s' % (self.__gsessionid,)

    server_response = self.request('GET', uri, 
        headers=extra_headers)
    result_body = server_response.read()

    if server_response.status == 200:
      if converter:
        return converter(result_body)
      # There was no ResultsTransformer specified, so try to convert the
      # server's response into a GDataFeed.
      feed = gdata.GDataFeedFromString(result_body)
      if not feed:
        # If conversion to a GDataFeed failed, try to convert the server's
        # response to a GDataEntry.
        entry = gdata.GDataEntryFromString(result_body)
        if not entry:
          # The server's response wasn't a feed, or an entry, so return the
          # response body as a string.
          return result_body
        return entry
      return feed
    elif server_response.status == 302:
      if redirects_remaining > 0:
        location = (server_response.getheader('Location')
                    or server_response.getheader('location'))
        if location is not None:
          m = re.compile('[\?\&]gsessionid=(\w*\-)').search(location)
          if m is not None:
            self.__gsessionid = m.group(1)
          return GDataService.Get(self, location, extra_headers, redirects_remaining - 1, 
              encoding=encoding, converter=converter)
        else:
          raise RequestError, {'status': server_response.status,
              'reason': '302 received without Location header',
              'body': result_body}
      else:
        raise RequestError, {'status': server_response.status,
            'reason': 'Redirect received, but redirects_remaining <= 0',
            'body': result_body}
    else:
      raise RequestError, {'status': server_response.status,
          'reason': server_response.reason, 'body': result_body}

  def GetMedia(self, uri, extra_headers=None):
    """Returns a MediaSource containing media and its metadata from the given
    URI string.
    """
    response_handle = self.request('GET', uri,
        headers=extra_headers)
    return gdata.MediaSource(response_handle, response_handle.getheader(
            'Content-Type'),
        response_handle.getheader('Content-Length'))

  def GetEntry(self, uri, extra_headers=None):
    """Query the GData API with the given URI and receive an Entry.
    
    See also documentation for gdata.service.Get

    Args:
      uri: string The query in the form of a URI. Example:
           '/base/feeds/snippets?bq=digital+camera'.
      extra_headers: dictionary (optional) Extra HTTP headers to be included
                     in the GET request. These headers are in addition to
                     those stored in the client's additional_headers property.
                     The client automatically sets the Content-Type and
                     Authorization headers.

    Returns:
      A GDataEntry built from the XML in the server's response.
    """

    result = GDataService.Get(self, uri, extra_headers, 
        converter=atom.EntryFromString)
    if isinstance(result, atom.Entry):
      return result
    else:
      raise UnexpectedReturnType, 'Server did not send an entry' 

  def GetFeed(self, uri, extra_headers=None, 
              converter=gdata.GDataFeedFromString):
    """Query the GData API with the given URI and receive a Feed.

    See also documentation for gdata.service.Get

    Args:
      uri: string The query in the form of a URI. Example:
           '/base/feeds/snippets?bq=digital+camera'.
      extra_headers: dictionary (optional) Extra HTTP headers to be included
                     in the GET request. These headers are in addition to
                     those stored in the client's additional_headers property.
                     The client automatically sets the Content-Type and
                     Authorization headers.

    Returns:
      A GDataFeed built from the XML in the server's response.
    """

    result = GDataService.Get(self, uri, extra_headers, converter=converter)
    if isinstance(result, atom.Feed):
      return result
    else:
      raise UnexpectedReturnType, 'Server did not send a feed'  

  def GetNext(self, feed):
    """Requests the next 'page' of results in the feed.
    
    This method uses the feed's next link to request an additional feed
    and uses the class of the feed to convert the results of the GET request.

    Args:
      feed: atom.Feed or a subclass. The feed should contain a next link and
          the type of the feed will be applied to the results from the 
          server. The new feed which is returned will be of the same class
          as this feed which was passed in.

    Returns:
      A new feed representing the next set of results in the server's feed.
      The type of this feed will match that of the feed argument.
    """
    next_link = feed.GetNextLink()
    # Create a closure which will convert an XML string to the class of
    # the feed object passed in.
    def ConvertToFeedClass(xml_string):
      return atom.CreateClassFromXMLString(feed.__class__, xml_string)
    # Make a GET request on the next link and use the above closure for the
    # converted which processes the XML string from the server.
    if next_link and next_link.href:
      return GDataService.Get(self, next_link.href, 
          converter=ConvertToFeedClass)
    else:
      return None

  def Post(self, data, uri, extra_headers=None, url_params=None,
           escape_params=True, redirects_remaining=4, media_source=None,
           converter=None):
    """Insert or update  data into a GData service at the given URI.

    Args:
      data: string, ElementTree._Element, atom.Entry, or gdata.GDataEntry The
            XML to be sent to the uri.
      uri: string The location (feed) to which the data should be inserted.
           Example: '/base/feeds/items'.
      extra_headers: dict (optional) HTTP headers which are to be included.
                     The client automatically sets the Content-Type,
                     Authorization, and Content-Length headers.
      url_params: dict (optional) Additional URL parameters to be included
                  in the URI. These are translated into query arguments
                  in the form '&dict_key=value&...'.
                  Example: {'max-results': '250'} becomes &max-results=250
      escape_params: boolean (optional) If false, the calling code has already
                     ensured that the query will form a valid URL (all
                     reserved characters have been escaped). If true, this
                     method will escape the query and any URL parameters
                     provided.
      media_source: MediaSource (optional) Container for the media to be sent
          along with the entry, if provided.
      converter: func (optional) A function which will be executed on the
          server's response. Often this is a function like
          GDataEntryFromString which will parse the body of the server's
          response and return a GDataEntry.

    Returns:
      If the post succeeded, this method will return a GDataFeed, GDataEntry,
      or the results of running converter on the server's result body (if
      converter was specified).
    """
    return GDataService.PostOrPut(self, 'POST', data, uri, 
        extra_headers=extra_headers, url_params=url_params, 
        escape_params=escape_params, redirects_remaining=redirects_remaining,
        media_source=media_source, converter=converter)

  def PostOrPut(self, verb, data, uri, extra_headers=None, url_params=None, 
           escape_params=True, redirects_remaining=4, media_source=None, 
           converter=None):
    """Insert data into a GData service at the given URI.

    Args:
      verb: string, either 'POST' or 'PUT'
      data: string, ElementTree._Element, atom.Entry, or gdata.GDataEntry The
            XML to be sent to the uri. 
      uri: string The location (feed) to which the data should be inserted. 
           Example: '/base/feeds/items'. 
      extra_headers: dict (optional) HTTP headers which are to be included. 
                     The client automatically sets the Content-Type,
                     Authorization, and Content-Length headers.
      url_params: dict (optional) Additional URL parameters to be included
                  in the URI. These are translated into query arguments
                  in the form '&dict_key=value&...'.
                  Example: {'max-results': '250'} becomes &max-results=250
      escape_params: boolean (optional) If false, the calling code has already
                     ensured that the query will form a valid URL (all
                     reserved characters have been escaped). If true, this
                     method will escape the query and any URL parameters
                     provided.
      media_source: MediaSource (optional) Container for the media to be sent
          along with the entry, if provided.
      converter: func (optional) A function which will be executed on the 
          server's response. Often this is a function like 
          GDataEntryFromString which will parse the body of the server's 
          response and return a GDataEntry.

    Returns:
      If the post succeeded, this method will return a GDataFeed, GDataEntry,
      or the results of running converter on the server's result body (if
      converter was specified).
    """
    if extra_headers is None:
      extra_headers = {}

    if self.__gsessionid is not None:
      if uri.find('gsessionid=') < 0:
        if url_params is None:
          url_params = {}
        url_params['gsessionid'] = self.__gsessionid

    if data and media_source:
      if ElementTree.iselement(data):
        data_str = ElementTree.tostring(data)
      else:
        data_str = str(data)
        
      multipart = []
      multipart.append('Media multipart posting\r\n--END_OF_PART\r\n' + \
          'Content-Type: application/atom+xml\r\n\r\n')
      multipart.append('\r\n--END_OF_PART\r\nContent-Type: ' + \
          media_source.content_type+'\r\n\r\n')
      multipart.append('\r\n--END_OF_PART--\r\n')
        
      extra_headers['MIME-version'] = '1.0'
      extra_headers['Content-Length'] = str(len(multipart[0]) +
          len(multipart[1]) + len(multipart[2]) +
          len(data_str) + media_source.content_length)

      extra_headers['Content-Type'] = 'multipart/related; boundary=END_OF_PART'
      server_response = self.request(verb, uri, 
          data=[multipart[0], data_str, multipart[1], media_source.file_handle,
              multipart[2]], headers=extra_headers, url_params=url_params)
      result_body = server_response.read()
      
    elif media_source or isinstance(data, gdata.MediaSource):
      if isinstance(data, gdata.MediaSource):
        media_source = data
      extra_headers['Content-Length'] = str(media_source.content_length)
      extra_headers['Content-Type'] = media_source.content_type
      server_response = self.request(verb, uri, 
          data=media_source.file_handle, headers=extra_headers,
          url_params=url_params)
      result_body = server_response.read()

    else:
      http_data = data
      if 'Content-Type' not in extra_headers:
        content_type = 'application/atom+xml'
        extra_headers['Content-Type'] = content_type
      server_response = self.request(verb, uri, data=http_data,
          headers=extra_headers, url_params=url_params)
      result_body = server_response.read()

    # Server returns 201 for most post requests, but when performing a batch
    # request the server responds with a 200 on success.
    if server_response.status == 201 or server_response.status == 200:
      if converter:
        return converter(result_body)
      feed = gdata.GDataFeedFromString(result_body)
      if not feed:
        entry = gdata.GDataEntryFromString(result_body)
        if not entry:
          return result_body
        return entry
      return feed
    elif server_response.status == 302:
      if redirects_remaining > 0:
        location = (server_response.getheader('Location')
                    or server_response.getheader('location'))
        if location is not None:
          m = re.compile('[\?\&]gsessionid=(\w*\-)').search(location)
          if m is not None:
            self.__gsessionid = m.group(1) 
          return GDataService.PostOrPut(self, verb, data, location, 
              extra_headers, url_params, escape_params, 
              redirects_remaining - 1, media_source, converter=converter)
        else:
          raise RequestError, {'status': server_response.status,
              'reason': '302 received without Location header',
              'body': result_body}
      else:
        raise RequestError, {'status': server_response.status,
            'reason': 'Redirect received, but redirects_remaining <= 0',
            'body': result_body}
    else:
      raise RequestError, {'status': server_response.status,
          'reason': server_response.reason, 'body': result_body}

  def Put(self, data, uri, extra_headers=None, url_params=None, 
          escape_params=True, redirects_remaining=3, media_source=None,
          converter=None):
    """Updates an entry at the given URI.
     
    Args:
      data: string, ElementTree._Element, or xml_wrapper.ElementWrapper The 
            XML containing the updated data.
      uri: string A URI indicating entry to which the update will be applied.
           Example: '/base/feeds/items/ITEM-ID'
      extra_headers: dict (optional) HTTP headers which are to be included.
                     The client automatically sets the Content-Type,
                     Authorization, and Content-Length headers.
      url_params: dict (optional) Additional URL parameters to be included
                  in the URI. These are translated into query arguments
                  in the form '&dict_key=value&...'.
                  Example: {'max-results': '250'} becomes &max-results=250
      escape_params: boolean (optional) If false, the calling code has already
                     ensured that the query will form a valid URL (all
                     reserved characters have been escaped). If true, this
                     method will escape the query and any URL parameters
                     provided.
      converter: func (optional) A function which will be executed on the 
          server's response. Often this is a function like 
          GDataEntryFromString which will parse the body of the server's 
          response and return a GDataEntry.

    Returns:
      If the put succeeded, this method will return a GDataFeed, GDataEntry,
      or the results of running converter on the server's result body (if
      converter was specified).
    """
    return GDataService.PostOrPut(self, 'PUT', data, uri, 
        extra_headers=extra_headers, url_params=url_params, 
        escape_params=escape_params, redirects_remaining=redirects_remaining,
        media_source=media_source, converter=converter)

  def Delete(self, uri, extra_headers=None, url_params=None, 
             escape_params=True, redirects_remaining=4):
    """Deletes the entry at the given URI.

    Args:
      uri: string The URI of the entry to be deleted. Example: 
           '/base/feeds/items/ITEM-ID'
      extra_headers: dict (optional) HTTP headers which are to be included.
                     The client automatically sets the Content-Type and
                     Authorization headers.
      url_params: dict (optional) Additional URL parameters to be included
                  in the URI. These are translated into query arguments
                  in the form '&dict_key=value&...'.
                  Example: {'max-results': '250'} becomes &max-results=250
      escape_params: boolean (optional) If false, the calling code has already
                     ensured that the query will form a valid URL (all
                     reserved characters have been escaped). If true, this
                     method will escape the query and any URL parameters
                     provided.

    Returns:
      True if the entry was deleted.
    """
    if extra_headers is None:
      extra_headers = {}

    if self.__gsessionid is not None:
      if uri.find('gsessionid=') < 0:
        if url_params is None:
          url_params = {}
        url_params['gsessionid'] = self.__gsessionid
 
    server_response = self.request('DELETE', uri, 
        headers=extra_headers, url_params=url_params)
    result_body = server_response.read()

    if server_response.status == 200:
      return True
    elif server_response.status == 302:
      if redirects_remaining > 0:
        location = (server_response.getheader('Location')
                    or server_response.getheader('location'))
        if location is not None:
          m = re.compile('[\?\&]gsessionid=(\w*\-)').search(location)
          if m is not None:
            self.__gsessionid = m.group(1) 
          return GDataService.Delete(self, location, extra_headers, 
              url_params, escape_params, redirects_remaining - 1)
        else:
          raise RequestError, {'status': server_response.status,
              'reason': '302 received without Location header',
              'body': result_body}
      else:
        raise RequestError, {'status': server_response.status,
            'reason': 'Redirect received, but redirects_remaining <= 0',
            'body': result_body}
    else:
      raise RequestError, {'status': server_response.status,
          'reason': server_response.reason, 'body': result_body}


def ExtractToken(url, scopes_included_in_next=True):
  """Gets the AuthSub token from the current page's URL.

  Designed to be used on the URL that the browser is sent to after the user
  authorizes this application at the page given by GenerateAuthSubRequestUrl.

  Args:
    url: The current page's URL. It should contain the token as a URL
        parameter. Example: 'http://example.com/?...&token=abcd435'
    scopes_included_in_next: If True, this function looks for a scope value
        associated with the token. The scope is a URL parameter with the
        key set to SCOPE_URL_PARAM_NAME. This parameter should be present
        if the AuthSub request URL was generated using
        GenerateAuthSubRequestUrl with include_scope_in_next set to True.

  Returns:
    A tuple containing the token string and a list of scope strings for which
    this token should be valid. If the scope was not included in the URL, the
    tuple will contain (token, None).
  """
  parsed = urlparse.urlparse(url)
  token = gdata.auth.AuthSubTokenFromUrl(parsed[4])
  scopes = ''
  if scopes_included_in_next:
    for pair in parsed[4].split('&'):
      if pair.startswith('%s=' % SCOPE_URL_PARAM_NAME):
        scopes = urllib.unquote_plus(pair.split('=')[1])
  return (token, scopes.split(' '))


def GenerateAuthSubRequestUrl(next, scopes, hd='default', secure=False,
    session=True, request_url='https://www.google.com/accounts/AuthSubRequest',
    include_scopes_in_next=True):
  """Creates a URL to request an AuthSub token to access Google services.

  For more details on AuthSub, see the documentation here:
  http://code.google.com/apis/accounts/docs/AuthSub.html

  Args:
    next: The URL where the browser should be sent after the user authorizes
        the application. This page is responsible for receiving the token
        which is embeded in the URL as a parameter.
    scopes: The base URL to which access will be granted. Example:
        'http://www.google.com/calendar/feeds' will grant access to all
        URLs in the Google Calendar data API. If you would like a token for
        multiple scopes, pass in a list of URL strings.
    hd: The domain to which the user's account belongs. This is set to the
        domain name if you are using Google Apps. Example: 'example.org'
        Defaults to 'default'
    secure: If set to True, all requests should be signed. The default is
        False.
    session: If set to True, the token received by the 'next' URL can be
        upgraded to a multiuse session token. If session is set to False, the
        token may only be used once and cannot be upgraded. Default is True.
    request_url: The base of the URL to which the user will be sent to
        authorize this application to access their data. The default is
        'https://www.google.com/accounts/AuthSubRequest'.
    include_scopes_in_next: Boolean if set to true, the 'next' parameter will
        be modified to include the requested scope as a URL parameter. The
        key for the next's scope parameter will be SCOPE_URL_PARAM_NAME. The
        benefit of including the scope URL as a parameter to the next URL, is
        that the page which receives the AuthSub token will be able to tell
        which URLs the token grants access to.

  Returns:
    A URL string to which the browser should be sent.
  """
  if isinstance(scopes, list):
    scope = ' '.join(scopes)
  else:
    scope = scopes
  if include_scopes_in_next:
    if next.find('?') > -1:
      next += '&%s' % urllib.urlencode({SCOPE_URL_PARAM_NAME:scope})
    else:
      next += '?%s' % urllib.urlencode({SCOPE_URL_PARAM_NAME:scope})
  return gdata.auth.GenerateAuthSubUrl(next=next, scope=scope, secure=secure,
      session=session, request_url=request_url, domain=hd)


class Query(dict):
  """Constructs a query URL to be used in GET requests
  
  Url parameters are created by adding key-value pairs to this object as a 
  dict. For example, to add &max-results=25 to the URL do
  my_query['max-results'] = 25

  Category queries are created by adding category strings to the categories
  member. All items in the categories list will be concatenated with the /
  symbol (symbolizing a category x AND y restriction). If you would like to OR
  2 categories, append them as one string with a | between the categories. 
  For example, do query.categories.append('Fritz|Laurie') to create a query
  like this feed/-/Fritz%7CLaurie . This query will look for results in both
  categories.
  """

  def __init__(self, feed=None, text_query=None, params=None, 
      categories=None):
    """Constructor for Query
    
    Args:
      feed: str (optional) The path for the feed (Examples: 
          '/base/feeds/snippets' or 'calendar/feeds/jo@gmail.com/private/full'
      text_query: str (optional) The contents of the q query parameter. The
          contents of the text_query are URL escaped upon conversion to a URI.
      params: dict (optional) Parameter value string pairs which become URL
          params when translated to a URI. These parameters are added to the
          query's items (key-value pairs).
      categories: list (optional) List of category strings which should be
          included as query categories. See 
          http://code.google.com/apis/gdata/reference.html#Queries for 
          details. If you want to get results from category A or B (both 
          categories), specify a single list item 'A|B'. 
    """
    
    self.feed = feed
    self.categories = []
    if text_query:
      self.text_query = text_query
    if isinstance(params, dict):
      for param in params:
        self[param] = params[param]
    if isinstance(categories, list):
      for category in categories:
        self.categories.append(category)

  def _GetTextQuery(self):
    if 'q' in self.keys():
      return self['q']
    else:
      return None

  def _SetTextQuery(self, query):
    self['q'] = query

  text_query = property(_GetTextQuery, _SetTextQuery, 
      doc="""The feed query's q parameter""")

  def _GetAuthor(self):
    if 'author' in self.keys():
      return self['author']
    else:
      return None

  def _SetAuthor(self, query):
    self['author'] = query

  author = property(_GetAuthor, _SetAuthor,
      doc="""The feed query's author parameter""")

  def _GetAlt(self):
    if 'alt' in self.keys():
      return self['alt']
    else:
      return None

  def _SetAlt(self, query):
    self['alt'] = query

  alt = property(_GetAlt, _SetAlt,
      doc="""The feed query's alt parameter""")

  def _GetUpdatedMin(self):
    if 'updated-min' in self.keys():
      return self['updated-min']
    else:
      return None

  def _SetUpdatedMin(self, query):
    self['updated-min'] = query

  updated_min = property(_GetUpdatedMin, _SetUpdatedMin,
      doc="""The feed query's updated-min parameter""")

  def _GetUpdatedMax(self):
    if 'updated-max' in self.keys():
      return self['updated-max']
    else:
      return None

  def _SetUpdatedMax(self, query):
    self['updated-max'] = query

  updated_max = property(_GetUpdatedMax, _SetUpdatedMax,
      doc="""The feed query's updated-max parameter""")

  def _GetPublishedMin(self):
    if 'published-min' in self.keys():
      return self['published-min']
    else:
      return None

  def _SetPublishedMin(self, query):
    self['published-min'] = query

  published_min = property(_GetPublishedMin, _SetPublishedMin,
      doc="""The feed query's published-min parameter""")

  def _GetPublishedMax(self):
    if 'published-max' in self.keys():
      return self['published-max']
    else:
      return None

  def _SetPublishedMax(self, query):
    self['published-max'] = query

  published_max = property(_GetPublishedMax, _SetPublishedMax,
      doc="""The feed query's published-max parameter""")

  def _GetStartIndex(self):
    if 'start-index' in self.keys():
      return self['start-index']
    else:
      return None

  def _SetStartIndex(self, query):
    if not isinstance(query, str):
      query = str(query)
    self['start-index'] = query

  start_index = property(_GetStartIndex, _SetStartIndex,
      doc="""The feed query's start-index parameter""")

  def _GetMaxResults(self):
    if 'max-results' in self.keys():
      return self['max-results']
    else:
      return None

  def _SetMaxResults(self, query):
    if not isinstance(query, str):
      query = str(query)
    self['max-results'] = query

  max_results = property(_GetMaxResults, _SetMaxResults,
      doc="""The feed query's max-results parameter""")

  def _GetOrderBy(self):
    if 'orderby' in self.keys():
      return self['orderby']
    else:
      return None
 
  def _SetOrderBy(self, query):
    self['orderby'] = query
  
  orderby = property(_GetOrderBy, _SetOrderBy, 
      doc="""The feed query's orderby parameter""")

  def ToUri(self):
    q_feed = self.feed or ''
    category_string = '/'.join(
        [urllib.quote_plus(c) for c in self.categories])
    # Add categories to the feed if there are any.
    if len(self.categories) > 0:
      q_feed = q_feed + '/-/' + category_string
    return atom.service.BuildUri(q_feed, self)

  def __str__(self):
    return self.ToUri()
