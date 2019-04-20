sudo apt-get --yes update
sudo apt --yes dist-upgrade
sudo apt --yes install build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libc6-dev libbz2-dev
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
tar xvf Python-3.7.3.tar.xz
cd Python-3.7.3
./configure --enable-optimizations
sudo make altinstall
PATH=/usr/local/bin:$PATH
/usr/local/bin/python -V
python -V
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
