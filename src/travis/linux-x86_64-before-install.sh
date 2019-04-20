deactivate
source deactivate
sudo apt-get --yes update
sudo apt --yes dist-upgrade
sudo apt --yes install build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libc6-dev libbz2-dev
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
tar xf Python-3.7.3.tar.xz
cd Python-3.7.3
sudo ./configure --enable-optimizations
echo "BEFORE"
ls -al /usr/bin
sudo make install
echo "AFTER"
ls -al /usr/bin
sudo /usr/bin/pip3 install --upgrade pip
sudo /usr/bin/pip3 freeze > requirements.txt
sudo /usr/bin/pip3 install --upgrade -r requirements.txt
sudo rm requirements.txt
sudo /usr/bin/pip3 pip install pyinstaller
