"""GAM access-error and entity-warning utilities.

Access-error diagnostics, API access denied handlers,
and entity warning functions.
"""

import sys

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg


_gam = lambda: sys.modules['gam']


Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()


# Something's wrong with CustomerID??
def accessErrorMessage(cd, errMsg=None):
  if cd is None:
    cd = _gam().buildGAPIObject(API.DIRECTORY)
  try:
    _gam().callGAPI(cd.customers(), 'get',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerKey=GC.Values[GC.CUSTOMER_ID], fields='id')
  except (GAPI.badRequest, GAPI.invalidInput):
    return _gam().formatKeyValueList('',
                              [Ent.Singular(Ent.CUSTOMER_ID), GC.Values[GC.CUSTOMER_ID],
                               Msg.INVALID],
                              '')
  except GAPI.resourceNotFound:
    return _gam().formatKeyValueList('',
                              [Ent.Singular(Ent.CUSTOMER_ID), GC.Values[GC.CUSTOMER_ID],
                               Msg.DOES_NOT_EXIST],
                              '')
  except (GAPI.forbidden, GAPI.permissionDenied):
    return _gam().formatKeyValueList('',
                              Ent.FormatEntityValueList([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID],
                                                         Ent.DOMAIN, GC.Values[GC.DOMAIN],
                                                         Ent.USER, GM.Globals[GM.ADMIN]])+[Msg.ACCESS_FORBIDDEN],
                              '')
  if errMsg:
    return _gam().formatKeyValueList('',
                              [Ent.Singular(Ent.CUSTOMER_ID), GC.Values[GC.CUSTOMER_ID],
                               errMsg],
                              '')
  return None

def accessErrorExit(cd, errMsg=None):
  _gam().systemErrorExit(_gam().INVALID_DOMAIN_RC, accessErrorMessage(cd or _gam().buildGAPIObject(API.DIRECTORY), errMsg))

def accessErrorExitNonDirectory(api, errMsg):
  _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC,
                  _gam().formatKeyValueList('',
                                     Ent.FormatEntityValueList([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID],
                                                                Ent.DOMAIN, GC.Values[GC.DOMAIN],
                                                                Ent.API, api])+[errMsg],
                                     ''))

def ClientAPIAccessDeniedExit(errMsg=None):
  if errMsg is None:
    _gam().stderrErrorMsg(Msg.API_ACCESS_DENIED)
    missingScopes = API.getClientScopesSet(GM.Globals[GM.CURRENT_CLIENT_API])-GM.Globals[GM.CURRENT_CLIENT_API_SCOPES]
    if missingScopes:
      _gam().writeStderr(Msg.API_CHECK_CLIENT_AUTHORIZATION.format(GM.Globals[GM.OAUTH2_CLIENT_ID],
                                                            ','.join(sorted(missingScopes))))
    _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC, None)
  else:
    _gam().stderrErrorMsg(errMsg)
    _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC, Msg.REAUTHENTICATION_IS_NEEDED)

def SvcAcctAPIAccessDenied():
  _gam()._getSvcAcctData()
  if (GM.Globals[GM.CURRENT_SVCACCT_API] == API.GMAIL and
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES] and
      GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES][0] == API.GMAIL_SEND_SCOPE):
    _gam().systemErrorExit(_gam().OAUTH2SERVICE_JSON_REQUIRED_RC, Msg.NO_SVCACCT_ACCESS_ALLOWED)
  _gam().stderrErrorMsg(Msg.API_ACCESS_DENIED)
  apiOrScopes = API.getAPIName(GM.Globals[GM.CURRENT_SVCACCT_API]) if GM.Globals[GM.CURRENT_SVCACCT_API] else ','.join(sorted(GM.Globals[GM.CURRENT_SVCACCT_API_SCOPES]))
  _gam().writeStderr(Msg.API_CHECK_SVCACCT_AUTHORIZATION.format(GM.Globals[GM.OAUTH2SERVICE_JSON_DATA]['client_id'],
                                                         apiOrScopes,
                                                         GM.Globals[GM.CURRENT_SVCACCT_USER] or _gam()._getAdminEmail()))
def SvcAcctAPIAccessDeniedExit():
  SvcAcctAPIAccessDenied()
  _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC, None)

def SvcAcctAPIDisabledExit():
  if not GM.Globals[GM.CURRENT_SVCACCT_USER] and GM.Globals[GM.CURRENT_CLIENT_API]:
    ClientAPIAccessDeniedExit()
  if GM.Globals[GM.CURRENT_SVCACCT_API]:
    _gam().stderrErrorMsg(Msg.SERVICE_ACCOUNT_API_DISABLED.format(API.getAPIName(GM.Globals[GM.CURRENT_SVCACCT_API])))
    _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC, None)
  _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC, Msg.API_ACCESS_DENIED)

def APIAccessDeniedExit():
  if not GM.Globals[GM.CURRENT_SVCACCT_USER] and GM.Globals[GM.CURRENT_CLIENT_API]:
    ClientAPIAccessDeniedExit()
  if GM.Globals[GM.CURRENT_SVCACCT_API]:
    SvcAcctAPIAccessDeniedExit()
  _gam().systemErrorExit(_gam().API_ACCESS_DENIED_RC, Msg.API_ACCESS_DENIED)

def checkEntityDNEorAccessErrorExit(cd, entityType, entityName, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    _gam().systemErrorExit(_gam().INVALID_DOMAIN_RC, message)
  _gam().entityDoesNotExistWarning(entityType, entityName, i, count)

def checkEntityAFDNEorAccessErrorExit(cd, entityType, entityName, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    _gam().systemErrorExit(_gam().INVALID_DOMAIN_RC, message)
  _gam().entityActionFailedWarning([entityType, entityName], Msg.DOES_NOT_EXIST, i, count)

def checkEntityItemValueAFDNEorAccessErrorExit(cd, entityType, entityName, itemType, itemValue, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    _gam().systemErrorExit(_gam().INVALID_DOMAIN_RC, message)
  _gam().entityActionFailedWarning([entityType, entityName, itemType, itemValue], Msg.DOES_NOT_EXIST, i, count)

def entityUnknownWarning(entityType, entityName, i=0, count=0):
  domain = _gam().getEmailAddressDomain(entityName)
  if (domain.endswith(GC.Values[GC.DOMAIN])) or (domain.endswith('google.com')):
    _gam().entityDoesNotExistWarning(entityType, entityName, i, count)
  else:
    _gam().entityServiceNotApplicableWarning(entityType, entityName, i, count)

def entityOrEntityUnknownWarning(entity1Type, entity1Name, entity2Type, entity2Name, i=0, count=0):
  _gam().setSysExitRC(_gam().ENTITY_DOES_NOT_EXIST_RC)
  _gam().writeStderr(_gam().formatKeyValueList(Ind.Spaces(),
                                 [f'{Msg.EITHER} {Ent.Singular(entity1Type)}', entity1Name, _gam().getPhraseDNEorSNA(entity1Name), None,
                                  f'{Msg.OR} {Ent.Singular(entity2Type)}', entity2Name, _gam().getPhraseDNEorSNA(entity2Name)],
                                 _gam().currentCountNL(i, count)))

def duplicateAliasGroupUserWarning(cd, entityValueList, i=0, count=0):
  email = entityValueList[1]
  try:
    result = _gam().callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=email, fields='id,primaryEmail')
    if (result['primaryEmail'].lower() == email) or (result['id'] == email):
      kvList = [Ent.USER, email]
    else:
      kvList = [Ent.USER_ALIAS, email, Ent.USER, result['primaryEmail']]
  except (GAPI.userNotFound, GAPI.badRequest,
          GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.backendError, GAPI.systemError):
    try:
      result = _gam().callGAPI(cd.groups(), 'get',
                        throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                        groupKey=email, fields='id,email')
      if (result['email'].lower() == email) or (result['id'] == email):
        kvList = [Ent.GROUP, email]
      else:
        kvList = [Ent.GROUP_ALIAS, email, Ent.GROUP, result['email']]
    except (GAPI.groupNotFound,
            GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest):
      kvList = [Ent.EMAIL, email]
  _gam().writeStderr(_gam().formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+
                                 [Act.Failed(), Msg.DUPLICATE]+
                                 Ent.FormatEntityValueList(kvList),
                                 _gam().currentCountNL(i, count)))
  _gam().setSysExitRC(_gam().ENTITY_DUPLICATE_RC)
  return kvList[0]
