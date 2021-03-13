'''Commands to manage directory printers.'''
# pylint: disable=unused-wildcard-import wildcard-import

import sys

from gam import controlflow
from gam import display
from gam import gapi
from gam import getUsersToModify
from gam.var import *
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import orgunits as gapi_directory_orgunits


def _get_customerid():
    ''' returns customer in "customers/C{customer}" format needed for this API'''
    customer = GC_Values[GC_CUSTOMER_ID]
    if customer != MY_CUSTOMER and customer[0] != 'C':
        customer = 'C' + customer
    return f'customers/{customer}'

def _get_printer_attributes(i, cdapi=None):
    '''get printer attributes for create/update commands'''
    body = {}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'description':
            body['description'] = sys.argv[i+1]
            i += 2
        elif myarg == 'displayname':
            body['displayName'] = sys.argv[i+1]
            i += 2
        elif myarg == 'makeandmodel':
            body['makeAndModel'] = sys.argv[i+1]
            i += 2
        elif myarg in ['ou', 'org', 'orgunit', 'orgunitid']:
            _, body['orgUnitId'] = gapi_directory_orgunits.getOrgUnitId(sys.argv[i+1], cdapi)
            body['orgUnitId'] = body['orgUnitId'][3:]
            i += 2
        elif myarg == 'uri':
            body['uri'] = sys.argv[i+1]
            i += 2
        elif myarg in {'driverless', 'usedriverlessconfig'}:
            body['useDriverlessConfig'] = True
            i += 1
    return body


def create():
    '''gam create printer'''
    cdapi = gapi_directory.build()
    parent = _get_customerid()
    body = _get_printer_attributes(3, cdapi)
    result = gapi.call(cdapi.customers().chrome().printers(),
                        'create',
                        parent=parent,
                        body=body)
    display.print_json(result)


def delete():
    '''gam delete printer <PrinterIDList>|(file <FileName>)|(csvfile <FileName>:<FieldName>)'''
    cdapi = gapi_directory.build()
    customer_id = _get_customerid()
    printer_id = sys.argv[3]
    if printer_id.lower() not in {'file', 'csvfile'}:
        printer_ids = printer_id.replace(',', ' ').split()
    else:
        printer_ids = getUsersToModify(f'cros{printer_id.lower()}', sys.argv[4])
    # max 50 per API call
    batch_size = 50
    for chunk in range(0, len(printer_ids), batch_size):
        body = {
                 'printerIds': printer_ids[chunk:chunk + batch_size]
               }
        result = gapi.call(cdapi.customers().chrome().printers(),
                           'batchDeletePrinters',
                           parent=customer_id,
                           body=body)
        for printer_id in result.get('printerIds', []):
            print(f'Deleted printer {printer_id}')
        for printer_id in result.get('failedPrinters', []):
            print(f'ERROR: failed to delete {printer_id.get("printerIds")}')

def print_():
    '''gam print printers'''
    cdapi = gapi_directory.build()
    parent = _get_customerid()
    filter_ = None
    todrive = False
    titles = []
    rows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'filter':
            filter_ = sys.argv[i+1]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print printermodels')
    printers = gapi.get_all_pages(cdapi.customers().chrome().printers(),
                                  'list',
                                  items='printers',
                                  parent=parent,
                                  filter=filter_)
    for printer in printers:
        row = {}
        for key, val in printer.items():
            if key not in titles:
                titles.append(key)
            row[key] = val
        rows.append(row)
    display.write_csv_file(rows, titles, 'Printer', todrive)


def print_models():
    '''gam print printermodels'''
    cdapi = gapi_directory.build()
    parent = _get_customerid()
    filter_ = None
    todrive = False
    titles = []
    rows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'filter':
            filter_ = sys.argv[i+1]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print printermodels')
    models = gapi.get_all_pages(cdapi.customers().chrome().printers(),
                                  'listPrinterModels',
                                  items='printerModels',
                                  parent=parent,
                                  pageSize=10000,
                                  filter=filter_)
    for model in models:
        row = {}
        for key, val in model.items():
            if key not in titles:
                titles.append(key)
            row[key] = val
        rows.append(row)
    display.write_csv_file(rows, titles, 'Printer Models', todrive)


def update():
    '''gam update printer'''
    cdapi = gapi_directory.build()
    customer = _get_customerid()
    printer_id = sys.argv[3]
    name = f'{customer}/chrome/printers/{printer_id}'
    body = _get_printer_attributes(4, cdapi)
    update_mask = ','.join(body)
    # note clearMask seems unnecessary. Updating field to '' clears it.
    result = gapi.call(cdapi.customers().chrome().printers(),
                        'patch',
                        name=name,
                        updateMask=update_mask,
                        body=body)
    display.print_json(result)
