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


"""Contains a client to communicate with the Google Spreadsheets servers.

For documentation on the Spreadsheets API, see:
http://code.google.com/apis/spreadsheets/
"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import gdata.client
import gdata.gauth
import gdata.spreadsheets.data
import atom.data
import atom.http_core


SPREADSHEETS_URL = ('https://spreadsheets.google.com/feeds/spreadsheets'
                    '/private/full')
WORKSHEETS_URL = ('https://spreadsheets.google.com/feeds/worksheets/'
                  '%s/private/full')
WORKSHEET_URL = ('https://spreadsheets.google.com/feeds/worksheets/'
                 '%s/private/full/%s')
TABLES_URL = 'https://spreadsheets.google.com/feeds/%s/tables'
RECORDS_URL = 'https://spreadsheets.google.com/feeds/%s/records/%s'
RECORD_URL = 'https://spreadsheets.google.com/feeds/%s/records/%s/%s'
CELLS_URL = 'https://spreadsheets.google.com/feeds/cells/%s/%s/private/full'
CELL_URL = ('https://spreadsheets.google.com/feeds/cells/%s/%s/private/full/'
            'R%sC%s')
LISTS_URL = 'https://spreadsheets.google.com/feeds/list/%s/%s/private/full'


class SpreadsheetsClient(gdata.client.GDClient):
  api_version = '3'
  auth_service = 'wise'
  auth_scopes = gdata.gauth.AUTH_SCOPES['wise']
  ssl = True

  def get_spreadsheets(self, auth_token=None,
                       desired_class=gdata.spreadsheets.data.SpreadsheetsFeed,
                       **kwargs):
    """Obtains a feed with the spreadsheets belonging to the current user.

    Args:
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.SpreadsheetsFeed.
    """
    return self.get_feed(SPREADSHEETS_URL, auth_token=auth_token,
                         desired_class=desired_class, **kwargs)

  GetSpreadsheets = get_spreadsheets

  def get_worksheets(self, spreadsheet_key, auth_token=None,
                     desired_class=gdata.spreadsheets.data.WorksheetsFeed,
                     **kwargs):
    """Finds the worksheets within a given spreadsheet.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.WorksheetsFeed.
    """
    return self.get_feed(WORKSHEETS_URL % spreadsheet_key,
                         auth_token=auth_token, desired_class=desired_class,
                         **kwargs)

  GetWorksheets = get_worksheets

  def add_worksheet(self, spreadsheet_key, title, rows, cols,
                    auth_token=None, **kwargs):
    """Creates a new worksheet entry in the spreadsheet.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      title: str, The title to be used in for the worksheet.
      rows: str or int, The number of rows this worksheet should start with.
      cols: str or int, The number of columns this worksheet should start with.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    new_worksheet = gdata.spreadsheets.data.WorksheetEntry(
        title=atom.data.Title(text=title),
        row_count=gdata.spreadsheets.data.RowCount(text=str(rows)),
        col_count=gdata.spreadsheets.data.ColCount(text=str(cols)))
    return self.post(new_worksheet, WORKSHEETS_URL % spreadsheet_key,
                     auth_token=auth_token, **kwargs)

  AddWorksheet = add_worksheet

  def get_worksheet(self, spreadsheet_key, worksheet_id,
                    desired_class=gdata.spreadsheets.data.WorksheetEntry,
                    auth_token=None, **kwargs):
    """Retrieves a single worksheet.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      worksheet_id: str, The unique ID for the worksheet withing the desired
                    spreadsheet.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.WorksheetEntry.

    """
    return self.get_entry(WORKSHEET_URL % (spreadsheet_key, worksheet_id,),
                          auth_token=auth_token, desired_class=desired_class,
                          **kwargs)

  GetWorksheet = get_worksheet

  def add_table(self, spreadsheet_key, title, summary, worksheet_name,
                header_row, num_rows, start_row, insertion_mode,
                column_headers, auth_token=None, **kwargs):
    """Creates a new table within the worksheet.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      title: str, The title for the new table within a worksheet.
      summary: str, A description of the table.
      worksheet_name: str The name of the worksheet in which this table
                      should live.
      header_row: int or str, The number of the row in the worksheet which
                  will contain the column names for the data in this table.
      num_rows: int or str, The number of adjacent rows in this table.
      start_row: int or str, The number of the row at which the data begins.
      insertion_mode: str
      column_headers: dict of strings, maps the column letters (A, B, C) to
                      the desired name which will be viewable in the
                      worksheet.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    data = gdata.spreadsheets.data.Data(
        insertion_mode=insertion_mode, num_rows=str(num_rows),
        start_row=str(start_row))
    for index, name in column_headers.iteritems():
      data.column.append(gdata.spreadsheets.data.Column(
          index=index, name=name))
    new_table = gdata.spreadsheets.data.Table(
        title=atom.data.Title(text=title), summary=atom.data.Summary(summary),
        worksheet=gdata.spreadsheets.data.Worksheet(name=worksheet_name),
        header=gdata.spreadsheets.data.Header(row=str(header_row)), data=data)
    return self.post(new_table, TABLES_URL % spreadsheet_key,
                     auth_token=auth_token, **kwargs)

  AddTable = add_table

  def get_tables(self, spreadsheet_key,
                 desired_class=gdata.spreadsheets.data.TablesFeed,
                 auth_token=None, **kwargs):
    """Retrieves a feed listing the tables in this spreadsheet.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.TablesFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_feed(TABLES_URL % spreadsheet_key,
                         desired_class=desired_class, auth_token=auth_token,
                         **kwargs)

  GetTables = get_tables

  def add_record(self, spreadsheet_key, table_id, fields,
                 title=None, auth_token=None, **kwargs):
    """Adds a new row to the table.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      table_id: str, The ID of the table within the worksheet which should
                receive this new record. The table ID can be found using the
                get_table_id method of a gdata.spreadsheets.data.Table.
      fields: dict of strings mapping column names to values.
      title: str, optional The title for this row.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    new_record = gdata.spreadsheets.data.Record()
    if title is not None:
      new_record.title = atom.data.Title(text=title)
    for name, value in fields.iteritems():
      new_record.field.append(gdata.spreadsheets.data.Field(
          name=name, text=value))
    return self.post(new_record, RECORDS_URL % (spreadsheet_key, table_id),
                     auth_token=auth_token, **kwargs)

  AddRecord = add_record

  def get_records(self, spreadsheet_key, table_id,
                  desired_class=gdata.spreadsheets.data.RecordsFeed,
                  auth_token=None, **kwargs):
    """Retrieves the records in a table.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      table_id: str, The ID of the table within the worksheet whose records
                we would like to fetch. The table ID can be found using the
                get_table_id method of a gdata.spreadsheets.data.Table.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.RecordsFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_feed(RECORDS_URL % (spreadsheet_key, table_id),
                         desired_class=desired_class, auth_token=auth_token,
                         **kwargs)

  GetRecords = get_records

  def get_record(self, spreadsheet_key, table_id, record_id,
                 desired_class=gdata.spreadsheets.data.Record,
                 auth_token=None, **kwargs):
    """Retrieves a single record from the table.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      table_id: str, The ID of the table within the worksheet whose records
                we would like to fetch. The table ID can be found using the
                get_table_id method of a gdata.spreadsheets.data.Table.
      record_id: str, The ID of the record within this table which we want to
                 fetch. You can find the record ID using get_record_id() on
                 an instance of the gdata.spreadsheets.data.Record class.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.RecordsFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_entry(RECORD_URL % (spreadsheet_key, table_id, record_id),
                          desired_class=desired_class, auth_token=auth_token,
                          **kwargs)

  GetRecord = get_record

  def get_cells(self, spreadsheet_key, worksheet_id,
                desired_class=gdata.spreadsheets.data.CellsFeed,
                auth_token=None, **kwargs):
    """Retrieves the cells which have values in this spreadsheet.

    Blank cells are not included.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      worksheet_id: str, The unique ID of the worksheet in this spreadsheet
                    whose cells we want. This can be obtained using
                    WorksheetEntry's get_worksheet_id method.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.CellsFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_feed(CELLS_URL % (spreadsheet_key, worksheet_id),
                         auth_token=auth_token, desired_class=desired_class,
                         **kwargs)

  GetCells = get_cells

  def get_cell(self, spreadsheet_key, worksheet_id, row_num, col_num,
               desired_class=gdata.spreadsheets.data.CellEntry,
               auth_token=None, **kwargs):
    """Retrieves a single cell from the worksheet.
    
    Indexes are 1 based so the first cell in the worksheet is 1, 1.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      worksheet_id: str, The unique ID of the worksheet in this spreadsheet
                    whose cells we want. This can be obtained using
                    WorksheetEntry's get_worksheet_id method.
      row_num: int, The row of the cell that we want. Numbering starts with 1.
      col_num: int, The column of the cell we want. Numbering starts with 1.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.CellEntry.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_entry(
        CELL_URL % (spreadsheet_key, worksheet_id, row_num, col_num),
        auth_token=auth_token, desired_class=desired_class, **kwargs)

  GetCell = get_cell

  def get_list_feed(self, spreadsheet_key, worksheet_id,
                    desired_class=gdata.spreadsheets.data.ListsFeed,
                    auth_token=None, **kwargs):
    """Retrieves the value rows from the worksheet's list feed.
    
    The list feed is a view of the spreadsheet in which the first row is used
    for column names and subsequent rows up to the first blank line are
    records.

    Args:
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      worksheet_id: str, The unique ID of the worksheet in this spreadsheet
                    whose cells we want. This can be obtained using
                    WorksheetEntry's get_worksheet_id method.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (converter=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.ListsFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_feed(LISTS_URL % (spreadsheet_key, worksheet_id),
                         auth_token=auth_token, desired_class=desired_class,
                         **kwargs)

  GetListFeed = get_list_feed
                    
  def add_list_entry(self, list_entry, spreadsheet_key, worksheet_id,
                     auth_token=None, **kwargs):
    """Adds a new row to the worksheet's list feed.

    Args:
      list_entry: gdata.spreadsheets.data.ListsEntry An entry which contains
                  the values which should be set for the columns in this
                  record.
      spreadsheet_key: str, The unique ID of this containing spreadsheet. This
                       can be the ID from the URL or as provided in a
                       Spreadsheet entry.
      worksheet_id: str, The unique ID of the worksheet in this spreadsheet
                    whose cells we want. This can be obtained using
                    WorksheetEntry's get_worksheet_id method.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.post(list_entry, LISTS_URL % (spreadsheet_key, worksheet_id),
                     auth_token=auth_token, **kwargs)

  AddListEntry = add_list_entry


class SpreadsheetQuery(gdata.client.Query):

  def __init__(self, title=None, title_exact=None, **kwargs):
    """Adds Spreadsheets feed query parameters to a request.

    Args:
      title: str Specifies the search terms for the title of a document.
             This parameter used without title-exact will only submit partial
             queries, not exact queries.
      title_exact: str Specifies whether the title query should be taken as an
                   exact string. Meaningless without title. Possible values are
                   'true' and 'false'.
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.title = title
    self.title_exact = title_exact

  def modify_request(self, http_request):
    gdata.client._add_query_param('title', self.title, http_request)
    gdata.client._add_query_param('title-exact', self.title_exact,
                                  http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request


class WorksheetQuery(SpreadsheetQuery):
  pass


class ListQuery(gdata.client.Query):

  def __init__(self, order_by=None, reverse=None, sq=None, **kwargs):
    """Adds List-feed specific query parameters to a request.

    Args:
      order_by: str Specifies what column to use in ordering the entries in
                the feed. By position (the default): 'position' returns
                rows in the order in which they appear in the GUI. Row 1, then
                row 2, then row 3, and so on. By column:
                'column:columnName' sorts rows in ascending order based on the
                values in the column with the given columnName, where
                columnName is the value in the header row for that column.
      reverse: str Specifies whether to sort in descending or ascending order.
               Reverses default sort order: 'true' results in a descending
               sort; 'false' (the default) results in an ascending sort.
      sq: str Structured query on the full text in the worksheet.
          [columnName][binaryOperator][value]
          Supported binaryOperators are:
          - (), for overriding order of operations
          - = or ==, for strict equality
          - <> or !=, for strict inequality
          - and or &&, for boolean and
          - or or ||, for boolean or
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.order_by = order_by
    self.reverse = reverse
    self.sq = sq

  def modify_request(self, http_request):
    gdata.client._add_query_param('orderby', self.order_by, http_request)
    gdata.client._add_query_param('reverse', self.reverse, http_request)
    gdata.client._add_query_param('sq', self.sq, http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request


class TableQuery(ListQuery):
  pass


class CellQuery(gdata.client.Query):

  def __init__(self, min_row=None, max_row=None, min_col=None, max_col=None,
               range=None, return_empty=None, **kwargs):
    """Adds Cells-feed specific query parameters to a request.

    Args:
      min_row: str or int Positional number of minimum row returned in query.
      max_row: str or int Positional number of maximum row returned in query.
      min_col: str or int Positional number of minimum column returned in query.
      max_col: str or int Positional number of maximum column returned in query.
      range: str A single cell or a range of cells. Use standard spreadsheet
             cell-range notations, using a colon to separate start and end of
             range. Examples:
             - 'A1' and 'R1C1' both specify only cell A1.
             - 'D1:F3' and 'R1C4:R3C6' both specify the rectangle of cells with
               corners at D1 and F3.
      return_empty: str If 'true' then empty cells will be returned in the feed.
                    If omitted, the default is 'false'.
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.min_row = min_row
    self.max_row = max_row
    self.min_col = min_col
    self.max_col = max_col
    self.range = range
    self.return_empty = return_empty

  def modify_request(self, http_request):
    gdata.client._add_query_param('min-row', self.min_row, http_request)
    gdata.client._add_query_param('max-row', self.max_row, http_request)
    gdata.client._add_query_param('min-col', self.min_col, http_request)
    gdata.client._add_query_param('max-col', self.max_col, http_request)
    gdata.client._add_query_param('range', self.range, http_request)
    gdata.client._add_query_param('return-empty', self.return_empty,
                                  http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request
