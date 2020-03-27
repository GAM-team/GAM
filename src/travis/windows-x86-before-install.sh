echo "Installing Net-Framework-Core..."
export mypath=$(pwd)

choco install vcbuildtools

until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cd ~
export exefile=Win32OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.exe
if [ ! -e $exefile ]; then
  echo "Downloading $exefile..."
  wget --quiet https://slproweb.com/download/$exefile
fi
echo "Installing $exefile..."
powershell ".\\${exefile} /silent /sp- /suppressmsgboxes /DIR=C:\\ssl"
export python_file=python-$BUILD_PYTHON_VERSION.exe
wget --quiet https://www.python.org/ftp/python/$BUILD_PYTHON_VERSION/$python_file
powershell ".\\${python_file} /quiet InstallAllUsers=1 TargetDir=c:\\python"
until cinst -y wixtoolset; do echo "trying again..."; done
until cp -v /c/ssl/libcrypto-1_1.dll /c/python/DLLs/libcrypto-1_1.dll; do echo "trying again..."; done
until cp -v /c/ssl/libssl-1_1.dll /c/python/DLLs/libssl-1_1.dll; do echo "trying again..."; done
export PATH=$PATH:/c/python/scripts
cd $mypath
export python=/c/python/python.exe
export pip=/c/python/scripts/pip.exe
until [ -f $python ]; do :; done
until [ -f $pip ]; do :; done

$pip install --upgrade pip
$pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 $pip install -U
$pip install --upgrade -r src/requirements.txt
#$pip install --upgrade pyinstaller
# Install PyInstaller from source and build bootloader
# to try and avoid getting flagged as malware since
# lots of malware uses PyInstaller default bootloader
# https://stackoverflow.com/questions/53584395/how-to-recompile-the-bootloader-of-pyinstaller
echo "Downloading PyInstaller..."
wget --quiet https://github.com/pyinstaller/pyinstaller/archive/develop.tar.gz
tar xf develop.tar.gz
cd pyinstaller-develop/bootloader
echo "bootloader before:"
md5sum ../PyInstaller/bootloader/Windows-32bit/*
$python ./waf all --msvc_version "msvc 14.0"
echo "bootloader after:"
md5sum ../PyInstaller/bootloader/Windows-32bit/*
echo "PATH: $PATH"
cd ..
$python setup.py install
echo "cd to $mypath"
cd $mypath
