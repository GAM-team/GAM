"""Contact Delegation API calls"""

import sys

import gam
from gam import controlflow
from gam import display
from gam import gapi


def build():
    return gam.buildGAPIObject('contactdelegation')


def create(users):
    condel = build()
    delegate = gam.normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
    body = {'email': delegate}
    i = 0
    count = len(users)
    for user in users:
        i += 1
        print(
            f'Granting {delegate} contact delegate access to {user}{gam.currentCount(i, count)}'
        )
        gapi.call(condel.delegates(),
                  'create',
                  soft_errors=True,
                  user=user,
                  body=body)


def delete(users):
    condel = build()
    delegate = gam.normalizeEmailAddressOrUID(sys.argv[5], noUid=True)
    i = 0
    count = len(users)
    for user in users:
        i += 1
        print(
            f'Deleting {delegate} contact delegate access to {user}{gam.currentCount(i, count)}'
        )
        gapi.call(condel.delegates(),
                  'delete',
                  soft_errors=True,
                  user=user,
                  delegate=delegate)


def print_(users):
    condel = build()
    titles = ['User', 'delegateAddress']
    csv_rows = []
    todrive = False
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print contactdelegation')
    page_message = gapi.got_total_items_msg('Contact Delegates', '...\n')
    for user in users:
        delegates = gapi.get_all_pages(condel.delegates(), 'list',
                                       'delegates',
                                       page_message=page_message,
                                       user=user)
        for delegate in delegates:
            csv_rows.append({'user': user, 'delegate': delegate.get('email')})
    display.write_csv_file(csv_rows, titles, 'Contact Delegates', todrive)
