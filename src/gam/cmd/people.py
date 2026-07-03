"""GAM People API contacts management."""

import re
import json

from gam.cmd.contacts import (
    PEOPLE_ADDRESSES,
    PEOPLE_BIOGRAPHIES,
    PEOPLE_BIRTHDAYS,
    PEOPLE_CALENDAR_URLS,
    PEOPLE_CLIENT_DATA,
    PEOPLE_COVER_PHOTOS,
    PEOPLE_DIRECTORY_MERGE_SOURCES_CHOICE_MAP,
    PEOPLE_DIRECTORY_SOURCES_CHOICE_MAP,
    PEOPLE_EMAIL_ADDRESSES,
    PEOPLE_EVENTS,
    PEOPLE_EXTERNAL_IDS,
    PEOPLE_FILE_ASES,
    PEOPLE_GENDERS,
    PEOPLE_GROUPS_LIST,
    PEOPLE_GROUP_NAME,
    PEOPLE_IM_CLIENTS,
    PEOPLE_INTERESTS,
    PEOPLE_LOCALES,
    PEOPLE_LOCATIONS,
    PEOPLE_MEMBERSHIPS,
    PEOPLE_METADATA,
    PEOPLE_MISC_KEYWORDS,
    PEOPLE_NAMES,
    PEOPLE_NICKNAMES,
    PEOPLE_OCCUPATIONS,
    PEOPLE_ORGANIZATIONS,
    PEOPLE_PHONE_NUMBERS,
    PEOPLE_PHOTOS,
    PEOPLE_READ_SOURCES_CHOICE_MAP,
    PEOPLE_RELATIONS,
    PEOPLE_REMOVE_GROUPS_LIST,
    PEOPLE_SIP_ADDRESSES,
    PEOPLE_SKILLS,
    PEOPLE_UPDATE_TIME,
    PEOPLE_URLS,
    PEOPLE_USER_DEFINED,
)
import base64
import os
import time

import google.auth
import google.auth.exceptions

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg

from gam.cmd.contacts import (
    CONTACTS_ORDERBY_CHOICE_MAP, CONTACTS_PROJECTION_CHOICE_MAP,
    PEOPLE_ADDRESSES, PEOPLE_ADD_GROUPS_LIST, PEOPLE_BIOGRAPHIES,
    PEOPLE_BIRTHDAYS, PEOPLE_CALENDAR_URLS, PEOPLE_CLIENT_DATA,
    PEOPLE_COVER_PHOTOS, PEOPLE_DIRECTORY_MERGE_SOURCES_CHOICE_MAP,
    PEOPLE_DIRECTORY_SOURCES_CHOICE_MAP, PEOPLE_EMAIL_ADDRESSES,
    PEOPLE_EVENTS, PEOPLE_EXTERNAL_IDS, PEOPLE_FILE_ASES,
    PEOPLE_GENDERS, PEOPLE_GROUPS_LIST, PEOPLE_GROUP_NAME,
    PEOPLE_IM_CLIENTS, PEOPLE_INTERESTS, PEOPLE_LOCALES,
    PEOPLE_LOCATIONS, PEOPLE_MEMBERSHIPS, PEOPLE_METADATA,
    PEOPLE_MISC_KEYWORDS, PEOPLE_NAMES, PEOPLE_NICKNAMES,
    PEOPLE_OCCUPATIONS, PEOPLE_ORGANIZATIONS, PEOPLE_PHONE_NUMBERS,
    PEOPLE_PHOTOS, PEOPLE_READ_SOURCES_CHOICE_MAP, PEOPLE_RELATIONS,
    PEOPLE_REMOVE_GROUPS_LIST, PEOPLE_SIP_ADDRESSES, PEOPLE_SKILLS,
    PEOPLE_UPDATE_TIME, PEOPLE_URLS, PEOPLE_USER_DEFINED,
)
from gam.util.access import entityUnknownWarning
from gam.util.api import (
    buildGAPIObject,
    buildGAPIServiceObject,
    callGAPI,
    callGAPIpages,
    getHttpObj,
    writeGotMessage,
)
from gam.util.args import (
    SORTORDER_CHOICE_MAP,
    UID_PATTERN,
    UTF8,
    checkForExtraneousArguments,
    formatLocalTime,
    getArgument,
    getBoolean,
    getChoice,
    getOrderBySortOrder,
    getREPattern,
    getString,
    getStringReturnInList,
    getYYYYMMDD,
    splitEmailAddress,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    addFieldToFieldsList,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityDoesNotHaveItemWarning,
    entityModifierNewValueActionPerformed,
    entityPerformActionModifierNumItems,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItemForWhom,
    printLine,
    userPeopleServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument, getEntityList
from gam.util.errors import deprecatedArgument, invalidChoiceExit, missingArgumentExit, unknownArgumentExit
from gam.util.fileio import UNKNOWN, setFilePath, writeFileReturnError
from gam.util.output import setSysExitRC, writeStdout
from gam.constants import NO_ENTITIES_FOUND_RC

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _initPeopleContactQueryAttributes(printShowCmd):
  return {'query': None, 'updateTime': None,
          'contactGroupSelect': None, 'contactGroupFilter': None, 'group': None, 'dropMemberships': False,
          'mainContacts': True, 'otherContacts': printShowCmd, 'emailMatchPattern': None, 'emailMatchType': None}

def _getPeopleContactQueryAttributes(contactQuery, myarg, entityType, unknownAction, printShowCmd):
  if myarg == 'query':
    contactQuery['query'] = getString(Cmd.OB_QUERY)
  elif myarg in {'contactgroup', 'selectcontactgroup'}:
    if entityType == Ent.USER:
      contactQuery['contactGroupSelect'] = getString(Cmd.OB_CONTACT_GROUP_ITEM)
      contactQuery['contactGroupFilter'] = None
      contactQuery['mainContacts'] = True
      contactQuery['otherContacts'] = False
    else:
      unknownArgumentExit()
  elif myarg == 'emailmatchpattern':
    contactQuery['emailMatchPattern'] = getREPattern(re.IGNORECASE)
  elif myarg == 'emailmatchtype':
    contactQuery['emailMatchType'] = getString(Cmd.OB_CONTACT_EMAIL_TYPE)
  elif myarg == 'updatedmin':
    deprecatedArgument(myarg)
    getYYYYMMDD()
  elif myarg == 'endquery':
    return False
  elif not printShowCmd:
    if unknownAction < 0:
      unknownArgumentExit()
    if unknownAction > 0:
      Cmd.Backup()
    return False
  elif myarg == 'filtercontactgroup':
    if entityType == Ent.USER:
      contactQuery['contactGroupFilter'] = getString(Cmd.OB_CONTACT_GROUP_ITEM)
      contactQuery['contactGroupSelect'] = None
      contactQuery['mainContacts'] = True
      contactQuery['otherContacts'] = False
    else:
      unknownArgumentExit()
  elif myarg in {'maincontacts', 'selectmaincontacts'}:
    if entityType == Ent.USER:
      contactQuery['contactGroupSelect'] = None
      contactQuery['contactGroupFilter'] = None
      contactQuery['mainContacts'] = True
      contactQuery['otherContacts'] = False
    else:
      unknownArgumentExit()
  elif myarg in {'othercontacts', 'selectothercontacts'}:
    if entityType == Ent.USER:
      contactQuery['contactGroupSelect'] = None
      contactQuery['contactGroupFilter'] = None
      contactQuery['mainContacts'] = False
      contactQuery['otherContacts'] = True
    else:
      unknownArgumentExit()
  elif myarg == 'orderby':
    getOrderBySortOrder(CONTACTS_ORDERBY_CHOICE_MAP, 'ascending', False)
    deprecatedArgument(myarg)
  elif myarg in CONTACTS_PROJECTION_CHOICE_MAP:
    deprecatedArgument(myarg)
  elif myarg == 'showdeleted':
    deprecatedArgument(myarg)
  else:
    if unknownAction < 0:
      unknownArgumentExit()
    if unknownAction > 0:
      Cmd.Backup()
    return False
  return True

PEOPLE_CONTACT_SELECT_ARGUMENTS = {
  'query', 'contactgroup', 'selectcontactgroup',
  'maincontacts', 'selectmaincontacts',
  'othercontacts', 'selectothercontacts',
  'emailmatchpattern', 'emailmatchtype',
  }
PEOPLE_CONTACT_DEPRECATED_SELECT_ARGUMENTS = {
  'orderby', 'basic', 'thin', 'full', 'showdeleted',
  }

def _getPeopleContactEntityList(entityType, unknownAction, noEntityArguments=None):
  contactQuery = _initPeopleContactQueryAttributes(False)
  if noEntityArguments is not None and (not Cmd.ArgumentsRemaining() or Cmd.PeekArgumentPresent(noEntityArguments)):
    # <PeopleResourceNameEntity>|<PeopleUserContactSelection> are optional in dedup|replacedomain contacts
    entityList = None
    queriedContacts = True
  elif Cmd.PeekArgumentPresent(PEOPLE_CONTACT_SELECT_ARGUMENTS.union(PEOPLE_CONTACT_DEPRECATED_SELECT_ARGUMENTS)):
    entityList = None
    queriedContacts = True
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if not _getPeopleContactQueryAttributes(contactQuery, myarg, entityType, unknownAction, False):
        break
  else:
    entityList = getEntityList(Cmd.OB_CONTACT_ENTITY)
    queriedContacts = False
    if unknownAction < 0:
      checkForExtraneousArguments()
  return (entityList, entityList if isinstance(entityList, dict) else None, contactQuery, queriedContacts)

def _initPeopleOtherContactQueryAttributes():
  return {'query': None,
          'otherContacts': True, 'emailMatchPattern': None, 'emailMatchType': None}

def _getPeopleOtherContactQueryAttributes(contactQuery, myarg, unknownAction):
  if myarg == 'query':
    contactQuery['query'] = getString(Cmd.OB_QUERY)
  elif myarg == 'emailmatchpattern':
    contactQuery['emailMatchPattern'] = getREPattern(re.IGNORECASE)
  elif myarg == 'emailmatchtype':
    contactQuery['emailMatchType'] = getString(Cmd.OB_CONTACT_EMAIL_TYPE)
  elif myarg == 'endquery':
    return False
  else:
    if unknownAction < 0:
      unknownArgumentExit()
    if unknownAction > 0:
      Cmd.Backup()
    return False
  return True

PEOPLE_OTHERCONTACT_SELECT_ARGUMENTS = {'query', 'emailmatchpattern', 'emailmatchtype'}

def _getPeopleOtherContactEntityList(unknownAction):
  contactQuery = _initPeopleOtherContactQueryAttributes()
  if Cmd.PeekArgumentPresent(PEOPLE_OTHERCONTACT_SELECT_ARGUMENTS):
    entityList = None
    queriedContacts = True
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if not _getPeopleOtherContactQueryAttributes(contactQuery, myarg, unknownAction):
        break
  else:
    entityList = getEntityList(Cmd.OB_CONTACT_ENTITY)
    queriedContacts = False
    if unknownAction < 0:
      checkForExtraneousArguments()
  return (entityList, entityList if isinstance(entityList, dict) else None, contactQuery, queriedContacts)

def _getPeopleOtherContacts(people, entityType, user, i=0, count=0):
  try:
    printGettingAllEntityItemsForWhom(Ent.OTHER_CONTACT, user, i, count)
    results = callGAPIpages(people.otherContacts(), 'list', 'otherContacts',
                            pageMessage=getPageMessageForWhom(),
                            throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            pageSize=1000,
                            readMask='emailAddresses', fields='nextPageToken,otherContacts(etag,resourceName,emailAddresses(value,type))')
    otherContacts = {}
    for contact in results:
      resourceName = contact.pop('resourceName')
      otherContacts[resourceName] = contact
    return otherContacts
  except GAPI.permissionDenied as e:
    ClientAPIAccessDeniedExit(str(e))
  except (GAPI.serviceNotAvailable, GAPI.forbidden):
    entityUnknownWarning(entityType, user, i, count)
  return None

def queryPeopleContacts(people, contactQuery, fields, sortOrder, entityType, user, i=0, count=0):
  sources = [PEOPLE_READ_SOURCES_CHOICE_MAP['domaincontact' if entityType == Ent.DOMAIN else 'contact']]
  printGettingAllEntityItemsForWhom(Ent.PEOPLE_CONTACT, user, i, count, query=contactQuery['query'])
  pageMessage = getPageMessageForWhom()
  try:
# Contact group not selected
    if not contactQuery['contactGroupSelect']:
      if not contactQuery['query']:
        results = callGAPIpages(people.people().connections(), 'list', 'connections',
                                pageMessage=pageMessage,
                                throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                pageSize=GC.Values[GC.PEOPLE_MAX_RESULTS],
                                resourceName='people/me', sources=sources, personFields=fields,
                                sortOrder=sortOrder, fields='nextPageToken,connections')
        if contactQuery['contactGroupFilter']:
          entityList = []
          for person in results:
            for membership in person.get(PEOPLE_MEMBERSHIPS, []):
              if membership.get('contactGroupMembership', {}).get('contactGroupResourceName', '') == contactQuery['group']:
                if contactQuery['dropMemberships']:
                  person.pop(PEOPLE_MEMBERSHIPS)
                entityList.append(person)
                break
        else:
          entityList = results
      else:
        results = callGAPI(people.people(), 'searchContacts',
                           throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                           sources=sources, readMask=fields, query=contactQuery['query'])
        entityList = [person['person'] for person in results.get('results', [])]
      totalItems = len(entityList)
# Contact group selected
    else:
      totalItems = callGAPI(people.contactGroups(), 'get',
                            throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                            resourceName=contactQuery['group'], groupFields='memberCount').get('memberCount', 0)
      entityList = []
      if totalItems > 0:
        results = callGAPI(people.contactGroups(), 'get',
                           throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                           resourceName=contactQuery['group'], maxMembers=totalItems, groupFields='name')
        for resourceName in results.get('memberResourceNames', []):
          result = callGAPI(people.people(), 'get',
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            resourceName=resourceName, sources=sources, personFields=fields)

          entityList.append(result)
    if pageMessage and (contactQuery['contactGroupSelect'] or contactQuery['contactGroupFilter'] or contactQuery['query']):
      showMessage = pageMessage.replace(TOTAL_ITEMS_MARKER, str(totalItems))
      writeGotMessage(showMessage.replace('{0}', str(Ent.Choose(Ent.PEOPLE_CONTACT, totalItems))))
    return entityList
  except (GAPI.permissionDenied, GAPI.failedPrecondition) as e:
    ClientAPIAccessDeniedExit(str(e))
  except (GAPI.serviceNotAvailable, GAPI.forbidden):
    entityUnknownWarning(entityType, user, i, count)
  return None

def queryPeopleOtherContacts(people, contactQuery, fields, entityType, user, i=0, count=0):
  sources = [PEOPLE_READ_SOURCES_CHOICE_MAP['contact']]
  printGettingAllEntityItemsForWhom(Ent.OTHER_CONTACT, user, i, count, query=contactQuery['query'])
  pageMessage = getPageMessageForWhom()
  try:
    if not contactQuery['query']:
      entityList = callGAPIpages(people.otherContacts(), 'list', 'otherContacts',
                                 pageMessage=pageMessage,
                                 throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 pageSize=GC.Values[GC.PEOPLE_MAX_RESULTS],
                                 readMask=fields, fields='nextPageToken,otherContacts', sources=sources)
    else:
      results = callGAPI(people.otherContacts(), 'search',
                         throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                         pageSize=30, readMask=fields, query=contactQuery['query'])
      entityList = [person['person'] for person in results.get('results', [])]
      totalItems = len(entityList)
      if pageMessage:
        showMessage = pageMessage.replace(TOTAL_ITEMS_MARKER, str(totalItems))
        writeGotMessage(showMessage.replace('{0}', str(Ent.Choose(Ent.OTHER_CONTACT, totalItems))))
    return entityList
  except GAPI.permissionDenied as e:
    ClientAPIAccessDeniedExit(str(e))
  except GAPI.forbidden:
    userPeopleServiceNotEnabledWarning(user, i, count)
  except GAPI.serviceNotAvailable:
    entityUnknownWarning(entityType, user, i, count)
  return None

def getPeopleContactGroupsInfo(people, entityType, entityName, i, count):
  contactGroupIDs = {}
  contactGroupNames = {}
  try:
    groups = callGAPIpages(people.contactGroups(), 'list', 'contactGroups',
                           throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                           pageSize=GC.Values[GC.PEOPLE_MAX_RESULTS],
                           groupFields='name', fields='nextPageToken,contactGroups(resourceName,name,formattedName)')
    if groups:
      for group in groups:
        contactGroupIDs[group['resourceName']] = group['formattedName']
        contactGroupNames.setdefault(group['formattedName'], [])
        contactGroupNames[group['formattedName']].append(group['resourceName'])
        if group['formattedName'] != group['name']:
          contactGroupNames.setdefault(group['name'], [])
          contactGroupNames[group['name']].append(group['resourceName'])
  except GAPI.permissionDenied as e:
    ClientAPIAccessDeniedExit(str(e))
  except GAPI.forbidden:
    userPeopleServiceNotEnabledWarning(entityName, i, count)
    return (contactGroupIDs, False)
  except GAPI.serviceNotAvailable:
    entityUnknownWarning(entityType, entityName, i, count)
    return (contactGroupIDs, False)
  return (contactGroupIDs, contactGroupNames)

def validatePeopleContactGroup(people, contactGroupName,
                               contactGroupIDs, contactGroupNames, entityType, entityName, i, count):
  from gam.cmd.contacts import normalizeContactGroupResourceName
  if not contactGroupNames:
    contactGroupIDs, contactGroupNames = getPeopleContactGroupsInfo(people, entityType, entityName, i, count)
    if contactGroupNames is False:
      return (None, contactGroupIDs, contactGroupNames)
  if contactGroupName == 'clear':
    return (contactGroupName, contactGroupIDs, contactGroupNames)
  cg = UID_PATTERN.match(contactGroupName)
  if cg:
    contactGroupName = cg.group(1)
    if contactGroupName in contactGroupIDs:
      return (contactGroupName, contactGroupIDs, contactGroupNames)
    normalizedContactGroupName = normalizeContactGroupResourceName(contactGroupName)
    if normalizedContactGroupName in contactGroupIDs:
      return (normalizedContactGroupName, contactGroupIDs, contactGroupNames)
  else:
    if contactGroupName in contactGroupIDs:
      return (contactGroupName, contactGroupIDs, contactGroupNames)
    if contactGroupName in contactGroupNames:
      return (contactGroupNames[contactGroupName][0], contactGroupIDs, contactGroupNames)
    normalizedContactGroupName = normalizeContactGroupResourceName(contactGroupName)
    if normalizedContactGroupName != contactGroupName and normalizedContactGroupName in contactGroupIDs:
      return (normalizedContactGroupName, contactGroupIDs, contactGroupNames)
  return (None, contactGroupIDs, contactGroupNames)

def validatePeopleContactGroupsList(people, contactId,
                                    contactGroupsList, entityType, entityName, i, count):
  result = True
  contactGroupIDs = contactGroupNames = None
  validatedContactGroupsList = []
  for contactGroup in contactGroupsList:
    groupId, contactGroupIDs, contactGroupNames = validatePeopleContactGroup(people, contactGroup,
                                                                             contactGroupIDs, contactGroupNames, entityType, entityName, i, count)
    if groupId:
      validatedContactGroupsList.append(groupId)
    else:
      if contactGroupNames:
        entityActionNotPerformedWarning([entityType, entityName, Ent.CONTACT, contactId],
                                        Ent.TypeNameMessage(Ent.CONTACT_GROUP, contactGroup, Msg.DOES_NOT_EXIST))
      result = False
  return (result, validatedContactGroupsList, contactGroupIDs)

# gam <UserTypeEntity> create contact <PeopleContactAttribute>+
#	(contactgroup <ContactGroupItem>)*
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
def createUserPeopleContact(users):
  from gam.cmd.contacts import PeopleManager
  entityType = Ent.USER
  peopleManager = PeopleManager()
  peopleEntityType = Ent.CONTACT
  sources = PEOPLE_READ_SOURCES_CHOICE_MAP['contact']
  parameters = {'csvPF': None, 'titles': ['User', 'resourceName'], 'addCSVData': {}, 'returnIdOnly': False}
  body, personFields, contactGroupsLists = peopleManager.GetPersonFields(entityType, False, parameters)
  csvPF = parameters['csvPF']
  addCSVData = parameters['addCSVData']
  if addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
  returnIdOnly = parameters['returnIdOnly']
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    if contactGroupsLists[PEOPLE_GROUPS_LIST]:
      result, validatedContactGroupsList, _ = validatePeopleContactGroupsList(people, '',
                                                                              contactGroupsLists[PEOPLE_GROUPS_LIST], entityType, user, i, count)
      if not result:
        continue
      peopleManager.AddContactGroupsToContact(body, validatedContactGroupsList)
      personFields.add(PEOPLE_MEMBERSHIPS)
    else:
      personFields.discard(PEOPLE_MEMBERSHIPS)
    try:
      result = callGAPI(people.people(), 'createContact',
                        throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS+[GAPI.INVALID_ARGUMENT],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        personFields=','.join(personFields), body=body, sources=sources)
      resourceName = result['resourceName']
      if returnIdOnly:
        writeStdout(f'{resourceName}\n')
      elif not csvPF:
        entityActionPerformed([entityType, user, peopleEntityType, resourceName], i, count)
      else:
        row = {'User': user, 'resourceName': resourceName}
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRow(row)
    except GAPI.invalidArgument as e:
      entityActionFailedWarning([entityType, user, peopleEntityType, None], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
      ClientAPIAccessDeniedExit(str(e))
  if csvPF:
    csvPF.writeCSVfile('People Contacts')

def localPeopleContactSelects(contactQuery, contact):
  if contactQuery['emailMatchPattern']:
    emailMatchType = contactQuery['emailMatchType']
    for item in contact.get(PEOPLE_EMAIL_ADDRESSES, []):
      if contactQuery['emailMatchPattern'].match(item['value']):
        if (not emailMatchType or emailMatchType == item.get('type', '')):
          break
    else:
      return False
  return True

def countLocalPeopleContactSelects(contactQuery, contacts):
  if contacts is not None and contactQuery['emailMatchPattern']:
    jcount = 0
    for contact in contacts:
      if localPeopleContactSelects(contactQuery, contact):
        jcount += 1
  else:
    jcount = len(contacts) if contacts is not None else 0
  return jcount

def clearPeopleEmailAddressMatches(contactClear, contact):
  savedAddresses = []
  updateRequired = False
  emailMatchType = contactClear['emailClearType']
  for item in contact.get(PEOPLE_EMAIL_ADDRESSES, []):
    if (contactClear['emailClearPattern'].match(item['value']) and
        (not emailMatchType or emailMatchType == item.get('type', ''))):
      updateRequired = True
    else:
      savedAddresses.append(item)
  if updateRequired:
    contact[PEOPLE_EMAIL_ADDRESSES] = savedAddresses
  return updateRequired

def _clearUpdatePeopleContacts(users, updateContacts):
  from gam.cmd.contacts import PeopleManager
  action = Act.Get()
  entityType = Ent.USER
  peopleManager = PeopleManager()
  peopleEntityType = Ent.PEOPLE_CONTACT
  sources = PEOPLE_READ_SOURCES_CHOICE_MAP['contact']
  entityList, resourceNameLists, contactQuery, queriedContacts = _getPeopleContactEntityList(entityType, 1)
  if updateContacts:
    body, updatePersonFields, contactGroupsLists = peopleManager.GetPersonFields(entityType, True)
  else:
    contactClear = {'emailClearPattern': contactQuery['emailMatchPattern'], 'emailClearType': contactQuery['emailMatchType']}
    deleteClearedContactsWithNoEmails = False
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'emailclearpattern':
        contactClear['emailClearPattern'] = getREPattern(re.IGNORECASE)
      elif myarg == 'emailcleartype':
        contactClear['emailClearType'] = getString(Cmd.OB_CONTACT_EMAIL_TYPE)
      elif myarg == 'deleteclearedcontactswithnoemails':
        deleteClearedContactsWithNoEmails = True
      else:
        unknownArgumentExit()
    if not contactClear['emailClearPattern']:
      missingArgumentExit('emailclearpattern')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    if contactQuery['contactGroupSelect']:
      groupId, _, contactGroupNames = validatePeopleContactGroup(people, contactQuery['contactGroupSelect'],
                                                                 None, None, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactQuery['contactGroupSelect']], Msg.DOES_NOT_EXIST, i, count)
        continue
      contactQuery['group'] = groupId
    if queriedContacts:
      entityList = queryPeopleContacts(people, contactQuery, 'emailAddresses,memberships', None, entityType, user, i, count)
      if entityList is None:
        continue
    Act.Set(action)
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, peopleEntityType, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    validatedContactGroupsLists = {
      PEOPLE_GROUPS_LIST: [],
      PEOPLE_ADD_GROUPS_LIST: [],
      PEOPLE_REMOVE_GROUPS_LIST: []
      }
    Ind.Increment()
    for contact in entityList:
      j += 1
      try:
        if not queriedContacts:
          resourceName = contact
          contact = callGAPI(people.people(), 'get',
                             bailOnInternalError=True,
                             throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             resourceName=contact, sources=sources, personFields='emailAddresses,memberships')
        else:
          if not localPeopleContactSelects(contactQuery, contact):
            continue
          resourceName = contact['resourceName']
        if updateContacts:
          body['etag'] = contact['etag']
          existingContactGroupsList = []
          for contactGroup in contact.get(PEOPLE_MEMBERSHIPS, []):
            if 'contactGroupMembership' in contactGroup:
              existingContactGroupsList.append(contactGroup['contactGroupMembership']['contactGroupResourceName'])
          groupError = False
          for field in [PEOPLE_GROUPS_LIST, PEOPLE_ADD_GROUPS_LIST, PEOPLE_REMOVE_GROUPS_LIST]:
            if contactGroupsLists[field] and not validatedContactGroupsLists[field]:
              status, validatedContactGroupsLists[field], _ = validatePeopleContactGroupsList(people, resourceName,
                                                                                              contactGroupsLists[field], entityType, user, i, count)
              if not status:
                groupError = True
          if groupError:
            break
          if validatedContactGroupsLists[PEOPLE_GROUPS_LIST]:
            peopleManager.AddContactGroupsToContact(body, validatedContactGroupsLists[PEOPLE_GROUPS_LIST])
            updatePersonFields.add(PEOPLE_MEMBERSHIPS)
          elif validatedContactGroupsLists[PEOPLE_ADD_GROUPS_LIST] or validatedContactGroupsLists[PEOPLE_REMOVE_GROUPS_LIST]:
            body[PEOPLE_MEMBERSHIPS] = []
            if contact.get(PEOPLE_MEMBERSHIPS):
              peopleManager.AddFilteredContactGroupsToContact(body, existingContactGroupsList,
                                                              validatedContactGroupsLists[PEOPLE_REMOVE_GROUPS_LIST])
            if validatedContactGroupsLists[PEOPLE_ADD_GROUPS_LIST]:
              peopleManager.AddAdditionalContactGroupsToContact(body, validatedContactGroupsLists[PEOPLE_ADD_GROUPS_LIST])
            updatePersonFields.add(PEOPLE_MEMBERSHIPS)
          elif existingContactGroupsList:
            updatePersonFields.discard(PEOPLE_MEMBERSHIPS)
        else:
          if not clearPeopleEmailAddressMatches(contactClear, contact):
            continue
          if deleteClearedContactsWithNoEmails and not contact[PEOPLE_EMAIL_ADDRESSES]:
            Act.Set(Act.DELETE)
            callGAPI(people.people(), 'deleteContact',
                     bailOnInternalError=True,
                     throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                     retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                     resourceName=resourceName)
            entityActionPerformed([entityType, user, peopleEntityType, resourceName], j, jcount)
            continue
          body = contact
          updatePersonFields = [PEOPLE_EMAIL_ADDRESSES]
        person = callGAPI(people.people(), 'updateContact',
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          resourceName=resourceName,
                          updatePersonFields=','.join(updatePersonFields), body=body, sources=sources)
        entityActionPerformed([entityType, user, peopleEntityType, person['resourceName']], j, jcount)
      except GAPI.invalidArgument as e:
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], str(e), j, jcount)
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()

# gam <UserTypeEntity> clear contacts <PeopleResourceNameEntity>|<PeopleUserContactSelection>
#	[emailclearpattern <REMatchPattern>] [emailcleartype work|home|other|<String>]
#	[deleteclearedcontactswithnoemails]
def clearUserPeopleContacts(users):
  _clearUpdatePeopleContacts(users, False)

# gam <UserTypeEntity> update contacts <PeopleResourceNameEntity>|(<PeopleUserContactSelection> endquery)
#	<PeopleContactAttribute>+
#	(contactgroup <ContactGroupItem>)*|((addcontactgroup <ContactGroupItem>)* (removecontactgroup <ContactGroupItem>)*)
# gam <UserTypeEntity> update contacts
def updateUserPeopleContacts(users):
  _clearUpdatePeopleContacts(users, True)

def dedupPeopleEmailAddressMatches(emailMatchType, contact):
  sai = -1
  savedAddresses = []
  matches = {}
  updateRequired = False
  for item in contact.get(PEOPLE_EMAIL_ADDRESSES, []):
    emailAddr = item['value']
    emailType = item.get('type', '')
    if (emailAddr in matches) and (not emailMatchType or emailType in matches[emailAddr]['types']):
      if item['metadata'].get('primary', False):
        savedAddresses[matches[emailAddr]['sai']]['metadata']['primary'] = True
      updateRequired = True
    else:
      savedAddresses.append(item)
      sai += 1
      matches.setdefault(emailAddr, {'types': set(), 'sai': sai})
      matches[emailAddr]['types'].add(emailType)
  if updateRequired:
    contact[PEOPLE_EMAIL_ADDRESSES] = savedAddresses
  return updateRequired

def replaceDomainPeopleEmailAddressMatches(contactQuery, contact, replaceDomains):
  updateRequired = False
  if contactQuery['emailMatchPattern']:
    emailMatchType = contactQuery['emailMatchType']
    for item in contact.get(PEOPLE_EMAIL_ADDRESSES, []):
      emailAddr = item['value']
      emailType = item.get('type', '')
      if contactQuery['emailMatchPattern'].match(emailAddr):
        userName, domain = splitEmailAddress(emailAddr)
        domain = domain.lower()
        if ((domain in replaceDomains) and
            (not emailMatchType or emailType == emailMatchType)):
          item['value'] = f'{userName}@{replaceDomains[domain]}'
          updateRequired = True
  else:
    for item in contact.get(PEOPLE_EMAIL_ADDRESSES, []):
      emailAddr = item['value']
      emailType = item.get('type', '')
      userName, domain = splitEmailAddress(emailAddr)
      domain = domain.lower()
      if domain in replaceDomains:
        item['value'] = f'{userName}@{replaceDomains[domain]}'
        updateRequired = True
  return updateRequired

# gam <UserTypeEntity> dedup contacts
#	[<PeopleResourceNameEntity>|<PeopleUserContactSelection>]
#	[matchType [<Boolean>]]
# gam <UserTypeEntity> replacedomain contacts
#	[<PeopleResourceNameEntity>|<PeopleUserContactSelection>]
#	(domain <DomainName> <DomainName>)+
def dedupReplaceDomainUserPeopleContacts(users):
  action = Act.Get()
  entityType = Ent.USER
  peopleEntityType = Ent.PEOPLE_CONTACT
  sources = PEOPLE_READ_SOURCES_CHOICE_MAP['contact']
  entityList, resourceNameLists, contactQuery, queriedContacts = _getPeopleContactEntityList(entityType, 1, {'matchtype', 'domain'})
  emailMatchType = False
  replaceDomains = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if action == Act.DEDUP and myarg == 'matchtype':
      emailMatchType = getBoolean()
    elif action == Act.REPLACE_DOMAIN and myarg == 'domain':
      domain = getString(Cmd.OB_DOMAIN_NAME).lower()
      replaceDomains[domain] = getString(Cmd.OB_DOMAIN_NAME).lower()
    else:
      unknownArgumentExit()
  if action == Act.REPLACE_DOMAIN and not replaceDomains:
    missingArgumentExit('domain')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    if contactQuery['contactGroupSelect']:
      groupId, _, contactGroupNames = validatePeopleContactGroup(people, contactQuery['contactGroupSelect'],
                                                                 None, None, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactQuery['contactGroupSelect']], Msg.DOES_NOT_EXIST, i, count)
        continue
      contactQuery['group'] = groupId
    if queriedContacts:
      entityList = queryPeopleContacts(people, contactQuery, 'emailAddresses,memberships', None, entityType, user, i, count)
      if entityList is None:
        continue
    Act.Set(action)
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, peopleEntityType, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Act.Set(Act.UPDATE)
    Ind.Increment()
    for contact in entityList:
      j += 1
      try:
        if not queriedContacts:
          resourceName = contact
          contact = callGAPI(people.people(), 'get',
                             bailOnInternalError=True,
                             throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                             resourceName=contact, sources=sources, personFields='emailAddresses,memberships')
        else:
          if action == Act.DEDUP and not localPeopleContactSelects(contactQuery, contact):
            continue
          resourceName = contact['resourceName']
        if action == Act.DEDUP:
          if not dedupPeopleEmailAddressMatches(emailMatchType, contact):
            continue
        else:
          if not replaceDomainPeopleEmailAddressMatches(contactQuery, contact, replaceDomains):
            continue
        Act.Set(Act.UPDATE)
        callGAPI(people.people(), 'updateContact',
                 throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 resourceName=resourceName,
                 updatePersonFields='emailAddresses', body=contact)
        entityActionPerformed([entityType, user, peopleEntityType, resourceName], j, jcount)
      except GAPI.invalidArgument as e:
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], str(e), j, jcount)
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()

# gam <UserTypeEntity> delete contacts <PeopleResourceNameEntity>|<PeopleUserContactSelection>
def deleteUserPeopleContacts(users):
  from gam.cmd.contacts import normalizePeopleResourceName
  entityType = Ent.USER
  peopleEntityType = Ent.PEOPLE_CONTACT
  entityList, resourceNameLists, contactQuery, queriedContacts = _getPeopleContactEntityList(entityType, -1)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    if contactQuery['contactGroupSelect']:
      groupId, _, contactGroupNames = validatePeopleContactGroup(people, contactQuery['contactGroupSelect'],
                                                                 None, None, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactQuery['contactGroupSelect']], Msg.DOES_NOT_EXIST, i, count)
        continue
      contactQuery['group'] = groupId
    if queriedContacts:
      entityList = queryPeopleContacts(people, contactQuery, 'emailAddresses', None, entityType, user, i, count)
      if entityList is None:
        continue
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, peopleEntityType, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contact in entityList:
      j += 1
      if isinstance(contact, dict):
        if not localPeopleContactSelects(contactQuery, contact):
          continue
        resourceName = contact['resourceName']
      else:
        resourceName = normalizePeopleResourceName(contact)
      try:
        callGAPI(people.people(), 'deleteContact',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 resourceName=resourceName)
        entityActionPerformed([entityType, user, peopleEntityType, resourceName], j, jcount)
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()

def _initPersonMetadataParameters():
  return {'strip': True, 'mapUpdateTime': False, 'sourceTypes': set()}

def _processPersonMetadata(person, parameters):
  metadata = person.get(PEOPLE_METADATA, None)
  if metadata is not None:
    if parameters['mapUpdateTime']:
      sources = person[PEOPLE_METADATA].get('sources', [])
      if sources and sources[0].get(PEOPLE_UPDATE_TIME, None) is not None:
        person[PEOPLE_UPDATE_TIME] = formatLocalTime(sources[0][PEOPLE_UPDATE_TIME])
  if parameters['sourceTypes']:
    stripKeys = []
    for k, v in person.items():
      if isinstance(v, list):
        person[k] = []
        for entry in v:
          if isinstance(entry, dict):
            if entry.get('metadata', {}).get('source', {}).get('type', None) in parameters['sourceTypes']:
              person[k].append(entry)
          else:
            person[k].append(entry)
        if not person[k]:
          stripKeys.append(k)
    for k in stripKeys:
      person.pop(k, None)
  if parameters['strip']:
    person.pop(PEOPLE_METADATA, None)
    for v in person.values():
      if isinstance(v, list):
        for entry in v:
          if isinstance(entry, dict):
            entry.pop(PEOPLE_METADATA, None)

def addContactGroupNamesToContacts(contacts, contactGroupIDs, showContactGroupNamesList):
  for contact in contacts:
    if showContactGroupNamesList:
      contact[PEOPLE_GROUPS_LIST] = []
    for membership in contact.get('memberships', []):
      if 'contactGroupMembership' in membership:
        membership['contactGroupMembership']['contactGroupName'] = contactGroupIDs.get(membership['contactGroupMembership']['contactGroupResourceName'], UNKNOWN)
        if showContactGroupNamesList:
          contact[PEOPLE_GROUPS_LIST].append(membership['contactGroupMembership']['contactGroupName'])

def _printPerson(entityTypeName, user, person, csvPF, FJQC, parameters):
  _processPersonMetadata(person, parameters)
  row = flattenJSON(person, flattened={entityTypeName: user})
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    csvPF.WriteRowNoFilter({entityTypeName: user, 'resourceName': person['resourceName'],
                            'JSON': json.dumps(cleanJSON(person),
                                               ensure_ascii=False, sort_keys=True)})

PEOPLE_CONTACT_OBJECT_KEYS = {
  'addresses': 'type',
  'calendarUrls': 'type',
  'emailAddresses': 'type',
  'events': 'type',
  'externalIds': 'type',
  'genders': 'value',
  'imClients': 'type',
  'locations': 'type',
  'miscKeywords': 'type',
  'nicknames': 'type',
  'organizations': 'type',
  'relations': 'type',
  'urls': 'type',
  'userDefined': 'key',
  }

def _showPerson(userEntityType, user, entityType, person, i, count, FJQC, parameters):
  _processPersonMetadata(person, parameters)
  if not FJQC.formatJSON:
    printEntity([userEntityType, user, entityType, person['resourceName']], i, count)
    Ind.Increment()
    showJSON(None, person, dictObjectsKey=PEOPLE_CONTACT_OBJECT_KEYS)
    Ind.Decrement()
  else:
    printLine(json.dumps(cleanJSON(person), ensure_ascii=False, sort_keys=True))

def _printPersonEntityList(entityType, entityList, userEntityType, user, i, count, csvPF, FJQC, parameters, contactQuery):
  if not csvPF:
    jcount = len(entityList)
    if not FJQC.formatJSON:
      entityPerformActionModifierNumItems([userEntityType, user], Msg.MAXIMUM_OF, jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for person in entityList:
      j += 1
      if not contactQuery or localPeopleContactSelects(contactQuery, person):
        _showPerson(userEntityType, user, entityType, person, j, jcount, FJQC, parameters)
    Ind.Decrement()
  elif entityList:
    entityTypeName = Ent.Singular(userEntityType)
    for person in entityList:
      if not contactQuery or localPeopleContactSelects(contactQuery, person):
        _printPerson(entityTypeName, user, person, csvPF, FJQC, parameters)
  elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
    csvPF.WriteRowNoFilter({userEntityType: user})

PEOPLE_FIELDS_CHOICE_MAP = {
  'additionalname': PEOPLE_NAMES,
  'address': PEOPLE_ADDRESSES,
  'addresses': PEOPLE_ADDRESSES,
  'ageranges': 'ageRanges',
  'billinginfo': PEOPLE_MISC_KEYWORDS,
  'biography': PEOPLE_BIOGRAPHIES,
  'biographies': PEOPLE_BIOGRAPHIES,
  'birthday': PEOPLE_BIRTHDAYS,
  'birthdays': PEOPLE_BIRTHDAYS,
  'calendar': PEOPLE_CALENDAR_URLS,
  'calendars': PEOPLE_CALENDAR_URLS,
  'calendarurls': PEOPLE_CALENDAR_URLS,
  'clientdata': PEOPLE_CLIENT_DATA,
  'coverphotos': PEOPLE_COVER_PHOTOS,
  'directoryserver': PEOPLE_MISC_KEYWORDS,
  'email': PEOPLE_EMAIL_ADDRESSES,
  'emails': PEOPLE_EMAIL_ADDRESSES,
  'emailaddresses': PEOPLE_EMAIL_ADDRESSES,
  'event': PEOPLE_EVENTS,
  'events': PEOPLE_EVENTS,
  'externalid': PEOPLE_EXTERNAL_IDS,
  'externalids': PEOPLE_EXTERNAL_IDS,
  'familyname': PEOPLE_NAMES,
  'fileas': PEOPLE_FILE_ASES,
  'firstname': PEOPLE_NAMES,
  'gender': PEOPLE_GENDERS,
  'genders': PEOPLE_GENDERS,
  'givenname': PEOPLE_NAMES,
  'hobby': PEOPLE_INTERESTS,
  'hobbies': PEOPLE_INTERESTS,
  'im': PEOPLE_IM_CLIENTS,
  'ims': PEOPLE_IM_CLIENTS,
  'imclients': PEOPLE_IM_CLIENTS,
  'initials': PEOPLE_NICKNAMES,
  'interests': PEOPLE_INTERESTS,
  'jot': PEOPLE_MISC_KEYWORDS,
  'jots': PEOPLE_MISC_KEYWORDS,
  'language': PEOPLE_LOCALES,
  'languages': PEOPLE_LOCALES,
  'lastname': PEOPLE_NAMES,
  'locales': PEOPLE_LOCALES,
  'location': PEOPLE_LOCATIONS,
  'locations': PEOPLE_LOCATIONS,
  'maidenname': PEOPLE_NAMES,
  'memberships': PEOPLE_MEMBERSHIPS,
  'metadata': PEOPLE_METADATA,
  'middlename': PEOPLE_NAMES,
  'mileage': PEOPLE_MISC_KEYWORDS,
  'misckeywords': PEOPLE_MISC_KEYWORDS,
  'name': PEOPLE_NAMES,
  'names': PEOPLE_NAMES,
  'nickname': PEOPLE_NICKNAMES,
  'nicknames': PEOPLE_NICKNAMES,
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
  'photo': PEOPLE_PHOTOS,
  'photos': PEOPLE_PHOTOS,
  'prefix': PEOPLE_NAMES,
  'priority': PEOPLE_MISC_KEYWORDS,
  'relation': PEOPLE_RELATIONS,
  'relations': PEOPLE_RELATIONS,
  'sensitivity': PEOPLE_MISC_KEYWORDS,
  'shortname': PEOPLE_NICKNAMES,
  'sipaddress': PEOPLE_SIP_ADDRESSES,
  'sipaddresses': PEOPLE_SIP_ADDRESSES,
  'skills': PEOPLE_SKILLS,
  'subject': PEOPLE_MISC_KEYWORDS,
  'suffix': PEOPLE_NAMES,
  'updated': PEOPLE_UPDATE_TIME,
  'updatetime': PEOPLE_UPDATE_TIME,
  'urls': PEOPLE_URLS,
  'userdefined': PEOPLE_USER_DEFINED,
  'userdefinedfield': PEOPLE_USER_DEFINED,
  'userdefinedfields': PEOPLE_USER_DEFINED,
  'website': PEOPLE_URLS,
  'websites': PEOPLE_URLS,
  }

PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP = {
  'email': PEOPLE_EMAIL_ADDRESSES,
  'emails': PEOPLE_EMAIL_ADDRESSES,
  'emailaddresses': PEOPLE_EMAIL_ADDRESSES,
  'metadata': PEOPLE_METADATA,
  'names': PEOPLE_NAMES,
  'phone': PEOPLE_PHONE_NUMBERS,
  'phones': PEOPLE_PHONE_NUMBERS,
  'phonenumbers': PEOPLE_PHONE_NUMBERS,
  'photo': PEOPLE_PHOTOS,
  'photos': PEOPLE_PHOTOS,
  }

PEOPLE_CONTACTS_DEFAULT_FIELDS = ['names', 'emailaddresses', 'phonenumbers']

PEOPLE_ORDERBY_CHOICE_MAP = {
  'firstname': 'FIRST_NAME_ASCENDING',
  'lastname': 'LAST_NAME_ASCENDING',
  'lastmodified': 'LAST_MODIFIED_',
  }

def getPersonFieldsList(myarg, fieldsChoiceMap, fieldsList, initialField=None, fieldsArg='fields'):
  if fieldsList is None:
    fieldsList = []
  return getFieldsList(myarg, fieldsChoiceMap, fieldsList, initialField, fieldsArg)

def _getPersonFields(fieldsChoiceMap, defaultFields, fieldsList, parameters):
  if fieldsList is None:
    fieldsList = []
    for field in fieldsChoiceMap:
      addFieldToFieldsList(field, fieldsChoiceMap, fieldsList)
  elif not fieldsList:
    for field in defaultFields:
      addFieldToFieldsList(field, fieldsChoiceMap, fieldsList)
  fieldsList = list(set(fieldsList))
  if PEOPLE_UPDATE_TIME in fieldsList:
    parameters['mapUpdateTime'] = True
    fieldsList.remove(PEOPLE_UPDATE_TIME)
    fieldsList.append(PEOPLE_METADATA)
  return ','.join(fieldsList)

def _infoPeople(users, entityType, source):
  from gam.cmd.contacts import normalizePeopleResourceName
  if entityType == Ent.DOMAIN:
    people = buildGAPIObject(API.PEOPLE)
  peopleEntityType = Ent.DOMAIN_PROFILE if source == 'profile' else Ent.PEOPLE_CONTACT
  sources = [PEOPLE_READ_SOURCES_CHOICE_MAP[source]]
  entityList = getEntityList(Cmd.OB_CONTACT_ENTITY)
  resourceNameLists = entityList if isinstance(entityList, dict) else None
  showContactGroups = False
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'showgroups':
      showContactGroups = True
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getPersonFields(PEOPLE_FIELDS_CHOICE_MAP, PEOPLE_CONTACTS_DEFAULT_FIELDS, fieldsList, parameters)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    contactGroupIDs = contactGroupNames = None
    if entityType != Ent.DOMAIN:
      user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
      if not people:
        continue
      if showContactGroups:
        contactGroupIDs, contactGroupNames = getPeopleContactGroupsInfo(people, entityType, user, i, count)
        if contactGroupNames is False:
          continue
    j = 0
    jcount = len(entityList)
    if not FJQC.formatJSON:
      entityPerformActionNumItems([entityType, user], jcount, peopleEntityType, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contact in entityList:
      j += 1
      if isinstance(contact, dict):
        resourceName = contact['resourceName']
      else:
        resourceName = normalizePeopleResourceName(contact)
      try:
        result = callGAPI(people.people(), 'get',
                          bailOnInternalError=True,
                          throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR, GAPI.INVALID_ARGUMENT]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          resourceName=resourceName, sources=sources, personFields=fields)
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
        continue
      except GAPI.invalidArgument as e:
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], str(e), j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
      if showContactGroups and contactGroupIDs:
        addContactGroupNamesToContacts([result], contactGroupIDs, False)
      _showPerson(entityType, user, peopleEntityType, result, j, jcount, FJQC, parameters)
    Ind.Decrement()

# gam <UserTypeEntity> info contacts <PeopleResourceNameEntity>
#	[showgroups]
#	[allFields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[formatjson]
def infoUserPeopleContacts(users):
  _infoPeople(users, Ent.USER, 'contact')

# gam <UserTypeEntity> print contacts [todrive <ToDriveAttribute>*] <PeoplePrintShowUserContactSelection>
#	[showgroups|showgroupnameslist] [orderby firstname|lastname|(lastmodified ascending)|(lastnodified descending)
#	[allfields|fields <PeopleFieldNameList>] [showmetadata]
#	[countsonly|(formatjson [quotechar <Character>])]
# gam <UserTypeEntity> show contacts <PeoplePrintShowUserContactSelection>
#	[showgroups] [orderby firstname|lastname|(lastmodified ascending)|(lastnodified descending)
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonly|formatjson]
def printShowUserPeopleContacts(users):
  entityType = Ent.USER
  entityTypeName = Ent.Singular(entityType)
  csvPF = CSVPrintFile([entityTypeName, 'resourceName'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  CSVTitle = 'People Contacts'
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  sortOrder = None
  countsOnly = showContactGroups = showContactGroupNamesList = False
  contactQuery = _initPeopleContactQueryAttributes(True)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showgroups':
      showContactGroups = True
    elif myarg == 'showgroupnameslist':
      showContactGroups = showContactGroupNamesList = True
    elif myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'countsonly':
      countsOnly = True
      if csvPF:
        csvPF.SetTitles([entityTypeName, CSVTitle])
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    elif myarg == 'orderby':
      sortOrder = getChoice(PEOPLE_ORDERBY_CHOICE_MAP, mapChoice=True)
      if sortOrder == 'LAST_MODIFIED_':
        sortOrder += getChoice(SORTORDER_CHOICE_MAP, defaultChoice='DESCENDING', mapChoice=True)
    elif _getPeopleContactQueryAttributes(contactQuery, myarg, entityType, 0, True):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if countsOnly:
    if csvPF:
      csvPF.SetFormatJSON(False)
    fieldsList = ['emailAddresses']
  if contactQuery['mainContacts']:
    fields = _getPersonFields(PEOPLE_FIELDS_CHOICE_MAP, PEOPLE_CONTACTS_DEFAULT_FIELDS, fieldsList, parameters)
    if contactQuery['contactGroupFilter'] and 'memberships' not in fields:
      fields += ',memberships'
      contactQuery['dropMemberships'] = True
  if contactQuery['otherContacts']:
    if not fieldsList:
      ofields = _getPersonFields(PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP, PEOPLE_CONTACTS_DEFAULT_FIELDS, fieldsList, parameters)
    else:
      ofields = getFieldsFromFieldsList([PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP[field.lower()] for field in fieldsList if field.lower() in PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    if contactQuery['otherContacts']:
      _, opeople = buildGAPIServiceObject(API.PEOPLE_OTHERCONTACTS, user, i, count)
      if not opeople:
        continue
    contactGroupIDs = contactGroupNames = None
    if showContactGroups:
      contactGroupIDs, contactGroupNames = getPeopleContactGroupsInfo(people, entityType, user, i, count)
      if contactGroupNames is False:
        continue
    contactGroupSelectFilter = contactQuery['contactGroupSelect'] or contactQuery['contactGroupFilter']
    if contactGroupSelectFilter:
      groupId, _, contactGroupNames =\
        validatePeopleContactGroup(people, contactGroupSelectFilter,
                                   contactGroupIDs, contactGroupNames, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroupSelectFilter], Msg.DOES_NOT_EXIST, i, count)
        continue
      contactQuery['group'] = groupId
    if contactQuery['mainContacts']:
      contacts = queryPeopleContacts(people, contactQuery, fields, sortOrder, entityType, user, i, count)
    else:
      contacts = []
    if contactQuery['otherContacts']:
      ocontacts = queryPeopleOtherContacts(opeople, contactQuery, ofields, entityType, user, i, count)
    else:
      ocontacts = []
    if countsOnly:
      jcount = countLocalPeopleContactSelects(contactQuery, contacts)+countLocalPeopleContactSelects(contactQuery, ocontacts)
      if csvPF:
        csvPF.WriteRowTitles({entityTypeName: user, CSVTitle: jcount})
      else:
        printEntityKVList([entityType, user], [CSVTitle, jcount], i, count)
    elif contacts is not None or ocontacts is not None:
      if not csvPF:
        if contacts is not None and contactQuery['mainContacts']:
          if showContactGroups and contactGroupIDs:
            addContactGroupNamesToContacts(contacts, contactGroupIDs, False)
          _printPersonEntityList(Ent.PEOPLE_CONTACT, contacts, entityType, user, i, count, csvPF, FJQC, parameters, contactQuery)
        if ocontacts is not None and contactQuery['otherContacts']:
          _printPersonEntityList(Ent.OTHER_CONTACT, ocontacts, entityType, user, i, count, csvPF, FJQC, parameters, contactQuery)
      elif contacts or ocontacts:
        if contacts:
          if showContactGroups and contactGroupIDs:
            addContactGroupNamesToContacts(contacts, contactGroupIDs, showContactGroupNamesList and FJQC.formatJSON)
          _printPersonEntityList(Ent.PEOPLE_CONTACT, contacts, entityType, user, i, count, csvPF, FJQC, parameters, contactQuery)
        if ocontacts:
          _printPersonEntityList(Ent.OTHER_CONTACT, ocontacts, entityType, user, i, count, csvPF, FJQC, parameters, contactQuery)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({Ent.Singular(entityType): user})
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

CONTACTGROUPS_MYCONTACTS_ID = 'contactGroups/myContacts'
CONTACTGROUPS_MYCONTACTS_NAME = 'My Contacts'

# gam <UserTypeEntity> copy othercontacts
#	<OtherContactResourceNameEntity>|<OtherContactSelection>
def copyUserPeopleOtherContacts(users):
  from gam.cmd.contacts import normalizeOtherContactsResourceName
  entityType = Ent.USER
  peopleEntityType = Ent.OTHER_CONTACT
  sources = [PEOPLE_READ_SOURCES_CHOICE_MAP['contact']]
  copyMask = ['emailAddresses', 'names', 'phoneNumbers']
  entityList, resourceNameLists, contactQuery, queriedContacts = _getPeopleOtherContactEntityList(-1)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE_OTHERCONTACTS, user, i, count)
    if not people:
      continue
    if queriedContacts:
      entityList = queryPeopleOtherContacts(people, contactQuery, 'emailAddresses', entityType, user, i, count)
      if entityList is None:
        continue
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, peopleEntityType, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contact in entityList:
      j += 1
      if isinstance(contact, dict):
        if not localPeopleContactSelects(contactQuery, contact):
          continue
        resourceName = contact['resourceName']
      else:
        resourceName = normalizeOtherContactsResourceName(contact)
      try:
        callGAPI(people.otherContacts(), 'copyOtherContactToMyContactsGroup',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                 resourceName=resourceName, body={'copyMask': ','.join(copyMask), 'sources': sources})
        entityModifierNewValueActionPerformed([entityType, user, peopleEntityType, resourceName], Act.MODIFIER_TO, CONTACTGROUPS_MYCONTACTS_NAME)
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()

# gam <UserTypeEntity> delete othercontacts
#	<OtherContactResourceNameEntity>|<OtherContactSelection>
# gam <UserTypeEntity> move othercontacts
#	<OtherContactResourceNameEntity>|<OtherContactSelection>
# gam <UserTypeEntity> update othercontacts
#	<OtherResourceNameEntity>|<OtherContactSelection>
#	<PeopleContactAttribute>*
#	(contactgroup <ContactGroupItem>)*
def processUserPeopleOtherContacts(users):
  from gam.cmd.contacts import PeopleManager, normalizeOtherContactsResourceName
  action = Act.Get()
  entityType = Ent.USER
  peopleEntityType = Ent.OTHER_CONTACT
  sources = PEOPLE_READ_SOURCES_CHOICE_MAP['contact']
  entityList, resourceNameLists, contactQuery, queriedContacts = _getPeopleOtherContactEntityList(1)
  if action == Act.UPDATE:
    Act.Set(Act.UPDATE_MOVE)
    peopleManager = PeopleManager()
    body, updatePersonFields, contactGroupsLists = peopleManager.GetPersonFields(entityType, False)
  else:
    body = {PEOPLE_MEMBERSHIPS: [{'contactGroupMembership': {'contactGroupResourceName': CONTACTGROUPS_MYCONTACTS_ID}}]}
    updatePersonFields = [PEOPLE_MEMBERSHIPS]
    checkForExtraneousArguments()
  validatedContactGroupsList = [CONTACTGROUPS_MYCONTACTS_ID]
  contactGroupIDs = {CONTACTGROUPS_MYCONTACTS_ID: CONTACTGROUPS_MYCONTACTS_NAME}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE_OTHERCONTACTS, user, i, count)
    if not people:
      continue
    _, upeople = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not upeople:
      continue
    if queriedContacts:
      entityList = queryPeopleOtherContacts(people, contactQuery, 'emailAddresses', entityType, user, i, count)
      if entityList is None:
        continue
    else:
      otherContacts = _getPeopleOtherContacts(people, entityType, user, i=0, count=0)
      if otherContacts is None:
        continue
    if action == Act.UPDATE:
      if contactGroupsLists[PEOPLE_GROUPS_LIST]:
        result, validatedContactGroupsList, contactGroupIDs =\
          validatePeopleContactGroupsList(people, '', contactGroupsLists[PEOPLE_GROUPS_LIST], entityType, user, i, count)
        if not result:
          continue
      if CONTACTGROUPS_MYCONTACTS_ID not in validatedContactGroupsList:
        validatedContactGroupsList.insert(0, CONTACTGROUPS_MYCONTACTS_ID)
      updatePersonFields.add(PEOPLE_MEMBERSHIPS)
    contactGroupNamesList = []
    for resourceName in validatedContactGroupsList:
      contactGroupNamesList.append(contactGroupIDs[resourceName])
    contactGroupNames = ','.join(contactGroupNamesList)
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, peopleEntityType, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contact in entityList:
      j += 1
      if isinstance(contact, dict):
        if not localPeopleContactSelects(contactQuery, contact):
          continue
        resourceName = contact['resourceName']
      else:
        resourceName = normalizeOtherContactsResourceName(contact)
        contact = otherContacts.get(resourceName)
        if contact is None:
          entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
          continue
      peopleResourceName = resourceName.replace('otherContacts', 'people')
      body['etag'] = contact['etag']
      if action == Act.UPDATE and validatedContactGroupsList:
        peopleManager.AddContactGroupsToContact(body, validatedContactGroupsList)
      try:
        callGAPI(upeople.people(), 'updateContact',
                 throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 resourceName=peopleResourceName,
                 updatePersonFields=','.join(updatePersonFields), body=body, sources=sources)
        if action != Act.DELETE:
          entityModifierNewValueActionPerformed([entityType, user, peopleEntityType, resourceName],
                                                Act.MODIFIER_TO, contactGroupNames, j, jcount)
        else:
          maxRetries = 5
          for retry in range(1, maxRetries+1):
            try:
              callGAPI(upeople.people(), 'deleteContact',
                       bailOnInternalError=True,
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                       retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                       resourceName=peopleResourceName)
              entityActionPerformed([entityType, user, peopleEntityType, resourceName], j, jcount)
              break
            except (GAPI.notFound, GAPI.internalError):
              if retry == maxRetries:
                entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
                break
              time.sleep(retry*2)
      except GAPI.invalidArgument as e:
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], str(e), j, jcount)
        continue
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()

# gam <UserTypeEntity> print othercontacts [todrive <ToDriveAttribute>*] <OtherContactSelection>
#	[allfields|(fields <OtherContactFieldNameList>)] [showmetadata]
#	[countsonly|(formatjson [quotechar <Character>])]
# gam <UserTypeEntity> show othercontacts <OtherContactSelection>
#	[allfields|(fields <OtherContactFieldNameList>)] [showmetadata]
#	[countsonly|formatjson]
def printShowUserPeopleOtherContacts(users):
  entityType = Ent.USER
  entityTypeName = Ent.Singular(entityType)
  csvPF = CSVPrintFile([entityTypeName, 'resourceName'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  CSVTitle = 'Other Contacts'
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  countsOnly = False
  contactQuery = _initPeopleOtherContactQueryAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'countsonly':
      countsOnly = True
      if csvPF:
        csvPF.SetTitles([entityTypeName, CSVTitle])
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    elif _getPeopleOtherContactQueryAttributes(contactQuery, myarg, 0):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if countsOnly:
    if csvPF:
      csvPF.SetFormatJSON(False)
    fieldsList = ['emailAddresses']
  fields = _getPersonFields(PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP, PEOPLE_CONTACTS_DEFAULT_FIELDS, fieldsList, parameters)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, people = buildGAPIServiceObject(API.PEOPLE_OTHERCONTACTS, user, i, count)
    if not people:
      continue
    contacts = queryPeopleOtherContacts(people, contactQuery, fields, entityType, user, i, count)
    if countsOnly:
      jcount = countLocalPeopleContactSelects(contactQuery, contacts)
      if csvPF:
        csvPF.WriteRowTitles({entityTypeName: user, CSVTitle: jcount})
      else:
        printEntityKVList([entityType, user], [CSVTitle, jcount], i, count)
    elif contacts is not None:
      if not csvPF:
        _printPersonEntityList(Ent.OTHER_CONTACT, contacts, entityType, user, i, count, csvPF, FJQC, parameters, contactQuery)
      elif contacts:
        _printPersonEntityList(Ent.OTHER_CONTACT, contacts, entityType, user, i, count, csvPF, FJQC, parameters, contactQuery)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({Ent.Singular(entityType): user})
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

def _printShowPeople(source):
  people = buildGAPIObject(API.PEOPLE_DIRECTORY)
  entityType = Ent.DOMAIN
  entityTypeName = Ent.Singular(entityType)
  sources = [PEOPLE_DIRECTORY_SOURCES_CHOICE_MAP[source]]
  if sources[0] == 'DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE':
    peopleEntityType = Ent.DOMAIN_PROFILE
    CSVTitle = 'People Profiles'
  else:
    peopleEntityType = Ent.DOMAIN_PEOPLE_CONTACT
    CSVTitle = 'People Contacts'
  function = 'listDirectoryPeople'
  csvPF = CSVPrintFile([entityTypeName, 'resourceName'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  parameters = _initPersonMetadataParameters()
  mergeSources = []
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  countsOnly = False
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif source is None and myarg in {'source', 'sources'}:
      sources = [getChoice(PEOPLE_DIRECTORY_SOURCES_CHOICE_MAP, mapChoice=True)]
    elif myarg in {'mergesource', 'mergesources'}:
      mergeSources = [getChoice(PEOPLE_DIRECTORY_MERGE_SOURCES_CHOICE_MAP, mapChoice=True)]
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    elif myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'countsonly':
      countsOnly = True
      fieldsList = [PEOPLE_METADATA]
      if csvPF:
        csvPF.SetTitles([entityTypeName, CSVTitle])
    elif myarg == 'query':
      kwargs['query'] = getString(Cmd.OB_QUERY)
      function = 'searchDirectoryPeople'
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if countsOnly and csvPF:
    csvPF.SetFormatJSON(False)
  fields = _getPersonFields(PEOPLE_FIELDS_CHOICE_MAP, PEOPLE_CONTACTS_DEFAULT_FIELDS, fieldsList, parameters)
  printGettingAllEntityItemsForWhom(peopleEntityType, GC.Values[GC.DOMAIN], query=kwargs.get('query'))
  try:
    entityList = callGAPIpages(people.people(), function, 'people',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                               pageSize=GC.Values[GC.PEOPLE_MAX_RESULTS],
                               sources=sources, mergeSources=mergeSources,
                               readMask=fields, fields='nextPageToken,people', **kwargs)
  except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
    ClientAPIAccessDeniedExit(str(e))
  if not countsOnly:
    _printPersonEntityList(peopleEntityType, entityList, Ent.DOMAIN, GC.Values[GC.DOMAIN], 0, 0, csvPF, FJQC, parameters, None)
  else:
    jcount = len(entityList)
    if csvPF:
      csvPF.WriteRowTitles({entityTypeName: GC.Values[GC.DOMAIN], CSVTitle: jcount})
    else:
      printEntityKVList([entityType, GC.Values[GC.DOMAIN]], [CSVTitle, jcount])
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

# gam info people|peopleprofile <PeopleResourceNameEntity>
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[formatjson]
def doInfoDomainPeopleProfile():
  _infoPeople([GC.Values[GC.DOMAIN]], Ent.DOMAIN, 'profile')

# gam info peoplecontact <PeopleResourceNameEntity>
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[formatjson]
def doInfoDomainPeopleContacts():
  _infoPeople([GC.Values[GC.DOMAIN]], Ent.DOMAIN, 'domaincontact')

# gam print people|peopleprofile [todrive <ToDriveAttribute>*]
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonly|(formatjson [quotechar <Character>])]
# gam show people|peopleprofile
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonlyformatjson]
# gam print domaincontacts|peoplecontacts [todrive <ToDriveAttribute>*]
#	[sources <PeopleSourceName>]
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonly|(formatjson [quotechar <Character>])]
# gam show domaincontacts|peoplecontacts
#	[sources <PeopleSourceName>]
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[countsonlyformatjson]
def doPrintShowDomainPeopleProfiles():
  _printShowPeople('profile')

def doPrintShowDomainPeopleContacts():
  _printShowPeople('domaincontact')

PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP = {
  'account': 'ACCOUNT',
  'accounts': 'ACCOUNT',
  'domain': 'DOMAIN_PROFILE',
  'domains': 'DOMAIN_PROFILE',
  'profile': 'PROFILE',
  'profiles': 'PROFILE',
  }

# gam <UserTypeEntity> print peopleprofile [todrive <ToDriveAttribute>*]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[sources <PeopleProfileSourceNameList>]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show peopleprofile
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[sources <PeopleProfileSourceNameList>]
#	[formatjson]
def printShowUserPeopleProfiles(users):
  entityType = Ent.USER
  entityTypeName = Ent.Singular(entityType)
  sources = [PEOPLE_READ_SOURCES_CHOICE_MAP['profile']]
  csvPF = CSVPrintFile([entityTypeName, 'resourceName'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg in {'source', 'sources'}:
      for field in _getFieldsList():
        if field in PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP:
          parameters['sourceTypes'].add(PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP, True)
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    elif myarg == 'peoplelookupuser':
      deprecatedArgument(myarg)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = _getPersonFields(PEOPLE_FIELDS_CHOICE_MAP, PEOPLE_CONTACTS_DEFAULT_FIELDS, fieldsList, parameters)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
#    user, people = buildGAPIServiceObject(API.PEOPLE_DIRECTORY, user, i, count)
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.PEOPLE_PROFILE, user, i, count)
    try:
      result = callGAPI(people.people(), 'get',
                        throwReasons=[GAPI.NOT_FOUND]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        resourceName='people/me', sources=sources, personFields=fields)
    except GAPI.notFound:
      entityUnknownWarning(Ent.PEOPLE_PROFILE, user, i, count)
      continue
    except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
      ClientAPIAccessDeniedExit(str(e))
    if not csvPF:
      _showPerson(entityType, user, Ent.PEOPLE_PROFILE, result, i, count, FJQC, parameters)
    else:
      _printPerson(entityTypeName, user, result, csvPF, FJQC, parameters)
  if csvPF:
    csvPF.writeCSVfile('People Profiles')

def _processPeopleContactPhotos(users, function):
  from gam.cmd.contacts import normalizePeopleResourceName
  def _makeFilenameFromPattern(resourceName):
    filename = filenamePattern[:]
    if subForContactId:
      filename = filename.replace('#contactid#', resourceName.split('/')[1])
    if subForEmail:
      for email in result.get(PEOPLE_EMAIL_ADDRESSES, []):
        if email.get(PEOPLE_METADATA, {}).get('primary', False):
          filename = filename.replace('#email#', email['value'])
          break
      else:
        filename = filename.replace('#email#', resourceName.split('/')[1])
    return filename

  if users is not None:
    entityType = Ent.USER
    peopleEntityType = Ent.PEOPLE_CONTACT
    sources = [PEOPLE_READ_SOURCES_CHOICE_MAP['contact']]
  else:
    users = [None]
    people = buildGAPIObject(API.PEOPLE_DIRECTORY)
    entityType = Ent.DOMAIN
    peopleEntityType = Ent.PEOPLE_CONTACT
    sources = [PEOPLE_READ_SOURCES_CHOICE_MAP['domaincontact']]
  entityList, resourceNameLists, contactQuery, queriedContacts = _getPeopleContactEntityList(entityType, 1)
  if function in {'updateContactPhoto', 'getContactPhoto'}:
    sourceFolder = targetFolder = os.getcwd()
    filenamePattern = '#contactid#.jpg'
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'drivedir':
        targetFolder = GC.Values[GC.DRIVE_DIR]
      elif myarg == 'sourcefolder':
        sourceFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.INPUT_DIR)
      elif myarg == 'targetfolder':
        targetFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
        if not os.path.isdir(targetFolder):
          os.makedirs(targetFolder)
      elif myarg == 'filename':
        filenamePattern = getString(Cmd.OB_FILE_NAME_PATTERN)
      else:
        unknownArgumentExit()
    subForContactId = filenamePattern.find('#contactid#') != -1
    subForEmail = filenamePattern.find('#email#') != -1
    if not subForContactId and not subForEmail:
      filename = filenamePattern
  else: #elif function == 'deleteContactPhoto':
    checkForExtraneousArguments()
    subForContactId = subForEmail = False
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if resourceNameLists:
      entityList = resourceNameLists[user]
    if user is not None:
      user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
      if not people:
        continue
    else:
      user = Ent.Singular(entityType)
    if contactQuery['contactGroupSelect']:
      groupId, _, contactGroupNames = validatePeopleContactGroup(people, contactQuery['contactGroupSelect'],
                                                                 None, None, entityType, user, i, count)
      if not groupId:
        if contactGroupNames:
          entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactQuery['contactGroupSelect']], Msg.DOES_NOT_EXIST, i, count)
        continue
      contactQuery['group'] = groupId
    if queriedContacts:
      entityList = queryPeopleContacts(people, contactQuery, 'emailAddresses,photos', None, entityType, user, i, count)
      if entityList is None:
        continue
    j = 0
    jcount = len(entityList)
    entityPerformActionModifierNumItems([entityType, user], Msg.MAXIMUM_OF, jcount, Ent.PHOTO, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contact in entityList:
      j += 1
      if isinstance(contact, dict):
        if not localPeopleContactSelects(contactQuery, contact):
          continue
        resourceName = contact['resourceName']
      else:
        resourceName = normalizePeopleResourceName(contact)
      try:
        if subForEmail:
          result = callGAPI(people.people(), 'get',
                            bailOnInternalError=True,
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            resourceName=resourceName, sources=sources, personFields='emailAddresses')
        if function == 'updateContactPhoto':
          if subForContactId or subForEmail:
            filename = _makeFilenameFromPattern(resourceName)
          filename = os.path.join(sourceFolder, filename)
          with open(filename, 'rb') as f:
            image_data = f.read()
          callGAPI(people.people(), function,
                   throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                   resourceName=resourceName,
                   body={'photoBytes': base64.urlsafe_b64encode(image_data).decode(UTF8)})
          entityActionPerformed([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], j, jcount)
        elif function == 'getContactPhoto':
          if subForContactId or subForEmail:
            filename = _makeFilenameFromPattern(resourceName)
          filename = os.path.join(targetFolder, filename)
          result = callGAPI(people.people(), 'get',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            resourceName=resourceName, personFields='photos')
          url = None
          for photo in result.get('photos', []):
            if photo['metadata']['source']['type'] == 'CONTACT':
              url = photo['url']
              break
          if not url:
            entityActionFailedWarning([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, None], Msg.CONTACT_PHOTO_NOT_FOUND, j, jcount)
            continue
          try:
            status, photo_data = getHttpObj().request(url, 'GET')
            if status['status'] != '200':
              entityActionFailedWarning([entityType, user, Ent.PHOTO, filename], Msg.NOT_ALLOWED, j, jcount)
              continue
          except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
            entityActionFailedWarning([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], str(e), j, jcount)
            continue
          status, e = writeFileReturnError(filename, photo_data, mode='wb')
          if status:
            entityActionPerformed([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], j, jcount)
          else:
            entityActionFailedWarning([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], str(e), j, jcount)
        else: #elif function == 'deleteContactPhoto':
          filename = ''
          callGAPI(people.people(), function,
                   throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR, GAPI.PHOTO_NOT_FOUND]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                   resourceName=resourceName)
          entityActionPerformed([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], j, jcount)
      except (GAPI.notFound, GAPI.internalError):
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName], Msg.DOES_NOT_EXIST, j, jcount)
        continue
      except GAPI.photoNotFound:
        entityDoesNotHaveItemWarning([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], j, jcount)
      except (GAPI.invalidArgument, OSError, IOError) as e:
        entityActionFailedWarning([entityType, user, peopleEntityType, resourceName, Ent.PHOTO, filename], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
        ClientAPIAccessDeniedExit(str(e))
        break
    Ind.Decrement()

# gam <UserTypeEntity> update contactphotos <PeopleResourceNameEntity>|<PeopleUserContactSelection>
#	[drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]
def updateUserPeopleContactPhoto(users):
  _processPeopleContactPhotos(users, 'updateContactPhoto')

# gam <UserTypeEntity> get contactphotos <PeopleResourceNameEntity>|<PeopleUserContactSelection>
#	[drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
def getUserPeopleContactPhoto(users):
  _processPeopleContactPhotos(users, 'getContactPhoto')

# gam <UserTypeEntity> delete contactphotos <PeopleResourceNameEntity>|<PeopleUserContactSelection>
def deleteUserPeopleContactPhoto(users):
  _processPeopleContactPhotos(users, 'deleteContactPhoto')

# gam update contactphotos <PeopleResourceNameEntity>|<PeopleUserContactSelection>
#	[drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]
def doUpdateDomainContactPhoto():
  _processPeopleContactPhotos(None, 'updateContactPhoto')

# gam get contactphotos <PeopleResourceNameEntity>|<PeopleUserContactSelection>
#	[drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
def doGetDomainContactPhoto():
  _processPeopleContactPhotos(None, 'getContactPhoto')

# gam delete contactphoto <PeopleResourceNameEntity>|<PeopleUserContactSelection>
def doDeleteDomainContactPhoto():
  _processPeopleContactPhotos(None, 'deleteContactPhoto')

# gam <UserTypeEntity> create contactgroup <ContactGroupAttribute>+
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
def createUserPeopleContactGroup(users):
  from gam.cmd.contacts import PeopleManager
  peopleManager = PeopleManager()
  entityType = Ent.USER
  parameters = {'csvPF': None, 'titles': ['User', 'resourceName'], 'addCSVData': {}, 'returnIdOnly': False}
  body, _ = peopleManager.GetContactGroupFields(parameters)
  if PEOPLE_GROUP_NAME not in body:
    return
  csvPF = parameters['csvPF']
  addCSVData = parameters['addCSVData']
  if addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
  returnIdOnly = parameters['returnIdOnly']
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    _, contactGroupNames = getPeopleContactGroupsInfo(people, entityType, user, i, count)
    if contactGroupNames is False:
      continue
    contactGroup = body[PEOPLE_GROUP_NAME]
    if contactGroup in contactGroupNames:
      entityActionFailedWarning([entityType, user], Ent.TypeNameMessage(Ent.CONTACT_GROUP, contactGroup, Msg.DUPLICATE), i, count)
      continue
    try:
      result = callGAPI(people.contactGroups(), 'create',
                        throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                        body={'contactGroup': body}, fields='resourceName')
      resourceName = result['resourceName']
      if returnIdOnly:
        writeStdout(f'{resourceName}\n')
      elif not csvPF:
        entityActionPerformed([entityType, user, Ent.CONTACT_GROUP, resourceName], i, count)
      else:
        row = {'User': user, 'resourceName': resourceName}
        if addCSVData:
          row.update(addCSVData)
        csvPF.WriteRow(row)
    except (GAPI.forbidden, GAPI.permissionDenied):
      userPeopleServiceNotEnabledWarning(user, i, count)
    except GAPI.serviceNotAvailable:
      entityUnknownWarning(entityType, user, i, count)
  if csvPF:
    csvPF.writeCSVfile('People Contact Groups')

# gam <UserTypeEntity> update contactgroups <ContactGroupItem> <ContactAttribute>+
def updateUserPeopleContactGroup(users):
  from gam.cmd.contacts import PeopleManager
  peopleManager = PeopleManager()
  entityType = Ent.USER
  entityList = getStringReturnInList(Cmd.OB_CONTACT_GROUP_ITEM)
  body, fields = peopleManager.GetContactGroupFields()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    contactGroupIDs = contactGroupNames = None
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems([entityType, user], jcount, Ent.CONTACT_GROUP, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contactGroup in entityList:
      j += 1
      try:
        groupId, contactGroupIDs, contactGroupNames = validatePeopleContactGroup(people, contactGroup,
                                                                                 contactGroupIDs, contactGroupNames, entityType, user, i, count)
        if not groupId:
          if contactGroupNames:
            entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup], Msg.DOES_NOT_EXIST, j, jcount)
            continue
          break
        result = callGAPI(people.contactGroups(), 'get',
                          bailOnInternalError=True,
                          throwReasons=[GAPI.NOT_FOUND, GAPI.INTERNAL_ERROR]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                          resourceName=groupId)
        body['etag'] = result['etag']
        newContactGroup = body.get(PEOPLE_GROUP_NAME)
        if newContactGroup:
          if newContactGroup in contactGroupNames and groupId not in contactGroupNames[newContactGroup]:
            entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup],
                                      Ent.TypeNameMessage(Ent.CONTACT_GROUP, newContactGroup, Msg.DUPLICATE), i, count)
            continue
        callGAPI(people.contactGroups(), 'update',
                 throwReasons=[GAPI.NOT_FOUND]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                 resourceName=groupId, body={'contactGroup': body, 'updateGroupFields': fields})
        entityActionPerformed([entityType, user, Ent.CONTACT_GROUP, contactGroup], j, jcount)
      except (GAPI.notFound, GAPI.internalError) as e:
        entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied):
        userPeopleServiceNotEnabledWarning(user, i, count)
        break
      except GAPI.serviceNotAvailable:
        entityUnknownWarning(entityType, user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> delete contactgroups <ContactGroupEntity>
def deleteUserPeopleContactGroups(users):
  entityType = Ent.USER
  entityList = getEntityList(Cmd.OB_CONTACT_GROUP_ENTITY, shlexSplit=True)
  contactGroupIdLists = entityList if isinstance(entityList, dict) else None
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if contactGroupIdLists:
      entityList = contactGroupIdLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    contactGroupIDs = contactGroupNames = None
    j = 0
    jcount = len(entityList)
    entityPerformActionNumItems([entityType, user], jcount, Ent.CONTACT_GROUP, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contactGroup in entityList:
      j += 1
      try:
        groupId, contactGroupIDs, contactGroupNames = validatePeopleContactGroup(people, contactGroup,
                                                                                 contactGroupIDs, contactGroupNames, entityType, user, i, count)
        if not groupId:
          if contactGroupNames:
            entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup], Msg.DOES_NOT_EXIST, j, jcount)
            continue
          break
        callGAPI(people.contactGroups(), 'delete',
                 throwReasons=[GAPI.NOT_FOUND]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                 resourceName=groupId)
        entityActionPerformed([entityType, user, Ent.CONTACT_GROUP, contactGroup], j, jcount)
      except GAPI.notFound as e:
        entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied):
        userPeopleServiceNotEnabledWarning(user, i, count)
        break
      except GAPI.serviceNotAvailable:
        entityUnknownWarning(entityType, user, i, count)
        break
    Ind.Decrement()

PEOPLE_GROUP_TIME_OBJECTS = {'updateTime'}

def _normalizeContactGroupMetadata(contactGroup):
  normalizedContactGroup = contactGroup.copy()
  for k, v in normalizedContactGroup.pop('metadata', {}).items():
    normalizedContactGroup[k] = v
  return normalizedContactGroup

def _showContactGroup(userEntityType, user, entityType, contactGroup, i, count, FJQC):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(contactGroup, timeObjects=PEOPLE_GROUP_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  normalizedContactGroup = _normalizeContactGroupMetadata(contactGroup)
  printEntity([userEntityType, user, entityType, contactGroup['resourceName']], i, count)
  Ind.Increment()
  showJSON(None, normalizedContactGroup, timeObjects=PEOPLE_GROUP_TIME_OBJECTS)
  Ind.Decrement()

def _printContactGroup(entityTypeName, user, contactGroup, csvPF, FJQC):
  normalizedContactGroup = _normalizeContactGroupMetadata(contactGroup)
  row = flattenJSON(normalizedContactGroup, flattened={entityTypeName: user}, timeObjects=PEOPLE_GROUP_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    csvPF.WriteRowNoFilter({entityTypeName: user, 'resourceName': contactGroup['resourceName'],
                            'JSON': json.dumps(cleanJSON(contactGroup, timeObjects=PEOPLE_GROUP_TIME_OBJECTS),
                                               ensure_ascii=False, sort_keys=True)})

PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP = {
  'clientdata': 'clientData',
  'grouptype': 'groupType',
  'membercount': 'memberCount',
  'metadata': 'metadata',
  'name': 'name',
  }

PEOPLE_CONTACTGROUPS_DEFAULT_FIELDS = ['name', 'metadata', 'grouptype', 'membercount']

# gam <UserTypeEntity> info contactgroups <PeopleContactGroupEntity>
#	[allfields|(fields <PeoplaContactGroupFieldList>)] [showmetadata]
#	[formatjson]
def infoUserPeopleContactGroups(users):
  entityType = Ent.USER
  entityList = getEntityList(Cmd.OB_CONTACT_GROUP_ENTITY, shlexSplit=True)
  contactGroupIdLists = entityList if isinstance(entityList, dict) else None
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getPersonFields(PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP, PEOPLE_CONTACTGROUPS_DEFAULT_FIELDS, fieldsList, parameters)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if contactGroupIdLists:
      entityList = contactGroupIdLists[user]
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    contactGroupIDs = contactGroupNames = None
    j = 0
    jcount = len(entityList)
    if not FJQC.formatJSON:
      entityPerformActionNumItems([entityType, user], jcount, Ent.CONTACT_GROUP, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    for contactGroup in entityList:
      j += 1
      try:
        groupId, contactGroupIDs, contactGroupNames = validatePeopleContactGroup(people, contactGroup,
                                                                                 contactGroupIDs, contactGroupNames, entityType, user, i, count)
        if not groupId:
          if contactGroupNames:
            entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup], Msg.DOES_NOT_EXIST, j, jcount)
            continue
          break
        group = callGAPI(people.contactGroups(), 'get',
                         throwReasons=[GAPI.NOT_FOUND]+GAPI.PEOPLE_ACCESS_THROW_REASONS,
                         resourceName=groupId, groupFields=fields)
        _showContactGroup(entityType, user, Ent.CONTACT_GROUP, group, j, jcount, FJQC)
      except GAPI.notFound as e:
        entityActionFailedWarning([entityType, user, Ent.CONTACT_GROUP, contactGroup], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied):
        userPeopleServiceNotEnabledWarning(user, i, count)
        break
      except GAPI.serviceNotAvailable:
        entityUnknownWarning(entityType, user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> print contactgroups [todrive <ToDriveAttribute>*]
#	[allfields|(fields <PeoplaContactGroupFieldList>)] [showmetadata]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show contactgroups
#	[allfields|(fields <PeoplaContactGroupFieldList>)] [showmetadata]
#	[formatjson]
def printShowUserPeopleContactGroups(users):
  entityType = Ent.USER
  entityTypeName = Ent.Singular(entityType)
  csvPF = CSVPrintFile([entityTypeName, 'resourceName'], 'sortall') if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  parameters = _initPersonMetadataParameters()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'allfields':
      fieldsList = None
    elif getPersonFieldsList(myarg, PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'showmetadata':
      parameters['strip'] = False
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = _getPersonFields(PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP, PEOPLE_CONTACTGROUPS_DEFAULT_FIELDS, fieldsList, parameters)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, people = buildGAPIServiceObject(API.PEOPLE, user, i, count)
    if not people:
      continue
    printGettingAllEntityItemsForWhom(Ent.PEOPLE_CONTACT_GROUP, user, i, count)
    try:
      entityList = callGAPIpages(people.contactGroups(), 'list', 'contactGroups',
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=GAPI.PEOPLE_ACCESS_THROW_REASONS,
                                 pageSize=GC.Values[GC.PEOPLE_MAX_RESULTS],
                                 groupFields=fields, fields='nextPageToken,contactGroups')
    except (GAPI.serviceNotAvailable, GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    _printPersonEntityList(Ent.PEOPLE_CONTACT_GROUP, entityList, entityType, user, i, count, csvPF, FJQC, parameters, None)
  if csvPF:
    csvPF.writeCSVfile('People Contact Groups')

# Delegate command utilities
