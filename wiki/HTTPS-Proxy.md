# HTTPS Proxy

GAM should be run on a server with direct access to talk to Google servers via the Internet.
However, if you must push GAM traffic through an HTTPS proxy this can be done by setting the HTTPS_PROXY environment variable.

## Linux and MacOS and Google Cloud Shell

Add the following line (use the actual proxy IP address and port number):
```
export HTTPS_PROXY="http://192.168.1.1:3128"
```
to one of these files based on your shell:
```
~/.bash_profile
~/.bashrc
~/.zshrc
~/.profile
```
## Windows

Set a system environment variable (use the actual proxy IP address and port number):
```
Start Control Panel
Click System
Click Advanced system settings
Click Environment Variables...
Set Variable name: HTTPS_PROXY
Set Variable value: http://192.168.1.1:3128
Click OK
Click OK
Click OK
Exit Control Panel
```
