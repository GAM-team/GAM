sudo brew update
sudo brew install python@2 || true
sudo brew link --overwrite python@2
sudo pip install --upgrade pip
sudo pip freeze > requirements.txt
sudo pip install --upgrade -r requirements.txt
sudo rm requirements.txt
sudo pip install --upgrade altgraph
sudo pip install pyinstaller
