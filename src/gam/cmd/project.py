"""GAM GCP project and service account management.

GCP project creation/deletion, service account management,
key operations, and API enablement.
"""

import base64
import json
import os
import re
import sys
import time

import httplib2

import google.auth
import google.auth.exceptions


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import (
    _getAdminEmail,
    _getSvcAcctData,
    buildGAPIObject,
    buildGAPIObjectNoAuthentication,
    getAPIService,
    getHttpObj,
    getSvcAcctCredentials,
    get_adc_request,
    handleServerError,
    shortenURL,
    transportAuthorizedHttp,
    transportCreateRequest,
)
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIitems, callGAPIpages
from gam.util.args import (
    UTF8,
    checkArgumentPresent,
    checkForExtraneousArguments,
    getArgument,
    getCharacter,
    getChoice,
    getEmailAddress,
    getEmailAddressDomain,
    getInteger,
    getString,
    todaysTime,
)
from gam.util.connection import getLocalGoogleTimeOffset
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar, cleanJSON, flattenJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    entityPerformActionSubItemModifierNumItems,
    printBlankLine,
    printEntity,
    printEntityKVList,
    printEntityMessage,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
    printLine,
)
from gam.util.entity import getEntityArgument, getEntityList, getEntityToModify, setTrueCustomerId
from gam.util.errors import (
    USAGE_ERROR_RC,
    entityActionFailedExit,
    invalidArgumentExit,
    invalidChoiceExit,
    invalidClientSecretsJsonExit,
    invalidOauth2serviceJsonExit,
    missingArgumentExit,
    missingChoiceExit,
    unknownArgumentExit,
)
from gam.util.fileio import readFile, writeFile
from gam.util.crypto import _generatePrivateKeyAndPublicCert
from gam.util.output import (
    createGreenText,
    createRedText,
    createYellowText,
    currentCount,
    formatLocalTime,
    readStdin,
    setSysExitRC,
    systemErrorExit,
    writeStderr,
    writeStdout,
)
from gam.constants import API_ACCESS_DENIED_RC, GAM, GAM_PROJECT_CREATION, GAM_PROJECT_CREATION_CLIENT_ID, GOOGLE_TIMECHECK_LOCATION, JSON_ALREADY_EXISTS_RC, MAX_LOCAL_GOOGLE_TIME_OFFSET, MULTIPLE_PROJECT_FOLDERS_FOUND_RC, SCOPES_NOT_AUTHORIZED_RC
from gam.cmd.oauth import _getValidateLoginHint
from gam.cmd.oauth import getScopesFromUser

try:
    from gam.cmd import yubikey
except ImportError:
    yubikey = None  # Optional: requires yubikey-manager


from urllib.parse import quote, urlencode

import string
from gam.util.uid import convertUIDtoEmailAddress
LOWERNUMERIC_CHARS = string.ascii_lowercase + string.digits

def getCRMService(login_hint):
  scopes = [API.CLOUD_PLATFORM_SCOPE]
  client_id = GAM_PROJECT_CREATION_CLIENT_ID
  client_secret = 'qM3dP8f_4qedwzWQE1VR4zzU'
  credentials = Credentials.from_client_secrets(
    client_id,
    client_secret,
    scopes=scopes,
    access_type='online',
    login_hint=login_hint,
    open_browser=not GC.Values[GC.NO_BROWSER])
  httpObj = transportAuthorizedHttp(credentials, http=getHttpObj())
  return (httpObj, getAPIService(API.CLOUDRESOURCEMANAGER, httpObj))

def enableGAMProjectAPIs(httpObj, projectId, login_hint, checkEnabled, i=0, count=0):
  apis = API.PROJECT_APIS[:]
  projectName = f'projects/{projectId}'
  serveu = getAPIService(API.SERVICEUSAGE, httpObj)
  status = True
  if checkEnabled:
    try:
      services = callGAPIpages(serveu.services(), 'list', 'services',
                               throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                               parent=projectName, filter='state:ENABLED',
                               fields='nextPageToken,services(name)')
      Act.Set(Act.CHECK)
      jcount = len(services)
      entityPerformActionNumItems([Ent.PROJECT, projectId], jcount, Ent.API, i, count)
      Ind.Increment()
      j = 0
      for service in sorted(services, key=lambda k: k['name']):
        j += 1
        if 'name' in service:
          serviceName = service['name'].split('/')[-1]
          if serviceName in apis:
            printEntityKVList([Ent.API, serviceName], ['Already enabled'], j, jcount)
            apis.remove(serviceName)
          else:
            printEntityKVList([Ent.API, serviceName], ['Already enabled (non-GAM which is fine)'], j, jcount)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.PROJECT, projectId], str(e), i, count)
      status = False
  jcount = len(apis)
  if status and jcount > 0:
    Act.Set(Act.ENABLE)
    entityPerformActionNumItems([Ent.PROJECT, projectId], jcount, Ent.API, i, count)
    failed = 0
    Ind.Increment()
    j = 0
    for api in apis:
      j += 1
      serviceName = f'projects/{projectId}/services/{api}'
      while True:
        try:
          callGAPI(serveu.services(), 'enable',
                   throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                   retryReasons=[GAPI.INTERNAL_ERROR],
                   name=serviceName)
          entityActionPerformed([Ent.API, api], j, jcount)
          break
        except GAPI.failedPrecondition as e:
          entityActionFailedWarning([Ent.API, api], str(e), j, jcount)
          readStdin(Msg.ACCEPT_CLOUD_TOS.format(login_hint))
        except (GAPI.forbidden, GAPI.permissionDenied, GAPI.internalError) as e:
          entityActionFailedWarning([Ent.API, api], str(e), j, jcount)
          failed += 1
          break
    Ind.Decrement()
    if not checkEnabled:
      status = failed <= 2
    else:
      status = failed == 0
  return status

# gam enable apis [auto|manual]
def doEnableAPIs():
  automatic = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'auto':
      automatic = True
    elif myarg == 'manual':
      automatic = False
    else:
      unknownArgumentExit()
  request = get_adc_request()
  try:
    _, projectId = google.auth.default(scopes=[API.IAM_SCOPE], request=request)
  except (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError):
    projectId = readStdin(Msg.WHAT_IS_YOUR_PROJECT_ID).strip()
  while automatic is None:
    a_or_m = readStdin(Msg.ENABLE_PROJECT_APIS_AUTOMATICALLY_OR_MANUALLY).strip().lower()
    if a_or_m.startswith('a'):
      automatic = True
      break
    if a_or_m.startswith('m'):
      automatic = False
      break
    writeStdout(Msg.PLEASE_ENTER_A_OR_M)
  if automatic:
    login_hint = _getValidateLoginHint(None)
    httpObj, _ = getCRMService(login_hint)
    enableGAMProjectAPIs(httpObj, projectId, login_hint, True)
  else:
    apis = API.PROJECT_APIS[:]
    chunk_size = 20
    writeStdout('Using an account with project access, please use ALL of these URLs to enable 20 APIs at a time:\n\n')
    for chunk in range(0, len(apis), chunk_size):
      apiid = ",".join(apis[chunk:chunk+chunk_size])
      url = f'https://console.cloud.google.com/apis/enableflow?apiid={apiid}&project={projectId}'
      writeStdout(f'    {url}\n\n')

def _waitForSvcAcctCompletion(i):
  sleep_time = i*5
  if i > 3:
    sys.stdout.write(Msg.WAITING_FOR_ITEM_CREATION_TO_COMPLETE_SLEEPING.format(Ent.Singular(Ent.SVCACCT), sleep_time))
  time.sleep(sleep_time)

def _grantRotateRights(iam, projectId, service_account, account_type='serviceAccount'):
  body = {'policy': {'bindings': [{'role': 'roles/iam.serviceAccountKeyAdmin',
                                   'members': [f'{account_type}:{service_account}']}]}}
  maxRetries = 10
  kvList = [Ent.PROJECT, projectId, Ent.SVCACCT, service_account]
  printEntityMessage(kvList, Msg.GRANTING_RIGHTS_TO_ROTATE_ITS_OWN_PRIVATE_KEY.format('Granting'))
  for retry in range(1, maxRetries+1):
    try:
      callGAPI(iam.projects().serviceAccounts(), 'setIamPolicy',
               throwReasons=[GAPI.INVALID_ARGUMENT],
               resource=f'projects/{projectId}/serviceAccounts/{service_account}', body=body)
      printEntityMessage(kvList, Msg.GRANTING_RIGHTS_TO_ROTATE_ITS_OWN_PRIVATE_KEY.format('Granted'))
      return True
    except GAPI.invalidArgument as e:
      entityActionFailedWarning(kvList, str(e))
      if 'does not exist' not in str(e) or retry == maxRetries:
        return False
      _waitForSvcAcctCompletion(retry)
    except Exception as e:
      entityActionFailedWarning(kvList, str(e))
      return False

def _createOauth2serviceJSON(httpObj, projectInfo, svcAcctInfo, create_key=True):
  iam = getAPIService(API.IAM, httpObj)
  try:
    service_account = callGAPI(iam.projects().serviceAccounts(), 'create',
                               throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.NOT_FOUND,
                                             GAPI.PERMISSION_DENIED, GAPI.ALREADY_EXISTS],
                               name=f'projects/{projectInfo["projectId"]}',
                               body={'accountId': svcAcctInfo['name'],
                                     'serviceAccount': {'displayName': svcAcctInfo['displayName'],
                                                        'description': svcAcctInfo['description']}})
    entityActionPerformed([Ent.PROJECT, projectInfo['projectId'], Ent.SVCACCT, service_account['name'].rsplit('/', 1)[-1]])
  except (GAPI.failedPrecondition, GAPI.notFound, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.PROJECT, projectInfo['projectId']], str(e))
    return False
  except GAPI.alreadyExists as e:
    entityActionFailedWarning([Ent.PROJECT, projectInfo['projectId'], Ent.SVCACCT, svcAcctInfo['name']], str(e))
    writeStderr(Msg.RERUN_THE_COMMAND_AND_SPECIFY_A_NEW_SANAME)
    return False
  GM.Globals[GM.SVCACCT_SCOPES_DEFINED] = False
  if create_key and not doProcessSvcAcctKeys(mode='retainexisting', iam=iam,
                                             projectId=service_account['projectId'],
                                             clientEmail=service_account['email'],
                                             clientId=service_account['uniqueId']):
    return False
  sa_email = service_account['name'].rsplit('/', 1)[-1]
  return _grantRotateRights(iam, projectInfo['projectId'], sa_email)

def _createClientSecretsOauth2service(httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key=True):
  def _checkClientAndSecret(csHttpObj, client_id, client_secret):
    post_data = {'client_id': client_id, 'client_secret': client_secret,
                 'code': 'ThisIsAnInvalidCodeOnlyBeingUsedToTestIfClientAndSecretAreValid',
                 'redirect_uri': 'http://127.0.0.1:8080', 'grant_type': 'authorization_code'}
    _, content = csHttpObj.request(API.GOOGLE_OAUTH2_TOKEN_ENDPOINT, 'POST', urlencode(post_data),
                                   headers={'Content-type': 'application/x-www-form-urlencoded'})
    try:
      content = json.loads(content)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      sys.stderr.write(f'{str(e)}: {content}')
      return False
    if 'error' not in content or 'error_description' not in content:
      sys.stderr.write(f'Unknown error: {content}\n')
      return False
    if content['error'] == 'invalid_grant':
      return True
    if content['error_description'] == 'The OAuth client was not found.':
      sys.stderr.write(Msg.IS_NOT_A_VALID_CLIENT_ID.format(client_id))
      return False
    if content['error_description'] == 'Unauthorized':
      sys.stderr.write(Msg.IS_NOT_A_VALID_CLIENT_SECRET.format(client_secret))
      return False
    sys.stderr.write(f'Unknown error: {content}\n')
    return False

  if not enableGAMProjectAPIs(httpObj, projectInfo['projectId'], login_hint, False):
    return
  sys.stdout.write(Msg.SETTING_GAM_PROJECT_CONSENT_SCREEN_CREATING_CLIENT)
  console_url = f'https://console.cloud.google.com/auth/clients?project={projectInfo["projectId"]}&authuser={login_hint}'
  csHttpObj = getHttpObj()
  while True:
    sys.stdout.write(Msg.CREATE_CLIENT_INSTRUCTIONS.format(console_url, appInfo['applicationTitle'], appInfo['supportEmail']))
    client_id = readStdin(Msg.ENTER_YOUR_CLIENT_ID).strip()
    if not client_id:
      client_id = readStdin('').strip()
    client_secret = readStdin(Msg.ENTER_YOUR_CLIENT_SECRET).strip()
    if not client_secret:
      client_secret = readStdin('').strip()
    client_valid = _checkClientAndSecret(csHttpObj, client_id, client_secret)
    if client_valid:
      break
    sys.stdout.write('\n')
  cs_data = f'''{{
    "installed": {{
        "auth_provider_x509_cert_url": "{API.GOOGLE_AUTH_PROVIDER_X509_CERT_URL}",
        "auth_uri": "{API.GOOGLE_OAUTH2_ENDPOINT}",
        "client_id": "{client_id}",
        "client_secret": "{client_secret}",
        "created_by": "{login_hint}",
        "project_id": "{projectInfo['projectId']}",
        "token_uri": "{API.GOOGLE_OAUTH2_TOKEN_ENDPOINT}"
    }}
}}'''
  writeFile(GC.Values[GC.CLIENT_SECRETS_JSON], cs_data, continueOnError=False)
  sys.stdout.write(Msg.TRUST_GAM_CLIENT_ID.format(GAM, client_id))
  readStdin('')
  if not _createOauth2serviceJSON(httpObj, projectInfo, svcAcctInfo, create_key):
    return
  sys.stdout.write(Msg.YOUR_GAM_PROJECT_IS_CREATED_AND_READY_TO_USE)

def _getProjects(crm, pfilter, returnNF=False):
  try:
    projects = callGAPIpages(crm.projects(), 'search', 'projects',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                             query=pfilter)
    if projects:
      return projects
    if (not pfilter) or pfilter == GAM_PROJECT_FILTER:
      return []
    if pfilter.startswith('id:'):
      projects = [callGAPI(crm.projects(), 'get',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                           name=f'projects/{pfilter[3:]}')]
      if projects or not returnNF:
        return projects
    return []
  except (GAPI.badRequest, GAPI.invalidArgument) as e:
    entityActionFailedExit([Ent.PROJECT, pfilter], str(e))
  except GAPI.permissionDenied:
    if (not pfilter) or (not pfilter.startswith('id:')) or (not returnNF):
      return []
  return [{'projectId': pfilter[3:], 'state': 'NF'}]

def _checkProjectFound(project, i, count):
  if project.get('state', '') != 'NF':
    return True
  entityActionFailedWarning([Ent.PROJECT, project['projectId']], Msg.DOES_NOT_EXIST, i, count)
  return False

def convertGCPFolderNameToID(parent, crm):
  folders = callGAPIpages(crm.folders(), 'search', 'folders',
                          query=f'displayName="{parent}"')
  if not folders:
    entityActionFailedExit([Ent.PROJECT_FOLDER, parent], Msg.NOT_FOUND)
  jcount = len(folders)
  if jcount > 1:
    entityActionNotPerformedWarning([Ent.PROJECT_FOLDER, parent],
                                    Msg.PLEASE_SELECT_ENTITY_TO_PROCESS.format(jcount, Ent.Plural(Ent.PROJECT_FOLDER), 'use in create', 'parent <String>'))
    Ind.Increment()
    j = 0
    for folder in folders:
      j += 1
      printKeyValueListWithCount(['Name', folder['name'], 'ID', folder['displayName']], j, jcount)
    Ind.Decrement()
    systemErrorExit(MULTIPLE_PROJECT_FOLDERS_FOUND_RC, None)
  return folders[0]['name']

PROJECTID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$')
PROJECTID_FORMAT_REQUIRED = '[a-z][a-z0-9-]{4,28}[a-z0-9]'
def _checkProjectId(projectId):
  if not PROJECTID_PATTERN.match(projectId):
    Cmd.Backup()
    invalidArgumentExit(PROJECTID_FORMAT_REQUIRED)

PROJECTNAME_PATTERN = re.compile('^[a-zA-Z0-9 '+"'"+'"!-]{4,30}$')
PROJECTNAME_FORMAT_REQUIRED = '[a-zA-Z0-9 \'"!-]{4,30}'
def _checkProjectName(projectName):
  if not PROJECTNAME_PATTERN.match(projectName):
    Cmd.Backup()
    invalidArgumentExit(PROJECTNAME_FORMAT_REQUIRED)

def _getSvcAcctInfo(myarg, svcAcctInfo):
  if myarg == 'saname':
    svcAcctInfo['name'] = getString(Cmd.OB_STRING, minLen=6, maxLen=30)
    _checkProjectId(svcAcctInfo['name'])
  elif myarg == 'sadisplayname':
    svcAcctInfo['displayName'] = getString(Cmd.OB_STRING, maxLen=100)
  elif myarg == 'sadescription':
    svcAcctInfo['description'] = getString(Cmd.OB_STRING, maxLen=256)
  else:
    return False
  return True

def _getAppInfo(myarg, appInfo):
  if myarg == 'appname':
    appInfo['applicationTitle'] = getString(Cmd.OB_STRING)
  elif myarg == 'supportemail':
    appInfo['supportEmail'] = getEmailAddress(noUid=True)
  else:
    return False
  return True

def _generateProjectSvcAcctId(prefix):
  return f'{prefix}-{"".join(random.choice(LOWERNUMERIC_CHARS) for _ in range(5))}'

def _getLoginHintProjectInfo(createCmd):
  login_hint = None
  create_key = True
  appInfo = {'applicationTitle': '', 'supportEmail': ''}
  projectInfo = {'projectId': '', 'parent': '', 'name': ''}
  svcAcctInfo = {'name': '', 'displayName': '', 'description': ''}
  if not Cmd.PeekArgumentPresent(['admin', 'appname', 'supportemail', 'project', 'parent',
                                  'projectname', 'saname', 'sadisplayname', 'sadescription',
                                  'algorithm', 'localkeysize', 'validityhours', 'yubikey', 'nokey']):
    login_hint = getString(Cmd.OB_EMAIL_ADDRESS, optional=True)
    if login_hint and login_hint.find('@') == -1:
      Cmd.Backup()
      login_hint = None
    projectInfo['projectId'] = getString(Cmd.OB_STRING, optional=True, minLen=6, maxLen=30).strip()
    if projectInfo['projectId']:
      _checkProjectId(projectInfo['projectId'])
    checkForExtraneousArguments()
  else:
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'admin':
        login_hint = getEmailAddress(noUid=True)
      elif myarg == 'nokey':
        create_key = False
      elif myarg == 'project':
        projectInfo['projectId'] = getString(Cmd.OB_STRING, minLen=6, maxLen=30)
        _checkProjectId(projectInfo['projectId'])
      elif createCmd and myarg == 'parent':
        projectInfo['parent'] = getString(Cmd.OB_STRING)
      elif myarg == 'projectname':
        projectInfo['name'] = getString(Cmd.OB_STRING, minLen=4, maxLen=30)
        _checkProjectName(projectInfo['name'])
      elif _getSvcAcctInfo(myarg, svcAcctInfo):
        pass
      elif _getAppInfo(myarg, appInfo):
        pass
      elif myarg in {'algorithm', 'localkeysize', 'validityhours', 'yubikey'}:
        Cmd.Backup()
        break
      else:
        unknownArgumentExit()
  if not projectInfo['projectId']:
    if createCmd:
      projectInfo['projectId'] = _generateProjectSvcAcctId('gam-project')
    else:
      projectInfo['projectId'] = readStdin(Msg.WHAT_IS_YOUR_PROJECT_ID).strip()
      if not PROJECTID_PATTERN.match(projectInfo['projectId']):
        systemErrorExit(USAGE_ERROR_RC, f'{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]} {Cmd.OB_PROJECT_ID}: {Msg.EXPECTED} <{PROJECTID_FORMAT_REQUIRED}>')
  if not projectInfo['name']:
    projectInfo['name'] = 'GAM Project' if not GC.Values[GC.USE_PROJECTID_AS_NAME] else projectInfo['projectId']
  if not svcAcctInfo['name']:
    svcAcctInfo['name'] = projectInfo['projectId']
  if not svcAcctInfo['displayName']:
    svcAcctInfo['displayName'] = projectInfo['name']
  if not svcAcctInfo['description']:
    svcAcctInfo['description'] = svcAcctInfo['displayName']
  login_hint = _getValidateLoginHint(login_hint, projectInfo['projectId'])
  if not appInfo['applicationTitle']:
    appInfo['applicationTitle'] = 'GAM' if not GC.Values[GC.USE_PROJECTID_AS_NAME] else projectInfo['projectId']
  if not appInfo['supportEmail']:
    appInfo['supportEmail'] = login_hint
  httpObj, crm = getCRMService(login_hint)
  if projectInfo['parent'] and not projectInfo['parent'].startswith('organizations/') and not projectInfo['parent'].startswith('folders/'):
    projectInfo['parent'] = convertGCPFolderNameToID(projectInfo['parent'], crm)
  projects = _getProjects(crm, f'id:{projectInfo["projectId"]}')
  if not createCmd:
    if not projects:
      entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], Msg.DOES_NOT_EXIST)
    if projects[0]['state'] != 'ACTIVE':
      entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], Msg.NOT_ACTIVE)
  else:
    if projects:
      entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], Msg.DUPLICATE)
  return (crm, httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key)

def _getCurrentProjectId():
  jsonData = readFile(GC.Values[GC.OAUTH2SERVICE_JSON], continueOnError=True, displayError=False)
  if jsonData:
    try:
      return json.loads(jsonData)['project_id']
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
      pass
  jsonData = readFile(GC.Values[GC.CLIENT_SECRETS_JSON], continueOnError=True, displayError=True)
  if not jsonData:
    invalidClientSecretsJsonExit(Msg.NO_DATA)
  try:
    return json.loads(jsonData)['installed']['project_id']
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    invalidClientSecretsJsonExit(str(e))

GAM_PROJECT_FILTER = 'id:gam-project-*'
PROJECTID_FILTER_REQUIRED = '<ProjectIDEntity>'
PROJECTS_CREATESVCACCT_OPTIONS = {'saname', 'sadisplayname', 'sadescription'}
PROJECTS_DELETESVCACCT_OPTIONS = {'saemail', 'saname', 'sauniqueid'}
PROJECTS_PRINTSHOW_OPTIONS = {'showsakeys', 'showiampolicies', 'onememberperrow', 'states', 'todrive', 'delimiter', 'formatjson', 'quotechar'}

def _getLoginHintProjects(createSvcAcctCmd=False, deleteSvcAcctCmd=False, printShowCmd=False, readOnly=False):
  if checkArgumentPresent(['admin']):
    login_hint = getEmailAddress(noUid=True)
  else:
    login_hint = getString(Cmd.OB_EMAIL_ADDRESS, optional=True)
  if login_hint and login_hint.find('@') == -1:
    Cmd.Backup()
    login_hint = None
  if readOnly and login_hint and login_hint != _getAdminEmail():
    readOnly = False
  projectIds = None
  pfilter = getString(Cmd.OB_STRING, optional=True)
  if not pfilter:
    pfilter = 'current' if not printShowCmd else GAM_PROJECT_FILTER
  elif printShowCmd and pfilter in PROJECTS_PRINTSHOW_OPTIONS:
    pfilter = GAM_PROJECT_FILTER
    Cmd.Backup()
  elif createSvcAcctCmd and pfilter in PROJECTS_CREATESVCACCT_OPTIONS:
    pfilter = 'current'
    Cmd.Backup()
  elif deleteSvcAcctCmd and pfilter in PROJECTS_DELETESVCACCT_OPTIONS:
    pfilter = 'current'
    Cmd.Backup()
  elif printShowCmd and pfilter.lower() == 'all':
    pfilter = None
  elif pfilter.lower() == 'current':
    pfilter = 'current'
  elif pfilter.lower() == 'gam':
    pfilter = GAM_PROJECT_FILTER
  elif pfilter.lower() == 'filter':
    pfilter = getString(Cmd.OB_STRING)
  elif pfilter.lower() == 'select':
    projectIds = getEntityList(Cmd.OB_PROJECT_ID_ENTITY, False)
    projectId = None
  elif PROJECTID_PATTERN.match(pfilter):
    pfilter = f'id:{pfilter}'
  elif pfilter.startswith('id:') and PROJECTID_PATTERN.match(pfilter[3:]):
    pass
  else:
    Cmd.Backup()
    invalidArgumentExit(['', 'all|'][printShowCmd]+PROJECTID_FILTER_REQUIRED)
  if not printShowCmd and not createSvcAcctCmd and not deleteSvcAcctCmd:
    checkForExtraneousArguments()
  if projectIds is None:
    if pfilter in {'current', 'id:current'}:
      projectId = _getCurrentProjectId()
    else:
      projectId = f'filter {pfilter or "all"}'
  login_hint = _getValidateLoginHint(login_hint, projectId)
  crm = None
  if readOnly:
    _, crm = buildGAPIServiceObject(API.CLOUDRESOURCEMANAGER, None)
    if crm:
      httpObj = crm._http
  if not crm:
    httpObj, crm = getCRMService(login_hint)
  if projectIds is None:
    if pfilter in {'current', 'id:current'}:
      if not printShowCmd:
        projects = [{'projectId': projectId}]
      else:
        projects = _getProjects(crm, f'id:{projectId}', returnNF=True)
    else:
      projects = _getProjects(crm, pfilter, returnNF=printShowCmd)
  else:
    projects = []
    for projectId in projectIds:
      projects.extend(_getProjects(crm, f'id:{projectId}', returnNF=True))
  return (crm, httpObj, login_hint, projects)

def _checkForExistingProjectFiles(projectFiles):
  for a_file in projectFiles:
    if os.path.exists(a_file):
      systemErrorExit(JSON_ALREADY_EXISTS_RC, Msg.AUTHORIZATION_FILE_ALREADY_EXISTS.format(a_file, Act.ToPerform()))

def getCRMOrgId(forceSearch=False):
  if not GC.Values[GC.GCP_ORG_ID] or forceSearch:
    setTrueCustomerId()
    _, crm = buildGAPIServiceObject(API.CLOUDRESOURCEMANAGER, None)
    results = callGAPI(crm.organizations(), 'search',
                       query=f'directorycustomerid:{GC.Values[GC.CUSTOMER_ID]}',
                       pageSize=1, fields='organizations/name')
    orgs = results.get('organizations')
    if not orgs:
      # return nothing and let calling API deal with it
      # since caller knows what GCP role would serve best
      return None
    return orgs[0].get('name')
  return GC.Values[GC.GCP_ORG_ID]


# gam info gcporgid
def doInfoGCPOrgId():
  checkForExtraneousArguments()
  writeStdout(f'{getCRMOrgId(forceSearch=True)}\n')

def getGCPOrgId(crm, login_hint, login_domain):
  if not GC.Values[GC.GCP_ORG_ID]:
    try:
      results = callGAPI(crm.organizations(), 'search',
                         throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                         query=f'domain:{login_domain}',
                         pageSize=1, fields='organizations/name')
      return results['organizations'][0]['name']
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.USER, login_hint, Ent.DOMAIN, login_domain], str(e))
    except (KeyError, IndexError):
      systemErrorExit(3, Msg.YOU_HAVE_NO_RIGHTS_TO_CREATE_PROJECTS_AND_YOU_ARE_NOT_A_SUPER_ADMIN)
  return GC.Values[GC.GCP_ORG_ID]

# gam create gcpfolder <String>
# gam create gcpfolder [admin <EmailAddress] folder <String>
def doCreateGCPFolder():
  login_hint = None
  if not Cmd.PeekArgumentPresent(['admin', 'folder']):
    name = getString(Cmd.OB_STRING)
    checkForExtraneousArguments()
  else:
    name = ''
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'admin':
        login_hint = getEmailAddress(noUid=True)
      elif myarg == 'folder':
        name = getString(Cmd.OB_STRING)
      else:
        unknownArgumentExit()
    if not name:
      missingChoiceExit('folder')
  login_hint = _getValidateLoginHint(login_hint)
  login_domain = getEmailAddressDomain(login_hint)
  _, crm = getCRMService(login_hint)
  organization = getGCPOrgId(crm, login_hint, login_domain)
  try:
    result = callGAPI(crm.folders(), 'create',
                      throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                      body={'parent': organization, 'displayName': name})
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedExit([Ent.USER, login_hint, Ent.GCP_FOLDER, name], str(e))
  entityActionPerformed([Ent.USER, login_hint, Ent.GCP_FOLDER, name, Ent.GCP_FOLDER_NAME, result['name']])

# gam create project [<EmailAddress>] [<ProjectID>]
# gam create project [admin <EmailAddress>] [project <ProjectID>]
#	[appname <String>] [supportemail <EmailAddress>]
#	[projectname <ProjectName>] [parent <String>]
#	[saname <ServiceAccountName>] [sadisplayname <ServiceAccountDisplayName>] [sadescription <ServiceAccountDescription>]
#	[(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	 (localkeysize 1024|2048|4096 [validityhours <Number>])|
#	 (yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)|
#	 nokey]
def doCreateProject():
  _checkForExistingProjectFiles([GC.Values[GC.OAUTH2SERVICE_JSON], GC.Values[GC.CLIENT_SECRETS_JSON]])
  sys.stdout.write(Msg.TRUST_GAM_CLIENT_ID.format(GAM_PROJECT_CREATION, GAM_PROJECT_CREATION_CLIENT_ID))
  readStdin('')
  crm, httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key = _getLoginHintProjectInfo(True)
  login_domain = getEmailAddressDomain(login_hint)
  body = {'projectId': projectInfo['projectId'], 'displayName': projectInfo['name']}
  if projectInfo['parent']:
    body['parent'] = projectInfo['parent']
  while True:
    create_again = False
    sys.stdout.write(Msg.CREATING_PROJECT.format(body['displayName']))
    try:
      create_operation = callGAPI(crm.projects(), 'create',
                                  throwReasons=[GAPI.BAD_REQUEST, GAPI.ALREADY_EXISTS,
                                                GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                                  body=body)
    except (GAPI.badRequest, GAPI.alreadyExists, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
      entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], str(e))
    operation_name = create_operation['name']
    time.sleep(5) # Google recommends always waiting at least 5 seconds
    for i in range(1, 10):
      sys.stdout.write(Msg.CHECKING_PROJECT_CREATION_STATUS)
      status = callGAPI(crm.operations(), 'get',
                        name=operation_name)
      if 'error' in status:
        if status['error'].get('message', '') == 'No permission to create project in organization':
          sys.stdout.write(Msg.NO_RIGHTS_GOOGLE_CLOUD_ORGANIZATION)
          organization = getGCPOrgId(crm, login_hint, login_domain)
          org_policy = callGAPI(crm.organizations(), 'getIamPolicy',
                                resource=organization)
          if 'bindings' not in org_policy:
            org_policy['bindings'] = []
            sys.stdout.write(Msg.LOOKS_LIKE_NO_ONE_HAS_RIGHTS_TO_YOUR_GOOGLE_CLOUD_ORGANIZATION_ATTEMPTING_TO_GIVE_YOU_CREATE_RIGHTS)
          else:
            sys.stdout.write(Msg.THE_FOLLOWING_RIGHTS_SEEM_TO_EXIST)
            for a_policy in org_policy['bindings']:
              if 'role' in a_policy:
                sys.stdout.write(f'  Role: {a_policy["role"]}\n')
              if 'members' in a_policy:
                sys.stdout.write('  Members:\n')
                for member in a_policy['members']:
                  sys.stdout.write(f'    {member}\n')
          my_role = 'roles/resourcemanager.projectCreator'
          sys.stdout.write(Msg.GIVING_LOGIN_HINT_THE_CREATOR_ROLE.format(login_hint, my_role))
          org_policy['bindings'].append({'role': my_role, 'members': [f'user:{login_hint}']})
          callGAPI(crm.organizations(), 'setIamPolicy',
                   resource=organization, body={'policy': org_policy})
          create_again = True
          break
        try:
          if status['error']['details'][0]['violations'][0]['description'] == 'Callers must accept Terms of Service':
            readStdin(Msg.ACCEPT_CLOUD_TOS.format(login_hint))
            create_again = True
            break
        except (IndexError, KeyError):
          pass
        systemErrorExit(1, str(status)+'\n')
      if status.get('done', False):
        break
      sleep_time = min(2 ** i, 60)
      sys.stdout.write(Msg.PROJECT_STILL_BEING_CREATED_SLEEPING.format(sleep_time))
      time.sleep(sleep_time)
    if create_again:
      continue
    if not status.get('done', False):
      systemErrorExit(1, Msg.FAILED_TO_CREATE_PROJECT.format(status))
    elif 'error' in status:
      systemErrorExit(2, status['error']+'\n')
    break
# Try to set policy on project to allow Service Account Key Upload
#  orgp = getAPIService(API.ORGPOLICY, httpObj)
#  projectParent = f"projects/{projectInfo['projectId']}"
#  policyName = f'{projectParent}/policies/iam.managed.disableServiceAccountKeyUpload'
#  try:
#    result = callGAPI(orgp.projects().policies(), 'get',
#                      throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
#                      name=policyName)
#    if result['spec']['rules'][0]['enforce']:
#      callGAPI(orgp.projects().policies(), 'patch',
#               throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
#               name=policyName, body={'spec': {'rules': [{'enforce': False}]}}, updateMask='policy.spec')
#  except GAPI.notFound:
#    callGAPI(orgp.projects().policies(), 'create',
#             throwReasons=[GAPI.BAD_REQUEST, GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
#             parent=projectParent, body={'name': policyName, 'spec': {'rules': [{'enforce': False}]}})
#  except (GAPI.badRequest, GAPI.failedPrecondition, GAPI.permissionDenied):
#    pass
# Create client_secrets.json and oauth2service.json
  _createClientSecretsOauth2service(httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key)

# gam use project [<EmailAddress>] [<ProjectID>]
# gam use project [admin <EmailAddress>] [project <ProjectID>]
#	[appname <String>] [supportemail <EmailAddress>]
#	[saname <ServiceAccountName>] [sadisplayname <ServiceAccountDisplayName>] [sadescription <ServiceAccountDescription>]
#	[(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	 (localkeysize 1024|2048|4096 [validityhours <Number>])|
#	 (yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)]
def doUseProject():
  _checkForExistingProjectFiles([GC.Values[GC.OAUTH2SERVICE_JSON], GC.Values[GC.CLIENT_SECRETS_JSON]])
  _, httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key = _getLoginHintProjectInfo(False)
  _createClientSecretsOauth2service(httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key)

# gam update project [[admin] <EmailAddress>] [<ProjectIDEntity>]
def doUpdateProject():
  _, httpObj, login_hint, projects = _getLoginHintProjects()
  count = len(projects)
  entityPerformActionNumItems([Ent.USER, login_hint], count, Ent.PROJECT)
  Ind.Increment()
  i = 0
  for project in projects:
    i += 1
    if not _checkProjectFound(project, i, count):
      continue
    projectId = project['projectId']
    Act.Set(Act.UPDATE)
    if not enableGAMProjectAPIs(httpObj, projectId, login_hint, True, i, count):
      continue
    iam = getAPIService(API.IAM, httpObj)
    _getSvcAcctData() # needed to read in GM.OAUTH2SERVICE_JSON_DATA
    _grantRotateRights(iam, projectId, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email'])
  Ind.Decrement()

# gam delete project [[admin] <EmailAddress>] [<ProjectIDEntity>]
def doDeleteProject():
  crm, _, login_hint, projects = _getLoginHintProjects()
  count = len(projects)
  entityPerformActionNumItems([Ent.USER, login_hint], count, Ent.PROJECT)
  Ind.Increment()
  i = 0
  for project in projects:
    i += 1
    if not _checkProjectFound(project, i, count):
      continue
    projectId = project['projectId']
    try:
      callGAPI(crm.projects(), 'delete',
               throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
               name=project['name'])
      entityActionPerformed([Ent.PROJECT, projectId])
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
      entityActionFailedWarning([Ent.PROJECT, projectId], str(e))
  Ind.Decrement()

PROJECT_TIMEOBJECTS = ['createTime']
PROJECT_STATE_CHOICE_MAP = {
  'all': {'ACTIVE', 'DELETE_REQUESTED'},
  'active': {'ACTIVE'},
  'deleterequested': {'DELETE_REQUESTED'}
  }

# gam print projects [[admin] <EmailAddress>] [all|<ProjectIDEntity>] [todrive <ToDriveAttribute>*]
#	[states all|active|deleterequested] [showiampolicies 0|1|3 [onememberperrow]]
#	[delimiter <Character>] [formatjson [quotechar <Character>]]
# gam show projects [[admin] <EmailAddress>] [all|<ProjectIDEntity>]
#	[states all|active|deleterequested] [showiampolicies 0|1|3]
def doPrintShowProjects():
  def _getProjectPolicies(crm, project, policyBody, i, count):
    try:
      policy = callGAPI(crm.projects(), 'getIamPolicy',
                        throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        resource=project['name'], body=policyBody)
      return policy
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.PROJECT, project['projectId'], Ent.IAM_POLICY, None], str(e), i, count)
    return {}

  readOnly = not Cmd.ArgumentIsAhead('showiampolicies')
  crm, _, login_hint, projects = _getLoginHintProjects(printShowCmd=True, readOnly=readOnly)
  csvPF = CSVPrintFile(['User', 'projectId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  oneMemberPerRow = False
  showIAMPolicies = -1
  lifecycleStates = PROJECT_STATE_CHOICE_MAP['active']
  policy = None
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'onememberperrow':
      oneMemberPerRow = True
    elif myarg == 'states':
      lifecycleStates = getChoice(PROJECT_STATE_CHOICE_MAP, mapChoice=True)
    elif myarg == 'showiampolicies':
      showIAMPolicies = int(getChoice(['0', '1', '3']))
      policyBody = {'options': {"requestedPolicyVersion": showIAMPolicies}}
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not csvPF:
    count = len(projects)
    entityPerformActionNumItems([Ent.USER, login_hint], count, Ent.PROJECT)
    Ind.Increment()
    i = 0
    for project in projects:
      i += 1
      if not _checkProjectFound(project, i, count):
        continue
      if project['state'] not in lifecycleStates:
        continue
      projectId = project['projectId']
      if showIAMPolicies >= 0:
        policy = _getProjectPolicies(crm, project, policyBody, i, count)
      printEntity([Ent.PROJECT, projectId], i, count)
      Ind.Increment()
      printKeyValueList(['name', project['name']])
      printKeyValueList(['displayName', project['displayName']])
      for field in ['createTime', 'updateTime', 'deleteTime']:
        if field in project:
          printKeyValueList([field, formatLocalTime(project[field])])
      printKeyValueList(['state', project['state']])
      jcount = len(project.get('labels', []))
      if jcount > 0:
        printKeyValueList(['labels', jcount])
        Ind.Increment()
        for k, v in project['labels'].items():
          printKeyValueList([k, v])
        Ind.Decrement()
      if 'parent' in project:
        printKeyValueList(['parent', project['parent']])
      if policy:
        printKeyValueList([Ent.Singular(Ent.IAM_POLICY), ''])
        Ind.Increment()
        bindings = policy.get('bindings', [])
        jcount = len(bindings)
        printKeyValueList(['version', policy['version']])
        printKeyValueList(['bindings', jcount])
        Ind.Increment()
        j = 0
        for binding in bindings:
          j += 1
          printKeyValueListWithCount(['role', binding['role']], j, jcount)
          Ind.Increment()
          for member in binding.get('members', []):
            printKeyValueList(['member', member])
          if 'condition' in binding:
            printKeyValueList(['condition', ''])
            Ind.Increment()
            for k, v in binding['condition'].items():
              printKeyValueList([k, v])
            Ind.Decrement()
          Ind.Decrement()
        Ind.Decrement()
        Ind.Decrement()
      Ind.Decrement()
    Ind.Decrement()
  else:
    if not FJQC.formatJSON:
      csvPF.AddTitles(['projectId', 'name', 'displayName', 'createTime', 'updateTime', 'deleteTime', 'state'])
      csvPF.SetSortAllTitles()
    count = len(projects)
    i = 0
    for project in projects:
      i += 1
      if not _checkProjectFound(project, i, count):
        continue
      if project['state'] not in lifecycleStates:
        continue
      projectId = project['projectId']
      if showIAMPolicies >= 0:
        policy = _getProjectPolicies(crm, project, policyBody, i, count)
      if FJQC.formatJSON:
        if policy is not None:
          project['policy'] = policy
        row = flattenJSON(project, flattened={'User': login_hint}, timeObjects=PROJECT_TIMEOBJECTS)
        if csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'User': login_hint, 'projectId': projectId,
                                  'JSON': json.dumps(cleanJSON(project),
                                                     ensure_ascii=False, sort_keys=True)})
        continue
      row = flattenJSON(project, flattened={'User': login_hint}, timeObjects=PROJECT_TIMEOBJECTS)
      if not policy:
        csvPF.WriteRowTitles(row)
        continue
      row[f'policy{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}version'] = policy['version']
      for binding in policy.get('bindings', []):
        prow = row.copy()
        prow[f'policy{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}role'] = binding['role']
        if 'condition' in binding:
          for k, v in binding['condition'].items():
            prow[f'policy{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}condition{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = v
        members = binding.get('members', [])
        if not oneMemberPerRow:
          prow[f'policy{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}members'] = delimiter.join(members)
          csvPF.WriteRowTitles(prow)
        else:
          for member in members:
            mrow = prow.copy()
            mrow[f'policy{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}member'] = member
            csvPF.WriteRowTitles(mrow)
    csvPF.writeCSVfile('Projects')

# gam info currentprojectid
def doInfoCurrentProjectId():
  checkForExtraneousArguments()
  printEntity([Ent.PROJECT_ID, _getCurrentProjectId()])

# gam create svcacct [[admin] <EmailAddress>] [<ProjectIDEntity>]
#	[saname <ServiceAccountName>] [sadisplayname <ServiceAccountDisplayName>] [sadescription <ServiceAccountDescription>]
#	[(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	 (localkeysize 1024|2048|4096 [validityhours <Number>])|
#	 (yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)]
def doCreateSvcAcct():
  _checkForExistingProjectFiles([GC.Values[GC.OAUTH2SERVICE_JSON]])
  _, httpObj, login_hint, projects = _getLoginHintProjects(createSvcAcctCmd=True)
  svcAcctInfo = {'name': '', 'displayName': '', 'description': ''}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getSvcAcctInfo(myarg, svcAcctInfo):
      pass
    else:
      unknownArgumentExit()
  if not svcAcctInfo['name']:
    svcAcctInfo['name'] = _generateProjectSvcAcctId('gam-svcacct')
  if not svcAcctInfo['displayName']:
    svcAcctInfo['displayName'] = svcAcctInfo['name']
  if not svcAcctInfo['description']:
    svcAcctInfo['description'] = svcAcctInfo['displayName']
  count = len(projects)
  entityPerformActionSubItemModifierNumItems([Ent.USER, login_hint], Ent.SVCACCT, Act.MODIFIER_TO, count, Ent.PROJECT)
  Ind.Increment()
  i = 0
  for project in projects:
    i += 1
    if not _checkProjectFound(project, i, count):
      continue
    projectInfo = {'projectId': project['projectId']}
    _createOauth2serviceJSON(httpObj, projectInfo, svcAcctInfo)
  Ind.Decrement()

# gam delete svcacct [[admin] <EmailAddress>] [<ProjectIDEntity>]
#	(saemail <ServiceAccountEmail>)|(saname <ServiceAccountName>)|(sauniqueid <ServiceAccountUniqueID>)
def doDeleteSvcAcct():
  _, httpObj, login_hint, projects = _getLoginHintProjects(deleteSvcAcctCmd=True)
  iam = getAPIService(API.IAM, httpObj)
  clientEmail = clientId = clientName = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'saemail':
      clientEmail = getEmailAddress(noUid=True)
      clientName = clientId = None
    elif myarg == 'saname':
      clientName = getString(Cmd.OB_STRING, minLen=6, maxLen=30).strip()
      _checkProjectId(clientName)
      clientEmail = clientId = None
    elif myarg == 'sauniqueid':
      clientId = getInteger(minVal=0)
      clientEmail = clientName = None
    else:
      unknownArgumentExit()
  if not clientEmail and not clientId and not clientName:
    missingArgumentExit('email|name|uniqueid')
  count = len(projects)
  entityPerformActionSubItemModifierNumItems([Ent.USER, login_hint], Ent.SVCACCT, Act.MODIFIER_FROM, count, Ent.PROJECT)
  Ind.Increment()
  i = 0
  for project in projects:
    i += 1
    if not _checkProjectFound(project, i, count):
      continue
    projectId = project['projectId']
    try:
      if clientEmail:
        saName = clientEmail
      elif clientName:
        saName = f'{clientName}@{projectId}.iam.gserviceaccount.com'
      else: #clientId
        saName = clientId
      callGAPI(iam.projects().serviceAccounts(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST],
               name=f'projects/{projectId}/serviceAccounts/{saName}')
      entityActionPerformed([Ent.PROJECT, projectId, Ent.SVCACCT, saName], i, count)
    except (GAPI.notFound, GAPI.badRequest) as e:
      entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, saName], str(e), i, count)
    Ind.Decrement()

def _getSvcAcctKeyProjectClientFields():
  return (GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].get('private_key_id', ''),
          GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'],
          GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email'],
          GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_id'])

# gam <UserTypeEntity> check serviceaccount (scope|scopes <APIScopeURLList>)* [usecolor]
# gam <UserTypeEntity> update serviceaccount (scope|scopes <APIScopeURLList>)* [usecolor]
def checkServiceAccount(users):
  def printMessage(message):
    writeStdout(Ind.Spaces()+message+'\n')

  def printPassFail(description, result):
    writeStdout(Ind.Spaces()+f'{description:73} {result}'+'\n')

  def authorizeScopes(message):
    long_url = ('https://admin.google.com/ac/owl/domainwidedelegation'
                f'?clientScopeToAdd={",".join(sorted(checkScopes))}'
                f'&clientIdToAdd={service_account}&overwriteClientId=true')
    if GC.Values[GC.DOMAIN]:
      long_url += f'&dn={GC.Values[GC.DOMAIN]}'
    long_url += f'&authuser={_getAdminEmail()}'
    short_url = shortenURL(long_url)
    printLine(message.format('', short_url))

  credentials = getSvcAcctCredentials([API.USERINFO_EMAIL_SCOPE], None, forceOauth=True)
  allScopes = API.getSvcAcctScopes(GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY], Act.Get() == Act.UPDATE)
  checkScopesSet = set()
  saScopes = {}
  checkDeprecatedScopes = True
  useColor = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'scope', 'scopes'}:
      checkDeprecatedScopes = False
      for scope in getString(Cmd.OB_API_SCOPE_URL_LIST).lower().replace(',', ' ').split():
        api = API.getSvcAcctScopeAPI(scope)
        if api is not None:
          saScopes.setdefault(api, [])
          saScopes[api].append(scope)
          checkScopesSet.add(scope)
        else:
          invalidChoiceExit(scope, allScopes, True)
    elif myarg == 'usecolor':
      useColor = True
    else:
      unknownArgumentExit()
  if useColor:
    testPass = createGreenText('PASS')
    testFail = createRedText('FAIL')
    testWarn = createYellowText('WARN')
    testDeprecated = createRedText('DEPRECATED')
  else:
    testPass = 'PASS'
    testFail = 'FAIL'
    testWarn = 'WARN'
    testDeprecated = 'DEPRECATED'
  if Act.Get() == Act.CHECK:
    if not checkScopesSet:
      for scope in GM.Globals[GM.SVCACCT_SCOPES].values():
        checkScopesSet.update(scope)
  else:
    if not checkScopesSet:
      scopesList = API.getSvcAcctScopesList(GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY], True)
      selectedScopes = getScopesFromUser(scopesList, False, GM.Globals[GM.SVCACCT_SCOPES] if GM.Globals[GM.SVCACCT_SCOPES_DEFINED] else None)
      if selectedScopes is None:
        return False
      i = 0
      for scope in scopesList:
        if selectedScopes[i] == '*':
          saScopes.setdefault(scope['api'], [])
          if not isinstance(scope['scope'], list):
            saScopes[scope['api']].append(scope['scope'])
            checkScopesSet.add(scope['scope'])
          else:
            saScopes[scope['api']].extend(scope['scope'])
            checkScopesSet.update(scope['scope'])
        elif selectedScopes[i] == 'R':
          saScopes.setdefault(scope['api'], [])
          if 'roscope' not in scope:
            saScopes[scope['api']].append(f'{scope["scope"]}.readonly')
            checkScopesSet.add(f'{scope["scope"]}.readonly')
          else:
            saScopes[scope['api']].append(scope['roscope'])
            checkScopesSet.add(scope['roscope'])
        i += 1
    if API.DRIVE3 in saScopes:
      saScopes[API.DRIVE2] = saScopes[API.DRIVE3]
    GM.Globals[GM.OAUTH2SERVICE_JSON_DATA][API.OAUTH2SA_SCOPES] = saScopes
    writeFile(GC.Values[GC.OAUTH2SERVICE_JSON],
              json.dumps(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA], ensure_ascii=False, indent=2, sort_keys=True),
              continueOnError=False)
  checkScopes = sorted(checkScopesSet)
  jcount = len(checkScopes)
  printMessage(Msg.SYSTEM_TIME_STATUS)
  offsetSeconds, offsetFormatted = getLocalGoogleTimeOffset()
  if offsetSeconds <= MAX_LOCAL_GOOGLE_TIME_OFFSET:
    timeStatus = testPass
  else:
    timeStatus = testFail
  Ind.Increment()
  printPassFail(Msg.YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE.format(GOOGLE_TIMECHECK_LOCATION, offsetFormatted), timeStatus)
  Ind.Decrement()
  oa2 = buildGAPIObject(API.OAUTH2)
  printMessage(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AUTHENTICATION)
  # We are explicitly not doing DwD here, just confirming service account can auth
  auth_error = ''
  try:
    request = transportCreateRequest()
    credentials.refresh(request)
    sa_token_info = callGAPI(oa2, 'tokeninfo', access_token=credentials.token)
    if sa_token_info:
      saTokenStatus = testPass
    else:
      saTokenStatus = testFail
  except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
    handleServerError(e)
  except google.auth.exceptions.RefreshError as e:
    saTokenStatus = testFail
    if isinstance(e.args, tuple):
      e = e.args[0]
    auth_error = ' - '+str(e)
  Ind.Increment()
  printPassFail(f'Authentication{auth_error}', saTokenStatus)
  Ind.Decrement()
  if saTokenStatus == testFail:
    invalidOauth2serviceJsonExit(f'Authentication{auth_error}')
  _getSvcAcctData() # needed to read in GM.OAUTH2SERVICE_JSON_DATA
  if API.IAM not in GM.Globals[GM.SVCACCT_SCOPES]:
    GM.Globals[GM.SVCACCT_SCOPES][API.IAM] = [API.IAM_SCOPE]
  key_type = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].get('key_type', 'default')
  if key_type == 'default':
    printMessage(Msg.SERVICE_ACCOUNT_CHECK_PRIVATE_KEY_AGE)
    _, iam = buildGAPIServiceObject(API.IAM, None)
    currentPrivateKeyId, projectId, _, clientId = _getSvcAcctKeyProjectClientFields()
    name = f'projects/{projectId}/serviceAccounts/{clientId}/keys/{currentPrivateKeyId}'
    Ind.Increment()
    try:
      key = callGAPI(iam.projects().serviceAccounts().keys(), 'get',
                     throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.NOT_FOUND,
                                   GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                     name=name, fields='validAfterTime')
      key_created = arrow.get(key['validAfterTime'])
      key_age = todaysTime()-key_created
      printPassFail(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AGE.format(key_age.days), testWarn if key_age.days > 30 else testPass)
    except GAPI.permissionDenied:
      printMessage(Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
      printPassFail(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AGE.format('UNKNOWN'), testWarn)
    except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
      entityActionFailedWarning([Ent.PROJECT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'],
                                 Ent.SVCACCT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']],
                                str(e))
      printPassFail(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AGE.format('UNKNOWN'), testWarn)
    except GAPI.serviceNotAvailable as e:
      entityActionFailedExit([Ent.PROJECT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'],
                              Ent.SVCACCT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']],
                             str(e))
  else:
    printPassFail(Msg.SERVICE_ACCOUNT_SKIPPING_KEY_AGE_CHECK.format(key_type), testPass)
  Ind.Decrement()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    allScopesPass = True
    user = convertUIDtoEmailAddress(user)
    printKeyValueListWithCount([Msg.DOMAIN_WIDE_DELEGATION_AUTHENTICATION, '',
                                Ent.Singular(Ent.USER), user,
                                Ent.Choose(Ent.SCOPE, jcount), jcount],
                               i, count)
    Ind.Increment()
    j = 0
    for scope in checkScopes:
      j += 1
      # try with and without email scope
      for scopes in [[scope, API.USERINFO_EMAIL_SCOPE], [scope]]:
        try:
          credentials = getSvcAcctCredentials(scopes, user)
          credentials.refresh(request)
          break
        except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
          handleServerError(e)
        except google.auth.exceptions.RefreshError:
          continue
      if credentials.token:
        token_info = callGAPI(oa2, 'tokeninfo', access_token=credentials.token)
        if scope in token_info.get('scope', '').split(' ') and user == token_info.get('email', user).lower():
          scopeStatus = testPass
        else:
          scopeStatus = testFail
          allScopesPass = False
      else:
        scopeStatus = testFail
        allScopesPass = False
      printPassFail(scope, f'{scopeStatus}{currentCount(j, jcount)}')
    Ind.Decrement()
    if checkDeprecatedScopes:
      deprecatedScopes = sorted(API.DEPRECATED_SCOPES)
      jcount = len(deprecatedScopes)
      printKeyValueListWithCount([Msg.DEPRECATED_SCOPES, '',
                                  Ent.Singular(Ent.USER), user,
                                  Ent.Choose(Ent.SCOPE, jcount), jcount],
                                 i, count)
      Ind.Increment()
      j = 0
      for scope in deprecatedScopes:
        j += 1
        # try with and without email scope
        for scopes in [[scope, API.USERINFO_EMAIL_SCOPE], [scope]]:
          try:
            credentials = getSvcAcctCredentials(scopes, user)
            credentials.refresh(request)
            break
          except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
            handleServerError(e)
          except google.auth.exceptions.RefreshError:
            continue
        if credentials.token:
          token_info = callGAPI(oa2, 'tokeninfo', access_token=credentials.token)
          if scope in token_info.get('scope', '').split(' ') and user == token_info.get('email', user).lower():
            scopeStatus = testDeprecated
            allScopesPass = False
          else:
            scopeStatus = testPass
        else:
          scopeStatus = testPass
        printPassFail(scope, f'{scopeStatus}{currentCount(j, jcount)}')
      Ind.Decrement()
    service_account = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_id']
    if allScopesPass:
      if Act.Get() == Act.CHECK:
        printLine(Msg.SCOPE_AUTHORIZATION_PASSED.format(service_account))
      else:
        authorizeScopes(Msg.SCOPE_AUTHORIZATION_UPDATE_PASSED)
    else:
      # Tack on email scope for more accurate checking
      checkScopes.append(API.USERINFO_EMAIL_SCOPE)
      setSysExitRC(SCOPES_NOT_AUTHORIZED_RC)
      authorizeScopes(Msg.SCOPE_AUTHORIZATION_FAILED)
    printBlankLine()

# gam check svcacct <UserTypeEntity> (scope|scopes <APIScopeURLList>)*
# gam update svcacct <UserTypeEntity> (scope|scopes <APIScopeURLList>)*
def doCheckUpdateSvcAcct():
  _, entityList = getEntityToModify(defaultEntityType=Cmd.ENTITY_USER)
  checkServiceAccount(entityList)

def _getSAKeys(iam, projectId, clientEmail, name, keyTypes):
  try:
    keys = callGAPIitems(iam.projects().serviceAccounts().keys(), 'list', 'keys',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                         name=name, fields='*', keyTypes=keyTypes)
    return (True, keys)
  except GAPI.permissionDenied:
    entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
  except GAPI.badRequest as e:
    entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
  return (False, None)

SVCACCT_KEY_TIME_OBJECTS = {'validAfterTime', 'validBeforeTime'}

def _showSAKeys(keys, count, currentPrivateKeyId):
  Ind.Increment()
  i = 0
  for key in keys:
    i += 1
    keyName = key.pop('name').rsplit('/', 1)[-1]
    printKeyValueListWithCount(['name', keyName], i, count)
    Ind.Increment()
    for k, v in sorted(key.items()):
      if k not in SVCACCT_KEY_TIME_OBJECTS:
        printKeyValueList([k, v])
      else:
        printKeyValueList([k, formatLocalTime(v)])
    if keyName == currentPrivateKeyId:
      printKeyValueList(['usedToAuthenticateThisRequest', True])
    Ind.Decrement()
  Ind.Decrement()

SVCACCT_DISPLAY_FIELDS = ['displayName', 'description', 'oauth2ClientId', 'uniqueId', 'disabled']
SVCACCT_KEY_TYPE_CHOICE_MAP = {
  'all': None,
  'system': 'SYSTEM_MANAGED',
  'systemmanaged': 'SYSTEM_MANAGED',
  'user': 'USER_MANAGED',
  'usermanaged': 'USER_MANAGED'
  }

# gam print svcaccts [[admin] <EmailAddress>] [all|<ProjectIDEntity>]
#	[showsakeys all|system|user]
#	[todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]
# gam show svcaccts [<EmailAddress>] [all|<ProjectIDEntity>]
#	[showsakeys all|system|user]
def doPrintShowSvcAccts():
  _, httpObj, login_hint, projects = _getLoginHintProjects(printShowCmd=True, readOnly=False)
  csvPF = CSVPrintFile(['User', 'projectId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  iam = getAPIService(API.IAM, httpObj)
  keyTypes = None
  showSAKeys = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showsakeys':
      keyTypes = getChoice(SVCACCT_KEY_TYPE_CHOICE_MAP, mapChoice=True)
      showSAKeys = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  count = len(projects)
  if not csvPF:
    entityPerformActionSubItemModifierNumItems([Ent.USER, login_hint], Ent.SVCACCT, Act.MODIFIER_FOR, count, Ent.PROJECT)
  else:
    csvPF.AddTitles(['projectId']+SVCACCT_DISPLAY_FIELDS)
    csvPF.SetSortAllTitles()
  i = 0
  for project in projects:
    i += 1
    if not _checkProjectFound(project, i, count):
      continue
    projectId = project['projectId']
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.SVCACCT, projectId, i, count)
    if project['state'] != 'ACTIVE':
      entityActionNotPerformedWarning([Ent.PROJECT, projectId], Msg.DELETED, i, count)
      continue
    try:
      svcAccts = callGAPIpages(iam.projects().serviceAccounts(), 'list', 'accounts',
                               throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                               name=f'projects/{projectId}')
      if not csvPF:
        jcount = len(svcAccts)
        entityPerformActionNumItems([Ent.PROJECT, projectId], jcount, Ent.SVCACCT, i, count)
        Ind.Increment()
        j = 0
        for svcAcct in svcAccts:
          j += 1
          printKeyValueListWithCount(['email', svcAcct['email']], j, jcount)
          Ind.Increment()
          for field in SVCACCT_DISPLAY_FIELDS:
            if field in svcAcct:
              printKeyValueList([field, svcAcct[field]])
          if showSAKeys:
            name = f"projects/{projectId}/serviceAccounts/{svcAcct['oauth2ClientId']}"
            status, keys = _getSAKeys(iam, projectId, svcAcct['email'], name, keyTypes)
            if status:
              kcount = len(keys)
              if kcount > 0:
                printKeyValueList([Ent.Choose(Ent.SVCACCT_KEY, kcount), kcount])
                _showSAKeys(keys, kcount, '')
          Ind.Decrement()
        Ind.Decrement()
      else:
        for svcAcct in svcAccts:
          if showSAKeys:
            name = f"projects/{projectId}/serviceAccounts/{svcAcct['oauth2ClientId']}"
            status, keys = _getSAKeys(iam, projectId, svcAcct['email'], name, keyTypes)
            if status:
              svcAcct['keys'] = keys
          row = flattenJSON(svcAcct, flattened={'User': login_hint}, timeObjects=SVCACCT_KEY_TIME_OBJECTS)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            csvPF.WriteRowNoFilter({'User': login_hint, 'projectId': projectId,
                                    'JSON': json.dumps(cleanJSON(svcAcct, timeObjects=SVCACCT_KEY_TIME_OBJECTS),
                                                       ensure_ascii=False, sort_keys=True)})
    except (GAPI.notFound, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.PROJECT, projectId], str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Service Accounts')

def _formatOAuth2ServiceData(service_data):
  quotedEmail = quote(service_data.get('client_email', ''))
  service_data['auth_provider_x509_cert_url'] = API.GOOGLE_AUTH_PROVIDER_X509_CERT_URL
  service_data['auth_uri'] = API.GOOGLE_OAUTH2_ENDPOINT
  service_data['client_x509_cert_url'] = f'https://www.googleapis.com/robot/v1/metadata/x509/{quotedEmail}'
  service_data['token_uri'] = API.GOOGLE_OAUTH2_TOKEN_ENDPOINT
  service_data['type'] = 'service_account'
  GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = service_data.copy()
  return json.dumps(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA], indent=2, sort_keys=True)

def doProcessSvcAcctKeys(mode=None, iam=None, projectId=None, clientEmail=None, clientId=None):
  def getSAKeyParms(body, new_data):
    nonlocal local_key_size, validityHours
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'algorithm':
        body['keyAlgorithm'] = getChoice(["key_alg_rsa_1024", "key_alg_rsa_2048"]).upper()
        local_key_size = 0
      elif myarg == 'localkeysize':
        local_key_size = int(getChoice(['1024', '2048', '4096']))
      elif myarg == 'validityhours':
        validityHours = getInteger()
      elif myarg == 'yubikey':
        new_data['key_type'] = 'yubikey'
      elif myarg == 'yubikeyslot':
        new_data['yubikey_slot'] = getString(Cmd.OB_STRING).upper()
      elif myarg == 'yubikeypin':
        new_data['yubikey_pin'] = readStdin('Enter your YubiKey PIN: ')
      elif myarg == 'yubikeyserialnumber':
        new_data['yubikey_serial_number'] = getInteger()
      else:
        unknownArgumentExit()

  local_key_size = 2048
  validityHours = 0
  body = {}
  if mode is None:
    mode = getChoice(['retainnone', 'retainexisting', 'replacecurrent'])
  if iam is None or mode == 'upload':
    if iam is None:
      _, iam = buildGAPIServiceObject(API.IAM, None)
    _getSvcAcctData()
    currentPrivateKeyId, projectId, clientEmail, clientId = _getSvcAcctKeyProjectClientFields()
    # dict() ensures we have a real copy, not pointer
    new_data = dict(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA])
    # assume default key type unless we are told otherwise
    new_data['key_type'] = 'default'
    getSAKeyParms(body, new_data)
  else:
    new_data = {
      'client_email': clientEmail,
      'project_id': projectId,
      'client_id': clientId,
      'key_type': 'default'
    }
    getSAKeyParms(body, new_data)
  name = f'projects/{projectId}/serviceAccounts/{clientId}'
  if mode != 'retainexisting':
    try:
      keys = callGAPIitems(iam.projects().serviceAccounts().keys(), 'list', 'keys',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                           name=name, keyTypes='USER_MANAGED')
    except GAPI.permissionDenied:
      entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
      return False
    except GAPI.badRequest as e:
      entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
      return False
  if new_data.get('key_type') == 'yubikey':
    # Use yubikey private key
    new_data['yubikey_key_type'] = f'RSA{local_key_size}'
    new_data.pop('private_key', None)
    yk = yubikey.YubiKey(new_data)
    if 'yubikey_serial_number' not in new_data:
      new_data['yubikey_serial_number'] = yk.get_serial_number()
      yk = yubikey.YubiKey(new_data)
    if 'yubikey_slot' not in new_data:
      new_data['yubikey_slot'] = 'AUTHENTICATION'
    publicKeyData = yk.get_certificate()
  elif local_key_size:
    # Generate private key locally, store in file
    new_data['private_key'], publicKeyData = _generatePrivateKeyAndPublicCert(projectId, clientEmail, name,
                                                                              local_key_size, validityHours=validityHours)
    new_data['key_type'] = 'default'
    for key in list(new_data):
      if key.startswith('yubikey_'):
        new_data.pop(key, None)
  if local_key_size:
    Act.Set(Act.UPLOAD)
    maxRetries = 10
    printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPLOADING_NEW_PUBLIC_CERTIFICATE_TO_GOOGLE)
    for retry in range(1, maxRetries+1):
      try:
        result = callGAPI(iam.projects().serviceAccounts().keys(), 'upload',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                          name=name, body={'publicKeyData': publicKeyData})
        newPrivateKeyId = result['name'].rsplit('/', 1)[-1]
        break
      except GAPI.notFound as e:
        if retry == maxRetries:
          entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
          return False
        _waitForSvcAcctCompletion(retry)
      except GAPI.permissionDenied:
        if retry == maxRetries:
          entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
          return False
        _waitForSvcAcctCompletion(retry)
      except GAPI.badRequest as e:
        entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
        return False
      except GAPI.failedPrecondition as e:
        entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
        if 'iam.disableServiceAccountKeyUpload' not in str(e) and 'iam.managed.disableServiceAccountKeyUpload' not in str(e):
          return False
        if retry == maxRetries or mode != 'upload':
          sys.stdout.write(Msg.ENABLE_SERVICE_ACCOUNT_PRIVATE_KEY_UPLOAD.format(projectId))
          new_data['private_key'] = ''
          newPrivateKeyId = ''
          break
        _waitForSvcAcctCompletion(retry)
    new_data['private_key_id'] = newPrivateKeyId
    oauth2service_data = _formatOAuth2ServiceData(new_data)
  else:
    Act.Set(Act.CREATE)
    maxRetries = 10
    for retry in range(1, maxRetries+1):
      try:
        result = callGAPI(iam.projects().serviceAccounts().keys(), 'create',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                          name=name, body=body)
        newPrivateKeyId = result['name'].rsplit('/', 1)[-1]
        break
      except GAPI.permissionDenied:
        if retry == maxRetries:
          entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
          return False
        _waitForSvcAcctCompletion(retry)
      except GAPI.badRequest as e:
        entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
        return False
    oauth2service_data = base64.b64decode(result['privateKeyData']).decode(UTF8)
  if newPrivateKeyId != '':
    entityActionPerformed([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail, Ent.SVCACCT_KEY, newPrivateKeyId])
  if GM.Globals[GM.SVCACCT_SCOPES_DEFINED]:
    try:
      GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = json.loads(oauth2service_data)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      invalidOauth2serviceJsonExit(str(e))
    GM.Globals[GM.OAUTH2SERVICE_JSON_DATA][API.OAUTH2SA_SCOPES] = GM.Globals[GM.SVCACCT_SCOPES]
    oauth2service_data = json.dumps(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA], ensure_ascii=False, indent=2, sort_keys=True)
  writeFile(GC.Values[GC.OAUTH2SERVICE_JSON], oauth2service_data, continueOnError=False)
  Act.Set(Act.UPDATE)
  entityActionPerformed([Ent.OAUTH2SERVICE_JSON_FILE, GC.Values[GC.OAUTH2SERVICE_JSON],
                         Ent.SVCACCT_KEY, newPrivateKeyId])
  if mode in {'retainexisting', 'upload'}:
    return newPrivateKeyId != ''
  Act.Set(Act.REVOKE)
  count = len(keys) if mode == 'retainnone' else 1
  entityPerformActionNumItems([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], count, Ent.SVCACCT_KEY)
  Ind.Increment()
  i = 0
  for key in keys:
    keyName = key['name'].rsplit('/', 1)[-1]
    if mode == 'retainnone' or keyName == currentPrivateKeyId and keyName != newPrivateKeyId:
      i += 1
      maxRetries = 5
      for retry in range(1, maxRetries+1):
        try:
          callGAPI(iam.projects().serviceAccounts().keys(), 'delete',
                   throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                   name=key['name'])
          entityActionPerformed([Ent.SVCACCT_KEY, keyName], i, count)
          break
        except GAPI.permissionDenied:
          if retry == maxRetries:
            entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
            break
          _waitForSvcAcctCompletion(retry)
        except GAPI.badRequest as e:
          entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], str(e), i, count)
          break
      if mode != 'retainnone':
        break
  Ind.Decrement()
  return True

# gam create sakey|sakeys
# gam rotate sakey|sakeys retain_existing
#	(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	(localkeysize 1024|2048|4096 [validityhours <Number>])|
#	(yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)
def doCreateSvcAcctKeys():
  doProcessSvcAcctKeys(mode='retainexisting')

# gam update sakey|sakeys
# gam rotate sakey|sakeys replace_current
#	(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	(localkeysize 1024|2048|4096 [validityhours <Number>])|
#	(yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)
def doUpdateSvcAcctKeys():
  doProcessSvcAcctKeys(mode='replacecurrent')

# gam replace sakey|sakeys
# gam rotate sakey|sakeys retain_none
#	(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	(localkeysize 1024|2048|4096 [validityhours <Number>])|
#	(yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)
def doReplaceSvcAcctKeys():
  doProcessSvcAcctKeys(mode='retainnone')

# gam upload sakey|sakeys [admin <EmailAddress>]
#	(algorithm KEY_ALG_RSA_1024|KEY_ALG_RSA_2048)|
#	(localkeysize 1024|2048|4096 [validityhours <Number>])|
#	(yubikey yubikey_pin yubikey_slot AUTHENTICATION yubikey_serialnumber <String>)
def doUploadSvcAcctKeys():
  login_hint = getEmailAddress(noUid=True) if checkArgumentPresent(['admin']) else None
  httpObj, _ = getCRMService(login_hint)
  iam = getAPIService(API.IAM, httpObj)
  if doProcessSvcAcctKeys(mode='upload', iam=iam):
    sa_email = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']
    _grantRotateRights(iam, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'], sa_email)
    sys.stdout.write(Msg.YOUR_GAM_PROJECT_IS_CREATED_AND_READY_TO_USE)

# gam delete sakeys <ServiceAccountKeyList>
def doDeleteSvcAcctKeys():
  _, iam = buildGAPIServiceObject(API.IAM, None)
  doit = False
  keyList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'doit':
      doit = True
    else:
      Cmd.Backup()
      keyList.extend(getString(Cmd.OB_SERVICE_ACCOUNT_KEY_LIST, minLen=0).strip().replace(',', ' ').split())
  currentPrivateKeyId, projectId, clientEmail, clientId = _getSvcAcctKeyProjectClientFields()
  name = f'projects/{projectId}/serviceAccounts/{clientId}'
  try:
    keys = callGAPIitems(iam.projects().serviceAccounts().keys(), 'list', 'keys',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                         name=name, keyTypes='USER_MANAGED')
  except GAPI.permissionDenied:
    entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
    return
  except GAPI.badRequest as e:
    entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
    return
  Act.Set(Act.REVOKE)
  count = len(keyList)
  entityPerformActionNumItems([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], count, Ent.SVCACCT_KEY)
  Ind.Increment()
  i = 0
  for dkeyName in keyList:
    i += 1
    for key in keys:
      keyName = key['name'].rsplit('/', 1)[-1]
      if keyName == dkeyName:
        if keyName == currentPrivateKeyId and not doit:
          entityActionNotPerformedWarning([Ent.SVCACCT_KEY, keyName],
                                          Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION+Msg.ON_CURRENT_PRIVATE_KEY, i, count)
          break
        try:
          callGAPI(iam.projects().serviceAccounts().keys(), 'delete',
                   throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                   name=key['name'])
          entityActionPerformed([Ent.SVCACCT_KEY, keyName], i, count)
        except GAPI.permissionDenied:
          entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
        except GAPI.badRequest as e:
          entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], str(e), i, count)
        break
    else:
      entityActionNotPerformedWarning([Ent.SVCACCT_KEY, dkeyName], Msg.NOT_FOUND, i, count)
  Ind.Decrement()

# gam show sakeys [all|system|user]
def doShowSvcAcctKeys():
  _, iam = buildGAPIServiceObject(API.IAM, None)
  keyTypes = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in SVCACCT_KEY_TYPE_CHOICE_MAP:
      keyTypes = SVCACCT_KEY_TYPE_CHOICE_MAP[myarg]
    else:
      unknownArgumentExit()
  currentPrivateKeyId, projectId, clientEmail, clientId = _getSvcAcctKeyProjectClientFields()
  name = f'projects/{projectId}/serviceAccounts/{clientId}'
  status, keys = _getSAKeys(iam, projectId, clientEmail, name, keyTypes)
  if not status:
    return
  count = len(keys)
  entityPerformActionNumItems([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], count, Ent.SVCACCT_KEY)
  if count > 0:
    _showSAKeys(keys, count, currentPrivateKeyId)

# gam create gcpserviceaccount|signjwtserviceaccount
def doCreateGCPServiceAccount():
  checkForExtraneousArguments()
  _checkForExistingProjectFiles([GC.Values[GC.OAUTH2SERVICE_JSON]])
  sa_info = {'key_type': 'signjwt', 'token_uri': API.GOOGLE_OAUTH2_TOKEN_ENDPOINT, 'type': 'service_account'}
  request = get_adc_request()
  try:
    credentials, sa_info['project_id'] = google.auth.default(scopes=[API.IAM_SCOPE], request=request)
  except (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError) as e:
    systemErrorExit(API_ACCESS_DENIED_RC, str(e))
  credentials.refresh(request)
  sa_info['client_email'] = credentials.service_account_email
  oa2 = buildGAPIObjectNoAuthentication(API.OAUTH2)
  try:
    token_info = callGAPI(oa2, 'tokeninfo',
                          throwReasons=[GAPI.INVALID],
                          access_token=credentials.token)
  except GAPI.invalid as e:
    systemErrorExit(API_ACCESS_DENIED_RC, str(e))
  sa_info['client_id'] = token_info['issued_to']
  sa_output = json.dumps(sa_info, ensure_ascii=False, indent=2, sort_keys=True)
  writeStdout(f'Writing SignJWT service account data:\n\n{sa_output}\n')
  writeFile(GC.Values[GC.OAUTH2SERVICE_JSON], sa_output, continueOnError=False)

# Audit command utilities
