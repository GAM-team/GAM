#!/usr/bin/python
#
# Copyright (C) 2006 Google Inc.
# Refactored in 2009 to work for Google Analytics by Sal Uryasev at Juice Inc.
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

"""
  AccountsService extends the GDataService to streamline Google Analytics
            account information operations.

  AnalyticsDataService: Provides methods to query google analytics data feeds.
                    Extends GDataService.

  DataQuery: Queries a Google Analytics Data list feed.
  
  AccountQuery: Queries a Google Analytics Account list feed.
"""


__author__ = 'api.suryasev (Sal Uryasev)'


import urllib
import atom
import gdata.service
import gdata.analytics


class AccountsService(gdata.service.GDataService):

  """Client extension for the Google Analytics Account List feed."""

  def __init__(self, email="", password=None, source=None,
               server='www.google.com/analytics', additional_headers=None, 
               **kwargs):
    """Creates a client for the Google Analytics service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='analytics', 
        source=source, server=server, additional_headers=additional_headers,
        **kwargs)

  def QueryAccountListFeed(self, uri):
    """Retrieves an AccountListFeed by retrieving a URI based off the Document
       List feed, including any query parameters. An AccountListFeed object 
       can be used to construct these parameters.

    Args:
      uri: string The URI of the feed being retrieved possibly with query
           parameters.

    Returns:
      An AccountListFeed object representing the feed returned by the server.
    """
    return self.Get(uri, converter=gdata.analytics.AccountListFeedFromString)

  def GetAccountListEntry(self, uri):
    """Retrieves a particular AccountListEntry by its unique URI.

    Args:
      uri: string The unique URI of an entry in an Account List feed.

    Returns:
      An AccountLisFeed object representing the retrieved entry.
      """
    return self.Get(uri, converter=gdata.analytics.AccountListEntryFromString)

  def GetAccountList(self, max_results=1000, text_query=None,
                     params=None, categories=None):
    """Retrieves a feed containing all of a user's accounts and profiles."""
    q = gdata.analytics.service.AccountQuery(max_results=max_results,
                                             text_query=text_query, 
                                             params=params,
                                             categories=categories);
    return self.QueryAccountListFeed(q.ToUri())




class AnalyticsDataService(gdata.service.GDataService):

  """Client extension for the Google Analytics service Data List feed."""

  def __init__(self, email=None, password=None, source=None,
               server='www.google.com/analytics', additional_headers=None, 
               **kwargs):
    """Creates a client for the Google Analytics service.

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
    
    gdata.service.GDataService.__init__(self, 
        email=email, password=password, service='analytics', source=source,
        server=server, additional_headers=additional_headers, **kwargs)
    
  def GetData(self, ids='', dimensions='', metrics='',
              sort='', filters='', start_date='',
              end_date='', start_index='',
              max_results=''):
    """Retrieves a feed containing a user's data
    
      ids: comma-separated string of analytics accounts.
      dimensions: comma-separated string of dimensions.
      metrics: comma-separated string of metrics.
      sort: comma-separated string of dimensions and metrics for sorting.
            This may be previxed with a minus to sort in reverse order. 
                (e.g. '-ga:keyword')
            If ommited, the first dimension passed in will be used.
      filters: comma-separated string of filter parameters.
            (e.g. 'ga:keyword==google')
      start_date: start date for data pull.
      end_date: end date for data pull.
      start_index: used in combination with max_results to pull more than 1000 
            entries. This defaults to 1.
      max_results: maximum results that the pull will return.  This defaults
            to, and maxes out at 1000.
    """
    q = gdata.analytics.service.DataQuery(ids=ids, 
                                          dimensions=dimensions,
                                          metrics=metrics,
                                          filters=filters,
                                          sort=sort,
                                          start_date=start_date,
                                          end_date=end_date,
                                          start_index=start_index,
                                          max_results=max_results);
    return self.AnalyticsDataFeed(q.ToUri())
    
  def AnalyticsDataFeed(self, uri):
    """Retrieves an AnalyticsListFeed by retrieving a URI based off the 
       Document List feed, including any query parameters. An 
       AnalyticsListFeed object can be used to construct these parameters.

    Args:
      uri: string The URI of the feed being retrieved possibly with query
           parameters.

    Returns:
      An AnalyticsListFeed object representing the feed returned by the 
      server.
    """
    return self.Get(uri,
                    converter=gdata.analytics.AnalyticsDataFeedFromString)
    
  """
  Account Fetching
  """    
    
  def QueryAccountListFeed(self, uri):
    """Retrieves an Account ListFeed by retrieving a URI based off the Account
       List feed, including any query parameters. A AccountQuery object can
       be used to construct these parameters.

    Args:
      uri: string The URI of the feed being retrieved possibly with query
           parameters.

    Returns:
      An AccountListFeed object representing the feed returned by the server.
    """
    return self.Get(uri, converter=gdata.analytics.AccountListFeedFromString)

  def GetAccountListEntry(self, uri):
    """Retrieves a particular AccountListEntry by its unique URI.

    Args:
      uri: string The unique URI of an entry in an Account List feed.

    Returns:
      An AccountListEntry object representing the retrieved entry.
      """
    return self.Get(uri, converter=gdata.analytics.AccountListEntryFromString)

  def GetAccountList(self, username="default", max_results=1000, 
                     start_index=1):
    """Retrieves a feed containing all of a user's accounts and profiles.
       The username parameter is soon to be deprecated, with 'default' 
       becoming the only allowed parameter.
    """
    if not username:
      raise Exception("username is a required parameter")
    q = gdata.analytics.service.AccountQuery(username=username, 
                                             max_results=max_results,
                                             start_index=start_index);
    return self.QueryAccountListFeed(q.ToUri())

class DataQuery(gdata.service.Query):
  """Object used to construct a URI to a data feed"""
  def __init__(self, feed='/feeds/data', text_query=None, 
               params=None, categories=None, ids="",
               dimensions="", metrics="", sort="", filters="",
               start_date="", end_date="", start_index="",
               max_results=""):
    """Constructor for Analytics List Query

    Args:
      feed: string (optional) The path for the feed. (e.g. '/feeds/data')

      text_query: string (optional) The contents of the q query parameter. 
            This string is URL escaped upon conversion to a URI.
      params: dict (optional) Parameter value string pairs which become URL
            params when translated to a URI. These parameters are added to
              the query's items.
      categories: list (optional) List of category strings which should be
            included as query categories. See gdata.service.Query for
            additional documentation.
      ids: comma-separated string of analytics accounts.
      dimensions: comma-separated string of dimensions.
      metrics: comma-separated string of metrics.
      sort: comma-separated string of dimensions and metrics.
            This may be previxed with a minus to sort in reverse order 
            (e.g. '-ga:keyword').
            If ommited, the first dimension passed in will be used.
      filters: comma-separated string of filter parameters 
            (e.g. 'ga:keyword==google').
      start_date: start date for data pull.
      end_date: end date for data pull.
      start_index: used in combination with max_results to pull more than 1000 
            entries. This defaults to 1.
      max_results: maximum results that the pull will return.  This defaults 
            to, and maxes out at 1000.

    Yields:
      A DocumentQuery object used to construct a URI based on the Document
      List feed.
    """
    self.elements = {'ids': ids,
                     'dimensions': dimensions,
                     'metrics': metrics,
                     'sort': sort,
                     'filters': filters,
                     'start-date': start_date,
                     'end-date': end_date,
                     'start-index': start_index,
                     'max-results': max_results}
    
    gdata.service.Query.__init__(self, feed, text_query, params, categories)
  
  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI used to retrieve entries from the Analytics
      List feed.
    """
    old_feed = self.feed
    self.feed = '/'.join([old_feed]) + '?' + \
                urllib.urlencode(dict([(key, value) for key, value in \
                self.elements.iteritems() if value]))
    new_feed = gdata.service.Query.ToUri(self)
    self.feed = old_feed
    return new_feed


class AccountQuery(gdata.service.Query):
  """Object used to construct a URI to query the Google Account List feed"""
  def __init__(self, feed='/feeds/accounts', start_index=1,
               max_results=1000, username='default', text_query=None,
               params=None, categories=None):
    """Constructor for Account List Query

    Args:
      feed: string (optional) The path for the feed. (e.g. '/feeds/documents')
      visibility: string (optional) The visibility chosen for the current 
            feed.
      projection: string (optional) The projection chosen for the current 
            feed.
      text_query: string (optional) The contents of the q query parameter. 
            This string is URL escaped upon conversion to a URI.
      params: dict (optional) Parameter value string pairs which become URL
              params when translated to a URI. These parameters are added to
              the query's items.
      categories: list (optional) List of category strings which should be
              included as query categories. See gdata.service.Query for
              additional documentation.
      username: string (deprecated) This value should now always be passed as 
              'default'.

    Yields:
      A DocumentQuery object used to construct a URI based on the Document
      List feed.
    """
    self.max_results = max_results
    self.start_index = start_index
    self.username = username
    gdata.service.Query.__init__(self, feed, text_query, params, categories)
  
  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI used to retrieve entries from the Account
      List feed.
    """
    old_feed = self.feed
    self.feed = '/'.join([old_feed, self.username]) + '?' + \
                '&'.join(['max-results=' + str(self.max_results), 
                          'start-index=' + str(self.start_index)])
    new_feed = self.feed
    self.feed = old_feed
    return new_feed
