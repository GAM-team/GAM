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

"""Contains extensions to Atom objects used with Google Documents."""

__author__ = ('api.jfisher (Jeff Fisher), '
              'api.eric@google.com (Eric Bidelman)')

import atom
import gdata


DOCUMENTS_NAMESPACE = 'http://schemas.google.com/docs/2007'


class Scope(atom.AtomBase):
  """The DocList ACL scope element"""

  _tag = 'scope'
  _namespace = gdata.GACL_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['value'] = 'value'
  _attributes['type'] = 'type'

  def __init__(self, value=None, type=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.value = value
    self.type = type
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


class Role(atom.AtomBase):
  """The DocList ACL role element"""

  _tag = 'role'
  _namespace = gdata.GACL_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.value = value
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


class FeedLink(atom.AtomBase):
  """The DocList gd:feedLink element"""

  _tag = 'feedLink'
  _namespace = gdata.GDATA_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['rel'] = 'rel'
  _attributes['href'] = 'href'

  def __init__(self, href=None, rel=None, text=None, extension_elements=None,
               extension_attributes=None):
    self.href = href
    self.rel = rel
    atom.AtomBase.__init__(self, extension_elements=extension_elements,
                           extension_attributes=extension_attributes, text=text)


class ResourceId(atom.AtomBase):
  """The DocList gd:resourceId element"""

  _tag = 'resourceId'
  _namespace = gdata.GDATA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.value = value
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


class LastModifiedBy(atom.Person):
  """The DocList gd:lastModifiedBy element"""

  _tag = 'lastModifiedBy'
  _namespace = gdata.GDATA_NAMESPACE


class LastViewed(atom.Person):
  """The DocList gd:lastViewed element"""

  _tag = 'lastViewed'
  _namespace = gdata.GDATA_NAMESPACE


class WritersCanInvite(atom.AtomBase):
  """The DocList docs:writersCanInvite element"""

  _tag = 'writersCanInvite'
  _namespace = DOCUMENTS_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['value'] = 'value'


class DocumentListEntry(gdata.GDataEntry):
  """The Google Documents version of an Atom Entry"""

  _tag = gdata.GDataEntry._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feedLink', FeedLink)
  _children['{%s}resourceId' % gdata.GDATA_NAMESPACE] = ('resourceId',
                                                         ResourceId)
  _children['{%s}lastModifiedBy' % gdata.GDATA_NAMESPACE] = ('lastModifiedBy',
                                                             LastModifiedBy)
  _children['{%s}lastViewed' % gdata.GDATA_NAMESPACE] = ('lastViewed',
                                                         LastViewed)
  _children['{%s}writersCanInvite' % DOCUMENTS_NAMESPACE] = (
      'writersCanInvite', WritersCanInvite)

  def __init__(self, resourceId=None, feedLink=None, lastViewed=None,
               lastModifiedBy=None, writersCanInvite=None, author=None,
               category=None, content=None, atom_id=None, link=None,
               published=None, title=None, updated=None, text=None,
               extension_elements=None, extension_attributes=None):
    self.feedLink = feedLink
    self.lastViewed = lastViewed
    self.lastModifiedBy = lastModifiedBy
    self.resourceId = resourceId
    self.writersCanInvite = writersCanInvite
    gdata.GDataEntry.__init__(
        self, author=author, category=category, content=content,
        atom_id=atom_id, link=link, published=published, title=title,
        updated=updated, extension_elements=extension_elements,
        extension_attributes=extension_attributes, text=text)

  def GetAclLink(self):
    """Extracts the DocListEntry's <gd:feedLink>.

    Returns:
      A FeedLink object.
    """
    return self.feedLink

  def GetDocumentType(self):
    """Extracts the type of document from the DocListEntry.

    This method returns the type of document the DocListEntry
    represents.  Possible values are document, presentation,
    spreadsheet, folder, or pdf.

    Returns:
      A string representing the type of document.
    """
    if self.category:
      for category in self.category:
        if category.scheme == gdata.GDATA_NAMESPACE + '#kind':
          return category.label
    else:
      return None


def DocumentListEntryFromString(xml_string):
  """Converts an XML string into a DocumentListEntry object.

  Args:
    xml_string: string The XML describing a Document List feed entry.

  Returns:
    A DocumentListEntry object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(DocumentListEntry, xml_string)


class DocumentListAclEntry(gdata.GDataEntry):
  """A DocList ACL Entry flavor of an Atom Entry"""

  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}scope' % gdata.GACL_NAMESPACE] = ('scope', Scope)
  _children['{%s}role' % gdata.GACL_NAMESPACE] = ('role', Role)

  def __init__(self, category=None, atom_id=None, link=None,
               title=None, updated=None, scope=None, role=None,
               extension_elements=None, extension_attributes=None, text=None):
    gdata.GDataEntry.__init__(self, author=None, category=category,
                              content=None, atom_id=atom_id, link=link,
                              published=None, title=title,
                              updated=updated, text=None)
    self.scope = scope
    self.role = role


def DocumentListAclEntryFromString(xml_string):
  """Converts an XML string into a DocumentListAclEntry object.

  Args:
    xml_string: string The XML describing a Document List ACL feed entry.

  Returns:
    A DocumentListAclEntry object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(DocumentListAclEntry, xml_string)


class DocumentListFeed(gdata.GDataFeed):
  """A feed containing a list of Google Documents Items"""

  _tag = gdata.GDataFeed._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [DocumentListEntry])


def DocumentListFeedFromString(xml_string):
  """Converts an XML string into a DocumentListFeed object.

  Args:
    xml_string: string The XML describing a DocumentList feed.

  Returns:
    A DocumentListFeed object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(DocumentListFeed, xml_string)


class DocumentListAclFeed(gdata.GDataFeed):
  """A DocList ACL feed flavor of a Atom feed"""

  _tag = gdata.GDataFeed._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [DocumentListAclEntry])


def DocumentListAclFeedFromString(xml_string):
  """Converts an XML string into a DocumentListAclFeed object.

  Args:
    xml_string: string The XML describing a DocumentList feed.

  Returns:
    A DocumentListFeed object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(DocumentListAclFeed, xml_string)
