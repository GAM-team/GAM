#!/usr/bin/python
#
# Copyright (C) 2008 Google.
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

"""Contains the methods to import mail via Google Apps Email Migration API.

  MigrationService: Provides methids to import mail.
"""

__author__ = 'google-apps-apis@googlegroups.com'


import base64
import gdata
import gdata.apps.service
import gdata.service
from gdata.apps import migration


API_VER = '2.0'


class MigrationService(gdata.apps.service.AppsService):
  """Client for the EMAPI migration service.  Use either ImportMail to import
  one message at a time, or AddBatchEntry and SubmitBatch to import a batch of
  messages at a time.
  """
  def __init__(self, email=None, password=None, domain=None, source=None,
               server='apps-apis.google.com', additional_headers=None):
    gdata.apps.service.AppsService.__init__(
        self, email=email, password=password, domain=domain, source=source,
        server=server, additional_headers=additional_headers)
    self.mail_batch = migration.BatchMailEventFeed()

  def _BaseURL(self):
    return '/a/feeds/migration/%s/%s' % (API_VER, self.domain)

  def ImportMail(self, user_name, mail_message, mail_item_properties,
                 mail_labels):
    """Import a single mail message.

    Args:
      user_name: The username to import messages to.
      mail_message: An RFC822 format email message.
      mail_item_properties: A list of Gmail properties to apply to the message.
      mail_labels: A list of labels to apply to the message.

    Returns:
      A MailEntry representing the successfully imported message.

    Raises:
      AppsForYourDomainException: An error occurred importing the message.
    """
    uri = '%s/%s/mail' % (self._BaseURL(), user_name)

    mail_entry = migration.MailEntry()
    mail_entry.rfc822_msg = migration.Rfc822Msg(text=(base64.b64encode(
        mail_message)))
    mail_entry.rfc822_msg.encoding = 'base64'
    mail_entry.mail_item_property = map(
        lambda x: migration.MailItemProperty(value=x), mail_item_properties)
    mail_entry.label = map(lambda x: migration.Label(label_name=x),
                           mail_labels)

    try:
      return migration.MailEntryFromString(str(self.Post(mail_entry, uri)))
    except gdata.service.RequestError, e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def AddBatchEntry(self, mail_message, mail_item_properties,
                    mail_labels):
    """Add a message to the current batch that you later will submit.

    Args:
      mail_message: An RFC822 format email message.
      mail_item_properties: A list of Gmail properties to apply to the message.
      mail_labels: A list of labels to apply to the message.

    Returns:
      The length of the MailEntry representing the message.
    """
    mail_entry = migration.BatchMailEntry()
    mail_entry.rfc822_msg = migration.Rfc822Msg(text=(base64.b64encode(
        mail_message)))
    mail_entry.rfc822_msg.encoding = 'base64'
    mail_entry.mail_item_property = map(
        lambda x: migration.MailItemProperty(value=x), mail_item_properties)
    mail_entry.label = map(lambda x: migration.Label(label_name=x),
                           mail_labels)

    self.mail_batch.AddBatchEntry(mail_entry)

    return len(str(mail_entry))

  def SubmitBatch(self, user_name):
    """Send a all the mail items you have added to the batch to the server.

    Args:
      user_name: The username to import messages to.

    Returns:
      A HTTPResponse from the web service call.

    Raises:
      AppsForYourDomainException: An error occurred importing the batch.
    """
    uri = '%s/%s/mail/batch' % (self._BaseURL(), user_name)

    try:
      self.result = self.Post(self.mail_batch, uri,
                              converter=migration.BatchMailEventFeedFromString)
    except gdata.service.RequestError, e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

    self.mail_batch = migration.BatchMailEventFeed()

    return self.result
