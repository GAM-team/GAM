"""GAM shared constants.

Return codes, Drive query fragments, choice maps, and other constants
shared across cmd/ modules.
"""

import re
import string

from gamlib import glcfg as GC

# Time formats
IS08601_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%:z'
RFC2822_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S %z'

# Application name
GIT_USER = 'GAM-team'
GAM = 'GAM'
GAM_PROJECT_CREATION = 'GAM Project Creation'
GAM_PROJECT_CREATION_CLIENT_ID = '297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com'

# Byte sizes
ONE_KILO_BYTES = 1024
ONE_MEGA_BYTES = ONE_KILO_BYTES * ONE_KILO_BYTES
ONE_GIGA_BYTES = ONE_KILO_BYTES * ONE_MEGA_BYTES
ONE_TERA_BYTES = ONE_KILO_BYTES * ONE_GIGA_BYTES

# Day names
DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Time constants
MAX_LOCAL_GOOGLE_TIME_OFFSET = 30

# Character sets
LOWERNUMERIC_CHARS = string.ascii_lowercase + string.digits
ALPHANUMERIC_CHARS = LOWERNUMERIC_CHARS + string.ascii_uppercase
PASSWORD_SAFE_CHARS = ALPHANUMERIC_CHARS + '!#$%&()*-./:;<=>?@[\\\\]^_{|}~'

# Google Meet
GOOGLE_MEETID_PATTERN = re.compile(r'^[a-z]{3}-[a-z]{4}-[a-z]{3}$')
GOOGLE_MEETID_FORMAT_REQUIRED = 'abc-defg-hij'
GOOGLE_TIMECHECK_LOCATION = 'admin.googleapis.com'

# Drive constants
MY_DRIVE = 'My Drive'
TEAM_DRIVE = 'Drive'
ROOT = 'root'

# Access options
ADMIN_ACCESS_OPTIONS = {'adminaccess', 'asadmin'}
OWNER_ACCESS_OPTIONS = {'owneraccess', 'asowner'}

# Choice maps
PROJECTION_CHOICE_MAP = {'basic': 'BASIC', 'full': 'FULL'}

# Google API MIME types
APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'

# Queries
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS + " and "
AND_ME_IN_OWNERS = " and " + ME_IN_OWNERS
NOT_ME_IN_OWNERS = "not " + ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS + " and "
AND_NOT_ME_IN_OWNERS = " and " + NOT_ME_IN_OWNERS
ANY_FOLDERS = "mimeType = '" + MIMETYPE_GA_FOLDER + "'"
NON_TRASHED = "trashed = false"
WITH_PARENTS = "'{0}' in parents"
ANY_NON_TRASHED_WITH_PARENTS = "trashed = false and '{0}' in parents"
ANY_NON_TRASHED_FOLDER_NAME = "mimeType = '" + MIMETYPE_GA_FOLDER + "' and name = '{0}' and trashed = false"
MY_NON_TRASHED_FOLDER_NAME = ME_IN_OWNERS_AND + ANY_NON_TRASHED_FOLDER_NAME
MY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS = ME_IN_OWNERS_AND + "mimeType = '" + MIMETYPE_GA_FOLDER + "' and name = '{0}' and trashed = false and '{1}' in parents"
ANY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS = "mimeType = '" + MIMETYPE_GA_FOLDER + "' and name = '{0}' and trashed = false and '{1}' in parents"
AND_NOT_SHORTCUT = " and mimeType != '" + MIMETYPE_GA_SHORTCUT + "'"

# Program return codes
UNKNOWN_ERROR_RC = 1
USAGE_ERROR_RC = 2
SOCKET_ERROR_RC = 3
GOOGLE_API_ERROR_RC = 4
NETWORK_ERROR_RC = 5
FILE_ERROR_RC = 6
MEMORY_ERROR_RC = 7
KEYBOARD_INTERRUPT_RC = 8
HTTP_ERROR_RC = 9
SCOPES_NOT_AUTHORIZED_RC = 10
DATA_ERROR_RC = 11
API_ACCESS_DENIED_RC = 12
CONFIG_ERROR_RC = 13
SYSTEM_ERROR_RC = 14
NO_SCOPES_FOR_API_RC = 15
CLIENT_SECRETS_JSON_REQUIRED_RC = 16
OAUTH2SERVICE_JSON_REQUIRED_RC = 16
OAUTH2_TXT_REQUIRED_RC = 16
INVALID_JSON_RC = 17
JSON_ALREADY_EXISTS_RC = 17
AUTHENTICATION_TOKEN_REFRESH_ERROR_RC = 18
HARD_ERROR_RC = 19
# Information
ENTITY_IS_A_USER_RC = 20
ENTITY_IS_A_USER_ALIAS_RC = 21
ENTITY_IS_A_GROUP_RC = 22
ENTITY_IS_A_GROUP_ALIAS_RC = 23
ENTITY_IS_AN_UNMANAGED_ACCOUNT_RC = 24
ORGUNIT_NOT_EMPTY_RC = 25
USER_SUSPENDED_RC = 26
CHECK_USER_GROUPS_ERROR_RC = 29
ORPHANS_COLLECTED_RC = 30
# Warnings/Errors
ACTION_FAILED_RC = 50
ACTION_NOT_PERFORMED_RC = 51
INVALID_ENTITY_RC = 52
BAD_REQUEST_RC = 53
ENTITY_IS_NOT_UNIQUE_RC = 54
DATA_NOT_AVALIABLE_RC = 55
ENTITY_DOES_NOT_EXIST_RC = 56
ENTITY_DUPLICATE_RC = 57
ENTITY_IS_NOT_AN_ALIAS_RC = 58
ENTITY_IS_UKNOWN_RC = 59
NO_ENTITIES_FOUND_RC = 60
INVALID_DOMAIN_RC = 61
INVALID_DOMAIN_VALUE_RC = 62
INVALID_TOKEN_RC = 63
JSON_LOADS_ERROR_RC = 64
MULTIPLE_DELETED_USERS_FOUND_RC = 65
MULTIPLE_PROJECT_FOLDERS_FOUND_RC = 65
STDOUT_STDERR_ERROR_RC = 66
INSUFFICIENT_PERMISSIONS_RC = 67
REQUEST_COMPLETED_NO_RESULTS_RC = 71
REQUEST_NOT_COMPLETED_RC = 72
SERVICE_NOT_APPLICABLE_RC = 73
TARGET_DRIVE_SPACE_ERROR_RC = 74
USER_REQUIRED_TO_CHANGE_PASSWORD_ERROR_RC = 75
USER_SUSPENDED_ERROR_RC = 76
NO_CSV_DATA_TO_UPLOAD_RC = 77
NO_SA_ACCESS_CONTEXT_MANAGER_EDITOR_ROLE_RC = 78
ACCESS_POLICY_ERROR_RC = 79
YUBIKEY_CONNECTION_ERROR_RC = 80
YUBIKEY_INVALID_KEY_TYPE_RC = 81
YUBIKEY_INVALID_SLOT_RC = 82
YUBIKEY_INVALID_PIN_RC = 83
YUBIKEY_APDU_ERROR_RC = 84
YUBIKEY_VALUE_ERROR_RC = 85
YUBIKEY_MULTIPLE_CONNECTED_RC = 86
YUBIKEY_NOT_FOUND_RC = 87

# Building address field map
BUILDING_ADDRESS_FIELD_MAP = {
  'address': 'addressLines',
  'addresslines': 'addressLines',
  'administrativearea': 'administrativeArea',
  'city': 'locality',
  'country': 'regionCode',
  'language': 'languageCode',
  'languagecode': 'languageCode',
  'locality': 'locality',
  'postalcode': 'postalCode',
  'regioncode': 'regionCode',
  'state': 'administrativeArea',
  'sublocality': 'sublocality',
  'zipcode': 'postalCode',
}

# Alias target types (moved from cmd/orgunits.py)
ALIAS_TARGET_TYPES = ['user', 'group', 'target']

# Info/display option sets (moved from cmd/groups/members.py, cmd/users/manage.py)
INFO_GROUP_OPTIONS = {'nousers', 'groups'}
INFO_USER_OPTIONS = {'noaliases', 'nobuildingnames', 'nogroups', 'nolicenses', 'nolicences', 'noschemas', 'schemas', 'userview'}
USER_SKIP_OBJECTS = {'thumbnailPhotoEtag'}
USER_TIME_OBJECTS = {'creationTime', 'deletionTime', 'lastLoginTime', 'suspensionTime', 'archivalTime', 'disabledTime'}

# License constants (moved from cmd/userop/usergroups.py)
LICENSE_PRODUCT_SKUIDS = 'productSkuIds'

# Drive file attribute keys (moved from cmd/drive/core.py)
DFA_URL = 'url'

# User fields choice map (moved from cmd/users/manage.py)
USER_FIELDS_CHOICE_MAP = {
  'address': 'addresses',
  'addresses': 'addresses',
  'admin': ['isAdmin', 'isDelegatedAdmin'],
  'agreed2terms': 'agreedToTerms',
  'agreedtoterms': 'agreedToTerms',
  'aliases': ['aliases', 'nonEditableAliases'],
  'archived': ['archived', 'archivalTime'],
  'changepassword': 'changePasswordAtNextLogin',
  'changepasswordatnextlogin': 'changePasswordAtNextLogin',
  'creationtime': 'creationTime',
  'customerid': 'customerId',
  'deletiontime': 'deletionTime',
  'displayname': 'name.displayName',
  'email': 'emails',
  'emails': 'emails',
  'employeeid': 'externalIds',
  'externalid': 'externalIds',
  'externalids': 'externalIds',
  'familyname': 'name.familyName',
  'firstname': 'name.givenName',
  'fullname': 'name.fullName',
  'gal': 'includeInGlobalAddressList',
  'gender': ['gender.type', 'gender.customGender', 'gender.addressMeAs'],
  'givenname': 'name.givenName',
  'guestaccountinfo': ['guestAccountInfo.primaryGuestEmail'],
  'id': 'id',
  'im': 'ims',
  'ims': 'ims',
  'includeinglobaladdresslist': 'includeInGlobalAddressList',
  'ipwhitelisted': 'ipWhitelisted',
  'isadmin': ['isAdmin', 'isDelegatedAdmin'],
  'isdelegatedadmin': ['isAdmin', 'isDelegatedAdmin'],
  'isenforcedin2sv': 'isEnforcedIn2Sv',
  'isenrolledin2sv': 'isEnrolledIn2Sv',
  'isguestuser': 'isGuestUser',
  'is2svenforced': 'isEnforcedIn2Sv',
  'is2svenrolled': 'isEnrolledIn2Sv',
  'ismailboxsetup': 'isMailboxSetup',
  'keyword': 'keywords',
  'keywords': 'keywords',
  'language': 'languages',
  'languages': 'languages',
  'lastlogintime': 'lastLoginTime',
  'lastname': 'name.familyName',
  'location': 'locations',
  'locations': 'locations',
  'manager': 'relations',
  'name': ['name.givenName', 'name.familyName', 'name.fullName', 'name.displayName'],
  'nicknames': ['aliases', 'nonEditableAliases'],
  'noneditablealiases': ['aliases', 'nonEditableAliases'],
  'note': 'notes',
  'notes': 'notes',
  'org': 'orgUnitPath',
  'organization': 'organizations',
  'organizations': 'organizations',
  'organisation': 'organizations',
  'organisations': 'organizations',
  'orgunit': 'orgUnitPath',
  'orgunitpath': 'orgUnitPath',
  'otheremail': 'emails',
  'otheremails': 'emails',
  'ou': 'orgUnitPath',
  'phone': 'phones',
  'phones': 'phones',
  'photo': 'thumbnailPhotoUrl',
  'photourl': 'thumbnailPhotoUrl',
  'posix': 'posixAccounts',
  'posixaccounts': 'posixAccounts',
  'primaryemail': 'primaryEmail',
  'recoveryemail': 'recoveryEmail',
  'recoveryphone': 'recoveryPhone',
  'relation': 'relations',
  'relations': 'relations',
  'ssh': 'sshPublicKeys',
  'sshkeys': 'sshPublicKeys',
  'sshpublickeys': 'sshPublicKeys',
  'suspended': ['suspended', 'suspensionReason', 'suspensionTime'],
  'thumbnailphotourl': 'thumbnailPhotoUrl',
  'username': 'primaryEmail',
  'website': 'websites',
  'websites': 'websites',
  }

# Group settings choice maps (moved from cmd/mobile.py)
GROUP_DISCOVER_CHOICES = {
  'allmemberscandiscover': 'ALL_MEMBERS_CAN_DISCOVER',
  'allindomaincandiscover': 'ALL_IN_DOMAIN_CAN_DISCOVER',
  'anyonecandiscover': 'ANYONE_CAN_DISCOVER',
  }
GROUP_ASSIST_CONTENT_CHOICES = {
  'allmembers': 'ALL_MEMBERS',
  'ownersandmanagers': 'OWNERS_AND_MANAGERS',
  'managersonly': 'MANAGERS_ONLY',
  'ownersonly': 'OWNERS_ONLY',
  'none': 'NONE',
  }
GROUP_MODERATE_CONTENT_CHOICES = {
  'allmembers': 'ALL_MEMBERS',
  'ownersandmanagers': 'OWNERS_AND_MANAGERS',
  'ownersonly': 'OWNERS_ONLY',
  'none': 'NONE',
  }
GROUP_MODERATE_MEMBERS_CHOICES = {
  'allmembers': 'ALL_MEMBERS',
  'ownersandmanagers': 'OWNERS_AND_MANAGERS',
  'ownersonly': 'OWNERS_ONLY',
  'none': 'NONE',
  }

# Group settings attribute maps (moved from cmd/mobile.py)
GROUP_DEPRECATED_ATTRIBUTES = {
  'allowgooglecommunication': ['allowGoogleCommunication', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'favoriterepliesontop': ['favoriteRepliesOnTop', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'maxmessagebytes': ['maxMessageBytes', {GC.VAR_TYPE: GC.TYPE_INTEGER, GC.VAR_LIMITS: (1024, 1048576)}],
  'messagedisplayfont': ['messageDisplayFont', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                'choices': {'defaultfont': 'DEFAULT_FONT', 'fixedwidthfont': 'FIXED_WIDTH_FONT'}}],
  'whocanaddreferences': ['whoCanAddReferences', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarkfavoritereplyonowntopic': ['whoCanMarkFavoriteReplyOnOwnTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  }
GROUP_DISCOVER_ATTRIBUTES = {
  'showingroupdirectory': ['showInGroupDirectory', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  }
GROUP_ASSIST_CONTENT_ATTRIBUTES = {
  'whocanassigntopics': ['whoCanAssignTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanenterfreeformtags': ['whoCanEnterFreeFormTags', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanhideabuse': ['whoCanHideAbuse', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmaketopicssticky': ['whoCanMakeTopicsSticky', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarkduplicate': ['whoCanMarkDuplicate', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarkfavoritereplyonanytopic': ['whoCanMarkFavoriteReplyOnAnyTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmarknoresponseneeded': ['whoCanMarkNoResponseNeeded', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmodifytagsandcategories': ['whoCanModifyTagsAndCategories', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocantaketopics': ['whoCanTakeTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanunassigntopic': ['whoCanUnassignTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanunmarkfavoritereplyonanytopic': ['whoCanUnmarkFavoriteReplyOnAnyTopic', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  }
GROUP_MODERATE_CONTENT_ATTRIBUTES = {
  'whocanapprovemessages': ['whoCanApproveMessages', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocandeleteanypost': ['whoCanDeleteAnyPost', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocandeletetopics': ['whoCanDeleteTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanlocktopics': ['whoCanLockTopics', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanmovetopicsin': ['whoCanMoveTopicsIn', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanmovetopicsout': ['whoCanMoveTopicsOut', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanpostannouncements': ['whoCanPostAnnouncements', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  }
GROUP_MODERATE_MEMBERS_ATTRIBUTES = {
  'whocanadd': ['whoCanAdd', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                              'choices': {'allmanagerscanadd': 'ALL_MANAGERS_CAN_ADD', 'allownerscanadd': 'ALL_OWNERS_CAN_ADD',
                                          'allmemberscanadd': 'ALL_MEMBERS_CAN_ADD', 'nonecanadd': 'NONE_CAN_ADD'}}],
  'whocanapprovemembers': ['whoCanApproveMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                    'choices': {'allownerscanapprove': 'ALL_OWNERS_CAN_APPROVE', 'allmanagerscanapprove': 'ALL_MANAGERS_CAN_APPROVE',
                                                                'allmemberscanapprove': 'ALL_MEMBERS_CAN_APPROVE', 'nonecanapprove': 'NONE_CAN_APPROVE'}}],
  'whocanbanusers': ['whoCanBanUsers', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_MEMBERS_CHOICES}],
  'whocaninvite': ['whoCanInvite', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                    'choices': {'allmemberscaninvite': 'ALL_MEMBERS_CAN_INVITE', 'allmanagerscaninvite': 'ALL_MANAGERS_CAN_INVITE',
                                                'allownerscaninvite': 'ALL_OWNERS_CAN_INVITE', 'nonecaninvite': 'NONE_CAN_INVITE'}}],
  'whocanmodifymembers': ['whoCanModifyMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_MEMBERS_CHOICES}],
  }
GROUP_BASIC_ATTRIBUTES = {
  'description': ['description', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'name': ['name', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'displayname': ['name', {GC.VAR_TYPE: GC.TYPE_STRING}],
  }
GROUP_SETTINGS_ATTRIBUTES = {
  'allowexternalmembers': ['allowExternalMembers', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'allowwebposting': ['allowWebPosting', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'archiveonly': ['archiveOnly', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'customfootertext': ['customFooterText', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'customreplyto': ['customReplyTo', {GC.VAR_TYPE: GC.TYPE_EMAIL_OPTIONAL}],
  'customrolesenabledforsettingstobemerged': ['customRolesEnabledForSettingsToBeMerged', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'defaultmessagedenynotificationtext': ['defaultMessageDenyNotificationText', {GC.VAR_TYPE: GC.TYPE_STRING}],
  'defaultsender': ['defaultSender', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                      'choices': {'self': 'DEFAULT_SELF', 'defaultself': 'DEFAULT_SELF', 'group': 'GROUP'}}],
  'enablecollaborativeinbox': ['enableCollaborativeInbox', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'includecustomfooter': ['includeCustomFooter', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'includeinglobaladdresslist': ['includeInGlobalAddressList', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'isarchived': ['isArchived', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'memberscanpostasthegroup': ['membersCanPostAsTheGroup', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'messagemoderationlevel': ['messageModerationLevel', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                        'choices': {'moderateallmessages': 'MODERATE_ALL_MESSAGES', 'moderatenonmembers': 'MODERATE_NON_MEMBERS',
                                                                    'moderatenewmembers': 'MODERATE_NEW_MEMBERS', 'moderatenone': 'MODERATE_NONE'}}],
  'primarylanguage': ['primaryLanguage', {GC.VAR_TYPE: GC.TYPE_LANGUAGE}],
  'replyto': ['replyTo', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                          'choices': {'replytocustom': 'REPLY_TO_CUSTOM', 'replytosender': 'REPLY_TO_SENDER', 'replytolist': 'REPLY_TO_LIST',
                                      'replytoowner': 'REPLY_TO_OWNER', 'replytoignore': 'REPLY_TO_IGNORE', 'replytomanagers': 'REPLY_TO_MANAGERS'}}],
  'sendmessagedenynotification': ['sendMessageDenyNotification', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'spammoderationlevel': ['spamModerationLevel', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                  'choices': {'allow': 'ALLOW', 'moderate': 'MODERATE', 'silentlymoderate': 'SILENTLY_MODERATE', 'reject': 'REJECT'}}],
  'whocanaddexternalmembers': ['whoCanAddExternalMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                            'choices': {'onlyadminscanaddexternalmembers': 'ONLY_ADMINS_CAN_ADD_EXTERNAL_MEMBERS',
                                                                        'enduserscanaddexternalmembers': 'END_USERS_CAN_ADD_EXTERNAL_MEMBERS'}}],
  'whocancontactowner': ['whoCanContactOwner', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                'choices': {'anyonecancontact': 'ANYONE_CAN_CONTACT', 'allindomaincancontact': 'ALL_IN_DOMAIN_CAN_CONTACT',
                                                            'allmemberscancontact': 'ALL_MEMBERS_CAN_CONTACT', 'allmanagerscancontact': 'ALL_MANAGERS_CAN_CONTACT',
                                                            'allownerscancontact': 'ALL_OWNERS_CAN_CONTACT'}}],
  'whocanjoin': ['whoCanJoin', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                'choices': {'anyonecanjoin': 'ANYONE_CAN_JOIN', 'allindomaincanjoin': 'ALL_IN_DOMAIN_CAN_JOIN',
                                            'invitedcanjoin': 'INVITED_CAN_JOIN', 'canrequesttojoin': 'CAN_REQUEST_TO_JOIN'}}],
  'whocanleavegroup': ['whoCanLeaveGroup', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                            'choices': {'allmanagerscanleave': 'ALL_MANAGERS_CAN_LEAVE', 'allownerscanleave': 'ALL_OWNERS_CAN_LEAVE',
                                                        'allmemberscanleave': 'ALL_MEMBERS_CAN_LEAVE', 'nonecanleave': 'NONE_CAN_LEAVE'}}],
  'whocanpostmessage': ['whoCanPostMessage', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                              'choices': {'nonecanpost': 'NONE_CAN_POST', 'allmanagerscanpost': 'ALL_MANAGERS_CAN_POST',
                                                          'allmemberscanpost': 'ALL_MEMBERS_CAN_POST', 'allownerscanpost': 'ALL_OWNERS_CAN_POST',
                                                          'allindomaincanpost': 'ALL_IN_DOMAIN_CAN_POST', 'anyonecanpost': 'ANYONE_CAN_POST'}}],
  'whocanviewgroup': ['whoCanViewGroup', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                          'choices': {'anyonecanview': 'ANYONE_CAN_VIEW', 'allindomaincanview': 'ALL_IN_DOMAIN_CAN_VIEW',
                                                      'allmemberscanview': 'ALL_MEMBERS_CAN_VIEW', 'allmanagerscanview': 'ALL_MANAGERS_CAN_VIEW',
                                                      'allownerscanview': 'ALL_OWNERS_CAN_VIEW'}}],
  'whocanviewmembership': ['whoCanViewMembership', {GC.VAR_TYPE: GC.TYPE_CHOICE,
                                                    'choices': {'allindomaincanview': 'ALL_IN_DOMAIN_CAN_VIEW', 'allmemberscanview': 'ALL_MEMBERS_CAN_VIEW',
                                                                'allmanagerscanview': 'ALL_MANAGERS_CAN_VIEW', 'allownerscanview': 'ALL_OWNERS_CAN_VIEW'}}],
  }
GROUP_ALIAS_ATTRIBUTES = {
  'collaborative': ['enableCollaborativeInbox', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  'gal': ['includeInGlobalAddressList', {GC.VAR_TYPE: GC.TYPE_BOOLEAN}],
  }
GROUP_MERGED_ATTRIBUTES = {
  'whocandiscovergroup': ['whoCanDiscoverGroup', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_DISCOVER_CHOICES}],
  'whocanassistcontent': ['whoCanAssistContent', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_ASSIST_CONTENT_CHOICES}],
  'whocanmoderatecontent': ['whoCanModerateContent', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_CONTENT_CHOICES}],
  'whocanmoderatemembers': ['whoCanModerateMembers', {GC.VAR_TYPE: GC.TYPE_CHOICE, 'choices': GROUP_MODERATE_MEMBERS_CHOICES}],
  }
GROUP_MERGED_ATTRIBUTES_PRINT_ORDER = ['whoCanDiscoverGroup', 'whoCanAssistContent', 'whoCanModerateContent', 'whoCanModerateMembers']
GROUP_MERGED_TO_COMPONENT_MAP = {
  'whoCanDiscoverGroup': GROUP_DISCOVER_ATTRIBUTES,
  'whoCanAssistContent': GROUP_ASSIST_CONTENT_ATTRIBUTES,
  'whoCanModerateContent': GROUP_MODERATE_CONTENT_ATTRIBUTES,
  'whoCanModerateMembers': GROUP_MODERATE_MEMBERS_ATTRIBUTES,
  }
GROUP_ATTRIBUTES_SET = set(list(GROUP_BASIC_ATTRIBUTES)+list(GROUP_SETTINGS_ATTRIBUTES)+list(GROUP_ALIAS_ATTRIBUTES)+
                           list(GROUP_ASSIST_CONTENT_ATTRIBUTES)+list(GROUP_MODERATE_CONTENT_ATTRIBUTES)+list(GROUP_MODERATE_MEMBERS_ATTRIBUTES)+
                           list(GROUP_MERGED_ATTRIBUTES)+list(GROUP_DEPRECATED_ATTRIBUTES))
GROUP_FIELDS_WITH_CRS_NLS = {'customFooterText', 'defaultMessageDenyNotificationText', 'description'}
