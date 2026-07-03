"""S/MIME certificate management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re
import sys

from gam.util.args import formatLocalTimestamp
import base64

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

def createSmime(users):
  sendAsEmailBase = None
  setDefault = False
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'file':
      smimeData = _getMain().readFile(_getMain().setFilePath(_getMain().getString(Cmd.OB_FILE_NAME), GC.INPUT_DIR), mode='rb')
      body['pkcs12'] = base64.urlsafe_b64encode(smimeData).decode(_getMain().UTF8)
    elif myarg == 'password':
      body['encryptedKeyPassword'] = _getMain().getString(Cmd.OB_PASSWORD)
    elif myarg == 'default':
      setDefault = True
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = _getMain().getEmailAddress(noUid=True)
    else:
      _getMain().unknownArgumentExit()
  if 'pkcs12' not in body:
    _getMain().missingArgumentExit('file')
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    sendAsEmail = sendAsEmailBase if sendAsEmailBase else user
    try:
      Act.Set(Act.CREATE)
      result = _getMain().callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'insert',
                        throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                        userId='me', sendAsEmail=sendAsEmail, body=body, fields='id,issuerCn')
      _getMain().entityModifierNewValueActionPerformed([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, result['id']],
                                            Act.MODIFIER_FROM, f'{Ent.Singular(Ent.ISSUER_CN)}: {result["issuerCn"]}', i, count)
      if setDefault:
        Act.Set(Act.UPDATE)
        smimeId = result['id']
        _getMain().callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'setDefault',
                 throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                 userId='me', sendAsEmail=sendAsEmail, id=smimeId)
        _getMain().entityActionPerformedMessage([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, smimeId], Msg.DEFAULT_SMIME, i, count)
    except (GAPI.forbidden, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)

def _getSmimeIds(gmail, user, i, count, sendAsEmail, function):
  try:
    result = _getMain().callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'list',
                      throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                      userId='me', sendAsEmail=sendAsEmail, fields='smimeInfo(id)')
    smimes = result.get('smimeInfo', [])
    jcount = len(smimes)
    if jcount == 0:
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, None],
                                      Msg.NO_ENTITIES_FOUND.format(Ent.Plural(Ent.SMIME_ID)), i, count)
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
    elif jcount > 1:
      _getMain().entityActionNotPerformedWarning([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, None],
                                      Msg.PLEASE_SELECT_ENTITY_TO_PROCESS.format(jcount, Ent.Plural(Ent.SMIME_ID), function, 'id <S/MIMEID>'),
                                      i, count)
      Ind.Increment()
      j = 0
      for smime in smimes:
        j += 1
        _getMain().printEntityKVList([Ent.SMIME_ID, smime['id'], Ent.ISSUER_CN, smime['issuerCn']], ['Default', smime.get('isDefault', False)], j, jcount)
      Ind.Decrement()
    else:
      return smimes[0]['id']
  except GAPI.forbidden as e:
    _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
  except GAPI.serviceNotAvailable:
    _getMain().userGmailServiceNotEnabledWarning(user, i, count)
  return None

# gam <UserTypeEntity> update smime default
#	[id <SmimeID>] [sendas|sendasemail <EmailAddress>]
def updateSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  setDefault = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'id':
      smimeIdBase = _getMain().getString(Cmd.OB_SMIME_ID)
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = _getMain().getEmailAddress(noUid=True)
    elif myarg == 'default':
      setDefault = True
    else:
      _getMain().unknownArgumentExit()
  if not setDefault:
    _getMain().missingArgumentExit('default')
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
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
      _getMain().callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'setDefault',
               throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
               userId='me', sendAsEmail=sendAsEmail, id=smimeId)
      _getMain().entityActionPerformedMessage([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, smimeId], Msg.DEFAULT_SMIME, i, count)
    except GAPI.notFound as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SMIME_ID, smimeId], str(e), i, count)
    except (GAPI.forbidden, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete smime
#	[id <SmimeID>] [sendas|sendasemail <EmailAddress>]
def deleteSmime(users):
  smimeIdBase = None
  sendAsEmailBase = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'id':
      smimeIdBase = _getMain().getString(Cmd.OB_SMIME_ID)
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = _getMain().getEmailAddress(noUid=True)
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
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
      _getMain().callGAPI(gmail.users().settings().sendAs().smimeInfo(), 'delete',
               throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
               userId='me', sendAsEmail=sendAsEmail, id=smimeId)
      _getMain().entityActionPerformed([Ent.USER, user, Ent.SENDAS_ADDRESS, sendAsEmail, Ent.SMIME_ID, smimeId], i, count)
    except GAPI.notFound as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.SMIME_ID, smimeId], str(e), i, count)
    except (GAPI.forbidden, GAPI.invalidArgument, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> print smimes [todrive <ToDriveAttribute>*]
#	[primary|default|(sendas|sendasemail <EmailAddress>)]
# gam <UserTypeEntity> show smimes
#	[primary|default|(sendas|sendasemail <EmailAddress>)]
def printShowSmimes(users):
  csvPF = _getMain().CSVPrintFile(['User', 'id', 'isDefault', 'issuerCn', 'expiration', 'encryptedKeyPassword', 'pem']) if Act.csvFormat() else None
  selectField = 'sendAsEmail'
  sendAsEmailBase = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'default', 'defaultonly'}:
      selectField = 'isDefault'
    elif myarg in {'primary', 'primaryonly'}:
      selectField = 'isPrimary'
    elif myarg in {'sendas', 'sendasemail'}:
      sendAsEmailBase = _getMain().getEmailAddress(noUid=True)
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      if sendAsEmailBase:
        sendAsEmails = [sendAsEmailBase]
      else:
        results = _getMain().callGAPIitems(gmail.users().settings().sendAs(), 'list', 'sendAs',
                                throwReasons=GAPI.GMAIL_THROW_REASONS,
                                userId='me', fields='sendAs(isDefault,isPrimary,sendAsEmail)')
        sendAsEmails = [sendAs['sendAsEmail'] for sendAs in results if sendAs.get(selectField, False)]
      jcount = len(sendAsEmails)
      if not csvPF:
        _getMain().entityPerformActionSubItemModifierNumItems([Ent.USER, user], Ent.SMIME_ID, Act.MODIFIER_FROM, jcount, Ent.SENDAS_ADDRESS, i, count)
      else:
        _getMain().printGettingEntityItemForWhom(Ent.SENDAS_ADDRESS, user, i, count)
      if sendAsEmails:
        j = 0
        for sendAsEmail in sendAsEmails:
          j += 1
          smimes = _getMain().callGAPIitems(gmail.users().settings().sendAs().smimeInfo(), 'list', 'smimeInfo',
                                 throwReasons=GAPI.GMAIL_SMIME_THROW_REASONS,
                                 userId='me', sendAsEmail=sendAsEmail)
          kcount = len(smimes)
          if not csvPF:
            Ind.Increment()
            _getMain().printEntity([Ent.SENDAS_ADDRESS, sendAsEmail], j, jcount)
            Ind.Increment()
            k = 0
            for smime in smimes:
              k += 1
              _getMain().printEntity([Ent.SMIME_ID, smime['id']], k, kcount)
              Ind.Increment()
              _getMain().printKeyValueList(['Default', smime.get('isDefault', False)])
              _getMain().printKeyValueList(['Issuer CN', smime['issuerCn']])
              _getMain().printKeyValueList(['Expiration', formatLocalTimestamp(smime['expiration'])])
              _getMain().printKeyValueList(['Password', smime.get('encryptedKeyPassword', '')])
              _getMain().printKeyValueList(['PEM', None])
              Ind.Increment()
              _getMain().printKeyValueList([Ind.MultiLineText(smime['pem'])])
              Ind.Decrement()
              Ind.Decrement()
            Ind.Decrement()
            Ind.Decrement()
          elif smimes:
            for smime in smimes:
              smime['expiration'] = formatLocalTimestamp(smime['expiration'])
              csvPF.WriteRowTitles(_getMain().flattenJSON(smime, flattened={'User': user}))
          elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
            csvPF.WriteRowNoFilter({'User': user})
      elif csvPF and GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except (GAPI.forbidden, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('S/MIME')

