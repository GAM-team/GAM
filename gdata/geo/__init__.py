# -*-*- encoding: utf-8 -*-*-
#
# This is gdata.photos.geo, implementing geological positioning in gdata structures
#
# $Id: __init__.py 81 2007-10-03 14:41:42Z havard.gulldahl $
#
# Copyright 2007 Håvard Gulldahl 
# Portions copyright 2007 Google Inc.
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

"""Picasa Web Albums uses the georss and gml namespaces for 
elements defined in the GeoRSS and Geography Markup Language specifications.

Specifically, Picasa Web Albums uses the following elements:

georss:where
gml:Point
gml:pos

http://code.google.com/apis/picasaweb/reference.html#georss_reference


Picasa Web Albums also accepts geographic-location data in two other formats:
W3C format and plain-GeoRSS (without GML) format. 
"""
# 
#Over the wire, the Picasa Web Albums only accepts and sends the 
#elements mentioned above, but this module will let you seamlessly convert 
#between the different formats (TODO 2007-10-18 hg)

__author__ = u'havard@gulldahl.no'# (Håvard Gulldahl)' #BUG: api chokes on non-ascii chars in __author__
__license__ = 'Apache License v2'


import atom
import gdata

GEO_NAMESPACE = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
GML_NAMESPACE = 'http://www.opengis.net/gml'
GEORSS_NAMESPACE = 'http://www.georss.org/georss'

class GeoBaseElement(atom.AtomBase):
  """Base class for elements.

  To add new elements, you only need to add the element tag name to self._tag
  and the namespace to self._namespace
  """
  
  _tag = ''
  _namespace = GML_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, name=None, extension_elements=None,
      extension_attributes=None, text=None):
    self.name = name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

class Pos(GeoBaseElement):
  """(string) Specifies a latitude and longitude, separated by a space,
  e.g. `35.669998 139.770004'"""
  
  _tag = 'pos'
def PosFromString(xml_string):
  return atom.CreateClassFromXMLString(Pos, xml_string)

class Point(GeoBaseElement):
  """(container)  Specifies a particular geographical point, by means of
  a <gml:pos> element."""
  
  _tag = 'Point'
  _children = atom.AtomBase._children.copy()
  _children['{%s}pos' % GML_NAMESPACE] = ('pos', Pos) 
  def __init__(self, pos=None, extension_elements=None, extension_attributes=None, text=None):
    GeoBaseElement.__init__(self, extension_elements=extension_elements,
                            extension_attributes=extension_attributes,
                            text=text)
    if pos is None:
      pos = Pos()
    self.pos=pos
def PointFromString(xml_string):
  return atom.CreateClassFromXMLString(Point, xml_string)

class Where(GeoBaseElement):
  """(container) Specifies a geographical location or region.
  A container element, containing a single <gml:Point> element.
  (Not to be confused with <gd:where>.) 
  
  Note that the (only) child attribute, .Point, is title-cased.
  This reflects the names of elements in the xml stream
  (principle of least surprise).
  
  As a convenience, you can get a tuple of (lat, lon) with Where.location(),
  and set the same data with Where.setLocation( (lat, lon) ).

  Similarly, there are methods to set and get only latitude and longitude.
  """
  
  _tag = 'where'
  _namespace = GEORSS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _children['{%s}Point' % GML_NAMESPACE] = ('Point', Point) 
  def __init__(self, point=None, extension_elements=None, extension_attributes=None, text=None):
    GeoBaseElement.__init__(self, extension_elements=extension_elements,
                            extension_attributes=extension_attributes,
                            text=text)
    if point is None:
      point = Point()
    self.Point=point
  def location(self):
    "(float, float) Return Where.Point.pos.text as a (lat,lon) tuple"
    try:
      return tuple([float(z) for z in self.Point.pos.text.split(' ')])
    except AttributeError:
      return tuple()
  def set_location(self, latlon):
    """(bool) Set Where.Point.pos.text from a (lat,lon) tuple.

    Arguments:
    lat (float): The latitude in degrees, from -90.0 to 90.0
    lon (float): The longitude in degrees, from -180.0 to 180.0
    
    Returns True on success.

    """
    
    assert(isinstance(latlon[0], float))
    assert(isinstance(latlon[1], float))
    try:
      self.Point.pos.text = "%s %s" % (latlon[0], latlon[1])
      return True
    except AttributeError:
      return False
  def latitude(self):
    "(float) Get the latitude value of the geo-tag. See also .location()"
    lat, lon = self.location()
    return lat
  
  def longitude(self):
    "(float) Get the longtitude value of the geo-tag. See also .location()"
    lat, lon = self.location()
    return lon

  longtitude = longitude

  def set_latitude(self, lat):
    """(bool) Set the latitude value of the geo-tag.

    Args:
    lat (float): The new latitude value

    See also .set_location()
    """
    _lat, lon = self.location()
    return self.set_location(lat, lon)
  
  def set_longitude(self, lon):
    """(bool) Set the longtitude value of the geo-tag.
    
    Args:
    lat (float): The new latitude value

    See also .set_location()
    """
    lat, _lon = self.location()
    return self.set_location(lat, lon)

  set_longtitude = set_longitude

def WhereFromString(xml_string):
  return atom.CreateClassFromXMLString(Where, xml_string)
  
