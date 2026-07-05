"""GAM calendar resources commands."""
        

from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api_call import callGAPI
from gam.util.args import getChoice
from gam.util.entity import getEntityList

from gam.cmd.calendar.acls import *

def _validateResourceId(cd, resourceId, i, count, exitOnNotFound):
  try:
    return callGAPI(cd.resources().calendars(), 'get',
                    throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                    customer=GC.Values[GC.CUSTOMER_ID], calendarResourceId=resourceId, fields='resourceEmail')['resourceEmail']
  except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
    if exitOnNotFound:
      entityDoesNotExistExit(Ent.RESOURCE_CALENDAR, resourceId, i, count)
    checkEntityAFDNEorAccessErrorExit(cd, Ent.RESOURCE_CALENDAR, resourceId, i, count)
    return None

def executeResourceCommands(resourceEntity):
  CL_subCommand = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS, choiceAliases=RESOURCE_SUBCOMMAND_ALIASES)
  Act.Set(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION], choiceAliases=RESOURCE_SUBCOMMANDS_OBJECT_ALIASES)
  RESOURCE_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](resourceEntity)

def processResourceCommands():
  executeResourceCommands(getStringReturnInList(Cmd.OB_RESOURCE_ID))

def processResourcesCommands():
  executeResourceCommands(getEntityList(Cmd.OB_RESOURCE_ENTITY))

