# What is GAM7?
GAM7 is a new official version of GAM which is based on and supports all the commands and features of Ross’ GAM-ADV release as well as the commands of Jay’s release. Ross and Jay have worked to re-combine (merge) the source codebases for their separate GAM versions into a single version. This means all admins get the same rich GAM feature set and there’s no community confusion about standard GAM vs advanced GAM.

# Is the GAM7 announcement a big deal?
Yes! We’re announcing a single version of GAM, no need to choose between Jay and Ross’ version. GAM7 has a rich feature set that’s available to all Workspace admins. A single version that supports all commands.
# Is the GAM7 announcement a big deal?
No! This is also just business as usual for the GAM community. Forking (splitting the source code into a separate project) and merging (combining them back together again) is a purposefully designed feature of open-source. Both Ross and Jay will continue to support the GAM community but going forward we’ll do so with a single GAM7 codebase and release.

# Has something changed for Jay?
Nope! Jay continues to work for Google professional services as he has for the past 6 years. He’s still raising three great kids (two in high school now) and enjoys projects around the house during his ever-dwindling free time. He’s still contributing to GAM with both source code and new features as well as helping in the GAM Chat and Group communities. He’s still a huge Philly sports fan. Go [Phillies](https://www.mlb.com/phillies)! Go [Eagles](https://www.philadelphiaeagles.com/)!

![image](https://github.com/user-attachments/assets/a8eb6d3d-1d50-4f2d-ba43-a2a18d90fa6b)

The 27ft RV Jay drove his family to Niagara Falls this summer. They’re all still talking to him,
some in full sentences 🙂

# Has something changed with Ross?
He’s just older, 75 and counting.

(Jay here, this is all I could get from Ross but he’s his usual awesome self helping admins in Chat and Groups forums as I write this and adding new features. Because some have asked, Ross is a real person. He is not an Advanced GenAI as rumours have claimed. 🙂)

# How do I know which GAM I’m using today?
Run:

```
gam version
```

- If you see jay0lee@gmail.com in the output, you’re running Jay’s version (Standard GAM). 

- If you see ross.scroggs@gmail.com in the output you’re running Ross’ Advanced GAM version.

- If you see google-apps-manager@googlegroups.com in the output you’ve already upgraded to GAM7.

# What does this mean if I’m using Jay’s GAM (Standard / Basic GAM)?
Updating from Jay’s GAM to GAM7 may introduce some issues. If your GAM install is critical to your product Google environment you may want to wait for some of the upgrade challenges to be ironed out in the next few weeks. Having said that, GAM stores all of it’s configuration in the GAM install folder so backing up that folder should preserve your old GAM config. For [upgrade instructions see the wiki](https://github.com/GAM-team/GAM/wiki/How-to-upgrade-from-Standard-GAM).

# What does this mean if I’m using Ross’ GAM-ADV?
GAM7 is effectively the same source as GAMADV-XTD3 with minor changes to point to the [github.com/GAM-team/GAM](http://github.com/GAM-team/GAM) site. On Linux/MacOS you should be able to run:

```
bash <(curl -s -S -L https://git.io/gam-install) -l
```

To upgrade. On Windows, download the latest MSI from [git.io/gam-releases](http://git.io/gam-releases) and install it to the same path you had GAM-ADV installed.

Both GAM7 and GAM-ADV versions use the same configuration file (gam.cfg), and credentials; they are interchangeable.

# Help!!! Something went wrong!
Well that’s not really a question but as ever, please reach out to either the GAM email support group:

[git.io/gam-group](http://git.io/gam-group)

Or the Google Chat Space:

[git.io/gam-chat](http://git.io/gam-chat)