"""Drive file listing and printing.

"""

"""GAM Google Drive file, permission, shared drive, and label management."""

import json


from gam.cmd.drive.core import _getSharedDriveNameFromId, _mapDrive2QueryToDrive3, _simpleFileIdEntityList, _validateUserGetFileIDs, _validateUserSharedDrive, cleanFileIDsList, getDriveFileEntity, getDriveFileEntitySharedDriveOnly, initDriveFileEntity
from gam.cmd.drive.filepaths import _finalizeIncludeLabels, _finalizeIncludePermissionsForView, _formatFileDriveLabels, _mapDriveInfo, _setGetCheckFilePermissions, _setGetPermissionsForMyDriveSharedDrives, _setSkipObjects, getFilePaths, initFilePathInfo

from gam.util.csv_pf import DEFAULT_SKIP_OBJECTS

from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.constants import NO_ENTITIES_FOUND_RC, TEAM_DRIVE, WITH_PARENTS

from gam.var import Act, Cmd, Ent, Ind

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
WITH_ANY_FILE_NAME = "name = '{0}'"
ROOT = 'root'
ORPHANS = 'Orphans'
SHARED_WITHME = 'SharedWithMe'
SHARED_DRIVES = 'SharedDrives'

from gam.cmd.drive.filepaths import (
    addFilePathsToInfo,
    addFilePathsToRow,
    DRIVEFILE_BASIC_PERMISSION_FIELDS, DRIVEFILE_ORDERBY_CHOICE_MAP,
    DRIVE_FIELDS_CHOICE_MAP, DRIVE_LIST_FIELDS, DRIVE_SUBFIELDS_CHOICE_MAP,
    DRIVE_TIME_OBJECTS, DriveFileFields, FILEPATH_FIELDS_TITLES,
    SHOWLABELS_CHOICES, _finalizeIncludeLabels,
    _finalizeIncludePermissionsForView, _formatFileDriveLabels,
    _mapDriveInfo, _setGetCheckFilePermissions,
    _setGetPermissionsForMyDriveSharedDrives, _setSkipObjects,
    getFilePaths, initFilePathInfo,
)

from gam.cmd.drive.core import (
    _getSharedDriveNameFromId,
    _mapDrive2QueryToDrive3,
    _simpleFileIdEntityList,
    _validateUserGetFileIDs,
    _validateUserSharedDrive,
    cleanFileIDsList,
    getDriveFileEntity,
    getDriveFileEntitySharedDriveOnly,
    initDriveFileEntity,
)

from gam.cmd.drive.filetree import (
    CHECK_LOCATION_FIELDS_TITLES,
    DRIVE_INDEXED_TITLES,
    DriveListParameters,
    FILECOUNT_SUMMARY_CHOICE_MAP,
    FILECOUNT_SUMMARY_NONE,
    FILECOUNT_SUMMARY_ONLY,
    FILECOUNT_SUMMARY_USER,
    FILELIST_FIELDS_TITLES,
    OWNED_BY_ME_FIELDS_TITLES,
    SIZE_FIELD_CHOICE_MAP,
    _getGettingEntity,
    extendFileTree,
    extendFileTreeParents,
    initFileTree,
    noFileSelectFileIdEntity,
)
from gam.util.api_call import callGAPI, callGAPIitems, callGAPIpages, yieldGAPIpages
from gam.util.args import (
    NEVER_TIME,
    OrderBy,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getInteger,
    getString,
    getTimeOrDeltaFromNow,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    addFieldToFieldsList,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    invalidQuery,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printGotEntityItemsForWhom,
    printKeyValueList,
    printLine,
    setGettingAllEntityItemsForWhom,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import invalidChoiceExit, unknownArgumentExit, usageErrorExit
from gam.util.fileio import UNKNOWN
from gam.util.output import (
    _stripControlCharsFromName,
    flushStderr,
    formatFileSize,
    formatLocalTime,
    setSysExitRC,
    writeStderr,
    writeStdout,
)

MY_DRIVE = 'My Drive'
NEVER_TIME = '1970-01-01T00:00:00.000Z'

def printFileList(users):
  def _setSelectionFields():
    if fileIdEntity or filepath:
      _setSkipObjects(skipObjects, FILELIST_FIELDS_TITLES, DFF.fieldsList)
    if DLP.showOwnedBy is not None:
      _setSkipObjects(skipObjects, OWNED_BY_ME_FIELDS_TITLES, DFF.fieldsList)
    if DLP.showSharedByMe is not None or DLP.checkLocation is not None:
      _setSkipObjects(skipObjects, CHECK_LOCATION_FIELDS_TITLES, DFF.fieldsList)
    if DLP.mimeTypeCheck.mimeTypes:
      _setSkipObjects(skipObjects, ['mimeType'], DFF.fieldsList)
    if countsOnly:
      skipObjects.discard('mimeType')
      if 'mimeType' not in DFF.fieldsList:
        DFF.fieldsList.append('mimeType')
      skipObjects.discard(sizeField)
      if (showSize or showSizeUnits) and sizeField not in DFF.fieldsList:
        DFF.fieldsList.append(sizeField)
    if (DLP.minimumFileSize is not None) or (DLP.maximumFileSize is not None):
      _setSkipObjects(skipObjects, [sizeField], DFF.fieldsList)
    if DLP.filenameMatchPattern or showParent:
      _setSkipObjects(skipObjects, ['name'], DFF.fieldsList)
    if DLP.excludeTrashed:
      _setSkipObjects(skipObjects, ['trashed'], DFF.fieldsList)
    if DLP.PM.permissionMatches:
      for field in DFF.fieldsList:
        if field.startswith('permissions'):
          break
      else:
        skipObjects.add('permissions')
      if 'permissions' not in DFF.fieldsList:
        for field in DLP.PM.permissionFields:
          permfield = 'permissions.'+field
          if permfield not in DFF.fieldsList:
            DFF.fieldsList.append(permfield)
    if DLP.onlySharedDrives or getPermissionsForSharedDrives or DFF.showSharedDriveNames:
      _setSkipObjects(skipObjects, ['driveId'], DFF.fieldsList)

  def _printFileInfoRow(baserow, fileInfo):
    row = baserow.copy()
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(flattenJSON(fileInfo, flattened=row, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS,
                                       simpleLists=simpleLists, delimiter=delimiter))
    else:
      if addCSVData and includeCSVDataInJSON:
        fileInfo.update(addCSVData)
      row['JSON'] = json.dumps(cleanJSON(fileInfo, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS),
                               ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowTitlesJSONNoFilter(row)

  def _printFileInfo(drive, user, f_file, cleanFileName):
    nonlocal getSharedDriveACLsCount
    driveId = f_file.get('driveId')
    getCheckFilePermissions = _setGetCheckFilePermissions(f_file, getPermissionDetailsForMyDrive, getPermissionsForSharedDrives,
                                                          driveId, DLP)
    if (f_file.get('noDisplay', False) or
        not DLP.CheckShowOwnedBy(f_file) or
        not DLP.CheckShowSharedByMe(f_file) or
        not DLP.CheckExcludeTrashed(f_file) or
        not DLP.CheckMimeType(f_file) or
        not DLP.CheckFileSize(f_file, sizeField) or
        not DLP.CheckFilenameMatch(f_file) or
        (not getCheckFilePermissions and not DLP.CheckFilePermissionMatches(f_file)) or
        (DLP.onlySharedDrives and not driveId)):
      return
    if getCheckFilePermissions:
      if buildTree and not incrementalPrint:
        getSharedDriveACLsCount += 1
        if getSharedDriveACLsCount % 100 == 0:
          writeStderr(f'{Msg.GOT} {getSharedDriveACLsCount} {Ent.Plural(Ent.DRIVE_FILE_OR_FOLDER_ACL)} {Msg.FOR} {gettingEntity}\n')
      try:
        f_file['permissions'] = callGAPIpages(drive.permissions(), 'list', 'permissions',
                                              throwReasons=GAPI.DRIVE3_GET_ACL_REASONS,
                                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                              fileId=f_file['id'], fields=permissionsFields, supportsAllDrives=True)
        if not DLP.CheckFilePermissionMatches(f_file):
          return
        for permission in f_file['permissions']:
          permission.pop('teamDrivePermissionDetails', None)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError,
              GAPI.insufficientAdministratorPrivileges, GAPI.insufficientFilePermissions,
              GAPI.unknownError, GAPI.invalid,
              GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy):
        pass
    row = {'Owner': user}
    fileInfo = f_file.copy()
    if cleanFileName:
      fileInfo['name'] = _stripControlCharsFromName(fileInfo['name'])
    if not pmselect and 'permissions' in fileInfo:
      fileInfo['permissions'] = DLP.GetFileMatchingPermission(fileInfo)
    if DFF.showSharedDriveNames and driveId:
      fileInfo['driveName'] = _getSharedDriveNameFromId(drive, driveId)
    if filepath:
      if not FJQC.formatJSON or not addPathsToJSON:
        addFilePathsToRow(drive, fileTree, fileInfo, filePathInfo, csvPF, row,
                          fullpath=fullpath, showDepth=showDepth, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
      else:
        addFilePathsToInfo(drive, fileTree, fileInfo, filePathInfo, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
    _mapDriveInfo(fileInfo, DFF.parentsSubFields, showParentsIdsAsList)
    if showParentsIdsAsList and 'parentsIds' in fileInfo:
      fileInfo['parents'] = len(fileInfo['parentsIds'])
    if addCSVData:
      row.update(addCSVData)
    if not countsOnly:
      if not oneItemPerRow or 'permissions' not in fileInfo:
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(flattenJSON(fileInfo, flattened=row, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS,
                                           simpleLists=simpleLists, delimiter=delimiter))
        else:
          if 'id' in fileInfo:
            row['id'] = fileInfo['id']
          if 'name' in fileInfo:
            row['name'] = fileInfo['name']
          if 'owners' in fileInfo:
            flattenJSON({'owners': fileInfo['owners']}, flattened=row, skipObjects=skipObjects)
          if addCSVData and includeCSVDataInJSON:
            fileInfo.update(addCSVData)
          row['JSON'] = json.dumps(cleanJSON(fileInfo, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS),
                                   ensure_ascii=False, sort_keys=True)
          csvPF.WriteRowTitlesJSONNoFilter(row)
      else:
        baserow = row.copy()
        if 'id' in fileInfo:
          baserow['id'] = fileInfo['id']
        if 'name' in fileInfo:
          baserow['name'] = fileInfo['name']
        if 'owners' in fileInfo:
          flattenJSON({'owners': fileInfo['owners']}, flattened=baserow, skipObjects=skipObjects)
        for permission in fileInfo.pop('permissions'):
          fileInfo['permission'] = permission
          pdetails = fileInfo['permission'].pop('permissionDetails', [])
          if not pdetails:
            _printFileInfoRow(baserow, fileInfo)
          else:
            for pdetail in pdetails:
              fileInfo['permission']['permissionDetails'] = pdetail
              _printFileInfoRow(baserow, fileInfo)
    else:
      if not countsRowFilter:
        csvPFco.UpdateMimeTypeCounts(flattenJSON(fileInfo, flattened=row, skipObjects=skipObjects, timeObjects=DRIVE_TIME_OBJECTS,
                                                 simpleLists=simpleLists, delimiter=delimiter), mimeTypeInfo, sizeField)
      else:
        mimeTypeInfo.setdefault(fileInfo['mimeType'], {'count': 0, 'size': 0})
        mimeTypeInfo[fileInfo['mimeType']]['count'] += 1
        mimeTypeInfo[fileInfo['mimeType']]['size'] += int(fileInfo.get(sizeField, '0'))

  def _printChildDriveFolderContents(drive, fileEntry, user, i, count, depth):
    parentFileEntry = fileTree.get(fileEntry['id'])
    if parentFileEntry and 'children' in parentFileEntry:
      for childFileId in parentFileEntry['children']:
        childEntry = fileTree.get(childFileId)
        if childEntry:
          if not DLP.CheckExcludeTrashed(childEntry['info']):
            continue
          if childFileId not in filesPrinted:
            filesPrinted.add(childFileId)
            # Don't show My Drive/Shared Drive unless asked when parent is 'SharedDrives'
            if showParent or parentFileEntry['info']['id'] != SHARED_DRIVES:
              _printFileInfo(drive, user, childEntry['info'].copy(), False)
          if childEntry['info']['mimeType'] == MIMETYPE_GA_FOLDER and (maxdepth == -1 or depth < maxdepth):
            _printChildDriveFolderContents(drive, childEntry['info'], user, i, count, depth+1)
      return
    q = WITH_PARENTS.format(fileEntry['id'])
    if selectSubQuery:
      q += ' and ('+selectSubQuery+')'
    if depth == 0:
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, i, count, query=q)
      pageMessage = getPageMessageForWhom()
    else:
      setGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, user, query=q)
      pageMessage = getPageMessageForWhom(clearLastGotMsgLen=False)
    try:
      children = callGAPIpages(drive.files(), 'list', 'files',
                               pageMessage=pageMessage, noFinalize=True,
                               throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                           GAPI.BAD_REQUEST],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR],
                               q=q, orderBy=DFF.orderBy, includeLabels=includeLabels, includePermissionsForView=includePermissionsForView,
                               fields=pagesFields,
                               pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], includeItemsFromAllDrives=True, supportsAllDrives=True)
      for childEntryInfo in children:
        childFileId = childEntryInfo['id']
        if showLabels is not None:
          labels = callGAPIitems(drive.files(), 'listLabels', 'labels',
                                 throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR],
                                 fileId=childFileId)
          _formatFileDriveLabels(showLabels, labels, childEntryInfo, True, delimiter)
        if filepath:
          fileTree.setdefault(childFileId, {'info': childEntryInfo})
        if childFileId not in filesPrinted:
          filesPrinted.add(childFileId)
          _printFileInfo(drive, user, childEntryInfo.copy(), stripCRsFromName)
        if childEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER and (maxdepth == -1 or depth < maxdepth):
          _printChildDriveFolderContents(drive, childEntryInfo, user, i, count, depth+1)
    except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest) as e:
      errMsg = str(e)
      if 'Invalid field selection' in errMsg or "Only a 'published' value is supported." in errMsg:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None], errMsg, i, count)
      else:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE, None], invalidQuery(selectSubQuery), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)

  def writeMimeTypeCountsRow(user, sourceId, sourceName, mimeTypeInfo):
    countTotal = sizeTotal = 0
    for mtinfo in mimeTypeInfo.values():
      countTotal += mtinfo['count']
      sizeTotal += mtinfo['size']
    row = {'Owner': user, 'Total': countTotal}
    if showSource:
      row['Source'] = sourceId
      row['Name'] = sourceName
    if showSize:
      row['Size'] = sizeTotal
    if showSizeUnits:
      row['SizeUnits'] = formatFileSize(sizeTotal)
    if addCSVData:
      row.update(addCSVData)
    for mimeType, mtinfo in sorted(mimeTypeInfo.items()):
      row[f'{mimeType}'] = mtinfo['count']
      if showMimeTypeSize:
        row[f'{mimeType}:Size'] = mtinfo['size']
    if not countsRowFilter:
      csvPFco.WriteRowTitlesNoFilter(row)
    else:
      csvPFco.WriteRowTitles(row)

  csvPF = CSVPrintFile('Owner', indexedTitles=DRIVE_INDEXED_TITLES)
  csvPFco = None
  FJQC = FormatJSONQuoteChar(csvPF)
  addPathsToJSON = continueOnInvalidQuery = countsRowFilter = buildTree = countsOnly = filepath = fullpath = folderPathOnly = parentPathOnly = \
    getPermissionDetailsForMyDrive = getPermissionsForSharedDrives = mimeTypeInQuery = noRecursion = oneItemPerRow = stripCRsFromName = \
    showParentsIdsAsList = showDepth = showParent = showSize = showSizeUnits = showMimeTypeSize = showSource = False
  sizeField = 'quotaBytesUsed'
  pathDelimiter = '/'
  pmselect = True
  showLabels = None
  rootFolderId = ROOT
  rootFolderName = MY_DRIVE
  maxdepth = -1
  nodataFields = []
  simpleLists = ['permissionIds', 'spaces']
  permissionsFieldsList = []
  skipObjects = set()
  fileIdEntity = {}
  selectSubQuery = ''
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  DLP = DriveListParameters({'allowChoose': True, 'allowCorpora': True, 'allowQuery': True, 'mimeTypeInQuery': False})
  DFF = DriveFileFields()
  summary = FILECOUNT_SUMMARY_NONE
  summaryUser = FILECOUNT_SUMMARY_USER
  summaryMimeTypeInfo = {}
  addCSVData = {}
  includeCSVDataInJSON = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif DLP.ProcessArgument(myarg, fileIdEntity):
      pass
    elif DFF.ProcessArgument(myarg):
      pass
    elif myarg == 'select':
      if fileIdEntity:
        usageErrorExit(Msg.CAN_NOT_BE_SPECIFIED_MORE_THAN_ONCE.format('select'))
      if not DLP.fileIdEntity:
        fileIdEntity = getDriveFileEntity(DLP=DLP)
      else:
        fileIdEntity = getDriveFileEntitySharedDriveOnly()
    elif myarg == 'selectsubquery':
      selectSubQuery = getString(Cmd.OB_QUERY, minLen=0)
    elif myarg == 'norecursion':
      noRecursion = getBoolean()
    elif myarg == 'mimetypeinquery':
      mimeTypeInQuery = getBoolean()
    elif myarg == 'depth':
      maxdepth = getInteger(minVal=-1)
    elif myarg == 'showdepth':
      showDepth = True
    elif myarg == 'showparent':
      showParent = getBoolean()
    elif myarg == 'nodataheaders':
      nodataFields = getString(Cmd.OB_FIELD_NAME_LIST).replace('_', '').replace(',', ' ').split()
    elif myarg in {'filepath', 'fullpath'}:
      filepath = True
      fullpath = myarg == 'fullpath'
    elif myarg == 'folderpathonly':
      folderPathOnly = getBoolean()
    elif myarg == 'parentpathonly':
      parentPathOnly = getBoolean()
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif myarg == 'addpathstojson':
      addPathsToJSON = True
    elif myarg == 'buildtree':
      buildTree = True
    elif myarg == 'countsrowfilter':
      countsRowFilter = True
    elif myarg == 'countsonly':
      countsOnly = True
      csvPFco = CSVPrintFile(['Owner', 'Total'], 'sortall')
      csvPFco.SetZeroBlankMimeTypeCounts(True)
    elif myarg == 'summary':
      summary = getChoice(FILECOUNT_SUMMARY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'summaryuser':
      summaryUser = getString(Cmd.OB_STRING)
    elif myarg == 'showsource':
      showSource = True
    elif myarg == 'showsize':
      showSize = True
    elif myarg == 'showsizeunits':
      showSizeUnits = True
    elif myarg == 'showmimetypesize':
      showMimeTypeSize = showSize = True
    elif myarg == 'sizefield':
      sizeField = getChoice(SIZE_FIELD_CHOICE_MAP, mapChoice=True)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'showparentsidsaslist':
      showParentsIdsAsList = True
      simpleLists.append('parentsIds')
    elif myarg == 'showpermissionslast':
      csvPF.SetShowPermissionsLast(True)
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    elif myarg == 'showlabels':
      showLabels = getChoice(SHOWLABELS_CHOICES)
    elif myarg == 'showshareddrivepermissions':
      permissionsFieldsList = DRIVEFILE_BASIC_PERMISSION_FIELDS.copy()
    elif myarg == 'pmfilter':
      pmselect = False
    elif myarg == 'oneitemperrow':
      oneItemPerRow = True
      csvPF.RemoveIndexedTitles('permissions')
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = getBoolean()
    elif myarg == 'continueoninvalidquery':
      continueOnInvalidQuery = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  if countsOnly:
    titles = ['Owner', 'Total'] if not showSource else ['Owner', 'Source', 'Name', 'Total']
    if showSize:
      titles.append('Size')
    if showSizeUnits:
      titles.append('SizeUnits')
    csvPFco.SetTitles(titles)
    csvPFco.SetSortAllTitles()

  if not filepath and not fullpath:
    showDepth = False
  noSelect = noFileSelectFileIdEntity(fileIdEntity)
  if noSelect:
    buildTree = True
    if maxdepth != -1 or filepath:
      if not fileIdEntity:
        fileIdEntity = initDriveFileEntity()
        DLP.GetFileIdEntity()
      if not fileIdEntity['shareddrive']:
        cleanFileIDsList(fileIdEntity, [ROOT, ORPHANS])
      if maxdepth != -1:
        noSelect = False
    elif not fileIdEntity:
      fileIdEntity = DLP.GetFileIdEntity()
  elif not buildTree:
    buildTree = (not noRecursion
                 and not fileIdEntity['dict']
                 and not fileIdEntity['query']
                 and not fileIdEntity['shareddrivefilequery']
                 and _simpleFileIdEntityList(fileIdEntity['list']))
  incrementalPrint = buildTree and (not filepath) and noSelect and not DLP.locationSet and not showParent
  if buildTree and ((not filepath) or mimeTypeInQuery) and noSelect and not DLP.locationSet and not showParent:
    DLP.AddMimeTypeToQuery()
  if buildTree:
    if not fileIdEntity.get('shareddrive'):
      btkwargs = DLP.kwargs
    else:
      btkwargs = fileIdEntity['shareddrive']
    DLP.Finalize(fileIdEntity)
  if DLP.PM.permissionMatches:
    permissionsFieldsList += list(DLP.PM.permissionFields)
  getPermissionDetailsForMyDrive, getPermissionsForSharedDrives, permissionsFields = \
    _setGetPermissionsForMyDriveSharedDrives(DFF.fieldsList, permissionsFieldsList)
  if DFF.fieldsList:
    _setSelectionFields()
    fields = getFieldsFromFieldsList(DFF.fieldsList)
    pagesFields = getItemFieldsFromFieldsList('files', DFF.fieldsList)
  elif not DFF.allFields:
    _setSelectionFields()
    if not countsOnly and not set(DFF.fieldsList)-skipObjects:
      for field in ['name', 'webviewlink']:
        skipObjects.discard(DRIVE_FIELDS_CHOICE_MAP[field])
        csvPF.AddField(field, DRIVE_FIELDS_CHOICE_MAP, DFF.fieldsList)
    fields = getFieldsFromFieldsList(DFF.fieldsList)
    pagesFields = getItemFieldsFromFieldsList('files', DFF.fieldsList)
  else:
    fields = pagesFields = '*'
    DFF.SetAllParentsSubFields()
    skipObjects = skipObjects.union(DEFAULT_SKIP_OBJECTS)
  if stripCRsFromName:
    if (countsOnly and not showSource) or (fields != '*' and 'name' not in DFF.fieldsList):
      stripCRsFromName = False
  shareddriveFields = []
  for field in ['capabilities', 'createdTime']:
    if fields == '*' or field in DFF.fieldsList:
      shareddriveFields.append(field)
  if addCSVData:
    if not countsOnly:
      csvPF.AddTitles(sorted(addCSVData.keys()))
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
    else:
      csvPFco.AddTitles(sorted(addCSVData.keys()))
      csvPFco.MoveTitlesToEnd(['Total'])
      if showSize:
        csvPFco.MoveTitlesToEnd(['Size'])
      if showSizeUnits:
        csvPFco.MoveTitlesToEnd(['SizeUnits'])
      csvPFco.SetSortAllTitles()
  if filepath and not countsOnly:
    csvPF.AddTitles('paths')
    csvPF.SetFixPaths(True)
  includeLabels = _finalizeIncludeLabels(DFF.includeLabels)
  includePermissionsForView = _finalizeIncludePermissionsForView(DFF.includePermissionsForView)
  csvPF.RemoveTitles(['capabilities'])
  if DLP.queryTimes and selectSubQuery:
    for queryTimeName, queryTimeValue in DLP.queryTimes.items():
      selectSubQuery = selectSubQuery.replace(f'#{queryTimeName}#', queryTimeValue)
    selectSubQuery = _mapDrive2QueryToDrive3(selectSubQuery)
  if not nodataFields:
    if DFF.fieldsList:
      if not FJQC.formatJSON:
        nodataFields = ['Owner']+list(set(DFF.fieldsList)-skipObjects)
      else:
        nodataFields = ['Owner', 'id', 'name', 'owners.emailAddress']
    else:
      nodataFields = ['Owner', 'id', 'name', 'owners.emailAddress']
      if not FJQC.formatJSON:
        nodataFields.append('permissions')
    if filepath:
      nodataFields.append('paths')
    if FJQC.formatJSON:
      nodataFields.append('JSON')
    csvPF.SetNodataFields(True, nodataFields, DRIVE_LIST_FIELDS, DRIVE_SUBFIELDS_CHOICE_MAP, oneItemPerRow)
  else:
    csvPF.SetNodataFields(False, nodataFields, None, None, False)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, drive = _validateUserSharedDrive(user, i, count, fileIdEntity)
    if not drive:
      continue
    if ((incrementalPrint and countsOnly) or
        (not showParentsIdsAsList and DFF.parentsSubFields['isRoot'])):
      try:
        if not fileIdEntity['shareddrive']:
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                            fileId=ROOT, fields='id,name')
          rootFolderId = result['id']
          rootFolderName = result['name']
        else:
          rootFolderId = fileIdEntity['shareddrive']['driveId']
          if not fileIdEntity['shareddrivename']:
            fileIdEntity['shareddrivename'] = callGAPI(drive.drives(), 'get',
                                                     throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FILE_NOT_FOUND, GAPI.NOT_FOUND],
                                                     driveId=rootFolderId, fields='name')['name']
          rootFolderName = fileIdEntity['shareddrivename']
        if not showParentsIdsAsList and DFF.parentsSubFields['isRoot']:
          DFF.parentsSubFields['rootFolderId'] = rootFolderId
      except (GAPI.fileNotFound, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileIdEntity['shareddrive']['driveId']], str(e), i, count)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    if filepath:
      filePathInfo = initFilePathInfo(pathDelimiter)
    filesPrinted = set()
    mimeTypeInfo = {}
    getSharedDriveACLsCount = 0
    if buildTree:
      gettingEntity = _getGettingEntity(user, fileIdEntity)
      printGettingAllEntityItemsForWhom(Ent.DRIVE_FILE_OR_FOLDER, gettingEntity, i, count, query=DLP.fileIdEntity['query'])
      if not incrementalPrint:
        fileTree, status = initFileTree(drive, fileIdEntity.get('shareddrive'), DLP, shareddriveFields, showParent, user, i, count)
        if not status:
          continue
      try:
        feed = yieldGAPIpages(drive.files(), 'list', 'files',
                              pageMessage=getPageMessageForWhom(), maxItems=DLP.maxItems,
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.INVALID_QUERY, GAPI.INVALID,
                                                                          GAPI.BAD_REQUEST, GAPI.FILE_NOT_FOUND,
                                                                          GAPI.NOT_FOUND, GAPI.TEAMDRIVE_MEMBERSHIP_REQUIRED],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR],
                              q=DLP.fileIdEntity['query'], orderBy=DFF.orderBy,
                              includeLabels=includeLabels, includePermissionsForView=includePermissionsForView,
                              fields=pagesFields, pageSize=GC.Values[GC.DRIVE_MAX_RESULTS], **btkwargs)
        for files in feed:
          if showLabels is not None:
            for f_file in files:
              labels = callGAPIitems(drive.files(), 'listLabels', 'labels',
                                     throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                     retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR],
                                     fileId=f_file['id'])
              _formatFileDriveLabels(showLabels, labels, f_file, True, delimiter)
          if not incrementalPrint:
            extendFileTree(fileTree, files, DLP, stripCRsFromName)
          else:
            for f_file in files:
              if stripCRsFromName:
                f_file['name'] = _stripControlCharsFromName(f_file['name'])
              _printFileInfo(drive, user, f_file, False)
        if incrementalPrint:
          if countsOnly:
            if summary != FILECOUNT_SUMMARY_NONE:
              for mimeType, mtinfo in mimeTypeInfo.items():
                summaryMimeTypeInfo.setdefault(mimeType, {'count': 0, 'size': 0})
                summaryMimeTypeInfo[mimeType]['count'] += mtinfo['count']
                summaryMimeTypeInfo[mimeType]['size'] += mtinfo['size']
            if summary != FILECOUNT_SUMMARY_ONLY:
              writeMimeTypeCountsRow(user, rootFolderId, rootFolderName, mimeTypeInfo)
          continue
        extendFileTreeParents(drive, fileTree, fields)
        DLP.GetLocationFileIdsFromTree(fileTree, fileIdEntity)
      except (GAPI.invalidQuery, GAPI.invalid, GAPI.badRequest) as e:
        errMsg = str(e)
        if 'Invalid field selection' in errMsg or "Only a 'published' value is supported." in errMsg:
          entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None], errMsg, i, count)
          break
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, None], invalidQuery(DLP.fileIdEntity['query']), i, count)
        if not continueOnInvalidQuery:
          break
        continue
      except GAPI.fileNotFound:
        printGotEntityItemsForWhom(0)
        continue
      except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileIdEntity['shareddrive']['driveId']], str(e), i, count)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        continue
    else:
      fileTree = {}
    user, drive, jcount = _validateUserGetFileIDs(origUser, i, count, fileIdEntity, drive=drive)
    if jcount == 0:
      continue
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      if showSource:
        mimeTypeInfo = {}
      fileEntry = fileTree.get(fileId)
      if fileEntry:
        fileEntryInfo = fileEntry['info']
      else:
        try:
          fileEntryInfo = callGAPI(drive.files(), 'get',
                                   throwReasons=GAPI.DRIVE_GET_THROW_REASONS+[GAPI.INVALID],
                                   fileId=fileId, includeLabels=includeLabels, includePermissionsForView=includePermissionsForView,
                                   fields=fields, supportsAllDrives=True)
          if stripCRsFromName:
            fileEntryInfo['name'] = _stripControlCharsFromName(fileEntryInfo['name'])
          if showLabels is not None:
            labels = callGAPIitems(drive.files(), 'listLabels', 'labels',
                                   throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                                   retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR],
                                   fileId=fileId)
            _formatFileDriveLabels(showLabels, labels, fileEntryInfo, True, delimiter)
          if filepath:
            fileTree[fileId] = {'info': fileEntryInfo}
        except GAPI.invalid as e:
          entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, fileId], str(e), j, jcount)
          continue
        except GAPI.fileNotFound:
          entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER, fileId], Msg.NOT_FOUND, j, jcount)
          continue
        except (GAPI.notFound, GAPI.teamDriveMembershipRequired) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.SHAREDDRIVE_ID, fileIdEntity['shareddrive']['driveId']], str(e), j, jcount)
          continue
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
      if fullpath:
        getFilePaths(drive, fileTree, fileEntryInfo, filePathInfo, addParentsToTree=True,
                     fullpath=fullpath, showDepth=showDepth, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
      if ((showParent and (fileEntryInfo['id'] not in {ORPHANS, SHARED_WITHME, SHARED_DRIVES})) or
          fileEntryInfo['mimeType'] != MIMETYPE_GA_FOLDER or noRecursion):
        if fileId not in filesPrinted:
          filesPrinted.add(fileId)
          _printFileInfo(drive, user, fileEntryInfo.copy(), False)
      if fileEntryInfo['mimeType'] == MIMETYPE_GA_FOLDER and not noRecursion:
        _printChildDriveFolderContents(drive, fileEntryInfo, user, i, count, 0)
        if GC.Values[GC.SHOW_GETTINGS] and not GC.Values[GC.SHOW_GETTINGS_GOT_NL]:
          writeStderr('\r\n')
          flushStderr()
      if countsOnly:
        if showSource:
          if summary != FILECOUNT_SUMMARY_NONE:
            for mimeType, mtinfo in mimeTypeInfo.items():
              summaryMimeTypeInfo.setdefault(mimeType, {'count': 0, 'size': 0})
              summaryMimeTypeInfo[mimeType]['count'] += mtinfo['count']
              summaryMimeTypeInfo[mimeType]['size'] += mtinfo['size']
          if summary != FILECOUNT_SUMMARY_ONLY:
            writeMimeTypeCountsRow(user, fileId, fileEntryInfo['name'], mimeTypeInfo)
    if countsOnly:
      if not showSource:
        if summary != FILECOUNT_SUMMARY_NONE:
          for mimeType, mtinfo in mimeTypeInfo.items():
            summaryMimeTypeInfo.setdefault(mimeType, {'count': 0, 'size': 0})
            summaryMimeTypeInfo[mimeType]['count'] += mtinfo['count']
            summaryMimeTypeInfo[mimeType]['size'] += mtinfo['size']
        if summary != FILECOUNT_SUMMARY_ONLY:
          writeMimeTypeCountsRow(user, 'Various', 'Various', mimeTypeInfo)
  titlePrefix = f'{Cmd.Argument(GM.Globals[GM.ENTITY_CL_START])} {Cmd.Argument(GM.Globals[GM.ENTITY_CL_START]+1)} ' if GM.Globals[GM.CSVFILE][GM.REDIRECT_QUEUE] is None else ''
  if not countsOnly:
    if not csvPF.rows:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    sortTitles = ['Owner']
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(['id', 'name'])
    csvPF.SetSortTitles(sortTitles)
    if FJQC.formatJSON:
      if 'JSON' in csvPF.JSONtitlesList:
        csvPF.MoveJSONTitlesToEnd(['JSON'])
    csvPF.writeCSVfile(f'{titlePrefix}Drive Files')
  else:
    if not csvPFco.rows:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    if summary != FILECOUNT_SUMMARY_NONE:
      writeMimeTypeCountsRow(summaryUser, 'Various', 'Various', summaryMimeTypeInfo)
    csvPFco.todrive = csvPF.todrive
    csvPFco.writeCSVfile(f'{titlePrefix}Drive File Counts', not countsRowFilter)

FILECOMMENTS_FIELDS_CHOICE_MAP = {
  'action': 'action',
  'author': 'author',
  'content': 'content',
  'createddate': 'createdTime',
  'createdtime': 'createdTime',
  'deleted': 'deleted',
  'htmlcontent': 'htmlContent',
  'id': 'id',
  'modifieddate': 'modifiedTime',
  'modifiedtime': 'modifiedTime',
  'quotedfilecontent': 'quotedFileContent',
  'reply': 'replies',
  'replies': 'replies',
  'resolved': 'resolved',
  }

FILECOMMENTS_AUTHOR_SUBFIELDS_CHOICE_MAP = {
  'displayname': 'displayName',
  'emailaddress': 'emailAddress',
  'me': 'me',
  'permissionid': 'permissionId',
  'photolink': 'photoLink',
  }

FILECOMMENTS_REPLIES_SUBFIELDS_CHOICE_MAP = {
  'action': 'action',
  'author': 'author',
  'content': 'content',
  'createddate': 'createdTime',
  'createdtime': 'createdTime',
  'deleted': 'deleted',
  'htmlcontent': 'htmlContent',
  'id': 'id',
  'modifieddate': 'modifiedTime',
  'modifiedtime': 'modifiedTime',
  }

FILECOMMENTS_SUBFIELDS_CHOICE_MAP = {
  'author': FILECOMMENTS_AUTHOR_SUBFIELDS_CHOICE_MAP,
  'reply': FILECOMMENTS_REPLIES_SUBFIELDS_CHOICE_MAP,
  'replies': FILECOMMENTS_REPLIES_SUBFIELDS_CHOICE_MAP,
  }

def _getCommentFields(fieldsList):
  for field in _getFieldsList():
    if field.find('.') == -1:
      if field in FILECOMMENTS_FIELDS_CHOICE_MAP:
        addFieldToFieldsList(field, FILECOMMENTS_FIELDS_CHOICE_MAP, fieldsList)
      else:
        invalidChoiceExit(field, FILECOMMENTS_FIELDS_CHOICE_MAP, True)
    else:
      field, subField = field.split('.', 1)
      if field in FILECOMMENTS_SUBFIELDS_CHOICE_MAP:
        if subField.find('.') == -1:
          if subField in FILECOMMENTS_SUBFIELDS_CHOICE_MAP[field]:
            fieldsList.append(f'{FILECOMMENTS_FIELDS_CHOICE_MAP[field]}.{FILECOMMENTS_SUBFIELDS_CHOICE_MAP[field][subField]}')
          else:
            invalidChoiceExit(subField, FILECOMMENTS_SUBFIELDS_CHOICE_MAP[field], True)
        else:
          subField, subSubField = subField.split('.', 1)
          if subField in FILECOMMENTS_SUBFIELDS_CHOICE_MAP[field]:
            if subSubField in FILECOMMENTS_SUBFIELDS_CHOICE_MAP[subField]:
              fieldsList.append(f'{FILECOMMENTS_FIELDS_CHOICE_MAP[field]}.{FILECOMMENTS_SUBFIELDS_CHOICE_MAP[field][subField]}.{FILECOMMENTS_SUBFIELDS_CHOICE_MAP[subField][subSubField]}')
            else:
              invalidChoiceExit(subSubField, FILECOMMENTS_SUBFIELDS_CHOICE_MAP[subField], True)
          else:
            invalidChoiceExit(subField, FILECOMMENTS_SUBFIELDS_CHOICE_MAP[field], True)
      else:
        invalidChoiceExit(field, FILECOMMENTS_SUBFIELDS_CHOICE_MAP, True)

FILECOMMENTS_INDEXED_TITLES = ['replies']
FILECOMMENTS_TIME_OBJECTS = {'createdTime', 'modifiedTime'}

def _stripCommentPhotoLinks(comment):
  if 'author' in comment:
    comment['author'].pop('photoLink', None)
  for reply in comment.get('replies', []):
    if 'author' in reply:
      reply['author'].pop('photoLink', None)

def _showComment(comment, stripPhotoLinks, timeObjects, i=0, count=0, FJQC=None):
  if stripPhotoLinks:
    _stripCommentPhotoLinks(comment)
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(comment, timeObjects=FILECOMMENTS_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.DRIVE_FILE_COMMENT, comment['id']], i, count)
  Ind.Increment()
  showJSON(None, comment, ['id'], timeObjects)
  Ind.Decrement()

# gam <UserTypeEntity> show filecomments <DriveFileEntity>
#	[showdeleted] [start <Date>|<Time>] [countsonly|positivecountsonly]
#	[fields <CommentsFieldNameList>] [showphotolinks]
#	[countsonly]
#	[formatjson]
# gam <UserTypeEntity> print filecomments <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	[showdeleted] [start <Date>|<Time>]
#	[fields <CommentsFieldNameList>] [showphotolinks]
#	[countsonly|positivecountsonly]
#	(addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
def printShowFileComments(users):
  def _printComment(comment, commentId, replyId, baserow):
    row = flattenJSON(comment, flattened=baserow.copy(), timeObjects=timeObjects)
    row['commentId'] = commentId
    row['replyId'] = replyId
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      row = baserow.copy()
      row['commentId'] = commentId
      comment['id'] = commentId
      row['replyId'] = replyId
      if replyId:
        comment['reply']['id'] = replyId
      row['JSON'] = json.dumps(cleanJSON(comment, timeObjects=timeObjects),
                               ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  csvPF = CSVPrintFile(['User', 'fileId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  fileIdEntity = getDriveFileEntity()
  countsOnly = positiveCountsOnly = False
  stripPhotoLinks = True
  kwargs = {}
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showdeleted':
      kwargs['includeDeleted'] = True
    elif myarg == 'start':
      kwargs['startModifiedTime'] = getTimeOrDeltaFromNow()
    elif myarg == 'showphotolinks':
      stripPhotoLinks = False
    elif myarg == 'fields':
      _getCommentFields(fieldsList)
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'countsonly':
      countsOnly = True
    elif myarg == 'positivecountsonly':
      countsOnly = positiveCountsOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  if csvPF:
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    if not countsOnly:
      csvPF.AddTitles(['commentId', 'replyId'])
    else:
      csvPF.AddTitles(['comments', 'replies'])
    if FJQC.formatJSON:
      csvPF.AddTitles(['JSON'])
      csvPF.SetJSONTitles(csvPF.titlesList)
  if fieldsList:
    if 'id' not in fieldsList:
      fieldsList.append('id')
    if 'replies' not in fieldsList:
      for field in fieldsList.copy():
        if field.startswith('replies.'):
          fieldsList.append('replies.id')
          break
    fields = getItemFieldsFromFieldsList('comments', fieldsList)
  else:
    fields = '*'
  timeObjects = FILECOMMENTS_TIME_OBJECTS
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=[Ent.DRIVE_FILE_COMMENT, None][csvPF is not None])
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        comments = callGAPIpages(drive.comments(), 'list', 'comments',
                                 throwReasons=GAPI.DRIVE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST],
                                 fileId=fileId, fields=fields, **kwargs)
      except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
              GAPI.badRequest) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_ID, fileId], str(e), j, jcount)
        continue
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
      kcount = len(comments)
      if countsOnly:
        numReplies = 0
        for comment in comments:
          numReplies += len(comment['replies'])
      if not csvPF:
        if countsOnly:
          if not positiveCountsOnly or kcount > 0:
            printKeyValueList([Ent.Singular(Ent.DRIVE_FILE_ID), fileId, 'comments', kcount, 'replies', numReplies])
        else:
          if not FJQC.formatJSON:
            entityPerformActionNumItems([Ent.DRIVE_FILE_ID, fileId], kcount, Ent.DRIVE_FILE_COMMENT, j, jcount)
          Ind.Increment()
          if not countsOnly:
            k = 0
            for comment in comments:
              k += 1
              _showComment(comment, stripPhotoLinks, timeObjects, k, kcount, FJQC)
        Ind.Decrement()
      elif countsOnly:
        if not positiveCountsOnly or kcount > 0:
          row = {'User': user, 'fileId': fileId}
          if addCSVData:
            row.update(addCSVData)
          row['comments'] = kcount
          row['replies'] = numReplies
          csvPF.WriteRowTitles(row)
      elif comments:
        baserow = {'User': user, 'fileId': fileId}
        if addCSVData:
          baserow.update(addCSVData)
        for comment in comments:
          if stripPhotoLinks:
            _stripCommentPhotoLinks(comment)
          commentId = comment.pop('id')
          replies = comment.pop('replies')
          if not replies:
            _printComment(comment, commentId, '', baserow)
          else:
            for reply in replies:
              replyId = reply.pop('id')
              baserow['replyId'] = replyId
              comment['reply'] = reply
              _printComment(comment, commentId, replyId, baserow)
    Ind.Decrement()
  if csvPF:
    csvPF.SetIndexedTitles(FILECOMMENTS_INDEXED_TITLES)
    csvPF.writeCSVfile('Drive File Comments')

# gam <UserTypeEntity> print filepaths <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[stripcrsfromname] [oneitemperrow]
#	[fullpath] [folderpathonly|parentpathonly [<Boolean>]] [pathdelimiter <Character>]
#	[followshortcuts [<Boolean>]]
# gam <UserTypeEntity> show filepaths <DriveFileEntity>
#	[returnpathonly]
#	(orderby <DriveFileOrderByFieldName> [ascending|descending])*
#	[stripcrsfromname]
#	[fullpath] [folderpathonly|parentpathonly [<Boolean>]] [pathdelimiter <Character>]
#	[followshortcuts [<Boolean>]]
def printShowFilePaths(users):
  csvPF = CSVPrintFile(['Owner', 'id', 'name', 'paths'], 'sortall', ['paths']) if Act.csvFormat() else None
  fileIdEntity = getDriveFileEntity()
  fullpath = folderPathOnly = parentPathOnly = followShortcuts = oneItemPerRow = returnPathOnly = stripCRsFromName = False
  pathDelimiter = '/'
  OBY = OrderBy(DRIVEFILE_ORDERBY_CHOICE_MAP)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'fullpath':
      fullpath = True
    elif myarg == 'folderpathonly':
      folderPathOnly = getBoolean()
    elif myarg == 'parentpathonly':
      parentPathOnly = getBoolean()
    elif myarg == 'pathdelimiter':
      pathDelimiter = getCharacter()
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    elif csvPF is None and myarg == 'returnpathonly':
      returnPathOnly = True
    elif myarg == 'followshortcuts':
      followShortcuts = getBoolean()
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
      csvPF.RemoveTitles('paths')
      csvPF.AddTitles('path')
      csvPF.SetSortAllTitles()
      csvPF.SetIndexedTitles([])
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      unknownArgumentExit()
  fieldsList = FILEPATH_FIELDS_TITLES
  if followShortcuts:
    fieldsList.append('shortcutDetails')
  pathFields = ','.join(fieldsList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if returnPathOnly:
      GC.Values[GC.SHOW_GETTINGS] = False
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity,
                                                  entityType=[Ent.DRIVE_FILE_OR_FOLDER, None][(csvPF is not None) or returnPathOnly],
                                                  orderBy=OBY.orderBy)
    if jcount == 0:
      continue
    filePathInfo = initFilePathInfo(pathDelimiter)
    if fullpath:
      fileTree, status = initFileTree(drive, fileIdEntity.get('shareddrive'), None, [], True, user, i, count)
      if not status:
        continue
    else:
      fileTree =  None
    Ind.Increment()
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      try:
        result = callGAPI(drive.files(), 'get',
                          throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                          fileId=fileId, fields=pathFields, supportsAllDrives=True)
        if followShortcuts and result['mimeType'] == MIMETYPE_GA_SHORTCUT:
          fileId = result['shortcutDetails']['targetId']
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId, fields=pathFields, supportsAllDrives=True)
        if returnPathOnly and result['mimeType'] == MIMETYPE_GA_FOLDER and result['name'] == MY_DRIVE and not result.get('parents'):
          writeStdout(f'{MY_DRIVE}\n')
          continue
        if stripCRsFromName:
          result['name'] = _stripControlCharsFromName(result['name'])
        driveId = result.get('driveId')
        if driveId:
          if result['mimeType'] == MIMETYPE_GA_FOLDER and result['name'] == TEAM_DRIVE:
            result['name'] = _getSharedDriveNameFromId(drive, driveId)
            if returnPathOnly:
              if fullpath:
                writeStdout(f'{SHARED_DRIVES}/{result["name"]}\n')
              else:
                writeStdout(f'{result["name"]}\n')
              continue
        if fullpath:
          extendFileTree(fileTree, [result], None, False)
          extendFileTreeParents(drive, fileTree, pathFields)
        entityType, paths, _ = getFilePaths(drive, fileTree, result, filePathInfo, addParentsToTree=True,
                                            fullpath=fullpath, folderPathOnly=folderPathOnly, parentPathOnly=parentPathOnly)
        if returnPathOnly:
          for path in paths:
            writeStdout(f'{path}\n')
        elif not csvPF:
          kcount = len(paths)
          entityPerformActionNumItems([entityType, f'{result["name"]} ({fileId})'], kcount, Ent.DRIVE_PATH, j, jcount)
          Ind.Increment()
          k = 0
          for path in paths:
            k += 1
            printEntity([Ent.DRIVE_PATH, path], k, kcount)
          Ind.Decrement()
        else:
          if oneItemPerRow:
            if paths:
              for path in paths:
                csvPF.WriteRow({'Owner': user, 'id': fileId, 'name': result['name'], 'path': path})
            else:
              csvPF.WriteRow({'Owner': user, 'id': fileId, 'name': result['name']})
          else:
            csvPF.WriteRowTitles(flattenJSON({'paths': paths}, flattened={'Owner': user, 'id': fileId, 'name': result['name']}))
      except GAPI.fileNotFound:
        entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], Msg.DOES_NOT_EXIST, j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Drive File Paths')

# gam <UserTypeEntity> print fileparenttree <DriveFileEntity> [todrive <ToDriveAttribute>*]
#	[stripcrsfromname]
def printFileParentTree(users):
  csvPF = CSVPrintFile(['Owner', 'isBase', 'baseId', 'id', 'name', 'parentId', 'depth', 'isRoot'], 'sortall')
  fileIdEntity = getDriveFileEntity()
  stripCRsFromName = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'stripcrsfromname':
      stripCRsFromName = True
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=Ent.FILE_PARENT_TREE)
    if jcount == 0:
      continue
    try:
      rootId = callGAPI(drive.files(), 'get',
                              throwReasons=GAPI.DRIVE_USER_THROW_REASONS,
                              fileId=ROOT, fields='id')['id']
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
      continue
    j = 0
    for fileId in fileIdEntity['list']:
      j += 1
      fileList = []
      baseId = fileId
      while True:
        try:
          result = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId, fields='id,name,mimeType,parents,driveId', supportsAllDrives=True)
          if stripCRsFromName:
            result['name'] = _stripControlCharsFromName(result['name'])
          result['isRoot'] = False
          if not result.get('parents', []):
            if fileId == rootId:
              result['isRoot'] = True
            else:
              driveId = result.get('driveId')
              if driveId:
                if result['mimeType'] == MIMETYPE_GA_FOLDER and result['name'] == TEAM_DRIVE:
                  result['name'] = _getSharedDriveNameFromId(drive, driveId)
                  result['isRoot'] = True
            result['parents'] = ['']
            fileList.append(result)
            break
          fileList.append(result)
          fileId = result['parents'][0]
        except GAPI.fileNotFound:
          entityActionFailedWarning([Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId], Msg.DOES_NOT_EXIST, j, jcount)
          break
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          userDriveServiceNotEnabledWarning(user, str(e), i, count)
          break
      kcount = len(fileList)
      isBase = True
      for result in fileList:
        csvPF.WriteRow({'Owner': user, 'isBase': isBase, 'baseId': baseId, 'id': result['id'], 'name': result['name'],
                        'parentId': result['parents'][0], 'depth': kcount, 'isRoot': result['isRoot']})
        isBase = False
        kcount -= 1
  csvPF.writeCSVfile('Drive File Parent Tree')

# Last file modification utilities
def _initLastModification():
  return {'lastModifiedFileId': '', 'lastModifiedFileName': '',
          'lastModifiedFileMimeType': '', 'lastModifiedFilePath': '',
          'lastModifyingUser': '', 'lastModifiedTime': NEVER_TIME,
          'fileEntryInfo': {}}

def _checkUpdateLastModifiction(f_file, userLastModification):
  if f_file.get('modifiedTime', NEVER_TIME) > userLastModification['lastModifiedTime'] and 'lastModifyingUser' in f_file:
    userLastModification['lastModifiedFileId'] = f_file['id']
    userLastModification['lastModifiedFileName'] = _stripControlCharsFromName(f_file['name'])
    userLastModification['lastModifiedFileMimeType'] = f_file['mimeType']
    userLastModification['lastModifiedTime'] = f_file['modifiedTime']
    userLastModification['lastModifyingUser'] = f_file['lastModifyingUser'].get('emailAddress',
                                                                                f_file['lastModifyingUser'].get('displayName', UNKNOWN))
    userLastModification['fileEntryInfo'] = f_file.copy()

def _getLastModificationPath(drive, userLastModification, pathDelimiter):
  if userLastModification['fileEntryInfo']:
    filePathInfo = initFilePathInfo(pathDelimiter)
    _, paths, _ = getFilePaths(drive, {}, userLastModification['fileEntryInfo'], filePathInfo)
    userLastModification['lastModifiedFilePath'] = paths[0] if paths else UNKNOWN

def _showLastModification(lastModification):
  printKeyValueList(['lastModifiedFileId', lastModification['lastModifiedFileId']])
  printKeyValueList(['lastModifiedFileName', lastModification['lastModifiedFileName']])
  printKeyValueList(['lastModifiedFileMimeType', lastModification['lastModifiedFileMimeType']])
  printKeyValueList(['lastModifiedFilePath', lastModification['lastModifiedFilePath']])
  printKeyValueList(['lastModifyingUser', lastModification['lastModifyingUser']])
  printKeyValueList(['lastModifiedTime', formatLocalTime(lastModification['lastModifiedTime'])])

def _updateLastModificationRow(row, lastModification):
  row.update({'lastModifiedFileId': lastModification['lastModifiedFileId'],
              'lastModifiedFileName': lastModification['lastModifiedFileName'],
              'lastModifiedFileMimeType': lastModification['lastModifiedFileMimeType'],
              'lastModifiedFilePath': lastModification['lastModifiedFilePath'],
              'lastModifyingUser': lastModification['lastModifyingUser'],
              'lastModifiedTime': formatLocalTime(lastModification['lastModifiedTime'])})

# gam <UserTypeEntity> print filecounts [todrive <ToDriveAttribute>*]
#	[((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>) (querytime<String> <Time>)*]
#	[continueoninvalidquery [<Boolean>]]
#	[corpora <CorporaAttribute>]
#	[select <SharedDriveEntity>]
#	[anyowner|(showownedby any|me|others)]
#	[showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
#	[sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
#	[filenamematchpattern <REMatchPattern>]
#	<PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
#	[excludetrashed] (addcsvdata <FieldName> <String>)*
#	[showsize] [showsizeunits] [showmimetypesize]
#	[showlastmodification] [pathdelimiter <Character>]
#	(addcsvdata <FieldName> <String>)*
#	[summary none|only|plus] [summaryuser <String>]
# gam <UserTypeEntity> show filecounts
#	[((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>) (querytime<String> <Time>)*]
#	[continueoninvalidquery [<Boolean>]]
#	[corpora <CorporaAttribute>]
#	[select <SharedDriveEntity>]
#	[anyowner|(showownedby any|me|others)]
#	[showmimetype [not] <MimeTypeList>] [showmimetype category <MimeTypeNameList>]
#	[sizefield quotabytesused|size] [minimumfilesize <Integer>] [maximumfilesize <Integer>]
#	[filenamematchpattern <REMatchPattern>]
#	<PermissionMatch>* [<PermissionMatchMode>] [<PermissionMatchAction>]
#	[excludetrashed]
#	[showsize] [showsizeunits] [showmimetypesize]
#	[showlastmodification] [pathdelimiter <Character>]
#	[summary none|only|plus] [summaryuser <String>]
