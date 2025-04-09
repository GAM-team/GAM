Google [Context Aware Access (CAA)](https://support.google.com/a/answer/9275380) provides contextual security requirements for endpoints accessing Google Workspace Services. GAM 6.20 and newer can create and manage access levels which can be assigned to Workspace services for your users.

- [Grant Service Account Rights to Manage CAA](#grant-service-account-rights-to-manage-caa)
- [Creating an Access Level](#creating-an-access-level)
- [Updating an Access Level](#updating-an-access-level)
- [Parameters for Basic Levels](#parameters-for-basic-levels)
- [Showing all Access Levels](#showing-all-access-levels)
- [Deleting an Access Level](#deleting-an-access-level)

# Grant Service Account Rights to Manage CAA

In order for GAM to manage CAA access levels, you need to grant your service account a special role for your GCP organization.
1. Run a GAM command like `gam print caalevels`. This will show you the service account email and role you need to grant it. Copy the service account email.
1. As an organization admin (Workspace Super Admin should work) go to [https://console.cloud.google.com](https://console.cloud.google.com).
1. In the top blue bar, to the right of "Google Cloud Platform" click the selected project.
1. Select your GCP organization which has a building icon next to it and is named after your primary domain.
1. In the 3-bar "hamburger" menu at the top left, click IAM & Admin > IAM. The page should show `permissions for organization <primary domain>`
1. Near the top click "Add".
1. Enter the service account email address you recorded earlier.
1. Select Roles > Access Context Manager > Access Context Manager Editor.
1. Click Save. It may take 15 minutes or more for the role permissions to propagate.
1. Confirm the role is in place by re-running `gam print caalevels`

# Creating an Access Level

## Syntax

```
gam create caalevel <name> [basic <basic condition> | custom <CEL query>]
```

Creates a new access level with the defined conditions. CAA supports basic and custom conditions. Custom is followed by [a CEL query](https://cloud.google.com/access-context-manager/docs/custom-access-level-spec). Basic is followed by a [basic condition](#parameters-for-basic-levels).

## Example

This example defines a custom access level that requires the user to use a Cloud-managed Chrome browser (CBCM) or be logged into a Cloud-managed Chrome profile.

```
gam create caalevel custom "device.chrome.management_state == ChromeManagementState.CHROME_MANAGEMENT_STATE_BROWSER_MANAGED | ChromeManagementState.CHROME_MANAGEMENT_STATE_PROFILE_MANAGED"
```

This example creates a basic access level that requires the user to come from the US or Canada regions

```
gam create caalevel CORP_COUNTRIES basic condition regions US,CA endcondition
```

This example creates a basic access level that requires the user come from one of the given IP ranges

```
gam create caalevel CORP_IPS basic condition ipsubnetworks 1.2.3.0/24,4.5.6.0/24 endcondition
```

----

# Updating an Access Level

## Syntax

```
gam update caalevel <name> [basic <basic condition> | custom <CEL query>]
```

Updates an existing access level. CAA supports basic and custom conditions. Custom is followed by [a CEL query](https://cloud.google.com/access-context-manager/docs/custom-access-level-spec). Basic is followed by a [basic condition](#parameters-for-basic-levels).

## Examples

This example adds UK to the allowed regions for CORP_COUNTRIES

```
gam update caalevel CORP_COUNTRIES basic condition regions US,CA,UK endcondition
```

----

# Parameters for Basic Levels

## Syntax

```
gam create/update accesslevel <name> basic
  combiningfunction and|or
  condition
    negate true|false
    ipsubnetworks ip4range,ip6range,...
    regions <country code>,country code>,...
    devicepolicy
      requirescreenlock true|false
      allowedencryptionstatuses ENCRYPTION_UNSUPPORTED,ENCRYPTED,UNENCRYPTED
      alloweddevicemanagementlevels NONE,BASIC,COMPLETE
      requireadminapproval true|false
      requirecorpowned true|false
      osconstraints DESKTOP_MAC:version,DESKTOP_WINDOWS:version,DESKTOP_LINUX:version,
                    DESKTOP_CHROME_OS:version,VERIFIED_DESKTOP_CHROME_OS:version,
                    ANDROID:version,IOS:version
    enddevicepolicy
  endcondition
  condition
    <another condition>
  endcondition
```

Defines a basic access level. The combiningfunction argument specifies if a user must pass all 2+ conditions (AND) or only one (OR). The negate argument specifies whether a user that matches the condition passes it or fails. The ipsubnetworks argument specifies a comma-separated list of IPv4 or IPv6 networks the user must be coming from to match. The regions argument specifies a comma-separated list of country/regions the user must be coming from to match. The device policy argument specifies characteristics of the user's device that must be present to match.

----

# Showing all access levels

## Syntax

```
gam print caalevels
```

Prints out the current defined access levels.

----

# Deleting an Access Level

## Syntax

```
gam delete caalevel <name>
```

Deletes the specified access level.

----