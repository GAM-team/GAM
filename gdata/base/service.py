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

"""GBaseService extends the GDataService to streamline Google Base operations.

  GBaseService: Provides methods to query feeds and manipulate items. Extends 
                GDataService.

  DictionaryToParamList: Function which converts a dictionary into a list of 
                         URL arguments (represented as strings). This is a 
                         utility function used in CRUD operations.
"""

__author__ = 'api.jscudder (Jeffrey Scudder)'

import urllib
import gdata
import atom.service
import gdata.service
import gdata.base
import atom


# URL to which all batch requests are sent.
BASE_BATCH_URL = 'http://www.google.com/base/feeds/items/batch'


class Error(Exception):
  pass


class RequestError(Error):
  pass


class GBaseService(gdata.service.GDataService):
  """Client for the Google Base service."""

  def __init__(self, email=None, password=None, source=None,
               server='base.google.com', api_key=None, additional_headers=None,
               handler=None, **kwargs):
    """Creates a client for the Google Base service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'base.google.com'.
      api_key: string (optional) The Google Base API key to use.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='gbase', source=source,
        server=server, additional_headers=additional_headers, handler=handler,
        **kwargs)
    self.api_key = api_key

  def _SetAPIKey(self, api_key):
    if not isinstance(self.additional_headers, dict):
      self.additional_headers = {}
    self.additional_headers['X-Google-Key'] = api_key

  def __SetAPIKey(self, api_key):
    self._SetAPIKey(api_key)

  def _GetAPIKey(self):
    if 'X-Google-Key' not in self.additional_headers:
      return None
    else:
      return self.additional_headers['X-Google-Key']

  def __GetAPIKey(self):
    return self._GetAPIKey()

  api_key = property(__GetAPIKey, __SetAPIKey,
      doc="""Get or set the API key to be included in all requests.""")
    
  def Query(self, uri, converter=None):
    """Performs a style query and returns a resulting feed or entry.

    Args:
      uri: string The full URI which be queried. Examples include
          '/base/feeds/snippets?bq=digital+camera', 
          'http://www.google.com/base/feeds/snippets?bq=digital+camera'
          '/base/feeds/items'
          I recommend creating a URI using a query class.
      converter: func (optional) A function which will be executed on the
          server's response. Examples include GBaseItemFromString, etc. 

    Returns:
      If converter was specified, returns the results of calling converter on
      the server's response. If converter was not specified, and the result
      was an Atom Entry, returns a GBaseItem, by default, the method returns
      the result of calling gdata.service's Get method.
    """
 
    result = self.Get(uri, converter=converter)
    if converter:
      return result
    elif isinstance(result, atom.Entry):
      return gdata.base.GBaseItemFromString(result.ToString())
    return result

  def QuerySnippetsFeed(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseSnippetFeedFromString)

  def QueryItemsFeed(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseItemFeedFromString)

  def QueryAttributesFeed(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseAttributesFeedFromString)

  def QueryItemTypesFeed(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseItemTypesFeedFromString)

  def QueryLocalesFeed(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseLocalesFeedFromString)

  def GetItem(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseItemFromString)

  def GetSnippet(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseSnippetFromString)

  def GetAttribute(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseAttributeEntryFromString)

  def GetItemType(self, uri):
    return self.Get(uri, converter=gdata.base.GBaseItemTypeEntryFromString)

  def GetLocale(self, uri):
    return self.Get(uri, converter=gdata.base.GDataEntryFromString)

  def InsertItem(self, new_item, url_params=None, escape_params=True, 
      converter=None):
    """Adds an item to Google Base.

    Args: 
      new_item: atom.Entry or subclass A new item which is to be added to 
                Google Base.
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request. 
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.
      converter: func (optional) Function which is executed on the server's
          response before it is returned. Usually this is a function like
          GBaseItemFromString which will parse the response and turn it into
          an object.

    Returns:
      If converter is defined, the results of running converter on the server's
      response. Otherwise, it will be a GBaseItem.
    """

    response = self.Post(new_item, '/base/feeds/items', url_params=url_params,
                         escape_params=escape_params, converter=converter)

    if not converter and isinstance(response, atom.Entry):
      return gdata.base.GBaseItemFromString(response.ToString())
    return response

  def DeleteItem(self, item_id, url_params=None, escape_params=True):
    """Removes an item with the specified ID from Google Base.

    Args:
      item_id: string The ID of the item to be deleted. Example:
               'http://www.google.com/base/feeds/items/13185446517496042648'
      url_params: dict (optional) Additional URL parameters to be included
                  in the deletion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      True if the delete succeeded.
    """
    
    return self.Delete('%s' % (item_id[len('http://www.google.com'):],),
                       url_params=url_params, escape_params=escape_params)
                           
  def UpdateItem(self, item_id, updated_item, url_params=None, 
                 escape_params=True, 
                 converter=gdata.base.GBaseItemFromString):
    """Updates an existing item.

    Args:
      item_id: string The ID of the item to be updated.  Example:
               'http://www.google.com/base/feeds/items/13185446517496042648'
      updated_item: atom.Entry, subclass, or string, containing
                    the Atom Entry which will replace the base item which is 
                    stored at the item_id.
      url_params: dict (optional) Additional URL parameters to be included
                  in the update request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.
      converter: func (optional) Function which is executed on the server's
          response before it is returned. Usually this is a function like
          GBaseItemFromString which will parse the response and turn it into
          an object.

    Returns:
      If converter is defined, the results of running converter on the server's
      response. Otherwise, it will be a GBaseItem.
    """
    
    response = self.Put(updated_item, 
        item_id, url_params=url_params, escape_params=escape_params, 
        converter=converter)
    if not converter and isinstance(response, atom.Entry):
      return gdata.base.GBaseItemFromString(response.ToString())
    return response

  def ExecuteBatch(self, batch_feed, 
                   converter=gdata.base.GBaseItemFeedFromString):
    """Sends a batch request feed to the server.
    
    Args: 
      batch_feed: gdata.BatchFeed A feed containing BatchEntry elements which
          contain the desired CRUD operation and any necessary entry data.
      converter: Function (optional) Function to be executed on the server's
          response. This function should take one string as a parameter. The
          default value is GBaseItemFeedFromString which will turn the result 
          into a gdata.base.GBaseItem object.

    Returns:
      A gdata.BatchFeed containing the results.
    """
    
    return self.Post(batch_feed, BASE_BATCH_URL, converter=converter) 


class BaseQuery(gdata.service.Query):

  def _GetBaseQuery(self):
    return self['bq']

  def _SetBaseQuery(self, base_query):
    self['bq'] = base_query

  bq = property(_GetBaseQuery, _SetBaseQuery, 
      doc="""The bq query parameter""")
