until powershell Install-WindowsFeature Net-Framework-Core; do echo "trying again..."; done
cinst -y python3
cinst -y openssl.light
cp -v /c/Program\ Files/OpenSSL/bin/*.dll /c/Python37/DLLs
export PATH=$PATH:/c/Python37/scripts
until cinst -y wixtoolset; do echo "trying again..."; done
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
