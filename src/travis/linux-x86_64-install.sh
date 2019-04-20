cd src
pyinstaller --clean -F --distpath=gam $GAMOS-gam.spec
gam/gam version
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam
echo "PyInstaller GAM is:"
du -ch gam/gam
staticx gam/gam gam/gam-static
mv gam/gam gam/gam-linked
mv gam/gam-static gam/gam
echo "StaticX GAM is:"
du -ch gam/gam
echo "PyInstaller GAM time is:"
gam/gam-linked version check
echo "StaticX GAM is:"
gam/gam version check
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.tar.xz
tar cfJ $GAM_ARCHIVE gam/
echo "Archive size is:"
du -ch $GAM_ARCHIVE
