echo "Installing Net-Framework-Core..."
export mypath=$(pwd)
until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cd ~/pybuild
export exefile=Win64OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.exe
if [ ! -e $exefile ]; then
  echo "Downloading $exefile..."
  wget --quiet https://slproweb.com/download/$exefile
fi
echo "Installing $exefile..."
powershell ".\\${exefile} /silent /sp- /suppressmsgboxes /DIR=C:\\ssl"
cinst -y python3
until cinst -y wixtoolset; do echo "trying again..."; done
echo "OpenSSL dlls..."
ls -alRF /c/ssl
echo "c drive"
ls -al /c/
echo "Python dlls..."
ls -al /c/Python37/DLLs
until cp -v /c/ssl/*.dll /c/Python37/DLLs; do echo "trying again..."; done
export PATH=$PATH:/c/Python37/scripts
cd $mypath
export python=/c/Python37/python.exe
export pip=pip

$pip install --upgrade pip
$pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 $pip install -U
$pip install --upgrade -r src/requirements.txt
#$pip install --upgrade pyinstaller

# Install PyInstaller from source and build bootloader
# to try and avoid getting flagged as malware since
# lots of malware uses PyInstaller default bootloader
# https://stackoverflow.com/questions/53584395/how-to-recompile-the-bootloader-of-pyinstaller
echo "Downloading PyInstaller..."
wget --quiet https://github.com/pyinstaller/pyinstaller/releases/download/v$PYINSTALLER_VERSION/PyInstaller-$PYINSTALLER_VERSION.tar.gz
tar xf PyInstaller-$PYINSTALLER_VERSION.tar.gz
cd PyInstaller-$PYINSTALLER_VERSION/bootloader
echo "bootloader before:"
md5sum ../PyInstaller/bootloader/Windows-64bit/*
$python ./waf all --target-arch=64bit
echo "bootloader after:"
md5sum ../PyInstaller/bootloader/Windows-64bit/*
echo "PATH: $PATH"
cd ..
$python setup.py install
echo "cd to $mypath..."
cd $mypath
