#!/usr/bin/python
#
# Copyright 2009 Google Inc. All Rights Reserved.
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

"""Data model for parsing and generating XML for the Calendar Resource API."""


__author__ = 'Vic Fryzel <vf@google.com>'


import atom.core
import atom.data
import gdata.apps
import gdata.apps_property
import gdata.data


# This is required to work around a naming conflict between the Google
# Spreadsheets API and Python's built-in property function
pyproperty = property


# The apps:property name of the resourceId property
RESOURCE_ID_NAME = 'resourceId'
# The apps:property name of the resourceCommonName property
RESOURCE_COMMON_NAME_NAME = 'resourceCommonName'
# The apps:property name of the resourceDescription property
RESOURCE_DESCRIPTION_NAME = 'resourceDescription'
# The apps:property name of the resourceType property
RESOURCE_TYPE_NAME = 'resourceType'
# The apps:property name of the resourceEmail property
RESOURCE_EMAIL_NAME = 'resourceEmail'


class CalendarResourceEntry(gdata.data.GDEntry):
  """Represents a Calendar Resource entry in object form."""

  property = [gdata.apps_property.AppsProperty]

  def _GetProperty(self, name):
    """Get the apps:property value with the given name.

    Args:
      name: string Name of the apps:property value to get.

    Returns:
      The apps:property value with the given name, or None if the name was
      invalid.
    """

    for p in self.property:
      if p.name == name:
        return p.value
    return None

  def _SetProperty(self, name, value):
    """Set the apps:property value with the given name to the given value.

    Args:
      name: string Name of the apps:property value to set.
      value: string Value to give the apps:property value with the given name.
    """

    for i in range(len(self.property)):
      if self.property[i].name == name:
        self.property[i].value = value
        return
    self.property.append(gdata.apps_property.AppsProperty(name=name, value=value))

  def GetResourceId(self):
    """Get the resource ID of this Calendar Resource object.

    Returns:
      The resource ID of this Calendar Resource object as a string or None.
    """

    return self._GetProperty(RESOURCE_ID_NAME)

  def SetResourceId(self, value):
    """Set the resource ID of this Calendar Resource object.

    Args:
      value: string The new resource ID value to give this object.
    """

    self._SetProperty(RESOURCE_ID_NAME, value)

  resource_id = pyproperty(GetResourceId, SetResourceId)

  def GetResourceCommonName(self):
    """Get the common name of this Calendar Resource object.

    Returns:
      The common name of this Calendar Resource object as a string or None.
    """

    return self._GetProperty(RESOURCE_COMMON_NAME_NAME)

  def SetResourceCommonName(self, value):
    """Set the common name of this Calendar Resource object.

    Args:
      value: string The new common name value to give this object.
    """

    self._SetProperty(RESOURCE_COMMON_NAME_NAME, value)

  resource_common_name = pyproperty(
      GetResourceCommonName,
      SetResourceCommonName)

  def GetResourceDescription(self):
    """Get the description of this Calendar Resource object.

    Returns:
      The description of this Calendar Resource object as a string or None.
    """

    return self._GetProperty(RESOURCE_DESCRIPTION_NAME)

  def SetResourceDescription(self, value):
    """Set the description of this Calendar Resource object.
    
    Args:
      value: string The new description value to give this object.
    """

    self._SetProperty(RESOURCE_DESCRIPTION_NAME, value)

  resource_description = pyproperty(
      GetResourceDescription,
      SetResourceDescription)

  def GetResourceType(self):
    """Get the type of this Calendar Resource object.

    Returns:
      The type of this Calendar Resource object as a string or None.
    """

    return self._GetProperty(RESOURCE_TYPE_NAME)

  def SetResourceType(self, value):
    """Set the type value of this Calendar Resource object.

    Args:
      value: string The new type value to give this object.
    """

    self._SetProperty(RESOURCE_TYPE_NAME, value)

  resource_type = pyproperty(GetResourceType, SetResourceType)

  def GetResourceEmail(self):
    """Get the email of this Calendar Resource object.
    
    Returns:
    The email of this Calendar Resource object as a string or None.
    """
    
    return self._GetProperty(RESOURCE_EMAIL_NAME)
    
  resource_email = pyproperty(GetResourceEmail)

  def __init__(self, resource_id=None, resource_common_name=None,
               resource_description=None, resource_type=None, *args, **kwargs):
    """Constructs a new CalendarResourceEntry object with the given arguments.

    Args:
      resource_id: string (optional) The resource ID to give this new object.
      resource_common_name: string (optional) The common name to give this new
                            object.
      resource_description: string (optional) The description to give this new
                            object.
      resource_type: string (optional) The type to give this new object.
      args: The other parameters to pass to gdata.entry.GDEntry constructor. 
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor. 
    """
    super(CalendarResourceEntry, self).__init__(*args, **kwargs)
    if resource_id:
      self.resource_id = resource_id
    if resource_common_name:
      self.resource_common_name = resource_common_name
    if resource_description:
      self.resource_description = resource_description
    if resource_type:
      self.resource_type = resource_type


class CalendarResourceFeed(gdata.data.GDFeed):
  """Represents a feed of CalendarResourceEntry objects."""

  # Override entry so that this feed knows how to type its list of entries.
  entry = [CalendarResourceEntry]
