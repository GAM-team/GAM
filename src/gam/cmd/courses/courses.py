"""Course CRUD, info, and listing operations.

Part of the _courses_tmp sub-package."""

"""GAM Google Classroom course management."""

import re
import json
import time

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, buildGAPIServiceObject, callGAPI, callGAPIpages
from gam.util.args import (
    addCourseIdScope,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getChoice,
    getCourseAlias,
    getEmailAddress,
    getPhraseDNEorSNA,
    getREPattern,
    getString,
    getStringReturnInList,
    getStringWithCRsNLs,
    getTimeOrDeltaFromNow,
    removeCourseAliasScope,
    removeCourseIdScope,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    _getFieldsList,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityDoesNotExistWarning,
    entityDoesNotHaveItemWarning,
    entityModifierItemValueListActionFailedWarning,
    entityModifierItemValueListActionNotPerformedWarning,
    entityModifierItemValueListActionPerformed,
    entityModifierNewValueActionPerformed,
    entityPerformActionModifierItemValueList,
    getPageMessage,
    getPageMessageForWhom,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItemForWhom,
    printKeyValueList,
    printLine,
)
from gam.util.entity import getEntityList
from gam.util.errors import invalidChoiceExit, missingArgumentExit, unknownArgumentExit
from gam.util.fileio import UNKNOWN
from gam.util.output import currentCount, formatKeyValueList, writeStdout
from gam.constants import OWNER_ACCESS_OPTIONS

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def checkCourseExists(croom, courseId, i=0, count=0, entityType=Ent.COURSE):
  courseId = addCourseIdScope(courseId)
  try:
    result = callGAPI(croom.courses(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      id=courseId, fields='id,ownerId')
    return result
  except GAPI.notFound:
    entityActionFailedWarning([entityType, removeCourseIdScope(courseId)], Msg.DOES_NOT_EXIST, i, count)
  except (GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
  return None

COURSE_MEMBER_ARGUMENTS = ['none', 'all', 'students', 'teachers']
COURSE_STATE_MAPS = {
  Cmd.OB_COURSE_STATE_LIST: {
    'active': 'ACTIVE',
    'archived': 'ARCHIVED',
    'provisioned': 'PROVISIONED',
    'declined': 'DECLINED',
    'suspended': 'SUSPENDED',
    },
  Cmd.OB_COURSE_ANNOUNCEMENT_STATE_LIST: {
    'draft': 'DRAFT',
    'published': 'PUBLISHED',
    'deleted': 'DELETED',
    },
  Cmd.OB_COURSE_ANNOUNCEMENT_ADD_STATE_LIST: {
    'draft': 'DRAFT',
    'published': 'PUBLISHED',
    },
  Cmd.OB_COURSE_ANNOUNCEMENT_UPDATE_STATE_LIST: {
    'published': 'PUBLISHED',
    },
  Cmd.OB_COURSE_WORK_STATE_LIST: {
    'draft': 'DRAFT',
    'published': 'PUBLISHED',
    'deleted': 'DELETED',
    },
  Cmd.OB_COURSE_MATERIAL_STATE_LIST: {
    'draft': 'DRAFT',
    'published': 'PUBLISHED',
    'deleted': 'DELETED',
    },
  Cmd.OB_COURSE_SUBMISSION_STATE_LIST: {
    'new': 'NEW',
    'created': 'CREATED',
    'turnedin': 'TURNED_IN',
    'returned': 'RETURNED',
    'reclaimedbystudent': 'RECLAIMED_BY_STUDENT',
    },
  }

def _getCourseStates(item, states):
  stateMap = COURSE_STATE_MAPS[item]
  for state in getString(item).lower().replace(',', ' ').split():
    if state == 'all':
      states.extend([stateMap[state] for state in stateMap])
    elif state in stateMap:
      states.append(stateMap[state])
    else:
      invalidChoiceExit(state, stateMap, True)

def _gettingCourseEntityQuery(entityType, courseWorkStates):
  query = ''
  if courseWorkStates:
    query += f'{Ent.Choose(entityType, len(courseWorkStates))}: {",".join(courseWorkStates)}, '
  if query:
    query = query[:-2]
  return query

class CourseAttributes():

  def __init__(self, croom, updateMode):
    self.croom = croom
    self.ocroom = croom
    self.tcroom = None
    self.updateMode = updateMode
    self.body = {}
    self.courseId = None
    self.ownerId = None
    self.markDraftAsPublished = False
    self.markPublishedAsDraft = False
    self.removeDueDate = False
    self.mapShareModeStudentCopy = None
    self.copyMaterialsFiles = False
    self.members = 'none'
    self.teachers = []
    self.students = []
    self.announcementStates = []
    self.courseAnnouncements = []
    self.materialStates = []
    self.courseMaterials = []
    self.workStates = []
    self.courseWorks = []
    self.individualStudentAnnouncements = 'copy'
    self.individualStudentMaterials = 'copy'
    self.individualStudentCourseWork = 'copy'
    self.copyTopics = False
    self.topicsById = {}
    self.reversedTopicIdList = []
    self.currDateTime = None
    self.csvPF = None

  COURSE_ANNOUNCEMENT_READONLY_FIELDS = [
    'alternateLink',
    'courseId',
    'creationTime',
    'creatorUserId',
    'updateTime',
    ]
  COURSE_MATERIAL_READONLY_FIELDS = [
    'alternateLink',
    'courseId',
    'creationTime',
    'creatorUserId',
    'updateTime',
    ]

  COURSE_COURSEWORK_READONLY_FIELDS = [
    'alternateLink',
    'assignment',
    'associatedWithDeveloper',
    'courseId',
    'creationTime',
    'creatorUserId',
    'updateTime',
    ]

  MAX_TITLE_DISPLAY_LENGTH = 34

  def trimTitle(self, title):
    if len(title) <= self.MAX_TITLE_DISPLAY_LENGTH:
      return title
    return title[:self.MAX_TITLE_DISPLAY_LENGTH]+'...'

  def CleanMaterials(self, body, entityType, entityId):
    if 'materials' not in body:
      return
    materials = body.pop('materials')
    body['materials'] = []
    for material in materials:
      if 'driveFile' in material:
        material['driveFile']['driveFile'].pop('title', None)
        material['driveFile']['driveFile'].pop('alternateLink', None)
        material['driveFile']['driveFile'].pop('thumbnailUrl', None)
        if material['driveFile'].get('shareMode', '') == 'STUDENT_COPY' and self.mapShareModeStudentCopy is not None:
          material['driveFile']['shareMode'] = self.mapShareModeStudentCopy
        body['materials'].append(material)
        if self.csvPF and not self.copyMaterialsFiles:
          self.csvPF.WriteRow({'courseId': self.courseId, 'ownerId': self.ownerId, 'fileId': material['driveFile']['driveFile']['id']})
      elif 'youtubeVideo' in material:
        material['youtubeVideo'].pop('title', None)
        material['youtubeVideo'].pop('alternateLink', None)
        material['youtubeVideo'].pop('thumbnailUrl', None)
        body['materials'].append(material)
      elif 'link' in material:
        material['link'].pop('title', None)
        material['link'].pop('thumbnailUrl', None)
        body['materials'].append(material)
      elif 'form' in material:
        action = Act.Get()
        Act.Set(Act.COPY)
        entityActionNotPerformedWarning([Ent.COURSE, self.courseId, entityType, entityId,
                                         Ent.COURSE_MATERIAL_FORM, self.trimTitle(material['form'].get('title', UNKNOWN))],
                                        Msg.NOT_COPYABLE)
        Act.Set(action)

  @staticmethod
  def CleanAssignments(body):
    if 'assignment' in body and 'studentWorkFolder' in body['assignment']:
      body['assignment']['studentWorkFolder'].pop('title', None)
      body['assignment']['studentWorkFolder'].pop('alternateLink', None)

  COURSE_MATERIAL_SHAREMODE_MAP = {
    'edit': 'EDIT',
    'none': None,
    'view': 'VIEW'
    }

  COURSE_INDIVIDUAL_STUDENT_OPTIONS = {'copy', 'delete', 'maptoall'}

  def GetAttributes(self):
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if not self.updateMode and myarg in {'alias', 'id'}:
        self.body['id'] = getCourseAlias()
      elif myarg == 'name':
        self.body['name'] = getString(Cmd.OB_STRING)
      elif myarg == 'section':
        self.body['section'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg in {'heading', 'descriptionheading'}:
        self.body['descriptionHeading'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg == 'description':
        self.body['description'] = getStringWithCRsNLs()
      elif myarg == 'room':
        self.body['room'] = getString(Cmd.OB_STRING, minLen=0)
      elif myarg in {'owner', 'ownerid', 'teacher'}:
        self.body['ownerId'] = getEmailAddress()
      elif myarg in {'state', 'status', 'coursestate'}:
        self.body['courseState'] = getChoice(COURSE_STATE_MAPS[Cmd.OB_COURSE_STATE_LIST], mapChoice=True)
      elif myarg == 'guardiansenabled':
        self.body['guardiansEnabled'] = getBoolean()
      elif myarg == 'copyfrom':
        self.courseId = getString(Cmd.OB_COURSE_ID)
      elif myarg in {'announcementstate', 'announcementstates'}:
        _getCourseStates(Cmd.OB_COURSE_ANNOUNCEMENT_STATE_LIST, self.announcementStates)
      elif myarg in {'workstate', 'workstates', 'courseworkstate', 'courseworkstates'}:
        _getCourseStates(Cmd.OB_COURSE_WORK_STATE_LIST, self.workStates)
      elif myarg in {'materialstate', 'materialstates', 'coursematerialstate', 'coursematerialstates'}:
        _getCourseStates(Cmd.OB_COURSE_MATERIAL_STATE_LIST, self.materialStates)
      elif myarg == 'individualstudentannouncements':
        self.individualStudentAnnouncements = getChoice(self.COURSE_INDIVIDUAL_STUDENT_OPTIONS)
      elif myarg == 'individualstudentmaterials':
        self.individualStudentMaterials = getChoice(self.COURSE_INDIVIDUAL_STUDENT_OPTIONS)
      elif myarg == 'individualstudentcoursework':
        self.individualStudentCourseWork = getChoice(self.COURSE_INDIVIDUAL_STUDENT_OPTIONS)
      elif myarg == 'individualstudentassignments':
        self.individualStudentAnnouncements = self.individualStudentMaterials = self.individualStudentCourseWork =\
          getChoice(self.COURSE_INDIVIDUAL_STUDENT_OPTIONS)
      elif myarg == 'members':
        self.members = getChoice(COURSE_MEMBER_ARGUMENTS)
      elif myarg == 'markdraftaspublished':
        self.markDraftAsPublished = getBoolean()
      elif myarg == 'markpublishedasdraft':
        self.markPublishedAsDraft = getBoolean()
      elif myarg == 'removeduedate':
        self.removeDueDate = getBoolean()
      elif myarg == 'mapsharemodestudentcopy':
        self.mapShareModeStudentCopy = getChoice(self.COURSE_MATERIAL_SHAREMODE_MAP, mapChoice=True)
      elif myarg == 'copymaterialsfiles':
        self.copyMaterialsFiles = getBoolean()
      elif myarg == 'copytopics':
        self.copyTopics = getBoolean()
      elif myarg == 'logdrivefileids':
        if getBoolean():
          self.csvPF = CSVPrintFile(['courseId', 'ownerId', 'fileId'])
        else:
          self.csvPF = None
      else:
        unknownArgumentExit()
    if not self.updateMode:
      if 'ownerId' not in self.body:
        missingArgumentExit('teacher <UserItem>')
      if 'name' not in self.body:
        missingArgumentExit('name <String>')
    if self.courseId:
      copyFromCourseInfo = checkCourseExists(self.croom, self.courseId, entityType=Ent.COPYFROM_COURSE)
      if copyFromCourseInfo is None:
        return False
      self.ownerId = copyFromCourseInfo['ownerId']
      if (self.announcementStates or self.materialStates or self.workStates) and self.copyMaterialsFiles:
        self.body['courseState'] = 'ACTIVE'
    elif self.members != 'none' or self.announcementStates or self.materialStates or self.workStates or self.copyTopics:
      missingArgumentExit('copyfrom <CourseID>')
    else:
      return True
# ocroom - copyfrom course owner
    self.ocroom = self.croom
    if GC.Values[GC.USE_COURSE_OWNER_ACCESS]:
      if self.announcementStates or self.materialStates or self.workStates or self.copyTopics or self.members != 'none':
        _, self.ocroom = buildGAPIServiceObject(API.CLASSROOM, f'uid:{self.ownerId}')
        if self.ocroom is None:
          return False
    if self.members != 'none':
      _, self.teachers, self.students = _getCourseAliasesMembers(self.croom, self.ocroom, self.courseId, {'members': self.members},
                                                                 'nextPageToken,teachers(profile(emailAddress,id))',
                                                                 'nextPageToken,students(profile(emailAddress))')
    if self.announcementStates:
      printGettingAllEntityItemsForWhom(Ent.COURSE_ANNOUNCEMENT_ID, Ent.TypeName(Ent.COURSE, self.courseId), 0, 0,
                                        _gettingCourseEntityQuery(Ent.COURSE_ANNOUNCEMENT_STATE, self.announcementStates))
      try:
        self.courseAnnouncements = callGAPIpages(self.ocroom.courses().announcements(), 'list', 'announcements',
                                                 pageMessage=getPageMessageForWhom(),
                                                 throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                                 courseId=self.courseId, announcementStates=self.announcementStates,
                                                 pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        for courseAnnouncement in self.courseAnnouncements:
          for field in self.COURSE_ANNOUNCEMENT_READONLY_FIELDS:
            courseAnnouncement.pop(field, None)
          self.CleanMaterials(courseAnnouncement, Ent.COURSE_ANNOUNCEMENT_ID, courseAnnouncement['id'])
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, self.courseId], str(e))
        return False
    if self.materialStates:
      printGettingAllEntityItemsForWhom(Ent.COURSE_MATERIAL_ID, Ent.TypeName(Ent.COURSE, self.courseId), 0, 0,
                                        _gettingCourseEntityQuery(Ent.COURSE_MATERIAL_STATE, self.materialStates))
      try:
        self.courseMaterials = callGAPIpages(self.ocroom.courses().courseWorkMaterials(), 'list', 'courseWorkMaterial',
                                             pageMessage=getPageMessageForWhom(),
                                             throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                             courseId=self.courseId, courseWorkMaterialStates=self.materialStates,
                                             pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        for courseMaterial in self.courseMaterials:
          for field in self.COURSE_MATERIAL_READONLY_FIELDS:
            courseMaterial.pop(field, None)
          if self.markPublishedAsDraft and courseMaterial['state'] == 'PUBLISHED':
            courseMaterial['state'] = 'DRAFT'
          elif self.markDraftAsPublished and courseMaterial['state'] == 'DRAFT':
            courseMaterial['state'] = 'PUBLISHED'
          self.CleanMaterials(courseMaterial, Ent.COURSE_MATERIAL_ID, courseMaterial['id'])
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, self.courseId], str(e))
        return False
    if self.workStates:
      printGettingAllEntityItemsForWhom(Ent.COURSE_WORK_ID, Ent.TypeName(Ent.COURSE, self.courseId), 0, 0,
                                        _gettingCourseEntityQuery(Ent.COURSE_WORK_STATE, self.workStates))
      try:
        self.courseWorks = callGAPIpages(self.ocroom.courses().courseWork(), 'list', 'courseWork',
                                         pageMessage=getPageMessageForWhom(),
                                         throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                         retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                         courseId=self.courseId, courseWorkStates=self.workStates,
                                         pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        for courseWork in self.courseWorks:
          for field in self.COURSE_COURSEWORK_READONLY_FIELDS:
            courseWork.pop(field, None)
          self.CleanMaterials(courseWork, Ent.COURSE_WORK_ID, courseWork['id'])
          self.CleanAssignments(courseWork)
          if self.markPublishedAsDraft and courseWork['state'] == 'PUBLISHED':
            courseWork['state'] = 'DRAFT'
          elif self.markDraftAsPublished and courseWork['state'] == 'DRAFT':
            courseWork['state'] = 'PUBLISHED'
          if self.removeDueDate:
            courseWork.pop('dueDate', None)
            courseWork.pop('dueTime', None)
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, self.courseId], str(e))
        return False
    if self.copyTopics:
      printGettingAllEntityItemsForWhom(Ent.COURSE_TOPIC, Ent.TypeName(Ent.COURSE, self.courseId), 0, 0)
      try:
        courseTopics = callGAPIpages(self.ocroom.courses().topics(), 'list', 'topic',
                                     pageMessage=getPageMessageForWhom(),
                                     throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.SERVICE_NOT_AVAILABLE],
                                     retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                     courseId=self.courseId, fields='nextPageToken,topic(topicId,name)',
                                     pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        for topic in courseTopics:
          self.topicsById[topic['topicId']] = topic['name']
          self.reversedTopicIdList.append(topic['topicId'])
        self.reversedTopicIdList.reverse()
      except (GAPI.notFound, GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, self.courseId], str(e))
        return False
    return True

  def CopyMaterials(self, drive, newCourseId, body, entityType, entityId, teacherFolderId):
    def _copyMaterialsError(fileId, errMsg):
      entityModifierItemValueListActionNotPerformedWarning([Ent.COURSE, newCourseId, entityType, entityId, Ent.COURSE_MATERIAL_DRIVEFILE, ''], Act.MODIFIER_FROM,
                                                           [Ent.COURSE, self.courseId, Ent.COURSE_MATERIAL_DRIVEFILE, fileId], errMsg)

    if 'materials' not in body:
      return
    action = Act.Get()
    Act.Set(Act.COPY)
    materials = body.pop('materials')
    body['materials'] = []
    for material in materials:
      if 'driveFile' in material:
        fileId = material['driveFile']['driveFile']['id']
        try:
          source = callGAPI(drive.files(), 'get',
                            throwReasons=GAPI.DRIVE_GET_THROW_REASONS,
                            fileId=fileId,
                            fields='name,appProperties,capabilities,contentHints,copyRequiresWriterPermission,'\
                              'description,mimeType,modifiedTime,properties,starred,driveId,viewedByMeTime,writersCanShare',
                            supportsAllDrives=True)
          if not source.pop('capabilities')['canCopy']:
            _copyMaterialsError(fileId, Msg.NOT_COPYABLE)
            continue
          source['parents'] = [teacherFolderId]
          result = callGAPI(drive.files(), 'copy',
                            throwReasons=GAPI.DRIVE_COPY_THROW_REASONS,
                            fileId=fileId, body=source, fields='id', supportsAllDrives=True)
          material['driveFile']['driveFile']['id'] = result['id']
          body['materials'].append(material)
          entityModifierItemValueListActionPerformed([Ent.COURSE, newCourseId, entityType, entityId, Ent.COURSE_MATERIAL_DRIVEFILE, result['id']], Act.MODIFIER_FROM,
                                                     [Ent.COURSE, self.courseId, Ent.COURSE_MATERIAL_DRIVEFILE, fileId])
          if self.csvPF:
            self.csvPF.WriteRow({'courseId': self.courseId, 'ownerId': self.ownerId, 'fileId': result['id']})
        except (GAPI.fileNotFound, GAPI.forbidden, GAPI.internalError, GAPI.insufficientFilePermissions, GAPI.unknownError,
                GAPI.invalid, GAPI.cannotCopyFile, GAPI.badRequest, GAPI.responsePreparationFailure, GAPI.fileNeverWritable, GAPI.fieldNotWritable,
                GAPI.teamDrivesSharingRestrictionNotAllowed, GAPI.rateLimitExceeded, GAPI.userRateLimitExceeded) as e:
          _copyMaterialsError(fileId, str(e))
        except (GAPI.storageQuotaExceeded, GAPI.teamDriveFileLimitExceeded, GAPI.teamDriveHierarchyTooDeep) as e:
          _copyMaterialsError(fileId, str(e))
          break
        except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
          _copyMaterialsError(fileId, str(e))
          break
      else:
        body['materials'].append(material)
    Act.Set(action)

  def checkDueDate(self, body):
    if 'dueDate' in body and 'dueTime' in body:
      try:
        return self.currDateTime < arrow.Arrow(body['dueDate']['year'], body['dueDate']['month'], body['dueDate']['day'],
                                               body['dueTime'].get('hours', 0), body['dueTime'].get('minutes', 0), tzinfo='UTC')
      except ValueError:
        pass
    return False

  def getItemIdTitle(self, body):
    itemId = body.pop('id')
    return self.trimTitle(body.get('title', itemId))

  def checkItemCopyable(self, state, newCourseId, entityType, entityId, body, individualStudentOption, clarg, j, jcount):
    if state == 'DELETED':
      entityModifierItemValueListActionNotPerformedWarning([Ent.COURSE, newCourseId, entityType, entityId], Act.MODIFIER_FROM,
                                                           [Ent.COURSE, self.courseId], Msg.DELETED, j, jcount)
      return False
    if body['assigneeMode'] == 'INDIVIDUAL_STUDENTS':
      if individualStudentOption == 'delete':
        entityModifierItemValueListActionNotPerformedWarning([Ent.COURSE, newCourseId, entityType, entityId], Act.MODIFIER_FROM,
                                                             [Ent.COURSE, self.courseId], f'{clarg} delete', j, jcount)
        return False
      if individualStudentOption == 'maptoall':
        body['assigneeMode'] = 'ALL_STUDENTS'
        body.pop('individualStudentsOptions', None)
      else: # individualStudentOption == 'copy':
        if 'individualStudentsOptions' not in body:
          body['assigneeMode'] = 'ALL_STUDENTS'
    return True

  def CopyAttributes(self, newCourse, i=0, count=0):
    newCourseId = newCourse['id']
    ownerId = newCourse['ownerId']
    teacherFolderId = newCourse['teacherFolder']['id']
# tcroom - new/update course owner
    if self.announcementStates or self.materialStates or self.workStates or self.copyTopics:
      _, self.tcroom = buildGAPIServiceObject(API.CLASSROOM, f'uid:{ownerId}')
      if self.tcroom is None:
        return
    if (self.announcementStates or self.materialStates or self.workStates) and self.copyMaterialsFiles:
      _, tdrive = buildGAPIServiceObject(API.DRIVE3, f'uid:{ownerId}')
      if tdrive is None:
        return
# Adds are done with domain admin
    if self.members in {'all', 'students'}:
      addParticipants = [student['profile']['emailAddress'] for student in self.students if 'emailAddress' in student['profile']]
      _batchAddItemsToCourse(self.croom, newCourseId, i, count, addParticipants, Ent.STUDENT)
    if self.members in {'all', 'teachers'}:
      addParticipants = [teacher['profile']['emailAddress'] for teacher in self.teachers if teacher['profile']['id'] != ownerId and 'emailAddress' in teacher['profile']]
      _batchAddItemsToCourse(self.croom, newCourseId, i, count, addParticipants, Ent.TEACHER)
    if self.copyTopics:
      try:
        newCourseTopics = callGAPIpages(self.tcroom.courses().topics(), 'list', 'topic',
                                        throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.FAILED_PRECONDITION, GAPI.SERVICE_NOT_AVAILABLE],
                                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                        courseId=newCourseId, fields='nextPageToken,topic(topicId,name)',
                                        pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
        newTopicsByName = {}
        for topic in newCourseTopics:
          newTopicsByName[topic['name']] = topic['topicId']
      except GAPI.notFound as e:
        entityActionFailedWarning([Ent.COURSE, newCourseId], str(e), i, count)
        return
      except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.forbidden, GAPI.failedPrecondition, GAPI.invalidArgument, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, newCourseId], str(e), i, count)
      jcount = len(self.topicsById)
      j = 0
      for topicId in self.reversedTopicIdList:
        topicName = self.topicsById[topicId]
        j += 1
        if topicName in newTopicsByName:
          entityModifierItemValueListActionNotPerformedWarning([Ent.COURSE, newCourseId, Ent.COURSE_TOPIC, topicName], Act.MODIFIER_FROM,
                                                               [Ent.COURSE, self.courseId], Msg.DUPLICATE, j, jcount)
          continue
        try:
          result = callGAPI(self.tcroom.courses().topics(), 'create',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.FAILED_PRECONDITION, GAPI.INVALID_ARGUMENT, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            courseId=newCourseId, body={'name': topicName}, fields='topicId')
          newTopicsByName[topicName] = result['topicId']
          entityModifierItemValueListActionPerformed([Ent.COURSE, newCourseId, Ent.COURSE_TOPIC, topicName], Act.MODIFIER_FROM,
                                                     [Ent.COURSE, self.courseId], j, jcount)
        except (GAPI.notFound, GAPI.failedPrecondition, GAPI.invalidArgument, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
          entityModifierItemValueListActionFailedWarning([Ent.COURSE, newCourseId], Act.MODIFIER_FROM,
                                                         [Ent.COURSE, self.courseId, Ent.COURSE_TOPIC, topicName], str(e), j, jcount)
    if self.courseAnnouncements:
      jcount = len(self.courseAnnouncements)
      j = 0
      for courseAnnouncement in self.courseAnnouncements:
        j += 1
        body = courseAnnouncement.copy()
        courseAnnouncementId = self.getItemIdTitle(body)
        if not self.checkItemCopyable(courseAnnouncement['state'], newCourseId, Ent.COURSE_ANNOUNCEMENT, courseAnnouncementId,
                                      body, self.individualStudentAnnouncements, 'individualstudentannouncements', j, jcount):
          continue
        if self.copyMaterialsFiles:
          self.CopyMaterials(tdrive, newCourseId, body, Ent.COURSE_ANNOUNCEMENT, courseAnnouncementId, teacherFolderId)
        try:
          result = callGAPI(self.tcroom.courses().announcements(), 'create',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FORBIDDEN,
                                          GAPI.BAD_REQUEST, GAPI.FAILED_PRECONDITION, GAPI.BACKEND_ERROR, GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            courseId=newCourseId, body=body, fields='id')
          entityModifierItemValueListActionPerformed([Ent.COURSE, newCourseId, Ent.COURSE_ANNOUNCEMENT_ID, result['id']], Act.MODIFIER_FROM,
                                                     [Ent.COURSE, self.courseId, Ent.COURSE_ANNOUNCEMENT, courseAnnouncementId], j, jcount)
        except (GAPI.notFound, GAPI.badRequest, GAPI.failedPrecondition, GAPI.backendError, GAPI.internalError,
                GAPI.permissionDenied, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
          entityModifierItemValueListActionFailedWarning([Ent.COURSE, newCourseId], Act.MODIFIER_FROM,
                                                         [Ent.COURSE, self.courseId, Ent.COURSE_ANNOUNCEMENT, courseAnnouncementId], str(e), j, jcount)
    if self.courseMaterials:
      jcount = len(self.courseMaterials)
      j = 0
      for courseMaterial in self.courseMaterials:
        j += 1
        body = courseMaterial.copy()
        courseMaterialId = self.getItemIdTitle(body)
        if not self.checkItemCopyable(courseMaterial['state'], newCourseId, Ent.COURSE_MATERIAL, courseMaterialId,
                                      body, self.individualStudentMaterials, 'individualstudentmaterials', j, jcount):
          continue
        if self.copyMaterialsFiles:
          self.CopyMaterials(tdrive, newCourseId, body, Ent.COURSE_MATERIAL, courseMaterialId, teacherFolderId)
        topicId = body.pop('topicId', None)
        if self.copyTopics:
          if topicId:
            topicName = self.topicsById.get(topicId)
            if topicName:
              newTopicId = newTopicsByName.get(topicName)
              if newTopicId:
                body['topicId'] = newTopicId
        try:
          result = callGAPI(self.tcroom.courses().courseWorkMaterials(), 'create',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FORBIDDEN,
                                          GAPI.BAD_REQUEST, GAPI.FAILED_PRECONDITION, GAPI.BACKEND_ERROR, GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            courseId=newCourseId, body=body, fields='id')
          entityModifierItemValueListActionPerformed([Ent.COURSE, newCourseId, Ent.COURSE_MATERIAL_ID, result['id']], Act.MODIFIER_FROM,
                                                     [Ent.COURSE, self.courseId, Ent.COURSE_MATERIAL, courseMaterialId], j, jcount)
        except (GAPI.notFound, GAPI.badRequest, GAPI.failedPrecondition, GAPI.backendError, GAPI.internalError,
                GAPI.permissionDenied, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
          entityModifierItemValueListActionFailedWarning([Ent.COURSE, newCourseId], Act.MODIFIER_FROM,
                                                         [Ent.COURSE, self.courseId, Ent.COURSE_MATERIAL, courseMaterialId], str(e), j, jcount)
    if self.courseWorks:
      jcount = len(self.courseWorks)
      j = 0
      for courseWork in self.courseWorks:
        j += 1
        body = courseWork.copy()
        courseWorkId = self.getItemIdTitle(body)
        if not self.checkItemCopyable(courseWork['state'], newCourseId, Ent.COURSE_WORK, courseWorkId,
                                      body, self.individualStudentCourseWork, 'individualstudentcoursework', j, jcount):
          continue
        if self.copyMaterialsFiles:
          self.CopyMaterials(tdrive, newCourseId, body, Ent.COURSE_WORK, courseWorkId, teacherFolderId)
        topicId = body.pop('topicId', None)
        if self.copyTopics:
          if topicId:
            topicName = self.topicsById.get(topicId)
            if topicName:
              newTopicId = newTopicsByName.get(topicName)
              if newTopicId:
                body['topicId'] = newTopicId
        if not self.removeDueDate and not self.checkDueDate(body):
          body.pop('dueDate', None)
          body.pop('dueTime', None)
        try:
          result = callGAPI(self.tcroom.courses().courseWork(), 'create',
                            bailOnInternalError=True,
                            throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FORBIDDEN,
                                          GAPI.BAD_REQUEST, GAPI.FAILED_PRECONDITION, GAPI.BACKEND_ERROR,
                                          GAPI.INTERNAL_ERROR, GAPI.INVALID_ARGUMENT, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            courseId=newCourseId, body=body, fields='id')
          entityModifierItemValueListActionPerformed([Ent.COURSE, newCourseId, Ent.COURSE_WORK_ID, result['id']], Act.MODIFIER_FROM,
                                                     [Ent.COURSE, self.courseId, Ent.COURSE_WORK, courseWorkId], j, jcount)
        except (GAPI.notFound, GAPI.badRequest, GAPI.failedPrecondition, GAPI.backendError, GAPI.internalError, GAPI.invalidArgument,
                GAPI.permissionDenied, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
          entityModifierItemValueListActionFailedWarning([Ent.COURSE, newCourseId], Act.MODIFIER_FROM,
                                                         [Ent.COURSE, self.courseId, Ent.COURSE_WORK, courseWorkId], str(e), j, jcount)

  def CopyFromCourse(self, newCourse, i=0, count=0):
    action = Act.Get()
    Act.Set(Act.COPY)
    entityPerformActionModifierItemValueList([Ent.COURSE, newCourse['id']], Act.MODIFIER_FROM, [Ent.COURSE, self.courseId], i, count)
    Ind.Increment()
    if not self.removeDueDate:
      self.currDateTime = arrow.utcnow()
    self.CopyAttributes(newCourse, i, count)
    if self.csvPF:
      self.csvPF.writeCSVfile('Course Drive File IDs')
    Ind.Decrement()
    Act.Set(action)

# gam create course [id|alias <CourseAlias>] <CourseAttribute>*
#	 [copyfrom <CourseID>
#	    [announcementstates <CourseAnnouncementStateList>]
#		[individualstudentannouncements copy|delete|maptoall]
#	    [materialstates <CourseMaterialStateList>]
#		[individualstudentmaterials copy|delete|maptoall]
#	    [workstates <CourseWorkStateList>]
#		[individualstudentcoursework copy|delete|maptoall]
#		[removeduedate [<Boolean>]]
#		[mapsharemodestudentcopy edit|none|view]
#	    [individualstudentassignments copy|delete|maptoall]
#           [copymaterialsfiles [<Boolean>]]
#	    [copytopics [<Boolean>]]
#	    [markpublishedasdraft [<Boolean>]] [markdraftaspublished [<Boolean>]]
#	    [members none|all|students|teachers]]
#	    [logdrivefileids [<Boolean>]]
def doCreateCourse():
  croom = buildGAPIObject(API.CLASSROOM)
  courseAttributes = CourseAttributes(croom, False)
  if not courseAttributes.GetAttributes():
    return
  try:
    result = callGAPI(croom.courses(), 'create',
                      throwReasons=[GAPI.ALREADY_EXISTS, GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED,
                                    GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.SERVICE_NOT_AVAILABLE],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      body=courseAttributes.body, fields='id,name,ownerId,courseState,teacherFolder(id)')
    entityActionPerformed([Ent.COURSE_NAME, result['name'], Ent.COURSE, result['id']])
    if courseAttributes.courseId:
      courseAttributes.CopyFromCourse(result)
  except (GAPI.alreadyExists, GAPI.notFound, GAPI.permissionDenied, GAPI.failedPrecondition, GAPI.forbidden, GAPI.badRequest, GAPI.serviceNotAvailable) as e:
    entityActionFailedWarning([Ent.COURSE_NAME, courseAttributes.body['name'], Ent.TEACHER, courseAttributes.body['ownerId']], str(e))

def _doUpdateCourses(entityList):
  croom = buildGAPIObject(API.CLASSROOM)
  courseAttributes = CourseAttributes(croom, True)
  if not courseAttributes.GetAttributes():
    return
  i = 0
  count = len(entityList)
  for course in entityList:
    i += 1
    courseId = addCourseIdScope(course)
    body = courseAttributes.body.copy()
    newOwner = body.get('ownerId')
    modifier = Act.MODIFIER_WITH_COTEACHER_OWNER
    complete = False
    while not complete:
      complete = True
      try:
        if body:
          result = callGAPI(croom.courses(), 'patch',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION,
                                          GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT,
                                          GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            id=courseId, body=body, updateMask=','.join(list(body)), fields='id,name,ownerId,courseState,teacherFolder(id)')
        else:
          result = callGAPI(croom.courses(), 'get',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            id=courseId, fields='id,name,ownerId,courseState,teacherFolder(id)')
        if courseAttributes.body:
          if not newOwner:
            entityActionPerformed([Ent.COURSE_NAME, result['name'], Ent.COURSE, result['id']], i, count)
          else:
            entityModifierNewValueActionPerformed([Ent.COURSE_NAME, result['name'], Ent.COURSE, result['id']],
                                                  modifier, newOwner, i, count)
        if courseAttributes.courseId:
          courseAttributes.CopyFromCourse(result, i, count)
      except (GAPI.notFound, GAPI.permissionDenied,
              GAPI.forbidden, GAPI.badRequest, GAPI.invalidArgument,
              GAPI.internalError, GAPI.serviceNotAvailable) as e:
        entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
      except GAPI.failedPrecondition as e:
        errMsg = str(e)
        if newOwner and '@UserAlreadyOwner Cannot transfer course to the user who is already the owner' in errMsg:
## Handle trying to update current owner to owner, we're done if nothing else was being updated
          body.pop('ownerId')
          modifier = Act.MODIFIER_WITH_CURRENT_OWNER
          complete = False
        elif newOwner and '@IneligibleOwner Only a co-teacher can be invited as owner of the course' in errMsg:
## Add new owner as teacher, then go back and do update
          action = Act.Get()
          Act.Set(Act.ADD)
          try:
            callGAPI(croom.courses().teachers(), 'create',
                     throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR,
                                   GAPI.ALREADY_EXISTS, GAPI.FAILED_PRECONDITION,
                                   GAPI.QUOTA_EXCEEDED, GAPI.SERVICE_NOT_AVAILABLE],
                     retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                     courseId=courseId, body={'userId': newOwner}, fields='')
            modifier = Act.MODIFIER_WITH_NEW_TEACHER_OWNER
            time.sleep(10)
            complete = False
          except (GAPI.notFound, GAPI.backendError, GAPI.forbidden):
            entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, newOwner], getPhraseDNEorSNA(newOwner), i, count)
          except GAPI.alreadyExists:
            entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, newOwner], Msg.DUPLICATE, i, count)
          except GAPI.failedPrecondition:
            entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, newOwner], Msg.NOT_ALLOWED, i, count)
          except (GAPI.quotaExceeded, GAPI.serviceNotAvailable) as ei:
            entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId), Ent.TEACHER, newOwner], str(ei), i, count)
          Act.Set(action)
        else:
          entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)

# gam update courses <CourseEntity> <CourseAttribute>+
#	 [copyfrom <CourseID>
#	    [announcementstates <CourseAnnouncementStateList>]
#		[individualstudentannouncements copy|delete|maptoall]
#	    [materialstates <CourseMaterialStateList>]
#		[individualstudentmaterials copy|delete|maptoall]
#	    [workstates <CourseWorkStateList>]
#		[individualstudentcoursework copy|delete|maptoall]
#		[removeduedate [<Boolean>]]
#		[mapsharemodestudentcopy edit|none|view]
#	    [individualstudentassignments copy|delete|maptoall]
#           [copymaterialsfiles [<Boolean>]]
#	    [copytopics [<Boolean>]]
#	    [markpublishedasdraft [<Boolean>]] [markdraftaspublished [<Boolean>]]
#	    [members none|all|students|teachers]]
#	    [logdrivefileids [<Boolean>]]
def doUpdateCourses():
  _doUpdateCourses(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True))

# gam update course <CourseID> <CourseAttribute>+
#	 [copyfrom <CourseID>
#	    [announcementstates <CourseAnnouncementStateList>]
#		[individualstudentannouncements copy|delete|maptoall]
#	    [materialstates <CourseMaterialStateList>]
#		[individualstudentmaterials copy|delete|maptoall]
#	    [workstates <CourseWorkStateList>]
#		[individualstudentcoursework copy|delete|maptoall]
#		[removeduedate [<Boolean>]]
#		[mapsharemodestudentcopy edit|none|view]
#	    [individualstudentassignments copy|delete|maptoall]
#           [copymaterialsfiles [<Boolean>]]
#	    [copytopics [<Boolean>]]
#	    [markpublishedasdraft [<Boolean>]] [markdraftaspublished [<Boolean>]]
#	    [members none|all|students|teachers]]
def doUpdateCourse():
  _doUpdateCourses(getStringReturnInList(Cmd.OB_COURSE_ID))

def _doDeleteCourses(entityList):
  croom = buildGAPIObject(API.CLASSROOM)
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'archive', 'archived'}:
      body['courseState'] = 'ARCHIVED'
      updateMask = 'courseState'
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  for course in entityList:
    i += 1
    courseId = addCourseIdScope(course)
    try:
      if body:
        callGAPI(croom.courses(), 'patch',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION,
                               GAPI.FORBIDDEN, GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT,
                               GAPI.INTERNAL_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 id=courseId, body=body, updateMask=updateMask, fields='')
      callGAPI(croom.courses(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.FAILED_PRECONDITION, GAPI.INTERNAL_ERROR],
               id=courseId)
      entityActionPerformed([Ent.COURSE, removeCourseIdScope(courseId)], i, count)
    except (GAPI.notFound, GAPI.permissionDenied, GAPI.failedPrecondition,
            GAPI.forbidden, GAPI.badRequest, GAPI.invalidArgument,
            GAPI.internalError, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)

# gam delete courses <CourseEntity> [archive|archived]
def doDeleteCourses():
  _doDeleteCourses(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True))

# gam delete course <CourseID> [archive|archived]
def doDeleteCourse():
  _doDeleteCourses(getStringReturnInList(Cmd.OB_COURSE_ID))

COURSE_FIELDS_CHOICE_MAP = {
  'alternatelink': 'alternateLink',
  'calendarid': 'calendarId',
  'coursegroupemail': 'courseGroupEmail',
  'coursematerialsets': 'courseMaterialSets',
  'coursestate': 'courseState',
  'creationtime': 'creationTime',
  'description': 'description',
  'descriptionheading': 'descriptionHeading',
  'enrollmentcode': 'enrollmentCode',
  'gradebooksettings': 'gradebookSettings',
  'guardiansenabled': 'guardiansEnabled',
  'heading': 'descriptionHeading',
  'id': 'id',
  'name': 'name',
  'owneremail': 'ownerId',
  'ownerid': 'ownerId',
  'ownername': 'ownerId',
  'room': 'room',
  'section': 'section',
  'teacherfolder': 'teacherFolder',
  'teachergroupemail': 'teacherGroupEmail',
  'updatetime': 'updateTime',
  }
COURSE_TIME_OBJECTS = {'creationTime', 'updateTime'}
COURSE_NOLEN_OBJECTS = {'materials'}
COURSE_PROPERTY_PRINT_ORDER = [
  'id',
  'name',
  'Aliases',
  'courseState',
  'descriptionHeading',
  'description',
  'section',
  'room',
  'enrollmentCode',
  'guardiansEnabled',
  'alternateLink',
  'ownerEmail',
  'ownerId',
  'ownerName',
  'creationTime',
  'updateTime',
  'calendarId',
  'courseGroupEmail',
  'teacherGroupEmail',
  'teacherFolder.id',
  'teacherFolder.title',
  'teacherFolder.alternateLink',
  ]

def _initCourseShowProperties(fields=None):
  return {'aliases': False, 'aliasesInColumns': False, 'ownerEmail': False, 'ownerEmailMatchPattern': None,
          'ownerName': False, 'members': 'none', 'countsOnly': False,
          'fields': fields if fields is not None else [], 'skips': []}

def _getCourseShowProperties(myarg, courseShowProperties):
  if myarg in {'alias', 'aliases'}:
    courseShowProperties['aliases'] = True
    courseShowProperties['aliasesInColumns'] = False
  elif myarg == 'aliasesincolumns':
    courseShowProperties['aliases'] = True
    courseShowProperties['aliasesInColumns'] = True
  elif myarg == 'owneremail':
    courseShowProperties['ownerEmail'] = True
  elif myarg == 'owneremailmatchpattern':
    courseShowProperties['ownerEmail'] = True
    courseShowProperties['ownerEmailMatchPattern'] = getREPattern(re.IGNORECASE)
  elif myarg == 'ownername':
    courseShowProperties['ownerName'] = True
  elif myarg == 'show':
    courseShowProperties['members'] = getChoice(COURSE_MEMBER_ARGUMENTS)
  elif myarg == 'countsonly':
    courseShowProperties['countsOnly'] = True
  elif myarg == 'fields':
    for field in _getFieldsList():
      if field in {'alias', 'aliases'}:
        courseShowProperties['aliases'] = True
        courseShowProperties['aliasesInColumns'] = False
      elif field == 'aliasesincolumns':
        courseShowProperties['aliases'] = True
        courseShowProperties['aliasesInColumns'] = True
      elif field == 'owneremail':
        courseShowProperties['ownerEmail'] = True
        courseShowProperties['fields'].append(COURSE_FIELDS_CHOICE_MAP[field])
      elif field == 'ownername':
        courseShowProperties['ownerName'] = True
        courseShowProperties['fields'].append(COURSE_FIELDS_CHOICE_MAP[field])
      elif field == 'teachers':
        if courseShowProperties['members'] == 'none':
          courseShowProperties['members'] = field
        elif courseShowProperties['members'] == 'students':
          courseShowProperties['members'] = 'all'
      elif field == 'students':
        if courseShowProperties['members'] == 'none':
          courseShowProperties['members'] = field
        elif courseShowProperties['members'] == 'teachers':
          courseShowProperties['members'] = 'all'
      elif field in COURSE_FIELDS_CHOICE_MAP:
        courseShowProperties['fields'].append(COURSE_FIELDS_CHOICE_MAP[field])
      else:
        invalidChoiceExit(field, COURSE_FIELDS_CHOICE_MAP, True)
  elif myarg == 'skipfields':
    for field in _getFieldsList():
      if field in {'alias', 'aliases'}:
        courseShowProperties['aliases'] = False
      elif field == 'teachers':
        if courseShowProperties['members'] == 'all':
          courseShowProperties['members'] = 'students'
        elif courseShowProperties['members'] == field:
          courseShowProperties['members'] = 'none'
      elif field == 'students':
        if courseShowProperties['members'] == 'all':
          courseShowProperties['members'] = 'teachers'
        elif courseShowProperties['members'] == field:
          courseShowProperties['members'] = 'none'
      elif field in COURSE_FIELDS_CHOICE_MAP:
        if field != 'id':
          courseShowProperties['skips'].append(COURSE_FIELDS_CHOICE_MAP[field])
      else:
        invalidChoiceExit(field, COURSE_FIELDS_CHOICE_MAP, True)
  else:
    return False
  return True

def _setCourseFields(courseShowProperties, pagesMode, getOwnerId=False):
  if not courseShowProperties['fields']:
    return None
  courseShowProperties['fields'].append('id')
  if courseShowProperties['ownerEmail'] or courseShowProperties['ownerName'] or getOwnerId:
    courseShowProperties['fields'].append('ownerId')
  if not pagesMode:
    return ','.join(set(courseShowProperties['fields']))
  return f'nextPageToken,courses({",".join(set(courseShowProperties["fields"]))})'

def _convertCourseUserIdToEmailName(croom, userId, emails, entityValueList, i, count):
  if userId not in emails:
    try:
      result = callGAPI(croom.userProfiles(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.SERVICE_NOT_AVAILABLE],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        userId=userId, fields='emailAddress,name(fullName)')
    except (GAPI.notFound, GAPI.permissionDenied, GAPI.badRequest, GAPI.forbidden, GAPI.serviceNotAvailable):
      result = {}
    if not result:
      entityDoesNotHaveItemWarning(entityValueList, i, count)
    emails[userId] = (result.get('emailAddress', 'Unknown user'),
                      result.get('name', {}).get('fullName', 'Unknown user'))
  return emails[userId]

def _getCourseOwnerSA(croom, course, useOwnerAccess):
  if not useOwnerAccess:
    return croom
  courseOwnerId = course["ownerId"]
  if courseOwnerId not in GM.Globals[GM.CLASSROOM_OWNER_SA]:
    _, GM.Globals[GM.CLASSROOM_OWNER_SA][courseOwnerId] = buildGAPIServiceObject(API.CLASSROOM, f'uid:{courseOwnerId}')
  return GM.Globals[GM.CLASSROOM_OWNER_SA][courseOwnerId]

def _getCoursesOwnerInfo(croom, courseIds, useOwnerAccess, addCIIdScope=True):
  coursesInfo = {}
  for courseId in courseIds:
    ciCourseId = courseId
    courseId = addCourseIdScope(courseId)
    if addCIIdScope:
      ciCourseId = courseId
    if courseId not in coursesInfo:
      try:
        course = callGAPI(croom.courses(), 'get',
                          throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                        GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                          retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                          id=courseId, fields='id,name,ownerId')
        ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
        if ocroom is not None:
          coursesInfo[ciCourseId] = {'id': course['id'], 'name': course['name'], 'croom': ocroom}
      except GAPI.notFound:
        entityDoesNotExistWarning(Ent.COURSE, courseId)
      except GAPI.serviceNotAvailable as e:
        entityActionFailedWarning([Ent.COURSE, courseId], str(e))
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
  return 0, len(coursesInfo), coursesInfo

def _getCourseAliasesMembers(croom, ocroom, courseId, courseShowProperties, teachersFields, studentsFields, showGettings=False, i=0, count=0):
  aliases = []
  teachers = []
  students = []
  if not showGettings:
    pageMessage = None
  if courseShowProperties.get('aliases'):
    if showGettings:
      printGettingEntityItemForWhom(Ent.ALIAS, formatKeyValueList('', [Ent.Singular(Ent.COURSE), courseId], currentCount(i, count)))
      pageMessage = getPageMessage()
    try:
      aliases = callGAPIpages(croom.courses().aliases(), 'list', 'aliases',
                              pageMessage=pageMessage,
                              throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                                            GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                              courseId=courseId, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
    except (GAPI.notFound, GAPI.serviceNotAvailable, GAPI.notImplemented):
      pass
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  if courseShowProperties['members'] != 'none':
    if courseShowProperties['members'] != 'students':
      if showGettings:
        printGettingEntityItemForWhom(Ent.TEACHER, formatKeyValueList('', [Ent.Singular(Ent.COURSE), courseId], currentCount(i, count)))
        pageMessage = getPageMessage()
      try:
        teachers = callGAPIpages(ocroom.courses().teachers(), 'list', 'teachers',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 courseId=courseId, fields=teachersFields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
      except (GAPI.notFound, GAPI.serviceNotAvailable):
        pass
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
    if courseShowProperties['members'] != 'teachers':
      if showGettings:
        printGettingEntityItemForWhom(Ent.STUDENT, formatKeyValueList('', [Ent.Singular(Ent.COURSE), courseId], currentCount(i, count)))
        pageMessage = getPageMessage()
      try:
        students = callGAPIpages(ocroom.courses().students(), 'list', 'students',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 courseId=courseId, fields=studentsFields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
      except (GAPI.notFound, GAPI.serviceNotAvailable):
        pass
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
  return (aliases, teachers, students)

def _doInfoCourses(courseIdList):
  croom = buildGAPIObject(API.CLASSROOM)
  courseShowProperties = _initCourseShowProperties()
  courseShowProperties['ownerEmail'] = True
  ownerEmails = {}
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if _getCourseShowProperties(myarg, courseShowProperties):
      pass
    elif myarg in OWNER_ACCESS_OPTIONS:
      useOwnerAccess = True
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _setCourseFields(courseShowProperties, False)
  if courseShowProperties['members'] != 'none':
    if courseShowProperties['countsOnly']:
      teachersFields = 'nextPageToken,teachers(profile(id))'
      studentsFields = 'nextPageToken,students(profile(id))'
    else:
      teachersFields = 'nextPageToken,teachers(profile)'
      studentsFields = 'nextPageToken,students(profile)'
  else:
    teachersFields = studentsFields = None
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, useOwnerAccess)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    try:
      course = callGAPI(croom.courses(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        id=courseId, fields=fields)
      if courseShowProperties['ownerEmail'] or courseShowProperties['ownerName']:
        ownerEmail, ownerName = _convertCourseUserIdToEmailName(croom, course['ownerId'], ownerEmails,
                                                                [Ent.COURSE, course['id'], Ent.OWNER_ID, course['ownerId']], i, count)
        if courseShowProperties['ownerEmail']:
          course['ownerEmail'] = ownerEmail
        if courseShowProperties['ownerName']:
          course['ownerName'] = ownerName
      aliases, teachers, students = _getCourseAliasesMembers(croom, courseInfo['croom'], courseId, courseShowProperties, teachersFields, studentsFields)
      if FJQC.formatJSON:
        if courseShowProperties['aliases']:
          course.update({'aliases': list(aliases)})
        if courseShowProperties['members'] != 'none':
          if courseShowProperties['members'] != 'students':
            if not courseShowProperties['countsOnly']:
              course.update({'teachers': list(teachers)})
            else:
              course.update({'teachers': len(teachers)})
          if courseShowProperties['members'] != 'teachers':
            if not courseShowProperties['countsOnly']:
              course.update({'students': list(students)})
            else:
              course.update({'students': len(students)})
        printLine(json.dumps(cleanJSON(course, skipObjects=courseShowProperties['skips'],
                                       timeObjects=COURSE_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
        continue
      printEntity([Ent.COURSE, course['id']], i, count)
      Ind.Increment()
      showJSON(None, course, courseShowProperties['skips'], COURSE_TIME_OBJECTS)
      if courseShowProperties['aliases']:
        printKeyValueList(['Aliases', len(aliases)])
        Ind.Increment()
        for alias in aliases:
          printKeyValueList([removeCourseAliasScope(alias['alias'])])
        Ind.Decrement()
      if courseShowProperties['members'] != 'none':
        printKeyValueList(['Participants', None])
        Ind.Increment()
        if courseShowProperties['members'] != 'students':
          if teachers:
            printKeyValueList(['Teachers', len(teachers)])
            if not courseShowProperties['countsOnly']:
              Ind.Increment()
              for teacher in teachers:
                if 'emailAddress' in teacher['profile']:
                  printKeyValueList([f'{teacher["profile"]["name"]["fullName"]} - {teacher["profile"]["emailAddress"]}'])
                else:
                  printKeyValueList([teacher['profile']['name']['fullName']])
              Ind.Decrement()
        if courseShowProperties['members'] != 'teachers':
          if students:
            printKeyValueList(['Students', len(students)])
            if not courseShowProperties['countsOnly']:
              Ind.Increment()
              for student in students:
                if 'emailAddress' in student['profile']:
                  printKeyValueList([f'{student["profile"]["name"]["fullName"]} - {student["profile"]["emailAddress"]}'])
                else:
                  printKeyValueList([student['profile']['name']['fullName']])
              Ind.Decrement()
          Ind.Decrement()
        Ind.Decrement()
      Ind.Decrement()
    except GAPI.notFound:
      entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], Msg.DOES_NOT_EXIST, i, count)
    except GAPI.serviceNotAvailable as e:
      entityActionFailedWarning([Ent.COURSE, removeCourseIdScope(courseId)], str(e), i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam info courses <CourseEntity> [owneraccess]
#	[owneremail] [ownername] [alias|aliases] [show none|all|students|teachers] [countsonly]
#	[fields <CourseFieldNameList>] [skipfields <CourseFieldNameList>]
#	[formatjson]
def doInfoCourses():
  _doInfoCourses(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True))

# gam info course <CourseID> [owneraccess]
#	[owneremail] [ownername] [alias|aliases] [show none|all|students|teachers] [countsonly]
#	[fields <CourseFieldNameList>] [skipfields <CourseFieldNameList>]
#	[formatjson]
def doInfoCourse():
  _doInfoCourses(getStringReturnInList(Cmd.OB_COURSE_ID))

def _initCourseSelectionParameters():
  return {'courseIds': [], 'teacherId': None, 'studentId': None, 'courseStates': []}

def _getCourseSelectionParameters(myarg, courseSelectionParameters):
  if myarg in {'course', 'courses', 'class', 'classes'}:
    courseSelectionParameters['courseIds'].extend(getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True))
  elif myarg == 'teacher':
    courseSelectionParameters['teacherId'] = getEmailAddress()
  elif myarg == 'student':
    courseSelectionParameters['studentId'] = getEmailAddress()
  elif myarg in {'state', 'states', 'status'}:
    _getCourseStates(Cmd.OB_COURSE_STATE_LIST, courseSelectionParameters['courseStates'])
  else:
    return False
  return True

COURSE_CU_FILTER_FIELDS_MAP = {'creationtime': 'creationTime', 'updatetime': 'updateTime'}
COURSE_CUS_FILTER_FIELDS_MAP = {'creationtime': 'creationTime', 'updatetime': 'updateTime', 'scheduledtime': 'scheduledTime'}
COURSE_U_FILTER_FIELDS_MAP = {'updatetime': 'updateTime'}
COURSE_START_ARGUMENTS = ['start', 'startdate', 'oldestdate']
COURSE_END_ARGUMENTS = ['end', 'enddate']

def _initCourseItemFilter():
  return {'timefilter': None, 'startTime': None, 'endTime': None}

def _getCourseItemFilter(myarg, courseItemFilter, courseFilterFields):
  if myarg == 'timefilter':
    courseItemFilter['timefilter'] = getChoice(courseFilterFields, mapChoice=True)
  elif myarg in COURSE_START_ARGUMENTS:
    courseItemFilter['startTime'], _, _ = getTimeOrDeltaFromNow(True)
  elif myarg in COURSE_END_ARGUMENTS:
    courseItemFilter['endTime'], _, _ = getTimeOrDeltaFromNow(True)
  else:
    return False
  return True

def _setApplyCourseItemFilter(courseItemFilter, fieldsList):
  if courseItemFilter['timefilter'] and (courseItemFilter['startTime'] or courseItemFilter['endTime']):
    if fieldsList:
      fieldsList.append(courseItemFilter['timefilter'])
    return True
  return False

def _courseItemPassesFilter(item, courseItemFilter):
  timeStr = item.get(courseItemFilter['timefilter'])
  if not timeStr:
    return False
  startTime = courseItemFilter['startTime']
  endTime = courseItemFilter['endTime']
  timeValue = arrow.get(timeStr)
  return ((startTime is None) or (timeValue >= startTime)) and ((endTime is None) or (timeValue <= endTime))

def _gettingCoursesQuery(courseSelectionParameters):
  query = ''
  if courseSelectionParameters['teacherId']:
    query += f'{Ent.Singular(Ent.TEACHER)}: {courseSelectionParameters["teacherId"]}, '
  if courseSelectionParameters['studentId']:
    query += f'{Ent.Singular(Ent.STUDENT)}: {courseSelectionParameters["studentId"]}, '
  if courseSelectionParameters['courseStates']:
    query += f'{Ent.Choose(Ent.COURSE_STATE, len(courseSelectionParameters["courseStates"]))}: {",".join(courseSelectionParameters["courseStates"])}, '
  if query:
    query = query[:-2]
  return query

def _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, getOwnerId=False):
  if not courseSelectionParameters['courseIds']:
    fields = _setCourseFields(courseShowProperties, True, getOwnerId)
    printGettingAllAccountEntities(Ent.COURSE, _gettingCoursesQuery(courseSelectionParameters))
    try:
      return callGAPIpages(croom.courses(), 'list', 'courses',
                           pageMessage=getPageMessage(),
                           throwReasons=GAPI.COURSE_ACCESS_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.INVALID, GAPI.SERVICE_NOT_AVAILABLE],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                           teacherId=courseSelectionParameters['teacherId'],
                           studentId=courseSelectionParameters['studentId'],
                           courseStates=courseSelectionParameters['courseStates'],
                           fields=fields, pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
    except (GAPI.invalid, GAPI.notFound):
      if (not courseSelectionParameters['studentId']) and courseSelectionParameters['teacherId']:
        entityUnknownWarning(Ent.TEACHER, courseSelectionParameters['teacherId'])
      elif (not courseSelectionParameters['teacherId']) and courseSelectionParameters['studentId']:
        entityUnknownWarning(Ent.STUDENT, courseSelectionParameters['studentId'])
      elif courseSelectionParameters['studentId'] and courseSelectionParameters['teacherId']:
        entityOrEntityUnknownWarning(Ent.TEACHER, courseSelectionParameters['teacherId'], Ent.STUDENT, courseSelectionParameters['studentId'])
    except (GAPI.insufficientPermissions, GAPI.permissionDenied, GAPI.invalidArgument, GAPI.badRequest, GAPI.serviceNotAvailable) as e:
      entityActionFailedWarning([Ent.COURSE, None], str(e))
    return None
  fields = _setCourseFields(courseShowProperties, False, getOwnerId)
  coursesInfo = []
  for courseId in courseSelectionParameters['courseIds']:
    courseId = addCourseIdScope(courseId)
    try:
      info = callGAPI(croom.courses(), 'get',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      id=courseId, fields=fields)
      coursesInfo.append(info)
    except GAPI.notFound:
      entityDoesNotExistWarning(Ent.COURSE, courseId)
    except GAPI.serviceNotAvailable as e:
      entityActionFailedWarning([Ent.COURSE, courseId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
  return coursesInfo

# gam print courses [todrive <ToDriveAttribute>*] (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[owneremail] [owneremailmatchpattern <REMatchPattern>] [ownername]
#	[alias|aliases|aliasesincolumns [delimiter <Character>]]
#	[show none|all|students|teachers] [countsonly]
#	[fields <CourseFieldNameList>] [skipfields <CourseFieldNameList>]
#	[timefilter creationtime|updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	(addcsvdata <FieldName> <String>)*
#	[showitemcountonly] [formatjson [quotechar <Character>]]
def doPrintCourses():
  def _saveParticipants(course, participants, role, rtitles):
    jcount = len(participants)
    course[role] = jcount
    if courseShowProperties['countsOnly']:
      return
    j = 0
    for member in participants:
      memberTitles = []
      prefix = f'{role}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{j}.'
      profile = member['profile']
      emailAddress = profile.get('emailAddress')
      if emailAddress:
        memberTitle = prefix+'emailAddress'
        course[memberTitle] = emailAddress
        memberTitles.append(memberTitle)
      memberId = profile.get('id')
      if memberId:
        memberTitle = prefix+'id'
        course[memberTitle] = memberId
        memberTitles.append(memberTitle)
      fullName = profile.get('name', {}).get('fullName')
      if fullName:
        memberTitle = prefix+'name.fullName'
        course[memberTitle] = fullName
        memberTitles.append(memberTitle)
      for title in memberTitles:
        if title not in rtitles['set']:
          rtitles['set'].add(title)
          rtitles['list'].append(title)
      j += 1

  croom = buildGAPIObject(API.CLASSROOM)
  csvPF = CSVPrintFile('id')
  FJQC = FormatJSONQuoteChar(csvPF)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseItemFilter = _initCourseItemFilter()
  courseShowProperties = _initCourseShowProperties()
  ownerEmails = {}
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  showItemCountOnly = False
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  addCSVData = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif _getCourseItemFilter(myarg, courseItemFilter, COURSE_CU_FILTER_FIELDS_MAP):
      pass
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif _getCourseShowProperties(myarg, courseShowProperties):
      pass
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    elif myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  applyCourseItemFilter = _setApplyCourseItemFilter(courseItemFilter, None)
  if applyCourseItemFilter:
    if courseShowProperties['fields']:
      courseShowProperties['fields'].append(courseItemFilter['timefilter'])
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if coursesInfo is None:
    if showItemCountOnly:
      writeStdout('0\n')
    return
  if addCSVData:
    csvPF.AddTitles(sorted(addCSVData.keys()))
    if FJQC.formatJSON:
      csvPF.AddJSONTitles(sorted(addCSVData.keys()))
      csvPF.MoveJSONTitlesToEnd(['JSON'])
  if courseShowProperties['aliases']:
    if FJQC.formatJSON:
      csvPF.AddJSONTitles('JSON-aliases')
  if courseShowProperties['members'] != 'none':
    ttitles = {'set': set(), 'list': []}
    stitles = {'set': set(), 'list': []}
    if courseShowProperties['members'] != 'students':
      ttitles['set'].add('teachers')
      ttitles['list'].append('teachers')
      if FJQC.formatJSON:
        csvPF.AddJSONTitles('JSON-teachers')
    if courseShowProperties['members'] != 'teachers':
      stitles['set'].add('students')
      stitles['list'].append('students')
      if FJQC.formatJSON:
        csvPF.AddJSONTitles('JSON-students')
    if courseShowProperties['countsOnly']:
      teachersFields = 'nextPageToken,teachers(profile(id))'
      studentsFields = 'nextPageToken,students(profile(id))'
    else:
      teachersFields = 'nextPageToken,teachers(profile)'
      studentsFields = 'nextPageToken,students(profile)'
  else:
    teachersFields = studentsFields = None
  itemCount = 0
  count = len(coursesInfo)
  i = 0
  for course in coursesInfo:
    i += 1
    if applyCourseItemFilter and not _courseItemPassesFilter(course, courseItemFilter):
      continue
    for field in courseShowProperties['skips']:
      course.pop(field, None)
    courseId = course['id']
    ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
    if not ocroom:
      continue
    if courseShowProperties['ownerEmail'] or courseShowProperties['ownerName']:
      ownerEmail, ownerName = _convertCourseUserIdToEmailName(croom, course['ownerId'], ownerEmails,
                                                              [Ent.COURSE, courseId, Ent.OWNER_ID, course['ownerId']], i, count)
      if courseShowProperties['ownerEmail']:
        course['ownerEmail'] = ownerEmail
        if courseShowProperties['ownerEmailMatchPattern'] and not courseShowProperties['ownerEmailMatchPattern'].match(ownerEmail):
          continue
      if courseShowProperties['ownerName']:
        course['ownerName'] = ownerName
    if showItemCountOnly:
      itemCount += 1
      continue
    aliases, teachers, students = _getCourseAliasesMembers(croom, ocroom, courseId, courseShowProperties, teachersFields, studentsFields, True, i, count)
    if courseShowProperties['aliases']:
      if not courseShowProperties['aliasesInColumns']:
        course['Aliases'] = delimiter.join([removeCourseAliasScope(alias['alias']) for alias in aliases])
      else:
        course['Aliases'] = [removeCourseAliasScope(alias['alias']) for alias in aliases]
    if courseShowProperties['members'] != 'none':
      if courseShowProperties['members'] != 'students':
        _saveParticipants(course, teachers, 'teachers', ttitles)
      if courseShowProperties['members'] != 'teachers':
        _saveParticipants(course, students, 'students', stitles)
    row = flattenJSON(course, timeObjects=COURSE_TIME_OBJECTS, noLenObjects=COURSE_NOLEN_OBJECTS)
    if addCSVData:
      row.update(addCSVData)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      row = {'id': courseId, 'JSON': json.dumps(cleanJSON(course, timeObjects=COURSE_TIME_OBJECTS),
                                                ensure_ascii=False, sort_keys=True)}
      if addCSVData:
        row.update(addCSVData)
      if courseShowProperties['aliases']:
        row['JSON-aliases'] = json.dumps(list(aliases))
      if courseShowProperties['members'] != 'none':
        if courseShowProperties['members'] != 'students':
          if not courseShowProperties['countsOnly']:
            row['JSON-teachers'] = json.dumps(list(teachers))
          else:
            row['JSON-teachers'] = json.dumps(len(teachers))
        if courseShowProperties['members'] != 'teachers':
          if not courseShowProperties['countsOnly']:
            row['JSON-students'] = json.dumps(list(students))
          else:
            row['JSON-students'] = json.dumps(len(students))
      csvPF.WriteRowNoFilter(row)
  if showItemCountOnly:
    writeStdout(f'{itemCount}\n')
    return
  if not FJQC.formatJSON:
    if courseShowProperties['aliases']:
      csvPF.AddTitles('Aliases')
    csvPF.SetSortTitles(COURSE_PROPERTY_PRINT_ORDER)
    if courseShowProperties['aliases'] and courseShowProperties['aliasesInColumns']:
      csvPF.FixCourseAliasesTitles()
    csvPF.SortTitles()
    csvPF.SetSortTitles([])
    if courseShowProperties['members'] != 'none':
      csvPF.RearrangeCourseTitles(ttitles, stitles)
  csvPF.writeCSVfile('Courses')

def _printCourseItemCount(course, results, title, applyCourseItemFilter, courseItemFilter, csvPF):
  if applyCourseItemFilter:
    numItems = 0
    for item in results:
      if _courseItemPassesFilter(item, courseItemFilter):
        numItems += 1
  else:
    numItems = len(results)
  if csvPF:
    csvPF.WriteRowTitles({'courseId': course['id'], 'courseName': course['name'], title: numItems})
  return numItems

COURSE_ANNOUNCEMENTS_FIELDS_CHOICE_MAP = {
  'alternatelink': 'alternateLink',
  'announcementid': 'id',
  'assigneemode': 'assigneeMode',
  'courseid': 'courseId',
  'courseannouncementid': 'id',
  'creationtime': 'creationTime',
  'creator': 'creatorUserId',
  'creatoruserid': 'creatorUserId',
  'id': 'id',
  'individualstudentsoptions': 'individualStudentsOptions',
  'materials': 'materials',
  'scheduledtime': 'scheduledTime',
  'state': 'state',
  'text': 'text',
  'updatetime': 'updateTime',
  }
COURSE_ANNOUNCEMENTS_ORDERBY_CHOICE_MAP = {
  'updatetime': 'updateTime',
  'updatedate': 'updateTime',
  }
COURSE_ANNOUNCEMENTS_TIME_OBJECTS = {'creationTime', 'scheduledTime', 'updateTime'}
COURSE_ANNOUNCEMENTS_SORT_TITLES = ['courseId', 'courseName', 'id', 'text', 'state']
COURSE_ANNOUNCEMENTS_INDEXED_TITLES = ['materials']

# gam print course-announcements [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
#	(announcementids <CourseAnnouncementIDEntity>)|((announcementstates <CourseAnnouncementStateList>)*
#	(orderby <CourseAnnouncementOrderByFieldName> [ascending|descending])*)
#	[showcreatoremails|creatoremail] [fields <CourseAnnouncementFieldNameList>]
#	[timefilter creationtime|updatetime|scheduledtime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
#	[countsonly|(formatjson [quotechar <Character>])]
