echo "RUNNING: apt update..."
sudo apt-get --yes update > /dev/null
echo "RUNNING: apt dist-upgrade..."
sudo apt-get --yes dist-upgrade > /dev/null
echo "Installing StaticX deps..."
sudo apt-get --yes install binutils patchelf
echo "Upgrading pip packages..."
pip freeze > requirements.txt
pip install --upgrade -r requirements.txt
sudo rm requirements.txt
pip install pyinstaller
pip install staticx
