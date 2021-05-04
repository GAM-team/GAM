"""Chrome Browser Cloud Management API calls"""

import re
import sys

import googleapiclient.errors

import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER
from gam import controlflow
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi import chromehistory as gapi_chromehistory
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
    orgunitPath = gapi_directory_orgunits.orgunit_from_orgunitid(orgunit[9:], None)
    header = f'Organizational Unit: {orgunitPath}'
    if printer_id:
        header += f', printerid: {printer_id}'
    elif app_id:
        header += f', appid: {app_id}'
    print(header)
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
        for policy in sorted(policies, key=lambda k: k.get('value', {}).get('policySchema', '')):
            print()
            name = policy.get('value', {}).get('policySchema', '')
            schema = CHROME_SCHEMA_TYPE_MESSAGE.get(name)
            print(name)
            values = policy.get('value', {}).get('value', {})
            for setting, value in values.items():
                # Handle TYPE_MESSAGE fields with durations or counts as a special case
                if schema and setting == schema['casedField']:
                  value = value.get(schema['type'], '')
                  if value:
                      if value.endswith('s'):
                          value = value[:-1]
                      value = int(value) // schema['scale']
                elif isinstance(value, str) and value.find('_ENUM_') != -1:
                    value = value.split('_ENUM_')[-1]
                print(f'  {setting}: {value}')


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
        field_descriptions = schema.get('fieldDescriptions', [])
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
                            setting_dict['descriptions'] = ['']*len(setting_dict['enums'])
                            if field_descriptions:
                                for i, an in enumerate(setting_dict['enums']):
                                    for fdesc in field_descriptions:
                                      if fdesc.get('field') == setting_name:
                                          for d in fdesc.get('knownValueDescriptions', []):
                                              if d['value'][prefix_len:] == an:
                                                  setting_dict['descriptions'][i] = d['description']
                                                  break
                                          break
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
    for _, value in sorted(iter(schemas.items())):
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


CHROME_SCHEMA_TYPE_MESSAGE = {
  'chrome.users.SessionLength':
    {'field': 'sessiondurationlimit', 'casedField': 'sessionDurationLimit',
     'type': 'duration', 'minVal': 1, 'maxVal': 1440, 'scale': 60},
  'chrome.users.BrowserSwitcherDelayDuration':
    {'field': 'browserswitcherdelayduration', 'casedField': 'browserSwitcherDelayDuration',
     'type': 'duration', 'minVal': 0, 'maxVal': 30, 'scale': 1},
  'chrome.users.MaxInvalidationFetchDelay':
    {'field': 'maxinvalidationfetchdelay', 'casedField': 'maxInvalidationFetchDelay',
     'type': 'duration', 'minVal': 1, 'maxVal': 30, 'scale': 1},
  'chrome.users.SecurityTokenSessionSettings':
    {'field': 'securitytokensessionnotificationseconds', 'casedField': 'securityTokenSessionNotificationSeconds',
     'type': 'duration', 'minVal': 0, 'maxVal': 9999, 'scale': 1},
  'chrome.users.PrintingMaxSheetsAllowed':
    {'field': 'printingmaxsheetsallowednullable', 'casedField': 'printingMaxSheetsAllowedNullable',
     'type': 'value', 'minVal': 1, 'maxVal': None, 'scale': 1},
  }


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
            schemaName = schemas[myarg]['name']
            body['requests'].append({'policyValue': {'policySchema': schemaName,
                                                     'value': {}},
                                     'updateMask': ''})
            i += 1
            while i < len(sys.argv):
                field = sys.argv[i].lower()
                if field in ['ou', 'org', 'orgunit', 'printerid', 'appid'] or '.' in field:
                    break # field is actually a new policy, orgunit or app/printer id
                # Handle TYPE_MESSAGE fields with durations or counts as a special case
                schema = CHROME_SCHEMA_TYPE_MESSAGE.get(schemaName)
                if schema and field == schema['field']:
                  casedField = schema['casedField']
                  value = gam.getInteger(sys.argv[i+1], casedField,
                                         minVal=schema['minVal'], maxVal=schema['maxVal'])*schema['scale']
                  if schema['type'] == 'duration':
                    body['requests'][-1]['policyValue']['value'][casedField] = {schema['type']: f'{value}s'}
                  else:
                    body['requests'][-1]['policyValue']['value'][casedField] = {schema['type']: value}
                  body['requests'][-1]['updateMask'] += f'{casedField},'
                  i += 2
                  continue
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
                    prefix = schemas[myarg]['settings'][field]['enum_prefix']
                    enum_values = schemas[myarg]['settings'][field]['enums']
                    if value in enum_values:
                        value = f'{prefix}{value}'
                    elif value.replace(prefix, '') in enum_values:
                        pass
                    else:
                        expected_enums = ', '.join(enum_values)
                        msg = f'Expected {myarg} {field} value to be one of ' \
                              f'{expected_enums}, got {value}'
                        controlflow.system_error_exit(8, msg)
                elif vtype in ['TYPE_LIST']:
                    value = value.split(',')
                if myarg == 'chrome.users.chromebrowserupdates' and \
                      cased_field == 'targetVersionPrefixSetting':
                    mg = re.compile(r'^([a-z]+)-(\d+)$').match(value)
                    if mg:
                        channel = mg.group(1).lower().replace('_', '')
                        minus = mg.group(2)
                        channel_map = gapi_chromehistory.get_channel_map(None)
                        if channel not in channel_map:
                            expected_channels = ', '.join(channel_map)
                            msg = f'Expected {myarg} {cased_field} channel to be one of ' \
                                f'{expected_channels}, got {channel}'
                            controlflow.system_error_exit(8, msg)
                        milestone = gapi_chromehistory.get_relative_milestone(
                            channel_map[channel], int(minus))
                        if not milestone:
                            msg = f'{myarg} {cased_field} channel {channel} offset {minus} does not exist'
                            controlflow.system_error_exit(8, msg)
                        value = f'{milestone}.'
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
