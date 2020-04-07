#!/usr/bin/env bash

usage()
{
cat << EOF
GAM installation script.

OPTIONS:
   -h      show help.
   -d      Directory where gam folder will be installed. Default is \$HOME/bin/
   -a      Architecture to install (i386, x86_64, x86_64_legacy, arm, arm64). Default is to detect your arch with "uname -m".
   -o      OS we are running (linux, macos). Default is to detect your OS with "uname -s".
   -b      OS version. Default is to detect on MacOS and Linux.
   -l      Just upgrade GAM to latest version. Skips project creation and auth.
   -p      Profile update (true, false). Should script add gam command to environment. Default is true.
   -u      Admin user email address to use with GAM. Default is to prompt.
   -r      Regular user email address. Used to test service account access to user data. Default is to prompt.
   -v      Version to install (latest, prerelease, draft, 3.8, etc). Default is latest.
EOF
}

target_dir="$HOME/bin"
gamarch=$(uname -m)
gamos=$(uname -s)
osversion=""
update_profile=true
upgrade_only=false
gamversion="latest"
adminuser=""
regularuser=""
gam_glibc_vers="2.27 2.23"
gam_macos_vers="10.14.6 10.13.6"

while getopts "hd:a:o:b:lp:u:r:v:" OPTION
do
     case $OPTION in
         h) usage; exit;;
         d) target_dir="$OPTARG";;
         a) gamarch="$OPTARG";;
         o) gamos="$OPTARG";;
         b) osversion="$OPTARG";;
         l) upgrade_only=true;;
         p) update_profile="$OPTARG";;
         u) adminuser="$OPTARG";;
         r) regularuser="$OPTARG";;
         v) gamversion="$OPTARG";;
         ?) usage; exit;;
     esac
done

# remove possible / from end of target_dir
target_dir=${target_dir%/}

update_profile() {
	[ $2 -eq 1 ] || [ -f "$1" ] || return 1

	grep -F "$alias_line" "$1" > /dev/null 2>&1
	if [ $? -ne 0 ]; then
                echo_yellow "Adding gam alias to profile file $1."
		echo -e "\n$alias_line" >> "$1"
        else
          echo_yellow "gam alias already exists in profile file $1. Skipping add."
	fi
}

echo_red()
{
echo -e "\x1B[1;31m$1"
echo -e '\x1B[0m'
}

echo_green()
{
echo -e "\x1B[1;32m$1"
echo -e '\x1B[0m'
}

echo_yellow()
{
echo -e "\x1B[1;33m$1"
echo -e '\x1B[0m'
}

version_gt()
{
# MacOS < 10.13 doesn't support sort -V
echo "" | sort -V > /dev/null 2>&1
vsort_failed=$?
if [ "${1}" = "${2}" ]; then
  true
elif (( $vsort_failed != 0 )); then
  false
else
  test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
fi
}

case $gamos in
  [lL]inux)
    gamos="linux"
    if [ "$osversion" == "" ]; then
      this_glibc_ver=$(ldd --version | awk '/ldd/{print $NF}')
    else
      this_glibc_ver=$osversion
    fi
    echo "This Linux distribution uses glibc $this_glibc_ver"
    useglibc="legacy"
    for gam_glibc_ver in $gam_glibc_vers; do
      if version_gt $this_glibc_ver $gam_glibc_ver; then
        useglibc="glibc$gam_glibc_ver"
        echo_green "Using GAM compiled against $useglibc"
        break
      fi
    done
    case $gamarch in
      x86_64) gamfile="linux-x86_64-$useglibc.tar.xz";;
      arm64|aarch64) gamfile="linux-arm64-$useglibc.tar.xz";;
      *)
        echo_red "ERROR: this installer currently only supports x86_64 and arm64 Linux. Looks like you're running on $gamarch. Exiting."
        exit
    esac
    ;;
  [Mm]ac[Oo][sS]|[Dd]arwin)
    gamos="macos"
    if [ "$osversion" == "" ]; then
      this_macos_ver=$(sw_vers -productVersion)
    else
      this_macos_ver=$osversion
    fi
    echo "You are running MacOS $this_macos_ver"
    use_macos_ver=""
    for gam_macos_ver in $gam_macos_vers; do
      if version_gt $this_macos_ver $gam_macos_ver; then
        use_macos_ver="MacOS$gam_macos_ver"
        echo_green "Using GAM compiled on $use_macos_ver"
        break
      fi
    done
    if [ "$use_macos_ver" == "" ]; then
      echo_red "Sorry, you need to be running at least MacOS $gam_macos_ver to run GAM"
      exit
    fi
    gamfile="macos-x86_64-$use_macos_ver.tar.xz"
    ;;
  *)
    echo_red "Sorry, this installer currently only supports Linux and MacOS. Looks like you're runnning on $gamos. Exiting."
    exit
    ;;
esac

if [ "$gamversion" == "latest" -o "$gamversion" == "prerelease" -o "$gamversion" == "draft" ]; then
  release_url="https://api.github.com/repos/jay0lee/GAM/releases"
else
  release_url="https://api.github.com/repos/jay0lee/GAM/releases/tags/v$gamversion"
fi

echo_yellow "Checking GitHub URL $release_url for $gamversion GAM release..."
release_json=$(curl -s $release_url 2>&1 /dev/null)

echo_yellow "Getting file and download URL..."
# Python is sadly the nearest to universal way to safely handle JSON with Bash
# At least this code should be compatible with just about any Python version ever
# unlike GAM itself. If some users don't have Python we can try grep / sed / etc
# but that gets really ugly
pycode="import json
import sys

attrib = sys.argv[1]
gamversion = sys.argv[2]

release = json.load(sys.stdin)
if type(release) is list:
  for a_release in release:
    if a_release['prerelease'] and gamversion != 'prerelease':
      continue
    elif a_release['draft'] and gamversion != 'draft':
      continue
    release = a_release
    break
try:
  for asset in release['assets']:
    if asset[attrib].endswith('$gamfile'):
      print(asset[attrib])
      break
  else:
    print('ERROR: Attribute: {0} for $gamfile version {1} not found'.format(attrib, gamversion))
except KeyError:
  print('ERROR: assets value not found in JSON value of:\n\n%s' % release)"

pycmd="python3"
$pycmd -V >/dev/null 2>&1
rc=$?
if (( $rc != 0 )); then
  pycmd="python"
fi
$pycmd -V >/dev/null 2>&1
rc=$?
if (( $rc != 0 )); then
  pycmd="python2"
fi
$pycmd -V >/dev/null 2>&1
rc=$?
if (( $rc != 0 )); then
  echo_red "ERROR: No version of python installed."
  exit
fi

browser_download_url=$(echo "$release_json" | $pycmd -c "$pycode" browser_download_url $gamversion)
if [[ ${browser_download_url:0:5} = "ERROR" ]]; then
  echo_red "${browser_download_url}"
  exit
fi
name=$(echo "$release_json" | $pycmd -c "$pycode" name $gamversion)
if [[ ${name:0:5} = "ERROR" ]]; then
  echo_red "${name}"
  exit
fi
# Temp dir for archive
#temp_archive_dir=$(mktemp -d)
temp_archive_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
echo_yellow "Downloading file $name from $browser_download_url to $temp_archive_dir."
# Save archive to temp w/o losing our path
(cd $temp_archive_dir && curl -O -L $browser_download_url)

mkdir -p "$target_dir"

echo_yellow "Extracting archive to $target_dir"
tar xf $temp_archive_dir/$name -C "$target_dir"
rc=$?
if (( $rc != 0 )); then
  echo_red "ERROR: extracting the GAM archive with tar failed with error $rc. Exiting."
  exit
else
  echo_green "Finished extracting GAM archive."
fi

# Update profile to add gam command
if [ "$update_profile" = true ]; then
  alias_line="gam() { \"$target_dir/gam/gam\" \"\$@\" ; }"
  if [ "$gamos" == "linux" ]; then
    update_profile "$HOME/.bash_aliases" 0 || update_profile "$HOME/.bash_profile" 0 || update_profile "$HOME/.bashrc" 0
    update_profile "$HOME/.zshrc" 0
  elif [ "$gamos" == "macos" ]; then
    update_profile "$HOME/.bash_aliases" 0 || update_profile "$HOME/.bash_profile" 0 || update_profile "$HOME/.bashrc" 0 || update_profile "$HOME/.profile" 1
    update_profile "$HOME/.zshrc" 0
  fi
else
  echo_yellow "skipping profile update."
fi

if [ "$upgrade_only" = true ]; then
  echo_green "Here's information about your GAM upgrade:"
  "$target_dir/gam/gam" version extended
  rc=$?
  if (( $rc != 0 )); then
    echo_red "ERROR: Failed running GAM for the first time with $rc. Please report this error to GAM mailing list. Exiting."
    exit
  fi

  echo_green "GAM upgrade complete!"
  exit
fi

while true; do
  read -p "Can you run a full browser on this machine? (usually Y for MacOS, N for Linux if you SSH into this machine) " yn
  case $yn in
    [Yy]*)
      break
      ;;
    [Nn]*)
      touch "$target_dir/gam/nobrowser.txt" > /dev/null 2>&1
      break
      ;;
    *)
      echo_red "Please answer yes or no."
      ;;
  esac
done
echo

project_created=false
while true; do
  read -p "GAM is now installed. Are you ready to set up a Google API project for GAM? (yes or no) " yn
  case $yn in
    [Yy]*)
      if [ "$adminuser" == "" ]; then
        read -p "Please enter your G Suite admin email address: " adminuser
      fi
      "$target_dir/gam/gam" create project $adminuser
      rc=$?
      if (( $rc == 0 )); then
        echo_green "Project creation complete."
        project_created=true
        break
      else
        echo_red "Project creation failed. Trying again. Say N to skip project creation."
      fi
      ;;
    [Nn]*)
      echo -e "\nYou can create an API project later by running:\n\ngam create project\n"
      break
      ;;
    *)
      echo_red "Please answer yes or no."
      ;;
  esac
done

admin_authorized=false
while $project_created; do
  read -p "Are you ready to authorize GAM to perform G Suite management operations as your admin account? (yes or no) " yn
  case $yn in
    [Yy]*)
      "$target_dir/gam/gam" oauth create $adminuser
      rc=$?
      if (( $rc == 0 )); then
        echo_green "Admin authorization complete."
        admin_authorized=true
        break
      else
        echo_red "Admin authorization failed. Trying again. Say N to skip admin authorization."
      fi
      ;;
     [Nn]*)
       echo -e "\nYou can authorize an admin later by running:\n\ngam oauth create\n"
       break
       ;;
     *)
       echo_red "Please answer yes or no."
       ;;
  esac
done

service_account_authorized=false
while $project_created; do
  read -p "Are you ready to authorize GAM to manage G Suite user data and settings? (yes or no) " yn
  case $yn in
    [Yy]*)
      if [ "$regularuser" == "" ]; then
        read -p "Please enter the email address of a regular G Suite user: " regularuser
      fi
      echo_yellow "Great! Checking service account scopes.This will fail the first time. Follow the steps to authorize and retry. It can take a few minutes for scopes to PASS after they've been authorized in the admin console."
      "$target_dir/gam/gam" user $adminuser check serviceaccount
      rc=$?
      if (( $rc == 0 )); then
        echo_green "Service account authorization complete."
        service_account_authorized=true
        break
      else
        echo_red "Service account authorization failed. Confirm you entered the scopes correctly in the admin console. It can take a few minutes for scopes to PASS after they are entered in the admin console so if you're sure you entered them correctly, go grab a coffee and then hit Y to try again. Say N to skip admin authorization."
      fi
      ;;
     [Nn]*)
       echo -e "\nYou can authorize a service account later by running:\n\ngam check serviceaccount\n"
       break
       ;;
     *)
       echo_red "Please answer yes or no."
       ;;
  esac
done

echo_green "Here's information about your new GAM installation:"
"$target_dir/gam/gam" version extended
rc=$?
if (( $rc != 0 )); then
  echo_red "ERROR: Failed running GAM for the first time with $rc. Please report this error to GAM mailing list. Exiting."
  exit
fi

echo_green "GAM installation and setup complete!"
if [ "$update_profile" = true ]; then
  echo_green "Please restart your terminal shell or to get started right away run:\n\n$alias_line"
fi

# Clean up after ourselves even if we are killed with CTRL-C
trap "rm -rf $temp_archive_dir" EXIT
