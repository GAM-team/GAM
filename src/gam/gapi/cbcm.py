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


def _get_customerid():
    ''' returns customer id without C prefix'''
    customer_id = GC_Values[GC_CUSTOMER_ID]
    if customer_id[0] == 'C':
        customer_id = customer_id[1:]
    return customer_id


def build():
    return gam.buildGAPIObject('cbcm')


def delete():
    cbcm = build()
    device_id = sys.argv[3]
    customer_id = _get_customerid()
    gapi.call(cbcm.chromebrowsers(), 'delete', deviceId=device_id,
              customer=customer_id)
    print(f'Deleted browser {device_id}')


def info():
    cbcm = build()
    device_id = sys.argv[3]
    projection = 'BASIC'
    fields = None
    customer_id = _get_customerid()
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
                        customer=customer_id,
                        fields=fields, deviceId=device_id,
                        projection=projection)
    display.print_json(browser)


def move():
    cbcm = build()
    body = {'resource_ids': []}
    customer_id = _get_customerid()
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
                         customer=customer_id,
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
                                              'gam move browsers')
    if 'org_unit_path' not in body:
        controlflow.missing_argument_exit('ou', 'gam move browsers')
    elif not resource_ids:
        controlflow.missing_argument_exit('query or ids',
                                          'gam move browsers')
    # split moves into max 600 devices per batch
    for chunk in range(0, len(resource_ids), batch_size):
        body['resource_ids'] = resource_ids[chunk:chunk + batch_size]
        print(f' moving {len(body["resource_ids"])} browsers to ' \
                       f'{body["org_unit_path"]}')
        gapi.call(cbcm.chromebrowsers(), 'moveChromeBrowsersToOu',
                  customer=customer_id, body=body)


def print_():
    cbcm = build()
    customer_id = _get_customerid()
    projection = 'BASIC'
    orgUnitPath = query = None
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
        elif myarg in ['ou', 'org', 'orgunit']:
            orgUnitPath = gapi_directory_orgunits.getOrgUnitItem(sys.argv[i + 1], pathOnly=True, absolutePath=True)
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
            fields = sys.argv[i + 1].replace(',', ' ').split()
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print browsers')
    if fields:
        fields.append('deviceId')
        fields = f'browsers({",".join(set(fields))}),nextPageToken'
    page_message = gapi.got_total_items_msg('Browsers', '...\n')
    browsers = gapi.get_all_pages(cbcm.chromebrowsers(), 'list',
                         'browsers', page_message=page_message,
                         customer=customer_id,
                         orgUnitPath=orgUnitPath, query=query, projection=projection,
                         fields=fields)
    for browser in browsers:
        browser = utils.flatten_json(browser)
        for a_key in browser:
            if a_key not in titles:
                titles.append(a_key)
        csv_rows.append(browser)
    if sort_headers:
        display.sort_csv_titles(['deviceId',], titles)
    display.write_csv_file(csv_rows, titles, 'Browsers', todrive)


attributes = {
    'assetid': 'annotatedAssetId',
    'location': 'annotatedLocation',
    'notes': 'annotatedNotes',
    'user': 'annotatedUser'
    }
attribute_fields = ','.join(list(attributes.values()))

def update():
    cbcm = build()
    customer_id = _get_customerid()
    device_id = sys.argv[3]
    body = {'deviceId': device_id}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in attributes:
            body[attributes[myarg]] = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam update browser')
    browser = gapi.call(cbcm.chromebrowsers(), 'get', deviceId=device_id,
                        customer=customer_id,
                        projection='BASIC', fields=attribute_fields)
    browser.update(body)
    result = gapi.call(cbcm.chromebrowsers(), 'update', deviceId=device_id,
                       customer=customer_id, body=browser,
                       projection='BASIC', fields="deviceId")
    print(f'Updated browser {result["deviceId"]}')


def createtoken():
    cbcm = build()
    customer_id = _get_customerid()
    body = {'token_type': 'CHROME_BROWSER'}
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['ou', 'orgunit', 'org']:
            body['org_unit_path'] = gapi_directory_orgunits.getOrgUnitItem(sys.argv[i + 1])
            i += 2
        elif myarg in ['expire', 'expires']:
            body['expire_time'] = utils.get_time_or_delta_from_now(sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam create browsertoken')
    browser = gapi.call(cbcm.enrollmentTokens(), 'create',
                        customer=customer_id, body=body)
    print(f'Created browser enrollment token {browser["token"]}')


def revoketoken():
    cbcm = build()
    customer_id = _get_customerid()
    token_permanent_id = sys.argv[3]
    gapi.call(cbcm.enrollmentTokens(), 'revoke', tokenPermanentId=token_permanent_id,
              customer=customer_id)
    print(f'Deleted browser enrollment token {token_permanent_id}')


def printshowtokens(csvFormat):
    cbcm = build()
    customer_id = _get_customerid()
    query = None
    fields = None
    if csvFormat:
        titles = ['token']
        csv_rows = []
        todrive = False
        sort_headers = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'query':
            query = sys.argv[i+1]
            i += 2
        elif csvFormat and myarg == 'todrive':
            todrive = True
            i += 1
        elif csvFormat and myarg == 'sortheaders':
            sort_headers = True
            i += 1
        elif myarg == 'fields':
            fields = sys.argv[i + 1].replace(',', ' ').split()
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                f"gam {['show', 'print'][csvFormat]} browsertokens")
    if fields:
        fields.append('token')
        fields = f'chromeEnrollmentTokens({",".join(set(fields))}),nextPageToken'
    page_message = gapi.got_total_items_msg('Chrome Browser Enrollment Tokens', '...\n')
    browsers = gapi.get_all_pages(cbcm.enrollmentTokens(), 'list',
                         'chromeEnrollmentTokens', page_message=page_message,
                         customer=customer_id,
                         query=query, fields=fields)
    if not csvFormat:
        count = len(browsers)
        print(f'Show {count} Chrome Browser Enrollment Tokens')
        i = 0
        for browser in browsers:
            i += 1
            print(f'  Chrome Browser Enrollment Token: {browser["token"]}{gam.currentCount(i, count)}')
            browser.pop('kind', None)
            for field in browser:
                print(f'    {field}: {browser[field]}')
    else:
        for browser in browsers:
            browser = utils.flatten_json(browser)
            for a_key in browser:
                if a_key not in titles:
                    titles.append(a_key)
            csv_rows.append(browser)
        if sort_headers:
            display.sort_csv_titles(['token',], titles)
        display.write_csv_file(csv_rows, titles, 'Chrome Browser Enrollment Tokens', todrive)
