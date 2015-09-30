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


# This module is used for version 2 of the Google Data APIs.


__author__ = 'j.s@google.com (Jeff Scudder)'


import StringIO
import pickle
import os.path
import tempfile
import atom.http_core


class Error(Exception):
  pass


class NoRecordingFound(Error):
  pass


class MockHttpClient(object):
  debug = None
  real_client = None
  last_request_was_live = False

  # The following members are used to construct the session cache temp file
  # name.
  # These are combined to form the file name
  # /tmp/cache_prefix.cache_case_name.cache_test_name
  cache_name_prefix = 'gdata_live_test'
  cache_case_name = ''
  cache_test_name = ''

  def __init__(self, recordings=None, real_client=None):
    self._recordings = recordings or []
    if real_client is not None:
      self.real_client = real_client

  def add_response(self, http_request, status, reason, headers=None,
      body=None):
    response = MockHttpResponse(status, reason, headers, body)
    # TODO Scrub the request and the response.
    self._recordings.append((http_request._copy(), response))

  AddResponse = add_response

  def request(self, http_request):
    """Provide a recorded response, or record a response for replay.

    If the real_client is set, the request will be made using the
    real_client, and the response from the server will be recorded.
    If the real_client is None (the default), this method will examine
    the recordings and find the first which matches.
    """
    request = http_request._copy()
    _scrub_request(request)
    if self.real_client is None:
      self.last_request_was_live = False
      for recording in self._recordings:
        if _match_request(recording[0], request):
          return recording[1]
    else:
      # Pass along the debug settings to the real client.
      self.real_client.debug = self.debug
      # Make an actual request since we can use the real HTTP client.
      self.last_request_was_live = True
      response = self.real_client.request(http_request)
      scrubbed_response = _scrub_response(response)
      self.add_response(request, scrubbed_response.status,
                        scrubbed_response.reason,
                        dict(atom.http_core.get_headers(scrubbed_response)),
                        scrubbed_response.read())
      # Return the recording which we just added.
      return self._recordings[-1][1]
    raise NoRecordingFound('No recoding was found for request: %s %s' % (
        request.method, str(request.uri)))

  Request = request

  def _save_recordings(self, filename):
    recording_file = open(os.path.join(tempfile.gettempdir(), filename),
                          'wb')
    pickle.dump(self._recordings, recording_file)
    recording_file.close()

  def _load_recordings(self, filename):
    recording_file = open(os.path.join(tempfile.gettempdir(), filename),
                          'rb')
    self._recordings = pickle.load(recording_file)
    recording_file.close()

  def _delete_recordings(self, filename):
    full_path = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(full_path):
      os.remove(full_path)

  def _load_or_use_client(self, filename, http_client):
    if os.path.exists(os.path.join(tempfile.gettempdir(), filename)):
      self._load_recordings(filename)
    else:
      self.real_client = http_client

  def use_cached_session(self, name=None, real_http_client=None):
    """Attempts to load recordings from a previous live request.

    If a temp file with the recordings exists, then it is used to fulfill
    requests. If the file does not exist, then a real client is used to
    actually make the desired HTTP requests. Requests and responses are
    recorded and will be written to the desired temprary cache file when
    close_session is called.

    Args:
      name: str (optional) The file name of session file to be used. The file
            is loaded from the temporary directory of this machine. If no name
            is passed in, a default name will be constructed using the
            cache_name_prefix, cache_case_name, and cache_test_name of this
            object.
      real_http_client: atom.http_core.HttpClient the real client to be used
                        if the cached recordings are not found. If the default
                        value is used, this will be an
                        atom.http_core.HttpClient.
    """
    if real_http_client is None:
      real_http_client = atom.http_core.HttpClient()
    if name is None:
      self._recordings_cache_name = self.get_cache_file_name()
    else:
      self._recordings_cache_name = name
    self._load_or_use_client(self._recordings_cache_name, real_http_client)

  def close_session(self):
    """Saves recordings in the temporary file named in use_cached_session."""
    if self.real_client is not None:
      self._save_recordings(self._recordings_cache_name)

  def delete_session(self, name=None):
    """Removes recordings from a previous live request."""
    if name is None:
      self._delete_recordings(self._recordings_cache_name)
    else:
      self._delete_recordings(name)

  def get_cache_file_name(self):
    return '%s.%s.%s' % (self.cache_name_prefix, self.cache_case_name,
                         self.cache_test_name)

  def _dump(self):
    """Provides debug information in a string."""
    output = 'MockHttpClient\n  real_client: %s\n  cache file name: %s\n' % (
        self.real_client, self.get_cache_file_name())
    output += '  recordings:\n'
    i = 0
    for recording in self._recordings:
      output += '    recording %i is for: %s %s\n' % (
          i, recording[0].method, str(recording[0].uri))
      i += 1
    return output


def _match_request(http_request, stored_request):
  """Determines whether a request is similar enough to a stored request
     to cause the stored response to be returned."""
  # Check to see if the host names match.
  if (http_request.uri.host is not None
      and http_request.uri.host != stored_request.uri.host):
    return False
  # Check the request path in the URL (/feeds/private/full/x)
  elif http_request.uri.path != stored_request.uri.path:
    return False
  # Check the method used in the request (GET, POST, etc.)
  elif http_request.method != stored_request.method:
    return False
  # If there is a gsession ID in either request, make sure that it is matched
  # exactly.
  elif ('gsessionid' in http_request.uri.query
        or 'gsessionid' in stored_request.uri.query):
    if 'gsessionid' not in stored_request.uri.query:
      return False
    elif 'gsessionid' not in http_request.uri.query:
      return False
    elif (http_request.uri.query['gsessionid']
          != stored_request.uri.query['gsessionid']):
      return False
  # Ignores differences in the query params (?start-index=5&max-results=20),
  # the body of the request, the port number, HTTP headers, just to name a
  # few.
  return True


def _scrub_request(http_request):
  """ Removes email address and password from a client login request.

  Since the mock server saves the request and response in plantext, sensitive
  information like the password should be removed before saving the
  recordings. At the moment only requests sent to a ClientLogin url are
  scrubbed.
  """
  if (http_request and http_request.uri and http_request.uri.path and
      http_request.uri.path.endswith('ClientLogin')):
    # Remove the email and password from a ClientLogin request.
    http_request._body_parts = []
    http_request.add_form_inputs(
        {'form_data': 'client login request has been scrubbed'})
  else:
    # We can remove the body of the post from the recorded request, since
    # the request body is not used when finding a matching recording.
    http_request._body_parts = []
  return http_request


def _scrub_response(http_response):
  return http_response


class EchoHttpClient(object):
  """Sends the request data back in the response.

  Used to check the formatting of the request as it was sent. Always responds
  with a 200 OK, and some information from the HTTP request is returned in
  special Echo-X headers in the response. The following headers are added
  in the response:
  'Echo-Host': The host name and port number to which the HTTP connection is
               made. If no port was passed in, the header will contain
               host:None.
  'Echo-Uri': The path portion of the URL being requested. /example?x=1&y=2
  'Echo-Scheme': The beginning of the URL, usually 'http' or 'https'
  'Echo-Method': The HTTP method being used, 'GET', 'POST', 'PUT', etc.
  """

  def request(self, http_request):
    return self._http_request(http_request.uri, http_request.method,
                              http_request.headers, http_request._body_parts)

  def _http_request(self, uri, method, headers=None, body_parts=None):
    body = StringIO.StringIO()
    response = atom.http_core.HttpResponse(status=200, reason='OK', body=body)
    if headers is None:
      response._headers = {}
    else:
      # Copy headers from the request to the response but convert values to
      # strings. Server response headers always come in as strings, so an int
      # should be converted to a corresponding string when echoing.
      for header, value in headers.iteritems():
        response._headers[header] = str(value)
    response._headers['Echo-Host'] = '%s:%s' % (uri.host, str(uri.port))
    response._headers['Echo-Uri'] = uri._get_relative_path()
    response._headers['Echo-Scheme'] = uri.scheme
    response._headers['Echo-Method'] = method
    for part in body_parts:
      if isinstance(part, str):
        body.write(part)
      elif hasattr(part, 'read'):
        body.write(part.read())
    body.seek(0)
    return response


class SettableHttpClient(object):
  """An HTTP Client which responds with the data given in set_response."""

  def __init__(self, status, reason, body, headers):
    """Configures the response for the server.

    See set_response for details on the arguments to the constructor.
    """
    self.set_response(status, reason, body, headers)
    self.last_request = None

  def set_response(self, status, reason, body, headers):
    """Determines the response which will be sent for each request.

    Args:
      status: An int for the HTTP status code, example: 200, 404, etc.
      reason: String for the HTTP reason, example: OK, NOT FOUND, etc.
      body: The body of the HTTP response as a string or a file-like
            object (something with a read method).
      headers: dict of strings containing the HTTP headers in the response.
    """
    self.response = atom.http_core.HttpResponse(status=status, reason=reason,
        body=body)
    self.response._headers = headers.copy()

  def request(self, http_request):
    self.last_request = http_request
    return self.response


class MockHttpResponse(atom.http_core.HttpResponse):

  def __init__(self, status=None, reason=None, headers=None, body=None):
    self._headers = headers or {}
    if status is not None:
      self.status = status
    if reason is not None:
      self.reason = reason
    if body is not None:
      # Instead of using a file-like object for the body, store as a string
      # so that reads can be repeated.
      if hasattr(body, 'read'):
        self._body = body.read()
      else:
        self._body = body

  def read(self):
    return self._body
