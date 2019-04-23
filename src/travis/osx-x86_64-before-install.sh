brew update
brew upgrade openssl@1.1
brew upgrade python3
export PATH=/usr/local/opt/python/libexec/bin:$PATH
pip install --upgrade pip
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r src/requirements.txt
pip install pyinstaller
