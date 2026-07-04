"""UID-to-email-address resolution utilities.

Convert UIDs to email addresses by querying the Directory/CI APIs.
Extracted from entity.py to break the entity↔api circular dependency.
"""

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gam.var import Ent
from util.api import buildGAPIObject
from util.api_call import callGAPI
from util.args import normalizeEmailAddressOrUID

NON_EMAIL_MEMBER_PREFIXES = (
                              "cbcm-browser.",
                              "chrome-os-device.",
                            )

def convertUIDtoEmailAddressWithType(emailAddressOrUID, cd=None, sal=None, emailTypes=None,
                                     checkForCustomerId=False, ciGroupsAPI=False, aliasAllowed=True):
  if emailTypes is None:
    emailTypes = ['user']
  elif not isinstance(emailTypes, list):
    emailTypes = [emailTypes] if emailTypes != 'any' else ['user', 'group']
  if checkForCustomerId and (emailAddressOrUID == GC.Values[GC.CUSTOMER_ID]):
    return (emailAddressOrUID, 'email')
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID, ciGroupsAPI=ciGroupsAPI)
  if ciGroupsAPI and emailAddressOrUID.startswith('groups/'):
    return emailAddressOrUID
  if normalizedEmailAddressOrUID.find('@') > 0 and aliasAllowed:
    return (normalizedEmailAddressOrUID, 'email')
  if cd is None:
    cd = buildGAPIObject(API.DIRECTORY)
  if 'user' in emailTypes and 'group' in emailTypes:
    # Google User IDs *TEND* to be integers while groups tend to have letters
    # thus we can optimize which check we try first. We'll still check
    # both since there is no guarantee this will always be true.
    if normalizedEmailAddressOrUID.isdigit():
      uid = getUserEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'user')
      uid = getGroupEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'group')
    else:
      uid = getGroupEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'group')
      uid = getUserEmailFromID(normalizedEmailAddressOrUID, cd)
      if uid:
        return (uid, 'user')
  elif 'user' in emailTypes:
    uid = getUserEmailFromID(normalizedEmailAddressOrUID, cd)
    if uid:
      return (uid, 'user')
  elif 'group' in emailTypes:
    uid = getGroupEmailFromID(normalizedEmailAddressOrUID, cd)
    if uid:
      return (uid, 'group')
  if 'resource' in emailTypes:
    try:
      result = callGAPI(cd.resources().calendars(), 'get',
                        throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN],
                        calendarResourceId=normalizedEmailAddressOrUID,
                        customer=GC.Values[GC.CUSTOMER_ID], fields='resourceEmail')
      if 'resourceEmail' in result:
        return (result['resourceEmail'].lower(), 'resource')
    except (GAPI.badRequest, GAPI.resourceNotFound, GAPI.forbidden):
      pass
  if 'serviceaccount' in emailTypes:
    uid = getServiceAccountEmailFromID(normalizedEmailAddressOrUID, sal)
    if uid:
      return (uid, 'serviceaccount')
  return (normalizedEmailAddressOrUID, 'unknown')


def convertUIDtoEmailAddress(emailAddressOrUID, cd=None, emailTypes=None,
                             checkForCustomerId=False, ciGroupsAPI=False, aliasAllowed=True):
  if ciGroupsAPI:
    if emailAddressOrUID.startswith(NON_EMAIL_MEMBER_PREFIXES):
      return emailAddressOrUID
    normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID, ciGroupsAPI=ciGroupsAPI)
    if normalizedEmailAddressOrUID.startswith(NON_EMAIL_MEMBER_PREFIXES):
      return normalizedEmailAddressOrUID
  email, _ = convertUIDtoEmailAddressWithType(emailAddressOrUID, cd, None, emailTypes,
                                              checkForCustomerId, ciGroupsAPI, aliasAllowed)
  return email


def convertEmailAddressToUID(emailAddressOrUID, cd=None, emailType='user', savedLocation=None):
  normalizedEmailAddressOrUID = normalizeEmailAddressOrUID(emailAddressOrUID)
  if normalizedEmailAddressOrUID.find('@') == -1:
    return normalizedEmailAddressOrUID
  if cd is None:
    cd = buildGAPIObject(API.DIRECTORY)
  if emailType != 'group':
    try:
      return callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      userKey=normalizedEmailAddressOrUID, fields='id')['id']
    except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
            GAPI.badRequest, GAPI.backendError, GAPI.systemError):
      if emailType == 'user':
        if savedLocation is not None:
          Cmd.SetLocation(savedLocation)
        entityDoesNotExistExit(Ent.USER, normalizedEmailAddressOrUID, errMsg=getPhraseDNEorSNA(normalizedEmailAddressOrUID))
  try:
    return callGAPI(cd.groups(), 'get',
                    throwReasons=GAPI.GROUP_GET_THROW_REASONS, retryReasons=GAPI.GROUP_GET_RETRY_REASONS,
                    groupKey=normalizedEmailAddressOrUID, fields='id')['id']
  except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.invalid, GAPI.systemError):
    if savedLocation is not None:
      Cmd.SetLocation(savedLocation)
    entityDoesNotExistExit([Ent.USER, Ent.GROUP][emailType == 'group'], normalizedEmailAddressOrUID, errMsg=getPhraseDNEorSNA(normalizedEmailAddressOrUID))
