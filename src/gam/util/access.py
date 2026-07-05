"""GAM access-error and entity-warning utilities.

Access-error diagnostics, API access denied handlers,
and entity warning functions.
"""


from gamlib import action
from gamlib import api as API
from gamlib import settings as GC
from gamlib import entity
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import indent
from gamlib import msgs as Msg
from gam.constants import API_ACCESS_DENIED_RC, INVALID_DOMAIN_RC
from util.api import buildGAPIObject
from util.api_call import callGAPI
from util.args import getEmailAddressDomain, getPhraseDNEorSNA
from util.display import ENTITY_DOES_NOT_EXIST_RC, ENTITY_DUPLICATE_RC, entityActionFailedWarning, entityDoesNotExistWarning, entityServiceNotApplicableWarning
from util.output import currentCountNL, formatKeyValueList, setSysExitRC, systemErrorExit, writeStderr




Act = action.GamAction()
Ent = entity.GamEntity()
Ind = indent.GamIndent()


# Something's wrong with CustomerID??
def accessErrorMessage(cd, errMsg=None):
  if cd is None:
    cd = buildGAPIObject(API.DIRECTORY)
  try:
    callGAPI(cd.customers(), 'get',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerKey=GC.Values[GC.CUSTOMER_ID], fields='id')
  except (GAPI.badRequest, GAPI.invalidInput):
    return formatKeyValueList('',
                              [Ent.Singular(Ent.CUSTOMER_ID), GC.Values[GC.CUSTOMER_ID],
                               Msg.INVALID],
                              '')
  except GAPI.resourceNotFound:
    return formatKeyValueList('',
                              [Ent.Singular(Ent.CUSTOMER_ID), GC.Values[GC.CUSTOMER_ID],
                               Msg.DOES_NOT_EXIST],
                              '')
  except (GAPI.forbidden, GAPI.permissionDenied):
    return formatKeyValueList('',
                              Ent.FormatEntityValueList([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID],
                                                         Ent.DOMAIN, GC.Values[GC.DOMAIN],
                                                         Ent.USER, GM.Globals[GM.ADMIN]])+[Msg.ACCESS_FORBIDDEN],
                              '')
  if errMsg:
    return formatKeyValueList('',
                              [Ent.Singular(Ent.CUSTOMER_ID), GC.Values[GC.CUSTOMER_ID],
                               errMsg],
                              '')
  return None

def accessErrorExit(cd, errMsg=None):
  systemErrorExit(INVALID_DOMAIN_RC, accessErrorMessage(cd or buildGAPIObject(API.DIRECTORY), errMsg))

def accessErrorExitNonDirectory(api, errMsg):
  systemErrorExit(API_ACCESS_DENIED_RC,
                  formatKeyValueList('',
                                     Ent.FormatEntityValueList([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID],
                                                                Ent.DOMAIN, GC.Values[GC.DOMAIN],
                                                                Ent.API, api])+[errMsg],
                                     ''))

def checkEntityDNEorAccessErrorExit(cd, entityType, entityName, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    systemErrorExit(INVALID_DOMAIN_RC, message)
  entityDoesNotExistWarning(entityType, entityName, i, count)

def checkEntityAFDNEorAccessErrorExit(cd, entityType, entityName, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    systemErrorExit(INVALID_DOMAIN_RC, message)
  entityActionFailedWarning([entityType, entityName], Msg.DOES_NOT_EXIST, i, count)

def checkEntityItemValueAFDNEorAccessErrorExit(cd, entityType, entityName, itemType, itemValue, i=0, count=0):
  message = accessErrorMessage(cd)
  if message:
    systemErrorExit(INVALID_DOMAIN_RC, message)
  entityActionFailedWarning([entityType, entityName, itemType, itemValue], Msg.DOES_NOT_EXIST, i, count)

def entityUnknownWarning(entityType, entityName, i=0, count=0):
  domain = getEmailAddressDomain(entityName)
  if (domain.endswith(GC.Values[GC.DOMAIN])) or (domain.endswith('google.com')):
    entityDoesNotExistWarning(entityType, entityName, i, count)
  else:
    entityServiceNotApplicableWarning(entityType, entityName, i, count)

def entityOrEntityUnknownWarning(entity1Type, entity1Name, entity2Type, entity2Name, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [f'{Msg.EITHER} {Ent.Singular(entity1Type)}', entity1Name, getPhraseDNEorSNA(entity1Name), None,
                                  f'{Msg.OR} {Ent.Singular(entity2Type)}', entity2Name, getPhraseDNEorSNA(entity2Name)],
                                 currentCountNL(i, count)))

def duplicateAliasGroupUserWarning(cd, entityValueList, i=0, count=0):
  email = entityValueList[1]
  try:
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=email, fields='id,primaryEmail')
    if (result['primaryEmail'].lower() == email) or (result['id'] == email):
      kvList = [Ent.USER, email]
    else:
      kvList = [Ent.USER_ALIAS, email, Ent.USER, result['primaryEmail']]
  except (GAPI.userNotFound, GAPI.badRequest,
          GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.backendError, GAPI.systemError):
    try:
      result = callGAPI(cd.groups(), 'get',
                        throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                        groupKey=email, fields='id,email')
      if (result['email'].lower() == email) or (result['id'] == email):
        kvList = [Ent.GROUP, email]
      else:
        kvList = [Ent.GROUP_ALIAS, email, Ent.GROUP, result['email']]
    except (GAPI.groupNotFound,
            GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest):
      kvList = [Ent.EMAIL, email]
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+
                                 [Act.Failed(), Msg.DUPLICATE]+
                                 Ent.FormatEntityValueList(kvList),
                                 currentCountNL(i, count)))
  setSysExitRC(ENTITY_DUPLICATE_RC)
  return kvList[0]
