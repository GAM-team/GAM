import sys

from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import customer as gapi_directory_customer
from gam import utils


def create():
    cd = gapi_directory.build()
    domain_name = sys.argv[3]
    body = {'domainName': domain_name}
    gapi.call(cd.domains(),
              'insert',
              customer=GC_Values[GC_CUSTOMER_ID],
              body=body)
    print(f'Added domain {domain_name}')


def info():
    if (len(sys.argv) < 4) or (sys.argv[3] == 'logo'):
        gapi_directory_customer.doGetCustomerInfo()
        return
    cd = gapi_directory.build()
    domainName = sys.argv[3]
    result = gapi.call(cd.domains(),
                       'get',
                       customer=GC_Values[GC_CUSTOMER_ID],
                       domainName=domainName)
    if 'creationTime' in result:
        result['creationTime'] = utils.formatTimestampYMDHMSF(
            result['creationTime'])
    if 'domainAliases' in result:
        for i in range(0, len(result['domainAliases'])):
            if 'creationTime' in result['domainAliases'][i]:
                result['domainAliases'][i][
                    'creationTime'] = utils.formatTimestampYMDHMSF(
                        result['domainAliases'][i]['creationTime'])
    display.print_json(result)


def update():
    cd = gapi_directory.build()
    domain_name = sys.argv[3]
    i = 4
    body = {}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'primary':
            body['customerDomain'] = domain_name
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam update domain')
    gapi.call(cd.customers(),
              'update',
              customerKey=GC_Values[GC_CUSTOMER_ID],
              body=body)
    print(f'{domain_name} is now the primary domain.')


def delete():
    cd = gapi_directory.build()
    domainName = sys.argv[3]
    print(f'Deleting domain {domainName}')
    gapi.call(cd.domains(),
              'delete',
              customer=GC_Values[GC_CUSTOMER_ID],
              domainName=domainName)


def print_():
    cd = gapi_directory.build()
    todrive = False
    titles = [
        'domainName',
    ]
    csvRows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print domains')
    results = gapi.call(cd.domains(),
                        'list',
                        customer=GC_Values[GC_CUSTOMER_ID])
    for domain in results.get('domains', []):
        domain_attributes = {}
        domain['type'] = ['secondary', 'primary'][domain['isPrimary']]
        for attr in domain:
            if attr in ['kind', 'etag', 'domainAliases', 'isPrimary']:
                continue
            if attr in [
                    'creationTime',
            ]:
                domain[attr] = utils.formatTimestampYMDHMSF(domain[attr])
            if attr not in titles:
                titles.append(attr)
            domain_attributes[attr] = domain[attr]
        csvRows.append(domain_attributes)
        if 'domainAliases' in domain:
            for aliasdomain in domain['domainAliases']:
                aliasdomain['domainName'] = aliasdomain['domainAliasName']
                del aliasdomain['domainAliasName']
                aliasdomain['type'] = 'alias'
                aliasdomain_attributes = {}
                for attr in aliasdomain:
                    if attr in ['kind', 'etag']:
                        continue
                    if attr in [
                            'creationTime',
                    ]:
                        aliasdomain[attr] = utils.formatTimestampYMDHMSF(
                            aliasdomain[attr])
                    if attr not in titles:
                        titles.append(attr)
                    aliasdomain_attributes[attr] = aliasdomain[attr]
                csvRows.append(aliasdomain_attributes)
    display.write_csv_file(csvRows, titles, 'Domains', todrive)
