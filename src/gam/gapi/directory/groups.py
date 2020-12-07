import sys

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi import errors as gapi_errors
from gam.gapi.directory import customer as gapi_directory_customer
from gam import utils


def GroupIsAbuseOrPostmaster(emailAddr):
    return emailAddr.startswith('abuse@') or emailAddr.startswith('postmaster@')


def mapGroupEmailForSettings(emailAddr):
  return emailAddr.replace('/', '%2F')


def create():
    cd = gapi_directory.build()
    body = {'email': gam.normalizeEmailAddressOrUID(sys.argv[3], noUid=True)}
    gs_get_before_update = got_name = False
    i = 4
    gs_body = {}
    gs = None
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'name':
            body['name'] = sys.argv[i + 1]
            got_name = True
            i += 2
        elif myarg == 'description':
            description = sys.argv[i + 1].replace('\\n', '\n')
            # The Directory API Groups insert method can not handle any of
            # these characters ('\n<>=') in the description field. If any of
            # these characters are present, use the Group Settings API to set
            # the description.
            for c in '\n<>=':
                if description.find(c) != -1:
                    gs_body['description'] = description
                    if not gs:
                        gs = gam.buildGAPIObject('groupssettings')
                        gs_object = gs._rootDesc
                    break
            else:
                body['description'] = description
            i += 2
        elif myarg == 'getbeforeupdate':
            gs_get_before_update = True
            i += 1
        else:
            if not gs:
                gs = gam.buildGAPIObject('groupssettings')
                gs_object = gs._rootDesc
            getGroupAttrValue(myarg, sys.argv[i + 1], gs_object, gs_body,
                              'create')
            i += 2
    if not got_name:
        body['name'] = body['email']
    print(f'Creating group {body["email"]}')
    gapi.call(cd.groups(), 'insert', body=body, fields='email')
    if gs and not GroupIsAbuseOrPostmaster(body['email']):
        if gs_get_before_update:
            current_settings = gapi.call(
                gs.groups(),
                'get',
                retry_reasons=[
                    gapi_errors.ErrorReason.SERVICE_LIMIT,
                    gapi_errors.ErrorReason.NOT_FOUND
                ],
                groupUniqueId=mapGroupEmailForSettings(body['email']),
                fields='*')
            if current_settings is not None:
                gs_body = dict(
                    list(current_settings.items()) + list(gs_body.items()))
        if gs_body:
            gapi.call(gs.groups(),
                      'update',
                      groupUniqueId=mapGroupEmailForSettings(body['email']),
                      retry_reasons=[
                          gapi_errors.ErrorReason.SERVICE_LIMIT,
                          gapi_errors.ErrorReason.NOT_FOUND
                      ],
                      body=gs_body)


def delete():
    cd = gapi_directory.build()
    group = gam.normalizeEmailAddressOrUID(sys.argv[3])
    print(f'Deleting group {group}')
    gapi.call(cd.groups(), 'delete', groupKey=group)


def deleteUserFromGroups(users):
    cd = gapi_directory.build()
    for user in users:
        user_groups = gapi.get_all_pages(cd.groups(),
                                         'list',
                                         'groups',
                                         userKey=user,
                                         fields='groups(id,email)')
        jcount = len(user_groups)
        print(f'{user} is in {jcount} groups')
        j = 0
        for user_group in user_groups:
            j += 1
            group_email = user_group['email']
            current_count = gam.currentCount(j, jcount)
            print(f' removing {user} from {group_email} {current_count}')
            gapi.call(cd.members(),
                      'delete',
                      soft_errors=True,
                      groupKey=user_group['id'],
                      memberKey=user)
        print('')


def exists(cd, group, i=0, count=0):
    group = gam.normalizeEmailAddressOrUID(group)
    try:
        return gapi.call(cd.groups(),
                         'get',
                         throw_reasons=gapi_errors.GROUP_GET_THROW_REASONS,
                         retry_reasons=gapi_errors.GROUP_GET_RETRY_REASONS,
                         groupKey=group,
                         fields='email')['email']
    except (gapi_errors.GapiGroupNotFoundError,
            gapi_errors.GapiDomainNotFoundError,
            gapi_errors.GapiDomainCannotUseApisError,
            gapi_errors.GapiForbiddenError, gapi_errors.GapiBadRequestError):
        gam.entityUnknownWarning('Group', group, i, count)
        return None


def info(group_name=None):
    cd = gapi_directory.build()
    gs = gam.buildGAPIObject('groupssettings')
    getAliases = getUsers = True
    getGroups = False
    if group_name is None:
        group_name = gam.normalizeEmailAddressOrUID(sys.argv[3])
        i = 4
    else:
        i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'nousers':
            getUsers = False
            i += 1
        elif myarg == 'noaliases':
            getAliases = False
            i += 1
        elif myarg == 'groups':
            getGroups = True
            i += 1
        elif myarg in [
                'nogroups', 'nolicenses', 'nolicences', 'noschemas', 'schemas',
                'userview'
        ]:
            i += 1
            if myarg == 'schemas':
                i += 1
        else:
            controlflow.invalid_argument_exit(myarg, 'gam info group')
    basic_info = gapi.call(cd.groups(), 'get', groupKey=group_name)
    settings = {}
    if not GroupIsAbuseOrPostmaster(basic_info['email']):
        try:
            settings = gapi.call(
                gs.groups(),
                'get',
                throw_reasons=[gapi_errors.ErrorReason.AUTH_ERROR],
                retry_reasons=[gapi_errors.ErrorReason.SERVICE_LIMIT],
                groupUniqueId=mapGroupEmailForSettings(basic_info['email'])
            )  # Use email address retrieved from cd since GS API doesn't support uid
            if settings is None:
                settings = {}
        except gapi_errors.GapiAuthErrorError:
            pass
    print('')
    print('Group Settings:')
    for key, value in list(basic_info.items()):
        if (key in ['kind', 'etag']) or ((key == 'aliases') and
                                         (not getAliases)):
            continue
        if isinstance(value, list):
            print(f' {key}:')
            for val in value:
                print(f'  {val}')
        else:
            print(f' {key}: {value}')
    for key, value in list(settings.items()):
        if key in ['kind', 'etag', 'description', 'email', 'name']:
            continue
        print(f' {key}: {value}')
    if getGroups:
        groups = gapi.get_all_pages(cd.groups(),
                                    'list',
                                    'groups',
                                    userKey=basic_info['email'],
                                    fields='nextPageToken,groups(name,email)')
        if groups:
            print(f'Groups: ({len(groups)})')
            for groupm in groups:
                print(f'  {groupm["name"]}: {groupm["email"]}')
    if getUsers:
        members = gapi.get_all_pages(
            cd.members(),
            'list',
            'members',
            groupKey=group_name,
            fields='nextPageToken,members(email,id,role,type)')
        print('Members:')
        for member in members:
            print(
                f' {member.get("role", ROLE_MEMBER).lower()}: {member.get("email", member["id"])} ({member["type"].lower()})'
            )
        print(f'Total {len(members)} users in group')


def info_member():
    cd = gapi_directory.build()
    memberKey = gam.normalizeEmailAddressOrUID(sys.argv[3])
    groupKey = gam.normalizeEmailAddressOrUID(sys.argv[4])
    member_info = gapi.call(cd.members(),
                            'get',
                            memberKey=memberKey,
                            groupKey=groupKey)
    display.print_json(member_info)


GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP = {
    'admincreated': ['adminCreated', 'Admin_Created'],
    'aliases': [
        'aliases', 'Aliases', 'nonEditableAliases', 'NonEditableAliases'
    ],
    'description': ['description', 'Description'],
    'directmemberscount': ['directMembersCount', 'DirectMembersCount'],
    'email': ['email', 'Email'],
    'id': ['id', 'ID'],
    'name': ['name', 'Name'],
}

GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP = {
    'allowexternalmembers':
        'allowExternalMembers',
    'allowgooglecommunication':
        'allowGoogleCommunication',
    'allowwebposting':
        'allowWebPosting',
    'archiveonly':
        'archiveOnly',
    'customfootertext':
        'customFooterText',
    'customreplyto':
        'customReplyTo',
    'defaultmessagedenynotificationtext':
        'defaultMessageDenyNotificationText',
    'enablecollaborativeinbox':
        'enableCollaborativeInbox',
    'favoriterepliesontop':
        'favoriteRepliesOnTop',
    'gal':
        'includeInGlobalAddressList',
    'includecustomfooter':
        'includeCustomFooter',
    'includeinglobaladdresslist':
        'includeInGlobalAddressList',
    'isarchived':
        'isArchived',
    'memberscanpostasthegroup':
        'membersCanPostAsTheGroup',
    'messagemoderationlevel':
        'messageModerationLevel',
    'primarylanguage':
        'primaryLanguage',
    'replyto':
        'replyTo',
    'sendmessagedenynotification':
        'sendMessageDenyNotification',
    'showingroupdirectory':
        'showInGroupDirectory',
    'spammoderationlevel':
        'spamModerationLevel',
    'whocanadd':
        'whoCanAdd',
    'whocanapprovemembers':
        'whoCanApproveMembers',
    'whocanapprovemessages':
        'whoCanApproveMessages',
    'whocanassigntopics':
        'whoCanAssignTopics',
    'whocanassistcontent':
        'whoCanAssistContent',
    'whocanbanusers':
        'whoCanBanUsers',
    'whocancontactowner':
        'whoCanContactOwner',
    'whocandeleteanypost':
        'whoCanDeleteAnyPost',
    'whocandeletetopics':
        'whoCanDeleteTopics',
    'whocandiscovergroup':
        'whoCanDiscoverGroup',
    'whocanenterfreeformtags':
        'whoCanEnterFreeFormTags',
    'whocanhideabuse':
        'whoCanHideAbuse',
    'whocaninvite':
        'whoCanInvite',
    'whocanjoin':
        'whoCanJoin',
    'whocanleavegroup':
        'whoCanLeaveGroup',
    'whocanlocktopics':
        'whoCanLockTopics',
    'whocanmaketopicssticky':
        'whoCanMakeTopicsSticky',
    'whocanmarkduplicate':
        'whoCanMarkDuplicate',
    'whocanmarkfavoritereplyonanytopic':
        'whoCanMarkFavoriteReplyOnAnyTopic',
    'whocanmarkfavoritereplyonowntopic':
        'whoCanMarkFavoriteReplyOnOwnTopic',
    'whocanmarknoresponseneeded':
        'whoCanMarkNoResponseNeeded',
    'whocanmoderatecontent':
        'whoCanModerateContent',
    'whocanmoderatemembers':
        'whoCanModerateMembers',
    'whocanmodifymembers':
        'whoCanModifyMembers',
    'whocanmodifytagsandcategories':
        'whoCanModifyTagsAndCategories',
    'whocanmovetopicsin':
        'whoCanMoveTopicsIn',
    'whocanmovetopicsout':
        'whoCanMoveTopicsOut',
    'whocanpostannouncements':
        'whoCanPostAnnouncements',
    'whocanpostmessage':
        'whoCanPostMessage',
    'whocantaketopics':
        'whoCanTakeTopics',
    'whocanunassigntopic':
        'whoCanUnassignTopic',
    'whocanunmarkfavoritereplyonanytopic':
        'whoCanUnmarkFavoriteReplyOnAnyTopic',
    'whocanviewgroup':
        'whoCanViewGroup',
    'whocanviewmembership':
        'whoCanViewMembership',
}


def print_():
    cd = gapi_directory.build()
    i = 3
    members = membersCountOnly = managers = managersCountOnly = owners = ownersCountOnly = False
    customer = GC_Values[GC_CUSTOMER_ID]
    usedomain = usemember = usequery = None
    aliasDelimiter = ' '
    memberDelimiter = '\n'
    todrive = False
    cdfieldsList = []
    gsfieldsList = []
    fieldsTitles = {}
    titles = []
    csvRows = []
    display.add_field_title_to_csv_file('email',
                                        GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP,
                                        cdfieldsList, fieldsTitles, titles)
    roles = []
    getSettings = sortHeaders = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'domain':
            usedomain = sys.argv[i + 1].lower()
            customer = None
            i += 2
        elif myarg == 'member':
            usemember = gam.normalizeEmailAddressOrUID(sys.argv[i + 1])
            customer = usequery = None
            i += 2
        elif myarg == 'query':
            usequery = sys.argv[i + 1]
            usemember = None
            i += 2
        elif myarg == 'maxresults':
            # deprecated argument
            i += 2
        elif myarg == 'delimiter':
            aliasDelimiter = memberDelimiter = sys.argv[i + 1]
            i += 2
        elif myarg in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
            display.add_field_title_to_csv_file(
                myarg, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList,
                fieldsTitles, titles)
            i += 1
        elif myarg == 'settings':
            getSettings = True
            i += 1
        elif myarg == 'allfields':
            getSettings = sortHeaders = True
            cdfieldsList = []
            gsfieldsList = []
            fieldsTitles = {}
            for field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
                display.add_field_title_to_csv_file(
                    field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP, cdfieldsList,
                    fieldsTitles, titles)
            i += 1
        elif myarg == 'sortheaders':
            sortHeaders = True
            i += 1
        elif myarg == 'fields':
            fieldNameList = sys.argv[i + 1]
            for field in fieldNameList.lower().replace(',', ' ').split():
                if field in GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP:
                    display.add_field_title_to_csv_file(
                        field, GROUP_ARGUMENT_TO_PROPERTY_TITLE_MAP,
                        cdfieldsList, fieldsTitles, titles)
                elif field in GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP:
                    display.add_field_to_csv_file(field, {
                        field:
                            [GROUP_ATTRIBUTES_ARGUMENT_TO_PROPERTY_MAP[field]]
                    }, gsfieldsList, fieldsTitles, titles)
                elif field == 'collaborative':
                    for attrName in COLLABORATIVE_INBOX_ATTRIBUTES:
                        display.add_field_to_csv_file(attrName,
                                                      {attrName: [attrName]},
                                                      gsfieldsList,
                                                      fieldsTitles, titles)
                else:
                    controlflow.invalid_argument_exit(
                        field, 'gam print groups fields')
            i += 2
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
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print groups')
    cdfields = ','.join(set(cdfieldsList))
    if gsfieldsList:
        getSettings = True
        gsfields = ','.join(set(gsfieldsList))
    elif getSettings:
        gsfields = None
    if getSettings:
        gs = gam.buildGAPIObject('groupssettings')
    roles = ','.join(sorted(set(roles)))
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
    gam.printGettingAllItems('Groups', None)
    page_message = gapi.got_total_items_first_last_msg('Groups')
    entityList = gapi.get_all_pages(cd.groups(),
                                    'list',
                                    'groups',
                                    page_message=page_message,
                                    message_attribute='email',
                                    customer=customer,
                                    domain=usedomain,
                                    userKey=usemember,
                                    query=usequery,
                                    fields=f'nextPageToken,groups({cdfields})')
    i = 0
    count = len(entityList)
    for groupEntity in entityList:
        i += 1
        groupEmail = groupEntity['email']
        group = {}
        for field in cdfieldsList:
            if field in groupEntity:
                if isinstance(groupEntity[field], list):
                    group[fieldsTitles[field]] = aliasDelimiter.join(
                        groupEntity[field])
                else:
                    group[fieldsTitles[field]] = groupEntity[field]
        if roles:
            sys.stderr.write(
                f' Getting {roles} for {groupEmail}{gam.currentCountNL(i, count)}')
            page_message = gapi.got_total_items_first_last_msg('Members')
            validRoles, listRoles, listFields = gam._getRoleVerification(
                roles, 'nextPageToken,members(email,id,role)')
            groupMembers = gapi.get_all_pages(cd.members(),
                                              'list',
                                              'members',
                                              page_message=page_message,
                                              message_attribute='email',
                                              soft_errors=True,
                                              groupKey=groupEmail,
                                              roles=listRoles,
                                              fields=listFields)
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
                member_email = member.get('email', member.get('id', None))
                if not member_email:
                    sys.stderr.write(f' Not sure what to do with: {member}')
                    continue
                role = member.get('role', ROLE_MEMBER)
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
        if getSettings and not GroupIsAbuseOrPostmaster(groupEmail):
            sys.stderr.write(
                f' Retrieving Settings for group {groupEmail}{gam.currentCountNL(i, count)}'
            )
            settings = gapi.call(gs.groups(),
                                 'get',
                                 soft_errors=True,
                                 retry_reasons=[
                                     gapi_errors.ErrorReason.SERVICE_LIMIT,
                                     gapi_errors.ErrorReason.INVALID
                                 ],
                                 groupUniqueId=mapGroupEmailForSettings(groupEmail),
                                 fields=gsfields)
            if settings:
                for key in settings:
                    if key in ['email', 'name', 'description', 'kind', 'etag']:
                        continue
                    setting_value = settings[key]
                    if setting_value is None:
                        setting_value = ''
                    if key not in titles:
                        titles.append(key)
                    group[key] = setting_value
            else:
                sys.stderr.write(
                    f' Settings unavailable for group {groupEmail}{gam.currentCountNL(i, count)}'
                )
        csvRows.append(group)
    if sortHeaders:
        display.sort_csv_titles([
            'Email',
        ], titles)
    display.write_csv_file(csvRows, titles, 'Groups', todrive)


def print_members():
    cd = gapi_directory.build()
    todrive = False
    membernames = False
    includeDerivedMembership = False
    customer = GC_Values[GC_CUSTOMER_ID]
    checkSuspended = usedomain = usemember = usequery = None
    roles = []
    fields = 'nextPageToken,members(email,id,role,status,type)'
    titles = ['group']
    csvRows = []
    groups_to_get = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'domain':
            usedomain = sys.argv[i + 1].lower()
            customer = None
            i += 2
        elif myarg == 'member':
            usemember = gam.normalizeEmailAddressOrUID(sys.argv[i + 1])
            customer = usequery = None
            i += 2
        elif myarg == 'query':
            usequery = sys.argv[i + 1]
            usemember = None
            i += 2
        elif myarg == 'fields':
            memberFieldsList = sys.argv[i + 1].replace(',', ' ').lower().split()
            fields = f'nextPageToken,members({",".join(memberFieldsList)})'
            i += 2
        elif myarg == 'membernames':
            membernames = True
            titles.append('name')
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
        elif myarg in ['group', 'groupns', 'groupsusp']:
            group_email = gam.normalizeEmailAddressOrUID(sys.argv[i + 1])
            groups_to_get = [{'email': group_email}]
            if myarg == 'groupns':
                checkSuspended = False
            elif myarg == 'groupsusp':
                checkSuspended = True
            i += 2
        elif myarg in ['suspended', 'notsuspended']:
            checkSuspended = myarg == 'suspended'
            i += 1
        elif myarg == 'includederivedmembership':
            includeDerivedMembership = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print group-members')
    if not groups_to_get:
        groups_to_get = gapi.get_all_pages(cd.groups(),
                                           'list',
                                           'groups',
                                           message_attribute='email',
                                           customer=customer,
                                           domain=usedomain,
                                           userKey=usemember,
                                           query=usequery,
                                           fields='nextPageToken,groups(email)')
    i = 0
    count = len(groups_to_get)
    for group in groups_to_get:
        i += 1
        group_email = group['email']
        sys.stderr.write(
            f'Getting members for {group_email}{gam.currentCountNL(i, count)}')
        validRoles, listRoles, listFields = gam._getRoleVerification(
            ','.join(roles), fields)
        group_members = gapi.get_all_pages(
            cd.members(),
            'list',
            'members',
            soft_errors=True,
            includeDerivedMembership=includeDerivedMembership,
            groupKey=group_email,
            roles=listRoles,
            fields=listFields)
        for member in group_members:
            if not _checkMemberRoleIsSuspended(member, validRoles,
                                               checkSuspended):
                continue
            for title in member:
                if title not in titles:
                    titles.append(title)
            member['group'] = group_email
            if membernames and 'type' in member and 'id' in member:
                if member['type'] == 'USER':
                    try:
                        mbinfo = gapi.call(
                            cd.users(),
                            'get',
                            throw_reasons=[
                                gapi_errors.ErrorReason.USER_NOT_FOUND,
                                gapi_errors.ErrorReason.NOT_FOUND,
                                gapi_errors.ErrorReason.FORBIDDEN
                            ],
                            userKey=member['id'],
                            fields='name')
                        memberName = mbinfo['name']['fullName']
                    except (gapi_errors.GapiUserNotFoundError,
                            gapi_errors.GapiNotFoundError,
                            gapi_errors.GapiForbiddenError):
                        memberName = 'Unknown'
                elif member['type'] == 'GROUP':
                    try:
                        mbinfo = gapi.call(
                            cd.groups(),
                            'get',
                            throw_reasons=[
                                gapi_errors.ErrorReason.NOT_FOUND,
                                gapi_errors.ErrorReason.FORBIDDEN
                            ],
                            groupKey=member['id'],
                            fields='name')
                        memberName = mbinfo['name']
                    except (gapi_errors.GapiNotFoundError,
                            gapi_errors.GapiForbiddenError):
                        memberName = 'Unknown'
                elif member['type'] == 'CUSTOMER':
                    try:
                        mbinfo = gapi.call(
                            cd.customers(),
                            'get',
                            throw_reasons=[
                                gapi_errors.ErrorReason.BAD_REQUEST,
                                gapi_errors.ErrorReason.RESOURCE_NOT_FOUND,
                                gapi_errors.ErrorReason.FORBIDDEN
                            ],
                            customerKey=member['id'],
                            fields='customerDomain')
                        memberName = mbinfo['customerDomain']
                    except (gapi_errors.GapiBadRequestError,
                            gapi_errors.GapiResourceNotFoundError,
                            gapi_errors.GapiForbiddenError):
                        memberName = 'Unknown'
                else:
                    memberName = 'Unknown'
                member['name'] = memberName
            csvRows.append(member)
    display.write_csv_file(csvRows, titles, 'Group Members', todrive)


def _checkMemberRoleIsSuspended(member, validRoles, isSuspended):
    if validRoles and member.get('role', ROLE_MEMBER) not in validRoles:
        return False
    if isSuspended is None:
        return True
    memberStatus = member.get('status', 'UNKNOWN')
    if not isSuspended:
        return memberStatus != 'SUSPENDED'
    return memberStatus == 'SUSPENDED'


UPDATE_GROUP_SUBCMDS = ['add', 'clear', 'delete', 'remove', 'sync', 'update']
GROUP_ROLES_MAP = {
    'owner': ROLE_OWNER,
    'owners': ROLE_OWNER,
    'manager': ROLE_MANAGER,
    'managers': ROLE_MANAGER,
    'member': ROLE_MEMBER,
    'members': ROLE_MEMBER,
}
MEMBER_DELIVERY_MAP = {
    'allmail': 'ALL_MAIL',
    'digest': 'DIGEST',
    'daily': 'DAILY',
    'abridged': 'DAILY',
    'nomail': 'NONE',
    'none': 'NONE'
}


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
        role = None
        delivery = None
        i = 5
        if sys.argv[i].lower() in GROUP_ROLES_MAP:
            role = GROUP_ROLES_MAP[sys.argv[i].lower()]
            i += 1
        if sys.argv[i].lower() in ['suspended', 'notsuspended']:
            checkSuspended = sys.argv[i].lower() == 'suspended'
            i += 1
        if sys.argv[i].lower().replace('_', '') in MEMBER_DELIVERY_MAP:
            delivery = MEMBER_DELIVERY_MAP[sys.argv[i].lower().replace('_', '')]
            i += 1
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
        return (role, users_email, delivery)

    gs_get_before_update = False
    cd = gapi_directory.build()
    group = sys.argv[3]
    myarg = sys.argv[4].lower()
    items = []
    if myarg in UPDATE_GROUP_SUBCMDS:
        group = gam.normalizeEmailAddressOrUID(group)
        if myarg == 'add':
            role, users_email, delivery = _getRoleAndUsers()
            if not role:
                role = ROLE_MEMBER
            if not exists(cd, group):
                return
            if len(users_email) > 1:
                sys.stderr.write(
                    f'Group: {group}, Will add {len(users_email)} {role}s.\n')
                for user_email in users_email:
                    item = ['gam', 'update', 'group', group, 'add', role]
                    if delivery:
                        item.append(delivery)
                    item.append(user_email)
                    items.append(item)
            elif len(users_email) > 0:
                body = {
                    'role':
                        role,
                    'email' if users_email[0].find('@') != -1 else 'id':
                        users_email[0]
                }
                add_text = [f'as {role}']
                if delivery:
                    body['delivery_settings'] = delivery
                    add_text.append(f'delivery {delivery}')
                for i in range(2):
                    try:
                        gapi.call(
                            cd.members(),
                            'insert',
                            throw_reasons=[
                                gapi_errors.ErrorReason.DUPLICATE,
                                gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                gapi_errors.ErrorReason.RESOURCE_NOT_FOUND,
                                gapi_errors.ErrorReason.INVALID_MEMBER,
                                gapi_errors.ErrorReason.
                                CYCLIC_MEMBERSHIPS_NOT_ALLOWED
                            ],
                            groupKey=group,
                            body=body)
                        print(
                            f' Group: {group}, {users_email[0]} Added {" ".join(add_text)}'
                        )
                        break
                    except gapi_errors.GapiDuplicateError as e:
                        # check if user is a full member, not pending
                        try:
                            result = gapi.call(
                                cd.members(),
                                'get',
                                throw_reasons=[
                                    gapi_errors.ErrorReason.MEMBER_NOT_FOUND
                                ],
                                memberKey=users_email[0],
                                groupKey=group,
                                fields='role')
                            print(
                                f' Group: {group}, {users_email[0]} Add {" ".join(add_text)} Failed: Duplicate, already a {result["role"]}'
                            )
                            break  # if get succeeds, user is a full member and we throw duplicate error
                        except gapi_errors.GapiMemberNotFoundError:
                            # insert fails on duplicate and get fails on not found, user is pending
                            print(
                                f' Group: {group}, {users_email[0]} member is pending, deleting and re-adding to solve...'
                            )
                            gapi.call(cd.members(),
                                      'delete',
                                      memberKey=users_email[0],
                                      groupKey=group)
                            continue  # 2nd insert should succeed now that pending is clear
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
            role, users_email, delivery = _getRoleAndUsers()
            for user_email in users_email:
                if user_email in ('*', GC_Values[GC_CUSTOMER_ID]):
                    syncMembersSet.add(GC_Values[GC_CUSTOMER_ID])
                else:
                    syncMembersSet.add(
                        _cleanConsumerAddress(user_email.lower(),
                                              syncMembersMap))
            group = exists(cd, group)
            if group:
                currentMembersSet = set()
                currentMembersMap = {}
                for current_email in gam.getUsersToModify(
                        entity_type='group',
                        entity=group,
                        member_type=role,
                        groupUserMembersOnly=False):
                    if current_email == GC_Values[GC_CUSTOMER_ID]:
                        currentMembersSet.add(current_email)
                    else:
                        currentMembersSet.add(
                            _cleanConsumerAddress(current_email.lower(),
                                                  currentMembersMap))


# Compare incoming members and current members using the cleaned addresses; we actually add/remove with the original addresses
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
                    item = ['gam', 'update', 'group', group, 'add']
                    if role:
                        item.append(role)
                    if delivery:
                        item.append(delivery)
                    item.append(user)
                    items.append(item)
                for user in to_remove:
                    items.append(
                        ['gam', 'update', 'group', group, 'remove', user])
        elif myarg in ['delete', 'remove']:
            _, users_email, _ = _getRoleAndUsers()
            if not exists(cd, group):
                return
            if len(users_email) > 1:
                sys.stderr.write(
                    f'Group: {group}, Will remove {len(users_email)} emails.\n')
                for user_email in users_email:
                    items.append(
                        ['gam', 'update', 'group', group, 'remove', user_email])
            elif len(users_email) > 0:
                try:
                    gapi.call(cd.members(),
                              'delete',
                              throw_reasons=[
                                  gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                  gapi_errors.ErrorReason.INVALID_MEMBER
                              ],
                              groupKey=group,
                              memberKey=users_email[0])
                    print(f' Group: {group}, {users_email[0]} Removed')
                except (gapi_errors.GapiMemberNotFoundError,
                        gapi_errors.GapiInvalidMemberError) as e:
                    print(
                        f' Group: {group}, {users_email[0]} Remove Failed: {str(e)}'
                    )
        elif myarg == 'update':
            role, users_email, delivery = _getRoleAndUsers()
            group = exists(cd, group)
            if group:
                if not role and not delivery:
                    role = ROLE_MEMBER
                if len(users_email) > 1:
                    sys.stderr.write(
                        f'Group: {group}, Will update {len(users_email)} {role}s.\n'
                    )
                    for user_email in users_email:
                        item = ['gam', 'update', 'group', group, 'update']
                        if role:
                            item.append(role)
                        if delivery:
                            item.append(delivery)
                        item.append(user_email)
                        items.append(item)
                elif len(users_email) > 0:
                    body = {}
                    update_text = []
                    if role:
                        body['role'] = role
                        update_text.append(f'to {role}')
                    if delivery:
                        body['delivery_settings'] = delivery
                        update_text.append(f'delivery {delivery}')
                    try:
                        gapi.call(cd.members(),
                                  'update',
                                  throw_reasons=[
                                      gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                      gapi_errors.ErrorReason.INVALID_MEMBER
                                  ],
                                  groupKey=group,
                                  memberKey=users_email[0],
                                  body=body)
                        print(
                            f' Group: {group}, {users_email[0]} Updated {" ".join(update_text)}'
                        )
                    except (gapi_errors.GapiMemberNotFoundError,
                            gapi_errors.GapiInvalidMemberError) as e:
                        print(
                            f' Group: {group}, {users_email[0]} Update to {role} Failed: {str(e)}'
                        )
        else:  # clear
            checkSuspended = None
            fields = ['email', 'id']
            roles = []
            i = 5
            while i < len(sys.argv):
                myarg = sys.argv[i].lower()
                if myarg.upper() in [ROLE_OWNER, ROLE_MANAGER, ROLE_MEMBER]:
                    roles.append(myarg.upper())
                    i += 1
                elif myarg in ['suspended', 'notsuspended']:
                    checkSuspended = myarg == 'suspended'
                    fields.append('status')
                    i += 1
                else:
                    controlflow.invalid_argument_exit(sys.argv[i],
                                                      'gam update group clear')
            if roles:
                roles = ','.join(sorted(set(roles)))
            else:
                roles = ROLE_MEMBER
            group = gam.normalizeEmailAddressOrUID(group)
            member_type_message = f'{roles.lower()}s'
            sys.stderr.write(
                f'Getting {member_type_message} of {group} (may take some time for large groups)...\n'
            )
            page_message = gapi.got_total_items_msg(f'{member_type_message}',
                                                    '...')
            validRoles, listRoles, listFields = gam._getRoleVerification(
                roles, f'nextPageToken,members({",".join(fields)})')
            try:
                result = gapi.get_all_pages(
                    cd.members(),
                    'list',
                    'members',
                    page_message=page_message,
                    throw_reasons=gapi_errors.MEMBERS_THROW_REASONS,
                    groupKey=group,
                    roles=listRoles,
                    fields=listFields)
                if not result:
                    print('Group already has 0 members')
                    return
                users_email = [
                    member.get('email', member['id'])
                    for member in result
                    if _checkMemberRoleIsSuspended(member, validRoles,
                                                   checkSuspended)
                ]
                if len(users_email) > 1:
                    sys.stderr.write(
                        f'Group: {group}, Will remove {len(users_email)} {"" if checkSuspended is None else ["Non-suspended ", "Suspended "][checkSuspended]}{roles}s.\n'
                    )
                    for user_email in users_email:
                        items.append([
                            'gam', 'update', 'group', group, 'remove',
                            user_email
                        ])
                elif len(users_email) > 0:
                    try:
                        gapi.call(cd.members(),
                                  'delete',
                                  throw_reasons=[
                                      gapi_errors.ErrorReason.MEMBER_NOT_FOUND,
                                      gapi_errors.ErrorReason.INVALID_MEMBER
                                  ],
                                  groupKey=group,
                                  memberKey=users_email[0])
                        print(f' Group: {group}, {users_email[0]} Removed')
                    except (gapi_errors.GapiMemberNotFoundError,
                            gapi_errors.GapiInvalidMemberError) as e:
                        print(
                            f' Group: {group}, {users_email[0]} Remove Failed: {str(e)}'
                        )
            except (gapi_errors.GapiGroupNotFoundError,
                    gapi_errors.GapiDomainNotFoundError,
                    gapi_errors.GapiInvalidError,
                    gapi_errors.GapiForbiddenError):
                gam.entityUnknownWarning('Group', group, 0, 0)
        if items:
            gam.run_batch(items)
    else:
        i = 4
        use_cd_api = False
        gs = None
        gs_body = {}
        cd_body = {}
        while i < len(sys.argv):
            myarg = sys.argv[i].lower().replace('_', '')
            if myarg == 'email':
                use_cd_api = True
                cd_body['email'] = gam.normalizeEmailAddressOrUID(sys.argv[i +
                                                                           1])
                i += 2
            elif myarg == 'admincreated':
                use_cd_api = True
                cd_body['adminCreated'] = gam.getBoolean(sys.argv[i + 1], myarg)
                i += 2
            elif myarg == 'getbeforeupdate':
                gs_get_before_update = True
                i += 1
            else:
                if not gs:
                    gs = gam.buildGAPIObject('groupssettings')
                    gs_object = gs._rootDesc
                getGroupAttrValue(myarg, sys.argv[i + 1], gs_object, gs_body,
                                  'update')
                i += 2
        group = gam.normalizeEmailAddressOrUID(group)
        if use_cd_api or (
                group.find('@') == -1
        ):  # group settings API won't take uid so we make sure cd API is used so that we can grab real email.
            group = gapi.call(cd.groups(),
                              'update',
                              groupKey=group,
                              body=cd_body,
                              fields='email')['email']
        if gs:
            if not GroupIsAbuseOrPostmaster(group):
                if gs_get_before_update:
                    current_settings = gapi.call(
                        gs.groups(),
                        'get',
                        retry_reasons=[gapi_errors.ErrorReason.SERVICE_LIMIT],
                        groupUniqueId=mapGroupEmailForSettings(group),
                        fields='*')
                    if current_settings is not None:
                        gs_body = dict(
                            list(current_settings.items()) +
                            list(gs_body.items()))
                if gs_body:
                    gapi.call(
                        gs.groups(),
                        'update',
                        retry_reasons=[gapi_errors.ErrorReason.SERVICE_LIMIT],
                        groupUniqueId=mapGroupEmailForSettings(group),
                        body=gs_body)
        print(f'updated group {group}')


GROUP_SETTINGS_LIST_PATTERN = re.compile(r'([A-Z][A-Z_]+[A-Z]?)')


def getGroupAttrValue(myarg, value, gs_object, gs_body, function):
    if myarg == 'collaborative':
        myarg = 'enablecollaborativeinbox'
    for (attrib,
         params) in list(gs_object['schemas']['Groups']['properties'].items()):
        if attrib in ['kind', 'etag', 'email']:
            continue
        if myarg == attrib.lower():
            if params['type'] == 'integer':
                try:
                    if value[-1:].upper() == 'M':
                        value = int(value[:-1]) * 1024 * 1024
                    elif value[-1:].upper() == 'K':
                        value = int(value[:-1]) * 1024
                    elif value[-1].upper() == 'B':
                        value = int(value[:-1])
                    else:
                        value = int(value)
                except ValueError:
                    controlflow.system_error_exit(
                        2,
                        f'{myarg} must be a number ending with M (megabytes), K (kilobytes) or nothing (bytes); got {value}'
                    )
            elif params['type'] == 'string':
                if attrib == 'description':
                    value = value.replace('\\n', '\n')
                elif attrib == 'primaryLanguage':
                    value = LANGUAGE_CODES_MAP.get(value.lower(), value)
                elif attrib in GROUP_SETTINGS_LIST_ATTRIBUTES:
                    value = value.upper()
                    possible_values = GROUP_SETTINGS_LIST_PATTERN.findall(
                        params['description'])
                    if value not in possible_values:
                        controlflow.expected_argument_exit(
                            f'value for {attrib}', ', '.join(possible_values),
                            value)
                elif attrib in GROUP_SETTINGS_BOOLEAN_ATTRIBUTES:
                    value = value.lower()
                    if value in true_values:
                        value = 'true'
                    elif value in false_values:
                        value = 'false'
                    else:
                        controlflow.expected_argument_exit(
                            f'value for {attrib}', ', '.join(['true', 'false']),
                            value)
            gs_body[attrib] = value
            return
    controlflow.invalid_argument_exit(myarg, f'gam {function} group')
