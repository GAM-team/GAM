import sys

from gam.var import *
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam import utils


def info(users):
    cd = gapi_directory.build()
    for user in users:
        asps = gapi.get_items(cd.asps(), 'list', 'items', userKey=user)
        if asps:
            print(f'Application-Specific Passwords for {user}')
            for asp in asps:
                if asp['creationTime'] == '0':
                    created_date = 'Unknown'
                else:
                    created_date = utils.formatTimestampYMDHMS(
                        asp['creationTime'])
                if asp['lastTimeUsed'] == '0':
                    used_date = 'Never'
                else:
                    last_used = asp['lastTimeUsed']
                    used_date = utils.formatTimestampYMDHMS(last_used)
                print(f' ID: {asp["codeId"]}\n' \
                      f'  Name: {asp["name"]}\n' \
                      f'  Created: {created_date}\n' \
                      f'  Last Used: {used_date}\n')
        else:
            print(f' no ASPs for {user}\n')


def delete(users, cd=None, codeIdList=None):
    if not cd:
        cd = gapi_directory.build()
    if not codeIdList:
        codeIdList = sys.argv[5].lower()
    if codeIdList == 'all':
        allCodeIds = True
    else:
        allCodeIds = False
        codeIds = codeIdList.replace(',', ' ').split()
    for user in users:
        if allCodeIds:
            print(f'Getting Application Specific Passwords for {user}')
            asps = gapi.get_items(cd.asps(),
                                  'list',
                                  'items',
                                  userKey=user,
                                  fields='items/codeId')
            codeIds = [asp['codeId'] for asp in asps]
        if not codeIds:
            print('No ASPs')
        for codeId in codeIds:
            gapi.call(cd.asps(), 'delete', userKey=user, codeId=codeId)
            print(f'deleted ASP {codeId} for {user}')
