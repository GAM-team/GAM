"""GAM calendar resources commands."""


from gam.var import Act, Cmd
from gam.util.args import getChoice, getStringReturnInList
from gam.util.entity import getEntityList
from gam.constants import CMD_ACTION, CMD_FUNCTION

from gam.cmd.calendar.acls import *
from gam.cmd.calendar.core import _validateResourceId as _validateResourceId  # re-export for backward compat

def executeResourceCommands(resourceEntity):
  from gam.cmd.calendar.dispatch import RESOURCE_SUBCOMMANDS_WITH_OBJECTS, RESOURCE_SUBCOMMAND_ALIASES, RESOURCE_SUBCOMMANDS_OBJECT_ALIASES  # deferred: circular
  CL_subCommand = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS, choiceAliases=RESOURCE_SUBCOMMAND_ALIASES)
  Act.Set(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION], choiceAliases=RESOURCE_SUBCOMMANDS_OBJECT_ALIASES)
  RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](resourceEntity)

def processResourceCommands():
  executeResourceCommands(getStringReturnInList(Cmd.OB_RESOURCE_ID))

def processResourcesCommands():
  executeResourceCommands(getEntityList(Cmd.OB_RESOURCE_ENTITY))

