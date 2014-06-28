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

"""Data model classes for the Email Settings API."""


__author__ = 'Claudio Cherubino <ccherubino@google.com>'


import atom.data
import gdata.apps
import gdata.apps_property
import gdata.data


# This is required to work around a naming conflict between the Google
# Spreadsheets API and Python's built-in property function
pyproperty = property


# The apps:property label of the label property
LABEL_NAME = 'label'

# The apps:property from of the filter property
FILTER_FROM_NAME = 'from'
# The apps:property to of the filter property
FILTER_TO_NAME = 'to'
# The apps:property subject of the filter property
FILTER_SUBJECT_NAME = 'subject'
# The apps:property hasTheWord of the filter property
FILTER_HAS_THE_WORD_NAME = 'hasTheWord'
# The apps:property doesNotHaveTheWord of the filter property
FILTER_DOES_NOT_HAVE_THE_WORD_NAME = 'doesNotHaveTheWord'
# The apps:property hasAttachment of the filter property
FILTER_HAS_ATTACHMENTS_NAME = 'hasAttachment'
# The apps:property label of the filter action property
FILTER_LABEL = 'label'
# The apps:property shouldMarkAsRead of the filter action property
FILTER_MARK_AS_READ = 'shouldMarkAsRead'
# The apps:property shouldArchive of the filter action propertylabel
FILTER_ARCHIVE = 'shouldArchive'

# The apps:property name of the send-as alias property
SENDAS_ALIAS_NAME = 'name'
# The apps:property address of theAPPS_TEMPLATE send-as alias property
SENDAS_ALIAS_ADDRESS = 'address'
# The apps:property replyTo of the send-as alias property
SENDAS_ALIAS_REPLY_TO = 'replyTo'
# The apps:property makeDefault of the send-as alias property
SENDAS_ALIAS_MAKE_DEFAULT = 'makeDefault'

# The apps:property enable of the webclip property
WEBCLIP_ENABLE = 'enable'

# The apps:property enable of the forwarding property
FORWARDING_ENABLE = 'enable'
# The apps:property forwardTo of the forwarding property
FORWARDING_TO = 'forwardTo'
# The apps:property action of the forwarding property
FORWARDING_ACTION = 'action'

# The apps:property enable of the POP property
POP_ENABLE = 'enable'
# The apps:property enableFor of the POP propertyACTION
POP_ENABLE_FOR = 'enableFor'
# The apps:property action of the POP property
POP_ACTION = 'action'

# The apps:property enable of the IMAP property
IMAP_ENABLE = 'enable'

# The apps:property enable of the vacation responder property
VACATION_RESPONDER_ENABLE = 'enable'
# The apps:property subject of the vacation responder property
VACATION_RESPONDER_SUBJECT = 'subject'
# The apps:property message of the vacation responder property
VACATION_RESPONDER_MESSAGE = 'message'
# The apps:property contactsOnly of the vacation responder property
VACATION_RESPONDER_CONTACTS_ONLY = 'contactsOnly'

# The apps:property signature of the signature property
SIGNATURE_VALUE = 'signature'

# The apps:property language of the language property
LANGUAGE_TAG = 'language'

# The apps:property pageSize of the general settings property
GENERAL_PAGE_SIZE = 'pageSize'
# The apps:property shortcuts of the general settings property
GENERAL_SHORTCUTS = 'shortcuts'
# The apps:property arrows of the general settings property
GENERAL_ARROWS = 'arrows'
# The apps:prgdata.appsoperty snippets of the general settings property
GENERAL_SNIPPETS = 'snippets'
# The apps:property uniAppsProcode of the general settings property
GENERAL_UNICODE = 'unicode'


class EmailSettingsEntry(gdata.data.GDEntry):
  """Represents an Email Settings entry in object form."""

  property = [gdata.apps_property.AppsProperty]

  def _GetProperty(self, name):
    """Get the apps:property value with the given name.

    Args:
      name: string Name of the apps:property value to get.

    Returns:
      The apps:property value with the given name, or None if the name was
      invalid.
    """

    value = None
    for p in self.property:
      if p.name == name:
        value = p.value
        break
    return value

  def _SetProperty(self, name, value):
    """Set the apps:property value with the given name to the given value.

    Args:
      name: string Name of the apps:property value to set.
      value: string Value to give the apps:property value with the given name.
    """
    found = False
    for i in range(len(self.property)):
      if self.property[i].name == name:
        self.property[i].value = value
        found = True
        break
    if not found:
      self.property.append(gdata.apps_property.AppsProperty(name=name, value=value))

  def find_edit_link(self):
    return self.uri


class EmailSettingsLabel(EmailSettingsEntry):
  """Represents a Label in object form."""

  def GetName(self):
    """Get the name of the Label object.

    Returns:
      The name of this Label object as a string or None.
    """

    return self._GetProperty(LABEL_NAME)

  def SetName(self, value):
    """Set the name of this Label object.

    Args:
      value: string The new label name to give this object.
    """

    self._SetProperty(LABEL_NAME, value)

  name = pyproperty(GetName, SetName)

  def __init__(self, uri=None, name=None, *args, **kwargs):
    """Constructs a new EmailSettingsLabel object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      name: string (optional) The name to give this new object.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsLabel, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if name:
      self.name = name


class EmailSettingsFilter(EmailSettingsEntry):
  """Represents an Email Settings Filter in object form."""

  def GetFrom(self):
    """Get the From value of the Filter object.

    Returns:
      The From value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_FROM_NAME)

  def SetFrom(self, value):
    """Set the From value of this Filter object.

    Args:
      value: string The new From value to give this object.
    """

    self._SetProperty(FILTER_FROM_NAME, value)

  from_address = pyproperty(GetFrom, SetFrom)

  def GetTo(self):
    """Get the To value of the Filter object.

    Returns:
      The To value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_TO_NAME)

  def SetTo(self, value):
    """Set the To value of this Filter object.

    Args:
      value: string The new To value to give this object.
    """

    self._SetProperty(FILTER_TO_NAME, value)

  to_address = pyproperty(GetTo, SetTo)

  def GetSubject(self):
    """Get the Subject value of the Filter object.

    Returns:
      The Subject value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_SUBJECT_NAME)

  def SetSubject(self, value):
    """Set the Subject value of this Filter object.

    Args:
      value: string The new Subject value to give this object.
    """

    self._SetProperty(FILTER_SUBJECT_NAME, value)

  subject = pyproperty(GetSubject, SetSubject)

  def GetHasTheWord(self):
    """Get the HasTheWord value of the Filter object.

    Returns:
      The HasTheWord value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_HAS_THE_WORD_NAME)

  def SetHasTheWord(self, value):
    """Set the HasTheWord value of this Filter object.

    Args:
      value: string The new HasTheWord value to give this object.
    """

    self._SetProperty(FILTER_HAS_THE_WORD_NAME, value)

  has_the_word = pyproperty(GetHasTheWord, SetHasTheWord)

  def GetDoesNotHaveTheWord(self):
    """Get the DoesNotHaveTheWord value of the Filter object.

    Returns:
      The DoesNotHaveTheWord value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_DOES_NOT_HAVE_THE_WORD_NAME)

  def SetDoesNotHaveTheWord(self, value):
    """Set the DoesNotHaveTheWord value of this Filter object.

    Args:
      value: string The new DoesNotHaveTheWord value to give this object.
    """

    self._SetProperty(FILTER_DOES_NOT_HAVE_THE_WORD_NAME, value)

  does_not_have_the_word = pyproperty(GetDoesNotHaveTheWord,
                                       SetDoesNotHaveTheWord)

  def GetHasAttachments(self):
    """Get the HasAttachments value of the Filter object.

    Returns:
      The HasAttachments value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_HAS_ATTACHMENTS_NAME)

  def SetHasAttachments(self, value):
    """Set the HasAttachments value of this Filter object.

    Args:
      value: string The new HasAttachments value to give this object.
    """

    self._SetProperty(FILTER_HAS_ATTACHMENTS_NAME, value)

  has_attachments = pyproperty(GetHasAttachments,
                               SetHasAttachments)

  def GetLabel(self):
    """Get the Label value of the Filter object.

    Returns:
      The Label value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_LABEL)

  def SetLabel(self, value):
    """Set the Label value of this Filter object.

    Args:
      value: string The new Label value to give this object.
    """

    self._SetProperty(FILTER_LABEL, value)

  label = pyproperty(GetLabel, SetLabel)

  def GetMarkAsRead(self):
    """Get the MarkAsRead value of the Filter object.

    Returns:
      The MarkAsRead value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_MARK_AS_READ)

  def SetMarkAsRead(self, value):
    """Set the MarkAsRead value of this Filter object.

    Args:
      value: string The new MarkAsRead value to give this object.
    """

    self._SetProperty(FILTER_MARK_AS_READ, value)

  mark_as_read = pyproperty(GetMarkAsRead, SetMarkAsRead)

  def GetArchive(self):
    """Get the Archive value of the Filter object.

    Returns:
      The Archive value of this Filter object as a string or None.
    """

    return self._GetProperty(FILTER_ARCHIVE)

  def SetArchive(self, value):
    """Set the Archive value of this Filter object.

    Args:
      value: string The new Archive value to give this object.
    """

    self._SetProperty(FILTER_ARCHIVE, value)

  archive = pyproperty(GetArchive, SetArchive)

  def __init__(self, uri=None, from_address=None, to_address=None,
    subject=None, has_the_word=None, does_not_have_the_word=None,
    has_attachments=None, label=None, mark_as_read=None,
    archive=None, *args, **kwargs):
    """Constructs a new EmailSettingsFilter object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      from_address: string (optional) The source email address for the filter.
      to_address: string (optional) The destination email address for
          the filter.
      subject: string (optional) The value the email must have in its
          subject to be filtered.
      has_the_word: string (optional) The value the email must have in its
          subject or body to be filtered.
      does_not_have_the_word: string (optional) The value the email cannot
           have in its subject or body to be filtered.
      has_attachments: Boolean (optional) Whether or not the email must
          have an attachment to be filtered.
      label: string (optional) The name of the label to apply to
          messages matching the filter criteria.
      mark_as_read: Boolean (optional) Whether or not to mark messages
          matching the filter criteria as read.
      archive: Boolean (optional) Whether or not to move messages
          matching to Archived state.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsFilter, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if from_address:
      self.from_address = from_address
    if to_address:
      self.to_address = to_address
    if subject:
      self.subject = subject
    if has_the_word:
      self.has_the_word = has_the_word
    if does_not_have_the_word:
      self.does_not_have_the_word = does_not_have_the_word
    if has_attachments is not None:
      self.has_attachments = str(has_attachments)
    if label:
      self.label = label
    if mark_as_read is not None:
      self.mark_as_read = str(mark_as_read)
    if archive is not None:
      self.archive = str(archive)


class EmailSettingsSendAsAlias(EmailSettingsEntry):
  """Represents an Email Settings send-as Alias in object form."""

  def GetName(self):
    """Get the Name of the send-as Alias object.

    Returns:
      The Name of this send-as Alias object as a string or None.
    """

    return self._GetProperty(SENDAS_ALIAS_NAME)

  def SetName(self, value):
    """Set the Name of this send-as Alias object.

    Args:
      value: string The new Name to give this object.
    """

    self._SetProperty(SENDAS_ALIAS_NAME, value)

  name = pyproperty(GetName, SetName)

  def GetAddress(self):
    """Get the Address of the send-as Alias object.

    Returns:
      The Address of this send-as Alias object as a string or None.
    """

    return self._GetProperty(SENDAS_ALIAS_ADDRESS)

  def SetAddress(self, value):
    """Set the Address of this send-as Alias object.

    Args:
      value: string The new Address to give this object.
    """

    self._SetProperty(SENDAS_ALIAS_ADDRESS, value)

  address = pyproperty(GetAddress, SetAddress)

  def GetReplyTo(self):
    """Get the ReplyTo address of the send-as Alias object.

    Returns:
      The ReplyTo address of this send-as Alias object as a string or None.
    """

    return self._GetProperty(SENDAS_ALIAS_REPLY_TO)

  def SetReplyTo(self, value):
    """Set the ReplyTo address of this send-as Alias object.

    Args:
      value: string The new ReplyTo address to give this object.
    """

    self._SetProperty(SENDAS_ALIAS_REPLY_TO, value)

  reply_to = pyproperty(GetReplyTo, SetReplyTo)

  def GetMakeDefault(self):
    """Get the MakeDefault value of the send-as Alias object.

    Returns:
      The MakeDefault value of this send-as Alias object as a string or None.
    """

    return self._GetProperty(SENDAS_ALIAS_MAKE_DEFAULT)

  def SetMakeDefault(self, value):
    """Set the MakeDefault value of this send-as Alias object.

    Args:
      value: string The new MakeDefault valueto give this object.WebClip
    """

    self._SetProperty(SENDAS_ALIAS_MAKE_DEFAULT, value)

  make_default = pyproperty(GetMakeDefault, SetMakeDefault)

  def __init__(self, uri=None, name=None, address=None, reply_to=None,
    make_default=None, *args, **kwargs):
    """Constructs a new EmailSettingsSendAsAlias object with the given
       arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      name: string (optional) The name that will appear in the "From" field
            for this user.
      address: string (optional) The email address that appears as the
               origination address for emails sent by this user.
      reply_to: string (optional) The address to be used as the reply-to
                address in email sent using the alias.
      make_default: Boolean (optional) Whether or not this alias should
                    become the default alias for this user.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsSendAsAlias, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if name:
      self.name = name
    if address:
      self.address = address
    if reply_to:
      self.reply_to = reply_to
    if make_default is not None:
      self.make_default = str(make_default)


class EmailSettingsWebClip(EmailSettingsEntry):
  """Represents a WebClip in object form."""

  def GetEnable(self):
    """Get the Enable value of the WebClip object.

    Returns:
      The Enable value of this WebClip object as a string or None.
    """

    return self._GetProperty(WEBCLIP_ENABLE)

  def SetEnable(self, value):
    """Set the Enable value of this WebClip object.

    Args:
      value: string The new Enable value to give this object.
    """

    self._SetProperty(WEBCLIP_ENABLE, value)

  enable = pyproperty(GetEnable, SetEnable)

  def __init__(self, uri=None, enable=None, *args, **kwargs):
    """Constructs a new EmailSettingsWebClip object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      enable: Boolean (optional) Whether to enable showing Web clips.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsWebClip, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if enable is not None:
      self.enable = str(enable)


class EmailSettingsForwarding(EmailSettingsEntry):
  """Represents Forwarding settings in object form."""

  def GetEnable(self):
    """Get the Enable value of the Forwarding object.

    Returns:
      The Enable value of this Forwarding object as a string or None.
    """

    return self._GetProperty(FORWARDING_ENABLE)

  def SetEnable(self, value):
    """Set the Enable value of this Forwarding object.

    Args:
      value: string The new Enable value to give this object.
    """

    self._SetProperty(FORWARDING_ENABLE, value)

  enable = pyproperty(GetEnable, SetEnable)

  def GetForwardTo(self):
    """Get the ForwardTo value of the Forwarding object.

    Returns:
      The ForwardTo value of this Forwarding object as a string or None.
    """

    return self._GetProperty(FORWARDING_TO)

  def SetForwardTo(self, value):
    """Set the ForwardTo value of this Forwarding object.

    Args:
      value: string The new ForwardTo value to give this object.
    """

    self._SetProperty(FORWARDING_TO, value)

  forward_to = pyproperty(GetForwardTo, SetForwardTo)

  def GetAction(self):
    """Get the Action value of the Forwarding object.

    Returns:
      The Action value of this Forwarding object as a string or None.
    """

    return self._GetProperty(FORWARDING_ACTION)

  def SetAction(self, value):
    """Set the Action value of this Forwarding object.

    Args:
      value: string The new Action value to give this object.
    """

    self._SetProperty(FORWARDING_ACTION, value)

  action = pyproperty(GetAction, SetAction)

  def __init__(self, uri=None, enable=None, forward_to=None, action=None,
    *args, **kwargs):
    """Constructs a new EmailSettingsForwarding object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      enable: Boolean (optional) Whether to enable incoming email forwarding.
      forward_to: string (optional) The address email will be forwarded to.
      action: string (optional) The action to perform after forwarding an
              email ("KEEP", "ARCHIVE", "DELETE").
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsForwarding, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if enable is not None:
      self.enable = str(enable)
    if forward_to:
      self.forward_to = forward_to
    if action:
      self.action = action


class EmailSettingsPop(EmailSettingsEntry):
  """Represents POP settings in object form."""

  def GetEnable(self):
    """Get the Enable value of the POP object.

    Returns:
      The Enable value of this POP object as a string or None.
    """

    return self._GetProperty(POP_ENABLE)

  def SetEnable(self, value):
    """Set the Enable value of this POP object.

    Args:
      value: string The new Enable value to give this object.
    """

    self._SetProperty(POP_ENABLE, value)

  enable = pyproperty(GetEnable, SetEnable)

  def GetEnableFor(self):
    """Get the EnableFor value of the POP object.

    Returns:
      The EnableFor value of this POP object as a string or None.
    """

    return self._GetProperty(POP_ENABLE_FOR)

  def SetEnableFor(self, value):
    """Set the EnableFor value of this POP object.

    Args:
      value: string The new EnableFor value to give this object.
    """

    self._SetProperty(POP_ENABLE_FOR, value)

  enable_for = pyproperty(GetEnableFor, SetEnableFor)

  def GetPopAction(self):
    """Get the Action value of the POP object.

    Returns:
      The Action value of this POP object as a string or None.
    """

    return self._GetProperty(POP_ACTION)

  def SetPopAction(self, value):
    """Set the Action value of this POP object.

    Args:
      value: string The new Action value to give this object.
    """

    self._SetProperty(POP_ACTION, value)

  action = pyproperty(GetPopAction, SetPopAction)

  def __init__(self, uri=None, enable=None, enable_for=None,
    action=None, *args, **kwargs):
    """Constructs a new EmailSettingsPOP object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      enable: Boolean (optional) Whether to enable incoming POP3 access.
      enable_for: string (optional) Whether to enable POP3 for all mail
                  ("ALL_MAIL"), or mail from now on ("MAIL_FROM_NOW_ON").
      action: string (optional) What Google Mail should do with its copy
              of the email after it is retrieved using POP
              ("KEEP", "ARCHIVE", or "DELETE").
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsPop, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if enable is not None:
      self.enable = str(enable)
    if enable_for:
      self.enable_for = enable_for
    if action:
      self.action = action


class EmailSettingsImap(EmailSettingsEntry):
  """Represents IMAP settings in object form."""

  def GetEnable(self):
    """Get the Enable value of the IMAP object.

    Returns:
      The Enable value of this IMAP object as a string or None.
    """

    return self._GetProperty(IMAP_ENABLE)

  def SetEnable(self, value):
    """Set the Enable value of this IMAP object.

    Args:
      value: string The new Enable value to give this object.
    """

    self._SetProperty(IMAP_ENABLE, value)

  enable = pyproperty(GetEnable, SetEnable)

  def __init__(self, uri=None, enable=None, *args, **kwargs):
    """Constructs a new EmailSettingsImap object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      enable: Boolean (optional) Whether to enable IMAP access.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsImap, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if enable is not None:
      self.enable = str(enable)


class EmailSettingsVacationResponder(EmailSettingsEntry):
  """Represents Vacation Responder settings in object form."""

  def GetEnable(self):
    """Get the Enable value of the Vacation Responder object.

    Returns:
      The Enable value of this Vacation Responder object as a string or None.
    """

    return self._GetProperty(VACATION_RESPONDER_ENABLE)

  def SetEnable(self, value):
    """Set the Enable value of this Vacation Responder object.

    Args:
      value: string The new Enable value to give this object.
    """

    self._SetProperty(VACATION_RESPONDER_ENABLE, value)

  enable = pyproperty(GetEnable, SetEnable)

  def GetSubject(self):
    """Get the Subject value of the Vacation Responder object.

    Returns:
      The Subject value of this Vacation Responder object as a string or None.
    """

    return self._GetProperty(VACATION_RESPONDER_SUBJECT)

  def SetSubject(self, value):
    """Set the Subject value of this Vacation Responder object.

    Args:
      value: string The new Subject value to give this object.
    """

    self._SetProperty(VACATION_RESPONDER_SUBJECT, value)

  subject = pyproperty(GetSubject, SetSubject)

  def GetMessage(self):
    """Get the Message value of the Vacation Responder object.

    Returns:
      The Message value of this Vacation Responder object as a string or None.
    """

    return self._GetProperty(VACATION_RESPONDER_MESSAGE)

  def SetMessage(self, value):
    """Set the Message value of this Vacation Responder object.

    Args:
      value: string The new Message value to give this object.
    """

    self._SetProperty(VACATION_RESPONDER_MESSAGE, value)

  message = pyproperty(GetMessage, SetMessage)

  def GetContactsOnly(self):
    """Get the ContactsOnly value of the Vacation Responder object.

    Returns:
      The ContactsOnly value of this Vacation Responder object as a
      string or None.
    """

    return self._GetProperty(VACATION_RESPONDER_ENABLE)

  def SetContactsOnly(self, value):
    """Set the ContactsOnly value of this Vacation Responder object.

    Args:
      value: string The new ContactsOnly value to give this object.
    """

    self._SetProperty(VACATION_RESPONDER_CONTACTS_ONLY, value)

  contacts_only = pyproperty(GetContactsOnly, SetContactsOnly)

  def __init__(self, uri=None, enable=None, subject=None,
    message=None, contacts_only=None, *args, **kwargs):
    """Constructs a new EmailSettingsVacationResponder object with the
       given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      enable: Boolean (optional) Whether to enable the vacation responder.
      subject: string (optional) The subject line of the vacation responder
               autoresponse.
      message: string (optional) The message body of the vacation responder
               autoresponse.
      contacts_only: Boolean (optional) Whether to only send autoresponses
                     to known contacts.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsVacationResponder, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if enable is not None:
      self.enable = str(enable)
    if subject:
      self.subject = subject
    if message:
      self.message = message
    if contacts_only is not None:
      self.contacts_only = str(contacts_only)


class EmailSettingsSignature(EmailSettingsEntry):
  """Represents a Signature in object form."""

  def GetValue(self):
    """Get the value of the Signature object.

    Returns:
      The value of this Signature object as a string or None.
    """

    value = self._GetProperty(SIGNATURE_VALUE)
    if value == ' ': # hack to support empty signature
      return ''
    else:
      return value

  def SetValue(self, value):
    """Set the name of this Signature object.

    Args:
      value: string The new signature value to give this object.
    """

    if value == '': # hack to support empty signature
      value = ' '
    self._SetProperty(SIGNATURE_VALUE, value)

  signature_value = pyproperty(GetValue, SetValue)

  def __init__(self, uri=None, signature=None, *args, **kwargs):
    """Constructs a new EmailSettingsSignature object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      signature: string (optional) The signature to be appended to outgoing
                 messages.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsSignature, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if signature is not None:
      self.signature_value = signature  


class EmailSettingsLanguage(EmailSettingsEntry):
  """Represents Language Settings in object form."""

  def GetLanguage(self):
    """Get the tag of the Language object.

    Returns:
      The tag of this Language object as a string or None.
    """

    return self._GetProperty(LANGUAGE_TAG)

  def SetLanguage(self, value):
    """Set the tag of this Language object.

    Args:
      value: string The new tag value to give this object.
    """

    self._SetProperty(LANGUAGE_TAG, value)

  language_tag = pyproperty(GetLanguage, SetLanguage)

  def __init__(self, uri=None, language=None, *args, **kwargs):
    """Constructs a new EmailSettingsLanguage object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      language: string (optional) The language tag for Google Mail's display
                language.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsLanguage, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if language:
      self.language_tag = language


class EmailSettingsGeneral(EmailSettingsEntry):
  """Represents General Settings in object form."""

  def GetPageSize(self):
    """Get the Page Size value of the General Settings object.

    Returns:
      The Page Size value of this General Settings object as a string or None.
    """

    return self._GetProperty(GENERAL_PAGE_SIZE)

  def SetPageSize(self, value):
    """Set the Page Size value of this General Settings object.

    Args:
      value: string The new Page Size value to give this object.
    """

    self._SetProperty(GENERAL_PAGE_SIZE, value)

  page_size = pyproperty(GetPageSize, SetPageSize)

  def GetShortcuts(self):
    """Get the Shortcuts value of the General Settings object.

    Returns:
      The Shortcuts value of this General Settings object as a string or None.
    """

    return self._GetProperty(GENERAL_SHORTCUTS)

  def SetShortcuts(self, value):
    """Set the Shortcuts value of this General Settings object.

    Args:
      value: string The new Shortcuts value to give this object.
    """

    self._SetProperty(GENERAL_SHORTCUTS, value)

  shortcuts = pyproperty(GetShortcuts, SetShortcuts)

  def GetArrows(self):
    """Get the Arrows value of the General Settings object.

    Returns:
      The Arrows value of this General Settings object as a string or None.
    """

    return self._GetProperty(GENERAL_ARROWS)

  def SetArrows(self, value):
    """Set the Arrows value of this General Settings object.

    Args:
      value: string The new Arrows value to give this object.
    """

    self._SetProperty(GENERAL_ARROWS, value)

  arrows = pyproperty(GetArrows, SetArrows)

  def GetSnippets(self):
    """Get the Snippets value of the General Settings object.

    Returns:
      The Snippets value of this General Settings object as a string or None.
    """

    return self._GetProperty(GENERAL_SNIPPETS)

  def SetSnippets(self, value):
    """Set the Snippets value of this General Settings object.

    Args:
      value: string The new Snippets value to give this object.
    """

    self._SetProperty(GENERAL_SNIPPETS, value)

  snippets = pyproperty(GetSnippets, SetSnippets)

  def GetUnicode(self):
    """Get the Unicode value of the General Settings object.

    Returns:
      The Unicode value of this General Settings object as a string or None.
    """

    return self._GetProperty(GENERAL_UNICODE)

  def SetUnicode(self, value):
    """Set the Unicode value of this General Settings object.

    Args:
      value: string The new Unicode value to give this object.
    """

    self._SetProperty(GENERAL_UNICODE, value)

  use_unicode = pyproperty(GetUnicode, SetUnicode)

  def __init__(self, uri=None, page_size=None, shortcuts=None,
    arrows=None, snippets=None, use_unicode=None, *args, **kwargs):
    """Constructs a new EmailSettingsGeneral object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      page_size: int (optional) The number of conversations to be shown per page.
      shortcuts: Boolean (optional) Whether to enable keyboard shortcuts.
      arrows: Boolean (optional) Whether to display arrow-shaped personal
              indicators next to email sent specifically to the user.
      snippets: Boolean (optional) Whether to display snippets of the messages
                in the inbox and when searching.
      use_unicode: Boolean (optional) Whether to use UTF-8 (unicode) encoding
                   for all outgoing messages.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(EmailSettingsGeneral, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if page_size is not None:
      self.page_size = str(page_size)
    if shortcuts is not None:
      self.shortcuts = str(shortcuts)
    if arrows is not None:
      self.arrows = str(arrows)
    if snippets is not None:
      self.snippets = str(snippets)
    if use_unicode is not None:
      self.use_unicode = str(use_unicode)
