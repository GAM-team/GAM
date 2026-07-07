"""Gemini Enterprise license management commands.

Uses the Discovery Engine API (discoveryengine.googleapis.com) to manage
GE licenses. Authenticates as the GAM service account (no DwD).

Commands:
  gam show geuserstore project <N> location <R>
  gam show|print gesubscriptions project <N> location <R> [todrive]
  gam show|print gelicenses project <N> location <R> [todrive]
  gam create gelicense project <N> location <R> user <Email> [subscriptionid <ID>]
  gam delete gelicense project <N> location <R> user <Email> [deleterecord]
  gam sync gelicenses project <N> location <R> csvfile <F> column <C>
                       [subscriptionid <ID>] [deleterecord]
"""

import csv
import time

from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gamlib import state as GM

from gam.var import Act, Cmd

from gam.util.api import buildGAPIObjectGE
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
    getString,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import (
    printKeyValueList,
)
from gam.util.errors import systemErrorExit
from gam.util.output import stderrErrorMsg, writeStderr, writeStdout

from gam.constants import GOOGLE_API_ERROR_RC

# The API uses 'default_user_store' for the top-level user store
USER_STORE_ID = 'default_user_store'

# Max page size for userLicenses.list
GE_LICENSE_PAGE_SIZE = 1000

GE_THROW_REASONS = [GAPI.PERMISSION_DENIED, GAPI.NOT_FOUND, GAPI.FORBIDDEN]


# --- Internal Helpers ---

def _getProjectAndLocation(action, entity):
  """Parse required project and location arguments from the command line."""
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
  if not project or not location:
    systemErrorExit(GOOGLE_API_ERROR_RC, Msg.GE_PROJECT_LOCATION_REQUIRED.format(action, entity))
  return project, location


def _buildGEService(project, location):
  """Build the Discovery Engine service client."""
  return buildGAPIObjectGE(project, location)


def _getGEParent(project, location):
  """Build the userStore parent path."""
  return f'projects/{project}/locations/{location}/userStores/{USER_STORE_ID}'


def _getLicenseConfigsParent(project, location):
  """Build the licenseConfigs parent path."""
  return f'projects/{project}/locations/{location}'


def _handleGEError(e, project):
  """Handle common GE API errors with actionable IAM guidance."""
  sa_email = GM.Globals.get(GM.ADMIN, 'unknown')
  if isinstance(e, GAPI.permissionDenied) or isinstance(e, GAPI.forbidden):
    stderrErrorMsg(Msg.GE_IAM_PERMISSION_DENIED.format(sa_email, project))
    stderrErrorMsg(Msg.GE_API_NOT_ENABLED.format(project))
    systemErrorExit(GOOGLE_API_ERROR_RC, '')
  elif isinstance(e, GAPI.notFound):
    stderrErrorMsg(Msg.GE_USERSTORE_NOT_FOUND.format(project))
    systemErrorExit(GOOGLE_API_ERROR_RC, '')
  raise


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
  """Validate or auto-discover the subscription ID."""
  if provided_id:
    return provided_id

  writeStdout('No subscriptionid provided. Checking available subscriptions...\n')
  configs = _fetchSubscriptions(service, project, location)

  if not configs:
    systemErrorExit(GOOGLE_API_ERROR_RC,
                    'No subscriptions found for this project and location.')

  sub_ids = [config.get('name', '').split('/')[-1] for config in configs]

  if len(sub_ids) == 1:
    writeStdout(f'Auto-selected subscription: {sub_ids[0]}\n')
    return sub_ids[0]

  systemErrorExit(GOOGLE_API_ERROR_RC,
                  f'Multiple subscriptions found ({", ".join(sub_ids)}). '
                  f'Specify one with subscriptionid <ID>.')
  return None  # unreachable


def _batchUpdateLicenses(service, project, location, subscription_id, assigns, removes, delete_record):
  """Perform a batch license update (assign and/or remove)."""
  parent = _getGEParent(project, location)

  user_licenses = []
  if assigns and subscription_id:
    license_config_path = f'projects/{project}/locations/{location}/licenseConfigs/{subscription_id}'
    for email in assigns:
      user_licenses.append({
        'userPrincipal': email,
        'licenseConfig': license_config_path,
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


# --- Public Command Functions ---

# gam show geuserstore project <Number> location <Region>
def doShowGEUserStore():
  project, location = _getProjectAndLocation('show', 'geuserstore')
  checkForExtraneousArguments()
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


# gam create gelicense project <N> location <R> user <Email> [subscriptionid <ID>]
def doCreateGELicense():
  project, location = _getProjectAndLocation('create', 'gelicense')
  emails = []
  subscription_id = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'user':
      emails.append(getString(Cmd.OB_EMAIL_ADDRESS))
    elif myarg == 'subscriptionid':
      subscription_id = getString(Cmd.OB_STRING)
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  if not emails:
    systemErrorExit(GOOGLE_API_ERROR_RC, 'At least one user email is required.')
  service = _buildGEService(project, location)
  subscription_id = _resolveSubscriptionId(service, project, location, subscription_id)
  writeStdout(f'Assigning GE license to {len(emails)} user(s)...\n')
  _batchUpdateLicenses(service, project, location, subscription_id,
                       assigns=emails, removes=[], delete_record=False)


# gam delete gelicense project <N> location <R> user <Email> [deleterecord]
def doDeleteGELicense():
  project, location = _getProjectAndLocation('delete', 'gelicense')
  emails = []
  delete_record = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'user':
      emails.append(getString(Cmd.OB_EMAIL_ADDRESS))
    elif myarg == 'deleterecord':
      delete_record = True
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  if not emails:
    systemErrorExit(GOOGLE_API_ERROR_RC, 'At least one user email is required.')
  service = _buildGEService(project, location)
  action = 'Removing and deleting' if delete_record else 'Removing'
  writeStdout(f'{action} GE license from {len(emails)} user(s)...\n')
  _batchUpdateLicenses(service, project, location, subscription_id=None,
                       assigns=[], removes=emails, delete_record=delete_record)


# gam sync gelicenses project <N> location <R> csvfile <F> column <C>
#                       [subscriptionid <ID>] [deleterecord]
def doSyncGELicenses():
  project, location = _getProjectAndLocation('sync', 'gelicenses')
  csv_file = None
  column_name = None
  subscription_id = None
  delete_record = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'csvfile':
      csv_file = getString(Cmd.OB_FILE_NAME)
    elif myarg == 'column':
      column_name = getString(Cmd.OB_STRING)
    elif myarg == 'subscriptionid':
      subscription_id = getString(Cmd.OB_STRING)
    elif myarg == 'deleterecord':
      delete_record = True
    else:
      systemErrorExit(GOOGLE_API_ERROR_RC, f'Unknown argument: {myarg}')
  if not csv_file or not column_name:
    systemErrorExit(GOOGLE_API_ERROR_RC, 'csvfile and column arguments are required.')

  # Read target emails from CSV
  target_emails = set()
  try:
    with open(csv_file, encoding='utf-8') as f:
      reader = csv.DictReader(f)
      if column_name not in reader.fieldnames:
        systemErrorExit(GOOGLE_API_ERROR_RC,
                        f'Column "{column_name}" not found in CSV. '
                        f'Available: {", ".join(reader.fieldnames)}')
      for row in reader:
        email = row[column_name].strip()
        if email:
          target_emails.add(email)
  except FileNotFoundError:
    systemErrorExit(GOOGLE_API_ERROR_RC, f'CSV file not found: {csv_file}')

  service = _buildGEService(project, location)
  subscription_id = _resolveSubscriptionId(service, project, location, subscription_id)

  # Fetch current state
  writeStdout('Fetching current GE license state...\n')
  current_licenses = _getAllLicenses(service, project, location)
  current_emails = set()
  for lic in current_licenses:
    state = lic.get('licenseAssignmentState')
    if delete_record or state == 'ASSIGNED':
      name = lic.get('name', '')
      email = lic.get('userPrincipal', name.split('/')[-1])
      current_emails.add(email)

  to_assign = list(target_emails - current_emails)
  to_remove = list(current_emails - target_emails)

  writeStdout(f'CSV target users:  {len(target_emails)}\n')
  writeStdout(f'Currently active:  {len(current_emails)}\n')
  writeStdout(f'To assign:         {len(to_assign)}\n')
  writeStdout(f'To remove:         {len(to_remove)}\n')

  if not to_assign and not to_remove:
    writeStdout('Licenses are already in sync. No changes needed.\n')
    return

  _batchUpdateLicenses(service, project, location, subscription_id,
                       assigns=to_assign, removes=to_remove, delete_record=delete_record)
