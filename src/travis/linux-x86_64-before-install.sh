sudo apt-get --yes update
sudo apt --yes dist-upgrade
sudo apt --yes install build-essential checkinstall libreadline-gplv2-dev libncursesw5-dev libssl-dev libc6-dev libbz2-dev
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
tar xvf Python-3.7.3.tar.xz
cd Python-3.7.3
./configure --enable-optimizations
sudo make altinstall
PATH=/usr/local/bin:$PATH
ls -alRF /usr/local/bin
echo "PYTHON -V"
/usr/local/bin/python -V
echo "PYTHON3 -V"
/usr/local/bin/python3 -V
echo "general PYTHON -V"
/usr/local/bin/python -V
python3 -V
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python get-pip.py
pip3 install --upgrade pip
pip3 freeze > requirements.txt
pip3 install --upgrade -r requirements.txt
rm requirements.txt
pip3 install pyinstaller
