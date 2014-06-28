#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.
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

  MigrationService: Provides methods to import mail.
"""

__author__ = ('google-apps-apis@googlegroups.com',
              'pti@google.com (Prashant Tiwari)')


import base64
import threading
import time
from atom.service import deprecation
from gdata.apps import migration
from gdata.apps.migration import MailEntryProperties
import gdata.apps.service
import gdata.service


API_VER = '2.0'


class MigrationService(gdata.apps.service.AppsService):
  """Client for the EMAPI migration service.  Use either ImportMail to import
  one message at a time, or AddMailEntry and ImportMultipleMails to import a
  bunch of messages at a time.
  """

  def __init__(self, email=None, password=None, domain=None, source=None,
               server='apps-apis.google.com', additional_headers=None):
    gdata.apps.service.AppsService.__init__(
        self, email=email, password=password, domain=domain, source=source,
        server=server, additional_headers=additional_headers)
    self.mail_batch = migration.BatchMailEventFeed()
    self.mail_entries = []
    self.exceptions = 0

  def _BaseURL(self):
    return '/a/feeds/migration/%s/%s' % (API_VER, self.domain)

  def ImportMail(self, user_name, mail_message, mail_item_properties,
                 mail_labels):
    """Imports a single mail message.

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
      # Store the number of failed imports when importing several at a time 
      self.exceptions += 1
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def AddBatchEntry(self, mail_message, mail_item_properties,
                    mail_labels):
    """Adds a message to the current batch that you later will submit.
    
    Deprecated, use AddMailEntry instead

    Args:
      mail_message: An RFC822 format email message.
      mail_item_properties: A list of Gmail properties to apply to the message.
      mail_labels: A list of labels to apply to the message.

    Returns:
      The length of the MailEntry representing the message.
    """
    deprecation("calling deprecated method AddBatchEntry")
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
    """Sends all the mail items you have added to the batch to the server.
    
    Deprecated, use ImportMultipleMails instead

    Args:
      user_name: The username to import messages to.

    Returns:
      An HTTPResponse from the web service call.

    Raises:
      AppsForYourDomainException: An error occurred importing the batch.
    """
    deprecation("calling deprecated method SubmitBatch")
    uri = '%s/%s/mail/batch' % (self._BaseURL(), user_name)

    try:
      self.result = self.Post(self.mail_batch, uri,
                              converter=migration.BatchMailEventFeedFromString)
    except gdata.service.RequestError, e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

    self.mail_batch = migration.BatchMailEventFeed()

    return self.result

  def AddMailEntry(self, mail_message, mail_item_properties=None,
                   mail_labels=None, identifier=None):
    """Prepares a list of mail messages to import using ImportMultipleMails.
    
    Args:
      mail_message: An RFC822 format email message as a string.
      mail_item_properties: List of Gmail properties to apply to the
          message.
      mail_labels: List of Gmail labels to apply to the message.
      identifier: The optional file identifier string
    
    Returns:
      The number of email messages to be imported.
    """
    mail_entry_properties = MailEntryProperties(
        mail_message=mail_message,
        mail_item_properties=mail_item_properties,
        mail_labels=mail_labels,
        identifier=identifier)

    self.mail_entries.append(mail_entry_properties)
    return len(self.mail_entries)

  def ImportMultipleMails(self, user_name, threads_per_batch=20):
    """Launches separate threads to import every message added by AddMailEntry.
    
    Args:
      user_name: The user account name to import messages to.
      threads_per_batch: Number of messages to import at a time.
    
    Returns:
      The number of email messages that were successfully migrated.
    
    Raises:
      Exception: An error occurred while importing mails.
    """
    num_entries = len(self.mail_entries)

    if not num_entries:
      return 0

    threads = []
    for mail_entry_properties in self.mail_entries:
      t = threading.Thread(name=mail_entry_properties.identifier,
                           target=self.ImportMail,
                           args=(user_name, mail_entry_properties.mail_message,
                                 mail_entry_properties.mail_item_properties,
                                 mail_entry_properties.mail_labels))
      threads.append(t)
    try:
      # Determine the number of batches needed with threads_per_batch in each
      batches = num_entries / threads_per_batch + (
          0 if num_entries % threads_per_batch == 0 else 1)
      batch_min = 0
      # Start the threads, one batch at a time
      for batch in range(batches):
        batch_max = ((batch + 1) * threads_per_batch
                     if (batch + 1) * threads_per_batch < num_entries
                     else num_entries)
        for i in range(batch_min, batch_max):
          threads[i].start()
          time.sleep(1)

        for i in range(batch_min, batch_max):
          threads[i].join()

        batch_min = batch_max

      self.mail_entries = []
    except Exception, e:
      raise Exception(e.args[0])
    else:
      return num_entries - self.exceptions
