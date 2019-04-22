#!/usr/bin/env bash

mypath=$(readlink -e $0)
export GAM_REAL_PATH=$(dirname $mypath)
staticx_binary="$mypath-staticx"
"$staticx_binary" "$@"
