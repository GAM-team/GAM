Legacy GAM used Drive API v2, GAM7 uses  Drive API v3. See: https://developers.google.com/drive/v3/web/migration
Many of the changes are internal to GAM7 and have no visible effect.
Google has modified/renamed many field names and these will affect scripts that parse the output from `gam print/show drivesettings/drivefileacls/fileinfo/filelist/filerevisions`.
Additionally, Google has dropped some fields and their values are no longer available. On input, GAM7 accepts both the old and new field names where applicable.

If you use Legacy GAM and have scripts that process the output from these print commands, you may have to make modifications to your scripts when you upgrade to GAM7.
Run your print/show commands with a version of Legacy GAM and save the output.
Run your print/show commands with GAM7 and compare the output to that saved in the previous run;
modify your scripts that process the output as appropriate.

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
        withLink->allowFileDiscovery - value is complemented

print/show fileinfo/filelist
Dropped fields:
        defaultOpenWithLink
        embedLink
        exportLinks
        labels(hidden)
        markedViewedByMeDate
        openWithLinks
        ownerNames
        parents(isRoot)
        parents(parentLink)
        parents(selfLink)
        permissions(selfLink)
        selfLink
        userPermission
Renamed fields (Old->New):
        alternateLink->webViewLink
        capabilities(canChangeRestrictedDownload)->capabilities(canChangeViewersCanCopyContent)
        createdDate->createdTime
        expirationDate->expirationTime
        fileSize->size
        lastModifyingUserName->lastModifyingUser(displayName)
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
