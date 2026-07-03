"""GAM reseller customer/subscription and channel partner management."""

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
from gamlib import glskus as SKU
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    LANGUAGE_CODES_MAP,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getEmailAddress,
    getInteger,
    getLanguageCode,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    cleanJSON,
    flattenJSON,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    performActionNumItems,
    printEntity,
    printKeyValueList,
    printLine,
)
from gam.util.errors import invalidChoiceExit, missingArgumentExit, unknownArgumentExit, usageErrorExit

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

def _showCustomerAddressPhoneNumber(customerInfo):
  if 'postalAddress' in customerInfo:
    printKeyValueList(['Address', None])
    Ind.Increment()
    for field in _getMain().ADDRESS_FIELDS_PRINT_ORDER:
      if field in customerInfo['postalAddress']:
        printKeyValueList([field, customerInfo['postalAddress'][field]])
    Ind.Decrement()
  if 'phoneNumber' in customerInfo:
    printKeyValueList(['Phone', customerInfo['phoneNumber']])

ADDRESS_FIELDS_ARGUMENT_MAP = {
  'contact': 'contactName', 'contactname': 'contactName',
  'name': 'organizationName', 'organizationname': 'organizationName', 'organisationname': 'organizationName',
  'address': 'addressLine1', 'address1': 'addressLine1', 'addressline1': 'addressLine1',
  'address2': 'addressLine2', 'addressline2': 'addressLine2',
  'address3': 'addressLine3', 'addressline3': 'addressLine3',
  'city': 'locality', 'locality': 'locality',
  'state': 'region', 'region': 'region',
  'zipcode': 'postalCode', 'postal': 'postalCode', 'postalcode': 'postalCode',
  'country': 'countryCode', 'countrycode': 'countryCode',
  }

def _getResoldCustomerAttr():
  body = {}
  customerAuthToken = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
      body.setdefault('postalAddress', {})
      body['postalAddress'][ADDRESS_FIELDS_ARGUMENT_MAP[myarg]] = getString(Cmd.OB_STRING, minLen=0, maxLen=255)
    elif myarg in {'email', 'alternateemail'}:
      body['alternateEmail'] = getEmailAddress(noUid=True)
    elif myarg in {'phone', 'phonenumber'}:
      body['phoneNumber'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg in {'customerauthtoken', 'transfertoken'}:
      customerAuthToken = getString(Cmd.OB_STRING)
    else:
      unknownArgumentExit()
  return customerAuthToken, body

# gam create resoldcustomer <CustomerDomain> (customer_auth_token <String>) <ResoldCustomerAttribute>+
def doCreateResoldCustomer():
  res = buildGAPIObject(API.RESELLER)
  customerDomain = getString('customerDomain')
  customerAuthToken, body = _getResoldCustomerAttr()
  body['customerDomain'] = customerDomain
  try:
    result = callGAPI(res.customers(), 'insert',
                      throwReasons=GAPI.RESELLER_THROW_REASONS,
                      body=body, customerAuthToken=customerAuthToken, fields='customerId')
    entityActionPerformed([Ent.CUSTOMER_DOMAIN, body['customerDomain'], Ent.CUSTOMER_ID, result['customerId']])
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_DOMAIN, body['customerDomain']], str(e))

# gam update resoldcustomer <CustomerID> <ResoldCustomerAttribute>+
def doUpdateResoldCustomer():
  res = buildGAPIObject(API.RESELLER)
  customerId = getString(Cmd.OB_CUSTOMER_ID)
  _, body = _getResoldCustomerAttr()
  try:
    callGAPI(res.customers(), 'patch',
             throwReasons=GAPI.RESELLER_THROW_REASONS,
             customerId=customerId, body=body, fields='')
    entityActionPerformed([Ent.CUSTOMER_ID, customerId])
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_ID, customerId], str(e))

# gam info resoldcustomer <CustomerID> [formatjson]
def doInfoResoldCustomer():
  res = buildGAPIObject(API.RESELLER)
  customerId = getString(Cmd.OB_CUSTOMER_ID)
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  try:
    customerInfo = callGAPI(res.customers(), 'get',
                            throwReasons=GAPI.RESELLER_THROW_REASONS,
                            customerId=customerId)
    if not FJQC.formatJSON:
      printKeyValueList(['Customer ID', customerInfo['customerId']])
      printKeyValueList(['Customer Type', customerInfo['customerType']])
      printKeyValueList(['Customer Domain', customerInfo['customerDomain']])
      if 'customerDomainVerified' in customerInfo:
        printKeyValueList(['Customer Domain Verified', customerInfo['customerDomainVerified']])
      _showCustomerAddressPhoneNumber(customerInfo)
      primaryEmail = customerInfo.get('primaryAdmin', {}).get('primaryEmail')
      if primaryEmail:
        printKeyValueList(['Customer Primary Email', primaryEmail])
      if 'alternateEmail' in customerInfo:
        printKeyValueList(['Customer Alternate Email', customerInfo['alternateEmail']])
      printKeyValueList(['Customer Admin Console URL', customerInfo['resourceUiUrl']])
    else:
      printLine(json.dumps(cleanJSON(customerInfo), ensure_ascii=False, sort_keys=False))
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_ID, customerId], str(e))

def getCustomerSubscription(res):
  customerId = getString(Cmd.OB_CUSTOMER_ID)
  productId, skuId = _getMain().SKU.getProductAndSKU(getString(Cmd.OB_SKU_ID))
  if not productId:
    invalidChoiceExit(skuId, _getMain().SKU.getSortedSKUList(), True)
  try:
    subscriptions = callGAPIpages(res.subscriptions(), 'list', 'subscriptions',
                                  throwReasons=GAPI.RESELLER_THROW_REASONS,
                                  customerId=customerId, fields='nextPageToken,subscriptions(skuId,subscriptionId,plan(planName))')
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.SUBSCRIPTION, None], str(e))
    sys.exit(GM.Globals[GM.SYSEXITRC])
  for subscription in subscriptions:
    if skuId == subscription['skuId']:
      return (customerId, skuId, subscription['subscriptionId'], subscription['plan']['planName'])
  Cmd.Backup()
  usageErrorExit(f'{Ent.FormatEntityValueList([Ent.CUSTOMER_ID, customerId, Ent.SKU, skuId])}, {Msg.SUBSCRIPTION_NOT_FOUND}')

PLAN_NAME_MAP = {
  'annualmonthlypay': 'ANNUAL_MONTHLY_PAY',
  'annualyearlypay': 'ANNUAL_YEARLY_PAY',
  'flexible': 'FLEXIBLE',
  'free': 'FREE',
  'trial': 'TRIAL',
  }

def _getResoldSubscriptionAttr(customerId):
  body = {'customerId': customerId,
          'plan': {},
          'seats': {},
          'skuId': None,
         }
  customerAuthToken = None
  seats1 = seats2 = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'deal', 'dealcode'}:
      body['dealCode'] = getString('dealCode')
    elif myarg in {'plan', 'planname'}:
      body['plan']['planName'] = getChoice(PLAN_NAME_MAP, mapChoice=True)
    elif myarg in {'purchaseorderid', 'po'}:
      body['purchaseOrderId'] = getString('purchaseOrderId')
    elif myarg == 'seats':
      seats1 = getInteger(minVal=0)
      if Cmd.ArgumentsRemaining() and Cmd.Current().isdigit():
        seats2 = getInteger(minVal=0)
    elif myarg in {'sku', 'skuid'}:
      productId, body['skuId'] = _getMain().SKU.getProductAndSKU(getString(Cmd.OB_SKU_ID))
      if not productId:
        invalidChoiceExit(body['skuId'], _getMain().SKU.getSortedSKUList(), True)
    elif myarg in {'customerauthtoken', 'transfertoken'}:
      customerAuthToken = getString('customer_auth_token')
    else:
      unknownArgumentExit()
  for field in ['plan', 'skuId']:
    if not body[field]:
      missingArgumentExit(field.lower())
  if seats1 is None:
    missingArgumentExit('seats')
  if body['plan']['planName'].startswith('ANNUAL'):
    body['seats']['numberOfSeats'] = seats1
  else:
    body['seats']['maximumNumberOfSeats'] = seats1 if seats2 is None else seats2
  return customerAuthToken, body

SUBSCRIPTION_SKIP_OBJECTS = {'customerId', 'skuId', 'subscriptionId'}
SUBSCRIPTION_TIME_OBJECTS = {'creationTime', 'startTime', 'endTime', 'trialEndTime', 'transferabilityExpirationTime'}

def _showSubscription(subscription, FJQC=None):
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(subscription, timeObjects=SUBSCRIPTION_TIME_OBJECTS), ensure_ascii=False, sort_keys=False))
    return
  Ind.Increment()
  printEntity([Ent.SUBSCRIPTION, subscription['subscriptionId']])
  showJSON(None, subscription, SUBSCRIPTION_SKIP_OBJECTS, SUBSCRIPTION_TIME_OBJECTS)
  Ind.Decrement()

# gam create resoldsubscription <CustomerID> (sku <SKUID>)
#	 (plan annual_monthly_pay|annual_yearly_pay|flexible|trial) (seats <Number>)
#	 [customer_auth_token <String>] [deal <String>] [purchaseorderid <String>]
def doCreateResoldSubscription():
  res = buildGAPIObject(API.RESELLER)
  customerId = getString(Cmd.OB_CUSTOMER_ID)
  customerAuthToken, body = _getResoldSubscriptionAttr(customerId)
  try:
    subscription = callGAPI(res.subscriptions(), 'insert',
                            throwReasons=GAPI.RESELLER_THROW_REASONS,
                            customerId=customerId, customerAuthToken=customerAuthToken, body=body)
    entityActionPerformed([Ent.CUSTOMER_ID, customerId, Ent.SKU, subscription['skuId']])
    _showSubscription(subscription)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_ID, customerId], str(e))

RENEWAL_TYPE_MAP = {
  'autorenewmonthlypay': 'AUTO_RENEW_MONTHLY_PAY',
  'autorenewyearlypay': 'AUTO_RENEW_YEARLY_PAY',
  'cancel': 'CANCEL',
  'renewcurrentusersmonthlypay': 'RENEW_CURRENT_USERS_MONTHLY_PAY',
  'renewcurrentusersyearlypay': 'RENEW_CURRENT_USERS_YEARLY_PAY',
  'switchtopayasyougo': 'SWITCH_TO_PAY_AS_YOU_GO',
  }

# gam update resoldsubscription <CustomerID> <SKUID>
#	activate|suspend|startpaidservice|
#	(renewal auto_renew_monthly_pay|auto_renew_yearly_pay|cancel|renew_current_users_monthly_pay|renew_current_users_yearly_pay|switch_to_pay_as_you_go)|
#	(seats <Number>)|
#	(plan annual_monthly_pay|annual_yearly_pay|flexible|trial|free [deal <String>] [purchaseorderid <String>] [seats <Number>])
def doUpdateResoldSubscription():
  def _getSeats():
    seats1 = getInteger(minVal=0)
    if Cmd.ArgumentsRemaining() and Cmd.Current().isdigit():
      seats2 = getInteger(minVal=0)
    else:
      seats2 = None
    if planName.startswith('ANNUAL'):
      return {'numberOfSeats': seats1}
    return {'maximumNumberOfSeats': seats1 if seats2 is None else seats2}

  res = buildGAPIObject(API.RESELLER)
  function = None
  customerId, skuId, subscriptionId, planName = getCustomerSubscription(res)
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'activate':
      function = 'activate'
    elif myarg == 'suspend':
      function = 'suspend'
    elif myarg == 'startpaidservice':
      function = 'startPaidService'
    elif myarg in {'renewal', 'renewaltype'}:
      function = 'changeRenewalSettings'
      kwargs['body'] = {'renewalType': getChoice(RENEWAL_TYPE_MAP, mapChoice=True)}
    elif myarg == 'seats':
      function = 'changeSeats'
      kwargs['body'] =  _getSeats()
    elif myarg == 'plan':
      function = 'changePlan'
      planName = getChoice(PLAN_NAME_MAP, mapChoice=True)
      kwargs['body'] = {'planName': planName}
      while Cmd.ArgumentsRemaining():
        planarg = getArgument()
        if planarg == 'seats':
          kwargs['body']['seats'] = _getSeats()
        elif planarg in {'purchaseorderid', 'po'}:
          kwargs['body']['purchaseOrderId'] = getString('purchaseOrderId')
        elif planarg in {'dealcode', 'deal'}:
          kwargs['body']['dealCode'] = getString('dealCode')
        else:
          unknownArgumentExit()
    else:
      unknownArgumentExit()
  try:
    subscription = callGAPI(res.subscriptions(), function,
                            throwReasons=GAPI.RESELLER_THROW_REASONS,
                            customerId=customerId, subscriptionId=subscriptionId, **kwargs)
    entityActionPerformed([Ent.CUSTOMER_ID, customerId, Ent.SKU, skuId])
    if subscription:
      _showSubscription(subscription)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_ID, customerId], str(e))

DELETION_TYPE_MAP = {
  'cancel': 'cancel',
  'downgrade': 'downgrade',
  'transfertodirect': 'transfer_to_direct',
  }

# gam delete resoldsubscription <CustomerID> <SKUID> cancel|downgrade|transfer_to_direct
def doDeleteResoldSubscription():
  res = buildGAPIObject(API.RESELLER)
  customerId, skuId, subscriptionId, _ = getCustomerSubscription(res)
  deletionType = getChoice(DELETION_TYPE_MAP, mapChoice=True)
  checkForExtraneousArguments()
  try:
    callGAPI(res.subscriptions(), 'delete',
             throwReasons=GAPI.RESELLER_THROW_REASONS,
             customerId=customerId, subscriptionId=subscriptionId, deletionType=deletionType)
    entityActionPerformed([Ent.CUSTOMER_ID, customerId, Ent.SKU, skuId])
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_ID, customerId, Ent.SKU, skuId], str(e))

# gam info resoldsubscription <CustomerID> <SKUID>
def doInfoResoldSubscription():
  res = buildGAPIObject(API.RESELLER)
  customerId, skuId, subscriptionId, _ = getCustomerSubscription(res)
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  try:
    subscription = callGAPI(res.subscriptions(), 'get',
                            throwReasons=GAPI.RESELLER_THROW_REASONS,
                            customerId=customerId, subscriptionId=subscriptionId)
    if not FJQC.formatJSON:
      printEntity([Ent.CUSTOMER_ID, customerId, Ent.SKU, skuId])
    _showSubscription(subscription, FJQC)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.CUSTOMER_ID, customerId, Ent.SKU, skuId], str(e))

PRINT_RESOLD_SUBSCRIPTIONS_TITLES = ['customerId', 'skuId', 'subscriptionId']

# gam print resoldsubscriptions [todrive <ToDriveAttribute>*]
#	[customerid <CustomerID>] [customer_auth_token <String>] [customer_prefix <String>]
#	[maxresults <Number>]
#	[formatjson [quotechar <Character>]]
# gam show resoldsubscriptions
#	[customerid <CustomerID>] [customer_auth_token <String>] [customer_prefix <String>]
#	[maxresults <Number>]
#	[formatjson]
def doPrintShowResoldSubscriptions():
  res = buildGAPIObject(API.RESELLER)
  kwargs = {'maxResults': 100}
  csvPF = CSVPrintFile(PRINT_RESOLD_SUBSCRIPTIONS_TITLES, 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'customerid':
      kwargs['customerId'] = getString(Cmd.OB_CUSTOMER_ID)
    elif myarg in {'customerauthtoken', 'transfertoken'}:
      kwargs['customerAuthToken'] = getString(Cmd.OB_CUSTOMER_AUTH_TOKEN)
    elif myarg == 'customerprefix':
      kwargs['customerNamePrefix'] = getString(Cmd.OB_STRING)
    elif myarg == 'maxresults':
      kwargs['maxResults'] = getInteger(minVal=1, maxVal=100)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  try:
    subscriptions = callGAPIpages(res.subscriptions(), 'list', 'subscriptions',
                                  throwReasons=GAPI.RESELLER_THROW_REASONS,
                                  fields='nextPageToken,subscriptions', **kwargs)
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.SUBSCRIPTION, None], str(e))
    return
  jcount = len(subscriptions)
  if not csvPF:
    if not FJQC.formatJSON:
      performActionNumItems(jcount, Ent.SUBSCRIPTION)
    Ind.Increment()
    j = 0
    for subscription in subscriptions:
      j += 1
      if not FJQC.formatJSON:
        printEntity([Ent.CUSTOMER_ID, subscription['customerId'], Ent.SKU, subscription['skuId']], j, jcount)
      _showSubscription(subscription, FJQC)
    Ind.Decrement()
  else:
    for subscription in subscriptions:
      row = flattenJSON(subscription, timeObjects=SUBSCRIPTION_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'customerId': subscription['customerId'],
                                'skuId': subscription['skuId'],
                                'subscriptionId': subscription['subscriptionId'],
                                'JSON': json.dumps(cleanJSON(subscription, timeObjects=SUBSCRIPTION_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
    csvPF.writeCSVfile('Resold Subscriptions')

def normalizeChannelResellerID(resellerId):
  if resellerId.startswith('accounts/'):
    return resellerId
  return f'accounts/{resellerId}'

def normalizeChannelCustomerID(customerId):
  if customerId.startswith('customers/'):
    return customerId
  return f'customers/{customerId}'

def normalizeChannelProductID(productId):
  if productId.startswith('products/'):
    return productId
  return f'products/{productId}'

CHANNEL_ENTITY_MAP = {
  Ent.CHANNEL_CUSTOMER:
    {'JSONtitles': ['name', 'domain', 'JSON'],
     'timeObjects': ['createTime', 'updateTime'],
     'items': 'customers',
     'pageSize': 50,
     'maxPageSize': 50,
     'fields': {
        'name': 'name',
        'orgdisplayname': 'orgDisplayName',
        'orgpostaladdress': 'orgPostalAddress',
        'primarycontactinfo': 'primaryContactInfo',
        'alternateemail': 'alternateEmail',
        'domain': 'domain',
        'createtime': 'createTime',
        'updatetime': 'updateTime',
        'cloudidentityid': 'cloudIdentityId',
        'languagecode': 'languageCode',
        'cloudidentityinfo': 'cloudIdentityInfo',
        'channelpartnerid': 'channelPartnerId',
        }
     },
  Ent.CHANNEL_CUSTOMER_ENTITLEMENT:
    {'JSONtitles': ['name', 'offer', 'JSON'],
     'timeObjects': ['createTime', 'updateTime', 'startTime', 'endTime'],
     'items': 'entitlements',
     'pageSize': 100,
     'maxPageSize': 100,
     'fields': {
        'name': 'name',
        'createtime': 'createTime',
        'updatetime': 'updateTime',
        'offer': 'offer',
        'commitmentsettings': 'commitmentSettings',
        'provisioningstate': 'provisioningState',
        'provisionedservice': 'provisionedService',
        'suspensionreasons': 'suspensionReasons',
        'purchaseorderid': 'purchaseOrderId',
        'trialsettings': 'trialSettings',
        'associationinfo': 'associationInfo',
        'parameters': 'parameters',
        }
     },
  Ent.CHANNEL_OFFER:
    {'JSONtitles': ['name', 'sku', 'JSON'],
     'timeObjects': ['startTime', 'endTime'],
     'items': 'offers',
     'pageSize': 1000,
     'maxPageSize': 1000,
     'fields': {
        'name': 'name',
        'marketinginfo': 'marketingInfo',
        'sku': 'sku',
        'plan': 'plan',
        'constraints': 'constraints',
        'pricebyresources': 'priceByResources',
        'starttime': 'startTime',
        'endtime': 'endTime',
        'parameterdefinitions': 'parameterDefinitions',
        }
     },
  Ent.CHANNEL_PRODUCT:
    {'JSONtitles': ['name', 'JSON'],
     'timeObjects': None,
     'items': 'products',
     'pageSize': 1000,
     'maxPageSize': 1000,
     'fields': {
        'name': 'name',
        'marketinginfo': 'marketingInfo',
        }
     },
  Ent.CHANNEL_SKU:
    {'JSOBtitles': ['name', 'JSON'],
     'timeObjects': None,
     'items': 'skus',
     'pageSize': 1000,
     'maxPageSize': 1000,
     'fields': {
        'name': 'name',
        'marketinginfo': 'marketingInfo',
        'product': 'product',
        }
     }
  }

def doPrintShowChannelItems(entityType):
  cchan = buildGAPIObject(API.CLOUDCHANNEL)
  if entityType == Ent.CHANNEL_CUSTOMER:
    service = cchan.accounts().customers()
  elif entityType == Ent.CHANNEL_CUSTOMER_ENTITLEMENT:
    service = cchan.accounts().customers().entitlements()
  elif entityType == Ent.CHANNEL_OFFER:
    service = cchan.accounts().offers()
  elif entityType == Ent.CHANNEL_PRODUCT:
    service = cchan.products()
  else: #Ent.CHANNEL_SKU
    service = cchan.products().skus()
  channelEntityMap = CHANNEL_ENTITY_MAP[entityType]
#  csvPF = CSVPrintFile(channelEntityMap['titles'], 'sortall') if Act.csvFormat() else None
  csvPF = CSVPrintFile(['name'], 'sortall') if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  resellerId = normalizeChannelResellerID(GC.Values[GC.RESELLER_ID] if GC.Values[GC.RESELLER_ID] else GC.Values[GC.CUSTOMER_ID])
  customerId = normalizeChannelCustomerID(GC.Values[GC.CHANNEL_CUSTOMER_ID])
  name = None
  productId = 'products/-'
  kwargs = {'pageSize': channelEntityMap['pageSize']}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'resellerid':
      resellerId = normalizeChannelResellerID(getString(Cmd.OB_RESELLER_ID))
    elif (entityType == Ent.CHANNEL_CUSTOMER_ENTITLEMENT) and myarg in {'customerid', 'channelcustomerid'}:
      customerId = normalizeChannelCustomerID(getString(Cmd.OB_CHANNEL_CUSTOMER_ID))
    elif (entityType == Ent.CHANNEL_CUSTOMER_ENTITLEMENT) and myarg == 'name':
      name = getString(Cmd.OB_STRING)
      parent = name.split('/')
      if (len(parent) != 4) or (parent[0] != 'accounts') or (not parent[1]) or (parent[2] != 'customers') or (not parent[3]):
        Cmd.Backup()
        usageErrorExit(Msg.INVALID_RESELLER_CUSTOMER_NAME)
    elif (entityType in {Ent.CHANNEL_OFFER, Ent.CHANNEL_PRODUCT, Ent.CHANNEL_SKU}) and myarg == 'language':
      kwargs['languageCode'] = getLanguageCode(LANGUAGE_CODES_MAP)
    elif (entityType in {Ent.CHANNEL_CUSTOMER, Ent.CHANNEL_OFFER}) and myarg == 'filter':
      kwargs['filter'] = getString(Cmd.OB_STRING)
    elif (entityType == Ent.CHANNEL_SKU) and myarg == 'productid':
      productId = normalizeChannelProductID(getString(Cmd.OB_PRODUCT_ID))
    elif myarg == 'fields':
      if not fieldsList:
        fieldsList.append('name')
      for field in _getFieldsList():
        if field in channelEntityMap['fields']:
          fieldsList.append(channelEntityMap['fields'][field])
        else:
          invalidChoiceExit(field, list(channelEntityMap['fields']), True)
    elif myarg == 'maxresults':
      kwargs['pageSize'] = getInteger(minVal=1, maxVal=channelEntityMap['maxPageSize'])
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if entityType != Ent.CHANNEL_CUSTOMER_ENTITLEMENT:
    entityName = resellerId
    if entityType in {Ent.CHANNEL_CUSTOMER, Ent.CHANNEL_OFFER}:
      kwargs['parent'] = resellerId
    else:
      kwargs['account'] = resellerId
      if entityType == Ent.CHANNEL_SKU:
        kwargs['parent'] = productId
  else:
    if not name and customerId == 'customers/':
      missingArgumentExit('channelcustomerid')
    entityName = kwargs['parent'] = name if name else f'{resellerId}/{customerId}'
  fields = getItemFieldsFromFieldsList(channelEntityMap['items'], fieldsList)
#  if csvPF and FJQC.formatJSON and not fieldsList:
#    csvPF.SetJSONTitles(channelEntityMap['JSONtitles'])
  try:
    results = callGAPIpages(service, 'list', channelEntityMap['items'],
                            bailOnInternalError=True,
                            throwReasons=[GAPI.PERMISSION_DENIED, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.INTERNAL_ERROR, GAPI.NOT_FOUND],
                            fields=fields, **kwargs)
  except (GAPI.permissionDenied, GAPI.invalidArgument, GAPI.badRequest, GAPI.internalError, GAPI.notFound) as e:
    entityActionFailedWarning([entityType, entityName], str(e))
    return
  jcount = len(results)
  if not csvPF:
    if not FJQC.formatJSON:
      performActionNumItems(jcount, entityType)
    Ind.Increment()
    j = 0
    for item in results:
      j += 1
      if not FJQC.formatJSON:
        printEntity([entityType, item['name']], j, jcount)
        Ind.Increment()
        showJSON(None, item, timeObjects=channelEntityMap['timeObjects'])
        Ind.Decrement()
      else:
        printLine(json.dumps(cleanJSON(item, timeObjects=channelEntityMap['timeObjects']),
                             ensure_ascii=False, sort_keys=False))
    Ind.Decrement()
  else:
    for item in results:
      row = flattenJSON(item, timeObjects=channelEntityMap['timeObjects'])
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        row = {'name': item['name'],
               'JSON': json.dumps(cleanJSON(item, timeObjects=channelEntityMap['timeObjects']),
                                  ensure_ascii=False, sort_keys=True)}
#        if not fieldsList:
#          if entityType == Ent.CHANNEL_CUSTOMER:
#            row.update({'domain': item['domain']})
#          elif entityType == Ent.CHANNEL_CUSTOMER_ENTITLEMENT:
#            row.update({'offer': item['offer']})
#          elif entityType == Ent.CHANNEL_OFFER:
#            row.update({'sku': item['sku']})
        csvPF.WriteRowNoFilter(row)
    csvPF.writeCSVfile(Ent.Plural(entityType))

# gam print channelcustomers [todrive <ToDriveAttribute>*]
#	[resellerid <ResellerID>] [filter <String>]
#	[fields <ChannelCustomerFieldList>]
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam show channelcustomers
#	[resellerid <ResellerID>] [filter <String>]
#	[fields <ChannelCustomerFieldList>]
#	[maxresults <Integer>]
#	[formatjson]
def doPrintShowChannelCustomers():
  doPrintShowChannelItems(Ent.CHANNEL_CUSTOMER)

# gam print channelcustomercentitlements [todrive <ToDriveAttribute>*]
#	([resellerid <ResellerID>] [customerid <ChannelCustomerID>])|
#	(name accounts/<ResellerID>/customers/<ChannelCustomerID>)
#	[fields <ChannelCustomerEntitlementFieldList>]
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam show channelcustomerentitlements
#	([resellerid <ResellerID>] [customerid <ChannelCustomerID>])|
#	(name accounts/<ResellerID>/customers/<ChannelCustomerID>)
#	[fields <ChannelCustomerEntitlementFieldList>]
#	[maxresults <Integer>]
#	[formatjson]
def doPrintShowChannelCustomerEntitlements():
  doPrintShowChannelItems(Ent.CHANNEL_CUSTOMER_ENTITLEMENT)

# gam print channeloffers [todrive <ToDriveAttribute>*]
#	[resellerid <ResellerID>] [filter <String>] [language <LanguageCode]
#	[fields <ChannelOfferFieldList>]
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam show channeloffers
#	[resellerid <ResellerID>] [filter <String>] [language <LanguageCode]
#	[fields <ChannelOfferFieldList>]
#	[maxresults <Integer>]
#	[formatjson]
def doPrintShowChannelOffers():
  doPrintShowChannelItems(Ent.CHANNEL_OFFER)

# gam print channelproducts [todrive <ToDriveAttribute>*]
#	[resellerid <ResellerID>] [language <LanguageCode]
#	[fields <ChannelProductFieldList>]
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam show channelproducts
#	[resellerid <ResellerID>] [language <LanguageCode]
#	[fields <ChannelProductFieldList>]
#	[maxresults <Integer>]
#	[formatjson]
def doPrintShowChannelProducts():
  doPrintShowChannelItems(Ent.CHANNEL_PRODUCT)

# gam print channelskus [todrive <ToDriveAttribute>*]
#	[resellerid <ResellerID>] [language <LanguageCode] [productid <ProductID>]
#	[fields <ChannelSKUFieldList>]
#	[maxresults <Integer>]
#	[formatjson [quotechar <Character>]]
# gam show channelskus
#	[resellerid <ResellerID>] [language <LanguageCode] [productid <ProductID>]
#	[fields <ChannelSKUFieldList>]
#	[maxresults <Integer>]
#	[formatjson]
def doPrintShowChannelSKUs():
  doPrintShowChannelItems(Ent.CHANNEL_SKU)

ANALYTIC_ENTITY_MAP = {
  Ent.ANALYTIC_ACCOUNT:
    {'titles': ['User', 'name', 'displayName', 'createTime', 'updateTime', 'regionCode', 'deleted'],
     'JSONtitles': ['User', 'name', 'displayName', 'JSON'],
     'timeObjects': ['createTime', 'updateTime'],
     'items': 'accounts',
     'pageSize': 50,
     'maxPageSize': 200,
     },
  Ent.ANALYTIC_ACCOUNT_SUMMARY:
    {'titles': ['User', 'name', 'displayName', 'account'],
     'JSONtitles': ['User', 'name', 'displayName', 'account', 'JSON'],
     'timeObjects': ['createTime', 'updateTime', 'deleteTime', 'expireTime'],
     'items': 'accountSummaries',
     'pageSize': 50,
     'maxPageSize': 200,
     },
  Ent.ANALYTIC_DATASTREAM:
    {'titles': ['User', 'name', 'displayName', 'type', 'createTime', 'updateTime'],
     'JSONtitles': ['User', 'name', 'displayName', 'type', 'JSON'],
     'timeObjects': ['createTime', 'updateTime'],
     'items': 'dataStreams',
     'pageSize': 50,
     'maxPageSize': 200,
     },
  Ent.ANALYTIC_PROPERTY:
    {'titles': ['User', 'name', 'displayName', 'createTime', 'updateTime', 'propertyType', 'parent'],
     'JSONtitles': ['User', 'name', 'displayName', 'propertyType', 'parent', 'JSON'],
     'timeObjects': ['createTime', 'updateTime', 'deleteTime', 'expireTime'],
     'items': 'properties',
     'pageSize': 50,
     'maxPageSize': 200,
     },
  }

