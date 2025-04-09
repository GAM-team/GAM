# Context-Aware Access Levels

- [Notes](#Notes)
- [API documentation](#api-documentation)
- [Grant Service Account Rights to Manage CAA](#grant-service-account-rights-to-manage-caa)
- [Definitions](#definitions)
- [Parameters for Basic Levels](#parameters-for-basic-levels)
- [Create an Access Level](#create-an-access-level)
- [Update an Access Level](#update-an-access-level)
- [Update Access Levels with JSON](#update-access-levels-with-json)
- [Delete an Access Level](#delete-an-access-level)
- [Display all Access Levels](#display-all-access-levels)
- [CAA Region Codes](#caa-region-codes)

## Notes
This Wiki page was built directly from Jay Lee's Wiki page; my sincere thanks for his efforts.

GAM 6.20.00 and newer can create and manage access levels which can be assigned to Workspace services for your users.

To use these features you must update your project.
```
gam update project
```

## API documentation
* [Context-Aware Access documentation](https://support.google.com/a/answer/9275380)
* [Access Context Manager API - Access Policies](https://cloud.google.com/access-context-manager/docs/reference/rest/v1/accessPolicies)

## Grant Service Account Rights to Manage CAA
In order for GAM to manage CAA access levels, you need to grant your service account a special role for your GCP organization.
1. Run a GAM command like `gam print caalevels`. This will show you the service account email and role you need to grant it. Copy the service account email.
2. You can also get the value from oauth2service.json: `"client_email": "gam-project-abc-123-xyz@gam-project-abc-123-xyz.iam.gserviceaccount.com"`
3. As an organization admin (Workspace Super Admin should work) go to [https://console.cloud.google.com/iam-admin/iam](https://console.cloud.google.com/iam-admin/iam).
4. In the top blue bar, to the right of `Google Cloud Platform` click the desired `<Project Name>`.
5. If the page shows `Permissions for organization <Primary Domain>`", skip the next step.
6. If the page shows `Permissions for project <Project Name>`", click the building icon immediately to the left of your `<Primary Domain>` in the Inheritance column.
7. Near the top click `Add`.
8. Enter the service account email address you recorded earlier into the `New principals*` box.
9. In the `Select a role*` box, select Access Context Manager > Access Context Manager Editor.
10. Click `Save`. It may take 15 minutes or more for the role permissions to propagate.
11. Confirm the role is in place by re-running `gam print caalevels`

## Definitions
```
<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |

<QueryCEL> ::= <String>
        See: https://cloud.google.com/access-context-manager/docs/custom-access-level-spec

<CAALevelName> ::= <String>

<CAAAllowedEncryptionStatus> ::=
        encryption_unsupported |
        encrypted |
        unencrypted
<CAAAllowedEncryptionStatusList> ::= "<CAAAllowedEncryptionStatus>(,<CAAAllowedEncryptionStatus>)"

<CAAAllowedDeviceManagementLevel> ::=
        basic |
        advanced|complete |
        none
<CAAAllowedDeviceManagementLevelList> ::= "<CAAAllowedDeviceManagementLevel>(,<CAAAllowedDeviceManagementLevel>)"

<CAACombiningFunction> ::=
        and |
        or

<CAAIPSubNetwork> ::=
        <CIDRnetmask>
<CAAIPSubNetworkList> ::= "<CAAIPSubNetwork>(,<CAAIPSubNetwork>)"

<CAAMember> ::=
        user:<EmailAddress> |
        serviceAccount:<EmailAddress>
<CAAMemberList> ::= "<CAAMember>(,<CAAMember>)"

<CAAOsType> ::=
        DESKTOP_MAC |
        DESKTOP_WINDOWS |
        DESKTOP_LINUX |
        DESKTOP_CHROME_OS |
        VERIFIED_DESKTOP_CHROME_OS |
        ANDROID |
        IOS

<CAAOsConstraint> ::=
        <CAAOsType> |
        <CAAOsType>:<String>.<String>.<String>
<CAAOsConstraintList> ::= "<CAAOsConstraint>(,<CAAOsConstraint>)"

<CAARegion> ::=
        <Character><Character>
<CAARegionList> ::= "<CAARegion>(,<CAARegion>)"

<CAADevicePolicyAttribute> ::=
        (requirescreenlock <Boolean>) |
        (allowedencryptionstatuses <CAAAllowedEncryptionStatusList>) |
        (osconstraints <CAAOsConstraintList>) |
        (alloweddevicemanagementlevels <CAAAllowedDeviceManagementLevelList>) |
        (requireadminapproval <Boolean>) |
        (requirecorpowned <Boolean>)    # See: https://www.iso.org/obp/ui/#search

<CAAConditionAttribute> ::=
        (ipsubnetworks <CAAIPSubNetworkList>) |
        (devicepolicy <CAADevicePolicyAttribute> enddevicepolicy) |
        (requiredaccesslevels <StringList>) |
        (negate <Boolean>) |
        (members <CAAMemberList>) |
        (regions <CAARegionList>)
        
<CAABasicAttribute> ::+
        (combiningfunction <CAACombiningFunction>) |
        (condition <CAAConditionAttribute>+ endcondition)
```

# Parameters for Basic Levels

```
basic
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
    ...
  endcondition
```
* The combiningfunction argument specifies if a user must pass all 2+ conditions (AND) or only one (OR).
* The negate argument specifies whether a user that matches the condition passes it or fails.
* The ipsubnetworks argument specifies a comma-separated list of IPv4 or IPv6 networks the user must be coming from to match.
* The regions argument specifies a comma-separated list of country/regions the user must be coming from to match.
* The device policy argument specifies characteristics of the user's device that must be present to match.


## Create an Access Level
Create a new access level. CAA supports basic and custom conditions.
```
gam create caalevel <String> [description <String>] (basic <CAABasicAttribute>+)|(custom <QueryCEL>)|<JSONData>
```

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
## Update an Access Level
Updates an existing access level. CAA supports basic and custom conditions.
```
gam update caalevel <CAALevelName> [description <String>] (basic <CAABasicAttribute>+)|(custom <QueryCEL>)|<JSONData>
```

## Examples
This example adds UK to the allowed regions for CORP_COUNTRIES
```
gam update caalevel CORP_COUNTRIES basic condition regions US,CA,UK endcondition
```

## Update Access Levels with JSON
Update existing CAA levels via their JSON data; create a CSV file of CAA levels.
```
gam redirect csv ./CAAlevels.csv print caalevels formatjson quotechar "'"
```
Edit the JSON column for the desired CAA level(s) in CAAlevels.csv.
Update the desired CAA level by selecting the row by it's title; repeat for each title to update.
```
gam config csv_input_row_filter "title:text='Example Title'" csv CAAlevels.csv quotechar "'" gam update caalevel "~name" json "~JSON"
```

## Example
Edit CAAlevels.csv and add UK to the allowed regions for CORP_COUNTRIES
```
{"regions": ["US", "CA", "UK"]}
```
Do the update.
```
gam config csv_input_row_filter "title:text='CORP_COUNTRIES'" csv CAAlevels.csv quotechar "'" gam update caalevel "~name" json "~JSON"
```

## Delete an Access Level
Deletes the specified access level.
```
gam delete caalevel <CAALevelName>
```
# Display all access levels
```
gam show caalevels
        [formatjson]
```
By default, Gam displays the information as an indented list of keys and values:
* `formatjson` - Display the fields in JSON format.
```
gam print caalevels [todrive <ToDriveAttribute>*]
        [formatjson [quotechar <Character>]]
```
By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format:
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## CAA Region Codes
```
AD: Andorra
AE: United Arab Emirates
AF: Afghanistan
AG: Antigua and Barbuda
AI: Anguilla
AL: Albania
AM: Armenia
AO: Angola
AQ: Antarctica
AR: Argentina
AS: American Samoa
AT: Austria
AU: Australia
AW: Aruba
AX: Åland Islands
AZ: Azerbaijan
BA: Bosnia and Herzegovina
BB: Barbados
BD: Bangladesh
BE: Belgium
BF: Burkina Faso
BG: Bulgaria
BH: Bahrain
BI: Burundi
BJ: Benin
BL: Saint Barthélemy
BM: Bermuda
BN: Brunei Darussalam
BO: Bolivia Plurinational State of
BQ: Bonaire Sint Eustatius and Saba
BR: Brazil
BS: Bahamas
BT: Bhutan
BV: Bouvet Island
BW: Botswana
BY: Belarus
BZ: Belize
CA: Canada
CC: Cocos (Keeling) Islands
CD: Congo The Democratic Republic of the
CF: Central African Republic
CG: Congo
CH: Switzerland
CI: Côte d'Ivoire
CK: Cook Islands
CL: Chile
CM: Cameroon
CN: China
CO: Colombia
CR: Costa Rica
CU: Cuba
CV: Cabo Verde
CW: Curaçao
CX: Christmas Island
CY: Cyprus
CZ: Czechia
DE: Germany
DJ: Djibouti
DK: Denmark
DM: Dominica
DO: Dominican Republic
DZ: Algeria
EC: Ecuador
EE: Estonia
EG: Egypt
EH: Western Sahara
ER: Eritrea
ES: Spain
ET: Ethiopia
FI: Finland
FJ: Fiji
FK: Falkland Islands (Malvinas)
FM: Micronesia Federated States of
FO: Faroe Islands
FR: France
GA: Gabon
GB: United Kingdom
GD: Grenada
GE: Georgia
GF: French Guiana
GG: Guernsey
GH: Ghana
GI: Gibraltar
GL: Greenland
GM: Gambia
GN: Guinea
GP: Guadeloupe
GQ: Equatorial Guinea
GR: Greece
GS: South Georgia and the South Sandwich Islands
GT: Guatemala
GU: Guam
GW: Guinea-Bissau
GY: Guyana
HK: Hong Kong
HM: Heard Island and McDonald Islands
HN: Honduras
HR: Croatia
HT: Haiti
HU: Hungary
ID: Indonesia
IE: Ireland
IL: Israel
IM: Isle of Man
IN: India
IO: British Indian Ocean Territory
IQ: Iraq
IR: Iran Islamic Republic of
IS: Iceland
IT: Italy
JE: Jersey
JM: Jamaica
JO: Jordan
JP: Japan
KE: Kenya
KG: Kyrgyzstan
KH: Cambodia
KI: Kiribati
KM: Comoros
KN: Saint Kitts and Nevis
KP: Korea Democratic People's Republic of
KR: Korea Republic of
KW: Kuwait
KY: Cayman Islands
KZ: Kazakhstan
LA: Lao People's Democratic Republic
LB: Lebanon
LC: Saint Lucia
LI: Liechtenstein
LK: Sri Lanka
LR: Liberia
LS: Lesotho
LT: Lithuania
LU: Luxembourg
LV: Latvia
LY: Libya
MA: Morocco
MC: Monaco
MD: Moldova Republic of
ME: Montenegro
MF: Saint Martin (French part)
MG: Madagascar
MH: Marshall Islands
MK: North Macedonia
ML: Mali
MM: Myanmar
MN: Mongolia
MO: Macao
MP: Northern Mariana Islands
MQ: Martinique
MR: Mauritania
MS: Montserrat
MT: Malta
MU: Mauritius
MV: Maldives
MW: Malawi
MX: Mexico
MY: Malaysia
MZ: Mozambique
NA: Namibia
NC: New Caledonia
NE: Niger
NF: Norfolk Island
NG: Nigeria
NI: Nicaragua
NL: Netherlands
NO: Norway
NP: Nepal
NR: Nauru
NU: Niue
NZ: New Zealand
OM: Oman
PA: Panama
PE: Peru
PF: French Polynesia
PG: Papua New Guinea
PH: Philippines
PK: Pakistan
PL: Poland
PM: Saint Pierre and Miquelon
PN: Pitcairn
PR: Puerto Rico
PS: Palestine State of
PT: Portugal
PW: Palau
PY: Paraguay
QA: Qatar
RE: Réunion
RO: Romania
RS: Serbia
RU: Russian Federation
RW: Rwanda
SA: Saudi Arabia
SB: Solomon Islands
SC: Seychelles
SD: Sudan
SE: Sweden
SG: Singapore
SH: Saint Helena Ascension and Tristan da Cunha
SI: Slovenia
SJ: Svalbard and Jan Mayen
SK: Slovakia
SL: Sierra Leone
SM: San Marino
SN: Senegal
SO: Somalia
SR: Suriname
SS: South Sudan
ST: Sao Tome and Principe
SV: El Salvador
SX: Sint Maarten (Dutch part)
SY: Syrian Arab Republic
SZ: Eswatini
TC: Turks and Caicos Islands
TD: Chad
TF: French Southern Territories
TG: Togo
TH: Thailand
TJ: Tajikistan
TK: Tokelau
TL: Timor-Leste
TM: Turkmenistan
TN: Tunisia
TO: Tonga
TR: Turkey
TT: Trinidad and Tobago
TV: Tuvalu
TW: Taiwan Province of China
TZ: Tanzania United Republic of
UA: Ukraine
UG: Uganda
UM: United States Minor Outlying Islands
US: United States
UY: Uruguay
UZ: Uzbekistan
VA: Holy See (Vatican City State)
VC: Saint Vincent and the Grenadines
VE: Venezuela Bolivarian Republic of
VG: Virgin Islands British
VI: Virgin Islands U.S.
VN: Viet Nam
VU: Vanuatu
WF: Wallis and Futuna
WS: Samoa
YE: Yemen
YT: Mayotte
ZA: South Africa
ZM: Zambia
ZW: Zimbabwe
```