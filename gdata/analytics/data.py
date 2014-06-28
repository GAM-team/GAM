#!/usr/bin/env python
#
# Copyright (C) 2009 Google Inc.
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


# This module is used for version 2 of the Google Data APIs.


"""Provides classes and constants for the XML in the Google Data namespace.

Documentation for the raw XML which these classes represent can be found here:
http://code.google.com/apis/gdata/docs/2.0/elements.html
"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import os
import atom.core
import atom.data


GDATA_TEMPLATE = '{http://schemas.google.com/g/2005}%s'
GD_TEMPLATE = GDATA_TEMPLATE
OPENSEARCH_TEMPLATE_V1 = '{http://a9.com/-/spec/opensearchrss/1.0/}%s'
OPENSEARCH_TEMPLATE_V2 = '{http://a9.com/-/spec/opensearch/1.1/}%s'
BATCH_TEMPLATE = '{http://schemas.google.com/gdata/batch}%s'


# Labels used in batch request entries to specify the desired CRUD operation.
BATCH_INSERT = 'insert'
BATCH_UPDATE = 'update'
BATCH_DELETE = 'delete'
BATCH_QUERY = 'query'

EVENT_LOCATION = 'http://schemas.google.com/g/2005#event'
ALTERNATE_LOCATION = 'http://schemas.google.com/g/2005#event.alternate'
PARKING_LOCATION = 'http://schemas.google.com/g/2005#event.parking'

CANCELED_EVENT = 'http://schemas.google.com/g/2005#event.canceled'
CONFIRMED_EVENT = 'http://schemas.google.com/g/2005#event.confirmed'
TENTATIVE_EVENT = 'http://schemas.google.com/g/2005#event.tentative'

CONFIDENTIAL_EVENT = 'http://schemas.google.com/g/2005#event.confidential'
DEFAULT_EVENT = 'http://schemas.google.com/g/2005#event.default'
PRIVATE_EVENT = 'http://schemas.google.com/g/2005#event.private'
PUBLIC_EVENT = 'http://schemas.google.com/g/2005#event.public'

OPAQUE_EVENT = 'http://schemas.google.com/g/2005#event.opaque'
TRANSPARENT_EVENT = 'http://schemas.google.com/g/2005#event.transparent'

CHAT_MESSAGE = 'http://schemas.google.com/g/2005#message.chat'
INBOX_MESSAGE = 'http://schemas.google.com/g/2005#message.inbox'
SENT_MESSAGE = 'http://schemas.google.com/g/2005#message.sent'
SPAM_MESSAGE = 'http://schemas.google.com/g/2005#message.spam'
STARRED_MESSAGE = 'http://schemas.google.com/g/2005#message.starred'
UNREAD_MESSAGE = 'http://schemas.google.com/g/2005#message.unread'

BCC_RECIPIENT = 'http://schemas.google.com/g/2005#message.bcc'
CC_RECIPIENT = 'http://schemas.google.com/g/2005#message.cc'
SENDER = 'http://schemas.google.com/g/2005#message.from'
REPLY_TO = 'http://schemas.google.com/g/2005#message.reply-to'
TO_RECIPIENT = 'http://schemas.google.com/g/2005#message.to'

ASSISTANT_REL = 'http://schemas.google.com/g/2005#assistant'
CALLBACK_REL = 'http://schemas.google.com/g/2005#callback'
CAR_REL = 'http://schemas.google.com/g/2005#car'
COMPANY_MAIN_REL = 'http://schemas.google.com/g/2005#company_main'
FAX_REL = 'http://schemas.google.com/g/2005#fax'
HOME_REL = 'http://schemas.google.com/g/2005#home'
HOME_FAX_REL = 'http://schemas.google.com/g/2005#home_fax'
ISDN_REL = 'http://schemas.google.com/g/2005#isdn'
MAIN_REL = 'http://schemas.google.com/g/2005#main'
MOBILE_REL = 'http://schemas.google.com/g/2005#mobile'
OTHER_REL = 'http://schemas.google.com/g/2005#other'
OTHER_FAX_REL = 'http://schemas.google.com/g/2005#other_fax'
PAGER_REL = 'http://schemas.google.com/g/2005#pager'
RADIO_REL = 'http://schemas.google.com/g/2005#radio'
TELEX_REL = 'http://schemas.google.com/g/2005#telex'
TTL_TDD_REL = 'http://schemas.google.com/g/2005#tty_tdd'
WORK_REL = 'http://schemas.google.com/g/2005#work'
WORK_FAX_REL = 'http://schemas.google.com/g/2005#work_fax'
WORK_MOBILE_REL = 'http://schemas.google.com/g/2005#work_mobile'
WORK_PAGER_REL = 'http://schemas.google.com/g/2005#work_pager'
NETMEETING_REL = 'http://schemas.google.com/g/2005#netmeeting'
OVERALL_REL = 'http://schemas.google.com/g/2005#overall'
PRICE_REL = 'http://schemas.google.com/g/2005#price'
QUALITY_REL = 'http://schemas.google.com/g/2005#quality'
EVENT_REL = 'http://schemas.google.com/g/2005#event'
EVENT_ALTERNATE_REL = 'http://schemas.google.com/g/2005#event.alternate'
EVENT_PARKING_REL = 'http://schemas.google.com/g/2005#event.parking'

AIM_PROTOCOL = 'http://schemas.google.com/g/2005#AIM'
MSN_PROTOCOL = 'http://schemas.google.com/g/2005#MSN'
YAHOO_MESSENGER_PROTOCOL = 'http://schemas.google.com/g/2005#YAHOO'
SKYPE_PROTOCOL = 'http://schemas.google.com/g/2005#SKYPE'
QQ_PROTOCOL = 'http://schemas.google.com/g/2005#QQ'
GOOGLE_TALK_PROTOCOL = 'http://schemas.google.com/g/2005#GOOGLE_TALK'
ICQ_PROTOCOL = 'http://schemas.google.com/g/2005#ICQ'
JABBER_PROTOCOL = 'http://schemas.google.com/g/2005#JABBER'

REGULAR_COMMENTS = 'http://schemas.google.com/g/2005#regular'
REVIEW_COMMENTS = 'http://schemas.google.com/g/2005#reviews'

MAIL_BOTH = 'http://schemas.google.com/g/2005#both'
MAIL_LETTERS = 'http://schemas.google.com/g/2005#letters'
MAIL_PARCELS = 'http://schemas.google.com/g/2005#parcels'
MAIL_NEITHER = 'http://schemas.google.com/g/2005#neither'

GENERAL_ADDRESS = 'http://schemas.google.com/g/2005#general'
LOCAL_ADDRESS = 'http://schemas.google.com/g/2005#local'

OPTIONAL_ATENDEE = 'http://schemas.google.com/g/2005#event.optional'
REQUIRED_ATENDEE = 'http://schemas.google.com/g/2005#event.required'

ATTENDEE_ACCEPTED = 'http://schemas.google.com/g/2005#event.accepted'
ATTENDEE_DECLINED = 'http://schemas.google.com/g/2005#event.declined'
ATTENDEE_INVITED = 'http://schemas.google.com/g/2005#event.invited'
ATTENDEE_TENTATIVE = 'http://schemas.google.com/g/2005#event.tentative'

FULL_PROJECTION = 'full'
VALUES_PROJECTION = 'values'
BASIC_PROJECTION = 'basic'

PRIVATE_VISIBILITY = 'private'
PUBLIC_VISIBILITY = 'public'

OPAQUE_TRANSPARENCY = 'http://schemas.google.com/g/2005#event.opaque'
TRANSPARENT_TRANSPARENCY = 'http://schemas.google.com/g/2005#event.transparent'

CONFIDENTIAL_EVENT_VISIBILITY = 'http://schemas.google.com/g/2005#event.confidential'
DEFAULT_EVENT_VISIBILITY = 'http://schemas.google.com/g/2005#event.default'
PRIVATE_EVENT_VISIBILITY = 'http://schemas.google.com/g/2005#event.private'
PUBLIC_EVENT_VISIBILITY = 'http://schemas.google.com/g/2005#event.public'

CANCELED_EVENT_STATUS = 'http://schemas.google.com/g/2005#event.canceled'
CONFIRMED_EVENT_STATUS = 'http://schemas.google.com/g/2005#event.confirmed'
TENTATIVE_EVENT_STATUS = 'http://schemas.google.com/g/2005#event.tentative'

ACL_REL = 'http://schemas.google.com/acl/2007#accessControlList'


class Error(Exception):
  pass


class MissingRequiredParameters(Error):
  pass


class LinkFinder(atom.data.LinkFinder):
  """Mixin used in Feed and Entry classes to simplify link lookups by type.

  Provides lookup methods for edit, edit-media, post, ACL and other special
  links which are common across Google Data APIs.
  """

  def find_html_link(self):
    """Finds the first link with rel of alternate and type of text/html."""
    for link in self.link:
      if link.rel == 'alternate' and link.type == 'text/html':
        return link.href
    return None

  FindHtmlLink = find_html_link

  def get_html_link(self):
    for a_link in self.link:
      if a_link.rel == 'alternate' and a_link.type == 'text/html':
        return a_link
    return None

  GetHtmlLink = get_html_link

  def find_post_link(self):
    """Get the URL to which new entries should be POSTed.

    The POST target URL is used to insert new entries.

    Returns:
      A str for the URL in the link with a rel matching the POST type.
    """
    return self.find_url('http://schemas.google.com/g/2005#post')

  FindPostLink = find_post_link

  def get_post_link(self):
    return self.get_link('http://schemas.google.com/g/2005#post')

  GetPostLink = get_post_link

  def find_acl_link(self):
    acl_link = self.get_acl_link()
    if acl_link:
      return acl_link.href

    return None

  FindAclLink = find_acl_link

  def get_acl_link(self):
    """Searches for a link or feed_link (if present) with the rel for ACL."""

    acl_link = self.get_link(ACL_REL)
    if acl_link:
      return acl_link
    elif hasattr(self, 'feed_link'):
      for a_feed_link in self.feed_link:
        if a_feed_link.rel == ACL_REL:
          return a_feed_link

    return None

  GetAclLink = get_acl_link

  def find_feed_link(self):
    return self.find_url('http://schemas.google.com/g/2005#feed')

  FindFeedLink = find_feed_link

  def get_feed_link(self):
    return self.get_link('http://schemas.google.com/g/2005#feed')

  GetFeedLink = get_feed_link

  def find_previous_link(self):
    return self.find_url('previous')

  FindPreviousLink = find_previous_link

  def get_previous_link(self):
    return self.get_link('previous')

  GetPreviousLink = get_previous_link


class TotalResults(atom.core.XmlElement):
  """opensearch:TotalResults for a GData feed."""
  _qname = (OPENSEARCH_TEMPLATE_V1 % 'totalResults',
            OPENSEARCH_TEMPLATE_V2 % 'totalResults')


class StartIndex(atom.core.XmlElement):
  """The opensearch:startIndex element in GData feed."""
  _qname = (OPENSEARCH_TEMPLATE_V1 % 'startIndex',
            OPENSEARCH_TEMPLATE_V2 % 'startIndex')


class ItemsPerPage(atom.core.XmlElement):
  """The opensearch:itemsPerPage element in GData feed."""
  _qname = (OPENSEARCH_TEMPLATE_V1 % 'itemsPerPage',
            OPENSEARCH_TEMPLATE_V2 % 'itemsPerPage')


class ExtendedProperty(atom.core.XmlElement):
  """The Google Data extendedProperty element.

  Used to store arbitrary key-value information specific to your
  application. The value can either be a text string stored as an XML
  attribute (.value), or an XML node (XmlBlob) as a child element.

  This element is used in the Google Calendar data API and the Google
  Contacts data API.
  """
  _qname = GDATA_TEMPLATE % 'extendedProperty'
  name = 'name'
  value = 'value'

  def get_xml_blob(self):
    """Returns the XML blob as an atom.core.XmlElement.

    Returns:
      An XmlElement representing the blob's XML, or None if no
      blob was set.
    """
    if self._other_elements:
      return self._other_elements[0]
    else:
      return None

  GetXmlBlob = get_xml_blob

  def set_xml_blob(self, blob):
    """Sets the contents of the extendedProperty to XML as a child node.

    Since the extendedProperty is only allowed one child element as an XML
    blob, setting the XML blob will erase any preexisting member elements
    in this object.

    Args:
      blob: str  or atom.core.XmlElement representing the XML blob stored in
            the extendedProperty.
    """
    # Erase any existing extension_elements, clears the child nodes from the
    # extendedProperty.
    if isinstance(blob, atom.core.XmlElement):
      self._other_elements = [blob]
    else:
      self._other_elements = [atom.core.parse(str(blob))]

  SetXmlBlob = set_xml_blob


class GDEntry(atom.data.Entry, LinkFinder):
  """Extends Atom Entry to provide data processing"""
  etag = '{http://schemas.google.com/g/2005}etag'

  def get_id(self):
    if self.id is not None and self.id.text is not None:
      return self.id.text.strip()
    return None

  GetId = get_id

  def is_media(self):
    if self.find_edit_media_link():
      return True
    return False

  IsMedia = is_media

  def find_media_link(self):
    """Returns the URL to the media content, if the entry is a media entry.
    Otherwise returns None.
    """
    if self.is_media():
      return self.content.src
    return None

  FindMediaLink = find_media_link


class GDFeed(atom.data.Feed, LinkFinder):
  """A Feed from a GData service."""
  etag = '{http://schemas.google.com/g/2005}etag'
  total_results = TotalResults
  start_index = StartIndex
  items_per_page = ItemsPerPage
  entry = [GDEntry]

  def get_id(self):
    if self.id is not None and self.id.text is not None:
      return self.id.text.strip()
    return None

  GetId = get_id

  def get_generator(self):
    if self.generator and self.generator.text:
      return self.generator.text.strip()
    return None


class BatchId(atom.core.XmlElement):
  """Identifies a single operation in a batch request."""
  _qname = BATCH_TEMPLATE % 'id'


class BatchOperation(atom.core.XmlElement):
  """The CRUD operation which this batch entry represents."""
  _qname = BATCH_TEMPLATE % 'operation'
  type = 'type'


class BatchStatus(atom.core.XmlElement):
  """The batch:status element present in a batch response entry.

  A status element contains the code (HTTP response code) and
  reason as elements. In a single request these fields would
  be part of the HTTP response, but in a batch request each
  Entry operation has a corresponding Entry in the response
  feed which includes status information.

  See http://code.google.com/apis/gdata/batch.html#Handling_Errors
  """
  _qname = BATCH_TEMPLATE % 'status'
  code = 'code'
  reason = 'reason'
  content_type = 'content-type'


class BatchEntry(GDEntry):
  """An atom:entry for use in batch requests.

  The BatchEntry contains additional members to specify the operation to be
  performed on this entry and a batch ID so that the server can reference
  individual operations in the response feed. For more information, see:
  http://code.google.com/apis/gdata/batch.html
  """
  batch_operation = BatchOperation
  batch_id = BatchId
  batch_status = BatchStatus


class BatchInterrupted(atom.core.XmlElement):
  """The batch:interrupted element sent if batch request was interrupted.

  Only appears in a feed if some of the batch entries could not be processed.
  See: http://code.google.com/apis/gdata/batch.html#Handling_Errors
  """
  _qname = BATCH_TEMPLATE % 'interrupted'
  reason = 'reason'
  success = 'success'
  failures = 'failures'
  parsed = 'parsed'


class BatchFeed(GDFeed):
  """A feed containing a list of batch request entries."""
  interrupted = BatchInterrupted
  entry = [BatchEntry]

  def add_batch_entry(self, entry=None, id_url_string=None,
      batch_id_string=None, operation_string=None):
    """Logic for populating members of a BatchEntry and adding to the feed.

    If the entry is not a BatchEntry, it is converted to a BatchEntry so
    that the batch specific members will be present.

    The id_url_string can be used in place of an entry if the batch operation
    applies to a URL. For example query and delete operations require just
    the URL of an entry, no body is sent in the HTTP request. If an
    id_url_string is sent instead of an entry, a BatchEntry is created and
    added to the feed.

    This method also assigns the desired batch id to the entry so that it
    can be referenced in the server's response. If the batch_id_string is
    None, this method will assign a batch_id to be the index at which this
    entry will be in the feed's entry list.

    Args:
      entry: BatchEntry, atom.data.Entry, or another Entry flavor (optional)
          The entry which will be sent to the server as part of the batch
          request. The item must have a valid atom id so that the server
          knows which entry this request references.
      id_url_string: str (optional) The URL of the entry to be acted on. You
          can find this URL in the text member of the atom id for an entry.
          If an entry is not sent, this id will be used to construct a new
          BatchEntry which will be added to the request feed.
      batch_id_string: str (optional) The batch ID to be used to reference
          this batch operation in the results feed. If this parameter is None,
          the current length of the feed's entry array will be used as a
          count. Note that batch_ids should either always be specified or
          never, mixing could potentially result in duplicate batch ids.
      operation_string: str (optional) The desired batch operation which will
          set the batch_operation.type member of the entry. Options are
          'insert', 'update', 'delete', and 'query'

    Raises:
      MissingRequiredParameters: Raised if neither an id_ url_string nor an
          entry are provided in the request.

    Returns:
      The added entry.
    """
    if entry is None and id_url_string is None:
      raise MissingRequiredParameters('supply either an entry or URL string')
    if entry is None and id_url_string is not None:
      entry = BatchEntry(id=atom.data.Id(text=id_url_string))
    if batch_id_string is not None:
      entry.batch_id = BatchId(text=batch_id_string)
    elif entry.batch_id is None or entry.batch_id.text is None:
      entry.batch_id = BatchId(text=str(len(self.entry)))
    if operation_string is not None:
      entry.batch_operation = BatchOperation(type=operation_string)
    self.entry.append(entry)
    return entry

  AddBatchEntry = add_batch_entry

  def add_insert(self, entry, batch_id_string=None):
    """Add an insert request to the operations in this batch request feed.

    If the entry doesn't yet have an operation or a batch id, these will
    be set to the insert operation and a batch_id specified as a parameter.

    Args:
      entry: BatchEntry The entry which will be sent in the batch feed as an
          insert request.
      batch_id_string: str (optional) The batch ID to be used to reference
          this batch operation in the results feed. If this parameter is None,
          the current length of the feed's entry array will be used as a
          count. Note that batch_ids should either always be specified or
          never, mixing could potentially result in duplicate batch ids.
    """
    self.add_batch_entry(entry=entry, batch_id_string=batch_id_string,
        operation_string=BATCH_INSERT)

  AddInsert = add_insert

  def add_update(self, entry, batch_id_string=None):
    """Add an update request to the list of batch operations in this feed.

    Sets the operation type of the entry to insert if it is not already set
    and assigns the desired batch id to the entry so that it can be
    referenced in the server's response.

    Args:
      entry: BatchEntry The entry which will be sent to the server as an
          update (HTTP PUT) request. The item must have a valid atom id
          so that the server knows which entry to replace.
      batch_id_string: str (optional) The batch ID to be used to reference
          this batch operation in the results feed. If this parameter is None,
          the current length of the feed's entry array will be used as a
          count. See also comments for AddInsert.
    """
    self.add_batch_entry(entry=entry, batch_id_string=batch_id_string,
        operation_string=BATCH_UPDATE)

  AddUpdate = add_update

  def add_delete(self, url_string=None, entry=None, batch_id_string=None):
    """Adds a delete request to the batch request feed.

    This method takes either the url_string which is the atom id of the item
    to be deleted, or the entry itself. The atom id of the entry must be
    present so that the server knows which entry should be deleted.

    Args:
      url_string: str (optional) The URL of the entry to be deleted. You can
         find this URL in the text member of the atom id for an entry.
      entry: BatchEntry (optional) The entry to be deleted.
      batch_id_string: str (optional)

    Raises:
      MissingRequiredParameters: Raised if neither a url_string nor an entry
          are provided in the request.
    """
    self.add_batch_entry(entry=entry, id_url_string=url_string,
        batch_id_string=batch_id_string, operation_string=BATCH_DELETE)

  AddDelete = add_delete

  def add_query(self, url_string=None, entry=None, batch_id_string=None):
    """Adds a query request to the batch request feed.

    This method takes either the url_string which is the query URL
    whose results will be added to the result feed. The query URL will
    be encapsulated in a BatchEntry, and you may pass in the BatchEntry
    with a query URL instead of sending a url_string.

    Args:
      url_string: str (optional)
      entry: BatchEntry (optional)
      batch_id_string: str (optional)

    Raises:
      MissingRequiredParameters
    """
    self.add_batch_entry(entry=entry, id_url_string=url_string,
        batch_id_string=batch_id_string, operation_string=BATCH_QUERY)

  AddQuery = add_query

  def find_batch_link(self):
    return self.find_url('http://schemas.google.com/g/2005#batch')

  FindBatchLink = find_batch_link


class EntryLink(atom.core.XmlElement):
  """The gd:entryLink element.

  Represents a logically nested entry. For example, a <gd:who>
  representing a contact might have a nested entry from a contact feed.
  """
  _qname = GDATA_TEMPLATE % 'entryLink'
  entry = GDEntry
  rel = 'rel'
  read_only = 'readOnly'
  href = 'href'


class FeedLink(atom.core.XmlElement):
  """The gd:feedLink element.

  Represents a logically nested feed. For example, a calendar feed might
  have a nested feed representing all comments on entries.
  """
  _qname = GDATA_TEMPLATE % 'feedLink'
  feed = GDFeed
  rel = 'rel'
  read_only = 'readOnly'
  count_hint = 'countHint'
  href = 'href'


class AdditionalName(atom.core.XmlElement):
  """The gd:additionalName element.

  Specifies additional (eg. middle) name of the person.
  Contains an attribute for the phonetic representaton of the name.
  """
  _qname = GDATA_TEMPLATE % 'additionalName'
  yomi = 'yomi'


class Comments(atom.core.XmlElement):
  """The gd:comments element.

  Contains a comments feed for the enclosing entry (such as a calendar event).
  """
  _qname = GDATA_TEMPLATE % 'comments'
  rel = 'rel'
  feed_link = FeedLink


class Country(atom.core.XmlElement):
  """The gd:country element.

  Country name along with optional country code. The country code is
  given in accordance with ISO 3166-1 alpha-2:
  http://www.iso.org/iso/iso-3166-1_decoding_table
  """
  _qname = GDATA_TEMPLATE % 'country'
  code = 'code'


class EmailImParent(atom.core.XmlElement):
  address = 'address'
  label = 'label'
  rel = 'rel'
  primary = 'primary'


class Email(EmailImParent):
  """The gd:email element.

  An email address associated with the containing entity (which is
  usually an entity representing a person or a location).
  """
  _qname = GDATA_TEMPLATE % 'email'
  display_name = 'displayName'


class FamilyName(atom.core.XmlElement):
  """The gd:familyName element.

  Specifies family name of the person, eg. "Smith".
  """
  _qname = GDATA_TEMPLATE % 'familyName'
  yomi = 'yomi'


class Im(EmailImParent):
  """The gd:im element.

  An instant messaging address associated with the containing entity.
  """
  _qname = GDATA_TEMPLATE % 'im'
  protocol = 'protocol'


class GivenName(atom.core.XmlElement):
  """The gd:givenName element.

  Specifies given name of the person, eg. "John".
  """
  _qname = GDATA_TEMPLATE % 'givenName'
  yomi = 'yomi'


class NamePrefix(atom.core.XmlElement):
  """The gd:namePrefix element.

  Honorific prefix, eg. 'Mr' or 'Mrs'.
  """
  _qname = GDATA_TEMPLATE % 'namePrefix'


class NameSuffix(atom.core.XmlElement):
  """The gd:nameSuffix element.

  Honorific suffix, eg. 'san' or 'III'.
  """
  _qname = GDATA_TEMPLATE % 'nameSuffix'


class FullName(atom.core.XmlElement):
  """The gd:fullName element.

  Unstructured representation of the name.
  """
  _qname = GDATA_TEMPLATE % 'fullName'


class Name(atom.core.XmlElement):
  """The gd:name element.

  Allows storing person's name in a structured way. Consists of
  given name, additional name, family name, prefix, suffix and full name.
  """
  _qname = GDATA_TEMPLATE % 'name'
  given_name = GivenName
  additional_name = AdditionalName
  family_name = FamilyName
  name_prefix = NamePrefix
  name_suffix = NameSuffix
  full_name = FullName


class OrgDepartment(atom.core.XmlElement):
  """The gd:orgDepartment element.

  Describes a department within an organization. Must appear within a
  gd:organization element.
  """
  _qname = GDATA_TEMPLATE % 'orgDepartment'


class OrgJobDescription(atom.core.XmlElement):
  """The gd:orgJobDescription element.

  Describes a job within an organization. Must appear within a
  gd:organization element.
  """
  _qname = GDATA_TEMPLATE % 'orgJobDescription'


class OrgName(atom.core.XmlElement):
  """The gd:orgName element.

  The name of the organization. Must appear within a gd:organization
  element.

  Contains a Yomigana attribute (Japanese reading aid) for the
  organization name.
  """
  _qname = GDATA_TEMPLATE % 'orgName'
  yomi = 'yomi'


class OrgSymbol(atom.core.XmlElement):
  """The gd:orgSymbol element.

  Provides a symbol of an organization. Must appear within a
  gd:organization element.
  """
  _qname = GDATA_TEMPLATE % 'orgSymbol'


class OrgTitle(atom.core.XmlElement):
  """The gd:orgTitle element.

  The title of a person within an organization. Must appear within a
  gd:organization element.
  """
  _qname = GDATA_TEMPLATE % 'orgTitle'


class Organization(atom.core.XmlElement):
  """The gd:organization element.

  An organization, typically associated with a contact.
  """
  _qname = GDATA_TEMPLATE % 'organization'
  label = 'label'
  primary = 'primary'
  rel = 'rel'
  department = OrgDepartment
  job_description = OrgJobDescription
  name = OrgName
  symbol = OrgSymbol
  title = OrgTitle


class When(atom.core.XmlElement):
  """The gd:when element.

  Represents a period of time or an instant.
  """
  _qname = GDATA_TEMPLATE % 'when'
  end = 'endTime'
  start = 'startTime'
  value = 'valueString'


class OriginalEvent(atom.core.XmlElement):
  """The gd:originalEvent element.

  Equivalent to the Recurrence ID property specified in section 4.8.4.4
  of RFC 2445. Appears in every instance of a recurring event, to identify
  the original event.

  Contains a <gd:when> element specifying the original start time of the
  instance that has become an exception.
  """
  _qname = GDATA_TEMPLATE % 'originalEvent'
  id = 'id'
  href = 'href'
  when = When


class PhoneNumber(atom.core.XmlElement):
  """The gd:phoneNumber element.

  A phone number associated with the containing entity (which is usually
  an entity representing a person or a location).
  """
  _qname = GDATA_TEMPLATE % 'phoneNumber'
  label = 'label'
  rel = 'rel'
  uri = 'uri'
  primary = 'primary'


class PostalAddress(atom.core.XmlElement):
  """The gd:postalAddress element."""
  _qname = GDATA_TEMPLATE % 'postalAddress'
  label = 'label'
  rel = 'rel'
  uri = 'uri'
  primary = 'primary'


class Rating(atom.core.XmlElement):
  """The gd:rating element.

  Represents a numeric rating of the enclosing entity, such as a
  comment. Each rating supplies its own scale, although it may be
  normalized by a service; for example, some services might convert all
  ratings to a scale from 1 to 5.
  """
  _qname = GDATA_TEMPLATE % 'rating'
  average = 'average'
  max = 'max'
  min = 'min'
  num_raters = 'numRaters'
  rel = 'rel'
  value = 'value'


class Recurrence(atom.core.XmlElement):
  """The gd:recurrence element.

  Represents the dates and times when a recurring event takes place.

  The string that defines the recurrence consists of a set of properties,
  each of which is defined in the iCalendar standard (RFC 2445).

  Specifically, the string usually begins with a DTSTART property that
  indicates the starting time of the first instance of the event, and
  often a DTEND property or a DURATION property to indicate when the
  first instance ends. Next come RRULE, RDATE, EXRULE, and/or EXDATE
  properties, which collectively define a recurring event and its
  exceptions (but see below). (See section 4.8.5 of RFC 2445 for more
  information about these recurrence component properties.) Last comes a
  VTIMEZONE component, providing detailed timezone rules for any timezone
  ID mentioned in the preceding properties.

  Google services like Google Calendar don't generally generate EXRULE
  and EXDATE properties to represent exceptions to recurring events;
  instead, they generate <gd:recurrenceException> elements. However,
  Google services may include EXRULE and/or EXDATE properties anyway;
  for example, users can import events and exceptions into Calendar, and
  if those imported events contain EXRULE or EXDATE properties, then
  Calendar will provide those properties when it sends a <gd:recurrence>
  element.

  Note the the use of <gd:recurrenceException> means that you can't be
  sure just from examining a <gd:recurrence> element whether there are
  any exceptions to the recurrence description. To ensure that you find
  all exceptions, look for <gd:recurrenceException> elements in the feed,
  and use their <gd:originalEvent> elements to match them up with
  <gd:recurrence> elements.
  """
  _qname = GDATA_TEMPLATE % 'recurrence'


class RecurrenceException(atom.core.XmlElement):
  """The gd:recurrenceException element.

  Represents an event that's an exception to a recurring event-that is,
  an instance of a recurring event in which one or more aspects of the
  recurring event (such as attendance list, time, or location) have been
  changed.

  Contains a <gd:originalEvent> element that specifies the original
  recurring event that this event is an exception to.

  When you change an instance of a recurring event, that instance becomes
  an exception. Depending on what change you made to it, the exception
  behaves in either of two different ways when the original recurring
  event is changed:

  - If you add, change, or remove comments, attendees, or attendee
    responses, then the exception remains tied to the original event, and
    changes to the original event also change the exception.
  - If you make any other changes to the exception (such as changing the
    time or location) then the instance becomes "specialized," which means
    that it's no longer as tightly tied to the original event. If you
    change the original event, specialized exceptions don't change. But
    see below.

  For example, say you have a meeting every Tuesday and Thursday at
  2:00 p.m. If you change the attendance list for this Thursday's meeting
  (but not for the regularly scheduled meeting), then it becomes an
  exception. If you change the time for this Thursday's meeting (but not
  for the regularly scheduled meeting), then it becomes specialized.

  Regardless of whether an exception is specialized or not, if you do
  something that deletes the instance that the exception was derived from,
  then the exception is deleted. Note that changing the day or time of a
  recurring event deletes all instances, and creates new ones.

  For example, after you've specialized this Thursday's meeting, say you
  change the recurring meeting to happen on Monday, Wednesday, and Friday.
  That change deletes all of the recurring instances of the
  Tuesday/Thursday meeting, including the specialized one.

  If a particular instance of a recurring event is deleted, then that
  instance appears as a <gd:recurrenceException> containing a
  <gd:entryLink> that has its <gd:eventStatus> set to
  "http://schemas.google.com/g/2005#event.canceled". (For more
  information about canceled events, see RFC 2445.)
  """
  _qname = GDATA_TEMPLATE % 'recurrenceException'
  specialized = 'specialized'
  entry_link = EntryLink
  original_event = OriginalEvent


class Reminder(atom.core.XmlElement):
  """The gd:reminder element.

  A time interval, indicating how long before the containing entity's start
  time or due time attribute a reminder should be issued. Alternatively,
  may specify an absolute time at which a reminder should be issued. Also
  specifies a notification method, indicating what medium the system
  should use to remind the user.
  """
  _qname = GDATA_TEMPLATE % 'reminder'
  absolute_time = 'absoluteTime'
  method = 'method'
  days = 'days'
  hours = 'hours'
  minutes = 'minutes'


class Transparency(atom.core.XmlElement):
  """The gd:transparency element:

  Extensible enum corresponding to the TRANSP property defined in RFC 244.
  """
  _qname = GDATA_TEMPLATE % 'transparency'
  value = 'value'


class Agent(atom.core.XmlElement):
  """The gd:agent element.

  The agent who actually receives the mail. Used in work addresses.
  Also for 'in care of' or 'c/o'.
  """
  _qname = GDATA_TEMPLATE % 'agent'


class HouseName(atom.core.XmlElement):
  """The gd:housename element.

  Used in places where houses or buildings have names (and not
  necessarily numbers), eg. "The Pillars".
  """
  _qname = GDATA_TEMPLATE % 'housename'


class Street(atom.core.XmlElement):
  """The gd:street element.

  Can be street, avenue, road, etc. This element also includes the
  house number and room/apartment/flat/floor number.
  """
  _qname = GDATA_TEMPLATE % 'street'


class PoBox(atom.core.XmlElement):
  """The gd:pobox element.

  Covers actual P.O. boxes, drawers, locked bags, etc. This is usually
  but not always mutually exclusive with street.
  """
  _qname = GDATA_TEMPLATE % 'pobox'


class Neighborhood(atom.core.XmlElement):
  """The gd:neighborhood element.

  This is used to disambiguate a street address when a city contains more
  than one street with the same name, or to specify a small place whose
  mail is routed through a larger postal town. In China it could be a
  county or a minor city.
  """
  _qname = GDATA_TEMPLATE % 'neighborhood'


class City(atom.core.XmlElement):
  """The gd:city element.

  Can be city, village, town, borough, etc. This is the postal town and
  not necessarily the place of residence or place of business.
  """
  _qname = GDATA_TEMPLATE % 'city'


class Subregion(atom.core.XmlElement):
  """The gd:subregion element.

  Handles administrative districts such as U.S. or U.K. counties that are
  not used for mail addressing purposes. Subregion is not intended for
  delivery addresses.
  """
  _qname = GDATA_TEMPLATE % 'subregion'


class Region(atom.core.XmlElement):
  """The gd:region element.

  A state, province, county (in Ireland), Land (in Germany),
  departement (in France), etc.
  """
  _qname = GDATA_TEMPLATE % 'region'


class Postcode(atom.core.XmlElement):
  """The gd:postcode element.

  Postal code. Usually country-wide, but sometimes specific to the
  city (e.g. "2" in "Dublin 2, Ireland" addresses).
  """
  _qname = GDATA_TEMPLATE % 'postcode'


class Country(atom.core.XmlElement):
  """The gd:country element.

  The name or code of the country.
  """
  _qname = GDATA_TEMPLATE % 'country'


class FormattedAddress(atom.core.XmlElement):
  """The gd:formattedAddress element.

  The full, unstructured postal address.
  """
  _qname = GDATA_TEMPLATE % 'formattedAddress'


class StructuredPostalAddress(atom.core.XmlElement):
  """The gd:structuredPostalAddress element.

  Postal address split into components. It allows to store the address
  in locale independent format. The fields can be interpreted and used
  to generate formatted, locale dependent address. The following elements
  reperesent parts of the address: agent, house name, street, P.O. box,
  neighborhood, city, subregion, region, postal code, country. The
  subregion element is not used for postal addresses, it is provided for
  extended uses of addresses only. In order to store postal address in an
  unstructured form formatted address field is provided.
  """
  _qname = GDATA_TEMPLATE % 'structuredPostalAddress'
  rel = 'rel'
  mail_class = 'mailClass'
  usage = 'usage'
  label = 'label'
  primary = 'primary'
  agent = Agent
  house_name = HouseName
  street = Street
  po_box = PoBox
  neighborhood = Neighborhood
  city = City
  subregion = Subregion
  region = Region
  postcode = Postcode
  country = Country
  formatted_address = FormattedAddress


class Where(atom.core.XmlElement):
  """The gd:where element.

  A place (such as an event location) associated with the containing
  entity. The type of the association is determined by the rel attribute;
  the details of the location are contained in an embedded or linked-to
  Contact entry.

  A <gd:where> element is more general than a <gd:geoPt> element. The
  former identifies a place using a text description and/or a Contact
  entry, while the latter identifies a place using a specific geographic
  location.
  """
  _qname = GDATA_TEMPLATE % 'where'
  label = 'label'
  rel = 'rel'
  value = 'valueString'
  entry_link = EntryLink


class AttendeeType(atom.core.XmlElement):
  """The gd:attendeeType element."""
  _qname = GDATA_TEMPLATE % 'attendeeType'
  value = 'value'


class AttendeeStatus(atom.core.XmlElement):
  """The gd:attendeeStatus element."""
  _qname = GDATA_TEMPLATE % 'attendeeStatus'
  value = 'value'


class EventStatus(atom.core.XmlElement):
  """The gd:eventStatus element."""
  _qname = GDATA_TEMPLATE % 'eventStatus'
  value = 'value'


class Visibility(atom.core.XmlElement):
  """The gd:visibility element."""
  _qname = GDATA_TEMPLATE % 'visibility'
  value = 'value'


class Who(atom.core.XmlElement):
  """The gd:who element.

  A person associated with the containing entity. The type of the
  association is determined by the rel attribute; the details about the
  person are contained in an embedded or linked-to Contact entry.

  The <gd:who> element can be used to specify email senders and
  recipients, calendar event organizers, and so on.
  """
  _qname = GDATA_TEMPLATE % 'who'
  email = 'email'
  rel = 'rel'
  value = 'valueString'
  attendee_status = AttendeeStatus
  attendee_type = AttendeeType
  entry_link = EntryLink


class Deleted(atom.core.XmlElement):
  """gd:deleted when present, indicates the containing entry is deleted."""
  _qname = GD_TEMPLATE % 'deleted'


class Money(atom.core.XmlElement):
  """Describes money"""
  _qname = GD_TEMPLATE % 'money'
  amount = 'amount'
  currency_code = 'currencyCode'


class MediaSource(object):
  """GData Entries can refer to media sources, so this class provides a
  place to store references to these objects along with some metadata.
  """

  def __init__(self, file_handle=None, content_type=None, content_length=None,
      file_path=None, file_name=None):
    """Creates an object of type MediaSource.

    Args:
      file_handle: A file handle pointing to the file to be encapsulated in the
                   MediaSource.
      content_type: string The MIME type of the file. Required if a file_handle
                    is given.
      content_length: int The size of the file. Required if a file_handle is
                      given.
      file_path: string (optional) A full path name to the file. Used in
                    place of a file_handle.
      file_name: string The name of the file without any path information.
                 Required if a file_handle is given.
    """
    self.file_handle = file_handle
    self.content_type = content_type
    self.content_length = content_length
    self.file_name = file_name

    if (file_handle is None and content_type is not None and
        file_path is not None):
      self.set_file_handle(file_path, content_type)

  def set_file_handle(self, file_name, content_type):
    """A helper function which can create a file handle from a given filename
    and set the content type and length all at once.

    Args:
      file_name: string The path and file name to the file containing the media
      content_type: string A MIME type representing the type of the media
    """

    self.file_handle = open(file_name, 'rb')
    self.content_type = content_type
    self.content_length = os.path.getsize(file_name)
    self.file_name = os.path.basename(file_name)

  SetFileHandle = set_file_handle

  def modify_request(self, http_request):
    http_request.add_body_part(self.file_handle, self.content_type,
                               self.content_length)
    return http_request

  ModifyRequest = modify_request
