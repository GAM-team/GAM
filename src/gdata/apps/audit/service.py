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

"""Allow Google Apps domain administrators to audit user data.

  AuditService: Set auditing."""

__author__ = 'jlee@pbu.edu'

from base64 import b64encode

import gdata.apps
import gdata.apps.service
import gdata.service

class AuditService(gdata.apps.service.PropertyService):
  """Client for the Google Apps Audit service."""

  def _serviceUrl(self, setting_id, domain=None, user=None):
    if domain is None:
      domain = self.domain
    if user is None:
      return '/a/feeds/compliance/audit/%s/%s' % (setting_id, domain)
    else:
      return '/a/feeds/compliance/audit/%s/%s/%s' % (setting_id, domain, user)

  def updatePGPKey(self, pgpkey):
    """Updates Public PGP Key Google uses to encrypt audit data

    Args:
      pgpkey: string, ASCII text of PGP Public Key to be used

    Returns:
      A dict containing the result of the POST operation."""

    uri = self._serviceUrl('publickey')
    b64pgpkey = b64encode(pgpkey)
    properties = {}
    properties['publicKey'] = b64pgpkey
    return self._PostProperties(uri, properties)

  def createEmailMonitor(self, source_user, destination_user, end_date, 
                         begin_date=None, incoming_headers_only=False, 
                         outgoing_headers_only=False, drafts=False, 
                         drafts_headers_only=False, chats=False, 
                         chats_headers_only=False):
    """Creates a email monitor, forwarding the source_users emails/chats

    Args:
      source_user: string, the user whose email will be audited
      destination_user: string, the user to receive the audited email
      end_date: string, the date the audit will end in
                "yyyy-MM-dd HH:mm" format, required
      begin_date: string, the date the audit will start in 
                  "yyyy-MM-dd HH:mm" format, leave blank to use current time
      incoming_headers_only: boolean, whether to audit only the headers of
                             mail delivered to source user
      outgoing_headers_only: boolean, whether to audit only the headers of
                             mail sent from the source user
      drafts: boolean, whether to audit draft messages of the source user
      drafts_headers_only: boolean, whether to audit only the headers of
                           mail drafts saved by the user
      chats: boolean, whether to audit archived chats of the source user
      chats_headers_only: boolean, whether to audit only the headers of
                          archived chats of the source user

    Returns:
      A dict containing the result of the POST operation."""

    uri = self._serviceUrl('mail/monitor', user=source_user)
    properties = {}
    properties['destUserName'] = destination_user
    if begin_date is not None:
      properties['beginDate'] = begin_date
    properties['endDate'] = end_date
    if incoming_headers_only:
      properties['incomingEmailMonitorLevel'] = 'HEADER_ONLY'
    else:
      properties['incomingEmailMonitorLevel'] = 'FULL_MESSAGE'
    if outgoing_headers_only:
      properties['outgoingEmailMonitorLevel'] = 'HEADER_ONLY'
    else:
      properties['outgoingEmailMonitorLevel'] = 'FULL_MESSAGE'
    if drafts:
      if drafts_headers_only:
        properties['draftMonitorLevel'] = 'HEADER_ONLY'
      else:
        properties['draftMonitorLevel'] = 'FULL_MESSAGE'
    if chats:
      if chats_headers_only:
        properties['chatMonitorLevel'] = 'HEADER_ONLY'
      else:
        properties['chatMonitorLevel'] = 'FULL_MESSAGE'
    return self._PostProperties(uri, properties)

  def getEmailMonitors(self, user):
    """"Gets the email monitors for the given user

    Args:
      user: string, the user to retrieve email monitors for

    Returns:
      list results of the POST operation

    """
    uri = self._serviceUrl('mail/monitor', user=user)
    return self._GetPropertiesList(uri)

  def deleteEmailMonitor(self, source_user, destination_user):
    """Deletes the email monitor for the given user

    Args:
      source_user: string, the user who is being monitored
      destination_user: string, theuser who recieves the monitored emails

    Returns:
      Nothing
    """

    uri = self._serviceUrl('mail/monitor', user=source_user+'/'+destination_user)
    try:
      return self._DeleteProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])

  def createAccountInformationRequest(self, user):
    """Creates a request for account auditing details

    Args:
      user: string, the user to request account information for

    Returns:
      A dict containing the result of the post operation."""

    uri = self._serviceUrl('account', user=user)
    properties = {}
    #XML Body is left empty
    try:
      return self._PostProperties(uri, properties)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])

  def getAccountInformationRequestStatus(self, user, request_id):
    """Gets the status of an account auditing request

    Args:
      user: string, the user whose account auditing details were requested
      request_id: string, the request_id

    Returns:
      A dict containing the result of the get operation."""

    uri = self._serviceUrl('account', user=user+'/'+request_id)
    try:
      return self._GetProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])

  def getAllAccountInformationRequestsStatus(self):
    """Gets the status of all account auditing requests for the domain

    Args:
      None

    Returns:
      list results of the POST operation
    """

    uri = self._serviceUrl('account')
    return self._GetPropertiesList(uri)


  def deleteAccountInformationRequest(self, user, request_id):
    """Deletes the request for account auditing information

   Args:
     user: string, the user whose account auditing details were requested
     request_id: string, the request_id

   Returns:
     Nothing
   """

    uri = self._serviceUrl('account', user=user+'/'+request_id)
    try:
      return self._DeleteProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])

  def createMailboxExportRequest(self, user, begin_date=None, end_date=None, include_deleted=False, search_query=None, headers_only=False):
    """Creates a mailbox export request

    Args:
      user: string, the user whose mailbox export is being requested
      begin_date: string, date of earliest emails to export, optional, defaults to date of account creation
                  format is 'yyyy-MM-dd HH:mm'
      end_date: string, date of latest emails to export, optional, defaults to current date
                format is 'yyyy-MM-dd HH:mm'
      include_deleted: boolean, whether to include deleted emails in export, mutually exclusive with search_query
      search_query: string, gmail style search query, matched emails will be exported, mutually exclusive with include_deleted

    Returns:
      A dict containing the result of the post operation."""

    uri = self._serviceUrl('mail/export', user=user)
    properties = {}
    if begin_date is not None:
      properties['beginDate'] = begin_date
    if end_date is not None:
      properties['endDate'] = end_date
    if include_deleted is not None:
      properties['includeDeleted'] = gdata.apps.service._bool2str(include_deleted)
    if search_query is not None:
      properties['searchQuery'] = search_query
    if headers_only is True:
      properties['packageContent'] = 'HEADER_ONLY'
    else:
      properties['packageContent'] = 'FULL_MESSAGE'
    return self._PostProperties(uri, properties)

  def getMailboxExportRequestStatus(self, user, request_id):
    """Gets the status of an mailbox export request

    Args:
      user: string, the user whose mailbox were requested
      request_id: string, the request_id

    Returns:
      A dict containing the result of the get operation."""

    uri = self._serviceUrl('mail/export', user=user+'/'+request_id)
    try:
      return self._GetProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])

  def getAllMailboxExportRequestsStatus(self):
    """Gets the status of all mailbox export requests for the domain

    Args:
      None

    Returns:
      list results of the POST operation
    """

    uri = self._serviceUrl('mail/export')
    return self._GetPropertiesList(uri)


  def deleteMailboxExportRequest(self, user, request_id):
    """Deletes the request for mailbox export

   Args:
     user: string, the user whose mailbox were requested
     request_id: string, the request_id

   Returns:
     Nothing
   """

    uri = self._serviceUrl('mail/export', user=user+'/'+request_id)
    try:
      return self._DeleteProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])
