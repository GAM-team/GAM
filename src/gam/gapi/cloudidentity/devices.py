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

def _get_device_customerid():
  customer = GC_Values[GC_CUSTOMER_ID]
  if customer.startswith('C'):
    customer = customer[1:]
  return f'customers/{customer}'

def create():
    ci = gapi_cloudidentity.build_dwd()
    customer = _get_device_customerid()
    device_types = gapi.get_enum_values_minus_unspecified(
        ci._rootDesc['schemas']['GoogleAppsCloudidentityDevicesV1Device']['properties']['deviceType']['enum'])
    body = {'deviceType': '', 'serialNumber': ''}
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
        elif myarg in {'assettag', 'assetid'}:
            body['assetTag'] = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create device')
    if not body['serialNumber'] or not body['deviceType']:
        controlflow.system_error_exit(
            3, 'serial_number and device_type are required arguments for "gam create device".')
    result = gapi.call(ci.devices(), 'create', customer=customer, body=body)
    print(f'Created device {result["response"]["name"]}')


def _parse_action(action):
    kwargs = {}
    i = 3
    name = sys.argv[i]
    if name == 'id':
        i += 1
        name = sys.argv[i]
    i += 1
    if not name.startswith('devices/'):
        name = f'devices/{name}'
    customer = _get_device_customerid()
    # bah, inconsistencies in API
    if action == 'delete':
        kwargs['customer'] = customer
    else:
        kwargs['body'] = {'customer': customer}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if action == 'wipe' and myarg == 'removeresetlock':
            kwargs['body']['removeResetLock'] = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], f'gam {action} device')
    return name, kwargs


def info():
    ci = gapi_cloudidentity.build_dwd()
    customer = _get_device_customerid()
    _, name = _get_deviceuser_name()
    device = gapi.call(ci.devices(), 'get', name=name, customer=customer)
    device_users = gapi.get_all_pages(ci.devices().deviceUsers(), 'list',
        'deviceUsers', parent=name, customer=customer)
    for device_user in device_users:
        parent = device_user['name']
        device_user['client_states'] = gapi.get_all_pages(
                  ci.devices().deviceUsers().clientStates(),
                  'list', 'clientStates', parent=parent, customer=customer)
    display.print_json(device)
    print('Device Users:')
    display.print_json(device_users)


def _generic_action(action, device_user=False):
    ci = gapi_cloudidentity.build_dwd()
    customer = _get_device_customerid()
    name, kwargs = _parse_action(action)
    if device_user:
        endpoint = ci.devices().deviceUsers()
    else:
        endpoint = ci.devices()
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


def _get_deviceuser_name():
    i = 3
    name = sys.argv[i]
    if name == 'id':
        i += 1
        name = sys.argv[i]
    if not name.startswith('devices/'):
        name = f'devices/{name}'
    return (i+1, name)

def info_state():
    ci = gapi_cloudidentity.build_dwd()
    gapi_directory_customer.setTrueCustomerId()
    customer = _get_device_customerid()
    customer_id = customer[10:]
    client_id = f'{customer_id}-gam'
    i, deviceuser = _get_deviceuser_name()
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'clientid':
            client_id = f'{customer_id}-{sys.argv[i+1]}'
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam info deviceuserstate')
    name = f'{deviceuser}/clientStates/{client_id}'
    result = gapi.call(ci.devices().deviceUsers().clientStates(), 'get',
                       name=name, customer=customer)
    display.print_json(result)


def update_state():
    ci = gapi_cloudidentity.build_dwd()
    gapi_directory_customer.setTrueCustomerId()
    customer = _get_device_customerid()
    customer_id = customer[10:]
    client_id = f'{customer_id}-gam'
    body = {}
    i, deviceuser = _get_deviceuser_name()
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'clientid':
            client_id = f'{customer_id}-{sys.argv[i+1]}'
            i += 2
        elif myarg in ['assettag', 'assettags']:
            body['assetTags'] = gam.shlexSplitList(sys.argv[i+1])
            if body['assetTags'] == ['clear']:
                # TODO: this doesn't work to clear
                # existing values. Figure out why.
                body['assetTags'] = [None]
            i += 2
        elif myarg in ['compliantstate', 'compliancestate']:
            comp_states = gapi.get_enum_values_minus_unspecified(
              ci._rootDesc['schemas']['GoogleAppsCloudidentityDevicesV1ClientState']['properties']['complianceState']['enum'])
            body['complianceState'] = sys.argv[i+1].upper()
            if body['complianceState'] not in comp_states:
                controlflow.expected_argument_exit('compliant_state',
                                                   ', '.join(comp_states),
                                                   sys.argv[i+1])
            i += 2
        elif myarg == 'customid':
            body['customId'] = sys.argv[i+1]
            i += 2
        elif myarg == 'healthscore':
            health_scores = gapi.get_enum_values_minus_unspecified(
            ci._rootDesc['schemas']['GoogleAppsCloudidentityDevicesV1ClientState']['properties']['healthScore']['enum'])
            body['healthScore'] = sys.argv[i+1].upper()
            if body['healthScore'] == 'CLEAR':
                body['healthScore'] = None
            if body['healthScore'] and body['healthScore'] not in health_scores:
                controlflow.expected_argument_exit('health_score',
                                                   ', '.join(health_scores),
                                                   sys.argv[i+1])
            i += 2
        elif myarg == 'customvalue':
            allowed_types = ['bool', 'number', 'string']
            value_type = sys.argv[i+1].lower()
            if value_type not in allowed_types:
                controlflow.expected_argument_exit('custom_value',
                                                   ', '.join(allowed_types),
                                                   sys.argv[i+1])
            key = sys.argv[i+2]
            value = sys.argv[i+3]
            if value_type == 'bool':
                value = gam.getBoolean(value, key)
            elif value_type == 'number':
                value = int(value)
            body.setdefault('keyValuePairs', {})
            body['keyValuePairs'][key] = {f'{value_type}Value': value}
            i += 4
        elif myarg in ['managedstate']:
            managed_states = gapi.get_enum_values_minus_unspecified(
              ci._rootDesc['schemas']['GoogleAppsCloudidentityDevicesV1ClientState']['properties']['managed']['enum'])
            body['managed'] = sys.argv[i+1].upper()
            if body['managed'] == 'CLEAR':
                body['managed'] = None
            if body['managed'] and body['managed'] not in managed_states:
                controlflow.expected_argument_exit('managed_state',
                                                   ', '.join(managed_states),
                                                   sys.argv[i+1])
            i += 2
        elif myarg in ['scorereason']:
            body['scoreReason'] = sys.argv[i+1]
            if body['scoreReason'] == 'clear':
                body['scoreReason'] = None
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam update deviceuserstate')
    name = f'{deviceuser}/clientStates/{client_id}'
    updateMask = ','.join(body.keys())
    result = gapi.call(ci.devices().deviceUsers().clientStates(), 'patch',
                       name=name, customer=customer, updateMask=updateMask, body=body)
    display.print_json(result)


def print_():
    ci = gapi_cloudidentity.build_dwd()
    customer = _get_device_customerid()
    parent = 'devices/-'
    device_filter = None
    get_device_users = True
    view = None
    orderByList = []
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
        elif myarg == 'company':
            view = 'COMPANY_INVENTORY'
            i += 1
        elif myarg == 'personal':
            view = 'USER_ASSIGNED_DEVICES'
            i += 1
        elif myarg == 'nocompanydevices':
            view = 'USER_ASSIGNED_DEVICES'
            i += 1
        elif myarg == 'nopersonaldevices':
            view = 'COMPANY_INVENTORY'
            i += 1
        elif myarg == 'nodeviceusers':
            get_device_users = False
            i += 1
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'orderby':
            fieldName = sys.argv[i + 1].lower()
            i += 2
            if fieldName in DEVICE_ORDERBY_CHOICES_MAP:
                fieldName = DEVICE_ORDERBY_CHOICES_MAP[fieldName]
                orderBy = ''
                if i < len(sys.argv):
                    orderBy = sys.argv[i].lower()
                    if orderBy in SORTORDER_CHOICES_MAP:
                        orderBy = SORTORDER_CHOICES_MAP[orderBy]
                        i += 1
                if orderBy != 'DESCENDING':
                    orderByList.append(fieldName)
                else:
                    orderByList.append(f'{fieldName} desc')
            else:
                controlflow.expected_argument_exit(
                    'orderby', ', '.join(sorted(DEVICE_ORDERBY_CHOICES_MAP)),
                    fieldName)
        elif myarg == 'sortheaders':
            sortHeaders = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print devices')
    view_name_map = {
      None: 'Devices',
      'COMPANY_INVENTORY': 'Company Devices',
      'USER_ASSIGNED_DEVICES': 'Personal Devices',
      }
    if orderByList:
        orderBy = ','.join(orderByList)
    else:
        orderBy = None
    devices = []
    page_message = gapi.got_total_items_msg(view_name_map[view], '...\n')
    devices += gapi.get_all_pages(ci.devices(), 'list', 'devices',
        customer=customer, page_message=page_message,
        pageSize=100, filter=device_filter, view=view, orderBy=orderBy)
    if get_device_users:
        page_message = gapi.got_total_items_msg('Device Users', '...\n')
        device_users = gapi.get_all_pages(ci.devices().deviceUsers(), 'list',
            'deviceUsers', customer=customer, parent=parent,
            page_message=page_message, pageSize=1, filter=device_filter)
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
    customer = _get_device_customerid()
    device_filter = None
    csv_file = None
    serialnumber_column = 'serialNumber'
    devicetype_column = 'deviceType'
    static_devicetype = None
    assettag_column = None
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
        elif myarg in {'assettagcolumn', 'assetidcolumn'}:
          assettag_column = sys.argv[i+1]
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
    if assettag_column and assettag_column not in input_file.fieldnames:
        controlflow.csv_field_error_exit(assettag_column, input_file.fieldnames)
    local_devices = {}
    for row in input_file:
        # upper() is very important to comparison since Google
        # always return uppercase serials
        local_device = {'serialNumber': row[serialnumber_column].strip().upper()}
        if static_devicetype:
            local_device['deviceType'] = static_devicetype
        else:
            local_device['deviceType'] = row[devicetype_column].strip()
        sndt = f"{local_device['serialNumber']}-{local_device['deviceType']}"
        if assettag_column:
            local_device['assetTag'] = row[assettag_column].strip()
            sndt += f"-{local_device['assetTag']}"
        local_devices[sndt] = local_device
    fileutils.close_file(f)
    page_message = gapi.got_total_items_msg('Company Devices', '...\n')
    device_fields = ['serialNumber', 'deviceType', 'lastSyncTime', 'name']
    if assettag_column:
       device_fields.append('assetTag')
    fields = f'nextPageToken,devices({",".join(device_fields)})'
    remote_devices = {}
    remote_device_map = {}
    result = gapi.get_all_pages(ci.devices(), 'list', 'devices',
            customer=customer, page_message=page_message,
            pageSize=100, filter=device_filter, view='COMPANY_INVENTORY', fields=fields)
    for remote_device in result:
        sn = remote_device['serialNumber']
        last_sync = remote_device.pop('lastSyncTime', NEVER_TIME_NOMS)
        name = remote_device.pop('name')
        sndt = f"{remote_device['serialNumber']}-{remote_device['deviceType']}"
        if assettag_column:
            if 'assetTag' not in remote_device:
                remote_device['assetTag'] = ''
            sndt += f"-{remote_device['assetTag']}"
        remote_devices[sndt] = remote_device
        remote_device_map[sndt] = {'name': name}
        if last_sync == NEVER_TIME_NOMS:
            remote_device_map[sndt]['unassigned'] = True
    devices_to_add = []
    for sndt, device in iter(local_devices.items()):
      if sndt not in remote_devices:
        devices_to_add.append(device)
    missing_devices = []
    for sndt, device in iter(remote_devices.items()):
      if sndt not in local_devices:
        missing_devices.append(device)
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
        sndt = f"{sn}-{missing_device['deviceType']}"
        if assettag_column:
          sndt += f"-{missing_device['assetTag']}"
        name = remote_device_map[sndt]['name']
        unassigned = remote_device_map[sndt].get('unassigned')
        action = unassigned_missing_action if unassigned else assigned_missing_action
        if action == 'donothing':
            pass
        else:
            if action == 'delete':
                kwargs = {'customer': customer}
            else:
                kwargs = {'body': {'customer': customer}}
            gapi.call(ci.devices(), action,
                name=name, **kwargs)
            print(f'{action}d {sn}')
