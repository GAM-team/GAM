echo "RUNNING: apt update..."
sudo apt-get --yes update > /dev/null
echo "RUNNING: apt dist-upgrade..."
sudo apt-get --yes dist-upgrade > /dev/null
echo "Installing build tools..."
sudo apt-get --yes install build-essential
echo "Installing StaticX deps..."
sudo apt-get --yes install binutils patchelf

mypath=$HOME
# Compile latest OpenSSL
OPENSSL_VER=1.1.1b
wget https://www.openssl.org/source/openssl-$OPENSSL_VER.tar.gz
tar xf openssl-$OPENSSL_VER.tar.gz
cd openssl-$OPENSSL_VER
./config shared --prefix=$mypath/ssl
make
make install
cd ~

# Compile latest Python
PYTHON_VER=3.7.3
wget https://www.python.org/ftp/python/$PYTHON_VER/Python-$PYTHON_VER.tar.xz
tar xf Python-$PYTHON_VER.tar.xz
cd Python-$PYTHON_VER
./configure --with-openssl=$mypath/ssl --enable-optimizations --enable-shared \
	--prefix=$mypath/python --with-ensurepip=upgrade
make
make install
cd ~

export LD_LIBRARY_PATH=~/ssl/lib:~/python/lib
$python=~/python/bin/python3
$pip=~/python/bin/pip3

$python -V
ls -al ~/python/bin

echo "Upgrading pip packages..."
$pip freeze > upgrades.txt
$pip install --upgrade -r upgrades.txt
$pip install -r src/requirements.txt
$pip install pyinstaller
$pip install staticx
