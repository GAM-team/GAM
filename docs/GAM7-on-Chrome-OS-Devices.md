# GAM7 on Chrome OS Devices
Chrome OS devices that [support Linux apps](https://support.google.com/chromebook/answer/9145439?hl=en) can run GAM7. This includes Intel/AMD x86_64 Chromebooks as well as ARM-based Chromebooks with Mediatek or Rockchip 64-bit CPUs.

1. [Set up Linux on your Chromebook](https://support.google.com/chromebook/answer/9145439?hl=en).
1. From the Terminal app, run the following commands:
```
    sudo apt update
    sudo apt install xz-utils
```
3. [How to Install Advanced GAM](How-to-Install-Advanced-GAM)

# Google cloud shell

Note that from a Chrome OS device, it might be just as easy to use [Google Cloud Shell](https://cloud.google.com/shell). Especially if you are concerned about network connectivity and/or bandwidth, using a shell instance within Google's server infrastructure is always going to be less resource intensive than sending data back and forth between a Google API and your local machine on your local network.
