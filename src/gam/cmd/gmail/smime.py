"""S/MIME certificate management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""


from gam.util.args import formatLocalTimestamp
import base64

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIitems
from gam.util.args import UTF8, getArgument, getEmailAddress, getString
from gam.util.csv_pf import CSVPrintFile, flattenJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityModifierNewValueActionPerformed,
    entityPerformActionSubItemModifierNumItems,
    printEntity,
    printEntityKVList,
    printGettingEntityItemForWhom,
    printKeyValueList,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.fileio import readFile, setFilePath
from gam.util.output import setSysExitRC
from gam.constants import NO_ENTITIES_FOUND_RC

from gam.var import Act, Cmd, Ent, Ind

def createSmime(users):
  sendAsEmailBase = None
  setDefault = False
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'file':
      smimeData = readFile(setFilePath(getString(Cmd.OB_FILE_NAME), GC.INPUT_DIR), mode='rb')
      body['pkcs12'] = base64.urlsafe_b64encode(smimeData).decode(UTF8)
    elif myarg == 'password':
      body['encryptedKeyPassword'] = getString(Cmd.OB_PASSWORD)
    elif myarg == 'default':
      setDefault = True
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = getEmailAddress(noUid=True)
    else:
      unknownArgumentExit()
  if 'pkcs12' not in body:
    missingArgumentExit('file')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    try:
      Act.Set(Act.CREATE)
      result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'insert',
                        throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                        userId='me', sendAsEmail=sendAsEmail, body=body, fields='id,issuerCn')
      entityModifierNewValueActionPerformed([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, result['id']],
                                            Act.MODIFIER_FROM, f'{Ent.Singular(Ent.ISSUER_CN)}: {result["issuerCn"]}', i, count)
      if setDefault:
        Act.Set(Act.UPDATE)
        smimeId = result['id']
        callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'setDefault',
                 throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                 userId='me', sendAsEmail=sendAsEmail, id=smimeId)
        entityActionPerformedMessage([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, smimeId], Msg.DEFAULT_SMIME, i, count)
    except (GAPI.forbidden, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

def _getSmimeIds(gmail, user, i, count, sendAsEmail, function):
  try:
    result = callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'list',
                      throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                      userId='me', sendAsEmail=sendAsEmail, fields='smimeInfo(id)')
    smimes = result.get('smimeInfo', [])
    jcount = len(smimes)
    if jcount == 0:
      entityActionNotPerformedWarning([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, None],
                                      Msg.NO_ENTITIES_FOUND.format(Ent.Plural(Ent.SMIME_ID)), i, count)
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    elif jcount > 1:
      entityActionNotPerformedWarning([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, None],
                                      Msg.PLEASE_SELECT_ENTITY_TO_PROCESS.format(jcount, Ent.Plural(Ent.SMIME_ID), function, 'id <S/MIMEID>'),
                                      i, count)
      Ind.Increment()
      j = 0
      for smime in smimes:
        j += 1
        printEntityKVList([Ent.SMIME_ID, smime['id'], Ent.ISSUER_CN, smime['issuerCn']], ['Default', smime.get('isDefault', False)], j, jcount)
      Ind.Decrement()
    else:
      return smimes[0]['id']
  except GAPI.forbidden as e:
    entityActionFailedWarning([Ent.USER, user], str(e), i, count)
  except GAPI.serviceNotAvailable:
    userGmailServiceNotEnabledWarning(user, i, count)
  return None

# gam <UserTypeEntity> update smime default
#	[id <SmimeID>] [sendas|sendasemail <EmailAddress>]
def updateSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  setDefault = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'id':
      smimeIdBase = getString(Cmd.OB_SMIME_ID)
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = getEmailAddress(noUid=True)
    elif myarg == 'default':
      setDefault = True
    else:
      unknownArgumentExit()
  if not setDefault:
    missingArgumentExit('default')
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    if not smimeIdBase:
      smimeId = _getSmimeIds(gmail, user, i, count, sendAsEmail, 'update')
      if not smimeId:
        continue
    else:
      smimeId = smimeIdBase
    try:
      callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'setDefault',
               throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
               userId='me', sendAsEmail=sendAsEmail, id=smimeId)
      entityActionPerformedMessage([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, smimeId], Msg.DEFAULT_SMIME, i, count)
    except GAPI.notFound as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SMIME_ID, smimeId], str(e), i, count)
    except (GAPI.forbidden, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete smime
#	[id <SmimeID>] [sendas|sendasemail <EmailAddress>]
def deleteSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'id':
      smimeIdBase = getString(Cmd.OB_SMIME_ID)
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = getEmailAddress(noUid=True)
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    if not smimeIdBase:
      smimeId = _getSmimeIds(gmail, user, i, count, sendAsEmail, 'delete')
      if not smimeId:
        continue
    else:
      smimeId = smimeIdBase
    try:
      callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'delete',
               throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
               userId='me', sendAsEmail=sendAsEmail, id=smimeId)
      entityActionPerformed([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, smimeId], i, count)
    except GAPI.notFound as e:
      entityActionFailedWarning([Ent.USER, user, Ent.SMIME_ID, smimeId], str(e), i, count)
    except (GAPI.forbidden, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> print smimes [todrive <ToDriveAttribute>*]
#	[primary|default|(sendas|sendasemail <EmailAddress>)]
# gam <UserTypeEntity> show smimes
#	[primary|default|(sendas|sendasemail <EmailAddress>)]
def printShowSmimes(users):
  csvPF = CSVPrintFile(['User', 'id', 'isDefault', 'issuerCn', 'expiration', 'encryptedKeyPassword', 'pem']) if Act.csvFormat() else None
  selectField = 'sendAsEmail'
  sendAsEmailBase = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'default', 'defaultonly'}:
      selectField = 'isDefault'
    elif myarg in {'primary', 'primaryonly'}:
      selectField = 'isPrimary'
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = getEmailAddress(noUid=True)
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      if sendAsEmailBase:
        sendAsEmails = [sendAsEmailBase]
      else:
        results = callGAPIitems(gmail.users().settings().sendAs(), 'list', 'sendAs',
                                throwReasons=GAPI.GMAIL_THROW_REASONS,
                                userId='me', fields='sendAs(isDefault,isPrimary,sendAsEmail)')
        sendAsEmails = [sendAs['sendAsEmail'] for sendAs in results if sendAs.get(selectField, False)]
      jcount = len(sendAsEmails)
      if not csvPF:
        entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.SMIME_ID, Act.MODIFIER_FROM, jcount, Ent.SENDAS_ADDRESS, i, count)
      else:
        printGettingEntityItemForWhom(Ent.SENDAS_ADDRESS, user, i, count)
      if sendAsEmails:
        j = 0
        for sendAsEmail in sendAsEmails:
          j += 1
          smimes = callGAPIitems(gmail.users().settings().sendAs().smimeInfo(), 'list', 'smimeInfo',
                                 throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                                 userId='me', sendAsEmail=sendAsEmail)
          kcount = len(smimes)
          if not csvPF:
            Ind.Increment()
            printEntity([Ent.SENDAS_ADDRESS, sendAsEmail], j, jcount)
            Ind.Increment()
            k = 0
            for smime in smimes:
              k += 1
              printEntity([Ent.SMIME_ID, smime['id']], k, kcount)
              Ind.Increment()
              printKeyValueList(['Default', smime.get('isDefault', False)])
              printKeyValueList(['Issuer CN', smime['issuerCn']])
              printKeyValueList(['Expiration', formatLocalTimestamp(smime['expiration'])])
              printKeyValueList(['Password', smime.get('encryptedKeyPassword', '')])
              printKeyValueList(['PEM', None])
              Ind.Increment()
              printKeyValueList([Ind.MultiLineText(smime['pem'])])
              Ind.Decrement()
              Ind.Decrement()
            Ind.Decrement()
            Ind.Decrement()
          elif smimes:
            for smime in smimes:
              smime['expiration'] = formatLocalTimestamp(smime['expiration'])
              csvPF.WriteRowTitles(flattenJSON(smime, flattened={'User': user}))
          elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
            csvPF.WriteRowNoFilter({'User': user})
      elif csvPF and GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except (GAPI.forbidden, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('S/MIME')

