echo "RUNNING: apt update..."
sudo apt-get --yes update > /dev/null
echo "RUNNING: apt dist-upgrade..."
sudo apt-get --yes dist-upgrade > /dev/null
echo "Installing StaticX deps..."
sudo apt-get --yes install binutils patchelf
echo "Upgrading pip packages..."
pip freeze > upgrades.txt
pip install --upgrade -r upgrades.txt
pip install -r requirements.txt
pip install pyinstaller
pip install staticx
