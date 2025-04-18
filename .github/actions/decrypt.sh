#!/bin/sh
credspath="$1"
if [ ! -d "$credspath" ]; then
    echo "creating ${credspath}"
    mkdir -p "$credspath"
fi

echo -e "$oa2" > "${credspath}/oauth2.txt"
