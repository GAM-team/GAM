"""GAM Google Tasks and Tag Manager management."""

import json
import sys

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def verifyTasksServiceEnabled(svc, user, i, count):
  try:
    _getMain().callGAPIpages(svc.tasklists(), 'list', 'items',
                  throwReasons=GAPI.TASKLIST_THROW_REASONS,
                  maxItems=1)
    return True
  except (GAPI.notFound, GAPI.badRequest, GAPI.invalid):
    _getMain().userTasksServiceNotEnabledWarning(user, i, count)
    return False

def getTaskLists(svc, user, i, count):
  try:
    results = _getMain().callGAPIpages(svc.tasklists(), 'list', 'items',
                            pageMessage=_getMain().getPageMessageForWhom(),
                            throwReasons=GAPI.TASKLIST_THROW_REASONS,
                            maxResults=100)
  except (GAPI.badRequest, GAPI.invalid) as e:
    _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, None], str(e), i, count)
    results = None
  except GAPI.notFound:
    _getMain().userTasksServiceNotEnabledWarning(user, i, count)
    results = None
  return results

def getTaskListIDfromTitle(svc, userTasklists, title, user, i, count):
  if userTasklists is None:
    _getMain().printGettingEntityItemForWhom(Ent.TASKLIST, user, i, count)
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
    _getMain().printLine(json.dumps(_getMain().cleanJSON(task, skipObjects=TASK_SKIP_OBJECTS, timeObjects=TASK_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.TASK, task['taskId']], j, jcount)
  Ind.Increment()
  _getMain().showJSON(None, task, skipObjects=TASK_SKIP_OBJECTS+['notes'], timeObjects=TASK_TIME_OBJECTS)
  field = 'notes'
  if field in task:
    if not compact:
      _getMain().printKeyValueList([field, None])
      Ind.Increment()
      _getMain().printKeyValueList([Ind.MultiLineText(task[field])])
      Ind.Decrement()
    else:
      _getMain().printKeyValueList(['notes', _getMain().escapeCRsNLs(task[field])])
  Ind.Decrement()

TASK_STATUS_MAP = {
  'completed': 'completed',
  'needsaction': 'needsAction',
  }

def getTaskAttribute(myarg, body):
  if myarg == 'title':
    body[myarg] = _getMain().getString(Cmd.OB_STRING, minLen=0)
  elif myarg == 'notes':
    body[myarg] = _getMain().getStringWithCRsNLs()
  elif myarg == 'status':
    body[myarg] = _getMain().getChoice(TASK_STATUS_MAP, mapChoice=True)
  elif myarg == 'due':
    body[myarg] = _getMain().getTimeOrDeltaFromNow()
  else:
    return False
  return True

def getTaskMoveAttribute(myarg, kwargs):
  if myarg == 'parent':
    kwargs[myarg] = _getMain().getString(Cmd.OB_TASK_ID)
  elif myarg == 'previous':
    kwargs[myarg] = _getMain().getString(Cmd.OB_TASK_ID)
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
    tasklistTaskEntity = _getMain().getUserObjectEntity(Cmd.OB_TASKLIST_ID_TASK_ID_ENTITY, Ent.TASK, shlexSplit=True)
  else:
    tasklistTaskEntity = _getMain().getUserObjectEntity(Cmd.OB_TASKLIST_ID_ENTITY, Ent.TASK, shlexSplit=True)
  if action in {Act.DELETE, Act.CLEAR}:
    FJQC = None
    _getMain().checkForExtraneousArguments()
  else:
    FJQC = _getMain().FormatJSONQuoteChar()
    body = {}
    kwargs = {}
    compact = returnIdOnly = False
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
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
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, svc, tasklistTasks, jcount = _getMain()._validateUserGetObjectList(user, i, count, tasklistTaskEntity,
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
            _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklistTitle, Ent.TASK, task], Msg.TASKLIST_TITLE_NOT_FOUND, j, jcount)
            continue
      try:
        if action == Act.DELETE:
          _getMain().callGAPI(svc.tasks(), 'delete',
                   throwReasons=GAPI.TASK_THROW_REASONS,
                   tasklist=tasklist, task=task)
          _getMain().entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, task], j, jcount)
        elif action == Act.INFO:
          result = _getMain().callGAPI(svc.tasks(), 'get',
                            throwReasons=GAPI.TASK_THROW_REASONS,
                            tasklist=tasklist, task=task)
          _showTask(tasklist, result, j, jcount, FJQC, compact)
        else:
          if action == Act.CREATE:
            result = _getMain().callGAPI(svc.tasks(), 'insert',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, body=body, **kwargs)
            if returnIdOnly:
              _getMain().writeStdout(f"{result['id']}\n")
              continue
          elif action == Act.UPDATE:
            result = _getMain().callGAPI(svc.tasks(), 'patch',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, task=task, body=body)
          else: #elif action == Act.MOVE
            result = _getMain().callGAPI(svc.tasks(), 'move',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, task=task, **kwargs)
          if not FJQC.formatJSON:
            _getMain().entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, result['id']], j, jcount)
          Ind.Increment()
          _showTask(tasklist, result, j, jcount, FJQC, compact)
          Ind.Decrement()
      except (GAPI.badRequest, GAPI.permissionDenied, GAPI.invalid, GAPI.notFound) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, task], str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        Ind.Decrement()
        _getMain().userTasksServiceNotEnabledWarning(user, i, count)
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
      row = _getMain().flattenJSON(task, flattened={'User': user}, skipObjects=TASK_SKIP_OBJECTS, timeObjects=TASK_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        row = {'User': user, 'id': task['id'], 'tasklistId': tasklist, 'taskId': task['taskId'], 'title': task.get('title', '')}
        row['JSON'] = json.dumps(_getMain().cleanJSON(task, skipObjects=TASK_SKIP_OBJECTS, timeObjects=TASK_TIME_OBJECTS),
                                 ensure_ascii=False, sort_keys=True)
        csvPF.WriteRowNoFilter(row)
      for task in taskParents.get(taskId, []):
        _printTaskAndChildren(tasklist, task['taskId'])

  csvPF = _getMain().CSVPrintFile(['User', 'tasklistId', 'id', 'taskId', 'title', 'status', 'due', 'updated', 'completed'], 'sortall') if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  CSVTitle = 'Tasks'
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  tasklistEntity = None
  kwargs = {'maxResults': 100}
  compact = countsOnly = False
  orderBy = orderByNoDataValue = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'tasklist', 'tasklists'}:
      tasklistEntity = _getMain().getUserObjectEntity(Cmd.OB_TASKLIST_ID_ENTITY, Ent.TASKLIST, shlexSplit=True)
    elif myarg in TASK_QUERY_TIME_MAP:
      kwargs[TASK_QUERY_TIME_MAP[myarg]] = _getMain().getTimeOrDeltaFromNow()
    elif myarg in TASK_QUERY_STATE_MAP:
      kwargs[TASK_QUERY_STATE_MAP[myarg]] = _getMain().getBoolean()
    elif myarg == 'showall':
      for field in TASK_QUERY_STATE_MAP.values():
        kwargs[field] = True
    elif not csvPF and myarg == 'compact':
      compact = True
    elif myarg == 'orderby':
      orderBy, orderByNoDataValue = _getMain().getChoice(TASK_ORDERBY_CHOICE_MAP, mapChoice=True)
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
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    if tasklistEntity is None:
      user, svc = _getMain().buildGAPIServiceObject(API.TASKS, user, i, count)
      if not svc:
        continue
      _getMain().printGettingEntityItemForWhom(Ent.TASKLIST, user, i, count)
      results = getTaskLists(svc, user, i, count)
      if results is None:
        continue
      tasklists = [tasklist['id'] for tasklist in results]
      jcount = len(tasklists)
    else:
      userTasklists = None
      user, svc, tasklists, jcount = _getMain()._validateUserGetObjectList(user, i, count, tasklistEntity, api=API.TASKS,
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
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklistTitle], Msg.TASKLIST_TITLE_NOT_FOUND, j, jcount)
          continue
      _getMain().printGettingEntityItemForWhom(Ent.TASK, tasklist, j, jcount)
      try:
        tasks = _getMain().callGAPIpages(svc.tasks(), 'list', 'items',
                              pageMessage=_getMain().getPageMessageForWhom(),
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
            _getMain().entityPerformActionNumItems([Ent.TASKLIST, tasklist], kcount, Ent.TASK, j, jcount)
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
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklist, Ent.TASK, None], str(e), i, count)
      except GAPI.serviceNotAvailable:
        _getMain().userTasksServiceNotEnabledWarning(user, i, count)
    Ind.Decrement()
    if countsOnly:
      if csvPF:
        csvPF.WriteRowTitles({'User': user, CSVTitle: taskCount})
      else:
        _getMain().printEntityKVList([Ent.USER, user], [CSVTitle, taskCount], i, count)
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

TASKLIST_SKIP_OBJECTS = ['selfLink']
TASKLIST_TIME_OBJECTS = ['updated']

def _showTasklist(tasklist, j=0, jcount=0, FJQC=None):
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(tasklist, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS),
                         ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.TASKLIST, tasklist['id']], j, jcount)
  Ind.Increment()
  _getMain().showJSON(None, tasklist, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS)
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
    tasklistEntity = _getMain().getUserObjectEntity(Cmd.OB_TASKLIST_ID_ENTITY, Ent.TASKLIST, shlexSplit=True)
  else:
    tasklistEntity = {'item': Ent.TASKLIST, 'list': [None], 'dict': None}
  if action in {Act.DELETE, Act.CLEAR}:
    FJQC = None
    _getMain().checkForExtraneousArguments()
  else:
    FJQC = _getMain().FormatJSONQuoteChar()
    body = {}
    returnIdOnly = False
    while Cmd.ArgumentsRemaining():
      myarg = _getMain().getArgument()
      if action in {Act.CREATE, Act.UPDATE} and myarg == 'title':
        body['title'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
      elif action == Act.CREATE and myarg == 'returnidonly':
        returnIdOnly = True
      else:
        FJQC.GetFormatJSON(myarg)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    userTasklists = None
    user, svc, tasklists, jcount = _getMain()._validateUserGetObjectList(user, i, count, tasklistEntity,
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
            _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklistTitle], Msg.TASKLIST_TITLE_NOT_FOUND, j, jcount)
            continue
      try:
        if action == Act.DELETE:
          _getMain().callGAPI(svc.tasklists(), 'delete',
                   throwReasons=GAPI.TASK_THROW_REASONS,
                   tasklist=tasklist)
          _getMain().entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist], j, jcount)
        elif action == Act.CLEAR:
          _getMain().callGAPI(svc.tasks(), 'clear',
                   throwReasons=GAPI.TASK_THROW_REASONS,
                   tasklist=tasklist)
          _getMain().entityActionPerformed([Ent.USER, user, Ent.TASKLIST, tasklist], j, jcount)
        elif action == Act.INFO:
          result = _getMain().callGAPI(svc.tasklists(), 'get',
                            throwReasons=GAPI.TASK_THROW_REASONS,
                            tasklist=tasklist)
          _showTasklist(result, j, jcount, FJQC)
        else:
          if action == Act.CREATE:
            result = _getMain().callGAPI(svc.tasklists(), 'insert',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              body=body)
            if returnIdOnly:
              _getMain().writeStdout(f"{result['id']}\n")
              continue
          else: # Act.UPDATE
            result = _getMain().callGAPI(svc.tasklists(), 'patch',
                              throwReasons=GAPI.TASK_THROW_REASONS,
                              tasklist=tasklist, body=body)
          if not FJQC.formatJSON:
            _getMain().entityActionPerformed([Ent.USER, user, Ent.TASKLIST, result['id']], i, count)
          Ind.Increment()
          _showTasklist(result, j, jcount, FJQC)
          Ind.Decrement()
      except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.TASKLIST, tasklist], str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        Ind.Decrement()
        _getMain().userTasksServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> show tasklists
#	[countsonly|formatjson]
# gam <UserTypeEntity> print tasklists [todrive <ToDriveAttribute>*]
#	[countsonly|(formatjson [quotechar <Character>])]
def printShowTasklists(users):
  csvPF = _getMain().CSVPrintFile(['User', 'id', 'title']) if Act.csvFormat() else None
  if csvPF:
    csvPF.SetNoEscapeChar(True)
  CSVTitle = 'TaskLists'
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  countsOnly = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
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
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, svc = _getMain().buildGAPIServiceObject(API.TASKS, user, i, count)
    if not svc:
      continue
    _getMain().printGettingAllEntityItemsForWhom(Ent.TASKLIST, user, i, count)
    tasklists = getTaskLists(svc, user, i, count)
    if tasklists is None:
      continue
    jcount = len(tasklists)
    if countsOnly:
      if csvPF:
        csvPF.WriteRowTitles({'User': user, CSVTitle: jcount})
      else:
        _getMain().printEntityKVList([Ent.USER, user], [CSVTitle, jcount], i, count)
    elif not csvPF:
      if not  FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.TASKLIST, i, count)
      Ind.Increment()
      j = 0
      for tasklist in tasklists:
        j += 1
        _showTasklist(tasklist, j, jcount, FJQC)
      Ind.Decrement()
    elif tasklists:
      for tasklist in tasklists:
        row = _getMain().flattenJSON(tasklist, flattened={'User': user}, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS)
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles(row)
        elif csvPF.CheckRowTitles(row):
          row = {'User': user, 'id': tasklist['id'], 'title': tasklist.get('title', '')}
          row['JSON'] = json.dumps(_getMain().cleanJSON(tasklist, skipObjects=TASKLIST_SKIP_OBJECTS, timeObjects=TASKLIST_TIME_OBJECTS),
                                   ensure_ascii=False, sort_keys=True)
          csvPF.WriteRowNoFilter(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile(CSVTitle)

# gam <UserTypeEntity> import tasklist <Filename> [charset <Charset>]))
def importTasklist(users):
  filename = _getMain().getString(Cmd.OB_FILE_NAME)
  encoding = _getMain().getCharSet()
  try:
    jsonData = json.loads(_getMain().readFile(_getMain().setFilePath(filename, GC.INPUT_DIR), encoding=encoding))
  except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
    Cmd.Backup()
    _getMain().usageErrorExit(Msg.JSON_ERROR.format(str(e), filename))
  if jsonData.get('kind', '') != 'tasks#taskLists':
    Cmd.Backup()
    _getMain().usageErrorExit(f'{"Not a Tasks takeout JSON file"}: {filename}')
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
    _getMain().writeStdout('No tasks to import\n')
    return
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, svc = _getMain().buildGAPIServiceObject(API.TASKS, user, i, count)
    if not svc:
      continue
    if not verifyTasksServiceEnabled(svc, user, i, count):
      continue
    for tasklist in cleanData['items']:
      body = {'title': tasklist['title']}
      result = _getMain().callGAPI(svc.tasklists(), 'insert',
                        throwReasons=GAPI.TASK_THROW_REASONS,
                        body=body)
      tasklistId = result['id']
      for task in tasklist['items']:
        taskId = task.pop('id')
        if 'parent' in task:
          parent = parentIdMap[task.pop('parent')]
        else:
          parent = None
        result = _getMain().callGAPI(svc.tasks(), 'insert',
                          throwReasons=GAPI.TASK_THROW_REASONS,
                          tasklist=tasklistId, parent=parent, body=task)
        parentIdMap[taskId] = result['id']

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
  csvPF = _getMain().CSVPrintFile(['User']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  if entityType == Ent.TAGMANAGER_ACCOUNT:
    kwargs = {'includeGoogleTags': False}
    parentList = [None]
  else:
    kwargs = {'parent': None}
    if not _getMain().checkArgumentPresent('select'):
      parentList = _getMain().getString(Cmd.OB_TAGMANAGER_PATH_LIST).replace(',', ' ').split()
    else:
      parentList = _getMain().getEntityList(Cmd.OB_TAGMANAGER_PATH_LIST)
  parameters = TAGMANAGER_PARAMETERS[entityType]
  if csvPF:
    csvPF.AddTitles([parameters['name'], 'path'])
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif entityType == Ent.TAGMANAGER_ACCOUNT and myarg == 'includegoogletags':
      kwargs['includeGoogleTags'] = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, svc = _getMain().buildGAPIServiceObject(parameters['api'], user, i, count)
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
        _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count)
      else:
        kwargs['parent'] = parent
        qualifier = f' for {Ent.Singular(parameters["parentEntityType"])}: {parent}'
        _getMain().printGettingAllEntityItemsForWhom(entityType, user, i, count, qualifier=qualifier)
      try:
        results = _getMain().callGAPIpages(svc, 'list', parameters['respType'],
                                 pageMessage=_getMain().getPageMessageForWhom(),
                                 throwReasons=GAPI.TAGMANAGER_THROW_REASONS,
                                 **kwargs)
      except (GAPI.badRequest, GAPI.invalid, GAPI.notFound) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, entityType, kwargs['parent']], str(e), j, jcount)
        continue
      if not csvPF:
        kcount = len(results)
        if not  FJQC.formatJSON:
          _getMain().entityPerformActionNumItems([Ent.USER, user], kcount, entityType, j, jcount)
        Ind.Increment()
        k = 0
        for result in results:
          k += 1
          if not  FJQC.formatJSON:
            _getMain().printEntity([entityType, result['path']], k, kcount)
            Ind.Increment()
            _getMain().printKeyValueList([parameters['name'], result.pop(parameters['name'])])
            for tmid in parameters['idList']:
              _getMain().printKeyValueList([tmid, result.pop(tmid)])
            _getMain().showJSON(None, result)
            Ind.Decrement()
          else:
            _getMain().printLine(json.dumps(_getMain().cleanJSON(result), ensure_ascii=False, sort_keys=True))
        Ind.Decrement()
      elif results:
        for result in results:
          baseRow = {'User': user}
          for tmid in parameters['idList']:
            baseRow[tmid] = result.pop(tmid)
          row = _getMain().flattenJSON(result, flattened=baseRow)
          if not FJQC.formatJSON:
            csvPF.WriteRowTitles(row)
          elif csvPF.CheckRowTitles(row):
            row = {'User': user, parameters['name']: result[parameters['name']], 'path': result['path']}
            row['JSON'] = json.dumps(_getMain().cleanJSON(result), ensure_ascii=False, sort_keys=True)
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

