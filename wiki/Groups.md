# Groups
- [API documentation](#api-documentation)
- [Query documentation](#query-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [GUI API Group settings mapping](#gui-api-group-settings-mapping)
- [GUI API Group access type settings mapping](#gui-api-group-access-type-settings-mapping)
- [whoCanViewMembership and whoCanDiscoverGroup interactions](#whocanviewmembership-and-whocandiscovergroup-interactions)
- [Manage groups](#manage-groups)
- [Update a group's settings with JSON data](#update-a-groups-settings-with-json-data)
- [Display information about specific groups](#display-information-about-specific-groups)
- [Display information about selected groups](#display-information-about-selected-groups)
- [Display a group and its parents](#Display-a-group-and-its-parents)
- [Examples](#Examples)
- [Display group counts](#display-group-counts)

## API documentation
* [API Overview](https://support.google.com/a/answer/10427204)
* [Collaborative Inbox](https://support.google.com/a/answer/167430)
* [Directory API - Groups](https://developers.google.com/admin-sdk/directory/reference/rest/v1/groups)
* [Group Settings API](https://developers.google.com/admin-sdk/groups-settings/v1/reference/groups)
* [Cloud Identity Groups Overview](https://cloud.google.com/identity/docs/groups)
* [Cloud Identity Groups API - Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups)
* [Cloud Identity Groups](https://gsuiteupdates.googleblog.com/2020/08/new-api-cloud-identity-groups-google.html)
* [Security Groups](https://gsuiteupdates.googleblog.com/2020/09/security-groups-beta.html)
* [Name guidelines](https://support.google.com/a/answer/9193374)

## Query documentation
* [Directory API - Search Groups](https://developers.google.com/admin-sdk/directory/v1/guides/search-groups)
* [Cloud Identity API - Search Dynamic Groups](https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery)

## Definitions
See [Collections of Items](Collections-of-Items)
```
<DomainName> ::= <String>(.<String>)+
<DomainNameList> ::= "<DomainName>(,<DomainName>)*"
<DomainNameEntity> ::=
        <DomainNameList> | <FileSelector> | <CSVFileSelector>
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<EmailItem> ::= <EmailAddress>|<UniqueID>|<String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<GroupList> ::= "<GroupItem>(,<GroupItem>)*"
<GroupEntity> ::=
        <GroupList> | <FileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<GroupRole> ::= owner|manager|member
<GroupRoleList> ::= "<GroupRole>(,<GroupRole>)*"
<GroupMemberType> ::= customer|group|user
<GroupMemberTypeList> ::= "<GroupMemberType>(,<GroupMemberType>)*"
<QueryGroup> ::= <String>
        See: https://developers.google.com/admin-sdk/directory/v1/guides/search-groups
<QueryGroupList> ::= "<QueryGroup>(,<QueryGroup>)*"
<QueryDynamicGroup> ::= <String>
        See: https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery

<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<GroupSettingsAttribute> ::=
        (accesstype public|team|announcementonly|restricted)|
        (allowexternalmembers <Boolean>)|
        (allowwebposting <Boolean>)|
        (archiveonly <Boolean>)|
        (customfootertext <String>)|
        (customreplyto <EmailAddress>)|
        (defaultmessagedenynotificationtext <String>)|
        (defaultsender self|group)|
        (description <String>)|
        (enablecollaborativeinbox|collaborative <Boolean>)|
        (includeinglobaladdresslist|gal <Boolean>)|
        (includecustomfooter <Boolean>)|
        (isarchived <Boolean>)|
        (memberscanpostasthegroup <Boolean>)|
        (messagemoderationlevel moderate_all_messages|moderate_non_members|moderate_new_members|moderate_none)|
        (name <String>)|
        (primarylanguage <Language>)|
        (replyto reply_to_custom|reply_to_sender|reply_to_list|reply_to_owner|reply_to_ignore|reply_to_managers)|
        (sendmessagedenynotification <Boolean>)|
        (spammoderationlevel allow|moderate|silently_moderate|reject)|
        (whocanadd all_members_can_add|all_managers_can_add|all_owners_can_add|none_can_add)|
        (whocancontactowner anyone_can_contact|all_in_domain_can_contact|all_members_can_contact|all_managers_can_contact|all_owners_can_contact)|
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
        (whocandiscovergroup all_members_can_discover|all_in_domain_can_discover|anyone_can_discover)|
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
        groupkey|
        labels|
        name|
        parent|
        updatetime
<CIGroupFieldNameList> ::= "<CIGroupFieldName>(,<CIGroupFieldName>)*"
```
## GUI API Group settings mapping
The entries appear in the order presented on the GUI Group settings page.

| GUI setting | API setting |
|------------|------------|
| Group name | name |
| Group email | email |
| Group description | description |
| Welcome message | Not available |
| Collaborative Inbox | enableCollaborativeInbox |
| Enable shared labels for this group | Not available |
| Who can see group | whoCanDiscoverGroup |
| Who can join group | whoCanJoin |
| Not available | whoCanLeaveGroup |
| Allow external members | allowExternalMembers |
| Who can view conversations | whoCanViewGroup |
| Who can post | whoCanPostMessage |
| Who can view members | whoCanViewMembership |
| Identification required for new members | Not available |
| Who can contact group owners | whoCanContactOwner |
| Who can view member email addresses | Not available |
| Allow Email Posting | Not available |
| Allow web posting | allowWebPosting |
| Conversation history | isArchived |
| Who can reply privately to authors | Not available |
| Who can attach files | Not available |
| Who can moderate content | whoCanModerateContent |
| Who can moderate metadata | whoCanAssistContent |
| Who can post as group | membersCanPostAsTheGroup |
| Default sender | defaultSender |
| Message moderation | messageModerationLevel |
| New member restrictions | Not available |
| Spam message handling | spamModerationLevel |
| Rejected message notification | sendMessageDenyNotification |
| Include default rejected message response | defaultMessageDenyNotificationText |
| Subject prefix | Not available |
| Include the standard Groups footer | Not available |
| Include a custom footer | includeCustomFooter |
| Custom footer text | customFooterText |
| Group email language | primaryLanguage |
| Auto replies | Not available |
| Post replies to | replyTo |
| Custom address for replies | customReplyTo |
| Conversation mode | Not available |
| Who can manage members | whoCanModerateMembers |
| Who can manaage custom roles | Not available |

## GUI API Group access type settings mapping
You can apply these settings when creating/updating a group with the option:
```
accesstype public|team|announcementonly|restricted
```

```
Public
  whoCanJoin ALL_IN_DOMAIN_CAN_JOIN
  whoCanPostMessage ALL_IN_DOMAIN_CAN_POST
  whoCanViewGroup ALL_IN_DOMAIN_CAN_VIEW
  whoCanViewMembership ALL_IN_DOMAIN_CAN_VIEW

Team
  whoCanJoin CAN_REQUEST_TO_JOIN
  whoCanPostMessage ALL_IN_DOMAIN_CAN_POST
  whoCanViewGroup ALL_IN_DOMAIN_CAN_VIEW
  whoCanViewMembership ALL_IN_DOMAIN_CAN_VIEW

Announcement Only
  whoCanJoin ALL_IN_DOMAIN_CAN_JOIN
  whoCanPostMessage ALL_MANAGERS_CAN_POST
  whoCanViewGroup ALL_IN_DOMAIN_CAN_VIEW
  whoCanViewMembership ALL_MANAGERS_CAN_VIEW

Restricted
  whoCanJoin CAN_REQUEST_TO_JOIN
  whoCanPostMessage ALL_MEMBERS_CAN_POST
  whoCanViewGroup ALL_MEMBERS_CAN_VIEW
  whoCanViewMembership ALL_MEMBERS_CAN_VIEW
```

## whoCanViewMembership and whoCanDiscoverGroup interactions
Some combinations of these two settings are not allowed:
```
gam update group group@domain.com whoCanViewMembership ALL_IN_DOMAIN_CAN_VIEW whoCanDiscoverGroup ANYONE_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_OWNERS_CAN_VIEW whoCanDiscoverGroup ANYONE_CAN_DISCOVER
Group: group@domain.com, Update Failed: Failed request validation in update settings: DONT_USE_OR_ELSE_WHO_CAN_MANAGE_MEMBERS_CANNOT_BE_BROADER_THAN_WHO_CAN_VIEW_MEMBERSHIP

gam update group group@domain.com whoCanViewMembership ALL_MANAGERS_CAN_VIEW whoCanDiscoverGroup ANYONE_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_MEMBERS_CAN_VIEW whoCanDiscoverGroup ANYONE_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_IN_DOMAIN_CAN_VIEW whoCanDiscoverGroup ALL_IN_DOMAIN_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_OWNERS_CAN_VIEW whoCanDiscoverGroup ALL_IN_DOMAIN_CAN_DISCOVER
Group: group@domain.com, Update Failed: Failed request validation in update settings: DONT_USE_OR_ELSE_WHO_CAN_MANAGE_MEMBERS_CANNOT_BE_BROADER_THAN_WHO_CAN_VIEW_MEMBERSHIP

gam update group group@domain.com whoCanViewMembership ALL_MANAGERS_CAN_VIEW whoCanDiscoverGroup ALL_IN_DOMAIN_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_MEMBERS_CAN_VIEW whoCanDiscoverGroup ALL_IN_DOMAIN_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_IN_DOMAIN_CAN_VIEW whoCanDiscoverGroup ALL_MEMBERS_CAN_DISCOVER
Group: group@domain.com, Update Failed: Failed request validation in update settings: WHO_CAN_VIEW_MEMBERSHIP_CANNOT_BE_BROADER_THAN_WHO_CAN_SEE_GROUP

gam update group group@domain.com whoCanViewMembership ALL_OWNERS_CAN_VIEW whoCanDiscoverGroup ALL_MEMBERS_CAN_DISCOVER
Group: group@domain.com, Update Failed: Failed request validation in update settings: DONT_USE_OR_ELSE_WHO_CAN_MANAGE_MEMBERS_CANNOT_BE_BROADER_THAN_WHO_CAN_VIEW_MEMBERSHIP

gam update group group@domain.com whoCanViewMembership ALL_MANAGERS_CAN_VIEW whoCanDiscoverGroup ALL_MEMBERS_CAN_DISCOVER
Group: group@domain.com, Updated

gam update group group@domain.com whoCanViewMembership ALL_MEMBERS_CAN_VIEW whoCanDiscoverGroup ALL_MEMBERS_CAN_DISCOVER
Group: group@domain.com, Updated
```

## Manage groups

These commands allow you to create, update and delete groups.
```
gam create group <EmailAddress>
        [copyfrom <GroupItem>] <GroupAttribute>*
        [verifynotinvitable]
gam update group|groups <GroupEntity> [email <EmailAddress>]
        [copyfrom <GroupItem>] <GroupAttribute>*
        [makesecuritygroup|security]
        [admincreated <Boolean>]
        [verifynotinvitable]
gam delete group|groups <GroupEntity> [noactionifalias]
```
The `copyfrom <GroupItem>` allows copying of group attributes from one group to another.
The following attributes are not copied: name, description, email, admincreated, aliases, noneditablealiases.
Any `<GroupAttribute>` specified will override the copied attributes.

You can update a group to a security group with the `makesecuritygroup` option.
* Warning: A Security Group cannot be changed back to a Google Group.

When deleting and `noactionifalias` is specified, no action is performed if `<GroupEntity>` specifies an alias rather than a primary email address.

## Update a group's settings with JSON data
You can save group settings in JSON format which can simplify updating multiple settings. Suppose you have
a set of test groups that you will use to experiment with the new group settings coming in May 2019. You
want to backup the current settings so you can restore them later after your experiments.

Backup the current settings.
```
$ gam redirect csv ./groups.csv print groups query "name:test*" settings formatjson quotechar "'"
Getting all Groups that match query (query="name:test*"), may take some time on a large Google Workspace Account...
Got 4 Groups: testgroup1@domain.com - testgroup4@domain.com
Getting Group Settings for testgroup1@domain.com (1/4)
Getting Group Settings for testgroup2@domain.com (2/4)
Getting Group Settings for testgroup3@domain.com (3/4)
Getting Group Settings for testgroup4@domain.com (4/4)
```
Perform your experiments and then restore the original settings.
```
$ gam csv ./groups.csv quotechar "'" gam update group "~email" json "~JSON-settings"
Using 4 processes...
Group: testgroup1@domain.com, Updated
Group: testgroup2@domain.com, Updated
Group: testgroup3@domain.com, Updated
Group: testgroup4@domain.com, Updated
```

## Display information about specific groups
The info command displays information as an indented list of keys and values.
```
gam info group|groups <GroupEntity>
        [nousers] [quick] [noaliases] [groups]
        [basic] <GroupFieldName>* [fields <GroupFieldNameList>] [nodeprecated]
        [ciallfields|(cifields <CIGroupFieldNameList>)]
        [roles <GroupRoleList>] [members] [managers] [owners]
        [internal] [internaldomains <DomainNameList>] [external]
        [notsuspended|suspended] [notarchived|archived]
        [types <GroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [formatjson]
```
By default, all members, managers and owners in the group are displayed; these options modify that behavior:
* `members` - Display members
* `managers` - Display managers
* `owners` - Display owners
* `nousers` or `quick` - Do not display any members, managers or owners
* `roles <GroupRoleList>` - Display specified roles


By default, when displaying members from a group, all members, whether suspended or not, are included.
* `notsuspended` - Display only non-suspended members
* `suspended` - Display only suspended members
* `notarchived` - Display only non-archived members
* `archived` - Display only archived members
* `notsuspended notarchived` - Display only non-suspended and non-archived members
* `suspended archived` - Display only suspended or archived members
* `notsuspended archived` - Display only archived members
* `suspended notarchived` - Display only suspended members

By default, when displaying members from a group, all types of members (customer, group, user) in the group are displayed; this option modifies that behavior:
* `types <GroupMemberTypeList>` - Display specified types

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, are considered internal.

Members that have met the above qualifications to be displayed can be further qualifed by their email address.
* `memberemaildisplaypattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will be displayed; others will not be displayed
* `memberemailskippattern <REMatchPattern>` - Members with email addresses that match `<REMatchPattern>` will not be displayed; others will be displayed

By default, all group aliases are displayed, these options modify that behavior:
* `noaliases` or `quick` - Do not display group aliases

By default, the groups of which this group is a member are not displayed, this option enables that display
* `groups` - Display groups of which this group is a member

These options specify what group fields to display:
* `basic` - These fields `id,name,description,directMembersCount,aliases,nonEditableAliases,adminCreated` are displayed
* `<GroupFieldName>*` - Individual fields to display
* `fields <GroupFieldNameList>` - A comma separated list of fields to display
* `ciallfields` - All Cloud Identity Group fields
* `cifields <CIGroupFieldNameList>` - A comma separated list of Cloud Identity Groups fields to display
* `nodeprecated` - Do not display deprecated fields

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the output in JSON notation

## Display information about selected groups
This command displays information in CSV format.
```
gam print groups [todrive <ToDriveAttribute>*]
        [([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryGroupList>)]))|
         (group|group_ns|group_susp <GroupItem>)|
         (select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>] (matchsetting [not] <GroupAttribute>)*
        [admincreatedmatch <Boolean>]
        [maxresults <Number>]
        [allfields|([basic] [settings] <GroupFieldName>* [fields <GroupFieldNameList>])]
        [ciallfields|(cifields <CIGroupFieldNameList>)]
        [nodeprecated]
        [roles <GroupRoleList>]
        [internal] [internaldomains <DomainNameList>] [external]
        [members|memberscount] [managers|managerscount] [owners|ownerscount] [totalcount] [countsonly]
        [includederivedmembership]
        [notsuspended|suspended] [notarchived|archived]
        [types <GroupMemberTypeList>]
        [memberemaildisplaypattern|memberemailskippattern <REMatchPattern>]
        [convertcrnl] [delimiter <Character>] [sortheaders]
        [formatjson [quotechar <Character>]]
```
By default, all groups in the account are displayed, these options allow selection of subsets of groups:
* `domain|domains <DomainNameEntity>` - Limit display to groups in the domains specified by `<DomainNameEntity>`
  * You can predefine this list with the `print_agu_domains` variable in `gam.cfg`.
* `member <EmailItem>` - Limit display to groups that contain `<EmailItem>` as a member; mutually exclusive with `query <QueryGroup>`
* `showownedby <EmailItem>` - Limit display to groups that contain `<EmailItem>` as an owner; mutually exclusive with `query <QueryGroup>`
* `(query <QueryGroup>)|(queries <QueryGroupList>)` - Limit groups to those that match a query; each query is run against each domain
* `group <GroupItem>` - Limit display to the single group `<GroupItem>`
* `group_ns <GroupItem>` - Limit display to the single group `<GroupItem>`, display non-suspended members
* `group_susp <GroupItem>` - Limit display to the single group `<GroupItem>`, display suspended members
* `select <GroupEntity>` - Limit display to the groups specified in `<GroupEntity>`

When using `query <QueryGroup>` with the `name:{PREFIX}*` query, `PREFIX` must contain at least three characters.

You can identify groups with the `All users in the organization` member with:
* `query "memberKey=<CustomerID>"`
* `member id:<CustomerID>`

These options further limit the list of groups selected above:
* `emailmatchpattern <REMatchPattern>` - Limit display to groups whose email address matches `<REMatchPattern>`
* `emailmatchpattern not <REMatchPattern>` - Limit display to groups whose email address does not match `<REMatchPattern>`
* `namematchpattern <REMatchPattern>` - Limit display to groups whose name matches `<REMatchPattern>`
* `namematchpattern not <REMatchPattern>` - Limit display to groups whose name does not match `<REMatchPattern>`
* `descriptionmatchpattern <REMatchPattern>` - Limit display to groups whose description matches `<REMatchPattern>`
* `descriptionmatchpattern not <REMatchPattern>` - Limit display to groups whose description does not match `<REMatchPattern>`
* `admincreatedmatch True` - Limit display to groups created by administrators
* `admincreatedmatch False` - Limit display to groups created by users
* `matchsetting <GroupAttribute>` - Limit display to groups that have `<GroupAttribute>`
* `matchsetting not <GroupAttribute>` - Limit display to groups that do not have `<GroupAttribute>`

* You can specify multiple `matchsetting` options, all of them must match for the group to be displayed.
* You can specify multiple `matchsetting` options for the same `<GroupAttribute>`, it is a match if the group has any of the `<GroupAttribute>` values.
* You can specify multiple `matchsetting not` options for the same `<GroupAttribute>`, it is a match if the group has none of the `<GroupAttribute>` values.

When retrieving lists of Google Groups from API, how many should be retrieved in each API call.
* `maxresults <Number>` - How many groups to retrieve in each API call; default is 200.

By default, only the group email address is displayed, these options specify what group fields to display:
* `basic` - These fields `id,name,description,directMembersCount,aliases,nonEditableAliases,adminCreated` are displayed
* `allfields` - All group fields are displayed
* `settings` - All group settings fields are displayed
* `<GroupFieldName>*` - Individual fields to display
* `fields <GroupFieldNameList>` - A comma separated list of fields to display
* `ciallfields` - All Cloud Identity Group fields
* `cifields <CIGroupFieldNameList>` - A comma separated list of Cloud Identity Groups fields to display
* `nodeprecated` - Do not display deprecated fields

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
* `roles <GroupRoleList>` - Display lists of the specified roles
* `ownerscount` - Display count of owners but not individual owners
* `countsonly` - Change any `members`, `managers`, `owners` or `roles` options to `memberscount`, `managerscount` or `ownerscount`
* `totalcount` - Display sum of counts of members, managers, owners.

The `includederivedmembership` option causes the API to expand type GROUP and type CUSTOMER
members to display their constituent members while still displaying the original member.
The API produces inconsistent results, use with caution.

By default, when displaying members from a group, all members, whether suspended or not, are included.
* `notsuspended` - Display only non-suspended members
* `suspended` - Display only suspended members
* `notarchived` - Display only non-archived members
* `archived` - Display only archived members
* `notsuspended notarchived` - Display only non-suspended and non-archived members
* `suspended archived` - Display only suspended or archived members
* `notsuspended archived` - Display only archived members
* `suspended notarchived` - Display only suspended members

By default, when displaying members from a group, all types of members (customer, group, user) in the group are displayed; this option modifies that behavior:
* `types <GroupMemberTypeList>` - Display specified types

By default, when listing group members, GAM does not take the domain of the member into account.
* `internal internaldomains <DomainNameList>` - Display members whose domain is in `<DomainNameList>`
* `external internaldomains <DomainNameList>` - Display members whose domain is not in `<DomainNameList>`
* `internal external internaldomains <DomainNameList>` - Display all members, indicate their category: internal or external
* `internaldomains <DomainNameList>` - Defaults to value of `domain` in `gam.cfg`

Members without an email address, e.g. `customer`, are considered internal.

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
gam print group select testgroup roles member,manager,owner countsonly totalcount                  
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,ManagersCount,MembersCount,OwnersCount
testgroup@domain.com,9,0,7,2

gam print group select testgroup roles member,manager,owner countsonly totalcount internal
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,TotalInternalCount,InternalManagersCount,InternalMembersCount,InternalOwnersCount
testgroup@domain.com,7,7,0,5,2

gam print group select testgroup roles member,manager,owner countsonly totalcount external
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,TotalExternalCount,ExternalManagersCount,ExternalMembersCount,ExternalOwnersCount
testgroup@domain.com,2,2,0,2,0

gam print group select testgroup roles member,manager,owner countsonly totalcount external internal
Getting Cloud Identity Groups for testgroup@domain.com
Getting Members, Managers, Owners for testgroup@domain.com
Got 9 Members, Managers, Owners...
email,TotalCount,TotalInternalCount,InternalManagersCount,InternalMembersCount,InternalOwnersCount,TotalExternalCount,ExternalManagersCount,ExternalMembersCount,ExternalOwnersCount
testgroup@domain.com,9,7,0,5,2,2,0,2,0
```

## Examples
### Some simple use cases.
#### Output can be either redirected to a file on the command line using ">file.ouput", or the csv redirect gam option
#### Print a list of all your groups
```
gam print groups
```
#### Display groups with no members.
```
gam config csv_output_row_filter "directMembersCount:count=0" print groups directmemberscount
```

## Display a group and its parents
Display a group and its parents as an indented list.
```
gam show grouptree <GroupEntity>
```
Display a group and its parents in CSV format.
```
gam print grouptree <GroupEntity> [todrive <ToDriveAttribute>*]
        [showparentsaslist [<Boolean>]] [delimiter <Character>]
```
By default, the group parent emails and names are displayed in multiple indexed columns.
Use options `showparentsaslist [<Boolean>]` and `delimiter <Character>` to display
the group parent emails and names in two columns as delimited lists.

#### Examples
```
$ gam show grouptree testgroup2@domain.com
Show 1 Group Tree
testgroup2@domain.com: Test - Group 2
  testgroup1@domain.com: Test Group1
    testgroup@domain.com: Test Group Org
  testgroup@domain.net: Test Group Net

$ gam print grouptree testgroup2@domain.com
Group,Name,parents,parents.0.email,parents.0.name,parents.1.email,parents.1.name
testgroup2@domain.com,Test - Group 2,2,testgroup1@domain.com,Test Group1,testgroup@domain.com,Test Group Org
testgroup2@domain.com,Test - Group 2,1,testgroup@domain.net,Test Group Net,,

$ gam print grouptree testgroup2@domain.com showparentsaslist delimiter "|"
Group,Name,ParentsCount,Parents,ParentsName
testgroup2@domain.com,Test - Group 2,2,testgroup1@domain.com|testgroup@domain.com,Test Group1|Test Group Org
testgroup2@domain.com,Test - Group 2,1,testgroup@domain.net,Test Group Net
```
## Display group counts
Display the number of groups.
```
gam print groups
        [([domain|domains <DomainNameEntity>] ([member|showownedby <EmailItem>]|[(query <QueryGroup>)|(queries <QueryGroupList>)]))|
         (select <GroupEntity>)]
        [emailmatchpattern [not] <REMatchPattern>] [namematchpattern [not] <REMatchPattern>]
        [descriptionmatchpattern [not] <REMatchPattern>] (matchsetting [not] <GroupAttribute>)*
        [admincreatedmatch <Boolean>]
        showitemcountonly
```
Example
```
$ gam print groups showitemcountonly
Getting all Groups, may take some time on a large Google Workspace Account...
Got 200 Groups: 1aparents@domain.com - students-genderfood@domain.com
Got 238 Groups: students-worldculture@domain.com - xcarestaff@domain.com
238
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print groups showitemcountonly)
Windows PowerShell
count = & gam print groups showitemcountonly
```
