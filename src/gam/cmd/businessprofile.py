"""GAM Business Profile account management."""

from gamlib import api as API
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPIpages
from gam.util.args import getArgument, getChoice
from gam.util.csv_pf import CSVPrintFile, flattenJSON, showJSON
from gam.util.display import (
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printGettingAllEntityItemsForWhom,
    printKeyValueListWithCount,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import unknownArgumentExit
from gam.util.access import accessErrorExitNonDirectory

PROFILE_ACCOUNT_TYPE_MAP = {
  'locationgroup': 'LOCATION_GROUP',
  'organization': 'ORGANIZATION',
  'personal': 'PERSONAL',
  'usergroup': 'USER_GROUP',
  }

# gam <UserTypeEntity> show businessprofileaccounts
#	[type locationgroup|organization|personal|usergroup]
# gam <UserTypeEntity> print businessprofileaccounts [todrive <ToDriveAttribute>*]
#	[type locationgroup|organization|personal|usergroup]
def printShowBusinessProfileAccounts(users):
  csvPF = CSVPrintFile(['User', 'name', 'accountName']) if Act.csvFormat() else None
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'type':
      kwargs['filter'] = f'type={getChoice(PROFILE_ACCOUNT_TYPE_MAP, mapChoice=True)}'
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, bp = buildGAPIServiceObject(API.BUSINESSACCOUNTMANAGEMENT, user, i, count)
    if not bp:
      continue
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.BUSINESS_PROFILE_ACCOUNT, user, i, count, query=kwargs.get('filter'))
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    try:
      accounts = callGAPIpages(bp.accounts(), 'list', 'accounts',
                               pageMessage=pageMessage,
                               throwReasons=[GAPI.PERMISSION_DENIED],
                               **kwargs)
    except GAPI.permissionDenied as e:
      accessErrorExitNonDirectory(API.BUSINESSACCOUNTMANAGEMENT, str(e))
    if not csvPF:
      jcount = len(accounts)
      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.BUSINESS_PROFILE_ACCOUNT, i, count)
      Ind.Increment()
      j = 0
      for account in sorted(accounts, key=lambda k: k['name']):
        j += 1
        printKeyValueListWithCount(['Account', account['name']], j, jcount)
        Ind.Increment()
        showJSON(None, account)
        Ind.Decrement()
      Ind.Decrement()
    else:
      for account in accounts:
        row = flattenJSON(account, flattened={'User': user, 'name': account['name'], 'accountName': account['accountName']})
        csvPF.WriteRowTitles(row)
  if csvPF:
    csvPF.writeCSVfile('Business Profile Accounts')
