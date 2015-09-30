# Copyright (C) 2008 Google, Inc.
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

"""Allow Google Apps domain administrators to create/modify/delete resource calendars.

  ResCalService: Interact with Resource Calendars."""

__author__ = 'jlee@pbu.edu'

import gdata.apps
import gdata.apps.service
import gdata.service

class ResCalService(gdata.apps.service.PropertyService):
  """Client for the Google Apps Resource Calendar service."""

  def _serviceUrl(self, domain=None):
    if domain is None:
      domain = self.domain
    return '/a/feeds/calendar/resource/2.0/%s' % domain

  def CreateResourceCalendar(self, id, common_name, description=None, type=None):
  
    uri = self._serviceUrl()
    properties = {}
    properties['resourceId'] = id
    properties['resourceCommonName'] = common_name
    if description != None:
      properties['resourceDescription'] = description
    if type != None:
      properties['resourceType'] = type
    return self._PostProperties(uri, properties)

  def RetrieveResourceCalendar(self, id):
  
    uri = self._serviceUrl()+'/'+id
    return self._GetProperties(uri)

  def RetrieveAllResourceCalendars(self):
  
    uri = self._serviceUrl()+'/'
    return self._GetPropertiesList(uri)

  def UpdateResourceCalendar(self, id, common_name=None, description=None, type=None):
  
    uri = self._serviceUrl()+'/'+id
    properties = {}
    properties['resourceId'] = id
    if common_name != None:
      properties['resourceCommonName'] = common_name
    if description != None:
      properties['resourceDescription'] = description
    if type != None:
      properties['resourceType'] = type
    return self._PutProperties(uri, properties)

  def DeleteResourceCalendar(self, id):
  
    uri = self._serviceUrl()+'/'+id
    return self._DeleteProperties(uri)