sudo apt update
sudo apt -y dist-upgrade
sudo sh -c "echo 'foreign-architecture i386' > /etc/dpkg/dpkg.cfg.d/multiarch"
sudo apt update
sudo apt install -y python:i386 python2.7:i386 python2.7-minimal:i386 mime-support:i386
python -V
sudo pip install --upgrade pip
sudo pip freeze > requirements.txt
sudo pip install --upgrade -r requirements.txt
sudo rm requirements.txt
sudo pip install pyinstaller
