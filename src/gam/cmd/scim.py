"""GAM SCIM user, group, schema, resource type, and config management.

Implements commands for the Cloud Identity Inbound SCIM API.

User commands:   create|update|delete|info scimuser, print|show scimusers
Group commands:  create|update|delete|info scimgroup, print|show scimgroups
Schema commands: info scimschema, print|show scimschemas
ResourceType:    info scimresourcetype, print|show scimresourcetypes
Config:          show scimconfig
"""

import json

from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api_call import callGAPI
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
    getBoolean,
    getChoice,
    getEmailAddress,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityDoesNotExistWarning,
    entityDuplicateWarning,
    printEntity,
    printKeyValueList,
    printLine,
)
from gam.util.errors import missingArgumentExit, unknownArgumentExit, usageErrorExit
from gam.util.scim import (
    SCHEMA_CI_GROUP,
    SCHEMA_ENTERPRISE_USER,
    MAX_GROUP_PATCH_OPS,
    MAX_USER_PATCH_OPS,
    VALID_ADDRESS_TYPES,
    VALID_EMAIL_TYPES,
    VALID_PHONE_TYPES,
    addOp,
    batchOps,
    buildPatchBody,
    buildSCIMObject,
    customerId,
    flattenSCIMResource,
    newGroupBody,
    newUserBody,
    removeOp,
    replaceOp,
    resolveGroupId,
    resolveUserId,
    scimGroups,
    scimResourceTypes,
    scimSchemas,
    scimServiceProviderConfig,
    scimUsers,
)


# ---------------------------------------------------------------------------
# Attribute parsing helpers
# ---------------------------------------------------------------------------

def _parsePhoneEntry():
  """Parse: type <home|work|mobile|fax|pager|other> value <String> [primary]"""
  entry = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'type':
      entry['type'] = getChoice(VALID_PHONE_TYPES)
    elif myarg == 'value':
      entry['value'] = getString(Cmd.OB_STRING)
    elif myarg == 'primary':
      entry['primary'] = True
    elif myarg == 'notprimary':
      entry['primary'] = False
    else:
      Cmd.Backup()
      break
  if 'value' not in entry:
    missingArgumentExit('value')
  return entry


def _parseEmailEntry():
  """Parse: type <home|work|other> value <String>"""
  entry = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'type':
      entry['type'] = getChoice(VALID_EMAIL_TYPES)
    elif myarg == 'value':
      entry['value'] = getString(Cmd.OB_STRING)
    else:
      Cmd.Backup()
      break
  if 'value' not in entry:
    missingArgumentExit('value')
  return entry


def _parseAddressEntry():
  """Parse: type <home|work|other> [streetaddress <S>] [locality <S>]
            [region <S>] [postalcode <S>] [country <S>]
            [formatted <S>] [primary]"""
  entry = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'type':
      entry['type'] = getChoice(VALID_ADDRESS_TYPES)
    elif myarg == 'streetaddress':
      entry['streetAddress'] = getString(Cmd.OB_STRING)
    elif myarg == 'locality':
      entry['locality'] = getString(Cmd.OB_STRING)
    elif myarg == 'region':
      entry['region'] = getString(Cmd.OB_STRING)
    elif myarg in ('postalcode', 'zipcode'):
      entry['postalCode'] = getString(Cmd.OB_STRING)
    elif myarg == 'country':
      entry['country'] = getString(Cmd.OB_STRING)
    elif myarg == 'formatted':
      entry['formatted'] = getString(Cmd.OB_STRING)
    elif myarg == 'primary':
      entry['primary'] = True
    elif myarg == 'notprimary':
      entry['primary'] = False
    else:
      Cmd.Backup()
      break
  return entry


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

USER_PRINT_ORDER = [
    'userName', 'id', 'active', 'displayName', 'externalId',
    'name', 'emails', 'phoneNumbers', 'addresses',
]

GROUP_PRINT_ORDER = [
    'displayName', 'id', 'externalId', 'members',
]


def _showSCIMResource(result, entityType, entityName, print_order,
                      FJQC, i=0, count=0):
  """Generic display for a single SCIM resource in show/info mode."""
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=True))
    return
  printEntity([entityType, entityName], i, count)
  Ind.Increment()
  skipObjects = set()
  for field in print_order:
    if field in result:
      value = result[field]
      if isinstance(value, (dict, list)):
        printKeyValueList([field, ''])
        Ind.Increment()
        showJSON(None, value)
        Ind.Decrement()
      else:
        printKeyValueList([field, value])
      skipObjects.add(field)
  showJSON(None, result, skipObjects)
  Ind.Decrement()


def _showSCIMUser(result, FJQC, i=0, count=0):
  _showSCIMResource(result, Ent.SCIM_USER,
                    result.get('userName', result.get('id', 'Unknown')),
                    USER_PRINT_ORDER, FJQC, i, count)


def _showSCIMGroup(result, FJQC, i=0, count=0):
  _showSCIMResource(result, Ent.SCIM_GROUP,
                    result.get('displayName', result.get('id', 'Unknown')),
                    GROUP_PRINT_ORDER, FJQC, i, count)


def _printSCIMResourceCSV(resource, csvPF):
  """Flatten a SCIM resource and write it as a CSV row."""
  row = flattenSCIMResource(resource)
  for key in row:
    csvPF.AddTitles(key)
  csvPF.WriteRow(row)


# ---------------------------------------------------------------------------
# User commands
# ---------------------------------------------------------------------------

# gam create scimuser <email> [firstname <String>] [lastname <String>]
#   [active <Boolean>] [displayname <String>] [externalid <String>]
#   [employeenumber|department|costcenter|organization <String>]
#   [email type <home|work|other> value <String>]
#   [phone type <home|work|mobile|fax|pager|other> value <String> [primary]]
#   [address type <home|work|other> [streetaddress <S>] [locality <S>]
#            [region <S>] [postalcode <S>] [country <S>] [formatted <S>] [primary]]
def doCreateSCIMUser():
  scim = buildSCIMObject()
  email = getEmailAddress()
  name = {}
  enterprise = {}
  emails_list = []
  phones = []
  addresses = []
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'firstname':
      name['givenName'] = getString(Cmd.OB_STRING)
    elif myarg == 'lastname':
      name['familyName'] = getString(Cmd.OB_STRING)
    elif myarg == 'active':
      kwargs['active'] = getBoolean()
    elif myarg == 'externalid':
      kwargs['externalId'] = getString(Cmd.OB_STRING)
    elif myarg == 'displayname':
      kwargs['displayName'] = getString(Cmd.OB_STRING)
    elif myarg == 'employeenumber':
      enterprise['employeeNumber'] = getString(Cmd.OB_STRING)
    elif myarg == 'department':
      enterprise['department'] = getString(Cmd.OB_STRING)
    elif myarg == 'costcenter':
      enterprise['costCenter'] = getString(Cmd.OB_STRING)
    elif myarg == 'organization':
      enterprise['organization'] = getString(Cmd.OB_STRING)
    elif myarg == 'email':
      emails_list.append(_parseEmailEntry())
    elif myarg == 'phone':
      phones.append(_parsePhoneEntry())
    elif myarg == 'address':
      addresses.append(_parseAddressEntry())
    elif myarg == 'password':
      usageErrorExit(Msg.SCIM_USER_PASSWORDLESS)
    else:
      unknownArgumentExit()
  body = newUserBody(email, name=name or None,
                     enterprise=enterprise or None, **kwargs)
  if emails_list:
    body['emails'] = emails_list
  if phones:
    body['phoneNumbers'] = phones
  if addresses:
    body['addresses'] = addresses
  try:
    callGAPI(scimUsers(scim), 'create',
             throwReasons=[GAPI.DUPLICATE, GAPI.ALREADY_EXISTS,
                           GAPI.INVALID, GAPI.BAD_REQUEST,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerId=customerId(), body=body)
    entityActionPerformed([Ent.SCIM_USER, email])
  except (GAPI.duplicate, GAPI.alreadyExists):
    entityDuplicateWarning([Ent.SCIM_USER, email])
  except (GAPI.invalid, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.SCIM_USER, email], str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_USER, email], str(e))


# gam update scimuser <email> [firstname|lastname|displayname|externalid <String>]
#   [active <Boolean>]
#   [employeenumber|department|costcenter|organization <String>]
#   [addemail type <home|work|other> value <String>]
#   [clearemail]
#   [addphone type <home|work|mobile|fax|pager|other> value <String> [primary]]
#   [clearphone]
#   [addaddress type <home|work|other> ...]
#   [clearaddress]
#   [clearexternalid]
def doUpdateSCIMUser():
  scim = buildSCIMObject()
  email = getEmailAddress()
  userId = resolveUserId(scim, email)
  if not userId:
    entityDoesNotExistWarning(Ent.SCIM_USER, email)
    return
  operations = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'firstname':
      operations.append(replaceOp('name.givenName', getString(Cmd.OB_STRING)))
    elif myarg == 'lastname':
      operations.append(replaceOp('name.familyName', getString(Cmd.OB_STRING)))
    elif myarg == 'displayname':
      operations.append(replaceOp('displayName', getString(Cmd.OB_STRING)))
    elif myarg == 'active':
      operations.append(replaceOp('active', getBoolean()))
    elif myarg == 'externalid':
      operations.append(replaceOp('externalId', getString(Cmd.OB_STRING)))
    elif myarg == 'clearexternalid':
      operations.append(removeOp('externalId'))
    elif myarg == 'employeenumber':
      operations.append(replaceOp(
          f'{SCHEMA_ENTERPRISE_USER}.employeeNumber', getString(Cmd.OB_STRING)))
    elif myarg == 'department':
      operations.append(replaceOp(
          f'{SCHEMA_ENTERPRISE_USER}.department', getString(Cmd.OB_STRING)))
    elif myarg == 'costcenter':
      operations.append(replaceOp(
          f'{SCHEMA_ENTERPRISE_USER}.costCenter', getString(Cmd.OB_STRING)))
    elif myarg == 'organization':
      operations.append(replaceOp(
          f'{SCHEMA_ENTERPRISE_USER}.organization', getString(Cmd.OB_STRING)))
    elif myarg == 'addemail':
      operations.append(addOp('emails', [_parseEmailEntry()]))
    elif myarg == 'clearemail':
      operations.append(removeOp('emails'))
    elif myarg == 'addphone':
      operations.append(addOp('phoneNumbers', [_parsePhoneEntry()]))
    elif myarg == 'clearphone':
      operations.append(removeOp('phoneNumbers'))
    elif myarg == 'addaddress':
      operations.append(addOp('addresses', [_parseAddressEntry()]))
    elif myarg == 'clearaddress':
      operations.append(removeOp('addresses'))
    elif myarg == 'password':
      usageErrorExit(Msg.SCIM_USER_PASSWORDLESS)
    else:
      unknownArgumentExit()
  if not operations:
    return
  try:
    for batch in batchOps(operations, MAX_USER_PATCH_OPS):
      callGAPI(scimUsers(scim), 'patch',
               throwReasons=[GAPI.NOT_FOUND,
                             GAPI.INVALID, GAPI.BAD_REQUEST,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               customerId=customerId(), userId=userId,
               body=buildPatchBody(batch))
    entityActionPerformed([Ent.SCIM_USER, email])
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_USER, email)
  except (GAPI.invalid, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.SCIM_USER, email], str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_USER, email], str(e))


# gam delete scimuser <email>
def doDeleteSCIMUser():
  scim = buildSCIMObject()
  email = getEmailAddress()
  checkForExtraneousArguments()
  userId = resolveUserId(scim, email)
  if not userId:
    entityDoesNotExistWarning(Ent.SCIM_USER, email)
    return
  try:
    callGAPI(scimUsers(scim), 'delete',
             throwReasons=[GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerId=customerId(), userId=userId)
    entityActionPerformed([Ent.SCIM_USER, email])
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_USER, email)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_USER, email], str(e))


# gam info scimuser <email> [attributes <comma-separated>] [formatjson]
def doInfoSCIMUser():
  scim = buildSCIMObject()
  email = getEmailAddress()
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  attributes = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'attributes':
      attributes = getString(Cmd.OB_STRING)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  userId = resolveUserId(scim, email)
  if not userId:
    entityDoesNotExistWarning(Ent.SCIM_USER, email)
    return
  kwargs = {}
  if attributes:
    kwargs['attributes'] = attributes
  try:
    result = callGAPI(scimUsers(scim), 'get',
                      throwReasons=[GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId(), userId=userId, **kwargs)
    _showSCIMUser(result, FJQC)
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_USER, email)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_USER, email], str(e))


# gam print|show scimusers filter <SCIMFilter>
#   [attributes <comma-separated>] [todrive ...] [formatjson [quotechar <Char>]]
def doPrintShowSCIMUsers():
  scim = buildSCIMObject()
  csvPF = CSVPrintFile(['userName', 'id', 'active']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  scim_filter = None
  attributes = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'filter':
      scim_filter = getString(Cmd.OB_STRING)
    elif myarg == 'attributes':
      attributes = getString(Cmd.OB_STRING)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not scim_filter:
    missingArgumentExit('filter')
  kwargs = {}
  if attributes:
    kwargs['attributes'] = attributes
  try:
    result = callGAPI(scimUsers(scim), 'list',
                      throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId(), filter=scim_filter, **kwargs)
  except (GAPI.invalid, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.SCIM_USER, scim_filter], str(e))
    return
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_USER, scim_filter], str(e))
    return
  resources = result.get('resources', result.get('Resources', []))
  jcount = len(resources)
  for i, user in enumerate(resources, start=1):
    if csvPF:
      if FJQC.formatJSON:
        csvPF.WriteRowNoFilter({'userName': user.get('userName', ''),
                                'id': user.get('id', ''),
                                'JSON': json.dumps(cleanJSON(user),
                                                   ensure_ascii=False,
                                                   sort_keys=True)})
      else:
        _printSCIMResourceCSV(user, csvPF)
    else:
      _showSCIMUser(user, FJQC, i, jcount)
  if csvPF:
    csvPF.writeCSVfile('SCIM Users')


# ---------------------------------------------------------------------------
# Group commands
# ---------------------------------------------------------------------------

# gam create scimgroup <email>
#   [name <String>] [externalid <String>] [description <String>]
#   [member <email> ...]
def doCreateSCIMGroup():
  scim = buildSCIMObject()
  email = getEmailAddress()
  display_name = None
  external_id = None
  description = None
  members = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      display_name = getString(Cmd.OB_STRING)
    elif myarg == 'externalid':
      external_id = getString(Cmd.OB_STRING)
    elif myarg == 'description':
      description = getString(Cmd.OB_STRING)
    elif myarg == 'member':
      members.append({'value': getEmailAddress()})
    else:
      unknownArgumentExit()
  if not display_name:
    display_name = email.split('@')[0]
  body = newGroupBody(display_name, email,
                      external_id=external_id, description=description,
                      members=members or None)
  try:
    callGAPI(scimGroups(scim), 'create',
             throwReasons=[GAPI.DUPLICATE, GAPI.ALREADY_EXISTS,
                           GAPI.INVALID, GAPI.BAD_REQUEST,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerId=customerId(), body=body)
    entityActionPerformed([Ent.SCIM_GROUP, email])
  except (GAPI.duplicate, GAPI.alreadyExists):
    entityDuplicateWarning([Ent.SCIM_GROUP, email])
  except (GAPI.invalid, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, email], str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, email], str(e))


# gam update scimgroup <id:|uid:|displayName>
#   [name <String>] [email <email>]
#   [externalid <String>] [clearexternalid]
#   [description <String>]
#   [add member <email>] [remove member <email>]
def doUpdateSCIMGroup():
  scim = buildSCIMObject()
  group_key = getString(Cmd.OB_STRING)
  groupId = resolveGroupId(scim, group_key)
  if not groupId:
    entityDoesNotExistWarning(Ent.SCIM_GROUP, group_key)
    return
  operations = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      operations.append(replaceOp('displayName', getString(Cmd.OB_STRING)))
    elif myarg == 'email':
      operations.append(replaceOp(
          f'{SCHEMA_CI_GROUP}.email', getEmailAddress()))
    elif myarg == 'externalid':
      operations.append(replaceOp('externalId', getString(Cmd.OB_STRING)))
    elif myarg == 'clearexternalid':
      operations.append(removeOp('externalId'))
    elif myarg == 'description':
      operations.append(replaceOp(
          f'{SCHEMA_CI_GROUP}.description', getString(Cmd.OB_STRING)))
    elif myarg == 'add':
      getChoice(['member'])
      member = getEmailAddress()
      operations.append(addOp('members', [{'value': member}]))
    elif myarg == 'remove':
      getChoice(['member'])
      member = getEmailAddress()
      memberId = resolveUserId(scim, member)
      if not memberId:
        entityDoesNotExistWarning(Ent.SCIM_USER, member)
        return
      operations.append(removeOp(f'members[value eq "{memberId}"]'))
    else:
      unknownArgumentExit()
  if not operations:
    return
  try:
    # Groups: max 2 ops per PATCH — auto-batch
    for batch in batchOps(operations, MAX_GROUP_PATCH_OPS):
      callGAPI(scimGroups(scim), 'patch',
               throwReasons=[GAPI.NOT_FOUND,
                             GAPI.INVALID, GAPI.BAD_REQUEST,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               customerId=customerId(), groupId=groupId,
               body=buildPatchBody(batch))
    entityActionPerformed([Ent.SCIM_GROUP, group_key])
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_GROUP, group_key)
  except (GAPI.invalid, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, group_key], str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, group_key], str(e))


# gam delete scimgroup <id:|uid:|displayName>
def doDeleteSCIMGroup():
  scim = buildSCIMObject()
  group_key = getString(Cmd.OB_STRING)
  checkForExtraneousArguments()
  groupId = resolveGroupId(scim, group_key)
  if not groupId:
    entityDoesNotExistWarning(Ent.SCIM_GROUP, group_key)
    return
  try:
    callGAPI(scimGroups(scim), 'delete',
             throwReasons=[GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerId=customerId(), groupId=groupId)
    entityActionPerformed([Ent.SCIM_GROUP, group_key])
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_GROUP, group_key)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, group_key], str(e))


# gam info scimgroup <id:|uid:|displayName> [formatjson]
def doInfoSCIMGroup():
  scim = buildSCIMObject()
  group_key = getString(Cmd.OB_STRING)
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSONQuoteChar(myarg, True)
  groupId = resolveGroupId(scim, group_key)
  if not groupId:
    entityDoesNotExistWarning(Ent.SCIM_GROUP, group_key)
    return
  try:
    result = callGAPI(scimGroups(scim), 'get',
                      throwReasons=[GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId(), groupId=groupId)
    _showSCIMGroup(result, FJQC)
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_GROUP, group_key)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, group_key], str(e))


# gam print|show scimgroups filter <SCIMFilter>
#   [todrive ...] [formatjson [quotechar <Char>]]
def doPrintShowSCIMGroups():
  scim = buildSCIMObject()
  csvPF = CSVPrintFile(['displayName', 'id', 'externalId']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  scim_filter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'filter':
      scim_filter = getString(Cmd.OB_STRING)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not scim_filter:
    missingArgumentExit('filter')
  try:
    result = callGAPI(scimGroups(scim), 'list',
                      throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId(), filter=scim_filter)
  except (GAPI.invalid, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, scim_filter], str(e))
    return
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_GROUP, scim_filter], str(e))
    return
  resources = result.get('resources', result.get('Resources', []))
  jcount = len(resources)
  for i, group in enumerate(resources, start=1):
    if csvPF:
      if FJQC.formatJSON:
        csvPF.WriteRowNoFilter({'displayName': group.get('displayName', ''),
                                'id': group.get('id', ''),
                                'JSON': json.dumps(cleanJSON(group),
                                                   ensure_ascii=False,
                                                   sort_keys=True)})
      else:
        _printSCIMResourceCSV(group, csvPF)
    else:
      _showSCIMGroup(group, FJQC, i, jcount)
  if csvPF:
    csvPF.writeCSVfile('SCIM Groups')


# ---------------------------------------------------------------------------
# Schema commands
# ---------------------------------------------------------------------------


def _formatAttrFlags(attr):
  """Build a compact flags string like (string, required, unique:server, readWrite)."""
  parts = []
  atype = attr.get('type', 'string')
  if attr.get('multiValued'):
    atype += '[]'
  parts.append(atype)
  if attr.get('required'):
    parts.append('required')
  mutability = attr.get('mutability')
  if mutability and mutability != 'readWrite':
    parts.append(mutability)
  uniqueness = attr.get('uniqueness')
  if uniqueness and uniqueness != 'none':
    parts.append(f'unique:{uniqueness}')
  returned = attr.get('returned')
  if returned and returned != 'default':
    parts.append(f'returned:{returned}')
  if attr.get('caseExact'):
    parts.append('caseExact')
  return ', '.join(parts)


def _showSchemaAttributes(attributes, depth=0):
  """Recursively display schema attributes in human-readable format."""
  for attr in attributes:
    name = attr.get('name', '?')
    flags = _formatAttrFlags(attr)
    printKeyValueList([name, f'({flags})'])
    desc = attr.get('description')
    if desc:
      Ind.Increment()
      printKeyValueList([desc])
      Ind.Decrement()
    sub_attrs = attr.get('subAttributes', [])
    if sub_attrs:
      Ind.Increment()
      _showSchemaAttributes(sub_attrs, depth + 1)
      Ind.Decrement()


def _showSCIMSchema(schema, FJQC, i=0, count=0):
  """Display a SCIM schema in human-readable format."""
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(schema), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.SCIM_SCHEMA, schema.get('id', '')], i, count)
  Ind.Increment()
  printKeyValueList(['Name', schema.get('name', '')])
  desc = schema.get('description')
  if desc:
    printKeyValueList(['Description', desc])
  attributes = schema.get('attributes', [])
  if attributes:
    printKeyValueList([f'Attributes ({len(attributes)})', ''])
    Ind.Increment()
    _showSchemaAttributes(attributes)
    Ind.Decrement()
  Ind.Decrement()


# gam info scimschema <schemaURN> [formatjson]
def doInfoSCIMSchema():
  scim = buildSCIMObject()
  schemaId = getString(Cmd.OB_STRING)
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    result = callGAPI(scimSchemas(scim), 'get',
                      throwReasons=[GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId(), schemaId=schemaId)
    _showSCIMSchema(result, FJQC)
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_SCHEMA, schemaId)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_SCHEMA, schemaId], str(e))


# gam print|show scimschemas [formatjson [quotechar <Char>]] [todrive ...]
def doPrintShowSCIMSchemas():
  scim = buildSCIMObject()
  csvPF = CSVPrintFile(['id', 'name', 'description']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    result = callGAPI(scimSchemas(scim), 'list',
                      throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId())
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_SCHEMA, ''], str(e))
    return
  resources = result.get('resources', result.get('Resources', []))
  jcount = len(resources)
  for i, schema in enumerate(resources, start=1):
    if csvPF:
      if FJQC.formatJSON:
        csvPF.WriteRowNoFilter({'id': schema.get('id', ''),
                                'JSON': json.dumps(cleanJSON(schema),
                                                   ensure_ascii=False,
                                                   sort_keys=True)})
      else:
        _printSCIMResourceCSV(schema, csvPF)
    else:
      _showSCIMSchema(schema, FJQC, i, jcount)
  if csvPF:
    csvPF.writeCSVfile('SCIM Schemas')


# ---------------------------------------------------------------------------
# ResourceType commands
# ---------------------------------------------------------------------------

RESOURCE_TYPE_PRINT_ORDER = ['id', 'name', 'description', 'endpoint',
                             'schema', 'schemaExtensions']


# gam info scimresourcetype <resourceTypeId> [formatjson]
def doInfoSCIMResourceType():
  scim = buildSCIMObject()
  resourceTypeId = getString(Cmd.OB_STRING)
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    result = callGAPI(scimResourceTypes(scim), 'get',
                      throwReasons=[GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId(), resourceTypeId=resourceTypeId)
    _showSCIMResource(result, Ent.SCIM_RESOURCE_TYPE,
                      result.get('id', resourceTypeId),
                      RESOURCE_TYPE_PRINT_ORDER, FJQC)
  except GAPI.notFound:
    entityDoesNotExistWarning(Ent.SCIM_RESOURCE_TYPE, resourceTypeId)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_RESOURCE_TYPE, resourceTypeId], str(e))


# gam print|show scimresourcetypes [formatjson [quotechar <Char>]] [todrive ...]
def doPrintShowSCIMResourceTypes():
  scim = buildSCIMObject()
  csvPF = CSVPrintFile(['id', 'name', 'description', 'endpoint']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    result = callGAPI(scimResourceTypes(scim), 'list',
                      throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId())
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_RESOURCE_TYPE, ''], str(e))
    return
  resources = result.get('resources', result.get('Resources', []))
  jcount = len(resources)
  for i, rt in enumerate(resources, start=1):
    if csvPF:
      if FJQC.formatJSON:
        csvPF.WriteRowNoFilter({'id': rt.get('id', ''),
                                'JSON': json.dumps(cleanJSON(rt),
                                                   ensure_ascii=False,
                                                   sort_keys=True)})
      else:
        _printSCIMResourceCSV(rt, csvPF)
    else:
      _showSCIMResource(rt, Ent.SCIM_RESOURCE_TYPE, rt.get('id', ''),
                        RESOURCE_TYPE_PRINT_ORDER, FJQC, i, jcount)
  if csvPF:
    csvPF.writeCSVfile('SCIM Resource Types')


# ---------------------------------------------------------------------------
# ServiceProviderConfig command
# ---------------------------------------------------------------------------

CONFIG_PRINT_ORDER = ['documentationUri', 'patch', 'bulk', 'filter',
                      'changePassword', 'sort', 'etag',
                      'authenticationSchemes']


# gam show scimconfig [formatjson]
def doShowSCIMConfig():
  scim = buildSCIMObject()
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    result = callGAPI(scimServiceProviderConfig(scim), 'get',
                      throwReasons=[GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=customerId())
    _showSCIMResource(result, Ent.SCIM_CONFIG, 'ServiceProviderConfig',
                      CONFIG_PRINT_ORDER, FJQC)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.SCIM_CONFIG, ''], str(e))
