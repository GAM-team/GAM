import datetime

from var import *
import controlflow
import gapi
import gapi.directory
import gapi.reports


def doGetCustomerInfo():
    cd = gapi.directory.buildGAPIObject()
    customer_info = gapi.call(cd.customers(), 'get',
                              customerKey=GC_Values[GC_CUSTOMER_ID])
    print(f'Customer ID: {customer_info["id"]}')
    print(f'Primary Domain: {customer_info["customerDomain"]}')
    result = gapi.call(cd.domains(), 'get', customer=customer_info['id'],
                       domainName=customer_info['customerDomain'],
                       fields='verified')
    print(f'Primary Domain Verified: {result["verified"]}')
    # If customer has changed primary domain customerCreationTime is date
    # of current primary being added, not customer create date.
    # We should also get all domains and use oldest date
    customer_creation = customer_info['customerCreationTime']
    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    oldest = datetime.datetime.strptime(customer_creation, date_format)
    domains = gapi.get_items(cd.domains(), 'list', 'domains',
                             customer=GC_Values[GC_CUSTOMER_ID],
                             fields='domains(creationTime)')
    for domain in domains:
        creation_timestamp = int(domain['creationTime'])/1000
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
    customerId = GC_Values[GC_CUSTOMER_ID]
    if customerId == MY_CUSTOMER:
        customerId = None
    rep = gapi.reports.buildGAPIObject()
    usage = None
    throw_reasons = [gapi.errors.ErrorReason.INVALID]
    while True:
        try:
            usage = gapi.get_all_pages(rep.customerUsageReports(), 'get',
                                       'usageReports',
                                       throw_reasons=throw_reasons,
                                       customerId=customerId, date=tryDate,
                                       parameters=parameters)
            break
        except gapi.errors.GapiInvalidError as e:
            tryDate = gapi.reports._adjust_date(str(e))
    if not usage:
        print('No user count data available.')
        return
    print(f'User counts as of {tryDate}:')
    for item in usage[0]['parameters']:
        api_name = user_counts_map.get(item['name'])
        api_value = int(item.get('intValue', 0))
        if api_name and api_value:
            print(f'  {api_name}: {api_value:,}')


def doUpdateCustomer():
    cd = gapi.directory.buildGAPIObject()
    body = {}
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ADDRESS_FIELDS_ARGUMENT_MAP:
            body.setdefault('postalAddress', {})
            arg = ADDRESS_FIELDS_ARGUMENT_MAP[myarg]
            body['postalAddress'][arg] = sys.argv[i+1]
            i += 2
        elif myarg in ['adminsecondaryemail', 'alternateemail']:
            body['alternateEmail'] = sys.argv[i+1]
            i += 2
        elif myarg in ['phone', 'phonenumber']:
            body['phoneNumber'] = sys.argv[i+1]
            i += 2
        elif myarg == 'language':
            body['language'] = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, "gam update customer")
    if not body:
        controlflow.system_error_exit(2, 'no arguments specified for "gam '
                                         'update customer"')
    gapi.call(cd.customers(), 'patch', customerKey=GC_Values[GC_CUSTOMER_ID],
              body=body)
    print('Updated customer')
