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

"""CalendarResourceClient simplifies Calendar Resources API calls.

CalendarResourceClient extends gdata.client.GDClient to ease interaction with
the Google Apps Calendar Resources API.  These interactions include the ability
to create, retrieve, update, and delete calendar resources in a Google Apps
domain.
"""


__author__ = 'Vic Fryzel <vf@google.com>'


import gdata.calendar_resource.data
import gdata.client
import urllib


# Feed URI template.  This must end with a /
# The strings in this template are eventually replaced with the API version 
# and Google Apps domain name, respectively.
RESOURCE_FEED_TEMPLATE = '/a/feeds/calendar/resource/%s/%s/'


class CalendarResourceClient(gdata.client.GDClient):
  """Client extension for the Google Calendar Resource API service.

  Attributes:
    host: string The hostname for the Calendar Resouce API service.
    api_version: string The version of the Calendar Resource API.
  """

  host = 'apps-apis.google.com'
  api_version = '2.0'
  auth_service = 'apps'
  auth_scopes = gdata.gauth.AUTH_SCOPES['apps']
  ssl = True

  def __init__(self, domain, auth_token=None, **kwargs):
    """Constructs a new client for the Calendar Resource API.

    Args:
      domain: string The Google Apps domain with Calendar Resources.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or 
          OAuthToken which authorizes this client to edit the calendar resource
          data.
      kwargs: The other parameters to pass to the gdata.client.GDClient
          constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.domain = domain

  def make_resource_feed_uri(self, resource_id=None, params=None):
    """Creates a resource feed URI for the Calendar Resource API.

    Using this client's Google Apps domain, create a feed URI for calendar
    resources in that domain. If a resource_id is provided, return a URI
    for that specific resource.  If params are provided, append them as GET
    params.

    Args:
      resource_id: string (optional) The ID of the calendar resource for which
          to make a feed URI.
      params: dict (optional) key -> value params to append as GET vars to the
          URI. Example: params={'start': 'my-resource-id'}
    Returns:
      A string giving the URI for calendar resources for this client's Google
      Apps domain.
    """
    uri = RESOURCE_FEED_TEMPLATE % (self.api_version, self.domain)
    if resource_id:
      uri += resource_id
    if params:
      uri += '?' + urllib.urlencode(params)
    return uri

  MakeResourceFeedUri = make_resource_feed_uri

  def get_resource_feed(self, uri=None, **kwargs):
    """Fetches a ResourceFeed of calendar resources at the given URI.

    Args:
      uri: string The URI of the feed to pull.
      kwargs: The other parameters to pass to gdata.client.GDClient.get_feed().

    Returns:
      A ResourceFeed object representing the feed at the given URI.
    """

    if uri is None:
      uri = self.MakeResourceFeedUri()
    return self.get_feed(
        uri,
        desired_class=gdata.calendar_resource.data.CalendarResourceFeed,
        **kwargs)

  GetResourceFeed = get_resource_feed
  
  def get_resource(self, uri=None, resource_id=None, **kwargs):
    """Fetches a single calendar resource by resource ID.

    Args:
      uri: string The base URI of the feed from which to fetch the resource.
      resource_id: string The string ID of the Resource to fetch.
      kwargs: The other parameters to pass to gdata.client.GDClient.get_entry().

    Returns:
      A Resource object representing the calendar resource with the given 
      base URI and resource ID.
    """

    if uri is None:
      uri = self.MakeResourceFeedUri(resource_id)
    return self.get_entry(
        uri,
        desired_class=gdata.calendar_resource.data.CalendarResourceEntry,
        **kwargs)

  GetResource = get_resource

  def create_resource(self, resource_id, resource_common_name=None,
                      resource_description=None, resource_type=None, **kwargs):
    """Creates a calendar resource with the given properties.

    Args:
      resource_id: string The resource ID of the calendar resource.
      resource_common_name: string (optional) The common name of the resource.
      resource_description: string (optional) The description of the resource.
      resource_type: string (optional) The type of the resource.
      kwargs: The other parameters to pass to gdata.client.GDClient.post().

    Returns:
      gdata.calendar_resource.data.CalendarResourceEntry of the new resource.
    """
    new_resource = gdata.calendar_resource.data.CalendarResourceEntry(
        resource_id=resource_id,
        resource_common_name=resource_common_name,
        resource_description=resource_description,
        resource_type=resource_type)
    return self.post(new_resource, self.MakeResourceFeedUri(), **kwargs)

  CreateResource = create_resource
  
  def update_resource(self, resource_id, resource_common_name=None,
                      resource_description=None, resource_type=None, **kwargs):
    """Updates the calendar resource with the given resource ID.

    Args:
      resource_id: string The resource ID of the calendar resource to update.
      resource_common_name: string (optional) The common name to give the
          resource.
      resource_description: string (optional) The description to give the
          resource.
      resource_type: string (optional) The type to give the resource.
      kwargs: The other parameters to pass to gdata.client.GDClient.update().

    Returns:
      gdata.calendar_resource.data.CalendarResourceEntry of the updated
      resource.
    """
    new_resource = gdata.calendar_resource.data.CalendarResourceEntry(
        resource_id=resource_id,
        resource_common_name=resource_common_name,
        resource_description=resource_description,
        resource_type=resource_type)
    return self.update(new_resource, uri=self.MakeResourceFeedUri(resource_id),
                       **kwargs)

  UpdateResource = update_resource

  def delete_resource(self, resource_id, **kwargs):
    """Deletes the calendar resource with the given resource ID.

    Args:
      resource_id: string The resource ID of the calendar resource to delete.
      kwargs: The other parameters to pass to gdata.client.GDClient.delete()

    Returns:
      An HTTP response object.  See gdata.client.request().
    """

    return self.delete(self.MakeResourceFeedUri(resource_id), **kwargs)

  DeleteResource = delete_resource
