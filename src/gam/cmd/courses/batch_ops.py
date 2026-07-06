"""Batch operations for Classroom course items."""

import re

from gam.util.batch import RI_ENTITY, RI_J, RI_JCOUNT, RI_ITEM

from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.api import waitOnFailure
from gam.util.api_call import callGAPI, checkGAPIError
from gam.util.args import (
    getHTTPError,
    getPhraseDNEorSNA,
    normalizeEmailAddressOrUID,
)
from gam.util.batch import batchRequestID, executeBatch
from gam.util.display import entityActionFailedWarning, entityActionPerformed, entityPerformActionNumItems
from gam.util.course_scope import addCourseAliasScope, addCourseIdScope, removeCourseIdScope, removeCourseAliasScope

from gam.var import Act, Ent, Ind


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
