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

__author__ = 'jay@ditoweb.com'


import gdata.apps
import gdata.apps.service
import gdata.service

import urllib

API_VER='2.0'

class MultiDomainService(gdata.apps.service.PropertyService):
  """Extended functions for Google Apps Multi-Domain Support."""

  def _serviceUrl(self, setting_id, email=None, params=None):
    uri = '/a/feeds/%s/%s/%s' % (setting_id, API_VER, self.domain)
    if email:
      uri += '/' + email
    if params:
      uri += '?' + urllib.urlencode(params)
    return uri


  def CreateUser(self, user_email, password, first_name, last_name, is_admin=None, hash_function=None, change_password=None, agreed_to_terms=None,
                 suspended=None, ip_whitelisted=None, quota_in_gb=None):
    if user_email.find('@') == -1:
      user_email = '%s@%s' % (user_email, self.domain)
    uri = self._serviceUrl(setting_id='user')
    properties = {}
    properties['userEmail'] = user_email
    properties['password'] = password
    properties['firstName'] = first_name
    properties['lastName'] = last_name
    if is_admin != None:
      properties['isAdmin'] = gdata.apps.service._bool2str(is_admin)
    if hash_function != None:
      properties['hashFunction'] = hash_function
    if change_password != None:
      properties['isChangePasswordAtNextLogin'] = gdata.apps.service._bool2str(change_password)
    if agreed_to_terms != None:
      properties['agreedToTerms'] = gdata.apps.service._bool2str(agreed_to_terms)
    if suspended != None:
      properties['isSuspended'] = gdata.apps.service._bool2str(suspended)
    if ip_whitelisted != None:
      properties['ipWhitelisted'] = gdata.apps.service._bool2str(ip_whitelisted)
    if quota_in_gb != None:
      properties['quotaInGb'] = quota_in_gb
    return self._PostProperties(uri, properties)

  def UpdateUser(self, user_email, password=None, first_name=None, last_name=None, is_admin=None, hash_function=None, change_password=None, agreed_to_terms=None,
                 suspended=None, ip_whitelisted=None, quota_in_gb=None):
    if user_email.find('@') == -1:
      user_email = '%s@%s' % (user_email, self.domain)
    uri = self._serviceUrl(setting_id='user', email=user_email)
    properties = {}
    if password != None:
      properties['password'] = password
    if first_name != None:
      properties['firstName'] = first_name
    if last_name != None:
      properties['lastName'] = last_name
    if is_admin != None:
      properties['isAdmin'] =  gdata.apps.service._bool2str(is_admin)
    if hash_function != None:
      properties['hashFunction'] = hash_function
    if change_password != None:
      properties['isChangePasswordAtNextLogin'] = gdata.apps.service._bool2str(change_password)
    if agreed_to_terms != None:
      properties['agreedToTerms'] = gdata.apps.service._bool2str(agreed_to_terms)
    if suspended != None:
      properties['isSuspended'] = gdata.apps.service._bool2str(suspended)
    if ip_whitelisted != None:
      properties['ipWhitelisted'] = gdata.apps.service._bool2str(ip_whitelisted)
    if quota_in_gb != None:
      properties['quotaInGb'] = str(quota_in_gb)
    return self._PutProperties(uri, properties)

  def RetrieveUser(self, user_email):
    if user_email.find('@') == -1:
      user_email = '%s@%s' % (user_email, self.domain)
    uri = self._serviceUrl(setting_id='user', email=user_email)
    return self._GetProperties(uri)

  def RetrieveAllUsers(self):
    uri = self._serviceUrl(setting_id='user')
    return self._GetPropertiesList(uri)

  def DeleteUser(self, user_email):
    if user_email.find('@') == -1:
      user_email = '%s@%s' % (user_email, self.domain)
    uri = self._serviceUrl(setting_id='user', email=user_email)
    return self._DeleteProperties(uri)

  def RenameUser(self, old_email, new_email):
    if old_email.find('@') == -1:
      old_email = '%s@%s' % (old_email, self.domain)
    if new_email.find('@') == -1:
      new_email = '%s@%s' % (new_email, self.domain)
    uri = self._serviceUrl(setting_id='user/userEmail', email=old_email)
    properties = {}
    properties['newEmail'] = new_email
    return self._PutProperties(uri, properties)

  def CreateAlias(self, user_email, alias_email):
    if alias_email.find('@') == -1:
      alias_email = '%s@%s' % (alias_email, self.domain)
    if user_email.find('@') == -1:
      user_email = '%s@%s' % (user_email, self.domain)
    uri = self._serviceUrl(setting_id='alias')
    properties = {}
    properties['userEmail'] = user_email
    properties['aliasEmail'] = alias_email
    return self._PostProperties(uri, properties)

  def RetrieveAlias(self, alias_email):
    if alias_email.find('@') == -1:
      alias_email = '%s@%s' % (alias_email, self.domain)
    uri = self._serviceUrl(setting_id='alias', email=alias_email)
    return self._GetProperties(uri)

  def RetrieveAllAliases(self):
    uri = self._serviceUrl(setting_id='alias')
    return self._GetPropertiesList(uri)

  def DeleteAlias(self, alias_email):
    if alias_email.find('@') == -1:
      alias_email = '%s@%s' % (alias_email, self.domain)
    uri = self._serviceUrl(setting_id='alias', email=alias_email)
    return self._DeleteProperties(uri)
    
  def GetUserAliases(self, user_email):
    if user_email.find('@') == -1:
      user_email = '%s@%s' % (user_email, self.domain)
    uri = self._serviceUrl(setting_id='alias', params={'userEmail' : user_email})
    return self._GetPropertiesList(uri)
