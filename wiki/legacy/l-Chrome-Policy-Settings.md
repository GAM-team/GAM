- [Showing Chrome Schema of Policy Settings](#showing-chrome-schema-of-policy-settings)
- [Showing Current Chrome Policy For An OrgUnit](#showing-current-chrome-policy-for-an-orgunit)
- [Updating Chrome Policy](#updating-chrome-policy)
- [Clearing Chrome Policies](#clearing-chrome-policies)

## Showing Chrome Schema of Policy Settings
### Syntax
```
gam show chromeschema [filter <filter>]
```
Shows the schema of all possible Chrome policy settings available for your organization. The optional filter argument filters results down to matches. The schema is comprised of the top level schema name which groups the policy settings together, an individual setting, the type of the setting (string, boolean, enum) and possible values for the setting with their description.

### Example
This example prints the full schema for your organization. A truncated example output is also shown with the parts of the schema. In the example output, the schema name is chrome.users.ChromeBrowserUpdates and controls how browsers update. Within this schema there are three settings, rollbackToTargetVersionEnabled, targetVersionPrefixSetting and updateSetting. rollbackToTargetVersionEnabled and updateSetting are TYPE_ENUM meaning there is a limited set of values they can be set to. These values are described in the lines just after the setting. targetVersionPrefixSetting is TYPE_STRING so it accepts a string value as mentioned in it's description.
```
gam show chromeschema
...
chrome.users.ChromeBrowserUpdates: Chrome browser updates.
  rollbackToTargetVersionEnabled: TYPE_ENUM
    ROLLBACK_TO_TARGET_VERSION_DISABLED: Do not rollback to target version.
    ROLLBACK_TO_TARGET_VERSION_ENABLED: Rollback to target version.
  targetVersionPrefixSetting: TYPE_STRING
    Target version prefix. Specifies which version the Chrome browser should be updated to. When a value is set, Chrome will be updated to the version prefixed with this value. For example, if the value is '55.', Chrome will be updated to any minor version of 55 (e.g. 55.24.34.0 or 55.60.2.10). If the value is '55.2.', Chrome will be updated to any minor version of 55.2 (e.g. 55.2.34.100 or 55.2.2.1). If the value is '55.24.34.1', Chrome will be updated to that specific version only. Chrome may stop updating or not rollback if the specified version is more than three major milestones old.
  updateSetting: TYPE_ENUM
    UPDATES_DISABLED: Updates disabled.
    UPDATES_ENABLED: Always allow updates.
    MANUAL_UPDATES_ONLY: Manual updates only.
    AUTOMATIC_UPDATES_ONLY: Automatic updates only.
...
```
----

## Showing Current Chrome Policy For An OrgUnit
### Syntax
```
gam show chromepolicy orgunit <orgunit> [printer_id <id>] [app_id <id>]
```
Shows the current Chrome policies for the given OrgUnit. The optional argument printer_id will scope the returned policies to those set on the given printer. The optional argument app_id will scope the returned policies to those set on the given app.

### Example
This example prints policies for the root OrgUnit.
```
gam show chromepolicy orgunit /
```
This example shows policies for the identified printer.
```
gam show chromepolicy orgunit / printer_id 0gjdgxs3dgp3kj
```
----

## Updating Chrome Policy
### Syntax
```
gam update chromepolicy [orgunit <orgunit>] [printer_Id <id>] [app_id <id>] schema1 setting1 value setting2 value schema2 setting1 value ...
```
Updates the policy settings of the given OrgUnit. The optional printer_id and app_id specify a printer or app to set policy for. Policies involve a schema name, the specific setting of the schema and a value. You can set multiple schemas and settings with one command but they must all apply to the same OrgUnit / printer / app.

### Example
This example sets Chrome to limit updates to version 89 for the /Browsers OrgUnit. Browsers on newer versions will be rolled back.
```
gam update chromepolicy orgunit /Browsers chrome.users.ChromeBrowserUpdates rollbackToTargetVersionEnabled ROLLBACK_TO_TARGET_VERSION_ENABLED targetVersionPrefixSetting "89." updateSetting UPDATES_ENABLED
```
This example blocks notifications except for specific URLs
```
gam update chromepolicy orgunit /Browsers chrome.users.Notifications defaultNotificationsSetting BLOCK_NOTIFICATIONS notificationsAllowedForUrls *.google.com,*.salesforce.com,*.youtube.com
```

## Clearing Chrome Policies
### Syntax
```
gam delete policy [orgunit <orgunit>] [printer_id <id>] [app_id <id>] schema1 schema2 schema3 ...
```
Clears the settings for the given schema so that they inherit from their parent OrgUnit or, in the case of the / root OrgUnit, inherit from the Google default setting. The optional printer_id and app_id specify a specific printer or app to clear the policies for. Multiple schemas can be cleared by specifying each one separated by spaces but the policies must all apply to the given OrgUnit / printer / app combo.

### Example
This example clears the Chrome update and notification policies for the /Browsers OrgUnit. They will then inherit either from the / root OrgUnit if set there or from the Google default setting.
```
gam delete chromepolicy orgunit /Browsers chrome.users.Notifications chrome.users.ChromeBrowserUpdates
```