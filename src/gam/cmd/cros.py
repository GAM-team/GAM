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
from gam.util.output import ISOformatTimeStamp, formatMilliSeconds
from gam.util.args import (
        SORTORDER_CHOICE_MAP,
    StartEndTime,
    YYYYMMDDTHHMMSS_FORMAT_REQUIRED,
    YYYYMMDD_FORMAT,
    _getFilterDateTime,
    checkArgumentPresent,
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
    getStringWithCRsNLs,
    getTimeOrDeltaFromNow,
    makeOrgUnitPathAbsolute,
    makeOrgUnitPathRelative,
    substituteQueryTimes,
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
    ACTION_NOT_PERFORMED_RC,
    actionNotPerformedNumItemsWarning,
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
    printLine,
)
from gam.util.entity import (
    _getCustomersCustomerIdWithC,
    convertEntityToList,
    getDeviceQueries,
    getEntityArgument,
    getEntityList,
    getEntitySelection,
    getEntitySelector,
    getEntityToModify,
    getItemsToModify,
)
from gam.util.errors import (
    entityActionFailedExit,
    invalidArgumentExit,
    invalidChoiceExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.fileio import setFilePath, writeFile
from gam.util.orgunits import getOrgUnitId, getOrgUnitItem
from gam.util.output import (
    formatLocalDatestamp,
    formatLocalTime,
    stderrWarningMsg,
    systemErrorExit,
    writeStderr,
    writeStdout,
)
from gam.constants import PROJECTION_CHOICE_MAP
from gam.cmd.orgunits import _batchMoveCrOSesToOrgUnit, checkOrgUnitPathExists


UNKNOWN = 'Unknown'
WARNING_PREFIX = 'WARNING: '

def getCrOSDeviceEntity():
  if checkArgumentPresent('crossn'):
    return getItemsToModify(Cmd.ENTITY_CROS_SN, getString(Cmd.OB_SERIAL_NUMBER_LIST))
  if checkArgumentPresent('query'):
    return getItemsToModify(Cmd.ENTITY_CROS_QUERY, getString(Cmd.OB_QUERY))
  deviceId = getString(Cmd.OB_CROS_DEVICE_ENTITY)
  if deviceId[:6].lower() == 'query:':
    query = deviceId[6:]
    if query[:12].lower() == 'orgunitpath:':
      return getItemsToModify(Cmd.ENTITY_CROS_OU, query[12:])
    return getItemsToModify(Cmd.ENTITY_CROS_QUERY, query)
  Cmd.Backup()
  return getEntityList(Cmd.OB_CROS_ENTITY)

UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP = {
  'annotatedassetid': 'annotatedAssetId',
  'annotatedlocation': 'annotatedLocation',
  'annotateduser': 'annotatedUser',
  'asset': 'annotatedAssetId',
  'assetid': 'annotatedAssetId',
  'location': 'annotatedLocation',
  'notes': 'notes',
  'org': 'orgUnitPath',
  'orgunitpath': 'orgUnitPath',
  'ou': 'orgUnitPath',
  'tag': 'annotatedAssetId',
  'updatenotes': 'notes',
  'user': 'annotatedUser',
  }

CROS_ACTION_CHOICE_MAP = {
  'deprovisiondifferentmodelreplace': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION', 'DEPROVISION_REASON_DIFFERENT_MODEL_REPLACEMENT'),
  'deprovisiondifferentmodelreplacement': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION', 'DEPROVISION_REASON_DIFFERENT_MODEL_REPLACEMENT'),
  'deprovisionretiringdevice': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION', 'DEPROVISION_REASON_RETIRING_DEVICE'),
  'deprovisionsamemodelreplace': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION', 'DEPROVISION_REASON_SAME_MODEL_REPLACEMENT'),
  'deprovisionsamemodelreplacement': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION', 'DEPROVISION_REASON_SAME_MODEL_REPLACEMENT'),
  'deprovisionupgradetransfer': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION', 'DEPROVISION_REASON_UPGRADE_TRANSFER'),
  'disable': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DISABLE', None),
  'reenable': ('CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_REENABLE', None),
#  'preprovisioneddisable': ('pre_provisioned_disable', None),
#  'preprovisionedreenable': ('pre_provisioned_reenable', None)
  }

CROS_ACTION_NAME_MAP = {
  'CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION': Act.DEPROVISION,
  'CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DISABLE': Act.DISABLE,
  'CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_REENABLE': Act.REENABLE,
#  'pre_provisioned_disable': Act.PRE_PROVISIONED_DISABLE,
#  'pre_provisioned_reenable': Act.PRE_PROVISIONED_REENABLE
  }

# gam <CrOSTypeEntity> update <CrOSAttribute>+ [quickcrosmove [<Boolean>]] [nobatchupdate]
# gam <CrOSTypeEntity> update action <CrOSAction> [acknowledge_device_touch_requirement]
#	[actionbatchsize <Integer>] [maxtodeprov <Integer>]
def updateCrOSDevices(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  noBatchUpdate = False
  update_body = {}
  action_body = {}
  orgUnitPath = updateNotes = None
  ackWipe = False
  quickCrOSMove = GC.Values[GC.QUICK_CROS_MOVE]
  actionBatchSize = 10
  maxToDeprovision = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP:
      up = UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP[myarg]
      if up == 'orgUnitPath':
        orgUnitPath = getOrgUnitItem()
      elif up == 'notes':
        update_body[up] = getStringWithCRsNLs()
        updateNotes = update_body[up] if myarg == 'updatenotes' and update_body[up].find('#notes#') != -1 else None
      else:
        update_body[up] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'action':
      actionLocation = Cmd.Location()
      action_body['changeChromeOsDeviceStatusAction'], deprovisionReason = getChoice(CROS_ACTION_CHOICE_MAP, mapChoice=True)
      if deprovisionReason:
        action_body['deprovisionReason'] = deprovisionReason
      Act.Set(CROS_ACTION_NAME_MAP[action_body['changeChromeOsDeviceStatusAction']])
    elif myarg == 'acknowledgedevicetouchrequirement':
      ackWipe = True
    elif myarg == 'quickcrosmove':
      quickCrOSMove = getBoolean()
    elif myarg == 'nobatchupdate':
      noBatchUpdate = getBoolean()
    elif myarg == 'actionbatchsize':
      actionBatchSize = getInteger(minVal=10, maxVal=250)
    elif myarg == 'maxtodeprov':
      maxToDeprovision = getInteger(minVal=0)
    else:
      unknownArgumentExit()
  if action_body and update_body:
    Cmd.SetLocation(actionLocation-1)
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('action', '<CrOSAttribute>'))
  if orgUnitPath:
    status, orgUnitPath, orgUnitId = checkOrgUnitPathExists(cd, orgUnitPath)
    if not status:
      entityActionFailedWarning([Ent.CROS_DEVICE, ''], f'{Ent.Singular(Ent.ORGANIZATIONAL_UNIT)}: {orgUnitPath}, {Msg.DOES_NOT_EXIST}')
      return
  i, count, entityList = getEntityArgument(entityList)
# Action
  if action_body:
    if action_body['changeChromeOsDeviceStatusAction'] == 'CHANGE_CHROME_OS_DEVICE_STATUS_ACTION_DEPROVISION':
      if not ackWipe:
        stderrWarningMsg(Msg.REFUSING_TO_DEPROVISION_DEVICES.format(count))
        systemErrorExit(ACTION_NOT_PERFORMED_RC, None)
      if maxToDeprovision is None:
        maxToDeprovision = 1
      if count > maxToDeprovision > 0:
        stderrWarningMsg(Msg.REFUSING_TO_DEPROVISION_N_DEVICES.format(count, maxToDeprovision))
        systemErrorExit(ACTION_NOT_PERFORMED_RC, None)
    while i < count:
      bcount = min(count-i, actionBatchSize)
      action_body['deviceIds'] = entityList[i:i+bcount]
      try:
        result = callGAPI(cd.customer().devices().chromeos(), 'batchChangeStatus',
                          throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.CONDITION_NOT_MET, GAPI.INVALID_INPUT,
                                        GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                          customerId=GC.Values[GC.CUSTOMER_ID], body=action_body)
        for status in result['changeChromeOsDeviceStatusResults']:
          i += 1
          deviceId = status['deviceId']
          if 'error' not in status:
            entityActionPerformed([Ent.CROS_DEVICE, deviceId], i, count)
          else:
            entityActionFailedWarning([Ent.CROS_DEVICE, deviceId], status['error']['message'], i, count)
      except (GAPI.invalid, GAPI.invalidArgument, GAPI.conditionNotMet, GAPI.invalidInput, GAPI.badRequest, GAPI.forbidden) as e:
        entityActionFailedExit([Ent.CROS_DEVICE, None], str(e))
    return
# Update
  function = None
  if update_body or noBatchUpdate:
    if orgUnitPath and (not quickCrOSMove or noBatchUpdate):
      update_body['orgUnitPath'] = orgUnitPath
      if GC.Values[GC.UPDATE_CROS_OU_WITH_ID]:
        update_body['orgUnitId'] = orgUnitId
      orgUnitPath = None
    function = 'update'
    parmId = 'deviceId'
    kwargs = {parmId: None, 'body': update_body, 'fields': ''}
  if orgUnitPath:
    Act.Set(Act.ADD)
    _batchMoveCrOSesToOrgUnit(cd, orgUnitPath, orgUnitId, 0, 0, entityList, quickCrOSMove)
    Act.Set(Act.UPDATE)
  if function is None:
    return
  for deviceId in entityList:
    i += 1
    kwargs[parmId] = deviceId
    try:
      if updateNotes:
        oldNotes = callGAPI(cd.chromeosdevices(), 'get',
                            throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                            customerId=GC.Values[GC.CUSTOMER_ID], deviceId=deviceId, fields='notes').get('notes', '')
        update_body['notes'] = updateNotes.replace('#notes#', oldNotes)
      callGAPI(cd.chromeosdevices(), function,
               throwReasons=[GAPI.INVALID, GAPI.CONDITION_NOT_MET, GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT,
                             GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
               customerId=GC.Values[GC.CUSTOMER_ID], **kwargs)
      entityActionPerformed([Ent.CROS_DEVICE, deviceId], i, count)
    except (GAPI.invalid, GAPI.conditionNotMet, GAPI.invalidInput) as e:
      entityActionFailedWarning([Ent.CROS_DEVICE, deviceId], str(e), i, count)
    except GAPI.invalidOrgunit:
      entityActionFailedWarning([Ent.CROS_DEVICE, deviceId], Msg.INVALID_ORGUNIT, i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.CROS_DEVICE, deviceId, i, count)

# gam update cros|croses <CrOSEntity> <CrOSAttribute>+ [quickcrosmove [<Boolean>]] [nobatchupdate]
# gam update cros|croses <CrOSEntity> action <CrOSAction> [acknowledge_device_touch_requirement]
def doUpdateCrOSDevices():
  updateCrOSDevices(getCrOSDeviceEntity())

CROS_COMMAND_CHOICE_MAP = {
  'reboot': 'REBOOT',
  'remotepowerwash': 'REMOTE_POWERWASH',
  'setvolume': 'SET_VOLUME',
  'takeascreenshot': 'TAKE_A_SCREENSHOT',
  'wipeusers': 'WIPE_USERS'
  }

CROS_DOIT_REQUIRED_COMMANDS = {'WIPE_USERS', 'REMOTE_POWERWASH'}
CROS_KIOSK_COMMANDS = {'REBOOT', 'SET_VOLUME', 'TAKE_A_SCREENSHOT'}
CROS_COMMAND_FINAL_STATES = {'EXPIRED', 'CANCELLED', 'EXECUTED_BY_CLIENT'}
CROS_COMMAND_TIME_OBJECTS = {'executeTime', 'issueTime', 'commandExpireTime'}

def displayCrOSCommandResult(cd, deviceId, commandId, checkResultRetries, i, count, csvPF, addCSVData):
  Ind.Increment()
  try:
    for _ in range(0, checkResultRetries):
      time.sleep(2)
      result = callGAPI(cd.customer().devices().chromeos().commands(), 'get',
                        throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.FORBIDDEN],
                        customerId=GC.Values[GC.CUSTOMER_ID], deviceId=deviceId, commandId=commandId)
      if csvPF:
        result['deviceId'] = deviceId
        if addCSVData:
          result.update(addCSVData)
        csvPF.WriteRowTitles(flattenJSON(result, timeObjects=CROS_COMMAND_TIME_OBJECTS))
        break
      showJSON(None, result, timeObjects=CROS_COMMAND_TIME_OBJECTS)
      state = result.get('state')
      if state in CROS_COMMAND_FINAL_STATES:
        break
  except (GAPI.invalidArgument, GAPI.badRequest, GAPI.notFound, GAPI.forbidden) as e:
    entityActionFailedWarning([Ent.CROS_DEVICE, deviceId, Ent.COMMAND_ID, commandId], str(e), i, count)
  Ind.Decrement()

def writeCrOSCommandResults(csvPF, addCSVData):
  sortTitles = ['deviceId']
  if addCSVData:
    sortTitles.extend(sorted(addCSVData.keys()))
  sortTitles.append('commandId')
  csvPF.SetSortTitles(sortTitles)
  csvPF.writeCSVfile('CrOS Commands')

# gam <CrOSTypeEntity> issuecommand command <CrOSCommand>
#	[times_to_check_status <Integer>] [doit]
#	[csv (addcsvdata <FieldName> <String>)*]
def issueCommandCrOSDevices(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = None
  addCSVData = {}
  body = {}
  checkResultRetries = 1
  doit = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'command':
      body['commandType'] = getChoice(CROS_COMMAND_CHOICE_MAP, mapChoice=True)
      if body['commandType'] == 'SET_VOLUME':
        body['payload'] = json.dumps({'volume': getInteger(minVal=0, maxVal=100)})
    elif myarg == 'timestocheckstatus':
      checkResultRetries = getInteger(minVal=0)
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['deviceId'])
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'doit':
      doit = True
    else:
      unknownArgumentExit()
  if not body:
    missingArgumentExit('command <CrOSCommand>')
  i, count, entityList = getEntityArgument(entityList)
  if body['commandType'] in CROS_DOIT_REQUIRED_COMMANDS and not doit:
    actionNotPerformedNumItemsWarning(count, Ent.CROS_DEVICE, Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION)
    return
  for deviceId in entityList:
    i += 1
    try:
      result = callGAPI(cd.customer().devices().chromeos(), 'issueCommand',
                        throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND],
                        customerId=GC.Values[GC.CUSTOMER_ID], deviceId=deviceId, body=body)
      commandId = result.get('commandId')
      entityActionPerformed([Ent.CROS_DEVICE, deviceId, Ent.ACTION, body['commandType'], Ent.COMMAND_ID, commandId], i, count)
      displayCrOSCommandResult(cd, deviceId, commandId, checkResultRetries, i, count, csvPF, addCSVData)
    except GAPI.invalidArgument as e:
      errMsg = str(e)
      if body['commandType'] in CROS_KIOSK_COMMANDS:
        errMsg += Msg.KIOSK_MODE_REQUIRED.format(body['commandType'])
      entityActionFailedWarning([Ent.CROS_DEVICE, deviceId], errMsg, i, count)
    except GAPI.notFound as e:
      entityActionFailedWarning([Ent.CROS_DEVICE, deviceId], str(e), i, count)
  if csvPF:
    writeCrOSCommandResults(csvPF, addCSVData)

# gam issuecommand <CrOSEntity> command <CrOSCommand>
#	[times_to_check_status <Integer>] [doit]
#	[csv (addcsvdata <FieldName> <String>)*]
def doIssueCommandCrOSDevices():
  issueCommandCrOSDevices(getCrOSDeviceEntity())

# gam <CrOSTypeEntity> getcommand commandid <CommandID>
#	[times_to_check_status <Integer>] [csv]
#	[csv (addcsvdata <FieldName> <String>)*]
def getCommandResultCrOSDevices(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = None
  addCSVData = {}
  commandId = ''
  checkResultRetries = 1
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'commandid':
      commandId = getString(Cmd.OB_COMMAND_ID)
    elif myarg == 'timestocheckstatus':
      checkResultRetries = getInteger(minVal=0)
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['deviceId'])
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      unknownArgumentExit()
  if not commandId:
    missingArgumentExit('commandid <CommandID>')
  i, count, entityList = getEntityArgument(entityList)
  for deviceId in entityList:
    i += 1
    printEntity([Ent.CROS_DEVICE, deviceId, Ent.COMMAND_ID, commandId], i, count)
    displayCrOSCommandResult(cd, deviceId, commandId, checkResultRetries, i, count, csvPF, addCSVData)
  if csvPF:
    writeCrOSCommandResults(csvPF, addCSVData)

# gam getcommand <CrOSEntity> commandid <CommandID>
#	[times_to_check_status <Integer>] [csv]
#	[csv (addcsvdata <FieldName> <String>)*]
def doGetCommandResultCrOSDevices():
  getCommandResultCrOSDevices(getCrOSDeviceEntity())

# From https://www.chromium.org/chromium-os/tpm_firmware_update
CROS_TPM_VULN_VERSIONS = ['41f', '420', '628', '8520']
CROS_TPM_FIXED_VERSIONS = ['422', '62b', '8521']

def checkTPMVulnerability(cros):
  if 'tpmVersionInfo' in cros and 'firmwareVersion' in cros['tpmVersionInfo']:
    if cros['tpmVersionInfo']['firmwareVersion'] in CROS_TPM_VULN_VERSIONS:
      cros['tpmVersionInfo']['tpmVulnerability'] = 'VULNERABLE'
    elif cros['tpmVersionInfo']['firmwareVersion'] in CROS_TPM_FIXED_VERSIONS:
      cros['tpmVersionInfo']['tpmVulnerability'] = 'UPDATED'
    else:
      cros['tpmVersionInfo']['tpmVulnerability'] = 'NOT IMPACTED'

def _filterActiveTimeRanges(cros, selected, listLimit, startDate, endDate, activeTimeRangesOrder):
  if not selected:
    cros.pop('activeTimeRanges', None)
    return []
  filteredItems = []
  activeTimeRanges = cros.get('activeTimeRanges', [])
  if activeTimeRangesOrder == 'DESCENDING':
    activeTimeRanges.reverse()
  i = 0
  for item in activeTimeRanges:
    activityDate = arrow.Arrow.strptime(item['date'], YYYYMMDD_FORMAT)
    if ((startDate is None) or (activityDate >= startDate)) and ((endDate is None) or (activityDate <= endDate)):
      item['duration'] = formatMilliSeconds(item['activeTime'])
      item['minutes'] = item['activeTime']//60000
      item['activeTime'] = str(item['activeTime'])
      filteredItems.append(item)
      i += 1
      if listLimit and i == listLimit:
        break
  cros['activeTimeRanges'] = filteredItems
  return cros['activeTimeRanges']

def _filterDeviceFiles(cros, selected, listLimit, startTime, endTime):
  if not selected:
    cros.pop('deviceFiles', None)
    return []
  filteredItems = []
  i = 0
  for item in cros.get('deviceFiles', []):
    timeValue = arrow.get(item['createTime'])
    if ((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime)):
      item['createTime'] = formatLocalTime(item['createTime'])
      filteredItems.append(item)
      i += 1
      if listLimit and i == listLimit:
        break
  cros['deviceFiles'] = filteredItems
  return cros['deviceFiles']

def _filterCPUStatusReports(cros, selected, listLimit, startTime, endTime):
  if not selected:
    cros.pop('cpuStatusReports', None)
    return []
  filteredItems = []
  i = 0
  for item in cros.get('cpuStatusReports', []):
    timeValue = arrow.get(item['reportTime'])
    if ((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime)):
      item['reportTime'] = formatLocalTime(item['reportTime'])
      for tempInfo in item.get('cpuTemperatureInfo', []):
        tempInfo['label'] = tempInfo['label'].strip()
      if 'cpuUtilizationPercentageInfo' in item:
        item['cpuUtilizationPercentageInfo'] = ','.join([str(x) for x in item['cpuUtilizationPercentageInfo']])
      filteredItems.append(item)
      i += 1
      if listLimit and i == listLimit:
        break
  cros['cpuStatusReports'] = filteredItems
  return cros['cpuStatusReports']

def _filterSystemRamFreeReports(cros, selected, listLimit, startTime, endTime):
  if not selected:
    cros.pop('systemRamFreeReports', None)
    return []
  filteredItems = []
  i = 0
  for item in cros.get('systemRamFreeReports', []):
    timeValue = arrow.get(item['reportTime'])
    if ((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime)):
      item['reportTime'] = formatLocalTime(item['reportTime'])
      item['systemRamFreeInfo'] = ','.join([str(x) for x in item['systemRamFreeInfo']])
      filteredItems.append(item)
      i += 1
      if listLimit and i == listLimit:
        break
  cros['systemRamFreeReports'] = filteredItems
  return cros['systemRamFreeReports']

def _filterRecentUsers(cros, selected, listLimit):
  if not selected:
    cros.pop('recentUsers', None)
    return []
  filteredItems = []
  i = 0
  for item in cros.get('recentUsers', []):
    item['email'] = item.get('email', [UNKNOWN, 'UnmanagedUser'][item['type'] == 'USER_TYPE_UNMANAGED'])
    filteredItems.append(item)
    i += 1
    if listLimit and i == listLimit:
      break
  cros['recentUsers'] = filteredItems
  return cros['recentUsers']

def _filterScreenshotFiles(cros, selected, listLimit, startTime, endTime):
  if not selected:
    cros.pop('screenshotFiles', None)
    return []
  filteredItems = []
  i = 0
  for item in cros.get('screenshotFiles', []):
    timeValue = arrow.get(item['createTime'])
    if ((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime)):
      item['createTime'] = formatLocalTime(item['createTime'])
      filteredItems.append(item)
      i += 1
      if listLimit and i == listLimit:
        break
  cros['screenshotFiles'] = filteredItems
  return cros['screenshotFiles']

def _filterBasicList(cros, field, selected, listLimit):
  if not selected:
    cros.pop(field, None)
    return []
  if listLimit:
    filteredItems = []
    i = 0
    for item in cros.get(field, []):
      filteredItems.append(item)
      i += 1
      if listLimit and i == listLimit:
        break
    cros[field] = filteredItems
    return cros[field]
  return cros.get(field, [])

def _computeDVRstorageFreePercentage(cros):
  for diskVolumeReport in cros.get('diskVolumeReports', []):
    volumeInfo = diskVolumeReport['volumeInfo']
    for volume in volumeInfo:
      if volume['storageTotal'] != '0':
        volume['storageFreePercentage'] = str(int(int(volume['storageFree'])/int(volume['storageTotal'])*100))
      else:
        volume['storageFreePercentage'] = '0'


CROS_FIELDS_CHOICE_MAP = {
  'activetimeranges': 'activeTimeRanges',
  'annotatedassetid': 'annotatedAssetId',
  'annotatedlocation': 'annotatedLocation',
  'annotateduser': 'annotatedUser',
  'asset': 'annotatedAssetId',
  'assetid': 'annotatedAssetId',
  'autoupdateexpiration': 'autoUpdateExpiration',
  'autoupdatethrough': 'autoUpdateThrough',
  'backlightinfo': 'backlightInfo',
  'bluetoothadapterinfo': 'bluetoothAdapterInfo',
  'bootmode': 'bootMode',
  'chromeostype': 'chromeOsType',
  'cpuinfo': 'cpuInfo',
  'cpustatusreports': 'cpuStatusReports',
  'deprovisionreason': 'deprovisionReason',
  'devicefiles': 'deviceFiles',
  'deviceid': 'deviceId',
  'devicelicensetype': 'deviceLicenseType',
  'diskspaceusage': 'diskSpaceUsage',
  'diskvolumereports': 'diskVolumeReports',
  'dockmacaddress': 'dockMacAddress',
  'ethernetmacaddress': 'ethernetMacAddress',
  'ethernetmacaddress0': 'ethernetMacAddress0',
  'extendedsupporteligible': 'extendedSupportEligible',
  'extendedsupportstart': 'extendedSupportStart',
  'extendedsupportenabled': 'extendedSupportEnabled',
  'faninfo': 'fanInfo',
  'firmwareversion': 'firmwareVersion',
  'firstenrollmenttime': 'firstEnrollmentTime',
  'lastdeprovisiontimestamp': 'lastDeprovisionTimestamp',
  'lastenrollmenttime': 'lastEnrollmentTime',
  'lastknownnetwork': 'lastKnownNetwork',
  'lastsync': 'lastSync',
  'location': 'annotatedLocation',
  'macaddress': 'macAddress',
  'manufacturedate': 'manufactureDate',
  'meid': 'meid',
  'model': 'model',
  'notes': 'notes',
  'ordernumber': 'orderNumber',
  'org': 'orgUnitPath',
  'orgunitid': 'orgUnitId',
  'orgunitpath': 'orgUnitPath',
  'osupdatestatus': 'osUpdateStatus',
  'osversion': 'osVersion',
  'osversioncompliance': 'osVersionCompliance',
  'ou': 'orgUnitPath',
  'platformversion': 'platformVersion',
  'recentusers': 'recentUsers',
  'screenshotfiles': 'screenshotFiles',
  'serialnumber': 'serialNumber',
  'status': 'status',
  'supportenddate': 'supportEndDate',
  'systemramfreereports': 'systemRamFreeReports',
  'systemramtotal': 'systemRamTotal',
  'tag': 'annotatedAssetId',
  'timeranges': 'activeTimeRanges',
  'times': 'activeTimeRanges',
  'tpmversioninfo': 'tpmVersionInfo',
  'user': 'annotatedUser',
  'users': 'recentUsers',
  'willautorenew': 'willAutoRenew',
  }
CROS_BASIC_FIELDS_LIST = ['deviceId', 'annotatedAssetId', 'annotatedLocation', 'annotatedUser', 'lastSync', 'notes', 'serialNumber', 'status']

CROS_SCALAR_PROPERTY_PRINT_ORDER = [
  'orgUnitId',
  'orgUnitPath',
  'annotatedAssetId',
  'annotatedLocation',
  'annotatedUser',
  'lastSync',
  'notes',
  'serialNumber',
  'status',
  'chromeOsType',
  'deviceLicenseType',
  'model',
  'firmwareVersion',
  'platformVersion',
  'osVersion',
  'osVersionCompliance',
  'bootMode',
  'meid',
  'dockMacAddress',
  'ethernetMacAddress',
  'ethernetMacAddress0',
  'macAddress',
  'systemRamTotal',
  'firstEnrollmentTime',
  'lastEnrollmentTime',
  'deprovisionReason',
  'lastDeprovisionTimestamp',
  'orderNumber',
  'manufactureDate',
  'supportEndDate',
  'autoUpdateExpiration',
  'autoUpdateThrough',
  'willAutoRenew',
  ]

CROS_LIST_FIELDS_CHOICE_MAP = {
  'activetimeranges': 'activeTimeRanges',
  'cpustatusreports': 'cpuStatusReports',
  'devicefiles': 'deviceFiles',
  'diskvolumereports': 'diskVolumeReports',
  'files': 'deviceFiles',
  'lastknownnetwork': 'lastKnownNetwork',
  'recentusers': 'recentUsers',
  'screenshotfiles': 'screenshotFiles',
  'systemramfreereports': 'systemRamFreeReports',
  'timeranges': 'activeTimeRanges',
  'times': 'activeTimeRanges',
  'users': 'recentUsers',
  }

CROS_TIME_OBJECTS = {
  'createTime',
  'extendedSupportStart',
  'firstEnrollmentTime',
  'lastDeprovisionTimestamp',
  'lastEnrollmentTime',
  'lastSync',
  'rebootTime',
  'reportTime',
  'supportEndDate',
  'updateTime',
  'updateCheckTime',
  }
CROS_FIELDS_WITH_CRS_NLS = {'notes'}
CROS_START_ARGUMENTS = ['start', 'startdate', 'oldestdate']
CROS_END_ARGUMENTS = ['end', 'enddate']

# gam info cros <CrOSEntity>
# gam <CrOSTypeEntity> info
#	[basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
#	[nolists]
#	[start <Date>] [end <Date>] [listlimit <Number>]
#	[reverselists <CrOSListFieldNameList>]
#	[timerangeorder ascending|descending] [showdvrsfp]
#	[downloadfile latest|<Time>] [targetfolder <FilePath>]
#	[formatjson]
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
  getCrOSDeviceFiles(getCrOSDeviceEntity())


# Get CrOS devices from gam.cfg print_cros_ous and print_cros_ous_and_children
def getCfgCrOSEntities():
  if GC.Values[GC.PRINT_CROS_OUS]:
    entityList = getItemsToModify(Cmd.ENTITY_CROS_OUS, GC.Values[GC.PRINT_CROS_OUS])
  else:
    entityList = []
  if GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN]:
    entityList.extend(getItemsToModify(Cmd.ENTITY_CROS_OUS_AND_CHILDREN, GC.Values[GC.PRINT_CROS_OUS_AND_CHILDREN]))
  return entityList

CROS_ORDERBY_CHOICE_MAP = {
  'lastsync': 'lastSync',
  'location': 'annotatedLocation',
  'notes': 'notes',
  'serialnumber': 'serialNumber',
  'status': 'status',
  'supportenddate': 'supportEndDate',
  'user': 'annotatedUser',
  }

CROS_ENTITIES_MAP = {
  'crosorg': Cmd.ENTITY_CROS_OU,
  'crosorgandchildren': Cmd.ENTITY_CROS_OU_AND_CHILDREN,
  'crosorgs': Cmd.ENTITY_CROS_OUS,
  'crosorgsandchildren': Cmd.ENTITY_CROS_OUS_AND_CHILDREN,
  'crosou': Cmd.ENTITY_CROS_OU,
  'crosouandchildren': Cmd.ENTITY_CROS_OU_AND_CHILDREN,
  'crosous': Cmd.ENTITY_CROS_OUS,
  'crosousandchildren': Cmd.ENTITY_CROS_OUS_AND_CHILDREN
  }

CROS_INDEXED_TITLES = ['activeTimeRanges', 'recentUsers', 'deviceFiles',
                       'cpuStatusReports', 'cpuInfo', 'backlightInfo', 'bluetoothAdapterInfo', 'fanInfo',
                       'diskVolumeReports', 'lastKnownNetwork', 'screenshotFiles', 'systemRamFreeReports']

# gam print cros [todrive <ToDriveAttribute>*]
#	[(query <QueryCrOS>)|(queries <QueryCrOSList>) [querytime<String> <Time>]
#	 [(limittoou|cros_ou <OrgUnitItem>)|(cros_ou_and_children <OrgUnitItem>)|
#	  (cros_ous <OrgUnitList>)|(cros_ous_and_children <OrgUnitList>)]]
# 	[showitemcountonly]
# gam print cros [todrive <ToDriveAttribute>*] select <CrOSTypeEntity>
# gam <CrOSTypeEntity> print cros [todrive <ToDriveAttribute>*]
#	[orderby <CrOSOrderByFieldName> [ascending|descending]]
#	[basic|full|allfields] <CrOSFieldName>* [fields <CrOSFieldNameList>]
#	[nolists|(<CrOSListFieldName>* [onerow])]
#	[start <Date>] [end <Date>] [listlimit <Number>]
#	[reverselists <CrOSListFieldNameList>]
#	[timerangeorder ascending|descending] [showdvrsfp]
#	(addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#	[sortheaders]
#	[formatjson [quotechar <Character>]]
# 	[showitemcountonly]
def doPrintCrOSDevices(entityList=None):
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
