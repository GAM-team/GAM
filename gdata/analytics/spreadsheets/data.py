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


"""Provides classes and constants for the XML in the Google Spreadsheets API.

Documentation for the raw XML which these classes represent can be found here:
http://code.google.com/apis/spreadsheets/docs/3.0/reference.html#Elements
"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import gdata.data


GS_TEMPLATE = '{http://schemas.google.com/spreadsheets/2006}%s'
GSX_NAMESPACE = 'http://schemas.google.com/spreadsheets/2006/extended'


INSERT_MODE = 'insert'
OVERWRITE_MODE = 'overwrite'


WORKSHEETS_REL = 'http://schemas.google.com/spreadsheets/2006#worksheetsfeed'


class Error(Exception):
  pass


class FieldMissing(Exception):
  pass


class HeaderNotSet(Error):
  """The desired column header had no value for the row in the list feed."""


class Cell(atom.core.XmlElement):
  """The gs:cell element.

  A cell in the worksheet. The <gs:cell> element can appear only as a child
  of <atom:entry>.
  """
  _qname = GS_TEMPLATE % 'cell'
  col = 'col'
  input_value = 'inputValue'
  numeric_value = 'numericValue'
  row = 'row'


class ColCount(atom.core.XmlElement):
  """The gs:colCount element.

  Indicates the number of columns in the worksheet, including columns that
  contain only empty cells. The <gs:colCount> element can appear as a child
  of <atom:entry> or <atom:feed>
  """
  _qname = GS_TEMPLATE % 'colCount'


class Field(atom.core.XmlElement):
  """The gs:field element.

  A field single cell within a record. Contained in an <atom:entry>.
  """
  _qname = GS_TEMPLATE % 'field'
  index = 'index'
  name = 'name'


class Column(Field):
  """The gs:column element."""
  _qname = GS_TEMPLATE % 'column'


class Data(atom.core.XmlElement):
  """The gs:data element.

  A data region of a table. Contained in an <atom:entry> element.
  """
  _qname = GS_TEMPLATE % 'data'
  column = [Column]
  insertion_mode = 'insertionMode'
  num_rows = 'numRows'
  start_row = 'startRow'


class Header(atom.core.XmlElement):
  """The gs:header element.

  Indicates which row is the header row. Contained in an <atom:entry>.
  """
  _qname = GS_TEMPLATE % 'header'
  row = 'row'


class RowCount(atom.core.XmlElement):
  """The gs:rowCount element.

  Indicates the number of total rows in the worksheet, including rows that
  contain only empty cells. The <gs:rowCount> element can appear as a
  child of <atom:entry> or <atom:feed>.
  """
  _qname = GS_TEMPLATE % 'rowCount'


class Worksheet(atom.core.XmlElement):
  """The gs:worksheet element.

  The worksheet where the table lives.Contained in an <atom:entry>.
  """
  _qname = GS_TEMPLATE % 'worksheet'
  name = 'name'


class Spreadsheet(gdata.data.GDEntry):
  """An Atom entry which represents a Google Spreadsheet."""

  def find_worksheets_feed(self):
    return self.find_url(WORKSHEETS_REL)

  FindWorksheetsFeed = find_worksheets_feed

  def get_spreadsheet_key(self):
    """Extracts the spreadsheet key unique to this spreadsheet."""
    return self.get_id().split('/')[-1]

  GetSpreadsheetKey = get_spreadsheet_key


class SpreadsheetsFeed(gdata.data.GDFeed):
  """An Atom feed listing a user's Google Spreadsheets."""
  entry = [Spreadsheet]


class WorksheetEntry(gdata.data.GDEntry):
  """An Atom entry representing a single worksheet in a spreadsheet."""
  row_count = RowCount
  col_count = ColCount

  def get_worksheet_id(self):
    """The worksheet ID identifies this worksheet in its spreadsheet."""
    return self.get_id().split('/')[-1]

  GetWorksheetId = get_worksheet_id


class WorksheetsFeed(gdata.data.GDFeed):
  """A feed containing the worksheets in a single spreadsheet."""
  entry = [WorksheetEntry]


class Table(gdata.data.GDEntry):
  """An Atom entry that represents a subsection of a worksheet.

  A table allows you to treat part or all of a worksheet somewhat like a
  table in a database that is, as a set of structured data items. Tables
  don't exist until you explicitly create them before you can use a table
  feed, you have to explicitly define where the table data comes from.
  """
  data = Data
  header = Header
  worksheet = Worksheet

  def get_table_id(self):
    if self.id.text:
      return self.id.text.split('/')[-1]
    return None

  GetTableId = get_table_id


class TablesFeed(gdata.data.GDFeed):
  """An Atom feed containing the tables defined within a worksheet."""
  entry = [Table]


class Record(gdata.data.GDEntry):
  """An Atom entry representing a single record in a table.

  Note that the order of items in each record is the same as the order of
  columns in the table definition, which may not match the order of
  columns in the GUI.
  """
  field = [Field]

  def value_for_index(self, column_index):
    for field in self.field:
      if field.index == column_index:
        return field.text
    raise FieldMissing('There is no field for %s' % column_index)

  ValueForIndex = value_for_index

  def value_for_name(self, name):
    for field in self.field:
      if field.name == name:
        return field.text
    raise FieldMissing('There is no field for %s' % name)

  ValueForName = value_for_name

  def get_record_id(self):
    if self.id.text:
      return self.id.text.split('/')[-1]
    return None


class RecordsFeed(gdata.data.GDFeed):
  """An Atom feed containing the individuals records in a table."""
  entry = [Record]


class ListRow(atom.core.XmlElement):
  """A gsx column value within a row.

  The local tag in the _qname is blank and must be set to the column
  name. For example, when adding to a ListEntry, do:
  col_value = ListRow(text='something')
  col_value._qname = col_value._qname % 'mycolumnname'
  """
  _qname = '{http://schemas.google.com/spreadsheets/2006/extended}%s'


class ListEntry(gdata.data.GDEntry):
  """An Atom entry representing a worksheet row in the list feed.

  The values for a particular column can be get and set using
  x.get_value('columnheader') and x.set_value('columnheader', 'value').
  See also the explanation of column names in the ListFeed class.
  """

  def get_value(self, column_name):
    """Returns the displayed text for the desired column in this row.

    The formula or input which generated the displayed value is not accessible
    through the list feed, to see the user's input, use the cells feed.

    If a column is not present in this spreadsheet, or there is no value
    for a column in this row, this method will return None.
    """
    values = self.get_elements(column_name, GSX_NAMESPACE)
    if len(values) == 0:
      return None
    return values[0].text

  def set_value(self, column_name, value):
    """Changes the value of cell in this row under the desired column name.

    Warning: if the cell contained a formula, it will be wiped out by setting
    the value using the list feed since the list feed only works with
    displayed values.

    No client side checking is performed on the column_name, you need to
    ensure that the column_name is the local tag name in the gsx tag for the
    column. For example, the column_name will not contain special characters,
    spaces, uppercase letters, etc.
    """
    # Try to find the column in this row to change an existing value.
    values = self.get_elements(column_name, GSX_NAMESPACE)
    if len(values) > 0:
      values[0].text = value
    else:
      # There is no value in this row for the desired column, so add a new
      # gsx:column_name element.
      new_value = ListRow(text=value)
      new_value._qname = new_value._qname % (column_name,)
      self._other_elements.append(new_value)

  def to_dict(self):
    """Converts this row to a mapping of column names to their values."""
    result = {}
    values = self.get_elements(namespace=GSX_NAMESPACE)
    for item in values:
      result[item._get_tag()] = item.text
    return result

  def from_dict(self, values):
    """Sets values for this row from the dictionary.
    
    Old values which are already in the entry will not be removed unless
    they are overwritten with new values from the dict.
    """
    for column, value in values.iteritems():
      self.set_value(column, value)


class ListsFeed(gdata.data.GDFeed):
  """An Atom feed in which each entry represents a row in a worksheet.

  The first row in the worksheet is used as the column names for the values
  in each row. If a header cell is empty, then a unique column ID is used
  for the gsx element name.

  Spaces in a column name are removed from the name of the corresponding
  gsx element.

  Caution: The columnNames are case-insensitive. For example, if you see
  a <gsx:e-mail> element in a feed, you can't know whether the column
  heading in the original worksheet was "e-mail" or "E-Mail".

  Note: If two or more columns have the same name, then subsequent columns
  of the same name have _n appended to the columnName. For example, if the
  first column name is "e-mail", followed by columns named "E-Mail" and
  "E-mail", then the columnNames will be gsx:e-mail, gsx:e-mail_2, and
  gsx:e-mail_3 respectively.
  """
  entry = [ListEntry]


class CellEntry(gdata.data.BatchEntry):
  """An Atom entry representing a single cell in a worksheet."""
  cell = Cell


class CellsFeed(gdata.data.BatchFeed):
  """An Atom feed contains one entry per cell in a worksheet.

  The cell feed supports batch operations, you can send multiple cell
  operations in one HTTP request.
  """
  entry = [CellEntry]

  def batch_set_cell(row, col, input):
    pass

