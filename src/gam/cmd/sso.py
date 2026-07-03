"""GAM inbound SSO profile, credential, and assignment management."""

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


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def getCIOrgunitID(cd, orgunit):
  ou_id = _getMain().getOrgUnitId(cd, orgunit)[1]
  if ou_id.startswith('id:'):
    ou_id = ou_id[3:]
  return f'orgUnits/{ou_id}'

def _getInboundSSOProfiles(ci, mode):
  customer = _getMain().normalizeChannelCustomerID(GC.Values[GC.CUSTOMER_ID])
  profiles = []
  if mode in _getMain().INBOUNDSSO_ALL_SAML:
    try:
      profiles.extend(_getMain().callGAPIpages(ci.inboundSamlSsoProfiles(), 'list', 'inboundSamlSsoProfiles',
                                    throwReasons=GAPI.CISSO_LIST_THROW_REASONS,
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    bailOnInternalError=True,
                                    filter=f'customer=="{customer}"'))
    except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
            GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.INBOUND_SSO_PROFILE, customer], str(e))
  if mode in _getMain().INBOUNDSSO_ALL_OIDC:
    try:
      profiles.extend(_getMain().callGAPIpages(ci.inboundOidcSsoProfiles(), 'list', 'inboundOidcSsoProfiles',
                                    throwReasons=GAPI.CISSO_LIST_THROW_REASONS,
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    bailOnInternalError=True,
                                    filter=f'customer=="{customer}"'))
    except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
            GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.INBOUND_SSO_PROFILE, customer], str(e))
  return profiles

def _convertInboundSSOProfileDisplaynameToName(ci, mode, displayName='',
                                               entityType=Ent.INBOUND_SSO_PROFILE):
  if displayName.lower().startswith('id:') or displayName.lower().startswith('uid:'):
    displayName = displayName.split(':', 1)[1]
    if mode == 'all':
      if not (displayName.startswith('inboundSamlSsoProfiles/') and
              displayName.startswith('inboundOidcSsoProfiles/')):
        displayName = f'inboundSamlSsoProfiles/{displayName}'
    elif mode == 'saml':
      if not displayName.startswith('inboundSamlSsoProfiles/'):
        displayName = f'inboundSamlSsoProfiles/{displayName}'
    else:
      if not displayName.startswith('inboundOidcSsoProfiles/'):
        displayName = f'inboundOidcSsoProfiles/{displayName}'
    return displayName
  profiles = _getInboundSSOProfiles(ci, mode)
  matches = []
  for profile in profiles:
    if displayName.lower() == profile.get('displayName', '').lower():
      matches.append(profile)
  if len(matches) == 1:
    return matches[0]['name']
  if len(matches) == 0:
    errMsg = Msg.NO_SSO_PROFILE_MATCHES.format(displayName)
  else:
    errMsg = Msg.MULTIPLE_SSO_PROFILES_MATCH.format(displayName)
    for m in matches:
      errMsg += f'  {m["name"]}  {m["displayName"]}\n'
  _getMain().entityActionFailedWarning([entityType, None], errMsg)
  return None

def _getInboundSSOProfileArguments(body, mode):
  returnNameOnly = False
  if mode == 'saml':
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if myarg == 'name':
        body['displayName'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'entityid':
        body.setdefault('idpConfig', {})['entityId'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'loginurl':
        body.setdefault('idpConfig', {})['singleSignOnServiceUri'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'logouturl':
        body.setdefault('idpConfig', {})['logoutRedirectUri'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'changepasswordurl':
        body.setdefault('idpConfig', {})['changePasswordUri'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'returnnameonly':
        returnNameOnly = True
      else:
        _getMain().unknownArgumentExit()
  else:
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if myarg == 'name':
        body['displayName'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'issueruri':
        body.setdefault('idpConfig', {})['issuerUri'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'changepasswordurl':
        body.setdefault('idpConfig', {})['changePasswordUri'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'clientid':
        body.setdefault('rpConfig', {})['clientId'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'clientsecret':
        body.setdefault('rpConfig', {})['clientSecret'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'returnnameonly':
        returnNameOnly = True
      else:
        _getMain().unknownArgumentExit()
  return (returnNameOnly, body)

def _showInboundSSOProfile(profile, FJQC, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(profile), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.INBOUND_SSO_PROFILE, profile['name']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, profile)
  Ind.Decrement()

def _processInboundSSOProfileResult(result, returnNameOnly, kvlist, function):
  if GC.Values[GC.DEBUG_LEVEL] > 0:
    _getMain().writeStderr(f'inboundSSOProfileResult: {result}\n')
  if result.get('done', False):
    if 'error' not in result:
      if 'response' in result:
        if not returnNameOnly:
          _showInboundSSOProfile(result['response'], None)
        else:
          _getMain().writeStdout(f'{result["response"]["name"]}\n')
      else:
        _getMain().entityActionPerformed(kvlist)
    else:
      _getMain().entityActionFailedWarning(kvlist, result['error']['message'])
  elif not returnNameOnly:
    _getMain().entityActionPerformedMessage(kvlist, Msg.ACTION_IN_PROGRESS.format(f'{function} inboundssoprofile'))
  else:
    _getMain().writeStdout('inProgress\n')

def _getInboundSSOModeService(ci):
  mode = _getMain().getChoice(_getMain().INBOUNDSSO_INPUT_MODE_CHOICE_MAP, defaultChoice='saml', mapChoice=True)
  service = ci.inboundSamlSsoProfiles() if mode == 'saml' else ci.inboundOidcSsoProfiles()
  return (mode, service)

# gam create inboundssoprofile [saml|oidc] [name <SSOProfileName>]
#	[entityid <String>] [loginurl <URL>] [logouturl <URL>] [changepasswordurl <URL>]
#	[returnnameonly]
def doCreateInboundSSOProfile():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  mode, service = _getInboundSSOModeService(ci)
  body = {'customer': _getMain().normalizeChannelCustomerID(GC.Values[GC.CUSTOMER_ID]),
          'displayName': 'SSO Profile'
         }
  returnNameOnly, body = _getInboundSSOProfileArguments(body, mode)
  kvlist = [Ent.INBOUND_SSO_PROFILE, body['displayName']]
  try:
    result = _getMain().callGAPI(service, 'create',
                      throwReasons=GAPI.CISSO_CREATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      body=body)
    _processInboundSSOProfileResult(result, returnNameOnly, kvlist, 'create')
  except (GAPI.failedPrecondition, GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam update inboundssoprofile [saml|oidc] <SSOProfileItem>
#	[entityid <String>] [loginurl <URL>] [logouturl <URL>] [changepasswordurl <URL>]
#	[returnnameonly]
def doUpdateInboundSSOProfile():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  mode, service = _getInboundSSOModeService(ci)
  name = _convertInboundSSOProfileDisplaynameToName(ci, mode, _getMain().getString(Cmd.OB_STRING))
  if not name:
    return
  returnNameOnly, body = _getInboundSSOProfileArguments({}, mode)
  kvlist = [Ent.INBOUND_SSO_PROFILE, name]
  try:
    result = _getMain().callGAPI(service, 'patch',
                      throwReasons=GAPI.CISSO_UPDATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name, updateMask=','.join(body.keys()), body=body)
    _processInboundSSOProfileResult(result, returnNameOnly, kvlist, 'update')
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.failedPrecondition, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam delete inboundssoprofile [saml|oidc] <SSOProfileItem>
def doDeleteInboundSSOProfile():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  mode, service = _getInboundSSOModeService(ci)
  name = _convertInboundSSOProfileDisplaynameToName(ci, mode, _getMain().getString(Cmd.OB_STRING))
  if not name:
    return
  _getMain().checkForExtraneousArguments()
  kvlist = [Ent.INBOUND_SSO_PROFILE, name]
  try:
    result = _getMain().callGAPI(service, 'delete',
                      throwReasons=GAPI.CISSO_UPDATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name)
    _processInboundSSOProfileResult(result, True, kvlist, 'delete')
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.failedPrecondition, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

def _getInboundSSOProfileByName(ci, mode, name):
  notFound = False
  kvlist = [Ent.INBOUND_SSO_PROFILE, name]
  if mode in _getMain().INBOUNDSSO_ALL_SAML:
    try:
      return _getMain().callGAPI(ci.inboundSamlSsoProfiles(), 'get',
                      throwReasons=GAPI.CISSO_GET_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name)
    except GAPI.notFound:
      notFound = True
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.invalid, GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning(kvlist, str(e))
  if mode in _getMain().INBOUNDSSO_ALL_OIDC:
    try:
      return _getMain().callGAPI(ci.inboundOidcSsoProfiles(), 'get',
                      throwReasons=GAPI.CISSO_GET_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name)
    except GAPI.notFound:
      notFound = True
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.invalid, GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning(kvlist, str(e))
  if notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  return None

# gam info inboundssoprofile [all|saml|oidc] <SSOProfileItem> [formatjson]
def doInfoInboundSSOProfile():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  mode = _getMain().getChoice(_getMain().INBOUNDSSO_OUTPUT_MODE_CHOICE_MAP, defaultChoice='all', mapChoice=True)
  name = _getMain().getString(Cmd.OB_STRING)
  FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  name = _convertInboundSSOProfileDisplaynameToName(ci, mode, name)
  if not name:
    return
  mode = 'saml' if name.startswith('inboundSamlSsoProfiles/') else 'oidc'
  profile = _getInboundSSOProfileByName(ci, mode, name)
  if profile:
    _showInboundSSOProfile(profile, FJQC)

# gam show inboundssoprofile [all|saml|oidc]
#	[formatjson]
# gam print inboundssoprofile [all|saml|oidc] [todrive <ToDriveAttribute>*]
#	[[formatjson [quotechar <Character>]]
def doPrintShowInboundSSOProfiles():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  customer = _getMain().normalizeChannelCustomerID(GC.Values[GC.CUSTOMER_ID])
  csvPF = _getMain().CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  cfilter = f'customer=="{customer}"'
  mode = _getMain().getChoice(_getMain().INBOUNDSSO_OUTPUT_MODE_CHOICE_MAP, defaultChoice='all', mapChoice=True)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF:
    _getMain().printGettingAllAccountEntities(Ent.INBOUND_SSO_PROFILE, cfilter)
  profiles = _getInboundSSOProfiles(ci, mode)
  if not csvPF:
    count = len(profiles)
    if not FJQC.formatJSON:
      _getMain().performActionNumItems(count, Ent.INBOUND_SSO_PROFILE)
    Ind.Increment()
    i = 0
    for profile in profiles:
      i += 1
      _showInboundSSOProfile(profile, FJQC, i, count)
    Ind.Decrement()
  else:
    for profile in profiles:
      row = _getMain().flattenJSON(profile)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'name': profile['name'],
                                'JSON': json.dumps(_getMain().cleanJSON(profile), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Inbound SSO Profiles')

def getInboundSSOProfileCredentials(ci, profile):
  try:
    return _getMain().callGAPIpages(ci.inboundSamlSsoProfiles().idpCredentials(), 'list', 'idpCredentials',
                         throwReasons=GAPI.CISSO_LIST_THROW_REASONS,
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                         bailOnInternalError=True,
                         parent=profile)
  except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning([Ent.INBOUND_SSO_PROFILE, profile], str(e))
    return None

def getInboundSSOCredentialsName():
  name = _getMain().getString(Cmd.OB_STRING)
  if name.startswith('id:') or name.startswith('uid:'):
    name = name.split(':', 1)[1]
  return name

INBOUNDSSO_CREDENTIALS_TIME_OBJECTS = ['updateTime']

def _showInboundSSOCredentials(credentials, FJQC, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(credentials, timeObjects=INBOUNDSSO_CREDENTIALS_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.INBOUND_SSO_CREDENTIALS, credentials['name']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, credentials, timeObjects=INBOUNDSSO_CREDENTIALS_TIME_OBJECTS)
  Ind.Decrement()

def _processInboundSSOCredentialsResult(result, kvlist, function):
  if result.get('done', False):
    if 'error' not in result:
      if 'response' in result:
        _showInboundSSOCredentials(result['response'], None)
      else:
        _getMain().entityActionPerformed(kvlist)
    else:
      _getMain().entityActionFailedWarning(kvlist, result['error']['message'])
  else:
    _getMain().entityActionPerformedMessage(kvlist, Msg.ACTION_IN_PROGRESS.format(f'{function} inboundssocredentials'))

# gam create inboundssocredentials profile <SSOProfileItem>
#	(pemfile <FileName>)|(generatekey [keysize 1024|2048|4096]) [replaceolddest]
def doCreateInboundSSOCredential():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  mode = 'saml'
  profile = None
  generateKey = replaceOldest = False
  keySize = 2048
  pemData = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'profile':
      profile = _convertInboundSSOProfileDisplaynameToName(ci, mode,
                                                           _getMain().getString(Cmd.OB_STRING),
                                                           Ent.INBOUND_SSO_CREDENTIALS)
      if not profile:
        return
    elif myarg == 'pemfile':
      pemData = _getMain().readFile(_getMain().setFilePath(_getMain().getString(Cmd.OB_FILE_NAME), GC.INPUT_DIR))
    elif myarg == 'generatekey':
      generateKey = True
    elif myarg == 'replaceoldest':
      replaceOldest = True
    elif myarg == 'keysize':
      keySize=int(_getMain().getChoice([1024, 2048, 4096]))
    else:
      _getMain().unknownArgumentExit()
  if not profile:
    _getMain().missingArgumentExit('profile')
  if not pemData and not generateKey:
    _getMain().missingArgumentExit('pemfile|generatekey')
  if pemData and generateKey:
    _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('pemfile', 'generatekey'))
  if replaceOldest:
    credentials = getInboundSSOProfileCredentials(ci, profile)
    if credentials is None:
      return
    count = len(credentials)
    if count == 2:
      oldest_key = min(credentials, key=lambda x:x['updateTime'])
      action = Act.Get()
      Act.Set(Act.DELETE)
      doDeleteInboundSSOCredential(ci=ci, name=oldest_key['name'])
      Act.Set(action)
    else:
      _getMain().writeStdout(Msg.NO_CREDENTIALS_REPLACEMENT.format(Ent.Singular(Ent.INBOUND_SSO_PROFILE), profile,
                                                        count, Ent.Choose(Ent.INBOUND_SSO_CREDENTIALS, count)))
  if generateKey:
    privKey, pemData = _getMain()._generatePrivateKeyAndPublicCert('', '', 'GAM', keySize, b64enc_pub=False)
    timestamp = arrow.now(GC.Values[GC.TIMEZONE]).strftime('%Y%m%d-%I%M%S')
    priv_file = f'privatekey-{timestamp}.pem'
    _getMain().writeFile(priv_file, privKey)
    _getMain().writeStdout(Msg.WROTE_PRIVATE_KEY_DATA.format(priv_file))
    pub_file = f'publiccert-{timestamp}.pem'
    _getMain().writeFile(pub_file, pemData)
    _getMain().writeStdout(Msg.WROTE_PUBLIC_CERTIFICATE.format(pub_file))
    kvlist = [Ent.INBOUND_SSO_CREDENTIALS, profile]
  try:
    result = _getMain().callGAPI(ci.inboundSamlSsoProfiles().idpCredentials(), 'add',
                      throwReasons=GAPI.CISSO_UPDATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      parent=profile, body={'pemData': pemData})
    _processInboundSSOCredentialsResult(result, kvlist, 'create')
  except GAPI.notFound as e:
    _getMain().entityActionFailedWarning([Ent.INBOUND_SSO_PROFILE, profile], str(e))
  except (GAPI.failedPrecondition, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam delete inboundssocredential <SSOCredentialsName>
def doDeleteInboundSSOCredential(ci=None, name=None):
  if not ci:
    ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  if not name:
    name = getInboundSSOCredentialsName()
  _getMain().checkForExtraneousArguments()
  kvlist = [Ent.INBOUND_SSO_CREDENTIALS, name]
  try:
    result = _getMain().callGAPI(ci.inboundSamlSsoProfiles().idpCredentials(), 'delete',
                      throwReasons=GAPI.CISSO_UPDATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name)
    _processInboundSSOCredentialsResult(result, kvlist, 'delete')
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.failedPrecondition, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam info inboundssocredential <SSOCredentialsName> [formatjson]
def doInfoInboundSSOCredential():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  name = getInboundSSOCredentialsName()
  FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  kvlist = [Ent.INBOUND_SSO_CREDENTIALS, name]
  try:
    credentials = _getMain().callGAPI(ci.inboundSamlSsoProfiles().idpCredentials(), 'get',
                          throwReasons=GAPI.CISSO_GET_THROW_REASONS,
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          bailOnInternalError=True,
                          name=name)
    _showInboundSSOCredentials(credentials, FJQC)
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam show inboundssocredentials [profile|profiles <SSOProfileItemList>]
#	[formatjson]
# gam print inboundssocredentials [profile|profiles <SSOProfileItemList>]
#	[[formatjson [quotechar <Character>]]
def doPrintShowInboundSSOCredentials():
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  csvPF = _getMain().CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  mode = 'saml'
  profiles = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'profile', 'profiles'}:
      errors = 0
      for profile in _getMain().getEntityList(Cmd.OB_STRING_LIST, shlexSplit=True):
        name = _convertInboundSSOProfileDisplaynameToName(ci, mode, profile, Ent.INBOUND_SSO_CREDENTIALS)
        if name:
          profiles.append(name)
        else:
          errors += 1
      if errors:
        return
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not profiles:
    profiles = [p['name'] for p in _getInboundSSOProfiles(ci, mode)]
  count = len(profiles)
  i = 0
  for profile in profiles:
    i += 1
    credentials = getInboundSSOProfileCredentials(ci, profile)
    if credentials is None:
      continue
    if not csvPF:
      jcount = len(credentials)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.INBOUND_SSO_PROFILE, profile], jcount, Ent.INBOUND_SSO_CREDENTIALS, i, count)
      Ind.Increment()
      j = 0
      for credential in credentials:
        j += 1
        _showInboundSSOCredentials(credential, FJQC, j, jcount)
      Ind.Decrement()
    else:
      for credential in credentials:
        row = _getMain().flattenJSON(credential, timeObjects=INBOUNDSSO_CREDENTIALS_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'name': credential['name'],
                                  'JSON': json.dumps(_getMain().cleanJSON(credential, timeObjects=INBOUNDSSO_CREDENTIALS_TIME_OBJECTS),
                                                     ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Inbound SSO Credentials')

def _getInboundSSOAssignment(ci, name):
  kvlist = [Ent.INBOUND_SSO_ASSIGNMENT, name]
  try:
    return _getMain().callGAPI(ci.inboundSsoAssignments(), 'get',
                    throwReasons=GAPI.CISSO_GET_THROW_REASONS,
                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                    bailOnInternalError=True,
                    name=name)
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))
  return None

def _getInboundSSOAssignments(ci):
  customer = _getMain().normalizeChannelCustomerID(GC.Values[GC.CUSTOMER_ID])
  try:
    return _getMain().callGAPIpages(ci.inboundSsoAssignments(), 'list', 'inboundSsoAssignments',
                         throwReasons=GAPI.CISSO_LIST_THROW_REASONS,
                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                         bailOnInternalError=True,
                         filter=f'customer=="{customer}"')
  except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalid,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning([Ent.INBOUND_SSO_ASSIGNMENT, customer], str(e))
    return None

def _getInboundSSOAssignmentName():
  name = _getMain().getString(Cmd.OB_STRING)
  if name.startswith('id:') or name.startswith('uid:'):
    name = name.split(':', 1)[1]
  if not name.startswith('inboundSsoAssignments/'):
    name = f'inboundSsoAssignments/{name}'
  return name

def _getInboundSSOAssignmentByTarget(ci, cd, target):
  targetType = 'name'
  if target.startswith('id:') or target.startswith('uid:'):
    target = target.split(':', 1)[1]
  elif re.match(r'^groups/[^/]+$', target):
    targetType = 'targetGroup'
  elif re.match(r'^orgUnits/[^/]+$', target):
    targetType = 'targetOrgUnit'
  elif target.lower().startswith('group:'):
    targetType = 'targetGroup'
    _, target, _ = _getMain().convertGroupEmailToCloudID(ci, target[6:])
  elif target.lower().startswith('orgunit:'):
    targetType = 'targetOrgUnit'
    target = getCIOrgunitID(cd, target[8:])
  elif not target.startswith('inboundSsoAssignments/'):
    target = f'inboundSsoAssignments/{target}'
  if targetType == 'name':
    return _getInboundSSOAssignment(ci, target)
  assignments = _getInboundSSOAssignments(ci)
  if assignments is not None:
    for assignment in assignments:
      if targetType in assignment and assignment[targetType] == target:
        return assignment
  _getMain().usageErrorExit(Msg.NO_SSO_PROFILE_ASSIGNED.format(targetType, target))

def _getInboundSSOAssignmentArguments(ci, cd, body):
  mode = None
  rank = 0
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'rank':
      rank = _getMain().getInteger(minVal=1)
    elif myarg == 'mode':
      body['ssoMode'] = _getMain().getChoice(_getMain().INBOUNDSSO_MODE_CHOICE_MAP, mapChoice=True)
      if body['ssoMode'] == 'SAML_SSO':
        mode = 'saml'
        profile = 'inboundSamlSsoProfile'
      elif body['ssoMode'] == 'OIDC_SSO':
        mode = 'oidc'
        profile = 'inboundOidcSsoProfile'
    elif mode and myarg == 'profile':
      name = _convertInboundSSOProfileDisplaynameToName(ci, mode,
                                                        _getMain().getString(Cmd.OB_STRING),
                                                        Ent.INBOUND_SSO_ASSIGNMENT)
      if not name:
        return None
      body['samlSsoInfo'] = {profile: name}
    elif myarg == 'neverredirect':
      body['signInBehavior'] = {'redirectCondition': 'NEVER'}
    elif myarg == 'group':
      _, body['targetGroup'], _ = _getMain().convertGroupEmailToCloudID(ci, _getMain().getString(Cmd.OB_STRING))
    elif myarg in {'ou', 'org', 'orgunit'}:
      body['targetOrgUnit'] = getCIOrgunitID(cd, _getMain().getString(Cmd.OB_ORGUNIT_ITEM))
    else:
      _getMain().unknownArgumentExit()
  if 'ssoMode' not in body:
    _getMain().missingArgumentExit('mode')
  if mode and 'samlSsoInfo' not in body:
    _getMain().missingArgumentExit('profile')
  if 'targetGroup' in body:
    if 'targetOrgUnit' in body:
      _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('group', 'ou|org|orgunit'))
    if not rank:
      _getMain().missingArgumentExit('rank')
    body['rank'] = rank
  return body

def _updateInboundAssignmentTargetNames(ci, cd, assignment):
  if 'targetGroup' in assignment:
    _, _, assignment['targetGroupEmail'] = convertGroupCloudIDToEmail(ci, assignment['targetGroup'])
  elif 'targetOrgUnit' in assignment:
    assignment['targetOrgUnitPath'] = convertOrgUnitIDtoPath(cd, assignment['targetOrgUnit'])

def _showInboundSSOAssignment(assignment, FJQC, ci, cd, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(assignment), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.INBOUND_SSO_ASSIGNMENT, assignment['name']], i, count)
  _updateInboundAssignmentTargetNames(ci, cd, assignment)
  Ind.Increment()
  _getMain().showJSON(None, assignment)
  Ind.Decrement()

def _processInboundSSOAssignmentResult(result, kvlist, ci, cd, function):
  if result['done']:
    if 'error' not in result:
      if 'response' in result:
        _showInboundSSOAssignment(result['response'], None, ci, cd)
      else:
        _getMain().entityActionPerformed(kvlist)
    else:
      _getMain().entityActionFailedWarning(kvlist, result['error']['message'])
  else:
    _getMain().entityActionPerformedMessage(kvlist, Msg.ACTION_IN_PROGRESS.format(f'{function} inboundssoassignment'))

# gam create inboundssoassignment
#	(group <GroupItem> rank <Number>)|(ou|org|orgunit <OrgUnitItem>)
#	(mode sso_off)|(mode saml_sso profile <SSOProfileItem>)|(mode oidc_sso profile <SSOProfileName>}|(mode domain_wide_saml_if_enabled)
#	[neverredirect]
def doCreateInboundSSOAssignment():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  body = {'customer': _getMain().normalizeChannelCustomerID(GC.Values[GC.CUSTOMER_ID])}
  body = _getInboundSSOAssignmentArguments(ci, cd, body)
  if not body:
    return
  kvlist = [Ent.INBOUND_SSO_ASSIGNMENT, body['customer']]
  try:
    result = _getMain().callGAPI(ci.inboundSsoAssignments(), 'create',
                      throwReasons=GAPI.CISSO_CREATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      body=body)
    _processInboundSSOAssignmentResult(result, kvlist, ci, cd, 'create')
  except (GAPI.failedPrecondition, GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam update inboundssoassignment <SSOAssignmentName>
#	[(group <GroupItem> rank <Number>)|(ou|org|orgunit <OrgUnitItem>)]
#	(mode sso_off)|(mode saml_sso profile <SSOProfileItem>)|(mode oidc_sso profile <SSOProfileName>}|(mode domain_wide_saml_if_enabled)
#	[neverredirect]
def doUpdateInboundSSOAssignment():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  name = _getInboundSSOAssignmentName()
  body = _getInboundSSOAssignmentArguments(ci,cd, {})
  kvlist = [Ent.INBOUND_SSO_ASSIGNMENT, name]
  try:
    result = _getMain().callGAPI(ci.inboundSsoAssignments(), 'patch',
                      throwReasons=GAPI.CISSO_UPDATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name, updateMask=','.join(list(body.keys())), body=body)
    _processInboundSSOAssignmentResult(result, kvlist, ci, cd, 'update')
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.failedPrecondition, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam delete inboundssoassignment <SSOAssignmentSelector>
def doDeleteInboundSSOAssignment():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  target = _getMain().getString(Cmd.OB_STRING)
  assignment = _getInboundSSOAssignmentByTarget(ci, cd, target)
  if assignment is None:
    return
  name = assignment['name']
  _getMain().checkForExtraneousArguments()
  kvlist = [Ent.INBOUND_SSO_ASSIGNMENT, name]
  try:
    result = _getMain().callGAPI(ci.inboundSsoAssignments(), 'delete',
                      throwReasons=GAPI.CISSO_UPDATE_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      bailOnInternalError=True,
                      name=name)
    _processInboundSSOAssignmentResult(result, kvlist, None, None, 'delete')
  except GAPI.notFound:
    _getMain().entityActionFailedWarning(kvlist, Msg.DOES_NOT_EXIST)
  except (GAPI.failedPrecondition, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
          GAPI.systemError, GAPI.permissionDenied, GAPI.internalError, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning(kvlist, str(e))

# gam info inboundssoassignment <SSOAssignmentSelector> [formatjson]
def doInfoInboundSSOAssignment():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  target = _getMain().getString(Cmd.OB_STRING)
  FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  assignment = _getInboundSSOAssignmentByTarget(ci, cd, target)
  if assignment is None:
    return
  name = assignment.get('samlSsoInfo', {}).get('inboundSamlSsoProfile')
  if name:
    profile = _getInboundSSOProfileByName(ci, 'saml', name)
    if profile:
      assignment['samlSsoInfo']['inboundSamlSsoProfile'] = profile
  else:
    name = assignment.get('oidcSsoInfo', {}).get('inboundOidcSsoProfile')
    if name:
      profile = _getInboundSSOProfileByName(ci, 'oidc', name)
      if profile:
        assignment['oidcSsoInfo']['inboundOidcSsoProfile'] = profile
  _showInboundSSOAssignment(assignment, FJQC, ci, cd)

# gam show inboundssoassignments
#	[formatjson]
# gam print inboundssoassignments [todrive <ToDriveAttribute>*]
#	[[formatjson [quotechar <Character>]]
def doPrintShowInboundSSOAssignments():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = _getMain().buildGAPIObject(API.CLOUDIDENTITY_INBOUND_SSO)
  customer = _getMain().normalizeChannelCustomerID(GC.Values[GC.CUSTOMER_ID])
  csvPF = _getMain().CSVPrintFile(['name']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  cfilter = f'customer=="{customer}"'
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF:
    _getMain().printGettingAllAccountEntities(Ent.INBOUND_SSO_ASSIGNMENT, cfilter)
  assignments = _getInboundSSOAssignments(ci)
  if assignments is None:
    return
  if not csvPF:
    count = len(assignments)
    if not FJQC.formatJSON:
      _getMain().performActionNumItems(count, Ent.INBOUND_SSO_ASSIGNMENT)
    Ind.Increment()
    i = 0
    for assignment in assignments:
      i += 1
      _showInboundSSOAssignment(assignment, FJQC, ci, cd, i, count)
    Ind.Decrement()
  else:
    for assignment in assignments:
      _updateInboundAssignmentTargetNames(ci, cd, assignment)
      row = _getMain().flattenJSON(assignment)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'name': assignment['name'],
                                'JSON': json.dumps(_getMain().cleanJSON(assignment), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Inbound SSO Assignments')

SITEVERIFICATION_METHOD_CHOICE_MAP = {
  'cname': 'DNS_CNAME',
  'dnscname': 'DNS_CNAME',
  'dnstxt': 'DNS_TXT',
  'txt': 'DNS_TXT',
  'text': 'DNS_TXT',
  'file': 'FILE',
  'site': 'FILE',
  }

# gam create verify|verification <DomainName>
