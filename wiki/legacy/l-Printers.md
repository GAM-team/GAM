- [Listing Printer Models](#listing-printer-models)
- [Printing Printers](#printing-printers)
- [Creating a Printer](#creating-a-printer)
- [Updating a Printer](#updating-a-printer)
- [Displaying Info About a Printer](#displaying-info-about-a-printer)
- [Deleting a Printer](#deleting-a-printer)

## Listing Printer Models
### Syntax
```
gam print printermodels [filter <filter>] todrive
```
Outputs a CSV list of the printer model drivers available for Chrome printers. The optional filter argument limits output to printers that match. The optional todrive argument creates a Google Sheet of the printer models rather than outputing CSV.

### Example
This example prints available models.
```
gam print printermodels
manufacturer,displayName,makeAndModel
...
Apple,Apple 12/640ps,apple 12/640ps
Apple,Apple Color StyleWriter 1500,apple color stylewriter 1500
Apple,Apple Color StyleWriter 2200,apple color stylewriter 2200
Apple,Apple Color StyleWriter 2400,apple color stylewriter 2400
Apple,Apple Color StyleWriter 2500,apple color stylewriter 2500
Apple,Apple ImageWriter,apple imagewriter
Apple,Apple ImageWriter II,apple imagewriter ii
Apple,Apple ImageWriter LQ,apple imagewriter lq
Apple,Apple LaserWriter 16/600,apple laserwriter 16/600
Apple,Apple LaserWriter 4/600,apple laserwriter 4/600
Apple,Apple LaserWriter IIg,apple laserwriter iig
Apple,Apple LaserWriter Pro 630,apple laserwriter pro 630
...
```
----

## Printing Printers
### Syntax
```
gam print printers [filter <filter>] [todrive]
```
Prints a CSV list of the printers configured in your organization. The optional argument filter limits the output to matching printers. The optional argument todrive creates a Google Sheet of the results rather than outputting it to the console or a file.

### Example
This example prints your printers.
```
gam print printers
name,id,displayName,makeAndModel,uri,createTime,orgUnitId,orgUnitPath
customers/C01wfv983/chrome/printers/0gjdgxs3dgp3kj,0gjdgxs3dgp3kj,Brother MFC-L3770CDW,brother mfc-l3770cdw series,ipp://192.168.86.3:631/ipp/print,2019-12-10T17:40:18.930Z,03w261t745aficu,/
...
```
----

## Creating a Printer
### Syntax
```
gam create printer displayname <name> description <description> [makeandmodel <makeandmodel>] [driverless] [orgunit <orgunit>] [uri <uri>]
```
Creates a new printer. Displayname and description are visible to the user. You must either specify a makeandmodel which matches a makeandmodel from the [listing printer models[#listing-printer-models] output or driverless which tells Chrome OS to attempt to detect the device type and features using standard protocols (this may be a good option if you can't find an exact makemodel match). orgunit specifies the location of the printer in the Google console. uri specifies the protocol and address of the printer.

### Example
This example would allow you to print to my home printer if you were in my home.
```
gam create printer displayname "Jay's Printer" description "Upstairs" makeandmodel "Brother MFC-L3770CDW" orgunit / uri ipp://192.168.86.3:631/ipp/print
```
----

## Updating a Printer
### Syntax
```
gam update printer <id> displayname <name> description <description> [makeandmodel <makeandmodel>] [driverless] [orgunit <orgunit>] [uri <uri>]
```
Updates a printer's configuration. The arguments are identical to the create command. You can update a printers uri if it's address or protocol should be changed and you can change to a different printer makeandmodel or to driverless as preferred.

### Example
This example switches my home printer to using driverless.
```
gam update printer 0gjdgxs3dgp3kj driverless
```
----

## Displaying Info About a Printer
### Syntax
```
gam info printer <id>
```
Shows information about the specified printer.

### Example
This example shows information about my printer
```
gam info printer 0gjdgxs3dgp3kj
 name: customers/C01wfv983/chrome/printers/0gjdgxs3dgp3kj
 id: 0gjdgxs3dgp3kj
 displayName: Brother MFC-L3770CDW
 makeAndModel: brother mfc-l3770cdw series
 uri: ipp://192.168.86.3:631/ipp/print
 createTime: 2019-12-10T17:40:18.930Z
 orgUnitId: 03w261t745aficu
 orgUnitPath: /
```
----

## Deleting a Printer
### Syntax
```
gam delete printer id1,id2 | file <filename> | csvfile <filename:column>
```
Deletes one or more printers.

### Example
This example delete's my printer.
```
gam delete printer 0gjdgxs3dgp3kj
```