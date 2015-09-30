#!/usr/bin/python
#
# Copyright (C) 2007 - 2009 Google Inc.
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


import cgi
import math
import random
import re
import time
import types
import urllib
import atom.http_interface
import atom.token_store
import atom.url
import gdata.oauth as oauth
import gdata.oauth.rsa as oauth_rsa
import gdata.tlslite.utils.keyfactory as keyfactory
import gdata.tlslite.utils.cryptomath as cryptomath

import gdata.gauth

__author__ = 'api.jscudder (Jeff Scudder)'


PROGRAMMATIC_AUTH_LABEL = 'GoogleLogin auth='
AUTHSUB_AUTH_LABEL = 'AuthSub token='


"""This module provides functions and objects used with Google authentication.

Details on Google authorization mechanisms used with the Google Data APIs can
be found here: 
http://code.google.com/apis/gdata/auth.html
http://code.google.com/apis/accounts/

The essential functions are the following.
Related to ClientLogin:
  generate_client_login_request_body: Constructs the body of an HTTP request to
                                      obtain a ClientLogin token for a specific
                                      service. 
  extract_client_login_token: Creates a ClientLoginToken with the token from a
                              success response to a ClientLogin request.
  get_captcha_challenge: If the server responded to the ClientLogin request
                         with a CAPTCHA challenge, this method extracts the
                         CAPTCHA URL and identifying CAPTCHA token.

Related to AuthSub:
  generate_auth_sub_url: Constructs a full URL for a AuthSub request. The 
                         user's browser must be sent to this Google Accounts
                         URL and redirected back to the app to obtain the
                         AuthSub token.
  extract_auth_sub_token_from_url: Once the user's browser has been 
                                   redirected back to the web app, use this
                                   function to create an AuthSubToken with
                                   the correct authorization token and scope.
  token_from_http_body: Extracts the AuthSubToken value string from the 
                        server's response to an AuthSub session token upgrade
                        request.
"""

def generate_client_login_request_body(email, password, service, source, 
    account_type='HOSTED_OR_GOOGLE', captcha_token=None, 
    captcha_response=None):
  """Creates the body of the autentication request

  See http://code.google.com/apis/accounts/AuthForInstalledApps.html#Request
  for more details.

  Args:
    email: str
    password: str
    service: str
    source: str
    account_type: str (optional) Defaul is 'HOSTED_OR_GOOGLE', other valid
        values are 'GOOGLE' and 'HOSTED'
    captcha_token: str (optional)
    captcha_response: str (optional)

  Returns:
    The HTTP body to send in a request for a client login token.
  """
  return gdata.gauth.generate_client_login_request_body(email, password,
      service, source, account_type, captcha_token, captcha_response)


GenerateClientLoginRequestBody = generate_client_login_request_body


def GenerateClientLoginAuthToken(http_body):
  """Returns the token value to use in Authorization headers.

  Reads the token from the server's response to a Client Login request and
  creates header value to use in requests.

  Args:
    http_body: str The body of the server's HTTP response to a Client Login
        request
 
  Returns:
    The value half of an Authorization header.
  """
  token = get_client_login_token(http_body)
  if token:
    return 'GoogleLogin auth=%s' % token
  return None


def get_client_login_token(http_body):
  """Returns the token value for a ClientLoginToken.

  Reads the token from the server's response to a Client Login request and
  creates the token value string to use in requests.

  Args:
    http_body: str The body of the server's HTTP response to a Client Login
        request
 
  Returns:
    The token value string for a ClientLoginToken.
  """
  return gdata.gauth.get_client_login_token_string(http_body)


def extract_client_login_token(http_body, scopes):
  """Parses the server's response and returns a ClientLoginToken.
  
  Args:
    http_body: str The body of the server's HTTP response to a Client Login
               request. It is assumed that the login request was successful.
    scopes: list containing atom.url.Urls or strs. The scopes list contains
            all of the partial URLs under which the client login token is
            valid. For example, if scopes contains ['http://example.com/foo']
            then the client login token would be valid for 
            http://example.com/foo/bar/baz

  Returns:
    A ClientLoginToken which is valid for the specified scopes.
  """
  token_string = get_client_login_token(http_body)
  token = ClientLoginToken(scopes=scopes)
  token.set_token_string(token_string)
  return token


def get_captcha_challenge(http_body, 
    captcha_base_url='http://www.google.com/accounts/'):
  """Returns the URL and token for a CAPTCHA challenge issued by the server.

  Args:
    http_body: str The body of the HTTP response from the server which 
        contains the CAPTCHA challenge.
    captcha_base_url: str This function returns a full URL for viewing the 
        challenge image which is built from the server's response. This
        base_url is used as the beginning of the URL because the server
        only provides the end of the URL. For example the server provides
        'Captcha?ctoken=Hi...N' and the URL for the image is
        'http://www.google.com/accounts/Captcha?ctoken=Hi...N'

  Returns:
    A dictionary containing the information needed to repond to the CAPTCHA
    challenge, the image URL and the ID token of the challenge. The 
    dictionary is in the form:
    {'token': string identifying the CAPTCHA image,
     'url': string containing the URL of the image}
    Returns None if there was no CAPTCHA challenge in the response.
  """
  return gdata.gauth.get_captcha_challenge(http_body, captcha_base_url)


GetCaptchaChallenge = get_captcha_challenge


def GenerateOAuthRequestTokenUrl(
    oauth_input_params, scopes,
    request_token_url='https://www.google.com/accounts/OAuthGetRequestToken',
    extra_parameters=None):
  """Generate a URL at which a request for OAuth request token is to be sent.
  
  Args:
    oauth_input_params: OAuthInputParams OAuth input parameters.
    scopes: list of strings The URLs of the services to be accessed.
    request_token_url: string The beginning of the request token URL. This is
        normally 'https://www.google.com/accounts/OAuthGetRequestToken' or
        '/accounts/OAuthGetRequestToken'
    extra_parameters: dict (optional) key-value pairs as any additional
        parameters to be included in the URL and signature while making a
        request for fetching an OAuth request token. All the OAuth parameters
        are added by default. But if provided through this argument, any
        default parameters will be overwritten. For e.g. a default parameter
        oauth_version 1.0 can be overwritten if
        extra_parameters = {'oauth_version': '2.0'}
  
  Returns:
    atom.url.Url OAuth request token URL.
  """
  scopes_string = ' '.join([str(scope) for scope in scopes])
  parameters = {'scope': scopes_string}
  if extra_parameters:
    parameters.update(extra_parameters)
  oauth_request = oauth.OAuthRequest.from_consumer_and_token(
      oauth_input_params.GetConsumer(), http_url=request_token_url,
      parameters=parameters)
  oauth_request.sign_request(oauth_input_params.GetSignatureMethod(),
                             oauth_input_params.GetConsumer(), None)
  return atom.url.parse_url(oauth_request.to_url())


def GenerateOAuthAuthorizationUrl(
    request_token,
    authorization_url='https://www.google.com/accounts/OAuthAuthorizeToken',
    callback_url=None, extra_params=None,
    include_scopes_in_callback=False, scopes_param_prefix='oauth_token_scope'):
  """Generates URL at which user will login to authorize the request token.
  
  Args:
    request_token: gdata.auth.OAuthToken OAuth request token.
    authorization_url: string The beginning of the authorization URL. This is
        normally 'https://www.google.com/accounts/OAuthAuthorizeToken' or
        '/accounts/OAuthAuthorizeToken'
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

  Returns:
    atom.url.Url OAuth authorization URL.
  """
  scopes = request_token.scopes
  if isinstance(scopes, list):
    scopes = ' '.join(scopes)  
  if include_scopes_in_callback and callback_url:
    if callback_url.find('?') > -1:
      callback_url += '&'
    else:
      callback_url += '?'
    callback_url += urllib.urlencode({scopes_param_prefix:scopes})  
  oauth_token = oauth.OAuthToken(request_token.key, request_token.secret)
  oauth_request = oauth.OAuthRequest.from_token_and_callback(
      token=oauth_token, callback=callback_url,
      http_url=authorization_url, parameters=extra_params)
  return atom.url.parse_url(oauth_request.to_url())


def GenerateOAuthAccessTokenUrl(
    authorized_request_token,
    oauth_input_params,
    access_token_url='https://www.google.com/accounts/OAuthGetAccessToken',
    oauth_version='1.0',
    oauth_verifier=None):
  """Generates URL at which user will login to authorize the request token.
  
  Args:
    authorized_request_token: gdata.auth.OAuthToken OAuth authorized request
        token.
    oauth_input_params: OAuthInputParams OAuth input parameters.    
    access_token_url: string The beginning of the authorization URL. This is
        normally 'https://www.google.com/accounts/OAuthGetAccessToken' or
        '/accounts/OAuthGetAccessToken'
    oauth_version: str (default='1.0') oauth_version parameter.
    oauth_verifier: str (optional) If present, it is assumed that the client
        will use the OAuth v1.0a protocol which includes passing the
        oauth_verifier (as returned by the SP) in the access token step.

  Returns:
    atom.url.Url OAuth access token URL.
  """
  oauth_token = oauth.OAuthToken(authorized_request_token.key,
                                 authorized_request_token.secret)
  parameters = {'oauth_version': oauth_version}
  if oauth_verifier is not None:
    parameters['oauth_verifier'] = oauth_verifier
  oauth_request = oauth.OAuthRequest.from_consumer_and_token(
      oauth_input_params.GetConsumer(), token=oauth_token,
      http_url=access_token_url, parameters=parameters)
  oauth_request.sign_request(oauth_input_params.GetSignatureMethod(),
                             oauth_input_params.GetConsumer(), oauth_token)
  return atom.url.parse_url(oauth_request.to_url())


def GenerateAuthSubUrl(next, scope, secure=False, session=True, 
    request_url='https://www.google.com/accounts/AuthSubRequest',
    domain='default'):
  """Generate a URL at which the user will login and be redirected back.

  Users enter their credentials on a Google login page and a token is sent
  to the URL specified in next. See documentation for AuthSub login at:
  http://code.google.com/apis/accounts/AuthForWebApps.html

  Args:
    request_url: str The beginning of the request URL. This is normally
        'http://www.google.com/accounts/AuthSubRequest' or 
        '/accounts/AuthSubRequest'
    next: string The URL user will be sent to after logging in.
    scope: string The URL of the service to be accessed.
    secure: boolean (optional) Determines whether or not the issued token
            is a secure token.
    session: boolean (optional) Determines whether or not the issued token
             can be upgraded to a session token.
    domain: str (optional) The Google Apps domain for this account. If this
            is not a Google Apps account, use 'default' which is the default
            value.
  """
  # Translate True/False values for parameters into numeric values acceoted
  # by the AuthSub service.
  if secure:
    secure = 1
  else:
    secure = 0

  if session:
    session = 1
  else:
    session = 0

  request_params = urllib.urlencode({'next': next, 'scope': scope,
                                     'secure': secure, 'session': session, 
                                     'hd': domain})
  if request_url.find('?') == -1:
    return '%s?%s' % (request_url, request_params)
  else:
    # The request URL already contained url parameters so we should add
    # the parameters using the & seperator
    return '%s&%s' % (request_url, request_params)


def generate_auth_sub_url(next, scopes, secure=False, session=True,
    request_url='https://www.google.com/accounts/AuthSubRequest', 
    domain='default', scopes_param_prefix='auth_sub_scopes'):
  """Constructs a URL string for requesting a multiscope AuthSub token.

  The generated token will contain a URL parameter to pass along the 
  requested scopes to the next URL. When the Google Accounts page 
  redirects the broswser to the 'next' URL, it appends the single use
  AuthSub token value to the URL as a URL parameter with the key 'token'.
  However, the information about which scopes were requested is not
  included by Google Accounts. This method adds the scopes to the next
  URL before making the request so that the redirect will be sent to 
  a page, and both the token value and the list of scopes can be 
  extracted from the request URL. 

  Args:
    next: atom.url.URL or string The URL user will be sent to after
          authorizing this web application to access their data.
    scopes: list containint strings The URLs of the services to be accessed.
    secure: boolean (optional) Determines whether or not the issued token
            is a secure token.
    session: boolean (optional) Determines whether or not the issued token
             can be upgraded to a session token.
    request_url: atom.url.Url or str The beginning of the request URL. This
        is normally 'http://www.google.com/accounts/AuthSubRequest' or 
        '/accounts/AuthSubRequest'
    domain: The domain which the account is part of. This is used for Google
        Apps accounts, the default value is 'default' which means that the
        requested account is a Google Account (@gmail.com for example)
    scopes_param_prefix: str (optional) The requested scopes are added as a 
        URL parameter to the next URL so that the page at the 'next' URL can
        extract the token value and the valid scopes from the URL. The key
        for the URL parameter defaults to 'auth_sub_scopes'

  Returns:
    An atom.url.Url which the user's browser should be directed to in order
    to authorize this application to access their information.
  """
  if isinstance(next, (str, unicode)):
    next = atom.url.parse_url(next)
  scopes_string = ' '.join([str(scope) for scope in scopes])
  next.params[scopes_param_prefix] = scopes_string

  if isinstance(request_url, (str, unicode)):
    request_url = atom.url.parse_url(request_url)
  request_url.params['next'] = str(next)
  request_url.params['scope'] = scopes_string
  if session:
    request_url.params['session'] = 1
  else:
    request_url.params['session'] = 0
  if secure:
    request_url.params['secure'] = 1
  else:
    request_url.params['secure'] = 0
  request_url.params['hd'] = domain
  return request_url


def AuthSubTokenFromUrl(url):
  """Extracts the AuthSub token from the URL. 

  Used after the AuthSub redirect has sent the user to the 'next' page and
  appended the token to the URL. This function returns the value to be used
  in the Authorization header. 

  Args:
    url: str The URL of the current page which contains the AuthSub token as
        a URL parameter.
  """
  token = TokenFromUrl(url)
  if token:
    return 'AuthSub token=%s' % token
  return None


def TokenFromUrl(url):
  """Extracts the AuthSub token from the URL.

  Returns the raw token value.

  Args:
    url: str The URL or the query portion of the URL string (after the ?) of
        the current page which contains the AuthSub token as a URL parameter.
  """
  if url.find('?') > -1:
    query_params = url.split('?')[1]
  else:
    query_params = url
  for pair in query_params.split('&'):
    if pair.startswith('token='):
      return pair[6:]
  return None


def extract_auth_sub_token_from_url(url, 
    scopes_param_prefix='auth_sub_scopes', rsa_key=None):
  """Creates an AuthSubToken and sets the token value and scopes from the URL.
  
  After the Google Accounts AuthSub pages redirect the user's broswer back to 
  the web application (using the 'next' URL from the request) the web app must
  extract the token from the current page's URL. The token is provided as a 
  URL parameter named 'token' and if generate_auth_sub_url was used to create
  the request, the token's valid scopes are included in a URL parameter whose
  name is specified in scopes_param_prefix.

  Args:
    url: atom.url.Url or str representing the current URL. The token value
         and valid scopes should be included as URL parameters.
    scopes_param_prefix: str (optional) The URL parameter key which maps to
                         the list of valid scopes for the token.

  Returns:
    An AuthSubToken with the token value from the URL and set to be valid for
    the scopes passed in on the URL. If no scopes were included in the URL,
    the AuthSubToken defaults to being valid for no scopes. If there was no
    'token' parameter in the URL, this function returns None.
  """
  if isinstance(url, (str, unicode)):
    url = atom.url.parse_url(url)
  if 'token' not in url.params:
    return None
  scopes = []
  if scopes_param_prefix in url.params:
    scopes = url.params[scopes_param_prefix].split(' ')
  token_value = url.params['token']
  if rsa_key:
    token = SecureAuthSubToken(rsa_key, scopes=scopes)
  else:
    token = AuthSubToken(scopes=scopes)
  token.set_token_string(token_value)
  return token


def AuthSubTokenFromHttpBody(http_body):
  """Extracts the AuthSub token from an HTTP body string.

  Used to find the new session token after making a request to upgrade a
  single use AuthSub token.

  Args:
    http_body: str The repsonse from the server which contains the AuthSub
        key. For example, this function would find the new session token
        from the server's response to an upgrade token request.

  Returns:
    The header value to use for Authorization which contains the AuthSub
    token.
  """
  token_value = token_from_http_body(http_body)
  if token_value:
    return '%s%s' % (AUTHSUB_AUTH_LABEL, token_value)
  return None


def token_from_http_body(http_body):
  """Extracts the AuthSub token from an HTTP body string.

  Used to find the new session token after making a request to upgrade a 
  single use AuthSub token.

  Args:
    http_body: str The repsonse from the server which contains the AuthSub 
        key. For example, this function would find the new session token
        from the server's response to an upgrade token request.

  Returns:
    The raw token value to use in an AuthSubToken object.
  """
  for response_line in http_body.splitlines():
    if response_line.startswith('Token='):
      # Strip off Token= and return the token value string.
      return response_line[6:]
  return None


TokenFromHttpBody = token_from_http_body


def OAuthTokenFromUrl(url, scopes_param_prefix='oauth_token_scope'):
  """Creates an OAuthToken and sets token key and scopes (if present) from URL.
  
  After the Google Accounts OAuth pages redirect the user's broswer back to 
  the web application (using the 'callback' URL from the request) the web app
  can extract the token from the current page's URL. The token is same as the
  request token, but it is either authorized (if user grants access) or
  unauthorized (if user denies access). The token is provided as a 
  URL parameter named 'oauth_token' and if it was chosen to use
  GenerateOAuthAuthorizationUrl with include_scopes_in_param=True, the token's
  valid scopes are included in a URL parameter whose name is specified in
  scopes_param_prefix.

  Args:
    url: atom.url.Url or str representing the current URL. The token value
        and valid scopes should be included as URL parameters.
    scopes_param_prefix: str (optional) The URL parameter key which maps to
        the list of valid scopes for the token.

  Returns:
    An OAuthToken with the token key from the URL and set to be valid for
    the scopes passed in on the URL. If no scopes were included in the URL,
    the OAuthToken defaults to being valid for no scopes. If there was no
    'oauth_token' parameter in the URL, this function returns None.
  """
  if isinstance(url, (str, unicode)):
    url = atom.url.parse_url(url)
  if 'oauth_token' not in url.params:
    return None
  scopes = []
  if scopes_param_prefix in url.params:
    scopes = url.params[scopes_param_prefix].split(' ')
  token_key = url.params['oauth_token']
  token = OAuthToken(key=token_key, scopes=scopes)
  return token


def OAuthTokenFromHttpBody(http_body):
  """Parses the HTTP response body and returns an OAuth token.
  
  The returned OAuth token will just have key and secret parameters set.
  It won't have any knowledge about the scopes or oauth_input_params. It is
  your responsibility to make it aware of the remaining parameters.
  
  Returns:
    OAuthToken OAuth token.
  """
  token = oauth.OAuthToken.from_string(http_body)
  oauth_token = OAuthToken(key=token.key, secret=token.secret)
  return oauth_token
  

class OAuthSignatureMethod(object):
  """Holds valid OAuth signature methods.
  
  RSA_SHA1: Class to build signature according to RSA-SHA1 algorithm.
  HMAC_SHA1: Class to build signature according to HMAC-SHA1 algorithm.
  """
  
  HMAC_SHA1 = oauth.OAuthSignatureMethod_HMAC_SHA1  
  
  class RSA_SHA1(oauth_rsa.OAuthSignatureMethod_RSA_SHA1):
    """Provides implementation for abstract methods to return RSA certs."""

    def __init__(self, private_key, public_cert):
      self.private_key = private_key
      self.public_cert = public_cert
  
    def _fetch_public_cert(self, unused_oauth_request):
      return self.public_cert
  
    def _fetch_private_cert(self, unused_oauth_request):
      return self.private_key
  

class OAuthInputParams(object):
  """Stores OAuth input parameters.
  
  This class is a store for OAuth input parameters viz. consumer key and secret,
  signature method and RSA key.
  """
  
  def __init__(self, signature_method, consumer_key, consumer_secret=None,
               rsa_key=None, requestor_id=None):
    """Initializes object with parameters required for using OAuth mechanism.
    
    NOTE: Though consumer_secret and rsa_key are optional, either of the two
    is required depending on the value of the signature_method.
    
    Args:
      signature_method: class which provides implementation for strategy class
          oauth.oauth.OAuthSignatureMethod. Signature method to be used for
          signing each request. Valid implementations are provided as the
          constants defined by gdata.auth.OAuthSignatureMethod. Currently
          they are gdata.auth.OAuthSignatureMethod.RSA_SHA1 and
          gdata.auth.OAuthSignatureMethod.HMAC_SHA1. Instead of passing in
          the strategy class, you may pass in a string for 'RSA_SHA1' or 
          'HMAC_SHA1'. If you plan to use OAuth on App Engine (or another
          WSGI environment) I recommend specifying signature method using a
          string (the only options are 'RSA_SHA1' and 'HMAC_SHA1'). In these
          environments there are sometimes issues with pickling an object in 
          which a member references a class or function. Storing a string to
          refer to the signature method mitigates complications when
          pickling.
      consumer_key: string Domain identifying third_party web application.
      consumer_secret: string (optional) Secret generated during registration.
          Required only for HMAC_SHA1 signature method.
      rsa_key: string (optional) Private key required for RSA_SHA1 signature
          method.
      requestor_id: string (optional) User email adress to make requests on
          their behalf.  This parameter should only be set when performing
          2 legged OAuth requests.
    """
    if (signature_method == OAuthSignatureMethod.RSA_SHA1
        or signature_method == 'RSA_SHA1'):
      self.__signature_strategy = 'RSA_SHA1'
    elif (signature_method == OAuthSignatureMethod.HMAC_SHA1
        or signature_method == 'HMAC_SHA1'):
      self.__signature_strategy = 'HMAC_SHA1'
    else:
      self.__signature_strategy = signature_method
    self.rsa_key = rsa_key
    self._consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
    self.requestor_id = requestor_id

  def __get_signature_method(self):
    if self.__signature_strategy == 'RSA_SHA1':
      return OAuthSignatureMethod.RSA_SHA1(self.rsa_key, None)
    elif self.__signature_strategy == 'HMAC_SHA1':
      return OAuthSignatureMethod.HMAC_SHA1()
    else:
      return self.__signature_strategy()

  def __set_signature_method(self, signature_method):
    if (signature_method == OAuthSignatureMethod.RSA_SHA1
        or signature_method == 'RSA_SHA1'):
      self.__signature_strategy = 'RSA_SHA1'
    elif (signature_method == OAuthSignatureMethod.HMAC_SHA1
        or signature_method == 'HMAC_SHA1'):
      self.__signature_strategy = 'HMAC_SHA1'
    else:
      self.__signature_strategy = signature_method

  _signature_method = property(__get_signature_method, __set_signature_method,
      doc="""Returns object capable of signing the request using RSA of HMAC.
      
      Replaces the _signature_method member to avoid pickle errors.""")

  def GetSignatureMethod(self):
    """Gets the OAuth signature method.

    Returns:
      object of supertype <oauth.oauth.OAuthSignatureMethod>
    """
    return self._signature_method

  def GetConsumer(self):
    """Gets the OAuth consumer.

    Returns:
      object of type <oauth.oauth.Consumer>
    """
    return self._consumer


class ClientLoginToken(atom.http_interface.GenericToken):
  """Stores the Authorization header in auth_header and adds to requests.

  This token will add it's Authorization header to an HTTP request
  as it is made. Ths token class is simple but
  some Token classes must calculate portions of the Authorization header
  based on the request being made, which is why the token is responsible
  for making requests via an http_client parameter.

  Args:
    auth_header: str The value for the Authorization header.
    scopes: list of str or atom.url.Url specifying the beginnings of URLs
        for which this token can be used. For example, if scopes contains
        'http://example.com/foo', then this token can be used for a request to
        'http://example.com/foo/bar' but it cannot be used for a request to
        'http://example.com/baz'
  """
  def __init__(self, auth_header=None, scopes=None):
    self.auth_header = auth_header
    self.scopes = scopes or []

  def __str__(self):
    return self.auth_header

  def perform_request(self, http_client, operation, url, data=None,
                      headers=None):
    """Sets the Authorization header and makes the HTTP request."""
    if headers is None:
      headers = {'Authorization':self.auth_header}
    else:
      headers['Authorization'] = self.auth_header
    return http_client.request(operation, url, data=data, headers=headers)

  def get_token_string(self):
    """Removes PROGRAMMATIC_AUTH_LABEL to give just the token value."""
    return self.auth_header[len(PROGRAMMATIC_AUTH_LABEL):]

  def set_token_string(self, token_string):
    self.auth_header = '%s%s' % (PROGRAMMATIC_AUTH_LABEL, token_string)
  
  def valid_for_scope(self, url):
    """Tells the caller if the token authorizes access to the desired URL.
    """
    if isinstance(url, (str, unicode)):
      url = atom.url.parse_url(url)
    for scope in self.scopes:
      if scope == atom.token_store.SCOPE_ALL:
        return True
      if isinstance(scope, (str, unicode)):
        scope = atom.url.parse_url(scope)
      if scope == url:
        return True
      # Check the host and the path, but ignore the port and protocol.
      elif scope.host == url.host and not scope.path:
        return True
      elif scope.host == url.host and scope.path and not url.path:
        continue
      elif scope.host == url.host and url.path.startswith(scope.path):
        return True
    return False


class AuthSubToken(ClientLoginToken):
  def get_token_string(self):
    """Removes AUTHSUB_AUTH_LABEL to give just the token value."""
    return self.auth_header[len(AUTHSUB_AUTH_LABEL):]

  def set_token_string(self, token_string):
    self.auth_header = '%s%s' % (AUTHSUB_AUTH_LABEL, token_string)


class OAuthToken(atom.http_interface.GenericToken):
  """Stores the token key, token secret and scopes for which token is valid.
  
  This token adds the authorization header to each request made. It
  re-calculates authorization header for every request since the OAuth
  signature to be added to the authorization header is dependent on the
  request parameters.
  
  Attributes:
    key: str The value for the OAuth token i.e. token key.
    secret: str The value for the OAuth token secret.
    scopes: list of str or atom.url.Url specifying the beginnings of URLs
        for which this token can be used. For example, if scopes contains
        'http://example.com/foo', then this token can be used for a request to
        'http://example.com/foo/bar' but it cannot be used for a request to
        'http://example.com/baz'
    oauth_input_params: OAuthInputParams OAuth input parameters.      
  """
  
  def __init__(self, key=None, secret=None, scopes=None,
               oauth_input_params=None):
    self.key = key
    self.secret = secret
    self.scopes = scopes or []
    self.oauth_input_params = oauth_input_params
  
  def __str__(self):
    return self.get_token_string()

  def get_token_string(self):
    """Returns the token string.
    
    The token string returned is of format
    oauth_token=[0]&oauth_token_secret=[1], where [0] and [1] are some strings.
    
    Returns:
      A token string of format oauth_token=[0]&oauth_token_secret=[1],
      where [0] and [1] are some strings. If self.secret is absent, it just
      returns oauth_token=[0]. If self.key is absent, it just returns
      oauth_token_secret=[1]. If both are absent, it returns None.
    """
    if self.key and self.secret:
      return urllib.urlencode({'oauth_token': self.key,
                               'oauth_token_secret': self.secret})
    elif self.key:
      return 'oauth_token=%s' % self.key
    elif self.secret:
      return 'oauth_token_secret=%s' % self.secret
    else:
      return None

  def set_token_string(self, token_string):
    """Sets the token key and secret from the token string.
    
    Args:
      token_string: str Token string of form
          oauth_token=[0]&oauth_token_secret=[1]. If oauth_token is not present,
          self.key will be None. If oauth_token_secret is not present,
          self.secret will be None.
    """
    token_params = cgi.parse_qs(token_string, keep_blank_values=False)
    if 'oauth_token' in token_params:
      self.key = token_params['oauth_token'][0]
    if 'oauth_token_secret' in token_params:
      self.secret = token_params['oauth_token_secret'][0]
    
  def GetAuthHeader(self, http_method, http_url, realm=''):
    """Get the authentication header.

    Args:
      http_method: string HTTP method i.e. operation e.g. GET, POST, PUT, etc.
      http_url: string or atom.url.Url HTTP URL to which request is made.
      realm: string (default='') realm parameter to be included in the
          authorization header.

    Returns:
      dict Header to be sent with every subsequent request after
      authentication.
    """
    if isinstance(http_url, types.StringTypes):
      http_url = atom.url.parse_url(http_url)
    header = None
    token = None
    if self.key or self.secret:
      token = oauth.OAuthToken(self.key, self.secret)
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        self.oauth_input_params.GetConsumer(), token=token,
        http_url=str(http_url), http_method=http_method,
        parameters=http_url.params)
    oauth_request.sign_request(self.oauth_input_params.GetSignatureMethod(),
                               self.oauth_input_params.GetConsumer(), token)
    header = oauth_request.to_header(realm=realm)
    header['Authorization'] = header['Authorization'].replace('+', '%2B')
    return header
  
  def perform_request(self, http_client, operation, url, data=None,
                      headers=None):
    """Sets the Authorization header and makes the HTTP request."""
    if not headers:
      headers = {}
    if self.oauth_input_params.requestor_id:
      url.params['xoauth_requestor_id'] = self.oauth_input_params.requestor_id
    headers.update(self.GetAuthHeader(operation, url))
    return http_client.request(operation, url, data=data, headers=headers)
    
  def valid_for_scope(self, url):
    if isinstance(url, (str, unicode)):
      url = atom.url.parse_url(url)
    for scope in self.scopes:
      if scope == atom.token_store.SCOPE_ALL:
        return True
      if isinstance(scope, (str, unicode)):
        scope = atom.url.parse_url(scope)
      if scope == url:
        return True
      # Check the host and the path, but ignore the port and protocol.
      elif scope.host == url.host and not scope.path:
        return True
      elif scope.host == url.host and scope.path and not url.path:
        continue
      elif scope.host == url.host and url.path.startswith(scope.path):
        return True
    return False    
    

class SecureAuthSubToken(AuthSubToken):
  """Stores the rsa private key, token, and scopes for the secure AuthSub token.
  
  This token adds the authorization header to each request made. It
  re-calculates authorization header for every request since the secure AuthSub
  signature to be added to the authorization header is dependent on the
  request parameters.
  
  Attributes:
    rsa_key: string The RSA private key in PEM format that the token will
             use to sign requests
    token_string: string (optional) The value for the AuthSub token.
    scopes: list of str or atom.url.Url specifying the beginnings of URLs
        for which this token can be used. For example, if scopes contains
        'http://example.com/foo', then this token can be used for a request to
        'http://example.com/foo/bar' but it cannot be used for a request to
        'http://example.com/baz'     
  """
  
  def __init__(self, rsa_key, token_string=None, scopes=None):
    self.rsa_key = keyfactory.parsePEMKey(rsa_key)
    self.token_string = token_string or ''
    self.scopes = scopes or [] 
   
  def __str__(self):
    return self.get_token_string()

  def get_token_string(self):
    return str(self.token_string)

  def set_token_string(self, token_string):
    self.token_string = token_string
    
  def GetAuthHeader(self, http_method, http_url):
    """Generates the Authorization header.

    The form of the secure AuthSub Authorization header is
    Authorization: AuthSub token="token" sigalg="sigalg" data="data" sig="sig"
    and  data represents a string in the form
    data = http_method http_url timestamp nonce

    Args:
      http_method: string HTTP method i.e. operation e.g. GET, POST, PUT, etc.
      http_url: string or atom.url.Url HTTP URL to which request is made.
      
    Returns:
      dict Header to be sent with every subsequent request after authentication.
    """
    timestamp = int(math.floor(time.time()))
    nonce = '%lu' % random.randrange(1, 2**64)
    data = '%s %s %d %s' % (http_method, str(http_url), timestamp, nonce)
    sig = cryptomath.bytesToBase64(self.rsa_key.hashAndSign(data))
    header = {'Authorization': '%s"%s" data="%s" sig="%s" sigalg="rsa-sha1"' %
              (AUTHSUB_AUTH_LABEL, self.token_string, data, sig)}
    return header
  
  def perform_request(self, http_client, operation, url, data=None, 
                      headers=None):
    """Sets the Authorization header and makes the HTTP request."""
    if not headers:
      headers = {}
    headers.update(self.GetAuthHeader(operation, url))
    return http_client.request(operation, url, data=data, headers=headers)
