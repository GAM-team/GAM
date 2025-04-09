# Cloud Storage
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Download a Cloud Storage Bucket Object](#download-a-cloud-storage-bucket-object)

## API documentation
* [Cloud Storage API - Objects](https://cloud.google.com/storage/docs/json_api/v1/objects)

## Notes
To use these commands you must add the 'Cloud Storage API' to your project and update your client access authorization.
Enable `Cloud Storage API (Read, Vault/Takeout Download)`.
```
gam update project
gam oauth create
```

## Definitions
```
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>
```
## Download a Cloud Storage Bucket Object
```
gam download storagefile <StorageBucketObjectName>
        [targetfolder <FilePath>] [overwrite [<Boolean>]] [nogcspath [<Boolean>]]
```
By default, the takeout files will be downloaded to the directory specified by `drive_dir` in gam.cfg.
* `targetfolder <FilePath>` - The takeout files will be downloaded to `<FilePath>`

By default, when getting a document, an existing local file will not be overwritten; a numeric prefix is added to the filename.
* `overwrite false` - Do not overwite an existing file; add a numeric prefix and create a new file
* `overwrite | overwrite true` - Overwite an existing file

By default, when getting a document, its Google Cloud Storage path is preserved.
* `nogcspath false` - Preserve the Google Cloud Storage path
* `nogcspath | nogcspath true` - Do not preserve the Google Cloud Storage path

### Example
This example downloads a Google Cloud Storage file preserving its path
```
$ gam download storagefile gs://gam-bucket/SubFolder/SimpleText.txt
Getting File SubFolder/SimpleText.txt
Cloud Storage File: SubFolder/SimpleText.txt, Downloaded to: /Users/admin/Documents/GamWork/SubFolder/SimpleText.txt
```
This example downloads a Google Cloud Storage file removing its path
```
$ gam download storagefile gs://gam-bucket/SubFolder/SimpleText.txt nogcspath
Getting File SubFolder/SimpleText.txt
Cloud Storage File: SubFolder/SimpleText.txt, Downloaded to: /Users/admin/Documents/GamWork/SimpleText.txt

```
