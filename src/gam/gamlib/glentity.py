# -*- coding: utf-8 -*-

# Copyright (C) 2024 Ross Scroggs All Rights Reserved.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""GAM entity processing

"""

class GamEntity():

  ROLE_MANAGER = 'MANAGER'
  ROLE_MEMBER = 'MEMBER'
  ROLE_OWNER = 'OWNER'
  ROLE_LIST = [ROLE_MANAGER, ROLE_MEMBER, ROLE_OWNER]
  ROLE_USER = 'USER'
  ROLE_MANAGER_MEMBER = ','.join([ROLE_MANAGER, ROLE_MEMBER])
  ROLE_MANAGER_OWNER = ','.join([ROLE_MANAGER, ROLE_OWNER])
  ROLE_MEMBER_OWNER = ','.join([ROLE_MEMBER, ROLE_OWNER])
  ROLE_MANAGER_MEMBER_OWNER = ','.join(ROLE_LIST)
  ROLE_PUBLIC = 'PUBLIC'
  ROLE_ALL = ROLE_MANAGER_MEMBER_OWNER

  TYPE_CBCM_BROWSER = 'CBCM_BROWSER'
  TYPE_CUSTOMER = 'CUSTOMER'
  TYPE_EXTERNAL = 'EXTERNAL'
  TYPE_OTHER = 'OTHER'
  TYPE_GROUP = 'GROUP'
  TYPE_SERVICE_ACCOUNT = 'SERVICE_ACCOUNT'
  TYPE_USER = 'USER'

# Keys into NAMES; arbitrary values but must be unique
  ACCESS_TOKEN = 'atok'
  ACCOUNT = 'acct'
  ACTION = 'actn'
  ACTIVITY = 'actv'
  ADMINISTRATOR = 'admi'
  ADMIN_ROLE = 'adro'
  ADMIN_ROLE_ASSIGNMENT = 'adra'
  ALERT = 'alrt'
  ALERT_ID = 'alri'
  ALERT_FEEDBACK = 'alfb'
  ALERT_FEEDBACK_ID = 'alfi'
  ALIAS = 'alia'
  ALIAS_EMAIL = 'alie'
  ALIAS_TARGET = 'alit'
  ANALYTIC_ACCOUNT = 'anac'
  ANALYTIC_ACCOUNT_SUMMARY = 'anas'
  ANALYTIC_DATASTREAM = 'anad'
  ANALYTIC_PROPERTY = 'anap'
  API = 'api '
  APP_ACCESS_SETTINGS = 'apps'
  APP_ID = 'appi'
  APP_NAME = 'appn'
  APPLICATION_SPECIFIC_PASSWORD = 'aspa'
  ARROWS_ENABLED = 'arro'
  ATTACHMENT = 'atta'
  ATTENDEE = 'atnd'
  AUDIT_ACTIVITY_REQUEST = 'auda'
  AUDIT_EXPORT_REQUEST = 'audx'
  AUDIT_MONITOR_REQUEST = 'audm'
  BACKUP_VERIFICATION_CODES = 'buvc'
  BUILDING = 'bldg'
  BUILDING_ID = 'bldi'
  CAA_LEVEL = 'calv'
  CALENDAR = 'cale'
  CALENDAR_ACL = 'cacl'
  CALENDAR_SETTINGS = 'cset'
  CHANNEL_CUSTOMER = 'chcu'
  CHANNEL_CUSTOMER_ENTITLEMENT = 'chce'
  CHANNEL_OFFER = 'chof'
  CHANNEL_PRODUCT = 'chpr'
  CHANNEL_SKU = 'chsk'
  CHAT_BOT = 'chbo'
  CHAT_ADMIN = 'chad'
  CHAT_EVENT = 'chev'
  CHAT_MANAGER_USER = 'chgu'
  CHAT_MEMBER = 'chme'
  CHAT_MEMBER_GROUP = 'chmg'
  CHAT_MEMBER_USER = 'chmu'
  CHAT_MESSAGE = 'chms'
  CHAT_MESSAGE_ID = 'chmi'
  CHAT_SPACE = 'chsp'
  CHAT_THREAD = 'chth'
  CHILD_ORGANIZATIONAL_UNIT = 'corg'
  CHROME_APP = 'capp'
  CHROME_APP_DEVICE = 'capd'
  CHROME_BROWSER = 'chbr'
  CHROME_BROWSER_ENROLLMENT_TOKEN = 'cbet'
  CHROME_CHANNEL = 'chan'
  CHROME_DEVICE = 'chdv'
  CHROME_MODEL = 'chmo'
  CHROME_NETWORK_ID = 'chni'
  CHROME_NETWORK_NAME = 'chnn'
  CHROME_PLATFORM = 'cpla'
  CHROME_POLICY = 'cpol'
  CHROME_POLICY_IMAGE = 'cpim'
  CHROME_POLICY_SCHEMA = 'cpsc'
  CHROME_PROFILE = 'cpro'
  CHROME_RELEASE = 'crel'
  CHROME_VERSION = 'cver'
  CLASSIFICATION_LABEL = 'dlab'
  CLASSIFICATION_LABEL_FIELD_ID = 'dlfi'
  CLASSIFICATION_LABEL_ID = 'dlid'
  CLASSIFICATION_LABEL_NAME = 'dlna'
  CLASSIFICATION_LABEL_PERMISSION = 'dlpe'
  CLASSIFICATION_LABEL_PERMISSION_NAME = 'dlpn'
  CLASSROOM_INVITATION = 'clai'
  CLASSROOM_INVITATION_OWNER = 'clio'
  CLASSROOM_INVITATION_STUDENT = 'clis'
  CLASSROOM_INVITATION_TEACHER = 'clit'
  CLASSROOM_OAUTH2_TXT_FILE = 'coa'
  CLASSROOM_USER_PROFILE = 'clup'
  CLIENT_ID = 'clid'
  CLIENT_SECRETS_JSON_FILE = 'csjf'
  CLOUD_IDENTITY_GROUP = 'cidg'
  CLOUD_STORAGE_BUCKET = 'clsb'
  CLOUD_STORAGE_FILE = 'clsf'
  COLLABORATOR = 'cola'
  COMMAND_ID = 'cmdi'
  COMPANY_DEVICE = 'codv'
  CONFIG_FILE = 'conf'
  CONTACT = 'cont'
  CONTACT_DELEGATE = 'cond'
  CONTACT_GROUP = 'cogr'
  CONTACT_GROUP_NAME = 'cogn'
  COPYFROM_COURSE = 'cfco'
  COPYFROM_GROUP = 'cfgr'
  COURSE = 'cour'
  COURSE_ALIAS = 'coal'
  COURSE_ANNOUNCEMENT = 'cann'
  COURSE_ANNOUNCEMENT_ID = 'caid'
  COURSE_ANNOUNCEMENT_STATE = 'cast'
  COURSE_MATERIAL_DRIVEFILE = 'comd'
  COURSE_MATERIAL_FORM = 'comf'
  COURSE_MATERIAL = 'cmtl'
  COURSE_MATERIAL_ID = 'cmid'
  COURSE_MATERIAL_STATE = 'cmst'
  COURSE_NAME = 'cona'
  COURSE_STATE = 'cost'
  COURSE_SUBMISSION_ID = 'csid'
  COURSE_SUBMISSION_STATE = 'csst'
  COURSE_TOPIC = 'ctop'
  COURSE_TOPIC_ID = 'ctoi'
  COURSE_WORK = 'cwrk'
  COURSE_WORK_ID = 'cwid'
  COURSE_WORK_STATE = 'cwst'
  CREATOR_ID = 'crid'
  CREDENTIALS = 'cred'
  CRITERIA = 'crit'
  CROS_DEVICE = 'cros'
  CROS_SERIAL_NUMBER = 'crsn'
  CSE_IDENTITY = 'csei'
  CSE_KEYPAIR = 'csek'
  CUSTOMER_DOMAIN = 'cudo'
  CUSTOMER_ID = 'cuid'
  DATE = 'date'
  DEFAULT_LANGUAGE = 'dfla'
  DELEGATE = 'dele'
  DELETED_USER = 'delu'
  DELIVERY = 'deli'
  DEVICE = 'devi'
  DEVICE_FILE = 'devf'
  DIRECTORY = 'drct'
  DEVICE_USER = 'devu'
  DEVICE_USER_CLIENT_STATE = 'ducs'
  DISCOVERY_JSON_FILE = 'disc'
  DOCUMENT = 'docu'
  DOMAIN = 'doma'
  DOMAIN_ALIAS = 'doal'
  DOMAIN_CONTACT = 'doco'
  DOMAIN_PEOPLE_CONTACT = 'dopc'
  DOMAIN_PROFILE = 'dopr'
  DRIVE_DISK_USAGE = 'drdu'
  DRIVE_FILE = 'dfil'
  DRIVE_FILE_COMMENT = 'filc'
  DRIVE_FILE_ID = 'fili'
  DRIVE_FILE_NAME = 'filn'
  DRIVE_FILE_RENAMED = 'firn'
  DRIVE_FILE_REVISION = 'filr'
  DRIVE_FILE_SHORTCUT = 'fils'
  DRIVE_FILE_OR_FOLDER = 'fifo'
  DRIVE_FILE_OR_FOLDER_ACL = 'fiac'
  DRIVE_FILE_OR_FOLDER_ID = 'fifi'
  DRIVE_FOLDER = 'fold'
  DRIVE_FOLDER_ID = 'foli'
  DRIVE_FOLDER_NAME = 'foln'
  DRIVE_FOLDER_PATH = 'folp'
  DRIVE_FOLDER_RENAMED = 'forn'
  DRIVE_FOLDER_SHORTCUT = 'fols'
  DRIVE_ORPHAN_FILE_OR_FOLDER = 'orph'
  DRIVE_PARENT_FOLDER = 'fipf'
  DRIVE_PARENT_FOLDER_ID = 'fipi'
  DRIVE_PARENT_FOLDER_REFERENCE = 'pfrf'
  DRIVE_PATH = 'drvp'
  DRIVE_SETTINGS = 'drvs'
  DRIVE_SHORTCUT = 'drsc'
  DRIVE_SHORTCUT_ID = 'dsci'
  DRIVE_3PSHORTCUT = 'dr3s'
  DRIVE_TRASH = 'drvt'
  EMAIL = 'emai'
  EMAIL_ALIAS = 'emal'
  EMAIL_SETTINGS = 'emse'
  END_TIME = 'endt'
  ENTITY = 'enti'
  EVENT = 'evnt'
  EVENT_BIRTHDAY = 'evbd'
  EVENT_FOCUSTIME = 'evft'
  EVENT_OUTOFOFFICE = 'evoo'
  EVENT_WORKINGLOCATION = 'evwl'
  FEATURE = 'feat'
  FIELD = 'fiel'
  FILE = 'file'
  FILE_PARENT_TREE = 'fptr'
  FILTER = 'filt'
  FORM = 'form'
  FORM_RESPONSE = 'frmr'
  FORWARD_ENABLED = 'fwde'
  FORWARDING_ADDRESS = 'fwda'
  GCP_FOLDER = 'gcpf'
  GCP_FOLDER_NAME = 'gcpn'
  GMAIL_PROFILE = 'gmpr'
  GROUP = 'grou'
  GROUP_ALIAS = 'gali'
  GROUP_EMAIL = 'gale'
  GROUP_MEMBERSHIP = 'gmem'
  GROUP_MEMBERSHIP_TREE = 'gmtr'
  GROUP_SETTINGS = 'gset'
  GROUP_TREE = 'gtre'
  GUARDIAN = 'guar'
  GUARDIAN_INVITATION = 'gari'
  GUARDIAN_AND_INVITATION = 'gani'
  IAM_POLICY = 'iamp'
  IMAP_ENABLED = 'imap'
  INBOUND_SSO_ASSIGNMENT = 'insa'
  INBOUND_SSO_CREDENTIALS = 'insc'
  INBOUND_SSO_PROFILE = 'insp'
  INSTANCE = 'inst'
  ITEM = 'item'
  ISSUER_CN = 'iscn'
  KEYBOARD_SHORTCUTS_ENABLED = 'kbsc'
  LABEL = 'labe'
  LABEL_ID = 'labi'
  LANGUAGE = 'lang'
  LICENSE = 'lice'
  LOCATION = 'loca'
  LOOKERSTUDIO_ASSET = 'lsas'
  LOOKERSTUDIO_ASSET_DATASOURCE = 'lsad'
  LOOKERSTUDIO_ASSETID = 'lsai'
  LOOKERSTUDIO_ASSET_REPORT = 'lsar'
  LOOKERSTUDIO_PERMISSION = 'lspe'
  MD5HASH = 'md5h'
  MEET_SPACE = 'mesp'
  MEET_CONFERENCE = 'msco'
  MEET_PARTICIPANT = 'msps'
  MEET_RECORDING = 'msre'
  MEET_TRANSCRIPT = 'mstr'
  MEMBER = 'memb'
  MEMBER_NOT_ARCHIVED = 'mena'
  MEMBER_ARCHIVED = 'mear'
  MEMBER_NOT_SUSPENDED = 'mens'
  MEMBER_SUSPENDED = 'mesu'
  MEMBER_NOT_SUSPENDED_NOT_ARCHIVED = 'nsna'
  MEMBER_SUSPENDED_ARCHIVED = 'suar'
  MEMBER_RESTRICTION = 'memr'
  MEMBER_URI = 'memu'
  MEMBERSHIP_TREE = 'metr'
  MESSAGE = 'mesg'
  MIMETYPE = 'mime'
  MOBILE_DEVICE = 'mobi'
  NAME = 'name'
  NOTE = 'note'
  NOTE_ACL = 'nota'
  NOTES_ACLS = 'naac'
  NONEDITABLE_ALIAS = 'neal'
  OAUTH2_TXT_FILE = 'oaut'
  OAUTH2SERVICE_JSON_FILE = 'oau2'
  ORGANIZATIONAL_UNIT = 'orgu'
  OTHER_CONTACT = 'otco'
  OWNER = 'ownr'
  OWNER_ID = 'owid'
  PAGE_SIZE = 'page'
  PARENT_ORGANIZATIONAL_UNIT = 'porg'
  PARTICIPANT = 'part'
  PEOPLE_CONTACT = 'peco'
  PEOPLE_CONTACT_GROUP = 'pecg'
  PEOPLE_PHOTO = 'peph'
  PEOPLE_PROFILE = 'pepr'
  PERMISSION = 'perm'
  PERMISSION_ID = 'peid'
  PERMITTEE = 'prmt'
  PERSONAL_DEVICE = 'pedv'
  PHOTO = 'phot'
  POLICY = 'poli'
  POP_ENABLED = 'popa'
  PRESENTATION = 'pres'
  PRINTER = 'prin'
  PRINTER_ID = 'prid'
  PRINTER_MODEL = 'prmd'
  PRIVILEGE = 'priv'
  PRODUCT = 'prod'
  PROFILE_SHARING_ENABLED = 'prof'
  PROJECT = 'proj'
  PROJECT_FOLDER = 'prjf'
  PROJECT_ID = 'prji'
  PUBLIC_KEY = 'pubk'
  QUERY = 'quer'
  RECIPIENT = 'recp'
  RECIPIENT_BCC = 'rebc'
  RECIPIENT_CC = 'recc'
  REPORT = 'rept'
  REQUEST_ID = 'reqi'
  RESOURCE_CALENDAR = 'resc'
  RESOURCE_ID = 'resi'
  ROLE = 'role'
  ROW = 'row '
  SCOPE = 'scop'
  SECTION = 'sect'
  SENDAS_ADDRESS = 'sasa'
  SENDER = 'send'
  SERVICE = 'serv'
  SHAREDDRIVE = 'tdrv'
  SHAREDDRIVE_ACL = 'tdac'
  SHAREDDRIVE_FOLDER = 'tdfo'
  SHAREDDRIVE_ID = 'tdid'
  SHAREDDRIVE_NAME = 'tdna'
  SHAREDDRIVE_THEME = 'tdth'
  SHEET = 'shet'
  SHEET_ID = 'shti'
  SIGNATURE = 'sign'
  SIZE = 'size'
  SKU = 'sku '
  SMIME_ID = 'smid'
  SNIPPETS_ENABLED = 'snip'
  SSO_KEY = 'ssok'
  SSO_SETTINGS = 'ssos'
  SOURCE_USER = 'src'
  SPREADSHEET = 'sprd'
  SPREADSHEET_RANGE = 'ssrn'
  START_TIME = 'strt'
  STATUS = 'stat'
  STUDENT = 'stud'
  SUBSCRIPTION = 'subs'
  SVCACCT = 'svac'
  SVCACCT_KEY = 'svky'
  TARGET_USER = 'tgt'
  TASK = 'task'
  TASKLIST = 'tali'
  TEACHER = 'teac'
  THREAD = 'thre'
  TRANSFER_APPLICATION = 'trap'
  TRANSFER_ID = 'trid'
  TRANSFER_REQUEST = 'trnr'
  TRASHED_EVENT = 'trev'
  TRUSTED_APPLICATION = 'trus'
  TYPE = 'type'
  UNICODE_ENCODING_ENABLED = 'unic'
  UNIQUE_ID = 'uniq'
  URL = 'url '
  USER = 'user'
  USER_ALIAS = 'uali'
  USER_EMAIL = 'uema'
  USER_INVITATION = 'uinv'
  USER_NOT_SUSPENDED = 'uns'
  USER_SCHEMA = 'usch'
  USER_SUSPENDED = 'usup'
  VACATION = 'vaca'
  VACATION_ENABLED = 'vace'
  VALUE = 'val'
  VAULT_EXPORT = 'vlte'
  VAULT_HOLD = 'vlth'
  VAULT_MATTER = 'vltm'
  VAULT_MATTER_ARTIFACT = 'vlma'
  VAULT_MATTER_ID = 'vlmi'
  VAULT_OPERATION = 'vlto'
  VAULT_QUERY = 'vltq'
  WEBCLIPS_ENABLED = 'webc'
  YOUTUBE_CHANNEL = 'ytch'
  # _NAMES[0] is plural, _NAMES[1] is singular unless the item name is explicitly plural (Calendar Settings)
  # For items with Boolean values, both entries are singular (Forward, POP)
  # These values can be translated into other languages
  _NAMES = {
    ACCESS_TOKEN: ['Access Tokens', 'Access Token'],
    ACCOUNT: ['Google Workspace Accounts', 'Google Workspace Account'],
    ACTION: ['Actions', 'Action'],
    ACTIVITY: ['Activities', 'Activity'],
    ADMINISTRATOR: ['Administrators', 'Administrator'],
    ADMIN_ROLE: ['Admin Roles', 'Admin Role'],
    ADMIN_ROLE_ASSIGNMENT: ['Admin Role Assignments', 'Admin Role Assignment'],
    ALERT: ['Alerts', 'Alert'],
    ALERT_ID: ['Alert IDs', 'Alert ID'],
    ALERT_FEEDBACK: ['Alert Feedbacks', 'Alert Feedback'],
    ALERT_FEEDBACK_ID: ['Alert Feedback IDs', 'Alert Feedback ID'],
    ALIAS: ['Aliases', 'Alias'],
    ALIAS_EMAIL: ['Alias Emails', 'Alias Email'],
    ALIAS_TARGET: ['Alias Targets', 'Alias Target'],
    ANALYTIC_ACCOUNT: ['Analytic Accounts', 'Analytic Account'],
    ANALYTIC_ACCOUNT_SUMMARY: ['Analytic Account Summaries', 'Analytic Account Summary'],
    ANALYTIC_DATASTREAM: ['Analytic Datastreams', 'Analytic Datastream'],
    ANALYTIC_PROPERTY: ['Analytic GA4 Properties', 'Analytic GA4 Property'],
    API: ['APIs', 'API'],
    APP_ACCESS_SETTINGS: ['Application Access Settings', 'Application Access Settings'],
    APP_ID: ['Application IDs', 'Application ID'],
    APP_NAME: ['Application Names', 'Application Name'],
    APPLICATION_SPECIFIC_PASSWORD: ['Application Specific Password IDs', 'Application Specific Password ID'],
    ARROWS_ENABLED: ['Personal Indicator Arrows Enabled', 'Personal Indicator Arrows Enabled'],
    ATTACHMENT: ['Attachments', 'Attachment'],
    ATTENDEE: ['Attendees', 'Attendee'],
    AUDIT_ACTIVITY_REQUEST: ['Audit Activity Requests', 'Audit Activity Request'],
    AUDIT_EXPORT_REQUEST: ['Audit Export Requests', 'Audit Export Request'],
    AUDIT_MONITOR_REQUEST: ['Audit Monitor Requests', 'Audit Monitor Request'],
    BACKUP_VERIFICATION_CODES: ['Backup Verification Codes', 'Backup Verification Codes'],
    BUILDING: ['Buildings', 'Building'],
    BUILDING_ID: ['Building IDs', 'Building ID'],
    CAA_LEVEL: ['CAA Levels', 'CAA Level'],
    CALENDAR: ['Calendars', 'Calendar'],
    CALENDAR_ACL: ['Calendar ACLs', 'Calendar ACL'],
    CALENDAR_SETTINGS: ['Calendar Settings', 'Calendar Settings'],
    CHANNEL_CUSTOMER: ['Channel Customers', 'Channel Customer'],
    CHANNEL_CUSTOMER_ENTITLEMENT: ['Channel Customer Entitlements', 'Channel Customer Entitlement'],
    CHANNEL_OFFER: ['Channel Offers', 'Channel Offer'],
    CHANNEL_PRODUCT: ['Channel Products', 'Channel Product'],
    CHANNEL_SKU: ['Channel SKUs', 'Channel SKU'],
    CHAT_BOT: ['Chat BOTs', 'Chat BOT'],
    CHAT_ADMIN: ['Chat Admins', 'Chat Admin'],
    CHAT_EVENT: ['Chat Events', 'Chat Event'],
    CHAT_MANAGER_USER: ['Chat User Managers', 'Chat User Manager'],
    CHAT_MESSAGE: ['Chat Messages', 'Chat Message'],
    CHAT_MESSAGE_ID: ['Chat Message IDs', 'Chat Message ID'],
    CHAT_MEMBER: ['Chat Members', 'Chat Member'],
    CHAT_MEMBER_GROUP: ['Chat Group Members', 'Chat Group Member'],
    CHAT_MEMBER_USER: ['Chat User Members', 'Chat User Member'],
    CHAT_SPACE: ['Chat Spaces', 'Chat Space'],
    CHAT_THREAD: ['Chat Threads', 'Chat Thread'],
    CHILD_ORGANIZATIONAL_UNIT: ['Child Organizational Units', 'Child Organizational Unit'],
    CHROME_APP: ['Chrome Applications', 'Chrome Application'],
    CHROME_APP_DEVICE: ['Chrome Application Devices', 'Chrome Application Device'],
    CHROME_BROWSER: ['Chrome Browsers', 'Chrome Browser'],
    CHROME_BROWSER_ENROLLMENT_TOKEN: ['Chrome Browser Enrollment Tokens', 'Chrome Browser Enrollment Token'],
    CHROME_CHANNEL: ['Chrome Channels', 'Chrome Channel'],
    CHROME_DEVICE: ['Chrome Devices', 'Chrome Device'],
    CHROME_MODEL: ['Chrome Models', 'Chrome Model'],
    CHROME_NETWORK_ID: ['Chrome Network IDs', 'Chrome Network ID'],
    CHROME_NETWORK_NAME: ['Chrome Network Names', 'Chrome Network Name'],
    CHROME_PLATFORM: ['Chrome Platforms', 'Chrome Platform'],
    CHROME_POLICY: ['Chrome Policies', 'Chrome Policy'],
    CHROME_POLICY_IMAGE: ['Chrome Policy Images', 'Chrome Policy Image'],
    CHROME_POLICY_SCHEMA: ['Chrome Policy Schemas', 'Chrome Policy Schema'],
    CHROME_PROFILE: ['Chrome Profiles', 'Chrome Profile'],
    CHROME_RELEASE: ['Chrome Releases', 'Chrome Release'],
    CHROME_VERSION: ['Chrome Versions', 'Chrome Version'],
    CLASSIFICATION_LABEL: ['Classification Labels', 'Classification Label'],
    CLASSIFICATION_LABEL_FIELD_ID: ['Classification Label Field IDs', 'Classification Label Field ID'],
    CLASSIFICATION_LABEL_ID: ['Classification Label IDs', 'Classification Label ID'],
    CLASSIFICATION_LABEL_NAME: ['Classification Label Names', 'Classification Label Name'],
    CLASSIFICATION_LABEL_PERMISSION: ['Classification Label Permissions', 'Classification Label Permission'],
    CLASSIFICATION_LABEL_PERMISSION_NAME: ['Classification Label Permission Names', 'Classification Label Permission Name'],
    CLASSROOM_INVITATION: ['Classroom Invitations', 'Classroom Invitation'],
    CLASSROOM_INVITATION_OWNER: ['Classroom Owner Invitations', 'Classroom Owner Invitation'],
    CLASSROOM_INVITATION_STUDENT: ['Classroom Student Invitations', 'Classroom Student Invitation'],
    CLASSROOM_INVITATION_TEACHER: ['Classroom Teacher Invitations', 'Classroom Teacher Invitation'],
    CLASSROOM_OAUTH2_TXT_FILE: ['Classroom OAuth2 File', 'Classroom OAuth2 File'],
    CLASSROOM_USER_PROFILE: ['Classroom User Profile', 'Classroom User Profile'],
    CLIENT_ID: ['Client IDs', 'Client ID'],
    CLIENT_SECRETS_JSON_FILE: ['Client Secrets File', 'Client Secrets File'],
    CLOUD_IDENTITY_GROUP: ['Cloud Identity Groups', 'Cloud Identity Group'],
    CLOUD_STORAGE_BUCKET: ['Cloud Storage Buckets', 'Cloud Storage Bucket'],
    CLOUD_STORAGE_FILE: ['Cloud Storage Files', 'Cloud Storage File'],
    COLLABORATOR: ['Collaborators', 'Collaborator'],
    COMMAND_ID: ['Command IDs', 'Command ID'],
    COMPANY_DEVICE: ['Company Devices', 'Company Device'],
    CONFIG_FILE: ['Config File', 'Config File'],
    CONTACT: ['Contacts', 'Contact'],
    CONTACT_DELEGATE: ['Contact Delegates', 'Contact Delegate'],
    CONTACT_GROUP: ['Contact Groups', 'Contact Group'],
    CONTACT_GROUP_NAME: ['Contact Group Names', 'Contact Group Name'],
    COPYFROM_COURSE: ['Copy From Courses', 'CopyFrom Course'],
    COPYFROM_GROUP: ['Copy From Groups', 'CopyFrom Group'],
    COURSE: ['Courses', 'Course'],
    COURSE_ALIAS: ['Course Aliases', 'Course Alias'],
    COURSE_ANNOUNCEMENT: ['Course Announcements', 'Course Announcement'],
    COURSE_ANNOUNCEMENT_ID: ['Course Announcement IDs', 'Course Announcement ID'],
    COURSE_ANNOUNCEMENT_STATE: ['Course Announcement States', 'Course Announcement State'],
    COURSE_MATERIAL_DRIVEFILE: ['Course Material Drive Files', 'Course Material Drive File'],
    COURSE_MATERIAL_FORM: ['Course Material Forms', 'Course Material Form'],
    COURSE_MATERIAL: ['Course Materials', 'Course Material'],
    COURSE_MATERIAL_ID: ['Course Material IDs', 'Course Material ID'],
    COURSE_MATERIAL_STATE: ['Course Material States', 'Course Material State'],
    COURSE_NAME: ['Course Names', 'Course Name'],
    COURSE_STATE: ['Course States', 'Course State'],
    COURSE_SUBMISSION_ID: ['Course Submission IDs', 'Course Submission ID'],
    COURSE_SUBMISSION_STATE: ['Course Submission States', 'Course Submission State'],
    COURSE_TOPIC: ['Course Topics', 'Course Topic'],
    COURSE_TOPIC_ID: ['Course Topic IDs', 'Course Topic ID'],
    COURSE_WORK: ['Course Works', 'Course Work'],
    COURSE_WORK_ID: ['Course Work IDs', 'Course Work ID'],
    COURSE_WORK_STATE: ['Course Work States', 'Course Work State'],
    CREATOR_ID: ['Creator IDs', 'Creator ID'],
    CREDENTIALS: ['Credentials', 'Credentials'],
    CRITERIA: ['Criteria', 'Criteria'],
    CROS_DEVICE: ['CrOS Devices', 'CrOS Device'],
    CROS_SERIAL_NUMBER: ['CrOS Serial Numbers', 'CrOS Serial Numbers'],
    CSE_IDENTITY: ['CSE Identities', 'CSE Identity'],
    CSE_KEYPAIR: ['CSE KeyPairs', 'CSE KeyPair'],
    CUSTOMER_DOMAIN: ['Customer Domains', 'Customer Domain'],
    CUSTOMER_ID: ['Customer IDs', 'Customer ID'],
    DATE: ['Dates', 'Date'],
    DEFAULT_LANGUAGE: ['Default Language', 'Default Language'],
    DELEGATE: ['Delegates', 'Delegate'],
    DELETED_USER: ['Deleted Users', 'Deleted User'],
    DELIVERY: ['Delivery', 'Delivery'],
    DEVICE: ['Devices', 'Device'],
    DEVICE_FILE: ['Device Files', 'Device File'],
    DEVICE_USER: ['Device Users', 'Device User'],
    DEVICE_USER_CLIENT_STATE: ['Device Users Client States', 'Device User Client State'],
    DIRECTORY: ['Directories', 'Directory'],
    DISCOVERY_JSON_FILE: ['Discovery File', 'Discovery File'],
    DOCUMENT: ['Documents', 'Document'],
    DOMAIN: ['Domains', 'Domain'],
    DOMAIN_ALIAS: ['Domain Aliases', 'Domain Alias'],
    DOMAIN_CONTACT: ['Domain Contacts', 'Domain Contact'],
    DOMAIN_PEOPLE_CONTACT: ['Domain People Contacts', 'Domain People Contact'],
    DOMAIN_PROFILE: ['Domain Profiles', 'Domain Profile'],
    DRIVE_DISK_USAGE: ['Drive Disk Usages', 'Drive Disk Usage'],
    DRIVE_FILE: ['Drive Files', 'Drive File'],
    DRIVE_FILE_COMMENT: ['Drive File Comments', 'Drive File Comment'],
    DRIVE_FILE_ID: ['Drive File IDs', 'Drive File ID'],
    DRIVE_FILE_NAME: ['Drive File Names', 'Drive File Name'],
    DRIVE_FILE_REVISION: ['Drive File Revisions', 'Drive File Revision'],
    DRIVE_FILE_RENAMED: ['Drive Files Renamed', 'Drive File Renamed'],
    DRIVE_FILE_SHORTCUT: ['Drive File Shortcuts', 'Drive File Shortcut'],
    DRIVE_FILE_OR_FOLDER: ['Drive Files/Folders', 'Drive File/Folder'],
    DRIVE_FILE_OR_FOLDER_ACL: ['Drive File/Folder ACLs', 'Drive File/Folder ACL'],
    DRIVE_FILE_OR_FOLDER_ID: ['Drive File/Folder IDs', 'Drive File/Folder ID'],
    DRIVE_FOLDER: ['Drive Folders', 'Drive Folder'],
    DRIVE_FOLDER_ID: ['Drive Folder IDs', 'Drive Folder ID'],
    DRIVE_FOLDER_NAME: ['Drive Folder Names', 'Drive Folder Name'],
    DRIVE_FOLDER_PATH: ['Drive Folder Paths', 'Drive Folder Path'],
    DRIVE_FOLDER_RENAMED: ['Drive Folders Renamed', 'Drive Folder Renamed'],
    DRIVE_FOLDER_SHORTCUT: ['Drive Folder Shortcuts', 'Drive Folder Shortcut'],
    DRIVE_ORPHAN_FILE_OR_FOLDER: ['Drive Orphan Files/Folders', 'Drive Orphan File/Folder'],
    DRIVE_PARENT_FOLDER: ['Drive Parent Folders', 'Drive Parent Folder'],
    DRIVE_PARENT_FOLDER_ID: ['Drive Parent Folder IDs', 'Drive Parent Folder ID'],
    DRIVE_PARENT_FOLDER_REFERENCE: ['Drive Parent Folder References', 'Drive Parent Folder Reference'],
    DRIVE_PATH: ['Drive Paths', 'Drive Path'],
    DRIVE_SETTINGS: ['Drive Settings', 'Drive Settings'],
    DRIVE_SHORTCUT: ['Drive Shortcuts', 'Drive Shortcut'],
    DRIVE_SHORTCUT_ID: ['Drive Shortcut IDs', 'Drive Shortcut ID'],
    DRIVE_3PSHORTCUT: ['Drive 3rd Party Shortcuts', 'Drive 3rd Party Shortcut'],
    DRIVE_TRASH: ['Drive Trash', 'Drive Trash'],
    EMAIL: ['Email Addresses', 'Email Address'],
    EMAIL_ALIAS: ['Email Aliases', 'Email Alias'],
    EMAIL_SETTINGS: ['Email Settings', 'Email Settings'],
    END_TIME: ['End Times', 'End Time'],
    ENTITY: ['Entities', 'Entity'],
    EVENT: ['Events', 'Event'],
    EVENT_BIRTHDAY: ['Borthday Events', 'Birthday Event'],
    EVENT_FOCUSTIME: ['Focus Time Events', 'Focus Time Event'],
    EVENT_OUTOFOFFICE: ['Out of Office Events', 'Out of Office Event'],
    EVENT_WORKINGLOCATION: ['Working Location Events', 'Working Location Event'],
    FEATURE: ['Features', 'Feature'],
    FIELD: ['Fields', 'Field'],
    FILE: ['Files', 'File'],
    FILE_PARENT_TREE: ['File Parent Trees', 'File Parent Tree'],
    FILTER: ['Filters', 'Filter'],
    FORM: ['Forms', 'Form'],
    FORM_RESPONSE: ['Form Responses', 'Form Response'],
    FORWARD_ENABLED: ['Forward Enabled', 'Forward Enabled'],
    FORWARDING_ADDRESS: ['Forwarding Addresses', 'Forwarding Address'],
    GCP_FOLDER: ['GCP Folders', 'GCP Folder'],
    GCP_FOLDER_NAME: ['GCP Folder Names', 'GCP Folder Name'],
    GMAIL_PROFILE: ['Gmail Profile', 'Gmail Profile'],
    GROUP: ['Groups', 'Group'],
    GROUP_ALIAS: ['Group Aliases', 'Group Alias'],
    GROUP_EMAIL: ['Group Emails', 'Group Email'],
    GROUP_MEMBERSHIP: ['Group Memberships', 'Group Membership'],
    GROUP_MEMBERSHIP_TREE: ['Group Membership Trees', 'Group Membership Tree'],
    GROUP_SETTINGS: ['Group Settings', 'Group Settings'],
    GROUP_TREE: ['Group Trees', 'Group Tree'],
    GUARDIAN: ['Guardians', 'Guardian'],
    GUARDIAN_INVITATION: ['Guardian Invitations', 'Guardian Invitation'],
    GUARDIAN_AND_INVITATION: ['Guardians and Invitations', 'Guardian and Invitation'],
    IAM_POLICY: ['IAM Policies', 'IAM Policy'],
    IMAP_ENABLED: ['IMAP Enabled', 'IMAP Enabled'],
    INBOUND_SSO_ASSIGNMENT: ['Inbound SSO Assignments', 'Inbound SSO Assignment'],
    INBOUND_SSO_CREDENTIALS: ['Inbound SSO Credentials', 'Inbound SSO Credential'],
    INBOUND_SSO_PROFILE: ['Inbound SSO Profiles', 'Inbound SSO Profile'],
    INSTANCE: ['Instances', 'Instance'],
    ISSUER_CN: ['Issuer CNs', 'Issuer CN'],
    ITEM: ['Items', 'Item'],
    KEYBOARD_SHORTCUTS_ENABLED: ['Keyboard Shortcuts Enabled', 'Keyboard Shortcuts Enabled'],
    LABEL: ['Labels', 'Label'],
    LABEL_ID: ['Label IDs', 'Label ID'],
    LANGUAGE: ['Languages', 'Language'],
    LICENSE: ['Licenses', 'License'],
    LOCATION: ['Locations', 'Location'],
    LOOKERSTUDIO_ASSET: ['Looker Studio Assets', 'Looker Studio Asset'],
    LOOKERSTUDIO_ASSET_DATASOURCE: ['Looker Studio DATA_SOURCE Assets', 'Looker Studio DATA_SOURCE Asset'],
    LOOKERSTUDIO_ASSETID: ['Looker Studio Asset IDs', 'Looker Studio Asset ID'],
    LOOKERSTUDIO_ASSET_REPORT: ['Looker Studio REPORT Assets', 'Looker Studio REPORT Asset'],
    LOOKERSTUDIO_PERMISSION: ['Looker Studio Permissions', 'Looker Studio Permission'],
    MD5HASH: ['MD5 hash', 'MD5 Hash'],
    MEET_SPACE: ['Meet Spaces', 'Meet Space'],
    MEET_CONFERENCE: ['Meet Conferences', 'Meet Conference'],
    MEET_PARTICIPANT: ['Meet Participants', 'Meet Participant'],
    MEET_RECORDING: ['Meet Recordings', 'Meet Recording'],
    MEET_TRANSCRIPT: ['Meet Transcripts', 'Meet Transcript'],
    MEMBER: ['Members', 'Member'],
    MEMBER_NOT_ARCHIVED: ['Members (Not Archived)', 'Member (Not Archived)'],
    MEMBER_ARCHIVED: ['Members (Archived)', 'Member (Archived)'],
    MEMBER_NOT_SUSPENDED: ['Members (Not Suspended)', 'Member (Not Suspended)'],
    MEMBER_SUSPENDED: ['Members (Suspended)', 'Member (Suspended)'],
    MEMBER_NOT_SUSPENDED_NOT_ARCHIVED: ['Members (Not Suspended & Not Archived)', 'Member (Not Suspended & Not Archived)'],
    MEMBER_SUSPENDED_ARCHIVED: ['Members (Suspended & Archived)', 'Member (Suspended & Archived)'],
    MEMBER_RESTRICTION: ['Member Restrictions', 'Member Restriction'],
    MEMBER_URI: ['Member URIs', 'Member URI'],
    MEMBERSHIP_TREE: ['Membership Trees', 'Membership Tree'],
    MESSAGE: ['Messages', 'Message'],
    MIMETYPE: ['MIME Types', 'MIME Type'],
    MOBILE_DEVICE: ['Mobile Devices', 'Mobile Device'],
    NAME: ['Names', 'Name'],
    NOTE: ['Notes', 'Note'],
    NOTE_ACL: ['Note ACLs', 'Note ACL'],
    NOTES_ACLS: ["'Note's ACLs", "Note's ACLs"],
    NONEDITABLE_ALIAS: ['Non-Editable Aliases', 'Non-Editable Alias'],
    OAUTH2_TXT_FILE: ['Client OAuth2 File', 'Client OAuth2 File'],
    OAUTH2SERVICE_JSON_FILE: ['Service Account OAuth2 File', 'Service Account OAuth2 File'],
    ORGANIZATIONAL_UNIT: ['Organizational Units', 'Organizational Unit'],
    OTHER_CONTACT: ['Other Contacts', 'Other Contact'],
    OWNER: ['Owners', 'Owner'],
    OWNER_ID: ['Owner IDs', 'Owner ID'],
    PAGE_SIZE: ['Page Size', 'Page Size'],
    PARENT_ORGANIZATIONAL_UNIT: ['Parent Organizational Units', 'Parent Organizational Unit'],
    PARTICIPANT: ['Participants', 'Participant'],
    PEOPLE_CONTACT: ['People Contacts', 'Person Contact'],
    PEOPLE_CONTACT_GROUP: ['People Contact Groups', 'People Contact Group'],
    PEOPLE_PHOTO: ['People Photos', 'Person Photo'],
    PEOPLE_PROFILE: ['People Profiles', 'People Profile'],
    PERMISSION: ['Permissions', 'Permission'],
    PERMISSION_ID: ['Permission IDs', 'Permission ID'],
    PERMITTEE: ['Permittees', 'Permittee'],
    PERSONAL_DEVICE: ['Personal Devices', 'Personal Device'],
    PHOTO: ['Photos', 'Photo'],
    POLICY: ['Policies', 'Policy'],
    POP_ENABLED: ['POP Enabled', 'POP Enabled'],
    PRESENTATION: ['Presentations', 'Presentation'],
    PRINTER: ['Printers', 'Printer'],
    PRINTER_ID: ['Printer IDs', 'Printer ID'],
    PRINTER_MODEL: ['Printer Models', 'Printer Model'],
    PRIVILEGE: ['Privileges', 'Privilege'],
    PRODUCT: ['Products', 'Product'],
    PROFILE_SHARING_ENABLED: ['Profile Sharing Enabled', 'Profile Sharing Enabled'],
    PROJECT: ['Projects', 'Project'],
    PROJECT_FOLDER: ['Project Folders', 'Project Folder'],
    PROJECT_ID: ['Project IDs', 'Project ID'],
    PUBLIC_KEY: ['Public Key', 'Public Key'],
    QUERY: ['Queries', 'Query'],
    RECIPIENT: ['Recipients', 'Recipient'],
    RECIPIENT_BCC: ['Recipients (BCC)', 'Recipient (BCC)'],
    RECIPIENT_CC: ['Recipients (CC)', 'Recipient (CC)'],
    REPORT: ['Reports', 'Report'],
    REQUEST_ID: ['Request IDs', 'Request ID'],
    RESOURCE_CALENDAR: ['Resource Calendars', 'Resource Calendar'],
    RESOURCE_ID: ['Resource IDs', 'Resource ID'],
    ROLE: ['Roles', 'Role'],
    ROW: ['Rows', 'Row'],
    SCOPE: ['Scopes', 'Scope'],
    SECTION: ['Sections', 'Section'],
    SENDAS_ADDRESS: ['SendAs Addresses', 'SendAs Address'],
    SENDER: ['Senders', 'Sender'],
    SERVICE: ['Services', 'Service'],
    SHAREDDRIVE: ['Shared Drives', 'Shared Drive'],
    SHAREDDRIVE_ACL: ['Shared Drive ACLs', 'Shared Drive ACL'],
    SHAREDDRIVE_FOLDER: ['Shared Drive Folders', 'Shared Drive Folder'],
    SHAREDDRIVE_ID: ['Shared Drive IDs', 'Shared Drive ID'],
    SHAREDDRIVE_NAME: ['Shared Drive Names', 'Shared Drive Name'],
    SHAREDDRIVE_THEME: ['Shared Drive Themes', 'Shared Drive Theme'],
    SHEET: ['Sheets', 'Sheet'],
    SHEET_ID: ['Sheet IDs', 'Sheet ID'],
    SIGNATURE: ['Signatures', 'Signature'],
    SIZE: ['Sizes', 'Size'],
    SKU: ['SKUs', 'SKU'],
    SMIME_ID: ['S/MIME Certificate IDs', 'S/MIME Certificate ID'],
    SNIPPETS_ENABLED: ['Preview Snippets Enabled', 'Preview Snippets Enabled'],
    SSO_KEY: ['SSO Key', 'SSO Key'],
    SSO_SETTINGS: ['SSO Settings', 'SSO Settings'],
    SOURCE_USER: ['Source Users', 'Source User'],
    SPREADSHEET: ['Spreadsheets', 'Spreadsheet'],
    SPREADSHEET_RANGE: ['Spreadsheet Ranges', 'Spreadsheet Range'],
    START_TIME: ['Start Times', 'Start Time'],
    STATUS: ['Status', 'Status'],
    STUDENT: ['Students', 'Student'],
    SUBSCRIPTION: ['Subscriptions', 'Subscription'],
    SVCACCT: ['Service Accounts', 'Service Account'],
    SVCACCT_KEY: ['Service Account Keys', 'Service Account Key'],
    TARGET_USER: ['Target Users', 'Target User'],
    TASK: ['Tasks', 'Task'],
    TASKLIST: ['Tasklists', 'Tasklist'],
    TEACHER: ['Teachers', 'Teacher'],
    THREAD: ['Threads', 'Thread'],
    TRANSFER_APPLICATION: ['Transfer Applications', 'Transfer Application'],
    TRANSFER_ID: ['Transfer IDs', 'Transfer ID'],
    TRANSFER_REQUEST: ['Transfer Requests', 'Transfer Request'],
    TRASHED_EVENT: ['Trashed Events', 'Trashed Event'],
    TRUSTED_APPLICATION: ['Trusted Applications', 'Trusted Application'],
    TYPE: ['Types', 'Type'],
    UNICODE_ENCODING_ENABLED: ['UTF-8 Encoding Enabled', 'UTF-8 Encoding Enabled'],
    UNIQUE_ID: ['Unique IDs', 'Unique ID'],
    URL: ['URLs', 'URL'],
    USER: ['Users', 'User'],
    USER_ALIAS: ['User Aliases', 'User Alias'],
    USER_EMAIL: ['User Emails', 'User Email'],
    USER_INVITATION: ['User Invitations', 'User Invitation'],
    USER_NOT_SUSPENDED: ['Users (Not suspended)', 'User (Not suspended)'],
    USER_SCHEMA: ['Schemas', 'Schema'],
    USER_SUSPENDED: ['Users (Suspended)', 'User (Suspended)'],
    VACATION: ['Vacation', 'Vacation'],
    VACATION_ENABLED: ['Vacation Enabled', 'Vacation Enabled'],
    VALUE: ['Values', 'Value'],
    VAULT_EXPORT: ['Vault Exports', 'Vault Export'],
    VAULT_HOLD: ['Vault Holds', 'Vault Hold'],
    VAULT_MATTER: ['Vault Matters', 'Vault Matter'],
    VAULT_MATTER_ARTIFACT: ['Vault Matter Artifacts', 'Vault Matter Artifact'],
    VAULT_MATTER_ID: ['Vault Matter IDs', 'Vault Matter ID'],
    VAULT_OPERATION: ['Vault Operations', 'Vault Operation'],
    VAULT_QUERY: ['Vault Queries', 'Vault Query'],
    WEBCLIPS_ENABLED: ['Web Clips Enabled', 'Web Clips Enabled'],
    YOUTUBE_CHANNEL: ['YouTube Channels', 'YouTube Channel'],
    ROLE_MANAGER: ['Managers', 'Manager'],
    ROLE_MEMBER: ['Members', 'Member'],
    ROLE_OWNER: ['Owners', 'Owner'],
    ROLE_ALL: ['Members, Managers, Owners', 'Member, Manager, Owner'],
    ROLE_USER: ['Users', 'User'],
    ROLE_MANAGER_MEMBER: ['Members, Managers', 'Member, Manager'],
    ROLE_MANAGER_OWNER: ['Managers, Owners', 'Manager, Owner'],
    ROLE_MEMBER_OWNER: ['Members, Owners', 'Member, Owner'],
    ROLE_MANAGER_MEMBER_OWNER: ['Members, Managers, Owners', 'Member, Manager, Owner'],
    ROLE_PUBLIC: ['Public', 'Public'],
    }

  def __init__(self):
    self.entityType = None
    self.forWhom = None
    self.preQualifier = ''
    self.postQualifier = ''

  def SetGetting(self, entityType):
    self.entityType = entityType
    self.preQualifier = self.postQualifier = ''

  def SetGettingQuery(self, entityType, query):
    self.entityType = entityType
    self.preQualifier = f' that match query ({query})'
    self.postQualifier = f' that matched query ({query})'

  def SetGettingQualifier(self, entityType, qualifier):
    self.entityType = entityType
    self.preQualifier = self.postQualifier = qualifier

  def Getting(self):
    return self.entityType

  def GettingPreQualifier(self):
    return self.preQualifier

  def GettingPostQualifier(self):
    return self.postQualifier

  def SetGettingForWhom(self, forWhom):
    self.forWhom = forWhom

  def GettingForWhom(self):
    return self.forWhom

  def Choose(self, entityType, count):
    return self._NAMES[entityType][[0, 1][count == 1]]

  def ChooseGetting(self, count):
    return self._NAMES[self.entityType][[0, 1][count == 1]]

  def Plural(self, entityType):
    return self._NAMES[entityType][0]

  def PluralGetting(self):
    return self._NAMES[self.entityType][0]

  def Singular(self, entityType):
    return self._NAMES[entityType][1]

  def SingularGetting(self):
    return self._NAMES[self.entityType][1]

  def MayTakeTime(self, entityType):
    if entityType:
      return f', may take some time on a large {self.Singular(entityType)}...'
    return ''

  def FormatEntityValueList(self, entityValueList):
    evList = []
    for j in range(0, len(entityValueList), 2):
      evList.append(self.Singular(entityValueList[j]))
      evList.append(entityValueList[j+1])
    return evList

  def TypeMessage(self, entityType, message):
    return f'{self.Singular(entityType)}: {message}'

  def TypeName(self, entityType, entityName):
    return f'{self.Singular(entityType)}: {entityName}'

  def TypeNameMessage(self, entityType, entityName, message):
    return f'{self.Singular(entityType)}: {entityName} {message}'
