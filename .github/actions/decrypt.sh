#!/bin/sh
credspath="$3"
if [ ! -d "$credspath" ]; then
    echo "creating ${credspath}"
    mkdir -p "$credspath"
fi
gpgfile="$1"
if [ -f "$gpgfile" ]; then
    echo "source file is ${gpgfile}"
else
    echo "ERROR: ${gpgfile} does not exist"
    exit 1
fi
credsfile="$2"
echo "target file is ${credsfile}"
if [ -z ${PASSCODE+x} ]; then
  echo "ERROR: PASSCODE is unset";
  exit 2
else
  echo "PASSCODE is set";
fi

gpg --batch \
    --yes \
    --decrypt \
    --passphrase="$PASSCODE" \
    --output "$credsfile" \
    "$gpgfile"

if [[ "$RUNNER_OS" == "macOS" ]]; then
  tar="gtar"
else
  tar="tar"
fi

"$tar" xlvvf "$credsfile" --directory "$credspath"
rm -rvf "$gpgfile"
rm -rvf "$credsfile"
