#!/usr/bin/python
#
# Copyright Google 2007-2008, all rights reserved.
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


import StringIO
import gdata
import gdata.service
import gdata.spreadsheet
import gdata.spreadsheet.service
import gdata.docs
import gdata.docs.service


"""Make the Google Documents API feel more like using a database.

This module contains a client and other classes which make working with the 
Google Documents List Data API and the Google Spreadsheets Data API look a
bit more like working with a heirarchical database. Using the DatabaseClient,
you can create or find spreadsheets and use them like a database, with 
worksheets representing tables and rows representing records.

Example Usage:
# Create a new database, a new table, and add records.
client = gdata.spreadsheet.text_db.DatabaseClient(username='jo@example.com', 
    password='12345')
database = client.CreateDatabase('My Text Database')
table = database.CreateTable('addresses', ['name','email',
    'phonenumber', 'mailingaddress'])
record = table.AddRecord({'name':'Bob', 'email':'bob@example.com', 
    'phonenumber':'555-555-1234', 'mailingaddress':'900 Imaginary St.'})

# Edit a record
record.content['email'] = 'bob2@example.com'
record.Push()

# Delete a table
table.Delete

Warnings: 
Care should be exercised when using this module on spreadsheets
which contain formulas. This module treats all rows as containing text and
updating a row will overwrite any formula with the output of the formula. 
The intended use case is to allow easy storage of text data in a spreadsheet.

  Error: Domain specific extension of Exception.
  BadCredentials: Error raised is username or password was incorrect.
  CaptchaRequired: Raised if a login attempt failed and a CAPTCHA challenge 
      was issued.
  DatabaseClient: Communicates with Google Docs APIs servers.
  Database: Represents a spreadsheet and interacts with tables.
  Table: Represents a worksheet and interacts with records.
  RecordResultSet: A list of records in a table.
  Record: Represents a row in a worksheet allows manipulation of text data.
"""


__author__ = 'api.jscudder (Jeffrey Scudder)'


class Error(Exception):
  pass


class BadCredentials(Error):
  pass


class CaptchaRequired(Error):
  pass


class DatabaseClient(object):
  """Allows creation and finding of Google Spreadsheets databases.

  The DatabaseClient simplifies the process of creating and finding Google 
  Spreadsheets and will talk to both the Google Spreadsheets API and the 
  Google Documents List API. 
  """

  def __init__(self, username=None, password=None):
    """Constructor for a Database Client. 
  
    If the username and password are present, the constructor  will contact
    the Google servers to authenticate.

    Args:
      username: str (optional) Example: jo@example.com
      password: str (optional)
    """
    self.__docs_client = gdata.docs.service.DocsService()
    self.__spreadsheets_client = (
        gdata.spreadsheet.service.SpreadsheetsService())
    self.SetCredentials(username, password)

  def SetCredentials(self, username, password):
    """Attempts to log in to Google APIs using the provided credentials.

    If the username or password are None, the client will not request auth 
    tokens.

    Args:
      username: str (optional) Example: jo@example.com
      password: str (optional)
    """
    self.__docs_client.email = username
    self.__docs_client.password = password
    self.__spreadsheets_client.email = username
    self.__spreadsheets_client.password = password
    if username and password:
      try:
        self.__docs_client.ProgrammaticLogin()
        self.__spreadsheets_client.ProgrammaticLogin()
      except gdata.service.CaptchaRequired:
        raise CaptchaRequired('Please visit https://www.google.com/accounts/'
                            'DisplayUnlockCaptcha to unlock your account.')
      except gdata.service.BadAuthentication:
        raise BadCredentials('Username or password incorrect.')
    
  def CreateDatabase(self, name):
    """Creates a new Google Spreadsheet with the desired name.

    Args:
      name: str The title for the spreadsheet.

    Returns:
      A Database instance representing the new spreadsheet. 
    """
    # Create a Google Spreadsheet to form the foundation of this database.
    # Spreadsheet is created by uploading a file to the Google Documents
    # List API.
    virtual_csv_file = StringIO.StringIO(',,,')
    virtual_media_source = gdata.MediaSource(file_handle=virtual_csv_file, content_type='text/csv', content_length=3)
    db_entry = self.__docs_client.UploadSpreadsheet(virtual_media_source, name)
    return Database(spreadsheet_entry=db_entry, database_client=self)

  def GetDatabases(self, spreadsheet_key=None, name=None):
    """Finds spreadsheets which have the unique key or title.

    If querying on the spreadsheet_key there will be at most one result, but
    searching by name could yield multiple results.

    Args:
      spreadsheet_key: str The unique key for the spreadsheet, this 
          usually in the the form 'pk23...We' or 'o23...423.12,,,3'.
      name: str The title of the spreadsheets.

    Returns:
      A list of Database objects representing the desired spreadsheets.
    """
    if spreadsheet_key:
      db_entry = self.__docs_client.GetDocumentListEntry(
          r'/feeds/documents/private/full/spreadsheet%3A' + spreadsheet_key)
      return [Database(spreadsheet_entry=db_entry, database_client=self)]
    else:
      title_query = gdata.docs.service.DocumentQuery()
      title_query['title'] = name
      db_feed = self.__docs_client.QueryDocumentListFeed(title_query.ToUri())
      matching_databases = []
      for entry in db_feed.entry:
        matching_databases.append(Database(spreadsheet_entry=entry, 
                                           database_client=self))
      return matching_databases
    
  def _GetDocsClient(self):
    return self.__docs_client

  def _GetSpreadsheetsClient(self):
    return self.__spreadsheets_client


class Database(object):
  """Provides interface to find and create tables.

  The database represents a Google Spreadsheet.
  """

  def __init__(self, spreadsheet_entry=None, database_client=None):
    """Constructor for a database object.

    Args:
      spreadsheet_entry: gdata.docs.DocumentListEntry The 
          Atom entry which represents the Google Spreadsheet. The
          spreadsheet's key is extracted from the entry and stored as a 
          member.
      database_client: DatabaseClient A client which can talk to the
          Google Spreadsheets servers to perform operations on worksheets
          within this spreadsheet.
    """
    self.entry = spreadsheet_entry
    if self.entry:
      id_parts = spreadsheet_entry.id.text.split('/')
      self.spreadsheet_key = id_parts[-1].replace('spreadsheet%3A', '')
    self.client = database_client

  def CreateTable(self, name, fields=None):
    """Add a new worksheet to this spreadsheet and fill in column names.

    Args:
      name: str The title of the new worksheet.
      fields: list of strings The column names which are placed in the
          first row of this worksheet. These names are converted into XML
          tags by the server. To avoid changes during the translation
          process I recommend using all lowercase alphabetic names. For
          example ['somelongname', 'theothername']

    Returns:
      Table representing the newly created worksheet.
    """
    worksheet = self.client._GetSpreadsheetsClient().AddWorksheet(title=name,
        row_count=1, col_count=len(fields), key=self.spreadsheet_key)
    return Table(name=name, worksheet_entry=worksheet, 
        database_client=self.client, 
        spreadsheet_key=self.spreadsheet_key, fields=fields)

  def GetTables(self, worksheet_id=None, name=None):
    """Searches for a worksheet with the specified ID or name.

    The list of results should have one table at most, or no results
    if the id or name were not found.

    Args:
      worksheet_id: str The ID of the worksheet, example: 'od6'
      name: str The title of the worksheet.

    Returns:
      A list of length 0 or 1 containing the desired Table. A list is returned
      to make this method feel like GetDatabases and GetRecords.
    """
    if worksheet_id:
      worksheet_entry = self.client._GetSpreadsheetsClient().GetWorksheetsFeed(
          self.spreadsheet_key, wksht_id=worksheet_id)
      return [Table(name=worksheet_entry.title.text, 
          worksheet_entry=worksheet_entry, database_client=self.client, 
          spreadsheet_key=self.spreadsheet_key)]
    else:
      matching_tables = []
      query = None
      if name:
        query = gdata.spreadsheet.service.DocumentQuery()
        query.title = name
 
      worksheet_feed = self.client._GetSpreadsheetsClient().GetWorksheetsFeed(
          self.spreadsheet_key, query=query)
      for entry in worksheet_feed.entry:
        matching_tables.append(Table(name=entry.title.text, 
            worksheet_entry=entry, database_client=self.client, 
            spreadsheet_key=self.spreadsheet_key))
      return matching_tables

  def Delete(self):
    """Deletes the entire database spreadsheet from Google Spreadsheets."""
    entry = self.client._GetDocsClient().Get(
        r'http://docs.google.com/feeds/documents/private/full/spreadsheet%3A' +
        self.spreadsheet_key)
    self.client._GetDocsClient().Delete(entry.GetEditLink().href)


class Table(object):

  def __init__(self, name=None, worksheet_entry=None, database_client=None, 
      spreadsheet_key=None, fields=None):
    self.name = name
    self.entry = worksheet_entry
    id_parts = worksheet_entry.id.text.split('/')
    self.worksheet_id = id_parts[-1]
    self.spreadsheet_key = spreadsheet_key
    self.client = database_client
    self.fields = fields or []
    if fields:
      self.SetFields(fields)

  def LookupFields(self):
    """Queries to find the column names in the first row of the worksheet.
    
    Useful when you have retrieved the table from the server and you don't 
    know the column names.
    """
    if self.entry:
      first_row_contents = []
      query = gdata.spreadsheet.service.CellQuery()
      query.max_row = '1'
      query.min_row = '1'
      feed = self.client._GetSpreadsheetsClient().GetCellsFeed(
          self.spreadsheet_key, wksht_id=self.worksheet_id, query=query)
      for entry in feed.entry:
        first_row_contents.append(entry.content.text)
      # Get the next set of cells if needed.
      next_link = feed.GetNextLink()
      while next_link:
        feed = self.client._GetSpreadsheetsClient().Get(next_link.href, 
            converter=gdata.spreadsheet.SpreadsheetsCellsFeedFromString)
        for entry in feed.entry:
          first_row_contents.append(entry.content.text)
        next_link = feed.GetNextLink()
      # Convert the contents of the cells to valid headers.
      self.fields = ConvertStringsToColumnHeaders(first_row_contents)
    
  def SetFields(self, fields):
    """Changes the contents of the cells in the first row of this worksheet.

    Args:
      fields: list of strings The names in the list comprise the
          first row of the worksheet. These names are converted into XML
          tags by the server. To avoid changes during the translation
          process I recommend using all lowercase alphabetic names. For
          example ['somelongname', 'theothername']
    """
    # TODO: If the table already had fields, we might want to clear out the,
    # current column headers.
    self.fields = fields
    i = 0
    for column_name in fields:
      i = i + 1
      # TODO: speed this up by using a batch request to update cells.
      self.client._GetSpreadsheetsClient().UpdateCell(1, i, column_name, 
          self.spreadsheet_key, self.worksheet_id)

  def Delete(self):
    """Deletes this worksheet from the spreadsheet."""
    worksheet = self.client._GetSpreadsheetsClient().GetWorksheetsFeed(
        self.spreadsheet_key, wksht_id=self.worksheet_id)
    self.client._GetSpreadsheetsClient().DeleteWorksheet(
        worksheet_entry=worksheet)

  def AddRecord(self, data):
    """Adds a new row to this worksheet.

    Args:
      data: dict of strings Mapping of string values to column names. 

    Returns:
      Record which represents this row of the spreadsheet.
    """
    new_row = self.client._GetSpreadsheetsClient().InsertRow(data, 
        self.spreadsheet_key, wksht_id=self.worksheet_id)
    return Record(content=data, row_entry=new_row, 
        spreadsheet_key=self.spreadsheet_key, worksheet_id=self.worksheet_id,
        database_client=self.client)

  def GetRecord(self, row_id=None, row_number=None):
    """Gets a single record from the worksheet based on row ID or number.
    
    Args:
      row_id: The ID for the individual row.
      row_number: str or int The position of the desired row. Numbering 
          begins at 1, which refers to the second row in the worksheet since
          the first row is used for column names.

    Returns:
      Record for the desired row.
    """
    if row_id:
      row_entry = self.client._GetSpreadsheetsClient().GetListFeed(
          self.spreadsheet_key, wksht_id=self.worksheet_id, row_id=row_id)
      return Record(content=None, row_entry=row_entry, 
           spreadsheet_key=self.spreadsheet_key, 
           worksheet_id=self.worksheet_id, database_client=self.client)
    else:
      row_query = gdata.spreadsheet.service.ListQuery()
      row_query.start_index = str(row_number)
      row_query.max_results = '1'
      row_feed = self.client._GetSpreadsheetsClient().GetListFeed(
          self.spreadsheet_key, wksht_id=self.worksheet_id, query=row_query)
      if len(row_feed.entry) >= 1:
        return Record(content=None, row_entry=row_feed.entry[0],
            spreadsheet_key=self.spreadsheet_key,
            worksheet_id=self.worksheet_id, database_client=self.client)
      else:
        return None

  def GetRecords(self, start_row, end_row):
    """Gets all rows between the start and end row numbers inclusive.

    Args:
      start_row: str or int
      end_row: str or int

    Returns:
      RecordResultSet for the desired rows.
    """
    start_row = int(start_row)
    end_row = int(end_row)
    max_rows = end_row - start_row + 1
    row_query = gdata.spreadsheet.service.ListQuery()
    row_query.start_index = str(start_row)
    row_query.max_results = str(max_rows)
    rows_feed = self.client._GetSpreadsheetsClient().GetListFeed(
        self.spreadsheet_key, wksht_id=self.worksheet_id, query=row_query)
    return RecordResultSet(rows_feed, self.client, self.spreadsheet_key,
        self.worksheet_id)

  def FindRecords(self, query_string):
    """Performs a query against the worksheet to find rows which match.

    For details on query string syntax see the section on sq under
    http://code.google.com/apis/spreadsheets/reference.html#list_Parameters

    Args:
      query_string: str Examples: 'name == john' to find all rows with john
          in the name column, '(cost < 19.50 and name != toy) or cost > 500'

    Returns:
      RecordResultSet with the first group of matches.
    """
    row_query = gdata.spreadsheet.service.ListQuery()
    row_query.sq = query_string
    matching_feed = self.client._GetSpreadsheetsClient().GetListFeed(
        self.spreadsheet_key, wksht_id=self.worksheet_id, query=row_query)
    return RecordResultSet(matching_feed, self.client, 
        self.spreadsheet_key, self.worksheet_id)


class RecordResultSet(list):
  """A collection of rows which allows fetching of the next set of results.

  The server may not send all rows in the requested range because there are
  too many. Using this result set you can access the first set of results
  as if it is a list, then get the next batch (if there are more results) by
  calling GetNext().
  """

  def __init__(self, feed, client, spreadsheet_key, worksheet_id):
    self.client = client
    self.spreadsheet_key = spreadsheet_key
    self.worksheet_id = worksheet_id
    self.feed = feed
    list(self)
    for entry in self.feed.entry:
      self.append(Record(content=None, row_entry=entry, 
          spreadsheet_key=spreadsheet_key, worksheet_id=worksheet_id,
          database_client=client))

  def GetNext(self):
    """Fetches the next batch of rows in the result set.

    Returns:
      A new RecordResultSet.
    """
    next_link = self.feed.GetNextLink()
    if next_link and next_link.href:
      new_feed = self.client._GetSpreadsheetsClient().Get(next_link.href, 
          converter=gdata.spreadsheet.SpreadsheetsListFeedFromString)
      return RecordResultSet(new_feed, self.client, self.spreadsheet_key,
          self.worksheet_id)


class Record(object):
  """Represents one row in a worksheet and provides a dictionary of values.

  Attributes:
    custom: dict Represents the contents of the row with cell values mapped
        to column headers.
  """

  def __init__(self, content=None, row_entry=None, spreadsheet_key=None, 
       worksheet_id=None, database_client=None):
    """Constructor for a record.
    
    Args:
      content: dict of strings Mapping of string values to column names.
      row_entry: gdata.spreadsheet.SpreadsheetsList The Atom entry 
          representing this row in the worksheet.
      spreadsheet_key: str The ID of the spreadsheet in which this row 
          belongs.
      worksheet_id: str The ID of the worksheet in which this row belongs.
      database_client: DatabaseClient The client which can be used to talk
          the Google Spreadsheets server to edit this row.
    """
    self.entry = row_entry
    self.spreadsheet_key = spreadsheet_key
    self.worksheet_id = worksheet_id
    if row_entry:
      self.row_id = row_entry.id.text.split('/')[-1]
    else:
      self.row_id = None
    self.client = database_client
    self.content = content or {}
    if not content:
      self.ExtractContentFromEntry(row_entry)

  def ExtractContentFromEntry(self, entry):
    """Populates the content and row_id based on content of the entry.

    This method is used in the Record's contructor.

    Args:
      entry: gdata.spreadsheet.SpreadsheetsList The Atom entry 
          representing this row in the worksheet.
    """
    self.content = {}
    if entry:
      self.row_id = entry.id.text.split('/')[-1]
      for label, custom in entry.custom.iteritems():
        self.content[label] = custom.text

  def Push(self):
    """Send the content of the record to spreadsheets to edit the row.

    All items in the content dictionary will be sent. Items which have been
    removed from the content may remain in the row. The content member
    of the record will not be modified so additional fields in the row
    might be absent from this local copy.
    """
    self.entry = self.client._GetSpreadsheetsClient().UpdateRow(self.entry, self.content)

  def Pull(self):
    """Query Google Spreadsheets to get the latest data from the server.

    Fetches the entry for this row and repopulates the content dictionary 
    with the data found in the row.
    """
    if self.row_id:
      self.entry = self.client._GetSpreadsheetsClient().GetListFeed(
          self.spreadsheet_key, wksht_id=self.worksheet_id, row_id=self.row_id)
    self.ExtractContentFromEntry(self.entry)

  def Delete(self):
    self.client._GetSpreadsheetsClient().DeleteRow(self.entry)


def ConvertStringsToColumnHeaders(proposed_headers):
  """Converts a list of strings to column names which spreadsheets accepts.

  When setting values in a record, the keys which represent column names must
  fit certain rules. They are all lower case, contain no spaces or special
  characters. If two columns have the same name after being sanitized, the 
  columns further to the right have _2, _3 _4, etc. appended to them.

  If there are column names which consist of all special characters, or if
  the column header is blank, an obfuscated value will be used for a column
  name. This method does not handle blank column names or column names with
  only special characters.
  """
  headers = []
  for input_string in proposed_headers:
    # TODO: probably a more efficient way to do this. Perhaps regex.
    sanitized = input_string.lower().replace('_', '').replace(
        ':', '').replace(' ', '')
    # When the same sanitized header appears multiple times in the first row
    # of a spreadsheet, _n is appended to the name to make it unique.
    header_count = headers.count(sanitized)
    if header_count > 0:
      headers.append('%s_%i' % (sanitized, header_count+1))
    else:
      headers.append(sanitized)
  return headers
