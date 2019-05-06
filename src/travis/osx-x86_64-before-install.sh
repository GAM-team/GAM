mypath=$HOME
whereibelong=$(pwd)
echo "Brew installing xz..."
brew install xz > /dev/null

# Compile latest OpenSSL
OPENSSL_VER=1.1.1b
wget https://www.openssl.org/source/openssl-$OPENSSL_VER.tar.gz
echo "Extracting OpenSSL..."
tar xf openssl-$OPENSSL_VER.tar.gz
cd openssl-$OPENSSL_VER
echo "Compiling OpenSSL $OPENSSL_VER..."
./config shared --prefix=$mypath/ssl
echo "Running make for OpenSSL..."
make -j$cpucount -s
echo "Running make install for OpenSSL..."
make install > /dev/null
export LD_LIBRARY_PATH=~/ssl/lib
cd ~

# Compile latest Python
PYTHON_VER=3.7.3
wget https://www.python.org/ftp/python/$PYTHON_VER/Python-$PYTHON_VER.tar.xz
echo "Extracting Python..."
tar xf Python-$PYTHON_VER.tar.xz
cd Python-$PYTHON_VER
echo "Compiling Python $PYTHON_VER..."
./configure --with-openssl=$mypath/ssl --enable-shared \
		--prefix=$mypath/python --with-ensurepip=upgrade > /dev/null
make -j$cpucount -s
echo "Installing Python..."
make install > /dev/null
cd ~

export LD_LIBRARY_PATH=~/ssl/lib:~/python/lib
python=~/python/bin/python3
pip=~/python/bin/pip3

$python -V

cd $whereibelong

export PATH=/usr/local/opt/python/libexec/bin:$PATH
$pip install --upgrade pip
$pip freeze > upgrades.txt
$pip install --upgrade -r upgrades.txt
$pip install -r src/requirements.txt
$pip install pyinstaller
