# Administrators
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Display administrative privileges](#display-administrative-privileges)
- [Manage administrative roles](#manage-administrative-roles)
- [Display administrative roles](#display-administrative-roles)
- [Create an administrator](#create-an-administrator)
- [Delete an administrator](#delete-an-administrator)
- [Display administrators](#display-administrators)
- [Copy roles from one administrator to another](#copy-roles-from-one-administrator-to-another)

## API documentation
* [About Administrator roles](https://support.google.com/a/answer/33325?ref_topic=4514341)
* [Directory API - Privileges](https://developers.google.com/admin-sdk/directory/reference/rest/v1/privileges)
* [Directory API - Roles](https://developers.google.com/admin-sdk/directory/reference/rest/v1/roles)
* [Directory API - Role SAssignments](https://developers.google.com/admin-sdk/directory/reference/rest/v1/roleAssignments)

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

Here is the output from `gam show privileges`; use this to find `<Privilege>`.
```
Show 91 Privileges
  Privilege: MANAGE_CSE_SETTINGS (1/91)
    serviceId: 02pta16n4hxgyp2
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_PLAY_FOR_WORK_STORE (2/91)
    serviceId: 00tyjcwt49hs5nq
    serviceName: play_for_work
    isOuScopable: False
  Privilege: MANAGE_ENTERPRISE_PRIVATE_APPS (3/91)
    serviceId: 00tyjcwt49hs5nq
    serviceName: play_for_work
    isOuScopable: False
  Privilege: MANAGE_EXTERNALLY_HOSTED_APK_UPLOAD_IN_PLAY (4/91)
    serviceId: 00tyjcwt49hs5nq
    serviceName: play_for_work
    isOuScopable: False
  Privilege: MANAGE_PLAY_FOR_WORK_STORE (5/91)
    serviceId: 02w5ecyt3pkeyqi
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_ENTERPRISE_PRIVATE_APPS (6/91)
    serviceId: 02w5ecyt3pkeyqi
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_EXTERNALLY_HOSTED_APK_UPLOAD_IN_PLAY (7/91)
    serviceId: 02w5ecyt3pkeyqi
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (8/91)
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
  Privilege: APP_ADMIN (9/91)
    serviceId: 03cqmetx3hnlpuf
    serviceName: gplus
    isOuScopable: False
  Privilege: GPLUS_SQUARE_BATCH_ADD (10/91)
    serviceId: 03cqmetx3hnlpuf
    serviceName: gplus
    isOuScopable: False
  Privilege: GPLUS_CONTENT_MANAGER_PRIVILEGE (11/91)
    serviceId: 03cqmetx3hnlpuf
    serviceName: gplus
    isOuScopable: False
  Privilege: APP_ADMIN (12/91)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: ACCESS_EMAIL_LOG_SEARCH (13/91)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: ACCESS_ADMIN_QUARANTINE (14/91)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: ACCESS_RESTRICTED_QUARANTINE (15/91)
    serviceId: 039kk8xu49mji9t
    serviceName: gmail
    isOuScopable: False
  Privilege: APP_ADMIN (16/91)
    serviceId: 01tuee744837sjz
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_COURSE_SETTINGS (17/91)
    serviceId: 037m2jsg4g9nirj
    serviceName: Unknown
    isOuScopable: True
  Privilege: MANAGE_LTI_CREDENTIAL_MANAGEMENT_MODE (18/91)
    serviceId: 037m2jsg4g9nirj
    serviceName: Unknown
    isOuScopable: True
  Privilege: APP_ADMIN (19/91)
    serviceId: 01baon6m1wv6b0p
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (20/91)
    serviceId: 01yyy98l4k9lq4l
    serviceName: directory
    isOuScopable: False
    childPrivileges: 3
      Privilege: DIRECTORY_SETTINGS_READONLY (1/3)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
        childPrivileges: 2
          Privilege: PROFILE_EDITABILITY_READONLY (1/2)
            serviceId: 01yyy98l4k9lq4l
            serviceName: directory
            isOuScopable: False
          Privilege: CUSTOM_DIRECTORY_READONLY (2/2)
            serviceId: 01yyy98l4k9lq4l
            serviceName: directory
            isOuScopable: False
      Privilege: PROFILE_EDITABILITY_READWRITE (2/3)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
      Privilege: CUSTOM_DIRECTORY_READWRITE (3/3)
        serviceId: 01yyy98l4k9lq4l
        serviceName: directory
        isOuScopable: False
  Privilege: LDAP_MANAGER (21/91)
    serviceId: 02lwamvv18la4iw
    serviceName: ldap
    isOuScopable: False
  Privilege: LDAP_PASSWORD_REBIND (22/91)
    serviceId: 02lwamvv18la4iw
    serviceName: ldap
    isOuScopable: True
    childPrivileges: 1
      Privilege: LDAP_PASSWORD_REBIND_READONLY
        serviceId: 02lwamvv18la4iw
        serviceName: ldap
        isOuScopable: True
  Privilege: APP_ADMIN (23/91)
    serviceId: 0319y80a15kueje
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (24/91)
    serviceId: 044sinio4cntx2o
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (25/91)
    serviceId: 01ksv4uv2d2noaq
    serviceName: sites
    isOuScopable: False
  Privilege: ADMIN_DASHBOARD (26/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: True
  Privilege: SERVICES (27/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: SECURITY_SETTINGS (28/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: SUPPORT (29/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: ADMIN_DOMAIN_SETTINGS (30/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: REPORTS (31/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: ADMIN_DASHBOARD (32/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: True
  Privilege: SERVICES (33/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: SUPPORT (34/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: REPORTS (35/91)
    serviceId: 01ci93xb3tmzyin
    serviceName: admin
    isOuScopable: False
  Privilege: APP_ADMIN (36/91)
    serviceId: 03fwokq01e2ht7x
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: UDM_NETWORK_ADMIN
        serviceId: 03fwokq01e2ht7x
        serviceName: Unknown
        isOuScopable: True
  Privilege: ADMIN_MATTER (37/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: REMOVE_HOLD (38/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: MANAGE_SEARCHES (39/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: MANAGE_EXPORTS (40/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: True
  Privilege: MANAGE_RETENTION_POLICY (41/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: False
    childPrivileges: 1
      Privilege: VIEW_RETENTION_POLICY
        serviceId: 03l18frh45c63dw
        serviceName: vault
        isOuScopable: False
  Privilege: AUDIT_SYSTEM (42/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: False
  Privilege: ACCESS_ALL_MATTERS (43/91)
    serviceId: 03l18frh45c63dw
    serviceName: vault
    isOuScopable: False
  Privilege: APP_ADMIN (44/91)
    serviceId: 02afmg282jiquyg
    serviceName: device_management
    isOuScopable: False
  Privilege: APP_ADMIN (45/91)
    serviceId: 037m2jsg3ckz96v
    serviceName: calendar
    isOuScopable: False
    childPrivileges: 2
      Privilege: CALENDAR_SETTINGS (1/2)
        serviceId: 037m2jsg3ckz96v
        serviceName: calendar
        isOuScopable: False
        childPrivileges: 1
          Privilege: CALENDAR_SETTINGS_READ
            serviceId: 037m2jsg3ckz96v
            serviceName: calendar
            isOuScopable: False
      Privilege: CALENDAR_RESOURCE (2/2)
        serviceId: 037m2jsg3ckz96v
        serviceName: calendar
        isOuScopable: False
        childPrivileges: 2
          Privilege: ROOM_INSIGHTS_DASHBOARD_ACCESS (1/2)
            serviceId: 037m2jsg3ckz96v
            serviceName: calendar
            isOuScopable: False
          Privilege: CALENDAR_RESOURCE_MANAGE (2/2)
            serviceId: 037m2jsg3ckz96v
            serviceName: calendar
            isOuScopable: False
            childPrivileges: 1
              Privilege: CALENDAR_RESOURCE_READ
                serviceId: 037m2jsg3ckz96v
                serviceName: calendar
                isOuScopable: False
  Privilege: APP_ADMIN (46/91)
    serviceId: 03dy6vkm2sk0pzo
    serviceName: docs
    isOuScopable: False
    childPrivileges: 5
      Privilege: DOCS_TEMPLATE_ADMIN (1/5)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: MIGRATE_TO_TEAM_DRIVE (2/5)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: WRITE_APPS_METADATA_SCHEMAS (3/5)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: VIEW_SITE_DETAILS (4/5)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
      Privilege: MANAGE_CLASSIC_GOOGLE_SITES (5/5)
        serviceId: 03dy6vkm2sk0pzo
        serviceName: docs
        isOuScopable: False
  Privilege: APP_ACCESS (47/91)
    serviceId: 03cqmetx1vygwki
    serviceName: Unknown
    isOuScopable: False
  Privilege: ORGANIZATION_UNITS_ALL (48/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: True
    childPrivileges: 4
      Privilege: ORGANIZATION_UNITS_CREATE (1/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: ORGANIZATION_UNITS_RETRIEVE (2/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: ORGANIZATION_UNITS_UPDATE (3/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: ORGANIZATION_UNITS_DELETE (4/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
  Privilege: USERS_ALL (49/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: True
    childPrivileges: 5
      Privilege: USERS_CREATE (1/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_RETRIEVE (2/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_UPDATE (3/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
        childPrivileges: 6
          Privilege: USERS_ALIAS (1/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_MOVE (2/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_RESET_PASSWORD (3/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_FORCE_PASSWORD_CHANGE (4/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_ADD_NICKNAME (5/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
          Privilege: USERS_SUSPEND (6/6)
            serviceId: 00haapch16h1ysv
            serviceName: admin_apis
            isOuScopable: True
      Privilege: USERS_UPDATE_CUSTOM_ATTRIBUTES_USER_PRIVILEGE_GROUP (4/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
      Privilege: USERS_DELETE (5/5)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: True
  Privilege: GROUPS_ALL (50/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 4
      Privilege: GROUPS_CREATE (1/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
      Privilege: GROUPS_RETRIEVE (2/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
      Privilege: GROUPS_UPDATE (3/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
      Privilege: GROUPS_DELETE (4/4)
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: USER_SECURITY_ALL (51/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: True
  Privilege: DATATRANSFER_API_PRIVILEGE_GROUP (52/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: DOMAIN_REGISTRATION_MANAGEMENT (53/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: SCHEMA_MANAGEMENT (54/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: SCHEMA_RETRIEVE
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: LICENSING (55/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: LICENSING_READ
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: BILLING (56/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: BILLING_READ
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: SAML2_SERVICE_PROVIDER (57/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: DOMAIN_MANAGEMENT (58/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: UPGRADE_CONSUMER_CONVERSION (59/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: TRUSTED_DOMAIN_WHITELIST_WRITE (60/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: TRUSTED_DOMAIN_WHITELIST_READ
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: FULL_MIGRATION_ACCESS (61/91)
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
  Privilege: GROUPS_MANAGE_SECURITY_LABEL (62/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: GROUPS_MANAGE_LOCKED_LABEL (63/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: ADMIN_REPORTING_ACCESS (64/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
    childPrivileges: 1
      Privilege: REPORTING_AUDIT_ACCESS
        serviceId: 00haapch16h1ysv
        serviceName: admin_apis
        isOuScopable: False
  Privilege: SUPPORT_PRIVILEGE_GROUP (65/91)
    serviceId: 00haapch16h1ysv
    serviceName: admin_apis
    isOuScopable: False
  Privilege: APPS_INCIDENTS_FULL_ACCESS (66/91)
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
  Privilege: APP_ADMIN (67/91)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: ADMIN_OVERSIGHT_MANAGE_CLASSES (68/91)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: EDU_ANALYTICS_DATA_ACCESS (69/91)
    serviceId: 019c6y1840fzfkt
    serviceName: classroom
    isOuScopable: True
  Privilege: APP_ADMIN (70/91)
    serviceId: 037m2jsg46www3g
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DYNAMITE_SETTINGS (71/91)
    serviceId: 03whwml44f3n4vd
    serviceName: Unknown
    isOuScopable: False
  Privilege: MODERATE_DYNAMITE_REPORT (72/91)
    serviceId: 03whwml44f3n4vd
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DYNAMITE_SPACES (73/91)
    serviceId: 03whwml44f3n4vd
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (74/91)
    serviceId: 03hv69ve4bjwe54
    serviceName: Unknown
    isOuScopable: True
    childPrivileges: 6
      Privilege: MANAGE_CHROME_USER_SETTINGS (1/6)
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
      Privilege: MANAGE_CHROME_BROWSERS (2/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 1
          Privilege: MANAGED_CHROME_BROWSERS_READ_ONLY
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
      Privilege: VIEW_CHROME_REPORTS (3/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 4
          Privilege: VIEW_CHROME_EXTENSIONS_REPORT (1/4)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_VERSION_REPORT (2/4)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_INSIGHTS_REPORT (3/4)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
          Privilege: VIEW_CHROME_PRINTERS_REPORT (4/4)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
      Privilege: MANAGE_PRINTERS (4/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
      Privilege: MANAGE_DEVICES (5/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
        childPrivileges: 2
          Privilege: MANAGE_DEVICES_READ_ONLY (1/2)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
            childPrivileges: 1
              Privilege: TELEMETRY_API
                serviceId: 03hv69ve4bjwe54
                serviceName: Unknown
                isOuScopable: True
                childPrivileges: 19
                  Privilege: TELEMETRY_API_DEVICE (1/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_USER (2/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_AUDIO_REPORT (3/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_BUS_DEVICE_INFO (4/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_OS_REPORT (5/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_CPU_INFO (6/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_CPU_REPORT (7/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_MEMORY_INFO (8/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_MEMORY_REPORT (9/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_GRAPHICS_INFO (10/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_GRAPHICS_REPORT (11/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_BATTERY_INFO (12/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_BATTERY_REPORT (13/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_STORAGE_INFO (14/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_STORAGE_REPORT (15/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_NETWORK_INFO (16/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_NETWORK_REPORT (17/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_DEVICE_ACTIVITY_REPORT (18/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
                  Privilege: TELEMETRY_API_PERIPHERALS_REPORT (19/19)
                    serviceId: 03hv69ve4bjwe54
                    serviceName: Unknown
                    isOuScopable: True
          Privilege: DEVICE_ACTION_CRD (2/2)
            serviceId: 03hv69ve4bjwe54
            serviceName: Unknown
            isOuScopable: True
      Privilege: MANAGE_DEVICE_SETTINGS (6/6)
        serviceId: 03hv69ve4bjwe54
        serviceName: Unknown
        isOuScopable: True
  Privilege: SERVICE_DATA_DOWNLOADER (75/91)
    serviceId: 03hv69ve4bjwe54
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DIRECTORY_SYNC_SETTINGS (76/91)
    serviceId: 0147n2zr1ynkkmf
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: READ_DIRECTORY_SYNC_SETTINGS
        serviceId: 0147n2zr1ynkkmf
        serviceName: Unknown
        isOuScopable: False
  Privilege: APP_ADMIN (77/91)
    serviceId: 0279ka651l5iy5q
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: ADMIN_QUALITY_DASHBOARD_ACCESS
        serviceId: 0279ka651l5iy5q
        serviceName: Unknown
        isOuScopable: False
  Privilege: SECURITY_SETTINGS (78/91)
    serviceId: 00vx122734tbite
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: INBOUND_SSO_SETTINGS
        serviceId: 00vx122734tbite
        serviceName: Unknown
        isOuScopable: False
  Privilege: VIEW_DLP_RULE (79/91)
    serviceId: 02250f4o3hg8pg8
    serviceName: Unknown
    isOuScopable: False
  Privilege: MANAGE_DLP_RULE (80/91)
    serviceId: 02250f4o3hg8pg8
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (81/91)
    serviceId: 00nmf14n14wtgcf
    serviceName: app_maker
    isOuScopable: False
  Privilege: VIEW_ALL_PROJECTS (82/91)
    serviceId: 00nmf14n14wtgcf
    serviceName: app_maker
    isOuScopable: False
  Privilege: APP_ADMIN (83/91)
    serviceId: 02zbgiuw2wdxo5p
    serviceName: youtube
    isOuScopable: False
  Privilege: APP_ADMIN (84/91)
    serviceId: 03as4poj2zjehv7
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (85/91)
    serviceId: 02afmg283v5nmx6
    serviceName: Unknown
    isOuScopable: False
    childPrivileges: 1
      Privilege: ADMIN_QUALITY_DASHBOARD_ACCESS
        serviceId: 02afmg283v5nmx6
        serviceName: Unknown
        isOuScopable: False
  Privilege: APP_ADMIN (86/91)
    serviceId: 00upglbi0qz687j
    serviceName: takeout
    isOuScopable: False
  Privilege: CLOUD_PRINT_MANAGER (87/91)
    serviceId: 02bn6wsx379ol8g
    serviceName: cloud_print
    isOuScopable: False
  Privilege: MANAGE_AGE_BASED_ACCESS_SETTINGS_AGE_LABEL (88/91)
    serviceId: 046r0co22dnadsi
    serviceName: Unknown
    isOuScopable: True
    childPrivileges: 1
      Privilege: AGE_BASED_ACCESS_SETTINGS_AGE_LABEL_READ
        serviceId: 046r0co22dnadsi
        serviceName: Unknown
        isOuScopable: True
  Privilege: LOGO_PRIVILEGE_GROUP (89/91)
    serviceId: 03j2qqm31d4j55e
    serviceName: Unknown
    isOuScopable: False
  Privilege: APP_ADMIN (90/91)
    serviceId: 04f1mdlm0ki64aw
    serviceName: cros
    isOuScopable: True
    childPrivileges: 7
      Privilege: MANAGE_DEVICES (1/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_USER_SETTINGS (2/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
        childPrivileges: 1
          Privilege: MANAGE_APPLICATION_SETTINGS
            serviceId: 04f1mdlm0ki64aw
            serviceName: cros
            isOuScopable: True
      Privilege: MANAGE_DEVICE_SETTINGS (3/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_BROWSERS (4/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: VIEW_EXTENSIONS_REPORT (5/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: VIEW_VERSION_REPORT (6/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
      Privilege: MANAGE_PRINTERS (7/7)
        serviceId: 04f1mdlm0ki64aw
        serviceName: cros
        isOuScopable: True
  Privilege: APP_ADMIN (91/91)
    serviceId: 02et92p02l9sq0n
    serviceName: Unknown
    isOuScopable: True
```

## Manage administrative roles
```
gam create adminrole <String> privileges all|all_ou|<PrivilegeList> [description <String>]
gam update adminrole <RoleItem> [name <String>] [privileges all|all_ou|<PrivilegeList>] [description <String>]
gam delete adminrole <RoleItem>
```
* `privileges all` - All defined privileges
* `privileges all_ou` - All defined privileges than can be scoped to an OU
* `privileges <PrivilegeList>` - A specific list of privileges

## Display administrative roles
```
gam info adminrole <RoleItem> [privileges]
gam print adminroles|roles [todrive <ToDriveAttribute>*]
        [privileges] [oneitemperrow]
gam show adminroles|roles [todrive <ToDriveAttribute>*] [privileges]
```
* `privileges` - Display privileges associated with each role

By default, all privileges for a role are shown on one row as a repeating item.
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

