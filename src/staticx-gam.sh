#!/usr/bin/env bash

mypath=$(realpath $0)
export GAM_REAL_PATH=$(dirname $mypath)
staticx_binary="$mypath-staticx"
"$staticx_binary" "$@"
