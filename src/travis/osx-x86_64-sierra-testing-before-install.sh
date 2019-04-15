brew update
brew install python@2
curl https://bootstrap.pypa.io/get-pip.py | sudo python
pip freeze > requirements.txt
sudo pip install --upgrade -r requirements.txt
rm requirements.txt
sudo pip install --upgrade altgraph
sudo pip install pyinstaller
