# Introduction
GAM7 is a free, open source command line tool for Google Workspace (formerly G Suite) Administrators to manage domain and user settings quickly and easily.

GAM7 is built with Python 3.

This page provides simple instructions for downloading, installing and starting to use GAM7.

GAM7 runs on all versions of Google Workspace; Google Apps Free Edition has limited API support and not all GAM commands work.

GAM7 is a rewrite/extension of Jay Lee's Legacy GAM.

GAM7 is backwards compatible with Legacy GAM, meaning that if your command works with Legacy GAM, it will also work with GAM7. There may be differences in output, but the syntax is compatible.

# Documentation
Documentation for GAM7 is hosted in the [GitHub Wiki] and in Gam*.txt files.

# Mailing List / Discussion group
The GAM mailing list / discussion group is hosted on [Google Groups].  You can join the list and interact via email, or just post from the web itself.

# Source Repository
The official GAM7 source repository is on [GitHub] in the master branch.

# Author
GAM7 is maintained by Jay <a href="mailto:google-apps-manager@googlegroups.com">Jay Lee</a> and Ross <a href="mailto:ross.scroggs@gmail.com">Ross Scroggs</a>.

# Requirements
To run all commands properly, GAM7 requires three things:
* An API project which identifies your install of GAM7 to Google and keeps track of API quotas.
* Authorization to act as your G Suite Administrator in order to perform management functions like add users, modify group settings and membership and pull domain reports.
* A special service account that is authorized to act on behalf of your users in order to modify user-specific settings and data such as Drive files, Calendars and Gmail messages and settings like signatures.

# Installation - First time GAM installation
Use these steps if you have never used any version of GAM in your domain. They will create a GAM project
and all necessary authentications.

| [Downloads] | [Configuration] | [Install] |
|    :---:    |      :---:      |   :---:   |

# Installation - Update GAM7
Use these steps to update your version of GAM7.

| [Downloads] | [Configuration] | [Update] |
|    :---:    |      :---:      |      :---:       |

# Installation - Upgrading from Advanced GAM
Use these steps if you have used any version of Advanced GAM in your domain.
and all necessary authentications.

| [Downloads] | [Configuration] | [UpgradeFromAdvanced] |
|    :---:    |      :---:      |         :---:         |

# Installation - Upgrading from Legacy GAM
Use these steps if you have used any version of Legacy GAM in your domain. They will update your GAM project
and all necessary authentications.

| [Downloads] | [Configuration] | [UpgradeFromLegacy] |
|    :---:    |      :---:      |         :---:         |

# Multiple Versions
You can install multiple versions of GAM and GAM7 in different parallel directories.

[GAM]: https://github.com/GAM-team/GAM
[GitHub Releases]: https://github.com/GAM-team/GAM/releases
[GitHub]: https://github.com/GAM-team/GAM/tree/master
[GitHub Wiki]: https://github.com/GAM-team/GAM/wiki
[Google Groups]: https://groups.google.com/group/google-apps-manager
[Downloads]: https://github.com/GAM-team/GAM/wiki/Downloads
[Configuration]: https://github.com/GAM-team/GAM/wiki/gam.cfg
[Install]: https://github.com/GAM-team/GAM/wiki/How-to-Install-GAM7
[Update]: https://github.com/GAM-team/GAM/wiki/How-to-Update-GAM7
[UpgradeFromAdvanced]: https://github.com/GAM-team/GAM/wiki/How-to-Upgrade-Advanced-GAM-to-GAM7
[UpgradeFromLegacy]: https://github.com/GAM-team/GAM/wiki/How-to-Upgrade-Legacy-GAM-to-GAM7
[Updates]: https://github.com/GAM-team/GAM/wiki/GAM-Updates
