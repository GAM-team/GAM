#!/usr/bin/env python
#
# Copyright (C) 2009 Google Inc.
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


"""AtomPubClient provides CRUD ops. in line with the Atom Publishing Protocol.

"""

__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.http_core


class Error(Exception):
  pass


class MissingHost(Error):
  pass


class AtomPubClient(object):
  host = None
  auth_token = None
  ssl = False # Whether to force all requests over https
  xoauth_requestor_id = None

  def __init__(self, http_client=None, host=None, auth_token=None, source=None,
               xoauth_requestor_id=None, **kwargs):
    """Creates a new AtomPubClient instance.

    Args:
      source: The name of your application.
      http_client: An object capable of performing HTTP requests through a
                   request method. This object is used to perform the request
                   when the AtomPubClient's request method is called. Used to
                   allow HTTP requests to be directed to a mock server, or use
                   an alternate library instead of the default of httplib to
                   make HTTP requests.
      host: str The default host name to use if a host is not specified in the
            requested URI.
      auth_token: An object which sets the HTTP Authorization header when its
                  modify_request method is called.
    """
    self.http_client = http_client or atom.http_core.ProxiedHttpClient()
    if host is not None:
      self.host = host
    if auth_token is not None:
      self.auth_token = auth_token
    self.xoauth_requestor_id = xoauth_requestor_id
    self.source = source

  def request(self, method=None, uri=None, auth_token=None,
              http_request=None, **kwargs):
    """Performs an HTTP request to the server indicated.

    Uses the http_client instance to make the request.

    Args:
      method: The HTTP method as a string, usually one of 'GET', 'POST',
              'PUT', or 'DELETE'
      uri: The URI desired as a string or atom.http_core.Uri.
      http_request:
      auth_token: An authorization token object whose modify_request method
                  sets the HTTP Authorization header.

    Returns:
      The results of calling self.http_client.request. With the default
      http_client, this is an HTTP response object.
    """
    # Modify the request based on the AtomPubClient settings and parameters
    # passed in to the request.
    http_request = self.modify_request(http_request)
    if isinstance(uri, (str, unicode)):
      uri = atom.http_core.Uri.parse_uri(uri)
    if uri is not None:
      uri.modify_request(http_request)
    if isinstance(method, (str, unicode)):
      http_request.method = method
    # Any unrecognized arguments are assumed to be capable of modifying the
    # HTTP request.
    for name, value in kwargs.iteritems():
      if value is not None:
        value.modify_request(http_request)
    # Default to an http request if the protocol scheme is not set.
    if http_request.uri.scheme is None:
      http_request.uri.scheme = 'http'
    # Override scheme. Force requests over https.
    if self.ssl:
      http_request.uri.scheme = 'https'
    if http_request.uri.path is None:
      http_request.uri.path = '/'
    # Add the Authorization header at the very end. The Authorization header
    # value may need to be calculated using information in the request.
    if auth_token:
      auth_token.modify_request(http_request)
    elif self.auth_token:
      self.auth_token.modify_request(http_request)
    # Check to make sure there is a host in the http_request.
    if http_request.uri.host is None:
      raise MissingHost('No host provided in request %s %s' % (
          http_request.method, str(http_request.uri)))
    # Perform the fully specified request using the http_client instance.
    # Sends the request to the server and returns the server's response.
    return self.http_client.request(http_request)

  Request = request

  def get(self, uri=None, auth_token=None, http_request=None, **kwargs):
    """Performs a request using the GET method, returns an HTTP response."""
    return self.request(method='GET', uri=uri, auth_token=auth_token,
                        http_request=http_request, **kwargs)

  Get = get

  def post(self, uri=None, data=None, auth_token=None, http_request=None,
           **kwargs):
    """Sends data using the POST method, returns an HTTP response."""
    return self.request(method='POST', uri=uri, auth_token=auth_token,
                        http_request=http_request, data=data, **kwargs)

  Post = post

  def put(self, uri=None, data=None, auth_token=None, http_request=None,
          **kwargs):
    """Sends data using the PUT method, returns an HTTP response."""
    return self.request(method='PUT', uri=uri, auth_token=auth_token,
                        http_request=http_request, data=data, **kwargs)

  Put = put

  def delete(self, uri=None, auth_token=None, http_request=None, **kwargs):
    """Performs a request using the DELETE method, returns an HTTP response."""
    return self.request(method='DELETE', uri=uri, auth_token=auth_token,
                        http_request=http_request, **kwargs)

  Delete = delete

  def modify_request(self, http_request):
    """Changes the HTTP request before sending it to the server.

    Sets the User-Agent HTTP header and fills in the HTTP host portion
    of the URL if one was not included in the request (for this it uses
    the self.host member if one is set). This method is called in
    self.request.

    Args:
      http_request: An atom.http_core.HttpRequest() (optional) If one is
                    not provided, a new HttpRequest is instantiated.

    Returns:
      An atom.http_core.HttpRequest() with the User-Agent header set and
      if this client has a value in its host member, the host in the request
      URL is set.
    """
    if http_request is None:
      http_request = atom.http_core.HttpRequest()

    if self.host is not None and http_request.uri.host is None:
      http_request.uri.host = self.host

    if self.xoauth_requestor_id is not None:
      http_request.uri.query['xoauth_requestor_id'] = self.xoauth_requestor_id

    # Set the user agent header for logging purposes.
    if self.source:
      http_request.headers['User-Agent'] = '%s gdata-py/2.0.14' % self.source
    else:
      http_request.headers['User-Agent'] = 'gdata-py/2.0.14'

    return http_request

  ModifyRequest = modify_request


class CustomHeaders(object):
  """Add custom headers to an http_request.

  Usage:
    >>> custom_headers = atom.client.CustomHeaders(header1='value1',
            header2='value2')
    >>> client.get(uri, custom_headers=custom_headers)
  """

  def __init__(self, **kwargs):
    """Creates a CustomHeaders instance.

    Initialize the headers dictionary with the arguments list.
    """
    self.headers = kwargs

  def modify_request(self, http_request):
    """Changes the HTTP request before sending it to the server.

    Adds the custom headers to the HTTP request.

    Args:
      http_request: An atom.http_core.HttpRequest().

    Returns:
      An atom.http_core.HttpRequest() with the added custom headers.
    """

    for name, value in self.headers.iteritems():
      if value is not None:
        http_request.headers[name] = value
    return http_request
