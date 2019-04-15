powershell Install-WindowsFeature Net-Framework-Core
cinst -y --forcex86 python2
export PATH=$PATH:/c/Python27/scripts
cinst -y wixtoolset
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
