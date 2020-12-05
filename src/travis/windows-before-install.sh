if [[ "$PLATFORM" == "x86_64" ]]; then
  export BITS="64"
  export PYTHONFILE_BITS="-amd64"
  export OPENSSL_BITS="-x64"
elif [[ "$PLATFORM" == "x86" ]]; then
  export BITS="32"
  export PYTHONFILE_BITS=""
  export OPENSSL_BITS=""
  export CHOCOPTIONS="--forcex86"
fi
echo "This is a ${BITS}-bit build for ${PLATFORM}"

export mypath=$(pwd)
cd ~

export python="python"
export pip="pip"

# Python
#echo "Installing Python..."
#export python_file=python-${BUILD_PYTHON_VERSION}${PYTHONFILE_BITS}.exe
#if [ ! -e $python_file ]; then
#  echo "Downloading $python_file..."
#  curl -O https://www.python.org/ftp/python/$BUILD_PYTHON_VERSION/$python_file
#fi
#until ./${python_file} /quiet InstallAllUsers=1 TargetDir=c:\\python; do echo "trying python again..."; done
#export python=/c/python/python.exe
#export pip=/c/python/scripts/pip.exe
#until [ -f $python ]; do sleep 1; done
#export PATH=$PATH:/c/python/scripts

# OpenSSL
#echo "Installing OpenSSL..."
#export exefile=Win${BITS}OpenSSL_Light-${BUILD_OPENSSL_VERSION//./_}.exe
#if [ ! -e $exefile ]; then
#  echo "Downloading $exefile..."
#  curl -O https://slproweb.com/download/$exefile
#fi
#until ./${exefile} /silent /sp- /suppressmsgboxes /DIR=C:\\ssl; do echo "trying openssl again..."; done
#until cp -v /c/ssl/libcrypto-1_1${OPENSSL_BITS}.dll /c/python/DLLs/; do echo "trying libcrypto copy again..."; sleep 3; done
#until cp -v /c/ssl/libssl-1_1${OPENSSL_BITS}.dll /c/python/DLLs/; do echo "trying libssl copy again..."; done
#if [[ "$PLATFORM" == "x86_64" ]]; then
#  cp -v /c/python/DLLs/libssl-1_1-x64.dll /c/python/DLLs/libssl-1_1.dll
#  cp -v /c/python/DLLs/libcrypto-1_1-x64.dll /c/python/DLLs/libcrypto-1_1.dll
#fi

cd $mypath

echo "PATH: $PATH"
cd ..
$python setup.py install
echo "cd to $mypath"
cd $mypath
