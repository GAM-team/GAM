import sys

from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam import utils


def create():
    cd = gapi_directory.build()
    body = {'domainAliasName': sys.argv[3], 'parentDomainName': sys.argv[4]}
    print(f'Adding {body["domainAliasName"]} alias for ' \
       f'{body["parentDomainName"]}')
    gapi.call(cd.domainAliases(),
              'insert',
              customer=GC_Values[GC_CUSTOMER_ID],
              body=body)


def delete():
    cd = gapi_directory.build()
    domainAliasName = sys.argv[3]
    print(f'Deleting domain alias {domainAliasName}')
    gapi.call(cd.domainAliases(),
              'delete',
              customer=GC_Values[GC_CUSTOMER_ID],
              domainAliasName=domainAliasName)


def info():
    cd = gapi_directory.build()
    alias = sys.argv[3]
    result = gapi.call(cd.domainAliases(),
                       'get',
                       customer=GC_Values[GC_CUSTOMER_ID],
                       domainAliasName=alias)
    if 'creationTime' in result:
        result['creationTime'] = utils.formatTimestampYMDHMSF(
            result['creationTime'])
    display.print_json(result)


def print_():
    cd = gapi_directory.build()
    todrive = False
    titles = [
        'domainAliasName',
    ]
    csvRows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print domainaliases')
    results = gapi.call(cd.domainAliases(),
                        'list',
                        customer=GC_Values[GC_CUSTOMER_ID])
    for domainAlias in results['domainAliases']:
        domainAlias_attributes = {}
        for attr in domainAlias:
            if attr in ['kind', 'etag']:
                continue
            if attr == 'creationTime':
                domainAlias[attr] = utils.formatTimestampYMDHMSF(
                    domainAlias[attr])
            if attr not in titles:
                titles.append(attr)
            domainAlias_attributes[attr] = domainAlias[attr]
        csvRows.append(domainAlias_attributes)
    display.write_csv_file(csvRows, titles, 'Domains', todrive)
