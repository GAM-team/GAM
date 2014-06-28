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

"""Contains extensions to Atom objects used with Google Health."""

__author__ = 'api.eric@google.com (Eric Bidelman)'

import atom
import gdata


CCR_NAMESPACE = 'urn:astm-org:CCR'
METADATA_NAMESPACE = 'http://schemas.google.com/health/metadata'


class Ccr(atom.AtomBase):
  """Represents a Google Health <ContinuityOfCareRecord>."""

  _tag = 'ContinuityOfCareRecord'
  _namespace = CCR_NAMESPACE
  _children = atom.AtomBase._children.copy()

  def __init__(self, extension_elements=None,
               extension_attributes=None, text=None):
    atom.AtomBase.__init__(self, extension_elements=extension_elements,
                           extension_attributes=extension_attributes, text=text)

  def GetAlerts(self):
    """Helper for extracting Alert/Allergy data from the CCR.

    Returns:
      A list of ExtensionElements (one for each allergy found) or None if
      no allergies where found in this CCR.
    """
    try:
      body = self.FindExtensions('Body')[0]
      return body.FindChildren('Alerts')[0].FindChildren('Alert')
    except:
      return None

  def GetAllergies(self):
    """Alias for GetAlerts()."""
    return self.GetAlerts()

  def GetProblems(self):
    """Helper for extracting Problem/Condition data from the CCR.

    Returns:
      A list of ExtensionElements (one for each problem found) or None if
      no problems where found in this CCR.
    """
    try:
      body = self.FindExtensions('Body')[0]
      return body.FindChildren('Problems')[0].FindChildren('Problem')
    except:
      return None

  def GetConditions(self):
    """Alias for GetProblems()."""
    return self.GetProblems()

  def GetProcedures(self):
    """Helper for extracting Procedure data from the CCR.

    Returns:
      A list of ExtensionElements (one for each procedure found) or None if
      no procedures where found in this CCR.
    """
    try:
      body = self.FindExtensions('Body')[0]
      return body.FindChildren('Procedures')[0].FindChildren('Procedure')
    except:
      return None

  def GetImmunizations(self):
    """Helper for extracting Immunization data from the CCR.

    Returns:
      A list of ExtensionElements (one for each immunization found) or None if
      no immunizations where found in this CCR.
    """
    try:
      body = self.FindExtensions('Body')[0]
      return body.FindChildren('Immunizations')[0].FindChildren('Immunization')
    except:
      return None

  def GetMedications(self):
    """Helper for extracting Medication data from the CCR.

    Returns:
      A list of ExtensionElements (one for each medication found) or None if
      no medications where found in this CCR.
    """
    try:
      body = self.FindExtensions('Body')[0]
      return body.FindChildren('Medications')[0].FindChildren('Medication')
    except:
      return None

  def GetResults(self):
    """Helper for extracting Results/Labresults data from the CCR.

    Returns:
      A list of ExtensionElements (one for each result found) or None if
      no results where found in this CCR.
    """
    try:
      body = self.FindExtensions('Body')[0]
      return body.FindChildren('Results')[0].FindChildren('Result')
    except:
      return None


class ProfileEntry(gdata.GDataEntry):
  """The Google Health version of an Atom Entry."""

  _tag = gdata.GDataEntry._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}ContinuityOfCareRecord' % CCR_NAMESPACE] = ('ccr', Ccr)

  def __init__(self, ccr=None, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, title=None,
               updated=None, text=None, extension_elements=None,
               extension_attributes=None):
    self.ccr = ccr
    gdata.GDataEntry.__init__(
        self, author=author, category=category, content=content,
        atom_id=atom_id, link=link, published=published, title=title,
        updated=updated, extension_elements=extension_elements,
        extension_attributes=extension_attributes, text=text)


class ProfileFeed(gdata.GDataFeed):
  """A feed containing a list of Google Health profile entries."""

  _tag = gdata.GDataFeed._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [ProfileEntry])


class ProfileListEntry(gdata.GDataEntry):
  """The Atom Entry in the Google Health profile list feed."""

  _tag = gdata.GDataEntry._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()

  def GetProfileId(self):
    return self.content.text

  def GetProfileName(self):
    return self.title.text


class ProfileListFeed(gdata.GDataFeed):
  """A feed containing a list of Google Health profile list entries."""

  _tag = gdata.GDataFeed._tag
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [ProfileListEntry])


def ProfileEntryFromString(xml_string):
  """Converts an XML string into a ProfileEntry object.

  Args:
    xml_string: string The XML describing a Health profile feed entry.

  Returns:
    A ProfileEntry object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(ProfileEntry, xml_string)


def ProfileListEntryFromString(xml_string):
  """Converts an XML string into a ProfileListEntry object.

  Args:
    xml_string: string The XML describing a Health profile list feed entry.

  Returns:
    A ProfileListEntry object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(ProfileListEntry, xml_string)


def ProfileFeedFromString(xml_string):
  """Converts an XML string into a ProfileFeed object.

  Args:
    xml_string: string The XML describing a ProfileFeed feed.

  Returns:
    A ProfileFeed object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(ProfileFeed, xml_string)


def ProfileListFeedFromString(xml_string):
  """Converts an XML string into a ProfileListFeed object.

  Args:
    xml_string: string The XML describing a ProfileListFeed feed.

  Returns:
    A ProfileListFeed object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(ProfileListFeed, xml_string)
