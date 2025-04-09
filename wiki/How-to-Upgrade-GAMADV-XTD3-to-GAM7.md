# Installation - Upgrade GAMADV-XTD3 to GAM7

- [Downloads-Installs](Downloads-Installs)
- [Linux and MacOS and Google Cloud Shell](#linux-and-mac-os-and-google-cloud-shell)
- [Windows](#windows)

* GAM7 uses the same code base as GAMADV-XTD3
* It is packaged differently which makes it start much faster on MacOS
* It is signed on MacOS and Windows
* It uses the same gam.cfg
* It uses your existing project

## Linux and MacOS and Google Cloud Shell

This example assumes that GAMADV-XTD3 was installed in `/Users/admin/bin/gamadv-xtd3`.
If GAMADV-XTD3 was installed in another directory, substitute that value in the directions,
e.g., `/home/administrator/bin/gamadv-xtd3`.

See: [Downloads-Installs](Downloads-Installs)

### Update to latest version, use current path `~/bin/gamadv-xtd3`.
You don't have to update any aliases or scripts.

Start a terminal session and execute the following command:
*  `bash <(curl -s -S -L https://git.io/gam-install) -l -d ~/bin/gamadv-xtd3 -s -p false`

Your update is complete.

### Update to latest version, use new path `~/bin/gam7`.

Start a terminal session and execute the following command:
* `bash <(curl -s -S -L https://git.io/gam-install) -l`

### Update gam alias
You should set an alias to point to `/Users/admin/bin/gam7/gam` so you can operate from the `/Users/admin/GAMWork directory`.
Aliases aren't available in scripts, so you may want to set a symlink instead, see below.

Change the following line:
```
alias gam="/Users/admin/bin/gamadv-xtd3/gam"
```
to
```
alias gam="/Users/admin/bin/gam7/gam"
```
in one of these files based on your shell:
```
~/.bash_aliases
~/.bash_profile
~/.bashrc
~/.zshrc
~/.profile
```

Issue the following command replacing `<Filename>` with the name of the file you edited:
```
source <Filename>
```

### Set a symlink if desired
Set a symlink in `/usr/local/bin` (or some other location on $PATH) to point to GAM. 
```
ln -s "/Users/admin/bin/gam7/gam" /usr/local/bin/gam
```

### Test
```
gam version
gam info domain
```

### Update scripts
If you have shell scripts that reference gam like this:
```
gam='/Users/admin/bin/gamadv-xtd3/gam'
```
you should update them:
```
gam='/Users/admin/bin/gam7/gam'
```
If you have so many scripts that this is not feasible, you can do:
```
cd /Users/admin/bin/gamadv-xtd3
mv gam gamxtd3
ln -s /Users/admin/bin/gam7/gam gam
```

### Delete GAMADV-XTD3 install directory
Once you are satisfied that GAM7 is operating correctly, you can delete the GAMADV-XTD3 install directory.
Verify that there are no files in /Users/admin/bin/gamadv-xtd3 other than these:
```
GamCommands.txt
GamUpdate.txt
LICENSE
cacerts.pem
gam
license.rtf
```
If there are, move them to some other directory.
If you did not set a symbolic link in the step above, you can delete the install directory.
```
rm -fr /Users/admin/bin/gamadv-xtd3
```
If you did set a symbolic link in the step above, delete these files but not the directory;
all that should remain is the symbolic link.
```
cd /Users/admin/bin/gamadv-xtd3
rm GamCommands.txt
rm GamUpdate.txt
rm LICENSE
rm cacerts.pem
rm gamxtd3
rm license.rtf
```


## Windows

You can download and install the current GAM7 release from the [GitHub Releases](https://github.com/GAM-team/GAM/releases/latest) page.

This example assumes that GAMADV-XTD3 was installed in C:\GAMADV-XTD3.
If GAMADV-XTD3 was installed in another directory, substitute that value in the directions,
e.g., D:\GAMADV-XTD3.

These steps assume Command Prompt, adjust if you're using PowerShell.

See: [Downloads-Installs-GAM7](Downloads-Installs-GAM7)

### Update to latest version, use current path `C:\GAMADV-XTD3`.
You don't have to update path or scripts.
* Executable Installer, Manual, Windows 64 bit
  - `gam-7.wx.yz-windows-x86_64.msi`
  - Download the installer and run it. When prompted for the Destination Foler, enter `C:\GAMADV-XTD3`.
* Executable Archive, Manual, Windows 64 bit
  - `gam-7.wx.yz-windows-x86_64.zip`
  - Download the archive, extract the contents into `C:\GAMADV-XTD3`.

Your update is complete.

### Update to latest version, use new path `C:\GAM7`.
* Executable Installer, Manual, Windows 64 bit
  - `gam-7.wx.yz-windows-x86_64.msi`
  - Download the installer and run it.
  - Start a Command Prompt/PowerShell session.
* Executable Archive, Manual, Windows 64 bit
  - `gam-7.wx.yz-windows-x86_64.zip`
  - Download the archive, extract the contents into C:\GAM7.
  - Start a Command Prompt/PowerShell session.

### Update system path
You should set the system path to point to C:\GAM7 so you can operate from the C:\GAMWork directory.
```
Start Control Panel
Click System
Click Advanced system settings
Click Environment Variables...
Click Path under System variables
Click Edit...
If you have an existing entry referencing GAMADV-XTD3:
  Click that entry
  Click Delete
If C:\GAM7 is already on the Path, skip the next three steps
  Click New
  Enter C:\GAM7
  Click OK
Click OK
Click OK
Exit Control Panel
```

At this point, you should restart Command Prompt so that it has the updated path and environment variables.

### Test
```
gam version
gam info domain
```

### Delete GAMADV-XTD3 install folder
Once you are satisfied that GAM7 is operating correctly, you can delete the GAMADV-XTD3 install folder.
Verify that there are no files in C:\GAMADV-XTD3 other than these:
```
cacerts.pem
gam.exe
GamCommands.txt
gam-setup.bat
GamUpdate.txt
LICENSE
```
If there are, move them to some other folder and then delete C:\GAMADV-XTD3.
```
