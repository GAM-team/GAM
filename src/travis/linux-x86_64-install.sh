cd src
pyinstaller --clean --debug -F --distpath=gam $GAMOS-gam.spec
gam/gam version
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.tar.xz
tar cfJ $GAM_ARCHIVE gam/
echo "PyInstaller GAM  info:"
du -h gam/gam
time gam/gam version

GAM_LEGACY_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-legacy.tar.xz
staticx gam/gam gam/gam-staticx
strip gam/gam-staticx
rm gam/gam
cp staticx-gam.sh gam/gam
tar cfJ $GAM_LEGACY_ARCHIVE gam/
echo "Legacy StaticX GAM info:"
du -h gam/gam-staticx
time gam/gam version
