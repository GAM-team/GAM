cd src
echo "MacOS Version Info According to Python:"
python -c "import platform; print(platform.mac_ver())"
$python -OO -m PyInstaller --clean --noupx --strip -F --distpath=gam gam.spec
export gam="gam/gam"
export gampath=gam
$gam version extended
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam
MACOSVERSION=$(defaults read loginwindow SystemVersionStampAsString)
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-MacOS$MACOSVERSION.tar.xz
rm gam/lastupdatecheck.txt
tar cfJ $GAM_ARCHIVE gam/
