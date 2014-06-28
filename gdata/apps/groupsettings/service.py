#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GroupSettingsService simplifies Group Settings API calls.

GroupSettingsService extends gdata.apps.service.PropertyService to ease interaction with
the Google Apps Group Settings API.
"""

__author__ = 'Jay Lee <jay0lee@gmail.com>'

import gdata.apps
import gdata.apps.service
import gdata.service

# Group Settings URI template
GROUP_SETTINGS_URI_TEMPLATE = '/groups/v1/groups/%s?alt=atom'

class GroupSettingsService(gdata.apps.service.PropertyService):
  """Service extension for the Google Group Settings API service."""

  def __init__(self, email=None, password=None, domain=None, source=None,
               server='www.googleapis.com', additional_headers=None,
               **kwargs):
    """Creates a client for the Group Settings service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      domain: string (optional) The Google Apps domain name.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'apps-apis.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='apps', source=source,
        server=server, additional_headers=additional_headers, **kwargs)
    self.ssl = True
    self.port = 443
    self.domain = domain

  def make_group_settings_uri(self, group_email):
    """Creates the URI for the Group Settings API call.

    Create the URI to access the group settings API. If params are provided,
    append them as GET params.

    Args:
      group: email address of the group

    Returns:
      A string giving the URI for Group Settings API calls

    """
    uri = GROUP_SETTINGS_URI_TEMPLATE % (group_email)
    return uri

  MakeGroupSettingsUri = make_group_settings_uri

  def retrieve_group_settings(self, group_email):
    """Retrieves group settings

    Args:
      group_email: string, the group email address

    Returns:
      A dict. The group settings
    """
    uri = self.MakeGroupSettingsUri(group_email)
    group_settings_entry = self.Get(uri)
    group_settings_values = []
    for group_settings_value in group_settings_entry.extension_elements:
      group_settings_values.append({group_settings_value.tag: group_settings_value.text})
    return group_settings_values

  RetrieveGroupSettings = retrieve_group_settings
  
  def update_group_settings(self, group_email, allow_external_members=None,
    allow_google_communication=None, allow_web_posting=None, archive_only=None, custom_reply_to=None,
    default_message_deny_notification_text=None, description=None, is_archived=None, max_message_bytes=None,
    members_can_post_as_the_group=None, message_display_font=None, message_moderation_level=None, name=None,
    primary_language=None, reply_to=None, send_message_deny_notification=None, show_in_group_directory=None,
    who_can_invite=None, who_can_join=None, who_can_post_message=None, who_can_view_group=None,
    who_can_view_membership=None, include_in_global_address_list=None, spam_moderation_level=None):
    
    uri = self.MakeGroupSettingsUri(group_email)
    
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:apps="http://schemas.google.com/apps/2006" xmlns:gd="http://schemas.google.com/g/2005">
  <id>tag:googleapis.com,2010:apps:groupssettings:GROUP:NNN</id>
  <title>Groups Resource Entry</title>
  <author>
    <name>Google</name>
  </author>
  <apps:id>%s</apps:id>
  <apps:email>%s</apps:email>

''' % (group_email, group_email)
  
    template = "<apps:%s>%s</apps:%s>\n"
    if name != None:
      xml += template % ('name', name, 'name')
    if allow_external_members != None:
      xml += template % ('allowExternalMembers', allow_external_members, 'allowExternalMembers')
    if allow_google_communication != None:
      xml += template % ('allowGoogleCommunication', allow_google_communication, 'allowGoogleCommunication')
    if allow_web_posting != None:
      xml += template % ('allowWebPosting', allow_web_posting, 'allowWebPosting')
    if archive_only != None:
      xml += template % ('archiveOnly', archive_only, 'archiveOnly')
    if custom_reply_to != None:
      xml += template % ('customReplyTo', custom_reply_to, 'customReplyTo')
    if default_message_deny_notification_text != None:
      xml += template % ('defaultMessageDenyNotificationText', default_message_deny_notification_text, 'defaultMessageDenyNotificationText')
    if description != None:
      xml += template % ('description', description, 'description')
    if is_archived != None:
      xml += template % ('isArchived', is_archived, 'isArchived')
    if max_message_bytes != None:
      xml += template % ('maxMessageBytes', max_message_bytes, 'maxMessageBytes')
    if members_can_post_as_the_group != None:
      xml += template % ('membersCanPostAsTheGroup', members_can_post_as_the_group, 'membersCanPostAsTheGroup')
    if message_display_font != None:
      xml += template % ('messageDisplayFont', message_display_font, 'messageDisplayFont')
    if message_moderation_level != None:
      xml += template % ('messageModerationLevel', message_moderation_level, 'messageModerationLevel')
    if primary_language != None:
      xml += template % ('primaryLanguage', primary_language, 'primaryLanguage')
    if reply_to != None:
      xml += template % ('replyTo', reply_to, 'replyTo')
    if send_message_deny_notification != None:
      xml += template % ('sendMessageDenyNotification', send_message_deny_notification, 'sendMessageDenyNotification')
    if show_in_group_directory != None:
      xml += template % ('showInGroupDirectory', show_in_group_directory, 'showInGroupDirectory')
    if who_can_invite != None:
      xml += template % ('whoCanInvite', who_can_invite, 'whoCanInvite')
    if who_can_join != None:
      xml += template % ('whoCanJoin', who_can_join, 'whoCanJoin')
    if who_can_post_message != None:
      xml += template % ('whoCanPostMessage', who_can_post_message, 'whoCanPostMessage')
    if who_can_view_group != None:
      xml += template % ('whoCanViewGroup', who_can_view_group, 'whoCanViewGroup')
    if who_can_view_membership != None:
      xml += template % ('whoCanViewMembership', who_can_view_membership, 'whoCanViewMembership')
    if include_in_global_address_list != None:
      xml += template % ('includeInGlobalAddressList', include_in_global_address_list, 'includeInGlobalAddressList')
    if spam_moderation_level != None:
      xml += template % ('spamModerationLevel', spam_moderation_level, 'spamModerationLevel')
    xml += '</entry>'
    group_settings_entry = self.Put(uri=uri, data=xml)
    group_settings_values = []
    for group_settings_value in group_settings_entry.extension_elements:
      group_settings_values.append({group_settings_value.tag: group_settings_value.text})
    return group_settings_values

  UpdateGroupSettings = update_group_settings
