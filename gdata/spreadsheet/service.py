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

"""SpreadsheetsService extends the GDataService to streamline Google
Spreadsheets operations.

  SpreadsheetService: Provides methods to query feeds and manipulate items.
                      Extends GDataService.

  DictionaryToParamList: Function which converts a dictionary into a list of
                         URL arguments (represented as strings). This is a
                         utility function used in CRUD operations.
"""

__author__ = 'api.laurabeth@gmail.com (Laura Beth Lincoln)'


import gdata
import atom.service
import gdata.service
import gdata.spreadsheet
import atom


class Error(Exception):
  """Base class for exceptions in this module."""
  pass


class RequestError(Error):
  pass


class SpreadsheetsService(gdata.service.GDataService):
  """Client for the Google Spreadsheets service."""

  def __init__(self, email=None, password=None, source=None,
               server='spreadsheets.google.com', additional_headers=None,
               **kwargs):
    """Creates a client for the Google Spreadsheets service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'spreadsheets.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='wise', source=source,
        server=server, additional_headers=additional_headers, **kwargs)

  def GetSpreadsheetsFeed(self, key=None, query=None, visibility='private', 
      projection='full'):
    """Gets a spreadsheets feed or a specific entry if a key is defined
    Args:
      key: string (optional) The spreadsheet key defined in /ccc?key=
      query: DocumentQuery (optional) Query parameters
      
    Returns:
      If there is no key, then a SpreadsheetsSpreadsheetsFeed.
      If there is a key, then a SpreadsheetsSpreadsheet.
    """
    
    uri = ('http://%s/feeds/spreadsheets/%s/%s' 
           % (self.server, visibility, projection))
    
    if key is not None:
      uri = '%s/%s' % (uri, key)
      
    if query != None:
      query.feed = uri
      uri = query.ToUri()

    if key:
      return self.Get(uri, 
          converter=gdata.spreadsheet.SpreadsheetsSpreadsheetFromString)
    else:
      return self.Get(uri,
          converter=gdata.spreadsheet.SpreadsheetsSpreadsheetsFeedFromString)
  
  def GetWorksheetsFeed(self, key, wksht_id=None, query=None, 
      visibility='private', projection='full'):
    """Gets a worksheets feed or a specific entry if a wksht is defined
    Args:
      key: string The spreadsheet key defined in /ccc?key=
      wksht_id: string (optional) The id for a specific worksheet entry
      query: DocumentQuery (optional) Query parameters
      
    Returns:
      If there is no wksht_id, then a SpreadsheetsWorksheetsFeed.
      If there is a wksht_id, then a SpreadsheetsWorksheet.
    """
    
    uri = ('http://%s/feeds/worksheets/%s/%s/%s' 
           % (self.server, key, visibility, projection))
    
    if wksht_id != None:
      uri = '%s/%s' % (uri, wksht_id)
      
    if query != None:
      query.feed = uri
      uri = query.ToUri()

    if wksht_id:
      return self.Get(uri, 
          converter=gdata.spreadsheet.SpreadsheetsWorksheetFromString)
    else:
      return self.Get(uri,
          converter=gdata.spreadsheet.SpreadsheetsWorksheetsFeedFromString)

  def AddWorksheet(self, title, row_count, col_count, key):
    """Creates a new worksheet in the desired spreadsheet.

    The new worksheet is appended to the end of the list of worksheets. The
    new worksheet will only have the available number of columns and cells 
    specified.

    Args:
      title: str The title which will be displayed in the list of worksheets.
      row_count: int or str The number of rows in the new worksheet.
      col_count: int or str The number of columns in the new worksheet.
      key: str The spreadsheet key to the spreadsheet to which the new 
          worksheet should be added. 

    Returns:
      A SpreadsheetsWorksheet if the new worksheet was created succesfully.  
    """
    new_worksheet = gdata.spreadsheet.SpreadsheetsWorksheet(
        title=atom.Title(text=title), 
        row_count=gdata.spreadsheet.RowCount(text=str(row_count)), 
        col_count=gdata.spreadsheet.ColCount(text=str(col_count)))
    return self.Post(new_worksheet, 
        'http://%s/feeds/worksheets/%s/private/full' % (self.server, key),
        converter=gdata.spreadsheet.SpreadsheetsWorksheetFromString)

  def UpdateWorksheet(self, worksheet_entry, url=None):
    """Changes the size and/or title of the desired worksheet.
    
    Args:
      worksheet_entry: SpreadsheetWorksheet The new contents of the 
          worksheet. 
      url: str (optional) The URL to which the edited worksheet entry should
          be sent. If the url is None, the edit URL from the worksheet will
          be used.

    Returns: 
      A SpreadsheetsWorksheet with the new information about the worksheet.
    """
    target_url = url or worksheet_entry.GetEditLink().href
    return self.Put(worksheet_entry, target_url, 
        converter=gdata.spreadsheet.SpreadsheetsWorksheetFromString)
    
  def DeleteWorksheet(self, worksheet_entry=None, url=None):
    """Removes the desired worksheet from the spreadsheet
    
    Args:
      worksheet_entry: SpreadsheetWorksheet (optional) The worksheet to
          be deleted. If this is none, then the DELETE reqest is sent to 
          the url specified in the url parameter.
      url: str (optaional) The URL to which the DELETE request should be
          sent. If left as None, the worksheet's edit URL is used.

    Returns:
      True if the worksheet was deleted successfully. 
    """
    if url:
      target_url = url
    else:
      target_url = worksheet_entry.GetEditLink().href
    return self.Delete(target_url)
  
  def GetCellsFeed(self, key, wksht_id='default', cell=None, query=None, 
      visibility='private', projection='full'):
    """Gets a cells feed or a specific entry if a cell is defined
    Args:
      key: string The spreadsheet key defined in /ccc?key=
      wksht_id: string The id for a specific worksheet entry
      cell: string (optional) The R1C1 address of the cell
      query: DocumentQuery (optional) Query parameters
      
    Returns:
      If there is no cell, then a SpreadsheetsCellsFeed.
      If there is a cell, then a SpreadsheetsCell.
    """
    
    uri = ('http://%s/feeds/cells/%s/%s/%s/%s' 
           % (self.server, key, wksht_id, visibility, projection))
    
    if cell != None:
      uri = '%s/%s' % (uri, cell)
      
    if query != None:
      query.feed = uri
      uri = query.ToUri()

    if cell:
      return self.Get(uri, 
          converter=gdata.spreadsheet.SpreadsheetsCellFromString)
    else:
      return self.Get(uri, 
          converter=gdata.spreadsheet.SpreadsheetsCellsFeedFromString)
  
  def GetListFeed(self, key, wksht_id='default', row_id=None, query=None,
      visibility='private', projection='full'):
    """Gets a list feed or a specific entry if a row_id is defined
    Args:
      key: string The spreadsheet key defined in /ccc?key=
      wksht_id: string The id for a specific worksheet entry
      row_id: string (optional) The row_id of a row in the list
      query: DocumentQuery (optional) Query parameters
      
    Returns:
      If there is no row_id, then a SpreadsheetsListFeed.
      If there is a row_id, then a SpreadsheetsList.
    """
    
    uri = ('http://%s/feeds/list/%s/%s/%s/%s' 
           % (self.server, key, wksht_id, visibility, projection))

    if row_id is not None:
      uri = '%s/%s' % (uri, row_id)
      
    if query is not None:
      query.feed = uri
      uri = query.ToUri()

    if row_id:
      return self.Get(uri, 
          converter=gdata.spreadsheet.SpreadsheetsListFromString)
    else:
      return self.Get(uri, 
          converter=gdata.spreadsheet.SpreadsheetsListFeedFromString)
    
  def UpdateCell(self, row, col, inputValue, key, wksht_id='default'):
    """Updates an existing cell.
    
    Args:
      row: int The row the cell to be editted is in
      col: int The column the cell to be editted is in
      inputValue: str the new value of the cell
      key: str The key of the spreadsheet in which this cell resides.
      wksht_id: str The ID of the worksheet which holds this cell.
      
    Returns:
      The updated cell entry
    """
    row = str(row)
    col = str(col)
    # make the new cell
    new_cell = gdata.spreadsheet.Cell(row=row, col=col, inputValue=inputValue)
    # get the edit uri and PUT
    cell = 'R%sC%s' % (row, col)
    entry = self.GetCellsFeed(key, wksht_id, cell)
    for a_link in entry.link:
      if a_link.rel == 'edit':
        entry.cell = new_cell
        return self.Put(entry, a_link.href, 
            converter=gdata.spreadsheet.SpreadsheetsCellFromString)

  def _GenerateCellsBatchUrl(self, spreadsheet_key, worksheet_id):
    return ('http://spreadsheets.google.com/feeds/cells/%s/%s/'
            'private/full/batch' % (spreadsheet_key, worksheet_id))

  def ExecuteBatch(self, batch_feed, url=None, spreadsheet_key=None, 
      worksheet_id=None,
      converter=gdata.spreadsheet.SpreadsheetsCellsFeedFromString):
    """Sends a batch request feed to the server.

    The batch request needs to be sent to the batch URL for a particular 
    worksheet. You can specify the worksheet by providing the spreadsheet_key
    and worksheet_id, or by sending the URL from the cells feed's batch link.

    Args:
      batch_feed: gdata.spreadsheet.SpreadsheetsCellFeed A feed containing 
          BatchEntry elements which contain the desired CRUD operation and 
          any necessary data to modify a cell.
      url: str (optional) The batch URL for the cells feed to which these 
          changes should be applied. This can be found by calling 
          cells_feed.GetBatchLink().href.
      spreadsheet_key: str (optional) Used to generate the batch request URL
          if the url argument is None. If using the spreadsheet key to 
          generate the URL, the worksheet id is also required.
      worksheet_id: str (optional) Used if the url is not provided, it is 
          oart of the batch feed target URL. This is used with the spreadsheet
          key.
      converter: Function (optional) Function to be executed on the server's
          response. This function should take one string as a parameter. The
          default value is SpreadsheetsCellsFeedFromString which will turn the result
          into a gdata.spreadsheet.SpreadsheetsCellsFeed object.

    Returns:
      A gdata.BatchFeed containing the results.
    """

    if url is None:
      url = self._GenerateCellsBatchUrl(spreadsheet_key, worksheet_id)
    return self.Post(batch_feed, url, converter=converter)
    
  def InsertRow(self, row_data, key, wksht_id='default'):
    """Inserts a new row with the provided data
    
    Args:
      uri: string The post uri of the list feed
      row_data: dict A dictionary of column header to row data
    
    Returns:
      The inserted row
    """
    new_entry = gdata.spreadsheet.SpreadsheetsList()
    for k, v in row_data.iteritems():
      new_custom = gdata.spreadsheet.Custom()
      new_custom.column = k
      new_custom.text = v
      new_entry.custom[new_custom.column] = new_custom
    # Generate the post URL for the worksheet which will receive the new entry.
    post_url = 'http://spreadsheets.google.com/feeds/list/%s/%s/private/full'%(
        key, wksht_id) 
    return self.Post(new_entry, post_url, 
        converter=gdata.spreadsheet.SpreadsheetsListFromString)
    
  def UpdateRow(self, entry, new_row_data):
    """Updates a row with the provided data

    If you want to add additional information to a row, it is often
    easier to change the values in entry.custom, then use the Put
    method instead of UpdateRow. This UpdateRow method will replace
    the contents of the row with new_row_data - it will change all columns
    not just the columns specified in the new_row_data dict.
    
    Args:
      entry: gdata.spreadsheet.SpreadsheetsList The entry to be updated
      new_row_data: dict A dictionary of column header to row data
      
    Returns:
      The updated row
    """
    entry.custom = {}
    for k, v in new_row_data.iteritems():
      new_custom = gdata.spreadsheet.Custom()
      new_custom.column = k
      new_custom.text = v
      entry.custom[k] = new_custom
    for a_link in entry.link:
      if a_link.rel == 'edit':
        return self.Put(entry, a_link.href, 
            converter=gdata.spreadsheet.SpreadsheetsListFromString)
        
  def DeleteRow(self, entry):
    """Deletes a row, the provided entry
    
    Args:
      entry: gdata.spreadsheet.SpreadsheetsList The row to be deleted
    
    Returns:
      The delete response
    """
    for a_link in entry.link:
      if a_link.rel == 'edit':
        return self.Delete(a_link.href)


class DocumentQuery(gdata.service.Query):

  def _GetTitleQuery(self):
    return self['title']

  def _SetTitleQuery(self, document_query):
    self['title'] = document_query
    
  title = property(_GetTitleQuery, _SetTitleQuery,
      doc="""The title query parameter""")

  def _GetTitleExactQuery(self):
    return self['title-exact']

  def _SetTitleExactQuery(self, document_query):
    self['title-exact'] = document_query
    
  title_exact = property(_GetTitleExactQuery, _SetTitleExactQuery,
      doc="""The title-exact query parameter""")
 
 
class CellQuery(gdata.service.Query):

  def _GetMinRowQuery(self):
    return self['min-row']

  def _SetMinRowQuery(self, cell_query):
    self['min-row'] = cell_query
    
  min_row = property(_GetMinRowQuery, _SetMinRowQuery,
      doc="""The min-row query parameter""")

  def _GetMaxRowQuery(self):
    return self['max-row']

  def _SetMaxRowQuery(self, cell_query):
    self['max-row'] = cell_query
    
  max_row = property(_GetMaxRowQuery, _SetMaxRowQuery,
      doc="""The max-row query parameter""")
      
  def _GetMinColQuery(self):
    return self['min-col']

  def _SetMinColQuery(self, cell_query):
    self['min-col'] = cell_query
    
  min_col = property(_GetMinColQuery, _SetMinColQuery,
      doc="""The min-col query parameter""")
      
  def _GetMaxColQuery(self):
    return self['max-col']

  def _SetMaxColQuery(self, cell_query):
    self['max-col'] = cell_query
    
  max_col = property(_GetMaxColQuery, _SetMaxColQuery,
      doc="""The max-col query parameter""")
      
  def _GetRangeQuery(self):
    return self['range']

  def _SetRangeQuery(self, cell_query):
    self['range'] = cell_query
    
  range = property(_GetRangeQuery, _SetRangeQuery,
      doc="""The range query parameter""")
      
  def _GetReturnEmptyQuery(self):
    return self['return-empty']

  def _SetReturnEmptyQuery(self, cell_query):
    self['return-empty'] = cell_query
    
  return_empty = property(_GetReturnEmptyQuery, _SetReturnEmptyQuery,
      doc="""The return-empty query parameter""")
 
 
class ListQuery(gdata.service.Query):

  def _GetSpreadsheetQuery(self):
    return self['sq']

  def _SetSpreadsheetQuery(self, list_query):
    self['sq'] = list_query
    
  sq = property(_GetSpreadsheetQuery, _SetSpreadsheetQuery,
      doc="""The sq query parameter""")
      
  def _GetOrderByQuery(self):
    return self['orderby']

  def _SetOrderByQuery(self, list_query):
    self['orderby'] = list_query
    
  orderby = property(_GetOrderByQuery, _SetOrderByQuery,
      doc="""The orderby query parameter""")
      
  def _GetReverseQuery(self):
    return self['reverse']

  def _SetReverseQuery(self, list_query):
    self['reverse'] = list_query
    
  reverse = property(_GetReverseQuery, _SetReverseQuery,
      doc="""The reverse query parameter""")
