"""GAM contact delegate management."""


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import checkForExtraneousArguments, getArgument
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    userContactDelegateServiceNotEnabledWarning,
)
from gam.util.entity import checkUserExists, getEntityArgument, getUserObjectEntity
from gam.util.errors import unknownArgumentExit
from gam.util.output import setSysExitRC, writeStdout
from gam.constants import NO_ENTITIES_FOUND_RC


def _validateUserGetDelegateList(cd, user, i, count, entity):
  if entity['dict']:
    entityList = entity['dict'][user]
  else:
    entityList = entity['list']
  user = checkUserExists(cd, user, Ent.USER, i, count)
  if not user:
    return (user, None, 0)
  jcount = len(entityList)
  entityPerformActionNumItems([Ent.USER, user], jcount, entity['item'], i, count)
  if jcount == 0:
    setSysExitRC(NO_ENTITIES_FOUND_RC)
  return (user, entityList, jcount)

def _getDelegateName(cd, delegateEmail, delegateNames):
  if delegateEmail in delegateNames:
    return delegateNames[delegateEmail]
  try:
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=delegateEmail, fields='name(fullName)')
    delegateName = result.get('name', {'fullName': delegateEmail}).get('fullName', delegateEmail)
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError):
    delegateName = delegateEmail
  delegateNames[delegateEmail] = delegateName
  return delegateName

# gam <UserTypeEntity> create contactdelegate <UserEntity>
# gam <UserTypeEntity> delete contactdelegate <UserEntity>
def processContactDelegates(users):
  condel = buildGAPIObject(API.CONTACTDELEGATION)
  cd = buildGAPIObject(API.DIRECTORY)
  function = 'delete' if Act.Get() == Act.DELETE else 'create'
  delegateEntity = getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.DELEGATE)
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, delegates, jcount = _validateUserGetDelegateList(cd, user, i, count, delegateEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for delegate in delegates:
      j += 1
      delegateEmail = checkUserExists(cd, delegate, Ent.CONTACT_DELEGATE, j, jcount)
      if not delegateEmail:
        continue
      try:
        if function == 'create':
          callGAPI(condel.delegates(), function,
                   throwReasons=GAPI.CONTACT_DELEGATE_THROW_REASONS,
                   user=user, body={'email': delegateEmail})
        else:
          callGAPI(condel.delegates(), function,
                   throwReasons=GAPI.CONTACT_DELEGATE_THROW_REASONS,
                   user=user, delegate=delegateEmail)
        entityActionPerformed([Ent.USER, user, Ent.CONTACT_DELEGATE, delegateEmail], j, jcount)
      except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.CONTACT_DELEGATE, delegateEmail], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.badRequest):
        userContactDelegateServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()

# gam <UserTypeEntity> print contactdelegates [todrive <ToDriveAttribute>*] [shownames]
# gam <UserTypeEntity> show contactdelegates [shownames] [csv]
def printShowContactDelegates(users):
  condel = buildGAPIObject(API.CONTACTDELEGATION)
  titlesList = ['User', 'delegateAddress']
  csvPF = CSVPrintFile() if Act.csvFormat() else None
  cd = buildGAPIObject(API.DIRECTORY)
  csvStyle = showNames = False
  delegateNames = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif not csvPF and myarg == 'csv':
      csvStyle = True
    elif myarg == 'shownames':
      titlesList = ['User', 'delegateName', 'delegateAddress']
      showNames = True
    else:
      unknownArgumentExit()
  if csvPF:
    csvPF.AddTitles(titlesList)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = checkUserExists(cd, user, Ent.USER, i, count)
    if not user:
      continue
    printGettingAllEntityItemsForWhom(Ent.CONTACT_DELEGATE, user, i, count)
    try:
      delegates = callGAPIpages(condel.delegates(), 'list', 'delegates',
                                pageMessage=getPageMessageForWhom(),
                                throwReasons=GAPI.CONTACT_DELEGATE_THROW_REASONS,
                                user=user)
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.CONTACT_DELEGATE, None], str(e), i, count)
      continue
    except (GAPI.serviceNotAvailable, GAPI.badRequest):
      userContactDelegateServiceNotEnabledWarning(user, i, count)
      continue
    if not csvPF:
      if not csvStyle:
        jcount = len(delegates)
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CONTACT_DELEGATE, i, count)
        Ind.Increment()
        j = 0
        for delegate in delegates:
          j += 1
          delegateEmail = delegate['email']
          if showNames:
            printEntity([Ent.CONTACT_DELEGATE, _getDelegateName(cd, delegateEmail, delegateNames)], j, jcount)
            Ind.Increment()
            printKeyValueList(['Delegate Email', delegateEmail])
            Ind.Decrement()
          else:
            printEntity([Ent.DELEGATE, delegateEmail], j, jcount)
        Ind.Decrement()
      else:
        j = 0
        for delegate in delegates:
          j += 1
          delegateEmail = delegate['email']
          if showNames:
            writeStdout(f'{user},{_getDelegateName(cd, delegateEmail, delegateNames)},{delegateEmail}\n')
          else:
            writeStdout(f'{user},{delegateEmail}\n')
    elif delegates:
      if showNames:
        for delegate in delegates:
          csvPF.WriteRow({'User': user, 'delegateName': _getDelegateName(cd, delegate['email'], delegateNames),
                          'delegateAddress': delegate['email']})
      else:
        for delegate in delegates:
          csvPF.WriteRow({'User': user, 'delegateAddress': delegate['email']})
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Contact Delegates')

# CrOS commands utilities
