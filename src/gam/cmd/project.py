"""_getMain().GAM GCP project and service account management.

Extracted from gam/__init__.py. Provides GCP project creation/deletion,
service account management, key operations, and API enablement.
"""

import base64
import datetime
import json
import os
import re
import sys
import time

import httplib2

import google.auth
import google.auth.exceptions

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

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

from urllib.parse import urlencode
from cryptography.hazmat.backends import default_backend
import string
LOWERNUMERIC_CHARS = string.ascii_lowercase + string.digits

def getCRMService(login_hint):
  scopes = [API.CLOUD_PLATFORM_SCOPE]
  client_id = _getMain().GAM_PROJECT_CREATION_CLIENT_ID
  client_secret = 'qM3dP8f_4qedwzWQE1VR4zzU'
  credentials = Credentials.from_client_secrets(
    client_id,
    client_secret,
    scopes=scopes,
    access_type='online',
    login_hint=login_hint,
    open_browser=not GC.Values[GC.NO_BROWSER])
  httpObj = _getMain().transportAuthorizedHttp(credentials, http=_getMain().getHttpObj())
  return (httpObj, _getMain().getAPIService(API.CLOUDRESOURCEMANAGER, httpObj))

def enableGAMProjectAPIs(httpObj, projectId, login_hint, checkEnabled, i=0, count=0):
  apis = API.PROJECT_APIS[:]
  projectName = f'projects/{projectId}'
  serveu = _getMain().getAPIService(API.SERVICEUSAGE, httpObj)
  status = True
  if checkEnabled:
    try:
      services = _getMain().callGAPIpages(serveu.services(), 'list', 'services',
                               throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                               parent=projectName, filter='state:ENABLED',
                               fields='nextPageToken,services(name)')
      Act.Set(Act.CHECK)
      jcount = len(services)
      _getMain().entityPerformActionNumItems([Ent.PROJECT, projectId], jcount, Ent.API, i, count)
      Ind.Increment()
      j = 0
      for service in sorted(services, key=lambda k: k['name']):
        j += 1
        if 'name' in service:
          serviceName = service['name'].split('/')[-1]
          if serviceName in apis:
            _getMain().printEntityKVList([Ent.API, serviceName], ['Already enabled'], j, jcount)
            apis.remove(serviceName)
          else:
            _getMain().printEntityKVList([Ent.API, serviceName], ['Already enabled (non-GAM which is fine)'], j, jcount)
      Ind.Decrement()
    except (GAPI.notFound, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, projectId], str(e), i, count)
      status = False
  jcount = len(apis)
  if status and jcount > 0:
    Act.Set(Act.ENABLE)
    _getMain().entityPerformActionNumItems([Ent.PROJECT, projectId], jcount, Ent.API, i, count)
    failed = 0
    Ind.Increment()
    j = 0
    for api in apis:
      j += 1
      serviceName = f'projects/{projectId}/services/{api}'
      while True:
        try:
          _getMain().callGAPI(serveu.services(), 'enable',
                   throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.INTERNAL_ERROR],
                   retryReasons=[GAPI.INTERNAL_ERROR],
                   name=serviceName)
          _getMain().entityActionPerformed([Ent.API, api], j, jcount)
          break
        except GAPI.failedPrecondition as e:
          _getMain().entityActionFailedWarning([Ent.API, api], str(e), j, jcount)
          _getMain().readStdin(Msg.ACCEPT_CLOUD_TOS.format(login_hint))
        except (GAPI.forbidden, GAPI.permissionDenied, GAPI.internalError) as e:
          _getMain().entityActionFailedWarning([Ent.API, api], str(e), j, jcount)
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
    myarg = _getMain().getArgument()
    if myarg == 'auto':
      automatic = True
    elif myarg == 'manual':
      automatic = False
    else:
      _getMain().unknownArgumentExit()
  request = _getMain().get_adc_request()
  try:
    _, projectId = google.auth.default(scopes=[API.IAM_SCOPE], request=request)
  except (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError):
    projectId = _getMain().readStdin(Msg.WHAT_IS_YOUR_PROJECT_ID).strip()
  while automatic is None:
    a_or_m = _getMain().readStdin(Msg.ENABLE_PROJECT_APIS_AUTOMATICALLY_OR_MANUALLY).strip().lower()
    if a_or_m.startswith('a'):
      automatic = True
      break
    if a_or_m.startswith('m'):
      automatic = False
      break
    _getMain().writeStdout(Msg.PLEASE_ENTER_A_OR_M)
  if automatic:
    login_hint = _getMain()._getValidateLoginHint(None)
    httpObj, _ = getCRMService(login_hint)
    enableGAMProjectAPIs(httpObj, projectId, login_hint, True)
  else:
    apis = API.PROJECT_APIS[:]
    chunk_size = 20
    _getMain().writeStdout('Using an account with project access, please use ALL of these URLs to enable 20 APIs at a time:\n\n')
    for chunk in range(0, len(apis), chunk_size):
      apiid = ",".join(apis[chunk:chunk+chunk_size])
      url = f'https://console.cloud.google.com/apis/enableflow?apiid={apiid}&project={projectId}'
      _getMain().writeStdout(f'    {url}\n\n')

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
  _getMain().printEntityMessage(kvList, Msg.GRANTING_RIGHTS_TO_ROTATE_ITS_OWN_PRIVATE_KEY.format('Granting'))
  for retry in range(1, maxRetries+1):
    try:
      _getMain().callGAPI(iam.projects().serviceAccounts(), 'setIamPolicy',
               throwReasons=[GAPI.INVALID_ARGUMENT],
               resource=f'projects/{projectId}/serviceAccounts/{service_account}', body=body)
      _getMain().printEntityMessage(kvList, Msg.GRANTING_RIGHTS_TO_ROTATE_ITS_OWN_PRIVATE_KEY.format('Granted'))
      return True
    except GAPI.invalidArgument as e:
      _getMain().entityActionFailedWarning(kvList, str(e))
      if 'does not exist' not in str(e) or retry == maxRetries:
        return False
      _waitForSvcAcctCompletion(retry)
    except Exception as e:
      _getMain().entityActionFailedWarning(kvList, str(e))
      return False

def _createOauth2serviceJSON(httpObj, projectInfo, svcAcctInfo, create_key=True):
  iam = _getMain().getAPIService(API.IAM, httpObj)
  try:
    service_account = _getMain().callGAPI(iam.projects().serviceAccounts(), 'create',
                               throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.NOT_FOUND,
                                             GAPI.PERMISSION_DENIED, GAPI.ALREADY_EXISTS],
                               name=f'projects/{projectInfo["projectId"]}',
                               body={'accountId': svcAcctInfo['name'],
                                     'serviceAccount': {'displayName': svcAcctInfo['displayName'],
                                                        'description': svcAcctInfo['description']}})
    _getMain().entityActionPerformed([Ent.PROJECT, projectInfo['projectId'], Ent.SVCACCT, service_account['name'].rsplit('/', 1)[-1]])
  except (GAPI.failedPrecondition, GAPI.notFound, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.PROJECT, projectInfo['projectId']], str(e))
    return False
  except GAPI.alreadyExists as e:
    _getMain().entityActionFailedWarning([Ent.PROJECT, projectInfo['projectId'], Ent.SVCACCT, svcAcctInfo['name']], str(e))
    _getMain().writeStderr(Msg.RERUN_THE_COMMAND_AND_SPECIFY_A_NEW_SANAME)
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
    if not 'error' in content or not 'error_description' in content:
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
  csHttpObj = _getMain().getHttpObj()
  while True:
    sys.stdout.write(Msg.CREATE_CLIENT_INSTRUCTIONS.format(console_url, appInfo['applicationTitle'], appInfo['supportEmail']))
    client_id = _getMain().readStdin(Msg.ENTER_YOUR_CLIENT_ID).strip()
    if not client_id:
      client_id = _getMain().readStdin('').strip()
    client_secret = _getMain().readStdin(Msg.ENTER_YOUR_CLIENT_SECRET).strip()
    if not client_secret:
      client_secret = _getMain().readStdin('').strip()
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
  _getMain().writeFile(GC.Values[GC.CLIENT_SECRETS_JSON], cs_data, continueOnError=False)
  sys.stdout.write(Msg.TRUST_GAM_CLIENT_ID.format(_getMain().GAM, client_id))
  _getMain().readStdin('')
  if not _createOauth2serviceJSON(httpObj, projectInfo, svcAcctInfo, create_key):
    return
  sys.stdout.write(Msg.YOUR_GAM_PROJECT_IS_CREATED_AND_READY_TO_USE)

def _getProjects(crm, pfilter, returnNF=False):
  try:
    projects = _getMain().callGAPIpages(crm.projects(), 'search', 'projects',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                             query=pfilter)
    if projects:
      return projects
    if (not pfilter) or pfilter == GAM_PROJECT_FILTER:
      return []
    if pfilter.startswith('id:'):
      projects = [_getMain().callGAPI(crm.projects(), 'get',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                           name=f'projects/{pfilter[3:]}')]
      if projects or not returnNF:
        return projects
    return []
  except (GAPI.badRequest, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedExit([Ent.PROJECT, pfilter], str(e))
  except GAPI.permissionDenied:
    if (not pfilter) or (not pfilter.startswith('id:')) or (not returnNF):
      return []
  return [{'projectId': pfilter[3:], 'state': 'NF'}]

def _checkProjectFound(project, i, count):
  if project.get('state', '') != 'NF':
    return True
  _getMain().entityActionFailedWarning([Ent.PROJECT, project['projectId']], Msg.DOES_NOT_EXIST, i, count)
  return False

def convertGCPFolderNameToID(parent, crm):
  folders = _getMain().callGAPIpages(crm.folders(), 'search', 'folders',
                          query=f'displayName="{parent}"')
  if not folders:
    _getMain().entityActionFailedExit([Ent.PROJECT_FOLDER, parent], Msg.NOT_FOUND)
  jcount = len(folders)
  if jcount > 1:
    _getMain().entityActionNotPerformedWarning([Ent.PROJECT_FOLDER, parent],
                                    Msg.PLEASE_SELECT_ENTITY_TO_PROCESS.format(jcount, Ent.Plural(Ent.PROJECT_FOLDER), 'use in create', 'parent <String>'))
    Ind.Increment()
    j = 0
    for folder in folders:
      j += 1
      _getMain().printKeyValueListWithCount(['Name', folder['name'], 'ID', folder['displayName']], j, jcount)
    Ind.Decrement()
    _getMain().systemErrorExit(_getMain().MULTIPLE_PROJECT_FOLDERS_FOUND_RC, None)
  return folders[0]['name']

PROJECTID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$')
PROJECTID_FORMAT_REQUIRED = '[a-z][a-z0-9-]{4,28}[a-z0-9]'
def _checkProjectId(projectId):
  if not PROJECTID_PATTERN.match(projectId):
    Cmd.Backup()
    _getMain().invalidArgumentExit(PROJECTID_FORMAT_REQUIRED)

PROJECTNAME_PATTERN = re.compile('^[a-zA-Z0-9 '+"'"+'"!-]{4,30}$')
PROJECTNAME_FORMAT_REQUIRED = '[a-zA-Z0-9 \'"!-]{4,30}'
def _checkProjectName(projectName):
  if not PROJECTNAME_PATTERN.match(projectName):
    Cmd.Backup()
    _getMain().invalidArgumentExit(PROJECTNAME_FORMAT_REQUIRED)

def _getSvcAcctInfo(myarg, svcAcctInfo):
  if myarg == 'saname':
    svcAcctInfo['name'] = _getMain().getString(Cmd.OB_STRING, minLen=6, maxLen=30)
    _checkProjectId(svcAcctInfo['name'])
  elif myarg == 'sadisplayname':
    svcAcctInfo['displayName'] = _getMain().getString(Cmd.OB_STRING, maxLen=100)
  elif myarg == 'sadescription':
    svcAcctInfo['description'] = _getMain().getString(Cmd.OB_STRING, maxLen=256)
  else:
    return False
  return True

def _getAppInfo(myarg, appInfo):
  if myarg == 'appname':
    appInfo['applicationTitle'] = _getMain().getString(Cmd.OB_STRING)
  elif myarg == 'supportemail':
    appInfo['supportEmail'] = _getMain().getEmailAddress(noUid=True)
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
    login_hint = _getMain().getString(Cmd.OB_EMAIL_ADDRESS, optional=True)
    if login_hint and login_hint.find('@') == -1:
      Cmd.Backup()
      login_hint = None
    projectInfo['projectId'] = _getMain().getString(Cmd.OB_STRING, optional=True, minLen=6, maxLen=30).strip()
    if projectInfo['projectId']:
      _checkProjectId(projectInfo['projectId'])
    _getMain().checkForExtraneousArguments()
  else:
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if myarg == 'admin':
        login_hint = _getMain().getEmailAddress(noUid=True)
      elif myarg == 'nokey':
        create_key = False
      elif myarg == 'project':
        projectInfo['projectId'] = _getMain().getString(Cmd.OB_STRING, minLen=6, maxLen=30)
        _checkProjectId(projectInfo['projectId'])
      elif createCmd and myarg == 'parent':
        projectInfo['parent'] = _getMain().getString(Cmd.OB_STRING)
      elif myarg == 'projectname':
        projectInfo['name'] = _getMain().getString(Cmd.OB_STRING, minLen=4, maxLen=30)
        _checkProjectName(projectInfo['name'])
      elif _getSvcAcctInfo(myarg, svcAcctInfo):
        pass
      elif _getAppInfo(myarg, appInfo):
        pass
      elif myarg in {'algorithm', 'localkeysize', 'validityhours', 'yubikey'}:
        Cmd.Backup()
        break
      else:
        _getMain().unknownArgumentExit()
  if not projectInfo['projectId']:
    if createCmd:
      projectInfo['projectId'] = _generateProjectSvcAcctId('gam-project')
    else:
      projectInfo['projectId'] = _getMain().readStdin(Msg.WHAT_IS_YOUR_PROJECT_ID).strip()
      if not PROJECTID_PATTERN.match(projectInfo['projectId']):
        _getMain().systemErrorExit(_getMain().USAGE_ERROR_RC, f'{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1]} {Cmd.OB_PROJECT_ID}: {Msg.EXPECTED} <{PROJECTID_FORMAT_REQUIRED}>')
  if not projectInfo['name']:
    projectInfo['name'] = 'GAM Project' if not GC.Values[GC.USE_PROJECTID_AS_NAME] else projectInfo['projectId']
  if not svcAcctInfo['name']:
    svcAcctInfo['name'] = projectInfo['projectId']
  if not svcAcctInfo['displayName']:
    svcAcctInfo['displayName'] = projectInfo['name']
  if not svcAcctInfo['description']:
    svcAcctInfo['description'] = svcAcctInfo['displayName']
  login_hint = _getMain()._getValidateLoginHint(login_hint, projectInfo['projectId'])
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
      _getMain().entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], Msg.DOES_NOT_EXIST)
    if projects[0]['state'] != 'ACTIVE':
      _getMain().entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], Msg.NOT_ACTIVE)
  else:
    if projects:
      _getMain().entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], Msg.DUPLICATE)
  return (crm, httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key)

def _getCurrentProjectId():
  jsonData = _getMain().readFile(GC.Values[GC.OAUTH2SERVICE_JSON], continueOnError=True, displayError=False)
  if jsonData:
    try:
      return json.loads(jsonData)['project_id']
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
      pass
  jsonData = _getMain().readFile(GC.Values[GC.CLIENT_SECRETS_JSON], continueOnError=True, displayError=True)
  if not jsonData:
    _getMain().invalidClientSecretsJsonExit(Msg.NO_DATA)
  try:
    return json.loads(jsonData)['installed']['project_id']
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    _getMain().invalidClientSecretsJsonExit(str(e))

GAM_PROJECT_FILTER = 'id:gam-project-*'
PROJECTID_FILTER_REQUIRED = '<ProjectIDEntity>'
PROJECTS_CREATESVCACCT_OPTIONS = {'saname', 'sadisplayname', 'sadescription'}
PROJECTS_DELETESVCACCT_OPTIONS = {'saemail', 'saname', 'sauniqueid'}
PROJECTS_PRINTSHOW_OPTIONS = {'showsakeys', 'showiampolicies', 'onememberperrow', 'states', 'todrive', 'delimiter', 'formatjson', 'quotechar'}

def _getLoginHintProjects(createSvcAcctCmd=False, deleteSvcAcctCmd=False, printShowCmd=False, readOnly=False):
  if _getMain().checkArgumentPresent(['admin']):
    login_hint = _getMain().getEmailAddress(noUid=True)
  else:
    login_hint = _getMain().getString(Cmd.OB_EMAIL_ADDRESS, optional=True)
  if login_hint and login_hint.find('@') == -1:
    Cmd.Backup()
    login_hint = None
  if readOnly and login_hint and login_hint != _getMain()._getAdminEmail():
    readOnly = False
  projectIds = None
  pfilter = _getMain().getString(Cmd.OB_STRING, optional=True)
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
    pfilter = _getMain().getString(Cmd.OB_STRING)
  elif pfilter.lower() == 'select':
    projectIds = _getMain().getEntityList(Cmd.OB_PROJECT_ID_ENTITY, False)
    projectId = None
  elif PROJECTID_PATTERN.match(pfilter):
    pfilter = f'id:{pfilter}'
  elif pfilter.startswith('id:') and PROJECTID_PATTERN.match(pfilter[3:]):
    pass
  else:
    Cmd.Backup()
    _getMain().invalidArgumentExit(['', 'all|'][printShowCmd]+PROJECTID_FILTER_REQUIRED)
  if not printShowCmd and not createSvcAcctCmd and not deleteSvcAcctCmd:
    _getMain().checkForExtraneousArguments()
  if projectIds is None:
    if pfilter in {'current', 'id:current'}:
      projectId = _getCurrentProjectId()
    else:
      projectId = f'filter {pfilter or "all"}'
  login_hint = _getMain()._getValidateLoginHint(login_hint, projectId)
  crm = None
  if readOnly:
    _, crm = _getMain().buildGAPIServiceObject(API.CLOUDRESOURCEMANAGER, None)
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
      _getMain().systemErrorExit(_getMain().JSON_ALREADY_EXISTS_RC, Msg.AUTHORIZATION_FILE_ALREADY_EXISTS.format(a_file, Act.ToPerform()))

def getCRMOrgId(forceSearch=False):
  if not GC.Values[GC.GCP_ORG_ID] or forceSearch:
    _getMain().setTrueCustomerId()
    _, crm = _getMain().buildGAPIServiceObject(API.CLOUDRESOURCEMANAGER, None)
    results = _getMain().callGAPI(crm.organizations(), 'search',
                       query=f'directorycustomerid:{GC.Values[GC.CUSTOMER_ID]}',
                       pageSize=1, fields='organizations/name')
    orgs = results.get('organizations')
    if not orgs:
      # return nothing and let calling API deal with it
      # since caller knows what GCP role would serve best
      return None
    return orgs[0].get('name')
  return GC.Values[GC.GCP_ORG_ID]

# gam info customerid
def doInfoCustomerId():
  _getMain().checkForExtraneousArguments()
  _getMain().setTrueCustomerId(cd=None, forceUpdate=True)
  _getMain().writeStdout(f'{GC.Values[GC.CUSTOMER_ID]}\n')

# gam info gcporgid
def doInfoGCPOrgId():
  _getMain().checkForExtraneousArguments()
  _getMain().writeStdout(f'{getCRMOrgId(forceSearch=True)}\n')

def getGCPOrgId(crm, login_hint, login_domain):
  if not GC.Values[GC.GCP_ORG_ID]:
    try:
      results = _getMain().callGAPI(crm.organizations(), 'search',
                         throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                         query=f'domain:{login_domain}',
                         pageSize=1, fields='organizations/name')
      return results['organizations'][0]['name']
    except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedExit([Ent.USER, login_hint, Ent.DOMAIN, login_domain], str(e))
    except (KeyError, IndexError):
      _getMain().systemErrorExit(3, Msg.YOU_HAVE_NO_RIGHTS_TO_CREATE_PROJECTS_AND_YOU_ARE_NOT_A_SUPER_ADMIN)
  return GC.Values[GC.GCP_ORG_ID]

# gam create gcpfolder <String>
# gam create gcpfolder [admin <EmailAddress] folder <String>
def doCreateGCPFolder():
  login_hint = None
  if not Cmd.PeekArgumentPresent(['admin', 'folder']):
    name = _getMain().getString(Cmd.OB_STRING)
    _getMain().checkForExtraneousArguments()
  else:
    name = ''
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if myarg == 'admin':
        login_hint = _getMain().getEmailAddress(noUid=True)
      elif myarg == 'folder':
        name = _getMain().getString(Cmd.OB_STRING)
      else:
        _getMain().unknownArgumentExit()
    if not name:
      _getMain().missingChoiceExit('folder')
  login_hint = _getMain()._getValidateLoginHint(login_hint)
  login_domain = _getMain().getEmailAddressDomain(login_hint)
  _, crm = getCRMService(login_hint)
  organization = getGCPOrgId(crm, login_hint, login_domain)
  try:
    result = _getMain().callGAPI(crm.folders(), 'create',
                      throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                      body={'parent': organization, 'displayName': name})
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedExit([Ent.USER, login_hint, Ent.GCP_FOLDER, name], str(e))
  _getMain().entityActionPerformed([Ent.USER, login_hint, Ent.GCP_FOLDER, name, Ent.GCP_FOLDER_NAME, result['name']])

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
  sys.stdout.write(Msg.TRUST_GAM_CLIENT_ID.format(_getMain().GAM_PROJECT_CREATION, _getMain().GAM_PROJECT_CREATION_CLIENT_ID))
  _getMain().readStdin('')
  crm, httpObj, login_hint, appInfo, projectInfo, svcAcctInfo, create_key = _getLoginHintProjectInfo(True)
  login_domain = _getMain().getEmailAddressDomain(login_hint)
  body = {'projectId': projectInfo['projectId'], 'displayName': projectInfo['name']}
  if projectInfo['parent']:
    body['parent'] = projectInfo['parent']
  while True:
    create_again = False
    sys.stdout.write(Msg.CREATING_PROJECT.format(body['displayName']))
    try:
      create_operation = _getMain().callGAPI(crm.projects(), 'create',
                                  throwReasons=[GAPI.BAD_REQUEST, GAPI.ALREADY_EXISTS,
                                                GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                                  body=body)
    except (GAPI.badRequest, GAPI.alreadyExists, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedExit([Ent.USER, login_hint, Ent.PROJECT, projectInfo['projectId']], str(e))
    operation_name = create_operation['name']
    time.sleep(5) # Google recommends always waiting at least 5 seconds
    for i in range(1, 10):
      sys.stdout.write(Msg.CHECKING_PROJECT_CREATION_STATUS)
      status = _getMain().callGAPI(crm.operations(), 'get',
                        name=operation_name)
      if 'error' in status:
        if status['error'].get('message', '') == 'No permission to create project in organization':
          sys.stdout.write(Msg.NO_RIGHTS_GOOGLE_CLOUD_ORGANIZATION)
          organization = getGCPOrgId(crm, login_hint, login_domain)
          org_policy = _getMain().callGAPI(crm.organizations(), 'getIamPolicy',
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
          _getMain().callGAPI(crm.organizations(), 'setIamPolicy',
                   resource=organization, body={'policy': org_policy})
          create_again = True
          break
        try:
          if status['error']['details'][0]['violations'][0]['description'] == 'Callers must accept Terms of Service':
            _getMain().readStdin(Msg.ACCEPT_CLOUD_TOS.format(login_hint))
            create_again = True
            break
        except (IndexError, KeyError):
          pass
        _getMain().systemErrorExit(1, str(status)+'\n')
      if status.get('done', False):
        break
      sleep_time = min(2 ** i, 60)
      sys.stdout.write(Msg.PROJECT_STILL_BEING_CREATED_SLEEPING.format(sleep_time))
      time.sleep(sleep_time)
    if create_again:
      continue
    if not status.get('done', False):
      _getMain().systemErrorExit(1, Msg.FAILED_TO_CREATE_PROJECT.format(status))
    elif 'error' in status:
      _getMain().systemErrorExit(2, status['error']+'\n')
    break
# Try to set policy on project to allow Service Account Key Upload
#  orgp = _getMain().getAPIService(API.ORGPOLICY, httpObj)
#  projectParent = f"projects/{projectInfo['projectId']}"
#  policyName = f'{projectParent}/policies/iam.managed.disableServiceAccountKeyUpload'
#  try:
#    result = _getMain().callGAPI(orgp.projects().policies(), 'get',
#                      throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
#                      name=policyName)
#    if result['spec']['rules'][0]['enforce']:
#      _getMain().callGAPI(orgp.projects().policies(), 'patch',
#               throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
#               name=policyName, body={'spec': {'rules': [{'enforce': False}]}}, updateMask='policy.spec')
#  except GAPI.notFound:
#    _getMain().callGAPI(orgp.projects().policies(), 'create',
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
  _getMain().entityPerformActionNumItems([Ent.USER, login_hint], count, Ent.PROJECT)
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
    iam = _getMain().getAPIService(API.IAM, httpObj)
    _getMain()._getSvcAcctData() # needed to read in GM.OAUTH2SERVICE_JSON_DATA
    _grantRotateRights(iam, projectId, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email'])
  Ind.Decrement()

# gam delete project [[admin] <EmailAddress>] [<ProjectIDEntity>]
def doDeleteProject():
  crm, _, login_hint, projects = _getLoginHintProjects()
  count = len(projects)
  _getMain().entityPerformActionNumItems([Ent.USER, login_hint], count, Ent.PROJECT)
  Ind.Increment()
  i = 0
  for project in projects:
    i += 1
    if not _checkProjectFound(project, i, count):
      continue
    projectId = project['projectId']
    try:
      _getMain().callGAPI(crm.projects(), 'delete',
               throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
               name=project['name'])
      _getMain().entityActionPerformed([Ent.PROJECT, projectId])
    except (GAPI.forbidden, GAPI.permissionDenied, GAPI.failedPrecondition) as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, projectId], str(e))
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
      policy = _getMain().callGAPI(crm.projects(), 'getIamPolicy',
                        throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        resource=project['name'], body=policyBody)
      return policy
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, project['projectId'], Ent.IAM_POLICY, None], str(e), i, count)
    return {}

  readOnly = not Cmd.ArgumentIsAhead('showiampolicies')
  crm, _, login_hint, projects = _getLoginHintProjects(printShowCmd=True, readOnly=readOnly)
  csvPF = _getMain().CSVPrintFile(['User', 'projectId']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  oneMemberPerRow = False
  showIAMPolicies = -1
  lifecycleStates = PROJECT_STATE_CHOICE_MAP['active']
  policy = None
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'onememberperrow':
      oneMemberPerRow = True
    elif myarg == 'states':
      lifecycleStates = _getMain().getChoice(PROJECT_STATE_CHOICE_MAP, mapChoice=True)
    elif myarg == 'showiampolicies':
      showIAMPolicies = int(_getMain().getChoice(['0', '1', '3']))
      policyBody = {'options': {"requestedPolicyVersion": showIAMPolicies}}
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not csvPF:
    count = len(projects)
    _getMain().entityPerformActionNumItems([Ent.USER, login_hint], count, Ent.PROJECT)
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
      _getMain().printEntity([Ent.PROJECT, projectId], i, count)
      Ind.Increment()
      _getMain().printKeyValueList(['name', project['name']])
      _getMain().printKeyValueList(['displayName', project['displayName']])
      for field in ['createTime', 'updateTime', 'deleteTime']:
        if field in project:
          _getMain().printKeyValueList([field, _getMain().formatLocalTime(project[field])])
      _getMain().printKeyValueList(['state', project['state']])
      jcount = len(project.get('labels', []))
      if jcount > 0:
        _getMain().printKeyValueList(['labels', jcount])
        Ind.Increment()
        for k, v in project['labels'].items():
          _getMain().printKeyValueList([k, v])
        Ind.Decrement()
      if 'parent' in project:
        _getMain().printKeyValueList(['parent', project['parent']])
      if policy:
        _getMain().printKeyValueList([Ent.Singular(Ent.IAM_POLICY), ''])
        Ind.Increment()
        bindings = policy.get('bindings', [])
        jcount = len(bindings)
        _getMain().printKeyValueList(['version', policy['version']])
        _getMain().printKeyValueList(['bindings', jcount])
        Ind.Increment()
        j = 0
        for binding in bindings:
          j += 1
          _getMain().printKeyValueListWithCount(['role', binding['role']], j, jcount)
          Ind.Increment()
          for member in binding.get('members', []):
            _getMain().printKeyValueList(['member', member])
          if 'condition' in binding:
            _getMain().printKeyValueList(['condition', ''])
            Ind.Increment()
            for k, v in binding['condition'].items():
              _getMain().printKeyValueList([k, v])
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
        row = _getMain().flattenJSON(project, flattened={'User': login_hint}, timeObjects=PROJECT_TIMEOBJECTS)
        if csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'User': login_hint, 'projectId': projectId,
                                  'JSON': json.dumps(_getMain().cleanJSON(project),
                                                     ensure_ascii=False, sort_keys=True)})
        continue
      row = _getMain().flattenJSON(project, flattened={'User': login_hint}, timeObjects=PROJECT_TIMEOBJECTS)
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
  _getMain().checkForExtraneousArguments()
  _getMain().printEntity([Ent.PROJECT_ID, _getCurrentProjectId()])

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
    myarg = _getMain().getArgument()
    if _getSvcAcctInfo(myarg, svcAcctInfo):
      pass
    else:
      _getMain().unknownArgumentExit()
  if not svcAcctInfo['name']:
    svcAcctInfo['name'] = _generateProjectSvcAcctId('gam-svcacct')
  if not svcAcctInfo['displayName']:
    svcAcctInfo['displayName'] = svcAcctInfo['name']
  if not svcAcctInfo['description']:
    svcAcctInfo['description'] = svcAcctInfo['displayName']
  count = len(projects)
  _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, login_hint], Ent.SVCACCT, Act.MODIFIER_TO, count, Ent.PROJECT)
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
  iam = _getMain().getAPIService(API.IAM, httpObj)
  clientEmail = clientId = clientName = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'saemail':
      clientEmail = _getMain().getEmailAddress(noUid=True)
      clientName = clientId = None
    elif myarg == 'saname':
      clientName = _getMain().getString(Cmd.OB_STRING, minLen=6, maxLen=30).strip()
      _checkProjectId(clientName)
      clientEmail = clientId = None
    elif myarg == 'sauniqueid':
      clientId = _getMain().getInteger(minVal=0)
      clientEmail = clientName = None
    else:
      _getMain().unknownArgumentExit()
  if not clientEmail and not clientId and not clientName:
    _getMain().missingArgumentExit('email|name|uniqueid')
  count = len(projects)
  _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, login_hint], Ent.SVCACCT, Act.MODIFIER_FROM, count, Ent.PROJECT)
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
      _getMain().callGAPI(iam.projects().serviceAccounts(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST],
               name=f'projects/{projectId}/serviceAccounts/{saName}')
      _getMain().entityActionPerformed([Ent.PROJECT, projectId, Ent.SVCACCT, saName], i, count)
    except (GAPI.notFound, GAPI.badRequest) as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, saName], str(e), i, count)
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
    _getMain().writeStdout(Ind.Spaces()+message+'\n')

  def printPassFail(description, result):
    _getMain().writeStdout(Ind.Spaces()+f'{description:73} {result}'+'\n')

  def authorizeScopes(message):
    long_url = ('https://admin.google.com/ac/owl/domainwidedelegation'
                f'?clientScopeToAdd={",".join(sorted(checkScopes))}'
                f'&clientIdToAdd={service_account}&overwriteClientId=true')
    if GC.Values[GC.DOMAIN]:
      long_url += f'&dn={GC.Values[GC.DOMAIN]}'
    long_url += f'&authuser={_getAdminEmail()}'
    short_url = _getMain().shortenURL(long_url)
    _getMain().printLine(message.format('', short_url))

  credentials = _getMain().getSvcAcctCredentials([API.USERINFO_EMAIL_SCOPE], None, forceOauth=True)
  allScopes = API.getSvcAcctScopes(GC.Values[GC.USER_SERVICE_ACCOUNT_ACCESS_ONLY], Act.Get() == Act.UPDATE)
  checkScopesSet = set()
  saScopes = {}
  checkDeprecatedScopes = True
  useColor = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'scope', 'scopes'}:
      checkDeprecatedScopes = False
      for scope in _getMain().getString(Cmd.OB_API_SCOPE_URL_LIST).lower().replace(',', ' ').split():
        api = API.getSvcAcctScopeAPI(scope)
        if api is not None:
          saScopes.setdefault(api, [])
          saScopes[api].append(scope)
          checkScopesSet.add(scope)
        else:
          _getMain().invalidChoiceExit(scope, allScopes, True)
    elif myarg == 'usecolor':
      useColor = True
    else:
      _getMain().unknownArgumentExit()
  if useColor:
    testPass = _getMain().createGreenText('PASS')
    testFail = _getMain().createRedText('FAIL')
    testWarn = _getMain().createYellowText('WARN')
    testDeprecated = _getMain().createRedText('DEPRECATED')
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
      selectedScopes = _getMain().getScopesFromUser(scopesList, False, GM.Globals[GM.SVCACCT_SCOPES] if GM.Globals[GM.SVCACCT_SCOPES_DEFINED] else None)
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
    _getMain().writeFile(GC.Values[GC.OAUTH2SERVICE_JSON],
              json.dumps(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA], ensure_ascii=False, indent=2, sort_keys=True),
              continueOnError=False)
  checkScopes = sorted(checkScopesSet)
  jcount = len(checkScopes)
  printMessage(Msg.SYSTEM_TIME_STATUS)
  offsetSeconds, offsetFormatted = _getMain().getLocalGoogleTimeOffset()
  if offsetSeconds <= _getMain().MAX_LOCAL_GOOGLE_TIME_OFFSET:
    timeStatus = testPass
  else:
    timeStatus = testFail
  Ind.Increment()
  printPassFail(Msg.YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE.format(_getMain().GOOGLE_TIMECHECK_LOCATION, offsetFormatted), timeStatus)
  Ind.Decrement()
  oa2 = _getMain().buildGAPIObject(API.OAUTH2)
  printMessage(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AUTHENTICATION)
  # We are explicitly not doing DwD here, just confirming service account can auth
  auth_error = ''
  try:
    request = _getMain().transportCreateRequest()
    credentials.refresh(request)
    sa_token_info = _getMain().callGAPI(oa2, 'tokeninfo', access_token=credentials.token)
    if sa_token_info:
      saTokenStatus = testPass
    else:
      saTokenStatus = testFail
  except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
    _getMain().handleServerError(e)
  except google.auth.exceptions.RefreshError as e:
    saTokenStatus = testFail
    if isinstance(e.args, tuple):
      e = e.args[0]
    auth_error = ' - '+str(e)
  Ind.Increment()
  printPassFail(f'Authentication{auth_error}', saTokenStatus)
  Ind.Decrement()
  if saTokenStatus == testFail:
    _getMain().invalidOauth2serviceJsonExit(f'Authentication{auth_error}')
  _getMain()._getSvcAcctData() # needed to read in GM.OAUTH2SERVICE_JSON_DATA
  if API.IAM not in GM.Globals[GM.SVCACCT_SCOPES]:
    GM.Globals[GM.SVCACCT_SCOPES][API.IAM] = [API.IAM_SCOPE]
  key_type = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA].get('key_type', 'default')
  if key_type == 'default':
    printMessage(Msg.SERVICE_ACCOUNT_CHECK_PRIVATE_KEY_AGE)
    _, iam = _getMain().buildGAPIServiceObject(API.IAM, None)
    currentPrivateKeyId, projectId, _, clientId = _getSvcAcctKeyProjectClientFields()
    name = f'projects/{projectId}/serviceAccounts/{clientId}/keys/{currentPrivateKeyId}'
    Ind.Increment()
    try:
      key = _getMain().callGAPI(iam.projects().serviceAccounts().keys(), 'get',
                     throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.NOT_FOUND,
                                   GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                     name=name, fields='validAfterTime')
      key_created = arrow.get(key['validAfterTime'])
      key_age = _getMain().todaysTime()-key_created
      printPassFail(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AGE.format(key_age.days), testWarn if key_age.days > 30 else testPass)
    except GAPI.permissionDenied:
      printMessage(Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
      printPassFail(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AGE.format('UNKNOWN'), testWarn)
    except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'],
                                 Ent.SVCACCT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']],
                                str(e))
      printPassFail(Msg.SERVICE_ACCOUNT_PRIVATE_KEY_AGE.format('UNKNOWN'), testWarn)
    except GAPI.serviceNotAvailable as e:
      _getMain().entityActionFailedExit([Ent.PROJECT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'],
                              Ent.SVCACCT, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']],
                             str(e))
  else:
    printPassFail(Msg.SERVICE_ACCOUNT_SKIPPING_KEY_AGE_CHECK.format(key_type), testPass)
  Ind.Decrement()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    allScopesPass = True
    user = _getMain().convertUIDtoEmailAddress(user)
    _getMain().printKeyValueListWithCount([Msg.DOMAIN_WIDE_DELEGATION_AUTHENTICATION, '',
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
          credentials = _getMain().getSvcAcctCredentials(scopes, user)
          credentials.refresh(request)
          break
        except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
          _getMain().handleServerError(e)
        except google.auth.exceptions.RefreshError:
          continue
      if credentials.token:
        token_info = _getMain().callGAPI(oa2, 'tokeninfo', access_token=credentials.token)
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
      _getMain().printKeyValueListWithCount([Msg.DEPRECATED_SCOPES, '',
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
            credentials = _getMain().getSvcAcctCredentials(scopes, user)
            credentials.refresh(request)
            break
          except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
            _getMain().handleServerError(e)
          except google.auth.exceptions.RefreshError:
            continue
        if credentials.token:
          token_info = _getMain().callGAPI(oa2, 'tokeninfo', access_token=credentials.token)
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
        _getMain().printLine(Msg.SCOPE_AUTHORIZATION_PASSED.format(service_account))
      else:
        authorizeScopes(Msg.SCOPE_AUTHORIZATION_UPDATE_PASSED)
    else:
      # Tack on email scope for more accurate checking
      checkScopes.append(API.USERINFO_EMAIL_SCOPE)
      _getMain().setSysExitRC(_getMain().SCOPES_NOT_AUTHORIZED_RC)
      authorizeScopes(Msg.SCOPE_AUTHORIZATION_FAILED)
    _getMain().printBlankLine()

# gam check svcacct <UserTypeEntity> (scope|scopes <APIScopeURLList>)*
# gam update svcacct <UserTypeEntity> (scope|scopes <APIScopeURLList>)*
def doCheckUpdateSvcAcct():
  _, entityList = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USER)
  checkServiceAccount(entityList)

def _getSAKeys(iam, projectId, clientEmail, name, keyTypes):
  try:
    keys = _getMain().callGAPIitems(iam.projects().serviceAccounts().keys(), 'list', 'keys',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                         name=name, fields='*', keyTypes=keyTypes)
    return (True, keys)
  except GAPI.permissionDenied:
    _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
  except GAPI.badRequest as e:
    _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
  return (False, None)

SVCACCT_KEY_TIME_OBJECTS = {'validAfterTime', 'validBeforeTime'}

def _showSAKeys(keys, count, currentPrivateKeyId):
  Ind.Increment()
  i = 0
  for key in keys:
    i += 1
    keyName = key.pop('name').rsplit('/', 1)[-1]
    _getMain().printKeyValueListWithCount(['name', keyName], i, count)
    Ind.Increment()
    for k, v in sorted(key.items()):
      if k not in SVCACCT_KEY_TIME_OBJECTS:
        _getMain().printKeyValueList([k, v])
      else:
        _getMain().printKeyValueList([k, _getMain().formatLocalTime(v)])
    if keyName == currentPrivateKeyId:
      _getMain().printKeyValueList(['usedToAuthenticateThisRequest', True])
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
  csvPF = _getMain().CSVPrintFile(['User', 'projectId']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  iam = _getMain().getAPIService(API.IAM, httpObj)
  keyTypes = None
  showSAKeys = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showsakeys':
      keyTypes = _getMain().getChoice(SVCACCT_KEY_TYPE_CHOICE_MAP, mapChoice=True)
      showSAKeys = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  count = len(projects)
  if not csvPF:
    _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, login_hint], Ent.SVCACCT, Act.MODIFIER_FOR, count, Ent.PROJECT)
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
      _getMain().printGettingAllEntityItemsForWhom(Ent.SVCACCT, projectId, i, count)
    if project['state'] != 'ACTIVE':
      _getMain().entityActionNotPerformedWarning([Ent.PROJECT, projectId], Msg.DELETED, i, count)
      continue
    try:
      svcAccts = _getMain().callGAPIpages(iam.projects().serviceAccounts(), 'list', 'accounts',
                               throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                               name=f'projects/{projectId}')
      if not csvPF:
        jcount = len(svcAccts)
        _getMain().entityPerformActionNumItems([Ent.PROJECT, projectId], jcount, Ent.SVCACCT, i, count)
        Ind.Increment()
        j = 0
        for svcAcct in svcAccts:
          j += 1
          _getMain().printKeyValueListWithCount(['email', svcAcct['email']], j, jcount)
          Ind.Increment()
          for field in SVCACCT_DISPLAY_FIELDS:
            if field in svcAcct:
              _getMain().printKeyValueList([field, svcAcct[field]])
          if showSAKeys:
            name = f"projects/{projectId}/serviceAccounts/{svcAcct['oauth2ClientId']}"
            status, keys = _getSAKeys(iam, projectId, svcAcct['email'], name, keyTypes)
            if status:
              kcount = len(keys)
              if kcount > 0:
                _getMain().printKeyValueList([Ent.Choose(Ent.SVCACCT_KEY, kcount), kcount])
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
          row = _getMain().flattenJSON(svcAcct, flattened={'User': login_hint}, timeObjects=SVCACCT_KEY_TIME_OBJECTS)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            csvPF.WriteRowNoFilter({'User': login_hint, 'projectId': projectId,
                                    'JSON': json.dumps(_getMain().cleanJSON(svcAcct, timeObjects=SVCACCT_KEY_TIME_OBJECTS),
                                                       ensure_ascii=False, sort_keys=True)})
    except (GAPI.notFound, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, projectId], str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Service Accounts')

def _generatePrivateKeyAndPublicCert(projectId, clientEmail, name, key_size, b64enc_pub=True, validityHours=0):
  if projectId:
    _getMain().printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.GENERATING_NEW_PRIVATE_KEY)
  else:
    _getMain().writeStdout(Msg.GENERATING_NEW_PRIVATE_KEY+'\n')
  private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size, backend=default_backend())
  private_pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                          format=serialization.PrivateFormat.PKCS8,
                                          encryption_algorithm=serialization.NoEncryption()).decode()

  if projectId:
    _getMain().printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.EXTRACTING_PUBLIC_CERTIFICATE)
  else:
    _getMain().writeStdout(Msg.EXTRACTING_PUBLIC_CERTIFICATE+'\n')
  public_key = private_key.public_key()
  builder = x509.CertificateBuilder()
  # suppress cryptography warnings on service account email length
  with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='.*Attribute\'s length.*')
    builder = builder.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                                                 name,
                                                                 _validate=False)]))
    builder = builder.issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                                                name,
                                                                _validate=False)]))
  # Gooogle seems to enforce the not before date strictly. Set the not before
  # date to be UTC two minutes ago which should cover any clock skew.
  now = arrow.utcnow()
  builder = builder.not_valid_before(now.shift(minutes=-2).naive)
  # Google defaults to 12/31/9999 date for end time if there's no
  # policy to restrict key age
  if validityHours:
    expires = now.shift(hours=validityHours, minutes=-2).naive
    builder = builder.not_valid_after(expires)
  else:
    builder = builder.not_valid_after(arrow.Arrow(9999, 12, 31, 23, 59).naive)
  builder = builder.serial_number(x509.random_serial_number())
  builder = builder.public_key(public_key)
  builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
  builder = builder.add_extension(x509.KeyUsage(key_cert_sign=False,
                                                crl_sign=False, digital_signature=True, content_commitment=False,
                                                key_encipherment=False, data_encipherment=False, key_agreement=False,
                                                encipher_only=False, decipher_only=False), critical=True)
  builder = builder.add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=True)
  certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256(), backend=default_backend())
  public_cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
  if projectId:
    _getMain().printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.DONE_GENERATING_PRIVATE_KEY_AND_PUBLIC_CERTIFICATE)
  else:
    _getMain().writeStdout(Msg.DONE_GENERATING_PRIVATE_KEY_AND_PUBLIC_CERTIFICATE+'\n')
  if not b64enc_pub:
    return (private_pem, public_cert_pem)
  publicKeyData = base64.b64encode(public_cert_pem.encode())
  if isinstance(publicKeyData, bytes):
    publicKeyData = publicKeyData.decode()
  return (private_pem, publicKeyData)

def _formatOAuth2ServiceData(service_data):
  quotedEmail = _getMain().quote(service_data.get('client_email', ''))
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
      myarg = _getMain().getArgument()
      if myarg == 'algorithm':
        body['keyAlgorithm'] = _getMain().getChoice(["key_alg_rsa_1024", "key_alg_rsa_2048"]).upper()
        local_key_size = 0
      elif myarg == 'localkeysize':
        local_key_size = int(_getMain().getChoice(['1024', '2048', '4096']))
      elif myarg == 'validityhours':
        validityHours = _getMain().getInteger()
      elif myarg == 'yubikey':
        new_data['key_type'] = 'yubikey'
      elif myarg == 'yubikeyslot':
        new_data['yubikey_slot'] = _getMain().getString(Cmd.OB_STRING).upper()
      elif myarg == 'yubikeypin':
        new_data['yubikey_pin'] = _getMain().readStdin('Enter your YubiKey PIN: ')
      elif myarg == 'yubikeyserialnumber':
        new_data['yubikey_serial_number'] = _getMain().getInteger()
      else:
        _getMain().unknownArgumentExit()

  local_key_size = 2048
  validityHours = 0
  body = {}
  if mode is None:
    mode = _getMain().getChoice(['retainnone', 'retainexisting', 'replacecurrent'])
  if iam is None or mode == 'upload':
    if iam is None:
      _, iam = _getMain().buildGAPIServiceObject(API.IAM, None)
    _getMain()._getSvcAcctData()
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
      keys = _getMain().callGAPIitems(iam.projects().serviceAccounts().keys(), 'list', 'keys',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                           name=name, keyTypes='USER_MANAGED')
    except GAPI.permissionDenied:
      _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
      return False
    except GAPI.badRequest as e:
      _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
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
    _getMain().printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPLOADING_NEW_PUBLIC_CERTIFICATE_TO_GOOGLE)
    for retry in range(1, maxRetries+1):
      try:
        result = _getMain().callGAPI(iam.projects().serviceAccounts().keys(), 'upload',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION],
                          name=name, body={'publicKeyData': publicKeyData})
        newPrivateKeyId = result['name'].rsplit('/', 1)[-1]
        break
      except GAPI.notFound as e:
        if retry == maxRetries:
          _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
          return False
        _waitForSvcAcctCompletion(retry)
      except GAPI.permissionDenied:
        if retry == maxRetries:
          _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
          return False
        _waitForSvcAcctCompletion(retry)
      except GAPI.badRequest as e:
        _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
        return False
      except GAPI.failedPrecondition as e:
        _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
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
        result = _getMain().callGAPI(iam.projects().serviceAccounts().keys(), 'create',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                          name=name, body=body)
        newPrivateKeyId = result['name'].rsplit('/', 1)[-1]
        break
      except GAPI.permissionDenied:
        if retry == maxRetries:
          _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
          return False
        _waitForSvcAcctCompletion(retry)
      except GAPI.badRequest as e:
        _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
        return False
    oauth2service_data = base64.b64decode(result['privateKeyData']).decode(_getMain().UTF8)
  if newPrivateKeyId != '':
    _getMain().entityActionPerformed([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail, Ent.SVCACCT_KEY, newPrivateKeyId])
  if GM.Globals[GM.SVCACCT_SCOPES_DEFINED]:
    try:
      GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = json.loads(oauth2service_data)
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      _getMain().invalidOauth2serviceJsonExit(str(e))
    GM.Globals[GM.OAUTH2SERVICE_JSON_DATA][API.OAUTH2SA_SCOPES] = GM.Globals[GM.SVCACCT_SCOPES]
    oauth2service_data = json.dumps(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA], ensure_ascii=False, indent=2, sort_keys=True)
  _getMain().writeFile(GC.Values[GC.OAUTH2SERVICE_JSON], oauth2service_data, continueOnError=False)
  Act.Set(Act.UPDATE)
  _getMain().entityActionPerformed([Ent.OAUTH2SERVICE_JSON_FILE, GC.Values[GC.OAUTH2SERVICE_JSON],
                         Ent.SVCACCT_KEY, newPrivateKeyId])
  if mode in {'retainexisting', 'upload'}:
    return newPrivateKeyId != ''
  Act.Set(Act.REVOKE)
  count = len(keys) if mode == 'retainnone' else 1
  _getMain().entityPerformActionNumItems([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], count, Ent.SVCACCT_KEY)
  Ind.Increment()
  i = 0
  for key in keys:
    keyName = key['name'].rsplit('/', 1)[-1]
    if mode == 'retainnone' or keyName == currentPrivateKeyId and keyName != newPrivateKeyId:
      i += 1
      maxRetries = 5
      for retry in range(1, maxRetries+1):
        try:
          _getMain().callGAPI(iam.projects().serviceAccounts().keys(), 'delete',
                   throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                   name=key['name'])
          _getMain().entityActionPerformed([Ent.SVCACCT_KEY, keyName], i, count)
          break
        except GAPI.permissionDenied:
          if retry == maxRetries:
            _getMain().entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
            break
          _waitForSvcAcctCompletion(retry)
        except GAPI.badRequest as e:
          _getMain().entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], str(e), i, count)
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
  login_hint = _getMain().getEmailAddress(noUid=True) if _getMain().checkArgumentPresent(['admin']) else None
  httpObj, _ = getCRMService(login_hint)
  iam = _getMain().getAPIService(API.IAM, httpObj)
  if doProcessSvcAcctKeys(mode='upload', iam=iam):
    sa_email = GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_email']
    _grantRotateRights(iam, GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['project_id'], sa_email)
    sys.stdout.write(Msg.YOUR_GAM_PROJECT_IS_CREATED_AND_READY_TO_USE)

# gam delete sakeys <ServiceAccountKeyList>
def doDeleteSvcAcctKeys():
  _, iam = _getMain().buildGAPIServiceObject(API.IAM, None)
  doit = False
  keyList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'doit':
      doit = True
    else:
      Cmd.Backup()
      keyList.extend(_getMain().getString(Cmd.OB_SERVICE_ACCOUNT_KEY_LIST, minLen=0).strip().replace(',', ' ').split())
  currentPrivateKeyId, projectId, clientEmail, clientId = _getSvcAcctKeyProjectClientFields()
  name = f'projects/{projectId}/serviceAccounts/{clientId}'
  try:
    keys = _getMain().callGAPIitems(iam.projects().serviceAccounts().keys(), 'list', 'keys',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                         name=name, keyTypes='USER_MANAGED')
  except GAPI.permissionDenied:
    _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
    return
  except GAPI.badRequest as e:
    _getMain().entityActionFailedWarning([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], str(e))
    return
  Act.Set(Act.REVOKE)
  count = len(keyList)
  _getMain().entityPerformActionNumItems([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], count, Ent.SVCACCT_KEY)
  Ind.Increment()
  i = 0
  for dkeyName in keyList:
    i += 1
    for key in keys:
      keyName = key['name'].rsplit('/', 1)[-1]
      if keyName == dkeyName:
        if keyName == currentPrivateKeyId and not doit:
          _getMain().entityActionNotPerformedWarning([Ent.SVCACCT_KEY, keyName],
                                          Msg.USE_DOIT_ARGUMENT_TO_PERFORM_ACTION+Msg.ON_CURRENT_PRIVATE_KEY, i, count)
          break
        try:
          _getMain().callGAPI(iam.projects().serviceAccounts().keys(), 'delete',
                   throwReasons=[GAPI.BAD_REQUEST, GAPI.PERMISSION_DENIED],
                   name=key['name'])
          _getMain().entityActionPerformed([Ent.SVCACCT_KEY, keyName], i, count)
        except GAPI.permissionDenied:
          _getMain().entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], Msg.UPDATE_PROJECT_TO_VIEW_MANAGE_SAKEYS)
        except GAPI.badRequest as e:
          _getMain().entityActionFailedWarning([Ent.SVCACCT_KEY, keyName], str(e), i, count)
        break
    else:
      _getMain().entityActionNotPerformedWarning([Ent.SVCACCT_KEY, dkeyName], Msg.NOT_FOUND, i, count)
  Ind.Decrement()

# gam show sakeys [all|system|user]
def doShowSvcAcctKeys():
  _, iam = _getMain().buildGAPIServiceObject(API.IAM, None)
  keyTypes = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in SVCACCT_KEY_TYPE_CHOICE_MAP:
      keyTypes = SVCACCT_KEY_TYPE_CHOICE_MAP[myarg]
    else:
      _getMain().unknownArgumentExit()
  currentPrivateKeyId, projectId, clientEmail, clientId = _getSvcAcctKeyProjectClientFields()
  name = f'projects/{projectId}/serviceAccounts/{clientId}'
  status, keys = _getSAKeys(iam, projectId, clientEmail, name, keyTypes)
  if not status:
    return
  count = len(keys)
  _getMain().entityPerformActionNumItems([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], count, Ent.SVCACCT_KEY)
  if count > 0:
    _showSAKeys(keys, count, currentPrivateKeyId)

# gam create gcpserviceaccount|signjwtserviceaccount
def doCreateGCPServiceAccount():
  _getMain().checkForExtraneousArguments()
  _checkForExistingProjectFiles([GC.Values[GC.OAUTH2SERVICE_JSON]])
  sa_info = {'key_type': 'signjwt', 'token_uri': API.GOOGLE_OAUTH2_TOKEN_ENDPOINT, 'type': 'service_account'}
  request = _getMain().get_adc_request()
  try:
    credentials, sa_info['project_id'] = google.auth.default(scopes=[API.IAM_SCOPE], request=request)
  except (google.auth.exceptions.DefaultCredentialsError, google.auth.exceptions.RefreshError) as e:
    _getMain().systemErrorExit(_getMain().API_ACCESS_DENIED_RC, str(e))
  credentials.refresh(request)
  sa_info['client_email'] = credentials.service_account_email
  oa2 = _getMain().buildGAPIObjectNoAuthentication(API.OAUTH2)
  try:
    token_info = _getMain().callGAPI(oa2, 'tokeninfo',
                          throwReasons=[GAPI.INVALID],
                          access_token=credentials.token)
  except GAPI.invalid as e:
    _getMain().systemErrorExit(_getMain().API_ACCESS_DENIED_RC, str(e))
  sa_info['client_id'] = token_info['issued_to']
  sa_output = json.dumps(sa_info, ensure_ascii=False, indent=2, sort_keys=True)
  _getMain().writeStdout(f'Writing SignJWT service account data:\n\n{sa_output}\n')
  _getMain().writeFile(GC.Values[GC.OAUTH2SERVICE_JSON], sa_output, continueOnError=False)

# Audit command utilities
