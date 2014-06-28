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

"""Organization Support.

  OrganizationService: Organization Support."""

__author__ = 'jlee@pbu.edu'


import urllib
import gdata.apps
import gdata.apps.service
import gdata.service


API_VER='2.0'

class OrganizationService(gdata.apps.service.PropertyService):
  """Extended functions for Google Apps Organization Support."""

  def _serviceUrl(self, setting_id, domain=None):
    if domain is None:
      domain = self.domain
    return '/a/feeds/%s/%s/%s' % (setting_id, API_VER, domain)

  def RetrieveCustomerId(self):
  
    uri = '/a/feeds/customer/2.0/customerId'
    return self._GetProperties(uri)

  def CreateOrganizationUnit(self, name, description, parent_org_unit_path='/', block_inheritance=False):
  
    customer_id = self.RetrieveCustomerId()['customerId']
    uri = '/a/feeds/orgunit/2.0/%s' % customer_id
    properties = {}
    properties['name'] = name
    properties['description'] = description
    properties['parentOrgUnitPath'] = urllib.quote_plus(parent_org_unit_path, safe='/')
    properties['blockInheritance'] = gdata.apps.service._bool2str(block_inheritance)
    return self._PostProperties(uri, properties)
    
  def UpdateOrganizationUnit(self, old_name, new_name=None, description=None, parent_org_unit_path=None, block_inheritance=None, users_to_move=None):
  
    customer_id = self.RetrieveCustomerId()['customerId']
    old_name = urllib.quote_plus(old_name, safe='/')
    uri = '/a/feeds/orgunit/2.0/%s/%s' % (customer_id, old_name)
    properties = {}
    if new_name != None:
      properties['name'] = new_name
    if description != None:
      properties['description'] = description
    if parent_org_unit_path != None:
      properties['parentOrgUnitPath'] = urllib.quote_plus(parent_org_unit_path, safe='/')
    if block_inheritance != None:
      properties['blockInheritance'] = gdata.apps.service._bool2str(block_inheritance)
    if users_to_move != None:
      properties['usersToMove'] = ''
      for user in users_to_move:
        if user.find('@') < 0:
          user = user+'@'+self.domain
        properties['usersToMove'] += user+', '
    return self._PutProperties(uri, properties)

  def RetrieveOrganizationUnit(self, name):

    customer_id = self.RetrieveCustomerId()['customerId']
    name = urllib.quote_plus(name, safe='/')
    uri = '/a/feeds/orgunit/2.0/%s/%s' % (customer_id, name)
    org = self._GetProperties(uri)
    try:
      org['orgUnitPath'] = urllib.unquote_plus(org['orgUnitPath'])
      org['parentOrgUnitPath'] = urllib.unquote_plus(org['parentOrgUnitPath'])
    except AttributeError:
      pass
    return org

  def RetrieveAllOrganizationUnits(self):
  
    customer_id = self.RetrieveCustomerId()['customerId']
    uri = '/a/feeds/orgunit/2.0/%s?get=all' % customer_id
    all_orgs = self._GetPropertiesList(uri)
    for org in all_orgs:
      try:
        org['orgUnitPath'] = urllib.unquote_plus(org['orgUnitPath'])
        org['parentOrgUnitPath'] = urllib.unquote_plus(org['parentOrgUnitPath'])
      except AttributeError:
        pass
    return all_orgs

  def RetrieveSubOrganizationUnits(self, name):

    customer_id = self.RetrieveCustomerId()['customerId']
    uri = '/a/feeds/orgunit/2.0/%s?get=children&orgUnitPath=%s' % (customer_id, urllib.quote_plus(name, safe='/'))
    sub_orgs = self._GetPropertiesList(uri)
    for org in sub_orgs:
      try:
        org['orgUnitPath'] = urllib.unquote_plus(org['orgUnitPath'])
        org['parentOrgUnitPath'] = urllib.unquote_plus(org['parentOrgUnitPath'])
      except AttributeError:
        pass
    return sub_orgs

  def DeleteOrganizationUnit(self, name):

    customer_id = self.RetrieveCustomerId()['customerId']
    name = urllib.quote_plus(name, safe='/')
    uri = '/a/feeds/orgunit/2.0/%s/%s' % (customer_id, name)
    return self._DeleteProperties(uri)
    
  def RetrieveUserOrganization(self, user):
 
    customer_id = self.RetrieveCustomerId()['customerId']
    if user.find('@') < 0:
      user = user+'@'+self.domain
    uri = '/a/feeds/orguser/2.0/%s/%s' % (customer_id, urllib.quote_plus(user))
    org = self._GetProperties(uri)
    try:
      org['orgUnitPath'] = urllib.unquote_plus(org['orgUnitPath'])
    except AttributeError:
      pass
    return org
    
  def RetrieveAllOrganizationUsers(self):
  
    customer_id = self.RetrieveCustomerId()['customerId']
    uri = '/a/feeds/orguser/2.0/%s?get=all' % customer_id
    all_users = self._GetPropertiesList(uri)
    for user in all_users:
      try:
        user['orgUnitPath'] = urllib.unquote_plus(user['orgUnitPath'])
      except AttributeError:
        pass
    return all_users

  def RetrieveAllOrganizationUnitUsers(self, name):
  
    customer_id = self.RetrieveCustomerId()['customerId']
    uri = '/a/feeds/orguser/2.0/%s?get=children&orgUnitPath=%s' % (customer_id, urllib.quote_plus(name))
    all_users = self._GetPropertiesList(uri)
    for user in all_users:
      try:
        user['orgUnitPath'] = urllib.unquote_plus(user['orgUnitPath'])
      except AttributeError:
        pass
    return all_users