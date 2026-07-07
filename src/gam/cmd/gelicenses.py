"""Gemini Enterprise license management commands.

Uses the Discovery Engine API (discoveryengine.googleapis.com) to manage
GE licenses. Authenticates as the GAM service account (no DwD).

Admin-scoped (read-only):
  gam show geuserstore project <N> [location <R>]
  gam show|print gesubscriptions project <N> [location <R>] [todrive]
  gam show|print gelicenses project <N> [location <R>] [todrive]

User-scoped (mutating, receive users from <UserTypeEntity>):
  gam <UserTypeEntity> create gelicense project <N> [location <R>] [subscriptionid <ID>]
  gam <UserTypeEntity> delete gelicense project <N> [location <R>] [deleterecord]
  gam <UserTypeEntity> sync gelicense project <N> [location <R>] [subscriptionid <ID>] [deleterecord]
"""

import time

from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gamlib import state as GM

from gam.var import Act, Cmd, Ent, Ind

from gam.util.api import buildGAPIObjectGE
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
    getString,
    normalizeEmailAddressOrUID,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    entityActionPerformed,
    entityPerformActionModifierNumItems,
    printKeyValueList,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import systemErrorExit
from gam.util.output import stderrErrorMsg, writeStderr, writeStdout

from gam.constants import GOOGLE_API_ERROR_RC

# The API uses 'default_user_store' for the top-level user store
USER_STORE_ID = 'default_user_store'

# Max page size for userLicenses.list
GE_LICENSE_PAGE_SIZE = 1000

GE_THROW_REASONS = [GAPI.PERMISSION_DENIED, GAPI.NOT_FOUND, GAPI.FORBIDDEN]

# Known GE locations to probe when auto-detecting
KNOWN_GE_LOCATIONS = ['global', 'us', 'eu']


# --- Internal Helpers ---

def _getProjectAndLocation(action, entity):
  """Parse project and optional location arguments from the command line."""
  project = None
  location = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'project':
      project = getString(Cmd.OB_PROJECT_ID)
    elif myarg == 'location':
      location = getString(Cmd.OB_STRING)
    else:
      Cmd.Backup()
      break
  if not project:
    systemErrorExit(GOOGLE_API_ERROR_RC, Msg.GE_PROJECT_LOCATION_REQUIRED.format(action, entity))
  return project, location


def _buildGEService(project, location):
  """Build the Discovery Engine service client."""
  return buildGAPIObjectGE(project, location)


def _resolveLocation(project, provided_location):
  """Auto-detect the GE location if not provided.

  Probes known locations by building a service for each and checking
  whether any licenseConfigs exist. Auto-selects if exactly one location
  has configs.
  """
  if provided_location:
    return provided_location

  writeStdout('No location provided. Detecting available locations...\n')
  found = []
  for loc in KNOWN_GE_LOCATIONS:
    try:
      svc = _buildGEService(project, loc)
      parent = _getLicenseConfigsParent(project, loc)
      result = svc.projects().locations().licenseConfigs().list(parent=parent).execute()
      configs = result.get('licenseConfigs', [])
      if configs:
        writeStdout(f'  {loc}: found {len(configs)} license config(s)\n')
        found.append(loc)
      else:
        writeStdout(f'  {loc}: no license configs\n')
    except Exception:
      writeStdout(f'  {loc}: not available\n')
      continue

  if not found:
    systemErrorExit(GOOGLE_API_ERROR_RC,
                    f'No GE license configs found in any known location ({", ".join(KNOWN_GE_LOCATIONS)}). '
                    f'Specify one with location <LOCATION>.')
  if len(found) == 1:
    writeStdout(f'Auto-selected location: {found[0]}\n')
    return found[0]
  systemErrorExit(GOOGLE_API_ERROR_RC,
                  f'Multiple locations have license configs ({", ".join(found)}). '
                  f'Specify one with location <LOCATION>.')
  return None  # unreachable


def _getGEParent(project, location):
  """Build the userStore parent path."""
  return f'projects/{project}/locations/{location}/userStores/{USER_STORE_ID}'


def _getLicenseConfigsParent(project, location):
  """Build the licenseConfigs parent path."""
  return f'projects/{project}/locations/{location}'


def _handleGEError(e, project):
  """Handle common GE API errors with actionable IAM guidance."""
  sa_email = GM.Globals.get(GM.ADMIN, 'unknown')
  if isinstance(e, (GAPI.permissionDenied, GAPI.forbidden)):
    err_msg = str(e).lower()
    if 'service_disabled' in err_msg or 'not been used' in err_msg or 'not enabled' in err_msg:
      stderrErrorMsg(Msg.GE_API_NOT_ENABLED.format(project))
    elif 'user_project_denied' in err_msg or 'serviceusage' in err_msg:
      # Ambiguous — can mean API not enabled OR missing serviceUsageConsumer
      stderrErrorMsg(Msg.GE_API_NOT_ENABLED.format(project))
      stderrErrorMsg(Msg.GE_SERVICE_USAGE_DENIED.format(sa_email, project))
    else:
      stderrErrorMsg(Msg.GE_IAM_PERMISSION_DENIED.format(sa_email, project))
    systemErrorExit(GOOGLE_API_ERROR_RC, str(e))
  elif isinstance(e, GAPI.notFound):
    stderrErrorMsg(Msg.GE_USERSTORE_NOT_FOUND.format(project))
    systemErrorExit(GOOGLE_API_ERROR_RC, str(e))


def _processLRO(service, op_data):
  """Poll a Long-Running Operation until completion."""
  if op_data.get('done'):
    return _handleLROResult(op_data)

  operation_name = op_data.get('name')
  if not operation_name:
    stderrErrorMsg('Operation started but no operation name returned to track.')
    return False

  writeStderr(f'Waiting for operation: {operation_name.split("/")[-1]} ')
  retries = 0
  while True:
    time.sleep(3)
    try:
      op_data = callGAPI(service.projects().locations().operations(), 'get',
                         name=operation_name)
      if op_data.get('done'):
        writeStderr(' Done!\n')
        return _handleLROResult(op_data)
      writeStderr('.')
    except GAPI.notFound:
      retries += 1
      if retries > 5:
        stderrErrorMsg(f'\nOperation {operation_name} not found after polling.')
        return False
      writeStderr('?')


def _handleLROResult(data):
  """Process the result of a completed LRO."""
  if 'error' in data:
    stderrErrorMsg(f'Operation failed: {data["error"].get("message", "Unknown error")}')
    return False
  res_data = data.get('response', {})
  if 'errorSamples' in res_data and res_data['errorSamples']:
    stderrErrorMsg('Operation completed with errors:')
    for err in res_data['errorSamples']:
      writeStderr(f'  {err.get("message", err)}\n')
    return False
  writeStdout('Operation completed successfully.\n')
  return True


def _getAllLicenses(service, project, location):
  """Fetch all licenses, handling pagination automatically."""
  parent = _getGEParent(project, location)
  try:
    return callGAPIpages(service.projects().locations().userStores().userLicenses(), 'list', 'userLicenses',
                         throwReasons=GE_THROW_REASONS,
                         parent=parent, pageSize=GE_LICENSE_PAGE_SIZE)
  except (GAPI.permissionDenied, GAPI.forbidden, GAPI.notFound) as e:
    _handleGEError(e, project)
  return []


def _fetchSubscriptions(service, project, location):
  """Fetch subscription license configs."""
  parent = _getLicenseConfigsParent(project, location)
  try:
    return callGAPIpages(service.projects().locations().licenseConfigs(), 'list', 'licenseConfigs',
                         throwReasons=GE_THROW_REASONS,
                         parent=parent)
  except GAPI.notFound:
    return []
  except (GAPI.permissionDenied, GAPI.forbidden) as e:
    _handleGEError(e, project)
  return []


def _resolveSubscriptionId(service, project, location, provided_id):
  """Validate or auto-discover the subscription ID.

  Returns the full licenseConfig resource name from the API (which uses
  the project number) rather than the short ID. The API rejects license
  config paths reconstructed with the project ID string.
  """
  configs = _fetchSubscriptions(service, project, location)

  if provided_id:
    # Match the provided short ID against the API's full resource names
    for config in configs:
      name = config.get('name', '')
      if name.split('/')[-1] == provided_id:
        return name
    # Fall back to constructing the path (will use project ID — may fail)
    return f'projects/{project}/locations/{location}/licenseConfigs/{provided_id}'

  writeStdout('No subscriptionid provided. Checking available subscriptions...\n')

  if not configs:
    systemErrorExit(GOOGLE_API_ERROR_RC,
                    'No subscriptions found for this project and location.')

  if len(configs) == 1:
    full_name = configs[0].get('name', '')
    short_id = full_name.split('/')[-1]
    writeStdout(f'Auto-selected subscription: {short_id}\n')
    return full_name

  sub_ids = [config.get('name', '').split('/')[-1] for config in configs]
  systemErrorExit(GOOGLE_API_ERROR_RC,
                  f'Multiple subscriptions found ({", ".join(sub_ids)}). '
                  f'Specify one with subscriptionid <ID>.')
  return None  # unreachable


def _batchUpdateLicenses(service, project, location, subscription_id, assigns, removes, delete_record):
  """Perform a batch license update (assign and/or remove).

  Args:
    subscription_id: Full licenseConfig resource name from the API
      (e.g. projects/123456/locations/global/licenseConfigs/free_trial_gemini).
  """
  parent = _getGEParent(project, location)

  user_licenses = []
  if assigns and subscription_id:
    for email in assigns:
      user_licenses.append({
        'userPrincipal': email,
        'licenseConfig': subscription_id,
        'licenseAssignmentState': 'ASSIGNED',
      })
  for email in removes:
    user_licenses.append({
      'userPrincipal': email,
      'licenseAssignmentState': 'UNASSIGNED',
    })

  if not user_licenses:
    writeStdout('No license changes to make.\n')
    return

  body = {
    'deleteUnassignedUserLicenses': delete_record,
    'inlineSource': {
      'userLicenses': user_licenses,
      'updateMask': 'userPrincipal,licenseConfig,licenseAssignmentState',
    },
  }

  try:
    response = callGAPI(service.projects().locations().userStores(), 'batchUpdateUserLicenses',
                        throwReasons=GE_THROW_REASONS,
                        parent=parent, body=body)
    _processLRO(service, response)
  except (GAPI.permissionDenied, GAPI.forbidden, GAPI.notFound) as e:
    _handleGEError(e, project)


# --- Admin-Scoped Commands (read-only) ---

# gam show geuserstore project <Number> location <Region>
def doShowGEUserStore():
  project, location = _getProjectAndLocation('show', 'geuserstore')
  checkForExtraneousArguments()
  location = _resolveLocation(project, location)
  service = _buildGEService(project, location)
  name = _getGEParent(project, location)
  try:
    response = callGAPI(service.projects().locations().userStores(), 'get',
                        throwReasons=GE_THROW_REASONS,
                        name=name)
  except (GAPI.permissionDenied, GAPI.forbidden, GAPI.notFound) as e:
    _handleGEError(e, project)
    return

  printKeyValueList(['User Store', response.get('name', 'Unknown')])
  printKeyValueList(['Display Name', response.get('displayName', 'N/A')])
  default_lic = response.get('defaultLicenseConfig', '')
  if default_lic:
    printKeyValueList(['Default Subscription', default_lic.split('/')[-1]])
    printKeyValueList(['Default Subscription Path', default_lic])
  else:
    printKeyValueList(['Default Subscription', 'None Configured'])
  printKeyValueList(['Auto-Register New Users', response.get('enableLicenseAutoRegister', False)])
  printKeyValueList(['Auto-Update Expired', response.get('enableExpiredLicenseAutoUpdate', False)])


# gam show|print gesubscriptions project <Number> location <Region> [todrive]
def doPrintShowGESubscriptions():
  project, location = _getProjectAndLocation('show', 'gesubscriptions')
  location = _resolveLocation(project, location)
  csvPF = CSVPrintFile(['subscriptionId', 'state', 'activeLicenseCount', 'totalLicenseCount']) if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  service = _buildGEService(project, location)
  configs = _fetchSubscriptions(service, project, location)

  if not configs:
    writeStdout('No subscriptions found for this project and location.\n')
    return

  for config in configs:
    name = config.get('name', 'Unknown')
    sub_id = name.split('/')[-1]
    state = config.get('state', 'UNKNOWN')
    active = config.get('activeLicenseCount', '0')
    total = config.get('totalLicenseCount', 'Unknown')
    if csvPF:
      csvPF.WriteRow({
        'subscriptionId': sub_id,
        'state': state,
        'activeLicenseCount': active,
        'totalLicenseCount': total,
      })
    else:
      printKeyValueList(['Subscription ID', sub_id])
      printKeyValueList(['State', f'{state} | Assigned: {active}/{total}'])

  if csvPF:
    csvPF.writeCSVfile('Gemini Enterprise Subscriptions')


# gam show|print gelicenses project <Number> location <Region> [todrive]
def doPrintShowGELicenses():
  project, location = _getProjectAndLocation('show', 'gelicenses')
  location = _resolveLocation(project, location)
  csvPF = CSVPrintFile(['userPrincipal', 'licenseAssignmentState', 'updateTime',
                        'lastLoginTime', 'licenseConfig']) if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  service = _buildGEService(project, location)
  licenses = _getAllLicenses(service, project, location)

  if not licenses:
    writeStdout('No licenses found.\n')
    return

  for lic in licenses:
    name = lic.get('name', 'Unknown')
    email = lic.get('userPrincipal', name.split('/')[-1])
    state = lic.get('licenseAssignmentState', 'UNKNOWN')
    update_time = lic.get('updateTime', '')
    last_login = lic.get('lastLoginTime', '')
    license_config = lic.get('licenseConfig', '')
    if csvPF:
      csvPF.WriteRow({
        'userPrincipal': email,
        'licenseAssignmentState': state,
        'updateTime': update_time,
        'lastLoginTime': last_login,
        'licenseConfig': license_config,
      })
    else:
      printKeyValueList(['User', f'{email} | State: {state}'])

  if not csvPF:
    writeStdout(f'Total: {len(licenses)}\n')
  else:
    csvPF.writeCSVfile('Gemini Enterprise Licenses')


# --- User-Scoped Commands (mutating, receive users from <UserTypeEntity>) ---

# gam <UserTypeEntity> create gelicense project <N> location <R> [subscriptionid <ID>]
def createGELicense(users):
  project, location = _getProjectAndLocation('create', 'gelicense')
  location = _resolveLocation(project, location)
  subscription_id = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'subscriptionid':
      subscription_id = getString(Cmd.OB_STRING)
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  service = _buildGEService(project, location)
  subscription_id = _resolveSubscriptionId(service, project, location, subscription_id)
  j, jcount, users = getEntityArgument(users)
  entityPerformActionModifierNumItems([Ent.LICENSE, 'Gemini Enterprise'], Msg.TO_LC, jcount, Ent.USER)
  Ind.Increment()
  emails = []
  for user in users:
    j += 1
    user = normalizeEmailAddressOrUID(user)
    emails.append(user)
    entityActionPerformed([Ent.USER, user, Ent.LICENSE, 'Gemini Enterprise'], j, jcount)
  Ind.Decrement()
  if emails:
    _batchUpdateLicenses(service, project, location, subscription_id,
                         assigns=emails, removes=[], delete_record=False)


# gam <UserTypeEntity> delete gelicense project <N> location <R> [deleterecord]
def deleteGELicense(users):
  project, location = _getProjectAndLocation('delete', 'gelicense')
  location = _resolveLocation(project, location)
  delete_record = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'deleterecord':
      delete_record = True
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  service = _buildGEService(project, location)
  j, jcount, users = getEntityArgument(users)
  entityPerformActionModifierNumItems([Ent.LICENSE, 'Gemini Enterprise'], Msg.FROM_LC, jcount, Ent.USER)
  Ind.Increment()
  emails = []
  for user in users:
    j += 1
    user = normalizeEmailAddressOrUID(user)
    emails.append(user)
    entityActionPerformed([Ent.USER, user, Ent.LICENSE, 'Gemini Enterprise'], j, jcount)
  Ind.Decrement()
  if emails:
    _batchUpdateLicenses(service, project, location, subscription_id=None,
                         assigns=[], removes=emails, delete_record=delete_record)


# gam <UserTypeEntity> sync gelicense project <N> location <R> [subscriptionid <ID>] [deleterecord]
def syncGELicense(users):
  project, location = _getProjectAndLocation('sync', 'gelicense')
  location = _resolveLocation(project, location)
  subscription_id = None
  delete_record = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'subscriptionid':
      subscription_id = getString(Cmd.OB_STRING)
    elif myarg == 'deleterecord':
      delete_record = True
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  service = _buildGEService(project, location)
  subscription_id = _resolveSubscriptionId(service, project, location, subscription_id)

  # Resolve target user set from <UserTypeEntity>
  _, _, users = getEntityArgument(users)
  target_emails = set()
  for user in users:
    target_emails.add(normalizeEmailAddressOrUID(user))

  # Fetch current GE license state
  writeStdout('Fetching current GE license state...\n')
  current_licenses = _getAllLicenses(service, project, location)
  current_assigned = set()
  for lic in current_licenses:
    state = lic.get('licenseAssignmentState')
    if state == 'ASSIGNED':
      email = lic.get('userPrincipal', lic.get('name', '').split('/')[-1])
      current_assigned.add(email)

  to_assign = list(target_emails - current_assigned)
  to_remove = list(current_assigned - target_emails)

  writeStdout(f'Target users:      {len(target_emails)}\n')
  writeStdout(f'Currently assigned: {len(current_assigned)}\n')
  writeStdout(f'To assign:         {len(to_assign)}\n')
  writeStdout(f'To remove:         {len(to_remove)}\n')

  if not to_assign and not to_remove:
    writeStdout('Licenses are already in sync. No changes needed.\n')
    return

  _batchUpdateLicenses(service, project, location, subscription_id,
                       assigns=to_assign, removes=to_remove, delete_record=delete_record)
