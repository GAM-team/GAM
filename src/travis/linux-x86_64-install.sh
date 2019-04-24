cd src
$python -OO -m PyInstaller --clean --debug -F --distpath=gam $GAMOS-gam.spec
gam/gam version extended
export GAMVERSION=`gam/gam version simple`
cp LICENSE gam
cp whatsnew.txt gam
cp GamCommands.txt gam
this_glibc_ver=$(ldd --version | awk '/ldd/{print $NF}')
GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-$this_glibc_ver.tar.xz
tar cfJ $GAM_ARCHIVE gam/
echo "PyInstaller GAM  info:"
du -h gam/gam
time gam/gam version extended

if [[ "$dist" == "xenial" ]]; then
  GAM_LEGACY_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-legacy.tar.xz
  $python -OO -m staticx gam/gam gam/gam-staticx
  strip gam/gam-staticx
  rm gam/gam
  cp staticx-gam.sh gam/gam
  tar cfJ $GAM_LEGACY_ARCHIVE gam/
  echo "Legacy StaticX GAM info:"
  du -h gam/gam-staticx
  time gam/gam version extended
fi
