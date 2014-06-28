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

"""Allow Google Apps domain administrators to manage groups, group members and group owners.

  GroupsService: Provides methods to manage groups, members and owners.
"""

__author__ = 'google-apps-apis@googlegroups.com'


import urllib
import gdata.apps
import gdata.apps.service
import gdata.service


API_VER = '2.0'
BASE_URL = '/a/feeds/group/' + API_VER + '/%s'
GROUP_MEMBER_URL = BASE_URL + '?member=%s'
GROUP_MEMBER_DIRECT_URL = GROUP_MEMBER_URL + '&directOnly=%s'
GROUP_ID_URL = BASE_URL + '/%s'
MEMBER_URL = BASE_URL + '/%s/member'
MEMBER_WITH_SUSPENDED_URL = MEMBER_URL + '?includeSuspendedUsers=%s'
MEMBER_ID_URL = MEMBER_URL + '/%s'
OWNER_URL = BASE_URL + '/%s/owner'
OWNER_WITH_SUSPENDED_URL = OWNER_URL + '?includeSuspendedUsers=%s'
OWNER_ID_URL = OWNER_URL + '/%s'

PERMISSION_OWNER = 'Owner'
PERMISSION_MEMBER = 'Member'
PERMISSION_DOMAIN = 'Domain'
PERMISSION_ANYONE = 'Anyone'


class GroupsService(gdata.apps.service.PropertyService):
  """Client for the Google Apps Groups service."""

  def _ServiceUrl(self, service_type, is_existed, group_id, member_id, owner_email,
                  direct_only=False, domain=None, suspended_users=False):
    if domain is None:
      domain = self.domain

    if service_type == 'group':
      if group_id != '' and is_existed:
        return GROUP_ID_URL % (domain, group_id)
      elif member_id != '':
        if direct_only:
          return GROUP_MEMBER_DIRECT_URL % (domain, urllib.quote_plus(member_id),
                                            self._Bool2Str(direct_only))
        else:
          return GROUP_MEMBER_URL % (domain, urllib.quote_plus(member_id))
      else:
        return BASE_URL % (domain)

    if service_type == 'member':
      if member_id != '' and is_existed:
        return MEMBER_ID_URL % (domain, group_id, urllib.quote_plus(member_id))
      elif suspended_users:
        return MEMBER_WITH_SUSPENDED_URL % (domain, group_id,
                                            self._Bool2Str(suspended_users))
      else:
        return MEMBER_URL % (domain, group_id)

    if service_type == 'owner':
      if owner_email != '' and is_existed:
        return OWNER_ID_URL % (domain, group_id, urllib.quote_plus(owner_email))
      elif suspended_users:
        return OWNER_WITH_SUSPENDED_URL % (domain, group_id,
                                           self._Bool2Str(suspended_users))
      else:
        return OWNER_URL % (domain, group_id)

  def _Bool2Str(self, b):
    if b is None:
      return None
    return str(b is True).lower()

  def _IsExisted(self, uri):
    try:
      self._GetProperties(uri)
      return True
    except gdata.apps.service.AppsForYourDomainException, e:
      if e.error_code == gdata.apps.service.ENTITY_DOES_NOT_EXIST:
        return False
      else:
        raise e

  def CreateGroup(self, group_id, group_name, description, email_permission):
    """Create a group.

    Args:
      group_id: The ID of the group (e.g. us-sales).
      group_name: The name of the group.
      description: A description of the group
      email_permission: The subscription permission of the group.

    Returns:
      A dict containing the result of the create operation.
    """
    uri = self._ServiceUrl('group', False, group_id, '', '')
    properties = {}
    properties['groupId'] = group_id
    properties['groupName'] = group_name
    properties['description'] = description
    properties['emailPermission'] = email_permission
    return self._PostProperties(uri, properties)

  def UpdateGroup(self, group_id, group_name, description, email_permission):
    """Update a group's name, description and/or permission.

    Args:
      group_id: The ID of the group (e.g. us-sales).
      group_name: The name of the group.
      description: A description of the group
      email_permission: The subscription permission of the group.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._ServiceUrl('group', True, group_id, '', '')
    properties = {}
    properties['groupId'] = group_id
    properties['groupName'] = group_name
    properties['description'] = description
    properties['emailPermission'] = email_permission
    return self._PutProperties(uri, properties)

  def RetrieveGroup(self, group_id):
    """Retrieve a group based on its ID.

    Args:
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('group', True, group_id, '', '')
    return self._GetProperties(uri)

  def RetrieveAllGroups(self):
    """Retrieve all groups in the domain.

    Args:
      None

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('group', True, '', '', '')
    return self._GetPropertiesList(uri)

  def RetrievePageOfGroups(self, start_group=None):
    """Retrieve one page of groups in the domain.
    
    Args:
      start_group: The key to continue for pagination through all groups.
      
    Returns:
      A feed object containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('group', True, '', '', '')
    if start_group is not None:
      uri += "?start="+start_group
    property_feed = self._GetPropertyFeed(uri)
    return property_feed

  def RetrieveGroups(self, member_id, direct_only=False):
    """Retrieve all groups that belong to the given member_id.

    Args:
      member_id: The member's email address (e.g. member@example.com).
      direct_only: Boolean whether only return groups that this member directly belongs to.

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('group', True, '', member_id, '', direct_only=direct_only)
    return self._GetPropertiesList(uri)

  def DeleteGroup(self, group_id):
    """Delete a group based on its ID.

    Args:
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the delete operation.
    """
    uri = self._ServiceUrl('group', True, group_id, '', '')
    return self._DeleteProperties(uri)

  def AddMemberToGroup(self, member_id, group_id):
    """Add a member to a group.

    Args:
      member_id: The member's email address (e.g. member@example.com).
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the add operation.
    """
    uri = self._ServiceUrl('member', False, group_id, member_id, '')
    properties = {}
    properties['memberId'] = member_id
    return self._PostProperties(uri, properties)

  def IsMember(self, member_id, group_id):
    """Check whether the given member already exists in the given group.

    Args:
      member_id: The member's email address (e.g. member@example.com).
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      True if the member exists in the group.  False otherwise.
    """
    uri = self._ServiceUrl('member', True, group_id, member_id, '')
    return self._IsExisted(uri)

  def RetrieveMember(self, member_id, group_id):
    """Retrieve the given member in the given group.

    Args:
      member_id: The member's email address (e.g. member@example.com).
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('member', True, group_id, member_id, '')
    return self._GetProperties(uri)

  def RetrieveAllMembers(self, group_id, suspended_users=False):
    """Retrieve all members in the given group.

    Args:
      group_id: The ID of the group (e.g. us-sales).
      suspended_users: A boolean; should we include any suspended users in
        the membership list returned?

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('member', True, group_id, '', '',
                           suspended_users=suspended_users)
    return self._GetPropertiesList(uri)
    
  def RetrievePageOfMembers(self, group_id, suspended_users=False, start=None):
    """Retrieve one page of members of a given group.
    
    Args:
      group_id: The ID of the group (e.g. us-sales).
      suspended_users: A boolean; should we include any suspended users in
        the membership list returned?
      start: The key to continue for pagination through all members.

    Returns:
      A feed object containing the result of the retrieve operation.
    """
    
    uri = self._ServiceUrl('member', True, group_id, '', '',
                           suspended_users=suspended_users)
    if start is not None:
      if suspended_users:
        uri += "&start="+start
      else:
        uri += "?start="+start
    property_feed = self._GetPropertyFeed(uri)
    return property_feed

  def RemoveMemberFromGroup(self, member_id, group_id):
    """Remove the given member from the given group.

    Args:
      member_id: The member's email address (e.g. member@example.com).
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the remove operation.
    """
    uri = self._ServiceUrl('member', True, group_id, member_id, '')
    return self._DeleteProperties(uri)

  def AddOwnerToGroup(self, owner_email, group_id):
    """Add an owner to a group.

    Args:
      owner_email: The email address of a group owner.
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the add operation.
    """
    uri = self._ServiceUrl('owner', False, group_id, '', owner_email)
    properties = {}
    properties['email'] = owner_email
    return self._PostProperties(uri, properties)

  def IsOwner(self, owner_email, group_id):
    """Check whether the given member an owner of the given group.

    Args:
      owner_email: The email address of a group owner.
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      True if the member is an owner of the given group.  False otherwise.
    """
    uri = self._ServiceUrl('owner', True, group_id, '', owner_email)
    return self._IsExisted(uri)

  def RetrieveOwner(self, owner_email, group_id):
    """Retrieve the given owner in the given group.

    Args:
      owner_email: The email address of a group owner.
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('owner', True, group_id, '', owner_email)
    return self._GetProperties(uri)

  def RetrieveAllOwners(self, group_id, suspended_users=False):
    """Retrieve all owners of the given group.

    Args:
      group_id: The ID of the group (e.g. us-sales).
      suspended_users: A boolean; should we include any suspended users in
        the ownership list returned?

    Returns:
      A list containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('owner', True, group_id, '', '',
                           suspended_users=suspended_users)
    return self._GetPropertiesList(uri)
    
  def RetrievePageOfOwners(self, group_id, suspended_users=False, start=None):
    """Retrieve one page of owners of the given group.
    
    Args:
      group_id: The ID of the group (e.g. us-sales).
      suspended_users: A boolean; should we include any suspended users in
        the ownership list returned?
      start: The key to continue for pagination through all owners.

    Returns:
      A feed object containing the result of the retrieve operation.
    """
    uri = self._ServiceUrl('owner', True, group_id, '', '',
                           suspended_users=suspended_users)
    if start is not None:
      if suspended_users:
        uri += "&start="+start
      else:
        uri += "?start="+start
    property_feed = self._GetPropertyFeed(uri)
    return property_feed
        
  def RemoveOwnerFromGroup(self, owner_email, group_id):
    """Remove the given owner from the given group.

    Args:
      owner_email: The email address of a group owner.
      group_id: The ID of the group (e.g. us-sales).

    Returns:
      A dict containing the result of the remove operation.
    """
    uri = self._ServiceUrl('owner', True, group_id, '', owner_email)
    return self._DeleteProperties(uri)
