#!/bin/sh

mydir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "running from ${mydir}"
credsfile="${gampath}/creds.tar"
echo "target file is ${credsfile}"
gpgfile="${mypath}/creds.tar.gpg"
echo "source file is ${credsfile}"
if [ -z ${PASSCODE+x} ]; then
  echo "PASSCODE is unset";
else
  echo "PASSCODE is set'";
fi

gpg --quiet --batch --yes --decrypt --passphrase="${PASSCODE}" \
    --output "${credsfile}" "${gpgfile}"

tar xf "${credsfile}" --directory "${gampath}"
