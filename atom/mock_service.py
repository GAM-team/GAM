#!/usr/bin/python
#
# Copyright (C) 2008 Google Inc.
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


"""MockService provides CRUD ops. for mocking calls to AtomPub services.

  MockService: Exposes the publicly used methods of AtomService to provide
      a mock interface which can be used in unit tests.
"""

import atom.service
import pickle


__author__ = 'api.jscudder (Jeffrey Scudder)'


# Recordings contains pairings of HTTP MockRequest objects with MockHttpResponse objects.
recordings = []
# If set, the mock service HttpRequest are actually made through this object.
real_request_handler = None

def ConcealValueWithSha(source):
  import sha
  return sha.new(source[:-5]).hexdigest()

def DumpRecordings(conceal_func=ConcealValueWithSha):
  if conceal_func:
    for recording_pair in recordings:
      recording_pair[0].ConcealSecrets(conceal_func)
  return pickle.dumps(recordings)

def LoadRecordings(recordings_file_or_string):
  if isinstance(recordings_file_or_string, str):
    atom.mock_service.recordings =  pickle.loads(recordings_file_or_string)
  elif hasattr(recordings_file_or_string, 'read'):
    atom.mock_service.recordings = pickle.loads(
      recordings_file_or_string.read())

def HttpRequest(service, operation, data, uri, extra_headers=None,
    url_params=None, escape_params=True, content_type='application/atom+xml'):
  """Simulates an HTTP call to the server, makes an actual HTTP request if 
  real_request_handler is set.

  This function operates in two different modes depending on if 
  real_request_handler is set or not. If real_request_handler is not set,
  HttpRequest will look in this module's recordings list to find a response
  which matches the parameters in the function call. If real_request_handler
  is set, this function will call real_request_handler.HttpRequest, add the
  response to the recordings list, and respond with the actual response.

  Args:
    service: atom.AtomService object which contains some of the parameters
        needed to make the request. The following members are used to
        construct the HTTP call: server (str), additional_headers (dict),
        port (int), and ssl (bool).
    operation: str The HTTP operation to be performed. This is usually one of
        'GET', 'POST', 'PUT', or 'DELETE'
    data: ElementTree, filestream, list of parts, or other object which can be
        converted to a string.
        Should be set to None when performing a GET or PUT.
        If data is a file-like object which can be read, this method will read
        a chunk of 100K bytes at a time and send them.
        If the data is a list of parts to be sent, each part will be evaluated
        and sent.
    uri: The beginning of the URL to which the request should be sent.
        Examples: '/', '/base/feeds/snippets',
        '/m8/feeds/contacts/default/base'
    extra_headers: dict of strings. HTTP headers which should be sent
        in the request. These headers are in addition to those stored in
        service.additional_headers.
    url_params: dict of strings. Key value pairs to be added to the URL as
        URL parameters. For example {'foo':'bar', 'test':'param'} will
        become ?foo=bar&test=param.
    escape_params: bool default True. If true, the keys and values in
        url_params will be URL escaped when the form is constructed
        (Special characters converted to %XX form.)
    content_type: str The MIME type for the data being sent. Defaults to
        'application/atom+xml', this is only used if data is set.
  """
  full_uri = atom.service.BuildUri(uri, url_params, escape_params)
  (server, port, ssl, uri) = atom.service.ProcessUrl(service, uri)
  current_request = MockRequest(operation, full_uri, host=server, ssl=ssl, 
      data=data, extra_headers=extra_headers, url_params=url_params, 
      escape_params=escape_params, content_type=content_type)
  # If the request handler is set, we should actually make the request using 
  # the request handler and record the response to replay later.
  if real_request_handler:
    response = real_request_handler.HttpRequest(service, operation, data, uri,
        extra_headers=extra_headers, url_params=url_params, 
        escape_params=escape_params, content_type=content_type)
    # TODO: need to copy the HTTP headers from the real response into the
    # recorded_response.
    recorded_response = MockHttpResponse(body=response.read(), 
        status=response.status, reason=response.reason)
    # Insert a tuple which maps the request to the response object returned
    # when making an HTTP call using the real_request_handler.
    recordings.append((current_request, recorded_response))
    return recorded_response
  else:
    # Look through available recordings to see if one matches the current 
    # request.
    for request_response_pair in recordings:
      if request_response_pair[0].IsMatch(current_request):
        return request_response_pair[1]
  return None


class MockRequest(object):
  """Represents a request made to an AtomPub server.
  
  These objects are used to determine if a client request matches a recorded
  HTTP request to determine what the mock server's response will be. 
  """

  def __init__(self, operation, uri, host=None, ssl=False, port=None, 
      data=None, extra_headers=None, url_params=None, escape_params=True,
      content_type='application/atom+xml'):
    """Constructor for a MockRequest
    
    Args:
      operation: str One of 'GET', 'POST', 'PUT', or 'DELETE' this is the
          HTTP operation requested on the resource.
      uri: str The URL describing the resource to be modified or feed to be
          retrieved. This should include the protocol (http/https) and the host
          (aka domain). For example, these are some valud full_uris:
          'http://example.com', 'https://www.google.com/accounts/ClientLogin'
      host: str (optional) The server name which will be placed at the 
          beginning of the URL if the uri parameter does not begin with 'http'.
          Examples include 'example.com', 'www.google.com', 'www.blogger.com'.
      ssl: boolean (optional) If true, the request URL will begin with https 
          instead of http.
      data: ElementTree, filestream, list of parts, or other object which can be
          converted to a string. (optional)
          Should be set to None when performing a GET or PUT.
          If data is a file-like object which can be read, the constructor 
          will read the entire file into memory. If the data is a list of 
          parts to be sent, each part will be evaluated and stored.
      extra_headers: dict (optional) HTTP headers included in the request.
      url_params: dict (optional) Key value pairs which should be added to 
          the URL as URL parameters in the request. For example uri='/', 
          url_parameters={'foo':'1','bar':'2'} could become '/?foo=1&bar=2'.
      escape_params: boolean (optional) Perform URL escaping on the keys and 
          values specified in url_params. Defaults to True.
      content_type: str (optional) Provides the MIME type of the data being 
          sent.
    """
    self.operation = operation
    self.uri = _ConstructFullUrlBase(uri, host=host, ssl=ssl)
    self.data = data
    self.extra_headers = extra_headers
    self.url_params = url_params or {}
    self.escape_params = escape_params
    self.content_type = content_type

  def ConcealSecrets(self, conceal_func):
    """Conceal secret data in this request."""
    if self.extra_headers.has_key('Authorization'):
      self.extra_headers['Authorization'] = conceal_func(
        self.extra_headers['Authorization'])

  def IsMatch(self, other_request):
    """Check to see if the other_request is equivalent to this request.
    
    Used to determine if a recording matches an incoming request so that a
    recorded response should be sent to the client.

    The matching is not exact, only the operation and URL are examined 
    currently.

    Args:
      other_request: MockRequest The request which we want to check this
          (self) MockRequest against to see if they are equivalent.
    """
    # More accurate matching logic will likely be required.
    return (self.operation == other_request.operation and self.uri == 
        other_request.uri)


def _ConstructFullUrlBase(uri, host=None, ssl=False):
  """Puts URL components into the form http(s)://full.host.strinf/uri/path
  
  Used to construct a roughly canonical URL so that URLs which begin with 
  'http://example.com/' can be compared to a uri of '/' when the host is 
  set to 'example.com'

  If the uri contains 'http://host' already, the host and ssl parameters
  are ignored.

  Args:
    uri: str The path component of the URL, examples include '/'
    host: str (optional) The host name which should prepend the URL. Example:
        'example.com'
    ssl: boolean (optional) If true, the returned URL will begin with https
        instead of http.

  Returns:
    String which has the form http(s)://example.com/uri/string/contents
  """
  if uri.startswith('http'):
    return uri
  if ssl:
    return 'https://%s%s' % (host, uri)
  else:
    return 'http://%s%s' % (host, uri)


class MockHttpResponse(object):
  """Returned from MockService crud methods as the server's response."""

  def __init__(self, body=None, status=None, reason=None, headers=None):
    """Construct a mock HTTPResponse and set members.

    Args:
      body: str (optional) The HTTP body of the server's response. 
      status: int (optional) 
      reason: str (optional)
      headers: dict (optional)
    """
    self.body = body
    self.status = status
    self.reason = reason
    self.headers = headers or {}

  def read(self):
    return self.body

  def getheader(self, header_name):
    return self.headers[header_name]

