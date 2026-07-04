"""GAM OrgUnit helper utilities.

OrgUnit path/ID resolution and parent OrgUnit traversal.
"""

import sys

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from util.access import accessErrorExit, checkEntityAFDNEorAccessErrorExit
from util.api import buildGAPIObject, callGAPI
from util.args import encodeOrgUnitPath, makeOrgUnitPathAbsolute, makeOrgUnitPathRelative
from util.errors import entityDoesNotExistExit, invalidArgumentExit, missingArgumentExit
from gam.var import Cmd, Ent




def getOrgUnitItem(pathOnly=False, absolutePath=True, cd=None):
  if Cmd.ArgumentsRemaining():
    path = Cmd.Current().strip()
    if path == 'root':
      path = '/'
    if path:
      if pathOnly and (path.startswith('id:') or path.startswith('uid:')) and cd is not None:
        try:
          result = callGAPI(cd.orgunits(), 'get',
                    throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                    customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=path,
                    fields='orgUnitPath')
          Cmd.Advance()
          if absolutePath:
            return makeOrgUnitPathAbsolute(result['orgUnitPath'])
          return makeOrgUnitPathRelative(result['orgUnitPath'])
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError,
                GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
          checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, path)
        invalidArgumentExit(Cmd.OB_ORGUNIT_PATH)
      Cmd.Advance()
      if absolutePath:
        return makeOrgUnitPathAbsolute(path)
      return makeOrgUnitPathRelative(path)
  missingArgumentExit([Cmd.OB_ORGUNIT_ITEM, Cmd.OB_ORGUNIT_PATH][pathOnly])

def getTopLevelOrgId(cd, parentOrgUnitPath):
  if parentOrgUnitPath != '/':
    try:
      result = callGAPI(cd.orgunits(), 'get',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(parentOrgUnitPath)),
                fields='orgUnitId')
      return result['orgUnitId']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      return None
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, parentOrgUnitPath)
      return None
  try:
    result = callGAPI(cd.orgunits(), 'list',
              throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
              customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath='/', type='allIncludingParent',
              fields='organizationUnits(orgUnitId,orgUnitPath)')
    for orgUnit in result.get('organizationUnits', []):
      if orgUnit['orgUnitPath'] == '/':
        return orgUnit['orgUnitId']
    return None
  except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
    return None
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, parentOrgUnitPath)
    return None

def getOrgUnitId(cd=None, orgUnit=None):
  if cd is None:
    cd = buildGAPIObject(API.DIRECTORY)
  if orgUnit is None:
    orgUnit = getOrgUnitItem()
  try:
    if orgUnit == '/':
      result = callGAPI(cd.orgunits(), 'list',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath='/', type='children',
                fields='organizationUnits(parentOrgUnitId,parentOrgUnitPath)')
      if result.get('organizationUnits', []):
        return (result['organizationUnits'][0]['parentOrgUnitPath'], result['organizationUnits'][0]['parentOrgUnitId'])
      topLevelOrgId = getTopLevelOrgId(cd, '/')
      if topLevelOrgId:
        return (orgUnit, topLevelOrgId)
      return (orgUnit, '/') #Bogus but should never happen
    result = callGAPI(cd.orgunits(), 'get',
              throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
              customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=encodeOrgUnitPath(makeOrgUnitPathRelative(orgUnit)),
              fields='orgUnitId,orgUnitPath')
    return (result['orgUnitPath'], result['orgUnitId'])
  except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
    entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, orgUnit)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    accessErrorExit(cd)

def getAllParentOrgUnitsForUser(cd, user):
  try:
    result = callGAPI(cd.users(), 'get',
              throwReasons=GAPI.USER_GET_THROW_REASONS,
              userKey=user, fields='orgUnitPath', projection='basic')
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden):
    entityDoesNotExistExit(Ent.USER, user)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    accessErrorExit(cd)
  parentPath = result['orgUnitPath']
  if parentPath == '/':
    orgUnitPath, orgUnitId = getOrgUnitId(cd, '/')
    return {orgUnitId: orgUnitPath}
  parentPath = encodeOrgUnitPath(makeOrgUnitPathRelative(parentPath))
  orgUnits = {}
  while True:
    try:
      result = callGAPI(cd.orgunits(), 'get',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=parentPath,
                fields='orgUnitId,orgUnitPath,parentOrgUnitId')
      orgUnits[result['orgUnitId']] = result['orgUnitPath']
      if 'parentOrgUnitId' not in result:
        break
      parentPath = result['parentOrgUnitId']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, parentPath)
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      accessErrorExit(cd)
  return orgUnits

def _getOrgunitsOrgUnitIdPath(cd, orgUnit):
  if orgUnit.startswith('orgunits/'):
    orgUnit = f'id:{orgUnit[9:]}'
  orgUnitPath, orgUnitId = getOrgUnitId(cd, orgUnit)
  return (orgUnitPath, f'orgunits/{orgUnitId[3:]}')
