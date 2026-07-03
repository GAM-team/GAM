"""Drive labels and label permissions.

Part of the drive sub-package, extracted from drive.py."""

"""GAM Google Drive file, permission, shared drive, and label management."""

import re
import json
import sys

from gam.cmd.drive.core import _validateUserGetFileIDs, getDriveFileEntity

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import _getAdminEmail, buildGAPIServiceObject, callGAPI, callGAPIpages
from gam.util.args import (
    BCP47_LANGUAGE_CODES_MAP,
    getArgument,
    getBoolean,
    getChoice,
    getEmailAddress,
    getInteger,
    getLanguageCode,
    getString,
    getYYYYMMDD,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    entityPerformActionSubItemModifierNumItems,
    getPageMessageForWhom,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printLine,
    userDriveServiceNotEnabledWarning,
)
from gam.util.entity import (
    _validateUserGetObjectList,
    convertEmailAddressToUID,
    convertEntityToList,
    convertUIDtoEmailAddressWithType,
    getEntityArgument,
    getEntityList,
    getUserObjectEntity,
)
from gam.util.errors import missingArgumentExit, unknownArgumentExit, usageErrorExit

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()

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
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "
WITH_ANY_FILE_NAME = "name = '{0}'"
WITH_MY_FILE_NAME = ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
WITH_OTHER_FILE_NAME = NOT_ME_IN_OWNERS_AND + WITH_ANY_FILE_NAME
ROOT = 'root'
ORPHANS = 'Orphans'
SHARED_WITHME = 'SharedWithMe'
SHARED_DRIVES = 'SharedDrives'

def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def _getDisplayDriveLabelsParameters(myarg, parameters):
  if myarg in DRIVELABELS_PROJECTION_CHOICE_MAP:
    parameters['view'] = DRIVELABELS_PROJECTION_CHOICE_MAP[myarg]
  elif myarg == 'language':
    parameters['languageCode'] = getLanguageCode(BCP47_LANGUAGE_CODES_MAP)
  elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
    parameters['useAdminAccess'] = True
  elif myarg == 'publishedonly':
    parameters['publishedOnly'] = getBoolean()
  elif myarg == 'minimumrole':
    parameters['minimumRole'] = getChoice(DRIVELABELS_PERMISSION_ROLE_MAP, mapChoice=True)
  else:
    return False
  return True

def normalizeDriveLabelID(driveLabelID):
  atLoc = driveLabelID.find('@')
  if atLoc != -1:
    driveLabelID = driveLabelID[:atLoc]
  if driveLabelID.startswith('labels/'):
    return driveLabelID[7:]
  return driveLabelID

def normalizeDriveLabelName(driveLabelName):
  if driveLabelName.startswith('labels/'):
    return driveLabelName
  return f'labels/{driveLabelName}'

def validateDriveLabelName(name, kvList, j, jcount, permName=False):
  name = normalizeDriveLabelName(name)
# Label name
  if not permName:
    mg = re.match(r'^(labels/[^/]+)$', name)
    if not mg:
      entityActionNotPerformedWarning(kvList, 'Expected labels/<String>', j, jcount)
      return None
    return name
# Label permission name
  mg = re.match(r'^(labels/[^/]+)/permissions/(?:audiences|groups|people)/.+$', name)
  if not mg:
    entityActionNotPerformedWarning(kvList, 'Expected labels/<String>/permissions/(audiences|groups|people)/<String>', j, jcount)
    return (None, None)
  return (name, mg.group(1))

def _showDriveLabel(label, j, jcount, FJQC):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(label, timeObjects=DRIVELABELS_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CLASSIFICATION_LABEL_NAME, f'{label["name"]}'], j, jcount)
  Ind.Increment()
  showJSON(None, label, timeObjects=DRIVELABELS_TIME_OBJECTS, dictObjectsKey={'fields': 'id', 'choices': 'id'})
  Ind.Decrement()

# gam [<UserTypeEntity>] info classificationlabels <ClassificationLabelNameEntity>
#	[[basic|full] [languagecode <BCP47LanguageCode>]
#	[formatjson] [asadmin]
def infoDriveLabels(users, useAdminAccess=False):
  driveLabelNameEntity = getUserObjectEntity(Cmd.OB_CLASSIFICATION_LABEL_NAME, Ent.CLASSIFICATION_LABEL, shlexSplit=True)
  FJQC = FormatJSONQuoteChar()
  parameters = {'useAdminAccess': useAdminAccess}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getDisplayDriveLabelsParameters(myarg, parameters):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  api = API.DRIVELABELS_ADMIN if parameters['useAdminAccess'] else API.DRIVELABELS_USER
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, labelNames, jcount = _validateUserGetObjectList(user, i, count, driveLabelNameEntity,
                                                                 api=api, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in labelNames:
      j += 1
      kvList = [Ent.USER, user, Ent.CLASSIFICATION_LABEL_NAME, name]
      name = validateDriveLabelName(name, kvList, j, jcount, False)
      if name is None:
        continue
      try:
        label = callGAPI(drive.labels(), 'get',
                         bailOnInternalError=True,
                         throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED,
                                                                     GAPI.INVALID_ARGUMENT, GAPI.INTERNAL_ERROR],
                         name=name, **parameters)
        _showDriveLabel(label, j, jcount, FJQC)
      except GAPI.notFound as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.permissionDenied, GAPI.invalidArgument, GAPI.internalError) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
        break
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

def doInfoDriveLabels():
  infoDriveLabels([_getAdminEmail()], True)

# gam [<UserTypeEntity>] print classificationlabels> [todrive <ToDriveAttribute>*]
#	[basic|full] [languagecode <BCP47LanguageCode>]
#	[publishedonly [<Boolean>]] [minimumrole applier|editor|organizer|reader]
#	[formatjson [quotechar <Character>]] [asadmin]
# gam [<UserTypeEntity>] show classificationlabels
#	[basic|full] [languagecode <BCP47LanguageCode>]
#	[publishedonly [<Boolean>]] [minimumrole applier|editor|organizer|reader]
#	[formatjson] [asadmin]
def printShowDriveLabels(users, useAdminAccess=False):
  csvPF = CSVPrintFile(['User', 'name', 'description', 'id'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  parameters = {'useAdminAccess': useAdminAccess}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getDisplayDriveLabelsParameters(myarg, parameters):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(['User', 'name', 'JSON'])
  api = API.DRIVELABELS_ADMIN if parameters['useAdminAccess'] else API.DRIVELABELS_USER
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive = buildGAPIServiceObject(api, user, i, count)
    if not drive:
      continue
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.CLASSIFICATION_LABEL, user, i, count)
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    try:
      labels = callGAPIpages(drive.labels(), 'list', 'labels',
                             pageMessage=pageMessage,
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                             **parameters, fields='nextPageToken,labels', pageSize=200)
      if not csvPF:
        jcount = len(labels)
        if not FJQC.formatJSON:
          entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CLASSIFICATION_LABEL, i, count)
        Ind.Increment()
        j = 0
        for label in labels:
          j += 1
          _showDriveLabel(label, j, jcount, FJQC)
        Ind.Decrement()
      else:
        for label in labels:
          row = flattenJSON(label, flattened={'User': user}, timeObjects=DRIVELABELS_TIME_OBJECTS)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            row = {'User': user, 'name': label['name']}
            row['JSON'] = json.dumps(cleanJSON(label, timeObjects=DRIVELABELS_TIME_OBJECTS),
                                     ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(row)
    except GAPI.permissionDenied as e:
      entityActionFailedWarning([Ent.USER, user, Ent.CLASSIFICATION_LABEL, None], str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
      userDriveServiceNotEnabledWarning(user, str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Classification Labels')

def doPrintShowDriveLabels():
  printShowDriveLabels([_getAdminEmail()], True)

def _showDriveLabelPermission(labelperm, j, jcount, FJQC):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(labelperm), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CLASSIFICATION_LABEL_PERMISSION_NAME, f'{labelperm["name"]}'], j, jcount)
  Ind.Increment()
  showJSON(None, labelperm)
  Ind.Decrement()

# gam [<UserTypeEntity>] create classificationlabelpermission <ClassificationLabelNameEntity>
#	(user <UserItem>) | (group <GroupItem) | (audience <String>)
#	role applier|editor|organizer|reader
#	[nodetails|formatjson] [asadmin]
def createDriveLabelPermissions(users, useAdminAccess=False):
  driveLabelNameEntity = getUserObjectEntity(Cmd.OB_CLASSIFICATION_LABEL_NAME, Ent.CLASSIFICATION_LABEL_PERMISSION, shlexSplit=True)
  FJQC = FormatJSONQuoteChar()
  parameters = {'useAdminAccess': useAdminAccess}
  body = {}
  showDetails = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      parameters['useAdminAccess'] = True
    elif myarg == 'role':
      body['role'] = getChoice(DRIVELABELS_PERMISSION_ROLE_MAP, mapChoice=True)
    elif myarg in {'user', 'group'}:
      email = getEmailAddress(returnUIDprefix='id:')
      body['email'], status = convertUIDtoEmailAddressWithType(email, emailTypes=[myarg])
      if status == 'unknown':
        Cmd.Backup()
        usageErrorExit(Msg.ENTITY_DOES_NOT_EXIST.format(email))
    elif myarg == 'audience':
      audience = getString(Cmd.OB_STRING)
      if not audience.startswith('audiences/'):
        audience = 'audiences/'+audience
      body['audience'] = audience
    elif myarg == 'nodetails':
      showDetails = False
    else:
      FJQC.GetFormatJSON(myarg)
  if 'role' not in body:
    missingArgumentExit(f'role {"|".join(DRIVELABELS_PERMISSION_ROLE_MAP.keys())}')
  if 'email' not in body and 'audience' not in body:
    missingArgumentExit('(user <UserItem>) | (group <GroupItem) | (audience <String>)')
  api = API.DRIVELABELS_ADMIN if parameters['useAdminAccess'] else API.DRIVELABELS_USER
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, labelNames, jcount = _validateUserGetObjectList(user, i, count, driveLabelNameEntity,
                                                                 api=api, showAction=not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in labelNames:
      j += 1
      kvList = [Ent.USER, user, Ent.CLASSIFICATION_LABEL_NAME, name, Ent.CLASSIFICATION_LABEL_PERMISSION, None]
      name = validateDriveLabelName(name, kvList, j, jcount, False)
      if name is None:
        continue
      try:
        labelperm = callGAPI(drive.labels().permissions(), 'create',
                             bailOnInternalError=True,
                             throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.NOT_FOUND,
                                                                         GAPI.INVALID, GAPI.INTERNAL_ERROR],
                             parent=name, body=body, **parameters)
        kvList = [Ent.USER, user, Ent.CLASSIFICATION_LABEL_PERMISSION, labelperm['name']]
        if not FJQC.formatJSON:
          entityActionPerformed(kvList, j, jcount)
        if showDetails:
          Ind.Increment()
          _showDriveLabelPermission(labelperm, j, jcount, FJQC)
          Ind.Decrement()
      except (GAPI.permissionDenied, GAPI.notFound, GAPI.invalid, GAPI.internalError)  as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

def doCreateDriveLabelPermissions():
  createDriveLabelPermissions([_getAdminEmail()], True)

# gam [<UserTypeEntity>] delete classificationlabelpermission <ClassificationLabelNameEntity>
#	(user <UserItem>) | (group <GroupItem) | (audience <String>)
#	[asadmin]
# gam [<UserTypeEntity>] remove classificationlabelpermission <ClassificationLabelPermissionNameEntity>
#	[asadmin]
def deleteDriveLabelPermissions(users, useAdminAccess=False):
  doDelete = Act.Get() == Act.DELETE
  if doDelete:
    driveLabelNameEntity = getUserObjectEntity(Cmd.OB_CLASSIFICATION_LABEL_NAME, Ent.CLASSIFICATION_LABEL, shlexSplit=True)
  else:
    driveLabelNameEntity = getUserObjectEntity(Cmd.OB_CLASSIFICATION_LABEL_PERMISSION_NAME, Ent.CLASSIFICATION_LABEL_PERMISSION, shlexSplit=True)
  parameters = {'useAdminAccess': useAdminAccess, 'requests': [None]}
  labelperm = ''
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      parameters['useAdminAccess'] = True
    elif doDelete and myarg in {'user', 'group'}:
      labelperm = ['people/', 'groups/'][myarg == 'group']+convertEmailAddressToUID(getEmailAddress(), cd=None, emailType=myarg, savedLocation=None)
    elif doDelete and myarg == 'audience':
      audience = getString(Cmd.OB_STRING)
      if not audience.startswith('audiences/'):
        audience = 'audiences/'+audience
      labelperm = audience
    else:
      unknownArgumentExit()
  if doDelete and not labelperm:
    missingArgumentExit('(user <UserItem>) | (group <GroupItem) | (audience <String>)')
  api = API.DRIVELABELS_ADMIN if parameters['useAdminAccess'] else API.DRIVELABELS_USER
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, labelPermNames, jcount = _validateUserGetObjectList(user, i, count, driveLabelNameEntity,
                                                                     api=api, showAction=True)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in labelPermNames:
      j += 1
      kvList = [Ent.USER, user, Ent.CLASSIFICATION_LABEL_PERMISSION_NAME, name]
      if doDelete:
        parent = validateDriveLabelName(name, kvList, j, jcount, False)
        if parent is None:
          continue
        name = parent+'/permissions/'+labelperm
      else:
        name, parent = validateDriveLabelName(name, kvList, j, jcount, True)
        if name is None:
          continue
      kvList[-1] = name
      parameters['requests'][0] = {'name': name}
      try:
        callGAPI(drive.labels().permissions(), 'batchDelete',
                 throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.INVALID, GAPI.NOT_FOUND],
                 parent=parent, body=parameters)
        entityActionPerformed(kvList, j, jcount)
      except (GAPI.permissionDenied, GAPI.invalid, GAPI.notFound) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()

def doDeleteDriveLabelPermissions():
  deleteDriveLabelPermissions([_getAdminEmail()], True)

# gam [<UserTypeEntity>] print classificationlabelpermissions <ClassificationLabelNameEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]] [asadmin]
# gam [<UserTypeEntity>] show classificationlabelpermissions <ClassificationLabelNameEntity>
#	[formatjson] [asadmin]
def printShowDriveLabelPermissions(users, useAdminAccess=False):
  csvPF = CSVPrintFile(['User', 'name', 'email', 'role', 'person', 'group', 'audience'], 'sortall') if Act.csvFormat() else None
  driveLabelNameEntity = getUserObjectEntity(Cmd.OB_CLASSIFICATION_LABEL_NAME, Ent.CLASSIFICATION_LABEL_PERMISSION, shlexSplit=True)
  FJQC = FormatJSONQuoteChar(csvPF)
  parameters = {'useAdminAccess': useAdminAccess}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      parameters['useAdminAccess'] = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(['User', 'name', 'JSON'])
  api = API.DRIVELABELS_ADMIN if parameters['useAdminAccess'] else API.DRIVELABELS_USER
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, labelNames, jcount = _validateUserGetObjectList(user, i, count, driveLabelNameEntity,
                                                                 api=api, showAction=FJQC is None or not FJQC.formatJSON)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for name in labelNames:
      j += 1
      kvList = [Ent.USER, user, Ent.CLASSIFICATION_LABEL_NAME, name, Ent.CLASSIFICATION_LABEL_PERMISSION, None]
      name = validateDriveLabelName(name, kvList, j, jcount, False)
      if name is None:
        continue
      kvList = [Ent.USER, user, Ent.CLASSIFICATION_LABEL_NAME, name]
      if csvPF:
        printGettingAllEntityItemsForWhom(Ent.CLASSIFICATION_LABEL_PERMISSION, name, j, jcount)
        pageMessage = getPageMessageForWhom()
      else:
        pageMessage = None
      try:
        labelperms = callGAPIpages(drive.labels().permissions(), 'list', 'labelPermissions',
                                   pageMessage=pageMessage,
                                   throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.NOT_FOUND],
                                   parent=name, **parameters, fields='nextPageToken,labelPermissions', pageSize=200)
        if not csvPF:
          jcount = len(labelperms)
          if not FJQC.formatJSON:
            entityPerformActionNumItems(kvList, jcount, Ent.CLASSIFICATION_LABEL_PERMISSION, i, count)
          Ind.Increment()
          j = 0
          for labelperm in labelperms:
            j += 1
            _showDriveLabelPermission(labelperm, j, jcount, FJQC)
          Ind.Decrement()
        else:
          for labelperm in labelperms:
            row = flattenJSON(labelperm, flattened={'User': user})
            if not FJQC.formatJSON:
              csvPF.WriteRowTitles(row)
            elif csvPF.CheckRowTitles(row):
              row = {'User': user, 'name': labelperm['name']}
              row['JSON'] = json.dumps(cleanJSON(labelperm), ensure_ascii=False, sort_keys=True)
              csvPF.WriteRowNoFilter(row)
      except (GAPI.permissionDenied, GAPI.notFound) as e:
        entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
        userDriveServiceNotEnabledWarning(user, str(e), i, count)
        break
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Classification Label Permissions')

def doPrintShowDriveLabelPermissions():
  printShowDriveLabelPermissions([_getAdminEmail()], True)

DRIVELABEL_FIELD_TYPE_MAP = {
  'text': 'setTextValues',
  'selection': 'setSelectionValues',
  'integer': 'setIntegerValues',
  'date': 'setDateValues',
  'user': 'setUserValues',
  }

# gam <UserTypeEntity> process filedrivelabels <DriveFileEntity>
#	(addlabel <ClassificationLabelIDList>)*
#	(deletelabel <ClassificationLabelIDList>)*
#	(addlabelfield <ClassificationLabelID> <ClassificationLabelFieldID>
#	    (text <String>)|selection <ClassificationLabelSelectionIDList>)|
#	    (integer <Number>)|(date <Date>)|(user <EmailAddressList>))*
#	(deletelabelfield <ClassificationLabelID> <ClassificationLabelFieldID>)*
#	[nodetails]
def processFileDriveLabels(users):
  fileIdEntity = getDriveFileEntity()
  actionList = {'addlabel': {'action': Act.CREATE, 'list': []},
                'deletelabel': {'action': Act.DELETE, 'list': []},
                'addlabelfield': {'action': Act.CREATE, 'list': []},
                'deletelabelfield': {'action': Act.DELETE, 'list': []},
               }
  showDetails = True
  kcount = 0
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'addlabel':
      labelIds = getEntityList(Cmd.OB_CLASSIFICATION_LABEL_ID, shlexSplit=True)
      for labelId in labelIds:
        actionList[myarg]['list'].append({'labelModifications': [{'labelId': normalizeDriveLabelID(labelId)}]})
        kcount += 1
    elif myarg == 'deletelabel':
      labelIds = getEntityList(Cmd.OB_CLASSIFICATION_LABEL_ID, shlexSplit=True)
      for labelId in labelIds:
        actionList[myarg]['list'].append({'labelModifications': [{'labelId': normalizeDriveLabelID(labelId), 'removeLabel': True}]})
        kcount += 1
    elif myarg == 'addlabelfield':
      labelId = normalizeDriveLabelID(getString(Cmd.OB_CLASSIFICATION_LABEL_ID))
      fieldId = getString(Cmd.OB_CLASSIFICATION_LABEL_FIELD_ID)
      fieldType = getChoice(DRIVELABEL_FIELD_TYPE_MAP, mapChoice=True)
      if fieldType == 'setTextValues':
        valueList = [getString(Cmd.OB_STRING, minLen=0)]
      elif fieldType == 'setSelectionValues':
        valueList = convertEntityToList(getString(Cmd.OB_CLASSIFICATION_LABEL_SELECTION_ID_LIST, minLen=0), shlexSplit=True)
      elif fieldType == 'setIntegerValues':
        valueList = [getInteger()]
      elif fieldType == 'setDateValues':
        valueList = [getYYYYMMDD()]
      else: #elif fieldType == 'setUserValues':
        valueList = convertEntityToList(getString(Cmd.OB_EMAIL_ADDRESS_LIST, minLen=0))
      actionList[myarg]['list'].append({'labelModifications': [{'labelId': labelId,
                                                                'fieldModifications': [{'fieldId': fieldId, fieldType: valueList}]}]})
      kcount += 1
    elif myarg == 'deletelabelfield':
      labelId = normalizeDriveLabelID(getString(Cmd.OB_CLASSIFICATION_LABEL_ID))
      fieldId = getString(Cmd.OB_CLASSIFICATION_LABEL_FIELD_ID)
      actionList[myarg]['list'].append({'labelModifications': [{'labelId': labelId,
                                                                'fieldModifications': [{'fieldId': fieldId, 'unsetValues': True}]}]})
      kcount += 1
    elif myarg == 'nodetails':
      showDetails = False
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, drive, jcount = _validateUserGetFileIDs(user, i, count, fileIdEntity, entityType=None)
    if jcount == 0:
      continue
    Act.Set(Act.PROCESS)
    entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.CLASSIFICATION_LABEL, Act.MODIFIER_FOR, jcount, Ent.DRIVE_FILE_OR_FOLDER)
    Ind.Increment()
    j = 0
    userError = False
    for fileId in fileIdEntity['list']:
      j += 1
      k = 0
      kvList = [Ent.USER, user, Ent.DRIVE_FILE_OR_FOLDER_ID, fileId]
      Act.Set(Act.PROCESS)
      entityPerformActionNumItems(kvList, kcount, Ent.CLASSIFICATION_LABEL)
      Ind.Increment()
      for operation in ['deletelabelfield', 'deletelabel', 'addlabel', 'addlabelfield']:
        Act.Set(actionList[operation]['action'])
        for action in actionList[operation]['list']:
          k += 1
          xkvList = kvList.copy()
          xkvList.extend([Ent.CLASSIFICATION_LABEL_ID, action['labelModifications'][0]['labelId']])
          if 'fieldModifications' in action['labelModifications'][0]:
            xkvList.extend([Ent.CLASSIFICATION_LABEL_FIELD_ID, action['labelModifications'][0]['fieldModifications'][0]['fieldId']])
          try:
            label = callGAPI(drive.files(), 'modifyLabels',
                             throwReasons=GAPI.DRIVE3_MODIFY_LABEL_THROW_REASONS,
                             fileId=fileId, body=action)
            entityActionPerformed(xkvList, k, kcount)
            if showDetails:
              Ind.Increment()
              showJSON(None, label, timeObjects=DRIVELABELS_TIME_OBJECTS, dictObjectsKey={'fields': 'id', 'modifiedLabels': 'id'})
              Ind.Decrement()
          except GAPI.fileNotFound as e:
            entityActionFailedWarning(kvList, str(e), j, jcount)
            break
          except (GAPI.notFound, GAPI.forbidden, GAPI.internalError,
                  GAPI.fileNeverWritable, GAPI.applyLabelForbidden,
                  GAPI.insufficientFilePermissions, GAPI.unknownError, GAPI.invalidInput, GAPI.badRequest,
                  GAPI.labelMutationUnknownField, GAPI.labelMutationIllegalSelection, GAPI.labelMutationForbidden,
                  GAPI.labelMultipleValuesForSingularField) as e:
            entityActionFailedWarning(xkvList, str(e), k, kcount)
          except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
            userDriveServiceNotEnabledWarning(user, str(e), i, count)
            userError = True
            break
      Ind.Decrement()
      if userError:
        break
    Ind.Decrement()

# gam print ownership <DriveFileID>|(drivefilename <DriveFileName>) [todrive <ToDriveAttribute>*]
#	(addcsvdata <FieldName> <String>)*
#	[formatjson [quotechar <Character>]]
# gam show ownership <DriveFileID>|(drivefilename <DriveFileName>)
#	[formatjson]
