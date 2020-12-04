#!/bin/sh

mydir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

credsfile="${gampath}/creds.tar"
gpg --quiet --batch --yes --decrypt --passphrase="${PASSPHRASE}" \
    --output "${credsfile}" "${mydir}/creds.tar.gpg"

tar xf "${credsfile}" --directory "${gampath}"
