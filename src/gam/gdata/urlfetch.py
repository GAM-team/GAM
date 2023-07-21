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


"""Provides HTTP functions for gdata.service to use on Google App Engine

AppEngineHttpClient: Provides an HTTP request method which uses App Engine's
   urlfetch API. Set the http_client member of a GDataService object to an
   instance of an AppEngineHttpClient to allow the gdata library to run on
   Google App Engine.

run_on_appengine: Function which will modify an existing GDataService object
   to allow it to run on App Engine. It works by creating a new instance of
   the AppEngineHttpClient and replacing the GDataService object's 
   http_client.

HttpRequest: Function that wraps google.appengine.api.urlfetch.Fetch in a 
    common interface which is used by gdata.service.GDataService. In other 
    words, this module can be used as the gdata service request handler so 
    that all HTTP requests will be performed by the hosting Google App Engine
    server. 
"""


__author__ = 'api.jscudder (Jeff Scudder)'


import io
import atom.service
import atom.http_interface
from google.appengine.api import urlfetch


def run_on_appengine(gdata_service):
  """Modifies a GDataService object to allow it to run on App Engine.

  Args:
    gdata_service: An instance of AtomService, GDataService, or any
        of their subclasses which has an http_client member.
  """
  gdata_service.http_client = AppEngineHttpClient()


class AppEngineHttpClient(atom.http_interface.GenericHttpClient):
  def __init__(self, headers=None):
    self.debug = False
    self.headers = headers or {}

  def request(self, operation, url, data=None, headers=None):
    """Performs an HTTP call to the server, supports GET, POST, PUT, and
    DELETE.

    Usage example, perform and HTTP GET on http://www.google.com/:
      import atom.http
      client = atom.http.HttpClient()
      http_response = client.request('GET', 'http://www.google.com/')

    Args:
      operation: str The HTTP operation to be performed. This is usually one
          of 'GET', 'POST', 'PUT', or 'DELETE'
      data: filestream, list of parts, or other object which can be converted
          to a string. Should be set to None when performing a GET or DELETE.
          If data is a file-like object which can be read, this method will
          read a chunk of 100K bytes at a time and send them.
          If the data is a list of parts to be sent, each part will be
          evaluated and sent.
      url: The full URL to which the request should be sent. Can be a string
          or atom.url.Url.
      headers: dict of strings. HTTP headers which should be sent
          in the request.
    """
    all_headers = self.headers.copy()
    if headers:
      all_headers.update(headers)

    # Construct the full payload.
    # Assume that data is None or a string.
    data_str = data
    if data:
      if isinstance(data, list):
        # If data is a list of different objects, convert them all to strings
        # and join them together.
        converted_parts = [__ConvertDataPart(x) for x in data]
        data_str = ''.join(converted_parts)
      else:
        data_str = __ConvertDataPart(data)

    # If the list of headers does not include a Content-Length, attempt to
    # calculate it based on the data object.
    if data and 'Content-Length' not in all_headers:
      all_headers['Content-Length'] = len(data_str)

    # Set the content type to the default value if none was set.
    if 'Content-Type' not in all_headers:
      all_headers['Content-Type'] = 'application/atom+xml'

    # Lookup the urlfetch operation which corresponds to the desired HTTP verb.
    if operation == 'GET':
      method = urlfetch.GET
    elif operation == 'POST':
      method = urlfetch.POST
    elif operation == 'PUT':
      method = urlfetch.PUT
    elif operation == 'DELETE':
      method = urlfetch.DELETE
    else:
      method = None
    return HttpResponse(urlfetch.Fetch(url=str(url), payload=data_str,
        method=method, headers=all_headers))
 

def HttpRequest(service, operation, data, uri, extra_headers=None,
    url_params=None, escape_params=True, content_type='application/atom+xml'):
  """Performs an HTTP call to the server, supports GET, POST, PUT, and DELETE.

  This function is deprecated, use AppEngineHttpClient.request instead.

  To use this module with gdata.service, you can set this module to be the
  http_request_handler so that HTTP requests use Google App Engine's urlfetch.
  import gdata.service
  import gdata.urlfetch
  gdata.service.http_request_handler = gdata.urlfetch

  Args:
    service: atom.AtomService object which contains some of the parameters
        needed to make the request. The following members are used to
        construct the HTTP call: server (str), additional_headers (dict),
        port (int), and ssl (bool).
    operation: str The HTTP operation to be performed. This is usually one of
        'GET', 'POST', 'PUT', or 'DELETE'
    data: filestream, list of parts, or other object which can be
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
  (server, port, ssl, partial_uri) = atom.service.ProcessUrl(service, full_uri)
  # Construct the full URL for the request.
  if ssl:
    full_url = 'https://%s%s' % (server, partial_uri)
  else:
    full_url = 'http://%s%s' % (server, partial_uri)

  # Construct the full payload. 
  # Assume that data is None or a string.
  data_str = data
  if data:
    if isinstance(data, list):
      # If data is a list of different objects, convert them all to strings
      # and join them together.
      converted_parts = [__ConvertDataPart(x) for x in data]
      data_str = ''.join(converted_parts)
    else:
      data_str = __ConvertDataPart(data)

  # Construct the dictionary of HTTP headers.
  headers = {}
  if isinstance(service.additional_headers, dict):
    headers = service.additional_headers.copy()
  if isinstance(extra_headers, dict):
    for header, value in extra_headers.items():
      headers[header] = value
  # Add the content type header (we don't need to calculate content length,
  # since urlfetch.Fetch will calculate for us).
  if content_type:
    headers['Content-Type'] = content_type

  # Lookup the urlfetch operation which corresponds to the desired HTTP verb.
  if operation == 'GET':
    method = urlfetch.GET
  elif operation == 'POST':
    method = urlfetch.POST
  elif operation == 'PUT':
    method = urlfetch.PUT
  elif operation == 'DELETE':
    method = urlfetch.DELETE
  else:
    method = None
  return HttpResponse(urlfetch.Fetch(url=full_url, payload=data_str, 
      method=method, headers=headers))


def __ConvertDataPart(data):
  if not data or isinstance(data, str):
    return data
  elif hasattr(data, 'read'):
    # data is a file like object, so read it completely.
    return data.read()
  # The data object was not a file.
  # Try to convert to a string and send the data.
  return str(data)


class HttpResponse(object):
  """Translates a urlfetch resoinse to look like an hhtplib resoinse.
  
  Used to allow the resoinse from HttpRequest to be usable by gdata.service
  methods.
  """

  def __init__(self, urlfetch_response):
    self.body = io.StringIO(urlfetch_response.content)
    self.headers = urlfetch_response.headers
    self.status = urlfetch_response.status_code
    self.reason = ''

  def read(self, length=None):
    if not length:
      return self.body.read()
    else:
      return self.body.read(length)

  def getheader(self, name):
    if name not in self.headers:
      return self.headers[name.lower()]
    return self.headers[name]
    
