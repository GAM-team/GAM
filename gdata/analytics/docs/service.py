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

"""DocsService extends the GDataService to streamline Google Documents
  operations.

  DocsService: Provides methods to query feeds and manipulate items.
                    Extends GDataService.

  DocumentQuery: Queries a Google Document list feed.

  DocumentAclQuery: Queries a Google Document Acl feed.
"""


__author__ = ('api.jfisher (Jeff Fisher), '
              'e.bidelman (Eric Bidelman)')

import re
import atom
import gdata.service
import gdata.docs
import urllib

# XML Namespaces used in Google Documents entities.
DATA_KIND_SCHEME = gdata.GDATA_NAMESPACE + '#kind'
DOCUMENT_LABEL = 'document'
SPREADSHEET_LABEL = 'spreadsheet'
PRESENTATION_LABEL = 'presentation'
FOLDER_LABEL = 'folder'
PDF_LABEL = 'pdf'

LABEL_SCHEME = gdata.GDATA_NAMESPACE + '/labels'
STARRED_LABEL_TERM = LABEL_SCHEME + '#starred'
TRASHED_LABEL_TERM = LABEL_SCHEME + '#trashed'
HIDDEN_LABEL_TERM = LABEL_SCHEME + '#hidden'
MINE_LABEL_TERM = LABEL_SCHEME + '#mine'
PRIVATE_LABEL_TERM = LABEL_SCHEME + '#private'
SHARED_WITH_DOMAIN_LABEL_TERM = LABEL_SCHEME + '#shared-with-domain'
VIEWED_LABEL_TERM = LABEL_SCHEME + '#viewed'

FOLDERS_SCHEME_PREFIX = gdata.docs.DOCUMENTS_NAMESPACE + '/folders/'

# File extensions of documents that are permitted to be uploaded or downloaded.
SUPPORTED_FILETYPES = {
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


class DocsService(gdata.service.GDataService):

  """Client extension for the Google Documents service Document List feed."""

  __FILE_EXT_PATTERN = re.compile('.*\.([a-zA-Z]{3,}$)')
  __RESOURCE_ID_PATTERN = re.compile('^([a-z]*)(:|%3A)([\w-]*)$')

  def __init__(self, email=None, password=None, source=None,
               server='docs.google.com', additional_headers=None, **kwargs):
    """Creates a client for the Google Documents service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'docs.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='writely', source=source,
        server=server, additional_headers=additional_headers, **kwargs)
    self.ssl = True

  def _MakeKindCategory(self, label):
    if label is None:
      return None
    return atom.Category(scheme=DATA_KIND_SCHEME,
        term=gdata.docs.DOCUMENTS_NAMESPACE + '#' + label, label=label)

  def _MakeContentLinkFromId(self, resource_id):
    match = self.__RESOURCE_ID_PATTERN.match(resource_id)
    label = match.group(1)
    doc_id = match.group(3)
    if label == DOCUMENT_LABEL:
      return '/feeds/download/documents/Export?docId=%s' % doc_id
    if label == PRESENTATION_LABEL:
      return '/feeds/download/presentations/Export?docId=%s' % doc_id
    if label == SPREADSHEET_LABEL:
      return ('https://spreadsheets.google.com/feeds/download/spreadsheets/'
              'Export?key=%s' % doc_id)
    raise ValueError, 'Invalid resource id: %s' % resource_id

  def _UploadFile(self, media_source, title, category, folder_or_uri=None):
    """Uploads a file to the Document List feed.

    Args:
      media_source: A gdata.MediaSource object containing the file to be
          uploaded.
      title: string The title of the document on the server after being
          uploaded.
      category: An atom.Category object specifying the appropriate document
          type.
      folder_or_uri: DocumentListEntry or string (optional) An object with a
          link to a folder or a uri to a folder to upload to.
          Note: A valid uri for a folder is of the form:
                /feeds/folders/private/full/folder%3Afolder_id

    Returns:
      A DocumentListEntry containing information about the document created on
      the Google Documents service.
    """
    if folder_or_uri:
      try:
        uri = folder_or_uri.content.src
      except AttributeError:
        uri = folder_or_uri
    else:
      uri = '/feeds/documents/private/full'

    entry = gdata.docs.DocumentListEntry()
    entry.title = atom.Title(text=title)
    if category is not None:
      entry.category.append(category)
    entry = self.Post(entry, uri, media_source=media_source,
                      extra_headers={'Slug': media_source.file_name},
                      converter=gdata.docs.DocumentListEntryFromString)
    return entry

  def _DownloadFile(self, uri, file_path):
    """Downloads a file.

    Args:
      uri: string The full Export URL to download the file from.
      file_path: string The full path to save the file to.

    Raises:
      RequestError: on error response from server.
    """
    server_response = self.request('GET', uri)
    response_body = server_response.read()
    timeout = 5
    while server_response.status == 302 and timeout > 0:
      server_response = self.request('GET',
                                     server_response.getheader('Location'))
      response_body = server_response.read()
      timeout -= 1
    if server_response.status != 200:
      raise gdata.service.RequestError, {'status': server_response.status,
                                         'reason': server_response.reason,
                                         'body': response_body}
    f = open(file_path, 'wb')
    f.write(response_body)
    f.flush()
    f.close()

  def MoveIntoFolder(self, source_entry, folder_entry):
    """Moves a document into a folder in the Document List Feed.

    Args:
      source_entry: DocumentListEntry An object representing the source
          document/folder.
      folder_entry: DocumentListEntry An object with a link to the destination
          folder.

    Returns:
      A DocumentListEntry containing information about the document created on
      the Google Documents service.
    """
    entry = gdata.docs.DocumentListEntry()
    entry.id = source_entry.id
    entry = self.Post(entry, folder_entry.content.src,
                      converter=gdata.docs.DocumentListEntryFromString)
    return entry

  def Query(self, uri, converter=gdata.docs.DocumentListFeedFromString):
    """Queries the Document List feed and returns the resulting feed of
       entries.

    Args:
      uri: string The full URI to be queried. This can contain query
          parameters, a hostname, or simply the relative path to a Document
          List feed. The DocumentQuery object is useful when constructing
          query parameters.
      converter: func (optional) A function which will be executed on the
          retrieved item, generally to render it into a Python object.
          By default the DocumentListFeedFromString function is used to
          return a DocumentListFeed object. This is because most feed
          queries will result in a feed and not a single entry.
    """
    return self.Get(uri, converter=converter)

  def QueryDocumentListFeed(self, uri):
    """Retrieves a DocumentListFeed by retrieving a URI based off the Document
       List feed, including any query parameters. A DocumentQuery object can
       be used to construct these parameters.

    Args:
      uri: string The URI of the feed being retrieved possibly with query
          parameters.

    Returns:
      A DocumentListFeed object representing the feed returned by the server.
    """
    return self.Get(uri, converter=gdata.docs.DocumentListFeedFromString)

  def GetDocumentListEntry(self, uri):
    """Retrieves a particular DocumentListEntry by its unique URI.

    Args:
      uri: string The unique URI of an entry in a Document List feed.

    Returns:
      A DocumentListEntry object representing the retrieved entry.
    """
    return self.Get(uri, converter=gdata.docs.DocumentListEntryFromString)

  def GetDocumentListFeed(self, uri=None):
    """Retrieves a feed containing all of a user's documents.

    Args:
      uri: string A full URI to query the Document List feed.
    """
    if not uri:
      uri = gdata.docs.service.DocumentQuery().ToUri()
    return self.QueryDocumentListFeed(uri)

  def GetDocumentListAclEntry(self, uri):
    """Retrieves a particular DocumentListAclEntry by its unique URI.

    Args:
      uri: string The unique URI of an entry in a Document List feed.

    Returns:
      A DocumentListAclEntry object representing the retrieved entry.
    """
    return self.Get(uri, converter=gdata.docs.DocumentListAclEntryFromString)

  def GetDocumentListAclFeed(self, uri):
    """Retrieves a feed containing all of a user's documents.

    Args:
      uri: string The URI of a document's Acl feed to retrieve.

    Returns:
      A DocumentListAclFeed object representing the ACL feed
      returned by the server.
    """
    return self.Get(uri, converter=gdata.docs.DocumentListAclFeedFromString)

  def Upload(self, media_source, title, folder_or_uri=None, label=None):
    """Uploads a document inside of a MediaSource object to the Document List
       feed with the given title.

    Args:
      media_source: MediaSource The gdata.MediaSource object containing a
          document file to be uploaded.
      title: string The title of the document on the server after being
          uploaded.
      folder_or_uri: DocumentListEntry or string (optional) An object with a
          link to a folder or a uri to a folder to upload to.
          Note: A valid uri for a folder is of the form:
                /feeds/folders/private/full/folder%3Afolder_id
      label: optional label describing the type of the document to be created.

    Returns:
      A DocumentListEntry containing information about the document created
      on the Google Documents service.
    """

    return self._UploadFile(media_source, title, self._MakeKindCategory(label),
                            folder_or_uri)

  def Download(self, entry_or_id_or_url, file_path, export_format=None,
               gid=None, extra_params=None):
    """Downloads a document from the Document List.

    Args:
      entry_or_id_or_url: a DocumentListEntry, or the resource id of an entry,
          or a url to download from (such as the content src).
      file_path: string The full path to save the file to.
      export_format: the format to convert to, if conversion is required.
      gid: grid id, for downloading a single grid of a spreadsheet
      extra_params: a map of any further parameters to control how the document
          is downloaded

    Raises:
      RequestError if the service does not respond with success
    """

    if isinstance(entry_or_id_or_url, gdata.docs.DocumentListEntry):
      url = entry_or_id_or_url.content.src
    else:
      if self.__RESOURCE_ID_PATTERN.match(entry_or_id_or_url):
        url = self._MakeContentLinkFromId(entry_or_id_or_url)
      else:
        url = entry_or_id_or_url

    if export_format is not None:
      if url.find('/Export?') == -1:
        raise gdata.service.Error, ('This entry cannot be exported '
                                    'as a different format')
      url += '&exportFormat=%s' % export_format

    if gid is not None:
      if url.find('spreadsheets') == -1:
        raise gdata.service.Error, 'grid id param is not valid for this entry'
      url += '&gid=%s' % gid

    if extra_params:
      url += '&' + urllib.urlencode(extra_params)

    self._DownloadFile(url, file_path)

  def Export(self, entry_or_id_or_url, file_path, gid=None, extra_params=None):
    """Downloads a document from the Document List in a different format.

    Args:
      entry_or_id_or_url: a DocumentListEntry, or the resource id of an entry,
          or a url to download from (such as the content src).
      file_path: string The full path to save the file to.  The export
          format is inferred from the the file extension.
      gid: grid id, for downloading a single grid of a spreadsheet
      extra_params: a map of any further parameters to control how the document
          is downloaded

    Raises:
      RequestError if the service does not respond with success
    """
    ext = None
    match = self.__FILE_EXT_PATTERN.match(file_path)
    if match:
      ext = match.group(1)
    self.Download(entry_or_id_or_url, file_path, ext, gid, extra_params)

  def CreateFolder(self, title, folder_or_uri=None):
    """Creates a folder in the Document List feed.

    Args:
      title: string The title of the folder on the server after being created.
      folder_or_uri: DocumentListEntry or string (optional) An object with a
          link to a folder or a uri to a folder to upload to.
          Note: A valid uri for a folder is of the form:
                /feeds/folders/private/full/folder%3Afolder_id

    Returns:
      A DocumentListEntry containing information about the folder created on
      the Google Documents service.
    """
    if folder_or_uri:
      try:
        uri = folder_or_uri.content.src
      except AttributeError:
        uri = folder_or_uri
    else:
      uri = '/feeds/documents/private/full'

    folder_entry = gdata.docs.DocumentListEntry()
    folder_entry.title = atom.Title(text=title)
    folder_entry.category.append(self._MakeKindCategory(FOLDER_LABEL))
    folder_entry = self.Post(folder_entry, uri,
                             converter=gdata.docs.DocumentListEntryFromString)

    return folder_entry


  def MoveOutOfFolder(self, source_entry):
    """Moves a document into a folder in the Document List Feed.

    Args:
      source_entry: DocumentListEntry An object representing the source
          document/folder.

    Returns:
      True if the entry was moved out.
    """
    return self.Delete(source_entry.GetEditLink().href)

  # Deprecated methods

  #@atom.deprecated('Please use Upload instead')
  def UploadPresentation(self, media_source, title, folder_or_uri=None):
    """Uploads a presentation inside of a MediaSource object to the Document
       List feed with the given title.

    This method is deprecated, use Upload instead.

    Args:
      media_source: MediaSource The MediaSource object containing a
          presentation file to be uploaded.
      title: string The title of the presentation on the server after being
          uploaded.
      folder_or_uri: DocumentListEntry or string (optional) An object with a
          link to a folder or a uri to a folder to upload to.
          Note: A valid uri for a folder is of the form:
                /feeds/folders/private/full/folder%3Afolder_id

    Returns:
      A DocumentListEntry containing information about the presentation created
      on the Google Documents service.
    """
    return self._UploadFile(
        media_source, title, self._MakeKindCategory(PRESENTATION_LABEL),
        folder_or_uri=folder_or_uri)

  UploadPresentation = atom.deprecated('Please use Upload instead')(
      UploadPresentation)

  #@atom.deprecated('Please use Upload instead')
  def UploadSpreadsheet(self, media_source, title, folder_or_uri=None):
    """Uploads a spreadsheet inside of a MediaSource object to the Document
       List feed with the given title.
       
    This method is deprecated, use Upload instead.

    Args:
      media_source: MediaSource The MediaSource object containing a spreadsheet
          file to be uploaded.
      title: string The title of the spreadsheet on the server after being
          uploaded.
      folder_or_uri: DocumentListEntry or string (optional) An object with a
          link to a folder or a uri to a folder to upload to.
          Note: A valid uri for a folder is of the form:
                /feeds/folders/private/full/folder%3Afolder_id

    Returns:
      A DocumentListEntry containing information about the spreadsheet created
      on the Google Documents service.
    """
    return self._UploadFile(
        media_source, title, self._MakeKindCategory(SPREADSHEET_LABEL),
        folder_or_uri=folder_or_uri)

  UploadSpreadsheet = atom.deprecated('Please use Upload instead')(
      UploadSpreadsheet)

  #@atom.deprecated('Please use Upload instead')
  def UploadDocument(self, media_source, title, folder_or_uri=None):
    """Uploads a document inside of a MediaSource object to the Document List
       feed with the given title.
       
    This method is deprecated, use Upload instead.

    Args:
      media_source: MediaSource The gdata.MediaSource object containing a
          document file to be uploaded.
      title: string The title of the document on the server after being
          uploaded.
      folder_or_uri: DocumentListEntry or string (optional) An object with a
          link to a folder or a uri to a folder to upload to.
          Note: A valid uri for a folder is of the form:
                /feeds/folders/private/full/folder%3Afolder_id

    Returns:
      A DocumentListEntry containing information about the document created
      on the Google Documents service.
    """
    return self._UploadFile(
        media_source, title, self._MakeKindCategory(DOCUMENT_LABEL),
        folder_or_uri=folder_or_uri)

  UploadDocument = atom.deprecated('Please use Upload instead')(
      UploadDocument)

  """Calling any of these functions is the same as calling Export"""
  DownloadDocument = atom.deprecated('Please use Export instead')(Export)
  DownloadPresentation = atom.deprecated('Please use Export instead')(Export)
  DownloadSpreadsheet = atom.deprecated('Please use Export instead')(Export)

  """Calling any of these functions is the same as calling MoveIntoFolder"""
  MoveDocumentIntoFolder = atom.deprecated(
      'Please use MoveIntoFolder instead')(MoveIntoFolder)
  MovePresentationIntoFolder = atom.deprecated(
      'Please use MoveIntoFolder instead')(MoveIntoFolder)
  MoveSpreadsheetIntoFolder = atom.deprecated(
      'Please use MoveIntoFolder instead')(MoveIntoFolder)
  MoveFolderIntoFolder = atom.deprecated(
      'Please use MoveIntoFolder instead')(MoveIntoFolder)


class DocumentQuery(gdata.service.Query):

  """Object used to construct a URI to query the Google Document List feed"""

  def __init__(self, feed='/feeds/documents', visibility='private',
      projection='full', text_query=None, params=None,
      categories=None):
    """Constructor for Document List Query

    Args:
      feed: string (optional) The path for the feed. (e.g. '/feeds/documents')
      visibility: string (optional) The visibility chosen for the current feed.
      projection: string (optional) The projection chosen for the current feed.
      text_query: string (optional) The contents of the q query parameter. This
                  string is URL escaped upon conversion to a URI.
      params: dict (optional) Parameter value string pairs which become URL
          params when translated to a URI. These parameters are added to
          the query's items.
      categories: list (optional) List of category strings which should be
          included as query categories. See gdata.service.Query for
          additional documentation.

    Yields:
      A DocumentQuery object used to construct a URI based on the Document
      List feed.
    """
    self.visibility = visibility
    self.projection = projection
    gdata.service.Query.__init__(self, feed, text_query, params, categories)

  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI used to retrieve entries from the Document
      List feed.
    """
    old_feed = self.feed
    self.feed = '/'.join([old_feed, self.visibility, self.projection])
    new_feed = gdata.service.Query.ToUri(self)
    self.feed = old_feed
    return new_feed

  def AddNamedFolder(self, email, folder_name):
    """Adds a named folder category, qualified by a schema.

    This function lets you query for documents that are contained inside a
    named folder without fear of collision with other categories.

    Args:
      email: string The email of the user who owns the folder.
      folder_name: string The name of the folder.

      Returns:
        The string of the category that was added to the object.
    """

    category = '{%s%s}%s' % (FOLDERS_SCHEME_PREFIX, email, folder_name)
    self.categories.append(category)
    return category

  def RemoveNamedFolder(self, email, folder_name):
    """Removes a named folder category, qualified by a schema.

    Args:
      email: string The email of the user who owns the folder.
      folder_name: string The name of the folder.

      Returns:
        The string of the category that was removed to the object.
    """
    category = '{%s%s}%s' % (FOLDERS_SCHEME_PREFIX, email, folder_name)
    self.categories.remove(category)
    return category


class DocumentAclQuery(gdata.service.Query):

  """Object used to construct a URI to query a Document's ACL feed"""

  def __init__(self, resource_id, feed='/feeds/acl/private/full'):
    """Constructor for Document ACL Query

    Args:
      resource_id: string The resource id. (e.g. 'document%3Adocument_id',
          'spreadsheet%3Aspreadsheet_id', etc.)
      feed: string (optional) The path for the feed.
          (e.g. '/feeds/acl/private/full')

    Yields:
      A DocumentAclQuery object used to construct a URI based on the Document
      ACL feed.
    """
    self.resource_id = resource_id
    gdata.service.Query.__init__(self, feed)

  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI used to retrieve entries from the Document
      ACL feed.
    """
    return '%s/%s' % (gdata.service.Query.ToUri(self), self.resource_id)
