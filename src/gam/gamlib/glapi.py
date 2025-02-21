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

"""Google API resources

"""
# APIs
ACCESSCONTEXTMANAGER = 'accesscontextmanager'
ALERTCENTER = 'alertcenter'
ANALYTICS = 'analytics'
ANALYTICS_ADMIN = 'analyticsadmin'
CALENDAR = 'calendar'
CBCM = 'cbcm'
CHAT = 'chat'
CHAT_EVENTS = 'chatevents'
CHAT_MEMBERSHIPS = 'chatmemberships'
CHAT_MEMBERSHIPS_ADMIN = 'chatmembershipsadmin'
CHAT_MESSAGES = 'chatmessages'
CHAT_SPACES = 'chatspaces'
CHAT_SPACES_ADMIN = 'chatspacesadmin'
CHAT_SPACES_DELETE = 'chatspacesdelete'
CHAT_SPACES_DELETE_ADMIN = 'chatspacesdeleteadmin'
CHROMEMANAGEMENT = 'chromemanagement'
CHROMEMANAGEMENT_APPDETAILS = 'chromemanagementappdetails'
CHROMEMANAGEMENT_CHROMEPROFILES = 'chromemanagementchromeprofiles'
CHROMEMANAGEMENT_TELEMETRY = 'chromemanagementtelemetry'
CHROMEPOLICY = 'chromepolicy'
CHROMEVERSIONHISTORY = 'versionhistory'
CLASSROOM = 'classroom'
CLOUDCHANNEL = 'cloudchannel'
CLOUDIDENTITY_DEVICES = 'cloudidentitydevices'
CLOUDIDENTITY_GROUPS = 'cloudidentitygroups'
CLOUDIDENTITY_GROUPS_BETA = 'cloudidentitygroupsbeta'
CLOUDIDENTITY_INBOUND_SSO = 'cloudidentityinboundsso'
CLOUDIDENTITY_ORGUNITS = 'cloudidentityorgunits'
CLOUDIDENTITY_ORGUNITS_BETA = 'cloudidentityorgunitsbeta'
CLOUDIDENTITY_POLICY = 'cloudidentitypolicy'
CLOUDIDENTITY_USERINVITATIONS = 'cloudidentityuserinvitations'
CLOUDRESOURCEMANAGER = 'cloudresourcemanager'
CONTACTS = 'contacts'
CONTACTDELEGATION = 'contactdelegation'
DATATRANSFER = 'datatransfer'
DIRECTORY = 'directory'
DOCS = 'docs'
DRIVE2 = 'drive2'
DRIVE3 = 'drive3'
DRIVETD = 'drivetd'
DRIVEACTIVITY = 'driveactivity'
DRIVELABELS = 'drivelabels'
DRIVELABELS_ADMIN = 'drivelabelsadmin'
DRIVELABELS_USER = 'drivelabelsuser'
EMAIL_AUDIT = 'email-audit'
FORMS = 'forms'
GMAIL = 'gmail'
GROUPSMIGRATION = 'groupsmigration'
GROUPSSETTINGS = 'groupssettings'
IAM = 'iam'
IAM_CREDENTIALS = 'iamcredentials'
KEEP = 'keep'
LICENSING = 'licensing'
LOOKERSTUDIO = 'datastudio'
MEET = 'meet'
MEET_BETA = 'meetbeta'
OAUTH2 = 'oauth2'
ORGPOLICY = 'orgpolicy'
PEOPLE = 'people'
PEOPLE_DIRECTORY = 'peopledirectory'
PEOPLE_OTHERCONTACTS = 'peopleothercontacts'
PRINTERS = 'printers'
PUBSUB = 'pubsub'
REPORTS = 'reports'
RESELLER = 'reseller'
SERVICEACCOUNTLOOKUP = 'serviceaccountlookup'
SERVICEMANAGEMENT = 'servicemanagement'
SERVICEUSAGE = 'serviceusage'
SHEETS = 'sheets'
SHEETSTD = 'sheetstd'
SITEVERIFICATION = 'siteVerification'
STORAGE = 'storage'
STORAGEREAD = 'storageread'
STORAGEWRITE = 'storagewrite'
TASKS = 'tasks'
VAULT = 'vault'
YOUTUBE = 'youtube'
#
CHROMEVERSIONHISTORY_URL = 'https://versionhistory.googleapis.com/v1/chrome/platforms'
DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
GMAIL_SEND_SCOPE = 'https://www.googleapis.com/auth/gmail.send'
GOOGLE_AUTH_PROVIDER_X509_CERT_URL = 'https://www.googleapis.com/oauth2/v1/certs'
GOOGLE_OAUTH2_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_OAUTH2_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
CLOUD_PLATFORM_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
IAM_SCOPE = 'https://www.googleapis.com/auth/iam'
PEOPLE_SCOPE = 'https://www.googleapis.com/auth/contacts'
STORAGE_READONLY_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_only'
STORAGE_READWRITE_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_write'
USERINFO_EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email' # email
USERINFO_PROFILE_SCOPE = 'https://www.googleapis.com/auth/userinfo.profile' # profile
VAULT_SCOPES = ['https://www.googleapis.com/auth/ediscovery', 'https://www.googleapis.com/auth/ediscovery.readonly']
REQUIRED_SCOPES = [USERINFO_EMAIL_SCOPE, USERINFO_PROFILE_SCOPE]
REQUIRED_SCOPES_SET = set(REQUIRED_SCOPES)
#
JWT_APIS = {
  ACCESSCONTEXTMANAGER: [CLOUD_PLATFORM_SCOPE],
  CHAT: ['https://www.googleapis.com/auth/chat.bot'],
  CLOUDRESOURCEMANAGER: [CLOUD_PLATFORM_SCOPE],
  ORGPOLICY: [CLOUD_PLATFORM_SCOPE],
  }
#
SCOPELESS_APIS = {
  CHROMEVERSIONHISTORY,
  OAUTH2,
  SERVICEACCOUNTLOOKUP,
  }
#
APIS_NEEDING_ACCESS_TOKEN = {
  CBCM: ['https://www.googleapis.com/auth/admin.directory.device.chromebrowsers']
  }
#
REFRESH_PERM_ERRORS = [
  'invalid_grant: reauth related error (rapt_required)', # no way to reauth today
  'invalid_grant: Token has been expired or revoked',
  ]

OAUTH2_TOKEN_ERRORS = [
  'access_denied',
  'access_denied: Requested client not authorized',
  'access_denied: Account restricted',
  'internal_failure: Backend Error',
  'internal_failure: None',
  'invalid_grant',
  'invalid_grant: Bad Request',
  'invalid_grant: Invalid email or User ID',
  'invalid_grant: Not a valid email',
  'invalid_grant: Invalid JWT: No valid verifier found for issuer',
  'invalid_grant: reauth related error (invalid_rapt)',
  'invalid_grant: The account has been deleted',
  'invalid_request: Invalid impersonation prn email address'
  ]
OAUTH2_UNAUTHORIZED_ERRORS = [
  'unauthorized_client: Client is unauthorized to retrieve access tokens using this method',
  'unauthorized_client: Client is unauthorized to retrieve access tokens using this method, or client not authorized for any of the scopes requested',
  'unauthorized_client: Unauthorized client or scope in request',
  ]

PROJECT_APIS = [
  'accesscontextmanager.googleapis.com',
  'admin.googleapis.com',
  'alertcenter.googleapis.com',
  'analytics.googleapis.com',
  'analyticsadmin.googleapis.com',
#  'audit.googleapis.com',
  'calendar-json.googleapis.com',
  'chat.googleapis.com',
  'chromemanagement.googleapis.com',
  'chromepolicy.googleapis.com',
  'classroom.googleapis.com',
  'cloudchannel.googleapis.com',
  'cloudidentity.googleapis.com',
  'cloudresourcemanager.googleapis.com',
  'contacts.googleapis.com',
  'datastudio.googleapis.com',
  'docs.googleapis.com',
  'drive.googleapis.com',
  'driveactivity.googleapis.com',
  'drivelabels.googleapis.com',
  'forms.googleapis.com',
  'gmail.googleapis.com',
  'groupsmigration.googleapis.com',
  'groupssettings.googleapis.com',
  'iam.googleapis.com',
  'keep.googleapis.com',
  'licensing.googleapis.com',
  'meet.googleapis.com',
  'people.googleapis.com',
  'pubsub.googleapis.com',
  'reseller.googleapis.com',
  'sheets.googleapis.com',
  'siteverification.googleapis.com',
  'storage-api.googleapis.com',
  'tasks.googleapis.com',
  'vault.googleapis.com',
  'youtube.googleapis.com',
  ]

_INFO = {
  ACCESSCONTEXTMANAGER: {'name': 'Access Context Manager API', 'version': 'v1', 'v2discovery': True},
  ALERTCENTER: {'name': 'AlertCenter API', 'version': 'v1beta1', 'v2discovery': True},
  ANALYTICS: {'name': 'Analytics API', 'version': 'v3', 'v2discovery': False},
  ANALYTICS_ADMIN: {'name': 'Analytics Admin API', 'version': 'v1beta', 'v2discovery': True},
  CALENDAR: {'name': 'Calendar API', 'version': 'v3', 'v2discovery': True, 'mappedAPI': 'calendar-json'},
  CBCM: {'name': 'Chrome Browser Cloud Management API', 'version': 'v1.1beta1', 'v2discovery': True, 'localjson': True},
  CHAT: {'name': 'Chat API', 'version': 'v1', 'v2discovery': True},
  CHAT_EVENTS: {'name': 'Chat API - Events', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_MEMBERSHIPS: {'name': 'Chat API - Memberships', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_MEMBERSHIPS_ADMIN: {'name': 'Chat API - Memberships Admin', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_MESSAGES: {'name': 'Chat API - Messages', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_SPACES: {'name': 'Chat API - Spaces', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_SPACES_ADMIN: {'name': 'Chat API - Spaces Admin', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_SPACES_DELETE: {'name': 'Chat API - Spaces Delete', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CHAT_SPACES_DELETE_ADMIN: {'name': 'Chat API - Spaces Delete Admin', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHAT},
  CLASSROOM: {'name': 'Classroom API', 'version': 'v1', 'v2discovery': True},
  CHROMEMANAGEMENT: {'name': 'Chrome Management API', 'version': 'v1', 'v2discovery': True},
  CHROMEMANAGEMENT_APPDETAILS: {'name': 'Chrome Management API - AppDetails', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHROMEMANAGEMENT},
  CHROMEMANAGEMENT_TELEMETRY: {'name': 'Chrome Management API - Telemetry', 'version': 'v1', 'v2discovery': True, 'mappedAPI': CHROMEMANAGEMENT},
  CHROMEPOLICY: {'name': 'Chrome Policy API', 'version': 'v1', 'v2discovery': True},
  CHROMEVERSIONHISTORY: {'name': 'Chrome Version History API', 'version': 'v1', 'v2discovery': True},
  CLOUDCHANNEL: {'name': 'Channel Channel API', 'version': 'v1', 'v2discovery': True},
  CLOUDIDENTITY_DEVICES: {'name': 'Cloud Identity Devices API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_GROUPS: {'name': 'Cloud Identity Groups API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_GROUPS_BETA: {'name': 'Cloud Identity Groups API', 'version': 'v1beta1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_INBOUND_SSO: {'name': 'Cloud Identity Inbound SSO API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_ORGUNITS: {'name': 'Cloud Identity OrgUnits API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_ORGUNITS_BETA: {'name': 'Cloud Identity OrgUnits API', 'version': 'v1beta1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_POLICY: {'name': 'Cloud Identity Policy API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDIDENTITY_USERINVITATIONS: {'name': 'Cloud Identity User Invitations API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': 'cloudidentity'},
  CLOUDRESOURCEMANAGER: {'name': 'Cloud Resource Manager API v3', 'version': 'v3', 'v2discovery': True},
  CONTACTS: {'name': 'Contacts API', 'version': 'v3', 'v2discovery': False},
  CONTACTDELEGATION: {'name': 'Contact Delegation API', 'version': 'v1', 'v2discovery': True, 'localjson': True},
  DATATRANSFER: {'name': 'Data Transfer API', 'version': 'datatransfer_v1', 'v2discovery': True, 'mappedAPI': 'admin'},
  DIRECTORY: {'name': 'Directory API', 'version': 'directory_v1', 'v2discovery': True, 'mappedAPI': 'admin'},
  DOCS: {'name': 'Docs API', 'version': 'v1', 'v2discovery': True},
  DRIVE2: {'name': 'Drive API v2', 'version': 'v2', 'v2discovery': False, 'mappedAPI': 'drive'},
  DRIVE3: {'name': 'Drive API v3', 'version': 'v3', 'v2discovery': False, 'mappedAPI': 'drive'},
  DRIVETD: {'name': 'Drive API v3 - todrive', 'version': 'v3', 'v2discovery': False, 'mappedAPI': 'drive'},
  DRIVEACTIVITY: {'name': 'Drive Activity API v2', 'version': 'v2', 'v2discovery': True},
  DRIVELABELS_ADMIN: {'name': 'Drive Labels API - Admin', 'version': 'v2', 'v2discovery': True, 'mappedAPI': DRIVELABELS},
  DRIVELABELS_USER: {'name': 'Drive Labels API - User', 'version': 'v2', 'v2discovery': True, 'mappedAPI': DRIVELABELS},
  EMAIL_AUDIT: {'name': 'Email Audit API', 'version': 'v1', 'v2discovery': False},
  FORMS: {'name': 'Forms API', 'version': 'v1', 'v2discovery': True},
  GMAIL: {'name': 'Gmail API', 'version': 'v1', 'v2discovery': True},
  GROUPSMIGRATION: {'name': 'Groups Migration API', 'version': 'v1', 'v2discovery': False},
  GROUPSSETTINGS: {'name': 'Groups Settings API', 'version': 'v1', 'v2discovery': True},
  IAM: {'name': 'Identity and Access Management API', 'version': 'v1', 'v2discovery': True},
  IAM_CREDENTIALS: {'name': 'Identity and Access Management Credentials API', 'version': 'v1', 'v2discovery': True},
  KEEP: {'name': 'Keep API', 'version': 'v1', 'v2discovery': True},
  LICENSING: {'name': 'License Manager API', 'version': 'v1', 'v2discovery': True},
  LOOKERSTUDIO: {'name': 'Looker Studio API', 'version': 'v1', 'v2discovery': True, 'localjson': True},
  MEET: {'name': 'Meet API', 'version': 'v2', 'v2discovery': True},
  MEET_BETA: {'name': 'Meet API', 'version': 'v2beta', 'v2discovery': True, 'localjson': True, 'mappedAPI': MEET},
  OAUTH2: {'name': 'OAuth2 API', 'version': 'v2', 'v2discovery': False},
  ORGPOLICY: {'name': 'Organization Policy API', 'version': 'v2', 'v2discovery': True},
  PEOPLE: {'name': 'People API', 'version': 'v1', 'v2discovery': True},
  PEOPLE_DIRECTORY: {'name': 'People Directory API', 'version': 'v1', 'v2discovery': True, 'mappedAPI': PEOPLE},
  PEOPLE_OTHERCONTACTS: {'name': 'People  API - Other Contacts', 'version': 'v1', 'v2discovery': True, 'mappedAPI': PEOPLE},
  PRINTERS: {'name': 'Directory API Printers', 'version': 'directory_v1', 'v2discovery': True, 'mappedAPI': 'admin'},
  PUBSUB: {'name': 'Pub / Sub API', 'version': 'v1', 'v2discovery': True},
  REPORTS: {'name': 'Reports API', 'version': 'reports_v1', 'v2discovery': True, 'mappedAPI': 'admin'},
  RESELLER: {'name': 'Reseller API', 'version': 'v1', 'v2discovery': True},
  SERVICEACCOUNTLOOKUP: {'name': 'Service Account Lookup pseudo-API', 'version': 'v1', 'v2discovery': True, 'localjson': True},
  SERVICEMANAGEMENT: {'name': 'Service Management API', 'version': 'v1', 'v2discovery': True},
  SERVICEUSAGE: {'name': 'Service Usage API', 'version': 'v1', 'v2discovery': True},
  SHEETS: {'name': 'Sheets API', 'version': 'v4', 'v2discovery': True},
  SHEETSTD: {'name': 'Sheets API - todrive', 'version': 'v4', 'v2discovery': True, 'mappedAPI': SHEETS},
  SITEVERIFICATION: {'name': 'Site Verification API', 'version': 'v1', 'v2discovery': True},
  STORAGE: {'name': 'Cloud Storage API', 'version': 'v1', 'v2discovery': True},
  STORAGEREAD: {'name': 'Cloud Storage API - Read', 'version': 'v1', 'v2discovery': True, 'mappedAPI': STORAGE},
  STORAGEWRITE: {'name': 'Cloud Storage API - Write', 'version': 'v1', 'v2discovery': True, 'mappedAPI': STORAGE},
  TASKS: {'name': 'Tasks API', 'version': 'v1', 'v2discovery': True},
  VAULT: {'name': 'Vault API', 'version': 'v1', 'v2discovery': True},
  YOUTUBE: {'name': 'Youtube API', 'version': 'v3', 'v2discovery': True},
  }

READONLY = ['readonly',]

_CLIENT_SCOPES = [
  {'name': 'Calendar API',
   'api': CALENDAR,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/calendar'},
  {'name': 'Chrome Browser Cloud Management API',
   'api': CBCM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.device.chromebrowsers'},
  {'name': 'Chrome Management API - read only',
   'api': CHROMEMANAGEMENT,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/chrome.management.reports.readonly'},
  {'name': 'Chrome Management API - AppDetails read only',
   'api': CHROMEMANAGEMENT_APPDETAILS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/chrome.management.appdetails.readonly'},
  {'name': 'Chrome Management API - Profiles',
   'api': CHROMEMANAGEMENT_CHROMEPROFILES,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chrome.management.profiles'},
  {'name': 'Chrome Management API - Telemetry read only',
   'api': CHROMEMANAGEMENT_TELEMETRY,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/chrome.management.telemetry.readonly'},
  {'name': 'Chrome Policy API',
   'api': CHROMEPOLICY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chrome.management.policy'},
  {'name': 'Chrome Printer Management API',
   'api': PRINTERS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.chrome.printers'},
  {'name': 'Chrome Version History API',
   'api': CHROMEVERSIONHISTORY,
   'subscopes': [],
   'scope': ''},
  {'name': 'Classroom API - Courses',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.courses'},
  {'name': 'Classroom API - Course Announcements',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.announcements'},
  {'name': 'Classroom API - Course Topics',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.topics'},
  {'name': 'Classroom API - Course Work/Materials',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.courseworkmaterials'},
  {'name': 'Classroom API - Course Work/Submissions',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.coursework.students'},
  {'name': 'Classroom API - Student Guardians',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.guardianlinks.students'},
  {'name': 'Classroom API - Profile Emails',
   'api': CLASSROOM,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/classroom.profile.emails'},
  {'name': 'Classroom API - Profile Photos',
   'api': CLASSROOM,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/classroom.profile.photos'},
  {'name': 'Classroom API - Rosters',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.rosters'},
  {'name': 'Cloud Channel API',
   'api': CLOUDCHANNEL,
   'subscopes': READONLY,
   'offByDefault': True,
   'scope': 'https://www.googleapis.com/auth/apps.order'},
  {'name': 'Cloud Identity Groups API',
   'api': CLOUDIDENTITY_GROUPS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/cloud-identity.groups'},
  {'name': 'Cloud Identity Groups API Beta (Enables group locking/unlocking)',
   'api': CLOUDIDENTITY_GROUPS_BETA,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/cloud-identity.groups'},
  {'name': 'Cloud Identity - Inbound SSO Settings',
   'api': CLOUDIDENTITY_INBOUND_SSO,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/cloud-identity.inboundsso'},
  {'name': 'Cloud Identity OrgUnits API',
   'api': CLOUDIDENTITY_ORGUNITS_BETA,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/cloud-identity.orgunits'},
  {'name': 'Cloud Identity - Policy',
   'api': CLOUDIDENTITY_POLICY,
   'subscopes': READONLY,
   'roByDefault': True,
   'scope': 'https://www.googleapis.com/auth/cloud-identity.policies'
  },
  {'name': 'Cloud Identity User Invitations API',
   'api': CLOUDIDENTITY_USERINVITATIONS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/cloud-identity.userinvitations'},
  {'name': 'Cloud Storage API (Read Only, Vault/Takeout Download, Cloud Storage)',
   'api': STORAGEREAD,
   'subscopes': [],
   'offByDefault': True,
   'scope': STORAGE_READONLY_SCOPE},
  {'name': 'Cloud Storage API (Read/Write, Vault/Takeout Copy/Download, Cloud Storage)',
   'api': STORAGEWRITE,
   'subscopes': [],
   'offByDefault': True,
   'scope': STORAGE_READWRITE_SCOPE},
  {'name': 'Contacts API - Domain Shared Contacts and GAL',
   'api': CONTACTS,
   'subscopes': [],
   'scope': 'https://www.google.com/m8/feeds'},
  {'name': 'Contact Delegation API',
   'api': CONTACTDELEGATION,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.contact.delegation'},
  {'name': 'Data Transfer API',
   'api': DATATRANSFER,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.datatransfer'},
  {'name': 'Directory API - Chrome OS Devices',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.device.chromeos'},
  {'name': 'Directory API - Customers',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.customer'},
  {'name': 'Directory API - Domains',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.domain'},
  {'name': 'Directory API - Groups',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.group'},
  {'name': 'Directory API - Mobile Devices Directory',
   'api': DIRECTORY,
   'subscopes': ['readonly', 'action'],
   'scope': 'https://www.googleapis.com/auth/admin.directory.device.mobile'},
  {'name': 'Directory API - Organizational Units',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.orgunit'},
  {'name': 'Directory API - Resource Calendars',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.resource.calendar'},
  {'name': 'Directory API - Roles',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.rolemanagement'},
  {'name': 'Directory API - User Schemas',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.userschema'},
  {'name': 'Directory API - User Security',
   'api': DIRECTORY,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/admin.directory.user.security'},
  {'name': 'Directory API - Users',
   'api': DIRECTORY,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/admin.directory.user'},
  {'name': 'Email Audit API',
   'api': EMAIL_AUDIT,
   'subscopes': [],
   'offByDefault': True,
   'scope': 'https://apps-apis.google.com/a/feeds/compliance/audit/'},
  {'name': 'Groups Migration API',
   'api': GROUPSMIGRATION,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/apps.groups.migration'},
  {'name': 'Groups Settings API',
   'api': GROUPSSETTINGS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/apps.groups.settings'},
  {'name': 'License Manager API',
   'api': LICENSING,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/apps.licensing'},
  {'name': 'People Directory API - read only',
   'api': PEOPLE_DIRECTORY,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/directory.readonly'},
  {'name': 'People API',
   'api': PEOPLE,
   'subscopes': READONLY,
   'scope': PEOPLE_SCOPE},
  {'name': 'Pub / Sub API',
   'api': PUBSUB,
   'subscopes': [],
   'offByDefault': True,
   'scope': 'https://www.googleapis.com/auth/pubsub'},
  {'name': 'Reports API - Audit Reports',
   'api': REPORTS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/admin.reports.audit.readonly'},
  {'name': 'Reports API - Usage Reports',
   'api': REPORTS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/admin.reports.usage.readonly'},
  {'name': 'Reseller API',
   'api': RESELLER,
   'subscopes': [],
   'offByDefault': True,
   'scope': 'https://www.googleapis.com/auth/apps.order'},
  {'name': 'Service Account Lookup pseudo-API',
   'api': SERVICEACCOUNTLOOKUP,
   'subscopes': [],
   'scope': ''},
  {'name': 'Site Verification API',
   'api': SITEVERIFICATION,
   'subscopes': [],
   'offByDefault': True,
   'scope': 'https://www.googleapis.com/auth/siteverification'},
  {'name': 'Vault API',
   'api': VAULT,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/ediscovery'},
  ]

_TODRIVE_CLIENT_SCOPES = [
  {'name': 'Drive API - todrive_clientaccess',
   'api': DRIVE3,
   'subscopes': [],
   'scope': DRIVE_SCOPE},
  {'name': 'Drive File API - todrive_clientaccess',
   'api': DRIVE3,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/drive.file'},
  {'name': 'Gmail API - todrive_clientaccess',
   'api': GMAIL,
   'subscopes': [],
   'scope': GMAIL_SEND_SCOPE},
  {'name': 'Sheets API - todrive_clientaccess',
   'api': SHEETS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/spreadsheets'},
  ]

OAUTH2SA_SCOPES = 'us_scopes'

_SVCACCT_SCOPES = [
  {'name': 'AlertCenter API',
   'api': ALERTCENTER,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/apps.alerts'},
  {'name': 'Analytics API - read only',
   'api': ANALYTICS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/analytics.readonly'},
  {'name': 'Analytics Admin API - read only',
   'api': ANALYTICS_ADMIN,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/analytics.readonly'},
  {'name': 'Calendar API',
   'api': CALENDAR,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/calendar'},
  {'name': 'Chat API - Memberships',
   'api': CHAT_MEMBERSHIPS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chat.memberships'},
  {'name': 'Chat API - Memberships Admin',
   'api': CHAT_MEMBERSHIPS_ADMIN,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chat.admin.memberships'},
  {'name': 'Chat API - Messages',
   'api': CHAT_MESSAGES,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chat.messages'},
  {'name': 'Chat API - Spaces',
   'api': CHAT_SPACES,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chat.spaces'},
  {'name': 'Chat API - Spaces Admin',
   'api': CHAT_SPACES_ADMIN,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/chat.admin.spaces'},
  {'name': 'Chat API - Spaces Delete',
   'api': CHAT_SPACES_DELETE,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/chat.delete'},
  {'name': 'Chat API - Spaces Delete Admin',
   'api': CHAT_SPACES_DELETE_ADMIN,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/chat.admin.delete'},
  {'name': 'Classroom API - Course Announcements',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.announcements'},
  {'name': 'Classroom API - Course Topics',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.topics'},
  {'name': 'Classroom API - Course Work/Materials',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.courseworkmaterials'},
  {'name': 'Classroom API - Course Work/Submissions',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.coursework.students'},
  {'name': 'Classroom API - Profile Emails',
   'api': CLASSROOM,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/classroom.profile.emails'},
  {'name': 'Classroom API - Profile Photos',
   'api': CLASSROOM,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/classroom.profile.photos'},
  {'name': 'Classroom API - Rosters',
   'api': CLASSROOM,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/classroom.rosters'},
  {'name': 'Cloud Identity Devices API',
   'api': CLOUDIDENTITY_DEVICES,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/cloud-identity'},
#  {'name': 'Cloud Identity User Invitations API',
#   'api': CLOUDIDENTITY_USERINVITATIONS,
#   'subscopes': READONLY,
#   'scope': 'https://www.googleapis.com/auth/cloud-identity'},
#  {'name': 'Contacts API - Users',
#   'api': CONTACTS,
#   'subscopes': [],
#   'scope': 'https://www.google.com/m8/feeds'},
  {'name': 'Drive API',
   'api': DRIVE3,
   'subscopes': READONLY,
   'scope': DRIVE_SCOPE},
  {'name': 'Drive Activity API v2 - must pair with Drive API',
   'api': DRIVEACTIVITY,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/drive.activity'},
  {'name': 'Drive Labels API - Admin',
   'api': DRIVELABELS_ADMIN,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/drive.admin.labels'},
  {'name': 'Drive Labels API - User',
   'api': DRIVELABELS_USER,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/drive.labels'},
  {'name': 'Docs API',
   'api': DOCS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/documents'},
  {'name': 'Forms API',
   'api': FORMS,
   'subscopes': [],
   'scope': DRIVE_SCOPE},
  {'name': 'Gmail API - Full Access (Labels, Messages)',
   'api': GMAIL,
   'subscopes': [],
   'scope': 'https://mail.google.com/'},
  {'name': 'Gmail API - Full Access (Labels, Messages) except delete message',
   'api': GMAIL,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/gmail.modify'},
  {'name': 'Gmail API - Basic Settings (Filters,IMAP, Language, POP, Vacation) - read/write, Sharing Settings (Delegates, Forwarding, SendAs) - read',
   'api': GMAIL,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/gmail.settings.basic'},
  {'name': 'Gmail API - Sharing Settings (Delegates, Forwarding, SendAs) - write',
   'api': GMAIL,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/gmail.settings.sharing'},
  {'name': 'Identity and Access Management API',
   'api': IAM,
   'subscopes': [],
   'scope': CLOUD_PLATFORM_SCOPE},
  {'name': 'Keep API',
   'api': KEEP,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/keep'},
  {'name': 'Looker Studio API',
   'api': LOOKERSTUDIO,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/datastudio'},
  {'name': 'Meet API',
   'api': MEET,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/meetings.space.created',
   'roscope': 'https://www.googleapis.com/auth/meetings.space.readonly'},
  {'name': 'OAuth2 API',
   'api': OAUTH2,
   'subscopes': [],
   'scope': USERINFO_PROFILE_SCOPE},
  {'name': 'People API',
   'api': PEOPLE,
   'subscopes': READONLY,
   'scope': PEOPLE_SCOPE},
  {'name': 'People Directory API - read only',
   'api': PEOPLE_DIRECTORY,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/directory.readonly'},
  {'name': 'People API - Other Contacts - read only',
   'api': PEOPLE_OTHERCONTACTS,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/contacts.other.readonly'},
  {'name': 'Sheets API',
   'api': SHEETS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/spreadsheets'},
  {'name': 'Tasks API',
   'api': TASKS,
   'subscopes': READONLY,
   'scope': 'https://www.googleapis.com/auth/tasks'},
  {'name': 'Youtube API - read only',
   'api': YOUTUBE,
   'subscopes': [],
   'offByDefault': True,
   'scope': 'https://www.googleapis.com/auth/youtube.readonly'},
  ]

_SVCACCT_SPECIAL_SCOPES = [
  {'name': 'Drive API - todrive',
   'api': DRIVETD,
   'subscopes': [],
   'scope': DRIVE_SCOPE},
  {'name': 'Gmail API - Full Access - read only',
   'api': GMAIL,
   'subscopes': [],
   'offByDefault': True,
   'scope': 'https://www.googleapis.com/auth/gmail.readonly'},
  {'name': 'Gmail API - Send Messages - including todrive',
   'api': GMAIL,
   'subscopes': [],
   'offByDefault': True,
   'scope': GMAIL_SEND_SCOPE},
  {'name': 'Sheets API - todrive',
   'api': SHEETSTD,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/spreadsheets'},
  ]

_USER_SVCACCT_ONLY_SCOPES = [
  {'name': 'Groups Migration API',
   'api': GROUPSMIGRATION,
   'subscopes': [],
   'scope': 'https://www.googleapis.com/auth/apps.groups.migration'},
  ]

DRIVE3_TO_DRIVE2_ABOUT_FIELDS_MAP = {
  'displayName': 'name',
  'limit': 'quotaBytesTotal',
  'usage': 'quotaBytesUsedAggregate',
  'usageInDrive': 'quotaBytesUsed',
  'usageInDriveTrash': 'quotaBytesUsedInTrash',
  }

DRIVE3_TO_DRIVE2_CAPABILITIES_FIELDS_MAP = {
  'canComment': 'canComment',
  'canReadRevisions': 'canReadRevisions',
  'canCopy': 'copyable',
  'canEdit': 'editable',
  'canShare': 'shareable',
  }

DRIVE3_TO_DRIVE2_CAPABILITIES_NAMES_MAP = {
  'canChangeViewersCanCopyContent': 'canChangeRestrictedDownload',
  }

DRIVE3_TO_DRIVE2_FILES_FIELDS_MAP = {
  'allowFileDiscovery': 'withLink',
  'createdTime': 'createdDate',
  'expirationTime': 'expirationDate',
  'modifiedByMe': 'modified',
  'modifiedByMeTime': 'modifiedByMeDate',
  'modifiedTime': 'modifiedDate',
  'name': 'title',
  'restrictionTime': 'restrictionDate',
  'sharedWithMeTime': 'sharedWithMeDate',
  'size': 'fileSize',
  'trashedTime': 'trashedDate',
  'viewedByMe': 'viewed',
  'viewedByMeTime': 'lastViewedByMeDate',
  'webViewLink': 'alternateLink',
  }

DRIVE3_TO_DRIVE2_LABELS_MAP = {
  'modifiedByMe': 'modified',
  'starred': 'starred',
  'trashed': 'trashed',
  'viewedByMe': 'viewed',
  }

DRIVE3_TO_DRIVE2_REVISIONS_FIELDS_MAP = {
  'modifiedTime': 'modifiedDate',
  'keepForever': 'pinned',
  'size': 'fileSize',
  }

def getAPIName(api):
  return _INFO[api]['name']

def getVersion(api):
  version = _INFO[api]['version']
  v2discovery = _INFO[api]['v2discovery']
  api = _INFO[api].get('mappedAPI', api)
  return (api, version, v2discovery)

def getClientScopesSet(api):
  return {scope['scope'] for scope in _CLIENT_SCOPES if scope['api'] == api}

def getClientScopesList(todriveClientAccess):
  caScopes = _CLIENT_SCOPES[:]
  if todriveClientAccess:
    caScopes.extend(_TODRIVE_CLIENT_SCOPES)
  return sorted(caScopes, key=lambda k: k['name'])

def getClientScopesURLs(todriveClientAccess):
  caScopes = _CLIENT_SCOPES[:]
  if todriveClientAccess:
    caScopes.extend(_TODRIVE_CLIENT_SCOPES)
  return sorted({scope['scope'] for scope in _CLIENT_SCOPES})

def getSvcAcctScopeAPI(uscope):
  for scope in _SVCACCT_SCOPES:
    if uscope == scope['scope'] or (uscope.endswith('.readonly') and 'readonly' in scope['subscopes']):
      return scope['api']
  return None

def getSvcAcctScopes(userServiceAccountAccessOnly, svcAcctSpecialScopes):
  saScopes = [scope['scope'] for scope in _SVCACCT_SCOPES]
  if userServiceAccountAccessOnly:
    saScopes.extend([scope['scope'] for scope in _USER_SVCACCT_ONLY_SCOPES])
  if svcAcctSpecialScopes:
    saScopes.extend([scope['scope'] for scope in _SVCACCT_SPECIAL_SCOPES])
  return saScopes

def getSvcAcctScopesList(userServiceAccountAccessOnly, svcAcctSpecialScopes):
  saScopes = _SVCACCT_SCOPES[:]
  if userServiceAccountAccessOnly:
    saScopes.extend(_USER_SVCACCT_ONLY_SCOPES)
  if svcAcctSpecialScopes:
    saScopes.extend(_SVCACCT_SPECIAL_SCOPES)
  return sorted(saScopes, key=lambda k: k['name'])

def hasLocalJSON(api):
  return _INFO[api].get('localjson', False)
