- [Printing browsers](#printing-browsers)
- [Moving browsers](#moving-browsers)
- [Updating browsers](#updating-browsers)
- [Get info about a browser](#get-info-about-a-browser)
- [Delete a browser](#delete-a-browser)

GAM 5.30 adds support for the new [Chrome Browser Cloud Management API calls](https://support.google.com/chrome/a/answer/9681204). The API allows you to print, move, update and delete enrolled browsers.

# Printing browsers
## Syntax
```
gam print browsers [query <query>] [projection BASIC|FULL] [todrive] [sort_headers] [fields <fields>]
```
Prints enrolled browsers. The optional argument query will limit results to matching browsers. Query format is described [in Google's help articles](https://support.google.com/chrome/a/answer/9681204#example:~:text=You%20can%20specify%20the%20following%20fields,the%20field%20names%20are%20case%20sensitive). By default, GAM only prints basic information about the browsers. The optional argument projection allows selecting FULL which prints a lot more information about each browser including user profiles, policies and extension details. The optional argument todrive will upload the output to a Google Sheet. The optional argument fields specifies a comma separated list of fields you'd like to limit results to.

## Example
This example prints all browsers.
```
gam print browsers
```
This example creates a Google Sheet of browsers running on Microsoft Windows
```
gam print browsers todrive query "os_platform:Windows"
```
----
## Moving browsers
### Syntax
```
gam move browsers [ids <ids>] [query <query>] [file <file>] [csvfile <csvfile:columnName>] [orgunit <orgunit>] [batch_size <number>]
```
Moves the specified browsers from one OrgUnit in Google to another. The browsers must be specified with the ids, query, file or csvfile argument. The orgunit argument specifies the destination of the browsers. By default, GAM will attempt to move 600 browsers at a time which is the max allowed by the API. You can modify this number by specifying batch_size.

### Example
This example moves all Windows browsers into their own Org Unit.
```
gam move browsers query "os_platform:Windows" orgunit /Chrome/Windows
```
----
## Updating browsers
### Syntax
```
gam update browser <id> [user <user>] [location <location>] [notes <notes>] [assetid <assetid>]
```
Updates information about a Chrome browser. Information can be set for the user, location, notes and assetid fields.

### Example
This example updates all four fields
```
gam update browser c052d4d7-90b1-407a-911f-c0d05ba0eaeb user jsmith@acme.com location "New York, NY" notes "Browser re-installed on 12/3/20" assetid ABC123
```
----
## Get info about a browser
### Syntax
```
gam info browser <id> [FULL|BASIC] [fields <fields>]
```
shows information about a single browser based on the id specified. The optional argument projection retrieves a basic or full list of device attributes. Full includes details like browser profiles, policies and extensions. The optional fields parameter limits which fields are retrieved and printed.

### Example
This example gets info about a browser
```
gam info browser c052d4d7-90b1-407a-911f-c0d05ba0eaeb
```
This example shows a LOT of information about the browser
```
gam info browser c052d4d7-90b1-407a-911f-c0d05ba0eaeb projection FULL
```
This example shows a limited amount of information
```
gam info browser c7cf1d21-50af-4419-bf75-67731423a259 fields osPlatform,lastPolicyFetchTime,osPlatformVersion,lastDeviceUser,orgUnitPath
```
----
## Delete a browser
### Syntax
```
gam delete browser <id>
```
Deletes the given browser by id. The browser will be removed from Google's admin console and no longer sync policy or reporting. However existing policies will still be applied until the device registration and dm tokens are removed.

### Example
This example deletes the device.
```
gam delete browser c7cf1d21-50af-4419-bf75-67731423a259
```
----
