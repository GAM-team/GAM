rmdir /q /s gam
rmdir /q /s gam-64
rmdir /q /s build
rmdir /q /s dist
del /q /f gam-%1-windows.zip
del /q /f gam-%1-windows-x64.zip

\python27-32\python.exe setup.py py2exe
xcopy LICENSE gam\
xcopy whatsnew.txt gam\
xcopy cacert.pem gam\
xcopy admin-settings-v1.json gam\
del gam\w9xpopen.exe
"%ProgramFiles(x86)%\7-Zip\7z.exe" a -tzip gam-%1-windows.zip gam\ -xr!.svn

\python27\python.exe setup-64.py py2exe
xcopy LICENSE gam-64\
xcopy whatsnew.txt gam-64\
xcopy cacert.pem gam-64\
xcopy admin-settings-v1.json gam-64\
"%ProgramFiles(x86)%\7-Zip\7z.exe" a -tzip gam-%1-windows-x64.zip gam-64\ -xr!.svn
