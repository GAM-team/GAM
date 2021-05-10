#!/bin/sh

gpgfile="$1"
echo "source file is ${gpgfile}"
credsfile="$2"
echo "target file is ${credsfile}"
if [ -z ${PASSCODE+x} ]; then
  echo "PASSCODE is unset";
else
  echo "PASSCODE is set";
fi

gpg --quiet --batch --yes --decrypt --passphrase="${PASSCODE}" \
    --output "${credsfile}" "${gpgfile}"

tar xvvf "${credsfile}" --directory "${gampath}"
ls -l "${gampath}"
