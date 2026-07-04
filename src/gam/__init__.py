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
import http.client
import importlib
import logging
import os
import platform
import re
import sys
import types

# disable legacy stuff we don't use and isn't secure
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = "1"

# Add package directory to sys.path for source installs (not needed for frozen/PyInstaller builds)
if not getattr(sys, 'frozen', False):
  sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import httplib2
httplib2.RETRIES = 5

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg

from gam.util.api import SvcAcctAPIDisabledExit  # noqa: E402
from gam.util.email import send_email  # noqa: E402


from gam.constants import *

from util.fileio import adjustRedirectedSTDFilesIfNotMultiprocessing, closeSTDFilesIfNotMultiprocessing  # noqa: E402

from gam.var import Act, Cmd, Ent, Ind  # noqa: E402,F401

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


from util.output import showAPICallsRetryData  # noqa: E402


# Multiprocessing lock
mplock = None

# Imports used by __init__.py's own dispatch tables and functions
from util.output import setSysExitRC, printErrorMessage  # noqa: E402
from util.args import getChoice  # noqa: E402
from util.args import checkArgumentPresent, NO_DEFAULT  # noqa: E402
from util.connection import doCheckConnection, doComment, doVersion, doUsage  # noqa: E402
from util.entity import getEntityArgument, getEntityToModify  # noqa: E402
from util.config import SetGlobalVariables  # noqa: E402
from util.fileio import closeGAMCommandLog, writeGAMCommandLog  # noqa: E402
from util.batch import (  # noqa: E402
    batchWriteStderr, doBatch, doThreadBatch, doAutoBatch,
    doCSV, doCSVTest, doLoop, doListType, doListCrOS, doListUser,
    showCountCrOS, showCountUser,
)


# Command module imports
from gam.cmd.admin import (
    doCreateAdmin,
    doCreateUpdateAdminRoles,
    doDeleteAdmin,
    doDeleteAdminRole,
    doInfoPrintShowAdminRoles,
    doPrintShowAdmins,
    doPrintShowPrivileges,
)
from gam.cmd.alerts import (
    doClearAlertSettings,
    doCreateAlertFeedback,
    doDeleteOrUndeleteAlert,
    doInfoAlert,
    doPrintShowAlertFeedback,
    doPrintShowAlerts,
    doShowAlertSettings,
    doUpdateAlertSettings,
)
from gam.cmd.aliases import (
    deleteUsersAliases,
    doCreateUpdateAliases,
    doDeleteAliases,
    doInfoAliases,
    doPrintAddresses,
    doPrintAliases,
    doRemoveAliases,
)
from gam.cmd.analytics import (
    printShowAnalyticAccountSummaries,
    printShowAnalyticAccounts,
    printShowAnalyticDatastreams,
    printShowAnalyticProperties,
)
from gam.cmd.audit import doCreateMonitor, doDeleteMonitor, doShowMonitors
from gam.cmd.browsers import (
    doCreateBrowserToken,
    doCreateChromeProfileCommand,
    doDeleteBrowsers,
    doDeleteChromeProfile,
    doInfoBrowsers,
    doInfoChromeProfile,
    doInfoChromeProfileCommand,
    doMoveBrowsers,
    doPrintShowBrowserTokens,
    doPrintShowBrowsers,
    doPrintShowChromeProfileCommands,
    doPrintShowChromeProfiles,
    doRevokeBrowserToken,
    doUpdateBrowsers,
)
from gam.cmd.caa import (
    doCreateCAALevel,
    doDeleteCAALevel,
    doPrintShowCAALevels,
    doUpdateCAALevel,
)
from gam.cmd.calendar import (
    doCalendarsCreateACL,
    doCalendarsCreateACLs,
    doCalendarsCreateEvent,
    doCalendarsDeleteACL,
    doCalendarsDeleteACLs,
    doCalendarsDeleteEvents,
    doCalendarsDeleteEventsOld,
    doCalendarsEmptyTrash,
    doCalendarsImportEvent,
    doCalendarsInfoACLs,
    doCalendarsInfoEvents,
    doCalendarsModifySettings,
    doCalendarsMoveEvents,
    doCalendarsMoveEventsOld,
    doCalendarsPrintShowACLs,
    doCalendarsPrintShowEvents,
    doCalendarsPrintShowSettings,
    doCalendarsPurgeEvents,
    doCalendarsUpdateACL,
    doCalendarsUpdateACLs,
    doCalendarsUpdateEvents,
    doCalendarsUpdateEventsOld,
    doCalendarsWipeEvents,
    doResourceCreateCalendarACLs,
    doResourceDeleteCalendarACLs,
    doResourceInfoCalendarACLs,
    doResourcePrintShowCalendarACLs,
    doResourceUpdateCalendarACLs,
)
from gam.cmd.chat import (
    createChatEmoji,
    createChatMember,
    createChatMessage,
    createChatSpace,
    createUpdateChatSection,
    deleteChatEmoji,
    deleteChatMessage,
    deleteChatSection,
    deleteChatSpace,
    deleteUpdateChatMember,
    doCreateChatMessage,
    doDeleteChatMessage,
    doInfoChatEvent,
    doInfoChatMember,
    doInfoChatMessage,
    doInfoChatSpace,
    doPrintShowChatMembers,
    doPrintShowChatSpaces,
    doSetupChat,
    doUpdateChatMessage,
    infoChatEmoji,
    infoChatEvent,
    infoChatMember,
    infoChatMessage,
    infoChatSpace,
    infoChatSpaceDM,
    moveShowChatSectionItem,
    printShowChatEmojis,
    printShowChatEvents,
    printShowChatMembers,
    printShowChatMessages,
    printShowChatSearchMessages,
    printShowChatSectionItems,
    printShowChatSections,
    printShowChatSpaces,
    syncChatMembers,
    updateChatMessage,
    updateChatSpace,
)
from gam.cmd.chromeapps import (
    doInfoChromeApp,
    doPrintChromeSnValidity,
    doPrintShowChromeAppDevices,
    doPrintShowChromeApps,
    doPrintShowChromeAues,
    doPrintShowChromeDeviceCounts,
    doPrintShowChromeHistory,
    doPrintShowChromeNeedsAttn,
    doPrintShowChromeVersions,
)
from gam.cmd.chromepolicies import (
    doCreateChromeNetwork,
    doCreateChromePolicyImage,
    doDeleteChromeNetwork,
    doDeleteChromePolicy,
    doInfoChromePolicySchemas,
    doPrintShowChromePolicies,
    doPrintShowChromePolicySchemas,
    doUpdateChromePolicy,
)
from gam.cmd.cidevices import (
    doApproveCIDeviceUser,
    doBlockCIDeviceUser,
    doCancelWipeCIDevice,
    doCancelWipeCIDeviceUser,
    doCreateCIDevice,
    doDeleteCIDevice,
    doDeleteCIDeviceUser,
    doInfoCIDevice,
    doInfoCIDeviceUser,
    doInfoCIDeviceUserState,
    doPrintCIDeviceUsers,
    doPrintCIDevices,
    doSyncCIDevices,
    doUpdateCIDevice,
    doUpdateCIDeviceUser,
    doUpdateCIDeviceUserState,
    doWipeCIDevice,
    doWipeCIDeviceUser,
)
from gam.cmd.cigroups import (
    doCreateCIGroup,
    doCreateUpdateCIPolicy,
    doDeleteCIGroups,
    doDeleteCIPolicies,
    doInfoCIGroupMembers,
    doInfoCIGroups,
    doInfoCIPolicies,
    doPrintCIGroupMembers,
    doPrintCIGroups,
    doPrintShowCIPolicies,
    doShowCIGroupMembers,
    doUpdateCIGroups,
    infoCIGroupMembers,
)
from gam.cmd.ciuserinvitations import (
    checkCIUserIsInvitable,
    doCIUserInvitationsAction,
    doCheckCIUserInvitations,
    doInfoCIUserInvitations,
    doPrintShowCIUserInvitations,
)
from gam.cmd.cloudstorage import doCopyCloudStorageBucket, doDownloadCloudStorageBucket, doDownloadCloudStorageFile
from gam.cmd.contacts import (
    doClearDomainContacts,
    doCreateDomainContact,
    doDedupDomainContacts,
    doDeleteDomainContacts,
    doInfoDomainContacts,
    doPrintShowDomainContacts,
    doUpdateDomainContacts,
)
from gam.cmd.courses import (
    acceptClassroomInvitations,
    cancelGuardianInvitations,
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
    doPrintCourseWork,
    doPrintCourses,
    doPrintShowClassroomInvitations,
    doPrintShowGuardians,
    doProcessCourseStudentGroupMembers,
    doUpdateCourse,
    doUpdateCourseStudentGroups,
    doUpdateCourses,
    inviteGuardians,
    printShowClassroomInvitations,
    printShowClassroomProfile,
    printShowGuardians,
    syncGuardians,
)
from gam.cmd.cros import (
    doGetCommandResultCrOSDevices,
    doGetCrOSDeviceFiles,
    doInfoCrOSDevices,
    doInfoPrintShowCrOSTelemetry,
    doIssueCommandCrOSDevices,
    doPrintCrOSActivity,
    doPrintCrOSDevices,
    doPrintCrOSEntity,
    doUpdateCrOSDevices,
    getCommandResultCrOSDevices,
    getCrOSDeviceFiles,
    infoCrOSDevices,
    issueCommandCrOSDevices,
    updateCrOSDevices,
)
from gam.cmd.customer import (
    doInfoCustomer,
    doInfoDomain,
    doInfoInstance,
    doPrintShowDomains,
    doUpdateCustomer,
)
from gam.cmd.datatransfer import (
    doCreateDataTransfer,
    doInfoDataTransfer,
    doPrintShowDataTransfers,
    doShowTransferApps,
)
from gam.cmd.delegates import printShowContactDelegates, processContactDelegates
from gam.cmd.domains import (
    doCreateDomain,
    doCreateDomainAlias,
    doDeleteDomain,
    doDeleteDomainAlias,
    doInfoDomainAlias,
    doPrintShowDomainAliases,
    doUpdateDomain,
)
from gam.cmd.drive import (
    checkDriveFileShortcut,
    claimOwnership,
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
    doShowSharedDriveThemes,
    doUpdateDriveFileACLs,
    doUpdateSharedDrive,
    emptyDriveTrash,
    getDriveFile,
    getGoogleDocument,
    hideUnhideSharedDrive,
    infoDriveFileACLs,
    infoDriveLabels,
    infoSharedDrive,
    moveDriveFile,
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
    purgeDriveFile,
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
)
from gam.cmd.gmail import (
    archiveMessages,
    createCSEKeyPair,
    createFilter,
    createForm,
    createForwardingAddresses,
    createLabel,
    createLabelList,
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
    deleteLabelList,
    deleteSmime,
    draftMessage,
    exportMessages,
    exportThreads,
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
    setForward,
    setImap,
    setLanguage,
    setPop,
    setSignature,
    setVacation,
    updateDelegates,
    updateForm,
    updateLabelSettings,
    updateLabelSettingsById,
    updateLabels,
    updateSmime,
    watchGmail,
)
from gam.cmd.groups import (
    doCreateGroup,
    doDeleteGroups,
    doInfoGroupMembers,
    doInfoGroups,
    doPrintGroupMembers,
    doPrintGroups,
    doPrintShowGroupTree,
    doShowGroupMembers,
    doUpdateGroups,
    infoGroupMembers,
)
from gam.cmd.licenses import doPrintLicenses, doShowLicenses
from gam.cmd.meet import (
    createMeetSpace,
    endMeetConference,
    infoMeetSpace,
    printShowMeetConferences,
    printShowMeetParticipants,
    printShowMeetRecordings,
    printShowMeetTranscripts,
    updateMeetSpace,
)
from gam.cmd.mobile import (
    doDeleteMobileDevices,
    doInfoMobileDevices,
    doPrintMobileDevices,
    doUpdateMobileDevices,
)
from gam.cmd.notes import (
    createNote,
    createNotesACLs,
    deleteInfoNotes,
    deleteNotesACLs,
    getNoteAttachments,
    printShowNotes,
)
from gam.cmd.oauth import (
    Credentials,
    doOAuthCreate,
    doOAuthDelete,
    doOAuthExport,
    doOAuthInfo,
    doOAuthRefresh,
    doOAuthUpdate,
)
from gam.cmd.orgunits import (
    doCheckOrgUnit,
    doCreateOrg,
    doDeleteOrg,
    doDeleteOrgs,
    doInfoOrg,
    doInfoOrgs,
    doPrintOrgs,
    doShowOrgTree,
    doUpdateOrg,
    doUpdateOrgs,
)
from gam.cmd.people import (
    clearUserPeopleContacts,
    copyUserPeopleOtherContacts,
    createUserPeopleContact,
    createUserPeopleContactGroup,
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
    getUserPeopleContactPhoto,
    infoUserPeopleContactGroups,
    infoUserPeopleContacts,
    printShowUserPeopleContactGroups,
    printShowUserPeopleContacts,
    printShowUserPeopleOtherContacts,
    printShowUserPeopleProfiles,
    processUserPeopleOtherContacts,
    updateUserPeopleContactGroup,
    updateUserPeopleContactPhoto,
    updateUserPeopleContacts,
)
from gam.cmd.printers import (
    doCreatePrinter,
    doDeletePrinter,
    doInfoPrinter,
    doPrintShowPrinterModels,
    doPrintShowPrinters,
    doUpdatePrinter,
)
from gam.cmd.project import (
    checkServiceAccount,
    doCheckUpdateSvcAcct,
    doCreateGCPFolder,
    doCreateGCPServiceAccount,
    doCreateProject,
    doCreateSvcAcct,
    doCreateSvcAcctKeys,
    doDeleteProject,
    doDeleteSvcAcct,
    doDeleteSvcAcctKeys,
    doEnableAPIs,
    doInfoCurrentProjectId,
    doInfoCustomerId,
    doInfoGCPOrgId,
    doPrintShowProjects,
    doPrintShowSvcAccts,
    doProcessSvcAcctKeys,
    doReplaceSvcAcctKeys,
    doShowSvcAcctKeys,
    doUpdateProject,
    doUpdateSvcAcctKeys,
    doUploadSvcAcctKeys,
    doUseProject,
)
from gam.cmd.reports import doReport, doWhatIs
from gam.cmd.reseller import (
    doCreateResoldCustomer,
    doCreateResoldSubscription,
    doDeleteResoldSubscription,
    doInfoResoldCustomer,
    doInfoResoldSubscription,
    doPrintShowChannelCustomerEntitlements,
    doPrintShowChannelCustomers,
    doPrintShowChannelOffers,
    doPrintShowChannelProducts,
    doPrintShowChannelSKUs,
    doPrintShowResoldSubscriptions,
    doUpdateResoldCustomer,
    doUpdateResoldSubscription,
)
from gam.cmd.resources import (
    doCreateBuilding,
    doCreateFeature,
    doCreateResourceCalendar,
    doDeleteBuilding,
    doDeleteFeature,
    doDeleteResourceCalendar,
    doDeleteResourceCalendars,
    doInfoBuilding,
    doInfoResourceCalendar,
    doInfoResourceCalendars,
    doPrintShowBuildings,
    doPrintShowFeatures,
    doPrintShowResourceCalendars,
    doUpdateBuilding,
    doUpdateFeature,
    doUpdateResourceCalendar,
    doUpdateResourceCalendars,
)
from gam.cmd.schemas import (
    doCreateUpdateUserSchemas,
    doDeleteUserSchemas,
    doInfoUserSchemas,
    doPrintShowUserSchemas,
)
from gam.cmd.send_email import doSendEmail, doSendReply
from gam.cmd.sites import (
    deprecatedDomainSites,
    deprecatedUserSites,
    doCreateSiteVerification,
    doInfoSiteVerification,
    doUpdateSiteVerification,
    printShowBusinessProfileAccounts,
    printShowWebMasterSites,
    printShowWebResources,
)
from gam.cmd.sso import (
    doCreateInboundSSOAssignment,
    doCreateInboundSSOCredential,
    doCreateInboundSSOProfile,
    doDeleteInboundSSOAssignment,
    doDeleteInboundSSOCredential,
    doDeleteInboundSSOProfile,
    doInfoInboundSSOAssignment,
    doInfoInboundSSOCredential,
    doInfoInboundSSOProfile,
    doPrintShowInboundSSOAssignments,
    doPrintShowInboundSSOCredentials,
    doPrintShowInboundSSOProfiles,
    doUpdateInboundSSOAssignment,
    doUpdateInboundSSOProfile,
)
from gam.cmd.tasks import (
    importTasklist,
    printShowTagManagerAccounts,
    printShowTagManagerContainers,
    printShowTagManagerPermissions,
    printShowTagManagerTags,
    printShowTagManagerWorkspaces,
    printShowTasklists,
    printShowTasks,
    processTasklists,
    processTasks,
)
from gam.cmd.userop import (
    addUserToGroups,
    appendSheetRanges,
    checkUserInGroups,
    clearSheetRanges,
    createLicense,
    createSheet,
    deleteLicense,
    deletePhoto,
    deleteTokens,
    deleteUserFromGroups,
    deprovisionUser,
    doPrintShowTokens,
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
from gam.cmd.users import (
    deleteUsers,
    doCheckUserSuspended,
    doCreateGuestUser,
    doCreateUser,
    doDeleteUser,
    doDeleteUsers,
    doInfoUser,
    doInfoUsers,
    doPrintUserCountsByOrgUnit,
    doPrintUserEntity,
    doPrintUserList,
    doPrintUsers,
    doSuspendUnsuspendUser,
    doSuspendUnsuspendUsers,
    doUndeleteUser,
    doUndeleteUsers,
    doUpdateUser,
    doUpdateUsers,
    infoUsers,
    signoutTurnoff2SVUsers,
    suspendUnsuspendUsers,
    undeleteUsers,
    updateUsers,
    waitForMailbox,
)
from gam.cmd.userservices import (
    addCreateCalendars,
    createCalendarACLs,
    createCalendarEvent,
    createFocusTime,
    createOutOfOffice,
    createWorkingLocation,
    deleteASP,
    deleteBackupCodes,
    deleteCalendarACLs,
    deleteCalendarEvents,
    deleteCalendars,
    deleteFocusTime,
    deleteOutOfOffice,
    deleteWorkingLocation,
    doCalendarsTransferOwnership,
    emptyCalendarTrash,
    importCalendarEvent,
    infoCalendarACLs,
    infoCalendarEvents,
    infoCalendars,
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
    printShowWorkingLocation,
    printShowYouTubeChannel,
    purgeCalendarEvents,
    removeCalendars,
    updateBackupCodes,
    updateCalendarACLs,
    updateCalendarAttendees,
    updateCalendarEvents,
    updateCalendars,
    wipeCalendarEvents,
)
from gam.cmd.vault import (
    doCloseVaultMatter,
    doCopyVaultExport,
    doCopyVaultQuery,
    doCreateVaultExport,
    doCreateVaultHold,
    doCreateVaultMatter,
    doCreateVaultQuery,
    doDeleteVaultExport,
    doDeleteVaultHold,
    doDeleteVaultMatter,
    doDeleteVaultQuery,
    doDownloadVaultExport,
    doInfoVaultExport,
    doInfoVaultHold,
    doInfoVaultMatter,
    doInfoVaultQuery,
    doPrintShowVaultExports,
    doPrintShowVaultHolds,
    doPrintShowVaultMatters,
    doPrintShowVaultQueries,
    doPrintVaultCounts,
    doReopenVaultMatter,
    doUndeleteVaultMatter,
    doUpdateVaultHold,
    doUpdateVaultMatter,
    printShowUserVaultHolds,
)
from gam.cmd.yubikey import doResetYubiKeyPIV


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
     {Cmd.ARG_RESETPIV:		doResetYubiKeyPIV,  # from cmd/yubikey
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

from gam.cmd.audit import processAuditCommands
from gam.cmd.oauth import processOauthCommands
from gam.cmd.calendar import processCalendarsCommands, processResourceCommands, processResourcesCommands
from gam.cmd.courses.participants import processCourseCommands, processCoursesCommands

# Multi-step commands (audit, oauth, calendars, courses, resources)
COMMANDS_MAP = {
  'oauth':			processOauthCommands,
  'audit':			processAuditCommands,
  'calendars':			processCalendarsCommands,
  'course':			processCourseCommands,
  'courses':			processCoursesCommands,
  'resource':			processResourceCommands,
  'resources':			processResourcesCommands,
  }

# Command name aliases
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

# Call GAM command (used by batch/loop to invoke sub-commands)
def CallGAMCommand(args, processGamCfg=True, inLoop=False, closeSTD=False):
  return ProcessGAMCommand(args, processGamCfg=processGamCfg, inLoop=inLoop, closeSTD=closeSTD)

