"""GAM OrgUnit helper utilities.

OrgUnit path/ID resolution and parent OrgUnit traversal.
"""

import sys

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM


_gam = lambda: sys.modules['gam']


def getOrgUnitItem(pathOnly=False, absolutePath=True, cd=None):
  Cmd = _gam().Cmd
  if Cmd.ArgumentsRemaining():
    path = Cmd.Current().strip()
    if path == 'root':
      path = '/'
    if path:
      if pathOnly and (path.startswith('id:') or path.startswith('uid:')) and cd is not None:
        try:
          result = _gam().callGAPI(cd.orgunits(), 'get',
                    throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                    customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=path,
                    fields='orgUnitPath')
          Cmd.Advance()
          if absolutePath:
            return _gam().makeOrgUnitPathAbsolute(result['orgUnitPath'])
          return _gam().makeOrgUnitPathRelative(result['orgUnitPath'])
        except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError,
                GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
          _gam().checkEntityAFDNEorAccessErrorExit(cd, _gam().Ent.ORGANIZATIONAL_UNIT, path)
        _gam().invalidArgumentExit(Cmd.OB_ORGUNIT_PATH)
      Cmd.Advance()
      if absolutePath:
        return _gam().makeOrgUnitPathAbsolute(path)
      return _gam().makeOrgUnitPathRelative(path)
  _gam().missingArgumentExit([Cmd.OB_ORGUNIT_ITEM, Cmd.OB_ORGUNIT_PATH][pathOnly])

def getTopLevelOrgId(cd, parentOrgUnitPath):
  Ent = _gam().Ent
  if parentOrgUnitPath != '/':
    try:
      result = _gam().callGAPI(cd.orgunits(), 'get',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=_gam().encodeOrgUnitPath(_gam().makeOrgUnitPathRelative(parentOrgUnitPath)),
                fields='orgUnitId')
      return result['orgUnitId']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      return None
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      _gam().checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, parentOrgUnitPath)
      return None
  try:
    result = _gam().callGAPI(cd.orgunits(), 'list',
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
    _gam().checkEntityAFDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, parentOrgUnitPath)
    return None

def getOrgUnitId(cd=None, orgUnit=None):
  Ent = _gam().Ent
  if cd is None:
    cd = _gam().buildGAPIObject(API.DIRECTORY)
  if orgUnit is None:
    orgUnit = getOrgUnitItem()
  try:
    if orgUnit == '/':
      result = _gam().callGAPI(cd.orgunits(), 'list',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath='/', type='children',
                fields='organizationUnits(parentOrgUnitId,parentOrgUnitPath)')
      if result.get('organizationUnits', []):
        return (result['organizationUnits'][0]['parentOrgUnitPath'], result['organizationUnits'][0]['parentOrgUnitId'])
      topLevelOrgId = getTopLevelOrgId(cd, '/')
      if topLevelOrgId:
        return (orgUnit, topLevelOrgId)
      return (orgUnit, '/') #Bogus but should never happen
    result = _gam().callGAPI(cd.orgunits(), 'get',
              throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
              customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=_gam().encodeOrgUnitPath(_gam().makeOrgUnitPathRelative(orgUnit)),
              fields='orgUnitId,orgUnitPath')
    return (result['orgUnitPath'], result['orgUnitId'])
  except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
    _gam().entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, orgUnit)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    _gam().accessErrorExit(cd)

def getAllParentOrgUnitsForUser(cd, user):
  Ent = _gam().Ent
  try:
    result = _gam().callGAPI(cd.users(), 'get',
              throwReasons=GAPI.USER_GET_THROW_REASONS,
              userKey=user, fields='orgUnitPath', projection='basic')
  except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden):
    _gam().entityDoesNotExistExit(Ent.USER, user)
  except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
    _gam().accessErrorExit(cd)
  parentPath = result['orgUnitPath']
  if parentPath == '/':
    orgUnitPath, orgUnitId = getOrgUnitId(cd, '/')
    return {orgUnitId: orgUnitPath}
  parentPath = _gam().encodeOrgUnitPath(_gam().makeOrgUnitPathRelative(parentPath))
  orgUnits = {}
  while True:
    try:
      result = _gam().callGAPI(cd.orgunits(), 'get',
                throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=parentPath,
                fields='orgUnitId,orgUnitPath,parentOrgUnitId')
      orgUnits[result['orgUnitId']] = result['orgUnitPath']
      if 'parentOrgUnitId' not in result:
        break
      parentPath = result['parentOrgUnitId']
    except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError):
      _gam().entityDoesNotExistExit(Ent.ORGANIZATIONAL_UNIT, parentPath)
    except (GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
      _gam().accessErrorExit(cd)
  return orgUnits

def _getOrgunitsOrgUnitIdPath(cd, orgUnit):
  if orgUnit.startswith('orgunits/'):
    orgUnit = f'id:{orgUnit[9:]}'
  orgUnitPath, orgUnitId = getOrgUnitId(cd, orgUnit)
  return (orgUnitPath, f'orgunits/{orgUnitId[3:]}')
