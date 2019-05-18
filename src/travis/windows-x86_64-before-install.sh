until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cinst -y python3
cd ~/pybuild
exefile=Win64OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.exe
if [ ! -e $exefile ]; then
  echo "Downloading $exefile..."
  wget --quiet https://slproweb.com/download/$exefile
fi
if [ ! -e ssl/libssl-1_1-x64.dll ]; then
  echo "Installing $exefile..."
  powershell ".\\${exefile} /silent /sp- /suppressmsgboxes /DIR=ssl"
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
