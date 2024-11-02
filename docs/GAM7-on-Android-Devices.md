# GAM7 on Android Devices
GAM7 now runs on 64-bit Android devices such as Google's Pixel phones. The installation requires an app that adds the Linux environment to Android such as [UserLAnd](https://play.google.com/store/apps/details?id=tech.ula&hl=en_US).

_Note: Chromebooks / Chrome OS devices should install GAM7 using [these instructions](GAM7-on-Chrome-OS-Devices)._

1. Install the [UserLAnd](https://play.google.com/store/apps/details?id=tech.ula&hl=en_US) app.
2. Click Debian to install a Debian environment.
3. Set a username and password.
4. Choose SSH for connection type.
5. Once setup, login with the password to get to a Linux shell.
6. Run the following commands to install prerequisites:
```
    sudo apt update
    sudo apt install curl python3
```
7. [How to Install Advanced GAM](How-to-Install-Advanced-GAM)
