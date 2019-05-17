until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cinst -y --forcex86 python3
cd ~/pybuild
msifile=Win32OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.msi
if [ ! -e $msifile ]; then
  echo "Downloading $msifile..."
  wget --quiet https://slproweb.com/download/$msifile
fi
if { ! -e ssl/libeay32.dll ]; then
  msiexec /a $msifile /qn TARGETDIR=ssl
fi
echo "OpenSSL dlls..."
ls -al ssl
echo "Python dlls..."
ls -al /c/Python37/DLLs
cp -v ssl/*.dll /c/Python37/DLLs
export PATH=$PATH:/c/Python37/scripts
until cinst -y wixtoolset; do echo "trying again..."; done
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
