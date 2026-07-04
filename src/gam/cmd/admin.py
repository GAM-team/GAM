"""GAM admin roles, privileges, and admin user management."""

import json


import re

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import accessErrorExit
from gam.util.api import buildGAPIObject, callGAPI, callGAPIitems, callGAPIpages
from gam.util.args import (
    UID_PATTERN,
    checkForExtraneousArguments,
    getAddCSVData,
    getArgument,
    getChoice,
    getEmailAddress,
    getJSON,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getItemFieldsFromFieldsList,
    getTodriveOnly,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    getPageMessage,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printKeyValueList,
    printLine,
)
from gam.util.entity import (
    ALL_GROUP_ROLES,
    PRINT_PRIVILEGES_FIELDS,
    convertEmailAddressToUID,
    convertOrgUnitIDtoPath,
    convertUIDtoEmailAddressWithType,
    getEntityList,
)
from gam.util.errors import entityActionFailedExit, invalidChoiceExit, missingArgumentExit, unknownArgumentExit
from gam.util.fileio import UNKNOWN
from gam.util.orgunits import getOrgUnitId


def _listPrivileges(cd):
  fields = f'items({",".join(PRINT_PRIVILEGES_FIELDS)})'
  try:
    return callGAPIitems(cd.privileges(), 'list', 'items',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                       GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                         customer=GC.Values[GC.CUSTOMER_ID], fields=fields)
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam print privileges [todrive <ToDriveAttribute>*]
# gam show privileges
def doPrintShowPrivileges():
  def _showPrivilege(privilege, i, count):
    printEntity([Ent.PRIVILEGE, privilege['privilegeName']], i, count)
    Ind.Increment()
    printKeyValueList(['serviceId', privilege['serviceId']])
    printKeyValueList(['serviceName', privilege.get('serviceName', UNKNOWN)])
    printKeyValueList(['isOuScopable', privilege['isOuScopable']])
    jcount = len(privilege.get('childPrivileges', []))
    if jcount > 0:
      printKeyValueList(['childPrivileges', jcount])
      Ind.Increment()
      j = 0
      for childPrivilege in privilege['childPrivileges']:
        j += 1
        _showPrivilege(childPrivilege, j, jcount)
      Ind.Decrement()
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(PRINT_PRIVILEGES_FIELDS, 'sortall') if Act.csvFormat() else None
  getTodriveOnly(csvPF)
  privileges = _listPrivileges(cd)
  if not csvPF:
    count = len(privileges)
    performActionNumItems(count, Ent.PRIVILEGE)
    Ind.Increment()
    i = 0
    for privilege in privileges:
      i += 1
      _showPrivilege(privilege, i, count)
    Ind.Decrement()
  else:
    for privilege in privileges:
      csvPF.WriteRowTitles(flattenJSON(privilege))
  if csvPF:
    csvPF.writeCSVfile('Privileges')

def makeRoleIdNameMap():
  GM.Globals[GM.MAKE_ROLE_ID_NAME_MAP] = False
  cd = buildGAPIObject(API.DIRECTORY)
  try:
    result = callGAPIpages(cd.roles(), 'list', 'items',
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                         GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                           customer=GC.Values[GC.CUSTOMER_ID],
                           fields='nextPageToken,items(roleId,roleName)',
                           maxResults=100)
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  for role in result:
    GM.Globals[GM.MAP_ROLE_ID_TO_NAME][role['roleId']] = role['roleName']
    GM.Globals[GM.MAP_ROLE_NAME_TO_ID][role['roleName'].lower()] = role['roleId']

def role_from_roleid(roleid):
  if GM.Globals[GM.MAKE_ROLE_ID_NAME_MAP]:
    makeRoleIdNameMap()
  return GM.Globals[GM.MAP_ROLE_ID_TO_NAME].get(roleid, roleid)

def roleid_from_role(role):
  if GM.Globals[GM.MAKE_ROLE_ID_NAME_MAP]:
    makeRoleIdNameMap()
  return GM.Globals[GM.MAP_ROLE_NAME_TO_ID].get(role.lower(), None)

def getRoleId():
  role = getString(Cmd.OB_ROLE_ITEM)
  cg = UID_PATTERN.match(role)
  if cg:
    roleId = cg.group(1)
  else:
    roleId = roleid_from_role(role)
    if not roleId:
      invalidChoiceExit(role, GM.Globals[GM.MAP_ROLE_NAME_TO_ID], True)
  return (role, roleId)

PRINT_ADMIN_ROLES_FIELDS = ['roleId', 'roleName', 'roleDescription', 'isSuperAdminRole', 'isSystemRole']

# gam create adminrole <String> [description <String>]
#	privileges all|all_ou|<PrivilegeList>|(select <FileSelector>|<CSVFileSelector>)|<JSONData>
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]] (addcsvdata <FieldName> <String>)*]
# gam update adminrole <RoleItem> [name <String>] [description <String>]
#	[privileges all|all_ou|<PrivilegeList>|(select <FileSelector>|<CSVFileSelector>)|<JSONData>]
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]] (addcsvdata <FieldName> <String>)*]
def doCreateUpdateAdminRoles():
  def expandChildPrivileges(privilege):
    for childPrivilege in privilege.get('childPrivileges', []):
      childPrivileges[childPrivilege['privilegeName']] = childPrivilege['serviceId']
      expandChildPrivileges(childPrivilege)

  cd = buildGAPIObject(API.DIRECTORY)
  updateCmd = Act.Get() == Act.UPDATE
  if not updateCmd:
    body = {'roleName': getString(Cmd.OB_STRING)}
  else:
    body = {}
    _, roleId = getRoleId()
  allPrivileges = {}
  ouPrivileges = {}
  childPrivileges = {}
  csvPF = None
  FJQC = FormatJSONQuoteChar(None)
  addCSVData = {}
  for privilege in _listPrivileges(cd):
    allPrivileges[privilege['privilegeName']] = privilege['serviceId']
    if privilege['isOuScopable']:
      ouPrivileges[privilege['privilegeName']] = privilege['serviceId']
    expandChildPrivileges(privilege)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'privileges':
      privs = getString(Cmd.OB_PRIVILEGE_LIST).upper()
      if privs == 'ALL':
        body['rolePrivileges'] = [{'privilegeName': p, 'serviceId': v} for p, v in allPrivileges.items()]
      elif privs == 'ALL_OU':
        body['rolePrivileges'] = [{'privilegeName': p, 'serviceId': v} for p, v in ouPrivileges.items()]
      elif privs == 'JSON':
        body['rolePrivileges'] = getJSON(['roleId', 'roleName', 'isAdminRole', 'isSystemRole']).get('rolePrivileges', [])
      else:
        if privs == 'SELECT':
          privsList = [p.upper() for p in getEntityList(Cmd.OB_PRIVILEGE_LIST)]
        else:
          privsList = privs.replace(',', ' ').split()
        body.setdefault('rolePrivileges', [])
        for p in privsList:
          if p in allPrivileges:
            body['rolePrivileges'].append({'privilegeName': p, 'serviceId': allPrivileges[p]})
          elif p in ouPrivileges:
            body['rolePrivileges'].append({'privilegeName': p, 'serviceId': ouPrivileges[p]})
          elif p in childPrivileges:
            body['rolePrivileges'].append({'privilegeName': p, 'serviceId': childPrivileges[p]})
          elif ':' in p:
            priv, serv = p.split(':')
            body['rolePrivileges'].append({'privilegeName': priv, 'serviceId': serv.lower()})
          elif p == 'SUPPORT':
            pass
          else:
            invalidChoiceExit(p, list(allPrivileges.keys())+list(ouPrivileges.keys())+list(childPrivileges.keys()), True)
    elif myarg == 'description':
      body['roleDescription'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'name':
      body['roleName'] = getString(Cmd.OB_STRING)
    elif myarg == 'csv':
      csvPF = CSVPrintFile(PRINT_ADMIN_ROLES_FIELDS)
      FJQC.SetCsvPF(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not updateCmd and not body.get('rolePrivileges'):
    missingArgumentExit('privileges')
  if csvPF:
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    if not FJQC.formatJSON:
      csvPF.AddTitles('rolePrivileges')
    else:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
      csvPF.MoveJSONTitlesToEnd(['JSON'])
    fieldsList = ','.join(PRINT_ADMIN_ROLES_FIELDS+['rolePrivileges'])
  else:
    fieldsList = 'roleId,roleName'
  try:
    if not updateCmd:
      result = callGAPI(cd.roles(), 'insert',
                        throwReasons=[GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                      GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED]+[GAPI.DUPLICATE, GAPI.INVALID, GAPI.REQUIRED],
                        customer=GC.Values[GC.CUSTOMER_ID], body=body, fields=fieldsList)
    else:
      result = callGAPI(cd.roles(), 'patch',
                        throwReasons=[GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                      GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED]+[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION,
                                                                               GAPI.CONFLICT, GAPI.INVALID, GAPI.REQUIRED],
                        customer=GC.Values[GC.CUSTOMER_ID], roleId=roleId, body=body, fields=fieldsList)
    if not csvPF:
      entityActionPerformed([Ent.ADMIN_ROLE, f"{result['roleName']}({result['roleId']})"])
    else:
      if not FJQC.formatJSON:
        if addCSVData:
          result.update(addCSVData)
        csvPF.WriteRowNoFilter(result)
      else:
        row = {}
        for field in PRINT_ADMIN_ROLES_FIELDS:
          if field in result:
            row[field] = result[field]
        if addCSVData:
          row.update(addCSVData)
        row['JSON'] = json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
  except (GAPI.duplicate, GAPI.invalid, GAPI.required) as e:
    entityActionFailedWarning([Ent.ADMIN_ROLE, f"{body['roleName']}"], str(e))
  except (GAPI.notFound, GAPI.failedPrecondition, GAPI.conflict) as e:
    entityActionFailedWarning([Ent.ADMIN_ROLE, roleId], str(e))
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  if csvPF:
    csvPF.writeCSVfile('Admin Roles')

# gam delete adminrole <RoleItem>
def doDeleteAdminRole():
  cd = buildGAPIObject(API.DIRECTORY)
  role, roleId = getRoleId()
  checkForExtraneousArguments()
  try:
    callGAPI(cd.roles(), 'delete',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED]+[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION],
             customer=GC.Values[GC.CUSTOMER_ID], roleId=roleId)
    entityActionPerformed([Ent.ADMIN_ROLE, f"{role}({roleId})"])
  except (GAPI.notFound, GAPI.failedPrecondition) as e:
    entityActionFailedWarning([Ent.ADMIN_ROLE, roleId], str(e))
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

def _showAdminRole(role, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(role), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.ADMIN_ROLE, role['roleName']], i, count)
  Ind.Increment()
  for field in PRINT_ADMIN_ROLES_FIELDS:
    if field != 'roleName' and field in role:
      printKeyValueList([field, role[field]])
  jcount = len(role.get('rolePrivileges', []))
  if jcount > 0:
    printKeyValueList(['rolePrivileges', jcount])
    Ind.Increment()
    j = 0
    for rolePrivilege in role['rolePrivileges']:
      j += 1
      printKeyValueList(['privilegeName', rolePrivilege['privilegeName']])
      Ind.Increment()
      printKeyValueList(['serviceId', rolePrivilege['serviceId']])
      Ind.Decrement()
    Ind.Decrement()
  Ind.Decrement()

# gam info adminrole <RoleItem> [privileges]
#	[formatjson]
# gam print adminroles|roles [todrive <ToDriveAttribute>*]
#	[role <RoleItem>] [privileges] [oneitemperrow]
#	[nosystemroles]
#	[formatjson [quotechar <Character>]]
# gam show adminroles|roles
#	[role <RoleItem>] [privileges]
#	[nosystemroles]
#	[formatjson]
def doInfoPrintShowAdminRoles():
  cd = buildGAPIObject(API.DIRECTORY)
  fieldsList = PRINT_ADMIN_ROLES_FIELDS[:]
  csvPF = CSVPrintFile(fieldsList, PRINT_ADMIN_ROLES_FIELDS) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  noSystemRoles = oneItemPerRow = False
  if Act.Get() != Act.INFO:
    roleId = None
  else:
    _, roleId = getRoleId()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif roleId is None and myarg == 'role':
      _, roleId = getRoleId()
    elif myarg == 'privileges':
      fieldsList.append('rolePrivileges')
    elif myarg == 'oneitemperrow':
      oneItemPerRow = True
    elif myarg == 'nosystemroles':
      noSystemRoles = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF:
    if 'rolePrivileges' in fieldsList:
      if not oneItemPerRow:
        if not FJQC.formatJSON:
          csvPF.AddTitles(['rolePrivileges'])
      else:
        csvPF.AddTitles(['privilegeName', 'serviceId'])
  try:
    if roleId is None:
      fields = getItemFieldsFromFieldsList('items', fieldsList)
      printGettingAllAccountEntities(Ent.ADMIN_ROLE)
      roles = callGAPIpages(cd.roles(), 'list', 'items',
                            pageMessage=getPageMessage(),
                            throwReasons=[GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            customer=GC.Values[GC.CUSTOMER_ID], fields=fields)
      if noSystemRoles:
        roles = [role for role in roles if not role.get('isSystemRole', False)]
    else:
      fields = getFieldsFromFieldsList(fieldsList)
      roles = [callGAPI(cd.roles(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION,
                                      GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                      GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        customer=GC.Values[GC.CUSTOMER_ID], roleId=roleId, fields=fields)]
  except (GAPI.notFound, GAPI.failedPrecondition) as e:
    entityActionFailedWarning([Ent.ADMIN_ROLE, roleId], str(e))
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  for role in roles:
    role.setdefault('isSuperAdminRole', False)
    role.setdefault('isSystemRole', False)
  if not csvPF:
    count = len(roles)
    if not FJQC.formatJSON:
      performActionNumItems(count, Ent.ADMIN_ROLE)
    Ind.Increment()
    i = 0
    for role in roles:
      i += 1
      _showAdminRole(role, FJQC, i, count)
    Ind.Decrement()
  else:
    for role in roles:
      if not oneItemPerRow or 'rolePrivileges' not in role:
        row = flattenJSON(role)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {}
          for field in PRINT_ADMIN_ROLES_FIELDS:
            if field in role:
              row[field] = role[field]
          row['JSON'] = json.dumps(cleanJSON(role), ensure_ascii=False, sort_keys=True)
          csvPF.WriteRowNoFilter(row)
      else:
        privileges = role.pop('rolePrivileges')
        baserow = flattenJSON(role)
        for privilege in privileges:
          row = flattenJSON(privilege, flattened=baserow.copy())
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            row = baserow.copy()
            row['JSON'] = json.dumps(cleanJSON(privilege), ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(row)
  if csvPF:
    csvPF.writeCSVfile('Admin Roles')

ADMIN_SCOPE_TYPE_CHOICE_MAP = {'customer': 'CUSTOMER', 'orgunit': 'ORG_UNIT', 'org': 'ORG_UNIT', 'ou': 'ORG_UNIT'}

SECURITY_GROUP_CONDITION = "api.getAttribute('cloudidentity.googleapis.com/groups.labels', []).hasAny(['groups.security']) && resource.type == 'cloudidentity.googleapis.com/Group'"
NONSECURITY_GROUP_CONDITION = f'!{SECURITY_GROUP_CONDITION}'
ADMIN_CONDITION_CHOICE_MAP = {
  'securitygroup': SECURITY_GROUP_CONDITION,
  'nonsecuritygroup': NONSECURITY_GROUP_CONDITION,
  }

# gam create admin <EmailAddress>|<UniqueID> <RoleItem> customer|(org_unit <OrgUnitItem>)
#	[condition securitygroup|nonsecuritygroup]
def doCreateAdmin():
  cd = buildGAPIObject(API.DIRECTORY)
  user = getEmailAddress(returnUIDprefix='uid:')
  body = {'assignedTo': convertEmailAddressToUID(user, cd, emailType='any')}
  role, roleId = getRoleId()
  body['roleId'] = roleId
  body['scopeType'] = getChoice(ADMIN_SCOPE_TYPE_CHOICE_MAP, mapChoice=True)
  if body['scopeType'] == 'ORG_UNIT':
    orgUnit, orgUnitId = getOrgUnitId(cd)
    body['orgUnitId'] = orgUnitId[3:]
    scope = f'ORG_UNIT {orgUnit}'
  else:
    scope = 'CUSTOMER'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'condition':
      body['condition'] = getChoice(ADMIN_CONDITION_CHOICE_MAP, mapChoice=True)
    else:
      unknownArgumentExit()
  try:
    result = callGAPI(cd.roleAssignments(), 'insert',
                      throwReasons=[GAPI.INTERNAL_ERROR, GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                    GAPI.CUSTOMER_EXCEEDED_ROLE_ASSIGNMENTS_LIMIT, GAPI.SERVICE_NOT_AVAILABLE,
                                    GAPI.INVALID_ORGUNIT, GAPI.DUPLICATE, GAPI.CONDITION_NOT_MET,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      customer=GC.Values[GC.CUSTOMER_ID], body=body, fields='roleAssignmentId,assigneeType')
    assigneeType = result.get('assigneeType')
    if assigneeType == 'user':
      entityType = Ent.USER
    elif assigneeType == 'group':
      entityType = Ent.GROUP
    else:
      entityType = Ent.ADMINISTRATOR
    entityActionPerformedMessage([Ent.ADMIN_ROLE_ASSIGNMENT, result['roleAssignmentId']],
                                 f'{Ent.Singular(entityType)} {user}, {Ent.Singular(Ent.ADMIN_ROLE)} {role}, {Ent.Singular(Ent.SCOPE)} {scope}')
  except GAPI.internalError:
    pass
  except (GAPI.customerExceededRoleAssignmentsLimit, GAPI.serviceNotAvailable, GAPI.conditionNotMet) as e:
    entityActionFailedWarning([Ent.ADMINISTRATOR, user, Ent.ADMIN_ROLE, role], str(e))
  except GAPI.invalidOrgunit:
    entityActionFailedWarning([Ent.ADMINISTRATOR, user], Msg.INVALID_ORGUNIT)
  except GAPI.duplicate:
    entityActionFailedWarning([Ent.ADMINISTRATOR, user, Ent.ADMIN_ROLE, role], Msg.DUPLICATE)
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam delete admin <RoleAssignmentId>
def doDeleteAdmin():
  cd = buildGAPIObject(API.DIRECTORY)
  roleAssignmentId = getString(Cmd.OB_ROLE_ASSIGNMENT_ID)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.roleAssignments(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.OPERATION_NOT_SUPPORTED,
                           GAPI.INVALID_INPUT, GAPI.SERVICE_NOT_AVAILABLE, GAPI.RESOURCE_NOT_FOUND,
                           GAPI.FAILED_PRECONDITION, GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
             customer=GC.Values[GC.CUSTOMER_ID], roleAssignmentId=roleAssignmentId)
    entityActionPerformed([Ent.ADMIN_ROLE_ASSIGNMENT, roleAssignmentId])
  except (GAPI.notFound, GAPI.operationNotSupported, GAPI.invalidInput,
          GAPI.serviceNotAvailable, GAPI.resourceNotFound, GAPI.failedPrecondition) as e:
    entityActionFailedWarning([Ent.ADMIN_ROLE_ASSIGNMENT, roleAssignmentId], str(e))
  except (GAPI.badRequest, GAPI.customerNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

ADMIN_ASSIGNEE_TYPE_TO_ASSIGNEDTO_FIELD_MAP = {
  'user': 'assignedToUser',
  'group': 'assignedToGroup',
  'serviceaccount': 'assignedToServiceAccount',
  'unknown': 'assignedToUnknown',
  }
ALL_ASSIGNEE_TYPES = ['user', 'group', 'serviceaccount']

PRINT_ADMIN_FIELDS = ['roleAssignmentId', 'roleId', 'assignedTo', 'scopeType', 'orgUnitId']
PRINT_ADMIN_TITLES = ['roleAssignmentId', 'roleId', 'role',
                      'assignedTo', 'assignedToUser', 'assignedToGroup', 'assignedToServiceAccount', 'assignedToUnknown',
                      'scopeType', 'orgUnitId', 'orgUnit']

# gam print admins [todrive <ToDriveAttribute>*]
#	[user|group <EmailAddress>|<UniqueID>] [role <RoleItem>]
#	[types <AdminAssigneeTypeList>]
#	[recursive] [condition] [privileges] [oneitemperrow]
# gam show admins
#	[user|group <EmailAddress>|<UniqueID>] [role <RoleItem>]
#	[types <AdminAssigneeTypeList>]
#	[recursive] [condition] [privileges]
def doPrintShowAdmins():
  def _getAssigneeTypes(myarg):
    if myarg in {'type', 'types'}:
      for gtype in getString(Cmd.OB_ADMIN_ASSIGNEE_TYPE_LIST).lower().replace(',', ' ').split():
        if gtype in ADMIN_ASSIGNEE_TYPE_TO_ASSIGNEDTO_FIELD_MAP:
          typesSet.add(ADMIN_ASSIGNEE_TYPE_TO_ASSIGNEDTO_FIELD_MAP[gtype])
        else:
          invalidChoiceExit(gtype, ADMIN_ASSIGNEE_TYPE_TO_ASSIGNEDTO_FIELD_MAP, True)
    else:
      return False
    return True

  def _getPrivileges(admin):
    if showPrivileges:
      roleId = admin['roleId']
      if roleId not in rolePrivileges:
        try:
          rolePrivileges[roleId] = callGAPI(cd.roles(), 'get',
                                            throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION,
                                                          GAPI.SERVICE_NOT_AVAILABLE, GAPI.BAD_REQUEST, GAPI.CUSTOMER_NOT_FOUND,
                                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                            customer=GC.Values[GC.CUSTOMER_ID],
                                            roleId=roleId,
                                            fields='rolePrivileges')
        except (GAPI.notFound, GAPI.failedPrecondition, GAPI.serviceNotAvailable) as e:
          entityActionFailedExit([Ent.USER, userKey, Ent.ADMIN_ROLE, admin['roleId']], str(e))
          rolePrivileges[roleId] = None
        except (GAPI.badRequest, GAPI.customerNotFound):
          accessErrorExit(cd)
        except (GAPI.forbidden, GAPI.permissionDenied) as e:
          ClientAPIAccessDeniedExit(str(e))
      return rolePrivileges[roleId]

  def _setNamesFromIds(admin, privileges):
    admin['role'] = role_from_roleid(admin['roleId'])
    assignedTo = admin['assignedTo']
    admin['assignedToUnknown'] = False
    if assignedTo not in assignedToIdEmailMap:
      emailTypes = ALL_ASSIGNEE_TYPES if admin.get('assigneeType', '') != 'group' else ['group']
      assigneeEmail, assigneeType = convertUIDtoEmailAddressWithType(f'uid:{assignedTo}', cd, sal, emailTypes=emailTypes)
      assignedToField = ADMIN_ASSIGNEE_TYPE_TO_ASSIGNEDTO_FIELD_MAP.get(assigneeType, 'assignedToUnknown')
      if assignedToField == 'assignedToUnknown':
        assigneeEmail = True
      assignedToIdEmailMap[assignedTo] = {'assignedToField': assignedToField, 'assigneeEmail': assigneeEmail}
    admin[assignedToIdEmailMap[assignedTo]['assignedToField']] = assignedToIdEmailMap[assignedTo]['assigneeEmail']
    admin['assignedToField'] = assignedToIdEmailMap[assignedTo]['assignedToField']
    if privileges is not None:
      admin.update(privileges)
    if 'orgUnitId' in admin:
      admin['orgUnit'] = convertOrgUnitIDtoPath(cd, f'id:{admin["orgUnitId"]}')
    if 'condition' in admin:
      if admin['condition'] == SECURITY_GROUP_CONDITION:
        admin['condition'] = 'securitygroup'
      elif admin['condition'] == NONSECURITY_GROUP_CONDITION:
        admin['condition'] = 'nonsecuritygroup'
#    if debug:
#      print('******', admin['assignedTo'], admin.get('assigneeType', 'no type'),
#            admin['assignedToField'], not typesSet or admin['assignedToField'] in typesSet)
    return not typesSet or admin['assignedToField'] in typesSet

  cd = buildGAPIObject(API.DIRECTORY)
  sal = buildGAPIObject(API.SERVICEACCOUNTLOOKUP)
  csvPF = CSVPrintFile(PRINT_ADMIN_TITLES) if Act.csvFormat() else None
  roleId = None
  userKey = None
#  debug = False
  oneItemPerRow = recursive = showPrivileges = False
  typesSet = set()
  kwargs = {}
  rolePrivileges = {}
  allGroupRoles = ','.join(sorted(ALL_GROUP_ROLES))
  fieldsList = PRINT_ADMIN_FIELDS+['assigneeType']
  assignedToIdEmailMap = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'user', 'group'}:
      userKey = kwargs['userKey'] = getEmailAddress()
