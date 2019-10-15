mypath=$HOME
whereibelong=$(pwd)
#echo "Brew installing xz..."
#brew install xz > /dev/null

#brew upgrade

cd ~

if [ ! -f python-$BUILD_PYTHON_VERSION-macosx10.9.pkg ]; then
  wget --quiet https://www.python.org/ftp/python/$BUILD_PYTHON_VERSION/python-$BUILD_PYTHON_VERSION-macosx10.9.pkg
fi
sudo installer -pkg python-$BUILD_PYTHON_VERSION-macosx10.9.pkg -target /

#brew install openssl@1.1
#brew upgrade python

export python=python3
export pip=pip3

echo "Python location:"
which $python

# Compile latest OpenSSL
#if [ ! -d openssl-$BUILD_OPENSSL_VERSION ]; then
#  wget --quiet https://www.openssl.org/source/openssl-$BUILD_OPENSSL_VERSION.tar.gz
#  echo "Extracting OpenSSL..."
#  tar xf openssl-$BUILD_OPENSSL_VERSION.tar.gz
#fi
#cd openssl-$BUILD_OPENSSL_VERSION
#echo "Compiling OpenSSL $BUILD_OPENSSL_VERSION..."
#./config shared --prefix=$mypath/ssl
#echo "Running make for OpenSSL..."
#make -j$cpucount -s
#echo "Running make install for OpenSSL..."
#make install > /dev/null
#export LD_LIBRARY_PATH=~/ssl/lib
#cd ~

# Compile latest Python
#if [ ! -d Python-$BUILD_PYTHON_VERSION ]; then
#  wget --quiet https://www.python.org/ftp/python/$BUILD_PYTHON_VERSION/Python-$BUILD_PYTHON_VERSION.tar.xz
#  echo "Extracting Python..."
#  tar xf Python-$BUILD_PYTHON_VERSION.tar.xz
#fi
#cd Python-$BUILD_PYTHON_VERSION
#echo "Compiling Python $BUILD_PYTHON_VERSION..."
#safe_flags="--with-openssl=$mypath/ssl --enable-shared --prefix=$mypath/python --with-ensurepip=upgrade"
#unsafe_flags="--enable-optimizations --with-lto"
#if [ ! -e Makefile ]; then
#  ./configure $safe_flags $unsafe_flags > /dev/null
#fi
#make -j$cpucount -s
#RESULT=$?
#echo "Make Python exited with $RESULT"
#if [ $RESULT != 0 ]; then
#  echo "Trying Python make again without unsafe flags..."
#  make clean
#  ./configure $safe_flags > /dev/null
#  make -j$cpucount -s
#fi
#echo "Installing Python..."
#make install > /dev/null
#cd ~

#export LD_LIBRARY_PATH=~/ssl/lib:~/python/lib
#python=~/python/bin/python3
#pip=~/python/bin/pip3

$python -V

cd $whereibelong

export PATH=/usr/local/opt/python/libexec/bin:$PATH
$pip install --upgrade pip
$pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 $pip install -U
$pip install --upgrade -r src/requirements.txt
$pip install --upgrade https://github.com/pyinstaller/pyinstaller/archive/develop.tar.gz 
