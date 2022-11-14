"""Methods related to Cloud Identity Inbound (Google as SP) SAML SSO"""
from datetime import datetime
import sys

import dateutil.parser
import googleapiclient

import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
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
    return gapi_cloudidentity.build('cloudidentity_beta')


'''parse cmd for profile create/update'''
def parse_profile(body, i):
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['displayName'] = sys.argv[i+1]
            i += 2
        elif myarg == 'entityid':
            body.setdefault('idpConfig', {})['entityId'] = sys.argv[i+1]
            i += 2
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
    return body


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
                                  filter=_filter,
                                  )
    matches = []
    for profile in profiles:
        if displayName.lower() == profile.get('displayName', '').lower():
            matches.append(profile)
    if len(matches) == 1:
        return matches[0]['name']
    elif len(matches) == 0:
        controlflow.system_error_exit(3, f'No Inbound SSO profile matching the name {displayName}')
    else:
        err_text = f'Multiple profiles matching {displayName}:\n\n'
        for m in matches:
            err_text += f'  {m["name"]}  {m["displayName"]}\n'
        controlflow.system_error_exit(3, err_text)


'''gam create inboundssoprofile'''
def create_profile():
    ci = build() 
    body = {
          'customer': get_sso_customer(),
          'displayName': 'SSO Profile'
          }
    body = parse_profile(body, 3)
    result = gapi.call(ci.inboundSamlSsoProfiles(), 'create', body=body)
    display.print_json(result)


'''gam print inboundssoprofiles'''
def print_profiles():
    customer = get_sso_customer()
    _filter = f'customer=="{customer}"'
    ci = build() 
    profiles = gapi.get_all_pages(ci.inboundSamlSsoProfiles(),
                                'list',
                                'inboundSamlSsoProfiles',
                                filter=_filter,
                                )
    for profile in profiles:
        display.print_json(profile)
        print()


'''gam update inboundssoprofile'''
def update_profile():
    ci = build() 
    name = profile_displayname_to_name(sys.argv[3], ci)
    body = {}
    body = parse_profile(body, 4)
    updateMask = ','.join(body.keys())
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'patch',
                       name=name,
                       updateMask=updateMask,
                       body=body)
    display.print_json(result)


'''gam info inboundssoprofile'''
def info_profile():
    ci = build()
    name = profile_displayname_to_name(sys.argv[3], ci)
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'get',
                       name=name,
                       )
    display.print_json(result)


'''gam delete inboundssoprofile'''
def delete_profile():
    ci = build()
    name = profile_displayname_to_name(sys.argv[3], ci)
    result = gapi.call(ci.inboundSamlSsoProfiles(),
                       'delete',
                       name=name)
    if result.get('done'):
        print(f' deleted profile {name}.')
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
                                                   ALLOWED_KEY_SIZES,
                                                   key_size)
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg,
                                              'gam create inboundssocredential')
    if not parent:
        controlflow.missing_argument_exit('profile',
                                          'gam create inboundssocredential')
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
                       fields='done,response',
                       body=body)
    if result.get('done'):
       print(f'Created credential {result["response"]["name"]}')
    else:
        controlflow.system_error_exit(3,
                                      'Create did not finish {result}')

def delete_credentials(ci=None, name=None):
    if not ci:
        ci = build()
    if not name:
        name = sys.argv[3] 
    result = gapi.call(ci.inboundSamlSsoProfiles().idpCredentials(),
                       'delete',
                       name=name)
    if result.get('done'):
        print(f' deleted credential {name}')
    else:
        controlflow.system_error_exit(3, 'Delete did not finish {result}')


def print_credentials():
    ci = build()
    i = 3
    profiles = []
    while i > len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['profile', 'profiles']:
            profiles = sys.argv[i+1].split(',')
            for profile in profiles:
                profile = profile_displayname_to_name(profile, ci)
        else:
            controlflow.invalid_argument_exit(myarg, 'gam print inboundssocredentials')
    if not profiles:
        customer = get_sso_customer()
        _filter = f'customer=="{customer}"'
        profiles = gapi.get_all_pages(ci.inboundSamlSsoProfiles(),
                                      'list',
                                      'inboundSamlSsoProfiles',
                                      fields='inboundSamlSsoProfiles/name',
                                      filter=_filter,
                                      )
        profiles = [p['name'] for p in profiles]
    for profile in profiles:
        credentials = gapi.get_all_pages(ci.inboundSamlSsoProfiles().idpCredentials(),
                                         'list',
                                         'idpCredentials',
                                         parent=profile)
        for c in credentials:
            display.print_json(c)
            print()

def parse_assignment(body, i, ci):
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'rank':
            body['rank'] = int(sys.argv[i+1])
            i += 2
        elif myarg == 'mode':
            mode_choices = gapi.get_enum_values_minus_unspecified(
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
        elif myarg in ['ou', 'orgunit']:
            body['targetOrgUnit'] = get_orgunit_id(sys.argv[i+1])
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam create/update inboundssoassignment')
    return body


def create_assignment():
    ci = build()
    body = {
            'customer': get_sso_customer(),
           }
    body = parse_assignment(body, 3, ci)
    result = gapi.call(ci.inboundSsoAssignments(),
                       'create',
                       body=body)
    display.print_json(result)


def update_assignment():
    ci = build()
    name = sys.argv[3]
    body = {}
    body = parse_assignment(body, 4, ci)
    updateMask = ','.join(list(body.keys()))
    result = gapi.call(ci.inboundSsoAssignments(),
                       'patch',
                       name=name,
                       updateMask=updateMask,
                       body=body,
                       )
    display.print_json(result)

def print_assignments():
    ci = build()
    customer = get_sso_customer()
    _filter = f'customer=="{customer}"'
    assignments = gapi.get_all_pages(ci.inboundSsoAssignments(),
                                'list',
                                'inboundSsoAssignments',
                                filter=_filter,
                                )
    cd = gapi_directory.build()
    for assignment in assignments:
        if 'targetGroup' in assignment:
            assignment['groupEmail'] = gapi_cloudidentity_groups.group_id_to_email(ci, assignment['targetGroup']) 
        if 'targetOrgUnit' in assignment:
            ou_id = assignment['targetOrgUnit']
            ou_id = ou_id.split('/')[1]
            ou_id = f'id:{ou_id}'
            assignment['orgUnit'] = gapi_directory_orgunits.orgunit_from_orgunitid(ou_id, cd)
        display.print_json(assignment)
        print()

