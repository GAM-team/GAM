#!/usr/bin/python
#
# Original Copyright (C) 2006 Google Inc.
# Refactored in 2009 to work for Google Analytics by Sal Uryasev at Juice Inc.
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
#
# Note that this module will not function without specifically adding
# 'analytics': [  #Google Analytics
#  'https://www.google.com/analytics/feeds/'],
# to CLIENT_LOGIN_SCOPES in the gdata/service.py file

"""Contains extensions to Atom objects used with Google Analytics."""

__author__ = 'api.suryasev (Sal Uryasev)'

import atom
import gdata

GAN_NAMESPACE = 'http://schemas.google.com/analytics/2009'

class TableId(gdata.GDataEntry):
  """tableId element."""
  _tag = 'tableId'
  _namespace = GAN_NAMESPACE  

class Property(gdata.GDataEntry):
  _tag = 'property'
  _namespace = GAN_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  
  _attributes['name'] = 'name'
  _attributes['value'] = 'value'
  
  def __init__(self, name=None, value=None, *args, **kwargs):
    self.name = name
    self.value = value
    super(Property, self).__init__(*args, **kwargs)
    
  def __str__(self):
    return self.value
      
  def __repr__(self):
    return self.value

class AccountListEntry(gdata.GDataEntry):
  """The Google Documents version of an Atom Entry"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}tableId' % GAN_NAMESPACE] = ('tableId', 
                          [TableId])
  _children['{%s}property' % GAN_NAMESPACE] = ('property', 
                          [Property])

  def __init__(self, tableId=None, property=None,
         *args, **kwargs):
    self.tableId = tableId
    self.property = property
    super(AccountListEntry, self).__init__(*args, **kwargs)


def AccountListEntryFromString(xml_string):
  """Converts an XML string into an AccountListEntry object.

  Args:
  xml_string: string The XML describing a Document List feed entry.

  Returns:
  A AccountListEntry object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(AccountListEntry, xml_string)


class AccountListFeed(gdata.GDataFeed):
  """A feed containing a list of Google Documents Items"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                          [AccountListEntry])


def AccountListFeedFromString(xml_string):
  """Converts an XML string into an AccountListFeed object.

  Args:
  xml_string: string The XML describing an AccountList feed.

  Returns:
  An AccountListFeed object corresponding to the given XML.
  All properties are also linked to with a direct reference
  from each entry object for convenience. (e.g. entry.AccountName)
  """
  feed = atom.CreateClassFromXMLString(AccountListFeed, xml_string)
  for entry in feed.entry:
    for pro in entry.property:
      entry.__dict__[pro.name.replace('ga:','')] = pro
    for td in entry.tableId:
      td.__dict__['value'] = td.text
  return feed

class Dimension(gdata.GDataEntry):
  _tag = 'dimension'
  _namespace = GAN_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  
  _attributes['name'] = 'name'
  _attributes['value'] = 'value'
  _attributes['type'] = 'type'
  _attributes['confidenceInterval'] = 'confidence_interval'
  
  def __init__(self, name=None, value=None, type=None, 
               confidence_interval = None, *args, **kwargs):
    self.name = name
    self.value = value
    self.type = type
    self.confidence_interval = confidence_interval
    super(Dimension, self).__init__(*args, **kwargs)   
    
  def __str__(self):
    return self.value

  def __repr__(self):
    return self.value 
    
class Metric(gdata.GDataEntry):
  _tag = 'metric'
  _namespace = GAN_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  
  _attributes['name'] = 'name'
  _attributes['value'] = 'value'
  _attributes['type'] = 'type'
  _attributes['confidenceInterval'] = 'confidence_interval'
  
  def __init__(self, name=None, value=None, type=None, 
               confidence_interval = None, *args, **kwargs):
    self.name = name
    self.value = value
    self.type = type
    self.confidence_interval = confidence_interval
    super(Metric, self).__init__(*args, **kwargs)
    
  def __str__(self):
    return self.value

  def __repr__(self):
    return self.value
  
class AnalyticsDataEntry(gdata.GDataEntry):
  """The Google Analytics version of an Atom Entry"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  
  _children['{%s}dimension' % GAN_NAMESPACE] = ('dimension', 
                          [Dimension])
                          
  _children['{%s}metric' % GAN_NAMESPACE] = ('metric', 
                         [Metric])
                         
  def __init__(self, dimension=None, metric=None, *args, **kwargs):
    self.dimension = dimension
    self.metric = metric
    
    super(AnalyticsDataEntry, self).__init__(*args, **kwargs)

class AnalyticsDataFeed(gdata.GDataFeed):
  """A feed containing a list of Google Analytics Data Feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                          [AnalyticsDataEntry])
                    
                         
"""
Data Feed
"""

def AnalyticsDataFeedFromString(xml_string):
  """Converts an XML string into an AccountListFeed object.

  Args:
  xml_string: string The XML describing an AccountList feed.

  Returns:
  An AccountListFeed object corresponding to the given XML.
  Each metric and dimension is also referenced directly from
  the entry for easier access. (e.g. entry.keyword.value)
  """
  feed = atom.CreateClassFromXMLString(AnalyticsDataFeed, xml_string)
  if feed.entry:
    for entry in feed.entry:
      for met in entry.metric:
        entry.__dict__[met.name.replace('ga:','')] = met
      if entry.dimension is not None:
        for dim in entry.dimension:
          entry.__dict__[dim.name.replace('ga:','')] = dim
        
  return feed
