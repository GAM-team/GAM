#!/usr/bin/env bash
# One-time (and idempotent) provisioning script to create permanent, pre-licensed
# regular Google Workspace test users for GAM GitHub Actions live tests.
#
# Creates:
#   OU:    /aaaGithub Actions/Fixtures
#   Users: gam-gha-{1..MAX_JID}-u{1..USERS_PER_JID}@pdl.jaylee.us
#   SKU:   workspaceenterpriseplus (configurable via LICENSE_SKU)
#
# Usage:
#   ./.github/actions/bootstrap-fixtures.sh
#   GAM="gam select pdl" ./.github/actions/bootstrap-fixtures.sh

set -euo pipefail

export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

GAM_CMD="${GAM:-gam}"
EXPECTED_DOMAIN="${EXPECTED_DOMAIN:-pdl.jaylee.us}"
EXPECTED_CUSTOMER="${EXPECTED_CUSTOMER:-C03uzfv2s}"
MAX_JID="${MAX_JID:-25}"
USERS_PER_JID="${USERS_PER_JID:-2}"
LICENSE_SKU="${LICENSE_SKU:-workspaceenterpriseplus}"
PARENT_OU="aaaGithub Actions"
FIXTURE_OU="${PARENT_OU}/Fixtures"
export GAM_THREADS="${GAM_THREADS:-10}"

echo "==> Verifying active GAM configuration points to ${EXPECTED_DOMAIN} (${EXPECTED_CUSTOMER})..."
domain_info=$($GAM_CMD info domain 2>&1 || true)
if ! echo "${domain_info}" | grep -q "${EXPECTED_DOMAIN}" && ! echo "${domain_info}" | grep -q "${EXPECTED_CUSTOMER}"; then
  echo "ERROR: Active GAM configuration does not appear to target ${EXPECTED_DOMAIN} (${EXPECTED_CUSTOMER})." >&2
  echo "Output from '${GAM_CMD} info domain':" >&2
  echo "${domain_info}" >&2
  echo "" >&2
  echo "Tip: Specify your GAM binary or config section via the GAM environment variable, e.g.:" >&2
  echo "  GAM=\"gam select <pdl-section>\" ./.github/actions/bootstrap-fixtures.sh" >&2
  exit 1
fi
echo "    Confirmed domain ${EXPECTED_DOMAIN}."

echo "==> Ensuring Organizational Units '/${PARENT_OU}' and '/${FIXTURE_OU}' exist..."
$GAM_CMD create ou "${PARENT_OU}" description "GAM GitHub Actions root test OU" 2>/dev/null || true
$GAM_CMD create ou "${FIXTURE_OU}" description "Permanent pre-licensed fixture users for GAM GHA jobs (do not delete)" 2>/dev/null || true

echo "==> Checking existing fixture users in '/${FIXTURE_OU}'..."
existing_emails=$($GAM_CMD print users query "orgUnitPath='/${FIXTURE_OU}'" fields primaryEmail 2>/dev/null | awk -F',' 'NR>1 {print $1}' || true)

batch_file=$(mktemp "${TMPDIR:-/tmp}/gam-gha-fixtures.XXXXXX")
trap 'rm -f "${batch_file}"' EXIT

create_count=0
update_count=0
update_batch_file=$(mktemp "${TMPDIR:-/tmp}/gam-gha-fixtures-upd.XXXXXX")
trap 'rm -f "${batch_file}" "${update_batch_file}"' EXIT

all_fixture_emails=()
for jid in $(seq 1 "${MAX_JID}"); do
  for u in $(seq 1 "${USERS_PER_JID}"); do
    email="gam-gha-${jid}-u${u}@${EXPECTED_DOMAIN}"
    all_fixture_emails+=("${email}")
    if echo "${existing_emails}" | grep -Fxq "${email}"; then
      echo "    [exists] ${email}"
      echo "gam update user ${email} suspended off ou \"${FIXTURE_OU}\"" >> "${update_batch_file}"
      update_count=$((update_count + 1))
    else
      echo "gam create user ${email} firstname \"GHA Fixture\" lastname \"JID ${jid} U${u}\" password uniquerandom ou \"${FIXTURE_OU}\"" >> "${batch_file}"
      create_count=$((create_count + 1))
    fi
  done
done

if [[ "${create_count}" -gt 0 ]]; then
  echo "==> Creating ${create_count} missing fixture user(s) via 'gam batch'..."
  echo "commit-batch" >> "${batch_file}"
  $GAM_CMD batch "${batch_file}"
else
  echo "==> All $((MAX_JID * USERS_PER_JID)) fixture users already exist."
fi

if [[ "${update_count}" -gt 0 ]]; then
  echo "==> Ensuring ${update_count} existing fixture user(s) are active and in '/${FIXTURE_OU}'..."
  echo "commit-batch" >> "${update_batch_file}"
  $GAM_CMD batch "${update_batch_file}"
fi

csv_emails=$(IFS=,; echo "${all_fixture_emails[*]}")

echo "==> Assigning '${LICENSE_SKU}' license to all ${#all_fixture_emails[@]} fixture users..."
# `add license` returns non-zero if a user already holds the license, so ignore already-assigned warnings
$GAM_CMD users "${csv_emails}" add license "${LICENSE_SKU}" || true

echo "==> Waiting for all ${#all_fixture_emails[@]} fixture user mailboxes to finish provisioning..."
$GAM_CMD users "${csv_emails}" waitformailbox retries 60

echo ""
echo "==> Provisioning complete! Summary of '/${FIXTURE_OU}':"
$GAM_CMD print users query "orgUnitPath='/${FIXTURE_OU}'" fields primaryEmail,orgUnitPath,isMailboxSetup | head -n 60
