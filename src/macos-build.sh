rmdir /q /s gam
rmdir /q /s build
rmdir /q /s dist
rm -rf gam-$1-macos.tar.xz

/Library/Frameworks/Python.framework/Versions/2.7/bin/pyinstaller --clean -F --distpath=gam macos-gam.spec
cp LICENSE gam
cp whatsnew.txt gam

tar cfJ gam-$1-macos.tar.xz gam/ 
