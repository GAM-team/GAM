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


__author__ = 'api.jscudder (Jeff Scudder)'


import atom.http_interface
import atom.url


class Error(Exception):
  pass


class NoRecordingFound(Error):
  pass


class MockRequest(object):
  """Holds parameters of an HTTP request for matching against future requests.
  """
  def __init__(self, operation, url, data=None, headers=None):
    self.operation = operation
    if isinstance(url, (str, unicode)):
      url = atom.url.parse_url(url)
    self.url = url
    self.data = data
    self.headers = headers


class MockResponse(atom.http_interface.HttpResponse):
  """Simulates an httplib.HTTPResponse object."""
  def __init__(self, body=None, status=None, reason=None, headers=None):
    if body and hasattr(body, 'read'):
      self.body = body.read()
    else:
      self.body = body
    if status is not None:
      self.status = int(status)
    else:
      self.status = None
    self.reason = reason
    self._headers = headers or {}

  def read(self):
    return self.body


class MockHttpClient(atom.http_interface.GenericHttpClient):
  def __init__(self, headers=None, recordings=None, real_client=None):
    """An HttpClient which responds to request with stored data.

    The request-response pairs are stored as tuples in a member list named
    recordings.

    The MockHttpClient can be switched from replay mode to record mode by
    setting the real_client member to an instance of an HttpClient which will
    make real HTTP requests and store the server's response in list of 
    recordings.
    
    Args:
      headers: dict containing HTTP headers which should be included in all
          HTTP requests.
      recordings: The initial recordings to be used for responses. This list
          contains tuples in the form: (MockRequest, MockResponse)
      real_client: An HttpClient which will make a real HTTP request. The 
          response will be converted into a MockResponse and stored in 
          recordings.
    """
    self.recordings = recordings or []
    self.real_client = real_client
    self.headers = headers or {}

  def add_response(self, response, operation, url, data=None, headers=None):
    """Adds a request-response pair to the recordings list.
    
    After the recording is added, future matching requests will receive the
    response.
    
    Args:
      response: MockResponse
      operation: str
      url: str
      data: str, Currently the data is ignored when looking for matching
          requests.
      headers: dict of strings: Currently the headers are ignored when
          looking for matching requests.
    """
    request = MockRequest(operation, url, data=data, headers=headers)
    self.recordings.append((request, response))

  def request(self, operation, url, data=None, headers=None):
    """Returns a matching MockResponse from the recordings.
    
    If the real_client is set, the request will be passed along and the 
    server's response will be added to the recordings and also returned. 

    If there is no match, a NoRecordingFound error will be raised.
    """
    if self.real_client is None:
      if isinstance(url, (str, unicode)):
        url = atom.url.parse_url(url)
      for recording in self.recordings:
        if recording[0].operation == operation and recording[0].url == url:
          return recording[1]
      raise NoRecordingFound('No recodings found for %s %s' % (
          operation, url))
    else:
      # There is a real HTTP client, so make the request, and record the 
      # response.
      response = self.real_client.request(operation, url, data=data, 
          headers=headers)
      # TODO: copy the headers
      stored_response = MockResponse(body=response, status=response.status,
          reason=response.reason)
      self.add_response(stored_response, operation, url, data=data, 
          headers=headers)
      return stored_response
