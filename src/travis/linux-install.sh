cd src
if [[ "$TRAVIS_JOB_NAME" == *"Testing" ]]; then
  export gam="$python -m gam"
  export gampath=$(readlink -e .)
else
  $python -OO -m PyInstaller --clean --noupx --strip -F gam.spec
  export gampath=$(readlink -e gam)
  export gam="${gampath}/gam"
  export GAMVERSION=`$gam version simple`
  cp LICENSE $gampath
  cp whatsnew.txt $gampath
  cp GamCommands.txt $gampath
  this_glibc_ver=$(ldd --version | awk '/ldd/{print $NF}')
  GAM_ARCHIVE=gam-$GAMVERSION-$GAMOS-$PLATFORM-glibc$this_glibc_ver.tar.xz
  rm $gampath/lastupdatecheck.txt
  tar cfJ --transform s/dist/gam/ $GAM_ARCHIVE $gampath
  echo "PyInstaller GAM info:"
  du -h $gam
  time $gam version extended

  if [ "${TRAVIS_DIST}" == "xenial" ] && [ "${PLATFORM}" == "x86_64" ]; then
    GAM_LEGACY_ARCHIVE=gam-${GAMVERSION}-${GAMOS}-${PLATFORM}-legacy.tar.xz
    $python -OO -m staticx -l /lib/x86_64-linux-gnu/libresolv.so.2 -l /lib/x86_64-linux-gnu/libnss_dns.so.2 $gam $gam-staticx
    strip $gam-staticx
    rm $gampath/gam
    mv $gam-staticx $gam
    chmod 755 $gam
    tar cvfJ --transform s/dist/gam/ $GAM_LEGACY_ARCHIVE $gampath
    echo "Legacy StaticX GAM info:"
    du -h $gam
    time $gam version extended
  fi
  echo "GAM packages:"
  ls -l gam-*.tar.xz
fi
