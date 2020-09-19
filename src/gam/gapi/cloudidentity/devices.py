import csv
import sys

import googleapiclient

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors
from gam.gapi import cloudidentity as gapi_cloudidentity
from gam.gapi.directory import customer as gapi_directory_customer
from gam.gapi.directory import groups as gapi_directory_groups


def create():
    ci = gapi_cloudidentity.build_dwd()
    customer = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    device_types = gapi.get_enum_values_minus_unspecified(
        ci._rootDesc['schemas']['GoogleAppsCloudidentityDevicesV1Device']['properties']['deviceType']['enum'])
    body = {}
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'serialnumber':
            body['serialNumber'] = sys.argv[i+1]
            i += 2
        elif myarg == 'devicetype':
            body['deviceType'] = sys.argv[i+1].upper()
            if body['deviceType'] not in device_types:
                controlflow.expected_argument_exit('device_type',
                                                   ', '.join(device_types),
                                                   sys.argv[i+1])
            i += 2
        else:
           controlflow.invalid_argument_exit(sys.argv[i], 'gam create device') 
    if not body.get('serialNumber') or not body.get('deviceType'):
        controlflow.system_error_exit(
            3, 'serial_number and device_type are required arguments for "gam create device".') 
    result = gapi.call(ci.devices(), 'create', customer=customer, body=body)
    print(f'Created device {result["response"]["name"]}')

def info():
    ci = gapi_cloudidentity.build_dwd()
    customer = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    name = sys.argv[3]
    if not name.startswith('devices/'):
        name = f'devices/{name}'
    device = gapi.call(ci.devices(), 'get', name=name, customer=customer)
    device_users = gapi.get_all_pages(ci.devices().deviceUsers(), 'list',
        'deviceUsers', parent=name, customer=customer)
    display.print_json(device)
    print('Device Users:')
    display.print_json(device_users)

def _generic_action(action, device_user=False):
    ci = gapi_cloudidentity.build_dwd()
    customer = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    
    # bah, inconsistencies in API
    if action == 'delete':
        kwargs = {'customer': customer}
    else:
        kwargs = {'body': {'customer': customer}}

    if device_user:
        endpoint = ci.devices().deviceUsers()
    else:
        endpoint = ci.devices()
    name = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        # The API calls it "name" but GAM will expose as "id" to avoid admin confusion.
        if myarg == 'id':
            name = sys.argv[i+1]
            if not name.startswith('devices/'):
                name = f'devices/{name}'
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], f'gam {action} device')
    if not name:
        controlflow.system_error_exit(3, f'id is a required argument for "gam {action} device".')
    op = gapi.call(endpoint, action, name=name, **kwargs)
    print(op) 

def delete():
     _generic_action('delete')

def cancel_wipe():
     _generic_action('cancelWipe')

def wipe():
     _generic_action('wipe')

def approve_user():
    _generic_action('approve', True)

def block_user():
    _generic_action('block', True)

def cancel_wipe_user():
    _generic_action('cancelWipe', True)

def delete_user():
    _generic_action('delete', True)

def wipe_user():
    _generic_action('wipe', True)

def print_():
    ci = gapi_cloudidentity.build_dwd()
    customer = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    parent = 'devices/-'
    device_filter = None
    get_device_users = True
    get_device_views = ['COMPANY_INVENTORY', 'USER_ASSIGNED_DEVICES']
    titles = []
    csvRows = []
    todrive = False
    sortHeaders = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['filter', 'query']:
          device_filter = sys.argv[i+1]
          i += 2
        elif myarg == 'nocompanydevices':
            get_device_views.remove('COMPANY_INVENTORY')
            i += 1
        elif myarg == 'nopersonaldevices':
            get_device_views.remove('USER_ASSIGNED_DEVICES')
            i += 1
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'sortheaders':
            sortHeaders = True
            i += 1
        else:
           controlflow.invalid_argument_exit(sys.argv[i], 'gam print devices')
    view_name_map = {
      'COMPANY_INVENTORY': 'Company Devices',
      'USER_ASSIGNED_DEVICES': 'Personal Devices',
      }
    devices = []
    for view in get_device_views:
        view_name = view_name_map.get(view, 'Devices')
        page_message = gapi.got_total_items_msg(view_name, '...\n')
        devices += gapi.get_all_pages(ci.devices(), 'list', 'devices',
            customer=customer, page_message=page_message,
            pageSize=100, filter=device_filter, view=view)
    if get_device_users:
        page_message = gapi.got_total_items_msg('Device Users', '...\n')
        device_users = gapi.get_all_pages(ci.devices().deviceUsers(), 'list',
            'deviceUsers', customer=customer, parent=parent,
            page_message=page_message, pageSize=20, filter=device_filter)
        for device_user in device_users:
            for device in devices:
                if device_user.get('name').startswith(device.get('name')):
                    if 'users' not in device:
                        device['users'] = []
                    device['users'].append(device_user)
                    break
    for device in devices:
        device = utils.flatten_json(device)
        for a_key in device:
            if a_key not in titles:
                titles.append(a_key)
        csvRows.append(device)
    if sortHeaders:
        display.sort_csv_titles(['name',], titles)
    display.write_csv_file(csvRows, titles, 'Devices', todrive)


def sync():
    ci = gapi_cloudidentity.build_dwd()
    device_types = gapi.get_enum_values_minus_unspecified(
        ci._rootDesc['schemas']['GoogleAppsCloudidentityDevicesV1Device']['properties']['deviceType']['enum'])
    customer = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    device_filter = None
    csv_file = None
    serialnumber_column = 'serialNumber'
    devicetype_column = 'deviceType'
    static_devicetype = None
    assetid_column = None
    unassigned_missing_action = 'delete'
    assigned_missing_action = 'donothing'
    missing_actions = ['delete', 'wipe', 'donothing']
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['filter', 'query']:
          device_filter = sys.argv[i+1]
          i += 2
        elif myarg == 'csvfile':
          csv_file = sys.argv[i+1]
          i += 2
        elif myarg == 'serialnumbercolumn':
          serialnumber_column = sys.argv[i+1]
          i += 2
        elif myarg == 'devicetypecolumn':
          devicetype_column = sys.argv[i+1]
          i += 2
        elif myarg == 'staticdevicetype':
          static_devicetype = sys.argv[i+1].upper()
          if static_devicetype not in device_types:
                controlflow.expected_argument_exit('device_type',
                                                   ', '.join(device_types),
                                                   sys.argv[i+1])
          i += 2
        elif myarg == 'assetidcolumn':
          assetid_column = sys.argv[i+1]
          i += 2
        elif myarg == 'unassignedmissingaction':
          unassigned_missing_action = sys.argv[i+1].lower().replace('_', '')
          if unassigned_missing_action not in missing_actions:
              controlflow.expected_argument_exit('unassigned_missing_action',
                                                   ', '.join(missing_actions),
                                                   sys.argv[i+1])
          i += 2
        elif myarg == 'assignedmissingaction':
          assigned_missing_action = sys.argv[i+1].lower().replace('_', '')
          if assigned_missing_action not in missing_actions:
              controlflow.expected_argument_exit('assigned_missing_action',
                                                   ', '.join(missing_actions),
                                                   sys.argv[i+1])
          i += 2
        else:
           controlflow.invalid_argument_exit(sys.argv[i], 'gam sync devices')
    if not csv_file:
        controlflow.system_error_exit(
            3, 'csvfile is a required argument for "gam sync devices".') 
    f = fileutils.open_file(csv_file)
    input_file = csv.DictReader(f, restval='')
    if serialnumber_column not in input_file.fieldnames:
        controlflow.csv_field_error_exit(serialnumber_column, input_file.fieldnames)
    if not static_devicetype and devicetype_column not in input_file.fieldnames:
        controlflow.csv_field_error_exit(devicetype_column, input_file.fieldnames)
    if assetid_column and assetid_column not in input_file.fieldnames:
        controlflow.csv_field_error_exit(assetid_column, input_file.fieldnames)
    local_devices = []
    for row in input_file:
        # upper() is very important to comparison since Google
        # always return uppercase serials
        serialnumber = row[serialnumber_column].strip().upper()
        local_device = {'serialNumber': serialnumber}
        if static_devicetype:
            local_device['deviceType'] = static_devicetype
        else:
            local_device['deviceType'] = row[devicetype_column].strip()
        if assetid_column:
            local_device['assetTag'] = row[assetid_column].strip()
        local_devices.append(local_device)
    fileutils.close_file(f)
    page_message = gapi.got_total_items_msg('Company Devices', '...\n')
    device_fields = ['serialNumber', 'deviceType', 'lastSyncTime', 'name']
    if assetid_column:
       device_fields.append('assetTag')
    fields = f'nextPageToken,devices({",".join(device_fields)})'
    remote_devices = gapi.get_all_pages(ci.devices(), 'list', 'devices',
            customer=customer, page_message=page_message,
            pageSize=100, filter=device_filter, view='COMPANY_INVENTORY', fields=fields)
    remote_device_map = {}
    for remote_device in remote_devices:
        sn = remote_device['serialNumber']
        last_sync = remote_device.pop('lastSyncTime')
        name = remote_device.pop('name')
        remote_device_map[sn] = {'name': name}
        if last_sync == '1970-01-01T00:00:00Z':
            remote_device_map[sn]['unassigned'] = True
    devices_to_add = [device for device in local_devices if device not in remote_devices]
    missing_devices = [device for device in remote_devices if device not in local_devices]
    print(f'Need to add {len(devices_to_add)} and remove {len(missing_devices)} devices...')
    for add_device in devices_to_add:
        print(f'Creating {add_device["serialNumber"]}')
        try:
            result = gapi.call(ci.devices(), 'create', customer=customer,
              throw_reasons=[gapi_errors.ErrorReason.FOUR_O_NINE], body=add_device)
            print(f' created {result["response"]["deviceType"]} device {result["response"]["name"]} with serial {result["response"]["serialNumber"]}')
        except googleapiclient.errors.HttpError:
            print(f' {add_device["serialNumber"]} already exists')
    for missing_device in missing_devices:
        sn = missing_device['serialNumber']
        name = remote_device_map[sn]['name']
        unassigned = remote_device_map[sn].get('unassigned')
        action = unassigned_missing_action if unassigned else assigned_missing_action
        if action == 'donothing':
            pass
        else:
            if action == 'delete':
                kwargs = {'customer': customer}
            else:
                kwargs = {'body': {'customer': customer}}
            gapi.call(ci.devices(), unassigned_missing_action,
                name=name, **kwargs)
            print(f'{action}d {sn}')
