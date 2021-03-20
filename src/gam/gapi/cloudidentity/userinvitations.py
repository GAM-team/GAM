"""Methods related to Cloud Identity User Invitation API"""
import sys
from urllib.parse import quote_plus

import googleapiclient

import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER, SORTORDER_CHOICES_MAP
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


USERINVITATION_ORDERBY_CHOICES_MAP = {
    'email': 'email',
    'updatetime': 'update_time',
    }

USERINVITATION_STATE_CHOICES_MAP = {
    'accepted': 'ACCEPTED',
    'declined': 'DECLINED',
    'invited': 'INVITED',
    'notyetsent': 'NOT_YET_SENT',
    }

def print_():
    '''gam print userinvitations'''
    svc = gapi_cloudidentity.build('cloudidentity_beta')
    customer = _get_customerid()
    todrive = False
    titles = ['name', 'state', 'updateTime']
    rows = []
    filter_ = None
    orderByList = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'state':
            state = sys.argv[i + 1].lower().replace('_', '')
            if state in USERINVITATION_STATE_CHOICES_MAP:
                filter_ = f"state=='{USERINVITATION_STATE_CHOICES_MAP[state]}'"
            else:
                controlflow.expected_argument_exit('state',
                                                   ', '.join(USERINVITATION_STATE_CHOICES_MAP),
                                                   state)
            i += 2
        elif myarg == 'orderby':
            fieldName = sys.argv[i + 1].lower()
            i += 2
            if fieldName in USERINVITATION_ORDERBY_CHOICES_MAP:
                fieldName = USERINVITATION_ORDERBY_CHOICES_MAP[fieldName]
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
                    'orderby', ', '.join(sorted(USERINVITATION_ORDERBY_CHOICES_MAP)),
                    fieldName)
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print userinvitations')
    if orderByList:
        orderBy = ' '.join(orderByList)
    else:
        orderBy = None
    gam.printGettingAllItems('User Invitations', filter_)
    page_message = gapi.got_total_items_msg('User Invitations', '...\n')
    invitations = gapi.get_all_pages(svc.customers().userinvitations(),
                                'list',
                                'userInvitations',
                                page_message=page_message,
                                parent=customer,
                                filter=filter_,
                                orderBy=orderBy)
    for invitation in invitations:
        invitation['name'] = _reduce_name(invitation['name'])
        row = {}
        for key, val in invitation.items():
            if key not in titles:
                titles.append(key)
            row[key] = val
        rows.append(row)
    display.write_csv_file(rows, titles, 'User Invitations', todrive)
