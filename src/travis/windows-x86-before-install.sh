powershell Install-WindowsFeature Net-Framework-Core
cinst -y --forcex86 python3
cinst -y --forcex86 openssl.light
/c/Program\ Files/OpenSSL/openssl version
cp -v /c/Program\ Files/OpenSSL/*.dll /c/Python37/DLLs
export PATH=$PATH:/c/Python37/scripts
cinst -y wixtoolset
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
