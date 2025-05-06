# Administrators
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Display administrative privileges](#display-administrative-privileges)
- [Manage administrative roles](#manage-administrative-roles)
- [Display administrative roles](#display-administrative-roles)
- [Create an administrator](#create-an-administrator)
- [Delete an administrator](#delete-an-administrator)
- [Display administrators](#display-administrators)
- [Copy privileges from one role to a new role](#copy-privileges-from-one-role-to-a-new-role)
- [Copy roles from one administrator to another](#copy-roles-from-one-administrator-to-another)

## API documentation
* [About Administrator roles](https://support.google.com/a/answer/33325?ref_topic=4514341)
* [Directory API - Privileges](https://developers.google.com/admin-sdk/directory/reference/rest/v1/privileges)
* [Directory API - Roles](https://developers.google.com/admin-sdk/directory/reference/rest/v1/roles)
* [Directory API - Role Assignments](https://developers.google.com/admin-sdk/directory/reference/rest/v1/roleAssignments)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>
<Privilege> ::= <String>
<PrivilegeList> ::= "<Privilege>(,<Privilege)*"
<RoleAssignmentID> ::= <String>
<RoleItem> ::= id:<String>|uid:<String>|<String>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>
```
## Display administrative privileges
```
gam print privileges [todrive <ToDriveAttribute>*]
gam show privileges
```

Here is the output from `gam show privileges`; use this to find a specific `<Privilege>`.
```
Show 111 Privileges
  Privilege: REPORTS_ACCESS (1/111)
    serviceId: 01fob9te2rj6rw9
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (2/111)
    serviceId: 02et92p02l9sq0n
    serviceName: Unknown
    isOuScopable: True
  Privilege: APP_ADMIN (3/111)
    serviceId: 00tyjcwt30rsnw6
    serviceName: Unknown
    isOuScopable: True
  Privilege: MANAGE_ENTERPRISE_PRIVATE_APPS (4/111)
    serviceId: 00tyjcwt49hs5nq
    serviceName: play_for_work
    isOuScopable: False
  Privilege: MANAGE_EXTERNALLY_HOSTED_APK_UPLOAD_IN_PLAY (5/111)
    serviceId: 00tyjcwt49hs5nq
    serviceName: play_for_work
    isOuScopable: False
  Privilege: MANAGE_PLAY_FOR_WORK_STORE (6/111)
    serviceId: 00tyjcwt49hs5nq
    serviceName: play_for_work
    isOuScopable: False
  Privilege: APP_ADMIN (7/111)
    serviceId: 03dy6vkm2sk0pzo
    serviceName: docs
    isOuScopable: False
    childPrivileges: 4
      Privilege: DOCS_TEMPLATE_ADMIN (1/4)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: MANAGE_CLASSIC_GOOGLE_SITES (2/4)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: MIGRATE_TO_TEAM_DRIVE (3/4)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: VIEW_SITE_DETAILS (4/4)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
  Privilege: REVIEW_ALL_SENSITIVE_ACTIONS (8/111)
    serviceId: 035nkun23a65bz3
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: REVIEW_SECURITY_ACTIONS
        serviceId: 035nkun23a65bz3
        serviceName: Unknown
        isOuScopable: False
  Privilege: APP_ADMIN (9/111)
    serviceId: 01ksv4uv2d2noaq
    serviceName: sites
    isOuScopable: False
  Privilege: APP_ADMIN (10/111)
    serviceId: 044sinio4cntx2o
    serviceName: Unknown
    isOuScopable: False
  Privilege: DATA_REGIONS_SETTINGS (11/111)
    serviceId: 02jxsxqh0hucks4
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: DATA_REGIONS_REPORTING
        serviceId: 02jxsxqh0hucks4
        serviceName: Unknown
        isOuScopable: False
  Privilege: LOGO_PRIVILEGE_GROUP (12/111)
    serviceId: 03j2qqm31d4j55e
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (13/111)
    serviceId: 04i7ojhp4kgosur
    serviceName: Unknown
    isOuScopable: True
  Privilege: ADMIN_DASHBOARD (14/111)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: True
  Privilege: ADMIN_DOMAIN_SETTINGS (15/111)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: REPORTS (16/111)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: SERVICES (17/111)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: SECURITY_SETTINGS (18/111)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: APP_ADMIN (19/111)
    serviceId: 01ci93xb43sd8me
    serviceName: Unknown
    isOuScopable: True
    childPrivileges: 2
      Privilege: DELEGATES_READ (1/2)
        serviceId: 01ci93xb43sd8me
        serviceName: Unknown
        isOuScopable: True
      Privilege: DELEGATES_WRITE (2/2)
        serviceId: 01ci93xb43sd8me
        serviceName: Unknown
        isOuScopable: True
  Privilege: MANAGE_DYNAMITE_SETTINGS (20/111)
    serviceId: 03whwml44f3n4vd
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DYNAMITE_SPACES (21/111)
    serviceId: 03whwml44f3n4vd
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: READ_DYNAMITE_SPACES
        serviceId: 03whwml44f3n4vd
        serviceName: Unknown
        isOuScopable: False
  Privilege: MODERATE_DYNAMITE_REPORT (22/111)
    serviceId: 03whwml44f3n4vd
    serviceName: Unknown
    isOuScopable: False
  Privilege: CLOUD_PRINT_MANAGER (23/111)
    serviceId: 02bn6wsx379ol8g
    serviceName: cloud_print
    isOuScopable: False
  Privilege: APP_ADMIN (24/111)
    serviceId: 03as4poj2zjehv7
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DIRECTORY_SYNC_SETTINGS (25/111)
    serviceId: 0147n2zr1ynkkmf
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: READ_DIRECTORY_SYNC_SETTINGS
        serviceId: 0147n2zr1ynkkmf
        serviceName: Unknown
        isOuScopable: False
  Privilege: SECURITY_SETTINGS (26/111)
    serviceId: 00vx122734tbite
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: INBOUND_SSO_SETTINGS
        serviceId: 00vx122734tbite
        serviceName: Unknown
        isOuScopable: False
  Privilege: APP_ADMIN (27/111)
    serviceId: 03fwokq01e2ht7x
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: UDM_NETWORK_ADMIN
        serviceId: 03fwokq01e2ht7x
        serviceName: Unknown
        isOuScopable: True
  Privilege: APP_ADMIN (28/111)
    serviceId: 04f1mdlm0ki64aw
    serviceName: cros
    isOuScopable: True
    childPrivileges: 7
      Privilege: MANAGE_BROWSERS (1/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_DEVICES (2/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_DEVICE_SETTINGS (3/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_PRINTERS (4/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_USER_SETTINGS (5/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
        childPrivileges: 1
          Privilege: MANAGE_APPLICATION_SETTINGS
            serviceId: 04f1mdlm0ki64aw
            serviceName: cros
            isOuScopable: True
      Privilege: VIEW_EXTENSIONS_REPORT (6/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: VIEW_VERSION_REPORT (7/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
  Privilege: ADMIN_OVERSIGHT_MANAGE_CLASSES (29/111)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: APP_ADMIN (30/111)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: BACKFILL_DRIVE_READWRITE (31/111)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: EDU_ANALYTICS_DATA_ACCESS (32/111)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: MIGRATE_MANAGE_DEPLOYMENT (33/111)
    serviceId: 03tbugp12newe5s
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: MIGRATE_ACCESS_DEPLOYMENT
        serviceId: 03tbugp12newe5s
        serviceName: Unknown
        isOuScopable: False
  Privilege: MODIFY_DASHER_ANALYTICS_APP_SETTINGS (34/111)
    serviceId: 00nmf14n2rzq5a5
    serviceName: Unknown
    isOuScopable: False
  Privilege: VIEW_DASHER_ANALYTICS_APP_SETTINGS (35/111)
    serviceId: 00nmf14n2rzq5a5
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_TRUST_RULES (36/111)
    serviceId: 00nmf14n34b7f81
    serviceName: Unknown
    isOuScopable: False
  Privilege: VIEW_TRUST_RULES (37/111)
    serviceId: 00nmf14n34b7f81
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (38/111)
    serviceId: 00nmf14n14wtgcf
    serviceName: app_maker
    isOuScopable: False
  Privilege: VIEW_ALL_PROJECTS (39/111)
    serviceId: 00nmf14n14wtgcf
    serviceName: app_maker
    isOuScopable: False
  Privilege: APP_ADMIN (40/111)
    serviceId: 037m2jsg3ckz96v
    serviceName: calendar
    isOuScopable: False
    childPrivileges: 2
      Privilege: CALENDAR_RESOURCE (1/2)
        serviceId: 037m2jsg3ckz96v
        serviceName: calendar
        isOuScopable: False
        childPrivileges: 2
          Privilege: CALENDAR_RESOURCE_MANAGE (1/2)
            serviceId: 037m2jsg3ckz96v
            serviceName: calendar
            isOuScopable: False
            childPrivileges: 1
              Privilege: CALENDAR_RESOURCE_READ
                serviceId: 037m2jsg3ckz96v
                serviceName: calendar
                isOuScopable: False
          Privilege: ROOM_INSIGHTS_DASHBOARD_ACCESS (2/2)
            serviceId: 037m2jsg3ckz96v
            serviceName: calendar
            isOuScopable: False
      Privilege: CALENDAR_SETTINGS (2/2)
        serviceId: 037m2jsg3ckz96v
        serviceName: calendar
        isOuScopable: False
        childPrivileges: 1
          Privilege: CALENDAR_SETTINGS_READ
            serviceId: 037m2jsg3ckz96v
            serviceName: calendar
            isOuScopable: False
  Privilege: CALENDAR_SUPER_ADMIN (41/111)
    serviceId: 037m2jsg3ckz96v
    serviceName: calendar
    isOuScopable: False
  Privilege: APP_ADMIN (42/111)
    serviceId: 037m2jsg46www3g
    serviceName: Unknown
    isOuScopable: False
  Privilege: LDAP_MANAGER (43/111)
    serviceId: 02lwamvv18la4iw
    serviceName: ldap
    isOuScopable: False
  Privilege: LDAP_PASSWORD_REBIND (44/111)
    serviceId: 02lwamvv18la4iw
    serviceName: ldap
    isOuScopable: True
    childPrivileges: 1
      Privilege: LDAP_PASSWORD_REBIND_READONLY
        serviceId: 02lwamvv18la4iw
        serviceName: ldap
        isOuScopable: True
  Privilege: ACCESS_ALL_LOGS (45/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: False
    childPrivileges: 1
      Privilege: AUDIT_SYSTEM
        serviceId: 03l18frh45c63dw
        serviceName: vault
        isOuScopable: False
  Privilege: ACCESS_ALL_MATTERS (46/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: False
  Privilege: ADMIN_MATTER (47/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: APPROVE_ACCELERATED_DELETION (48/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
    childPrivileges: 1
      Privilege: CREATE_ACCELERATED_DELETION
        serviceId: 03l18frh45c63dw
        serviceName: vault
        isOuScopable: True
  Privilege: MANAGE_EXPORTS (49/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: MANAGE_RETENTION_POLICY (50/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: False
    childPrivileges: 1
      Privilege: VIEW_RETENTION_POLICY
        serviceId: 03l18frh45c63dw
        serviceName: vault
        isOuScopable: False
  Privilege: MANAGE_SEARCHES (51/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: REMOVE_HOLD (52/111)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: APP_ADMIN (53/111)
    serviceId: 02zbgiuw2wdxo5p
    serviceName: youtube
    isOuScopable: False
  Privilege: ACTIVITY_RULES (54/111)
    serviceId: 01egqt2p2p8gvae
    serviceName: security_center
    isOuScopable: False
    childPrivileges: 2
      Privilege: MANAGE_GSC_RULE (1/2)
        serviceId: 01egqt2p2p8gvae
        serviceName: security_center
        isOuScopable: False
      Privilege: VIEW_GSC_RULE (2/2)
        serviceId: 01egqt2p2p8gvae
        serviceName: security_center
        isOuScopable: False
  Privilege: APP_ADMIN (55/111)
    serviceId: 01egqt2p2p8gvae
    serviceName: security_center
    isOuScopable: False
    childPrivileges: 4
      Privilege: AUDIT_INVESTIGATION_ACCESS (1/4)
        serviceId: 01egqt2p2p8gvae
        serviceName: security_center
        isOuScopable: False
        childPrivileges: 3
          Privilege: SIT_MANAGE (1/3)
            serviceId: 01egqt2p2p8gvae
            serviceName: security_center
            isOuScopable: False
            childPrivileges: 9
              Privilege: SIT_CHAT_UPDATE_DELETE (1/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CHROME_UPDATE_DELETE (2/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DEVICE_UPDATE_DELETE (3/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DRIVE_UPDATE_DELETE (4/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GMAIL_UPDATE_DELETE (5/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_MEET_UPDATE_DELETE (6/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_OAUTH_UPDATE_DELETE (7/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_RULE_UPDATE_DELETE (8/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_USER_UPDATE_DELETE (9/9)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
          Privilege: SIT_VIEW_METADATA (2/3)
            serviceId: 01egqt2p2p8gvae
            serviceName: security_center
            isOuScopable: False
            childPrivileges: 40
              Privilege: SIT_ADMIN_VIEW_METADATA (1/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_AUDITOR_VIEW_METADATA (2/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_AXT_VIEW_METADATA (3/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CAA_VIEW_METADATA (4/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CALENDAR_VIEW_METADATA (5/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CHAT_VIEW_METADATA (6/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CHROME_SYNC_VIEW_METADATA (7/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CHROME_VIEW_METADATA (8/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CLASSROOM_VIEW_METADATA (9/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CLOUD_SEARCH_VIEW_METADATA (10/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CONTACTS_VIEW_METADATA (11/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_COURSEKIT_VIEW_METADATA (12/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CURRENTS_VIEW_METADATA (13/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DATASTUDIO_VIEW_METADATA (14/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DATA_LOCATION_VIEW_METADATA (15/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DATA_MIGRATION_VIEW_METADATA (16/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DEVICE_VIEW_METADATA (17/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DIRECTORY_SYNC_VIEW_METADATA (18/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_DRIVE_VIEW_METADATA (19/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GEN_AI_PLATFORM_APP_VIEW_METADATA (20/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GMAIL_VIEW_METADATA (21/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GOOGLE_PROFILES_VIEW_METADATA (22/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GRADUATION_VIEW_METADATA (23/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GROUPSALT_VIEW_METADATA (24/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GROUPS_VIEW_METADATA (25/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_HODOR_VIEW_METADATA (26/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_JAMBOARD_VIEW_METADATA (27/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_KEEP_VIEW_METADATA (28/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_LDAP_VIEW_METADATA (29/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_MEET_HARDWARE_VIEW_METADATA (30/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_MEET_VIEW_METADATA (31/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_OAUTH_VIEW_METADATA (32/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_PASSWORD_VAULT_VIEW_METADATA (33/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_RULE_VIEW_METADATA (34/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_SAML_VIEW_METADATA (35/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_SCIM_DS_VIEW_METADATA (36/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_TASKS_VIEW_METADATA (37/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_USER_LEVEL_TAKEOUT_VIEW_METADATA (38/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_USER_VIEW_METADATA (39/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_VOICE_VIEW_METADATA (40/40)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
          Privilege: SIT_VIEW_SENSITIVE_CONTENT (3/3)
            serviceId: 01egqt2p2p8gvae
            serviceName: security_center
            isOuScopable: False
            childPrivileges: 4
              Privilege: SIT_CHAT_VIEW_DETAILED_CONTENT (1/4)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_CHROME_VIEW_DETAILED_CONTENT (2/4)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_GMAIL_VIEW_DETAILED_CONTENT (3/4)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
              Privilege: SIT_RULE_VIEW_DETAILED_CONTENT (4/4)
                serviceId: 01egqt2p2p8gvae
                serviceName: security_center
                isOuScopable: False
      Privilege: DASHBOARD_ACCESS (2/4)
        serviceId: 01egqt2p2p8gvae
        serviceName: security_center
        isOuScopable: False
      Privilege: GSC_VIEW_VIRUSTOTAL_REPORT (3/4)
        serviceId: 01egqt2p2p8gvae
        serviceName: security_center
        isOuScopable: False
      Privilege: SECURITY_HEALTH_DASHBOARD_ACCESS (4/4)
        serviceId: 01egqt2p2p8gvae
        serviceName: security_center
        isOuScopable: False
  Privilege: APP_ADMIN (56/111)
    serviceId: 00sqyw642iersp7
    serviceName: search
    isOuScopable: False
    childPrivileges: 1
      Privilege: TOPAZ_INDEXING_ADMIN_PRIVILEGE
        serviceId: 00sqyw642iersp7
        serviceName: search
        isOuScopable: False
        childPrivileges: 1
          Privilege: TOPAZ_INDEXING_READONLY_PRIVILEGE
            serviceId: 00sqyw642iersp7
            serviceName: search
            isOuScopable: False
  Privilege: APP_ACCESS (57/111)
    serviceId: 03cqmetx1vygwki
    serviceName: Unknown
    isOuScopable: False
  Privilege: ACCESS_LEVEL_ENFORCEMENT (58/111)
    serviceId: 01rvwp1q4axizdr
    serviceName: Unknown
    isOuScopable: False
  Privilege: ACCESS_LEVEL_MANAGEMENT (59/111)
    serviceId: 01rvwp1q4axizdr
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_LABELS (60/111)
    serviceId: 034g0dwd19r1crs
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: VIEW_LABELS
        serviceId: 034g0dwd19r1crs
        serviceName: Unknown
        isOuScopable: False
  Privilege: APP_ADMIN (61/111)
    serviceId: 03hv69ve4bjwe54
    serviceName: Unknown
    isOuScopable: True
    childPrivileges: 6
      Privilege: MANAGE_CHROME_BROWSERS (1/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 1
          Privilege: MANAGED_CHROME_BROWSERS_READ_ONLY
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
      Privilege: MANAGE_CHROME_USER_SETTINGS (2/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 2
          Privilege: MANAGE_CHROME_APPLICATION_SETTINGS (1/2)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: MANAGE_CHROME_WEB_SETTINGS (2/2)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
      Privilege: MANAGE_DEVICES (3/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 5
          Privilege: CHROME_DEVICE_ACTION_LOG_COLLECTION (1/5)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: DEVICE_ACTION_CRD (2/5)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: DEVICE_ACTION_REBOOT (3/5)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: DEVICE_ACTION_SCREENSHOT (4/5)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: MANAGE_DEVICES_READ_ONLY (5/5)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
            childPrivileges: 1
              Privilege: TELEMETRY_API
                serviceId: 03hv69ve4bjwe54
                serviceName: Unknown
                isOuScopable: True
                childPrivileges: 24
                  Privilege: TELEMETRY_API_APPS_REPORT (1/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_AUDIO_REPORT (2/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_BATTERY_INFO (3/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_BATTERY_REPORT (4/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_BUS_DEVICE_INFO (5/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_CPU_INFO (6/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_CPU_REPORT (7/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_CRASH_REPORT (8/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_DEVICE (9/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_DEVICE_ACTIVITY_REPORT (10/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_GRAPHICS_INFO (11/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_GRAPHICS_REPORT (12/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_KIOSK_VISION_INFO (13/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_KIOSK_VISION_REPORT (14/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_MEMORY_INFO (15/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_MEMORY_REPORT (16/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_NETWORK_INFO (17/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_NETWORK_REPORT (18/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_OS_REPORT (19/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_PERIPHERALS_REPORT (20/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_STORAGE_INFO (21/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_STORAGE_REPORT (22/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_USER (23/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_WEB_REPORT (24/24)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
      Privilege: MANAGE_DEVICE_SETTINGS (4/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
      Privilege: MANAGE_PRINTERS (5/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
      Privilege: VIEW_CHROME_REPORTS (6/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 6
          Privilege: VIEW_CHROME_CRASH_REPORTS (1/6)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_EXTENSIONS_REPORT (2/6)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_INSIGHTS_REPORT (3/6)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_LEGACY_TECH_REPORT (4/6)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_PRINTERS_REPORT (5/6)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_VERSION_REPORT (6/6)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
  Privilege: SERVICE_DATA_DOWNLOADER (62/111)
    serviceId: 03hv69ve4bjwe54
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_CHROME_INSIGHT_SETTINGS (63/111)
    serviceId: 01x0gk371sq486y
    serviceName: Unknown
    isOuScopable: False
  Privilege: VIEW_AND_MANAGE_CHROME_OCR_SETTING (64/111)
    serviceId: 01x0gk371sq486y
    serviceName: Unknown
    isOuScopable: False
  Privilege: VIEW_CHROME_INSIGHT_SETTINGS (65/111)
    serviceId: 01x0gk371sq486y
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_ENTERPRISE_PRIVATE_APPS (66/111)
    serviceId: 02w5ecyt3pkeyqi
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_EXTERNALLY_HOSTED_APK_UPLOAD_IN_PLAY (67/111)
    serviceId: 02w5ecyt3pkeyqi
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_PLAY_FOR_WORK_STORE (68/111)
    serviceId: 02w5ecyt3pkeyqi
    serviceName: Unknown
    isOuScopable: False
  Privilege: ENROLL_MEET_DEVICES (69/111)
    serviceId: 02w5ecyt3laroi5
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_HANGOUTS_SERVICE (70/111)
    serviceId: 02w5ecyt3laroi5
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 2
      Privilege: MANAGE_CALENDARS (1/2)
        serviceId: 02w5ecyt3laroi5
        serviceName: Unknown
        isOuScopable: False
        childPrivileges: 2
          Privilege: MANAGE_PERSONAL_CALENDARS (1/2)
            serviceId: 02w5ecyt3laroi5
            serviceName: Unknown
            isOuScopable: False
          Privilege: MANAGE_ROOM_CALENDARS (2/2)
            serviceId: 02w5ecyt3laroi5
            serviceName: Unknown
            isOuScopable: False
      Privilege: MANAGE_HANGOUTS_SERVICE_WITHOUT_CALENDAR (2/2)
        serviceId: 02w5ecyt3laroi5
        serviceName: Unknown
        isOuScopable: False
        childPrivileges: 4
          Privilege: DEPROVISION_MEET_DEVICES (1/4)
            serviceId: 02w5ecyt3laroi5
            serviceName: Unknown
            isOuScopable: False
          Privilege: MANAGE_MEET_DEVICES (2/4)
            serviceId: 02w5ecyt3laroi5
            serviceName: Unknown
            isOuScopable: False
            childPrivileges: 1
              Privilege: READ_MEET_DEVICES
                serviceId: 02w5ecyt3laroi5
                serviceName: Unknown
                isOuScopable: False
          Privilege: MANAGE_MEET_DEVICE_SETTINGS (3/4)
            serviceId: 02w5ecyt3laroi5
            serviceName: Unknown
            isOuScopable: False
            childPrivileges: 2
              Privilege: MANAGE_MEET_DEVICE_SIGNAGE_SETTING (1/2)
                serviceId: 02w5ecyt3laroi5
                serviceName: Unknown
                isOuScopable: False
              Privilege: READ_MEET_DEVICE_SETTINGS (2/2)
                serviceId: 02w5ecyt3laroi5
                serviceName: Unknown
                isOuScopable: False
          Privilege: OPERATE_MEET_DEVICES (4/4)
            serviceId: 02w5ecyt3laroi5
            serviceName: Unknown
            isOuScopable: False
            childPrivileges: 2
              Privilege: MANAGE_MEET_DEVICE_MEETINGS (1/2)
                serviceId: 02w5ecyt3laroi5
                serviceName: Unknown
                isOuScopable: False
              Privilege: PERFORM_MEET_DEVICE_COMMANDS (2/2)
                serviceId: 02w5ecyt3laroi5
                serviceName: Unknown
                isOuScopable: False
  Privilege: APP_ADMIN (71/111)
    serviceId: 01baon6m1wv6b0p
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (72/111)
    serviceId: 02afmg282jiquyg
    serviceName: device_management
    isOuScopable: True
  Privilege: APP_ADMIN (73/111)
    serviceId: 02afmg283v5nmx6
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: ADMIN_QUALITY_DASHBOARD_ACCESS
        serviceId: 02afmg283v5nmx6
        serviceName: Unknown
        isOuScopable: False
  Privilege: ACCESS_ADMIN_QUARANTINE (74/111)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: ACCESS_EMAIL_LOG_SEARCH (75/111)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: ACCESS_RESTRICTED_QUARANTINE (76/111)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: APP_ADMIN (77/111)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: APP_ADMIN (78/111)
    serviceId: 03mzq4wv1nvgcwf
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DLP_RULE (79/111)
    serviceId: 02250f4o3hg8pg8
    serviceName: Unknown
    isOuScopable: False
  Privilege: VIEW_DLP_RULE (80/111)
    serviceId: 02250f4o3hg8pg8
    serviceName: Unknown
    isOuScopable: False
  Privilege: ADMIN_REPORTING_ACCESS (81/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: REPORTING_AUDIT_ACCESS
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: API_APPS_ENTERPRISE_CUSTOMER (82/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 2
      Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ (1/2)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
        childPrivileges: 6
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ_BRANDING_SETTINGS (1/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ_CONTACT_INFO (2/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ_ONBOARD_SETTINGS (3/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ_PROFILE_SETTINGS (4/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ_SUPPORT_SETTINGS (5/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_READ_TIME_ZONE_SETTINGS (6/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
      Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE (2/2)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
        childPrivileges: 6
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE_BRANDING_SETTINGS (1/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE_CONTACT_INFO (2/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE_ONBOARD_SETTINGS (3/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE_PROFILE_SETTINGS (4/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE_SUPPORT_SETTINGS (5/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
          Privilege: API_APPS_ENTERPRISE_CUSTOMER_UPDATE_TIME_ZONE_SETTINGS (6/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
  Privilege: USER_SECURITY_ALL (83/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: True
  Privilege: BILLING (84/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: BILLING_READ
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: DATATRANSFER_API_PRIVILEGE_GROUP (85/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: DOMAIN_MANAGEMENT (86/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: DOMAIN_REGISTRATION_MANAGEMENT (87/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: FULL_MIGRATION_ACCESS (88/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: EXECUTE_MIGRATION
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
        childPrivileges: 1
          Privilege: MODIFY_MIGRATION
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: False
            childPrivileges: 1
              Privilege: VIEW_MIGRATION
                serviceId: 00haapch16h1ysv
                serviceName: admin_apis
                isOuScopable: False
  Privilege: GROUPS_ALL (89/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 4
      Privilege: GROUPS_CREATE (1/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
      Privilege: GROUPS_DELETE (2/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
      Privilege: GROUPS_RETRIEVE (3/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
      Privilege: GROUPS_UPDATE (4/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: GROUPS_MANAGE_LOCKED_LABEL (90/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: GROUPS_MANAGE_SECURITY_LABEL (91/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: LICENSING (92/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: LICENSING_READ
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: ORGANIZATION_UNITS_ALL (93/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: True
    childPrivileges: 4
      Privilege: ORGANIZATION_UNITS_CREATE (1/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: ORGANIZATION_UNITS_DELETE (2/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: ORGANIZATION_UNITS_RETRIEVE (3/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: ORGANIZATION_UNITS_UPDATE (4/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
  Privilege: SAML2_SERVICE_PROVIDER (94/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: SCHEMA_MANAGEMENT (95/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: SCHEMA_RETRIEVE
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: SUPPORT_PRIVILEGE_GROUP (96/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: TRUSTED_DOMAIN_WHITELIST_WRITE (97/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: TRUSTED_DOMAIN_WHITELIST_READ
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: UPGRADE_CONSUMER_CONVERSION (98/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: USERS_ALL (99/111)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: True
    childPrivileges: 5
      Privilege: USERS_CREATE (1/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_DELETE (2/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_RETRIEVE (3/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_UPDATE_CUSTOM_ATTRIBUTES_USER_PRIVILEGE_GROUP (4/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_UPDATE (5/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
        childPrivileges: 6
          Privilege: USERS_ADD_NICKNAME (1/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_FORCE_PASSWORD_CHANGE (2/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_MOVE (3/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_ALIAS (4/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_RESET_PASSWORD (5/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_SUSPEND (6/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
  Privilege: APP_ADMIN (100/111)
    serviceId: 0319y80a15kueje
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (101/111)
    serviceId: 00upglbi0qz687j
    serviceName: takeout
    isOuScopable: False
  Privilege: APP_ADMIN (102/111)
    serviceId: 01tuee744837sjz
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (103/111)
    serviceId: 02szc72q20usrb6
    serviceName: Unknown
    isOuScopable: True
  Privilege: APP_ADMIN (104/111)
    serviceId: 0279ka651l5iy5q
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: ADMIN_QUALITY_DASHBOARD_ACCESS
        serviceId: 0279ka651l5iy5q
        serviceName: Unknown
        isOuScopable: False
  Privilege: ACCESS_ALL_STATS (105/111)
    serviceId: 0279ka6513ygm10
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 3
      Privilege: ACCESS_GROUP_STATS (1/3)
        serviceId: 0279ka6513ygm10
        serviceName: Unknown
        isOuScopable: False
      Privilege: ACCESS_OU_STATS (2/3)
        serviceId: 0279ka6513ygm10
        serviceName: Unknown
        isOuScopable: True
      Privilege: ACCESS_TEAM_STATS (3/3)
        serviceId: 0279ka6513ygm10
        serviceName: Unknown
        isOuScopable: False
  Privilege: EDIT_WORK_INSIGHTS_SETTINGS (106/111)
    serviceId: 0279ka6513ygm10
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (107/111)
    serviceId: 01yyy98l4k9lq4l
    serviceName: directory
    isOuScopable: False
    childPrivileges: 4
      Privilege: CUSTOM_DIRECTORY_READWRITE (1/4)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
      Privilege: DIRECTORY_SETTINGS_READONLY (2/4)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
        childPrivileges: 2
          Privilege: CUSTOM_DIRECTORY_READONLY (1/2)
            serviceId: 01yyy98l4k9lq4l
            serviceName: directory
            isOuScopable: False
          Privilege: PROFILE_EDITABILITY_READONLY (2/2)
            serviceId: 01yyy98l4k9lq4l
            serviceName: directory
            isOuScopable: False
      Privilege: PROFILE_EDITABILITY_READWRITE (3/4)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
      Privilege: SHARED_CONTACTS_READWRITE (4/4)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
  Privilege: MANAGE_SERVICE_ON_OFF (108/111)
    serviceId: 04iylrwe1ih2v48
    serviceName: Unknown
    isOuScopable: False
  Privilege: APPS_INCIDENTS_FULL_ACCESS (109/111)
    serviceId: 02pta16n3efhw69
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 2
      Privilege: APPS_INCIDENTS_READONLY (1/2)
        serviceId: 02pta16n3efhw69
        serviceName: Unknown
        isOuScopable: False
      Privilege: APPS_INCIDENTS_VIEW_VIRUSTOTAL_REPORTS (2/2)
        serviceId: 02pta16n3efhw69
        serviceName: Unknown
        isOuScopable: False
  Privilege: MANAGE_CSE_SETTINGS (110/111)
    serviceId: 02pta16n4hxgyp2
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (111/111)
    serviceId: 03oy7u290lj7dci
    serviceName: Unknown
    isOuScopable: False
```

## Manage administrative roles
```
gam create adminrole <String> [description <String>]
        privileges all|all_ou|<PrivilegeList>|(select <FileSelector>|<CSVFileSelector>>)
gam update adminrole <RoleItem> [name <String>] [description <String>]
        [privileges all|all_ou|<PrivilegeList>|(select <FileSelector>|<CSVFileSelector>>)] 
gam delete adminrole <RoleItem>
```
* `privileges all` - All defined privileges
* `privileges all_ou` - All defined privileges than can be scoped to an OU
* `privileges <PrivilegeList>` - A specific list of privileges
* `privileges select <FileSelector>|<CSVFileSelector>>` - A collection of privileges from a flat or CSV file

## Display administrative roles
```
gam info adminrole <RoleItem> [privileges]
```
* `privileges` - Display privileges associated with role
```
gam print adminroles|roles [todrive <ToDriveAttribute>*]
        [role <RoleItem>] [privileges] [oneitemperrow]
gam show adminroles|roles
        [role <RoleItem>] [privileges]
```
By default, all roles are displayed, use `role <RoleItem>` to display a specific role.

* `privileges` - Display privileges associated with each role

By default, with `print`, all privileges for a role are shown on one row as a repeating item.
When `oneitemperrow` is specified, each privilege is output on a separate row/line with the other role fields.

## Create an administrator
Add an administrator role to an administrator.
```
gam create admin <EmailAddress>|<UniqueID> <RoleItem> customer|(org_unit <OrgUnitItem>)
        [condition securitygroup|nonsecuritygroup]
```
* `customer` - The administrator can manage all organization units
* `org_unit <OrgUnitItem>` - The administrator can manage the specified organization unit

The option `condition` limits the conditions for delegate admin access. This currently only works with the _GROUPS_EDITOR_ROLE and _GROUPS_READER_ROLE roles.
* `condition securitygroup` - limit the delegated admin to managing security groups
* `condition nonsecuritygroup` - limit the delegated admin to managing non-security groups

## Delete an administrator
Remove an administrator role from an administrator.
```
gam delete admin <RoleAssignmentId>
```
## Display administrators
```
gam print admins [todrive <ToDriveAttribute>*]
        [user|group <EmailAddress>|<UniqueID>] [role <RoleItem>] [condition]
        [privileges] [oneitemperrow]
gam show admins
        [user|group <EmailAddress>|<UniqueID>] [role <RoleItem>] [condition] [privileges]
```
By default, all administrators and roles are displayed; choose from the following
options to limit the display:
* `user <UserItem>` -  Display only this administrator
* `role <RoleItem>` - Display only administrators with this role

* `condition` - Display any conditions associated with a role assignment
* `privileges` - Display privileges associated with each role assignment

By default, all role privileges for an admin are shown on one row as a repeating item.
When `oneitemperrow` is specified, each role privilege is output on a separate row/line with the other admin fields.

## Copy privileges from one role to a new role
Get privileges for existing role; replace Role Name with actual role name
```
gam redirect csv ./RolePrivileges.csv print adminrole role 'Role Name' privileges oneitemperrow
```
Create a new role with those privileges
```
gam create adminrole "New Role Name" privileges select csvfile RolePrivileges.csv:privilegeName
```

## Copy roles from one administrator to another
Get roles for current admin.
```
gam redirect csv ./CurrentAdminRoles.csv print admins user currentadmin@domain.com
```
Add roles to new admin.
```
gam config csv_input_row_filter "scopeType:regex:CUSTOMER" redirect stdout ./UpdateNewAdminCustomerRoles.txt multiprocess redirect stderr stdout csv CurrentAdminRoles.csv gam create admin newadmin@domain.com "id:~~roleId~~" customer
gam config csv_input_row_filter "scopeType:regex:ORG_UNIT" redirect stdout ./UpdateNewAdminOrgUnitRoles.txt multiprocess redirect stderr stdout csv CurrentAdminRoles.csv gam create admin newadmin@domain.com "id:~~roleId~~" org_unit "id:~~orgUnitId~~"
```

