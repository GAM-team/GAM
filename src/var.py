import os
import ssl
import string
import sys
import platform
import re

gam_author = 'Jay Lee <jay0lee@gmail.com>'
gam_version = '4.87'
gam_license = 'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

GAM_URL = 'https://git.io/gam'
GAM_INFO = 'GAM {0} - {1} / {2} / Python {3}.{4}.{5} {6} / {7} {8} /'.format(gam_version, GAM_URL,
                                                                              gam_author,
                                                                              sys.version_info[0], sys.version_info[1],
                                                                              sys.version_info[2], sys.version_info[3],
                                                                              platform.platform(), platform.machine())

GAM_RELEASES = 'https://github.com/jay0lee/GAM/releases'
GAM_WIKI = 'https://github.com/jay0lee/GAM/wiki'
GAM_ALL_RELEASES = 'https://api.github.com/repos/jay0lee/GAM/releases'
GAM_LATEST_RELEASE = GAM_ALL_RELEASES+'/latest'
GAM_PROJECT_APIS = 'https://raw.githubusercontent.com/jay0lee/GAM/master/src/project-apis.txt'

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
SKUS = {
  '1010010001': {
    'product': '101001', 'aliases': ['identity', 'cloudidentity'], 'displayName': 'Cloud Identity'},
  '1010050001': {
    'product': '101005', 'aliases': ['identitypremium', 'cloudidentitypremium'], 'displayName': 'Cloud Identity Premium'},
  '1010310002': {
    'product': '101031', 'aliases': ['gsefe', 'e4e', 'gsuiteenterpriseeducation'], 'displayName': 'G Suite Enterprise for Education'},
  '1010310003': {
    'product': '101031', 'aliases': ['gsefes', 'e4es', 'gsuiteenterpriseeducationstudent'], 'displayName': 'G Suite Enterprise for Education Student'},
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
  '101006': 'Drive Enterprise',
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
  'datatransfer': 'datatransfer_v1',
  'directory': 'directory_v1',
  'drive': 'v2',
  'drive3': 'v3',
  'gmail': 'v1',
  'groupssettings': 'v1',
  'licensing': 'v1',
  'oauth2': 'v2',
  'pubsub': 'v1',
  'reports': 'reports_v1',
  'reseller': 'v1',
  'sheets': 'v4',
  'siteVerification': 'v1',
  'storage': 'v1',
  'vault': 'v1',
  }

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

_MICROSOFT_FORMATS_LIST = [{'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'ext': '.docx'},
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
                           {'mime': 'application/vnd.ms-excel', 'ext': '.xlt'}]

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
  'bootmode': ['bootMode',],
  'cpustatusreports': ['cpuStatusReports',],
  'devicefiles': ['deviceFiles',],
  'deviceid': ['deviceId',],
  'diskvolumereports': ['diskVolumeReports',],
  'ethernetmacaddress': ['ethernetMacAddress',],
  'firmwareversion': ['firmwareVersion',],
  'lastenrollmenttime': ['lastEnrollmentTime',],
  'lastsync': ['lastSync',],
  'location': ['annotatedLocation',],
  'macaddress': ['macAddress',],
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
  'ethernetMacAddress',
  'macAddress',
  'systemRamTotal',
  'lastEnrollmentTime',
  'orderNumber',
  'supportEndDate',
  'guessedAUEDate',
  'guessedAUEModel',
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

# parsed from https://support.google.com/chrome/a/answer/6220366?hl=en
# using src/tools/parse-aue.py
CROS_AUE_DATES = {
  'acer ac700': '2016-08-01T00:00:00.000Z',
  'acer c7 chromebook (c710)': '2017-10-01T00:00:00.000Z',
  'acer c7 chromebook': '2017-10-01T00:00:00.000Z',
  'acer c720 chromebook': '2019-06-01T00:00:00.000Z',
  'acer c740 chromebook': '2019-06-01T00:00:00.000Z',
  'acer chromebase 24': '2021-06-01T00:00:00.000Z',
  'acer chromebase': '2020-08-01T00:00:00.000Z',
  'acer chromebook 11 (c720, c720p)': '2019-06-01T00:00:00.000Z',
  'acer chromebook 11 (c732, c732t, c732l, c732lt)': '2023-11-01T00:00:00.000Z',
  'acer chromebook 11 (c740)': '2020-06-01T00:00:00.000Z',
  'acer chromebook 11 (c771, c771t)': '2022-11-01T00:00:00.000Z',
  'acer chromebook 11 (cb3-111, c730, c730e)': '2019-08-01T00:00:00.000Z',
  'acer chromebook 11 (cb3-131, c735)': '2021-01-01T00:00:00.000Z',
  'acer chromebook 11 (cb311-8h, cb311-8ht)': '2023-11-01T00:00:00.000Z',
  'acer chromebook 11 n7 (c731, c731t)': '2022-01-01T00:00:00.000Z',
  'acer chromebook 13 (cb5-311)': '2019-09-01T00:00:00.000Z',
  'acer chromebook 13 (cb5-311, c810)': '2019-09-01T00:00:00.000Z',
  'acer chromebook 13 (cb713-1w)': '2024-06-01T00:00:00.000Z',
  'acer chromebook 14 (cb3-431)': '2021-06-01T00:00:00.000Z',
  'acer chromebook 14 for work (cp5-471)': '2022-11-01T00:00:00.000Z',
  'acer chromebook 15 (c910 / cb5-571)': '2020-06-01T00:00:00.000Z',
  'acer chromebook 15 (cb3-531)': '2020-06-01T00:00:00.000Z',
  'acer chromebook 15 (cb3-532)': '2021-08-01T00:00:00.000Z',
  'acer chromebook 15 (cb315-1h,cb315-1ht)': '2023-11-01T00:00:00.000Z',
  'acer chromebook 15 (cb5-571, c910)': '2020-06-01T00:00:00.000Z',
  'acer chromebook 15 (cb515-1h,cb515-1ht)': '2023-11-01T00:00:00.000Z',
  'acer chromebook 311 (c721, c733, c733u, c733t)': '2025-06-01T00:00:00.000Z',
  'acer chromebook 311': '2025-06-01T00:00:00.000Z',
  'acer chromebook 315 (cb315-2h)': '2025-06-01T00:00:00.000Z',
  'acer chromebook 315': '2025-06-01T00:00:00.000Z',
  'acer chromebook 512 (c851, c851t)': '2025-06-01T00:00:00.000Z',
  'acer chromebook 514': '2023-11-01T00:00:00.000Z',
  'acer chromebook 714 (cb714-1w / cb714-1wt)': '2024-06-01T00:00:00.000Z',
  'acer chromebook 715 (cb715-1w / cb715-1wt)': '2024-06-01T00:00:00.000Z',
  'acer chromebook r11 (cb5-132t, c738t)': '2021-06-01T00:00:00.000Z',
  'acer chromebook r13 (cb5-312t)': '2021-09-01T00:00:00.000Z',
  'acer chromebook spin 11 (cp311-h1, cp311-1hn)': '2023-11-01T00:00:00.000Z',
  'acer chromebook spin 11 (r751t)': '2023-11-01T00:00:00.000Z',
  'acer chromebook spin 13 (cp713-1wn)': '2024-06-01T00:00:00.000Z',
  'acer chromebook spin 15 (cp315)': '2023-11-01T00:00:00.000Z',
  'acer chromebook spin 311 (r721t)': '2025-06-01T00:00:00.000Z',
  'acer chromebook spin 511 (r752t, r752tn)': '2025-06-01T00:00:00.000Z',
  'acer chromebook spin 511': '2025-06-01T00:00:00.000Z',
  'acer chromebook spin 512 (r851tn)': '2025-06-01T00:00:00.000Z',
  'acer chromebook tab 10': '2023-08-01T00:00:00.000Z',
  'acer chromebox cxi2 / cxv2': '2020-06-01T00:00:00.000Z',
  'acer chromebox cxi2': '2020-06-01T00:00:00.000Z',
  'acer chromebox cxi3': '2024-06-01T00:00:00.000Z',
  'acer chromebox': '2019-09-01T00:00:00.000Z',
  'aopen chromebase commercial': '2020-09-01T00:00:00.000Z',
  'aopen chromebase mini': '2022-02-01T00:00:00.000Z',
  'aopen chromebox commercial 2': '2024-06-01T00:00:00.000Z',
  'aopen chromebox commercial': '2020-09-01T00:00:00.000Z',
  'aopen chromebox mini': '2022-02-01T00:00:00.000Z',
  'asi chromebook': '2020-06-01T00:00:00.000Z',
  'asus chromebit cs10': '2020-11-01T00:00:00.000Z',
  'asus chromebook c200': '2019-06-01T00:00:00.000Z',
  'asus chromebook c200ma': '2019-06-01T00:00:00.000Z',
  'asus chromebook c201pa': '2020-06-01T00:00:00.000Z',
  'asus chromebook c201pa': '2020-06-01T00:00:00.000Z',
  'asus chromebook c202sa': '2021-06-01T00:00:00.000Z',
  'asus chromebook c204': '2025-06-01T00:00:00.000Z',
  'asus chromebook c204': '2025-06-01T00:00:00.000Z',
  'asus chromebook c213na': '2023-11-01T00:00:00.000Z',
  'asus chromebook c223': '2023-11-01T00:00:00.000Z',
  'asus chromebook c300': '2019-08-01T00:00:00.000Z',
  'asus chromebook c300ma': '2019-08-01T00:00:00.000Z',
  'asus chromebook c300sa / c301sa': '2021-06-01T00:00:00.000Z',
  'asus chromebook c403': '2023-11-01T00:00:00.000Z',
  'asus chromebook c423': '2023-11-01T00:00:00.000Z',
  'asus chromebook c523': '2023-11-01T00:00:00.000Z',
  'asus chromebook flip c100pa': '2020-07-01T00:00:00.000Z',
  'asus chromebook flip c101pa': '2023-08-01T00:00:00.000Z',
  'asus chromebook flip c213': '2023-11-01T00:00:00.000Z',
  'asus chromebook flip c214': '2025-06-01T00:00:00.000Z',
  'asus chromebook flip c302': '2022-11-01T00:00:00.000Z',
  'asus chromebook flip c434': '2024-06-01T00:00:00.000Z',
  'asus chromebook tablet ct100': '2023-08-01T00:00:00.000Z',
  'asus chromebox (cn60)': '2019-09-01T00:00:00.000Z',
  'asus chromebox 2 (cn62)': '2021-06-01T00:00:00.000Z',
  'asus chromebox 3 (cn65)': '2024-06-01T00:00:00.000Z',
  'asus chromebox 3': '2024-06-01T00:00:00.000Z',
  'asus chromebox cn60': '2019-09-01T00:00:00.000Z',
  'asus chromebox cn62': '2021-06-01T00:00:00.000Z',
  'bobicus chromebook 11': '2020-06-01T00:00:00.000Z',
  'chromebook 11 (c730 / cb3-111)': '2019-08-01T00:00:00.000Z',
  'chromebook 11 (c735)': '2021-01-01T00:00:00.000Z',
  'chromebook 15 (cb515 - 1ht / 1h)': '2023-11-01T00:00:00.000Z',
  'chromebook 311 (c721)': '2025-06-01T00:00:00.000Z',
  'chromebook pcm-116e': '2020-06-01T00:00:00.000Z',
  'consumer chromebook': '2020-06-01T00:00:00.000Z',
  'cr-48': '2015-12-01T00:00:00.000Z',
  'crambo chromebook': '2020-06-01T00:00:00.000Z',
  'ctl chromebook j41 / j41t': '2023-11-01T00:00:00.000Z',
  'ctl chromebook nl7 / nl7t-360 / nl7tw-360': '2023-11-01T00:00:00.000Z',
  'ctl chromebook nl7': '2023-11-01T00:00:00.000Z',
  'ctl chromebook tab tx1': '2023-08-01T00:00:00.000Z',
  'ctl chromebook tablet tx1 for education': '2023-08-01T00:00:00.000Z',
  'ctl chromebox cbx1': '2024-06-01T00:00:00.000Z',
  'ctl j2 / j4 chromebook': '2020-06-01T00:00:00.000Z',
  'ctl j5 chromebook': '2021-08-01T00:00:00.000Z',
  'ctl n6 education chromebook': '2020-06-01T00:00:00.000Z',
  'ctl nl61 chromebook': '2021-08-01T00:00:00.000Z',
  'dell chromebook 11 (3120)': '2020-06-01T00:00:00.000Z',
  'dell chromebook 11 (3180)': '2022-05-01T00:00:00.000Z',
  'dell chromebook 11 (5190)': '2023-11-01T00:00:00.000Z',
  'dell chromebook 11 2-in-1 (3189)': '2022-05-01T00:00:00.000Z',
  'dell chromebook 11 2-in-1 (5190)': '2023-11-01T00:00:00.000Z',
  'dell chromebook 11': '2019-06-01T00:00:00.000Z',
  'dell chromebook 13 (3380)': '2022-11-01T00:00:00.000Z',
  'dell chromebook 13 (7310)': '2020-09-01T00:00:00.000Z',
  'dell chromebook 3100 2-in-1': '2025-06-01T00:00:00.000Z',
  'dell chromebook 3100': '2025-06-01T00:00:00.000Z',
  'dell chromebook 3400': '2025-06-01T00:00:00.000Z',
  'dell chromebox': '2019-09-01T00:00:00.000Z',
  'dell inspiron chromebook 14 2-in-1 (7486)': '2024-06-01T00:00:00.000Z',
  'edugear chromebook k': '2020-06-01T00:00:00.000Z',
  'edugear chromebook m': '2020-06-01T00:00:00.000Z',
  'edugear chromebook r': '2020-06-01T00:00:00.000Z',
  'edugear cmt chromebook': '2021-08-01T00:00:00.000Z',
  'edxis chromebook': '2020-06-01T00:00:00.000Z',
  'edxis education chromebook': '2020-06-01T00:00:00.000Z',
  'epik 11.6" chromebook  elb1101': '2020-06-01T00:00:00.000Z',
  'google chromebook pixel (2015)': '2020-06-01T00:00:00.000Z',
  'google chromebook pixel': '2018-06-01T00:00:00.000Z',
  'google cr-48': '2015-12-01T00:00:00.000Z',
  'google pixel slate': '2024-06-01T00:00:00.000Z',
  'google pixelbook': '2024-06-01T00:00:00.000Z',
  'haier chromebook 11 c': '2021-08-01T00:00:00.000Z',
  'haier chromebook 11 g2': '2020-09-01T00:00:00.000Z',
  'haier chromebook 11': '2020-06-01T00:00:00.000Z',
  'haier chromebook 11e': '2020-06-01T00:00:00.000Z',
  'hexa chromebook pi': '2020-06-01T00:00:00.000Z',
  'hisense chromebook 11': '2020-06-01T00:00:00.000Z',
  'hp chromebook 11 1100-1199 / hp chromebook 11 g1': '2018-10-01T00:00:00.000Z',
  'hp chromebook 11 2000-2099 / hp chromebook 11 g2': '2019-06-01T00:00:00.000Z',
  'hp chromebook 11 2100-2199 / hp chromebook 11 g3': '2020-06-01T00:00:00.000Z',
  'hp chromebook 11 2200-2299 / hp chromebook 11 g4/g4 ee': '2020-06-01T00:00:00.000Z',
  'hp chromebook 11 g1': '2018-10-01T00:00:00.000Z',
  'hp chromebook 11 g2': '2019-06-01T00:00:00.000Z',
  'hp chromebook 11 g3': '2020-06-01T00:00:00.000Z',
  'hp chromebook 11 g4/g4 ee': '2020-06-01T00:00:00.000Z',
  'hp chromebook 11 g5 / hp chromebook 11-vxxx': '2021-07-01T00:00:00.000Z',
  'hp chromebook 11 g5 ee': '2022-01-01T00:00:00.000Z',
  'hp chromebook 11 g5': '2021-07-01T00:00:00.000Z',
  'hp chromebook 11 g6 ee': '2023-11-01T00:00:00.000Z',
  'hp chromebook 11 g7 ee': '2025-06-01T00:00:00.000Z',
  'hp chromebook 11a g6 ee': '2025-06-01T00:00:00.000Z',
  'hp chromebook 13 g1': '2022-11-01T00:00:00.000Z',
  'hp chromebook 14 / hp chromebook 14 g5': '2023-11-01T00:00:00.000Z',
  'hp chromebook 14 ak000-099 / hp chromebook 14 g4': '2021-09-01T00:00:00.000Z',
  'hp chromebook 14 db0000-db0999': '2025-06-01T00:00:00.000Z',
  'hp chromebook 14 g3': '2019-10-01T00:00:00.000Z',
  'hp chromebook 14 g4': '2021-09-01T00:00:00.000Z',
  'hp chromebook 14 g5': '2023-11-01T00:00:00.000Z',
  'hp chromebook 14 x000-x999 / hp chromebook 14 g3': '2019-10-01T00:00:00.000Z',
  'hp chromebook 14': '2019-06-01T00:00:00.000Z',
  'hp chromebook 14a g5': '2025-06-01T00:00:00.000Z',
  'hp chromebook 15 g1': '2024-06-01T00:00:00.000Z',
  'hp chromebook x2 ': '2024-06-01T00:00:00.000Z',
  'hp chromebook x360 11 g1 ee': '2023-11-01T00:00:00.000Z',
  'hp chromebook x360 11 g2 ee': '2025-06-01T00:00:00.000Z',
  'hp chromebook x360 14 g1': '2024-06-01T00:00:00.000Z',
  'hp chromebook x360 14': '2024-06-01T00:00:00.000Z',
  'hp chromebox cb1-(000-099) / hp chromebox g1/ hp chromebox for meetings': '2019-09-01T00:00:00.000Z',
  'hp chromebox g1': '2019-09-01T00:00:00.000Z',
  'hp chromebox g2': '2024-06-01T00:00:00.000Z',
  'hp pavilion chromebook 14': '2018-02-01T00:00:00.000Z',
  'jp sa couto chromebook': '2020-06-01T00:00:00.000Z',
  'lava xolo chromebook': '2020-06-01T00:00:00.000Z',
  'lenovo 100e chromebook 2nd gen mtk': '2025-06-01T00:00:00.000Z',
  'lenovo 100e chromebook 2nd gen': '2025-06-01T00:00:00.000Z',
  'lenovo 100e chromebook': '2023-11-01T00:00:00.000Z',
  'lenovo 100s chromebook': '2020-09-01T00:00:00.000Z',
  'lenovo 14e chromebook': '2025-06-01T00:00:00.000Z',
  'lenovo 300e chromebook 2nd gen mtk': '2025-06-01T00:00:00.000Z',
  'lenovo 300e chromebook 2nd gen': '2025-06-01T00:00:00.000Z',
  'lenovo 300e chromebook': '2025-06-01T00:00:00.000Z',
  'lenovo 500e chromebook 2nd gen': '2025-06-01T00:00:00.000Z',
  'lenovo 500e chromebook': '2023-11-01T00:00:00.000Z',
  'lenovo chromebook c330': '2022-06-01T00:00:00.000Z',
  'lenovo chromebook s330': '2022-06-01T00:00:00.000Z',
  'lenovo flex 11 chromebook': '2022-06-01T00:00:00.000Z',
  'lenovo ideapad c330 chromebook': '2022-06-01T00:00:00.000Z',
  'lenovo ideapad s330 chromebook': '2022-06-01T00:00:00.000Z',
  'lenovo n20 chromebook': '2019-06-01T00:00:00.000Z',
  'lenovo n21 chromebook': '2020-06-01T00:00:00.000Z',
  'lenovo n22 chromebook': '2021-06-01T00:00:00.000Z',
  'lenovo n23 chromebook': '2021-06-01T00:00:00.000Z',
  'lenovo n23 yoga chromebook': '2022-06-01T00:00:00.000Z',
  'lenovo n42 chromebook': '2021-06-01T00:00:00.000Z',
  'lenovo thinkcentre chromebox': '2020-06-01T00:00:00.000Z',
  'lenovo thinkpad 11e 3rd gen chromebook': '2021-06-01T00:00:00.000Z',
  'lenovo thinkpad 11e 4th gen chromebook': '2023-11-01T00:00:00.000Z',
  'lenovo thinkpad 11e chromebook (4th gen)/lenovo thinkpad yoga 11e chromebook (4th gen)': '2023-11-01T00:00:00.000Z',
  'lenovo thinkpad 11e chromebook': '2019-06-01T00:00:00.000Z',
  'lenovo thinkpad 13': '2022-11-01T00:00:00.000Z',
  'lenovo thinkpad x131e chromebook': '2018-06-01T00:00:00.000Z',
  'lenovo yoga c630 chromebook': '2024-06-01T00:00:00.000Z',
  'lg chromebase (22cb25s)': '2020-06-01T00:00:00.000Z',
  'lg chromebase (22cv241)': '2019-06-01T00:00:00.000Z',
  'lumos education chromebook': '2020-06-01T00:00:00.000Z',
  'm&a chromebook': '2020-06-01T00:00:00.000Z',
  'mecer chromebook': '2020-06-01T00:00:00.000Z',
  'mecer v2 chromebook': '2021-08-01T00:00:00.000Z',
  'medion chromebook akoya s2013 ': '2020-06-01T00:00:00.000Z',
  'medion chromebook s2015': '2020-06-01T00:00:00.000Z',
  'multilaser chromebook m11c': '2021-08-01T00:00:00.000Z',
  'ncomputing chromebook cx100': '2020-06-01T00:00:00.000Z',
  'ncomputing chromebook cx110': '2020-06-01T00:00:00.000Z',
  'nexian chromebook 11.6\"': '2020-06-01T00:00:00.000Z',
  'pcmerge chromebook al116': '2023-11-01T00:00:00.000Z',
  'pcmerge chromebookpcm-116e/pcm-116eb': '2020-06-01T00:00:00.000Z',
  'pcmerge chromebookpcm-116t-432b': '2021-08-01T00:00:00.000Z',
  'poin2 chromebook 11': '2020-06-01T00:00:00.000Z',
  'poin2 chromebook 11c': '2022-03-01T00:00:00.000Z',
  'poin2 chromebook 14': '2022-03-01T00:00:00.000Z',
  'positivo chromebook c216b': '2021-08-01T00:00:00.000Z',
  'positivo chromebook ch1190': '2020-06-01T00:00:00.000Z',
  'prowise 11.6" entry line chromebook': '2020-06-01T00:00:00.000Z',
  'prowise chromebook eduline': '2023-11-01T00:00:00.000Z',
  'prowise chromebook entryline': '2020-06-01T00:00:00.000Z',
  'prowise chromebook proline': '2021-08-01T00:00:00.000Z',
  'prowise proline chromebook': '2021-08-01T00:00:00.000Z',
  'rgs education chromebook': '2020-06-01T00:00:00.000Z',
  'samsung chromebook - xe303': '2018-07-01T00:00:00.000Z',
  'samsung chromebook 2 11\" - xe500c12': '2020-06-01T00:00:00.000Z',
  'samsung chromebook 2 11\"': '2019-06-01T00:00:00.000Z',
  'samsung chromebook 2 13\"': '2019-06-01T00:00:00.000Z',
  'samsung chromebook 3': '2021-06-01T00:00:00.000Z',
  'samsung chromebook plus (v2)': '2024-06-01T00:00:00.000Z',
  'samsung chromebook plus': '2023-08-01T00:00:00.000Z',
  'samsung chromebook pro': '2022-11-01T00:00:00.000Z',
  'samsung chromebook series 5 550': '2017-05-01T00:00:00.000Z',
  'samsung chromebook series 5': '2016-06-01T00:00:00.000Z',
  'samsung chromebook': '2018-07-01T00:00:00.000Z',
  'samsung chromebox series 3': '2018-03-01T00:00:00.000Z',
  'sector 5 e1 rugged chromebook': '2020-06-01T00:00:00.000Z',
  'sector 5 e3 chromebook': '2023-11-01T00:00:00.000Z',
  'senkatel c1101 chromebook': '2020-06-01T00:00:00.000Z',
  'thinkpad 11e chromebook 3rd gen (yoga/clamshell)': '2021-06-01T00:00:00.000Z',
  'thinkpad 13 chromebook': '2022-11-01T00:00:00.000Z',
  'toshiba chromebook 2 (2015 edition)': '2020-09-01T00:00:00.000Z',
  'toshiba chromebook 2': '2020-06-01T00:00:00.000Z',
  'toshiba chromebook': '2019-06-01T00:00:00.000Z',
  'true idc chromebook 11': '2020-06-01T00:00:00.000Z',
  'true idc chromebook': '2020-06-01T00:00:00.000Z',
  'videonet chromebook bl10': '2020-06-01T00:00:00.000Z',
  'videonet chromebook': '2020-06-01T00:00:00.000Z',
  'viewsonic nmp660 chromebox': '2024-06-01T00:00:00.000Z',
  'viglen chromebook 11': '2020-06-01T00:00:00.000Z',
  'viglen chromebook 11c': '2023-11-01T00:00:00.000Z',
  'viglen chromebook 360': '2021-08-01T00:00:00.000Z',
  'xolo chromebook': '2020-06-01T00:00:00.000Z',
}

COLLABORATIVE_ACL_CHOICES = {
  'members': 'ALL_MEMBERS',
  'managersonly': 'MANAGERS_ONLY',
  'managers': 'OWNERS_AND_MANAGERS',
  'owners': 'OWNERS_ONLY',
  'none': 'NONE',
  }

COLLABORATIVE_INBOX_ATTRIBUTES = {
  'whoCanAddReferences': 'acl',
  'whoCanAssignTopics': 'acl',
  'whoCanEnterFreeFormTags': 'acl',
  'whoCanMarkDuplicate': 'acl',
  'whoCanMarkFavoriteReplyOnAnyTopic': 'acl',
  'whoCanMarkFavoriteReplyOnOwnTopic': 'acl',
  'whoCanMarkNoResponseNeeded': 'acl',
  'whoCanModifyTagsAndCategories': 'acl',
  'whoCanTakeTopics': 'acl',
  'whoCanUnassignTopic': 'acl',
  'whoCanUnmarkFavoriteReplyOnAnyTopic': 'acl',
  'favoriteRepliesOnTop': True,
  }

#
# Global variables
#
# The following GM_XXX constants are arbitrary but must be unique
# Most errors print a message and bail out with a return code
# Some commands want to set a non-zero return code but not bail
GM_SYSEXITRC = 'sxrc'
# Path to gam
GM_GAM_PATH = 'gpth'
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
# When retrieving lists of Google Drive activities from API, how many should be retrieved in each chunk
GC_ACTIVITY_MAX_RESULTS = 'activity_max_results'
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
# When retrieving lists of ChromeOS/Mobile devices from API, how many should be retrieved in each chunk
GC_DEVICE_MAX_RESULTS = 'device_max_results'
# Domain obtained from gam.cfg or oauth2.txt
GC_DOMAIN = 'domain'
# Google Drive download directory
GC_DRIVE_DIR = 'drive_dir'
# When retrieving lists of Drive files/folders from API, how many should be retrieved in each chunk
GC_DRIVE_MAX_RESULTS = 'drive_max_results'
# When retrieving lists of Google Group members from API, how many should be retrieved in each chunk
GC_MEMBER_MAX_RESULTS = 'member_max_results'
# If no_browser is False, writeCSVfile won't open a browser when todrive is set
# and doRequestOAuth prints a link and waits for the verification code when oauth2.txt is being created
GC_NO_BROWSER = 'no_browser'
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
# When retrieving lists of Users from API, how many should be retrieved in each chunk
GC_USER_MAX_RESULTS = 'user_max_results'
# CSV Columns GAM should show on CSV output
GC_CSV_HEADER_FILTER = 'csv_header_filter'
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
  GC_ACTIVITY_MAX_RESULTS: 100,
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
  GC_DEVICE_MAX_RESULTS: 500,
  GC_DOMAIN: '',
  GC_DRIVE_DIR: '',
  GC_DRIVE_MAX_RESULTS: 1000,
  GC_MEMBER_MAX_RESULTS: 200,
  GC_NO_BROWSER: False,
  GC_NO_CACHE: False,
  GC_NO_UPDATE_CHECK: False,
  GC_NUM_THREADS: 25,
  GC_OAUTH2_TXT: _FN_OAUTH2_TXT,
  GC_OAUTH2SERVICE_JSON: _FN_OAUTH2SERVICE_JSON,
  GC_SECTION: '',
  GC_SHOW_COUNTS_MIN: 0,
  GC_SHOW_GETTINGS: True,
  GC_SITE_DIR: '',
  GC_USER_MAX_RESULTS: 500,
  GC_CSV_HEADER_FILTER: '',
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
  GC_DECODED_ID_TOKEN: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DEVICE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_DOMAIN: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_DRIVE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_DRIVE_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 1000)},
  GC_MEMBER_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 10000)},
  GC_NO_BROWSER: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_CACHE: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NO_UPDATE_CHECK: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_NUM_THREADS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, None)},
  GC_OAUTH2_TXT: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_OAUTH2SERVICE_JSON: {GC_VAR_TYPE: GC_TYPE_FILE},
  GC_SECTION: {GC_VAR_TYPE: GC_TYPE_STRING},
  GC_SHOW_COUNTS_MIN: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (0, None)},
  GC_SHOW_GETTINGS: {GC_VAR_TYPE: GC_TYPE_BOOLEAN},
  GC_SITE_DIR: {GC_VAR_TYPE: GC_TYPE_DIRECTORY},
  GC_USER_MAX_RESULTS: {GC_VAR_TYPE: GC_TYPE_INTEGER, GC_VAR_LIMITS: (1, 500)},
  GC_CSV_HEADER_FILTER: {GC_VAR_TYPE: GC_TYPE_HEADERFILTER},
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
MESSAGE_CONSOLE_AUTHORIZATION_PROMPT = '\nGo to the following link in your browser:\n\n\t{url}\n'
MESSAGE_CONSOLE_AUTHORIZATION_CODE = 'Enter verification code: '
MESSAGE_GAM_EXITING_FOR_UPDATE = 'GAM is now exiting so that you can overwrite this old version with the latest release'
MESSAGE_GAM_OUT_OF_MEMORY = 'GAM has run out of memory. If this is a large G Suite instance, you should use a 64-bit version of GAM on Windows or a 64-bit version of Python on other systems.'
MESSAGE_HEADER_NOT_FOUND_IN_CSV_HEADERS = 'Header "{0}" not found in CSV headers of "{1}".'
MESSAGE_HIT_CONTROL_C_TO_UPDATE = '\n\nHit CTRL+C to visit the GAM website and download the latest release or wait 15 seconds continue with this boring old version. GAM won\'t bother you with this announcement for 1 week or you can create a file named noupdatecheck.txt in the same location as gam.py or gam.exe and GAM won\'t ever check for updates.'
MESSAGE_INVALID_JSON = 'The file {0} has an invalid format.'
MESSAGE_LOCAL_SERVER_AUTHORIZATION_PROMPT = '\nYour browser has been opened to visit:\n\n\t{url}\n\nIf your browser is on a different machine then press CTRL+C and create a file called nobrowser.txt in the same folder as GAM.\n'
MESSAGE_LOCAL_SERVER_SUCCESS = 'The authentication flow has completed. You may close this browser window and return to GAM.'
MESSAGE_NO_DISCOVERY_INFORMATION = 'No online discovery doc and {0} does not exist locally'
MESSAGE_NO_TRANSFER_LACK_OF_DISK_SPACE = 'Cowardly refusing to perform migration due to lack of target drive space. Source size: {0}mb Target Free: {1}mb'
MESSAGE_RESULTS_TOO_LARGE_FOR_GOOGLE_SPREADSHEET = 'Results are too large for Google Spreadsheets. Uploading as a regular CSV file.'
MESSAGE_SERVICE_NOT_APPLICABLE = 'Service not applicable for this address: {0}. Please make sure service is enabled for user and run\n\ngam user <user> check serviceaccount\n\nfor further instructions'
MESSAGE_INSTRUCTIONS_OAUTH2SERVICE_JSON = 'Please run\n\ngam create project\ngam user <user> check serviceaccount\n\nto create and configure a service account.'
# oauth errors
OAUTH2_TOKEN_ERRORS = [
  'access_denied',
  'access_denied: Requested client not authorized',
  'internal_failure: Backend Error',
  'internal_failure: None',
  'invalid_grant',
  'invalid_grant: Bad Request',
  'invalid_grant: Invalid email or User ID',
  'invalid_grant: Not a valid email',
  'invalid_grant: Invalid JWT: No valid verifier found for issuer',
  'invalid_request: Invalid impersonation prn email address',
  'unauthorized_client: Client is unauthorized to retrieve access tokens using this method',
  'unauthorized_client: Client is unauthorized to retrieve access tokens using this method, or client not authorized for any of the scopes requested',
  'unauthorized_client: Unauthorized client or scope in request',
  ]
#
# callGAPI throw reasons
GAPI_ABORTED = 'aborted'
GAPI_AUTH_ERROR = 'authError'
GAPI_BACKEND_ERROR = 'backendError'
GAPI_BAD_REQUEST = 'badRequest'
GAPI_CONDITION_NOT_MET = 'conditionNotMet'
GAPI_CYCLIC_MEMBERSHIPS_NOT_ALLOWED = 'cyclicMembershipsNotAllowed'
GAPI_DOMAIN_CANNOT_USE_APIS = 'domainCannotUseApis'
GAPI_DOMAIN_NOT_FOUND = 'domainNotFound'
GAPI_DUPLICATE = 'duplicate'
GAPI_FAILED_PRECONDITION = 'failedPrecondition'
GAPI_FORBIDDEN = 'forbidden'
GAPI_GROUP_NOT_FOUND = 'groupNotFound'
GAPI_INTERNAL_ERROR = 'internalError'
GAPI_INVALID = 'invalid'
GAPI_INVALID_ARGUMENT = 'invalidArgument'
GAPI_INVALID_MEMBER = 'invalidMember'
GAPI_MEMBER_NOT_FOUND = 'memberNotFound'
GAPI_NOT_FOUND = 'notFound'
GAPI_NOT_IMPLEMENTED = 'notImplemented'
GAPI_PERMISSION_DENIED = 'permissionDenied'
GAPI_QUOTA_EXCEEDED = 'quotaExceeded'
GAPI_RATE_LIMIT_EXCEEDED = 'rateLimitExceeded'
GAPI_RESOURCE_NOT_FOUND = 'resourceNotFound'
GAPI_SERVICE_NOT_AVAILABLE = 'serviceNotAvailable'
GAPI_SYSTEM_ERROR = 'systemError'
GAPI_USER_NOT_FOUND = 'userNotFound'
GAPI_USER_RATE_LIMIT_EXCEEDED = 'userRateLimitExceeded'
#
GAPI_DEFAULT_RETRY_REASONS = [GAPI_QUOTA_EXCEEDED, GAPI_RATE_LIMIT_EXCEEDED, GAPI_USER_RATE_LIMIT_EXCEEDED, GAPI_BACKEND_ERROR, GAPI_INTERNAL_ERROR]
GAPI_GMAIL_THROW_REASONS = [GAPI_SERVICE_NOT_AVAILABLE]
GAPI_GROUP_GET_THROW_REASONS = [GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_DOMAIN_CANNOT_USE_APIS, GAPI_FORBIDDEN, GAPI_BAD_REQUEST]
GAPI_GROUP_GET_RETRY_REASONS = [GAPI_INVALID, GAPI_SYSTEM_ERROR]
GAPI_MEMBERS_THROW_REASONS = [GAPI_GROUP_NOT_FOUND, GAPI_DOMAIN_NOT_FOUND, GAPI_DOMAIN_CANNOT_USE_APIS, GAPI_INVALID, GAPI_FORBIDDEN]
GAPI_MEMBERS_RETRY_REASONS = [GAPI_SYSTEM_ERROR]

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
