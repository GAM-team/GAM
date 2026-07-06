"""GAM display utilities — printing, warning, action, and entity display functions.

Thin wrappers around writeStdout/writeStderr that format entity values, actions,
and messages for user-facing output.  Depends only on gamlib modules and
util.output.
"""


from gamlib import settings as GC
from gamlib import state as GM
from gamlib import msgs as Msg


from gam.var import Act, Ent, Ind
from gam.util.args import escapeCRsNLs
from gam.util.output import (
    currentCountNL,
    formatKeyValueList,
    printWarningMessage,
    setSysExitRC,
    writeStderr,
    writeStdout,
)

# Constants duplicated from __init__.py to avoid circular imports.
ACTION_FAILED_RC = 50
ACTION_NOT_PERFORMED_RC = 51
BAD_REQUEST_RC = 53
ENTITY_DOES_NOT_EXIST_RC = 56
ENTITY_DUPLICATE_RC = 57
SERVICE_NOT_APPLICABLE_RC = 73
ERROR = 'ERROR'
FIRST_ITEM_MARKER = '%%first_item%%'
LAST_ITEM_MARKER = '%%last_item%%'
TOTAL_ITEMS_MARKER = '%%total_items%%'



# --- Warnings ---

def badRequestWarning(entityType, itemType, itemValue):
  printWarningMessage(BAD_REQUEST_RC,
                      f'{Msg.GOT} 0 {Ent.Plural(entityType)}: {Msg.INVALID} {Ent.Singular(itemType)} - {itemValue}')

def emptyQuery(query, entityType):
  return f'{Ent.Singular(Ent.QUERY)} ({query}) {Msg.NO_ENTITIES_FOUND.format(Ent.Plural(entityType))}'

def invalidQuery(query):
  return f'{Ent.Singular(Ent.QUERY)} ({query}) {Msg.INVALID}'

def invalidMember(query):
  if query:
    badRequestWarning(Ent.GROUP, Ent.QUERY, invalidQuery(query))
    return True
  return False

def invalidUserSchema(schema):
  if isinstance(schema, list):
    return f'{Ent.Singular(Ent.USER_SCHEMA)} ({",".join(schema)}) {Msg.INVALID}'
  return f'{Ent.Singular(Ent.USER_SCHEMA)} {schema}) {Msg.INVALID}'


# --- Service Not Enabled Warnings ---

def userServiceNotEnabledWarning(entityName, service, i=0, count=0):
  setSysExitRC(SERVICE_NOT_APPLICABLE_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [Ent.Singular(Ent.USER), entityName, Msg.SERVICE_NOT_ENABLED.format(service)],
                                 currentCountNL(i, count)))

def userAlertsServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Alerts', i, count)

def userAnalyticsServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Alerts', i, count)

def userCalServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Calendar', i, count)

def userChatServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Chat', i, count)

def userContactDelegateServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Contact Delegate', i, count)

def userDriveServiceNotEnabledWarning(user, errMessage, i=0, count=0):
#  if errMessage.find('Drive apps') == -1 and errMessage.find('Active session is invalid') == -1:
#    entityServiceNotApplicableWarning(Ent.USER, user, i, count)
  if errMessage.find('Drive apps') >= 0 or errMessage.find('Active session is invalid') >= 0:
    userServiceNotEnabledWarning(user, 'Drive', i, count)
  else:
    entityActionNotPerformedWarning([Ent.USER, user], errMessage, i, count)

def userKeepServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Keep', i, count)

def userGmailServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Gmail', i, count)

def userLookerStudioServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Looker Studio', i, count)

def userPeopleServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'People', i, count)

def userTasksServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'Tasks', i, count)

def userYouTubeServiceNotEnabledWarning(entityName, i=0, count=0):
  userServiceNotEnabledWarning(entityName, 'YouTube', i, count)


# --- Entity Warning Functions ---

def entityServiceNotApplicableWarning(entityType, entityName, i=0, count=0):
  setSysExitRC(SERVICE_NOT_APPLICABLE_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [Ent.Singular(entityType), entityName, Msg.SERVICE_NOT_APPLICABLE],
                                 currentCountNL(i, count)))

def entityDoesNotExistWarning(entityType, entityName, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [Ent.Singular(entityType), entityName, Msg.DOES_NOT_EXIST],
                                 currentCountNL(i, count)))

def entityListDoesNotExistWarning(entityValueList, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Msg.DOES_NOT_EXIST],
                                 currentCountNL(i, count)))

def entityDoesNotHaveItemWarning(entityValueList, i=0, count=0):
  setSysExitRC(ENTITY_DOES_NOT_EXIST_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Msg.DOES_NOT_EXIST],
                                 currentCountNL(i, count)))

def entityDuplicateWarning(entityValueList, i=0, count=0):
  setSysExitRC(ENTITY_DUPLICATE_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.Failed(), Msg.DUPLICATE],
                                 currentCountNL(i, count)))

def entityActionFailedWarning(entityValueList, errMessage, i=0, count=0):
  setSysExitRC(ACTION_FAILED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.Failed(), errMessage],
                                 currentCountNL(i, count)))

def entityModifierItemValueListActionFailedWarning(entityValueList, modifier, infoTypeValueList, errMessage, i=0, count=0):
  setSysExitRC(ACTION_FAILED_RC)
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier}', None]+Ent.FormatEntityValueList(infoTypeValueList)+[Act.Failed(), errMessage],
                                 currentCountNL(i, count)))

def entityModifierActionFailedWarning(entityValueList, modifier, errMessage, i=0, count=0):
  setSysExitRC(ACTION_FAILED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier}', Act.Failed(), errMessage],
                                 currentCountNL(i, count)))

def entityModifierNewValueActionFailedWarning(entityValueList, modifier, newValue, errMessage, i=0, count=0):
  setSysExitRC(ACTION_FAILED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier}', newValue, Act.Failed(), errMessage],
                                 currentCountNL(i, count)))

def entityNumEntitiesActionFailedWarning(entityType, entityName, itemType, itemCount, errMessage, i=0, count=0):
  setSysExitRC(ACTION_FAILED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [Ent.Singular(entityType), entityName,
                                  Ent.Choose(itemType, itemCount), itemCount,
                                  Act.Failed(), errMessage],
                                 currentCountNL(i, count)))

def entityActionNotPerformedWarning(entityValueList, errMessage, i=0, count=0):
  setSysExitRC(ACTION_NOT_PERFORMED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.NotPerformed(), errMessage],
                                 currentCountNL(i, count)))

def entityItemValueListActionNotPerformedWarning(entityValueList, infoTypeValueList, errMessage, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.NotPerformed(), '']+Ent.FormatEntityValueList(infoTypeValueList)+[errMessage],
                                 currentCountNL(i, count)))

def entityModifierItemValueListActionNotPerformedWarning(entityValueList, modifier, infoTypeValueList, errMessage, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.NotPerformed()} {modifier}', None]+Ent.FormatEntityValueList(infoTypeValueList)+[errMessage],
                                 currentCountNL(i, count)))

def entityNumEntitiesActionNotPerformedWarning(entityValueList, itemType, itemCount, errMessage, i=0, count=0):
  setSysExitRC(ACTION_NOT_PERFORMED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Ent.Choose(itemType, itemCount), itemCount, Act.NotPerformed(), errMessage],
                                 currentCountNL(i, count)))

def entityBadRequestWarning(entityValueList, errMessage, i=0, count=0):
  setSysExitRC(BAD_REQUEST_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[ERROR, errMessage],
                                 currentCountNL(i, count)))


# --- Getting / Paging Display ---

def printGettingAllAccountEntities(entityType, query='', qualifier='', accountType=None):
  if accountType is None:
    accountType = Ent.ACCOUNT
  if GC.Values[GC.SHOW_GETTINGS]:
    if query:
      Ent.SetGettingQuery(entityType, query)
    elif qualifier:
      Ent.SetGettingQualifier(entityType, qualifier)
    else:
      Ent.SetGetting(entityType)
    writeStderr(f'{Msg.GETTING_ALL} {Ent.PluralGetting()}{Ent.GettingPreQualifier()}{Ent.MayTakeTime(accountType)}\n')

def printGotAccountEntities(count):
  if GC.Values[GC.SHOW_GETTINGS]:
    writeStderr(f'{Msg.GOT} {count} {Ent.ChooseGetting(count)}{Ent.GettingPostQualifier()}\n')

def setGettingAllEntityItemsForWhom(entityItem, forWhom, query='', qualifier=''):
  if GC.Values[GC.SHOW_GETTINGS]:
    if query:
      Ent.SetGettingQuery(entityItem, query)
    elif qualifier:
      Ent.SetGettingQualifier(entityItem, qualifier)
    else:
      Ent.SetGetting(entityItem)
    Ent.SetGettingForWhom(forWhom)

def printGettingAllEntityItemsForWhom(entityItem, forWhom, i=0, count=0, query='', qualifier='', entityType=None):
  if GC.Values[GC.SHOW_GETTINGS]:
    setGettingAllEntityItemsForWhom(entityItem, forWhom, query=query, qualifier=qualifier)
    writeStderr(f'{Msg.GETTING_ALL} {Ent.PluralGetting()}{Ent.GettingPreQualifier()} {Msg.FOR} {forWhom}{Ent.MayTakeTime(entityType)}{currentCountNL(i, count)}')

def printGotEntityItemsForWhom(count):
  if GC.Values[GC.SHOW_GETTINGS]:
    writeStderr(f'{Msg.GOT} {count} {Ent.ChooseGetting(count)}{Ent.GettingPostQualifier()} {Msg.FOR} {Ent.GettingForWhom()}\n')

def printGettingEntityItem(entityType, entityItem, i=0, count=0):
  if GC.Values[GC.SHOW_GETTINGS]:
    writeStderr(f'{Msg.GETTING} {Ent.Singular(entityType)} {entityItem}{currentCountNL(i, count)}')

def printGettingEntityItemForWhom(entityItem, forWhom, i=0, count=0):
  if GC.Values[GC.SHOW_GETTINGS]:
    Ent.SetGetting(entityItem)
    Ent.SetGettingForWhom(forWhom)
    writeStderr(f'{Msg.GETTING} {Ent.PluralGetting()} {Msg.FOR} {forWhom}{currentCountNL(i, count)}')

def stderrEntityMessage(entityValueList, message, i=0, count=0):
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[message],
                                 currentCountNL(i, count)))

def getPageMessage(showFirstLastItems=False, showDate=None):
  if not GC.Values[GC.SHOW_GETTINGS]:
    return None
  pageMessage = f'{Msg.GOT} {TOTAL_ITEMS_MARKER} {{0}}'
  if showDate:
    pageMessage += f' on {showDate}'
  if showFirstLastItems:
    pageMessage += f': {FIRST_ITEM_MARKER} - {LAST_ITEM_MARKER}'
  else:
    pageMessage += '...'
  if GC.Values[GC.SHOW_GETTINGS_GOT_NL]:
    pageMessage += '\n'
  else:
    GM.Globals[GM.LAST_GOT_MSG_LEN] = 0
  return pageMessage

def getPageMessageForWhom(forWhom=None, showFirstLastItems=False, showDate=None, clearLastGotMsgLen=True):
  if not GC.Values[GC.SHOW_GETTINGS]:
    return None
  if forWhom:
    Ent.SetGettingForWhom(forWhom)
  pageMessage = f'{Msg.GOT} {TOTAL_ITEMS_MARKER} {{0}}{Ent.GettingPostQualifier()} {Msg.FOR} {Ent.GettingForWhom()}'
  if showDate:
    pageMessage += f' on {showDate}'
  if showFirstLastItems:
    pageMessage += f': {FIRST_ITEM_MARKER} - {LAST_ITEM_MARKER}'
  else:
    pageMessage += '...'
  if GC.Values[GC.SHOW_GETTINGS_GOT_NL]:
    pageMessage += '\n'
  elif clearLastGotMsgLen:
    GM.Globals[GM.LAST_GOT_MSG_LEN] = 0
  return pageMessage


# --- Print Utilities ---

def printLine(message):
  writeStdout(message+'\n')

def printBlankLine():
  writeStdout('\n')

def printKeyValueList(kvList):
  writeStdout(formatKeyValueList(Ind.Spaces(), kvList, '\n'))

def printKeyValueListWithCount(kvList, i, count):
  writeStdout(formatKeyValueList(Ind.Spaces(), kvList, currentCountNL(i, count)))

def printKeyValueDict(kvDict):
  for key, value in kvDict.items():
    writeStdout(formatKeyValueList(Ind.Spaces(), [key, value], '\n'))

def printKeyValueWithCRsNLs(key, value):
  if value.find('\n') >= 0 or value.find('\r') >= 0:
    if GC.Values[GC.SHOW_CONVERT_CR_NL]:
      printKeyValueList([key, escapeCRsNLs(value)])
    else:
      printKeyValueList([key, ''])
      Ind.Increment()
      printKeyValueList([Ind.MultiLineText(value)])
      Ind.Decrement()
  else:
    printKeyValueList([key, value])

def printJSONKey(key):
  writeStdout(formatKeyValueList(Ind.Spaces(), [key, None], ''))

def printJSONValue(value):
  writeStdout(formatKeyValueList(' ', [value], '\n'))

def printEntity(entityValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList),
                                 currentCountNL(i, count)))

def printEntityMessage(entityValueList, message, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[message],
                                 currentCountNL(i, count)))

def printEntitiesCount(entityType, entityList):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 [Ent.Plural(entityType), None if entityList is None else f'({len(entityList)})'],
                                 '\n'))

def printEntityKVList(entityValueList, infoKVList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+infoKVList,
                                 currentCountNL(i, count)))


# --- performAction / entityPerformAction ---

def performAction(entityType, entityValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 [f'{Act.ToPerform()} {Ent.Singular(entityType)} {entityValue}'],
                                 currentCountNL(i, count)))

def performActionNumItems(itemCount, itemType, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 [f'{Act.ToPerform()} {itemCount} {Ent.Choose(itemType, itemCount)}'],
                                 currentCountNL(i, count)))

def performActionModifierNumItems(modifier, itemCount, itemType, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 [f'{Act.ToPerform()} {modifier} {itemCount} {Ent.Choose(itemType, itemCount)}'],
                                 currentCountNL(i, count)))

def actionPerformedNumItems(itemCount, itemType, i=0, count=0):
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [f'{itemCount} {Ent.Choose(itemType, itemCount)} {Act.Performed()} '],
                                 currentCountNL(i, count)))

def actionFailedNumItems(itemCount, itemType, errMessage, i=0, count=0):
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [f'{itemCount} {Ent.Choose(itemType, itemCount)} {Act.Failed()}: {errMessage} '],
                                 currentCountNL(i, count)))

def actionNotPerformedNumItemsWarning(itemCount, itemType, errMessage, i=0, count=0):
  setSysExitRC(ACTION_NOT_PERFORMED_RC)
  writeStderr(formatKeyValueList(Ind.Spaces(),
                                 [Ent.Choose(itemType, itemCount), itemCount, Act.NotPerformed(), errMessage],
                                 currentCountNL(i, count)))

def entityPerformAction(entityValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()}'],
                                 currentCountNL(i, count)))

def entityPerformActionNumItems(entityValueList, itemCount, itemType, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {itemCount} {Ent.Choose(itemType, itemCount)}'],
                                 currentCountNL(i, count)))

def entityPerformActionModifierNumItems(entityValueList, modifier, itemCount, itemType, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier} {itemCount} {Ent.Choose(itemType, itemCount)}'],
                                 currentCountNL(i, count)))

def entityPerformActionNumItemsModifier(entityValueList, itemCount, itemType, modifier, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {itemCount} {Ent.Choose(itemType, itemCount)} {modifier}'],
                                 currentCountNL(i, count)))

def entityPerformActionSubItemModifierNumItems(entityValueList, subitemType, modifier, itemCount, itemType, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {Ent.Plural(subitemType)} {modifier} {itemCount} {Ent.Choose(itemType, itemCount)}'],
                                 currentCountNL(i, count)))

def entityPerformActionSubItemModifierNumItemsModifierNewValue(entityValueList, subitemType, modifier1, itemCount, itemType, modifier2, newValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+
                                 [f'{Act.ToPerform()} {Ent.Plural(subitemType)} {modifier1} {itemCount} {Ent.Choose(itemType, itemCount)} {modifier2}', newValue],
                                 currentCountNL(i, count)))

def entityPerformActionModifierNumItemsModifier(entityValueList, modifier1, itemCount, itemType, modifier2, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier1} {itemCount} {Ent.Choose(itemType, itemCount)} {modifier2}'],
                                 currentCountNL(i, count)))

def entityPerformActionModifierItemValueList(entityValueList, modifier, infoTypeValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier}', None]+Ent.FormatEntityValueList(infoTypeValueList),
                                 currentCountNL(i, count)))

def entityPerformActionModifierNewValue(entityValueList, modifier, newValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier}', newValue],
                                 currentCountNL(i, count)))

def entityPerformActionModifierNewValueItemValueList(entityValueList, modifier, newValue, infoTypeValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.ToPerform()} {modifier}', newValue]+Ent.FormatEntityValueList(infoTypeValueList),
                                 currentCountNL(i, count)))

def entityPerformActionItemValue(entityValueList, itemType, itemValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.ToPerform(), None, Ent.Singular(itemType), itemValue],
                                 currentCountNL(i, count)))

def entityPerformActionInfo(entityValueList, infoValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.ToPerform(), infoValue],
                                 currentCountNL(i, count)))


# --- entityActionPerformed / entityModifier ---

def entityActionPerformed(entityValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[Act.Performed()],
                                 currentCountNL(i, count)))

def entityActionPerformedMessage(entityValueList, message, i=0, count=0):
  if message:
    writeStdout(formatKeyValueList(Ind.Spaces(),
                                   Ent.FormatEntityValueList(entityValueList)+[Act.Performed(), message],
                                   currentCountNL(i, count)))
  else:
    writeStdout(formatKeyValueList(Ind.Spaces(),
                                   Ent.FormatEntityValueList(entityValueList)+[Act.Performed()],
                                   currentCountNL(i, count)))

def entityNumItemsActionPerformed(entityValueList, itemCount, itemType, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{itemCount} {Ent.Choose(itemType, itemCount)} {Act.Performed()}'],
                                 currentCountNL(i, count)))

def entityModifierActionPerformed(entityValueList, modifier, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.Performed()} {modifier}', None],
                                 currentCountNL(i, count)))

def entityModifierItemValueListActionPerformed(entityValueList, modifier, infoTypeValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.Performed()} {modifier}', None]+Ent.FormatEntityValueList(infoTypeValueList),
                                 currentCountNL(i, count)))

def entityModifierNewValueActionPerformed(entityValueList, modifier, newValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.Performed()} {modifier}', newValue],
                                 currentCountNL(i, count)))

def entityModifierNewValueItemValueListActionPerformed(entityValueList, modifier, newValue, infoTypeValueList, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.Performed()} {modifier}', newValue]+Ent.FormatEntityValueList(infoTypeValueList),
                                 currentCountNL(i, count)))

def entityModifierNewValueKeyValueActionPerformed(entityValueList, modifier, newValue, infoKey, infoValue, i=0, count=0):
  writeStdout(formatKeyValueList(Ind.Spaces(),
                                 Ent.FormatEntityValueList(entityValueList)+[f'{Act.Performed()} {modifier}', newValue, infoKey, infoValue],
                                 currentCountNL(i, count)))
