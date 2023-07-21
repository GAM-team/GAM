#!/usr/bin/env python
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

import atom
import gdata

# XML Namespaces used in Google Sites entities.
SITES_NAMESPACE = 'http://schemas.google.com/sites/2008'
SITES_TEMPLATE = '{http://schemas.google.com/sites/2008}%s'
SPREADSHEETS_NAMESPACE = 'http://schemas.google.com/spreadsheets/2006'
SPREADSHEETS_TEMPLATE = '{http://schemas.google.com/spreadsheets/2006}%s'
GACL_NAMESPACE = 'http://schemas.google.com/acl/2007'
GACL_TEMPLATE = '{http://schemas.google.com/acl/2007}%s'
DC_TERMS_TEMPLATE = '{http://purl.org/dc/terms}%s'
THR_TERMS_TEMPLATE = '{http://purl.org/syndication/thread/1.0}%s'
XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'
XHTML_TEMPLATE = '{http://www.w3.org/1999/xhtml}%s'

SITES_INVITE_LINK_REL = SITES_NAMESPACE + '#invite'
SITES_PARENT_LINK_REL = SITES_NAMESPACE + '#parent'
SITES_REVISION_LINK_REL = SITES_NAMESPACE + '#revision'
SITES_SOURCE_LINK_REL = SITES_NAMESPACE + '#source'
SITES_TEMPLATE_LINK_REL = SITES_NAMESPACE + '#template'

ALTERNATE_REL = 'alternate'
WEB_ADDRESS_MAPPING_REL = 'webAddressMapping'

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


class GDataBase(atom.AtomBase):
  """The Google Sites intermediate class from atom.AtomBase."""
  _namespace = gdata.GDATA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, text=None):
    atom.AtomBase.__init__(self, text=text)

class SitesBase(GDataBase):
  _namespace = SITES_NAMESPACE

class SiteName(SitesBase):
  """Google Sites <sites:siteName>."""
  _tag = 'siteName'

class Theme(SitesBase):
  """Google Sites <sites:theme>."""
  _tag = 'theme'

class SiteEntry(gdata.BatchEntry):
  """Google Sites Site Feed Entry."""
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchEntry._children.copy()

  _children['{%s}siteName' % SITES_NAMESPACE] = ('siteName', SiteName)
  _children['{%s}theme' % SITES_NAMESPACE] = ('theme', Theme)
  _attributes = gdata.BatchEntry._attributes.copy()
  _attributes['{%s}etag' % gdata.GDATA_NAMESPACE] = 'etag'

  def __init__(self, siteName=None, title=None, summary=None, theme=None, sourceSite=None, category=None, etag=None):
    gdata.BatchEntry.__init__(self, category=category)
    self.siteName = siteName
    self.title = title
    self.summary = summary
    self.theme = theme
    if sourceSite is not None:
      sourceLink = atom.Link(href=sourceSite, rel=SITES_SOURCE_LINK_REL, link_type='application/atom+xml')
      self.link.append(sourceLink)
    self.etag = etag

  def find_alternate_link(self):
    for link in self.link:
      if link.rel == ALTERNATE_REL and link.href:
        return link.href
    return None

  FindAlternateLink = find_alternate_link

  def find_source_link(self):
    for link in self.link:
      if link.rel == SITES_SOURCE_LINK_REL and link.href:
        return link.href
    return None

  FindSourceLink = find_source_link

  def find_webaddress_mappings(self):
    mappingLinks = []
    for link in self.link:
      if link.rel == WEB_ADDRESS_MAPPING_REL and link.href:
        mappingLinks.append(link.href)
    return mappingLinks

  FindWebAddressMappings = find_webaddress_mappings

def SiteEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(SiteEntry, xml_string)

class SiteFeed(gdata.BatchFeed, gdata.LinkFinder):
  """A Google Sites feed flavor of an Atom Feed."""
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [SiteEntry])

  def __init__(self):
    gdata.BatchFeed.__init__(self)

def SiteFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SiteFeed, xml_string)

class AclBase(GDataBase):
  _namespace = GACL_NAMESPACE

class AclRole(AclBase):
  """Describes the role of an entry in an access control list."""
  _tag = 'role'
  _children = AclBase._children.copy()
  _attributes = AclBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None):
    AclBase.__init__(self)
    self.value = value

class AclAdditionalRole(AclBase):
  """Describes an additionalRole element."""
  _tag = 'additionalRole'
  _children = AclBase._children.copy()
  _attributes = AclBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None):
    AclBase.__init__(self)
    self.value = value

class AclScope(AclBase):
  """Describes the scope of an entry in an access control list."""
  _tag = 'scope'
  _children = AclBase._children.copy()
  _attributes = AclBase._attributes.copy()
  _attributes['type'] = 'type'
  _attributes['value'] = 'value'

  def __init__(self, stype=None, value=None):
    AclBase.__init__(self)
    self.type = stype
    self.value = value


class AclWithKey(AclBase):
  """Describes a key that can be used to access a document."""
  _tag = 'withKey'
  _children = AclBase._children.copy()
  _children['{%s}role' % GACL_NAMESPACE] = ('role', AclRole)
  _children['{%s}additionalRole' % GACL_NAMESPACE] = ('additionalRole', AclAdditionalRole)
  _attributes = AclBase._attributes.copy()
  _attributes['key'] = 'key'

  def __init__(self, key=None, role=None, additionalRole=None):
    AclBase.__init__(self)
    self.key = key
    self.role = role
    self.additionalRole = additionalRole

class AclEntry(gdata.BatchEntry):
  """Describes an entry in a feed of an access control list (ACL)."""
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchEntry._children.copy()

  _children['{%s}role' % GACL_NAMESPACE] = ('role', AclRole)
  _children['{%s}additionalRole' % GACL_NAMESPACE] = ('additionalRole', AclAdditionalRole)
  _children['{%s}scope' % GACL_NAMESPACE] = ('scope', AclScope)
  _children['{%s}withKey' % GACL_NAMESPACE] = ('withKey', AclWithKey)
  _attributes = gdata.BatchEntry._attributes.copy()
  _attributes['{%s}etag' % gdata.GDATA_NAMESPACE] = 'etag'

  def __init__(self, role=None, additionalRole=None, scope=None, withKey=None, etag=None):
    gdata.BatchEntry.__init__(self)
    self.role = role
    self.additionalRole = additionalRole
    self.scope = scope
    self.withKey = withKey
    self.etag = etag

  def find_invite_link(self):
    for link in self.link:
      if link.rel == SITES_INVITE_LINK_REL and link.href:
        return link.href
    return None

  FindInviteLink = find_invite_link

def AclEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(AclEntry, xml_string)

class AclFeed(gdata.BatchFeed, gdata.LinkFinder):
  """Describes a feed of an access control list (ACL)."""
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [AclEntry])

  def __init__(self):
    gdata.BatchFeed.__init__(self)

def AclFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(AclFeed, xml_string)

class ActivityEntry(gdata.BatchEntry):
  """Describes an entry in a feed of site activity (changes)."""
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchEntry._children.copy()
  _attributes = gdata.BatchEntry._attributes.copy()

  def __init__(self):
    gdata.BatchEntry.__init__(self)

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

def ActivityEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(ActivityEntry, xml_string)

class ActivityFeed(gdata.BatchFeed, gdata.LinkFinder):
  """Describes a feed of site activity (changes)."""
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [ActivityEntry])

  def __init__(self):
    gdata.BatchFeed.__init__(self)

def ActivityFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(ActivityFeed, xml_string)
