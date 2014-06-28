#!/usr/bin/env python
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

"""Contains extensions to ElementWrapper objects used with Google Contacts."""

__author__ = 'dbrattli (Dag Brattli)'


import atom
import gdata


## Constants from http://code.google.com/apis/gdata/elements.html ##
REL_HOME = 'http://schemas.google.com/g/2005#home'
REL_WORK = 'http://schemas.google.com/g/2005#work'
REL_OTHER = 'http://schemas.google.com/g/2005#other'

# AOL Instant Messenger protocol
IM_AIM = 'http://schemas.google.com/g/2005#AIM'
IM_MSN = 'http://schemas.google.com/g/2005#MSN'  # MSN Messenger protocol
IM_YAHOO = 'http://schemas.google.com/g/2005#YAHOO'  # Yahoo Messenger protocol
IM_SKYPE = 'http://schemas.google.com/g/2005#SKYPE'  # Skype protocol
IM_QQ = 'http://schemas.google.com/g/2005#QQ'  # QQ protocol
# Google Talk protocol
IM_GOOGLE_TALK = 'http://schemas.google.com/g/2005#GOOGLE_TALK'
IM_ICQ = 'http://schemas.google.com/g/2005#ICQ'  # ICQ protocol
IM_JABBER = 'http://schemas.google.com/g/2005#JABBER'  # Jabber protocol
IM_NETMEETING = 'http://schemas.google.com/g/2005#netmeeting'  # NetMeeting

PHOTO_LINK_REL = 'http://schemas.google.com/contacts/2008/rel#photo'
PHOTO_EDIT_LINK_REL = 'http://schemas.google.com/contacts/2008/rel#edit-photo'

# Different phone types, for more info see:
# http://code.google.com/apis/gdata/docs/2.0/elements.html#gdPhoneNumber
PHONE_CAR = 'http://schemas.google.com/g/2005#car'
PHONE_FAX = 'http://schemas.google.com/g/2005#fax'
PHONE_GENERAL = 'http://schemas.google.com/g/2005#general'
PHONE_HOME = REL_HOME
PHONE_HOME_FAX = 'http://schemas.google.com/g/2005#home_fax'
PHONE_INTERNAL = 'http://schemas.google.com/g/2005#internal-extension'
PHONE_MOBILE = 'http://schemas.google.com/g/2005#mobile'
PHONE_OTHER = REL_OTHER
PHONE_PAGER = 'http://schemas.google.com/g/2005#pager'
PHONE_SATELLITE = 'http://schemas.google.com/g/2005#satellite'
PHONE_VOIP = 'http://schemas.google.com/g/2005#voip'
PHONE_WORK = REL_WORK
PHONE_WORK_FAX = 'http://schemas.google.com/g/2005#work_fax'
PHONE_WORK_MOBILE = 'http://schemas.google.com/g/2005#work_mobile'
PHONE_WORK_PAGER = 'http://schemas.google.com/g/2005#work_pager'
PHONE_MAIN = 'http://schemas.google.com/g/2005#main'
PHONE_ASSISTANT = 'http://schemas.google.com/g/2005#assistant'
PHONE_CALLBACK = 'http://schemas.google.com/g/2005#callback'
PHONE_COMPANY_MAIN = 'http://schemas.google.com/g/2005#company_main'
PHONE_ISDN = 'http://schemas.google.com/g/2005#isdn'
PHONE_OTHER_FAX = 'http://schemas.google.com/g/2005#other_fax'
PHONE_RADIO = 'http://schemas.google.com/g/2005#radio'
PHONE_TELEX = 'http://schemas.google.com/g/2005#telex'
PHONE_TTY_TDD = 'http://schemas.google.com/g/2005#tty_tdd'

EXTERNAL_ID_ORGANIZATION = 'organization'

RELATION_MANAGER = 'manager'

CONTACTS_NAMESPACE = 'http://schemas.google.com/contact/2008'


class GDataBase(atom.AtomBase):
  """The Google Contacts intermediate class from atom.AtomBase."""

  _namespace = gdata.GDATA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, text=None,
               extension_elements=None, extension_attributes=None):
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


class ContactsBase(GDataBase):
  """The Google Contacts intermediate class for Contacts namespace."""

  _namespace = CONTACTS_NAMESPACE


class OrgName(GDataBase):
  """The Google Contacts OrgName element."""

  _tag = 'orgName'


class OrgTitle(GDataBase):
  """The Google Contacts OrgTitle element."""

  _tag = 'orgTitle'


class OrgDepartment(GDataBase):
  """The Google Contacts OrgDepartment element."""

  _tag = 'orgDepartment'


class OrgJobDescription(GDataBase):
  """The Google Contacts OrgJobDescription element."""

  _tag = 'orgJobDescription'


class Where(GDataBase):
  """The Google Contacts Where element."""

  _tag = 'where'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['rel'] = 'rel'
  _attributes['label'] = 'label'
  _attributes['valueString'] = 'value_string'

  def __init__(self, value_string=None, rel=None, label=None,
               text=None, extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.rel = rel
    self.label = label
    self.value_string = value_string


class When(GDataBase):
  """The Google Contacts When element."""

  _tag = 'when'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['startTime'] = 'start_time'
  _attributes['endTime'] = 'end_time'
  _attributes['label'] = 'label'

  def __init__(self, start_time=None, end_time=None, label=None,
               text=None, extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.start_time = start_time
    self.end_time = end_time
    self.label = label


class Organization(GDataBase):
  """The Google Contacts Organization element."""

  _tag = 'organization'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['primary'] = 'primary'
  _children['{%s}orgName' % GDataBase._namespace] = (
      'org_name', OrgName)
  _children['{%s}orgTitle' % GDataBase._namespace] = (
      'org_title', OrgTitle)
  _children['{%s}orgDepartment' % GDataBase._namespace] = (
      'org_department', OrgDepartment)
  _children['{%s}orgJobDescription' % GDataBase._namespace] = (
      'org_job_description', OrgJobDescription)
  #_children['{%s}where' % GDataBase._namespace] = ('where', Where)

  def __init__(self, label=None, rel=None, primary='false', org_name=None,
               org_title=None, org_department=None, org_job_description=None,
               where=None, text=None,
               extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.label = label
    self.rel = rel or REL_OTHER
    self.primary = primary
    self.org_name = org_name
    self.org_title = org_title
    self.org_department = org_department
    self.org_job_description = org_job_description
    self.where = where


class PostalAddress(GDataBase):
  """The Google Contacts PostalAddress element."""

  _tag = 'postalAddress'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['rel'] = 'rel'
  _attributes['primary'] = 'primary'

  def __init__(self, primary=None, rel=None, text=None,
               extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.rel = rel or REL_OTHER
    self.primary = primary


class FormattedAddress(GDataBase):
  """The Google Contacts FormattedAddress element."""

  _tag = 'formattedAddress'


class StructuredPostalAddress(GDataBase):
  """The Google Contacts StructuredPostalAddress element."""

  _tag = 'structuredPostalAddress'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['rel'] = 'rel'
  _attributes['primary'] = 'primary'
  _children['{%s}formattedAddress' % GDataBase._namespace] = (
      'formatted_address', FormattedAddress)

  def __init__(self, rel=None, primary=None,
               formatted_address=None, text=None,
               extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.rel = rel or REL_OTHER
    self.primary = primary
    self.formatted_address = formatted_address


class IM(GDataBase):
  """The Google Contacts IM element."""

  _tag = 'im'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['address'] = 'address'
  _attributes['primary'] = 'primary'
  _attributes['protocol'] = 'protocol'
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'

  def __init__(self, primary='false', rel=None, address=None, protocol=None,
               label=None, text=None,
               extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.protocol = protocol
    self.address = address
    self.primary = primary
    self.rel = rel or REL_OTHER
    self.label = label


class Email(GDataBase):
  """The Google Contacts Email element."""

  _tag = 'email'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['address'] = 'address'
  _attributes['primary'] = 'primary'
  _attributes['rel'] = 'rel'
  _attributes['label'] = 'label'

  def __init__(self, label=None, rel=None, address=None, primary='false',
               text=None, extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.label = label
    self.rel = rel or REL_OTHER
    self.address = address
    self.primary = primary


class PhoneNumber(GDataBase):
  """The Google Contacts PhoneNumber element."""

  _tag = 'phoneNumber'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['uri'] = 'uri'
  _attributes['primary'] = 'primary'

  def __init__(self, label=None, rel=None, uri=None, primary='false',
               text=None, extension_elements=None, extension_attributes=None):
    GDataBase.__init__(self, text=text, extension_elements=extension_elements,
                       extension_attributes=extension_attributes)
    self.label = label
    self.rel = rel or REL_OTHER
    self.uri = uri
    self.primary = primary


class Nickname(ContactsBase):
  """The Google Contacts Nickname element."""

  _tag = 'nickname'


class Occupation(ContactsBase):
  """The Google Contacts Occupation element."""

  _tag = 'occupation'


class Gender(ContactsBase):
  """The Google Contacts Gender element."""

  _tag = 'gender'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.value = value


class Birthday(ContactsBase):
  """The Google Contacts Birthday element."""

  _tag = 'birthday'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['when'] = 'when'

  def __init__(self, when=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.when = when


class Relation(ContactsBase):
  """The Google Contacts Relation element."""

  _tag = 'relation'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'

  def __init__(self, label=None, rel=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.label = label
    self.rel = rel


def RelationFromString(xml_string):
  return atom.CreateClassFromXMLString(Relation, xml_string)


class UserDefinedField(ContactsBase):
  """The Google Contacts UserDefinedField element."""

  _tag = 'userDefinedField'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['key'] = 'key'
  _attributes['value'] = 'value'

  def __init__(self, key=None, value=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.key = key
    self.value = value


def UserDefinedFieldFromString(xml_string):
  return atom.CreateClassFromXMLString(UserDefinedField, xml_string)


class Website(ContactsBase):
  """The Google Contacts Website element."""

  _tag = 'website'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['href'] = 'href'
  _attributes['label'] = 'label'
  _attributes['primary'] = 'primary'
  _attributes['rel'] = 'rel'

  def __init__(self, href=None, label=None, primary='false', rel=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.href = href
    self.label = label
    self.primary = primary
    self.rel = rel


def WebsiteFromString(xml_string):
  return atom.CreateClassFromXMLString(Website, xml_string)


class ExternalId(ContactsBase):
  """The Google Contacts ExternalId element."""

  _tag = 'externalId'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['value'] = 'value'

  def __init__(self, label=None, rel=None, value=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.label = label
    self.rel = rel
    self.value = value


def ExternalIdFromString(xml_string):
  return atom.CreateClassFromXMLString(ExternalId, xml_string)


class Event(ContactsBase):
  """The Google Contacts Event element."""

  _tag = 'event'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _children['{%s}when' % ContactsBase._namespace] = ('when', When)

  def __init__(self, label=None, rel=None, when=None,
               text=None, extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.label = label
    self.rel = rel
    self.when = when


def EventFromString(xml_string):
  return atom.CreateClassFromXMLString(Event, xml_string)


class Deleted(GDataBase):
  """The Google Contacts Deleted element."""

  _tag = 'deleted'


class GroupMembershipInfo(ContactsBase):
  """The Google Contacts GroupMembershipInfo element."""

  _tag = 'groupMembershipInfo'

  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['deleted'] = 'deleted'
  _attributes['href'] = 'href'

  def __init__(self, deleted=None, href=None, text=None,
               extension_elements=None, extension_attributes=None):
    ContactsBase.__init__(self, text=text,
                          extension_elements=extension_elements,
                          extension_attributes=extension_attributes)
    self.deleted = deleted
    self.href = href


class PersonEntry(gdata.BatchEntry):
  """Base class for ContactEntry and ProfileEntry."""

  _children = gdata.BatchEntry._children.copy()
  _children['{%s}organization' % gdata.GDATA_NAMESPACE] = (
      'organization', [Organization])
  _children['{%s}phoneNumber' % gdata.GDATA_NAMESPACE] = (
      'phone_number', [PhoneNumber])
  _children['{%s}nickname' % CONTACTS_NAMESPACE] = ('nickname', Nickname)
  _children['{%s}occupation' % CONTACTS_NAMESPACE] = ('occupation', Occupation)
  _children['{%s}gender' % CONTACTS_NAMESPACE] = ('gender', Gender)
  _children['{%s}birthday' % CONTACTS_NAMESPACE] = ('birthday', Birthday)
  _children['{%s}postalAddress' % gdata.GDATA_NAMESPACE] = ('postal_address',
                                                            [PostalAddress])
  _children['{%s}structuredPostalAddress' % gdata.GDATA_NAMESPACE] = (
      'structured_postal_address', [StructuredPostalAddress])
  _children['{%s}email' % gdata.GDATA_NAMESPACE] = ('email', [Email])
  _children['{%s}im' % gdata.GDATA_NAMESPACE] = ('im', [IM])
  _children['{%s}relation' % CONTACTS_NAMESPACE] = ('relation', [Relation])
  _children['{%s}userDefinedField' % CONTACTS_NAMESPACE] = (
      'user_defined_field', [UserDefinedField])
  _children['{%s}website' % CONTACTS_NAMESPACE] = ('website', [Website])
  _children['{%s}externalId' % CONTACTS_NAMESPACE] = (
      'external_id', [ExternalId])
  _children['{%s}event' % CONTACTS_NAMESPACE] = ('event', [Event])
  # The following line should be removed once the Python support
  # for GData 2.0 is mature.
  _attributes = gdata.BatchEntry._attributes.copy()
  _attributes['{%s}etag' % gdata.GDATA_NAMESPACE] = 'etag'

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None, organization=None, phone_number=None,
               nickname=None, occupation=None, gender=None, birthday=None,
               postal_address=None, structured_postal_address=None, email=None,
               im=None, relation=None, user_defined_field=None, website=None,
               external_id=None, event=None, batch_operation=None,
               batch_id=None, batch_status=None, text=None,
               extension_elements=None, extension_attributes=None, etag=None):
    gdata.BatchEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id, link=link,
                              published=published,
                              batch_operation=batch_operation,
                              batch_id=batch_id, batch_status=batch_status,
                              title=title, updated=updated)
    self.organization = organization or []
    self.phone_number = phone_number or []
    self.nickname = nickname
    self.occupation = occupation
    self.gender = gender
    self.birthday = birthday
    self.postal_address = postal_address or []
    self.structured_postal_address = structured_postal_address or []
    self.email = email or []
    self.im = im or []
    self.relation = relation or []
    self.user_defined_field = user_defined_field or []
    self.website = website or []
    self.external_id = external_id or []
    self.event = event or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    # The following line should be removed once the Python support
    # for GData 2.0 is mature.
    self.etag = etag


class ContactEntry(PersonEntry):
  """A Google Contact flavor of an Atom Entry."""

  _children = PersonEntry._children.copy()

  _children['{%s}deleted' % gdata.GDATA_NAMESPACE] = ('deleted', Deleted)
  _children['{%s}groupMembershipInfo' % CONTACTS_NAMESPACE] = (
      'group_membership_info', [GroupMembershipInfo])
  _children['{%s}extendedProperty' % gdata.GDATA_NAMESPACE] = (
      'extended_property', [gdata.ExtendedProperty])
  # Overwrite the organization rule in PersonEntry so that a ContactEntry
  # may only contain one <gd:organization> element.
  _children['{%s}organization' % gdata.GDATA_NAMESPACE] = (
      'organization', Organization)

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None, organization=None, phone_number=None,
               nickname=None, occupation=None, gender=None, birthday=None,
               postal_address=None, structured_postal_address=None, email=None,
               im=None, relation=None, user_defined_field=None, website=None,
               external_id=None, event=None, batch_operation=None,
               batch_id=None, batch_status=None, text=None,
               extension_elements=None, extension_attributes=None, etag=None,
               deleted=None, extended_property=None,
               group_membership_info=None):
    PersonEntry.__init__(self, author=author, category=category,
                         content=content, atom_id=atom_id, link=link,
                         published=published, title=title, updated=updated,
                         organization=organization, phone_number=phone_number,
                         nickname=nickname, occupation=occupation,
                         gender=gender, birthday=birthday,
                         postal_address=postal_address,
                         structured_postal_address=structured_postal_address,
                         email=email, im=im, relation=relation,
                         user_defined_field=user_defined_field,
                         website=website, external_id=external_id, event=event,
                         batch_operation=batch_operation, batch_id=batch_id,
                         batch_status=batch_status, text=text,
                         extension_elements=extension_elements,
                         extension_attributes=extension_attributes, etag=etag)
    self.deleted = deleted
    self.extended_property = extended_property or []
    self.group_membership_info = group_membership_info or []

  def GetPhotoLink(self):
    for a_link in self.link:
      if a_link.rel == PHOTO_LINK_REL:
        return a_link
    return None

  def GetPhotoEditLink(self):
    for a_link in self.link:
      if a_link.rel == PHOTO_EDIT_LINK_REL:
        return a_link
    return None


def ContactEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(ContactEntry, xml_string)


class ContactsFeed(gdata.BatchFeed, gdata.LinkFinder):
  """A Google Contacts feed flavor of an Atom Feed."""

  _children = gdata.BatchFeed._children.copy()

  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [ContactEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None,
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.BatchFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon, atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)


def ContactsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(ContactsFeed, xml_string)


class GroupEntry(gdata.BatchEntry):
  """Represents a contact group."""
  _children = gdata.BatchEntry._children.copy()
  _children['{%s}extendedProperty' % gdata.GDATA_NAMESPACE] = (
      'extended_property', [gdata.ExtendedProperty])

  def __init__(self, author=None, category=None, content=None,
               contributor=None, atom_id=None, link=None, published=None,
               rights=None, source=None, summary=None, control=None,
               title=None, updated=None,
               extended_property=None, batch_operation=None, batch_id=None,
               batch_status=None,
               extension_elements=None, extension_attributes=None, text=None):
    gdata.BatchEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              batch_operation=batch_operation,
                              batch_id=batch_id, batch_status=batch_status,
                              title=title, updated=updated)
    self.extended_property = extended_property or []


def GroupEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(GroupEntry, xml_string)


class GroupsFeed(gdata.BatchFeed):
  """A Google contact groups feed flavor of an Atom Feed."""
  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [GroupEntry])


def GroupsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GroupsFeed, xml_string)


class ProfileEntry(PersonEntry):
  """A Google Profiles flavor of an Atom Entry."""


def ProfileEntryFromString(xml_string):
  """Converts an XML string into a ProfileEntry object.

  Args:
    xml_string: string The XML describing a Profile entry.

  Returns:
    A ProfileEntry object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(ProfileEntry, xml_string)


class ProfilesFeed(gdata.BatchFeed, gdata.LinkFinder):
  """A Google Profiles feed flavor of an Atom Feed."""

  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [ProfileEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None,
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.BatchFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon, atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)


def ProfilesFeedFromString(xml_string):
  """Converts an XML string into a ProfilesFeed object.

  Args:
    xml_string: string The XML describing a Profiles feed.

  Returns:
    A ProfilesFeed object corresponding to the given XML.
  """
  return atom.CreateClassFromXMLString(ProfilesFeed, xml_string)
