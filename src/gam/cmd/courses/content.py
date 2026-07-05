"""Course announcements, topics, materials, work, and submissions.

Part of the _courses_tmp sub-package."""

"""GAM Google Classroom course management."""

import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gam.util.api import buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import (
    OrderBy,
    getArgument,
    getBoolean,
    getCharacter,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
)
from gam.util.display import entityActionFailedWarning, entityDoesNotHaveItemWarning, getPageMessageForWhom, printGettingAllEntityItemsForWhom
from gam.util.entity import getEntityList
from gam.util.course_scope import removeCourseIdScope

from gam.var import Cmd, Ent
from gam.cmd.courses.courses import (
    COURSE_ANNOUNCEMENTS_FIELDS_CHOICE_MAP,
    COURSE_ANNOUNCEMENTS_INDEXED_TITLES,
    COURSE_ANNOUNCEMENTS_ORDERBY_CHOICE_MAP,
    COURSE_ANNOUNCEMENTS_SORT_TITLES,
    COURSE_ANNOUNCEMENTS_TIME_OBJECTS,
    COURSE_CUS_FILTER_FIELDS_MAP,
    COURSE_CU_FILTER_FIELDS_MAP,
    COURSE_U_FILTER_FIELDS_MAP,
    _convertCourseUserIdToEmailName,
    _courseItemPassesFilter,
    _getCourseItemFilter,
    _getCourseSelectionParameters,
    _getCourseStates,
    _getCoursesInfo,
    _gettingCourseEntityQuery,
    _initCourseItemFilter,
    _initCourseSelectionParameters,
    _initCourseShowProperties,
    _printCourseItemCount,
    _setApplyCourseItemFilter,
)

def doPrintCourseAnnouncements():
  def _printCourseAnnouncement(course, courseAnnouncement, i, count):
    if applyCourseItemFilter and not _courseItemPassesFilter(courseAnnouncement, courseItemFilter):
      return
    if showCreatorEmail or showCreatorName:
      creatorUserEmail, creatorUserName = _convertCourseUserIdToEmailName(croom, courseAnnouncement['creatorUserId'], creatorEmails,
                                                                          [Ent.COURSE, course['id'], Ent.COURSE_ANNOUNCEMENT_ID, courseAnnouncement['id'],
                                                                           Ent.CREATOR_ID, courseAnnouncement['creatorUserId']], i, count)
      if showCreatorEmail:
        courseAnnouncement['creatorUserEmail'] = creatorUserEmail
      if showCreatorName:
        courseAnnouncement['creatorUserName'] = creatorUserName
    row = flattenJSON(courseAnnouncement, flattened={'courseId': course['id'], 'courseName': course['name']}, timeObjects=COURSE_ANNOUNCEMENTS_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'courseId': course['id'], 'courseName': course['name'],
                              'JSON': json.dumps(cleanJSON(courseAnnouncement, timeObjects=COURSE_ANNOUNCEMENTS_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  croom = buildGAPIObject(API.CLASSROOM)
  csvPF = CSVPrintFile(['courseId', 'courseName'], COURSE_ANNOUNCEMENTS_SORT_TITLES, COURSE_ANNOUNCEMENTS_INDEXED_TITLES)
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  courseSelectionParameters = _initCourseSelectionParameters()
  courseItemFilter = _initCourseItemFilter()
  courseShowProperties = _initCourseShowProperties(['name'])
  courseAnnouncementIds = []
  courseAnnouncementStates = []
  OBY = OrderBy(COURSE_ANNOUNCEMENTS_ORDERBY_CHOICE_MAP)
  creatorEmails = {}
  countsOnly = showCreatorEmail = showCreatorName = False
  items = 'courseAnnouncements'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif _getCourseItemFilter(myarg, courseItemFilter, COURSE_CUS_FILTER_FIELDS_MAP):
      pass
    elif myarg in {'announcementid', 'announcementids'}:
      courseAnnouncementIds = getEntityList(Cmd.OB_COURSE_ANNOUNCEMENT_ID_ENTITY)
    elif myarg in {'announcementstate', 'announcementstates'}:
      _getCourseStates(Cmd.OB_COURSE_ANNOUNCEMENT_STATE_LIST, courseAnnouncementStates)
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg in {'showcreatoremails', 'creatoremail'}:
      showCreatorEmail = True
    elif myarg in {'showcreatornames', 'creatorname'}:
      showCreatorName = True
    elif getFieldsList(myarg, COURSE_ANNOUNCEMENTS_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    elif myarg == 'countsonly':
      countsOnly = True
      csvPF.AddTitles(items)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties)
  if coursesInfo is None:
    return
  if countsOnly:
    csvPF.SetFormatJSON(False)
  applyCourseItemFilter = _setApplyCourseItemFilter(courseItemFilter, fieldsList)
  if showCreatorEmail and fieldsList:
    fieldsList.append('creatorUserId')
  courseAnnouncementIdsLists = courseAnnouncementIds if isinstance(courseAnnouncementIds, dict) else None
  i = 0
  count = len(coursesInfo)
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    if courseAnnouncementIdsLists:
      courseAnnouncementIds = courseAnnouncementIdsLists[courseId]
    if not courseAnnouncementIds:
      fields = getItemFieldsFromFieldsList('announcements', fieldsList)
      printGettingAllEntityItemsForWhom(Ent.COURSE_ANNOUNCEMENT_ID, Ent.TypeName(Ent.COURSE, courseId), i, count,
                                        _gettingCourseEntityQuery(Ent.COURSE_ANNOUNCEMENT_STATE, courseAnnouncementStates))
      try:
        results = callGAPIpages(croom.courses().announcements(), 'list', 'announcements',
                                pageMessage=getPageMessageForWhom(),
                                throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                courseId=courseId, announcementStates=courseAnnouncementStates, orderBy=OBY.orderBy,
                                fields=fields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        if not countsOnly:
          for courseAnnouncement in results:
            _printCourseAnnouncement(course, courseAnnouncement, i, count)
        else:
          _printCourseItemCount(course, results, items, applyCourseItemFilter, courseItemFilter, csvPF)
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
    else:
      jcount = len(courseAnnouncementIds)
      if jcount == 0:
        continue
      fields = f'{",".join(set(fieldsList))}' if fieldsList else None
      j = 0
      for courseAnnouncementId in courseAnnouncementIds:
        j += 1
        try:
          courseAnnouncement = callGAPI(croom.courses().announcements(), 'get',
                                        throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                        courseId=courseId, id=courseAnnouncementId, fields=fields)
          _printCourseAnnouncement(course, courseAnnouncement, i, count)
        except GAPI.notFound:
          entityDoesNotHaveItemWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_ANNOUNCEMENT_ID, courseAnnouncementId], j, jcount)
        except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
          entityActionFailedWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_ANNOUNCEMENT_ID, courseAnnouncementId], str(e), j, jcount)
  csvPF.writeCSVfile('Course Announcements')

COURSE_TOPICS_TIME_OBJECTS = {'updateTime'}
COURSE_TOPICS_SORT_TITLES = ['courseId', 'courseName', 'topicId', 'name', 'updateTime']

# gam print course-topics [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
#	[topicids <CourseTopicIDEntity>]
#	[timefilter updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[countsonly|(formatjson [quotechar <Character>])]
def doPrintCourseTopics():
  def _printCourseTopic(course, courseTopic):
    if applyCourseItemFilter and not _courseItemPassesFilter(courseTopic, courseItemFilter):
      return
    row = flattenJSON(courseTopic, flattened={'courseId': course['id'], 'courseName': course['name']}, timeObjects=COURSE_TOPICS_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'courseId': course['id'], 'courseName': course['name'],
                              'JSON': json.dumps(cleanJSON(courseTopic, timeObjects=COURSE_TOPICS_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  croom = buildGAPIObject(API.CLASSROOM)
  csvPF = CSVPrintFile(['courseId', 'courseName'], COURSE_TOPICS_SORT_TITLES)
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = ['topicId', 'name', 'updateTime']
  courseSelectionParameters = _initCourseSelectionParameters()
  courseItemFilter = _initCourseItemFilter()
  courseShowProperties = _initCourseShowProperties(['name'])
  courseTopicIds = []
  countsOnly = False
  items = 'courseTopics'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif _getCourseItemFilter(myarg, courseItemFilter, COURSE_U_FILTER_FIELDS_MAP):
      pass
    elif myarg in {'topicid', 'topicids'}:
      courseTopicIds = getEntityList(Cmd.OB_COURSE_TOPIC_ID_ENTITY)
    elif myarg == 'countsonly':
      countsOnly = True
      csvPF.AddTitles(items)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties)
  if coursesInfo is None:
    return
  if countsOnly:
    csvPF.SetFormatJSON(False)
  applyCourseItemFilter = _setApplyCourseItemFilter(courseItemFilter, fieldsList)
  courseTopicIdsLists = courseTopicIds if isinstance(courseTopicIds, dict) else None
  i = 0
  count = len(coursesInfo)
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    if courseTopicIdsLists:
      courseTopicIds = courseTopicIdsLists[courseId]
    if not courseTopicIds:
      fields = getItemFieldsFromFieldsList('topic', fieldsList)
      printGettingAllEntityItemsForWhom(Ent.COURSE_TOPIC, Ent.TypeName(Ent.COURSE, courseId), i, count)
      try:
        results = callGAPIpages(croom.courses().topics(), 'list', 'topic',
                                pageMessage=getPageMessageForWhom(),
                                throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                courseId=courseId,
                                fields=fields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        if not countsOnly:
          for courseTopic in results:
            _printCourseTopic(course, courseTopic)
        else:
          _printCourseItemCount(course, results, items, applyCourseItemFilter, courseItemFilter, csvPF)
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
    else:
      jcount = len(courseTopicIds)
      if jcount == 0:
        continue
      fields = getFieldsFromFieldsList(fieldsList)
      j = 0
      for courseTopicId in courseTopicIds:
        j += 1
        try:
          courseTopic = callGAPI(croom.courses().topics(), 'get',
                                 throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 courseId=courseId, id=courseTopicId, fields=fields)
          _printCourseTopic(course, courseTopic)
        except GAPI.notFound:
          entityDoesNotHaveItemWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_TOPIC_ID, courseTopicId], j, jcount)
        except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
          entityActionFailedWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_TOPIC_ID, courseTopicId], str(e), j, jcount)
  csvPF.writeCSVfile('Course Topics')

def _initCourseWMSelectionParameters():
  return {'courseWMIds': [], 'courseWMStates': []}

def _getCourseWMSelectionParameters(myarg, courseWMSelectionParameters,
                                    IDArguments, OBIDEntity,
                                    StateArguments, OBStateList):
  if myarg in IDArguments:
    courseWMSelectionParameters['courseWMIds'] = getEntityList(OBIDEntity)
  elif myarg in StateArguments:
    _getCourseStates(OBStateList, courseWMSelectionParameters['courseWMStates'])
  else:
    return False
  return True

COURSE_MATERIAL_ID_ARGUMENTS = {'materialid', 'materialids', 'coursematerialid', 'coursematerialids'}
COURSE_MATERIAL_STATE_ARGUMENTS = {'materialstate', 'materialstates', 'coursematerialstate', 'coursematerialstates'}
COURSE_MATERIAL_FIELDS_CHOICE_MAP = {
  'alternatelink': 'alternateLink',
  'assigneemode': 'assigneeMode',
  'courseid': 'courseId',
  'coursematerialid': 'id',
  'creationtime': 'creationTime',
  'creator': 'creatorUserId',
  'creatoruserid': 'creatorUserId',
  'description': 'description',
  'id': 'id',
  'individualstudentsoptions': 'individualStudentsOptions',
  'materialid': 'id',
  'materials': 'materials',
  'scheduledtime': 'scheduledTime',
  'state': 'state',
  'title': 'title',
  'topicid': 'topicId',
  'updatetime': 'updateTime',
  }
COURSE_MATERIAL_ORDERBY_CHOICE_MAP = {'updatetime': 'updateTime', 'updatedate': 'updateTime'}
COURSE_MATERIAL_TIME_OBJECTS = {'creationTime', 'scheduledTime', 'updateTime'}
COURSE_MATERIAL_SORT_TITLES = ['courseId', 'courseName', 'id', 'title', 'description', 'state']
COURSE_MATERIAL_INDEXED_TITLES = ['materials']

COURSE_WORK_ID_ARGUMENTS = {'workid', 'workids', 'courseworkid', 'courseworkids'}
COURSE_WORK_STATE_ARGUMENTS = {'workstate', 'workstates', 'courseworkstate', 'courseworkstates'}
COURSE_WORK_FIELDS_CHOICE_MAP = {
  'alternatelink': 'alternateLink',
  'assigneemode': 'assigneeMode',
  'courseid': 'courseId',
  'courseworkid': 'id',
  'courseworktype': 'workType',
  'creationtime': 'creationTime',
  'creator': 'creatorUserId',
  'creatoruserid': 'creatorUserId',
  'description': 'description',
  'duedate': 'dueDate',
  'duetime': 'dueTime',
  'id': 'id',
  'individualstudentsoptions': 'individualStudentsOptions',
  'materials': 'materials',
  'maxpoints': 'maxPoints',
  'scheduledtime': 'scheduledTime',
  'state': 'state',
  'submissionmodificationmode': 'submissionModificationMode',
  'title': 'title',
  'topicid': 'topicId',
  'updatetime': 'updateTime',
  'workid': 'id',
  'worktype': 'workType',
  }
COURSE_WORK_ORDERBY_CHOICE_MAP = {'duedate': 'dueDate', 'updatetime': 'updateTime', 'updatedate': 'updateTime'}
COURSE_WORK_TIME_OBJECTS = {'creationTime', 'scheduledTime', 'updateTime'}
COURSE_WORK_SORT_TITLES = ['courseId', 'courseName', 'id', 'title', 'description', 'state']
COURSE_WORK_INDEXED_TITLES = ['materials']

def doPrintCourseWM(entityIDType, entityStateType):
  def _getTopicNames(croom, courseId):
    topicNames = {}
    try:
      results = callGAPIpages(croom.courses().topics(), 'list', 'topic',
                              throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              courseId=courseId,
                              fields='nextPageToken,topic(topicId,name)', pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
      for courseTopic in results:
        topicNames[courseTopic['topicId']] = courseTopic['name']
    except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable):
      pass
    return topicNames

  def _printCourseWMrow(course, courseWM):
    row = flattenJSON(courseWM, flattened={'courseId': course['id'], 'courseName': course['name']}, timeObjects=TimeObjects,
                      simpleLists=['studentIds'] if showStudentsAsList else None, delimiter=delimiter)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'courseId': course['id'], 'courseName': course['name'],
                              'JSON': json.dumps(cleanJSON(courseWM, timeObjects=TimeObjects),
                                                 ensure_ascii=False, sort_keys=True)})

  def _printCourseWM(course, courseWM, i, count):
    if applyCourseItemFilter and not _courseItemPassesFilter(courseWM, courseItemFilter):
      return
    if showCreatorEmail or showCreatorName:
      creatorUserEmail, creatorUserName = _convertCourseUserIdToEmailName(croom, courseWM['creatorUserId'], creatorEmails,
                                                                          [Ent.COURSE, course['id'], entityIDType, courseWM['id'],
                                                                           Ent.CREATOR_ID, courseWM['creatorUserId']], i, count)
      if showCreatorEmail:
        courseWM['creatorUserEmail'] = creatorUserEmail
      if showCreatorName:
        courseWM['creatorUserName'] = creatorUserName
    if showTopicNames:
      topicId = courseWM.get('topicId')
      if topicId:
        courseWM['topicName'] = topicNames.get(topicId, topicId)
    if not oneItemPerRow or not courseWM.get('materials', []):
      _printCourseWMrow(course, courseWM)
    else:
      courseMaterials = courseWM.pop('materials')
      for courseMaterial in courseMaterials:
        courseWM['materials'] = courseMaterial
        _printCourseWMrow(course, courseWM)

  croom = buildGAPIObject(API.CLASSROOM)
  if entityIDType == Ent.COURSE_WORK_ID:
    SortTitles = COURSE_WORK_SORT_TITLES
    IndexedTitles = COURSE_WORK_INDEXED_TITLES
    TimeObjects = COURSE_WORK_TIME_OBJECTS
    OrderbyChoiceMap = COURSE_WORK_ORDERBY_CHOICE_MAP
    FieldsChoiceMap = COURSE_WORK_FIELDS_CHOICE_MAP
    IDArguments = COURSE_WORK_ID_ARGUMENTS
    OBIDEntity = Cmd.OB_COURSE_WORK_ID_ENTITY
    StateArguments = COURSE_WORK_STATE_ARGUMENTS
    OBStateList = Cmd.OB_COURSE_WORK_STATE_LIST
    CSVTitle = 'Course Work'
    service = croom.courses().courseWork()
    items = 'courseWork'
  else:
    SortTitles = COURSE_MATERIAL_SORT_TITLES
    IndexedTitles = COURSE_MATERIAL_INDEXED_TITLES
    TimeObjects = COURSE_MATERIAL_TIME_OBJECTS
    OrderbyChoiceMap = COURSE_MATERIAL_ORDERBY_CHOICE_MAP
    FieldsChoiceMap = COURSE_MATERIAL_FIELDS_CHOICE_MAP
    IDArguments = COURSE_MATERIAL_ID_ARGUMENTS
    OBIDEntity = Cmd.OB_COURSE_MATERIAL_ID_ENTITY
    StateArguments = COURSE_MATERIAL_STATE_ARGUMENTS
    OBStateList = Cmd.OB_COURSE_MATERIAL_STATE_LIST
    CSVTitle = 'Course Work Material'
    service = croom.courses().courseWorkMaterials()
    items = 'courseWorkMaterial'
  csvPF = CSVPrintFile(['courseId', 'courseName'], SortTitles, IndexedTitles)
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  courseSelectionParameters = _initCourseSelectionParameters()
  courseWMSelectionParameters = _initCourseWMSelectionParameters()
  courseItemFilter = _initCourseItemFilter()
  courseShowProperties = _initCourseShowProperties(['name'])
  OBY = OrderBy(OrderbyChoiceMap)
  creatorEmails = {}
  oneItemPerRow = showCreatorEmail = showCreatorName = showTopicNames = False
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  countsOnly = showStudentsAsList = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif _getCourseWMSelectionParameters(myarg, courseWMSelectionParameters,
                                         IDArguments, OBIDEntity,
                                         StateArguments, OBStateList):
      pass
    elif _getCourseItemFilter(myarg, courseItemFilter, COURSE_CUS_FILTER_FIELDS_MAP):
      pass
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg == 'oneitemperrow':
      oneItemPerRow = True
      csvPF.RemoveIndexedTitles('materials')
    elif myarg in {'showcreatoremails', 'creatoremail'}:
      showCreatorEmail = True
    elif myarg in {'showcreatornames', 'creatorname'}:
      showCreatorName = True
    elif myarg == 'showtopicnames':
      showTopicNames = True
    elif getFieldsList(myarg, FieldsChoiceMap, fieldsList, initialField='id'):
      pass
    elif myarg == 'showstudentsaslist':
      showStudentsAsList = getBoolean()
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'countsonly':
      countsOnly = True
      csvPF.AddTitles(items)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if (showCreatorEmail or showCreatorName)  and fieldsList:
    fieldsList.append('creatorUserId')
  if showTopicNames and fieldsList:
    fieldsList.append('topicId')
  if entityIDType == Ent.COURSE_WORK_ID:
    kwargs = {'courseWorkStates': courseWMSelectionParameters['courseWMStates']}
  else:
    kwargs = {'courseWorkMaterialStates': courseWMSelectionParameters['courseWMStates']}
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties)
  if coursesInfo is None:
    return
  if countsOnly:
    csvPF.SetFormatJSON(False)
  applyCourseItemFilter = _setApplyCourseItemFilter(courseItemFilter, fieldsList)
  courseWMIds = courseWMSelectionParameters['courseWMIds']
  courseWMIdsLists = courseWMIds if isinstance(courseWMIds, dict) else {}
  i = 0
  count = len(coursesInfo)
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    if showTopicNames:
      topicNames = _getTopicNames(croom, courseId)
    if courseWMIdsLists:
      courseWMIds = courseWMIdsLists[courseId]
    if not courseWMIds:
      fields = getItemFieldsFromFieldsList(items, fieldsList)
      printGettingAllEntityItemsForWhom(entityIDType, Ent.TypeName(Ent.COURSE, courseId), i, count,
                                        _gettingCourseEntityQuery(entityStateType, courseWMSelectionParameters['courseWMStates']))
      try:
        results = callGAPIpages(service, 'list', items,
                                pageMessage=getPageMessageForWhom(),
                                throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS,
                                courseId=courseId, orderBy=OBY.orderBy,
                                fields=fields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS], **kwargs)
        if not countsOnly:
          for courseWM in results:
            _printCourseWM(course, courseWM, i, count)
        else:
          _printCourseItemCount(course, results, items, applyCourseItemFilter, courseItemFilter, csvPF)
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument) as e:
        entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
    else:
      jcount = len(courseWMIds)
      if jcount == 0:
        continue
      fields = getFieldsFromFieldsList(fieldsList)
      j = 0
      for courseWMId in courseWMIds:
        j += 1
        try:
          courseWM = callGAPI(service, 'get',
                              throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS,
                              courseId=courseId, id=courseWMId, fields=fields)
          _printCourseWM(course, courseWM, i, count)
        except GAPI.notFound:
          entityDoesNotHaveItemWarning([Ent.COURSE_NAME, course['name'], entityIDType, courseWMId], j, jcount)
        except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument) as e:
          entityActionFailedWarning([Ent.COURSE_NAME, course['name'], entityIDType, courseWMId], str(e), j, jcount)
  csvPF.writeCSVfile(CSVTitle)

# gam print course-materials [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
#	(materialids <CourseMaterialIDEntity>)|((materialstates <CourseMaterialStateList>)*
#	(orderby <CourseMaterialsOrderByFieldName> [ascending|descending])*)
#	[showcreatoremails|creatoremail] [showcreatornames|creatorname] [showtopicnames]
#	[fields <CourseMaterialFieldNameList>]
#	[timefilter creationtime|updatetime|scheduledtime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[oneitemperrow]
#	[countsonly|(formatjson [quotechar <Character>])]
def doPrintCourseMaterials():
  doPrintCourseWM(Ent.COURSE_MATERIAL_ID, Ent.COURSE_MATERIAL_STATE)

# gam print course-work [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
#	(workids <CourseWorkIDEntity>)|((workstates <CourseWorkStateList>)*
#	(orderby <CourseWorkOrderByFieldName> [ascending|descending])*)
#	[showcreatoremails|creatoremail] [showcreatornames|creatorname] [showtopicnames]
#	[fields <CourseWorkFieldNameList>]
#	[showstudentsaslist [<Boolean>]] [delimiter <Character>]
#	[timefilter creationtime|updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[oneitemperrow]
#	[countsonly|(formatjson [quotechar <Character>])]
def doPrintCourseWork():
  doPrintCourseWM(Ent.COURSE_WORK_ID, Ent.COURSE_WORK_STATE)

COURSE_SUBMISSION_FIELDS_CHOICE_MAP = {
  'alternatelink': 'alternateLink',
  'assignedgrade': 'assignedGrade',
  'courseid': 'courseId',
  'coursesubmissionid': 'id',
  'courseworkid': 'courseWorkId',
  'courseworktype': 'courseWorkType',
  'creationtime': 'creationTime',
  'draftgrade': 'draftGrade',
  'id': 'id',
  'late': 'late',
  'state': 'state',
  'submissionhistory': 'submissionHistory',
  'submissionid': 'id',
  'updatetime': 'updateTime',
  'userid': 'userId',
  'workid': 'courseWorkId',
  'worktype': 'courseWorkType',
  }
COURSE_SUBMISSION_TIME_OBJECTS = {'creationTime', 'updateTime', 'gradeTimestamp', 'stateTimestamp'}

def _gettingCourseSubmissionQuery(courseSubmissionStates, late, userId):
  query = ''
  if courseSubmissionStates:
    query += f'{Ent.Choose(Ent.COURSE_SUBMISSION_STATE, len(courseSubmissionStates))}: {",".join(courseSubmissionStates)}, '
  if late:
    query += f'{late}, '
  if userId:
    query += f'{Ent.Singular(Ent.USER)}: {userId}, '
  if query:
    query = query[:-2]
  return query

# gam print course-submissions [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
#	(workids <CourseWorkIDEntity>)|((workstates <CourseWorkStateList>)*
#	(orderby <CourseWorkOrderByFieldName> [ascending|descending])*)
#	(submissionids <CourseSubmissionIDEntity>)|((submissionstates <CourseSubmissionStateList>)*) [late|notlate]
#	[fields <CourseSubmissionFieldNameList>] [showuserprofile]
#	[timefilter creationtime|updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[countsonly|(formatjson [quotechar <Character>])]
def doPrintCourseSubmissions():
  def _printCourseSubmission(course, courseSubmission):
    if applyCourseItemFilter and not _courseItemPassesFilter(courseSubmission, courseItemFilter):
      return
    if showUserProfile:
      userId = courseSubmission.get('userId')
      if userId:
        if userId not in userProfiles:
          try:
            userProfile = callGAPI(tcroom.userProfiles(), 'get',
                                   throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                   retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                   userId=userId, fields='emailAddress,name')
            userProfiles[userId] = {'profile': {'emailAddress': userProfile.get('emailAddress', ''), 'name': userProfile['name']}}
          except (GAPI.notFound, GAPI.permissionDenied, GAPI.serviceNotAvailable):
            userProfiles[userId] = {'profile': {'emailAddress': '', 'name': {'givenName': '', 'familyName': '', 'fullName': ''}}}
        courseSubmission.update(userProfiles[userId])
    row = flattenJSON(courseSubmission, flattened={'courseId': course['id'], 'courseName': course['name']}, timeObjects=COURSE_SUBMISSION_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'courseId': course['id'], 'courseName': course['name'],
                              'JSON': json.dumps(cleanJSON(courseSubmission, timeObjects=COURSE_SUBMISSION_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  croom = buildGAPIObject(API.CLASSROOM)
  csvPF = CSVPrintFile(['courseId', 'courseName'],
                       ['courseId', 'courseName', 'courseWorkId', 'id', 'userId',
                        f'profile{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}emailAddress',
                        f'profile{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}givenName',
                        f'profile{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}familyName',
                        f'profile{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}fullName',
                        'state'],
                       ['submissionHistory'])
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  courseSelectionParameters = _initCourseSelectionParameters()
  courseWMSelectionParameters = _initCourseWMSelectionParameters()
  courseItemFilter = _initCourseItemFilter()
  courseShowProperties = _initCourseShowProperties(['name'])
  courseSubmissionStates = []
  courseSubmissionIds = []
  OBY = OrderBy(COURSE_WORK_ORDERBY_CHOICE_MAP)
  late = None
  userProfiles = {}
  countsOnly = showUserProfile = False
  items = 'courseSubmissions'
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif _getCourseWMSelectionParameters(myarg, courseWMSelectionParameters,
                                         COURSE_WORK_ID_ARGUMENTS, Cmd.OB_COURSE_WORK_ID_ENTITY,
                                         COURSE_WORK_STATE_ARGUMENTS, Cmd.OB_COURSE_WORK_STATE_LIST):
      pass
    elif _getCourseItemFilter(myarg, courseItemFilter, COURSE_CU_FILTER_FIELDS_MAP):
      pass
    elif myarg == 'orderby':
      OBY.GetChoice()
    elif myarg in {'submissionid', 'submissionids', 'coursesubmissionid', 'coursesubmissionids'}:
      courseSubmissionIds = getEntityList(Cmd.OB_COURSE_SUBMISSION_ID_ENTITY)
    elif myarg in {'submissionstate', 'submissionstates', 'coursesubmissionstate', 'coursesubmissionstates'}:
      _getCourseStates(Cmd.OB_COURSE_SUBMISSION_STATE_LIST, courseSubmissionStates)
    elif myarg == 'late':
      late = 'LATE_ONLY'
    elif myarg == 'notlate':
      late = 'NOT_LATE_ONLY'
    elif myarg == 'showuserprofile':
      showUserProfile = True
    elif getFieldsList(myarg, COURSE_SUBMISSION_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    elif myarg == 'countsonly':
      countsOnly = True
      csvPF.AddTitles(items)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, getOwnerId=True)
  if coursesInfo is None:
    return
  if countsOnly:
    csvPF.SetFormatJSON(False)
  applyCourseItemFilter = _setApplyCourseItemFilter(courseItemFilter, fieldsList)
  courseWorkIds = courseWMSelectionParameters['courseWMIds']
  courseWorkIdsLists = courseWorkIds if isinstance(courseWorkIds, dict) else {}
  courseSubmissionIdsLists = courseSubmissionIds if isinstance(courseSubmissionIds, dict) else {}
  i = 0
  count = len(coursesInfo)
  for course in coursesInfo:
    i += 1
    _, tcroom = buildGAPIServiceObject(API.CLASSROOM, f"uid:{course['ownerId']}")
    if tcroom is None:
      continue
    submissionsCount = 0
    courseId = course['id']
    if courseWorkIdsLists:
      courseWorkIds = courseWorkIdsLists[courseId]
    if not courseWorkIds:
      printGettingAllEntityItemsForWhom(Ent.COURSE_WORK_ID, Ent.TypeName(Ent.COURSE, courseId), i, count,
                                        _gettingCourseEntityQuery(Ent.COURSE_WORK_STATE, courseWMSelectionParameters['courseWMStates']))
      try:
        results = callGAPIpages(croom.courses().courseWork(), 'list', 'courseWork',
                                pageMessage=getPageMessageForWhom(),
                                throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                courseId=courseId, courseWorkStates=courseWMSelectionParameters['courseWMStates'], orderBy=OBY.orderBy,
                                fields='nextPageToken,courseWork(id)', pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        courseWorkIdsForCourse = [courseWork['id'] for courseWork in results]
      except GAPI.notFound:
        continue
      except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
        continue
    else:
      courseWorkIdsForCourse = courseWorkIds
    jcount = len(courseWorkIdsForCourse)
    if jcount == 0:
      continue
    j = 0
    for courseWorkId in courseWorkIdsForCourse:
      j += 1
      if not courseSubmissionIds:
        fields = getItemFieldsFromFieldsList('studentSubmissions', fieldsList)
        printGettingAllEntityItemsForWhom(Ent.COURSE_SUBMISSION_ID, Ent.TypeName(Ent.COURSE_WORK_ID, courseWorkId), j, jcount,
                                          _gettingCourseSubmissionQuery(courseSubmissionStates, late, courseSelectionParameters['studentId']))
        try:
          results = callGAPIpages(croom.courses().courseWork().studentSubmissions(), 'list', 'studentSubmissions',
                                  pageMessage=getPageMessageForWhom(),
                                  throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  courseId=courseId, courseWorkId=courseWorkId, states=courseSubmissionStates, late=late, userId=courseSelectionParameters['studentId'],
                                  fields=fields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
          if not countsOnly:
            for submission in results:
              _printCourseSubmission(course, submission)
          else:
            submissionsCount += _printCourseItemCount(course, results, items, applyCourseItemFilter, courseItemFilter, None)
        except GAPI.notFound:
          entityDoesNotHaveItemWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_WORK_ID, courseWorkId], j, jcount)
        except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
          entityActionFailedWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_WORK_ID, courseWorkId], str(e), j, jcount)
      else:
        if courseSubmissionIdsLists:
          if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
            courseSubmissionIds = courseSubmissionIdsLists[courseWorkId]
          else:
            courseSubmissionIds = courseSubmissionIdsLists[courseId][courseWorkId]
        kcount = len(courseSubmissionIds)
        if kcount == 0:
          continue
        fields = f'{",".join(set(fieldsList))}' if fieldsList else None
        k = 0
        for courseSubmissionId in courseSubmissionIds:
          k += 1
          try:
            submission = callGAPI(croom.courses().courseWork().studentSubmissions(), 'get',
                                  throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  courseId=courseId, courseWorkId=courseWorkId, id=courseSubmissionId,
                                  fields=fields)
            _printCourseSubmission(course, submission)
          except GAPI.notFound:
            entityDoesNotHaveItemWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_WORK_ID, courseWorkId, Ent.COURSE_SUBMISSION_ID, courseSubmissionId], k, kcount)
          except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
            entityActionFailedWarning([Ent.COURSE_NAME, course['name'], Ent.COURSE_WORK_ID, courseWorkId, Ent.COURSE_SUBMISSION_ID, courseSubmissionId], str(e), k, kcount)
    if countsOnly:
      csvPF.WriteRowTitles({'courseId': course['id'], 'courseName': course['name'], items: submissionsCount})
  csvPF.writeCSVfile('Course Submissions')

COURSE_PARTICIPANTS_SORT_TITLES = ['courseId', 'courseName', 'userRole', 'userId']

# gam print course-participants [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[show all|students|teachers]
#	[showitemcountonly] [formatjson [quotechar <Character>]]
