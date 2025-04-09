# Cloud Identity Groups
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Notes](#Notes)
- [Definitions](#definitions)
- [Manage groups](#manage-groups)
- [Display information about individual groups](#display-information-about-individual-groups)
- [Display information about multiple groups](#display-information-about-multiple-groups)
- [Display group counts](#display-group-counts)

## API documentation
* [Cloud Identity Groups Overview](https://cloud.google.com/identity/docs/groups)
* [Create and Manage Groups uning API](https://support.google.com/a/answer/10427204)
* [Cloud Identity Groups API - Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups)
* [Restrict Group Membership](https://support.google.com/a/answer/11192679)
* [Lock Groups Beta](https://workspaceupdates.googleblog.com/2024/12/locked-groups-open-beta.html)
* [Cloud Identity Groups](https://gsuiteupdates.googleblog.com/2020/08/new-api-cloud-identity-groups-google.html)
* [Security Groups](https://gsuiteupdates.googleblog.com/2020/09/security-groups-beta.html)

## Query documentation
* [Cloud Identity Groups API - Search Dynamic Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery)
* [Member REstrictions](https://cloud.google.com/identity/docs/reference/rest/v1/SecuritySettings#MemberRestriction)

## Notes

In version 7.02.01 options `locked` and `unlocked` wre added to `gam update cigroups` that allow locking groups.

* See: https://workspaceupdates.googleblog.com/2024/12/locked-groups-open-beta.html

You'll have to do a `gam oauth create` and enable the following scope to use these options:
```
[*] 22)  Cloud Identity Groups API Beta (Enables group locking/unlocking)
```

In the Admin Directory API a group has the following characteristics:
* `id` - The unique ID of a group
* `email` - The group's email address
* `name` - The group's display name

In the Cloud Indentity Groups API a group has the following characteristics:
* `name` - The unique ID of a group
* `groupKey.id` - The group's email address
* `displayName` - The group's display name

The Admin Directory API group characteristic names will be used.

Dynamic Groups require Cloud Identity Premium accounts.

* https://cloud.google.com/identity/docs/how-to/create-dynamic-groups

The `cimember <UserItem>` option of `gam print cigroups` requires a Google Workspace Enterprise Standard, Enterprise Plus, and Enterprise for Education;
and Cloud Identity Premium accounts. Unfortunately, even if you have the required account, the API call that supports the query doesn't work.

* https://cloud.google.com/identity/docs/reference/rest/v1/groups.memberships/searchTransitiveGroups

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<GroupList> ::= "<GroupItem>(,<GroupItem>)*"
<GroupEntity> ::=
        <GroupList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<GroupRole> ::= owner|manager|member
<GroupRoleList> ::= "<GroupRole>(,<GroupRole>)*"
<CIGroupMemberType> ::= cbcmbrowser|customer|group|other|serviceaccount|user
<CIGroupMemberTypeList> ::= "<CIGroupMemberType>(,<CIGroupMemberType>)*"
<QueryDynamicGroup> ::= <String>
        See: https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery
<QueryMemberRestrictions> ::= <String>
        See: https://cloud.google.com/identity/docs/reference/rest/v1/SecuritySettings#MemberRestriction

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<GroupSettingsAttribute> ::=
        (allowexternalmembers <Boolean>)|
        (allowwebposting <Boolean>)|
        (archiveonly <Boolean>)|
        (customfootertext <String>)|
        (customreplyto <EmailAddress>)|
        (defaultmessagedenynotificationtext <String>)|
        (description <String>)|
        (enablecollaborativeinbox|collaborative <Boolean>)|
        (includeinglobaladdresslist|gal <Boolean>)|
        (includecustomfooter <Boolean>)|
        (isarchived <Boolean>)|
        (memberscanpostasthegroup <Boolean>)|
        (messagemoderationlevel moderate_all_messages|moderate_non_members|moderate_new_members|moderate_none)|
        (name|displayname <String>)|
        (primarylanguage <Language>)|
        (replyto reply_to_custom|reply_to_sender|reply_to_list|reply_to_owner|reply_to_ignore|reply_to_managers)|
        (sendmessagedenynotification <Boolean>)|
        (spammoderationlevel allow|moderate|silently_moderate|reject)|
        (whocanadd all_members_can_add|all_managers_can_add|all_owners_can_add|none_can_add)|
        (whocancontactowner anyone_can_contact|all_in_domain_can_contact|all_members_can_contact|all_managers_can_contact)|
        (whocanjoin anyone_can_join|all_in_domain_can_join|invited_can_join|can_request_to_join)|
        (whocanleavegroup all_members_can_leave|all_managers_can_leave|all_owners_can_leave|none_can_leave)|
        (whocanpostmessage none_can_post|all_managers_can_post|all_members_can_post|all_owners_can_post|all_in_domain_can_post|anyone_can_post)|
        (whocanviewgroup anyone_can_view|all_in_domain_can_view|all_members_can_view|all_managers_can_view|all_owners_can_view)|
        (whocanviewmembership all_in_domain_can_view|all_members_can_view|all_managers_can_view|all_owners_can_view)
<GroupWhoCanDiscoverGroupDeprecatedAttribute> ::=
        (showingroupdirectory <Boolean>)
<GroupWhoCanAssistContentDeprecatedAttribute> ::=
        (whocanassigntopics all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanenterfreeformtags all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanhideabuse all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmaketopicssticky all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmarkduplicate all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmarkfavoritereplyonanytopic all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmarknoresponseneeded all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmodifytagsandcategories all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocantaketopics all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanunassigntopic all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanunmarkfavoritereplyonanytopic all_members|owners_and_managers|managers_only|owners_only|none)
<GroupWhoCanModerateContentDeprecatedAttribute> ::=
        (whocanapprovemessages all_members|owners_and_managers|owners_only|none)|
        (whocandeleteanypost all_members|owners_and_managers|owners_only|none)|
        (whocandeletetopics all_members|owners_and_managers|owners_only|none)|
        (whocanlocktopics all_members|owners_and_managers|owners_only|none)|
        (whocanmovetopicsin all_members|owners_and_managers|owners_only|none)|
        (whocanmovetopicsout all_members|owners_and_managers|owners_only|none)|
        (whocanpostannouncements all_members|owners_and_managers|owners_only|none)
<GroupWhoCanModerateMembersDeprecatedAttribute> ::=
        (whocanadd all_members_can_add|all_managers_can_add|none_can_add)|
        (whocanapprovemembers all_members_can_approve|all_managers_can_approve|all_owners_can_approve|none_can_approve)|
        (whocanbanusers all_members|owners_and_managers|owners_only|none)|
        (whocaninvite all_members_can_invite|all_managers_can_invite|all_owners_can_invite|none_can_invite)|
        (whocanmodifymembers all_members|owners_and_managers|owners_only|none)
<GroupDeprecatedAttribute> ::=
        (allowgooglecommunication <Boolean>)|
        (favoriterepliesontop <Boolean>)|
        (maxmessagebytes <ByteCount>)|
        (messagedisplayfont default_font|fixed_width_font)|
        (whocanaddreferences all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmarkfavoritereplyonowntopic all_members|owners_and_managers|managers_only|owners_only|none)
<GroupAttribute> ::=
        <JSONData>|
        <GroupSettingsAttribute>|
        (whocandiscovergroup allmemberscandiscover|allindomaincandiscover|anyonecandiscover)|
        (whocanassistcontent all_members|owners_and_managers|managers_only|owners_only|none)|
        (whocanmoderatecontent all_members|owners_and_managers|owners_only|none)|
        (whocanmoderatemembers all_members|owners_and_managers|owners_only|none)|
        <GroupWhoCanDiscoverGroupDeprecatedAttribute>|
        <GroupWhoCanAssistContentDeprecatedAttribute>|
        <GroupWhoCanModerateContentDeprecatedAttribute>|
        <GroupWhoCanModerateMembersDeprecatedAttribute>|
        <GroupDeprecatedAttribute>
```
```
<GroupFieldName> ::=
        admincreated|
        aliases|
        allowexternalmembers|
        allowgooglecommunication|
        allowwebposting|
        archiveonly|
        customfootertext|
        customreplyto|
        customrolesenabledforsettingstobemerged|
        defaultmessagedenynotificationtext|
        description|
        directmemberscount|
        email|
        enablecollaborativeinbox|collaborative|
        favoriterepliesontop|
        id|
        includecustomfooter|
        includeinglobaladdresslist|gal|
        isarchived|
        maxmessagebytes|
        memberscanpostasthegroup|
        messagedisplayfont|
        messagemoderationlevel|
        name|
        primarylanguage|
        replyto|
        sendmessagedenynotification|
        showingroupdirectory|
        spammoderationlevel|
        whocanaddreferences|
        whocanadd|
        whocanapprovemessages|
        whocanassigntopics|
        whocanassistcontent|
        whocancontactowner|
        whocandeleteanypost|
        whocandeletetopics|
        whocandiscovergroup|
        whocanenterfreeformtags|
        whocanhideabuse|
        whocaninvite|
        whocanjoin|
        whocanleavegroup|
        whocanlocktopics|
        whocanmaketopicssticky|
        whocanmarkduplicate|
        whocanmarkfavoritereplyonanytopic|
        whocanmarkfavoritereplyonowntopic|
        whocanmarknoresponseneeded|
        whocanmoderatecontent|
        whocanmodifytagsandcategories|
        whocanmovetopicsin|
        whocanmovetopicsout|
        whocanpostannouncements|
        whocanpostmessage|
        whocantaketopics|
        whocanunassigntopic|
        whocanunmarkfavoritereplyonanytopic|
        whocanviewgroup|
        whocanviewmembership
<GroupFieldNameList> ::= "<GroupFieldName>(,<GroupFieldName>)*"
```
```
<CIGroupFieldName> ::=
        additionalgroupkeys|
        createtime|
        description|
        displayname|
        dynamicgroupmetadata|
        email|
        groupkey|
        id|
        labels|
        name|
        parent|
        updatetime
<CIGroupFieldNameList> ::= "<CIGroupFieldName>(,<CIGroupFieldName>)*"
```
## Manage groups

These commands allow you to create, update and delete groups. They use the Admin SDK Groups Settings API
to set `<GroupAttribute>`.
```
gam create cigroup <EmailAddress>
        [copyfrom <GroupItem>] <GroupAttribute>*
        [makeowner] [alias|aliases <CIGroupAliasList>]
        [security|makesecuritygroup]
        [dynamic <QueryDynamicGroup>]
gam update cigroup <GroupEntity> [copyfrom <GroupItem>] <GroupAttribute>
        [security|makesecuritygroup|
         dynamicsecurity|makedynamicsecuritygroup|
         lockedsecurity|makelockedsecuritygroup]
        [locked|unlocked]
        [dynamic <QueryDynamicGroup>]
        [memberrestrictions <QueryMemberRestrictions>]
gam delete cigroups <GroupEntity>
```
The `copyfrom <GroupItem>` allows copying of group attributes from one group to another.
The following attributes are not copied: name, description, email, admincreated, aliases, noneditablealiases.
Any `<GroupAttribute>` specified will override the copied attributes.

You can update a non-dynamic group to a non-dynamic security group with the `makesecuritygroup` option. To update a dynamic group to a security group, use the `makedynamicsecuritygroup` option instead.
* Warning: A Security Group cannot be changed back to a Google Group.

You can update a group to restrict its membership with the `memberrestrictions <QueryMemberRestrictions>`option.
* https://cloud.google.com/identity/docs/reference/rest/v1/SecuritySettings#MemberRestriction

The `makeowner` option makes the administrator in `oauth2.txt` the initial owner of the group.

## Display information about individual groups
This command displays information as an indented list of keys and values.
```
gam info cigroups <GroupEntity>
        [nousers|membertree] [quick] [noaliases]
        [nosecurity|nosecuritysettings]
        [allfields|<CIGroupFieldName>*|(fields <CIGroupFieldNameList>)]
        [roles <GroupRoleList>] [members] [managers] [owners]
        [internal] [internaldomains <DomainNameList>] [external]
        [types <CIGroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [formatjson]
```

By default, all direct members, managers and owners in the group are displayed; these options modify that behavior:
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners
* `nousers` or `quick` - Do not display any members, managers or owners
* `membertree` - Display all roles; expand all groups

By default, when displaying members from a group, all types of members (customer, group, serviceaccount, user) in the group are displayed; this option modifies that behavior:
* `types <CIGroupMemberTypeList>` - Display specified types

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, `chrome-os-device` and `cbcm-browser` are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, all group aliases are displayed, these options modify that behavior:
* `noaliases` or `quick` - Do not display group aliases

By default, GAM makes an additional API call to get the `SecuritySettings` for the group.
* `nosecuritysettings` - Do not make API and display `SecuritySettings`

* `allfields` - All Cloud Identity Group fields
* `<CIGroupFieldName>*` - Individual fields to display
* `fields <CIGroupFieldNameList>` - A comma separated list of fields to display

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the output in JSON notation

## Display information about multiple groups
This command displays information in CSV format.
```
gam print cigroups [todrive <ToDriveAttribute>*]
        [(cimember|showownedby <UserItem>)|(select <GroupEntity>)|(query <String>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        [basic|allfields|(<CIGroupFieldName>* [fields <CIGroupFieldNameList>])]
        [roles <GroupRoleList>] [memberrestrictions]
        [internal] [internaldomains <DomainNameList>] [external]
        [members|memberscount] [managers|managerscount] [owners|ownerscount] [totalcount] [countsonly]
        [types <CIGroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [convertcrnl] [delimiter <Character>]
        [formatjson [quotechar <Character>]]
```
By default, all groups in the account are displayed, these options allow selection of subsets of groups:
* `cimember <UserItem>` - Limit display to groups that contain `<UserItem>` as a member
* `showownedby <UserItem>` - Limit display to groups owned by `<UserItem>`
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`
* `query <String>` - Limit display to the groups that match the query

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`

By default, GAM does not make an additional API call todisplay the member restrictions from `SecuritySettings`.
* `memberrestrictions` - Make an additional API call and display the member restrictions from `SecuritySettings`

When retrieving lists of Google Groups from API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many groups to retrieve in each API call; default is 500.

By default, only the group email address is displayed, these options specify what group fields to display:
* `basic` - Only Cloud Identity Group basic fields are displayed; no additional API calls are required
* `allfields|ciallfields` - All Cloud Identity Group fields are displayed; an additional API call per group is required
* `<GroupFieldName>*` - Individual fields to display
* `fields|cifields <CIGroupFieldNameList>` - A comma separated list of fields to display

As of 2020-12-24, a separate API call is required for each group to get the following fields:
`additionalgroupkeys,createtime,dynamicgroupmetadata,parent,updatetime`

Some text fields may contain carriage returns or line feeds, displaying fields containing these characters will make processing the CSV file with a script hard; this option converts those characters to a text form.
The default value is `csv_output_convert_cr_nl` from `gam.cfg`
* `convertcrnl` - Convert carriage return to \r and line feed to \n

When lists of items are displayed, the delimiter between items defaults to the `csv_output_column_delimiter` value in gam.cfg; you can specify a different delimiter:
* `delimiter <Character>` - Use `<Character>` as the list item delimiter, `<Character>` must be a single character after processing any escape character

By default, no members, managers or owners in the group are displayed; these options modify that behavior:
* `members` - Display list of members
* `memberscount` - Display count of members but not individual members
* `managers` - Display list of managers
* `managerscount` - Display count of managers but not individual managers
* `owners` - Display list of owners
* `ownerscount` - Display count of owners but not individual owners
* `countsonly` - Change any `members`, `managers` or `owners` options to `memberscount`, `managerscount` or `ownerscount`
* `totalcount` - Display sum of counts of members, managers, owners.

By default, when displaying members from a group, all types of members (customer, group, serviceaccount, user) in the group are displayed; this option modifies that behavior:
* `types <CIGroupMemberTypeList>` - Display specified types

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, `chrome-os-device` and `cbcm-browser` are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

### Display member count examples
```
gam print cigroup select testgroup roles member,manager,owner countsonly totalcount                  
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,ManagersCount,MembersCount,OwnersCount
testgroup@domain.com,9,0,7,2

gam print cigroup select testgroup roles member,manager,owner countsonly totalcount internal
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,TotalInternalCount,InternalManagersCount,InternalMembersCount,InternalOwnersCount
testgroup@domain.com,7,7,0,5,2

gam print cigroup select testgroup roles member,manager,owner countsonly totalcount external
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,TotalExternalCount,ExternalManagersCount,ExternalMembersCount,ExternalOwnersCount
testgroup@domain.com,2,2,0,2,0

gam print cigroup select testgroup roles member,manager,owner countsonly totalcount external internal
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,TotalInternalCount,InternalManagersCount,InternalMembersCount,InternalOwnersCount,TotalExternalCount,ExternalManagersCount,ExternalMembersCount,ExternalOwnersCount
testgroup@domain.com,9,7,0,5,2,2,0,2,0
```

### Display dynamic groups
```
gam print cigroups query "'cloudidentity.googleapis.com/groups.dynamic' in labels"
```

### Display security groups
```
gam print cigroups query "'cloudidentity.googleapis.com/groups.security' in labels"
```

## Display group counts
Display the number of groups.
```
gam print cigroups
        [(cimember|showownedby <UserItem>)|(select <GroupEntity>)|(query <String>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>]
        showitemcountonly
```
Example
```
$ gam print cigroups showitemcountonly
Getting all Cloud Identity Groups, may take some time on a large Google Workspace Account...
Got 242 Cloud Identity Groups: td.current@domain.com - postmaster@domain.com
242
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print cigroups showitemcountonly)
Windows PowerShell
count = & gam print cidgroups showitemcountonly
```
