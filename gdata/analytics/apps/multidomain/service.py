#!/usr/bin/python
#
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

"""Extended Multi Domain Support.

  MultiDomainService: Multi Domain Support."""

__author__ = 'jlee@pbu.edu'


import gdata.apps
import gdata.apps.service
import gdata.service


API_VER='2.0'

class MultiDomainService(gdata.apps.service.PropertyService):
  """Extended functions for Google Apps Multi-Domain Support."""

  def _serviceUrl(self, setting_id, domain=None):
    if domain is None:
      domain = self.domain
    return '/a/feeds/%s/%s/%s' % (setting_id, API_VER, domain)

  def CreateUser(self, user_email, password, first_name, last_name, user_domain=None, is_admin=False):

    uri = self._serviceUrl('user', user_domain)
    properties = {}
    properties['userEmail'] = user_email
    properties['password'] = password
    properties['firstName'] = first_name
    properties['lastName'] = last_name
    properties['isAdmin'] = is_admin
    return self._PostProperties(uri, properties)

  def UpdateUser(self, user_email, user_domain=None, password=None, first_name=None, last_name=None, is_admin=None):

    uri = self._serviceUrl('user', user_domain)
    properties = RetrieveUser(user_domain, user_email)
    if password != None:
      properties['password'] = password
    if first_name != None:
      properties['firstName'] = first_name
    if last_name != None:
      properties['lastName'] = last_name
    if is_admin != None:
      properties['isAdmin'] =  gdata.apps.service._bool2str(is_admin)
    return self._PutProperties(uri, properties)

  def RenameUser(self, old_email, new_email):

    old_domain = old_email[old_email.find('@')+1:]
    uri = self._serviceUrl('user/userEmail', old_domain+'/'+old_email)
    properties = {}
    properties['newEmail'] = new_email
    return self._PutProperties(uri, properties)

  def CreateAlias(self, user_email, alias_email):

    if alias_email.find('@') > 0:
      domain = alias_email[alias_email.find('@')+1:]
    else:
      domain = self.domain
    uri = self._serviceUrl('alias', domain)
    properties = {}
    properties['userEmail'] = user_email
    properties['aliasEmail'] = alias_email
    return self._PostProperties(uri, properties)

  def RetrieveAlias(self, alias_email):
  
    alias_domain = alias_email[alias_email.find('@')+1:]
    uri = self._serviceUrl('alias', alias_domain+'/'+alias_email)
    return self._GetProperties(uri)

  def RetrieveAllAliases(self):

    uri = self._serviceUrl('alias', self.domain)
    return self._GetPropertiesList(uri)

  def DeleteAlias(self, alias_email):
  
    alias_domain = alias_email[alias_email.find('@')+1:]
    uri = self._serviceUrl('alias', alias_domain+'/'+alias_email)
    return self._DeleteProperties(uri)
    
  def GetUserAliases(self, user_email):
  
    user_domain = user_email[user_email.find('@')+1:]
    uri = self._serviceUrl('alias', user_domain+'?userEmail='+user_email)
    return self._GetPropertiesList(uri)