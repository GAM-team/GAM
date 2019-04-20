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
rm gam/gam
mv gam/gam-static gam/gam
echo "StaticX GAM is:"
du -ch gam/gam
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.tar.xz
tar cfJ $GAM_ARCHIVE gam/
