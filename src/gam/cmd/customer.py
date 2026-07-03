"""GAM customer info/update and instance info commands."""

import json
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

def _showCustomerLicenseInfo(customerInfo, FJQC):
  def numUsersAvailable(result):
    usageReports = result.get('usageReports', [])
    if usageReports:
      for item in usageReports[0].get('parameters', []):
        if item['name'] == 'accounts:num_users':
          return usageReports
    return None

  rep = _getMain().buildGAPIObject(API.REPORTS)
  parameters = ','.join(_getMain().CUSTOMER_LICENSE_MAP)
  tryDate = _getMain().todaysDate().strftime(_getMain().YYYYMMDD_FORMAT)
  dataRequiredServices = {'accounts'}
  while True:
    try:
      result = _getMain().callGAPI(rep.customerUsageReports(), 'get',
                        throwReasons=[GAPI.INVALID, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        date=tryDate, customerId=customerInfo['id'],
                        fields='warnings,usageReports', parameters=parameters)
      usageReports = numUsersAvailable(result)
      if usageReports:
        break
      fullData, tryDate, usageReports = _getMain()._checkDataRequiredServices(result, tryDate, dataRequiredServices)
      if fullData < 0:
        _getMain().printWarningMessage(_getMain().DATA_NOT_AVALIABLE_RC, Msg.NO_USER_COUNTS_DATA_AVAILABLE)
        return
      if fullData == 0:
        continue
      break
    except (GAPI.invalid, GAPI.failedPrecondition) as e:
      tryDate = _getMain()._adjustTryDate(str(e), 0, -1, tryDate)
      if not tryDate:
        return
      continue
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  if not FJQC.formatJSON:
    _getMain().printKeyValueList([f'User counts as of {tryDate}:'])
    Ind.Increment()
  for item in usageReports[0]['parameters']:
    api_name = _getMain().CUSTOMER_LICENSE_MAP.get(item['name'])
    api_value = int(item.get('intValue', '0'))
    if api_name and api_value:
      if not FJQC.formatJSON:
        _getMain().printKeyValueList([api_name, f'{api_value:,}'])
      else:
        customerInfo[item['name']] = api_value
  if not FJQC.formatJSON:
    Ind.Decrement()

def setTrueCustomerId(cd=None, forceUpdate=False):
  if GC.Values[GC.CUSTOMER_ID] == GC.MY_CUSTOMER or forceUpdate:
    if not cd:
      cd = _getMain().buildGAPIObject(API.DIRECTORY)
    try:
      customerInfo = _getMain().callGAPI(cd.customers(), 'get',
                              throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                                            GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              customerKey=GC.MY_CUSTOMER,
                              fields='id')
      GC.Values[GC.CUSTOMER_ID] = customerInfo['id']
    except (GAPI.badRequest, GAPI.invalidInput, GAPI.resourceNotFound):
      pass
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

def _getCustomerId():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId != GC.MY_CUSTOMER and customerId[0] != 'C':
    customerId = 'C' + customerId
  return customerId

def _getCustomerIdNoC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId[0] == 'C':
    return customerId[1:]
  return customerId

def _getCustomersCustomerIdNoC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId.startswith('C'):
    customerId = customerId[1:]
  return f'customers/{customerId}'

def _getCustomersCustomerIdWithC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId != GC.MY_CUSTOMER and customerId[0] != 'C':
    customerId = 'C' + customerId
  return f'customers/{customerId}'

def _getDomainList(cd, customer, fields):
  try:
    return _getMain().callGAPIitems(cd.domains(), 'list', 'domains',
                         throwReasons=[GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                       GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                         customer=customer, fields=fields)
  except (GAPI.badRequest, GAPI.notFound):
    _getMain().accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam info customer [formatjson]
def doInfoCustomer(returnCustomerInfo=None, FJQC=None):
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  customerId = _getCustomerId()
  if FJQC is None:
    FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  try:
    customerInfo = _getMain().callGAPI(cd.customers(), 'get',
                            throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            customerKey=customerId)
    if 'customerCreationTime' in customerInfo:
      customerInfo['customerCreationTime'] = _getMain().formatLocalTime(customerInfo['customerCreationTime'])
    else:
      customerInfo['customerCreationTime'] =  _getMain().UNKNOWN
    primaryDomain = {'domainName': _getMain().UNKNOWN, 'verified': _getMain().UNKNOWN}
    domains = _getDomainList(cd, customerInfo['id'], 'domains(creationTime,domainName,isPrimary,verified)')
    for domain in domains:
      if domain.get('isPrimary'):
        primaryDomain = domain
        break
    # From Jay Lee
    # If customer has changed primary domain, customerCreationTime is date of current primary being added, not customer create date.
    # We should get all domains and use oldest date
    customerCreationTime = _getMain().UNKNOWN
    for domain in domains:
      domainCreationTime = _getMain().formatLocalTimestampUTC(domain['creationTime'])
      if customerCreationTime == _getMain().UNKNOWN or domainCreationTime < customerCreationTime:
        customerCreationTime = domainCreationTime
    customerInfo['customerCreationTime'] = _getMain().formatLocalTime(customerCreationTime)
    customerInfo['customerDomain'] = primaryDomain['domainName']
    customerInfo['verified'] = primaryDomain['verified']
    if FJQC.formatJSON:
      _showCustomerLicenseInfo(customerInfo, FJQC)
      if returnCustomerInfo is not None:
        returnCustomerInfo.update(customerInfo)
        return
      _getMain().printLine(json.dumps(_getMain().cleanJSON(customerInfo), ensure_ascii=False, sort_keys=True))
      return
    _getMain().printKeyValueList(['Customer ID', customerInfo['id']])
    _getMain().printKeyValueList(['Primary Domain', customerInfo['customerDomain']])
    _getMain().printKeyValueList(['Primary Domain Verified', customerInfo['verified']])
    _getMain().printKeyValueList(['Customer Creation Time', customerInfo['customerCreationTime']])
    _getMain().printKeyValueList(['Default Language', customerInfo.get('language', 'Unset or Unknown (defaults to en)')])
    _getMain()._showCustomerAddressPhoneNumber(customerInfo)
    _getMain().printKeyValueList(['Admin Secondary Email', customerInfo.get('alternateEmail', _getMain().UNKNOWN)])
    _showCustomerLicenseInfo(customerInfo, FJQC)
  except (GAPI.badRequest, GAPI.invalidInput, GAPI.domainNotFound, GAPI.notFound, GAPI.resourceNotFound):
    _getMain().accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam update customer [primary <DomainName>] [adminsecondaryemail|alternateemail <EmailAddress>] [language <LanguageCode] [phone|phonenumber <String>]
#	[contact|contactname <String>] [name|organizationname <String>]
#	[address1|addressline1 <String>] [address2|addressline2 <String>] [address3|addressline3 <String>]
#	[locality <String>] [region <String>] [postalcode <String>] [country|countrycode <String>]
def doUpdateCustomer():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  customerId = _getCustomerId()
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in _getMain().ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault('postalAddress', {})
      body['postalAddress'][_getMain().ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'primary':
      body['customerDomain'] = _getMain().getString(Cmd.OB_DOMAIN_NAME)
    elif myarg in {'adminsecondaryemail', 'alternateemail'}:
      body['alternateEmail'] = _getMain().getEmailAddress(noUid=True)
    elif myarg in {'phone', 'phonenumber'}:
      body['phoneNumber'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'language':
      body['language'] = _getMain().getLanguageCode(_getMain().LANGUAGE_CODES_MAP)
    else:
      _getMain().unknownArgumentExit()
  if body:
    try:
      _getMain().callGAPI(cd.customers(), 'patch',
               throwReasons=[GAPI.DOMAIN_NOT_VERIFIED_SECONDARY, GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               customerKey=customerId, body=body, fields='')
      _getMain().entityActionPerformed([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID]])
    except GAPI.domainNotVerifiedSecondary:
      _getMain().entityActionFailedWarning([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID], Ent.DOMAIN, body['customerDomain']], Msg.DOMAIN_NOT_VERIFIED_SECONDARY)
    except (GAPI.invalid, GAPI.invalidInput) as e:
      _getMain().entityActionFailedWarning([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID]], str(e))
    except (GAPI.badRequest, GAPI.resourceNotFound):
      _getMain().accessErrorExit(cd)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam info instance [formatjson]
def doInfoInstance():
  FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  customerInfo = None if not FJQC.formatJSON else {}
  doInfoCustomer(customerInfo, FJQC)
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(customerInfo), ensure_ascii=False, sort_keys=True))

DOMAIN_PRINT_ORDER = ['customerDomain', 'creationTime', 'isPrimary', 'verified']
DOMAIN_SKIP_OBJECTS = {'domainName', 'domainAliases'}

def _showDomain(result, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(result, timeObjects=_getMain().DOMAIN_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  skipObjects = DOMAIN_SKIP_OBJECTS
  _getMain().printEntity([Ent.DOMAIN, result['domainName']], i, count)
  Ind.Increment()
  if 'creationTime' in result:
    result['creationTime'] = _getMain().formatLocalTimestamp(result['creationTime'])
  for field in DOMAIN_PRINT_ORDER:
    if field in result:
      _getMain().printKeyValueList([field, result[field]])
      skipObjects.add(field)
  field = 'domainAliases'
  aliases = result.get(field)
  if aliases:
    skipObjects.add(field)
    aliasSkipObjects = _getMain().DOMAIN_ALIAS_SKIP_OBJECTS
    for alias in aliases:
      _getMain()._showDomainAlias(alias, FJQC, aliasSkipObjects)
      _getMain().showJSON(None, alias, aliasSkipObjects)
  _getMain().showJSON(None, result, skipObjects)
  Ind.Decrement()

# gam info domain [<DomainName>] [formatjson]
def doInfoDomain():
  if (not Cmd.ArgumentsRemaining()) or (Cmd.Current().lower() == 'formatjson'):
    doInfoInstance()
    return
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  domainName = _getMain().getString(Cmd.OB_DOMAIN_NAME)
  FJQC = _getMain().FormatJSONQuoteChar(formatJSONOnly=True)
  try:
    result = _getMain().callGAPI(cd.domains(), 'get',
                      throwReasons=[GAPI.DOMAIN_NOT_FOUND, GAPI.BAD_REQUEST, GAPI.NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customer=GC.Values[GC.CUSTOMER_ID], domainName=domainName)
    _showDomain(result, FJQC)
  except GAPI.domainNotFound:
    _getMain().entityActionFailedWarning([Ent.DOMAIN, domainName], Msg.DOES_NOT_EXIST)
  except (GAPI.badRequest, GAPI.notFound):
    _getMain().accessErrorExit(cd)
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
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  csvPF = _getMain().CSVPrintFile(['domainName'], DOMAIN_SORT_TITLES) if Act.csvFormat() else None
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
  domains = _getDomainList(cd, GC.Values[GC.CUSTOMER_ID], '*')
  count = len(domains)
  if showItemCountOnly:
    _getMain().writeStdout(f'{count}\n')
    return
  i = 0
  for domain in domains:
    i += 1
    if not csvPF:
      _showDomain(domain, FJQC, i, count)
    elif not FJQC.formatJSON:
      domain['type'] = 'primary' if domain.pop('isPrimary') else 'secondary'
      domainAliases = domain.pop('domainAliases', [])
      _getMain()._printDomain(domain, csvPF)
      for domainAlias in domainAliases:
        domainAlias['type'] = 'alias'
        domainAlias['domainName'] = domainAlias.pop('domainAliasName')
        _getMain()._printDomain(domainAlias, csvPF)
    else:
      csvPF.WriteRowNoFilter({'domainName': domain['domainName'],
                              'JSON': json.dumps(_getMain().cleanJSON(domain, timeObjects=_getMain().DOMAIN_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Domains')

PRINT_PRIVILEGES_FIELDS = ['serviceId', 'serviceName', 'privilegeName', 'isOuScopable', 'childPrivileges']

