"""Course participant management: add, remove, sync, clear.

Part of the _courses_tmp sub-package."""

"""GAM Google Classroom course management."""

import re
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

def doPrintCourseParticipants():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  csvPF = _getMain().CSVPrintFile(['courseId', 'courseName'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties(['name'])
  courseShowProperties['members'] = 'all'
  showItemCountOnly = False
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'show':
      courseShowProperties['members'] = _getMain().getChoice(COURSE_MEMBER_ARGUMENTS)
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if coursesInfo is None:
    if showItemCountOnly:
      _getMain().writeStdout('0\n')
    return
  if courseShowProperties['members'] != 'none':
    if courseShowProperties['members'] != 'students':
      if FJQC.formatJSON:
        csvPF.AddJSONTitles('JSON-teachers')
    if courseShowProperties['members'] != 'teachers':
      if FJQC.formatJSON:
        csvPF.AddJSONTitles('JSON-students')
    teachersFields = 'nextPageToken,teachers(userId,profile)'
    studentsFields = 'nextPageToken,students(userId,profile)'
  else:
    teachersFields = studentsFields = None
  itemCount = 0
  count = len(coursesInfo)
  i = 0
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
    if not ocroom:
      continue
    _, teachers, students = _getCourseAliasesMembers(croom, ocroom, courseId, courseShowProperties, teachersFields, studentsFields, True, i, count)
    if showItemCountOnly:
      if courseShowProperties['members'] != 'students':
        itemCount += len(teachers)
      if courseShowProperties['members'] != 'teachers':
        itemCount += len(students)
      continue
    if not FJQC.formatJSON:
      if courseShowProperties['members'] != 'none':
        if courseShowProperties['members'] != 'students':
          for member in teachers:
            csvPF.WriteRowTitles(_getMain().flattenJSON(member, flattened={'courseId': courseId, 'courseName': course['name'], 'userRole': 'TEACHER'}))
        if courseShowProperties['members'] != 'teachers':
          for member in students:
            csvPF.WriteRowTitles(_getMain().flattenJSON(member, flattened={'courseId': courseId, 'courseName': course['name'], 'userRole': 'STUDENT'}))
    else:
      row = {'courseId': courseId, 'courseName': course['name']}
      if courseShowProperties['members'] != 'none':
        if courseShowProperties['members'] != 'students':
          row['JSON-teachers'] = json.dumps(list(teachers))
        if courseShowProperties['members'] != 'teachers':
          row['JSON-students'] = json.dumps(list(students))
      csvPF.WriteRowNoFilter(row)
  if showItemCountOnly:
    _getMain().writeStdout(f'{itemCount}\n')
    return
  if not FJQC.formatJSON:
    csvPF.SetSortTitles(COURSE_PARTICIPANTS_SORT_TITLES)
  csvPF.writeCSVfile('Course Participants')

COURSE_COUNTS_MEMBER_ARGUMENTS = ['students', 'teachers']
COURSE_COUNTS_KEY_TITLE = {'students': 'Student', 'teachers': 'Teacher'}

# gam print course-counts students|teachers [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[mincount <Integer>]
#	[formatjson [quotechar <Character>]]
def doPrintCourseCounts():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties()
  courseShowProperties['members'] = _getMain().getChoice(COURSE_COUNTS_MEMBER_ARGUMENTS)
  keyTitle = COURSE_COUNTS_KEY_TITLE[courseShowProperties['members']]
  csvPF = _getMain().CSVPrintFile([keyTitle, 'CourseCount'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  minCount = 0
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'mincount':
      minCount = _getMain().getInteger(minVal=0)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if not coursesInfo:
    coursesInfo = []
  teachersFields = 'nextPageToken,teachers(profile(emailAddress))'
  studentsFields = 'nextPageToken,students(profile(emailAddress))'
  courseCounts = {}
  count = len(coursesInfo)
  i = 0
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
    if not ocroom:
      continue
    _, teachers, students = _getCourseAliasesMembers(croom, ocroom, courseId, courseShowProperties, teachersFields, studentsFields, True, i, count)
    members = teachers if courseShowProperties['members'] == 'teachers' else students
    for member in members:
      memberKey = member['profile'].get('emailAddress', '')
      courseCounts.setdefault(memberKey, 0)
      courseCounts[memberKey] += 1
  if not FJQC.formatJSON:
    for key, count in sorted(courseCounts.items()):
      if count >= minCount:
        csvPF.WriteRow({keyTitle: key, 'CourseCount': count})
  else:
    csvPF.SetJSONTitles(['JSON'])
    for key, count in sorted(courseCounts.items()):
      if count >= minCount:
        csvPF.WriteRow({'JSON': {keyTitle: key, 'CourseCount': count}})
  csvPF.writeCSVfile(f'{keyTitle} Course Counts')

def _batchAddItemsToCourse(croom, courseId, i, count, addItems, addType):
  def _addIdToResponse(response, riItem):
    if addType == Ent.COURSE_ANNOUNCEMENT:
      respId = response.get('id', '')
    elif addType == Ent.COURSE_TOPIC:
      respId = response.get('topicId', '')
    else:
      respId = ''
    if respId:
      return riItem + f'({respId})'
    return riItem

  _ADD_PART_REASON_TO_MESSAGE_MAP = {GAPI.NOT_FOUND: Msg.DOES_NOT_EXIST,
                                     GAPI.ALREADY_EXISTS: Msg.DUPLICATE,
                                     GAPI.FAILED_PRECONDITION: Msg.NOT_ALLOWED}
  def _callbackAddItemsToCourse(request_id, response, exception):
    ri = request_id.splitlines()
    if addType == Ent.COURSE_ANNOUNCEMENT:
      mg = re.match(r"^{'text': '(.+)'}$", ri[RI_ITEM])
      if mg:
        riText = mg.group(1)
      else:
        riText = ''
      if len(riText) > 100:
        riItem = riText[0:100]+'...'
      else:
        riItem = riText
    else:
      riItem = ri[RI_ITEM]
    if exception is None:
      riItem = _addIdToResponse(response, riItem)
      _getMain().entityActionPerformed([Ent.COURSE, ri[RI_ENTITY], addType, riItem], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      if (reason not in {GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE}) and ((reason != GAPI.NOT_FOUND) or (addType == Ent.COURSE_ALIAS)):
        if reason in [GAPI.FORBIDDEN, GAPI.BACKEND_ERROR]:
          errMsg = _getMain().getPhraseDNEorSNA(riItem)
        else:
          errMsg = _getMain().getHTTPError(_ADD_PART_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        return
      _getMain().waitOnFailure(1, 10, reason, message)
      if addType in {Ent.STUDENT, Ent.TEACHER, Ent.COURSE_TOPIC}:
        rbody = {attribute: riItem}
      elif addType == Ent.COURSE_ALIAS:
        rbody = {attribute: _getMain().addCourseAliasScope(riItem)}
      else: # addType == Ent.COURSE_ANNOUNCEMENT:
        rbody = ri[RI_ITEM]
      try:
        result = _getMain().callGAPI(service, 'create',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR,
                                        GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION,
                                        GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE],
                          retryReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE], triesLimit=0 if reason != GAPI.NOT_FOUND else 3,
                          courseId=_getMain().addCourseIdScope(ri[RI_ENTITY]), body=rbody, fields=returnFields)
        riItem = _addIdToResponse(result, riItem)
      except (GAPI.notFound, GAPI.backendError, GAPI.forbidden):
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], _getMain().getPhraseDNEorSNA(riItem), int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.alreadyExists:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], Msg.DUPLICATE, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.failedPrecondition:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], Msg.NOT_ALLOWED, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except (GAPI.quotaExceeded, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))

  returnFields = ''
  if addType == Ent.STUDENT:
    service = croom.courses().students()
    attribute = 'userId'
  elif addType == Ent.TEACHER:
    service = croom.courses().teachers()
    attribute = 'userId'
  elif addType == Ent.COURSE_ALIAS:
    service = croom.courses().aliases()
    attribute = 'alias'
  elif addType == Ent.COURSE_TOPIC:
    service = croom.courses().topics()
    attribute = 'name'
    returnFields = 'topicId'
  else: # addType == Ent.COURSE_ANNOUNCEMENT:
    service = croom.courses().announcements()
    attribute = 'text'
    returnFields = 'id'
  method = getattr(service, 'create')
  Act.Set(Act.ADD)
  jcount = len(addItems)
  noScopeCourseId = _getMain().removeCourseIdScope(courseId)
  _getMain().entityPerformActionNumItems([Ent.COURSE, noScopeCourseId], jcount, addType, i, count)
  Ind.Increment()
  svcargs = dict([('courseId', courseId), ('body', {attribute: None}), ('fields', returnFields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
  dbatch = croom.new_batch_http_request(callback=_callbackAddItemsToCourse)
  bcount = 0
  j = 0
  for addItem in addItems:
    j += 1
    svcparms = svcargs.copy()
    if addType in {Ent.STUDENT, Ent.TEACHER}:
      svcparms['body'][attribute] = cleanItem = _getMain().normalizeEmailAddressOrUID(addItem)
    elif addType == Ent.COURSE_ALIAS:
      svcparms['body'][attribute] = _getMain().addCourseAliasScope(addItem)
      cleanItem = _getMain().removeCourseAliasScope(svcparms['body'][attribute])
    elif addType == Ent.COURSE_TOPIC:
      svcparms['body'][attribute] = cleanItem = addItem
    else: # addType == Ent.COURSE_ANNOUNCEMENT:
      svcparms['body'] = cleanItem = addItem
    dbatch.add(method(**svcparms), request_id=_getMain().batchRequestID(noScopeCourseId, 0, 0, j, jcount, cleanItem, addType))
    bcount += 1
    if bcount >= GC.Values[GC.BATCH_SIZE]:
      _getMain().executeBatch(dbatch)
      dbatch = croom.new_batch_http_request(callback=_callbackAddItemsToCourse)
      bcount = 0
  if bcount > 0:
    dbatch.execute()
  Ind.Decrement()

def _batchRemoveItemsFromCourse(croom, courseId, i, count, removeItems, removeType):
  _REMOVE_PART_REASON_TO_MESSAGE_MAP = {GAPI.NOT_FOUND: Msg.DOES_NOT_EXIST,
                                        GAPI.FORBIDDEN: Msg.FORBIDDEN,
                                        GAPI.PERMISSION_DENIED: Msg.PERMISSION_DENIED}
  def _callbackRemoveItemsFromCourse(request_id, _, exception):
    ri = request_id.splitlines()
    riItem = ri[RI_ITEM]
    if exception is None:
      _getMain().entityActionPerformed([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = _getMain().checkGAPIError(exception)
      if reason not in {GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE}:
        if reason == GAPI.NOT_FOUND and removeType != Ent.COURSE_ALIAS:
          errMsg = f'{Msg.NOT_A} {Ent.Singular(removeType)}'
        else:
          errMsg = _getMain().getHTTPError(_REMOVE_PART_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        return
      _getMain().waitOnFailure(1, 10, reason, message)
      if removeType in {Ent.STUDENT, Ent.TEACHER, Ent.COURSE_TOPIC, Ent.COURSE_ANNOUNCEMENT}:
        rbody = {attribute: riItem}
      else: # removeType == Ent.COURSE_ALIAS:
        rbody = {attribute: _getMain().addCourseAliasScope(riItem)}
      try:
        _getMain().callGAPI(service, 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED,
                               GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE, GAPI.FAILED_PRECONDITION],
                 retryReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE], triesLimit=0 if reason != GAPI.NOT_FOUND else 3,
                 courseId=_getMain().addCourseIdScope(ri[RI_ENTITY]), body=rbody, fields='')
      except GAPI.notFound:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], Msg.DOES_NOT_EXIST, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.forbidden:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], Msg.FORBIDDEN, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.permissionDenied:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], Msg.PERMISSION_DENIED, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except (GAPI.quotaExceeded, GAPI.serviceNotAvailable, GAPI.failedPrecondition) as e:
        _getMain().entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))

  if removeType == Ent.STUDENT:
    service = croom.courses().students()
    attribute = 'userId'
  elif removeType == Ent.TEACHER:
    service = croom.courses().teachers()
    attribute = 'userId'
  elif removeType == Ent.COURSE_ALIAS:
    service = croom.courses().aliases()
    attribute = 'alias'
  elif removeType == Ent.COURSE_TOPIC:
    service = croom.courses().topics()
    attribute = 'id'
  else: # removeType == Ent.COURSE_ANNOUNCEMENT:
    service = croom.courses().announcements()
    attribute = 'id'
  method = getattr(service, 'delete')
  Act.Set(Act.REMOVE)
  jcount = len(removeItems)
  noScopeCourseId = _getMain().removeCourseIdScope(courseId)
  _getMain().entityPerformActionNumItems([Ent.COURSE, noScopeCourseId], jcount, removeType, i, count)
  Ind.Increment()
  svcargs = dict([('courseId', courseId), ('fields', ''), (attribute, None)]+GM.Globals[GM.EXTRA_ARGS_LIST])
  dbatch = croom.new_batch_http_request(callback=_callbackRemoveItemsFromCourse)
  bcount = 0
  j = 0
  for removeItem in removeItems:
    j += 1
    svcparms = svcargs.copy()
    if removeType in {Ent.STUDENT, Ent.TEACHER}:
      svcparms[attribute] = cleanItem = _getMain().normalizeEmailAddressOrUID(removeItem)
    elif removeType == Ent.COURSE_ALIAS:
      svcparms[attribute] = _getMain().addCourseAliasScope(removeItem)
      cleanItem = _getMain().removeCourseAliasScope(svcparms[attribute])
    elif removeType == Ent.COURSE_TOPIC:
      svcparms[attribute] = cleanItem = removeItem
    else: # removeType == Ent.COURSE_ANNOUNCEMENT:
      svcparms[attribute] = cleanItem = removeItem
    dbatch.add(method(**svcparms), request_id=_getMain().batchRequestID(noScopeCourseId, 0, 0, j, jcount, cleanItem, removeType))
    bcount += 1
    if bcount >= GC.Values[GC.BATCH_SIZE]:
      _getMain().executeBatch(dbatch)
      dbatch = croom.new_batch_http_request(callback=_callbackRemoveItemsFromCourse)
      bcount = 0
  if bcount > 0:
    dbatch.execute()
  Ind.Decrement()

def _updateCourseOwner(croom, courseId, owner, i, count):
  action = Act.Get()
  Act.Set(Act.UPDATE_OWNER)
  try:
    _getMain().callGAPI(croom.courses(), 'patch',
             throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION,
                           GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT,
                           GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
             id=courseId, body={'ownerId': owner}, updateMask='ownerId', fields='ownerId')
    _getMain().entityActionPerformed([Ent.COURSE, _getMain().removeCourseIdScope(courseId), Ent.TEACHER, owner], i, count)
  except (GAPI.notFound, GAPI.permissionDenied, GAPI.failedPrecondition,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalidArgument,
          GAPI.internalError, GAPI.serviceNotAvailable) as e:
    errMsg = str(e)
    if '@UserAlreadyOwner' not in errMsg:
      _getMain().entityActionFailedWarning([Ent.COURSE, _getMain().removeCourseIdScope(courseId), Ent.TEACHER, owner], errMsg, i, count)
    else:
      _getMain().entityActionPerformedMessage([Ent.COURSE, _getMain().removeCourseIdScope(courseId), Ent.TEACHER, owner], Msg.ALREADY_WAS_OWNER, i, count)
  Act.Set(action)

def getCourseAnnouncement(createCmd):
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in _getMain().SORF_TEXT_ARGUMENTS:
      body['text'] = _getMain().getStringOrFile(myarg, minLen=1, unescapeCRLF=True)[0]
    elif myarg == 'scheduledtime':
      body['scheduledTime'] = _getMain().getTimeOrDeltaFromNow()
    elif myarg == 'state':
      body['state'] = _getMain().getChoice(COURSE_STATE_MAPS[Cmd.OB_COURSE_ANNOUNCEMENT_ADD_STATE_LIST if createCmd else Cmd.OB_COURSE_ANNOUNCEMENT_UPDATE_STATE_LIST],
                                mapChoice=True)
    else:
      _getMain().unknownArgumentExit()
  if createCmd and 'text' not in body:
    _getMain().missingArgumentExit('text <String>')
  return body

ADD_REMOVE_UPDATE_ITEM_TYPES_MAP = {
  'alias': Ent.COURSE_ALIAS,
  'aliases': Ent.COURSE_ALIAS,
  'announcement': Ent.COURSE_ANNOUNCEMENT,
  'announcements': Ent.COURSE_ANNOUNCEMENT,
  'student': Ent.STUDENT,
  'students': Ent.STUDENT,
  'teacher': Ent.TEACHER,
  'teachers': Ent.TEACHER,
  'topic': Ent.COURSE_TOPIC,
  'topics': Ent.COURSE_TOPIC,
  }
CLEAR_SYNC_PARTICIPANT_TYPES_MAP = {
  'student': Ent.STUDENT,
  'students': Ent.STUDENT,
  'teacher': Ent.TEACHER,
  'teachers': Ent.TEACHER,
  }
PARTICIPANT_EN_MAP = {
  Ent.STUDENT: Cmd.ENTITY_STUDENTS,
  Ent.TEACHER: Cmd.ENTITY_TEACHERS,
  }

# gam courses <CourseEntity> create alias <CourseAliasEntity>
# gam course <CourseID> create alias <CourseAlias>
# gam courses <CourseEntity> create announcement
#	<CourseAnnouncementContent> [scheduledtime <Time>] [state draft|published]
# gam course <CourseID> create announcement
#	<CourseAnnouncementContent> [scheduledtime <Time>] [state draft|published]
# gam courses <CourseEntity> create topic <CourseTopicEntity>
# gam course <CourseID> create topic <CourseTopic>
# gam courses <CourseEntity> create students <UserTypeEntity>
# gam course <CourseID> create student <EmailAddress>
# gam courses <CourseEntity> create teachers [makefirstteacherowner] <UserTypeEntity>
# gam course <CourseID> create teacher [makefirstteacherowner] <EmailAddress>
def doCourseAddItems(courseIdList, getEntityListArg):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  addType = _getMain().getChoice(ADD_REMOVE_UPDATE_ITEM_TYPES_MAP, mapChoice=True)
  if addType == Ent.TEACHER:
    makeFirstTeacherOwner = _getMain().checkArgumentPresent(['makefirstteacherowner'])
  else:
    makeFirstTeacherOwner = False
  if not getEntityListArg:
    if addType in {Ent.STUDENT, Ent.TEACHER}:
      addItems = _getMain().getStringReturnInList(Cmd.OB_EMAIL_ADDRESS)
    elif addType == Ent.COURSE_ALIAS:
      addItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_ALIAS)
    elif addType == Ent.COURSE_TOPIC:
      addItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_TOPIC)
    else: #elif addType == Ent.COURSE_ANNOUNCEMENT:
      addItems = [getCourseAnnouncement(True)]
    courseParticipantLists = None
  else:
    if addType in {Ent.STUDENT, Ent.TEACHER}:
      _, addItems = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                      typeMap={Cmd.ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[addType]},
                                      isSuspended=False, isArchived=False)
    elif addType == Ent.COURSE_ALIAS:
      addItems = _getMain().getEntityList(Cmd.OB_COURSE_ALIAS_ENTITY, shlexSplit=True)
    elif addType == Ent.COURSE_TOPIC:
      addItems = _getMain().getEntityList(Cmd.OB_COURSE_TOPIC_ENTITY, shlexSplit=True)
    else: # addType == Ent.COURSE_ANNOUNCEMENT:
      addItems = getCourseAnnouncement(True)
    courseParticipantLists = addItems if isinstance(addItems, dict) else None
  if courseParticipantLists is None:
    firstTeacher = None
    if makeFirstTeacherOwner and addItems:
      firstTeacher = _getMain().normalizeEmailAddressOrUID(addItems[0])
  _getMain().checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, addType in {Ent.COURSE_TOPIC, Ent.COURSE_ANNOUNCEMENT},
                                               addCIIdScope=courseParticipantLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseParticipantLists:
      addItems = courseParticipantLists[courseId]
      firstTeacher = None
      if makeFirstTeacherOwner and addItems:
        firstTeacher = _getMain().normalizeEmailAddressOrUID(addItems[0])
      courseId = _getMain().addCourseIdScope(courseId)
    _batchAddItemsToCourse(courseInfo['croom'], courseId, i, count, addItems, addType)
    if makeFirstTeacherOwner and firstTeacher:
      _updateCourseOwner(courseInfo['croom'], courseId, firstTeacher, i, count)

# gam courses <CourseEntity> remove alias <CourseAliasEntity>
# gam course <CourseID> remove alias <CourseAlias>
# gam courses <CourseEntity> remove announcement <CourseAnnouncementIDEntity>
# gam course <CourseID> remove announcement <CourseAnnouncementID>
# gam courses <CourseEntity> remove topic <CourseTopicIDEntity>
# gam course <CourseID> remove topic <CourseTopicID>
# gam courses <CourseEntity> remove teachers|students [owneracccess] <UserTypeEntity>
# gam course <CourseID> remove teacher|student [owneracccess] <EmailAddress>
def doCourseRemoveItems(courseIdList, getEntityListArg):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  removeType = _getMain().getChoice(ADD_REMOVE_UPDATE_ITEM_TYPES_MAP, mapChoice=True)
  if not getEntityListArg:
    if removeType in {Ent.STUDENT, Ent.TEACHER}:
      useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
      if _getMain().checkArgumentPresent(_getMain().OWNER_ACCESS_OPTIONS):
        useOwnerAccess = True
      removeItems = _getMain().getStringReturnInList(Cmd.OB_EMAIL_ADDRESS)
    elif removeType == Ent.COURSE_ALIAS:
      useOwnerAccess = False
      removeItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_ALIAS)
    elif removeType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      removeItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_TOPIC_ID)
    else: # removeType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      removeItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_ANNOUNCEMENT_ID)
    courseParticipantLists = None
  else:
    if removeType in {Ent.STUDENT, Ent.TEACHER}:
      useOwnerAccess = _getMain().checkArgumentPresent(_getMain().OWNER_ACCESS_OPTIONS)
      _, removeItems = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                         typeMap={Cmd.ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[removeType]})
    elif removeType == Ent.COURSE_ALIAS:
      useOwnerAccess = False
      removeItems = _getMain().getEntityList(Cmd.OB_COURSE_ALIAS_ENTITY, shlexSplit=True)
    elif removeType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      removeItems = _getMain().getEntityList(Cmd.OB_COURSE_TOPIC_ID_ENTITY, shlexSplit=True)
    else: # removeType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      removeItems = _getMain().getEntityList(Cmd.OB_COURSE_ANNOUNCEMENT_ID_ENTITY, shlexSplit=True)
    courseParticipantLists = removeItems if isinstance(removeItems, dict) else None
  _getMain().checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, useOwnerAccess,
                                               addCIIdScope=courseParticipantLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseParticipantLists:
      removeItems = courseParticipantLists[courseId]
      courseId = _getMain().addCourseIdScope(courseId)
    _batchRemoveItemsFromCourse(courseInfo['croom'], courseId, i, count, removeItems, removeType)

# gam courses <CourseEntity> update announcement <CourseAnnouncemntIDEntity>
#	[<CourseAnnouncementContent>] [scheduledtime <Time>] [state published]
# gam course <CourseID> update announcement <CourseAnnouncementID>
#	[<CourseAnnouncementContent>] [scheduledtime <Time>] [state published]
# gam courses <CourseEntity> update topic <CourseTopicIDEntity> <CourseTopic>
# gam course <CourseID> update topic <CourseTopicID> <CourseTopic>
def doCourseUpdateItems(courseIdList, getEntityListArg):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  updateType = _getMain().getChoice(ADD_REMOVE_UPDATE_ITEM_TYPES_MAP, mapChoice=True)
  if not getEntityListArg:
    if updateType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      updateItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_TOPIC_ID)
      body = {'name': _getMain().getString(Cmd.OB_COURSE_TOPIC)}
    else: # updateType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      updateItems = _getMain().getStringReturnInList(Cmd.OB_COURSE_ANNOUNCEMENT_ID)
      body = getCourseAnnouncement(False)
    courseItemLists = None
  else:
    if updateType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      updateItems = _getMain().getEntityList(Cmd.OB_COURSE_TOPIC_ID_ENTITY, shlexSplit=True)
      body = {'name': _getMain().getString(Cmd.OB_COURSE_TOPIC)}
    else: # updateType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      updateItems = _getMain().getEntityList(Cmd.OB_COURSE_ANNOUNCEMENT_ID_ENTITY, shlexSplit=True)
      body = getCourseAnnouncement(False)
    courseItemLists = updateItems if isinstance(updateItems, dict) else None
  _getMain().checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, useOwnerAccess,
                                               addCIIdScope=courseItemLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseItemLists:
      updateItems = courseItemLists[courseId]
      courseId = _getMain().addCourseIdScope(courseId)
    jcount = len(updateItems)
    noScopeCourseId = _getMain().removeCourseIdScope(courseId)
    if updateType == Ent.COURSE_TOPIC:
      service = courseInfo['croom'].courses().topics()
    else: # updateType == Ent.COURSE_ANNOUNCEMENT:
      service = courseInfo['croom'].courses().announcements()
    _getMain().entityPerformActionNumItems([Ent.COURSE, noScopeCourseId], jcount, updateType, i, count)
    Ind.Increment()
    j = 0
    for updateItem in updateItems:
      j += 1
      try:
        _getMain().callGAPI(service, 'patch',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED,
                               GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE],
                 retryReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE],
                 courseId=_getMain().addCourseIdScope(courseId), id=updateItem, updateMask=','.join(body.keys()), body=body, fields='')
        _getMain().entityActionPerformed([Ent.COURSE, courseId, updateType, updateItem], j, jcount)
      except GAPI.notFound:
        _getMain().entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], Msg.DOES_NOT_EXIST, j, jcount)
      except GAPI.forbidden:
        _getMain().entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], Msg.FORBIDDEN, j, jcount)
      except GAPI.permissionDenied:
        _getMain().entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], Msg.PERMISSION_DENIED, j, jcount)
      except (GAPI.quotaExceeded, GAPI.serviceNotAvailable) as e:
        _getMain().entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], str(e), j, jcount)
    Ind.Decrement()

# gam courses <CourseEntity> clear teachers|students
# gam course <CourseID> clear teacher|student
def doCourseClearParticipants(courseIdList, _):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  role = _getMain().getChoice(CLEAR_SYNC_PARTICIPANT_TYPES_MAP, mapChoice=True)
  _getMain().checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, GC.Values[GC.USE_COURSE_OWNER_ACCESS])
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    removeParticipants = _getMain().getItemsToModify(PARTICIPANT_EN_MAP[role], courseId, noListConversion=True)
    if GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE]:
      continue
    _batchRemoveItemsFromCourse(courseInfo['croom'], courseId, i, count, removeParticipants, role)

# gam courses <CourseEntity> sync students [addonly|removeonly] <UserTypeEntity>
# gam course <CourseID> sync students [addonly|removeonly] <UserTypeEntity>
# gam courses <CourseEntity> sync teachers [addonly|removeonly] [makefirstteacherowner] <UserTypeEntity>
# gam course <CourseID> sync teachers [addonly|removeonly] [makefirstteacherowner] <UserTypeEntity>
def doCourseSyncParticipants(courseIdList, _):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  role = _getMain().getChoice(CLEAR_SYNC_PARTICIPANT_TYPES_MAP, mapChoice=True)
  if role == Ent.TEACHER:
    makeFirstTeacherOwner = _getMain().checkArgumentPresent(['makefirstteacherowner'])
  else:
    makeFirstTeacherOwner = False
  syncOperation = _getMain().getSyncOperation()
  _, syncParticipants = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                          typeMap={Cmd.ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[role]},
                                          isSuspended=False, isArchived=False)
  _getMain().checkForExtraneousArguments()
  courseParticipantLists = syncParticipants if isinstance(syncParticipants, dict) else None
  if courseParticipantLists is None:
    syncParticipantsSet = set()
    firstTeacher = None
    if syncParticipants:
      for user in syncParticipants:
        syncParticipantsSet.add(_getMain().normalizeEmailAddressOrUID(user))
      if makeFirstTeacherOwner:
        firstTeacher = _getMain().normalizeEmailAddressOrUID(syncParticipants[0])
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, GC.Values[GC.USE_COURSE_OWNER_ACCESS],
                                               addCIIdScope=courseParticipantLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseParticipantLists:
      syncParticipantsSet = set()
      firstTeacher = None
      if courseParticipantLists[courseId]:
        for user in courseParticipantLists[courseId]:
          syncParticipantsSet.add(_getMain().normalizeEmailAddressOrUID(user))
        if makeFirstTeacherOwner:
          firstTeacher = _getMain().normalizeEmailAddressOrUID(courseParticipantLists[courseId][0])
        courseId = _getMain().addCourseIdScope(courseId)
    currentParticipantsSet = set()
    currentParticipants = _getMain().getItemsToModify(PARTICIPANT_EN_MAP[role], courseId, noListConversion=True)
    if GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE]:
      continue
    for user in currentParticipants:
      currentParticipantsSet.add(_getMain().normalizeEmailAddressOrUID(user))
    if syncOperation != 'removeonly':
      _batchAddItemsToCourse(croom, courseId, i, count, list(syncParticipantsSet-currentParticipantsSet), role)
    if makeFirstTeacherOwner and firstTeacher:
      _updateCourseOwner(croom, courseId, firstTeacher, i, count)
    if syncOperation != 'addonly':
      _batchRemoveItemsFromCourse(courseInfo['croom'], courseId, i, count, list(currentParticipantsSet-syncParticipantsSet), role)

