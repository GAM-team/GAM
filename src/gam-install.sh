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
   -s      Strip gam component from extracted files, files will be downloaded directly to $target_dir
EOF
}

target_dir="$HOME/bin"
target_folder="$target_dir/gam7"
gamarch=$(uname -m)
gamos=$(uname -s)
osversion=""
update_profile=true
upgrade_only=false
gamversion="latest"
adminuser=""
regularuser=""
strip_gam="--strip-components 0"

while getopts "hd:a:o:b:lp:u:r:v:s" OPTION
do
     case $OPTION in
         h) usage; exit;;
         d) target_dir="${OPTARG%/}"; target_folder="$target_dir/gam7";;
         a) gamarch="$OPTARG";;
         o) gamos="$OPTARG";;
         b) osversion="$OPTARG";;
         l) upgrade_only=true;;
         p) update_profile="$OPTARG";;
         u) adminuser="$OPTARG";;
         r) regularuser="$OPTARG";;
         v) gamversion="$OPTARG";;
         s) strip_gam="--strip-components 1"; target_folder="$target_dir";;
         ?) usage; exit;;
     esac
done
target_gam="$target_folder/gam"

update_profile() {
        [ "$2" -eq 1 ] || [ -f "$1" ] || return 1

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

if [ "$gamversion" == "latest" ]; then
  release_url="https://api.github.com/repos/GAM-team/GAM/releases/latest"
elif [ "$gamversion" == "prerelease" -o "$gamversion" == "draft" ]; then
  release_url="https://api.github.com/repos/GAM-team/GAM/releases"
else
  release_url="https://api.github.com/repos/GAM-team/GAM/releases/tags/v$gamversion"
fi

if [ -z ${GHCLIENT+x} ]; then
  check_type="unauthenticated"
  curl_opts=( )
else
  check_type="authenticated"
  curl_opts=( "$GHCLIENT" )
fi
curl_ver=$(curl --version|head -1|cut -d " " -f 2)
if [[ "${curl_ver:0:4}" < "7.76" ]]; then
  curl_fail=( )
else
  curl_fail=( "--fail-with-body" )
fi
echo_yellow "Checking GitHub URL $release_url for $gamversion GAM release ($check_type)..."
release_json=$(curl \
	--silent \
	"${curl_opts[@]}" \
	-H "Accept: application/vnd.github+json" \
	-H "X-GitHub-Api-Version: 2022-11-28" \
	"$release_url" \
	"${curl_fail[@]}")
curl_exit_code=$?
if [ $curl_exit_code -ne 0 ]; then
  echo_red "ERROR retrieving URL: ${release_json}"
  exit
else
  echo_green "done"
fi

echo_yellow "Calculating download URL for this device..."
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
    print(asset[attrib])
  #else:
  #  print('ERROR: Attribute: {0} for version {1} not found'.format(attrib, gamversion))
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
  pycmd="/usr/bin/python3"
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
# also sort the URLs once so we're evaluating newest OS version first
download_urls=$(echo "$release_json" | \
	        $pycmd -c "$pycode" browser_download_url "$gamversion" | \
	        sort --version-sort --reverse)
if [[ ${download_urls:0:5} = "ERROR" ]]; then
  echo_red "${download_urls}"
  exit
fi

case $gamos in
  [lL]inux)
    gamos="linux"
    download_urls=$(echo -e "$download_urls" | grep "\-linux-")
    if [ "$osversion" == "" ]; then
      this_glibc_ver=$(ldd --version | awk '/ldd/{print $NF}')
    else
      this_glibc_ver=$osversion
    fi
    echo "This Linux distribution uses glibc $this_glibc_ver"
    case $gamarch in
      x86_64)
	download_urls=$(echo -e "$download_urls" | grep "\-x86_64-")
	gam_x86_64_glibc_vers=$(echo -e "$download_urls" | \
		grep --only-matching 'glibc[0-9\.]*\.tar\.xz$' \
	        | cut -c 6-9 )
	useglibc="legacy"
        for gam_glibc_ver in $gam_x86_64_glibc_vers; do
	  if version_gt $this_glibc_ver $gam_glibc_ver; then
            useglibc="glibc$gam_glibc_ver"
            echo_green "Using GAM compiled against $useglibc"
            break
          fi
        done
        download_url=$(echo -e "$download_urls" | grep "$useglibc")
	;;
      arm|arm64|aarch64)
        download_urls=$(echo -e "$download_urls" | grep "\-aarch64-")
        gam_arm64_glibc_vers=$(echo -e "$download_urls" | \
                grep --only-matching 'glibc[0-9\.]*\.tar\.xz$' | \
                cut -c 6-9)
        useglibc="legacy"
        for gam_glibc_ver in $gam_arm64_glibc_vers; do
          if version_gt $this_glibc_ver $gam_glibc_ver; then
            useglibc="glibc$gam_glibc_ver"
            echo_green "Using GAM compiled against $useglibc"
            break
          fi
        done
        download_url=$(echo -e "$download_urls" | grep "$useglibc")
	;;
      *)
        echo_red "ERROR: this installer currently only supports x86_64 and arm64 Linux. Looks like you're running on $gamarch. Exiting."
        exit
    esac
    ;;
  [Mm]ac[Oo][sS]|[Dd]arwin)
    gamos="macos"
    currentversion=$(sw_vers -productVersion | awk -F '.' '{print $1 "." $2}')
    # override osversion only if it wasn't set by cli arguments
    osversion=${osversion:-${currentversion}}
    # override osversion only if it wasn't set by cli arguments
    download_urls=$(echo -e "$download_urls" | grep "\-macos")
    case $gamarch in
      x86_64)
        archgrep="\-x86_64"
	;;
      arm|arm64|aarch64)
        archgrep="\-aarch64"
        ;;
      *)
        echo_red "ERROR: this installer currently only supports x86_64 and arm64 MacOS. Looks like you're running on ${gamarch}. Exiting."
        exit
	;;
    esac
    gam_macos_urls=$(echo -e "$download_urls" | \
                     grep "$archgrep")
    versionless_urls=$(echo -e "$gam_macos_urls" | \
                       grep "\-macos-")
    if [ "$versionless_urls" == "" ]; then
        # versions after 7.00.38 include MacOS version info
        gam_macos_vers=$(echo -e "$gam_macos_urls" | \
                         grep --only-matching '\-macos[0-9\.]*' | \
                         cut -c 7-10)
        for gam_mac_ver in $gam_macos_vers; do
            if version_gt $currentversion $gam_mac_ver; then
                download_url=$(echo -e "$gam_macos_urls" | grep "$gam_mac_ver")
                echo_green "You are running MacOS ${currentversion} Using GAM compiled against ${gam_mac_ver}"
                break
            fi
            done
        if [ -z ${download_url+x} ]; then
	    echo_red "Sorry, you are running MacOS ${osversion} but GAM on ${gamarch} requires MacOS ${gam_mac_ver} or newer. Exiting."
            exit
	fi
    else
        # versions 7.00.38 and older don't include version info
        case $gamarch in
            x86_64)
	        minimum_version=13
                download_url=$(echo -e "$download_urls" | grep "\-x86_64")
                ;;
            arm|arm64|aarch64)
                download_url=$(echo -e "$download_urls" | grep "\-aarch64")
	        minimum_version=14
                ;;
        esac
        if version_gt "$osversion" "$minimum_version"; then
            echo_green "You are running MacOS ${osversion}, good. Downloading GAM from ${download_url}."
        else
          echo_red "Sorry, you are running MacOS ${osversion} but GAM on ${gamarch} requires MacOS ${minimum_version}. Exiting."
          exit
        fi 
        if [ -z ${download_url+x} ]; then
          echo_red "Sorry, you are running MacOS ${currentversion} but GAM on ${gamarch} requires MacOS ${minimum_version}. Exiting."
          exit
        fi
    fi
    ;;
  MINGW64_NT*)
    gamos="windows"
    echo "You are running Windows"
    download_url=$(echo -e "$download_urls" | \
                   grep "\-windows-" | \
                   grep ".zip")
    ;;
  *)
    echo_red "Sorry, this installer currently only supports Linux and MacOS. Looks like you're running on ${gamos}. Exiting."
    exit
    ;;
esac

# Temp dir for archive
temp_archive_dir=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')

# Clean up after ourselves even if we are killed with CTRL-C
trap "rm -rf $temp_archive_dir" EXIT

# hack to grab the end of the URL which should be the filename.
name=$(echo -e "$download_url" | rev | cut -f1 -d "/" | rev)

echo_yellow "Downloading ${download_url} to $temp_archive_dir ($check_type)..."
# Save archive to temp w/o losing our path
(cd "$temp_archive_dir" && curl -O -L -s "${curl_opts[@]}" "$download_url")

mkdir -p "$target_folder"
echo_yellow "Deleting contents of $target_folder/lib"
rm -frv "$target_folder/lib"

echo_yellow "Extracting archive to $target_dir"
if [[ "$name" =~ tar.xz|tar.gz|tar ]]; then
  tar $strip_gam -xf "$temp_archive_dir"/"$name" -C "$target_dir"
elif [[ "$name" == *.zip ]]; then
  unzip -o "${temp_archive_dir}/${name}" -d "${target_dir}"
else
  echo "I don't know what to do with files like ${name}. Giving up."
  exit 1
fi
rc=$?
if (( $rc != 0 )); then
  echo_red "ERROR: extracting the GAM archive with tar failed with error $rc. Exiting."
  exit
else
  echo_green "Finished extracting GAM archive."
fi

# Update profile to add gam command
if [ "$update_profile" = true ]; then
  alias_line="alias gam=\"$target_gam\""
  if [ "$gamos" == "linux" ]; then
    update_profile "$HOME/.bash_aliases" 0 || update_profile "$HOME/.bash_profile" 0 || update_profile "$HOME/.bashrc" 0
    update_profile "$HOME/.zshrc" 0
  elif [ "$gamos" == "macos" ]; then
    update_profile "$HOME/.bash_aliases" 0 || update_profile "$HOME/.bash_profile" 0 || update_profile "$HOME/.bashrc" 0 || update_profile "$HOME/.profile" 1
    update_profile "$HOME/.zshrc" 1
  fi
else
  echo_yellow "skipping profile update."
fi

if [ "$upgrade_only" = true ]; then
  echo_green "Here's information about your GAM upgrade:"
  "$target_gam" version extended
  rc=$?
  if (( $rc != 0 )); then
    echo_red "ERROR: Failed running GAM for the first time with return code $rc. Please report this error to GAM mailing list. Exiting."
    exit
  fi

  echo_green "GAM upgrade complete!"
  exit
fi

# Set config command
#config_cmd="config no_browser false"

while true; do
  read -p "Can you run a full browser on this machine? (usually Y for MacOS, N for Linux if you SSH into this machine) " yn
  case $yn in
    [Yy]*)
      break
      ;;
    [Nn]*)
#      config_cmd="config no_browser true"
      touch "$target_folder/nobrowser.txt" > /dev/null 2>&1
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
        read -p "Please enter your Google Workspace admin email address: " adminuser
      fi
#      "$target_gam" $config_cmd create project $adminuser
      "$target_gam" create project $adminuser
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
  read -p "Are you ready to authorize GAM to perform Google Workspace management operations as your admin account? (yes or no) " yn
  case $yn in
    [Yy]*)
#      "$target_gam" $config_cmd oauth create $adminuser
      "$target_gam" oauth create $adminuser
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
while $admin_authorized; do
  read -p "Are you ready to authorize GAM to manage Google Workspace user data and settings? (yes or no) " yn
  case $yn in
    [Yy]*)
      if [ "$regularuser" == "" ]; then
        read -p "Please enter the email address of a regular Google Workspace user: " regularuser
      fi
      echo_yellow "Great! Checking service account scopes.This will fail the first time. Follow the steps to authorize and retry. It can take a few minutes for scopes to PASS after they've been authorized in the admin console."
#      "$target_gam" $config_cmd user $regularuser check serviceaccount
      "$target_gam" user $regularuser check serviceaccount
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
       echo -e "\nYou can authorize a service account later by running:\n\ngam user $adminuser check serviceaccount\n"
       break
       ;;
     *)
       echo_red "Please answer yes or no."
       ;;
  esac
done

echo_green "Here's information about your new GAM installation:"
#"$target_gam" $config_cmd save version extended
"$target_gam" version extended
rc=$?
if (( $rc != 0 )); then
  echo_red "ERROR: Failed running GAM for the first time with $rc. Please report this error to GAM mailing list. Exiting."
  exit
fi

echo_green "GAM installation and setup complete!"
if [ "$update_profile" = true ]; then
  echo_green "Please restart your terminal shell or to get started right away run:\n\n$alias_line"
fi
