"""GAM Google Analytics commands."""

import json

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIServiceObject, callGAPIpages
from gam.util.args import getArgument, getBoolean, getInteger, getString
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printLine,
    userAnalyticsServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import missingArgumentExit
from gam.cmd.reseller import ANALYTIC_ENTITY_MAP


def printShowAnalyticItems(users, entityType):
  analyticEntityMap = ANALYTIC_ENTITY_MAP[entityType]
  csvPF = CSVPrintFile(analyticEntityMap['titles'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  kwargs = {'pageSize': analyticEntityMap['pageSize']}
  if entityType in {Ent.ANALYTIC_ACCOUNT, Ent.ANALYTIC_PROPERTY}:
    kwargs['showDeleted'] = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'maxresults':
      kwargs['pageSize'] = getInteger(minVal=1, maxVal=analyticEntityMap['maxPageSize'])
    elif entityType in {Ent.ANALYTIC_ACCOUNT, Ent.ANALYTIC_PROPERTY} and myarg == 'showdeleted':
      kwargs['showDeleted'] = getBoolean()
    elif entityType == Ent.ANALYTIC_PROPERTY and myarg == 'filter':
      kwargs['filter'] = getString(Cmd.OB_STRING)
    elif entityType == Ent.ANALYTIC_DATASTREAM and myarg == 'parent':
      kwargs['parent'] = getString(Cmd.OB_STRING)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if entityType == Ent.ANALYTIC_PROPERTY and 'filter' not in kwargs:
    missingArgumentExit('filter')
  if entityType == Ent.ANALYTIC_DATASTREAM and 'parent' not in kwargs:
    missingArgumentExit('parent')
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(analyticEntityMap['JSONtitles'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, analytics = buildGAPIServiceObject(API.ANALYTICS_ADMIN, user, i, count)
    if not analytics:
      continue
    if entityType == Ent.ANALYTIC_ACCOUNT:
      service = analytics.accounts()
    elif entityType == Ent.ANALYTIC_ACCOUNT_SUMMARY:
      service = analytics.accountSummaries()
    elif entityType == Ent.ANALYTIC_DATASTREAM:
      service = analytics.properties().dataStreams()
    else: #  entityType == Ent.ANALYTIC_PROPERTY:
      service = analytics.properties()
    if csvPF:
      printGettingAllEntityItemsForWhom(entityType, user, i, count)
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    try:
      results = callGAPIpages(service, 'list', analyticEntityMap['items'],
                              pageMessage=pageMessage,
                              throwReasons=[GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.INTERNAL_ERROR,
                                            GAPI.SERVICE_NOT_AVAILABLE],
                              **kwargs)
    except (GAPI.permissionDenied, GAPI.invalidArgument, GAPI.badRequest, GAPI.internalError) as e:
      entityActionFailedWarning([Ent.USER, user, entityType, None], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      userAnalyticsServiceNotEnabledWarning(user, i, count)
      continue
    if not csvPF:
      jcount = len(results)
      if not FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user], jcount, entityType)
      Ind.Increment()
      j = 0
      for item in results:
        j += 1
        if not FJQC.formatJSON:
          printEntity([entityType, item['name']], j, jcount)
          Ind.Increment()
          showJSON(None, item, timeObjects=analyticEntityMap['timeObjects'])
          Ind.Decrement()
        else:
          printLine(json.dumps(cleanJSON(item, timeObjects=analyticEntityMap['timeObjects']),
                               ensure_ascii=False, sort_keys=False))
      Ind.Decrement()
    elif results:
      for item in results:
        row = flattenJSON(item, flattened={'User': user}, timeObjects=analyticEntityMap['timeObjects'])
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {'User': user, 'name': item['name'], 'displayName': item['displayName']}
          for field in analyticEntityMap['JSONtitles'][2:-1]:
            row[field] = item[field]
          row['JSON'] = json.dumps(cleanJSON(item, timeObjects=analyticEntityMap['timeObjects']),
                                   ensure_ascii=False, sort_keys=True)
          csvPF.WriteRowNoFilter(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile(Ent.Plural(entityType))

# gam <UserTypeEntity> print analyticaccounts [todrive <ToDriveAttribute>*]
#	[maxresults <Integer>] [showdeleted [<Boolean>]]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show analyticaccounts
#	[maxresults <Integer>] [showdeleted [<Boolean>]]
#	[formatjson]
def printShowAnalyticAccounts(users):
  printShowAnalyticItems(users, Ent.ANALYTIC_ACCOUNT)

# gam <UserTypeEntity> print analyticaccountsummaries [todrive <ToDriveAttribute>*]
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show analyticaccountsummaries
#	[maxresults <Integer>]
#	[formatjson]
def printShowAnalyticAccountSummaries(users):
  printShowAnalyticItems(users, Ent.ANALYTIC_ACCOUNT_SUMMARY)

# gam <UserTypeEntity> print analyticproperties [todrive <ToDriveAttribute>*]
#	filter <String>
#	[maxresults <Integer>] [showdeleted [<Boolean>]]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show analyticproperties
#	filter <String>
#	[maxresults <Integer>] [showdeleted [<Boolean>]]
#	[formatjson]
def printShowAnalyticProperties(users):
  printShowAnalyticItems(users, Ent.ANALYTIC_PROPERTY)

# gam <UserTypeEntity> print analyticdatastreams [todrive <ToDriveAttribute>*]
#	parent <String>
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show analyticdatastreams
#	parent <String>
#	[maxresults <Integer>]
#	[formatjson]
def printShowAnalyticDatastreams(users):
  printShowAnalyticItems(users, Ent.ANALYTIC_DATASTREAM)

# gam create domainalias|aliasdomain <DomainAlias> <DomainName>
