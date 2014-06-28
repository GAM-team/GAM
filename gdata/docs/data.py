#!/usr/bin/python
#
# Copyright 2009 Google Inc. All Rights Reserved.
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

"""Data model classes for parsing and generating XML for the DocList Data API"""

__author__ = 'e.bidelman (Eric Bidelman)'


import re
import atom.core
import atom.data
import gdata.acl.data
import gdata.data

DOCUMENTS_NS = 'http://schemas.google.com/docs/2007'
DOCUMENTS_TEMPLATE = '{http://schemas.google.com/docs/2007}%s'
ACL_FEEDLINK_REL = 'http://schemas.google.com/acl/2007#accessControlList'
REVISION_FEEDLINK_REL = DOCUMENTS_NS + '/revisions'

# XML Namespaces used in Google Documents entities.
DATA_KIND_SCHEME = 'http://schemas.google.com/g/2005#kind'
DOCUMENT_LABEL = 'document'
SPREADSHEET_LABEL = 'spreadsheet'
PRESENTATION_LABEL = 'presentation'
FOLDER_LABEL = 'folder'
PDF_LABEL = 'pdf'

LABEL_SCHEME = 'http://schemas.google.com/g/2005/labels'
STARRED_LABEL_TERM = LABEL_SCHEME + '#starred'
TRASHED_LABEL_TERM = LABEL_SCHEME + '#trashed'
HIDDEN_LABEL_TERM = LABEL_SCHEME + '#hidden'
MINE_LABEL_TERM = LABEL_SCHEME + '#mine'
PRIVATE_LABEL_TERM = LABEL_SCHEME + '#private'
SHARED_WITH_DOMAIN_LABEL_TERM = LABEL_SCHEME + '#shared-with-domain'
VIEWED_LABEL_TERM = LABEL_SCHEME + '#viewed'

DOCS_PARENT_LINK_REL = DOCUMENTS_NS + '#parent'
DOCS_PUBLISH_LINK_REL = DOCUMENTS_NS + '#publish'

FILE_EXT_PATTERN = re.compile('.*\.([a-zA-Z]{3,}$)')
RESOURCE_ID_PATTERN = re.compile('^([a-z]*)(:|%3A)([\w-]*)$')

# File extension/mimetype pairs of common format.
MIMETYPES = {
  'CSV': 'text/csv',
  'TSV': 'text/tab-separated-values',
  'TAB': 'text/tab-separated-values',
  'DOC': 'application/msword',
  'DOCX': ('application/vnd.openxmlformats-officedocument.'
           'wordprocessingml.document'),
  'ODS': 'application/x-vnd.oasis.opendocument.spreadsheet',
  'ODT': 'application/vnd.oasis.opendocument.text',
  'RTF': 'application/rtf',
  'SXW': 'application/vnd.sun.xml.writer',
  'TXT': 'text/plain',
  'XLS': 'application/vnd.ms-excel',
  'XLSX': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'PDF': 'application/pdf',
  'PNG': 'image/png',
  'PPT': 'application/vnd.ms-powerpoint',
  'PPS': 'application/vnd.ms-powerpoint',
  'HTM': 'text/html',
  'HTML': 'text/html',
  'ZIP': 'application/zip',
  'SWF': 'application/x-shockwave-flash'
  }


def make_kind_category(label):
  """Builds the appropriate atom.data.Category for the label passed in.

  Args:
    label: str The value for the category entry.

  Returns:
    An atom.data.Category or None if label is None.
  """
  if label is None:
    return None

  return atom.data.Category(
    scheme=DATA_KIND_SCHEME, term='%s#%s' % (DOCUMENTS_NS, label), label=label)

MakeKindCategory = make_kind_category

def make_content_link_from_resource_id(resource_id):
  """Constructs export URL for a given resource.

  Args:
    resource_id: str The document/item's resource id. Example presentation:
        'presentation%3A0A1234567890'.

  Raises:
    gdata.client.ValueError if the resource_id is not a valid format.
  """
  match = RESOURCE_ID_PATTERN.match(resource_id)

  if match:
    label = match.group(1)
    doc_id = match.group(3)
    if label == DOCUMENT_LABEL:
      return '/feeds/download/documents/Export?docId=%s' % doc_id
    if label == PRESENTATION_LABEL:
      return '/feeds/download/presentations/Export?docId=%s' % doc_id
    if label == SPREADSHEET_LABEL:
      return ('http://spreadsheets.google.com/feeds/download/spreadsheets/'
              'Export?key=%s' % doc_id)
  raise ValueError, ('Invalid resource id: %s, or manually creating the '
                     'download url for this type of doc is not possible'
                     % resource_id)

MakeContentLinkFromResourceId = make_content_link_from_resource_id


class ResourceId(atom.core.XmlElement):
  """The DocList gd:resourceId element."""
  _qname = gdata.data.GDATA_TEMPLATE  % 'resourceId'


class LastModifiedBy(atom.data.Person):
  """The DocList gd:lastModifiedBy element."""
  _qname = gdata.data.GDATA_TEMPLATE  % 'lastModifiedBy'


class LastViewed(atom.data.Person):
  """The DocList gd:lastViewed element."""
  _qname = gdata.data.GDATA_TEMPLATE  % 'lastViewed'


class WritersCanInvite(atom.core.XmlElement):
  """The DocList docs:writersCanInvite element."""
  _qname = DOCUMENTS_TEMPLATE  % 'writersCanInvite'
  value = 'value'


class QuotaBytesUsed(atom.core.XmlElement):
  """The DocList gd:quotaBytesUsed element."""
  _qname = gdata.data.GDATA_TEMPLATE  % 'quotaBytesUsed'


class Publish(atom.core.XmlElement):
  """The DocList docs:publish element."""
  _qname = DOCUMENTS_TEMPLATE  % 'publish'
  value = 'value'


class PublishAuto(atom.core.XmlElement):
  """The DocList docs:publishAuto element."""
  _qname = DOCUMENTS_TEMPLATE  % 'publishAuto'
  value = 'value'


class PublishOutsideDomain(atom.core.XmlElement):
  """The DocList docs:publishOutsideDomain element."""
  _qname = DOCUMENTS_TEMPLATE  % 'publishOutsideDomain'
  value = 'value'


class DocsEntry(gdata.data.GDEntry):
  """A DocList version of an Atom Entry."""

  last_viewed = LastViewed
  last_modified_by = LastModifiedBy
  resource_id = ResourceId
  writers_can_invite = WritersCanInvite
  quota_bytes_used = QuotaBytesUsed
  feed_link = [gdata.data.FeedLink]

  def get_document_type(self):
    """Extracts the type of document this DocsEntry is.

    This method returns the type of document the DocsEntry represents. Possible
    values are document, presentation, spreadsheet, folder, or pdf.

    Returns:
      A string representing the type of document.
    """
    if self.category:
      for category in self.category:
        if category.scheme == DATA_KIND_SCHEME:
          return category.label
    else:
      return None

  GetDocumentType = get_document_type

  def get_acl_feed_link(self):
    """Extracts the DocsEntry's ACL feed <gd:feedLink>.

    Returns:
      A gdata.data.FeedLink object.
    """
    for feed_link in self.feed_link:
      if feed_link.rel == ACL_FEEDLINK_REL:
        return feed_link
    return None

  GetAclFeedLink = get_acl_feed_link

  def get_revisions_feed_link(self):
    """Extracts the DocsEntry's revisions feed <gd:feedLink>.

    Returns:
      A gdata.data.FeedLink object.
    """
    for feed_link in self.feed_link:
      if feed_link.rel == REVISION_FEEDLINK_REL:
        return feed_link
    return None

  GetRevisionsFeedLink = get_revisions_feed_link

  def in_folders(self):
    """Returns the parents link(s) (folders) of this entry."""
    links = []
    for link in self.link:
      if link.rel == DOCS_PARENT_LINK_REL and link.href:
        links.append(link)
    return links

  InFolders = in_folders


class Acl(gdata.acl.data.AclEntry):
  """A document ACL entry."""


class DocList(gdata.data.GDFeed):
  """The main DocList feed containing a list of Google Documents."""
  entry = [DocsEntry]


class AclFeed(gdata.acl.data.AclFeed):
  """A DocList ACL feed."""
  entry = [Acl]


class Revision(gdata.data.GDEntry):
  """A document Revision entry."""
  publish = Publish
  publish_auto = PublishAuto
  publish_outside_domain = PublishOutsideDomain

  def find_publish_link(self):
    """Get the link that points to the published document on the web.

    Returns:
      A str for the URL in the link with a rel ending in #publish.
    """
    return self.find_url(DOCS_PUBLISH_LINK_REL)

  FindPublishLink = find_publish_link

  def get_publish_link(self):
    """Get the link that points to the published document on the web.

    Returns:
      A gdata.data.Link for the link with a rel ending in #publish.
    """
    return self.get_link(DOCS_PUBLISH_LINK_REL)

  GetPublishLink = get_publish_link


class RevisionFeed(gdata.data.GDFeed):
  """A DocList Revision feed."""
  entry = [Revision]
