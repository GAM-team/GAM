echo "MacOS Version Info According to Python:"
python -c "import platform; print(platform.mac_ver())"
echo "Xcode versionn:"
xcodebuild -version
export gampath=dist/gam
rm -rf $gampath
export DYLD_LIBRARY_PATH="/Library/Frameworks/Python.framework/Versions/3.9/lib:$DYLD_LIBRARY_PATH"
export DYLD_PRINT_LIBRARIES=YES
$python ./gam.py version extended
unset DYLD_PRINT_LIBRARIES
$python -OO -m PyInstaller --clean --noupx --strip -F --distpath $gampath gam.spec
export gam="$gampath/gam"
$gam version extended
export GAMVERSION=`$gam version simple`
cp LICENSE $gampath
cp GamCommands.txt $gampath
MACOSVERSION=$(defaults read loginwindow SystemVersionStampAsString)
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-MacOS$MACOSVERSION.tar.xz
rm $gampath/lastupdatecheck.txt
# tar will cd to dist/ and tar up gam/
tar -C dist/ --create --file $GAM_ARCHIVE --xz gam
