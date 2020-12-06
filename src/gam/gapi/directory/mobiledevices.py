import sys
import uuid

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam import utils


def delete():
    cd = gapi_directory.build()
    resourceId = sys.argv[3]
    gapi.call(cd.mobiledevices(),
              'delete',
              resourceId=resourceId,
              customerId=GC_Values[GC_CUSTOMER_ID])



def info():
    cd = gapi_directory.build()
    resourceId = sys.argv[3]
    device_info = gapi.call(cd.mobiledevices(),
                            'get',
                            customerId=GC_Values[GC_CUSTOMER_ID],
                            resourceId=resourceId)
    if 'deviceId' in device_info:
        device_info['deviceId'] = device_info['deviceId'].encode('unicode-escape').decode(
            UTF8)
    attrib = 'securityPatchLevel'
    if attrib in device_info and int(device_info[attrib]):
        device_info[attrib] = utils.formatTimestampYMDHMS(device_info[attrib])
    display.print_json(device_info)



def print_():
    cd = gapi_directory.build()
    todrive = False
    titles = []
    csvRows = []
    fields = None
    projection = orderBy = sortOrder = None
    queries = [None]
    delimiter = ' '
    listLimit = 1
    appsLimit = -1
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['query', 'queries']:
            queries = gam.getQueries(myarg, sys.argv[i + 1])
            i += 2
        elif myarg == 'delimiter':
            delimiter = sys.argv[i + 1]
            i += 2
        elif myarg == 'listlimit':
            listLimit = gam.getInteger(sys.argv[i + 1], myarg, minVal=-1)
            i += 2
        elif myarg == 'appslimit':
            appsLimit = gam.getInteger(sys.argv[i + 1], myarg, minVal=-1)
            i += 2
        elif myarg == 'fields':
            fields = f'nextPageToken,mobiledevices({sys.argv[i+1]})'
            i += 2
        elif myarg == 'orderby':
            orderBy = sys.argv[i + 1].lower()
            validOrderBy = [
                'deviceid', 'email', 'lastsync', 'model', 'name', 'os',
                'status', 'type'
            ]
            if orderBy not in validOrderBy:
                controlflow.expected_argument_exit('orderby',
                                                   ', '.join(validOrderBy),
                                                   orderBy)
            if orderBy == 'lastsync':
                orderBy = 'lastSync'
            elif orderBy == 'deviceid':
                orderBy = 'deviceId'
            i += 2
        elif myarg in SORTORDER_CHOICES_MAP:
            sortOrder = SORTORDER_CHOICES_MAP[myarg]
            i += 1
        elif myarg in PROJECTION_CHOICES_MAP:
            projection = PROJECTION_CHOICES_MAP[myarg]
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print mobile')
    for query in queries:
        gam.printGettingAllItems('Mobile Devices', query)
        page_message = gapi.got_total_items_msg('Mobile Devices', '...\n')
        all_mobile = gapi.get_all_pages(cd.mobiledevices(),
                                        'list',
                                        'mobiledevices',
                                        page_message=page_message,
                                        customerId=GC_Values[GC_CUSTOMER_ID],
                                        query=query,
                                        projection=projection,
                                        fields=fields,
                                        orderBy=orderBy,
                                        sortOrder=sortOrder)
        for mobile in all_mobile:
            row = {}
            for attrib in mobile:
                if attrib in ['kind', 'etag']:
                    continue
                if attrib in ['name', 'email', 'otherAccountsInfo']:
                    if attrib not in titles:
                        titles.append(attrib)
                    if listLimit > 0:
                        row[attrib] = delimiter.join(
                            mobile[attrib][0:listLimit])
                    elif listLimit == 0:
                        row[attrib] = delimiter.join(mobile[attrib])
                elif attrib == 'applications':
                    if appsLimit >= 0:
                        if attrib not in titles:
                            titles.append(attrib)
                        applications = []
                        j = 0
                        for app in mobile[attrib]:
                            j += 1
                            if appsLimit and (j > appsLimit):
                                break
                            appDetails = []
                            for field in [
                                    'displayName', 'packageName', 'versionName'
                            ]:
                                appDetails.append(app.get(field, '<None>'))
                            appDetails.append(
                                str(app.get('versionCode', '<None>')))
                            permissions = app.get('permission', [])
                            if permissions:
                                appDetails.append('/'.join(permissions))
                            else:
                                appDetails.append('<None>')
                            applications.append('-'.join(appDetails))
                        row[attrib] = delimiter.join(applications)
                else:
                    if attrib not in titles:
                        titles.append(attrib)
                    if attrib == 'deviceId':
                        row[attrib] = mobile[attrib].encode(
                            'unicode-escape').decode(UTF8)
                    elif attrib == 'securityPatchLevel' and int(mobile[attrib]):
                        row[attrib] = utils.formatTimestampYMDHMS(
                            mobile[attrib])
                    else:
                        row[attrib] = mobile[attrib]
            csvRows.append(row)
    display.sort_csv_titles(
        ['resourceId', 'deviceId', 'serialNumber', 'name', 'email', 'status'],
        titles)
    display.write_csv_file(csvRows, titles, 'Mobile', todrive)


def update():
    cd = gapi_directory.build()
    resourceIds = sys.argv[3]
    match_users = None
    doit = False
    if resourceIds[:6] == 'query:':
        query = resourceIds[6:]
        fields = 'nextPageToken,mobiledevices(resourceId,email)'
        page_message = gapi.got_total_items_msg('Mobile Devices', '...\n')
        devices = gapi.get_all_pages(cd.mobiledevices(),
                                     'list',
                                     page_message=page_message,
                                     customerId=GC_Values[GC_CUSTOMER_ID],
                                     items='mobiledevices',
                                     query=query,
                                     fields=fields)
    else:
        devices = [{'resourceId': resourceIds, 'email': ['not set']}]
        doit = True
    i = 4
    body = {}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'action':
            body['action'] = sys.argv[i + 1].lower()
            validActions = [
                'wipe', 'wipeaccount', 'accountwipe', 'wipe_account',
                'account_wipe', 'approve', 'block',
                'cancel_remote_wipe_then_activate',
                'cancel_remote_wipe_then_block'
            ]
            if body['action'] not in validActions:
                controlflow.expected_argument_exit('action',
                                                   ', '.join(validActions),
                                                   body['action'])
            if body['action'] == 'wipe':
                body['action'] = 'admin_remote_wipe'
            elif body['action'].replace('_',
                                        '') in ['accountwipe', 'wipeaccount']:
                body['action'] = 'admin_account_wipe'
            i += 2
        elif myarg in ['ifusers', 'matchusers']:
            match_users = gam.getUsersToModify(entity_type=sys.argv[i + 1].lower(),
                                           entity=sys.argv[i + 2])
            i += 3
        elif myarg == 'doit':
            doit = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam update mobile')
    if body:
        if doit:
            print(f'Updating {len(devices)} devices')
            describe_as = 'Performing'
        else:
            print(
                f'Showing {len(devices)} changes that would be made, not actually making changes because doit argument not specified'
            )
            describe_as = 'Would perform'
        for device in devices:
            device_user = device.get('email', [''])[0]
            if match_users and device_user not in match_users:
                print(
                    f'Skipping device for user {device_user} that did not match match_users argument'
                )
            else:
                print(
                    f'{describe_as} {body["action"]} on user {device_user} device {device["resourceId"]}'
                )
                if doit:
                    gapi.call(cd.mobiledevices(),
                              'action',
                              resourceId=device['resourceId'],
                              body=body,
                              customerId=GC_Values[GC_CUSTOMER_ID])
