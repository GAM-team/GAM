import datetime
import sys

from gam.var import *
from gam import controlflow
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi import reports as gapi_reports


def _get_customerid():
    customer = GC_Values[GC_CUSTOMER_ID]
    if customer != MY_CUSTOMER and customer[0] != 'C':
        customer = 'C' + customer
    return customer

def doGetCustomerInfo():
    cd = gapi_directory.build()
    customer_id = _get_customerid()
    customer_info = gapi.call(cd.customers(),
                              'get',
                              customerKey=customer_id)
    print(f'Customer ID: {customer_info["id"]}')
    print(f'Primary Domain: {customer_info["customerDomain"]}')
    try:
        result = gapi.call(
            cd.domains(),
            'get',
            customer=customer_id,
            domainName=customer_info['customerDomain'],
            fields='verified',
            throw_reasons=[gapi.errors.ErrorReason.DOMAIN_NOT_FOUND])
    except gapi.errors.GapiDomainNotFoundError:
        result = {'verified': False}
    print(f'Primary Domain Verified: {result["verified"]}')
    # If customer has changed primary domain customerCreationTime is date
    # of current primary being added, not customer create date.
    # We should also get all domains and use oldest date
    customer_creation = customer_info['customerCreationTime']
    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    oldest = datetime.datetime.strptime(customer_creation, date_format)
    domains = gapi.get_items(cd.domains(),
                             'list',
                             'domains',
                             customer=customer_id,
                             fields='domains(creationTime)')
    for domain in domains:
        creation_timestamp = int(domain['creationTime']) / 1000
        domain_creation = datetime.datetime.fromtimestamp(creation_timestamp)
        if domain_creation < oldest:
            oldest = domain_creation
    print(f'Customer Creation Time: {oldest.strftime(date_format)}')
    customer_language = customer_info.get('language', 'Unset (defaults to en)')
    print(f'Default Language: {customer_language}')
    if 'postalAddress' in customer_info:
        print('Address:')
        for field in ADDRESS_FIELDS_PRINT_ORDER:
            if field in customer_info['postalAddress']:
                print(f' {field}: {customer_info["postalAddress"][field]}')
    if 'phoneNumber' in customer_info:
        print(f'Phone: {customer_info["phoneNumber"]}')
    print(f'Admin Secondary Email: {customer_info["alternateEmail"]}')
    user_counts_map = {
        'accounts:num_users': 'Total Users',
        'accounts:gsuite_basic_total_licenses': 'G Suite Basic Licenses',
        'accounts:gsuite_basic_used_licenses': 'G Suite Basic Users',
        'accounts:gsuite_enterprise_total_licenses': 'G Suite Enterprise ' \
        'Licenses',
        'accounts:gsuite_enterprise_used_licenses': 'G Suite Enterprise ' \
        'Users',
        'accounts:gsuite_unlimited_total_licenses': 'G Suite Business ' \
        'Licenses',
        'accounts:gsuite_unlimited_used_licenses': 'G Suite Business Users'
    }
    parameters = ','.join(list(user_counts_map))
    tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
    rep = gapi_reports.build()
    usage = None
    throw_reasons = [
        gapi.errors.ErrorReason.INVALID, gapi.errors.ErrorReason.FORBIDDEN
    ]
    while True:
        try:
            result = gapi.call(rep.customerUsageReports(),
                               'get',
                               throw_reasons=throw_reasons,
                               customerId=customer_id,
                               date=tryDate,
                               parameters=parameters)
        except gapi.errors.GapiInvalidError as e:
            tryDate = gapi_reports._adjust_date(str(e))
            continue
        except gapi.errors.GapiForbiddenError:
            return
        warnings = result.get('warnings', [])
        fullDataRequired = ['accounts']
        usage = result.get('usageReports')
        has_reports = bool(usage)
        fullData, tryDate = gapi_reports._check_full_data_available(
            warnings, tryDate, fullDataRequired, has_reports)
        if fullData < 0:
            print('No user report available.')
            sys.exit(1)
        if fullData == 0:
            continue
        break
    print(f'User counts as of {tryDate}:')
    for item in usage[0]['parameters']:
        api_name = user_counts_map.get(item['name'])
        api_value = int(item.get('intValue', 0))
        if api_name and api_value:
            print(f'  {api_name}: {api_value:,}')


def doUpdateCustomer():
    cd = gapi_directory.build()
    body = {}
    customer_id = _get_customerid()
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
            body.setdefault('postalAddress', {})
            arg = ADDRESS_FIELDS_ARGUMENT_MAP[myarg]
            body['postalAddress'][arg] = sys.argv[i + 1]
            i += 2
        elif myarg in ['adminsecondaryemail', 'alternateemail']:
            body['alternateEmail'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['phone', 'phonenumber']:
            body['phoneNumber'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'language':
            body['language'] = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam update customer')
    if not body:
        controlflow.system_error_exit(
            2, 'no arguments specified for "gam '
            'update customer"')
    gapi.call(cd.customers(),
              'patch',
              customerKey=customer_id,
              body=body)
    print('Updated customer')


def setTrueCustomerId(cd=None):
    customer_id = GC_Values[GC_CUSTOMER_ID]
    if customer_id == MY_CUSTOMER:
        if not cd:
            cd = gapi_directory.build()
        result = gapi.call(cd.customers(),
                           'get',
                            customerKey=customer_id,
                            fields='id')
        GC_Values[GC_CUSTOMER_ID] = result.get('id',
                                               customer_id)
