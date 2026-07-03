"""Client-side encryption identity and key pair management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re
import json
import sys
import os

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import buildGAPIServiceObject, callGAPI, callGAPIpages
from gam.util.args import (
    UTF8,
    getArgument,
    getBoolean,
    getEmailAddress,
    getString,
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
    printEntity,
    printGettingAllEntityItemsForWhom,
    printLine,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import entityDoesNotExistExit, missingArgumentExit, usageErrorExit
from gam.util.fileio import readFile, setFilePath
from gam.util.output import writeStdout

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _showCSEItem(result, entityType, keyField, timeObjects, i, count, FJQC):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(result, timeObjects=timeObjects),
                         ensure_ascii=False, sort_keys=True))
    return
  Ind.Increment()
  printEntity([entityType, result[keyField]], i, count)
  Ind.Increment()
  showJSON(None, result, timeObjects=timeObjects)
  Ind.Decrement()
  Ind.Decrement()

def _initCSEKeyPairSkipObjects():
  return {'pem', 'kaclsData'}

def _resetCSEKeyPairSkipObjects(myarg, skipObjects):
  if myarg == 'showpem':
    skipObjects.discard('pem')
  elif myarg == 'showkaclsdata':
    skipObjects.discard('kaclsData')
  else:
    return False
  return True

def _stripCSEKeyPairSkipObjects(result, skipObjects):
  if 'pem' in skipObjects:
    result.pop('pem', None)
  if 'kaclsData' in skipObjects:
    for privateKeyMetadata in result.get('privateKeyMetadata', []):
      if 'kaclsKeyMetadata' in privateKeyMetadata:
        privateKeyMetadata['kaclsKeyMetadata'].pop('kaclsData', None)

CSE_IDENTITY_TIME_OBJECTS = {}
CSE_KEYPAIR_TIME_OBJECTS = {'disableTime'}

def _printShowCSEItems(users, entityType, keyField, timeObjects):
  csvPF = CSVPrintFile(['User', keyField]) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  skipObjects = _initCSEKeyPairSkipObjects() if entityType == Ent.CSE_KEYPAIR else set()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif entityType == Ent.CSE_KEYPAIR and _resetCSEKeyPairSkipObjects(myarg, skipObjects):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    printGettingAllEntityItemsForWhom(entityType, user, i, count)
    kvList = [Ent.USER, user, entityType, None]
    try:
      if entityType == Ent.CSE_IDENTITY:
        results = callGAPIpages(gmail.users().settings().cse().identities(), 'list', 'cseIdentities',
                                throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                                userId='me', fields='nextPageToken,cseIdentities')
      else:
        results = callGAPIpages(gmail.users().settings().cse().keypairs(), 'list', 'cseKeyPairs',
                                throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED],
                                userId='me', fields='nextPageToken,cseKeyPairs')

    except GAPI.permissionDenied as e:
      entityActionFailedWarning(kvList, str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
      continue
    if not csvPF:
      jcount = len(results)
      if not  FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
      j = 0
      for result in results:
        j += 1
        if entityType == Ent.CSE_KEYPAIR:
          _stripCSEKeyPairSkipObjects(result, skipObjects)
        _showCSEItem(result, entityType, keyField, timeObjects, j, jcount, FJQC)
    else:
      for result in results:
        row = flattenJSON(result, flattened={'User': user})
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          csvPF.WriteRowNoFilter({'User': user, keyField: result[keyField],
                                  'JSON':  json.dumps(cleanJSON(result, skipObjects=skipObjects, timeObjects=timeObjects),
                                                      ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile(Ent.Plural(entityType))

CSE_IDENTITY_ACTION_FUNCTION_MAP = {
  Act.CREATE: 'create',
  Act.UPDATE: 'patch',
  Act.DELETE: 'delete',
  Act.INFO: 'get',
  }

# gam <UserTypeEntity> create cseidentity
#	(primarykeypairid <KeyPairID>) | (signingkeypairid <KeyPairID> encryptionkeypairid <KeyPairID>)
#	[kpemail <EmailAddress>]
#	[formatjson]
# gam <UserTypeEntity> update cseidentity
#	(primarykeypairid <KeyPairID>) | (signingkeypairid <KeyPairID> encryptionkeypairid <KeyPairID>)
#	[kpemail <EmailAddress>]
#	[formatjson]
def createUpdateCSEIdentity(users):
  function = CSE_IDENTITY_ACTION_FUNCTION_MAP[Act.Get()]
  primaryKeyPairId = signingKeyPairId = encryptionKeyPairId = None
  FJQC = FormatJSONQuoteChar()
  kpEmail = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'primarykeypairid':
      primaryKeyPairId = getString(Cmd.OB_CSE_KEYPAIR_ID)
    elif myarg == 'signingkeypairid':
      signingKeyPairId = getString(Cmd.OB_CSE_KEYPAIR_ID)
    elif myarg == 'encryptionkeypairid':
      encryptionKeyPairId = getString(Cmd.OB_CSE_KEYPAIR_ID)
    elif myarg == 'kpemail':
      kpEmail = getEmailAddress(noUid=True)
    else:
      FJQC.GetFormatJSON(myarg)
  if primaryKeyPairId:
    if signingKeyPairId or encryptionKeyPairId:
      usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('primarykeypairid', 'signingkeypairid/encryptionkeypairid'))
    identity = {'primaryKeyPairId': primaryKeyPairId, 'emailAddress': None}
    keyPairId = primaryKeyPairId
  elif signingKeyPairId or encryptionKeyPairId:
    if not signingKeyPairId or not encryptionKeyPairId:
      usageErrorExit(Msg.ARE_BOTH_REQUIRED.format('signingkeypairid', 'encryptionkeypairid'))
    identity = {'signAndEncryptKeyPairs': {'signingKeyPairId': signingKeyPairId, 'encryptionKeyPairId': encryptionKeyPairId},
                'emailAddress': None}
    keyPairId = f'{signingKeyPairId}/{encryptionKeyPairId}'
  else:
    missingArgumentExit('primarykeypairid|(signingkeypairid & encryptionkeypairid)')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    identity['emailAddress'] = user if not kpEmail else kpEmail
    kwargs = {'body': identity}
    if function == 'patch':
      kwargs['emailAddress'] = identity['emailAddress']
    kvList = [Ent.USER, user, Ent.CSE_IDENTITY, identity['emailAddress'], Ent.CSE_KEYPAIR, keyPairId]
    try:
      result = callGAPI(gmail.users().settings().cse().identities(), function,
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.NOT_FOUND, GAPI.ALREADY_EXISTS],
                        userId='me', **kwargs)
      if not  FJQC.formatJSON:
        entityActionPerformed(kvList, i, count)
      _showCSEItem(result, Ent.CSE_IDENTITY, 'emailAddress', CSE_IDENTITY_TIME_OBJECTS, i, count, FJQC)
    except (GAPI.permissionDenied, GAPI.invalidArgument, GAPI.notFound, GAPI.alreadyExists) as e:
      entityActionFailedWarning(kvList, str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete cseidentity [kpemail <EmailAddress>]
# gam <UserTypeEntity> info cseidentity [kpemail <EmailAddress>]
#	[formatjson]
def processCSEIdentity(users):
  function = CSE_IDENTITY_ACTION_FUNCTION_MAP[Act.Get()]
  FJQC = FormatJSONQuoteChar()
  kpEmail = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'kpemail':
      kpEmail = getEmailAddress(noUid=True)
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    kwargs = {'cseEmailAddress': user if not kpEmail else kpEmail}
    kvList = [Ent.USER, user, Ent.CSE_IDENTITY, kwargs['cseEmailAddress']]
    try:
      result = callGAPI(gmail.users().settings().cse().identities(), function,
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.NOT_FOUND],
                        userId='me', **kwargs)
      if not FJQC.formatJSON:
        entityActionPerformed(kvList, i, count)
      if function != 'delete':
        _showCSEItem(result, Ent.CSE_IDENTITY, 'emailAddress', CSE_IDENTITY_TIME_OBJECTS, i, count, FJQC)
    except (GAPI.permissionDenied, GAPI.notFound) as e:
      entityActionFailedWarning(kvList, str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> show cseidentities
#	[formatjson]
# gam <UserTypeEntity> print cseidentities [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def printShowCSEIdentities(users):
  _printShowCSEItems(users, Ent.CSE_IDENTITY, 'emailAddress', CSE_IDENTITY_TIME_OBJECTS)

# gam <UserTypeEntity> create csekeypair [incertdir <FilePath>] [inkeydir <FilePath>]
#	[addidentity [<Boolean>]] [kpemail <EmailAddress>]
#	[showpem] [showkaclsdata] [formatjson|returnidonly]
def createCSEKeyPair(users):
  def _getFolderPath(myarg, cfgDir):
    filepath = setFilePath(getString(Cmd.OB_FILE_PATH), cfgDir)
    if not os.path.isdir(filepath):
      entityDoesNotExistExit(Ent.DIRECTORY, f'{myarg} {filepath}')
    return filepath

  FJQC = FormatJSONQuoteChar()
  incertdir = GC.Values[GC.GMAIL_CSE_INCERT_DIR]
  inkeydir = GC.Values[GC.GMAIL_CSE_INKEY_DIR]
  addIdentity = returnIdOnly = False
  kpEmail = None
  skipObjects = _initCSEKeyPairSkipObjects()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'incertdir':
      incertdir = _getFolderPath(myarg, GC.GMAIL_CSE_INCERT_DIR)
    elif myarg == 'inkeydir':
      inkeydir = _getFolderPath(myarg, GC.GMAIL_CSE_INKEY_DIR)
    elif myarg == 'addidentity':
      addIdentity = getBoolean()
    elif myarg == 'kpemail':
      kpEmail = getEmailAddress(noUid=True)
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif _resetCSEKeyPairSkipObjects(myarg, skipObjects):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  if not incertdir:
    missingArgumentExit('incertdir <FilePath>')
  if not inkeydir:
    missingArgumentExit('inkeydir <FilePath>')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    kvList = [Ent.USER, user, Ent.CSE_KEYPAIR, None]
    smimeFilename = os.path.join(incertdir, user+'.p7pem')
    if not os.path.isfile(smimeFilename):
      entityActionNotPerformedWarning(kvList, Msg.FILE_NOT_FOUND.format(smimeFilename), i, count)
      continue
    smimeData = readFile(smimeFilename, mode='rb', continueOnError=True)
    if smimeData is None:
      continue
    kaclFilename = os.path.join(inkeydir, user+'.wrap')
    if not os.path.isfile(kaclFilename):
      entityActionNotPerformedWarning(kvList, Msg.FILE_NOT_FOUND.format(kaclFilename), i, count)
      continue
    jsonData = readFile(kaclFilename, mode='r', encoding=UTF8, continueOnError=True)
    if jsonData is None:
      continue
    try:
      keyData = json.loads(jsonData)
      key = 'kacls_url'
      kaclsUri = keyData[key]
      key = 'wrapped_private_key'
      kaclsData = keyData[key]
      cseKeyPair = {
        'pkcs7': smimeData.decode(UTF8),
        'privateKeyMetadata': [{'kaclsKeyMetadata': {'kaclsUri': kaclsUri, 'kaclsData': kaclsData}}]
      }
    except KeyError:
      entityActionNotPerformedWarning(kvList, Msg.JSON_KEY_NOT_FOUND.format(key, kaclFilename), i, count)
      continue
    except (IndexError, SyntaxError, TypeError, ValueError) as e:
      entityActionNotPerformedWarning(kvList, Msg.JSON_ERROR.format(str(e), kaclFilename) , i, count)
      continue
    try:
      result = callGAPI(gmail.users().settings().cse().keypairs(), 'create',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.ALREADY_EXISTS],
                        userId='me', body=cseKeyPair)

      keyPairId = result['keyPairId']
      if not returnIdOnly:
        kvList[-1] = keyPairId
        if not  FJQC.formatJSON:
          entityActionPerformed(kvList, i, count)
        _stripCSEKeyPairSkipObjects(result, skipObjects)
        _showCSEItem(result, Ent.CSE_KEYPAIR, 'keyPairId', CSE_KEYPAIR_TIME_OBJECTS, i, count, FJQC)
      elif not addIdentity:
        writeStdout(f'{keyPairId}\n')
      if addIdentity:
        identity = {'keyPairId': keyPairId, 'emailAddress': user if not kpEmail else kpEmail}
        kvList = [Ent.USER, user, Ent.CSE_KEYPAIR, keyPairId, Ent.CSE_IDENTITY, identity['emailAddress']]
        result = callGAPI(gmail.users().settings().cse().identities(), 'create',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.ALREADY_EXISTS],
                          userId='me', body=identity)
        if not returnIdOnly:
          if not  FJQC.formatJSON:
            entityActionPerformed(kvList, i, count)
          _showCSEItem(result, Ent.CSE_IDENTITY, 'emailAddress', CSE_IDENTITY_TIME_OBJECTS, i, count, FJQC)
        else:
          writeStdout(f'{keyPairId}-{user}\n')
    except (GAPI.permissionDenied, GAPI.alreadyExists) as e:
      entityActionFailedWarning(kvList, str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

CSE_KEYPAIR_ACTION_FUNCTION_MAP = {
  Act.DISABLE: 'disable',
  Act.ENABLE: 'enable',
  Act.OBLITERATE: 'obliterate',
  Act.INFO: 'get',
  }

# gam <UserTypeEntity> disable csekeypair <KeyPairID>
#	[showpem] [showkaclsdata] [formatjson]
# gam <UserTypeEntity> enable csekeypair <KeyPairID>
#	[showpem] [showkaclsdata] [formatjson]
# gam <UserTypeEntity> obliterate csekeypair <KeyPairID>
# gam <UserTypeEntity> info csekey3pair <KeyPairID>
#	[showpem] [showkaclsdata] [formatjson]
def processCSEKeyPair(users):
  function = CSE_KEYPAIR_ACTION_FUNCTION_MAP[Act.Get()]
  keyPairId = getString(Cmd.OB_CSE_KEYPAIR_ID)
  FJQC = FormatJSONQuoteChar()
  skipObjects = _initCSEKeyPairSkipObjects()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _resetCSEKeyPairSkipObjects(myarg, skipObjects):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    kvList = [Ent.USER, user, Ent.CSE_KEYPAIR, keyPairId]
    try:
      result = callGAPI(gmail.users().settings().cse().keypairs(), function,
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT,
                                                               GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.ALREADY_EXISTS],
                        userId='me', keyPairId=keyPairId)
      if function != 'obliterate':
        if not FJQC.formatJSON:
          entityActionPerformed(kvList, i, count)
        _stripCSEKeyPairSkipObjects(result, skipObjects)
        _showCSEItem(result, Ent.CSE_KEYPAIR, 'keyPairId', CSE_KEYPAIR_TIME_OBJECTS, i, count, FJQC)
      else:
        entityActionPerformed(kvList, i, count)
    except (GAPI.permissionDenied, GAPI.invalidArgument, GAPI.notFound, GAPI.failedPrecondition, GAPI.alreadyExists) as e:
      entityActionFailedWarning(kvList, str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> show csekeypairs
#	[showpem] [showkaclsdata] [formatjson]
# gam <UserTypeEntity> print csekeypairs [todrive <ToDriveAttribute>*]
#	[showpem] [showkaclsdata] [formatjson [quotechar <Character>]]
def printShowCSEKeyPairs(users):
  _printShowCSEItems(users, Ent.CSE_KEYPAIR, 'keyPairId', CSE_KEYPAIR_TIME_OBJECTS)

# gam <UserTypeEntity> signature|sig
#	<SignatureContent>
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution> <Tag> <String>)*
#	[html [<Boolean>]] [replyto <EmailAddress>] [default] [treatasalias <Boolean>]
#	[name <String>]
#	[primary]
