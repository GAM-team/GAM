rm -rf gam
rm -rf build
rm -rf dist
rm -rf gam-$1-linux-$(arch).tar.xz

export LD_LIBRARY_PATH=/usr/local/lib
pyinstaller --clean -F --distpath=gam linux-gam.spec
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam

tar cfJ gam-$1-linux-$(arch).tar.xz gam/ 
