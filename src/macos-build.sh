rm -rf gam
rm -rf build
rm -rf dist
rm -rf gam-$1-macos.tar.xz

/Library/Frameworks/Python.framework/Versions/2.7/bin/pyinstaller --clean -F --distpath=gam macos-gam.spec
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam

tar cfJ gam-$1-macos.tar.xz gam/ 
