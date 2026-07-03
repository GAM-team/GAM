"""GAM Context-Aware Access management."""

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


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def CAARoleErrorExit(caa):
  sa_email = caa._http.credentials.signer_email
  _getMain().systemErrorExit(_getMain().NO_SA_ACCESS_CONTEXT_MANAGER_EDITOR_ROLE_RC,
                  f'Please grant service account {sa_email} the Access Context Manager Editor role in your GCP organization.')

def buildCAAServiceObject():
  _, caa = _getMain().buildGAPIServiceObject(API.ACCESSCONTEXTMANAGER, None)
  return caa

def getAccessPolicy(caa=None):
  if not caa:
    caa = buildCAAServiceObject()
  parent = _getMain().getCRMOrgId()
  if not parent:
    CAARoleErrorExit(caa)
  try:
    aps = _getMain().callGAPIpages(caa.accessPolicies(), 'list', 'accessPolicies',
                        throwReasons=[GAPI.PERMISSION_DENIED],
                        parent=parent, fields='nextPageToken,accessPolicies(name,title)')
  except GAPI.permissionDenied:
    CAARoleErrorExit(caa)
  if not aps:
    _getMain().systemErrorExit(_getMain().ACCESS_POLICY_ERROR_RC, 'You don\'t seem to have any access policies. That is odd.')
  elif len(aps) == 1:
    return aps[0]['name']
  for ap in aps:
    if ap.get('title') == 'Access policy created in Cloud Identity Console':
      return ap['name']
  _getMain().systemErrorExit(_getMain().ACCESS_POLICY_ERROR_RC, 'Could not find a org level access policy. That is odd.')

def normalizeCAALevelName(caa, name):
  if name.startswith('accessPolicies/'):
    return name
  ap_name = getAccessPolicy(caa)
  return f'{ap_name}/accessLevels/{name}'

CAA_OS_TYPE_MAP = {
  'desktopmac': 'DESKTOP_MAC',
  'desktopwindows': 'DESKTOP_WINDOWS',
  'desktoplinux': 'DESKTOP_LINUX',
  'desktopchromeos': 'DESKTOP_CHROME_OS',
  'verifieddesktopchromeos': 'VERIFIED_DESKTOP_CHROME_OS',
  'android': 'ANDROID',
  'ios': 'IOS',
  }

def CAABuildOsConstraints():
  consts_obj = []
  for constraint in _getMain().getString(Cmd.OB_STRING).split(','):
    new_const = {}
    if ':' in constraint:
      osType, new_const['minimumVersion'] = constraint.split(':')
    else:
      osType = constraint
    osType = osType.lower().replace('_', '')
    if osType not in CAA_OS_TYPE_MAP:
      _getMain().invalidChoiceExit(osType, CAA_OS_TYPE_MAP, True)
    if osType != 'verifieddesktopchromeos':
      new_const['osType'] = CAA_OS_TYPE_MAP[osType]
    else:
      new_const['osType'] = 'DESKTOP_CHROME_OS'
      new_const['requireVerifiedChromeOs'] = True
    consts_obj.append(new_const)
  return consts_obj

CAA_ALLOWED_DEVICE_MANAGEMENT_LEVELS_MAP = {
  'basic': 'BASIC',
  'advanced': 'COMPLETE',
  'complete': 'COMPLETE',
  'none': 'NONE',
  }
CAA_ALLOWED_ENCRYPTIION_STATUS_MAP = {
  'encryptionunsupported': 'ENCRYPTION_UNSUPPORTED',
  'encrypted': 'ENCRYPTED',
  'unencrypted': 'UNENCRYPTED',
  }

def CAABuildDevicePolicy():
  device_policy = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'requirescreenlock':
      device_policy['requireScreenLock'] = _getMain().getBoolean()
    elif myarg == 'allowedencryptionstatuses':
      device_policy['allowedEncryptionStatuses'] = []
      for status in _getMain().getString(Cmd.OB_STRING).lower().split(','):
        if status not in CAA_ALLOWED_ENCRYPTIION_STATUS_MAP:
          _getMain().invalidChoiceExit(status, CAA_ALLOWED_ENCRYPTIION_STATUS_MAP, True)
        device_policy['allowedEncryptionStatuses'].append(CAA_ALLOWED_ENCRYPTIION_STATUS_MAP[status])
    elif myarg == 'osconstraints':
      device_policy['osConstraints'] = CAABuildOsConstraints()
    elif myarg == 'alloweddevicemanagementlevels':
      device_policy['allowedDeviceManagementLevels'] = []
      for level in _getMain().getString(Cmd.OB_STRING).lower().split(','):
        if level not in CAA_ALLOWED_DEVICE_MANAGEMENT_LEVELS_MAP:
          _getMain().invalidChoiceExit(level, CAA_ALLOWED_DEVICE_MANAGEMENT_LEVELS_MAP, True)
        device_policy['allowedDeviceManagementLevels'].append(CAA_ALLOWED_DEVICE_MANAGEMENT_LEVELS_MAP[level])
    elif myarg == 'requireadminapproval':
      device_policy['requireAdminApproval'] = _getMain().getBoolean()
    elif myarg == 'requirecorpowned':
      device_policy['requireCorpOwned'] = _getMain().getBoolean()
    elif myarg == 'enddevicepolicy':
      break
    else:
      _getMain().unknownArgumentExit()
  return device_policy

ISO3166_1_ALPHA_2_CODES = {
  "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
  "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV", "BW", "BY", "BZ",
  "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ",
  "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM", "FO", "FR",
  "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY",
  "HK", "HM", "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT", "JE", "JM", "JO", "JP",
  "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY",
  "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK", "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ",
  "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ",
  "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
  "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS", "ST", "SV", "SX", "SY", "SZ",
  "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW", "TZ",
  "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI", "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW",
  }

def validateISO3166_1_alpha2_code(region):
  if region not in ISO3166_1_ALPHA_2_CODES:
    Cmd.Backup()
    _getMain().expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID_CHOICE][1].format(region), Msg.INVALID_REGION)

def CAABuildCondition():
  condition = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'ipsubnetworks':
      condition['ipSubnetworks'] = getString(Cmd.OB_STRING_LIST).split(',')
    elif myarg == 'devicepolicy':
      condition['devicePolicy'] = CAABuildDevicePolicy()
    elif myarg == 'requiredaccesslevels':
      condition['requiredAccessLevels'] = getString(Cmd.OB_STRING_LIST).split(',')
    elif myarg == 'negate':
      condition['negate'] = _getMain().getBoolean()
    elif myarg == 'members':
      condition['members'] = getString(Cmd.OB_STRING_LIST).split(',')
    elif myarg == 'regions':
      condition['regions'] = getString(Cmd.OB_STRING_LIST).upper().split(',')
      for region in condition['regions']:
        validateISO3166_1_alpha2_code(region)
    elif myarg == 'endcondition':
      break
    else:
      _getMain().unknownArgumentExit()
  return condition

def CAABuildBasicLevel():
  basic_level = {'conditions': []}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'combiningfunction':
      basic_level['combiningFunction'] = _getMain().getChoice(_getMain().AND_OR_CONJUNCTION_MAP, mapChoice=True)
    elif myarg == 'condition':
      basic_level['conditions'].append(CAABuildCondition())
    else:
      _getMain().unknownArgumentExit()
  return basic_level

def CAABuildLevel(body):
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'basic':
      body['basic'] = CAABuildBasicLevel()
    elif myarg == 'custom':
      body['custom'] = {'expr': {'expression': getString(Cmd.OB_STRING), 'title': 'expr'}}
    elif myarg == 'description':
      body['description'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'json':
      body.update(_getMain().getJSON(['name']))
    else:
      _getMain().unknownArgumentExit()

# gam create caalevel <String> [description <String>] (basic <CAABasicAttribute>+)|(custom <String>)|<JSONData>
def doCreateCAALevel():
  caa = buildCAAServiceObject()
  ap_name = getAccessPolicy(caa)
  title = _getMain().getString(Cmd.OB_STRING).replace(' ', '_')
  allowed_title_chars = string.ascii_letters + string.digits + '_'
  name = ''.join([c for c in title if c in allowed_title_chars])[:50]
  name = f'{ap_name}/accessLevels/{name}'
  body = {'name': name, 'title': title}
  CAABuildLevel(body)
  try:
    _getMain().callGAPI(caa.accessPolicies().accessLevels(), 'create',
             throwReasons=[GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
             parent=ap_name, body=body)
    _getMain().entityActionPerformed([Ent.CAA_LEVEL, name])
  except (GAPI.alreadyExists, GAPI.failedPrecondition, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.CAA_LEVEL, name], str(e))
  except GAPI.permissionDenied:
    CAARoleErrorExit(caa)

# gam update caalevel <CAALevelName> [description <String>] (basic <CAABasicAttribute>+)|(custom <String>)|<JSONData>
def doUpdateCAALevel():
  caa = buildCAAServiceObject()
  name = normalizeCAALevelName(caa, _getMain().getString(Cmd.OB_ACCESS_LEVEL_NAME))
  body = {}
  CAABuildLevel(body)
  updateMask = ','.join(body.keys())
  try:
    _getMain().callGAPI(caa.accessPolicies().accessLevels(), 'patch',
             throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
             name=name, updateMask=updateMask, body=body)
    _getMain().entityActionPerformed([Ent.CAA_LEVEL, name])
  except (GAPI.notFound, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.CAA_LEVEL, name], str(e))
  except GAPI.permissionDenied:
    CAARoleErrorExit(caa)

# gam delete caalevel <CAALevelName>
def doDeleteCAALevel():
  caa = buildCAAServiceObject()
  name = normalizeCAALevelName(caa, _getMain().getString(Cmd.OB_ACCESS_LEVEL_NAME))
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(caa.accessPolicies().accessLevels(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
             name=name)
    _getMain().entityActionPerformed([Ent.CAA_LEVEL, name])
  except (GAPI.notFound, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.CAA_LEVEL, name], str(e))
  except GAPI.permissionDenied:
    CAARoleErrorExit(caa)

# gam print caalevels [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
# gam show caalevels
#	[formatjson]
def doPrintShowCAALevels():
  caa = buildCAAServiceObject()
  ap_name = getAccessPolicy(caa)
  csvPF = _getMain().CSVPrintFile(['name', 'title']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    levels = _getMain().callGAPIpages(caa.accessPolicies().accessLevels(), 'list', 'accessLevels',
                           throwReasons=[GAPI.PERMISSION_DENIED],
                           parent=ap_name, accessLevelFormat='CEL', fields='*')
  except GAPI.permissionDenied:
    CAARoleErrorExit(caa)
  if not csvPF:
    count = len(levels)
    if not FJQC.formatJSON:
      _getMain().performActionNumItems(count, Ent.CAA_LEVEL)
      i = 0
      for level in levels:
        i += 1
        _getMain().printEntity([Ent.CAA_LEVEL, level['name']], i, count)
        Ind.Increment()
        _getMain().showJSON(None, level)
        Ind.Decrement()
    else:
      for level in levels:
        _getMain().printLine(json.dumps(_getMain().cleanJSON(level), ensure_ascii=False, sort_keys=True))
  else:
    for level in levels:
      row = _getMain().flattenJSON(level)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        row = {'name': level['name'], 'title': level['title']}
        row['JSON'] = json.dumps(_getMain().cleanJSON(level, timeObjects=_getMain().NOTES_TIME_OBJECTS),
                                 ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
  if csvPF:
    csvPF.writeCSVfile('Context Aware Access Levels')

# Command line processing

