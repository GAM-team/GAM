import string
import sys

import googleapiclient.errors

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors
from gam.gapi import cloudresourcemanager as gapi_crm


THROW_REASONS = [gapi_errors.ErrorReason.FOUR_O_THREE]

def _gen_role_error(caa):
    sa_email = caa._http.credentials.signer_email
    role_error = f'Please grant service account {sa_email} the Access Context Manager Editor role to your GCP organization.'
    controlflow.system_error_exit(2, role_error)


def build():
    return gam.buildGAPIServiceObject('accesscontextmanager',
                                      act_as=None)


def get_access_policy(caa=None):
    if not caa:
        build()
    parent = gapi_crm.get_org_id()
    if not parent:
        _gen_role_error(caa)
    try:
        aps = gapi.get_all_pages(caa.accessPolicies(),
                                 'list',
                                 'accessPolicies',
                                 throw_reasons=THROW_REASONS,
                                 parent=parent,
                                 fields='accessPolicies(name,title)')
    except googleapiclient.errors.HttpError:
        _gen_role_error(caa)
    if not aps:
        controlflow.system_error_exit(2, 'You don\'t seem to have any access policies. That is odd.')
    elif len(aps) == 1:
        return aps[0]['name']
    for ap in aps:
        if ap.get('title') == 'Access policy created in Cloud Identity Console':
            return ap['name']
    controlflow.system_error_exit(2, ' Could not find a org level access policy. That is odd.')


def print_access_levels():
    caa = build()
    ap_name = get_access_policy(caa)
    try:
        levels = gapi.get_all_pages(caa.accessPolicies().accessLevels(),
                                    'list',
                                    'accessLevels',
                                    throw_reasons=THROW_REASONS,
                                    parent=ap_name,
                                    accessLevelFormat='CEL', fields='*')
    except googleapiclient.errors.HttpError:
        _gen_role_error(caa)
    for level in levels:
        display.print_json(level)
        print()


def build_os_constraints(constraints):
    consts_obj = []
    constraints = constraints.upper().split(',')
    valid_os_types = ['DESKTOP_MAC', 'DESKTOP_WINDOWS', 'DESKTOP_LINUX', 'DESKTOP_CHROMEOS', 'ANDROID', 'IOS'] 
    for constraint in constraints:
        new_const = {}
        new_const['osType'], new_const['minimumVersion'] = constraint.split(':')
        if new_const['osType'] == 'VERIFIED_DESKTOP_CHROME_OS':
            new_const['osType'] = 'DESKTOP_CHROME_OS'
            new_const['requireVerifiedChromeOs'] = True
        if new_const['osType'] not in valid_os_types:
            controlflow.system_error_exit(2, f'expected os type of {", ".join(valid_os_types)} got {new_const["osType"]}')
        consts_obj.append(new_const)
    return consts_obj


def build_device_policy(i, schemas):
    device_policy = {}
    while True:
        myarg = sys.argv[i].replace('_', '').lower()
        if myarg == 'requirescreenlock':
            device_policy['requireScreenLock'] = gam.getBoolean(sys.argv[i+1], myarg)
            i += 2
        elif myarg == 'allowedencryptionstatuses':
            allowed_statuses = gapi.get_enum_values_minus_unspecified(schemas["DevicePolicy"]["properties"]["allowedEncryptionStatuses"]["items"]["enum"])
            device_policy['allowedEncryptionStatuses'] = sys.argv[i+1].upper().split(',')
            for status in device_policy['allowedEncryptionStatuses']:
                if status not in allowed_statuses:
                    controlflow.system_error_exit(2, f'expected encryption status of {", ".join(allowed_statuses)} got {status}')
            i += 2
        elif myarg == 'osconstraints':
            device_policy['osConstraints'] = build_os_constraints(sys.argv[i+1])
            i += 2
        elif myarg == 'alloweddevicemanagementlevels':
            allowed_levels = gapi.get_enum_values_minus_unspecified(schemas["DevicePolicy"]["properties"]["allowedDeviceManagementLevels"]["items"]["enum"])
            device_policy['allowedDeviceManagementLevels'] = sys.argv[i+1].upper().split(',')
            for level in device_policy['allowedDeviceManagementLevels']:
                if level == 'ADVANCED':
                    level == 'COMPLETE'
                if level not in allowed_levels:
                    controlflow.system_error_exit(2, f'expected device management level of {", ".join(allowed_levels)} got {level}')
            i += 2
        elif myarg == 'requireadminapproval':
            device_policy['requireAdminApproval'] = gam.getBoolean(sys.argv[i+1], myarg)
            i += 2
        elif myarg == 'requirecorpowned':
            device_policy['requireCorpOwned'] = gam.getBoolean(sys.argv[i+1], myarg)
            i += 2
        elif myarg == 'enddevicepolicy':
            i += 1
            break
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create/update caalevel')
    return i, device_policy


def build_condition(i, schemas):
    condition = {}
    while True:
        myarg = sys.argv[i].replace('_', '').lower()
        if myarg == 'ipsubnetworks':
            condition['ipSubnetworks'] = sys.argv[i+1].split(',')
            i += 2
        elif myarg == 'devicepolicy':
            i += 1
            i, condition['devicePolicy'] = build_device_policy(i, schemas)
        elif myarg == 'requiredaccesslevels':
            condition['requiredaccesslevels'] = sys.argv[i+1].split(',')
            i += 2
        elif myarg == 'negate':
            condition['negate'] = gam.getBoolean(sys.argv[i+1], myarg)
            i += 2
        elif myarg == 'members':
            condition['members'] = sys.argv[i+1].split(',')
            i += 2
        elif myarg == 'regions':
            condition['regions'] = sys.argv[i+1].split(',')
            i += 2
        elif myarg == 'endcondition':
            i += 1
            break
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create/update caalevel')
    return i, condition


def build_basic_level(i, schemas):
    basic_level = {'conditions': []}
    valid_functions = gapi.get_enum_values_minus_unspecified(schemas['BasicLevel']['properties']['combiningFunction']['enum'])
    while i < len(sys.argv):
        myarg = sys.argv[i].replace('_', '').lower()
        if myarg == 'combiningfunction':
            combiningFunction = sys.argv[i+1].upper()
            if combiningFunction not in valid_functions:
                controlflow.system_error_exit(2, f'expected combining function of {",".join(valid_functions)} got {combiningFunction}')
            basic_level['combiningFunction'] = combiningFunction
            i += 2
        elif myarg == 'condition':
            i += 1
            i, condition = build_condition(i, schemas)
            basic_level['conditions'].append(condition)
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create/update caalevel') 
    return i, basic_level


def create_access_level():
    caa = build()
    ap_name = get_access_policy(caa)
    title = sys.argv[3].replace(' ', '_')
    custom = {'expr': {'expression': sys.argv[4], 'title': 'expr'}}
    allowed_title_chars = string.ascii_letters + string.digits + '_'
    name = ''.join([c for c in title if c in allowed_title_chars])[:49]
    name = f'{ap_name}/accessLevels/{name}'
    body = {
            'name': name,
            'title': title,
           }
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'basic':
            schemas = caa._rootDesc['schemas']
            i += 1
            i, body['basic'] = build_basic_level(i, schemas)
        elif myarg == 'custom':
            body['custom'] = {'expr': {'expression': sys.argv[i+1], 'title': 'expr'}}
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create caalevel')
    print(f'Creating access level {name}...')
    try:
        gapi.call(caa.accessPolicies().accessLevels(),
                  'create',
                  throw_reasons=THROW_REASONS,
                  parent=ap_name,
                  body=body)
    except googleapiclient.errors.HttpError:
        _gen_role_error(caa)

def update_access_level():
    caa = build()
    name = sys.argv[3]
    if not name.startswith('accessPolicies/'):
        ap_name = get_access_policy(caa)
        name = f'{ap_name}/accessLevels/{name}'
    body = {}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'basic':
            schemas = caa._rootDesc['schemas']
            i += 1
            i, body['basic'] = build_basic_level(i, schemas)
        elif myarg == 'custom':
            body['custom'] = {'expr': {'expression': sys.argv[i+1], 'title': 'expr'}}
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam update caalevel')
    updateMask = ','.join(body.keys())
    print(f'Updating access level {name}...')
    try:
        gapi.call(caa.accessPolicies().accessLevels(),
                  'patch',
                  throw_reasons=THROW_REASONS,
                  name=name,
                  updateMask=updateMask,
                  body=body)
    except googleapiclient.errors.HttpError:
        _gen_role_error(caa)

def delete_access_level():
    caa = build()
    name = sys.argv[3]
    if not name.startswith('accessPolicies/'):
        ap_name = get_access_policy(caa)
        name = f'{ap_name}/accessLevels/{name}'
    print(f'Deleting access level {name}...')
    try:
        gapi.call(caa.accessPolicies().accessLevels(),
                  'delete',
                  name=name)
    except googleapiclient.errors.HttpError:
        _gen_role_error(caa)
