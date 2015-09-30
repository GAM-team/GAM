#!/usr/bin/env python
#
#    Copyright (C) 2009 Google Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# This module is used for version 2 of the Google Data APIs.


__author__ = 'j.s@google.com (Jeff Scudder)'


import base64


class BasicAuth(object):
  """Sets the Authorization header as defined in RFC1945"""

  def __init__(self, user_id, password):
    self.basic_cookie = base64.encodestring(
        '%s:%s' % (user_id, password)).strip()

  def modify_request(self, http_request):
    http_request.headers['Authorization'] = 'Basic %s' % self.basic_cookie

  ModifyRequest = modify_request


class NoAuth(object):

  def modify_request(self, http_request):
    pass
