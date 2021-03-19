"""Chrome Browser Cloud Management API calls"""

import sys

import googleapiclient.errors

import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER
from gam import controlflow
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam import utils


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


def printshow_policies():
    svc = build()
    customer = _get_customerid()
    orgunit = None
    printer_id = None
    app_id = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['ou', 'org', 'orgunit']:
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg == 'printerid':
            printer_id = sys.argv[i+1]
            i += 2
        elif myarg == 'appid':
            app_id = sys.argv[i+1]
            i += 2
        else:
            msg = f'{myarg} is not a valid argument to "gam print chromepolicy"'
            controlflow.system_error_exit(3, msg)
    if not orgunit:
        controlflow.system_error_exit(3, 'You must specify an orgunit')
    body = {
             'policyTargetKey': {
               'targetResource': orgunit,
             }
           }
    if printer_id:
        body['policyTargetKey']['additionalTargetKeys'] = {'printer_id': printer_id}
        namespaces = ['chrome.printers']
    elif app_id:
        body['policyTargetKey']['additionalTargetKeys'] = {'app_id': app_id}
        namespaces = ['chrome.users.apps',
                      'chrome.devices.managedGuest.apps',
                      'chrome.devices.kiosk.apps']
    else:
        namespaces = [
            'chrome.users',
#           Not yet implemented:
#           'chrome.devices',
#           'chrome.devices.managedGuest',
#           'chrome.devices.kiosk',
            ]
    throw_reasons = [gapi_errors.ErrorReason.FOUR_O_O,]
    for namespace in namespaces:
        body['policySchemaFilter'] = f'{namespace}.*'
        try:
            policies = gapi.get_all_pages(svc.customers().policies(), 'resolve',
                                          items='resolvedPolicies',
                                          throw_reasons=throw_reasons,
                                          customer=customer,
                                          body=body)
        except googleapiclient.errors.HttpError:
            policies = []
        for policy in policies:
            name = policy.get('value', {}).get('policySchema', '')
            print(name)
            values = policy.get('value', {}).get('value', {})
            for setting, value in values.items():
                if isinstance(value, str) and value.find('_ENUM_') != -1:
                    value = value.split('_ENUM_')[-1]
                print(f'  {setting}: {value}')
            print()


def build_schemas(svc=None, sfilter=None):
    if not svc:
        svc = build()
    parent = _get_customerid()
    schemas = gapi.get_all_pages(svc.customers().policySchemas(), 'list',
            items='policySchemas', parent=parent, filter=sfilter)
    schema_objects = {}
    for schema in schemas:
        schema_name = schema.get('name', '').split('/')[-1]
        schema_dict = {
                'name': schema_name,
                'description': schema.get('policyDescription', ''),
                'settings': {},
                }
        for mtype in schema.get('definition', {}).get('messageType', {}):
            for setting in mtype.get('field', {}):
                setting_name = setting.get('name', '')
                setting_dict = {
                                 'name': setting_name,
                                 'constraints': None,
                                 'descriptions':  [],
                                 'type': setting.get('type'),
                               }
                if setting_dict['type'] == 'TYPE_STRING' and \
                   setting.get('label') == 'LABEL_REPEATED':
                    setting_dict['type'] = 'TYPE_LIST'
                if setting_dict['type'] == 'TYPE_ENUM':
                    type_name = setting['typeName']
                    for an_enum in schema['definition']['enumType']:
                        if an_enum['name'] == type_name:
                            setting_dict['enums'] = [enum['name'] for enum in an_enum['value']]
                            setting_dict['enum_prefix'] = utils.commonprefix(setting_dict['enums'])
                            prefix_len = len(setting_dict['enum_prefix'])
                            setting_dict['enums'] = [enum[prefix_len:] for enum \
                                                     in setting_dict['enums'] \
                                                     if not enum.endswith('UNSPECIFIED')]
                            break
                    for fdesc in schema.get('fieldDescriptions', []):
                        if fdesc.get('field') == setting_name:
                            setting_dict['descriptions'] = [d['description'] \
                                                            for d in \
                                                            fdesc.get('knownValueDescriptions', \
                                                            [])]
                            break
                elif setting_dict['type'] == 'TYPE_MESSAGE':
                    continue
                else:
                    setting_dict['enums'] = None
                    for fdesc in schema.get('fieldDescriptions', []):
                        if fdesc.get('field') == setting_name:
                            if 'knownValueDescriptions' in fdesc:
                                setting_dict['descriptions'] = fdesc['knownValueDescriptions']
                            elif 'description' in fdesc:
                                setting_dict['descriptions'] = [fdesc['description']]
                schema_dict['settings'][setting_name.lower()] = setting_dict
        schema_objects[schema_name.lower()] = schema_dict
    return schema_objects


def printshow_schemas():
    svc = build()
    sfilter = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'filter':
            sfilter = sys.argv[i+1]
            i += 2
        else:
            msg = f'{myarg} is not a valid argument to "gam print chromeschema"'
            controlflow.system_error_exit(3, msg)
    schemas = build_schemas(svc, sfilter)
    for value in schemas.values():
        print(f'{value.get("name")}: {value.get("description")}')
        for val in value['settings'].values():
            vtype = val.get('type')
            print(f'  {val.get("name")}: {vtype}')
            if vtype == 'TYPE_ENUM':
                enums = val.get('enums', [])
                descriptions = val.get('descriptions', [])
                for i in range(len(val.get('enums', []))):
                    print(f'    {enums[i]}: {descriptions[i]}')
            elif vtype == 'TYPE_BOOL':
                pvs = val.get('descriptions')
                for pvi in pvs:
                    if isinstance(pvi, dict):
                        pvalue = pvi.get('value')
                        pdescription = pvi.get('description')
                        print(f'    {pvalue}: {pdescription}')
                    elif isinstance(pvi, list):
                        print(f'    {pvi[0]}')
            else:
                description = val.get('descriptions')
                if len(description) > 0:
                    print(f'    {description[0]}')
        print()


def delete_policy():
    svc = build()
    customer = _get_customerid()
    schemas = build_schemas(svc)
    orgunit = None
    printer_id = None
    app_id = None
    i = 3
    body = {'requests': []}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['ou', 'org', 'orgunit']:
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg == 'printerid':
            printer_id = sys.argv[i+1]
            i += 2
        elif myarg == 'appid':
            app_id = sys.argv[i+1]
            i += 2
        elif myarg in schemas:
            body['requests'].append({'policySchema': schemas[myarg]['name']})
            i += 1
        else:
            msg = f'{myarg} is not a valid argument to "gam delete chromepolicy"'
            controlflow.system_error_exit(3, msg)
    if not orgunit:
        controlflow.system_error_exit(3, 'You must specify an orgunit')
    for request in body['requests']:
        request['policyTargetKey'] = {'targetResource': orgunit}
        if printer_id:
            request['policyTargetKey']['additionalTargetKeys'] = {'printer_id': printer_id}
        elif app_id:
            request['policyTargetKey']['additionalTargetKeys'] = {'app_id': app_id}
    gapi.call(svc.customers().policies().orgunits(), 'batchInherit', customer=customer, body=body)


def update_policy():
    svc = build()
    customer = _get_customerid()
    schemas = build_schemas(svc)
    orgunit = None
    printer_id = None
    app_id = None
    i = 3
    body = {'requests': []}
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['ou', 'org', 'orgunit']:
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg == 'printerid':
            printer_id = sys.argv[i+1]
            i += 2
        elif myarg == 'appid':
            app_id = sys.argv[i+1]
            i += 2
        elif myarg in schemas:
            body['requests'].append({'policyValue': {'policySchema': schemas[myarg]['name'],
                                                     'value': {}},
                                     'updateMask': ''})
            i += 1
            while i < len(sys.argv):
                field = sys.argv[i].lower()
                if field in ['ou', 'org', 'orgunit', 'printerid', 'appid'] or '.' in field:
                    break # field is actually a new policy, orgunit or app/printer id
                expected_fields = ', '.join(schemas[myarg]['settings'])
                if field not in expected_fields:
                    msg = f'Expected {myarg} field of {expected_fields}. Got {field}.'
                    controlflow.system_error_exit(4, msg)
                cased_field = schemas[myarg]['settings'][field]['name']
                value = sys.argv[i+1]
                vtype = schemas[myarg]['settings'][field]['type']
                if vtype in ['TYPE_INT64', 'TYPE_INT32', 'TYPE_UINT64']:
                    if not value.isnumeric():
                        msg = f'Value for {myarg} {field} must be a number, got {value}'
                        controlflow.system_error_exit(7, msg)
                    value = int(value)
                elif vtype in ['TYPE_BOOL']:
                    value = gam.getBoolean(value, field)
                elif vtype in ['TYPE_ENUM']:
                    value = value.upper()
                    enum_values = schemas[myarg]['settings'][field]['enums']
                    if value not in enum_values:
                        expected_enums = ', '.join(enum_values)
                        msg = f'Expected {myarg} {field} value to be one of ' \
                              f'{expected_enums}, got {value}'
                        controlflow.system_error_exit(8, msg)
                    prefix = schemas[myarg]['settings'][field]['enum_prefix']
                    value = f'{prefix}{value}'
                elif vtype in ['TYPE_LIST']:
                    value = value.split(',')
                body['requests'][-1]['policyValue']['value'][cased_field] = value
                body['requests'][-1]['updateMask'] += f'{cased_field},'
                i += 2
        else:
            msg = f'{myarg} is not a valid argument to "gam update chromepolicy"'
            controlflow.system_error_exit(4, msg)
    if not orgunit:
        controlflow.system_error_exit(3, 'You must specify an orgunit')
    for request in body['requests']:
        request['policyTargetKey'] = {'targetResource': orgunit}
        if printer_id:
            request['policyTargetKey']['additionalTargetKeys'] = {'printer_id': printer_id}
        elif app_id:
            request['policyTargetKey']['additionalTargetKeys'] = {'app_id': app_id}
    gapi.call(svc.customers().policies().orgunits(),
              'batchModify',
              customer=customer,
              body=body)
