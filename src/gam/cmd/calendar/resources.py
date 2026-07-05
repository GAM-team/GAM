"""GAM calendar resources commands."""


from gam.var import Act, Cmd
from gam.util.args import getChoice, getStringReturnInList
from gam.util.entity import getEntityList
from gam.constants import CMD_ACTION, CMD_FUNCTION

from gam.cmd.calendar.acls import *
from gam.cmd.calendar.core import _validateResourceId as _validateResourceId  # re-export for backward compat

# Resource command sub-commands
RESOURCE_SUBCOMMANDS_WITH_OBJECTS = {
  'add':
    (Act.ADD,
     {Cmd.ARG_CALENDARACL:	doResourceCreateCalendarACLs,
     }
    ),
  'create':
    (Act.CREATE,
     {Cmd.ARG_CALENDARACL:	doResourceCreateCalendarACLs,
     }
    ),
  'update':
    (Act.UPDATE,
     {Cmd.ARG_CALENDARACL:	doResourceUpdateCalendarACLs,
     }
    ),
  'delete':
    (Act.DELETE,
     {Cmd.ARG_CALENDARACL:	doResourceDeleteCalendarACLs,
     }
    ),
  'info':
    (Act.INFO,
     {Cmd.ARG_CALENDARACL:	doResourceInfoCalendarACLs,
     }
    ),
  'print':
    (Act.PRINT,
     {Cmd.ARG_CALENDARACL:	doResourcePrintShowCalendarACLs,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_CALENDARACL:	doResourcePrintShowCalendarACLs,
     }
    ),
  }

# Resource sub-command aliases
RESOURCE_SUBCOMMAND_ALIASES = {
  'del':			'delete',
  }

RESOURCE_SUBCOMMANDS_OBJECT_ALIASES = {
  Cmd.ARG_ACL:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_ACLS:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_CALENDARACLS:		Cmd.ARG_CALENDARACL,
  }

def executeResourceCommands(resourceEntity):
  CL_subCommand = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS, choiceAliases=RESOURCE_SUBCOMMAND_ALIASES)
  Act.Set(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION], choiceAliases=RESOURCE_SUBCOMMANDS_OBJECT_ALIASES)
  RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](resourceEntity)

def processResourceCommands():
  executeResourceCommands(getStringReturnInList(Cmd.OB_RESOURCE_ID))

def processResourcesCommands():
  executeResourceCommands(getEntityList(Cmd.OB_RESOURCE_ENTITY))
