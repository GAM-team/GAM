export distpath="dist/"
export gampath="${distpath}gam"
rm -rf $gampath
#mkdir -p $gampath
#export gampath=$(readlink -e $gampath)
$pip install wheel
$python -OO -m PyInstaller --clean --noupx --strip --distpath $gampath gam.spec
export gam="${gampath}/gam"
export GAMVERSION=$($gam version simple)
cp LICENSE $gampath
cp GamCommands.txt $gampath
this_glibc_ver=$(ldd --version | awk '/ldd/{print $NF}')
GAM_ARCHIVE="gam-${GAMVERSION}-${GAMOS}-${PLATFORM}-glibc${this_glibc_ver}.tar.xz"
rm $gampath/lastupdatecheck.txt
# tar will cd to dist and tar up gam/
tar -C ${distpath} --create --file "$GAM_ARCHIVE" --xz gam
echo "PyInstaller GAM info:"
du -h $gam
time $gam version extended
if ([ "${ImageOS}" == "ubuntu20" ]) && [ "${HOSTTYPE}" == "x86_64" ]; then
  GAM_LEGACY_ARCHIVE=gam-${GAMVERSION}-${GAMOS}-${PLATFORM}-legacy.tar.xz
  $python -OO -m staticx $gam $gam-staticx
  #strip $gam-staticx
  rm $gampath/gam
  mv $gam-staticx $gam
  chmod 755 $gam
  rm $gampath/lastupdatecheck.txt
  tar -C dist/ --create --file "$GAM_LEGACY_ARCHIVE" --xz gam
  echo "Legacy StaticX GAM info:"
  du -h $gam
  time $gam version extended
fi
echo "GAM packages:"
ls -l gam-*.tar.xz
