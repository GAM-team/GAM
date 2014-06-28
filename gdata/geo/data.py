#!/usr/bin/python
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

"""Contains the data classes of the Geography Extension"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core


GEORSS_TEMPLATE = '{http://www.georss.org/georss/}%s'
GML_TEMPLATE = '{http://www.opengis.net/gml/}%s'
GEO_TEMPLATE = '{http://www.w3.org/2003/01/geo/wgs84_pos#/}%s'


class GeoLat(atom.core.XmlElement):
  """Describes a W3C latitude."""
  _qname = GEO_TEMPLATE % 'lat'


class GeoLong(atom.core.XmlElement):
  """Describes a W3C longitude."""
  _qname = GEO_TEMPLATE % 'long'


class GeoRssBox(atom.core.XmlElement):
  """Describes a geographical region."""
  _qname = GEORSS_TEMPLATE % 'box'


class GeoRssPoint(atom.core.XmlElement):
  """Describes a geographical location."""
  _qname = GEORSS_TEMPLATE % 'point'


class GmlLowerCorner(atom.core.XmlElement):
  """Describes a lower corner of a region."""
  _qname = GML_TEMPLATE % 'lowerCorner'


class GmlPos(atom.core.XmlElement):
  """Describes a latitude and longitude."""
  _qname = GML_TEMPLATE % 'pos'


class GmlPoint(atom.core.XmlElement):
  """Describes a particular geographical point."""
  _qname = GML_TEMPLATE % 'Point'
  pos = GmlPos


class GmlUpperCorner(atom.core.XmlElement):
  """Describes an upper corner of a region."""
  _qname = GML_TEMPLATE % 'upperCorner'


class GmlEnvelope(atom.core.XmlElement):
  """Describes a Gml geographical region."""
  _qname = GML_TEMPLATE % 'Envelope'
  lower_corner = GmlLowerCorner
  upper_corner = GmlUpperCorner


class GeoRssWhere(atom.core.XmlElement):
  """Describes a geographical location or region."""
  _qname = GEORSS_TEMPLATE % 'where'
  Point = GmlPoint
  Envelope = GmlEnvelope


class W3CPoint(atom.core.XmlElement):
  """Describes a W3C geographical location."""
  _qname = GEO_TEMPLATE % 'Point'
  long = GeoLong
  lat = GeoLat


