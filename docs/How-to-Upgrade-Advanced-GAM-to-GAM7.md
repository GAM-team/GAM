# Installation - Update Advanced GAM to GAM7

- [Downloads-Installs-GAM7](Downloads-Installs-GAM7)
- [Linux and MacOS and Google Cloud Shell](#linux-and-mac-os-and-google-cloud-shell)
- [Windows](#windows)

## Linux and MacOS and Google Cloud Shell

This example assumes that GAMADV-XTD3 was installed in /Users/admin/bin/gamadv-xtd3.
If GAMADV-XTD3 was installed in another directory, substitute that value in the directions.

Rename install directory.
```
mv /Users/admin/bin/gamadv-xtd3 /Users/admin/bin/gam7
```

See: [Downloads-Installs-GAM7](Downloads-Installs-GAM7)

You can download and install the current GAM7 release from the [GitHub Releases](https://github.com/GAM-team/GAM/releases/latest) page. Choose one of the following:

* Executable Archive, Automatic, Linux/Mac OS/Google Cloud Shell/Raspberry Pi/ChromeOS
  - Start a terminal session and execute one of the following commands:
  - Update to latest version, do not create project or authorizations, default path `$HOME/bin`
    - `bash <(curl -s -S -L https://git.io/gam-install) -l`
  - Update to latest version, do not create project or authorizations, specify a path
    - `bash <(curl -s -S -L https://git.io/gam-install) -l -d <Path>`

In these examples, the user home folder is shown as /Users/admin; adjust according to your
specific situation; e.g., /home/administrator.

### Update gam  alias
You should set an alias to point to /Users/admin/bin/gam/gam so you can operate from the /Users/admin/GAMWork directory.
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
```

## Windows

You can download and install the current GAM7 release from the [GitHub Releases](https://github.com/GAM-team/GAM/releases/latest) page.

This example assumes that GAMADV-XTD3 was installed in C:\GAMADV-XTD3.
If GAMADV-XTD3 was installed in another directory, substitute that value in the directions.

These steps assume Command Prompt, adjust if you're using PowerShell.

Rename install directory.
```
ren C:\GAMADV-STD3 C:\GAM7
```

See: [Downloads-Installs-GAM7](Downloads-Installs-GAM7)

* Executable Archive, Manual, Windows 64 bit
  - `gam-7.wx.yz-windows-x86_64.zip`
  - Download the archive, extract the contents into C:\GAM7.
  - Start a Command Prompt/PowerShell session.

* Executable Installer, Manual, Windows 64 bit
  - `gam-7.wx.yz-windows-x86_64.msi`
  - Download the installer and run it.
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
```
