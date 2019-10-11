cd src
if [ "$VMTYPE" == "test" ]; then
  export gam="$python gam.py"
  export gampath=$(readlink -e .)
else
  $python -OO -m PyInstaller --clean --noupx --strip -F --distpath=gam $GAMOS-gam.spec
  export gam="gam/gam"
  export gampath=$(readlink -e gam)
  export GAMVERSION=`$gam version simple`
  cp LICENSE $gampath
  cp whatsnew.txt $gampath
  cp GamCommands.txt $gampath
  this_glibc_ver=$(ldd --version | awk '/ldd/{print $NF}')
  GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-glibc$this_glibc_ver.tar.xz
  rm $gampath/lastupdatecheck.txt
  tar cfJ $GAM_ARCHIVE gam/
  echo "PyInstaller GAM info:"
  du -h gam/gam
  time $gam version extended

  if [[ "$dist" == "precise" ]]; then
    GAM_LEGACY_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-legacy.tar.xz
    $python -OO -m staticx gam/gam gam/gam-staticx
    strip gam/gam-staticx
    rm gam/gam
    mv gam/gam-staticx gam/gam
    tar cfJ $GAM_LEGACY_ARCHIVE gam/
    echo "Legacy StaticX GAM info:"
    du -h gam/gam
    time $gam version extended
  fi

fi
