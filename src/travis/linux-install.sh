cd src
if [[ "$TRAVIS_JOB_NAME" == *"Testing" ]]; then
  export gam="$python gam.py"
  export gampath=$(readlink -e .)
else
  $python -OO -m PyInstaller --clean --noupx --strip -F --distpath=gam gam.spec
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

  if ([ "${TRAVIS_DIST}" == "trusty" ] || [ "${TRAVIS_DIST}" == "xenial" ]) && [ "${PLATFORM}" == "x86_64" ]; then
    GAM_LEGACY_ARCHIVE=gam-${GAMVERSION}-${GAMOS}-${PLATFORM}-legacy.tar.xz
    $python -OO -m staticx -l /lib/x86_64-linux-gnu/libresolv.so.2 -l /lib/x86_64-linux-gnu/libnss_dns.so.2 gam/gam gam/gam-staticx
    strip gam/gam-staticx
    rm gam/gam
    mv gam/gam-staticx gam/gam
    chmod 755 gam/gam
    tar cvfJ $GAM_LEGACY_ARCHIVE gam/
    echo "Legacy StaticX GAM info:"
    du -h gam/gam
    time $gam version extended
  fi
  echo "GAM packages:"
  ls -l gam-*.tar.xz
fi
