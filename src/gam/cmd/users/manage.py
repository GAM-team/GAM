"""User attributes, CRUD operations, schema handling.

Part of the _users_tmp sub-package."""

"""GAM user management."""

import re
import sys

from gam.util.args import DEFAULT_CHOICE

from gam.util.entity import GROUP_ROLES_MAP

from gamlib import gluprop as UProp
import base64
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
from gamlib import glskus as SKU
from gam.util.access import accessErrorExit, duplicateAliasGroupUserWarning, entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages, checkGAPIError
from gam.util.args import (
    LANGUAGE_CODES_MAP,
    SORF_MSG_FILE_ARGUMENTS,
    checkArgumentPresent,
    checkForExtraneousArguments,
    formatLocalTime,
    getArgument,
    getBoolean,
    getChoice,
    getDeliverySettings,
    getEmailAddress,
    getGoogleProduct,
    getGoogleSKUList,
    getInteger,
    getJSON,
    getREPatternSubstitution,
    getString,
    getStringOrFile,
    getStringReturnInList,
    getStringWithCRsNLs,
    getStringWithCRsNLsOrFile,
    makeOrgUnitPathAbsolute,
    normalizeEmailAddressOrUID,
    splitEmailAddress,
)
from gam.util.csv_pf import showJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityDoesNotExistWarning,
    performAction,
    printEntity,
    printEntityKVList,
    printKeyValueList,
)
from gam.util.entity import (
    convertEntityToList,
    getEntityArgument,
    getEntityList,
    getEntitySelection,
    getEntitySelector,
    getEntityToModify,
    getNormalizedEmailAddressEntity,
)
from gam.util.errors import (
    USAGE_ERROR_RC,
    csvFieldErrorExit,
    entityActionFailedExit,
    entityDoesNotExistExit,
    invalidArgumentExit,
    invalidChoiceExit,
    missingArgumentExit,
    missingChoiceExit,
    unknownArgumentExit,
    usageErrorExit,
)
from gam.util.fileio import closeFile, writeFile
from gam.util.gdoc import openCSVFileReader
from gam.util.orgunits import getOrgUnitItem
from gam.util.output import readStdin, setSysExitRC, systemErrorExit, writeStderr
from gam.constants import MULTIPLE_DELETED_USERS_FOUND_RC, NO_ENTITIES_FOUND_RC, PASSWORD_SAFE_CHARS, USER_SUSPENDED_RC
from gam.util.tags import (
    _getTagReplacement,
    _initTagReplacements,
    sendCreateUpdateUserNotification,
)

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


from secrets import SystemRandom
from passlib.hash import sha512_crypt
UTF8 = 'utf-8'
UNKNOWN = 'Unknown'


def _getGroupOrgUnitMap():

  def getKeyFieldInfo(keyword, defaultField):
    if not checkArgumentPresent(keyword):
      field = defaultField
    else:
      field = getString(Cmd.OB_FIELD_NAME)
    if field not in fieldnames:
      csvFieldErrorExit(field, fieldnames, backupArg=True)
    return field

  filename = getString(Cmd.OB_FILE_NAME)
  f, csvFile, fieldnames = openCSVFileReader(filename)
  keyField = getKeyFieldInfo('keyfield', 'Group')
  dataField = getKeyFieldInfo('datafield', 'OrgUnit')
  groupOrgUnitMap = {}
  for row in csvFile:
    group = row[keyField].strip().lower()
    orgUnit = row[dataField].strip()
    if not group or not orgUnit:
      systemErrorExit(USAGE_ERROR_RC, Msg.GROUP_MAPS_TO_OU_INVALID_ROW.format(filename, group, orgUnit))
    orgUnit = makeOrgUnitPathAbsolute(orgUnit)
    if group in groupOrgUnitMap:
      origOrgUnit = groupOrgUnitMap[group]
      if origOrgUnit != orgUnit:
        systemErrorExit(USAGE_ERROR_RC, Msg.GROUP_MAPS_TO_MULTIPLE_OUS.format(filename, group, ','.join([origOrgUnit, orgUnit])))
    groupOrgUnitMap[group] = orgUnit
  closeFile(f)
  return groupOrgUnitMap

class PasswordOptions():
  def __init__(self, updateCmd):
    self.password = ''
    self.notFoundPassword = ''
    self.b64DecryptPassword = False
    self.clearPassword = True
    self.hashPassword = True
    self.ignoreNullPassword = False
    self.makeRandomPassword = not updateCmd
    self.makeUniqueRandomPassword = False
    self.makeCleanPassword = True
    self.cleanPasswordLen = 25
    self.randomPasswordChars = None
    self.promptForPassword = False
    self.promptForUniquePassword = False
    self.notifyPasswordSet = False
    self.updateCmd = updateCmd
    self.filename = ''

  def GetPassword(self):
    return getString(Cmd.OB_PASSWORD, minLen=1 if not self.ignoreNullPassword else 0, maxLen=100)

  def SetCleanPasswordLen(self):
    self.cleanPasswordLen = getInteger(minVal=8, maxVal=100, default=25)

  def CreateRandomPassword(self):
    rnd = SystemRandom()
    if not self.makeCleanPassword:
    # Generate a password with unicode chars that are not allowed in passwords.
    # We expect "password random nohash" to fail but no one should be using that.
    # Our goal here is to purposefully block logins with this password.
      if not self.randomPasswordChars:
        self.randomPasswordChars = [chr(i) for i in range(1, 55296)]
      return ''.join(rnd.choice(self.randomPasswordChars) for _ in range(4096))
    # Generate a clean password that can be used for logins
    return ''.join(rnd.choice(PASSWORD_SAFE_CHARS) for _ in range(self.cleanPasswordLen))

  def ProcessArgument(self, myarg, notify, notFoundBody):
    if myarg == 'ignorenullpassword':
      self.ignoreNullPassword = True
    elif myarg == 'notifypassword':
      password = self.GetPassword()
      if password:
        notify['password'] = password
        self.notifyPasswordSet = True
    elif myarg == 'nohash':
      self.hashPassword = False
    elif self.updateCmd and myarg == 'notfoundpassword':
      up = 'password'
      password = self.GetPassword()
      if password:
        if password.lower() == 'blocklogin':
          self.makeCleanPassword = False
          notFoundBody[up] = self.CreateRandomPassword()
        elif password.lower() in {'random', 'uniquerandom'}:
          self.SetCleanPasswordLen()
          self.makeCleanPassword = True
          notFoundBody[up] = self.CreateRandomPassword()
        else:
          notFoundBody[up] = password
        self.notFoundPassword = notFoundBody[up]
    elif myarg in {'lograndompassword', 'logpassword'}:
      self.filename = getString(Cmd.OB_FILE_NAME)
    else:
      return False
    return True

  HASH_FUNCTION_MAP = {
    'base64-md5': 'MD5',
    'base64-sha1': 'SHA-1',
    'crypt': 'crypt',
    'md5': 'MD5',
    'sha': 'SHA-1',
    'sha-1': 'SHA-1',
    'sha1': 'SHA-1',
    }

  def ProcessPropertyArgument(self, myarg, up, body):
    if up == 'password':
      password = self.GetPassword()
      if password:
        body[up] = password
        self.makeRandomPassword = self.makeUniqueRandomPassword =\
          self.promptForPassword = self.promptForUniquePassword = False
        if password.lower() == 'blocklogin':
          self.makeRandomPassword = True
          self.makeCleanPassword = False
        elif password.lower() == 'random':
          self.SetCleanPasswordLen()
          self.makeRandomPassword = self.makeCleanPassword = True
        elif password.lower() == 'uniquerandom':
          self.SetCleanPasswordLen()
          if self.updateCmd:
            self.makeUniqueRandomPassword = self.makeCleanPassword = True
          else:
            self.makeRandomPassword = self.makeCleanPassword = True
        elif password.lower() == 'prompt':
          self.promptForPassword = True
        elif password.lower() == 'uniqueprompt':
          if self.updateCmd:
            self.promptForUniquePassword = True
          else:
            self.promptForPassword = True
        else:
          self.password = password
    elif up == 'hashFunction':
      body[up] = self.HASH_FUNCTION_MAP[myarg]
      self.clearPassword = self.hashPassword = False
      self.b64DecryptPassword = myarg.startswith('base64')
    else:
      return False
    return True

  def FinalizePassword(self, body, notify, up):
    if not self.notifyPasswordSet:
      notify[up] = body[up] if self.clearPassword else Msg.CONTACT_ADMINISTRATOR_FOR_PASSWORD
    if self.hashPassword:
      body[up] = sha512_crypt.hash(body[up], rounds=10000)
      body['hashFunction'] = 'crypt'
    elif self.b64DecryptPassword:
      if body[up].lower()[:5] in ['{md5}', '{sha}']:
        body[up] = body[up][5:]
      try:
        body[up] = base64.b64decode(body[up]).hex()
      except Exception:
        pass

  def AssignPassword(self, body, notify, notFoundBody, createIfNotFound, user=None):
    up = 'password'
    if self.makeRandomPassword or self.makeUniqueRandomPassword:
      body[up] = self.CreateRandomPassword()
      self.password = body[up]
    elif user and (self.promptForPassword or self.promptForUniquePassword):
      body[up] = readStdin(f'Enter password for {user}: ')
      self.password = body[up]
    elif self.promptForPassword:
      body[up] = readStdin('Enter password: ')
      self.password = body[up]
    if up in body:
      self.FinalizePassword(body, notify, up)
    elif 'hashFunction' in body:
      body.pop('hashFunction')
    if createIfNotFound:
      if not notFoundBody:
        if up in body:
          notFoundBody[up] = body[up]
          if 'hashfunction' in body:
            notFoundBody['hashfunction'] = body['hashFunction']
          notify['notFoundPassword'] = notify[up]
          self.notFoundPassword = self.password
      else:
        notify['notFoundPassword'] = notify[up] if notify[up] else notFoundBody[up] if self.clearPassword else Msg.CONTACT_ADMINISTRATOR_FOR_PASSWORD
        self.FinalizePassword(notFoundBody, notify, up)

UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP = {
  'address': 'addresses',
  'addresses': 'addresses',
  'archive': 'archived',
  'archived': 'archived',
  'base64-md5': 'hashFunction',
  'base64-sha1': 'hashFunction',
  'changepassword': 'changePasswordAtNextLogin',
  'changepasswordatnextlogin': 'changePasswordAtNextLogin',
  'crypt': 'hashFunction',
  'customerid': 'customerId',
  'displayname': 'displayName',
  'email': 'primaryEmail',
  'emails': 'emails',
  'externalid': 'externalIds',
  'externalids': 'externalIds',
  'familyname': 'familyName',
  'firstname': 'givenName',
  'gal': 'includeInGlobalAddressList',
  'gender': 'gender',
  'givenname': 'givenName',
  'im': 'ims',
  'ims': 'ims',
  'includeinglobaladdresslist': 'includeInGlobalAddressList',
  'ipwhitelisted': 'ipWhitelisted',
  'keyword': 'keywords',
  'keywords': 'keywords',
  'language': 'languages',
  'languages': 'languages',
  'lastname': 'familyName',
  'location': 'locations',
  'locations': 'locations',
  'md5': 'hashFunction',
  'note': 'notes',
  'notes': 'notes',
  'org': 'orgUnitPath',
  'organization': 'organizations',
  'organizations': 'organizations',
  'organisation': 'organizations',
  'organisations': 'organizations',
  'orgunitpath': 'orgUnitPath',
  'otheremail': 'emails',
  'otheremails': 'emails',
  'ou': 'orgUnitPath',
  'password': 'password',
  'phone': 'phones',
  'phones': 'phones',
  'posix': 'posixAccounts',
  'posixaccounts': 'posixAccounts',
  'primaryemail': 'primaryEmail',
  'recoveryemail': 'recoveryEmail',
  'recoveryphone': 'recoveryPhone',
  'relation': 'relations',
  'relations': 'relations',
  'sha': 'hashFunction',
  'sha-1': 'hashFunction',
  'sha1': 'hashFunction',
  'ssh': 'sshPublicKeys',
  'sshkeys': 'sshPublicKeys',
  'sshpublickeys': 'sshPublicKeys',
  'suspend': 'suspended',
  'suspended': 'suspended',
  'username': 'primaryEmail',
  'website': 'websites',
  'websites': 'websites',
  }

ADDRESS_ARGUMENT_TO_FIELD_MAP = {
  'country': 'country',
  'countrycode': 'countryCode',
  'extendedaddress': 'extendedAddress',
  'locality': 'locality',
  'pobox': 'poBox',
  'postalcode': 'postalCode',
  'region': 'region',
  'streetaddress': 'streetAddress',
  }

ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
  'costcenter': 'costCenter',
  'costcentre': 'costCenter',
  'department': 'department',
  'description': 'description',
  'domain': 'domain',
  'fulltimeequivalent': 'fullTimeEquivalent',
  'location': 'location',
  'name': 'name',
  'symbol': 'symbol',
  'title': 'title',
  }

# (MultiValue, IgnoreEmpty)
SCHEMA_VALUE_PROCESS_MAP = {
  'multivalued': (True, False),
  'multivalue': (True, False),
  'value': (True, False),
  'multinonempty': (True, True),
  'scalarnonempty': (False, True)
  }

USER_JSON_SKIP_FIELDS = ['agreedToTerms', 'aliases', 'creationTime', 'customerId', 'deletionTime', 'groups', 'id',
                         'isAdmin', 'isDelegatedAdmin', 'isEnforcedIn2Sv', 'isEnrolledIn2Sv', 'isMailboxSetup',
                         'lastLoginTime', 'licenses', 'primaryEmail', 'thumbnailPhotoEtag', 'thumbnailPhotoUrl',
                         'ipWhiteListed', 'posixAccounts', 'suspensionReason', 'nonEditableAliases']

ALLOW_EMPTY_CUSTOM_TYPE = 'allowEmptyCustomType'

def getNotifyArguments(myarg, notify, userNotification):
  if myarg == 'notify':
    if userNotification:
      notify['recipients'].extend(getNormalizedEmailAddressEntity(shlexSplit=True, noLower=True))
    else: #delegateNotificatiomn
      notify['notify'] = getBoolean()
  elif myarg == 'subject':
    notify['subject'] = getString(Cmd.OB_STRING)
  elif myarg in SORF_MSG_FILE_ARGUMENTS:
    notify['message'], notify['charset'], notify['html'] = getStringOrFile(myarg)
  elif myarg == 'html':
    notify['html'] = getBoolean()
  elif myarg == 'from':
    notify['from'] = getString(Cmd.OB_EMAIL_ADDRESS)
  elif myarg == 'mailbox':
    notify['mailbox'] = getString(Cmd.OB_EMAIL_ADDRESS)
  elif myarg == 'replyto':
    notify['replyto'] = getString(Cmd.OB_EMAIL_ADDRESS)
  else:
    return False
  return True

def getUserAttributes(cd, updateCmd, noUid=False):
  from gam.cmd.resources import _getBuildingByNameOrId
  from gam.cmd.userop.usergroups import LICENSE_PRODUCT_SKUIDS
  def getKeywordAttribute(keywords, attrdict, **opts):
    if Cmd.ArgumentsRemaining():
      keyword = Cmd.Current().strip().lower()
      if keyword in keywords[UProp.PTKW_KEYWORD_LIST]:
        Cmd.Advance()
        if keyword != keywords[UProp.PTKW_CL_CUSTOM_KEYWORD]:
          attrdict[keywords[UProp.PTKW_ATTR_TYPE_KEYWORD]] = keyword
          attrdict.pop(keywords[UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD], None)
          return
        if Cmd.ArgumentsRemaining():
          customType = Cmd.Current().strip()
          if customType or opts.get(ALLOW_EMPTY_CUSTOM_TYPE, False):
            Cmd.Advance()
            if keywords[UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]:
              attrdict[keywords[UProp.PTKW_ATTR_TYPE_KEYWORD]] = keywords[UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]
            else:
              attrdict.pop(keywords[UProp.PTKW_ATTR_TYPE_KEYWORD], None)
            attrdict[keywords[UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = customType
            return
        missingArgumentExit('custom attribute type')
      elif DEFAULT_CHOICE in opts:
        attrdict[keywords[UProp.PTKW_ATTR_TYPE_KEYWORD]] = opts[DEFAULT_CHOICE]
        return
      elif keywords[UProp.PTKW_CL_CUSTOM_KEYWORD]:
        if keywords[UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]:
          attrdict[keywords[UProp.PTKW_ATTR_TYPE_KEYWORD]] = keywords[UProp.PTKW_ATTR_TYPE_CUSTOM_VALUE]
        else:
          attrdict.pop(keywords[UProp.PTKW_ATTR_TYPE_KEYWORD], None)
        attrdict[keywords[UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = Cmd.Current()
        Cmd.Advance()
        return
      invalidChoiceExit(keyword, keywords[UProp.PTKW_KEYWORD_LIST], False)
    elif DEFAULT_CHOICE in opts:
      attrdict[keywords[UProp.PTKW_ATTR_TYPE_KEYWORD]] = opts[DEFAULT_CHOICE]
      return
    missingChoiceExit(keywords[UProp.PTKW_KEYWORD_LIST])

  def primaryNotPrimary(pnp, entry):
    if pnp == 'notprimary':
      return True
    if pnp == 'primary':
      entry['primary'] = True
      primary['location'] = Cmd.Location()
      return True
    return False

  def getPrimaryNotPrimaryChoice(entry, defaultChoice):
    if getChoice({'primary': True, 'notprimary': False}, defaultChoice=defaultChoice, mapChoice=True):
      entry['primary'] = True
      primary['location'] = Cmd.Location()

  def checkClearBodyList(body, itemName):
    if checkArgumentPresent(Cmd.CLEAR_NONE_ARGUMENT):
      body.pop(itemName, None)
      body[itemName] = None
      return True
    return False

  def appendItemToBodyList(body, itemName, itemValue, checkBlankField=None, checkSystemId=False):
    if (itemName in body) and (body[itemName] is None):
      del body[itemName]
    body.setdefault(itemName, [])
    if checkBlankField is None or itemValue[checkBlankField]:
# Throw an error if multiple items are marked primary
      if itemValue.get('primary', False):
        for citem in body[itemName]:
          if citem.get('primary', False):
            if not checkSystemId or itemValue.get('systemId') == citem.get('systemId'):
              Cmd.SetLocation(primary['location']-1)
              usageErrorExit(Msg.MULTIPLE_ITEMS_MARKED_PRIMARY.format(itemName))
      body[itemName].append(itemValue)

  def _splitSchemaNameDotFieldName(sn_fn, fnRequired=True):
    if sn_fn.find('.') != -1:
      schemaName, fieldName = sn_fn.split('.', 1)
      schemaName = schemaName.strip()
      fieldName = fieldName.strip()
      if schemaName and fieldName:
        return (schemaName, fieldName)
    elif not fnRequired:
      schemaName = sn_fn.strip()
      if schemaName:
        return (schemaName, None)
    invalidArgumentExit(Cmd.OB_SCHEMA_NAME_FIELD_NAME)

  parameters = {
    'notifyRecoveryEmail': False,
    'verifyNotInvitable': False,
    'createIfNotFound': False,
    'noActionIfAlias': False,
    'notifyOnUpdate': True,
    'setChangePasswordOnCreate': False,
    'immutableOUs': set(),
    'addNumericSuffixOnDuplicate': 0,
    'lic': None,
    LICENSE_PRODUCT_SKUIDS: [],
    }
  if updateCmd:
    body = {}
  else:
    body = {'name': {'givenName': UNKNOWN, 'familyName': UNKNOWN}}
    body['primaryEmail'] = getEmailAddress(noUid=noUid)
  notFoundBody = {}
  notify = {'recipients': [], 'subject': '', 'message': '', 'html': False, 'charset': UTF8, 'password': ''}
  primary = {}
  updatePrimaryEmail = []
  groupOrgUnitMap = None
  tagReplacements = _initTagReplacements()
  addGroups = {}
  addAliases = []
  PwdOpts = PasswordOptions(updateCmd)
  resolveConflictAccount = True
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getNotifyArguments(myarg, notify, True):
      pass
    elif myarg == 'notifyrecoveryemail':
      parameters['notifyRecoveryEmail'] = True
    elif PwdOpts.ProcessArgument(myarg, notify, notFoundBody):
      pass
    elif _getTagReplacement(myarg, tagReplacements, True):
      pass
    elif myarg == 'admin':
      value = getBoolean()
      if updateCmd or value:
        Cmd.Backup()
        unknownArgumentExit()
    elif myarg == 'verifynotinvitable':
      parameters['verifyNotInvitable'] = True
    elif myarg == 'alwaysevict':
      resolveConflictAccount = False
    elif updateCmd and myarg == 'createifnotfound':
      parameters['createIfNotFound'] = True
    elif updateCmd and myarg == 'noactionifalias':
      parameters['noActionIfAlias'] = True
    elif updateCmd and myarg == 'notifyonupdate':
      parameters['notifyOnUpdate'] = getBoolean()
    elif updateCmd and myarg == 'setchangepasswordoncreate':
      parameters['setChangePasswordOnCreate'] = getBoolean()
    elif updateCmd and myarg in {'immutableous', 'immutableorgs', 'immutableorgunitpaths'}:
      parameters['immutableOUs'] = set(getEntityList(Cmd.OB_ORGUNIT_ENTITY, shlexSplit=True))
    elif not updateCmd and myarg == 'addnumericsuffixonduplicate':
      parameters['addNumericSuffixOnDuplicate'] = getInteger(minVal=0, default=0)
    elif not updateCmd and myarg in {'license', 'licence', 'licenses', 'licences'}:
      if parameters['lic'] is None:
        parameters['lic'] = buildGAPIObject(API.LICENSING)
      parameters[LICENSE_PRODUCT_SKUIDS] = getGoogleSKUList(allowUnknownProduct=True)
      if checkArgumentPresent(['product', 'productid']):
        productId = getGoogleProduct()
        for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
          productSku = (productId, productSku[1])
      for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
        if not productSku[0]:
          invalidChoiceExit(productSku[1], SKU.getSortedSKUList(), True)
    elif updateCmd and myarg == 'updateoufromgroup':
      groupOrgUnitMap = _getGroupOrgUnitMap()
    elif updateCmd and myarg == 'updateprimaryemail':
      updatePrimaryEmail = list(getREPatternSubstitution(re.IGNORECASE))
      updatePrimaryEmail.append(checkArgumentPresent(['preview']))
#    elif updateCmd and myarg == 'primaryguestemail':
#      body['guestAccountInfo'] = {'primaryGuestEmail': getEmailAddress(noUid=True)}
    elif myarg == 'json':
      body.update(getJSON(USER_JSON_SKIP_FIELDS))
      if 'name' in body and 'fullName' in body['name']:
        body['name'].pop('fullName')
      if 'sshPublicKeys' in body and 'fingerprint' in body['sshPublicKeys']:
        body['sshPublicKeys'].pop('fingerprint')
      for location in body.get('locations', []):
        location.pop('buildingName', None)
    elif myarg == 'employeeid':
      entry = {'type': 'organization', 'value': getString(Cmd.OB_STRING, minLen=0)}
      appendItemToBodyList(body, 'externalIds', entry, 'value')
    elif myarg == 'manager':
      entry = {'type': 'manager', 'value': getString(Cmd.OB_STRING, minLen=0)}
      appendItemToBodyList(body, 'relations', entry, 'value')
    elif myarg in UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP:
      up = UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP[myarg]
      userProperty = UProp.PROPERTIES[up]
      propertyClass = userProperty[UProp.CLASS]
      if UProp.TYPE_KEYWORDS in userProperty:
        typeKeywords = userProperty[UProp.TYPE_KEYWORDS]
        clTypeKeyword = typeKeywords[UProp.PTKW_CL_TYPE_KEYWORD]
      if up == 'givenName':
        body.setdefault('name', {})
        body['name'][up] = getString(Cmd.OB_STRING, minLen=0, maxLen=60)
      elif up == 'familyName':
        body.setdefault('name', {})
        body['name'][up] = getString(Cmd.OB_STRING, minLen=0, maxLen=60)
      elif up == 'displayName':
        body.setdefault('name', {})
        body['name']['displayName'] = getString(Cmd.OB_STRING, minLen=0, maxLen=256)
      elif PwdOpts.ProcessPropertyArgument(myarg, up, body):
        pass
      elif propertyClass == UProp.PC_BOOLEAN:
        body[up] = getBoolean()
      elif up == 'primaryEmail':
        if updateCmd:
          body[up] = getEmailAddress(noUid=True)
        elif body[up] != getEmailAddress(noUid=True):
          Cmd.Backup()
          unknownArgumentExit()
      elif up == 'recoveryEmail':
        rcvryEmail = getEmailAddress(noUid=True, optional=True)
        body[up] = rcvryEmail if rcvryEmail is not None else ""
      elif up == 'recoveryPhone':
        body[up] = getString(Cmd.OB_STRING, minLen=0)
        if body[up] and body[up][0] != '+':
          body[up] = '+' + body[up]
      elif up == 'customerId':
        body[up] = getString(Cmd.OB_STRING)
      elif up == 'orgUnitPath':
        body[up] = getOrgUnitItem(pathOnly=True, cd=cd)
      elif up == 'languages':
        if checkClearBodyList(body, up):
          continue
        for language in getString(Cmd.OB_LANGUAGE_LIST).replace('_', '-').replace(',', ' ').split():
          langItem = {}
          if language[-1] == '+':
            suffix = '+'
            language = language[:-1]
            langItem['preference'] = 'preferred'
          elif language[-1] == '-':
            suffix = '-'
            language = language[:-1]
            langItem['preference'] = 'not_preferred'
          else:
            suffix = ''
          if language.lower() in LANGUAGE_CODES_MAP:
            langItem['languageCode'] = LANGUAGE_CODES_MAP[language.lower()]
          else:
            if suffix:
              Cmd.Backup()
              usageErrorExit(Msg.SUFFIX_NOT_ALLOWED_WITH_CUSTOMLANGUAGE.format(suffix, language))
            langItem['customLanguage'] = language
          appendItemToBodyList(body, up, langItem)
      elif up == 'gender':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        if checkArgumentPresent('addressmeas'):
          entry['addressMeAs'] = getString(Cmd.OB_STRING, minLen=0)
        body[up] = entry
      elif up == 'addresses':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        if checkArgumentPresent(['unstructured', 'formatted']):
          entry['sourceIsStructured'] = False
          entry['formatted'] = getStringWithCRsNLs()
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument in ADDRESS_ARGUMENT_TO_FIELD_MAP:
            value = getString(Cmd.OB_STRING, minLen=0)
            if value:
              entry[ADDRESS_ARGUMENT_TO_FIELD_MAP[argument]] = value
          elif primaryNotPrimary(argument, entry):
            break
          else:
            unknownArgumentExit()
        appendItemToBodyList(body, up, entry)
      elif up == 'ims':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        getChoice([UProp.IM_PROTOCOLS[UProp.PTKW_CL_TYPE_KEYWORD]])
        getKeywordAttribute(UProp.IM_PROTOCOLS, entry)
        # Backwards compatability: notprimary|primary on either side of IM address
        getPrimaryNotPrimaryChoice(entry, False)
        entry['im'] = getString(Cmd.OB_STRING, minLen=0)
        getPrimaryNotPrimaryChoice(entry, entry.get('primary', False))
        appendItemToBodyList(body, up, entry, 'im')
      elif up == 'keywords':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        appendItemToBodyList(body, up, entry, 'value')
      elif up == 'locations':
        if checkClearBodyList(body, up):
          continue
        entry = {'type': 'desk'}
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument == clTypeKeyword:
            getKeywordAttribute(typeKeywords, entry)
          elif argument == 'area':
            entry['area'] = getString(Cmd.OB_STRING)
          elif argument in {'building', 'buildingid'}:
            entry['buildingId'] = _getBuildingByNameOrId(cd, allowNV=True)
          elif argument in {'floor', 'floorname'}:
            entry['floorName'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument in {'section', 'floorsection'}:
            entry['floorSection'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument in {'desk', 'deskcode'}:
            entry['deskCode'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument == 'endlocation':
            break
          else:
            unknownArgumentExit()
        if 'area' not in entry:
          missingArgumentExit('area <String>')
        appendItemToBodyList(body, up, entry)
      elif up == 'notes':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getKeywordAttribute(typeKeywords, entry, defaultChoice='text_plain')
        entry['value'] = getStringWithCRsNLsOrFile()[0]
        body[up] = entry
      elif up == 'organizations':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument == clTypeKeyword:
            getKeywordAttribute(typeKeywords, entry)
          elif argument == typeKeywords[UProp.PTKW_CL_CUSTOMTYPE_KEYWORD]:
            entry[typeKeywords[UProp.PTKW_ATTR_CUSTOMTYPE_KEYWORD]] = getString(Cmd.OB_STRING, minLen=0)
            entry.pop(typeKeywords[UProp.PTKW_ATTR_TYPE_KEYWORD], None)
          elif argument in ORGANIZATION_ARGUMENT_TO_FIELD_MAP:
            argument = ORGANIZATION_ARGUMENT_TO_FIELD_MAP[argument]
            if argument != 'fullTimeEquivalent':
              value = getString(Cmd.OB_STRING, minLen=0)
              if value:
                entry[argument] = value
            else:
              entry[argument] = getInteger(minVal=0, maxVal=100000, default=0)
          elif primaryNotPrimary(argument, entry):
            break
          else:
            unknownArgumentExit()
        appendItemToBodyList(body, up, entry)
      elif up == 'phones':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument == clTypeKeyword:
            getKeywordAttribute(typeKeywords, entry)
          elif argument == 'value':
            entry['value'] = getString(Cmd.OB_STRING, minLen=0)
          elif primaryNotPrimary(argument, entry):
            break
          else:
            unknownArgumentExit()
        appendItemToBodyList(body, up, entry, 'value')
      elif up == 'posixAccounts':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument in {'username', 'name'}:
            entry['username'] = getString(Cmd.OB_STRING)
          elif argument == 'uid':
            entry['uid'] = getInteger(minVal=1000)
          elif argument == 'gid':
            entry['gid'] = getInteger(minVal=0)
          elif argument in {'system', 'systemid'}:
            entry['systemId'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument in {'home', 'homedirectory'}:
            entry['homeDirectory'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument == 'shell':
            entry['shell'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument == 'gecos':
            entry['gecos'] = getString(Cmd.OB_STRING, minLen=0)
          elif argument == 'primary':
            primary['location'] = Cmd.Location()
            entry['primary'] = getBoolean()
          elif argument in {'os', 'operatingsystemtype'}:
            entry['operatingSystemType'] = getChoice(['linux', 'unspecified', 'windows'])
          elif argument == 'endposix':
            break
          else:
            unknownArgumentExit()
        if 'username' not in entry:
          missingArgumentExit('username <String>')
        if 'uid' not in entry:
          missingArgumentExit('uid <Integer>')
        appendItemToBodyList(body, up, entry, checkSystemId=True)
      elif up == 'relations':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        appendItemToBodyList(body, up, entry, 'value')
      elif up == 'emails':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        entry['address'] = getEmailAddress(noUid=True, minLen=0)
        appendItemToBodyList(body, up, entry, 'address')
      elif up == 'sshPublicKeys':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        while Cmd.ArgumentsRemaining():
          argument = getArgument()
          if argument == 'expires':
            entry['expirationTimeUsec'] = getInteger(minVal=0)
          elif argument == 'key':
            entry['key'] = getString(Cmd.OB_STRING)
          elif argument == 'endssh':
            break
          else:
            unknownArgumentExit()
        if 'key' not in entry:
          missingArgumentExit('key <String>')
        appendItemToBodyList(body, up, entry)
      elif up == 'externalIds':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry, allowEmptyCustomType=True)
        entry['value'] = getString(Cmd.OB_STRING, minLen=0)
        appendItemToBodyList(body, up, entry, 'value')
      elif up == 'websites':
        if checkClearBodyList(body, up):
          continue
        entry = {}
        getChoice([clTypeKeyword], defaultChoice=None)
        getKeywordAttribute(typeKeywords, entry)
        entry['value'] = getString(Cmd.OB_URL, minLen=0)
        getPrimaryNotPrimaryChoice(entry, False)
        appendItemToBodyList(body, up, entry, 'value')
    elif myarg in {'group', 'groups'}:
      role = getChoice(GROUP_ROLES_MAP, defaultChoice=Ent.ROLE_MEMBER, mapChoice=True)
      delivery_settings = getDeliverySettings()
      for group in getEntityList(Cmd.OB_GROUP_ENTITY):
        addGroups[normalizeEmailAddressOrUID(group)] = {'role': role, 'delivery_settings': delivery_settings}
    elif myarg in {'alias', 'aliases'}:
      addAliases.extend(convertEntityToList(getString(Cmd.OB_EMAIL_ADDRESS_LIST, minLen=0)))
    elif myarg == 'clearschema':
      if not updateCmd:
        unknownArgumentExit()
      schemaName, fieldName = _splitSchemaNameDotFieldName(getString(Cmd.OB_SCHEMA_NAME_FIELD_NAME), False)
      up = 'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      if fieldName is None:
        try:
          schema = callGAPI(cd.schemas(), 'get',
                            throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                            customerId=GC.Values[GC.CUSTOMER_ID], schemaKey=schemaName, fields='fields(fieldName)')
          for field in schema['fields']:
            body[up][schemaName][field['fieldName']] = None
        except (GAPI.invalid, GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
          entityDoesNotExistWarning(Ent.USER_SCHEMA, schemaName)
          unknownArgumentExit()
      else:
        body[up][schemaName][fieldName] = None
    elif myarg.find('.') >= 0:
      schemaName, fieldName = _splitSchemaNameDotFieldName(Cmd.Previous())
      up = 'customSchemas'
      body.setdefault(up, {})
      body[up].setdefault(schemaName, {})
      multivalue, ignoreEmpty = getChoice(SCHEMA_VALUE_PROCESS_MAP, defaultChoice=(False, False), mapChoice=True)
      if multivalue:
        body[up][schemaName].setdefault(fieldName, [])
        typeKeywords = UProp.PROPERTIES[up][UProp.TYPE_KEYWORDS]
        clTypeKeyword = typeKeywords[UProp.PTKW_CL_TYPE_KEYWORD]
        schemaValue = {}
        if checkArgumentPresent(clTypeKeyword):
          getKeywordAttribute(typeKeywords, schemaValue)
        else:
          schemaValue['type'] = 'work'
        schemaValue['value'] = getString(Cmd.OB_STRING, minLen=0)
        if schemaValue['value'] or not ignoreEmpty:
          body[up][schemaName][fieldName].append(schemaValue)
      else:
        schemaValue = getString(Cmd.OB_STRING, minLen=0)
        if schemaValue or not ignoreEmpty:
          body[up][schemaName][fieldName] = schemaValue
        elif updateCmd:
          body[up][schemaName][fieldName] = None
    else:
      unknownArgumentExit()
  if PwdOpts.promptForPassword or PwdOpts.promptForUniquePassword:
    if not updateCmd:
      PwdOpts.AssignPassword(body, notify, notFoundBody, parameters['createIfNotFound'], body['primaryEmail'])
    elif not PwdOpts.promptForUniquePassword:
      PwdOpts.AssignPassword(body, notify, notFoundBody, parameters['createIfNotFound'])
  elif not PwdOpts.makeUniqueRandomPassword:
    PwdOpts.AssignPassword(body, notify, notFoundBody, parameters['createIfNotFound'])
  return (body, notify, tagReplacements, addGroups, addAliases, PwdOpts,
          updatePrimaryEmail, notFoundBody, groupOrgUnitMap, parameters,
          resolveConflictAccount)

def createUserAddToGroups(cd, user, addGroups, i, count):
  from gam.cmd.userop.usergroups import _addUserToGroups
  action = Act.Get()
  Act.Set(Act.ADD)
  Ind.Increment()
  _addUserToGroups(cd, user, set(addGroups), addGroups, i, count)
  Ind.Decrement()
  Act.Set(action)

def createUserAddAliases(cd, user, aliasList, i, count):
  from gam.cmd.aliases import _addUserAliases
  action = Act.Get()
  Act.Set(Act.ADD)
  Ind.Increment()
  _addUserAliases(cd, user, aliasList, i, count)
  Ind.Decrement()
  Act.Set(action)

# gam create user <EmailAddress> <UserAttribute>
#	[verifynotinvitable|alwaysevict]
#	(groups [<GroupRole>] [[delivery] <DeliverySetting>] <GroupEntity>)*
#	[alias|aliases <EmailAddressList>]
#	[license <SKUID> [product|productid <ProductID>]]
#	[[notify <EmailAddressList>] [notifyrecoveryemail]
#	    [subject <String>]
#	    [from <EmailAaddress>] [mailbox <EmailAddress>]
#	    [replyto <EmailAaddress>]
#	    [notifypassword <String>]
#	    [<NotifyMessageContent>] [html [<Boolean>]]
#	        (replace <Tag> <UserReplacement>)*
#	        (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
#	[logpassword <FileName>] [ignorenullpassword]
#	[addnumericsuffixonduplicate <Number>]
def doCreateUser():
  from gam.cmd.ciuserinvitations import _getIsInvitableUser
  from gam.cmd.userop.usergroups import LICENSE_PRODUCT_SKUIDS
  cd = buildGAPIObject(API.DIRECTORY)
  body, notify, tagReplacements, addGroups, addAliases, PwdOpts, \
    _, _, _, \
    parameters, resolveConflictAccount = getUserAttributes(cd, False, noUid=True)
  suffix = 0
  originalEmail = body['primaryEmail']
  atLoc = originalEmail.find('@')
  fields = '*' if tagReplacements['subs'] else 'primaryEmail,name,recoveryEmail'
  while True:
    user = body['primaryEmail']
    if parameters['verifyNotInvitable']:
      isInvitableUser, _ = _getIsInvitableUser(None, user)
      if isInvitableUser:
        entityActionNotPerformedWarning([Ent.USER, user], Msg.EMAIL_ADDRESS_IS_UNMANAGED_ACCOUNT)
        return
    try:
      result = callGAPI(cd.users(), 'insert',
                        throwReasons=[GAPI.DUPLICATE, GAPI.DOMAIN_NOT_FOUND,
                                      GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.FORBIDDEN,
                                      GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.INVALID_PARAMETER,
                                      GAPI.INVALID_ORGUNIT, GAPI.INVALID_SCHEMA_VALUE, GAPI.CONDITION_NOT_MET,
                                      GAPI.LIMIT_EXCEEDED],
                        body=body,
                        fields=fields,
                        resolveConflictAccount=resolveConflictAccount)
      entityActionPerformed([Ent.USER, user])
      break
    except GAPI.duplicate:
      if duplicateAliasGroupUserWarning(cd, [Ent.USER, user]) == Ent.USER and parameters['addNumericSuffixOnDuplicate'] > 0:
        parameters['addNumericSuffixOnDuplicate'] -= 1
        suffix +=1
        body['primaryEmail'] = originalEmail[0:atLoc]+str(suffix)+originalEmail[atLoc:]
        setSysExitRC(0)
        continue
      return
    except GAPI.invalidSchemaValue:
      entityActionFailedExit([Ent.USER, user], Msg.INVALID_SCHEMA_VALUE)
    except GAPI.invalidOrgunit:
      entityActionFailedExit([Ent.USER, user], Msg.INVALID_ORGUNIT)
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.invalid, GAPI.invalidInput, GAPI.invalidParameter, GAPI.conditionNotMet, GAPI.limitExceeded) as e:
      entityActionFailedExit([Ent.USER, user], str(e))
  if PwdOpts.filename and PwdOpts.password:
    writeFile(PwdOpts.filename, f'{user},{PwdOpts.password}\n', mode='a', continueOnError=True)
  if addGroups:
    createUserAddToGroups(cd, result['primaryEmail'], addGroups, 0, 0)
  if addAliases:
    createUserAddAliases(cd, result['primaryEmail'], addAliases, 0, 0)
  if (notify.get('recipients') or (parameters['notifyRecoveryEmail'] and result.get('recoveryEmail'))):
    if parameters['notifyRecoveryEmail'] and result.get('recoveryEmail'):
      notify['recipients'].append(result['recoveryEmail'])
    sendCreateUpdateUserNotification(result, notify, tagReplacements)
  for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
    productId = productSku[0]
    skuId = productSku[1]
    try:
      callGAPI(parameters['lic'].licenseAssignments(), 'insert',
               throwReasons=[GAPI.INTERNAL_ERROR, GAPI.DUPLICATE, GAPI.CONDITION_NOT_MET, GAPI.INVALID,
                             GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               productId=productId, skuId=skuId, body={'userId': user}, fields='')
      entityActionPerformed([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)])
    except (GAPI.internalError, GAPI.duplicate, GAPI.conditionNotMet, GAPI.invalid,
            GAPI.userNotFound, GAPI.forbidden, GAPI.backendError, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], str(e))

def verifyUserPrimaryEmail(cd, user, createIfNotFound, i, count):
  try:
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=user, fields='id,primaryEmail')
    if (result['primaryEmail'].lower() == user) or (result['id'] == user):
      return True
    entityActionNotPerformedWarning([Ent.USER, user], Msg.NOT_A_PRIMARY_EMAIL_ADDRESS, i, count)
    return False
  except GAPI.userNotFound:
    if createIfNotFound:
      return True
  except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    pass
  entityUnknownWarning(Ent.USER, user, i, count)
  return False

# gam create guestuser <EmailAddress>
def doCreateGuestUser():
  cd = buildGAPIObject(API.DIRECTORY)
  body = {'primaryGuestEmail':  getEmailAddress(noUid=True),
          'customer': GC.Values[GC.CUSTOMER_ID]}
  checkForExtraneousArguments()
  try:
    result = callGAPI(cd.users(), 'createGuest',
                      throwReasons=[GAPI.FAILED_PRECONDITION, GAPI.INVALID_ARGUMENT],
                      body=body)
    entityActionPerformed([Ent.GUEST_USER, body['primaryGuestEmail']])
    Ind.Increment()
    showJSON(None, result)
    Ind.Decrement()
  except (GAPI.failedPrecondition, GAPI.invalidArgument) as e:
    entityActionFailedExit([Ent.GUEST_USER, body['primaryGuestEmail']], str(e))

# gam <UserTypeEntity> update user <UserAttribute>*
#	[verifynotinvitable|alwaysevict] [noactionifalias]
#	[updateprimaryemail <RESEarchPattern> <RESubstitution> [preview]]
#	[updateoufromgroup <CSVFileInput> [keyfield <FieldName>] [datafield <FieldName>]]
#	[immutableous <OrgUnitEntity>]|
#	[clearschema <SchemaName>|<SchemaNameField>]
#	[createifnotfound] [notfoundpassword (random [<Integer>])|blocklogin|<Password>]
#	(groups [<GroupRole>] [[delivery] <DeliverySetting>] <GroupEntity>)*
#	[alias|aliases <EmailAddressList>]
#	[[notify <EmailAddressList>] [notifyrecoveryemail]
#	    [subject <String>]
#	    [from <EmailAaddress>] [mailbox <EmailAddress>]
#	    [replyto <EmailAaddress>]
#	    [<NotifyMessageContent> [html [<Boolean>]]
#	        (replace <Tag> <UserReplacement>)*
#	        (replaceregex <REMatchPattern> <RESubstitution> <Tag> <UserReplacement>)*]
#	    [notifypassword <String>]]
#	[notifyonupdate [<Boolean>]]
#	[logpassword <FileName>] [ignorenullpassword]
def updateUsers(entityList):
  from gam.cmd.ciuserinvitations import _getIsInvitableUser
  def waitingForCreationToComplete(sleep_time):
    writeStderr(Ind.Spaces()+Msg.WAITING_FOR_ITEM_CREATION_TO_COMPLETE_SLEEPING.format(Ent.Singular(Ent.USER), sleep_time))
    time.sleep(sleep_time)

  cd = buildGAPIObject(API.DIRECTORY)
  ci = None
  errorRetries = 5
  updateRetryDelay = 5
  body, notify, tagReplacements, addGroups, addAliases, PwdOpts, \
    updatePrimaryEmail, notFoundBody, groupOrgUnitMap, \
    parameters, resolveConflictAccount = getUserAttributes(cd, True)
  vfe = 'primaryEmail' in body and body['primaryEmail'][:4].lower() == 'vfe@'
  if body.get('orgUnitPath', '') and parameters['immutableOUs']:
    ubody = body.copy()
    checkImmutableOUs = True
  else:
    checkImmutableOUs = False
  i, count, entityList = getEntityArgument(entityList)
  fields = '*' if tagReplacements['subs'] else 'primaryEmail,name,recoveryEmail'
  for user in entityList:
    i += 1
    user = userKey = normalizeEmailAddressOrUID(user)
    if parameters['noActionIfAlias'] and not verifyUserPrimaryEmail(cd, user, parameters['createIfNotFound'], i, count):
      continue
    if checkImmutableOUs:
      body = ubody.copy()
    try:
      if vfe:
        result = callGAPI(cd.users(), 'get',
                          throwReasons=GAPI.USER_GET_THROW_REASONS,
                          userKey=userKey, fields='primaryEmail,id')
        userKey = result['id']
        userPrimary = result['primaryEmail']
        userName, userDomain = splitEmailAddress(userPrimary)
        body['primaryEmail'] = f'vfe.{userName}.{random.randint(1, 99999):05d}@{userDomain}'
        body['emails'] = [{'type': 'custom',
                           'customType': 'former_employee',
                           'primary': False, 'address': userPrimary}]
      elif updatePrimaryEmail:
        if updatePrimaryEmail[0].search(user) is not None:
          body['primaryEmail'] = re.sub(updatePrimaryEmail[0], updatePrimaryEmail[1], user)
          if updatePrimaryEmail[2]:
            entityActionNotPerformedWarning([Ent.USER, user], Msg.UPDATE_PRIMARY_EMAIL_PREVIEW.format(body['primaryEmail']), i, count)
            continue
        else:
          entityActionNotPerformedWarning([Ent.USER, user], Msg.PRIMARY_EMAIL_DID_NOT_MATCH_PATTERN.format(updatePrimaryEmail[0].pattern), i, count)
          continue
      if groupOrgUnitMap:
        try:
          groups = callGAPIpages(cd.groups(), 'list', 'groups',
                                 throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 userKey=userKey, orderBy='email', fields='nextPageToken,groups(email)')
        except (GAPI.invalidMember, GAPI.invalidInput):
          entityUnknownWarning(Ent.USER, userKey, i, count)
          continue
        groupList = []
        for group in groups:
          orgUnit = groupOrgUnitMap.get(group['email'].lower())
          if orgUnit:
            groupList.append(group['email'])
        jcount = len(groupList)
        if jcount != 1:
          entityActionNotPerformedWarning([Ent.USER, user], Msg.USER_BELONGS_TO_N_GROUPS_THAT_MAP_TO_ORGUNITS.format(jcount, ','.join(groupList)), i, count)
          continue
        body['orgUnitPath'] = orgUnit
      if checkImmutableOUs:
        try:
          result = callGAPI(cd.users(), 'get',
                            throwReasons=GAPI.USER_GET_THROW_REASONS,
                            userKey=userKey, fields='orgUnitPath')
          if result['orgUnitPath'] in parameters['immutableOUs']:
            body.pop('orgUnitPath')
        except Exception:
          pass
      if body:
        if 'primaryEmail' in body and parameters['verifyNotInvitable']:
          isInvitableUser, ci = _getIsInvitableUser(ci, body['primaryEmail'])
          if isInvitableUser:
            entityActionNotPerformedWarning([Ent.USER, body['primaryEmail']], Msg.EMAIL_ADDRESS_IS_UNMANAGED_ACCOUNT, i, count)
            continue
        if PwdOpts.makeUniqueRandomPassword or PwdOpts.promptForUniquePassword:
          PwdOpts.AssignPassword(body, notify, notFoundBody, parameters['createIfNotFound'], userKey)
        retry = 0
        while True:
          try:
            result = callGAPI(cd.users(), 'update',
                              throwReasons=[GAPI.CONDITION_NOT_MET, GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                                            GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.ADMIN_CANNOT_UNSUSPEND,
                                            GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.INVALID_PARAMETER,
                                            GAPI.INVALID_ORGUNIT, GAPI.INVALID_SCHEMA_VALUE, GAPI.DUPLICATE,
                                            GAPI.INSUFFICIENT_ARCHIVED_USER_LICENSES, GAPI.CONFLICT],
                              userKey=userKey, body=body, fields=fields)
            entityActionPerformed([Ent.USER, user], i, count)
            if PwdOpts.filename and PwdOpts.password:
              writeFile(PwdOpts.filename, f'{userKey},{PwdOpts.password}\n', mode='a', continueOnError=True)
            if (parameters['notifyOnUpdate'] and notify['password'] and
                (notify.get('recipients') or (parameters['notifyRecoveryEmail'] and result.get('recoveryEmail')))):
              if parameters['notifyRecoveryEmail'] and result.get('recoveryEmail'):
                notify['recipients'].append(result['recoveryEmail'])
              sendCreateUpdateUserNotification(result, notify, tagReplacements, i, count, createMessage=False)
            break
          except GAPI.conditionNotMet as e:
            retry += 1
            if ('User creation is not complete' not in str(e)) or retry > errorRetries:
              entityActionFailedWarning([Ent.USER, user], str(e), i, count)
              break
            waitingForCreationToComplete(updateRetryDelay)
            continue
          except GAPI.userNotFound:
            if parameters['createIfNotFound']:
              if notFoundBody and (count == 1) and not vfe and ('password' in notFoundBody) and ('name' in body) and ('givenName' in body['name']) and ('familyName' in body['name']):
                if 'primaryEmail' not in body:
                  body['primaryEmail'] = user
                body.update(notFoundBody)
                if parameters['setChangePasswordOnCreate']:
                  body['changePasswordAtNextLogin'] = True
                Act.Set(Act.CREATE)
                try:
                  result = callGAPI(cd.users(), 'insert',
                                    throwReasons=[GAPI.DUPLICATE, GAPI.DOMAIN_NOT_FOUND, GAPI.FORBIDDEN,
                                                  GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.INVALID_PARAMETER,
                                                  GAPI.INVALID_ORGUNIT, GAPI.INVALID_SCHEMA_VALUE, GAPI.CONDITION_NOT_MET],
                                    body=body,
                                    fields=fields,
                                    resolveConflictAccount=resolveConflictAccount)
                  entityActionPerformed([Ent.USER, body['primaryEmail']], i, count)
                  if PwdOpts.filename and PwdOpts.notFoundPassword:
                    writeFile(PwdOpts.filename, f'{user},{PwdOpts.notFoundPassword}\n', mode='a', continueOnError=True)
                  if addGroups:
                    createUserAddToGroups(cd, result['primaryEmail'], addGroups, i, count)
                  if addAliases:
                    createUserAddAliases(cd, result['primaryEmail'], addAliases, i, count)
                  if (notify.get('recipients') or (parameters['notifyRecoveryEmail'] and result.get('recoveryEmail'))):
                    notify['password'] = notify['notFoundPassword']
                    if parameters['notifyRecoveryEmail'] and result.get('recoveryEmail'):
                      notify['recipients'].append(result['recoveryEmail'])
                    sendCreateUpdateUserNotification(result, notify, tagReplacements, i, count)
                except GAPI.duplicate:
                  duplicateAliasGroupUserWarning(cd, [Ent.USER, body['primaryEmail']], i, count)
              else:
                entityActionFailedWarning([Ent.USER, user], Msg.UNABLE_TO_CREATE_NOT_FOUND_USER, i, count)
            else:
              entityUnknownWarning(Ent.USER, user, i, count)
          break
      else:
        entityActionNotPerformedWarning([Ent.USER, user], Msg.NO_CHANGES, i, count)
    except GAPI.userNotFound:
      entityUnknownWarning(Ent.USER, user, i, count)
    except GAPI.invalidSchemaValue:
      entityActionFailedWarning([Ent.USER, user], Msg.INVALID_SCHEMA_VALUE, i, count)
    except GAPI.duplicate as e:
      entityActionFailedWarning([Ent.USER, user, Ent.USER, body['primaryEmail']], str(e), i, count)
    except GAPI.invalidOrgunit:
      entityActionFailedWarning([Ent.USER, user], Msg.INVALID_ORGUNIT, i, count)
    except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.badRequest, GAPI.adminCannotUnsuspend,
            GAPI.invalid, GAPI.invalidInput, GAPI.invalidParameter, GAPI.insufficientArchivedUserLicenses,
            GAPI.conflict, GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.conditionNotMet) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)

# gam update users <UserTypeEntity> ...
def doUpdateUsers():
  updateUsers(getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)[1])

# gam update user <UserItem> ...
def doUpdateUser():
  updateUsers(getStringReturnInList(Cmd.OB_USER_ITEM))

# gam <UserTypeEntity> delete users [noactionifalias]
def deleteUsers(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  noActionIfAlias = checkArgumentPresent('noactionifalias')
  checkForExtraneousArguments()
  i, count, entityList = getEntityArgument(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    if noActionIfAlias and not verifyUserPrimaryEmail(cd, user, False, i, count):
      continue
    try:
      callGAPI(cd.users(), 'delete',
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                             GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.FORBIDDEN,
                             GAPI.CONDITION_NOT_MET],
               userKey=user)
      entityActionPerformed([Ent.USER, user], i, count)
    except GAPI.userNotFound:
      entityUnknownWarning(Ent.USER, user, i, count)
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.conditionNotMet as e:
      entityActionFailedWarning([Ent.USER, user], Msg.CAN_NOT_DELETE_USER_WITH_VAULT_HOLD.format(str(e), user), i, count)

# gam delete users <UserTypeEntity> [noactionifalias]
def doDeleteUsers():
  deleteUsers(getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)[1])

# gam delete user <UserItem> [noactionifalias]
def doDeleteUser():
  deleteUsers(getStringReturnInList(Cmd.OB_USER_ITEM))

# gam <UserEntity> undelete users [ou|org|orgunit <OrgUnitPath>]
def undeleteUsers(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  if checkArgumentPresent(['ou', 'org', 'orgunit']):
    entitySelector = getEntitySelector()
    if entitySelector:
      orgUnitPaths = getEntitySelection(entitySelector, True)
    else:
      orgUnitPaths = [getOrgUnitItem()]
    userOrgUnitLists = orgUnitPaths if isinstance(orgUnitPaths, dict) else None
  else:
    orgUnitPaths = ['/']
    userOrgUnitLists = None
  checkForExtraneousArguments()
  i, count, entityList = getEntityArgument(entityList)
  for user in entityList:
    i += 1
    origUser = user
    user = normalizeEmailAddressOrUID(user)
    user_uid = user if user.find('@') == -1 else None
    if not user_uid:
      printEntityKVList([Ent.DELETED_USER, user],
                        [Msg.LOOKING_UP_GOOGLE_UNIQUE_ID, None],
                        i, count)
      try:
        deleted_users = callGAPIpages(cd.users(), 'list', 'users',
                                      throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                      customer=GC.Values[GC.CUSTOMER_ID], showDeleted=True, orderBy='email',
                                      maxResults=GC.Values[GC.USER_MAX_RESULTS])
      except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
        accessErrorExit(cd)
      matching_users = []
      for deleted_user in deleted_users:
        if str(deleted_user['primaryEmail']).lower() == user:
          matching_users.append(deleted_user)
      jcount = len(matching_users)
      if jcount == 0:
        entityUnknownWarning(Ent.DELETED_USER, user, i, count)
        setSysExitRC(NO_ENTITIES_FOUND_RC)
        continue
      if jcount > 1:
        entityActionNotPerformedWarning([Ent.DELETED_USER, user],
                                        Msg.PLEASE_SELECT_ENTITY_TO_PROCESS.format(jcount, Ent.Plural(Ent.DELETED_USER), 'undelete', 'uid:<String>'),
                                        i, count)
        Ind.Increment()
        j = 0
        for matching_user in matching_users:
          printEntity([Ent.UNIQUE_ID, matching_user['id']], j, jcount)
          Ind.Increment()
          for attr_name in ['creationTime', 'lastLoginTime', 'deletionTime']:
            if attr_name in matching_user:
              printKeyValueList([attr_name, formatLocalTime(matching_user[attr_name])])
          Ind.Decrement()
        Ind.Decrement()
        setSysExitRC(MULTIPLE_DELETED_USERS_FOUND_RC)
        continue
      user_uid = matching_users[0]['id']
    if userOrgUnitLists:
      orgUnitPaths = userOrgUnitLists[origUser]
    try:
      callGAPI(cd.users(), 'undelete',
               throwReasons=[GAPI.DELETED_USER_NOT_FOUND, GAPI.INVALID_ORGUNIT,
                             GAPI.DOMAIN_NOT_FOUND, GAPI.DOMAIN_CANNOT_USE_APIS,
                             GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.DUPLICATE,
                             GAPI.LIMIT_EXCEEDED],
               userKey=user_uid, body={'orgUnitPath': makeOrgUnitPathAbsolute(orgUnitPaths[0])})
      entityActionPerformed([Ent.DELETED_USER, user], i, count)
    except GAPI.deletedUserNotFound:
      entityUnknownWarning(Ent.DELETED_USER, user, i, count)
    except GAPI.invalidOrgunit:
      entityActionFailedWarning([Ent.USER, user], Msg.INVALID_ORGUNIT, i, count)
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest,
            GAPI.invalid, GAPI.duplicate, GAPI.limitExceeded) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)

# gam undelete users <UserEntity> [ou|org|orgunit <OrgUnitPath>]
def doUndeleteUsers():
  undeleteUsers(getEntityList(Cmd.OB_USER_ENTITY))

# gam undelete user <UserItem> [ou|org|orgunit <OrgUnitPath>]
def doUndeleteUser():
  undeleteUsers(getStringReturnInList(Cmd.OB_USER_ITEM))

# gam check suspended <UserItem>
def doCheckUserSuspended():
  cd = buildGAPIObject(API.DIRECTORY)
  user = getEmailAddress()
  checkForExtraneousArguments()
  try:
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=user, fields='suspended,suspensionReason', projection='basic')
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden):
    entityDoesNotExistExit(Ent.USER, user)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    accessErrorExit(cd)
  kvList = [Ent.Singular(Ent.USER), user]
  up = 'suspended'
  kvList.extend([UProp.PROPERTIES[up][UProp.TITLE], result[up]])
  if result[up]:
    up = 'suspensionReason'
    kvList.extend([UProp.PROPERTIES[up][UProp.TITLE], result[up]])
    setSysExitRC(USER_SUSPENDED_RC)
  printKeyValueList(kvList)

# gam <UserTypeEntity> suspend users [noactionifalias]
# gam <UserTypeEntity> unsuspend users [noactionifalias]
def suspendUnsuspendUsers(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  noActionIfAlias = checkArgumentPresent('noactionifalias')
  checkForExtraneousArguments()
  body = {'suspended': Act.Get() == Act.SUSPEND}
  i, count, entityList = getEntityArgument(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    if noActionIfAlias and not verifyUserPrimaryEmail(cd, user, False, i, count):
      continue
    try:
      callGAPI(cd.users(), 'update',
               throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                             GAPI.DOMAIN_CANNOT_USE_APIS, GAPI.FORBIDDEN, GAPI.BAD_REQUEST,
                             GAPI.ADMIN_CANNOT_UNSUSPEND],
               userKey=user, body=body)
      entityActionPerformed([Ent.USER, user], i, count)
    except GAPI.userNotFound:
      entityUnknownWarning(Ent.USER, user, i, count)
    except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.adminCannotUnsuspend) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)

# gam suspend users <UserTypeEntity> [noactionifalias]
# gam unsuspend users <UserTypeEntity> [noactionifalias]
def doSuspendUnsuspendUsers():
  suspendUnsuspendUsers(getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)[1])

# gam suspend user <UserItem> [noactionifalias]
# gam unsuspend user <UserItem> [noactionifalias]
def doSuspendUnsuspendUser():
  suspendUnsuspendUsers(getStringReturnInList(Cmd.OB_USER_ITEM))

# gam <UserTypeEntity> signout
# gam <UserTypeEntity> turnoff2sv
def signoutTurnoff2SVUsers(entityList):
  cd = buildGAPIObject(API.DIRECTORY)
  if Act.Get() == Act.SIGNOUT:
    service = cd.users()
    function = 'signOut'
  else:
    service = cd.twoStepVerification()
    function = 'turnOff'
  checkForExtraneousArguments()
  i, count, entityList = getEntityArgument(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      callGAPI(service, function,
               throwReasons=[GAPI.NOT_FOUND, GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_INPUT,
                             GAPI.DOMAIN_NOT_FOUND, GAPI.DOMAIN_CANNOT_USE_APIS,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.AUTH_ERROR],
               userKey=user)
      entityActionPerformed([Ent.USER, user], i, count)
    except (GAPI.notFound, GAPI.userNotFound):
      entityUnknownWarning(Ent.USER, user, i, count)
    except (GAPI.invalid, GAPI.invalidInput, GAPI.domainNotFound, GAPI.domainCannotUseApis,
            GAPI.forbidden, GAPI.permissionDenied, GAPI.authError) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)

# gam <UserTypeEntity> waitformailbox [retries <Number>]
def waitForMailbox(entityList):
  def showRetryStatus(user, exists, i, count):
    kvList = ['Exists', exists, 'mailboxIsSetup', False]
    if maxRetries:
      kvList.extend(['Retry', f'{retries}/{maxRetries}'])
    else:
      kvList.extend(['Retry', f'{retries}'])
    printEntityKVList([Ent.USER, user], kvList, i, count)
    if maxRetries and retries >= maxRetries:
      entityActionFailedWarning([Ent.USER, user], Msg.RETRIES_EXHAUSTED.format(maxRetries), i, count)
      return False
    time.sleep(3)
    return True

  cd = buildGAPIObject(API.DIRECTORY)
  maxRetries = 0
  while Cmd.ArgumentsRemaining():
    argument = getArgument()
    if argument == 'retries':
      maxRetries = getInteger(minVal=0)
    else:
      unknownArgumentExit()
  i, count, entityList = getEntityArgument(entityList)
  for user in entityList:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    retries = 0
    performAction(Ent.USER, user, i, count)
    Ind.Increment()
    while True:
      retries += 1
      try:
        result = callGAPI(cd.users(), 'get',
                          throwReasons=GAPI.USER_GET_THROW_REASONS+[GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND],
                          userKey=user, fields='isMailboxSetup')
        if result.get('isMailboxSetup', False):
          entityActionPerformed([Ent.USER, user], i, count)
          break
        if not showRetryStatus(user, True, i, count):
          break
      except GAPI.userNotFound:
        if not showRetryStatus(user, False, i, count):
          break
      except (GAPI.invalid, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.authError) as e:
        entityActionFailedWarning([Ent.USER, user], str(e), i, count)
        break
      except KeyboardInterrupt:
        entityActionFailedWarning([Ent.USER, user], Msg.CHECK_INTERRUPTED, i, count)
        break
    Ind.Decrement()

def getUserLicenses(lic, user, skus):
  reasons_to_quit = [
    GAPI.ACCESS_NOT_CONFIGURED, # license API not turned on
    GAPI.PERMISSION_DENIED, # Admin doesn't have rights to license assignments
    GAPI.NOT_FOUND # API call succeeded, user does not have this license
  ]

  def _callbackGetLicense(request_id, response, exception):
    if exception is None:
      if response and 'skuId' in response:
        licenses.append(response['skuId'])
        del sku_calls[request_id]
    else:
      _, reason, _ = checkGAPIError(exception, softErrors=True)
      if reason in reasons_to_quit:
        del sku_calls[request_id]

  licenses = []
  svcargs = dict([('userId', user['primaryEmail']), ('productId', None), ('skuId', None), ('fields', 'skuId')]+GM.Globals[GM.EXTRA_ARGS_LIST])
  method = getattr(lic.licenseAssignments(), 'get')
  sku_calls = {}
  for sku in skus:
    svcparms = svcargs.copy()
    svcparms['productId'] = sku[0]
    sku_id = sku[1]
    svcparms['skuId'] = sku_id
    sku_calls[sku_id] = method(**svcparms)
  try_count = 0
  while sku_calls:
    try_count += 1
    dbatch = lic.new_batch_http_request(callback=_callbackGetLicense)
    for sku_id, sku_call in sku_calls.items():
      dbatch.add(sku_call, request_id=sku_id)
    dbatch.execute()
    if sku_calls:
      if try_count >= 5:
        # give up and return what we have
        licenses.append('Not available/incomplete')
        return licenses
      time.sleep(5)
  return licenses

USER_NAME_PROPERTY_PRINT_ORDER = [
  'givenName',
  'familyName',
  'fullName',
  'displayName',
  ]
USER_GUEST_PROPERTY_PRINT_ORDER = [
  'primaryGuestEmail',
  ]
USER_LANGUAGE_PROPERTY_PRINT_ORDER = [
  'languages',
  ]
USER_SCALAR_PROPERTY_PRINT_ORDER = [
  'isGuestUser',
  'guestAccountInfo',
  'isAdmin',
  'isDelegatedAdmin',
  'isEnrolledIn2Sv',
  'isEnforcedIn2Sv',
  'agreedToTerms',
  'ipWhitelisted',
  'suspended',
  'suspensionReason',
  'suspensionTime',
  'archived',
  'archivalTime',
  'changePasswordAtNextLogin',
  'id',
  'customerId',
  'isMailboxSetup',
  'includeInGlobalAddressList',
  'creationTime',
  'lastLoginTime',
  'deletionTime',
  'orgUnitPath',
  'recoveryEmail',
  'recoveryPhone',
  'thumbnailPhotoUrl',
  ]
USER_ARRAY_PROPERTY_PRINT_ORDER = [
  'gender',
  'keywords',
  'notes',
  'addresses',
  'locations',
  'organizations',
  'relations',
  'emails',
  'ims',
  'phones',
  'posixAccounts',
  'sshPublicKeys',
  'externalIds',
  'websites',
  ]

USER_ADDRESSES_PROPERTY_PRINT_ORDER = [
  'primary',
  'sourceIsStructured',
  'formatted',
  'extendedAddress',
  'streetAddress',
  'poBox',
  'locality',
  'region',
  'postalCode',
  'country',
  'countryCode',
  ]

USER_LOCATIONS_PROPERTY_PRINT_ORDER = [
  'area',
  'buildingId',
  'buildingName',
  'floorName',
  'floorSection',
  'deskCode',
  ]

USER_ORGANIZATIONS_PROPERTY_PRINT_ORDER = [
  'name',
  'description',
  'domain',
  'symbol',
  'location',
  'costCenter',
  'department',
  'title',
  'fullTimeEquivalent',
  'primary',
  ]

USER_POSIX_PROPERTY_PRINT_ORDER = [
  'accountId',
  'uid',
  'gid',
  'systemId',
  'operatingSystemType',
  'homeDirectory',
  'shell',
  'gecos',
  'primary',
  ]

USER_SSH_PROPERTY_PRINT_ORDER = [
  'expirationTimeUsec',
  'fingerprint',
  ]

USER_FIELDS_CHOICE_MAP = {
  'address': 'addresses',
  'addresses': 'addresses',
  'admin': ['isAdmin', 'isDelegatedAdmin'],
  'agreed2terms': 'agreedToTerms',
  'agreedtoterms': 'agreedToTerms',
  'aliases': ['aliases', 'nonEditableAliases'],
  'archived': ['archived', 'archivalTime'],
  'changepassword': 'changePasswordAtNextLogin',
  'changepasswordatnextlogin': 'changePasswordAtNextLogin',
  'creationtime': 'creationTime',
  'customerid': 'customerId',
  'deletiontime': 'deletionTime',
  'displayname': 'name.displayName',
  'email': 'emails',
  'emails': 'emails',
  'employeeid': 'externalIds',
  'externalid': 'externalIds',
  'externalids': 'externalIds',
  'familyname': 'name.familyName',
  'firstname': 'name.givenName',
  'fullname': 'name.fullName',
  'gal': 'includeInGlobalAddressList',
  'gender': ['gender.type', 'gender.customGender', 'gender.addressMeAs'],
  'givenname': 'name.givenName',
  'guestaccountinfo': ['guestAccountInfo.primaryGuestEmail'],
  'id': 'id',
  'im': 'ims',
  'ims': 'ims',
  'includeinglobaladdresslist': 'includeInGlobalAddressList',
  'ipwhitelisted': 'ipWhitelisted',
  'isadmin': ['isAdmin', 'isDelegatedAdmin'],
  'isdelegatedadmin': ['isAdmin', 'isDelegatedAdmin'],
  'isenforcedin2sv': 'isEnforcedIn2Sv',
  'isenrolledin2sv': 'isEnrolledIn2Sv',
  'isguestuser': 'isGuestUser',
  'is2svenforced': 'isEnforcedIn2Sv',
  'is2svenrolled': 'isEnrolledIn2Sv',
  'ismailboxsetup': 'isMailboxSetup',
  'keyword': 'keywords',
  'keywords': 'keywords',
  'language': 'languages',
  'languages': 'languages',
  'lastlogintime': 'lastLoginTime',
  'lastname': 'name.familyName',
  'location': 'locations',
  'locations': 'locations',
  'manager': 'relations',
  'name': ['name.givenName', 'name.familyName', 'name.fullName', 'name.displayName'],
  'nicknames': ['aliases', 'nonEditableAliases'],
  'noneditablealiases': ['aliases', 'nonEditableAliases'],
  'note': 'notes',
  'notes': 'notes',
  'org': 'orgUnitPath',
  'organization': 'organizations',
  'organizations': 'organizations',
  'organisation': 'organizations',
  'organisations': 'organizations',
  'orgunit': 'orgUnitPath',
  'orgunitpath': 'orgUnitPath',
  'otheremail': 'emails',
  'otheremails': 'emails',
  'ou': 'orgUnitPath',
  'phone': 'phones',
  'phones': 'phones',
  'photo': 'thumbnailPhotoUrl',
  'photourl': 'thumbnailPhotoUrl',
  'posix': 'posixAccounts',
  'posixaccounts': 'posixAccounts',
  'primaryemail': 'primaryEmail',
  'recoveryemail': 'recoveryEmail',
  'recoveryphone': 'recoveryPhone',
  'relation': 'relations',
  'relations': 'relations',
  'ssh': 'sshPublicKeys',
  'sshkeys': 'sshPublicKeys',
  'sshpublickeys': 'sshPublicKeys',
  'suspended': ['suspended', 'suspensionReason', 'suspensionTime'],
  'thumbnailphotourl': 'thumbnailPhotoUrl',
  'username': 'primaryEmail',
  'website': 'websites',
  'websites': 'websites',
  }

USER_MULTI_ATTR_FILTER_CHOICE_MAP = {
  'address': 'addresses',
  'addresses': 'addresses',
  'email': 'emails',
  'emails': 'emails',
  'externalid': 'externalIds',
  'externalids': 'externalIds',
  'im': 'ims',
  'ims': 'ims',
  'keyword': 'keywords',
  'keywords': 'keywords',
  'location': 'locations',
  'locations': 'locations',
  'organization': 'organizations',
  'organizations': 'organizations',
  'organisation': 'organizations',
  'organisations': 'organizations',
  'otheremail': 'emails',
  'otheremails': 'emails',
  'phone': 'phones',
  'phones': 'phones',
  'relation': 'relations',
  'relations': 'relations',
  'website': 'websites',
  'websites': 'websites',
  }

INFO_USER_OPTIONS = {'noaliases', 'nobuildingnames', 'nogroups', 'nolicenses', 'nolicences', 'noschemas', 'schemas', 'userview'}
USER_SKIP_OBJECTS = {'thumbnailPhotoEtag'}
USER_TIME_OBJECTS = {'creationTime', 'deletionTime', 'lastLoginTime', 'suspensionTime', 'archivalTime', 'disabledTime'}

def _getUserMultiAttributeFilters(myarg, userMultiAttributeFilters):
  up = getChoice(USER_MULTI_ATTR_FILTER_CHOICE_MAP, mapChoice=True)
  filterValue = getString(Cmd.OB_STRING)
  userMultiAttributeFilters.setdefault(up, [])
  if myarg == 'filtermultiattrtype':
    userMultiAttributeFilters[up].append({'type': filterValue})
  else: #elif myarg == 'filtermultiattrcustom':
    userMultiAttributeFilters[up].append({'customType': filterValue})

def _filterUserMultiAttributes(user, userMultiAttributeFilters):
  for up, upTypes in userMultiAttributeFilters.items():
    if up in user:
      filterAttrList = []
      for userAttr in user.pop(up):
        for upType in upTypes:
          if ((userAttr.get('type', None) == upType.get('type', '')) or
              (userAttr.get('customType', None) == upType.get('customType', ''))):
            filterAttrList.append(userAttr)
            break
      user[up] = filterAttrList

def _formatLanguagesList(propertyValue, delimiter):
  languages = []
  for language in propertyValue:
    if 'languageCode' in language:
      lang = language['languageCode']
      if language.get('preference') == 'preferred':
        lang += '+'
      elif language.get('preference') == 'not_preferred':
        lang += '-'
    else:
      lang = language.get('customLanguage')
    if lang:
      languages.append(lang)
  return delimiter.join(languages)

def _initSchemaParms(projection):
  return {'projection': projection, 'customFieldMask': None, 'selectedSchemaFields': {}}

def _getSchemaNameList(schemaParms):
  customFieldMask = getString(Cmd.OB_SCHEMA_NAME_LIST).replace(' ', ',')
  if customFieldMask.lower() == 'all':
    schemaParms['projection'] = 'full'
    schemaParms['customFieldMask'] = None
    schemaParms['selectedSchemaFields'] = {}
  else:
    schemaParms['projection'] = 'custom'
    customFieldMaskList = []
    for schemaField in customFieldMask.split(','):
      if schemaField.find('.') == -1:
        customFieldMaskList.append(schemaField)
      else:
        schemaName, fieldName = schemaField.split('.', 1)
        customFieldMaskList.append(schemaName)
        schemaParms['selectedSchemaFields'] .setdefault(schemaName, set())
        schemaParms['selectedSchemaFields'][schemaName].add(fieldName)
    schemaParms['customFieldMask'] = ','.join(customFieldMaskList)

def _filterSchemaFields(userEntity, schemaParms):
  schemas = userEntity.pop('customSchemas', None)
  if schemas is None:
    return
  customSchemas = {}
  for schema in sorted(schemas):
    if schema in schemaParms['selectedSchemaFields']:
      for field, value in sorted(schemas[schema].items()):
        if field not in schemaParms['selectedSchemaFields'][schema]:
          continue
        customSchemas.setdefault(schema, {})
        customSchemas[schema][field] = value
    else:
      customSchemas[schema] = schemas[schema]
  userEntity['customSchemas'] = customSchemas

