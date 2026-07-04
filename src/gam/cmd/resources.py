"""GAM buildings, features, and resource calendar management."""

import json
import uuid

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit, entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    LANGUAGE_CODES_MAP,
    UID_PATTERN,
    checkForExtraneousArguments,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getFloat,
    getInteger,
    getLanguageCode,
    getString,
    getStringReturnInList,
    getStringWithCRsNLs,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    cleanJSON,
    flattenJSON,
    getFieldsList,
    getItemFieldsFromFieldsList,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityDuplicateWarning,
    getPageMessage,
    performActionNumItems,
    printEntitiesCount,
    printEntity,
    printGettingAllAccountEntities,
    printKeyValueList,
    printKeyValueListWithCount,
    printKeyValueWithCRsNLs,
    printLine,
    userCalServiceNotEnabledWarning,
)
from gam.util.entity import getEntityList, shlexSplitList
from gam.util.errors import entityDoesNotExistExit, invalidChoiceExit, unknownArgumentExit, usageErrorExit
from gam.util.output import printErrorMessage, writeStdout
from gam.constants import BUILDING_ADDRESS_FIELD_MAP
from gam.cmd.calendar import _showCalendarSettings


def _getBuildingAttributes(body):
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'id':
      body['buildingId'] = getString(Cmd.OB_BUILDING_ID, maxLen=100)
    elif myarg == 'name':
      body['buildingName'] = getString(Cmd.OB_STRING, maxLen=100)
    elif myarg in {'lat', 'latitude'}:
      body.setdefault('coordinates', {})
      body['coordinates']['latitude'] = getFloat(minVal=-180.0, maxVal=180.0)
    elif myarg in {'long', 'lng', 'longitude'}:
      body.setdefault('coordinates', {})
      body['coordinates']['longitude'] = getFloat(minVal=-180.0, maxVal=180.0)
    elif myarg == 'description':
      body['description'] = getString(Cmd.OB_STRING)
    elif myarg == 'floors':
      body['floorNames'] = getString(Cmd.OB_STRING).split(',')
    elif myarg in BUILDING_ADDRESS_FIELD_MAP:
      myarg = BUILDING_ADDRESS_FIELD_MAP[myarg]
      body.setdefault('address', {})
      if myarg == 'addressLines':
        body['address'][myarg] = getStringWithCRsNLs().split('\n')
      elif myarg == 'languageCode':
        body['address'][myarg] = getLanguageCode(LANGUAGE_CODES_MAP)
      else:
        body['address'][myarg] = getString(Cmd.OB_STRING, minLen=0)
    else:
      unknownArgumentExit()
  return body

# gam create building <Name> <BuildingAttribute>*
def doCreateBuilding():
  cd = buildGAPIObject(API.DIRECTORY)
  body = _getBuildingAttributes({'buildingId': str(uuid.uuid4()),
                                 'buildingName': getString(Cmd.OB_NAME, maxLen=100),
                                 'floorNames': ['1']})
  try:
    callGAPI(cd.resources().buildings(), 'insert',
             throwReasons=[GAPI.DUPLICATE, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
             customer=GC.Values[GC.CUSTOMER_ID], body=body)
    entityActionPerformed([Ent.BUILDING_ID, body['buildingId'], Ent.BUILDING, body['buildingName']])
  except GAPI.duplicate:
    entityDuplicateWarning([Ent.BUILDING_ID, body['buildingId'], Ent.BUILDING, body['buildingName']])
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.BUILDING_ID, body['buildingId'], Ent.BUILDING, body['buildingName']], str(e))
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

def _makeBuildingIdNameMap(cd=None):
  GM.Globals[GM.MAKE_BUILDING_ID_NAME_MAP] = False
  if cd is None:
    cd = buildGAPIObject(API.DIRECTORY)
  try:
    buildings = callGAPIpages(cd.resources().buildings(), 'list', 'buildings',
                              throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                              customer=GC.Values[GC.CUSTOMER_ID],
                              fields='nextPageToken,buildings(buildingId,buildingName)')
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)
  for building in buildings:
    GM.Globals[GM.MAP_BUILDING_ID_TO_NAME][building['buildingId']] = building['buildingName']
    GM.Globals[GM.MAP_BUILDING_NAME_TO_ID][building['buildingName']] = building['buildingId']

def _getBuildingByNameOrId(cd, minLen=1, allowNV=False):
  which_building = getString(Cmd.OB_BUILDING_ID, minLen=minLen)
  if not which_building or (minLen == 0 and which_building in {'id:', 'uid:'}):
    return ''
  cg = UID_PATTERN.match(which_building)
  if cg:
    return cg.group(1)
  if allowNV and which_building.startswith('nv:'):
    return which_building[3:]
  if GM.Globals[GM.MAKE_BUILDING_ID_NAME_MAP]:
    _makeBuildingIdNameMap(cd)
# Exact name match, return ID
  if which_building in GM.Globals[GM.MAP_BUILDING_NAME_TO_ID]:
    return GM.Globals[GM.MAP_BUILDING_NAME_TO_ID][which_building]
# No exact name match, check for case insensitive name matches
  which_building_lower = which_building.lower()
  ci_matches = []
  for buildingName, buildingId in GM.Globals[GM.MAP_BUILDING_NAME_TO_ID].items():
    if buildingName.lower() == which_building_lower:
      ci_matches.append({'buildingName': buildingName, 'buildingId': buildingId})
# One match, return ID
  if len(ci_matches) == 1:
    return ci_matches[0]['buildingId']
# No or multiple name matches, try ID
# Exact ID match, return ID
  if which_building in GM.Globals[GM.MAP_BUILDING_ID_TO_NAME]:
    return which_building
# No exact ID match, check for case insensitive id match
  for buildingId in GM.Globals[GM.MAP_BUILDING_ID_TO_NAME]:
# Match, return ID
    if buildingId.lower() == which_building_lower:
      return buildingId
# Multiple name  matches
  if len(ci_matches) > 1:
    printErrorMessage(1, Msg.MULTIPLE_BUILDINGS_SAME_NAME.format(len(ci_matches), Ent.Plural(Ent.BUILDING)))
    Ind.Increment()
    for building in ci_matches:
      printEntity([Ent.BUILDING, building['buildingName'], Ent.BUILDING_ID, building['buildingId']])
    Ind.Decrement()
    Cmd.Backup()
    usageErrorExit(Msg.PLEASE_SPECIFY_BUILDING_EXACT_CASE_NAME_OR_ID)
# No matches
  entityDoesNotExistExit(Ent.BUILDING, which_building)

def _getBuildingNameById(cd, buildingId):
  if GM.Globals[GM.MAKE_BUILDING_ID_NAME_MAP]:
    _makeBuildingIdNameMap(cd)
  return GM.Globals[GM.MAP_BUILDING_ID_TO_NAME].get(buildingId, buildingId)

# gam update building <BuildIngID> <BuildingAttribute>*
def doUpdateBuilding():
  cd = buildGAPIObject(API.DIRECTORY)
  buildingId = _getBuildingByNameOrId(cd)
  body = _getBuildingAttributes({})
  try:
    callGAPI(cd.resources().buildings(), 'patch',
             throwReasons=[GAPI.DUPLICATE, GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
             customer=GC.Values[GC.CUSTOMER_ID], buildingId=buildingId, body=body)
    entityActionPerformed([Ent.BUILDING_ID, buildingId])
  except GAPI.duplicate:
    entityDuplicateWarning([Ent.BUILDING, body['buildingName']])
  except GAPI.resourceNotFound:
    entityUnknownWarning(Ent.BUILDING_ID, buildingId)
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.BUILDING_ID, buildingId], str(e))
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

# gam delete building <BuildIngID>
def doDeleteBuilding():
  cd = buildGAPIObject(API.DIRECTORY)
  buildingId = _getBuildingByNameOrId(cd)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.resources().buildings(), 'delete',
             throwReasons=[GAPI.RESOURCE_NOT_FOUND, GAPI.CONDITION_NOT_MET,
                           GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
             customer=GC.Values[GC.CUSTOMER_ID], buildingId=buildingId)
    entityActionPerformed([Ent.BUILDING_ID, buildingId])
  except GAPI.resourceNotFound:
    entityUnknownWarning(Ent.BUILDING_ID, buildingId)
  except GAPI.conditionNotMet as e:
    entityActionFailedWarning([Ent.BUILDING_ID, buildingId], str(e))
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

BUILDING_ADDRESS_PRINT_ORDER = ['addressLines', 'sublocality', 'locality', 'administrativeArea', 'postalCode', 'regionCode', 'languageCode']

def _showBuilding(building, delimiter=',', i=0, count=0, FJQC=None):
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(building), ensure_ascii=False, sort_keys=True))
    return
  if 'buildingName' in building:
    printEntity([Ent.BUILDING, building['buildingName']], i, count)
    Ind.Increment()
    printKeyValueList(['buildingId', f'id:{building["buildingId"]}'])
  else:
    printEntity([Ent.BUILDING_ID, f'id:{building["buildingId"]}'], i, count)
    Ind.Increment()
  if 'description' in building:
    printKeyValueList(['description', building['description']])
  if 'floorNames' in building:
    printKeyValueList(['floorNames', delimiter.join(building['floorNames'])])
  if 'coordinates' in building:
    printKeyValueList(['coordinates', None])
    Ind.Increment()
    printKeyValueList(['latitude', f'{building["coordinates"].get("latitude", 0):4.7f}'])
    printKeyValueList(['longitude', f'{building["coordinates"].get("longitude", 0):4.7f}'])
    Ind.Decrement()
  if 'address' in building:
    printKeyValueList(['address', None])
    Ind.Increment()
    for field in BUILDING_ADDRESS_PRINT_ORDER:
      if field in building['address']:
        if field != 'addressLines':
          printKeyValueList([field, building['address'][field]])
        else:
          printKeyValueList([field, None])
          Ind.Increment()
          for line in building['address'][field]:
            printKeyValueList([line])
          Ind.Decrement()
    Ind.Decrement()
  Ind.Decrement()

# gam info building <BuildingID>
#	[formatjson]
def doInfoBuilding():
  cd = buildGAPIObject(API.DIRECTORY)
  buildingId = _getBuildingByNameOrId(cd)
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  try:
    building = callGAPI(cd.resources().buildings(), 'get',
                        throwReasons=[GAPI.RESOURCE_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                        customer=GC.Values[GC.CUSTOMER_ID], buildingId=buildingId)
    _showBuilding(building, FJQC=FJQC)
  except GAPI.resourceNotFound:
    entityUnknownWarning(Ent.BUILDING_ID, buildingId)
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

BUILDINGS_FIELDS_CHOICE_MAP = {
  'address': 'address',
  'buildingid': 'buildingId',
  'buildingname': 'buildingName',
  'coordinates': 'coordinates',
  'description': 'description',
  'floors': 'floorNames',
  'floornames': 'floorNames',
  'id': 'buildingId',
  'name': 'buildingName',
  }
BUILDINGS_SORT_TITLES = ['buildingId', 'buildingName', 'description', 'floorNames']

# gam print buildings [todrive <ToDriveAttribute>*]
#	[allfields|<BuildingFildName>*|(fields <BuildingFieldNameList>)]
#	[delimiter <Character>] [formatjson [quotechar <Character>]]
# gam show buildings
#	[allfields|<BuildingFildName>*|(fields <BuildingFieldNameList>)]
#	[formatjson]
def doPrintShowBuildings():
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['buildingId'], BUILDINGS_SORT_TITLES) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER] if csvPF else ','
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'allfields':
      fieldsList = []
    elif getFieldsList(myarg, BUILDINGS_FIELDS_CHOICE_MAP, fieldsList, initialField='buildingId'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = getItemFieldsFromFieldsList('buildings', fieldsList)
  try:
    buildings = callGAPIpages(cd.resources().buildings(), 'list', 'buildings',
                              throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                              customer=GC.Values[GC.CUSTOMER_ID], fields=fields)
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)
  if not csvPF:
    jcount = len(buildings)
    performActionNumItems(jcount, Ent.BUILDING)
    Ind.Increment()
    j = 0
    for building in buildings:
      j += 1
      _showBuilding(building, delimiter, j, jcount, FJQC)
    Ind.Decrement()
  else:
    for building in buildings:
      if 'buildingId' in building:
        building['buildingId'] = f'id:{building["buildingId"]}'
      if 'floorNames' in building:
        building['floorNames'] = delimiter.join(building['floorNames'])
      if 'address' in building and 'addressLines' in building['address']:
        building['address']['addressLines'] = '\n'.join(building['address']['addressLines'])
      if 'coordinates' in building:
        building['coordinates']['latitude'] = f'{building["coordinates"].get("latitude", 0):4.7f}'
        building['coordinates']['longitude'] = f'{building["coordinates"].get("longitude", 0):4.7f}'
      row = flattenJSON(building)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      else:
        if (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'buildingId': building['buildingId'],
                                  'JSON': json.dumps(cleanJSON(building), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Buildings')

def _getFeatureAttributes(body):
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      body['name'] = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  return body

# gam create feature name <Name>
def doCreateFeature():
  cd = buildGAPIObject(API.DIRECTORY)
  body = _getFeatureAttributes({})
  try:
    callGAPI(cd.resources().features(), 'insert',
             throwReasons=[GAPI.DUPLICATE, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
             customer=GC.Values[GC.CUSTOMER_ID], body=body)
    entityActionPerformed([Ent.FEATURE, body['name']])
  except GAPI.duplicate:
    entityDuplicateWarning([Ent.FEATURE, body['name']])
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.FEATURE, body['name']], str(e))
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

#gam update feature <Name> name <Name>
def doUpdateFeature():
  # update does not work for name and name is only field to be updated
  # if additional writable fields are added to feature in the future
  # we'll add support for update as well as rename
  cd = buildGAPIObject(API.DIRECTORY)
  oldName = getString(Cmd.OB_STRING)
  getChoice(['name'])
  body = {'newName': getString(Cmd.OB_STRING)}
  checkForExtraneousArguments()
  try:
    callGAPI(cd.resources().features(), 'rename',
             throwReasons=[GAPI.DUPLICATE, GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
             customer=GC.Values[GC.CUSTOMER_ID], oldName=oldName, body=body)
    entityActionPerformed([Ent.FEATURE, oldName])
  except GAPI.duplicate:
    entityDuplicateWarning([Ent.FEATURE, body['newName']])
  except GAPI.resourceNotFound:
    entityUnknownWarning(Ent.FEATURE, oldName)
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.FEATURE, oldName], str(e))
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

# gam delete feature <Name>
def doDeleteFeature():
  cd = buildGAPIObject(API.DIRECTORY)
  featureKey = getString(Cmd.OB_NAME)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.resources().features(), 'delete',
             throwReasons=[GAPI.RESOURCE_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
             customer=GC.Values[GC.CUSTOMER_ID], featureKey=featureKey)
    entityActionPerformed([Ent.FEATURE, featureKey])
  except GAPI.resourceNotFound:
    entityUnknownWarning(Ent.FEATURE, featureKey)
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)

FEATURE_FIELDS_CHOICE_MAP = {
  'name': 'name',
  }

# gam print features [todrive <ToDriveAttribute>*]
# gam show features
def doPrintShowFeatures():
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile('name') if Act.csvFormat() else None
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'allfields':
      fieldsList = []
    elif getFieldsList(myarg, FEATURE_FIELDS_CHOICE_MAP, fieldsList):
      pass
    else:
      unknownArgumentExit()
  fields = getItemFieldsFromFieldsList('features', fieldsList)
  try:
    features = callGAPIpages(cd.resources().features(), 'list', 'features',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                             customer=GC.Values[GC.CUSTOMER_ID], fields=fields)
  except (GAPI.badRequest, GAPI.notFound, GAPI.forbidden):
    accessErrorExit(cd)
  if not csvPF:
    jcount = len(features)
    performActionNumItems(jcount, Ent.FEATURE)
    Ind.Increment()
    j = 0
    for feature in features:
      j += 1
      printEntity([Ent.FEATURE, feature['name']], j, jcount)
  else:
    for feature in features:
      csvPF.WriteRowTitles(flattenJSON(feature))
  if csvPF:
    csvPF.writeCSVfile('Features')

RESOURCE_CATEGORY_MAP = {
  'conference': 'CONFERENCE_ROOM',
  'conferenceroom': 'CONFERENCE_ROOM',
  'room': 'CONFERENCE_ROOM',
  'other': 'OTHER',
  'categoryunknown': 'CATEGORY_UNKNOWN',
  'unknown': 'CATEGORY_UNKNOWN',
  }

def _getResourceCalendarAttributes(cd, body, updateMode):
  autoAcceptInvitations = None
  featureChanges = {'add': set(), 'remove': set()}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'name', 'resourcename'}:
      body['resourceName'] = getString(Cmd.OB_STRING)
    elif myarg in {'description', 'resourcedescription'}:
      body['resourceDescription'] = getStringWithCRsNLs()
    elif myarg in {'type', 'resourcetype'}:
      body['resourceType'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'building', 'buildingid'}:
      body['buildingId'] = _getBuildingByNameOrId(cd, minLen=0)
    elif myarg == 'capacity':
      body['capacity'] = getInteger(minVal=0)
    elif myarg in {'feature', 'features', 'featureinstances'}:
      body.setdefault('featureInstances', [])
      for feature in shlexSplitList(getString(Cmd.OB_STRING, minLen=0)):
        body['featureInstances'].append({'feature': {'name': feature}})
    elif myarg in {'addfeature', 'addfeatures', 'addfeatureinstances'}:
      if not updateMode:
        body.setdefault('featureInstances', [])
        for feature in shlexSplitList(getString(Cmd.OB_STRING, minLen=0)):
          body['featureInstances'].append({'feature': {'name': feature}})
      else:
        for feature in shlexSplitList(getString(Cmd.OB_STRING, minLen=0)):
          featureChanges['add'].add(feature)
    elif updateMode and myarg in {'removefeature', 'removefeatures', 'removefeatureinstances'}:
      for feature in shlexSplitList(getString(Cmd.OB_STRING, minLen=0)):
        featureChanges['remove'].add(feature)
    elif myarg in {'floor', 'floorname'}:
      body['floorName'] = getString(Cmd.OB_STRING)
    elif myarg == 'floorsection':
      body['floorSection'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'category', 'resourcecategory'}:
      body['resourceCategory'] = getChoice(RESOURCE_CATEGORY_MAP, mapChoice=True)
    elif myarg in {'userdescription', 'uservisibledescription'}:
      body['userVisibleDescription'] = getString(Cmd.OB_STRING)
    elif myarg == 'autoacceptinvitations':
      autoAcceptInvitations = getBoolean()
    else:
      unknownArgumentExit()
  if ('featureInstances' in body and not body['featureInstances'] and
      not featureChanges['add'] and not featureChanges['remove']):
    body['featureInstances'] = [{}]
  if not updateMode:
    return body, autoAcceptInvitations, None
  return body, autoAcceptInvitations, featureChanges

def updateAutoAcceptInvitations(cal, calId, autoAcceptInvitations, i=0, count=0):
  Ind.Increment()
  try:
    callGAPI(cal.calendars(), 'patch',
             throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
             calendarId=calId, body={'autoAcceptInvitations': autoAcceptInvitations})
    entityActionPerformed([Ent.CALENDAR, calId], i, count)
  except (GAPI.notFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CALENDAR, calId], str(e), i, count)
  except GAPI.notACalendarUser:
    userCalServiceNotEnabledWarning(calId, i, count)
  Ind.Decrement()

# gam create resource <ResourceID> <Name> <ResourceAttribute>*
def doCreateResourceCalendar():
  cd = buildGAPIObject(API.DIRECTORY)
  body, autoAcceptInvitations, _ = _getResourceCalendarAttributes(cd, {'resourceId': getString(Cmd.OB_RESOURCE_ID), 'resourceName': getString(Cmd.OB_NAME)}, False)
  if autoAcceptInvitations is not None:
    cal = buildGAPIObject(API.CALENDAR)
  try:
    result = callGAPI(cd.resources().calendars(), 'insert',
                      throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.SERVICE_NOT_AVAILABLE,
                                    GAPI.REQUIRED, GAPI.DUPLICATE, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      customer=GC.Values[GC.CUSTOMER_ID], body=body, fields='resourceEmail')
    entityActionPerformed([Ent.RESOURCE_CALENDAR, body['resourceId']])
    if autoAcceptInvitations is not None:
      updateAutoAcceptInvitations(cal, result['resourceEmail'], autoAcceptInvitations)
  except (GAPI.invalid, GAPI.invalidInput, GAPI.serviceNotAvailable) as e:
    entityActionFailedWarning([Ent.RESOURCE_CALENDAR, body['resourceId']], str(e))
  except GAPI.required as e:
    errMsg = str(e)
    if '[resourceCapacity, resourceFloorName]' in errMsg:
      entityActionFailedWarning([Ent.RESOURCE_CALENDAR, body['resourceId']], Msg.RESOURCE_CAPACITY_FLOOR_REQUIRED)
    elif'[resourceFloorName]' in errMsg:
      entityActionFailedWarning([Ent.RESOURCE_CALENDAR, body['resourceId']], Msg.RESOURCE_FLOOR_REQUIRED)
    else:
      entityActionFailedWarning([Ent.RESOURCE_CALENDAR, body['resourceId']], errMsg)
  except GAPI.duplicate:
    entityDuplicateWarning([Ent.RESOURCE_CALENDAR, body['resourceId']])
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    accessErrorExit(cd)

def _doUpdateResourceCalendars(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  body, autoAcceptInvitations, featureChanges = _getResourceCalendarAttributes(cd, {}, True)
  if autoAcceptInvitations is not None:
    cal = buildGAPIObject(API.CALENDAR)
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      if autoAcceptInvitations is not None  or featureChanges['add'] or featureChanges['remove']:
        result = callGAPI(cd.resources().calendars(), 'get',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.FORBIDDEN],
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId, fields='resourceEmail,featureInstances(feature(name))')
        bodyFeatures = body.pop('featureInstances', [])
        body['featureInstances'] = []
        featureSet = set()
        for feature in bodyFeatures:
          featureName = feature['feature']['name']
          if featureName not in featureChanges['remove'] and featureName not in featureSet:
            body['featureInstances'].append({'feature': {'name': featureName}})
            featureSet.add(featureName)
        for feature in result.get('featureInstances', []):
          featureName = feature['feature']['name']
          if featureName not in featureChanges['remove'] and featureName not in featureSet:
            body['featureInstances'].append({'feature': {'name': featureName}})
            featureSet.add(featureName)
        for featureName in featureChanges['add']:
          if featureName not in featureChanges['remove'] and featureName not in featureSet:
            body['featureInstances'].append({'feature': {'name': featureName}})
            featureSet.add(featureName)
        if not body['featureInstances']:
          body['featureInstances'] = [{}]
      callGAPI(cd.resources().calendars(), 'patch',
               throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.SERVICE_NOT_AVAILABLE, GAPI.REQUIRED,
                             GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId, body=body, fields='')
      entityActionPerformed([Ent.RESOURCE_CALENDAR, resourceId], i, count)
      if autoAcceptInvitations is not None:
        updateAutoAcceptInvitations(cal, result['resourceEmail'], autoAcceptInvitations, i, count)
    except (GAPI.invalid, GAPI.invalidInput, GAPI.serviceNotAvailable, GAPI.required)  as e:
      entityActionFailedWarning([Ent.RESOURCE_CALENDAR, resourceId], str(e), i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)

# gam update resources <ResourceEntity> <ResourceAttribute>*
def doUpdateResourceCalendars():
  _doUpdateResourceCalendars(getEntityList(Cmd.OB_RESOURCE_ENTITY))

# gam update resource <ResourceID> <ResourceAttribute>*
def doUpdateResourceCalendar():
  _doUpdateResourceCalendars(getStringReturnInList(Cmd.OB_RESOURCE_ID))

def _doDeleteResourceCalendars(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      callGAPI(cd.resources().calendars(), 'delete',
               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId)
      entityActionPerformed([Ent.RESOURCE_CALENDAR, resourceId], i, count)
    except GAPI.serviceNotAvailable as e:
      entityActionFailedWarning([Ent.RESOURCE_CALENDAR, resourceId], str(e), i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)

# gam delete resources <ResourceEntity>
def doDeleteResourceCalendars():
  _doDeleteResourceCalendars(getEntityList(Cmd.OB_RESOURCE_ENTITY))

# gam delete resource <ResourceID>
def doDeleteResourceCalendar():
  _doDeleteResourceCalendars(getStringReturnInList(Cmd.OB_RESOURCE_ID))

def _getResourceACLsCalSettings(cal, resource, getCalSettings, getCalPermissions, i, count):
  calId = resource['resourceEmail']
  try:
    if getCalPermissions:
      acls = callGAPIpages(cal.acl(), 'list', 'items',
                           throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.AUTH_ERROR],
                           calendarId=calId, fields='nextPageToken,items(id,role,scope)')
    else:
      acls = {}
    if getCalSettings:
      settings = callGAPI(cal.calendars(), 'get',
                          throwReasons=GAPI.CALENDAR_THROW_REASONS+[GAPI.NOT_FOUND],
                          calendarId=calId)
      settings.pop('etag', None)
      settings.pop('kind', None)
      resource.update({'calendar': settings})
    return (True, acls)
  except (GAPI.forbidden, GAPI.serviceNotAvailable, GAPI.authError, GAPI.notACalendarUser) as e:
    entityActionFailedWarning([Ent.RESOURCE_CALENDAR, calId], str(e), i, count)
  except GAPI.notFound:
    entityUnknownWarning(Ent.RESOURCE_CALENDAR, calId, i, count)
  return (False, None)

RESOURCE_DFLT_FIELDS = ['resourceId', 'resourceName', 'resourceEmail', 'resourceDescription', 'resourceType']
RESOURCE_ADDTL_FIELDS = [
  'buildingId',	# buildingId must be first element
  'capacity',
  'featureInstances',
  'floorName',
  'floorSection',
  'generatedResourceName',
  'resourceCategory',
  'userVisibleDescription',
  ]
RESOURCE_ALL_FIELDS = RESOURCE_DFLT_FIELDS+RESOURCE_ADDTL_FIELDS
RESOURCE_FIELDS_WITH_CRS_NLS = {'resourceDescription'}

def _showResource(cd, resource, i, count, FJQC, acls=None, noSelfOwner=False):

  from gam.cmd.calendar import ACLRuleKeyValueList
  def _showResourceField(title, resource, field):
    if field in resource:
      if field not in RESOURCE_FIELDS_WITH_CRS_NLS:
        printKeyValueList([title, resource[field]])
      else:
        printKeyValueWithCRsNLs(title, resource[field])

  if 'buildingId' in resource:
    resource['buildingName'] = _getBuildingNameById(cd, resource['buildingId'])
    resource['buildingId'] = f'id:{resource["buildingId"]}'
  if FJQC.formatJSON:
    if acls:
      resource['acls'] = [{'id': rule['id'], 'role': rule['role']} for rule in acls]
    printLine(json.dumps(cleanJSON(resource), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.RESOURCE_ID, resource['resourceId']], i, count)
  Ind.Increment()
  _showResourceField('Name', resource, 'resourceName')
  _showResourceField('Email', resource, 'resourceEmail')
  _showResourceField('Type', resource, 'resourceType')
  _showResourceField('Description', resource, 'resourceDescription')
  if 'featureInstances' in resource:
    resource['featureInstances'] = ', '.join([a_feature['feature']['name'] for a_feature in resource.pop('featureInstances')])
  if 'buildingId' in resource:
    _showResourceField('buildingId', resource, 'buildingId')
    _showResourceField('buildingName', resource, 'buildingName')
  for field in RESOURCE_ADDTL_FIELDS[1:]:
    _showResourceField(field, resource, field)
  calendar = resource.get('calendar')
  if calendar:
    _showCalendarSettings(calendar, 0, 0)
  if acls:
    j = 0
    jcount = len(acls)
    printEntitiesCount(Ent.CALENDAR_ACL, acls)
    Ind.Increment()
    for rule in acls:
      j += 1
      if noSelfOwner and rule['role'] == 'owner' and rule['scope']['value'] == resource['resourceEmail']:
        continue
      printKeyValueListWithCount(ACLRuleKeyValueList(rule), j, jcount)
    Ind.Decrement()
  Ind.Decrement()

def _doInfoResourceCalendars(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  getCalSettings = getCalPermissions = noSelfOwner = False
  FJQC = FormatJSONQuoteChar()
  acls = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in [Cmd.ARG_ACLS, Cmd.ARG_CALENDARACLS, Cmd.ARG_PERMISSIONS]:
      getCalPermissions = True
    elif myarg == 'noselfowner':
      noSelfOwner = True
    elif myarg == Cmd.ARG_CALENDAR:
      getCalSettings = True
    else:
      FJQC.GetFormatJSON(myarg)
  if getCalSettings or getCalPermissions:
    cal = buildGAPIObject(API.CALENDAR)
  fields = ','.join(RESOURCE_ALL_FIELDS)
  i = 0
  count = len(entityList)
  for resourceId in entityList:
    i += 1
    try:
      resource = callGAPI(cd.resources().calendars(), 'get',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                          customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId, fields=fields)
      if getCalSettings or getCalPermissions:
        status, acls = _getResourceACLsCalSettings(cal, resource, getCalSettings, getCalPermissions, i, count)
        if not status:
          continue
      _showResource(cd, resource, i, count, FJQC, acls, noSelfOwner)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)

# gam info resources <ResourceEntity>
#	[acls] [noselfowner] [calendar] [formatjson]
def doInfoResourceCalendars():
  _doInfoResourceCalendars(getEntityList(Cmd.OB_RESOURCE_ENTITY))

# gam info resource <ResourceID>
#	[acls] [noselfowner] [calendar] [formatjson]
def doInfoResourceCalendar():
  _doInfoResourceCalendars(getStringReturnInList(Cmd.OB_RESOURCE_ID))

RESOURCE_FIELDS_CHOICE_MAP = {
  'description': 'resourceDescription',
  'building': 'buildingId',
  'buildingid': 'buildingId',
  'capacity': 'capacity',
  'category': 'resourceCategory',
  'email': 'resourceEmail',
  'feature': 'featureInstances',
  'features': 'featureInstances',
  'featureinstances': 'featureInstances',
  'floor': 'floorName',
  'floorname': 'floorName',
  'floorsection': 'floorSection',
  'generatedresourcename': 'generatedResourceName',
  'id': 'resourceId',
  'name': 'resourceName',
  'resourcecategory': 'resourceCategory',
  'resourcedescription': 'resourceDescription',
  'resourceemail': 'resourceEmail',
  'resourceid': 'resourceId',
  'resourcename': 'resourceName',
  'resourcetype': 'resourceType',
  'type': 'resourceType',
  'userdescription': 'userVisibleDescription',
  'uservisibledescription': 'userVisibleDescription',
  }

# gam show resources
#	[allfields|<ResourceFieldName>*|(fields <ResourceFieldNameList>)]
#	[query <String>]
#	[acls] [noselfowner] [calendar] [convertcrnl] [formatjson]
# gam print resources [todrive <ToDriveAttribute>*]
#	[allfields|<ResourceFieldName>*|(fields <ResourceFieldNameList>)]
#	[query <String>]
#	[acls] [noselfowner] [calendar] [convertcrnl] [formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintShowResourceCalendars():
  cd = buildGAPIObject(API.DIRECTORY)
  convertCRNL = GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]
  getCalSettings = getCalPermissions = noSelfOwner = False
  acls = query = None
  fieldsList = []
  csvPF = CSVPrintFile() if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'query':
      query = getString(Cmd.OB_QUERY)
    elif myarg == 'allfields':
      fieldsList = RESOURCE_ALL_FIELDS[:]
    elif myarg in [Cmd.ARG_ACLS, Cmd.ARG_CALENDARACLS, Cmd.ARG_PERMISSIONS]:
      getCalPermissions = True
    elif myarg == 'noselfowner':
      noSelfOwner = True
    elif myarg == Cmd.ARG_CALENDAR:
      getCalSettings = True
    elif myarg in RESOURCE_FIELDS_CHOICE_MAP:
      if not fieldsList:
        fieldsList = ['resourceId']
      fieldsList.append(RESOURCE_FIELDS_CHOICE_MAP[myarg])
    elif myarg == 'fields':
      if not fieldsList:
        fieldsList = ['resourceId']
      for field in _getFieldsList():
        if field in [Cmd.ARG_ACLS, Cmd.ARG_CALENDARACLS, Cmd.ARG_PERMISSIONS]:
          getCalPermissions = True
        elif field == Cmd.ARG_CALENDAR:
          getCalSettings = True
        elif field in RESOURCE_FIELDS_CHOICE_MAP:
          fieldsList.append(RESOURCE_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, RESOURCE_FIELDS_CHOICE_MAP, True)
    elif myarg in {'convertcrnl', 'converttextnl'}:
      convertCRNL = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not fieldsList:
    fieldsList = RESOURCE_DFLT_FIELDS[:]
  if getCalSettings or getCalPermissions:
    cal = buildGAPIObject(API.CALENDAR)
    fields = getItemFieldsFromFieldsList('items', fieldsList+['resourceEmail'])
  else:
    fields = getItemFieldsFromFieldsList('items', fieldsList)
  if 'buildingId' in fieldsList:
    fieldsList.append('buildingName')
  if csvPF:
    if not FJQC.formatJSON:
      csvPF.AddTitles(fieldsList)
      csvPF.SetSortTitles(RESOURCE_DFLT_FIELDS)
    else:
      if 'resourceName' in fieldsList:
        sortTitles = ['resourceId', 'resourceName', 'JSON']
      else:
        sortTitles = ['resourceId', 'JSON']
      csvPF.AddJSONTitles(sortTitles)
  printGettingAllAccountEntities(Ent.RESOURCE_CALENDAR)
  try:
    resources = callGAPIpages(cd.resources().calendars(), 'list', 'items',
                              pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='resourceName',
                              throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN,
                                            GAPI.PERMISSION_DENIED, GAPI.INVALID_INPUT],
                              query=query, customer=GC.Values[GC.CUSTOMER_ID], fields=fields)
  except (GAPI.badRequest, GAPI.resourceNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.RESOURCE_CALENDAR, ''], str(e))
    return
  count = len(resources)
  if showItemCountOnly:
    writeStdout(f'{count}\n')
    return
  i = 0
  for resource in resources:
    i += 1
    if getCalSettings or getCalPermissions:
      status, acls = _getResourceACLsCalSettings(cal, resource, getCalSettings, getCalPermissions, i, count)
      if not status:
        continue
    if not csvPF:
      _showResource(cd, resource, i, count, FJQC, acls, noSelfOwner)
    else:
      if 'buildingId' in resource:
        resource['buildingName'] = _getBuildingNameById(cd, resource['buildingId'])
        resource['buildingId'] = f'id:{resource["buildingId"]}'
      if not FJQC.formatJSON:
        if 'featureInstances' in resource:
          resource['featureInstances'] = ', '.join([a_feature['feature']['name'] for a_feature in resource.pop('featureInstances')])
        row = {}
        for field in fieldsList:
          if convertCRNL and field in RESOURCE_FIELDS_WITH_CRS_NLS:
            row[field] = escapeCRsNLs(resource.get(field, ''))
          else:
            row[field] = resource.get(field, '')
        if getCalSettings and 'calendar' in resource:
          flattenJSON(resource['calendar'], flattened=row)
        if getCalPermissions:
          for rule in acls:
            if noSelfOwner and rule['role'] == 'owner' and rule['scope']['value'] == resource['resourceEmail']:
              continue
            csvPF.WriteRowTitles(flattenJSON(rule, flattened=row.copy()))
        else:
          csvPF.WriteRowTitles(row)
      else:
        if getCalPermissions:
          resource['acls'] = []
          for rule in acls:
            if noSelfOwner and rule['role'] == 'owner' and rule['scope']['value'] == resource['resourceEmail']:
              continue
            resource['acls'].append({'id': rule['id'], 'role': rule['role']})
        row = {'resourceId': resource['resourceId'], 'JSON': json.dumps(cleanJSON(resource), ensure_ascii=False, sort_keys=True)}
        if 'resourceName' in resource:
          row['resourceName'] = resource['resourceName']
        csvPF.WriteRow(row)
  if csvPF:
    csvPF.writeCSVfile('Resources')

# Calendar commands utilities
