import sys
from time import sleep

import gam
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi import errors as gapi_errors


def delete():
    cd = gapi_directory.build()
    user_email = gam.normalizeEmailAddressOrUID(sys.argv[3])
    print(f'Deleting account for {user_email}')
    try:
        gapi.call(cd.users(),
                  'delete',
                  userKey=user_email,
                  throw_reasons=[gapi_errors.ErrorReason.CONDITION_NOT_MET])
    except gam.gapi.errors.GapiConditionNotMetError as err:
        controlflow.system_error_exit(3,
            f'{err} The user {user_email} may be (or have recently been) on Google Vault Hold and thus not eligible for deletion. You can check holds with "gam user <email> show vaultholds".'
        )


def get_primary(email):
    '''returns primary email of user or empty if email is not a user primary or
    alias address.'''
    cd = gapi_directory.build()
    result = gapi.call(cd.users(), 'get', userKey=email,
            projection='basic', fields='primaryEmail',
            soft_errors=True)
    if not result:
        return ''
    return result.get('primaryEmail', '').lower()


def signout(users):
    cd = gapi_directory.build()
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user = gam.normalizeEmailAddressOrUID(user)
        print(f'Signing Out {user}{gam.currentCount(i, count)}')
        gapi.call(cd.users(),
                  'signOut',
                  soft_errors=True,
                  userKey=user)


def turn_off_2sv(users):
    cd = gapi_directory.build()
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user = gam.normalizeEmailAddressOrUID(user)
        print(f'Turning Off 2-Step Verification for {user}{gam.currentCount(i, count)}')
        gapi.call(cd.twoStepVerification(),
                  'turnOff',
                  soft_errors=True,
                  userKey=user)

def wait_for_mailbox(users):
    '''Wait until users mailbox is provisioned.'''
    cd = gapi_directory.build()
    i = 0
    count = len(users)
    for user in users:
        i += 1
        user = gam.normalizeEmailAddressOrUID(user)
        while True:
            try:
                result = gapi.call(cd.users(),
                                   'get',
                                   'fields=isMailboxSetup',
                                   userKey=user,
                                   throw_reasons=[gapi_errors.ErrorReason.USER_NOT_FOUND])
            except gapi_errors.GapiUserNotFoundError:
                print(f'{user} mailboxIsSetup: False (user does not exist yet)')
                sleep(3)
                continue
            mailbox_is_setup = result.get('isMailboxSetup')
            print(f'{user} mailboxIsSetup: {mailbox_is_setup}')
            if mailbox_is_setup:
                break
            sleep(3)
