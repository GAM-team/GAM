#!/usr/bin/python
#
# Copyright (C) 2007 Google Inc.
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

"""Contains extensions to Atom objects used with Google Spreadsheets.
"""

__author__ = 'api.laurabeth@gmail.com (Laura Beth Lincoln)'


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
import re
import string


# XML namespaces which are often used in Google Spreadsheets entities.
GSPREADSHEETS_NAMESPACE = 'http://schemas.google.com/spreadsheets/2006'
GSPREADSHEETS_TEMPLATE = '{http://schemas.google.com/spreadsheets/2006}%s'

GSPREADSHEETS_EXTENDED_NAMESPACE = ('http://schemas.google.com/spreadsheets'
                                    '/2006/extended')
GSPREADSHEETS_EXTENDED_TEMPLATE = ('{http://schemas.google.com/spreadsheets'
                                   '/2006/extended}%s')


class ColCount(atom.AtomBase):
  """The Google Spreadsheets colCount element """
  
  _tag = 'colCount'
  _namespace = GSPREADSHEETS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, text=None, extension_elements=None,
      extension_attributes=None):
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

    
def ColCountFromString(xml_string):
  return atom.CreateClassFromXMLString(ColCount, xml_string)


class RowCount(atom.AtomBase):
  """The Google Spreadsheets rowCount element """
  
  _tag = 'rowCount'
  _namespace = GSPREADSHEETS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, text=None, extension_elements=None,
      extension_attributes=None):
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

def RowCountFromString(xml_string):
  return atom.CreateClassFromXMLString(RowCount, xml_string)
      

class Cell(atom.AtomBase):
  """The Google Spreadsheets cell element """
  
  _tag = 'cell'
  _namespace = GSPREADSHEETS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['row'] = 'row'
  _attributes['col'] = 'col'
  _attributes['inputValue'] = 'inputValue'
  _attributes['numericValue'] = 'numericValue'
  
  def __init__(self, text=None, row=None, col=None, inputValue=None, 
      numericValue=None, extension_elements=None, extension_attributes=None):
    self.text = text
    self.row = row
    self.col = col
    self.inputValue = inputValue
    self.numericValue = numericValue
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def CellFromString(xml_string):
  return atom.CreateClassFromXMLString(Cell, xml_string)


class Custom(atom.AtomBase):
  """The Google Spreadsheets custom element"""
  
  _namespace = GSPREADSHEETS_EXTENDED_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, column=None, text=None, extension_elements=None,
      extension_attributes=None):
    self.column = column   # The name of the column
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    
  def _BecomeChildElement(self, tree):
    new_child = ElementTree.Element('')
    tree.append(new_child)
    new_child.tag = '{%s}%s' % (self.__class__._namespace, 
                                self.column)
    self._AddMembersToElementTree(new_child)
  
  def _ToElementTree(self):
    new_tree = ElementTree.Element('{%s}%s' % (self.__class__._namespace,
                                               self.column))
    self._AddMembersToElementTree(new_tree)
    return new_tree
    
  def _HarvestElementTree(self, tree):
    namespace_uri, local_tag = string.split(tree.tag[1:], "}", 1)
    self.column = local_tag
    # Fill in the instance members from the contents of the XML tree.
    for child in tree:
      self._ConvertElementTreeToMember(child)
    for attribute, value in tree.attrib.iteritems():
      self._ConvertElementAttributeToMember(attribute, value)
    self.text = tree.text


def CustomFromString(xml_string):
  element_tree = ElementTree.fromstring(xml_string)
  return _CustomFromElementTree(element_tree)

  
def _CustomFromElementTree(element_tree):
  namespace_uri, local_tag = string.split(element_tree.tag[1:], "}", 1)
  if namespace_uri == GSPREADSHEETS_EXTENDED_NAMESPACE:
    new_custom = Custom()
    new_custom._HarvestElementTree(element_tree)
    new_custom.column = local_tag
    return new_custom
  return None

  


                                                  
class SpreadsheetsSpreadsheet(gdata.GDataEntry):
  """A Google Spreadsheets flavor of a Spreadsheet Atom Entry """
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  
  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, control=None, updated=None,
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
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    
    
def SpreadsheetsSpreadsheetFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsSpreadsheet, 
                                       xml_string)


class SpreadsheetsWorksheet(gdata.GDataEntry):
  """A Google Spreadsheets flavor of a Worksheet Atom Entry """
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}rowCount' % GSPREADSHEETS_NAMESPACE] = ('row_count', 
                                                         RowCount)
  _children['{%s}colCount' % GSPREADSHEETS_NAMESPACE] = ('col_count', 
                                                         ColCount)
  
  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, control=None, updated=None, 
      row_count=None, col_count=None, text=None, extension_elements=None, 
      extension_attributes=None):
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
    self.row_count = row_count
    self.col_count = col_count
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

    
def SpreadsheetsWorksheetFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsWorksheet, 
                                       xml_string)


class SpreadsheetsCell(gdata.BatchEntry):
  """A Google Spreadsheets flavor of a Cell Atom Entry """
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchEntry._children.copy()
  _attributes = gdata.BatchEntry._attributes.copy()
  _children['{%s}cell' % GSPREADSHEETS_NAMESPACE] = ('cell', Cell)
  
  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, control=None, updated=None, 
      cell=None, batch_operation=None, batch_id=None, batch_status=None,
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
    self.batch_operation = batch_operation
    self.batch_id = batch_id
    self.batch_status = batch_status
    self.updated = updated
    self.cell = cell
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def SpreadsheetsCellFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsCell, 
                                       xml_string)

                                       
class SpreadsheetsList(gdata.GDataEntry):
  """A Google Spreadsheets flavor of a List Atom Entry """
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  
  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, title=None, control=None, updated=None, 
      custom=None, 
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
    self.custom = custom or {}
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    
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
    elif child_tree.tag.find('{%s}' % GSPREADSHEETS_EXTENDED_NAMESPACE) == 0:
      # If this is in the custom namespace, make add it to the custom dict.
      name = child_tree.tag[child_tree.tag.index('}')+1:]
      custom = _CustomFromElementTree(child_tree)
      if custom:
        self.custom[name] = custom
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
    for name, custom in self.custom.iteritems():
      custom._BecomeChildElement(tree)
    # Lastly, call the ExtensionContainers's _AddMembersToElementTree to 
    # convert any extension attributes.
    atom.ExtensionContainer._AddMembersToElementTree(self, tree)

  
def SpreadsheetsListFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsList, 
                                       xml_string)
  element_tree = ElementTree.fromstring(xml_string)
  return _SpreadsheetsListFromElementTree(element_tree)


class SpreadsheetsSpreadsheetsFeed(gdata.GDataFeed):
  """A feed containing Google Spreadsheets Spreadsheets"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [SpreadsheetsSpreadsheet])


def SpreadsheetsSpreadsheetsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsSpreadsheetsFeed, 
                                       xml_string)
                                       
      
class SpreadsheetsWorksheetsFeed(gdata.GDataFeed):
  """A feed containing Google Spreadsheets Spreadsheets"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [SpreadsheetsWorksheet])


def SpreadsheetsWorksheetsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsWorksheetsFeed, 
                                       xml_string)


class SpreadsheetsCellsFeed(gdata.BatchFeed):
  """A feed containing Google Spreadsheets Cells"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _attributes = gdata.BatchFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [SpreadsheetsCell])
  _children['{%s}rowCount' % GSPREADSHEETS_NAMESPACE] = ('row_count', 
                                                         RowCount)
  _children['{%s}colCount' % GSPREADSHEETS_NAMESPACE] = ('col_count', 
                                                         ColCount)
                                                  
  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None, 
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None, row_count=None,
               col_count=None, interrupted=None):
    gdata.BatchFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text, interrupted=interrupted)
    self.row_count = row_count
    self.col_count = col_count

  def GetBatchLink(self):
    for link in self.link:
      if link.rel == 'http://schemas.google.com/g/2005#batch':
        return link
    return None


def SpreadsheetsCellsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsCellsFeed, 
                                       xml_string)

      
class SpreadsheetsListFeed(gdata.GDataFeed):
  """A feed containing Google Spreadsheets Spreadsheets"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [SpreadsheetsList])


def SpreadsheetsListFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SpreadsheetsListFeed, 
                                       xml_string)
