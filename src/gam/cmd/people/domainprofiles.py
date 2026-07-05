"""GAM people commands."""

import json
from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import getArgument, getChoice, getString
from gam.util.csv_pf import (
    CSVPrintFile, FormatJSONQuoteChar, addFieldToFieldsList,
    _getFieldsList, cleanJSON, flattenJSON, getFieldsList
)
from gam.util.display import entityActionFailedWarning, printEntity, printLine
from gam.util.entity import getEntityArgument, getEntityList
from gam.util.errors import deprecatedArgument, invalidChoiceExit
from gam.util.output import setSysExitRC, formatLocalTime
from gam.constants import NO_ENTITIES_FOUND_RC
from gam.cmd.contacts import normalizePeopleResourceName
from gam.cmd.people import (
    PEOPLE_CONTACTS_DEFAULT_FIELDS,
    PEOPLE_CONTACT_OBJECT_KEYS,
    PEOPLE_FIELDS_CHOICE_MAP,
    PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP,
)


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

def _printPerson(entityTypeName, user, person, csvPF, FJQC, parameters):
  _processPersonMetadata(person, parameters)
  row = flattenJSON(person, flattened={entityTypeName: user})
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    csvPF.WriteRowNoFilter({entityTypeName: user, 'resourceName': person['resourceName'],
                            'JSON': json.dumps(cleanJSON(person),
                                               ensure_ascii=False, sort_keys=True)})

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
  """Print information about domain people profiles."""
  _infoPeople([GC.Values[GC.DOMAIN]], Ent.DOMAIN, 'profile')

# gam info peoplecontact <PeopleResourceNameEntity>
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[formatjson]
def doPrintShowDomainPeopleProfiles():
  """Print or show a list of domain people profiles."""
  _printShowPeople('profile')

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

