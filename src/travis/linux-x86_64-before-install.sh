sudo apt-get --yes update
sudo apt --yes dist-upgrade
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
sudo rm requirements.txt
pip install pyinstaller
pip install staticx
