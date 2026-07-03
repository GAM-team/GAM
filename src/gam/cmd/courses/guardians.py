"""Guardian invitation and management.

Part of the _courses_tmp sub-package."""

"""GAM Google Classroom course management."""

import re
import json
import sys

from gamlib import gluprop as UProp

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

def studentUnknownWarning(studentId, errMsg, i, count):
  _getMain().setSysExitRC(_getMain().SERVICE_NOT_APPLICABLE_RC)
  _getMain().writeStderr(_getMain().formatKeyValueList(Ind.Spaces(),
                                 [Ent.Singular(Ent.STUDENT), studentId, f'{Msg.SERVICE_NOT_APPLICABLE}: {errMsg}'],
                                 _getMain().currentCountNL(i, count)))

def getGuardianEntity():
  guardians = _getMain().getEntityList(Cmd.OB_GUARDIAN_ENTITY)
  if isinstance(guardians, dict):
    return (guardians, guardians)
  return ([_getMain().normalizeEmailAddressOrUID(guardian) for guardian in guardians], None)

def getGuardianEmails(user, guardianEntity, guardianEntityList):
  studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(user)
  if guardianEntityList:
    guardianEmails = [_getMain().normalizeEmailAddressOrUID(guardian) for guardian in guardianEntityList[user]]
  else:
    guardianEmails = guardianEntity
  return (studentId, guardianEmails, len(guardianEmails))

def getGuardianInvitationEntity():
  invitations = _getMain().getEntityList(Cmd.OB_GUARDIAN_INVITATION_ID_ENTITY)
  if isinstance(invitations, dict):
    return (invitations, invitations)
  return (invitations, None)

def getGuardianInvitationIds(user, invitationEntity, invitationEntityList):
  studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(user)
  if invitationEntityList:
    invitationIds = invitationEntityList[user]
  else:
    invitationIds = invitationEntity
  return (studentId, invitationIds, len(invitationIds))

GUARDIAN_CLASS_UNDEFINED = 0
GUARDIAN_CLASS_ACCEPTED = 1
GUARDIAN_CLASS_INVITATIONS = 2
GUARDIAN_CLASS_ALL = 3

GUARDIAN_CLASS_MAP = {
  'all': GUARDIAN_CLASS_ALL,
  'accepted': GUARDIAN_CLASS_ACCEPTED,
  'invitation': GUARDIAN_CLASS_INVITATIONS,
  'invitations': GUARDIAN_CLASS_INVITATIONS,
  }
GUARDIAN_CLASS_ENTITY = {
  GUARDIAN_CLASS_ALL: Ent.GUARDIAN_AND_INVITATION,
  GUARDIAN_CLASS_ACCEPTED: Ent.GUARDIAN,
  GUARDIAN_CLASS_INVITATIONS: Ent.GUARDIAN_INVITATION,
  }

def _inviteGuardian(croom, studentId, guardianEmail, i=0, count=0, j=0, jcount=0):
  body = {'invitedEmailAddress': guardianEmail}
  try:
    result = _getMain().callGAPI(croom.userProfiles().guardianInvitations(), 'create',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.ALREADY_EXISTS,
                                    GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN,
                                    GAPI.PERMISSION_DENIED, GAPI.RESOURCE_EXHAUSTED, GAPI.SERVICE_NOT_AVAILABLE],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      studentId=studentId, body=body, fields='invitationId')
    _getMain().entityActionPerformed([Ent.STUDENT, studentId, Ent.GUARDIAN, body['invitedEmailAddress'], Ent.GUARDIAN_INVITATION, result['invitationId']], j, jcount)
    return 1
  except GAPI.notFound:
    _getMain().entityUnknownWarning(Ent.STUDENT, studentId, i, count)
    return -1
  except GAPI.alreadyExists:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN, body['invitedEmailAddress']], Msg.DUPLICATE, j, jcount)
    return 0
  except GAPI.resourceExhausted as e:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN, body['invitedEmailAddress']], str(e), j, jcount)
    return -1
  except (GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    studentUnknownWarning(studentId, str(e), i, count)
    return -1

# gam create guardian|guardianinvite|inviteguardian <EmailAddress> <StudentItem>
def doInviteGuardian():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  guardianEmail = _getMain().getEmailAddress()
  studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(_getMain().getString(Cmd.OB_STUDENT_ITEM))
  _getMain().checkForExtraneousArguments()
  _inviteGuardian(croom, studentId, guardianEmail)

# gam <UserTypeEntity> create guardian|guardianinvite|inviteguardian <GuardianEntity>
def inviteGuardians(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  guardianEntity, guardianEntityList = getGuardianEntity()
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    studentId, guardianEmails, jcount = getGuardianEmails(user, guardianEntity, guardianEntityList)
    _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId], jcount, Ent.GUARDIAN_INVITATION, i, count)
    Ind.Increment()
    j = 0
    for guardianEmail in guardianEmails:
      j += 1
      if _inviteGuardian(croom, studentId, guardianEmail, i, count, j, jcount) < 0:
        break
    Ind.Decrement()

def _cancelGuardianInvitation(croom, studentId, invitationId, i=0, count=0, j=0, jcount=0):
  try:
    result = _getMain().callGAPI(croom.userProfiles().guardianInvitations(), 'patch',
                      throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION,
                                    GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN,
                                    GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      studentId=studentId, invitationId=invitationId, updateMask='state', body={'state': 'COMPLETE'}, fields='invitedEmailAddress')
    _getMain().entityActionPerformed([Ent.STUDENT, studentId, Ent.GUARDIAN_INVITATION, result['invitedEmailAddress']], j, jcount)
    return 1
  except GAPI.notFound:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN_INVITATION, invitationId], Msg.NOT_FOUND, j, jcount)
    return 0
  except GAPI.failedPrecondition:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN_INVITATION, invitationId], Msg.GUARDIAN_INVITATION_STATUS_NOT_PENDING, j, jcount)
    return 1
  except (GAPI.invalidArgument, GAPI.badRequest, GAPI.serviceNotAvailable) as e:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN_INVITATION, invitationId], str(e), j, jcount)
    return -1
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
#    studentUnknownWarning(studentId, str(e), i, count)
    return -1

# gam cancel guardianinvitation|guardianinvitations <GuardianInvitationID> <StudentItem>
def doCancelGuardianInvitation():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  invitationId = _getMain().getString(Cmd.OB_GUARDIAN_INVITATION_ID)
  studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(_getMain().getString(Cmd.OB_STUDENT_ITEM))
  _getMain().checkForExtraneousArguments()
  _cancelGuardianInvitation(croom, studentId, invitationId)

# gam <UserTypeEntity> cancel guardianinvitation|guardianinvitations <GuardianInvitationIDEntity>
def cancelGuardianInvitations(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  invitationEntity, invitationEntityList = getGuardianInvitationEntity()
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    studentId, invitationIds, jcount = getGuardianInvitationIds(user, invitationEntity, invitationEntityList)
    _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId], jcount, Ent.GUARDIAN_INVITATION, i, count)
    Ind.Increment()
    j = 0
    for invitationId in invitationIds:
      j += 1
      if _cancelGuardianInvitation(croom, studentId, invitationId, i, count, j, jcount) == -1:
        break
    Ind.Decrement()

def _deleteGuardian(croom, studentId, guardianId, guardianEmail, i, count, j, jcount):
  try:
    _getMain().callGAPI(croom.userProfiles().guardians(), 'delete',
             throwReasons=[GAPI.NOT_FOUND, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
             retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
             studentId=studentId, guardianId=guardianId)
    _getMain().entityActionPerformed([Ent.STUDENT, studentId, Ent.GUARDIAN, guardianEmail], j, jcount)
    return 1
  except GAPI.notFound:
    if guardianId == guardianEmail:
      _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN, guardianEmail], Msg.NOT_FOUND, j, jcount)
    return 0
  except GAPI.serviceNotAvailable as e:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, Ent.GUARDIAN, guardianEmail], str(e), j, jcount)
    return -1
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
#    studentUnknownWarning(studentId, str(e), i, count)
    return -1

def _doDeleteGuardian(croom, studentId, guardianId, guardianClass, i=0, count=0, j=0, jcount=0):
  guardianIdIsEmail = guardianId.find('@') != -1
  guardianFound = False
  try:
    if guardianClass != GUARDIAN_CLASS_ACCEPTED:
      Act.Set(Act.CANCEL)
      if guardianIdIsEmail:
        invitations = _getMain().callGAPIpages(croom.userProfiles().guardianInvitations(), 'list', 'guardianInvitations',
                                    throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    studentId=studentId, invitedEmailAddress=guardianId, states=['PENDING'],
                                    fields='nextPageToken,guardianInvitations(studentId,invitationId)')
        for invitation in invitations:
          result = _cancelGuardianInvitation(croom, invitation['studentId'], invitation['invitationId'], i, count, j, jcount)
          if result < 0:
            return result
          if result > 0:
            guardianFound = True
      else:
        result = _cancelGuardianInvitation(croom, studentId, guardianId, i, count, j, jcount)
        if result != 0:
          return result
    if guardianClass != GUARDIAN_CLASS_INVITATIONS:
      Act.Set(Act.DELETE)
      if guardianIdIsEmail:
        guardians = _getMain().callGAPIpages(croom.userProfiles().guardians(), 'list', 'guardians',
                                  throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                                GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  studentId=studentId, invitedEmailAddress=guardianId,
                                  fields='nextPageToken,guardians(studentId,guardianId)')
        for guardian in guardians:
          result = _deleteGuardian(croom, guardian['studentId'], guardian['guardianId'], guardianId, i, count, j, jcount)
          if result < 0:
            return result
          if result > 0:
            guardianFound = True
      else:
        result = _deleteGuardian(croom, studentId, guardianId, guardianId, i, count, j, jcount)
        if result != 0:
          return result
  except GAPI.notFound:
    _getMain().entityUnknownWarning(Ent.STUDENT, studentId, i, count)
    return -1
  except (GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied) as e:
    studentUnknownWarning(studentId, str(e), i, count)
    return -1
  except GAPI.serviceNotAvailable as e:
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, GUARDIAN_CLASS_ENTITY[guardianClass], guardianId], str(e))
    return -1
  if not guardianFound:
    Act.Set(Act.DELETE)
    _getMain().entityActionFailedWarning([Ent.STUDENT, studentId, GUARDIAN_CLASS_ENTITY[guardianClass], guardianId], Msg.NOT_FOUND)
    return 0
  return 1

# gam delete guardian|guardians <GuardianItem> <StudentItem> [accepted|invitations|all]
def doDeleteGuardian():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  guardianId = _getMain().normalizeStudentGuardianEmailAddressOrUID(_getMain().getString(Cmd.OB_GUARDIAN_ITEM))
  studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(_getMain().getString(Cmd.OB_STUDENT_ITEM), allowDash=True)
  guardianClass = _getMain().getChoice(GUARDIAN_CLASS_MAP, mapChoice=True, defaultChoice=GUARDIAN_CLASS_ALL)
  _getMain().checkForExtraneousArguments()
  _doDeleteGuardian(croom, studentId, guardianId, guardianClass)

# gam <UserTypeEntity> delete guardian|guardians <GuardianEntity> [accepted|invitations|all]
def deleteGuardians(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  guardianEntity, guardianEntityList = getGuardianEntity()
  guardianClass = _getMain().getChoice(GUARDIAN_CLASS_MAP, mapChoice=True, defaultChoice=GUARDIAN_CLASS_ALL)
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    studentId, guardianEmails, jcount = getGuardianEmails(user, guardianEntity, guardianEntityList)
    _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId], jcount, GUARDIAN_CLASS_ENTITY[guardianClass], i, count)
    Ind.Increment()
    j = 0
    for guardianEmail in guardianEmails:
      j += 1
      if _doDeleteGuardian(croom, studentId, guardianEmail, guardianClass, i, count, j, jcount) < 0:
        break
    Ind.Decrement()

# gam <UserTypeEntity> clear guardian|guardians [accepted|invitations|all]
def clearGuardians(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  guardianClass = _getMain().getChoice(GUARDIAN_CLASS_MAP, mapChoice=True, defaultChoice=GUARDIAN_CLASS_ALL)
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(user)
    try:
      if guardianClass != GUARDIAN_CLASS_ACCEPTED:
        invitations = _getMain().callGAPIpages(croom.userProfiles().guardianInvitations(), 'list', 'guardianInvitations',
                                    throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    studentId=studentId, states=['PENDING'], fields='nextPageToken,guardianInvitations(invitationId)')
        Act.Set(Act.CANCEL)
        jcount = len(invitations)
        _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId], jcount, Ent.GUARDIAN_INVITATION, i, count)
        Ind.Increment()
        j = 0
        for invitation in invitations:
          j += 1
          _cancelGuardianInvitation(croom, studentId, invitation['invitationId'], i, count, j, jcount)
        Ind.Decrement()
      if guardianClass != GUARDIAN_CLASS_INVITATIONS:
        guardians = _getMain().callGAPIpages(croom.userProfiles().guardians(), 'list', 'guardians',
                                  throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                  studentId=studentId, fields='nextPageToken,guardians(guardianId,invitedEmailAddress)')
        Act.Set(Act.DELETE)
        jcount = len(guardians)
        _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId], jcount, Ent.GUARDIAN, i, count)
        Ind.Increment()
        j = 0
        for guardian in guardians:
          j += 1
          _deleteGuardian(croom, studentId, guardian['guardianId'], guardian['invitedEmailAddress'], i, count, j, jcount)
        Ind.Decrement()
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.STUDENT, studentId, i, count)
    except GAPI.serviceNotAvailable as e:
      _getMain().entityActionFailedWarning([Ent.STUDENT, studentId], str(e))
    except (GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied) as e:
      studentUnknownWarning(studentId, str(e), i, count)

# gam <UserTypeEntity> sync guardian|guardians <GuardianEntity>
def syncGuardians(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  guardianEntity, guardianEntityList = getGuardianEntity()
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    Act.Set(Act.SYNC)
    studentId, guardianEmails, jcount = getGuardianEmails(user, guardianEntity, guardianEntityList)
    _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId], jcount, Ent.GUARDIAN, i, count)
    try:
      invitations = _getMain().callGAPIpages(croom.userProfiles().guardianInvitations(), 'list', 'guardianInvitations',
                                  throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                                GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  studentId=studentId, states=['PENDING'], fields='nextPageToken,guardianInvitations(invitationId,invitedEmailAddress)')
      guardians = _getMain().callGAPIpages(croom.userProfiles().guardians(), 'list', 'guardians',
                                throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                              GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                studentId=studentId, fields='nextPageToken,guardians(guardianId,invitedEmailAddress)')
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.STUDENT, studentId, i, count)
      continue
    except GAPI.serviceNotAvailable as e:
      _getMain().entityActionFailedWarning([Ent.STUDENT, studentId], str(e), i, count)
    except (GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied) as e:
      studentUnknownWarning(studentId, str(e), i, count)
      continue
    Ind.Increment()
    Act.Set(Act.CANCEL)
    jcount = len(invitations)
    j = 0
    for invitation in invitations:
      j += 1
      if invitation['invitedEmailAddress'] not in guardianEmails:
        _cancelGuardianInvitation(croom, studentId, invitation['invitationId'], i, count, j, jcount)
    Act.Set(Act.DELETE)
    jcount = len(guardians)
    j = 0
    for guardian in guardians:
      j += 1
      if guardian['invitedEmailAddress'] not in guardianEmails:
        _deleteGuardian(croom, studentId, guardian['guardianId'], guardian['invitedEmailAddress'], i, count, j, jcount)
    Act.Set(Act.CREATE)
    for guardianEmail in guardianEmails:
      for guardian in guardians:
        if guardianEmail == guardian['invitedEmailAddress']:
          break
      else:
        for invitation in invitations:
          if guardianEmail == invitation['invitedEmailAddress']:
            break
        else:
          _inviteGuardian(croom, studentId, guardianEmail, i, count)
    Ind.Decrement()

def _getCourseName(croom, courseNames, courseId):
  courseName = courseNames.get(courseId)
  if courseName is None:
    try:
      courseName = _getMain().callGAPI(croom.courses(), 'get',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            id=courseId, fields='name')['name']
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.serviceNotAvailable):
      pass
    if courseName is None:
      courseName = courseId
    courseNames[courseId] = courseName
  return courseName

def _getClassroomEmail(croom, classroomEmails, userId, user):
  if user.find('@') != -1:
    return user
  userEmail = classroomEmails.get(userId)
  if userEmail is None:
    try:
      userEmail = _getMain().callGAPI(croom.userProfiles(), 'get',
                           throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST, GAPI.FORBIDDEN,
                                         GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                           userId=userId, fields='emailAddress').get('emailAddress')
    except (GAPI.notFound, GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.serviceNotAvailable):
      pass
    if userEmail is None:
      userEmail = userId
    classroomEmails[userId] = userEmail
  return userEmail

GUARDIAN_TIME_OBJECTS = {'creationTime'}
GUARDIAN_STATES = ['complete', 'pending']

def _printShowGuardians(entityList=None):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  if entityList is None:
    studentIds = ['-']
    allStudents = True
  else:
    studentIds = entityList
    allStudents = False
  showStudentEmails = False
  classroomEmails = {}
  invitedEmailAddress = None
  states = []
  guardianClass = GUARDIAN_CLASS_ACCEPTED
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'invitedguardian':
      invitedEmailAddress = _getMain().getEmailAddress()
    elif myarg in {'invitation', 'invitations'}:
      guardianClass = GUARDIAN_CLASS_INVITATIONS
      if not states:
        states = [state.upper() for state in GUARDIAN_STATES]
    elif myarg == 'accepted':
      guardianClass = GUARDIAN_CLASS_ACCEPTED
    elif myarg == 'all':
      guardianClass = GUARDIAN_CLASS_ALL
      if not states:
        states.append('PENDING')
    elif myarg in {'state', 'states', 'status'}:
      statesList = _getMain().getString(Cmd.OB_GUARDIAN_STATE_LIST).lower().split(',')
      states = []
      for state in statesList:
        if state in GUARDIAN_STATES:
          states.append(state.upper())
        else:
          _getMain().invalidChoiceExit(state, GUARDIAN_STATES, True)
    elif myarg == 'showstudentemails':
      showStudentEmails = True
    elif entityList is None and myarg == 'student':
      studentIds = [_getMain().getString(Cmd.OB_STUDENT_ITEM)]
      allStudents = studentIds[0] == '-'
    elif FJQC.GetFormatJSONQuoteChar(myarg, False, True):
      pass
    elif entityList is None:
      Cmd.Backup()
      _, studentIds = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
      allStudents = False
    else:
      _getMain().unknownArgumentExit()
  if csvPF:
    if not FJQC.formatJSON:
      sortTitles = ['studentEmail', 'studentId', 'invitedEmailAddress']
      if guardianClass != GUARDIAN_CLASS_ACCEPTED:
        sortTitles.extend(['invitationId', 'creationTime', 'state'])
      if guardianClass != GUARDIAN_CLASS_INVITATIONS:
        sortTitles.append('guardianId')
      csvPF.SetTitles(sortTitles)
      csvPF.SetSortAllTitles()
    else:
      csvPF.SetJSONTitles(['studentEmail', 'studentId', 'JSON'])
  i, count, studentIds = _getMain().getEntityArgument(studentIds)
  for studentId in studentIds:
    i += 1
    if not allStudents:
      studentId = _getMain().normalizeStudentGuardianEmailAddressOrUID(studentId)
      if showStudentEmails:
        studentId = _getClassroomEmail(croom, classroomEmails, studentId, studentId)
    try:
      if guardianClass != GUARDIAN_CLASS_ACCEPTED:
        if csvPF:
          if states:
            qualifier = f' ({",".join(states)})'
          else:
            qualifier = ''
          if not allStudents:
            _getMain().printGettingAllEntityItemsForWhom(Ent.GUARDIAN_INVITATION, studentId, i, count, qualifier=qualifier)
          else:
            _getMain().printGettingAllEntityItemsForWhom(Ent.GUARDIAN_INVITATION, 'All students', qualifier=qualifier)
          pageMessage = _getMain().getPageMessageForWhom()
        else:
          pageMessage = None
        invitations = _getMain().callGAPIpages(croom.userProfiles().guardianInvitations(), 'list', 'guardianInvitations',
                                    pageMessage=pageMessage,
                                    throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    studentId=studentId, invitedEmailAddress=invitedEmailAddress, states=states)
        if not csvPF:
          if not FJQC.formatJSON:
            jcount = len(invitations)
            _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId if not allStudents else 'All'], jcount, Ent.GUARDIAN_INVITATION, i, count)
            Ind.Increment()
            j = 0
            for invitation in invitations:
              j += 1
              _getMain().printKeyValueListWithCount(['invitedEmailAddress', invitation['invitedEmailAddress']], j, jcount)
              Ind.Increment()
              if showStudentEmails:
                invitation['studentEmail'] = _getClassroomEmail(croom, classroomEmails, invitation['studentId'], studentId)
              _getMain().showJSON(None, invitation, ['invitedEmailAddress'], GUARDIAN_TIME_OBJECTS)
              Ind.Decrement()
            Ind.Decrement()
          else:
            _getMain().printLine(json.dumps(_getMain().cleanJSON(invitations, timeObjects=GUARDIAN_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
        elif invitations:
          if not FJQC.formatJSON:
            for invitation in invitations:
              if showStudentEmails:
                invitation['studentEmail'] = _getClassroomEmail(croom, classroomEmails, invitation['studentId'], studentId)
              else:
                invitation['studentEmail'] = studentId
              csvPF.WriteRowTitles(_getMain().flattenJSON(invitation, timeObjects=GUARDIAN_TIME_OBJECTS))
          else:
            csvPF.WriteRow({'studentId': studentId, 'studentEmail': _getClassroomEmail(croom, classroomEmails, studentId, studentId),
                            'JSON': json.dumps(_getMain().cleanJSON(invitations, timeObjects=GUARDIAN_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
        elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
          csvPF.WriteRowNoFilter({'studentEmail': studentId})
      if guardianClass != GUARDIAN_CLASS_INVITATIONS:
        if csvPF:
          if not allStudents:
            _getMain().printGettingAllEntityItemsForWhom(Ent.GUARDIAN, studentId, i, count)
          else:
            _getMain().printGettingAllEntityItemsForWhom(Ent.GUARDIAN, 'All students')
          pageMessage = _getMain().getPageMessageForWhom()
        else:
          pageMessage = None
        guardians = _getMain().callGAPIpages(croom.userProfiles().guardians(), 'list', 'guardians',
                                  pageMessage=pageMessage,
                                  throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                                GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                  retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                  studentId=studentId, invitedEmailAddress=invitedEmailAddress)
        if not csvPF:
          if not FJQC.formatJSON:
            jcount = len(guardians)
            _getMain().entityPerformActionNumItems([Ent.STUDENT, studentId if not allStudents else 'All'], jcount, Ent.GUARDIAN, i, count)
            Ind.Increment()
            j = 0
            for guardian in guardians:
              j += 1
              _getMain().printKeyValueListWithCount(['invitedEmailAddress', guardian['invitedEmailAddress']], j, jcount)
              Ind.Increment()
              if showStudentEmails:
                guardian['studentEmail'] = _getClassroomEmail(croom, classroomEmails, guardian['studentId'], studentId)
              _getMain().showJSON(None, guardian, ['invitedEmailAddress'])
              Ind.Decrement()
            Ind.Decrement()
          else:
            _getMain().printLine(json.dumps(_getMain().cleanJSON(guardians), ensure_ascii=False, sort_keys=True))
        elif guardians:
          if not FJQC.formatJSON:
            for guardian in guardians:
              if showStudentEmails:
                guardian['studentEmail'] = _getClassroomEmail(croom, classroomEmails, guardian['studentId'], studentId)
              else:
                guardian['studentEmail'] = studentId
              csvPF.WriteRowTitles(_getMain().flattenJSON(guardian))
          else:
            csvPF.WriteRowNoFilter({'studentId': studentId, 'studentEmail': _getClassroomEmail(croom, classroomEmails, studentId, studentId),
                                    'JSON': json.dumps(_getMain().cleanJSON(guardians), ensure_ascii=False, sort_keys=True)})
        elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
          csvPF.WriteRowNoFilter({'studentEmail': studentId})
    except GAPI.notFound:
      _getMain().entityUnknownWarning(Ent.STUDENT, studentId, i, count)
    except (GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied) as e:
      studentUnknownWarning(studentId, str(e), i, count)
    except GAPI.serviceNotAvailable as e:
      _getMain().entityActionFailedWarning([Ent.STUDENT, studentId], str(e), i, count)
  if csvPF:
    csvPF.writeCSVfile('Guardians')

# gam show guardian|guardians [accepted|invitations|all] [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
#	[student <StudentItem>] [<UserTypeEntity>]
#	[showstudentemails] [formatjson]
# gam print guardian|guardians [todrive <ToDriveAttribute>*] [accepted|invitations|all] [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
#	[student <StudentItem>] [<UserTypeEntity>]
#	[showstudentemails] [formatjson [quotechar <Character>]]
def doPrintShowGuardians():
  _printShowGuardians()

# gam <UserTypeEntity> show guardian|guardians [accepted|invitations|all] [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
#	[showstudentemails] [formatjson]
# gam <UserTypeEntity> print guardian|guardians [todrive <ToDriveAttribute>*] [accepted|invitations|all] [states <GuardianInvitationStateList>] [invitedguardian <EmailAddress>]
#	[showstudentemails] [formatjson [quotechar <Character>]]
def printShowGuardians(users):
  _printShowGuardians(users)

CLASSROOM_ROLE_ALL = 'ALL'
CLASSROOM_ROLE_OWNER = 'OWNER'
CLASSROOM_ROLE_STUDENT = 'STUDENT'
CLASSROOM_ROLE_TEACHER = 'TEACHER'

def _getClassroomInvitations(croom, userId, courseId, role, i, count, j=0, jcount=0):
  try:
    invitations = _getMain().callGAPIpages(croom.invitations(), 'list', 'invitations',
                                throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.BAD_REQUEST,
                                              GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED, GAPI.SERVICE_NOT_AVAILABLE],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                userId=userId, courseId=courseId)
  except GAPI.notFound:
    if userId is not None:
      _getMain().entityUnknownWarning(Ent.USER, userId, i, count)
      return (-1, None)
    _getMain().entityUnknownWarning(Ent.COURSE, courseId, j, jcount)
    return (0, [])
  except (GAPI.invalidArgument, GAPI.badRequest, GAPI.forbidden, GAPI.permissionDenied, GAPI.serviceNotAvailable) as e:
    if userId is not None:
      _getMain().entityActionFailedWarning([Ent.USER, userId], str(e), i, count)
      return (-1, None)
    _getMain().entityActionFailedWarning([Ent.COURSE, courseId], str(e), j, jcount)
    return (0, [])
  if role == CLASSROOM_ROLE_ALL:
    return (1, invitations)
  return (1, [invitation for invitation in invitations if invitation['role'] == role])

def _getClassroomInvitationIds(croom, userId, courseIds, role, i, count):
  invitationIds = []
  if courseIds is not None:
    jcount = len(courseIds)
    j = 0
    for courseId in courseIds:
      j += 1
      courseId = _getMain().addCourseIdScope(courseId)
      status, invitations = _getClassroomInvitations(croom, userId, courseId, role, i, count, j, jcount)
      if status < 0:
        return (status, None)
      if status > 0:
        invitationIds.extend([invitation['id'] for invitation in invitations])
  else:
    status, invitations = _getClassroomInvitations(croom, userId, None, role, i, count)
    if status < 0:
      return (status, None)
    if status > 0:
      invitationIds.extend([invitation['id'] for invitation in invitations])
  return (1, invitationIds)

CLASSROOM_CREATE_ROLE_MAP = {
  'owner': CLASSROOM_ROLE_OWNER,
  'student': CLASSROOM_ROLE_STUDENT,
  'teacher': CLASSROOM_ROLE_TEACHER,
  }

CLASSROOM_ROLE_MAP = {
  'all': CLASSROOM_ROLE_ALL,
  'owner': CLASSROOM_ROLE_OWNER,
  'student': CLASSROOM_ROLE_STUDENT,
  'teacher': CLASSROOM_ROLE_TEACHER,
  }

CLASSROOM_ROLE_ENTITY_MAP = {
  CLASSROOM_ROLE_ALL: Ent.CLASSROOM_INVITATION,
  CLASSROOM_ROLE_OWNER: Ent.CLASSROOM_INVITATION_OWNER,
  CLASSROOM_ROLE_STUDENT: Ent.CLASSROOM_INVITATION_STUDENT,
  CLASSROOM_ROLE_TEACHER: Ent.CLASSROOM_INVITATION_TEACHER,
  }

# gam <UserTypeEntity> create classroominvitation courses <CourseEntity> [role owner|student|teacher]
#	[asadmin] [csv|csvformat] [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]
def createClassroomInvitations(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  classroomEmails = {}
  courseIds = None
  role = CLASSROOM_ROLE_STUDENT
  useOwnerAccess = True
  csvPF = None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'course', 'courses', 'class', 'classes'}:
      courseIds = _getMain().getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True)
    elif myarg == 'role':
      role = _getMain().getChoice(CLASSROOM_CREATE_ROLE_MAP, mapChoice=True)
    elif myarg in {'csv',  'csvformat'}:
      csvPF = _getMain().CSVPrintFile()
      FJQC.SetCsvPF(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in _getMain().ADMIN_ACCESS_OPTIONS:
      useOwnerAccess = False
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if courseIds is None:
    _getMain().missingArgumentExit('courses <CourseEntity>')
  if csvPF:
    if FJQC.formatJSON:
      csvPF.SetJSONTitles(['userEmail', 'JSON'])
    else:
      csvPF.SetTitles(['userEmail', 'courseId', 'courseName', 'id', 'role'])
      csvPF.SetSortAllTitles()
  courseIdsLists = courseIds if isinstance(courseIds, dict) else None
  if courseIdsLists is None:
    j, jcount, coursesInfo =  _getCoursesOwnerInfo(croom, courseIds, useOwnerAccess)
  entityType = CLASSROOM_ROLE_ENTITY_MAP[role]
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    userId = _getMain().normalizeEmailAddressOrUID(user)
    userEmail = _getClassroomEmail(croom, classroomEmails, userId, userId)
    if courseIdsLists:
      j, jcount, coursesInfo = _getCoursesOwnerInfo(croom, courseIdsLists[user], useOwnerAccess)
    if csvPF or not FJQC.formatJSON:
      _getMain().entityPerformActionNumItems([Ent.USER, userId], jcount, entityType, i, count)
    if jcount == 0:
      continue
    for courseId, courseInfo in coursesInfo.items():
      j += 1
      courseNameId = f'{courseInfo["name"]} ({courseId})'
      try:
        invitation = _getMain().callGAPI(courseInfo['croom'].invitations(), 'create',
                              throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.ALREADY_EXISTS, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              body={'userId': userId, 'courseId': courseId, 'role': role})
        invitation['courseName'] = courseInfo['name']
        invitation['userEmail'] = userEmail
        if not csvPF:
          if not FJQC.formatJSON:
            Ind.Increment()
            _getMain().entityActionPerformed([Ent.USER, userEmail, Ent.COURSE, courseNameId, entityType, invitation['id']], j, jcount)
            Ind.Decrement()
          else:
            _getMain().printLine(json.dumps(_getMain().cleanJSON(invitation), ensure_ascii=False, sort_keys=True))
        else:
          if not FJQC.formatJSON:
            csvPF.WriteRow(invitation)
          else:
            csvPF.WriteRowNoFilter({'userEmail': userEmail,
                                    'JSON': json.dumps(_getMain().cleanJSON(invitation), ensure_ascii=False, sort_keys=True)})
      except GAPI.permissionDenied as e:
        _getMain().entityActionFailedWarning([Ent.USER, userId, Ent.COURSE, courseNameId, entityType, None], str(e), j, jcount)
        break
      except GAPI.notFound:
        _getMain().entityUnknownWarning(Ent.COURSE, courseNameId, j, jcount)
      except (GAPI.failedPrecondition, GAPI.alreadyExists, GAPI.forbidden) as e:
        _getMain().entityActionFailedWarning([Ent.USER, userId, Ent.COURSE, courseNameId, entityType, None], str(e), j, jcount)
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('ClassroomInvitations')

def acceptDeleteClassroomInvitations(users, function):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  if function == 'delete':
    ucroom = croom
  courseIds = invitationIds = None
  role = CLASSROOM_ROLE_ALL
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'id', 'ids'}:
      invitationIds = _getMain().getEntityList(Cmd.OB_CLASSROOM_INVITATION_ID_ENTITY)
      courseIds = None
    elif myarg in {'course', 'courses', 'class', 'classes'}:
      courseIds = _getMain().getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True)
      invitationIds = None
    elif myarg == 'role':
      role = _getMain().getChoice(CLASSROOM_ROLE_MAP, mapChoice=True)
    else:
      _getMain().unknownArgumentExit()
  courseIdsLists = courseIds if isinstance(courseIds, dict) else None
  invitationIdsLists = invitationIds if isinstance(invitationIds, dict) else None
  entityType = CLASSROOM_ROLE_ENTITY_MAP[role]
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    if function == 'delete':
      userId = _getMain().normalizeEmailAddressOrUID(user)
    else:
      userId, ucroom = _getMain().buildGAPIServiceObject(API.CLASSROOM, user, i, count)
      if not ucroom:
        continue
    if invitationIdsLists:
      userInvitationIds = invitationIdsLists[user]
    elif invitationIds is not None:
      userInvitationIds = invitationIds
    else:
      if courseIdsLists:
        courseIds = courseIdsLists[user]
      status, userInvitationIds = _getClassroomInvitationIds(croom, userId, courseIds, role, i, count)
      if status < 0:
        continue
    jcount = len(userInvitationIds)
    _getMain().entityPerformActionNumItems([Ent.USER, userId], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for invitationId in userInvitationIds:
      j += 1
      try:
        _getMain().callGAPI(ucroom.invitations(), function,
                 throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                 id=invitationId)
        _getMain().entityActionPerformed([Ent.USER, userId, entityType, invitationId], j, jcount)
      except (GAPI.notFound, GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedWarning([Ent.USER, userId, entityType, invitationId], str(e), j, jcount)
    Ind.Decrement()

# gam <UserTypeEntity> accept classroominvitation (ids <ClassroomInvitationIDEntity>)|([courses <CourseEntity>] [role all|owner|student|teacher])
def acceptClassroomInvitations(users):
  acceptDeleteClassroomInvitations(users, 'accept')

# gam <UserTypeEntity> delete classroominvitation (ids <ClassroomInvitationIDEntity>)|([courses <CourseEntity>] [role all|owner|student|teacher])
def deleteClassroomInvitations(users):
  acceptDeleteClassroomInvitations(users, 'delete')

# gam <UserTypeEntity> show classroominvitations [role all|owner|student|teacher]
#	[formatjson]
# gam <UserTypeEntity> print classroominvitations [todrive <ToDriveAttribute>*] [role all|owner|student|teacher]
#	[formatjson [quotechar <Character>]]
def printShowClassroomInvitations(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  classroomEmails = {}
  courseNames = {}
  role = CLASSROOM_ROLE_ALL
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'role':
      role = _getMain().getChoice(CLASSROOM_ROLE_MAP, mapChoice=True)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, False)
  if csvPF:
    if FJQC.formatJSON:
      csvPF.SetJSONTitles(['userEmail', 'JSON'])
    else:
      csvPF.SetTitles(['userId', 'userEmail', 'courseId', 'courseName', 'id', 'role'])
      csvPF.SetSortAllTitles()
  entityType = CLASSROOM_ROLE_ENTITY_MAP[role]
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    userId = _getMain().normalizeEmailAddressOrUID(user)
    userEmail = _getClassroomEmail(croom, classroomEmails, userId, userId)
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(entityType, userId, i, count)
    status, invitations = _getClassroomInvitations(croom, userId, None, role, i, count)
    if status > 0:
      if not csvPF:
        if not FJQC.formatJSON:
          jcount = len(invitations)
          _getMain().entityPerformActionNumItems([Ent.USER, userId], jcount, entityType, i, count)
          Ind.Increment()
          j = 0
          for invitation in invitations:
            j += 1
            courseId = invitation['courseId']
            courseName = _getCourseName(croom, courseNames, courseId)
            _getMain().printKeyValueListWithCount([Ent.Singular(Ent.COURSE), f'{courseName} ({courseId})'], j, jcount)
            Ind.Increment()
            _getMain().printKeyValueList(['id', invitation['id']])
            _getMain().printKeyValueList(['role', invitation['role']])
            _getMain().printKeyValueList(['userid', invitation['userId']])
            _getMain().printKeyValueList(['userEmail', userEmail])
            Ind.Decrement()
          Ind.Decrement()
        else:
          _getMain().printLine(json.dumps(_getMain().cleanJSON(invitations), ensure_ascii=False, sort_keys=True))
      elif invitations:
        if not FJQC.formatJSON:
          for invitation in invitations:
            invitation['courseName'] = _getCourseName(croom, courseNames, invitation['courseId'])
            invitation['userEmail'] = userEmail
            csvPF.WriteRow(invitation)
        else:
          csvPF.WriteRowNoFilter({'userEmail': userEmail,
                                  'JSON': json.dumps(_getMain().cleanJSON(invitations), ensure_ascii=False, sort_keys=True)})
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'userId' if not FJQC.formatJSON else 'userEmail':  userEmail})
  if csvPF:
    csvPF.writeCSVfile('ClassroomInvitations')

# gam delete classroominvitation courses <CourseEntity> (ids <ClassroomInvitationIDEntity>)|(role all|owner|student|teacher)
def doDeleteClassroomInvitations():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  courseIdList = invitationIds = None
  role = CLASSROOM_ROLE_ALL
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg in {'course', 'courses', 'class', 'classes'}:
      courseIdList = _getMain().getEntityList(Cmd.OB_COURSE_ENTITY, shlexSplit=True)
    elif myarg in {'id', 'ids'}:
      invitationIds = _getMain().getEntityList(Cmd.OB_CLASSROOM_INVITATION_ID_ENTITY)
    elif myarg == 'role':
      role = _getMain().getChoice(CLASSROOM_ROLE_MAP, mapChoice=True)
    else:
      _getMain().unknownArgumentExit()
  if courseIdList is None:
    _getMain().missingArgumentExit('courses <CourseEntity>')
  entityType = Ent.CLASSROOM_INVITATION
  i, count, coursesInfo = _getCoursesOwnerInfo(croom, courseIdList, True)
  for courseId, courseInfo in coursesInfo.items():
    i += 1
    courseNameId = f'{courseInfo["name"]} ({courseId})'
    if invitationIds is not None:
      userInvitationIds = invitationIds
    else:
      status, userInvitationIds = _getClassroomInvitationIds(courseInfo['croom'], None, [courseId], role, i, count)
      if status < 0:
        continue
    jcount = len(userInvitationIds)
    _getMain().entityPerformActionNumItems([Ent.COURSE, courseNameId], jcount, entityType, i, count)
    Ind.Increment()
    j = 0
    for invitationId in userInvitationIds:
      j += 1
      try:
        _getMain().callGAPI(courseInfo['croom'].invitations(), 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.FAILED_PRECONDITION, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                 id=invitationId)
        _getMain().entityActionPerformed([Ent.COURSE, courseNameId, entityType, invitationId], j, jcount)
      except (GAPI.notFound, GAPI.failedPrecondition, GAPI.forbidden, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedWarning([Ent.COURSE, courseNameId, entityType, invitationId], str(e), j, jcount)
    Ind.Decrement()

# gam show classroominvitations (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[role all|owner|student|teacher] [formatjson]
# gam print classroominvitations [todrive <ToDriveAttribute>*] (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[role all|owner|student|teacher] [formatjson [quotechar <Character>]]
def doPrintShowClassroomInvitations():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  classroomEmails = {}
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties(['id', 'name'])
  role = CLASSROOM_ROLE_ALL
  csvPF = _getMain().CSVPrintFile(['courseId', 'courseName']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'role':
      role = _getMain().getChoice(CLASSROOM_ROLE_MAP, mapChoice=True)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties)
  if coursesInfo is None:
    return
  if csvPF and not FJQC.formatJSON:
    csvPF.AddTitles(['id', 'role', 'userId', 'userEmail'])
    csvPF.SetSortAllTitles()
  entityType = CLASSROOM_ROLE_ENTITY_MAP[role]
  i = 0
  count = len(coursesInfo)
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    courseName = course['name']
    status, invitations = _getClassroomInvitations(croom, None, courseId, role, i, count)
    if status > 0:
      jcount = len(invitations)
      if not FJQC.formatJSON:
        _getMain().entityPerformActionNumItems([Ent.COURSE, f'{courseName} ({courseId})'], jcount, entityType, i, count)
      if not csvPF:
        if not FJQC.formatJSON:
          Ind.Increment()
          j = 0
          for invitation in invitations:
            j += 1
            _getMain().printKeyValueListWithCount(['id', invitation['id']], j, jcount)
            Ind.Increment()
            _getMain().printKeyValueList(['role', invitation['role']])
            userId = invitation.get('userId')
            if userId is not None:
              _getMain().printKeyValueList(['userid', userId])
              _getMain().printKeyValueList(['userEmail', _getClassroomEmail(croom, classroomEmails, userId, userId)])
            Ind.Decrement()
          Ind.Decrement()
        else:
          _getMain().printLine(json.dumps(_getMain().cleanJSON(invitations), ensure_ascii=False, sort_keys=True))
      else:
        if not FJQC.formatJSON:
          for invitation in invitations:
            invitation['courseName'] = courseName
            userId = invitation.get('userId')
            if userId is not None:
              invitation['userEmail'] = _getClassroomEmail(croom, classroomEmails, userId, userId)
            csvPF.WriteRowNoFilter(invitation)
        else:
          csvPF.WriteRowNoFilter({'courseId': courseId, 'courseName': courseName,
                                  'JSON': json.dumps(_getMain().cleanJSON(invitations), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('ClassroomInvitations')

# gam <UserTypeEntity> print classroomprofile [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show classroomprofile
def printShowClassroomProfile(users):
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  csvPF = _getMain().CSVPrintFile(['emailAddress', 'id',
                        f'name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}givenName',
                        f'name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}familyName',
                        f'name{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}fullName',
                        'photoUrl'], indexedTitles=['permissions']) if Act.csvFormat() else None
  _getMain().getTodriveOnly(csvPF)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    userId = _getMain().normalizeEmailAddressOrUID(user)
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.CLASSROOM_USER_PROFILE, user, i, count)
    try:
      result = _getMain().callGAPI(croom.userProfiles(), 'get',
                        throwReasons=[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED, GAPI.BAD_REQUEST, GAPI.FORBIDDEN, GAPI.SERVICE_NOT_AVAILABLE],
                        retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                        userId=userId, fields='*')
      result.setdefault('verifiedTeacher', False)
      if not csvPF:
        _getMain().printEntity([Ent.USER, userId], i, count)
        Ind.Increment()
        _getMain().printKeyValueList(['email', result['emailAddress']])
        _getMain().printKeyValueList([UProp.PROPERTIES['id'][UProp.TITLE], result['id']])
        for up in USER_NAME_PROPERTY_PRINT_ORDER:
          if up in result['name']:
            _getMain().printKeyValueList([UProp.PROPERTIES[up][UProp.TITLE], result['name'][up]])
        _getMain().printKeyValueList([UProp.PROPERTIES['thumbnailPhotoUrl'][UProp.TITLE], result['photoUrl']])
        _getMain().printKeyValueList(['Permissions', ','.join([permission['permission'] for permission in result.get('permissions', [])])])
        _getMain().printKeyValueList(['Verified Teacher', result['verifiedTeacher']])
        Ind.Decrement()
      else:
        csvPF.WriteRowTitles(_getMain().flattenJSON(result))
    except (GAPI.notFound, GAPI.permissionDenied, GAPI.badRequest, GAPI.forbidden, GAPI.serviceNotAvailable) as e:
      _getMain().entityActionFailedWarning([Ent.USER, userId], str(e))
  if csvPF:
    csvPF.writeCSVfile('Classroom User Profiles')

# gam create course-studentgroups
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	((title <String>)|(select <StringEntity))+
#	[csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
def doCreateCourseStudentGroups():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  csvPF = None
  FJQC = _getMain().FormatJSONQuoteChar(None)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties(['name'])
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  kwargs  = {'courseId': None, 'body': {}}
  titles = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'title':
      titles.append(_getMain().getString(Cmd.OB_STRING, maxLen=100))
    elif myarg == 'select':
      titles.extend(_getMain().getEntityList(Cmd.OB_STRING_ENTITY, shlexSplit=True))
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'csv':
      csvPF = _getMain().CSVPrintFile(['courseId', 'courseName', 'studentGroupId', 'studentGroupTitle'])
      FJQC = _getMain().FormatJSONQuoteChar(csvPF)
    elif csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not titles:
    _getMain().missingArgumentExit('title')
  jcount = len(titles)
  if csvPF and FJQC.formatJSON:
    csvPF.SetJSONTitles(['courseId', 'courseName', 'JSON'])
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if coursesInfo is None:
    return
  count = len(coursesInfo)
  i = 0
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
    if not ocroom:
      continue
    kwargs['courseId'] = courseId
    _getMain().entityPerformActionNumItems([Ent.COURSE, courseId], jcount, Ent.COURSE_STUDENTGROUP, i, count)
    Ind.Increment()
    j = 0
    for title in titles:
      j += 1
      kwargs['body']['title'] = title
      kvList = [Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, None]
      try:
        studentGroup = _getMain().callGAPI(ocroom.courses().studentGroups(), 'create',
                                throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                                              GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                **kwargs)
        kvList[-1] = f"{studentGroup['title']}({studentGroup['id']})"
        if not csvPF:
          _getMain().entityActionPerformed(kvList, j, jcount)
        elif not  FJQC.formatJSON:
          csvPF.WriteRow({'courseId': courseId, 'courseName': course['name'],
                          'studentGroupId': studentGroup['id'], 'studentGroupTitle': studentGroup['title']})
        else:
          csvPF.WriteRowNoFilter({'courseId': courseId, 'courseName': course['name'],
                                  'JSON': json.dumps(_getMain().cleanJSON(studentGroup), ensure_ascii=False, sort_keys=True)})
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
        _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()
  if csvPF:
    csvPF.writeCSVfile('Course Student Groups')

# gam update course-studentgroup <CourseID> <StudentGroupID> title <String>
def doUpdateCourseStudentGroups():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  courseId = _getMain().getString(Cmd.OB_COURSE_ID)
  studentGroupId = _getMain().getString(Cmd.OB_STUDENTGROUP_ID)
  kwargs = {'courseId': courseId, 'id':  studentGroupId, 'body': {}, 'updateMask': ''}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'title':
      kwargs['body']['title'] = _getMain().getString(Cmd.OB_STRING)
      kwargs['updateMask'] = myarg
    else:
      _getMain().unknownArgumentExit()
  if 'title' not in kwargs['body']:
    _getMain().missingArgumentExit('title')
  _, count, coursesInfo = _getCoursesOwnerInfo(croom, [courseId], GC.Values[GC.USE_COURSE_OWNER_ACCESS])
  if count == 0:
    return
  ocroom = coursesInfo[courseId]['croom']
  courseId = coursesInfo[courseId]['id']
  kvList = [Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId]
  try:
    studentGroup = _getMain().callGAPI(ocroom.courses().studentGroups(), 'patch',
                            throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                                          GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                            retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                            **kwargs)
    kvList[-1] = f"{studentGroup['title']}({studentGroup['id']})"
    _getMain().entityActionPerformed(kvList)
  except GAPI.notFound as e:
    _getMain().entityActionFailedWarning(kvList, str(e))
  except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
    _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))

# gam delete course-studentgroups <CourseID> <StudentGroupIDEntity>
def doDeleteCourseStudentGroups():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  courseId = _getMain().getString(Cmd.OB_COURSE_ID)
  studentGroupIds = _getMain().getEntityList(Cmd.OB_STUDENTGROUP_ID_ENTITY, shlexSplit=False)
  _getMain().checkForExtraneousArguments()
  _, count, coursesInfo = _getCoursesOwnerInfo(croom, [courseId], GC.Values[GC.USE_COURSE_OWNER_ACCESS])
  if count == 0:
    return
  ocroom = coursesInfo[courseId]['croom']
  courseId = coursesInfo[courseId]['id']
  kwargs = {'courseId': courseId, 'id': None}
  kvList = [Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, None]
  count = len(studentGroupIds)
  i = 0
  for studentGroupId in studentGroupIds:
    i += 1
    kwargs['id'] = kvList[-1] = studentGroupId
    try:
      _getMain().callGAPI(ocroom.courses().studentGroups(), 'delete',
               throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               **kwargs)
      _getMain().entityActionPerformed(kvList, i, count)
    except GAPI.notFound as e:
      _getMain().entityActionFailedWarning(kvList, str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e), i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam clear course-studentgroups
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
def doClearCourseStudentGroups():
  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties(['name'])
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    else:
      _getMain().unknownArgumentExit()
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if coursesInfo is None:
    return
  count = len(coursesInfo)
  i = 0
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
    if not ocroom:
      continue
    kwargs = {'courseId': courseId, 'id': None}
    kvList = [Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, None]
    studentGroups = []
    _getMain().printGettingEntityItemForWhom(Ent.COURSE_STUDENTGROUP, _getMain().formatKeyValueList('', [Ent.Singular(Ent.COURSE), courseId], _getMain().currentCount(i, count)))
    pageMessage = _getMain().getPageMessage()
    try:
      studentGroups = _getMain().callGAPIpages(ocroom.courses().studentGroups(), 'list', 'studentGroups',
                                    pageMessage=pageMessage,
                                    throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    courseId=courseId)
    except GAPI.notFound as e:
      _getMain().entityActionFailedWarning([Ent.COURSE, courseId], str(e))
      continue
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    jcount = len(studentGroups)
    _getMain().entityPerformActionNumItems([Ent.COURSE, courseId], jcount, Ent.COURSE_STUDENTGROUP, i, count)
    Ind.Increment()
    j = 0
    for studentGroup in studentGroups:
      j += 1
      kwargs['id'] = kvList[-1] = studentGroup['id']
      try:
        _getMain().callGAPI(ocroom.courses().studentGroups(), 'delete',
                 throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 **kwargs)
        _getMain().entityActionPerformed(kvList, j, jcount)
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning(kvList, str(e), j, jcount)
      except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
        _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e), j, jcount)
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
    Ind.Decrement()

# gam print course-studentgroups [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[showitemcountonly] [formatjson [quotechar <Character>]]
def doPrintCourseStudentGroups(showMembers=False):
  def _getCourseStudents():
    studentIdEmailMap = {}
    try:
      students = _getMain().callGAPIpages(ocroom.courses().students(), 'list', 'students',
                               throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               courseId=courseId, fields='nextPageToken,students(profile(id,emailAddress))',
                               pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
      for student in students:
        studentIdEmailMap[student['profile']['id']] = student['profile']['emailAddress']
    except GAPI.notFound:
      pass
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    return studentIdEmailMap

  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  csvPF = _getMain().CSVPrintFile(['courseId', 'courseName', 'studentGroupId', 'studentGroupTitle'])
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  courseSelectionParameters = _initCourseSelectionParameters()
  courseShowProperties = _initCourseShowProperties(['name'])
  showItemCountOnly = False
  useOwnerAccess = GC.Values[GC.USE_COURSE_OWNER_ACCESS]
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getCourseSelectionParameters(myarg, courseSelectionParameters):
      pass
    elif myarg == 'showitemcountonly':
      showItemCountOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  coursesInfo = _getCoursesInfo(croom, courseSelectionParameters, courseShowProperties, useOwnerAccess)
  if coursesInfo is None:
    if showItemCountOnly:
      _getMain().writeStdout('0\n')
    return
  itemCount = 0
  count = len(coursesInfo)
  i = 0
  for course in coursesInfo:
    i += 1
    courseId = course['id']
    ocroom = _getCourseOwnerSA(croom, course, useOwnerAccess)
    if not ocroom:
      continue
    studentGroups = []
    _getMain().printGettingEntityItemForWhom(Ent.COURSE_STUDENTGROUP, _getMain().formatKeyValueList('', [Ent.Singular(Ent.COURSE), courseId], _getMain().currentCount(i, count)))
    pageMessage = _getMain().getPageMessage()
    try:
      studentGroups = _getMain().callGAPIpages(ocroom.courses().studentGroups(), 'list', 'studentGroups',
                                    pageMessage=pageMessage,
                                    throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                                                  GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                    retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                    courseId=courseId)
    except GAPI.notFound as e:
      _getMain().entityActionFailedWarning([Ent.COURSE, courseId], str(e))
      continue
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
    if not showMembers and showItemCountOnly:
      itemCount += len(studentGroups)
      continue
    if showMembers:
      studentIdEmailMap = _getCourseStudents()
    for studentGroup in studentGroups:
      studentGroupId = studentGroup['id']
      if not showMembers:
        if not FJQC.formatJSON:
          csvPF.WriteRowTitles({'courseId': courseId, 'courseName': course['name'],
                                'studentGroupId': studentGroupId, 'studentGroupTitle': studentGroup['title']})
        else:
          row = {'courseId': courseId, 'courseName': course['name']}
          if csvPF.CheckRowTitles(row):
            row['JSON'] = json.dumps(_getMain().cleanJSON(studentGroup), ensure_ascii=False, sort_keys=False)
            csvPF.WriteRowTitles(row)
        continue
      _getMain().printGettingEntityItemForWhom(Ent.STUDENT, _getMain().formatKeyValueList('', [Ent.Singular(Ent.COURSE_STUDENTGROUP), studentGroupId],
                                                                 _getMain().currentCount(i, count)))
      pageMessage = _getMain().getPageMessage()
      try:
        students = _getMain().callGAPIpages(ocroom.courses().studentGroups().studentGroupMembers(), 'list', 'studentGroupMembers',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                               GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                                 courseId=courseId, studentGroupId=studentGroupId)
        if showItemCountOnly:
          itemCount += len(students)
          continue
        for member in students:
          member['userEmail'] = studentIdEmailMap.get(member['userId'], member['userId'])
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning([Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId], str(e))
        continue
      except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
        _getMain().entityActionFailedExit([Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId], str(e))
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
      if not FJQC.formatJSON:
        row = {'courseId': courseId, 'courseName': course['name'],
               'studentGroupId': studentGroupId, 'studentGroupTitle': studentGroup['title']}
        for member in students:
          csvPF.WriteRowTitles(_getMain().flattenJSON(member, flattened=row.copy()))
      else:
        row = {'courseId': courseId, 'courseName': course['name'],
               'studentGroupId': studentGroupId, 'studentGroupTitle': studentGroup['title']}
        row['JSON'] = json.dumps(list(students))
        csvPF.WriteRowNoFilter(row)
  if showItemCountOnly:
    _getMain().writeStdout(f'{itemCount}\n')
    return
  if not showMembers:
    title = 'Course Student Groups'
  else:
    title = 'Course Student Group Members'
  csvPF.writeCSVfile(title)

# gam create course-studentgroup-members <CourseID> <StudentGroupID> <UserTypeEntity>
# gam delete course-studentgroup-members <CourseID> <StudentGroupID> <UserTypeEntity>
# gam sync course-studentgroup-members <CourseID> <StudentGroupID> <UserTypeEntity>
# gam clear course-studentgroup-members <CourseID> <StudentGroupID>
def doProcessCourseStudentGroupMembers():
  def _getCourseStudents():
    studentIdEmailMap = {}
    studentEmailIdMap = {}
    try:
      students = _getMain().callGAPIpages(ocroom.courses().students(), 'list', 'students',
                               throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               courseId=courseId, fields='nextPageToken,students(profile(id,emailAddress))',
                               pageSize=GC.Values[GC.CLASSROOM_MAX_RESULTS])
      for student in students:
        studentIdEmailMap[student['profile']['id']] = student['profile']['emailAddress'].lower()
        studentEmailIdMap[student['profile']['emailAddress'].lower()] = student['profile']['id']
      return (studentIdEmailMap, studentEmailIdMap)
    except GAPI.notFound as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

  def _getGroupCurrentStudents():
    _getMain().printGettingEntityItemForWhom(Ent.STUDENT, _getMain().formatKeyValueList('', [Ent.Singular(Ent.COURSE_STUDENTGROUP), studentGroupId], ''))
    pageMessage = _getMain().getPageMessage()
    try:
      return _getMain().callGAPIpages(ocroom.courses().studentGroups().studentGroupMembers(), 'list', 'studentGroupMembers',
                           pageMessage=pageMessage,
                           throwReasons=[GAPI.NOT_FOUND, GAPI.SERVICE_NOT_AVAILABLE,
                                         GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                           retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                           courseId=courseId, studentGroupId=studentGroupId)
    except GAPI.notFound as e:
      _getMain().entityActionFailedWarning([Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId], str(e))
      return []
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

  def _validateClStudents(clStudents):
    status = True
    clStudentIds = []
    count = len(clStudents)
    i = 0
    kvList = [Ent.COURSE, courseId, Ent.STUDENT, '']
    for student in clStudents:
      i += 1
      student = _getMain().normalizeEmailAddressOrUID(student)
      if student in studentIdEmailMap:
        clStudentIds.append(student)
      elif student in studentEmailIdMap:
        clStudentIds.append(studentEmailIdMap[student])
      else:
        kvList[-1] = student
        _getMain().entityActionFailedWarning(kvList, Msg.STUDENT_NOT_IN_COURSE, i, count)
        status = False
    return clStudentIds if status else None

  def _processStudent(function, kvList, kwargs, i, count):
    try:
      _getMain().callGAPI(ocroom.courses().studentGroups().studentGroupMembers(), function,
               throwReasons=[GAPI.NOT_FOUND, GAPI.ALREADY_EXISTS,
                             GAPI.SERVICE_NOT_AVAILABLE, GAPI.NOT_IMPLEMENTED,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
               **kwargs)
      _getMain().entityActionPerformed(kvList, i, count)
    except (GAPI.alreadyExists, GAPI.notFound) as e:
      _getMain().entityActionFailedWarning(kvList, str(e), i, count)
    except (GAPI.serviceNotAvailable, GAPI.notImplemented) as e:
      _getMain().entityActionFailedExit([Ent.COURSE, courseId], str(e))
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

  def _addStudents(students):
    count = len(students)
    i = 0
    _getMain().entityPerformActionNumItems([Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId], count, Ent.STUDENT)
    kvList = [Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId, Ent.STUDENT, '']
    kwargs = {'courseId': courseId, 'studentGroupId': studentGroupId, 'body': {'userId': ''}}
    Ind.Increment()
    for student in students:
      i += 1
      kvList[-1] = studentIdEmailMap[student]
      kwargs['body']['userId'] = student
      _processStudent('create', kvList, kwargs, i, count)
    Ind.Decrement()

  def _removeStudents(students):
    count = len(students)
    i = 0
    _getMain().entityPerformActionNumItems([Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId], count, Ent.STUDENT)
    kvList = [Ent.COURSE, courseId, Ent.COURSE_STUDENTGROUP, studentGroupId, Ent.STUDENT, '']
    kwargs = {'courseId': courseId, 'studentGroupId': studentGroupId, 'userId': ''}
    Ind.Increment()
    for student in students:
      i += 1
      kvList[-1] = studentIdEmailMap[student]
      kwargs['userId'] = student
      _processStudent('delete', kvList, kwargs, i, count)
    Ind.Decrement()

  croom = _getMain().buildGAPIObject(API.CLASSROOM)
  action = Act.Get()
  courseId = _getMain().getString(Cmd.OB_COURSE_ID)
  studentGroupId = _getMain().getString(Cmd.OB_STUDENTGROUP_ID)
  if action != Act.CLEAR:
    _, clStudents = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS, groupMemberType=Ent.TYPE_USER)
    clStudentIds = []
    _getMain().checkForExtraneousArguments()
  _, count, coursesInfo = _getCoursesOwnerInfo(croom, [courseId], GC.Values[GC.USE_COURSE_OWNER_ACCESS])
  if count == 0:
    return
  ocroom = coursesInfo[courseId]['croom']
  courseId = coursesInfo[courseId]['id']
  studentIdEmailMap, studentEmailIdMap = _getCourseStudents()
  if action in {Act.SYNC, Act.CLEAR}:
    currentStudents = [student['userId'] for student in _getGroupCurrentStudents()]
  if action != Act.CLEAR:
    clStudentIds = _validateClStudents(clStudents)
    if clStudentIds is None:
      return
  if action == Act.CLEAR:
    _removeStudents(currentStudents)
  elif action == Act.DELETE:
    _removeStudents(clStudentIds)
  elif action in {Act.ADD, Act.CREATE}:
    _addStudents(clStudentIds)
  else: # elif action == Act.SYNC:
    currentMembersSet = set(currentStudents)
    syncMembersSet = set(clStudentIds)
    removeStudentsSet = currentMembersSet-syncMembersSet
    addStudentsSet = syncMembersSet-currentMembersSet
    Act.Set(Act.DELETE)
    _removeStudents(removeStudentsSet)
    Act.Set(Act.ADD)
    _addStudents(addStudentsSet)

# gam print course-studentgroup-members [todrive <ToDriveAttribute>*]
#	(course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
#	[showitemcountonly] [formatjson [quotechar <Character>]]
def doPrintCourseStudentGroupMembers():
  doPrintCourseStudentGroups(showMembers=True)

