import sys

import googleapiclient

import gam
from gam.var import * # pylint: disable=unused-wildcard-import
from gam import controlflow
from gam import display
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors
from gam.gapi import cloudidentity as gapi_cloudidentity
from gam.gapi.directory import customer as gapi_directory_customer

# This allows easy switching between v1 and v1beta1
# v1
CIGROUP_API_BETA = 'cloudidentity'
CIGROUP_MEMBERKEY = 'preferredMemberKey'
# v1beta1
#CIGROUP_API_BETA = 'cloudidentity_beta'
#CIGROUP_MEMBERKEY = 'memberKey'


def create():
    ci = gapi_cloudidentity.build()
    initialGroupConfig = 'EMPTY'
    gapi_directory_customer.setTrueCustomerId()
    parent = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    body = {
        'groupKey': {
            'id': gam.normalizeEmailAddressOrUID(sys.argv[3], noUid=True)
        },
        'parent': parent,
        'labels': {
            'cloudidentity.googleapis.com/groups.discussion_forum': ''
        },
    }
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['displayName'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'description':
            body['description'] = sys.argv[i + 1]
            i += 2
        elif myarg in ['alias', 'aliases']:
            # As of 2020/06/25 this doesn't work (yet?)
            aliases = sys.argv[i + 1].split(' ')
            body['additionalGroupKeys'] = []
            for alias in aliases:
                body['additionalGroupKeys'].append({'id': alias})
            i += 2
        elif myarg in ['dynamic']:
            body['dynamicGroupMetadata'] = {
                'queries': [{
                    'query': sys.argv[i + 1],
                    'resourceType': 'USER'
                }]
            }
            i += 2
        elif myarg in ['makeowner']:
            initialGroupConfig = 'WITH_INITIAL_OWNER'
            i += 1
        else:
            print('should not get here')
            sys.exit(5)
    print(f'Creating group {body["groupKey"]["id"]}')
    gapi.call(ci.groups(),
              'create',
              initialGroupConfig=initialGroupConfig,
              body=body)


def delete():
    ci = gapi_cloudidentity.build()
    group = sys.argv[3]
    name = group_email_to_id(ci, group)
    print(f'Deleting group {group}')
    gapi.call(ci.groups(), 'delete', name=name)


def info():
    ci = gapi_cloudidentity.build(CIGROUP_API_BETA)
    group = gam.normalizeEmailAddressOrUID(sys.argv[3])
    getUsers = True
    getSecuritySettings = True
    showJoinDate = True
    showUpdateDate = False
    showMemberTree = False
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'nousers':
            getUsers = False
            i += 1
        elif myarg == 'nojoindate':
            showJoinDate = False
            i += 1
        elif myarg == 'showupdatedate':
            showUpdateDate = True
            i += 1
        elif myarg == 'membertree':
            showMemberTree = True
            i += 1
        elif myarg in ['nosecurity', 'nosecuritysettings']:
            getSecuritySettings = False
        else:
            controlflow.invalid_argument_exit(myarg, 'gam info cigroup')
    name = group_email_to_id(ci, group)
    basic_info = gapi.call(ci.groups(), 'get', name=name)
    display.print_json(basic_info)
    if getSecuritySettings:
        sec_info = gapi.call(ci.groups(),
                             'getSecuritySettings',
                             name=f'{name}/securitySettings',
                             readMask='*')
        print(' Security settings:')
        display.print_json(sec_info, spacing=' ')
    if getUsers and not showMemberTree:
        if not showJoinDate and not showUpdateDate:
            view = 'BASIC'
            pageSize = 1000
        else:
            view = 'FULL'
            pageSize = 500
        members = gapi.get_all_pages(ci.groups().memberships(),
                                     'list',
                                     'memberships',
                                     parent=name,
                                     fields='*',
                                     pageSize=pageSize,
                                     view=view)
        print(' Members:')
        for member in members:
            role = get_single_role(member.get('roles', [])).lower()
            email = member.get(CIGROUP_MEMBERKEY, {}).get('id')
            member_type = member.get('type', 'USER').lower()
            jc_string = ''
            if showJoinDate:
                joined = member.get('createTime', 'Unknown')
                jc_string += f'  joined {joined}'
            if showUpdateDate:
                updated = member.get('updateTime', 'Unknown')
                jc_string += f'  updated {updated}'
            print(f'  {role}: {email} ({member_type}){jc_string}')
        print(f'Total {len(members)} users in group')
    elif showMemberTree:
        print(' Membership Tree:')
        cached_group_members = {}
        print_member_tree(ci, name, cached_group_members, 2, True)


def print_member_tree(ci, group_id, cached_group_members, spaces, show_role):
    if not group_id in cached_group_members:
        cached_group_members[group_id] = gapi.get_all_pages(ci.groups().memberships(),
                                                            'list',
                                                            'memberships',
                                                            parent=group_id,
                                                            view='FULL',
                                                            fields='*',
                                                            pageSize=1000)
    for member in cached_group_members[group_id]:
        member_id = member.get('name', '')
        member_id = member_id.split('/')[-1]
        email = member.get(CIGROUP_MEMBERKEY, {}).get('id')
        member_type = member.get('type', 'USER').lower()
        if show_role:
            role = get_single_role(member.get('roles', [])).lower()
            print(f'{" " * spaces}{role}: {email} ({member_type})')
        else:
            print(f'{" " * spaces}{email} ({member_type})')
        if member_type == 'group':
            print_member_tree(ci, f'groups/{member_id}', cached_group_members, spaces + 2, False)


def info_member():
    ci = gapi_cloudidentity.build()
    member = gam.normalizeEmailAddressOrUID(sys.argv[3])
    group = gam.normalizeEmailAddressOrUID(sys.argv[4])
    group_name = gapi.call(ci.groups(),
                           'lookup',
                           groupKey_id=group,
                           fields='name').get('name')
    member_name = gapi.call(ci.groups().memberships(),
                            'lookup',
                            parent=group_name,
                            memberKey_id=member,
                            fields='name').get('name')
    member_details = gapi.call(ci.groups().memberships(),
                               'get',
                               name=member_name)
    display.print_json(member_details)


UPDATE_GROUP_SUBCMDS = ['add', 'clear', 'delete', 'remove', 'sync', 'update']
GROUP_ROLES_MAP = {
    'owner': ROLE_OWNER,
    'owners': ROLE_OWNER,
    'manager': ROLE_MANAGER,
    'managers': ROLE_MANAGER,
    'member': ROLE_MEMBER,
    'members': ROLE_MEMBER,
}


def print_():
    ci = gapi_cloudidentity.build(CIGROUP_API_BETA)
    i = 3
    members = False
    membersCountOnly = False
    managers = False
    managersCountOnly = False
    owners = False
    ownersCountOnly = False
    memberRestrictions = False
    gapi_directory_customer.setTrueCustomerId()
    parent = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    usemember = None
    query = None
    memberDelimiter = '\n'
    todrive = False
    titles = []
    csvRows = []
    roles = []
    sortHeaders = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'enterprisemember':
            member, _ = gam.convertUIDtoEmailAddress(sys.argv[i + 1], email_types=['user', 'group'])
            usemember = f"member_key_id == '{member}' && 'cloudidentity.googleapis.com/groups.discussion_forum' in labels"
            i += 2
        elif myarg == 'delimiter':
            memberDelimiter = sys.argv[i + 1]
            i += 2
        elif myarg == 'query':
            query = sys.argv[i + 1]
            i += 2
        elif myarg == 'sortheaders':
            sortHeaders = True
            i += 1
        elif myarg in ['members', 'memberscount']:
            roles.append(ROLE_MEMBER)
            members = True
            if myarg == 'memberscount':
                membersCountOnly = True
            i += 1
        elif myarg in ['owners', 'ownerscount']:
            roles.append(ROLE_OWNER)
            owners = True
            if myarg == 'ownerscount':
                ownersCountOnly = True
            i += 1
        elif myarg in ['managers', 'managerscount']:
            roles.append(ROLE_MANAGER)
            managers = True
            if myarg == 'managerscount':
                managersCountOnly = True
            i += 1
        elif myarg in ['memberrestrictions']:
            memberRestrictions = True
            display.add_titles_to_csv_file(
                    ['memberRestrictionQuery',],
                    titles)
            display.add_titles_to_csv_file(
                    ['memberRestrictionEvaluation',],
                    titles)
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print cigroups')
    if roles:
        if members:
            display.add_titles_to_csv_file([
                'MembersCount',
            ], titles)
            if not membersCountOnly:
                display.add_titles_to_csv_file([
                    'Members',
                ], titles)
        if managers:
            display.add_titles_to_csv_file([
                'ManagersCount',
            ], titles)
            if not managersCountOnly:
                display.add_titles_to_csv_file([
                    'Managers',
                ], titles)
        if owners:
            display.add_titles_to_csv_file([
                'OwnersCount',
            ], titles)
            if not ownersCountOnly:
                display.add_titles_to_csv_file([
                    'Owners',
                ], titles)
    gam.printGettingAllItems('Groups', usemember)
    page_message = gapi.got_total_items_first_last_msg('Groups')
    if usemember:
        try:
            result = gapi.get_all_pages(ci.groups().memberships(),
                                        'searchTransitiveGroups',
                                        'memberships',
                                        throw_reasons=[gapi_errors.ErrorReason.FOUR_O_O],
                                        page_message=page_message,
                                        message_attribute=['groupKey', 'id'],
                                        parent='groups/-', query=usemember,
                                        fields='nextPageToken,memberships(group,groupKey(id),relationType)',
                                        pageSize=1000)
        except googleapiclient.errors.HttpError:
            controlflow.system_error_exit(
                2,
                'enterprisemember requires Enterprise license')
        entityList = []
        for entity in result:
            if entity['relationType'] == 'DIRECT':
                entityList.append(gapi.call(ci.groups(), 'get', name=entity['group']))
    else:
        if query:
            method = 'search'
            kwargs = {'query': query}
        else:
            method = 'list'
            kwargs = {'parent': parent}
        entityList = gapi.get_all_pages(ci.groups(),
                                        method,
                                        'groups',
                                        page_message=page_message,
                                        message_attribute=['groupKey', 'id'],
                                        view='FULL',
                                        pageSize=500,
                                        **kwargs)
    i = 0
    count = len(entityList)
    for groupEntity in entityList:
        i += 1
        groupEmail = groupEntity['groupKey']['id']
        for k, v in iter(groupEntity.pop('labels', {}).items()):
            if v == '':
                groupEntity[f'labels.{k}'] = True
            else:
                groupEntity[f'labels.{k}'] = v
        group = utils.flatten_json(groupEntity)
        for a_key in group:
            if a_key not in titles:
                titles.append(a_key)
        groupKey_id = groupEntity['name']
        if roles:
            sys.stderr.write(
                f' Getting {roles} for {groupEmail}{gam.currentCountNL(i, count)}'
            )
            page_message = gapi.got_total_items_first_last_msg('Members')
            validRoles, _, _ = gam._getRoleVerification(
                ','.join(roles), 'nextPageToken,members(email,id,role)')
            groupMembers = gapi.get_all_pages(ci.groups().memberships(),
                                              'list',
                                              'memberships',
                                              page_message=page_message,
                                              message_attribute=[CIGROUP_MEMBERKEY, 'id'],
                                              soft_errors=True,
                                              parent=groupKey_id,
                                              view='BASIC')
            if members:
                membersList = []
                membersCount = 0
            if managers:
                managersList = []
                managersCount = 0
            if owners:
                ownersList = []
                ownersCount = 0
            for member in groupMembers:
                member_email = member[CIGROUP_MEMBERKEY]['id']
                role = get_single_role(member.get('roles', []))
                if not validRoles or role in validRoles:
                    if role == ROLE_MEMBER:
                        if members:
                            membersCount += 1
                            if not membersCountOnly:
                                membersList.append(member_email)
                    elif role == ROLE_MANAGER:
                        if managers:
                            managersCount += 1
                            if not managersCountOnly:
                                managersList.append(member_email)
                    elif role == ROLE_OWNER:
                        if owners:
                            ownersCount += 1
                            if not ownersCountOnly:
                                ownersList.append(member_email)
                    elif members:
                        membersCount += 1
                        if not membersCountOnly:
                            membersList.append(member_email)
            if members:
                group['MembersCount'] = membersCount
                if not membersCountOnly:
                    group['Members'] = memberDelimiter.join(membersList)
            if managers:
                group['ManagersCount'] = managersCount
                if not managersCountOnly:
                    group['Managers'] = memberDelimiter.join(managersList)
            if owners:
                group['OwnersCount'] = ownersCount
                if not ownersCountOnly:
                    group['Owners'] = memberDelimiter.join(ownersList)
        if memberRestrictions:
           name = f'{groupKey_id}/securitySettings'
           print(f'Getting member restrictions for {groupEmail} ({i}/{count}')
           sec_info = gapi.call(ci.groups(),
                                'getSecuritySettings',
                                name=name,
                                readMask='*')
           if 'memberRestriction' in sec_info:
               group['memberRestrictionQuery'] = sec_info['memberRestriction'].get('query', '')
               group['memberRestrictionEvaluation'] = sec_info['memberRestriction'].get('evaluation', {}).get('state', '')
        csvRows.append(group)
    if sortHeaders:
        display.sort_csv_titles([
            'name', 'groupKey.id'
        ], titles)
    display.write_csv_file(csvRows, titles, 'Groups', todrive)


def _get_groups_list(ci=None, member=None, parent=None):
    if not ci:
        ci = gapi_cloudidentity.build()
    if not parent:
            gapi_directory_customer.setTrueCustomerId()
            parent = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    gam.printGettingAllItems('Groups', member)
    page_message = gapi.got_total_items_first_last_msg('Groups')
    if member:
        fields = 'nextPageToken,memberships(groupKey(id),relationType)'
        try:
            groups_to_get = gapi.get_all_pages(ci.groups().memberships(),
                                               'searchTransitiveGroups',
                                               'memberships',
                                               throw_reasons=[gapi_errors.ErrorReason.FOUR_O_O],
                                               message_attribute=['groupKey', 'id'],
                                               page_message=page_message,
                                               parent='groups/-',
                                               query=member,
                                               pageSize=1000,
                                               fields=fields)
        except googleapiclient.errors.HttpError:
            controlflow.system_error_exit(
                    2,
                    'enterprisemember requires Enterprise license')
        return [group['groupKey']['id'] for group in groups_to_get if group['relationType'] == 'DIRECT']
    else:
        groups_to_get = gapi.get_all_pages(
            ci.groups(),
            'list',
            'groups',
            message_attribute=['groupKey', 'id'],
            page_message=page_message,
            parent=parent,
            view='BASIC',
            pageSize=1000,
            fields='nextPageToken,groups(groupKey(id))')
        return [group['groupKey']['id'] for group in groups_to_get]


def get_membership_graph(member):
    ci = gapi_cloudidentity.build(CIGROUP_API_BETA)
    query = f"member_key_id == '{member}' && 'cloudidentity.googleapis.com/groups.discussion_forum' in labels"
    result = gapi.call(ci.groups().memberships(),
                     'getMembershipGraph',
                     parent='groups/-',
                     query=query)
    return result.get('response')


def print_members():
    ci = gapi_cloudidentity.build(CIGROUP_API_BETA)
    todrive = False
    gapi_directory_customer.setTrueCustomerId()
    parent = f'customers/{GC_Values[GC_CUSTOMER_ID]}'
    usemember = None
    roles = []
    titles = ['group']
    csvRows = []
    groups_to_get = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['role', 'roles']:
            for role in sys.argv[i + 1].lower().replace(',', ' ').split():
                if role in GROUP_ROLES_MAP:
                    roles.append(GROUP_ROLES_MAP[role])
                else:
                    controlflow.system_error_exit(
                        2,
                        f'{role} is not a valid role for "gam print group-members {myarg}"'
                    )
            i += 2
        elif myarg == 'enterprisemember':
            member, _ = gam.convertUIDtoEmailAddress(sys.argv[i + 1], email_types=['user', 'group'])
            usemember = f"member_key_id == '{member}' && 'cloudidentity.googleapis.com/groups.discussion_forum' in labels"
            i += 2
        elif myarg in ['cigroup', 'cigroups']:
            group_email = gam.normalizeEmailAddressOrUID(sys.argv[i + 1])
            groups_to_get = [group_email]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print cigroup-members')
    if not groups_to_get:
        groups_to_get = _get_groups_list(ci, usemember, parent)
    i = 0
    count = len(groups_to_get)
    for group_email in groups_to_get:
        i += 1

        sys.stderr.write(
            f'Getting members for {group_email}{gam.currentCountNL(i, count)}')
        group_id = group_email_to_id(ci, group_email)
        print(f'Getting members of cigroup {group_email}...')
        page_message = f' {gapi.got_total_items_first_last_msg("Members")}'
        group_members = gapi.get_all_pages(
            ci.groups().memberships(),
            'list',
            'memberships',
            soft_errors=True,
            parent=group_id,
            view='FULL',
            pageSize=500,
            page_message=page_message,
            message_attribute=[CIGROUP_MEMBERKEY, 'id'])
        #fields=f'nextPageToken,memberships({CIGROUP_MEMBERKEY},roles,createTime,updateTime)')
        if roles:
            group_members = filter_members_to_roles(group_members, roles)
        for member in group_members:
            # reduce role to a single value
            member['role'] = get_single_role(member.pop('roles'))
            member = utils.flatten_json(member)
            for title in member:
                if title not in titles:
                    titles.append(title)
            member['group'] = group_email
            csvRows.append(member)
    display.write_csv_file(csvRows, titles, 'Group Members', todrive)


def update():

    # Convert foo@googlemail.com to foo@gmail.com; eliminate periods in name for foo.bar@gmail.com
    def _cleanConsumerAddress(emailAddress, mapCleanToOriginal):
        atLoc = emailAddress.find('@')
        if atLoc > 0:
            if emailAddress[atLoc + 1:] in ['gmail.com', 'googlemail.com']:
                cleanEmailAddress = emailAddress[:atLoc].replace(
                    '.', '') + '@gmail.com'
                if cleanEmailAddress != emailAddress:
                    mapCleanToOriginal[cleanEmailAddress] = emailAddress
                    return cleanEmailAddress
        return emailAddress

    def _getRoleAndUsers():
        checkSuspended = None
        role = ROLE_MEMBER
        expireTime = None
        i = 5
        if sys.argv[i].lower() in GROUP_ROLES_MAP:
            role = GROUP_ROLES_MAP[sys.argv[i].lower()]
            i += 1
        if sys.argv[i].lower() in ['suspended', 'notsuspended']:
            checkSuspended = sys.argv[i].lower() == 'suspended'
            i += 1
        if sys.argv[i].lower() in ['expire', 'expires']:
            if role != ROLE_MEMBER:
                controlflow.invalid_argument_exit(
                    sys.argv[i], f'role {role}')
            expireTime = utils.get_time_or_delta_from_now(sys.argv[i+1])
            i += 2
        if sys.argv[i].lower() in usergroup_types:
            users_email = gam.getUsersToModify(entity_type=sys.argv[i].lower(),
                                               entity=sys.argv[i + 1],
                                               checkSuspended=checkSuspended,
                                               groupUserMembersOnly=False)
        else:
            users_email = [
                gam.normalizeEmailAddressOrUID(sys.argv[i],
                                               checkForCustomerId=True)
            ]
        return (role, expireTime, users_email)

    ci = gapi_cloudidentity.build(CIGROUP_API_BETA)
    group = sys.argv[3]
    myarg = sys.argv[4].lower()
    items = []
    if myarg in UPDATE_GROUP_SUBCMDS:
        group = gam.normalizeEmailAddressOrUID(group)
        if group.startswith('groups/'):
            parent = group
        else:
            parent = group_email_to_id(ci, group)
        if not parent:
            return
        if myarg == 'add':
            role, expireTime, users_email = _getRoleAndUsers()
            if len(users_email) > 1:
                sys.stderr.write(
                    f'Group: {group}, Will add {len(users_email)} {role}s.\n')
                for user_email in users_email:
                    item = [
                        'gam', 'update', 'cigroup', f'id:{parent}', 'add', role,
                    ]
                    if expireTime:
                        item.extend(['expires', expireTime])
                    item.append(user_email)
                    items.append(item)
            elif len(users_email) > 0:
                body = {
                    CIGROUP_MEMBERKEY: {
                        'id': users_email[0]
                    },
                    'roles': [{
                        'name': ROLE_MEMBER
                    }]
                }
                if role != ROLE_MEMBER:
                    body['roles'].append({'name': role})
                elif expireTime not in {None, NEVER_TIME}:
                    for role in body['roles']:
                        if role['name'] == ROLE_MEMBER:
                            role['expiryDetail'] = {'expireTime': expireTime}
                add_text = [f'as {role}']
                for i in range(2):
                    try:
                        gapi.call(
                            ci.groups().memberships(),
                            'create',
                            throw_reasons=[
                                gapi_errors.ErrorReason.FOUR_O_NINE,
                                gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                gapi_errors.ErrorReason.RESOURCE_NOT_FOUND,
                                gapi_errors.ErrorReason.INVALID_MEMBER,
                                gapi_errors.ErrorReason.
                                CYCLIC_MEMBERSHIPS_NOT_ALLOWED
                            ],
                            parent=parent,
                            body=body)
                        print(
                            f' Group: {group}, {users_email[0]} Added {" ".join(add_text)}'
                        )
                        break
                    except (gapi_errors.GapiMemberNotFoundError,
                            gapi_errors.GapiResourceNotFoundError,
                            gapi_errors.GapiInvalidMemberError,
                            gapi_errors.GapiCyclicMembershipsNotAllowedError
                           ) as e:
                        print(
                            f' Group: {group}, {users_email[0]} Add {" ".join(add_text)} Failed: {str(e)}'
                        )
                        break
        elif myarg == 'sync':
            syncMembersSet = set()
            syncMembersMap = {}
            role, expireTime, users_email = _getRoleAndUsers()
            for user_email in users_email:
                if user_email in ('*', GC_Values[GC_CUSTOMER_ID]):
                    syncMembersSet.add(GC_Values[GC_CUSTOMER_ID])
                else:
                    syncMembersSet.add(
                        _cleanConsumerAddress(user_email.lower(),
                                              syncMembersMap))
            currentMembersSet = set()
            currentMembersMap = {}
            for current_email in gam.getUsersToModify(
                    entity_type='cigroup',
                    entity=group,
                    member_type=role,
                    groupUserMembersOnly=False):
                if current_email == GC_Values[GC_CUSTOMER_ID]:
                    currentMembersSet.add(current_email)
                else:
                    currentMembersSet.add(
                        _cleanConsumerAddress(current_email.lower(),
                                              currentMembersMap))
            to_add = [
                syncMembersMap.get(emailAddress, emailAddress)
                for emailAddress in syncMembersSet - currentMembersSet
            ]
            to_remove = [
                currentMembersMap.get(emailAddress, emailAddress)
                for emailAddress in currentMembersSet - syncMembersSet
            ]
            sys.stderr.write(
                f'Group: {group}, Will add {len(to_add)} and remove {len(to_remove)} {role}s.\n'
            )
            for user in to_add:
                item = ['gam', 'update', 'cigroup', f'id:{parent}', 'add',
                        role,]
                if role == ROLE_MEMBER and expireTime not in {None, NEVER_TIME}:
                    item.extend(['expires', expireTime])
                item.append(user)
                items.append(item)
            for user in to_remove:
                items.append([
                    'gam', 'update', 'cigroup', f'id:{parent}', 'remove', user
                ])
        elif myarg in ['delete', 'remove']:
            _, _, users_email = _getRoleAndUsers()
            if len(users_email) > 1:
                sys.stderr.write(
                    f'Group: {group}, Will remove {len(users_email)} emails.\n')
                for user_email in users_email:
                    items.append([
                        'gam', 'update', 'cigroup', f'id:{parent}', 'remove',
                        user_email
                    ])
            elif len(users_email) == 1:
                name = membership_email_to_id(ci, parent, users_email[0])
                try:
                    gapi.call(ci.groups().memberships(),
                              'delete',
                              throw_reasons=[
                                  gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                  gapi_errors.ErrorReason.INVALID_MEMBER
                              ],
                              name=name)
                    print(f' Group: {group}, {users_email[0]} Removed')
                except (gapi_errors.GapiMemberNotFoundError,
                        gapi_errors.GapiInvalidMemberError) as e:
                    print(
                        f' Group: {group}, {users_email[0]} Remove Failed: {str(e)}'
                    )
        elif myarg == 'update':
            role, expireTime, users_email = _getRoleAndUsers()
            if len(users_email) > 1:
                sys.stderr.write(
                    f'Group: {group}, Will update {len(users_email)} {role}s.\n'
                )
                for user_email in users_email:
                    item = [
                        'gam', 'update', 'cigroup', f'id:{parent}', 'update',
                        role,]
                    if expireTime:
                        item.extend(['expires', expireTime])
                    item.append(user_email)
                    items.append(item)
            elif len(users_email) > 0:
                name = membership_email_to_id(ci, parent, users_email[0])
                preUpdateRoles = []
                addRoles = []
                removeRoles = []
                postUpdateRoles = []
                member_roles = gapi.call(ci.groups().memberships(),
                                         'get',
                                         name=name,
                                         fields='roles').get('roles', [{'name': ROLE_MEMBER}])
                current_roles = [crole['name'] for crole in member_roles]
                # When upgrading role, strip any expiryDetail from member before role changes
                if role != ROLE_MEMBER:
                    for crole in member_roles:
                        if 'expiryDetail' in crole:
                            preUpdateRoles.append(
                                {'fieldMask': 'expiryDetail.expireTime',
                                 'membershipRole': {'name': ROLE_MEMBER,
                                                    'expiryDetail': {'expireTime': None}}})
                            break
                # When downgrading role or simply updating member expireTime, update expiryDetail after role changes
                elif expireTime:
                    postUpdateRoles.append(
                        {'fieldMask': 'expiryDetail.expireTime',
                         'membershipRole': {'name': role,
                                            'expiryDetail': {'expireTime':  expireTime if expireTime != NEVER_TIME else None}}})
                for crole in current_roles:
                    if crole not in {ROLE_MEMBER, role}:
                        removeRoles.append(crole)
                if role not in current_roles:
                    new_role = {'name': role}
                    if role == ROLE_MEMBER and expireTime not in {None, NEVER_TIME}:
                        new_role['expiryDetail'] = {'expireTime': expireTime}
                        postUpdateRoles = []
                    addRoles.append(new_role)
                bodys = []
                if preUpdateRoles:
                    bodys.append({'updateRolesParams': preUpdateRoles})
                if addRoles:
                    bodys.append({'addRoles': addRoles})
                if removeRoles:
                    bodys.append({'removeRoles': removeRoles})
                if postUpdateRoles:
                    bodys.append({'updateRolesParams': postUpdateRoles})
                for body in bodys:
                    try:
                        gapi.call(ci.groups().memberships(),
                                  'modifyMembershipRoles',
                                  throw_reasons=[
                                      gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                      gapi_errors.ErrorReason.INVALID_MEMBER
                                  ],
                                  name=name,
                                  body=body)
                    except (gapi_errors.GapiMemberNotFoundError,
                            gapi_errors.GapiInvalidMemberError) as e:
                        print(
                            f' Group: {group}, {users_email[0]} Update to {role} Failed: {str(e)}'
                        )
                        break
                print(
                  f' Group: {group}, {users_email[0]} Updated to {role}'
                )

        else:  # clear
            roles = []
            i = 5
            while i < len(sys.argv):
                myarg = sys.argv[i].lower()
                if myarg.upper() in [ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER]:
                    roles.append(myarg.upper())
                    i += 1
                else:
                    controlflow.invalid_argument_exit(
                        sys.argv[i], 'gam update cigroup clear')
            if not roles:
                roles = [ROLE_MEMBER]
            group = gam.normalizeEmailAddressOrUID(group)
            member_type_message = f'{",".join(roles).lower()}s'
            sys.stderr.write(
                f'Getting {member_type_message} of {group} (may take some time for large groups)...\n'
            )
            page_message = gapi.got_total_items_msg(f'{member_type_message}',
                                                    '...')
            try:
                result = gapi.get_all_pages(
                    ci.groups().memberships(),
                    'list',
                    'memberships',
                    page_message=page_message,
                    throw_reasons=gapi_errors.MEMBERS_THROW_REASONS,
                    parent=parent,
                    fields=f'nextPageToken,memberships({CIGROUP_MEMBERKEY},roles)')
                result = filter_members_to_roles(result, roles)
                if not result:
                    print('Group already has 0 members')
                    return
                users_email = [member[CIGROUP_MEMBERKEY]['id'] for member in result]
                sys.stderr.write(
                    f'Group: {group}, Will remove {len(users_email)} {", ".join(roles).lower()}s.\n'
                )
                for user_email in users_email:
                    items.append([
                        'gam', 'update', 'cigroup', group, 'remove', user_email
                    ])
            except (gapi_errors.GapiGroupNotFoundError,
                    gapi_errors.GapiDomainNotFoundError,
                    gapi_errors.GapiInvalidError,
                    gapi_errors.GapiForbiddenError):
                gam.entityUnknownWarning('Group', group, 0, 0)
        if items:
            gam.run_batch(items)
    else:
        i = 4
        body = {}
        sec_body = {}
        while i < len(sys.argv):
            myarg = sys.argv[i].lower().replace('_', '')
            if myarg == 'name':
                body['displayName'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'description':
                body['description'] = sys.argv[i + 1]
                i += 2
            elif myarg == 'security':
                body['labels'] = {
                    'cloudidentity.googleapis.com/groups.security': '',
                    'cloudidentity.googleapis.com/groups.discussion_forum': ''
                }
                i += 1
            elif myarg == 'locked':
                body['labels'] = {
                    'cloudidentity.googleapis.com/groups.locked': '',
                    'cloudidentity.googleapis.com/groups.security': '',
                    'cloudidentity.googleapis.com/groups.discussion_forum': ''
                }
                i += 1
            elif myarg == 'dynamicsecurity':
                body['labels'] = {
                    'cloudidentity.googleapis.com/groups.dynamic': '',
                    'cloudidentity.googleapis.com/groups.security': '',
                    'cloudidentity.googleapis.com/groups.discussion_forum': ''
                }
                i += 1
            elif myarg in ['dynamic']:
                body['dynamicGroupMetadata'] = {
                    'queries': [{
                        'query': sys.argv[i + 1],
                        'resourceType': 'USER'
                    }]
                }
                i += 2
            elif myarg in ['memberrestriction', 'memberrestrictions']:
                query = sys.argv[i + 1]
                member_types = {
                  'USER': '1',
                  'SERVICE_ACCOUNT': '2',
                  'GROUP': '3',
                  }
                for key, val in member_types.items():
                    query = query.replace(key, val)
                sec_body['memberRestriction'] = {'query': query}
                i += 2
            else:
                controlflow.invalid_argument_exit(sys.argv[i],
                                                  'gam update cigroup')
        if body:
            updateMask = ','.join(body.keys())
            name = group_email_to_id(ci, group)
            print(f'Updating group {group}')
            gapi.call(ci.groups(),
                      'patch',
                      updateMask=updateMask,
                      name=name,
                      body=body)
        if sec_body:
            updateMask = 'member_restriction.query'
            # it seems like a bug that API requires /securitySettings
            # appended to name. We'll see if Google servers change this
            # at some point.
            name = f'{group_email_to_id(ci, group)}/securitySettings'
            print(f'Updating group {group} security settings')
            gapi.call(ci.groups(),
                    'updateSecuritySettings',
                    name=name,
                    updateMask=updateMask,
                    body=sec_body)


def group_email_to_id(ci, group, i=0, count=0):
    group = gam.normalizeEmailAddressOrUID(group)
    try:
        return gapi.call(ci.groups(),
                         'lookup',
                         throw_reasons=gapi_errors.GROUP_GET_THROW_REASONS,
                         retry_reasons=gapi_errors.GROUP_GET_RETRY_REASONS,
                         groupKey_id=group,
                         fields='name').get('name')
    except (gapi_errors.GapiGroupNotFoundError,
            gapi_errors.GapiDomainNotFoundError,
            gapi_errors.GapiDomainCannotUseApisError,
            gapi_errors.GapiForbiddenError, gapi_errors.GapiBadRequestError):
        gam.entityUnknownWarning('Group', group, i, count)
        return None


def group_id_to_email(ci, group_id):
    return gapi.call(ci.groups(),
                         'get',
                         fields='groupKey/id',
                         name=group_id).get('groupKey', {}).get('id')

def membership_email_to_id(ci, parent, membership, i=0, count=0):
    membership = gam.normalizeEmailAddressOrUID(membership)
    try:
        return gapi.call(ci.groups().memberships(),
                         'lookup',
                         throw_reasons=gapi_errors.GROUP_GET_THROW_REASONS,
                         retry_reasons=gapi_errors.GROUP_GET_RETRY_REASONS,
                         parent=parent,
                         memberKey_id=membership,
                         fields='name').get('name')
    except (gapi_errors.GapiGroupNotFoundError,
            gapi_errors.GapiDomainNotFoundError,
            gapi_errors.GapiDomainCannotUseApisError,
            gapi_errors.GapiForbiddenError, gapi_errors.GapiBadRequestError):
        gam.entityUnknownWarning('Membership', membership, i, count)
        return None


def get_single_role(roles):
    ''' returns the highest role of member '''
    roles = [role.get('name') for role in roles]
    if not roles:
        return ROLE_MEMBER
    for a_role in [ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER]:
        if a_role in roles:
            return a_role
    return roles[0]


def filter_members_to_roles(members, roles):
    filtered_members = []
    for member in members:
        role = get_single_role(member.get('roles', []))
        if role in roles:
            filtered_members.append(member)
    return filtered_members
