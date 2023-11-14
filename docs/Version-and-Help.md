
# Version and Help

Print the current version of Gam with details
```
gam version
GAMADV-XTD3 6.65.09 - https://github.com/taers232c/GAMADV-XTD3 - pythonsource
Ross Scroggs <ross.scroggs@gmail.com>
Python 3.12.0 64-bit final
MacOS Monterey 12.7 x86_64
Path: /Users/Admin/bin/gamadv-xtd3
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain.com
Time: 2023-06-02T21:10:00-07:00
```

Print the current version of Gam with details and time offset information
```
gam version timeoffset
GAMADV-XTD3 6.65.09 - https://github.com/taers232c/GAMADV-XTD3 - pythonsource
Ross Scroggs <ross.scroggs@gmail.com>
Python 3.12.0 64-bit final
MacOS Monterey 12.7 x86_64
Path: /Users/Admin/bin/gamadv-xtd3
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain.com
Your system time differs from www.googleapis.com by less than 1 second
```

Print the current version of Gam with extended details and SSL information
```
gam version extended
GAMADV-XTD3 6.65.09 - https://github.com/taers232c/GAMADV-XTD3 - pythonsource
Ross Scroggs <ross.scroggs@gmail.com>
Python 3.12.0 64-bit final
MacOS Monterey 12.7 x86_64
Path: /Users/Admin/bin/gamadv-xtd3
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain.com
Time: 2023-06-02T21:10:00-07:00
Your system time differs from admin.googleapis.com by less than 1 second
OpenSSL 3.1.1 30 May 2023
cryptography 41.0.1
filelock 3.12.0
google-api-python-client 2.88.0
google-auth-httplib2 0.1.0
google-auth-oauthlib 1.0.0
google-auth 2.19.1
httplib2 0.22.0
passlib 1.7.4
python-dateutil 2.8.2
yubikey-manager 5.1.1
admin.googleapis.com connects using TLSv1.3 TLS_AES_256_GCM_SHA384
```

Print the current and latest versions of Gam and:
* set the return code to 0 if the current version is the latest version
* set the return code to 1 if the current version is not the latest
```
gam version checkrc
GAM 5.35.08 - https://github.com/taers232c/GAMADV-XTD3
Ross Scroggs <ross.scroggs@gmail.com>
Python 3.8.1 64-bit final
google-api-python-client 2.77.0
httplib2 0.16.0
oauth2client 4.1.3
MacOS High Sierra 10.13.6 x86_64
Path: /Users/Admin/bin/gamadv-xtd3
Version Check:
  Current: 5.35.08
   Latest: 6.65.09
echo $?
1
```

Print the current version number without details
```
gam version simple
6.65.09
```
In Linux/MacOS you can do:
```
VER=`gam version simple`
echo $VER
```
Print the current version of Gam and address of this Wiki
```
gam help
GAM 6.65.09 - https://github.com/taers232c/GAMADV-XTD3
Ross Scroggs <ross.scroggs@gmail.com>
Python 3.12.0 64-bit final
MacOS Monterey 12.7 x86_64
Path: /Users/Admin/bin/gamadv-xtd3
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain.com
Time: 2023-06-02T21:10:00-07:00
Help: Syntax in file /Users/Admin/bin/gamadv-xtd3/GamCommands.txt
Help: Documentation is at https://github.com/taers232c/GAMADV-XTD3/wiki
```
