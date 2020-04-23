cd src
echo "MacOS Version Info According to Python:"
python -c "import platform; print(platform.mac_ver())"
$python -OO -m PyInstaller --clean --noupx --strip -F gam.spec
export gampath=dist
export gam="$gampath/gam"
$gam version extended
export GAMVERSION=`$gam version simple`
cp LICENSE $gampath
cp whatsnew.txt $gampath
cp GamCommands.txt $gampath
MACOSVERSION=$(defaults read loginwindow SystemVersionStampAsString)
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-MacOS$MACOSVERSION.tar.xz
rm $gampath/lastupdatecheck.txt
gtar cfJ $GAM_ARCHIVE --transform s/$gampath/gam $gampath
