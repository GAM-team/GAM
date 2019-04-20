echo "RUNNING: apt update..."
sudo apt --yes update > /dev/null
echo "RUNNING: apt dist-upgrade..."
sudo apt --yes dist-upgrade > /dev/null
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
sudo rm requirements.txt
pip install pyinstaller
pip install staticx
