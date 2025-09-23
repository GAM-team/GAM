- [Request a Data Transfer](#request-a-data-transfer)
- [Get Information About a Data Transfer](#get-information-about-a-data-transfer)
- [Print All Data Transfers](#print-all-data-transfers)
- [Print Information About Apps That Support Data Transfer](#print-information-about-apps-that-support-data-transfer)

# Request a Data Transfer
## Syntax
```
gam create datatransfer <old owner> <app> <new owner> (<parameter> <value>)*
```
Creates a data transfer request. Old owner is the source user whose data will be transferred. App is the name of the application data to transfer. New owner is the target user that will receive the data. Depending on the app, optional parameters can be specified which determine the scope of data to be transferred.

## Example
This example transfers all Drive files for oldguy@acme.com to newguy@acme.com
```
gam create datatransfer oldguy@acme.com gdrive newguy@acme.com privacy_level shared,private
```
This example transfers only Drive files shared by terminated@acme.com to manager@acme.com
```
gam create datatransfer terminated@acme.com gdrive manager@acme.com privacy_level shared
```
This example transfers Calendar entries from oldguy to newguy and releases calendar resources booked by oldguy.
```
gam create datatransfer oldguy@acme.com calendar newguy@acme.com release_resources true
```
---

# Get Information About a Data Transfer
## Syntax
```
gam info datatransfer <id>
```
Get information about an existing data transfer including the status.

## Example
This example shows the status of a given data transfer.
```

gam info datatransfer AKrEtIYIysvNvudwY69gEtJNb85tK87Py2SJl8uwq78BxSMMRgn46rWtuKPIxmkWehZ_YJguKbSs
Old Owner: sarah@acme.com
New Owner: announce@acme.com
Request Time: 2015-09-29T20:45:28.085Z
Application: Drive
Status: completed
Parameters:
 PRIVACY_LEVEL: PRIVATE,SHARED
```
---
# Print All Data Transfers
## Syntax
```
gam print datatransfers [oldowner <email>] [newowner <email>] [status <completed|failed|inProgress>] [todrive]
```
Prints a CSV of all data transfers. With no parameters, all transfers will be printed. The oldowner, newowner and status parameters limit the output to results which match. The todrive parameter causes GAM to generate a Google Spreadsheet of the results rather than outputting the CSV file to the console.

## Example
This example prints all transfers
```
gam print datatransfers
```
This example prints all transfers that have failed to a Google Spreadsheet.
```
gam print datatransfers status failed todrive
```
---

# Print Information About Apps That Support Data Transfer
## Syntax
```
gam print transferapps
```

Prints information about all apps which support data transfer.

---