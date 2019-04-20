brew update
brew upgrade python3
export PATH=/usr/local/opt/python/libexec/bin:$PATH
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
