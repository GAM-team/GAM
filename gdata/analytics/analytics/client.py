#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.
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

"""Streamlines requests to the Google Analytics APIs."""

__author__ = 'api.nickm@google.com (Nick Mihailovski)'


import atom.data
import gdata.client
import gdata.analytics.data
import gdata.gauth


class AnalyticsClient(gdata.client.GDClient):
  """Client extension for the Google Analytics API service."""

  api_version = '2'
  auth_service = 'analytics'
  auth_scopes = gdata.gauth.AUTH_SCOPES['analytics']
  account_type = 'GOOGLE'
  ssl = True

  def __init__(self, auth_token=None, **kwargs):
    """Initializes a new client for the Google Analytics Data Export API.

    Args:
      auth_token: gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken (optional) Authorizes this client to edit the user's data.
      kwargs: The other parameters to pass to gdata.client.GDClient
          constructor.
    """

    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)

  def get_account_feed(self, feed_uri, auth_token=None, **kwargs):
    """Makes a request to the Analytics API Account Feed.

    Args:
      feed_uri: str or gdata.analytics.AccountFeedQuery The Analytics Account
          Feed uri to define what data to retrieve from the API. Can also be
          used with a gdata.analytics.AccountFeedQuery object.
    """

    return self.get_feed(feed_uri,
                         desired_class=gdata.analytics.data.AccountFeed,
                         auth_token=auth_token,
                         **kwargs)

  GetAccountFeed = get_account_feed

  def get_data_feed(self, feed_uri, auth_token=None, **kwargs):
    """Makes a request to the Analytics API Data Feed.

    Args:
      feed_uri: str or gdata.analytics.AccountFeedQuery The Analytics Data
          Feed uri to define what data to retrieve from the API. Can also be
          used with a gdata.analytics.AccountFeedQuery object.
    """

    return self.get_feed(feed_uri,
                         desired_class=gdata.analytics.data.DataFeed,
                         auth_token=auth_token,
                         **kwargs)

  GetDataFeed = get_data_feed

  def get_management_feed(self, feed_uri, auth_token=None, **kwargs):
    """Makes a request to the Google Analytics Management API.

    The Management API provides read-only access to configuration data for
    Google Analytics and supercedes the Data Export API Account Feed.
    The Management API supports 5 feeds: account, web property, profile,
    goal, advanced segment.

    You can access each feed through the respective management query class
    below. All requests return the same data object.

    Args:
      feed_uri: str or AccountQuery, WebPropertyQuery,
          ProfileQuery, GoalQuery, MgmtAdvSegFeedQuery
          The Management API Feed uri to define which feed to retrieve.
          Either use a string or one of the wrapper classes.
    """

    return self.get_feed(feed_uri,
                         desired_class=gdata.analytics.data.ManagementFeed,
                         auth_token=auth_token,
                         **kwargs)

  GetMgmtFeed = GetManagementFeed = get_management_feed


class AnalyticsBaseQuery(gdata.client.GDQuery):
  """Abstracts common configuration across all query objects.
  
  Attributes:
    scheme: string The default scheme. Should always be https.
    host: string The default host.
  """

  scheme = 'https'
  host = 'www.google.com'


class AccountFeedQuery(AnalyticsBaseQuery):
  """Account Feed query class to simplify constructing Account Feed Urls.

  To use this class, you can either pass a dict in the constructor that has
  all the data feed query parameters as keys:
     queryUrl = AccountFeedQuery({'max-results': '10000'})

  Alternatively you can add new parameters directly to the query object:
     queryUrl = AccountFeedQuery()
     queryUrl.query['max-results'] = '10000'

  Args:
    query: dict (optional) Contains all the GA Data Feed query parameters
        as keys.
  """

  path = '/analytics/feeds/accounts/default'

  def __init__(self, query={}, **kwargs):
    self.query = query
    gdata.client.GDQuery(self, **kwargs)


class DataFeedQuery(AnalyticsBaseQuery):
  """Data Feed query class to simplify constructing Data Feed Urls.

  To use this class, you can either pass a dict in the constructor that has
  all the data feed query parameters as keys:
     queryUrl = DataFeedQuery({'start-date': '2008-10-01'})

  Alternatively you can add new parameters directly to the query object:
     queryUrl = DataFeedQuery()
     queryUrl.query['start-date'] = '2008-10-01'

  Args:
    query: dict (optional) Contains all the GA Data Feed query parameters
        as keys.
  """

  path = '/analytics/feeds/data'

  def __init__(self, query={}, **kwargs):
    self.query = query
    gdata.client.GDQuery(self, **kwargs)


class AccountQuery(AnalyticsBaseQuery):
  """Management API Account Feed query class.

  Example Usage:
    queryUrl = AccountQuery()
    queryUrl = AccountQuery({'max-results': 100})

    queryUrl2 = AccountQuery()
    queryUrl2.query['max-results'] = 100

  Args:
    query: dict (optional) A dictionary of query parameters.
  """

  path = '/analytics/feeds/datasources/ga/accounts'

  def __init__(self, query={}, **kwargs):
    self.query = query
    gdata.client.GDQuery(self, **kwargs)

class WebPropertyQuery(AnalyticsBaseQuery):
  """Management API Web Property Feed query class.

  Example Usage:
    queryUrl = WebPropertyQuery()
    queryUrl = WebPropertyQuery('123', {'max-results': 100})
    queryUrl = WebPropertyQuery(acct_id='123',
                                query={'max-results': 100})

    queryUrl2 = WebPropertyQuery()
    queryUrl2.acct_id = '1234'
    queryUrl2.query['max-results'] = 100

  Args:
    acct_id: string (optional) The account ID to filter results.
        Default is ~all.
    query: dict (optional) A dictionary of query parameters.
  """

  def __init__(self, acct_id='~all', query={}, **kwargs):
    self.acct_id = acct_id
    self.query = query
    gdata.client.GDQuery(self, **kwargs)

  @property
  def path(self):
    """Wrapper for path attribute."""
    return ('/analytics/feeds/datasources/ga/accounts/%s/webproperties' %
        self.acct_id)


class ProfileQuery(AnalyticsBaseQuery):
  """Management API Profile Feed query class.

  Example Usage:
    queryUrl = ProfileQuery()
    queryUrl = ProfileQuery('123', 'UA-123-1', {'max-results': 100})
    queryUrl = ProfileQuery(acct_id='123',
                            web_prop_id='UA-123-1',
                            query={'max-results': 100})

    queryUrl2 = ProfileQuery()
    queryUrl2.acct_id = '123'
    queryUrl2.web_prop_id = 'UA-123-1'
    queryUrl2.query['max-results'] = 100

  Args:
    acct_id: string (optional) The account ID to filter results.
        Default is ~all.
    web_prop_id: string (optional) The web property ID to filter results.
        Default is ~all.
    query: dict (optional) A dictionary of query parameters.
  """

  def __init__(self, acct_id='~all', web_prop_id='~all', query={}, **kwargs):
    self.acct_id = acct_id
    self.web_prop_id = web_prop_id
    self.query = query
    gdata.client.GDQuery(self, **kwargs)

  @property
  def path(self):
    """Wrapper for path attribute."""
    return ('/analytics/feeds/datasources/ga/accounts/%s/webproperties'
        '/%s/profiles' % (self.acct_id, self.web_prop_id))


class GoalQuery(AnalyticsBaseQuery):
  """Management API Goal Feed query class.

  Example Usage:
    queryUrl = GoalQuery()
    queryUrl = GoalQuery('123', 'UA-123-1', '555',
        {'max-results': 100})
    queryUrl = GoalQuery(acct_id='123',
                         web_prop_id='UA-123-1',
                         profile_id='555',
                         query={'max-results': 100})

    queryUrl2 = GoalQuery()
    queryUrl2.acct_id = '123'
    queryUrl2.web_prop_id = 'UA-123-1'
    queryUrl2.query['max-results'] = 100

  Args:
    acct_id: string (optional) The account ID to filter results.
        Default is ~all.
    web_prop_id: string (optional) The web property ID to filter results.
        Default is ~all.
    profile_id: string (optional) The profile ID to filter results.
        Default is ~all.
    query: dict (optional) A dictionary of query parameters.
  """

  def __init__(self, acct_id='~all', web_prop_id='~all', profile_id='~all',
      query={}, **kwargs):
    self.acct_id = acct_id
    self.web_prop_id = web_prop_id
    self.profile_id = profile_id
    self.query = query or {}
    gdata.client.GDQuery(self, **kwargs)

  @property
  def path(self):
    """Wrapper for path attribute."""
    return ('/analytics/feeds/datasources/ga/accounts/%s/webproperties'
        '/%s/profiles/%s/goals' % (self.acct_id, self.web_prop_id,
        self.profile_id))


class AdvSegQuery(AnalyticsBaseQuery):
  """Management API Goal Feed query class.

  Example Usage:
    queryUrl = AdvSegQuery()
    queryUrl = AdvSegQuery({'max-results': 100})

    queryUrl1 = AdvSegQuery()
    queryUrl1.query['max-results'] = 100

  Args:
    query: dict (optional) A dictionary of query parameters.
  """

  path = '/analytics/feeds/datasources/ga/segments'

  def __init__(self, query={}, **kwargs):
    self.query = query
    gdata.client.GDQuery(self, **kwargs)
