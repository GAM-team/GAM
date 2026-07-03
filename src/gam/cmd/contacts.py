"""GAM domain contacts management."""

import re
import json
import sys

import gdata.apps.contacts

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _getMain():
  return sys.modules['gam']

from gamlib import glgdata as GDATA

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def _getCreateContactReturnOptions(parameters):
  myarg = _getMain().getArgument()
  if myarg == 'returnidonly':
    parameters['returnIdOnly'] = True
  elif myarg == 'csv':
    parameters['csvPF'] = CSVPrintFile(parameters['titles'], 'sortall')
  elif parameters['csvPF'] and myarg == 'todrive':
    parameters['csvPF'].GetTodriveParameters()
  elif parameters['csvPF'] and myarg == 'addcsvdata':
    _getMain().getAddCSVData(parameters['addCSVData'])
  else:
    return False
  return True
#
CONTACT_JSON = 'JSON'

CONTACT_ID = 'ContactID'
CONTACT_UPDATED = 'Updated'
CONTACT_NAME_PREFIX = 'Name Prefix'
CONTACT_GIVEN_NAME = 'Given Name'
CONTACT_ADDITIONAL_NAME = 'Additional Name'
CONTACT_FAMILY_NAME = 'Family Name'
CONTACT_NAME_SUFFIX = 'Name Suffix'
CONTACT_NAME = 'Name'
CONTACT_NICKNAME = 'Nickname'
CONTACT_MAIDENNAME = 'Maiden Name'
CONTACT_SHORTNAME = 'Short Name'
CONTACT_INITIALS = 'Initials'
CONTACT_BIRTHDAY = 'Birthday'
CONTACT_GENDER = 'Gender'
CONTACT_LOCATION = 'Location'
CONTACT_PRIORITY = 'Priority'
CONTACT_SENSITIVITY = 'Sensitivity'
CONTACT_SUBJECT = 'Subject'
CONTACT_LANGUAGE = 'Language'
CONTACT_NOTES = 'Notes'
CONTACT_OCCUPATION = 'Occupation'
CONTACT_BILLING_INFORMATION = 'Billing Information'
CONTACT_MILEAGE = 'Mileage'
CONTACT_DIRECTORY_SERVER = 'Directory Server'
CONTACT_ADDRESSES = 'Addresses'
CONTACT_CALENDARS = 'Calendars'
CONTACT_EMAILS = 'Emails'
CONTACT_EXTERNALIDS = 'External IDs'
CONTACT_EVENTS = 'Events'
CONTACT_HOBBIES = 'Hobbies'
CONTACT_IMS = 'IMs'
CONTACT_JOTS = 'Jots'
CONTACT_ORGANIZATIONS = 'Organizations'
CONTACT_PHONES = 'Phones'
CONTACT_RELATIONS = 'Relations'
CONTACT_USER_DEFINED_FIELDS = 'User Defined Fields'
CONTACT_WEBSITES = 'Websites'
#
class ContactsManager():

  CONTACT_ARGUMENT_TO_PROPERTY_MAP = {
    'json': CONTACT_JSON,
    'name': CONTACT_NAME,
    'prefix': CONTACT_NAME_PREFIX,
    'givenname': CONTACT_GIVEN_NAME,
    'additionalname': CONTACT_ADDITIONAL_NAME,
    'familyname': CONTACT_FAMILY_NAME,
    'firstname': CONTACT_GIVEN_NAME,
    'middlename': CONTACT_ADDITIONAL_NAME,
    'lastname': CONTACT_FAMILY_NAME,
    'suffix': CONTACT_NAME_SUFFIX,
    'nickname': CONTACT_NICKNAME,
    'maidenname': CONTACT_MAIDENNAME,
    'shortname': CONTACT_SHORTNAME,
    'initials': CONTACT_INITIALS,
    'birthday': CONTACT_BIRTHDAY,
    'gender': CONTACT_GENDER,
    'location': CONTACT_LOCATION,
    'priority': CONTACT_PRIORITY,
    'sensitivity': CONTACT_SENSITIVITY,
    'subject': CONTACT_SUBJECT,
    'language': CONTACT_LANGUAGE,
    'note': CONTACT_NOTES,
    'notes': CONTACT_NOTES,
    'occupation': CONTACT_OCCUPATION,
    'billinginfo': CONTACT_BILLING_INFORMATION,
    'mileage': CONTACT_MILEAGE,
    'directoryserver': CONTACT_DIRECTORY_SERVER,
    'address': CONTACT_ADDRESSES,
    'addresses': CONTACT_ADDRESSES,
    'calendar': CONTACT_CALENDARS,
    'calendars': CONTACT_CALENDARS,
    'email': CONTACT_EMAILS,
    'emails': CONTACT_EMAILS,
    'externalid': CONTACT_EXTERNALIDS,
    'externalids': CONTACT_EXTERNALIDS,
    'event': CONTACT_EVENTS,
    'events': CONTACT_EVENTS,
    'hobby': CONTACT_HOBBIES,
    'hobbies': CONTACT_HOBBIES,
    'im': CONTACT_IMS,
    'ims': CONTACT_IMS,
    'jot': CONTACT_JOTS,
    'jots': CONTACT_JOTS,
    'organization': CONTACT_ORGANIZATIONS,
    'organizations': CONTACT_ORGANIZATIONS,
    'organisation': CONTACT_ORGANIZATIONS,
    'organisations': CONTACT_ORGANIZATIONS,
    'phone': CONTACT_PHONES,
    'phones': CONTACT_PHONES,
    'relation': CONTACT_RELATIONS,
    'relations': CONTACT_RELATIONS,
    'userdefinedfield': CONTACT_USER_DEFINED_FIELDS,
    'userdefinedfields': CONTACT_USER_DEFINED_FIELDS,
    'website': CONTACT_WEBSITES,
    'websites': CONTACT_WEBSITES,
    'updated': CONTACT_UPDATED,
    }

  GENDER_CHOICE_MAP = {'male': 'male', 'female': 'female'}

  PRIORITY_CHOICE_MAP = {'low': 'low', 'normal': 'normal', 'high': 'high'}

  SENSITIVITY_CHOICE_MAP = {
    'confidential': 'confidential',
    'normal': 'normal',
    'personal': 'personal',
    'private': 'private',
    }

  CONTACT_NAME_FIELDS = (
    CONTACT_NAME_PREFIX,
    CONTACT_GIVEN_NAME,
    CONTACT_ADDITIONAL_NAME,
    CONTACT_FAMILY_NAME,
    CONTACT_NAME_SUFFIX,
    )

  ADDRESS_TYPE_ARGUMENT_TO_REL = {
    'work': gdata.apps.contacts.REL_WORK,
    'home': gdata.apps.contacts.REL_HOME,
    'other': gdata.apps.contacts.REL_OTHER,
    }

  ADDRESS_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: 'work',
    gdata.apps.contacts.REL_HOME: 'home',
    gdata.apps.contacts.REL_OTHER: 'other',
    }

  _getMain().ADDRESS_ARGUMENT_TO_FIELD_MAP = {
    'streetaddress': 'street',
    'pobox': 'pobox',
    'neighborhood': 'neighborhood',
    'locality': 'city',
    'region': 'region',
    'postalcode': 'postcode',
    'country': 'country',
    'formatted': 'value', 'unstructured': 'value',
    }

  ADDRESS_FIELD_TO_ARGUMENT_MAP = {
    'street': 'streetaddress',
    'pobox': 'pobox',
    'neighborhood': 'neighborhood',
    'city': 'locality',
    'region': 'region',
    'postcode': 'postalcode',
    'country': 'country',
    }

  ADDRESS_FIELD_PRINT_ORDER = [
    'street',
    'pobox',
    'neighborhood',
    'city',
    'region',
    'postcode',
    'country',
    ]

  CALENDAR_TYPE_ARGUMENT_TO_REL = {
    'work': 'work',
    'home': 'home',
    'free-busy': 'free-busy',
    }

  CALENDAR_REL_TO_TYPE_ARGUMENT = {
    'work': 'work',
    'home': 'home',
    'free-busy': 'free-busy',
    }

  EMAIL_TYPE_ARGUMENT_TO_REL = {
    'work': gdata.apps.contacts.REL_WORK,
    'home': gdata.apps.contacts.REL_HOME,
    'other': gdata.apps.contacts.REL_OTHER,
    }

  EMAIL_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: 'work',
    gdata.apps.contacts.REL_HOME: 'home',
    gdata.apps.contacts.REL_OTHER: 'other',
    }

  EVENT_TYPE_ARGUMENT_TO_REL = {
    'anniversary': 'anniversary',
    'other': 'other',
    }

  EVENT_REL_TO_TYPE_ARGUMENT = {
    'anniversary': 'anniversary',
    'other': 'other',
    }

  EXTERNALID_TYPE_ARGUMENT_TO_REL = {
    'account': 'account',
    'customer': 'customer',
    'network': 'network',
    'organization': 'organization',
    'organisation': 'organization',
    }

  EXTERNALID_REL_TO_TYPE_ARGUMENT = {
    'account': 'account',
    'customer': 'customer',
    'network': 'network',
    'organization': 'organization',
    'organisation': 'organization',
    }

  IM_TYPE_ARGUMENT_TO_REL = {
    'work': gdata.apps.contacts.REL_WORK,
    'home': gdata.apps.contacts.REL_HOME,
    'other': gdata.apps.contacts.REL_OTHER,
    }

  IM_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: 'work',
    gdata.apps.contacts.REL_HOME: 'home',
    gdata.apps.contacts.REL_OTHER: 'other',
    }

  IM_PROTOCOL_TO_REL_MAP = {
    'aim': gdata.apps.contacts.IM_AIM,
    'gtalk': gdata.apps.contacts.IM_GOOGLE_TALK,
    'icq': gdata.apps.contacts.IM_ICQ,
    'jabber': gdata.apps.contacts.IM_JABBER,
    'msn': gdata.apps.contacts.IM_MSN,
    'netmeeting': gdata.apps.contacts.IM_NETMEETING,
    'qq': gdata.apps.contacts.IM_QQ,
    'skype': gdata.apps.contacts.IM_SKYPE,
    'xmpp': gdata.apps.contacts.IM_JABBER,
    'yahoo': gdata.apps.contacts.IM_YAHOO,
    }

  IM_REL_TO_PROTOCOL_MAP = {
    gdata.apps.contacts.IM_AIM: 'aim',
    gdata.apps.contacts.IM_GOOGLE_TALK: 'gtalk',
    gdata.apps.contacts.IM_ICQ: 'icq',
    gdata.apps.contacts.IM_JABBER: 'jabber',
    gdata.apps.contacts.IM_MSN: 'msn',
    gdata.apps.contacts.IM_NETMEETING: 'netmeeting',
    gdata.apps.contacts.IM_QQ: 'qq',
    gdata.apps.contacts.IM_SKYPE: 'skype',
    gdata.apps.contacts.IM_YAHOO: 'yahoo',
    }

  JOT_TYPE_ARGUMENT_TO_REL = {
    'work': 'work',
    'home': 'home',
    'other': 'other',
    'keywords': 'keywords',
    'user': 'user',
    }

  JOT_REL_TO_TYPE_ARGUMENT = {
    'work': 'work',
    'home': 'home',
    'other': 'other',
    'keywords': 'keywords',
    'user': 'user',
    }

  ORGANIZATION_TYPE_ARGUMENT_TO_REL = {
    'work': gdata.apps.contacts.REL_WORK,
    'other': gdata.apps.contacts.REL_OTHER,
    }

  ORGANIZATION_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.REL_WORK: 'work',
    gdata.apps.contacts.REL_OTHER: 'other',
    }

  _getMain().ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
    'location': 'where',
    'department': 'department',
    'title': 'title',
    'jobdescription': 'jobdescription',
    'symbol': 'symbol',
    }

  ORGANIZATION_FIELD_TO_ARGUMENT_MAP = {
    'where': 'location',
    'department': 'department',
    'title': 'title',
    'jobdescription': 'jobdescription',
    'symbol': 'symbol',
    }

  ORGANIZATION_FIELD_PRINT_ORDER = [
    'where',
    'department',
    'title',
    'jobdescription',
    'symbol',
    ]

  PHONE_TYPE_ARGUMENT_TO_REL = {
    'work': gdata.apps.contacts.PHONE_WORK,
    'home': gdata.apps.contacts.PHONE_HOME,
    'other': gdata.apps.contacts.PHONE_OTHER,
    'fax': gdata.apps.contacts.PHONE_FAX,
    'home_fax': gdata.apps.contacts.PHONE_HOME_FAX,
    'work_fax': gdata.apps.contacts.PHONE_WORK_FAX,
    'other_fax': gdata.apps.contacts.PHONE_OTHER_FAX,
    'main': gdata.apps.contacts.PHONE_MAIN,
    'company_main': gdata.apps.contacts.PHONE_COMPANY_MAIN,
    'assistant': gdata.apps.contacts.PHONE_ASSISTANT,
    'mobile': gdata.apps.contacts.PHONE_MOBILE,
    'work_mobile': gdata.apps.contacts.PHONE_WORK_MOBILE,
    'pager': gdata.apps.contacts.PHONE_PAGER,
    'work_pager': gdata.apps.contacts.PHONE_WORK_PAGER,
    'car': gdata.apps.contacts.PHONE_CAR,
    'radio': gdata.apps.contacts.PHONE_RADIO,
    'callback': gdata.apps.contacts.PHONE_CALLBACK,
    'isdn': gdata.apps.contacts.PHONE_ISDN,
    'telex': gdata.apps.contacts.PHONE_TELEX,
    'tty_tdd': gdata.apps.contacts.PHONE_TTY_TDD,
    }

  PHONE_REL_TO_TYPE_ARGUMENT = {
    gdata.apps.contacts.PHONE_WORK: 'work',
    gdata.apps.contacts.PHONE_HOME: 'home',
    gdata.apps.contacts.PHONE_OTHER: 'other',
    gdata.apps.contacts.PHONE_FAX: 'fax',
    gdata.apps.contacts.PHONE_HOME_FAX: 'home_fax',
    gdata.apps.contacts.PHONE_WORK_FAX: 'work_fax',
    gdata.apps.contacts.PHONE_OTHER_FAX: 'other_fax',
    gdata.apps.contacts.PHONE_MAIN: 'main',
    gdata.apps.contacts.PHONE_COMPANY_MAIN: 'company_main',
    gdata.apps.contacts.PHONE_ASSISTANT: 'assistant',
    gdata.apps.contacts.PHONE_MOBILE: 'mobile',
    gdata.apps.contacts.PHONE_WORK_MOBILE: 'work_mobile',
    gdata.apps.contacts.PHONE_PAGER: 'pager',
    gdata.apps.contacts.PHONE_WORK_PAGER: 'work_pager',
    gdata.apps.contacts.PHONE_CAR: 'car',
    gdata.apps.contacts.PHONE_RADIO: 'radio',
    gdata.apps.contacts.PHONE_CALLBACK: 'callback',
    gdata.apps.contacts.PHONE_ISDN: 'isdn',
    gdata.apps.contacts.PHONE_TELEX: 'telex',
    gdata.apps.contacts.PHONE_TTY_TDD: 'tty_tdd',
    }

  RELATION_TYPE_ARGUMENT_TO_REL = {
    'spouse': 'spouse',
    'child': 'child',
    'mother': 'mother',
    'father': 'father',
    'parent': 'parent',
    'brother': 'brother',
    'sister': 'sister',
    'friend': 'friend',
    'relative': 'relative',
    'manager': 'manager',
    'assistant': 'assistant',
    'referredby': 'referred-by',
    'partner': 'partner',
    'domesticpartner': 'domestic-partner',
    }

  RELATION_REL_TO_TYPE_ARGUMENT = {
    'spouse' : 'spouse',
    'child' : 'child',
    'mother' : 'mother',
    'father' : 'father',
    'parent' : 'parent',
    'brother' : 'brother',
    'sister' : 'sister',
    'friend' : 'friend',
    'relative' : 'relative',
    'manager' : 'manager',
    'assistant' : 'assistant',
    'referred-by' : 'referred_by',
    'partner' : 'partner',
    'domestic-partner' : 'domestic_partner',
    }

  WEBSITE_TYPE_ARGUMENT_TO_REL = {
    'home-page': 'home-page',
    'blog': 'blog',
    'profile': 'profile',
    'work': 'work',
    'home': 'home',
    'other': 'other',
    'ftp': 'ftp',
    'reservations': 'reservations',
    'app-install-page': 'app-install-page',
    }

  WEBSITE_REL_TO_TYPE_ARGUMENT = {
    'home-page': 'home-page',
    'blog': 'blog',
    'profile': 'profile',
    'work': 'work',
    'home': 'home',
    'other': 'other',
    'ftp': 'ftp',
    'reservations': 'reservations',
    'app-install-page': 'app-install-page',
    }

  CONTACT_NAME_PROPERTY_PRINT_ORDER = [
    CONTACT_UPDATED,
    CONTACT_NAME,
    CONTACT_NAME_PREFIX,
    CONTACT_GIVEN_NAME,
    CONTACT_ADDITIONAL_NAME,
    CONTACT_FAMILY_NAME,
    CONTACT_NAME_SUFFIX,
    CONTACT_NICKNAME,
    CONTACT_MAIDENNAME,
    CONTACT_SHORTNAME,
    CONTACT_INITIALS,
    CONTACT_BIRTHDAY,
    CONTACT_GENDER,
    CONTACT_LOCATION,
    CONTACT_PRIORITY,
    CONTACT_SENSITIVITY,
    CONTACT_SUBJECT,
    CONTACT_LANGUAGE,
    CONTACT_NOTES,
    CONTACT_OCCUPATION,
    CONTACT_BILLING_INFORMATION,
    CONTACT_MILEAGE,
    CONTACT_DIRECTORY_SERVER,
    ]

  CONTACT_ARRAY_PROPERTY_PRINT_ORDER = [
    CONTACT_ADDRESSES,
    CONTACT_EMAILS,
    CONTACT_IMS,
    CONTACT_PHONES,
    CONTACT_CALENDARS,
    CONTACT_ORGANIZATIONS,
    CONTACT_EXTERNALIDS,
    CONTACT_EVENTS,
    CONTACT_HOBBIES,
    CONTACT_JOTS,
    CONTACT_RELATIONS,
    CONTACT_WEBSITES,
    CONTACT_USER_DEFINED_FIELDS,
    ]

  CONTACT_ARRAY_PROPERTIES = {
    CONTACT_ADDRESSES: {'relMap': ADDRESS_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'formatted', 'primary': True},
    CONTACT_EMAILS: {'relMap': EMAIL_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'address', 'primary': True},
    CONTACT_IMS: {'relMap': IM_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'address', 'primary': True},
    CONTACT_PHONES: {'relMap': PHONE_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'value', 'primary': True},
    CONTACT_CALENDARS: {'relMap': CALENDAR_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'address', 'primary': True},
    CONTACT_ORGANIZATIONS: {'relMap': ORGANIZATION_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'name', 'primary': True},
    CONTACT_EXTERNALIDS: {'relMap': EXTERNALID_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'value', 'primary': False},
    CONTACT_EVENTS: {'relMap': EVENT_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'date', 'primary': False},
    CONTACT_HOBBIES: {'relMap': None, 'infoTitle': 'value', 'primary': False},
    CONTACT_JOTS: {'relMap': JOT_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'value', 'primary': False},
    CONTACT_RELATIONS: {'relMap': RELATION_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'value', 'primary': False},
    CONTACT_USER_DEFINED_FIELDS: {'relMap': None, 'infoTitle': 'value', 'primary': False},
    CONTACT_WEBSITES: {'relMap': WEBSITE_REL_TO_TYPE_ARGUMENT, 'infoTitle': 'value', 'primary': True},
    }

  @staticmethod
  def GetContactShortId(contactEntry):
    full_id = contactEntry.id.text
    return full_id[full_id.rfind('/')+1:]

  @staticmethod
  def GetContactFields(parameters=None):

    fields = {}

    def CheckClearFieldsList(fieldName):
      if _getMain().checkArgumentPresent(Cmd.CLEAR_NONE_ARGUMENT):
        fields.pop(fieldName, None)
        fields[fieldName] = []
        return True
      return False

    def InitArrayItem(choices):
      item = {}
      rel = _getMain().getChoice(choices, mapChoice=True, defaultChoice=None)
      if rel:
        item['rel'] = rel
        item['label'] = None
      else:
        item['rel'] = None
        item['label'] = _getMain().getString(Cmd.OB_STRING)
      return item

    def PrimaryNotPrimary(pnp, entry):
      if pnp == 'notprimary':
        entry['primary'] = 'false'
        return True
      if pnp == 'primary':
        entry['primary'] = 'true'
        primary['location'] = Cmd.Location()
        return True
      return False

    def GetPrimaryNotPrimaryChoice(entry):
      if not _getMain().getChoice({'primary': True, 'notprimary': False}, mapChoice=True):
        entry['primary'] = 'false'
      else:
        entry['primary'] = 'true'
        primary['location'] = Cmd.Location()

    def AppendItemToFieldsList(fieldName, fieldValue, checkBlankField=None):
      fields.setdefault(fieldName, [])
      if checkBlankField is None or fieldValue[checkBlankField]:
        if isinstance(fieldValue, dict) and fieldValue.get('primary', 'false') == 'true':
          for citem in fields[fieldName]:
            if citem.get('primary', 'false') == 'true':
              Cmd.SetLocation(primary['location']-1)
              _getMain().usageErrorExit(Msg.MULTIPLE_ITEMS_MARKED_PRIMARY.format(fieldName))
        fields[fieldName].append(fieldValue)

    primary = {}
    while Cmd.ArgumentsRemaining():
      if parameters is not None:
        if _getCreateContactReturnOptions(parameters):
          continue
        Cmd.Backup()
      fieldName = _getMain().getChoice(ContactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if fieldName == CONTACT_BIRTHDAY:
        fields[fieldName] = _getMain().getYYYYMMDD(minLen=0)
      elif fieldName == CONTACT_GENDER:
        fields[fieldName] = _getMain().getChoice(ContactsManager.GENDER_CHOICE_MAP, mapChoice=True)
      elif fieldName == CONTACT_PRIORITY:
        fields[fieldName] = _getMain().getChoice(ContactsManager.PRIORITY_CHOICE_MAP, mapChoice=True)
      elif fieldName == CONTACT_SENSITIVITY:
        fields[fieldName] = _getMain().getChoice(ContactsManager.SENSITIVITY_CHOICE_MAP, mapChoice=True)
      elif fieldName == CONTACT_LANGUAGE:
        fields[fieldName] = _getMain().getLanguageCode(_getMain().LANGUAGE_CODES_MAP)
      elif fieldName == CONTACT_NOTES:
        fields[fieldName] = _getMain().getStringWithCRsNLsOrFile()[0]
      elif fieldName == CONTACT_ADDRESSES:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.ADDRESS_TYPE_ARGUMENT_TO_REL)
        entry['primary'] = 'false'
        while Cmd.ArgumentsRemaining():
          argument = _getMain().getArgument()
          if argument in ContactsManager.ADDRESS_ARGUMENT_TO_FIELD_MAP:
            value = _getMain().getString(Cmd.OB_STRING, minLen=0)
            if value:
              entry[ContactsManager.ADDRESS_ARGUMENT_TO_FIELD_MAP[argument]] = value.replace('\\n', '\n')
          elif PrimaryNotPrimary(argument, entry):
            break
          else:
            _getMain().unknownArgumentExit()
        AppendItemToFieldsList(fieldName, entry)
      elif fieldName == CONTACT_CALENDARS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.CALENDAR_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_EMAILS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.EMAIL_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getEmailAddress(noUid=True, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_EVENTS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.EVENT_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getYYYYMMDD(minLen=0)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_EXTERNALIDS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.EXTERNALID_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_HOBBIES:
        if CheckClearFieldsList(fieldName):
          continue
        entry = {'value': _getMain().getString(Cmd.OB_STRING, minLen=0)}
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_IMS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.IM_TYPE_ARGUMENT_TO_REL)
        entry['protocol'] = _getMain().getChoice(ContactsManager.IM_PROTOCOL_TO_REL_MAP, mapChoice=True)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_JOTS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = {'rel': _getMain().getChoice(ContactsManager.JOT_TYPE_ARGUMENT_TO_REL, mapChoice=True)}
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_ORGANIZATIONS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.ORGANIZATION_TYPE_ARGUMENT_TO_REL)
        entry['primary'] = 'false'
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        while Cmd.ArgumentsRemaining():
          argument = _getMain().getArgument()
          if argument in ContactsManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP:
            value = _getMain().getString(Cmd.OB_STRING, minLen=0)
            if value:
              entry[ContactsManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP[argument]] = value
          elif PrimaryNotPrimary(argument, entry):
            break
          else:
            _getMain().unknownArgumentExit()
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_PHONES:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.PHONE_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_RELATIONS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.RELATION_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_USER_DEFINED_FIELDS:
        if CheckClearFieldsList(fieldName):
          continue
        entry = {'rel': getString(Cmd.OB_STRING, minLen=0), 'value': _getMain().getString(Cmd.OB_STRING, minLen=0)}
        if not entry['rel'] or entry['rel'].lower() == 'none':
          entry['rel'] = None
        AppendItemToFieldsList(fieldName, entry, 'value')
      elif fieldName == CONTACT_WEBSITES:
        if CheckClearFieldsList(fieldName):
          continue
        entry = InitArrayItem(ContactsManager.WEBSITE_TYPE_ARGUMENT_TO_REL)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendItemToFieldsList(fieldName, entry, 'value')
      else:
        fields[fieldName] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    return fields

  @staticmethod
  def FieldsToContact(fields):
    def GetField(fieldName):
      return fields.get(fieldName)

    def SetClassAttribute(value, fieldClass, processNLs, attr):
      if value:
        if processNLs:
          value = value.replace('\\n', '\n')
        if attr == 'text':
          return fieldClass(text=value)
        if attr == 'code':
          return fieldClass(code=value)
        if attr == 'rel':
          return fieldClass(rel=value)
        if attr == 'value':
          return fieldClass(value=value)
        if attr == 'value_string':
          return fieldClass(value_string=value)
        if attr == 'when':
          return fieldClass(when=value)
      return None

    def GetContactField(fieldName, fieldClass, processNLs=False, attr='text'):
      return SetClassAttribute(fields.get(fieldName), fieldClass, processNLs, attr)

    def GetListEntryField(entry, fieldName, fieldClass, processNLs=False, attr='text'):
      return SetClassAttribute(entry.get(fieldName), fieldClass, processNLs, attr)

    contactEntry = gdata.apps.contacts.ContactEntry()
    value = GetField(CONTACT_NAME)
    if not value:
      value = ' '.join([fields[fieldName] for fieldName in ContactsManager.CONTACT_NAME_FIELDS if fieldName in fields])
    contactEntry.name = gdata.apps.contacts.Name(full_name=gdata.apps.contacts.FullName(text=value))
    contactEntry.name.name_prefix = GetContactField(CONTACT_NAME_PREFIX, gdata.apps.contacts.NamePrefix)
    contactEntry.name.given_name = GetContactField(CONTACT_GIVEN_NAME, gdata.apps.contacts.GivenName)
    contactEntry.name.additional_name = GetContactField(CONTACT_ADDITIONAL_NAME, gdata.apps.contacts.AdditionalName)
    contactEntry.name.family_name = GetContactField(CONTACT_FAMILY_NAME, gdata.apps.contacts.FamilyName)
    contactEntry.name.name_suffix = GetContactField(CONTACT_NAME_SUFFIX, gdata.apps.contacts.NameSuffix)
    contactEntry.nickname = GetContactField(CONTACT_NICKNAME, gdata.apps.contacts.Nickname)
    contactEntry.maidenName = GetContactField(CONTACT_MAIDENNAME, gdata.apps.contacts.MaidenName)
    contactEntry.shortName = GetContactField(CONTACT_SHORTNAME, gdata.apps.contacts.ShortName)
    contactEntry.initials = GetContactField(CONTACT_INITIALS, gdata.apps.contacts.Initials)
    contactEntry.birthday = GetContactField(CONTACT_BIRTHDAY, gdata.apps.contacts.Birthday, attr='when')
    contactEntry.gender = GetContactField(CONTACT_GENDER, gdata.apps.contacts.Gender, attr='value')
    contactEntry.where = GetContactField(CONTACT_LOCATION, gdata.apps.contacts.Where, attr='value_string')
    contactEntry.priority = GetContactField(CONTACT_PRIORITY, gdata.apps.contacts.Priority, attr='rel')
    contactEntry.sensitivity = GetContactField(CONTACT_SENSITIVITY, gdata.apps.contacts.Sensitivity, attr='rel')
    contactEntry.subject = GetContactField(CONTACT_SUBJECT, gdata.apps.contacts.Subject)
    contactEntry.language = GetContactField(CONTACT_LANGUAGE, gdata.apps.contacts.Language, attr='code')
    contactEntry.content = GetContactField(CONTACT_NOTES, gdata.apps.contacts.Content, processNLs=True)
    contactEntry.occupation = GetContactField(CONTACT_OCCUPATION, gdata.apps.contacts.Occupation)
    contactEntry.billingInformation = GetContactField(CONTACT_BILLING_INFORMATION, gdata.apps.contacts.BillingInformation, processNLs=True)
    contactEntry.mileage = GetContactField(CONTACT_MILEAGE, gdata.apps.contacts.Mileage)
    contactEntry.directoryServer = GetContactField(CONTACT_DIRECTORY_SERVER, gdata.apps.contacts.DirectoryServer)
    value = GetField(CONTACT_ADDRESSES)
    if value:
      for address in value:
        street = GetListEntryField(address, 'street', gdata.apps.contacts.Street)
        pobox = GetListEntryField(address, 'pobox', gdata.apps.contacts.PoBox)
        neighborhood = GetListEntryField(address, 'neighborhood', gdata.apps.contacts.Neighborhood)
        city = GetListEntryField(address, 'city', gdata.apps.contacts.City)
        region = GetListEntryField(address, 'region', gdata.apps.contacts.Region)
        postcode = GetListEntryField(address, 'postcode', gdata.apps.contacts.Postcode)
        country = GetListEntryField(address, 'country', gdata.apps.contacts.Country)
        formatted_address = GetListEntryField(address, 'value', gdata.apps.contacts.FormattedAddress, processNLs=True)
        contactEntry.structuredPostalAddress.append(gdata.apps.contacts.StructuredPostalAddress(street=street, pobox=pobox, neighborhood=neighborhood,
                                                                                                city=city, region=region,
                                                                                                postcode=postcode, country=country,
                                                                                                formatted_address=formatted_address,
                                                                                                rel=address['rel'], label=address['label'], primary=address['primary']))
    value = GetField(CONTACT_CALENDARS)
    if value:
      for calendarLink in value:
        contactEntry.calendarLink.append(gdata.apps.contacts.CalendarLink(href=calendarLink['value'], rel=calendarLink['rel'], label=calendarLink['label'], primary=calendarLink['primary']))
    value = GetField(CONTACT_EMAILS)
    if value:
      for emailaddr in value:
        contactEntry.email.append(gdata.apps.contacts.Email(address=emailaddr['value'], rel=emailaddr['rel'], label=emailaddr['label'], primary=emailaddr['primary']))
    value = GetField(CONTACT_EXTERNALIDS)
    if value:
      for externalid in value:
        contactEntry.externalId.append(gdata.apps.contacts.ExternalId(value=externalid['value'], rel=externalid['rel'], label=externalid['label']))
    value = GetField(CONTACT_EVENTS)
    if value:
      for event in value:
        contactEntry.event.append(gdata.apps.contacts.Event(rel=event['rel'], label=event['label'],
                                                            when=gdata.apps.contacts.When(startTime=event['value'])))
    value = GetField(CONTACT_HOBBIES)
    if value:
      for hobby in value:
        contactEntry.hobby.append(gdata.apps.contacts.Hobby(text=hobby['value']))
    value = GetField(CONTACT_IMS)
    if value:
      for im in value:
        contactEntry.im.append(gdata.apps.contacts.IM(address=im['value'], protocol=im['protocol'], rel=im['rel'], label=im['label'], primary=im['primary']))
    value = GetField(CONTACT_JOTS)
    if value:
      for jot in value:
        contactEntry.jot.append(gdata.apps.contacts.Jot(text=jot['value'], rel=jot['rel']))
    value = GetField(CONTACT_ORGANIZATIONS)
    if value:
      for organization in value:
        org_name = gdata.apps.contacts.OrgName(text=organization['value'])
        department = GetListEntryField(organization, 'department', gdata.apps.contacts.OrgDepartment)
        title = GetListEntryField(organization, 'title', gdata.apps.contacts.OrgTitle)
        job_description = GetListEntryField(organization, 'jobdescription', gdata.apps.contacts.OrgJobDescription)
        symbol = GetListEntryField(organization, 'symbol', gdata.apps.contacts.OrgSymbol)
        where = GetListEntryField(organization, 'where', gdata.apps.contacts.Where, attr='value_string')
        contactEntry.organization.append(gdata.apps.contacts.Organization(name=org_name, department=department,
                                                                          title=title, job_description=job_description,
                                                                          symbol=symbol, where=where,
                                                                          rel=organization['rel'], label=organization['label'], primary=organization['primary']))
    value = GetField(CONTACT_PHONES)
    if value:
      for phone in value:
        contactEntry.phoneNumber.append(gdata.apps.contacts.PhoneNumber(text=phone['value'], rel=phone['rel'], label=phone['label'], primary=phone['primary']))
    value = GetField(CONTACT_RELATIONS)
    if value:
      for relation in value:
        contactEntry.relation.append(gdata.apps.contacts.Relation(text=relation['value'], rel=relation['rel'], label=relation['label']))
    value = GetField(CONTACT_USER_DEFINED_FIELDS)
    if value:
      for userdefinedfield in value:
        contactEntry.userDefinedField.append(gdata.apps.contacts.UserDefinedField(key=userdefinedfield['rel'], value=userdefinedfield['value']))
    value = GetField(CONTACT_WEBSITES)
    if value:
      for website in value:
        contactEntry.website.append(gdata.apps.contacts.Website(href=website['value'], rel=website['rel'], label=website['label'], primary=website['primary']))
    return contactEntry

  @staticmethod
  def ContactToFields(contactEntry):
    fields = {}
    def GetContactField(fieldName, attrlist):
      objAttr = contactEntry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return
      fields[fieldName] = objAttr

    def GetListEntryField(entry, attrlist):
      objAttr = entry
      for attr in attrlist:
        objAttr = getattr(objAttr, attr)
        if not objAttr:
          return None
      return objAttr

    def AppendItemToFieldsList(fieldName, fieldValue):
      fields.setdefault(fieldName, [])
      fields[fieldName].append(fieldValue)

    fields[CONTACT_ID] = ContactsManager.GetContactShortId(contactEntry)
    GetContactField(CONTACT_UPDATED, ['updated', 'text'])
    if not contactEntry.deleted:
      GetContactField(CONTACT_NAME, ['title', 'text'])
    else:
      fields[CONTACT_NAME] = 'Deleted'
    GetContactField(CONTACT_NAME_PREFIX, ['name', 'name_prefix', 'text'])
    GetContactField(CONTACT_GIVEN_NAME, ['name', 'given_name', 'text'])
    GetContactField(CONTACT_ADDITIONAL_NAME, ['name', 'additional_name', 'text'])
    GetContactField(CONTACT_FAMILY_NAME, ['name', 'family_name', 'text'])
    GetContactField(CONTACT_NAME_SUFFIX, ['name', 'name_suffix', 'text'])
    GetContactField(CONTACT_NICKNAME, ['nickname', 'text'])
    GetContactField(CONTACT_MAIDENNAME, ['maidenName', 'text'])
    GetContactField(CONTACT_SHORTNAME, ['shortName', 'text'])
    GetContactField(CONTACT_INITIALS, ['initials', 'text'])
    GetContactField(CONTACT_BIRTHDAY, ['birthday', 'when'])
    GetContactField(CONTACT_GENDER, ['gender', 'value'])
    GetContactField(CONTACT_SUBJECT, ['subject', 'text'])
    GetContactField(CONTACT_LANGUAGE, ['language', 'code'])
    GetContactField(CONTACT_PRIORITY, ['priority', 'rel'])
    GetContactField(CONTACT_SENSITIVITY, ['sensitivity', 'rel'])
    GetContactField(CONTACT_NOTES, ['content', 'text'])
    GetContactField(CONTACT_LOCATION, ['where', 'value_string'])
    GetContactField(CONTACT_OCCUPATION, ['occupation', 'text'])
    GetContactField(CONTACT_BILLING_INFORMATION, ['billingInformation', 'text'])
    GetContactField(CONTACT_MILEAGE, ['mileage', 'text'])
    GetContactField(CONTACT_DIRECTORY_SERVER, ['directoryServer', 'text'])
    for address in contactEntry.structuredPostalAddress:
      AppendItemToFieldsList(CONTACT_ADDRESSES,
                             {'rel': address.rel,
                              'label': address.label,
                              'value': GetListEntryField(address, ['formatted_address', 'text']),
                              'street': GetListEntryField(address, ['street', 'text']),
                              'pobox': GetListEntryField(address, ['pobox', 'text']),
                              'neighborhood': GetListEntryField(address, ['neighborhood', 'text']),
                              'city': GetListEntryField(address, ['city', 'text']),
                              'region': GetListEntryField(address, ['region', 'text']),
                              'postcode': GetListEntryField(address, ['postcode', 'text']),
                              'country': GetListEntryField(address, ['country', 'text']),
                              'primary': address.primary})
    for calendarLink in contactEntry.calendarLink:
      AppendItemToFieldsList(CONTACT_CALENDARS,
                             {'rel': calendarLink.rel,
                              'label': calendarLink.label,
                              'value': calendarLink.href,
                              'primary': calendarLink.primary})
    for emailaddr in contactEntry.email:
      AppendItemToFieldsList(CONTACT_EMAILS,
                             {'rel': emailaddr.rel,
                              'label': emailaddr.label,
                              'value': emailaddr.address,
                              'primary': emailaddr.primary})
    for externalid in contactEntry.externalId:
      AppendItemToFieldsList(CONTACT_EXTERNALIDS,
                             {'rel': externalid.rel,
                              'label': externalid.label,
                              'value': externalid.value})
    for event in contactEntry.event:
      AppendItemToFieldsList(CONTACT_EVENTS,
                             {'rel': event.rel,
                              'label': event.label,
                              'value': GetListEntryField(event, ['when', 'startTime'])})
    for hobby in contactEntry.hobby:
      AppendItemToFieldsList(CONTACT_HOBBIES,
                             {'value': hobby.text})
    for im in contactEntry.im:
      AppendItemToFieldsList(CONTACT_IMS,
                             {'rel': im.rel,
                              'label': im.label,
                              'value': im.address,
                              'protocol': im.protocol,
                              'primary': im.primary})
    for jot in contactEntry.jot:
      AppendItemToFieldsList(CONTACT_JOTS,
                             {'rel': jot.rel,
                              'value': jot.text})
    for organization in contactEntry.organization:
      AppendItemToFieldsList(CONTACT_ORGANIZATIONS,
                             {'rel': organization.rel,
                              'label': organization.label,
                              'value': GetListEntryField(organization, ['name', 'text']),
                              'department': GetListEntryField(organization, ['department', 'text']),
                              'title': GetListEntryField(organization, ['title', 'text']),
                              'symbol': GetListEntryField(organization, ['symbol', 'text']),
                              'jobdescription': GetListEntryField(organization, ['job_description', 'text']),
                              'where': GetListEntryField(organization, ['where', 'value_string']),
                              'primary': organization.primary})
    for phone in contactEntry.phoneNumber:
      AppendItemToFieldsList(CONTACT_PHONES,
                             {'rel': phone.rel,
                              'label': phone.label,
                              'value': phone.text,
                              'primary': phone.primary})
    for relation in contactEntry.relation:
      AppendItemToFieldsList(CONTACT_RELATIONS,
                             {'rel': relation.rel,
                              'label': relation.label,
                              'value': relation.text})
    for userdefinedfield in contactEntry.userDefinedField:
      AppendItemToFieldsList(CONTACT_USER_DEFINED_FIELDS,
                             {'rel': userdefinedfield.key,
                              'value': userdefinedfield.value})
    for website in contactEntry.website:
      AppendItemToFieldsList(CONTACT_WEBSITES,
                             {'rel': website.rel,
                              'label': website.label,
                              'value': website.href,
                              'primary': website.primary})
    return fields

CONTACTS_PROJECTION_CHOICE_MAP = {'basic': 'thin', 'thin': 'thin', 'full': 'full'}
CONTACTS_ORDERBY_CHOICE_MAP = {'lastmodified': 'lastmodified'}

def normalizeContactId(contactId):
  if contactId.startswith('id:'):
    return contactId[3:]
  return contactId

def _initContactQueryAttributes():
  return {'query': None, 'projection': 'full', 'url_params': {'max-results': str(GC.Values[GC.CONTACT_MAX_RESULTS])},
          'emailMatchPattern': None, 'emailMatchType': None}

def _getContactQueryAttributes(contactQuery, myarg, unknownAction, printShowCmd):
  if myarg == 'query':
    contactQuery['query'] = _getMain().getString(Cmd.OB_QUERY)
  elif myarg == 'emailmatchpattern':
    contactQuery['emailMatchPattern'] = _getMain().getREPattern(re.IGNORECASE)
  elif myarg == 'emailmatchtype':
    contactQuery['emailMatchType'] = _getMain().getString(Cmd.OB_CONTACT_EMAIL_TYPE)
  elif myarg == 'updatedmin':
    contactQuery['url_params']['updated-min'] = _getMain().getYYYYMMDD()
  elif myarg == 'endquery':
    return False
  elif not printShowCmd:
    if unknownAction < 0:
      _getMain().unknownArgumentExit()
    if unknownAction > 0:
      Cmd.Backup()
    return False
  elif myarg == 'orderby':
    contactQuery['url_params']['orderby'], contactQuery['url_params']['sortorder'] = getOrderBySortOrder(CONTACTS_ORDERBY_CHOICE_MAP, 'ascending', False)
  elif myarg in CONTACTS_PROJECTION_CHOICE_MAP:
    contactQuery['projection'] = CONTACTS_PROJECTION_CHOICE_MAP[myarg]
  elif myarg == 'showdeleted':
    contactQuery['url_params']['showdeleted'] = 'true'
  else:
    if unknownAction < 0:
      _getMain().unknownArgumentExit()
    if unknownAction > 0:
      Cmd.Backup()
    return False
  return True

CONTACT_SELECT_ARGUMENTS = {'query', 'emailmatchpattern', 'emailmatchtype', 'updatedmin'}

def _getContactEntityList(unknownAction, printShowCmd):
  contactQuery = _initContactQueryAttributes()
  if Cmd.PeekArgumentPresent(CONTACT_SELECT_ARGUMENTS):
    entityList = None
    queriedContacts = True
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if not _getContactQueryAttributes(contactQuery, myarg, unknownAction, printShowCmd):
        break
  else:
    entityList = _getMain().getEntityList(Cmd.OB_CONTACT_ENTITY)
    queriedContacts = False
    if unknownAction < 0:
      _getMain().checkForExtraneousArguments()
  return (entityList, contactQuery, queriedContacts)

def queryContacts(contactsObject, contactQuery):
  entityType = Ent.DOMAIN
  user = GC.Values[GC.DOMAIN]
  if contactQuery['query']:
    uri = _getMain().getContactsQuery(feed=contactsObject.GetContactFeedUri(contact_list=user, projection=contactQuery['projection']),
                           text_query=contactQuery['query']).ToUri()
  else:
    uri = contactsObject.GetContactFeedUri(contact_list=user, projection=contactQuery['projection'])
  _getMain().printGettingAllEntityItemsForWhom(Ent.CONTACT, user, query=contactQuery['query'])
  try:
    entityList = _getMain().callGDataPages(contactsObject, 'GetContactsFeed',
                                pageMessage=_getMain().getPageMessageForWhom(),
                                throwErrors=[GDATA.BAD_REQUEST, GDATA.FORBIDDEN],
                                retryErrors=[GDATA.INTERNAL_SERVER_ERROR],
                                uri=uri, url_params=contactQuery['url_params'])
    return entityList
  except GDATA.badRequest as e:
    _getMain().entityActionFailedWarning([entityType, user, Ent.CONTACT, ''], str(e))
  except GDATA.forbidden:
    _getMain().entityServiceNotApplicableWarning(entityType, user)
  return None

def localContactSelects(contactsManager, contactQuery, fields):
  if contactQuery['emailMatchPattern']:
    emailMatchType = contactQuery['emailMatchType']
    for item in fields.get(CONTACT_EMAILS, []):
      if contactQuery['emailMatchPattern'].match(item['value']):
        if (not emailMatchType or
            emailMatchType == item.get('label') or
            emailMatchType == contactsManager.CONTACT_ARRAY_PROPERTIES[CONTACT_EMAILS]['relMap'].get(item['rel'], 'custom')):
          break
    else:
      return False
  return True

def countLocalContactSelects(contactsManager, contacts, contactQuery):
  if contacts is not None and contactQuery:
    jcount = 0
    for contact in contacts:
      fields = contactsManager.ContactToFields(contact)
      if localContactSelects(contactsManager, contactQuery, fields):
        jcount += 1
  else:
    jcount = len(contacts) if contacts is not None else 0
  return jcount

def clearEmailAddressMatches(contactsManager, contactClear, fields):
  savedAddresses = []
  updateRequired = False
  emailMatchType = contactClear['emailClearType']
  for item in fields.get(CONTACT_EMAILS, []):
    if (contactClear['emailClearPattern'].match(item['value']) and
        (not emailMatchType or
         emailMatchType == item.get('label') or
         emailMatchType == contactsManager.CONTACT_ARRAY_PROPERTIES[CONTACT_EMAILS]['relMap'].get(item['rel'], 'custom'))):
      updateRequired = True
    else:
      savedAddresses.append(item)
  if updateRequired:
    fields[CONTACT_EMAILS] = savedAddresses
  return updateRequired

def dedupEmailAddressMatches(contactsManager, emailMatchType, fields):
  sai = -1
  savedAddresses = []
  matches = {}
  updateRequired = False
  for item in fields.get(CONTACT_EMAILS, []):
    emailAddr = item['value']
    emailType = item.get('label')
    if emailType is None:
      emailType = contactsManager.CONTACT_ARRAY_PROPERTIES[CONTACT_EMAILS]['relMap'].get(item['rel'], 'custom')
    if (emailAddr in matches) and (not emailMatchType or emailType in matches[emailAddr]['types']):
      if item['primary'] == 'true':
        savedAddresses[matches[emailAddr]['sai']]['primary'] = 'true'
      updateRequired = True
    else:
      savedAddresses.append(item)
      sai += 1
      matches.setdefault(emailAddr, {'types': set(), 'sai': sai})
      matches[emailAddr]['types'].add(emailType)
  if updateRequired:
    fields[CONTACT_EMAILS] = savedAddresses
  return updateRequired

# gam create contact <ContactAttribute>+
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
def doCreateDomainContact():
  entityType = Ent.DOMAIN
  contactsManager = ContactsManager()
  parameters = {'csvPF': None, 'titles': ['Domain', CONTACT_ID], 'addCSVData': {}, 'returnIdOnly': False}
  fields = contactsManager.GetContactFields(parameters)
  csvPF = parameters['csvPF']
  addCSVData = parameters['addCSVData']
  if addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
  returnIdOnly = parameters['returnIdOnly']
  contactEntry = contactsManager.FieldsToContact(fields)
  user, contactsObject = _getMain().getContactsObject()
  try:
    contact = _getMain().callGData(contactsObject, 'CreateContact',
                        throwErrors=[GDATA.BAD_REQUEST, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN],
                        retryErrors=[GDATA.INTERNAL_SERVER_ERROR],
                        new_contact=contactEntry, insert_uri=contactsObject.GetContactFeedUri(contact_list=user))
    contactId = contactsManager.GetContactShortId(contact)
    if returnIdOnly:
      _getMain().writeStdout(f'{contactId}\n')
    elif not csvPF:
      _getMain().entityActionPerformed([entityType, user, Ent.CONTACT, contactId])
    else:
      row = {'Domain': user, CONTACT_ID: contactId}
      if addCSVData:
        row.update(addCSVData)
      csvPF.WriteRow(row)
  except GDATA.badRequest as e:
    _getMain().entityActionFailedWarning([entityType, user, Ent.CONTACT, ''], str(e))
  except GDATA.forbidden:
    _getMain().entityServiceNotApplicableWarning(entityType, user)
  except GDATA.serviceNotApplicable:
    _getMain().entityUnknownWarning(entityType, user)
  if csvPF:
    csvPF.writeCSVfile('Contacts')

def _clearUpdateContacts(updateContacts):
  entityType = Ent.DOMAIN
  contactsManager = ContactsManager()
  entityList, contactQuery, queriedContacts = _getContactEntityList(1, False)
  if updateContacts:
    update_fields = contactsManager.GetContactFields()
  else:
    contactClear = {'emailClearPattern': contactQuery['emailMatchPattern'], 'emailClearType': contactQuery['emailMatchType']}
    deleteClearedContactsWithNoEmails = False
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if myarg == 'emailclearpattern':
        contactClear['emailClearPattern'] = _getMain().getREPattern(re.IGNORECASE)
      elif myarg == 'emailcleartype':
        contactClear['emailClearType'] = _getMain().getString(Cmd.OB_CONTACT_EMAIL_TYPE)
      elif myarg == 'deleteclearedcontactswithnoemails':
        deleteClearedContactsWithNoEmails = True
      else:
        _getMain().unknownArgumentExit()
    if not contactClear['emailClearPattern']:
      _getMain().missingArgumentExit('emailclearpattern')
  user, contactsObject = _getMain().getContactsObject()
  if queriedContacts:
    entityList = queryContacts(contactsObject, contactQuery)
    if entityList is None:
      return
  j = 0
  jcount = len(entityList)
  _getMain().entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, Ent.CONTACT)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  for contact in entityList:
    j += 1
    try:
      if not queriedContacts:
        contactId = normalizeContactId(contact)
        contact = _getMain().callGData(contactsObject, 'GetContact',
                            throwErrors=[GDATA.NOT_FOUND, GDATA.BAD_REQUEST, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN, GDATA.NOT_IMPLEMENTED],
                            retryErrors=[GDATA.INTERNAL_SERVER_ERROR],
                            uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId))
        fields = contactsManager.ContactToFields(contact)
      else:
        contactId = contactsManager.GetContactShortId(contact)
        fields = contactsManager.ContactToFields(contact)
        if not localContactSelects(contactsManager, contactQuery, fields):
          continue
      if updateContacts:
##### Zip
        for field, value in update_fields.items():
          fields[field] = value
        contactEntry = contactsManager.FieldsToContact(fields)
      else:
        if not clearEmailAddressMatches(contactsManager, contactClear, fields):
          continue
        if deleteClearedContactsWithNoEmails and not fields[CONTACT_EMAILS]:
          Act.Set(Act.DELETE)
          _getMain().callGData(contactsObject, 'DeleteContact',
                    throwErrors=[GDATA.NOT_FOUND, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN],
                    edit_uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId), extra_headers={'If-Match': contact.etag})
          _getMain().entityActionPerformed([entityType, user, Ent.CONTACT, contactId], j, jcount)
          continue
        contactEntry = contactsManager.FieldsToContact(fields)
      contactEntry.category = contact.category
      contactEntry.link = contact.link
      contactEntry.etag = contact.etag
      contactEntry.id = contact.id
      Act.Set(Act.UPDATE)
      _getMain().callGData(contactsObject, 'UpdateContact',
                throwErrors=[GDATA.NOT_FOUND, GDATA.BAD_REQUEST, GDATA.PRECONDITION_FAILED, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN],
                edit_uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId), updated_contact=contactEntry, extra_headers={'If-Match': contact.etag})
      _getMain().entityActionPerformed([entityType, user, Ent.CONTACT, contactId], j, jcount)
    except (GDATA.notFound, GDATA.badRequest, GDATA.preconditionFailed) as e:
      _getMain().entityActionFailedWarning([entityType, user, Ent.CONTACT, contactId], str(e), j, jcount)
    except (GDATA.forbidden, GDATA.notImplemented):
      _getMain().entityServiceNotApplicableWarning(entityType, user)
      break
    except GDATA.serviceNotApplicable:
      _getMain().entityUnknownWarning(entityType, user)
      break
  Ind.Decrement()

# gam clear contacts <ContactEntity>|<ContactSelection>
#	[clearmatchpattern <REMatchPattern>] [clearmatchtype work|home|other|<String>]
#	[deleteclearedcontactswithnoemails]
def doClearDomainContacts():
  _clearUpdateContacts(False)

# gam update contacts <ContactEntity>|<ContactSelection> <ContactAttribute>+
def doUpdateDomainContacts():
  _clearUpdateContacts(True)

# gam dedup contacts <ContactEntity>|<ContactSelection> [matchType [<Boolean>]]
def doDedupDomainContacts():
  entityType = Ent.DOMAIN
  contactsManager = ContactsManager()
  contactQuery = _initContactQueryAttributes()
  emailMatchType = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matchtype':
      emailMatchType = _getMain().getBoolean()
    else:
      _getContactQueryAttributes(contactQuery, myarg, -1, False)
  user, contactsObject = _getMain().getContactsObject()
  contacts = queryContacts(contactsObject, contactQuery)
  if contacts is None:
    return
  j = 0
  jcount = len(contacts)
  _getMain().entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, Ent.CONTACT)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  for contact in contacts:
    j += 1
    try:
      fields = contactsManager.ContactToFields(contact)
      if not localContactSelects(contactsManager, contactQuery, fields):
        continue
      if not dedupEmailAddressMatches(contactsManager, emailMatchType, fields):
        continue
      contactId = fields[CONTACT_ID]
      contactEntry = contactsManager.FieldsToContact(fields)
      contactEntry.category = contact.category
      contactEntry.link = contact.link
      contactEntry.etag = contact.etag
      contactEntry.id = contact.id
      Act.Set(Act.UPDATE)
      _getMain().callGData(contactsObject, 'UpdateContact',
                throwErrors=[GDATA.NOT_FOUND, GDATA.BAD_REQUEST, GDATA.PRECONDITION_FAILED, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN],
                edit_uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId), updated_contact=contactEntry, extra_headers={'If-Match': contact.etag})
      _getMain().entityActionPerformed([entityType, user, Ent.CONTACT, contactId], j, jcount)
    except (GDATA.notFound, GDATA.badRequest, GDATA.preconditionFailed) as e:
      _getMain().entityActionFailedWarning([entityType, user, Ent.CONTACT, contactId], str(e), j, jcount)
    except (GDATA.forbidden, GDATA.notImplemented):
      _getMain().entityServiceNotApplicableWarning(entityType, user)
      break
    except GDATA.serviceNotApplicable:
      _getMain().entityUnknownWarning(entityType, user)
      break
  Ind.Decrement()

# gam delete contacts <ContactEntity>|<ContactSelection>
def doDeleteDomainContacts():
  entityType = Ent.DOMAIN
  contactsManager = ContactsManager()
  entityList, contactQuery, queriedContacts = _getContactEntityList(-1, False)
  user, contactsObject = _getMain().getContactsObject()
  if queriedContacts:
    entityList = queryContacts(contactsObject, contactQuery)
    if entityList is None:
      return
  j = 0
  jcount = len(entityList)
  _getMain().entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, Ent.CONTACT)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  for contact in entityList:
    j += 1
    try:
      if not queriedContacts:
        contactId = normalizeContactId(contact)
        contact = _getMain().callGData(contactsObject, 'GetContact',
                            throwErrors=[GDATA.NOT_FOUND, GDATA.BAD_REQUEST, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN, GDATA.NOT_IMPLEMENTED],
                            retryErrors=[GDATA.INTERNAL_SERVER_ERROR],
                            uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId))
      else:
        contactId = contactsManager.GetContactShortId(contact)
        fields = contactsManager.ContactToFields(contact)
        if not localContactSelects(contactsManager, contactQuery, fields):
          continue
      _getMain().callGData(contactsObject, 'DeleteContact',
                throwErrors=[GDATA.NOT_FOUND, GDATA.SERVICE_NOT_APPLICABLE, GDATA.FORBIDDEN],
                edit_uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId), extra_headers={'If-Match': contact.etag})
      _getMain().entityActionPerformed([entityType, user, Ent.CONTACT, contactId], j, jcount)
    except (GDATA.notFound, GDATA.badRequest) as e:
      _getMain().entityActionFailedWarning([entityType, user, Ent.CONTACT, contactId], str(e), j, jcount)
    except (GDATA.forbidden, GDATA.notImplemented):
      _getMain().entityServiceNotApplicableWarning(entityType, user)
      break
    except GDATA.serviceNotApplicable:
      _getMain().entityUnknownWarning(entityType, user)
      break
  Ind.Decrement()

CONTACT_TIME_OBJECTS = {CONTACT_UPDATED}
CONTACT_FIELDS_WITH_CRS_NLS = {CONTACT_NOTES, CONTACT_BILLING_INFORMATION}

def _showContact(contactsManager, fields, displayFieldsList, j, jcount, FJQC):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(fields, timeObjects=CONTACT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.CONTACT, fields[CONTACT_ID]], j, jcount)
  Ind.Increment()
  for key in contactsManager.CONTACT_NAME_PROPERTY_PRINT_ORDER:
    if displayFieldsList and key not in displayFieldsList:
      continue
    if key in fields:
      if key in CONTACT_TIME_OBJECTS:
        _getMain().printKeyValueList([key, _getMain().formatLocalTime(fields[key])])
      elif key not in CONTACT_FIELDS_WITH_CRS_NLS:
        _getMain().printKeyValueList([key, fields[key]])
      else:
        _getMain().printKeyValueWithCRsNLs(key, fields[key])
  for key in contactsManager.CONTACT_ARRAY_PROPERTY_PRINT_ORDER:
    if displayFieldsList and key not in displayFieldsList:
      continue
    if key in fields:
      keymap = contactsManager.CONTACT_ARRAY_PROPERTIES[key]
      _getMain().printKeyValueList([key, None])
      Ind.Increment()
      for item in fields[key]:
        fn = item.get('label')
        if keymap['relMap']:
          if not fn:
            fn = keymap['relMap'].get(item['rel'], 'custom')
          _getMain().printKeyValueList(['type', fn])
          Ind.Increment()
        if keymap['primary']:
          _getMain().printKeyValueList(['rank', ['notprimary', 'primary'][item['primary'] == 'true']])
        value = item['value']
        if value is None:
          value = ''
        if key == CONTACT_IMS:
          _getMain().printKeyValueList(['protocol', contactsManager.IM_REL_TO_PROTOCOL_MAP.get(item['protocol'], item['protocol'])])
          _getMain().printKeyValueList([keymap['infoTitle'], value])
        elif key == CONTACT_ADDRESSES:
          _getMain().printKeyValueWithCRsNLs(keymap['infoTitle'], value)
          for org_key in contactsManager.ADDRESS_FIELD_PRINT_ORDER:
            if item[org_key]:
              _getMain().printKeyValueList([contactsManager.ADDRESS_FIELD_TO_ARGUMENT_MAP[org_key], item[org_key]])
        elif key == CONTACT_ORGANIZATIONS:
          _getMain().printKeyValueList([keymap['infoTitle'], value])
          for org_key in contactsManager.ORGANIZATION_FIELD_PRINT_ORDER:
            if item[org_key]:
              _getMain().printKeyValueList([contactsManager.ORGANIZATION_FIELD_TO_ARGUMENT_MAP[org_key], item[org_key]])
        elif key == CONTACT_USER_DEFINED_FIELDS:
          _getMain().printKeyValueList([item.get('rel') or 'None', value])
        else:
          _getMain().printKeyValueList([keymap['infoTitle'], value])
        if keymap['relMap']:
          Ind.Decrement()
      Ind.Decrement()
  Ind.Decrement()

def _getContactFieldsList(contactsManager, displayFieldsList):
  for field in _getMain()._getFieldsList():
    if field in contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP:
      displayFieldsList.append(contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP[field])
    else:
      _getMain().invalidChoiceExit(field, contactsManager.CONTACT_ARGUMENT_TO_PROPERTY_MAP, True)

# gam info contacts <ContactEntity>
#	[basic|full]
#	[fields <ContactFieldNameList>] [formatjson]
def doInfoDomainContacts():
  entityType = Ent.DOMAIN
  contactsManager = ContactsManager()
  entityList = _getMain().getEntityList(Cmd.OB_CONTACT_ENTITY)
  contactQuery = _initContactQueryAttributes()
  FJQC = _getMain().FormatJSONQuoteChar()
  displayFieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in CONTACTS_PROJECTION_CHOICE_MAP:
      contactQuery['projection'] = CONTACTS_PROJECTION_CHOICE_MAP[myarg]
    elif myarg == 'fields':
      _getContactFieldsList(contactsManager, displayFieldsList)
    else:
      FJQC.GetFormatJSON(myarg)
  user, contactsObject = _getMain().getContactsObject()
  j = 0
  jcount = len(entityList)
  if not FJQC.formatJSON:
    _getMain().entityPerformActionNumItems([entityType, user], jcount, Ent.CONTACT)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  for contact in entityList:
    j += 1
    try:
      contactId = normalizeContactId(contact)
      contact = _getMain().callGData(contactsObject, 'GetContact',
                          bailOnInternalServerError=True,
                          throwErrors=[GDATA.NOT_FOUND, GDATA.BAD_REQUEST, GDATA.SERVICE_NOT_APPLICABLE,
                                       GDATA.FORBIDDEN, GDATA.NOT_IMPLEMENTED, GDATA.INTERNAL_SERVER_ERROR],
                          retryErrors=[GDATA.INTERNAL_SERVER_ERROR],
                          uri=contactsObject.GetContactFeedUri(contact_list=user, contactId=contactId, projection=contactQuery['projection']))
      fields = contactsManager.ContactToFields(contact)
      _showContact(contactsManager, fields, displayFieldsList, j, jcount, FJQC)
    except (GDATA.notFound, GDATA.badRequest, GDATA.forbidden, GDATA.notImplemented, GDATA.internalServerError) as e:
      _getMain().entityActionFailedWarning([entityType, user, Ent.CONTACT, contactId], str(e), j, jcount)
    except GDATA.serviceNotApplicable:
      _getMain().entityUnknownWarning(entityType, user)
      break
  Ind.Decrement()

# gam print contacts [todrive <ToDriveAttribute>*] <ContactSelection>
#	[basic|full|countsonly] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]]
#	[fields <ContactFieldNameList>] [formatjson [quotechar <Character>]]
# gam show contacts <ContactSelection>
#	[basic|full|countsonly] [showdeleted] [orderby <ContactOrderByFieldName> [ascending|descending]]
#	[fields <ContactFieldNameList>] [formatjson]
def doPrintShowDomainContacts():
  entityType = Ent.DOMAIN
  entityTypeName = Ent.Singular(entityType)
  contactsManager = ContactsManager()
  csvPF = _getMain().CSVPrintFile([entityTypeName, CONTACT_ID, CONTACT_NAME], 'sortall',
                       contactsManager.CONTACT_ARRAY_PROPERTY_PRINT_ORDER) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  CSVTitle = 'Contacts'
  contactQuery = _initContactQueryAttributes()
  countsOnly = False
  displayFieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'fields':
      _getContactFieldsList(contactsManager, displayFieldsList)
    elif myarg == 'countsonly':
      countsOnly = True
      contactQuery['projection'] = CONTACTS_PROJECTION_CHOICE_MAP['basic']
      if csvPF:
        csvPF.SetTitles([entityTypeName, CSVTitle])
    elif _getContactQueryAttributes(contactQuery, myarg, 0, True):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  user, contactsObject = _getMain().getContactsObject()
  contacts = queryContacts(contactsObject, contactQuery)
  if countsOnly:
    jcount = countLocalContactSelects(contactsManager, contacts, contactQuery)
    if csvPF:
      csvPF.WriteRowTitles({entityTypeName: user, CSVTitle: jcount})
    else:
      _getMain().printEntityKVList([entityType, user], [CSVTitle, jcount])
  elif contacts is not None:
    jcount = len(contacts)
    if not csvPF:
      if not FJQC.formatJSON:
        _getMain().entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, Ent.CONTACT)
      Ind.Increment()
      j = 0
      for contact in contacts:
        j += 1
        fields = contactsManager.ContactToFields(contact)
        if not localContactSelects(contactsManager, contactQuery, fields):
          continue
        _showContact(contactsManager, fields, displayFieldsList, j, jcount, FJQC)
      Ind.Decrement()
    elif contacts:
      for contact in contacts:
        fields = contactsManager.ContactToFields(contact)
        if not localContactSelects(contactsManager, contactQuery, fields):
          continue
        contactRow = {entityTypeName: user, CONTACT_ID: fields[CONTACT_ID]}
        for key in contactsManager.CONTACT_NAME_PROPERTY_PRINT_ORDER:
          if displayFieldsList and key not in displayFieldsList:
            continue
          if key in fields:
            if key == CONTACT_UPDATED:
              contactRow[key] = _getMain().formatLocalTime(fields[key])
            elif key not in (CONTACT_NOTES, CONTACT_BILLING_INFORMATION):
              contactRow[key] = fields[key]
            else:
              contactRow[key] = _getMain().escapeCRsNLs(fields[key])
        for key in contactsManager.CONTACT_ARRAY_PROPERTY_PRINT_ORDER:
          if displayFieldsList and key not in displayFieldsList:
            continue
          if key in fields:
            keymap = contactsManager.CONTACT_ARRAY_PROPERTIES[key]
            j = 0
            contactRow[f'{key}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}count'] = len(fields[key])
            for item in fields[key]:
              j += 1
              fn = f'{key}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}'
              fnt = item.get('label')
              if fnt:
                contactRow[fn+'type'] = fnt
              elif keymap['relMap']:
                contactRow[fn+'type'] = keymap['relMap'].get(item['rel'], 'custom')
              if keymap['primary']:
                contactRow[fn+'rank'] = 'primary' if item['primary'] == 'true' else 'notprimary'
              value = item['value']
              if value is None:
                value = ''
              if key == CONTACT_IMS:
                contactRow[fn+'protocol'] = contactsManager.IM_REL_TO_PROTOCOL_MAP.get(item['protocol'], item['protocol'])
                contactRow[fn+keymap['infoTitle']] = value
              elif key == CONTACT_ADDRESSES:
                contactRow[fn+keymap['infoTitle']] = _getMain().escapeCRsNLs(value)
                for org_key in contactsManager.ADDRESS_FIELD_PRINT_ORDER:
                  if item[org_key]:
                    contactRow[fn+contactsManager.ADDRESS_FIELD_TO_ARGUMENT_MAP[org_key]] = _getMain().escapeCRsNLs(item[org_key])
              elif key == CONTACT_ORGANIZATIONS:
                contactRow[fn+keymap['infoTitle']] = value
                for org_key in contactsManager.ORGANIZATION_FIELD_PRINT_ORDER:
                  if item[org_key]:
                    contactRow[fn+contactsManager.ORGANIZATION_FIELD_TO_ARGUMENT_MAP[org_key]] = item[org_key]
              elif key == CONTACT_USER_DEFINED_FIELDS:
                contactRow[fn+'type'] = item.get('rel') or 'None'
                contactRow[fn+keymap['infoTitle']] = value
              else:
                contactRow[fn+keymap['infoTitle']] = value
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(contactRow)
        elif csvPF.CheckRowTitles(contactRow):
          csvPF.WriteRowNoFilter({entityTypeName: user, CONTACT_ID: fields[CONTACT_ID],
                                  CONTACT_NAME: fields.get(CONTACT_NAME, ''),
                                  'JSON': json.dumps(_getMain().cleanJSON(fields, timeObjects=CONTACT_TIME_OBJECTS),
                                                     ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

# Prople commands utilities
#
def normalizePeopleResourceName(resourceName):
  if resourceName.startswith('people/'):
    return resourceName
  return f'people/{resourceName}'

def normalizeContactGroupResourceName(resourceName):
  if resourceName.startswith('contactGroups/'):
    return resourceName
  return f'contactGroups/{resourceName}'

def normalizeOtherContactsResourceName(resourceName):
  if resourceName.startswith('otherContacts/'):
    return resourceName
  return f'otherContacts/{resourceName}'

PEOPLE_JSON = 'JSON'

PEOPLE_ADDRESSES = 'addresses'
PEOPLE_BIOGRAPHIES = 'biographies'
PEOPLE_BIRTHDAYS = 'birthdays'
PEOPLE_CALENDAR_URLS = 'calendarUrls'
PEOPLE_CLIENT_DATA = 'clientData'
PEOPLE_COVER_PHOTOS = 'coverPhotos'
PEOPLE_EMAIL_ADDRESSES = 'emailAddresses'
PEOPLE_EVENTS = 'events'
PEOPLE_EXTERNAL_IDS = 'externalIds'
PEOPLE_FILE_ASES = 'fileAses'
PEOPLE_GENDERS = 'genders'
PEOPLE_IM_CLIENTS = 'imClients'
PEOPLE_INTERESTS = 'interests'
PEOPLE_LOCALES = 'locales'
PEOPLE_LOCATIONS = 'locations'
PEOPLE_MEMBERSHIPS = 'memberships'
PEOPLE_METADATA = 'metadata'
PEOPLE_MISC_KEYWORDS = 'miscKeywords'
PEOPLE_MISC_KEYWORDS_BILLING_INFORMATION = PEOPLE_MISC_KEYWORDS+'.OUTLOOK_BILLING_INFORMATION'
PEOPLE_MISC_KEYWORDS_DIRECTORY_SERVER = PEOPLE_MISC_KEYWORDS+'.OUTLOOK_DIRECTORY_SERVER'
PEOPLE_MISC_KEYWORDS_JOT = PEOPLE_MISC_KEYWORDS+'.jot'
PEOPLE_MISC_KEYWORDS_MILEAGE = PEOPLE_MISC_KEYWORDS+'.OUTLOOK_MILEAGE'
PEOPLE_MISC_KEYWORDS_PRIORITY = PEOPLE_MISC_KEYWORDS+'.OUTLOOK_PRIORITY'
PEOPLE_MISC_KEYWORDS_SENSITIVITY = PEOPLE_MISC_KEYWORDS+'.OUTLOOK_SENSITIVITY'
PEOPLE_MISC_KEYWORDS_SUBJECT = PEOPLE_MISC_KEYWORDS+'.OUTLOOK_SUBJECT'
PEOPLE_NAMES = 'names'
PEOPLE_NAMES_FAMILY_NAME = PEOPLE_NAMES+'.familyName'
PEOPLE_NAMES_GIVEN_NAME = PEOPLE_NAMES+'.givenName'
PEOPLE_NAMES_HONORIFIC_PREFIX = PEOPLE_NAMES+'.honorificPrefix'
PEOPLE_NAMES_HONORIFIC_SUFFIX = PEOPLE_NAMES+'.honorificSuffix'
PEOPLE_NAMES_MIDDLE_NAME = PEOPLE_NAMES+'.middleName'
PEOPLE_NAMES_PHONETIC_FAMILY_NAME = PEOPLE_NAMES+'.phoneticFamilyName'
PEOPLE_NAMES_PHONETIC_GIVEN_NAME = PEOPLE_NAMES+'.phoneticGivenName'
PEOPLE_NAMES_PHONETIC_HONORIFIC_PREFIX = PEOPLE_NAMES+'.phoneticHonorificPrefix'
PEOPLE_NAMES_PHONETIC_HONORIFIC_SUFFIX = PEOPLE_NAMES+'.phoneticHonorificSuffix'
PEOPLE_NAMES_PHONETIC_MIDDLE_NAME = PEOPLE_NAMES+'.phoneticMiddleName'
PEOPLE_NAMES_UNSTRUCTURED_NAME = PEOPLE_NAMES+'.unstructuredName'
PEOPLE_NICKNAMES = 'nicknames'
PEOPLE_NICKNAMES_INITIALS = PEOPLE_NICKNAMES+'.INITIALS'
PEOPLE_NICKNAMES_MAIDENNAME = PEOPLE_NICKNAMES+'.MAIDEN_NAME'
PEOPLE_NICKNAMES_NICKNAME = PEOPLE_NICKNAMES+'.DEFAULT'
PEOPLE_NICKNAMES_SHORTNAME = PEOPLE_NICKNAMES+'.SHORT_NAME'
PEOPLE_OCCUPATIONS = 'occupations'
PEOPLE_ORGANIZATIONS = 'organizations'
PEOPLE_PHONE_NUMBERS = 'phoneNumbers'
PEOPLE_PHOTOS = 'photos'
PEOPLE_RELATIONS = 'relations'
PEOPLE_SIP_ADDRESSES = 'sipAddresses'
PEOPLE_SKILLS = 'skills'
PEOPLE_UPDATE_TIME = 'updateTime'
PEOPLE_URLS = 'urls'
PEOPLE_USER_DEFINED = 'userDefined'

PEOPLE_GROUPS = 'ContactGroups'
PEOPLE_GROUPS_LIST = 'ContactGroupsList'
PEOPLE_ADD_GROUPS = 'ContactAddGroups'
PEOPLE_ADD_GROUPS_LIST = 'ContactAddGroupsList'
PEOPLE_REMOVE_GROUPS = 'ContactRemoveGroups'
PEOPLE_REMOVE_GROUPS_LIST = 'ContactRemoveGroupsList'

PEOPLE_GROUP_NAME = 'name'
PEOPLE_GROUP_CLIENT_DATA = 'clientData'
#
class PeopleManager():
  PEOPLE_ARGUMENT_TO_PROPERTY_MAP = {
    'json': PEOPLE_JSON,
    'additionalname': PEOPLE_NAMES_MIDDLE_NAME,
    'address': PEOPLE_ADDRESSES,
    'addresses': PEOPLE_ADDRESSES,
    'billinginfo': PEOPLE_MISC_KEYWORDS_BILLING_INFORMATION,
    'biography': PEOPLE_BIOGRAPHIES,
    'biographies': PEOPLE_BIOGRAPHIES,
    'birthday': PEOPLE_BIRTHDAYS,
    'birthdays': PEOPLE_BIRTHDAYS,
    'calendar': PEOPLE_CALENDAR_URLS,
    'calendars': PEOPLE_CALENDAR_URLS,
    'clientdata': PEOPLE_CLIENT_DATA,
#    'coverphoto': PEOPLE_COVER_PHOTOS,
#    'coverphotos': PEOPLE_COVER_PHOTOS,
    'directoryserver': PEOPLE_MISC_KEYWORDS_DIRECTORY_SERVER,
    'email': PEOPLE_EMAIL_ADDRESSES,
    'emails': PEOPLE_EMAIL_ADDRESSES,
    'emailadresses': PEOPLE_EMAIL_ADDRESSES,
    'event': PEOPLE_EVENTS,
    'events': PEOPLE_EVENTS,
    'externalid': PEOPLE_EXTERNAL_IDS,
    'externalids': PEOPLE_EXTERNAL_IDS,
    'familyname': PEOPLE_NAMES_FAMILY_NAME,
    'fileas': PEOPLE_FILE_ASES,
    'firstname': PEOPLE_NAMES_GIVEN_NAME,
    'gender': PEOPLE_GENDERS,
    'genders': PEOPLE_GENDERS,
    'givenname': PEOPLE_NAMES_GIVEN_NAME,
    'hobby': PEOPLE_INTERESTS,
    'hobbies': PEOPLE_INTERESTS,
    'im': PEOPLE_IM_CLIENTS,
    'ims': PEOPLE_IM_CLIENTS,
    'imclients': 'imClients',
    'initials': PEOPLE_NICKNAMES_INITIALS,
    'interests': PEOPLE_INTERESTS,
    'jot': PEOPLE_MISC_KEYWORDS_JOT,
    'jots': PEOPLE_MISC_KEYWORDS_JOT,
    'language': PEOPLE_LOCALES,
    'lastname': PEOPLE_NAMES_FAMILY_NAME,
    'locale': PEOPLE_LOCALES,
    'location': PEOPLE_LOCATIONS,
    'locations': PEOPLE_LOCATIONS,
    'maidenname': PEOPLE_NICKNAMES_MAIDENNAME,
    'middlename': PEOPLE_NAMES_MIDDLE_NAME,
    'mileage': PEOPLE_MISC_KEYWORDS_MILEAGE,
    'misckeywords': PEOPLE_MISC_KEYWORDS,
    'name': PEOPLE_NAMES_UNSTRUCTURED_NAME,
    'names': PEOPLE_NAMES_UNSTRUCTURED_NAME,
    'nickname': PEOPLE_NICKNAMES_NICKNAME,
    'nicknames': PEOPLE_NICKNAMES_NICKNAME,
    'note': PEOPLE_BIOGRAPHIES,
    'notes': PEOPLE_BIOGRAPHIES,
    'occupation': PEOPLE_OCCUPATIONS,
    'occupations': PEOPLE_OCCUPATIONS,
    'organization': PEOPLE_ORGANIZATIONS,
    'organizations': PEOPLE_ORGANIZATIONS,
    'organisation': PEOPLE_ORGANIZATIONS,
    'organisations': PEOPLE_ORGANIZATIONS,
    'phone': PEOPLE_PHONE_NUMBERS,
    'phones': PEOPLE_PHONE_NUMBERS,
    'phonenumbers': PEOPLE_PHONE_NUMBERS,
#    'photo': PEOPLE_PHOTOS,
#    'photos': PEOPLE_PHOTOS,
    'prefix': PEOPLE_NAMES_HONORIFIC_PREFIX,
    'priority': PEOPLE_MISC_KEYWORDS_PRIORITY,
    'relation': PEOPLE_RELATIONS,
    'relations': PEOPLE_RELATIONS,
    'sensitivity': PEOPLE_MISC_KEYWORDS_SENSITIVITY,
    'shortname': PEOPLE_NICKNAMES_SHORTNAME,
    'sipaddress': PEOPLE_SIP_ADDRESSES,
    'sipaddresses': PEOPLE_SIP_ADDRESSES,
    'skills': PEOPLE_SKILLS,
    'subject': PEOPLE_MISC_KEYWORDS_SUBJECT,
    'suffix': PEOPLE_NAMES_HONORIFIC_SUFFIX,
    'url': PEOPLE_URLS,
    'urls': PEOPLE_URLS,
    'userdefined': PEOPLE_USER_DEFINED,
    'userdefinedfield': PEOPLE_USER_DEFINED,
    'userdefinedfields': PEOPLE_USER_DEFINED,
    'website': PEOPLE_URLS,
    'websites': PEOPLE_URLS,
    'contactgroup': PEOPLE_GROUPS,
    'contactgroups': PEOPLE_GROUPS,
    'addcontactgroup': PEOPLE_ADD_GROUPS,
    'addcontactgroups': PEOPLE_ADD_GROUPS,
    'removecontactgroup': PEOPLE_REMOVE_GROUPS,
    'removecontactgroups': PEOPLE_REMOVE_GROUPS,
    }

  _getMain().ADDRESS_ARGUMENT_TO_FIELD_MAP = {
    'formatted': 'formattedValue',
    'unstructured': 'formattedValue',
    'pobox': 'poBox',
    'street': 'streetAddress',
    'streetaddress': 'streetAddress',
    'extended': 'extendedAddress',
    'neighborhood': 'extendedAddress',
    'city': 'city',
    'locality': 'city',
    'region': 'region',
    'postalcode': 'postalCode',
    'country': 'country',
    'countrycode': 'countryCode',
    }

  JOT_TYPE_MAP = {
    'work': 'WORK',
    'home': 'HOME',
    'other': 'OTHER',
    'keyword': 'KEYWORD',
    'keywords': 'KEYWORD',
    'user': 'USER',
    }

  IM_PROTOCOLS = {
    'aim': 'aim',
    'googletalk': 'googleTalk',
    'gtalk': 'googleTalk',
    'icq': 'icq',
    'jabber': 'jabber',
    'msn': 'msn',
    'netmeeting': 'netMeeting',
    'qq': 'qq',
    'skype': 'skype',
    'xmpp': 'jabber',
    'yahoo': 'yahoo',
    }

  _getMain().ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
    'startdate': 'startDate',
    'enddate': 'endDate',
    'current': 'current',
    'phoneticname': 'phoneticName',
    'title': 'title',
    'department': 'department',
    'jobdescription': 'jobDescription',
    'symbol': 'symbol',
    'domain': 'domain',
    'location': 'location',
    }

# Fields with a key and value
  KEY_VALUE_FIELDS = {
    PEOPLE_CLIENT_DATA,
    PEOPLE_USER_DEFINED,
    }

# Fields with a type and value
  TYPE_VALUE_FIELDS = {
    PEOPLE_EVENTS: {
      'anniversary': 'anniversary',
      'other': 'other',
      },
    PEOPLE_EXTERNAL_IDS: {
      'account': 'account',
      'customer': 'customer',
      'loginid': 'loginId',
      'network': 'network',
      'organization': 'organization',
      'organisation': 'organization',
      },
    PEOPLE_RELATIONS: {
      'spouse' : 'spouse',
      'child' : 'child',
      'mother' : 'mother',
      'father' : 'father',
      'parent' : 'parent',
      'brother' : 'brother',
      'sister' : 'sister',
      'friend' : 'friend',
      'relative' : 'relative',
      'domesticpartner' : 'domesticPartner',
      'manager' : 'manager',
      'assistant' : 'assistant',
      'referredby' : 'referredBy',
      'partner' : 'partner',
      },
    PEOPLE_SIP_ADDRESSES: {
      'work': 'work',
      'home': 'home',
      'other': 'other',
      'mobile': 'mobile',
      },
    }

# Fields with a type, value and primary|notprimary; some fields may have additional arguments
  TYPE_VALUE_PNP_FIELDS = {
    PEOPLE_ADDRESSES: {
      'work': 'work',
      'home': 'home',
      'other': 'other',
      },
    PEOPLE_CALENDAR_URLS: {
      'work': 'work',
      'home': 'home',
      'freebusy': 'freeBusy',
      },
    PEOPLE_EMAIL_ADDRESSES: {
      'work': 'work',
      'home': 'home',
      'other': 'other',
      },
    PEOPLE_IM_CLIENTS: {
      'work': 'work',
      'home': 'home',
      'other': 'other',
      },
    PEOPLE_ORGANIZATIONS: {
      'school': 'school',
      'work': 'work',
      'other': 'other',
      },
    PEOPLE_PHONE_NUMBERS: {
      'work': 'work',
      'home': 'home',
      'other': 'other',
      'googlevoice': 'googleVoice',
      'fax': 'homeFax',
      'homefax': 'homeFax',
      'workfax': 'workFax',
      'otherfax': 'otherFax',
      'main': 'main',
      'company_main': 'companyMain',
      'assistant': 'assistant',
      'mobile': 'mobile',
      'workmobile': 'workMobile',
      'pager': 'pager',
      'workpager': 'workPager',
      'car': 'car',
      'radio': 'radio',
      'callback': 'callback',
      'isdn': 'isdn',
      'telex': 'telex',
      'ttytdd': 'TTY_TDD',
      },
    PEOPLE_SIP_ADDRESSES: {
      'work': 'work',
      'home': 'home',
      'mobile': 'mobile',
      'other': 'other',
      },
    PEOPLE_URLS: {
      'appinstallpage': 'appInstallPage',
      'blog': 'blog',
      'ftp': 'ftp',
      'home': 'homePage',
      'homepage': 'homePage',
      'other': 'other',
      'profile': 'profile',
      'reservations': 'reservations',
      'resume': 'resume',
      'work': 'work',
      }
    }

# Fields that allow an empty type
  EMPTY_TYPE_ALLOWED_FIELDS = {PEOPLE_ADDRESSES, PEOPLE_EMAIL_ADDRESSES, PEOPLE_PHONE_NUMBERS, PEOPLE_URLS}

# Fields with just a URL
#  URL_FIELDS = {
#    PEOPLE_COVER_PHOTOS,
#    PEOPLE_PHOTOS,
#    }

# Fields with a single value
  SINGLE_VALUE_FIELDS = {
    PEOPLE_FILE_ASES,
    }

# Fields with multiple values
  MULTI_VALUE_FIELDS = {
    PEOPLE_INTERESTS,
    PEOPLE_LOCALES,
    PEOPLE_LOCATIONS,
    PEOPLE_OCCUPATIONS,
    PEOPLE_SKILLS,
    }

  @staticmethod
  def GetPersonFields(entityType, allowAddRemove, parameters=None):
    person = {}
    contactGroupsLists = {
      PEOPLE_GROUPS_LIST: [],
      PEOPLE_ADD_GROUPS_LIST: [],
      PEOPLE_REMOVE_GROUPS_LIST: []
      }
    locations = {'primary': None}

    def CheckClearPersonField(fieldName):
      if _getMain().checkArgumentPresent(Cmd.CLEAR_NONE_ARGUMENT):
        person.pop(fieldName, None)
        person[fieldName] = []
        return True
      return False

    def GetSingleFieldEntry(fieldName):
      person.setdefault(fieldName, [])
      if not person[fieldName]:
        person[fieldName].append({})
      return person[fieldName][0]

    def InitArrayFieldEntry(choices, typeMinLen=1):
      entry = {'metadata': {'primary': False}}
      if choices is not None:
        ftype = _getMain().getChoice(choices, mapChoice=True, defaultChoice=None)
        if ftype:
          entry['type'] = ftype
        else:
          entry['type'] = _getMain().getString(Cmd.OB_STRING, minLen=typeMinLen)
      return entry

    def GetMultiFieldEntry(fieldName):
      person.setdefault(fieldName, [])
      person[fieldName].append({})
      return person[fieldName][-1]

    def getDate(entry, fieldName):
      event = _getMain().getYYYYMMDD(minLen=0, returnDateTime=True)
      if event:
        entry[fieldName] = {'year': event.year, 'month': event.month, 'day': event.day}

    def PrimaryNotPrimary(pnp, entry):
      if pnp == 'notprimary':
        entry['metadata']['primary'] = 'false'
        return True
      if pnp == 'primary':
        entry['metadata']['primary'] = 'true'
        locations['primary'] = Cmd.Location()
        return True
      return False

    def GetPrimaryNotPrimaryChoice(entry):
      pnp = _getMain().getChoice({'primary': True, 'notprimary': False}, mapChoice=True)
      entry['metadata']['primary'] = pnp
      if pnp:
        locations['primary'] = Cmd.Location()

    def AppendArrayEntryToFields(fieldName, entry, checkBlankField=None):
      person.setdefault(fieldName, [])
      if checkBlankField is None or entry[checkBlankField]:
        if entry.get('metadata', {}).get('primary', False):
          for centry in person[fieldName][1:]:
            if centry.get('metadata', {}).get('primary', False):
              Cmd.SetLocation(locations['primary']-1)
              _getMain().usageErrorExit(Msg.MULTIPLE_ITEMS_MARKED_PRIMARY.format(fieldName))
        person[fieldName].append(entry)

    while Cmd.ArgumentsRemaining():
      if parameters is not None:
        if _getCreateContactReturnOptions(parameters):
          continue
        Cmd.Backup()
      locations['fieldName'] = Cmd.Location()
      fieldName = _getMain().getChoice(PeopleManager.PEOPLE_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if '.' in fieldName:
        fieldName, subFieldName = fieldName.split('.')
      if fieldName == PEOPLE_ADDRESSES:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_PNP_FIELDS[fieldName], typeMinLen=0)
        while Cmd.ArgumentsRemaining():
          argument = _getMain().getArgument()
          if argument in PeopleManager.ADDRESS_ARGUMENT_TO_FIELD_MAP:
            subFieldName = PeopleManager.ADDRESS_ARGUMENT_TO_FIELD_MAP[argument]
            value = _getMain().getString(Cmd.OB_STRING, minLen=0)
            if value: ### Delete?
              entry[subFieldName] = value.replace('\\n', '\n')
          elif PrimaryNotPrimary(argument, entry):
            break
          else:
            _getMain().unknownArgumentExit()
        AppendArrayEntryToFields(fieldName, entry, None)
      elif fieldName == PEOPLE_BIRTHDAYS:
        entry = GetSingleFieldEntry(fieldName)
        getDate(entry, 'date')
      elif fieldName == PEOPLE_BIOGRAPHIES:
        entry = GetSingleFieldEntry(fieldName)
        text, _, html = _getMain().getStringWithCRsNLsOrFile()
        entry['value' ] = text
        entry['contentType'] = ['TEXT_PLAIN', 'TEXT_HTML'][html]
      elif fieldName == PEOPLE_GENDERS:
        entry = GetSingleFieldEntry(fieldName)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
      elif fieldName == PEOPLE_MISC_KEYWORDS:
        entry = GetMultiFieldEntry(fieldName)
        if subFieldName == 'jot':
          subFieldName = _getMain().getChoice(PeopleManager.JOT_TYPE_MAP, mapChoice=True)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        entry['type'] = subFieldName
      elif fieldName == PEOPLE_NAMES:
        entry = GetSingleFieldEntry(fieldName)
        entry[subFieldName] = _getMain().getString(Cmd.OB_STRING, minLen=0)
      elif fieldName == PEOPLE_NICKNAMES:
        entry = GetMultiFieldEntry(fieldName)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        entry['type'] = subFieldName
      elif fieldName == PEOPLE_ORGANIZATIONS:
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_PNP_FIELDS[fieldName])
        entry['name'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        while Cmd.ArgumentsRemaining():
          argument = _getMain().getArgument()
          if argument in PeopleManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP:
            subFieldName = PeopleManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP[argument]
            if subFieldName == 'current':
              entry[subFieldName] = _getMain().getBoolean()
            elif subFieldName in {'startDate', 'endDate'}:
              getDate(entry, subFieldName)
            else:
              value = _getMain().getString(Cmd.OB_STRING, minLen=0)
              if value: ### Delete?
                entry[subFieldName] = value
          elif PrimaryNotPrimary(argument, entry):
            break
          else:
            _getMain().unknownArgumentExit()
        AppendArrayEntryToFields(fieldName, entry, None)
      elif fieldName in PeopleManager.KEY_VALUE_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(None)
        entry['key'] = _getMain().getString(Cmd.OB_STRING, minLen=1)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        AppendArrayEntryToFields(fieldName, entry, 'value')
      elif fieldName in PeopleManager.TYPE_VALUE_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_FIELDS[fieldName])
        if fieldName == PEOPLE_EVENTS:
          checkBlankField = 'date'
          getDate(entry, checkBlankField)
        elif fieldName == PEOPLE_RELATIONS:
          checkBlankField = 'type'
          entry['person'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        else:
          checkBlankField = 'value'
          entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        AppendArrayEntryToFields(fieldName, entry, checkBlankField)
      elif fieldName in PeopleManager.TYPE_VALUE_PNP_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_PNP_FIELDS[fieldName],
                                    typeMinLen=0 if fieldName in PeopleManager.EMPTY_TYPE_ALLOWED_FIELDS else 1)
        if fieldName == PEOPLE_IM_CLIENTS:
          checkBlankField = None
          entry['protocol'] = _getMain().getChoice(PeopleManager.IM_PROTOCOLS, mapChoice=True)
          entry['username'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        elif fieldName == PEOPLE_EMAIL_ADDRESSES:
          checkBlankField = 'value'
          entry[checkBlankField] = _getMain().getString(Cmd.OB_STRING, minLen=0)
          if _getMain().checkArgumentPresent(['displayname']):
            entry['displayName'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        elif fieldName == PEOPLE_CALENDAR_URLS:
          checkBlankField = 'url'
          entry[checkBlankField] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        else:
          checkBlankField = 'value'
          entry[checkBlankField] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendArrayEntryToFields(fieldName, entry, checkBlankField)
      elif fieldName in PeopleManager.SINGLE_VALUE_FIELDS:
        entry = GetSingleFieldEntry(fieldName)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
      elif fieldName in PeopleManager.MULTI_VALUE_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(None)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        AppendArrayEntryToFields(fieldName, entry, 'value')
#      elif fieldName in PeopleManager.URL_FIELDS:
#        if CheckClearPersonField(fieldName):
#          continue
#        entry = InitArrayFieldEntry(None)
#        entry['url'] = getString(Cmd.OB_STRING, minLen=0)
#        entry['default'] = False
#        AppendArrayEntryToFields(fieldName, entry, 'url')
      elif fieldName == PEOPLE_GROUPS:
        if entityType != Ent.USER:
          Cmd.Backup()
          _getMain().unknownArgumentExit()
        contactGroupsLists[PEOPLE_GROUPS_LIST].append(_getMain().getString(Cmd.OB_STRING))
      elif fieldName == PEOPLE_ADD_GROUPS:
        if not allowAddRemove:
          _getMain().unknownArgumentExit()
        if entityType != Ent.USER:
          Cmd.Backup()
          _getMain().unknownArgumentExit()
        contactGroupsLists[PEOPLE_ADD_GROUPS_LIST].append(_getMain().getString(Cmd.OB_STRING))
      elif fieldName == PEOPLE_REMOVE_GROUPS:
        if not allowAddRemove:
          _getMain().unknownArgumentExit()
        if entityType != Ent.USER:
          Cmd.Backup()
          _getMain().unknownArgumentExit()
        contactGroupsLists[PEOPLE_REMOVE_GROUPS_LIST].append(_getMain().getString(Cmd.OB_STRING))
      elif fieldName == PEOPLE_JSON:
        jsonData = _getMain().getJSON(['resourceName', 'etag', 'metadata', PEOPLE_COVER_PHOTOS, PEOPLE_PHOTOS, PEOPLE_UPDATE_TIME])
        for membership in jsonData.pop('memberships', []):
          contactGroupName = membership.get('contactGroupMembership', {}).get('contactGroupName', '')
          if contactGroupName:
            contactGroupsLists[PEOPLE_GROUPS_LIST].append(contactGroupName)
        newClientData = []
        for clientData in jsonData.pop('clientData', []):
          if clientData['key'] not in {'ContactId', 'CtsContactHash'}:
            newClientData.append({'key': clientData['key'], 'value': clientData['value']})
        if newClientData:
          person.setdefault(PEOPLE_CLIENT_DATA, [])
          person[PEOPLE_CLIENT_DATA].extend(newClientData)
        person.update(jsonData)
    return (person, set(person.keys()), contactGroupsLists)

  PEOPLE_GROUP_ARGUMENT_TO_PROPERTY_MAP = {
    'json': PEOPLE_JSON,
    'name': PEOPLE_GROUP_NAME,
    'clientdata': PEOPLE_GROUP_CLIENT_DATA,
    }

  @staticmethod
  def AddContactGroupsToContact(contactEntry, contactGroupsList):
    contactEntry[PEOPLE_MEMBERSHIPS] = []
    for groupId in contactGroupsList:
      if groupId != 'clear':
        contactEntry[PEOPLE_MEMBERSHIPS].append({'contactGroupMembership': {'contactGroupResourceName': groupId}})
      else:
        contactEntry[PEOPLE_MEMBERSHIPS] = []

  @staticmethod
  def AddFilteredContactGroupsToContact(contactEntry, contactGroupsList, contactRemoveGroupsList):
    contactEntry[PEOPLE_MEMBERSHIPS] = []
    for groupId in contactGroupsList:
      if groupId not in contactRemoveGroupsList:
        contactEntry[PEOPLE_MEMBERSHIPS].append({'contactGroupMembership': {'contactGroupResourceName': groupId}})

  @staticmethod
  def AddAdditionalContactGroupsToContact(contactEntry, contactGroupsList):
    for groupId in contactGroupsList:
      contactEntry[PEOPLE_MEMBERSHIPS].append({'contactGroupMembership': {'contactGroupResourceName': groupId}})

  @staticmethod
  def GetContactGroupFields(parameters=None):
    contactGroup = {}
    while Cmd.ArgumentsRemaining():
      if parameters is not None:
        if _getCreateContactReturnOptions(parameters):
          continue
        Cmd.Backup()
      fieldName = _getMain().getChoice(PeopleManager.PEOPLE_GROUP_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if fieldName == PEOPLE_GROUP_NAME:
        contactGroup[PEOPLE_GROUP_NAME] = _getMain().getString(Cmd.OB_STRING)
      elif fieldName == PEOPLE_GROUP_CLIENT_DATA:
        entry = {}
        entry['key'] = _getMain().getString(Cmd.OB_STRING, minLen=1)
        entry['value'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
        if entry['value']:
          contactGroup.setdefault(fieldName, [])
          contactGroup[fieldName].append(entry)
      elif fieldName == PEOPLE_JSON:
        jsonData = _getMain().getJSON(['resourceName', 'etag', 'metadata', 'formattedName', 'memberResourceNames',  'memberCount'])
        if jsonData.get('groupType', '') != 'SYSTEM_CONTACT_GROUP':
          contactGroup[PEOPLE_GROUP_NAME] = jsonData['name']
    return (contactGroup, ','.join(contactGroup.keys()))

PEOPLE_DIRECTORY_SOURCES_CHOICE_MAP = {
  'contact': 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT',
  'contacts': 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT',
  'domaincontact': 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT',
  'comaincontacts': 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT',
  'profile': 'DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE',
  'profiles': 'DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE'
  }

PEOPLE_READ_SOURCES_CHOICE_MAP = {
  'contact': 'READ_SOURCE_TYPE_CONTACT',
  'contacts': 'READ_SOURCE_TYPE_CONTACT',
  'domaincontact': 'READ_SOURCE_TYPE_DOMAIN_CONTACT',
  'domaincontacts': 'READ_SOURCE_TYPE_DOMAIN_CONTACT',
  'profile': 'READ_SOURCE_TYPE_PROFILE',
  'profiles': 'READ_SOURCE_TYPE_PROFILE'
  }

PEOPLE_DIRECTORY_MERGE_SOURCES_CHOICE_MAP = {
  'contact': 'DIRECTORY_MERGE_SOURCE_TYPE_CONTACT',
  'contacts': 'DIRECTORY_MERGE_SOURCE_TYPE_CONTACT',
  }

