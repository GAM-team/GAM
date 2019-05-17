until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cinst -y python3
cd ~/pybuild
msifile=Win64OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.msi
if [ ! -e $msifile ]; then
  echo "Downloading $msifile..."
  wget --quiet https://slproweb.com/download/$msifile
fi
if [ ! -e ssl/libeay32.dll ]; then
  echo "Extracting $msifile..."
  /c/Program\ Files/7-Zip/7z.exe e $msifile -ossl
fi
echo "OpenSSL dlls..."
ls -alRF ssl
echo "Python dlls..."
ls -al /c/Python37/DLLs
cp -v ssl/MainInstaller/*.dll /c/Python37/DLLs
export PATH=$PATH:/c/Python37/scripts
until cinst -y wixtoolset; do echo "trying again..."; done
cd ~
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
