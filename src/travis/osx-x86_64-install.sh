cd src
$python -OO -m PyInstaller --clean --debug -F --distpath=gam $GAMOS-gam.spec
export gam="gam/gam"
export gampath=~/gam
$gam version extended
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.tar.xz
rm gam/lastupdatecheck.txt
tar cfJ $GAM_ARCHIVE gam/
