# Cloud Identity Policies
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Policies](#policies)
- [Display Cloud Identity Policies](#display-cloud-identity-policies)

## API documentation
* https://cloud.google.com/identity/docs/concepts/overview-policies
* https://cloud.google.com/identity/docs/reference/rest/v1beta1/policies/list

## Notes
To use these commands you must update your client access authentication.
```
gam oauth create
...
[*] 19)  Cloud Identity - Policy
```

## Definitions
```
<CIPolicyName> ::= policies/<String>
```

## Policies
These are the supported policies GAM can show today.
```
user_takeout_status (is takeout enabled for service)
  blogger
  books
  location_history
  maps
  pay
  photos
  play
  play_console
  youtube
service_status (is service enabled)
  ad_manager
  ads
  adsense
  alerts
  analytics
  applied_digital_skills
  appsheet
  arts_and_culture
  beyondcorp_enterprise
  blogger
  bookmarks
  books
  calendar
  campaign_manager
  chat
  chrome_canvas
  chrome_remote_desktop
  chrome_sync
  chrome_web_store
  classroom
  cloud
  cloud_search
  colab
  cs_first
  data_studio
  developers
  domains
  drive_and_docs
  earth
  enterprise_service_restrictions
  experimental_apps
  feedburner
  fi
  gmail
  groups
  groups_for_business
  jamboard
  keep
  location_history
  managed_play
  maps
  material_gallery
  meet
  merchant_center
  messages
  migrate
  my_business
  my_maps
  news
  partner_dash
  pay
  pay_for_business
  photos
  pinpoint
  play
  play_books_partner_center
  play_console
  public_data
  question_hub
  scholar_profiles
  search_ads_360
  search_and_assistant
  search_console
  sites
  socratic
  takeout
  tasks
  third_party_app_backups
  translate
  trips
  vault
  voice
  work_insights
  youtube
calendar.appointment_schedules
  enablePayments
chat.chat_apps_access
  enableApps
  enableWebhooks
chat.chat_file_sharing
  externalFileSharing
  internalFileSharing
chat.chat_history
  enableChatHistory
  historyOnByDefault
  allowUserModification
chat.external_chat_restriction
  allowExternalChat
chat.space_history
  historyState
classroom.api_data_access
  enableApiAccess
classroom.class_membership
  whoCanJoinClasses
  whichClassesCanUsersJoin
classroom.guardian_access
  allowAccess
  whoCanManageGuardianAccess
classroom.originality_reports
  enableOriginalityReportsSchoolMatches
classroom.roster_import
  rosterImportOption
classroom.student_unenrollment
  whoCanUnenrollStudents
classroom.teacher_permissions
  whoCanCreateClasses
cloud_sharing_options.cloud_data_sharing
  sharingOptions
detector.regular_expression
  displayName
  regularExpression
  createTime
  updateTime
detector.word_list
  displayName
  wordList
  createTime
  updateTime
  description
drive_and_docs.drive_for_desktop
  allowDriveForDesktop
  restrictToAuthorizedDevices
  showDownloadLink
  allowRealTimePresence
drive_and_docs.external_sharing
  externalSharingMode
  allowReceivingExternalFiles
  warnForSharingOutsideAllowlistedDomains
  allowReceivingFilesOutsideAllowlistedDomains
  allowNonGoogleInvitesInAllowlistedDomains
  warnForExternalSharing
  allowNonGoogleInvites
  allowPublishingFiles
  accessCheckerSuggestions
  allowedPartiesForDistributingContent
drive_and_docs.file_security_update
  securityUpdate
  allowUsersToManageUpdate
drive_and_docs.shared_drive_creation
  allowSharedDriveCreation
  orgUnitForNewSharedDrives
  customOrgUnit
  allowManagersToOverrideSettings
  allowExternalUserAccess
  allowNonMemberAccess
  allowedPartiesForDownloadPrintCopy
  allowContentManagersToShareFolders
gmail.auto_forwarding
  enableAutoForwarding
gmail.confidential_mode
  enableConfidentialMode
gmail.email_attachment_safety
  enableEncryptedAttachmentProtection
  encryptedAttachmentProtectionConsequence
  enableAttachmentWithScriptsProtection
  attachmentWithScriptsProtectionConsequence
  enableAnomalousAttachmentProtection
  anomalousAttachmentProtectionConsequence
  allowedAnomalousAttachmentFiletypes
  applyFutureRecommendedSettingsAutomatically
  encryptedAttachmentProtectionQuarantineId
  attachmentWithScriptsProtectionQuarantineId
  anomalousAttachmentProtectionQuarantineId
gmail.email_image_proxy_bypass
  imageProxyBypassPattern
  enableImageProxy
gmail.enhanced_pre_delivery_message_scanning
  enableImprovedSuspiciousContentDetection
gmail.enhanced_smime_encryption
  enableSmimeEncryption
  allowUserToUploadCertificates
gmail.gmail_name_format
  allowCustomDisplayNames
  defaultDisplayNameFormat
gmail.imap_access
  enableImapAccess
gmail.links_and_external_images
  enableShortenerScanning
  enableExternalImageScanning
  enableAggressiveWarningsOnUntrustedLinks
  applyFutureSettingsAutomatically
gmail.per_user_outbound_gateway
  allowUsersToUseExternalSmtpServers
gmail.pop_access
  enablePopAccess
gmail.spoofing_and_authentication
  detectDomainNameSpoofing
  detectEmployeeNameSpoofing
  detectDomainSpoofingFromUnauthenticatedSenders
  detectUnauthenticatedEmails
  domainNameSpoofingConsequence
  employeeNameSpoofingConsequence
  domainSpoofingConsequence
  unauthenticatedEmailConsequence
  detectGroupsSpoofing
  groupsSpoofingVisibilityType
  groupsSpoofingConsequence
  applyFutureSettingsAutomatically
  domainNameSpoofingQuarantineId
  employeeNameSpoofingQuarantineId
  domainSpoofingQuarantineId
  unauthenticatedEmailQuarantineId
  groupsSpoofingQuarantineId
gmail.user_email_uploads
  enableMailAndContactsImport
gmail.workspace_sync_for_outlook
  enableGoogleWorkspaceSyncForMicrosoftOutlook
groups_for_business.groups_sharing
  ownersCanAllowIncomingMailFromPublic
  collaborationCapability
  createGroupsAccessLevel
  ownersCanAllowExternalMembers
  ownersCanHideGroups
  newGroupsAreHidden
  viewTopicsDefaultAccessLevel
meet.safety_access
  meetingsAllowedToJoin
meet.safety_domain
  usersAllowedToJoin
meet.safety_external_participants
  enableExternalLabel
meet.safety_host_management
  enableHostManagement
meet.video_recording
  enableRecording
rule.dlp
  displayName
  description
  triggers
  condition
  action
  state
  createTime
  updateTime
  ruleTypeMetadata
rule.system_defined_alerts
  displayName
  description
  action
  state
  createTime
  updateTime
security.advanced_protection_program
  enableAdvancedProtectionSelfEnrollment
  securityCodeOption
security.less_secure_apps
  allowLessSecureApps
security.login_challenges
  enableEmployeeIdChallenge
security.password
  allowedStrength
  minimumLength
  maximumLength
  enforceRequirementsAtLogin
  allowReuse
  expirationDuration
security.session_controls
  webSessionDuration
security.super_admin_account_recovery
  enableAccountRecovery
security.user_account_recovery
  enableAccountRecovery
sites.sites_creation_and_modification
  allowSitesCreation
  allowSitesModification
workspace_marketplace.apps_allowlist
  apps
```
## Display Cloud Identity Policies
```
gam show policies
        [(filter <String>)|(name <CIPolicyName>)] [nowarnings]
        [formatjson]
```
By default, all policies are displayed.
* `filter <String>` - Display filtered policies, See https://github.com/taers232c/GAMADV-XTD3/wiki/Cloud-Identity-Policies
* `name <CIPolicyName>` - Display a specfic policy

By default, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

```
gam print policies [todrive <ToDriveAttribute>*]
        [(filter <String>)|(name <CIPolicyName>)] [nowarnings]
        [formatjson [quotechar <Character>]]
```
By default, all policies are displayed:
* `filter <String>` - Display filtered policies, See https://github.com/taers232c/GAMADV-XTD3/wiki/Cloud-Identity-Policies
* `name <CIPolicyName>` - Display a specfic policy

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
