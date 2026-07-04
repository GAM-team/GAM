"""GAM Tag Manager account, container, workspace, tag, and permission management."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPIpages
from gam.util.args import (
    checkArgumentPresent,
    getArgument,
    getBoolean,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printLine,
)
from gam.util.entity import getEntityArgument, getEntityList


TAGMANAGER_PARAMETERS = {
  Ent.TAGMANAGER_ACCOUNT: {'api': API.TAGMANAGER, 'respType': 'account', 'parentEntityType': None,
                           'name': 'name', 'idList': ['accountId']},
  Ent.TAGMANAGER_CONTAINER: {'api': API.TAGMANAGER, 'respType': 'container', 'parentEntityType': Ent.TAGMANAGER_ACCOUNT,
                             'name': 'name', 'idList': ['accountId', 'containerId']},
  Ent.TAGMANAGER_WORKSPACE: {'api': API.TAGMANAGER, 'respType': 'workspace', 'parentEntityType': Ent.TAGMANAGER_CONTAINER,
                             'name': 'name', 'idList': ['accountId', 'containerId', 'workspaceId']},
  Ent.TAGMANAGER_TAG: {'api': API.TAGMANAGER, 'respType': 'tag', 'parentEntityType': Ent.TAGMANAGER_WORKSPACE,
                       'name': 'name', 'idList': ['accountId', 'containerId', 'workspaceId', 'tagId']},
  Ent.TAGMANAGER_PERMISSION: {'api': API.TAGMANAGER_USERS, 'respType': 'userPermission', 'parentEntityType': Ent.TAGMANAGER_ACCOUNT,
                             'name': 'emailAddress', 'idList': ['accountId']},
  }

def printShowTagManagerObjects(users, entityType):
  csvPF = CSVPrintFile(['User']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  if entityType == Ent.TAGMANAGER_ACCOUNT:
    kwargs = {'includeGoogleTags': False}
    parentList = [None]
  else:
    kwargs = {'parent': None}
    if not checkArgumentPresent('select'):
      parentList = getString(Cmd.OB_TAGMANAGER_PATH_LIST).replace(',', ' ').split()
    else:
      parentList = getEntityList(Cmd.OB_TAGMANAGER_PATH_LIST)
  parameters = TAGMANAGER_PARAMETERS[entityType]
  if csvPF:
    csvPF.AddTitles([parameters['name'], 'path'])
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif entityType == Ent.TAGMANAGER_ACCOUNT and myarg == 'includegoogletags':
      kwargs['includeGoogleTags'] = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, svc = buildGAPIServiceObject(parameters['api'], user, i, count)
    if not svc:
      continue
    if entityType == Ent.TAGMANAGER_ACCOUNT:
      svc = svc.accounts()
    elif entityType == Ent.TAGMANAGER_CONTAINER:
      svc = svc.accounts().containers()
    elif entityType == Ent.TAGMANAGER_WORKSPACE:
      svc = svc.accounts().containers().workspaces()
    elif entityType == Ent.TAGMANAGER_TAG:
      svc = svc.accounts().containers().workspaces().tags()
    else: #elif entityType == Ent.TAGMANAGER_PERMISSION:
      svc = svc.accounts().user_permissions()
    jcount = len(parentList)
    j = 0
    for parent in parentList:
      j += 1
      if entityType == Ent.TAGMANAGER_ACCOUNT:
        printGettingAllEntityItemsForWhom(entityType, user, i, count)
      else:
        kwargs['parent'] = parent
        qualifier = f' for {Ent.Singular(parameters["parentEntityType"])}: {parent}'
        printGettingAllEntityItemsForWhom(entityType, user, i, count, qualifier=qualifier)
      try:
        results = callGAPIpages(svc, 'list', parameters['respType'],
                                 pageMessage=getPageMessageForWhom(),
                                 throwReasons=GAPI.TAGMANAGER_THROW_REASONS,
                                 **kwargs)
      except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.USER, user, entityType, kwargs['parent']], str(e), j, jcount)
        continue
      if not csvPF:
        kcount = len(results)
        if not  FJQC.formatJSON:
          entityPerformActionNumItems([Ent.USER, user], kcount, entityType, j, jcount)
        Ind.Increment()
        k = 0
        for result in results:
          k += 1
          if not  FJQC.formatJSON:
            printEntity([entityType, result['path']], k, kcount)
            Ind.Increment()
            printKeyValueList([parameters['name'], result.pop(parameters['name'])])
            for tmid in parameters['idList']:
              printKeyValueList([tmid, result.pop(tmid)])
            showJSON(None, result)
            Ind.Decrement()
          else:
            printLine(json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=True))
        Ind.Decrement()
      elif results:
        for result in results:
          baseRow = {'User': user}
          for tmid in parameters['idList']:
            baseRow[tmid] = result.pop(tmid)
          row = flattenJSON(result, flattened=baseRow)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            row = {'User': user, parameters['name']: result[parameters['name']], 'path': result['path']}
            row['JSON'] = json.dumps(cleanJSON(result), ensure_ascii=False, sort_keys=True)
            csvPF.WriteRowNoFilter(row)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile(Ent.Plural(entityType))

# gam <UserTypeEntity> show tagmanageraccounts
#	[includegoogletags [<Boolean>]]
#	[formatjson]
# gam <UserTypeEntity> print tagmanagerccounts [todrive <ToDriveAttribute>*]
#	[includegoogletags [<Boolean>]]
#	[formatjson [quotechar <Character>]]
def printShowTagManagerAccounts(users):
  printShowTagManagerObjects(users, Ent.TAGMANAGER_ACCOUNT)

# gam <UserTypeEntity> show tagmanagercontainers <TagManagerAccountPathEntity>
#	[formatjson]
# gam <UserTypeEntity> print tagmanagercontainers <TagManagerAccountPathEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def printShowTagManagerContainers(users):
  printShowTagManagerObjects(users, Ent.TAGMANAGER_CONTAINER)

# gam <UserTypeEntity> show tagmanagerworkspaces <TagManagerContainerPathEntity>
#	[formatjson]
# gam <UserTypeEntity> print tagmanagerworkspaces <TagManagerContainerPathEntity>
#	[formatjson [quotechar <Character>]]
def printShowTagManagerWorkspaces(users):
  printShowTagManagerObjects(users, Ent.TAGMANAGER_WORKSPACE)

# gam <UserTypeEntity> show tagmanagertags <TagManagerWorkspacePathEntity>
#	[formatjson]
# gam <UserTypeEntity> print tagmanagertags <TagManagerWorkspacePathEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def printShowTagManagerTags(users):
  printShowTagManagerObjects(users, Ent.TAGMANAGER_TAG)

# gam <UserTypeEntity> show tagmanagerpermissions <TagManagerAccountPathEntity>
#	[formatjson]
# gam <UserTypeEntity> print tagmanagerpermissions <TagManagerAccountPathEntity> [todrive <ToDriveAttribute>*]
#	[formatjson [quotechar <Character>]]
def printShowTagManagerPermissions(users):
  printShowTagManagerObjects(users, Ent.TAGMANAGER_PERMISSION)
