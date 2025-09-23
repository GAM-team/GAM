# GAM Drive Command Reference

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

## gam \<who\> show filelist
* [todrive]
* [query \<query\>]
* [allfields]
* [createddate]
* [description]
* [fileextension]
* [filesize]
* [id]
* [restricted]
* [starred]
* [trashed]
* [viewed]
* [lastmodifyingusername]
* [lastviewedbymedate]
* [modifieddate]
* [originalfilename]
* [quotaused]
* [shared]
* [writerscanshare]

## gam \<who\> show driveactivity
* [todrive]
* [fileid \<id\>]
* [folderid \<id\>]

## gam \<who\> show drivesettings [todrive]

## gam \<who\> show fileinfo \<id\>|
* [allfields|\<DriveFieldName\>*]

## gam \<who\> show filetree

## gam \<who\> show filerevisions \<id\>

## gam \<who\> add drivefile
* [localfile \<filepath\>]
* [drivefilename \<filename\>]
* [convert]
* [ocr]
* [ocrlanguage \<language\>]
* [restricted]
* [starred]
* [trashed]
* [viewed]
* [lastviewedbyme \<date\>]
* [modifieddate \<date\>]
* [description \<description\>]
* [mimetype \<type\>]
* [parentid \<folder id\>]
* [parentname \<folder name\>]
* [writerscantshare]

## gam \<who\> update drivefile
* [localfile \<filepath\>]
* [newfilename \<filename\>]
* [id \<drive file id\> | drivefilename \<filename\>]
* [convert]
* [ocr]
* [ocrlanguage \<language\>]
* [restricted true|false]
* [starred true|false]
* [trashed true|false]
* [viewed true|false]
* [lastviewedbyme \<date\>]
* [modifieddate \<date\>]
* [description \<description\>]
* [mimetype \<type\>]
* [parentid \<folder id\>]
* [parentname \<folder name\>]
* [writerscantshare]

## gam \<who\> get drivefile [id \<file id\> | query \<query\>]
* [format \<openoffice|microsoft|pdf\>]
* [targetfolder \<local path\>]
* [revision \<number\>]

## gam \<who\> delete emptydrivefolders|
 drivefile \<file id\> [purge]

## gam \<who\> transfer drive \<target user\> [keepuser]

## gam \<who\> empty drivetrash

# ACLs
## gam user \<user email\> show drivefileacl \<file id\> [asadmin]

## gam user \<user email\> add drivefileacl \<file id\>
* [user|group|domain \<value\>|anyone]
* [withlink]
* [role \<reader|commenter|writer|owner\>]
* [sendemail]
* [emailmessage \<message text\>]

## gam user \<user email\>update drivefileacl \<file id\> \<permission id\>
* [withlink]
* [role \<reader|commenter|writer|owner\>]
* [transferownership \<true|false\>]
* [asadmin]

## gam user \<user email\>delete drivefileacl \<file id\> \<permission id\> [asadmin]

# Team Drive

## gam user \<email\>

## gam user \<email\> print|show teamdrives
 [todrive] [asadmin]
 