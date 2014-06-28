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


"""Contains a client to communicate with the Maps Data servers.

For documentation on the Maps Data API, see:
http://code.google.com/apis/maps/documentation/mapsdata/
"""


__author__ = 'api.roman.public@google.com (Roman Nurik)'


import gdata.client
import gdata.maps.data
import atom.data
import atom.http_core
import gdata.gauth


# List user's maps, takes a user ID, or 'default'.
MAP_URL_TEMPLATE = 'http://maps.google.com/maps/feeds/maps/%s/full'

# List map's features, takes a user ID (or 'default') and map ID.
MAP_FEATURE_URL_TEMPLATE = ('http://maps.google.com/maps'
                            '/feeds/features/%s/%s/full')

# The KML mime type
KML_CONTENT_TYPE = 'application/vnd.google-earth.kml+xml'


class MapsClient(gdata.client.GDClient):
  """Maps Data API GData client."""

  api_version = '2'
  auth_service = 'local'
  auth_scopes = gdata.gauth.AUTH_SCOPES['local']

  def get_maps(self, user_id='default', auth_token=None,
               desired_class=gdata.maps.data.MapFeed, **kwargs):
    """Retrieves a Map feed for the given user ID.

    Args:
      user_id: An optional string representing the user ID; should be 'default'.

    Returns:
      A gdata.maps.data.MapFeed.
    """
    return self.get_feed(MAP_URL_TEMPLATE % user_id, auth_token=auth_token,
                         desired_class=desired_class, **kwargs)

  GetMaps = get_maps

  def get_features(self, map_id, user_id='default', auth_token=None,
                   desired_class=gdata.maps.data.FeatureFeed, query=None,
                   **kwargs):
    """Retrieves a Feature feed for the given map ID/user ID combination.

    Args:
      map_id: A string representing the ID of the map whose features should be
          retrieved.
      user_id: An optional string representing the user ID; should be 'default'.

    Returns:
      A gdata.maps.data.FeatureFeed.
    """
    return self.get_feed(MAP_FEATURE_URL_TEMPLATE % (user_id, map_id),
                         auth_token=auth_token, desired_class=desired_class,
                         query=query, **kwargs)

  GetFeatures = get_features

  def create_map(self, title, summary=None, unlisted=False,
                 auth_token=None, title_type='text', summary_type='text',
                 **kwargs):
    """Creates a new map and posts it to the Maps Data servers.

    Args:
      title: A string representing the title of the new map.
      summary: An optional string representing the new map's description.
      unlisted: An optional boolean identifying whether the map should be
          unlisted (True) or public (False). Default False.

    Returns:
      A gdata.maps.data.Map.
    """
    new_entry = gdata.maps.data.Map(
        title=atom.data.Title(text=title, type=title_type))
    if summary:
      new_entry.summary = atom.data.Summary(text=summary, type=summary_type)
    if unlisted:
      new_entry.control = atom.data.Control(draft=atom.data.Draft(text='yes'))
    return self.post(new_entry, MAP_URL_TEMPLATE % 'default',
                     auth_token=auth_token, **kwargs)

  CreateMap = create_map

  def add_feature(self, map_id, title, content,
                  auth_token=None, title_type='text',
                  content_type=KML_CONTENT_TYPE, **kwargs):
    """Adds a new feature to the given map.

    Args:
      map_id: A string representing the ID of the map to which the new feature
          should be added.
      title: A string representing the name/title of the new feature.
      content: A KML string or gdata.maps.data.KmlContent object representing
          the new feature's KML contents, including its description.

    Returns:
      A gdata.maps.data.Feature.
    """
    if content_type == KML_CONTENT_TYPE:
      if type(content) != gdata.maps.data.KmlContent:
        content = gdata.maps.data.KmlContent(kml=content)
    else:
      content = atom.data.Content(content=content, type=content_type)
    new_entry = gdata.maps.data.Feature(
        title=atom.data.Title(text=title, type=title_type),
        content=content)
    return self.post(new_entry, MAP_FEATURE_URL_TEMPLATE % ('default', map_id),
                     auth_token=auth_token, **kwargs)

  AddFeature = add_feature

  def update(self, entry, auth_token=None, **kwargs):
    """Sends changes to a given map or feature entry to the Maps Data servers.

    Args:
      entry: A gdata.maps.data.Map or gdata.maps.data.Feature to be updated
          server-side.
    """
    # The Maps Data API does not currently support ETags, so for now remove
    # the ETag before performing an update.
    old_etag = entry.etag
    entry.etag = None
    response = gdata.client.GDClient.update(self, entry,
                                            auth_token=auth_token, **kwargs)
    entry.etag = old_etag
    return response

  Update = update

  def delete(self, entry_or_uri, auth_token=None, **kwargs):
    """Deletes the given entry or entry URI server-side.

    Args:
      entry_or_uri: A gdata.maps.data.Map, gdata.maps.data.Feature, or URI
          string representing the entry to delete.
    """
    if isinstance(entry_or_uri, (str, unicode, atom.http_core.Uri)):
      return gdata.client.GDClient.delete(self, entry_or_uri,
                                          auth_token=auth_token, **kwargs)
    # The Maps Data API does not currently support ETags, so for now remove
    # the ETag before performing a delete.
    old_etag = entry_or_uri.etag
    entry_or_uri.etag = None
    response = gdata.client.GDClient.delete(self, entry_or_uri,
                                            auth_token=auth_token, **kwargs)
    # TODO: if GDClient.delete raises and exception, the entry's etag may be
    # left as None. Should revisit this logic.
    entry_or_uri.etag = old_etag
    return response

  Delete = delete
