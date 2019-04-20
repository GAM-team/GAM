sudo apt-get --yes update
sudo apt --yes dist-upgrade
sudo apt --yes install build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libc6-dev libbz2-dev
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
tar xf Python-3.7.3.tar.xz
cd Python-3.7.3
./configure --enable-optimizations
sudo make altinstall > /dev/null || sudo make altinstall
alias python=/usr/local/bin/python3.7
alias python3=/usr/local/bin/python3.7
alias python37=/usr/local/bin/python3.7
alias pip=/usr/local/bin/pip3.7
alias pip3=/usr/local/bin/pip3.7
alias pip37=/usr/local/bin/pip3.7
PATH=/usr/local/bin:$PATH
ls -alRF /usr/local/bin
echo "PYTHON -V"
python -V
echo "PYTHON3 -V"
python3 -V
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
