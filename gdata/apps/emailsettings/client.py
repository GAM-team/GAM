#!/usr/bin/python
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

"""EmailSettingsClient simplifies Email Settings API calls.

EmailSettingsClient extends gdata.client.GDClient to ease interaction with
the Google Apps Email Settings API.  These interactions include the ability
to create labels, filters, aliases, and update web-clip, forwarding, POP,
IMAP, vacation-responder, signature, language, and general settings.
"""


__author__ = 'Claudio Cherubino <ccherubino@google.com>'


import gdata.apps.emailsettings.data
import gdata.client
import urllib


# Email Settings URI template
# The strings in this template are eventually replaced with the API version,
# Google Apps domain name, username, and settingID, respectively.
EMAIL_SETTINGS_URI_TEMPLATE = '/a/feeds/emailsettings/%s/%s/%s/%s'


# The settingID value for the label requests
SETTING_ID_LABEL = 'label'
# The settingID value for the filter requests
SETTING_ID_FILTER = 'filter'
# The settingID value for the send-as requests
SETTING_ID_SENDAS = 'sendas'
# The settingID value for the webclip requests
SETTING_ID_WEBCLIP = 'webclip'
# The settingID value for the forwarding requests
SETTING_ID_FORWARDING = 'forwarding'
# The settingID value for the POP requests
SETTING_ID_POP = 'pop'
# The settingID value for the IMAP requests
SETTING_ID_IMAP = 'imap'
# The settingID value for the vacation responder requests
SETTING_ID_VACATION_RESPONDER = 'vacation'
# The settingID value for the signature requests
SETTING_ID_SIGNATURE = 'signature'
# The settingID value for the language requests
SETTING_ID_LANGUAGE = 'language'
# The settingID value for the general requests
SETTING_ID_GENERAL = 'general'


class EmailSettingsClient(gdata.client.GDClient):
  """Client extension for the Google Email Settings API service.

  Attributes:
    host: string The hostname for the Email Settings API service.
    api_version: string The version of the Email Settings API.
  """

  host = 'apps-apis.google.com'
  api_version = '2.0'
  auth_service = 'apps'
  auth_scopes = gdata.gauth.AUTH_SCOPES['apps']
  ssl = True

  def __init__(self, domain, auth_token=None, **kwargs):
    """Constructs a new client for the Email Settings API.

    Args:
      domain: string The Google Apps domain with Email Settings.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the email settings.
      kwargs: The other parameters to pass to the gdata.client.GDClient
          constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.domain = domain

  def make_email_settings_uri(self, username, setting_id):
    """Creates the URI for the Email Settings API call.

    Using this client's Google Apps domain, create the URI to setup
    email settings for the given user in that domain. If params are provided,
    append them as GET params.

    Args:
      username: string The name of the user affected by this setting.
      setting_id: string The key of the setting to be configured.

    Returns:
      A string giving the URI for Email Settings API calls for this client's
      Google Apps domain.
    """
    uri = EMAIL_SETTINGS_URI_TEMPLATE % (self.api_version, self.domain,
      username, setting_id)
    return uri

  MakeEmailSettingsUri = make_email_settings_uri

  def create_label(self, username, name, **kwargs):
    """Creates a label with the given properties.

    Args:
      username: string The name of the user.
      name: string The name of the label.
      kwargs: The other parameters to pass to gdata.client.GDClient.post().

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsLabel of the new resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_LABEL)
    new_label = gdata.apps.emailsettings.data.EmailSettingsLabel(
        uri=uri, name=name)
    return self.post(new_label, uri, **kwargs)

  CreateLabel = create_label

  def create_filter(self, username, from_address=None,
    to_address=None, subject=None, has_the_word=None,
    does_not_have_the_word=None, has_attachments=None,
    label=None, mark_as_read=None, archive=None, **kwargs):
    """Creates a filter with the given properties.

    Args:
      username: string The name of the user.
      from_address: string The source email address for the filter.
      to_address: string (optional) The destination email address for
          the filter.
      subject: string (optional) The value the email must have in its
          subject to be filtered.
      has_the_word: string (optional) The value the email must have
          in its subject or body to be filtered.
      does_not_have_the_word: string (optional) The value the email
          cannot have in its subject or body to be filtered.
      has_attachments: string (optional) A boolean string representing
          whether the email must have an attachment to be filtered.
      label: string (optional) The name of the label to apply to
          messages matching the filter criteria.
      mark_as_read: Boolean (optional) Whether or not to mark
          messages matching the filter criteria as read.
      archive: Boolean (optional) Whether or not to move messages
          matching to Archived state.
      kwargs: The other parameters to pass to gdata.client.GDClient.post().

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsFilter of the new resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_FILTER)
    new_filter = gdata.apps.emailsettings.data.EmailSettingsFilter(
        uri=uri, from_address=from_address,
        to_address=to_address, subject=subject,
        has_the_word=has_the_word,
        does_not_have_the_word=does_not_have_the_word,
        has_attachments=has_attachments, label=label,
        mark_as_read=mark_as_read, archive=archive)
    return self.post(new_filter, uri, **kwargs)

  CreateFilter = create_filter

  def create_sendas(self, username, name, address, reply_to=None,
    make_default=None, **kwargs):
    """Creates a send-as alias with the given properties.

    Args:
      username: string The name of the user.
      name: string The name that will appear in the "From" field.
      address: string The email address that appears as the
          origination address for emails sent by this user.
      reply_to: string (optional) The address to be used as the reply-to
          address in email sent using the alias.
      make_default: Boolean (optional) Whether or not this alias should
          become the default alias for this user.
      kwargs: The other parameters to pass to gdata.client.GDClient.post().

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsSendAsAlias of the
      new resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_SENDAS)
    new_alias = gdata.apps.emailsettings.data.EmailSettingsSendAsAlias(
        uri=uri, name=name, address=address,
        reply_to=reply_to, make_default=make_default)
    return self.post(new_alias, uri, **kwargs)

  CreateSendAs = create_sendas

  def update_webclip(self, username, enable, **kwargs):
    """Enable/Disable Google Mail web clip.

    Args:
      username: string The name of the user.
      enable: Boolean Whether to enable showing Web clips.
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsWebClip of the
      updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_WEBCLIP)
    new_webclip = gdata.apps.emailsettings.data.EmailSettingsWebClip(
        uri=uri, enable=enable)
    return self.update(new_webclip, **kwargs)

  UpdateWebclip = update_webclip

  def update_forwarding(self, username, enable, forward_to=None,
    action=None, **kwargs):
    """Update Google Mail Forwarding settings.

    Args:
      username: string The name of the user.
      enable: Boolean Whether to enable incoming email forwarding.
      forward_to: (optional) string The address email will be forwarded to.
      action: string (optional) The action to perform after forwarding 
          an email ("KEEP", "ARCHIVE", "DELETE").
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsForwarding of the
      updated resource
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_FORWARDING)
    new_forwarding = gdata.apps.emailsettings.data.EmailSettingsForwarding(
        uri=uri, enable=enable, forward_to=forward_to, action=action)
    return self.update(new_forwarding, **kwargs)

  UpdateForwarding = update_forwarding

  def update_pop(self, username, enable, enable_for=None, action=None,
    **kwargs):
    """Update Google Mail POP settings.

    Args:
      username: string The name of the user.
      enable: Boolean Whether to enable incoming POP3 access.
      enable_for: string (optional) Whether to enable POP3 for all mail
          ("ALL_MAIL"), or mail from now on ("MAIL_FROM_NOW_ON").
      action: string (optional) What Google Mail should do with its copy 
          of the email after it is retrieved using POP ("KEEP",
          "ARCHIVE", or "DELETE").
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsPop of the updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_POP)
    new_pop = gdata.apps.emailsettings.data.EmailSettingsPop(
        uri=uri, enable=enable,
        enable_for=enable_for, action=action)
    return self.update(new_pop, **kwargs)

  UpdatePop = update_pop

  def update_imap(self, username, enable, **kwargs):
    """Update Google Mail IMAP settings.

    Args:import gdata.apps_property
      username: string The name of the user.
      enable: Boolean Whether to enable IMAP access.language
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsImap of the updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_IMAP)
    new_imap = gdata.apps.emailsettings.data.EmailSettingsImap(
        uri=uri, enable=enable)
    return self.update(new_imap, **kwargs)

  UpdateImap = update_imap

  def update_vacation(self, username, enable, subject=None, message=None,
    contacts_only=None, **kwargs):
    """Update Google Mail vacation-responder settings.

    Args:
      username: string The name of the user.
      enable: Boolean Whether to enable the vacation responder.
      subject: string (optional) The subject line of the vacation responder
          autoresponse.
      message: string (optional) The message body of the vacation responder
          autoresponse.
      contacts_only: Boolean (optional) Whether to only send autoresponses
          to known contacts.
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsVacationResponder of the
      updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_VACATION_RESPONDER)
    new_vacation = gdata.apps.emailsettings.data.EmailSettingsVacationResponder(
        uri=uri, enable=enable, subject=subject,
        message=message, contacts_only=contacts_only)
    return self.update(new_vacation, **kwargs)

  UpdateVacation = update_vacation

  def update_signature(self, username, signature, **kwargs):
    """Update Google Mail signature.

    Args:
      username: string The name of the user.
      signature: string The signature to be appended to outgoing messages.
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsSignature of the
      updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_SIGNATURE)
    new_signature = gdata.apps.emailsettings.data.EmailSettingsSignature(
        uri=uri, signature=signature)
    return self.update(new_signature, **kwargs)

  UpdateSignature = update_signature

  def update_language(self, username, language, **kwargs):
    """Update Google Mail language settings.

    Args:
      username: string The name of the user.
      signature: string The language tag for Google Mail's display language.
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsLanguage of the
      updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_LANGUAGE)
    new_language = gdata.apps.emailsettings.data.EmailSettingsLanguage(
        uri=uri, language=language)
    return self.update(new_language, **kwargs)

  UpdateLanguage = update_language

  def update_general(self, username, page_size=None, shortcuts=None, arrows=None,
    snippets=None, use_unicode=None, **kwargs):
    """Update Google Mail general settings.

    Args:
      username: string The name of the user.
      page_size: int (optional) The number of conversations to be shown per page.
      shortcuts: Boolean (optional) Whether to enable keyboard shortcuts.
      arrows: Boolean (optional) Whether to display arrow-shaped personal
          indicators next to email sent specifically to the user.
      snippets: Boolean (optional) Whether to display snippets of the messages
          in the inbox and when searching.
      use_unicode: Boolean (optional) Whether to use UTF-8 (unicode) encoding
          for all outgoing messages.
      kwargs: The other parameters to pass to the update method.

    Returns:
      gdata.apps.emailsettings.data.EmailSettingsGeneral of the
      updated resource.
    """
    uri = self.MakeEmailSettingsUri(username=username,
      setting_id=SETTING_ID_GENERAL)
    new_general = gdata.apps.emailsettings.data.EmailSettingsGeneral(
        uri=uri, page_size=page_size, shortcuts=shortcuts,
        arrows=arrows, snippets=snippets, use_unicode=use_unicode)
    return self.update(new_general, **kwargs)

  UpdateGeneral = update_general
