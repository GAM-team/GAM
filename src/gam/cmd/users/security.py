"""GAM user security commands (ASPs, Backup Codes)."""



from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind

from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPIitems, callGAPI
from gam.util.args import getArgument, checkForExtraneousArguments
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import entityActionFailedWarning, entityActionPerformed, printKeyValueList

def _showASPs(user, asps, i=0, count=0):
  Act.Set(Act.SHOW)
  jcount = len(asps)
  entityPerformActionNumItems([Ent.USER, user], jcount, Ent.APPLICATION_SPECIFIC_PASSWORD, i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  for asp in asps:
    if asp['creationTime'] == '0':
      created_date = UNKNOWN
    else:
      created_date = formatLocalTimestamp(asp['creationTime'])
    if asp['lastTimeUsed'] == '0':
      used_date = GC.NEVER
    else:
      used_date = formatLocalTimestamp(asp['lastTimeUsed'])
    printKeyValueList(['ID', asp['codeId']])
    Ind.Increment()
    printKeyValueList(['Name', asp['name']])
    printKeyValueList(['Created', created_date])
    printKeyValueList(['Last Used', used_date])
    Ind.Decrement()
  Ind.Decrement()

# gam <UserTypeEntity> delete asps|applicationspecificpasswords all|<AspIDList>
def deleteASP(users):
  cd = buildGAPIObject(API.DIRECTORY)
  codeIdList = getString(Cmd.OB_ASP_ID_LIST).lower()
  if codeIdList == 'all':
    allCodeIds = True
  else:
    allCodeIds = False
    codeIds = codeIdList.replace(',', ' ').split()
    for codeId in codeIds:
      if not codeId.isdigit():
        Cmd.Backup()
        usageErrorExit(Msg.INVALID_ENTITY.format(Ent.Singular(Ent.APPLICATION_SPECIFIC_PASSWORD), Msg.MUST_BE_NUMERIC))
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    if allCodeIds:
      try:
        asps = callGAPIitems(cd.asps(), 'list', 'items',
                             throwReasons=[GAPI.USER_NOT_FOUND],
                             userKey=user, fields='items(codeId)')
        codeIds = [asp['codeId'] for asp in asps]
      except GAPI.userNotFound:
        entityUnknownWarning(Ent.USER, user, i, count)
        continue
    jcount = len(codeIds)
    entityPerformActionNumItems([Ent.USER, user], jcount, Ent.APPLICATION_SPECIFIC_PASSWORD, i, count)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
      continue
    Ind.Increment()
    j = 0
    for codeId in codeIds:
      j += 1
      try:
        callGAPI(cd.asps(), 'delete',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_PARAMETER, GAPI.FORBIDDEN],
                 userKey=user, codeId=codeId)
        entityActionPerformed([Ent.USER, user, Ent.APPLICATION_SPECIFIC_PASSWORD, codeId], j, jcount)
      except (GAPI.invalid, GAPI.invalidParameter, GAPI.forbidden) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.APPLICATION_SPECIFIC_PASSWORD, codeId], str(e), j, jcount)
      except GAPI.userNotFound:
        entityUnknownWarning(Ent.USER, user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> print asps|applicationspecificpasswords [todrive <ToDriveAttribute>*]
#	[oneitemperrow]
# gam <UserTypeEntity> show asps|applicationspecificpasswords
def printShowASPs(users):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['User']) if Act.csvFormat() else None
  oneItemPerRow = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif csvPF and myarg == 'oneitemperrow':
      oneItemPerRow = True
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    if csvPF:
      printGettingEntityItemForWhom(Ent.APPLICATION_SPECIFIC_PASSWORD, user, i, count)
    try:
      asps = callGAPIitems(cd.asps(), 'list', 'items',
                           throwReasons=[GAPI.USER_NOT_FOUND],
                           userKey=user)
      if not csvPF:
        _showASPs(user, asps, i, count)
      else:
        for asp in asps:
          asp.pop('userKey', None)
          if asp['creationTime'] == '0':
            asp['creationTime'] = UNKNOWN
          else:
            asp['creationTime'] = formatLocalTimestamp(asp['creationTime'])
          if asp['lastTimeUsed'] == '0':
            asp['lastTimeUsed'] = GC.NEVER
          else:
            asp['lastTimeUsed'] = formatLocalTimestamp(asp['lastTimeUsed'])
        if not oneItemPerRow:
          csvPF.WriteRowTitles(flattenJSON({'asps': asps}, flattened={'User': user}))
        else:
          for asp in asps:
            csvPF.WriteRowTitles(flattenJSON({'asp': asp}, flattened={'User': user}))
    except GAPI.userNotFound:
      entityUnknownWarning(Ent.USER, user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Application Specific Passwords')

def _showBackupCodes(user, codes, i, count):
  Act.Set(Act.SHOW)
  jcount = 0
  for code in codes:
    if code.get('verificationCode'):
      jcount += 1
  entityPerformActionNumItems([Ent.USER, user], jcount, Ent.BACKUP_VERIFICATION_CODES, i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
    return
  Ind.Increment()
  j = 0
  for code in codes:
    j += 1
    printKeyValueList([f'{j:2}', code.get('verificationCode')])
  Ind.Decrement()

# gam <UserTypeEntity> update backupcodes|verificationcodes
def updateBackupCodes(users):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    userSuspended = checkUserSuspended(cd, user, Ent.USER, i, count)
    if userSuspended is None:
      continue
    if not userSuspended:
      try:
        callGAPI(cd.verificationCodes(), 'generate',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_INPUT],
                 userKey=user)
        codes = callGAPIitems(cd.verificationCodes(), 'list', 'items',
                              throwReasons=[GAPI.USER_NOT_FOUND],
                              userKey=user, fields='items(verificationCode)')
        _showBackupCodes(user, codes, i, count)
      except GAPI.userNotFound:
        entityUnknownWarning(Ent.USER, user, i, count)
      except (GAPI.invalid, GAPI.invalidInput) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None], str(e), i, count)
    else:
      entityActionNotPerformedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None],
                                      Msg.IS_SUSPENDED_NO_BACKUPCODES, i, count)

# gam <UserTypeEntity> delete backupcodes|verificationcodes
def deleteBackupCodes(users):
  cd = buildGAPIObject(API.DIRECTORY)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    userSuspended = checkUserSuspended(cd, user, Ent.USER, i, count)
    if userSuspended is None:
      continue
    if not userSuspended:
      try:
        callGAPI(cd.verificationCodes(), 'invalidate',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.INVALID, GAPI.INVALID_INPUT],
                 userKey=user)
        printEntityKVList([Ent.USER, user], [Ent.Plural(Ent.BACKUP_VERIFICATION_CODES), '', 'Invalidated'], i, count)
      except GAPI.userNotFound:
        entityUnknownWarning(Ent.USER, user, i, count)
      except (GAPI.invalid, GAPI.invalidInput) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None], str(e), i, count)
    else:
      entityActionNotPerformedWarning([Ent.USER, user, Ent.BACKUP_VERIFICATION_CODES, None],
                                      Msg.IS_SUSPENDED_NO_BACKUPCODES, i, count)

# gam <UserTypeEntity> print backupcodes|verificationcodes [todrive <ToDriveAttribute>*]
#	[delimiter <Character>] [countsonly]
# gam <UserTypeEntity> show backupcodes|verificationcodes
def printShowBackupCodes(users):
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['User', 'verificationCodesCount', 'verificationCodes']) if Act.csvFormat() else None
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  counts_only = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'countsonly':
      counts_only = True
    else:
      unknownArgumentExit()
  # if we're only getting counts, we don't want actual codes pulled down
  if counts_only:
    csvPF.RemoveTitles('verificationCodes')
    fields = 'items(etag)'
  else:
    fields = 'items(verificationCode)'
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = normalizeEmailAddressOrUID(user)
    if csvPF:
      printGettingEntityItemForWhom(Ent.BACKUP_VERIFICATION_CODES, user, i, count)
    try:
      codes = callGAPIitems(cd.verificationCodes(), 'list', 'items',
                            throwReasons=[GAPI.USER_NOT_FOUND],
                            userKey=user, fields=fields)
      if not csvPF:
        _showBackupCodes(user, codes, i, count)
      elif counts_only:
        csvPF.WriteRow({'User': user, 'verificationCodesCount': len(codes)})
      else:
        csvPF.WriteRow({'User': user,
                        'verificationCodesCount': len(codes),
                        'verificationCodes': delimiter.join([code['verificationCode'] for code in codes if 'verificationCode' in code])})
    except GAPI.userNotFound:
      entityUnknownWarning(Ent.USER, user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Backup Verification Codes')

