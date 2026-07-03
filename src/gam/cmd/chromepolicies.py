"""GAM Chrome policy and network management."""

import re
import json
import sys
import mimetypes
import os

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    FALSE_VALUES,
    TRUE_FALSE,
    TRUE_VALUES,
    checkArgumentPresent,
    checkForExtraneousArguments,
    encodeOrgUnitPath,
    getArgument,
    getArgumentEmptyAllowed,
    getChoice,
    getEmailAddress,
    getHHMM,
    getInteger,
    getIntegerEmptyAllowed,
    getJSON,
    getString,
    integerLimits,
    makeOrgUnitPathRelative,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionModifierNumItems,
    entityPerformActionNumItems,
    getPageMessage,
    getPageMessageForWhom,
    invalidQuery,
    performActionNumItems,
    printBlankLine,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
    printLine,
)
from gam.util.entity import convertEmailAddressToUID, convertOrgUnitIDtoPath, getGroupEmailFromID
from gam.util.errors import (
    entityDoesNotExistExit,
    invalidArgumentExit,
    invalidChoiceExit,
    missingArgumentExit,
    missingChoiceExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.fileio import UNKNOWN, setFilePath
from gam.util.orgunits import getOrgUnitId

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

def _getOrgunitsOrgUnitIdPath(cd, orgUnit):
  if orgUnit.startswith('orgunits/'):
    orgUnit = f'id:{orgUnit[9:]}'
  orgUnitPath, orgUnitId = getOrgUnitId(cd, orgUnit)
  return (orgUnitPath, f'orgunits/{orgUnitId[3:]}')

def _getChromePolicySchemaName():
  name = getString(Cmd.OB_SCHEMA_NAME)
  if not name.startswith('customers'):
    name = f'customers/{GC.Values[GC.CUSTOMER_ID]}/policySchemas/{name}'
  return name

def _getChromePolicySchema(cp, name, fields):
  if not name.startswith('customers'):
    name = f'customers/{GC.Values[GC.CUSTOMER_ID]}/policySchemas/{name}'
  try:
    return callGAPI(cp.customers().policySchemas(), 'get',
                    throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                    name=name, fields=fields)
  except GAPI.notFound:
    entityDoesNotExistExit(Ent.CHROME_POLICY_SCHEMA, name)
  except (GAPI.badRequest, GAPI.forbidden):
    accessErrorExit(None)

def commonprefix(m):
  '''Given a list of strings m, return string which is prefix common to all'''
  s1 = min(m)
  loc = s1.find('ENUM_')
  if loc > 0:
    return s1[:loc+5]
  s2 = max(m)
  for i, c in enumerate(s1):
    if c != s2[i]:
      return s1[:i]
  return s1

SCHEMA_TYPE_MESSAGE_MAP = {
  'NullableDuration': {'type': 'TYPE_INT64', 'namedType': 'duration'},
  'NullableLong': {'type': 'TYPE_INT64', 'namedType': 'value'},
  'SystemTimezone': {'type': 'TYPE_STRING', 'namedType': 'value'}
  }

def simplifyChromeSchemaUpdate(schema):
  schema_name = schema['name'].split('/')[-1]
  schema_dict = {'name': schema_name, 'settings': {}}
  for mtype in schema['definition']['messageType']:
    if mtype['name'] in SCHEMA_TYPE_MESSAGE_MAP:
      continue
    for setting in mtype['field']:
      setting_name = setting['name']
      setting_dict = {'name': setting_name, 'type': setting['type'], 'namedType': ''}
      if setting_dict['type'] == 'TYPE_STRING' and setting.get('label') == 'LABEL_REPEATED':
        setting_dict['type'] = 'TYPE_LIST'
      if setting_dict['type'] == 'TYPE_ENUM':
        type_name = setting['typeName']
        for an_enum in schema['definition']['enumType']:
          if an_enum['name'] == type_name:
            setting_dict['enums'] = [enum['name'] for enum in an_enum['value']]
            setting_dict['enum_prefix'] = commonprefix(setting_dict['enums'])
            prefix_len = len(setting_dict['enum_prefix'])
            setting_dict['enums'] = [enum[prefix_len:] for enum in setting_dict['enums'] if not enum.endswith('UNSPECIFIED')]
      elif setting_dict['type'] == 'TYPE_MESSAGE':
        type_name = setting['typeName']
        if type_name not in SCHEMA_TYPE_MESSAGE_MAP:
          continue
        setting_dict['type'] = SCHEMA_TYPE_MESSAGE_MAP[type_name]['type']
        setting_dict['namedType'] = SCHEMA_TYPE_MESSAGE_MAP[type_name]['namedType']
      schema_dict['settings'][setting_name.lower()] = setting_dict
  return(schema_name, schema_dict)

def simplifyChromeSchemaDisplay(schema):
  schema_name = schema['name'].split('/')[-1]
  schema_dict = {'name': schema_name, 'description': schema.get('policyDescription', '')}
  fieldDescriptions = schema['fieldDescriptions']
  enumDict = {}
  for enumType in schema['definition'].get('enumType', []):
    enumEntry = {}
    enumEntry['enums'] = [enum['name'] for enum in enumType['value']]
    enumEntry['enum_prefix'] = commonprefix(enumEntry['enums'])
    enumEntry['enum_prefix_len'] = prefix_len = len(enumEntry['enum_prefix'])
    enumEntry['enums'] = [enum[prefix_len:] for enum in enumEntry['enums'] if not enum.endswith('UNSPECIFIED')]
    enumDict[enumType['name']] = enumEntry.copy()
  mesgDict = {}
  mesgPops = set()
  for mesgType in schema['definition']['messageType']:
    mtypeEntry = {'field': {}, 'subfield': False}
    for mfield in mesgType['field']:
      mfield.pop('number')
      mtypeEntry['field'][mfield.pop('name')] = mfield
    mesgDict[mesgType['name']] = mtypeEntry.copy()
  for mtypeEntry in mesgDict.values():
    for mfieldName, mfield in mtypeEntry['field'].items():
      mfield['descriptions'] = []
      if mfield['type'] == 'TYPE_STRING' and mfield.get('label') == 'LABEL_REPEATED':
        mfield['type'] = 'TYPE_LIST'
      if mfield['type'] == 'TYPE_ENUM':
        mfield['subtype'] = enumDict[mfield['typeName']]
        for an_enum in schema['definition']['enumType']:
          if an_enum['name'] == mfield['typeName']:
            mfield['descriptions'] = ['']*len(mfield['subtype']['enums'])
            for i, an in enumerate(mfield['subtype']['enums']):
              for fdesc in fieldDescriptions:
                if fdesc.get('field') == mfieldName:
                  for d in fdesc.get('knownValueDescriptions', []):
                    if d['value'][mfield['subtype']['enum_prefix_len']:] == an:
                      mfield['descriptions'][i] = d.get('description', '')
                      break
                  break
            break
      elif mfield['type'] == 'TYPE_MESSAGE':
        subfield = mfield['typeName']
        if subfield not in SCHEMA_TYPE_MESSAGE_MAP:
          mesgDict[subfield]['subfield'] = True
          mfield['subtype'] = mesgDict[subfield]
        else:
          mfield['type'] = SCHEMA_TYPE_MESSAGE_MAP[subfield]['type']
          mesgPops.add(subfield)
        continue
      else:
        for fdesc in fieldDescriptions:
          if fdesc['field'] == mfieldName:
            if 'knownValueDescriptions' in fdesc:
              if isinstance(fdesc['knownValueDescriptions'], list):
                for kvd in fdesc['knownValueDescriptions']:
                  if isinstance(kvd, dict):
                    if 'description' in kvd:
                      mfield['descriptions'].append(f"{kvd['value']}: {kvd['description']}")
                    else:
                      mfield['descriptions'].append(f"{kvd['value']}")
                  else:
                    mfield['descriptions'].extend(kvd)
              else:
                mfield['descriptions'].append(kvd)
            elif 'description' in fdesc:
              mfield['descriptions'].append(fdesc['description'])
  for pfield in mesgPops:
    mesgDict.pop(pfield)
  schema_dict['settings'] = mesgDict
  return(schema_name, schema_dict)

def _getPolicyOrgUnitTarget(cd, cp, myarg, groupEmail):
  if groupEmail:
    Cmd.Backup()
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'group'))
  targetName, targetResource = _getOrgunitsOrgUnitIdPath(cd, getString(Cmd.OB_ORGUNIT_PATH))
  return (targetName, targetName, targetResource, Ent.ORGANIZATIONAL_UNIT, cp.customers().policies().orgunits())

def _getPolicyGroupTarget(cd, cp, myarg, orgUnit):
  if orgUnit:
    Cmd.Backup()
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format(myarg, 'ou|org|orgunit'))
  targetName = getEmailAddress(returnUIDprefix='uid:')
  targetResource = f"groups/{convertEmailAddressToUID(targetName, cd, emailType='group')}"
  return (targetName, targetName, targetResource, Ent.GROUP, cp.customers().policies().groups())

def checkPolicyArgs(targetResource, printer_id, app_id):
  if not targetResource:
    missingArgumentExit('ou|org|orgunit|group')
  if printer_id and app_id:
    usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('printerid', 'appid'))

def setPolicyKVList(baseList, printer_id, app_id):
  kvList = baseList[:]
  if app_id:
    kvList.extend([Ent.APP_ID, app_id])
  elif printer_id:
    kvList.extend([Ent.PRINTER_ID, printer_id])
  return kvList

def updatePolicyRequests(body, targetResource, printer_id, app_id):
  for request in body['requests']:
    request.setdefault('policyTargetKey', {})
    request['policyTargetKey']['targetResource'] = targetResource
    if app_id or printer_id:
      request['policyTargetKey'].setdefault('additionalTargetKeys', {})
      if app_id:
        request['policyTargetKey']['additionalTargetKeys']['app_id'] = app_id
      elif printer_id:
        request['policyTargetKey']['additionalTargetKeys']['printer_id'] = printer_id

# gam delete chromepolicy
#	(<SchemaName> [<JSONData>])+
#	((ou|org|orgunit <OrgUnitItem>)|(group <GroupItem>))
#	[(printerid <PrinterID>)|(appid <AppID>)]
def doDeleteChromePolicy():
  cp = buildGAPIObject(API.CHROMEPOLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  customer = _getMain()._getCustomersCustomerIdWithC()
  app_id = groupEmail = orgUnit = printer_id = targetResource = None
  body = {'requests': []}
  schemaNameList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'ou', 'org', 'orgunit'}:
      orgUnit, targetName, targetResource, entityType, service = _getPolicyOrgUnitTarget(cd, cp, myarg, groupEmail)
      function = 'batchInherit'
    elif myarg == 'group':
      groupEmail, targetName, targetResource, entityType, service = _getPolicyGroupTarget(cd, cp, myarg, orgUnit)
      function = 'batchDelete'
    elif myarg == 'printerid':
      printer_id = getString(Cmd.OB_PRINTER_ID)
    elif myarg == 'appid':
      app_id = getString(Cmd.OB_APP_ID)
    else:
      schema = _getChromePolicySchema(cp, Cmd.Previous(), 'name')
      schemaName = schema['name'].split('/')[-1]
      schemaNameList.append(schemaName)
      body['requests'].append({'policySchema': schemaName})
      if checkArgumentPresent('json'):
        jsonData = getJSON(['direct', 'name', 'orgUnitPath', 'parentOrgUnitPath', 'group'])
        if 'additionalTargetKeys' in jsonData:
          body['requests'][-1].setdefault('policyTargetKey', {'additionalTargetKeys': {}})
          for atk in jsonData['additionalTargetKeys']:
            body['requests'][-1]['policyTargetKey']['additionalTargetKeys'][atk['name']] = atk['value']
  checkPolicyArgs(targetResource, printer_id, app_id)
  count = len(body['requests'])
  if count != 1:
    entityPerformActionNumItems([entityType, targetName], count, Ent.CHROME_POLICY)
    if count == 0:
      return
  kvList = setPolicyKVList([entityType, targetName, Ent.CHROME_POLICY, ','.join(schemaNameList)], printer_id, app_id)
  updatePolicyRequests(body, targetResource, printer_id, app_id)
  if orgUnit and app_id:
    for request in body['requests']:
      if request['policySchema'] == 'chrome.users.apps.InstallType':
        # Deleting an app must be done at the Organizational Unit at which the app was explicitly added for management.
        # When calling resolve, the field addedSourceKey contains the Organization Unit where it was added for management.
        # In other words, delete should only be called for apps where the Organizational Unit in addedSourceKey is equal to the one in policyTargetKey.
        # In order to delete an app (explicitly remove it from management) you should send a batchInherit request in which
        # the policySchema is the schema for the given app type, with an asterisk (*) in place of a specific policy.
        try:
          result = callGAPI(cp.customers().policies(), 'resolve', 'resolvedPolicies',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT,
                                          GAPI.SERVICE_NOT_AVAILABLE, GAPI.QUOTA_EXCEEDED],
                            customer=customer, body={'policySchemaFilter': request['policySchema'], 'policyTargetKey': request['policyTargetKey']})
          if result:
            policy = result['resolvedPolicies'][0]
            if request['policyTargetKey']['targetResource'] == policy['addedSourceKey'].get('targetResource', ''):
              request['policySchema'] = 'chrome.users.apps.*'
        except (GAPI.notFound, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable, GAPI.quotaExceeded):
          continue
  try:
    callGAPI(service, function,
             throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED,
                           GAPI.INVALID_ARGUMENT, GAPI.SERVICE_NOT_AVAILABLE, GAPI.QUOTA_EXCEEDED],
             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
             customer=customer, body=body)
    entityActionPerformed(kvList)
  except (GAPI.notFound, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable, GAPI.quotaExceeded) as e:
    entityActionFailedWarning(kvList, str(e))

CHROME_SCHEMA_SPECIAL_CASES = {
# duration
  'chrome.users.AutoUpdateCheckPeriodNewV2':
    {'autoupdatecheckperiodminutesnew':
       {'casedField': 'autoUpdateCheckPeriodMinutesNew',
        'type': 'duration', 'minVal': 1, 'maxVal': 720}},
  'chrome.users.BrowserSwitcherDelayDurationV2':
    {'browserswitcherdelayduration':
       {'casedField': 'browserSwitcherDelayDuration',
        'type': 'duration', 'minVal': 0, 'maxVal': 30}},
  'chrome.users.BrowsingDataLifetimeV2':
    {'browsinghistoryttl':
       {'casedField': 'browsingHistoryTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'downloadhistoryttl':
       {'casedField': 'downloadHistoryTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'cookiesandothersitedatattl':
       {'casedField': 'cookiesAndOtherSiteDataTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'cachedimagesandfilesttl':
       {'casedField': 'cachedImagesAndFilesTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'passwordsigninttl':
       {'casedField': 'passwordSigninTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'autofillttl':
       {'casedField': 'autofillTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'sitesettingsttl':
       {'casedField': 'siteSettingsTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'hostedappdatattl':
       {'casedField': 'hostedAppDataTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None}},
  'chrome.users.CloudReportingUploadFrequencyV2':
    {'cloudreportinguploadfrequency':
       {'casedField': 'cloudReportingUploadFrequency',
        'type': 'duration', 'minVal': 3, 'maxVal': 24}},
  'chrome.users.FetchKeepaliveDurationSecondsOnShutdownV2':
    {'fetchkeepalivedurationsecondsonshutdown':
       {'casedField': 'fetchKeepaliveDurationSecondsOnShutdown',
        'type': 'duration', 'minVal': 0, 'maxVal': 5}},
  'chrome.users.MaxInvalidationFetchDelayV2':
    {'maxinvalidationfetchdelay':
       {'casedField': 'maxInvalidationFetchDelay',
        'type': 'duration', 'minVal': 1, 'maxVal': 30, 'default': 10}},
  'chrome.users.PrintJobHistoryExpirationPeriodNewV2':
    {'printjobhistoryexpirationperioddaysnew':
       {'casedField': 'printJobHistoryExpirationPeriodDaysNew',
        'type': 'duration', 'minVal': -1, 'maxVal': None}},
  'chrome.users.RelaunchNotificationWithDurationV2':
    {'relaunchnotificationperiodduration':
       {'casedField': 'relaunchNotificationPeriodDuration',
        'type': 'duration', 'minVal': 1, 'maxVal': 168},
     'relaunchinitialquietperiodduration':
       {'casedField': 'relaunchInitialQuietPeriodDuration',
        'type': 'duration', 'minVal': 0, 'maxVal': None},
     'relaunchwindowstarttime':
       {'casedField': 'relaunchWindowStartTime',
        'type': 'timeOfDay'},
     'relaunchwindowdurationmin':
       {'casedField': 'relaunchWindowDurationMin',
        'type': 'duration', 'minVal': 1, 'maxVal': 1440}},
  'chrome.users.SecurityTokenSessionSettingsV2':
    {'securitytokensessionnotificationseconds':
       {'casedField': 'securityTokenSessionNotificationSeconds',
        'type': 'duration', 'minVal': 0, 'maxVal': 9999}},
  'chrome.users.SessionLengthV2':
    {'sessiondurationlimit':
       {'casedField': 'sessionDurationLimit',
        'type': 'duration', 'minVal': 1, 'maxVal': 1440}},
  'chrome.users.UpdatesSuppressed':
    {'updatessuppresseddurationmin':
       {'casedField': 'updatesSuppressedDurationMin',
        'type': 'count', 'minVal': 1, 'maxVal': 1440},
     'updatessuppressedstarttime':
       {'casedField': 'updatesSuppressedStartTime',
        'type': 'timeOfDay'}},
  'chrome.devices.EnableReportUploadFrequencyV2':
    {'reportdeviceuploadfrequency':
       {'casedField': 'reportDeviceUploadFrequency',
        'type': 'duration', 'minVal': 60, 'maxVal': 25379}},
  'chrome.devices.ScheduledRebootDurationV2':
    {'uptimelimitduration':
       {'casedField': 'uptimeLimitDuration',
        'type': 'duration', 'minVal': 1, 'maxVal': 365}},
  'chrome.devices.kiosk.AcPowerSettingsV2':
    {'acidletimeout':
       {'casedField': 'acIdleTimeout',
        'type': 'duration', 'minVal': 1, 'maxVal': 35000},
     'acwarningtimeout':
       {'casedField': 'acWarningTimeout',
        'type': 'duration', 'minVal': 0, 'maxVal': 35000},
     'acdimtimeout':
       {'casedField': 'acDimTimeout',
        'type': 'duration', 'minVal': 0, 'maxVal': 35000},
     'acscreenofftimeout':
       {'casedField': 'acScreenOffTimeout',
        'type': 'duration', 'minVal': 0, 'maxVal': 35000}},
  'chrome.devices.kiosk.BatteryPowerSettingsV2':
    {'batteryidletimeout':
       {'casedField': 'batteryIdleTimeout',
        'type': 'duration', 'minVal': 1, 'maxVal': 35000},
     'batterywarningtimeout':
       {'casedField': 'batteryWarningTimeout',
        'type': 'duration', 'minVal': 0, 'maxVal': 35000},
     'batterydimtimeout':
       {'casedField': 'batteryDimTimeout',
        'type': 'duration', 'minVal': 0, 'maxVal': 35000},
     'batteryscreenofftimeout':
       {'casedField': 'batteryScreenOffTimeout',
        'type': 'duration', 'minVal': 0, 'maxVal': 35000}},
  'chrome.devices.managedguest.BrowsingDataLifetimeV2':
    {'browsinghistoryttl':
       {'casedField': 'browsingHistoryTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'downloadhistoryttl':
       {'casedField': 'downloadHistoryTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'cookiesandothersitedatattl':
       {'casedField': 'cookiesAndOtherSiteDataTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'cachedimagesandfilesttl':
       {'casedField': 'cachedImagesAndFilesTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'passwordsigninttl':
       {'casedField': 'passwordSigninTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'autofillttl':
       {'casedField': 'autofillTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'sitesettingsttl':
       {'casedField': 'siteSettingsTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None},
     'hostedappdatattl':
       {'casedField': 'hostedAppDataTtl',
        'type': 'duration', 'minVal': 1, 'maxVal': None}},
  'chrome.devices.managedguest.MaxInvalidationFetchDelayV2':
    {'maxinvalidationfetchdelay':
       {'casedField': 'maxInvalidationFetchDelay',
        'type': 'duration', 'minVal': 1, 'maxVal': 30, 'default': 10}},
  'chrome.devices.managedguest.PrintJobHistoryExpirationPeriodNewV2':
    {'printjobhistoryexpirationperioddaysnew':
       {'casedField': 'printJobHistoryExpirationPeriodDaysNew',
        'type': 'duration', 'minVal': -1, 'maxVal': None}},
  'chrome.devices.managedguest.SecurityTokenSessionSettingsV2':
    {'securitytokensessionnotificationseconds':
       {'casedField': 'securityTokenSessionNotificationSeconds',
        'type': 'duration', 'minVal': 0, 'maxVal': 9999}},
  'chrome.devices.managedguest.SessionLengthV2':
    {'sessiondurationlimit':
       {'casedField': 'sessionDurationLimit',
        'type': 'duration', 'minVal': 1, 'maxVal': 1440}},
# value
  'chrome.users.GaiaLockScreenOfflineSigninTimeLimitDays':
    {'gaialockscreenofflinesignintimelimitdays':
       {'casedField': 'gaiaLockScreenOfflineSigninTimeLimitDays',
        'type': 'value', 'minVal': 0, 'maxVal': 365}},
  'chrome.users.GaiaOfflineSigninTimeLimitDays':
    {'gaiaofflinesignintimelimitdays':
       {'casedField': 'gaiaOfflineSigninTimeLimitDays',
        'type': 'value', 'minVal': 0, 'maxVal': 365}},
  'chrome.users.PrintingMaxSheetsAllowed':
    {'printingmaxsheetsallowednullable':
       {'casedField': 'printingMaxSheetsAllowedNullable',
        'type': 'value', 'minVal': 1, 'maxVal': None}},
  'chrome.users.RemoteAccessHostClipboardSizeBytes':
    {'remoteaccesshostclipboardsizebytes':
       {'casedField': 'remoteAccessHostClipboardSizeBytes',
        'type': 'value', 'minVal': 0, 'maxVal': 2147483647}},
  'chrome.users.SamlLockScreenOfflineSigninTimeLimitDays':
    {'samllockscreenofflinesignintimelimitdays':
       {'casedField': 'samlLockScreenOfflineSigninTimeLimitDays',
        'type': 'value', 'minVal': 0, 'maxVal': 365}},
  'chrome.devices.ExtensionCacheSize':
    {'extensioncachesize':
       {'casedField': 'extensionCacheSize',
        'type': 'value', 'minVal': 1048576, 'maxVal': None, 'default': 268435456}},
  'chrome.devices.managedguest.PrintingMaxSheetsAllowed':
    {'printingmaxsheetsallowednullable':
       {'casedField': 'printingMaxSheetsAllowedNullable',
        'type': 'value', 'minVal': 1, 'maxVal': None}},
  'chrome.devices.managedguest.RemoteAccessHostClipboardSizeBytes':
    {'remoteaccesshostclipboardsizebytes':
       {'casedField': 'remoteAccessHostClipboardSizeBytes',
        'type': 'value', 'minVal': 0, 'maxVal': 2147483647}},
# downloadUri
  'chrome.users.Avatar':
    {'useravatarimage':
       {'casedField': 'userAvatarImage',
        'type': 'downloadUri'}},
  'chrome.users.Wallpaper':
    {'wallpaperimage':
       {'casedField': 'wallpaperImage',
        'type': 'downloadUri'}},
  'chrome.devices.SignInWallpaperImage':
    {'devicewallpaperimage':
       {'casedField': 'deviceWallpaperImage',
        'type': 'downloadUri'}},
  'chrome.devices.managedguest.Avatar':
    {'useravatarimage':
       {'casedField': 'userAvatarImage',
        'type': 'downloadUri'}},
  'chrome.devices.managedguest.Wallpaper':
    {'wallpaperimage':
       {'casedField': 'wallpaperImage',
        'type': 'downloadUri'}},
  }

CHROME_TARGET_VERSION_CHANNEL_MINUS_PATTERN = re.compile(r'^([a-z]+)-(\d+)$')
CHROME_TARGET_VERSION_PATTERN = re.compile(r'^(\d{1,4}\.){1,4}$')

# gam update chromepolicy [convertcrnl]
#	(<SchemaName> ((<Field> <Value>)+ | <JSONData>))+
#	((ou|orgunit <OrgUnitItem>)|(group <GroupItem>))
#	[(printerid <PrinterID>)|(appid <AppID>)]
def doUpdateChromePolicy():
  def getSpecialVtypeValue(vtype, value):
    if vtype in {'duration', 'value', 'downloadUri'}:
      return {vtype: value}
    if vtype == 'count':
      return value
    #if vtype == timeOfDay:
    hours, minutes = value.split(':')
    return {vtype: {'hours': int(hours), 'minutes': int(minutes)}}

  cp = buildGAPIObject(API.CHROMEPOLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  cv = None
  customer = _getMain()._getCustomersCustomerIdWithC()
  app_id = channelMap = groupEmail = orgUnit = printer_id = targetResource = None
  body = {'requests': []}
  schemaNameList = []
  convertCRsNLs = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'ou', 'org', 'orgunit'}:
      orgUnit, targetName, targetResource, entityType, service = _getPolicyOrgUnitTarget(cd, cp, myarg, groupEmail)
    elif myarg == 'group':
      groupEmail, targetName, targetResource, entityType, service = _getPolicyGroupTarget(cd, cp, myarg, orgUnit)
    elif myarg == 'printerid':
      printer_id = getString(Cmd.OB_PRINTER_ID)
    elif myarg == 'appid':
      app_id = getString(Cmd.OB_APP_ID)
    elif myarg == 'convertcrnl':
      convertCRsNLs = True
    else:
      schemaName, schema = simplifyChromeSchemaUpdate(_getChromePolicySchema(cp, Cmd.Previous(), '*'))
      body['requests'].append({'policyValue': {'policySchema': schemaName, 'value': {}},
                               'updateMask': ''})
      schemaNameList.append(schemaName)
      while Cmd.ArgumentsRemaining():
        field = getArgumentEmptyAllowed()
        # Allow an empty field/value pair which makes processing an input CSV file with schemas with different numbers of fields easy
        if not field:
          if Cmd.ArgumentsRemaining():
            Cmd.Advance()
          continue
        if field in {'ou', 'org', 'orgunit', 'group', 'printerid', 'appid'} or '.' in field:
          if field != 'appid' or not schemaName.startswith('chrome.devices.kiosk'):
            Cmd.Backup()
            break # field is actually a new policy name or orgunit
        # JSON
        if field == 'json':
          jsonData = getJSON(['direct', 'name', 'orgUnitPath', 'parentOrgUnitPath', 'group'])
          schemaNameAppId = schemaName
          if 'additionalTargetKeys' in jsonData:
            body['requests'][-1].setdefault('policyTargetKey', {'additionalTargetKeys': {}})
            for atk in jsonData['additionalTargetKeys']:
              body['requests'][-1]['policyTargetKey']['additionalTargetKeys'][atk['name']] = atk['value']
              if atk['name'] == 'app_id':
                schemaNameAppId += f"({atk['value']})"
          schemaNameList[-1] = schemaNameAppId
          for field in jsonData.get('fields', []):
            casedField = field['name']
            lowerField = casedField.lower()
            # Handle fields with durations, values, counts and timeOfDay as special cases
            tmschema = CHROME_SCHEMA_SPECIAL_CASES.get(schemaName, {}).get(lowerField)
            if tmschema:
              body['requests'][-1]['policyValue']['value'][casedField] = getSpecialVtypeValue(tmschema['type'], field['value'])
              body['requests'][-1]['updateMask'] += f'{casedField},'
              continue
            vtype = schema['settings'].get(lowerField, {}).get('type')
            value = field['value']
            if vtype in ['TYPE_INT64', 'TYPE_INT32', 'TYPE_UINT64']:
              value = int(value)
            elif vtype == 'TYPE_BOOL':
              pass
            elif vtype == 'TYPE_ENUM':
              prefix = schema['settings'][lowerField]['enum_prefix']
              if not value.startswith(prefix):
                value = f"{prefix}{value}"
            elif vtype == 'TYPE_LIST':
              value = value.split(',') if value else []
            if myarg == 'chrome.users.chromebrowserupdates' and casedField == 'targetVersionPrefixSetting':
              mg = CHROME_TARGET_VERSION_CHANNEL_MINUS_PATTERN.match(value)
              if mg:
                channel = mg.group(1).lower().replace('_', '')
                if channelMap is None:
                  cv, channelMap = _getMain().getPlatformChannelMap(cv, Ent.CHROME_CHANNEL)
                if channel not in channelMap:
                  invalidChoiceExit(value, channelMap, True)
                cv, status, milestone = _getMain().getRelativeMilestone(cv, channelMap[channel], int(mg.group(2)))
                if not status:
                  Cmd.Backup()
                  invalidArgumentExit(f'{milestone} for {casedField}: {value}')
                value =  f'{milestone}.'
              elif value and not CHROME_TARGET_VERSION_PATTERN.match(value):
                Cmd.Backup()
                invalidArgumentExit(f'{Msg.CHROME_TARGET_VERSION_FORMAT} for {casedField}: {value}')
            body['requests'][-1]['policyValue']['value'][casedField] = value
            body['requests'][-1]['updateMask'] += f'{casedField},'
          break
        # Handle fields with durations, values, counts and timeOfDay as special cases
        tmschema = CHROME_SCHEMA_SPECIAL_CASES.get(schemaName, {}).get(field)
        if tmschema:
          casedField = tmschema['casedField']
          vtype = tmschema['type']
          if vtype == 'downloadUri':
            value = getString(Cmd.OB_STRING)
          elif vtype != 'timeOfDay':
            if 'default' not in tmschema:
              value = getInteger(minVal=tmschema['minVal'], maxVal=tmschema['maxVal'])
            else:
              value = getIntegerEmptyAllowed(minVal=tmschema['minVal'], maxVal=tmschema['maxVal'], default=tmschema['default'])
          else:
            value = getHHMM()
          body['requests'][-1]['policyValue']['value'][casedField] = getSpecialVtypeValue(vtype, value)
          body['requests'][-1]['updateMask'] += f'{casedField},'
          continue
        if field not in schema['settings']:
          Cmd.Backup()
          missingChoiceExit(schema['settings'])
        field_settings = schema['settings'][field]
        casedField = field_settings['name']
        vtype = field_settings['type']
        value = getString(Cmd.OB_STRING, minLen=0 if vtype in {'TYPE_STRING', 'TYPE_LIST'}  else 1)
        if vtype in ['TYPE_INT64', 'TYPE_INT32', 'TYPE_UINT64']:
          if not value.isnumeric():
            Cmd.Backup()
            invalidArgumentExit(integerLimits(None, None))
          value = int(value)
        elif vtype == 'TYPE_BOOL':
          value = value.lower()
          if value in TRUE_VALUES:
            value = True
          elif value in FALSE_VALUES:
            value = False
          else:
            invalidChoiceExit(value, TRUE_FALSE, True)
        elif vtype == 'TYPE_ENUM':
          value = value.upper()
          prefix = field_settings['enum_prefix']
          enum_values = field_settings['enums']
          if value in enum_values:
            value = f'{prefix}{value}'
          elif value.replace(prefix, '') in enum_values:
            pass
          else:
            invalidChoiceExit(value, enum_values, True)
        elif vtype == 'TYPE_LIST':
          value = value.split(',') if value else []
        elif vtype == 'TYPE_STRING' and convertCRsNLs:
          value = _getMain().un_getMain().escapeCRsNLs(value)
        if myarg == 'chrome.users.chromebrowserupdates' and casedField == 'targetVersionPrefixSetting':
          mg = CHROME_TARGET_VERSION_CHANNEL_MINUS_PATTERN.match(value)
          if mg:
            channel = mg.group(1).lower().replace('_', '')
            if channelMap is None:
              cv, channelMap = _getMain().getPlatformChannelMap(cv, Ent.CHROME_CHANNEL)
            if channel not in channelMap:
              invalidChoiceExit(value, channelMap, True)
            cv, status, milestone = _getMain().getRelativeMilestone(cv, channelMap[channel], int(mg.group(2)))
            if not status:
              Cmd.Backup()
              invalidArgumentExit(f'{milestone} for {casedField}: {value}')
            value = f'{milestone}.'
          elif value and not CHROME_TARGET_VERSION_PATTERN.match(value):
            Cmd.Backup()
            invalidArgumentExit(Msg.CHROME_TARGET_VERSION_FORMAT)
        if field_settings['namedType']:
          body['requests'][-1]['policyValue']['value'][casedField] = {field_settings['namedType']: value}
        else:
          body['requests'][-1]['policyValue']['value'][casedField] = value
        body['requests'][-1]['updateMask'] += f'{casedField},'
  checkPolicyArgs(targetResource, printer_id, app_id)
  count = len(body['requests'])
  if count > 0 and not body['requests'][-1]['updateMask']:
    body['requests'].pop()
  kvList = setPolicyKVList([entityType, targetName, Ent.CHROME_POLICY, ','.join(schemaNameList)], printer_id, app_id)
  if count != 1:
    entityPerformActionNumItems(kvList, count, Ent.CHROME_POLICY)
    if count == 0:
      return
  updatePolicyRequests(body, targetResource, printer_id, app_id)
  try:
    callGAPI(service, 'batchModify',
             throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT,
                           GAPI.SERVICE_NOT_AVAILABLE, GAPI.QUOTA_EXCEEDED],
             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
             customer=customer, body=body)
    entityActionPerformed(kvList)
  except (GAPI.notFound, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable, GAPI.quotaExceeded) as e:
    entityActionFailedWarning(kvList, str(e))

CHROME_POLICY_INDEXED_TITLES = ['fields']

CHROME_POLICY_SHOW_ALL = -1
CHROME_POLICY_SHOW_DIRECT = True
CHROME_POLICY_SHOW_INHERITED = False
CHROME_POLICY_SHOW_CHOICE_MAP = {
  'all': CHROME_POLICY_SHOW_ALL,
  'direct': CHROME_POLICY_SHOW_DIRECT,
  'inherited': CHROME_POLICY_SHOW_INHERITED
  }

# gam show chromepolicies
#	((ou|orgunit <OrgUnitItem>)|(group <GroupItem>))
#	[(printerid <PrinterID>)|(appid <AppID>)]
#	(filter <StringList>)* (namespace <NamespaceList>)*
#	[show all|direct|inherited]
#	[formatjson]
# gam print chromepolicies [todrive <ToDriveAttribute>*]
#	((ou|orgunit <OrgUnitItem>)|(group <GroupItem>))
#	[(printerid <PrinterID>)|(appid <AppID>)]
#	(filter <StringList>)* (namespace <NamespaceList>)*
#	[show all|direct|inherited] [shownopolicy]
#	[[formatjson [quotechar <Character>]]
def doPrintShowChromePolicies():
  def normalizedPolicy(policy):
    norm = {'name': policy['value']['policySchema']}
    if app_id:
      norm['appId'] = app_id
    elif printer_id:
      norm['printerId'] = printer_id
    if entityType == Ent.ORGANIZATIONAL_UNIT:
      orgUnitId = policy.get('targetKey', {}).get('targetResource')
      norm['orgUnitPath'] = convertOrgUnitIDtoPath(cd, orgUnitId) if orgUnitId else UNKNOWN
      parentOrgUnitId = policy.get('sourceKey', {}).get('targetResource')
      norm['parentOrgUnitPath'] = convertOrgUnitIDtoPath(cd, parentOrgUnitId) if parentOrgUnitId else UNKNOWN
      norm['direct'] = orgUnitId == parentOrgUnitId
    else:
      groupId = policy.get('targetKey', {}).get('targetResource')
      if groupId is not None:
        groupId = groupId.split('/')[1]
        norm['group'] = getGroupEmailFromID(groupId, cd)
        if norm['group'] is None:
          norm['group'] = groupId
      else:
        norm['group'] = UNKNOWN
    norm['additionalTargetKeys'] = []
    for setting, value in sorted(policy.get('targetKey', {}).get('additionalTargetKeys', {}).items()):
      norm['additionalTargetKeys'].append({'name': setting, 'value': value})
    norm['fields'] = []
    name = policy['value']['policySchema']
    values = policy.get('value', {}).get('value', {})
    if name in {'chrome.devices.managedguest.apps.ManagedConfiguration',
                'chrome.devices.kiosk.apps.ManagedConfiguration',
                'chrome.users.apps.ManagedConfiguration'} and 'managedConfiguration' in values:
      values['managedConfiguration'] = json.dumps(values['managedConfiguration'], ensure_ascii=False).replace('\\n', '').replace('\\"', '"')[1:-1]
    for setting, value in values.items():
      # Handle fields with durations, values, counts and timeOfDay as special cases
      schema = CHROME_SCHEMA_SPECIAL_CASES.get(name, {}).get(setting.lower())
      if schema and setting == schema['casedField']:
        vtype = schema['type']
        if vtype in {'duration', 'value', 'downloadUri'}:
          value = value.get(vtype, '')
        elif vtype == 'count':
          pass
        else: #timeOfDay
          hours = value.get(vtype, {}).get('hours', 0)
          minutes = value.get(vtype, {}).get('minutes', 0)
          value = f'{hours:02}:{minutes:02}'
      elif isinstance(value, str) and value.find('_ENUM_') != -1:
        value = value.split('_ENUM_')[-1]
      elif isinstance(value, list):
        if len(value) > 0:
          if not isinstance(value[0], dict):
            value = ','.join(value)
          else:
            value = json.dumps(value, ensure_ascii=False)
        else:
          value = ''
      norm['fields'].append({'name': setting, 'value': value})
    return norm

  def _showPolicy(policy, j, jcount):
    policy = normalizedPolicy(policy)
    if (entityType == Ent.GROUP) or showPolicies in (CHROME_POLICY_SHOW_ALL, policy['direct']):
      if FJQC.formatJSON:
        printLine(json.dumps(cleanJSON(policy), ensure_ascii=False, sort_keys=True))
        return
      printKeyValueListWithCount([policy['name']], j, jcount)
      Ind.Increment()
      showJSON(None, policy, sortDictKeys=False)
      Ind.Decrement()

  def _printPolicyRow(policy):
    row = flattenJSON(policy)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(row):
      if entityType == Ent.ORGANIZATIONAL_UNIT:
        csvPF.WriteRowNoFilter({'name': policy['name'],
                                'orgUnitPath': policy['orgUnitPath'],
                                'parentOrgUnitPath': policy['parentOrgUnitPath'],
                                'direct': policy['direct'],
                                'JSON': json.dumps(cleanJSON(policy),
                                                   ensure_ascii=False, sort_keys=True)})
      else:
        csvPF.WriteRowNoFilter({'name': policy['name'],
                                'group': policy['group'],
                                'JSON': json.dumps(cleanJSON(policy),
                                                   ensure_ascii=False, sort_keys=True)})


  def _printPolicy(policy):
    nonlocal policiesShown
    policy = normalizedPolicy(policy)
    if (entityType == Ent.GROUP) or showPolicies in (CHROME_POLICY_SHOW_ALL, policy['direct']):
      policiesShown += 1
      _printPolicyRow(policy)

  def _printNoPolicy():
    nonlocal targetName
    policy = {'name': 'noPolicy'}
    if app_id:
      policy['appId'] = app_id
    elif printer_id:
      policy['printerId'] = printer_id
    if entityType == Ent.ORGANIZATIONAL_UNIT:
      policy['orgUnitPath'] = targetName
      if targetName == '/':
        policy['parentOrgUnitPath'] = '/'
      else:
        targetName = makeOrgUnitPathRelative(targetName)
        policy['parentOrgUnitPath'] = callGAPI(cd.orgunits(), 'get',
                                               throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                                               customerId=GC.Values[GC.CUSTOMER_ID],
                                               orgUnitPath=encodeOrgUnitPath(targetName),
                                               fields='parentOrgUnitPath')['parentOrgUnitPath']
      policy['direct'] = False
    else:
      policy['group'] = targetName
    _printPolicyRow(policy)

  cp = buildGAPIObject(API.CHROMEPOLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  customer = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['name'], indexedTitles=CHROME_POLICY_INDEXED_TITLES) if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  FJQC = FormatJSONQuoteChar(csvPF)
  app_id = groupEmail = orgUnit = printer_id = targetResource = None
  showPolicies = CHROME_POLICY_SHOW_ALL
  psFilters = []
  showNoPolicy = False
  policiesShown = 0
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'ou', 'org', 'orgunit'}:
      orgUnit, targetName, targetResource, entityType, _ = _getPolicyOrgUnitTarget(cd, cp, myarg, groupEmail)
    elif myarg == 'group':
      groupEmail, targetName, targetResource, entityType, _ = _getPolicyGroupTarget(cd, cp, myarg, orgUnit)
    elif myarg == 'printerid':
      printer_id = getString(Cmd.OB_PRINTER_ID)
    elif myarg == 'appid':
      app_id = getString(Cmd.OB_APP_ID)
    elif myarg == 'filter':
      for psFilter in getString(Cmd.OB_STRING).replace(',', ' ').split():
        psFilters.append(psFilter)
    elif myarg == 'namespace':
      for psFilter in getString(Cmd.OB_STRING).replace(',', ' ').split():
        if psFilter.endswith('.*'):
          psFilters.append(psFilter)
        else:
          psFilters.append(f'{psFilter}.*')
    elif myarg == 'show':
      showPolicies = getChoice(CHROME_POLICY_SHOW_CHOICE_MAP, mapChoice=True)
    elif csvPF and myarg == 'shownopolicy':
      showNoPolicy = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  checkPolicyArgs(targetResource, printer_id, app_id)
  body = {'policyTargetKey': {'targetResource': targetResource}}
  if app_id:
    body['policyTargetKey']['additionalTargetKeys'] = {'app_id': app_id}
    if not psFilters:
      psFilters = ['chrome.users.apps.*',
                   'chrome.devices.kiosk.apps.*',
                   'chrome.devices.managedguest.apps.*',
                    ]
  elif printer_id:
    body['policyTargetKey']['additionalTargetKeys'] = {'printer_id': printer_id}
    if not psFilters:
      psFilters = ['chrome.printers.*']
  elif not psFilters:
    if entityType == Ent.ORGANIZATIONAL_UNIT:
      psFilters = ['chrome.users.*',
                   'chrome.users.apps.*',
                   'chrome.users.appsconfig.*',
                   'chrome.devices.*',
                   'chrome.devices.kiosk.*',
                   'chrome.devices.kiosk.apps.*',
                   'chrome.devices.managedguest.*',
                   'chrome.devices.managedguest.apps.*',
                   'chrome.networks.cellular.*',
                   'chrome.networks.certificates.*',
                   'chrome.networks.ethernet.*',
                   'chrome.networks.globalsettings.*',
                   'chrome.networks.vpn.*',
                   'chrome.networks.wifi.*',
                   'chrome.printers.*',
                   'chrome.printservers.*',
                   ]
    else:
      psFilters = ['chrome.users.*',
                   'chrome.users.apps.*',
                   'chrome.users.appsconfig.*',
                   'chrome.printers.*',
                   'chrome.printservers.*',
                   ]
  if csvPF:
    if entityType == Ent.ORGANIZATIONAL_UNIT:
      csvPF.AddTitles(['orgUnitPath', 'parentOrgUnitPath', 'direct'])
    else:
      csvPF.AddTitles(['group'])
    csvPF.SetSortAllTitles()
    if not FJQC.formatJSON:
      if app_id:
        csvPF.AddSortTitles(['appId'])
      elif printer_id:
        csvPF.AddSortTitles(['printerId'])
    else:
      csvPF.SetJSONTitles(csvPF.titlesList+['JSON'])
  policies = []
  for psFilter in psFilters:
    body['policySchemaFilter'] = psFilter
    body['pageToken'] = None
    printGettingAllEntityItemsForWhom(Ent.CHROME_POLICY, targetName, query=body['policySchemaFilter'])
    try:
      policies.extend(callGAPIpages(cp.customers().policies(), 'resolve', 'resolvedPolicies',
                                    pageMessage=getPageMessageForWhom(),
                                    throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT,
                                                  GAPI.SERVICE_NOT_AVAILABLE, GAPI.QUOTA_EXCEEDED],
                                    customer=customer, body=body, pageArgsInBody=True))
    except (GAPI.notFound, GAPI.permissionDenied, GAPI.quotaExceeded) as e:
      entityActionFailedWarning([entityType, targetName], str(e))
      continue
    except (GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.CHROME_POLICY, body['policySchemaFilter']], str(e))
      continue
    # sort policies first by app/printer id then by schema name
    policies = sorted(policies,
                      key=lambda k: (list(k.get('targetKey', {}).get('additionalTargetKeys', {}).values()),
                                     k.get('value', {}).get('policySchema', '')))
  if not csvPF:
    jcount = len(policies)
    if not FJQC.formatJSON:
      kvList = setPolicyKVList([entityType, targetName], printer_id, app_id)
      entityPerformActionModifierNumItems(kvList, Msg.MAXIMUM_OF, jcount, Ent.CHROME_POLICY)
    Ind.Increment()
    j = 0
    for policy in policies:
      j += 1
      _getMain()._showPolicy(policy, j, jcount)
    Ind.Decrement()
  else:
    for policy in policies:
      _printPolicy(policy)
    if showNoPolicy and policiesShown == 0:
      _printNoPolicy()
    csvPF.writeCSVfile(f'Chrome Policies - {targetName}')

CHROME_IMAGE_SCHEMAS_MAP = {
  'chrome.devices.managedguest.avatar': {'name': 'chrome.devices.managedguest.Avatar', 'field': 'userAvatarImage'},
  'chrome.devices.managedguest.wallpaper': {'name': 'chrome.devices.managedguest.Wallpaper', 'field': 'wallpaperImage'},
  'chrome.devices.signinwallpaperimage': {'name': 'chrome.devices.SignInWallpaperImage', 'field': 'deviceWallpaperImage'},
  'chrome.users.avatar': {'name': 'chrome.users.Avatar', 'field': 'userAvatarImage'},
  'chrome.users.wallpaper': {'name': 'chrome.users.Wallpaper', 'field': 'wallpaperImage'},
  }

# gam create chromepolicyimage <ChromePolicyImageSchemaName> <FileName>
def doCreateChromePolicyImage():
  cp = buildGAPIObject(API.CHROMEPOLICY)
  parent = _getMain()._getCustomersCustomerIdWithC()
  schema = getChoice(CHROME_IMAGE_SCHEMAS_MAP, mapChoice=True)
  parameters = {_getMain().DFA_URL: None}
  parameters[DFA_LOCALFILEPATH] = setFilePath(getString(Cmd.OB_FILE_NAME), GC.INPUT_DIR)
  try:
    f = open(parameters[DFA_LOCALFILEPATH], 'rb')
    f.close()
  except IOError as e:
    Cmd.Backup()
    usageErrorExit(f'{parameters[DFA_LOCALFILEPATH]}: {str(e)}')
  parameters[DFA_LOCALFILENAME] = os.path.basename(parameters[DFA_LOCALFILEPATH])
  parameters[DFA_LOCALMIMETYPE] = mimetypes.guess_type(parameters[DFA_LOCALFILEPATH])[0]
  if parameters[DFA_LOCALMIMETYPE] is None:
    parameters[DFA_LOCALMIMETYPE] = 'image/jpeg'
  checkForExtraneousArguments()
  media_body = _getMain().getMediaBody(parameters)
  try:
    result = callGAPI(cp.media(), 'upload',
                      throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN],
                      customer=parent, media_body=media_body,
                      body={'policyField': f"{schema['name']}.{schema['field']}"})
    entityActionPerformed([Ent.CHROME_POLICY_IMAGE, f"{schema['name']} {schema['field']} {result['downloadUri']}"])
  except (GAPI.invalidArgument, GAPI.forbidden) as e:
    entityActionFailedWarning([Ent.CHROME_POLICY_IMAGE, f"{schema['name']}", Ent.FILE, f"{parameters[DFA_LOCALFILEPATH]}"], str(e))

def _showChromePolicySchema(schema, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(schema), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_POLICY_SCHEMA, schema['name']], i, count)
  Ind.Increment()
  showJSON(None, schema,
           dictObjectsKey={'messageType': 'name', 'field': 'name',
                           'fieldDescriptions': 'field', 'knownValueDescriptions': 'value'})
  Ind.Decrement()

CHROME_POLICY_SCHEMA_FIELDS_CHOICE_MAP = {
  'accessrestrictions': 'accessRestrictions',
  'additionaltargetkeynames': 'additionalTargetKeyNames',
  'categorytitle': 'categoryTitle',
  'definition': 'definition',
  'fielddescriptions': 'fieldDescriptions',
  'name': 'name',
  'notices': 'notices',
  'policyapilifecycle': 'policyApiLifecycle',
  'policydescription': 'policyDescription',
  'schemaname': 'schemaName',
  'supporturi': 'supportUri',
  'validtargetresources': 'validTargetResources',
  }

# gam info chromeschema <SchemaName>
#	<ChromePolicySchemaFieldName>* [fields <ChromePolicySchemaFieldNameList>]
#	[formatjson]
def doInfoChromePolicySchemas():
  cp = buildGAPIObject(API.CHROMEPOLICY)
  if checkArgumentPresent('std'):
    doInfoChromePolicySchemasStd(cp)
    return
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  name = _getChromePolicySchemaName()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getFieldsList(myarg, CHROME_POLICY_SCHEMA_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    schema = callGAPI(cp.customers().policySchemas(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                      name=name, fields=fields)
    _showChromePolicySchema(schema, FJQC, 0, 0)
  except GAPI.notFound:
    entityUnknownWarning(Ent.CHROME_POLICY_SCHEMA, name)
  except (GAPI.badRequest, GAPI.forbidden):
    accessErrorExit(None)

# gam show chromeschemas
#	[filter <String>]
#	<ChromePolicySchemaFieldName>* [fields <ChromePolicySchemaFieldNameList>]
#	[formatjson]
# gam print chromschemas [todrive <ToDriveAttribute>*]
#	[filter <String>]
#	<ChromePolicySchemaFieldName>* [fields <ChromePolicySchemaFieldNameList>]
#	[[formatjson [quotechar <Character>]]
def doPrintShowChromePolicySchemas():
  def _printChromePolicySchema(schema):
    row = flattenJSON(schema)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif (not csvPF.rowFilter and not csvPF.rowDropFilter) or csvPF.CheckRowTitles(row):
      row = {'name': schema['name']}
      if 'policyDescription' in schema:
        row['policyDescription'] = schema['policyDescription']
      if 'policyApiLifecycle' in schema:
        row['policyApiLifecycleStage'] = schema['policyApiLifecycle'].get('policyApiLifecycleStage', '')
      row['JSON'] = json.dumps(cleanJSON(schema), ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  cp = buildGAPIObject(API.CHROMEPOLICY)
  if checkArgumentPresent('std'):
    if not Act.csvFormat():
      doShowChromePolicySchemasStd(cp)
      return
    unknownArgumentExit()
  parent = _getMain()._getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['name', 'schemaName', 'policyDescription',
                        'policyApiLifecycle.policyApiLifecycleStage',
                        'policyApiLifecycle.description',
                        'policyApiLifecycle.endSupport.year',
                        'policyApiLifecycle.endSupport.month',
                        'policyApiLifecycle.endSupport.day',
                        'policyApiLifecycle.deprecatedInFavorOf',
                        'policyApiLifecycle.deprecatedInFavorOf.0'],
                        'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      pfilter = getString(Cmd.OB_STRING)
    elif getFieldsList(myarg, CHROME_POLICY_SCHEMA_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and FJQC.formatJSON:
    jsonTitles = ['name']
    if not fieldsList or 'policyDescription' in fieldsList:
      jsonTitles.append('policyDescription')
    if not fieldsList or 'policyApiLifecycle' in fieldsList:
      jsonTitles.append('policyApiLifecycleStage')
    jsonTitles.append('JSON')
    csvPF.SetJSONTitles(jsonTitles)
  fields = getItemFieldsFromFieldsList('policySchemas', fieldsList)
  printGettingAllAccountEntities(Ent.CHROME_POLICY_SCHEMA, pfilter)
  pageMessage = getPageMessage()
  try:
    schemas = callGAPIpages(cp.customers().policySchemas(), 'list', 'policySchemas',
                            pageMessage=pageMessage,
                            throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                            parent=parent, filter=pfilter, fields=fields)
    if not csvPF:
      jcount = len(schemas)
      if not FJQC.formatJSON:
        performActionNumItems(jcount, Ent.CHROME_POLICY_SCHEMA)
      Ind.Increment()
      j = 0
      for schema in schemas:
        j += 1
        _showChromePolicySchema(schema, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for schema in schemas:
        _printChromePolicySchema(schema)
  except GAPI.invalidInput as e:
    entityActionFailedWarning([Ent.CHROME_POLICY, None], invalidQuery(pfilter) if pfilter else str(e))
  except (GAPI.badRequest, GAPI.forbidden):
    accessErrorExit(None)
  if csvPF:
    csvPF.writeCSVfile('Chrome Policy Schemas')

def _showChromePolicySchemaStd(schema):
  def _printEntry(mtypeName, mtypeEntry):
    vtype = mtypeEntry['type']
    if vtype != 'TYPE_MESSAGE':
      printKeyValueList([f'{mtypeName}', f'{vtype}'])
    else:
      printKeyValueList([f'{mtypeName}'])
    Ind.Increment()
    if vtype == 'TYPE_ENUM':
      enums = mtypeEntry['subtype']['enums']
      descriptions = mtypeEntry['descriptions']
      for i, v in enumerate(enums):
        printKeyValueList([f'{v}', f'{descriptions[i]}'])
    elif vtype == 'TYPE_MESSAGE':
      for mfieldName, mfield in mtypeEntry['subtype']['field'].items():
        # managedBookmarks is recursive
        if mtypeName != 'entries':
          _printEntry(mfieldName, mfield)
    else:
      for description in mtypeEntry.get('descriptions', []):
        printKeyValueList([description])
    Ind.Decrement()

  printKeyValueList([f'{schema.get("name")}', f'{schema.get("description")}'])
  Ind.Increment()
  for mtypeEntry in schema['settings'].values():
    if mtypeEntry['subfield']:
      continue
    for mfieldName, mfield in mtypeEntry['field'].items():
      _printEntry(mfieldName, mfield)
  Ind.Decrement()

# gam info chromeschema std <SchemaName>
def doInfoChromePolicySchemasStd(cp):
  name = _getChromePolicySchemaName()
  checkForExtraneousArguments()
  try:
    schema = callGAPI(cp.customers().policySchemas(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.FORBIDDEN],
                      name=name)
    _, schema_dict = simplifyChromeSchemaDisplay(schema)
    _showChromePolicySchemaStd(schema_dict)
  except GAPI.notFound:
    entityUnknownWarning(Ent.CHROME_POLICY_SCHEMA, name)
  except (GAPI.badRequest, GAPI.forbidden):
    accessErrorExit(None)

# gam show chromeschemas std [filter <String>]
def doShowChromePolicySchemasStd(cp):
  sfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'filter':
      sfilter = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  parent = _getMain()._getCustomersCustomerIdWithC()
  result = callGAPIpages(cp.customers().policySchemas(), 'list', 'policySchemas',
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                         parent=parent, filter=sfilter)
  schemas = {}
  for schema in result:
    schema_name, schema_dict = simplifyChromeSchemaDisplay(schema)
    schemas[schema_name.lower()] = schema_dict
  for _, schema in sorted(schemas.items()):
    _showChromePolicySchemaStd(schema)
    printBlankLine()

# gam create chromenetwork
#	<OrgUnitItem> <String> <JSONData>
def doCreateChromeNetwork():
  cp = buildGAPIObject(API.CHROMEPOLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  customer = _getMain()._getCustomersCustomerIdWithC()
  body = {}
  orgUnitPath, body['targetResource'] = _getOrgunitsOrgUnitIdPath(cd, getString(Cmd.OB_ORGUNIT_PATH))
  body['name'] = getString(Cmd.OB_STRING)
  body.update(getJSON(['direct', 'name', 'orgUnitPath', 'parentOrgUnitPath', 'group']))
  checkForExtraneousArguments()
  kvList = [Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CHROME_NETWORK_NAME, body['name']]
  try:
    result = callGAPI(cp.customers().policies().networks(), 'defineNetwork',
                      bailOnInternalError=True,
                      throwReasons=[GAPI.ALREADY_EXISTS, GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT,
                                    GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      customer=customer, body=body)
    entityActionPerformed(kvList+[Ent.CHROME_NETWORK_ID, result['networkId']])
  except (GAPI.alreadyExists, GAPI.permissionDenied, GAPI.invalidArgument,
          GAPI.internalError, GAPI.serviceNotAvailable) as e:
    entityActionFailedWarning(kvList, str(e))

# gam delete chromenetwork
#	 <OrgUnitItem> <NetworkID>
def doDeleteChromeNetwork():
  cp = buildGAPIObject(API.CHROMEPOLICY)
  cd = buildGAPIObject(API.DIRECTORY)
  customer = _getMain()._getCustomersCustomerIdWithC()
  body = {}
  orgUnitPath, body['targetResource'] = _getOrgunitsOrgUnitIdPath(cd, getString(Cmd.OB_ORGUNIT_PATH))
  body['networkId'] = getString(Cmd.OB_NETWORK_ID)
  checkForExtraneousArguments()
  kvList = [Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CHROME_NETWORK_ID, body['networkId']]
  try:
    callGAPI(cp.customers().policies().networks(), 'removeNetwork',
             throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED,
                           GAPI.INVALID_ARGUMENT, GAPI.SERVICE_NOT_AVAILABLE],
             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
             customer=customer, body=body)
    entityActionPerformed(kvList)
  except (GAPI.notFound, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
    entityActionFailedWarning(kvList, str(e))

# Device command utilities
