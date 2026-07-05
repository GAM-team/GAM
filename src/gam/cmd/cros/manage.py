"""GAM ChromeOS device management."""

import arrow
import json


import time

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI
from gam.util.output import formatMilliSeconds
from gam.util.args import (
    YYYYMMDD_FORMAT,
    checkArgumentPresent,
    getAddCSVData,
    getArgument,
    getBoolean,
    getChoice,
    getInteger,
    getString,
    getStringWithCRsNLs
)
from gam.util.csv_pf import CSVPrintFile, flattenJSON, showJSON
from gam.util.display import (
    ACTION_NOT_PERFORMED_RC,
    actionNotPerformedNumItemsWarning,
    entityActionFailedWarning,
    entityActionPerformed,
    printEntity
)
from gam.util.entity import getEntityArgument, getEntityList, getItemsToModify
from gam.util.errors import (
    entityActionFailedExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit
)
from gam.util.orgunits import getOrgUnitItem
from gam.util.output import formatLocalTime, stderrWarningMsg, systemErrorExit
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
  """Update settings or state for Chrome OS devices."""
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
  """Issue remote commands (e.g., wipe, reboot) to Chrome OS devices."""
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
  """Get results of previously issued remote commands for Chrome OS devices."""
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
