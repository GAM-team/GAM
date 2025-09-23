- [Printing devices](#printing-devices)
- [Sync devices with a CSV file](#sync-devices-with-a-csv-file)
- [Get information about a device](#get-information-about-a-device)
- [Create a corporate device](#create-a-corporate-device)
- [Action a device (delete, wipe or cancel wipe)](#action-a-device-delete-wipe-or-cancel-wipe)
- [Action a device user (delete, wipe, cancel wipe, approve or block)](#action-a-device-user-delete-wipe-cancel-wipe-approve-or-block)

GAM 5.20 adds support for the new [Cloud Identity Devices API calls](https://cloud.google.com/identity/docs/reference/rest/v1/devices). The new API allows management of mobile and desktop devices and also allows managing your [company-owned device inventory](https://support.google.com/a/answer/9090870?hl=en).

# Printing devices
## Syntax
```
gam print devices [filter <filter>] [no_company_devices] [no_personal_devices]
    [no_users] [to_drive] [sort_headers]
```
Prints CSV output of devices registered in your domain. The optional filter parameter limits which devices are returned based on [Google's filter syntax](https://support.google.com/a/answer/7549103). By default, both company-owned and personal/BYOD devices are retrieved. The optional arguments no_company_devices and no_personal_devices reduce which devices are retrieved. By default, information on associated user profiles is also retrieved. The optional argument no_users disables user profile retrieval. The optional argument to_drive creates a Google Sheet with the CSV data rather than outputing it to the screen. The optional argument sort_headers will sort the output columns alphabetically by header.

## Example
This example prints all devices in the domain.
```
gam print devices
```
This example prints only company-owned devices
```
gam print devices no_personal_devices
```
---

# Sync devices with a CSV file
## Syntax
```
gam sync devices [filter <filter>] [csv_file <csv file>] [serial_number_column <column>]
    [device_type_column <column>] [asset_id_column <column>] [static_device_type <type>]
    [unassigned_missing_action <delete|wipe|donothing>]
    [assigned_missing_action <delete|wipe|donothing>]
```
Syncs the company-owned inventory of devices with a local CSV file. The optional filter parameter limits which devices are returned based on [Google's filter syntax](https://support.google.com/a/answer/7549103). The filter can be used to only sync the file against one portion of the company-owned inventory such as Windows or Android devices. csv_file is a required argument and specifies the CSV file GAM should read for the sync. By default, GAM looks for columns named serialNumber and deviceType, asset_id is not used. The optional arguments serial_number_column, device_type_column and asset_id_column specify other columns to use if your headers are different. If you know all devices in your CSV are of the same type you can specify static_device_type to use that type for all created devices. By default, GAM will delete any devices that are registered in Google admin company-owned inventory but are not present in (missing from) the CSV file AND have not been assigned to a user yet. Missing devices that are registered to a user will be left alone. The optional arguments unassigned_missing_action and assigned_missing_action specify what action GAM should perform on these devices.

## Example
This example reads devices.csv which has only the header serialNumber and will create any that are in the file but not in Google as well as delete any that are in Google but not the file and are not yet assigned to a user. The filter ensures that GAM is only comparing against Android devices in the Google inventory.
```
gam sync devices csv_file android-devices.csv filter type:android static_device_type android
```
----

# Create a corporate device
## Syntax
```
gam create device [serial_number <serial>] [device_type <type>]
```
Adds a new device to the Google company-owned inventory. Once a user is assigned and enrolled on the device the device will be considered company-owned for management purposes. The device will also register as company-owned with Google services like [Context-Aware Access (CAA)](https://support.google.com/a/answer/9275380?hl=en). Arguments serial_number and device_type are both required and specify the serial and device type respectively. Device type can be one of ANDROID, IOS, GOOGLE_SYNC, WINDOWS, MAC_OS, LINUX or CHROME_OS.

## Example
This example creates an Android phone so it is ready to be user-enrolled as a company-owned device
```
gam create device serial_number abc123 device_type android
```
----

# Action a device (delete, wipe or cancel wipe)
## Syntax
```
gam delete|wipe|cancel_wipe id <device id> [remove_reset_lock]
```
deletes, wipes all device data or cancels a pending wipe respectively. id is a required argument and specifies the name/ID of the device to be acted upon. On wipe, the optional argument `remove_reset_lock` will remove [the account lock on the Android or iOS device](https://support.google.com/android/answer/9459346?hl=en). This lock is enabled by default and requires the existing device user to log in after the wipe in order to unlock the device.

## Example
This example deletes a device so that it will no longer show in the Google admin console. Sync will also break for the user but no user data on device should be removed.
```
gam delete device id devices/CiRkMzk4N2RjYS1hODhmLTQwYTAtOTQ1Zi1mZDMwOTY2MmNjNGY%3D
```
This example wipes a device (factory reset). All data on the device will be lost.
```
gam wipe device id devices/CiRkMzk4N2RjYS1hODhmLTQwYTAtOTQ1Zi1mZDMwOTY2MmNjNGY%3D
```
----

# Action a device user (delete, wipe, cancel wipe, approve or block)
## Syntax
```
gam delete|wipe|cancelwipe|approve|block deviceuser id <device id>
```
deletes, wipes all device data, cancels a pending wipe respectively, approves or blocks a user profile on a device. id is a required argument and specifies the name/ID of the device user profile to be acted upon.

## Example
This example deletes a device user so that it will no longer show in the Google admin console. Sync will also break for the user but no user data on device should be removed.
```
gam delete deviceuser id devices/CiRjY2RiZjk5Yy01Y2EwLTQyMTUtODY4Yi0zZjI5ZGRkODc2M2M%3D/deviceUsers/0af7153a-f661-4baa-a666-e3868340290e
```
This example wipes a device user profile from a device. In the case of Android for Work, the work profile will be removed but the personal profile left alone.
```
gam wipe deviceuser id devices/CiRjY2RiZjk5Yy01Y2EwLTQyMTUtODY4Yi0zZjI5ZGRkODc2M2M%3D/deviceUsers/0af7153a-f661-4baa-a666-e3868340290e
```
----