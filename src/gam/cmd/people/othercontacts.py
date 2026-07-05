"""GAM people commands."""

import re
import time
from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import entityUnknownWarning
from gam.util.api import ClientAPIAccessDeniedExit
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import writeGotMessage, callGAPI, callGAPIpages
from gam.util.args import checkForExtraneousArguments, getArgument, getREPattern, getString
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar
from gam.util.display import (
    TOTAL_ITEMS_MARKER,
    entityActionFailedWarning,
    entityActionPerformed,
    entityModifierNewValueActionPerformed,
    entityPerformActionModifierNumItems,
    getPageMessageForWhom,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    userPeopleServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument, getEntityList
from gam.util.errors import unknownArgumentExit
from gam.util.output import setSysExitRC
from gam.constants import NO_ENTITIES_FOUND_RC
from gam.cmd.contacts import (
    PEOPLE_MEMBERSHIPS,
    PEOPLE_READ_SOURCES_CHOICE_MAP,
    PeopleManager,
    normalizeOtherContactsResourceName,
)
from gam.cmd.people.core import (
    PEOPLE_GROUPS_LIST,
    _getPersonFields,
    _initPersonMetadataParameters,
    countLocalPeopleContactSelects,
    getPersonFieldsList,
    localPeopleContactSelects,
)
from gam.cmd.people.core import (
    CONTACTGROUPS_MYCONTACTS_ID,
    CONTACTGROUPS_MYCONTACTS_NAME,
    PEOPLE_CONTACTS_DEFAULT_FIELDS,
    PEOPLE_OTHERCONTACT_SELECT_ARGUMENTS,
    PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP,
)
from gam.cmd.people.domainprofiles import _printPersonEntityList
from gam.cmd.people.contacts import validatePeopleContactGroupsList


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

def copyUserPeopleOtherContacts(users):
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

