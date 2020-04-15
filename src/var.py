import os
import ssl
import string
import sys
import platform
import re

gam_author = 'Jay Lee <jay0lee@gmail.com>'
gam_version = '5.05'
gam_license = 'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

GAM_URL = 'https://git.io/gam'
GAM_INFO = (f'GAM {gam_version} - {GAM_URL} / {gam_author} / '
            f'Python {platform.python_version()} {sys.version_info.releaselevel} / '
            f'{platform.platform()} {platform.machine()}')

GAM_RELEASES = 'https://github.com/jay0lee/GAM/releases'
GAM_WIKI = 'https://github.com/jay0lee/GAM/wiki'
GAM_ALL_RELEASES = 'https://api.github.com/repos/jay0lee/GAM/releases'
GAM_LATEST_RELEASE = GAM_ALL_RELEASES+'/latest'
GAM_PROJECT_FILEPATH = 'https://raw.githubusercontent.com/jay0lee/GAM/master/src/'

true_values = ['on', 'yes', 'enabled', 'true', '1']
false_values = ['off', 'no', 'disabled', 'false', '0']
usergroup_types = ['user', 'users',
                   'group', 'group_ns', 'grooup_susp',
                   'ou', 'org', 'ou_ns', 'org_ns', 'ou_susp', 'org_susp',
                   'ou_and_children', 'ou_and_child', 'ou_and_children_ns', 'ou_and_child_ns', 'ou_and_children_susp', 'ou_and_child_susp',
                   'query', 'queries', 'license', 'licenses', 'licence', 'licences', 'file', 'csv', 'csvfile', 'all',
                   'cros', 'cros_sn', 'crosquery', 'crosqueries', 'crosfile', 'croscsv', 'croscsvfile']
ERROR_PREFIX = 'ERROR: '
WARNING_PREFIX = 'WARNING: '
UTF8 = 'utf-8'
UTF8_SIG = 'utf-8-sig'
FN_EXTRA_ARGS_TXT = 'extra-args.txt'
FN_LAST_UPDATE_CHECK_TXT = 'lastupdatecheck.txt'
MY_CUSTOMER = 'my_customer'
# See https://support.google.com/drive/answer/37603
MAX_GOOGLE_SHEET_CELLS = 5000000
MAX_LOCAL_GOOGLE_TIME_OFFSET = 30

SKUS = {
  '1010010001': {
    'product': '101001', 'aliases': ['identity', 'cloudidentity'], 'displayName': 'Cloud Identity'},
  '1010050001': {
    'product': '101005', 'aliases': ['identitypremium', 'cloudidentitypremium'], 'displayName': 'Cloud Identity Premium'},
  '1010310002': {
    'product': '101031', 'aliases': ['gsefe', 'e4e', 'gsuiteenterpriseeducation'], 'displayName': 'G Suite Enterprise for Education'},
  '1010310003': {
    'product': '101031', 'aliases': ['gsefes', 'e4es', 'gsuiteenterpriseeducationstudent'], 'displayName': 'G Suite Enterprise for Education (Student)'},
  '1010330003': {
    'product': '101033', 'aliases': ['gvstarter', 'voicestarter', 'googlevoicestarter'], 'displayName': 'Google Voice Starter'},
  '1010330004': {
    'product': '101033', 'aliases': ['gvstandard', 'voicestandard', 'googlevoicestandard'], 'displayName': 'Google Voice Standard'},
  '1010330002': {
    'product': '101033', 'aliases': ['gvpremier', 'voicepremier', 'googlevoicepremier'], 'displayName': 'Google Voice Premier'},
  'Google-Apps': {
    'product': 'Google-Apps', 'aliases': ['standard', 'free'], 'displayName': 'G Suite Free/Standard'},
  'Google-Apps-For-Business': {
    'product': 'Google-Apps', 'aliases': ['gafb', 'gafw', 'basic', 'gsuitebasic'], 'displayName': 'G Suite Basic'},
  'Google-Apps-For-Government': {
    'product': 'Google-Apps', 'aliases': ['gafg', 'gsuitegovernment', 'gsuitegov'], 'displayName': 'G Suite Government'},
  'Google-Apps-For-Postini': {
    'product': 'Google-Apps', 'aliases': ['gams', 'postini', 'gsuitegams', 'gsuitepostini', 'gsuitemessagesecurity'], 'displayName': 'G Suite Message Security'},
  'Google-Apps-Lite': {
    'product': 'Google-Apps', 'aliases': ['gal', 'gsl', 'lite', 'gsuitelite'], 'displayName': 'G Suite Lite'},
  'Google-Apps-Unlimited': {
    'product': 'Google-Apps', 'aliases': ['gau', 'gsb', 'unlimited', 'gsuitebusiness'], 'displayName': 'G Suite Business'},
  '1010020020': {
    'product': 'Google-Apps', 'aliases': ['gae', 'gse', 'enterprise', 'gsuiteenterprise'], 'displayName': 'G Suite Enterprise'},
  '1010340002': {
    'product': '101034', 'aliases': ['gsbau', 'businessarchived', 'gsuitebusinessarchived'], 'displayName': 'G Suite Business Archived'},
  '1010340001': {
    'product': '101034', 'aliases': ['gseau', 'enterprisearchived', 'gsuiteenterprisearchived'], 'displayName': 'G Suite Enterprise Archived'},
  '1010060001': {
    'product': 'Google-Apps', 'aliases': ['d4e', 'driveenterprise', 'drive4enterprise'], 'displayName': 'Drive Enterprise'},
  'Google-Drive-storage-20GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive20gb', '20gb', 'googledrivestorage20gb'], 'displayName': 'Google Drive Storage 20GB'},
  'Google-Drive-storage-50GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive50gb', '50gb', 'googledrivestorage50gb'], 'displayName': 'Google Drive Storage 50GB'},
  'Google-Drive-storage-200GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive200gb', '200gb', 'googledrivestorage200gb'], 'displayName': 'Google Drive Storage 200GB'},
  'Google-Drive-storage-400GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive400gb', '400gb', 'googledrivestorage400gb'], 'displayName': 'Google Drive Storage 400GB'},
  'Google-Drive-storage-1TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive1tb', '1tb', 'googledrivestorage1tb'], 'displayName': 'Google Drive Storage 1TB'},
  'Google-Drive-storage-2TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive2tb', '2tb', 'googledrivestorage2tb'], 'displayName': 'Google Drive Storage 2TB'},
  'Google-Drive-storage-4TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive4tb', '4tb', 'googledrivestorage4tb'], 'displayName': 'Google Drive Storage 4TB'},
  'Google-Drive-storage-8TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive8tb', '8tb', 'googledrivestorage8tb'], 'displayName': 'Google Drive Storage 8TB'},
  'Google-Drive-storage-16TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive16tb', '16tb', 'googledrivestorage16tb'], 'displayName': 'Google Drive Storage 16TB'},
  'Google-Vault': {
    'product': 'Google-Vault', 'aliases': ['vault', 'googlevault'], 'displayName': 'Google Vault'},
  'Google-Vault-Former-Employee': {
    'product': 'Google-Vault', 'aliases': ['vfe', 'googlevaultformeremployee'], 'displayName': 'Google Vault Former Employee'},
  'Google-Coordinate': {
    'product': 'Google-Coordinate', 'aliases': ['coordinate', 'googlecoordinate'], 'displayName': 'Google Coordinate'},
  'Google-Chrome-Device-Management': {
    'product': 'Google-Chrome-Device-Management', 'aliases': ['chrome', 'cdm', 'googlechromedevicemanagement'], 'displayName': 'Google Chrome Device Management'}
  }

PRODUCTID_NAME_MAPPINGS = {
  '101001': 'Cloud Identity Free',
  '101005': 'Cloud Identity Premium',
  '101031': 'G Suite Enterprise for Education',
  '101033': 'Google Voice',
  '101034': 'G Suite Archived',
  'Google-Apps': 'G Suite',
  'Google-Chrome-Device-Management': 'Google Chrome Device Management',
  'Google-Coordinate': 'Google Coordinate',
  'Google-Drive-storage': 'Google Drive Storage',
  'Google-Vault': 'Google Vault',
  }

# Legacy APIs that use v1 discovery. Newer APIs should all use v2.
V1_DISCOVERY_APIS = {
  'admin',
  'appsactivity',
  'calendar',
  'drive',
  'gmail',
  'groupssettings',
  'licensing',
  'oauth2',
  'reseller',
  'siteVerification',
  'storage',
  }

API_VER_MAPPING = {
  'alertcenter': 'v1beta1',
  'appsactivity': 'v1',
  'calendar': 'v3',
  'classroom': 'v1',
  'cloudprint': 'v2',
  'cloudresourcemanager': 'v2',
  'cloudresourcemanagerv1': 'v1',
  'datatransfer': 'datatransfer_v1',
  'directory': 'directory_v1',
  'drive': 'v2',
  'drive3': 'v3',
  'gmail': 'v1',
  'groupssettings': 'v1',
  'iam': 'v1',
  'iap': 'v1',
  'licensing': 'v1',
  'oauth2': 'v2',
  'pubsub': 'v1',
  'reports': 'reports_v1',
  'reseller': 'v1',
  'servicemanagement': 'v1',
  'sheets': 'v4',
  'siteVerification': 'v1',
  'storage': 'v1',
  'vault': 'v1',
  }

USERINFO_EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'

API_SCOPE_MAPPING = {
  'alertcenter': ['https://www.googleapis.com/auth/apps.alerts',],
  'appsactivity': ['https://www.googleapis.com/auth/activity',
                   'https://www.googleapis.com/auth/drive',],
  'calendar': ['https://www.googleapis.com/auth/calendar',],
  'drive': ['https://www.googleapis.com/auth/drive',],
  'drive3': ['https://www.googleapis.com/auth/drive',],
  'gmail': ['https://mail.google.com/',
            'https://www.googleapis.com/auth/gmail.settings.basic',
            'https://www.googleapis.com/auth/gmail.settings.sharing',],
  'sheets': ['https://www.googleapis.com/auth/spreadsheets',],
}

ADDRESS_FIELDS_PRINT_ORDER = [
  'contactName', 'organizationName',
  'addressLine1', 'addressLine2', 'addressLine3',
  'locality', 'region', 'postalCode', 'countryCode',
  ]

ADDRESS_FIELDS_ARGUMENT_MAP = {
  'contact': 'contactName', 'contactname': 'contactName',
  'name': 'organizationName', 'organizationname': 'organizationName',
  'address': 'addressLine1', 'address1': 'addressLine1', 'addressline1': 'addressLine1',
  'address2': 'addressLine2', 'addressline2': 'addressLine2',
  'address3': 'addressLine3', 'addressline3': 'addressLine3',
  'city': 'locality', 'locality': 'locality',
  'state': 'region', 'region': 'region',
  'zipcode': 'postalCode', 'postal': 'postalCode', 'postalcode': 'postalCode',
  'country': 'countryCode', 'countrycode': 'countryCode',
  }

SERVICE_NAME_TO_ID_MAP = {
  'Drive and Docs': '55656082996',
  'Calendar': '435070579839'
  }

SERVICE_NAME_CHOICES_MAP = {
  'drive': 'Drive and Docs',
  'drive and docs': 'Drive and Docs',
  'googledrive': 'Drive and Docs',
  'gdrive': 'Drive and Docs',
  'calendar': 'Calendar',
  }

PRINTJOB_ASCENDINGORDER_MAP = {
  'createtime': 'CREATE_TIME',
  'status': 'STATUS',
  'title': 'TITLE',
  }
PRINTJOB_DESCENDINGORDER_MAP = {
  'CREATE_TIME': 'CREATE_TIME_DESC',
  'STATUS':  'STATUS_DESC',
  'TITLE': 'TITLE_DESC',
  }

PRINTJOBS_DEFAULT_JOB_LIMIT = 0
PRINTJOBS_DEFAULT_MAX_RESULTS = 100

CALENDAR_REMINDER_METHODS = ['email', 'sms', 'popup',]
CALENDAR_NOTIFICATION_METHODS = ['email', 'sms',]
CALENDAR_NOTIFICATION_TYPES_MAP = {
  'eventcreation': 'eventCreation',
  'eventchange': 'eventChange',
  'eventcancellation': 'eventCancellation',
  'eventresponse': 'eventResponse',
  'agenda': 'agenda',
  }

DRIVEFILE_FIELDS_CHOICES_MAP = {
  'alternatelink': 'alternateLink',
  'appdatacontents': 'appDataContents',
  'cancomment': 'canComment',
  'canreadrevisions': 'canReadRevisions',
  'copyable': 'copyable',
  'copyrequireswriterpermission': 'copyRequiresWriterPermission',
  'createddate': 'createdDate',
  'createdtime': 'createdDate',
  'description': 'description',
  'editable': 'editable',
  'explicitlytrashed': 'explicitlyTrashed',
  'fileextension': 'fileExtension',
  'filesize': 'fileSize',
  'foldercolorrgb': 'folderColorRgb',
  'fullfileextension': 'fullFileExtension',
  'headrevisionid': 'headRevisionId',
  'iconlink': 'iconLink',
  'id': 'id',
  'lastmodifyinguser': 'lastModifyingUser',
  'lastmodifyingusername': 'lastModifyingUserName',
  'lastviewedbyme': 'lastViewedByMeDate',
  'lastviewedbymedate': 'lastViewedByMeDate',
  'lastviewedbymetime': 'lastViewedByMeDate',
  'lastviewedbyuser': 'lastViewedByMeDate',
  'md5': 'md5Checksum',
  'md5checksum': 'md5Checksum',
  'md5sum': 'md5Checksum',
  'mime': 'mimeType',
  'mimetype': 'mimeType',
  'modifiedbyme': 'modifiedByMeDate',
  'modifiedbymedate': 'modifiedByMeDate',
  'modifiedbymetime': 'modifiedByMeDate',
  'modifiedbyuser': 'modifiedByMeDate',
  'modifieddate': 'modifiedDate',
  'modifiedtime': 'modifiedDate',
  'name': 'title',
  'originalfilename': 'originalFilename',
  'ownedbyme': 'ownedByMe',
  'ownernames': 'ownerNames',
  'owners': 'owners',
  'parents': 'parents',
  'permissions': 'permissions',
  'quotabytesused': 'quotaBytesUsed',
  'quotaused': 'quotaBytesUsed',
  'shareable': 'shareable',
  'shared': 'shared',
  'sharedwithmedate': 'sharedWithMeDate',
  'sharedwithmetime': 'sharedWithMeDate',
  'sharinguser': 'sharingUser',
  'spaces': 'spaces',
  'thumbnaillink': 'thumbnailLink',
  'title': 'title',
  'userpermission': 'userPermission',
  'version': 'version',
  'viewedbyme': 'labels(viewed)',
  'viewedbymedate': 'lastViewedByMeDate',
  'viewedbymetime': 'lastViewedByMeDate',
  'viewerscancopycontent': 'labels(restricted)',
  'webcontentlink': 'webContentLink',
  'webviewlink': 'webViewLink',
  'writerscanshare': 'writersCanShare',
  }

DRIVEFILE_LABEL_CHOICES_MAP = {
  'restricted': 'restricted',
  'restrict': 'restricted',
  'starred': 'starred',
  'star': 'starred',
  'trashed': 'trashed',
  'trash': 'trashed',
  'viewed': 'viewed',
  'view': 'viewed',
}

DRIVEFILE_ORDERBY_CHOICES_MAP = {
  'createddate': 'createdDate',
  'folder': 'folder',
  'lastviewedbyme': 'lastViewedByMeDate',
  'lastviewedbymedate': 'lastViewedByMeDate',
  'lastviewedbyuser': 'lastViewedByMeDate',
  'modifiedbyme': 'modifiedByMeDate',
  'modifiedbymedate': 'modifiedByMeDate',
  'modifiedbyuser': 'modifiedByMeDate',
  'modifieddate': 'modifiedDate',
  'name': 'title',
  'quotabytesused': 'quotaBytesUsed',
  'quotaused': 'quotaBytesUsed',
  'recency': 'recency',
  'sharedwithmedate': 'sharedWithMeDate',
  'starred': 'starred',
  'title': 'title',
  'viewedbymedate': 'lastViewedByMeDate',
  }

DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP = {
  'delete': 'purging',
  'trash': 'trashing',
  'untrash': 'untrashing',
  }

DRIVEFILE_LABEL_CHOICES_MAP = {
  'restricted': 'restricted',
  'restrict': 'restricted',
  'starred': 'starred',
  'star': 'starred',
  'trashed': 'trashed',
  'trash': 'trashed',
  'viewed': 'viewed',
  'view': 'viewed',
  }

APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = APPLICATION_VND_GOOGLE_APPS+'document'
MIMETYPE_GA_DRAWING = APPLICATION_VND_GOOGLE_APPS+'drawing'
MIMETYPE_GA_FOLDER = APPLICATION_VND_GOOGLE_APPS+'folder'
MIMETYPE_GA_FORM = APPLICATION_VND_GOOGLE_APPS+'form'
MIMETYPE_GA_FUSIONTABLE = APPLICATION_VND_GOOGLE_APPS+'fusiontable'
MIMETYPE_GA_MAP = APPLICATION_VND_GOOGLE_APPS+'map'
MIMETYPE_GA_PRESENTATION = APPLICATION_VND_GOOGLE_APPS+'presentation'
MIMETYPE_GA_SCRIPT = APPLICATION_VND_GOOGLE_APPS+'script'
MIMETYPE_GA_SITES = APPLICATION_VND_GOOGLE_APPS+'sites'
MIMETYPE_GA_SPREADSHEET = APPLICATION_VND_GOOGLE_APPS+'spreadsheet'

MIMETYPE_CHOICES_MAP = {
  'gdoc': MIMETYPE_GA_DOCUMENT,
  'gdocument': MIMETYPE_GA_DOCUMENT,
  'gdrawing': MIMETYPE_GA_DRAWING,
  'gfolder': MIMETYPE_GA_FOLDER,
  'gdirectory': MIMETYPE_GA_FOLDER,
  'gform': MIMETYPE_GA_FORM,
  'gfusion': MIMETYPE_GA_FUSIONTABLE,
  'gpresentation': MIMETYPE_GA_PRESENTATION,
  'gscript': MIMETYPE_GA_SCRIPT,
  'gsite': MIMETYPE_GA_SITES,
  'gsheet': MIMETYPE_GA_SPREADSHEET,
  'gspreadsheet': MIMETYPE_GA_SPREADSHEET,
  }

DFA_CONVERT = 'convert'
DFA_LOCALFILEPATH = 'localFilepath'
DFA_LOCALFILENAME = 'localFilename'
DFA_LOCALMIMETYPE = 'localMimeType'
DFA_OCR = 'ocr'
DFA_OCRLANGUAGE = 'ocrLanguage'
DFA_PARENTQUERY = 'parentQuery'

NON_DOWNLOADABLE_MIMETYPES = [MIMETYPE_GA_FORM, MIMETYPE_GA_FUSIONTABLE, MIMETYPE_GA_MAP]

GOOGLEDOC_VALID_EXTENSIONS_MAP = {
  MIMETYPE_GA_DRAWING: ['.jpeg', '.jpg', '.pdf', '.png', '.svg'],
  MIMETYPE_GA_DOCUMENT: ['.docx', '.html', '.odt', '.pdf', '.rtf', '.txt', '.zip'],
  MIMETYPE_GA_PRESENTATION: ['.pdf', '.pptx', '.odp', '.txt'],
  MIMETYPE_GA_SPREADSHEET: ['.csv', '.ods', '.pdf', '.xlsx', '.zip'],
  }

MACOS_CODENAMES = {
  6:  'Snow Leopard',
  7:  'Lion',
  8:  'Mountain Lion',
  9:  'Mavericks',
  10: 'Yosemite',
  11: 'El Capitan',
  12: 'Sierra',
  13: 'High Sierra',
  14: 'Mojave',
  15: 'Catalina'
  }

_MICROSOFT_FORMATS_LIST = [
  {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'ext': '.docx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template', 'ext': '.dotx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'ext': '.pptx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.template', 'ext': '.potx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'ext': '.xlsx'},
  {'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template', 'ext': '.xltx'},
  {'mime': 'application/msword', 'ext': '.doc'},
  {'mime': 'application/msword', 'ext': '.dot'},
  {'mime': 'application/vnd.ms-powerpoint', 'ext': '.ppt'},
  {'mime': 'application/vnd.ms-powerpoint', 'ext': '.pot'},
  {'mime': 'application/vnd.ms-excel', 'ext': '.xls'},
  {'mime': 'application/vnd.ms-excel', 'ext': '.xlt'}
  ]

DOCUMENT_FORMATS_MAP = {
  'csv': [{'mime': 'text/csv', 'ext': '.csv'}],
  'doc': [{'mime': 'application/msword', 'ext': '.doc'}],
  'dot': [{'mime': 'application/msword', 'ext': '.dot'}],
  'docx': [{'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'ext': '.docx'}],
  'dotx': [{'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template', 'ext': '.dotx'}],
  'epub': [{'mime': 'application/epub+zip', 'ext': '.epub'}],
  'html': [{'mime': 'text/html', 'ext': '.html'}],
  'jpeg': [{'mime': 'image/jpeg', 'ext': '.jpeg'}],
  'jpg': [{'mime': 'image/jpeg', 'ext': '.jpg'}],
  'mht': [{'mime': 'message/rfc822', 'ext': 'mht'}],
  'odp': [{'mime': 'application/vnd.oasis.opendocument.presentation', 'ext': '.odp'}],
  'ods': [{'mime': 'application/x-vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'},
          {'mime': 'application/vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'}],
  'odt': [{'mime': 'application/vnd.oasis.opendocument.text', 'ext': '.odt'}],
  'pdf': [{'mime': 'application/pdf', 'ext': '.pdf'}],
  'png': [{'mime': 'image/png', 'ext': '.png'}],
  'ppt': [{'mime': 'application/vnd.ms-powerpoint', 'ext': '.ppt'}],
  'pot': [{'mime': 'application/vnd.ms-powerpoint', 'ext': '.pot'}],
  'potx': [{'mime': 'application/vnd.openxmlformats-officedocument.presentationml.template', 'ext': '.potx'}],
  'pptx': [{'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'ext': '.pptx'}],
  'rtf': [{'mime': 'application/rtf', 'ext': '.rtf'}],
  'svg': [{'mime': 'image/svg+xml', 'ext': '.svg'}],
  'tsv': [{'mime': 'text/tab-separated-values', 'ext': '.tsv'},
          {'mime': 'text/tsv', 'ext': '.tsv'}],
  'txt': [{'mime': 'text/plain', 'ext': '.txt'}],
  'xls': [{'mime': 'application/vnd.ms-excel', 'ext': '.xls'}],
  'xlt': [{'mime': 'application/vnd.ms-excel', 'ext': '.xlt'}],
  'xlsx': [{'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'ext': '.xlsx'}],
  'xltx': [{'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template', 'ext': '.xltx'}],
  'zip': [{'mime': 'application/zip', 'ext': '.zip'}],
  'ms': _MICROSOFT_FORMATS_LIST,
  'microsoft': _MICROSOFT_FORMATS_LIST,
  'micro$oft': _MICROSOFT_FORMATS_LIST,
  'openoffice': [{'mime': 'application/vnd.oasis.opendocument.presentation', 'ext': '.odp'},
                 {'mime': 'application/x-vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'},
                 {'mime': 'application/vnd.oasis.opendocument.spreadsheet', 'ext': '.ods'},
                 {'mime': 'application/vnd.oasis.opendocument.text', 'ext': '.odt'}],
  }

REFRESH_PERM_ERRORS = [
  'invalid_grant: reauth related error (rapt_required)', # no way to reauth today
  'invalid_grant: Token has been expired or revoked.',
  ]

DNS_ERROR_CODES_MAP = {
  1: 'DNS Query Format Error',
  2: 'Server failed to complete the DNS request',
  3: 'Domain name does not exist',
  4: 'Function not implemented',
  5: 'The server refused to answer for the query',
  6: 'Name that should not exist, does exist',
  7: 'RRset that should not exist, does exist',
  8: 'Server not authoritative for the zone',
  9: 'Name not in zone'
  }

EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP = {
  'ARCHIVE': 'archive',
  'DELETE': 'trash',
  'KEEP': 'leaveInInBox',
  'MARK_READ': 'markRead',
  'archive': 'ARCHIVE',
  'trash': 'DELETE',
  'leaveInInbox': 'KEEP',
  'markRead': 'MARK_READ',
  }

EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICES_MAP = {
  'archive': 'archive',
  'deleteforever': 'deleteForever',
  'trash': 'trash',
  }

EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES = ['0', '1000', '2000', '5000', '10000']

EMAILSETTINGS_POP_ENABLE_FOR_CHOICES_MAP = {
  'allmail': 'allMail',
  'fromnowon': 'fromNowOn',
  'mailfromnowon': 'fromNowOn',
  'newmail': 'fromNowOn',
  }

EMAILSETTINGS_FORWARD_POP_ACTION_CHOICES_MAP = {
  'archive': 'archive',
  'delete': 'trash',
  'keep': 'leaveInInbox',
  'leaveininbox': 'leaveInInbox',
  'markread': 'markRead',
  'trash': 'trash',
  }

RT_PATTERN = re.compile(r'(?s){RT}.*?{(.+?)}.*?{/RT}')
RT_OPEN_PATTERN = re.compile(r'{RT}')
RT_CLOSE_PATTERN = re.compile(r'{/RT}')
RT_STRIP_PATTERN = re.compile(r'(?s){RT}.*?{/RT}')
RT_TAG_REPLACE_PATTERN = re.compile(r'{(.*?)}')

LOWERNUMERIC_CHARS = string.ascii_lowercase+string.digits
ALPHANUMERIC_CHARS = LOWERNUMERIC_CHARS+string.ascii_uppercase
URL_SAFE_CHARS = ALPHANUMERIC_CHARS+'-._~'
PASSWORD_SAFE_CHARS = ALPHANUMERIC_CHARS+string.punctuation+' '
FILENAME_SAFE_CHARS = ALPHANUMERIC_CHARS+'-_.() '

FILTER_ADD_LABEL_TO_ARGUMENT_MAP = {
  'IMPORTANT': 'important',
  'STARRED': 'star',
  'TRASH': 'trash',
  }

FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP = {
  'IMPORTANT': 'notimportant',
  'UNREAD': 'markread',
  'INBOX': 'archive',
  'SPAM': 'neverspam',
  }

FILTER_CRITERIA_CHOICES_MAP = {
  'excludechats': 'excludeChats',
  'from': 'from',
  'hasattachment': 'hasAttachment',
  'haswords': 'query',
  'musthaveattachment': 'hasAttachment',
  'negatedquery': 'negatedQuery',
  'nowords': 'negatedQuery',
  'query': 'query',
  'size': 'size',
  'subject': 'subject',
  'to': 'to',
  }
FILTER_ACTION_CHOICES = [
  'archive', 'forward', 'important', 'label',
  'markread', 'neverspam', 'notimportant', 'star', 'trash',
  ]

VAULT_MATTER_ACTIONS = [
  'reopen',
  'undelete',
  'close',
  'delete',
  ]

CROS_ARGUMENT_TO_PROPERTY_MAP = {
  'activetimeranges': ['activeTimeRanges.activeTime', 'activeTimeRanges.date'],
  'annotatedassetid': ['annotatedAssetId',],
  'annotatedlocation': ['annotatedLocation',],
  'annotateduser': ['annotatedUser',],
  'asset': ['annotatedAssetId',],
  'assetid': ['annotatedAssetId',],
  'autoupdateexpiration': ['autoUpdateExpiration',],
  'bootmode': ['bootMode',],
  'cpustatusreports': ['cpuStatusReports',],
  'devicefiles': ['deviceFiles',],
  'deviceid': ['deviceId',],
  'dockmacaddress': ['dockMacAddress',],
  'diskvolumereports': ['diskVolumeReports',],
  'ethernetmacaddress': ['ethernetMacAddress',],
  'ethernetmacaddress0': ['ethernetMacAddress0',],
  'firmwareversion': ['firmwareVersion',],
  'lastenrollmenttime': ['lastEnrollmentTime',],
  'lastsync': ['lastSync',],
  'location': ['annotatedLocation',],
  'macaddress': ['macAddress',],
  'manufacturedate': ['manufactureDate',],
  'meid': ['meid',],
  'model': ['model',],
  'notes': ['notes',],
  'ordernumber': ['orderNumber',],
  'org': ['orgUnitPath',],
  'orgunitpath': ['orgUnitPath',],
  'osversion': ['osVersion',],
  'ou': ['orgUnitPath',],
  'platformversion': ['platformVersion',],
  'recentusers': ['recentUsers.email', 'recentUsers.type'],
  'serialnumber': ['serialNumber',],
  'status': ['status',],
  'supportenddate': ['supportEndDate',],
  'systemramtotal': ['systemRamTotal',],
  'systemramfreereports': ['systemRamFreeReports',],
  'tag': ['annotatedAssetId',],
  'timeranges': ['activeTimeRanges.activeTime', 'activeTimeRanges.date'],
  'times': ['activeTimeRanges.activeTime', 'activeTimeRanges.date'],
  'tpmversioninfo': ['tpmVersionInfo',],
  'user': ['annotatedUser',],
  'users': ['recentUsers.email', 'recentUsers.type'],
  'willautorenew': ['willAutoRenew',],
  }

CROS_BASIC_FIELDS_LIST = ['deviceId', 'annotatedAssetId', 'annotatedLocation', 'annotatedUser', 'lastSync', 'notes', 'serialNumber', 'status']

CROS_SCALAR_PROPERTY_PRINT_ORDER = [
  'orgUnitPath',
  'annotatedAssetId',
  'annotatedLocation',
  'annotatedUser',
  'lastSync',
  'notes',
  'serialNumber',
  'status',
  'model',
  'firmwareVersion',
  'platformVersion',
  'osVersion',
  'bootMode',
  'meid',
  'dockMacAddress',
  'ethernetMacAddress',
  'ethernetMacAddress0',
  'macAddress',
  'systemRamTotal',
  'lastEnrollmentTime',
  'orderNumber',
  'manufactureDate',
  'supportEndDate',
  'autoUpdateExpiration',
  'tpmVersionInfo',
  'willAutoRenew',
  ]

CROS_RECENT_USERS_ARGUMENTS = ['recentusers', 'users']
CROS_ACTIVE_TIME_RANGES_ARGUMENTS = ['timeranges', 'activetimeranges', 'times']
CROS_DEVICE_FILES_ARGUMENTS = ['devicefiles', 'files']
CROS_CPU_STATUS_REPORTS_ARGUMENTS = ['cpustatusreports',]
CROS_DISK_VOLUME_REPORTS_ARGUMENTS = ['diskvolumereports',]
CROS_SYSTEM_RAM_FREE_REPORTS_ARGUMENTS = ['systemramfreereports',]
CROS_LISTS_ARGUMENTS = CROS_ACTIVE_TIME_RANGES_ARGUMENTS+CROS_RECENT_USERS_ARGUMENTS+CROS_DEVICE_FILES_ARGUMENTS+CROS_CPU_STATUS_REPORTS_ARGUMENTS+CROS_DISK_VOLUME_REPORTS_ARGUMENTS+CROS_SYSTEM_RAM_FREE_REPORTS_ARGUMENTS
CROS_START_ARGUMENTS = ['start', 'startdate', 'oldestdate']
CROS_END_ARGUMENTS = ['end', 'enddate']

# From https://www.chromium.org/chromium-os/tpm_firmware_update
CROS_TPM_VULN_VERSIONS = ['41f', '420', '628', '8520',]
CROS_TPM_FIXED_VERSIONS = ['422', '62b', '8521',]

COLLABORATIVE_INBOX_ATTRIBUTES = [
  'whoCanAddReferences',
  'whoCanAssignTopics',
  'whoCanEnterFreeFormTags',
  'whoCanMarkDuplicate',
  'whoCanMarkFavoriteReplyOnAnyTopic',
  'whoCanMarkFavoriteReplyOnOwnTopic',
  'whoCanMarkNoResponseNeeded',
  'whoCanModifyTagsAndCategories',
  'whoCanTakeTopics',
  'whoCanUnassignTopic',
  'whoCanUnmarkFavoriteReplyOnAnyTopic',
  'favoriteRepliesOnTop',
  ]

GROUP_SETTINGS_LIST_ATTRIBUTES = set([
  # ACL choices
  'whoCanAdd',
  'whoCanApproveMembers',
  'whoCanApproveMessages',
  'whoCanAssignTopics',
  'whoCanAssistContent',
  'whoCanBanUsers',
  'whoCanContactOwner',
  'whoCanDeleteAnyPost',
  'whoCanDeleteTopics',
  'whoCanDiscoverGroup',
  'whoCanEnterFreeFormTags',
  'whoCanHideAbuse',
  'whoCanInvite',
  'whoCanJoin',
  'whoCanLeaveGroup',
  'whoCanLockTopics',
  'whoCanMakeTopicsSticky',
  'whoCanMarkDuplicate',
  'whoCanMarkFavoriteReplyOnAnyTopic',
  'whoCanMarkFavoriteReplyOnOwnTopic',
  'whoCanMarkNoResponseNeeded',
  'whoCanModerateContent',
  'whoCanModerateMembers',
  'whoCanModifyMembers',
  'whoCanModifyTagsAndCategories',
  'whoCanMoveTopicsIn',
  'whoCanMoveTopicsOut',
  'whoCanPostAnnouncements',
  'whoCanPostMessage',
  'whoCanTakeTopics',
  'whoCanUnassignTopic',
  'whoCanUnmarkFavoriteReplyOnAnyTopic',
  'whoCanViewGroup',
  'whoCanViewMembership',
  # Miscellaneous hoices
  'messageModerationLevel',
  'replyTo',
  'spamModerationLevel',
  ])
GROUP_SETTINGS_BOOLEAN_ATTRIBUTES = set([
  'allowExternalMembers',
  'allowGoogleCommunication',
  'allowWebPosting',
  'archiveOnly',
  'enableCollaborativeInbox',
  'favoriteRepliesOnTop',
  'includeCustomFooter',
  'includeInGlobalAddressList',
  'isArchived',
  'membersCanPostAsTheGroup',
  'sendMessageDenyNotification',
  'showInGroupDirectory',
  ])

#
# Global variables
#
# The following GM_XXX constants are arbitrary but must be unique
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
GM_SYSEXITRC = 'sxrc'
# Path to gam
GM_GAM_PATH = 'gpth'
# Python source, PyInstaller or StaticX?
GM_GAM_TYPE = 'gtyp'
# Are we on Windows?
GM_WINDOWS = 'wndo'
# Encodings
GM_SYS_ENCODING = 'syen'
# Extra arguments to pass to GAPI functions
GM_EXTRA_ARGS_DICT = 'exad'
# Current API services
GM_CURRENT_API_SERVICES = 'caps'
# Current API user
GM_CURRENT_API_USER = 'capu'
# Current API scope
GM_CURRENT_API_SCOPES = 'scoc'
# Values retrieved from oauth2service.json
GM_OAUTH2SERVICE_JSON_DATA = 'oajd'
GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID = 'oaci'
# File containing time of last GAM update check
GM_LAST_UPDATE_CHECK_TXT = 'lupc'
# Dictionary mapping OrgUnit ID to Name
GM_MAP_ORGUNIT_ID_TO_NAME = 'oi2n'
# Dictionary mapping Role ID to Name
GM_MAP_ROLE_ID_TO_NAME = 'ri2n'
# Dictionary mapping Role Name to ID
GM_MAP_ROLE_NAME_TO_ID = 'rn2i'
# Dictionary mapping User ID to Name
GM_MAP_USER_ID_TO_NAME = 'ui2n'
# GAM cache directory. If no_cache is True, this variable will be set to None
GM_CACHE_DIR = 'gacd'
# Reset GAM cache directory after discovery
GM_CACHE_DISCOVERY_ONLY = 'gcdo'
# Dictionary mapping Building ID to Name
GM_MAP_BUILDING_ID_TO_NAME = 'bi2n'
# Dictionary mapping Building Name to ID
GM_MAP_BUILDING_NAME_TO_ID = 'bn2i'

#
_DEFAULT_CHARSET = UTF8
_FN_CLIENT_SECRETS_JSON = 'client_secrets.json'
_FN_OAUTH2SERVICE_JSON = 'oauth2service.json'
_FN_OAUTH2_TXT = 'oauth2.txt'
#
GM_Globals = {
  GM_SYSEXITRC: 0,
  GM_GAM_PATH: None,
  GM_GAM_TYPE: None,
  GM_WINDOWS: os.name == 'nt',
  GM_SYS_ENCODING: _DEFAULT_CHARSET,
  GM_EXTRA_ARGS_DICT:  {'prettyPrint': False},
  GM_CURRENT_API_SERVICES: {},
  GM_CURRENT_API_USER: None,
  GM_CURRENT_API_SCOPES: [],
  GM_OAUTH2SERVICE_JSON_DATA: None,
  GM_OAUTH2SERVICE_ACCOUNT_CLIENT_ID: None,
  GM_LAST_UPDATE_CHECK_TXT: '',
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
# Automatically generate gam batch command if number of users specified in gam users xxx command exceeds this number
# Default: 0, don't automatically generate gam batch commands
GC_AUTO_BATCH_MIN = 'auto_batch_min'
# When processing items in batches, how many should be processed in each batch
GC_BATCH_SIZE = 'batch_size'
# GAM cache directory. If no_cache is specified, this variable will be set to None
GC_CACHE_DIR = 'cache_dir'
# GAM cache discovery only. If no_cache is False, only API discovery calls will be cached
GC_CACHE_DISCOVERY_ONLY = 'cache_discovery_only'
# Character set of batch, csv, data files
GC_CHARSET = 'charset'
# Path to client_secrets.json
GC_CLIENT_SECRETS_JSON = 'client_secrets_json'
# GAM config directory containing client_secrets.json, oauth2.txt, oauth2service.json, extra_args.txt
GC_CONFIG_DIR = 'config_dir'
# custmerId from gam.cfg or retrieved from Google
GC_CUSTOMER_ID = 'customer_id'
# If debug_level > 0: extra_args[u'prettyPrint'] = True, httplib2.debuglevel = gam_debug_level, appsObj.debug = True
GC_DEBUG_LEVEL = 'debug_level'
# ID Token decoded from OAuth 2.0 refresh token response. Includes hd (domain) and email of authorized user
GC_DECODED_ID_TOKEN = 'decoded_id_token'
# Domain obtained from gam.cfg or oauth2.txt
GC_DOMAIN = 'domain'
# Google Drive download directory
GC_DRIVE_DIR = 'drive_dir'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doRequestOAuth prints a link and waits for the verification code when oauth2.txt is being created
GC_NO_BROWSER = 'no_browser'
# oauth_browser forces usage of web server OAuth flow that proved problematic.
GC_OAUTH_BROWSER = 'oauth_browser'
# Disable GAM API caching
GC_NO_CACHE = 'no_cache'
# Disable GAM update check
GC_NO_UPDATE_CHECK = 'no_update_check'
# Number of threads for gam batch
GC_NUM_THREADS = 'num_threads'
# Path to oauth2.txt
GC_OAUTH2_TXT = 'oauth2_txt'
# Path to oauth2service.json
GC_OAUTH2SERVICE_JSON = 'oauth2service_json'
# Default section to use for processing
GC_SECTION = 'section'
# Add (n/m) to end of messages if number of items to be processed exceeds this number
GC_SHOW_COUNTS_MIN = 'show_counts_min'
# Enable/disable "Getting ... " messages
GC_SHOW_GETTINGS = 'show_gettings'
# GAM config directory containing json discovery files
GC_SITE_DIR = 'site_dir'
# CSV Columns GAM should show on CSV output
GC_CSV_HEADER_FILTER = 'csv_header_filter'
# CSV Columns GAM should not show on CSV output
GC_CSV_HEADER_DROP_FILTER = 'csv_header_drop_filter'
# CSV Rows GAM should filter
GC_CSV_ROW_FILTER = 'csv_row_filter'
# Minimum TLS Version required for HTTPS connections
GC_TLS_MIN_VERSION = 'tls_min_ver'
# Maximum TLS Version used for HTTPS connections
GC_TLS_MAX_VERSION = 'tls_max_ver'
# Path to certificate authority file for validating TLS hosts
GC_CA_FILE = 'ca_file'

tls_min = "TLSv1_2" if hasattr(ssl.SSLContext(), "minimum_version") else None
GC_Defaults = {
  GC_AUTO_BATCH_MIN: 0,
  GC_BATCH_SIZE: 50,
  GC_CACHE_DIR: '',
  GC_CACHE_DISCOVERY_ONLY: True,
  GC_CHARSET: _DEFAULT_CHARSET,
  GC_CLIENT_SECRETS_JSON: _FN_CLIENT_SECRETS_JSON,
  GC_CONFIG_DIR: '',
  GC_CUSTOMER_ID: MY_CUSTOMER,
  GC_DEBUG_LEVEL: 0,
  GC_DECODED_ID_TOKEN: '',
  GC_DOMAIN: '',
  GC_DRIVE_DIR: '',
  GC_NO_BROWSER: False,
  GC_NO_CACHE: False,
  GC_NO_UPDATE_CHECK: False,
  GC_NUM_THREADS: 25,
  GC_OAUTH_BROWSER: False,
  GC_OAUTH2_TXT: _FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: _FN_OAUTH2SERVICE_JSON,
  GC_SECTION: '',
  GC_SHOW_COUNTS_MIN: 0,
  GC_SHOW_GETTINGS: True,
  GC_SITE_DIR: '',
  GC_CSV_HEADER_FILTER: '',
  GC_CSV_HEADER_DROP_FILTER: '',
  GC_CSV_ROW_FILTER: '',
  GC_TLS_MIN_VERSION: tls_min,
  GC_TLS_MAX_VERSION: None,
  GC_CA_FILE: None,
  }

GC_Values = {}

GC_TYPE_BOOLEAN = 'bool'
GC_TYPE_CHOICE = 'choi'
GC_TYPE_DIRECTORY = 'dire'
GC_TYPE_EMAIL = 'emai'
GC_TYPE_FILE = 'file'
GC_TYPE_HEADERFILTER = 'heaf'
GC_TYPE_INTEGER = 'inte'
GC_TYPE_LANGUAGE = 'lang'
GC_TYPE_ROWFILTER = 'rowf'
GC_TYPE_STRING = 'stri'

GC_VAR_TYPE = 'type'
GC_VAR_LIMITS = 'lmit'

GC_VAR_INFO = {
  GC_AUTO_BATCH_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_BATCH_SIZE: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_CACHE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CACHE_DISCOVERY_ONLY: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_CHARSET: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_CLIENT_SECRETS_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_CONFIG_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CUSTOMER_ID: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DEBUG_LEVEL: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_DECODED_ID_TOKEN: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DOMAIN: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DRIVE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_NO_BROWSER: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_CACHE: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NUM_THREADS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, None)},
  GC_OAUTH_BROWSER: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_OAUTH2_TXT: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_SECTION: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_SHOW_COUNTS_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_SITE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_CSV_HEADER_FILTER: {GC_VAR_TYPE: GC_TYPE_HEADERFILTER},
  GC_CSV_HEADER_DROP_FILTER: {GC_VAR_TYPE: GC_TYPE_HEADERFILTER},
  GC_CSV_ROW_FILTER: {GC_VAR_TYPE: GC_TYPE_ROWFILTER},
  GC_TLS_MIN_VERSION: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_TLS_MAX_VERSION: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_CA_FILE: {GC_VAR_TYPE: GC_TYPE_FILE},
  }
# Google API constants

NEVER_TIME = '1970-01-01T00:00:00.000Z'
ROLE_MANAGER = 'MANAGER'
ROLE_MEMBER = 'MEMBER'
ROLE_OWNER = 'OWNER'
PROJECTION_CHOICES_MAP = {'basic': 'BASIC', 'full': 'FULL',}
SORTORDER_CHOICES_MAP = {'ascending': 'ASCENDING', 'descending': 'DESCENDING',}
#
CLEAR_NONE_ARGUMENT = ['clear', 'none',]
#
MESSAGE_API_ACCESS_CONFIG = 'API access is configured in your Control Panel under: Security-Show more-Advanced settings-Manage API client access'
MESSAGE_API_ACCESS_DENIED = 'API access Denied.\n\nPlease make sure the Client ID: {0} is authorized for the API Scope(s): {1}'
MESSAGE_GAM_EXITING_FOR_UPDATE = 'GAM is now exiting so that you can overwrite this old version with the latest release'
MESSAGE_GAM_OUT_OF_MEMORY = 'GAM has run out of memory. If this is a large G Suite instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS = 'Header "{0}" not found in CSV headers of "{1}".'
MESSAGE_HIT_CONTROL_C_TO_UPDATE = '\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can create a file named noupdatecheck.txt in the same location as gam.py or gam.exe and GAM won\'t ever check for updates.'
MESSAGE_INVALID_JSON = 'The file {0} has an invalid format.'
MESSAGE_NO_DISCOVERY_INFORMATION = 'No online discovery doc and {0} does not exist locally'
MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE = 'Cowardly refusing to perform migration due to lack of target drive space. Source size: {0}mb Target Free: {1}mb'
MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = 'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
MESSAGE_SERVICE_NOT_APPLICABLE = 'Service not applicable for this address: {0}. Please make sure service is enabled for user and run\n\ngam user <user> check serviceaccount\n\nfor further instructions'
MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON = 'Please run\n\ngam create project\ngam user <user> check serviceaccount\n\nto create and configure a service account.'
MESSAGE_UPDATE_GAM_TO_64BIT = "You're running a 32-bit version of GAM on a 64-bit version of Windows, upgrade to a windows-x86_64 version of GAM"
MESSAGE_YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE_BY = 'Your system time differs from %s by %s'

USER_ADDRESS_TYPES = ['home', 'work', 'other']
USER_EMAIL_TYPES = ['home', 'work', 'other']
USER_EXTERNALID_TYPES = ['account', 'customer', 'login_id', 'network', 'organization']
USER_GENDER_TYPES = ['female', 'male', 'unknown']
USER_IM_TYPES = ['home', 'work', 'other']
USER_KEYWORD_TYPES = ['occupation', 'outlook']
USER_LOCATION_TYPES = ['default', 'desk']
USER_ORGANIZATION_TYPES = ['domain_only', 'school', 'unknown', 'work']
USER_PHONE_TYPES = ['assistant', 'callback', 'car', 'company_main',
                    'grand_central', 'home', 'home_fax', 'isdn', 'main',
                    'mobile', 'other', 'other_fax', 'pager', 'radio',
                    'telex', 'tty_tdd', 'work', 'work_fax', 'work_mobile',
                    'work_pager']
USER_RELATION_TYPES = ['admin_assistant', 'assistant', 'brother', 'child',
                       'domestic_partner', 'dotted_line_manager',
                       'exec_assistant', 'father', 'friend', 'manager',
                       'mother', 'parent', 'partner', 'referred_by',
                       'relative', 'sister', 'spouse']
USER_WEBSITE_TYPES = ['app_install_page', 'blog', 'ftp', 'home',
                      'home_page', 'other', 'profile', 'reservations',
                      'work']

WEBCOLOR_MAP = {
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aqua': '#00ffff',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'black': '#000000',
    'blanchedalmond': '#ffebcd',
    'blue': '#0000ff',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgrey': '#a9a9a9',
    'darkgreen': '#006400',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'fuchsia': '#ff00ff',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'gray': '#808080',
    'grey': '#808080',
    'green': '#008000',
    'greenyellow': '#adff2f',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgray': '#d3d3d3',
    'lightgrey': '#d3d3d3',
    'lightgreen': '#90ee90',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'lime': '#00ff00',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'maroon': '#800000',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'navy': '#000080',
    'oldlace': '#fdf5e6',
    'olive': '#808000',
    'olivedrab': '#6b8e23',
    'orange': '#ffa500',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#db7093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'purple': '#800080',
    'red': '#ff0000',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'silver': '#c0c0c0',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'teal': '#008080',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'white': '#ffffff',
    'whitesmoke': '#f5f5f5',
    'yellow': '#ffff00',
    'yellowgreen': '#9acd32',
}

# Gmail label colors
LABEL_COLORS = [
  '#000000', '#076239', '#0b804b', '#149e60', '#16a766', '#1a764d', '#1c4587', '#285bac',
  '#2a9c68', '#3c78d8', '#3dc789', '#41236d', '#434343', '#43d692', '#44b984', '#4a86e8',
  '#653e9b', '#666666', '#68dfa9', '#6d9eeb', '#822111', '#83334c', '#89d3b2', '#8e63ce',
  '#999999', '#a0eac9', '#a46a21', '#a479e2', '#a4c2f4', '#aa8831', '#ac2b16', '#b65775',
  '#b694e8', '#b9e4d0', '#c6f3de', '#c9daf8', '#cc3a21', '#cccccc', '#cf8933', '#d0bcf1',
  '#d5ae49', '#e07798', '#e4d7f5', '#e66550', '#eaa041', '#efa093', '#efefef', '#f2c960',
  '#f3f3f3', '#f691b3', '#f6c5be', '#f7a7c0', '#fad165', '#fb4c2f', '#fbc8d9', '#fcda83',
  '#fcdee8', '#fce8b3', '#fef1d1', '#ffad47', '#ffbc6b', '#ffd6a2', '#ffe6c7', '#ffffff',
  ]

# Valid language codes
LANGUAGE_CODES_MAP = {
  'ach': 'ach', 'af': 'af', 'ag': 'ga', 'ak': 'ak', 'am': 'am', 'ar': 'ar', 'az': 'az', #Luo, Afrikaans, Irish, Akan, Amharic, Arabica, Azerbaijani
  'be': 'be', 'bem': 'bem', 'bg': 'bg', 'bn': 'bn', 'br': 'br', 'bs': 'bs', 'ca': 'ca', #Belarusian, Bemba, Bulgarian, Bengali, Breton, Bosnian, Catalan
  'chr': 'chr', 'ckb': 'ckb', 'co': 'co', 'crs': 'crs', 'cs': 'cs', 'cy': 'cy', 'da': 'da', #Cherokee, Kurdish (Sorani), Corsican, Seychellois Creole, Czech, Welsh, Danish
  'de': 'de', 'ee': 'ee', 'el': 'el', 'en': 'en', 'en-gb': 'en-GB', 'en-us': 'en-US', 'eo': 'eo', #German, Ewe, Greek, English, English (UK), English (US), Esperanto
  'es': 'es', 'es-419': 'es-419', 'et': 'et', 'eu': 'eu', 'fa': 'fa', 'fi': 'fi', 'fo': 'fo', #Spanish, Spanish (Latin American), Estonian, Basque, Persian, Finnish, Faroese
  'fr': 'fr', 'fr-ca': 'fr-ca', 'fy': 'fy', 'ga': 'ga', 'gaa': 'gaa', 'gd': 'gd', 'gl': 'gl', #French, French (Canada), Frisian, Irish, Ga, Scots Gaelic, Galician
  'gn': 'gn', 'gu': 'gu', 'ha': 'ha', 'haw': 'haw', 'he': 'he', 'hi': 'hi', 'hr': 'hr', #Guarani, Gujarati, Hausa, Hawaiian, Hebrew, Hindi, Croatian
  'ht': 'ht', 'hu': 'hu', 'hy': 'hy', 'ia': 'ia', 'id': 'id', 'ig': 'ig', 'in': 'in', #Haitian Creole, Hungarian, Armenian, Interlingua, Indonesian, Igbo, in
  'is': 'is', 'it': 'it', 'iw': 'iw', 'ja': 'ja', 'jw': 'jw', 'ka': 'ka', 'kg': 'kg', #Icelandic, Italian, Hebrew, Japanese, Javanese, Georgian, Kongo
  'kk': 'kk', 'km': 'km', 'kn': 'kn', 'ko': 'ko', 'kri': 'kri', 'ku': 'ku', 'ky': 'ky', #Kazakh, Khmer, Kannada, Korean, Krio (Sierra Leone), Kurdish, Kyrgyz
  'la': 'la', 'lg': 'lg', 'ln': 'ln', 'lo': 'lo', 'loz': 'loz', 'lt': 'lt', 'lua': 'lua', #Latin, Luganda, Lingala, Laothian, Lozi, Lithuanian, Tshiluba
  'lv': 'lv', 'mfe': 'mfe', 'mg': 'mg', 'mi': 'mi', 'mk': 'mk', 'ml': 'ml', 'mn': 'mn', #Latvian, Mauritian Creole, Malagasy, Maori, Macedonian, Malayalam, Mongolian
  'mo': 'mo', 'mr': 'mr', 'ms': 'ms', 'mt': 'mt', 'my': 'my', 'ne': 'ne', 'nl': 'nl', #Moldavian, Marathi, Malay, Maltese, Burmese, Nepali, Dutch
  'nn': 'nn', 'no': 'no', 'nso': 'nso', 'ny': 'ny', 'nyn': 'nyn', 'oc': 'oc', 'om': 'om', #Norwegian (Nynorsk), Norwegian, Northern Sotho, Chichewa, Runyakitara, Occitan, Oromo
  'or': 'or', 'pa': 'pa', 'pcm': 'pcm', 'pl': 'pl', 'ps': 'ps', 'pt-br': 'pt-BR', 'pt-pt': 'pt-PT', #Oriya, Punjabi, Nigerian Pidgin, Polish, Pashto, Portuguese (Brazil), Portuguese (Portugal)
  'qu': 'qu', 'rm': 'rm', 'rn': 'rn', 'ro': 'ro', 'ru': 'ru', 'rw': 'rw', 'sd': 'sd', #Quechua, Romansh, Kirundi, Romanian, Russian, Kinyarwanda, Sindhi
  'sh': 'sh', 'si': 'si', 'sk': 'sk', 'sl': 'sl', 'sn': 'sn', 'so': 'so', 'sq': 'sq', #Serbo-Croatian, Sinhalese, Slovak, Slovenian, Shona, Somali, Albanian
  'sr': 'sr', 'sr-me': 'sr-ME', 'st': 'st', 'su': 'su', 'sv': 'sv', 'sw': 'sw', 'ta': 'ta', #Serbian, Montenegrin, Sesotho, Sundanese, Swedish, Swahili, Tamil
  'te': 'te', 'tg': 'tg', 'th': 'th', 'ti': 'ti', 'tk': 'tk', 'tl': 'tl', 'tn': 'tn', #Telugu, Tajik, Thai, Tigrinya, Turkmen, Tagalog, Setswana
  'to': 'to', 'tr': 'tr', 'tt': 'tt', 'tum': 'tum', 'tw': 'tw', 'ug': 'ug', 'uk': 'uk', #Tonga, Turkish, Tatar, Tumbuka, Twi, Uighur, Ukrainian
  'ur': 'ur', 'uz': 'uz', 'vi': 'vi', 'wo': 'wo', 'xh': 'xh', 'yi': 'yi', 'yo': 'yo', #Urdu, Uzbek, Vietnamese, Wolof, Xhosa, Yiddish, Yoruba
  'zh-cn': 'zh-CN', 'zh-hk': 'zh-HK', 'zh-tw': 'zh-TW', 'zu': 'zu', #Chinese (Simplified), Chinese (Hong Kong/Traditional), Chinese (Taiwan/Traditional), Zulu
  }

# maxResults exception values for API list calls. Should only be listed if:
#   - discovery doc does not specify maximum value (we use maximum value if it
#     exists, not this)
#   - actual max API returns with maxResults=<bigNum>  > default API returns
#     when maxResults isn't specified (we should use default otherwise by not
#     setting maxResults)

MAX_RESULTS_API_EXCEPTIONS = {
  'calendar.acl.list': 250,
  'calendar.calendarList.list': 250,
  'calendar.events.list': 2500,
  'calendar.settings.list': 250,
  'directory.chromeosdevices.list': 200,
  'drive.files.list': 1000,
  }

ONE_KILO_BYTES = 1000
ONE_MEGA_BYTES = 1000000
ONE_GIGA_BYTES = 1000000000

DELTA_DATE_PATTERN = re.compile(r'^([+-])(\d+)([dwy])$')
DELTA_DATE_FORMAT_REQUIRED = '(+|-)<Number>(d|w|y)'

DELTA_TIME_PATTERN = re.compile(r'^([+-])(\d+)([mhdwy])$')
DELTA_TIME_FORMAT_REQUIRED = '(+|-)<Number>(m|h|d|w|y)'

YYYYMMDD_FORMAT = '%Y-%m-%d'
YYYYMMDD_FORMAT_REQUIRED = 'yyyy-mm-dd'

YYYYMMDDTHHMMSS_FORMAT_REQUIRED = 'yyyy-mm-ddThh:mm:ss[.fff](Z|(+|-(hh:mm)))'

YYYYMMDD_PATTERN = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')

UID_PATTERN = re.compile(r'u?id: ?(.+)', re.IGNORECASE)
