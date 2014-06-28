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

"""Allow Google Apps domain administrators to set users' email settings.

  EmailSettingsService: Set various email settings.
"""

__author__ = 'google-apps-apis@googlegroups.com'


import gdata.apps
import gdata.apps.service
import gdata.service


API_VER='2.0'
# Forwarding and POP3 options
KEEP='KEEP'
ARCHIVE='ARCHIVE'
DELETE='DELETE'
ALL_MAIL='ALL_MAIL'
MAIL_FROM_NOW_ON='MAIL_FROM_NOW_ON'


class EmailSettingsService(gdata.apps.service.PropertyService):
  """Client for the Google Apps Email Settings service."""

  def _serviceUrl(self, setting_id, username, domain=None):
    if domain is None:
      domain = self.domain
    return '/a/feeds/emailsettings/%s/%s/%s/%s' % (API_VER, domain, username,
                                                   setting_id)

  def CreateLabel(self, username, label):
    """Create a label.

    Args:
      username: User to create label for.
      label: Label to create.

    Returns:
      A dict containing the result of the create operation.
    """
    uri = self._serviceUrl('label', username)
    properties = {'label': label}
    return self._PostProperties(uri, properties)

  def CreateFilter(self, username, from_=None, to=None, subject=None,
                   has_the_word=None, does_not_have_the_word=None,
                   has_attachment=None, label=None, should_mark_as_read=None,
                   should_archive=None):
    """Create a filter.

    Args:
      username: User to create filter for.
      from_: Filter from string.
      to: Filter to string.
      subject: Filter subject.
      has_the_word: Words to filter in.
      does_not_have_the_word: Words to filter out.
      has_attachment:  Boolean for message having attachment.
      label: Label to apply.
      should_mark_as_read: Boolean for marking message as read.
      should_archive: Boolean for archiving message.

    Returns:
      A dict containing the result of the create operation.
    """
    uri = self._serviceUrl('filter', username)
    properties = {}
    properties['from'] = from_
    properties['to'] = to
    properties['subject'] = subject
    properties['hasTheWord'] = has_the_word
    properties['doesNotHaveTheWord'] = does_not_have_the_word
    properties['hasAttachment'] = gdata.apps.service._bool2str(has_attachment)
    properties['label'] = label
    properties['shouldMarkAsRead'] = gdata.apps.service._bool2str(should_mark_as_read)
    properties['shouldArchive'] = gdata.apps.service._bool2str(should_archive)
    return self._PostProperties(uri, properties)

  def CreateSendAsAlias(self, username, name, address, reply_to=None,
                        make_default=None):
    """Create alias to send mail as.

    Args:
      username: User to create alias for.
      name: Name of alias.
      address: Email address to send from.
      reply_to: Email address to reply to.
      make_default: Boolean for whether this is the new default sending alias.

    Returns:
      A dict containing the result of the create operation.
    """
    uri = self._serviceUrl('sendas', username)
    properties = {}
    properties['name'] = name
    properties['address'] = address
    properties['replyTo'] = reply_to
    properties['makeDefault'] = gdata.apps.service._bool2str(make_default)
    return self._PostProperties(uri, properties)

  def UpdateWebClipSettings(self, username, enable):
    """Update WebClip Settings

    Args:
      username: User to update forwarding for.
      enable: Boolean whether to enable Web Clip.
    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('webclip', username)
    properties = {}
    properties['enable'] = gdata.apps.service._bool2str(enable)
    return self._PutProperties(uri, properties)

  def UpdateForwarding(self, username, enable, forward_to=None, action=None):
    """Update forwarding settings.

    Args:
      username: User to update forwarding for.
      enable: Boolean whether to enable this forwarding rule.
      forward_to: Email address to forward to.
      action: Action to take after forwarding.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('forwarding', username)
    properties = {}
    properties['enable'] = gdata.apps.service._bool2str(enable)
    if enable is True:
      properties['forwardTo'] = forward_to
      properties['action'] = action
    return self._PutProperties(uri, properties)

  def UpdatePop(self, username, enable, enable_for=None, action=None):
    """Update POP3 settings.

    Args:
      username: User to update POP3 settings for.
      enable: Boolean whether to enable POP3.
      enable_for: Which messages to make available via POP3.
      action: Action to take after user retrieves email via POP3.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('pop', username)
    properties = {}
    properties['enable'] = gdata.apps.service._bool2str(enable)
    if enable is True:
      properties['enableFor'] = enable_for
      properties['action'] = action
    return self._PutProperties(uri, properties)

  def UpdateImap(self, username, enable):
    """Update IMAP settings.

    Args:
      username: User to update IMAP settings for.
      enable: Boolean whether to enable IMAP.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('imap', username)
    properties = {'enable': gdata.apps.service._bool2str(enable)}
    return self._PutProperties(uri, properties)

  def UpdateVacation(self, username, enable, subject=None, message=None,
                     contacts_only=None):
    """Update vacation settings.

    Args:
      username: User to update vacation settings for.
      enable: Boolean whether to enable vacation responses.
      subject: Vacation message subject.
      message: Vacation message body.
      contacts_only: Boolean whether to send message only to contacts.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('vacation', username)
    properties = {}
    properties['enable'] = gdata.apps.service._bool2str(enable)
    if enable is True:
      properties['subject'] = subject
      properties['message'] = message
      properties['contactsOnly'] = gdata.apps.service._bool2str(contacts_only)
    return self._PutProperties(uri, properties)

  def UpdateSignature(self, username, signature):
    """Update signature.

    Args:
      username: User to update signature for.
      signature: Signature string.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('signature', username)
    properties = {'signature': signature}
    return self._PutProperties(uri, properties)

  def UpdateLanguage(self, username, language):
    """Update user interface language.

    Args:
      username: User to update language for.
      language: Language code.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('language', username)
    properties = {'language': language}
    return self._PutProperties(uri, properties)

  def UpdateGeneral(self, username, page_size=None, shortcuts=None, arrows=None,
                    snippets=None, unicode=None):
    """Update general settings.

    Args:
      username: User to update general settings for.
      page_size: Number of messages to show.
      shortcuts: Boolean whether shortcuts are enabled.
      arrows: Boolean whether arrows are enabled.
      snippets: Boolean whether snippets are enabled.
      unicode: Wheter unicode is enabled.

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('general', username)
    properties = {}
    if page_size != None:
      properties['pageSize'] = str(page_size)
    if shortcuts != None:
      properties['shortcuts'] = gdata.apps.service._bool2str(shortcuts)
    if arrows != None:
      properties['arrows'] = gdata.apps.service._bool2str(arrows)
    if snippets != None:
      properties['snippets'] = gdata.apps.service._bool2str(snippets)
    if unicode != None:
      properties['unicode'] = gdata.apps.service._bool2str(unicode)
    return self._PutProperties(uri, properties)
