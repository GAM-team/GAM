!# Users - Photo
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Upload a user's photo from a default file](#upload-a-users-photo-from-a-default-file)
- [Upload a user's photo specifying file name](#upload-a-users-photo-specifying-file-name)
- [Upload a user's photo specifying separate path and file name](#upload-a-users-photo-specifying-separate-path-and-file-name)
- [Upload a user's photo specifying a Google Drive owner and file name](#upload-a-users-photo-specifying-a-google-drive-owner-and-file-name)
- [Download a user's photo](#download-a-users-photo)
- [Delete a user's photo](#delete-a-users-photo)
- [Download a user's Profile photo](#download-a-users-profile-photo)

## API documentation
* https://developers.google.com/admin-sdk/directory/reference/rest/v1/users.photos
* https://developers.google.com/people/api/rest/v1/people

## Definitions
* [`<DriveFileEntity>`](Drive-File-Selection)
* [`<UserTypeEntity>`](Collections-of-Users)

## Upload a user's photo from a default file
```
gam <UserTypeEntity> update photo
```
* The default file is named `#email#.#ext#` in the current working directory.
    * `#email#` will be replaced by the user's full email address

## Upload a user's photo specifying file name
```
gam <UserTypeEntity> update photo <FileNamePattern>
```
By default, the user's photo will be uploaded from the current working directory.
* `<FileNamePattern>` can be a full file path/name or just a file name
    * `#email#` and `#user#` will be replaced by the user's full email address
    * `#username#` will be replaced by the local part of the user's email address

## Upload a user's photo specifying separate path and file name
```
gam <UserTypeEntity> update photo
        [drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]
```
By default, the user's photo will be uploaded from the current working directory.
* `drivedir` - The photo will be uploaded from the directory specified by `drive_dir` in gam.cfg
* `sourcefolder <FilePath>` - The photo will be uploaded from `<FilePath>`

* `filename <FileNamePattern>` - A file name
    * `#email#` and `#user#` will be replaced by the user's full email address
    * `#username#` will be replaced by the local part of the user's email address

## Upload a user's photo specifying a Google Drive owner and file name
```
gam <UserTypeEntity> update photo
        gphoto <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>
```
* `<DriveFileIDEntity>` - A file ID
* `<DriveFileNameEntity>` - A file name
    * `#email#` and `#user#` will be replaced by the user's full email address
    * `#username#` will be replaced by the local part of the user's email address

## Download a user's photo
```
gam <UserTypeEntity> get photo
        [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
        [noshow] [nofile]
```
By default, the user's photo will be downloaded into the current working directory.
* `drivedir` - The photo will be downloaded to the directory specified by `drive_dir` in gam.cfg
* `targetfolder <FilePath>` - The photo will be downloaded to `<FilePath>`
* `nofile` - Suppress writing the photo data to a file

By default, the user's photo will be named `#email#.#ext#`; use the following option to specify a different file name.
  * `filename <FileNamePattern>` - The downloaded file name will be `<FileNamePattern>`

In either case, the following substitutions will be made:
  * `#email#` and `#user#` will be replaced by the user's full email address
  * `#username#` will be replaced by the local part of the user's email address
  * `#ext#` will be replaced by the appropriate extension based on the data: `jpg`, `png`, `gif`

By default, the Base64 encoded data is dumped to stdout.
* `noshow` - Suppress dumping the photo data to stdout

## Delete a user's photo
```
gam <UserTypeEntity> delete|del photo
```
## Download a user's Profile photo
```
gam <UserTypeEntity> get profilephoto
        [drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
        [noshow] [nofile] [returnurlonly] [nodefault] [size <Integer>]
```
By default, the user's photo will be downloaded into the current working directory.
* `drivedir` - The photo will be downloaded to the directory specified by `drive_dir` in gam.cfg
* `targetfolder <FilePath>` - The photo will be downloaded to `<FilePath>`
* `nofile` - Suppress writing the photo data to a file

By default, the user's photo will be named `#email#.#ext#`; use the following option to specify a different file name.
  * `filename <FileNamePattern>` - The downloaded file name will be `<FileNamePattern>`

In either case, the following substitutions will be made:
  * `#email#` and `#user#` will be replaced by the user's full email address
  * `#username#` will be replaced by the local part of the user's email address
  * `#ext#` will be replaced by the appropriate extension based on the data: `jpg`, `png`, `gif`

By default, the Base64 encoded data is dumped to stdout.
* `noshow` - Suppress dumping the photo data to stdout

Use the `returnurlonly` option to get the URL of the profile photo but not the photo itself.

If `nodefault` is specified and the user has a default profile photo, GAM will display an
error message and set the return code to 50.

Use `size <Integer>` to specify the size in pixels of the file to download.
