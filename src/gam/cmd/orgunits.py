"""GAM organizational unit management."""

import json

from gam.util.csv_pf import RI_I, RI_J, RI_JCOUNT, RI_ITEM
import time

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import (
    _finalizeGAPIpagesResult,
    _processGAPIpagesResult,
    buildGAPIObject,
    callGAPI,
    callGAPIpages,
    checkGAPIError,
    waitOnFailure,
    yieldGAPIpages,
)
from gam.util.args import (
    ARCHIVED_ARGUMENTS,
    SUSPENDED_ARGUMENTS,
    _getIsArchived,
    _getIsSuspended,
    checkArgumentPresent,
    checkForExtraneousArguments,
    encodeOrgUnitPath,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getChoice,
    getHTTPError,
    getInteger,
    getString,
    getStringWithCRsNLs,
    makeOrgUnitPathAbsolute,
    makeOrgUnitPathRelative,
    normalizeEmailAddressOrUID,
    orgUnitPathQuery,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    batchRequestID,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityDuplicateWarning,
    entityModifierActionFailedWarning,
    entityModifierActionPerformed,
    entityPerformActionNumItems,
    entityPerformActionNumItemsModifier,
    getPageMessage,
    getPageMessageForWhom,
    printEntitiesCount,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printGotAccountEntities,
    printGotEntityItemsForWhom,
    printKeyValueList,
    printKeyValueWithCRsNLs,
)
from gam.util.entity import _getCustomerIdNoC, _getCustomersCustomerIdWithC, getEntityList, getEntityToModify, getItemsToModify
from gam.util.errors import (
    entityActionFailedExit,
    entityDoesNotExistExit,
    invalidChoiceExit,
    missingArgumentExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.fileio import DEFAULT_FILE_WRITE_MODE, closeFile, openFile, setFilePath
from gam.util.orgunits import getOrgUnitId, getOrgUnitItem, getTopLevelOrgId
from gam.util.output import (
    executeBatch,
    setSysExitRC,
    systemErrorExit,
    writeStderr,
    writeStdout,
)
from gam.constants import INVALID_DOMAIN_RC, ORGUNIT_NOT_EMPTY_RC

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


WARNING_PREFIX = 'WARNING: '

def doCreateOrg():

  def _createOrg(body, parentPath, fullPath):
    try:
      callGAPI(cd.orgunits(), 'insert',
               throwReasons=[GAPI.INVALID_PARENT_ORGUNIT, GAPI.INVALID_ORGUNIT, GAPI.BACKEND_ERROR, GAPI.BAD_REQUEST, GAPI.INVALID_CUSTOMER_ID, GAPI.LOGIN_REQUIRED],
               customerId=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
      entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, fullPath])
    except GAPI.invalidParentOrgunit:
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, fullPath, Ent.PARENT_ORGANIZATIONAL_UNIT, parentPath], Msg.ENTITY_DOES_NOT_EXIST.format(Ent.Singular(Ent.PARENT_ORGANIZATIONAL_UNIT)))
      return False
    except (GAPI.invalidOrgunit, GAPI.backendError):
      entityDuplicateWarning([Ent.ORGANIZATIONAL_UNIT, fullPath])
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, fullPath)
    return True

  cd = buildGAPIObject(API.DIRECTORY)
  name = getOrgUnitItem(pathOnly=True, absolutePath=False)
  parent = ''
  body = {}
  buildPath = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'description':
      body['description'] = getStringWithCRsNLs()
    elif myarg == 'parent':
      parent = getOrgUnitItem()
    elif myarg == 'buildpath':
      buildPath = True
    else:
      unknownArgumentExit()
  if parent.startswith('id:'):
    parentPath = None
    try:
      parentPath = callGAPI(cd.orgunits(), 'get',
                            throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                            customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=parent, fields='orgUnitPath')['orgUnitPath']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      pass
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      errMsg = accessErrorMessage(cd)
      if errMsg:
        systemErrorExit(INVALID_DOMAIN_RC, errMsg)
    if not parentPath and not buildPath:
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, name, Ent.PARENT_ORGANIZATIONAL_UNIT, parent], Msg.ENTITY_DOES_NOT_EXIST.format(Ent.Singular(Ent.PARENT_ORGANIZATIONAL_UNIT)))
      return
    parent = parentPath
  if parent == '/':
    orgUnitPath = parent+name
  else:
    orgUnitPath = parent+'/'+name
  if orgUnitPath.count('/') > 1:
    body['parentOrgUnitPath'], body['name'] = orgUnitPath.rsplit('/', 1)
  else:
    body['parentOrgUnitPath'] = '/'
    body['name'] = orgUnitPath[1:]
  parent = body['parentOrgUnitPath']
  if _createOrg(body, parent, orgUnitPath) or not buildPath:
    return
  description = body.pop('description', None)
  fullPath = '/'
  getPath = ''
  orgNames = orgUnitPath.split('/')
  n = len(orgNames)-1
  for i in range(1, n+1):
    body['parentOrgUnitPath'] = fullPath
    if fullPath != '/':
      fullPath += '/'
    fullPath += orgNames[i]
    if getPath != '':
      getPath += '/'
    getPath += orgNames[i]
    try:
      callGAPI(cd.orgunits(), 'get',
               throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
               customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(getPath), fields='')
      printKeyValueList([Ent.Singular(Ent.ORGANIZATIONAL_UNIT), fullPath, Msg.EXISTS])
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      body['name'] = orgNames[i]
      if i == n and description:
        body['description'] = description
      if not _createOrg(body, body['parentOrgUnitPath'], fullPath):
        return
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, fullPath)

def checkOrgUnitPathExists(cd, orgUnitPath, i=0, count=0, showError=False):
  if orgUnitPath == '/':
    _, orgUnitId = getOrgUnitId(cd, orgUnitPath)
    return (True, orgUnitPath, orgUnitId)
  try:
    orgUnit = callGAPI(cd.orgunits(), 'get',
                       throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                       customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(orgUnitPath)),
                       fields='orgUnitPath,orgUnitId')
    return (True, orgUnit['orgUnitPath'], orgUnit['orgUnitId'])
  except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
    pass
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    errMsg = accessErrorMessage(cd)
    if errMsg:
      systemErrorExit(INVALID_DOMAIN_RC, errMsg)
  if showError:
    entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.DOES_NOT_EXIST, i, count)
  return (False, orgUnitPath, orgUnitPath)

def _batchMoveCrOSesToOrgUnit(cd, orgUnitPath, orgUnitId, i, count, items, quickCrOSMove, fromOrgUnitPath=None):
  def _callbackMoveCrOSesToOrgUnit(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      if not fromOrgUnitPath:
        entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        entityModifierActionPerformed([Ent.ORGANIZATIONAL_UNIT, fromOrgUnitPath, Ent.CROS_DEVICE, ri[RI_ITEM]], toOrgUnitPath, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in [GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN]:
        checkEntityItemValueAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        errMsg = getHTTPError({}, http_status, reason, message)
        if not fromOrgUnitPath:
          entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        else:
          entityModifierActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, fromOrgUnitPath, Ent.CROS_DEVICE, ri[RI_ITEM]], toOrgUnitPath, errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  jcount = len(items)
  if not fromOrgUnitPath:
    entityPerformActionNumItems([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], jcount, Ent.CROS_DEVICE, i, count)
  else:
    toOrgUnitPath = f'{Act.MODIFIER_TO} {Ent.Singular(Ent.ORGANIZATIONAL_UNIT)}: {orgUnitPath}'
    entityPerformActionNumItemsModifier([Ent.ORGANIZATIONAL_UNIT, fromOrgUnitPath], jcount, Ent.CROS_DEVICE, toOrgUnitPath, i, count)
  Ind.Increment()
  if not quickCrOSMove:
    svcargs = dict([('customerId', GC.Values[GC.CUSTOMER_ID]),
                    ('deviceId', None),
                    ('fields', '')]+GM.Globals[GM.EXTRA_ARGS_LIST])
    if not GC.Values[GC.UPDATE_CROS_OU_WITH_ID]:
      svcargs['body'] = {'orgUnitPath': orgUnitPath}
      method = getattr(cd.chromeosdevices(), 'update')
    else:
      svcargs['body'] = {'orgUnitPath': orgUnitPath, 'orgUnitId': orgUnitId}
      method = getattr(cd.chromeosdevices(), 'patch')
    dbatch = cd.new_batch_http_request(callback=_callbackMoveCrOSesToOrgUnit)
    bcount = 0
    j = 0
    for deviceId in items:
      j += 1
      svcparms = svcargs.copy()
      svcparms['deviceId'] = deviceId
      dbatch.add(method(**svcparms), request_id=batchRequestID('', 0, 0, j, jcount, deviceId))
      bcount += 1
      if bcount >= GC.Values[GC.BATCH_SIZE]:
        executeBatch(dbatch)
        dbatch = cd.new_batch_http_request(callback=_callbackMoveCrOSesToOrgUnit)
        bcount = 0
    if bcount > 0:
      dbatch.execute()
  else:
    bcount = 0
    j = 0
    while bcount < jcount:
      kcount = min(jcount-bcount, GC.Values[GC.BATCH_SIZE])
      try:
        deviceIds = items[bcount:bcount+kcount]
        callGAPI(cd.chromeosdevices(), 'moveDevicesToOu',
                 throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                 customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=orgUnitPath,
                 body={'deviceIds': deviceIds})
        for deviceId in deviceIds:
          j += 1
          entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, deviceId], j, jcount)
        bcount += kcount
      except GAPI.invalidOrgunit:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.INVALID_ORGUNIT, i, count)
        break
      except GAPI.invalidInput as e:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, None], str(e), i, count)
        break
      except GAPI.resourceNotFound as e:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, ','.join(deviceIds)], str(e), i, count)
        break
      except (GAPI.badRequest, GAPI.forbidden):
        checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath, i, count)
        bcount += kcount
  Ind.Decrement()

def _batchMoveUsersToOrgUnit(cd, orgUnitPath, i, count, items, fromOrgUnitPath=None):
  _MOVE_USER_REASON_TO_MESSAGE_MAP = {GAPI.USER_NOT_FOUND: Msg.DOES_NOT_EXIST, GAPI.DOMAIN_NOT_FOUND: Msg.SERVICE_NOT_APPLICABLE, GAPI.FORBIDDEN: Msg.SERVICE_NOT_APPLICABLE}
  def _callbackMoveUsersToOrgUnit(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      if not fromOrgUnitPath:
        entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.USER, ri[RI_ITEM]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        entityModifierActionPerformed([Ent.ORGANIZATIONAL_UNIT, fromOrgUnitPath, Ent.USER, ri[RI_ITEM]], toOrgUnitPath, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError(_MOVE_USER_REASON_TO_MESSAGE_MAP, http_status, reason, message)
      if not fromOrgUnitPath:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.USER, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        entityModifierActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, fromOrgUnitPath, Ent.USER, ri[RI_ITEM]], toOrgUnitPath, errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))

  jcount = len(items)
  if not fromOrgUnitPath:
    entityPerformActionNumItems([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], jcount, Ent.USER, i, count)
  else:
    toOrgUnitPath = f'{Act.MODIFIER_TO} {Ent.Singular(Ent.ORGANIZATIONAL_UNIT)}: {orgUnitPath}'
    entityPerformActionNumItemsModifier([Ent.ORGANIZATIONAL_UNIT, fromOrgUnitPath], jcount, Ent.USER, toOrgUnitPath, i, count)
  Ind.Increment()
  svcargs = dict([('userKey', None), ('body', {'orgUnitPath': orgUnitPath}), ('fields', '')]+GM.Globals[GM.EXTRA_ARGS_LIST])
  method = getattr(cd.users(), 'update')
  dbatch = cd.new_batch_http_request(callback=_callbackMoveUsersToOrgUnit)
  bcount = 0
  j = 0
  for user in items:
    j += 1
    svcparms = svcargs.copy()
    svcparms['userKey'] = normalizeEmailAddressOrUID(user)
    dbatch.add(method(**svcparms), request_id=batchRequestID('', 0, 0, j, jcount, svcparms['userKey']))
    bcount += 1
    if bcount >= GC.Values[GC.BATCH_SIZE]:
      executeBatch(dbatch)
      dbatch = cd.new_batch_http_request(callback=_callbackMoveUsersToOrgUnit)
      bcount = 0
  if bcount > 0:
    dbatch.execute()
  Ind.Decrement()

def _doUpdateOrgs(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  if checkArgumentPresent(['move', 'add']):
    entityType, items = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS, crosAllowed=True)
    orgItemLists = items if isinstance(items, dict) else None
    quickCrOSMove = GC.Values[GC.QUICK_CROS_MOVE]
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if entityType == Cmd.ENTITY_CROS and myarg == 'quickcrosmove':
        quickCrOSMove = getBoolean()
      else:
        unknownArgumentExit()
    Act.Set(Act.ADD)
    i = 0
    count = len(entityList)
    for orgUnitPath in entityList:
      i += 1
      if orgItemLists:
        items = orgItemLists[orgUnitPath]
      status, orgUnitPath, orgUnitId = checkOrgUnitPathExists(cd, orgUnitPath, i, count, True)
      if not status:
        continue
      if entityType == Cmd.ENTITY_USERS:
        _batchMoveUsersToOrgUnit(cd, orgUnitPath, i, count, items)
      else:
        _batchMoveCrOSesToOrgUnit(cd, orgUnitPath, orgUnitId, i, count, items, quickCrOSMove)
  elif checkArgumentPresent(['sync']):
    entityType, syncMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS, crosAllowed=True)
    cmdEntityType = Cmd.ENTITY_OU if entityType == Cmd.ENTITY_USERS else Cmd.ENTITY_CROS_OU
    orgItemLists = syncMembers if isinstance(syncMembers, dict) else None
    if orgItemLists is None:
      syncMembersSet = set(syncMembers)
    removeToOrgUnitPath = '/'
    removeToOrgUnitId = None
    quickCrOSMove = GC.Values[GC.QUICK_CROS_MOVE]
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if entityType == Cmd.ENTITY_CROS and myarg == 'quickcrosmove':
        quickCrOSMove = getBoolean()
      elif myarg == 'removetoou':
        status, removeToOrgUnitPath, removeToOrgUnitId = checkOrgUnitPathExists(cd, getOrgUnitItem())
        if not status:
          entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, removeToOrgUnitPath)
      else:
        unknownArgumentExit()
    if entityType == Cmd.ENTITY_CROS and not removeToOrgUnitId:
      _, removeToOrgUnitPath, removeToOrgUnitId = checkOrgUnitPathExists(cd, removeToOrgUnitPath)
    i = 0
    count = len(entityList)
    for orgUnitPath in entityList:
      i += 1
      if orgItemLists:
        syncMembersSet = set(orgItemLists[orgUnitPath])
      status, orgUnitPath, orgUnitId = checkOrgUnitPathExists(cd, orgUnitPath, i, count, True)
      if not status:
        continue
      currentMembersSet = set(getItemsToModify(cmdEntityType, orgUnitPath))
      if entityType == Cmd.ENTITY_USERS:
        Act.Set(Act.ADD)
        _batchMoveUsersToOrgUnit(cd, orgUnitPath, i, count, list(syncMembersSet-currentMembersSet))
        Act.Set(Act.REMOVE)
        _batchMoveUsersToOrgUnit(cd, removeToOrgUnitPath, i, count, list(currentMembersSet-syncMembersSet), orgUnitPath)
      else:
        Act.Set(Act.ADD)
        _batchMoveCrOSesToOrgUnit(cd, orgUnitPath, orgUnitId, i, count, list(syncMembersSet-currentMembersSet), quickCrOSMove)
        Act.Set(Act.REMOVE)
        _batchMoveCrOSesToOrgUnit(cd, removeToOrgUnitPath, removeToOrgUnitId, i, count, list(currentMembersSet-syncMembersSet), quickCrOSMove, orgUnitPath)
  else:
    body = {}
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'name':
        body['name'] = getString(Cmd.OB_STRING)
      elif myarg == 'description':
        body['description'] = getStringWithCRsNLs()
      elif myarg == 'parent':
        parent = getOrgUnitItem()
        if parent.startswith('id:'):
          body['parentOrgUnitId'] = parent
        else:
          body['parentOrgUnitPath'] = parent
      else:
        unknownArgumentExit()
    i = 0
    count = len(entityList)
    for orgUnitPath in entityList:
      i += 1
      try:
        callGAPI(cd.orgunits(), 'update',
                 throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND, GAPI.BACKEND_ERROR, GAPI.INVALID_ORGUNIT_NAME,
                               GAPI.CONDITION_NOT_MET, GAPI.BAD_REQUEST, GAPI.INVALID_CUSTOMER_ID, GAPI.LOGIN_REQUIRED],
                 customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(orgUnitPath)), body=body, fields='')
        entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], i, count)
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.DOES_NOT_EXIST, i, count)
      except GAPI.invalidOrgunitName as e:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.NAME, body['name']], str(e), i, count)
      except GAPI.conditionNotMet as e:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], str(e), i, count)
      except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath)

# gam update orgs|ous <OrgUnitEntity> [name <String>] [description <String>] [parent <OrgUnitItem>]
# gam update orgs|ous <OrgUnitEntity> add|move <CrosTypeEntity> [quickcrosmove [<Boolean>]]
# gam update orgs|ous <OrgUnitEntity> add|move <UserTypeEntity>
# gam update orgs|ous <OrgUnitEntity> sync <CrosTypeEntity> [removetoou <OrgUnitItem>] [quickcrosmove [<Boolean>]]
# gam update orgs|ous <OrgUnitEntity> sync <UserTypeEntity> [removetoou <OrgUnitItem>]
def doUpdateOrgs():
  _doUpdateOrgs(getEntityList(Cmd.OB_ORGUNIT_ENTITY, shlexSplit=True))

# gam update org|ou <OrgUnitItem> [name <String>] [description <String>] [parent <OrgUnitItem>]
# gam update org|ou <OrgUnitItem> add|move <CrosTypeEntity> [quickcrosmove [<Boolean>]]
# gam update org|ou <OrgUnitItem> add|move <UserTypeEntity>
# gam update org|ou <OrgUnitItem> sync <CrosTypeEntity> [removetoou <OrgUnitItem>] [quickcrosmove [<Boolean>]]
# gam update org|ou <OrgUnitItem> sync <UserTypeEntity> [removetoou <OrgUnitItem>]
def doUpdateOrg():
  _doUpdateOrgs([getOrgUnitItem()])

def _doDeleteOrgs(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for orgUnitPath in entityList:
    i += 1
    try:
      orgUnitPath = makeOrgUnitPathAbsolute(orgUnitPath)
      callGAPI(cd.orgunits(), 'delete',
               throwReasons=[GAPI.CONDITION_NOT_MET, GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND, GAPI.BACKEND_ERROR,
                             GAPI.INVALID_CUSTOMER_ID, GAPI.SERVICE_NOT_AVAILABLE,
                             GAPI.BAD_REQUEST,  GAPI.LOGIN_REQUIRED],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(orgUnitPath)))
      entityActionPerformed([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], i, count)
    except GAPI.conditionNotMet:
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.HAS_CHILD_ORGS.format(Ent.Plural(Ent.ORGANIZATIONAL_UNIT)), i, count)
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.invalidCustomerId, GAPI.serviceNotAvailable) as e:
### Check for my_customer
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID]], str(e), i, count)
    except (GAPI.badRequest, GAPI.loginRequired):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath)

# gam delete orgs|ous <OrgUnitEntity>
def doDeleteOrgs():
  _doDeleteOrgs(getEntityList(Cmd.OB_ORGUNIT_ENTITY, shlexSplit=True))

# gam delete org|ou <OrgUnitItem>
def doDeleteOrg():
  _doDeleteOrgs([getOrgUnitItem()])

ORG_FIELD_INFO_ORDER = ['orgUnitId', 'name', 'description', 'parentOrgUnitPath', 'parentOrgUnitId', 'blockInheritance']
ORG_FIELDS_WITH_CRS_NLS = {'description'}

def _doInfoOrgs(entityList):
  def _printUsers(entityType, orgUnitPath, isSuspended, isArchived):
    users = callGAPIpages(cd.users(), 'list', 'users',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          customer=GC.Values[GC.CUSTOMER_ID], query=orgUnitPathQuery(orgUnitPath, isSuspended, isArchived), orderBy='email',
                          fields='nextPageToken,users(primaryEmail,orgUnitPath)', maxResults=GC.Values[GC.USER_MAX_RESULTS])
    printEntitiesCount(entityType, None)
    usersInOU = 0
    Ind.Increment()
    orgUnitPath = orgUnitPath.lower()
    for user in users:
      if orgUnitPath == user['orgUnitPath'].lower():
        printKeyValueList([user['primaryEmail']])
        usersInOU += 1
      elif showChildren:
        printKeyValueList([f'{user["primaryEmail"]} (child)'])
        usersInOU += 1
    Ind.Decrement()
    printKeyValueList([Msg.TOTAL_ITEMS_IN_ENTITY.format(Ent.Plural(entityType), Ent.Singular(Ent.ORGANIZATIONAL_UNIT)), usersInOU])

  cd = buildGAPIObject(API.DIRECTORY)
  getUsers = True
  isSuspended = isArchived = None
  showChildren = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'nousers':
      getUsers = False
    elif myarg in SUSPENDED_ARGUMENTS:
      isSuspended = _getIsSuspended(myarg)
    elif myarg in ARCHIVED_ARGUMENTS:
      isArchived = _getIsArchived(myarg)
    elif myarg in {'children', 'child'}:
      showChildren = True
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for origOrgUnitPath in entityList:
    i += 1
    try:
      if origOrgUnitPath == '/':
        _, orgUnitPath = getOrgUnitId(cd, origOrgUnitPath)
      else:
        orgUnitPath = makeOrgUnitPathRelative(origOrgUnitPath)
      result = callGAPI(cd.orgunits(), 'get',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(orgUnitPath))
      if 'orgUnitPath' not in result:
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, origOrgUnitPath], Msg.DOES_NOT_EXIST, i, count)
        continue
      printEntity([Ent.ORGANIZATIONAL_UNIT, result['orgUnitPath']], i, count)
      Ind.Increment()
      for field in ORG_FIELD_INFO_ORDER:
        value = result.get(field, None)
        if value is not None:
          if field not in ORG_FIELDS_WITH_CRS_NLS:
            printKeyValueList([field, value])
          else:
            printKeyValueWithCRsNLs(field, value)
      if getUsers:
        orgUnitPath = result['orgUnitPath']
        if isArchived is None and isSuspended is None:
          _printUsers(Ent.USER, orgUnitPath, None, None)
        else:
          if isArchived is not None:
            _printUsers(Ent.USER_ARCHIVED if isArchived else Ent.USER_NOT_ARCHIVED, orgUnitPath, None, isArchived)
          if isSuspended is not None:
            _printUsers(Ent.USER_SUSPENDED if isSuspended else Ent.USER_NOT_SUSPENDED, orgUnitPath, isSuspended, None)
      Ind.Decrement()
    except (GAPI.invalidInput, GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath)

# gam info org|ou <OrgUnitItem>
#	[nousers | ([notarchived|archived] [notsuspended|suspended])] [children|child]
def doInfoOrg():
  _doInfoOrgs([getOrgUnitItem()])

# gam info orgs|ous <OrgUnitEntity>
#	[nousers | ([notarchived|archived] [notsuspended|suspended])] [children|child]
def doInfoOrgs():
  _doInfoOrgs(getEntityList(Cmd.OB_ORGUNIT_ENTITY, shlexSplit=True))

ORG_ARGUMENT_TO_FIELD_MAP = {
  'description': 'description',
  'id': 'orgUnitId',
  'name': 'name',
  'orgunitid': 'orgUnitId',
  'orgunitpath': 'orgUnitPath',
  'path': 'orgUnitPath',
  'parentorgunitid': 'parentOrgUnitId',
  'parentid': 'parentOrgUnitId',
  'parentorgunitpath': 'parentOrgUnitPath',
  'parent': 'parentOrgUnitPath',
  }
ORG_FIELD_PRINT_ORDER = ['orgUnitPath', 'orgUnitId', 'name', 'description', 'parentOrgUnitPath', 'parentOrgUnitId', 'blockInheritance']
PRINT_ORGS_DEFAULT_FIELDS = ['orgUnitPath', 'orgUnitId', 'name', 'parentOrgUnitId']

ORG_UNIT_SELECTOR_FIELD = 'orgUnitSelector'
PRINT_OUS_SELECTOR_CHOICES = [
  Cmd.ENTITY_CROS_OU, Cmd.ENTITY_CROS_OU_AND_CHILDREN,
  Cmd.ENTITY_OU, Cmd.ENTITY_OU_NS, Cmd.ENTITY_OU_SUSP,
  Cmd.ENTITY_OU_AND_CHILDREN, Cmd.ENTITY_OU_AND_CHILDREN_NS, Cmd.ENTITY_OU_AND_CHILDREN_SUSP,
  ]

def _getOrgUnits(cd, orgUnitPath, fieldsList, listType, showParent, batchSubOrgs, childSelector=None, parentSelector=None):
  def _callbackListOrgUnits(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      orgUnits.extend(response.get('organizationUnits', []))
    else:
      http_status, reason, message = checkGAPIError(exception)
      errMsg = getHTTPError({}, http_status, reason, message)
      if reason not in GAPI.DEFAULT_RETRY_REASONS:
        if reason in [GAPI.BAD_REQUEST, GAPI.INVALID_CUSTOMER_ID, GAPI.LOGIN_REQUIRED]:
          accessErrorExit(cd)
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, topLevelOrgUnits[int(ri[RI_I])]], errMsg)
        return
      waitOnFailure(1, 10, reason, message)
      try:
        response = callGAPI(cd.orgunits(), 'list',
                            throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                            customerId=GC.Values[GC.CUSTOMER_ID], type='all', orgUnitPath=topLevelOrgUnits[int(ri[RI_I])], fields=listfields)
        orgUnits.extend(response.get('organizationUnits', []))
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
        entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, topLevelOrgUnits[int(ri[RI_I])]], Msg.DOES_NOT_EXIST)
      except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        accessErrorExit(cd)

  def _batchListOrgUnits():
    svcargs = dict([('customerId', GC.Values[GC.CUSTOMER_ID]), ('orgUnitPath', None), ('type', 'all'), ('fields', listfields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(cd.orgunits(), 'list')
    dbatch = cd.new_batch_http_request(callback=_callbackListOrgUnits)
    bcount = 0
    i = 0
    for orgUnitPath in topLevelOrgUnits:
      svcparms = svcargs.copy()
      svcparms['orgUnitPath'] = orgUnitPath
      dbatch.add(method(**svcparms), request_id=batchRequestID('', i, 0, 0, 0, ''))
      bcount += 1
      i += 1
      if bcount >= GC.Values[GC.BATCH_SIZE]:
        executeBatch(dbatch)
        dbatch = cd.new_batch_http_request(callback=_callbackListOrgUnits)
        bcount = 0
    if bcount > 0:
      dbatch.execute()

  deleteOrgUnitId = deleteParentOrgUnitId = False
  if showParent:
    localFieldsList = fieldsList[:]
    if 'orgUnitId' not in fieldsList:
      localFieldsList.append('orgUnitId')
      deleteOrgUnitId = True
    if 'parentOrgUnitId' not in fieldsList:
      localFieldsList.append('parentOrgUnitId')
      deleteParentOrgUnitId = True
    fields = getFieldsFromFieldsList(localFieldsList)
  else:
    fields = getFieldsFromFieldsList(fieldsList)
  listfields = f'organizationUnits({fields})'
  if listType == 'all' and  orgUnitPath == '/':
    printGettingAllAccountEntities(Ent.ORGANIZATIONAL_UNIT)
  else:
    printGettingAllEntityItemsForWhom(Ent.CHILD_ORGANIZATIONAL_UNIT, orgUnitPath,
                                      qualifier=' (Direct Children)' if listType == 'children' else '', entityType=Ent.ORGANIZATIONAL_UNIT)
  if listType == 'children':
    batchSubOrgs = False
  try:
    orgs = callGAPI(cd.orgunits(), 'list',
                    throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                    customerId=GC.Values[GC.CUSTOMER_ID], type=listType if not batchSubOrgs else 'children',
                    orgUnitPath=orgUnitPath, fields=listfields)
  except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
    entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath], Msg.DOES_NOT_EXIST)
    return None
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    accessErrorExit(cd)
  orgUnits = orgs.get('organizationUnits', [])
  topLevelOrgUnits = [orgUnit['orgUnitPath'] for orgUnit in orgUnits]
  if batchSubOrgs:
    _batchListOrgUnits()
  if showParent:
    parentOrgIds = []
    retrievedOrgIds = []
    if not orgUnits:
      topLevelOrgId = getTopLevelOrgId(cd, orgUnitPath)
      if topLevelOrgId:
        parentOrgIds.append(topLevelOrgId)
    for orgUnit in orgUnits:
      retrievedOrgIds.append(orgUnit['orgUnitId'])
      if orgUnit['parentOrgUnitId'] not in parentOrgIds:
        parentOrgIds.append(orgUnit['parentOrgUnitId'])
    missing_parents = set(parentOrgIds)-set(retrievedOrgIds)
    for missing_parent in missing_parents:
      try:
        result = callGAPI(cd.orgunits(), 'get',
                          throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                          customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=missing_parent, fields=fields)
        orgUnits.append(result)
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError,
              GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        pass
  if listType == 'all' and  orgUnitPath == '/':
    printGotAccountEntities(len(orgUnits))
  else:
    printGotEntityItemsForWhom(len(orgUnits))
  if childSelector is not None:
    for orgUnit in orgUnits:
      orgUnit[ORG_UNIT_SELECTOR_FIELD] = childSelector if orgUnit['orgUnitPath'] != orgUnitPath else parentSelector
  if deleteOrgUnitId or deleteParentOrgUnitId:
    for orgUnit in orgUnits:
      if deleteOrgUnitId:
        orgUnit.pop('orgUnitId', None)
      if deleteParentOrgUnitId:
        orgUnit.pop('parentOrgUnitId', None)
  return orgUnits

def getOrgUnitIdToPathMap(cd=None):
  if cd is None:
    cd = buildGAPIObject(API.DIRECTORY)
  orgUnits = _getOrgUnits(cd, '/', ['orgUnitPath', 'orgUnitId'], 'all', True, False)
  return {ou['orgUnitId']:ou['orgUnitPath'] for ou in orgUnits}

# gam print orgs|ous [todrive <ToDriveAttribute>*]
#	[fromparent <OrgUnitItem>] [showparent] [toplevelonly]
#	[parentselector <OrgUnitSelector> childselector <OrgUnitSelector>]
#	[allfields|<OrgUnitFieldName>*|(fields <OrgUnitFieldNameList>)] [convertcrnl] [batchsuborgs [<Boolean>]]
#	[mincroscount <Number>] [maxcroscount <Number>]
#	[minusercount <Number>] [maxusercount <Number>]
# 	[showitemcountonly]
def doPrintOrgs():
  cd = buildGAPIObject(API.DIRECTORY)
  convertCRNL = GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]
  fieldsList = []
  csvPF = CSVPrintFile(sortTitles=ORG_FIELD_PRINT_ORDER)
  orgUnitPath = '/'
  listType = 'all'
  batchSubOrgs = showParent = False
  childSelector = parentSelector = None
  minCrOSCounts = maxCrOSCounts = minUserCounts = maxUserCounts = -1
  crosCounts = {}
  userCounts = {}
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'fromparent':
      orgUnitPath = getOrgUnitItem()
    elif myarg == 'showparent':
      showParent = getBoolean()
    elif myarg == 'parentselector':
      parentSelector = getChoice(PRINT_OUS_SELECTOR_CHOICES)
    elif myarg == 'childselector':
      childSelector = getChoice(PRINT_OUS_SELECTOR_CHOICES)
    elif myarg == 'mincroscount':
      minCrOSCounts = getInteger(minVal=-1)
    elif myarg == 'maxcroscount':
      maxCrOSCounts = getInteger(minVal=-1)
    elif myarg == 'minusercount':
      minUserCounts = getInteger(minVal=-1)
    elif myarg == 'maxusercount':
      maxUserCounts = getInteger(minVal=-1)
    elif myarg == 'batchsuborgs':
      batchSubOrgs = getBoolean()
    elif myarg == 'toplevelonly':
      listType = 'children'
    elif myarg == 'allfields':
      fieldsList = []
      csvPF.SetTitles(fieldsList)
      for field in ORG_FIELD_PRINT_ORDER:
        csvPF.AddField(field, ORG_ARGUMENT_TO_FIELD_MAP, fieldsList)
    elif myarg in ORG_ARGUMENT_TO_FIELD_MAP:
      if not fieldsList:
        csvPF.AddField('orgUnitPath', ORG_ARGUMENT_TO_FIELD_MAP, fieldsList)
      csvPF.AddField(myarg, ORG_ARGUMENT_TO_FIELD_MAP, fieldsList)
    elif myarg == 'fields':
      if not fieldsList:
        csvPF.AddField('orgUnitPath', ORG_ARGUMENT_TO_FIELD_MAP, fieldsList)
      for field in _getFieldsList():
        if field in ORG_ARGUMENT_TO_FIELD_MAP:
          csvPF.AddField(field, ORG_ARGUMENT_TO_FIELD_MAP, fieldsList)
        else:
          invalidChoiceExit(field, list(ORG_ARGUMENT_TO_FIELD_MAP), True)
    elif myarg in {'convertcrnl', 'converttextnl'}:
      convertCRNL = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      unknownArgumentExit()
  if childSelector:
    if showParent and parentSelector is None:
      missingArgumentExit('parentselector')
    csvPF.AddTitle(ORG_UNIT_SELECTOR_FIELD)
    csvPF.AddSortTitle(ORG_UNIT_SELECTOR_FIELD)
  showCrOSCounts = (minCrOSCounts >= 0 or maxCrOSCounts >= 0)
  showUserCounts = (minUserCounts >= 0 or maxUserCounts >= 0)
  if not fieldsList:
    for field in PRINT_ORGS_DEFAULT_FIELDS:
      csvPF.AddField(field, ORG_ARGUMENT_TO_FIELD_MAP, fieldsList)
  orgUnits = _getOrgUnits(cd, orgUnitPath, fieldsList, listType, showParent, batchSubOrgs, childSelector, parentSelector)
  if showItemCountOnly:
    writeStdout(f'{0 if orgUnits is None else (len(orgUnits))}\n')
    return
  if orgUnits is None:
    return
  if showUserCounts:
    for orgUnit in orgUnits:
      userCounts[orgUnit['orgUnitPath']] = {'suspended': [0, 0], 'archived': [0, 0], 'total': 0}
    qualifier = Msg.IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
    printGettingAllEntityItemsForWhom(Ent.USER, orgUnitPath, qualifier=qualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
    pageMessage = getPageMessageForWhom()
    try:
      feed = yieldGAPIpages(cd.users(), 'list', 'users',
                            pageMessage=pageMessage,
                            throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                          GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            customer=GC.Values[GC.CUSTOMER_ID], query=orgUnitPathQuery(orgUnitPath, None, None), orderBy='email',
                            fields='nextPageToken,users(orgUnitPath,suspended,archived)', maxResults=GC.Values[GC.USER_MAX_RESULTS])
      for users in feed:
        for user in users:
          if user['orgUnitPath'] in userCounts:
            userCounts[user['orgUnitPath']]['suspended'][user['suspended']] += 1
            userCounts[user['orgUnitPath']]['archived'][user['archived']] += 1
            userCounts[user['orgUnitPath']]['total'] += 1
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.invalidInput, GAPI.badRequest, GAPI.backendError,
            GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath)
  for orgUnit in sorted(orgUnits, key=lambda k: k['orgUnitPath']):
    orgUnitPath = orgUnit['orgUnitPath']
    if showCrOSCounts:
      crosCounts[orgUnit['orgUnitPath']] = {}
      printGettingAllEntityItemsForWhom(Ent.CROS_DEVICE, orgUnitPath, entityType=Ent.ORGANIZATIONAL_UNIT)
      pageMessage = getPageMessageForWhom()
      pageToken = None
      totalItems = 0
      tokenRetries = 0
      while True:
        try:
          feed = callGAPI(cd.chromeosdevices(), 'list', 'chromeosdevices',
                          throwReasons=[GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                        GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          pageToken=pageToken,
                          customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=orgUnitPath, includeChildOrgunits=False,
                          fields='nextPageToken,chromeosdevices(status)', maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
          tokenRetries = 0
          pageToken, totalItems = _processGAPIpagesResult(feed, 'chromeosdevices', None, totalItems, pageMessage, None, Ent.CROS_DEVICE)
          if feed:
            for cros in feed.get('chromeosdevices', []):
              crosCounts[orgUnitPath].setdefault(cros['status'], 0)
              crosCounts[orgUnitPath][cros['status']] += 1
            del feed
          if not pageToken:
            _finalizeGAPIpagesResult(pageMessage)
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
          entityActionFailedWarning([Ent.ORGANIZATIONAL_UNIT, orgUnitPath, Ent.CROS_DEVICE, None], message)
          break
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.badRequest, GAPI.backendError,
                GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
          checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath)
          break
    row = {}
    for field in fieldsList:
      if convertCRNL and field in ORG_FIELDS_WITH_CRS_NLS:
        row[field] = escapeCRsNLs(orgUnit.get(field, ''))
      else:
        row[field] = orgUnit.get(field, '')
    if childSelector:
      row[ORG_UNIT_SELECTOR_FIELD] = orgUnit[ORG_UNIT_SELECTOR_FIELD]
    if showCrOSCounts or showUserCounts:
      if showCrOSCounts:
        total = 0
        for k, v in sorted(crosCounts[orgUnitPath].items()):
          row[f'CrOS{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = v
          total += v
        row[f'CrOS{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}Total'] = total
        if ((minCrOSCounts != -1 and total < minCrOSCounts) or
            (maxCrOSCounts != -1 and total > maxCrOSCounts)):
          continue
      if showUserCounts:
        row[f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}NotArchived'] = userCounts[orgUnitPath]['archived'][0]
        row[f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}Archived'] = userCounts[orgUnitPath]['archived'][1]
        row[f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}NotSuspended'] = userCounts[orgUnitPath]['suspended'][0]
        row[f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}Suspended'] = userCounts[orgUnitPath]['suspended'][1]
        row[f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}Total'] = total = userCounts[orgUnitPath]['total']
        if ((minUserCounts != -1 and total < minUserCounts) or
            (maxUserCounts != -1 and total > maxUserCounts)):
          continue
      csvPF.WriteRowTitles(row)
    else:
      csvPF.WriteRow(row)
  if showCrOSCounts or showUserCounts:
    crosTitles = []
    userTitles = []
    allTitles = csvPF.titlesList[:]
    for title in allTitles:
      if showCrOSCounts and title.startswith(f'CrOS{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}'):
        crosTitles.append(title)
        csvPF.RemoveTitles(title)
      if showUserCounts and title.startswith(f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}'):
        userTitles.append(title)
        csvPF.RemoveTitles(title)
    if showCrOSCounts:
      csvPF.AddTitles(sorted(crosTitles))
    if showUserCounts:
      for title in ['NotArchived', 'Archived', 'NotSuspended', 'Suspended', 'Total']:
        csvPF.AddTitles(f'Users{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{title}')
    csvPF.SetSortTitles([])
  csvPF.writeCSVfile('Orgs')

# gam show orgtree [fromparent <OrgUnitItem>] [batchsuborgs [Boolean>]]
def doShowOrgTree():
  def addOrgUnitToTree(orgPathList, i, n, tree):
    if orgPathList[i] not in tree:
      tree[orgPathList[i]] = {}
    if i < n:
      addOrgUnitToTree(orgPathList, i+1, n, tree[orgPathList[i]])

  def printOrgUnit(parentOrgUnit, tree):
    printKeyValueList([parentOrgUnit])
    Ind.Increment()
    for childOrgUnit in sorted(tree[parentOrgUnit]):
      printOrgUnit(childOrgUnit, tree[parentOrgUnit])
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  orgUnitPath = '/'
  fieldsList = ['orgUnitPath']
  listType = 'all'
  batchSubOrgs = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'fromparent':
      orgUnitPath = getOrgUnitItem()
    elif myarg == 'batchsuborgs':
      batchSubOrgs = getBoolean()
    else:
      unknownArgumentExit()
  orgUnits = _getOrgUnits(cd, orgUnitPath, fieldsList, listType, False, batchSubOrgs)
  if orgUnits is None:
    return
  orgTree = {}
  for orgUnit in orgUnits:
    orgPath = orgUnit['orgUnitPath'].split('/')
    addOrgUnitToTree(orgPath, 1, len(orgPath)-1, orgTree)
  for org in sorted(orgTree):
    printOrgUnit(org, orgTree)

ORG_ITEMS_FIELD_MAP = {
  'browsers': 'browsers',
  'devices': 'devices',
  'shareddrives': 'sharedDrives',
  'subous': 'subOus',
  'users': 'users',
  }

# gam check ou|org <OrgUnitItem> [todrive <ToDriveAttribute>*]
#	[<OrgUnitCheckName>*|(fields <OrgUnitCheckNameList>)]
#	[filename <FileName>] [movetoou <OrgUnitItem>]
#	[formatjson [quotechar <Character>]]
def doCheckOrgUnit():
  def writeCommandInfo(field):
    nonlocal commitBatch
    if commitBatch:
      f.write(f'{Cmd.COMMIT_BATCH_CMD}\n')
    else:
      commitBatch = True
    f.write(f'{Cmd.PRINT_CMD} Move {field} from {orgUnitPath} to {moveToOrgUnitPath}\n')

  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['orgUnitPath', 'orgUnitId', 'empty'])
  FJQC = FormatJSONQuoteChar(csvPF)
  f = orgUnitPath = None
  fieldsList = []
  titlesList = []
  status, orgUnitPath, orgUnitId = checkOrgUnitPathExists(cd, getOrgUnitItem())
  if not status:
    entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, orgUnitPath)
  orgUnitPathLower = orgUnitPath.lower()
  fileName = 'CleanOuBatch.txt'
  moveToOrgUnitPath = moveToOrgUnitPathLower = None
  commitBatch = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in ORG_ITEMS_FIELD_MAP:
      fieldsList.append(myarg)
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in ORG_ITEMS_FIELD_MAP:
          fieldsList.append(field)
        else:
          invalidChoiceExit(field, list(ORG_ITEMS_FIELD_MAP), True)
    elif myarg == 'filename':
      fileName = setFilePath(getString(Cmd.OB_FILE_NAME), GC.DRIVE_DIR)
    elif myarg == 'movetoou':
      movetoouLocation = Cmd.Location()
      status, moveToOrgUnitPath, _ = checkOrgUnitPathExists(cd, getOrgUnitItem())
      moveToOrgUnitPathLower = moveToOrgUnitPath.lower()
      if not status:
        entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, moveToOrgUnitPath)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not fieldsList:
    fieldsList = ORG_ITEMS_FIELD_MAP.keys()
  if moveToOrgUnitPath is not None:
    Cmd.SetLocation(movetoouLocation)
    if orgUnitPathLower == moveToOrgUnitPathLower:
      usageErrorExit(Msg.OU_AND_MOVETOOU_CANNOT_BE_IDENTICAL.format(orgUnitPath, moveToOrgUnitPath))
    if 'subous' in fieldsList and moveToOrgUnitPathLower.startswith(orgUnitPathLower):
      usageErrorExit(Msg.OU_SUBOUS_CANNOT_BE_MOVED_TO_MOVETOOU.format(orgUnitPath, moveToOrgUnitPath))
    fileName = setFilePath(fileName, GC.DRIVE_DIR)
    f = openFile(fileName, DEFAULT_FILE_WRITE_MODE)
  orgUnitItemCounts = {}
  for field in sorted(fieldsList):
    title = ORG_ITEMS_FIELD_MAP[field]
    orgUnitItemCounts[title] = 0
    if not FJQC.formatJSON:
      titlesList.append(title)
  if 'browsers' in fieldsList:
    cbcm = buildGAPIObject(API.CBCM)
    customerId = _getCustomerIdNoC()
    printGettingAllEntityItemsForWhom(Ent.CHROME_BROWSER, orgUnitPath, entityType=Ent.ORGANIZATIONAL_UNIT)
    pageMessage = getPageMessage()
    try:
      feed = yieldGAPIpages(cbcm.chromebrowsers(), 'list', 'browsers',
                            pageMessage=pageMessage, messageAttribute='deviceId',
                            throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            customer=customerId, orgUnitPath=orgUnitPath, projection='BASIC',
                            fields='nextPageToken,browsers(deviceId)')
      for browsers in feed:
        orgUnitItemCounts['browsers'] += len(browsers)
      if f is not None and orgUnitItemCounts['browsers'] > 0:
        writeCommandInfo('browsers')
        f.write(f'gam move browsers ou {moveToOrgUnitPath} browserou {orgUnitPath}\n')
    except (GAPI.invalidInput, GAPI.forbidden) as e:
      entityActionFailedWarning([Ent.CHROME_BROWSER, None], str(e))
    except GAPI.invalidOrgunit  as e:
      entityActionFailedExit([Ent.CHROME_BROWSER, None], str(e))
    except (GAPI.badRequest, GAPI.resourceNotFound):
      accessErrorExit(None)
  if 'devices' in fieldsList:
    printGettingAllEntityItemsForWhom(Ent.CROS_DEVICE, orgUnitPath, entityType=Ent.ORGANIZATIONAL_UNIT)
    pageMessage = getPageMessageForWhom()
    pageToken = None
    totalItems = 0
    tokenRetries = 0
    while True:
      try:
        feed = callGAPI(cd.chromeosdevices(), 'list',
                        throwReasons=[GAPI.INVALID_INPUT, GAPI.INVALID_ORGUNIT,
                                      GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        pageToken=pageToken, customerId=GC.Values[GC.CUSTOMER_ID],
                        orgUnitPath=orgUnitPath, fields='nextPageToken,chromeosdevices(deviceId)', maxResults=GC.Values[GC.DEVICE_MAX_RESULTS])
        tokenRetries = 0
        pageToken, totalItems = _processGAPIpagesResult(feed, 'chromeosdevices', None, totalItems, pageMessage, None, Ent.CROS_DEVICE)
        if feed:
          orgUnitItemCounts['devices'] += len(feed.get('chromeosdevices', []))
          del feed
        if not pageToken:
          _finalizeGAPIpagesResult(pageMessage)
          printGotAccountEntities(totalItems)
          if f is not None and orgUnitItemCounts['devices'] > 0:
            writeCommandInfo('devices')
            f.write(f'gam update  ou {moveToOrgUnitPath} add cros_ou {orgUnitPath}\n')
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
          break
        entityActionFailedWarning([Ent.CROS_DEVICE, None], message)
        break
      except GAPI.invalidOrgunit as e:
        entityActionFailedExit([Ent.CROS_DEVICE, None], str(e))
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        accessErrorExit(cd)
  if 'shareddrives' in fieldsList:
    ci = buildGAPIObject(API.CLOUDIDENTITY_ORGUNITS_BETA)
    printGettingAllEntityItemsForWhom(Ent.SHAREDDRIVE, orgUnitPath, entityType=Ent.ORGANIZATIONAL_UNIT)
    sds = callGAPIpages(ci.orgUnits().memberships(), 'list', 'orgMemberships',
                        pageMessage=getPageMessageForWhom(),
                        parent=f'orgUnits/{orgUnitId[3:]}',
                        customer=_getCustomersCustomerIdWithC(),
                        filter="type == 'shared_drive'")
    orgUnitItemCounts['sharedDrives'] = len(sds)
    if f is not None and orgUnitItemCounts['sharedDrives'] > 0:
      writeCommandInfo('Shared Drives')
      for sd in sds:
        name = sd['name'].split(';')[1]
        f.write(f'gam update shareddrive {name} ou {moveToOrgUnitPath}\n')
  if 'subous' in fieldsList:
    subOus = _getOrgUnits(cd, orgUnitPath, ['orgUnitPath'], 'children', False, False, None, None)
    orgUnitItemCounts['subOus'] = len(subOus)
    if f is not None and orgUnitItemCounts['subOus'] > 0:
      writeCommandInfo('Sub OrgUnit')
      for ou in subOus:
        f.write(f'gam update ou {ou["orgUnitPath"]} parent {moveToOrgUnitPath}\n')
  if 'users' in fieldsList:
    printGettingAllEntityItemsForWhom(Ent.USER, orgUnitPath, entityType=Ent.ORGANIZATIONAL_UNIT)
    pageMessage = getPageMessageForWhom()
    try:
      feed = yieldGAPIpages(cd.users(), 'list', 'users',
                            pageMessage=pageMessage,
                            throwReasons=[GAPI.INVALID_ORGUNIT, GAPI.ORGUNIT_NOT_FOUND,
                                          GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            customer=GC.Values[GC.CUSTOMER_ID], query=orgUnitPathQuery(orgUnitPath, None, None),
                            fields='nextPageToken,users(orgUnitPath)', maxResults=GC.Values[GC.USER_MAX_RESULTS])
      for users in feed:
        for user in users:
          if orgUnitPathLower == user.get('orgUnitPath', '').lower():
            orgUnitItemCounts['users'] += 1
      if f is not None and orgUnitItemCounts['users'] > 0:
        writeCommandInfo('users')
        f.write(f'gam update ou {moveToOrgUnitPath} add ou {orgUnitPath}\n')
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.invalidInput, GAPI.badRequest, GAPI.backendError,
            GAPI.invalidCustomerId, GAPI.loginRequired, GAPI.resourceNotFound, GAPI.forbidden):
      checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, orgUnitPath)
  if f is not None:
    closeFile(f)
    writeStderr(Msg.GAM_BATCH_FILE_WRITTEN.format(fileName))
  empty = True
  for count in orgUnitItemCounts.values():
    if count > 0:
      empty = False
      break
  baseRow = {'orgUnitPath': orgUnitPath, 'orgUnitId': orgUnitId, 'empty': empty}
  row = flattenJSON(orgUnitItemCounts, baseRow.copy())
  if not FJQC.formatJSON:
    csvPF.WriteRowTitles(row)
  elif csvPF.CheckRowTitles(row):
    baseRow['JSON'] = json.dumps(cleanJSON(orgUnitItemCounts), ensure_ascii=False, sort_keys=True)
    csvPF.WriteRowNoFilter(baseRow)
  csvPF.writeCSVfile(f'OrgUnit {orgUnitPath} Item Counts')
  if not empty and GM.Globals[GM.SYSEXITRC] == 0:
    setSysExitRC(ORGUNIT_NOT_EMPTY_RC)

ALIAS_TARGET_TYPES = ['user', 'group', 'target']

# gam create aliases|nicknames <EmailAddressEntity> user|group|target <UniqueID>|<EmailAddress>
#	[verifynotinvitable]
# gam update aliases|nicknames <EmailAddressEntity> user|group|target <UniqueID>|<EmailAddress>
#	[notargetverify] [waitafterdelete <Integer>]
