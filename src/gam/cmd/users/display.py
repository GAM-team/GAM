"""User info display and print/show operations.

Part of the _users_tmp sub-package."""

"""GAM user management."""

import re
import json
import sys

from gam.util.csv_pf import RI_JCOUNT, RI_ITEM

from gam.cmd.users.manage import (
    USER_ADDRESSES_PROPERTY_PRINT_ORDER,
    USER_ARRAY_PROPERTY_PRINT_ORDER,
    USER_FIELDS_CHOICE_MAP,
    USER_GUEST_PROPERTY_PRINT_ORDER,
    USER_LANGUAGE_PROPERTY_PRINT_ORDER,
    USER_LOCATIONS_PROPERTY_PRINT_ORDER,
    USER_NAME_PROPERTY_PRINT_ORDER,
    USER_ORGANIZATIONS_PROPERTY_PRINT_ORDER,
    USER_POSIX_PROPERTY_PRINT_ORDER,
    USER_SCALAR_PROPERTY_PRINT_ORDER,
    USER_SKIP_OBJECTS,
    USER_SSH_PROPERTY_PRINT_ORDER,
    USER_TIME_OBJECTS,
)

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

from gamlib import glskus as SKU
from gamlib import gluprop as UProp
from util.csv_pf import RI_J, RI_JCOUNT, RI_ITEM
from gam.util.html import dehtml
from gam.cmd.groups.members import INFO_GROUP_OPTIONS
from gam.util.display import invalidQuery, invalidUserSchema


from gam.cmd.users.manage import (  # cross-module refs
    USER_ADDRESSES_PROPERTY_PRINT_ORDER,
    USER_ARRAY_PROPERTY_PRINT_ORDER,
    USER_FIELDS_CHOICE_MAP,
    USER_GUEST_PROPERTY_PRINT_ORDER,
    USER_LANGUAGE_PROPERTY_PRINT_ORDER,
    USER_LOCATIONS_PROPERTY_PRINT_ORDER,
    USER_NAME_PROPERTY_PRINT_ORDER,
    USER_ORGANIZATIONS_PROPERTY_PRINT_ORDER,
    USER_POSIX_PROPERTY_PRINT_ORDER,
    USER_SCALAR_PROPERTY_PRINT_ORDER,
    USER_SKIP_OBJECTS,
    USER_SSH_PROPERTY_PRINT_ORDER,
    USER_TIME_OBJECTS,
    _filterSchemaFields,
    _filterUserMultiAttributes,
    _formatLanguagesList,
    _getSchemaNameList,
    _getUserMultiAttributeFilters,
    getUserLicenses,
    _initSchemaParms,
)

def infoUsers(entityList):
  def printUserCIGroupMap(parent, group_name_mappings, seen_group_count, edges, direction):
    for a_parent, a_child in edges:
      if a_parent == parent:
        output = f'{Ind.Spaces()}{a_child}: {group_name_mappings[a_child]} ({direction})'
        if seen_group_count[a_child] > 1:
          output += ' *'
        _getMain().printLine(output)
        Ind.Increment()
        printUserCIGroupMap(a_child, group_name_mappings, seen_group_count, edges, 'inherited')
        Ind.Decrement()

  def _showType(row, typeKey, typeCustomValue, customTypeKey, defaultType=None):
    if typeKey in row:
      if row[typeKey] != typeCustomValue or not row.get(customTypeKey):
        _getMain().printKeyValueList([typeKey, row[typeKey]])
      else:
        _getMain().printKeyValueList([typeKey, row[typeKey]])
        Ind.Increment()
        _getMain().printKeyValueList([customTypeKey, row[customTypeKey]])
        Ind.Decrement()
      return True
    if customTypeKey in row:
      _getMain().printKeyValueList([customTypeKey, row[customTypeKey]])
      return True
    if defaultType:
      _getMain().printKeyValueList([typeKey, defaultType])
      return True
    return False

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  ci = None
  _getMain().setTrueCustomerId(cd)
  getAliases = getBuildingNames = getCIGroupsTree = getGroups = getLicenses = getSchemas = not GC.Values[GC.QUICK_INFO_USER]
  getGroupsTree = getIsGuestUser = False
  FJQC = _getMain().FormatJSONQuoteChar()
  schemaParms = _initSchemaParms('full')
  viewType = 'admin_view'
  fieldsList = []
  groups = []
  memberships = []
  userMultiAttributeFilters = {}
  skus = SKU.getAllSKUs() if not GM.Globals[GM.LICENSE_SKUS] else GM.Globals[GM.LICENSE_SKUS]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'quick':
      getAliases = getBuildingNames = getCIGroupsTree = getGroups = getGroupsTree = getLicenses = getSchemas = False
    elif myarg in {'noaliases', 'aliases'}:
      getAliases = myarg == 'aliases'
    elif myarg in {'nobuildingnames', 'buildingnames'}:
      getBuildingNames = myarg == 'buildingnames'
    elif myarg in {'nogroups', 'groups', 'grouptree', 'cigrouptree'}:
      getGroups = getGroupsTree = getCIGroupsTree = False
      getGroups = myarg == 'groups'
      getGroupsTree = myarg == 'grouptree'
      getCIGroupsTree = myarg == 'cigrouptree'
    elif myarg in {'nolicenses', 'nolicences', 'licenses', 'licences'}:
      getLicenses = myarg in {'licenses', 'licences'}
    elif myarg == 'noschemas':
      getSchemas = False
      schemaParms = _initSchemaParms('basic')
    elif myarg in {'allschemas', 'custom', 'schemas', 'customschemas'}:
      if myarg == 'allschemas':
        schemaParms = _initSchemaParms('full')
      else:
        _getSchemaNameList(schemaParms)
      getSchemas = True
    elif myarg in {'products', 'product'}:
      skus = SKU.convertProductListToSKUList(_getMain().getGoogleProductList())
    elif myarg in {'sku', 'skus'}:
      skus = _getMain().getGoogleSKUList()
    elif myarg == 'userview':
      viewType = 'domain_public'
      getGroups = getLicenses = False
    elif _getMain().getFieldsList(myarg, USER_FIELDS_CHOICE_MAP, fieldsList):
      pass
    elif myarg in {'filtermultiattrtype', 'filtermultiattrcustom'}:
      _getUserMultiAttributeFilters(myarg, userMultiAttributeFilters)
# Ignore info group arguments that may have come from whatis
    elif myarg in INFO_GROUP_OPTIONS:
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if fieldsList:
    fieldsList.append('primaryEmail')
    if getSchemas:
      fieldsList.append('customSchemas')
    if getAliases:
      fieldsList.extend(['aliases', 'nonEditableAliases'])
  getIsGuestUser = not fieldsList or 'isGuestUser' in fieldsList
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  if getLicenses:
    lic = _getMain().buildGAPIObject(API.LICENSING)
# Special case; for info users, 'all users' means 'all users_ns_susp'
  if isinstance(entityList, dict) and entityList.get('entityType') == Cmd.ENTITY_ALL_USERS:
    entityList['entityType'] = Cmd.ENTITY_ALL_USERS_NS_SUSP
  groupParents = {}
  i, count, entityList = _getMain().getEntityArgument(entityList)
  for userEmail in entityList:
    i += 1
    userEmail = _getMain().normalizeEmailAddressOrUID(userEmail)
    try:
      user = _getMain().callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS+[GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND],
                      userKey=userEmail, projection=schemaParms['projection'], customFieldMask=schemaParms['customFieldMask'],
                      viewType=viewType, fields=fields)
      if getIsGuestUser and 'isGuestUser' not in user:
        user['isGuestUser'] = False
      if userMultiAttributeFilters:
        _filterUserMultiAttributes(user, userMultiAttributeFilters)
      groups = []
      memberships = []
      if getGroups or getGroupsTree:
        kwargs = {}
        if GC.Values[GC.ENABLE_DASA]:
          # Allows groups.list() to function but will limit
          # returned groups to those in same domain as user
          # so only do this for DASA admins
          kwargs['domain'] = GC.Values[GC.DOMAIN]
        try:
          groups = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                                 throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 userKey=user['primaryEmail'], orderBy='email', fields='nextPageToken,groups(name,email)', **kwargs)
        except (GAPI.forbidden, GAPI.domainNotFound):
### Print some message
          pass
      elif getCIGroupsTree:
        ci, memberships = _getMain().getCIGroupMembershipGraph(ci, user['primaryEmail'])
        if memberships is None:
          getCIGroupsTree = False
      licenses = getUserLicenses(lic, user, skus) if getLicenses else []
      if FJQC.formatJSON:
        if getGroups or getGroupsTree:
          user['groups'] = groups
          if getGroupsTree:
            for group in user['groups']:
              groupEmail = group['email']
              if groupEmail not in groupParents:
                _getMain().getGroupParents(cd, groupParents, groupEmail, group['name'], {})
              _getMain().addJsonGroupParents(groupParents, group, groupEmail)
        if getLicenses:
          user['licenses'] = [SKU.formatSKUIdDisplayName(u_license) for u_license in licenses]
        if getBuildingNames:
          for location in user.get('locations', []):
            location['buildingName'] = _getMain()._getBuildingNameById(cd, location.get('buildingId', ''))
        if not getAliases:
          user.pop('aliases', None)
          user.pop('nonEditableAliases', None)
        if not getSchemas:
          user.pop('customSchemas', None)
        _getMain().printLine(json.dumps(_getMain().cleanJSON(user, skipObjects=USER_SKIP_OBJECTS, timeObjects=USER_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
        continue
      _getMain().printEntity([Ent.USER, user['primaryEmail']], i, count)
      Ind.Increment()
      _getMain().printKeyValueList(['Settings', None])
      Ind.Increment()
      up = 'name'
      if up in user:
        for nup in USER_NAME_PROPERTY_PRINT_ORDER:
          if nup in user[up]:
            _getMain().printKeyValueList([UProp.PROPERTIES[nup][UProp.TITLE], user[up][nup]])
      up = 'languages'
      if up in user:
        _getMain().printKeyValueList([UProp.PROPERTIES[up][UProp.TITLE], _formatLanguagesList(user[up], ',')])
      for up in USER_SCALAR_PROPERTY_PRINT_ORDER:
        if up in user:
          if up not in USER_TIME_OBJECTS:
            if up != 'guestAccountInfo':
              _getMain().printKeyValueList([UProp.PROPERTIES[up][UProp.TITLE], user[up]])
            else:
              for gup in USER_GUEST_PROPERTY_PRINT_ORDER:
                if gup in user[up]:
                  _getMain().printKeyValueList([UProp.PROPERTIES[gup][UProp.TITLE], user[up][gup]])
          else:
            _getMain().printKeyValueList([UProp.PROPERTIES[up][UProp.TITLE], _getMain().formatLocalTime(user[up])])
      Ind.Decrement()
      for up in USER_ARRAY_PROPERTY_PRINT_ORDER:
        if up not in user:
          continue
        propertyValue = user[up]
        userProperty = UProp.PROPERTIES[up]
        propertyClass = userProperty[UProp.CLASS]
        propertyTitle = userProperty[UProp.TITLE]
        if UProp.TYPE_KEYWORDS in userProperty:
          typeKey = userProperty[UProp.TYPE_KEYWORDS][UProp.PTKW_ATTR_TYPE_KEYWORD]
          typeCustomValue = userProperty[UProp.TYPE_KEYWORDS][UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]
          customTypeKey = userProperty[UProp.TYPE_KEYWORDS][UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD]
        if propertyClass == UProp.PC_ARRAY:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            for row in propertyValue:
              _showType(row, typeKey, typeCustomValue, customTypeKey)
              Ind.Increment()
              for key in row:
                if key in [typeKey, customTypeKey]:
                  continue
                _getMain().printKeyValueList([key, row[key]])
              Ind.Decrement()
            Ind.Decrement()
        elif propertyClass == UProp.PC_GENDER:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            _showType(propertyValue, typeKey, typeCustomValue, customTypeKey)
            if 'addressMeAs' in propertyValue:
              _getMain().printKeyValueList(['addressMeAs', propertyValue['addressMeAs']])
            Ind.Decrement()
        elif propertyClass == UProp.PC_ADDRESSES:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            for row in propertyValue:
              _showType(row, typeKey, typeCustomValue, customTypeKey)
              Ind.Increment()
              for key in USER_ADDRESSES_PROPERTY_PRINT_ORDER:
                if key in row:
                  if key != 'formatted':
                    _getMain().printKeyValueList([key, row[key]])
                  else:
                    _getMain().printKeyValueWithCRsNLs(key, row[key])
              Ind.Decrement()
            Ind.Decrement()
        elif propertyClass == UProp.PC_EMAILS:
          if propertyValue:
            needTitle = True
            for row in propertyValue:
              if row['address'].lower() == user['primaryEmail'].lower():
                continue
              if needTitle:
                needTitle = False
                _getMain().printKeyValueList([propertyTitle, None])
                Ind.Increment()
              if not _showType(row, typeKey, typeCustomValue, customTypeKey):
                if not getAliases:
                  continue
                _getMain().printKeyValueList([typeKey, 'alias'])
              Ind.Increment()
              for key in row:
                if key in [typeKey, customTypeKey]:
                  continue
                _getMain().printKeyValueList([key, row[key]])
              Ind.Decrement()
            if not needTitle:
              Ind.Decrement()
        elif propertyClass == UProp.PC_IMS:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            protocolKey = UProp.IM_PROTOCOLS[UProp.PTKW_ATTR_TYPE_KEYWORD]
            protocolCustomValue = UProp.IM_PROTOCOLS[UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]
            customProtocolKey = UProp.IM_PROTOCOLS[UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD]
            for row in propertyValue:
              _showType(row, typeKey, typeCustomValue, customTypeKey)
              Ind.Increment()
              _showType(row, protocolKey, protocolCustomValue, customProtocolKey)
              for key in row:
                if key in [typeKey, customTypeKey, protocolKey, customProtocolKey]:
                  continue
                _getMain().printKeyValueList([key, row[key]])
              Ind.Decrement()
            Ind.Decrement()
        elif propertyClass == UProp.PC_NOTES:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            if isinstance(propertyValue, dict):
              typeVal = propertyValue.get(typeKey, 'text_plain')
              _getMain().printKeyValueList([typeKey, typeVal])
              Ind.Increment()
              if typeVal == 'text_html':
                _getMain().printKeyValueWithCRsNLs('value', dehtml(propertyValue['value']))
              else:
                _getMain().printKeyValueWithCRsNLs('value', propertyValue['value'])
              Ind.Decrement()
            else:
              _getMain().printKeyValueList([Ind.MultiLineText(propertyValue)])
            Ind.Decrement()
        elif propertyClass == UProp.PC_LOCATIONS:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            if isinstance(propertyValue, list):
              for row in propertyValue:
                _showType(row, typeKey, typeCustomValue, customTypeKey)
                Ind.Increment()
                if getBuildingNames:
                  row['buildingName'] = _getMain()._getBuildingNameById(cd, row.get('buildingId', ''))
                for key in USER_LOCATIONS_PROPERTY_PRINT_ORDER:
                  if key in row:
                    _getMain().printKeyValueList([key, row[key]])
                Ind.Decrement()
            else:
              _getMain().printKeyValueList([Ind.MultiLineText(propertyValue)])
            Ind.Decrement()
        elif propertyClass == UProp.PC_ORGANIZATIONS:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            for row in propertyValue:
              _showType(row, typeKey, typeCustomValue, customTypeKey)
              Ind.Increment()
              for key in USER_ORGANIZATIONS_PROPERTY_PRINT_ORDER:
                if key in row:
                  _getMain().printKeyValueList([key, row[key]])
              Ind.Decrement()
            Ind.Decrement()
        elif propertyClass == UProp.PC_POSIX:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            if isinstance(propertyValue, list):
              for row in propertyValue:
                _getMain().printKeyValueList(['username', row.get('username')])
                Ind.Increment()
                for key in USER_POSIX_PROPERTY_PRINT_ORDER:
                  if key in row:
                    _getMain().printKeyValueList([key, row[key]])
                Ind.Decrement()
            else:
              _getMain().printKeyValueList([Ind.MultiLineText(propertyValue)])
            Ind.Decrement()
        elif propertyClass == UProp.PC_SSH:
          if propertyValue:
            _getMain().printKeyValueList([propertyTitle, None])
            Ind.Increment()
            if isinstance(propertyValue, list):
              for row in propertyValue:
                _getMain().printKeyValueList(['key', row['key']])
                Ind.Increment()
                for key in USER_SSH_PROPERTY_PRINT_ORDER:
                  if key in row:
                    _getMain().printKeyValueList([key, row[key]])
                Ind.Decrement()
            else:
              _getMain().printKeyValueList([Ind.MultiLineText(propertyValue)])
            Ind.Decrement()
      if getSchemas:
        up = 'customSchemas'
        if up in user:
          propertyValue = user[up]
          userProperty = UProp.PROPERTIES[up]
          propertyTitle = userProperty[UProp.TITLE]
          typeKey = userProperty[UProp.TYPE_KEYWORDS][UProp.PTKW_ATTR_TYPE_KEYWORD]
          typeCustomValue = userProperty[UProp.TYPE_KEYWORDS][UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]
          customTypeKey = userProperty[UProp.TYPE_KEYWORDS][UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD]
          if schemaParms['selectedSchemaFields']:
            _filterSchemaFields(user, schemaParms)
          propertyValue = user[up]
          if propertyValue:
            _getMain().printKeyValueList([UProp.PROPERTIES[up][UProp.TITLE], None])
            Ind.Increment()
            for schema in sorted(propertyValue):
              _getMain().printKeyValueList(['Schema', schema])
              Ind.Increment()
              for field in propertyValue[schema]:
                if isinstance(propertyValue[schema][field], list):
                  _getMain().printKeyValueList([field])
                  Ind.Increment()
                  for an_item in propertyValue[schema][field]:
                    _showType(an_item, typeKey, typeCustomValue, customTypeKey, defaultType='work')
                    Ind.Increment()
                    _getMain().printKeyValueList(['value', an_item['value']])
                    Ind.Decrement()
                  Ind.Decrement()
                else:
                  _getMain().printKeyValueList([field, propertyValue[schema][field]])
              Ind.Decrement()
            Ind.Decrement()
      if getAliases:
        for up in ['aliases', 'nonEditableAliases']:
          propertyValue = user.get(up, [])
          if propertyValue:
            _getMain().printEntitiesCount([Ent.NONEDITABLE_ALIAS, Ent.EMAIL_ALIAS][up == 'aliases'], propertyValue)
            Ind.Increment()
            for alias in propertyValue:
              _getMain().printKeyValueList(['alias', alias])
            Ind.Decrement()
      if getGroups:
        _getMain().printEntitiesCount(Ent.GROUP, groups)
        Ind.Increment()
        for group in groups:
          _getMain().printKeyValueList([group['name'], group['email']])
        Ind.Decrement()
      elif getGroupsTree:
        _getMain().printEntity([Ent.GROUP_MEMBERSHIP_TREE, ''])
        Ind.Increment()
        for group in groups:
          groupEmail = group['email']
          if groupEmail not in groupParents:
            _getMain().getGroupParents(cd, groupParents, groupEmail, group['name'], {})
          _getMain().showGroupParents(groupParents, groupEmail, None, 0, 0)
        Ind.Decrement()
      elif getCIGroupsTree:
        _getMain().printEntity([Ent.GROUP_MEMBERSHIP_TREE, ''])
        if memberships:
          Ind.Increment()
          group_name_mapping = {}
          group_displayname_mapping = {}
          groups = memberships.get('groups', [])
          for group in groups:
            group_name = group.get('name')
            group_key = group.get('groupKey', {})
            group_email = group_key.get('id', '')
            group_display_name = group.get('displayName', '')
            group_name_mapping[group_name] = group_email
            group_displayname_mapping[group_email] = group_display_name
          edges = []
          seen_group_count = {}
          for adj in memberships.get('adjacencyList', []):
            group_name = adj.get('group', '')
            group_email = group_name_mapping[group_name]
            for edge in adj.get('edges', []):
              seen_group_count[group_email] = seen_group_count.get(group_email, 0) + 1
              member_email = edge.get('preferredMemberKey', {}).get('id')
              edges.append((member_email, group_email))
          printUserCIGroupMap(user['primaryEmail'], group_displayname_mapping, seen_group_count, edges, 'direct')
          if max(seen_group_count.values()) > 1:
            _getMain().printLine(f'{Ind.Spaces()}* {Msg.USER_HAS_MULTIPLE_DIRECT_OR_INHERITED_MEMBERSHIPS_IN_GROUP}')
          Ind.Decrement()
      if getLicenses:
        _getMain().printEntitiesCount(Ent.LICENSE, licenses)
        Ind.Increment()
        for u_license in licenses:
          _getMain().printKeyValueList([SKU.formatSKUIdDisplayName(u_license)])
        Ind.Decrement()
      Ind.Decrement()
    except GAPI.userNotFound:
      _getMain().entityUnknownWarning(Ent.USER, userEmail, i, count)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.backendError, GAPI.systemError) as e:
      _getMain().entityActionFailedWarning([Ent.USER, userEmail], str(e), i, count)
    except (GAPI.invalidInput, GAPI.invalidMember) as e:
      if schemaParms['customFieldMask']:
        _getMain().entityActionFailedWarning([Ent.USER, userEmail], _getMain().invalidUserSchema(schemaParms['customFieldMask']), i, count)
      else:
        _getMain().entityActionFailedWarning([Ent.USER, userEmail], str(e), i, count)

# gam info users <UserTypeEntity>
#	[quick]
#	[noaliases|aliases]
#	[nobuildingnames|buildingnames]
#	[nogroups|groups|grouptree|cigrouptree]
#	[nolicenses|nolicences|licenses|licences]
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)]
#	[noschemas|allschemas|(schemas|custom|customschemas <SchemaNameList>)]
#	[userview] <UserFieldName>* [fields <UserFieldNameList>]
#	[formatjson]
def doInfoUsers():
  infoUsers(_getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS, delayGet=True)[1])

# gam info user <UserItem>
#	[quick]
#	[noaliases|aliases]
#	[nobuildingnames|buildingnames]
#	[nogroups|groups|grouptree|cigrouptree]
#	[nolicenses|nolicences|licenses|licences]
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)]
#	[noschemas|allschemas|(schemas|custom|customschemas <SchemaNameList>)]
#	[userview] <UserFieldName>* [fields <UserFieldNameList>]
#	[formatjson]
# gam info user
def doInfoUser():
  if Cmd.ArgumentsRemaining():
    infoUsers(_getMain().getStringReturnInList(Cmd.OB_USER_ITEM))
  else:
    infoUsers([_getMain()._getAdminEmail()])

USERS_ORDERBY_CHOICE_MAP = {
  'familyname': 'familyName',
  'lastname': 'familyName',
  'givenname': 'givenName',
  'firstname': 'givenName',
  'email': 'email',
  }
USERS_INDEXED_TITLES = ['addresses', 'aliases', 'nonEditableAliases', 'emails', 'externalIds',
                        'ims', 'keywords', 'locations', 'organizations',
                        'phones', 'posixAccounts', 'relations', 'sshPublicKeys', 'websites']

# gam print users [todrive <ToDriveAttribute>*]
#	([domain|domains <DomainNameEntity>] [(query <QueryUser>)|(queries <QueryUserList>)]
#	 [limittoou <OrgUnitItem>] [deleted_only|only_deleted])|[select <UserTypeEntity>]
#	[groups|groupsincolumns]
#	[license|licenses|licence|licences|licensebyuser|licensesbyuser|licencebyuser|licencesbyuser]
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)]
#	[emailpart|emailparts|username] [schemas|custom all|<SchemaNameList>]
#	[orderby <UserOrderByFieldName> [ascending|descending]]
#	[userview] [basic|full|allfields | <UserFieldName>* | fields <UserFieldNameList>]
#	[delimiter <Character>] [sortheaders] [formatjson [quotechar <Character>]] [quoteplusphonenumbers]
#	[convertcrnl]
#	([issuspended [<Boolean>]] [isarchived [<Boolean>]])|(isdisabled [<Boolean>])]
#	[disabledafter <DateTime>] [disabledbefore <DateTime>]
#	[aliasmatchpattern <REMatchPattern>]
# 	[showitemcountonly]
#	[showvalidcolumn] (addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#
# gam <UserTypeEntity> print users [todrive <ToDriveAttribute>*]
#	[groups|groupsincolumns]
#	[license|licenses|licence|licences|licensebyuser|licensesbyuser|licencebyuser|licencesbyuser]
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)]
#	[emailpart|emailparts|username] [schemas|custom all|<SchemaNameList>]
#	[orderby <UserOrderByFieldName> [ascending|descending]]
#	[userview] [basic|full|allfields | <UserFieldName>* | fields <UserFieldNameList>]
#	[delimiter <Character>] [sortheaders] [formatjson [quotechar <Character>]] [quoteplusphonenumbers]
#	[convertcrnl]
#	([issuspended [<Boolean>]] [isarchived [<Boolean>]])|(isdisabled [<Boolean>])]
#	[disabledafter <DateTime>] [disabledbefore <DateTime>]
#	[aliasmatchpattern <REMatchPattern>]
# 	[showitemcountonly]
#	[showvalidcolumn] (addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#
# gam print users [todrive <ToDriveAttribute>*]
#	([domain <DomainName>] [(query <QueryUser>)|(queries <QueryUserList>)]
#	 [limittoou <OrgUnitItem>] [deleted_only|only_deleted])|[select <UserTypeEntity>]
#	[formatjson [quotechar <Character>]] [countonly]
#	([issuspended [<Boolean>]] [isarchived [<Boolean>]])|(isdisabled [<Boolean>])]
#	[disabledafter <DateTime>] [disabledbefore <DateTime>]
#	[aliasmatchpattern <REMatchPattern>]
# 	[showitemcountonly]
#	[showvalidcolumn] (addcsvdata <FieldName> <String>)* [includecsvdatainjson [<Boolean>]]
#
# gam <UserTypeEntity> print users [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]] [countonly]
#	[issuspended <Boolean>] [isarchived <Boolean>]
# 	[showitemcountonly]
def doPrintUsers(entityList=None):
  def _writeUserEntity(userEntity):
    row = _getMain().flattenJSON(userEntity, skipObjects=USER_SKIP_OBJECTS, timeObjects=USER_TIME_OBJECTS)
    if not FJQC.formatJSON:
      if addCSVData:
        row.update(addCSVData)
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      row = {'primaryEmail': userEntity['primaryEmail']}
      if showValidColumn:
        row[showValidColumn] = userEntity[showValidColumn]
      if addCSVData:
        row.update(addCSVData)
        if includeCSVDataInJSON:
          userEntity.update(addCSVData)
      row['JSON'] = json.dumps(_getMain().cleanJSON(userEntity, skipObjects=USER_SKIP_OBJECTS, timeObjects=USER_TIME_OBJECTS),
                               ensure_ascii=False, sort_keys=True)
      csvPF.WriteRowNoFilter(row)

  def _getDisabledTimeStr(userEntity):
    disabledTimeStr = ''
    if isDisabled or (isSuspended and isArchived):
      if 'suspensionTime' in userEntity:
        if 'archivalTime' in userEntity:
          disabledTimeStr = min(userEntity['suspensionTime'], userEntity['archivalTime'])
        else:
          disabledTimeStr = userEntity['suspensionTime']
          userEntity['archivalTime'] = ''
      elif 'archivalTime' in userEntity:
        disabledTimeStr = userEntity['archivalTime']
        userEntity['suspensionTime'] = ''
    elif isSuspended:
      if 'suspensionTime' in userEntity:
        disabledTimeStr = userEntity['suspensionTime']
    else: #isArchived
      if 'archivalTime' in userEntity:
        disabledTimeStr = userEntity['archivalTime']
    return disabledTimeStr

  def _printUser(userEntity, i, count):
    getDisabledTime = isDisabled or isSuspended or isArchived
    if disabledAfterTime is not None or disabledBeforeTime is not None:
      if not (isDisabled or isSuspended or isArchived):
        return
      if isDisabled:
        if (not (('suspended' in userEntity and userEntity['suspended']) or
                 ('archived' in userEntity and userEntity['archived']))):
          return
        if userEntity['primaryEmail'] in archivedSuspendedUsers:
          return
        archivedSuspendedUsers.add(userEntity['primaryEmail'])
      else:
        if (isSuspended and not ('suspended' in userEntity and userEntity['suspended'])):
          return
        if (isArchived and not ('archived' in userEntity and userEntity['archived'])):
          return
      disabledTimeStr = _getDisabledTimeStr(userEntity)
      if not disabledTimeStr:
        return
      try:
        disabledTime = arrow.get(disabledTimeStr)
        if ((disabledAfterTime is not None and disabledTime < disabledAfterTime) or
            (disabledBeforeTime is not None and disabledTime >= disabledBeforeTime)):
          return
      except (arrow.parser.ParserError, OverflowError):
        return
      userEntity.update({'disabled': True, 'disabledTime':  disabledTimeStr})
      getDisabledTime = False
      showUser = True
    elif isDisabled is not None:
      if isDisabled:
        showUser = ((isDisabled == userEntity.get('suspended', False)) or
                    (isDisabled == userEntity.get('archived', False)))
      else:
        showUser = ((isDisabled == userEntity.get('suspended', False)) and
                    (isDisabled == userEntity.get('archived', False)))
      if showUser and userEntity['primaryEmail'] in archivedSuspendedUsers:
        return
      archivedSuspendedUsers.add(userEntity['primaryEmail'])
      userEntity['disabled'] = isDisabled
    elif (isSuspended is None and isArchived is None):
      showUser = True
    elif (isSuspended is not None and isArchived is None):
      showUser = isSuspended == userEntity.get('suspended', False)
      userEntity['disabled'] = isSuspended
    elif (isSuspended is None and isArchived is not None):
      showUser = isArchived == userEntity.get('archived', False)
      userEntity['disabled'] = isArchived
    else: # (isSuspended is not None and isArchived is not None)
      showUser = ((isSuspended == userEntity.get('suspended', False)) and
                  (isArchived == userEntity.get('archived', False)))
      if showUser and userEntity['primaryEmail'] in archivedSuspendedUsers:
        return
      archivedSuspendedUsers.add(userEntity['primaryEmail'])
      userEntity['disabled'] = isSuspended or isArchived
    if not showUser:
      return
    if getDisabledTime:
      userEntity['disabledTime'] =  _getDisabledTimeStr(userEntity)
    if getIsGuestUser and 'isGuestUser' not in userEntity:
      userEntity['isGuestUser'] = False
    if showValidColumn:
      userEntity[showValidColumn] = True
    if userMultiAttributeFilters:
      _filterUserMultiAttributes(userEntity, userMultiAttributeFilters)
    userEmail = userEntity['primaryEmail']
    if printOptions['emailParts']:
      if userEmail.find('@') != -1:
        userEntity['primaryEmailLocal'], userEntity['primaryEmailDomain'] = _getMain().splitEmailAddress(userEmail)
    if 'languages' in userEntity and not FJQC.formatJSON:
      userEntity['languages'] = _formatLanguagesList(userEntity.pop('languages'), delimiter)
    for location in userEntity.get('locations', []):
      location['buildingName'] = _getMain()._getBuildingNameById(cd, location.get('buildingId', ''))
    if quotePlusPhoneNumbers:
      for phone in userEntity.get('phones', []):
        phoneNumber = phone.get('value', '')
        if phoneNumber.startswith('+'):
          phone['value'] = "'"+phoneNumber
    if schemaParms['selectedSchemaFields']:
      _filterSchemaFields(userEntity, schemaParms)
    if printOptions['getGroupFeed']:
      _getMain().printGettingAllEntityItemsForWhom(Ent.GROUP_MEMBERSHIP, userEmail, i, count)
      try:
        groups = _getMain().callGAPIpages(cd.groups(), 'list', 'groups',
                               pageMessage=_getMain().getPageMessageForWhom(),
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               userKey=userEmail, orderBy='email', fields='nextPageToken,groups(email)')
        numGroups = len(groups)
        if not printOptions['groupsInColumns']:
          userEntity['GroupsCount'] = numGroups
          userEntity['Groups'] = delimiter.join([groupname['email'] for groupname in groups])
        else:
          if numGroups > printOptions['maxGroups']:
            printOptions['maxGroups'] = numGroups
          userEntity['Groups'] = numGroups
          for j, group in enumerate(groups):
            userEntity[f'Groups{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}'] = group['email']
      except (GAPI.invalidMember, GAPI.invalidInput):
        _getMain().badRequestWarning(Ent.GROUP, Ent.MEMBER, userEmail)
      except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
        _getMain().accessErrorExit(cd)
    if aliasMatchPattern and 'aliases' in userEntity:
      userEntity['aliases'] = [alias for alias in userEntity['aliases'] if aliasMatchPattern.match(alias)]
    if printOptions['getLicenseFeed'] or printOptions['getLicenseFeedByUser']:
      if printOptions['getLicenseFeed']:
        u_licenses = licenses.get(userEmail.lower(), [])
      else:
        u_licenses = getUserLicenses(lic, userEntity, skus)
      if not oneLicensePerRow:
        userEntity['LicensesCount'] = len(u_licenses)
        if u_licenses:
          userEntity['Licenses'] = delimiter.join(u_licenses)
          userEntity['LicensesDisplay'] = delimiter.join([SKU.skuIdToDisplayName(skuId) for skuId in u_licenses])
    else:
      u_licenses = []
    if not oneLicensePerRow:
      _writeUserEntity(userEntity)
    else:
      if u_licenses:
        for skuId in u_licenses:
          userEntity['License'] = skuId
          userEntity['LicenseDisplay'] = SKU.skuIdToDisplayName(skuId)
          _writeUserEntity(userEntity)
      else:
        userEntity['License'] = userEntity['LicenseDisplay'] = ''
        _writeUserEntity(userEntity)

  def _updateDomainCounts(emailAddress):
    nonlocal domainCounts
    atLoc = emailAddress.find('@')
    if atLoc == -1:
      dom = _getMain().UNKNOWN
    else:
      dom = emailAddress[atLoc+1:].lower()
    domainCounts.setdefault(dom, 0)
    domainCounts[dom] += 1

  _PRINT_USER_REASON_TO_MESSAGE_MAP = {GAPI.RESOURCE_NOT_FOUND: Msg.DOES_NOT_EXIST}
  def _callbackPrintUser(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _printUser(response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      if reason in GAPI.USER_GET_THROW_REASONS:
        if not showValidColumn:
          _getMain().entityUnknownWarning(Ent.USER, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
        else:
          _writeUserEntity({'primaryEmail': ri[RI_ITEM], showValidColumn: False})
      elif (reason == GAPI.INVALID_INPUT) and schemaParms['customFieldMask']:
        _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ITEM]], _getMain().invalidUserSchema(schemaParms['customFieldMask']), int(ri[RI_J]), int(ri[RI_JCOUNT]))
      elif reason not in GAPI.DEFAULT_RETRY_REASONS:
        errMsg = _getMain().getHTTPError(_PRINT_USER_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        _getMain().printKeyValueList([_getMain().ERROR, errMsg])
      else:
        _getMain().waitOnFailure(1, 10, reason, message)
        try:
          user = _getMain().callGAPI(cd.users(), 'get',
                          throwReasons=GAPI.USER_GET_THROW_REASONS+[GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND, GAPI.RATE_LIMIT_EXCEEDED],
                          userKey=ri[RI_ITEM], projection=schemaParms['projection'], customFieldMask=schemaParms['customFieldMask'],
                          viewType=viewType, fields=fields)
          _printUser(user, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        except (GAPI.userNotFound, GAPI.resourceNotFound):
          if not showValidColumn:
            _getMain().entityUnknownWarning(Ent.USER, ri[RI_ITEM], int(ri[RI_J]), int(ri[RI_JCOUNT]))
          else:
            _writeUserEntity({'primaryEmail': ri[RI_ITEM], showValidColumn: False})
        except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
                GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.rateLimitExceeded) as e:
          _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ITEM]], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))
        except GAPI.invalidInput as e:
          if schemaParms['customFieldMask']:
            _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ITEM]], _getMain().invalidUserSchema(schemaParms['customFieldMask']), int(ri[RI_J]), int(ri[RI_JCOUNT]))
          else:
            _getMain().entityActionFailedWarning([Ent.USER, ri[RI_ITEM]], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  fieldsList = ['primaryEmail']
  csvPF = _getMain().CSVPrintFile(fieldsList, indexedTitles=USERS_INDEXED_TITLES)
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  printOptions = {
    'countOnly': False,
    'emailParts': False,
    'getGroupFeed': False,
    'getLicenseFeed': False,
    'getLicenseFeedByUser': False,
    'groupsInColumns': False,
    'scalarsFirst': False,
    'sortHeaders': False,
    'maxGroups': 0
    }
  kwargsDict = _getMain().initUserGroupDomainQueryFilters()
  licenses = {}
  lic = None
  skus = None
  maxResults = GC.Values[GC.USER_MAX_RESULTS]
  schemaParms = _initSchemaParms('basic')
  projectionSet = False
  getIsGuestUser = oneLicensePerRow = quotePlusPhoneNumbers = showDeleted = False
  aliasMatchPattern = orgUnitPath = orgUnitPathLower = orderBy = sortOrder = None
  disabledAfterTime = disabledBeforeTime = isArchived = isDisabled = isSuspended = None
  archivedSuspendedUsers = set()
  viewType = 'admin_view'
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  showValidColumn = ''
  showItemCountOnly = False
  addCSVData = {}
  includeCSVDataInJSON = False
  userMultiAttributeFilters = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif entityList is None and myarg == 'limittoou':
      orgUnitPath = _getMain().getOrgUnitItem(pathOnly=True, cd=cd)
      orgUnitPathLower = orgUnitPath.lower()
    elif entityList is None and _getMain().getUserGroupDomainQueryFilters(myarg, kwargsDict):
      pass
    elif entityList is None and myarg in {'deletedonly', 'onlydeleted'}:
      showDeleted = True
    elif entityList is None and myarg == 'select':
      _, entityList = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    elif myarg == 'issuspended':
      isSuspended = _getMain().getBoolean()
      isDisabled = None
    elif myarg == 'isarchived':
      isArchived = _getMain().getBoolean()
      isDisabled = None
    elif myarg == 'isdisabled':
      isDisabled  = _getMain().getBoolean()
      isSuspended = isArchived = None
    elif myarg == 'disabledafter':
      disabledAfterTime, _, _ = _getMain().getTimeOrDeltaFromNow(True)
    elif myarg == 'disabledbefore':
      disabledBeforeTime, _, _ = _getMain().getTimeOrDeltaFromNow(True)
    elif myarg == 'orderby':
      orderBy, sortOrder = _getMain().getOrderBySortOrder(USERS_ORDERBY_CHOICE_MAP)
    elif myarg == 'userview':
      viewType = 'domain_public'
    elif myarg in {'allfields', 'basic'}:
      schemaParms = _initSchemaParms('basic')
      projectionSet = printOptions['sortHeaders'] = True
      fieldsList = []
    elif myarg == 'full':
      if schemaParms['projection'] != 'custom':
        schemaParms = _initSchemaParms(myarg)
      projectionSet = printOptions['sortHeaders'] = True
      fieldsList = []
    elif myarg in {'custom', 'schemas', 'customschemas'}:
      projectionSet = True
      _getSchemaNameList(schemaParms)
      if fieldsList:
        fieldsList.append('customSchemas')
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    elif myarg == 'sortheaders':
      printOptions['sortHeaders'] = _getMain().getBoolean()
    elif myarg == 'scalarsfirst':
      printOptions['scalarsFirst'] = _getMain().getBoolean()
    elif csvPF.GetFieldsListTitles(myarg, USER_FIELDS_CHOICE_MAP, fieldsList, initialField='primaryEmail'):
      pass
    elif myarg == 'groups':
      printOptions['getGroupFeed'] = True
      printOptions['groupsInColumns'] = False
    elif myarg == 'groupsincolumns':
      printOptions['getGroupFeed'] = True
      printOptions['groupsInColumns'] = True
    elif myarg in {'license', 'licenses', 'licence', 'licences'}:
      printOptions['getLicenseFeed'] = True
      printOptions['getLicenseFeedByUser'] = False
    elif myarg in {'licensebyuser', 'licensesbyuser', 'licencebyuser', 'licencesbyuser'}:
      printOptions['getLicenseFeedByUser'] = True
      printOptions['getLicenseFeed'] = False
    elif myarg in {'onelicenseperrow', 'onelicenceperrow'}:
      oneLicensePerRow = True
    elif myarg in {'products', 'product'}:
      skus = SKU.convertProductListToSKUList(_getMain().getGoogleProductList())
    elif myarg in {'sku', 'skus'}:
      skus = _getMain().getGoogleSKUList()
    elif myarg == 'aliasmatchpattern':
      aliasMatchPattern = _getMain().getREPattern(re.IGNORECASE)
    elif myarg in {'emailpart', 'emailparts', 'username'}:
      printOptions['emailParts'] = True
    elif myarg in {'countonly', 'countsonly'}:
      printOptions['countOnly'] = True
    elif myarg == 'maxresults':
      maxResults = _getMain().getInteger(minVal=1, maxVal=500)
    elif myarg == 'quoteplusphonenumbers':
      quotePlusPhoneNumbers = True
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif myarg == 'showvalidcolumn':
      showValidColumn = 'Valid'
    elif myarg == 'addcsvdata':
      _getMain().getAddCSVData(addCSVData)
    elif myarg == 'includecsvdatainjson':
      includeCSVDataInJSON = _getMain().getBoolean()
    elif myarg in {'filtermultiattrtype', 'filtermultiattrcustom'}:
      _getUserMultiAttributeFilters(myarg, userMultiAttributeFilters)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  _, _, entityList = _getMain().getEntityArgument(entityList)
  if printOptions['countOnly']:
    fieldsList = ['primaryEmail']
    domainCounts = {}
    if not FJQC.formatJSON:
      csvPF.SetTitles(['domain', 'count'])
    else:
      csvPF.SetJSONTitles(['JSON'])
  else:
    if FJQC.formatJSON:
      printOptions['sortHeaders'] = False
      titles = ['primaryEmail']
      if showValidColumn:
        titles.append(showValidColumn)
      if addCSVData:
        titles.extend(sorted(addCSVData.keys()))
      titles.append('JSON')
      csvPF.SetJSONTitles(titles)
    else:
      if showValidColumn:
        csvPF.AddTitles([showValidColumn])
      if addCSVData:
        csvPF.AddTitles(sorted(addCSVData.keys()))
      if printOptions['getGroupFeed']:
        if not printOptions['groupsInColumns']:
          csvPF.AddTitles(['GroupsCount', 'Groups'])
        else:
          csvPF.AddTitles(['Groups'])
      if printOptions['getLicenseFeed'] or printOptions['getLicenseFeedByUser']:
        if not oneLicensePerRow:
          licenseTitles = ['LicensesCount', 'Licenses', 'LicensesDisplay']
        else:
          licenseTitles = ['License', 'LicenseDisplay']
        csvPF.AddTitles(licenseTitles)
    if printOptions['getLicenseFeed']:
      if skus is None and GM.Globals[GM.LICENSE_SKUS]:
        skus = GM.Globals[GM.LICENSE_SKUS]
      licenses = _getMain().doPrintLicenses(returnFields=['userId', 'skuId'], skus=skus)
    elif printOptions['getLicenseFeedByUser']:
      lic = _getMain().buildGAPIObject(API.LICENSING)
      if skus is None:
        skus = SKU.getAllSKUs() if not GM.Globals[GM.LICENSE_SKUS] else GM.Globals[GM.LICENSE_SKUS]
  if ((disabledAfterTime is not None or disabledBeforeTime is not None) and
      isArchived is None and isDisabled is None and isSuspended is None):
    isDisabled = True
  if entityList is None:
    sortRows = False
    if orgUnitPath is not None and fieldsList:
      fieldsList.append('orgUnitPath')
    getIsGuestUser = not fieldsList or 'isGuestUser' in fieldsList
    if isSuspended is not None or isArchived is not None or isDisabled is not None:
      if len(kwargsDict['queries']) == 1 and kwargsDict['queries'][0] is None:
        kwargsDict['queries'][0] = ''
      if fieldsList:
        if isSuspended is not None or isDisabled is not None:
          fieldsList.extend(USER_FIELDS_CHOICE_MAP['suspended'])
        if isArchived is not None or isDisabled is not None:
          fieldsList.extend(USER_FIELDS_CHOICE_MAP['archived'])
    fields = _getMain().getItemFieldsFromFieldsList('users', fieldsList)
    itemCount = 0
    for kwargsQuery in _getMain().makeUserGroupDomainQueryFilters(kwargsDict, isSuspended, isArchived, isDisabled):
      kwargs = kwargsQuery[0]
      query  = kwargsQuery[1]
      query, pquery = _getMain().userFilters(kwargs, query, orgUnitPath)
      _getMain().printGettingAllAccountEntities(Ent.USER, pquery)
      pageMessage = _getMain().getPageMessage(showFirstLastItems=True)
      try:
        feed = _getMain().yieldGAPIpages(cd.users(), 'list', 'users',
                              pageMessage=pageMessage, messageAttribute='primaryEmail',
                              throwReasons=[GAPI.DOMAIN_NOT_FOUND, GAPI.INVALID_ORGUNIT, GAPI.INVALID_INPUT,
                                            GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN,
                                            GAPI.UNKNOWN_ERROR, GAPI.FAILED_PRECONDITION],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS+[GAPI.UNKNOWN_ERROR, GAPI.FAILED_PRECONDITION],
                              showDeleted=showDeleted, orderBy=orderBy, sortOrder=sortOrder, viewType=viewType,
                              projection=schemaParms['projection'], customFieldMask=schemaParms['customFieldMask'],
                              query=query, fields=fields,
                              maxResults=maxResults, **kwargs)
        for users in feed:
          if orgUnitPath is None:
            if showItemCountOnly:
              itemCount += len(users)
            elif not printOptions['countOnly']:
              for user in users:
                _printUser(user, 0, 0)
            else:
              for user in users:
                _updateDomainCounts(user['primaryEmail'])
          else:
            if showItemCountOnly:
              for user in users:
                if orgUnitPathLower == user.get('orgUnitPath', '').lower():
                  itemCount += 1
            elif not printOptions['countOnly']:
              for user in users:
                if orgUnitPathLower == user.get('orgUnitPath', '').lower():
                  _printUser(user, 0, 0)
            else:
              for user in users:
                if orgUnitPathLower == user.get('orgUnitPath', '').lower():
                  _updateDomainCounts(user['primaryEmail'])
      except GAPI.domainNotFound:
        _getMain().entityActionFailedWarning([Ent.USER, None, Ent.DOMAIN, kwargs['domain']], Msg.NOT_FOUND)
        continue
      except (GAPI.invalidOrgunit, GAPI.invalidInput) as e:
        if query and not schemaParms['customFieldMask']:
          _getMain().entityActionFailedWarning([Ent.USER, None], _getMain().invalidQuery(query))
        elif schemaParms['customFieldMask'] and not query:
          _getMain().entityActionFailedWarning([Ent.USER, None], _getMain().invalidUserSchema(schemaParms['customFieldMask']))
        elif query and schemaParms['customFieldMask']:
          _getMain().entityActionFailedWarning([Ent.USER, None], f'{invalidQuery(query)} or {invalidUserSchema(schemaParms["customFieldMask"])}')
        else:
          _getMain().entityActionFailedWarning([Ent.USER, None], str(e))
        continue
      except (GAPI.unknownError, GAPI.failedPrecondition) as e:
        _getMain().entityActionFailedExit([Ent.USER, None], str(e))
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        _getMain().accessErrorExit(cd)
    if showItemCountOnly:
      _getMain().writeStdout(f'{itemCount}\n')
      return
  else:
    if showItemCountOnly:
      _getMain().writeStdout(f'{len(entityList)}\n')
      return
    sortRows = True
# If no individual fields were specified (allfields, basic, full) or individual fields other than primaryEmail were specified, look up each user
    getIsGuestUser = not fieldsList or 'isGuestUser' in fieldsList
    if (isSuspended is not None or isDisabled is not None) and fieldsList:
      fieldsList.extend(USER_FIELDS_CHOICE_MAP['suspended'])
    if (isArchived is not None or isDisabled is not None) and fieldsList:
      fieldsList.extend(USER_FIELDS_CHOICE_MAP['archived'])
    if projectionSet or len(set(fieldsList)) > 1 or showValidColumn:
      jcount = len(entityList)
      fields = _getMain().getFieldsFromFieldsList(fieldsList)
      if GC.Values[GC.BATCH_SIZE] > 1 and jcount > 1:
        svcargs = dict([('userKey', None), ('fields', fields),
                        ('projection', schemaParms['projection']), ('customFieldMask', schemaParms['customFieldMask']),
                        ('viewType', viewType)]+GM.Globals[GM.EXTRA_ARGS_LIST])
        method = getattr(cd.users(), 'get')
        dbatch = cd.new_batch_http_request(callback=_callbackPrintUser)
        bcount = 0
        j = 0
        for userEntity in entityList:
          j += 1
          svcparms = svcargs.copy()
          svcparms['userKey'] = _getMain().normalizeEmailAddressOrUID(userEntity)
          dbatch.add(method(**svcparms), request_id=_getMain().batchRequestID('', 0, 0, j, jcount, svcparms['userKey']))
          bcount += 1
          if bcount >= GC.Values[GC.BATCH_SIZE]:
            _getMain().executeBatch(dbatch)
            dbatch = cd.new_batch_http_request(callback=_callbackPrintUser)
            bcount = 0
        if bcount > 0:
          dbatch.execute()
      else:
        j = 0
        for userEntity in entityList:
          j += 1
          userEmail = _getMain().normalizeEmailAddressOrUID(userEntity)
          try:
            user = _getMain().callGAPI(cd.users(), 'get',
                            throwReasons=GAPI.USER_GET_THROW_REASONS+[GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND, GAPI.RATE_LIMIT_EXCEEDED],
                            userKey=userEmail, projection=schemaParms['projection'], customFieldMask=schemaParms['customFieldMask'],
                            viewType=viewType, fields=fields)
            _printUser(user, j, jcount)
          except (GAPI.userNotFound, GAPI.resourceNotFound):
            if not showValidColumn:
              _getMain().entityUnknownWarning(Ent.USER, userEmail, j, jcount)
            else:
              _writeUserEntity({'primaryEmail': userEmail, showValidColumn: False})
          except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
                  GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.rateLimitExceeded) as e:
            _getMain().entityActionFailedWarning([Ent.USER, userEmail], str(e), j, jcount)
          except GAPI.invalidInput as e:
            if schemaParms['customFieldMask']:
              _getMain().entityActionFailedWarning([Ent.USER, userEmail], _getMain().invalidUserSchema(schemaParms['customFieldMask']), j, jcount)
            else:
              _getMain().entityActionFailedWarning([Ent.USER, userEmail], str(e), j, jcount)
# The only field specified was primaryEmail, just list the users/count the domains
    elif not printOptions['countOnly']:
      for userEntity in entityList:
        _printUser({'primaryEmail': _getMain().normalizeEmailAddressOrUID(userEntity)}, 0, 0)
    else:
      for userEntity in entityList:
        _updateDomainCounts(_getMain().normalizeEmailAddressOrUID(userEntity))
  if not printOptions['countOnly']:
    if not FJQC.formatJSON:
      if printOptions['sortHeaders']:
        sortTitles = ['primaryEmail']
        if printOptions['scalarsFirst']:
          sortTitles.extend([f'name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{field}' for field in USER_NAME_PROPERTY_PRINT_ORDER]+sorted(USER_LANGUAGE_PROPERTY_PRINT_ORDER+USER_SCALAR_PROPERTY_PRINT_ORDER))
        csvPF.SetSortTitles(sortTitles)
        csvPF.SortTitles()
        csvPF.SetSortTitles([])
      if printOptions['getGroupFeed']:
        if not printOptions['groupsInColumns']:
          csvPF.MoveTitlesToEnd(['GroupsCount', 'Groups'])
        else:
          csvPF.MoveTitlesToEnd(['Groups']+[f'Groups{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}' for j in range(printOptions['maxGroups'])])
      if printOptions['getLicenseFeed'] or printOptions['getLicenseFeedByUser']:
        csvPF.MoveTitlesToEnd(licenseTitles)
      if sortRows and orderBy:
        orderBy = 'primaryEmail' if orderBy == 'email' else f'name.{orderBy}'
        csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
    else:
      if sortRows and orderBy == 'email':
        csvPF.SortRows('primaryEmail', reverse=sortOrder == 'DESCENDING')
  elif not FJQC.formatJSON:
    for domain, count in sorted(domainCounts.items()):
      csvPF.WriteRowNoFilter({'domain': domain, 'count': count})
  else:
    csvPF.WriteRowNoFilter({'JSON': json.dumps(_getMain().cleanJSON(domainCounts), ensure_ascii=False, sort_keys=True)})
  if printOptions['countOnly']:
    csvPF.SetIndexedTitles([])
  csvPF.writeCSVfile('Users' if not printOptions['countOnly'] else 'User Domain Counts')

# gam <UserTypeEntity> print users
def doPrintUserEntity(entityList):
  if not Cmd.ArgumentsRemaining():
    _getMain().writeEntityNoHeaderCSVFile(Ent.USER, entityList)
  else:
    doPrintUsers(entityList)

# gam <UserTypeEntity> print userlist [todrive <ToDriveAttribute>*]
#	[title <String>]
#	[delimiter <Character>] [formatjson] [quotechar <Character>]
def doPrintUserList(entityList):
  csvPF = _getMain().CSVPrintFile(['title', 'count', 'users'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  title = 'Users'
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'title':
      title = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'delimiter':
      delimiter = _getMain().getCharacter()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  _, count, entityList = _getMain().getEntityArgument(entityList)
  if not FJQC.formatJSON:
    csvPF.WriteRow({'title': title, 'count': count, 'users': delimiter.join(entityList)})
  else:
    csvPF.WriteRow({'title': title, 'count': count, 'users': json.dumps(_getMain().cleanJSON(entityList), ensure_ascii=False, sort_keys=True)})
  csvPF.writeCSVfile('User List')

# gam print usercountsbyorgunit [todrive <ToDriveAttribute>*]
#	[domain <String>]
def doPrintUserCountsByOrgUnit():
  def _printUserCounts(title, v):
    csvPF.WriteRow({'orgUnitPath': title, 'archived': v['archived'], 'active': v['active'], 'suspended': v['suspended'], 'total': v['total']})

  USER_COUNTS_FIELDS = ['archived', 'active', 'suspended', 'total']
  USER_COUNTS_ZERO_FIELDS = {'archived': 0, 'active': 0, 'suspended': 0, 'total': 0}
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile(['orgUnitPath']+USER_COUNTS_FIELDS)
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  kwargs = {'customer': GC.Values[GC.CUSTOMER_ID]}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'domain':
      kwargs = {'domain': _getMain().getString(Cmd.OB_DOMAIN_NAME)}
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if 'domain' in kwargs:
    _getMain().printGettingAllEntityItemsForWhom(Ent.USER, kwargs['domain'], entityType=Ent.DOMAIN)
    pageMessage = _getMain().getPageMessageForWhom()
    title = f"Total({kwargs['domain']})"
  else:
    _getMain().printGettingAllAccountEntities(Ent.USER)
    pageMessage = _getMain().getPageMessage()
    title = f"Total({kwargs['customer']})"
  userCounts = {}
  try:
    result = _getMain().callGAPIpages(cd.users(), 'list', 'users',
                           pageMessage=pageMessage,
                           throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND, GAPI.FORBIDDEN],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                           orderBy='email', fields='nextPageToken,users(orgUnitPath,archived,suspended)',
                           maxResults=GC.Values[GC.USER_MAX_RESULTS], **kwargs)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.domainNotFound):
    if 'domain' in kwargs:
      _getMain().checkEntityDNEorAccessErrorExit(cd, Ent.DOMAIN, kwargs['domain'])
    else:
      _getMain().checkEntityDNEorAccessErrorExit(cd, Ent.CUSTOMER_ID, kwargs['customer'])
    return
  for user in result:
    orgUnitPath = user['orgUnitPath']
    if orgUnitPath not in userCounts:
      userCounts[orgUnitPath] = USER_COUNTS_ZERO_FIELDS.copy()
    if user['suspended'] or user['archived']:
      if user['archived']:
        userCounts[orgUnitPath]['archived'] += 1
      if user['suspended']:
        userCounts[orgUnitPath]['suspended'] += 1
    else:
      userCounts[orgUnitPath]['active'] += 1
    userCounts[orgUnitPath]['total'] += 1
  totalCounts = USER_COUNTS_ZERO_FIELDS.copy()
  for k, v in sorted(userCounts.items()):
    _printUserCounts(k, v)
    for f in USER_COUNTS_FIELDS:
      totalCounts[f] += v[f]
  _printUserCounts(title, totalCounts)
  csvPF.writeCSVfile('User Counts by OrgUnit')

