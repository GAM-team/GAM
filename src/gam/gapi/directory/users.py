from time import sleep

import gam
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi import errors as gapi_errors


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
