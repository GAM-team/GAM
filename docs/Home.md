- [Introduction](#introduction)
- [Requirements](#requirements)
- [Installation - First time GAM7 installation](#installation---first-time-gam7-installation)
- [Installation - Upgrading from Legacy GAM](#installation---upgrading-from-legacy-gam)

# Introduction
GAM7 is a free, open source command line tool for Google Workspace Administrators to manage domain and user settings quickly and easily.

This page provides simple instructions for downloading, installing and starting to use GAM7.

GAM7 requires paid, or Education/Non-profit, editions of Google Workspace. G Suite Legacy Free Edition has limited API support and not all GAM commands work.

GAM7 is a rewrite/extension of Jay Lee's [Legacy GAM], without his efforts, this version wouldn't exist.

GAM7 is backwards compatible with [Legacy GAM], meaning that if your command works with Legacy GAM, it will also work with GAM7. There may be differences in output, but the syntax is compatible.

# Documentation
Documentation for GAM7 is hosted in the [GitHub GAM7 Wiki] and in Gam*.txt files.
Legacy GAM documentation is hosted in the [GitHub Legacy Wiki].

# Mailing List / Discussion group
The GAM mailing list / discussion group is hosted on [Google Groups].  You can join the list and interact via email, or just post from the web itself.

# Source Repository
The official GAM7 source repository is on [GitHub] in the master branch.

# Author
GAM7 is maintained by <a href="mailto:ross.scroggs@gmail.com">Ross Scroggs</a>.

# Requirements
To run all commands properly, GAM7 requires three things:
* An API project which identifies your install of GAM7 to Google and keeps track of API quotas.
* Authorization to act as your Google Workspace Administrator in order to perform management functions like add users, modify group settings and membership and pull domain reports.
* A special service account that is authorized to act on behalf of your users in order to modify user-specific settings and data such as Drive files, Calendars and Gmail messages and settings like signatures.

# Installation - First time GAM7 installation
Use these steps if you have never used any version of GAM in your domain. They will create a GAM project
and all necessary authentications.

* Download: [Downloads-Installs](Downloads-Installs)
* Configuration: [GAM7 Configuration](gam.cfg)
* Install: [How to Install Advanced GAM](How-to-Install-Advanced-GAM)

# Installation - Upgrading from Legacy GAM
Use these steps if you have used any version of Legacy GAM in your domain. They will update your GAM project
and all necessary authentications.

* Download: [Downloads-Installs](Downloads-Installs)
* Configuration: [GAM7 Configuration](gam.cfg)
* Upgrade: [How to Upgrade from Legacy GAM](How-to-Upgrade-from-Legacy-GAM)

You can install multiple versions of GAM and GAM7 in different parallel directories.

[Legacy GAM]: https://github.com/GAM-team/GAM/releases?q=6.58&expanded=true
[GAM7]: https://github.com/GAM-team/GAM
[GitHub Releases]: https://github.com/GAM-team/GAM/releases
[GitHub]: https://github.com/GAM-team/GAM/tree/master
[GitHub Legacy Wiki]: https://github.com/GAM-team/GAM/wiki/
[GitHub GAM7 Wiki]: https://github.com/taers232c/GAMADV-XTD3/wiki/
[Google Groups]: https://groups.google.com/group/google-apps-manager
[GAM Updates]: https://github.com/taers232c/GAMADV-XTD3/wiki/GamUpdates
