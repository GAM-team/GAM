sudo add-apt-repository --yes ppa:deadsnakes/ppa
sudo apt-get --yes update
sudo apt --yes dist-upgrade
sudo apt --yes install python3
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
