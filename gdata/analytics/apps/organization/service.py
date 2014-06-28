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

"""Allow Google Apps domain administrators to manage organization unit and organization user.

  OrganizationService: Provides methods to manage organization unit and organization user.
"""

__author__ = 'Alexandre Vivien (alex@simplecode.fr)'


import gdata.apps
import gdata.apps.service
import gdata.service


API_VER = '2.0'
CUSTOMER_BASE_URL = '/a/feeds/customer/2.0/customerId'
BASE_UNIT_URL = '/a/feeds/orgunit/' + API_VER + '/%s'
UNIT_URL = BASE_UNIT_URL + '/%s'
UNIT_ALL_URL = BASE_UNIT_URL + '?get=all'
UNIT_CHILD_URL = BASE_UNIT_URL + '?get=children&orgUnitPath=%s'
BASE_USER_URL = '/a/feeds/orguser/' + API_VER + '/%s'
USER_URL = BASE_USER_URL + '/%s'
USER_ALL_URL = BASE_USER_URL + '?get=all'
USER_CHILD_URL = BASE_USER_URL + '?get=children&orgUnitPath=%s'


class OrganizationService(gdata.apps.service.PropertyService):
  """Client for the Google Apps Organizations service."""

  def _Bool2Str(self, b):
    if b is None:
      return None
    return str(b is True).lower()

  def RetrieveCustomerId(self):
    """Retrieve the Customer ID for the account of the authenticated administrator making this request.

    Args:
      None.

    Returns:
      A dict containing the result of the retrieve operation.
    """

    uri = CUSTOMER_BASE_URL
    return self._GetProperties(uri)

  def CreateOrgUnit(self, customer_id, name, parent_org_unit_path='/', description='', block_inheritance=False):
    """Create a Organization Unit.

    Args:
      customer_id: The ID of the Google Apps customer.
      name: The simple organization unit text name, not the full path name.
      parent_org_unit_path: The full path of the parental tree to this organization unit (default: '/').
                            Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)
      description: The human readable text description of the organization unit (optional).
      block_inheritance: This parameter blocks policy setting inheritance 
                         from organization units higher in the organization tree (default: False).

    Returns:
      A dict containing the result of the create operation.
    """

    uri = BASE_UNIT_URL % (customer_id)
    properties = {}
    properties['name'] = name
    properties['parentOrgUnitPath'] = parent_org_unit_path
    properties['description'] = description
    properties['blockInheritance'] = self._Bool2Str(block_inheritance)
    return self._PostProperties(uri, properties)

  def UpdateOrgUnit(self, customer_id, org_unit_path, name=None, parent_org_unit_path=None, 
                    description=None, block_inheritance=None):
    """Update a Organization Unit.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)
      name: The simple organization unit text name, not the full path name.
      parent_org_unit_path: The full path of the parental tree to this organization unit.
                            Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)
      description: The human readable text description of the organization unit.
      block_inheritance: This parameter blocks policy setting inheritance 
                         from organization units higher in the organization tree.

    Returns:
      A dict containing the result of the update operation.
    """
    
    uri = UNIT_URL % (customer_id, org_unit_path)
    properties = {}
    if name:
      properties['name'] = name
    if parent_org_unit_path:
      properties['parentOrgUnitPath'] = parent_org_unit_path
    if description:
      properties['description'] = description
    if block_inheritance:
      properties['blockInheritance'] = self._Bool2Str(block_inheritance)
    return self._PutProperties(uri, properties)
    
  def MoveUserToOrgUnit(self, customer_id, org_unit_path, users_to_move):
    """Move a user to an Organization Unit.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)
      users_to_move: Email addresses list of users to move. Note: You can move a maximum of 25 users at one time.

    Returns:
      A dict containing the result of the update operation.
    """
    
    uri = UNIT_URL % (customer_id, org_unit_path)
    properties = {}
    if users_to_move and isinstance(users_to_move, list):
      properties['usersToMove'] = ', '.join(users_to_move)
    return self._PutProperties(uri, properties)

  def RetrieveOrgUnit(self, customer_id, org_unit_path):
    """Retrieve a Orgunit based on its path.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)

    Returns:
      A dict containing the result of the retrieve operation.
    """
    uri = UNIT_URL % (customer_id, org_unit_path)
    return self._GetProperties(uri)
 
  def DeleteOrgUnit(self, customer_id, org_unit_path):
    """Delete a Orgunit based on its path.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)

    Returns:
      A dict containing the result of the delete operation.
    """
    uri = UNIT_URL % (customer_id, org_unit_path)
    return self._DeleteProperties(uri)

  def RetrieveAllOrgUnits(self, customer_id):
    """Retrieve all OrgUnits in the customer's domain.

    Args:
      customer_id: The ID of the Google Apps customer.

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = UNIT_ALL_URL % (customer_id)
    return self._GetPropertiesList(uri)

  def RetrievePageOfOrgUnits(self, customer_id, startKey=None):
    """Retrieve one page of OrgUnits in the customer's domain.
    
    Args:
      customer_id: The ID of the Google Apps customer.
      startKey: The key to continue for pagination through all OrgUnits.
      
    Returns:
      A feed object containing the result of the retrieve operation.
    """
    uri = UNIT_ALL_URL % (customer_id)
    if startKey is not None:
      uri += "&startKey=" + startKey
    property_feed = self._GetPropertyFeed(uri)
    return property_feed

  def RetrieveSubOrgUnits(self, customer_id, org_unit_path):
    """Retrieve all Sub-OrgUnits of the provided OrgUnit.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = UNIT_CHILD_URL % (customer_id, org_unit_path)
    return self._GetPropertiesList(uri)

  def RetrieveOrgUser(self, customer_id, user_email):
    """Retrieve the OrgUnit of the user.

    Args:
      customer_id: The ID of the Google Apps customer.
      user_email: The email address of the user.

    Returns:
      A dict containing the result of the retrieve operation.
    """
    uri = USER_URL % (customer_id, user_email)
    return self._GetProperties(uri)
    
  def UpdateOrgUser(self, customer_id, user_email, org_unit_path):
    """Update the OrgUnit of a OrgUser.

    Args:
      customer_id: The ID of the Google Apps customer.
      user_email: The email address of the user.
      org_unit_path: The new organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)

    Returns:
      A dict containing the result of the update operation.
    """
    
    uri = USER_URL % (customer_id, user_email)
    properties = {}
    if org_unit_path:
      properties['orgUnitPath'] = org_unit_path
    return self._PutProperties(uri, properties)

  def RetrieveAllOrgUsers(self, customer_id):
    """Retrieve all OrgUsers in the customer's domain.

    Args:
      customer_id: The ID of the Google Apps customer.

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = USER_ALL_URL % (customer_id)
    return self._GetPropertiesList(uri)

  def RetrievePageOfOrgUsers(self, customer_id, startKey=None):
    """Retrieve one page of OrgUsers in the customer's domain.
    
    Args:
      customer_id: The ID of the Google Apps customer.
      startKey: The key to continue for pagination through all OrgUnits.
      
    Returns:
      A feed object containing the result of the retrieve operation.
    """
    uri = USER_ALL_URL % (customer_id)
    if startKey is not None:
      uri += "&startKey=" + startKey
    property_feed = self._GetPropertyFeed(uri)
    return property_feed

  def RetrieveOrgUnitUsers(self, customer_id, org_unit_path):
    """Retrieve all OrgUsers of the provided OrgUnit.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = USER_CHILD_URL % (customer_id, org_unit_path)
    return self._GetPropertiesList(uri)

  def RetrieveOrgUnitPageOfUsers(self, customer_id, org_unit_path, startKey=None):
    """Retrieve one page of OrgUsers of the provided OrgUnit.

    Args:
      customer_id: The ID of the Google Apps customer.
      org_unit_path: The organization's full path name.
                     Note: Each element of the path MUST be URL encoded (example: finance%2Forganization/suborganization)
      startKey: The key to continue for pagination through all OrgUsers.

    Returns:
      A feed object containing the result of the retrieve operation.
    """
    uri = USER_CHILD_URL % (customer_id, org_unit_path)
    if startKey is not None:
      uri += "&startKey=" + startKey
    property_feed = self._GetPropertyFeed(uri)
    return property_feed
