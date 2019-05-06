if [ "$VMTYPE" == "test" ]; then
  export python="python"
  export pip="pip"
  echo "Travis setup Python $TRAVIS_PYTHON_VERSION"
  echo "running tests with this version"
else
  export whereibelong=$(pwd)
  export dist=$(lsb_release --codename --short)
  echo "We are running on Ubuntu $dist"
  echo "RUNNING: apt update..."
  sudo apt-get --yes update > /dev/null
  echo "RUNNING: apt dist-upgrade..."
  sudo apt-get --yes dist-upgrade > /dev/null
  echo "Installing build tools..."
  sudo apt-get --yes install build-essential

  echo "Installing deps for python3"
  sudo cp -v /etc/apt/sources.list /tmp
  chmod a+rwx /tmp/sources.list
  echo "deb-src http://archive.ubuntu.com/ubuntu/ $dist main" >> /tmp/sources.list
  sudo cp -v /tmp/sources.list /etc/apt
  sudo apt-get --yes update > /dev/null
  sudo apt-get --yes build-dep python3

  mypath=$HOME
  echo "My Path is $mypath"
  cpucount=$(nproc --all)
  echo "This device has $cpucount CPUs for compiling..."


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

  if [[ "$dist" == "xenial" ]]; then
    echo "Installing deps for StaticX..."
    sudo apt-get install --yes patchelf scons musl
    $pip install git+https://github.com/JonathonReinhart/staticx.git@master
  fi
  cd $whereibelong
fi

echo "Upgrading pip packages..."
$pip freeze > upgrades.txt
$pip install --upgrade -r upgrades.txt
$pip install -r src/requirements.txt
$pip install pyinstaller
