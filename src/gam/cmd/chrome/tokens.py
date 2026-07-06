"""GAM Chrome browser enrollment token management."""

import json

from gamlib import api as API
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
    getOrderBySortOrder,
    getString,
    getTimeOrDeltaFromNow,
    substituteQueryTimes,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    getPageMessage,
    invalidQuery,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printLine,
)
from gam.util.customer import _getCustomerIdNoC
from gam.util.entity import getDeviceQueries
from gam.util.orgunits import getOrgUnitItem
from gam.util.access import accessErrorExit


BROWSER_TOKEN_TIME_OBJECTS = {'createTime', 'expireTime', 'revokeTime'}

def _showBrowserToken(browser, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(browser), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, browser['token']], i, count)
  Ind.Increment()
  showJSON(None, browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS)
  Ind.Decrement()

# gam create browsertoken
#	[ou|org|orgunit|browserou <OrgUnitPath>] [expire|expires <Time>]
#	[formatjson]
def doCreateBrowserToken():
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  FJQC = FormatJSONQuoteChar()
  body = {'token_type': 'CHROME_BROWSER'}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      body['org_unit_path'] = getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg in ['expire', 'expires']:
      body['expire_time'] = getTimeOrDeltaFromNow()
    else:
      FJQC.GetFormatJSON(myarg)
  try:
    browser = callGAPI(cbcm.enrollmentTokens(), 'create',
                       throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                       customer=customerId, body=body)
    if not FJQC.formatJSON:
      entityActionPerformed([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, browser['token']])
    Ind.Increment()
    _showBrowserToken(browser, FJQC, 0, 0)
    Ind.Decrement()
  except (GAPI.invalidInput, GAPI.invalidOrgunit) as e:
    entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    accessErrorExit(None)

# gam revoke browsertoken <BrowserTokenPermanentID>
def doRevokeBrowserToken():
  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  tokenPermanentId = getString(Cmd.OB_BROWSER_ENROLLEMNT_TOKEN_ID)
  checkForExtraneousArguments()
  try:
    callGAPI(cbcm.enrollmentTokens(), 'revoke',
             throwReasons=[GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
             customer=customerId, tokenPermanentId=tokenPermanentId)
    entityActionPerformed([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, tokenPermanentId])
  except (GAPI.invalid, GAPI.invalidInput, GAPI.badRequest, GAPI.resourceNotFound, GAPI.invalidOrgunit) as e:
    entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, tokenPermanentId], str(e))
  except GAPI.forbidden:
    accessErrorExit(None)

BROWSER_TOKEN_FIELDS_CHOICE_MAP = {
  'createtime': 'createTime',
  'creatorid': 'creatorId',
  'customerid': 'customerId',
  'expiretime': 'expireTime',
  'org': 'orgUnitPath',
  'orgunit': 'orgUnitPath',
  'orgunitpath': 'orgUnitPath',
  'ou': 'orgUnitPath',
  'revoketime': 'revokeTime',
  'revokerid': 'revokerId',
  'state': 'state',
  'token': 'token',
  'tokenpermanentid': 'tokenPermanentId',
  }

# gam show browsertokens
#	([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
#	[querytime<String> <Time>]
#	[orderby <BrowserTokenFieldName> [ascending|descending]]
#	[allfields] <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
#	[formatjson]
# gam print browsertokens [todrive <ToDriveAttribute>*]
#	([ou|org|orgunit|browserou <OrgUnitPath>] [(query <QueryBrowserToken)|(queries <QueryBrowserTokenList>)))
#	[querytime<String> <Time>]
#	[orderby <BrowserTokenFieldName> [ascending|descending]]
#	[allfields] <BrowserTokenFieldName>* [fields <BrowserTokenFieldNameList>]
#	[sortheaders] [formatjson [quotechar <Character>]]
def doPrintShowBrowserTokens():
  def _printBrowserToken(browser):
    row = flattenJSON(browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'token': browser['token'],
                              'JSON': json.dumps(cleanJSON(browser, timeObjects=BROWSER_TOKEN_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cbcm = buildGAPIObject(API.CBCM)
  customerId = _getCustomerIdNoC()
  csvPF = CSVPrintFile(['token']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  orderBy = 'token'
  sortOrder = 'ASCENDING'
  orgUnitPath = None
  queries = [None]
  queryTimes = {}
  sortHeaders = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'query', 'queries'}:
      queries = getDeviceQueries(myarg, Ent.CHROME_BROWSER)
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = getTimeOrDeltaFromNow()[0:19]
    elif myarg in {'ou', 'org', 'orgunit', 'browserou'}:
      orgUnitPath = getOrgUnitItem(pathOnly=True, absolutePath=True)
    elif myarg == 'orderby':
      orderBy, sortOrder = getOrderBySortOrder(BROWSER_TOKEN_FIELDS_CHOICE_MAP, 'DESCENDING', True)
    elif myarg == 'allfields':
      sortHeaders = True
      fieldsList = []
    elif myarg == 'sortheaders':
      sortHeaders = True
    elif getFieldsList(myarg, BROWSER_TOKEN_FIELDS_CHOICE_MAP, fieldsList, initialField='token'):
      pass
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  fields = getItemFieldsFromFieldsList('chromeEnrollmentTokens', fieldsList)
  if FJQC.formatJSON:
    sortHeaders = False
  substituteQueryTimes(queries, queryTimes)
  for query in queries:
    printGettingAllAccountEntities(Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, query)
    pageMessage = getPageMessage()
    try:
      browsers = callGAPIpages(cbcm.enrollmentTokens(), 'list', 'chromeEnrollmentTokens',
                               pageMessage=pageMessage,
                               throwReasons=[GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.INVALID_ORGUNIT, GAPI.FORBIDDEN],
                               customer=customerId, orgUnitPath=orgUnitPath, query=query,
                               fields=fields)
      if not csvPF:
        jcount = len(browsers)
        performActionNumItems(jcount, Ent.CHROME_BROWSER_ENROLLMENT_TOKEN)
        Ind.Increment()
        j = 0
        for browser in browsers:
          j += 1
          _showBrowserToken(browser, FJQC, j, jcount)
        Ind.Decrement()
      else:
        for browser in browsers:
          _printBrowserToken(browser)
    except GAPI.invalidInput as e:
      if query:
        entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], invalidQuery(query))
      else:
        entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
    except GAPI.invalidOrgunit as e:
      entityActionFailedWarning([Ent.CHROME_BROWSER_ENROLLMENT_TOKEN, None], str(e))
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      accessErrorExit(None)
  if csvPF:
    if orderBy:
      csvPF.SortRows(orderBy, reverse=sortOrder == 'DESCENDING')
    if sortHeaders:
      csvPF.SetSortTitles(['token'])
    csvPF.writeCSVfile('Chrome Browser Enrollment Tokens')
