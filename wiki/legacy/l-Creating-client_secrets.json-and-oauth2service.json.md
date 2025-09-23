I am going to write here what i have done. I am a newbie on Debian :)

Step 1. 'apt install python2.7'

Step 2. 'sudo apt install python-wxgtk3.0'

Step 3. 'sudo apt install python-pip'

Step 4. 'pip install GoSync'

Step 5. 'apt-get install libyaml-dev libpython2.7-dev' <-- I had to install these

Step 6. 'sudo apt install libcanberra-gtk-module libcanberra-gtk3-module'

Step 7. 'python setup.py install'

Step 8. 'mkdir GoogleDrive'

Step 9. 'cd GoogleDrive'

Step 10. navigate to https://console.developers.google.com/apis/credentials hit 'Create credentials' and then 'OAuth client ID' (create one) and then navigate to it in the menu OAuth 2.0 client IDs. On the top you should see 'Download JSON'. Rename it to client_secrets.json and move it to the folder .gosync in your home directory.

Step 11. 'run GoSync in the GoogleDrive directory' (Chome or Chromium doesn't seem to work as default browser)

But from here i ran into GoSync failed to initialize. It is late maybe I continue this tomorrow (also formatting this here). But at least something is standing here.

It seems that python-wxgtk3.0 change a little bit (and i was unable to find the 2.8 version) I changed in:

/.local/lib/python2.7/site-packages/GoSync/GoSync.py:30: wxPyDeprecationWarning: Using deprecated class PySimpleApp. 
  app = wx.PySimpleApp()

to: 

/.local/lib/python2.7/site-packages/GoSync/GoSync.py:30: wxPyDeprecationWarning: Using deprecated class PySimpleApp. 
  app = wx.App(False)

asoneuhtaoeruchc234**(*HTHBXTFY&()(()*&)(*&%ŶITGEODONCDHCORLE)OÔ*E&%ÔE*%&O&OFDEOE

It would be nice if this page explained what's going on, since the GoSync app still sends people here, but evidently random typing was somehow considered to be a better choice.