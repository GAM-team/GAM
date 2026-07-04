"""GAM domain contacts management."""

from gamlib import msgs as Msg
from gam.var import Cmd, Ent
from gam.util.args import (
    checkArgumentPresent,
    getAddCSVData,
    getArgument,
    getBoolean,
    getChoice,
    getJSON,
    getString,
    getStringWithCRsNLsOrFile,
    getYYYYMMDD,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.errors import unknownArgumentExit, usageErrorExit
from gam.util.output import systemErrorExit
from gam.constants import USAGE_ERROR_RC



def _getCreateContactReturnOptions(parameters):
  myarg = getArgument()
  if myarg == 'returnidonly':
    parameters['returnIdOnly'] = True
  elif myarg == 'csv':
    parameters['csvPF'] = CSVPrintFile(parameters['titles'], 'sortall')
  elif parameters['csvPF'] and myarg == 'todrive':
    parameters['csvPF'].GetTodriveParameters()
  elif parameters['csvPF'] and myarg == 'addcsvdata':
    getAddCSVData(parameters['addCSVData'])
  else:
    return False
  return True


# Domain Shared Contacts — REMOVED (GData Contacts API v3 deprecated)
LAST_SUPPORTED_VERSION = '7.46.07'

def _deprecatedDomainContactCommand():
  systemErrorExit(
    USAGE_ERROR_RC,
    f'GAM no longer supports the legacy Domain Shared Contacts (GData Contacts v3) API '
    f'and this command. If you must use this API you can install a copy of GAM '
    f'{LAST_SUPPORTED_VERSION} which is the last version to support this command.'
  )

def doCreateDomainContact():
  _deprecatedDomainContactCommand()

def doClearDomainContacts():
  _deprecatedDomainContactCommand()

def doUpdateDomainContacts():
  _deprecatedDomainContactCommand()

def doDedupDomainContacts():
  _deprecatedDomainContactCommand()

def doDeleteDomainContacts():
  _deprecatedDomainContactCommand()

def doInfoDomainContacts():
  _deprecatedDomainContactCommand()

def doPrintShowDomainContacts():
  _deprecatedDomainContactCommand()


# Contact query parameters (shared with people.py)
CONTACTS_PROJECTION_CHOICE_MAP = {'basic': 'thin', 'thin': 'thin', 'full': 'full'}
CONTACTS_ORDERBY_CHOICE_MAP = {'lastmodified': 'lastmodified'}

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
class PeopleManager:
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

  ADDRESS_ARGUMENT_TO_FIELD_MAP = {
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

  ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
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
      if checkArgumentPresent(Cmd.CLEAR_NONE_ARGUMENT):
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
        ftype = getChoice(choices, mapChoice=True, defaultChoice=None)
        if ftype:
          entry['type'] = ftype
        else:
          entry['type'] = getString(Cmd.OB_STRING, minLen=typeMinLen)
      return entry

    def GetMultiFieldEntry(fieldName):
      person.setdefault(fieldName, [])
      person[fieldName].append({})
      return person[fieldName][-1]

    def getDate(entry, fieldName):
      event = getYYYYMMDD(minLen=0, returnDateTime=True)
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
      pnp = getChoice({'primary': True, 'notprimary': False}, mapChoice=True)
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
              usageErrorExit(Msg.MULTIPLE_ITEMS_MARKED_PRIMARY.format(fieldName))
        person[fieldName].append(entry)

    while Cmd.ArgumentsRemaining():
      if parameters is not None:
        if _getCreateContactReturnOptions(parameters):
          continue
        Cmd.Backup()
      locations['fieldName'] = Cmd.Location()
      fieldName = getChoice(PeopleManager.PEOPLE_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if '.' in fieldName:
        fieldName, subFieldName = fieldName.split('.')
      if fieldName == PEOPLE_ADDRESSES:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_PNP_FIELDS[fieldName], typeMinLen=0)
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument in PeopleManager.ADDRESS_ARGUMENT_TO_FIELD_MAP:
            subFieldName = PeopleManager.ADDRESS_ARGUMENT_TO_FIELD_MAP[argument]
            value = getString(Cmd.OB_STRING, minLen=0)
            if value: ### Delete?
              entry[subFieldName] = value.replace('\\n', '\n')
          elif PrimaryNotPrimary(argument, entry):
            break
          else:
            unknownArgumentExit()
        AppendArrayEntryToFields(fieldName, entry, None)
      elif fieldName == PEOPLE_BIRTHDAYS:
        entry = GetSingleFieldEntry(fieldName)
        getDate(entry, 'date')
      elif fieldName == PEOPLE_BIOGRAPHIES:
        entry = GetSingleFieldEntry(fieldName)
        text, _, html = getStringWithCRsNLsOrFile()
        entry['value' ] = text
        entry['contentType'] = ['TEXT_PLAIN', 'TEXT_HTML'][html]
      elif fieldName == PEOPLE_GENDERS:
        entry = GetSingleFieldEntry(fieldName)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
      elif fieldName == PEOPLE_MISC_KEYWORDS:
        entry = GetMultiFieldEntry(fieldName)
        if subFieldName == 'jot':
          subFieldName = getChoice(PeopleManager.JOT_TYPE_MAP, mapChoice=True)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        entry['type'] = subFieldName
      elif fieldName == PEOPLE_NAMES:
        entry = GetSingleFieldEntry(fieldName)
        entry[subFieldName] = getString(Cmd.OB_STRING, minLen=0)
      elif fieldName == PEOPLE_NICKNAMES:
        entry = GetMultiFieldEntry(fieldName)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        entry['type'] = subFieldName
      elif fieldName == PEOPLE_ORGANIZATIONS:
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_PNP_FIELDS[fieldName])
        entry['name'] = getString(Cmd.OB_STRING, minLen=0)
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument in PeopleManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP:
            subFieldName = PeopleManager.ORGANIZATION_ARGUMENT_TO_FIELD_MAP[argument]
            if subFieldName == 'current':
              entry[subFieldName] = getBoolean()
            elif subFieldName in {'startDate', 'endDate'}:
              getDate(entry, subFieldName)
            else:
              value = getString(Cmd.OB_STRING, minLen=0)
              if value: ### Delete?
                entry[subFieldName] = value
          elif PrimaryNotPrimary(argument, entry):
            break
          else:
            unknownArgumentExit()
        AppendArrayEntryToFields(fieldName, entry, None)
      elif fieldName in PeopleManager.KEY_VALUE_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(None)
        entry['key'] = getString(Cmd.OB_STRING, minLen=1)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
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
          entry['person'] = getString(Cmd.OB_STRING, minLen=0)
        else:
          checkBlankField = 'value'
          entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        AppendArrayEntryToFields(fieldName, entry, checkBlankField)
      elif fieldName in PeopleManager.TYPE_VALUE_PNP_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(PeopleManager.TYPE_VALUE_PNP_FIELDS[fieldName],
                                    typeMinLen=0 if fieldName in PeopleManager.EMPTY_TYPE_ALLOWED_FIELDS else 1)
        if fieldName == PEOPLE_IM_CLIENTS:
          checkBlankField = None
          entry['protocol'] = getChoice(PeopleManager.IM_PROTOCOLS, mapChoice=True)
          entry['username'] = getString(Cmd.OB_STRING, minLen=0)
        elif fieldName == PEOPLE_EMAIL_ADDRESSES:
          checkBlankField = 'value'
          entry[checkBlankField] = getString(Cmd.OB_STRING, minLen=0)
          if checkArgumentPresent(['displayname']):
            entry['displayName'] = getString(Cmd.OB_STRING, minLen=0)
        elif fieldName == PEOPLE_CALENDAR_URLS:
          checkBlankField = 'url'
          entry[checkBlankField] = getString(Cmd.OB_STRING, minLen=0)
        else:
          checkBlankField = 'value'
          entry[checkBlankField] = getString(Cmd.OB_STRING, minLen=0)
        GetPrimaryNotPrimaryChoice(entry)
        AppendArrayEntryToFields(fieldName, entry, checkBlankField)
      elif fieldName in PeopleManager.SINGLE_VALUE_FIELDS:
        entry = GetSingleFieldEntry(fieldName)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
      elif fieldName in PeopleManager.MULTI_VALUE_FIELDS:
        if CheckClearPersonField(fieldName):
          continue
        entry = InitArrayFieldEntry(None)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
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
          unknownArgumentExit()
        contactGroupsLists[PEOPLE_GROUPS_LIST].append(getString(Cmd.OB_STRING))
      elif fieldName == PEOPLE_ADD_GROUPS:
        if not allowAddRemove:
          unknownArgumentExit()
        if entityType != Ent.USER:
          Cmd.Backup()
          unknownArgumentExit()
        contactGroupsLists[PEOPLE_ADD_GROUPS_LIST].append(getString(Cmd.OB_STRING))
      elif fieldName == PEOPLE_REMOVE_GROUPS:
        if not allowAddRemove:
          unknownArgumentExit()
        if entityType != Ent.USER:
          Cmd.Backup()
          unknownArgumentExit()
        contactGroupsLists[PEOPLE_REMOVE_GROUPS_LIST].append(getString(Cmd.OB_STRING))
      elif fieldName == PEOPLE_JSON:
        jsonData = getJSON(['resourceName', 'etag', 'metadata', PEOPLE_COVER_PHOTOS, PEOPLE_PHOTOS, PEOPLE_UPDATE_TIME])
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
      fieldName = getChoice(PeopleManager.PEOPLE_GROUP_ARGUMENT_TO_PROPERTY_MAP, mapChoice=True)
      if fieldName == PEOPLE_GROUP_NAME:
        contactGroup[PEOPLE_GROUP_NAME] = getString(Cmd.OB_STRING)
      elif fieldName == PEOPLE_GROUP_CLIENT_DATA:
        entry = {}
        entry['key'] = getString(Cmd.OB_STRING, minLen=1)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        if entry['value']:
          contactGroup.setdefault(fieldName, [])
          contactGroup[fieldName].append(entry)
      elif fieldName == PEOPLE_JSON:
        jsonData = getJSON(['resourceName', 'etag', 'metadata', 'formattedName', 'memberResourceNames',  'memberCount'])
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

