sudo sh -c "echo 'foreign-architecture i386' > /etc/dpkg/dpkg.cfg.d/multiarch"
apt update
apt install -y python:i386
python -V
pip install --upgrade pip
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
rm requirements.txt
pip install pyinstaller
