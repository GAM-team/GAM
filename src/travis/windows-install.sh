cd src
echo "compiling GAM with pyinstaller..."
pyinstaller --clean --noupx -F gam.spec
export gampath=$(readlink -e dist)
export gam="${gampath}/gam"
echo "running compiled GAM..."
$gam version
export GAMVERSION=`$gam version simple`
rm $gampath/lastupdatecheck.txt
cp LICENSE $gampath
cp GamCommands.txt $gampath
cp whatsnew.txt $gampath
cp gam-setup.bat $gampath
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.zip
/c/Program\ Files/7-Zip/7z.exe a -tzip $GAM_ARCHIVE $gampath -xr!.svn
/c/Program\ Files/7-Zip/7z.exe rn $GAM_ARCHIVE dist\ gam\
mkdir gam-64
cp -rf $gampath/* gam-64/
/c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/candle.exe -arch $WIX_BITS gam.wxs
/c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/light.exe -ext /c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/WixUIExtension.dll gam.wixobj -o gam-$GAMVERSION-$GAMOS-$PLATFORM.msi || true;
rm *.wixpdb
