#!/usr/bin/env bash

update_profile() {
	[ -f "$1" ] || return 1

	grep -F "$alias_line" "$1" > /dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo -e "\n$alias_line" >> "$1"
	fi
}

case "$(uname -s)" in
  Linux)
    gamos="linux"
    case "$(uname -m)" in
      x86_64) gamfile="linux-x86_64.tar.xz";;
      i386) gamfile="linux-i686.tar.xz";;
      i686) gamfile="linux-i686.tar.xz";;
      arm*) gamfile="linux-armv7l.tar.xz";;
      *) echo "Sorry, this installer currently only supports i386, x86_64 and arm Linux. Exiting."; return;;
    esac
    ;;
  Darwin)
    gamos="macos"
    gamfile="macos.tar.xz"
    ;;
  *)
    echo "Sorry, this installer currently only supports Linux and MacOS. Exiting."
    return
    ;;
esac

if [ "$1" == "prerelease" ]; then
  release_url="https://api.github.com/repos/jay0lee/GAM/releases"
else
  release_url="https://api.github.com/repos/jay0lee/GAM/releases/latest"
fi

echo "Checking GitHub for latest GAM release..."
latest_release_json=$(curl -s $release_url 2>&1 /dev/null)

echo "Getting file and download URL..."
# Python is sadly the nearest to universal way to safely handle JSON with Bash
# At least this code should be compatible with just about any Python version ever
# unlike GAM itself. If some users don't have Python we can try grep / sed / etc
# but that gets really ugly
pycode="import json
import sys
l = json.load(sys.stdin)
if type(l) is list:
  l = l[0]
for i in l['assets']:
  if i[sys.argv[1]].endswith('$gamfile'):
    print i[sys.argv[1]]
    break"
browser_download_url=$(echo "$latest_release_json" | python -c "$pycode" browser_download_url)
name=$(echo "$latest_release_json" | python -c "$pycode" name)
# Temp dir for archive
temp_archive_dir=$(mktemp -d)

echo "Downloading file $name from $browser_download_url to $temp_archive_dir"

# Save archive to temp w/o losing our path
(cd $temp_archive_dir && curl -O -L $browser_download_url)

mkdir -p ~/bin

tar xf $temp_archive_dir/$name -C ~/bin

# Update profile to add gam command
alias_line="alias gam=~/bin/gam/gam"
if [ "$gamos" == "linux" ]; then
  update_profile "$HOME/.bashrc" || update_profile "$HOME/.bash_profile"
elif [ "$gamos" == "macos" ]; then
  update_profile "$HOME/.profile" || update_profile "$HOME/.bash_profile"
fi

echo -e "\n"
while true; do
  read -p "Can you run a full browser on this machine? (usually Y for MacOS, N for Linux if you SSH  into this machine) " yn
  case $yn in
    [Yy]*) break;;
    [Nn]*) touch ~/bin/gam/nobrowser.txt; break;;
    * ) echo "Please answer yes or no.";;
  esac
done

echo -e "\n"

while true; do
  read -p "GAM is now installed. Are you ready to set up a Google API project for GAM? (yes or no) " yn
  case $yn in
    [Yy]*) ~/bin/gam/gam create project; break;;
    [Nn]*) echo -e "\nYou can create an API project later by running:\n\ngam create project"; break;;
    * ) echo "Please answer yes or no.";;
  esac
done

~/bin/gam/gam version

# Clean up after ourselves even if we are killed with CTRL-C
trap "rm -rf $temp_archive_dir" EXIT
