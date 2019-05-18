echo "Installing Net-Framework-Core..."
export mypath=$(pwd)
until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cinst -y --forcex86 python3
cd ~/pybuild
export exefile=Win32OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.exe
if [ ! -e $exefile ]; then
  echo "Downloading $exefile..."
  wget --quiet https://slproweb.com/download/$exefile
fi
if [ ! -e ssl/libssl-1_1-x64.dll ]; then
  echo "Installing $exefile..."
  powershell ".\\${exefile} /silent /sp- /suppressmsgboxes /DIR=C:\\ssl"
fi
echo "OpenSSL dlls..."
ls -alRF /c/ssl
echo "Python dlls..."
ls -al /c/Python37/DLLs
cp -v /c/ssl/*.dll /c/Python37/DLLs
export PATH=$PATH:/c/Python37/scripts
until cinst -y wixtoolset; do echo "trying again..."; done
cd $mypath
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
