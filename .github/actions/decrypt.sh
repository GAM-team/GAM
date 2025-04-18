#!/bin/sh
credspath="$1"
if [ ! -d "$credspath" ]; then
    echo "creating ${credspath}"
    mkdir -p "$credspath"
fi
credsfile="${credspath}/oauth2.txt"
echo "$oa2" > "$credsfile"
echo "File size:"
wc -c "$credsfile"
echo "File type:"
file "$credsfile"
echo "Validation:"
jq -e . "$credsfile" > /dev/null
if [ $? -eq 0 ]; then
  echo "Valid JSON"
else
  echo "Invalid JSON"
fi
