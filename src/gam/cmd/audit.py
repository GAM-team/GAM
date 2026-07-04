"""GAM audit monitor commands — REMOVED.

The Email Audit API has been deprecated by Google. These commands
now print a deprecation notice and exit.
"""

from gam.var import Act
from gam.util.args import getChoice
from gam.util.output import systemErrorExit
from gam.constants import CMD_ACTION, CMD_FUNCTION, USAGE_ERROR_RC

LAST_SUPPORTED_VERSION = '7.46.07'

def _deprecatedCommand(api_name):
  systemErrorExit(
    USAGE_ERROR_RC,
    f'GAM no longer supports the legacy {api_name} API and this command. '
    f'If you must use this API you can install a copy of GAM {LAST_SUPPORTED_VERSION} '
    f'which is the last version to support this command.'
  )

def doCreateMonitor():
  _deprecatedCommand('Email Audit')

def doDeleteMonitor():
  _deprecatedCommand('Email Audit')

def doShowMonitors():
  _deprecatedCommand('Email Audit')

# Dispatch tables and routing (moved from __init__.py)
AUDIT_SUBCOMMANDS_WITH_OBJECTS = {
  'monitor':
    {'create': (Act.CREATE, doCreateMonitor),
     'delete': (Act.DELETE, doDeleteMonitor),
     'list': (Act.LIST, doShowMonitors),
    },
  }

def processAuditCommands():
  CL_subCommand = getChoice(list(AUDIT_SUBCOMMANDS_WITH_OBJECTS))
  CL_objectName = getChoice(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand])
  Act.Set(AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_ACTION])
  AUDIT_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CL_objectName][CMD_FUNCTION]()
