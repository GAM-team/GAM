"""Course participant management: add, remove, sync, clear.

Part of the _courses_tmp sub-package."""

"""GAM Google Classroom course management."""

import re
import json

from gam.util.csv_pf import RI_ENTITY, RI_J, RI_JCOUNT, RI_ITEM

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.api import buildGAPIObject, callGAPI, checkGAPIError, waitOnFailure
from gam.util.args import (
    SORF_TEXT_ARGUMENTS,
    addCourseAliasScope,
    addCourseIdScope,
    checkArgumentPresent,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getHTTPError,
    getInteger,
    getPhraseDNEorSNA,
    getString,
    getStringOrFile,
    getStringReturnInList,
    getTimeOrDeltaFromNow,
    normalizeEmailAddressOrUID,
    removeCourseAliasScope,
    removeCourseIdScope,
)
from gam.util.csv_pf import CSVPrintFile, FormatJSONQuoteChar, batchRequestID, flattenJSON
from gam.util.display import entityActionFailedWarning, entityActionPerformed, entityActionPerformedMessage, entityPerformActionNumItems
from gam.util.entity import getEntityList, getEntityToModify, getItemsToModify
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.output import executeBatch, writeStdout
from gam.constants import OWNER_ACCESS_OPTIONS
from gam.cmd.groups.groups import getSyncOperation
from gam.var import Act, Cmd, Ent, Ind

def doPrintCourseParticipants():
  croom = buildGAPIObject(API.CLASSROOM)
  csvPF = CSVPrintFile(['courseId', 'courseName'])
  FJQC = FormatJSONQuoteChar(csvPF)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties(['name'])
  courseShowProperties['members'] = 'all'
  showItemCountOnly = False
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'show':
      courseShowProperties['members'] = getChoice(COURSE_MEMBER_ARGUMENTS)
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if coursesInfo is None:
    if showItemCountOnly:
      writeStdout('0\n')
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
            csvPF.WriteRowTitles(flattenJSON(member, flattened={'courseId': courseId, 'courseName': course['name'], 'userRole': 'TEACHER'}))
        if courseShowProperties['members'] != 'teachers':
          for member in students:
            csvPF.WriteRowTitles(flattenJSON(member, flattened={'courseId': courseId, 'courseName': course['name'], 'userRole': 'STUDENT'}))
    else:
      row = {'courseId': courseId, 'courseName': course['name']}
      if courseShowProperties['members'] != 'none':
        if courseShowProperties['members'] != 'students':
          row['JSON-teachers'] = json.dumps(list(teachers))
        if courseShowProperties['members'] != 'teachers':
          row['JSON-students'] = json.dumps(list(students))
      csvPF.WriteRowNoFilter(row)
  if showItemCountOnly:
    writeStdout(f'{itemCount}\n')
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
  croom = buildGAPIObject(API.CLASSROOM)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties()
  courseShowProperties['members'] = getChoice(COURSE_COUNTS_MEMBER_ARGUMENTS)
  keyTitle = COURSE_COUNTS_KEY_TITLE[courseShowProperties['members']]
  csvPF = CSVPrintFile([keyTitle, 'CourseCount'])
  FJQC = FormatJSONQuoteChar(csvPF)
  minCount = 0
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'mincount':
      minCount = getInteger(minVal=0)
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
      entityActionPerformed([Ent.COURSE, ri[RI_ENTITY], addType, riItem], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if (reason not in {GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE}) and ((reason != GAPI.NOT_FOUND) or (addType == Ent.COURSE_ALIAS)):
        if reason in [GAPI.FORBIDDEN, GAPI.BACKEND_ERROR]:
          errMsg = getPhraseDNEorSNA(riItem)
        else:
          errMsg = getHTTPError(_ADD_PART_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        return
      waitOnFailure(1, 10, reason, message)
      if addType in {Ent.STUDENT, Ent.TEACHER, Ent.COURSE_TOPIC}:
        rbody = {attribute: riItem}
      elif addType == Ent.COURSE_ALIAS:
        rbody = {attribute: addCourseAliasScope(riItem)}
      else: # addType == Ent.COURSE_ANNOUNCEMENT:
        rbody = ri[RI_ITEM]
      try:
        result = callGAPI(service, 'create',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR,
                                        GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION,
                                        GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE],
                          retryReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE], triesLimit=0 if reason != GAPI.NOT_FOUND else 3,
                          courseId=addCourseIdScope(ri[RI_ENTITY]), body=rbody, fields=returnFields)
        riItem = _addIdToResponse(result, riItem)
      except (GAPI.notFound, GAPI.backendError, GAPI.forbidden):
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], getPhraseDNEorSNA(riItem), int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.alreadyExists:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], Msg.DUPLICATE, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.failedPrecondition:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], Msg.NOT_ALLOWED, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except (GAPI.quotaExceeded, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], addType, riItem], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))

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
  noScopeCourseId = removeCourseIdScope(courseId)
  entityPerformActionNumItems([Ent.COURSE, noScopeCourseId], jcount, addType, i, count)
  Ind.Increment()
  svcargs = dict([('courseId', courseId), ('body', {attribute: None}), ('fields', returnFields)]+GM.Globals[GM.EXTRA_ARGS_LIST])
  dbatch = croom.new_batch_http_request(callback=_callbackAddItemsToCourse)
  bcount = 0
  j = 0
  for addItem in addItems:
    j += 1
    svcparms = svcargs.copy()
    if addType in {Ent.STUDENT, Ent.TEACHER}:
      svcparms['body'][attribute] = cleanItem = normalizeEmailAddressOrUID(addItem)
    elif addType == Ent.COURSE_ALIAS:
      svcparms['body'][attribute] = addCourseAliasScope(addItem)
      cleanItem = removeCourseAliasScope(svcparms['body'][attribute])
    elif addType == Ent.COURSE_TOPIC:
      svcparms['body'][attribute] = cleanItem = addItem
    else: # addType == Ent.COURSE_ANNOUNCEMENT:
      svcparms['body'] = cleanItem = addItem
    dbatch.add(method(**svcparms), request_id=batchRequestID(noScopeCourseId, 0, 0, j, jcount, cleanItem, addType))
    bcount += 1
    if bcount >= GC.Values[GC.BATCH_SIZE]:
      executeBatch(dbatch)
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
      entityActionPerformed([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      http_status, reason, message = checkGAPIError(exception)
      if reason not in {GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE}:
        if reason == GAPI.NOT_FOUND and removeType != Ent.COURSE_ALIAS:
          errMsg = f'{Msg.NOT_A} {Ent.Singular(removeType)}'
        else:
          errMsg = getHTTPError(_REMOVE_PART_REASON_TO_MESSAGE_MAP, http_status, reason, message)
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        return
      waitOnFailure(1, 10, reason, message)
      if removeType in {Ent.STUDENT, Ent.TEACHER, Ent.COURSE_TOPIC, Ent.COURSE_ANNOUNCEMENT}:
        rbody = {attribute: riItem}
      else: # removeType == Ent.COURSE_ALIAS:
        rbody = {attribute: addCourseAliasScope(riItem)}
      try:
        callGAPI(service, 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED,
                               GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE, GAPI.FAILED_PRECONDITION],
                 retryReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE], triesLimit=0 if reason != GAPI.NOT_FOUND else 3,
                 courseId=addCourseIdScope(ri[RI_ENTITY]), body=rbody, fields='')
      except GAPI.notFound:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], Msg.DOES_NOT_EXIST, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.forbidden:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], Msg.FORBIDDEN, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except GAPI.permissionDenied:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], Msg.PERMISSION_DENIED, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      except (GAPI.quotaExceeded, GAPI.serviceNotAvailable, GAPI.failedPrecondition) as e:
        entityActionFailedWarning([Ent.COURSE, ri[RI_ENTITY], removeType, riItem], str(e), int(ri[RI_J]), int(ri[RI_JCOUNT]))

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
  noScopeCourseId = removeCourseIdScope(courseId)
  entityPerformActionNumItems([Ent.COURSE, noScopeCourseId], jcount, removeType, i, count)
  Ind.Increment()
  svcargs = dict([('courseId', courseId), ('fields', ''), (attribute, None)]+GM.Globals[GM.EXTRA_ARGS_LIST])
  dbatch = croom.new_batch_http_request(callback=_callbackRemoveItemsFromCourse)
  bcount = 0
  j = 0
  for removeItem in removeItems:
    j += 1
    svcparms = svcargs.copy()
    if removeType in {Ent.STUDENT, Ent.TEACHER}:
      svcparms[attribute] = cleanItem = normalizeEmailAddressOrUID(removeItem)
    elif removeType == Ent.COURSE_ALIAS:
      svcparms[attribute] = addCourseAliasScope(removeItem)
      cleanItem = removeCourseAliasScope(svcparms[attribute])
    elif removeType == Ent.COURSE_TOPIC:
      svcparms[attribute] = cleanItem = removeItem
    else: # removeType == Ent.COURSE_ANNOUNCEMENT:
      svcparms[attribute] = cleanItem = removeItem
    dbatch.add(method(**svcparms), request_id=batchRequestID(noScopeCourseId, 0, 0, j, jcount, cleanItem, removeType))
    bcount += 1
    if bcount >= GC.Values[GC.BATCH_SIZE]:
      executeBatch(dbatch)
      dbatch = croom.new_batch_http_request(callback=_callbackRemoveItemsFromCourse)
      bcount = 0
  if bcount > 0:
    dbatch.execute()
  Ind.Decrement()

def _updateCourseOwner(croom, courseId, owner, i, count):
  action = Act.Get()
  Act.Set(Act.UPDATE_OWNER)
  try:
    callGAPI(croom.courses(), 'patch',
             throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION,
                           GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT,
                           GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
             id=courseId, body={'ownerId': owner}, updateMask='ownerId', fields='ownerId')
    entityActionPerformed([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, owner], i, count)
  except (GAPI.notFound, GAPI.permissionDenied, GAPI.failedPrecondition,
          GAPI.forbidden, GAPI.badRequest, GAPI.invalidArgument,
          GAPI.internalError, GAPI.serviceNotAvailable) as e:
    errMsg = str(e)
    if '@UserAlreadyOwner' not in errMsg:
      entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, owner], errMsg, i, count)
    else:
      entityActionPerformedMessage([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, owner], Msg.ALREADY_WAS_OWNER, i, count)
  Act.Set(action)

def getCourseAnnouncement(createCmd):
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in SORF_TEXT_ARGUMENTS:
      body['text'] = getStringOrFile(myarg, minLen=1, unescapeCRLF=True)[0]
    elif myarg == 'scheduledtime':
      body['scheduledTime'] = getTimeOrDeltaFromNow()
    elif myarg == 'state':
      body['state'] = getChoice(COURSE_STATE_MAPS[Cmd.OB_COURSE_ANNOUNCEMENT_ADD_STATE_LIST if createCmd else Cmd.OB_COURSE_ANNOUNCEMENT_UPDATE_STATE_LIST],
                                mapChoice=True)
    else:
      unknownArgumentExit()
  if createCmd and 'text' not in body:
    missingArgumentExit('text <String>')
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
  croom = buildGAPIObject(API.CLASSROOM)
  addType = getChoice(ADD_REMOVE_UPDATE_ITEM_TYPES_MAP, mapChoice=True)
  if addType == Ent.TEACHER:
    makeFirstTeacherOwner = checkArgumentPresent(['makefirstteacherowner'])
  else:
    makeFirstTeacherOwner = False
  if not getEntityListArg:
    if addType in {Ent.STUDENT, Ent.TEACHER}:
      addItems = getStringReturnInList(Cmd.OB_EMAIL_ADDRESS)
    elif addType == Ent.COURSE_ALIAS:
      addItems = getStringReturnInList(Cmd.OB_COURSE_ALIAS)
    elif addType == Ent.COURSE_TOPIC:
      addItems = getStringReturnInList(Cmd.OB_COURSE_TOPIC)
    else: #elif addType == Ent.COURSE_ANNOUNCEMENT:
      addItems = [getCourseAnnouncement(True)]
    courseParticipantLists = None
  else:
    if addType in {Ent.STUDENT, Ent.TEACHER}:
      _, addItems = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                      typeMap={Cmd.ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[addType]},
                                      isSuspended=False, isArchived=False)
    elif addType == Ent.COURSE_ALIAS:
      addItems = getEntityList(Cmd.OB_COURSE_ALIAS_ENTITY, shlexSplit=True)
    elif addType == Ent.COURSE_TOPIC:
      addItems = getEntityList(Cmd.OB_COURSE_TOPIC_ENTITY, shlexSplit=True)
    else: # addType == Ent.COURSE_ANNOUNCEMENT:
      addItems = getCourseAnnouncement(True)
    courseParticipantLists = addItems if isinstance(addItems, dict) else None
  if courseParticipantLists is None:
    firstTeacher = None
    if makeFirstTeacherOwner and addItems:
      firstTeacher = normalizeEmailAddressOrUID(addItems[0])
  checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, addType in {Ent.COURSE_TOPIC, Ent.COURSE_ANNOUNCEMENT},
                                               addCIIdScope=courseParticipantLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseParticipantLists:
      addItems = courseParticipantLists[courseId]
      firstTeacher = None
      if makeFirstTeacherOwner and addItems:
        firstTeacher = normalizeEmailAddressOrUID(addItems[0])
      courseId = addCourseIdScope(courseId)
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
  croom = buildGAPIObject(API.CLASSROOM)
  removeType = getChoice(ADD_REMOVE_UPDATE_ITEM_TYPES_MAP, mapChoice=True)
  if not getEntityListArg:
    if removeType in {Ent.STUDENT, Ent.TEACHER}:
      useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
      if checkArgumentPresent(OWNER_ACCESS_OPTIONS):
        useOwnerAccess = True
      removeItems = getStringReturnInList(Cmd.OB_EMAIL_ADDRESS)
    elif removeType == Ent.COURSE_ALIAS:
      useOwnerAccess = False
      removeItems = getStringReturnInList(Cmd.OB_COURSE_ALIAS)
    elif removeType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      removeItems = getStringReturnInList(Cmd.OB_COURSE_TOPIC_ID)
    else: # removeType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      removeItems = getStringReturnInList(Cmd.OB_COURSE_ANNOUNCEMENT_ID)
    courseParticipantLists = None
  else:
    if removeType in {Ent.STUDENT, Ent.TEACHER}:
      useOwnerAccess = checkArgumentPresent(OWNER_ACCESS_OPTIONS)
      _, removeItems = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                         typeMap={Cmd.ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[removeType]})
    elif removeType == Ent.COURSE_ALIAS:
      useOwnerAccess = False
      removeItems = getEntityList(Cmd.OB_COURSE_ALIAS_ENTITY, shlexSplit=True)
    elif removeType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      removeItems = getEntityList(Cmd.OB_COURSE_TOPIC_ID_ENTITY, shlexSplit=True)
    else: # removeType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      removeItems = getEntityList(Cmd.OB_COURSE_ANNOUNCEMENT_ID_ENTITY, shlexSplit=True)
    courseParticipantLists = removeItems if isinstance(removeItems, dict) else None
  checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, useOwnerAccess,
                                               addCIIdScope=courseParticipantLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseParticipantLists:
      removeItems = courseParticipantLists[courseId]
      courseId = addCourseIdScope(courseId)
    _batchRemoveItemsFromCourse(courseInfo['croom'], courseId, i, count, removeItems, removeType)

# gam courses <CourseEntity> update announcement <CourseAnnouncemntIDEntity>
#	[<CourseAnnouncementContent>] [scheduledtime <Time>] [state published]
# gam course <CourseID> update announcement <CourseAnnouncementID>
#	[<CourseAnnouncementContent>] [scheduledtime <Time>] [state published]
# gam courses <CourseEntity> update topic <CourseTopicIDEntity> <CourseTopic>
# gam course <CourseID> update topic <CourseTopicID> <CourseTopic>
def doCourseUpdateItems(courseIdList, getEntityListArg):
  croom = buildGAPIObject(API.CLASSROOM)
  updateType = getChoice(ADD_REMOVE_UPDATE_ITEM_TYPES_MAP, mapChoice=True)
  if not getEntityListArg:
    if updateType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      updateItems = getStringReturnInList(Cmd.OB_COURSE_TOPIC_ID)
      body = {'name': getString(Cmd.OB_COURSE_TOPIC)}
    else: # updateType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      updateItems = getStringReturnInList(Cmd.OB_COURSE_ANNOUNCEMENT_ID)
      body = getCourseAnnouncement(False)
    courseItemLists = None
  else:
    if updateType == Ent.COURSE_TOPIC:
      useOwnerAccess = True
      updateItems = getEntityList(Cmd.OB_COURSE_TOPIC_ID_ENTITY, shlexSplit=True)
      body = {'name': getString(Cmd.OB_COURSE_TOPIC)}
    else: # updateType == Ent.COURSE_ANNOUNCEMENT:
      useOwnerAccess = True
      updateItems = getEntityList(Cmd.OB_COURSE_ANNOUNCEMENT_ID_ENTITY, shlexSplit=True)
      body = getCourseAnnouncement(False)
    courseItemLists = updateItems if isinstance(updateItems, dict) else None
  checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, useOwnerAccess,
                                               addCIIdScope=courseItemLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseItemLists:
      updateItems = courseItemLists[courseId]
      courseId = addCourseIdScope(courseId)
    jcount = len(updateItems)
    noScopeCourseId = removeCourseIdScope(courseId)
    if updateType == Ent.COURSE_TOPIC:
      service = courseInfo['croom'].courses().topics()
    else: # updateType == Ent.COURSE_ANNOUNCEMENT:
      service = courseInfo['croom'].courses().announcements()
    entityPerformActionNumItems([Ent.COURSE, noScopeCourseId], jcount, updateType, i, count)
    Ind.Increment()
    j = 0
    for updateItem in updateItems:
      j += 1
      try:
        callGAPI(service, 'patch',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED,
                               GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE],
                 retryReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE],
                 courseId=addCourseIdScope(courseId), id=updateItem, updateMask=','.join(body.keys()), body=body, fields='')
        entityActionPerformed([Ent.COURSE, courseId, updateType, updateItem], j, jcount)
      except GAPI.notFound:
        entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], Msg.DOES_NOT_EXIST, j, jcount)
      except GAPI.forbidden:
        entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], Msg.FORBIDDEN, j, jcount)
      except GAPI.permissionDenied:
        entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], Msg.PERMISSION_DENIED, j, jcount)
      except (GAPI.quotaExceeded, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, courseId, updateType, updateItem], str(e), j, jcount)
    Ind.Decrement()

# gam courses <CourseEntity> clear teachers|students
# gam course <CourseID> clear teacher|student
def doCourseClearParticipants(courseIdList, _):
  croom = buildGAPIObject(API.CLASSROOM)
  role = getChoice(CLEAR_SYNC_PARTICIPANT_TYPES_MAP, mapChoice=True)
  checkForExtraneousArguments()
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, GC.Values[GC.USE_COURSE_OWNER_ACCESS])
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    removeParticipants = getItemsToModify(PARTICIPANT_EN_MAP[role], courseId, noListConversion=True)
    if GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE]:
      continue
    _batchRemoveItemsFromCourse(courseInfo['croom'], courseId, i, count, removeParticipants, role)

# gam courses <CourseEntity> sync students [addonly|removeonly] <UserTypeEntity>
# gam course <CourseID> sync students [addonly|removeonly] <UserTypeEntity>
# gam courses <CourseEntity> sync teachers [addonly|removeonly] [makefirstteacherowner] <UserTypeEntity>
# gam course <CourseID> sync teachers [addonly|removeonly] [makefirstteacherowner] <UserTypeEntity>
def doCourseSyncParticipants(courseIdList, _):
  croom = buildGAPIObject(API.CLASSROOM)
  role = getChoice(CLEAR_SYNC_PARTICIPANT_TYPES_MAP, mapChoice=True)
  if role == Ent.TEACHER:
    makeFirstTeacherOwner = checkArgumentPresent(['makefirstteacherowner'])
  else:
    makeFirstTeacherOwner = False
  syncOperation = getSyncOperation()
  _, syncParticipants = getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS,
                                          typeMap={Cmd.ENTITY_COURSEPARTICIPANTS: PARTICIPANT_EN_MAP[role]},
                                          isSuspended=False, isArchived=False)
  checkForExtraneousArguments()
  courseParticipantLists = syncParticipants if isinstance(syncParticipants, dict) else None
  if courseParticipantLists is None:
    syncParticipantsSet = set()
    firstTeacher = None
    if syncParticipants:
      for user in syncParticipants:
        syncParticipantsSet.add(normalizeEmailAddressOrUID(user))
      if makeFirstTeacherOwner:
        firstTeacher = normalizeEmailAddressOrUID(syncParticipants[0])
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, GC.Values[GC.USE_COURSE_OWNER_ACCESS],
                                               addCIIdScope=courseParticipantLists is None)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    if courseParticipantLists:
      syncParticipantsSet = set()
      firstTeacher = None
      if courseParticipantLists[courseId]:
        for user in courseParticipantLists[courseId]:
          syncParticipantsSet.add(normalizeEmailAddressOrUID(user))
        if makeFirstTeacherOwner:
          firstTeacher = normalizeEmailAddressOrUID(courseParticipantLists[courseId][0])
        courseId = addCourseIdScope(courseId)
    currentParticipantsSet = set()
    currentParticipants = getItemsToModify(PARTICIPANT_EN_MAP[role], courseId, noListConversion=True)
    if GM.Globals[GM.CLASSROOM_SERVICE_NOT_AVAILABLE]:
      continue
    for user in currentParticipants:
      currentParticipantsSet.add(normalizeEmailAddressOrUID(user))
    if syncOperation != 'removeonly':
      _batchAddItemsToCourse(croom, courseId, i, count, list(syncParticipantsSet-currentParticipantsSet), role)
    if makeFirstTeacherOwner and firstTeacher:
      _updateCourseOwner(croom, courseId, firstTeacher, i, count)
    if syncOperation != 'addonly':
      _batchRemoveItemsFromCourse(courseInfo['croom'], courseId, i, count, list(currentParticipantsSet-syncParticipantsSet), role)

# Dispatch tables and routing (moved from __init__.py)
# Additional imports for dispatch
from gam.constants import CMD_ACTION, CMD_FUNCTION

# Course command sub-commands
COURSE_SUBCOMMANDS = {
  'add': 			(Act.ADD, doCourseAddItems),
  'clear': 			(Act.REMOVE, doCourseClearParticipants),
  'remove': 			(Act.REMOVE, doCourseRemoveItems),
  'update': 			(Act.UPDATE, doCourseUpdateItems),
  'sync': 			(Act.SYNC, doCourseSyncParticipants),
  }

# Course sub-command aliases
COURSE_SUBCOMMAND_ALIASES = {
  'create':			'add',
  'del':			'remove',
  'delete':			'remove',
  }

def executeCourseCommands(courseIdList, getEntityListArg):
  CL_subCommand = getChoice(COURSE_SUBCOMMANDS, choiceAliases=COURSE_SUBCOMMAND_ALIASES)
  Act.Set(COURSE_SUBCOMMANDS[CL_subCommand][CMD_ACTION])
  COURSE_SUBCOMMANDS[CL_subCommand][CMD_FUNCTION](courseIdList, getEntityListArg)

def processCourseCommands():
  executeCourseCommands(getStringReturnInList(Cmd.OB_COURSE_ID), False)

def processCoursesCommands():
  executeCourseCommands(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True), True)

