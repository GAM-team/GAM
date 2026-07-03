"""GAM domain and domain alias management."""

import json
import sys

import re

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

def doCreateDomainAlias():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  body = {'domainAliasName': _getMain().getString(Cmd.OB_DOMAIN_ALIAS)}
  body['parentDomainName'] = _getMain().getString(Cmd.OB_DOMAIN_NAME)
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cd.domainAliases(), 'insert',
             throwReasons=[GAPI.DOMAIN_NOT_FOUND, GAPI.DUPLICATE, GAPI.INVALID, GAPI.CONFLICT,
                           GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
    _getMain().entityActionPerformed([Ent.DOMAIN, body['parentDomainName'], Ent.DOMAIN_ALIAS, body['domainAliasName']])
  except GAPI.domainNotFound:
    _getMain().entityActionFailedWarning([Ent.DOMAIN, body['parentDomainName']], Msg.DOES_NOT_EXIST)
  except GAPI.duplicate:
    _getMain().entityActionFailedWarning([Ent.DOMAIN, body['parentDomainName'], Ent.DOMAIN_ALIAS, body['domainAliasName']], Msg.DUPLICATE)
  except (GAPI.invalid, GAPI.conflict) as e:
    _getMain().entityActionFailedWarning([Ent.DOMAIN, body['parentDomainName'], Ent.DOMAIN_ALIAS, body['domainAliasName']], str(e))
  except (GAPI.badRequest, GAPI.notFound) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam delete domainalias|aliasdomain <DomainAlias>
def doDeleteDomainAlias():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  domainAliasName = _getMain().getString(Cmd.OB_DOMAIN_ALIAS)
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cd.domainAliases(), 'delete',
             throwReasons=[GAPI.DOMAIN_ALIAS_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], domainAliasName=domainAliasName)
    _getMain().entityActionPerformed([Ent.DOMAIN_ALIAS, domainAliasName])
  except GAPI.domainAliasNotFound:
    _getMain().entityActionFailedWarning([Ent.DOMAIN_ALIAS, domainAliasName], Msg.DOES_NOT_EXIST)
  except (GAPI.badRequest, GAPI.notFound) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

DOMAIN_TIME_OBJECTS = {'creationTime'}
DOMAIN_ALIAS_PRINT_ORDER = ['parentDomainName', 'creationTime', 'verified']
DOMAIN_ALIAS_SKIP_OBJECTS = {'domainAliasName'}

def _showDomainAlias(alias, FJQC, aliasSkipObjects, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(alias, timeObjects=DOMAIN_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.DOMAIN_ALIAS, alias['domainAliasName']], i, count)
  Ind.Increment()
  if 'creationTime' in alias:
    alias['creationTime'] = _getMain().formatLocalTimestamp(alias['creationTime'])
  for field in DOMAIN_ALIAS_PRINT_ORDER:
    if field in alias:
      _getMain().printKeyValueList([field, alias[field]])
      aliasSkipObjects.add(field)
  _getMain().showJSON(None, alias, aliasSkipObjects)
  Ind.Decrement()

# gam info domainalias|aliasdomain <DomainAlias> [formatjson]
def doInfoDomainAlias():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  domainAliasName = _getMain().getString(Cmd.OB_DOMAIN_ALIAS)
  FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  try:
    result = _getMain().callGAPI(cd.domainAliases(), 'get',
                      throwReasons=[GAPI.DOMAIN_ALIAS_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customer=GC.Values[GC.CUSTOMER_ID], domainAliasName=domainAliasName)
    aliasSkipObjects = DOMAIN_ALIAS_SKIP_OBJECTS
    _showDomainAlias(result, FJQC, aliasSkipObjects)
  except GAPI.domainAliasNotFound:
    _getMain().entityActionFailedWarning([Ent.DOMAIN_ALIAS, domainAliasName], Msg.DOES_NOT_EXIST)
  except (GAPI.badRequest, GAPI.notFound) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

def _printDomain(domain, csvPF):
  row = {}
  for attr in domain:
    if attr not in _getMain().DEFAULT_SKIP_OBJECTS:
      if attr in DOMAIN_TIME_OBJECTS:
        row[attr] = _getMain().formatLocalTimestamp(domain[attr])
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
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile(['domainAliasName'], DOMAIN_ALIAS_SORT_TITLES) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  showItemCountOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    domainAliases = _getMain().callGAPIitems(cd.domainAliases(), 'list', 'domainAliases',
                                  throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                                GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                  customer=GC.Values[GC.CUSTOMER_ID])
    count = len(domainAliases)
    if showItemCountOnly:
      _getMain().writeStdout(f'{count}\n')
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
                                'JSON': json.dumps(_getMain().cleanJSON(domainAlias, timeObjects=DOMAIN_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
  except (GAPI.badRequest, GAPI.notFound) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  if csvPF:
    csvPF.writeCSVfile('Domain Aliases')

# gam create domain <DomainName>
def doCreateDomain():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  body = {'domainName': _getMain().getString(Cmd.OB_DOMAIN_NAME)}
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cd.domains(), 'insert',
             throwReasons=[GAPI.DUPLICATE, GAPI.CONFLICT,
                           GAPI.DOMAIN_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
    _getMain().entityActionPerformed([Ent.DOMAIN, body['domainName']])
  except GAPI.duplicate:
    _getMain().entityDuplicateWarning([Ent.DOMAIN, body['domainName']])
  except GAPI.conflict as e:
    _getMain().entityActionFailedWarning([Ent.DOMAIN, body['domainName']], str(e))
  except (GAPI.domainNotFound, GAPI.badRequest, GAPI.notFound) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam update domain <DomainName> primary
def doUpdateDomain():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  domainName = _getMain().getString(Cmd.OB_DOMAIN_NAME)
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'primary':
      body['customerDomain'] = domainName
    else:
      _getMain().unknownArgumentExit()
  if not body:
    _getMain().missingArgumentExit('primary')
  try:
    _getMain().callGAPI(cd.customers(), 'update',
             throwReasons=[GAPI.DOMAIN_NOT_VERIFIED_SECONDARY, GAPI.BAD_REQUEST,
                           GAPI.RESOURCE_NOT_FOUND, GAPI.INVALID_INPUT,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customerKey=GC.Values[GC.CUSTOMER_ID], body=body, fields='')
    _getMain().entityActionPerformedMessage([Ent.DOMAIN, domainName], Msg.NOW_THE_PRIMARY_DOMAIN)
  except GAPI.domainNotVerifiedSecondary:
    _getMain().entityActionFailedWarning([Ent.DOMAIN, domainName], Msg.DOMAIN_NOT_VERIFIED_SECONDARY)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.invalidInput) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam delete domain <DomainName>
def doDeleteDomain():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  domainName = _getMain().getString(Cmd.OB_DOMAIN_NAME)
  _getMain().checkForExtraneousArguments()
  try:
    _getMain().callGAPI(cd.domains(), 'delete',
             throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                           GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
             customer=GC.Values[GC.CUSTOMER_ID], domainName=domainName)
    _getMain().entityActionPerformed([Ent.DOMAIN, domainName])
  except (GAPI.badRequest, GAPI.notFound) as e:
    _getMain().accessErrorExit(cd, str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

CUSTOMER_LICENSE_MAP = {
  'accounts:num_users': 'Total Users',
  'accounts:gsuite_basic_total_licenses': 'G Suite Basic Licenses',
  'accounts:gsuite_basic_used_licenses': 'G Suite Basic Users',
  'accounts:gsuite_enterprise_total_licenses': 'Workspace Enterprise Plus Licenses',
  'accounts:gsuite_enterprise_used_licenses': 'Workspace Enterprise Plus Users',
  'accounts:gsuite_unlimited_total_licenses': 'G Suite Business Licenses',
  'accounts:gsuite_unlimited_used_licenses': 'G Suite Business Users',
  'accounts:vault_total_licenses': 'Google Vault Licenses',
  }

