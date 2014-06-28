#!/usr/bin/python
#
# Copyright (C) 2006 Google Inc.
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

"""Contains extensions to Atom objects used with Google Base."""


__author__ = 'api.jscudder (Jeffrey Scudder)'


try:
  from xml.etree import cElementTree as ElementTree
except ImportError:
  try:
    import cElementTree as ElementTree
  except ImportError:
    try:
      from xml.etree import ElementTree
    except ImportError:
      from elementtree import ElementTree
import atom
import gdata


# XML namespaces which are often used in Google Base entities.
GBASE_NAMESPACE = 'http://base.google.com/ns/1.0'
GBASE_TEMPLATE = '{http://base.google.com/ns/1.0}%s'
GMETA_NAMESPACE = 'http://base.google.com/ns-metadata/1.0'
GMETA_TEMPLATE = '{http://base.google.com/ns-metadata/1.0}%s'


class ItemAttributeContainer(atom.AtomBase):
  """Provides methods for finding Google Base Item attributes.
  
  Google Base item attributes are child nodes in the gbase namespace. Google
  Base allows you to define your own item attributes and this class provides
  methods to interact with the custom attributes.   
  """

  def GetItemAttributes(self, name):
    """Returns a list of all item attributes which have the desired name.

    Args:
      name: str The tag of the desired base attributes. For example, calling
          this method with 'rating' would return a list of ItemAttributes
          represented by a 'g:rating' tag.

    Returns:
      A list of matching ItemAttribute objects.
    """
    result = []
    for attrib in self.item_attributes:
      if attrib.name == name:
        result.append(attrib)
    return result

  def FindItemAttribute(self, name):
    """Get the contents of the first Base item attribute which matches name.

    This method is deprecated, please use GetItemAttributes instead.
    
    Args: 
      name: str The tag of the desired base attribute. For example, calling
          this method with name = 'rating' would search for a tag rating
          in the GBase namespace in the item attributes. 

    Returns:
      The text contents of the item attribute, or none if the attribute was
      not found.
    """
  
    for attrib in self.item_attributes:
      if attrib.name == name:
        return attrib.text
    return None

  def AddItemAttribute(self, name, value, value_type=None, access=None):
    """Adds a new item attribute tag containing the value.
    
    Creates a new extension element in the GBase namespace to represent a
    Google Base item attribute.
    
    Args:
      name: str The tag name for the new attribute. This must be a valid xml
        tag name. The tag will be placed in the GBase namespace.
      value: str Contents for the item attribute
      value_type: str (optional) The type of data in the vlaue, Examples: text
          float
      access: str (optional) Used to hide attributes. The attribute is not 
          exposed in the snippets feed if access is set to 'private'.
    """

    new_attribute =  ItemAttribute(name, text=value, 
        text_type=value_type, access=access)
    self.item_attributes.append(new_attribute)
    return new_attribute
    
  def SetItemAttribute(self, name, value):
    """Changes an existing item attribute's value."""

    for attrib in self.item_attributes:
      if attrib.name == name:
        attrib.text = value
        return

  def RemoveItemAttribute(self, name):
    """Deletes the first extension element which matches name.
    
    Deletes the first extension element which matches name. 
    """

    for i in xrange(len(self.item_attributes)):
      if self.item_attributes[i].name == name:
        del self.item_attributes[i]
        return
  
  # We need to overwrite _ConvertElementTreeToMember to add special logic to
  # convert custom attributes to members
  def _ConvertElementTreeToMember(self, child_tree):
    # Find the element's tag in this class's list of child members
    if self.__class__._children.has_key(child_tree.tag):
      member_name = self.__class__._children[child_tree.tag][0]
      member_class = self.__class__._children[child_tree.tag][1]
      # If the class member is supposed to contain a list, make sure the
      # matching member is set to a list, then append the new member
      # instance to the list.
      if isinstance(member_class, list):
        if getattr(self, member_name) is None:
          setattr(self, member_name, [])
        getattr(self, member_name).append(atom._CreateClassFromElementTree(
            member_class[0], child_tree))
      else:
        setattr(self, member_name, 
                atom._CreateClassFromElementTree(member_class, child_tree))
    elif child_tree.tag.find('{%s}' % GBASE_NAMESPACE) == 0:
      # If this is in the gbase namespace, make it into an extension element.
      name = child_tree.tag[child_tree.tag.index('}')+1:]
      value = child_tree.text
      if child_tree.attrib.has_key('type'):
        value_type = child_tree.attrib['type']
      else:
        value_type = None
      attrib=self.AddItemAttribute(name, value, value_type)
      for sub in child_tree.getchildren():
        sub_name = sub.tag[sub.tag.index('}')+1:]
        sub_value=sub.text
        if sub.attrib.has_key('type'): 
          sub_type = sub.attrib['type']
        else:
          sub_type=None
        attrib.AddItemAttribute(sub_name, sub_value, sub_type)
    else:
      atom.ExtensionContainer._ConvertElementTreeToMember(self, child_tree)
  
  # We need to overwtite _AddMembersToElementTree to add special logic to
  # convert custom members to XML nodes.
  def _AddMembersToElementTree(self, tree):
    # Convert the members of this class which are XML child nodes. 
    # This uses the class's _children dictionary to find the members which
    # should become XML child nodes.
    member_node_names = [values[0] for tag, values in 
                                       self.__class__._children.iteritems()]
    for member_name in member_node_names:
      member = getattr(self, member_name)
      if member is None:
        pass
      elif isinstance(member, list):
        for instance in member:
          instance._BecomeChildElement(tree)
      else:
        member._BecomeChildElement(tree)
    # Convert the members of this class which are XML attributes.
    for xml_attribute, member_name in self.__class__._attributes.iteritems():
      member = getattr(self, member_name)
      if member is not None:
        tree.attrib[xml_attribute] = member
    # Convert all special custom item attributes to nodes
    for attribute in self.item_attributes:
      attribute._BecomeChildElement(tree)
    # Lastly, call the ExtensionContainers's _AddMembersToElementTree to 
    # convert any extension attributes.
    atom.ExtensionContainer._AddMembersToElementTree(self, tree)


class ItemAttribute(ItemAttributeContainer):
  """An optional or user defined attribute for a GBase item.
  
  Google Base allows items to have custom attribute child nodes. These nodes
  have contents and a type attribute which tells Google Base whether the
  contents are text, a float value with units, etc. The Atom text class has 
  the same structure, so this class inherits from Text.
  """
  
  _namespace = GBASE_NAMESPACE
  _children = atom.Text._children.copy()
  _attributes = atom.Text._attributes.copy()
  _attributes['access'] = 'access'

  def __init__(self, name, text_type=None, access=None, text=None, 
      extension_elements=None, extension_attributes=None, item_attributes=None):
    """Constructor for a GBase item attribute

    Args:
      name: str The name of the attribute. Examples include
          price, color, make, model, pages, salary, etc.
      text_type: str (optional) The type associated with the text contents
      access: str (optional) If the access attribute is set to 'private', the
          attribute will not be included in the item's description in the 
          snippets feed
      text: str (optional) The text data in the this element
      extension_elements: list (optional) A  list of ExtensionElement 
          instances
      extension_attributes: dict (optional) A dictionary of attribute 
          value string pairs
    """

    self.name = name
    self.type = text_type
    self.access = access
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    self.item_attributes = item_attributes or []
    
  def _BecomeChildElement(self, tree):
    new_child = ElementTree.Element('')
    tree.append(new_child)
    new_child.tag = '{%s}%s' % (self.__class__._namespace, 
                                self.name)
    self._AddMembersToElementTree(new_child)
  
  def _ToElementTree(self):
    new_tree = ElementTree.Element('{%s}%s' % (self.__class__._namespace,
                                               self.name))
    self._AddMembersToElementTree(new_tree)
    return new_tree
    

def ItemAttributeFromString(xml_string):
  element_tree = ElementTree.fromstring(xml_string)
  return _ItemAttributeFromElementTree(element_tree)  
  
  
def _ItemAttributeFromElementTree(element_tree):
  if element_tree.tag.find(GBASE_TEMPLATE % '') == 0:
    to_return = ItemAttribute('')
    to_return._HarvestElementTree(element_tree)
    to_return.name = element_tree.tag[element_tree.tag.index('}')+1:]
    if to_return.name and to_return.name != '':
      return to_return
  return None
  

class Label(atom.AtomBase):
  """The Google Base label element"""
  
  _tag = 'label'
  _namespace = GBASE_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, text=None, extension_elements=None,
      extension_attributes=None):
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def LabelFromString(xml_string):
  return atom.CreateClassFromXMLString(Label, xml_string)


class Thumbnail(atom.AtomBase):
  """The Google Base thumbnail element"""
  
  _tag = 'thumbnail'
  _namespace = GMETA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['width'] = 'width'
  _attributes['height'] = 'height'

  def __init__(self, width=None, height=None, text=None, extension_elements=None,
      extension_attributes=None):
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    self.width = width
    self.height = height


def ThumbnailFromString(xml_string):
  return atom.CreateClassFromXMLString(Thumbnail, xml_string)


class ImageLink(atom.Text):
  """The Google Base image_link element"""
  
  _tag = 'image_link'
  _namespace = GBASE_NAMESPACE
  _children = atom.Text._children.copy()
  _attributes = atom.Text._attributes.copy()
  _children['{%s}thumbnail' % GMETA_NAMESPACE] = ('thumbnail', [Thumbnail])

  def __init__(self, thumbnail=None, text=None, extension_elements=None,
      text_type=None, extension_attributes=None):
    self.thumbnail = thumbnail or []
    self.text = text
    self.type = text_type
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    

def ImageLinkFromString(xml_string):
  return atom.CreateClassFromXMLString(ImageLink, xml_string)


class ItemType(atom.Text):
  """The Google Base item_type element"""
  
  _tag = 'item_type'
  _namespace = GBASE_NAMESPACE
  _children = atom.Text._children.copy()
  _attributes = atom.Text._attributes.copy()

  def __init__(self, text=None, extension_elements=None,
      text_type=None, extension_attributes=None):
    self.text = text
    self.type = text_type
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def ItemTypeFromString(xml_string):
  return atom.CreateClassFromXMLString(ItemType, xml_string)


class MetaItemType(ItemType):
  """The Google Base item_type element"""
  
  _tag = 'item_type'
  _namespace = GMETA_NAMESPACE
  _children = ItemType._children.copy()
  _attributes = ItemType._attributes.copy()

  
def MetaItemTypeFromString(xml_string):
  return atom.CreateClassFromXMLString(MetaItemType, xml_string)


class Value(atom.AtomBase):
  """Metadata about common values for a given attribute
  
  A value is a child of an attribute which comes from the attributes feed.
  The value's text is a commonly used value paired with an attribute name
  and the value's count tells how often this value appears for the given
  attribute in the search results.
  """
  
  _tag = 'value'
  _namespace = GMETA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['count'] = 'count'
 
  def __init__(self, count=None, text=None, extension_elements=None, 
      extension_attributes=None):
    """Constructor for Attribute metadata element

    Args:
      count: str (optional) The number of times the value in text is given
          for the parent attribute.
      text: str (optional) The value which appears in the search results.
      extension_elements: list (optional) A  list of ExtensionElement
          instances
      extension_attributes: dict (optional) A dictionary of attribute value
          string pairs
    """

    self.count = count
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def ValueFromString(xml_string):
  return atom.CreateClassFromXMLString(Value, xml_string)


class Attribute(atom.Text):
  """Metadata about an attribute from the attributes feed
  
  An entry from the attributes feed contains a list of attributes. Each 
  attribute describes the attribute's type and count of the items which
  use the attribute.
  """
  
  _tag = 'attribute'
  _namespace = GMETA_NAMESPACE
  _children = atom.Text._children.copy()
  _attributes = atom.Text._attributes.copy()
  _children['{%s}value' % GMETA_NAMESPACE] = ('value', [Value])
  _attributes['count'] = 'count'
  _attributes['name'] = 'name'

  def __init__(self, name=None, attribute_type=None, count=None, value=None, 
      text=None, extension_elements=None, extension_attributes=None):
    """Constructor for Attribute metadata element

    Args:
      name: str (optional) The name of the attribute
      attribute_type: str (optional) The type for the attribute. Examples:
          test, float, etc.
      count: str (optional) The number of times this attribute appears in
          the query results.
      value: list (optional) The values which are often used for this 
          attirbute.
      text: str (optional) The text contents of the XML for this attribute.
      extension_elements: list (optional) A  list of ExtensionElement 
          instances
      extension_attributes: dict (optional) A dictionary of attribute value 
          string pairs
    """

    self.name = name
    self.type = attribute_type
    self.count = count
    self.value = value or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def AttributeFromString(xml_string):
  return atom.CreateClassFromXMLString(Attribute, xml_string)

  
class Attributes(atom.AtomBase):
  """A collection of Google Base metadata attributes"""
  
  _tag = 'attributes'
  _namespace = GMETA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _children['{%s}attribute' % GMETA_NAMESPACE] = ('attribute', [Attribute])
  
  def __init__(self, attribute=None, extension_elements=None, 
      extension_attributes=None, text=None):
    self.attribute = attribute or []
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    self.text = text  
  
  
class GBaseItem(ItemAttributeContainer, gdata.BatchEntry):
  """An Google Base flavor of an Atom Entry.
  
  Google Base items have required attributes, recommended attributes, and user
  defined attributes. The required attributes are stored in this class as 
  members, and other attributes are stored as extension elements. You can 
  access the recommended and user defined attributes by using 
  AddItemAttribute, SetItemAttribute, FindItemAttribute, and 
  RemoveItemAttribute.
  
  The Base Item
  """
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchEntry._children.copy()
  _attributes = gdata.BatchEntry._attributes.copy()
  _children['{%s}label' % GBASE_NAMESPACE] = ('label', [Label])
  _children['{%s}item_type' % GBASE_NAMESPACE] = ('item_type', ItemType)
  
  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, updated=None, control=None, 
      label=None, item_type=None, item_attributes=None,
      batch_operation=None, batch_id=None, batch_status=None,
      text=None, extension_elements=None, extension_attributes=None):
    self.author = author or []
    self.category = category or []
    self.content = content
    self.contributor = contributor or []
    self.id = atom_id
    self.link = link or []
    self.published = published
    self.rights = rights
    self.source = source
    self.summary = summary
    self.title = title
    self.updated = updated
    self.control = control
    self.label = label or []
    self.item_type = item_type
    self.item_attributes = item_attributes or []
    self.batch_operation = batch_operation
    self.batch_id = batch_id
    self.batch_status = batch_status
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def GBaseItemFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseItem, xml_string)


class GBaseSnippet(GBaseItem):
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = GBaseItem._children.copy()
  _attributes = GBaseItem._attributes.copy()
  
  
def GBaseSnippetFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseSnippet, xml_string)


class GBaseAttributeEntry(gdata.GDataEntry):
  """An Atom Entry from the attributes feed"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}attribute' % GMETA_NAMESPACE] = ('attribute', [Attribute])

  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, updated=None, label=None,
      attribute=None, control=None,
      text=None, extension_elements=None, extension_attributes=None):
    self.author = author or []
    self.category = category or []
    self.content = content
    self.contributor = contributor or []
    self.id = atom_id
    self.link = link or []
    self.published = published
    self.rights = rights
    self.source = source
    self.summary = summary
    self.control = control
    self.title = title
    self.updated = updated
    self.label = label or []
    self.attribute = attribute or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {} 


def GBaseAttributeEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseAttributeEntry, xml_string)


class GBaseItemTypeEntry(gdata.GDataEntry):
  """An Atom entry from the item types feed
  
  These entries contain a list of attributes which are stored in one
  XML node called attributes. This class simplifies the data structure
  by treating attributes as a list of attribute instances. 

  Note that the item_type for an item type entry is in the Google Base meta
  namespace as opposed to item_types encountered in other feeds.
  """
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}attributes' % GMETA_NAMESPACE] = ('attributes', Attributes)
  _children['{%s}attribute' % GMETA_NAMESPACE] = ('attribute', [Attribute])
  _children['{%s}item_type' % GMETA_NAMESPACE] = ('item_type', MetaItemType)

  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, updated=None, label=None,
      item_type=None, control=None, attribute=None, attributes=None,
      text=None, extension_elements=None, extension_attributes=None):
    self.author = author or []
    self.category = category or []
    self.content = content
    self.contributor = contributor or []
    self.id = atom_id
    self.link = link or []
    self.published = published
    self.rights = rights
    self.source = source
    self.summary = summary
    self.title = title
    self.updated = updated
    self.control = control
    self.label = label or []
    self.item_type = item_type
    self.attributes = attributes
    self.attribute = attribute  or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def GBaseItemTypeEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseItemTypeEntry, xml_string)
  
  
class GBaseItemFeed(gdata.BatchFeed):
  """A feed containing Google Base Items"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _attributes = gdata.BatchFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [GBaseItem])


def GBaseItemFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseItemFeed, xml_string)


class GBaseSnippetFeed(gdata.GDataFeed):
  """A feed containing Google Base Snippets"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [GBaseSnippet])


def GBaseSnippetFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseSnippetFeed, xml_string)


class GBaseAttributesFeed(gdata.GDataFeed):
  """A feed containing Google Base Attributes
 
  A query sent to the attributes feed will return a feed of
  attributes which are present in the items that match the
  query. 
  """
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [GBaseAttributeEntry])


def GBaseAttributesFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseAttributesFeed, xml_string)


class GBaseLocalesFeed(gdata.GDataFeed):
  """The locales feed from Google Base.

  This read-only feed defines the permitted locales for Google Base. The 
  locale value identifies the language, currency, and date formats used in a
  feed.
  """
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()

  
def GBaseLocalesFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseLocalesFeed, xml_string)
 
 
class GBaseItemTypesFeed(gdata.GDataFeed):
  """A feed from the Google Base item types feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [GBaseItemTypeEntry])


def GBaseItemTypesFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GBaseItemTypesFeed, xml_string)
