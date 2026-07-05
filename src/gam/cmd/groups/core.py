"""Shared constants and helpers for groups sub-package.

Extracted from groups.py to break the groups ↔ members circular import."""

from gam.constants import (
    GROUP_ALIAS_ATTRIBUTES,
    GROUP_ASSIST_CONTENT_ATTRIBUTES,
    GROUP_BASIC_ATTRIBUTES,
    GROUP_DEPRECATED_ATTRIBUTES,
    GROUP_DISCOVER_ATTRIBUTES,
    GROUP_MERGED_ATTRIBUTES,
    GROUP_MODERATE_CONTENT_ATTRIBUTES,
    GROUP_MODERATE_MEMBERS_ATTRIBUTES,
    GROUP_SETTINGS_ATTRIBUTES,
)
from gam.util.args import getString
from gam.util.errors import invalidChoiceExit
from gam.var import Cmd, Ent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GROUP_CIGROUP_ENTITYTYPE_MAP = {False: Ent.GROUP, True: Ent.CLOUD_IDENTITY_GROUP}

GROUP_MEMBER_TYPES_MAP = {
  'customer': Ent.TYPE_CUSTOMER,
  'group': Ent.TYPE_GROUP,
  'user': Ent.TYPE_USER,
}
ALL_GROUP_MEMBER_TYPES = {Ent.TYPE_CUSTOMER, Ent.TYPE_GROUP, Ent.TYPE_USER}

MEMBEROPTION_MEMBERNAMES = 0
MEMBEROPTION_NODUPLICATES = 1
MEMBEROPTION_RECURSIVE = 2
MEMBEROPTION_GETDELIVERYSETTINGS = 3
MEMBEROPTION_ISARCHIVED = 4
MEMBEROPTION_ISSUSPENDED = 5
MEMBEROPTION_INCLUDEDERIVEDMEMBERSHIP = 6
MEMBEROPTION_MATCHPATTERN = 7
MEMBEROPTION_DISPLAYMATCH = 8

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def GroupIsAbuseOrPostmaster(emailAddr):
  return emailAddr.startswith('abuse@') or emailAddr.startswith('postmaster@')

def mapGroupEmailForSettings(emailAddr):
  return emailAddr.replace('/', '%2F')

def getGroupAttrProperties(myarg):
  attrProperties = GROUP_BASIC_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_SETTINGS_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_ALIAS_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_DISCOVER_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_ASSIST_CONTENT_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_MODERATE_CONTENT_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_MODERATE_MEMBERS_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_MERGED_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  attrProperties = GROUP_DEPRECATED_ATTRIBUTES.get(myarg)
  if attrProperties is not None:
    return attrProperties
  return None

def getGroupMemberTypes(myarg, typesSet):
  if myarg in {'type', 'types'}:
    for gtype in getString(Cmd.OB_GROUP_TYPE_LIST).lower().replace(',', ' ').split():
      if gtype in GROUP_MEMBER_TYPES_MAP:
        typesSet.add(GROUP_MEMBER_TYPES_MAP[gtype])
      else:
        invalidChoiceExit(gtype, GROUP_MEMBER_TYPES_MAP, True)
  else:
    return False
  return True
