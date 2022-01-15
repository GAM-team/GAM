import sys

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi import errors as gapi_errors


def _getAllParentOrgUnitsForUser(user, cd=None):
    if not cd:
        cd = gapi_directory.build()
    parent_path = gapi.call(cd.users(),
                            'get',
                            userKey=user,
                            fields='orgUnitPath',
                            projection='basic')['orgUnitPath']
    if parent_path == '/':
        topLevelOrgId = getTopLevelOrgId(cd, '/')
        if topLevelOrgId:
            return {topLevelOrgId: '/'}
        return {'/': '/'}  #Bogus but should never happen
    parent_path = encodeOrgUnitPath(makeOrgUnitPathRelative(parent_path))
    orgUnits = {}
    while True:
        result = gapi.call(cd.orgunits(),
                           'get',
                           customerId=GC_Values[GC_CUSTOMER_ID],
                           orgUnitPath=parent_path,
                           fields='orgUnitId,orgUnitPath,parentOrgUnitId')
        orgUnits[result['orgUnitId']] = result['orgUnitPath']
        if 'parentOrgUnitId' not in result:
            break
        parent_path = result['parentOrgUnitId']
    return orgUnits


def create():
    cd = gapi_directory.build()
    name = getOrgUnitItem(sys.argv[3], pathOnly=True, absolutePath=False)
    parent = ''
    body = {}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'description':
            body['description'] = sys.argv[i + 1].replace('\\n', '\n')
            i += 2
        elif myarg == 'parent':
            parent = getOrgUnitItem(sys.argv[i + 1])
            i += 2
        elif myarg == 'noinherit':
            body['blockInheritance'] = True
            i += 1
        elif myarg == 'inherit':
            body['blockInheritance'] = False
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create org')
    if parent.startswith('id:'):
        parent = gapi.call(cd.orgunits(),
                           'get',
                           customerId=GC_Values[GC_CUSTOMER_ID],
                           orgUnitPath=parent,
                           fields='orgUnitPath')['orgUnitPath']
    if parent == '/':
        orgUnitPath = parent + name
    else:
        orgUnitPath = parent + '/' + name
    if orgUnitPath.count('/') > 1:
        body['parentOrgUnitPath'], body['name'] = orgUnitPath.rsplit('/', 1)
    else:
        body['parentOrgUnitPath'] = '/'
        body['name'] = orgUnitPath[1:]
    parent = body['parentOrgUnitPath']
    gapi.call(cd.orgunits(),
              'insert',
              customerId=GC_Values[GC_CUSTOMER_ID],
              body=body,
              retry_reasons=[gapi_errors.ErrorReason.DAILY_LIMIT_EXCEEDED])
    print(f'Created OrgUnit {body["name"]}')


def delete():
    cd = gapi_directory.build()
    name = getOrgUnitItem(sys.argv[3])
    print(f'Deleting organization {name}')
    gapi.call(cd.orgunits(),
              'delete',
              customerId=GC_Values[GC_CUSTOMER_ID],
              orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(name)))


def info(name=None, return_attrib=None):
    cd = gapi_directory.build()
    checkSuspended = None
    if not name:
        name = getOrgUnitItem(sys.argv[3])
        get_users = True
        show_children = False
        i = 4
        while i < len(sys.argv):
            myarg = sys.argv[i].lower()
            if myarg == 'nousers':
                get_users = False
                i += 1
            elif myarg in ['children', 'child']:
                show_children = True
                i += 1
            elif myarg in ['suspended', 'notsuspended']:
                checkSuspended = myarg == 'suspended'
                i += 1
            else:
                controlflow.invalid_argument_exit(sys.argv[i], 'gam info org')
    if name == '/':
        orgs = gapi.call(cd.orgunits(),
                         'list',
                         customerId=GC_Values[GC_CUSTOMER_ID],
                         type='children',
                         fields='organizationUnits/parentOrgUnitId')
        if 'organizationUnits' in orgs and orgs['organizationUnits']:
            name = orgs['organizationUnits'][0]['parentOrgUnitId']
        else:
            topLevelOrgId = getTopLevelOrgId(cd, '/')
            if topLevelOrgId:
                name = topLevelOrgId
    else:
        name = makeOrgUnitPathRelative(name)
    result = gapi.call(cd.orgunits(),
                       'get',
                       customerId=GC_Values[GC_CUSTOMER_ID],
                       orgUnitPath=encodeOrgUnitPath(name))
    if return_attrib:
        return result[return_attrib]
    display.print_json(result)
    if get_users:
        name = result['orgUnitPath']
        page_message = gapi.got_total_items_first_last_msg('Users')
        users = gapi.get_all_pages(
            cd.users(),
            'list',
            'users',
            page_message=page_message,
            message_attribute='primaryEmail',
            customer=GC_Values[GC_CUSTOMER_ID],
            query=orgUnitPathQuery(name, checkSuspended),
            fields='users(primaryEmail,orgUnitPath),nextPageToken')
        if checkSuspended is None:
            print('Users:')
        elif not checkSuspended:
            print('Users (Not suspended):')
        else:
            print('Users (Suspended):')
        for user in users:
            if show_children or (name.lower() == user['orgUnitPath'].lower()):
                sys.stdout.write(f' {user["primaryEmail"]}')
                if name.lower() != user['orgUnitPath'].lower():
                    print(' (child)')
                else:
                    print('')


def print_():
    print_order = [
        'orgUnitPath', 'orgUnitId', 'name', 'description', 'parentOrgUnitPath',
        'parentOrgUnitId', 'blockInheritance'
    ]
    cd = gapi_directory.build()
    listType = 'all'
    orgUnitPath = '/'
    todrive = False
    fields = ['orgUnitPath', 'name', 'orgUnitId', 'parentOrgUnitId']
    titles = []
    csvRows = []
    parentOrgIds = []
    retrievedOrgIds = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'toplevelonly':
            listType = 'children'
            i += 1
        elif myarg == 'fromparent':
            orgUnitPath = getOrgUnitItem(sys.argv[i + 1])
            i += 2
        elif myarg == 'allfields':
            fields = None
            i += 1
        elif myarg == 'fields':
            fields += sys.argv[i + 1].split(',')
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print orgs')
    gam.printGettingAllItems('Organizational Units', None)
    if fields:
        get_fields = ','.join(fields)
        list_fields = f'organizationUnits({get_fields})'
    else:
        list_fields = None
        get_fields = None
    orgs = gapi.call(cd.orgunits(),
                     'list',
                     customerId=GC_Values[GC_CUSTOMER_ID],
                     type=listType,
                     orgUnitPath=orgUnitPath,
                     fields=list_fields)
    if not 'organizationUnits' in orgs:
        topLevelOrgId = getTopLevelOrgId(cd, orgUnitPath)
        if topLevelOrgId:
            parentOrgIds.append(topLevelOrgId)
        orgunits = []
    else:
        orgunits = orgs['organizationUnits']
    for row in orgunits:
        retrievedOrgIds.append(row['orgUnitId'])
        if row['parentOrgUnitId'] not in parentOrgIds:
            parentOrgIds.append(row['parentOrgUnitId'])
    missing_parents = set(parentOrgIds) - set(retrievedOrgIds)
    for missing_parent in missing_parents:
        try:
            result = gapi.call(cd.orgunits(),
                               'get',
                               throw_reasons=['required'],
                               customerId=GC_Values[GC_CUSTOMER_ID],
                               orgUnitPath=missing_parent,
                               fields=get_fields)
            orgunits.append(result)
        except:
            pass
    for row in orgunits:
        orgEntity = {}
        for key, value in list(row.items()):
            if key in ['kind', 'etag', 'etags']:
                continue
            if key not in titles:
                titles.append(key)
            orgEntity[key] = value
        csvRows.append(orgEntity)
    for title in titles:
        if title not in print_order:
            print_order.append(title)
    titles = sorted(titles, key=print_order.index)
    # sort results similar to how they list in admin console
    csvRows.sort(key=lambda x: x['orgUnitPath'].lower(), reverse=False)
    display.write_csv_file(csvRows, titles, 'Orgs', todrive)


def update():
    cd = gapi_directory.build()
    orgUnitPath = getOrgUnitItem(sys.argv[3])
    if sys.argv[4].lower() in ['move', 'add']:
        entity_type = sys.argv[5].lower()
        if entity_type in usergroup_types:
            users = gam.getUsersToModify(entity_type=entity_type,
                                         entity=sys.argv[6])
        else:
            entity_type = 'users'
            users = gam.getUsersToModify(entity_type=entity_type,
                                         entity=sys.argv[5])
        if (entity_type.startswith('cros')) or (
            (entity_type == 'all') and (sys.argv[6].lower() == 'cros')):
            for l in range(0, len(users), 50):
                move_body = {'deviceIds': users[l:l + 50]}
                print(
                    f' moving {len(move_body["deviceIds"])} devices to {orgUnitPath}'
                )
                gapi.call(cd.chromeosdevices(),
                          'moveDevicesToOu',
                          customerId=GC_Values[GC_CUSTOMER_ID],
                          orgUnitPath=orgUnitPath,
                          body=move_body)
        else:
            i = 0
            count = len(users)
            for user in users:
                i += 1
                sys.stderr.write(
                    f' moving {user} to {orgUnitPath}{gam.currentCountNL(i, count)}'
                )
                try:
                    gapi.call(cd.users(),
                              'update',
                              throw_reasons=[
                                  gapi_errors.ErrorReason.CONDITION_NOT_MET
                              ],
                              userKey=user,
                              body={'orgUnitPath': orgUnitPath})
                except gapi_errors.GapiConditionNotMetError:
                    pass
    else:
        body = {}
        i = 4
        while i < len(sys.argv):
            myarg = sys.argv[i].lower()
            if myarg == 'name':
                body['name'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'description':
                body['description'] = sys.argv[i + 1].replace('\\n', '\n')
                i += 2
            elif myarg == 'parent':
                parent = getOrgUnitItem(sys.argv[i + 1])
                if parent.startswith('id:'):
                    body['parentOrgUnitId'] = parent
                else:
                    body['parentOrgUnitPath'] = parent
                i += 2
            elif myarg == 'noinherit':
                body['blockInheritance'] = True
                i += 1
            elif myarg == 'inherit':
                body['blockInheritance'] = False
                i += 1
            else:
                controlflow.invalid_argument_exit(sys.argv[i], 'gam update org')
        gapi.call(cd.orgunits(),
                  'update',
                  customerId=GC_Values[GC_CUSTOMER_ID],
                  orgUnitPath=encodeOrgUnitPath(
                      makeOrgUnitPathRelative(orgUnitPath)),
                  body=body)


def orgUnitPathQuery(path, checkSuspended):
    query = "orgUnitPath='{}'".format(path.replace(
        "'", "\\'")) if path != '/' else ''
    if checkSuspended is not None:
        query += f' isSuspended={checkSuspended}'
    return query


def makeOrgUnitPathAbsolute(path):
    if path == '/':
        return path
    if path.startswith('/'):
        return path.rstrip('/')
    if path.startswith('id:'):
        return path
    if path.startswith('uid:'):
        return path[1:]
    return '/' + path.rstrip('/')


def makeOrgUnitPathRelative(path):
    if path == '/':
        return path
    if path.startswith('/'):
        return path[1:].rstrip('/')
    if path.startswith('id:'):
        return path
    if path.startswith('uid:'):
        return path[1:]
    return path.rstrip('/')


def encodeOrgUnitPath(path):
    if path.find('+') == -1 and path.find('%') == -1:
        return path
    encpath = ''
    for c in path:
        if c == '+':
            encpath += '%2B'
        elif c == '%':
            encpath += '%25'
        else:
            encpath += c
    return encpath


def getOrgUnitItem(orgUnit, pathOnly=False, absolutePath=True):
    if pathOnly and (orgUnit.startswith('id:') or orgUnit.startswith('uid:')):
        controlflow.system_error_exit(
            2, f'{orgUnit} is not valid in this context')
    if absolutePath:
        return makeOrgUnitPathAbsolute(orgUnit)
    return makeOrgUnitPathRelative(orgUnit)


def getTopLevelOrgId(cd, orgUnitPath):
    try:
        # create a temp org so we can learn what the top level org ID is (sigh)
        temp_org = gapi.call(cd.orgunits(),
                             'insert',
                             customerId=GC_Values[GC_CUSTOMER_ID],
                             body={
                                 'name': 'temp-delete-me',
                                 'parentOrgUnitPath': orgUnitPath
                             },
                             fields='parentOrgUnitId,orgUnitId')
        gapi.call(cd.orgunits(),
                  'delete',
                  customerId=GC_Values[GC_CUSTOMER_ID],
                  orgUnitPath=temp_org['orgUnitId'])
        return temp_org['parentOrgUnitId']
    except:
        pass
    return None


def getOrgUnitId(orgUnit, cd=None):
    if cd is None:
        cd = gapi_directory.build()
    orgUnit = getOrgUnitItem(orgUnit)
    if orgUnit[:3] == 'id:':
        return (orgUnit, orgUnit)
    if orgUnit == '/':
        result = gapi.call(cd.orgunits(),
                           'list',
                           customerId=GC_Values[GC_CUSTOMER_ID],
                           orgUnitPath='/',
                           type='children',
                           fields='organizationUnits(parentOrgUnitId)')
        if result.get('organizationUnits', []):
            return (orgUnit, result['organizationUnits'][0]['parentOrgUnitId'])
        topLevelOrgId = getTopLevelOrgId(cd, '/')
        if topLevelOrgId:
            return (orgUnit, topLevelOrgId)
        return (orgUnit, '/')  #Bogus but should never happen
    result = gapi.call(cd.orgunits(),
                       'get',
                       customerId=GC_Values[GC_CUSTOMER_ID],
                       orgUnitPath=encodeOrgUnitPath(
                           makeOrgUnitPathRelative(orgUnit)),
                       fields='orgUnitId')
    return (orgUnit, result['orgUnitId'])


def orgunit_from_orgunitid(orgunitid, cd=None):
    if cd is None:
        cd = gapi_directory.build()
    orgunitpath = GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME].get(orgunitid)
    if not orgunitpath:
        try:
            orgunitpath = gapi.call(cd.orgunits(),
                                    'get',
                                    customerId=GC_Values[GC_CUSTOMER_ID],
                                    orgUnitPath=f'id:{orgunitid}' if not orgunitid.startswith('id:') else orgunitid,
                                    fields='orgUnitPath')['orgUnitPath']
        except:
            orgunitpath = orgunitid
        GM_Globals[GM_MAP_ORGUNIT_ID_TO_NAME][orgunitid] = orgunitpath
    return orgunitpath
