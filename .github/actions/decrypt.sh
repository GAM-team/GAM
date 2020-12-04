#!/bin/sh

credsfile="$1"
echo "target file is ${credsfile}"
gpgfile="$2"
echo "source file is ${gpgfile}"
if [ -z ${PASSCODE+x} ]; then
  echo "PASSCODE is unset";
else
  echo "PASSCODE is set";
fi

gpg --quiet --batch --yes --decrypt --passphrase="${PASSCODE}" \
    --output "${credsfile}" "${gpgfile}"

tar xf "${credsfile}" --directory "${gampath}"
