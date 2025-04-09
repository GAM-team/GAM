# Users - Profile Photo
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Download a user's Profile photo](#download-a-users-profile-photo)

## API documentation
* [People API](https://developers.google.com/people/api/rest/v1/people/get)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

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
