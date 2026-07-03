"""Vault matter and export management.

Part of the _vault_tmp sub-package."""

"""GAM Google Vault management."""

import re
import json
import sys
import base64
import os
import time

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

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

WARNING_PREFIX = 'WARNING: '


def formatVaultNameId(vaultName, vaultId):
  return f'{vaultName}({vaultId})'

def convertExportNameToID(v, nameOrId, matterId, matterNameId):
  cg = _getMain().UID_PATTERN.match(nameOrId)
  if cg:
    try:
      export = _getMain().callGAPI(v.matters().exports(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED,
                                      GAPI.INVALID_ARGUMENT, GAPI.FAILED_PRECONDITION],
                        matterId=matterId, exportId=cg.group(1))
      return (export['id'], export['name'], formatVaultNameId(export['id'], export['name']))
    except (GAPI.notFound, GAPI.badRequest):
      _getMain().entityDoesNotHaveItemExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, nameOrId])
    except (GAPI.failedPrecondition) as e:
      _getMain().entityActionFailedExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, nameOrId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      ClientAPIAccessDeniedExit(str(e))
  nameOrIdlower = nameOrId.lower()
  try:
    exports = _getMain().callGAPIpages(v.matters().exports(), 'list', 'exports',
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                            matterId=matterId, fields='exports(id,name),nextPageToken')
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    ClientAPIAccessDeniedExit(str(e))
  for export in exports:
    if export['name'].lower() == nameOrIdlower:
      return (export['id'], export['name'], formatVaultNameId(export['id'], export['name']))
  _getMain().entityDoesNotHaveItemExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, nameOrId])

def convertHoldNameToID(v, nameOrId, matterId, matterNameId):
  cg = _getMain().UID_PATTERN.match(nameOrId)
  if cg:
    try:
      hold = _getMain().callGAPI(v.matters().holds(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                      matterId=matterId, holdId=cg.group(1))
      return (hold['holdId'], hold['name'], formatVaultNameId(hold['holdId'], hold['name']))
    except (GAPI.notFound, GAPI.badRequest):
      _getMain().entityDoesNotHaveItemExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, nameOrId])
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      ClientAPIAccessDeniedExit(str(e))
  nameOrIdlower = nameOrId.lower()
  try:
    holds = _getMain().callGAPIpages(v.matters().holds(), 'list', 'holds',
                          throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                          matterId=matterId, fields='holds(holdId,name),nextPageToken')
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    ClientAPIAccessDeniedExit(str(e))
  for hold in holds:
    if hold['name'].lower() == nameOrIdlower:
      return (hold['holdId'], hold['name'], formatVaultNameId(hold['holdId'], hold['name']))
  _getMain().entityDoesNotHaveItemExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_HOLD, nameOrId])

def convertMatterNameToID(v, nameOrId, state=None):
  cg = _getMain().UID_PATTERN.match(nameOrId)
  if cg:
    try:
      matter = _getMain().callGAPI(v.matters(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                        matterId=cg.group(1), view='BASIC', fields='matterId,name,state')
      return (matter['matterId'], matter['name'], formatVaultNameId(matter['name'], matter['matterId']), matter['state'])
    except GAPI.notFound:
      _getMain().entityDoesNotExistExit(Ent.VAULT_MATTER, nameOrId)
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      ClientAPIAccessDeniedExit(str(e))
  try:
    matters = _getMain().callGAPIpages(v.matters(), 'list', 'matters',
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                            view='BASIC', state=state, fields='matters(matterId,name,state),nextPageToken')
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    ClientAPIAccessDeniedExit(str(e))
  nameOrIdlower = nameOrId.lower()
  ids = []
  states = []
  for matter in matters:
    if matter['name'].lower() == nameOrIdlower:
      nameOrId = matter['name']
      ids.append(matter['matterId'])
      states.append(matter['state'])
  if len(ids) == 1:
    return (ids[0], nameOrId, formatVaultNameId(nameOrId, ids[0]), states[0])
  if not ids:
    _getMain().entityDoesNotExistExit(Ent.VAULT_MATTER, nameOrId)
  else:
    _getMain().entityIsNotUniqueExit(Ent.VAULT_MATTER, nameOrId, Ent.VAULT_MATTER_ID, ids)

def convertQueryNameToID(v, nameOrId, matterId, matterNameId):
  cg = _getMain().UID_PATTERN.match(nameOrId)
  if cg:
    try:
      query = _getMain().callGAPI(v.matters().savedQueries(), 'get',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                       matterId=matterId, savedQueryId=cg.group(1))
      return (query['savedQueryId'], query['displayName'], formatVaultNameId(query['savedQueryId'], query['displayName']), query['query'])
    except (GAPI.notFound, GAPI.badRequest):
      _getMain().entityDoesNotHaveItemExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, nameOrId])
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      ClientAPIAccessDeniedExit(str(e))
  nameOrIdlower = nameOrId.lower()
  try:
    queries = _getMain().callGAPIpages(v.matters().savedQueries(), 'list', 'savedQueries',
                            throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                            matterId=matterId, fields='savedQueries(savedQueryId,displayName,query),nextPageToken')
  except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    ClientAPIAccessDeniedExit(str(e))
  for query in queries:
    if query['displayName'].lower() == nameOrIdlower:
      return (query['savedQueryId'], query['displayName'], formatVaultNameId(query['savedQueryId'], query['displayName']), query['query'])
  _getMain().entityDoesNotHaveItemExit([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_QUERY, nameOrId])

def getMatterItem(v, state=None):
  matterId, _, matterNameId, _ = convertMatterNameToID(v, _getMain().getString(Cmd.OB_MATTER_ITEM), state=state)
  return (matterId, matterNameId)

def warnMatterNotOpen(v, matter, matterNameId, j, jcount):
  if v is not None:
    try:
      matter['state'] = _getMain().callGAPI(v.matters(), 'get',
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                                 matterId=matter['matterId'], view='BASIC', fields='state')['state']
    except (GAPI.notFound, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument):
      matter['state'] = 'Unknown'
  else:
    _getMain().setSysExitRC(_getMain().DATA_NOT_AVALIABLE_RC)
  message = _getMain().formatKeyValueList('',
                               Ent.FormatEntityValueList([Ent.VAULT_MATTER, matterNameId])+
                               [Msg.MATTER_NOT_OPEN.format(matter['state'])],
                               _getMain().currentCount(j, jcount))
  _getMain().writeStderr(f'\n{Ind.Spaces()}{WARNING_PREFIX}{message}\n')

def _cleanVaultExport(export, cd):
  query = export.get('query')
  if query:
    if cd is not None:
      if 'orgUnitInfo' in query:
        query['orgUnitInfo']['orgUnitPath'] = convertOrgUnitIDtoPath(cd, query['orgUnitInfo']['orgUnitId'])

VAULT_EXPORT_TIME_OBJECTS = {'versionDate', 'createTime', 'startTime', 'endTime'}

def _showVaultExport(matterNameId, export, cd, FJQC, k=0, kcount=0):
  _cleanVaultExport(export, cd)
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(export, timeObjects=VAULT_EXPORT_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
    return
  if matterNameId is not None:
    _getMain().printEntity([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, formatVaultNameId(export['name'], export['id'])], k, kcount)
  Ind.Increment()
  _getMain().showJSON(None, export, timeObjects=VAULT_EXPORT_TIME_OBJECTS)
  Ind.Decrement()

VAULT_SEARCH_METHODS_MAP = {
  'account': 'ACCOUNT',
  'accounts': 'ACCOUNT',
  'chatspace': 'ROOM',
  'chatspaces': 'ROOM',
  'documentids': 'DRIVE_DOCUMENT',
  'entireorg': 'ENTIRE_ORG',
  'everyone': 'ENTIRE_ORG',
  'org': 'ORG_UNIT',
  'orgunit': 'ORG_UNIT',
  'ou': 'ORG_UNIT',
  'room': 'ROOM',
  'rooms': 'ROOM',
  'shareddrive': 'SHARED_DRIVE',
  'shareddrives': 'SHARED_DRIVE',
  'sitesurl': 'SITES_URL',
  'teamdrive': 'SHARED_DRIVE',
  'teamdrives': 'SHARED_DRIVE',
  }
VAULT_CORPUS_ARGUMENT_MAP = {
  'calendar': 'CALENDAR',
  'drive': 'DRIVE',
  'gemini': 'GEMINI',
  'groups': 'GROUPS',
  'hangoutschat': 'HANGOUTS_CHAT',
  'mail': 'MAIL',
  'voice': 'VOICE',
  }
VAULT_COUNTS_CORPUS_ARGUMENT_MAP = {
  'mail': 'MAIL',
  'groups': 'GROUPS',
  }
VAULT_RESPONSE_STATUS_MAP = {
  'accepted': 'ATTENDEE_RESPONSE_ACCEPTED',
  'declined': 'ATTENDEE_RESPONSE_DECLINED',
  'needsaction': 'ATTENDEE_RESPONSE_NEEDS_ACTION',
  'tentative': 'ATTENDEE_RESPONSE_TENTATIVE',
  }
VAULT_SHARED_DRIVES_OPTION_MAP = {
  'included': 'INCLUDED',
  'includedifaccountisnotamember': 'INCLUDED_IF_ACCOUNT_IS_NOT_A_MEMBER',
  'notincluded': 'NOT_INCLUDED',
  }
VAULT_VOICE_COVERED_DATA_MAP = {
  'calllogs': 'CALL_LOGS',
  'textmessages': 'TEXT_MESSAGES',
  'voicemails': 'VOICEMAILS',
  }
VAULT_EXPORT_DATASCOPE_MAP = {
  'alldata': 'ALL_DATA',
  'helddata': 'HELD_DATA',
  'unprocesseddata': 'UNPROCESSED_DATA',
  }
VAULT_EXPORT_FORMAT_MAP = {
  'ics': 'ICS',
  'mbox': 'MBOX',
  'pst': 'PST',
  'xml': 'XML',
  }
VAULT_CORPUS_EXPORT_FORMATS = {
  'CALENDAR': ['ICS', 'PST'],
  'DRIVE': [],
  'GEMINI': ['XML'],
  'GROUPS': ['MBOX', 'PST'],
  'HANGOUTS_CHAT': ['MBOX', 'PST'],
  'MAIL': ['MBOX', 'PST'],
  'VOICE' : ['MBOX', 'PST'],
  }
VAULT_CSE_OPTION_MAP = {
  'any': 'CLIENT_SIDE_ENCRYPTED_OPTION_ANY',
  'encrypted': 'CLIENT_SIDE_ENCRYPTED_OPTION_ENCRYPTED',
  'unencrypted': 'CLIENT_SIDE_ENCRYPTED_OPTION_UNENCRYPTED',
  }
VAULT_EXPORT_REGION_MAP = {
  'any': 'ANY',
  'europe': 'EUROPE',
  'us': 'US',
  }
VAULT_CORPUS_OPTIONS_MAP = {
  'CALENDAR': 'calendarOptions',
  'DRIVE': 'driveOptions',
  'GEMINI': 'geminiOptions',
  'GROUPS': 'groupsOptions',
  'HANGOUTS_CHAT': 'hangoutsChatOptions',
  'MAIL': 'mailOptions',
  'VOICE': 'voiceOptions',
  }
VAULT_CORPUS_QUERY_MAP = {
  'CALENDAR': None,
  'DRIVE': 'driveQuery',
  'GEMINI': None,
  'GROUPS': 'groupsQuery',
  'MAIL': 'mailQuery',
  'HANGOUTS_CHAT': 'hangoutsChatQuery',
  'VOICE': 'voiceQuery',
  }
VAULT_QUERY_ARGS = [
  'corpus', 'scope', 'terms', 'start', 'starttime', 'end', 'endtime', 'timezone',
# calendar
  'locationquery', 'peoplequery', 'minuswords', 'responsestatuses', 'caldendarversiondate',
# drive
  'driveclientsideencryption', 'driveversiondate', 'includeshareddrives', 'includeteamdrives', 'shareddrivesoption',
# hangoutsChat
  'includerooms', 
# mail
  'mailclientsideencryption', 'excludedrafts',
# voice
  'covereddata',
# all
  'json',
  ] + list(VAULT_SEARCH_METHODS_MAP.keys())

def _buildVaultQuery(myarg, query, corpusArgumentMap):
  def _getQueryList(obNameList):
    itemList = _getMain().getString(obNameList)
    if itemList != 'select':
      return itemList.replace(',', ' ').split()
    return _getMain().getEntityList(obNameList)

  if not query:
    query['dataScope'] = 'ALL_DATA'
  if myarg == 'corpus':
    query['corpus'] = _getMain().getChoice(corpusArgumentMap, mapChoice=True)
  elif myarg == 'scope':
    query['dataScope'] = _getMain().getChoice(VAULT_EXPORT_DATASCOPE_MAP, mapChoice=True)
  elif myarg in VAULT_SEARCH_METHODS_MAP:
    if query.get('method'):
      Cmd.Backup()
      _getMain().usageErrorExit(Msg.MULTIPLE_SEARCH_METHODS_SPECIFIED.format(_getMain().formatChoiceList(VAULT_SEARCH_METHODS_MAP)))
    searchMethod = VAULT_SEARCH_METHODS_MAP[myarg]
    query['method'] = searchMethod
    if searchMethod == 'ACCOUNT':
      query['accountInfo'] = {'emails': _getMain().getNormalizedEmailAddressEntity()}
    elif searchMethod == 'ORG_UNIT':
      query['orgUnitInfo'] = {'orgUnitId': _getMain().getOrgUnitId()[1]}
    elif searchMethod == 'SHARED_DRIVE':
      query['sharedDriveInfo'] = {'sharedDriveIds': _getQueryList(Cmd.OB_SHAREDDRIVE_ID_LIST)}
    elif searchMethod == 'ROOM':
      roomIds = _getQueryList(Cmd.OB_CHAT_SPACE_LIST)
      for i, roomId in enumerate(roomIds):
        if roomId.startswith('spaces/') or roomId.startswith('space/'):
          _, roomIds[i] = roomId.split('/', 1)
      query['hangoutsChatInfo'] = {'roomId': roomIds}
    elif searchMethod == 'SITES_URL':
      query['sitesUrlInfo'] = {'urls': _getQueryList(Cmd.OB_URL_LIST)}
    elif searchMethod == 'DRIVE_DOCUMENT':
      query['driveDocumentInfo'] = {'documentIds': {'ids': _getQueryList(Cmd.OB_DRIVE_FILE_ID_LIST)}}
  elif myarg == 'terms':
    query['terms'] = _getMain().getString(Cmd.OB_STRING)
  elif myarg in {'start', 'starttime'}:
    query['startTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg in {'end', 'endtime'}:
    query['endTime'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg == 'timezone':
    query['timeZone'] = _getMain().getString(Cmd.OB_STRING)
# calendar
  elif myarg == 'locationquery':
    query.setdefault('calendarOptions', {})['locationQuery'] = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_STRING_LIST))
  elif myarg == 'peoplequery':
    query.setdefault('calendarOptions', {})['peopleQuery'] = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_STRING_LIST))
  elif myarg == 'minuswords':
    query.setdefault('calendarOptions', {})['minusWords'] = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_STRING_LIST))
  elif myarg == 'responsestatuses':
    query.setdefault('calendarOptions', {})['responseStatuses'] = []
    for response in _getMain().getString(Cmd.OB_FIELD_NAME_LIST).lower().replace('_', '').replace(',', ' ').split():
      if response in VAULT_RESPONSE_STATUS_MAP:
        query['calendarOptions']['responseStatuses'].append(VAULT_RESPONSE_STATUS_MAP[response])
      else:
        _getMain().invalidChoiceExit(response, VAULT_RESPONSE_STATUS_MAP, True)
  elif myarg == 'calendarversiondate':
    query.setdefault('calendarOptions', {})['versionDate'] = _getMain().getTimeOrDeltaFromNow()
# drive
  elif myarg == 'driveversiondate':
    query.setdefault('driveOptions', {})['versionDate'] = _getMain().getTimeOrDeltaFromNow()
  elif myarg in {'includeshareddrives', 'includeteamdrives'}:
    query.setdefault('driveOptions', {})['sharedDrivesOption'] = 'INCLUDED' if _getMain().getBoolean() else 'INCLUDED_IF_ACCOUNT_IS_NOT_A_MEMBER'
  elif myarg == 'shareddrivesoption':
    query.setdefault('driveOptions', {})['sharedDrivesOption'] = _getMain().getChoice(VAULT_SHARED_DRIVES_OPTION_MAP, mapChoice=True)
  elif myarg == 'driveclientsideencryption':
    query.setdefault('driveOptions', {})['clientSideEncryptedOption'] = _getMain().getChoice(VAULT_CSE_OPTION_MAP, mapChoice=True)
# hangoutsChat
  elif myarg == 'includerooms':
    query['hangoutsChatOptions'] = {'includeRooms': _getMain().getBoolean()}
# mail
  elif myarg == 'excludedrafts':
    query.setdefault('mailOptions', {})['excludeDrafts'] =  _getMain().getBoolean()
  elif myarg == 'mailclientsideencryption':
    query.setdefault('mailOptions', {})['clientSideEncryptedOption'] = _getMain().getChoice(VAULT_CSE_OPTION_MAP, mapChoice=True)
# voice
  elif myarg == 'covereddata':
    query.setdefault('voiceOptions', {'coveredData': []})
    query['voiceOptions']['coveredData'].append(_getMain().getChoice(VAULT_VOICE_COVERED_DATA_MAP, mapChoice=True))
# all
  elif myarg == 'json':
    jsonData = _getMain().getJSON([])
    if 'query' in jsonData:
      query.update(jsonData['query'])
    else:
      query.update(jsonData)


def _validateVaultQuery(body, corpusArgumentMap):
  if 'corpus' not in body['query']:
    _getMain().missingArgumentExit(f'corpus {formatChoiceList(corpusArgumentMap)}')
  if 'method' not in body['query']:
    _getMain().missingArgumentExit(_getMain().formatChoiceList(VAULT_SEARCH_METHODS_MAP))
  if 'exportOptions' in body:
    for corpus, options in VAULT_CORPUS_OPTIONS_MAP.items():
      if body['query']['corpus'] != corpus:
        body['exportOptions'].pop(options, None)

# gam create vaultexport|export matter <MatterItem> [name <String>]
#	vaultquery <QueryItem>
#	[driveclientsideencryption any|encrypted|unencrypted]
#	[includeaccessinfo <Boolean>]
#	[excludedrafts <Boolean>] [mailclientsideencryption any|encrypted|unencrypted]
#	[showconfidentialmodecontent <Boolean>] [usenewexport <Boolean>] [exportlinkeddrivefiles <Boolean>]
#	[format ics|mbox|pst|xml]
#	[region any|europe|us] [showdetails|returnidonly]
# gam create vaultexport|export matter <MatterItem> [name <String>]
#	corpus calendar|drive|gemini|groups|hangouts_chat|mail|voice
#	[scope all_data|held_data|unprocessed_data]
#	(accounts <EmailAddressEntity>) | (orgunit|org|ou <OrgUnitPath>) | everyone|entireorg
#	(documentids  (<DriveFileIDList>|(select <FileSelector>|<CSVFileSelector>))) |
#	(shareddrives|teamdrives (<SharedDriveIDList>|(select <FileSelector>|<CSVFileSelector>))) |
#	[(includeshareddrives <Boolean>)|(shareddrivesoption included|included_if_account_is_not_a_member|not_included)]
#	(sitesurl (<URLList>||(select <FileSelector>|<CSVFileSelector>)))
#	[driveversiondate <Date>|<Time>]
#	[includerooms <Boolean>]
#	(rooms (<ChatSpaceList>|(select <FileSelector>|<CSVFileSelector>))) |
#	[terms <String>] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>] [timezone <TimeZone>]
#	[locationquery <StringList>] [peoplequery <StringList>] [minuswords <StringList>]
#	[responsestatuses <AttendeeStatus>(,<AttendeeStatus>)*] [calendarversiondate <Date>|<Time>]
#	(covereddata calllogs|textmessages|voicemails)*
#	[<JSONData>]
#	[driveclientsideencryption any|encrypted|unencrypted]
#	[includeaccessinfo <Boolean>]
#	[excludedrafts <Boolean>] [mailclientsideencryption any|encrypted|unencrypted]
#	[showconfidentialmodecontent <Boolean>] [usenewexport <Boolean>] [exportlinkeddrivefiles <Boolean>]
#	[format ics|mbox|pst|xml]
#	[region any|europe|us] [showdetails|returnidonly]
def doCreateVaultExport():
  v = _getMain().buildGAPIObject(API.VAULT)
  matterId = None
  body = {'query': {'dataScope': 'ALL_DATA'}, 'exportOptions': {}}
  includeAccessInfo = None
  exportFormat = None
  formatLocation = None
  useNewExport = None
  showConfidentialModeContent = None
  exportLinkedDriveFiles = None
  returnIdOnly = showDetails = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v, state='OPEN')
      body['matterId'] = matterId
    elif myarg == 'name':
      body['name'] = _getMain().getString(Cmd.OB_STRING)
    elif matterId is not None and myarg == 'vaultquery':
      _, _, _, body['query'] = convertQueryNameToID(v, _getMain().getString(Cmd.OB_QUERY_ITEM), matterId, matterNameId)
    elif myarg in VAULT_QUERY_ARGS:
      _buildVaultQuery(myarg, body['query'], VAULT_CORPUS_ARGUMENT_MAP)
    elif myarg == 'includeaccessinfo':
      includeAccessInfo = _getMain().getBoolean()
    elif myarg == 'format':
      formatLocation = Cmd.Location()
      exportFormat = _getMain().getChoice(VAULT_EXPORT_FORMAT_MAP, mapChoice=True)
    elif myarg == 'usenewexport':
      useNewExport = _getMain().getBoolean()
    elif myarg == 'showconfidentialmodecontent':
      showConfidentialModeContent = _getMain().getBoolean()
    elif myarg == 'exportlinkeddrivefiles':
      exportLinkedDriveFiles = _getMain().getBoolean()
    elif myarg == 'region':
      body['exportOptions']['region'] = _getMain().getChoice(VAULT_EXPORT_REGION_MAP, mapChoice=True)
    elif myarg == 'showdetails':
      showDetails = True
      returnIdOnly = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
      showDetails = False
    else:
      _getMain().unknownArgumentExit()
  if not matterId:
    _getMain().missingArgumentExit('matter')
  _validateVaultQuery(body, VAULT_CORPUS_ARGUMENT_MAP)
  if 'name' not in body:
    body['name'] = f'GAM {body["query"]["corpus"]} Export - {ISOformatTimeStamp(todaysTime())}'
  optionsField = VAULT_CORPUS_OPTIONS_MAP[body['query']['corpus']]
  if body['query']['corpus'] == 'DRIVE':
    if includeAccessInfo is not None:
      body['exportOptions'][optionsField] = {'includeAccessInfo': includeAccessInfo}
  else:
    if exportFormat is not None:
      if not exportFormat in VAULT_CORPUS_EXPORT_FORMATS[body['query']['corpus']]:
        Cmd.SetLocation(formatLocation)
        _getMain().invalidChoiceExit(exportFormat, VAULT_CORPUS_EXPORT_FORMATS[body['query']['corpus']], False)
    else:
      exportFormat = VAULT_CORPUS_EXPORT_FORMATS[body['query']['corpus']][0]
    body['exportOptions'][optionsField] = {'exportFormat': exportFormat}
    if body['query']['corpus'] == 'MAIL':
      if showConfidentialModeContent is not None:
        body['exportOptions'][optionsField]['showConfidentialModeContent'] = showConfidentialModeContent
      if useNewExport is not None:
        body['exportOptions'][optionsField]['useNewExport'] = useNewExport
      if exportLinkedDriveFiles is not None:
        body['exportOptions'][optionsField]['exportLinkedDriveFiles'] = exportLinkedDriveFiles
  try:
    export = _getMain().callGAPI(v.matters().exports(), 'create',
                      throwReasons=[GAPI.ALREADY_EXISTS, GAPI.BAD_REQUEST, GAPI.BACKEND_ERROR, GAPI.INVALID_ARGUMENT,
                                    GAPI.INVALID, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.QUOTA_EXCEEDED, GAPI.NOT_FOUND],
                      matterId=matterId, body=body)
    if not returnIdOnly:
      _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, formatVaultNameId(export['name'], export['id'])])
      if showDetails:
        _showVaultExport(None, export, None, None)
    else:
      _getMain().writeStdout(f'{export["id"]}\n')
  except (GAPI.alreadyExists, GAPI.badRequest, GAPI.backendError, GAPI.invalidArgument,
          GAPI.invalid, GAPI.failedPrecondition, GAPI.forbidden, GAPI.quotaExceeded, GAPI.notFound) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, body.get('name')], str(e))

# gam delete vaultexport|export <ExportItem> matter <MatterItem>
# gam delete vaultexport|export <MatterItem> <ExportItem>
def doDeleteVaultExport():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    exportId, exportName, exportNameId = convertExportNameToID(v, _getMain().getString(Cmd.OB_EXPORT_ITEM), matterId, matterNameId)
  else:
    exportName = _getMain().getString(Cmd.OB_EXPORT_ITEM)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      exportId, exportName, exportNameId = convertExportNameToID(v, exportName, matterId, matterNameId)
    else:
      _getMain().unknownArgumentExit()
  try:
    _getMain().callGAPI(v.matters().exports(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
             matterId=matterId, exportId=exportId)
    _getMain().entityActionPerformed([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId])
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], str(e))

VAULT_EXPORT_FIELDS_CHOICE_MAP = {
  'cloudstoragesink': 'cloudStorageSink',
  'createtime': 'createTime',
  'exportoptions': 'exportOptions',
  'id': 'id',
  'matterid': 'matterId',
  'name': 'name',
  'query': 'query',
  'requester': 'requester',
  'requester.displayname': 'requester.displayName',
  'requester.email': 'requester.email',
  'stats': 'stats',
  'stats.exportedartifactcount': 'stats.exportedArtifactCount',
  'stats.sizeinbytes': 'stats.sizeInBytes',
  'stats.totalartifactcount': 'stats.totalArtifactCount',
  'status': 'status',
  }

# gam info vaultexport|export <ExportItem> matter <MatterItem>
#	[fields <VaultExportFieldNameList>] [shownames]
#	[formatjson]
# gam info vaultexport|export <MatterItem> <ExportItem>
#	[fields <VaultExportFieldNameList>] [shownames]
#	[formatjson]
def doInfoVaultExport():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    exportId, exportName, exportNameId = convertExportNameToID(v, _getMain().getString(Cmd.OB_EXPORT_ITEM), matterId, matterNameId)
  else:
    exportName = _getMain().getString(Cmd.OB_EXPORT_ITEM)
  cd = None
  fieldsList = []
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      exportId, exportName, exportNameId = convertExportNameToID(v, exportName, matterId, matterNameId)
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    elif _getMain().getFieldsList(myarg, VAULT_EXPORT_FIELDS_CHOICE_MAP, fieldsList, initialField=['id', 'name']):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  try:
    export = _getMain().callGAPI(v.matters().exports(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN,
                                    GAPI.INVALID_ARGUMENT, GAPI.FAILED_PRECONDITION],
                      matterId=matterId, exportId=exportId, fields=fields)
    _showVaultExport(matterNameId, export, cd, FJQC)
  except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
    _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], str(e))

VAULT_EXPORT_STATUS_MAP = {'completed': 'COMPLETED', 'failed': 'FAILED', 'inprogress': 'IN_PROGRESS'}
PRINT_VAULT_EXPORTS_TITLES = ['matterId', 'matterName', 'id', 'name']

# gam print vaultexports|exports [todrive <ToDriveAttribute>*]
#	[matters <MatterItemList>] [exportstatus <ExportStatusList>]
#	[fields <VaultExportFieldNameList>] [shownames]
#	[formatjson [quotechar <Character>]]
#	[oneitemperrow]
# gam show vaultexports|exports
#	[matters <MatterItemList>] [exportstatus <ExportStatusList>]
#	[fields <VaultExportFieldNameList>] [shownames]
#	[formatjson]
def doPrintShowVaultExports():
  def _printVaultExport(export):
    row = _getMain().flattenJSON(export, flattened={'matterId': matterId, 'matterName': matterName}, timeObjects=VAULT_EXPORT_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'matterId': matterId, 'matterName': matterName,
                              'id': export['id'], 'name': export['name'],
                              'JSON': json.dumps(_getMain().cleanJSON(export, timeObjects=VAULT_EXPORT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})

  v = _getMain().buildGAPIObject(API.VAULT)
  csvPF = _getMain().CSVPrintFile(PRINT_VAULT_EXPORTS_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar()
  matters = []
  exportStatusList = []
  cd = None
  fieldsList = []
  oneItemPerRow = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'matter', 'matters'}:
      matters = _getMain().shlexSplitList(_getMain().getString(Cmd.OB_MATTER_ITEM_LIST))
    elif myarg == 'exportstatus':
      for state in _getMain().getString(Cmd.OB_STATE_NAME_LIST).lower().replace('_', '').replace(',', ' ').split():
        if state in VAULT_EXPORT_STATUS_MAP:
          exportStatusList.append(VAULT_EXPORT_STATUS_MAP[state])
        else:
          _getMain().invalidChoiceExit(state, list(VAULT_EXPORT_STATUS_MAP), True)
    elif myarg == 'shownames':
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    elif _getMain().getFieldsList(myarg, VAULT_EXPORT_FIELDS_CHOICE_MAP, fieldsList, initialField=['id', 'name']):
      pass
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  fields = _getMain().getItemFieldsFromFieldsList('exports', fieldsList)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(PRINT_VAULT_EXPORTS_TITLES+['JSON'])
  exportStatuses = set(exportStatusList)
  exportQualifier = f' ({",".join(exportStatusList)})' if exportStatusList else ''
  if not matters:
    _getMain().printGettingAllAccountEntities(Ent.VAULT_MATTER, qualifier=' (OPEN)')
    try:
      results = _getMain().callGAPIpages(v.matters(), 'list', 'matters',
                              pageMessage=_getMain().getPageMessage(),
                              throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                              view='BASIC', state='OPEN', fields='matters(matterId,name,state),nextPageToken')
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_EXPORT, None], str(e))
      return
  else:
    results = []
    for matter in matters:
      matterId, matterName, _, state = convertMatterNameToID(v, matter)
      results.append({'matterId': matterId, 'name': matterName, 'state': state})
  jcount = len(results)
  if not csvPF:
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  j = 0
  for matter in results:
    j += 1
    matterId = matter['matterId']
    matterName = matter['name']
    matterNameId = formatVaultNameId(matterName, matterId)
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(Ent.VAULT_EXPORT, f'{Ent.Singular(Ent.VAULT_MATTER)}: {matterNameId}',
                                        j, jcount, qualifier=exportQualifier)
      pageMessage = _getMain().getPageMessageForWhom()
    else:
      pageMessage = None
    if matter['state'] == 'OPEN':
      try:
        exports = _getMain().callGAPIpages(v.matters().exports(), 'list', 'exports',
                                pageMessage=pageMessage,
                                throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT],
                                matterId=matterId, fields=fields)
      except GAPI.failedPrecondition:
        warnMatterNotOpen(v, matter, matterNameId, j, jcount)
        continue
      except (GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.VAULT_EXPORT, None], str(e))
        break
    else:
      warnMatterNotOpen(None, matter, matterNameId, j, jcount)
      continue
    if not csvPF:
      kcount = len(exports)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId], kcount, Ent.VAULT_EXPORT, j, jcount)
      Ind.Increment()
      k = 0
      for export in exports:
        k += 1
        if not exportStatuses or export['status'] in exportStatuses:
          _showVaultExport(matterNameId, export, cd, FJQC, k, kcount)
      Ind.Decrement()
    else:
      for export in exports:
        if not exportStatuses or export['status'] in exportStatuses:
          _cleanVaultExport(export, cd)
          if not oneItemPerRow or not export.get('cloudStorageSink', {}).get('files'):
            _printVaultExport(export)
          else:
            for file in export['cloudStorageSink'].pop('files'):
              export['cloudStorageSink']['files'] = file
              _printVaultExport(export)
  if csvPF:
    csvPF.writeCSVfile('Vault Exports')

# gam copy vaultexport|export <ExportItem> matter <MatterItem>
#	[targetbucket <String>] [targetprefix <String>]
#	[bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
#	[copyattempts <Integer>] [retryinterval <Integer>]
# gam copy vaultexport|export <MatterItem> <ExportItem>
#	[targetbucket <String>] [targetprefix <String>]
#	[bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
#	[copyattempts <Integer>] [retryinterval <Integer>]
def doCopyVaultExport():
  v = _getMain().buildGAPIObject(API.VAULT)
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    exportId, exportName, exportNameId = convertExportNameToID(v, _getMain().getString(Cmd.OB_EXPORT_ITEM), matterId, matterNameId)
  else:
    exportName = _getMain().getString(Cmd.OB_EXPORT_ITEM)
  target_bucket = None
  target_prefix = ''
  bucketMatchPattern = objectMatchPattern = None
  copyAttempts = 1
  retryInterval = 30
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      exportId, exportName, exportNameId = convertExportNameToID(v, exportName, matterId, matterNameId)
    elif myarg == 'targetbucket':
      target_bucket = _getMain().getString(Cmd.OB_URL)
    elif myarg == 'targetprefix':
      target_prefix = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'bucketmatchpattern':
      bucketMatchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg == 'objectmatchpattern':
      objectMatchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg == 'copyattempts':
      copyAttempts = _getMain().getInteger(minVal=1)
    elif myarg == 'retryinterval':
      retryInterval = _getMain().getInteger(minVal=10)
    else:
      _getMain().unknownArgumentExit()
  if not target_bucket:
    _getMain().missingArgumentExit('targetbucket')
  attempts = 0
  while True:
    try:
      export = _getMain().callGAPI(v.matters().exports(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN,
                                      GAPI.INVALID_ARGUMENT, GAPI.FAILED_PRECONDITION],
                        matterId=matterId, exportId=exportId)
    except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], str(e))
      return
    if export['status'] == 'COMPLETED':
      break
    attempts += 1
    _getMain().entityActionNotPerformedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], Msg.EXPORT_NOT_COMPLETE.format(export['status']), attempts, copyAttempts)
    if attempts >= copyAttempts:
      return
    time.sleep(retryInterval)
  objects = []
  for s_file in export['cloudStorageSink']['files']:
    if ((bucketMatchPattern and not bucketMatchPattern.match(s_file['bucketName'])) or
        (objectMatchPattern and not objectMatchPattern.match(s_file['objectName']))):
      continue
    # Convert to md5Hash format Storage API uses because OF COURSE they differ
    md5Hash = base64.b64encode(bytes.fromhex(s_file['md5Hash'])).decode()
    objects.append({'bucket': s_file['bucketName'], 'name': s_file['objectName'], 'md5Hash': md5Hash})
  _getMain()._copyStorageObjects(objects, target_bucket, target_prefix)

ZIP_EXTENSION_PATTERN = re.compile(r'^.*\.zip$', re.IGNORECASE)

# gam download vaultexport|export <ExportItem> matter <MatterItem>
#	[targetfolder <FilePath>] [targetname <FileName>] [noverify] [noextract] [ziptostdout]
#	[bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
#	[downloadattempts <Integer>] [retryinterval <Integer>]
# gam download vaultexport|export <MatterItem> <ExportItem>
#	[targetfolder <FilePath>] [targetname <FileName>] [noverify] [noextract] [ziptostdout]
#	[bucketmatchpattern <REMatchPattern>] [objectmatchpattern <REMatchPattern>]
#	[downloadattempts <Integer>] [retryinterval <Integer>]
def doDownloadVaultExport():
  def extract_nested_zip(zippedFile):
    """ Extract a zip file including any nested zip files
        Delete the zip file(s) after extraction
    """
    Act.Set(Act.UNZIP)
    _getMain().performAction(Ent.FILE, zippedFile)
    Ind.Increment()
    with zipfile.ZipFile(zippedFile, 'r') as zfile:
      inner_files = zfile.infolist()
      for inner_file in inner_files:
        Act.Set(Act.EXTRACT)
        _getMain().performAction(Ent.FILE, inner_file.filename)
        innerFilePath = zfile.extract(inner_file, targetFolder)
        if ZIP_EXTENSION_PATTERN.match(inner_file.filename):
          extract_nested_zip(innerFilePath)
    Ind.Decrement()
    try:
      os.remove(zippedFile)
    except OSError as e:
      _getMain().stderrWarningMsg(e)

  v = _getMain().buildGAPIObject(API.VAULT)
  s = _getMain().buildGAPIObject(API.STORAGEREAD)
  verifyFiles = extractFiles = True
  targetFolder = GC.Values[GC.DRIVE_DIR]
  targetName = None
  if not Cmd.ArgumentIsAhead('matter'):
    matterId, matterNameId = getMatterItem(v)
    exportId, exportName, exportNameId = convertExportNameToID(v, _getMain().getString(Cmd.OB_EXPORT_ITEM), matterId, matterNameId)
  else:
    exportName = _getMain().getString(Cmd.OB_EXPORT_ITEM)
  zipToStdout = False
  bucketMatchPattern = objectMatchPattern = None
  downloadAttempts = 1
  retryInterval = 30
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'matter':
      matterId, matterNameId = getMatterItem(v)
      exportId, exportName, exportNameId = convertExportNameToID(v, exportName, matterId, matterNameId)
    elif myarg == 'targetname':
      targetName = _getMain().getString(Cmd.OB_FILE_NAME)
    elif myarg == 'targetfolder':
      targetFolder = _getMain().setFilePath(_getMain().getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    elif myarg == 'noverify':
      verifyFiles = False
    elif myarg == 'noextract':
      extractFiles = False
    elif myarg == 'ziptostdout':
      zipToStdout = True
      verifyFiles = extractFiles = False
    elif myarg == 'bucketmatchpattern':
      bucketMatchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg == 'objectmatchpattern':
      objectMatchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg == 'downloadattempts':
      downloadAttempts = _getMain().getInteger(minVal=1)
    elif myarg == 'retryinterval':
      retryInterval = _getMain().getInteger(minVal=10)
    else:
      _getMain().unknownArgumentExit()
  attempts = 0
  while True:
    try:
      export = _getMain().callGAPI(v.matters().exports(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN,
                                      GAPI.INVALID_ARGUMENT, GAPI.FAILED_PRECONDITION],
                        matterId=matterId, exportId=exportId)
    except (GAPI.notFound, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.failedPrecondition) as e:
      _getMain().entityActionFailedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], str(e))
      return
    if export['status'] == 'COMPLETED':
      break
    attempts += 1
    _getMain().entityActionNotPerformedWarning([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], Msg.EXPORT_NOT_COMPLETE.format(export['status']), attempts, downloadAttempts)
    if attempts >= downloadAttempts:
      return
    time.sleep(retryInterval)
  jcount = len(export['cloudStorageSink']['files'])
  if not zipToStdout:
    if not bucketMatchPattern and not objectMatchPattern:
      _getMain().entityPerformActionNumItems([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], jcount, Ent.CLOUD_STORAGE_FILE)
    else:
      _getMain().entityPerformActionModifierNumItems([Ent.VAULT_MATTER, matterNameId, Ent.VAULT_EXPORT, exportNameId], Msg.MAXIMUM_OF, jcount, Ent.CLOUD_STORAGE_FILE)
  Ind.Increment()
  j = 0
  extCounts = {}
  for s_file in export['cloudStorageSink']['files']:
    j += 1
    bucket = s_file['bucketName']
    s_object = s_file['objectName']
    if ((bucketMatchPattern and not bucketMatchPattern.match(bucket)) or
        (objectMatchPattern and not objectMatchPattern.match(s_object))):
      continue
    filename = os.path.join(targetFolder, _getMain().cleanFilename(s_object))
    if zipToStdout and not ZIP_EXTENSION_PATTERN.match(filename):
      continue
    if targetName:
      _, s_objectFilename = s_object.rsplit('/', 1)
      if s_objectFilename.find('.') != -1:
        s_objectFilename, s_objectExtension = s_objectFilename.rsplit('.', 1)
      else:
        s_objectExtension = ''
      if targetName.find('#') == -1:
        extCounts.setdefault(s_objectExtension, 0)
        extCounts[s_objectExtension] += 1
        if s_objectExtension:
          filename = f"{targetName}-{extCounts[s_objectExtension]}.{s_objectExtension}"
        else:
          filename = f"{targetName}-{extCounts[s_objectExtension]}"
      else:
        filename = targetName.replace('#objectname#', s_object).replace('#filename#', s_objectFilename).replace('#extension#', s_objectExtension)
      filename = os.path.join(targetFolder, _getMain().cleanFilename(filename))
    Act.Set(Act.DOWNLOAD)
    if not zipToStdout:
      _getMain().performAction(Ent.CLOUD_STORAGE_FILE, s_object, j, jcount)
    Ind.Increment()
    _getMain()._getCloudStorageObject(s, bucket, s_object, filename,
                           expectedMd5=s_file['md5Hash'] if verifyFiles else None,
                           zipToStdout=zipToStdout, j=j, jcount=jcount)
    if extractFiles and ZIP_EXTENSION_PATTERN.match(filename):
      Act.Set(Act.EXTRACT)
      extract_nested_zip(filename)
      Act.Set(Act.DOWNLOAD)
    Ind.Decrement()
  Ind.Decrement()

