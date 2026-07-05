"""GAM customer info/update and instance info commands."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Cmd, Ent, Ind
from gam.util.access import accessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI
from gam.util.args import (
    LANGUAGE_CODES_MAP,
    YYYYMMDD_FORMAT,
    checkForExtraneousArguments,
    getArgument,
    getEmailAddress,
    getLanguageCode,
    getString,
    todaysDate,
)
from gam.util.csv_pf import FormatJSONQuoteChar, cleanJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    printKeyValueList,
    printLine,
)
from gam.util.errors import unknownArgumentExit
from gam.util.fileio import UNKNOWN
from gam.util.output import printWarningMessage, writeStdout, formatLocalTime, formatLocalTimestampUTC
from gam.util.entity import (
    _getCustomerId,
    _getDomainList,
    setTrueCustomerId,
)
from gam.constants import DATA_NOT_AVALIABLE_RC

# Moved here from domains.py to break the customer↔domains import cycle.
# customer.py is the sole consumer of this constant.
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
from gam.cmd.reports import _adjustTryDate, _checkDataRequiredServices
from gam.cmd.reseller import _showCustomerAddressPhoneNumber
from gam.cmd.reseller import ADDRESS_FIELDS_ARGUMENT_MAP
from gam.util.api import ClientAPIAccessDeniedExit



def _showCustomerLicenseInfo(customerInfo, FJQC):
  def numUsersAvailable(result):
    usageReports = result.get('usageReports', [])
    if usageReports:
      for item in usageReports[0].get('parameters', []):
        if item['name'] == 'accounts:num_users':
          return usageReports
    return None

  rep = buildGAPIObject(API.REPORTS)
  parameters = ','.join(CUSTOMER_LICENSE_MAP)
  tryDate = todaysDate().strftime(YYYYMMDD_FORMAT)
  dataRequiredServices = {'accounts'}
  while True:
    try:
      result = callGAPI(rep.customerUsageReports(), 'get',
                        throwReasons=[GAPI.INVALID, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        date=tryDate, customerId=customerInfo['id'],
                        fields='warnings,usageReports', parameters=parameters)
      usageReports = numUsersAvailable(result)
      if usageReports:
        break
      fullData, tryDate, usageReports = _checkDataRequiredServices(result, tryDate, dataRequiredServices)
      if fullData < 0:
        printWarningMessage(DATA_NOT_AVALIABLE_RC, Msg.NO_USER_COUNTS_DATA_AVAILABLE)
        return
      if fullData == 0:
        continue
      break
    except (GAPI.invalid, GAPI.failedPrecondition) as e:
      tryDate = _adjustTryDate(str(e), 0, -1, tryDate)
      if not tryDate:
        return
      continue
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  if not FJQC.formatJSON:
    printKeyValueList([f'User counts as of {tryDate}:'])
    Ind.Increment()
  for item in usageReports[0]['parameters']:
    api_name = CUSTOMER_LICENSE_MAP.get(item['name'])
    api_value = int(item.get('intValue', '0'))
    if api_name and api_value:
      if not FJQC.formatJSON:
        printKeyValueList([api_name, f'{api_value:,}'])
      else:
        customerInfo[item['name']] = api_value
  if not FJQC.formatJSON:
    Ind.Decrement()


# gam info customer [formatjson]
def doInfoCustomer(returnCustomerInfo=None, FJQC=None):
  cd = buildGAPIObject(API.DIRECTORY)
  customerId = _getCustomerId()
  if FJQC is None:
    FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  try:
    customerInfo = callGAPI(cd.customers(), 'get',
                            throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            customerKey=customerId)
    if 'customerCreationTime' in customerInfo:
      customerInfo['customerCreationTime'] = formatLocalTime(customerInfo['customerCreationTime'])
    else:
      customerInfo['customerCreationTime'] =  UNKNOWN
    primaryDomain = {'domainName': UNKNOWN, 'verified': UNKNOWN}
    domains = _getDomainList(cd, customerInfo['id'], 'domains(creationTime,domainName,isPrimary,verified)')
    for domain in domains:
      if domain.get('isPrimary'):
        primaryDomain = domain
        break
    # From Jay Lee
    # If customer has changed primary domain, customerCreationTime is date of current primary being added, not customer create date.
    # We should get all domains and use oldest date
    customerCreationTime = UNKNOWN
    for domain in domains:
      domainCreationTime = formatLocalTimestampUTC(domain['creationTime'])
      if customerCreationTime == UNKNOWN or domainCreationTime < customerCreationTime:
        customerCreationTime = domainCreationTime
    customerInfo['customerCreationTime'] = formatLocalTime(customerCreationTime)
    customerInfo['customerDomain'] = primaryDomain['domainName']
    customerInfo['verified'] = primaryDomain['verified']
    if FJQC.formatJSON:
      _showCustomerLicenseInfo(customerInfo, FJQC)
      if returnCustomerInfo is not None:
        returnCustomerInfo.update(customerInfo)
        return
      printLine(json.dumps(cleanJSON(customerInfo), ensure_ascii=False, sort_keys=True))
      return
    printKeyValueList(['Customer ID', customerInfo['id']])
    printKeyValueList(['Primary Domain', customerInfo['customerDomain']])
    printKeyValueList(['Primary Domain Verified', customerInfo['verified']])
    printKeyValueList(['Customer Creation Time', customerInfo['customerCreationTime']])
    printKeyValueList(['Default Language', customerInfo.get('language', 'Unset or Unknown (defaults to en)')])
    _showCustomerAddressPhoneNumber(customerInfo)
    printKeyValueList(['Admin Secondary Email', customerInfo.get('alternateEmail', UNKNOWN)])
    _showCustomerLicenseInfo(customerInfo, FJQC)
  except (GAPI.badRequest, GAPI.invalidInput, GAPI.domainNotFound, GAPI.notFound, GAPI.resourceNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam update customer [primary <DomainName>] [adminsecondaryemail|alternateemail <EmailAddress>] [language <LanguageCode] [phone|phonenumber <String>]
#	[contact|contactname <String>] [name|organizationname <String>]
#	[address1|addressline1 <String>] [address2|addressline2 <String>] [address3|addressline3 <String>]
#	[locality <String>] [region <String>] [postalcode <String>] [country|countrycode <String>]
def doUpdateCustomer():
  cd = buildGAPIObject(API.DIRECTORY)
  customerId = _getCustomerId()
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault('postalAddress', {})
      body['postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'primary':
      body['customerDomain'] = getString(Cmd.OB_DOMAIN_NAME)
    elif myarg in {'adminsecondaryemail', 'alternateemail'}:
      body['alternateEmail'] = getEmailAddress(noUid=True)
    elif myarg in {'phone', 'phonenumber'}:
      body['phoneNumber'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'language':
      body['language'] = getLanguageCode(LANGUAGE_CODES_MAP)
    else:
      unknownArgumentExit()
  if body:
    try:
      callGAPI(cd.customers(), 'patch',
               throwReasons=[GAPI.DOMAIN_NOT_VERIFIED_SECONDARY, GAPI.INVALID, GAPI.INVALID_INPUT, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               customerKey=customerId, body=body, fields='')
      entityActionPerformed([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID]])
    except GAPI.domainNotVerifiedSecondary:
      entityActionFailedWarning([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID], Ent.DOMAIN, body['customerDomain']], Msg.DOMAIN_NOT_VERIFIED_SECONDARY)
    except (GAPI.invalid, GAPI.invalidInput) as e:
      entityActionFailedWarning([Ent.CUSTOMER_ID, GC.Values[GC.CUSTOMER_ID]], str(e))
    except (GAPI.badRequest, GAPI.resourceNotFound):
      accessErrorExit(cd)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam info instance [formatjson]
def doInfoInstance():
  FJQC = FormatJSONQuoteChar(formatJSONOnly=True)
  customerInfo = None if not FJQC.formatJSON else {}
  doInfoCustomer(customerInfo, FJQC)
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(customerInfo), ensure_ascii=False, sort_keys=True))

def doInfoCustomerId():
  checkForExtraneousArguments()
  setTrueCustomerId(cd=None, forceUpdate=True)
  writeStdout(f'{GC.Values[GC.CUSTOMER_ID]}\n')
