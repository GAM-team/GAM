#!/usr/bin/env bash
# GAM GitHub Actions Live API Test Suite
# Runs across all build and test matrix jobs with 20-way concurrency hardening,
# age-gated (>2h) startup cleanup, EXIT trap teardown, in-process `gam loop`
# read-only sweeps, and regular fixture users.

set -eo pipefail

export GAM_THREADS="${GAM_THREADS:-5}"
# Skip google-auth GCE metadata server probes (169.254.169.254), which time out
# for ~4-5s on every SignJWT call on Apple-hosted macOS GitHub runners.
export NO_GCE_CHECK="true"

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
    exit "$(( exit_code != 0 ? exit_code : 1 ))"
  done
}

# Execute an in-process `gam ... loop <csv> showcmds true gam ...` sweep and
# verify that BOTH the outer process AND every individual looped command exited 0.
run_gam_loop() {
  local label="$1"
  shift
  local loop_err="./loop-${label}.stderr"
  local exit_code=0

  echo "::group::Executing in-process loop (${label}): gam $*" >&2
  $gam "$@" 2>"${loop_err}" || exit_code=$?
  cat "${loop_err}" >&2 || true
  echo "::endgroup::" >&2

  if [[ "${exit_code}" -ne 0 ]] || grep -Eq ',End,[^0],' "${loop_err}"; then
    echo "::error::In-process loop (${label}) had non-zero command exit (outer=${exit_code}):" >&2
    grep -E ',End,[^0],' "${loop_err}" >&2 || true
    echo "| \`gam loop (${label})\` | 🔴 Fail | ${exit_code} |" >> "${GITHUB_STEP_SUMMARY}"
    exit "${exit_code:-1}"
  fi

  local row_count
  row_count=$(grep -c ',End,0,' "${loop_err}" || true)
  echo "| \`gam loop (${label}: ${row_count} commands)\` | 🟢 Pass | 0 |" >> "${GITHUB_STEP_SUMMARY}"
}

# Filter a GAM CSV file in-place to retain ONLY stale test resources older than
# STALE_SECONDS (default 7200s = 2 hours), based on embedded `gha_test_<JID>_<ts>`
# timestamps (supports both 10-digit Unix epoch seconds and legacy 19-digit time_ns).
# Returns 0 if >=1 stale row remains to clean up, or 1 if 0 rows remain.
filter_stale_csv() {
  local csv_file="$1"
  local stale_seconds="${2:-7200}"
  local max_age_seconds="${3:-0}"
  if [[ ! -f "${csv_file}" ]]; then
    return 1
  fi
  "${PYTHON}" - "${csv_file}" "${JID}" "${stale_seconds}" "${max_age_seconds}" <<'PYEOF'
import csv
import re
import sys
import time

csv_path, jid = sys.argv[1], sys.argv[2]
stale_sec, max_age_sec = int(sys.argv[3]), int(sys.argv[4])
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
        age = now - ts
        if age >= stale_sec and (max_age_sec <= 0 or age <= max_age_sec):
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

# Verify bundled library versions (OpenSSL, cryptography, lxml, passlib, chardet, etc.),
# client OAuth, and DwD service account auth.
run_gam version extended
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
alert_since=$("${PYTHON}" -c "from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ'))" | tr -d '\r')
run_tag="${GITHUB_RUN_ID:-local}_${GITHUB_RUN_ATTEMPT:-1}"
export newbase="gha_test_${JID}_${epoch_sec}_${run_tag}"
export newuser="${newbase}@pdl.jaylee.us"
export newgroup="${newbase}-group@pdl.jaylee.us"
export newcigroup="${newbase}-cigroup@pdl.jaylee.us"
export newalias="${newbase}-alias@pdl.jaylee.us"
export newbuilding="${newbase}-building"
export newresource="${newbase}-resource"
export newou="aaaGithub Actions/${newbase}"
export newschema="gha_test_${JID}_${epoch_sec}"

# Track current-run ephemeral resources for best-effort EXIT trap cleanup if a step fails mid-run.
cleanup_ou=""
cleanup_user=""
cleanup_group=""
cleanup_cigroup=""
cleanup_schema=""
cleanup_building=""
cleanup_resource=""
cleanup_feat1=""
cleanup_feat2=""
cleanup_driveid=""
cleanup_folderid=""
cleanup_docid=""
cleanup_copyid=""
cleanup_sheetid=""
cleanup_formid=""
cleanup_tasklistid=""
cleanup_noteid=""
cleanup_contactid=""
cleanup_cgid=""
cleanup_filterid=""
cleanup_vacation=""
cleanup_seccal=""
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
    $gam select nodasa delete inboundssoprofile "id:${cleanup_ssoprofile}" >/dev/null 2>&1
  fi
  if [[ -n "${cleanup_driveid}" ]]; then
    $gam user "${gam_user}" update shareddrive "${cleanup_driveid}" ou "aaaGithub Actions" >/dev/null 2>&1
    $gam user "${gam_user}" delete shareddrive "${cleanup_driveid}" nukefromorbit >/dev/null 2>&1
  fi
  for fid in "${cleanup_folderid}" "${cleanup_copyid}" "${cleanup_docid}" "${cleanup_sheetid}" "${cleanup_formid}"; do
    if [[ -n "${fid}" ]]; then
      $gam user "${reg_user1}" delete drivefile "id:${fid}" purge >/dev/null 2>&1
    fi
  done
  [[ -n "${cleanup_tasklistid}" ]] && $gam user "${reg_user1}" delete tasklist "${cleanup_tasklistid}" >/dev/null 2>&1
  [[ -n "${cleanup_noteid}" ]] && $gam user "${reg_user1}" delete note "${cleanup_noteid}" >/dev/null 2>&1
  [[ -n "${cleanup_contactid}" ]] && $gam user "${reg_user1}" delete contacts "${cleanup_contactid}" >/dev/null 2>&1
  [[ -n "${cleanup_cgid}" ]] && $gam user "${reg_user1}" delete contactgroups "${cleanup_cgid}" >/dev/null 2>&1
  [[ -n "${cleanup_filterid}" ]] && $gam user "${reg_user1}" delete filter "${cleanup_filterid}" >/dev/null 2>&1
  [[ -n "${cleanup_vacation}" ]] && $gam user "${reg_user1}" vacation false >/dev/null 2>&1
  [[ -n "${cleanup_seccal}" ]] && $gam user "${reg_user1}" remove calendar "${cleanup_seccal}" >/dev/null 2>&1
  [[ -n "${cleanup_label}" ]] && $gam user "${reg_user1}" delete label "${cleanup_label}" >/dev/null 2>&1
  if [[ -n "${cleanup_devicesn}" ]]; then
    $gam redirect csv ./trap-devices.csv print devices nopersonaldevices nodeviceusers filter "serial:${cleanup_devicesn}" >/dev/null 2>&1
    $gam csv ./trap-devices.csv gam delete device id ~name >/dev/null 2>&1
  fi
  [[ -n "${cleanup_schema}" ]] && $gam select nodasa delete schema "${cleanup_schema}" >/dev/null 2>&1
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

run_gam select nodasa config csv_output_row_filter "schemaName:regex:^gha_test_${JID}_" redirect csv ./schemas.csv print schemas
if filter_stale_csv ./schemas.csv; then
  run_gam -a "0 50" select nodasa csv ./schemas.csv gam delete schema ~schemaName
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
  run_gam -a "0 50" csv ./users.csv gam update user ~primaryEmail ou root
  run_gam -a "0 50" csv ./users.csv gam delete user ~primaryEmail
fi

# Skip legacy >48h OUs that are permanently blocked by ghost/soft-deleted objects
run_gam config csv_output_row_filter "name:regex:^gha_test_${JID}_" redirect csv ./ous.csv print ous fromparent "aaaGithub Actions"
if filter_stale_csv ./ous.csv 7200 172800; then
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
# In-Process `gam loop` Read-Only API Sweeps & Batch/ThreadBatch/CSVTest Modes
# ==============================================================================
cat > ./loop-admin.csv <<EOF
verb,obj
info,customer
print,domains
print,domainaliases
print,schemas
show,transferapps
print,datatransfers
show,alertsettings
print,chromeversions
print,chromeprofiles
print,chromedevicecounts
print,chromeneedsattn
print,chromeaues
print,classificationlabels
EOF
run_gam_loop "admin-ro" select nodasa redirect stdout ./loop-admin.out loop ./loop-admin.csv showcmds true gam ~verb ~obj

run_gam select nodasa redirect csv ./roles.csv print roles nosystemroles
run_gam select nodasa info adminrole _HELP_DESK_ADMIN_ROLE
run_gam select nodasa redirect csv ./chromehistory.csv print chromehistory platforms
run_gam select nodasa redirect csv ./courses.csv print courses teacher "${reg_user1}"
run_gam redirect csv ./alerts.csv print alerts filter "createTime >= '${alert_since}'"

cat > ./loop-user.csv <<EOF
u,verb,obj
${reg_user1},print,analyticaccounts
${reg_user1},print,analyticaccountsummaries
${reg_user1},print,lookerstudioassets
${reg_user1},print,classificationlabels
${reg_user1},print,othercontacts
${reg_user1},print,peopleprofile
${reg_user1},show,gmailprofile
${reg_user1},show,pop
${reg_user1},show,vacation
${reg_user1},show,signature
${reg_user1},show,forward
${reg_user1},print,sendas
${reg_user1},print,filters
${reg_user1},print,forwardingaddresses
${reg_user1},print,calsettings
${reg_user1},print,calendars
${reg_user1},show,drivesettings
${reg_user1},print,notes
${reg_user1},print,tasklists
${reg_user1},print,tasks
EOF
run_gam_loop "user-ro" redirect stdout ./loop-user.out loop ./loop-user.csv showcmds true gam user ~u ~verb ~obj

run_gam redirect csv ./driveactivity.csv user "${reg_user1}" print driveactivity maxactivities 5
run_gam -a "0 60" redirect csv ./meetconf.csv user "${reg_user1}" print meetconferences

# Exercise batch (subprocess), tbatch (free-threaded / threadpool), and csvtest execution engines
cat > ./smoke.bat <<EOF
gam info domain
gam info user ${reg_user1} quick
EOF
run_gam batch ./smoke.bat
run_gam tbatch ./smoke.bat
printf 'email\n%s\n' "${reg_user1}" > ./smoke-u.csv
run_gam csvtest ./smoke-u.csv gam info user ~email

# ==============================================================================
# Live API CRUD Test Execution
# ==============================================================================

echo "Creating OrgUnit ${newou}" >&2
run_gam create ou "${newou}"
cleanup_ou="${newou}"

# Chrome Policy schema & OU policy lifecycle (reads against permanent parent OU, writes scoped to $newou)
run_gam select nodasa info chromeschema chrome.users.QrCodeGeneratorEnabled
run_gam select nodasa redirect csv ./chromepolicies.csv print chromepolicies ou "aaaGithub Actions" namespace chrome.users
run_gam -r 2 select nodasa update chromepolicy chrome.users.QrCodeGeneratorEnabled qrCodeGeneratorEnabled false ou "${newou}"
run_gam -r 2 select nodasa delete chromepolicy chrome.users.QrCodeGeneratorEnabled ou "${newou}"

# Directory Custom Schema (read permanent `gha` schema; create/delete ephemeral schema without immediate read-back)
run_gam select nodasa info schema gha
run_gam -r 2 select nodasa create schema "${newschema}" field badge type string endfield
cleanup_schema="${newschema}"
run_gam -a "0 56" -r 2 select nodasa delete schema "${newschema}"
cleanup_schema=""

# Directory User CRUD, Photo, Alias, License, and OU move tests on ephemeral $newuser
run_gam create user "${newuser}" firstname GHA lastname "${JID}" displayname "Github Actions ${JID}" password uniquerandom recoveryphone 12125121110 recoveryemail jay0lee@gmail.com gha.jid "${JID}" languages en+,en-GB- ou "${newou}"
cleanup_user="${newuser}"

run_gam -r 2 user "${newuser}" update photo https://dummyimage.com/98x98/000/fff.jpg
run_gam user "${newuser}" get photo
run_gam user "${newuser}" delete photo
run_gam create alias "${newalias}" user "${newuser}"

# User security handlers against permanent pre-provisioned $reg_user2 (avoids new-user propagation lag)
run_gam select nodasa user "${reg_user2}" print asps
run_gam select nodasa user "${reg_user2}" signout

# Separate Directory Group vs. Cloud Identity Group to avoid cross-API replication races
run_gam create group "${newgroup}" name "GHA ${JID} group" description "This is a description" isarchived true
cleanup_group="${newgroup}"
run_gam -r 2 update group "${newgroup}" whocanpostmessage all_members_can_post

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
  run_gam -r 2 select nodasa create admin "${reg_user1}" _HELP_DESK_ADMIN_ROLE org_unit "${newou}"
  run_gam select nodasa redirect csv ./admins.csv print admins user "${reg_user1}"
  if [[ -f ./admins.csv && $(wc -l < ./admins.csv) -gt 1 ]]; then
    run_gam select nodasa csv ./admins.csv gam delete admin "~roleAssignmentId"
  fi

  run_gam select nodasa user "${reg_user1}" add contactdelegate "${reg_user2}"
  run_gam select nodasa user "${reg_user1}" print contactdelegates
  run_gam select nodasa user "${reg_user1}" delete contactdelegate "${reg_user2}"
fi

# Mailbox, Gmail Settings & Groups Migration operations on pre-licensed $reg_user1
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

filt_out=$(run_gam user "${reg_user1}" filter from "noreply-${newbase}@example.com" label STARRED | tr -d '\r')
filt_id=$(echo "${filt_out}" | sed -n 's/.*Filter: \([^, ]*\).*/\1/p' | head -n 1)
if [[ -n "${filt_id}" ]]; then
  cleanup_filterid="${filt_id}"
  run_gam -a "0 50" user "${reg_user1}" delete filter "${filt_id}"
  cleanup_filterid=""
fi

run_gam user "${reg_user1}" language en
run_gam user "${reg_user1}" signature "GHA Test Signature ${newbase}"
cleanup_vacation="true"
run_gam user "${reg_user1}" vacation true subject "OOO ${newbase}" message "Automated GHA test"
run_gam user "${reg_user1}" vacation false
cleanup_vacation=""

run_gam user "${reg_user1}" importemail subject "GHA import ${newbase}" message "This is a test import" labels IMPORTANT,UNREAD,INBOX,STARRED
run_gam user "${reg_user1}" insertemail subject "GHA insert ${newbase}" file gam.py labels INBOX,UNREAD
run_gam user "${reg_user1}" sendemail recipient admin@pdl.jaylee.us subject "GHA send ${reg_user1} ${newbase}" file gam.py
run_gam user "${reg_user1}" draftemail subject "GHA draft ${newbase}" message "Draft message test"

# Archive messages into $newgroup via Groups Migration API (allowing RC 60 if Gmail search index hasn't caught up yet)
run_gam -a "0 60" -r 2 select nodasa user "${reg_user1}" archive messages "${newgroup}" query "subject:\"GHA import ${newbase}\"" max_to_archive 5 doit

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

# Drive v3, Docs, Sheets, and Forms lifecycles on pre-licensed $reg_user1
folder_id=$(run_gam user "${reg_user1}" add drivefile drivefilename "TPS Reports ${newbase}" mimetype gfolder returnidonly | tr -d '\r')
cleanup_folderid="${folder_id}"
run_gam user "${reg_user1}" show filelist query "'me' in owners" maxfiles 10
run_gam user "${reg_user1}" delete drivefile "id:${folder_id}" purge
cleanup_folderid=""

doc_id=$(run_gam user "${reg_user1}" create drivefile drivefilename "GHA Doc ${newbase}" mimetype gdoc returnidonly | tr -d '\r')
cleanup_docid="${doc_id}"
run_gam user "${reg_user1}" update document "id:${doc_id}" json '{"requests":[{"insertText":{"location":{"index":1},"text":"Hello from GAM Phase 2 CI\n"}}]}'
doc_dl_dir="${RUNNER_TEMP}/DOC_DL_${newbase}"
mkdir -p "${doc_dl_dir}"
run_gam user "${reg_user1}" get document "id:${doc_id}" targetfolder "${doc_dl_dir}" overwrite true
rm -rf "${doc_dl_dir}"
copy_id=$(run_gam user "${reg_user1}" copy drivefile "id:${doc_id}" newfilename "GHA Copy ${newbase}" returnidonly | tr -d '\r')
cleanup_copyid="${copy_id}"
acl_target="${reg_user2}"
if [[ "${acl_target}" == "${reg_user1}" ]]; then
  acl_target="${gam_user}"
fi
run_gam user "${reg_user1}" create drivefileacl "id:${doc_id}" user "${acl_target}" role reader nodetails
run_gam user "${reg_user1}" print drivefileacls "id:${doc_id}"
run_gam -a "0 56" -r 2 user "${reg_user1}" delete drivefileacl "id:${doc_id}" "${acl_target}"
run_gam user "${reg_user1}" print filerevisions "id:${doc_id}"
run_gam user "${reg_user1}" trash drivefile "id:${copy_id}"
run_gam user "${reg_user1}" untrash drivefile "id:${copy_id}"
run_gam user "${reg_user1}" delete drivefile "id:${copy_id}" purge
cleanup_copyid=""
run_gam user "${reg_user1}" delete drivefile "id:${doc_id}" purge
cleanup_docid=""

sheet_id=$(run_gam user "${reg_user1}" create sheet json "{\"properties\":{\"title\":\"GHA Sheet ${newbase}\"}}" returnidonly | tr -d '\r')
cleanup_sheetid="${sheet_id}"
run_gam user "${reg_user1}" info sheet "${sheet_id}"
run_gam user "${reg_user1}" append sheetrange "${sheet_id}" json '{"range":"Sheet1!A1:B2","values":[["ColA","ColB"],["1","2"]]}'
run_gam user "${reg_user1}" print sheetrange "${sheet_id}" range "Sheet1!A1:B2"
run_gam user "${reg_user1}" clear sheetrange "${sheet_id}" range "Sheet1!A1:B2"
run_gam user "${reg_user1}" delete drivefile "id:${sheet_id}" purge
cleanup_sheetid=""

form_id=$(run_gam user "${reg_user1}" create form title "GHA Form ${newbase}" returnidonly | tr -d '\r')
cleanup_formid="${form_id}"
run_gam user "${reg_user1}" update form "${form_id}" description "Automated GAM CI form test"
run_gam user "${reg_user1}" print forms "${form_id}"
run_gam user "${reg_user1}" print formresponses "${form_id}"
run_gam user "${reg_user1}" delete drivefile "id:${form_id}" purge
cleanup_formid=""

# Tasks, Keep, People Contacts, and Meet v2 lifecycles on $reg_user1
tl_id=$(run_gam user "${reg_user1}" create tasklist title "GHA Tasks ${newbase}" returnidonly | tr -d '\r')
cleanup_tasklistid="${tl_id}"
task_id=$(run_gam user "${reg_user1}" create task "${tl_id}" title "Task ${newbase}" notes "CI task note" returnidonly | tr -d '\r')
run_gam -r 2 user "${reg_user1}" update task "${tl_id}:${task_id}" status completed
run_gam -a "0 50" user "${reg_user1}" delete task "${tl_id}:${task_id}"
run_gam -a "0 50" user "${reg_user1}" delete tasklist "${tl_id}"
cleanup_tasklistid=""

note_out=$(run_gam user "${reg_user1}" create note title "GHA Note ${newbase}" text "Hello from GAM CI" nodetails | tr -d '\r')
note_id=$(echo "${note_out}" | sed -n 's/.*Note: \(notes\/[^, ]*\).*/\1/p' | head -n 1)
if [[ -n "${note_id}" ]]; then
  cleanup_noteid="${note_id}"
  run_gam -a "0 50" user "${reg_user1}" delete note "${note_id}"
  cleanup_noteid=""
fi

cg_out=$(run_gam user "${reg_user1}" create contactgroup name "GHA_CG_${newbase}" | tr -d '\r')
cg_id=$(echo "${cg_out}" | sed -n 's/.*Contact Group: \(contactGroups\/[^, ]*\).*/\1/p' | head -n 1)
cleanup_cgid="${cg_id}"
contact_out=$(run_gam user "${reg_user1}" create contact givenname GHA familyname "${JID}" email work "${newbase}@example.com" primary | tr -d '\r')
contact_id=$(echo "${contact_out}" | sed -n 's/.*Contact: \(people\/[^, ]*\).*/\1/p' | head -n 1)
if [[ -n "${contact_id}" ]]; then
  cleanup_contactid="${contact_id}"
  run_gam -r 2 user "${reg_user1}" update contacts "${contact_id}" note "Updated by GAM CI"
  run_gam -a "0 50" user "${reg_user1}" delete contacts "${contact_id}"
  cleanup_contactid=""
fi
if [[ -n "${cg_id}" ]]; then
  run_gam -a "0 50" user "${reg_user1}" delete contactgroups "${cg_id}"
  cleanup_cgid=""
fi

meet_space=$(run_gam user "${reg_user1}" create meetspace returnidonly | tr -d '\r')
if [[ -n "${meet_space}" ]]; then
  run_gam -r 2 user "${reg_user1}" update meetspace "${meet_space}" accesstype open
fi

# Calendar ACL, Primary Event & Secondary Calendar operations
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

seccal_out=$(run_gam user "${reg_user1}" create calendar summary "GHA SecCal ${newbase}" | tr -d '\r')
seccal_id=$(echo "${seccal_out}" | grep -Eo '[a-z0-9_]+@group\.calendar\.google\.com' | head -n 1)
if [[ -n "${seccal_id}" ]]; then
  cleanup_seccal="${seccal_id}"
  run_gam -r 2 user "${reg_user1}" modify calendar "${seccal_id}" description "Updated secondary calendar ${newbase}"
  run_gam -a "0 50" user "${reg_user1}" remove calendar "${seccal_id}"
  cleanup_seccal=""
fi

# Google Vault Matter, Hold, Count & Export lifecycle
# Paced slightly by JID so 20 parallel runners don't spike `Export Writes per minute`.
vault_jitter=$(( (JID % 10) * 3 + (RANDOM % 3) ))
if [[ "${vault_jitter}" -gt 0 ]]; then
  echo "Pacing Vault burst by ${vault_jitter}s for JID=${JID}..." >&2
  sleep "${vault_jitter}"
fi
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
run_gam -r 2 select nodasa create device serialnumber "${sn}" devicetype android
cleanup_devicesn="${sn}"

run_gam update user "${newuser}" ou root
run_gam -a "0 50" -r 2 delete user "${newuser}"
cleanup_user=""

# Device, Browser, CrOS & Reports checks (scoped to avoid domain-wide bloat + 1x todrive test)
run_gam print mobile
run_gam print devices nopersonaldevices clientstates filter "serial:${sn}"
run_gam print browsers
run_gam print cros allfields orderby serialnumber
run_gam show crostelemetry storagepercentonly
run_gam report usageparameters customer
run_gam report usage customer parameters gmail:num_emails_sent,accounts:num_1day_logins
run_gam -r 3 report customer todrive tdnobrowser
run_gam redirect csv ./report-users.csv report users
run_gam redirect csv ./report-admin.csv report admin user "${gam_user}" start -1h

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

# Inbound SAML SSO Profile & Credential lifecycle (requires client OAuth / nodasa)
ssoprofile=$(run_gam -r 2 select nodasa create inboundssoprofile name "El Goog ${newbase}" loginurl https://www.google.com logouturl https://www.google.com changepasswordurl https://www.google.com entityid ElGoog return_name_only | tr -d '\r')
cleanup_ssoprofile="${ssoprofile}"
if [[ -n "${ssoprofile}" && "${ssoprofile}" != "inProgress" ]]; then
  run_gam -r 2 select nodasa create inboundssocredential profile "id:${ssoprofile}" generate_key
  run_gam -r 2 select nodasa delete inboundssoprofile "id:${ssoprofile}"
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
