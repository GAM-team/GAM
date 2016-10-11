rm -rf gam
rm -rf build
rm -rf  dist
rm -rf gam-$1-linux-$(arch).tar.xz

pyinstaller --clean -F --distpath=gam linux-gam.spec
cp LICENSE gam
cp whatsnew.txt gam

tar cfJ gam-$1-linux-$(arch).tar.xz gam/ 
