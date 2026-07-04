"""GAM Google Tasks management."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    checkForExtraneousArguments,
    escapeCRsNLs,
    getArgument,
    getBoolean,
    getCharSet,
    getChoice,
    getString,
    getStringWithCRsNLs,
    getTimeOrDeltaFromNow,
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
    entityActionPerformed,
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printEntity,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItemForWhom,
    printKeyValueList,
    printLine,
    userTasksServiceNotEnabledWarning,
)
from gam.util.entity import _validateUserGetObjectList, getEntityArgument, getUserObjectEntity
from gam.util.errors import usageErrorExit
from gam.util.fileio import readFile, setFilePath
from gam.util.output import writeStdout


def verifyTasksServiceEnabled(svc, user, i, count):
  try:
    callGAPIpages(svc.tasklists(), 'list', 'items',
                  throwReasons=GAPI.TASKLIST_THROW_REASONS,
                  maxItems=1)
    return True
  except (GAPI.notFound, GAPI.badRequest, GAPI.invalid):
    userTasksServiceNotEnabledWarning(user, i, count)
    return False

def getTaskLists(svc, user, i, count):
  try:
    results = callGAPIpages(svc.tasklists(), 'list', 'items',
                            pageMessage=getPageMessageForWhom(),
                            throwReasons=GAPI.TASKLIST_THROW_REASONS,
                            maxResults=100)
  except (GAPI.badRequest, GAPI.invalid) as e:
    entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, None], str(e), i, count)
    results = None
  except GAPI.notFound:
    userTasksServiceNotEnabledWarning(user, i, count)
    results = None
  return results

def getTaskListIDfromTitle(svc, userTasklists, title, user, i, count):
  if userTasklists is None:
    printGettingEntityItemForWhom(Ent.TASKLIST, user, i, count)
    userTasklists = getTaskLists(svc, user, i, count)
    if userTasklists is None:
      return None, None
  for userTasklist in userTasklists:
    if userTasklist['title'] == title:
      return userTasklists, userTasklist['id']
  return userTasklists, None

TASK_SKIP_OBJECTS = ['selfLink']
TASK_TIME_OBJECTS = ['completed', 'updated']

def _showTask(tasklist, task, j=0, jcount=0, FJQC=None, compact=False):
  task['tasklistId'] = tasklist
  task['taskId'] = f"{tasklist}/{task['id']}"
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(task, skipObjects=TASK_SKIP_OBJECTS, timeObjects=TASK_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.TASK, task['taskId']], j, jcount)
  Ind.Increment()
  showJSON(None, task, skipObjects=TASK_SKIP_OBJECTS+['notes'], timeObjects=TASK_TIME_OBJECTS)
  field = 'notes'
  if field in task:
    if not compact:
      printKeyValueList([field, None])
      Ind.Increment()
      printKeyValueList([Ind.MultiLineText(task[field])])
      Ind.Decrement()
    else:
      printKeyValueList(['notes', escapeCRsNLs(task[field])])
  Ind.Decrement()

TASK_STATUS_MAP = {
  'completed': 'completed',
  'needsaction': 'needsAction',
  }

def getTaskAttribute(myarg, body):
  if myarg == 'title':
    body[myarg] = getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'notes':
    body[myarg] = getStringWithCRsNLs()
  elif myarg == 'status':
    body[myarg] = getChoice(TASK_STATUS_MAP, mapChoice=True)
  elif myarg == 'due':
    body[myarg] = getTimeOrDeltaFromNow()
  else:
    return False
  return True

def getTaskMoveAttribute(myarg, kwargs):
  if myarg == 'parent':
    kwargs[myarg] = getString(Cmd.OB_TASK_ID)
  elif myarg == 'previous':
    kwargs[myarg] = getString(Cmd.OB_TASK_ID)
  else:
    return False
  return True

# gam <UserTypeEntity> create task <TasklistEntity>
#	<TaskAttribute>* [parent <TaskID>] [previous <TaskID>]
#	[compact|formatjson|returnidonly]
# gam <UserTypeEntity> update task <TasklistIDTaskIDEntity>
#	<TaskAttribute>*
#	[compact|formatjson]
# gam <UserTypeEntity> info task <TasklistIDTaskIDEntity>
#	[compact|formatjson]
# gam <UserTypeEntity> delete task <TasklistIDTaskIDEntity>
# gam <UserTypeEntity> move task <TasklistIDTaskIDEntity>
#	[parent <TaskID>] [previous <TaskID>]
#	[compact|formatjson]
def processTasks(users):
  action = Act.Get()
  if action != Act.CREATE:
    tasklistTaskEntity = getUserObjectEntity(Cmd.OB_TASKLIST_ID_TASK_ID_ENTITY, Ent.TASK, shlexSplit=True)
  else:
    tasklistTaskEntity = getUserObjectEntity(Cmd.OB_TASKLIST_ID_ENTITY, Ent.TASK, shlexSplit=True)
  if action in {Act.DELETE, Act.CLEAR}:
    FJQC = None
    checkForExtraneousArguments()
  else:
    FJQC = FormatJSONQuoteChar()
    body = {}
    kwargs = {}
    compact = returnIdOnly = False
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if action in {Act.CREATE, Act.UPDATE} and getTaskAttribute(myarg, body):
        pass
      elif action in {Act.CREATE, Act.MOVE} and getTaskMoveAttribute(myarg, kwargs):
        pass
      elif action == Act.CREATE and myarg == 'returnidonly':
        returnIdOnly = True
      elif myarg == 'compact':
        compact = True
      else:
        FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, svc, tasklistTasks, jcount = _validateUserGetObjectList(user, i, count, tasklistTaskEntity,
                                                                  api=API.TASKS, showAction=FJQC is None or not FJQC.formatJSON)
    if jcount == 0 or not verifyTasksServiceEnabled(svc, user, i, count):
      continue
    userTasklists = None
    Ind.Increment()
    j = 0
    for tasklistTask in tasklistTasks:
      j += 1
      if action != Act.CREATE:
        if '/' not in tasklistTask:
          continue
        tasklist, task = tasklistTask.split('/', 1)
      else:
        tasklist = tasklistTask
        task = body.get('title', '')
        if tasklist.startswith('tltitle:'):
          tasklistTitle = tasklist[8:]
          userTasklists, tasklist = getTaskListIDfromTitle(svc, userTasklists, tasklistTitle, user, i, count)
          if tasklist is None:
            entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklistTitle, Ent.TASK, task], Msg.TASKLIST_TITLE_NOT_FOUND, j, jcount)
            continue
      try:
        if action == Act.DELETE:
          callGAPI(svc.tasks(), 'delete',
                   throwReasons=GAPI.TASK_THROW_REASONS,
                   tasklist=tasklist, task=task)
          entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, task], j, jcount)
        elif action == Act.INFO:
          result = callGAPI(svc.tasks(), 'get',
                            throwReasons=GAPI.TASK_THROW_REASONS,
                            tasklist=tasklist, task=task)
          _showTask(tasklist, result, j, jcount, FJQC, compact)
        else:
          if action == Act.CREATE:
            result = callGAPI(svc.tasks(), 'insert',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, body=body, **kwargs)
            if returnIdOnly:
              writeStdout(f"{result['id']}\n")
              continue
          elif action == Act.UPDATE:
            result = callGAPI(svc.tasks(), 'patch',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, task=task, body=body)
          else: #elif action == Act.MOVE
            result = callGAPI(svc.tasks(), 'move',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, task=task, **kwargs)
          if not FJQC.formatJSON:
            entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, result['id']], j, jcount)
          Ind.Increment()
          _showTask(tasklist, result, j, jcount, FJQC, compact)
          Ind.Decrement()
      except (GAPI.badRequest, GAPI.permissionDenied, GAPI.invalid, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, task], str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        Ind.Decrement()
        userTasksServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

TASK_ORDERBY_CHOICE_MAP = {
  'completed': ('completed', 'No date'),
  'due': ('due', 'No date'),
  'updated': ('updated', 'No date'),
  }

TASK_QUERY_TIME_MAP = {
  'completedmin': 'completedMin',
  'completedmax': 'completedMax',
  'duemin': 'dueMin',
  'duemax': 'dueMax',
  'updatedmin': 'updatedMin',
  }
TASK_QUERY_STATE_MAP = {
  'showcompleted': 'showCompleted',
  'showdeleted': 'showDeleted',
  'showhidden': 'showHidden',
  }

# gam <UserTypeEntity> show tasks [tasklists <TasklistEntity>]
#	[completedmin <Time>] [completedmax <Time>]
#	[duemin <Time>] [duemax <Time>]
#	[updatedmin <Time>]
#	[showcompleted [<Boolean>]] [showdeleted [<Boolean>]] [showhidden [<Boolean>]] [showall]
#	[orderby completed|due|updated]
#	[countsonly|compact|formatjson]
# gam <UserTypeEntity> print tasks [tasklists <TasklistEntity>] [todrive <ToDriveAttribute>*]
#	[completedmin <Time>] [completedmax <Time>]
#	[duemin <Time>] [duemax <Time>]
#	[updatedmin <Time>]
#	[showcompleted [<Boolean>]] [showdeleted [<Boolean>]] [showhidden [<Boolean>]] [showall]
#	[orderby completed|due|updated]
#	[countsonly|(formatjson [quotechar <Character>])]
def printShowTasks(users):
  def _showTaskAndChildren(tasklist, taskId, k, compact):
    if taskId in taskParentsProcessed:
      return k
    taskParentsProcessed.add(taskId)
    if taskId in taskData:
      k += 1
      _showTask(tasklist, taskData[taskId], k, kcount, FJQC, compact)
      Ind.Increment()
    for task in taskParents.get(taskId, []):
      k = _showTaskAndChildren(tasklist, task['taskId'], k, compact)
    if taskId in taskData:
      Ind.Decrement()
    return k

  def _printTaskAndChildren(tasklist, taskId):
    if taskId in taskParentsProcessed:
      return
    taskParentsProcessed.add(taskId)
    if taskId in taskData:
      task = taskData[taskId]
      task['tasklistId'] = tasklist
      task['taskId'] = f"{tasklist}/{task['id']}"
      row = flattenJSON(task, flattened={'User': user}, skipObjects=TASK_SKIP_OBJECTS, timeObjects=TASK_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        row = {'User': user, 'id': task['id'], 'tasklistId': tasklist, 'taskId': task['taskId'], 'title': task.get('title', '')}
        row['JSON'] = json.dumps(cleanJSON(task, skipObjects=TASK_SKIP_OBJECTS, timeObjects=TASK_TIME_OBJECTS),
                                 ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
      for task in taskParents.get(taskId, []):
        _printTaskAndChildren(tasklist, task['taskId'])

  csvPF = CSVPrintFile(['User', 'tasklistId', 'id', 'taskId', 'title', 'status', 'due', 'updated', 'completed'], 'sortall') if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  CSVTitle = 'Tasks'
  FJQC = FormatJSONQuoteChar(csvPF)
  tasklistEntity = None
  kwargs = {'maxResults': 100}
  compact = countsOnly = False
  orderBy = orderByNoDataValue = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'tasklist', 'tasklists'}:
      tasklistEntity = getUserObjectEntity(Cmd.OB_TASKLIST_ID_ENTITY, Ent.TASKLIST, shlexSplit=True)
    elif myarg in TASK_QUERY_TIME_MAP:
      kwargs[TASK_QUERY_TIME_MAP[myarg]] = getTimeOrDeltaFromNow()
    elif myarg in TASK_QUERY_STATE_MAP:
      kwargs[TASK_QUERY_STATE_MAP[myarg]] = getBoolean()
    elif myarg == 'showall':
      for field in TASK_QUERY_STATE_MAP.values():
        kwargs[field] = True
    elif not csvPF and myarg == 'compact':
      compact = True
    elif myarg == 'orderby':
      orderBy, orderByNoDataValue = getChoice(TASK_ORDERBY_CHOICE_MAP, mapChoice=True)
    elif myarg == 'countsonly':
      countsOnly = True
      if csvPF:
        csvPF.SetTitles(['User', CSVTitle])
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if csvPF:
    if countsOnly:
      csvPF.SetFormatJSON(False)
    elif FJQC.formatJSON:
      csvPF.SetJSONTitles(['User', 'tasklistId', 'id', 'taskId', 'title', 'JSON'])
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    if tasklistEntity is None:
      user, svc = buildGAPIServiceObject(API.TASKS, user, i, count)
      if not svc:
        continue
      printGettingEntityItemForWhom(Ent.TASKLIST, user, i, count)
      results = getTaskLists(svc, user, i, count)
      if results is None:
        continue
      tasklists = [tasklist['id'] for tasklist in results]
      jcount = len(tasklists)
    else:
      userTasklists = None
      user, svc, tasklists, jcount = _validateUserGetObjectList(user, i, count, tasklistEntity, api=API.TASKS,
                                                                showAction=FJQC is None or not FJQC.formatJSON)
      if jcount == 0:
        continue
    taskCount = 0
#    if not csvPF and not FJQC.formatJSON:
#      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.TASKLIST, i, count)
    Ind.Increment()
    j = 0
    for tasklist in tasklists:
      j += 1
      if tasklist.startswith('tltitle:'):
        tasklistTitle = tasklist[8:]
        userTasklists, tasklist = getTaskListIDfromTitle(svc, userTasklists, tasklistTitle, user, i, count)
        if tasklist is None:
          entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklistTitle], Msg.TASKLIST_TITLE_NOT_FOUND, j, jcount)
          continue
      printGettingEntityItemForWhom(Ent.TASK, tasklist, j, jcount)
      try:
        tasks = callGAPIpages(svc.tasks(), 'list', 'items',
                              pageMessage=getPageMessageForWhom(),
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, **kwargs)
        kcount = len(tasks)
        if countsOnly:
          taskCount += kcount
          continue
        taskParents = {None: []}
        taskData = {}
        taskParentsProcessed = set()
        if orderBy is None:
          for task in tasks:
            taskData[task['id']] = task
            parent = task.get('parent', None)
            taskInfo = {'taskId': task['id'], 'parent': parent, 'position': task['position']}
            taskParents.setdefault(parent, [])
            taskParents[parent].append(taskInfo)
          for parent in taskParents:
            taskParents[parent].sort(key=lambda k: k['position'])
        else:
          for task in tasks:
            taskData[task['id']] = task
            if orderBy not in task:
              task[orderBy] = orderByNoDataValue
            taskInfo = {'taskId': task['id'], orderBy: task[orderBy],
                        'parent': task.get('parent', ' '), 'position': task['position']}
            taskParents[None].append(taskInfo)
          taskParents[None].sort(key=lambda k: (k[orderBy], k['parent'], k['position']))
        if not csvPF:
          if not FJQC.formatJSON:
            entityPerformActionNumItems([Ent.TASKLIST, tasklist], kcount, Ent.TASK, j, jcount)
          Ind.Increment()
          k = 0
          for parent in taskParents.values():
            for task in parent:
              k = _showTaskAndChildren(tasklist, task['taskId'], k, compact)
          Ind.Decrement()
        else:
          for parent in taskParents.values():
            for task in parent:
              _printTaskAndChildren(tasklist, task['taskId'])
      except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, None], str(e), i, count)
      except GAPI.serviceNotAvailable:
        userTasksServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()
    if countsOnly:
      if csvPF:
        csvPF.WriteRowTitles({'User': user, CSVTitle: taskCount})
      else:
        printEntityKVList([Ent.USER, user], [CSVTitle, taskCount], i, count)
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

TASKLIST_SKIP_OBJECTS = ['selfLink']
TASKLIST_TIME_OBJECTS = ['updated']

def _showTasklist(tasklist, j=0, jcount=0, FJQC=None):
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(tasklist, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.TASKLIST, tasklist['id']], j, jcount)
  Ind.Increment()
  showJSON(None, tasklist, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS)
  Ind.Decrement()

# gam <UserTypeEntity> create tasklist
#	[title <String>]
#	[returnidonly] [formatjson]
# gam <UserTypeEntity> update tasklist <TasklistEntity>
#	[title <String>]
#	[formatjson]
# gam <UserTypeEntity> info tasklist <TasklistEntity>
#	[formatjson]
# gam <UserTypeEntity> delete tasklist <TasklistEntity>
# gam <UserTypeEntity> clear tasklist <TasklistEntity>
def processTasklists(users):
  action = Act.Get()
  if action != Act.CREATE:
    tasklistEntity = getUserObjectEntity(Cmd.OB_TASKLIST_ID_ENTITY, Ent.TASKLIST, shlexSplit=True)
  else:
    tasklistEntity = {'item': Ent.TASKLIST, 'list': [None], 'dict': None}
  if action in {Act.DELETE, Act.CLEAR}:
    FJQC = None
    checkForExtraneousArguments()
  else:
    FJQC = FormatJSONQuoteChar()
    body = {}
    returnIdOnly = False
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if action in {Act.CREATE, Act.UPDATE} and myarg == 'title':
        body['title'] = getString(Cmd.OB_STRING, minLen=0)
      elif action == Act.CREATE and myarg == 'returnidonly':
        returnIdOnly = True
      else:
        FJQC.GetFormatJSON(myarg)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    userTasklists = None
    user, svc, tasklists, jcount = _validateUserGetObjectList(user, i, count, tasklistEntity,
                                                              api=API.TASKS,
                                                              showAction=action != Act.CREATE and (FJQC is None or not FJQC.formatJSON))
    if jcount == 0 or not verifyTasksServiceEnabled(svc, user, i, count):
      continue
    Ind.Increment()
    j = 0
    for tasklist in tasklists:
      j += 1
      if action != Act.CREATE:
        if tasklist.startswith('tltitle:'):
          tasklistTitle = tasklist[8:]
          userTasklists, tasklist = getTaskListIDfromTitle(svc, userTasklists, tasklistTitle, user, i, count)
          if userTasklists is None:
            continue
          if tasklist is None:
            entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklistTitle], Msg.TASKLIST_TITLE_NOT_FOUND, j, jcount)
            continue
      try:
        if action == Act.DELETE:
          callGAPI(svc.tasklists(), 'delete',
                   throwReasons=GAPI.TASK_THROW_REASONS,
                   tasklist=tasklist)
          entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist], j, jcount)
        elif action == Act.CLEAR:
          callGAPI(svc.tasks(), 'clear',
                   throwReasons=GAPI.TASK_THROW_REASONS,
                   tasklist=tasklist)
          entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist], j, jcount)
        elif action == Act.INFO:
          result = callGAPI(svc.tasklists(), 'get',
                            throwReasons=GAPI.TASK_THROW_REASONS,
                            tasklist=tasklist)
          _showTasklist(result, j, jcount, FJQC)
        else:
          if action == Act.CREATE:
            result = callGAPI(svc.tasklists(), 'insert',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              body=body)
            if returnIdOnly:
              writeStdout(f"{result['id']}\n")
              continue
          else: # Act.UPDATE
            result = callGAPI(svc.tasklists(), 'patch',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, body=body)
          if not FJQC.formatJSON:
            entityActionPerformed([Ent.USER, user, Ent.TASKLIST, result['id']], i, count)
          Ind.Increment()
          _showTasklist(result, j, jcount, FJQC)
          Ind.Decrement()
      except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklist], str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        Ind.Decrement()
        userTasksServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> show tasklists
#	[countsonly|formatjson]
# gam <UserTypeEntity> print tasklists [todrive <ToDriveAttribute>*]
#	[countsonly|(formatjson [quotechar <Character>])]
def printShowTasklists(users):
  csvPF = CSVPrintFile(['User', 'id', 'title']) if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  CSVTitle = 'TaskLists'
  FJQC = FormatJSONQuoteChar(csvPF)
  countsOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'countsonly':
      countsOnly = True
      if csvPF:
        csvPF.SetTitles(['User', CSVTitle])
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if countsOnly and csvPF:
    csvPF.SetFormatJSON(False)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, svc = buildGAPIServiceObject(API.TASKS, user, i, count)
    if not svc:
      continue
    printGettingAllEntityItemsForWhom(Ent.TASKLIST, user, i, count)
    tasklists = getTaskLists(svc, user, i, count)
    if tasklists is None:
      continue
    jcount = len(tasklists)
    if countsOnly:
      if csvPF:
        csvPF.WriteRowTitles({'User': user, CSVTitle: jcount})
      else:
        printEntityKVList([Ent.USER, user], [CSVTitle, jcount], i, count)
    elif not csvPF:
      if not  FJQC.formatJSON:
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.TASKLIST, i, count)
      Ind.Increment()
      j = 0
      for tasklist in tasklists:
        j += 1
        _showTasklist(tasklist, j, jcount, FJQC)
      Ind.Decrement()
    elif tasklists:
      for tasklist in tasklists:
        row = flattenJSON(tasklist, flattened={'User': user}, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {'User': user, 'id': tasklist['id'], 'title': tasklist.get('title', '')}
          row['JSON'] = json.dumps(cleanJSON(tasklist, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS),
                                   ensure_ascii=False, sort_keys=True)
          csvPF.WriteRowNoFilter(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

# gam <UserTypeEntity> import tasklist <Filename> [charset <Charset>]))
def importTasklist(users):
  filename = getString(Cmd.OB_FILE_NAME)
  encoding = getCharSet()
  try:
    jsonData = json.loads(readFile(setFilePath(filename, GC.INPUT_DIR), encoding=encoding))
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    Cmd.Backup()
    usageErrorExit(Msg.JSON_ERROR.format(str(e), filename))
  if jsonData.get('kind', '') != 'tasks#taskLists':
    Cmd.Backup()
    usageErrorExit(f'{"Not a Tasks takeout JSON file"}: {filename}')
  parentIdMap = {}
  cleanData = {'items': []}
  for tasklist in jsonData.get('items', []):
    cleanTasklist = {'title': tasklist['title'], 'items': []}
    for task in tasklist.get('items', []):
      cleanTask = {}
      for field in ['id', 'parent', 'title', 'notes', 'status', 'due', 'completed', 'deleted']:
        if field in task:
          cleanTask[field] = task[field]
        parentIdMap[task['id']] = None
      cleanTasklist['items'].append(cleanTask.copy())
    cleanData['items'].append(cleanTasklist.copy())
  if not cleanData['items']:
    writeStdout('No tasks to import\n')
    return
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, svc = buildGAPIServiceObject(API.TASKS, user, i, count)
    if not svc:
      continue
    if not verifyTasksServiceEnabled(svc, user, i, count):
      continue
    for tasklist in cleanData['items']:
      body = {'title': tasklist['title']}
      result = callGAPI(svc.tasklists(), 'insert',
                        throwReasons=GAPI.TASK_THROW_REASONS,
                        body=body)
      tasklistId = result['id']
      for task in tasklist['items']:
        taskId = task.pop('id')
        if 'parent' in task:
          parent = parentIdMap[task.pop('parent')]
        else:
          parent = None
        result = callGAPI(svc.tasks(), 'insert',
                          throwReasons=GAPI.TASK_THROW_REASONS,
                          tasklist=tasklistId, parent=parent, body=task)
        parentIdMap[taskId] = result['id']

