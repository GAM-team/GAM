powershell Install-WindowsFeature Net-Framework-Core
cinst -y $CINST_ARGS python3
export PATH=$PATH:/c/Python37/scripts
cinst -y wixtoolset
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r requirements.txt
pip install pyinstaller
