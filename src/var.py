import os
import sys
import platform
import re

gam_author = u'Jay Lee <jay0lee@gmail.com>'
gam_version = u'4.40'
gam_license = u'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

GAM_URL = u'https://git.io/gam'
GAM_INFO = u'GAM {0} - {1} / {2} / Python {3}.{4}.{5} {6} / {7} {8} /'.format(gam_version, GAM_URL,
                                                                              gam_author,
                                                                              sys.version_info[0], sys.version_info[1],
                                                                              sys.version_info[2], sys.version_info[3],
                                                                              platform.platform(), platform.machine())

GAM_RELEASES = u'https://github.com/jay0lee/GAM/releases'
GAM_WIKI = u'https://github.com/jay0lee/GAM/wiki'
GAM_ALL_RELEASES = u'https://api.github.com/repos/jay0lee/GAM/releases'
GAM_LATEST_RELEASE = GAM_ALL_RELEASES+u'/latest'
GAM_PROJECT_APIS = u'https://raw.githubusercontent.com/jay0lee/GAM/master/src/project-apis.txt'

TRUE = u'true'
FALSE = u'false'
true_values = [u'on', u'yes', u'enabled', u'true', u'1']
false_values = [u'off', u'no', u'disabled', u'false', u'0']
usergroup_types = [u'user', u'users', u'group', u'ou', u'org',
                   u'ou_and_children', u'ou_and_child', u'query',
                   u'license', u'licenses', u'licence', u'licences', u'file', u'csv', u'csvfile', u'all',
                   u'cros']
ERROR = u'ERROR'
ERROR_PREFIX = ERROR+u': '
WARNING = u'WARNING'
WARNING_PREFIX = WARNING+u': '
DEFAULT_CHARSET = [u'mbcs', u'utf-8'][os.name != u'nt']
ONE_KILO_BYTES = 1000
ONE_MEGA_BYTES = 1000000
ONE_GIGA_BYTES = 1000000000
FN_CLIENT_SECRETS_JSON = u'client_secrets.json'
FN_EXTRA_ARGS_TXT = u'extra-args.txt'
FN_LAST_UPDATE_CHECK_TXT = u'lastupdatecheck.txt'
FN_OAUTH2SERVICE_JSON = u'oauth2service.json'
FN_OAUTH2_TXT = u'oauth2.txt'
MY_CUSTOMER = u'my_customer'
SKUS = {
  u'Google-Apps': {
    u'product': u'Google-Apps', u'aliases': [u'standard', u'free'], u'displayName': u'G Suite Free/Standard'},
  u'Google-Apps-For-Business': {
    u'product': u'Google-Apps', u'aliases': [u'gafb', u'gafw', u'basic', u'gsuitebasic'], u'displayName': u'G Suite Basic'},
  u'Google-Apps-For-Government': {
    u'product': u'Google-Apps', u'aliases': [u'gafg', u'gsuitegovernment', u'gsuitegov'], u'displayName': u'G Suite Government'},
  u'Google-Apps-For-Postini': {
    u'product': u'Google-Apps', u'aliases': [u'gams', u'postini', u'gsuitegams', u'gsuitepostini', u'gsuitemessagesecurity'], u'displayName': u'G Suite Message Security'},
  u'Google-Apps-Lite': {
    u'product': u'Google-Apps', u'aliases': [u'gal', u'lite', u'gsuitelite'], u'displayName': u'G Suite Lite'},
  u'Google-Apps-Unlimited': {
    u'product': u'Google-Apps', u'aliases': [u'gau', u'unlimited', u'gsuitebusiness'], u'displayName': u'G Suite Business'},
  u'1010020020': {
    u'product': u'Google-Apps', u'aliases': [u'gae', u'enterprise', u'gsuiteenterprise'], u'displayName': u'G Suite Enterprise'},
  u'Google-Drive-storage-20GB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive20gb', u'20gb', u'googledrivestorage20gb'], u'displayName': u'Google Drive Storage 20GB'},
  u'Google-Drive-storage-50GB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive50gb', u'50gb', u'googledrivestorage50gb'], u'displayName': u'Google Drive Storage 50GB'},
  u'Google-Drive-storage-200GB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive200gb', u'200gb', u'googledrivestorage200gb'], u'displayName': u'Google Drive Storage 200GB'},
  u'Google-Drive-storage-400GB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive400gb', u'400gb', u'googledrivestorage400gb'], u'displayName': u'Google Drive Storage 400GB'},
  u'Google-Drive-storage-1TB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive1tb', u'1tb', u'googledrivestorage1tb'], u'displayName': u'Google Drive Storage 1TB'},
  u'Google-Drive-storage-2TB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive2tb', u'2tb', u'googledrivestorage2tb'], u'displayName': u'Google Drive Storage 2TB'},
  u'Google-Drive-storage-4TB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive4tb', u'4tb', u'googledrivestorage4tb'], u'displayName': u'Google Drive Storage 4TB'},
  u'Google-Drive-storage-8TB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive8tb', u'8tb', u'googledrivestorage8tb'], u'displayName': u'Google Drive Storage 8TB'},
  u'Google-Drive-storage-16TB': {
    u'product': u'Google-Drive-storage', u'aliases': [u'drive16tb', u'16tb', u'googledrivestorage16tb'], u'displayName': u'Google Drive Storage 16TB'},
  u'Google-Vault': {
    u'product': u'Google-Vault', u'aliases': [u'vault', u'googlevault'], u'displayName': u'Google Vault'},
  u'Google-Vault-Former-Employee': {
    u'product': u'Google-Vault', u'aliases': [u'vfe', u'googlevaultformeremployee'], u'displayName': u'Google Vault Former Employee'},
  u'Google-Coordinate': {
    u'product': u'Google-Coordinate', u'aliases': [u'coordinate', u'googlecoordinate'], u'displayName': u'Google Coordinate'},
  u'Google-Chrome-Device-Management': {
    u'product': u'Google-Chrome-Device-Management', u'aliases': [u'chrome', u'cdm', u'googlechromedevicemanagement'], u'displayName': u'Google Chrome Device Management'}
  }

API_VER_MAPPING = {
  u'appsactivity': u'v1',
  u'calendar': u'v3',
  u'classroom': u'v1',
  u'cloudprint': u'v2',
  u'datatransfer': u'datatransfer_v1',
  u'directory': u'directory_v1',
  u'drive': u'v2',
  u'drive3': u'v3',
  u'email-settings': u'v2',
  u'gmail': u'v1',
  u'groupssettings': u'v1',
  u'licensing': u'v1',
  u'oauth2': u'v2',
  u'plus': u'v1',
  u'pubsub': u'v1',
  u'reports': u'reports_v1',
  u'reseller': u'v1',
  u'siteVerification': u'v1',
  u'urlshortener': u'v1',
  u'vault': u'v1',
  }

API_SCOPE_MAPPING = {
  u'appsactivity': [u'https://www.googleapis.com/auth/activity',
                    u'https://www.googleapis.com/auth/drive'],
  u'calendar': [u'https://www.googleapis.com/auth/calendar',],
  u'drive': [u'https://www.googleapis.com/auth/drive',],
  u'drive3': [u'https://www.googleapis.com/auth/drive',],
  u'gmail': [u'https://mail.google.com/',
             u'https://www.googleapis.com/auth/gmail.settings.basic',
             u'https://www.googleapis.com/auth/gmail.settings.sharing',],
  u'plus': [u'https://www.googleapis.com/auth/plus.me',],
}

ADDRESS_FIELDS_PRINT_ORDER = [
  u'contactName', u'organizationName',
  u'addressLine1', u'addressLine2', u'addressLine3',
  u'locality', u'region', u'postalCode', u'countryCode',
  ]

ADDRESS_FIELDS_ARGUMENT_MAP = {
  u'contact': u'contactName', u'contactname': u'contactName',
  u'name': u'organizationName', u'organizationname': u'organizationName',
  u'address': u'addressLine1', u'address1': u'addressLine1', u'addressline1': u'addressLine1',
  u'address2': u'addressLine2', u'addressline2': u'addressLine2',
  u'address3': u'addressLine3', u'addressline3': u'addressLine3',
  u'city': u'locality', u'locality': u'locality',
  u'state': u'region', u'region': u'region',
  u'zipcode': u'postalCode', u'postal': u'postalCode', u'postalcode': u'postalCode',
  u'country': u'countryCode', u'countrycode': u'countryCode',
  }

SERVICE_NAME_TO_ID_MAP = {
  u'Drive and Docs': u'55656082996',
  u'Google+': u'553547912911',
  u'Calendar': u'435070579839'
  }

SERVICE_NAME_CHOICES_MAP = {
  u'drive': u'Drive and Docs',
  u'drive and docs': u'Drive and Docs',
  u'googledrive': u'Drive and Docs',
  u'gdrive': u'Drive and Docs',
  u'calendar': u'Calendar',
  }

PRINTJOB_ASCENDINGORDER_MAP = {
  u'createtime': u'CREATE_TIME',
  u'status': u'STATUS',
  u'title': u'TITLE',
  }
PRINTJOB_DESCENDINGORDER_MAP = {
  u'CREATE_TIME': u'CREATE_TIME_DESC',
  u'STATUS':  u'STATUS_DESC',
  u'TITLE': u'TITLE_DESC',
  }

PRINTJOBS_DEFAULT_JOB_LIMIT = 0
PRINTJOBS_DEFAULT_MAX_RESULTS = 100

CALENDAR_REMINDER_METHODS = [u'email', u'sms', u'popup',]
CALENDAR_NOTIFICATION_METHODS = [u'email', u'sms',]
CALENDAR_NOTIFICATION_TYPES_MAP = {
  u'eventcreation': u'eventCreation',
  u'eventchange': u'eventChange',
  u'eventcancellation': u'eventCancellation',
  u'eventresponse': u'eventResponse',
  u'agenda': u'agenda',
  }

DRIVEFILE_FIELDS_CHOICES_MAP = {
  u'alternatelink': u'alternateLink',
  u'appdatacontents': u'appDataContents',
  u'cancomment': u'canComment',
  u'canreadrevisions': u'canReadRevisions',
  u'copyable': u'copyable',
  u'createddate': u'createdDate',
  u'createdtime': u'createdDate',
  u'description': u'description',
  u'editable': u'editable',
  u'explicitlytrashed': u'explicitlyTrashed',
  u'fileextension': u'fileExtension',
  u'filesize': u'fileSize',
  u'foldercolorrgb': u'folderColorRgb',
  u'fullfileextension': u'fullFileExtension',
  u'headrevisionid': u'headRevisionId',
  u'iconlink': u'iconLink',
  u'id': u'id',
  u'lastmodifyinguser': u'lastModifyingUser',
  u'lastmodifyingusername': u'lastModifyingUserName',
  u'lastviewedbyme': u'lastViewedByMeDate',
  u'lastviewedbymedate': u'lastViewedByMeDate',
  u'lastviewedbymetime': u'lastViewedByMeDate',
  u'lastviewedbyuser': u'lastViewedByMeDate',
  u'md5': u'md5Checksum',
  u'md5checksum': u'md5Checksum',
  u'md5sum': u'md5Checksum',
  u'mime': u'mimeType',
  u'mimetype': u'mimeType',
  u'modifiedbyme': u'modifiedByMeDate',
  u'modifiedbymedate': u'modifiedByMeDate',
  u'modifiedbymetime': u'modifiedByMeDate',
  u'modifiedbyuser': u'modifiedByMeDate',
  u'modifieddate': u'modifiedDate',
  u'modifiedtime': u'modifiedDate',
  u'name': u'title',
  u'originalfilename': u'originalFilename',
  u'ownedbyme': u'ownedByMe',
  u'ownernames': u'ownerNames',
  u'owners': u'owners',
  u'parents': u'parents',
  u'permissions': u'permissions',
  u'quotabytesused': u'quotaBytesUsed',
  u'quotaused': u'quotaBytesUsed',
  u'shareable': u'shareable',
  u'shared': u'shared',
  u'sharedwithmedate': u'sharedWithMeDate',
  u'sharedwithmetime': u'sharedWithMeDate',
  u'sharinguser': u'sharingUser',
  u'spaces': u'spaces',
  u'thumbnaillink': u'thumbnailLink',
  u'title': u'title',
  u'userpermission': u'userPermission',
  u'version': u'version',
  u'viewedbyme': u'labels(viewed)',
  u'viewedbymedate': u'lastViewedByMeDate',
  u'viewedbymetime': u'lastViewedByMeDate',
  u'viewerscancopycontent': u'labels(restricted)',
  u'webcontentlink': u'webContentLink',
  u'webviewlink': u'webViewLink',
  u'writerscanshare': u'writersCanShare',
  }

DRIVEFILE_LABEL_CHOICES_MAP = {
  u'restricted': u'restricted',
  u'restrict': u'restricted',
  u'starred': u'starred',
  u'star': u'starred',
  u'trashed': u'trashed',
  u'trash': u'trashed',
  u'viewed': u'viewed',
  u'view': u'viewed',
}

DRIVEFILE_ORDERBY_CHOICES_MAP = {
  u'createddate': u'createdDate',
  u'folder': u'folder',
  u'lastviewedbyme': u'lastViewedByMeDate',
  u'lastviewedbymedate': u'lastViewedByMeDate',
  u'lastviewedbyuser': u'lastViewedByMeDate',
  u'modifiedbyme': u'modifiedByMeDate',
  u'modifiedbymedate': u'modifiedByMeDate',
  u'modifiedbyuser': u'modifiedByMeDate',
  u'modifieddate': u'modifiedDate',
  u'name': u'title',
  u'quotabytesused': u'quotaBytesUsed',
  u'quotaused': u'quotaBytesUsed',
  u'recency': u'recency',
  u'sharedwithmedate': u'sharedWithMeDate',
  u'starred': u'starred',
  u'title': u'title',
  u'viewedbymedate': u'lastViewedByMeDate',
  }

DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP = {
  u'delete': u'purging',
  u'trash': u'trashing',
  u'untrash': u'untrashing',
  }

DRIVEFILE_LABEL_CHOICES_MAP = {
  u'restricted': u'restricted',
  u'restrict': u'restricted',
  u'starred': u'starred',
  u'star': u'starred',
  u'trashed': u'trashed',
  u'trash': u'trashed',
  u'viewed': u'viewed',
  u'view': u'viewed',
  }

APPLICATION_VND_GOOGLE_APPS = u'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = APPLICATION_VND_GOOGLE_APPS+u'document'
MIMETYPE_GA_DRAWING = APPLICATION_VND_GOOGLE_APPS+u'drawing'
MIMETYPE_GA_FOLDER = APPLICATION_VND_GOOGLE_APPS+u'folder'
MIMETYPE_GA_FORM = APPLICATION_VND_GOOGLE_APPS+u'form'
MIMETYPE_GA_FUSIONTABLE = APPLICATION_VND_GOOGLE_APPS+u'fusiontable'
MIMETYPE_GA_MAP = APPLICATION_VND_GOOGLE_APPS+u'map'
MIMETYPE_GA_PRESENTATION = APPLICATION_VND_GOOGLE_APPS+u'presentation'
MIMETYPE_GA_SCRIPT = APPLICATION_VND_GOOGLE_APPS+u'script'
MIMETYPE_GA_SITES = APPLICATION_VND_GOOGLE_APPS+u'sites'
MIMETYPE_GA_SPREADSHEET = APPLICATION_VND_GOOGLE_APPS+u'spreadsheet'

MIMETYPE_CHOICES_MAP = {
  u'gdoc': MIMETYPE_GA_DOCUMENT,
  u'gdocument': MIMETYPE_GA_DOCUMENT,
  u'gdrawing': MIMETYPE_GA_DRAWING,
  u'gfolder': MIMETYPE_GA_FOLDER,
  u'gdirectory': MIMETYPE_GA_FOLDER,
  u'gform': MIMETYPE_GA_FORM,
  u'gfusion': MIMETYPE_GA_FUSIONTABLE,
  u'gpresentation': MIMETYPE_GA_PRESENTATION,
  u'gscript': MIMETYPE_GA_SCRIPT,
  u'gsite': MIMETYPE_GA_SITES,
  u'gsheet': MIMETYPE_GA_SPREADSHEET,
  u'gspreadsheet': MIMETYPE_GA_SPREADSHEET,
  }

DFA_CONVERT = u'convert'
DFA_LOCALFILEPATH = u'localFilepath'
DFA_LOCALFILENAME = u'localFilename'
DFA_LOCALMIMETYPE = u'localMimeType'
DFA_OCR = u'ocr'
DFA_OCRLANGUAGE = u'ocrLanguage'
DFA_PARENTQUERY = u'parentQuery'

DOCUMENT_FORMATS_MAP = {
  u'csv': [{u'mime': u'text/csv', u'ext': u'.csv'}],
  u'html': [{u'mime': u'text/html', u'ext': u'.html'}],
  u'txt': [{u'mime': u'text/plain', u'ext': u'.txt'}],
  u'tsv': [{u'mime': u'text/tsv', u'ext': u'.tsv'}],
  u'jpeg': [{u'mime': u'image/jpeg', u'ext': u'.jpeg'}],
  u'jpg': [{u'mime': u'image/jpeg', u'ext': u'.jpg'}],
  u'png': [{u'mime': u'image/png', u'ext': u'.png'}],
  u'svg': [{u'mime': u'image/svg+xml', u'ext': u'.svg'}],
  u'pdf': [{u'mime': u'application/pdf', u'ext': u'.pdf'}],
  u'rtf': [{u'mime': u'application/rtf', u'ext': u'.rtf'}],
  u'zip': [{u'mime': u'application/zip', u'ext': u'.zip'}],
  u'pptx': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'}],
  u'xlsx': [{u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'}],
  u'docx': [{u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'ms': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'},
          {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'},
          {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'microsoft': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'micro$oft': [{u'mime': u'application/vnd.openxmlformats-officedocument.presentationml.presentation', u'ext': u'.pptx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', u'ext': u'.xlsx'},
                 {u'mime': u'application/vnd.openxmlformats-officedocument.wordprocessingml.document', u'ext': u'.docx'}],
  u'odt': [{u'mime': u'application/vnd.oasis.opendocument.text', u'ext': u'.odt'}],
  u'ods': [{u'mime': u'application/x-vnd.oasis.opendocument.spreadsheet', u'ext': u'.ods'}],
  u'openoffice': [{u'mime': u'application/vnd.oasis.opendocument.text', u'ext': u'.odt'},
                  {u'mime': u'application/x-vnd.oasis.opendocument.spreadsheet', u'ext': u'.ods'}],
  }

EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP = {
  u'ARCHIVE': u'archive',
  u'DELETE': u'trash',
  u'KEEP': u'leaveInInBox',
  u'MARK_READ': u'markRead',
  u'archive': u'ARCHIVE',
  u'trash': u'DELETE',
  u'leaveInInbox': u'KEEP',
  u'markRead': u'MARK_READ',
  }

EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP = {
  u'archive': u'archive',
  u'deleteforever': u'deleteForever',
  u'trash': u'trash',
  }

EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES = [u'0', u'1000', u'2000', u'5000', u'10000']

EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP = {
  u'allmail': u'allMail',
  u'fromnowon': u'fromNowOn',
  u'mailfromnowon': u'fromNowOn',
  u'newmail': u'fromNowOn',
  }

EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP = {
  u'archive': u'archive',
  u'delete': u'trash',
  u'keep': u'leaveInInbox',
  u'leaveininbox': u'leaveInInbox',
  u'markread': u'markRead',
  u'trash': u'trash',
  }

RT_PATTERN = re.compile(r'(?s){RT}.*?{(.+?)}.*?{/RT}')
RT_OPEN_PATTERN = re.compile(r'{RT}')
RT_CLOSE_PATTERN = re.compile(r'{/RT}')
RT_STRIP_PATTERN = re.compile(r'(?s){RT}.*?{/RT}')
RT_TAG_REPLACE_PATTERN = re.compile(r'{(.*?)}')

FILTER_ADD_LABEL_TO_ARGUMENT_MAP = {
  u'IMPORTANT': u'important',
  u'STARRED': u'star',
  u'TRASH': u'trash',
  }

FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP = {
  u'IMPORTANT': u'notimportant',
  u'UNREAD': u'markread',
  u'INBOX': u'archive',
  u'SPAM': u'neverspam',
  }

FILTER_CRITERIA_CHOICES_MAP = {
  u'excludechats': u'excludeChats',
  u'from': u'from',
  u'hasattachment': u'hasAttachment',
  u'haswords': u'query',
  u'musthaveattachment': u'hasAttachment',
  u'negatedquery': u'negatedQuery',
  u'nowords': u'negatedQuery',
  u'query': u'query',
  u'size': u'size',
  u'subject': u'subject',
  u'to': u'to',
  }
FILTER_ACTION_CHOICES = [
  u'archive', u'forward', u'important', u'label',
  u'markread', u'neverspam', u'notimportant', u'star', u'trash',
  ]

VAULT_MATTER_ACTIONS = [
  u'reopen',
  u'undelete',
  u'close',
  u'delete',
  ]

CROS_ARGUMENT_TO_PROPERTY_MAP = {
  u'activetimeranges': [u'activeTimeRanges.activeTime', u'activeTimeRanges.date'],
  u'annotatedassetid': [u'annotatedAssetId',],
  u'annotatedlocation': [u'annotatedLocation',],
  u'annotateduser': [u'annotatedUser',],
  u'asset': [u'annotatedAssetId',],
  u'assetid': [u'annotatedAssetId',],
  u'bootmode': [u'bootMode',],
  u'devicefiles': [u'deviceFiles',],
  u'deviceid': [u'deviceId',],
  u'ethernetmacaddress': [u'ethernetMacAddress',],
  u'firmwareversion': [u'firmwareVersion',],
  u'lastenrollmenttime': [u'lastEnrollmentTime',],
  u'lastsync': [u'lastSync',],
  u'location': [u'annotatedLocation',],
  u'macaddress': [u'macAddress',],
  u'meid': [u'meid',],
  u'model': [u'model',],
  u'notes': [u'notes',],
  u'ordernumber': [u'orderNumber',],
  u'org': [u'orgUnitPath',],
  u'orgunitpath': [u'orgUnitPath',],
  u'osversion': [u'osVersion',],
  u'ou': [u'orgUnitPath',],
  u'platformversion': [u'platformVersion',],
  u'recentusers': [u'recentUsers.email', u'recentUsers.type'],
  u'serialnumber': [u'serialNumber',],
  u'status': [u'status',],
  u'supportenddate': [u'supportEndDate',],
  u'tag': [u'annotatedAssetId',],
  u'timeranges': [u'activeTimeRanges.activeTime', u'activeTimeRanges.date'],
  u'times': [u'activeTimeRanges.activeTime', u'activeTimeRanges.date'],
  u'tpmversioninfo': [u'tpmVersionInfo',],
  u'user': [u'annotatedUser',],
  u'users': [u'recentUsers.email', u'recentUsers.type'],
  u'willautorenew': [u'willAutoRenew',],
  }

CROS_BASIC_FIELDS_LIST = [u'deviceId', u'annotatedAssetId', u'annotatedLocation', u'annotatedUser', u'lastSync', u'notes', u'serialNumber', u'status']

CROS_SCALAR_PROPERTY_PRINT_ORDER = [
  u'orgUnitPath',
  u'annotatedAssetId',
  u'annotatedLocation',
  u'annotatedUser',
  u'lastSync',
  u'notes',
  u'serialNumber',
  u'status',
  u'model',
  u'firmwareVersion',
  u'platformVersion',
  u'osVersion',
  u'bootMode',
  u'meid',
  u'ethernetMacAddress',
  u'macAddress',
  u'lastEnrollmentTime',
  u'orderNumber',
  u'supportEndDate',
  u'tpmVersionInfo',
  u'willAutoRenew',
  ]

CROS_RECENT_USERS_ARGUMENTS = [u'recentusers', u'users']
CROS_ACTIVE_TIME_RANGES_ARGUMENTS = [u'timeranges', u'activetimeranges', u'times']
CROS_DEVICE_FILES_ARGUMENTS = [u'devicefiles', u'files']
CROS_START_ARGUMENTS = [u'start', u'startdate', u'oldestdate']
CROS_END_ARGUMENTS = [u'end', u'enddate']

# From https://www.chromium.org/chromium-os/tpm_firmware_update
CROS_TPM_VULN_VERSIONS = [u'41f', u'420', u'628', u'8520',]
CROS_TPM_FIXED_VERSIONS = [u'422', u'62b', u'8521',]

#
# Global variables
#
# The following GM_XXX constants are arbitrary but must be unique
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
GM_SYSEXITRC = u'sxrc'
# Path to gam
GM_GAM_PATH = u'gpth'
# Are we on Windows?
GM_WINDOWS = u'wndo'
# Encodings
GM_SYS_ENCODING = u'syen'
# Extra arguments to pass to GAPI functions
GM_EXTRA_ARGS_DICT = u'exad'
# Current API user
GM_CURRENT_API_USER = u'capu'
# Current API scope
GM_CURRENT_API_SCOPES = u'scoc'
# Values retrieved from oauth2service.json
GM_OAUTH2SERVICE_JSON_DATA = u'oajd'
GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID = u'oaci'
# File containing time of last GAM update check
GM_LAST_UPDATE_CHECK_TXT = u'lupc'
# Dictionary mapping OrgUnit ID to Name
GM_MAP_ORGUNIT_ID_TO_NAME = u'oi2n'
# Dictionary mapping Role ID to Name
GM_MAP_ROLE_ID_TO_NAME = u'ri2n'
# Dictionary mapping Role Name to ID
GM_MAP_ROLE_NAME_TO_ID = u'rn2i'
# Dictionary mapping User ID to Name
GM_MAP_USER_ID_TO_NAME = u'ui2n'
# GAM cache directory. If no_cache is True, this variable will be set to None
GM_CACHE_DIR = u'gacd'
# Reset GAM cache directory after discovery
GM_CACHE_DISCOVERY_ONLY = u'gcdo'
# Dictionary mapping Building ID to Name
GM_MAP_BUILDING_ID_TO_NAME = u'bi2n'
# Dictionary mapping Building Name to ID
GM_MAP_BUILDING_NAME_TO_ID = u'bn2i'
#
GM_Globals = {
  GM_SYSEXITRC: 0,
  GM_GAM_PATH: os.path.dirname(os.path.realpath(__file__)) if not getattr(sys, u'frozen', False) else os.path.dirname(sys.executable),
  GM_WINDOWS: os.name == u'nt',
  GM_SYS_ENCODING: DEFAULT_CHARSET,
  GM_EXTRA_ARGS_DICT:  {u'prettyPrint': False},
  GM_CURRENT_API_USER: None,
  GM_CURRENT_API_SCOPES: [],
  GM_OAUTH2SERVICE_JSON_DATA: None,
  GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID: None,
  GM_LAST_UPDATE_CHECK_TXT: u'',
  GM_MAP_ORGUNIT_ID_TO_NAME: None,
  GM_MAP_ROLE_ID_TO_NAME: None,
  GM_MAP_ROLE_NAME_TO_ID: None,
  GM_MAP_USER_ID_TO_NAME: None,
  GM_CACHE_DIR: None,
  GM_CACHE_DISCOVERY_ONLY: True,
  GM_MAP_BUILDING_ID_TO_NAME: None,
  GM_MAP_BUILDING_NAME_TO_ID: None,
  }
#
# Global variables defined by environment variables/signal files
#
# When retrieving lists of Google Drive activities from API, how many should be retrieved in each chunk
GC_ACTIVITY_MAX_RESULTS = u'activity_max_results'
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, don't automatically generate gam batch commands
GC_AUTO_BATCH_MIN = u'auto_batch_min'
# When processing items in batches, how many should be processed in each batch
GC_BATCH_SIZE = u'batch_size'
# GAM cache directory. If no_cache is specified, this variable will be set to None
GC_CACHE_DIR = u'cache_dir'
# GAM cache discovery only. If no_cache is False, only API discovery calls will be cached
GC_CACHE_DISCOVERY_ONLY = u'cache_discovery_only'
# Character set of batch, csv, data files
GC_CHARSET = u'charset'
# Path to client_secrets.json
GC_CLIENT_SECRETS_JSON = u'client_secrets_json'
# GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
GC_CONFIG_DIR = u'config_dir'
# custmerId from gam.cfg or retrieved from Google
GC_CUSTOMER_ID = u'customer_id'
# If debug_level > 0: extra_args[u'prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
GC_DEBUG_LEVEL = u'debug_level'
# When retrieving lists of ChromeOS/Mobile devices from API, how many should be retrieved in each chunk
GC_DEVICE_MAX_RESULTS = u'device_max_results'
# Domain obtained from gam.cfg or oauth2.txt
GC_DOMAIN = u'domain'
# Google Drive download directory
GC_DRIVE_DIR = u'drive_dir'
# When retrieving lists of Drive files/folders from API, how many should be retrieved in each chunk
GC_DRIVE_MAX_RESULTS = u'drive_max_results'
# When retrieving lists of Google Group members from API, how many should be retrieved in each chunk
GC_MEMBER_MAX_RESULTS = u'member_max_results'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doRequestOAuth prints a link and waits for the verification code when oauth2.txt is being created
GC_NO_BROWSER = u'no_browser'
# Disable GAM API caching
GC_NO_CACHE = u'no_cache'
# Disable GAM update check
GC_NO_UPDATE_CHECK = u'no_update_check'
# Disable SSL certificate validation
GC_NO_VERIFY_SSL = u'no_verify_ssl'
# Number of threads for gam batch
GC_NUM_THREADS = u'num_threads'
# Path to oauth2.txt
GC_OAUTH2_TXT = u'oauth2_txt'
# Path to oauth2service.json
GC_OAUTH2SERVICE_JSON = u'oauth2service_json'
# Default section to use for processing
GC_SECTION = u'section'
# Add (n/m) to end of messages if number of items to be processed exceeds this number
GC_SHOW_COUNTS_MIN = u'show_counts_min'
# Enable/disable "Getting ... " messages
GC_SHOW_GETTINGS = u'show_gettings'
# GAM config directory containing json discovery files
GC_SITE_DIR = u'site_dir'
# When retrieving lists of Users from API, how many should be retrieved in each chunk
GC_USER_MAX_RESULTS = u'user_max_results'

GC_Defaults = {
  GC_ACTIVITY_MAX_RESULTS: 100,
  GC_AUTO_BATCH_MIN: 0,
  GC_BATCH_SIZE: 50,
  GC_CACHE_DIR: u'',
  GC_CACHE_DISCOVERY_ONLY: True,
  GC_CHARSET: DEFAULT_CHARSET,
  GC_CLIENT_SECRETS_JSON: FN_CLIENT_SECRETS_JSON,
  GC_CONFIG_DIR: u'',
  GC_CUSTOMER_ID: MY_CUSTOMER,
  GC_DEBUG_LEVEL: 0,
  GC_DEVICE_MAX_RESULTS: 500,
  GC_DOMAIN: u'',
  GC_DRIVE_DIR: u'',
  GC_DRIVE_MAX_RESULTS: 1000,
  GC_MEMBER_MAX_RESULTS: 200,
  GC_NO_BROWSER: False,
  GC_NO_CACHE: False,
  GC_NO_UPDATE_CHECK: False,
  GC_NO_VERIFY_SSL: False,
  GC_NUM_THREADS: 25,
  GC_OAUTH2_TXT: FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: FN_OAUTH2SERVICE_JSON,
  GC_SECTION: u'',
  GC_SHOW_COUNTS_MIN: 0,
  GC_SHOW_GETTINGS: True,
  GC_SITE_DIR: u'',
  GC_USER_MAX_RESULTS: 500,
  }

GC_Values = {}

GC_TYPE_BOOLEAN = u'bool'
GC_TYPE_CHOICE = u'choi'
GC_TYPE_DIRECTORY = u'dire'
GC_TYPE_EMAIL = u'emai'
GC_TYPE_FILE = u'file'
GC_TYPE_INTEGER = u'inte'
GC_TYPE_LANGUAGE = u'lang'
GC_TYPE_STRING = u'stri'

GC_VAR_TYPE = u'type'
GC_VAR_LIMITS = u'lmit'

GC_VAR_INFO = {
  GC_ACTIVITY_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 500)},
  GC_AUTO_BATCH_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_BATCH_SIZE: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_CACHE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CACHE_DISCOVERY_ONLY: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_CHARSET: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_CLIENT_SECRETS_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_CONFIG_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CUSTOMER_ID: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DEBUG_LEVEL: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_DEVICE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_DOMAIN: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DRIVE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_DRIVE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_MEMBER_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 10000)},
  GC_NO_BROWSER: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_CACHE: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_VERIFY_SSL: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NUM_THREADS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, None)},
  GC_OAUTH2_TXT: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_SECTION: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_SHOW_COUNTS_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_SITE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_USER_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 500)},
  }
# Google API constants

NEVER_TIME = u'1970-01-01T00:00:00.000Z'
NEVER_START_DATE = u'1970-01-01'
NEVER_END_DATE = u'1969-12-31'
ROLE_MANAGER = u'MANAGER'
ROLE_MEMBER = u'MEMBER'
ROLE_OWNER = u'OWNER'
ROLE_USER = u'USER'
ROLE_MANAGER_MEMBER = u','.join([ROLE_MANAGER, ROLE_MEMBER])
ROLE_MANAGER_OWNER = u','.join([ROLE_MANAGER, ROLE_OWNER])
ROLE_MANAGER_MEMBER_OWNER = u','.join([ROLE_MANAGER, ROLE_MEMBER, ROLE_OWNER])
ROLE_MEMBER_OWNER = u','.join([ROLE_MEMBER, ROLE_OWNER])
PROJECTION_CHOICES_MAP = {u'basic': u'BASIC', u'full': u'FULL',}
SORTORDER_CHOICES_MAP = {u'ascending': u'ASCENDING', u'descending': u'DESCENDING',}
#
CLEAR_NONE_ARGUMENT = [u'clear', u'none',]
#
MESSAGE_API_ACCESS_CONFIG = u'API access is configured in your Control Panel under: Security-Show more-Advanced settings-Manage API client access'
MESSAGE_API_ACCESS_DENIED = u'API access Denied.\n\nPlease make sure the Client ID: {0} is authorized for the API Scope(s): {1}'
MESSAGE_GAM_EXITING_FOR_UPDATE = u'GAM is now exiting so that you can overwrite this old version with the latest release'
MESSAGE_GAM_OUT_OF_MEMORY = u'GAM has run out of memory. If this is a large G Suite instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS = u'Header "{0}" not found in CSV headers of "{1}".'
MESSAGE_HIT_CONTROL_C_TO_UPDATE = u'\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can create a file named noupdatecheck.txt in the same location as gam.py or gam.exe and GAM won\'t ever check for updates.'
MESSAGE_INVALID_JSON = u'The file {0} has an invalid format.'
MESSAGE_NO_DISCOVERY_INFORMATION = u'No online discovery doc and {0} does not exist locally'
MESSAGE_NO_PYTHON_SSL = u'You don\'t have the Python SSL module installed so we can\'t verify SSL Certificates. You can fix this by installing the Python SSL module or you can live on the edge and turn SSL validation off by creating a file named noverifyssl.txt in the same location as gam.exe / gam.py'
MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE = u'Cowardly refusing to perform migration due to lack of target drive space. Source size: {0}mb Target Free: {1}mb'
MESSAGE_REQUEST_COMPLETED_NO_FILES = u'Request completed but no results/files were returned, try requesting again'
MESSAGE_REQUEST_NOT_COMPLETE = u'Request needs to be completed before downloading, current status is: {0}'
MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = u'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
MESSAGE_SERVICE_NOT_APPLICABLE = u'Service not applicable for this address: {0}. Please make sure service is enabled for user and run\n\ngam user <user> check serviceaccount\n\nfor further instructions'
MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON = u'Please run\n\ngam create project\ngam user <user> check serviceaccount\n\nto create and configure a service account.'
MESSAGE_OAUTH2SERVICE_JSON_INVALID = u'The file {0} is missing required keys (client_email, client_id or private_key). Please remove it and recreate with the commands:\n\ngam create project\ngam user <user> check serviceaccount'
# oauth errors
OAUTH2_TOKEN_ERRORS = [
  u'access_denied',
  u'access_denied: Requested client not authorized',
  u'internal_failure: Backend Error',
  u'invalid_grant: Bad Request',
  u'invalid_grant: Invalid email or User ID',
  u'invalid_grant: Not a valid email',
  u'invalid_request: Invalid impersonation prn email address',
  u'unauthorized_client: Client is unauthorized to retrieve access tokens using this method',
  u'unauthorized_client: Unauthorized client or scope in request',
  ]
#
# callGAPI throw reasons
GAPI_ABORTED = u'aborted'
GAPI_AUTH_ERROR = u'authError'
GAPI_BACKEND_ERROR = u'backendError'
GAPI_BAD_REQUEST = u'badRequest'
GAPI_CONDITION_NOT_MET = u'conditionNotMet'
GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED = u'cyclicMembershipsNotAllowed'
GAPI_DOMAIN_CANNOT_USE_APIS = u'domainCannotUseApis'
GAPI_DOMAIN_NOT_FOUND = u'domainNotFound'
GAPI_DUPLICATE = u'duplicate'
GAPI_FAILED_PRECONDITION = u'failedPrecondition'
GAPI_FORBIDDEN = u'forbidden'
GAPI_GROUP_NOT_FOUND = u'groupNotFound'
GAPI_INTERNAL_ERROR = u'internalError'
GAPI_INVALID = u'invalid'
GAPI_INVALID_ARGUMENT = u'invalidArgument'
GAPI_INVALID_MEMBER = u'invalidMember'
GAPI_MEMBER_NOT_FOUND = u'memberNotFound'
GAPI_NOT_FOUND = u'notFound'
GAPI_NOT_IMPLEMENTED = u'notImplemented'
GAPI_QUOTA_EXCEEDED = u'quotaExceeded'
GAPI_RATE_LIMIT_EXCEEDED = u'rateLimitExceeded'
GAPI_RESOURCE_NOT_FOUND = u'resourceNotFound'
GAPI_SERVICE_NOT_AVAILABLE = u'serviceNotAvailable'
GAPI_SYSTEM_ERROR = u'systemError'
GAPI_USER_NOT_FOUND = u'userNotFound'
GAPI_USER_RATE_LIMIT_EXCEEDED = u'userRateLimitExceeded'
#
GAPI_DEFAULT_RETRY_REASONS = [GAPI_QUOTA_EXCEEDED, GAPI_RATE_LIMIT_EXCEEDED, GAPI_USER_RATE_LIMIT_EXCEEDED, GAPI_BACKEND_ERROR, GAPI_INTERNAL_ERROR]
GAPI_GMAIL_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE]
GAPI_GPLUS_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE]
GAPI_GROUP_GET_THROW_REASONS = [GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_DOMAIN_CANNOT_USE_APIS, GAPI_FORBIDDEN, GAPI_BAD_REQUEST]
GAPI_GROUP_GET_RETRY_REASONS = [GAPI_INVALID, GAPI_SYSTEM_ERROR]
GAPI_MEMBERS_THROW_REASONS = [GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_DOMAIN_CANNOT_USE_APIS, GAPI_INVALID, GAPI_FORBIDDEN]
GAPI_MEMBERS_RETRY_REASONS = [GAPI_SYSTEM_ERROR]

USER_ADDRESS_TYPES = [u'home', u'work', u'other']
USER_EMAIL_TYPES = [u'home', u'work', u'other']
USER_EXTERNALID_TYPES = [u'account', u'customer', u'login_id', u'network', u'organization']
USER_GENDER_TYPES = [u'female', u'male', u'unknown']
USER_IM_TYPES = [u'home', u'work', u'other']
USER_KEYWORD_TYPES = [u'occupation', u'outlook']
USER_LOCATION_TYPES = [u'default', u'desk']
USER_ORGANIZATION_TYPES = [u'domain_only', u'school', u'unknown', u'work']
USER_PHONE_TYPES = [u'assistant', u'callback', u'car', u'company_main',
                    u'grand_central', u'home', u'home_fax', u'isdn', u'main',
                    u'mobile', u'other', u'other_fax', u'pager', u'radio',
                    u'telex', u'tty_tdd', u'work', u'work_fax', u'work_mobile',
                    u'work_pager']
USER_RELATION_TYPES = [u'admin_assistant', u'assistant', u'brother', u'child',
                       u'domestic_partner', u'dotted_line_manager',
                       u'exec_assistant', u'father', u'friend', u'manager',
                       u'mother', u'parent', u'partner', u'referred_by',
                       u'relative', u'sister', u'spouse']
USER_WEBSITE_TYPES = [u'app_install_page', u'blog', u'ftp', u'home',
                      u'home_page', u'other', u'profile', u'reservations',
                      u'work']

WEBCOLOR_MAP = {
    u'aliceblue': u'#f0f8ff',
    u'antiquewhite': u'#faebd7',
    u'aqua': u'#00ffff',
    u'aquamarine': u'#7fffd4',
    u'azure': u'#f0ffff',
    u'beige': u'#f5f5dc',
    u'bisque': u'#ffe4c4',
    u'black': u'#000000',
    u'blanchedalmond': u'#ffebcd',
    u'blue': u'#0000ff',
    u'blueviolet': u'#8a2be2',
    u'brown': u'#a52a2a',
    u'burlywood': u'#deb887',
    u'cadetblue': u'#5f9ea0',
    u'chartreuse': u'#7fff00',
    u'chocolate': u'#d2691e',
    u'coral': u'#ff7f50',
    u'cornflowerblue': u'#6495ed',
    u'cornsilk': u'#fff8dc',
    u'crimson': u'#dc143c',
    u'cyan': u'#00ffff',
    u'darkblue': u'#00008b',
    u'darkcyan': u'#008b8b',
    u'darkgoldenrod': u'#b8860b',
    u'darkgray': u'#a9a9a9',
    u'darkgrey': u'#a9a9a9',
    u'darkgreen': u'#006400',
    u'darkkhaki': u'#bdb76b',
    u'darkmagenta': u'#8b008b',
    u'darkolivegreen': u'#556b2f',
    u'darkorange': u'#ff8c00',
    u'darkorchid': u'#9932cc',
    u'darkred': u'#8b0000',
    u'darksalmon': u'#e9967a',
    u'darkseagreen': u'#8fbc8f',
    u'darkslateblue': u'#483d8b',
    u'darkslategray': u'#2f4f4f',
    u'darkslategrey': u'#2f4f4f',
    u'darkturquoise': u'#00ced1',
    u'darkviolet': u'#9400d3',
    u'deeppink': u'#ff1493',
    u'deepskyblue': u'#00bfff',
    u'dimgray': u'#696969',
    u'dimgrey': u'#696969',
    u'dodgerblue': u'#1e90ff',
    u'firebrick': u'#b22222',
    u'floralwhite': u'#fffaf0',
    u'forestgreen': u'#228b22',
    u'fuchsia': u'#ff00ff',
    u'gainsboro': u'#dcdcdc',
    u'ghostwhite': u'#f8f8ff',
    u'gold': u'#ffd700',
    u'goldenrod': u'#daa520',
    u'gray': u'#808080',
    u'grey': u'#808080',
    u'green': u'#008000',
    u'greenyellow': u'#adff2f',
    u'honeydew': u'#f0fff0',
    u'hotpink': u'#ff69b4',
    u'indianred': u'#cd5c5c',
    u'indigo': u'#4b0082',
    u'ivory': u'#fffff0',
    u'khaki': u'#f0e68c',
    u'lavender': u'#e6e6fa',
    u'lavenderblush': u'#fff0f5',
    u'lawngreen': u'#7cfc00',
    u'lemonchiffon': u'#fffacd',
    u'lightblue': u'#add8e6',
    u'lightcoral': u'#f08080',
    u'lightcyan': u'#e0ffff',
    u'lightgoldenrodyellow': u'#fafad2',
    u'lightgray': u'#d3d3d3',
    u'lightgrey': u'#d3d3d3',
    u'lightgreen': u'#90ee90',
    u'lightpink': u'#ffb6c1',
    u'lightsalmon': u'#ffa07a',
    u'lightseagreen': u'#20b2aa',
    u'lightskyblue': u'#87cefa',
    u'lightslategray': u'#778899',
    u'lightslategrey': u'#778899',
    u'lightsteelblue': u'#b0c4de',
    u'lightyellow': u'#ffffe0',
    u'lime': u'#00ff00',
    u'limegreen': u'#32cd32',
    u'linen': u'#faf0e6',
    u'magenta': u'#ff00ff',
    u'maroon': u'#800000',
    u'mediumaquamarine': u'#66cdaa',
    u'mediumblue': u'#0000cd',
    u'mediumorchid': u'#ba55d3',
    u'mediumpurple': u'#9370db',
    u'mediumseagreen': u'#3cb371',
    u'mediumslateblue': u'#7b68ee',
    u'mediumspringgreen': u'#00fa9a',
    u'mediumturquoise': u'#48d1cc',
    u'mediumvioletred': u'#c71585',
    u'midnightblue': u'#191970',
    u'mintcream': u'#f5fffa',
    u'mistyrose': u'#ffe4e1',
    u'moccasin': u'#ffe4b5',
    u'navajowhite': u'#ffdead',
    u'navy': u'#000080',
    u'oldlace': u'#fdf5e6',
    u'olive': u'#808000',
    u'olivedrab': u'#6b8e23',
    u'orange': u'#ffa500',
    u'orangered': u'#ff4500',
    u'orchid': u'#da70d6',
    u'palegoldenrod': u'#eee8aa',
    u'palegreen': u'#98fb98',
    u'paleturquoise': u'#afeeee',
    u'palevioletred': u'#db7093',
    u'papayawhip': u'#ffefd5',
    u'peachpuff': u'#ffdab9',
    u'peru': u'#cd853f',
    u'pink': u'#ffc0cb',
    u'plum': u'#dda0dd',
    u'powderblue': u'#b0e0e6',
    u'purple': u'#800080',
    u'red': u'#ff0000',
    u'rosybrown': u'#bc8f8f',
    u'royalblue': u'#4169e1',
    u'saddlebrown': u'#8b4513',
    u'salmon': u'#fa8072',
    u'sandybrown': u'#f4a460',
    u'seagreen': u'#2e8b57',
    u'seashell': u'#fff5ee',
    u'sienna': u'#a0522d',
    u'silver': u'#c0c0c0',
    u'skyblue': u'#87ceeb',
    u'slateblue': u'#6a5acd',
    u'slategray': u'#708090',
    u'slategrey': u'#708090',
    u'snow': u'#fffafa',
    u'springgreen': u'#00ff7f',
    u'steelblue': u'#4682b4',
    u'tan': u'#d2b48c',
    u'teal': u'#008080',
    u'thistle': u'#d8bfd8',
    u'tomato': u'#ff6347',
    u'turquoise': u'#40e0d0',
    u'violet': u'#ee82ee',
    u'wheat': u'#f5deb3',
    u'white': u'#ffffff',
    u'whitesmoke': u'#f5f5f5',
    u'yellow': u'#ffff00',
    u'yellowgreen': u'#9acd32',
}
# Valid language codes
LANGUAGE_CODES_MAP = {
  u'ach': u'ach', u'af': u'af', u'ag': u'ga', u'ak': u'ak', u'am': u'am', u'ar': u'ar', u'az': u'az', #Luo, Afrikaans, Irish, Akan, Amharic, Arabica, Azerbaijani
  u'be': u'be', u'bem': u'bem', u'bg': u'bg', u'bn': u'bn', u'br': u'br', u'bs': u'bs', u'ca': u'ca', #Belarusian, Bemba, Bulgarian, Bengali, Breton, Bosnian, Catalan
  u'chr': u'chr', u'ckb': u'ckb', u'co': u'co', u'crs': u'crs', u'cs': u'cs', u'cy': u'cy', u'da': u'da', #Cherokee, Kurdish (Sorani), Corsican, Seychellois Creole, Czech, Welsh, Danish
  u'de': u'de', u'ee': u'ee', u'el': u'el', u'en': u'en', u'en-gb': u'en-GB', u'en-us': u'en-US', u'eo': u'eo', #German, Ewe, Greek, English, English (UK), English (US), Esperanto
  u'es': u'es', u'es-419': u'es-419', u'et': u'et', u'eu': u'eu', u'fa': u'fa', u'fi': u'fi', u'fo': u'fo', #Spanish, Spanish (Latin American), Estonian, Basque, Persian, Finnish, Faroese
  u'fr': u'fr', u'fr-ca': u'fr-ca', u'fy': u'fy', u'ga': u'ga', u'gaa': u'gaa', u'gd': u'gd', u'gl': u'gl', #French, French (Canada), Frisian, Irish, Ga, Scots Gaelic, Galician
  u'gn': u'gn', u'gu': u'gu', u'ha': u'ha', u'haw': u'haw', u'he': u'he', u'hi': u'hi', u'hr': u'hr', #Guarani, Gujarati, Hausa, Hawaiian, Hebrew, Hindi, Croatian
  u'ht': u'ht', u'hu': u'hu', u'hy': u'hy', u'ia': u'ia', u'id': u'id', u'ig': u'ig', u'in': u'in', #Haitian Creole, Hungarian, Armenian, Interlingua, Indonesian, Igbo, in
  u'is': u'is', u'it': u'it', u'iw': u'iw', u'ja': u'ja', u'jw': u'jw', u'ka': u'ka', u'kg': u'kg', #Icelandic, Italian, Hebrew, Japanese, Javanese, Georgian, Kongo
  u'kk': u'kk', u'km': u'km', u'kn': u'kn', u'ko': u'ko', u'kri': u'kri', u'ku': u'ku', u'ky': u'ky', #Kazakh, Khmer, Kannada, Korean, Krio (Sierra Leone), Kurdish, Kyrgyz
  u'la': u'la', u'lg': u'lg', u'ln': u'ln', u'lo': u'lo', u'loz': u'loz', u'lt': u'lt', u'lua': u'lua', #Latin, Luganda, Lingala, Laothian, Lozi, Lithuanian, Tshiluba
  u'lv': u'lv', u'mfe': u'mfe', u'mg': u'mg', u'mi': u'mi', u'mk': u'mk', u'ml': u'ml', u'mn': u'mn', #Latvian, Mauritian Creole, Malagasy, Maori, Macedonian, Malayalam, Mongolian
  u'mo': u'mo', u'mr': u'mr', u'ms': u'ms', u'mt': u'mt', u'my': u'my', u'ne': u'ne', u'nl': u'nl', #Moldavian, Marathi, Malay, Maltese, Burmese, Nepali, Dutch
  u'nn': u'nn', u'no': u'no', u'nso': u'nso', u'ny': u'ny', u'nyn': u'nyn', u'oc': u'oc', u'om': u'om', #Norwegian (Nynorsk), Norwegian, Northern Sotho, Chichewa, Runyakitara, Occitan, Oromo
  u'or': u'or', u'pa': u'pa', u'pcm': u'pcm', u'pl': u'pl', u'ps': u'ps', u'pt-br': u'pt-BR', u'pt-pt': u'pt-PT', #Oriya, Punjabi, Nigerian Pidgin, Polish, Pashto, Portuguese (Brazil), Portuguese (Portugal)
  u'qu': u'qu', u'rm': u'rm', u'rn': u'rn', u'ro': u'ro', u'ru': u'ru', u'rw': u'rw', u'sd': u'sd', #Quechua, Romansh, Kirundi, Romanian, Russian, Kinyarwanda, Sindhi
  u'sh': u'sh', u'si': u'si', u'sk': u'sk', u'sl': u'sl', u'sn': u'sn', u'so': u'so', u'sq': u'sq', #Serbo-Croatian, Sinhalese, Slovak, Slovenian, Shona, Somali, Albanian
  u'sr': u'sr', u'sr-me': u'sr-ME', u'st': u'st', u'su': u'su', u'sv': u'sv', u'sw': u'sw', u'ta': u'ta', #Serbian, Montenegrin, Sesotho, Sundanese, Swedish, Swahili, Tamil
  u'te': u'te', u'tg': u'tg', u'th': u'th', u'ti': u'ti', u'tk': u'tk', u'tl': u'tl', u'tn': u'tn', #Telugu, Tajik, Thai, Tigrinya, Turkmen, Tagalog, Setswana
  u'to': u'to', u'tr': u'tr', u'tt': u'tt', u'tum': u'tum', u'tw': u'tw', u'ug': u'ug', u'uk': u'uk', #Tonga, Turkish, Tatar, Tumbuka, Twi, Uighur, Ukrainian
  u'ur': u'ur', u'uz': u'uz', u'vi': u'vi', u'wo': u'wo', u'xh': u'xh', u'yi': u'yi', u'yo': u'yo', #Urdu, Uzbek, Vietnamese, Wolof, Xhosa, Yiddish, Yoruba
  u'zh-cn': u'zh-CN', u'zh-hk': u'zh-HK', u'zh-tw': u'zh-TW', u'zu': u'zu', #Chinese (Simplified), Chinese (Hong Kong/Traditional), Chinese (Taiwan/Traditional), Zulu
  }
