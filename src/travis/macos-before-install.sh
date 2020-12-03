mypath=$HOME
whereibelong=$(pwd)
cpucount=$(sysctl -n hw.ncpu)
echo "This device has $cpucount CPUs for compiling..."

#echo "Brew installing xz..."
#brew install xz > /dev/null

#brew upgrade

# prefer standard GNU tools like date over MacOS defaults
export PATH="/usr/local/opt/coreutils/libexec/gnubin:$(brew --prefix)/opt/gnu-tar/libexec/gnubin:$PATH"

cd ~

#if [ ! -f python-$MIN_PYTHON_VERSION-macosx10.9.pkg ]; then
#  wget --quiet https://www.python.org/ftp/python/$MIN_PYTHON_VERSION/python-$MIN_PYTHON_VERSION-macosx10.9.pkg
#fi
#sudo installer -pkg python-$MIN_PYTHON_VERSION-macosx10.9.pkg -target /

#brew install openssl@1.1
#brew upgrade python

#export python=python3
#export pip=pip3

#echo "Python location:"
#which $python

cd ~

export LD_LIBRARY_PATH=~/ssl/lib:~/python/lib
export openssl=~/ssl/bin/openssl
export python=~/python/bin/python3
export pip=~/python/bin/pip3
SSLVER=$($openssl version)
SSLRESULT=$?
PYVER=$($python -V)
PYRESULT=$?
if [ $SSLRESULT -ne 0 ] || [[ "$SSLVER" != "OpenSSL $BUILD_OPENSSL_VERSION "* ]] || [ $PYRESULT -ne 0 ] || [[ "$PYVER" != "Python $BUILD_PYTHON_VERSION"* ]]; then
  echo "SSL Result: $SSLRESULT - SSL Ver: $SSLVER - Py Result: $PYRESULT - Py Ver: $PYVER"
  if [ $SSLRESULT -ne 0 ]; then
    echo "sslresult -ne 0"
  fi
  if [[ "$SSLVER" != "OpenSSL $BUILD_OPENSSL_VERSION "* ]]; then
    echo "sslver not equal to..."
  fi
  if [ $PYRESULT -ne 0 ]; then
    echo "pyresult -ne 0"
  fi
  if [[ "$PYVER" != "Python $BUILD_PYTHON_VERSION" ]]; then
    echo "pyver not equal to..."
  fi

  # Start clean
  rm -rf python
  rm -rf ssl
  mkdir python
  mkdir ssl

  # Compile latest OpenSSL
  wget --quiet https://www.openssl.org/source/openssl-$BUILD_OPENSSL_VERSION.tar.gz
  echo "Extracting OpenSSL..."
  tar xf openssl-$BUILD_OPENSSL_VERSION.tar.gz
  cd openssl-$BUILD_OPENSSL_VERSION
  echo "Compiling OpenSSL $BUILD_OPENSSL_VERSION..."
  ./config shared --prefix=$HOME/ssl
  echo "Running make for OpenSSL..."
  make -j$cpucount -s
  echo "Running make install for OpenSSL..."
  make install > /dev/null
  cd ~

  # Compile latest Python
  echo "Downloading Python $BUILD_PYTHON_VERSION..."
  curl -O https://www.python.org/ftp/python/$BUILD_PYTHON_VERSION/Python-$BUILD_PYTHON_VERSION.tar.xz
  echo "Extracting Python..."
  tar xf Python-$BUILD_PYTHON_VERSION.tar.xz
  cd Python-$BUILD_PYTHON_VERSION
  echo "Compiling Python $BUILD_PYTHON_VERSION..."
  safe_flags="--with-openssl=$HOME/ssl --enable-shared --prefix=$HOME/python --with-ensurepip=upgrade"
  unsafe_flags="--enable-optimizations --with-lto"
  if [ ! -e Makefile ]; then
    echo "running configure with safe and unsafe"
    ./configure $safe_flags $unsafe_flags > /dev/null
  fi
  make -j$cpucount PROFILE_TASK="-m test.regrtest --pgo -j$(( $cpucount * 2 ))" -s
  RESULT=$?
  echo "First make exited with $RESULT"
  if [ $RESULT != 0 ]; then
    echo "Trying Python compile again without unsafe flags..."
    make clean
    ./configure $safe_flags > /dev/null
    make -j$cpucount -s
    echo "Sticking with safe Python for now..."
  fi
  echo "Installing Python..."
  make install > /dev/null
  cd ~
fi

$python -V

cd $whereibelong

#export PATH=/usr/local/opt/python/libexec/bin:$PATH
$pip install --upgrade pip
$pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 $pip install -U
$pip install --upgrade -r requirements.txt
$pip install --upgrade git+git://github.com/pyinstaller/pyinstaller.git@$PYINSTALLER_COMMIT
 
