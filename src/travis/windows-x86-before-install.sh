echo "Installing Net-Framework-Core..."
export mypath=$(pwd)
until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cd ~/pybuild
#export exefile=Win32OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.exe
#if [ ! -e $exefile ]; then
#  echo "Downloading $exefile..."
#  wget --quiet https://slproweb.com/download/$exefile
#fi
#echo "Installing $exefile..."
#powershell ".\\${exefile} /silent /sp- /suppressmsgboxes /DIR=C:\\ssl"
cinst -y --forcex86 python3
until cinst -y wixtoolset; do echo "trying again..."; done
#echo "OpenSSL dlls..."
#ls -alRF /c/ssl
#echo "c drive"
#ls -al /c/
#echo "Python dlls..."
#ls -al /c/Python37/DLLs
#until cp -v /c/ssl/*.dll /c/Python37/DLLs; do echo "trying again..."; done
export PATH=$PATH:/c/Python37/scripts
cd $mypath
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install --upgrade -r src/requirements.txt
pip install --upgrade pyinstaller
