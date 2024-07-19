- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation - First time GAM installation](#installation---first-time-gam-installation)
- [Installation - Upgrading from a GAM version other than a prior version of GAMADV-X or GAMADV-XTD or GAMADV-XTD3](#installation---upgrading-from-a-gam-version-other-than-a-prior-version-of-gamadv-x-or-gamadv-xtd-or-gamadv-xtd3)
- [Installation - Upgrading from a prior version of GAMADV-X or GAMADV-XTD or GAMADV-XTD3](#installation---upgrading-from-a-prior-version-of-gamadv-x-or-gamadv-xtd-or-gamadv-xtd3)

# Introduction
GAMADV-XTD3 is a free, open source command line tool for Google Workspace Administrators to manage domain and user settings quickly and easily.

GAMADV-XTD3 is built with Python 3; as Python 2 support ends on 2020-01-01, this is the version of Advanced GAM that new/existing users should install.

This page provides simple instructions for downloading, installing and starting to use GAMADV-XTD3.

GAMADV-XTD3 requires paid, or Education/Non-profit, editions of Google Workspace. G Suite Legacy Free Edition has limited API support and not all GAM commands work.

GAMADV-XTD3 is a rewrite/extension of Jay Lee's [GAM], without his efforts, this version wouldn't exist.

GAMADV-XTD3 is backwards compatible with [GAM], meaning that if your command works with regular GAM, it will also work with GAMADV-XTD3. There may be differences in output, but the syntax is compatible.

# Documentation
Basic GAM documentation is hosted in the [GitHub Wiki]. Documentation specifically for GAMADV-XTD3 is hosted in the [GitHub GAMADV-XTD3 Wiki] and in Gam*.txt files.

# Mailing List / Discussion group
The GAM mailing list / discussion group is hosted on [Google Groups].  You can join the list and interact via email, or just post from the web itself.

# Source Repository
The official GAMADV-XTD3 source repository is on [GitHub] in the master branch.

# Author
GAMADV-XTD3 is maintained by <a href="mailto:ross.scroggs@gmail.com">Ross Scroggs</a>.

# Requirements
To run all commands properly, GAMADV-XTD3 requires three things:
* An API project which identifies your install of GAMADV-XTD3 to Google and keeps track of API quotas.
* Authorization to act as your Google Workspace Administrator in order to perform management functions like add users, modify group settings and membership and pull domain reports.
* A special service account that is authorized to act on behalf of your users in order to modify user-specific settings and data such as Drive files, Calendars and Gmail messages and settings like signatures.

# Installation - First time GAM installation
Use these steps if you have never used any version of GAM in your domain. They will create a GAM project
and all necessary authentications.

* Download: [Downloads-Installs](Downloads-Installs)
* Configuration: [GAM Configuration](gam.cfg)
* Install: [How to Install Advanced GAM](How-to-Install-Advanced-GAM)

# Installation - Upgrading from a GAM version other than a prior version of GAMADV-X or GAMADV-XTD or GAMADV-XTD3
Use these steps if you have used any version of GAM in your domain. They will update your GAM project
and all necessary authentications.

* Download: [Downloads-Installs](Downloads-Installs)
* Configuration: [GAM Configuration](gam.cfg)
* Upgrade: [How to Upgrade from Standard GAM](How-to-Upgrade-from-Standard-GAM)

# Installation - Upgrading from a prior version of GAMADV-X or GAMADV-XTD or GAMADV-XTD3
Use these steps if you already use GAMADV-X or GAMADV-XTD or GAMADV-XTD3. The updates may tell you to update your GAM project
or authentications because new features have been included.

* Updates: [GAM Updates]
* Download: [Downloads-Installs](Downloads-Installs)

You can install multiple versions of GAM and GAMADV-XTD3 in different parallel directories.

[GAM]: https://github.com/GAM-team/GAM
[GitHub Releases]: https://github.com/taers232c/GAMADV-XTD3/releases
[GitHub]: https://github.com/taers232c/GAMADV-XTD3/tree/master
[GitHub Wiki]: https://github.com/GAM-team/GAM/wiki/
[GitHub GAMADV-XTD3 Wiki]: https://github.com/taers232c/GAMADV-XTD3/wiki/
[Google Groups]: https://groups.google.com/group/google-apps-manager
[GAM Updates]: https://github.com/taers232c/GAMADV-XTD3/wiki/GamUpdates

