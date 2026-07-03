"""Drive activity reporting and settings display.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
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

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()

APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = f'{APPLICATION_VND_GOOGLE_APPS}document'
MIMETYPE_GA_DRAWING = f'{APPLICATION_VND_GOOGLE_APPS}drawing'
MIMETYPE_GA_FILE = f'{APPLICATION_VND_GOOGLE_APPS}file'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_FORM = f'{APPLICATION_VND_GOOGLE_APPS}form'
MIMETYPE_GA_FUSIONTABLE = f'{APPLICATION_VND_GOOGLE_APPS}fusiontable'
MIMETYPE_GA_JAM = f'{APPLICATION_VND_GOOGLE_APPS}jam'
MIMETYPE_GA_MAP = f'{APPLICATION_VND_GOOGLE_APPS}map'
MIMETYPE_GA_PRESENTATION = f'{APPLICATION_VND_GOOGLE_APPS}presentation'
MIMETYPE_GA_SCRIPT = f'{APPLICATION_VND_GOOGLE_APPS}script'
MIMETYPE_GA_SCRIPT_JSON = f'{APPLICATION_VND_GOOGLE_APPS}script+json'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'
MIMETYPE_GA_3P_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}drive-sdk'
MIMETYPE_GA_SITE = f'{APPLICATION_VND_GOOGLE_APPS}site'
MIMETYPE_GA_SPREADSHEET = f'{APPLICATION_VND_GOOGLE_APPS}spreadsheet'
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "
WITH_ANY_FILE_NAME = "name = '{0}'"
WITH_MY_FILE_NAME = ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
WITH_OTHER_FILE_NAME = NOT_ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
ROOT = 'root'
ORPHANS = 'Orphans'
SHARED_WITHME = 'SharedWithMe'
SHARED_DRIVES = 'SharedDrives'

def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def printDriveActivity(users):
  def _getUserInfo(userId):
    if userId.startswith('people/'):
      userId = userId[7:]
    entry = userInfo.get(userId)
    if entry is None:
      try:
        result = _getMain().callGAPI(cd.users(), 'get',
                          throwReasons=GAPI.USER_GET_THROW_REASONS+[GAPI.INVALID_INPUT],
                          userKey=userId, fields='primaryEmail,name.fullName')
        entry = (result['primaryEmail'], result['name']['fullName'])
      except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
              GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.invalidInput):
        entry = (f'uid:{userId}', _getMain().UNKNOWN)
      userInfo[userId] = entry
    return entry

  def _updateKnownUsers(structure):
    if isinstance(structure, list):
      for v in structure:
        if isinstance(v, (dict, list)):
          _updateKnownUsers(v)
    elif isinstance(structure, dict):
      for k, v in sorted(structure.items()):
        if k != 'knownUser':
          if isinstance(v, (dict, list)):
            _updateKnownUsers(v)
        else:
          entry = _getUserInfo(v['personName'])
          v['emailAddress'] = entry[0]
          v['personName'] = entry[1]
          break

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  startEndTime = _getMain().StartEndTime()
  baseFileList = []
  query = ''
  activityFilter = ''
  actions = set()
  strategy = 'none'
  negativeAction = stripCRsFromName = False
  maxActivities = 0
  _getMain().checkArgumentPresent(['v2'])
  csvPF = _getMain().CSVPrintFile([f'user{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name',
                        f'user{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}emailAddress',
                        f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}id',
                        f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name',
                        f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}mimeType',
                        'eventTime'],
                       'sortall')
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  userInfo = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'fileid':
      baseFileList.append({'id': _getMain().getString(Cmd.OB_DRIVE_FILE_ID), 'mimeType': MIMETYPE_GA_DOCUMENT})
    elif myarg == 'folderid':
      baseFileList.append({'id': _getMain().getString(Cmd.OB_DRIVE_FOLDER_ID), 'mimeType': MIMETYPE_GA_FOLDER})
    elif myarg == 'drivefilename':
      query = f"mimeType != '{MIMETYPE_GA_FOLDER}' and name = '{getEscapedDriveFileName()}'"
    elif myarg == 'drivefoldername':
      query = f"mimeType = '{MIMETYPE_GA_FOLDER}' and name = '{getEscapedDriveFileName()}'"
    elif myarg == 'query':
      query = _mapDrive2QueryToDrive3(_getMain().getString(Cmd.OB_QUERY))
    elif myarg in {'start', 'starttime', 'end', 'endtime', 'yesterday', 'today', 'range', 'thismonth', 'previousmonths'}:
      startEndTime.Get(myarg)
    elif myarg in {'action', 'actions'}:
      negativeAction = _getMain().checkArgumentPresent('not')
      for action in _getMain()._getFieldsList():
        if action in DRIVE_ACTIVITY_ACTION_MAP:
          mappedAction = DRIVE_ACTIVITY_ACTION_MAP[action]
          if mappedAction:
            actions.add(mappedAction)
        else:
          _getMain().invalidChoiceExit(action, DRIVE_ACTIVITY_ACTION_MAP, True)
    elif myarg in {'allevents', 'combinedevents', 'singleevents'}:
      pass
    elif myarg in {'consolidationstrategy', 'groupingstrategy'}:
      strategy = _getMain().getChoice(CONSOLIDATION_GROUPING_STRATEGY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'idmapfile':
      f, csvFile, _ = _getMain().openCSVFileReader(_getMain().getString(Cmd.OB_FILE_NAME))
      for row in csvFile:
        userInfo[row['id']] = (row['primaryEmail'], row.get('name.fullName', _getMain().UNKNOWN))
      _getMain().closeFile(f)
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    elif myarg == 'maxactivities':
      maxActivities = _getMain().getInteger(minVal=0)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not baseFileList and not query:
    baseFileList = [{'id': ROOT, 'mimeType': MIMETYPE_GA_FOLDER}]
  if startEndTime.startTime:
    if activityFilter:
      activityFilter += ' AND '
    activityFilter += f'time >= "{startEndTime.startTime}"'
  if startEndTime.endTime:
    if activityFilter:
      activityFilter += ' AND '
    activityFilter += f'time <= "{startEndTime.endTime}"'
  if actions:
    if activityFilter:
      activityFilter += ' AND '
    activityFilter += f'{"-" if negativeAction else ""}detail.action_detail_case:({" ".join(actions)})'
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, activity = _getMain().buildGAPIServiceObject(API.DRIVEACTIVITY, user, i, count)
    if not activity:
      continue
    _, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    fileList = baseFileList[:]
    if query:
      if GC.Values[GC.SHOW_GETTINGS]:
        _getMain().printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, i, count, query=query)
      try:
        fileList.extend(_getMain().callGAPIpages(drive.files(), 'list', 'files',
                                      pageMessage=_getMain().getPageMessageForWhom(),
                                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                                  GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND],
                                      retryReasons=[GAPI.UNKNOWN_ERROR],
                                      q=query, fields='nextPageToken,files(id,mimeType)', pageSize=GC.Values[GC.DRIVE_MAX_RESULTS]))
        if not fileList:
          _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], _getMain().emptyQuery(query, Ent.DRIVE_FILE_OR_FOLDER), i, count)
          continue
      except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest):
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], _getMain().invalidQuery(query), i, count)
        break
      except GAPI.fileNotFound:
        _getMain().printGotEntityItemsForWhom(0)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    for f_file in fileList:
      fileId = f_file['id']
      entityType = Ent.DRIVE_FOLDER_ID if f_file['mimeType'] == MIMETYPE_GA_FOLDER else Ent.DRIVE_FILE_ID
      if entityType == Ent.DRIVE_FILE_ID:
        drive_key = 'itemName'
      else:
        drive_key = 'ancestorName'
      qualifier = f' for {Ent.Singular(entityType)}: {fileId}'
      _getMain().printGettingAllEntityItemsForWhom(Ent.ACTIVITY, user, i, count, qualifier=qualifier)
      pageMessage = _getMain().getPageMessageForWhom()
      body = {
        'consolidationStrategy': {strategy: {}},
        'pageSize': GC.Values[GC.ACTIVITY_MAX_RESULTS],
        'pageToken': None,
        drive_key: f'items/{fileId}',
        'filter': activityFilter}
      numActivities = 0
      try:
        feed = _getMain().yieldGAPIpages(activity.activity(), 'query', 'activities',
                              pageMessage=pageMessage, maxItems=maxActivities,
                              throwReasons=GAPI.ACTIVITY_THROW_REASONS,
                              fields='nextPageToken,activities', body=body, pageArgsInBody=True)
        for activities in feed:
          for activityEvent in activities:
            eventRow = {}
            actors = activityEvent.get('actors', [])
            if actors:
              userId = actors[0].get('user', {}).get('knownUser', {}).get('personName', '')
              if not userId:
                userId = actors[0].get('impersonation', {}).get('impersonatedUser', {}).get('knownUser', {}).get('personName', '')
              if userId:
                entry = _getUserInfo(userId)
                eventRow[f'user{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name'] = entry[1]
                eventRow[f'user{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}emailAddress'] = entry[0]
            targets = activityEvent.get('targets', [])
            if targets:
              driveItem = targets[0].get('driveItem')
              if driveItem:
                eventRow[f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}id'] = driveItem['name'][6:]
                if stripCRsFromName:
                  driveItem['title'] = _stripControlCharsFromName(driveItem['title'])
                eventRow[f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name'] = driveItem['title']
                eventRow[f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}mimeType'] = driveItem['mimeType']
              else:
                sharedDrive = targets[0].get('teamDrive')
                if sharedDrive:
                  eventRow[f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}id'] = sharedDrive['name'][11:]
                  if stripCRsFromName:
                    sharedDrive['title'] = _stripControlCharsFromName(sharedDrive['title'])
                  eventRow[f'target{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name'] = sharedDrive['title']
            if 'timestamp' in activityEvent:
              eventRow['eventTime'] = formatLocalTime(activityEvent['timestamp'])
            elif 'timeRange' in activityEvent:
              timeRange = activityEvent['timeRange']
              eventRow['eventTime'] = f'{formatLocalTime(timeRange["startTime"])}-{formatLocalTime(timeRange["endTime"])}'
            _updateKnownUsers(activityEvent)
            if not FJQC.formatJSON:
              activityEvent.pop('timestamp', None)
              activityEvent.pop('timeRange', None)
              _getMain().flattenJSON(activityEvent, flattened=eventRow)
              csvPF.WriteRowTitles(eventRow)
            else:
              checkRow = eventRow.copy()
              _getMain().flattenJSON(activityEvent, flattened=checkRow)
              if csvPF.CheckRowTitles(checkRow):
                eventRow['JSON'] = json.dumps(_getMain().cleanJSON(activityEvent), ensure_ascii=False, sort_keys=True)
                csvPF.WriteRowNoFilter(eventRow)
            numActivities += 1
            if maxActivities and numActivities >= maxActivities:
              break
      except GAPI.badRequest as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, entityType, fileId], str(e), i, count)
        continue
      except GAPI.serviceNotAvailable as e:
        _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
  csvPF.writeCSVfile('Drive Activity')

DRIVESETTINGS_FIELDS_CHOICE_MAP = {
  'appinstalled': 'appInstalled',
  'exportformats': 'exportFormats',
  'foldercolorpalette': 'folderColorPalette',
  'importformats': 'importFormats',
  'largestchangeid': 'largestChangeId',
  'limit': 'limit',
  'maximportsizes': 'maxImportSizes',
  'maxuploadsize': 'maxUploadSize',
  'name': 'name',
  'permissionid': 'permissionId',
  'rootfolderid': 'rootFolderId',
  'drivethemes': 'driveThemes',
  'shareddrivethemes': 'driveThemes',
  'teamdrivethemes': 'driveThemes',
  'usage': 'usage',
  'usageindrive': 'usageInDrive',
  'usageindrivetrash': 'usageInDriveTrash',
  }

DRIVESETTINGS_SCALAR_FIELDS = [
  'name',
  'appInstalled',
  'largestChangeId',
  'limit',
  'maxUploadSize',
  'permissionId',
  'rootFolderId',
  'usage',
  'usageInDrive',
  'usageInDriveTrash',
  ]

DRIVESETTINGS_USAGE_BYTES_FIELDS = {
  'usage': 'usageBytes',
  'usageInDrive': 'usageInDriveBytes',
  'usageInDriveTrash': 'usageInDriveTrashBytes',
  }

def _showSharedDriveThemeSettings(themes):
  Ind.Increment()
  for theme in themes:
    _getMain().printKeyValueList(['id', theme['id']])
    Ind.Increment()
    _getMain().printKeyValueList(['backgroundImageLink', theme['backgroundImageLink']])
    _getMain().printKeyValueList(['colorRgb', theme['colorRgb']])
    Ind.Decrement()
  Ind.Decrement()

# gam <UserTypeEntity> print drivesettings [todrive <ToDriveAttribute>*]
#	[allfields|<DriveSettingsFieldName>*|(fields <DriveSettingsFieldNameList>)]
#	[delimiter <Character>] [showusagebytes]
# gam <UserTypeEntity> show drivesettings
#	[allfields|<DriveSettingsFieldName>*|(fields <DriveSettingsFieldNameList>)]
#	[delimiter <Character>] [showusagebytes]
def printShowDriveSettings(users):
  def _showFormats(title):
    if title in fieldsList and title in feed:
      _getMain().printKeyValueList([title, None])
      Ind.Increment()
      for item, value in sorted(feed[title].items()):
        _getMain().printKeyValueList([item, delimiter.join(value)])
      Ind.Decrement()

  def _showSetting(title):
    if title in fieldsList and title in feed:
      if not isinstance(feed[title], list):
        _getMain().printKeyValueList([title, feed[title]])
      else:
        _getMain().printKeyValueList([title, delimiter.join(feed[title])])

  def _addFormats(row, title):
    if title in fieldsList and title in feed:
      jcount = len(feed[title])
      row[title] = jcount
      j = 0
      for item, value in sorted(feed[title].items()):
        row[f'{title}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j:02d}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{item}'] = delimiter.join(value)
        j += 1

  def _addSetting(row, title):
    if title in fieldsList and title in feed:
      if not isinstance(feed[title], list):
        row[title] = feed[title]
      else:
        row[title] = delimiter.join(feed[title])

  csvPF = _getMain().CSVPrintFile(['email'], ['email']+DRIVESETTINGS_SCALAR_FIELDS) if Act.csvFormat() else None
  fieldsList = []
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  showUsageBytes = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg == 'allfields':
      fieldsList.extend(DRIVESETTINGS_FIELDS_CHOICE_MAP.values())
    elif _getMain().getFieldsList(myarg, DRIVESETTINGS_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg == 'showusagebytes':
      showUsageBytes = True
    else:
      _getMain().unknownArgumentExit()
  if not fieldsList:
    fieldsList = DRIVESETTINGS_SCALAR_FIELDS[:]
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.DRIVE_SETTINGS, user, i, count)
    try:
      feed = _getMain().callGAPI(drive.about(), 'get',
                      throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                      fields='*')
      feed['name'] = feed['user']['displayName']
      feed['maxUploadSize'] = formatFileSize(int(feed['maxUploadSize']))
      feed['permissionId'] = feed['user']['permissionId']
      if 'limit' in feed['storageQuota']:
        feed['limit'] = formatFileSize(int(feed['storageQuota']['limit']))
      else:
        feed['limit'] = 'UNLIMITED'
      for setting in ['usage', 'usageInDrive', 'usageInDriveTrash']:
        uval = int(feed['storageQuota'].get(setting, '0'))
        feed[setting] = _getMain().formatFileSize(uval)
        if showUsageBytes:
          feed[DRIVESETTINGS_USAGE_BYTES_FIELDS[setting]] = uval
      if 'rootFolderId' in fieldsList:
        feed['rootFolderId'] = _getMain().callGAPI(drive.files(), 'get',
                                        throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                        fileId=ROOT, fields='id')['id']
      if 'largestChangeId' in fieldsList:
        feed['largestChangeId'] = _getMain().callGAPI(drive.changes(), 'getStartPageToken',
                                           throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                                           fields='startPageToken')['startPageToken']
      if not csvPF:
        _getMain().entityPerformActionNumItems([Ent.USER, user], 1, Ent.DRIVE_SETTINGS, i, count)
        Ind.Increment()
        for setting in DRIVESETTINGS_SCALAR_FIELDS:
          _showSetting(setting)
        if showUsageBytes:
          for title, setting in DRIVESETTINGS_USAGE_BYTES_FIELDS.items():
            if title in fieldsList and setting in feed:
              _getMain().printKeyValueList([setting, feed[setting]])
        _showSetting('folderColorPalette')
        _showFormats('exportFormats')
        _showFormats('importFormats')
        if 'maxImportSizes' in fieldsList and 'maxImportSizes' in fieldsList:
          _getMain().printKeyValueList(['maxImportSizes', None])
          Ind.Increment()
          for setting, value in feed['maxImportSizes'].items():
            _getMain().printKeyValueList([setting, _getMain().formatFileSize(int(value))])
          Ind.Decrement()
        if 'driveThemes' in fieldsList and 'driveThemes' in feed:
          _getMain().printKeyValueList(['driveThemes', None])
          _showSharedDriveThemeSettings(feed['driveThemes'])
        Ind.Decrement()
      else:
        row = {'email': user}
        for setting in DRIVESETTINGS_SCALAR_FIELDS:
          _addSetting(row, setting)
        if showUsageBytes:
          for title, setting in DRIVESETTINGS_USAGE_BYTES_FIELDS.items():
            if title in fieldsList and setting in feed:
              row[setting] = feed[setting]
        _addSetting(row, 'folderColorPalette')
        _addFormats(row, 'exportFormats')
        _addFormats(row, 'importFormats')
        if 'maxImportSizes' in fieldsList and 'maxImportSizes' in fieldsList:
          jcount = len(feed['maxImportSizes'])
          row['maxImportSizes'] = jcount
          j = 0
          for setting, value in feed['maxImportSizes'].items():
            row[f'maxImportSizes{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{setting}'] = _getMain().formatFileSize(int(value))
            j += 1
        if 'driveThemes' in fieldsList and 'driveThemes' in feed:
          jcount = len(feed['driveThemes'])
          row['driveThemes'] = jcount
          j = 0
          for setting in feed['driveThemes']:
            row[f'driveThemes{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j:02d}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}id'] = setting['id']
            row[f'driveThemes{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j:02d}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}backgroundImageLink'] = setting['backgroundImageLink']
            row[f'driveThemes{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j:02d}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}colorRgb'] = setting['colorRgb']
            j += 1
        csvPF.WriteRowTitles(row)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('User Drive Settings')

# gam <UserTypeEntity> show shareddrivethemes
def showSharedDriveThemes(users):
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = _getMain().buildGAPIServiceObject(API.DRIVE3, user, i, count)
    if not drive:
      continue
    try:
      themes = _getMain().callGAPIitems(drive.about(), 'get', 'driveThemes',
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                             fields='driveThemes')
      jcount = len(themes)
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.SHAREDDRIVE_THEME, i, count)
      _showSharedDriveThemeSettings(themes)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      _getMain().userDriveServiceNotEnabledWarning(user, str(e), i, count)

def doShowSharedDriveThemes():
  showSharedDriveThemes([_getMain()._getAdminEmail()])

