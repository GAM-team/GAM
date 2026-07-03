"""GAM contact delegate management."""

import sys

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

def _validateUserGetDelegateList(cd, user, i, count, entity):
  if entity['dict']:
    entityList = entity['dict'][user]
  else:
    entityList = entity['list']
  user = _getMain().checkUserExists(cd, user, Ent.USER, i, count)
  if not user:
    return (user, None, 0)
  jcount = len(entityList)
  _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, entity['item'], i, count)
  if jcount == 0:
    _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
  return (user, entityList, jcount)

def _getDelegateName(cd, delegateEmail, delegateNames):
  if delegateEmail in delegateNames:
    return delegateNames[delegateEmail]
  try:
    result = _getMain().callGAPI(cd.users(), 'get',
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
  condel = _getMain().buildGAPIObject(API.CONTACTDELEGATION)
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  function = 'delete' if Act.Get() == Act.DELETE else 'create'
  delegateEntity = _getMain().getUserObjectEntity(Cmd.OB_USER_ENTITY, Ent.DELEGATE)
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, delegates, jcount = _validateUserGetDelegateList(cd, user, i, count, delegateEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for delegate in delegates:
      j += 1
      delegateEmail = _getMain().checkUserExists(cd, delegate, Ent.CONTACT_DELEGATE, j, jcount)
      if not delegateEmail:
        continue
      try:
        if function == 'create':
          _getMain().callGAPI(condel.delegates(), function,
                   throwReasons=GAPI.CONTACT_DELEGATE_THROW_REASONS,
                   user=user, body={'email': delegateEmail})
        else:
          _getMain().callGAPI(condel.delegates(), function,
                   throwReasons=GAPI.CONTACT_DELEGATE_THROW_REASONS,
                   user=user, delegate=delegateEmail)
        _getMain().entityActionPerformed([Ent.USER, user, Ent.CONTACT_DELEGATE, delegateEmail], j, jcount)
      except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.CONTACT_DELEGATE, delegateEmail], str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.badRequest):
        _getMain().userContactDelegateServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()

# gam <UserTypeEntity> print contactdelegates [todrive <ToDriveAttribute>*] [shownames]
# gam <UserTypeEntity> show contactdelegates [shownames] [csv]
def printShowContactDelegates(users):
  condel = _getMain().buildGAPIObject(API.CONTACTDELEGATION)
  titlesList = ['User', 'delegateAddress']
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvStyle = showNames = False
  delegateNames = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif not csvPF and myarg == 'csv':
      csvStyle = True
    elif myarg == 'shownames':
      titlesList = ['User', 'delegateName', 'delegateAddress']
      showNames = True
    else:
      _getMain().unknownArgumentExit()
  if csvPF:
    csvPF.AddTitles(titlesList)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user = _getMain().checkUserExists(cd, user, Ent.USER, i, count)
    if not user:
      continue
    _getMain().printGettingAllEntityItemsForWhom(Ent.CONTACT_DELEGATE, user, i, count)
    try:
      delegates = _getMain().callGAPIpages(condel.delegates(), 'list', 'delegates',
                                pageMessage=_getMain().getPageMessageForWhom(),
                                throwReasons=GAPI.CONTACT_DELEGATE_THROW_REASONS,
                                user=user)
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.CONTACT_DELEGATE, None], str(e), i, count)
      continue
    except (GAPI.serviceNotAvailable, GAPI.badRequest):
      _getMain().userContactDelegateServiceNotEnabledWarning(user, i, count)
      continue
    if not csvPF:
      if not csvStyle:
        jcount = len(delegates)
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.CONTACT_DELEGATE, i, count)
        Ind.Increment()
        j = 0
        for delegate in delegates:
          j += 1
          delegateEmail = delegate['email']
          if showNames:
            _getMain().printEntity([Ent.CONTACT_DELEGATE, _getDelegateName(cd, delegateEmail, delegateNames)], j, jcount)
            Ind.Increment()
            _getMain().printKeyValueList(['Delegate Email', delegateEmail])
            Ind.Decrement()
          else:
            _getMain().printEntity([Ent.DELEGATE, delegateEmail], j, jcount)
        Ind.Decrement()
      else:
        j = 0
        for delegate in delegates:
          j += 1
          delegateEmail = delegate['email']
          if showNames:
            _getMain().writeStdout(f'{user},{_getDelegateName(cd, delegateEmail, delegateNames)},{delegateEmail}\n')
          else:
            _getMain().writeStdout(f'{user},{delegateEmail}\n')
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
