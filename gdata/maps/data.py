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


"""Data model classes for parsing and generating XML for the Maps Data API."""


__author__ = 'api.roman.public@google.com (Roman Nurik)'


import re
import atom.core
import gdata.data


MAP_ATOM_ID_PATTERN = re.compile('/maps/feeds/maps/'
                                 '(?P<user_id>\w+)/'
                                 '(?P<map_id>\w+)$')

FEATURE_ATOM_ID_PATTERN = re.compile('/maps/feeds/features/'
                                     '(?P<user_id>\w+)/'
                                     '(?P<map_id>\w+)/'
                                     '(?P<feature_id>\w+)$')

# The KML mime type
KML_CONTENT_TYPE = 'application/vnd.google-earth.kml+xml'

# The OGC KML 2.2 namespace
KML_NAMESPACE = 'http://www.opengis.net/kml/2.2'

class MapsDataEntry(gdata.data.GDEntry):
  """Adds convenience methods inherited by all Maps Data entries."""

  def get_user_id(self):
    """Extracts the user ID of this entry."""
    if self.id.text:
      match = self.__class__.atom_id_pattern.search(self.id.text)
      if match:
        return match.group('user_id')
    return None

  GetUserId = get_user_id

  def get_map_id(self):
    """Extracts the map ID of this entry."""
    if self.id.text:
      match = self.__class__.atom_id_pattern.search(self.id.text)
      if match:
        return match.group('map_id')
    return None

  GetMapId = get_map_id


class Map(MapsDataEntry):
  """Represents a map which belongs to the user."""
  atom_id_pattern = MAP_ATOM_ID_PATTERN


class MapFeed(gdata.data.GDFeed):
  """Represents an atom feed of maps."""
  entry = [Map]


class KmlContent(atom.data.Content):
  """Represents an atom content element that encapsulates KML content."""

  def __init__(self, **kwargs):
    super(KmlContent, self).__init__(type=KML_CONTENT_TYPE, **kwargs)
    if 'kml' in kwargs:
      self.kml = kwargs['kml']

  def _get_kml(self):
    if self.children:
      return self.children[0]
    else:
      return ''

  def _set_kml(self, kml):
    if not kml:
      self.children = []
      return

    if type(kml) == str:
      kml = atom.core.parse(kml)
      if not kml.namespace:
        kml.namespace = KML_NAMESPACE

    self.children = [kml]

  kml = property(_get_kml, _set_kml)


class Feature(MapsDataEntry):
  """Represents a single feature in a map."""
  atom_id_pattern = FEATURE_ATOM_ID_PATTERN
  content = KmlContent

  def get_feature_id(self):
    """Extracts the feature ID of this feature."""
    if self.id.text:
      match = self.__class__.atom_id_pattern.search(self.id.text)
      if match:
        return match.group('feature_id')
    return None

  GetFeatureId = get_feature_id


class FeatureFeed(gdata.data.GDFeed):
  """Represents an atom feed of features."""
  entry = [Feature]
