"""GAM Google Meet management."""

import json
import sys

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import buildGAPIServiceObject, callGAPI, callGAPIpages
from gam.util.args import (
    getArgument,
    getBoolean,
    getChoice,
    getString,
    getTimeOrDeltaFromNow,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionPerformed,
    entityPerformAction,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printLine,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import entityActionFailedExit, missingArgumentExit, unknownArgumentExit
from gam.util.output import setSysExitRC, writeStdout

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

def buildMeetServiceObject(api, user=None, i=0, count=0, entityTypeList=None):
  user, meet = buildGAPIServiceObject(api, user, i, count)
  kvList = [Ent.USER, user]
  if entityTypeList is not None:
    kvList.extend(entityTypeList)
  return user, meet, kvList

def _showMeetItem(mitem, FJQC=None, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(mitem), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.MEET_SPACE, mitem['name']], i, count)
  Ind.Increment()
  showJSON(None, mitem)
  Ind.Decrement()

MEET_SPACE_OPTIONS_MAP = {
  'accesstype': 'accessType',
  'entrypointaccess': 'entryPointAccess',
  'moderation': 'moderation',
  'chatrestriction': 'chatRestriction',
  'reactionrestriction': 'reactionRestriction',
  'presentrestriction': 'presentRestriction',
  'defaultjoinasviewer': 'defaultJoinAsViewerType',
  'firstjoiner': 'firstJoinerType',
  'autorecording': 'recordingConfig',
  'autosmartnotes': 'smartNotesConfig',
  'autotranscription': 'transcriptionConfig',
  }

MEET_SPACE_ACCESSTYPE_CHOICES = {'open', 'trusted', 'restricted'}
MEET_SPACE_ENTRYPOINTACCESS_CHOICES_MAP = {
  'all': 'ALL',
  'creatorapponly': 'CREATOR_APP_ONLY'
  }

MEET_SPACE_RESTRICTIONS_CHOICES_MAP = {
  'hostsonly': 'HOSTS_ONLY',
  'norestriction': 'NO_RESTRICTION'
  }

#MEET_SPACE_FIRSTJOINERTYPE_CHOICES_MAP = {
#  'hostsonly': 'HOSTS_ONLY',
#  'anyone': 'ANYONE'
#  }

MEET_SPACE_ARTIFACT_SUB_OPTIONS = {
  'recordingConfig': 'autoRecordingGeneration',
  'smartNotesConfig': 'autoSmartNotesGeneration',
  'transcriptionConfig': 'autoTranscriptionGeneration'
  }

#	[accesstype open|trusted|restricted]
#	[entrypointaccess all|creatorapponly]
#	[moderation <Boolean>]
#	[chatrestriction hostsonly|norestriction]
#	[reactionrestriction hostsonly|norestriction]
#	[presentrestriction hostsonly|norestriction]
#	[defaultjoinasviewer <Boolean>]
#	[firstjoiner hostsonly|anyone]
#	[autorecording <Boolean>]
#	[autosmartnotes <Boolean>]
#	[autotranscription <Boolean>]
def _getMeetSpaceParameters(myarg, body):
  option = MEET_SPACE_OPTIONS_MAP.get(myarg, None)
  if option is None:
    return False
  if option == 'accessType':
    body['config'][option] = getChoice(MEET_SPACE_ACCESSTYPE_CHOICES).upper()
  elif option == 'entryPointAccess':
    body['config'][option] = getChoice(MEET_SPACE_ENTRYPOINTACCESS_CHOICES_MAP, mapChoice=True)
  elif option == 'moderation':
    body['config'][option] = 'ON' if getBoolean() else 'OFF'
  elif option in {'chatRestriction', 'reactionRestriction', 'presentRestriction'}:
    body['config'].setdefault('moderationRestrictions', {})
    body['config']['moderationRestrictions'][option] = getChoice(MEET_SPACE_RESTRICTIONS_CHOICES_MAP, mapChoice=True)
  elif option == 'defaultJoinAsViewerType':
    body['config'][option] = 'ON' if getBoolean() else 'OFF'
#  elif option == 'firstJoinerType':
#    body['config'][option] = getChoice(MEET_SPACE_FIRSTJOINERTYPE_CHOICES_MAP, mapChoice=True)
  elif option in {'recordingConfig', 'transcriptionConfig', 'smartNotesConfig'}:
    body['config'].setdefault('artifactConfig', {})
    body['config']['artifactConfig'].setdefault(option, {})
    body['config']['artifactConfig'][option][MEET_SPACE_ARTIFACT_SUB_OPTIONS[option]] = 'ON' if getBoolean() else 'OFF'
  return True

# gam <UserTypeEntity> create meetspace
#	<MeetSpaceOptions>*
#	[formatjson|returnidonly]
def createMeetSpace(users):
  FJQC = FormatJSONQuoteChar()
  body = {'config': {'accessType': 'TRUSTED',
                     'entryPointAccess': 'ALL',
#                     'moderation': 'OFF',
#                     'moderationRestrictions': {},
#                     'firstJoinerType': 'ANYONE',
                     }}
  returnIdOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getMeetSpaceParameters(myarg, body):
      pass
    elif myarg == 'returnidonly':
      returnIdOnly = True
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, meet, kvList = buildMeetServiceObject(API.MEET_SPACES, user, i, count, [Ent.MEET_SPACE, None])
    if not meet:
      continue
    try:
      space = callGAPI(meet.spaces(), 'create',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       body=body)
      if not returnIdOnly:
        kvList[-1] = space['name']
        if not FJQC.formatJSON:
          entityActionPerformed(kvList, i, count)
        Ind.Increment()
        _showMeetItem(space, FJQC)
        Ind.Decrement()
      else:
        writeStdout(f'{space["name"]}\n')
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.MEET_SPACE, None], str(e))

# gam <UserTypeEntity> update meetspace <MeetSpaceName>
#	<MeetSpaceOptions>*
#	[formatjson]
def updateMeetSpace(users):
  FJQC = FormatJSONQuoteChar()
  name = None
  body = {'config': {}}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if (myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/')):
      name = _getMain().getSpaceName(myarg)
    elif _getMeetSpaceParameters(myarg, body):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if not name:
    missingArgumentExit('space')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, meet, kvList = buildMeetServiceObject(API.MEET_SPACES, user, i, count, [Ent.MEET_SPACE, name])
    if not meet:
      continue
    try:
      space = callGAPI(meet.spaces(), 'patch',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       name=name, updateMask='', body=body)
      if not FJQC.formatJSON:
        entityActionPerformed(kvList, i, count)
      Ind.Increment()
      _showMeetItem(space, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.MEET_SPACE, name], str(e))

# gam <UserTypeEntity> info meetspace <MeetSpaceName>
#	[formatjson]
def infoMeetSpace(users):
  FJQC = FormatJSONQuoteChar()
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if (myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/')):
      name = _getMain().getSpaceName(myarg)
    else:
      FJQC.GetFormatJSON(myarg)
  if not name:
    missingArgumentExit('space')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, meet, kvList = buildMeetServiceObject(API.MEET_SPACES, user, i, count, [Ent.MEET_SPACE, name])
    if not meet:
      continue
    try:
      space = callGAPI(meet.spaces(), 'get',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       name=name)
      if not FJQC.formatJSON:
        entityPerformAction(kvList, i, count)
      Ind.Increment()
      _showMeetItem(space, FJQC)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit(kvList, str(e))

# gam <UserTypeEntity> end meetconference <MeetSpaceName>
def endMeetConference(users):
  name = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if (myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/')):
      name = _getMain().getSpaceName(myarg)
    else:
      unknownArgumentExit()
  if not name:
    missingArgumentExit('space')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, meet, kvList = buildMeetServiceObject(API.MEET_SPACES, user, i, count, [Ent.MEET_SPACE, name, Ent.MEET_CONFERENCE, None])
    if not meet:
      continue
    try:
      callGAPI(meet.spaces(), 'endActiveConference',
               throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
               name=name)
      entityActionPerformed(kvList, i,count)
    except (GAPI.failedPrecondition, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.MEET_CONFERENCE, name], str(e))

def _getMeetPageMessage(entityType, user, i, count, pfilter):
  printGettingAllEntityItemsForWhom(entityType, user, i, count, pfilter)
  return getPageMessageForWhom()

MEET_CONFERENCE_TIME_OBJECTS = {'startTime', 'endTime', 'expireTime', 'earliestStartTime', 'latestEndTime'}

def _showMeetConfItem(citem, entityType, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(citem, timeObjects=MEET_CONFERENCE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([entityType, citem['name']], i, count)
  Ind.Increment()
  showJSON(None, citem, timeObjects=MEET_CONFERENCE_TIME_OBJECTS)
  Ind.Decrement()

def _printMeetConfItem(user, citem, csvPF, FJQC):
  baserow = {'User': user}
  row = flattenJSON(citem, flattened=baserow.copy(), timeObjects=MEET_CONFERENCE_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    row = baserow.copy()
    row.update({'name': citem['name'],
                'JSON': json.dumps(cleanJSON(citem, timeObjects=MEET_CONFERENCE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
    csvPF.WriteRowNoFilter(row)

# gam <UserItem> show meetconferences
#	[space <MeetSpaceName>] [code <String>]
#	[andquery|orquery <String>] [querytime<String> <Time>]
#	[formatjson]
# gam <UserItem> print meetconferences [todrive <ToDriveAttribute>*]
#	[space <MeetSpaceName>] [code <String>]
#	[andquery|orquery <String>] [querytime<String> <Time>]
#	[formatjson [quotechar <Character>]]
def printShowMeetConferences(users):
  def _updateQuery(conjunction, clause):
    if queries[0]:
      queries[0] += f' {conjunction} '
    queries[0] += clause

  csvPF = CSVPrintFile(['User', 'space', 'name', 'startTime', 'endTime', 'expireTime']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  queries = ['']
  queryTimes = {}
  pfilter = ''
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif (myarg == 'space' or myarg.startswith('spaces/') or myarg.startswith('space/')):
      _updateQuery('AND', f'space.name = "{getSpaceName(myarg)}"')
    elif myarg == 'code':
      _updateQuery('AND', f'space.meeting_code = "{getString(Cmd.OB_STRING)}"')
    elif  myarg == 'andquery':
      _updateQuery('AND', getString(Cmd.OB_QUERY))
    elif  myarg == 'orquery':
      _updateQuery('OR', getString(Cmd.OB_QUERY))
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getMain().substituteQueryTimes(queries, queryTimes)
  if queries[0]:
    pfilter = kwargs['filter'] = queries[0]
  else:
    pfilter = None
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, meet, kvList = buildMeetServiceObject(API.MEET_READONLY, user, i, count, [Ent.MEET_CONFERENCE, None])
    if not meet:
      continue
    try:
      confRecs = callGAPIpages(meet.conferenceRecords(), 'list', 'conferenceRecords',
                               pageMessage=_getMeetPageMessage(Ent.MEET_CONFERENCE, user, i, count, pfilter),
                               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                               pageSize=100, **kwargs)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit(kvList, str(e))
      continue
    jcount = len(confRecs)
    if jcount == 0:
      setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, Ent.MEET_CONFERENCE, i, count)
      Ind.Increment()
      j = 0
      for confRec in confRecs:
        j += 1
        _showMeetConfItem(confRec, Ent.MEET_CONFERENCE, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for confRec in confRecs:
        _printMeetConfItem(user, confRec, csvPF, FJQC)
  if csvPF:
    csvPF.writeCSVfile(Ent.Plural(Ent.MEET_CONFERENCE))

# gam <UserItem> show meetparticipants <MeetConferenceName>
#	[query <String>] [querytime<String> <Time>]
#	[formatjson]
# gam <UserItem> print meetparticipants <MeetConferenceName> [todrive <ToDriveAttribute>*]
#	[query <String>] [querytime<String> <Time>]
#	[formatjson [quotechar <Character>]]
# gam <UserItem> show meetrecordings <MeetConferenceName>
#	[formatjson]
# gam <UserItem> print meetrecordings <MeetConferenceName> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
# gam <UserItem> show meettranscripts <MeetConferenceName>
#	[formatjson]
# gam <UserItem> print meettranscripts <MeetConferenceName> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def _printShowMeetItems(users, entityType):
  def _updateQuery(conjunction, clause):
    if queries[0]:
      queries[0] += f' {conjunction} '
    queries[0] += clause

  csvPF = CSVPrintFile(['User', 'name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  queries = ['']
  queryTimes = {}
  pfilter = ''
  kwargs = {}
  parent = getString(Cmd.OB_MEET_CONFERENCE_NAME)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif entityType == Ent.MEET_PARTICIPANT and myarg == 'andquery':
      _updateQuery('AND', getString(Cmd.OB_QUERY))
    elif entityType == Ent.MEET_PARTICIPANT and myarg == 'orquery':
      _updateQuery('OR', getString(Cmd.OB_QUERY))
    elif entityType == Ent.MEET_PARTICIPANT and myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getMain().substituteQueryTimes(queries, queryTimes)
  if queries[0]:
    pfilter = kwargs['filter'] = queries[0]
  else:
    pfilter = None
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, meet, kvList = buildMeetServiceObject(API.MEET_READONLY, user, i, count, [Ent.MEET_CONFERENCE, parent])
    if not meet:
      continue
    if entityType == Ent.MEET_PARTICIPANT:
      service = meet.conferenceRecords().participants()
      recType = 'participants'
      pageSize = 250
    elif entityType == Ent.MEET_RECORDING:
      service = meet.conferenceRecords().recordings()
      recType = 'recordings'
      pageSize = 100
    else:
      service = meet.conferenceRecords().transcripts()
      recType = 'transcripts'
      pageSize = 100
    try:
      confRecs = callGAPIpages(service, 'list', recType,
                               pageMessage=_getMeetPageMessage(entityType, user, i, count, pfilter),
                               throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                               parent=parent, pageSize=pageSize, **kwargs)
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit(kvList, str(e))
      continue
    jcount = len(confRecs)
    if jcount == 0:
      setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    if not csvPF:
      if not FJQC.formatJSON:
        entityPerformActionNumItems(kvList, jcount, entityType, i, count)
      Ind.Increment()
      j = 0
      for confRec in confRecs:
        j += 1
        _showMeetConfItem(confRec, entityType, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for confRec in confRecs:
        _printMeetConfItem(user, confRec, csvPF, FJQC)
  if csvPF:
    csvPF.writeCSVfile(Ent.Plural(entityType))

def printShowMeetParticipants(users):
  _printShowMeetItems(users, Ent.MEET_PARTICIPANT)

def printShowMeetRecordings(users):
  _printShowMeetItems(users, Ent.MEET_RECORDING)

def printShowMeetTranscripts(users):
  _printShowMeetItems(users, Ent.MEET_TRANSCRIPT)

