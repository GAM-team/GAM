from base64 import b64encode
import datetime
import json
import sys
from time import sleep

import googleapiclient.http

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi import storage as gapi_storage
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam import utils


def buildGAPIObject():
    return gam.buildGAPIObject('vault')


def validateCollaborators(collaboratorList, cd):
    collaborators = []
    for collaborator in collaboratorList.split(','):
        collaborator_id = gam.convertEmailAddressToUID(collaborator, cd)
        if not collaborator_id:
            controlflow.system_error_exit(
                4, f'failed to get a UID for '
                f'{collaborator}. Please make '
                f'sure this is a real user.')
        collaborators.append({'email': collaborator, 'id': collaborator_id})
    return collaborators


def createMatter():
    v = buildGAPIObject()
    matter_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    body = {'name': f'New Matter - {matter_time}'}
    collaborators = []
    cd = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['name'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'description':
            body['description'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['collaborator', 'collaborators']:
            if not cd:
                cd = gam.buildGAPIObject('directory')
            collaborators.extend(validateCollaborators(sys.argv[i + 1], cd))
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create matter')
    matterId = gapi.call(v.matters(), 'create', body=body,
                         fields='matterId')['matterId']
    print(f'Created matter {matterId}')
    for collaborator in collaborators:
        print(f' adding collaborator {collaborator["email"]}')
        body = {
            'matterPermission': {
                'role': 'COLLABORATOR',
                'accountId': collaborator['id']
            }
        }
        gapi.call(v.matters(), 'addPermissions', matterId=matterId, body=body)


VAULT_SEARCH_METHODS_MAP = {
    'account': 'ACCOUNT',
    'accounts': 'ACCOUNT',
    'entireorg': 'ENTIRE_ORG',
    'everyone': 'ENTIRE_ORG',
    'orgunit': 'ORG_UNIT',
    'ou': 'ORG_UNIT',
    'room': 'ROOM',
    'rooms': 'ROOM',
    'shareddrive': 'SHARED_DRIVE',
    'shareddrives': 'SHARED_DRIVE',
    'teamdrive': 'SHARED_DRIVE',
    'teamdrives': 'SHARED_DRIVE',
}
VAULT_SEARCH_METHODS_LIST = [
    'accounts', 'orgunit', 'shareddrives', 'rooms', 'everyone'
]
QUERY_ARGS = ['corpus', 'scope', 'terms', 'start', 'starttime',
              'end', 'endtime', 'timezone', 'excludedrafts',
              'driveversiondate', 'includeshareddrives', 'includeteamdrives',
              'includerooms'] + list(VAULT_SEARCH_METHODS_MAP.keys())

def _build_query(query, myarg, i, query_discovery):
    if not query:
        query = {'dataScope': 'ALL_DATA'}
    if myarg == 'corpus':
        query['corpus'] = sys.argv[i + 1].upper()
        allowed_corpuses = gapi.get_enum_values_minus_unspecified(
                  query_discovery['properties']['corpus']['enum'])
        if query['corpus'] not in allowed_corpuses:
            controlflow.expected_argument_exit('corpus',
                                               ', '.join(allowed_corpuses),
                                               sys.argv[i + 1])
        i += 2
    elif myarg in VAULT_SEARCH_METHODS_MAP:
        if query.get('searchMethod'):
            message = f'Multiple search methods ' \
                      f'({", ".join(VAULT_SEARCH_METHODS_LIST)})' \
                      f'specified, only one is allowed'
            controlflow.system_error_exit(3, message)
        searchMethod = VAULT_SEARCH_METHODS_MAP[myarg]
        query['searchMethod'] = searchMethod
        if searchMethod == 'ACCOUNT':
            query['accountInfo'] = {
                'emails': sys.argv[i + 1].split(',')
            }
            i += 2
        elif searchMethod == 'ORG_UNIT':
            query['orgUnitInfo'] = {
                'orgUnitId': gapi_directory_orgunits.getOrgUnitId(sys.argv[i + 1])[1]
            }
            i += 2
        elif searchMethod == 'SHARED_DRIVE':
            query['sharedDriveInfo'] = {
                'sharedDriveIds': sys.argv[i + 1].split(',')
            }
            i += 2
        elif searchMethod == 'ROOM':
            query['hangoutsChatInfo'] = {
                'roomId': sys.argv[i + 1].split(',')
            }
            i += 2
        else:
            i += 1
    elif myarg == 'scope':
        query['dataScope'] = sys.argv[i + 1].upper()
        allowed_scopes = gapi.get_enum_values_minus_unspecified(
              query_discovery['properties']['dataScope']['enum'])
        if query['dataScope'] not in allowed_scopes:
            controlflow.expected_argument_exit('scope',
                                               ', '.join(allowed_scopes),
                                               sys.argv[i + 1])
        i += 2
    elif myarg in ['terms']:
        query['terms'] = sys.argv[i + 1]
        i += 2
    elif myarg in ['start', 'starttime']:
        query['startTime'] = utils.get_date_zero_time_or_full_time(
            sys.argv[i + 1])
        i += 2
    elif myarg in ['end', 'endtime']:
        query['endTime'] = utils.get_date_zero_time_or_full_time(
            sys.argv[i + 1])
        i += 2
    elif myarg in ['timezone']:
        query['timeZone'] = sys.argv[i + 1]
        i += 2
    elif myarg in ['excludedrafts']:
        query['mailOptions'] = {
           'excludeDrafts': gam.getBoolean(sys.argv[i + 1], myarg)
        }
        i += 2
    elif myarg in ['driveversiondate']:
        query.setdefault('driveOptions', {})['versionDate'] = \
            utils.get_date_zero_time_or_full_time(sys.argv[i+1])
        i += 2
    elif myarg in ['includeshareddrives', 'includeteamdrives']:
        query.setdefault(
            'driveOptions', {})['includeSharedDrives'] = gam.getBoolean(
                sys.argv[i + 1], myarg)
        i += 2
    elif myarg in ['includerooms']:
        query['hangoutsChatOptions'] = {
            'includeRooms': gam.getBoolean(sys.argv[i + 1], myarg)
        }
        i += 2
    return (query, i)

def _validate_query(query, query_discovery):
    if 'corpus' not in query:
        allowed_corpuses = gapi.get_enum_values_minus_unspecified(
            query_discovery['properties']['corpus']['enum'])
        controlflow.system_error_exit(3, 'you must specify a corpus. ' \
          f'Choose one of {", ".join(allowed_corpuses)}')
    if 'searchMethod' not in query:
        controlflow.system_error_exit(3, f'you must specify a search method. ' \
          'Choose one of ' \
          f'{", ".join(VAULT_SEARCH_METHODS_LIST)}')


def createExport():
    v = buildGAPIObject()
    query_discovery = v._rootDesc['schemas']['Query']
    allowed_formats = gapi.get_enum_values_minus_unspecified(
        v._rootDesc['schemas']['MailExportOptions']['properties']
        ['exportFormat']['enum'])
    export_format = 'MBOX'
    showConfidentialModeContent = None  # default to not even set
    matterId = None
    query = None
    useNewExport = None
    body = {'exportOptions': {}}
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'matter':
            matterId = getMatterItem(v, sys.argv[i + 1], state='OPEN')
            body['matterId'] = matterId
            i += 2
        elif myarg == 'name':
            body['name'] = sys.argv[i + 1]
            i += 2
        elif myarg in QUERY_ARGS:
            query, i = _build_query(query, myarg, i, query_discovery)
        elif myarg == 'usenewexport':
            useNewExport = gam.getBoolean(sys.argv[i+1], myarg)
            i += 2
        elif myarg in ['format']:
            export_format = sys.argv[i + 1].upper()
            if export_format not in allowed_formats:
                controlflow.expected_argument_exit('export format',
                                                   ', '.join(allowed_formats),
                                                   export_format)
            i += 2
        elif myarg in ['showconfidentialmodecontent']:
            showConfidentialModeContent = gam.getBoolean(sys.argv[i + 1], myarg)
            i += 2
        elif myarg in ['region']:
            allowed_regions = gapi.get_enum_values_minus_unspecified(
                v._rootDesc['schemas']['ExportOptions']['properties']['region']
                ['enum'])
            body['exportOptions']['region'] = sys.argv[i + 1].upper()
            if body['exportOptions']['region'] not in allowed_regions:
                controlflow.expected_argument_exit(
                    'region', ', '.join(allowed_regions),
                    body['exportOptions']['region'])
            i += 2
        elif myarg in ['includeaccessinfo']:
            body['exportOptions'].setdefault(
                'driveOptions', {})['includeAccessInfo'] = gam.getBoolean(
                    sys.argv[i + 1], myarg)
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create export')
    if not matterId:
        controlflow.system_error_exit(
            3, 'you must specify a matter for the new export.')
    _validate_query(query, query_discovery)
    body['query'] = query
    if 'name' not in body:
        corpus_name = body['query']['corpus']
        corpus_date = datetime.datetime.now()
        body['name'] = f'GAM {corpus_name} export - {corpus_date}'
    options_field = None
    if body['query']['corpus'] == 'MAIL':
        options_field = 'mailOptions'
    elif body['query']['corpus'] == 'GROUPS':
        options_field = 'groupsOptions'
    elif body['query']['corpus'] == 'HANGOUTS_CHAT':
        options_field = 'hangoutsChatOptions'
    if options_field:
        body['exportOptions'].pop('driveOptions', None)
        body['exportOptions'][options_field] = {'exportFormat': export_format}
        if showConfidentialModeContent is not None:
            body['exportOptions'][options_field][
                'showConfidentialModeContent'] = showConfidentialModeContent
        if useNewExport is not None:
            body['exportOptions'][options_field][
                'useNewExport'] = useNewExport
    results = gapi.call(v.matters().exports(),
                        'create',
                        matterId=matterId,
                        body=body)
    print(f'Created export {results["id"]}')
    display.print_json(results)


def deleteExport():
    v = buildGAPIObject()
    matterId = getMatterItem(v, sys.argv[3])
    exportId = convertExportNameToID(v, sys.argv[4], matterId)
    print(f'Deleting export {sys.argv[4]} / {exportId}')
    gapi.call(v.matters().exports(),
              'delete',
              matterId=matterId,
              exportId=exportId)


def getExportInfo():
    v = buildGAPIObject()
    matterId = getMatterItem(v, sys.argv[3])
    exportId = convertExportNameToID(v, sys.argv[4], matterId)
    export = gapi.call(v.matters().exports(),
                       'get',
                       matterId=matterId,
                       exportId=exportId)
    display.print_json(export)


def print_count():
    v = buildGAPIObject()
    query_discovery = v._rootDesc['schemas']['Query']
    matterId = None
    operation_wait = 15
    query = None
    body = {'view': 'ALL'}
    name = None
    todrive = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'matter':
            matterId = getMatterItem(v, sys.argv[i + 1])
            i += 2
        elif myarg == 'operation':
            name = sys.argv[i+1]
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in QUERY_ARGS:
            query, i = _build_query(query, myarg, i, query_discovery)
        elif myarg == 'wait':
            operation_wait = int(sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create export')
    if not matterId:
        controlflow.system_error_exit(
            3, 'you must specify a matter for the count.')
    if name:
        operation = {'name': name}
    else:
        _validate_query(query, query_discovery)
        body['query'] = query
        operation = gapi.call(v.matters(), 'count', matterId=matterId, body=body)
    sys.stderr.write(f'Watching operation {operation["name"]}...\n')
    while not operation.get('done'):
        sys.stderr.write(f' operation {operation["name"]} is not done yet. Checking again in {operation_wait} seconds\n')
        sleep(operation_wait)
        operation = gapi.call(v.operations(), 'get', name=operation['name'])
    response = operation.get('response', {})
    query = operation['metadata']['query']
    search_method = query.get('searchMethod')
    # ARGH count results don't include accounts with zero items.
    # so we keep track of which accounts we searched and can report
    # zero data for them.
    if search_method == 'ACCOUNT':
      query_accounts = query.get('accountInfo', {}).get('emails', [])
    elif search_method == 'ENTIRE_ORG':
      query_accounts = gam.getUsersToModify('all', 'users')
    elif search_method == 'ORG_UNIT':
      org_unit = query['orgUnitInfo']['orgUnitId']
      query_accounts = gam.getUsersToModify('ou', org_unit)
    mailcounts = response.get('mailCountResult', {})
    groupcounts = response.get('groupsCountResult', {})
    csv_rows = []
    for a_count in [mailcounts, groupcounts]:
        for errored_account in a_count.get('accountCountErrors', []):
            account = errored_account.get('account')
            csv_rows.append({'account': account, 'error': errored_account.get('errorType')})
            if account in query_accounts: query_accounts.remove(account)
        for account in a_count.get('nonQueryableAccounts', []):
            csv_rows.append({'account': account, 'error': 'Not queried because not on hold'})
            if account in query_accounts: query_accounts.remove(account)
        for account in a_count.get('accountCounts', []):
            email = account.get('account', {}).get('email', '')
            if email:
                csv_rows.append({'account': email, 'count': account.get('count', 0)})
                if email in query_accounts: query_accounts.remove(email)
    for account in query_accounts:
        csv_rows.append({'account': account, 'count': 0})
    titles = ['account', 'count', 'error']
    display.write_csv_file(csv_rows, titles, 'Vault Counts', todrive)

def createHold():
    v = buildGAPIObject()
    allowed_corpuses = gapi.get_enum_values_minus_unspecified(
        v._rootDesc['schemas']['Hold']['properties']['corpus']['enum'])
    body = {'query': {}}
    i = 3
    query = None
    start_time = None
    end_time = None
    matterId = None
    accounts = []
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['name'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'query':
            query = sys.argv[i + 1]
            i += 2
        elif myarg == 'corpus':
            body['corpus'] = sys.argv[i + 1].upper()
            if body['corpus'] not in allowed_corpuses:
                controlflow.expected_argument_exit('corpus',
                                                   ', '.join(allowed_corpuses),
                                                   sys.argv[i + 1])
            i += 2
        elif myarg in ['accounts', 'users', 'groups']:
            accounts = sys.argv[i + 1].split(',')
            i += 2
        elif myarg in ['orgunit', 'ou']:
            body['orgUnit'] = {
                'orgUnitId': gapi_directory_orgunits.getOrgUnitId(sys.argv[i + 1])[1]
            }
            i += 2
        elif myarg in ['start', 'starttime']:
            start_time = utils.get_date_zero_time_or_full_time(sys.argv[i + 1])
            i += 2
        elif myarg in ['end', 'endtime']:
            end_time = utils.get_date_zero_time_or_full_time(sys.argv[i + 1])
            i += 2
        elif myarg == 'matter':
            matterId = getMatterItem(v, sys.argv[i + 1])
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create hold')
    if not matterId:
        controlflow.system_error_exit(
            3, 'you must specify a matter for the new hold.')
    if not body.get('name'):
        controlflow.system_error_exit(
            3, 'you must specify a name for the new hold.')
    if not body.get('corpus'):
        controlflow.system_error_exit(3, f'you must specify a corpus for ' \
          f'the new hold. Choose one of {", ".join(allowed_corpuses)}')
    if body['corpus'] == 'HANGOUTS_CHAT':
        query_type = 'hangoutsChatQuery'
    else:
        query_type = f'{body["corpus"].lower()}Query'
    body['query'][query_type] = {}
    if body['corpus'] == 'DRIVE':
        if query:
            try:
                body['query'][query_type] = json.loads(query)
            except ValueError as e:
                controlflow.system_error_exit(3, f'{str(e)}, query: {query}')
    elif body['corpus'] in ['GROUPS', 'MAIL']:
        if query:
            body['query'][query_type] = {'terms': query}
        if start_time:
            body['query'][query_type]['startTime'] = start_time
        if end_time:
            body['query'][query_type]['endTime'] = end_time
    if accounts:
        body['accounts'] = []
        cd = gam.buildGAPIObject('directory')
        account_type = 'group' if body['corpus'] == 'GROUPS' else 'user'
        for account in accounts:
            body['accounts'].append({
                'accountId':
                    gam.convertEmailAddressToUID(account, cd, account_type)
            })
    holdId = gapi.call(v.matters().holds(),
                       'create',
                       matterId=matterId,
                       body=body,
                       fields='holdId')
    print(f'Created hold {holdId["holdId"]}')


def deleteHold():
    v = buildGAPIObject()
    hold = sys.argv[3]
    matterId = None
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'matter':
            matterId = getMatterItem(v, sys.argv[i + 1])
            holdId = convertHoldNameToID(v, hold, matterId)
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam delete hold')
    if not matterId:
        controlflow.system_error_exit(
            3, 'you must specify a matter for the hold.')
    print(f'Deleting hold {hold} / {holdId}')
    gapi.call(v.matters().holds(), 'delete', matterId=matterId, holdId=holdId)


def getHoldInfo():
    v = buildGAPIObject()
    hold = sys.argv[3]
    matterId = None
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'matter':
            matterId = getMatterItem(v, sys.argv[i + 1])
            holdId = convertHoldNameToID(v, hold, matterId)
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam info hold')
    if not matterId:
        controlflow.system_error_exit(
            3, 'you must specify a matter for the hold.')
    results = gapi.call(v.matters().holds(),
                        'get',
                        matterId=matterId,
                        holdId=holdId)
    cd = gam.buildGAPIObject('directory')
    if 'accounts' in results:
        account_type = 'group' if results['corpus'] == 'GROUPS' else 'user'
        for i in range(0, len(results['accounts'])):
            uid = f'uid:{results["accounts"][i]["accountId"]}'
            acct_email, _ = gam.convertUIDtoEmailAddress(uid, cd, [account_type])
            results['accounts'][i]['email'] = acct_email
    if 'orgUnit' in results:
        results['orgUnit']['orgUnitPath'] = gapi_directory_orgunits.info(
            results['orgUnit']['orgUnitId'], return_attrib='orgUnitPath')
    display.print_json(results)


def convertExportNameToID(v, nameOrID, matterId):
    cg = UID_PATTERN.match(nameOrID)
    if cg:
        return cg.group(1)
    fields = 'exports(id,name),nextPageToken'
    exports = gapi.get_all_pages(v.matters().exports(),
                                 'list',
                                 'exports',
                                 matterId=matterId,
                                 fields=fields)
    for export in exports:
        if export['name'].lower() == nameOrID.lower():
            return export['id']
    controlflow.system_error_exit(
        4, f'could not find export name {nameOrID} '
        f'in matter {matterId}')


def convertHoldNameToID(v, nameOrID, matterId):
    nameOrID = nameOrID.lower()
    cg = UID_PATTERN.match(nameOrID)
    if cg:
        return cg.group(1)
    fields = 'holds(holdId,name),nextPageToken'
    holds = gapi.get_all_pages(v.matters().holds(),
                               'list',
                               'holds',
                               matterId=matterId,
                               fields=fields)
    for hold in holds:
        if hold['name'].lower() == nameOrID:
            return hold['holdId']
    controlflow.system_error_exit(
        4, f'could not find hold name {nameOrID} '
        f'in matter {matterId}')


def convertMatterNameToID(v, nameOrID, state=None):
    nameOrID = nameOrID.lower()
    cg = UID_PATTERN.match(nameOrID)
    if cg:
        return cg.group(1)
    fields = 'matters(matterId,name),nextPageToken'
    matters = gapi.get_all_pages(v.matters(),
                                 'list',
                                 'matters',
                                 view='BASIC',
                                 state=state,
                                 fields=fields)
    for matter in matters:
        if matter['name'].lower() == nameOrID:
            return matter['matterId']
    return None


def getMatterItem(v, nameOrID, state=None):
    matterId = convertMatterNameToID(v, nameOrID, state=state)
    if not matterId:
        controlflow.system_error_exit(4, f'could not find matter {nameOrID}')
    return matterId


def updateHold():
    v = buildGAPIObject()
    hold = sys.argv[3]
    matterId = None
    body = {}
    query = None
    add_accounts = []
    del_accounts = []
    start_time = None
    end_time = None
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'matter':
            matterId = getMatterItem(v, sys.argv[i + 1])
            holdId = convertHoldNameToID(v, hold, matterId)
            i += 2
        elif myarg == 'query':
            query = sys.argv[i + 1]
            i += 2
        elif myarg in ['orgunit', 'ou']:
            body['orgUnit'] = {
                'orgUnitId': gapi_directory_orgunits.getOrgUnitId(sys.argv[i + 1])[1]
            }
            i += 2
        elif myarg in ['start', 'starttime']:
            start_time = utils.get_date_zero_time_or_full_time(sys.argv[i + 1])
            i += 2
        elif myarg in ['end', 'endtime']:
            end_time = utils.get_date_zero_time_or_full_time(sys.argv[i + 1])
            i += 2
        elif myarg in ['addusers', 'addaccounts', 'addgroups']:
            add_accounts = sys.argv[i + 1].split(',')
            i += 2
        elif myarg in ['removeusers', 'removeaccounts', 'removegroups']:
            del_accounts = sys.argv[i + 1].split(',')
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam update hold')
    if not matterId:
        controlflow.system_error_exit(
            3, 'you must specify a matter for the hold.')
    if query or start_time or end_time or body.get('orgUnit'):
        fields = 'corpus,query,orgUnit'
        old_body = gapi.call(v.matters().holds(),
                             'get',
                             matterId=matterId,
                             holdId=holdId,
                             fields=fields)
        body['query'] = old_body['query']
        body['corpus'] = old_body['corpus']
        if 'orgUnit' in old_body and 'orgUnit' not in body:
            # bah, API requires this to be sent
            # on update even when it's not changing
            body['orgUnit'] = old_body['orgUnit']
        query_type = f'{body["corpus"].lower()}Query'
        if body['corpus'] == 'DRIVE':
            if query:
                try:
                    body['query'][query_type] = json.loads(query)
                except ValueError as e:
                    message = f'{str(e)}, query: {query}'
                    controlflow.system_error_exit(3, message)
        elif body['corpus'] in ['GROUPS', 'MAIL']:
            if query:
                body['query'][query_type]['terms'] = query
            if start_time:
                body['query'][query_type]['startTime'] = start_time
            if end_time:
                body['query'][query_type]['endTime'] = end_time
    if body:
        print(f'Updating hold {hold} / {holdId}')
        gapi.call(v.matters().holds(),
                  'update',
                  matterId=matterId,
                  holdId=holdId,
                  body=body)
    if add_accounts or del_accounts:
        cd = gam.buildGAPIObject('directory')
        for account in add_accounts:
            print(f'adding {account} to hold.')
            add_body = {'accountId': gam.convertEmailAddressToUID(account, cd)}
            gapi.call(v.matters().holds().accounts(),
                      'create',
                      matterId=matterId,
                      holdId=holdId,
                      body=add_body)
        for account in del_accounts:
            print(f'removing {account} from hold.')
            accountId = gam.convertEmailAddressToUID(account, cd)
            gapi.call(v.matters().holds().accounts(),
                      'delete',
                      matterId=matterId,
                      holdId=holdId,
                      accountId=accountId)


def showHoldsForUsers(users):
    cd = gapi_directory.build()
    v = buildGAPIObject()
    matterIds = _getAllMatterIds(v)
    matterHolds = {}
    fields = 'holds(holdId,name,accounts(accountId,email),orgUnit),nextPageToken'
    for matterId in matterIds:
        try:
            matterHolds[matterId] = gapi.get_all_pages(v.matters().holds(),
                                                       'list',
                                                       'holds',
                                                       fields=fields,
                                                       throw_reasons=[gapi_errors.ErrorReason.FOUR_O_O],
                                                       matterId=matterId)
        except googleapiclient.errors.HttpError:
            continue
    totalHolds = 0
    for user in users:
        user = user.lower()
        orgUnits = gapi_directory_orgunits._getAllParentOrgUnitsForUser(user, cd)
        for matterId, holds in matterHolds.items():
            for hold in holds:
                if 'orgUnit' in hold:
                    orgUnitId = hold['orgUnit'].get('orgUnitId')
                    if orgUnitId in orgUnits:
                        print(f'FOUND: OrgUnit {orgUnits[orgUnitId]} for user {user} is on hold in matterId {matterId} and holdId {hold["holdId"]} named "{hold["name"]}"')
                        totalHolds += 1
                else:
                    for account in hold.get('accounts', []):
                        if (user == account.get('email', '').lower()) or (user == account.get('accountId', '')):
                            print(f'FOUND: User account {user} is on hold in matterId {matterId} and holdId {hold["holdId"]} named "{hold["name"]}"')
                            totalHolds += 1
                            break
    sys.stdout.write(f'Total Holds: {totalHolds}\n')


def updateMatter(action=None):
    v = buildGAPIObject()
    matterId = getMatterItem(v, sys.argv[3])
    body = {}
    action_kwargs = {'body': {}}
    add_collaborators = []
    remove_collaborators = []
    cd = None
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'action':
            action = sys.argv[i + 1].lower()
            if action not in VAULT_MATTER_ACTIONS:
                controlflow.system_error_exit(3, f'allowed actions are ' \
                    f'{", ".join(VAULT_MATTER_ACTIONS)}, got {action}')
            i += 2
        elif myarg == 'name':
            body['name'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'description':
            body['description'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['addcollaborator', 'addcollaborators']:
            if not cd:
                cd = gam.buildGAPIObject('directory')
            add_collaborators.extend(validateCollaborators(sys.argv[i + 1], cd))
            i += 2
        elif myarg in ['removecollaborator', 'removecollaborators']:
            if not cd:
                cd = gam.buildGAPIObject('directory')
            remove_collaborators.extend(
                validateCollaborators(sys.argv[i + 1], cd))
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam update matter')
    if action == 'delete':
        action_kwargs = {}
    if body:
        print(f'Updating matter {sys.argv[3]}...')
        if 'name' not in body or 'description' not in body:
            # bah, API requires name/description to be sent
            # on update even when it's not changing
            result = gapi.call(v.matters(),
                               'get',
                               matterId=matterId,
                               view='BASIC')
            body.setdefault('name', result['name'])
            body.setdefault('description', result.get('description'))
        gapi.call(v.matters(), 'update', body=body, matterId=matterId)
    if action:
        print(f'Performing {action} on matter {sys.argv[3]}')
        gapi.call(v.matters(), action, matterId=matterId, **action_kwargs)
    for collaborator in add_collaborators:
        print(f' adding collaborator {collaborator["email"]}')
        body = {
            'matterPermission': {
                'role': 'COLLABORATOR',
                'accountId': collaborator['id']
            }
        }
        gapi.call(v.matters(), 'addPermissions', matterId=matterId, body=body)
    for collaborator in remove_collaborators:
        print(f' removing collaborator {collaborator["email"]}')
        gapi.call(v.matters(),
                  'removePermissions',
                  matterId=matterId,
                  body={'accountId': collaborator['id']})


def getMatterInfo():
    v = buildGAPIObject()
    matterId = getMatterItem(v, sys.argv[3])
    result = gapi.call(v.matters(), 'get', matterId=matterId, view='FULL')
    if 'matterPermissions' in result:
        cd = gam.buildGAPIObject('directory')
        for i in range(0, len(result['matterPermissions'])):
            uid = f'uid:{result["matterPermissions"][i]["accountId"]}'
            user_email, _ = gam.convertUIDtoEmailAddress(uid, cd)
            result['matterPermissions'][i]['email'] = user_email
    display.print_json(result)


def copyExport():
    v = buildGAPIObject()
    s = gapi_storage.build()
    matterId = getMatterItem(v, sys.argv[3])
    exportId = convertExportNameToID(v, sys.argv[4], matterId)
    target_bucket = None
    target_prefix = ''
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'targetbucket':
            target_bucket = sys.argv[i+1]
            i += 2
        elif myarg == 'targetprefix':
            target_prefix = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam copy export')
    if not target_bucket:
        controlflow.missing_argument_exit('target_bucket', 'gam copy export')
    export = gapi.call(v.matters().exports(),
                       'get',
                       matterId=matterId,
                       exportId=exportId)
    objects = []
    for s_file in export['cloudStorageSink']['files']:
        # Convert to md5Hash format Storage API uses
        # because OF COURSE they differ
        md5Hash = b64encode(bytes.fromhex(s_file['md5Hash'])).decode()
        objects.append({'bucket': s_file['bucketName'],
                        'name': s_file['objectName'],
                        'md5Hash': md5Hash})
    gapi_storage.copy_objects(objects,
                              target_bucket,
                              target_prefix)


def downloadExport():
    verifyFiles = True
    extractFiles = True
    v = buildGAPIObject()
    s = gapi_storage.build()
    matterId = getMatterItem(v, sys.argv[3])
    exportId = convertExportNameToID(v, sys.argv[4], matterId)
    targetFolder = GC_Values[GC_DRIVE_DIR]
    i = 5
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'targetfolder':
            targetFolder = os.path.expanduser(sys.argv[i + 1])
            if not os.path.isdir(targetFolder):
                os.makedirs(targetFolder)
            i += 2
        elif myarg == 'noverify':
            verifyFiles = False
            i += 1
        elif myarg == 'noextract':
            extractFiles = False
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam download export')
    export = gapi.call(v.matters().exports(),
                       'get',
                       matterId=matterId,
                       exportId=exportId)
    for s_file in export['cloudStorageSink']['files']:
        bucket = s_file['bucketName']
        s_object = s_file['objectName']
        if verifyFiles:
            expected_hash = s_file['md5Hash']
        else:
            expected_hash = None
        local_file = s_object.replace('/', '-').replace(':', '-')
        filename = os.path.join(targetFolder, local_file)
        gapi_storage.get_cloud_storage_object(s,
                             bucket,
                             s_object,
                             local_file=filename,
                             expectedMd5=expected_hash)
        if extractFiles and re.search(r'\.zip$', filename):
            gam.extract_nested_zip(filename, targetFolder)


def printMatters():
    v = buildGAPIObject()
    todrive = False
    csvRows = []
    initialTitles = ['matterId', 'name', 'description', 'state']
    titles = initialTitles[:]
    view = 'FULL'
    state = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in PROJECTION_CHOICES_MAP:
            view = PROJECTION_CHOICES_MAP[myarg]
            i += 1
        elif myarg == 'matterstate':
            valid_states = gapi.get_enum_values_minus_unspecified(
                v._rootDesc['schemas']['Matter']['properties']['state']['enum'])
            state = sys.argv[i + 1].upper()
            if state not in valid_states:
                controlflow.expected_argument_exit('state',
                                                   ', '.join(valid_states),
                                                   state)
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam print matters')
    gam.printGettingAllItems('Vault Matters', None)
    page_message = gapi.got_total_items_msg('Vault Matters', '...\n')
    matters = gapi.get_all_pages(v.matters(),
                                 'list',
                                 'matters',
                                 page_message=page_message,
                                 view=view,
                                 state=state)
    for matter in matters:
        display.add_row_titles_to_csv_file(utils.flatten_json(matter), csvRows,
                                           titles)
    display.sort_csv_titles(initialTitles, titles)
    display.write_csv_file(csvRows, titles, 'Vault Matters', todrive)


def printExports():
    v = buildGAPIObject()
    todrive = False
    csvRows = []
    initialTitles = ['matterId', 'id', 'name', 'createTime', 'status']
    titles = initialTitles[:]
    matters = []
    matterIds = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['matter', 'matters']:
            matters = sys.argv[i + 1].split(',')
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam print exports')
    if not matters:
        fields = 'matters(matterId),nextPageToken'
        matters_results = gapi.get_all_pages(v.matters(),
                                             'list',
                                             'matters',
                                             view='BASIC',
                                             state='OPEN',
                                             fields=fields)
        for matter in matters_results:
            matterIds.append(matter['matterId'])
    else:
        for matter in matters:
            matterIds.append(getMatterItem(v, matter))
    for matterId in matterIds:
        sys.stderr.write(f'Retrieving exports for matter {matterId}\n')
        exports = gapi.get_all_pages(v.matters().exports(),
                                     'list',
                                     'exports',
                                     matterId=matterId)
        for export in exports:
            display.add_row_titles_to_csv_file(
                utils.flatten_json(export, flattened={'matterId': matterId}),
                csvRows, titles)
    display.sort_csv_titles(initialTitles, titles)
    display.write_csv_file(csvRows, titles, 'Vault Exports', todrive)


def _getAllMatterIds(v=None, state='OPEN'):
    if not v:
        v = buildGAPIObject()
    fields = 'matters(matterId),nextPageToken'
    results = gapi.get_all_pages(v.matters(),
            'list',
            'matters',
            view='BASIC',
            state=state,
            fields=fields)
    return [matter['matterId'] for matter in results]


def printHolds():
    v = buildGAPIObject()
    todrive = False
    csvRows = []
    initialTitles = ['matterId', 'holdId', 'name', 'corpus', 'updateTime']
    titles = initialTitles[:]
    matters = []
    matterIds = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['matter', 'matters']:
            matters = sys.argv[i + 1].split(',')
            i += 2
        else:
            controlflow.invalid_argument_exit(myarg, 'gam print holds')
    if not matters:
        matterIds = _getAllMatterIds(v)
    else:
        for matter in matters:
            matterIds.append(getMatterItem(v, matter))
    i = 0
    matter_count = len(matterIds)
    for matterId in matterIds:
        i += 1
        sys.stderr.write(f'Retrieving holds for matter {matterId} ({i}/{matter_count})\n')
        try:
            holds = gapi.get_all_pages(v.matters().holds(),
                                   'list',
                                   'holds',
                                   throw_reasons=[gapi_errors.ErrorReason.FOUR_O_O],
                                   matterId=matterId)
        except googleapiclient.errors.HttpError:
            continue
        for hold in holds:
            display.add_row_titles_to_csv_file(
                utils.flatten_json(hold, flattened={'matterId': matterId}),
                csvRows, titles)
    display.sort_csv_titles(initialTitles, titles)
    display.write_csv_file(csvRows, titles, 'Vault Holds', todrive)
