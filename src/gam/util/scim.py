"""SCIM 2.0 protocol utilities for Cloud Identity SCIM API.

Provides helpers for SCIM-specific behaviors that differ from standard
Google APIs: patch body construction, ID resolution, user/group body
builders, and resource accessor shortcuts.

All actual API calls go through the standard callGAPI() infrastructure.
"""

from gamlib import api as API
from gamlib import settings as GC
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI

# ---------------------------------------------------------------------------
# SCIM schema URNs
# ---------------------------------------------------------------------------
SCHEMA_USER = 'urn:ietf:params:scim:schemas:core:2.0:User'
SCHEMA_GROUP = 'urn:ietf:params:scim:schemas:core:2.0:Group'
SCHEMA_ENTERPRISE_USER = (
    'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User')
SCHEMA_CI_GROUP = (
    'urn:ietf:params:scim:schemas:extension:google:2.0:CloudIdentityGroup')
SCHEMA_PATCH_OP = 'urn:ietf:params:scim:api:messages:2.0:PatchOp'

# Max operations per PATCH request (documented in discovery doc)
MAX_USER_PATCH_OPS = 20
MAX_GROUP_PATCH_OPS = 2

# Valid type values per multi-valued attribute
VALID_EMAIL_TYPES = ('home', 'work', 'other')
VALID_PHONE_TYPES = ('home', 'work', 'mobile', 'fax', 'pager', 'other')
VALID_ADDRESS_TYPES = ('home', 'work', 'other')

# Map config setting values to API constants
_SCIM_VERSION_MAP = {
    'v1': API.CLOUDIDENTITYSCIM,
    'v1beta1': API.CLOUDIDENTITYSCIM_BETA,
    'v1alpha1': API.CLOUDIDENTITYSCIM_ALPHA,
}

def buildSCIMObject():
  """Build the SCIM service using the version from gam.cfg scim_api_version."""
  version = GC.Values.get(GC.SCIM_API_VERSION, 'v1')
  api = _SCIM_VERSION_MAP.get(version, API.CLOUDIDENTITYSCIM)
  return buildGAPIObject(api)


def scimUsers(scim):
  """Return the Users resource chain."""
  return scim.customers().v2().Users()


def scimGroups(scim):
  """Return the Groups resource chain."""
  return scim.customers().v2().Groups()


def scimSchemas(scim):
  """Return the Schemas resource chain."""
  return scim.customers().v2().Schemas()


def scimResourceTypes(scim):
  """Return the ResourceTypes resource chain."""
  return scim.customers().v2().ResourceTypes()


def scimServiceProviderConfig(scim):
  """Return the ServiceProviderConfig resource chain."""
  return scim.customers().v2().ServiceProviderConfig()


def customerId():
  """Return the Cxxx customer ID for SCIM API calls."""
  return GC.Values[GC.CUSTOMER_ID]


# ---------------------------------------------------------------------------
# SCIM Patch body builders
# ---------------------------------------------------------------------------

def buildPatchBody(operations):
  """Build a SCIM PatchOp request body with the required schema URN."""
  return {
      'schemas': [SCHEMA_PATCH_OP],
      'Operations': operations,
  }


def replaceOp(path, value):
  """Build a SCIM 'replace' operation."""
  return {'op': 'replace', 'path': path, 'value': value}


def addOp(path, value):
  """Build a SCIM 'add' operation."""
  return {'op': 'add', 'path': path, 'value': value}


def removeOp(path):
  """Build a SCIM 'remove' operation."""
  return {'op': 'remove', 'path': path}


def batchOps(operations, max_ops):
  """Yield operation batches respecting per-request limits.

  Groups: max 2 ops per PATCH. Users: max 20 ops per PATCH.
  """
  for i in range(0, len(operations), max_ops):
    yield operations[i:i + max_ops]


# ---------------------------------------------------------------------------
# User body builder
# ---------------------------------------------------------------------------

def newUserBody(email, name=None, enterprise=None, **kwargs):
  """Build a SCIM User creation body.

  No password field — SCIM users are passwordless.
  """
  body = {
      'schemas': [SCHEMA_USER],
      'userName': email,
  }
  if name:
    body['name'] = name
  if enterprise:
    body['schemas'].append(SCHEMA_ENTERPRISE_USER)
    body[SCHEMA_ENTERPRISE_USER] = enterprise
  body.update(kwargs)
  return body


# ---------------------------------------------------------------------------
# Group body builder
# ---------------------------------------------------------------------------

def newGroupBody(display_name, email, external_id=None,
                 description=None, members=None):
  """Build a SCIM Group creation body.

  Groups require the CloudIdentityGroup extension with an email field.
  """
  body = {
      'schemas': [SCHEMA_GROUP, SCHEMA_CI_GROUP],
      'displayName': display_name,
      SCHEMA_CI_GROUP: {'email': email},
  }
  if external_id:
    body['externalId'] = external_id
  if description:
    body[SCHEMA_CI_GROUP]['description'] = description
  if members:
    body['members'] = members
  return body


# ---------------------------------------------------------------------------
# ID resolution helpers
# ---------------------------------------------------------------------------

def resolveUserId(scim, email):
  """Resolve email address → SCIM user ID via filter lookup.

  Returns the SCIM id string, or None if not found.
  """
  result = callGAPI(scimUsers(scim), 'list',
                    customerId=customerId(),
                    filter=f'userName eq "{email}"')
  resources = result.get('resources', result.get('Resources', []))
  return resources[0]['id'] if resources else None


def resolveGroupId(scim, group_key):
  """Resolve group key → SCIM group ID.

  Accepts:
    id:abc123       → returns 'abc123' directly (raw SCIM ID)
    uid:ext-id-123  → searches by externalId filter
    <name>          → searches by displayName filter
  """
  if group_key.startswith('id:'):
    return group_key[3:]
  if group_key.startswith('uid:'):
    filt = f'externalId eq "{group_key[4:]}"'
  else:
    filt = f'displayName eq "{group_key}"'
  result = callGAPI(scimGroups(scim), 'list',
                    customerId=customerId(), filter=filt)
  resources = result.get('resources', result.get('Resources', []))
  return resources[0]['id'] if resources else None


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def flattenSCIMResource(resource, prefix=''):
  """Flatten nested SCIM resource into dot-notation dict for CSV output.

  Recurses into dicts with dot notation (e.g., 'name.givenName').
  Lists are serialized as semicolon-separated strings.
  """
  row = {}
  for key, value in resource.items():
    full_key = f'{prefix}.{key}' if prefix else key
    if isinstance(value, dict):
      row.update(flattenSCIMResource(value, full_key))
    elif isinstance(value, list):
      if value and isinstance(value[0], dict):
        # Array of objects — flatten each with index
        for i, item in enumerate(value):
          row.update(flattenSCIMResource(item, f'{full_key}.{i}'))
      else:
        row[full_key] = ';'.join(str(v) for v in value)
    else:
      row[full_key] = value
  return row
