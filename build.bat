rmdir /q /s gam
rmdir /q /s gam-64
rmdir /q /s python-src-%1
rmdir /q /s build
rmdir /q /s dist
del /q /f gam-%1-python-src.zip
del /q /f gam-%1-windows.zip
del /q /f gam-%1-windows-x64.zip

\python27-32\python.exe setup.py py2exe
xcopy LICENSE gam\
xcopy whatsnew.txt gam\
xcopy cacert.pem gam\
xcopy admin-settings-v1.json gam\
del gam\w9xpopen.exe
"%ProgramFiles%\7-Zip\7z.exe" a -tzip gam-%1-windows.zip gam\ -xr!.svn

\python27\python.exe setup-64.py py2exe
xcopy LICENSE gam-64\
xcopy whatsnew.txt gam-64\
xcopy cacert.pem gam-64\
xcopy admin-settings-v1.json gam-64\
"%ProgramFiles%\7-Zip\7z.exe" a -tzip gam-%1-windows-x64.zip gam-64\ -xr!.svn

mkdir python-src-%1
mkdir python-src-%1\gdata
mkdir python-src-%1\atom
mkdir python-src-%1\apiclient
mkdir python-src-%1\httplib2
mkdir python-src-%1\oauth2client
mkdir python-src-%1\simplejson
mkdir python-src-%1\uritemplate
xcopy gam.py python-src-%1\
xcopy LICENSE python-src-%1\
xcopy whatsnew.txt python-src-%1\
xcopy /e gdata\*.* python-src-%1\gdata
xcopy /e atom\*.* python-src-%1\atom
xcopy /e apiclient\*.* python-src-%1\apiclient
xcopy /e httplib2\*.* python-src-%1\httplib2
xcopy /e oauth2client\*.* python-src-%1\oauth2client
xcopy /e simplejson\*.* python-src-%1\simplejson
xcopy /e uritemplate\*.* python-src-%1\uritemplate
xcopy cacert.pem python-src-%1\
xcopy admin-settings-v1.json python-src-%1\

cd python-src-%1
"%ProgramFiles%\7-Zip\7z.exe" a -tzip ..\gam-%1-python-src.zip * -xr!.svn
cd ..

\python27\python.exe googlecode_upload.py --project google-apps-manager --summary "GAM %1 Windows" --user %2 --password %3 --labels "ALPHA,Type-Archive,OpSys-Windows" gam-%1-windows.zip
\python27\python.exe googlecode_upload.py --project google-apps-manager --summary "GAM %1 Windows x64" --user %2 --password %3 --labels "ALPHA,Type-Archive,OpSys-Windows" gam-%1-windows-x64.zip
\python27\python.exe googlecode_upload.py --project google-apps-manager --summary "GAM %1 Python Source" --user %2 --password %3 --labels "ALPHA,Type-Archive,OpSys-All" gam-%1-python-src.zip
