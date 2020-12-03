echo "compiling GAM with pyinstaller..."
export gampath="dist/gam"
rm -rf $gampath
mkdir -p $gampath
export gampath=$(readlink -e $gampath)
pyinstaller --clean --noupx -F --distpath $gampath gam.spec
export gam="${gampath}/gam"
echo "running compiled GAM..."
$gam version
export GAMVERSION=`$gam version simple`
rm $gampath/lastupdatecheck.txt
cp LICENSE $gampath
cp GamCommands.txt $gampath
cp gam-setup.bat $gampath
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.zip
/c/Program\ Files/7-Zip/7z.exe a -tzip $GAM_ARCHIVE $gampath -xr!.svn

echo "Running WIX candle $WIX_BITS..."
/c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/candle.exe -arch $WIX_BITS gam.wxs
echo "Done with WIX candle..."
echo "Running WIX light..."
/c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/light.exe -ext /c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/WixUIExtension.dll gam.wixobj -o gam-$GAMVERSION-$GAMOS-$PLATFORM.msi || true;
echo "Done with WIX light..."
rm *.wixpdb
