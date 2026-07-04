"""GAM Cloud Identity user invitation management."""

import re
import json

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    OrderBy,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getString,
    normalizeEmailAddressOrUID,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getTodriveOnly,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityPerformAction,
    getPageMessage,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printLine,
)
from gam.util.entity import _getCustomersCustomerIdWithC, convertUIDtoEmailAddress, getEntityArgument


from urllib.parse import quote_plus

def isolateCIUserInvitatonsEmail(name):
  ''' converts long name into email address'''
  return name.split('/')[-1]

def quotedCIUserInvitatonsEmail(customer, email):
  return f"{customer}/userinvitations/{quote_plus(email, safe='@')}"

def _getCIUserInvitationsEntity(ci=None, email=None):
  if ci is None:
    ci = buildGAPIObject(API.CLOUDIDENTITY_USERINVITATIONS)
  customer = _getCustomersCustomerIdWithC()
  if email is None:
    email = getString(Cmd.OB_EMAIL_ADDRESS)
  pattern = re.compile(rf'^{customer}/userinvitations/(.+)$')
  mg = pattern.match(email)
  if mg:
    email = mg.group(1)
  else:
    email = normalizeEmailAddressOrUID(email, noUid=True)
  return (quotedCIUserInvitatonsEmail(customer, email), email, ci)

def _getIsInvitableUser(ci, email):
  name, _, ci = _getCIUserInvitationsEntity(ci, email)
  try:
    result = callGAPI(ci.customers().userinvitations(), 'isInvitableUser',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                      name=name)
    return (result['isInvitableUser'], ci)
  except GAPI.notFound:
    return (False, ci)
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied):
    return (False, ci)

# gam send userinvitation <EmailAddress>
# gam cancel userinvitation <EmailAddress>
def doCIUserInvitationsAction():
  name, user, ci = _getCIUserInvitationsEntity()
  checkForExtraneousArguments()
  if Act.Get() == Act.CANCEL:
    action = 'cancel'
  else:
    Act.Set(Act.SEND)
    action = 'send'
  entityPerformAction([Ent.USER_INVITATION, user])
  try:
    result = callGAPI(ci.customers().userinvitations(), action,
                      throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                      name=name)
    name = result.get('response', {}).get('name')
    if name:
      result['response']['name'] = isolateCIUserInvitatonsEmail(name)
    Ind.Increment()
    showJSON(None, result)
    Ind.Decrement()
  except GAPI.notFound:
    entityUnknownWarning(Ent.USER_INVITATION, f'{user}')
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.USER_INVITATION, f'{user}'], str(e))

CI_USERINVITATION_TIME_OBJECTS = {'updateTime'}

def _showUserInvitation(invitation, FJQC, i=0, count=0):
  if FJQC is not None and FJQC.formatJSON:
    invitation['email'] = isolateCIUserInvitatonsEmail(invitation['name'])
    printLine(json.dumps(cleanJSON(invitation, timeObjects=CI_USERINVITATION_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.USER_INVITATION, isolateCIUserInvitatonsEmail(invitation['name'])], i, count)
  Ind.Increment()
  showJSON(None, invitation, timeObjects=CI_USERINVITATION_TIME_OBJECTS)
  Ind.Decrement()

# gam check userinvitation|isinvitable <EmailAddress>
def doCheckCIUserInvitations():
  name, user, ci = _getCIUserInvitationsEntity()
  checkForExtraneousArguments()
  try:
    result = callGAPI(ci.customers().userinvitations(), 'isInvitableUser',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                      name=name)
    printEntity([Ent.USER_INVITATION, user])
    Ind.Increment()
    showJSON(None, result)
    Ind.Decrement()
  except GAPI.notFound:
    entityUnknownWarning(Ent.USER_INVITATION, f'{user}')
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.USER_INVITATION, f'{user}'], str(e))

def infoCIUserInvitations(name, user, ci, FJQC):
  try:
    invitation = callGAPI(ci.customers().userinvitations(), 'get',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                          name=name)
    _showUserInvitation(invitation, FJQC)
  except GAPI.notFound:
    entityUnknownWarning(Ent.USER_INVITATION, f'{user}')
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.USER_INVITATION, f'{user}'], str(e))

# gam info userinvitation <EmailAddress> [formatjson]
def doInfoCIUserInvitations():
  name, user, ci = _getCIUserInvitationsEntity()
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  infoCIUserInvitations(name, user, ci, FJQC)

CI_USERINVITATION_ORDERBY_CHOICE_MAP = {
  'email': 'email',
  'updatetime': 'update_time',
  }

CI_USERINVITATION_STATE_CHOICE_MAP = {
  'accepted': 'ACCEPTED',
  'declined': 'DECLINED',
  'invited': 'INVITED',
  'notyetsent': 'NOT_YET_SENT',
  }

# gam show userinvitations
#	[state notyetsent|invited|accepted|declined]
#	[orderby email|updatetime [ascending|descending]]
#	[formatjson]
# gam print userinvitations [todrive <ToDriveAttribute>*]
#	[state notyetsent|invited|accepted|declined]
#	[orderby email|updatetime [ascending|descending]]
#	[[formatjson [quotechar <Character>]]
def doPrintShowCIUserInvitations():
  def _printUserInvitation(invitation):
    invitation['email'] = isolateCIUserInvitatonsEmail(invitation['name'])
    row = flattenJSON(invitation, timeObjects=CI_USERINVITATION_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'email': invitation['email'],
                              'JSON': json.dumps(cleanJSON(invitation, timeObjects=CI_USERINVITATION_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  ci = buildGAPIObject(API.CLOUDIDENTITY_USERINVITATIONS)
  customer = _getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['email']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  OBY = OrderBy(CI_USERINVITATION_ORDERBY_CHOICE_MAP)
  ifilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'state':
      state = getChoice(CI_USERINVITATION_STATE_CHOICE_MAP, mapChoice=True)
      ifilter = f"state=='{state}'"
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  printGettingAllAccountEntities(Ent.USER_INVITATION, ifilter)
  pageMessage = getPageMessage()
  try:
    invitations = callGAPIpages(ci.customers().userinvitations(), 'list', 'userInvitations',
                                throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                                pageMessage=pageMessage,
                                parent=customer, filter=ifilter, orderBy=OBY.orderBy)
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.USER_INVITATION, None], str(e))
    return
  if not csvPF:
    jcount = len(invitations)
    performActionNumItems(jcount, Ent.USER_INVITATION)
    Ind.Increment()
    j = 0
    for invitation in invitations:
      j += 1
      _showUserInvitation(invitation, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for invitation in invitations:
      _printUserInvitation(invitation)
  if csvPF:
    csvPF.writeCSVfile('User Invitations')

# gam <UserTypeEntity> check isinvitable [todrive <ToDriveAttribute>*]
# /batch is broken for Cloud Identity. Once fixed move this to using batch.
# Current serial implementation will be SLOW...
def checkCIUserIsInvitable(users):
  ci = buildGAPIObject(API.CLOUDIDENTITY_USERINVITATIONS)
  customer = _getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['invitableUsers'])
  getTodriveOnly(csvPF)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user = convertUIDtoEmailAddress(user)
    name = quotedCIUserInvitatonsEmail(customer, user)
    try:
      result = callGAPI(ci.customers().userinvitations(), 'isInvitableUser',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.PERMISSION_DENIED],
                        name=name)
      if result.get('isInvitableUser'):
        csvPF.WriteRow({'invitableUsers': user})
    except GAPI.notFound:
      entityUnknownWarning(Ent.USER_INVITATION, f'{user}', i, count)
    except (GAPI.invalid, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.USER_INVITATION, user], str(e), i, count)
      return
  csvPF.writeCSVfile('Invitable Users')

INBOUNDSSO_INPUT_MODE_CHOICE_MAP = {
  'saml': 'saml',
  'samlsso': 'saml',
  'oidc': 'oidc',
  'oidcsso': 'oidc',
}

INBOUNDSSO_OUTPUT_MODE_CHOICE_MAP = {
  'all': 'all',
  'saml': 'saml',
  'samlsso': 'saml',
  'oidc': 'oidc',
  'oidcsso': 'oidc',
}

INBOUNDSSO_ALL_SAML = {'all', 'saml'}
INBOUNDSSO_ALL_OIDC = {'all', 'oidc'}

INBOUNDSSO_MODE_CHOICE_MAP = {
  'ssooff': 'SSO_OFF',
  'saml': 'SAML_SSO',
  'samlsso': 'SAML_SSO',
  'oidc': 'OIDC_SSO',
  'oidcsso': 'OIDC_SSO',
  'domainwidesamlifenabled': 'DOMAIN_WIDE_SAML_IF_ENABLED'
  }

