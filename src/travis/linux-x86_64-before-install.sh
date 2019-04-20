sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt dist-upgrade
sudo apt install python3
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
