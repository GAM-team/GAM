"""Methods related to Cloud Identity Inbound (Google as SP) SAML SSO"""
from datetime import datetime
import re
import sys

import dateutil.parser
import googleapiclient

import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors
from gam.gapi import cloudidentity as gapi_cloudidentity
from gam.gapi import directory as gapi_directory
from gam.gapi.cloudidentity import groups as gapi_cloudidentity_groups
from gam.gapi.directory import orgunits as gapi_directory_orgunits

'''returns customer in the format inboundsso requires'''
def get_sso_customer():
    customer = GC_Values[GC_CUSTOMER_ID]
    return f'customers/{customer}'


'''returns org unit in the format inboundsso requires'''
def get_orgunit_id(orgunit):
    ou_id = gapi_directory_orgunits.getOrgUnitId(orgunit)[1]
    if ou_id.startswith('id:'):
        ou_id = ou_id[3:]
    return f'orgUnits/{ou_id}'


'''build Cloud Identity API'''
def build():
    return gapi_cloudidentity.build('cloudidentity')


'''parse cmd for profile create/update'''
def parse_profile(body, i):
    name_only = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['displayName'] = sys.argv[i+1]
            i += 2
        elif myarg == 'entityid':
            body.setdefault('idpConfig', {})['entityId'] = sys.argv[i+1]
            i += 2
        elif myarg == 'returnnameonly':
            name_only = True
            i += 1
        elif myarg == 'loginurl':
            body.setdefault('idpConfig', {})['singleSignOnServiceUri'] = sys.argv[i+1]
            i += 2
        elif myarg == 'logouturl':
            body.setdefault('idpConfig', {})['logoutRedirectUri'] = sys.argv[i+1]
            i += 2
        elif myarg == 'changepasswordurl':
            body.setdefault('idpConfig', {})['changePasswordUri'] = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create/update inboundssoprofile')
    return (name_only, body)


'''convert profile nice names to unique ID'''
def profile_displayname_to_name(displayName, ci=None):
    if displayName.lower().startswith('id:') or displayName.lower().startswith('uid:'):
        displayName = displayName.split(':', 1)[1]
        if not displayName.startswith('inboundSamlSsoProfiles/'):
            displayName = f'inboundSamlSsoProfiles/{displayName}'
        return displayName
    if not ci:
        ci = build()
    customer = get_sso_customer()
    _filter = f'customer=="{customer}"'
    profiles = gapi.get_all_pages(ci.inboundSamlSsoProfiles(),
                                  'list',
                                  'inboundSamlSsoProfiles',
                                  filter=_filter)
    matches = []
    for profile in profiles:
        if displayName.lower() == profile.get('displayName', '').lower():
            matches.append(profile)
    if len(matches) == 1:
        return matches[0]['name']
    if len(matches) == 0:
        controlflow.system_error_exit(3, f'No Inbound SSO profile matches the name {displayName}')
    else:
        err_text = f'Multiple profiles match {displayName}:\n\n'
        for m in matches:
            err_text += f'  {m["name"]}  {m["displayName"]}\n'
        controlflow.system_error_exit(3, err_text)


'''get an assignment based on target'''
def assignment_by_target(target, ci=None):
    if not ci:
        ci = build()
    group_pattern = r'^groups/[^/]+$'
    ou_pattern = r'^orgUnits/[^/]+$'
    if re.match(group_pattern, target):
        target_type = 'targetGroup'
    elif re.match(ou_pattern, target):
        target_type = 'targetOrgUnit'
    elif target.lower().startswith('group:'):
        target_type = 'targetGroup'
        group_email = target[6:]
        target = gapi_cloudidentity_groups.group_email_to_id(
                    ci,
                    group_email)
    elif target.lower().startswith('orgunit:'):
        target_type = 'targetOrgUnit'
        ou_name = target[8:]
        target = get_orgunit_id(ou_name)
    else:
        controlflow.system_error_exit(3, 'assignments should be prefixed with ' +
                                         'group:, groups/, orgunit: or orgunits/')
    customer = get_sso_customer()
    _filter = f'customer=="{customer}"'
    assignments = gapi.get_all_pages(ci.inboundSsoAssignments(),
                                     'list',
                                     'inboundSsoAssignments',
                                     filter=_filter)
    for assignment in assignments:
        if target_type in assignment and assignment[target_type] == target:
            return assignment
    controlflow.system_error_exit(3, f'No SSO profile assigned to {target_type} {target}')


'''gam create inboundssoprofile'''
def create_profile():
    ci = build()
    body = {
          'customer': get_sso_customer(),
          'displayName': 'SSO Profile'
          }
    name_only, body = parse_profile(body, 3)
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'create',
                       body=body)
    if result.get('done'):
        if name_only:
            print(result['response']['name'])
        else:
            print(f'Created profile {result["response"]["name"]}')
            display.print_json(result['response'])
    else:
        controlflow.system_error_exit(3, 'Create did not finish {result}')


'''gam print inboundssoprofiles'''
def print_show_profiles(action='print'):
    customer = get_sso_customer()
    _filter = f'customer=="{customer}"'
    ci = build()
    todrive = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, f'gam {action} inboundssoprofiles')

    profiles = gapi.get_all_pages(ci.inboundSamlSsoProfiles(),
                                  'list',
                                  'inboundSamlSsoProfiles',
                                  filter=_filter)
    if action == 'show':
        for profile in profiles:
            display.print_json(profile)
            print()
    elif action == 'print':
        csv_rows = []
        titles = []
        for profile in profiles:
            row = utils.flatten_json(profile)
            for item in row:
                if item not in titles:
                    titles.append(item)
            csv_rows.append(row)
        display.write_csv_file(csv_rows,
                               titles,
                               'Inbound SSO Profiles',
                               todrive)


'''gam update inboundssoprofile'''
def update_profile():
    ci = build()
    name = profile_displayname_to_name(sys.argv[3], ci)
    body = {}
    name_only, body = parse_profile(body, 4)
    updateMask = ','.join(body.keys())
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'patch',
                       name=name,
                       updateMask=updateMask,
                       body=body)
    if name_only:
        print(result['response']['name'])
    else:
        display.print_json(result)


'''gam info inboundssoprofile'''
def info_profile(return_only=False, displayName=None, ci=None):
    if not ci:
        ci = build()
    if not displayName:
        displayName = sys.argv[3]
    name = profile_displayname_to_name(displayName, ci)
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'get',
                       name=name)
    if return_only:
        return result
    display.print_json(result)

'''gam delete inboundssoprofile'''
def delete_profile():
    ci = build()
    name = profile_displayname_to_name(sys.argv[3], ci)
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'delete',
                       name=name)
    if result.get('done'):
        print(f'Deleted profile {name}.')
    else:
        controlflow.system_error_exit(3, 'Delete did not finish: {result}')


'''gam create inboundssocredentials'''
def create_credentials():
    allowed_sizes = [1024, 2048, 4096]
    ci = build()
    parent = None
    generate_key = False
    key_size = 2048
    pemData = None
    replace_oldest = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'profile':
            parent = sys.argv[i+1]
            parent = profile_displayname_to_name(parent, ci)
            i += 2
        elif myarg == 'pemfile':
            pemfile = sys.argv[i+1]
            pemData = fileutils.read_file(pemfile)
            i += 2
        elif myarg == 'generatekey':
            generate_key = True
            i += 1
        elif myarg == 'replaceoldest':
            replace_oldest = True
            i += 1
        elif myarg == 'keysize':
            key_size = int(sys.argv[i+1])
            if key_size not in allowed_sizes:
                controlflow.expected_argument_exit('key_size',
                                                   allowed_sizes,
                                                   key_size)
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create inboundssocredential')
    if not parent:
        controlflow.missing_argument_exit('profile', 'gam create inboundssocredential')
    if replace_oldest:
        fields='nextPageToken,idpCredentials(name,updateTime)'
        current_creds = gapi.get_all_pages(
                ci.inboundSamlSsoProfiles().idpCredentials(),
                'list',
                'idpCredentials',
                parent=parent,
                fields=fields)
        if len(current_creds) == 2:
            oldest_key = min(current_creds,
                             key=lambda x:x['updateTime'])
            print(' deleting older key...')
            delete_credentials(ci=ci,
                               name=oldest_key['name'])
        else:
            print(' profile has {len(current_creds)} credentials. We only replace if there are 2.')
    if generate_key:
        privKey, pemData = gam._generatePrivateKeyAndPublicCert('GAM',
                                                                key_size,
                                                                b64enc_pub=False)
        timestamp = datetime.now().strftime('%Y%m%d-%I%M%S')
        priv_file = f'privatekey-{timestamp}.pem'
        pub_file = f'publiccert-{timestamp}.pem'
        fileutils.write_file(priv_file, privKey)
        print(f' Wrote private key data to {priv_file}')
        fileutils.write_file(pub_file, pemData)
        print(f' Wrote public certificate to {pub_file}')
    if not pemData:
        controlflow.system_error_exit(3, 'You must either specify "pemfile <filename>" or "generate_key"')
    body = {
            'pemData': pemData,
           }
    result = gapi.call(ci.inboundSamlSsoProfiles().idpCredentials(),
                       'add',
                       parent=parent,
                       body=body)
    if result.get('done'):
       print(f'Created credential {result["response"]["name"]}')
       display.print_json(result['response'])
    else:
        controlflow.system_error_exit(3, 'Create did not finish {result}')


'''gam delete inboundssocredential'''
def delete_credentials(ci=None, name=None):
    if not ci:
        ci = build()
    if not name:
        name = sys.argv[3]
    result = gapi.call(ci.inboundSamlSsoProfiles().idpCredentials(),
                       'delete',
                       name=name)
    if result.get('done'):
        print(f'Deleted credential {name}')
    else:
        controlflow.system_error_exit(3, 'Delete did not finish {result}')


'''gam print inboundssocredentials'''
def print_show_credentials(action='print'):
    ci = build()
    todrive = False
    i = 3
    profiles = []
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['profile', 'profiles']:
            profiles = [profile_displayname_to_name(profile, ci)
                            for profile in sys.argv[i+1].split(',')]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg, f'gam {action} inboundssocredentials')
    if not profiles:
        customer = get_sso_customer()
        _filter = f'customer=="{customer}"'
        profiles = gapi.get_all_pages(ci.inboundSamlSsoProfiles(),
                                      'list',
                                      'inboundSamlSsoProfiles',
                                      fields='inboundSamlSsoProfiles/name',
                                      filter=_filter)
        profiles = [p['name'] for p in profiles]
    if action == 'print':
        titles = []
        csv_rows = []
    credentials = []
    for profile in profiles:
        results = gapi.get_all_pages(ci.inboundSamlSsoProfiles().idpCredentials(),
                                     'list',
                                     'idpCredentials',
                                     parent=profile)
        credentials.extend(results)
    if action == 'show':
        for c in credentials:
            display.print_json(c)
            print()
    elif action == 'print':
        for c in credentials:
            csv_row = utils.flatten_json(c)
            for item in csv_row:
                if item not in titles:
                    titles.append(item)
            csv_rows.append(csv_row)
        display.write_csv_file(csv_rows,
                               titles,
                               'Inbound SSO Credentials',
                               todrive)

'''parse command for create/update inboundssoassignment'''
def parse_assignment(body, i, ci):
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'rank':
            body['rank'] = int(sys.argv[i+1])
            i += 2
        elif myarg == 'mode':
            mode_choices = \
                gapi.get_enum_values_minus_unspecified(
                    ci._rootDesc['schemas']['InboundSsoAssignment']['properties']['ssoMode']['enum'])
            body['ssoMode'] = sys.argv[i+1].upper()
            if body['ssoMode'] not in mode_choices:
                controlflow.expected_argument_exit('mode',
                                                   ', '.join(mode_choices),
                                                   sys.argv[i+1])
            i += 2
        elif myarg == 'profile':
            profile_name = profile_displayname_to_name(
                    sys.argv[i+1],
                    ci)
            body['samlSsoInfo'] = {
                    'inboundSamlSsoProfile': profile_name
                    }
            i += 2
        elif myarg == 'neverredirect':
            body['signInBehavior'] = {
                    'redirectCondition': 'NEVER'
                    }
            i += 1
        elif myarg == 'group':
            group = sys.argv[i+1]
            body['targetGroup'] = gapi_cloudidentity_groups.group_email_to_id(
                    ci,
                    group)
            i += 2
        elif myarg in ['ou', 'org', 'orgunit']:
            body['targetOrgUnit'] = get_orgunit_id(sys.argv[i+1])
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create/update inboundssoassignment')
    return body


def update_assignment_target_names(assignment, ci, cd):
    if 'targetGroup' in assignment:
        assignment['targetGroupEmail'] = \
            gapi_cloudidentity_groups.group_id_to_email(ci,
                                                        assignment['targetGroup'])
    elif 'targetOrgUnit' in assignment:
        ou_id = assignment['targetOrgUnit'].split('/')[1]
        assignment['targetOrgUnitPath'] = \
            gapi_directory_orgunits.orgunit_from_orgunitid(f'id:{ou_id}', cd)


'''gam create inboundssoassignment'''
def create_assignment():
    ci = build()
    cd = gapi_directory.build()
    body = {
            'customer': get_sso_customer(),
           }
    body = parse_assignment(body, 3, ci)
    result = gapi.call(ci.inboundSsoAssignments(),
                       'create',
                       body=body)
    if result.get('done'):
       print(f'Created assignment {result["response"]["name"]}')
       update_assignment_target_names(result['response'], ci, cd)
       display.print_json(result['response'])
    else:
        controlflow.system_error_exit(3, 'Create did not finish {result}')


def get_assignment_name(name):
  if name.startswith('id:') or name.startswith('uid:'):
    name = name.split(':', 1)[1]
  if not name.startswith('inboundSsoAssignments/'):
    name = f'inboundSsoAssignments/{name}'
  return name


'''gam update inboundssoassignment'''
def update_assignment():
    ci = build()
    cd = gapi_directory.build()
    name = get_assignment_name(sys.argv[3])
    body = parse_assignment({}, 4, ci)
    updateMask = ','.join(list(body.keys()))
    result = gapi.call(ci.inboundSsoAssignments(),
                       'patch',
                       name=name,
                       updateMask=updateMask,
                       body=body)
    if result.get('done'):
       print(f'Updated assignment {result["response"]["name"]}')
       update_assignment_target_names(result['response'], ci, cd)
       display.print_json(result['response'])
    else:
        controlflow.system_error_exit(3, 'Update did not finish {result}')


'''gam delete inboundssoassignment'''
def delete_assignment():
    ci = build()
    assignment = assignment_by_target(sys.argv[3], ci).get('name')
    print(f'Deleting Inbound SSO Assignmnet {assignment}...')
    gapi.call(ci.inboundSsoAssignments(),
              'delete',
              name=assignment)


'''gam info inboundssoassignment'''
def info_assignment():
    ci = build()
    cd = gapi_directory.build()
    assignment = assignment_by_target(sys.argv[3], ci)
    update_assignment_target_names(assignment, ci, cd)
    profile = assignment.get('samlSsoInfo', {}).get('inboundSamlSsoProfile')
    if profile:
        assignment['samlSsoInfo']['inboundSamlSsoProfile'] = \
            info_profile(return_only=True, displayName=f'id:{profile}', ci=ci)
    display.print_json(assignment)


'''gam print inboundssoassignments'''
def print_show_assignments(action='print'):
    ci = build()
    cd = gapi_directory.build()
    customer = get_sso_customer()
    _filter = f'customer=="{customer}"'
    todrive = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(myarg,
                                              f'gam {action} inboundssoassignments')
    assignments = gapi.get_all_pages(ci.inboundSsoAssignments(),
                                     'list',
                                     'inboundSsoAssignments',
                                     filter=_filter)
    if action == 'show':
        for assignment in assignments:
            update_assignment_target_names(assignment, ci, cd)
            display.print_json(assignment)
            print()
    elif action == 'print':
        titles = []
        csv_rows = []
        for assignment in assignments:
            update_assignment_target_names(assignment, ci, cd)
            csv_row = utils.flatten_json(assignment)
            for item in csv_row:
                if item not in titles:
                    titles.append(item)
            csv_rows.append(csv_row)
        display.write_csv_file(csv_rows,
                               titles,
                               'Inbound SSO Assignments',
                               todrive)
