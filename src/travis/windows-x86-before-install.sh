echo "Installing Net-Framework-Core..."
export mypath=$(pwd)
cd ~
until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cinst -y --forcex86 python3
until cinst -y wixtoolset; do echo "trying again..."; done
export PATH=$PATH:/c/Python38/scripts
cd $mypath
export python=/c/Python38/python.exe
export pip=/c/Python38/scripts/pip.exe

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
$python ./waf all --target-arch=32bit
echo "bootloader after:"
md5sum ../PyInstaller/bootloader/Windows-32bit/*
echo "PATH: $PATH"
cd ..
$python setup.py install
echo "cd to $mypath"
cd $mypath
