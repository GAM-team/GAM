#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# GAM7
#
# Copyright 2026, All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
GAM is a command line tool which allows Administrators to control their Google Workspace domain and accounts.

For more information, see:
https://github.com/GAM-team/GAM
https://github.com/GAM-team/GAM/wiki
"""

__author__ = 'GAM Team <google-apps-manager@googlegroups.com>'
__version__ = '7.46.03'
__license__ = 'Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)'

# pylint: disable=wrong-import-position
import base64
import codecs
import collections
import configparser
import csv
from email.charset import add_charset, QP
from email.generator import Generator
from email.header import decode_header, Header
from email import message_from_string
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email.policy import SMTP as policySMTP
import hashlib
from html.entities import name2codepoint
from html.parser import HTMLParser
import http.client
import importlib
from importlib.metadata import version as lib_version
import io
import ipaddress
import json
import logging
from logging.handlers import RotatingFileHandler
import mimetypes
import multiprocessing
import os
import platform
import queue
import random
import re
from secrets import SystemRandom
import shlex
import signal
import smtplib
import socket
import sqlite3
import ssl
import string
import struct
import subprocess
import sys
from tempfile import TemporaryFile
try:
  import termios
except ImportError:
  # termios does not exist for Windows
  pass
import threading
import time
from traceback import print_exc
import types
from urllib.parse import quote, quote_plus, unquote, urlencode, urlparse, parse_qs
import uuid
import warnings
import webbrowser
import wsgiref.simple_server
import wsgiref.util
import zipfile

# disable legacy stuff we don't use and isn't secure
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = "1"
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# 10/2024 - I don't recall why we did this but PyInstaller
# 6.10.0+ does not like it. Only run this when we're not
# Frozen.
if not getattr(sys, 'frozen', False):
  sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import arrow

from pathvalidate import sanitize_filename, sanitize_filepath

import google.oauth2.credentials
import google.oauth2.id_token
import google.auth
import google.auth.transport.requests
from google.auth.compute_engine import _metadata as gce_metadata
from google.auth.jwt import Credentials as JWTCredentials
import google.oauth2.service_account
import google_auth_oauthlib.flow
import google_auth_httplib2
import googleapiclient
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
import httplib2

httplib2.RETRIES = 5

from passlib.hash import sha512_crypt
from filelock import FileLock

if platform.system() == 'Linux':
  import distro

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glgdata as GDATA
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gamlib import glskus as SKU
from gamlib import gluprop as UProp
from gamlib import glverlibs

import gdata.apps.service
import gdata.apps.audit
import gdata.apps.audit.service
import gdata.apps.contacts
import gdata.apps.contacts.service

from gam.util.html import _DeHTMLParser, dehtml  # noqa: F401  # re-export
from gam.util.access import (  # noqa: F401  # re-export
    accessErrorMessage, accessErrorExit, accessErrorExitNonDirectory,
    ClientAPIAccessDeniedExit, SvcAcctAPIAccessDenied, SvcAcctAPIAccessDeniedExit,
    SvcAcctAPIDisabledExit, APIAccessDeniedExit,
    checkEntityDNEorAccessErrorExit, checkEntityAFDNEorAccessErrorExit,
    checkEntityItemValueAFDNEorAccessErrorExit,
    entityUnknownWarning, entityOrEntityUnknownWarning, duplicateAliasGroupUserWarning,
)
from gam.util.email import (  # noqa: F401  # re-export
    _addAttachmentsToMessage, _addEmbeddedImagesToMessage, send_email,
)
from gam.cmd.oauth import (  # noqa: F401  # re-export
    VALIDEMAIL_PATTERN, _getValidateLoginHint, getOAuthClientIDAndSecret,
    getScopesFromUser, _localhost_to_ip, _waitForHttpClient, _waitForUserInput,
    _GamOauthFlow, Credentials, doOAuthRequest, doOAuthCreate, exitIfNoOauth2Txt,
    doOAuthDelete, doOAuthInfo, doOAuthUpdate, doOAuthRefresh, doOAuthExport,
)
from gam.cmd.project import (  # noqa: F401  # re-export
    getCRMService, enableGAMProjectAPIs, doEnableAPIs,
    _waitForSvcAcctCompletion, _grantRotateRights,
    _createOauth2serviceJSON, _createClientSecretsOauth2service,
    _getProjects, _checkProjectFound, convertGCPFolderNameToID,
    PROJECTID_PATTERN, PROJECTID_FORMAT_REQUIRED, _checkProjectId,
    PROJECTNAME_PATTERN, PROJECTNAME_FORMAT_REQUIRED, _checkProjectName,
    _getSvcAcctInfo, _getAppInfo, _generateProjectSvcAcctId,
    _getLoginHintProjectInfo, _getCurrentProjectId,
    GAM_PROJECT_FILTER, PROJECTID_FILTER_REQUIRED,
    PROJECTS_CREATESVCACCT_OPTIONS, PROJECTS_DELETESVCACCT_OPTIONS,
    PROJECTS_PRINTSHOW_OPTIONS,
    _getLoginHintProjects, _checkForExistingProjectFiles,
    getCRMOrgId, doInfoCustomerId, doInfoGCPOrgId, getGCPOrgId,
    doCreateGCPFolder, doCreateProject, doUseProject, doUpdateProject,
    doDeleteProject,
    PROJECT_TIMEOBJECTS, PROJECT_STATE_CHOICE_MAP, doPrintShowProjects,
    doInfoCurrentProjectId, doCreateSvcAcct, doDeleteSvcAcct,
    _getSvcAcctKeyProjectClientFields, checkServiceAccount, doCheckUpdateSvcAcct,
    _getSAKeys, SVCACCT_KEY_TIME_OBJECTS, _showSAKeys,
    SVCACCT_DISPLAY_FIELDS, SVCACCT_KEY_TYPE_CHOICE_MAP, doPrintShowSvcAccts,
    _generatePrivateKeyAndPublicCert, _formatOAuth2ServiceData,
    doProcessSvcAcctKeys, doCreateSvcAcctKeys, doUpdateSvcAcctKeys,
    doReplaceSvcAcctKeys, doUploadSvcAcctKeys, doDeleteSvcAcctKeys,
    doShowSvcAcctKeys, doCreateGCPServiceAccount,
)
from gam.cmd.audit import (  # noqa: F401  # re-export
    _showMailboxMonitorRequestStatus,
    doCreateMonitor, doDeleteMonitor, doShowMonitors, getAuditParameters,
)
from gam.cmd.reports import (  # noqa: F401  # re-export
    CUSTOMER_REPORT_SERVICES, CUSTOMER_USER_CHOICES,
    DISABLED_REASON_TIME_PATTERN, NL_SPACES_PATTERN,
    REPORTS_PARAMETERS_SIMPLE_TYPES,
    REPORT_ACTIVITIES_FILTER_MAP, REPORT_ACTIVITIES_TIME_OBJECTS,
    REPORT_ACTIVITIES_UPPERCASE_EVENTS, REPORT_ALIASES_CHOICE_MAP,
    REPORT_CHOICE_MAP, USER_REPORT_SERVICES,
    _adjustTryDate, _checkDataRequiredServices,
    convertReportMBtoGB, doReport, doReportUsage,
    doReportUsageParameters, doWhatIs, getUserOrgUnits,
)
from gam.cmd.send_email import (  # noqa: F401  # re-export
    ADDRESS_FIELDS_PRINT_ORDER, CASE_MARKERS, LC_PATTERN, PC_PATTERN,
    RTL_PATTERN, RT_MARKERS, RT_PATTERN, SKIP_PATTERNS, UC_PATTERN,
    TAG_ADDRESS_ARGUMENT_TO_FIELD_MAP, TAG_EMAIL_ARGUMENT_TO_FIELD_MAP,
    TAG_EXTERNALID_ARGUMENT_TO_FIELD_MAP, TAG_FIELD_SUBFIELD_CHOICE_MAP,
    TAG_GENDER_ARGUMENT_TO_FIELD_MAP, TAG_IM_ARGUMENT_TO_FIELD_MAP,
    TAG_KEYWORD_ARGUMENT_TO_FIELD_MAP, TAG_LOCATION_ARGUMENT_TO_FIELD_MAP,
    TAG_NAME_ARGUMENT_TO_FIELD_MAP, TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP,
    TAG_OTHEREMAIL_ARGUMENT_TO_FIELD_MAP, TAG_PHONE_ARGUMENT_TO_FIELD_MAP,
    TAG_POSIXACCOUNT_ARGUMENT_TO_FIELD_MAP, TAG_RELATION_ARGUMENT_TO_FIELD_MAP,
    TAG_REPLACE_PATTERN, TAG_SSHPUBLICKEY_ARGUMENT_TO_FIELD_MAP,
    TAG_WEBSITE_ARGUMENT_TO_FIELD_MAP,
    _getTagReplacement, _getTagReplacementFieldValues, _initTagReplacements,
    _processTagReplacements, _substituteForUser,
    doSendEmail, doSendReply, getRecipients, sendCreateUpdateUserNotification,
)
from gam.cmd.reseller import (  # noqa: F401  # re-export
    ADDRESS_FIELDS_ARGUMENT_MAP, ANALYTIC_ENTITY_MAP, CHANNEL_ENTITY_MAP,
    DELETION_TYPE_MAP, PLAN_NAME_MAP, PRINT_RESOLD_SUBSCRIPTIONS_TITLES,
    RENEWAL_TYPE_MAP, SUBSCRIPTION_SKIP_OBJECTS, SUBSCRIPTION_TIME_OBJECTS,
    _getResoldCustomerAttr, _getResoldSubscriptionAttr,
    _showCustomerAddressPhoneNumber, _showSubscription,
    doCreateResoldCustomer, doCreateResoldSubscription,
    doDeleteResoldSubscription, doInfoResoldCustomer, doInfoResoldSubscription,
    doPrintShowChannelCustomerEntitlements, doPrintShowChannelCustomers,
    doPrintShowChannelItems, doPrintShowChannelOffers,
    doPrintShowChannelProducts, doPrintShowChannelSKUs,
    doPrintShowResoldSubscriptions, doUpdateResoldCustomer,
    doUpdateResoldSubscription, getCustomerSubscription,
    normalizeChannelCustomerID, normalizeChannelProductID, normalizeChannelResellerID,
)
from gam.cmd.analytics import (  # noqa: F401  # re-export
    printShowAnalyticAccountSummaries, printShowAnalyticAccounts,
    printShowAnalyticDatastreams, printShowAnalyticItems, printShowAnalyticProperties,
)
from gam.cmd.domains import (  # noqa: F401  # re-export
    CUSTOMER_LICENSE_MAP, DOMAIN_ALIAS_PRINT_ORDER, DOMAIN_ALIAS_SKIP_OBJECTS,
    DOMAIN_ALIAS_SORT_TITLES, DOMAIN_TIME_OBJECTS,
    _printDomain, _showDomainAlias,
    doCreateDomain, doCreateDomainAlias, doDeleteDomain, doDeleteDomainAlias,
    doInfoDomainAlias, doPrintShowDomainAliases, doUpdateDomain,
)
from gam.cmd.customer import (  # noqa: F401  # re-export
    DOMAIN_PRINT_ORDER, DOMAIN_SKIP_OBJECTS, DOMAIN_SORT_TITLES,
    PRINT_PRIVILEGES_FIELDS,
    _getCustomerId, _getCustomerIdNoC, _getCustomersCustomerIdNoC,
    _getCustomersCustomerIdWithC, _getDomainList, _showCustomerLicenseInfo,
    _showDomain, doInfoCustomer, doInfoDomain, doInfoInstance,
    doPrintShowDomains, doUpdateCustomer, setTrueCustomerId,
)
from gam.cmd.admin import (  # noqa: F401  # re-export
    ADMIN_ASSIGNEE_TYPE_TO_ASSIGNEDTO_FIELD_MAP, ADMIN_CONDITION_CHOICE_MAP,
    ADMIN_SCOPE_TYPE_CHOICE_MAP, ALL_ASSIGNEE_TYPES,
    NONSECURITY_GROUP_CONDITION, PRINT_ADMIN_FIELDS,
    PRINT_ADMIN_ROLES_FIELDS, PRINT_ADMIN_TITLES, SECURITY_GROUP_CONDITION,
    _listPrivileges, _showAdminRole,
    doCreateAdmin, doCreateUpdateAdminRoles, doDeleteAdmin, doDeleteAdminRole,
    doInfoPrintShowAdminRoles, doPrintShowAdmins, doPrintShowPrivileges,
    getRoleId, makeRoleIdNameMap, role_from_roleid, roleid_from_role,
)
from gam.cmd.datatransfer import (  # noqa: F401  # re-export
    DATA_TRANSFER_SORT_TITLES, DATA_TRANSFER_STATUS_MAP,
    DRIVE_AND_DOCS_APP_NAME, GOOGLE_LOOKER_STUDIO_APP_NAME,
    PRIVACY_LEVEL_CHOICE_MAP, SERVICE_NAME_CHOICE_MAP,
    _convertTransferAppIDtoName, _showTransfer, _validateTransferAppName,
    doCreateDataTransfer, doInfoDataTransfer, doPrintShowDataTransfers,
    doShowTransferApps, getTransferApplications,
)
from gam.cmd.orgunits import (  # noqa: F401  # re-export
    ALIAS_TARGET_TYPES, ORG_ARGUMENT_TO_FIELD_MAP, ORG_FIELDS_WITH_CRS_NLS,
    ORG_FIELD_INFO_ORDER, ORG_FIELD_PRINT_ORDER, ORG_ITEMS_FIELD_MAP,
    ORG_UNIT_SELECTOR_FIELD, PRINT_ORGS_DEFAULT_FIELDS,
    PRINT_OUS_SELECTOR_CHOICES,
    _batchMoveCrOSesToOrgUnit, _batchMoveUsersToOrgUnit,
    _doDeleteOrgs, _doInfoOrgs, _doUpdateOrgs, _getOrgUnits,
    checkOrgUnitPathExists, doCheckOrgUnit, doCreateOrg,
    doDeleteOrg, doDeleteOrgs, doInfoOrg, doInfoOrgs,
    doPrintOrgs, doShowOrgTree, doUpdateOrg, doUpdateOrgs,
    getOrgUnitIdToPathMap,
)
from gam.cmd.aliases import (  # noqa: F401  # re-export
    _addUserAliases, deleteUsersAliases, doCreateUpdateAliases,
    doDeleteAliases, doInfoAliases, doPrintAddresses, doPrintAliases,
    doRemoveAliases, getUserGroupDomainQueryFilters, infoAliases,
    initUserGroupDomainQueryFilters, makeUserGroupDomainQueryFilters,
    userFilters,
)
from gam.cmd.contacts import (  # noqa: F401  # re-export
    CONTACTS_ORDERBY_CHOICE_MAP, CONTACTS_PROJECTION_CHOICE_MAP,
    CONTACT_ADDITIONAL_NAME, CONTACT_ADDRESSES, CONTACT_BILLING_INFORMATION,
    CONTACT_BIRTHDAY, CONTACT_CALENDARS, CONTACT_DIRECTORY_SERVER,
    CONTACT_EMAILS, CONTACT_EVENTS, CONTACT_EXTERNALIDS, CONTACT_FAMILY_NAME,
    CONTACT_FIELDS_WITH_CRS_NLS, CONTACT_GENDER, CONTACT_GIVEN_NAME,
    CONTACT_HOBBIES, CONTACT_ID, CONTACT_IMS, CONTACT_INITIALS,
    CONTACT_JOTS, CONTACT_JSON, CONTACT_LANGUAGE, CONTACT_LOCATION,
    CONTACT_MAIDENNAME, CONTACT_MILEAGE, CONTACT_NAME, CONTACT_NAME_PREFIX,
    CONTACT_NAME_SUFFIX, CONTACT_NICKNAME, CONTACT_NOTES, CONTACT_OCCUPATION,
    CONTACT_ORGANIZATIONS, CONTACT_PHONES, CONTACT_PRIORITY,
    CONTACT_RELATIONS, CONTACT_SELECT_ARGUMENTS, CONTACT_SENSITIVITY,
    CONTACT_SHORTNAME, CONTACT_SUBJECT, CONTACT_TIME_OBJECTS,
    CONTACT_UPDATED, CONTACT_USER_DEFINED_FIELDS, CONTACT_WEBSITES,
    ContactsManager,
    PEOPLE_ADDRESSES, PEOPLE_ADD_GROUPS, PEOPLE_ADD_GROUPS_LIST,
    PEOPLE_BIOGRAPHIES, PEOPLE_BIRTHDAYS, PEOPLE_CALENDAR_URLS,
    PEOPLE_CLIENT_DATA, PEOPLE_COVER_PHOTOS,
    PEOPLE_DIRECTORY_MERGE_SOURCES_CHOICE_MAP,
    PEOPLE_DIRECTORY_SOURCES_CHOICE_MAP,
    PEOPLE_EMAIL_ADDRESSES, PEOPLE_EVENTS, PEOPLE_EXTERNAL_IDS,
    PEOPLE_FILE_ASES, PEOPLE_GENDERS, PEOPLE_GROUPS, PEOPLE_GROUPS_LIST,
    PEOPLE_GROUP_CLIENT_DATA, PEOPLE_GROUP_NAME, PEOPLE_IM_CLIENTS,
    PEOPLE_INTERESTS, PEOPLE_JSON, PEOPLE_LOCALES, PEOPLE_LOCATIONS,
    PEOPLE_MEMBERSHIPS, PEOPLE_METADATA, PEOPLE_MISC_KEYWORDS,
    PEOPLE_MISC_KEYWORDS_BILLING_INFORMATION,
    PEOPLE_MISC_KEYWORDS_DIRECTORY_SERVER, PEOPLE_MISC_KEYWORDS_JOT,
    PEOPLE_MISC_KEYWORDS_MILEAGE, PEOPLE_MISC_KEYWORDS_PRIORITY,
    PEOPLE_MISC_KEYWORDS_SENSITIVITY, PEOPLE_MISC_KEYWORDS_SUBJECT,
    PEOPLE_NAMES, PEOPLE_NAMES_FAMILY_NAME, PEOPLE_NAMES_GIVEN_NAME,
    PEOPLE_NAMES_HONORIFIC_PREFIX, PEOPLE_NAMES_HONORIFIC_SUFFIX,
    PEOPLE_NAMES_MIDDLE_NAME, PEOPLE_NAMES_PHONETIC_FAMILY_NAME,
    PEOPLE_NAMES_PHONETIC_GIVEN_NAME, PEOPLE_NAMES_PHONETIC_HONORIFIC_PREFIX,
    PEOPLE_NAMES_PHONETIC_HONORIFIC_SUFFIX,
    PEOPLE_NAMES_PHONETIC_MIDDLE_NAME, PEOPLE_NAMES_UNSTRUCTURED_NAME,
    PEOPLE_NICKNAMES, PEOPLE_NICKNAMES_INITIALS,
    PEOPLE_NICKNAMES_MAIDENNAME, PEOPLE_NICKNAMES_NICKNAME,
    PEOPLE_NICKNAMES_SHORTNAME, PEOPLE_OCCUPATIONS, PEOPLE_ORGANIZATIONS,
    PEOPLE_PHONE_NUMBERS, PEOPLE_PHOTOS, PEOPLE_READ_SOURCES_CHOICE_MAP,
    PEOPLE_RELATIONS, PEOPLE_REMOVE_GROUPS, PEOPLE_REMOVE_GROUPS_LIST,
    PEOPLE_SIP_ADDRESSES, PEOPLE_SKILLS, PEOPLE_UPDATE_TIME,
    PEOPLE_URLS, PEOPLE_USER_DEFINED, PeopleManager,
    _clearUpdateContacts, _getContactEntityList, _getContactFieldsList,
    _getContactQueryAttributes, _getCreateContactReturnOptions,
    _initContactQueryAttributes, _showContact,
    clearEmailAddressMatches, countLocalContactSelects,
    dedupEmailAddressMatches, doClearDomainContacts,
    doCreateDomainContact, doDedupDomainContacts, doDeleteDomainContacts,
    doInfoDomainContacts, doPrintShowDomainContacts, doUpdateDomainContacts,
    localContactSelects, normalizeContactGroupResourceName,
    normalizeContactId, normalizeOtherContactsResourceName,
    normalizePeopleResourceName, queryContacts,
)
from gam.cmd.people import (  # noqa: F401  # re-export
    CONTACTGROUPS_MYCONTACTS_ID,
    CONTACTGROUPS_MYCONTACTS_NAME,
    PEOPLE_CONTACTGROUPS_DEFAULT_FIELDS,
    PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP,
    PEOPLE_CONTACTS_DEFAULT_FIELDS,
    PEOPLE_CONTACT_DEPRECATED_SELECT_ARGUMENTS,
    PEOPLE_CONTACT_OBJECT_KEYS,
    PEOPLE_CONTACT_SELECT_ARGUMENTS,
    PEOPLE_FIELDS_CHOICE_MAP,
    PEOPLE_GROUP_TIME_OBJECTS,
    PEOPLE_ORDERBY_CHOICE_MAP,
    PEOPLE_OTHERCONTACT_SELECT_ARGUMENTS,
    PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP,
    PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP,
    _clearUpdatePeopleContacts,
    _getPeopleContactEntityList,
    _getPeopleContactQueryAttributes,
    _getPeopleOtherContactEntityList,
    _getPeopleOtherContactQueryAttributes,
    _getPeopleOtherContacts,
    _getPersonFields,
    _infoPeople,
    _initPeopleContactQueryAttributes,
    _initPeopleOtherContactQueryAttributes,
    _initPersonMetadataParameters,
    _normalizeContactGroupMetadata,
    _printContactGroup,
    _printPerson,
    _printPersonEntityList,
    _printShowPeople,
    _processPeopleContactPhotos,
    _processPersonMetadata,
    _showContactGroup,
    _showPerson,
    addContactGroupNamesToContacts,
    clearPeopleEmailAddressMatches,
    clearUserPeopleContacts,
    copyUserPeopleOtherContacts,
    countLocalPeopleContactSelects,
    createUserPeopleContact,
    createUserPeopleContactGroup,
    dedupPeopleEmailAddressMatches,
    dedupReplaceDomainUserPeopleContacts,
    deleteUserPeopleContactGroups,
    deleteUserPeopleContactPhoto,
    deleteUserPeopleContacts,
    doDeleteDomainContactPhoto,
    doGetDomainContactPhoto,
    doInfoDomainPeopleContacts,
    doInfoDomainPeopleProfile,
    doPrintShowDomainPeopleContacts,
    doPrintShowDomainPeopleProfiles,
    doUpdateDomainContactPhoto,
    getPeopleContactGroupsInfo,
    getPersonFieldsList,
    getUserPeopleContactPhoto,
    infoUserPeopleContactGroups,
    infoUserPeopleContacts,
    localPeopleContactSelects,
    printShowUserPeopleContactGroups,
    printShowUserPeopleContacts,
    printShowUserPeopleOtherContacts,
    printShowUserPeopleProfiles,
    processUserPeopleOtherContacts,
    queryPeopleContacts,
    queryPeopleOtherContacts,
    replaceDomainPeopleEmailAddressMatches,
    updateUserPeopleContactGroup,
    updateUserPeopleContactPhoto,
    updateUserPeopleContacts,
    validatePeopleContactGroup,
    validatePeopleContactGroupsList,
)
from gam.cmd.delegates import (  # noqa: F401  # re-export
    _getDelegateName,
    _validateUserGetDelegateList,
    printShowContactDelegates,
    processContactDelegates,
)
from gam.cmd.cros import (  # noqa: F401  # re-export
    CROS_ACTION_CHOICE_MAP,
    CROS_ACTION_NAME_MAP,
    CROS_ACTIVITY_LIST_FIELDS_CHOICE_MAP,
    CROS_ACTIVITY_TIME_OBJECTS,
    CROS_BASIC_FIELDS_LIST,
    CROS_COMMAND_CHOICE_MAP,
    CROS_COMMAND_FINAL_STATES,
    CROS_COMMAND_TIME_OBJECTS,
    CROS_DOIT_REQUIRED_COMMANDS,
    CROS_END_ARGUMENTS,
    CROS_ENTITIES_MAP,
    CROS_FIELDS_CHOICE_MAP,
    CROS_FIELDS_WITH_CRS_NLS,
    CROS_INDEXED_TITLES,
    CROS_KIOSK_COMMANDS,
    CROS_LIST_FIELDS_CHOICE_MAP,
    CROS_ORDERBY_CHOICE_MAP,
    CROS_SCALAR_PROPERTY_PRINT_ORDER,
    CROS_START_ARGUMENTS,
    CROS_TELEMETRY_FIELDS_CHOICE_MAP,
    CROS_TELEMETRY_LIST_FIELDS,
    CROS_TELEMETRY_LIST_FIELDS_CHOICE_MAP,
    CROS_TELEMETRY_SCALAR_FIELDS,
    CROS_TELEMETRY_SCALAR_FIELDS_SET,
    CROS_TELEMETRY_TIME_OBJECTS,
    CROS_TIME_OBJECTS,
    CROS_TPM_FIXED_VERSIONS,
    CROS_TPM_VULN_VERSIONS,
    UPDATE_CROS_ARGUMENT_TO_PROPERTY_MAP,
    _computeDVRstorageFreePercentage,
    _filterActiveTimeRanges,
    _filterBasicList,
    _filterCPUStatusReports,
    _filterDeviceFiles,
    _filterRecentUsers,
    _filterScreenshotFiles,
    _filterSystemRamFreeReports,
    _getFilterDateTime,
    _selectDeviceFiles,
    checkTPMVulnerability,
    displayCrOSCommandResult,
    doGetCommandResultCrOSDevices,
    doGetCrOSDeviceFiles,
    doInfoCrOSDevices,
    doInfoPrintShowCrOSTelemetry,
    doIssueCommandCrOSDevices,
    doPrintCrOSActivity,
    doPrintCrOSDevices,
    doPrintCrOSEntity,
    doUpdateCrOSDevices,
    getCfgCrOSEntities,
    getCommandResultCrOSDevices,
    getCrOSDeviceEntity,
    getCrOSDeviceFiles,
    getDeviceFilesEntity,
    infoCrOSDevices,
    issueCommandCrOSDevices,
    substituteQueryTimes,
    updateCrOSDevices,
    writeCrOSCommandResults,
)

from gam.cmd.browsers import (  # noqa: F401  # re-export
    BROWSER_ANNOTATED_FIELDS_LIST, BROWSER_DEVICEID_ANNOTATED_FIELDS,
    BROWSER_FIELDS_CHOICE_MAP, BROWSER_FULL_ACCESS_FIELDS,
    BROWSER_ORDERBY_CHOICE_MAP, BROWSER_TIME_OBJECTS,
    BROWSER_TOKEN_FIELDS_CHOICE_MAP, BROWSER_TOKEN_TIME_OBJECTS,
    CHROMEPROFILECOMMAND_TIME_OBJECTS, CHROMEPROFILE_FIELDS_CHOICE_MAP,
    CHROMEPROFILE_ORDERBY_CHOICE_MAP, CHROMEPROFILE_TIME_OBJECTS,
    UPDATE_BROWSER_ARGUMENT_TO_PROPERTY_MAP,
    _getChromeProfileName, _getChromeProfileNameEntityForCommand,
    _getChromeProfileNameList, _getChromeProfileNameParameters,
    _initChromeProfileNameParameters, _printChromeProfileCommand,
    _showBrowser, _showBrowserToken, _showChromeProfile,
    _showChromeProfileCommand, doCreateBrowserToken,
    doCreateChromeProfileCommand, doDeleteBrowsers, doDeleteChromeProfile,
    doInfoBrowsers, doInfoChromeProfile, doInfoChromeProfileCommand,
    doMoveBrowsers, doPrintShowBrowserTokens, doPrintShowBrowsers,
    doPrintShowChromeProfileCommands, doPrintShowChromeProfiles,
    doRevokeBrowserToken, doUpdateBrowsers,
)
from gam.cmd.chat import (  # noqa: F401  # re-export
CHAT_EMOJI_SHOW_CREATED_BY_CHOICE_MAP, CHAT_MEMBERS_FIELDS_CHOICE_MAP,
    CHAT_MEMBER_ROLE_MAP, CHAT_MEMBER_TYPE_MAP,
    CHAT_MESSAGES_FIELDS_CHOICE_MAP, CHAT_MESSAGES_ORDERBY_CHOICE_MAP,
    CHAT_MESSAGE_REPLY_OPTION_MAP, CHAT_ROLE_ENTITY_TYPE_MAP,
    CHAT_SEARCHMESSAGES_ORDERBY_CHOICE_MAP,
    CHAT_SEARCHMESSAGES_VIEW_CHOICE_MAP, CHAT_SECTION_POSITION,
    CHAT_SPACES_ADMIN_ORDERBY_CHOICE_MAP, CHAT_SPACES_FIELDS_CHOICE_MAP,
    CHAT_SPACE_MIN_MAX_MEMBERS, CHAT_SPACE_PREDEFINED_PERMS_MAP,
    CHAT_SPACE_ROLE_PERMISSIONS_MAP, CHAT_SPACE_TYPE_MAP,
    CHAT_SYNC_PREVIEW_TITLES, CHAT_TIME_OBJECTS,
    CHAT_UPDATE_SPACE_PERMISSIONS_MAP, CHAT_UPDATE_SPACE_TYPE_MAP,
    _chkChatAdminAccess, _cleanChatMessage, _cleanChatSpace,
    _deleteChatMembers, _getChatAdminAccess, _getChatMemberEmail,
    _getChatPageMessage, _getChatSenderEmail, _getChatSpaceDisplayName,
    _getChatSpaceListParms, _getChatSpaceMembers, _getChatSpaceSearchParms,
    _getValidateEmojiName, _printChatItem, _showChatItem,
    buildChatServiceObject, createChatEmoji, createChatMember,
    createChatMessage, createChatSpace, createUpdateChatSection,
    deleteChatEmoji, deleteChatMessage, deleteChatSection,
    deleteChatSpace, deleteUpdateChatMember, doCreateChatMessage,
    doDeleteChatMessage, doInfoChatEvent, doInfoChatMember,
    doInfoChatMessage, doInfoChatSpace, doPrintShowChatMembers,
    doPrintShowChatSpaces, doSetupChat, doUpdateChatMessage,
    exitIfChatNotConfigured, getChatSectionName, getChatSpaceParameters,
    getEmojiName, getSpaceName, getGroupMemberID, getUserMemberID,
    infoChatEmoji, infoChatEvent, infoChatMember, infoChatMessage,
    infoChatSpace, infoChatSpaceDM, moveShowChatSectionItem,
    normalizeUserMember, printShowChatEmojis, printShowChatEvents,
    printShowChatMembers, printShowChatMessages,
    printShowChatSearchMessages, printShowChatSectionItems,
    printShowChatSections, printShowChatSpaces, setupChatURL,
    syncChatMembers, trimChatMessageIfRequired, updateChatMessage,
    updateChatSpace,
)

from gam.cmd.meet import (  # noqa: F401  # re-export
    MEET_CONFERENCE_TIME_OBJECTS, MEET_SPACE_ACCESSTYPE_CHOICES,
    MEET_SPACE_ARTIFACT_SUB_OPTIONS, MEET_SPACE_ENTRYPOINTACCESS_CHOICES_MAP,
    MEET_SPACE_OPTIONS_MAP, MEET_SPACE_RESTRICTIONS_CHOICES_MAP,
    _getMeetPageMessage, _getMeetSpaceParameters, _printMeetConfItem,
    _printShowMeetItems, _showMeetConfItem, _showMeetItem,
    buildMeetServiceObject, createMeetSpace, endMeetConference,
    infoMeetSpace, printShowMeetConferences, printShowMeetParticipants,
    printShowMeetRecordings, printShowMeetTranscripts, updateMeetSpace,
)
from gam.cmd.chromepolicies import (  # noqa: F401  # re-export
    CHROME_IMAGE_SCHEMAS_MAP, CHROME_POLICY_INDEXED_TITLES,
    CHROME_POLICY_SCHEMA_FIELDS_CHOICE_MAP, CHROME_POLICY_SHOW_ALL,
    CHROME_POLICY_SHOW_CHOICE_MAP, CHROME_POLICY_SHOW_DIRECT,
    CHROME_POLICY_SHOW_INHERITED, CHROME_SCHEMA_SPECIAL_CASES,
    CHROME_TARGET_VERSION_CHANNEL_MINUS_PATTERN, CHROME_TARGET_VERSION_PATTERN,
    SCHEMA_TYPE_MESSAGE_MAP,
    _getChromePolicySchema, _getChromePolicySchemaName,
    _getOrgunitsOrgUnitIdPath, _getPolicyGroupTarget, _getPolicyOrgUnitTarget,
    _showChromePolicySchema, _showChromePolicySchemaStd,
    checkPolicyArgs, commonprefix, doCreateChromeNetwork,
    doCreateChromePolicyImage, doDeleteChromeNetwork, doDeleteChromePolicy,
    doInfoChromePolicySchemas, doInfoChromePolicySchemasStd,
    doPrintShowChromePolicies, doPrintShowChromePolicySchemas,
    doShowChromePolicySchemasStd, doUpdateChromePolicy,
    setPolicyKVList, simplifyChromeSchemaDisplay, simplifyChromeSchemaUpdate,
    updatePolicyRequests,
)

from gam.cmd.cidevices import (  # noqa: F401  # re-export
    DEVICEUSER_FIELDS_CHOICE_MAP, DEVICE_ACTION_CHOICES,
    DEVICE_FIELDS_CHOICE_MAP, DEVICE_MISSING_ACTION_MAP,
    DEVICE_ORDERBY_CHOICE_MAP, DEVICE_TIME_OBJECTS, DEVICE_TYPE_MAP,
    DEVICE_USERNAME_CLIENT_STATE_PATTERN, DEVICE_USERNAME_FORMAT_REQUIRED,
    DEVICE_USERNAME_PATTERN, DEVICE_USER_ACTION_CHOICES,
    DEVICE_USER_COMPLIANCE_STATE_CHOICE_MAP,
    DEVICE_USER_CUSTOM_VALUE_TYPE_CHOICE_MAP,
    DEVICE_USER_HEALTH_SCORE_CHOICE_MAP,
    DEVICE_USER_MANAGED_STATE_CHOICE_MAP, DEVICE_VIEW_CHOICE_MAP,
    _makeDeviceId, _performCIDeviceAction, _performCIDeviceUserAction,
    buildGAPICIDeviceServiceObject, doApproveCIDeviceUser,
    doBlockCIDeviceUser, doCancelWipeCIDevice, doCancelWipeCIDeviceUser,
    doCreateCIDevice, doDeleteCIDevice, doDeleteCIDeviceUser,
    doInfoCIDevice, doInfoCIDeviceUser, doInfoCIDeviceUserState,
    doPrintCIDeviceUsers, doPrintCIDevices, doSyncCIDevices,
    doUpdateCIDevice, doUpdateCIDeviceUser, doUpdateCIDeviceUserState,
    doWipeCIDevice, doWipeCIDeviceUser, getCIDeviceEntity,
    getCIDeviceUserEntity, getUpdateDeleteCIDeviceOptions,
)
from gam.cmd.printers import (  # noqa: F401  # re-export
    CHROME_APPS_TIME_OBJECTS, CHROME_APPS_TYPE_CHOICES,
    CREATE_PRINTER_JSON_SKIP_FIELDS, ORGUNIT_ENTITIES_MAP,
    PRINTER_FIELDS_CHOICE_MAP, PRINTER_TIME_OBJECTS,
    UPDATE_PRINTER_JSON_SKIP_FIELDS,
    _checkPrinterInheritance, _getPrinterAttributes, _getPrinterEntity,
    _getPrinterID, _showPrinter, doCreatePrinter, doDeletePrinter,
    doInfoPrinter, doPrintShowPrinterModels, doPrintShowPrinters,
    doUpdatePrinter, isolatePrinterID,
)
from gam.cmd.chromeapps import (  # noqa: F401  # re-export
    CHROME_APPS_ORDERBY_CHOICE_MAP, CHROME_APPS_TITLES,
    CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP,
    CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP, CHROME_APP_DEVICES_TITLES,
    CHROME_AUE_TITLES, CHROME_DEVICE_COUNTS_MODE_CHOICES,
    CHROME_DEVICE_COUNTS_MODE_CSV_TITLE, CHROME_DEVICE_COUNTS_MODE_FUNCTIONS,
    CHROME_HISTORY_ENTITY_CHOICE_MAP, CHROME_NEEDSATTN_TITLES,
    CHROME_VERSIONHISTORY_ITEMS, CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP,
    CHROME_VERSIONHISTORY_TIMEOBJECTS, CHROME_VERSIONHISTORY_TITLES,
    CHROME_VERSIONS_TITLES, MOBILE_ACTION_CHOICE_MAP,
    _getPrintChromeGetting, doInfoChromeApp, doPrintChromeSnValidity,
    doPrintShowChromeAppDevices, doPrintShowChromeApps,
    doPrintShowChromeAues, doPrintShowChromeDeviceCounts,
    doPrintShowChromeHistory, doPrintShowChromeNeedsAttn,
    doPrintShowChromeVersions, getPlatformChannelMap, getRelativeMilestone,
)

from gam.cmd.mobile import (  # noqa: F401  # re-export
    GROUP_ALIAS_ATTRIBUTES, GROUP_ASSIST_CONTENT_ATTRIBUTES,
    GROUP_ASSIST_CONTENT_CHOICES, GROUP_ATTRIBUTES_SET,
    GROUP_BASIC_ATTRIBUTES, GROUP_DEPRECATED_ATTRIBUTES,
    GROUP_DISCOVER_ATTRIBUTES, GROUP_DISCOVER_CHOICES,
    GROUP_FIELDS_WITH_CRS_NLS, GROUP_MERGED_ATTRIBUTES,
    GROUP_MERGED_ATTRIBUTES_PRINT_ORDER, GROUP_MERGED_TO_COMPONENT_MAP,
    GROUP_MODERATE_CONTENT_ATTRIBUTES, GROUP_MODERATE_CONTENT_CHOICES,
    GROUP_MODERATE_MEMBERS_ATTRIBUTES, GROUP_MODERATE_MEMBERS_CHOICES,
    GROUP_SETTINGS_ATTRIBUTES, MOBILE_FIELDS_CHOICE_MAP,
    MOBILE_ORDERBY_CHOICE_MAP, MOBILE_TIME_OBJECTS,
    _getMobileDeviceUser, _getMobileFieldsArguments,
    _getUpdateDeleteMobileOptions, _initMobileFieldsParameters,
    doDeleteMobileDevices, doInfoMobileDevices, doPrintMobileDevices,
    doUpdateMobileDevices, getMobileDeviceEntity,
)
from gam.cmd.groups import (  # noqa: F401  # re-export
ALL_GROUP_MEMBER_TYPES, CIGROUP_FIELDS_CHOICE_MAP,
    CIGROUP_FIELDS_WITH_CRS_NLS, CIGROUP_FULL_FIELDS,
    CIGROUP_INFO_ORDER, CIGROUP_PRINT_ORDER, CIGROUP_TIME_OBJECTS,
    GROUPMEMBERS_DEFAULT_FIELDS, GROUPMEMBERS_FIELDS_CHOICE_MAP,
    GROUPMEMBERS_SORT_FIELDS, GROUP_ACCESS_TYPE_CHOICE_MAP,
    GROUP_CIGROUP_ENTITYTYPE_MAP, GROUP_CIGROUP_FIELDS_MAP,
    GROUP_FIELDS_CHOICE_MAP, GROUP_INFO_PRINT_ORDER,
    GROUP_JSON_SKIP_FIELDS, GROUP_MEMBER_TYPES_MAP, GROUP_PREVIEW_TITLES,
    GroupIsAbuseOrPostmaster, INFO_GROUPMEMBERS_FIELDS,
    INFO_GROUP_OPTIONS, MEMBEROPTION_DISPLAYMATCH,
    MEMBEROPTION_GETDELIVERYSETTINGS, MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP,
    MEMBEROPTION_ISARCHIVED, MEMBEROPTION_ISSUSPENDED,
    MEMBEROPTION_MATCHPATTERN, MEMBEROPTION_MEMBERNAMES,
    MEMBEROPTION_NODUPLICATES, MEMBEROPTION_RECURSIVE, MEMBERS_TITLES,
    UPDATE_GROUP_SUBCMDS, _checkCIMemberMatch, _checkMemberMatch,
    _showCIGroup, addJsonGroupParents, addMemberInfoToRow,
    checkGroupMatchPatterns, checkGroupShowOwnedBy, checkReplyToCustom,
    clearUnneededGroupMatchPatterns, doCreateGroup, doDeleteGroups,
    doInfoGroupMembers, doInfoGroups, doPrintGroupMembers, doPrintGroups,
    doPrintShowGroupTree, doShowGroupMembers, doUpdateGroups,
    finalizeIPSGMGroupRolesMemberDisplayOptions, finalizeInternalDomains,
    getGroupAllowExternalMembers, getGroupAttrProperties, getGroupAttrValue,
    getGroupFilters, getGroupMatchPatterns, getGroupMemberTypes,
    getGroupMembers, getGroupMembersEntityList, getGroupParents,
    getGroupRoles, getIPSGMGroupRolesMemberDisplayOptions,
    getMemberMatchOptions, getPGGroupRolesMemberDisplayOptions,
    getSettingsFromGroup, getSyncOperation, groupFilters, infoGroupMembers,
    infoGroups, initIPSGMGroupMemberDisplayOptions, initMemberOptions,
    mapCIGroupFieldNames, mapCIGroupMemberFieldNames,
    mapGroupEmailForSettings, printGroupParents, setMemberDisplaySortTitles,
    setMemberDisplayTitles, showGroupParents,
    updateFieldsForGroupMatchPatterns, verifyGroupPrimaryEmail,
)
from gam.cmd.cigroups import (  # noqa: F401  # re-export
ALL_CIGROUP_MEMBER_TYPES, CIGROUPMEMBERS_DEFAULT_FIELDS,
    CIGROUPMEMBERS_FIELDS_CHOICE_MAP, CIGROUPMEMBERS_SORT_FIELDS,
    CIGROUPMEMBERS_TIME_OBJECTS, CIGROUP_MEMBER_TYPES_MAP,
    CIPOLICY_ADDITIONAL_WARNINGS, CIPOLICY_TIME_OBJECTS,
    _checkPoliciesWithDASA, _cleanPolicy, _filterPolicies,
    _getCIListGroupMembersArgs, _getPolicyAppNameFromId, _showPolicies,
    _showPolicy, checkCIGroupShowOwnedBy, doCreateCIGroup,
    doCreateUpdateCIPolicy, doDeleteCIGroups, doDeleteCIPolicies,
    doInfoCIGroupMembers, doInfoCIGroups, doInfoCIPolicies,
    doPrintCIGroupMembers, doPrintCIGroups, doPrintShowCIPolicies,
    doShowCIGroupMembers, doUpdateCIGroups, getCIGroupMemberTypes,
    getCIGroupMembers, getCIGroupMembersEntityList,
    getCIGroupTransitiveMembers, infoCIGroupMembers,
    updateFieldsForCIGroupMatchPatterns,
)

from gam.cmd.licenses import (  # noqa: F401  # re-export
    doPrintLicenses, doShowLicenses,
)
from gam.cmd.alerts import (  # noqa: F401  # re-export
    ALERT_FEEDBACK_ORDERBY_CHOICE_MAP, ALERT_ORDERBY_CHOICE_MAP,
    ALERT_TIME_OBJECTS, ALERT_TYPE_MAP, _showAlert, _showAlertFeedback,
    _showAlertSettings, doClearAlertSettings, doCreateAlertFeedback,
    doDeleteOrUndeleteAlert, doInfoAlert, doPrintShowAlertFeedback,
    doPrintShowAlerts, doShowAlertSettings, doUpdateAlertSettings,
)
from gam.cmd.resources import (  # noqa: F401  # re-export
    BUILDINGS_FIELDS_CHOICE_MAP, BUILDINGS_SORT_TITLES,
    BUILDING_ADDRESS_PRINT_ORDER, FEATURE_FIELDS_CHOICE_MAP,
    RESOURCE_ADDTL_FIELDS, RESOURCE_ALL_FIELDS, RESOURCE_CATEGORY_MAP,
    RESOURCE_DFLT_FIELDS, RESOURCE_FIELDS_CHOICE_MAP,
    RESOURCE_FIELDS_WITH_CRS_NLS,
    _doDeleteResourceCalendars, _doInfoResourceCalendars,
    _doUpdateResourceCalendars, _getBuildingAttributes,
    _getBuildingByNameOrId, _getBuildingNameById, _getFeatureAttributes,
    _getResourceACLsCalSettings, _getResourceCalendarAttributes,
    _makeBuildingIdNameMap, _showBuilding, _showResource,
    doCreateBuilding, doCreateFeature, doCreateResourceCalendar,
    doDeleteBuilding, doDeleteFeature, doDeleteResourceCalendar,
    doDeleteResourceCalendars, doInfoBuilding, doInfoResourceCalendar,
    doInfoResourceCalendars, doPrintShowBuildings, doPrintShowFeatures,
    doPrintShowResourceCalendars, doUpdateBuilding, doUpdateFeature,
    doUpdateResourceCalendar, doUpdateResourceCalendars,
    updateAutoAcceptInvitations,
)
from gam.cmd.calendar import (  # noqa: F401  # re-export
    ACL_SCOPE_CHOICES, CALENDAR_ACL_ROLES_MAP,
    CALENDAR_ATTENDEE_OPTIONAL_CHOICE_MAP,
    CALENDAR_ATTENDEE_STATUS_CHOICE_MAP,
    CALENDAR_EVENT_MAX_COLOR_INDEX, CALENDAR_EVENT_MIN_COLOR_INDEX,
    CALENDAR_EVENT_SENDUPDATES_CHOICE_MAP,
    CALENDAR_EVENT_STATUS_CHOICES, CALENDAR_EVENT_TRANSPARENCY_CHOICES,
    CALENDAR_EVENT_VISIBILITY_CHOICES,
    CALENDAR_MAX_COLOR_INDEX, CALENDAR_MIN_COLOR_INDEX,
    CALENDAR_SETTINGS_FIELDS_CHOICE_MAP,
    EVENT_ATTACHMENTS_SUBFIELDS_CHOICE_MAP,
    EVENT_ATTENDEES_SUBFIELDS_CHOICE_MAP,
    EVENT_CONFERENCEDATA_SUBFIELDS_CHOICE_MAP,
    EVENT_CREATOR_SUBFIELDS_CHOICE_MAP, EVENT_FIELDS_CHOICE_MAP,
    EVENT_FOCUSTIME_SUBFIELDS_CHOICE_MAP, EVENT_INDEXED_TITLES,
    EVENT_JSONATTENDEES_SUBFIELD_CLEAR_FIELDS, EVENT_JSON_CLEAR_FIELDS,
    EVENT_JSON_INSERT_CLEAR_FIELDS, EVENT_JSON_SUBFIELD_CLEAR_FIELDS,
    EVENT_JSON_UPDATE_CLEAR_FIELDS, EVENT_ORGANIZER_SUBFIELDS_CHOICE_MAP,
    EVENT_OUTOFOFFICE_SUBFIELDS_CHOICE_MAP, EVENT_PRINT_ORDER,
    EVENT_SHOW_ORDER, EVENT_SUBFIELDS_CHOICE_MAP, EVENT_TIME_OBJECTS,
    EVENT_TYPES_CHOICE_MAP, EVENT_TYPE_BIRTHDAY, EVENT_TYPE_DEFAULT,
    EVENT_TYPE_ENTITY_MAP, EVENT_TYPE_FOCUSTIME, EVENT_TYPE_FROMGMAIL,
    EVENT_TYPE_OUTOFOFFICE, EVENT_TYPE_PROPERTIES_NAME_MAP,
    EVENT_TYPE_WORKINGLOCATION, EVENT_WORKINGLOCATION_SUBFIELDS_CHOICE_MAP,
    LIST_EVENTS_DISPLAY_PROPERTIES, LIST_EVENTS_MATCH_FIELDS,
    LIST_EVENTS_SELECT_PROPERTIES,
    _addEventEntitySelectFields, _createCalendarACLs,
    _createCalendarEvents, _deleteCalendarEvents,
    _doCalendarsCreateACLs, _doInfoCalendarACLs,
    _doUpdateDeleteCalendarACLs, _emptyCalendarTrash, _eventMatches,
    _getCalendarCreateImportUpdateEventOptions,
    _getCalendarDeleteEventOptions, _getCalendarEventAttribute,
    _getCalendarEventReminders, _getCalendarInfoACLOptions,
    _getCalendarInfoEventOptions, _getCalendarListEventsDisplayProperty,
    _getCalendarListEventsProperty, _getCalendarMoveEventsOptions,
    _getCalendarPrintShowACLOptions, _getCalendarPrintShowEventOptions,
    _getCalendarSendUpdates, _getCalendarSetting, _getEventDaysOfWeek,
    _getEventFields, _getEventMatchFields, _getEventTypes,
    _infoCalendarACLs, _infoCalendarEvents, _moveCalendarEvents,
    _normalizeCalIdGetRuleIds, _normalizeResourceIdGetRuleIds,
    _printCalendarEvent, _printShowCalendarACLs,
    _printShowCalendarEvents, _processCalendarACLs,
    _purgeCalendarEvents, _resourceUpdateDeleteCalendarACLs,
    _setEventRecurrenceTimeZone, _showCalendarACL, _showCalendarEvent,
    _showCalendarSettings, _updateCalendarEvents,
    _updateDeleteCalendarACLs, _validateCalendarGetEventIDs,
    _validateCalendarGetEvents, _validateResourceId,
    _wipeCalendarEvents, checkCalendarExists,
    doCalendarsCreateACL, doCalendarsCreateACLs,
    doCalendarsCreateEvent, doCalendarsDeleteACL, doCalendarsDeleteACLs,
    doCalendarsDeleteEvents, doCalendarsDeleteEventsOld,
    doCalendarsEmptyTrash, doCalendarsImportEvent,
    doCalendarsInfoACLs, doCalendarsInfoEvents,
    doCalendarsModifySettings, doCalendarsMoveEvents,
    doCalendarsMoveEventsOld, doCalendarsPrintShowACLs,
    doCalendarsPrintShowEvents, doCalendarsPrintShowSettings,
    doCalendarsPurgeEvents, doCalendarsUpdateACL, doCalendarsUpdateACLs,
    doCalendarsUpdateEvents, doCalendarsUpdateEventsOld,
    doCalendarsWipeEvents, doResourceCreateCalendarACLs,
    doResourceDeleteCalendarACLs, doResourceInfoCalendarACLs,
    doResourcePrintShowCalendarACLs, doResourceUpdateCalendarACLs,
    getACLScope, getCalendarACLScope, getCalendarACLSendNotifications,
    getCalendarCreateUpdateACLsOptions, getCalendarDeleteACLsOptions,
    getCalendarEventEntity, getCalendarSettings,
    getCalendarSiteACLScopeEntity, getNormalizedCalIdCal,
    initCalendarEventEntity, normalizeCalendarId, validateCalendar,
)

from gam.cmd.schemas import (  # noqa: F401  # re-export
    SCHEMAS_INDEXED_TITLES, SCHEMAS_SORT_TITLES,
    SCHEMA_FIELDTYPE_CHOICE_MAP, _showSchema,
    doCreateUpdateUserSchemas, doDeleteUserSchemas,
    doInfoUserSchemas, doPrintShowUserSchemas,
)
from gam.cmd.cloudstorage import (  # noqa: F401  # re-export
    TAKEOUT_EXPORT_PATTERN, _copyStorageObjects,
    _getCloudStorageObject, doCopyCloudStorageBucket,
    doDownloadCloudStorageBucket, doDownloadCloudStorageFile,
    md5MatchesFile,
)
from gam.cmd.vault import (  # noqa: F401  # re-export
PRINT_USER_VAULT_HOLDS_TITLES, PRINT_VAULT_COUNTS_TITLES,
    PRINT_VAULT_EXPORTS_TITLES, PRINT_VAULT_HOLDS_TITLES,
    PRINT_VAULT_MATTERS_TITLES, PRINT_VAULT_QUERIES_TITLES,
    VAULT_CORPUS_ARGUMENT_MAP, VAULT_CORPUS_EXPORT_FORMATS,
    VAULT_CORPUS_OPTIONS_MAP, VAULT_CORPUS_QUERY_MAP,
    VAULT_COUNTS_CORPUS_ARGUMENT_MAP, VAULT_CSE_OPTION_MAP,
    VAULT_EXPORT_DATASCOPE_MAP, VAULT_EXPORT_FIELDS_CHOICE_MAP,
    VAULT_EXPORT_FORMAT_MAP, VAULT_EXPORT_REGION_MAP,
    VAULT_EXPORT_STATUS_MAP, VAULT_EXPORT_TIME_OBJECTS,
    VAULT_HOLD_FIELDS_CHOICE_MAP, VAULT_HOLD_TIME_OBJECTS,
    VAULT_MATTER_ACTIONS, VAULT_MATTER_FIELDS_CHOICE_MAP,
    VAULT_MATTER_STATE_MAP, VAULT_QUERY_ARGS,
    VAULT_QUERY_FIELDS_CHOICE_MAP, VAULT_QUERY_TIME_OBJECTS,
    VAULT_RESPONSE_STATUS_MAP, VAULT_SEARCH_METHODS_MAP,
    VAULT_SHARED_DRIVES_OPTION_MAP, VAULT_VOICE_COVERED_DATA_MAP,
    ZIP_EXTENSION_PATTERN,
    _buildVaultQuery, _cleanVaultExport, _cleanVaultHold,
    _cleanVaultMatter, _cleanVaultQuery, _getHoldQueryParameters,
    _setHoldQuery, _showVaultExport, _showVaultHold,
    _showVaultMatter, _showVaultQuery, _useVaultQueryForHold,
    _validateVaultQuery, convertExportNameToID, convertHoldNameToID,
    convertMatterNameToID, convertQueryNameToID, doActionVaultMatter,
    doCloseVaultMatter, doCopyVaultExport, doCopyVaultQuery,
    doCreateCopyVaultQuery, doCreateVaultExport, doCreateVaultHold,
    doCreateVaultMatter, doCreateVaultQuery, doDeleteVaultExport,
    doDeleteVaultHold, doDeleteVaultMatter, doDeleteVaultQuery,
    doDownloadVaultExport, doInfoVaultExport, doInfoVaultHold,
    doInfoVaultMatter, doInfoVaultQuery, doPrintShowVaultExports,
    doPrintShowVaultHolds, doPrintShowVaultMatters,
    doPrintShowVaultQueries, doPrintVaultCounts, doReopenVaultMatter,
    doUndeleteVaultMatter, doUpdateVaultHold, doUpdateVaultMatter,
    formatVaultNameId, getMatterItem, printShowUserVaultHolds,
    validateCollaborators, warnMatterNotOpen,
)

from gam.cmd.users import (  # noqa: F401  # re-export
ADDRESS_ARGUMENT_TO_FIELD_MAP, ALLOW_EMPTY_CUSTOM_TYPE,
    INFO_USER_OPTIONS, ORGANIZATION_ARGUMENT_TO_FIELD_MAP,
    PasswordOptions, SCHEMA_VALUE_PROCESS_MAP,
    UPDATE_USER_ARGUMENT_TO_PROPERTY_MAP, USERS_INDEXED_TITLES,
    USERS_ORDERBY_CHOICE_MAP, USER_ADDRESSES_PROPERTY_PRINT_ORDER,
    USER_ARRAY_PROPERTY_PRINT_ORDER, USER_FIELDS_CHOICE_MAP,
    USER_GUEST_PROPERTY_PRINT_ORDER, USER_JSON_SKIP_FIELDS,
    USER_LANGUAGE_PROPERTY_PRINT_ORDER,
    USER_LOCATIONS_PROPERTY_PRINT_ORDER,
    USER_MULTI_ATTR_FILTER_CHOICE_MAP, USER_NAME_PROPERTY_PRINT_ORDER,
    USER_ORGANIZATIONS_PROPERTY_PRINT_ORDER,
    USER_POSIX_PROPERTY_PRINT_ORDER, USER_SCALAR_PROPERTY_PRINT_ORDER,
    USER_SKIP_OBJECTS, USER_SSH_PROPERTY_PRINT_ORDER, USER_TIME_OBJECTS,
    _filterSchemaFields, _filterUserMultiAttributes,
    _formatLanguagesList, _getGroupOrgUnitMap, _getSchemaNameList,
    _getUserMultiAttributeFilters, _initSchemaParms,
    createUserAddAliases, createUserAddToGroups, deleteUsers,
    doCheckUserSuspended, doCreateGuestUser, doCreateUser,
    doDeleteUser, doDeleteUsers, doInfoUser, doInfoUsers,
    doPrintUserCountsByOrgUnit, doPrintUserEntity, doPrintUserList,
    doPrintUsers, doSuspendUnsuspendUser, doSuspendUnsuspendUsers,
    doUndeleteUser, doUndeleteUsers, doUpdateUser, doUpdateUsers,
    getNotifyArguments, getUserAttributes, getUserLicenses,
    infoUsers, signoutTurnoff2SVUsers, suspendUnsuspendUsers,
    undeleteUsers, updateUsers, verifyUserPrimaryEmail, waitForMailbox,
)
from gam.cmd.ciuserinvitations import (  # noqa: F401  # re-export
    CI_USERINVITATION_ORDERBY_CHOICE_MAP,
    CI_USERINVITATION_STATE_CHOICE_MAP,
    CI_USERINVITATION_TIME_OBJECTS,
    INBOUNDSSO_ALL_OIDC, INBOUNDSSO_ALL_SAML,
    INBOUNDSSO_INPUT_MODE_CHOICE_MAP, INBOUNDSSO_MODE_CHOICE_MAP,
    INBOUNDSSO_OUTPUT_MODE_CHOICE_MAP,
    _getCIUserInvitationsEntity, _getIsInvitableUser,
    _showUserInvitation, checkCIUserIsInvitable,
    doCIUserInvitationsAction, doCheckCIUserInvitations,
    doInfoCIUserInvitations, doPrintShowCIUserInvitations,
    infoCIUserInvitations, isolateCIUserInvitatonsEmail,
    quotedCIUserInvitatonsEmail,
)
from gam.cmd.sso import (  # noqa: F401  # re-export
    INBOUNDSSO_CREDENTIALS_TIME_OBJECTS,
    SITEVERIFICATION_METHOD_CHOICE_MAP,
    _convertInboundSSOProfileDisplaynameToName,
    _getInboundSSOAssignment, _getInboundSSOAssignmentArguments,
    _getInboundSSOAssignmentByTarget, _getInboundSSOAssignmentName,
    _getInboundSSOAssignments, _getInboundSSOModeService,
    _getInboundSSOProfileArguments, _getInboundSSOProfileByName,
    _getInboundSSOProfiles, _processInboundSSOAssignmentResult,
    _processInboundSSOCredentialsResult,
    _processInboundSSOProfileResult, _showInboundSSOAssignment,
    _showInboundSSOCredentials, _showInboundSSOProfile,
    _updateInboundAssignmentTargetNames,
    doCreateInboundSSOAssignment, doCreateInboundSSOCredential,
    doCreateInboundSSOProfile, doDeleteInboundSSOAssignment,
    doDeleteInboundSSOCredential, doDeleteInboundSSOProfile,
    doInfoInboundSSOAssignment, doInfoInboundSSOCredential,
    doInfoInboundSSOProfile, doPrintShowInboundSSOAssignments,
    doPrintShowInboundSSOCredentials, doPrintShowInboundSSOProfiles,
    doUpdateInboundSSOAssignment, doUpdateInboundSSOProfile,
    getCIOrgunitID, getInboundSSOCredentialsName,
    getInboundSSOProfileCredentials,
)
from gam.cmd.sites import (  # noqa: F401  # re-export
    deprecatedDomainSites, deprecatedUserSites,
    DNS_ERROR_CODES_MAP, PROFILE_ACCOUNT_TYPE_MAP,
    _showSiteVerificationInfo, doCreateSiteVerification,
    doInfoSiteVerification, doUpdateSiteVerification,
    printShowBusinessProfileAccounts, printShowWebMasterSites,
    printShowWebResources,
)
from gam.cmd.courses import (  # noqa: F401  # re-export
ADD_REMOVE_UPDATE_ITEM_TYPES_MAP,
    CLASSROOM_CREATE_ROLE_MAP,
    CLASSROOM_ROLE_ALL,
    CLASSROOM_ROLE_ENTITY_MAP,
    CLASSROOM_ROLE_MAP,
    CLASSROOM_ROLE_OWNER,
    CLASSROOM_ROLE_STUDENT,
    CLASSROOM_ROLE_TEACHER,
    CLEAR_SYNC_PARTICIPANT_TYPES_MAP,
    COURSE_ANNOUNCEMENTS_FIELDS_CHOICE_MAP,
    COURSE_ANNOUNCEMENTS_INDEXED_TITLES,
    COURSE_ANNOUNCEMENTS_ORDERBY_CHOICE_MAP,
    COURSE_ANNOUNCEMENTS_SORT_TITLES,
    COURSE_ANNOUNCEMENTS_TIME_OBJECTS,
    COURSE_COUNTS_KEY_TITLE,
    COURSE_COUNTS_MEMBER_ARGUMENTS,
    COURSE_CUS_FILTER_FIELDS_MAP,
    COURSE_CU_FILTER_FIELDS_MAP,
    COURSE_END_ARGUMENTS,
    COURSE_FIELDS_CHOICE_MAP,
    COURSE_MATERIAL_FIELDS_CHOICE_MAP,
    COURSE_MATERIAL_ID_ARGUMENTS,
    COURSE_MATERIAL_INDEXED_TITLES,
    COURSE_MATERIAL_ORDERBY_CHOICE_MAP,
    COURSE_MATERIAL_SORT_TITLES,
    COURSE_MATERIAL_STATE_ARGUMENTS,
    COURSE_MATERIAL_TIME_OBJECTS,
    COURSE_MEMBER_ARGUMENTS,
    COURSE_NOLEN_OBJECTS,
    COURSE_PARTICIPANTS_SORT_TITLES,
    COURSE_PROPERTY_PRINT_ORDER,
    COURSE_START_ARGUMENTS,
    COURSE_STATE_MAPS,
    COURSE_SUBMISSION_FIELDS_CHOICE_MAP,
    COURSE_SUBMISSION_TIME_OBJECTS,
    COURSE_TIME_OBJECTS,
    COURSE_TOPICS_SORT_TITLES,
    COURSE_TOPICS_TIME_OBJECTS,
    COURSE_U_FILTER_FIELDS_MAP,
    COURSE_WORK_FIELDS_CHOICE_MAP,
    COURSE_WORK_ID_ARGUMENTS,
    COURSE_WORK_INDEXED_TITLES,
    COURSE_WORK_ORDERBY_CHOICE_MAP,
    COURSE_WORK_SORT_TITLES,
    COURSE_WORK_STATE_ARGUMENTS,
    COURSE_WORK_TIME_OBJECTS,
    CourseAttributes,
    GUARDIAN_CLASS_ACCEPTED,
    GUARDIAN_CLASS_ALL,
    GUARDIAN_CLASS_ENTITY,
    GUARDIAN_CLASS_INVITATIONS,
    GUARDIAN_CLASS_MAP,
    GUARDIAN_CLASS_UNDEFINED,
    GUARDIAN_STATES,
    GUARDIAN_TIME_OBJECTS,
    PARTICIPANT_EN_MAP,
    _batchAddItemsToCourse,
    _batchRemoveItemsFromCourse,
    _cancelGuardianInvitation,
    _convertCourseUserIdToEmailName,
    _courseItemPassesFilter,
    _deleteGuardian,
    _doDeleteCourses,
    _doDeleteGuardian,
    _doInfoCourses,
    _doUpdateCourses,
    _getClassroomEmail,
    _getClassroomInvitationIds,
    _getClassroomInvitations,
    _getCourseAliasesMembers,
    _getCourseItemFilter,
    _getCourseName,
    _getCourseOwnerSA,
    _getCourseSelectionParameters,
    _getCourseShowProperties,
    _getCourseStates,
    _getCourseWMSelectionParameters,
    _getCoursesInfo,
    _getCoursesOwnerInfo,
    _gettingCourseEntityQuery,
    _gettingCourseSubmissionQuery,
    _gettingCoursesQuery,
    _initCourseItemFilter,
    _initCourseSelectionParameters,
    _initCourseShowProperties,
    _initCourseWMSelectionParameters,
    _inviteGuardian,
    _printCourseItemCount,
    _printShowGuardians,
    _setApplyCourseItemFilter,
    _setCourseFields,
    _updateCourseOwner,
    acceptClassroomInvitations,
    acceptDeleteClassroomInvitations,
    cancelGuardianInvitations,
    checkCourseExists,
    clearGuardians,
    createClassroomInvitations,
    deleteClassroomInvitations,
    deleteGuardians,
    doCancelGuardianInvitation,
    doClearCourseStudentGroups,
    doCourseAddItems,
    doCourseClearParticipants,
    doCourseRemoveItems,
    doCourseSyncParticipants,
    doCourseUpdateItems,
    doCreateCourse,
    doCreateCourseStudentGroups,
    doDeleteClassroomInvitations,
    doDeleteCourse,
    doDeleteCourseStudentGroups,
    doDeleteCourses,
    doDeleteGuardian,
    doInfoCourse,
    doInfoCourses,
    doInviteGuardian,
    doPrintCourseAnnouncements,
    doPrintCourseCounts,
    doPrintCourseMaterials,
    doPrintCourseParticipants,
    doPrintCourseStudentGroupMembers,
    doPrintCourseStudentGroups,
    doPrintCourseSubmissions,
    doPrintCourseTopics,
    doPrintCourseWM,
    doPrintCourseWork,
    doPrintCourses,
    doPrintShowClassroomInvitations,
    doPrintShowGuardians,
    doProcessCourseStudentGroupMembers,
    doUpdateCourse,
    doUpdateCourseStudentGroups,
    doUpdateCourses,
    getCourseAnnouncement,
    getGuardianEmails,
    getGuardianEntity,
    getGuardianInvitationEntity,
    getGuardianInvitationIds,
    inviteGuardians,
    printShowClassroomInvitations,
    printShowClassroomProfile,
    printShowGuardians,
    studentUnknownWarning,
    syncGuardians,
)
from gam.cmd.userservices import (  # noqa: F401  # re-export
    Act,
    CALENDAR_EXCLUDE_DOMAINS,
    CALENDAR_EXCLUDE_OPTIONS,
    CALENDAR_LIST_FIELDS_CHOICE_MAP,
    CALENDAR_NOTIFICATION_METHODS,
    CALENDAR_NOTIFICATION_TYPES_MAP,
    CALENDAR_SIMPLE_LISTS,
    CORPORA_ALL_DRIVES,
    CORPORA_CHOICE_MAP,
    Cmd,
    EVENT_AUTO_DECLINE_MODE_CHOICE_MAP,
    EVENT_CHAT_STATUS_CHOICE_MAP,
    Ent,
    Ind,
    QUERY_SHORTCUTS_MAP,
    SHAREDDRIVE_QUERY_SHORTCUTS_MAP,
    STATUS_EVENTS_DATETIME_CHOICES,
    USER_CALENDAR_SETTINGS_FIELDS_CHOICE_MAP,
    WORKING_LOCATION_CHOICE_MAP,
    YOUTUBE_CHANNEL_FIELDS_CHOICE_MAP,
    YOUTUBE_CHANNEL_TIME_OBJECTS,
    _createImportCalendarEvent,
    _getCalendarAttributes,
    _getCalendarPermissions,
    _getCalendarSelectProperty,
    _getEntityMimeType,
    _getMain,
    _getTargetEntityMimeType,
    _modifyRemoveCalendars,
    _processCalendarList,
    _showASPs,
    _showBackupCodes,
    _showCalendar,
    _showCalendarStatusEvent,
    _updateDeleteCalendars,
    _validateUserGetCalendarIds,
    addCalendars,
    addCreateCalendars,
    createCalendar,
    createCalendarACLs,
    createCalendarEvent,
    createFocusTime,
    createOutOfOffice,
    createStatusEvent,
    createWorkingLocation,
    deleteASP,
    deleteBackupCodes,
    deleteCalendarACLs,
    deleteCalendarEvents,
    deleteCalendars,
    deleteFocusTime,
    deleteOutOfOffice,
    deleteStatusEvent,
    deleteWorkingLocation,
    doCalendarsTransferOwnership,
    emptyCalendarTrash,
    getFocusTimeProperties,
    getOutOfOfficeProperties,
    getStatusEventDateTime,
    getStatusEventProperties,
    getStatusEventSummaryDecline,
    getUserCalendarEntity,
    getWorkingLocationProperties,
    importCalendarEvent,
    infoCalendarACLs,
    infoCalendarEvents,
    infoCalendars,
    initUserCalendarEntity,
    modifyCalendars,
    moveCalendarEvents,
    printShowASPs,
    printShowBackupCodes,
    printShowCalSettings,
    printShowCalendarACLs,
    printShowCalendarEvents,
    printShowCalendars,
    printShowFocusTime,
    printShowOutOfOffice,
    printShowStatusEvent,
    printShowWorkingLocation,
    printShowYouTubeChannel,
    purgeCalendarEvents,
    removeCalendars,
    updateBackupCodes,
    updateCalendarACLs,
    updateCalendarAttendees,
    updateCalendarEvents,
    updateCalendars,
    updateDeleteCalendarACLs,
    wipeCalendarEvents,
)
from gam.cmd.drive import (  # noqa: F401  # re-export
CHECK_LOCATION_FIELDS_TITLES,
    CONSOLIDATION_GROUPING_STRATEGY_CHOICE_MAP,
    COPY_NONINHERITED_PERMISSIONS_ALWAYS,
    COPY_NONINHERITED_PERMISSIONS_CHOICES_MAP,
    COPY_NONINHERITED_PERMISSIONS_NEVER,
    COPY_NONINHERITED_PERMISSIONS_SYNC_ALL_FOLDERS,
    COPY_NONINHERITED_PERMISSIONS_SYNC_UPDATED_FOLDERS,
    COPY_OWNED_BY_CHOICE_MAP,
    DELETE_DRIVEFILE_CHOICE_MAP,
    DELETE_DRIVEFILE_FUNCTION_TO_ACTION_MAP,
    DELETE_DRIVEFILE_FUNCTION_TO_CAPABILITY_MAP,
    DEST_PARENT_MYDRIVE_FOLDER,
    DEST_PARENT_MYDRIVE_ROOT,
    DEST_PARENT_SHAREDDRIVE_FOLDER,
    DEST_PARENT_SHAREDDRIVE_ROOT,
    DFA_ADD_PARENT_IDS,
    DFA_ADD_PARENT_NAMES,
    DFA_CREATED_TIME,
    DFA_IGNORE_DEFAULT_VISIBILITY,
    DFA_KEEP_REVISION_FOREVER,
    DFA_KWARGS,
    DFA_LOCALFILENAME,
    DFA_LOCALFILEPATH,
    DFA_LOCALMIMETYPE,
    DFA_MODIFIED_TIME,
    DFA_OCRLANGUAGE,
    DFA_PARENTID,
    DFA_PARENTQUERY,
    DFA_PRESERVE_FILE_TIMES,
    DFA_REMOVE_PARENT_IDS,
    DFA_REMOVE_PARENT_NAMES,
    DFA_REPLACEFILENAME,
    DFA_SEARCHARGS,
    DFA_SHAREDDRIVE_PARENT,
    DFA_SHAREDDRIVE_PARENTID,
    DFA_SHAREDDRIVE_PARENTQUERY,
    DFA_STRIPNAMEPREFIX,
    DFA_TIMEFORMAT,
    DFA_TIMESTAMP,
    DFA_URL,
    DFA_USE_CONTENT_AS_INDEXABLE_TEXT,
    DISKUSAGE_SHOW_CHOICES,
    DOCUMENT_FORMATS_MAP,
    DRIVEFILE_ACL_PERMISSION_DETAILS_TYPES,
    DRIVEFILE_ACL_PERMISSION_TYPES,
    DRIVEFILE_ACL_ROLES_MAP,
    DRIVEFILE_BASIC_PERMISSION_FIELDS,
    DRIVEFILE_ORDERBY_CHOICE_MAP,
    DRIVEFILE_PERMISSIONS_FOR_VIEW_CHOICES,
    DRIVEFILE_PROPERTY_VISIBILITY_CHOICE_MAP,
    DRIVELABELS_PERMISSION_ROLE_MAP,
    DRIVELABELS_PROJECTION_CHOICE_MAP,
    DRIVELABELS_TIME_OBJECTS,
    DRIVELABEL_FIELD_TYPE_MAP,
    DRIVESETTINGS_FIELDS_CHOICE_MAP,
    DRIVESETTINGS_SCALAR_FIELDS,
    DRIVESETTINGS_USAGE_BYTES_FIELDS,
    DRIVE_ACTIVITY_ACTION_MAP,
    DRIVE_BY_NAME_CHOICE_MAP,
    DRIVE_CAPABILITIES_SUBFIELDS_CHOICE_MAP,
    DRIVE_CONTENT_RESTRICTIONS_SUBFIELDS_CHOICE_MAP,
    DRIVE_DOWNLOAD_RESTRICTIONS_SUBFIELDS_CHOICE_MAP,
    DRIVE_FIELDS_CHOICE_MAP,
    DRIVE_FILE_CONTENT_RESTRICTIONS_CHOICE_MAP,
    DRIVE_FILE_ITEM_DOWNLOAD_RESTRICTION_CHOICE_MAP,
    DRIVE_INDEXED_TITLES,
    DRIVE_LABELINFO_SUBFIELDS_CHOICE_MAP,
    DRIVE_LABEL_CHOICE_MAP,
    DRIVE_LIST_FIELDS,
    DRIVE_OWNERS_SUBFIELDS_CHOICE_MAP,
    DRIVE_PARENTS_SUBFIELDS_CHOICE_MAP,
    DRIVE_PERMISSIONS_SUBFIELDS_CHOICE_MAP,
    DRIVE_REVISIONS_INDEXED_TITLES,
    DRIVE_SHARINGUSER_SUBFIELDS_CHOICE_MAP,
    DRIVE_SHORTCUTDETAILS_SUBFIELDS_CHOICE_MAP,
    DRIVE_SUBFIELDS_CHOICE_MAP,
    DRIVE_TIME_OBJECTS,
    DUPLICATE_FILE_CHOICES,
    DUPLICATE_FILE_DUPLICATE_NAME,
    DUPLICATE_FILE_OVERWRITE_ALL,
    DUPLICATE_FILE_OVERWRITE_OLDER,
    DUPLICATE_FILE_SKIP,
    DUPLICATE_FILE_UNIQUE_NAME,
    DUPLICATE_FOLDER_CHOICES,
    DUPLICATE_FOLDER_DUPLICATE_NAME,
    DUPLICATE_FOLDER_MERGE,
    DUPLICATE_FOLDER_SKIP,
    DUPLICATE_FOLDER_UNIQUE_NAME,
    DriveFileFields,
    DriveListParameters,
    FILECOMMENTS_AUTHOR_SUBFIELDS_CHOICE_MAP,
    FILECOMMENTS_FIELDS_CHOICE_MAP,
    FILECOMMENTS_INDEXED_TITLES,
    FILECOMMENTS_REPLIES_SUBFIELDS_CHOICE_MAP,
    FILECOMMENTS_SUBFIELDS_CHOICE_MAP,
    FILECOMMENTS_TIME_OBJECTS,
    FILECOUNT_SUMMARY_CHOICE_MAP,
    FILECOUNT_SUMMARY_NONE,
    FILECOUNT_SUMMARY_ONLY,
    FILECOUNT_SUMMARY_PLUS,
    FILECOUNT_SUMMARY_USER,
    FILEINFO_FIELDS_TITLES,
    FILELIST_FIELDS_TITLES,
    FILEPATH_FIELDS,
    FILEPATH_FIELDS_TITLES,
    FILEREVISIONS_FIELDS_CHOICE_MAP,
    FILEREVISIONS_TIME_OBJECTS,
    FILESHARECOUNTS_CATEGORIES,
    FILESHARECOUNTS_OWNER,
    FILESHARECOUNTS_SHARED,
    FILESHARECOUNTS_SHARED_EXTERNAL,
    FILESHARECOUNTS_SHARED_INTERNAL,
    FILESHARECOUNTS_TOTAL,
    FILESHARECOUNTS_ZEROCOUNTS,
    FILETREE_FIELDS_CHOICE_MAP,
    FILETREE_FIELDS_PRINT_ORDER,
    FILE_SUBTOTAL_STATS,
    FOLDER_SUBTOTAL_STATS,
    GOOGLEDOC_VALID_EXTENSIONS_MAP,
    HTTP_ERROR_PATTERN,
    LOCATION_ALL_DRIVES,
    LOCATION_CHOICE_MAP,
    LOCATION_MYDRIVE,
    LOCATION_ONLY_SHARED_DRIVES,
    LOCATION_ORPHANS,
    LOCATION_OWNEDBY_ANY,
    LOCATION_OWNEDBY_OTHERS,
    LOCATION_SHARED_WITHME,
    LOOKERSTUDIO_ADD_UPDATE_PERMISSION_ROLE_CHOICE_MAP,
    LOOKERSTUDIO_ASSETS_ORDERBY_CHOICE_MAP,
    LOOKERSTUDIO_ASSETS_TIME_OBJECTS,
    LOOKERSTUDIO_ASSETTYPE_CHOICE_MAP,
    LOOKERSTUDIO_DELETE_PERMISSION_ROLE_CHOICE_MAP,
    LOOKERSTUDIO_PERMISSION_MODIFIER_MAP,
    LOOKERSTUDIO_VIEW_PERMISSION_ROLE_CHOICE_MAP,
    MICROSOFT_FORMATS_LIST,
    MIMETYPE_CHOICE_MAP,
    MIMETYPE_EXTENSION_MAP,
    MIMETYPE_TYPES,
    MimeTypeCheck,
    NON_DOWNLOADABLE_MIMETYPES,
    OPENOFFICE_FORMATS_LIST,
    OWNED_BY_ME_FIELDS_TITLES,
    PRINT_ORGANIZER_TYPES,
    PermissionMatch,
    REVISIONS_FIELDS_CHOICE_MAP,
    SHAREDDRIVE_ACL_ROLES_MAP,
    SHAREDDRIVE_API_GUI_ROLES_MAP,
    SHAREDDRIVE_DOWNLOAD_RESTRICTIONS_MAP,
    SHAREDDRIVE_FIELDS_CHOICE_MAP,
    SHAREDDRIVE_LIST_FIELDS_CHOICE_MAP,
    SHAREDDRIVE_RESTRICTIONS_MAP,
    SHAREDDRIVE_ROLES_CAPABILITIES_MAP,
    SHAREDDRIVE_TIME_OBJECTS,
    SHORTCUT_CODE_MIMETYPE_MISMATCH,
    SHORTCUT_CODE_NOT_A_SHORTCUT,
    SHORTCUT_CODE_SHORTCUT_NOT_FOUND,
    SHORTCUT_CODE_TARGET_NOT_FOUND,
    SHORTCUT_CODE_VALID,
    SHOWLABELS_CHOICES,
    SHOWWEBVIEWLINK_CHOICES,
    SHOW_NO_PERMISSIONS_DRIVES_CHOICE_MAP,
    SHOW_OWNED_BY_CHOICE_MAP,
    SIZE_FIELD_CHOICE_MAP,
    STAT_FILE_COPIED_MOVED,
    STAT_FILE_DUPLICATE,
    STAT_FILE_FAILED,
    STAT_FILE_IN_SKIPIDS,
    STAT_FILE_NOT_COPYABLE_MOVABLE,
    STAT_FILE_PERMISSIONS_FAILED,
    STAT_FILE_PROTECTEDRANGES_FAILED,
    STAT_FILE_SHORTCUT_CREATED,
    STAT_FILE_SHORTCUT_EXISTS,
    STAT_FILE_TOTAL,
    STAT_FOLDER_COPIED_MOVED,
    STAT_FOLDER_DUPLICATE,
    STAT_FOLDER_FAILED,
    STAT_FOLDER_MERGED,
    STAT_FOLDER_NOT_WRITABLE,
    STAT_FOLDER_PERMISSIONS_FAILED,
    STAT_FOLDER_SHORTCUT_CREATED,
    STAT_FOLDER_SHORTCUT_EXISTS,
    STAT_FOLDER_TOTAL,
    STAT_LENGTH,
    STAT_USER_NOT_ORGANIZER,
    SUGGESTIONS_VIEW_MODE_CHOICE_MAP,
    TITLE_QUERY_PATTERN,
    TRANSFER_DRIVEFILE_ACL_ROLES_MAP,
    UNIQUE_PREFIX_PATTERN,
    _checkFileIdEntityDomainAccess,
    _checkForDuplicateTargetFile,
    _checkForExistingShortcut,
    _checkSharedDriveRestrictions,
    _checkUpdateLastModifiction,
    _convertSharedDriveNameToId,
    _copyPermissions,
    _driveFileParentSpecified,
    _finalizeIncludeLabels,
    _finalizeIncludePermissionsForView,
    _formatFileDriveLabels,
    _getCommentFields,
    _getCopyFolderNonInheritedPermissions,
    _getCopyMoveParentInfo,
    _getCopyMoveTargetInfo,
    _getDisplayDriveLabelsParameters,
    _getDriveFieldSubField,
    _getDriveFileACLPrintKeysTimeObjects,
    _getDriveFileAddRemoveParentInfo,
    _getDriveFileDownloadRestrictions,
    _getDriveFileNameFromId,
    _getDriveFileParentInfo,
    _getFileIdFromURL,
    _getFilenameParts,
    _getFilenamePrefix,
    _getGettingEntity,
    _getIncludeLabels,
    _getIncludePermissionsForView,
    _getLastModificationPath,
    _getLookerStudioAssetByID,
    _getLookerStudioAssets,
    _getSharedDriveNameFromId,
    _getSharedDriveRestrictions,
    _getSharedDriveRole,
    _getSharedDriveTheme,
    _getSheetProtectedRanges,
    _getUniqueFilename,
    _identicalSourceTarget,
    _incrStatistic,
    _initLastModification,
    _initStatistics,
    _mapDrive2QueryToDrive3,
    _mapDriveInfo,
    _mapDrivePermissionNames,
    _mapDriveUser,
    _moveSharedDriveToOU,
    _printStatistics,
    _recursiveUpdateMovePermissions,
    _selectRevisionIds,
    _selectRevisionResults,
    _setGetCheckFilePermissions,
    _setGetPermissionsForMyDriveSharedDrives,
    _setSkipObjects,
    _showComment,
    _showDriveFilePermission,
    _showDriveFilePermissionJSON,
    _showDriveFilePermissions,
    _showDriveFilePermissionsJSON,
    _showDriveLabel,
    _showDriveLabelPermission,
    _showLastModification,
    _showLookerStudioPermissions,
    _showRevision,
    _showSharedDrive,
    _showSharedDriveThemeSettings,
    _simpleFileIdEntityList,
    _stripCommentPhotoLinks,
    _stripMeInOwners,
    _stripNotMeInOwners,
    _targetFilenameExists,
    _updateAnyOwnerQuery,
    _updateLastModificationRow,
    _updateMoveFilePermissions,
    _updateSheetProtectedRanges,
    _updateSheetProtectedRangesACLchange,
    _validateACLAttributes,
    _validateACLOwnerType,
    _validatePermissionAttributes,
    _validatePermissionOwnerType,
    _validateUserGetFileIDs,
    _validateUserGetLookerStudioAssetIds,
    _validateUserGetSharedDriveFileIDs,
    _validateUserSharedDrive,
    _verifyUserIsOrganizer,
    addFilePathsToInfo,
    addFilePathsToRow,
    addTimestampToFilename,
    buildFileTree,
    checkDriveFileShortcut,
    claimOwnership,
    cleanFileIDsList,
    collectOrphans,
    copyDriveFile,
    copySyncSharedDriveACLs,
    createDriveFile,
    createDriveFileACL,
    createDriveFilePermissions,
    createDriveFileShortcut,
    createDriveFolderPath,
    createDriveLabelPermissions,
    createSharedDrive,
    deleteDriveFile,
    deleteDriveFileACLs,
    deleteDriveLabelPermissions,
    deleteEmptyDriveFolders,
    deleteFileRevisions,
    deletePermissions,
    deleteSharedDrive,
    doCopySyncSharedDriveACLs,
    doCreateDriveFileACL,
    doCreateDriveLabelPermissions,
    doCreatePermissions,
    doCreateSharedDrive,
    doDeleteDriveFileACLs,
    doDeleteDriveLabelPermissions,
    doDeletePermissions,
    doDeleteSharedDrive,
    doDriveSearch,
    doHideUnhideSharedDrive,
    doInfoDriveFileACLs,
    doInfoDriveLabels,
    doInfoSharedDrive,
    doPrintSharedDriveOrganizers,
    doPrintShowDriveFileACLs,
    doPrintShowDriveLabelPermissions,
    doPrintShowDriveLabels,
    doPrintShowOrgunitSharedDrives,
    doPrintShowOwnership,
    doPrintShowSharedDriveACLs,
    doPrintShowSharedDrives,
    doSharedDriveSearch,
    doShowSharedDriveThemes,
    doUpdateDriveFileACLs,
    doUpdateSharedDrive,
    emptyDriveTrash,
    escapeDriveFileName,
    extendFileTree,
    extendFileTreeParents,
    getCopyMoveOptions,
    getCreationModificationTimes,
    getDriveFile,
    getDriveFileAddRemoveParentAttribute,
    getDriveFileAttribute,
    getDriveFileCopyAttribute,
    getDriveFileEntity,
    getDriveFileEntitySharedDriveOnly,
    getDriveFileParentAttribute,
    getDriveFilePermissionsFields,
    getDriveFileProperty,
    getEscapedDriveFileName,
    getEscapedDriveFolderName,
    getFilePaths,
    getGoogleDocument,
    getLookerStudioAssetSelectionParameters,
    getMediaBody,
    getMimeType,
    getPermissionIdForEmail,
    getRevisionsEntity,
    getSharedDriveEntity,
    hideUnhideSharedDrive,
    infoDriveFileACLs,
    infoDriveLabels,
    infoSharedDrive,
    initCopyMoveOptions,
    initDriveFileAttributes,
    initDriveFileEntity,
    initFilePathInfo,
    initFileTree,
    initLookerStudioAssetSelectionParameters,
    moveDriveFile,
    noFileSelectFileIdEntity,
    normalizeDriveLabelID,
    normalizeDriveLabelName,
    printDiskUsage,
    printDriveActivity,
    printEmptyDriveFolders,
    printFileList,
    printFileParentTree,
    printSharedDriveOrganizers,
    printShowDriveFileACLs,
    printShowDriveLabelPermissions,
    printShowDriveLabels,
    printShowDriveSettings,
    printShowDrivelastModifications,
    printShowFileComments,
    printShowFileCounts,
    printShowFilePaths,
    printShowFileRevisions,
    printShowFileShareCounts,
    printShowFileTree,
    printShowLookerStudioAssets,
    printShowSharedDriveACLs,
    printShowSharedDrives,
    processFileDriveLabels,
    processFilenameReplacements,
    purgeDriveFile,
    setPreservedFileTimes,
    showFileInfo,
    showSharedDriveThemes,
    transferDrive,
    transferOwnership,
    trashDriveFile,
    untrashDriveFile,
    updateDriveFile,
    updateDriveFileACLs,
    updateFileRevisions,
    updateGoogleDocument,
    updateSharedDrive,
    validateDriveLabelName,
    validateMimeType,
    validateUserGetPermissionId,
    writeReturnIdLink,
)
from gam.cmd.gmail import (  # noqa: F401  # re-export
    CSE_IDENTITY_ACTION_FUNCTION_MAP,
    CSE_IDENTITY_TIME_OBJECTS,
    CSE_KEYPAIR_ACTION_FUNCTION_MAP,
    CSE_KEYPAIR_TIME_OBJECTS,
    EMAILSETTINGS_FORWARD_POP_ACTION_CHOICE_MAP,
    EMAILSETTINGS_IMAP_EXPUNGE_BEHAVIOR_CHOICE_MAP,
    EMAILSETTINGS_IMAP_MAX_FOLDER_SIZE_CHOICES,
    EMAILSETTINGS_OLD_NEW_OLD_FORWARD_ACTION_MAP,
    EMAILSETTINGS_POP_ENABLE_FOR_CHOICE_MAP,
    FILTER_ACTION_CHOICES,
    FILTER_ACTION_LABEL_MAP,
    FILTER_ADD_LABEL_ACTIONS,
    FILTER_ADD_LABEL_TO_ARGUMENT_MAP,
    FILTER_CATEGORY_CHOICE_MAP,
    FILTER_CRITERIA_CHOICE_MAP,
    FILTER_REMOVE_LABEL_ACTIONS,
    FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP,
    FORM_RESPONSE_TIME_OBJECTS,
    GMAIL_CATEGORY_LABELS,
    GMAIL_SYSTEM_LABELS,
    HEADER_ENCODE_PATTERN,
    IMPORT_INSERT,
    LABEL_COUNTS_FIELDS,
    LABEL_COUNTS_FIELDS_LIST,
    LABEL_DISPLAY_FIELDS_LIST,
    LABEL_LABEL_LIST_VISIBILITY_CHOICE_MAP,
    LABEL_MESSAGE_LIST_VISIBILITY_CHOICES,
    LABEL_QUERY_REPLACEMENT_CHARACTERS,
    LABEL_TYPE_SYSTEM,
    LABEL_TYPE_USER,
    MESSAGES_MAX_TO_KEYWORDS,
    MESSAGE_TIME_QUERY_PATTERN,
    PRINT_LABELS_TITLES,
    SHOW_LABELS_DISPLAY_CHOICES,
    SIG_REPLY_COMPACT,
    SIG_REPLY_FORMAT,
    SIG_REPLY_HTML,
    SIG_REPLY_OPTIONS_MAP,
    SIG_REPLY_TEMPLATE,
    SMTPMSA_DISPLAY_FIELDS,
    SMTPMSA_PORTS,
    SMTPMSA_REQUIRED_FIELDS,
    SMTPMSA_SECURITY_MODES,
    SMTP_ADDRESS_HEADERS,
    SMTP_DATE_HEADERS,
    SMTP_HEADERS_MAP,
    SMTP_NAME_ADDRESS_PATTERN,
    VACATION_END_NOT_SPECIFIED,
    VACATION_START_STARTED,
    _convertLabelNamesToIds,
    _decodeHeader,
    _deleteInfoForwardingAddreses,
    _draftImportInsertMessage,
    _finalizeMessageSelectParameters,
    _getLabelId,
    _getLabelName,
    _getLabelSet,
    _getMessageSelectParameters,
    _getPublishSettings,
    _getSmimeIds,
    _getUserGmailLabels,
    _imapDefaults,
    _initCSEKeyPairSkipObjects,
    _initLabelNameMap,
    _initMessageThreadParameters,
    _initPublishSettings,
    _mapFilterLabelIdsToNames,
    _mapMessageQueryDates,
    _popDefaults,
    _printFilter,
    _printShowCSEItems,
    _processForwardingAddress,
    _processMessagesThreads,
    _processSendAs,
    _processSignature,
    _resetCSEKeyPairSkipObjects,
    _setImap,
    _setPop,
    _showCSEItem,
    _showFilter,
    _showForward,
    _showForwardingAddress,
    _showImap,
    _showPop,
    _showSendAs,
    _showVacation,
    _stripCSEKeyPairSkipObjects,
    _validateLabelList,
    archiveMessages,
    buildLabelPath,
    checkLabelColor,
    cleanLabelQuery,
    createCSEKeyPair,
    createFilter,
    createForm,
    createForwardingAddresses,
    createLabel,
    createLabelList,
    createLabels,
    createSmime,
    createUpdateCSEIdentity,
    createUpdateSendAs,
    delegateTo,
    deleteFilters,
    deleteForwardingAddresses,
    deleteInfoSendAs,
    deleteLabel,
    deleteLabelId,
    deleteLabelIdList,
    deleteLabelIds,
    deleteLabelList,
    deleteLabels,
    deleteSmime,
    draftMessage,
    exportMessages,
    exportMessagesThreads,
    exportThreads,
    findFormRequest,
    forwardMessagesThreads,
    getLabelAttributes,
    getSendAsAttributes,
    importMessage,
    infoFilters,
    infoForwardingAddresses,
    insertMessage,
    printShowCSEIdentities,
    printShowCSEKeyPairs,
    printShowDelegates,
    printShowFilters,
    printShowFormResponses,
    printShowForms,
    printShowForward,
    printShowForwardingAddresses,
    printShowGmailProfile,
    printShowImap,
    printShowLabels,
    printShowLanguage,
    printShowMessages,
    printShowMessagesThreads,
    printShowPop,
    printShowSendAs,
    printShowSignature,
    printShowSmimes,
    printShowThreads,
    printShowVacation,
    processCSEIdentity,
    processCSEKeyPair,
    processDelegates,
    processMessages,
    processThreads,
    sendCreateDelegateNotification,
    setForward,
    setImap,
    setLanguage,
    setPop,
    setSignature,
    setVacation,
    updateDelegates,
    updateForm,
    updateFormInfoRequest,
    updateFormRequestUpdateMasks,
    updateFormSettingsRequest,
    updateLabelSettings,
    updateLabelSettingsById,
    updateLabels,
    updateSmime,
    watchGmail,
)

from gam.cmd.userop import (  # noqa: F401  # re-export
    LICENSE_PREVIEW_TITLES,
    LICENSE_PRODUCT_SKUIDS,
    PROFILE_SHARING_CHOICE_MAP,
    SHEET_DATETIME_RENDER_OPTIONS_MAP,
    SHEET_DIMENSIONS_MAP,
    SHEET_INSERT_DATA_OPTIONS_MAP,
    SHEET_VALUE_INPUT_OPTIONS_MAP,
    SHEET_VALUE_RENDER_OPTIONS_MAP,
    SPREADSHEET_FIELDS_CHOICE_MAP,
    SPREADSHEET_SHEETS_SUBFIELDS_CHOICE_MAP,
    TOKENS_AGGREGATE_FIELDS_TITLES,
    TOKENS_AGGREGATE_ORDERBY_CHOICE_MAP,
    TOKENS_FIELDS_TITLES,
    TOKENS_TITLE_MAP,
    _addUserToGroups,
    _createLicenses,
    _deleteLicenses,
    _deleteUserFromGroups,
    _getSpreadsheetRangesValues,
    _getUserGroupDomainCustomerId,
    _getUserGroupOptionalDomainCustomerId,
    _printShowTokens,
    _setShowProfile,
    _setUserGroupArgs,
    _showUpdateValuesResponse,
    _showValueRange,
    _updateUserGroups,
    _validateSubkeyRoleGetGroups,
    _validateUserGetSpreadsheetIDs,
    _writeLicenseAction,
    addUserToGroups,
    appendSheetRanges,
    checkUserGroupMatchPattern,
    checkUserInGroups,
    clearSheetRanges,
    commonClientIds,
    createLicense,
    createSheet,
    deleteLicense,
    deletePhoto,
    deleteTokens,
    deleteUserFromGroups,
    deprovisionUser,
    doPrintShowTokens,
    getLicenseParameters,
    getPhoto,
    getProfilePhoto,
    getUserPhoto,
    infoPrintShowSheets,
    printShowGroupTree,
    printShowLookerStudioPermissions,
    printShowSheetRanges,
    printShowTokens,
    printShowUserGroups,
    printUserGroupsList,
    processLookerStudioPermissions,
    setProfile,
    showProfile,
    syncLicense,
    syncUserWithGroups,
    updateLicense,
    updatePhoto,
    updateSheetRanges,
    updateSheets,
    updateUserGroups,
)

from gam.cmd.notes import (  # noqa: F401  # re-export
    Act,
    Cmd,
    Ent,
    GET_NOTE_HTTP_ERROR_PATTERN,
    Ind,
    NOTES_COUNTS_MAP,
    NOTES_FIELDS_CHOICE_MAP,
    NOTES_ROLE_CHOICE_MAP,
    NOTES_TIME_OBJECTS,
    _assignNoteOwner,
    _checkNoteUserRole,
    _getMain,
    _showNote,
    _showNoteAttachments,
    _showNoteListItems,
    _showNotePermissions,
    createNote,
    createNotesACLs,
    deleteInfoNotes,
    deleteNotesACLs,
    getNoteAttachments,
    normalizeNoteName,
    printShowNotes,
)

from gam.cmd.tasks import (  # noqa: F401  # re-export
    Act,
    Cmd,
    Ent,
    Ind,
    TAGMANAGER_PARAMETERS,
    TASKLIST_SKIP_OBJECTS,
    TASKLIST_TIME_OBJECTS,
    TASK_ORDERBY_CHOICE_MAP,
    TASK_QUERY_STATE_MAP,
    TASK_QUERY_TIME_MAP,
    TASK_SKIP_OBJECTS,
    TASK_STATUS_MAP,
    TASK_TIME_OBJECTS,
    _getMain,
    _showTask,
    _showTasklist,
    getTaskAttribute,
    getTaskListIDfromTitle,
    getTaskLists,
    getTaskMoveAttribute,
    importTasklist,
    printShowTagManagerAccounts,
    printShowTagManagerContainers,
    printShowTagManagerObjects,
    printShowTagManagerPermissions,
    printShowTagManagerTags,
    printShowTagManagerWorkspaces,
    printShowTasklists,
    printShowTasks,
    processTasklists,
    processTasks,
    verifyTasksServiceEnabled,
)
from gam.cmd.caa import (  # noqa: F401  # re-export
    Act,
    CAABuildBasicLevel,
    CAABuildCondition,
    CAABuildDevicePolicy,
    CAABuildLevel,
    CAABuildOsConstraints,
    CAARoleErrorExit,
    CAA_ALLOWED_DEVICE_MANAGEMENT_LEVELS_MAP,
    CAA_ALLOWED_ENCRYPTIION_STATUS_MAP,
    CAA_OS_TYPE_MAP,
    Cmd,
    Ent,
    ISO3166_1_ALPHA_2_CODES,
    Ind,
    _getMain,
    buildCAAServiceObject,
    doCreateCAALevel,
    doDeleteCAALevel,
    doPrintShowCAALevels,
    doUpdateCAALevel,
    getAccessPolicy,
    normalizeCAALevelName,
    validateISO3166_1_alpha2_code,
)















IS08601_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S%:z'
RFC2822_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S %z'

def ISOformatTimeStamp(timestamp):
  return timestamp.isoformat('T', 'seconds')

def currentISOformatTimeStamp(timespec='milliseconds'):
  return arrow.now(GC.Values[GC.TIMEZONE]).isoformat('T', timespec)

Act = glaction.GamAction()
Cmd = glclargs.GamCLArgs()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()

# Finding path method varies between Python source, PyInstaller and StaticX
if os.environ.get('STATICX_PROG_PATH', False):
  # StaticX static executable
  GM.Globals[GM.GAM_PATH] = os.path.dirname(os.environ['STATICX_PROG_PATH'])
  GM.Globals[GM.GAM_TYPE] = 'staticx'
elif getattr(sys, 'frozen', False):
  # Pyinstaller executable
  GM.Globals[GM.GAM_PATH] = os.path.dirname(sys.executable)
  GM.Globals[GM.GAM_TYPE] = 'pyinstaller'
else:
  # Source code
  GM.Globals[GM.GAM_PATH] = os.path.dirname(os.path.realpath(__file__))
  GM.Globals[GM.GAM_TYPE] = 'pythonsource'

GIT_USER = 'GAM-team'
GAM = 'GAM'
GAM_URL = f'https://github.com/{GIT_USER}/{GAM}'
GAM_USER_AGENT = (f'{GAM} {__version__} - {GAM_URL} / '
                  f'{__author__} / '
                  f'Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]} {sys.version_info[3]} / '
                  f'{platform.platform()} {platform.machine()} /'
                  )
GAM_RELEASES = f'https://github.com/{GIT_USER}/{GAM}/releases'
GAM_WIKI = f'https://github.com/{GIT_USER}/{GAM}/wiki'
GAM_LATEST_RELEASE = f'https://api.github.com/repos/{GIT_USER}/{GAM}/releases/latest'
GAM_PROJECT_CREATION = 'GAM Project Creation'
GAM_PROJECT_CREATION_CLIENT_ID = '297408095146-fug707qsjv4ikron0hugpevbrjhkmsk7.apps.googleusercontent.com'

TRUE = 'true'
FALSE = 'false'
TRUE_VALUES = [TRUE, 'on', 'yes', 'enabled', '1']
FALSE_VALUES = [FALSE, 'off', 'no', 'disabled', '0']
TRUE_FALSE = [TRUE, FALSE]
ERROR = 'ERROR'
ERROR_PREFIX = ERROR+': '
WARNING = 'WARNING'
WARNING_PREFIX = WARNING+': '
ONE_KILO_10_BYTES = 1000
ONE_MEGA_10_BYTES = ONE_KILO_10_BYTES*ONE_KILO_10_BYTES
ONE_GIGA_10_BYTES = ONE_KILO_10_BYTES*ONE_MEGA_10_BYTES
ONE_TERA_10_BYTES = ONE_KILO_10_BYTES*ONE_GIGA_10_BYTES
ONE_KILO_BYTES = 1024
ONE_MEGA_BYTES = ONE_KILO_BYTES*ONE_KILO_BYTES
ONE_GIGA_BYTES = ONE_KILO_BYTES*ONE_MEGA_BYTES
ONE_TERA_BYTES = ONE_KILO_BYTES*ONE_GIGA_BYTES
DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800
MAX_GOOGLE_SHEET_CELLS = 10000000 # See https://support.google.com/drive/answer/37603
MAX_LOCAL_GOOGLE_TIME_OFFSET = 30
SHARED_DRIVE_MAX_FILES_FOLDERS = 500000
UTF8 = 'utf-8'
UTF8_SIG = 'utf-8-sig'
EV_GAMCFGDIR = 'GAMCFGDIR'
EV_GAMCFGSECTION = 'GAMCFGSECTION'
EV_OLDGAMPATH = 'OLDGAMPATH'
FN_GAM_CFG = 'gam.cfg'
FN_LAST_UPDATE_CHECK_TXT = 'lastupdatecheck.txt'
FN_GAMCOMMANDS_TXT = 'GamCommands.txt'
MY_DRIVE = 'My Drive'
TEAM_DRIVE = 'Drive'
ROOT = 'root'
ROOTID = 'rootid'
ORPHANS = 'Orphans'
SHARED_WITHME = 'SharedWithMe'
SHARED_DRIVES = 'SharedDrives'

LOWERNUMERIC_CHARS = string.ascii_lowercase+string.digits
ALPHANUMERIC_CHARS = LOWERNUMERIC_CHARS+string.ascii_uppercase
URL_SAFE_CHARS = ALPHANUMERIC_CHARS+'-._~'
PASSWORD_SAFE_CHARS = ALPHANUMERIC_CHARS+'!#$%&()*-./:;<=>?@[\\]^_{|}~'
FILENAME_SAFE_CHARS = ALPHANUMERIC_CHARS+'-_.() '
CHAT_MESSAGEID_CHARS = string.ascii_lowercase+string.digits+'-'

GOOGLE_MEETID_PATTERN = re.compile(r'^[a-z]{3}-[a-z]{4}-[a-z]{3}$')
GOOGLE_MEETID_FORMAT_REQUIRED = 'abc-defg-hij'

ADMIN_ACCESS_OPTIONS = {'adminaccess', 'asadmin'}
OWNER_ACCESS_OPTIONS = {'owneraccess', 'asowner'}

# Python 3 values
DEFAULT_CSV_READ_MODE = 'r'
DEFAULT_FILE_APPEND_MODE = 'a'
DEFAULT_FILE_READ_MODE = 'r'
DEFAULT_FILE_WRITE_MODE = 'w'

# Google API constants
APPLICATION_VND_GOOGLE_APPS = 'application/vnd.google-apps.'
MIMETYPE_GA_DOCUMENT = f'{APPLICATION_VND_GOOGLE_APPS}document'
MIMETYPE_GA_DRAWING = f'{APPLICATION_VND_GOOGLE_APPS}drawing'
MIMETYPE_GA_FILE = f'{APPLICATION_VND_GOOGLE_APPS}file'
MIMETYPE_GA_FOLDER = f'{APPLICATION_VND_GOOGLE_APPS}folder'
MIMETYPE_GA_FORM = f'{APPLICATION_VND_GOOGLE_APPS}form'
MIMETYPE_GA_FUSIONTABLE = f'{APPLICATION_VND_GOOGLE_APPS}fusiontable'
MIMETYPE_GA_JAM = f'{APPLICATION_VND_GOOGLE_APPS}jam'
MIMETYPE_GA_MAP = f'{APPLICATION_VND_GOOGLE_APPS}map'
MIMETYPE_GA_PRESENTATION = f'{APPLICATION_VND_GOOGLE_APPS}presentation'
MIMETYPE_GA_SCRIPT = f'{APPLICATION_VND_GOOGLE_APPS}script'
MIMETYPE_GA_SCRIPT_JSON = f'{APPLICATION_VND_GOOGLE_APPS}script+json'
MIMETYPE_GA_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}shortcut'
MIMETYPE_GA_3P_SHORTCUT = f'{APPLICATION_VND_GOOGLE_APPS}drive-sdk'
MIMETYPE_GA_SITE = f'{APPLICATION_VND_GOOGLE_APPS}site'
MIMETYPE_GA_SPREADSHEET = f'{APPLICATION_VND_GOOGLE_APPS}spreadsheet'
MIMETYPE_TEXT_CSV = 'text/csv'
MIMETYPE_TEXT_HTML = 'text/html'
MIMETYPE_TEXT_PLAIN = 'text/plain'

GOOGLE_NAMESERVERS = ['8.8.8.8', '8.8.4.4']
GOOGLE_TIMECHECK_LOCATION = 'admin.googleapis.com'
NEVER_DATE = '1970-01-01'
NEVER_DATETIME = '1970-01-01 00:00'
NEVER_TIME = '1970-01-01T00:00:00.000Z'
NEVER_TIME_NOMS = '1970-01-01T00:00:00Z'
NEVER_END_DATE = '1969-12-31'
NEVER_START_DATE = NEVER_DATE
PROJECTION_CHOICE_MAP = {'basic': 'BASIC', 'full': 'FULL'}
REFRESH_EXPIRY = '1970-01-01T00:00:01Z'
REPLACE_GROUP_PATTERN = re.compile(r'\\(\d+)')
UNKNOWN = 'Unknown'

# Queries
ME_IN_OWNERS = "'me' in owners"
ME_IN_OWNERS_AND = ME_IN_OWNERS+" and "
AND_ME_IN_OWNERS = " and "+ME_IN_OWNERS
NOT_ME_IN_OWNERS = "not "+ME_IN_OWNERS
NOT_ME_IN_OWNERS_AND = NOT_ME_IN_OWNERS+" and "
AND_NOT_ME_IN_OWNERS = " and "+NOT_ME_IN_OWNERS
ANY_FOLDERS = "mimeType = '"+MIMETYPE_GA_FOLDER+"'"
MY_FOLDERS = ME_IN_OWNERS_AND+ANY_FOLDERS
NON_TRASHED = "trashed = false"
WITH_PARENTS = "'{0}' in parents"
ANY_NON_TRASHED_WITH_PARENTS = "trashed = false and '{0}' in parents"
ANY_NON_TRASHED_FOLDER_NAME = "mimeType = '"+MIMETYPE_GA_FOLDER+"' and name = '{0}' and trashed = false"
MY_NON_TRASHED_FOLDER_NAME = ME_IN_OWNERS_AND+ANY_NON_TRASHED_FOLDER_NAME
MY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS = ME_IN_OWNERS_AND+"mimeType = '"+MIMETYPE_GA_FOLDER+"' and name = '{0}' and trashed = false and '{1}' in parents"
ANY_NON_TRASHED_FOLDER_NAME_WITH_PARENTS = "mimeType = '"+MIMETYPE_GA_FOLDER+"' and name = '{0}' and trashed = false and '{1}' in parents"
WITH_ANY_FILE_NAME = "name = '{0}'"
WITH_MY_FILE_NAME = ME_IN_OWNERS_AND+WITH_ANY_FILE_NAME
WITH_OTHER_FILE_NAME = NOT_ME_IN_OWNERS_AND+WITH_ANY_FILE_NAME
AND_NOT_SHORTCUT = " and mimeType != '"+MIMETYPE_GA_SHORTCUT+"'"

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

DEBUG_REDACTION_PATTERNS = [
  # Positional patterns that redact sensitive credentials based on their location
  (r'(Bearer\s+)\S+', r'\1*****'), # access tokens and JWTs in auth header
  (r'([?&]refresh_token=)[^&]*', r'\1*****'), # refresh token URL parameter
  (r'([?&]client_secret=)[^&]*', r'\1*****'), # client secret URL parameter
  (r'([?&]key=)[^&]*', r'\1*****'), # API key URL parameter
  (r'([?&]code=)[^&]*', r'\1*****'), # auth code URL parameter

  # Pattern match patterns that redact sensitive credentials based on known credential pattern
  (r'ya29.[0-9A-Za-z-_]+', '*****'), # Access token
  (r'1%2F%2F[0-9A-Za-z-_]{100}|1%2F%2F[0-9A-Za-z-_]{64}|1%2F%2F[0-9A-Za-z-_]{43}', '*****'), # Refresh token
  (r'4/[0-9A-Za-z-_]+', '*****'), # Auth code
  (r'GOCSPX-[0-9a-zA-Z-_]{28}', '*****'), # Client secret
  (r'AIza[0-9A-Za-z-_]{35}', '*****'), # API key
  (r'eyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]*', '*****'), # JWT
  ]

def redactable_debug_print(*args):
  processed_args = []
  for arg in args:
    if arg.startswith('b\''):
      sbytes = arg[2:-1]
      sbytes = bytes(sbytes, 'utf-8')
      arg = sbytes.decode()
      arg = arg.replace('\\r\\n', "\n          ")
    if GC.Values[GC.DEBUG_REDACTION]:
      for pattern, replace in DEBUG_REDACTION_PATTERNS:
        arg = re.sub(pattern, replace, arg)
    processed_args.append(arg)
  print(*processed_args)

# Multiprocessing lock
mplock = None

# stdin/stdout/stderr — extracted to gam.util.output
from util.output import readStdin  # noqa: E402
from util.output import stdErrorExit  # noqa: E402
from util.output import writeStdout  # noqa: E402
from util.output import flushStdout  # noqa: E402
from util.output import writeStderr  # noqa: E402
from util.output import flushStderr  # noqa: E402
from util.output import setSysExitRC  # noqa: E402
from util.output import stderrErrorMsg  # noqa: E402
from util.output import stderrWarningMsg  # noqa: E402
from util.output import systemErrorExit  # noqa: E402
from util.output import printErrorMessage  # noqa: E402
from util.output import printWarningMessage  # noqa: E402
from util.output import supportsColoredText  # noqa: E402
from util.output import createColoredText  # noqa: E402
from util.output import createRedText  # noqa: E402
from util.output import createGreenText  # noqa: E402
from util.output import createYellowText  # noqa: E402
from util.output import executeBatch  # noqa: E402
from util.output import _stripControlCharsFromName  # noqa: E402
from util.output import currentCount  # noqa: E402
from util.output import currentCountNL  # noqa: E402
from util.output import formatKeyValueList  # noqa: E402

# File I/O — extracted to gam.util.fileio
from util.fileio import cleanFilename  # noqa: E402
from util.fileio import setFilePath  # noqa: E402
from util.fileio import uniqueFilename  # noqa: E402
from util.fileio import cleanFilepath  # noqa: E402
from util.fileio import fileErrorMessage  # noqa: E402
from util.fileio import fdErrorMessage  # noqa: E402
from util.fileio import setEncoding  # noqa: E402
from util.fileio import StringIOobject  # noqa: E402
from util.fileio import openFile  # noqa: E402
from util.fileio import closeFile  # noqa: E402
from util.fileio import readFile  # noqa: E402
from util.fileio import writeFile  # noqa: E402
from util.fileio import writeFileReturnError  # noqa: E402
from util.fileio import deleteFile  # noqa: E402
from util.fileio import getGDocSheetDataRetryWarning  # noqa: E402
from util.fileio import getGDocSheetDataFailedExit  # noqa: E402
from util.fileio import incrAPICallsRetryData  # noqa: E402
from util.fileio import initAPICallsRateCheck  # noqa: E402
from util.fileio import checkAPICallsRate  # noqa: E402
from util.fileio import openGAMCommandLog  # noqa: E402
from util.fileio import writeGAMCommandLog  # noqa: E402
from util.fileio import closeGAMCommandLog  # noqa: E402

# Display / warning / action — extracted to gam.util.display
from util.display import badRequestWarning  # noqa: E402
from util.display import emptyQuery  # noqa: E402
from util.display import invalidQuery  # noqa: E402
from util.display import invalidMember  # noqa: E402
from util.display import invalidUserSchema  # noqa: E402
from util.display import userServiceNotEnabledWarning  # noqa: E402
from util.display import userAlertsServiceNotEnabledWarning  # noqa: E402
from util.display import userAnalyticsServiceNotEnabledWarning  # noqa: E402
from util.display import userCalServiceNotEnabledWarning  # noqa: E402
from util.display import userChatServiceNotEnabledWarning  # noqa: E402
from util.display import userContactDelegateServiceNotEnabledWarning  # noqa: E402
from util.display import userDriveServiceNotEnabledWarning  # noqa: E402
from util.display import userKeepServiceNotEnabledWarning  # noqa: E402
from util.display import userGmailServiceNotEnabledWarning  # noqa: E402
from util.display import userLookerStudioServiceNotEnabledWarning  # noqa: E402
from util.display import userPeopleServiceNotEnabledWarning  # noqa: E402
from util.display import userTasksServiceNotEnabledWarning  # noqa: E402
from util.display import userYouTubeServiceNotEnabledWarning  # noqa: E402
from util.display import entityServiceNotApplicableWarning  # noqa: E402
from util.display import entityDoesNotExistWarning  # noqa: E402
from util.display import entityListDoesNotExistWarning  # noqa: E402
from util.display import entityDoesNotHaveItemWarning  # noqa: E402
from util.display import entityDuplicateWarning  # noqa: E402
from util.display import entityActionFailedWarning  # noqa: E402
from util.display import entityModifierItemValueListActionFailedWarning  # noqa: E402
from util.display import entityModifierActionFailedWarning  # noqa: E402
from util.display import entityModifierNewValueActionFailedWarning  # noqa: E402
from util.display import entityNumEntitiesActionFailedWarning  # noqa: E402
from util.display import entityActionNotPerformedWarning  # noqa: E402
from util.display import entityItemValueListActionNotPerformedWarning  # noqa: E402
from util.display import entityModifierItemValueListActionNotPerformedWarning  # noqa: E402
from util.display import entityNumEntitiesActionNotPerformedWarning  # noqa: E402
from util.display import entityBadRequestWarning  # noqa: E402
from util.display import printGettingAllAccountEntities  # noqa: E402
from util.display import printGotAccountEntities  # noqa: E402
from util.display import setGettingAllEntityItemsForWhom  # noqa: E402
from util.display import printGettingAllEntityItemsForWhom  # noqa: E402
from util.display import printGotEntityItemsForWhom  # noqa: E402
from util.display import printGettingEntityItem  # noqa: E402
from util.display import printGettingEntityItemForWhom  # noqa: E402
from util.display import stderrEntityMessage  # noqa: E402
from util.display import FIRST_ITEM_MARKER  # noqa: E402
from util.display import LAST_ITEM_MARKER  # noqa: E402
from util.display import TOTAL_ITEMS_MARKER  # noqa: E402
from util.display import getPageMessage  # noqa: E402
from util.display import getPageMessageForWhom  # noqa: E402
from util.display import printLine  # noqa: E402
from util.display import printBlankLine  # noqa: E402
from util.display import printKeyValueList  # noqa: E402
from util.display import printKeyValueListWithCount  # noqa: E402
from util.display import printKeyValueDict  # noqa: E402
from util.display import printKeyValueWithCRsNLs  # noqa: E402
from util.display import printJSONKey  # noqa: E402
from util.display import printJSONValue  # noqa: E402
from util.display import printEntity  # noqa: E402
from util.display import printEntityMessage  # noqa: E402
from util.display import printEntitiesCount  # noqa: E402
from util.display import printEntityKVList  # noqa: E402
from util.display import performAction  # noqa: E402
from util.display import performActionNumItems  # noqa: E402
from util.display import performActionModifierNumItems  # noqa: E402
from util.display import actionPerformedNumItems  # noqa: E402
from util.display import actionFailedNumItems  # noqa: E402
from util.display import actionNotPerformedNumItemsWarning  # noqa: E402
from util.display import entityPerformAction  # noqa: E402
from util.display import entityPerformActionNumItems  # noqa: E402
from util.display import entityPerformActionModifierNumItems  # noqa: E402
from util.display import entityPerformActionNumItemsModifier  # noqa: E402
from util.display import entityPerformActionSubItemModifierNumItems  # noqa: E402
from util.display import entityPerformActionSubItemModifierNumItemsModifierNewValue  # noqa: E402
from util.display import entityPerformActionModifierNumItemsModifier  # noqa: E402
from util.display import entityPerformActionModifierItemValueList  # noqa: E402
from util.display import entityPerformActionModifierNewValue  # noqa: E402
from util.display import entityPerformActionModifierNewValueItemValueList  # noqa: E402
from util.display import entityPerformActionItemValue  # noqa: E402
from util.display import entityPerformActionInfo  # noqa: E402
from util.display import entityActionPerformed  # noqa: E402
from util.display import entityActionPerformedMessage  # noqa: E402
from util.display import entityNumItemsActionPerformed  # noqa: E402
from util.display import entityModifierActionPerformed  # noqa: E402
from util.display import entityModifierItemValueListActionPerformed  # noqa: E402
from util.display import entityModifierNewValueActionPerformed  # noqa: E402
from util.display import entityModifierNewValueItemValueListActionPerformed  # noqa: E402
from util.display import entityModifierNewValueKeyValueActionPerformed  # noqa: E402

from util.errors import invalidClientSecretsJsonExit  # noqa: E402
from util.errors import invalidOauth2serviceJsonExit  # noqa: E402
from util.errors import invalidOauth2TxtExit  # noqa: E402
from util.errors import expiredRevokedOauth2TxtExit  # noqa: E402
from util.errors import invalidDiscoveryJsonExit  # noqa: E402
from util.errors import entityActionFailedExit  # noqa: E402
from util.errors import entityDoesNotExistExit  # noqa: E402
from util.errors import entityDoesNotHaveItemExit  # noqa: E402
from util.errors import entityIsNotUniqueExit  # noqa: E402
from util.errors import usageErrorExit  # noqa: E402
from util.errors import csvFieldErrorExit  # noqa: E402
from util.errors import csvDataAlreadySavedErrorExit  # noqa: E402
from util.errors import unknownArgumentExit  # noqa: E402
from util.errors import expectedArgumentExit  # noqa: E402
from util.errors import blankArgumentExit  # noqa: E402
from util.errors import emptyArgumentExit  # noqa: E402
from util.errors import invalidArgumentExit  # noqa: E402
from util.errors import missingArgumentExit  # noqa: E402
from util.errors import deprecatedArgument  # noqa: E402
from util.errors import deprecatedArgumentExit  # noqa: E402
from util.errors import deprecatedCommandExit  # noqa: E402
from util.errors import formatChoiceList  # noqa: E402
from util.errors import invalidChoiceExit  # noqa: E402
from util.errors import missingChoiceExit  # noqa: E402

from util.args import *  # noqa: E402,F403 - re-exports ~155 symbols

from util.connection import getLocalGoogleTimeOffset  # noqa: E402
from util.connection import _getServerTLSUsed  # noqa: E402
from util.connection import getOSPlatform  # noqa: E402
from util.connection import inspect_untrusted_cert  # noqa: E402
from util.connection import doCheckConnection  # noqa: E402
from util.connection import doComment  # noqa: E402
from util.connection import doVersion  # noqa: E402
from util.connection import doUsage  # noqa: E402
from util.connection import MACOS_CODENAMES  # noqa: E402

# API transport, service builders, and call wrappers — extracted to gam.util.api
from util.api import handleServerError  # noqa: E402
from util.api import getHttpObj  # noqa: E402
from util.api import _force_user_agent  # noqa: E402
from util.api import transportAgentRequest  # noqa: E402
from util.api import transportAuthorizedHttp  # noqa: E402
from util.api import transportCreateRequest  # noqa: E402
from util.api import doGAMCheckForUpdates  # noqa: E402
from util.api import signjwtJWTCredentials  # noqa: E402
from util.api import signjwtCredentials  # noqa: E402
from util.api import get_adc_request  # noqa: E402
from util.api import signjwtSignJwt  # noqa: E402
from util.api import handleOAuthTokenError  # noqa: E402
from util.api import getOauth2TxtCredentials  # noqa: E402
from util.api import _getValueFromOAuth  # noqa: E402
from util.api import _getAdminEmail  # noqa: E402
from util.api import writeClientCredentials  # noqa: E402
from util.api import shortenURL  # noqa: E402
from util.api import runSqliteQuery  # noqa: E402
from util.api import refreshCredentialsWithReauth  # noqa: E402
from util.api import getClientCredentials  # noqa: E402
from util.api import waitOnFailure  # noqa: E402
from util.api import clearServiceCache  # noqa: E402
from util.api import getAPIService  # noqa: E402
from util.api import getService  # noqa: E402
from util.api import defaultSvcAcctScopes  # noqa: E402
from util.api import _getSvcAcctData  # noqa: E402
from util.api import getSvcAcctCredentials  # noqa: E402
from util.api import getGDataOAuthToken  # noqa: E402
from util.api import checkGDataError  # noqa: E402
from util.api import callGData  # noqa: E402
from util.api import callGDataPages  # noqa: E402
from util.api import checkGAPIError  # noqa: E402
from util.api import callGAPI  # noqa: E402
from util.api import _showGAPIpagesResult  # noqa: E402
from util.api import callGAPIpages  # noqa: E402
from util.api import yieldGAPIpages  # noqa: E402
from util.api import callGAPIitems  # noqa: E402
from util.api import readDiscoveryFile  # noqa: E402
from util.api import buildGAPIObject  # noqa: E402
from util.api import buildGAPIServiceObject  # noqa: E402
from util.api import buildGAPIObjectNoAuthentication  # noqa: E402
from util.api import initGDataObject  # noqa: E402
from util.api import getGDataUserCredentials  # noqa: E402
from util.api import getContactsObject  # noqa: E402
from util.api import getContactsQuery  # noqa: E402
from util.api import getEmailAuditObject  # noqa: E402
from util.api import _processGAPIpagesResult  # noqa: E402
from util.api import _finalizeGAPIpagesResult  # noqa: E402
from util.api import _setMaxArgResults  # noqa: E402
from util.api import writeGotMessage  # noqa: E402
from util.api import getSaUser  # noqa: E402
from util.api import chooseSaAPI  # noqa: E402

# Entity resolution — extracted to gam.util.entity
from util.entity import getUserEmailFromID  # noqa: E402
from util.entity import getGroupEmailFromID  # noqa: E402
from util.entity import getServiceAccountEmailFromID  # noqa: E402
from util.entity import convertUIDtoEmailAddressWithType  # noqa: E402
from util.entity import NON_EMAIL_MEMBER_PREFIXES  # noqa: E402
from util.entity import convertUIDtoEmailAddress  # noqa: E402
from util.entity import convertEmailAddressToUID  # noqa: E402
from util.entity import convertUserIDtoEmail  # noqa: E402
from util.entity import splitEmailAddressOrUID  # noqa: E402
from util.entity import convertOrgUnitIDtoPath  # noqa: E402
from util.entity import shlexSplitList  # noqa: E402
from util.entity import shlexSplitListStatus  # noqa: E402
from util.entity import getQueries  # noqa: E402
from util.entity import _validateDeviceQuery  # noqa: E402
from util.entity import getDeviceQueries  # noqa: E402
from util.entity import convertEntityToList  # noqa: E402
from util.entity import GROUP_ROLES_MAP  # noqa: E402
from util.entity import ALL_GROUP_ROLES  # noqa: E402
from util.entity import _getRoleVerification  # noqa: E402
from util.entity import _getCIRoleVerification  # noqa: E402
from util.entity import _checkMemberStatusIsSuspendedIsArchived  # noqa: E402
from util.entity import _checkMemberIsSuspendedIsArchived  # noqa: E402
from util.entity import _checkMemberRole  # noqa: E402
from util.entity import _checkMemberRoleIsSuspendedIsArchived  # noqa: E402
from util.entity import _checkMemberCategory  # noqa: E402
from util.entity import _checkCIMemberCategory  # noqa: E402
from util.entity import getCIGroupMemberRoleFixType  # noqa: E402
from util.entity import getCIGroupTransitiveMemberRoleFixType  # noqa: E402
from util.entity import convertGroupCloudIDToEmail  # noqa: E402
from util.entity import convertGroupEmailToCloudID  # noqa: E402
from util.entity import CIGROUP_DISCUSSION_FORUM_LABEL  # noqa: E402
from util.entity import CIGROUP_DYNAMIC_LABEL  # noqa: E402
from util.entity import CIGROUP_SECURITY_LABEL  # noqa: E402
from util.entity import CIGROUP_LOCKED_LABEL  # noqa: E402
from util.entity import getCIGroupMembershipGraph  # noqa: E402
from util.entity import checkGroupExists  # noqa: E402
from util.entity import getItemsToModify  # noqa: E402
from util.entity import splitEntityList  # noqa: E402
from util.entity import splitEntityListShlex  # noqa: E402
from util.entity import fileDataErrorExit  # noqa: E402
from util.entity import getEntitiesFromFile  # noqa: E402
from util.entity import getEntitiesFromCSVFile  # noqa: E402
from util.entity import getEntitiesFromCSVbyField  # noqa: E402
from util.entity import mapEntityType  # noqa: E402
from util.entity import getEntityArgument  # noqa: E402
from util.entity import getEntityToModify  # noqa: E402
from util.entity import getEntitySelector  # noqa: E402
from util.entity import getEntitySelection  # noqa: E402
from util.entity import getEntityList  # noqa: E402
from util.entity import getNormalizedEmailAddressEntity  # noqa: E402
from util.entity import getUserObjectEntity  # noqa: E402
from util.entity import _validateUserGetObjectList  # noqa: E402
from util.entity import _validateUserGetMessageIds  # noqa: E402
from util.entity import checkUserExists  # noqa: E402
from util.entity import checkUserSuspended  # noqa: E402

# CSV Print Framework — extracted to gam.util.csv_pf
from util.csv_pf import addFieldToFieldsList  # noqa: E402
from util.csv_pf import _getFieldsList  # noqa: E402
from util.csv_pf import _getRawFields  # noqa: E402
from util.csv_pf import CheckInputRowFilterHeaders  # noqa: E402
from util.csv_pf import RowFilterMatch  # noqa: E402
from util.csv_pf import getFieldsList  # noqa: E402
from util.csv_pf import getFieldsFromFieldsList  # noqa: E402
from util.csv_pf import getItemFieldsFromFieldsList  # noqa: E402
from util.csv_pf import CSVPrintFile  # noqa: E402
from util.csv_pf import writeEntityNoHeaderCSVFile  # noqa: E402
from util.csv_pf import getTodriveOnly  # noqa: E402
from util.csv_pf import DEFAULT_SKIP_OBJECTS  # noqa: E402
from util.csv_pf import cleanJSON  # noqa: E402
from util.csv_pf import flattenJSON  # noqa: E402
from util.csv_pf import showJSON  # noqa: E402
from util.csv_pf import FormatJSONQuoteChar  # noqa: E402
from util.csv_pf import RI_ENTITY  # noqa: E402
from util.csv_pf import RI_I  # noqa: E402
from util.csv_pf import RI_COUNT  # noqa: E402
from util.csv_pf import RI_J  # noqa: E402
from util.csv_pf import RI_JCOUNT  # noqa: E402
from util.csv_pf import RI_ITEM  # noqa: E402
from util.csv_pf import RI_ROLE  # noqa: E402
from util.csv_pf import RI_OPTION  # noqa: E402
from util.csv_pf import batchRequestID  # noqa: E402
# OrgUnit helpers — extracted to gam.util.orgunits
from util.orgunits import getOrgUnitItem  # noqa: E402
from util.orgunits import getTopLevelOrgId  # noqa: E402
from util.orgunits import getOrgUnitId  # noqa: E402
from util.orgunits import getAllParentOrgUnitsForUser  # noqa: E402
# GDoc/GSheet/Storage/CSV readers — extracted to gam.util.gdoc
from util.gdoc import GDOC_FORMAT_MIME_TYPES  # noqa: E402
from util.gdoc import getGDocData  # noqa: E402
from util.gdoc import HTML_TITLE_PATTERN  # noqa: E402
from util.gdoc import getGSheetData  # noqa: E402
from util.gdoc import BUCKET_OBJECT_PATTERNS  # noqa: E402
from util.gdoc import getBucketObjectName  # noqa: E402
from util.gdoc import GCS_FORMAT_MIME_TYPES  # noqa: E402
from util.gdoc import getStorageFileData  # noqa: E402
from util.gdoc import openCSVFileReader  # noqa: E402
# Configuration — extracted to gam.util.config
from util.config import SetGlobalVariables  # noqa: E402
# Batch/multiprocess infrastructure — extracted to gam.util.batch
from util.batch import NullHandler  # noqa: E402
from util.batch import initializeLogging  # noqa: E402
from util.batch import saveNonPickleableValues  # noqa: E402
from util.batch import restoreNonPickleableValues  # noqa: E402
from util.batch import CSVFileQueueHandler  # noqa: E402
from util.batch import initializeCSVFileQueueHandler  # noqa: E402
from util.batch import terminateCSVFileQueueHandler  # noqa: E402
from util.batch import StdQueueHandler  # noqa: E402
from util.batch import initializeStdQueueHandler  # noqa: E402
from util.batch import batchWriteStderr  # noqa: E402
from util.batch import writeStdQueueHandler  # noqa: E402
from util.batch import terminateStdQueueHandler  # noqa: E402
from util.batch import ProcessGAMCommandMulti  # noqa: E402
from util.batch import checkChildProcessRC  # noqa: E402
from util.batch import initGamWorker  # noqa: E402
from util.batch import MultiprocessGAMCommands  # noqa: E402
from util.batch import threadBatchWorker  # noqa: E402
from util.batch import ThreadBatchGAMCommands  # noqa: E402
from util.batch import _getShowCommands  # noqa: E402
from util.batch import _getSkipRows  # noqa: E402
from util.batch import _getMaxRows  # noqa: E402
from util.batch import doBatch  # noqa: E402
from util.batch import doThreadBatch  # noqa: E402
from util.batch import doAutoBatch  # noqa: E402
from util.batch import getSubFields  # noqa: E402
from util.batch import processSubFields  # noqa: E402
from util.batch import doCSV  # noqa: E402
from util.batch import doCSVTest  # noqa: E402
from util.batch import doLoop  # noqa: E402
from util.batch import _doList  # noqa: E402
from util.batch import doListType  # noqa: E402
from util.batch import doListCrOS  # noqa: E402
from util.batch import doListUser  # noqa: E402
from util.batch import _showCount  # noqa: E402
from util.batch import showCountCrOS  # noqa: E402
from util.batch import showCountUser  # noqa: E402

class LazyLoader(types.ModuleType):
  """Lazily import a module, mainly to avoid pulling in large dependencies.

  `contrib`, and `ffmpeg` are examples of modules that are large and not always
  needed, and this allows them to only be loaded when they are used.
  """

  # The lint error here is incorrect.
  def __init__(self, local_name, parent_module_globals, name):
    self._local_name = local_name
    self._parent_module_globals = parent_module_globals

    super().__init__(name)

  def _load(self):
    # Import the target module and insert it into the parent's namespace
    module = importlib.import_module(self.__name__)
    self._parent_module_globals[self._local_name] = module

    # Update this object's dict so that if someone keeps a reference to the
    #   LazyLoader, lookups are efficient (__getattr__ is only called on lookups
    #   that fail).
    self.__dict__.update(module.__dict__)

    return module

  def __getattr__(self, item):
    module = self._load()
    return getattr(module, item)

  def __dir__(self):
    module = self._load()
    return dir(module)

yubikey = LazyLoader('yubikey', globals(), 'gam.gamlib.yubikey')

# gam yubikey resetpvi [yubikey_serialnumber <String>]
def doResetYubiKeyPIV():
  new_data = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'yubikeyserialnumber':
      new_data['yubikey_serial_number'] =  getInteger()
    else:
      unknownArgumentExit()
  yk = yubikey.YubiKey(new_data)
  yk.serial_number = yk.get_serial_number()
  yk.reset_piv()


# Audit command utilities
def ACLRuleDict(rule):
  if rule['scope']['type'] != 'default':
    return {'Scope': f'{rule["scope"]["type"]}:{rule["scope"]["value"]}', 'Role': rule['role']}
  return {'Scope': f'{rule["scope"]["type"]}', 'Role': rule['role']}

def ACLRuleKeyValueList(rule):
  if rule['scope']['type'] != 'default':
    return ['Scope', f'{rule["scope"]["type"]}:{rule["scope"]["value"]}', 'Role', rule['role']]
  return ['Scope', f'{rule["scope"]["type"]}', 'Role', rule['role']]

def formatACLRule(rule):
  return formatKeyValueList('(', ACLRuleKeyValueList(rule), ')')

def formatACLScopeRole(scope, role):
  if role:
    return formatKeyValueList('(', ['Scope', scope, 'Role', role], ')')
  return formatKeyValueList('(', ['Scope', scope], ')')

def normalizeRuleId(ruleId):
  ruleIdParts = ruleId.split(':', 1)
  if (len(ruleIdParts) == 1) or not ruleIdParts[1]:
    if ruleIdParts[0] == 'default':
      return ruleId
    if ruleIdParts[0] == 'domain':
      return f'domain:{GC.Values[GC.DOMAIN]}'
    return f'user:{normalizeEmailAddressOrUID(ruleIdParts[0], noUid=True)}'
  if ruleIdParts[0] in {'user', 'group'}:
    return f'{ruleIdParts[0]}:{normalizeEmailAddressOrUID(ruleIdParts[1], noUid=True)}'
  return ruleId

def makeRoleRuleIdBody(role, ruleId):
  ruleIdParts = ruleId.split(':', 1)
  if len(ruleIdParts) == 1:
    if ruleIdParts[0] == 'default':
      return {'role': role, 'scope': {'type': ruleIdParts[0]}}
    if ruleIdParts[0] == 'domain':
      return {'role': role, 'scope': {'type': ruleIdParts[0], 'value': GC.Values[GC.DOMAIN]}}
    return {'role': role, 'scope': {'type': 'user', 'value': ruleIdParts[0]}}
  return {'role': role, 'scope': {'type': ruleIdParts[0], 'value': ruleIdParts[1]}}

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

CMD_ACTION = 0
CMD_FUNCTION = 1

# Batch commands
BATCH_CSV_COMMANDS = {
  Cmd.BATCH_CMD: 		(Act.PERFORM, doBatch),
  Cmd.CSV_CMD: 			(Act.PERFORM, doCSV),
  Cmd.CSVTEST_CMD: 		(Act.PERFORM, doCSVTest),
  Cmd.TBATCH_CMD: 		(Act.PERFORM, doThreadBatch),
  }

# Main commands
MAIN_COMMANDS = {
  'checkconn':			(Act.CHECK, doCheckConnection),
  'checkconnection':		(Act.CHECK, doCheckConnection),
  'comment':			(Act.COMMENT, doComment),
  'help': 			(Act.PERFORM, doUsage),
  'list': 			(Act.LIST, doListType),
  'report': 			(Act.REPORT, doReport),
  'sendemail': 			(Act.SENDEMAIL, doSendEmail),
  'version': 			(Act.PERFORM, doVersion),
  'whatis': 			(Act.INFO, doWhatIs),
  }

# Main commands with objects
MAIN_ADD_CREATE_FUNCTIONS = {
  Cmd.ARG_ADMIN:		doCreateAdmin,
  Cmd.ARG_ADMINROLE:		doCreateUpdateAdminRoles,
  Cmd.ARG_ALERTFEEDBACK:	doCreateAlertFeedback,
  Cmd.ARG_ALIAS:		doCreateUpdateAliases,
  Cmd.ARG_BROWSERTOKEN:		doCreateBrowserToken,
  Cmd.ARG_BUILDING:		doCreateBuilding,
  Cmd.ARG_CAALEVEL:		doCreateCAALevel,
  Cmd.ARG_CHATMESSAGE:		doCreateChatMessage,
  Cmd.ARG_CHROMENETWORK:	doCreateChromeNetwork,
  Cmd.ARG_CHROMEPOLICYIMAGE:	doCreateChromePolicyImage,
  Cmd.ARG_CHROMEPROFILECOMMAND:	doCreateChromeProfileCommand,
  Cmd.ARG_CIGROUP:		doCreateCIGroup,
  Cmd.ARG_CIPOLICY:		doCreateUpdateCIPolicy,
  Cmd.ARG_CONTACT:		doCreateDomainContact,
  Cmd.ARG_COURSE:		doCreateCourse,
  Cmd.ARG_COURSESTUDENTGROUP:	doCreateCourseStudentGroups,
  Cmd.ARG_COURSESTUDENTGROUPMEMBERS:	doProcessCourseStudentGroupMembers,
  Cmd.ARG_DATATRANSFER:		doCreateDataTransfer,
  Cmd.ARG_DEVICE:		doCreateCIDevice,
  Cmd.ARG_DOMAIN:		doCreateDomain,
  Cmd.ARG_DOMAINALIAS:		doCreateDomainAlias,
  Cmd.ARG_DRIVEFILEACL:		doCreateDriveFileACL,
  Cmd.ARG_DRIVELABELPERMISSION:	doCreateDriveLabelPermissions,
  Cmd.ARG_FEATURE:		doCreateFeature,
  Cmd.ARG_GCPFOLDER:		doCreateGCPFolder,
  Cmd.ARG_GCPSERVICEACCOUNT:	doCreateGCPServiceAccount,
  Cmd.ARG_GROUP:		doCreateGroup,
  Cmd.ARG_GUARDIAN:		doInviteGuardian,
  Cmd.ARG_GUARDIANINVITATION:	doInviteGuardian,
  Cmd.ARG_GUESTUSER:		doCreateGuestUser,
  Cmd.ARG_INBOUNDSSOASSIGNMENT:	doCreateInboundSSOAssignment,
  Cmd.ARG_INBOUNDSSOCREDENTIAL:	doCreateInboundSSOCredential,
  Cmd.ARG_INBOUNDSSOPROFILE:	doCreateInboundSSOProfile,
  Cmd.ARG_ORG:			doCreateOrg,
  Cmd.ARG_PERMISSION:		doCreatePermissions,
  Cmd.ARG_PRINTER:		doCreatePrinter,
  Cmd.ARG_PROJECT:		doCreateProject,
  Cmd.ARG_RESOLDCUSTOMER:	doCreateResoldCustomer,
  Cmd.ARG_RESOLDSUBSCRIPTION:	doCreateResoldSubscription,
  Cmd.ARG_RESOURCE:		doCreateResourceCalendar,
  Cmd.ARG_SAKEY:		doCreateSvcAcctKeys,
  Cmd.ARG_SCHEMA:		doCreateUpdateUserSchemas,
  Cmd.ARG_SHAREDDRIVE:		doCreateSharedDrive,
  Cmd.ARG_SITE:			deprecatedDomainSites,
  Cmd.ARG_SITEACL:		deprecatedDomainSites,
  Cmd.ARG_SVCACCT:		doCreateSvcAcct,
  Cmd.ARG_USER:			doCreateUser,
  Cmd.ARG_VAULTEXPORT:		doCreateVaultExport,
  Cmd.ARG_VAULTHOLD:		doCreateVaultHold,
  Cmd.ARG_VAULTMATTER:		doCreateVaultMatter,
  Cmd.ARG_VAULTQUERY:		doCreateVaultQuery,
  Cmd.ARG_VERIFY:		doCreateSiteVerification,
  }

MAIN_COMMANDS_WITH_OBJECTS = {
  'add':
    (Act.ADD,
     MAIN_ADD_CREATE_FUNCTIONS
    ),
  'approve':
    (Act.APPROVE,
     {Cmd.ARG_DEVICEUSER:	doApproveCIDeviceUser,
     }
    ),
  'block':
    (Act.BLOCK,
     {Cmd.ARG_DEVICEUSER:	doBlockCIDeviceUser,
     }
    ),
  'cancel':
    (Act.CANCEL,
     {Cmd.ARG_GUARDIANINVITATION:	doCancelGuardianInvitation,
      Cmd.ARG_USERINVITATION:	doCIUserInvitationsAction,
     }
    ),
  'cancelwipe':
    (Act.CANCEL_WIPE,
     {Cmd.ARG_DEVICE:		doCancelWipeCIDevice,
      Cmd.ARG_DEVICEUSER:	doCancelWipeCIDeviceUser,
     }
    ),
  'check':
    (Act.CHECK,
     {Cmd.ARG_SVCACCT:		doCheckUpdateSvcAcct,
      Cmd.ARG_USERINVITATION:	doCheckCIUserInvitations,
      Cmd.ARG_ISINVITABLE:	doCheckCIUserInvitations,
      Cmd.ARG_ORG:		doCheckOrgUnit,
      Cmd.ARG_SUSPENDED:	doCheckUserSuspended,
     }
    ),
  'clear':
    (Act.CLEAR,
     {Cmd.ARG_ALERTSETTINGS:	doClearAlertSettings,
      Cmd.ARG_CONTACT:		doClearDomainContacts,
      Cmd.ARG_COURSESTUDENTGROUP:	doClearCourseStudentGroups,
      Cmd.ARG_COURSESTUDENTGROUPMEMBERS:	doProcessCourseStudentGroupMembers,
     }
    ),
  'close':
    (Act.CLOSE,
     {Cmd.ARG_VAULTMATTER:	doCloseVaultMatter,
     }
    ),
  'copy':
    (Act.COPY,
     {Cmd.ARG_SHAREDDRIVEACLS:	doCopySyncSharedDriveACLs,
      Cmd.ARG_STORAGEBUCKET:	doCopyCloudStorageBucket,
      Cmd.ARG_VAULTEXPORT:	doCopyVaultExport,
      Cmd.ARG_VAULTQUERY:	doCopyVaultQuery,
     }
    ),
  'create':
    (Act.CREATE,
     MAIN_ADD_CREATE_FUNCTIONS
    ),
  'dedup':
    (Act.DEDUP,
     {Cmd.ARG_CONTACT:		doDedupDomainContacts,
     }
    ),
  'delete':
    (Act.DELETE,
     {Cmd.ARG_ADMIN:		doDeleteAdmin,
      Cmd.ARG_ADMINROLE:	doDeleteAdminRole,
      Cmd.ARG_ALIAS:		doDeleteAliases,
      Cmd.ARG_ALERT:		doDeleteOrUndeleteAlert,
      Cmd.ARG_BROWSER:		doDeleteBrowsers,
      Cmd.ARG_BUILDING:		doDeleteBuilding,
      Cmd.ARG_CAALEVEL:		doDeleteCAALevel,
      Cmd.ARG_CHATMESSAGE:	doDeleteChatMessage,
      Cmd.ARG_CHROMENETWORK:	doDeleteChromeNetwork,
      Cmd.ARG_CHROMEPOLICY:	doDeleteChromePolicy,
      Cmd.ARG_CHROMEPROFILE:	doDeleteChromeProfile,
      Cmd.ARG_CIGROUP:		doDeleteCIGroups,
      Cmd.ARG_CIPOLICY:		doDeleteCIPolicies,
      Cmd.ARG_CLASSROOMINVITATION:	doDeleteClassroomInvitations,
      Cmd.ARG_CONTACT:		doDeleteDomainContacts,
      Cmd.ARG_CONTACTPHOTO:	doDeleteDomainContactPhoto,
      Cmd.ARG_COURSE:		doDeleteCourse,
      Cmd.ARG_COURSES:		doDeleteCourses,
      Cmd.ARG_COURSESTUDENTGROUP:	doDeleteCourseStudentGroups,
      Cmd.ARG_COURSESTUDENTGROUPMEMBERS:	doProcessCourseStudentGroupMembers,
      Cmd.ARG_DEVICE:		doDeleteCIDevice,
      Cmd.ARG_DEVICEUSER:	doDeleteCIDeviceUser,
      Cmd.ARG_DOMAIN:		doDeleteDomain,
      Cmd.ARG_DOMAINALIAS:	doDeleteDomainAlias,
      Cmd.ARG_DOMAINCONTACT:	doDeleteDomainContacts,
      Cmd.ARG_DRIVEFILEACL:	doDeleteDriveFileACLs,
      Cmd.ARG_DRIVELABELPERMISSION:	doDeleteDriveLabelPermissions,
      Cmd.ARG_FEATURE:		doDeleteFeature,
      Cmd.ARG_GROUP:		doDeleteGroups,
      Cmd.ARG_GUARDIAN:		doDeleteGuardian,
      Cmd.ARG_INBOUNDSSOASSIGNMENT:	doDeleteInboundSSOAssignment,
      Cmd.ARG_INBOUNDSSOCREDENTIAL:	doDeleteInboundSSOCredential,
      Cmd.ARG_INBOUNDSSOPROFILE:	doDeleteInboundSSOProfile,
      Cmd.ARG_MOBILE:		doDeleteMobileDevices,
      Cmd.ARG_ORG:		doDeleteOrg,
      Cmd.ARG_ORGS:		doDeleteOrgs,
      Cmd.ARG_PERMISSION:	doDeletePermissions,
      Cmd.ARG_PRINTER:		doDeletePrinter,
      Cmd.ARG_PROJECT:		doDeleteProject,
      Cmd.ARG_RESOLDSUBSCRIPTION:	doDeleteResoldSubscription,
      Cmd.ARG_RESOURCE:		doDeleteResourceCalendar,
      Cmd.ARG_RESOURCES:	doDeleteResourceCalendars,
      Cmd.ARG_SAKEY:		doDeleteSvcAcctKeys,
      Cmd.ARG_SCHEMA:		doDeleteUserSchemas,
      Cmd.ARG_SHAREDDRIVE:	doDeleteSharedDrive,
      Cmd.ARG_SITEACL:		deprecatedDomainSites,
      Cmd.ARG_SVCACCT:		doDeleteSvcAcct,
      Cmd.ARG_USER:		doDeleteUser,
      Cmd.ARG_USERS:		doDeleteUsers,
      Cmd.ARG_VAULTEXPORT:	doDeleteVaultExport,
      Cmd.ARG_VAULTHOLD:	doDeleteVaultHold,
      Cmd.ARG_VAULTMATTER:	doDeleteVaultMatter,
      Cmd.ARG_VAULTQUERY:	doDeleteVaultQuery,
     }
    ),
  'download':
    (Act.DOWNLOAD,
     {Cmd.ARG_STORAGEBUCKET:	doDownloadCloudStorageBucket,
      Cmd.ARG_STORAGEFILE:	doDownloadCloudStorageFile,
      Cmd.ARG_VAULTEXPORT:	doDownloadVaultExport,
     }
    ),
  'enable':
    (Act.ENABLE,
     {Cmd.ARG_API:		doEnableAPIs,
     }
    ),
  'get':
    (Act.DOWNLOAD,
     {Cmd.ARG_CONTACTPHOTO:	doGetDomainContactPhoto,
      Cmd.ARG_DEVICEFILE:	doGetCrOSDeviceFiles,
     }
    ),
  'getcommand':
    (Act.GET_COMMAND_RESULT,
     {Cmd.ARG_CROS:		doGetCommandResultCrOSDevices,
     }
    ),
  'hide':
    (Act.HIDE,
     {Cmd.ARG_SHAREDDRIVE:	doHideUnhideSharedDrive,
     }
    ),
  'info':
    (Act.INFO,
     {Cmd.ARG_ADMINROLE:	doInfoPrintShowAdminRoles,
      Cmd.ARG_ALERT:		doInfoAlert,
      Cmd.ARG_ALIAS:		doInfoAliases,
      Cmd.ARG_BUILDING:		doInfoBuilding,
      Cmd.ARG_BROWSER:		doInfoBrowsers,
      Cmd.ARG_CHATEVENT:	doInfoChatEvent,
      Cmd.ARG_CHATMEMBER:	doInfoChatMember,
      Cmd.ARG_CHATMESSAGE:	doInfoChatMessage,
      Cmd.ARG_CHATSPACE:	doInfoChatSpace,
      Cmd.ARG_CHROMEAPP:	doInfoChromeApp,
      Cmd.ARG_CHROMEPROFILE:	doInfoChromeProfile,
      Cmd.ARG_CHROMEPROFILECOMMAND:	doInfoChromeProfileCommand,
      Cmd.ARG_CHROMESCHEMA:	doInfoChromePolicySchemas,
      Cmd.ARG_CIGROUP:		doInfoCIGroups,
      Cmd.ARG_CIGROUPMEMBERS:	doInfoCIGroupMembers,
      Cmd.ARG_CIPOLICY:		doInfoCIPolicies,
      Cmd.ARG_CONTACT:		doInfoDomainContacts,
      Cmd.ARG_COURSE:		doInfoCourse,
      Cmd.ARG_COURSES:		doInfoCourses,
      Cmd.ARG_CROS:		doInfoCrOSDevices,
      Cmd.ARG_CROSTELEMETRY:	doInfoPrintShowCrOSTelemetry,
      Cmd.ARG_CURRENTPROJECTID:	doInfoCurrentProjectId,
      Cmd.ARG_CUSTOMER:		doInfoCustomer,
      Cmd.ARG_CUSTOMERID:	doInfoCustomerId,
      Cmd.ARG_DATATRANSFER:	doInfoDataTransfer,
      Cmd.ARG_DEVICE:		doInfoCIDevice,
      Cmd.ARG_DEVICEUSER:	doInfoCIDeviceUser,
      Cmd.ARG_DEVICEUSERSTATE:	doInfoCIDeviceUserState,
      Cmd.ARG_DOMAIN:		doInfoDomain,
      Cmd.ARG_DOMAINALIAS:	doInfoDomainAlias,
      Cmd.ARG_DOMAINCONTACT:	doInfoDomainContacts,
      Cmd.ARG_DRIVEFILEACL:	doInfoDriveFileACLs,
      Cmd.ARG_DRIVELABEL:	doInfoDriveLabels,
      Cmd.ARG_INSTANCE:		doInfoInstance,
      Cmd.ARG_GCPORGID:		doInfoGCPOrgId,
      Cmd.ARG_GROUP:		doInfoGroups,
      Cmd.ARG_GROUPMEMBERS:	doInfoGroupMembers,
      Cmd.ARG_INBOUNDSSOASSIGNMENT:	doInfoInboundSSOAssignment,
      Cmd.ARG_INBOUNDSSOCREDENTIAL:	doInfoInboundSSOCredential,
      Cmd.ARG_INBOUNDSSOPROFILE:	doInfoInboundSSOProfile,
      Cmd.ARG_MOBILE:		doInfoMobileDevices,
      Cmd.ARG_ORG:		doInfoOrg,
      Cmd.ARG_ORGS:		doInfoOrgs,
      Cmd.ARG_PEOPLEPROFILE:	doInfoDomainPeopleProfile,
      Cmd.ARG_PEOPLECONTACT:	doInfoDomainPeopleContacts,
      Cmd.ARG_PRINTER:		doInfoPrinter,
      Cmd.ARG_RESOLDCUSTOMER:	doInfoResoldCustomer,
      Cmd.ARG_RESOLDSUBSCRIPTION:	doInfoResoldSubscription,
      Cmd.ARG_RESOURCE:		doInfoResourceCalendar,
      Cmd.ARG_RESOURCES:	doInfoResourceCalendars,
      Cmd.ARG_SCHEMA:		doInfoUserSchemas,
      Cmd.ARG_SHAREDDRIVE:	doInfoSharedDrive,
      Cmd.ARG_SITE:		deprecatedDomainSites,
      Cmd.ARG_SITEACL:		deprecatedDomainSites,
      Cmd.ARG_USER:		doInfoUser,
      Cmd.ARG_USERS:		doInfoUsers,
      Cmd.ARG_USERINVITATION:	doInfoCIUserInvitations,
      Cmd.ARG_VAULTEXPORT:	doInfoVaultExport,
      Cmd.ARG_VAULTHOLD:	doInfoVaultHold,
      Cmd.ARG_VAULTMATTER:	doInfoVaultMatter,
      Cmd.ARG_VAULTQUERY:	doInfoVaultQuery,
      Cmd.ARG_VERIFY:		doInfoSiteVerification,
     }
    ),
  'issuecommand':
    (Act.ISSUE_COMMAND,
     {Cmd.ARG_CROS:		doIssueCommandCrOSDevices,
     }
    ),
  'move':
    (Act.MOVE,
     {Cmd.ARG_BROWSER:		doMoveBrowsers,
     }
    ),
  'print':
    (Act.PRINT,
     {Cmd.ARG_ADDRESSES:	doPrintAddresses,
      Cmd.ARG_ADMINROLE:	doInfoPrintShowAdminRoles,
      Cmd.ARG_ADMIN:		doPrintShowAdmins,
      Cmd.ARG_ALERT:		doPrintShowAlerts,
      Cmd.ARG_ALERTFEEDBACK:	doPrintShowAlertFeedback,
      Cmd.ARG_ALIAS:		doPrintAliases,
      Cmd.ARG_BROWSER:		doPrintShowBrowsers,
      Cmd.ARG_BROWSERTOKEN:	doPrintShowBrowserTokens,
      Cmd.ARG_BUILDING:		doPrintShowBuildings,
      Cmd.ARG_CAALEVEL:		doPrintShowCAALevels,
      Cmd.ARG_CHANNELCUSTOMER:	doPrintShowChannelCustomers,
      Cmd.ARG_CHANNELCUSTOMERENTITLEMENT:	doPrintShowChannelCustomerEntitlements,
      Cmd.ARG_CHANNELOFFER:	doPrintShowChannelOffers,
      Cmd.ARG_CHANNELPRODUCT:	doPrintShowChannelProducts,
      Cmd.ARG_CHANNELSKU:	doPrintShowChannelSKUs,
      Cmd.ARG_CHATMEMBER:	doPrintShowChatMembers,
      Cmd.ARG_CHATSPACE:	doPrintShowChatSpaces,
      Cmd.ARG_CHROMEAPP:	doPrintShowChromeApps,
      Cmd.ARG_CHROMEAPPDEVICES:	doPrintShowChromeAppDevices,
      Cmd.ARG_CHROMEAUES:	doPrintShowChromeAues,
      Cmd.ARG_CHROMEDEVICECOUNTS:	doPrintShowChromeDeviceCounts,
      Cmd.ARG_CHROMEHISTORY:	doPrintShowChromeHistory,
      Cmd.ARG_CHROMENEEDSATTN:	doPrintShowChromeNeedsAttn,
      Cmd.ARG_CHROMEPOLICY:	doPrintShowChromePolicies,
      Cmd.ARG_CHROMEPROFILE:	doPrintShowChromeProfiles,
      Cmd.ARG_CHROMEPROFILECOMMAND:	doPrintShowChromeProfileCommands,
      Cmd.ARG_CHROMESCHEMA:	doPrintShowChromePolicySchemas,
      Cmd.ARG_CHROMESNVALIDITY:	doPrintChromeSnValidity,
      Cmd.ARG_CHROMEVERSIONS:	doPrintShowChromeVersions,
      Cmd.ARG_CIGROUP:		doPrintCIGroups,
      Cmd.ARG_CIGROUPMEMBERS:	doPrintCIGroupMembers,
      Cmd.ARG_CIPOLICY:		doPrintShowCIPolicies,
      Cmd.ARG_CLASSROOMINVITATION:	doPrintShowClassroomInvitations,
      Cmd.ARG_CONTACT:		doPrintShowDomainContacts,
      Cmd.ARG_COURSE:		doPrintCourses,
      Cmd.ARG_COURSES:		doPrintCourses,
      Cmd.ARG_COURSEANNOUNCEMENTS:	doPrintCourseAnnouncements,
      Cmd.ARG_COURSECOUNTS:	doPrintCourseCounts,
      Cmd.ARG_COURSEMATERIALS:	doPrintCourseMaterials,
      Cmd.ARG_COURSEPARTICIPANTS:	doPrintCourseParticipants,
      Cmd.ARG_COURSESTUDENTGROUP:	doPrintCourseStudentGroups,
      Cmd.ARG_COURSESTUDENTGROUPMEMBERS:	doPrintCourseStudentGroupMembers,
      Cmd.ARG_COURSESUBMISSIONS:	doPrintCourseSubmissions,
      Cmd.ARG_COURSETOPICS:	doPrintCourseTopics,
      Cmd.ARG_COURSEWORK:	doPrintCourseWork,
      Cmd.ARG_CROS:		doPrintCrOSDevices,
      Cmd.ARG_CROSACTIVITY:	doPrintCrOSActivity,
      Cmd.ARG_CROSTELEMETRY:	doInfoPrintShowCrOSTelemetry,
      Cmd.ARG_DATATRANSFER:	doPrintShowDataTransfers,
      Cmd.ARG_DEVICE:		doPrintCIDevices,
      Cmd.ARG_DEVICEUSER:	doPrintCIDeviceUsers,
      Cmd.ARG_DOMAIN:		doPrintShowDomains,
      Cmd.ARG_DOMAINALIAS:	doPrintShowDomainAliases,
      Cmd.ARG_DOMAINCONTACT:	doPrintShowDomainContacts,
      Cmd.ARG_DRIVEFILEACL:	doPrintShowDriveFileACLs,
      Cmd.ARG_DRIVELABEL:	doPrintShowDriveLabels,
      Cmd.ARG_DRIVELABELPERMISSION:	doPrintShowDriveLabelPermissions,
      Cmd.ARG_FEATURE:		doPrintShowFeatures,
      Cmd.ARG_GROUP:		doPrintGroups,
      Cmd.ARG_GROUPMEMBERS:	doPrintGroupMembers,
      Cmd.ARG_GROUPTREE:	doPrintShowGroupTree,
      Cmd.ARG_GUARDIAN:		doPrintShowGuardians,
      Cmd.ARG_INBOUNDSSOASSIGNMENT:	doPrintShowInboundSSOAssignments,
      Cmd.ARG_INBOUNDSSOCREDENTIAL:	doPrintShowInboundSSOCredentials,
      Cmd.ARG_INBOUNDSSOPROFILE:	doPrintShowInboundSSOProfiles,
      Cmd.ARG_LICENSE:		doPrintLicenses,
      Cmd.ARG_MOBILE:		doPrintMobileDevices,
      Cmd.ARG_ORG:		doPrintOrgs,
      Cmd.ARG_ORGS:		doPrintOrgs,
      Cmd.ARG_ORGUNITSHAREDDRIVE:	doPrintShowOrgunitSharedDrives,
      Cmd.ARG_OWNERSHIP:	doPrintShowOwnership,
      Cmd.ARG_PEOPLECONTACT:	doPrintShowDomainPeopleContacts,
      Cmd.ARG_PEOPLEPROFILE:	doPrintShowDomainPeopleProfiles,
      Cmd.ARG_PRINTER:		doPrintShowPrinters,
      Cmd.ARG_PRINTERMODEL:	doPrintShowPrinterModels,
      Cmd.ARG_PRIVILEGES:	doPrintShowPrivileges,
      Cmd.ARG_PROJECT:		doPrintShowProjects,
      Cmd.ARG_RESOLDSUBSCRIPTION:	doPrintShowResoldSubscriptions,
      Cmd.ARG_RESOURCE:		doPrintShowResourceCalendars,
      Cmd.ARG_RESOURCES:	doPrintShowResourceCalendars,
      Cmd.ARG_SCHEMA:		doPrintShowUserSchemas,
      Cmd.ARG_SHAREDDRIVE:	doPrintShowSharedDrives,
      Cmd.ARG_SHAREDDRIVEACLS:	doPrintShowSharedDriveACLs,
      Cmd.ARG_SHAREDDRIVEORGANIZERS:	doPrintSharedDriveOrganizers,
      Cmd.ARG_SITE:		deprecatedDomainSites,
      Cmd.ARG_SITEACL:		deprecatedDomainSites,
      Cmd.ARG_SITEACTIVITY:	deprecatedDomainSites,
      Cmd.ARG_SVCACCT:		doPrintShowSvcAccts,
      Cmd.ARG_TOKEN:		doPrintShowTokens,
      Cmd.ARG_TRANSFERAPPS:	doShowTransferApps,
      Cmd.ARG_USER:		doPrintUsers,
      Cmd.ARG_USERS:		doPrintUsers,
      Cmd.ARG_USERCOUNTSBYORGUNIT:	doPrintUserCountsByOrgUnit,
      Cmd.ARG_USERINVITATION:	doPrintShowCIUserInvitations,
      Cmd.ARG_VAULTCOUNT:	doPrintVaultCounts,
      Cmd.ARG_VAULTEXPORT:	doPrintShowVaultExports,
      Cmd.ARG_VAULTHOLD:	doPrintShowVaultHolds,
      Cmd.ARG_VAULTMATTER:	doPrintShowVaultMatters,
      Cmd.ARG_VAULTQUERY:	doPrintShowVaultQueries,
     }
    ),
  'remove':
    (Act.REMOVE,
     {Cmd.ARG_ALIAS:		doRemoveAliases,
      Cmd.ARG_DRIVELABELPERMISSION:	doDeleteDriveLabelPermissions,
     }
    ),
  'reopen':
    (Act.REOPEN,
     {Cmd.ARG_VAULTMATTER:	doReopenVaultMatter,
     }
    ),
  'replace':
    (Act.UPDATE,
     {Cmd.ARG_SAKEY:		doReplaceSvcAcctKeys,
     }
    ),
  'rotate':
    (Act.UPDATE,
     {Cmd.ARG_SAKEY:		doProcessSvcAcctKeys,
     }
    ),
  'revoke':
    (Act.REVOKE,
     {Cmd.ARG_BROWSERTOKEN:	doRevokeBrowserToken,
     }
    ),
  'send':
    (Act.SEND,
     {Cmd.ARG_USERINVITATION:	doCIUserInvitationsAction,
     }
    ),
  'setup':
    (Act.SETUP,
     {Cmd.ARG_CHAT:		doSetupChat,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_ADMINROLE:	doInfoPrintShowAdminRoles,
      Cmd.ARG_ADMIN:		doPrintShowAdmins,
      Cmd.ARG_ALERT:		doPrintShowAlerts,
      Cmd.ARG_ALERTFEEDBACK:	doPrintShowAlertFeedback,
      Cmd.ARG_ALERTSETTINGS:	doShowAlertSettings,
      Cmd.ARG_BROWSER:		doPrintShowBrowsers,
      Cmd.ARG_BROWSERTOKEN:	doPrintShowBrowserTokens,
      Cmd.ARG_BUILDING:		doPrintShowBuildings,
      Cmd.ARG_CAALEVEL:		doPrintShowCAALevels,
      Cmd.ARG_CHANNELCUSTOMER:	doPrintShowChannelCustomers,
      Cmd.ARG_CHANNELCUSTOMERENTITLEMENT:	doPrintShowChannelCustomerEntitlements,
      Cmd.ARG_CHANNELOFFER:	doPrintShowChannelOffers,
      Cmd.ARG_CHANNELPRODUCT:	doPrintShowChannelProducts,
      Cmd.ARG_CHANNELSKU:	doPrintShowChannelSKUs,
      Cmd.ARG_CHATMEMBER:	doPrintShowChatMembers,
      Cmd.ARG_CHATSPACE:	doPrintShowChatSpaces,
      Cmd.ARG_CHROMEAPP:	doPrintShowChromeApps,
      Cmd.ARG_CHROMEAPPDEVICES:	doPrintShowChromeAppDevices,
      Cmd.ARG_CHROMEAUES:	doPrintShowChromeAues,
      Cmd.ARG_CHROMEDEVICECOUNTS:	doPrintShowChromeDeviceCounts,
      Cmd.ARG_CHROMEHISTORY:	doPrintShowChromeHistory,
      Cmd.ARG_CHROMENEEDSATTN:	doPrintShowChromeNeedsAttn,
      Cmd.ARG_CHROMEPOLICY:	doPrintShowChromePolicies,
      Cmd.ARG_CHROMEPROFILE:	doPrintShowChromeProfiles,
      Cmd.ARG_CHROMEPROFILECOMMAND:	doPrintShowChromeProfileCommands,
      Cmd.ARG_CHROMESCHEMA:	doPrintShowChromePolicySchemas,
      Cmd.ARG_CHROMEVERSIONS:	doPrintShowChromeVersions,
      Cmd.ARG_CIGROUPMEMBERS:	doShowCIGroupMembers,
      Cmd.ARG_CIPOLICY:		doPrintShowCIPolicies,
      Cmd.ARG_CLASSROOMINVITATION:	doPrintShowClassroomInvitations,
      Cmd.ARG_CONTACT:		doPrintShowDomainContacts,
      Cmd.ARG_CROSTELEMETRY:	doInfoPrintShowCrOSTelemetry,
      Cmd.ARG_DATATRANSFER:	doPrintShowDataTransfers,
      Cmd.ARG_DOMAIN:		doPrintShowDomains,
      Cmd.ARG_DOMAINALIAS:	doPrintShowDomainAliases,
      Cmd.ARG_DOMAINCONTACT:	doPrintShowDomainContacts,
      Cmd.ARG_DRIVEFILEACL:	doPrintShowDriveFileACLs,
      Cmd.ARG_DRIVELABEL:	doPrintShowDriveLabels,
      Cmd.ARG_DRIVELABELPERMISSION:	doPrintShowDriveLabelPermissions,
      Cmd.ARG_FEATURE:		doPrintShowFeatures,
      Cmd.ARG_GROUPMEMBERS:	doShowGroupMembers,
      Cmd.ARG_GROUPTREE:	doPrintShowGroupTree,
      Cmd.ARG_GUARDIAN:		doPrintShowGuardians,
      Cmd.ARG_INBOUNDSSOASSIGNMENT:	doPrintShowInboundSSOAssignments,
      Cmd.ARG_INBOUNDSSOCREDENTIAL:	doPrintShowInboundSSOCredentials,
      Cmd.ARG_INBOUNDSSOPROFILE:	doPrintShowInboundSSOProfiles,
      Cmd.ARG_ORGUNITSHAREDDRIVE:	doPrintShowOrgunitSharedDrives,
      Cmd.ARG_LICENSE:		doShowLicenses,
      Cmd.ARG_ORGTREE:		doShowOrgTree,
      Cmd.ARG_OWNERSHIP:	doPrintShowOwnership,
      Cmd.ARG_PEOPLECONTACT:	doPrintShowDomainPeopleContacts,
      Cmd.ARG_PEOPLEPROFILE:	doPrintShowDomainPeopleProfiles,
      Cmd.ARG_PRINTER:		doPrintShowPrinters,
      Cmd.ARG_PRINTERMODEL:	doPrintShowPrinterModels,
      Cmd.ARG_PRIVILEGES:	doPrintShowPrivileges,
      Cmd.ARG_PROJECT:		doPrintShowProjects,
      Cmd.ARG_RESOLDSUBSCRIPTION:	doPrintShowResoldSubscriptions,
      Cmd.ARG_RESOURCE:		doPrintShowResourceCalendars,
      Cmd.ARG_RESOURCES:	doPrintShowResourceCalendars,
      Cmd.ARG_SAKEY:		doShowSvcAcctKeys,
      Cmd.ARG_SCHEMA:		doPrintShowUserSchemas,
      Cmd.ARG_SHAREDDRIVE:	doPrintShowSharedDrives,
      Cmd.ARG_SHAREDDRIVEACLS:	doPrintShowSharedDriveACLs,
      Cmd.ARG_SHAREDDRIVEINFO:	doInfoSharedDrive,
      Cmd.ARG_SHAREDDRIVETHEMES:	doShowSharedDriveThemes,
      Cmd.ARG_SITE:		deprecatedDomainSites,
      Cmd.ARG_SITEACL:		deprecatedDomainSites,
      Cmd.ARG_SVCACCT:		doPrintShowSvcAccts,
      Cmd.ARG_TOKEN:		doPrintShowTokens,
      Cmd.ARG_TRANSFERAPPS:	doShowTransferApps,
      Cmd.ARG_USERINVITATION:	doPrintShowCIUserInvitations,
      Cmd.ARG_VAULTEXPORT:	doPrintShowVaultExports,
      Cmd.ARG_VAULTHOLD:	doPrintShowVaultHolds,
      Cmd.ARG_VAULTMATTER:	doPrintShowVaultMatters,
      Cmd.ARG_VAULTQUERY:	doPrintShowVaultQueries,
     }
    ),
  'suspend':
    (Act.SUSPEND,
     {Cmd.ARG_USER:		doSuspendUnsuspendUser,
      Cmd.ARG_USERS:		doSuspendUnsuspendUsers,
     }
    ),
  'sync':
    (Act.SYNC,
     {Cmd.ARG_DEVICE:		doSyncCIDevices,
      Cmd.ARG_SHAREDDRIVEACLS:	copySyncSharedDriveACLs,
      Cmd.ARG_COURSESTUDENTGROUPMEMBERS:	doProcessCourseStudentGroupMembers,
     }
    ),
  'unhide':
    (Act.UNHIDE,
     {Cmd.ARG_SHAREDDRIVE:	doHideUnhideSharedDrive,
     }
    ),
  'update':
    (Act.UPDATE,
     {Cmd.ARG_ADMINROLE:	doCreateUpdateAdminRoles,
      Cmd.ARG_ALERTSETTINGS:	doUpdateAlertSettings,
      Cmd.ARG_ALIAS:		doCreateUpdateAliases,
      Cmd.ARG_BROWSER:		doUpdateBrowsers,
      Cmd.ARG_BUILDING:		doUpdateBuilding,
      Cmd.ARG_CAALEVEL:		doUpdateCAALevel,
      Cmd.ARG_CHATMESSAGE:	doUpdateChatMessage,
      Cmd.ARG_CHROMEPOLICY:	doUpdateChromePolicy,
      Cmd.ARG_CIGROUP:		doUpdateCIGroups,
      Cmd.ARG_CIPOLICY:		doCreateUpdateCIPolicy,
      Cmd.ARG_CONTACT:		doUpdateDomainContacts,
      Cmd.ARG_CONTACTPHOTO:	doUpdateDomainContactPhoto,
      Cmd.ARG_COURSE:		doUpdateCourse,
      Cmd.ARG_COURSES:		doUpdateCourses,
      Cmd.ARG_COURSESTUDENTGROUP:	doUpdateCourseStudentGroups,
      Cmd.ARG_CROS:		doUpdateCrOSDevices,
      Cmd.ARG_CUSTOMER:		doUpdateCustomer,
      Cmd.ARG_DEVICE:		doUpdateCIDevice,
      Cmd.ARG_DEVICEUSER:	doUpdateCIDeviceUser,
      Cmd.ARG_DEVICEUSERSTATE:	doUpdateCIDeviceUserState,
      Cmd.ARG_DOMAIN:		doUpdateDomain,
      Cmd.ARG_DRIVEFILEACL:	doUpdateDriveFileACLs,
      Cmd.ARG_FEATURE:		doUpdateFeature,
      Cmd.ARG_GROUP:		doUpdateGroups,
      Cmd.ARG_INBOUNDSSOASSIGNMENT:	doUpdateInboundSSOAssignment,
      Cmd.ARG_INBOUNDSSOPROFILE:	doUpdateInboundSSOProfile,
      Cmd.ARG_MOBILE:		doUpdateMobileDevices,
      Cmd.ARG_ORG:		doUpdateOrg,
      Cmd.ARG_ORGS:		doUpdateOrgs,
      Cmd.ARG_PRINTER:		doUpdatePrinter,
      Cmd.ARG_PROJECT:		doUpdateProject,
      Cmd.ARG_RESOLDCUSTOMER:	doUpdateResoldCustomer,
      Cmd.ARG_RESOLDSUBSCRIPTION:	doUpdateResoldSubscription,
      Cmd.ARG_RESOURCE:		doUpdateResourceCalendar,
      Cmd.ARG_RESOURCES:	doUpdateResourceCalendars,
      Cmd.ARG_SAKEY:		doUpdateSvcAcctKeys,
      Cmd.ARG_SCHEMA:		doCreateUpdateUserSchemas,
      Cmd.ARG_SHAREDDRIVE:	doUpdateSharedDrive,
      Cmd.ARG_SITE:		deprecatedDomainSites,
      Cmd.ARG_SITEACL:		deprecatedDomainSites,
      Cmd.ARG_SVCACCT:		doCheckUpdateSvcAcct,
      Cmd.ARG_USER:		doUpdateUser,
      Cmd.ARG_USERS:		doUpdateUsers,
      Cmd.ARG_VAULTHOLD:	doUpdateVaultHold,
      Cmd.ARG_VAULTMATTER:	doUpdateVaultMatter,
      Cmd.ARG_VERIFY:		doUpdateSiteVerification,
     }
    ),
  'undelete':
    (Act.UNDELETE,
     {Cmd.ARG_ALERT:		doDeleteOrUndeleteAlert,
      Cmd.ARG_USER:		doUndeleteUser,
      Cmd.ARG_USERS:		doUndeleteUsers,
      Cmd.ARG_VAULTMATTER:	doUndeleteVaultMatter,
     }
    ),
  'unsuspend':
    (Act.UNSUSPEND,
     {Cmd.ARG_USER:		doSuspendUnsuspendUser,
      Cmd.ARG_USERS:		doSuspendUnsuspendUsers,
     }
    ),
  'upload':
    (Act.USE,
     {Cmd.ARG_SAKEY:		doUploadSvcAcctKeys,
     }
    ),
  'use':
    (Act.USE,
     {Cmd.ARG_PROJECT:		doUseProject,
     }
    ),
  'wipe':
    (Act.WIPE,
     {Cmd.ARG_DEVICE:		doWipeCIDevice,
      Cmd.ARG_DEVICEUSER:	doWipeCIDeviceUser,
     }
    ),
  'yubikey':
    (Act.RESET_YUBIKEY_PIV,
     {Cmd.ARG_RESETPIV:		doResetYubiKeyPIV,
     }
    ),
  }

MAIN_COMMANDS_OBJ_ALIASES = {
  Cmd.ARG_ADMINS:		Cmd.ARG_ADMIN,
  Cmd.ARG_ADMINROLES:		Cmd.ARG_ADMINROLE,
  Cmd.ARG_ALERTFEEDBACKS:	Cmd.ARG_ALERTFEEDBACK,
  Cmd.ARG_ALERTS:		Cmd.ARG_ALERT,
  Cmd.ARG_ALERTSFEEDBACK:	Cmd.ARG_ALERTFEEDBACK,
  Cmd.ARG_ALIASDOMAIN:		Cmd.ARG_DOMAINALIAS,
  Cmd.ARG_ALIASDOMAINS:		Cmd.ARG_DOMAINALIAS,
  Cmd.ARG_ALIASES:		Cmd.ARG_ALIAS,
  Cmd.ARG_APIS:			Cmd.ARG_API,
  Cmd.ARG_APIPROJECT:		Cmd.ARG_PROJECT,
  Cmd.ARG_APPDETAILS:		Cmd.ARG_CHROMEAPP,
  Cmd.ARG_BROWSERS:		Cmd.ARG_BROWSER,
  Cmd.ARG_BROWSERTOKENS:	Cmd.ARG_BROWSERTOKEN,
  Cmd.ARG_BUCKET:		Cmd.ARG_STORAGEBUCKET,
  Cmd.ARG_BUCKETS:		Cmd.ARG_STORAGEBUCKET,
  Cmd.ARG_BUILDINGS:		Cmd.ARG_BUILDING,
  Cmd.ARG_CAALEVELS:		Cmd.ARG_CAALEVEL,
  Cmd.ARG_CHATMEMBERS:		Cmd.ARG_CHATMEMBER,
  Cmd.ARG_CHANNELCUSTOMERS:	Cmd.ARG_CHANNELCUSTOMER,
  Cmd.ARG_CHANNELCUSTOMERENTITLEMENTS:	Cmd.ARG_CHANNELCUSTOMERENTITLEMENT,
  Cmd.ARG_CHANNELOFFERS:	Cmd.ARG_CHANNELOFFER,
  Cmd.ARG_CHANNELPRODUCTS:	Cmd.ARG_CHANNELPRODUCT,
  Cmd.ARG_CHANNELSKUS:		Cmd.ARG_CHANNELSKU,
  Cmd.ARG_CHATSPACES:		Cmd.ARG_CHATSPACE,
  Cmd.ARG_CHROMEAPPS:		Cmd.ARG_CHROMEAPP,
  Cmd.ARG_CHROMENETWORKS:	Cmd.ARG_CHROMENETWORK,
  Cmd.ARG_CHROMEPOLICIES:	Cmd.ARG_CHROMEPOLICY,
  Cmd.ARG_CHROMEPROFILES:	Cmd.ARG_CHROMEPROFILE,
  Cmd.ARG_CHROMEPROFILECOMMANDS:	Cmd.ARG_CHROMEPROFILECOMMAND,
  Cmd.ARG_CHROMESCHEMAS:	Cmd.ARG_CHROMESCHEMA,
  Cmd.ARG_CIGROUPS:		Cmd.ARG_CIGROUP,
  Cmd.ARG_CIGROUPSMEMBERS:	Cmd.ARG_CIGROUPMEMBERS,
  Cmd.ARG_CIMEMBER:		Cmd.ARG_CIGROUPMEMBERS,
  Cmd.ARG_CIMEMBERS:		Cmd.ARG_CIGROUPMEMBERS,
  Cmd.ARG_CIPOLICIES:		Cmd.ARG_CIPOLICY,
  Cmd.ARG_CLASSIFICATIONLABEL:	Cmd.ARG_DRIVELABEL,
  Cmd.ARG_CLASSIFICATIONLABELS:	Cmd.ARG_DRIVELABEL,
  Cmd.ARG_CLASSIFICATIONLABELPERMISSION:	Cmd.ARG_DRIVELABELPERMISSION,
  Cmd.ARG_CLASSIFICATIONLABELPERMISSIONS:	Cmd.ARG_DRIVELABELPERMISSION,
  Cmd.ARG_CLASS:		Cmd.ARG_COURSE,
  Cmd.ARG_CLASSES:		Cmd.ARG_COURSES,
  Cmd.ARG_CLASSCOUNTS:		Cmd.ARG_COURSECOUNTS,
  Cmd.ARG_CLASSPARTICIPANTS:	Cmd.ARG_COURSEPARTICIPANTS,
  Cmd.ARG_CLASSROOMINVITATIONS:	Cmd.ARG_CLASSROOMINVITATION,
  Cmd.ARG_CONTACTS:		Cmd.ARG_CONTACT,
  Cmd.ARG_CONTACTPHOTOS:	Cmd.ARG_CONTACTPHOTO,
  Cmd.ARG_COURSESTUDENTGROUPS:	Cmd.ARG_COURSESTUDENTGROUP,
  Cmd.ARG_CROSES:		Cmd.ARG_CROS,
  Cmd.ARG_DATATRANSFERS:	Cmd.ARG_DATATRANSFER,
  Cmd.ARG_DEVICES:		Cmd.ARG_DEVICE,
  Cmd.ARG_DEVICEFILES:		Cmd.ARG_DEVICEFILE,
  Cmd.ARG_DEVICEUSERS:		Cmd.ARG_DEVICEUSER,
  Cmd.ARG_DOMAINS:		Cmd.ARG_DOMAIN,
  Cmd.ARG_DOMAINALIASES:	Cmd.ARG_DOMAINALIAS,
  Cmd.ARG_DOMAINCONTACT:	Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_DOMAINCONTACTS:	Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_DOMAINPROFILES:	Cmd.ARG_PEOPLEPROFILE,
  Cmd.ARG_DRIVEFILEACLS:	Cmd.ARG_DRIVEFILEACL,
  Cmd.ARG_DRIVELABELS:		Cmd.ARG_DRIVELABEL,
  Cmd.ARG_DRIVELABELPERMISSIONS:	Cmd.ARG_DRIVELABELPERMISSION,
  Cmd.ARG_EXPORT:		Cmd.ARG_VAULTEXPORT,
  Cmd.ARG_EXPORTS:		Cmd.ARG_VAULTEXPORT,
  Cmd.ARG_FEATURES:		Cmd.ARG_FEATURE,
  Cmd.ARG_FORMS:		Cmd.ARG_FORM,
  Cmd.ARG_GROUPS:		Cmd.ARG_GROUP,
  Cmd.ARG_GROUPSMEMBERS:	Cmd.ARG_GROUPMEMBERS,
  Cmd.ARG_GUARDIANINVITATIONS:	Cmd.ARG_GUARDIANINVITATION,
  Cmd.ARG_GUARDIANINVITE:	Cmd.ARG_GUARDIANINVITATION,
  Cmd.ARG_GUARDIANS:		Cmd.ARG_GUARDIAN,
  Cmd.ARG_HOLD:			Cmd.ARG_VAULTHOLD,
  Cmd.ARG_HOLDS:		Cmd.ARG_VAULTHOLD,
  Cmd.ARG_INBOUNDSSOASSIGNMENTS:	Cmd.ARG_INBOUNDSSOASSIGNMENT,
  Cmd.ARG_INBOUNDSSOCREDENTIALS:	Cmd.ARG_INBOUNDSSOCREDENTIAL,
  Cmd.ARG_INBOUNDSSOPROFILES:	Cmd.ARG_INBOUNDSSOPROFILE,
  Cmd.ARG_INVITEGUARDIAN:	Cmd.ARG_GUARDIANINVITATION,
  Cmd.ARG_LICENCE:		Cmd.ARG_LICENSE,
  Cmd.ARG_LICENCES:		Cmd.ARG_LICENSE,
  Cmd.ARG_LICENSES:		Cmd.ARG_LICENSE,
  Cmd.ARG_MATTER:		Cmd.ARG_VAULTMATTER,
  Cmd.ARG_MATTERS:		Cmd.ARG_VAULTMATTER,
  Cmd.ARG_MEMBER:		Cmd.ARG_GROUPMEMBERS,
  Cmd.ARG_MEMBERS:		Cmd.ARG_GROUPMEMBERS,
  Cmd.ARG_MOBILES:		Cmd.ARG_MOBILE,
  Cmd.ARG_NICKNAME:		Cmd.ARG_ALIAS,
  Cmd.ARG_NICKNAMES:		Cmd.ARG_ALIAS,
  Cmd.ARG_ORGUNIT:		Cmd.ARG_ORG,
  Cmd.ARG_ORGUNITS:		Cmd.ARG_ORGS,
  Cmd.ARG_ORGUNITSHAREDDRIVES:	Cmd.ARG_ORGUNITSHAREDDRIVE,
  Cmd.ARG_OU:			Cmd.ARG_ORG,
  Cmd.ARG_OUS:			Cmd.ARG_ORGS,
  Cmd.ARG_OUSHAREDDRIVE:	Cmd.ARG_ORGUNITSHAREDDRIVE,
  Cmd.ARG_OUSHAREDDRIVES:	Cmd.ARG_ORGUNITSHAREDDRIVE,
  Cmd.ARG_OUTREE:		Cmd.ARG_ORGTREE,
  Cmd.ARG_PARTICIPANTS:		Cmd.ARG_COURSEPARTICIPANTS,
  Cmd.ARG_PEOPLE:		Cmd.ARG_PEOPLEPROFILE,
  Cmd.ARG_PEOPLECONTACTS:	Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_PEOPLEPROFILES:	Cmd.ARG_PEOPLEPROFILE,
  Cmd.ARG_PERMISSIONS:		Cmd.ARG_PERMISSION,
  Cmd.ARG_PRINTERS:		Cmd.ARG_PRINTER,
  Cmd.ARG_PRINTERMODELS:	Cmd.ARG_PRINTERMODEL,
  Cmd.ARG_PROJECTS:		Cmd.ARG_PROJECT,
  Cmd.ARG_RESELLERCUSTOMERS:	Cmd.ARG_RESOLDCUSTOMER,
  Cmd.ARG_RESELLERSUBSCRIPTIONS:	Cmd.ARG_RESOLDSUBSCRIPTION,
  Cmd.ARG_RESOLDCUSTOMERS:	Cmd.ARG_RESOLDCUSTOMER,
  Cmd.ARG_RESOLDSUBSCRIPTIONS:	Cmd.ARG_RESOLDSUBSCRIPTION,
  Cmd.ARG_ROLE:			Cmd.ARG_ADMINROLE,
  Cmd.ARG_ROLES:		Cmd.ARG_ADMINROLE,
  Cmd.ARG_SAKEYS:		Cmd.ARG_SAKEY,
  Cmd.ARG_SCHEMAS:		Cmd.ARG_SCHEMA,
  Cmd.ARG_SHAREDDRIVES:		Cmd.ARG_SHAREDDRIVE,
  Cmd.ARG_SIGNJWTSERVICEACCOUNT:	Cmd.ARG_GCPSERVICEACCOUNT,
  Cmd.ARG_SITEACLS:		Cmd.ARG_SITEACL,
  Cmd.ARG_SITES:		Cmd.ARG_SITE,
  Cmd.ARG_STORAGEBUCKETS:	Cmd.ARG_STORAGEBUCKET,
  Cmd.ARG_STORAGEFILES:		Cmd.ARG_STORAGEFILE,
  Cmd.ARG_SVCACCTS:		Cmd.ARG_SVCACCT,
  Cmd.ARG_TEAMDRIVE:		Cmd.ARG_SHAREDDRIVE,
  Cmd.ARG_TEAMDRIVES:		Cmd.ARG_SHAREDDRIVE,
  Cmd.ARG_TEAMDRIVEACLS:	Cmd.ARG_SHAREDDRIVEACLS,
  Cmd.ARG_TEAMDRIVEINFO:	Cmd.ARG_SHAREDDRIVEINFO,
  Cmd.ARG_TEAMDRIVEORGANIZERS:	Cmd.ARG_SHAREDDRIVEORGANIZERS,
  Cmd.ARG_TEAMDRIVETHEMES:	Cmd.ARG_SHAREDDRIVETHEMES,
  Cmd.ARG_TOKENS:		Cmd.ARG_TOKEN,
  Cmd.ARG_TRANSFER:		Cmd.ARG_DATATRANSFER,
  Cmd.ARG_TRANSFERS:		Cmd.ARG_DATATRANSFER,
  Cmd.ARG_USERINVITATIONS:	Cmd.ARG_USERINVITATION,
  Cmd.ARG_VAULTCOUNTS:		Cmd.ARG_VAULTCOUNT,
  Cmd.ARG_VAULTEXPORTS:		Cmd.ARG_VAULTEXPORT,
  Cmd.ARG_VAULTHOLDS:		Cmd.ARG_VAULTHOLD,
  Cmd.ARG_VAULTQUERIES:		Cmd.ARG_VAULTQUERY,
  Cmd.ARG_VAULTMATTERS:		Cmd.ARG_VAULTMATTER,
  Cmd.ARG_VERIFICATION:		Cmd.ARG_VERIFY,
  }

# Audit command sub-commands with objects
AUDIT_SUBCOMMANDS_WITH_OBJECTS = {
  'monitor':
    {'create': (Act.CREATE, doCreateMonitor),
     'delete': (Act.DELETE, doDeleteMonitor),
     'list': (Act.LIST, doShowMonitors),
    },
  }

def processAuditCommands():
  CL_subCommand = getChoice(list(AUDIT_SUBCOMMANDS_WITH_OBJECTS))
  CL_objectName = getChoice(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand])
  Act.Set(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_ACTION])
  AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_FUNCTION]()

# Oauth command sub-commands
OAUTH2_SUBCOMMANDS = {
  'create': 			(Act.CREATE, doOAuthCreate),
  'delete': 			(Act.DELETE, doOAuthDelete),
  'export': 			(Act.EXPORT, doOAuthExport),
  'info': 			(Act.INFO, doOAuthInfo),
  'refresh': 			(Act.REFRESH, doOAuthRefresh),
  'update': 			(Act.UPDATE, doOAuthUpdate),
  }

# Oauth sub-command aliases
OAUTH2_SUBCOMMAND_ALIASES = {
  'request':			'create',
  'revoke':			'delete',
  'verify':			'info',
  }

def processOauthCommands():
  CL_subCommand = getChoice(OAUTH2_SUBCOMMANDS, choiceAliases=OAUTH2_SUBCOMMAND_ALIASES)
  Act.Set(OAUTH2_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  if GC.Values[GC.ENABLE_DASA]:
    systemErrorExit(USAGE_ERROR_RC, Msg.COMMAND_NOT_COMPATIBLE_WITH_ENABLE_DASA.format('oauth', CL_subCommand))
  OAUTH2_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION]()

# Calendar command sub-commands
CALENDAR_SUBCOMMANDS = {
  'showacl': 			(Act.SHOW, doCalendarsPrintShowACLs),
  'printacl': 			(Act.PRINT, doCalendarsPrintShowACLs),
  'addevent': 			(Act.ADD, doCalendarsCreateEvent),
  'deleteevent': 		(Act.DELETE, doCalendarsDeleteEventsOld),
  'moveevent': 			(Act.MOVE, doCalendarsMoveEventsOld),
  'updateevent': 		(Act.UPDATE, doCalendarsUpdateEventsOld),
  'printevents': 		(Act.PRINT, doCalendarsPrintShowEvents),
  'wipe': 			(Act.WIPE, doCalendarsWipeEvents),
  'modify': 			(Act.MODIFY, doCalendarsModifySettings),
  }

CALENDAR_OLDACL_SUBCOMMANDS = {
  'add': 			(Act.ADD, doCalendarsCreateACL),
  'create': 			(Act.CREATE, doCalendarsCreateACL),
  'delete': 			(Act.DELETE, doCalendarsDeleteACL),
  'update': 			(Act.UPDATE, doCalendarsUpdateACL),
  }

# Calendar sub-command aliases
CALENDAR_OLDACL_SUBCOMMAND_ALIASES = {
  'del':			'delete',
  }

# Calendars command sub-commands with objects
CALENDARS_SUBCOMMANDS_WITH_OBJECTS = {
  'add':
    (Act.ADD,
     {Cmd.ARG_CALENDARACL:	doCalendarsCreateACLs,
      Cmd.ARG_EVENT:		doCalendarsCreateEvent,
     }
    ),
  'create':
    (Act.CREATE,
     {Cmd.ARG_CALENDARACL:	doCalendarsCreateACLs,
      Cmd.ARG_EVENT:		doCalendarsCreateEvent,
     }
    ),
  'delete':
    (Act.DELETE,
     {Cmd.ARG_CALENDARACL:	doCalendarsDeleteACLs,
      Cmd.ARG_EVENT:		doCalendarsDeleteEvents,
     }
    ),
  'empty':
    (Act.EMPTY,
     {Cmd.ARG_CALENDARTRASH:	doCalendarsEmptyTrash,
     }
    ),
  'import':
    (Act.IMPORT,
     {Cmd.ARG_EVENT:		doCalendarsImportEvent,
     }
    ),
  'info':
    (Act.INFO,
     {Cmd.ARG_CALENDARACL:	doCalendarsInfoACLs,
      Cmd.ARG_EVENT:		doCalendarsInfoEvents,
     }
    ),
  'move':
    (Act.MOVE,
     {Cmd.ARG_EVENT:		doCalendarsMoveEvents,
     }
    ),
  'print':
    (Act.PRINT,
     {Cmd.ARG_CALENDARACL:	doCalendarsPrintShowACLs,
      Cmd.ARG_EVENT:		doCalendarsPrintShowEvents,
      Cmd.ARG_SETTINGS:		doCalendarsPrintShowSettings,
     }
    ),
  'purge':
    (Act.PURGE,
     {Cmd.ARG_EVENT:		doCalendarsPurgeEvents,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_CALENDARACL:	doCalendarsPrintShowACLs,
      Cmd.ARG_EVENT:		doCalendarsPrintShowEvents,
      Cmd.ARG_SETTINGS:		doCalendarsPrintShowSettings,
     }
    ),
  'transfer':
    (Act.TRANSFER,
     {Cmd.ARG_OWNERSHIP:	doCalendarsTransferOwnership,
     }
    ),
  'update':
    (Act.UPDATE,
     {Cmd.ARG_CALENDARACL:	doCalendarsUpdateACLs,
      Cmd.ARG_EVENT:		doCalendarsUpdateEvents,
     }
    ),
  'wipe':
    (Act.WIPE,
     {Cmd.ARG_EVENT:		doCalendarsWipeEvents,
     }
    ),
  }

CALENDARS_SUBCOMMANDS_OBJECT_ALIASES = {
  Cmd.ARG_ACL:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_ACLS:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_CALENDARACLS:		Cmd.ARG_CALENDARACL,
  Cmd.ARG_EVENTS:		Cmd.ARG_EVENT,
  }

def processCalendarsCommands():
  calendarList = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
  CL_subCommand = getChoice(CALENDAR_SUBCOMMANDS, defaultChoice=None)
  if CL_subCommand:
    Act.Set(CALENDAR_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
    CALENDAR_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](calendarList)
    return
  CL_subCommand = getChoice(CALENDAR_OLDACL_SUBCOMMANDS, choiceAliases=CALENDAR_OLDACL_SUBCOMMAND_ALIASES, defaultChoice=None)
  if CL_subCommand:
    Act.Set(CALENDAR_OLDACL_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
    CL_objectName = getChoice([Cmd.ARG_CALENDARACL, Cmd.ARG_EVENT], choiceAliases=CALENDARS_SUBCOMMANDS_OBJECT_ALIASES, defaultChoice=None)
    if not CL_objectName:
      CALENDAR_OLDACL_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](calendarList)
    else:
      CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](calendarList)
    return
  CL_subCommand = getChoice(CALENDARS_SUBCOMMANDS_WITH_OBJECTS)
  Act.Set(CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION], choiceAliases=CALENDARS_SUBCOMMANDS_OBJECT_ALIASES)
  CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](calendarList)

# Course command sub-commands
COURSE_SUBCOMMANDS = {
  'add': 			(Act.ADD, doCourseAddItems),
  'clear': 			(Act.REMOVE, doCourseClearParticipants),
  'remove': 			(Act.REMOVE, doCourseRemoveItems),
  'update': 			(Act.UPDATE, doCourseUpdateItems),
  'sync': 			(Act.SYNC, doCourseSyncParticipants),
  }

# Course sub-command aliases
COURSE_SUBCOMMAND_ALIASES = {
  'create':			'add',
  'del':			'remove',
  'delete':			'remove',
  }

def executeCourseCommands(courseIdList, getEntityListArg):
  CL_subCommand = getChoice(COURSE_SUBCOMMANDS, choiceAliases=COURSE_SUBCOMMAND_ALIASES)
  Act.Set(COURSE_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  COURSE_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](courseIdList, getEntityListArg)

def processCourseCommands():
  executeCourseCommands(getStringReturnInList(Cmd.OB_COURSE_ID), False)

def processCoursesCommands():
  executeCourseCommands(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True), True)

# Resource command sub-commands
RESOURCE_SUBCOMMANDS_WITH_OBJECTS = {
  'add':
    (Act.ADD,
     {Cmd.ARG_CALENDARACL:	doResourceCreateCalendarACLs,
     }
    ),
  'create':
    (Act.CREATE,
     {Cmd.ARG_CALENDARACL:	doResourceCreateCalendarACLs,
     }
    ),
  'update':
    (Act.UPDATE,
     {Cmd.ARG_CALENDARACL:	doResourceUpdateCalendarACLs,
     }
    ),
  'delete':
    (Act.DELETE,
     {Cmd.ARG_CALENDARACL:	doResourceDeleteCalendarACLs,
     }
    ),
  'info':
    (Act.INFO,
     {Cmd.ARG_CALENDARACL:	doResourceInfoCalendarACLs,
     }
    ),
  'print':
    (Act.PRINT,
     {Cmd.ARG_CALENDARACL:	doResourcePrintShowCalendarACLs,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_CALENDARACL:	doResourcePrintShowCalendarACLs,
     }
    ),
  }

# Resource sub-command aliases
RESOURCE_SUBCOMMAND_ALIASES = {
  'del':			'delete',
  }

RESOURCE_SUBCOMMANDS_OBJECT_ALIASES = {
  Cmd.ARG_ACL:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_ACLS:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_CALENDARACLS:		Cmd.ARG_CALENDARACL,
  }

def executeResourceCommands(resourceEntity):
  CL_subCommand = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS, choiceAliases=RESOURCE_SUBCOMMAND_ALIASES)
  Act.Set(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION], choiceAliases=RESOURCE_SUBCOMMANDS_OBJECT_ALIASES)
  RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](resourceEntity)

def processResourceCommands():
  executeResourceCommands(getStringReturnInList(Cmd.OB_RESOURCE_ID))

def processResourcesCommands():
  executeResourceCommands(getEntityList(Cmd.OB_RESOURCE_ENTITY))

# Commands
COMMANDS_MAP = {
  'oauth':			processOauthCommands,
  'audit':			processAuditCommands,
  'calendars':			processCalendarsCommands,
  'course':			processCourseCommands,
  'courses':			processCoursesCommands,
  'resource':			processResourceCommands,
  'resources':			processResourcesCommands,
  }

# Commands aliases
COMMANDS_ALIASES = {
  'oauth2':			'oauth',
  'calendar':			'calendars',
  }

# <CrOSTypeEntity> commands
CROS_COMMANDS = {
  'getcommand': 		(Act.GET_COMMAND_RESULT, getCommandResultCrOSDevices),
  'info': 			(Act.INFO, infoCrOSDevices),
  'issuecommand': 		(Act.ISSUE_COMMAND, issueCommandCrOSDevices),
  'list': 			(Act.LIST, doListCrOS),
  'print': 			(Act.PRINT, doPrintCrOSEntity),
  'update': 			(Act.UPDATE, updateCrOSDevices),
  }

CROS_COMMANDS_WITH_OBJECTS = {
  'get':
    (Act.DOWNLOAD,
     {Cmd.ARG_DEVICEFILE:	getCrOSDeviceFiles,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_COUNT: 		showCountCrOS,
     }
    ),
  }

CROS_COMMANDS_OBJ_ALIASES = {
  Cmd.ARG_DEVICEFILES:		Cmd.ARG_DEVICEFILE,
  Cmd.ARG_COUNTS:		Cmd.ARG_COUNT,
  }

# <UserTypeEntity> commands
USER_COMMANDS = {
  'delegate': 			(Act.ADD, delegateTo),
  'deprovision':		(Act.DEPROVISION, deprovisionUser),
  'draftemail': 		(Act.DRAFT, draftMessage),
  'filter': 			(Act.ADD, createFilter),
  'forward': 			(Act.SET, setForward),
  'imap': 			(Act.SET, setImap),
  'importemail': 		(Act.IMPORT, importMessage),
  'insertemail': 		(Act.INSERT, insertMessage),
  'label': 			(Act.ADD, createLabel),
  'list': 			(Act.LIST, doListUser),
  'language': 			(Act.SET, setLanguage),
  'pop': 			(Act.SET, setPop),
  'profile': 			(Act.SET, setProfile),
  'sendas': 			(Act.ADD, createUpdateSendAs),
  'sendemail': 			(Act.SENDEMAIL, doSendEmail),
  'sendreply': 			(Act.SENDREPLY, doSendReply),
  'signature': 			(Act.SET, setSignature),
  'signout': 			(Act.SIGNOUT, signoutTurnoff2SVUsers),
  'turnoff2sv': 		(Act.TURNOFF2SV, signoutTurnoff2SVUsers),
  'vacation': 			(Act.SET, setVacation),
  'waitformailbox': 		(Act.WAITFORMAILBOX, waitForMailbox),
  }

# User commands with objects
#
USER_ADD_CREATE_FUNCTIONS = {
  Cmd.ARG_CALENDAR:		addCreateCalendars,
  Cmd.ARG_GROUP:		addUserToGroups,
  Cmd.ARG_CALENDARACL:		createCalendarACLs,
  Cmd.ARG_CHATEMOJI:		createChatEmoji,
  Cmd.ARG_CHATMEMBER:		createChatMember,
  Cmd.ARG_CHATMESSAGE:		createChatMessage,
  Cmd.ARG_CHATSECTION:		createUpdateChatSection,
  Cmd.ARG_CHATSPACE:		createChatSpace,
  Cmd.ARG_CLASSROOMINVITATION:	createClassroomInvitations,
  Cmd.ARG_CONTACTDELEGATE:	processContactDelegates,
  Cmd.ARG_CSEIDENTITY:		createUpdateCSEIdentity,
  Cmd.ARG_CSEKEYPAIR:		createCSEKeyPair,
  Cmd.ARG_LOOKERSTUDIOPERMISSION:	processLookerStudioPermissions,
  Cmd.ARG_DELEGATE:		processDelegates,
  Cmd.ARG_DRIVEFILE:		createDriveFile,
  Cmd.ARG_DRIVEFILEACL:		createDriveFileACL,
  Cmd.ARG_DRIVEFILESHORTCUT:	createDriveFileShortcut,
  Cmd.ARG_DRIVEFOLDERPATH:	createDriveFolderPath,
  Cmd.ARG_DRIVELABELPERMISSION:	createDriveLabelPermissions,
  Cmd.ARG_EVENT:		createCalendarEvent,
  Cmd.ARG_FILTER:		createFilter,
  Cmd.ARG_FOCUSTIME:		createFocusTime,
  Cmd.ARG_FORM:			createForm,
  Cmd.ARG_FORWARDINGADDRESS:	createForwardingAddresses,
  Cmd.ARG_GUARDIAN:		inviteGuardians,
  Cmd.ARG_GUARDIANINVITATION:	inviteGuardians,
  Cmd.ARG_LABEL:		createLabel,
  Cmd.ARG_LABELLIST:		createLabelList,
  Cmd.ARG_LICENSE:		createLicense,
  Cmd.ARG_MEETSPACE:		createMeetSpace,
  Cmd.ARG_NOTE:			createNote,
  Cmd.ARG_NOTEACL:		createNotesACLs,
  Cmd.ARG_OUTOFOFFICE:		createOutOfOffice,
  Cmd.ARG_PEOPLECONTACT:	createUserPeopleContact,
  Cmd.ARG_PEOPLECONTACTGROUP:	createUserPeopleContactGroup,
  Cmd.ARG_PERMISSION:		createDriveFilePermissions,
  Cmd.ARG_SENDAS:		createUpdateSendAs,
  Cmd.ARG_SHAREDDRIVE:		createSharedDrive,
  Cmd.ARG_SHEET:		createSheet,
  Cmd.ARG_SITE:			deprecatedUserSites,
  Cmd.ARG_SITEACL:		deprecatedUserSites,
  Cmd.ARG_SMIME:		createSmime,
  Cmd.ARG_TASK:			processTasks,
  Cmd.ARG_TASKLIST:		processTasklists,
  Cmd.ARG_WORKINGLOCATION:	createWorkingLocation,
  }

USER_COMMANDS_WITH_OBJECTS = {
  'accept':
    (Act.ACCEPT,
     {Cmd.ARG_CLASSROOMINVITATION:	acceptClassroomInvitations,
     }
    ),
  'add':
    (Act.ADD,
     USER_ADD_CREATE_FUNCTIONS
    ),
  'append':
    (Act.APPEND,
     {Cmd.ARG_SHEETRANGE:	appendSheetRanges,
     }
    ),
  'archive':
    (Act.ARCHIVE,
     {Cmd.ARG_MESSAGE:		archiveMessages,
     }
    ),
  'cancel':
    (Act.CANCEL,
     {Cmd.ARG_GUARDIANINVITATION:	cancelGuardianInvitations,
     }
    ),
  'check':
    (Act.CHECK,
     {Cmd.ARG_DRIVEFILESHORTCUT:	checkDriveFileShortcut,
      Cmd.ARG_GROUP:		checkUserInGroups,
      Cmd.ARG_ISINVITABLE:	checkCIUserIsInvitable,
      Cmd.ARG_SERVICEACCOUNT:	checkServiceAccount,
     }
    ),
  'claim':
    (Act.CLAIM,
     {Cmd.ARG_OWNERSHIP:	claimOwnership,
     }
    ),
  'clear':
    (Act.CLEAR,
     {Cmd.ARG_GUARDIAN:		clearGuardians,
      Cmd.ARG_PEOPLECONTACT:	clearUserPeopleContacts,
      Cmd.ARG_SHEETRANGE:	clearSheetRanges,
      Cmd.ARG_TASKLIST:		processTasklists,
   }
    ),
  'collect':
    (Act.COLLECT,
     {Cmd.ARG_ORPHANS:		collectOrphans,
     }
    ),
  'copy':
    (Act.COPY,
     {Cmd.ARG_DRIVEFILE:	copyDriveFile,
      Cmd.ARG_OTHERCONTACT:	copyUserPeopleOtherContacts,
      Cmd.ARG_SHAREDDRIVEACLS:	copySyncSharedDriveACLs,
     }
    ),
  'create':
    (Act.CREATE,
     USER_ADD_CREATE_FUNCTIONS
    ),
  'dedup':
    (Act.DEDUP,
     {Cmd.ARG_PEOPLECONTACT:	dedupReplaceDomainUserPeopleContacts,
     }
    ),
  'delete':
    (Act.DELETE,
     {Cmd.ARG_ALIAS:		deleteUsersAliases,
      Cmd.ARG_ASP:		deleteASP,
      Cmd.ARG_BACKUPCODE:	deleteBackupCodes,
      Cmd.ARG_CALENDAR:		deleteCalendars,
      Cmd.ARG_CALENDARACL:	deleteCalendarACLs,
      Cmd.ARG_CHATEMOJI:	deleteChatEmoji,
      Cmd.ARG_CHATMEMBER:	deleteUpdateChatMember,
      Cmd.ARG_CHATMESSAGE:	deleteChatMessage,
      Cmd.ARG_CHATSECTION:	deleteChatSection,
      Cmd.ARG_CHATSPACE:	deleteChatSpace,
      Cmd.ARG_CLASSROOMINVITATION:	deleteClassroomInvitations,
      Cmd.ARG_CONTACTDELEGATE:	processContactDelegates,
      Cmd.ARG_CSEIDENTITY:	processCSEIdentity,
      Cmd.ARG_LOOKERSTUDIOPERMISSION:	processLookerStudioPermissions,
      Cmd.ARG_DELEGATE:		processDelegates,
      Cmd.ARG_DRIVEFILE:	deleteDriveFile,
      Cmd.ARG_DRIVEFILEACL:	deleteDriveFileACLs,
      Cmd.ARG_DRIVELABELPERMISSION:	deleteDriveLabelPermissions,
      Cmd.ARG_EMPTYDRIVEFOLDERS:	deleteEmptyDriveFolders,
      Cmd.ARG_EVENT:		deleteCalendarEvents,
      Cmd.ARG_FILEREVISION:	deleteFileRevisions,
      Cmd.ARG_FILTER:		deleteFilters,
      Cmd.ARG_FOCUSTIME:	deleteFocusTime,
      Cmd.ARG_FORWARDINGADDRESS:	deleteForwardingAddresses,
      Cmd.ARG_GROUP:		deleteUserFromGroups,
      Cmd.ARG_GUARDIAN:		deleteGuardians,
      Cmd.ARG_LABEL:		deleteLabel,
      Cmd.ARG_LABELLIST:	deleteLabelList,
      Cmd.ARG_LABELID:		deleteLabelId,
      Cmd.ARG_LABELIDLIST:	deleteLabelIdList,
      Cmd.ARG_LICENSE:		deleteLicense,
      Cmd.ARG_MESSAGE:		processMessages,
      Cmd.ARG_NOTE:		deleteInfoNotes,
      Cmd.ARG_NOTEACL:		deleteNotesACLs,
      Cmd.ARG_OUTOFOFFICE:	deleteOutOfOffice,
      Cmd.ARG_OTHERCONTACT:	processUserPeopleOtherContacts,
      Cmd.ARG_PEOPLECONTACT:	deleteUserPeopleContacts,
      Cmd.ARG_PEOPLECONTACTGROUP:	deleteUserPeopleContactGroups,
      Cmd.ARG_PEOPLECONTACTPHOTO:	deleteUserPeopleContactPhoto,
      Cmd.ARG_PERMISSION:	deletePermissions,
      Cmd.ARG_PHOTO:		deletePhoto,
      Cmd.ARG_SENDAS:		deleteInfoSendAs,
      Cmd.ARG_SMIME:		deleteSmime,
      Cmd.ARG_SHAREDDRIVE:	deleteSharedDrive,
      Cmd.ARG_SITEACL:		deprecatedUserSites,
      Cmd.ARG_TASK:		processTasks,
      Cmd.ARG_TASKLIST:		processTasklists,
      Cmd.ARG_THREAD:		processThreads,
      Cmd.ARG_TOKEN:		deleteTokens,
      Cmd.ARG_USER:		deleteUsers,
      Cmd.ARG_WORKINGLOCATION:	deleteWorkingLocation,
     }
    ),
  'disable':
    (Act.DISABLE,
     {Cmd.ARG_CSEKEYPAIR:	processCSEKeyPair,
     }
    ),
  'draft':
    (Act.DRAFT,
     {Cmd.ARG_MESSAGE:		draftMessage,
     }
    ),
  'empty':
    (Act.EMPTY,
     {Cmd.ARG_CALENDARTRASH:	emptyCalendarTrash,
      Cmd.ARG_DRIVETRASH:	emptyDriveTrash,
     }
    ),
  'enable':
    (Act.ENABLE,
     {Cmd.ARG_CSEKEYPAIR:	processCSEKeyPair,
     }
    ),
  'end':
    (Act.END,
     {Cmd.ARG_MEETCONFERENCE:	endMeetConference,
     }
    ),
  'export':
    (Act.EXPORT,
     {Cmd.ARG_MESSAGE:		exportMessages,
      Cmd.ARG_THREAD:		exportThreads,
     }
    ),
  'get':
    (Act.DOWNLOAD,
     {Cmd.ARG_DOCUMENT:		getGoogleDocument,
      Cmd.ARG_DRIVEFILE:	getDriveFile,
      Cmd.ARG_NOTEATTACHMENT:	getNoteAttachments,
      Cmd.ARG_PEOPLECONTACTPHOTO:	getUserPeopleContactPhoto,
      Cmd.ARG_PHOTO:		getUserPhoto,
      Cmd.ARG_PROFILE_PHOTO:	getProfilePhoto,
     }
    ),
  'hide':
    (Act.HIDE,
     {Cmd.ARG_SHAREDDRIVE:	hideUnhideSharedDrive,
     }
    ),
  'import':
    (Act.IMPORT,
     {Cmd.ARG_EVENT:		importCalendarEvent,
      Cmd.ARG_MESSAGE:		importMessage,
      Cmd.ARG_TASKLIST:		importTasklist,
     }
    ),
  'info':
    (Act.INFO,
     {Cmd.ARG_CALENDAR:		infoCalendars,
      Cmd.ARG_CALENDARACL:	infoCalendarACLs,
      Cmd.ARG_CHATEMOJI:	infoChatEmoji,
      Cmd.ARG_CHATEVENT:	infoChatEvent,
      Cmd.ARG_CHATMEMBER:	infoChatMember,
      Cmd.ARG_CHATMESSAGE:	infoChatMessage,
      Cmd.ARG_CHATSPACE:	infoChatSpace,
      Cmd.ARG_CHATSPACEDM:	infoChatSpaceDM,
      Cmd.ARG_CIGROUPMEMBERS:	infoCIGroupMembers,
      Cmd.ARG_CSEIDENTITY:	processCSEIdentity,
      Cmd.ARG_CSEKEYPAIR:	processCSEKeyPair,
      Cmd.ARG_DRIVEFILE:	showFileInfo,
      Cmd.ARG_DRIVEFILEACL:	infoDriveFileACLs,
      Cmd.ARG_DRIVELABEL:	infoDriveLabels,
      Cmd.ARG_EVENT:		infoCalendarEvents,
      Cmd.ARG_FILTER:		infoFilters,
      Cmd.ARG_FORWARDINGADDRESS:	infoForwardingAddresses,
      Cmd.ARG_GROUPMEMBERS:	infoGroupMembers,
      Cmd.ARG_MEETSPACE:	infoMeetSpace,
      Cmd.ARG_NOTE:		deleteInfoNotes,
      Cmd.ARG_PEOPLECONTACT:	infoUserPeopleContacts,
      Cmd.ARG_PEOPLECONTACTGROUP:	infoUserPeopleContactGroups,
      Cmd.ARG_SENDAS:		deleteInfoSendAs,
      Cmd.ARG_SHAREDDRIVE:	infoSharedDrive,
      Cmd.ARG_SHEET:		infoPrintShowSheets,
      Cmd.ARG_SITE:		deprecatedUserSites,
      Cmd.ARG_SITEACL:		deprecatedUserSites,
      Cmd.ARG_TASK:		processTasks,
      Cmd.ARG_TASKLIST:		processTasklists,
      Cmd.ARG_USER:		infoUsers,
     }
    ),
  'insert':
    (Act.INSERT,
     {Cmd.ARG_MESSAGE:		insertMessage,
     }
    ),
  'modify':
    (Act.MODIFY,
     {Cmd.ARG_CALENDAR:		modifyCalendars,
      Cmd.ARG_CHATMEMBER:	deleteUpdateChatMember,
      Cmd.ARG_MESSAGE:		processMessages,
      Cmd.ARG_THREAD:		processThreads,
     }
    ),
  'move':
    (Act.MOVE,
     {Cmd.ARG_DRIVEFILE:	moveDriveFile,
      Cmd.ARG_EVENT:		moveCalendarEvents,
      Cmd.ARG_CHATSECTIONITEM:	moveShowChatSectionItem,
      Cmd.ARG_OTHERCONTACT:	processUserPeopleOtherContacts,
      Cmd.ARG_TASK:		processTasks,
     }
    ),
  'obliterate':
    (Act.OBLITERATE,
     {Cmd.ARG_CSEKEYPAIR:	processCSEKeyPair,
     }
    ),
  'purge':
    (Act.PURGE,
     {Cmd.ARG_DRIVEFILE:	purgeDriveFile,
      Cmd.ARG_EVENT:		purgeCalendarEvents,
     }
    ),
  'print':
    (Act.PRINT,
     {Cmd.ARG_ANALYTICACCOUNT:	printShowAnalyticAccounts,
      Cmd.ARG_ANALYTICACCOUNTSUMMARY:	printShowAnalyticAccountSummaries,
      Cmd.ARG_ANALYTICDATASTREAM:	printShowAnalyticDatastreams,
      Cmd.ARG_ANALYTICPROPERTY:	printShowAnalyticProperties,
      Cmd.ARG_ASP:		printShowASPs,
      Cmd.ARG_BACKUPCODE:	printShowBackupCodes,
      Cmd.ARG_BUSINESSPROFILEACCOUNT:	printShowBusinessProfileAccounts,
      Cmd.ARG_CALENDAR:		printShowCalendars,
      Cmd.ARG_CALENDARACL:	printShowCalendarACLs,
      Cmd.ARG_CALSETTINGS:	printShowCalSettings,
      Cmd.ARG_CHATEMOJI:	printShowChatEmojis,
      Cmd.ARG_CHATEVENT:	printShowChatEvents,
      Cmd.ARG_CHATMEMBER:	printShowChatMembers,
      Cmd.ARG_CHATMESSAGE:	printShowChatMessages,
      Cmd.ARG_CHATSEARCHMESSAGE:	printShowChatSearchMessages,
      Cmd.ARG_CHATSECTION:	printShowChatSections,
      Cmd.ARG_CHATSECTIONITEM:	printShowChatSectionItems,
      Cmd.ARG_CHATSPACE:	printShowChatSpaces,
      Cmd.ARG_CLASSROOMINVITATION:	printShowClassroomInvitations,
      Cmd.ARG_CLASSROOMPROFILE:	printShowClassroomProfile,
      Cmd.ARG_CONTACTDELEGATE:	printShowContactDelegates,
      Cmd.ARG_CSEIDENTITY:	printShowCSEIdentities,
      Cmd.ARG_CSEKEYPAIR:	printShowCSEKeyPairs,
      Cmd.ARG_LOOKERSTUDIOASSET:	printShowLookerStudioAssets,
      Cmd.ARG_LOOKERSTUDIOPERMISSION:	printShowLookerStudioPermissions,
      Cmd.ARG_DELEGATE:		printShowDelegates,
      Cmd.ARG_DISKUSAGE:	printDiskUsage,
      Cmd.ARG_DRIVEACTIVITY:	printDriveActivity,
      Cmd.ARG_DRIVEFILEACL:	printShowDriveFileACLs,
      Cmd.ARG_DRIVELABEL:	printShowDriveLabels,
      Cmd.ARG_DRIVELABELPERMISSION:	printShowDriveLabelPermissions,
      Cmd.ARG_DRIVELASTMODIFICATION:	printShowDrivelastModifications,
      Cmd.ARG_DRIVESETTINGS:	printShowDriveSettings,
      Cmd.ARG_EMPTYDRIVEFOLDERS:	printEmptyDriveFolders,
      Cmd.ARG_EVENT:		printShowCalendarEvents,
      Cmd.ARG_FILECOMMENT:	printShowFileComments,
      Cmd.ARG_FILECOUNT:	printShowFileCounts,
      Cmd.ARG_FILEINFO:		showFileInfo,
      Cmd.ARG_FILELIST:		printFileList,
      Cmd.ARG_FILEPATH:		printShowFilePaths,
      Cmd.ARG_FILEREVISION:	printShowFileRevisions,
      Cmd.ARG_FILESHARECOUNT:	printShowFileShareCounts,
      Cmd.ARG_FILETREE:		printShowFileTree,
      Cmd.ARG_FILTER:		printShowFilters,
      Cmd.ARG_FOCUSTIME:	printShowFocusTime,
      Cmd.ARG_FORM:		printShowForms,
      Cmd.ARG_FORMRESPONSE:	printShowFormResponses,
      Cmd.ARG_FORWARD:		printShowForward,
      Cmd.ARG_FORWARDINGADDRESS:	printShowForwardingAddresses,
      Cmd.ARG_GMAILPROFILE:	printShowGmailProfile,
      Cmd.ARG_GROUP:		printShowUserGroups,
      Cmd.ARG_GROUPSLIST:	printUserGroupsList,
      Cmd.ARG_GROUPTREE:	printShowGroupTree,
      Cmd.ARG_GUARDIAN:		printShowGuardians,
      Cmd.ARG_IMAP:		printShowImap,
      Cmd.ARG_LABEL:		printShowLabels,
      Cmd.ARG_LANGUAGE:		printShowLanguage,
      Cmd.ARG_MEETCONFERENCE:	printShowMeetConferences,
      Cmd.ARG_MEETPARTICIPANT:	printShowMeetParticipants,
      Cmd.ARG_MEETRECORDING:	printShowMeetRecordings,
      Cmd.ARG_MEETTRANSCRIPT:	printShowMeetTranscripts,
      Cmd.ARG_MESSAGE:		printShowMessages,
      Cmd.ARG_NOTE:		printShowNotes,
      Cmd.ARG_OTHERCONTACT:	printShowUserPeopleOtherContacts,
      Cmd.ARG_OUTOFOFFICE:	printShowOutOfOffice,
      Cmd.ARG_FILEPARENTTREE:	printFileParentTree,
      Cmd.ARG_PEOPLECONTACT:	printShowUserPeopleContacts,
      Cmd.ARG_PEOPLECONTACTGROUP:	printShowUserPeopleContactGroups,
      Cmd.ARG_PEOPLEPROFILE:	printShowUserPeopleProfiles,
      Cmd.ARG_POP:		printShowPop,
      Cmd.ARG_SENDAS:		printShowSendAs,
      Cmd.ARG_SHAREDDRIVE:	printShowSharedDrives,
      Cmd.ARG_SHAREDDRIVEACLS:	printShowSharedDriveACLs,
      Cmd.ARG_SHAREDDRIVEORGANIZERS:	printSharedDriveOrganizers,
      Cmd.ARG_SHEET:		infoPrintShowSheets,
      Cmd.ARG_SHEETRANGE:	printShowSheetRanges,
      Cmd.ARG_SIGNATURE:	printShowSignature,
      Cmd.ARG_SMIME:		printShowSmimes,
      Cmd.ARG_SITE:		deprecatedUserSites,
      Cmd.ARG_SITEACL:		deprecatedUserSites,
      Cmd.ARG_SITEACTIVITY:	deprecatedUserSites,
      Cmd.ARG_TAGMANAGERACCOUNT:	printShowTagManagerAccounts,
      Cmd.ARG_TAGMANAGERCONTAINER:	printShowTagManagerContainers,
      Cmd.ARG_TAGMANAGERPERMISSION:	printShowTagManagerPermissions,
      Cmd.ARG_TAGMANAGERTAG:	printShowTagManagerTags,
      Cmd.ARG_TAGMANAGERWORKSPACE:	printShowTagManagerWorkspaces,
      Cmd.ARG_TASK:		printShowTasks,
      Cmd.ARG_TASKLIST:		printShowTasklists,
      Cmd.ARG_THREAD:		printShowThreads,
      Cmd.ARG_TOKEN:		printShowTokens,
      Cmd.ARG_USER:		doPrintUserEntity,
      Cmd.ARG_USERLIST:		doPrintUserList,
      Cmd.ARG_VACATION:		printShowVacation,
      Cmd.ARG_VAULTHOLD:	printShowUserVaultHolds,
      Cmd.ARG_WEBMASTERSITE:	printShowWebMasterSites,
      Cmd.ARG_WEBRESOURCE:	printShowWebResources,
      Cmd.ARG_WORKINGLOCATION:	printShowWorkingLocation,
      Cmd.ARG_YOUTUBECHANNEL:	printShowYouTubeChannel,
     }
    ),
  'process':
    (Act.PROCESS,
     {Cmd.ARG_FILEDRIVELABEL:	processFileDriveLabels,
     }
    ),
  'remove':
    (Act.REMOVE,
     {Cmd.ARG_CALENDAR:		removeCalendars,
      Cmd.ARG_CHATMEMBER:	deleteUpdateChatMember,
      Cmd.ARG_DRIVELABELPERMISSION:	deleteDriveLabelPermissions,
     }
    ),
  'replacedomain':
    (Act.REPLACE_DOMAIN,
     {Cmd.ARG_PEOPLECONTACT:	dedupReplaceDomainUserPeopleContacts,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_ANALYTICACCOUNT:	printShowAnalyticAccounts,
      Cmd.ARG_ANALYTICACCOUNTSUMMARY:	printShowAnalyticAccountSummaries,
      Cmd.ARG_ANALYTICDATASTREAM:	printShowAnalyticDatastreams,
      Cmd.ARG_ANALYTICPROPERTY:	printShowAnalyticProperties,
      Cmd.ARG_ASP:		printShowASPs,
      Cmd.ARG_BACKUPCODE:	printShowBackupCodes,
      Cmd.ARG_BUSINESSPROFILEACCOUNT:	printShowBusinessProfileAccounts,
      Cmd.ARG_CALENDAR:		printShowCalendars,
      Cmd.ARG_CALENDARACL:	printShowCalendarACLs,
      Cmd.ARG_CALSETTINGS:	printShowCalSettings,
      Cmd.ARG_CHATEMOJI:	printShowChatEmojis,
      Cmd.ARG_CHATEVENT:	printShowChatEvents,
      Cmd.ARG_CHATMEMBER:	printShowChatMembers,
      Cmd.ARG_CHATMESSAGE:	printShowChatMessages,
      Cmd.ARG_CHATSEARCHMESSAGE:	printShowChatSearchMessages,
      Cmd.ARG_CHATSECTION:	printShowChatSections,
      Cmd.ARG_CHATSECTIONITEM:	printShowChatSectionItems,
      Cmd.ARG_CHATSPACE:	printShowChatSpaces,
      Cmd.ARG_CLASSROOMINVITATION:	printShowClassroomInvitations,
      Cmd.ARG_CLASSROOMPROFILE:	printShowClassroomProfile,
      Cmd.ARG_CONTACTDELEGATE:	printShowContactDelegates,
      Cmd.ARG_COUNT: 		showCountUser,
      Cmd.ARG_CSEIDENTITY:	printShowCSEIdentities,
      Cmd.ARG_CSEKEYPAIR:	printShowCSEKeyPairs,
      Cmd.ARG_LOOKERSTUDIOASSET:	printShowLookerStudioAssets,
      Cmd.ARG_LOOKERSTUDIOPERMISSION:	printShowLookerStudioPermissions,
      Cmd.ARG_DELEGATE:		printShowDelegates,
      Cmd.ARG_DISKUSAGE:	printDiskUsage,
      Cmd.ARG_DRIVEACTIVITY:	printDriveActivity,
      Cmd.ARG_DRIVEFILEACL:	printShowDriveFileACLs,
      Cmd.ARG_DRIVELABEL:	printShowDriveLabels,
      Cmd.ARG_DRIVELABELPERMISSION:	printShowDriveLabelPermissions,
      Cmd.ARG_DRIVELASTMODIFICATION:	printShowDrivelastModifications,
      Cmd.ARG_DRIVESETTINGS:	printShowDriveSettings,
      Cmd.ARG_EVENT:		printShowCalendarEvents,
      Cmd.ARG_FILECOMMENT:	printShowFileComments,
      Cmd.ARG_FILECOUNT:	printShowFileCounts,
      Cmd.ARG_FILEINFO:		showFileInfo,
      Cmd.ARG_FILELIST:		printFileList,
      Cmd.ARG_FILEPATH:		printShowFilePaths,
      Cmd.ARG_FILEREVISION:	printShowFileRevisions,
      Cmd.ARG_FILESHARECOUNT:	printShowFileShareCounts,
      Cmd.ARG_FILETREE:		printShowFileTree,
      Cmd.ARG_FILTER:		printShowFilters,
      Cmd.ARG_FOCUSTIME:	printShowFocusTime,
      Cmd.ARG_FORM:		printShowForms,
      Cmd.ARG_FORMRESPONSE:	printShowFormResponses,
      Cmd.ARG_FORWARD:		printShowForward,
      Cmd.ARG_FORWARDINGADDRESS:	printShowForwardingAddresses,
      Cmd.ARG_GMAILPROFILE:	printShowGmailProfile,
      Cmd.ARG_GROUP:		printShowUserGroups,
      Cmd.ARG_GROUPTREE:	printShowGroupTree,
      Cmd.ARG_GUARDIAN:		printShowGuardians,
      Cmd.ARG_IMAP:		printShowImap,
      Cmd.ARG_LABEL:		printShowLabels,
      Cmd.ARG_LANGUAGE:		printShowLanguage,
      Cmd.ARG_MEETCONFERENCE:	printShowMeetConferences,
      Cmd.ARG_MEETPARTICIPANT:	printShowMeetParticipants,
      Cmd.ARG_MEETRECORDING:	printShowMeetRecordings,
      Cmd.ARG_MEETTRANSCRIPT:	printShowMeetTranscripts,
      Cmd.ARG_MESSAGE:		printShowMessages,
      Cmd.ARG_NOTE:		printShowNotes,
      Cmd.ARG_OTHERCONTACT:	printShowUserPeopleOtherContacts,
      Cmd.ARG_OUTOFOFFICE:	printShowOutOfOffice,
      Cmd.ARG_PEOPLECONTACT:	printShowUserPeopleContacts,
      Cmd.ARG_PEOPLECONTACTGROUP:	printShowUserPeopleContactGroups,
      Cmd.ARG_PEOPLEPROFILE:	printShowUserPeopleProfiles,
      Cmd.ARG_POP:		printShowPop,
      Cmd.ARG_PROFILE:		showProfile,
      Cmd.ARG_SENDAS:		printShowSendAs,
      Cmd.ARG_SHAREDDRIVE:	printShowSharedDrives,
      Cmd.ARG_SHAREDDRIVEACLS:	printShowSharedDriveACLs,
      Cmd.ARG_SHAREDDRIVEINFO:	infoSharedDrive,
      Cmd.ARG_SHAREDDRIVETHEMES:	showSharedDriveThemes,
      Cmd.ARG_SHEET:		infoPrintShowSheets,
      Cmd.ARG_SHEETRANGE:	printShowSheetRanges,
      Cmd.ARG_SIGNATURE:	printShowSignature,
      Cmd.ARG_SITE:		deprecatedUserSites,
      Cmd.ARG_SITEACL:		deprecatedUserSites,
      Cmd.ARG_SMIME:		printShowSmimes,
      Cmd.ARG_TAGMANAGERACCOUNT:	printShowTagManagerAccounts,
      Cmd.ARG_TAGMANAGERCONTAINER:	printShowTagManagerContainers,
      Cmd.ARG_TAGMANAGERPERMISSION:	printShowTagManagerPermissions,
      Cmd.ARG_TAGMANAGERTAG:	printShowTagManagerTags,
      Cmd.ARG_TAGMANAGERWORKSPACE:	printShowTagManagerWorkspaces,
      Cmd.ARG_TASK:		printShowTasks,
      Cmd.ARG_TASKLIST:		printShowTasklists,
      Cmd.ARG_THREAD:		printShowThreads,
      Cmd.ARG_TOKEN:		printShowTokens,
      Cmd.ARG_VAULTHOLD:	printShowUserVaultHolds,
      Cmd.ARG_VACATION:		printShowVacation,
      Cmd.ARG_WEBMASTERSITE:	printShowWebMasterSites,
      Cmd.ARG_WEBRESOURCE:	printShowWebResources,
      Cmd.ARG_WORKINGLOCATION:	printShowWorkingLocation,
      Cmd.ARG_YOUTUBECHANNEL:	printShowYouTubeChannel,
     }
    ),
  'spam':
    (Act.SPAM,
     {Cmd.ARG_MESSAGE:		processMessages,
      Cmd.ARG_THREAD:		processThreads,
     }
    ),
  'suspend':
    (Act.SUSPEND,
     {Cmd.ARG_USER:		suspendUnsuspendUsers,
     }
    ),
  'sync':
    (Act.SYNC,
     {Cmd.ARG_CHATMEMBER:	syncChatMembers,
      Cmd.ARG_GROUP:		syncUserWithGroups,
      Cmd.ARG_GUARDIAN:		syncGuardians,
      Cmd.ARG_LICENSE:		syncLicense,
      Cmd.ARG_SHAREDDRIVEACLS:	copySyncSharedDriveACLs,
     }
    ),
  'transfer':
    (Act.TRANSFER,
     {Cmd.ARG_DRIVE:		transferDrive,
      Cmd.ARG_OWNERSHIP:	transferOwnership,
     }
    ),
  'trash':
    (Act.TRASH,
     {Cmd.ARG_DRIVEFILE:	trashDriveFile,
      Cmd.ARG_MESSAGE:		processMessages,
      Cmd.ARG_THREAD:		processThreads,
     }
    ),
  'undelete':
    (Act.UNDELETE,
     {Cmd.ARG_USER:		undeleteUsers,
     }
    ),
  'unhide':
    (Act.UNHIDE,
     {Cmd.ARG_SHAREDDRIVE:	hideUnhideSharedDrive,
     }
    ),
  'unsuspend':
    (Act.UNSUSPEND,
     {Cmd.ARG_USER:		suspendUnsuspendUsers,
     }
    ),
  'untrash':
    (Act.UNTRASH,
     {Cmd.ARG_DRIVEFILE:	untrashDriveFile,
      Cmd.ARG_MESSAGE:		processMessages,
      Cmd.ARG_THREAD:		processThreads,
     }
    ),
  'update':
    (Act.UPDATE,
     {Cmd.ARG_BACKUPCODE:	updateBackupCodes,
      Cmd.ARG_CALATTENDEES:	updateCalendarAttendees,
      Cmd.ARG_CALENDAR:		updateCalendars,
      Cmd.ARG_CALENDARACL:	updateCalendarACLs,
      Cmd.ARG_CHATMEMBER:	deleteUpdateChatMember,
      Cmd.ARG_CHATMESSAGE:	updateChatMessage,
      Cmd.ARG_CHATSECTION:	createUpdateChatSection,
      Cmd.ARG_CHATSPACE:	updateChatSpace,
      Cmd.ARG_CSEIDENTITY:	createUpdateCSEIdentity,
      Cmd.ARG_LOOKERSTUDIOPERMISSION:	processLookerStudioPermissions,
      Cmd.ARG_DELEGATE:		updateDelegates,
      Cmd.ARG_DOCUMENT:		updateGoogleDocument,
      Cmd.ARG_DRIVEFILE:	updateDriveFile,
      Cmd.ARG_DRIVEFILEACL:	updateDriveFileACLs,
      Cmd.ARG_EVENT:		updateCalendarEvents,
      Cmd.ARG_FILEREVISION:	updateFileRevisions,
      Cmd.ARG_FORM:		updateForm,
      Cmd.ARG_GROUP:		updateUserGroups,
      Cmd.ARG_LABEL:		updateLabels,
      Cmd.ARG_LABELID:		updateLabelSettingsById,
      Cmd.ARG_LABELSETTINGS:	updateLabelSettings,
      Cmd.ARG_LICENSE:		updateLicense,
      Cmd.ARG_MEETSPACE:	updateMeetSpace,
      Cmd.ARG_OTHERCONTACT:	processUserPeopleOtherContacts,
      Cmd.ARG_PEOPLECONTACT:	updateUserPeopleContacts,
      Cmd.ARG_PEOPLECONTACTGROUP:	updateUserPeopleContactGroup,
      Cmd.ARG_PEOPLECONTACTPHOTO:	updateUserPeopleContactPhoto,
      Cmd.ARG_PHOTO:		updatePhoto,
      Cmd.ARG_SENDAS:		createUpdateSendAs,
      Cmd.ARG_SERVICEACCOUNT:	checkServiceAccount,
      Cmd.ARG_SHAREDDRIVE:	updateSharedDrive,
      Cmd.ARG_SHEET:		updateSheets,
      Cmd.ARG_SHEETRANGE:	updateSheetRanges,
      Cmd.ARG_SMIME:		updateSmime,
      Cmd.ARG_SITE:		deprecatedUserSites,
      Cmd.ARG_SITEACL:		deprecatedUserSites,
      Cmd.ARG_TASK:		processTasks,
      Cmd.ARG_TASKLIST:		processTasklists,
      Cmd.ARG_USER:		updateUsers,
     }
    ),
  'watch':
    (Act.WATCH,
     {Cmd.ARG_GMAIL:		watchGmail,
     }
    ),
  'wipe':
    (Act.WIPE,
     {Cmd.ARG_EVENT:		wipeCalendarEvents,
     }
    ),
  }

# User commands aliases
USER_COMMANDS_ALIASES = {
  'del':	'delete',
  'delegates':	'delegate',
  'deprov':	'deprovision',
  'imap4':	'imap',
  'pop3':	'pop',
  'sig':	'signature',
  'utf':	'unicode',
  'utf-8':	'unicode',
  'utf8':	'unicode',
  }

USER_COMMANDS_OBJ_ALIASES = {
  Cmd.ARG_3LO:			Cmd.ARG_TOKEN,
  Cmd.ARG_ALIASES:		Cmd.ARG_ALIAS,
  Cmd.ARG_APPLICATIONSPECIFICPASSWORDS:	Cmd.ARG_ASP,
  Cmd.ARG_ANALYTICACCOUNTS:	Cmd.ARG_ANALYTICACCOUNT,
  Cmd.ARG_ANALYTICACCOUNTSUMMARIES:	Cmd.ARG_ANALYTICACCOUNTSUMMARY,
  Cmd.ARG_ANALYTICDATASTREAMS:	Cmd.ARG_ANALYTICDATASTREAM,
  Cmd.ARG_ANALYTICPROPERTIES:	Cmd.ARG_ANALYTICPROPERTY,
  Cmd.ARG_ASPS:			Cmd.ARG_ASP,
  Cmd.ARG_BACKUPCODES:		Cmd.ARG_BACKUPCODE,
  Cmd.ARG_BUSINESSPROFILEACCOUNTS:	Cmd.ARG_BUSINESSPROFILEACCOUNT,
  Cmd.ARG_CALENDARS:		Cmd.ARG_CALENDAR,
  Cmd.ARG_CALENDARACLS:		Cmd.ARG_CALENDARACL,
  Cmd.ARG_CLASSIFICATIONLABEL:	Cmd.ARG_DRIVELABEL,
  Cmd.ARG_CLASSIFICATIONLABELS:	Cmd.ARG_DRIVELABEL,
  Cmd.ARG_CLASSIFICATIONLABELPERMISSION:	Cmd.ARG_DRIVELABELPERMISSION,
  Cmd.ARG_CLASSIFICATIONLABELPERMISSIONS:	Cmd.ARG_DRIVELABELPERMISSION,
  Cmd.ARG_CLASSROOMINVITATIONS:	Cmd.ARG_CLASSROOMINVITATION,
  Cmd.ARG_CHATEMOJIS:		Cmd.ARG_CHATEMOJI,
  Cmd.ARG_CHATEVENTS:		Cmd.ARG_CHATEVENT,
  Cmd.ARG_CHATMEMBERS:		Cmd.ARG_CHATMEMBER,
  Cmd.ARG_CHATMESSAGES:		Cmd.ARG_CHATMESSAGE,
  Cmd.ARG_CHATSEARCHMESSAGES:	Cmd.ARG_CHATSEARCHMESSAGE,
  Cmd.ARG_CHATSECTIONS:		Cmd.ARG_CHATSECTION,
  Cmd.ARG_CHATSECTIONITEMS:	Cmd.ARG_CHATSECTIONITEM,
  Cmd.ARG_CHATSPACES:		Cmd.ARG_CHATSPACE,
  Cmd.ARG_CIMEMBER:		Cmd.ARG_CIGROUPMEMBERS,
  Cmd.ARG_CIMEMBERS:		Cmd.ARG_CIGROUPMEMBERS,
  Cmd.ARG_CONTACT:		Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_CONTACTS:		Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_CONTACTDELEGATES:	Cmd.ARG_CONTACTDELEGATE,
  Cmd.ARG_CONTACTGROUP:		Cmd.ARG_PEOPLECONTACTGROUP,
  Cmd.ARG_CONTACTGROUPS:	Cmd.ARG_PEOPLECONTACTGROUP,
  Cmd.ARG_CONTACTPHOTO:		Cmd.ARG_PEOPLECONTACTPHOTO,
  Cmd.ARG_CONTACTPHOTOS:	Cmd.ARG_PEOPLECONTACTPHOTO,
  Cmd.ARG_CSEIDENTITIES:	Cmd.ARG_CSEIDENTITY,
  Cmd.ARG_CSEKEYPAIRS:		Cmd.ARG_CSEKEYPAIR,
  Cmd.ARG_COUNTS:		Cmd.ARG_COUNT,
  Cmd.ARG_DATASTUDIOASSET:	Cmd.ARG_LOOKERSTUDIOASSET,
  Cmd.ARG_DATASTUDIOPERMISSION:	Cmd.ARG_LOOKERSTUDIOPERMISSION,
  Cmd.ARG_DATASTUDIOASSETS:	Cmd.ARG_LOOKERSTUDIOASSET,
  Cmd.ARG_DATASTUDIOPERMISSIONS:	Cmd.ARG_LOOKERSTUDIOPERMISSION,
  Cmd.ARG_LOOKERSTUDIOASSETS:	Cmd.ARG_LOOKERSTUDIOASSET,
  Cmd.ARG_LOOKERSTUDIOPERMISSIONS:	Cmd.ARG_LOOKERSTUDIOPERMISSION,
  Cmd.ARG_DELEGATES:		Cmd.ARG_DELEGATE,
  Cmd.ARG_DOMAINCONTACT:	Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_DOMAINCONTACTS:	Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_DRIVEFILEACLS:	Cmd.ARG_DRIVEFILEACL,
  Cmd.ARG_DRIVEFILESHORTCUTS:	Cmd.ARG_DRIVEFILESHORTCUT,
  Cmd.ARG_DRIVELABELS:		Cmd.ARG_DRIVELABEL,
  Cmd.ARG_DRIVELABELPERMISSIONS:	Cmd.ARG_DRIVELABELPERMISSION,
  Cmd.ARG_DRIVELASTMODIFICATIONS:	Cmd.ARG_DRIVELASTMODIFICATION,
  Cmd.ARG_EVENTS:		Cmd.ARG_EVENT,
  Cmd.ARG_FILECOMMENTS:		Cmd.ARG_FILECOMMENT,
  Cmd.ARG_FILECOUNTS:		Cmd.ARG_FILECOUNT,
  Cmd.ARG_FILEDRIVELABELS:	Cmd.ARG_FILEDRIVELABEL,
  Cmd.ARG_FILEPATHS:		Cmd.ARG_FILEPATH,
  Cmd.ARG_FILEREVISIONS:	Cmd.ARG_FILEREVISION,
  Cmd.ARG_FILESHARECOUNTS:	Cmd.ARG_FILESHARECOUNT,
  Cmd.ARG_FILTERS:		Cmd.ARG_FILTER,
  Cmd.ARG_FOCUSTIMES:		Cmd.ARG_FOCUSTIME,
  Cmd.ARG_FORMS:		Cmd.ARG_FORM,
  Cmd.ARG_FORMRESPONSES:	Cmd.ARG_FORMRESPONSE,
  Cmd.ARG_FORWARDS:		Cmd.ARG_FORWARD,
  Cmd.ARG_FORWARDINGADDRESSES:	Cmd.ARG_FORWARDINGADDRESS,
  Cmd.ARG_GROUPS:		Cmd.ARG_GROUP,
  Cmd.ARG_GROUPLIST:		Cmd.ARG_GROUPSLIST,
  Cmd.ARG_GROUPSMEMBERS:	Cmd.ARG_GROUPMEMBERS,
  Cmd.ARG_GUARDIANINVITATIONS:	Cmd.ARG_GUARDIANINVITATION,
  Cmd.ARG_GUARDIANINVITE:	Cmd.ARG_GUARDIANINVITATION,
  Cmd.ARG_GUARDIANS:		Cmd.ARG_GUARDIAN,
  Cmd.ARG_GUESTUSERS:		Cmd.ARG_GUESTUSER,
  Cmd.ARG_HOLD:			Cmd.ARG_VAULTHOLD,
  Cmd.ARG_HOLDS:		Cmd.ARG_VAULTHOLD,
  Cmd.ARG_IMAP4:		Cmd.ARG_IMAP,
  Cmd.ARG_INVITEGUARDIAN:	Cmd.ARG_GUARDIANINVITATION,
  Cmd.ARG_LABELS:		Cmd.ARG_LABEL,
  Cmd.ARG_LICENCE:		Cmd.ARG_LICENSE,
  Cmd.ARG_LICENCES:		Cmd.ARG_LICENSE,
  Cmd.ARG_LICENSES:		Cmd.ARG_LICENSE,
  Cmd.ARG_MEETCONFERENCES:	Cmd.ARG_MEETCONFERENCE,
  Cmd.ARG_MEETPARTICIPANTS:	Cmd.ARG_MEETPARTICIPANT,
  Cmd.ARG_MEETRECORDINGS:	Cmd.ARG_MEETRECORDING,
  Cmd.ARG_MEETTRANSCRIPTS:	Cmd.ARG_MEETTRANSCRIPT,
  Cmd.ARG_MEETSPACES:		Cmd.ARG_MEETSPACE,
  Cmd.ARG_MEMBER:		Cmd.ARG_GROUPMEMBERS,
  Cmd.ARG_MEMBERS:		Cmd.ARG_GROUPMEMBERS,
  Cmd.ARG_MESSAGES:		Cmd.ARG_MESSAGE,
  Cmd.ARG_NOTES:		Cmd.ARG_NOTE,
  Cmd.ARG_NOTEACLS:		Cmd.ARG_NOTEACL,
  Cmd.ARG_NOTESACL:		Cmd.ARG_NOTEACL,
  Cmd.ARG_NOTESACLS:		Cmd.ARG_NOTEACL,
  Cmd.ARG_NOTEATTACHMENTS:	Cmd.ARG_NOTEATTACHMENT,
  Cmd.ARG_OAUTH:		Cmd.ARG_TOKEN,
  Cmd.ARG_OTHERCONTACTS:	Cmd.ARG_OTHERCONTACT,
  Cmd.ARG_OUTOFOFFICES:		Cmd.ARG_OUTOFOFFICE,
  Cmd.ARG_PEOPLECONTACTS:	Cmd.ARG_PEOPLECONTACT,
  Cmd.ARG_PEOPLECONTACTGROUPS:	Cmd.ARG_PEOPLECONTACTGROUP,
  Cmd.ARG_PEOPLECONTACTPHOTOS:	Cmd.ARG_PEOPLECONTACTPHOTO,
  Cmd.ARG_PEOPLE:		Cmd.ARG_PEOPLEPROFILE,
  Cmd.ARG_PEOPLEPROFILES:	Cmd.ARG_PEOPLEPROFILE,
  Cmd.ARG_PERMISSIONS:		Cmd.ARG_PERMISSION,
  Cmd.ARG_POP3:			Cmd.ARG_POP,
  Cmd.ARG_SECCALS:		Cmd.ARG_CALENDAR,
  Cmd.ARG_SHAREDDRIVES:		Cmd.ARG_SHAREDDRIVE,
  Cmd.ARG_SHEETS:		Cmd.ARG_SHEET,
  Cmd.ARG_SHEETRANGES:		Cmd.ARG_SHEETRANGE,
  Cmd.ARG_SIG:			Cmd.ARG_SIGNATURE,
  Cmd.ARG_SITES:		Cmd.ARG_SITE,
  Cmd.ARG_SITEACLS:		Cmd.ARG_SITEACL,
  Cmd.ARG_SMIMES:		Cmd.ARG_SMIME,
  Cmd.ARG_TAGMANAGERACCOUNTS:	Cmd.ARG_TAGMANAGERACCOUNT,
  Cmd.ARG_TAGMANAGERCONTAINERS:	Cmd.ARG_TAGMANAGERCONTAINER,
  Cmd.ARG_TAGMANAGERPERMISSIONS:	Cmd.ARG_TAGMANAGERPERMISSION,
  Cmd.ARG_TAGMANAGERTAGS:	Cmd.ARG_TAGMANAGERTAG,
  Cmd.ARG_TAGMANAGERWORKSPACES:	Cmd.ARG_TAGMANAGERWORKSPACE,
  Cmd.ARG_TASKS:		Cmd.ARG_TASK,
  Cmd.ARG_TASKLISTS:		Cmd.ARG_TASKLIST,
  Cmd.ARG_TEAMDRIVE:		Cmd.ARG_SHAREDDRIVE,
  Cmd.ARG_TEAMDRIVES:		Cmd.ARG_SHAREDDRIVE,
  Cmd.ARG_TEAMDRIVEACLS:	Cmd.ARG_SHAREDDRIVEACLS,
  Cmd.ARG_TEAMDRIVEINFO:	Cmd.ARG_SHAREDDRIVEINFO,
  Cmd.ARG_TEAMDRIVEORGANIZERS:	Cmd.ARG_SHAREDDRIVEORGANIZERS,
  Cmd.ARG_TEAMDRIVETHEMES:	Cmd.ARG_SHAREDDRIVETHEMES,
  Cmd.ARG_THREADS:		Cmd.ARG_THREAD,
  Cmd.ARG_TOKENS:		Cmd.ARG_TOKEN,
  Cmd.ARG_USERS:		Cmd.ARG_USER,
  Cmd.ARG_VAULTHOLDS:		Cmd.ARG_VAULTHOLD,
  Cmd.ARG_VERIFICATIONCODES:	Cmd.ARG_BACKUPCODE,
  Cmd.ARG_WEBMASTERSITES:	Cmd.ARG_WEBMASTERSITE,
  Cmd.ARG_WEBRESOURCES: 	Cmd.ARG_WEBRESOURCE,
  Cmd.ARG_WORKINGLOCATIONS:	Cmd.ARG_WORKINGLOCATION,
  Cmd.ARG_YOUTUBECHANNELS:	Cmd.ARG_YOUTUBECHANNEL,
  }

def showAPICallsRetryData():
  if GC.Values.get(GC.SHOW_API_CALLS_RETRY_DATA) and GM.Globals[GM.API_CALLS_RETRY_DATA]:
    Ind.Reset()
    writeStderr(Msg.API_CALLS_RETRY_DATA)
    Ind.Increment()
    for k, v in sorted(GM.Globals[GM.API_CALLS_RETRY_DATA].items()):
      m, s = divmod(int(v[1]), 60)
      h, m = divmod(m, 60)
      writeStderr(formatKeyValueList(Ind.Spaces(), [k, f'{v[0]}/{h}:{m:02d}:{s:02d}'], '\n'))
    Ind.Decrement()

def adjustRedirectedSTDFilesIfNotMultiprocessing():
  def adjustRedirectedSTDFile(stdtype):
    rdFd = GM.Globals[stdtype].get(GM.REDIRECT_FD)
    rdMultiFd = GM.Globals[stdtype].get(GM.REDIRECT_MULTI_FD)
    if rdFd and rdMultiFd and rdFd != rdMultiFd:
      try:
        rdFd.write(rdMultiFd.getvalue())
        rdMultiFd.close()
        GM.Globals[stdtype][GM.REDIRECT_MULTI_FD] = rdFd
        if (stdtype == GM.STDOUT) and (GM.Globals.get(GM.SAVED_STDOUT) is not None):
          sys.stdout = rdFd
      except IOError as e:
        systemErrorExit(FILE_ERROR_RC, e)

  adjustRedirectedSTDFile(GM.STDOUT)
  if GM.Globals[GM.STDERR].get(GM.REDIRECT_NAME) != 'stdout':
    adjustRedirectedSTDFile(GM.STDERR)
  else:
    GM.Globals[GM.STDERR][GM.REDIRECT_MULTI_FD] = GM.Globals[GM.STDOUT][GM.REDIRECT_MULTI_FD]

def closeSTDFilesIfNotMultiprocessing(closeSTD):
  def closeSTDFile(stdtype, stdfile):
    rdFd = GM.Globals[stdtype].get(GM.REDIRECT_FD)
    rdMultiFd = GM.Globals[stdtype].get(GM.REDIRECT_MULTI_FD)
    if rdFd and rdMultiFd and (rdFd == rdMultiFd) and (rdFd != stdfile):
      try:
        rdFd.flush()
        if closeSTD:
          rdFd.close()
      except BrokenPipeError:
        pass

  closeSTDFile(GM.STDOUT, sys.stdout)
  if GM.Globals[GM.STDERR].get(GM.REDIRECT_NAME) != 'stdout':
    closeSTDFile(GM.STDERR, sys.stderr)

# Process GAM command
def ProcessGAMCommand(args, processGamCfg=True, inLoop=False, closeSTD=True):
  setSysExitRC(0)
  Cmd.InitializeArguments(args)
  Ind.Reset()
  try:
    logCmd = Cmd.QuotedArgumentList(args)
    if checkArgumentPresent(Cmd.LOOP_CMD):
      if processGamCfg and (not SetGlobalVariables()):
        sys.exit(GM.Globals[GM.SYSEXITRC])
      doLoop(logCmd)
      sys.exit(GM.Globals[GM.SYSEXITRC])
    if processGamCfg and (not SetGlobalVariables()):
      sys.exit(GM.Globals[GM.SYSEXITRC])
    if checkArgumentPresent(Cmd.LOOP_CMD):
      doLoop(logCmd)
      sys.exit(GM.Globals[GM.SYSEXITRC])
    if not Cmd.ArgumentsRemaining():
      doUsage()
      sys.exit(GM.Globals[GM.SYSEXITRC])
    CL_command = getChoice(BATCH_CSV_COMMANDS, defaultChoice=None)
    if CL_command:
      Act.Set(BATCH_CSV_COMMANDS[CL_command][CMD_ACTION])
      if GM.Globals[GM.CMDLOG_LOGGER]:
        writeGAMCommandLog(GM.Globals, logCmd, '*')
      BATCH_CSV_COMMANDS[CL_command][CMD_FUNCTION]()
      sys.exit(GM.Globals[GM.SYSEXITRC])
    CL_command = getChoice(MAIN_COMMANDS, defaultChoice=None)
    if CL_command:
      adjustRedirectedSTDFilesIfNotMultiprocessing()
      Act.Set(MAIN_COMMANDS[CL_command][CMD_ACTION])
      MAIN_COMMANDS[CL_command][CMD_FUNCTION]()
      sys.exit(GM.Globals[GM.SYSEXITRC])
    CL_command = getChoice(MAIN_COMMANDS_WITH_OBJECTS, defaultChoice=None)
    if CL_command:
      adjustRedirectedSTDFilesIfNotMultiprocessing()
      Act.Set(MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_ACTION])
      CL_objectName = getChoice(MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION], choiceAliases=MAIN_COMMANDS_OBJ_ALIASES)
      MAIN_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION][CL_objectName]()
      sys.exit(GM.Globals[GM.SYSEXITRC])
    CL_command = getChoice(COMMANDS_MAP, choiceAliases=COMMANDS_ALIASES, defaultChoice=None)
    if CL_command:
      adjustRedirectedSTDFilesIfNotMultiprocessing()
      COMMANDS_MAP[CL_command]()
      sys.exit(GM.Globals[GM.SYSEXITRC])
    GM.Globals[GM.ENTITY_CL_START] = Cmd.Location()
    entityType, entityList = getEntityToModify(crosAllowed=True, delayGet=True)
    if entityType == Cmd.ENTITY_USERS:
      CL_command = getChoice(list(USER_COMMANDS)+list(USER_COMMANDS_WITH_OBJECTS), choiceAliases=USER_COMMANDS_ALIASES)
      if (CL_command != 'list') and (GC.Values[GC.AUTO_BATCH_MIN] > 0):
        _, count, entityList = getEntityArgument(entityList)
        if count > GC.Values[GC.AUTO_BATCH_MIN]:
          if GM.Globals[GM.CMDLOG_LOGGER]:
            writeGAMCommandLog(GM.Globals, logCmd, '*')
          doAutoBatch(Cmd.ENTITY_USER, entityList, CL_command)
          sys.exit(GM.Globals[GM.SYSEXITRC])
      adjustRedirectedSTDFilesIfNotMultiprocessing()
      if CL_command in USER_COMMANDS:
        Act.Set(USER_COMMANDS[CL_command][CMD_ACTION])
        USER_COMMANDS[CL_command][CMD_FUNCTION](entityList)
      else:
        Act.Set(USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_ACTION])
        CL_objectName = getChoice(USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION], choiceAliases=USER_COMMANDS_OBJ_ALIASES,
                                  defaultChoice=[Cmd.ARG_USER, NO_DEFAULT][CL_command != 'print'])
        USER_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION][CL_objectName](entityList)
    else:
      CL_command = getChoice(list(CROS_COMMANDS)+list(CROS_COMMANDS_WITH_OBJECTS))
      if (CL_command != 'list') and (GC.Values[GC.AUTO_BATCH_MIN] > 0):
        _, count, entityList = getEntityArgument(entityList)
        if count > GC.Values[GC.AUTO_BATCH_MIN]:
          if GM.Globals[GM.CMDLOG_LOGGER]:
            writeGAMCommandLog(GM.Globals, logCmd, '*')
          doAutoBatch(Cmd.ENTITY_CROS, entityList, CL_command)
          sys.exit(GM.Globals[GM.SYSEXITRC])
      adjustRedirectedSTDFilesIfNotMultiprocessing()
      if CL_command in CROS_COMMANDS:
        Act.Set(CROS_COMMANDS[CL_command][CMD_ACTION])
        CROS_COMMANDS[CL_command][CMD_FUNCTION](entityList)
      else:
        Act.Set(CROS_COMMANDS_WITH_OBJECTS[CL_command][CMD_ACTION])
        CL_objectName = getChoice(CROS_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION], choiceAliases=CROS_COMMANDS_OBJ_ALIASES,
                                  defaultChoice=NO_DEFAULT)
        CROS_COMMANDS_WITH_OBJECTS[CL_command][CMD_FUNCTION][CL_objectName](entityList)
    sys.exit(GM.Globals[GM.SYSEXITRC])
  except KeyboardInterrupt:
    batchWriteStderr('\nControl-C\n')
    setSysExitRC(KEYBOARD_INTERRUPT_RC)
    showAPICallsRetryData()
    adjustRedirectedSTDFilesIfNotMultiprocessing()
  except OSError as e:
    printErrorMessage(SOCKET_ERROR_RC, str(e))
    showAPICallsRetryData()
    adjustRedirectedSTDFilesIfNotMultiprocessing()
  except MemoryError:
    printErrorMessage(MEMORY_ERROR_RC, Msg.GAM_OUT_OF_MEMORY)
    showAPICallsRetryData()
    adjustRedirectedSTDFilesIfNotMultiprocessing()
  except (GAPI.permissionDenied, GAPI.accessNotConfigured):
    SvcAcctAPIDisabledExit()
  except SystemExit as e:
    GM.Globals[GM.SYSEXITRC] = e.code
    if GM.Globals[GM.SYSEXITRC] != STDOUT_STDERR_ERROR_RC and not inLoop:
      showAPICallsRetryData()
      try:
        adjustRedirectedSTDFilesIfNotMultiprocessing()
      except SystemExit:
        pass
  except Exception:
    print_exc(file=sys.stderr)
    setSysExitRC(UNKNOWN_ERROR_RC)
    showAPICallsRetryData()
    adjustRedirectedSTDFilesIfNotMultiprocessing()
  if processGamCfg:
    if not inLoop:
      if GM.Globals.get(GM.SAVED_STDOUT) is not None:
        sys.stdout = GM.Globals[GM.SAVED_STDOUT]
      closeSTDFilesIfNotMultiprocessing(closeSTD)
  if GM.Globals[GM.PID] == 0 and GM.Globals[GM.CMDLOG_LOGGER]:
    writeGAMCommandLog(GM.Globals, logCmd, GM.Globals[GM.SYSEXITRC])
    if not inLoop:
      closeGAMCommandLog(GM.Globals)
  return GM.Globals[GM.SYSEXITRC]

# Process GAM command
def CallGAMCommand(args, processGamCfg=True, inLoop=False, closeSTD=False):
  return ProcessGAMCommand(args, processGamCfg=processGamCfg, inLoop=inLoop, closeSTD=closeSTD)
