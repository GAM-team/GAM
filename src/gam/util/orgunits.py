"""GAM OrgUnit helper utilities.

OrgUnit path/ID resolution and parent OrgUnit traversal.
"""

import sys

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM


def _getMain():
  return sys.modules['gam']


def getOrgUnitItem(pathOnly=False, absolutePath=True, cd=None):
  Cmd = _getMain().Cmd
  if Cmd.ArgumentsRemaining():
    path = Cmd.Current().strip()
    if path == 'root':
      path = '/'
    if path:
      if pathOnly and (path.startswith('id:') or path.startswith('uid:')) and cd is not None:
        try:
          result = _getMain().callGAPI(cd.orgunits(), 'get',
                    throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                    customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=path,
                    fields='orgUnitPath')
          Cmd.Advance()
          if absolutePath:
            return _getMain().makeOrgUnitPathAbsolute(result['orgUnitPath'])
          return _getMain().makeOrgUnitPathRelative(result['orgUnitPath'])
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError,
                GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
          _getMain().checkEntityAFDNEorAccessErrorExit(cd, _getMain().Ent.ORGANIZATIONAL_UNIT, path)
        _getMain().invalidArgumentExit(Cmd.OB_ORGUNIT_PATH)
      Cmd.Advance()
      if absolutePath:
        return _getMain().makeOrgUnitPathAbsolute(path)
      return _getMain().makeOrgUnitPathRelative(path)
  _getMain().missingArgumentExit([Cmd.OB_ORGUNIT_ITEM, Cmd.OB_ORGUNIT_PATH][pathOnly])

def getTopLevelOrgId(cd, parentOrgUnitPath):
  Ent = _getMain().Ent
  if parentOrgUnitPath != '/':
    try:
      result = _getMain().callGAPI(cd.orgunits(), 'get',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=_getMain().encodeOrgUnitPath(_getMain().makeOrgUnitPathRelative(parentOrgUnitPath)),
                fields='orgUnitId')
      return result['orgUnitId']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      return None
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      _getMain().checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, parentOrgUnitPath)
      return None
  try:
    result = _getMain().callGAPI(cd.orgunits(), 'list',
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
    _getMain().checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, parentOrgUnitPath)
    return None

def getOrgUnitId(cd=None, orgUnit=None):
  Ent = _getMain().Ent
  if cd is None:
    cd = _getMain().buildGAPIObject(API.DIRECTORY)
  if orgUnit is None:
    orgUnit = getOrgUnitItem()
  try:
    if orgUnit == '/':
      result = _getMain().callGAPI(cd.orgunits(), 'list',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath='/', type='children',
                fields='organizationUnits(parentOrgUnitId,parentOrgUnitPath)')
      if result.get('organizationUnits', []):
        return (result['organizationUnits'][0]['parentOrgUnitPath'], result['organizationUnits'][0]['parentOrgUnitId'])
      topLevelOrgId = getTopLevelOrgId(cd, '/')
      if topLevelOrgId:
        return (orgUnit, topLevelOrgId)
      return (orgUnit, '/') #Bogus but should never happen
    result = _getMain().callGAPI(cd.orgunits(), 'get',
              throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
              customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=_getMain().encodeOrgUnitPath(_getMain().makeOrgUnitPathRelative(orgUnit)),
              fields='orgUnitId,orgUnitPath')
    return (result['orgUnitPath'], result['orgUnitId'])
  except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
    _getMain().entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, orgUnit)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    _getMain().accessErrorExit(cd)

def getAllParentOrgUnitsForUser(cd, user):
  Ent = _getMain().Ent
  try:
    result = _getMain().callGAPI(cd.users(), 'get',
              throwReasons=GAPI.USER_GET_THROW_REASONS,
              userKey=user, fields='orgUnitPath', projection='basic')
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden):
    _getMain().entityDoesNotExistExit(Ent.USER, user)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    _getMain().accessErrorExit(cd)
  parentPath = result['orgUnitPath']
  if parentPath == '/':
    orgUnitPath, orgUnitId = getOrgUnitId(cd, '/')
    return {orgUnitId: orgUnitPath}
  parentPath = _getMain().encodeOrgUnitPath(_getMain().makeOrgUnitPathRelative(parentPath))
  orgUnits = {}
  while True:
    try:
      result = _getMain().callGAPI(cd.orgunits(), 'get',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=parentPath,
                fields='orgUnitId,orgUnitPath,parentOrgUnitId')
      orgUnits[result['orgUnitId']] = result['orgUnitPath']
      if 'parentOrgUnitId' not in result:
        break
      parentPath = result['parentOrgUnitId']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      _getMain().entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, parentPath)
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      _getMain().accessErrorExit(cd)
  return orgUnits
