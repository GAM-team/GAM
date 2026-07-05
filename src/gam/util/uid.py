"""UID-to-email-address resolution utilities.

Convert UIDs to email addresses by querying the Directory/CI APIs.
Includes low-level lookup functions (getUserEmailFromID, etc.) that
were originally in entity.py but belong here since they're pure
UID-resolution helpers.
"""

import re
import warnings

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gam.var import Cmd, Ent
from util.api import buildGAPIObject
from util.api_call import callGAPI
from util.args import getPhraseDNEorSNA, normalizeEmailAddressOrUID
from util.errors import entityDoesNotExistExit

NON_EMAIL_MEMBER_PREFIXES = (
                              "cbcm-browser.",
                              "chrome-os-device.",
                            )


def getUserEmailFromID(uid, cd):
  try:
    result = callGAPI(cd.users(), 'get',
                      throwReasons=GAPI.USER_GET_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      userKey=uid, fields='primaryEmail')
    return result.get('primaryEmail')
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.backendError, GAPI.systemError, GAPI.serviceNotAvailable):
    return None

def getGroupEmailFromID(uid, cd):
  try:
    result = callGAPI(cd.groups(), 'get',
                      throwReasons=GAPI.GROUP_GET_THROW_REASONS,
                      retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                      groupKey=uid, fields='email')
    return result.get('email')
  except (GAPI.groupNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden,
          GAPI.badRequest, GAPI.serviceNotAvailable):
    return None

def getServiceAccountEmailFromID(account_id, sal=None):
  if sal is None:
    sal = buildGAPIObject(API.SERVICEACCOUNTLOOKUP)
  try:
    certs = callGAPI(sal.serviceaccounts(), 'lookup',
                     throwReasons = [GAPI.BAD_REQUEST, GAPI.NOT_FOUND, GAPI.RESOURCE_NOT_FOUND,  GAPI.INVALID_ARGUMENT],
                     account=account_id)
  except (GAPI.badRequest, GAPI.notFound, GAPI.resourceNotFound, GAPI.invalidArgument):
    return None
  sa_cn_rx = r'CN=(.+)\.(.+)\.iam\.gservice.*'
  sa_emails = []
  for _, raw_cert in certs.items():
    cert = x509.load_pem_x509_certificate(raw_cert.encode(), default_backend())
    # suppress crytography warning due to long service account email
    with warnings.catch_warnings():
      warnings.filterwarnings('ignore', message='.*Attribute\'s length.*')
      mg = re.match(sa_cn_rx, cert.issuer.rfc4514_string())
    if mg:
      sa_email = f'{mg.group(1)}@{mg.group(2)}.iam.gserviceaccount.com'
      if sa_email not in sa_emails:
        sa_emails.append(sa_email)
  return GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER].join(sa_emails)


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
