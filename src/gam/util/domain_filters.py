"""Domain/query filter utilities shared between aliases, groups, and users.

Moved here to break circular dependencies between cmd/ modules.
"""

from gamlib import glcfg as GC
from gamlib import glclargs

from gam.util.entity import getEntityList, getQueries

Cmd = glclargs.GamCLArgs()


def initUserGroupDomainQueryFilters():
  if not GC.Values[GC.PRINT_AGU_DOMAINS]:
    return {'list': [{'customer': GC.Values[GC.CUSTOMER_ID]}], 'queries': [None]}
  return {'list': [{'domain': domain.lower()} for domain in GC.Values[GC.PRINT_AGU_DOMAINS].replace(',', ' ').split()], 'queries': [None]}

def getUserGroupDomainQueryFilters(myarg, kwargsDict):
  if myarg in {'domain', 'domains'}:
    kwargsDict['list'] = [{'domain': domain.lower()} for domain in getEntityList(Cmd.OB_DOMAIN_NAME_ENTITY)]
  elif myarg in {'query', 'queries'}:
    kwargsDict['queries'] = getQueries(myarg)
  else:
    return False
  return True

def makeUserGroupDomainQueryFilters(kwargsDict, isSuspended, isArchived, isDisabled):
  def addToQuery(query, keyword, value):
    pquery = query
    if not pquery:
      pquery = ''
    else:
      pquery += ' '
    pquery += f'{keyword}={value}'
    kwargsQueries.append((kwargs, pquery))

  kwargsQueries = []
  for kwargs in kwargsDict['list']:
    for query in kwargsDict['queries']:
      if isDisabled is not None:
        addToQuery(query, 'isArchived', isDisabled)
        addToQuery(query, 'isSuspended', isDisabled)
      elif isSuspended is not None or isArchived is not None:
        if isArchived is not None:
          addToQuery(query, 'isArchived', isArchived)
        if isSuspended is not None:
          addToQuery(query, 'isSuspended', isSuspended)
      else:
        kwargsQueries.append((kwargs, query))
  return kwargsQueries

def groupFilters(kwargs, query):
  queryTitle = ''
  if kwargs.get('domain'):
    queryTitle += f'domain={kwargs["domain"]}, '
  if query is not None:
    queryTitle += f'query="{query}", '
  if queryTitle:
    return query, queryTitle[:-2]
  return query, queryTitle

def _setUserGroupArgs(user, kwargs):
  if 'customer' in kwargs:
    if "'" not in user:
      kwargs['query'] = f'memberKey={user}'
    else:
      quser = user.replace("'", "\\\\'")
      kwargs['query'] = f'memberKey={quser}'
  else:
    kwargs['userKey'] = user
