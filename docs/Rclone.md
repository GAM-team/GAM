# Rclone

GAM7 has the capability to upload and download single files between your local computer and Google Drive;
it has no capability for uploading and dowloading folders. For this you can use Rclone: https://rclone.org/

## Authorization
Rclone uses client and service account access to perform its operations; you can use your existing GAM7
authorization for Rclone, you don't need to create a new project or service account within your project.

You can use your Client ID and Client Secret from `client_secrets.json` and you can use your `oauth2service.json` file with rclone.
```
Google Application Client Id
client_id>

Google Application Client Secret
client_secret>

Scope that rclone should use when requesting access from drive.
Choose a number from below, or type in your own value
 1 / Full access all files, excluding Application Data Folder.
   \ "drive"
 2 / Read-only access to file metadata and file contents.
   \ "drive.readonly"
   / Access to files created by rclone only.
 3 | These are visible in the drive website.
   | File authorization is revoked when the user deauthorizes the app.
   \ "drive.file"
   / Allows read and write access to the Application Data folder.
 4 | This is not visible in the drive website.
   \ "drive.appfolder"
   / Allows read-only access to file metadata but
 5 | does not allow any access to read or download file content.
   \ "drive.metadata.readonly"
scope> 1

Service Account Credentials JSON file path
service_account_file>

