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

"""Data model classes for parsing and generating XML for the Sites Data API."""

__author__ = 'e.bidelman (Eric Bidelman)'


import atom.core
import atom.data
import gdata.acl.data
import gdata.data

# XML Namespaces used in Google Sites entities.
SITES_NAMESPACE = 'http://schemas.google.com/sites/2008'
SITES_TEMPLATE = '{http://schemas.google.com/sites/2008}%s'
SPREADSHEETS_NAMESPACE = 'http://schemas.google.com/spreadsheets/2006'
SPREADSHEETS_TEMPLATE = '{http://schemas.google.com/spreadsheets/2006}%s'
DC_TERMS_TEMPLATE = '{http://purl.org/dc/terms}%s'
THR_TERMS_TEMPLATE = '{http://purl.org/syndication/thread/1.0}%s'
XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'
XHTML_TEMPLATE = '{http://www.w3.org/1999/xhtml}%s'

SITES_PARENT_LINK_REL = SITES_NAMESPACE + '#parent'
SITES_REVISION_LINK_REL = SITES_NAMESPACE + '#revision'
SITES_SOURCE_LINK_REL = SITES_NAMESPACE + '#source'

SITES_KIND_SCHEME = 'http://schemas.google.com/g/2005#kind'
ANNOUNCEMENT_KIND_TERM = SITES_NAMESPACE + '#announcement'
ANNOUNCEMENT_PAGE_KIND_TERM = SITES_NAMESPACE + '#announcementspage'
ATTACHMENT_KIND_TERM = SITES_NAMESPACE + '#attachment'
COMMENT_KIND_TERM = SITES_NAMESPACE + '#comment'
FILECABINET_KIND_TERM = SITES_NAMESPACE + '#filecabinet'
LISTITEM_KIND_TERM = SITES_NAMESPACE + '#listitem'
LISTPAGE_KIND_TERM = SITES_NAMESPACE + '#listpage'
WEBPAGE_KIND_TERM = SITES_NAMESPACE + '#webpage'
WEBATTACHMENT_KIND_TERM = SITES_NAMESPACE + '#webattachment'
FOLDER_KIND_TERM = SITES_NAMESPACE + '#folder'
TAG_KIND_TERM = SITES_NAMESPACE + '#tag'

SUPPORT_KINDS = [
    'announcement', 'announcementspage', 'attachment', 'comment', 'filecabinet',
    'listitem', 'listpage', 'webpage', 'webattachment', 'tag'
    ]


class Revision(atom.core.XmlElement):
  """Google Sites <sites:revision>."""
  _qname = SITES_TEMPLATE % 'revision'


class PageName(atom.core.XmlElement):
  """Google Sites <sites:pageName>."""
  _qname = SITES_TEMPLATE % 'pageName'


class SiteName(atom.core.XmlElement):
  """Google Sites <sites:siteName>."""
  _qname = SITES_TEMPLATE % 'siteName'


class Theme(atom.core.XmlElement):
  """Google Sites <sites:theme>."""
  _qname = SITES_TEMPLATE % 'theme'


class Deleted(atom.core.XmlElement):
  """Google Sites <gd:deleted>."""
  _qname = gdata.data.GDATA_TEMPLATE % 'deleted'


class Publisher(atom.core.XmlElement):
  """Google Sites <dc:pulisher>."""
  _qname = DC_TERMS_TEMPLATE % 'publisher'


class Worksheet(atom.core.XmlElement):
  """Google Sites List Page <gs:worksheet>."""

  _qname = SPREADSHEETS_TEMPLATE % 'worksheet'
  name = 'name'


class Header(atom.core.XmlElement):
  """Google Sites List Page <gs:header>."""

  _qname = SPREADSHEETS_TEMPLATE % 'header'
  row = 'row'


class Column(atom.core.XmlElement):
  """Google Sites List Page <gs:column>."""

  _qname = SPREADSHEETS_TEMPLATE % 'column'
  index = 'index'
  name = 'name'


class Data(atom.core.XmlElement):
  """Google Sites List Page <gs:data>."""

  _qname = SPREADSHEETS_TEMPLATE % 'data'
  startRow = 'startRow'
  column = [Column]


class Field(atom.core.XmlElement):
  """Google Sites List Item <gs:field>."""

  _qname = SPREADSHEETS_TEMPLATE % 'field'
  index = 'index'
  name = 'name'


class InReplyTo(atom.core.XmlElement):
  """Google Sites List Item <thr:in-reply-to>."""

  _qname = THR_TERMS_TEMPLATE % 'in-reply-to'
  href = 'href'
  ref = 'ref'
  source = 'source'
  type = 'type'


class Content(atom.data.Content):
  """Google Sites version of <atom:content> that encapsulates XHTML."""

  def __init__(self, html=None, type=None, **kwargs):
    if type is None and html:
      type = 'xhtml'
    super(Content, self).__init__(type=type, **kwargs)
    if html is not None:
      self.html = html

  def _get_html(self):
    if self.children:
      return self.children[0]
    else:
      return ''

  def _set_html(self, html):
    if not html:
      self.children = []
      return

    if type(html) == str:
      html = atom.core.parse(html)
      if not html.namespace:
        html.namespace = XHTML_NAMESPACE

    self.children = [html]

  html = property(_get_html, _set_html)


class Summary(atom.data.Summary):
  """Google Sites version of <atom:summary>."""

  def __init__(self, html=None, type=None, text=None, **kwargs):
    if type is None and html:
      type = 'xhtml'

    super(Summary, self).__init__(type=type, text=text, **kwargs)
    if html is not None:
      self.html = html

  def _get_html(self):
    if self.children:
      return self.children[0]
    else:
      return ''

  def _set_html(self, html):
    if not html:
      self.children = []
      return

    if type(html) == str:
      html = atom.core.parse(html)
      if not html.namespace:
        html.namespace = XHTML_NAMESPACE

    self.children = [html]

  html = property(_get_html, _set_html)


class BaseSiteEntry(gdata.data.GDEntry):
  """Google Sites Entry."""

  def __init__(self, kind=None, **kwargs):
    super(BaseSiteEntry, self).__init__(**kwargs)
    if kind is not None:
      self.category.append(
          atom.data.Category(scheme=SITES_KIND_SCHEME,
                             term='%s#%s' % (SITES_NAMESPACE, kind),
                             label=kind))

  def __find_category_scheme(self, scheme):
    for category in self.category:
      if category.scheme == scheme:
        return category
    return None

  def kind(self):
    kind = self.__find_category_scheme(SITES_KIND_SCHEME)
    if kind is not None:
      return kind.term[len(SITES_NAMESPACE) + 1:]
    else:
      return None

  Kind = kind

  def get_node_id(self):
    return self.id.text[self.id.text.rfind('/') + 1:]

  GetNodeId = get_node_id

  def find_parent_link(self):
    return self.find_url(SITES_PARENT_LINK_REL)

  FindParentLink = find_parent_link

  def is_deleted(self):
    return self.deleted is not None

  IsDeleted = is_deleted


class ContentEntry(BaseSiteEntry):
  """Google Sites Content Entry."""
  content = Content
  deleted = Deleted
  publisher = Publisher
  in_reply_to = InReplyTo
  worksheet = Worksheet
  header = Header
  data = Data
  field = [Field]
  revision = Revision
  page_name = PageName
  feed_link = gdata.data.FeedLink

  def find_revison_link(self):
    return self.find_url(SITES_REVISION_LINK_REL)

  FindRevisionLink = find_revison_link


class ContentFeed(gdata.data.GDFeed):
  """Google Sites Content Feed.

  The Content feed is a feed containing the current, editable site content.
  """
  entry = [ContentEntry]

  def __get_entry_type(self, kind):
    matches = []
    for entry in self.entry:
      if entry.Kind() == kind:
        matches.append(entry)
    return matches

  def get_announcements(self):
    return self.__get_entry_type('announcement')

  GetAnnouncements = get_announcements

  def get_announcement_pages(self):
    return self.__get_entry_type('announcementspage')

  GetAnnouncementPages = get_announcement_pages

  def get_attachments(self):
    return self.__get_entry_type('attachment')

  GetAttachments = get_attachments

  def get_comments(self):
    return self.__get_entry_type('comment')

  GetComments = get_comments

  def get_file_cabinets(self):
    return self.__get_entry_type('filecabinet')

  GetFileCabinets = get_file_cabinets

  def get_list_items(self):
    return self.__get_entry_type('listitem')

  GetListItems = get_list_items

  def get_list_pages(self):
    return self.__get_entry_type('listpage')

  GetListPages = get_list_pages

  def get_webpages(self):
    return self.__get_entry_type('webpage')

  GetWebpages = get_webpages

  def get_webattachments(self):
    return self.__get_entry_type('webattachment')

  GetWebattachments = get_webattachments


class ActivityEntry(BaseSiteEntry):
  """Google Sites Activity Entry."""
  summary = Summary


class ActivityFeed(gdata.data.GDFeed):
  """Google Sites Activity Feed.

  The Activity feed is a feed containing recent Site activity.
  """
  entry = [ActivityEntry]


class RevisionEntry(BaseSiteEntry):
  """Google Sites Revision Entry."""
  content = Content


class RevisionFeed(gdata.data.GDFeed):
  """Google Sites Revision Feed.

  The Activity feed is a feed containing recent Site activity.
  """
  entry = [RevisionEntry]


class SiteEntry(gdata.data.GDEntry):
  """Google Sites Site Feed Entry."""
  site_name = SiteName
  theme = Theme

  def find_source_link(self):
    return self.find_url(SITES_SOURCE_LINK_REL)

  FindSourceLink = find_source_link


class SiteFeed(gdata.data.GDFeed):
  """Google Sites Site Feed.

  The Site feed can be used to list a user's sites and create new sites.
  """
  entry = [SiteEntry]


class AclEntry(gdata.acl.data.AclEntry):
  """Google Sites ACL Entry."""


class AclFeed(gdata.acl.data.AclFeed):
  """Google Sites ACL Feed.

  The ACL feed can be used to modify the sharing permissions of a Site.
  """
  entry = [AclEntry]
