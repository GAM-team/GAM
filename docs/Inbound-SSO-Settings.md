Beginning with GAM 6.31, you can now manage Workspace / Cloud Identity Inbound SSO settings. You can add SAML SSO profiles, upload certificates for those profiles and assign the profiles to OrgUnits or Groups.

- [Create an Inbound SSO Profile](#create-an-inbound-sso-profile)
- [Update an Inbound SSO Profile](#update-an-inbound-sso-profile)
- [Get Info About an Inbound SSO Profile](#get-info-about-an-inbound-sso-profile)
- [Delete an Inbound SSO Profile](#delete-an-inbound-sso-profile)
- [Print/show Inbound SSO Profiles](#printshow-inbound-sso-profiles)
- [Create or Replace Credentials](#create-or-replace-credentials)
- [Delete Credentials](#delete-credentials)
- [Print/show Credentials](#printshow-credentials)
- [Create an Inbound SSO Assignment](#create-an-inbound-sso-assignment)
- [Update an Inbound SSO Assignment](#update-an-inbound-sso-assignment)
- [Get Info About an Inbound SSO Assignment](#get-info-about-an-inbound-sso-assignment)
- [Print/show Inbound SSO Assignments](#printshow-inbound-sso-assignments)

# Create an Inbound SSO Profile
## Syntax
```
gam create inboundssoprofile [name <name>] [entityid <entityid>] [loginurl <url>] [logouturl <url>] [changepasswordurl <url>]
```
Creates a new Inbound SSO profile with details about the remote SAML IDP. All fields are optional on create but must be set in order for the profile to be considered complete and assignable to groups/orgunits. Name and entityid specify the name and entity ID for the profile. loginurl, logouturl and changepasswordurl specify the IDP URLs for the respective actions.

## Example
This example creates a profile for your SimpleSAMLPHP IDP
```
gam create inboundssoprofile name "SimpleSAMLPHP" entityid simplesamlphp loginurl "https://dev2.andreas.feide.no/simplesaml/saml2/idp/SSOService.php" logouturl "https://www.google.com" changepasswordurl "https://www.google.com"
```
----

# Update an Inbound SSO Profile
## Syntax
```
gam update inboundssoprofile <profile name or id:profile_id> [name <newname>] [entityid <newentityid>] [loginurl <url>] [logouturl <url>] [changepasswordurl <url>]
```
Update an existing Inbound SSO Profile. The profile to update can be specified using the profile name like "SimpleSAMLPHP" or the unique ID Of the profile prefixed with "id:". The name, entityid, loginurl, logouturl and changepasswordurl parameters can optionally be entered in order to update those respective fields for the profile.

## Example
This example updates the logout URL for our profile.
```
gam update inboundssoprofile "SimpleSAMLPHP" logouturl "https://dev2.andreas.feide.no/logout.html"
```
----

# Get Info About an Inbound SSO Profile
## Syntax
```
gam info inboundssoprofile <profile name or id:profile>
```
Show information about an existing profile. The profile can be referenced by name or unique ID prefixed with id:

## Example
Shows information about a profile
```
gam info inboundssoprofile SimpleSAMLPHP
```
----

# Delete an Inbound SSO Profile
## Syntax
```
gam delete inboundssoprofile <profile name or id:profile>
```
Deletes an existing inboundssoprofile. The profile can be referenced by name or unique ID prefixed with id:

## Example
Deletes a profile
```
gam delete inboundssoprofile SimpleSAMLPHP
```
----

# Print/show Inbound SSO Profiles
## Syntax
```
gam print|show inboundssoprofiles [todrive]
```
Prints (CSV output) or shows (human readable output) all current Inbound SSO Profiles. On print only, the optional argument todrive causes GAM to generate a Google Sheet of the CSV results rather than printing them to the console.

## Example
This example shows all current profiles.
```
gam show inboundssoprofiles
```
----

# Create or Replace Credentials
## Syntax
```
gam create inboundssocredential [profile <profile name or id:profile_id>] [pemfile <filename>] [generate_key] [key_size] [replace_oldest]
```
Creates a new key for the given Inbound SSO profile or replaces the oldest one (Google allows 2 credentials per profile). The profile argument is mandatory and specifies which Inbound SSO profile the credentials should be associated with. pemfile "filename" or generate_key must be specified in order to upload a RSA/DSA PEM file's contents or generate a new RSA private key and public certificate and upload the generated certificate. The generated filenames will show on the console. key_size specifies the size of the RSA key GAM should generate. Allowed values are 1024, 2048 and 4096. replace_oldest specifies that if there are already two credentials for the profile (and only if there are two), the oldest credentials should be deleted to make room for the new credential you are creating.

**IMPORTANT** Google ignores any expiration date on public certificates. As long as the public certificate credential exists in the profile Google will allow logins which are signed by the corresponding private key. You should ALWAYS delete old certificates once they should no longer be in use.

## Example
This example uploads an existing public certificate contained in a PEM file
```
gam create inboundssocredential profile SimpleSAMLPHP pemfile new_pub_cert.pem
```
This example generates a new 4k key and replaces the oldest key if there are already two.
```
gam create inboundssocredential profile SimpleSAMLPHP generate_key key_size 4096 replace_oldest
```
----

# Delete Credentials
## Syntax
```
gam delete inboundssocredential <name>
```
Deletes an existing Inbound SSO credential. The name is the unique ID Google assigns to a credential.

## Example
This example deletes an existing credential by name.
```
gam delete inboundssocredential inboundSamlSsoProfiles/03h0nwgl1qms6ww/idpCredentials/K8748028
```
----
 
# Print/show Credentials
## Syntax
```
gam print|show inboundssocredentials [profiles <name or id:profile>,<another name>] [todrive]
```
Print (CSV output) or show (human readable output) the current Inbound SSO credentials. The optional argument profiles specifies the name or ID of Inbound SSO profiles (comma separated) whose credentials should be output. On print, the optional argument todrive causes a Google Sheet to be generated with the CSV output rather than printing it to the console.

## Example
This example print all credentials to a Google Sheet.
```
gam print inboundssocredentials todrive
```
This example shows the credentials for a single profile.
```
gam show inboundssocredentials profile SimpleSAMLPHP
```
----

# Create an Inbound SSO Assignment
## Syntax
```
gam create inboundssoassignment [profile <name or id:profile_id>] [group groupemail@domain.com] [orgunit /OrgUnit/Path] [mode SAML_SSO|SSO_OFF|DOMAIN_WIDE_SAML_IF_ENABLED] [rank <number>] [never_redirect]
```
Assigns a given Inbound SSO profile to a group or orgunit. You must specify one of group or orgunit. mode is also a mandatory argument and specifies the SSO behavior of the assignment. Use one of SAML_SSO, SSO_OFF or DOMAIN_WIDE_SAML_IF_ENABLED. If mode is SAML_SSO you must specify the profile to assign with profile. rank is optional for group assignments and specifies the numeric ranking of the assignment for priority. The rank for orgunit assignments is always zero (0). The optional argument never_redirect causes Google to never redirect to the IDP (SP initiated login disabled, IDP initiated login will work).

## Example
This example assigns a profile to the Sales group
```
gam create inboundssoassignment profile SimpleSAMLPHP group sales@acme.com mode SAML_SSO
```
----

# Update an Inbound SSO Assignment
## Syntax
```
gam update inboundssoassignment group|orgunit [profile <name or id:profile_id>] [mode SAML_SSO|SSO_OFF|DOMAIN_WIDE_SAML_IF_ENABLED] [rank <number>] [never_redirect]
```
Updates an existing Inbound SSO assignment based on the group or orgunit. mode specifies the assigned SSO mode and should be one of SAML_SSO, SSO_OFF or DOMAIN_WIDE_SAML_IF_ENABLED. If mode is SAML_SSO, profile can be specified to update the SSO profile assigned. rank is optional for group assignments and specifies the numeric ranking which sets priority of the assignment, rank for OrgUnits is always 0. never_redirect is optional and disables Google redirecting users to the IDP, IDP-initiated login is still allowed.

## Example
This example turns SSO on for the root OU
```
gam update inboundssoassignment ou:/ mode SAML_SSO profile "SimpleSAMLPHP"
```
----

# Get Info About an Inbound SSO Assignment
## Syntax
```
gam info inboundssoassignment group|orgunit
```
Displays information about an existing Inbound SSO assignment.

## Example
These examples shows the assignment status of the root OU and the sales@acme.com group.
```
gam info inboundssoassignment ou:/
gam info inboundssoassignment group:sales@acme.com
```
----

# Print/show Inbound SSO Assignments
## Syntax
```
gam print|show inboundssoassignments [todrive]
```
Prints (CSV format) or shows (human readable format) all current Inbound SSO assignments. On print, if todrive is specified a Google Sheet of the CSV results is created rather than outputting it to the console.

## Example
This example shows all current assignments
```
gam show inboundssoassignments
```