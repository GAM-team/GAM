"""GAM domain and domain alias management."""

import json


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.cmd.customer import doInfoInstance
from gam.util.access import accessErrorExit
from gam.util.api import ClientAPIAccessDeniedExit, buildGAPIObject
from gam.util.api_call import callGAPI, callGAPIitems
from gam.util.args import checkForExtraneousArguments, getArgument, getString
from gam.util.csv_pf import (
    CSVPrintFile,
    DEFAULT_SKIP_OBJECTS,
    FormatJSONQuoteChar,
    cleanJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityActionPerformedMessage,
    entityDuplicateWarning,
    printEntity,
    printKeyValueList,
    printLine,
)
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.output import writeStdout, formatLocalTimestamp

from gam.util.entity import _getDomainList


def doCreateDomainAlias():
  cd = buildGAPIObject(API.DIRECTORY)
  body = {'domainAliasName': getString(Cmd.OB_DOMAIN_ALIAS)}
  body['parentDomainName'] = getString(Cmd.OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domainAliases(), 'insert',
             throwReasons=[GAPI.DOMAIN_NOT_FOUND, GAPI.DUPLICATE, GAPI.INVALID, GAPI.CONFLICT,
                           GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
    entityActionPerformed([Ent.DOMAIN, body['parentDomainName'], Ent.DOMAIN_ALIAS, body['domainAliasName']])
  except GAPI.domainNotFound:
    entityActionFailedWarning([Ent.DOMAIN, body['parentDomainName']], Msg.DOES_NOT_EXIST)
  except GAPI.duplicate:
    entityActionFailedWarning([Ent.DOMAIN, body['parentDomainName'], Ent.DOMAIN_ALIAS, body['domainAliasName']], Msg.DUPLICATE)
  except (GAPI.invalid, GAPI.conflict) as e:
    entityActionFailedWarning([Ent.DOMAIN, body['parentDomainName'], Ent.DOMAIN_ALIAS, body['domainAliasName']], str(e))
  except (GAPI.badRequest, GAPI.notFound) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam delete domainalias|aliasdomain <DomainAlias>
def doDeleteDomainAlias():
  cd = buildGAPIObject(API.DIRECTORY)
  domainAliasName = getString(Cmd.OB_DOMAIN_ALIAS)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domainAliases(), 'delete',
             throwReasons=[GAPI.DOMAIN_ALIAS_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], domainAliasName=domainAliasName)
    entityActionPerformed([Ent.DOMAIN_ALIAS, domainAliasName])
  except GAPI.domainAliasNotFound:
    entityActionFailedWarning([Ent.DOMAIN_ALIAS, domainAliasName], Msg.DOES_NOT_EXIST)
  except (GAPI.badRequest, GAPI.notFound) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

DOMAIN_TIME_OBJECTS = {'creationTime'}
DOMAIN_ALIAS_PRINT_ORDER = ['parentDomainName', 'creationTime', 'verified']
DOMAIN_ALIAS_SKIP_OBJECTS = {'domainAliasName'}

def _showDomainAlias(alias, FJQC, aliasSkipObjects, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(alias, timeObjects=DOMAIN_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.DOMAIN_ALIAS, alias['domainAliasName']], i, count)
  Ind.Increment()
  if 'creationTime' in alias:
    alias['creationTime'] = formatLocalTimestamp(alias['creationTime'])
  for field in DOMAIN_ALIAS_PRINT_ORDER:
    if field in alias:
      printKeyValueList([field, alias[field]])
      aliasSkipObjects.add(field)
  showJSON(None, alias, aliasSkipObjects)
  Ind.Decrement()

# gam info domainalias|aliasdomain <DomainAlias> [formatjson]
def doInfoDomainAlias():
  cd = buildGAPIObject(API.DIRECTORY)
  domainAliasName = getString(Cmd.OB_DOMAIN_ALIAS)
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  try:
    result = callGAPI(cd.domainAliases(), 'get',
                      throwReasons=[GAPI.DOMAIN_ALIAS_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customer=GC.Values[GC.CUSTOMER_ID], domainAliasName=domainAliasName)
    aliasSkipObjects = DOMAIN_ALIAS_SKIP_OBJECTS
    _showDomainAlias(result, FJQC, aliasSkipObjects)
  except GAPI.domainAliasNotFound:
    entityActionFailedWarning([Ent.DOMAIN_ALIAS, domainAliasName], Msg.DOES_NOT_EXIST)
  except (GAPI.badRequest, GAPI.notFound) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

def _printDomain(domain, csvPF):
  row = {}
  for attr in domain:
    if attr not in DEFAULT_SKIP_OBJECTS:
      if attr in DOMAIN_TIME_OBJECTS:
        row[attr] = formatLocalTimestamp(domain[attr])
      else:
        row[attr] = domain[attr]
      csvPF.AddTitles(attr)
  csvPF.WriteRow(row)

DOMAIN_ALIAS_SORT_TITLES = ['domainAliasName', 'parentDomainName', 'creationTime', 'verified']

# gam print domainaliases [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
#	[showitemcountonly]
# gam show domainaliases
#	[formatjson]
#	[showitemcountonly]
def doPrintShowDomainAliases():
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['domainAliasName'], DOMAIN_ALIAS_SORT_TITLES) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    domainAliases = callGAPIitems(cd.domainAliases(), 'list', 'domainAliases',
                                  throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                                GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                  customer=GC.Values[GC.CUSTOMER_ID])
    count = len(domainAliases)
    if showItemCountOnly:
      writeStdout(f'{count}\n')
      return
    i = 0
    for domainAlias in domainAliases:
      i += 1
      if not csvPF:
        aliasSkipObjects = DOMAIN_ALIAS_SKIP_OBJECTS
        _showDomainAlias(domainAlias, FJQC, aliasSkipObjects, i, count)
      elif not FJQC.formatJSON:
        _printDomain(domainAlias, csvPF)
      else:
        csvPF.WriteRowNoFilter({'domainAliasName': domainAlias['domainAliasName'],
                                'JSON': json.dumps(cleanJSON(domainAlias, timeObjects=DOMAIN_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
  except (GAPI.badRequest, GAPI.notFound) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  if csvPF:
    csvPF.writeCSVfile('Domain Aliases')

# gam create domain <DomainName>
def doCreateDomain():
  cd = buildGAPIObject(API.DIRECTORY)
  body = {'domainName': getString(Cmd.OB_DOMAIN_NAME)}
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domains(), 'insert',
             throwReasons=[GAPI.DUPLICATE, GAPI.CONFLICT,
                           GAPI.DOMAIN_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
    entityActionPerformed([Ent.DOMAIN, body['domainName']])
  except GAPI.duplicate:
    entityDuplicateWarning([Ent.DOMAIN, body['domainName']])
  except GAPI.conflict as e:
    entityActionFailedWarning([Ent.DOMAIN, body['domainName']], str(e))
  except (GAPI.domainNotFound, GAPI.badRequest, GAPI.notFound) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam update domain <DomainName> primary
def doUpdateDomain():
  cd = buildGAPIObject(API.DIRECTORY)
  domainName = getString(Cmd.OB_DOMAIN_NAME)
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'primary':
      body['customerDomain'] = domainName
    else:
      unknownArgumentExit()
  if not body:
    missingArgumentExit('primary')
  try:
    callGAPI(cd.customers(), 'update',
             throwReasons=[GAPI.DOMAIN_NOT_VERIFIED_SECONDARY, GAPI.BAD_REQUEST,
                           GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_INPUT,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerKey=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
    entityActionPerformedMessage([Ent.DOMAIN, domainName], Msg.NOW_THE_PRIMARY_DOMAIN)
  except GAPI.domainNotVerifiedSecondary:
    entityActionFailedWarning([Ent.DOMAIN, domainName], Msg.DOMAIN_NOT_VERIFIED_SECONDARY)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.invalidInput) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam delete domain <DomainName>
def doDeleteDomain():
  cd = buildGAPIObject(API.DIRECTORY)
  domainName = getString(Cmd.OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  try:
    callGAPI(cd.domains(), 'delete',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], domainName=domainName)
    entityActionPerformed([Ent.DOMAIN, domainName])
  except (GAPI.badRequest, GAPI.notFound) as e:
    accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))





DOMAIN_PRINT_ORDER = ['customerDomain', 'creationTime', 'isPrimary', 'verified']
DOMAIN_SKIP_OBJECTS = {'domainName', 'domainAliases'}

def _showDomain(result, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(result, timeObjects=DOMAIN_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  skipObjects = DOMAIN_SKIP_OBJECTS
  printEntity([Ent.DOMAIN, result['domainName']], i, count)
  Ind.Increment()
  if 'creationTime' in result:
    result['creationTime'] = formatLocalTimestamp(result['creationTime'])
  for field in DOMAIN_PRINT_ORDER:
    if field in result:
      printKeyValueList([field, result[field]])
      skipObjects.add(field)
  field = 'domainAliases'
  aliases = result.get(field)
  if aliases:
    skipObjects.add(field)
    aliasSkipObjects = DOMAIN_ALIAS_SKIP_OBJECTS
    for alias in aliases:
      _showDomainAlias(alias, FJQC, aliasSkipObjects)
      showJSON(None, alias, aliasSkipObjects)
  showJSON(None, result, skipObjects)
  Ind.Decrement()

# gam info domain [<DomainName>] [formatjson]
def doInfoDomain():
  if (not Cmd.ArgumentsRemaining()) or (Cmd.Current().lower() == 'formatjson'):
    doInfoInstance()
    return
  cd = buildGAPIObject(API.DIRECTORY)
  domainName = getString(Cmd.OB_DOMAIN_NAME)
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  try:
    result = callGAPI(cd.domains(), 'get',
                      throwReasons=[GAPI.DOMAIN_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customer=GC.Values[GC.CUSTOMER_ID], domainName=domainName)
    _showDomain(result, FJQC)
  except GAPI.domainNotFound:
    entityActionFailedWarning([Ent.DOMAIN, domainName], Msg.DOES_NOT_EXIST)
  except (GAPI.badRequest, GAPI.notFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

DOMAIN_SORT_TITLES = ['domainName', 'parentDomainName', 'creationTime', 'type', 'verified']

# gam print domains [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
#	[showitemcountonly]
# gam show domains
#	[formatjson]
#	[showitemcountonly]
def doPrintShowDomains():
  cd = buildGAPIObject(API.DIRECTORY)
  csvPF = CSVPrintFile(['domainName'], DOMAIN_SORT_TITLES) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  domains = _getDomainList(cd, GC.Values[GC.CUSTOMER_ID], '*')
  count = len(domains)
  if showItemCountOnly:
    writeStdout(f'{count}\n')
    return
  i = 0
  for domain in domains:
    i += 1
    if not csvPF:
      _showDomain(domain, FJQC, i, count)
    elif not FJQC.formatJSON:
      domain['type'] = 'primary' if domain.pop('isPrimary') else 'secondary'
      domainAliases = domain.pop('domainAliases', [])
      _printDomain(domain, csvPF)
      for domainAlias in domainAliases:
        domainAlias['type'] = 'alias'
        domainAlias['domainName'] = domainAlias.pop('domainAliasName')
        _printDomain(domainAlias, csvPF)
    else:
      csvPF.WriteRowNoFilter({'domainName': domain['domainName'],
                              'JSON': json.dumps(cleanJSON(domain, timeObjects=DOMAIN_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Domains')


# gam info customerid
