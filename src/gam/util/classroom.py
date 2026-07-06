"""Classroom API data-fetching utilities.

Pure data-fetching functions for the Google Classroom API.
These are single-purpose functions that take an API client and parameters,
call Google APIs, and return structured data.  They contain no CLI argument
parsing or output formatting.
"""

from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import api as API

from gam.util.api_call import callGAPI
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api import ClientAPIAccessDeniedExit
from gam.util.course_scope import addCourseIdScope
from gam.util.display import (
    entityActionFailedWarning,
    entityDoesNotExistWarning,
)

from gam.var import Ent


def getCourseOwnerServiceObject(croom, course, useOwnerAccess):
  """Build a Classroom API service object impersonating the course owner.

  If *useOwnerAccess* is ``False`` the original *croom* service is returned
  unchanged.  Otherwise a service-account-based client is built (and cached
  in ``GM.Globals[GM.CLASSROOM_OWNER_SA]``) for the course's ``ownerId``.
  """
  if not useOwnerAccess:
    return croom
  courseOwnerId = course["ownerId"]
  if courseOwnerId not in GM.Globals[GM.CLASSROOM_OWNER_SA]:
    _, GM.Globals[GM.CLASSROOM_OWNER_SA][courseOwnerId] = buildGAPIServiceObject(API.CLASSROOM, f'uid:{courseOwnerId}')
  return GM.Globals[GM.CLASSROOM_OWNER_SA][courseOwnerId]


def getCoursesOwnerInfo(croom, courseIds, useOwnerAccess, addCIIdScope=True):
  """Fetch course metadata and optionally build owner-impersonating clients.

  For each *courseId*, calls ``courses.get()`` to retrieve the course's ``id``,
  ``name``, and ``ownerId``, then delegates to :func:`getCourseOwnerServiceObject`
  to obtain the appropriate Classroom API client.

  Returns ``(0, len(coursesInfo), coursesInfo)`` where *coursesInfo* maps
  each resolved course ID to ``{'id': ..., 'name': ..., 'croom': ...}``.
  """
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
        ocroom = getCourseOwnerServiceObject(croom, course, useOwnerAccess)
        if ocroom is not None:
          coursesInfo[ciCourseId] = {'id': course['id'], 'name': course['name'], 'croom': ocroom}
      except GAPI.notFound:
        entityDoesNotExistWarning(Ent.COURSE, courseId)
      except GAPI.serviceNotAvailable as e:
        entityActionFailedWarning([Ent.COURSE, courseId], str(e))
      except (GAPI.forbidden, GAPI.permissionDenied) as e:
        ClientAPIAccessDeniedExit(str(e))
  return 0, len(coursesInfo), coursesInfo
