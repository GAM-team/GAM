"""Methods related to Cloud Identity User Invitation API"""
import sys
from urllib.parse import quote_plus

import googleapiclient

from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi import cloudidentity as gapi_cloudidentity

def _get_customerid():
    ''' returns customer in "customers/(C){customer_id}' format needed for this API'''
    customer = GC_Values[GC_CUSTOMER_ID]
    if customer != MY_CUSTOMER and customer[0] != 'C':
        customer = 'C' + customer
    return f'customers/{customer}'

def _reduce_name(name):
    ''' converts long name into email address'''
    return name.split('/')[-1]

def _generic_action(action):
    '''generic function to call actionable APIs'''
    svc = gapi_cloudidentity.build('cloudidentity_beta')
    customer = _get_customerid()
    email = sys.argv[3].lower()
    encoded_email = quote_plus(email)
    name = f'{customer}/userinvitations/{encoded_email}'
    action_map = {
            'cancel': 'Cancelling',
            'send': 'Sending'
            }
    print_action = action_map[action]
    print(f'{print_action} user invitation...')
    result = gapi.call(svc.customers().userinvitations(), action,
            name=name)
    name = result.get('response', {}).get('name')
    if name:
        result['response']['name'] = _reduce_name(name)
    display.print_json(result)

def _generic_get(get_type):
    '''generic function to call read data APIs'''
    svc = gapi_cloudidentity.build('cloudidentity_beta')
    customer = _get_customerid()
    email = sys.argv[3].lower()
    encoded_email = quote_plus(email)
    name = f'{customer}/userinvitations/{encoded_email}'
    result = gapi.call(svc.customers().userinvitations(), get_type,
            name=name)
    if 'name' in result:
        result['name'] = _reduce_name(result['name'])
    display.print_json(result)


# /batch is broken for Cloud Identity. Once fixed move this to using batch.
# Current serial implementation will be SLOW...
def bulk_is_invitable(emails):
    '''gam <users> check isinvitable'''
    def _invitation_result(request_id, response, _):
        if response.get('isInvitableUser'):
            rows.append({'invitableUsers': request_id})

    svc = gapi_cloudidentity.build('cloudidentity_beta')
    customer = _get_customerid()
    todrive = False
    #batch_size = 1000
    #ebatch = svc.new_batch_http_request(callback=_invitation_result)
    rows = []
    throw_reasons = [gapi_errors.ErrorReason.FOUR_O_THREE]
    for email in emails:
        encoded_email = quote_plus(email)
        name = f'{customer}/userinvitations/{encoded_email}'
        endpoint = svc.customers().userinvitations()
        #if len(ebatch._order) == batch_size:
        #    ebatch.execute()
        #    ebatch = svc.new_batch_http_request(callback=_invitation_result)
        #req = endpoint.isInvitableUser(name=name)
        #ebatch.add(req, request_id=email)
        try:
            result = gapi.call(endpoint,
                               'isInvitableUser',
                               throw_reasons=throw_reasons,
                               name=name)
        except googleapiclient.errors.HttpError:
            continue
        if result.get('isInvitableUser'):
            rows.append({'invitableUsers': email})
    #ebatch.execute()
    titles = ['invitableUsers']
    display.write_csv_file(rows, titles, 'Invitable Users', todrive)


def cancel():
    '''gam cancel userinvitation <email>'''
    _generic_action('cancel')


def get():
    '''gam info userinvitation <email>'''
    _generic_get('get')


def is_invitable_user():
    '''gam check userinvitation <email>'''
    _generic_get('isInvitableUser')


def send():
    '''gam create userinvitation <email>'''
    _generic_action('send')


def print_():
    '''gam print userinvitations'''
    svc = gapi_cloudidentity.build('cloudidentity_beta')
    customer = _get_customerid()
    todrive = False
    titles = []
    rows = []
    filter_ = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'filter':
            filter_ = sys.argv[i+1]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print userinvitations')
    invitations = gapi.get_all_pages(svc.customers().userinvitations(),
                                'list',
                                'userInvitations',
                                parent=customer,
                                filter=filter_)
    for invitation in invitations:
        invitation['name'] = _reduce_name(invitation['name'])
        row = {}
        for key, val in invitation.items():
            if key not in titles:
                titles.append(key)
            row[key] = val
        rows.append(row)
    display.write_csv_file(rows, titles, 'User Invitations', todrive)
