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


import urlparse
import urllib


DEFAULT_PROTOCOL = 'http'
DEFAULT_PORT = 80


def parse_url(url_string):
  """Creates a Url object which corresponds to the URL string.
  
  This method can accept partial URLs, but it will leave missing
  members of the Url unset.
  """
  parts = urlparse.urlparse(url_string)
  url = Url()
  if parts[0]:
    url.protocol = parts[0]
  if parts[1]:
    host_parts = parts[1].split(':')
    if host_parts[0]:
      url.host = host_parts[0]
    if len(host_parts) > 1:
      url.port = host_parts[1]
  if parts[2]:
    url.path = parts[2]
  if parts[4]:
    param_pairs = parts[4].split('&')
    for pair in param_pairs:
      pair_parts = pair.split('=')
      if len(pair_parts) > 1:
        url.params[urllib.unquote_plus(pair_parts[0])] = (
            urllib.unquote_plus(pair_parts[1]))
      elif len(pair_parts) == 1:
        url.params[urllib.unquote_plus(pair_parts[0])] = None
  return url
   
class Url(object):
  """Represents a URL and implements comparison logic.
  
  URL strings which are not identical can still be equivalent, so this object
  provides a better interface for comparing and manipulating URLs than 
  strings. URL parameters are represented as a dictionary of strings, and
  defaults are used for the protocol (http) and port (80) if not provided.
  """
  def __init__(self, protocol=None, host=None, port=None, path=None, 
               params=None):
    self.protocol = protocol
    self.host = host
    self.port = port
    self.path = path
    self.params = params or {}

  def to_string(self):
    url_parts = ['', '', '', '', '', '']
    if self.protocol:
      url_parts[0] = self.protocol
    if self.host:
      if self.port:
        url_parts[1] = ':'.join((self.host, str(self.port)))
      else:
        url_parts[1] = self.host
    if self.path:
      url_parts[2] = self.path
    if self.params:
      url_parts[4] = self.get_param_string()
    return urlparse.urlunparse(url_parts)

  def get_param_string(self):
    param_pairs = []
    for key, value in self.params.iteritems():
      param_pairs.append('='.join((urllib.quote_plus(key), 
          urllib.quote_plus(str(value)))))
    return '&'.join(param_pairs)

  def get_request_uri(self):
    """Returns the path with the parameters escaped and appended."""
    param_string = self.get_param_string()
    if param_string:
      return '?'.join([self.path, param_string])
    else:
      return self.path

  def __cmp__(self, other):
    if not isinstance(other, Url):
      return cmp(self.to_string(), str(other))
    difference = 0
    # Compare the protocol
    if self.protocol and other.protocol:
      difference = cmp(self.protocol, other.protocol)
    elif self.protocol and not other.protocol:
      difference = cmp(self.protocol, DEFAULT_PROTOCOL)
    elif not self.protocol and other.protocol:
      difference = cmp(DEFAULT_PROTOCOL, other.protocol)
    if difference != 0:
      return difference
    # Compare the host
    difference = cmp(self.host, other.host)
    if difference != 0:
      return difference
    # Compare the port
    if self.port and other.port:
      difference = cmp(self.port, other.port)
    elif self.port and not other.port:
      difference = cmp(self.port, DEFAULT_PORT)
    elif not self.port and other.port:
      difference = cmp(DEFAULT_PORT, other.port)
    if difference != 0:
      return difference
    # Compare the path
    difference = cmp(self.path, other.path)
    if difference != 0:
      return difference
    # Compare the parameters
    return cmp(self.params, other.params)

  def __str__(self):
    return self.to_string()
    
