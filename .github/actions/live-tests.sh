#!/usr/bin/env bash
# GAM GitHub Actions Live API Test Suite
# Runs across all build and test matrix jobs with 20-way concurrency hardening,
# age-gated (>2h) startup cleanup, EXIT trap teardown, and regular fixture users.

set -eo pipefail

export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"
export GAM_THREADS="${GAM_THREADS:-5}"

echo "### GAM Execution Report" >> "${GITHUB_STEP_SUMMARY}"
echo "| Command | Status | Exit Code |" >> "${GITHUB_STEP_SUMMARY}"
echo "| :--- | :---: | :---: |" >> "${GITHUB_STEP_SUMMARY}"

# Execute a GAM command with stderr log grouping, optional retries (-r N),
# and optional allowed exit codes (-a "0 50").
# Stdout is preserved cleanly for command substitution: out=$(run_gam ...).
run_gam() {
  local allowed_codes="0"
  local max_attempts=1
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -a)
        allowed_codes="$2"
        shift 2
        ;;
      -r)
        max_attempts="$2"
        shift 2
        ;;
      *)
        break
        ;;
    esac
  done

  allowed_codes="${allowed_codes//,/ }"
  local attempt=1
  local exit_code=0
  local passed=false

  while true; do
    exit_code=0
    if [[ "${attempt}" -eq 1 ]]; then
      echo "::group::Executing: gam $*" >&2
    else
      echo "::group::Executing (attempt ${attempt}/${max_attempts}): gam $*" >&2
    fi

    $gam "$@" || exit_code=$?
    echo "::endgroup::" >&2

    passed=false
    for code in ${allowed_codes}; do
      if [[ "${exit_code}" -eq "${code}" ]]; then
        passed=true
        break
      fi
    done

    if [[ "${passed}" == "true" ]]; then
      echo "| \`gam $*\` | 🟢 Pass | ${exit_code} |" >> "${GITHUB_STEP_SUMMARY}"
      return 0
    fi

    # Automatically allow 1 jittered retry on transient Google HTTP 5xx/429 (RC 9)
    # or transient DwD token exchange blips (RC 12) even if -r was not passed.
    local effective_max="${max_attempts}"
    if [[ "${effective_max}" -eq 1 && ( "${exit_code}" -eq 9 || "${exit_code}" -eq 12 ) ]]; then
      effective_max=2
    fi

    if [[ "${attempt}" -lt "${effective_max}" ]]; then
      local sleep_s=$(( attempt * 4 + (RANDOM % 5) + 1 ))
      echo "::warning::gam $* exited with ${exit_code} (attempt ${attempt}/${effective_max}); retrying in ${sleep_s}s..." >&2
      sleep "${sleep_s}"
      attempt=$((attempt + 1))
      continue
    fi

    echo "| \`gam $*\` | 🔴 Fail | ${exit_code} |" >> "${GITHUB_STEP_SUMMARY}"
    exit "${exit_code}"
  done
}

# Filter a GAM CSV file in-place to retain ONLY stale test resources older than
# STALE_SECONDS (default 7200s = 2 hours), based on embedded `gha_test_<JID>_<ts>`
# timestamps (supports both 10-digit Unix epoch seconds and legacy 19-digit time_ns).
# Returns 0 if >=1 stale row remains to clean up, or 1 if 0 rows remain.
filter_stale_csv() {
  local csv_file="$1"
  local stale_seconds="${2:-7200}"
  if [[ ! -f "${csv_file}" ]]; then
    return 1
  fi
  "${PYTHON}" - "${csv_file}" "${JID}" "${stale_seconds}" <<'PYEOF'
import csv
import re
import sys
import time

csv_path, jid, stale_sec = sys.argv[1], sys.argv[2], int(sys.argv[3])
now = int(time.time())
pat = re.compile(rf"gha[_-]test[_-]{re.escape(jid)}[_-](\d+)")

with open(csv_path, "r", encoding="utf-8", errors="replace", newline="") as f:
    rows = list(csv.reader(f))

if len(rows) <= 1:
    sys.exit(1)

header, body = rows[0], rows[1:]
kept = []
for row in body:
    joined = ",".join(row)
    m = pat.search(joined)
    if m:
        ts = int(m.group(1))
        if ts > 10**15:       # legacy time.time_ns()
            ts //= 10**9
        elif ts > 10**12:     # milliseconds
            ts //= 10**3
        if (now - ts) >= stale_sec:
            kept.append(row)
    else:
        # Rows matched by query "gha.jid=$JID" without timestamp in primaryEmail
        # check creationTime column if present, otherwise only clean if >2h
        kept_by_time = False
        for idx, col in enumerate(header):
            if col in ("creationTime", "createTime") and idx < len(row) and row[idx]:
                from datetime import datetime, timezone
                try:
                    dt = datetime.fromisoformat(row[idx].replace("Z", "+00:00"))
                    if (now - int(dt.timestamp())) >= stale_sec:
                        kept_by_time = True
                except ValueError:
                    pass
        if kept_by_time:
            kept.append(row)

with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(kept)

sys.exit(0 if kept else 1)
PYEOF
}

export gam_user="gam-gha-${JID}@pdl.jaylee.us"
echo "gam_user=${gam_user}" >> "${GITHUB_ENV}"

# Configure GAM once (preserving OS-specific paths initialized in gam.cfg)
# plus a [nodasa] section so we never need repeated `gam config enable_dasa ... save` spawns.
run_gam config \
  customer_id "C03uzfv2s" \
  domain "pdl.jaylee.us" \
  admin_email "${gam_user}" \
  enable_dasa true \
  clock_skew_in_seconds 120 \
  retry_api_service_not_available true \
  bail_on_internal_error_tries 5 \
  show_api_calls_retry_data true \
  save

if ! grep -q '^\[nodasa\]' "${GAMCFGDIR}/gam.cfg" 2>/dev/null; then
  printf '\n[nodasa]\nenable_dasa = false\n' >> "${GAMCFGDIR}/gam.cfg"
fi

# Verify client OAuth & DwD service account auth
run_gam -r 2 select nodasa oauth info
run_gam -r 2 select nodasa oauth refresh
run_gam -r 2 checkconn
run_gam -r 2 user "${gam_user}" check serviceaccount
run_gam info domain
run_gam info user

# Detect pre-created regular Workspace fixture users (`bootstrap-fixtures.sh`);
# gracefully fall back to $gam_user if not yet provisioned.
candidate_u1="gam-gha-${JID}-u1@pdl.jaylee.us"
candidate_u2="gam-gha-${JID}-u2@pdl.jaylee.us"
has_fixture_users=false
if $gam info user "${candidate_u1}" quick >/dev/null 2>&1 && $gam info user "${candidate_u2}" quick >/dev/null 2>&1; then
  reg_user1="${candidate_u1}"
  reg_user2="${candidate_u2}"
  has_fixture_users=true
  echo "Using pre-provisioned regular fixture users: ${reg_user1}, ${reg_user2}" >&2
else
  reg_user1="${gam_user}"
  reg_user2="${gam_user}"
  echo "::warning::Fixture users ${candidate_u1} / ${candidate_u2} not found; falling back to ${gam_user}. Run .github/actions/bootstrap-fixtures.sh to provision dedicated regular users." >&2
fi

epoch_sec=$("${PYTHON}" -c "import time; print(int(time.time()))" | tr -d '\r')
run_tag="${GITHUB_RUN_ID:-local}_${GITHUB_RUN_ATTEMPT:-1}"
export newbase="gha_test_${JID}_${epoch_sec}_${run_tag}"
export newuser="${newbase}@pdl.jaylee.us"
export newgroup="${newbase}-group@pdl.jaylee.us"
export newcigroup="${newbase}-cigroup@pdl.jaylee.us"
export newalias="${newbase}-alias@pdl.jaylee.us"
export newbuilding="${newbase}-building"
export newresource="${newbase}-resource"
export newou="aaaGithub Actions/${newbase}"

# Track current-run ephemeral resources for best-effort EXIT trap cleanup if a step fails mid-run.
cleanup_ou=""
cleanup_user=""
cleanup_group=""
cleanup_cigroup=""
cleanup_building=""
cleanup_resource=""
cleanup_feat1=""
cleanup_feat2=""
cleanup_driveid=""
cleanup_folderid=""
cleanup_matterid=""
cleanup_holdname=""
cleanup_ssoprofile=""
cleanup_printerid=""
cleanup_devicesn=""
cleanup_label=""

cleanup_current_run() {
  local exit_status=$?
  if [[ "${exit_status}" -eq 0 ]]; then
    return 0
  fi
  echo "::group::EXIT trap: cleaning up ephemeral resources from failed run (${newbase})" >&2
  set +e
  if [[ -n "${cleanup_holdname}" && -n "${cleanup_matterid}" ]]; then
    $gam select nodasa delete hold "${cleanup_holdname}" matter "${cleanup_matterid}" >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_matterid}" ]]; then
    $gam select nodasa update matter "${cleanup_matterid}" action close >/dev/null 2>&1
    $gam select nodasa update matter "${cleanup_matterid}" action delete >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_printerid}" ]]; then
    $gam delete printer "${cleanup_printerid}" >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_ssoprofile}" && "${cleanup_ssoprofile}" != "inProgress" ]]; then
    $gam delete inboundssoprofile "id:${cleanup_ssoprofile}" >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_driveid}" ]]; then
    $gam user "${gam_user}" update shareddrive "${cleanup_driveid}" ou "aaaGithub Actions" >/dev/null 2>&1
    $gam user "${gam_user}" delete shareddrive "${cleanup_driveid}" nukefromorbit >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_folderid}" ]]; then
    $gam user "${reg_user1}" delete drivefile "id:${cleanup_folderid}" purge >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_label}" ]]; then
    $gam user "${reg_user1}" delete label "${cleanup_label}" >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_devicesn}" ]]; then
    $gam redirect csv ./trap-devices.csv print devices nopersonaldevices nodeviceusers filter "serial:${cleanup_devicesn}" >/dev/null 2>&1
    $gam csv ./trap-devices.csv gam delete device id ~name >/dev/null 2>&1
  fi
  [[ -n "${cleanup_resource}" ]] && $gam delete resource "${cleanup_resource}" >/dev/null 2>&1
  [[ -n "${cleanup_feat1}" ]] && $gam delete feature "${cleanup_feat1}" >/dev/null 2>&1
  [[ -n "${cleanup_feat2}" ]] && $gam delete feature "${cleanup_feat2}" >/dev/null 2>&1
  [[ -n "${cleanup_building}" ]] && $gam delete building "${cleanup_building}" >/dev/null 2>&1
  [[ -n "${cleanup_group}" ]] && $gam delete group "${cleanup_group}" >/dev/null 2>&1
  [[ -n "${cleanup_cigroup}" ]] && $gam delete cigroup "${cleanup_cigroup}" >/dev/null 2>&1
  if [[ -n "${cleanup_user}" ]]; then
    $gam update user "${cleanup_user}" ou root >/dev/null 2>&1
    $gam delete user "${cleanup_user}" >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_ou}" ]]; then
    $gam delete ou "${cleanup_ou}" >/dev/null 2>&1
  fi
  echo "::endgroup::" >&2
}
trap cleanup_current_run EXIT

# ==============================================================================
# Age-gated cleanup of stale leftovers (>2 hours old) from old crashed runs.
# Active sibling runs (<2h old) are never touched.
# ==============================================================================
run_gam select nodasa config csv_output_row_filter "name:regex:gha_test_${JID}_" redirect csv ./vm-open.csv print vaultmatters matterstate OPEN
if filter_stale_csv ./vm-open.csv; then
  run_gam -a "0 55" select nodasa redirect csv ./vh-stale.csv multiprocess csv ./vm-open.csv gam print vaultholds matter "id:~~matterId~~"
  if [[ -f ./vh-stale.csv && $(wc -l < ./vh-stale.csv) -gt 1 ]]; then
    run_gam -a "0 55" select nodasa csv ./vh-stale.csv gam delete vaulthold "id:~~holdId~~" matter "id:~~matterId~~"
  fi
  run_gam select nodasa csv ./vm-open.csv gam update vaultmatter "id:~~matterId~~" action close
fi

run_gam select nodasa config csv_output_row_filter "name:regex:gha_test_${JID}_" redirect csv ./vm-closed.csv print vaultmatters matterstate CLOSED
if filter_stale_csv ./vm-closed.csv; then
  run_gam select nodasa csv ./vm-closed.csv gam update vaultmatter "id:~~matterId~~" action delete
fi

run_gam config csv_output_row_filter "name:regex:gha_test_${JID}_" redirect csv ./features.csv print features
if filter_stale_csv ./features.csv; then
  run_gam csv ./features.csv gam delete feature ~name
fi

run_gam config csv_output_row_filter "name:regex:^gha_test_${JID}_" redirect csv ./sd.csv user "${gam_user}" print shareddrives asadmin
if filter_stale_csv ./sd.csv; then
  run_gam csv ./sd.csv gam user "${gam_user}" delete shareddrive ~id nukefromorbit
fi

run_gam redirect csv ./users.csv print users query "gha.jid=${JID}" fields primaryEmail,creationTime
if filter_stale_csv ./users.csv; then
  run_gam -a "0 50" csv ./users.csv gam delete user ~primaryEmail
fi

run_gam config csv_output_row_filter "name:regex:^gha_test_${JID}_" redirect csv ./ous.csv print ous fromparent "aaaGithub Actions"
if filter_stale_csv ./ous.csv; then
  run_gam -a "0 50" csv ./ous.csv gam delete ou ~orgUnitId
fi

run_gam config csv_output_row_filter "email:regex:^gha_test_${JID}_" redirect csv ./cigroups.csv print cigroups
if filter_stale_csv ./cigroups.csv; then
  run_gam csv ./cigroups.csv gam delete cigroup ~email
fi

run_gam config csv_output_row_filter "resourceId:regex:^gha_test_${JID}_" redirect csv ./resources.csv print resources
if filter_stale_csv ./resources.csv; then
  run_gam csv ./resources.csv gam delete resource ~resourceId
fi

run_gam config csv_output_row_filter "buildingId:regex:^gha_test_${JID}_" redirect csv ./buildings.csv print buildings
if filter_stale_csv ./buildings.csv; then
  run_gam csv ./buildings.csv gam delete building ~buildingId
fi

run_gam config csv_output_row_filter "displayName:regex:^El\\ Goog\\ gha_test_${JID}_" redirect csv ./ssoprofiles.csv print inboundssoprofiles
if filter_stale_csv ./ssoprofiles.csv; then
  run_gam csv ./ssoprofiles.csv gam delete inboundssoprofile "id:~~name~~"
fi

run_gam redirect csv ./stale-devices.csv print devices nopersonaldevices nodeviceusers filter "serial:${JID}${JID}${JID}${JID}-"
if filter_stale_csv ./stale-devices.csv; then
  run_gam csv ./stale-devices.csv gam delete device id ~name
fi

# ==============================================================================
# Live API Test Execution
# ==============================================================================

echo "Creating OrgUnit ${newou}" >&2
run_gam create ou "${newou}"
cleanup_ou="${newou}"

# Directory User CRUD, Photo, Alias, License, and OU move tests on ephemeral $newuser
run_gam create user "${newuser}" firstname GHA lastname "${JID}" displayname "Github Actions ${JID}" password uniquerandom recoveryphone 12125121110 recoveryemail jay0lee@gmail.com gha.jid "${JID}" languages en+,en-GB- ou "${newou}"
cleanup_user="${newuser}"

run_gam -r 2 user "${newuser}" update photo https://dummyimage.com/98x98/000/fff.jpg
run_gam user "${newuser}" get photo
run_gam user "${newuser}" delete photo
run_gam create alias "${newalias}" user "${newuser}"

# Separate Directory Group vs. Cloud Identity Group to avoid cross-API replication races
run_gam create group "${newgroup}" name "GHA ${JID} group" description "This is a description" isarchived true
cleanup_group="${newgroup}"

run_gam create cigroup "${newcigroup}" name "GHA ${JID} CI group" description "Cloud Identity group test"
cleanup_cigroup="${newcigroup}"

run_gam user "${reg_user1}" sendemail recipient dev-null@pdl.jaylee.us subject "test message ${newbase}" message "GHA test message"
run_gam -r 2 user "${newuser}" add license workspaceenterpriseplus
run_gam update user "${newuser}" ou root # GAM synonym for / root OU
run_gam update user "${newuser}" ou "${newou}"

# Scoped Cloud Identity Policies check (1 page instead of 17 pages x 20 jobs)
run_gam -r 3 select nodasa redirect stdout ./policies.txt show policies filter "setting.type.matches('gmail.*')" noidmapping
run_gam select nodasa print privileges

# Cloud Identity Group & Directory Group operations
run_gam -r 3 update cigroup "${newcigroup}" security memberrestriction 'member.type == 1 || member.customer_id == groupCustomerId()'
run_gam -r 2 info cigroup "${newcigroup}"
run_gam -r 2 info cigroup "${newcigroup}" membertree

run_gam -r 3 update group "${newgroup}" add owner "${gam_user}"
run_gam -r 2 update group "${newgroup}" add member "${newuser}"
run_gam info group "${newgroup}"

# Delegated Admin Role & Contact Delegation tests using pre-provisioned regular fixture users
if [[ "${has_fixture_users}" == "true" ]]; then
  run_gam -r 2 select nodasa create admin "${reg_user1}" _GROUPS_EDITOR_ROLE org_unit "${newou}"
  run_gam select nodasa config csv_output_row_filter "assignedToUser:regex:${reg_user1}" redirect csv ./admins.csv print admins
  run_gam select nodasa csv ./admins.csv gam delete admin "~roleAssignmentId"

  run_gam select nodasa user "${reg_user1}" add contactdelegate "${reg_user2}"
  run_gam select nodasa user "${reg_user1}" print contactdelegates
  run_gam select nodasa user "${reg_user1}" delete contactdelegate "${reg_user2}"
fi

# Mailbox & Gmail operations on pre-licensed $reg_user1 (instant; zero license propagation wait)
run_gam user "${reg_user1}" waitformailbox retries 5
run_gam user "${reg_user1}" imap on
run_gam user "${reg_user1}" show imap
run_gam user "${reg_user1}" show delegates

biohazard=$(printf '\xe2\x98\xa3')
test_label="${biohazard} unicode ${newbase} ${biohazard}"
run_gam user "${reg_user1}" label "${test_label}"
cleanup_label="${test_label}"
run_gam user "${reg_user1}" show labels
run_gam redirect stdout ./labels.txt user "${reg_user1}" show labels

run_gam user "${reg_user1}" importemail subject "GHA import ${newbase}" message "This is a test import" labels IMPORTANT,UNREAD,INBOX,STARRED
run_gam user "${reg_user1}" insertemail subject "GHA insert ${newbase}" file gam.py labels INBOX,UNREAD
run_gam user "${reg_user1}" sendemail recipient admin@pdl.jaylee.us subject "GHA send ${reg_user1} ${newbase}" file gam.py
run_gam user "${reg_user1}" draftemail subject "GHA draft ${newbase}" message "Draft message test"

# Delete messages matching this run's unique $newbase (plus any >2d leftovers) so concurrent runs never collide
run_gam -a "0 60" users "${reg_user1}" delete messages query "(subject:\"${newbase}\" OR older_than:2d) in:anywhere" maxtodelete 99999 doit
run_gam user "${reg_user1}" delete label "${test_label}"
cleanup_label=""

# Buildings, Features, and Resource Calendars
run_gam create feature name "VC-${newbase}"
cleanup_feat1="VC-${newbase}"
run_gam create feature name "Whiteboard-${newbase}"
cleanup_feat2="Whiteboard-${newbase}"
run_gam create building "My Building - ${newbase}" id "${newbuilding}" floors 1,2,3,4,5,6,7,8,9,10,11,12,14,15 description "No 13th floor here..."
cleanup_building="${newbuilding}"
run_gam -r 2 create resource "${newresource}" "Resource Calendar ${epoch_sec}" capacity 25 features "Whiteboard-${newbase},VC-${newbase}" building "${newbuilding}" floor 15 type Room
cleanup_resource="${newresource}"
run_gam -r 2 info resource "${newresource}"

# Drive file operations on pre-licensed $reg_user1
folder_id=$(run_gam user "${reg_user1}" add drivefile drivefilename "TPS Reports ${newbase}" mimetype gfolder returnidonly | tr -d '\r')
cleanup_folderid="${folder_id}"
run_gam user "${reg_user1}" show filelist query "'me' in owners" maxfiles 10
run_gam user "${reg_user1}" delete drivefile "id:${folder_id}" purge
cleanup_folderid=""

# Calendar ACL & Event operations (skipping owner role on delete to avoid self-ACL error)
run_gam redirect csv ./cal-acl.csv calendar "${reg_user1}" printacl
run_gam csv ./cal-acl.csv skipfield role "^owner$" gam calendar "${reg_user1}" delete ~id
run_gam calendar "${reg_user1}" add read domain
run_gam calendar "${reg_user1}" add freebusy default
run_gam calendar "${reg_user1}" add editor "${newuser}"
run_gam calendar "${reg_user1}" showacl
run_gam redirect csv ./cal-acl.csv calendar "${reg_user1}" printacl
run_gam csv ./cal-acl.csv skipfield role "^owner$" gam calendar "${reg_user1}" delete ~id
run_gam calendar "${reg_user1}" addevent summary "GHA test event ${newbase}" start +1h end +2h attendee "${newgroup}" hangoutsmeet guestscanmodify true sendupdates all
run_gam calendar "${reg_user1}" printevents after -0d

# Google Vault Matter, Hold, Count & Export lifecycle
raw_matter_id=$(run_gam select nodasa create vaultmatter name "GHA matter ${newbase}" description "test matter" returnidonly | tr -d '\r')
matterid="uid:${raw_matter_id}"
cleanup_matterid="${matterid}"

run_gam -r 3 select nodasa create vaulthold matter "${matterid}" name "GHA hold ${newbase}" corpus mail ou "${newou}"
cleanup_holdname="GHA hold ${newbase}"
run_gam select nodasa print vaultmatters matterstate open
run_gam select nodasa print vaultholds matter "${matterid}"
run_gam select nodasa redirect csv ./vaultcount.csv print vaultcount matter "${matterid}" corpus mail everyone
run_gam -r 3 select nodasa create vaultexport matter "${matterid}" name "GHA export ${newbase}" corpus mail ou "${newou}"
run_gam select nodasa redirect csv ./exports.csv print exports matter "${matterid}"
run_gam select nodasa csv ./exports.csv gam info export "${matterid}" id:~~id~~

# Teardown resource/building/groups & license while empty Vault export finishes in background
run_gam -r 2 delete resource "${newresource}"
cleanup_resource=""
run_gam delete feature "Whiteboard-${newbase}"
cleanup_feat2=""
run_gam delete feature "VC-${newbase}"
cleanup_feat1=""
run_gam delete building "${newbuilding}"
cleanup_building=""
run_gam delete group "${newgroup}"
cleanup_group=""
run_gam delete cigroup "${newcigroup}"
cleanup_cigroup=""

run_gam -r 2 select nodasa user "${newuser}" delete license workspaceenterpriseplus
run_gam -a "0 20" whatis "${newuser}"
run_gam user "${gam_user}" show tokens

# Download Vault export (with built-in polling if export is still IN_PROGRESS), then close/delete matter
download_dir="${RUNNER_TEMP}/TEMP_DELETE_ME_${newbase}"
mkdir -p -v "${download_dir}"
run_gam select nodasa redirect csv ./exports.csv print exports matter "${matterid}"
run_gam select nodasa csv ./exports.csv gam download export "${matterid}" id:~~id~~ targetfolder "${download_dir}" downloadattempts 6 retryinterval 10
rm -rf "${download_dir}"

run_gam -r 2 select nodasa delete hold "GHA hold ${newbase}" matter "${matterid}"
cleanup_holdname=""
run_gam select nodasa update matter "${matterid}" action close
run_gam select nodasa update matter "${matterid}" action delete
cleanup_matterid=""

# Shake off Vault hold propagation on $newuser and delete user
run_gam redirect csv ./this-user.csv print users query "email:${newuser}" orgunitpath
run_gam csv ./this-user.csv gam update user ~primaryEmail ou ~orgUnitPath
run_gam -a "0 55" -r 3 select nodasa user "${newuser}" show holds

export sn="${JID}${JID}${JID}${JID}-$(openssl rand -base64 32 | sed 's/[^a-zA-Z0-9]//g')"
run_gam -r 2 create device serialnumber "${sn}" devicetype android
cleanup_devicesn="${sn}"

run_gam update user "${newuser}" ou root
run_gam -a "0 50" -r 2 delete user "${newuser}"
cleanup_user=""

# Device, Browser, CrOS & Reports checks (1x todrive test + local CSVs for remaining reports)
run_gam print mobile
run_gam print devices clientstates
run_gam print browsers
run_gam print cros allfields orderby serialnumber
run_gam show crostelemetry storagepercentonly
run_gam report usageparameters customer
run_gam report usage customer parameters gmail:num_emails_sent,accounts:num_1day_logins
run_gam -r 3 report customer todrive tdnobrowser
run_gam redirect csv ./report-users.csv report users
run_gam redirect csv ./report-admin.csv report admin start -3d

# Clean up any todrive Google Sheets older than 1 day on $gam_user so Drive stays clean
run_gam redirect csv ./old-td.csv user "${gam_user}" print filelist query "mimeType='application/vnd.google-apps.spreadsheet' and modifiedTime < '#querytimecutoff#' and 'me' in owners" querytimecutoff -1d
if [[ $(wc -l < ./old-td.csv) -gt 1 ]]; then
  run_gam csv ./old-td.csv gam user "${gam_user}" delete drivefile ~id purge
fi

run_gam redirect csv ./devices.csv print devices nopersonaldevices nodeviceusers filter "serial:${sn}"
run_gam csv ./devices.csv gam delete device id ~name
cleanup_devicesn=""

# Cloud Identity User Invitations & Access Context Manager CAA Levels (with jittered retry for 20-way org policy lock)
run_gam select nodasa print userinvitations
run_gam select nodasa redirect csv ./invitations.csv print userinvitations
run_gam select nodasa csv ./invitations.csv gam send userinvitation ~name

run_gam -r 4 select nodasa create caalevel "zzz_${newbase}" basic condition ipsubnetworks 1.1.1.1/32,2.2.2.2/32 endcondition
run_gam -r 4 select nodasa print caalevels
run_gam -r 4 select nodasa delete caalevel "zzz_${newbase}"

# Shared Drive lifecycle (created right where it is tested so lifetime is ~15s instead of 20m)
driveid=$(run_gam user "${gam_user}" add shareddrive "${newbase}" returnidonly | tr -d '\r')
cleanup_driveid="${driveid}"
echo "Created shared drive ${driveid}" >&2
run_gam -r 2 user "${gam_user}" add drivefile localfile gam.py parentid "${driveid}"
run_gam -r 2 user "${gam_user}" update shareddrive "${driveid}" ou "${newou}"
run_gam user "${gam_user}" show shareddrives asadmin
run_gam -r 2 user "${gam_user}" update shareddrive "${driveid}" ou "aaaGithub Actions" # move out before deleting OU
run_gam -r 2 user "${gam_user}" delete shareddrive "${driveid}" nukefromorbit
cleanup_driveid=""

# Inbound SAML SSO Profile & Credential lifecycle (fixed clean stdout capture)
ssoprofile=$(run_gam -r 2 create inboundssoprofile name "El Goog ${newbase}" loginurl https://www.google.com logouturl https://www.google.com changepasswordurl https://www.google.com entityid ElGoog return_name_only | tr -d '\r')
cleanup_ssoprofile="${ssoprofile}"
if [[ -n "${ssoprofile}" && "${ssoprofile}" != "inProgress" ]]; then
  run_gam -r 2 create inboundssocredential profile "id:${ssoprofile}" generate_key
  run_gam -r 2 delete inboundssoprofile "id:${ssoprofile}"
  cleanup_ssoprofile=""
fi

# Printers & Final OU check/delete
echo "printer model count:" >&2
run_gam print printermodels | wc -l
run_gam print printers
printerid=$(run_gam -r 2 create printer displayname "${newbase}" uri ipp://localhost:631 driverless description "made by ${gam_user}" ou "${newou}" returnIdOnly | tr -d '\r')
cleanup_printerid="${printerid}"
run_gam -r 2 info printer "${printerid}"
run_gam -r 2 delete printer "${printerid}"
cleanup_printerid=""

run_gam print ous showitemcountonly
run_gam check ou "${newou}" devices shareddrives subous users
run_gam -a "0 50" -r 3 delete ou "${newou}"
cleanup_ou=""
