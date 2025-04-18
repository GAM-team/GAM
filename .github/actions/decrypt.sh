#!/bin/sh
credspath="$1"
if [ ! -d "$credspath" ]; then
    echo "creating ${credspath}"
    mkdir -p "$credspath"
fi

secretvar="GAM_GHA_${JID}"
secretval="${!secretvar}"

echo -e "$secretval" > "${credspath}/oauth2.txt"
