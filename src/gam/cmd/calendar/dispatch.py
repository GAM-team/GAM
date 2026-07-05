"""GAM calendar dispatch tables."""

from gam.var import Act, Cmd
from gam.constants import CMD_ACTION, CMD_FUNCTION
from gam.util.entity import getEntityList
from gam.cmd.calendar.acls import *
from gam.cmd.calendar.events import *
from gam.cmd.calendar.calendars import *
from gam.cmd.calendar.settings import *
from gam.cmd.calendar.status import *
from gam.cmd.calendar.resources import *

CALENDAR_SUBCOMMANDS = {
  'showacl': 			(Act.SHOW, doCalendarsPrintShowACLs),
  'printacl': 			(Act.PRINT, doCalendarsPrintShowACLs),
  'addevent': 			(Act.ADD, doCalendarsCreateEvent),
  'deleteevent': 		(Act.DELETE, doCalendarsDeleteEventsOld),
  'moveevent': 			(Act.MOVE, doCalendarsMoveEventsOld),
  'updateevent': 		(Act.UPDATE, doCalendarsUpdateEventsOld),
  'printevents': 		(Act.PRINT, doCalendarsPrintShowEvents),
  'wipe': 			(Act.WIPE, doCalendarsWipeEvents),
  'modify': 			(Act.MODIFY, doCalendarsModifySettings),
  }

CALENDAR_OLDACL_SUBCOMMANDS = {
  'add': 			(Act.ADD, doCalendarsCreateACL),
  'create': 			(Act.CREATE, doCalendarsCreateACL),
  'delete': 			(Act.DELETE, doCalendarsDeleteACL),
  'update': 			(Act.UPDATE, doCalendarsUpdateACL),
  }

# Calendar sub-command aliases
CALENDAR_OLDACL_SUBCOMMAND_ALIASES = {
  'del':			'delete',
  }

# Calendars command sub-commands with objects
CALENDARS_SUBCOMMANDS_WITH_OBJECTS = {
  'add':
    (Act.ADD,
     {Cmd.ARG_CALENDARACL:	doCalendarsCreateACLs,
      Cmd.ARG_EVENT:		doCalendarsCreateEvent,
     }
    ),
  'create':
    (Act.CREATE,
     {Cmd.ARG_CALENDARACL:	doCalendarsCreateACLs,
      Cmd.ARG_EVENT:		doCalendarsCreateEvent,
     }
    ),
  'delete':
    (Act.DELETE,
     {Cmd.ARG_CALENDARACL:	doCalendarsDeleteACLs,
      Cmd.ARG_EVENT:		doCalendarsDeleteEvents,
     }
    ),
  'empty':
    (Act.EMPTY,
     {Cmd.ARG_CALENDARTRASH:	doCalendarsEmptyTrash,
     }
    ),
  'import':
    (Act.IMPORT,
     {Cmd.ARG_EVENT:		doCalendarsImportEvent,
     }
    ),
  'info':
    (Act.INFO,
     {Cmd.ARG_CALENDARACL:	doCalendarsInfoACLs,
      Cmd.ARG_EVENT:		doCalendarsInfoEvents,
     }
    ),
  'move':
    (Act.MOVE,
     {Cmd.ARG_EVENT:		doCalendarsMoveEvents,
     }
    ),
  'print':
    (Act.PRINT,
     {Cmd.ARG_CALENDARACL:	doCalendarsPrintShowACLs,
      Cmd.ARG_EVENT:		doCalendarsPrintShowEvents,
      Cmd.ARG_SETTINGS:		doCalendarsPrintShowSettings,
     }
    ),
  'purge':
    (Act.PURGE,
     {Cmd.ARG_EVENT:		doCalendarsPurgeEvents,
     }
    ),
  'show':
    (Act.SHOW,
     {Cmd.ARG_CALENDARACL:	doCalendarsPrintShowACLs,
      Cmd.ARG_EVENT:		doCalendarsPrintShowEvents,
      Cmd.ARG_SETTINGS:		doCalendarsPrintShowSettings,
     }
    ),
  'transfer':
    (Act.TRANSFER,
     {Cmd.ARG_OWNERSHIP:	doCalendarsTransferOwnership,
     }
    ),
  'update':
    (Act.UPDATE,
     {Cmd.ARG_CALENDARACL:	doCalendarsUpdateACLs,
      Cmd.ARG_EVENT:		doCalendarsUpdateEvents,
     }
    ),
  'wipe':
    (Act.WIPE,
     {Cmd.ARG_EVENT:		doCalendarsWipeEvents,
     }
    ),
  }

CALENDARS_SUBCOMMANDS_OBJECT_ALIASES = {
  Cmd.ARG_ACL:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_ACLS:			Cmd.ARG_CALENDARACL,
  Cmd.ARG_CALENDARACLS:		Cmd.ARG_CALENDARACL,
  Cmd.ARG_EVENTS:		Cmd.ARG_EVENT,
  }

def processCalendarsCommands():
  calendarList = getEntityList(Cmd.OB_EMAIL_ADDRESS_ENTITY)
  CL_subCommand = getChoice(CALENDAR_SUBCOMMANDS, defaultChoice=None)
  if CL_subCommand:
    Act.Set(CALENDAR_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
    CALENDAR_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](calendarList)
    return
  CL_subCommand = getChoice(CALENDAR_OLDACL_SUBCOMMANDS, choiceAliases=CALENDAR_OLDACL_SUBCOMMAND_ALIASES, defaultChoice=None)
  if CL_subCommand:
    Act.Set(CALENDAR_OLDACL_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
    CL_objectName = getChoice([Cmd.ARG_CALENDARACL, Cmd.ARG_EVENT], choiceAliases=CALENDARS_SUBCOMMANDS_OBJECT_ALIASES, defaultChoice=None)
    if not CL_objectName:
      CALENDAR_OLDACL_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](calendarList)
    else:
      CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](calendarList)
    return
  CL_subCommand = getChoice(CALENDARS_SUBCOMMANDS_WITH_OBJECTS)
  Act.Set(CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_ACTION])
  CL_objectName = getChoice(CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION], choiceAliases=CALENDARS_SUBCOMMANDS_OBJECT_ALIASES)
  CALENDARS_SUBCOMMANDS_WITH_OBJECTS[CL_subCommand][CMD_FUNCTION][CL_objectName](calendarList)


# Dispatch tables and routing (moved from __init__.py)
# Additional imports for dispatch
from gam.util.args import getChoice

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

