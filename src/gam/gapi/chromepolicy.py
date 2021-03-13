"""Chrome Browser Cloud Management API calls"""

import json
import sys

import gam
from gam.var import *
from gam import controlflow
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam import utils

import googleapiclient.errors


def _get_customerid():
  customer = GC_Values[GC_CUSTOMER_ID]
  if customer != MY_CUSTOMER and customer[0] != 'C':
    customer = 'C' + customer
  return f'customers/{customer}'


def _get_orgunit(orgunit):
    if orgunit.startswith('orgunits/'):
        return orgunit
    _, orgunitid = gapi_directory_orgunits.getOrgUnitId(orgunit)
    return f'orgunits/{orgunitid[3:]}'


def build():
    return gam.buildGAPIObject('chromepolicy')


def print_policies():
    cp = build()
    customer = _get_customerid()
    if len(sys.argv) < 4:
        orgunit = '/'
    else:
        orgunit = sys.argv[3]
    orgunit = _get_orgunit(orgunit)
    namespaces = [
            'chrome.users',
#            'chrome.users.apps',
#            'chrome.devices',
#            'chrome.devices.managedGuest',
#            'chrome.devices.managedGuest.apps',
#            'chrome.devices.kiosk',
#            'chrome.devices.kiosk.apps',
#            'chrome.printers',
            ]
    body = {
             'policyTargetKey': {
               'targetResource': orgunit,
             }
           }
    throw_reasons = [gapi_errors.ErrorReason.FOUR_O_O,]
    for namespace in namespaces:
        body['policySchemaFilter'] = f'{namespace}.*'
        try:
            policies = gapi.get_all_pages(cp.customers().policies(), 'resolve',
                                          items='resolvedPolicies',
                                          throw_reasons=throw_reasons,
                                          customer=customer,
                                          body=body)
        except googleapiclient.errors.HttpError:
            policies = []
        for policy in policies:
            #print(json.dumps(policy, indent=2))
            #print()
            name = policy.get('value', {}).get('policySchema', '')
            print(name)
            values = policy.get('value', {}).get('value', {})
            for setting, value in values.items():
                if isinstance(value, str) and value.find('_ENUM_') != -1:
                    value = value.split('_ENUM_')[-1]
                print(f' {setting}: {value}')
            print()

def build_schemas(cp=None):
    if not cp:
        cp = build()
    parent = _get_customerid()
    schemas = gapi.get_all_pages(cp.customers().policySchemas(), 'list',
            items='policySchemas', parent=parent)
    schema_objects = {}
    for schema in schemas:
        schema_name = schema.get('name', '').split('/')[-1]
        #print(schema)
        #continue
        schema_dict = {
                'name': schema_name,
                'description': schema.get('policyDescription', ''),
                'settings': {},
                }
        for mt in schema.get('definition', {}).get('messageType', {}):
            for setting in mt.get('field', {}):
                setting_name = setting.get('name', '')
                setting_dict = {
                                 'name': setting_name,
                                 'constraints': None,
                                 'descriptions':  [],
                                 'type': setting.get('type'),
                               }
                if setting_dict['type'] == 'TYPE_STRING' and setting.get('label') == 'LABEL_REPEATED':
                    setting_dict['type'] = 'TYPE_LIST'
                if setting_dict['type'] == 'TYPE_ENUM':
                    type_name = setting['typeName']
                    for an_enum in schema['definition']['enumType']:
                        if an_enum['name'] == type_name:
                            setting_dict['enums'] = [enum['name'] for enum in an_enum['value']]
                            setting_dict['enum_prefix'] = utils.commonprefix(setting_dict['enums'])
                            prefix_len = len(setting_dict['enum_prefix'])
                            setting_dict['enums'] = [enum[prefix_len:] for enum in setting_dict['enums'] if not enum.endswith('UNSPECIFIED')]
                            break
                    for fd in schema.get('fieldDescriptions', []):
                        if fd.get('field') == setting_name:
                            setting_dict['descriptions'] = [d['description'] for d in fd.get('knownValueDescriptions', [])]
                            break
                elif setting_dict['type'] == 'TYPE_MESSAGE':
                    print(setting_dict)
                    continue
                else:
                    setting_dict['enums'] = None
                    for fd in schema.get('fieldDescriptions', []):
                        if fd.get('field') == setting_name:
                            if 'knownValueDescriptions' in fd:
                                setting_dict['descriptions'] = fd['knownValueDescriptions']
                            elif 'description' in fd:
                                setting_dict['descriptions'] = [fd['description']]
                schema_dict['settings'][setting_name.lower()] = setting_dict
        schema_objects[schema_name.lower()] = schema_dict
    for obj in schema_objects.values():
        print(json.dumps(obj, indent=2))
    return schema_objects

def print_schemas():
    cp = build()
    schemas = build_schemas(cp)
    for val in schemas.values():
        print(f'{val.get("name")} - {val.get("description")}')
        for v in val['settings'].values():
            vtype = v.get('type')
            print(f'  {v.get("name")}: {vtype}')
            if vtype == 'TYPE_ENUM':
                enums = v.get('enums', [])
                descriptions = v.get('descriptions', [])
                #print('  ', ', '.join(v.get('enums')))
                for i in range(len(v.get('enums', []))):
                    print(f'    {enums[i]} - {descriptions[i]}')
            elif vtype == 'TYPE_BOOL':
                pvs = v.get('descriptions')
                for pv in pvs:
                    if isinstance(pv, dict):
                        pvalue = pv.get('value')
                        pdescription = pv.get('description')
                        print(f'    {pvalue} - {pdescription}')
                    elif isinstance(pv, list):
                        print(f'    {pv[0]}')
            else:
                print(f'    {v.get("descriptions")[0]}')
        print()


def delete_policy():
    cp = build()
    customer = _get_customerid()
    schemas = build_schemas(cp)
    orgunit = None
    i = 3
    body = {'requests': []}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'orgunit':
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg in schemas:
            body['requests'].append({'policySchema': schemas[myarg].name})
            i += 1
        else:
            controlflow.system_error_exit(3, f'{myarg} is not a valid argument to "gam delete chromepolicy"')
    if not orgunit:
        controlflow.system_error_exit(3, 'You must specify an orgunit.')
    for request in body['requests']:
        request['policyTargetKey'] = {'targetResource': orgunit}
    gapi.call(cp.customers().policies().orgunits(), 'batchInherit', customer=customer, body=body)


def update_policy():
    cp = build()
    customer = _get_customerid()
    schemas = build_schemas(cp)
    i = 3
    body = {'requests': []}
    orgunit = None
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'orgunit':
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg in schemas:
            body['requests'].append({'policyValue': {'policySchema': schemas[myarg].name,
                                                     'value': {}},
                                     'updateMask': ''})
            i += 1
            while i < len(sys.argv):
                field = sys.argv[i].lower()
                if field == 'orgunit' or '.' in field:
                    break # field is actually a new policy name or orgunit
                expected_fields = ', '.join(schemas[myarg].settings)
                if field not in expected_fields:
                    controlflow.system_error_exit(4, f'Expected {myarg} field of {expected_fields}. Got {field}.')
                value = sys.argv[i+1]
                vtype = schemas[myarg].settings[field].type
                if vtype in ['TYPE_INT64', 'TYPE_INT32', 'TYPE_UINT64']:
                    if not value.isnumeric():
                        controlflow.system_error_exit(7, f'Value for {myarg} {field} must be a number, got {value}')
                    value = int(value)
                elif vtype in ['TYPE_BOOL']:
                    value = gam.getBoolean(value, field)
                elif vtype in ['TYPE_ENUM']:
                    value = value.upper()
                    enum_values = schemas[myarg].settings[field].enums
                    if value not in enum_values:
                        expected_enums = ', '.join(enum_values)
                        controlflow.system_error_exit(8, f'Expected {myarg} {field} value to be one of {expected_enums}, got {value}')
                    prefix = schemas[myarg].settings[field].enum_prefix
                    value = f'{prefix}{value}'
                elif vtype in ['TYPE_LIST']:
                    value = value.split(',')
                body['requests'][-1]['policyValue']['value'][field] = value
                body['requests'][-1]['updateMask'] += f'{field},'
                i += 2
        else:
            controlflow.system_error_exit(4, f'{myarg} is not a valid argument to "gam update chromepolicy"')
    if not orgunit:
        controlflow.system_error_exit(3, 'You must specify an orgunit')
    for request in body['requests']:
        request['policyTargetKey'] = {'targetResource': orgunit}
    gapi.call(cp.customers().policies().orgunits(), 'batchModify', customer=customer, body=body)
