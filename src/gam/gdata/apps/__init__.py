#!/usr/bin/python
#
# Copyright (C) 2007 SIOS Technology, Inc.
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

__author__ = 'tmatsuo@sios.com (Takashi MATSUO)'


import atom
import gdata


# XML namespaces which are often used in Google Apps entity.
APPS_NAMESPACE = 'http://schemas.google.com/apps/2006'
APPS_TEMPLATE = '{http://schemas.google.com/apps/2006}%s'


class EmailList(atom.AtomBase):
  """The Google Apps EmailList element"""
  
  _tag = 'emailList'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['name'] = 'name'

  def __init__(self, name=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.name = name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

def EmailListFromString(xml_string):
  return atom.CreateClassFromXMLString(EmailList, xml_string)
  

class Who(atom.AtomBase):
  """The Google Apps Who element"""
  
  _tag = 'who'
  _namespace = gdata.GDATA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['rel'] = 'rel'
  _attributes['email'] = 'email'

  def __init__(self, rel=None, email=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.rel = rel
    self.email = email
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

def WhoFromString(xml_string):
  return atom.CreateClassFromXMLString(Who, xml_string)
  

class Login(atom.AtomBase):
  """The Google Apps Login element"""
  
  _tag = 'login'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['userName'] = 'user_name'
  _attributes['password'] = 'password'
  _attributes['suspended'] = 'suspended'
  _attributes['admin'] = 'admin'
  _attributes['changePasswordAtNextLogin'] = 'change_password'
  _attributes['agreedToTerms'] = 'agreed_to_terms'
  _attributes['ipWhitelisted'] = 'ip_whitelisted'
  _attributes['hashFunctionName'] = 'hash_function_name'

  def __init__(self, user_name=None, password=None, suspended=None,
               ip_whitelisted=None, hash_function_name=None, 
               admin=None, change_password=None, agreed_to_terms=None, 
               extension_elements=None, extension_attributes=None, 
               text=None):
    self.user_name = user_name
    self.password = password
    self.suspended = suspended
    self.admin = admin
    self.change_password = change_password
    self.agreed_to_terms = agreed_to_terms
    self.ip_whitelisted = ip_whitelisted
    self.hash_function_name = hash_function_name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

    
def LoginFromString(xml_string):
    return atom.CreateClassFromXMLString(Login, xml_string)
    

class Quota(atom.AtomBase):
  """The Google Apps Quota element"""
  
  _tag = 'quota'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['limit'] = 'limit'

  def __init__(self, limit=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.limit = limit
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}

    
def QuotaFromString(xml_string):
    return atom.CreateClassFromXMLString(Quota, xml_string)

    
class Name(atom.AtomBase):
  """The Google Apps Name element"""

  _tag = 'name'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()  
  _attributes['familyName'] = 'family_name'
  _attributes['givenName'] = 'given_name'
  
  def __init__(self, family_name=None, given_name=None,
               extension_elements=None, extension_attributes=None, text=None):
    self.family_name = family_name
    self.given_name = given_name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def NameFromString(xml_string):
    return atom.CreateClassFromXMLString(Name, xml_string)


class Nickname(atom.AtomBase):
  """The Google Apps Nickname element"""
  
  _tag = 'nickname'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy() 
  _attributes['name'] = 'name'

  def __init__(self, name=None,
               extension_elements=None, extension_attributes=None, text=None):
    self.name = name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def NicknameFromString(xml_string):
    return atom.CreateClassFromXMLString(Nickname, xml_string)
  

class NicknameEntry(gdata.GDataEntry):
  """A Google Apps flavor of an Atom Entry for Nickname"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}login' % APPS_NAMESPACE] = ('login', Login)
  _children['{%s}nickname' % APPS_NAMESPACE] = ('nickname', Nickname)

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, 
               title=None, updated=None,
               login=None, nickname=None,
               extended_property=None, 
               extension_elements=None, extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category, 
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated)
    self.login = login
    self.nickname = nickname
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def NicknameEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(NicknameEntry, xml_string)


class NicknameFeed(gdata.GDataFeed, gdata.LinkFinder):
  """A Google Apps Nickname feed flavor of an Atom Feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [NicknameEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None, 
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.GDataFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)


def NicknameFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(NicknameFeed, xml_string)


class UserEntry(gdata.GDataEntry):
  """A Google Apps flavor of an Atom Entry"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}login' % APPS_NAMESPACE] = ('login', Login)
  _children['{%s}name' % APPS_NAMESPACE] = ('name', Name)
  _children['{%s}quota' % APPS_NAMESPACE] = ('quota', Quota)
  # This child may already be defined in GDataEntry, confirm before removing.
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link', 
                                                       [gdata.FeedLink])
  _children['{%s}who' % gdata.GDATA_NAMESPACE] = ('who', Who)

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, 
               title=None, updated=None,
               login=None, name=None, quota=None, who=None, feed_link=None,
               extended_property=None, 
               extension_elements=None, extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category, 
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated)
    self.login = login
    self.name = name
    self.quota = quota
    self.who = who
    self.feed_link = feed_link or []
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    

def UserEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(UserEntry, xml_string)

  
class UserFeed(gdata.GDataFeed, gdata.LinkFinder):
  """A Google Apps User feed flavor of an Atom Feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [UserEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None, 
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.GDataFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)


def UserFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(UserFeed, xml_string)


class EmailListEntry(gdata.GDataEntry):
  """A Google Apps EmailList flavor of an Atom Entry"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}emailList' % APPS_NAMESPACE] = ('email_list', EmailList)
  # Might be able to remove this _children entry.
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link', 
                                                       [gdata.FeedLink])

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, 
               title=None, updated=None,
               email_list=None, feed_link=None,
               extended_property=None, 
               extension_elements=None, extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category, 
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated)
    self.email_list = email_list
    self.feed_link = feed_link or []
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def EmailListEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(EmailListEntry, xml_string)
  

class EmailListFeed(gdata.GDataFeed, gdata.LinkFinder):
  """A Google Apps EmailList feed flavor of an Atom Feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [EmailListEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None, 
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.GDataFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)
                             

def EmailListFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(EmailListFeed, xml_string)


class EmailListRecipientEntry(gdata.GDataEntry):
  """A Google Apps EmailListRecipient flavor of an Atom Entry"""
  
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}who' % gdata.GDATA_NAMESPACE] = ('who', Who)

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, 
               title=None, updated=None,
               who=None,
               extended_property=None, 
               extension_elements=None, extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category, 
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated)
    self.who = who
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def EmailListRecipientEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(EmailListRecipientEntry, xml_string)


class EmailListRecipientFeed(gdata.GDataFeed, gdata.LinkFinder):
  """A Google Apps EmailListRecipient feed flavor of an Atom Feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', 
                                                  [EmailListRecipientEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None, 
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.GDataFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)


def EmailListRecipientFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(EmailListRecipientFeed, xml_string)


class Property(atom.AtomBase):
  """The Google Apps Property element"""

  _tag = 'property'
  _namespace = APPS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['name'] = 'name'
  _attributes['value'] = 'value'

  def __init__(self, name=None, value=None, extension_elements=None,
               extension_attributes=None, text=None):
    self.name = name
    self.value = value
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def PropertyFromString(xml_string):
  return atom.CreateClassFromXMLString(Property, xml_string)


class PropertyEntry(gdata.GDataEntry):
  """A Google Apps Property flavor of an Atom Entry"""

  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}property' % APPS_NAMESPACE] = ('property', [Property])

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None,
               property=None,
               extended_property=None,
               extension_elements=None, extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated)
    self.property = property
    self.extended_property = extended_property or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def PropertyEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(PropertyEntry, xml_string)

class PropertyFeed(gdata.GDataFeed, gdata.LinkFinder):
  """A Google Apps Property feed flavor of an Atom Feed"""
  
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [PropertyEntry])

  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None, 
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.GDataFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)

def PropertyFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(PropertyFeed, xml_string)
