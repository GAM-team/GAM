import gam
from gam import gapi
from gam.gapi import directory as gapi_directory

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
