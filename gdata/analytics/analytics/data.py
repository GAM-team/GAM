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

"""Data model classes for parsing and generating XML for both the
Google Analytics Data Export and Management APIs. Although both APIs
operate on different parts of Google Analytics, they share common XML
elements and are released in the same module.

The Management API supports 5 feeds all using the same ManagementFeed
data class.
"""

__author__ = 'api.nickm@google.com (Nick Mihailovski)'


import gdata.data
import atom.core
import atom.data


# XML Namespace used in Google Analytics API entities.
DXP_NS = '{http://schemas.google.com/analytics/2009}%s'
GA_NS = '{http://schemas.google.com/ga/2009}%s'
GD_NS = '{http://schemas.google.com/g/2005}%s'


class GetProperty(object):
  """Utility class to simplify retrieving Property objects."""

  def get_property(self, name):
    """Helper method to return a propery object by its name attribute.

    Args:
      name: string The name of the <dxp:property> element to retrieve.

    Returns:
      A property object corresponding to the matching <dxp:property> element.
          if no property is found, None is returned.
    """

    for prop in self.property:
      if prop.name == name:
        return prop

    return None

  GetProperty = get_property


class GetMetric(object):
  """Utility class to simplify retrieving Metric objects."""

  def get_metric(self, name):
    """Helper method to return a propery value by its name attribute

    Args:
      name: string The name of the <dxp:metric> element to retrieve.

    Returns:
      A property object corresponding to the matching <dxp:metric> element.
          if no property is found, None is returned.
    """

    for met in self.metric:
      if met.name == name:
        return met

    return None

  GetMetric = get_metric


class GetDimension(object):
  """Utility class to simplify retrieving Dimension objects."""

  def get_dimension(self, name):
    """Helper method to return a dimention object by its name attribute

    Args:
      name: string The name of the <dxp:dimension> element to retrieve.

    Returns:
      A dimension object corresponding to the matching <dxp:dimension> element.
          if no dimension is found, None is returned.
    """

    for dim in self.dimension:
      if dim.name == name:
        return dim

    return None

  GetDimension = get_dimension


class GaLinkFinder(object):
  """Utility class to return specific links in Google Analytics feeds."""

  def get_parent_links(self):
    """Returns a list of all the parent links in an entry."""

    links = []
    for link in self.link:
      if link.rel == link.parent():
        links.append(link)

    return links

  GetParentLinks = get_parent_links

  def get_child_links(self):
    """Returns a list of all the child links in an entry."""

    links = []
    for link in self.link:
      if link.rel == link.child():
        links.append(link)

    return links

  GetChildLinks = get_child_links

  def get_child_link(self, target_kind):
    """Utility method to return one child link.

    Returns:
      A child link with the given target_kind. None if the target_kind was
      not found.
    """

    for link in self.link:
      if link.rel == link.child() and link.target_kind == target_kind:
        return link

    return None

  GetChildLink = get_child_link


class StartDate(atom.core.XmlElement):
  """Analytics Feed <dxp:startDate>"""
  _qname = DXP_NS % 'startDate'


class EndDate(atom.core.XmlElement):
  """Analytics Feed <dxp:endDate>"""
  _qname = DXP_NS % 'endDate'


class Metric(atom.core.XmlElement):
  """Analytics Feed <dxp:metric>"""
  _qname = DXP_NS % 'metric'
  name = 'name'
  type = 'type'
  value = 'value'
  confidence_interval = 'confidenceInterval'


class Aggregates(atom.core.XmlElement, GetMetric):
  """Analytics Data Feed <dxp:aggregates>"""
  _qname = DXP_NS % 'aggregates'
  metric = [Metric]


class ContainsSampledData(atom.core.XmlElement):
  """Analytics Data Feed <dxp:containsSampledData>"""
  _qname = DXP_NS % 'containsSampledData'


class TableId(atom.core.XmlElement):
  """Analytics Feed <dxp:tableId>"""
  _qname = DXP_NS % 'tableId'


class TableName(atom.core.XmlElement):
  """Analytics Feed <dxp:tableName>"""
  _qname = DXP_NS % 'tableName'


class Property(atom.core.XmlElement):
  """Analytics Feed <dxp:property>"""
  _qname = DXP_NS % 'property'
  name = 'name'
  value = 'value'


class Definition(atom.core.XmlElement):
  """Analytics Feed <dxp:definition>"""
  _qname = DXP_NS % 'definition'


class Segment(atom.core.XmlElement):
  """Analytics Feed <dxp:segment>"""
  _qname = DXP_NS % 'segment'
  id = 'id'
  name = 'name'
  definition = Definition


class Engagement(atom.core.XmlElement):
  """Analytics Feed <dxp:engagement>"""
  _qname = GA_NS % 'engagement'
  type = 'type'
  comparison = 'comparison'
  threshold_value = 'thresholdValue'


class Step(atom.core.XmlElement):
  """Analytics Feed <dxp:step>"""
  _qname = GA_NS % 'step'
  number = 'number'
  name = 'name'
  path = 'path'


class Destination(atom.core.XmlElement):
  """Analytics Feed <dxp:destination>"""
  _qname = GA_NS % 'destination'
  step = [Step]
  expression = 'expression'
  case_sensitive = 'caseSensitive'
  match_type = 'matchType'
  step1_required = 'step1Required'


class Goal(atom.core.XmlElement):
  """Analytics Feed <dxp:goal>"""
  _qname = GA_NS % 'goal'
  destination = Destination
  engagement = Engagement
  number = 'number'
  name = 'name'
  value = 'value'
  active = 'active'


class CustomVariable(atom.core.XmlElement):
  """Analytics Data Feed <dxp:customVariable>"""
  _qname = GA_NS % 'customVariable'
  index = 'index'
  name = 'name'
  scope = 'scope'


class DataSource(atom.core.XmlElement, GetProperty):
  """Analytics Data Feed <dxp:dataSource>"""
  _qname = DXP_NS % 'dataSource'
  table_id = TableId
  table_name = TableName
  property = [Property]


class Dimension(atom.core.XmlElement):
  """Analytics Feed <dxp:dimension>"""
  _qname = DXP_NS % 'dimension'
  name = 'name'
  value = 'value'


class AnalyticsLink(atom.data.Link):
  """Subclass of link <link>"""
  target_kind = GD_NS % 'targetKind'

  @classmethod
  def parent(cls):
    """Parent target_kind"""
    return '%s#parent' % GA_NS[1:-3]

  @classmethod
  def child(cls):
    """Child target_kind"""
    return '%s#child' % GA_NS[1:-3]


# Account Feed.
class AccountEntry(gdata.data.GDEntry, GetProperty):
  """Analytics Account Feed <entry>"""
  _qname = atom.data.ATOM_TEMPLATE % 'entry'
  table_id = TableId
  property = [Property]
  goal = [Goal]
  custom_variable = [CustomVariable]


class AccountFeed(gdata.data.GDFeed):
  """Analytics Account Feed <feed>"""
  _qname = atom.data.ATOM_TEMPLATE % 'feed'
  segment = [Segment]
  entry = [AccountEntry]


# Data Feed.
class DataEntry(gdata.data.GDEntry, GetMetric, GetDimension):
  """Analytics Data Feed <entry>"""
  _qname = atom.data.ATOM_TEMPLATE % 'entry'
  dimension = [Dimension]
  metric = [Metric]

  def get_object(self, name):
    """Returns either a Dimension or Metric object with the same name as the
    name parameter.

    Args:
      name: string The name of the object to retrieve.

    Returns:
      Either a Dimension or Object that has the same as the name parameter.
    """

    output = self.GetDimension(name)
    if not output:
      output = self.GetMetric(name)

    return output

  GetObject = get_object


class DataFeed(gdata.data.GDFeed):
  """Analytics Data Feed <feed>.

  Although there is only one datasource, it is stored in an array to replicate
  the design of the Java client library and ensure backwards compatibility if
  new data sources are added in the future.
  """

  _qname = atom.data.ATOM_TEMPLATE % 'feed'
  start_date = StartDate
  end_date = EndDate
  aggregates = Aggregates
  contains_sampled_data = ContainsSampledData
  data_source = [DataSource]
  entry = [DataEntry]
  segment = Segment

  def has_sampled_data(self):
    """Returns whether this feed has sampled data."""
    if (self.contains_sampled_data.text == 'true'):
      return True
    return False

  HasSampledData = has_sampled_data


# Management Feed.
class ManagementEntry(gdata.data.GDEntry, GetProperty, GaLinkFinder):
  """Analytics Managememt Entry <entry>."""

  _qname = atom.data.ATOM_TEMPLATE % 'entry'
  kind = GD_NS % 'kind'
  property  = [Property]
  goal = Goal
  segment = Segment
  link = [AnalyticsLink]


class ManagementFeed(gdata.data.GDFeed):
  """Analytics Management Feed <feed>.

  This class holds the data for all 5 Management API feeds: Account,
  Web Property, Profile, Goal, and Advanced Segment Feeds.
  """

  _qname = atom.data.ATOM_TEMPLATE % 'feed'
  entry = [ManagementEntry]
  kind = GD_NS % 'kind'
