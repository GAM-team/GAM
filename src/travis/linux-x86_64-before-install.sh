sudo apt-get --yes update
sudo apt --yes dist-upgrade
#sudo apt --yes install build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libc6-dev libbz2-dev
#wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
#tar xf Python-3.7.3.tar.xz
#cd Python-3.7.3
#sudo ./configure --enable-optimizations > /dev/null
#sudo make altinstall > /dev/null || sudo make altinstall
#echo "installing pip"
#wget https://bootstrap.pypa.io/get-pip.py
#sudo /usr/local/bin/python3.7 get-pip.py
#echo "pip3.7 installed"
#ls -alRF /usr/local/bin
pip freeze > requirements.txt
sudo pip install --upgrade -r requirements.txt
sudo rm requirements.txt
sudo pip install pyinstaller
