powershell Install-WindowsFeature Net-Framework-Core
cinst -y $CINST_ARGS python3
cinst -y $CINST_ARGS openssl.light
ls -alRF "/c/Program Files/OpenSSL"
ls -alRF "/c/Python37/"
cp "/c/Program Files/OpenSSL/*.dll" "/c/Python37/DLLs"
export PATH=$PATH:/c/Python37/scripts
cinst -y wixtoolset
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
