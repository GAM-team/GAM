"""Group parent hierarchy utilities shared between groups/members and userop/usergroups.

Moved here to break circular dependencies between cmd/ modules.
"""

from gamlib import entity
from gamlib import gapi as GAPI
from gamlib import indent

from gam.util.access import accessErrorExit
from gam.util.api import callGAPIpages
from gam.util.csv_pf import flattenJSON
from gam.util.display import badRequestWarning, printKeyValueListWithCount
from gam.util.domain_filters import _setUserGroupArgs

Ent = entity.GamEntity()
Ind = indent.GamIndent()


def getGroupParents(cd, groupParents, groupEmail, groupName, kwargs):
  groupParents[groupEmail] = {'name': groupName, 'parents': []}
  _setUserGroupArgs(groupEmail, kwargs)
  try:
    entityList = callGAPIpages(cd.groups(), 'list', 'groups',
                               throwReasons=GAPI.GROUP_LIST_USERKEY_THROW_REASONS,
                               retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                               orderBy='email', fields='nextPageToken,groups(email,name)', **kwargs)
    for parentGroup in entityList:
      groupParents[groupEmail]['parents'].append(parentGroup['email'])
      if parentGroup['email'] not in groupParents:
        getGroupParents(cd, groupParents, parentGroup['email'], parentGroup['name'], kwargs)
  except (GAPI.invalidMember, GAPI.invalidInput):
    badRequestWarning(Ent.GROUP, Ent.MEMBER, groupEmail)
  except (GAPI.resourceNotFound, GAPI.domainNotFound, GAPI.forbidden, GAPI.badRequest):
    accessErrorExit(cd)

def showGroupParents(groupParents, groupEmail, role, i, count):
  kvList = [groupEmail, f'{groupParents[groupEmail]["name"]}']
  if role:
    kvList.extend([Ent.Singular(Ent.ROLE), role])
  printKeyValueListWithCount(kvList, i, count)
  Ind.Increment()
  for parentEmail in groupParents[groupEmail]['parents']:
    showGroupParents(groupParents, parentEmail, None, 0, 0)
  Ind.Decrement()

def addJsonGroupParents(groupParents, userGroup, groupEmail):
  userGroup.setdefault('parents', [])
  for parentEmail in groupParents[groupEmail]['parents']:
    userGroup['parents'].append({'email': parentEmail, 'name': groupParents[parentEmail]['name'], 'parents': []})
    addJsonGroupParents(groupParents, userGroup['parents'][-1], parentEmail)

def printGroupParents(groupParents, groupEmail, row, csvPF, delimiter, showParentsAsList):
  if groupParents[groupEmail]['parents']:
    for parentEmail in groupParents[groupEmail]['parents']:
      row['parents'].append({'email': parentEmail, 'name': groupParents[parentEmail]['name']})
      printGroupParents(groupParents, parentEmail, row, csvPF, delimiter, showParentsAsList)
      del row['parents'][-1]
  else:
    if not showParentsAsList:
      csvPF.WriteRowTitles(flattenJSON(row))
    else:
      crow = row.copy()
      if 'Role' in row:
        crow['Role'] = row['Role']
      parents = crow.pop('parents')
      crow['ParentsCount'] = len(parents)
      crow['Parents'] = delimiter.join([parent['email'] for parent in parents])
      crow['ParentsName'] = delimiter.join([parent['name'] for parent in parents])
      csvPF.WriteRow(flattenJSON(crow))
