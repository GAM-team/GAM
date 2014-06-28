#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.
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

"""Contains objects used with Google Apps."""

__author__ = 'google-apps-apis@googlegroups.com'


import atom
import gdata


# XML namespaces which are often used in Google Apps entity.
APPS_NAMESPACE = 'http://schemas.google.com/apps/2006'
APPS_TEMPLATE = '{http://schemas.google.com/apps/2006}%s'


class Rfc822Msg(atom.AtomBase):
  """The Migration rfc822Msg element."""

  _tag = 'rfc822Msg'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['encoding'] = 'encoding'

  def __init__(self, extension_elements=None,
               extension_attributes=None, text=None):
    self.text = text
    self.encoding = 'base64'
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def Rfc822MsgFromString(xml_string):
  """Parse in the Rrc822 message from the XML definition."""

  return atom.CreateClassFromXMLString(Rfc822Msg, xml_string)


class MailItemProperty(atom.AtomBase):
  """The Migration mailItemProperty element."""

  _tag = 'mailItemProperty'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.value = value
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def MailItemPropertyFromString(xml_string):
  """Parse in the MailItemProperiy from the XML definition."""

  return atom.CreateClassFromXMLString(MailItemProperty, xml_string)


class Label(atom.AtomBase):
  """The Migration label element."""

  _tag = 'label'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['labelName'] = 'label_name'

  def __init__(self, label_name=None,
               extension_elements=None, extension_attributes=None,
               text=None):
    self.label_name = label_name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def LabelFromString(xml_string):
  """Parse in the mailItemProperty from the XML definition."""

  return atom.CreateClassFromXMLString(Label, xml_string)


class MailEntry(gdata.GDataEntry):
  """A Google Migration flavor of an Atom Entry."""

  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}rfc822Msg' % APPS_NAMESPACE] = ('rfc822_msg', Rfc822Msg)
  _children['{%s}mailItemProperty' % APPS_NAMESPACE] = ('mail_item_property',
                                                        [MailItemProperty])
  _children['{%s}label' % APPS_NAMESPACE] = ('label', [Label])

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None,
               rfc822_msg=None, mail_item_property=None, label=None,
               extended_property=None,
               extension_elements=None, extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated)
    self.rfc822_msg = rfc822_msg
    self.mail_item_property = mail_item_property
    self.label = label
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def MailEntryFromString(xml_string):
  """Parse in the MailEntry from the XML definition."""

  return atom.CreateClassFromXMLString(MailEntry, xml_string)


class BatchMailEntry(gdata.BatchEntry):
  """A Google Migration flavor of an Atom Entry."""

  _tag = gdata.BatchEntry._tag
  _namespace = gdata.BatchEntry._namespace
  _children = gdata.BatchEntry._children.copy()
  _attributes = gdata.BatchEntry._attributes.copy()
  _children['{%s}rfc822Msg' % APPS_NAMESPACE] = ('rfc822_msg', Rfc822Msg)
  _children['{%s}mailItemProperty' % APPS_NAMESPACE] = ('mail_item_property',
                                                        [MailItemProperty])
  _children['{%s}label' % APPS_NAMESPACE] = ('label', [Label])

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None,
               rfc822_msg=None, mail_item_property=None, label=None,
               batch_operation=None, batch_id=None, batch_status=None,
               extended_property=None,
               extension_elements=None, extension_attributes=None, text=None):

    gdata.BatchEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              batch_operation=batch_operation,
                              batch_id=batch_id, batch_status=batch_status,
                              title=title, updated=updated)
    self.rfc822_msg = rfc822_msg or None
    self.mail_item_property = mail_item_property or []
    self.label = label or []
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def BatchMailEntryFromString(xml_string):
  """Parse in the BatchMailEntry from the XML definition."""

  return atom.CreateClassFromXMLString(BatchMailEntry, xml_string)


class BatchMailEventFeed(gdata.BatchFeed):
  """A Migration event feed flavor of an Atom Feed."""

  _tag = gdata.BatchFeed._tag
  _namespace = gdata.BatchFeed._namespace
  _children = gdata.BatchFeed._children.copy()
  _attributes = gdata.BatchFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [BatchMailEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None,
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, interrupted=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.BatchFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon, atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             interrupted=interrupted,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)


class MailEntryProperties(object):
  """Represents a mail message and its attributes."""

  def __init__(self, mail_message=None, mail_item_properties=None,
               mail_labels=None, identifier=None):
    self.mail_message = mail_message
    self.mail_item_properties = mail_item_properties or []
    self.mail_labels = mail_labels or []
    self.identifier = identifier


def BatchMailEventFeedFromString(xml_string):
  """Parse in the BatchMailEventFeed from the XML definition."""

  return atom.CreateClassFromXMLString(BatchMailEventFeed, xml_string)
