cd src
pyinstaller --clean --debug -F --distpath=gam $GAMOS-gam.spec
gam/gam version
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM.tar.xz
tar cfJ $GAM_ARCHIVE gam/
