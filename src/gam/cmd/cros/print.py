"""GAM ChromeOS device management."""

import json


from gam.util.batch import batchRequestID, executeBatch, RI_J, RI_JCOUNT, RI_ITEM
import os
import time

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import _finalizeGAPIpagesResult, _processGAPIpagesResult
from gam.util.api_call import callGAPI, callGAPIitems, callGAPIpages, checkGAPIError
from gam.util.output import ISOformatTimeStamp
from gam.util.args import (
    SORTORDER_CHOICE_MAP,
    StartEndTime,
    YYYYMMDDTHHMMSS_FORMAT_REQUIRED,
    _getFilterDateTime,
    escapeCRsNLs,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getHTTPError,
    getInteger,
    getOrderBySortOrder,
    getString,
    getTimeOrDeltaFromNow,
    makeOrgUnitPathAbsolute,
    makeOrgUnitPathRelative,
    substituteQueryTimes
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
    writeEntityNoHeaderCSVFile,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    getPageMessage,
    getPageMessageForWhom,
    invalidQuery,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printGotAccountEntities,
    printKeyValueList,
    printKeyValueWithCRsNLs,
    printLine
)
from gam.util.entity import (
    _getCustomersCustomerIdWithC,
    convertEntityToList,
    getDeviceQueries,
    getEntityArgument,
    getEntitySelection,
    getEntitySelector,
    getEntityToModify
)
from gam.util.errors import (
    invalidArgumentExit,
    invalidChoiceExit,
    unknownArgumentExit,
    usageErrorExit
)
from gam.util.fileio import setFilePath, writeFile
from gam.util.orgunits import getOrgUnitId, getOrgUnitItem
from gam.util.output import (
    formatLocalDatestamp,
    formatLocalTime,
    writeStderr,
    writeStdout
)
from gam.constants import PROJECTION_CHOICE_MAP


UNKNOWN = 'Unknown'
WARNING_PREFIX = 'WARNING: '

def infoCrOSDevices(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  downloadfile = None
  targetFolder = GC.Values[GC.DRIVE_DIR]
  projection = None
  fieldsList = []
  reverseLists = []
  noLists = showDVRstorageFreePercentage = False
  FJQC = FormatJSONQuoteChar()
  listLimit = 0
  startDate = endDate = startTime = endTime = None
  activeTimeRangesOrder = 'ASCENDING'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'nolists':
      noLists = True
    elif myarg == 'listlimit':
      listLimit = getInteger(minVal=0)
    elif myarg in CROS_START_ARGUMENTS:
      startDate, startTime = _getFilterDateTime()
    elif myarg in CROS_END_ARGUMENTS:
      endDate, endTime = _getFilterDateTime()
    elif myarg == 'timerangeorder':
      activeTimeRangesOrder = getChoice(SORTORDER_CHOICE_MAP, mapChoice=True)
    elif myarg == 'allfields':
      projection = 'FULL'
      fieldsList = []
    elif myarg in PROJECTION_CHOICE_MAP:
      projection = PROJECTION_CHOICE_MAP[myarg]
      if projection == 'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
    elif myarg in CROS_FIELDS_CHOICE_MAP:
      addFieldToFieldsList(myarg, CROS_FIELDS_CHOICE_MAP, fieldsList)
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in CROS_FIELDS_CHOICE_MAP:
          addFieldToFieldsList(field, CROS_FIELDS_CHOICE_MAP, fieldsList)
          if field in CROS_LIST_FIELDS_CHOICE_MAP:
            projection = 'FULL'
            noLists = False
        else:
          invalidChoiceExit(field, CROS_FIELDS_CHOICE_MAP, True)
    elif myarg == 'reverselists':
      for field in _getFieldsList():
        if field in CROS_LIST_FIELDS_CHOICE_MAP:
          reverseLists.append(CROS_LIST_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, CROS_LIST_FIELDS_CHOICE_MAP, True)
    elif myarg == 'downloadfile':
      downloadfile = getString(Cmd.OB_STRING).lower()
      if downloadfile != 'latest':
        Cmd.Backup()
        downloadfile = formatLocalTime(getTimeOrDeltaFromNow())
    elif myarg == 'targetfolder':
      targetFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    elif myarg == 'showdvrsfp':
      showDVRstorageFreePercentage = True
    else:
      FJQC.GetFormatJSON(myarg)
  if fieldsList:
    fieldsList.append('deviceId')
    if downloadfile:
      fieldsList.append('deviceFiles.downloadUrl')
  fields = getFieldsFromFieldsList(fieldsList)
  i, count, entityList = getEntityArgument(entityList)
  for deviceId in entityList:
    i += 1
    try:
      cros = callGAPI(cd.chromeosdevices(), 'get',
                      throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=GC.Values[GC.CUSTOMER_ID], deviceId=deviceId, projection=projection, fields=fields)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.permissionDenied):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.CROS_DEVICE, deviceId, i, count)
      continue
    checkTPMVulnerability(cros)
    if 'autoUpdateExpiration' in cros:
      cros['autoUpdateExpiration'] = formatLocalDatestamp(cros['autoUpdateExpiration'])
    if showDVRstorageFreePercentage:
      _computeDVRstorageFreePercentage(cros)
    for field in reverseLists:
      if field in cros:
        cros[field].reverse()
    if 'orgUnitId' in cros:
      cros['orgUnitId'] = f"id:{cros['orgUnitId']}"
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(cros, timeObjects=CROS_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
      continue
    printEntity([Ent.CROS_DEVICE, deviceId], i, count)
    Ind.Increment()
    for up in CROS_SCALAR_PROPERTY_PRINT_ORDER:
      if up in cros:
        if up not in CROS_TIME_OBJECTS:
          if up not in CROS_FIELDS_WITH_CRS_NLS:
            printKeyValueList([up, cros[up]])
          else:
            printKeyValueWithCRsNLs(up, cros[up])
        else:
          printKeyValueList([up, formatLocalTime(cros[up])])
    for up in ['diskSpaceUsage', 'osUpdateStatus', 'tpmVersionInfo']:
      if up in cros:
        printKeyValueList([up, ''])
        Ind.Increment()
        for key, value in sorted(cros[up].items()):
          if key not in CROS_TIME_OBJECTS:
            printKeyValueList([key, value])
          else:
            printKeyValueList([key, formatLocalTime(value)])
        Ind.Decrement()
    if not noLists:
      activeTimeRanges = _filterActiveTimeRanges(cros, True, listLimit, startDate, endDate, activeTimeRangesOrder)
      if activeTimeRanges:
        printKeyValueList(['activeTimeRanges'])
        Ind.Increment()
        for activeTimeRange in activeTimeRanges:
          printKeyValueList(['date', activeTimeRange['date']])
          Ind.Increment()
          for key in ['activeTime', 'duration', 'minutes']:
            printKeyValueList([key, activeTimeRange[key]])
          Ind.Decrement()
        Ind.Decrement()
      recentUsers = _filterRecentUsers(cros, True, listLimit)
      if recentUsers:
        printKeyValueList(['recentUsers'])
        Ind.Increment()
        for recentUser in recentUsers:
          printKeyValueList(['type', recentUser['type']])
          Ind.Increment()
          printKeyValueList(['email', recentUser['email']])
          Ind.Decrement()
        Ind.Decrement()
      deviceFiles = _filterDeviceFiles(cros, True, listLimit, startTime, endTime)
      if deviceFiles:
        printKeyValueList(['deviceFiles'])
        Ind.Increment()
        for deviceFile in deviceFiles:
          printKeyValueList([deviceFile['type'], deviceFile['createTime']])
        Ind.Decrement()
        if downloadfile:
          if downloadfile == 'latest':
            deviceFile = deviceFiles[-1]
          else:
            for deviceFile in deviceFiles:
              if deviceFile['createTime'] == downloadfile:
                break
            else:
              deviceFile = None
          if deviceFile:
            downloadfilename = os.path.join(targetFolder, f'cros-logs-{deviceId}-{deviceFile["createTime"]}.zip')
            _, content = cd._http.request(deviceFile['downloadUrl'])
            writeFile(downloadfilename, content, mode='wb', continueOnError=True)
            printKeyValueList(['Downloaded', downloadfilename])
          else:
            Act.Set(Act.DOWNLOAD)
            entityActionFailedWarning([Ent.CROS_DEVICE, deviceId, Ent.DEVICE_FILE, downloadfile],
                                      Msg.DOES_NOT_EXIST, i, count)
            Act.Set(Act.INFO)
      elif downloadfile:
        Act.Set(Act.DOWNLOAD)
        entityActionNotPerformedWarning([Ent.CROS_DEVICE, deviceId, Ent.DEVICE_FILE, downloadfile],
                                        Msg.NO_ENTITIES_FOUND.format(Ent.Plural(Ent.DEVICE_FILE)), i, count)
        Act.Set(Act.INFO)
      cpuInfo = _filterBasicList(cros, 'cpuInfo', True, listLimit)
      if cpuInfo:
        showJSON('cpuInfo', cpuInfo, dictObjectsKey={'cpuInfo': 'model'})
      cpuStatusReports = _filterCPUStatusReports(cros, True, listLimit, startTime, endTime)
      if cpuStatusReports:
        printKeyValueList(['cpuStatusReports'])
        Ind.Increment()
        for cpuStatusReport in cpuStatusReports:
          printKeyValueList(['reportTime', formatLocalTime(cpuStatusReport['reportTime'])])
          Ind.Increment()
          if 'cpuTemperatureInfo' in cpuStatusReport:
            printKeyValueList(['cpuTemperatureInfo'])
            Ind.Increment()
            for tempInfo in cpuStatusReport.get('cpuTemperatureInfo', []):
              printKeyValueList([tempInfo['label'], tempInfo['temperature']])
            Ind.Decrement()
          if 'cpuUtilizationPercentageInfo' in cpuStatusReport:
            printKeyValueList(['cpuUtilizationPercentageInfo', cpuStatusReport['cpuUtilizationPercentageInfo']])
          Ind.Decrement()
        Ind.Decrement()
      backlightInfo = _filterBasicList(cros, 'backLightInfo', True, listLimit)
      if backlightInfo:
        showJSON('backlightInfo', backlightInfo, dictObjectsKey={'backlightInfo': 'path'})
      bluetoothAdapterInfo = _filterBasicList(cros, 'bluetoothAdapterInfo', True, listLimit)
      if bluetoothAdapterInfo:
        showJSON('bluetoothAdapterInfo', bluetoothAdapterInfo, dictObjectsKey={'bluetoothAdapterInfo': 'address'})
      fanInfo = _filterBasicList(cros, 'fanInfo', True, listLimit)
      if fanInfo:
        showJSON('fanInfo', fanInfo)
      diskVolumeReports = _filterBasicList(cros, 'diskVolumeReports', True, listLimit)
      if diskVolumeReports:
        printKeyValueList(['diskVolumeReports'])
        Ind.Increment()
        printKeyValueList(['volumeInfo'])
        for diskVolumeReport in diskVolumeReports:
          volumeInfo = diskVolumeReport['volumeInfo']
          Ind.Increment()
          for volume in volumeInfo:
            printKeyValueList(['volumeId', volume['volumeId']])
            Ind.Increment()
            printKeyValueList(['storageFree', volume['storageFree']])
            printKeyValueList(['storageTotal', volume['storageTotal']])
            if showDVRstorageFreePercentage:
              printKeyValueList(['storageFreePercentage', volume['storageFreePercentage']])
            Ind.Decrement()
          Ind.Decrement()
        Ind.Decrement()
      lastKnownNetworks = _filterBasicList(cros, 'lastKnownNetwork', True, listLimit)
      if lastKnownNetworks:
        printKeyValueList(['lastKnownNetwork'])
        Ind.Increment()
        for lastKnownNetwork in lastKnownNetworks:
          printKeyValueList(['ipAddress', lastKnownNetwork['ipAddress']])
          Ind.Increment()
          printKeyValueList(['wanIpAddress', lastKnownNetwork['wanIpAddress']])
          Ind.Decrement()
        Ind.Decrement()
      screenshotFiles = _filterScreenshotFiles(cros, True, listLimit, startTime, endTime)
      if screenshotFiles:
        printKeyValueList(['screenshotFiles'])
        Ind.Increment()
        for screenshotFile in screenshotFiles:
          printKeyValueList(['name', screenshotFile['name']])
          Ind.Increment()
          printKeyValueList(['type', screenshotFile['type']])
          printKeyValueList(['downloadUrl', screenshotFile['downloadUrl']])
          printKeyValueList(['createTime', screenshotFile['createTime']])
          Ind.Decrement()
        Ind.Decrement()
      systemRamFreeReports = _filterSystemRamFreeReports(cros, True, listLimit, startTime, endTime)
      if systemRamFreeReports:
        printKeyValueList(['systemRamFreeReports'])
        Ind.Increment()
        for systemRamFreeReport in systemRamFreeReports:
          printKeyValueList(['reportTime', systemRamFreeReport['reportTime']])
          Ind.Increment()
          printKeyValueList(['systemRamFreeInfo', systemRamFreeReport['systemRamFreeInfo']])
          Ind.Decrement()
        Ind.Decrement()
    Ind.Decrement()

def doInfoCrOSDevices():
  """Print detailed information about specific Chrome OS devices."""
  infoCrOSDevices(getCrOSDeviceEntity())

def getDeviceFilesEntity():
  deviceFilesEntity = {'list': [], 'dict': None, 'count': None, 'time': None, 'range': None}
  startEndTime = StartEndTime()
  entitySelector = getEntitySelector()
  if entitySelector:
    entityList = getEntitySelection(entitySelector, False)
    if isinstance(entityList, dict):
      deviceFilesEntity['dict'] = entityList
    else:
      deviceFilesEntity['list'] = entityList
  else:
    myarg = getString(Cmd.OB_DEVICE_FILE_ENTITY, checkBlank=True)
    mycmd = myarg.lower()
    if mycmd in {'first', 'last', 'allexceptfirst', 'allexceptlast'}:
      deviceFilesEntity['count'] = (mycmd, getInteger(minVal=1))
    elif mycmd in {'before', 'after'}:
      dateTime, _, _ = getTimeOrDeltaFromNow(True)
      deviceFilesEntity['time'] = (mycmd, dateTime)
    elif mycmd == 'range':
      startEndTime.Get(mycmd)
      deviceFilesEntity['range'] = (mycmd, startEndTime.startDateTime, startEndTime.endDateTime)
    else:
      for timeItem in myarg.split(','):
        try:
          timestamp = arrow.get(timeItem)
          deviceFilesEntity['list'].append(ISOformatTimeStamp(timestamp.astimezone(GC.Values[GC.TIMEZONE])))
        except (arrow.parser.ParserError, OverflowError):
          Cmd.Backup()
          invalidArgumentExit(YYYYMMDDTHHMMSS_FORMAT_REQUIRED)
  return deviceFilesEntity

def _selectDeviceFiles(deviceId, deviceFiles, deviceFilesEntity):
  numDeviceFiles = len(deviceFiles)
  if numDeviceFiles == 0:
    return deviceFiles
  for deviceFile in deviceFiles:
    deviceFile['createTime'] = formatLocalTime(deviceFile['createTime'])
  if deviceFilesEntity['count']:
    countType = deviceFilesEntity['count'][0]
    count = deviceFilesEntity['count'][1]
    if countType == 'first':
      return deviceFiles[:count]
    if countType == 'last':
      return deviceFiles[-count:]
    if countType == 'allexceptfirst':
      return deviceFiles[count:]
#   if countType == 'allexceptlast':
    return deviceFiles[:-count]
  if deviceFilesEntity['time']:
    dateTime = deviceFilesEntity['time'][1]
    count = 0
    if deviceFilesEntity['time'][0] == 'before':
      for deviceFile in deviceFiles:
        createTime = arrow.get(deviceFile['createTime'])
        if createTime >= dateTime:
          break
        count += 1
      return deviceFiles[:count]
#   if deviceFilesEntity['time'][0] == 'after':
    for deviceFile in deviceFiles:
      createTime = arrow.get(deviceFile['createTime'])
      if createTime >= dateTime:
        break
      count += 1
    return deviceFiles[count:]
  if deviceFilesEntity['range']:
    dateTime = deviceFilesEntity['range'][1]
    spos = 0
    for deviceFile in deviceFiles:
      createTime = arrow.get(deviceFile['createTime'])
      if createTime >= dateTime:
        break
      spos += 1
    dateTime = deviceFilesEntity['range'][2]
    epos = spos
    for deviceFile in deviceFiles[spos:]:
      createTime = arrow.get(deviceFile['createTime'])
      if createTime >= dateTime:
        break
      epos += 1
    return deviceFiles[spos:epos]
#  if deviceFilesEntity['range'] or deviceFilesEntity['dict']:
  if deviceFilesEntity['dict']:
    deviceFileCreateTimes = deviceFilesEntity['dict'][deviceId]
  else:
    deviceFileCreateTimes = deviceFilesEntity['list']
  return [deviceFile for deviceFile in deviceFiles if deviceFile['createTime'] in deviceFileCreateTimes]

# gam <CrOSTypeEntity> get devicefile [select <DeviceFileEntity>] [targetfolder <FilePath>]
def getCrOSDeviceFiles(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  targetFolder = GC.Values[GC.DRIVE_DIR]
  deviceFilesEntity = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'select':
      deviceFilesEntity = getDeviceFilesEntity()
    elif myarg == 'targetfolder':
      targetFolder = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    else:
      unknownArgumentExit()
  fields = 'deviceFiles(type,createTime,downloadUrl)'
  i, count, entityList = getEntityArgument(entityList)
  for deviceId in entityList:
    i += 1
    try:
      deviceFiles = callGAPIitems(cd.chromeosdevices(), 'get', 'deviceFiles',
                                  throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                                  customerId=GC.Values[GC.CUSTOMER_ID], deviceId=deviceId, fields=fields)
      if deviceFilesEntity:
        deviceFiles = _selectDeviceFiles(deviceId, deviceFiles, deviceFilesEntity)
      jcount = len(deviceFiles)
      entityPerformActionNumItems([Ent.CROS_DEVICE, deviceId], jcount, Ent.DEVICE_FILE, i, count)
      Ind.Increment()
      j = 0
      for deviceFile in deviceFiles:
        j += 1
        downloadfilename = os.path.join(targetFolder, f'cros-logs-{deviceId}-{deviceFile["createTime"]}.zip')
        _, content = cd._http.request(deviceFile['downloadUrl'])
        writeFile(downloadfilename, content, mode='wb', continueOnError=True)
        entityActionPerformed([Ent.DEVICE_FILE, downloadfilename], j, jcount)
      Ind.Decrement()
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.CROS_DEVICE, deviceId, i, count)

# gam get devicefile <CrOSEntity> [select <DeviceFileEntity>] [targetfolder <FilePath>]
def doGetCrOSDeviceFiles():
  """Retrieve recent files from specific Chrome OS devices."""
  getCrOSDeviceFiles(getCrOSDeviceEntity())


# Get CrOS devices from gam.cfg print_cros_ous and print_cros_ous_and_children
def doPrintCrOSDevices(entityList=None):
  """Print a list of Chrome OS devices with optional fields."""
  def _printCrOS(cros):
    checkTPMVulnerability(cros)
    if 'autoUpdateExpiration' in cros:
      cros['autoUpdateExpiration'] = formatLocalDatestamp(cros['autoUpdateExpiration'])
    if showDVRstorageFreePercentage:
      _computeDVRstorageFreePercentage(cros)
    for field in reverseLists:
      if field in cros:
        cros[field].reverse()
    if 'orgUnitId' in cros:
      cros['orgUnitId'] = f"id:{cros['orgUnitId']}"
    if FJQC.formatJSON:
      if (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(flattenJSON(cros, listLimit=listLimit, timeObjects=CROS_TIME_OBJECTS)):
        row = {'deviceId': cros['deviceId']}
        if addCSVData:
          row.update(addCSVData)
          if includeCSVDataInJSON:
            cros.update(addCSVData)
        row['JSON'] = json.dumps(cleanJSON(cros, listLimit=listLimit, timeObjects=CROS_TIME_OBJECTS),
                                 ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
      return
    if 'notes' in cros:
      cros['notes'] = escapeCRsNLs(cros['notes'])
    if addCSVData:
      cros.update(addCSVData)
    for cpuStatusReport in cros.get('cpuStatusReports', []):
      for tempInfo in cpuStatusReport.get('cpuTemperatureInfo', []):
        tempInfo['label'] = tempInfo['label'].strip()
    if not noLists and not selectedLists:
      csvPF.WriteRowTitles(flattenJSON(cros, listLimit=listLimit, timeObjects=CROS_TIME_OBJECTS))
      return
    for attrib in ['diskSpaceUsage', 'osUpdateStatus', 'tpmVersionInfo']:
      if attrib in cros:
        for key, value in sorted(cros[attrib].items()):
          attribKey = f'{attrib}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'
          if key not in CROS_TIME_OBJECTS:
            cros[attribKey] = value
          else:
            cros[attribKey] = formatLocalTime(value)
        cros.pop(attrib)
    activeTimeRanges = _filterActiveTimeRanges(cros, selectedLists.get('activeTimeRanges', False), listLimit, startDate, endDate, activeTimeRangesOrder)
    recentUsers = _filterRecentUsers(cros, selectedLists.get('recentUsers', False), listLimit)
    deviceFiles = _filterDeviceFiles(cros, selectedLists.get('deviceFiles', False), listLimit, startTime, endTime)
    cpuStatusReports = _filterCPUStatusReports(cros, selectedLists.get('cpuStatusReports', False), listLimit, startTime, endTime)
    diskVolumeReports = _filterBasicList(cros, 'diskVolumeReports', selectedLists.get('diskVolumeReports', False), listLimit)
    lastKnownNetworks = _filterBasicList(cros, 'lastKnownNetwork', selectedLists.get('lastKnownNetwork', False), listLimit)
    screenshotFiles = _filterScreenshotFiles(cros, selectedLists.get('screenshotFiles', False), listLimit, startTime, endTime)
    systemRamFreeReports = _filterSystemRamFreeReports(cros, selectedLists.get('systemRamFreeReports', False), listLimit, startTime, endTime)
    if oneRow:
      csvPF.WriteRowTitles(flattenJSON(cros, listLimit=listLimit, timeObjects=CROS_TIME_OBJECTS))
      return
    row = {}
    for attrib in cros:
      if attrib in {'cpuInfo', 'backlightInfo', 'bluetoothAdapterInfo', 'fanInfo'}:
        flattenJSON({attrib: cros[attrib]}, flattened=row)
      elif attrib not in {'kind', 'etag', 'diskSpaceUsage', 'osUpdateStatus', 'tpmVersionInfo', 'activeTimeRanges', 'recentUsers',
                          'deviceFiles', 'cpuStatusReports', 'diskVolumeReports', 'lastKnownNetwork', 'screenshotFiles', 'systemRamFreeReports'}:
        if attrib not in CROS_TIME_OBJECTS:
          row[attrib] = cros[attrib]
        else:
          row[attrib] = formatLocalTime(cros[attrib])
    if addCSVData:
      row.update(addCSVData)
    if noLists or (not activeTimeRanges and not recentUsers and not deviceFiles and
                   not cpuStatusReports and not diskVolumeReports and not lastKnownNetworks and not screenshotFiles and not systemRamFreeReports):
      csvPF.WriteRowTitles(row)
      return
    lenATR = len(activeTimeRanges)
    lenRU = len(recentUsers)
    lenDF = len(deviceFiles)
    lenCSR = len(cpuStatusReports)
    lenDVR = len(diskVolumeReports)
    lenLKN = len(lastKnownNetworks)
    lenSSF = len(screenshotFiles)
    lenSRFR = len(systemRamFreeReports)
    new_row = row
    for i in range(min(max(lenATR, lenRU, lenDF, lenCSR, lenDVR, lenLKN, lenSSF, lenSRFR), listLimit or max(lenATR, lenRU, lenDF, lenCSR, lenDVR, lenLKN, lenSSF, lenSRFR))):
      new_row = row.copy()
      if i < lenATR:
        for key in ['date', 'activeTime', 'duration', 'minutes']:
          new_row[f'activeTimeRanges{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = activeTimeRanges[i][key]
      if i < lenRU:
        for key in ['email', 'type']:
          new_row[f'recentUsers{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = recentUsers[i][key]
      if i < lenDF:
        for key in ['name', 'type', 'downloadUrl', 'createTime']:
          new_row[f'deviceFiles{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = deviceFiles[i][key]
      if i < lenCSR:
        new_row[f'cpuStatusReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}reportTime'] = cpuStatusReports[i]['reportTime']
        for tempInfo in cpuStatusReports[i].get('cpuTemperatureInfo', []):
          new_row[f'cpuStatusReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}cpuTemperatureInfo{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{tempInfo["label"]}'] = tempInfo['temperature']
        if 'cpuUtilizationPercentageInfo' in cpuStatusReports[i]:
          new_row[f'cpuStatusReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}cpuUtilizationPercentageInfo'] = cpuStatusReports[i]['cpuUtilizationPercentageInfo']
      if i < lenDVR:
        j = 0
        for volume in diskVolumeReports[i]['volumeInfo']:
          new_row[f'diskVolumeReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}volumeInfo{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}volumeId'] = volume['volumeId']
          new_row[f'diskVolumeReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}volumeInfo{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}storageFree'] = volume['storageFree']
          new_row[f'diskVolumeReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}volumeInfo{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}storageTotal'] = volume['storageTotal']
          if showDVRstorageFreePercentage:
            new_row[f'diskVolumeReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}volumeInfo{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}storageFreePercentage'] = volume['storageFreePercentage']
          j += 1
      if i < lenLKN:
        for key in ['ipAddress', 'wanIpAddress']:
          if key in lastKnownNetworks[i]:
            new_row[f'lastKnownNetwork{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = lastKnownNetworks[i][key]
      if i < lenSSF:
        for key in ['name', 'type', 'downloadUrl', 'createTime']:
          if key in screenshotFiles[i]:
            new_row[f'screenshotFiles{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = screenshotFiles[i][key]
      if i < lenSRFR:
        for key in ['reportTime', 'systemRamFreeInfo']:
          new_row[f'systemRamFreeReports{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = systemRamFreeReports[i][key]
      csvPF.WriteRowTitles(new_row)

  def _callbackPrintCrOS(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _printCrOS(response)
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in [GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN]:
        checkEntityAFDNEorAccessErrorExit(cd, Ent.CROS_DEVICE, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        errMsg = getHTTPError({}, http_status, reason, message)
        entityActionFailedWarning([Ent.CROS_DEVICE, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  cd = buildGAPIObject(API.DIRECTORY)
  fieldsList = ['deviceId']
  reverseLists = []
  csvPF = CSVPrintFile(fieldsList, indexedTitles=CROS_INDEXED_TITLES)
  FJQC = FormatJSONQuoteChar(csvPF)
  projection = orderBy = sortOrder = None
  ous = ['/']
  includeChildOrgunits = True
  queries = [None]
  listLimit = 0
  startDate = endDate = startTime = endTime = None
  selectedLists = {}
  queryTimes = {}
  selectionAllowed = entityList is None
  if selectionAllowed and (GC.Values[GC.PRINT_CROS_OUS] or GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN]):
    entityList = getCfgCrOSEntities()
    selectionAllowed = False
  allFields = noLists = oneRow = showDVRstorageFreePercentage = sortHeaders = False
  activeTimeRangesOrder = 'ASCENDING'
  showItemCountOnly = False
  addCSVData = {}
  includeCSVDataInJSON = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif selectionAllowed and myarg == 'limittoou':
      ous = [getOrgUnitItem()]
      selectionAllowed = False
      includeChildOrgunits = False
    elif selectionAllowed and myarg in CROS_ENTITIES_MAP:
      myarg = CROS_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_CROS_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_CROS_OU, Cmd.ENTITY_CROS_OU_AND_CHILDREN])
      selectionAllowed = False
      includeChildOrgunits = myarg in {Cmd.ENTITY_CROS_OU_AND_CHILDREN, Cmd.ENTITY_CROS_OUS_AND_CHILDREN}
    elif (selectionAllowed or queries == [None]) and myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.CROS_DEVICE)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif selectionAllowed and myarg == 'select':
      _, entityList = getEntityToModify(defaultEntityType=Cmd.ENTITY_CROS, crosAllowed=True, userAllowed=False)
      selectionAllowed = False
    elif myarg == 'orderby':
      orderBy, sortOrder = getOrderBySortOrder(CROS_ORDERBY_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'onerow':
      oneRow = True
    elif myarg == 'nolists':
      noLists = True
      selectedLists = {}
    elif myarg == 'listlimit':
      listLimit = getInteger(minVal=0)
    elif myarg in CROS_START_ARGUMENTS:
      startDate, startTime = _getFilterDateTime()
    elif myarg in CROS_END_ARGUMENTS:
      endDate, endTime = _getFilterDateTime()
    elif myarg == 'timerangeorder':
      activeTimeRangesOrder = getChoice(SORTORDER_CHOICE_MAP, mapChoice=True)
    elif myarg in PROJECTION_CHOICE_MAP:
      projection = PROJECTION_CHOICE_MAP[myarg]
      sortHeaders = True
      if projection == 'FULL':
        fieldsList = []
      else:
        fieldsList = CROS_BASIC_FIELDS_LIST[:]
    elif myarg == 'allfields':
      projection = 'FULL'
      allFields = sortHeaders = True
      fieldsList = []
    elif myarg == 'sortheaders':
      sortHeaders = getBoolean()
    elif myarg in CROS_LIST_FIELDS_CHOICE_MAP:
      selectedLists[CROS_LIST_FIELDS_CHOICE_MAP[myarg]] = True
    elif myarg in CROS_FIELDS_CHOICE_MAP:
      csvPF.AddField(myarg, CROS_FIELDS_CHOICE_MAP, fieldsList)
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in CROS_FIELDS_CHOICE_MAP:
          if field in CROS_LIST_FIELDS_CHOICE_MAP:
            selectedLists[CROS_LIST_FIELDS_CHOICE_MAP[field]] = True
          else:
            csvPF.AddField(field, CROS_FIELDS_CHOICE_MAP, fieldsList)
        else:
          invalidChoiceExit(field, CROS_FIELDS_CHOICE_MAP, True)
    elif myarg == 'reverselists':
      for field in _getFieldsList():
        if field in CROS_LIST_FIELDS_CHOICE_MAP:
          reverseLists.append(CROS_LIST_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, CROS_LIST_FIELDS_CHOICE_MAP, True)
    elif myarg == 'showdvrsfp':
      showDVRstorageFreePercentage = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if selectedLists:
    noLists = False
    projection = 'FULL'
    for selectList in selectedLists:
      addFieldToFieldsList(selectList, CROS_FIELDS_CHOICE_MAP, fieldsList)
  if fieldsList:
    fieldsList.append('deviceId')
  _, _, entityList = getEntityArgument(entityList)
  if FJQC.formatJSON:
    sortHeaders = False
    csvPF.SetJSONTitles(['deviceId', 'JSON'])
    if addCSVData:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
      csvPF.MoveJSONTitlesToEnd(['JSON'])
  substituteQueryTimes(queries, queryTimes)
  if entityList is None:
    sortRows = False
    fields = getItemFieldsFromFieldsList('chromeosdevices', fieldsList)
    for ou in ous:
      ou = makeOrgUnitPathAbsolute(ou)
      oneQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT)) if not includeChildOrgunits else Msg.IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
      for query in queries:
        printGettingAllEntityItemsForWhom(Ent.CROS_DEVICE, ou,
                                          query=query, qualifier=oneQualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
        pageMessage = getPageMessageForWhom()
        pageToken = None
        totalItems = 0
        tokenRetries = 0
        while True:
          try:
            feed = callGAPI(cd.chromeosdevices(), 'list',
                            throwReasons=[GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT,
                                          GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            pageToken=pageToken,
                            customerId=GC.Values[GC.CUSTOMER_ID], query=query, projection=projection,
                            orgUnitPath=ou, includeChildOrgunits=includeChildOrgunits,
                            orderBy=orderBy, sortOrder=sortOrder, fields=fields, maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
            tokenRetries = 0
            pageToken, totalItems = _processGAPIpagesResult(feed, 'chromeosdevices', None, totalItems, pageMessage, None, Ent.CROS_DEVICE)
            if feed:
              if not showItemCountOnly:
                for cros in feed.get('chromeosdevices', []):
                  _printCrOS(cros)
              del feed
            if not pageToken:
              _finalizeGAPIpagesResult(pageMessage)
              printGotAccountEntities(totalItems)
              break
          except GAPI.invalidInput as e:
            message = str(e)
# Invalid Input: xyz - Check for invalid pageToken!!
# 0123456789012345
            if message[15:] == pageToken:
              tokenRetries += 1
              if tokenRetries <= 2:
                writeStderr(f'{WARNING_PREFIX}{Msg.LIST_CHROMEOS_INVALID_INPUT_PAGE_TOKEN_RETRY}')
                time.sleep(tokenRetries*5)
                continue
              entityActionFailedWarning([Ent.CROS_DEVICE, None], message)
              return
            entityActionFailedWarning([Ent.CROS_DEVICE, None], invalidQuery(query) if query is not None else message)
            return
          except GAPI.invalidOrgunit as e:
            entityActionFailedWarning([Ent.CROS_DEVICE, None], str(e))
            return
          except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.permissionDenied):
            accessErrorExit(cd)
    if showItemCountOnly:
      writeStdout(f'{totalItems}\n')
      return
  else:
    if showItemCountOnly:
      writeStdout(f'{len(entityList)}\n')
      return
    sortRows = True
    if allFields or len(set(fieldsList)) > 1:
      jcount = len(entityList)
      fields = getFieldsFromFieldsList(fieldsList)
      svcargs = dict([('customerId', GC.Values[GC.CUSTOMER_ID]), ('deviceId', None), ('projection', projection), ('fields', fields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
      method = getattr(cd.chromeosdevices(), 'get')
      dbatch = cd.new_batch_http_request(callback=_callbackPrintCrOS)
      bcount = 0
      j = 0
      for deviceId in entityList:
        j += 1
        svcparms = svcargs.copy()
        svcparms['deviceId'] = deviceId
        dbatch.add(method(**svcparms), request_id=batchRequestID('', 0, 0, j, jcount, deviceId))
        bcount += 1
        if bcount >= GC.Values[GC.BATCH_SIZE]:
          executeBatch(dbatch)
          dbatch = cd.new_batch_http_request(callback=_callbackPrintCrOS)
          bcount = 0
      if bcount > 0:
        dbatch.execute()
# The only field specified was deviceId, just list the CrOS devices
    else:
      for cros in entityList:
        _printCrOS({'deviceId': cros})
  if sortRows and orderBy:
    csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
  if sortHeaders:
    csvPF.SetSortTitles(['deviceId'])
  csvPF.writeCSVfile('CrOS')

CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP = {
  'activetimeranges': 'activeTimeRanges',
  'devicefiles': 'deviceFiles',
  'files': 'deviceFiles',
  'recentusers': 'recentUsers',
  'timeranges': 'activeTimeRanges',
  'times': 'activeTimeRanges',
  'users': 'recentUsers',
  }
CROS_ACTIVITY_TIME_OBJECTS = {'createTime'}

# gam print crosactivity [todrive <ToDriveAttribute>*]
#	[(query <QueryCrOS>)|(queries <QueryCrOSList>) [querytime<String> <Time>]
#	 [(limittoou|cros_ou <OrgUnitItem>)|(cros_ou_and_children <OrgUnitItem>)|
#	  (cros_ous <OrgUnitList>)|(cros_ous_and_children <OrgUnitList>)]]
# gam print crosactivity [todrive <ToDriveAttribute>*] select <CrOSTypeEntity>
# gam <CrOSTypeEntity> print crosactivity [todrive <ToDriveAttribute>*]
#	[orderby <CrOSOrderByFieldName> [ascending|descending]]
#	[recentusers] [timeranges] [both] [devicefiles] [all] [oneuserperrow]
#	[start <Date>] [end <Date>] [listlimit <Number>]
#	[reverselists <CrOSActivityListFieldNameList>]
#	[timerangeorder ascending|descending]
#	[delimiter <Character>]
#	[formatjson [quotechar <Character>]]
def doPrintCrOSActivity(entityList=None):
  """Print recent activity for Chrome OS devices."""
  def _printCrOS(cros):
    row = {}
    for field in reverseLists:
      if field in cros:
        cros[field].reverse()
    if 'orgUnitId' in cros:
      cros['orgUnitId'] = f"id:{cros['orgUnitId']}"
    if FJQC.formatJSON:
      if (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(flattenJSON(cros, listLimit=listLimit, timeObjects=CROS_ACTIVITY_TIME_OBJECTS)):
        csvPF.WriteRowNoFilter({'deviceId': cros['deviceId'],
                                'JSON': json.dumps(cleanJSON(cros, timeObjects=CROS_ACTIVITY_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
      return
    for attrib in cros:
      if attrib not in {'recentUsers', 'activeTimeRanges', 'deviceFiles'}:
        row[attrib] = cros[attrib]
    for activeTimeRange in _filterActiveTimeRanges(cros, selectedLists.get('activeTimeRanges', False), listLimit, startDate, endDate, activeTimeRangesOrder):
      new_row = row.copy()
      for key in ['date', 'duration', 'minutes']:
        new_row[f'activeTimeRanges{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = activeTimeRange[key]
      csvPF.WriteRow(new_row)
    recentUsers = _filterRecentUsers(cros, selectedLists.get('recentUsers', False), listLimit)
    if recentUsers:
      if not oneUserPerRow:
        new_row = row.copy()
        new_row[f'recentUsers{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}email'] = delimiter.join([recentUser['email'] for recentUser in recentUsers])
        csvPF.WriteRow(new_row)
      else:
        for recentUser in recentUsers:
          new_row = row.copy()
          new_row[f'recentUsers{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}email'] = recentUser['email']
          csvPF.WriteRow(new_row)
    for deviceFile in _filterDeviceFiles(cros, selectedLists.get('deviceFiles', False), listLimit, startTime, endTime):
      new_row = row.copy()
      for key in ['type', 'createTime']:
        new_row[f'deviceFiles{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{key}'] = deviceFile[key]
      csvPF.WriteRow(new_row)

  def _callbackPrintCrOS(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _printCrOS(response)
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in [GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN]:
        checkEntityAFDNEorAccessErrorExit(cd, Ent.CROS_DEVICE, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        errMsg = getHTTPError({}, http_status, reason, message)
        entityActionFailedWarning([Ent.CROS_DEVICE, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  cd = buildGAPIObject(API.DIRECTORY)
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  fieldsList = ['deviceId', 'annotatedAssetId', 'annotatedLocation', 'serialNumber', 'orgUnitId', 'orgUnitPath']
  reverseLists = []
  csvPF = CSVPrintFile(fieldsList)
  FJQC = FormatJSONQuoteChar(csvPF)
  projection = 'FULL'
  orderBy = sortOrder = None
  ous = [None]
  queries = [None]
  listLimit = 0
  startDate = endDate = startTime = endTime = None
  selectedLists = {}
  queryTimes = {}
  selectionAllowed = entityList is None
  if selectionAllowed and (GC.Values[GC.PRINT_CROS_OUS] or GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN]):
    entityList = getCfgCrOSEntities()
    selectionAllowed = False
  oneUserPerRow = False
  directlyInOU = True
  activeTimeRangesOrder = 'ASCENDING'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif selectionAllowed and myarg == 'limittoou':
      ous = [getOrgUnitItem()]
      selectionAllowed = False
      directlyInOU = True
    elif selectionAllowed and myarg in CROS_ENTITIES_MAP:
      myarg = CROS_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_CROS_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_CROS_OU, Cmd.ENTITY_CROS_OU_AND_CHILDREN])
      selectionAllowed = False
      directlyInOU = myarg in {Cmd.ENTITY_CROS_OU, Cmd.ENTITY_CROS_OUS}
    elif (selectionAllowed or queries == [None]) and myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.CROS_DEVICE)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif selectionAllowed and myarg == 'select':
      _, entityList = getEntityToModify(defaultEntityType=Cmd.ENTITY_CROS, crosAllowed=True, userAllowed=False)
      selectionAllowed = False
    elif myarg == 'oneuserperrow':
      oneUserPerRow = True
    elif myarg == 'listlimit':
      listLimit = getInteger(minVal=0)
    elif myarg in CROS_START_ARGUMENTS:
      startDate, startTime = _getFilterDateTime()
    elif myarg in CROS_END_ARGUMENTS:
      endDate, endTime = _getFilterDateTime()
    elif myarg == 'timerangeorder':
      activeTimeRangesOrder = getChoice(SORTORDER_CHOICE_MAP, mapChoice=True)
    elif myarg in CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP:
      selectedLists[CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP[myarg]] = True
    elif myarg == 'both':
      selectedLists['activeTimeRanges'] = selectedLists['recentUsers'] = True
    elif myarg == 'all':
      selectedLists['activeTimeRanges'] = selectedLists['recentUsers'] = selectedLists['deviceFiles'] = True
    elif myarg == 'reverselists':
      for field in _getFieldsList():
        if field in CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP:
          reverseLists.append(CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP, True)
    elif myarg == 'orderby':
      orderBy, sortOrder = getOrderBySortOrder(CROS_ORDERBY_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not selectedLists:
    selectedLists['activeTimeRanges'] = selectedLists['recentUsers'] = True
  if selectedLists.get('recentUsers', False):
    fieldsList.append('recentUsers')
    csvPF.AddTitles(f'recentUsers{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}email')
  if selectedLists.get('activeTimeRanges', False):
    fieldsList.append('activeTimeRanges')
    csvPF.AddTitles([f'activeTimeRanges{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}date',
                     f'activeTimeRanges{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}duration',
                     f'activeTimeRanges{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}minutes'])
  if selectedLists.get('deviceFiles', False):
    fieldsList.append('deviceFiles')
    csvPF.AddTitles([f'deviceFiles{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}type',
                     f'deviceFiles{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}createTime'])
  _, _, entityList = getEntityArgument(entityList)
  if FJQC.formatJSON:
    csvPF.SetJSONTitles(['deviceId', 'JSON'])
  substituteQueryTimes(queries, queryTimes)
  if entityList is None:
    sortRows = False
    fields = getItemFieldsFromFieldsList('chromeosdevices', fieldsList)
    for ou in ous:
      if ou is not None:
        ou = makeOrgUnitPathAbsolute(ou)
      ouList = [ou]
      if not directlyInOU:
        try:
          orgs = callGAPI(cd.orgunits(), 'list',
                          throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                          customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
                          type='all', fields='organizationUnits(orgUnitPath)')
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
          checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
          return
        ouList.extend([subou['orgUnitPath'] for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
      for subou in ouList:
        if subou is not None:
          orgUnitPath = makeOrgUnitPathAbsolute(subou)
        else:
          orgUnitPath = subou
        for query in queries:
          if orgUnitPath is not None:
            oneQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
            printGettingAllEntityItemsForWhom(Ent.CROS_DEVICE, orgUnitPath, qualifier=oneQualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
            pageMessage = getPageMessageForWhom()
          else:
            printGettingAllAccountEntities(Ent.CROS_DEVICE, query)
            pageMessage = getPageMessage()
          pageToken = None
          totalItems = 0
          tokenRetries = 0
          while True:
            try:
              feed = callGAPI(cd.chromeosdevices(), 'list',
                              throwReasons=[GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT,
                                            GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              pageToken=pageToken,
                              customerId=GC.Values[GC.CUSTOMER_ID], query=query, projection=projection, orgUnitPath=orgUnitPath,
                              orderBy=orderBy, sortOrder=sortOrder, fields=fields, maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
              tokenRetries = 0
              pageToken, totalItems = _processGAPIpagesResult(feed, 'chromeosdevices', None, totalItems, pageMessage, None, Ent.CROS_DEVICE)
              if feed:
                for cros in feed.get('chromeosdevices', []):
                  _printCrOS(cros)
                del feed
              if not pageToken:
                _finalizeGAPIpagesResult(pageMessage)
                printGotAccountEntities(totalItems)
                break
            except GAPI.invalidInput as e:
              message = str(e)
# Invalid Input: xyz - Check for invalid pageToken!!
# 0123456789012345
              if message[15:] == pageToken:
                tokenRetries += 1
                if tokenRetries <= 2:
                  writeStderr(f'{WARNING_PREFIX}{Msg.LIST_CHROMEOS_INVALID_INPUT_PAGE_TOKEN_RETRY}')
                  time.sleep(tokenRetries*5)
                  continue
                entityActionFailedWarning([Ent.CROS_DEVICE, None], message)
                return
              entityActionFailedWarning([Ent.CROS_DEVICE, None], invalidQuery(query) if query is not None else message)
              return
            except GAPI.invalidOrgunit as e:
              entityActionFailedWarning([Ent.CROS_DEVICE, None], str(e))
              return
            except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
              accessErrorExit(cd)
  else:
    sortRows = True
    jcount = len(entityList)
    fields = getFieldsFromFieldsList(fieldsList)
    svcargs = dict([('customerId', GC.Values[GC.CUSTOMER_ID]), ('deviceId', None), ('projection', projection), ('fields', fields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(cd.chromeosdevices(), 'get')
    dbatch = cd.new_batch_http_request(callback=_callbackPrintCrOS)
    bcount = 0
    j = 0
    for deviceId in entityList:
      j += 1
      svcparms = svcargs.copy()
      svcparms['deviceId'] = deviceId
      dbatch.add(method(**svcparms), request_id=batchRequestID('', 0, 0, j, jcount, deviceId))
      bcount += 1
      if bcount >= GC.Values[GC.BATCH_SIZE]:
        executeBatch(dbatch)
        dbatch = cd.new_batch_http_request(callback=_callbackPrintCrOS)
        bcount = 0
    if bcount > 0:
      dbatch.execute()
  if sortRows and orderBy:
    csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
  csvPF.writeCSVfile('CrOS Activity')

# gam <CrOSTypeEntity> print [cros|croses|crosactivity]
def doPrintCrOSEntity(entityList):
  """Print or extract information for Chrome OS devices."""
  if getChoice([Cmd.ARG_CROS, Cmd.ARG_CROSES, Cmd.ARG_CROSACTIVITY], defaultChoice=None) != Cmd.ARG_CROSACTIVITY:
    if not Cmd.ArgumentsRemaining():
      writeEntityNoHeaderCSVFile(Ent.CROS_DEVICE, entityList)
    else:
      doPrintCrOSDevices(entityList)
  else:
    doPrintCrOSActivity(entityList)

CROS_TELEMETRY_FIELDS_CHOICE_MAP = {
  'appreport': 'appReport',
  'audiostatusreport': 'audioStatusReport',
  'batteryinfo': 'batteryInfo',
  'batterystatusreport': 'batteryStatusReport',
  'bootperformancereport': 'bootPerformanceReport',
  'cpuinfo': 'cpuInfo',
  'cpustatusreport': 'cpuStatusReport',
  'customer': 'customer',
  'deviceid': 'deviceId',
  'graphicsinfo': 'graphicsInfo',
  'graphicsstatusreport': 'graphicsStatusReport',
  'heartbeatstatusreport': 'heartbeatStatusReport',
  'kioskappstatusreport': 'kioskAppStatusReport',
  'memoryinfo': 'memoryInfo',
  'memorystatusreport': 'memoryStatusReport',
  'name': 'name',
  'networkbandwidthreport': 'networkBandwidthReport',
  'networkdiagnosticsreport': 'networkDiagnosticsReport',
  'networkinfo': 'networkInfo',
  'networkstatusreport': 'networkStatusReport',
  'orgunitid': 'orgUnitId',
  'osupdatestatus': 'osUpdateStatus',
  'peripheralsreport': 'peripheralsReport',
  'runtimecountersreport': 'runtimeCountersReport',
  'serialnumber': 'serialNumber',
  'storageinfo': 'storageInfo',
  'storagestatusreport': 'storageStatusReport',
  'thunderboltinfo': 'thunderboltInfo',
  }
CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP = {
  'appreport': 'appReport',
  'audiostatusreport': 'audioStatusReport',
  'batterystatusreport': 'batteryStatusReport',
  'bootperformancereport': 'bootPerformanceReport',
  'cpustatusreport': 'cpuStatusReport',
  'graphicsstatusreport': 'graphicsStatusReport',
  'heartbeatstatusreport': 'heartbeatStatusReport',
  'kioskappstatusreport': 'kioskAppStatusReport',
  'memorystatusreport': 'memoryStatusReport',
  'networkbandwidthreport': 'networkBandwidthReport',
  'networkdiagnosticsreport': 'networkDiagnosticsReport',
  'networkstatusreport': 'networkStatusReport',
  'osupdatestatus': 'osUpdateStatus',
  'peripheralsreport': 'peripheralsReport',
  'runtimecountersreport': 'runtimeCountersReport',
  'storagestatusreport': 'storageStatusReport',
  }

CROS_TELEMETRY_SCALAR_FIELDS = ['deviceId', 'serialNumber', 'customer', 'name', 'orgUnitId', 'orgUnitPath']
CROS_TELEMETRY_SCALAR_FIELDS_SET = set(CROS_TELEMETRY_SCALAR_FIELDS)
CROS_TELEMETRY_LIST_FIELDS = list(CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP.values())
CROS_TELEMETRY_TIME_OBJECTS = {'reportTime', 'lastUpdateTime', 'lastUpdateCheckTime', 'lastRebootTime'}

# gam info crostelemetry <SerialNumber>
#	<CrOSTelemetryFieldName>* [fields <CrOSTelemetryFieldNameList>]
#	[start <Date>] [end <Date>] [listlimit <Number>]
#	[reverselists <CrOSTelemetryListFieldNameList>]
#	[formatjson [quotechar <Character>]]
# gam show crostelemetry
#	[(ou|org|orgunit|ou_and_children <OrgUnitItem>)|(cros_sn <SerialNumber>)|(filter <String>)]
#	<CrOSTelemetryFieldName>* [fields <CrOSTelemetryFieldNameList>]
#	[start <Date>] [end <Date>] [listlimit <Number>]
#	[reverselists <CrOSTelemetryListFieldNameList>]
#	[formatjson [quotechar <Character>]]
# gam print crostelemetry [todrive <ToDriveAttribute>*]
#	[(ou|org|orgunit|ou_and_children <OrgUnitItem>)|(cros_sn <SerialNumber>)|(filter <String>)]
#	<CrOSTelemetryFieldName>* [fields <CrOSTelemetryFieldNameList>]
#	[reverselists <CrOSTelemetryListFieldNameList>] [oneitemperrow]
#	[start <Date>] [end <Date>] [listlimit <Number>]
#	[formatjson [quotechar <Character>]]
def doInfoPrintShowCrOSTelemetry():
  """Print Chrome OS device telemetry information."""
  def _cleanDevice(device):
    for field in reverseLists:
      if field in device:
        device[field].reverse()
    if listLimit or startTime or endTime:
      for field in CROS_TELEMETRY_LIST_FIELDS:
        if field in device:
          listItems = device.pop(field)
          device[field] = []
          i = 0
          for item in listItems:
            if 'reportTime' in item:
              timeValue = arrow.get(item['reportTime'])
            else:
              timeValue = None
            if (timeValue is None) or (((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime))):
              device[field].append(item)
              i += 1
              if listLimit and i == listLimit:
                break
    storageInfo = device.get('storageInfo', {})
    if 'totalDiskBytes' in storageInfo and 'availableDiskBytes' in storageInfo:
      disk_avail = int(storageInfo['availableDiskBytes'])
      disk_size = int(storageInfo['totalDiskBytes'])
      if diskPercentOnly:
        device['storageInfo'] = {}
      device['storageInfo']['percentDiskFree'] = int((disk_avail / disk_size) * 100)
      device['storageInfo']['percentDiskUsed'] = 100 - device['storageInfo']['percentDiskFree']
    for cpuStatusReport in device.get('cpuStatusReport', []):
      for tempInfo in cpuStatusReport.pop('cpuTemperatureInfo', []):
        if 'temperatureCelsius' in tempInfo:
          cpuStatusReport[f"cpuTemperatureInfo.{tempInfo['label'].strip()}"] = tempInfo['temperatureCelsius']
    if showOrgUnitPath:
      device['orgUnitPath'] = convertOrgUnitIDtoPath(cd, device['orgUnitId'])

  def _printDevice(device):
    _cleanDevice(device)
    if FJQC.formatJSON:
      if (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(flattenJSON(device, timeObjects=CROS_TELEMETRY_TIME_OBJECTS)):
        csvPF.WriteRowNoFilter({'deviceId': device['deviceId'],
                                'JSON': json.dumps(cleanJSON(device, timeObjects=CROS_TELEMETRY_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
      return
    if not oneItemPerRow:
      csvPF.WriteRowTitles(flattenJSON(device, timeObjects=CROS_TELEMETRY_TIME_OBJECTS))
      return
    listLens = {}
    maxLen = 0
    for field in CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP.values():
      if field in device:
        listLens[field] = len(device[field])
        if listLens[field] > maxLen:
          maxLen = listLens[field]
    baserow = {}
    for field in CROS_TELEMETRY_SCALAR_FIELDS:
      if field in device:
        baserow[field] = device[field]
    for i in range(maxLen):
      row = baserow.copy()
      for field, fieldLen in listLens.items():
        if i < fieldLen:
          flattenJSON({field: device[field][i]}, flattened=row, timeObjects=CROS_TELEMETRY_TIME_OBJECTS)
      csvPF.WriteRowTitles(row)

  def _showDevice(device, i=0, count=0):
    _cleanDevice(device)
    if FJQC.formatJSON:
      printLine(json.dumps(cleanJSON(device), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.CROS_DEVICE, device['deviceId']], i, count)
    Ind.Increment()
    for up in CROS_TELEMETRY_SCALAR_FIELDS:
      if up in device:
        printKeyValueList([up, device[up]])
    showJSON(None, device, skipObjects=CROS_TELEMETRY_SCALAR_FIELDS_SET, timeObjects=CROS_TELEMETRY_TIME_OBJECTS)
    Ind.Decrement()

  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  cd = None
  parent = _getCustomersCustomerIdWithC()
  fieldsList = []
  reverseLists = []
  action = Act.Get()
  if action == Act.INFO:
    sn = getString(Cmd.OB_SERIAL_NUMBER)
    pfilters = [(f'serialNumber={sn}', f'serialNumber={sn}')]
    Act.Set(Act.SHOW)
  else:
    pfilters = []
  csvPF = CSVPrintFile(['deviceId'], CROS_TELEMETRY_SCALAR_FIELDS) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  diskPercentOnly = showOrgUnitPath = False
  listLimit = 0
  startTime = endTime = None
  oneItemPerRow = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'ou', 'org', 'orgunit', 'limittoou', 'ouandchildren', 'crossn', 'filter'}:
      if pfilters:
        Cmd.Backup()
        usageErrorExit(Msg.ONLY_ONE_DEVICE_SELECTION_ALLOWED.format(pfilters[0][1]))
      if myarg == 'crossn':
        sn = getString(Cmd.OB_SERIAL_NUMBER)
        pfilters = [(f'serialNumber={sn}', f'serialNumber={sn}')]
      elif myarg == 'filter':
        pf = getString(Cmd.OB_STRING)
        pfilters = [(pf, pf)]
      else:
        if cd is None:
          cd = buildGAPIObject(API.DIRECTORY)
        orgUnitPath, orgUnitId = getOrgUnitId(cd)
        pfilters = [(f'orgUnitId={orgUnitId[3:]}', f'orgUnitPath={orgUnitPath}')]
        if myarg == 'ouandchildren':
          try:
            subous = callGAPI(cd.orgunits(), 'list',
                              throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                              customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=orgUnitId,
                              type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
          except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
            checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitId)
            return
          pfilters.extend([(f'orgUnitId={subou["orgUnitId"][3:]}', f'orgUnitPath={subou["orgUnitPath"]}') for subou in subous.get('organizationUnits', [])])
    elif myarg == 'listlimit':
      listLimit = getInteger()
    elif myarg in CROS_START_ARGUMENTS:
      _, startTime = _getFilterDateTime()
    elif myarg in CROS_END_ARGUMENTS:
      _, endTime = _getFilterDateTime()
    elif myarg in CROS_TELEMETRY_FIELDS_CHOICE_MAP:
      fieldsList.append(CROS_TELEMETRY_FIELDS_CHOICE_MAP[myarg])
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in CROS_TELEMETRY_FIELDS_CHOICE_MAP:
          fieldsList.append(CROS_TELEMETRY_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, CROS_TELEMETRY_FIELDS_CHOICE_MAP, True)
    elif myarg == 'reverselists':
      for field in _getFieldsList():
        if field in CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP:
          reverseLists.append(CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP[field])
        else:
          invalidChoiceExit(field, CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP, True)
    elif myarg == 'showorgunitpath':
      showOrgUnitPath = True
      if cd is None:
        cd = buildGAPIObject(API.DIRECTORY)
    elif myarg == 'storagepercentonly':
      diskPercentOnly = True
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if fieldsList:
    fieldsList.append('deviceId')
    if showOrgUnitPath:
      fieldsList.append('orgUnitId')
  else:
    fieldsList = list(CROS_TELEMETRY_FIELDS_CHOICE_MAP.values())
  readMask = ','.join(set(fieldsList))
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(['deviceId', 'JSON'])
  elif csvPF and not oneItemPerRow:
    csvPF.SetIndexedTitles(CROS_TELEMETRY_LIST_FIELDS)
  if not pfilters:
    pfilters = [(None, 'All')]
  for pfilter in pfilters:
    printGettingAllAccountEntities(Ent.CROS_DEVICE, pfilter[1])
    pageMessage = getPageMessage()
    try:
      devices = callGAPIpages(cm.customers().telemetry().devices(), 'list', 'devices',
                              pageMessage=pageMessage,
                              throwReasons=[GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.INVALID_INPUT],
                              parent=parent, filter=pfilter[0],
                              readMask=readMask, pageSize=GC.Values[GC.DEVICE_MAX_RESULTS])
    except (GAPI.invalidArgument, GAPI.invalidInput) as e:
      message = str(e).replace('\n', ',')
      entityActionFailedWarning([Ent.CROS_DEVICE, None], message)
      return
    except GAPI.permissionDenied as e:
      accessErrorExitNonDirectory(API.CHROMEMANAGEMENT, str(e))
    if csvPF:
      for device in devices:
        _printDevice(device)
    else:
      jcount = len(devices)
      performActionNumItems(jcount, Ent.CROS_DEVICE)
      j = 0
      for device in devices:
        j += 1
        _showDevice(device, j, jcount)
  if csvPF:
    csvPF.writeCSVfile('CrOS Devices Telemetry')

# gam delete browser <DeviceID>
