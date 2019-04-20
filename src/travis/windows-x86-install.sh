cd src
pyinstaller --clean -F --distpath=gam $GAMOS-gam.spec
gam/gam version
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp GamCommands.txt gam
cp whatsnew.txt gam
cp gam-setup.bat gam
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.zip
/c/Program\ Files/7-Zip/7z.exe a -tzip $GAM_ARCHIVE gam -xr!.svn
mkdir gam-64
cp -rf gam/* gam-64/;
/c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/candle.exe -arch x86 gam.wxs
/c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/light.exe -ext /c/Program\ Files\ \(x86\)/WiX\ Toolset\ v3.11/bin/WixUIExtension.dll gam.wixobj -o gam-$GAMVERSION-$GAMOS-$PLATFORM.msi || true;
rm *.wixpdb
