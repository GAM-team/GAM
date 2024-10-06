!All Google Drive API calls have been converted from v2 to v3, see: https://developers.google.com/drive/v3/web/migration
Many of the changes are internal to Gam and have no visible effect. Google has modified/renamed many field names and these will affect scripts that parse the output from `gam print/show drivesettings/drivefileacls/fileinfo/filelist/filerevisions`. Additionally, Google has dropped some fields and their values are no longer available. On input, Gam accepts both the old and new field names.

A variable, `drive_v3_native_names` (default value is True), has been added to `gam.cfg` to control the field names on output: when True, the v3 native field names are used; when False, the v3 native field names are mapped to the v2 field names.

If you have scripts that process the output from these print commands, you may have to make modifications to your scripts.
Run your print/show commands with a version of Legacy Gam and save the output.
With drive_v3_native_names = False, run your print/show commands with this version of Gam and compare the output to that saved in the previous run;
modify your scripts that process the output as appropriate.

There is a cost to mapping the v3 field names back to the v2 field names; you can avoid this cost by setting drive_v3_native_names = True,
running your print/show commands, comparing the output and making the appropriate script modifications.
```
print/show drivesettings
Dropped fields:
        DRIVE
        GMAIL
        PHOTOS
        domainSharingPolicy
        lauguageCode
Renamed fields (Old->New):
        name->displayName,
        quotaBytesTotal->limit
        quotaBytesUsed->usageInDrive
        quotaBytesUsedAggregate->usage
        quotaBytesUsedInTrash->usageInDriveTrash

print/show drivefileacls
Dropped fields:
        authKey
Renamed fields (Old->New):
        name->displayName
        withLink->allowFileDiscovery

print/show fileinfo/filelist
Dropped fields:
        defaultOpenWithLink
        embedLink
        exportLinks
        labels(hidden)
        markedViewedByMeDate
        openWithLinks
        selfLink
        parents(isRoot)
        parents(parentLink)
        parents(selfLink)
        permissions(selfLink)
        selfLink
        userPermission(selfLink)
Renamed fields (Old->New):
        alternateLink->webViewLink
        capabilities(canChangeRestrictedDownload)->capabilities(canChangeViewersCanCopyContent)
        createdDate->createdTime
        expirationDate->expirationTime
        fileSize->size
        lastViewedByMeDate->viewedByMeTime
        modified->modifiedByMe
        modifiedByMeDate->modifiedByMeTime
        modifiedDate->modifiedTime
        restricted->viewersCanCopyContent
        sharedWithMeDate->sharedWithMeTime
        title->name
        trashedDate->trashedTime
        viewed->viewedByMe
        withLink->allowFileDiscovery

print/show filerevisions
Dropped fields:
        exportLinks
        publishedLink
        selfLink
Renamed fields (Old->New):
        fileSize->size
        isAuthenticatedUser->me
        modifiedDate->modifiedTie
        picture.url->photoLink
        pinned->keepForever
```
The parents field of a file has undergone the most change. In Drive v2 it was a list of compound items with three sub-fields per item: id, isRoot, parentLink.
In Drive v3 the parents field is a list of simple items, the parent ids. The following examples show how the parents field is output in a CSV file for a file with two parents.
```
Previous versions of Gam:
Owner,title,parents,parents.0.isRoot,parents.0.id,parents.0.parentLink,parents.1.isRoot,parents.1.id,parents.1.parentLink
testuser@domain.com,TestFile,2,True,PPPP1111,https://www.googleapis.com/drive/v2/files/PPPP1111,False,PPPP2222,https://www.googleapis.com/drive/v2/files/PPPP2222

Current version of Gam with drive_v3_name_names = false
Owner,title,parents,parents.0.id,parents.1.id
testuser@domain.com,TestFile,2,PPPP1111,PPPP2222

Current version of Gam with drive_v3_name_names = true
Owner,name,parents
testuser@domain.com,TestFile,PPPP1111 PPPP2222
```
