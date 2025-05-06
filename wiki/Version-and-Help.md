k
# Version and Help

Print the current version of Gam with details
```
gam version
GAM 7.06.14 - https://github.com/GAM-team/GAM - pyinstaller
GAM Team <google-apps-manager@googlegroups.com>
Python 3.13.3 64-bit final
MacOS Sequoia 15.4.1 x86_64
Path: /Users/Admin/bin/gam7
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain: domain.com
Time: 2023-06-02T21:10:00-07:00
```

Print the current version of Gam with details and time offset information
```
gam version timeoffset
GAM 7.06.14 - https://github.com/GAM-team/GAM - pyinstaller
GAM Team <google-apps-manager@googlegroups.com>
Python 3.13.3 64-bit final
MacOS Sequoia 15.4.1 x86_64
Path: /Users/Admin/bin/gam7
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain: domain.com
Your system time differs from www.googleapis.com by less than 1 second
```

Print the current version of Gam with extended details and SSL information
```
gam version extended
GAM 7.06.14 - https://github.com/GAM-team/GAM - pyinstaller
GAM Team <google-apps-manager@googlegroups.com>
Python 3.13.3 64-bit final
MacOS Sequoia 15.4.1 x86_64
Path: /Users/Admin/bin/gam7
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain: domain.com
Time: 2023-06-02T21:10:00-07:00
Your system time differs from admin.googleapis.com by less than 1 second
OpenSSL 3.4.0 22 Oct Sep 2024
cryptography 43.0.3
filelock 3.16.1
google-api-python-client 2.149.0
google-auth-httplib2 0.2.0
google-auth-oauthlib 1.2.1
google-auth 2.35.0
httplib2 0.22.0
passlib 1.7.4
python-dateutil 2.9.0.post0
yubikey-manager 5.5.1
admin.googleapis.com connects using TLSv1.3 TLS_AES_256_GCM_SHA384
```

Print the current and latest versions of Gam and:
* set the return code to 0 if the current version is the latest version
* set the return code to 1 if the current version is not the latest
```
gam version checkrc
GAM 5.35.08 - https://github.com/taers232cGAM7
GAM Team <google-apps-manager@googlegroups.com>
Python 3.8.1 64-bit final
google-api-python-client 2.77.0
httplib2 0.16.0
oauth2client 4.1.3
MacOS High Sierra 10.13.6 x86_64
Path: /Users/Admin/bin/gam7
Version Check:
  Current: 5.35.08
   Latest: 7.06.14
echo $?
1
```

Print the current version number without details
```
gam version simple
7.06.14
```
In Linux/MacOS you can do:
```
VER=`gam version simple`
echo $VER
```
Print the current version of Gam and address of this Wiki
```
gam help
GAM 7.06.14 - https://github.com/GAM-team/GAM
GAM Team <google-apps-manager@googlegroups.com>
Python 3.13.3 64-bit final
MacOS Sequoia 15.4.1 x86_64
Path: /Users/Admin/bin/gam7
Config File: /Users/admin/GAMConfig/gam.cfg, Section: DEFAULT, customer_id: my_customer, domain: domain.com
Time: 2023-06-02T21:10:00-07:00
Help: Syntax in file /Users/Admin/bin/gam7/GamCommands.txt
Help: Documentation is at https://github.com/GAM-team/GAM/wiki
```
