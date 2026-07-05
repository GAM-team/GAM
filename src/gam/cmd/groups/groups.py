"""Group CRUD, info, settings, and listing.

Part of the _groups_tmp sub-package."""

"""GAM group management."""

import json
import re

from gam.util.batch import RI_ENTITY, RI_OPTION, RI_ROLE, RI_I, RI_COUNT, RI_J, RI_JCOUNT, RI_ITEM

from gam.util.entity import GROUP_ROLES_MAP
import time

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.access import accessErrorExit, duplicateAliasGroupUserWarning, entityUnknownWarning
from gam.util.api import buildGAPIObject, waitOnFailure
from gam.util.api_call import _finalizeGAPIpagesResult, _processGAPIpagesResult, callGAPI, callGAPIpages, checkGAPIError
from gam.util.args import (
    ARCHIVED_ARGUMENTS,
    DELIVERY_SETTINGS_UNDEFINED,
    LANGUAGE_CODES_MAP,
    SUSPENDED_ARGUMENTS,
    _getIsArchived,
    _getIsSuspended,
    _getOptionalIsSuspendedIsArchived,
    checkArgumentPresent,
    checkForExtraneousArguments,
    escapeCRsNLs,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getDeliverySettings,
    getEmailAddress,
    getHTTPError,
    getInteger,
    getJSON,
    getLanguageCode,
    getMaxMessageBytes,
    getREPattern,
    getREPatternSubstitution,
    getString,
    getStringWithCRsNLs,
    normalizeEmailAddressOrUID,
    splitEmailAddress,
)
from gam.util.batch import batchRequestID, executeBatch
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    addFieldToFieldsList,
    cleanJSON,
    flattenJSON,
)
from gam.util.display import (
    badRequestWarning,
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityItemValueListActionNotPerformedWarning,
    entityPerformActionNumItems,
    entityPerformActionNumItemsModifier,
    getPageMessage,
    getPageMessageForWhom,
    invalidMember,
    performAction,
    printEntityKVList,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItem,
    printGettingEntityItemForWhom,
)
from gam.util.entity import (
    CIGROUP_DISCUSSION_FORUM_LABEL,
    CIGROUP_LOCKED_LABEL,
    CIGROUP_SECURITY_LABEL,
    _checkMemberStatusIsSuspendedIsArchived,
    checkGroupExists,
    convertEntityToList,
    convertGroupCloudIDToEmail,
    convertGroupEmailToCloudID,
    convertUIDtoEmailAddress,
    getEntityList,
    getEntityToModify,
    setTrueCustomerId,
)
from gam.util.errors import entityActionFailedExit, invalidChoiceExit, unknownArgumentExit
from gam.util.output import writeStderr, writeStdout
from gam.constants import GROUP_ALIAS_ATTRIBUTES, GROUP_ASSIST_CONTENT_ATTRIBUTES, GROUP_ATTRIBUTES_SET, GROUP_BASIC_ATTRIBUTES, GROUP_DEPRECATED_ATTRIBUTES, GROUP_DISCOVER_ATTRIBUTES, GROUP_MERGED_ATTRIBUTES, GROUP_MERGED_ATTRIBUTES_PRINT_ORDER, GROUP_MERGED_TO_COMPONENT_MAP, GROUP_MODERATE_CONTENT_ATTRIBUTES, GROUP_MODERATE_MEMBERS_ATTRIBUTES, GROUP_SETTINGS_ATTRIBUTES
from gam.constants import GROUP_FIELDS_WITH_CRS_NLS
from gam.cmd.ciuserinvitations import _getIsInvitableUser
from gam.util.domain_filters import groupFilters, initUserGroupDomainQueryFilters, makeUserGroupDomainQueryFilters

from gam.var import Act, Cmd, Ent, Ind

WARNING_PREFIX = 'WARNING: '

def getGroupAttrProperties(myarg):
  attrProperties = GROUP_BASIC_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_SETTINGS_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_ALIAS_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_DISCOVER_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_ASSIST_CONTENT_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_MODERATE_CONTENT_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_MODERATE_MEMBERS_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_MERGED_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_DEPRECATED_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  return None

def getGroupAttrValue(argument, gs_body):
  if argument == 'copyfrom':
    gs_body[argument] = getEmailAddress()
    return
  attrProperties = getGroupAttrProperties(argument)
  if attrProperties is None:
    unknownArgumentExit()
  attrName = attrProperties[0]
  attribute = attrProperties[1]
  attrType = attribute[GC.VAR_TYPE]
  if attrType == GC.TYPE_BOOLEAN:
    gs_body[attrName] = str(getBoolean()).lower()
  elif attrType == GC.TYPE_STRING:
    if attrName in GROUP_FIELDS_WITH_CRS_NLS:
      gs_body[attrName] = getStringWithCRsNLs()
    else:
      gs_body[attrName] = getString(Cmd.OB_STRING, minLen=0)
  elif attrType == GC.TYPE_CHOICE:
    gs_body[attrName] = getChoice(attribute['choices'], mapChoice=True)
  elif attrType in [GC.TYPE_EMAIL, GC.TYPE_EMAIL_OPTIONAL]:
    gs_body[attrName] = getEmailAddress(noUid=True, optional=attrType == GC.TYPE_EMAIL_OPTIONAL)
    if attrType == GC.TYPE_EMAIL_OPTIONAL and gs_body[attrName] is None:
      gs_body[attrName] = ''
  elif attrType == GC.TYPE_LANGUAGE:
    gs_body[attrName] = getLanguageCode(LANGUAGE_CODES_MAP)
  else: # GC.TYPE_INTEGER
    minVal, maxVal = attribute[GC.VAR_LIMITS]
    if attrName == 'maxMessageBytes':
      gs_body[attrName] = getMaxMessageBytes(minVal, maxVal)
    else:
      gs_body[attrName] = getInteger(minVal, maxVal)

def GroupIsAbuseOrPostmaster(emailAddr):
  return emailAddr.startswith('abuse@') or emailAddr.startswith('postmaster@')

def mapGroupEmailForSettings(emailAddr):
  return emailAddr.replace('/', '%2F')

def getSettingsFromGroup(cd, group, gs, gs_body):
  if gs_body:
    copySettingsFromGroup = gs_body.pop('copyfrom', None)
    if copySettingsFromGroup:
      try:
        if copySettingsFromGroup.find('@') == -1: # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
          copySettingsFromGroup = callGAPI(cd.groups(), 'get',
                                           throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                                           groupKey=copySettingsFromGroup, fields='email')['email']
        settings = callGAPI(gs.groups(), 'get',
                            throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                            groupUniqueId=mapGroupEmailForSettings(copySettingsFromGroup), fields='*')
        if settings is not None:
          for field in ['email', 'name', 'description']:
            settings.pop(field, None)
          settings.update(gs_body)
          return settings
        entityItemValueListActionNotPerformedWarning([Ent.GROUP, group], [Ent.COPYFROM_GROUP, copySettingsFromGroup], Msg.API_ERROR_SETTINGS)
        return None
      except GAPI.notFound:
        entityItemValueListActionNotPerformedWarning([Ent.GROUP, group], [Ent.COPYFROM_GROUP, copySettingsFromGroup], Msg.DOES_NOT_EXIST)
        return None
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
              GAPI.backendError, GAPI.invalid, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
              GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
        entityItemValueListActionNotPerformedWarning([Ent.GROUP, group], [Ent.COPYFROM_GROUP, copySettingsFromGroup], str(e))
        return None
  return gs_body

def checkReplyToCustom(group, settings, i=0, count=0):
  if settings.get('replyTo') != 'REPLY_TO_CUSTOM' or settings.get('customReplyTo', ''):
    return True
  entityActionNotPerformedWarning([Ent.GROUP, group], Msg.REPLY_TO_CUSTOM_REQUIRES_EMAIL_ADDRESS, i, count)
  return False

GROUP_CIGROUP_ENTITYTYPE_MAP = {False: Ent.GROUP, True: Ent.CLOUD_IDENTITY_GROUP}
GROUP_CIGROUP_FIELDS_MAP = {'name': 'displayName', 'displayname': 'displayName', 'description': 'description'}
GROUP_JSON_SKIP_FIELDS = ['email', 'adminCreated', 'directMembersCount', 'members', 'aliases', 'nonEditableAliases']
GROUP_ACCESS_TYPE_CHOICE_MAP = {
  'public': {
    'whoCanJoin': 'ALL_IN_DOMAIN_CAN_JOIN',
    'whoCanPostMessage': 'ALL_IN_DOMAIN_CAN_POST',
    'whoCanViewGroup': 'ALL_IN_DOMAIN_CAN_VIEW',
    'whoCanViewMembership': 'ALL_IN_DOMAIN_CAN_VIEW',
  },
  'team': {
    'whoCanJoin': 'CAN_REQUEST_TO_JOIN',
    'whoCanPostMessage': 'ALL_IN_DOMAIN_CAN_POST',
    'whoCanViewGroup': 'ALL_IN_DOMAIN_CAN_VIEW',
    'whoCanViewMembership': 'ALL_IN_DOMAIN_CAN_VIEW',
    },
  'announcementonly': {
    'whoCanJoin': 'ALL_IN_DOMAIN_CAN_JOIN',
    'whoCanPostMessage': 'ALL_MANAGERS_CAN_POST',
    'whoCanViewGroup': 'ALL_IN_DOMAIN_CAN_VIEW',
    'whoCanViewMembership': 'ALL_MANAGERS_CAN_VIEW',
    },
  'restricted': {
    'whoCanJoin': 'CAN_REQUEST_TO_JOIN',
    'whoCanPostMessage': 'ALL_MEMBERS_CAN_POST',
    'whoCanViewGroup': 'ALL_MEMBERS_CAN_VIEW',
    'whoCanViewMembership': 'ALL_MEMBERS_CAN_VIEW',
    }
  }

# gam create group <EmailAddress> [copyfrom <GroupItem>] <GroupAttribute>*
#	[verifynotinvitable]
#	[verifyduplicateretries <Integer>] [verifyduplicateretrydelay <Integer>]
#	[verifycreationretries <Integer>] [verifycreationinitialdelay <Integer>] [verifycreationretrydelay <Integer>]
def doCreateGroup(ciGroupsAPI=False):
  def waitingForCreationToComplete(sleep_time):
    writeStderr(Ind.Spaces()+Msg.WAITING_FOR_ITEM_CREATION_TO_COMPLETE_SLEEPING.format(Ent.Singular(Ent.GROUP), sleep_time))
    time.sleep(sleep_time)

  cd = buildGAPIObject(API.DIRECTORY)
  verifyNotInvitable = getBeforeUpdate = False
  recentDeleteRetries = 0
  recentDeleteRetryDelay = 5
  verifyCreationRetries = 0
  verifyCreationInitialDelay = 5
  verifyCreationRetryDelay = 5
  groupEmail = getEmailAddress(noUid=True)
  entityType = GROUP_CIGROUP_ENTITYTYPE_MAP[ciGroupsAPI]
  if not ciGroupsAPI:
    ci = None
    body = {'email': groupEmail}
  else:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
    initialGroupConfig = 'EMPTY'
    setTrueCustomerId(cd)
    parent = f'customers/{GC.Values[GC.CUSTOMER_ID]}'
    body = {'groupKey': {'id': groupEmail},
            'parent': parent,
            'labels': {CIGROUP_DISCUSSION_FORUM_LABEL: ''},
            }
  gs_body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'getbeforeupdate':
      getBeforeUpdate = True
    elif myarg == 'json':
      gs_body.update(getJSON(GROUP_JSON_SKIP_FIELDS))
    elif myarg == 'accesstype':
      gs_body.update(getChoice(GROUP_ACCESS_TYPE_CHOICE_MAP, mapChoice=True))
    elif ciGroupsAPI and myarg in ['alias', 'aliases']:
      body.setdefault('additionalGroupKeys', [])
      for alias in convertEntityToList(getString(Cmd.OB_CIGROUP_ALIAS_LIST), shlexSplit=True):
        body['additionalGroupKeys'].append({'id': alias})
    elif ciGroupsAPI and myarg == 'dynamic':
      body.setdefault('dynamicGroupMetadata', {'queries': []})
      body['dynamicGroupMetadata']['queries'].append({'resourceType': 'USER',
                                                      'query': getString(Cmd.OB_QUERY)})
    elif ciGroupsAPI and myarg == 'makeowner':
      initialGroupConfig = 'WITH_INITIAL_OWNER'
    elif ciGroupsAPI and myarg in {'security', 'makesecuritygroup'}:
      body['labels'][CIGROUP_SECURITY_LABEL] = ''
    elif ciGroupsAPI and myarg in ['locked']:
      body['labels'][CIGROUP_LOCKED_LABEL] = ''
    elif myarg == 'verifynotinvitable':
      verifyNotInvitable = True
    elif myarg == 'recentdeleteretries':
      recentDeleteRetries = getInteger(minVal=0, maxVal=20)
    elif myarg == 'recentdeleteretrydelay':
      recentDeleteRetryDelay = getInteger(minVal=1, maxVal=60)
    elif myarg == 'verifycreationretries':
      verifyCreationRetries = getInteger(minVal=0, maxVal=20)
    elif myarg == 'verifycreationinitialdelay':
      verifyCreationInitialDelay = getInteger(minVal=0, maxVal=60)
    elif myarg == 'verifycreationretrydelay':
      verifyCreationRetryDelay = getInteger(minVal=1, maxVal=60)
    else:
      getGroupAttrValue(myarg, gs_body)
  if verifyNotInvitable:
    isInvitableUser, _ = _getIsInvitableUser(None, groupEmail)
    if isInvitableUser:
      entityActionNotPerformedWarning([Ent.GROUP, groupEmail], Msg.EMAIL_ADDRESS_IS_UNMANAGED_ACCOUNT)
      return
  if ciGroupsAPI:
    for k, v in GROUP_CIGROUP_FIELDS_MAP.items():
      if k in gs_body:
        body[v] = gs_body.pop(k)
    body.setdefault('displayName', groupEmail)
  if gs_body:
    gs_body.setdefault('name', body.get('displayName', groupEmail))
    gs = buildGAPIObject(API.GROUPSSETTINGS)
    gs_body = getSettingsFromGroup(cd, groupEmail, gs, gs_body)
    if not gs_body or not checkReplyToCustom(groupEmail, gs_body):
      return
    if not getBeforeUpdate:
      settings = gs_body
  duplicateRetries = 0
  while True:
    try:
      if not ciGroupsAPI:
        callGAPI(cd.groups(), 'insert',
                 throwReasons=GAPI.GROUP_CREATE_THROW_REASONS,
                 body=body, fields='')
      else:
        callGAPI(ci.groups(), 'create',
                 throwReasons=GAPI.CIGROUP_CREATE_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                 initialGroupConfig=initialGroupConfig, body=body, fields='')
      if gs_body and not GroupIsAbuseOrPostmaster(groupEmail):
        groupUniqueId = mapGroupEmailForSettings(groupEmail)
        if getBeforeUpdate:
          settings = callGAPI(gs.groups(), 'get',
                              throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS,
                              retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS+[GAPI.NOT_FOUND],
                              groupUniqueId=groupUniqueId, fields='*')
          settings.update(gs_body)
        callGAPI(gs.groups(), 'update',
                 bailOnInvalidError='messageModerationLevel' in settings,
                 throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS,
                 retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT],
                 groupUniqueId=groupUniqueId, body=settings, fields='')
      entityActionPerformed([entityType, groupEmail])
      break
    except GAPI.resourceNotFound as e:
      # If group we're trying to create was just deleted, Google gets confused; sleep and retry
      duplicateRetries += 1
      if ciGroupsAPI or duplicateRetries > recentDeleteRetries:
        entityActionFailedWarning([entityType, groupEmail], str(e))
        break
      time.sleep(recentDeleteRetryDelay)
      continue
    except (GAPI.alreadyExists, GAPI.duplicate):
      duplicateRetries += 1
      if ciGroupsAPI or duplicateRetries > recentDeleteRetries:
        duplicateAliasGroupUserWarning(cd, [entityType, groupEmail])
        break
      time.sleep(recentDeleteRetryDelay)
      continue
#    except GAPI.notFound:
#      entityActionFailedWarning([entityType, groupEmail], Msg.DOES_NOT_EXIST)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.backendError,
            GAPI.invalid, GAPI.invalidArgument, GAPI.invalidAttributeValue, GAPI.invalidInput, GAPI.invalidArgument, GAPI.failedPrecondition,
            GAPI.badRequest, GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
      entityActionFailedWarning([entityType, groupEmail], str(e))
      break
    except GAPI.required:
      entityActionFailedWarning([entityType, groupEmail], Msg.INVALID_JSON_SETTING)
      break
  if ciGroupsAPI or not verifyCreationRetries:
    return
  Act.Set(Act.VERIFYITEMEXISTS)
  action = Act.Get()
  performAction(Ent.GROUP, groupEmail)
  Ind.Increment()
  waitingForCreationToComplete(verifyCreationInitialDelay)
  retries = 0
  while True:
    try:
      callGAPI(cd.groups(), 'get',
               throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
               groupKey=groupEmail, fields='name')
      entityActionPerformed([Ent.GROUP, groupEmail])
      break
    except GAPI.groupNotFound:
      retries += 1
      kvList = [Act.PerformedName(action), False, 'Retry', f'{retries}/{verifyCreationRetries}']
      printEntityKVList([Ent.GROUP, groupEmail], kvList)
      if retries >= verifyCreationRetries:
        entityActionFailedWarning([Ent.GROUP, groupEmail], Msg.RETRIES_EXHAUSTED.format(verifyCreationRetries))
        break
      waitingForCreationToComplete(verifyCreationRetryDelay)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.backendError,
            GAPI.invalid, GAPI.invalidArgument, GAPI.invalidMember, GAPI.invalidParameter, GAPI.invalidInput, GAPI.forbidden,
            GAPI.badRequest, GAPI.permissionDenied, GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
      entityActionFailedWarning([Ent.GROUP, groupEmail], str(e))
      break
    except KeyboardInterrupt:
      entityActionFailedWarning([Ent.GROUP, groupEmail], Msg.CHECK_INTERRUPTED)
      break
  Ind.Decrement()

# [addonly|removeonly]
def getSyncOperation():
  return getChoice(['addonly', 'removeonly'], defaultChoice='addremove')

UPDATE_GROUP_SUBCMDS = ['add', 'create', 'delete', 'remove', 'clear', 'sync', 'update']
GROUP_PREVIEW_TITLES = ['group', 'email', 'role', 'action', 'message']

# gam update groups <GroupEntity> [email <EmailAddress>]
#	[updateprimaryemail <RESEarchPattern> <RESubstitution> [preview]]
#	[copyfrom <GroupItem>] <GroupAttribute>*
#	[security|makesecuritygroup]
#	[admincreated <Boolean>]
#	[verifynotinvitable]
# gam update groups <GroupEntity> create [<GroupRole>]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[delivery <DeliverySetting>]
#	[preview] [actioncsv]
#	<UserTypeEntity>
# gam update groups <GroupEntity> delete|remove [<GroupRole>]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[preview] [actioncsv]
#	<UserTypeEntity>
# gam update groups <GroupEntity> sync [<GroupRole>|ignorerole]
#	[usersonly|groupsonly] [addonly|removeonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[removedomainnostatusmembers]
#	[delivery <DeliverySetting>] [preview] [actioncsv]
#	(additionalmembers <EmailAddressEntity>)*
#	<UserTypeEntity>
# gam update groups <GroupEntity> update [<GroupRole>]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[delivery <DeliverySetting>] [preview] [actioncsv]
#	[createifnotfound]
#	<UserTypeEntity>
# gam update groups <GroupEntity> clear [member] [manager] [owner]
#	[usersonly|groupsonly]
#	[notsuspended|suspended] [notarchived|archived]
#	[emailclearpattern|emailretainpattern <REMatchPattern>]
#	[removedomainnostatusmembers]
#	[preview] [actioncsv]
def doUpdateGroups():

  def _getPreviewActionCSV():
    preview = checkArgumentPresent('preview')
    if checkArgumentPresent('actioncsv'):
      csvPF = CSVPrintFile(GROUP_PREVIEW_TITLES)
    else:
      csvPF = None
    return (preview, csvPF)

  def _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count):
    roleLower = role.lower()
    if roleLower in GROUP_ROLES_MAP:
      return (GROUP_ROLES_MAP[roleLower], groupMemberLists[origGroup][role])
    entityActionNotPerformedWarning([entityType, group, Ent.ROLE, role], Msg.INVALID_ROLE.format(','.join(sorted(GROUP_ROLES_MAP))), i, count)
    return (None, None)

  def _getRoleGroupMemberType(defaultRole=Ent.ROLE_MEMBER, allowIgnoreRole=False):
    if not allowIgnoreRole or not checkArgumentPresent(['ignorerole']):
      role = getChoice(GROUP_ROLES_MAP, defaultChoice=defaultRole, mapChoice=True)
    else:
      role = Ent.ROLE_ALL
    groupMemberType = getChoice({'usersonly': Ent.TYPE_USER, 'groupsonly': Ent.TYPE_GROUP}, defaultChoice='ALL', mapChoice=True)
    return (role, groupMemberType)

  def _getMemberEmailStatus(member):
    if member['type'] == Ent.TYPE_CUSTOMER:
      return (member['id'], member.get('status', 'UNKNOWN'))
    email = member['email'].lower()
    if not removeDomainNoStatusMembers or 'status' in member:
      return (email, member.get('status', 'UNKNOWN'))
    _, domain = splitEmailAddress(email)
    if domain != GC.Values[GC.DOMAIN]:
      return (email, 'UNKNOWN')
    return (email, 'NONE')

  def _executeBatch(dbatch, batchParms):
    dbatch.execute()
    if batchParms['wait'] > 0:
      time.sleep(batchParms['wait'])

# Convert foo@googlemail.com to foo@gmail.com; eliminate periods in name for foo.bar@gmail.com
  def _cleanConsumerAddress(emailAddress, mapCleanToOriginal):
    atLoc = emailAddress.find('@')
    if atLoc > 0:
      if emailAddress[atLoc+1:] in {'gmail.com', 'googlemail.com'}:
        cleanEmailAddress = emailAddress[:atLoc].replace('.', '')+'@gmail.com'
        if cleanEmailAddress != emailAddress:
          mapCleanToOriginal[cleanEmailAddress] = emailAddress
          return cleanEmailAddress
    return emailAddress

  def _previewAction(group, members, role, jcount, action):
    Ind.Increment()
    j = 0
    for member in members:
      j += 1
      entityActionPerformed([entityType, group, role, member], j, jcount)
    Ind.Decrement()
    if csvPF:
      for member in members:
        csvPF.WriteRow({'group': group, 'email': member, 'role': role, 'action': Act.PerformedName(action), 'message': Act.PREVIEW})

  def _showSuccess(group, member, role, delivery_settings, j, jcount, optMsg=None):
    kvList = []
    if role is not None and role != 'None':
      kvList.append(f'{Ent.Singular(Ent.ROLE)}: {role}')
    if delivery_settings != DELIVERY_SETTINGS_UNDEFINED:
      kvList.append(f'{Ent.Singular(Ent.DELIVERY)}: {delivery_settings}')
    if optMsg:
      kvList.append(optMsg)
    entityActionPerformedMessage([entityType, group, Ent.MEMBER, member], ', '.join(kvList), j, jcount)
    if csvPF:
      csvPF.WriteRow({'group': group, 'email': member, 'role': role, 'action': Act.Performed(), 'message': Act.SUCCESS})

  def _showFailure(group, member, role, errMsg, j, jcount):
    entityActionFailedWarning([entityType, group, Ent.MEMBER, member, Ent.ROLE, role], errMsg, j, jcount)
    if csvPF:
      csvPF.WriteRow({'group': group, 'email': member, 'role': role, 'action': Act.Failed(), 'message': errMsg})

  def _addMember(group, i, count, role, delivery_settings, member, j, jcount):
    body = {'role': role}
    if member.find('@') != -1:
      body['email'] = member
    else:
      body['id'] = member
    if delivery_settings != DELIVERY_SETTINGS_UNDEFINED:
      body['delivery_settings'] = delivery_settings
    try:
      callGAPI(cd.members(), 'insert',
               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.DUPLICATE, GAPI.MEMBER_NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,
                                                        GAPI.INVALID_MEMBER, GAPI.CYCLIC_MEMBERSHIPS_NOT_ALLOWED,
                                                        GAPI.CONDITION_NOT_MET, GAPI.CONFLICT],
               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
               groupKey=group, body=body, fields='')
      _showSuccess(group, member, role, delivery_settings, j, jcount)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
      entityUnknownWarning(entityType, group, i, count)
    except (GAPI.duplicate, GAPI.memberNotFound, GAPI.resourceNotFound,
            GAPI.invalidMember, GAPI.cyclicMembershipsNotAllowed, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
      _showFailure(group, member, role, str(e), j, jcount)
    except GAPI.conflict:
      _showSuccess(group, member, role, delivery_settings, j, jcount, Msg.ACTION_MAY_BE_DELAYED)

  def _handleDuplicateAdd(group, i, count, role, delivery_settings, member, j, jcount):
    try:
      result = callGAPI(cd.members(), 'get',
                        throwReasons=[GAPI.MEMBER_NOT_FOUND, GAPI.RESOURCE_NOT_FOUND],
                        groupKey=group, memberKey=member, fields='role')
      _showFailure(group, member, role, Msg.DUPLICATE_ALREADY_A_ROLE.format(Ent.Singular(result['role'])), j, jcount)
      return
    except (GAPI.memberNotFound, GAPI.resourceNotFound):
      pass
    printEntityKVList([entityType, group, Ent.MEMBER, member], [Msg.MEMBERSHIP_IS_PENDING_WILL_DELETE_ADD_TO_ACCEPT], j, jcount)
    try:
      callGAPI(cd.members(), 'delete',
               throwReasons=[GAPI.MEMBER_NOT_FOUND, GAPI.RESOURCE_NOT_FOUND],
               groupKey=group, memberKey=member)
    except (GAPI.memberNotFound, GAPI.resourceNotFound):
      _showFailure(group, member, role, Msg.DUPLICATE, j, jcount)
      return
    _addMember(group, i, count, role, delivery_settings, member, j, jcount)

  _ADD_MEMBER_REASON_TO_MESSAGE_MAP = {GAPI.DUPLICATE: Msg.DUPLICATE,
                                       GAPI.CONDITION_NOT_MET: Msg.DUPLICATE,
                                       GAPI.MEMBER_NOT_FOUND: Msg.DOES_NOT_EXIST,
                                       GAPI.RESOURCE_NOT_FOUND: Msg.DOES_NOT_EXIST,
                                       GAPI.INVALID_MEMBER: Msg.INVALID_MEMBER,
                                       GAPI.CYCLIC_MEMBERSHIPS_NOT_ALLOWED: Msg.WOULD_MAKE_MEMBERSHIP_CYCLE}

  def _callbackAddGroupMembers(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      _showSuccess(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], ri[RI_OPTION], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in GAPI.MEMBERS_THROW_REASONS and reason != GAPI.SERVICE_NOT_AVAILABLE:
        entityUnknownWarning(entityType, ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]))
      elif reason == GAPI.CONFLICT:
        _showSuccess(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], ri[RI_OPTION], int(ri[RI_J]), int(ri[RI_JCOUNT]), Msg.ACTION_MAY_BE_DELAYED)
      elif reason in [GAPI.DUPLICATE, GAPI.CONDITION_NOT_MET]:
        _handleDuplicateAdd(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]), ri[RI_ROLE], ri[RI_OPTION], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
      elif reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.MEMBERS_RETRY_REASONS:
        errMsg = getHTTPError(_ADD_MEMBER_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        _showFailure(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        if addBatchParms['adjust']:
          addBatchParms['adjust'] = False
          addBatchParms['wait'] += 0.25
          writeStderr(f'{WARNING_PREFIX}{Msg.INTER_BATCH_WAIT_INCREASED.format(addBatchParms["wait"])}\n')
        time.sleep(0.1)
        _addMember(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]), ri[RI_ROLE], ri[RI_OPTION], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchAddGroupMembers(group, i, count, addMembers, role, delivery_settings):
    Act.Set([Act.ADD, Act.ADD_PREVIEW][preview])
    jcount = len(addMembers)
    entityPerformActionNumItems([entityType, group], jcount, role, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(group, addMembers, role, jcount, Act.ADD)
      return
    if addBatchParms['size'] == 1 or jcount <= addBatchParms['size']:
      Ind.Increment()
      j = 0
      for member in addMembers:
        j += 1
        _addMember(group, i, count, role, delivery_settings, member, j, jcount)
      Ind.Decrement()
      return
    body = {'role': role}
    if delivery_settings != DELIVERY_SETTINGS_UNDEFINED:
      body['delivery_settings'] = delivery_settings
    svcargs = dict([('groupKey', group), ('body', body), ('fields', '')]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(cd.members(), 'insert')
    dbatch = cd.new_batch_http_request(callback=_callbackAddGroupMembers)
    bcount = 0
    Ind.Increment()
    j = 0
    for member in addMembers:
      j += 1
      svcparms = svcargs.copy()
      if member.find('@') != -1:
        svcparms['body']['email'] = member
        svcparms['body'].pop('id', None)
      else:
        svcparms['body']['id'] = member
        svcparms['body'].pop('email', None)
      dbatch.add(method(**svcparms), request_id=batchRequestID(group, i, count, j, jcount, member, role, delivery_settings))
      bcount += 1
      if bcount >= addBatchParms['size']:
        addBatchParms['adjust'] = True
        _executeBatch(dbatch, addBatchParms)
        dbatch = cd.new_batch_http_request(callback=_callbackAddGroupMembers)
        bcount = 0
    if bcount > 0:
      dbatch.execute()
    Ind.Decrement()

  def _removeMember(group, i, count, role, member, j, jcount):
    try:
      callGAPI(cd.members(), 'delete',
               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER,
                                                        GAPI.RESOURCE_NOT_FOUND,
                                                        GAPI.CONDITION_NOT_MET, GAPI.CONFLICT],
               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
               groupKey=group, memberKey=member)
      _showSuccess(group, member, role, DELIVERY_SETTINGS_UNDEFINED, j, jcount)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
      entityUnknownWarning(entityType, group, i, count)
    except (GAPI.memberNotFound, GAPI.invalidMember, GAPI.resourceNotFound, GAPI.conditionNotMet, GAPI.serviceNotAvailable) as e:
      _showFailure(group, member, role, str(e), j, jcount)
    except GAPI.conflict:
      _showSuccess(group, member, role, DELIVERY_SETTINGS_UNDEFINED, j, jcount, Msg.ACTION_MAY_BE_DELAYED)

  _REMOVE_MEMBER_REASON_TO_MESSAGE_MAP = {GAPI.MEMBER_NOT_FOUND: f'{Msg.NOT_A} {Ent.Singular(Ent.MEMBER)}',
                                          GAPI.CONDITION_NOT_MET: f'{Msg.NOT_A} {Ent.Singular(Ent.MEMBER)}',
                                          GAPI.INVALID_MEMBER: Msg.DOES_NOT_EXIST}

  def _callbackRemoveGroupMembers(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      _showSuccess(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], DELIVERY_SETTINGS_UNDEFINED, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason in GAPI.MEMBERS_THROW_REASONS and reason != GAPI.SERVICE_NOT_AVAILABLE:
        entityUnknownWarning(entityType, ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]))
      elif reason == GAPI.CONFLICT:
        _showSuccess(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], DELIVERY_SETTINGS_UNDEFINED, int(ri[RI_J]), int(ri[RI_JCOUNT]), Msg.ACTION_MAY_BE_DELAYED)
      elif reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.MEMBERS_RETRY_REASONS+[GAPI.RESOURCE_NOT_FOUND]:
        errMsg = getHTTPError(_REMOVE_MEMBER_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        _showFailure(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        if remBatchParms['adjust']:
          remBatchParms['adjust'] = False
          remBatchParms['wait'] += 0.25
          writeStderr(f'{WARNING_PREFIX}{Msg.INTER_BATCH_WAIT_INCREASED.format(remBatchParms["wait"])}\n')
        time.sleep(0.1)
        _removeMember(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]), ri[RI_ROLE], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchRemoveGroupMembers(group, i, count, removeMembers, role, qualifier=''):
    Act.Set([Act.REMOVE, Act.REMOVE_PREVIEW][preview])
    jcount = len(removeMembers)
    if not qualifier:
      entityPerformActionNumItems([entityType, group], jcount, role, i, count)
    else:
      entityPerformActionNumItemsModifier([entityType, group], jcount, role, qualifier, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(group, removeMembers, role, jcount, Act.REMOVE)
      return
    if remBatchParms['size'] == 1 or jcount <= remBatchParms['size']:
      Ind.Increment()
      j = 0
      for member in removeMembers:
        j += 1
        _removeMember(group, i, count, role, member, j, jcount)
      Ind.Decrement()
      return
    svcargs = dict([('groupKey', group), ('memberKey', None)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(cd.members(), 'delete')
    dbatch = cd.new_batch_http_request(callback=_callbackRemoveGroupMembers)
    bcount = 0
    Ind.Increment()
    j = 0
    for member in removeMembers:
      j += 1
      svcparms = svcargs.copy()
      svcparms['memberKey'] = member
      dbatch.add(method(**svcparms), request_id=batchRequestID(group, i, count, j, jcount, svcparms['memberKey'], role))
      bcount += 1
      if bcount >= remBatchParms['size']:
        remBatchParms['adjust'] = True
        _executeBatch(dbatch, remBatchParms)
        dbatch = cd.new_batch_http_request(callback=_callbackRemoveGroupMembers)
        bcount = 0
    if bcount > 0:
      dbatch.execute()
    Ind.Decrement()

  _UPDATE_MEMBER_REASON_TO_MESSAGE_MAP = {GAPI.MEMBER_NOT_FOUND: f'{Msg.NOT_A} {Ent.Singular(Ent.MEMBER)}',
                                          GAPI.INVALID_MEMBER: Msg.DOES_NOT_EXIST,
                                          GAPI.RESOURCE_NOT_FOUND: Msg.DOES_NOT_EXIST}

  def _getUpdateBody(role, delivery_settings):
    body = {}
    if role is not None:
      body['role'] = role
    else:
      if delivery_settings == DELIVERY_SETTINGS_UNDEFINED:
        # Backwards compatability; if neither role or delivery is specified, role = MEMBER
        role = Ent.ROLE_MEMBER
        body['role'] = role
    if delivery_settings != DELIVERY_SETTINGS_UNDEFINED:
      body['delivery_settings'] = delivery_settings
    return (body, role)

  def _updateMember(group, i, count, role, delivery_settings, member, j, jcount):
    body, role = _getUpdateBody(role, delivery_settings)
    try:
      callGAPI(cd.members(), 'patch',
               throwReasons=GAPI.MEMBERS_THROW_REASONS+[GAPI.MEMBER_NOT_FOUND, GAPI.INVALID_MEMBER, GAPI.RESOURCE_NOT_FOUND],
               retryReasons=GAPI.MEMBERS_RETRY_REASONS,
               groupKey=group, memberKey=member, body=body, fields='')
      _showSuccess(group, member, role, delivery_settings, j, jcount)
    except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden):
      entityUnknownWarning(entityType, group, i, count)
    except GAPI.memberNotFound as e:
      if createIfNotFound:
        Act.Set(Act.ADD)
        _addMember(group, i, count, role, delivery_settings, member, j, jcount)
        Act.Set(Act.UPDATE)
      else:
        _showFailure(group, member, role, str(e), j, jcount)
    except (GAPI.invalidMember, GAPI.resourceNotFound, GAPI.serviceNotAvailable) as e:
      _showFailure(group, member, role, str(e), j, jcount)

  def _callbackUpdateGroupMembers(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      _showSuccess(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], ri[RI_OPTION], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason == GAPI.MEMBER_NOT_FOUND and createIfNotFound:
        Act.Set(Act.ADD)
        _addMember(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]), ri[RI_ROLE], ri[RI_OPTION], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
        Act.Set(Act.UPDATE)
      elif reason in GAPI.MEMBERS_THROW_REASONS and reason != GAPI.SERVICE_NOT_AVAILABLE:
        entityUnknownWarning(entityType, ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]))
      elif reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.MEMBERS_RETRY_REASONS:
        errMsg = getHTTPError(_UPDATE_MEMBER_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        _showFailure(ri[RI_ENTITY], ri[RI_ITEM], ri[RI_ROLE], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      else:
        if addBatchParms['adjust']:
          addBatchParms['adjust'] = False
          addBatchParms['wait'] += 0.25
          writeStderr(f'{WARNING_PREFIX}{Msg.INTER_BATCH_WAIT_INCREASED.format(addBatchParms["wait"])}\n')
        time.sleep(0.1)
        _updateMember(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]), ri[RI_ROLE], ri[RI_OPTION], ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _batchUpdateGroupMembers(group, i, count, updateMembers, role, delivery_settings):
    Act.Set([Act.UPDATE, Act.UPDATE_PREVIEW][preview])
    jcount = len(updateMembers)
    entityPerformActionNumItems([entityType, group], jcount, Ent.MEMBER, i, count)
    if jcount == 0:
      return
    if preview:
      _previewAction(group, updateMembers, role or Ent.ROLE_USER, jcount, Act.UPDATE)
      return
    if updBatchParms['size'] == 1 or jcount <= updBatchParms['size']:
      Ind.Increment()
      j = 0
      for member in updateMembers:
        j += 1
        _updateMember(group, i, count, role, delivery_settings, member, j, jcount)
      Ind.Decrement()
      return
    body, role = _getUpdateBody(role, delivery_settings)
    svcargs = dict([('groupKey', group), ('memberKey', None), ('body', body), ('fields', '')]+GM.Globals[GM.EXTRA_ARGS_LIST])
    method = getattr(cd.members(), 'patch')
    dbatch = cd.new_batch_http_request(callback=_callbackUpdateGroupMembers)
    bcount = 0
    Ind.Increment()
    j = 0
    for member in updateMembers:
      j += 1
      svcparms = svcargs.copy()
      svcparms['memberKey'] = member
      dbatch.add(method(**svcparms), request_id=batchRequestID(group, i, count, j, jcount, svcparms['memberKey'], role, delivery_settings))
      bcount += 1
      if bcount >= updBatchParms['size']:
        updBatchParms['adjust'] = True
        _executeBatch(dbatch, updBatchParms)
        dbatch = cd.new_batch_http_request(callback=_callbackUpdateGroupMembers)
        bcount = 0
    if bcount > 0:
      dbatch.execute()
    Ind.Decrement()

  cd = buildGAPIObject(API.DIRECTORY)
  ci = None
  entityType = Ent.GROUP
  csvPF = None
  getBeforeUpdate = preview = False
  entityList = getEntityList(Cmd.OB_GROUP_ENTITY)
  CL_subCommand = getChoice(UPDATE_GROUP_SUBCMDS, defaultChoice=None)
  addBatchParms = {'size': GC.Values[GC.BATCH_SIZE], 'wait': GC.Values[GC.INTER_BATCH_WAIT], 'adjust': True}
  remBatchParms = {'size': GC.Values[GC.BATCH_SIZE], 'wait': GC.Values[GC.INTER_BATCH_WAIT], 'adjust': True}
  updBatchParms = {'size': GC.Values[GC.BATCH_SIZE], 'wait': GC.Values[GC.INTER_BATCH_WAIT], 'adjust': True}
  if not CL_subCommand:
    body = {}
    gs_body = {}
    ci_body = {}
    verifyNotInvitable = False
    updatePrimaryEmail = []
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'email':
        body['email'] = getEmailAddress(noUid=True)
      elif myarg == 'updateprimaryemail':
        updatePrimaryEmail = list(getREPatternSubstitution(re.IGNORECASE))
        updatePrimaryEmail.append(checkArgumentPresent(['preview']))
      elif myarg == 'admincreated':
        body['adminCreated'] = getBoolean()
      elif myarg == 'getbeforeupdate':
        getBeforeUpdate = True
      elif myarg in {'security', 'makesecuritygroup'}:
        ci_body['labels'] = {CIGROUP_DISCUSSION_FORUM_LABEL: '',
                             CIGROUP_SECURITY_LABEL: ''}
      elif myarg == 'json':
        gs_body.update(getJSON(GROUP_JSON_SKIP_FIELDS))
      elif myarg == 'accesstype':
        gs_body.update(getChoice(GROUP_ACCESS_TYPE_CHOICE_MAP, mapChoice=True))
      elif myarg == 'verifynotinvitable':
        verifyNotInvitable = True
      else:
        getGroupAttrValue(myarg, gs_body)
    if ci_body:
      ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
    if gs_body:
      gs = buildGAPIObject(API.GROUPSSETTINGS)
      gs_body = getSettingsFromGroup(cd, ','.join(entityList), gs, gs_body)
      if ci_body:
        for k, v in GROUP_CIGROUP_FIELDS_MAP.items():
          if k in gs_body:
            ci_body[v] = gs_body.pop(k)
      if gs_body:
        if not getBeforeUpdate:
          settings = gs_body
      elif not ci_body:
        return
    elif not body and not ci_body and not updatePrimaryEmail:
      return
    Act.Set(Act.UPDATE)
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      ci, _, group = convertGroupCloudIDToEmail(ci, group, i, count)
      if updatePrimaryEmail:
        if updatePrimaryEmail[0].search(group) is not None:
          body['email'] = re.sub(updatePrimaryEmail[0], updatePrimaryEmail[1], group)
          if updatePrimaryEmail[2]:
            entityActionNotPerformedWarning([Ent.GROUP, group], Msg.UPDATE_PRIMARY_EMAIL_PREVIEW.format(body['email']), i, count)
            continue
        else:
          entityActionNotPerformedWarning([Ent.GROUP, group], Msg.PRIMARY_EMAIL_DID_NOT_MATCH_PATTERN.format(updatePrimaryEmail[0].pattern), i, count)
          continue
      if 'email' in body and verifyNotInvitable:
        isInvitableUser, _ = _getIsInvitableUser(None, body['email'])
        if isInvitableUser:
          entityActionNotPerformedWarning([Ent.GROUP, body['email']], Msg.EMAIL_ADDRESS_IS_UNMANAGED_ACCOUNT)
          continue
      if ci_body and 'email' in body:
        ci_body['groupKey'] = {'id': body.pop('email')}
      origGroup = group
      if gs_body and not GroupIsAbuseOrPostmaster(group):
        try:
          if group.find('@') == -1: # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
            group = callGAPI(cd.groups(), 'get',
                             throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                             groupKey=group, fields='email')['email']
          if getBeforeUpdate:
            settings = callGAPI(gs.groups(), 'get',
                                throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                                groupUniqueId=mapGroupEmailForSettings(group), fields='*')
            settings.update(gs_body)
          if not checkReplyToCustom(group, settings, i, count):
            continue
        except GAPI.notFound:
          entityActionFailedWarning([entityType, origGroup], Msg.DOES_NOT_EXIST, i, count)
          continue
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
                GAPI.backendError, GAPI.invalid, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
                GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
          entityActionFailedWarning([entityType, origGroup], str(e), i, count)
          continue
      if body:
        try:
          group = callGAPI(cd.groups(), 'update',
                           throwReasons=GAPI.GROUP_UPDATE_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                           groupKey=group, body=body, fields='email')['email']
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalid, GAPI.invalidInput,
                GAPI.systemError, GAPI.permissionDenied, GAPI.failedPrecondition, GAPI.forbidden) as e:
          entityActionFailedWarning([entityType, origGroup], str(e), i, count)
          continue
      if gs_body and not GroupIsAbuseOrPostmaster(group):
        try:
          callGAPI(gs.groups(), 'update',
                   bailOnInvalidError='messageModerationLevel' in settings,
                   throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                   groupUniqueId=mapGroupEmailForSettings(group), body=settings, fields='')
        except GAPI.notFound:
          entityActionFailedWarning([entityType, origGroup], Msg.DOES_NOT_EXIST, i, count)
          continue
        except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.backendError,
                GAPI.invalid, GAPI.invalidArgument, GAPI.invalidAttributeValue, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
                GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
          entityActionFailedWarning([entityType, origGroup], str(e), i, count)
          continue
        except GAPI.required:
          entityActionFailedWarning([entityType, origGroup], Msg.INVALID_JSON_SETTING, i, count)
          continue
      if ci_body:
        _, name, groupEmail = convertGroupEmailToCloudID(ci, group, i, count)
        if not name or not groupEmail:
          continue
        try:
          callGAPI(ci.groups(), 'patch',
                   throwReasons=GAPI.CIGROUP_UPDATE_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                   name=name, body=ci_body, updateMask=','.join(list(ci_body.keys())))
        except (GAPI.notFound, GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidInput, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.failedPrecondition, GAPI.serviceNotAvailable) as e:
          entityActionFailedWarning([Ent.CLOUD_IDENTITY_GROUP, groupEmail], str(e), i, count)
          continue
      entityActionPerformed([entityType, origGroup], i, count)
  elif CL_subCommand in {'create', 'add'}:
    baseRole, groupMemberType = _getRoleGroupMemberType()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    delivery_settings = getDeliverySettings()
    preview, csvPF = _getPreviewActionCSV()
    _, addMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                      isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = addMembers if isinstance(addMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      roleList = [baseRole]
      if groupMemberLists:
        if not subkeyRoleField:
          addMembers = groupMemberLists[group]
        else:
          roleList = groupMemberLists[group]
      origGroup = group
      ci, _, group = checkGroupExists(cd, ci, False, group, i, count)
      if not group:
        continue
      for role in roleList:
        if groupMemberLists and subkeyRoleField:
          role, addMembers = _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count)
          if role is None:
            continue
        _batchAddGroupMembers(group, i, count,
                              [convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                        checkForCustomerId=True) for member in addMembers],
                              role, delivery_settings)
  elif CL_subCommand in {'delete', 'remove'}:
    baseRole, groupMemberType = _getRoleGroupMemberType()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    preview, csvPF = _getPreviewActionCSV()
    _, removeMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                         isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = removeMembers if isinstance(removeMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      roleList = [baseRole]
      if groupMemberLists:
        if not subkeyRoleField:
          removeMembers = groupMemberLists[group]
        else:
          roleList = groupMemberLists[group]
      origGroup = group
      ci, _, group = checkGroupExists(cd, ci, False, group, i, count)
      if not group:
        continue
      for role in roleList:
        if groupMemberLists and subkeyRoleField:
          role, removeMembers = _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count)
          if role is None:
            continue
        _batchRemoveGroupMembers(group, i, count,
                                 [convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                           checkForCustomerId=True) for member in removeMembers],
                                 role)
  elif CL_subCommand == 'sync':
    baseRole, groupMemberType = _getRoleGroupMemberType(allowIgnoreRole=True)
    ignoreRole = baseRole == Ent.ROLE_ALL
    syncOperation = getSyncOperation()
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    removeDomainNoStatusMembers = checkArgumentPresent('removedomainnostatusmembers')
    delivery_settings = getDeliverySettings()
    preview, csvPF = _getPreviewActionCSV()
    additionalMembers = {}
    while checkArgumentPresent('additionalmembers'):
      additionalRole = getChoice(GROUP_ROLES_MAP, defaultChoice=baseRole, mapChoice=True)
      additionalMembers.setdefault(additionalRole, [])
      additionalMembers[additionalRole].extend(getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY))
    _, syncMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                       isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = syncMembers if isinstance(syncMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    syncMembersSets = {}
    syncMembersMaps = {}
    currentMembersSets = {}
    currentMembersMaps = {}
    domainNoStatusMembersSets = {}
    if groupMemberLists is None:
      syncMembersSets[baseRole] = set()
      syncMembersMaps[baseRole] = {}
      for member in syncMembers:
        syncMembersSets[baseRole].add(_cleanConsumerAddress(convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                                                     checkForCustomerId=True), syncMembersMaps[baseRole]))
      for member in additionalMembers.get(baseRole, []):
        syncMembersSets[baseRole].add(_cleanConsumerAddress(convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                                                     checkForCustomerId=True), syncMembersMaps[baseRole]))
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      origGroup = group
      ci, _, group = checkGroupExists(cd, ci, False, group, i, count)
      if not group:
        continue
      if groupMemberLists is None:
        roleList = [baseRole]
      else:
        if not subkeyRoleField:
          roleList = [baseRole]
        else:
          roleList = groupMemberLists[origGroup]
        for role in roleList:
          role = role.upper()
          syncMembersSets[role] = set()
          syncMembersMaps[role] = {}
      rolesSet = set()
      for role in roleList:
        origRole = role
        role = role.upper()
        if groupMemberLists is None:
          rolesSet.add(role)
        else:
          if not subkeyRoleField:
            rolesSet.add(role)
            syncMembers = groupMemberLists[origGroup]
          else:
            role, syncMembers = _validateSubkeyRoleGetMembers(group, origRole, origGroup, groupMemberLists, i, count)
            if role is None:
              continue
            rolesSet.add(role)
          for member in syncMembers:
            syncMembersSets[role].add(_cleanConsumerAddress(convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                                                     checkForCustomerId=True), syncMembersMaps[role]))
          for member in additionalMembers.get(role, []):
            syncMembersSets[role].add(_cleanConsumerAddress(convertUIDtoEmailAddress(member, cd=cd, emailTypes='any',
                                                                                     checkForCustomerId=True), syncMembersMaps[role]))
      if not rolesSet:
        continue
      memberRoles = ','.join(sorted(rolesSet))
      printGettingAllEntityItemsForWhom(memberRoles, group, entityType=entityType)
      try:
        result = callGAPIpages(cd.members(), 'list', 'members',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               groupKey=group,
                               roles=None if Ent.ROLE_MEMBER in rolesSet or ignoreRole else memberRoles,
                               fields='nextPageToken,members(email,id,type,status,role)',
                               maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
        entityUnknownWarning(entityType, group, i, count)
        continue
      for role in rolesSet:
        currentMembersSets[role] = set()
        currentMembersMaps[role] = {}
        domainNoStatusMembersSets[role] = set()
      for member in result:
        role = member.get('role', Ent.ROLE_MEMBER) if not ignoreRole else Ent.ROLE_ALL
        email, memberStatus = _getMemberEmailStatus(member)
        if groupMemberType in ('ALL', member['type']) and role in rolesSet:
          if not removeDomainNoStatusMembers or memberStatus != 'NONE':
            if _checkMemberStatusIsSuspendedIsArchived(memberStatus, isSuspended, isArchived):
              currentMembersSets[role].add(_cleanConsumerAddress(email, currentMembersMaps[role]))
          else:
            domainNoStatusMembersSets[role].add(member['id'])
      del result
      if syncOperation != 'addonly':
        for role in rolesSet:
          if domainNoStatusMembersSets[role]:
            _batchRemoveGroupMembers(group, i, count,
                                     domainNoStatusMembersSets[role],
                                     role)
          _batchRemoveGroupMembers(group, i, count,
                                   [currentMembersMaps[role].get(emailAddress, emailAddress) for emailAddress in currentMembersSets[role]-syncMembersSets[role]],
                                   role)
      if syncOperation != 'removeonly':
        for role in [Ent.ROLE_OWNER, Ent.ROLE_MANAGER, Ent.ROLE_MEMBER, Ent.ROLE_ALL]:
          if role in rolesSet:
            _batchAddGroupMembers(group, i, count,
                                  [syncMembersMaps[role].get(emailAddress, emailAddress) for emailAddress in syncMembersSets[role]-currentMembersSets[role]],
                                  role if role != Ent.ROLE_ALL else Ent.ROLE_MEMBER, delivery_settings)
  elif CL_subCommand == 'update':
    baseRole, groupMemberType = _getRoleGroupMemberType(defaultRole=None)
    isSuspended, isArchived = _getOptionalIsSuspendedIsArchived()
    delivery_settings = getDeliverySettings()
    preview, csvPF = _getPreviewActionCSV()
    createIfNotFound = checkArgumentPresent('createifnotfound')
    _, updateMembers = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                         isSuspended=isSuspended, isArchived=isArchived, groupMemberType=groupMemberType)
    groupMemberLists = updateMembers if isinstance(updateMembers, dict) else None
    subkeyRoleField = GM.Globals[GM.CSV_SUBKEY_FIELD]
    checkForExtraneousArguments()
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      roleList = [baseRole]
      if groupMemberLists:
        if not subkeyRoleField:
          updateMembers = groupMemberLists[group]
        else:
          roleList = groupMemberLists[group]
      origGroup = group
      ci, _, group = checkGroupExists(cd, ci, False, group, i, count)
      if not group:
        continue
      for role in roleList:
        if groupMemberLists and subkeyRoleField:
          role, updateMembers = _validateSubkeyRoleGetMembers(group, role, origGroup, groupMemberLists, i, count)
          if role is None:
            continue
        _batchUpdateGroupMembers(group, i, count,
                                 [convertUIDtoEmailAddress(member, cd=cd, emailTypes='any', checkForCustomerId=True) for member in updateMembers],
                                 role, delivery_settings)
  else: #clear
    rolesSet = set()
    groupMemberType = 'ALL'
    isSuspended = isArchived = None
    removeDomainNoStatusMembers = False
    emailMatchPattern = None
    clearMatch = True
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg in GROUP_ROLES_MAP:
        rolesSet.add(GROUP_ROLES_MAP[myarg])
      elif myarg == 'usersonly':
        groupMemberType = Ent.TYPE_USER
      elif myarg == 'groupsonly':
        groupMemberType = Ent.TYPE_GROUP
      elif myarg in SUSPENDED_ARGUMENTS:
        isSuspended = _getIsSuspended(myarg)
      elif myarg in ARCHIVED_ARGUMENTS:
        isArchived = _getIsArchived(myarg)
      elif myarg == 'removedomainnostatusmembers':
        removeDomainNoStatusMembers = True
      elif myarg in {'emailclearpattern', 'emailretainpattern'}:
        emailMatchPattern = getREPattern(re.IGNORECASE)
        clearMatch = myarg == 'emailclearpattern'
      elif myarg == 'preview':
        preview = True
      elif myarg == 'actioncsv':
        csvPF = CSVPrintFile(GROUP_PREVIEW_TITLES)
      else:
        unknownArgumentExit()
    if isSuspended is not None and isArchived is not None:
      if isSuspended == isArchived:
        qualifier = '(Suspended) (Archived)' if isSuspended else '(Non-Suspended) (Non-Archived)'
      else:
        qualifier = '(Suspended)' if isSuspended else '(Archived)'
    elif isSuspended is not None:
      qualifier = '(Suspended)' if isSuspended else '(Non-Suspended)'
    elif isArchived is not None:
      qualifier = '(Archived)' if isArchived else '(Non-Archived)'
    else:
      qualifier = ''
    Act.Set(Act.REMOVE)
    if not rolesSet:
      rolesSet.add(Ent.ROLE_MEMBER)
    memberRoles = ','.join(sorted(rolesSet))
    i = 0
    count = len(entityList)
    for group in entityList:
      i += 1
      ci, _, group = checkGroupExists(cd, ci, False, group, i, count)
      if not group:
        continue
      printGettingAllEntityItemsForWhom(memberRoles, group, entityType=entityType)
      try:
        result = callGAPIpages(cd.members(), 'list', 'members',
                               pageMessage=getPageMessageForWhom(),
                               throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                               groupKey=group, roles=None if Ent.ROLE_MEMBER in rolesSet else memberRoles,
                               fields='nextPageToken,members(email,id,type,status,role)',
                               maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable):
        entityUnknownWarning(entityType, group, i, count)
        continue
      removeMembers = {}
      for role in rolesSet:
        removeMembers[role] = set()
      for member in result:
        role = member.get('role', Ent.ROLE_MEMBER)
        email, memberStatus = _getMemberEmailStatus(member)
        if groupMemberType in ('ALL', member['type']) and role in rolesSet:
          if not removeDomainNoStatusMembers:
            if _checkMemberStatusIsSuspendedIsArchived(memberStatus, isSuspended, isArchived):
              if emailMatchPattern is None:
                removeMembers[role].add(email if memberStatus != 'UNKNOWN' else member['id'])
              elif member['type'] == Ent.TYPE_CUSTOMER:
                pass
              elif emailMatchPattern.match(email):
                if clearMatch:
                  removeMembers[role].add(email if memberStatus != 'UNKNOWN' else member['id'])
              else:
                if not clearMatch:
                  removeMembers[role].add(email if memberStatus != 'UNKNOWN' else member['id'])
          elif memberStatus == 'NONE':
            removeMembers[role].add(member['id'])
      del result
      for role in rolesSet:
        _batchRemoveGroupMembers(group, i, count, removeMembers[role], role, qualifier)
  if csvPF:
    csvPF.writeCSVfile('Group Updates')

def verifyGroupPrimaryEmail(cd, group, i, count):
  try:
    result = callGAPI(cd.groups(), 'get',
                      throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                      groupKey=group, fields='id,email')
    if (result['email'].lower() == group) or (result['id'] == group):
      return True
    entityActionNotPerformedWarning([Ent.GROUP, group], Msg.NOT_A_PRIMARY_EMAIL_ADDRESS, i, count)
    return False
  except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    pass
  entityUnknownWarning(Ent.GROUP, group, i, count)
  return False

# gam delete groups <GroupEntity> [noactionifalias]
def doDeleteGroups(ciGroupsAPI=False):
  if not ciGroupsAPI:
    cd = buildGAPIObject(API.DIRECTORY)
    ci = None
  else:
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  entityType = GROUP_CIGROUP_ENTITYTYPE_MAP[ciGroupsAPI]
  entityList = getEntityList(Cmd.OB_GROUP_ENTITY)
  if not ciGroupsAPI:
    noActionIfAlias = checkArgumentPresent('noactionifalias')
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for group in entityList:
    i += 1
    try:
      if not ciGroupsAPI:
        ci, _, groupKey = convertGroupCloudIDToEmail(ci, group, i, count)
        if noActionIfAlias and not verifyGroupPrimaryEmail(cd, groupKey, i, count):
          continue
        callGAPI(cd.groups(), 'delete',
                 throwReasons=[GAPI.GROUP_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                 groupKey=groupKey)
      else:
        _, groupKey, groupEmail = convertGroupEmailToCloudID(ci, group, i, count)
        if not groupKey or not groupEmail:
          continue
        callGAPI(ci.groups(), 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.DOMAIN_NOT_FOUND, GAPI.FORBIDDEN, GAPI.INVALID],
                 name=groupKey)
      entityActionPerformed([entityType, groupKey], i, count)
    except (GAPI.notFound, GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.invalid):
      entityUnknownWarning(entityType, groupKey, i, count)

def getGroupRoles(myarg, rolesSet):
  if myarg in {'role', 'roles'}:
    for role in getString(Cmd.OB_GROUP_ROLE_LIST).lower().replace(',', ' ').split():
      if role in GROUP_ROLES_MAP:
        rolesSet.add(GROUP_ROLES_MAP[role])
      else:
        invalidChoiceExit(role, GROUP_ROLES_MAP, True)
  elif myarg in GROUP_ROLES_MAP:
    rolesSet.add(GROUP_ROLES_MAP[myarg])
  else:
    return False
  return True

GROUP_MEMBER_TYPES_MAP = {
  'customer': Ent.TYPE_CUSTOMER,
  'group': Ent.TYPE_GROUP,
  'user': Ent.TYPE_USER,
  }
ALL_GROUP_MEMBER_TYPES = {Ent.TYPE_CUSTOMER, Ent.TYPE_GROUP, Ent.TYPE_USER}

def getGroupMemberTypes(myarg, typesSet):
  if myarg in {'type', 'types'}:
    for gtype in getString(Cmd.OB_GROUP_TYPE_LIST).lower().replace(',', ' ').split():
      if gtype in GROUP_MEMBER_TYPES_MAP:
        typesSet.add(GROUP_MEMBER_TYPES_MAP[gtype])
      else:
        invalidChoiceExit(gtype, GROUP_MEMBER_TYPES_MAP, True)
  else:
    return False
  return True

MEMBEROPTION_MEMBERNAMES = 0
MEMBEROPTION_NODUPLICATES = 1
MEMBEROPTION_RECURSIVE = 2
MEMBEROPTION_GETDELIVERYSETTINGS = 3
MEMBEROPTION_ISARCHIVED = 4
MEMBEROPTION_ISSUSPENDED = 5
MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP = 6
MEMBEROPTION_MATCHPATTERN = 7
MEMBEROPTION_DISPLAYMATCH = 8



def doPrintGroups():
  from gam.cmd.groups.members import (  # deferred: circular
      CIGROUP_FIELDS_CHOICE_MAP,
      CIGROUP_TIME_OBJECTS,
      GROUP_FIELDS_CHOICE_MAP,
      GROUP_INFO_PRINT_ORDER,
      addMemberInfoToRow,
      checkGroupMatchPatterns,
      checkGroupShowOwnedBy,
      finalizeIPSGMGroupRolesMemberDisplayOptions,
      getGroupFilters,
      getGroupMatchPatterns,
      getMemberMatchOptions,
      getPGGroupRolesMemberDisplayOptions,
      initIPSGMGroupMemberDisplayOptions,
      initMemberOptions,
      setMemberDisplaySortTitles,
      setMemberDisplayTitles,
      updateFieldsForGroupMatchPatterns,
  )
  def _printGroupRow(groupEntity, groupSettings, groupMembers):
    nonlocal itemCount
    row = {}
    if matchSettings:
      if not isinstance(groupSettings, dict):
        return
      for key, matchp in matchSettings.items():
        gvalue = groupSettings.get(key)
        if matchp['notvalues'] and gvalue in matchp['notvalues']:
          return
        if matchp['values'] and gvalue not in matchp['values']:
          return
    if showOwnedBy and not checkGroupShowOwnedBy(showOwnedBy, groupMembers):
      return
    if showItemCountOnly:
      itemCount += 1
      return
    if deprecatedAttributesSet and isinstance(groupSettings, dict):
      deprecatedKeys = []
      for key in groupSettings:
        if key in deprecatedAttributesSet:
          deprecatedKeys.append(key)
      for key in deprecatedKeys:
        groupSettings.pop(key)
    if addCSVData:
      row.update(addCSVData)
    if FJQC.formatJSON:
      row['email'] = groupEntity['email']
      if addCSVData and includeCSVDataInJSON:
        groupEntity.update(addCSVData)
      row['JSON'] = json.dumps(cleanJSON(groupEntity), ensure_ascii=False, sort_keys=True)
      if rolesSet and groupMembers is not None:
        row['JSON-members'] = json.dumps(groupMembers, ensure_ascii=False, sort_keys=True)
      if isinstance(groupSettings, dict):
        row['JSON-settings'] = json.dumps(cleanJSON(groupSettings), ensure_ascii=False, sort_keys=True)
      groupCloudIdentity = ciGroups.get(row['email'], {})
      if groupCloudIdentity:
        row['JSON-cloudIdentity'] = json.dumps(cleanJSON(groupCloudIdentity, timeObjects=CIGROUP_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)
      return
    for field in groupFieldsLists['cd']:
      if field in groupEntity:
        if isinstance(groupEntity[field], list):
          row[field] = delimiter.join(groupEntity[field])
        elif convertCRNL and field in GROUP_FIELDS_WITH_CRS_NLS:
          row[field] = escapeCRsNLs(groupEntity[field])
        else:
          row[field] = groupEntity[field]
    if rolesSet and groupMembers is not None:
      addMemberInfoToRow(row, groupMembers, typesSet, memberOptions, memberDisplayOptions, delimiter,
                         isSuspended, isArchived, False)
    if isinstance(groupSettings, dict):
      for key, value in groupSettings.items():
        if key not in {'kind', 'etag', 'email', 'name', 'description'}:
          if value is None:
            value = ''
          csvPF.AddTitles(key)
          if convertCRNL and key in GROUP_FIELDS_WITH_CRS_NLS:
            row[key] = escapeCRsNLs(value)
          else:
            row[key] = value
    groupCloudEntity = ciGroups.get(row['email'], {})
    if groupCloudEntity:
      for k, v in groupCloudEntity.pop('labels', {}).items():
        if v == '':
          groupCloudEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = True
        else:
          groupCloudEntity[f'labels{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{k}'] = v
      for key, value in sorted(flattenJSON({'cloudIdentity': groupCloudEntity}, flattened={}, timeObjects=CIGROUP_TIME_OBJECTS).items()):
        csvPF.AddTitles(key)
        row[key] = value
    csvPF.WriteRow(row)

  def _callbackProcessGroupBasic(request_id, response, exception):
    ri = request_id.splitlines()
    i = int(ri[RI_I])
    if exception is not None:
      http_status, reason, message = checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.GROUP_GET_RETRY_REASONS:
        if reason in GAPI.GROUP_GET_THROW_REASONS:
          entityUnknownWarning(Ent.GROUP, ri[RI_ENTITY], i, int(ri[RI_COUNT]))
        else:
          errMsg = getHTTPError({}, http_status, reason, message)
          entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP, None], errMsg, i, int(ri[RI_COUNT]))
        return
      waitOnFailure(1, 10, reason, message)
      try:
        response = callGAPI(cd.groups(), 'get',
                            throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                            groupKey=ri[RI_ENTITY], fields=cdfields)
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.systemError) as e:
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP, None], str(e), i, int(ri[RI_COUNT]))
        return
    entityList.append(response)

  def _callbackProcessGroupMembers(request_id, response, exception):
    ri = request_id.splitlines()
    i = int(ri[RI_I])
    totalItems = 0
    items = 'members'
    pageMessage = getPageMessageForWhom(forWhom=ri[RI_ENTITY], showFirstLastItems=True)
    if exception is not None:
      http_status, reason, message = checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.MEMBERS_RETRY_REASONS:
        errMsg = getHTTPError({}, http_status, reason, message)
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], ri[RI_ROLE], None], errMsg, i, int(ri[RI_COUNT]))
        groupData[i]['required'] -= 1
        return
      waitOnFailure(1, 10, reason, message)
      try:
        response = callGAPI(cd.members(), 'list',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            includeDerivedMembership=memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP],
                            groupKey=ri[RI_ENTITY], roles=ri[RI_ROLE], fields='nextPageToken,members(email,id,role,type,status)',
                            maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], ri[RI_ROLE], None], str(e), i, int(ri[RI_COUNT]))
        groupData[i]['required'] -= 1
        return
    while True:
      pageToken, totalItems = _processGAPIpagesResult(response, items, groupData[i][items], totalItems, pageMessage, 'email', ri[RI_ROLE])
      if not pageToken:
        _finalizeGAPIpagesResult(pageMessage)
        break
      try:
        response = callGAPI(cd.members(), 'list',
                            throwReasons=GAPI.MEMBERS_THROW_REASONS, retryReasons=GAPI.MEMBERS_RETRY_REASONS,
                            pageToken=pageToken,
                            includeDerivedMembership=memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP],
                            groupKey=ri[RI_ENTITY], roles=ri[RI_ROLE], fields='nextPageToken,members(email,id,role,type,status)',
                            maxResults=GC.Values[GC.MEMBER_MAX_RESULTS])
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.invalid, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], ri[RI_ROLE], None], str(e), i, int(ri[RI_COUNT]))
        break
    groupData[i]['required'] -= 1

  def _callbackProcessGroupSettings(request_id, response, exception):
    ri = request_id.splitlines()
    i = int(ri[RI_I])
    if exception is not None:
      http_status, reason, message = checkGAPIError(exception)
      if reason not in GAPI.DEFAULT_RETRY_REASONS+GAPI.GROUP_SETTINGS_RETRY_REASONS:
        errMsg = getHTTPError({}, http_status, reason, message)
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP_SETTINGS, None], errMsg, i, int(ri[RI_COUNT]))
        groupData[i]['required'] -= 1
        return
      waitOnFailure(1, 10, reason, message)
      try:
        response = callGAPI(gs.groups(), 'get',
                            throwReasons=GAPI.GROUP_SETTINGS_THROW_REASONS, retryReasons=GAPI.GROUP_SETTINGS_RETRY_REASONS,
                            groupUniqueId=mapGroupEmailForSettings(ri[RI_ENTITY]), fields=gsfields)
      except GAPI.notFound:
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP_SETTINGS, None], Msg.DOES_NOT_EXIST, i, int(ri[RI_COUNT]))
        response = {}
      except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
              GAPI.backendError, GAPI.invalid, GAPI.invalidParameter, GAPI.invalidInput, GAPI.badRequest, GAPI.permissionDenied,
              GAPI.systemError, GAPI.serviceLimit, GAPI.serviceNotAvailable, GAPI.authError) as e:
        entityActionFailedWarning([Ent.GROUP, ri[RI_ENTITY], Ent.GROUP_SETTINGS, None], str(e), i, int(ri[RI_COUNT]))
        response = {}
    groupData[i]['settings'] = response
    groupData[i]['required'] -= 1

  def _writeCompleteRows():
    complete = [k for k in groupData if groupData[k]['required'] == 0]
    for k in complete:
      _printGroupRow(groupData[k]['entity'], groupData[k]['settings'], groupData[k]['members'])
      del groupData[k]

  cd = buildGAPIObject(API.DIRECTORY)
  ci = None
  kwargsDict = initUserGroupDomainQueryFilters()
  convertCRNL = GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  getCloudIdentity = getSettings = showCIgroupKey = sortHeaders = False
  memberDisplayOptions = initIPSGMGroupMemberDisplayOptions()
  maxResults = None
  groupFieldsLists = {'cd': ['email'], 'ci': [], 'gs': []}
  csvPF = CSVPrintFile(groupFieldsLists['cd'])
  FJQC = FormatJSONQuoteChar(csvPF)
  rolesSet = set()
  typesSet = set()
  memberOptions = initMemberOptions()
  entitySelection = isSuspended = isArchived = None
  showOwnedBy = {}
  matchPatterns = {}
  matchSettings = {}
  deprecatedAttributesSet = set()
  ciGroups = {}
  showItemCountOnly = False
  addCSVData = {}
  includeCSVDataInJSON = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif getGroupFilters(myarg, kwargsDict, showOwnedBy):
      pass
    elif getGroupMatchPatterns(myarg, matchPatterns, False):
      pass
    elif myarg in {'group', 'groupns', 'groupsusp'}:
      entitySelection = [getString(Cmd.OB_EMAIL_ADDRESS)]
      if myarg == 'groupns':
        isSuspended = False
      elif myarg == 'groupsusp':
        isSuspended = True
    elif myarg == 'select':
      entitySelection = getEntityList(Cmd.OB_GROUP_ENTITY)
    elif myarg in SUSPENDED_ARGUMENTS:
      isSuspended = _getIsSuspended(myarg)
    elif myarg in ARCHIVED_ARGUMENTS:
      isArchived = _getIsArchived(myarg)
    elif myarg == 'maxresults':
      maxResults = getInteger(minVal=1, maxVal=200)
    elif myarg == 'nodeprecated':
      deprecatedAttributesSet.update([attr[0] for attr in GROUP_DISCOVER_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in GROUP_ASSIST_CONTENT_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in GROUP_MODERATE_CONTENT_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in GROUP_MODERATE_MEMBERS_ATTRIBUTES.values()])
      deprecatedAttributesSet.update([attr[0] for attr in GROUP_DEPRECATED_ATTRIBUTES.values()])
    elif myarg in {'convertcrnl', 'converttextnl', 'convertfooternl'}:
      convertCRNL = True
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'basic':
      sortHeaders = True
      for field in GROUP_FIELDS_CHOICE_MAP:
        csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg in {'ciallfields', 'allcifields'}:
      sortHeaders = True
      groupFieldsLists['ci'] = []
      for field in CIGROUP_FIELDS_CHOICE_MAP:
        addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
    elif myarg == 'settings':
      getSettings = sortHeaders = True
    elif myarg == 'allfields':
      getSettings = sortHeaders = True
      groupFieldsLists['cd'] = []
      groupFieldsLists['gs'] = []
      for field in GROUP_FIELDS_CHOICE_MAP:
        csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg == 'sortheaders':
      sortHeaders = getBoolean()
    elif myarg in GROUP_FIELDS_CHOICE_MAP:
      csvPF.AddField(myarg, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
    elif myarg in GROUP_ATTRIBUTES_SET:
      attrProperties = getGroupAttrProperties(myarg)
      csvPF.AddField(myarg, {myarg: attrProperties[0]}, groupFieldsLists['gs'])
    elif myarg == 'fields':
      for field in _getFieldsList():
        if field in GROUP_FIELDS_CHOICE_MAP:
          csvPF.AddField(field, GROUP_FIELDS_CHOICE_MAP, groupFieldsLists['cd'])
        else:
          attrProperties = getGroupAttrProperties(field)
          if attrProperties is None:
            invalidChoiceExit(field, list(GROUP_FIELDS_CHOICE_MAP)+list(GROUP_ATTRIBUTES_SET), True)
          csvPF.AddField(field, {field: attrProperties[0]}, groupFieldsLists['gs'])
    elif myarg == 'cifields':
      for field in _getFieldsList():
        if field in CIGROUP_FIELDS_CHOICE_MAP:
          addFieldToFieldsList(field, CIGROUP_FIELDS_CHOICE_MAP, groupFieldsLists['ci'])
        else:
          invalidChoiceExit(field, list(CIGROUP_FIELDS_CHOICE_MAP), True)
    elif myarg == 'matchsetting':
      valueList = getChoice({'not': 'notvalues'}, mapChoice=True, defaultChoice='values')
      matchBody = {}
      getGroupAttrValue(getString(Cmd.OB_FIELD_NAME).lower(), matchBody)
      for key, value in matchBody.items():
        matchSettings.setdefault(key, {'notvalues': [], 'values': []})
        matchSettings[key][valueList].append(value)
    elif getPGGroupRolesMemberDisplayOptions(myarg, rolesSet, memberDisplayOptions):
      pass
    elif getGroupMemberTypes(myarg, typesSet):
      pass
    elif getMemberMatchOptions(myarg, memberOptions):
      pass
    elif myarg == 'includederivedmembership':
      memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP] = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if not typesSet:
    typesSet = ALL_GROUP_MEMBER_TYPES
  showCategory, _ = finalizeIPSGMGroupRolesMemberDisplayOptions(cd, memberDisplayOptions, False)
  if showCategory:
    groupFieldsLists['gs'].append('allowExternalMembers')
  updateFieldsForGroupMatchPatterns(matchPatterns, groupFieldsLists['cd'], csvPF)
  if groupFieldsLists['cd']:
    cdfields = ','.join(set(groupFieldsLists['cd']))
    cdfieldsnp = f'nextPageToken,groups({cdfields})'
  else:
    cdfields = cdfieldsnp = None
  if matchSettings:
    groupFieldsLists['gs'].extend(list(matchSettings))
  if groupFieldsLists['gs']:
    getSettings = True
    gsfields = ','.join(set(groupFieldsLists['gs']))
  else:
    gsfields = None
  if getSettings:
    gs = buildGAPIObject(API.GROUPSSETTINGS)
  if groupFieldsLists['ci']:
    setTrueCustomerId(cd)
    getCloudIdentity = True
    showCIgroupKey = 'groupKey' in groupFieldsLists['ci']
    if not showCIgroupKey:
      groupFieldsLists['ci'].append('groupKey(id)')
    cifields = ','.join(set(groupFieldsLists['ci']))
    ci = buildGAPIObject(API.CLOUDIDENTITY_GROUPS)
  if FJQC.formatJSON:
    sortHeaders = False
    if showCategory:
      csvPF.AddJSONTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
    csvPF.AddJSONTitles('JSON')
    if rolesSet:
      csvPF.AddJSONTitle('JSON-members')
    if getSettings:
      csvPF.AddJSONTitle('JSON-settings')
    if getCloudIdentity:
      csvPF.AddJSONTitle('JSON-cloudIdentity')
  else:
    if showCategory:
      csvPF.AddTitles(['allowExternalMembers'])
    if addCSVData:
      csvPF.AddTitles(sorted(addCSVData.keys()))
    csvPF.SetSortAllTitles()
  getRolesSet = rolesSet.copy()
  if showOwnedBy:
    getRolesSet.add(Ent.ROLE_OWNER)
  getRoles = ','.join(sorted(getRolesSet))
  showDetails = getRoles or getSettings or getCloudIdentity
  if rolesSet:
    setMemberDisplayTitles(memberDisplayOptions, csvPF)
  if entitySelection is None:
    entityList = []
    for kwargsQuery in makeUserGroupDomainQueryFilters(kwargsDict, None, None, None):
      kwargs = kwargsQuery[0]
      query  = kwargsQuery[1]
      query, pquery = groupFilters(kwargs, query)
      printGettingAllAccountEntities(Ent.GROUP, pquery)
      try:
        entityList.extend(callGAPIpages(cd.groups(), 'list', 'groups',
                                        pageMessage=getPageMessage(showFirstLastItems=True), messageAttribute='email',
                                        throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                        orderBy='email', query=query, fields=cdfieldsnp, maxResults=maxResults, **kwargs))
      except (GAPI.invalidMember, GAPI.invalidInput) as e:
        if not invalidMember(query):
          entityActionFailedExit([Ent.GROUP, None], str(e))
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
        if kwargs.get('domain'):
          badRequestWarning(Ent.GROUP, Ent.DOMAIN, kwargs['domain'])
        else:
          accessErrorExit(cd)
  else:
    svcargs = dict([('groupKey', None), ('fields', cdfields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
    cdmethod = getattr(cd.groups(), 'get')
    cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupBasic)
    cdbcount = 0
    entityList = []
    i = 0
    count = len(entitySelection)
    for groupEntity in entitySelection:
      i += 1
      groupEmail = normalizeEmailAddressOrUID(groupEntity)
      svcparms = svcargs.copy()
      svcparms['groupKey'] = groupEmail
      printGettingEntityItem(Ent.GROUP, groupEmail, i, count)
      cdbatch.add(cdmethod(**svcparms), request_id=batchRequestID(groupEmail, i, count, 0, 0, None))
      cdbcount += 1
      if cdbcount >= GC.Values[GC.BATCH_SIZE]:
        executeBatch(cdbatch)
        cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupBasic)
        cdbcount = 0
    if cdbcount > 0:
      cdbatch.execute()
  required = 0
  if getRoles:
    required += 1
    svcargs = dict([('groupKey', None), ('roles', getRoles), ('fields', 'nextPageToken,members(email,id,role,type,status)'),
                    ('includeDerivedMembership', memberOptions[MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP]),
                    ('maxResults', GC.Values[GC.MEMBER_MAX_RESULTS])]+GM.Globals[GM.EXTRA_ARGS_LIST])
  if getSettings:
    required += 1
    svcargsgs = dict([('groupUniqueId', None), ('fields', gsfields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
  cdmethod = getattr(cd.members(), 'list')
  cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupMembers)
  cdbcount = 0
  if getSettings:
    gsmethod = getattr(gs.groups(), 'get')
    gsbatch = gs.new_batch_http_request(callback=_callbackProcessGroupSettings)
    gsbcount = 0
  groupData = {}
  itemCount = 0
  i = 0
  count = len(entityList)
  for groupEntity in entityList:
    i += 1
    groupEmail = groupEntity['email']
    if not checkGroupMatchPatterns(groupEmail, groupEntity, matchPatterns):
      continue
    if not showDetails:
      _printGroupRow(groupEntity, None, None)
      continue
    if getCloudIdentity:
      _, name, groupEmail = convertGroupEmailToCloudID(ci, groupEmail, i, count)
      printGettingEntityItemForWhom(Ent.CLOUD_IDENTITY_GROUP, groupEmail, i, count)
      if name and groupEmail:
        try:
          ciGroup = callGAPI(ci.groups(), 'get',
                             throwReasons=GAPI.CIGROUP_GET_THROW_REASONS, retryReasons=GAPI.CIGROUP_RETRY_REASONS,
                             name=name, fields=cifields)
          key = ciGroup['groupKey']['id']
          if not showCIgroupKey:
            ciGroup.pop('groupKey')
          ciGroups[key] = ciGroup
        except (GAPI.notFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
                GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.invalidArgument,
                GAPI.systemError, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
          entityActionFailedWarning([Ent.GROUP, groupEmail, Ent.CLOUD_IDENTITY_GROUP, None], str(e), i, count)
    groupData[i] = {'entity': groupEntity, 'cloudIdentity': {}, 'settings': getSettings, 'members': [], 'required': required}
    if getRoles:
      printGettingEntityItemForWhom(getRoles, groupEmail, i, count)
      svcparms = svcargs.copy()
      svcparms['groupKey'] = groupEmail
      cdbatch.add(cdmethod(**svcparms), request_id=batchRequestID(groupEmail, i, count, 0, 0, None, getRoles))
      cdbcount += 1
      if cdbcount >= GC.Values[GC.BATCH_SIZE]:
        executeBatch(cdbatch)
        cdbatch = cd.new_batch_http_request(callback=_callbackProcessGroupMembers)
        cdbcount = 0
        _writeCompleteRows()
    if getSettings:
      if not GroupIsAbuseOrPostmaster(groupEmail):
        printGettingEntityItemForWhom(Ent.GROUP_SETTINGS, groupEmail, i, count)
        svcparmsgs = svcargsgs.copy()
        svcparmsgs['groupUniqueId'] = mapGroupEmailForSettings(groupEmail)
        gsbatch.add(gsmethod(**svcparmsgs), request_id=batchRequestID(groupEmail, i, count, 0, 0, None))
        gsbcount += 1
        if gsbcount >= GC.Values[GC.BATCH_SIZE]:
          executeBatch(gsbatch)
          gsbatch = gs.new_batch_http_request(callback=_callbackProcessGroupSettings)
          gsbcount = 0
          _writeCompleteRows()
      else:
        groupData[i]['settings'] = False
        groupData[i]['required'] -= 1
  if cdbcount > 0:
    cdbatch.execute()
  if getSettings and gsbcount > 0:
    gsbatch.execute()
  _writeCompleteRows()
  if showItemCountOnly:
    writeStdout(f'{itemCount}\n')
    return
  if sortHeaders:
    sortTitles = ['email']
    if showCategory:
      sortTitles.append('allowExternalMembers')
    if addCSVData:
      sortTitles.extend(sorted(addCSVData.keys()))
    sortTitles.extend(GROUP_INFO_PRINT_ORDER+['aliases', 'nonEditableAliases'])
    if getSettings:
      sortTitles += sorted([attr[0] for attr in GROUP_SETTINGS_ATTRIBUTES.values()])
      for key in GROUP_MERGED_ATTRIBUTES_PRINT_ORDER:
        sortTitles.append(key)
        if not deprecatedAttributesSet:
          sortTitles += sorted([attr[0] for attr in GROUP_MERGED_TO_COMPONENT_MAP[key].values()])
      if not deprecatedAttributesSet:
        sortTitles += sorted([attr[0] for attr in GROUP_DEPRECATED_ATTRIBUTES.values()])
    if rolesSet:
      setMemberDisplaySortTitles(memberDisplayOptions, sortTitles)
    csvPF.SetSortTitles(sortTitles)
  csvPF.SortRows('email', False)
  csvPF.writeCSVfile('Groups')


def doInfoGroups():
  from gam.cmd.groups.members import infoGroups  # deferred: circular
  infoGroups(getEntityList(Cmd.OB_GROUP_ENTITY))
