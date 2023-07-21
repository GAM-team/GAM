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

"""Data model classes for parsing and generating XML for the Contacts API."""

import atom
import gdata

## Constants from http://code.google.com/apis/gdata/elements.html ##
REL_HOME = 'http://schemas.google.com/g/2005#home'
REL_WORK = 'http://schemas.google.com/g/2005#work'
REL_OTHER = 'http://schemas.google.com/g/2005#other'

IM_AIM = 'http://schemas.google.com/g/2005#AIM'  # AOL Instant Messenger protocol
IM_MSN = 'http://schemas.google.com/g/2005#MSN'  # MSN Messenger protocol
IM_YAHOO = 'http://schemas.google.com/g/2005#YAHOO'  # Yahoo Messenger protocol
IM_SKYPE = 'http://schemas.google.com/g/2005#SKYPE'  # Skype protocol
IM_QQ = 'http://schemas.google.com/g/2005#QQ'  # QQ protocol
IM_GOOGLE_TALK = 'http://schemas.google.com/g/2005#GOOGLE_TALK'  # Google Talk protocol
IM_ICQ = 'http://schemas.google.com/g/2005#ICQ'  # ICQ protocol
IM_JABBER = 'http://schemas.google.com/g/2005#JABBER'  # Jabber protocol
IM_NETMEETING = 'http://schemas.google.com/g/2005#NETMEETING'  # NetMeeting

PHOTO_LINK_REL = 'http://schemas.google.com/contacts/2008/rel#photo'
PHOTO_EDIT_LINK_REL = 'http://schemas.google.com/contacts/2008/rel#edit-photo'

# Different phone types, for more info see:
# http://code.google.com/apis/gdata/docs/2.0/elements.html#gdPhoneNumber
PHONE_ASSISTANT = 'http://schemas.google.com/g/2005#assistant'
PHONE_CALLBACK = 'http://schemas.google.com/g/2005#callback'
PHONE_CAR = 'http://schemas.google.com/g/2005#car'
PHONE_COMPANY_MAIN = 'http://schemas.google.com/g/2005#company_main'
PHONE_FAX = 'http://schemas.google.com/g/2005#fax'
PHONE_GENERAL = 'http://schemas.google.com/g/2005#general'
PHONE_HOME = REL_HOME
PHONE_HOME_FAX = 'http://schemas.google.com/g/2005#home_fax'
PHONE_INTERNAL = 'http://schemas.google.com/g/2005#internal-extension'
PHONE_ISDN = 'http://schemas.google.com/g/2005#isdn'
PHONE_MAIN = 'http://schemas.google.com/g/2005#main'
PHONE_MOBILE = 'http://schemas.google.com/g/2005#mobile'
PHONE_OTHER = REL_OTHER
PHONE_OTHER_FAX = 'http://schemas.google.com/g/2005#other_fax'
PHONE_PAGER = 'http://schemas.google.com/g/2005#pager'
PHONE_RADIO = 'http://schemas.google.com/g/2005#radio'
PHONE_SATELLITE = 'http://schemas.google.com/g/2005#satellite'
PHONE_TELEX = 'http://schemas.google.com/g/2005#telex'
PHONE_TTY_TDD = 'http://schemas.google.com/g/2005#tty_tdd'
PHONE_VOIP = 'http://schemas.google.com/g/2005#voip'
PHONE_WORK = REL_WORK
PHONE_WORK_FAX = 'http://schemas.google.com/g/2005#work_fax'
PHONE_WORK_MOBILE = 'http://schemas.google.com/g/2005#work_mobile'
PHONE_WORK_PAGER = 'http://schemas.google.com/g/2005#work_pager'

MAIL_BOTH = 'http://schemas.google.com/g/2005#both'
MAIL_LETTERS = 'http://schemas.google.com/g/2005#letters'
MAIL_PARCELS = 'http://schemas.google.com/g/2005#parcels'
MAIL_NEITHER = 'http://schemas.google.com/g/2005#neither'

GENERAL_ADDRESS = 'http://schemas.google.com/g/2005#general'
LOCAL_ADDRESS = 'http://schemas.google.com/g/2005#local'

EXTERNAL_ID_ORGANIZATION = 'organization'

RELATION_MANAGER = 'manager'

CONTACTS_NAMESPACE = 'http://schemas.google.com/contact/2008'


class GDataBase(atom.AtomBase):
  """The Google Contacts intermediate class from atom.AtomBase."""
  _namespace = gdata.GDATA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, text=None):
    atom.AtomBase.__init__(self, text=text)

class ContactsBase(GDataBase):
  """The Google Contacts intermediate class for Contacts namespace."""
  _namespace = CONTACTS_NAMESPACE

class BillingInformation(ContactsBase):
  """The gContact:billingInformation element."""
  _tag = 'billingInformation'

class Birthday(ContactsBase):
  """The gContact:birthday element."""
  _tag = 'birthday'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['when'] = 'when'

  def __init__(self, when=None):
    ContactsBase.__init__(self)
    self.when = when

class CalendarLink(ContactsBase):
  """The gContact:calendarLink element."""
  _tag = 'calendarLink'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['href'] = 'href'
  _attributes['label'] = 'label'
  _attributes['primary'] = 'primary'
  _attributes['rel'] = 'rel'

  def __init__(self, href=None, label=None, primary='false', rel=None):
    ContactsBase.__init__(self)
    self.href = href
    self.label = label
    self.primary = primary
    self.rel = rel

class Content(atom.AtomBase):
  """The Google Contacts Content element."""
  _tag = 'content'
  _namespace = atom.ATOM_NAMESPACE

  def __init__(self, text=None):
    atom.AtomBase.__init__(self, text=text)

class DirectoryServer(ContactsBase):
  """The gContact:directoryServer element."""
  _tag = 'directoryServer'

class Email(GDataBase):
  """The gd:email element."""
  _tag = 'email'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['address'] = 'address'
  _attributes['primary'] = 'primary'
  _attributes['rel'] = 'rel'
  _attributes['label'] = 'label'

  def __init__(self, label=None, rel=None, address=None, primary='false'):
    GDataBase.__init__(self)
    self.label = label
    self.rel = rel
    self.address = address
    self.primary = primary

class When(GDataBase):
  """The Google Contacts when element."""
  _tag = 'when'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['startTime'] = 'startTime'
  _attributes['label'] = 'label'

  def __init__(self, startTime=None, label=None):
    GDataBase.__init__(self)
    self.startTime = startTime
    self.label = label

class Event(ContactsBase):
  """The gContact:event element."""
  _tag = 'event'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _children['{%s}when' % GDataBase._namespace] = ('when', When)

  def __init__(self, label=None, rel=None, when=None):
    ContactsBase.__init__(self)
    self.label = label
    self.rel = rel
    self.when = when

def EventFromString(xml_string):
  return atom.CreateClassFromXMLString(Event, xml_string)

class ExternalId(ContactsBase):
  """The gContact:externalId element."""
  _tag = 'externalId'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['value'] = 'value'

  def __init__(self, label=None, rel=None, value=None):
    ContactsBase.__init__(self)
    self.label = label
    self.rel = rel
    self.value = value

def ExternalIdFromString(xml_string):
  return atom.CreateClassFromXMLString(ExternalId, xml_string)

class Gender(ContactsBase):
  """The gContact:gender element."""
  _tag = 'gender'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['value'] = 'value'

  def __init__(self, value=None):
    ContactsBase.__init__(self)
    self.value = value

class Hobby(ContactsBase):
  """The gContact:hobby element."""
  _tag = 'hobby'

class IM(GDataBase):
  """The gd:im element."""
  _tag = 'im'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['address'] = 'address'
  _attributes['primary'] = 'primary'
  _attributes['protocol'] = 'protocol'
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'

  def __init__(self, primary='false', rel=None, address=None, protocol=None, label=None):
    GDataBase.__init__(self)
    self.protocol = protocol
    self.address = address
    self.primary = primary
    self.rel = rel
    self.label = label

class Initials(ContactsBase):
  """The gContact:initials element."""
  _tag = 'initials'

class Jot(ContactsBase):
  """The gContact:jot element."""
  _tag = 'jot'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['rel'] = 'rel'

  def __init__(self, rel=None, text=None):
    ContactsBase.__init__(self, text=text)
    self.rel = rel

class Language(ContactsBase):
  """The gContact:language element."""
  _tag = 'language'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['code'] = 'code'
  _attributes['label'] = 'label'

  def __init__(self, code=None, label=None):
    ContactsBase.__init__(self)
    self.code = code
    self.label = label

class MaidenName(ContactsBase):
  """The gContact:maidenName element."""
  _tag = 'maidenName'

class Mileage(ContactsBase):
  """The gContact:mileage element."""
  _tag = 'mileage'

class NamePrefix(GDataBase):
  """The gd:namePrefix element."""
  _tag = 'namePrefix'

class GivenName(GDataBase):
  """The gd:givenName element."""
  _tag = 'givenName'

class AdditionalName(GDataBase):
  """The gd:additionalName element."""
  _tag = 'additionalName'

class FamilyName(GDataBase):
  """The gd:familyName element."""
  _tag = 'familyName'

class NameSuffix(GDataBase):
  """The gd:nameSuffix element."""
  _tag = 'nameSuffix'

class FullName(GDataBase):
  """The gd:fullName element."""
  _tag = 'fullName'

class Name(GDataBase):
  """The gd:name element."""
  _tag = 'name'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _children['{%s}namePrefix' % GDataBase._namespace] = ('name_prefix', NamePrefix)
  _children['{%s}givenName' % GDataBase._namespace] = ('given_name', GivenName)
  _children['{%s}additionalName' % GDataBase._namespace] = ('additional_name', AdditionalName)
  _children['{%s}familyName' % GDataBase._namespace] = ('family_name', FamilyName)
  _children['{%s}nameSuffix' % GDataBase._namespace] = ('name_suffix', NameSuffix)
  _children['{%s}fullName' % GDataBase._namespace] = ('full_name', FullName)

  def __init__(self, given_name=None, additional_name=None, family_name=None,
               name_prefix=None, name_suffix=None, full_name=None,):
    GDataBase.__init__(self)
    self.given_name = given_name
    self.additional_name = additional_name
    self.family_name = family_name
    self.name_prefix = name_prefix
    self.name_suffix = name_suffix
    self.full_name = full_name

class Nickname(ContactsBase):
  """The gContact:nickname element."""
  _tag = 'nickname'

class Occupation(ContactsBase):
  """The gContact:occupation element."""
  _tag = 'occupation'

class PhoneNumber(GDataBase):
  """The gd:phoneNumber element."""
  _tag = 'phoneNumber'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['uri'] = 'uri'
  _attributes['primary'] = 'primary'

  def __init__(self, label=None, rel=None, uri=None, primary='false', text=None):
    GDataBase.__init__(self, text=text)
    self.label = label
    self.rel = rel
    self.uri = uri
    self.primary = primary

class OrgName(GDataBase):
  """The gd:orgName element."""
  _tag = 'orgName'

class OrgTitle(GDataBase):
  """The gd:orgTitle element."""
  _tag = 'orgTitle'

class OrgSymbol(GDataBase):
  """The gd:orgSymbol element."""
  _tag = 'orgSymbol'

class OrgDepartment(GDataBase):
  """The gd:orgDepartment element."""
  _tag = 'orgDepartment'

class OrgJobDescription(GDataBase):
  """The gd:orgJobDescription element."""
  _tag = 'orgJobDescription'

class Where(GDataBase):
  """The gd:where element."""
  _tag = 'where'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['valueString'] = 'value_string'

  def __init__(self, value_string=None):
    GDataBase.__init__(self)
    self.value_string = value_string

class Organization(GDataBase):
  """The gd:organization element."""
  _tag = 'organization'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['primary'] = 'primary'
  _children['{%s}orgName' % GDataBase._namespace] = ('name', OrgName)
  _children['{%s}orgSymbol' % GDataBase._namespace] = ('symbol', OrgSymbol)
  _children['{%s}orgTitle' % GDataBase._namespace] = ('title', OrgTitle)
  _children['{%s}orgDepartment' % GDataBase._namespace] = ('department', OrgDepartment)
  _children['{%s}orgJobDescription' % GDataBase._namespace] = ('job_description', OrgJobDescription)
  _children['{%s}where' % GDataBase._namespace] = ('where', Where)

  def __init__(self, label=None, rel=None, primary='false', name=None,
               title=None, symbol=None, department=None, job_description=None, where=None,):
    GDataBase.__init__(self)
    self.label = label
    self.rel = rel
    self.primary = primary
    self.name = name
    self.symbol = symbol
    self.title = title
    self.department = department
    self.job_description = job_description
    self.where = where

class PostalAddress(GDataBase):
  """The gd:postalAddress element."""
  _tag = 'postalAddress'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['primary'] = 'primary'

  def __init__(self, primary=None, rel=None, label=None, text=None):
    GDataBase.__init__(self, text=text)
    self.label = label
    self.rel = rel
    self.primary = primary

class Priority(ContactsBase):
  """The gContact:priority element."""
  _tag = 'priority'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['rel'] = 'rel'

  def __init__(self, rel=None):
    ContactsBase.__init__(self)
    self.rel = rel

class Relation(ContactsBase):
  """The gContact:relation element."""
  _tag = 'relation'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'

  def __init__(self, label=None, rel=None, text=None):
    ContactsBase.__init__(self, text=text)
    self.label = label
    self.rel = rel

def RelationFromString(xml_string):
  return atom.CreateClassFromXMLString(Relation, xml_string)

class Sensitivity(ContactsBase):
  """The gContact:sensitivity element."""
  _tag = 'sensitivity'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['rel'] = 'rel'

  def __init__(self, rel=None):
    ContactsBase.__init__(self)
    self.rel = rel

class ShortName(ContactsBase):
  """The gContact:shortName element."""
  _tag = 'shortName'

class Street(GDataBase):
  """The gd:street element.
  Can be street, avenue, road, etc. This element also includes the
  house number and room/apartment/flat/floor number.
  """
  _tag = 'street'

class PoBox(GDataBase):
  """The gd:pobox element.
  Covers actual P.O. boxes, drawers, locked bags, etc. This is usually
  but not always mutually exclusive with street.
  """
  _tag = 'pobox'

class Neighborhood(GDataBase):
  """The gd:neighborhood element.
  This is used to disambiguate a street address when a city contains more
  than one street with the same name, or to specify a small place whose
  mail is routed through a larger postal town. In China it could be a
  county or a minor city.
  """
  _tag = 'neighborhood'

class City(GDataBase):
  """The gd:city element.
  Can be city, village, town, borough, etc. This is the postal town and
  not necessarily the place of residence or place of business.
  """
  _tag = 'city'

class Region(GDataBase):
  """The gd:region element.
  A state, province, county (in Ireland), Land (in Germany),
  departement (in France), etc.
  """
  _tag = 'region'

class Postcode(GDataBase):
  """The gd:postcode element.
  Postal code. Usually country-wide, but sometimes specific to the
  city (e.g. "2" in "Dublin 2, Ireland" addresses).
  """
  _tag = 'postcode'

class Country(GDataBase):
  """The gd:country element.
  The name or code of the country.
  """
  _tag = 'country'

class FormattedAddress(GDataBase):
  """The gd:formattedAddress element."""
  _tag = 'formattedAddress'

class StructuredPostalAddress(GDataBase):
  """The gd:structuredPostalAddress element."""
  _tag = 'structuredPostalAddress'
  _children = GDataBase._children.copy()
  _attributes = GDataBase._attributes.copy()
  _attributes['label'] = 'label'
  _attributes['rel'] = 'rel'
  _attributes['primary'] = 'primary'
  _children['{%s}street' % GDataBase._namespace] = ('street', Street)
  _children['{%s}pobox' % GDataBase._namespace] = ('pobox', PoBox)
  _children['{%s}neighborhood' % GDataBase._namespace] = ('neighborhood', Neighborhood)
  _children['{%s}city' % GDataBase._namespace] = ('city', City)
  _children['{%s}region' % GDataBase._namespace] = ('region', Region)
  _children['{%s}postcode' % GDataBase._namespace] = ('postcode', Postcode)
  _children['{%s}country' % GDataBase._namespace] = ('country', Country)
  _children['{%s}formattedAddress' % GDataBase._namespace] = ('formatted_address', FormattedAddress)

  def __init__(self, rel=None, label=None, primary='false',
               street=None,
               pobox=None,
               neighborhood=None,
               city=None,
               region=None,
               postcode=None,
               country=None,
               formatted_address=None):
    GDataBase.__init__(self)
    self.label = label
    self.rel = rel
    self.primary = primary
    self.street = street
    self.pobox = pobox
    self.neighborhood = neighborhood
    self.city = city
    self.region = region
    self.postcode = postcode
    self.country = country
    self.formatted_address = formatted_address

class Subject(ContactsBase):
  """The gContact:Subject element."""
  _tag = 'subject'

class UserDefinedField(ContactsBase):
  """The gContact:userDefinedField element."""
  _tag = 'userDefinedField'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['key'] = 'key'
  _attributes['value'] = 'value'

  def __init__(self, key=None, value=None):
    ContactsBase.__init__(self)
    self.key = key
    self.value = value

def UserDefinedFieldFromString(xml_string):
  return atom.CreateClassFromXMLString(UserDefinedField, xml_string)

class Website(ContactsBase):
  """The gContact:Website element."""
  _tag = 'website'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['href'] = 'href'
  _attributes['label'] = 'label'
  _attributes['primary'] = 'primary'
  _attributes['rel'] = 'rel'

  def __init__(self, href=None, label=None, primary='false', rel=None):
    ContactsBase.__init__(self)
    self.href = href
    self.label = label
    self.primary = primary
    self.rel = rel

def WebsiteFromString(xml_string):
  return atom.CreateClassFromXMLString(Website, xml_string)

class PersonEntry(gdata.BatchEntry):
  """Base class for ContactEntry and ProfileEntry."""
  _children = gdata.BatchEntry._children.copy()
  _children['{%s}billingInformation' % CONTACTS_NAMESPACE] = ('billingInformation', BillingInformation)
  _children['{%s}birthday' % CONTACTS_NAMESPACE] = ('birthday', Birthday)
  _children['{%s}calendarLink' % CONTACTS_NAMESPACE] = ('calendarLink', [CalendarLink])
  _children['{%s}content' % atom.ATOM_NAMESPACE] = ('content', Content)
  _children['{%s}directoryServer' % CONTACTS_NAMESPACE] = ('directoryServer', DirectoryServer)
  _children['{%s}email' % gdata.GDATA_NAMESPACE] = ('email', [Email])
  _children['{%s}event' % CONTACTS_NAMESPACE] = ('event', [Event])
  _children['{%s}externalId' % CONTACTS_NAMESPACE] = ('externalId', [ExternalId])
  _children['{%s}gender' % CONTACTS_NAMESPACE] = ('gender', Gender)
  _children['{%s}hobby' % CONTACTS_NAMESPACE] = ('hobby', [Hobby])
  _children['{%s}im' % gdata.GDATA_NAMESPACE] = ('im', [IM])
  _children['{%s}initials' % CONTACTS_NAMESPACE] = ('initials', Initials)
  _children['{%s}jot' % CONTACTS_NAMESPACE] = ('jot', [Jot])
  _children['{%s}language' % CONTACTS_NAMESPACE] = ('language', Language)
  _children['{%s}maidenName' % CONTACTS_NAMESPACE] = ('maidenName', MaidenName)
  _children['{%s}mileage' % CONTACTS_NAMESPACE] = ('mileage', Mileage)
  _children['{%s}name' % gdata.GDATA_NAMESPACE] = ('name', Name)
  _children['{%s}nickname' % CONTACTS_NAMESPACE] = ('nickname', Nickname)
  _children['{%s}occupation' % CONTACTS_NAMESPACE] = ('occupation', Occupation)
  _children['{%s}organization' % gdata.GDATA_NAMESPACE] = ('organization', [Organization])
  _children['{%s}phoneNumber' % gdata.GDATA_NAMESPACE] = ('phoneNumber', [PhoneNumber])
  _children['{%s}postalAddress' % gdata.GDATA_NAMESPACE] = ('postalAddress', [PostalAddress])
  _children['{%s}priority' % CONTACTS_NAMESPACE] = ('priority', Priority)
  _children['{%s}relation' % CONTACTS_NAMESPACE] = ('relation', [Relation])
  _children['{%s}sensitivity' % CONTACTS_NAMESPACE] = ('sensitivity', Sensitivity)
  _children['{%s}shortName' % CONTACTS_NAMESPACE] = ('shortName', ShortName)
  _children['{%s}structuredPostalAddress' % gdata.GDATA_NAMESPACE] = ('structuredPostalAddress', [StructuredPostalAddress])
  _children['{%s}subject' % CONTACTS_NAMESPACE] = ('subject', Subject)
  _children['{%s}userDefinedField' % CONTACTS_NAMESPACE] = ('userDefinedField', [UserDefinedField])
  _children['{%s}website' % CONTACTS_NAMESPACE] = ('website', [Website])
  _children['{%s}where' % gdata.GDATA_NAMESPACE] = ('where', Where)

  _attributes = gdata.BatchEntry._attributes.copy()
  _attributes['{%s}etag' % gdata.GDATA_NAMESPACE] = 'etag'

  def __init__(self,
               billingInformation=None,
               birthday=None,
               calendarLink=None,
               content=None,
               directoryServer=None,
               email=None,
               event=None,
               externalId=None,
               gender=None,
               hobby=None,
               im=None,
               initials=None,
               jot=None,
               language=None,
               maidenName=None,
               mileage=None,
               name=None,
               nickname=None,
               occupation=None,
               organization=None,
               phoneNumber=None,
               postalAddress=None,
               priority=None,
               relation=None,
               sensitivity=None,
               shortName=None,
               structuredPostalAddress=None,
               subject=None,
               text=None,
               title=None,
               userDefinedField=None,
               website=None,
               where=None,
               etag=None):
    gdata.BatchEntry.__init__(self)
    self.billingInformation = billingInformation
    self.birthday = birthday
    self.calendarLink = calendarLink or []
    self.content = content
    self.directoryServer = directoryServer
    self.email = email or []
    self.event = event or []
    self.externalId = externalId or []
    self.gender = gender
    self.hobby = hobby or []
    self.im = im or []
    self.initials = initials
    self.jot = jot or []
    self.language = language
    self.maidenName = maidenName
    self.mileage = mileage
    self.name = name
    self.nickname = nickname
    self.occupation = occupation
    self.organization = organization or []
    self.phoneNumber = phoneNumber or []
    self.postalAddress = postalAddress or []
    self.priority = priority
    self.relation = relation or []
    self.sensitivity = sensitivity
    self.shortName = shortName
    self.structuredPostalAddress = structuredPostalAddress or []
    self.subject = subject
    self.text = text
    self.userDefinedField = userDefinedField or []
    self.website = website or []
    self.where = where
    self.extension_attributes = {}
    self.extension_elements = []
    self.etag = etag

class Deleted(GDataBase):
  """The gd:Deleted element."""
  _tag = 'deleted'

class GroupMembershipInfo(ContactsBase):
  """The Google Contacts GroupMembershipInfo element."""
  _tag = 'groupMembershipInfo'
  _children = ContactsBase._children.copy()
  _attributes = ContactsBase._attributes.copy()
  _attributes['deleted'] = 'deleted'
  _attributes['href'] = 'href'

  def __init__(self, deleted=None, href=None, text=None):
    ContactsBase.__init__(self, text=text)
    self.deleted = deleted
    self.href = href

class ContactEntry(PersonEntry):
  """Represents a contact."""
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = PersonEntry._children.copy()

  _children['{%s}deleted' % gdata.GDATA_NAMESPACE] = ('deleted', Deleted)
  _children['{%s}groupMembershipInfo' % CONTACTS_NAMESPACE] = ('groupMembershipInfo', [GroupMembershipInfo])
  _children['{%s}extendedProperty' % gdata.GDATA_NAMESPACE] = ('extended_property', [gdata.ExtendedProperty])
  # Overwrite the organization rule in PersonEntry so that a ContactEntry
  # may only contain one <gd:organization> element.
  #_children['{%s}organization' % gdata.GDATA_NAMESPACE] = ('organization', Organization)

  def __init__(self,
               billingInformation=None,
               birthday=None,
               calendarLink=None,
               content=None,
               deleted=None,
               directoryServer=None,
               email=None,
               event=None,
               extended_property=None,
               externalId=None,
               gender=None,
               groupMembershipInfo=None,
               hobby=None,
               im=None,
               initials=None,
               jot=None,
               language=None,
               maidenName=None,
               mileage=None,
               name=None,
               nickname=None,
               occupation=None,
               organization=None,
               phoneNumber=None,
               postalAddress=None,
               priority=None,
               relation=None,
               sensitivity=None,
               shortName=None,
               structuredPostalAddress=None,
               subject=None,
               text=None,
               title=None,
               userDefinedField=None,
               website=None,
               where=None,
               etag=None):
    PersonEntry.__init__(self,
                         billingInformation=billingInformation,
                         birthday=birthday,
                         calendarLink=calendarLink,
                         content=content,
                         directoryServer=directoryServer,
                         email=email,
                         event=event,
                         externalId=externalId,
                         gender=gender,
                         hobby=hobby,
                         im=im,
                         initials=initials,
                         jot=jot,
                         language=language,
                         maidenName=maidenName,
                         mileage=mileage,
                         name=name,
                         nickname=nickname,
                         occupation=occupation,
                         organization=organization,
                         phoneNumber=phoneNumber,
                         postalAddress=postalAddress,
                         priority=priority,
                         relation=relation,
                         sensitivity=sensitivity,
                         shortName=shortName,
                         structuredPostalAddress=structuredPostalAddress,
                         subject=subject,
                         text=text,
                         title=title,
                         userDefinedField=userDefinedField,
                         website=website,
                         where=where,
                         etag=etag)
    self.deleted = deleted
    self.extended_property = extended_property or []
    self.groupMembershipInfo = groupMembershipInfo or []

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
  """A Google contacts feed flavor of an Atom Feed."""
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [ContactEntry])

  def __init__(self):
    gdata.BatchFeed.__init__(self)

def ContactsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(ContactsFeed, xml_string)

class GroupEntry(gdata.BatchEntry):
  """Represents a contact group."""
  _children = gdata.BatchEntry._children.copy()
  _children['{%s}deleted' % gdata.GDATA_NAMESPACE] = ('deleted', Deleted)
  _children['{%s}extendedProperty' % gdata.GDATA_NAMESPACE] = ('extended_property', [gdata.ExtendedProperty])

  _attributes = gdata.BatchEntry._attributes.copy()
  _attributes['{%s}etag' % gdata.GDATA_NAMESPACE] = 'etag'

  def __init__(self,
               title=None,
               deleted=None,
               extended_property=None,
               etag=None):
    gdata.BatchEntry.__init__(self)
    self.title = title
    self.deleted = deleted
    self.extended_property = extended_property or []
    self.etag = etag

def GroupEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(GroupEntry, xml_string)

class GroupsFeed(gdata.BatchFeed):
  """A Google contact groups feed flavor of an Atom Feed."""
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.BatchFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [GroupEntry])

  def __init__(self):
    gdata.BatchFeed.__init__(self)

def GroupsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(GroupsFeed, xml_string)
