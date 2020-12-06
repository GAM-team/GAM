"""Chrome Browser Cloud Management API calls"""

import csv
import os.path
import sys

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam import utils


def build():
    return gam.buildGAPIObject('cbcm')


def delete():
    cbcm = build()
    device_id = sys.argv[3]
    gapi.call(cbcm.chromebrowsers(), 'delete', deviceId=device_id,
              customer=GC_Values[GC_CUSTOMER_ID])
    print(f'Deleted browser {device_id}')


def info():
    cbcm = build()
    device_id = sys.argv[3]
    projection = 'BASIC'
    fields = None
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['basic', 'full']:
            projection = myarg.upper()
            i += 1
        elif myarg == 'fields':
            fields = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam info browser')
    browser = gapi.call(cbcm.chromebrowsers(), 'get',
                        customer=GC_Values[GC_CUSTOMER_ID],
                        fields=fields, deviceId=device_id,
                        projection=projection)
    display.print_json(browser)


def move():
    cbcm = build()
    body = {'resource_ids': []}
    i = 3
    resource_ids = []
    batch_size = 600
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'ids':
            resource_ids.extend(sys.argv[i + 1].split(','))
            i += 2
        elif myarg == 'query':
            query = sys.argv[i + 1]
            page_message = gapi.got_total_items_msg('Browsers', '...\n')
            browsers = gapi.get_all_pages(cbcm.chromebrowsers(), 'list',
                         'browsers', page_message=page_message,
                         customer=GC_Values[GC_CUSTOMER_ID],
                         query=query, projection='BASIC',
                         fields='browsers(deviceId),nextPageToken')
            ids = [browser['deviceId'] for browser in browsers]
            resource_ids.extend(ids)
            i += 2
        elif myarg == 'file':
            with fileutils.open_file(sys.argv[i+1], strip_utf_bom=True) as filed:
                for row in filed:
                    rid = row.strip()
                    if rid:
                        resource_ids.append(rid)
            i += 2
        elif myarg == 'csvfile':
            drive, fname_column = os.path.splitdrive(sys.argv[i+1])
            if fname_column.find(':') == -1:
                controlflow.system_error_exit(
                    2, 'Expected csvfile FileName:FieldName')
            (filename, column) = fname_column.split(':')
            with fileutils.open_file(drive + filename) as filed:
                input_file = csv.DictReader(filed, restval='')
                if column not in input_file.fieldnames:
                    controlflow.csv_field_error_exit(column,
                                                     input_file.fieldnames)
                for row in input_file:
                    rid = row[column].strip()
                    if rid:
                        resource_ids.append(rid)
            i += 2
        elif myarg in ['ou', 'orgunit', 'org']:
            org_unit = gapi_directory_orgunits.getOrgUnitItem(sys.argv[i + 1])
            body['org_unit_path'] = org_unit
            i += 2
        elif myarg == 'batchsize':
            batch_size = int(sys.argv[i+1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam update browsers')
    if 'org_unit_path' not in body:
        controlflow.missing_argument_exit('ou', 'gam update browsers')
    elif not resource_ids:
        controlflow.missing_argument_exit('query or ids',
                                          'gam update browsers')
    # split moves into max 600 devices per batch
    for chunk in range(0, len(resource_ids), batch_size):
        body['resource_ids'] = resource_ids[chunk:chunk + batch_size]
        print(f' moving {len(body["resource_ids"])} browsers to ' \
                       f'{body["org_unit_path"]}')
        gapi.call(cbcm.chromebrowsers(), 'moveChromeBrowsersToOu',
                  customer=GC_Values[GC_CUSTOMER_ID], body=body)


def print_():
    cbcm = build()
    projection = 'BASIC'
    query = None
    fields = None
    titles = []
    csv_rows = []
    todrive = False
    sort_headers = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'query':
            query = sys.argv[i+1]
            i += 2
        elif myarg == 'projection':
            projection = sys.argv[i + 1].upper()
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'sortheaders':
            sort_headers = True
            i += 1
        elif myarg == 'fields':
            fields = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print browsers')
    if fields:
        fields = f'browsers({fields}),nextPageToken'
    page_message = gapi.got_total_items_msg('Browsers', '...\n')
    browsers = gapi.get_all_pages(cbcm.chromebrowsers(), 'list',
                         'browsers', page_message=page_message,
                         customer=GC_Values[GC_CUSTOMER_ID],
                         query=query, projection=projection,
                         fields=fields)
    for browser in browsers:
        browser = utils.flatten_json(browser)
        for a_key in browser:
            if a_key not in titles:
                titles.append(a_key)
        csv_rows.append(browser)
    if sort_headers:
        display.sort_csv_titles(['name',], titles)
    display.write_csv_file(csv_rows, titles, 'Browsers', todrive)

def update():
    cbcm = build()
    device_id = sys.argv[3]
    body = {'deviceId': device_id}
    attributes = ['user', 'location', 'notes', 'assetid']
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in attributes:
            attribute = f'annotated{myarg.capitalize()}'
            body[attribute] = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print browsers')
    result = gapi.call(cbcm.chromebrowsers(), 'update', deviceId=device_id,
                       customer=GC_Values[GC_CUSTOMER_ID], body=body,
                       projection='BASIC', fields="deviceId")
    print(f'Updated browser {result["deviceId"]}')
