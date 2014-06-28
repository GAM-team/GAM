#!/usr/bin/python
#
# Copyright 2009 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LicensingClient simplifies Google Apps Marketplace Licensing API calls.

LicensingClient extends gdata.client.GDClient to ease interaction with
the Google Apps Marketplace Licensing API.  These interactions include the ability
to retrieve License informations for an application in the Google Apps Marketplace.
"""


__author__ = 'Alexandre Vivien <alex@simplecode.fr>'

import gdata.marketplace.data
import gdata.client
import urllib


# Feed URI template.  This must end with a /
# The strings in this template are eventually replaced with the API version 
# and Google Apps domain name, respectively.
LICENSE_ROOT_URL = 'http://feedserver-enterprise.googleusercontent.com'
LICENSE_FEED_TEMPLATE = '%s/license?bq=' % LICENSE_ROOT_URL
LICENSE_NOTIFICATIONS_FEED_TEMPLATE = '%s/licensenotification?bq=' % LICENSE_ROOT_URL


class LicensingClient(gdata.client.GDClient):
  """Client extension for the Google Apps Marketplace Licensing API service.

  Attributes:
    host: string The hostname for the Google Apps Marketplace Licensing API service.
    api_version: string The version of the Google Apps Marketplace Licensing API.
  """

  api_version = '1.0'
  auth_service = 'apps'
  auth_scopes = gdata.gauth.AUTH_SCOPES['apps']
  ssl = False

  def __init__(self, domain, auth_token=None, **kwargs):
    """Constructs a new client for the Google Apps Marketplace Licensing API.

    Args:
      domain: string The Google Apps domain with the application installed.
      auth_token: (optional) gdata.gauth.OAuthToken which authorizes this client to retrieve the License information.
      kwargs: The other parameters to pass to the gdata.client.GDClient constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.domain = domain

  def make_license_feed_uri(self, app_id=None, params=None):
    """Creates a license feed URI for the Google Apps Marketplace Licensing API.

    Using this client's Google Apps domain, create a license feed URI for a particular application 
    in this domain. If params are provided, append them as GET params.

    Args:
      app_id: string The ID of the application for which to make a license feed URI.
      params: dict (optional) key -> value params to append as GET vars to the
          URI. Example: params={'start': 'my-resource-id'}
    Returns:
      A string giving the URI for the application's license for this client's Google
      Apps domain.
    """
    parameters = '[appid=%s][domain=%s]' % (app_id, self.domain)
    uri = LICENSE_FEED_TEMPLATE + urllib.quote_plus(parameters)
    if params:
      uri += '&' + urllib.urlencode(params)
    return uri

  MakeLicenseFeedUri = make_license_feed_uri
  
  def make_license_notifications_feed_uri(self, app_id=None, startdatetime=None, max_results=None, params=None):
    """Creates a license notifications feed URI for the Google Apps Marketplace Licensing API.

    Using this client's Google Apps domain, create a license notifications feed URI for a particular application. 
    If params are provided, append them as GET params.

    Args:
      app_id: string The ID of the application for which to make a license feed URI.
      startdatetime: Start date to retrieve the License notifications.
      max_results: Number of results per page. Maximum is 100.
      params: dict (optional) key -> value params to append as GET vars to the
          URI. Example: params={'start': 'my-resource-id'}
    Returns:
      A string giving the URI for the application's license notifications for this client's Google
      Apps domain.
    """
    parameters = '[appid=%s]' % (app_id)
    if startdatetime:
      parameters += '[startdatetime=%s]' % startdatetime
    else:
      parameters += '[startdatetime=1970-01-01T00:00:00Z]'
    if max_results:
      parameters += '[max-results=%s]' % max_results
    else:
      parameters += '[max-results=100]'
    uri = LICENSE_NOTIFICATIONS_FEED_TEMPLATE + urllib.quote_plus(parameters)
    if params:
      uri += '&' + urllib.urlencode(params)
    return uri

  MakeLicenseNotificationsFeedUri = make_license_notifications_feed_uri
  
  def get_license(self, uri=None, app_id=None, **kwargs):
    """Fetches the application's license by application ID.

    Args:
      uri: string The base URI of the feed from which to fetch the license.
      app_id: string The string ID of the application for which to fetch the license.
      kwargs: The other parameters to pass to gdata.client.GDClient.get_entry().

    Returns:
      A License feed object representing the license with the given 
      base URI and application ID.
    """

    if uri is None:
      uri = self.MakeLicenseFeedUri(app_id)
    return self.get_feed(uri,
                          desired_class=gdata.marketplace.data.LicenseFeed,
                          **kwargs)

  GetLicense = get_license
  
  def get_license_notifications(self, uri=None, app_id=None, startdatetime=None, max_results=None, **kwargs):
    """Fetches the application's license notifications by application ID.

    Args:
      uri: string The base URI of the feed from which to fetch the license.
      app_id: string The string ID of the application for which to fetch the license.
      startdatetime: Start date to retrieve the License notifications.
      max_results: Number of results per page. Maximum is 100.
      kwargs: The other parameters to pass to gdata.client.GDClient.get_entry().

    Returns:
      A License feed object representing the license notifications with the given 
      base URI and application ID.
    """

    if uri is None:
      uri = self.MakeLicenseNotificationsFeedUri(app_id, startdatetime, max_results)
    return self.get_feed(uri,
                         desired_class=gdata.marketplace.data.LicenseFeed,
                         **kwargs)

  GetLicenseNotifications = get_license_notifications
