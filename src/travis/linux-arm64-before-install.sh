export whereibelong=$(pwd)
export dist=$(lsb_release --codename --short)
echo "We are running on Ubuntu $dist"
export LD_LIBRARY_PATH=~/ssl/lib:~/python/lib
cpucount=$(nproc --all)
echo "This device has $cpucount CPUs for compiling..."
SSLVER=$(~/ssl/bin/openssl version)
SSLRESULT=$?
PYVER=$(~/python/bin/python3 -V)
PYRESULT=$?
if [ $SSLRESULT -ne 0 ] || [[ "$SSLVER" != "OpenSSL $BUILD_OPENSSL_VERSION "* ]] || [ $PYRESULT -ne 0 ] || [[ "$PYVER" != "Python $PYTHON_BUILD_VERSION"* ]]; then
  echo "RUNNING: apt update..."
  sudo apt-get -qq --yes update > /dev/null
  echo "RUNNING: apt dist-upgrade..."
  sudo apt-get -qq --yes dist-upgrade > /dev/null
  echo "Installing build tools..."
  sudo apt-get -qq --yes install build-essential

  echo "Installing deps for python3"
  sudo cp -v /etc/apt/sources.list /tmp
  sudo chmod a+rwx /tmp/sources.list
  echo "deb-src http://archive.ubuntu.com/ubuntu/ $dist main" >> /tmp/sources.list
  sudo cp -v /tmp/sources.list /etc/apt
  sudo apt-get -qq --yes update > /dev/null
  sudo apt-get -qq --yes build-dep python3 > /dev/null
  sudo apt-get -qq --yes install zlib1g-dev > /dev/null
  sudo apt-get -qq --yes install libffi-dev > /dev/null

  # Compile latest OpenSSL
  echo "Downloading OpenSSL..."
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
  echo "running configure with safe and unsafe"
  ./configure $safe_flags $unsafe_flags > /dev/null
  make -j$cpucount PROFILE_TASK="-m test.regrtest --pgo -j$(( $cpucount * 2 ))" -s
  echo "Installing Python..."
  make install > /dev/null
fi

python=~/python/bin/python3
pip=~/python/bin/pip3

$python -V

cd $whereibelong

echo "Upgrading pip packages..."
$pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 $pip install -U
$pip install --upgrade -r src/requirements.txt
$pip install --upgrade https://github.com/pyinstaller/pyinstaller/archive/develop.tar.gz

mkdir ~/.ruby
export GEM_HOME=~/.ruby
export PATH=$PATH:~/.ruby/bin
