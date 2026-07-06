"""GAM Chrome browser profile management."""

import json

from gamlib import api as API
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages, yieldGAPIpages
from gam.util.args import (
    OrderBy,
    checkForExtraneousArguments,
    getArgument,
    getBoolean,
    getString,
    getTimeOrDeltaFromNow,
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
    getPageMessage,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printGettingEntityItemForWhom,
    printLine,
)
from gam.util.customer import _getCustomerId
from gam.util.entity import getEntityList
from gam.util.errors import entityActionFailedExit


def _getChromeProfileName():
  profileName = getString(Cmd.OB_CHROMEPROFILE_NAME)
  if not profileName.startswith('customers'):
    customerId = _getCustomerId()
    profileName = f'customers/{customerId}/profiles/{profileName}'
  return profileName

# gam delete chromeprofile <ChromeProfileName>
def doDeleteChromeProfile():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  profileName = _getChromeProfileName()
  checkForExtraneousArguments()
  try:
    callGAPI(cm.customers().profiles(), 'delete',
             throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
             name=profileName)
    entityActionPerformed([Ent.CHROME_PROFILE, profileName])
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))

CHROMEPROFILE_TIME_OBJECTS = {
  'firstEnrollmentTime',
  'lastActivityTime',
  'lastPolicyFetchTime',
  'lastPolicySyncTime',
  'lastStatusReportTime',
  }

def _showChromeProfile(profile, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS),
              ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_PROFILE, profile['name']], i, count)
  Ind.Increment()
  showJSON(None, profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS)
  Ind.Decrement()

CHROMEPROFILE_FIELDS_CHOICE_MAP = {
  'affiliationstate': 'affiliationState',
  'annotatedlocation': 'annotatedLocation',
  'annotateduser': 'annotatedUser',
  'attestationcredential': 'attestationCredential',
  'browserchannel': 'browserChannel',
  'browserversion': 'browserVersion',
  'deviceinfo': 'deviceInfo',
  'displayname': 'displayName',
  'extensioncount': 'extensionCount',
  'firstenrollmenttime': 'firstEnrollmentTime',
  'identityprovider':'identityProvider',
  'lastactivitytime': 'lastActivityTime',
  'lastpolicyfetchtime': 'lastPolicyFetchTime',
  'lastpolicysynctime': 'lastPolicySyncTime',
  'laststatusreporttime': 'lastStatusReportTime',
  'name': 'name',
  'osplatformtype': 'osPlatformType',
  'osplatformversion':'osPlatformVersion',
  'osversion': 'osVersion',
  'policycount': 'policyCount',
  'profileid': 'profileId',
  'profilepermanentid': 'profilePermanentId',
  'reportingdata': 'reportingData',
  'useremail': 'userEmail',
  'userid': 'userId',
   }

# gam info chromeprofile <ChromeProfileName>
#	<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
#	[formatjson]
def doInfoChromeProfile():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  profileName = _getChromeProfileName()
  fieldsList = []
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getFieldsList(myarg, CHROMEPROFILE_FIELDS_CHOICE_MAP, fieldsList, initialField='name'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    profile = callGAPI(cm.customers().profiles(), 'get',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                       name=profileName, fields=fields)
    _showChromeProfile(profile, FJQC)
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))

CHROMEPROFILE_ORDERBY_CHOICE_MAP = {
  'affiliationstate': 'affiliationState',
  'browserchannel': 'browserChannel',
  'browserversion': 'browserVersion',
  'displayname': 'displayName',
  'extensioncount': 'extensionCount',
  'firstenrollmenttime': 'firstEnrollmentTime',
  'identityprovider': 'identityProvider',
  'lastactivitytime': 'lastActivityTime',
  'lastpolicysynctime': 'lastPolicySyncTime',
  'laststatusreporttime': 'lastStatusReportTime',
  'osplatformtype': 'osPlatformType',
  'osversion': 'osVersion',
  'policycount': 'policyCount',
  'profileid': 'profileId',
  'useremail': 'userEmail',
  }

# gam show chromeprofiles
#	[filter <String> (filtertime<String> <Time>)*]
#	[orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
#	<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
#	[formatjson]
# gam print chromeprofiles [todrive <ToDriveAttribute>*]
#	[filter <String> (filtertime<String> <Time>)*]
#	[orderby <ChromeProfileOrderByFieldName> [ascending|descending]]
#	<ChromeProfileFieldName>* [fields <ChromeProfileFieldNameList>]
#	[formatjson [quotechar <Character>]]
def doPrintShowChromeProfiles():
  def _printProfile(profile):
    row = flattenJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'name': profile['name'], 'profileId': profile['profileId'],
                              'JSON': json.dumps(cleanJSON(profile, timeObjects=CHROMEPROFILE_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  csvPF = CSVPrintFile(['name', 'profileId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  OBY = OrderBy(CHROMEPROFILE_ORDERBY_CHOICE_MAP)
  sortHeaders = False
  fieldsList = []
  cbfilter = None
  filterTimes = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getFieldsList(myarg, CHROMEPROFILE_FIELDS_CHOICE_MAP, fieldsList, initialField=['name', 'profileId']):
      pass
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg.startswith('filtertime'):
      filterTimes[myarg] = getTimeOrDeltaFromNow()
    elif myarg in {'filter', 'filters'}:
      cbfilter = getString(Cmd.OB_STRING)
    elif myarg == 'sortheaders':
      sortHeaders = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if filterTimes and cbfilter is not None:
    for filterTimeName, filterTimeValue in filterTimes.items():
      cbfilter = cbfilter.replace(f'#{filterTimeName}#', filterTimeValue)
  fields = getItemFieldsFromFieldsList('chromeBrowserProfiles', fieldsList)
  customerId = _getCustomerId()
  parent = f'customers/{customerId}'
  printGettingAllAccountEntities(Ent.CHROME_PROFILE, cbfilter)
  pageMessage = getPageMessage()
  try:
    feed = yieldGAPIpages(cm.customers().profiles(), 'list', 'chromeBrowserProfiles',
                          pageMessage=pageMessage,
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          parent=parent, pageSize=200,
                          filter=cbfilter, orderBy=OBY.orderBy, fields=fields)
    for profiles in feed:
      if not csvPF:
        jcount = len(profiles)
        if not FJQC.formatJSON:
          performActionNumItems(jcount, Ent.CHROME_PROFILE)
        Ind.Increment()
        j = 0
        for profile in profiles:
          j += 1
          _showChromeProfile(profile, FJQC, j, jcount)
        Ind.Decrement()
      else:
        for profile in profiles:
          _printProfile(profile)
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, cbfilter], str(e))
  if csvPF:
    if sortHeaders:
      csvPF.SetSortTitles(['name', 'profileId'])
    csvPF.writeCSVfile('Chrome Profiles')

def _getChromeProfileNameList():
  if not Cmd.PeekArgumentPresent(['select', 'commands', 'filter', 'filters']):
    return getString(Cmd.OB_CHROMEPROFILE_NAME_LIST).replace(',', ' ').split()
  return []

def _initChromeProfileNameParameters():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  return (cm, {'profileNameList': _getChromeProfileNameList(),
               'commandNameList': [],
               'customerId': _getCustomerId(),
               'cbfilter': None, 'filterTimes': {},
               'OBY': OrderBy(CHROMEPROFILE_ORDERBY_CHOICE_MAP)})

def _getChromeProfileNameParameters(myarg, parameters):
  if not parameters['cbfilter'] and not parameters['commandNameList'] and myarg == 'select':
    parameters['profileNameList'].extend(getEntityList(Cmd.OB_CHROMEPROFILE_NAME_LIST))
  elif not parameters['cbfilter'] and not parameters['profileNameList'] and myarg == 'commands':
    parameters['commandNameList'].extend(getEntityList(Cmd.OB_CHROMEPROFILE_COMMAND_NAME_LIST))
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg == 'orderby':
    parameters['OBY'].GetChoice()
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg.startswith('filtertime'):
    parameters['filterTimes'][myarg] = getTimeOrDeltaFromNow()
  elif not parameters['profileNameList'] and not parameters['commandNameList'] and myarg in {'filter', 'filters'}:
    parameters['cbfilter'] = getString(Cmd.OB_STRING)
  else:
    return False
  return True

def _getChromeProfileNameEntityForCommand(cm, parameters):
  if parameters['cbfilter'] is None:
    customerId = parameters['customerId']
    if parameters['profileNameList']:
      for i, profileName in enumerate(parameters['profileNameList']):
        if not profileName.startswith('customers'):
          parameters['profileNameList'][i] = f'customers/{customerId}/profiles/{profileName}'
    elif parameters['commandNameList']:
      for i, commandName in enumerate(parameters['commandNameList']):
        if not commandName.startswith('customers'):
          parameters['commandNameList'][i] = f'customers/{customerId}/profiles/{commandName}'
    return
  if parameters['filterTimes']:
    for filterTimeName, filterTimeValue in parameters['filterTimes'].items():
      parameters['cbfilter'] = parameters['cbfilter'].replace(f'#{filterTimeName}#', filterTimeValue)
  printGettingAllAccountEntities(Ent.CHROME_PROFILE, parameters['cbfilter'])
  pageMessage = getPageMessage()
  try:
    feed = yieldGAPIpages(cm.customers().profiles(), 'list', 'chromeBrowserProfiles',
                          pageMessage=pageMessage,
                          throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          parent=f'customers/{parameters["customerId"]}', pageSize=200,
                          filter=parameters['cbfilter'], orderBy=parameters['OBY'].orderBy,
                          fields='nextPageToken,chromeBrowserProfiles(name)')
    for profiles in feed:
      for profile in profiles:
        parameters['profileNameList'].append(profile['name'])
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, parameters['cbfilter']], str(e))

CHROMEPROFILECOMMAND_TIME_OBJECTS = {
  'clientExecutionTime',
  'issueTime',
  }

def _showChromeProfileCommand(profcmd, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS),
              ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_PROFILE_COMMAND, profcmd['name']], i, count)
  Ind.Increment()
  showJSON(None, profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS)
  Ind.Decrement()

def _printChromeProfileCommand(profcmd, csvPF, FJQC):
  row = flattenJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS)
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    csvPF.WriteRowNoFilter({'name': profcmd['name'],
                            'JSON': json.dumps(cleanJSON(profcmd, timeObjects=CHROMEPROFILECOMMAND_TIME_OBJECTS),
                                               ensure_ascii=False, sort_keys=True)})

# gam create chromeprofilecommand <ChromeProfileNameEntity>
#	[clearcache [<Boolean>]] [clearcookies [<Boolean>]]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCreateChromeProfileCommand():
  cm, parameters = _initChromeProfileNameParameters()
  body = {'commandType': 'clearBrowsingData', 'payload': {}}
  csvPF = None
  FJQC = FormatJSONQuoteChar(None)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getChromeProfileNameParameters(myarg, parameters):
      pass
    elif myarg == 'clearcache':
      body['payload']['clearCache'] = getBoolean()
    elif myarg == 'clearcookies':
      body['payload']['clearCookies'] = getBoolean()
    elif myarg == 'csv':
      csvPF = CSVPrintFile(['name'], 'sortall')
      FJQC.SetCsvPF(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getChromeProfileNameEntityForCommand(cm, parameters)
  count = len(parameters['profileNameList'])
  i = 0
  for profileName in parameters['profileNameList']:
    i +=1
    try:
      profcmd = callGAPI(cm.customers().profiles().commands(), 'create',
                         throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                         parent=profileName, body=body)
      if csvPF is None:
        _showChromeProfileCommand(profcmd, FJQC, i, count)
      else:
        _printChromeProfileCommand(profcmd, csvPF, FJQC)
    except (GAPI.notFound) as e:
      entityActionFailedWarning([Ent.CHROME_PROFILE_COMMAND, profileName], str(e), i, count)
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.CHROME_PROFILE_COMMAND, profileName], str(e))
  if csvPF:
    csvPF.writeCSVfile('Chrome Profile Commands')

# gam info chromeprofilecommand <ChromeProfileCommandName>
#	[formatjson]
def doInfoChromeProfileCommand():
  cm = buildGAPIObject(API.CHROMEMANAGEMENT)
  profileCommandName = _getChromeProfileName()
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  try:
    profcmd = callGAPI(cm.customers().profiles().commands(), 'get',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                       name=profileCommandName)
    _showChromeProfileCommand(profcmd, FJQC)
  except (GAPI.invalidArgument, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.CHROME_PROFILE, profileCommandName], str(e))

# gam show chromeprofilecommands <ChromeProfileNameEntity>
#	[formatjson]
# gam print chromeprofilecommands <ChromeProfilNameEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def doPrintShowChromeProfileCommands():
  csvPF = CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  cm, parameters = _initChromeProfileNameParameters()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getChromeProfileNameParameters(myarg, parameters):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  _getChromeProfileNameEntityForCommand(cm, parameters)
  if parameters['profileNameList']:
    count = len(parameters['profileNameList'])
    i = 0
    for profileName in parameters['profileNameList']:
      i +=1
      printGettingEntityItemForWhom(Ent.CHROME_PROFILE_COMMAND, profileName, i, count)
      pageMessage = getPageMessage()
      try:
        profcmds = callGAPIpages(cm.customers().profiles().commands(), 'list', 'chromeBrowserProfileCommands',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                 parent=profileName, pageSize=100)
        if not csvPF:
          jcount = len(profcmds)
          Ind.Increment()
          j = 0
          for profcmd in profcmds:
            j += 1
            _showChromeProfileCommand(profcmd, FJQC, j, jcount)
          Ind.Decrement()
        else:
          for profcmd in profcmds:
            _printChromeProfileCommand(profcmd, csvPF, FJQC)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.CHROME_PROFILE, profileName], str(e), i, count)
      except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
        entityActionFailedExit([Ent.CHROME_PROFILE, profileName], str(e))
  elif parameters['commandNameList']:
    count = len(parameters['commandNameList'])
    i = 0
    for profileCommandName in parameters['commandNameList']:
      i +=1
      try:
        profcmd = callGAPI(cm.customers().profiles().commands(), 'get',
                           throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                           name=profileCommandName)
        if not csvPF:
          _showChromeProfileCommand(profcmd, FJQC, i, count)
        else:
          _printChromeProfileCommand(profcmd, csvPF, FJQC)
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.CHROME_PROFILE_COMMAND, profileCommandName], str(e), i, count)
      except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
        entityActionFailedExit([Ent.CHROME_PROFILE, profileCommandName], str(e))
  if csvPF:
    csvPF.writeCSVfile('Chrome Profile Commands')
