"""Gmail filter management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re
import json
import sys

from gam.cmd.gmail.labels import _getLabelId, _getLabelName, _getLabelSet, _getUserGmailLabels, buildLabelPath

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

ONE_KILO_10_BYTES = 1000
ONE_MEGA_10_BYTES = 1000 * 1000

def _printFilter(user, userFilter, labels):
  row = {'User': user, 'id': userFilter['id']}
  if 'criteria' in userFilter:
    for item in userFilter['criteria']:
      if item in {'hasAttachment', 'excludeChats'}:
        row[item] = item
      elif item == 'size':
        row[item] = f'size {userFilter["criteria"]["sizeComparison"]} {formatMaxMessageBytes(userFilter["criteria"][item], ONE_KILO_10_BYTES, ONE_MEGA_10_BYTES)}'
      elif item == 'sizeComparison':
        pass
      else:
        row[item] = f'{item} {userFilter["criteria"][item]}'
  else:
    row['error'] = 'NoCriteria'
  if 'action' in userFilter:
    for labelId in userFilter['action'].get('addLabelIds', []):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]
      else:
        row['label'] = f'label {_getLabelName(labels, labelId)}'
    for labelId in userFilter['action'].get('removeLabelIds', []):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        row[FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]] = FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]
    if userFilter['action'].get('forward'):
      row['forward'] = f'forward {userFilter["action"]["forward"]}'
  else:
    row['error'] = 'NoActions'
  return row

def _mapFilterLabelIdsToNames(userFilter, labels):
  # Map user label IDs to label names
  if 'action' in userFilter:
    for field in ['addLabelIds', 'removeLabelIds']:
      if field in userFilter['action']:
        for i, labelId in enumerate(userFilter['action'][field]):
          if labelId not in GMAIL_SYSTEM_LABELS and labelId not in GMAIL_CATEGORY_LABELS:
            userFilter['action'][field][i] = _getLabelName(labels, labelId)

def _showFilter(userFilter, j, jcount, labels, FJQC=None):
  if FJQC is not None and FJQC.formatJSON:
    if labels['labels']:
      _mapFilterLabelIdsToNames(userFilter, labels)
    _getMain().printLine(json.dumps(_getMain().cleanJSON(userFilter), ensure_ascii=False, sort_keys=False))
    return
  _getMain().printEntity([Ent.FILTER, userFilter['id']], j, jcount)
  Ind.Increment()
  _getMain().printEntitiesCount(Ent.CRITERIA, None)
  Ind.Increment()
  if 'criteria' in userFilter:
    for item in sorted(userFilter['criteria']):
      if item in {'hasAttachment', 'excludeChats'}:
        _getMain().printKeyValueList([item])
      elif item == 'size':
        _getMain().printKeyValueList([f'{item} {userFilter["criteria"]["sizeComparison"]} {formatMaxMessageBytes(userFilter["criteria"][item], ONE_KILO_10_BYTES, ONE_MEGA_10_BYTES)}'])
      elif item == 'sizeComparison':
        pass
      else:
        _getMain().printKeyValueList([f'{item} "{userFilter["criteria"][item]}"'])
  else:
    _getMain().printKeyValueList([_getMain().ERROR, Msg.NO_FILTER_CRITERIA.format(Ent.Singular(Ent.FILTER))])
  Ind.Decrement()
  _getMain().printEntitiesCount(Ent.ACTION, None)
  Ind.Increment()
  if 'action' in userFilter:
    for labelId in sorted(userFilter['action'].get('addLabelIds', [])):
      if labelId in FILTER_ADD_LABEL_TO_ARGUMENT_MAP:
        _getMain().printKeyValueList([FILTER_ADD_LABEL_TO_ARGUMENT_MAP[labelId]])
      else:
        _getMain().printKeyValueList([f'label "{_getLabelName(labels, labelId)}"'])
    for labelId in sorted(userFilter['action'].get('removeLabelIds', [])):
      if labelId in FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP:
        _getMain().printKeyValueList([FILTER_REMOVE_LABEL_TO_ARGUMENT_MAP[labelId]])
    Ind.Decrement()
    if userFilter['action'].get('forward'):
      _getMain().printEntity([Ent.FORWARDING_ADDRESS, userFilter['action']['forward']])
  else:
    _getMain().printKeyValueList([_getMain().ERROR, Msg.NO_FILTER_ACTIONS.format(Ent.Singular(Ent.FILTER))])
    Ind.Decrement()
  Ind.Decrement()
#
FILTER_CATEGORY_CHOICE_MAP = {
  'personal': 'CATEGORY_PERSONAL',
  'social': 'CATEGORY_SOCIAL',
  'promotions': 'CATEGORY_PROMOTIONS',
  'updates': 'CATEGORY_UPDATES',
  'forums': 'CATEGORY_FORUMS',
  }
FILTER_CRITERIA_CHOICE_MAP = {
  'excludechats': 'excludeChats',
  'from': 'from',
  'hasattachment': 'hasAttachment',
  'haswords': 'query',
  'musthaveattachment': 'hasAttachment',
  'negatedquery': 'negatedQuery',
  'nowords': 'negatedQuery',
  'query': 'query',
  'size': 'size',
  'subject': 'subject',
  'to': 'to',
  }
FILTER_ADD_LABEL_ACTIONS = ['important', 'star', 'trash']
FILTER_REMOVE_LABEL_ACTIONS = ['markread', 'notimportant', 'archive', 'neverspam']
FILTER_ACTION_CHOICES = FILTER_ADD_LABEL_ACTIONS+FILTER_REMOVE_LABEL_ACTIONS+['category', 'forward', 'label']
FILTER_ACTION_LABEL_MAP = {
  'archive': 'INBOX',
  'important': 'IMPORTANT',
  'markread': 'UNREAD',
  'neverspam': 'SPAM',
  'notimportant': 'IMPORTANT',
  'star': 'STARRED',
  'trash': 'TRASH',
  }

# gam <UserTypeEntity> [create]
#	(filter <FilterCriteria>+ <FilterAction>+) |
#	((json [charset <Charset>] <String>) |
#	 (json file <FileName> [charset <Charset>]))
#	[buildpath [<Boolean>]]
def createFilter(users):
  body = {'criteria': {}, 'action': {'addLabelIds': [], 'removeLabelIds': []}}
  buildPath = False
  jsonData = None
  categorySpecified = labelSpecified = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if jsonData is None and myarg in FILTER_CRITERIA_CHOICE_MAP:
      myarg = FILTER_CRITERIA_CHOICE_MAP[myarg]
      if myarg in {'from', 'to', 'subject', 'query', 'negatedQuery'}:
        body['criteria'][myarg] = _getMain().getString(Cmd.OB_STRING)
      elif myarg in {'hasAttachment', 'excludeChats'}:
        body['criteria'][myarg] = True
      elif myarg == 'size':
        body['criteria']['sizeComparison'] = _getMain().getChoice(['larger', 'smaller'])
        body['criteria'][myarg] = _getMain().getMaxMessageBytes(_getMain().ONE_KILO_10_BYTES, _getMain().ONE_MEGA_10_BYTES)
    elif jsonData is None and myarg in FILTER_ACTION_CHOICES:
      if myarg in FILTER_ADD_LABEL_ACTIONS:
        myarg = FILTER_ACTION_LABEL_MAP[myarg]
        body['action']['addLabelIds'].append(myarg)
        if (myarg == 'IMPORTANT') and (myarg in body['action']['removeLabelIds']):
          body['action']['removeLabelIds'].remove(myarg)
      elif myarg in FILTER_REMOVE_LABEL_ACTIONS:
        myarg = FILTER_ACTION_LABEL_MAP[myarg]
        body['action']['removeLabelIds'].append(myarg)
        if (myarg == 'IMPORTANT') and (myarg in body['action']['addLabelIds']):
          body['action']['addLabelIds'].remove(myarg)
      elif myarg == 'forward':
        body['action']['forward'] = _getMain().getEmailAddress(noUid=True)
      elif myarg == 'label':
        label = _getMain().getString(Cmd.OB_LABEL_NAME)
        labelUpper = label.upper()
        if labelUpper not in GMAIL_SYSTEM_LABELS:
          if labelUpper not in GMAIL_CATEGORY_LABELS:
            if not labelSpecified:
              body['action']['addLabelIds'].append(label)
              labelSpecified = True
            else:
              Cmd.Backup()
              _getMain().usageErrorExit(Msg.FILTER_CAN_ONLY_CONTAIN_ONE_USER_LABEL)
          elif not categorySpecified:
            body['action']['addLabelIds'].append(labelUpper)
            categorySpecified = True
          else:
            Cmd.Backup()
            _getMain().usageErrorExit(Msg.FILTER_CAN_ONLY_CONTAIN_ONE_CATEGORY_LABEL)
        else:
          body['action']['addLabelIds'].append(labelUpper)
          if (labelUpper == 'IMPORTANT') and (labelUpper in body['action']['removeLabelIds']):
            body['action']['removeLabelIds'].remove(labelUpper)
      elif myarg == 'category':
        if not categorySpecified:
          body['action']['addLabelIds'].append(_getMain().getChoice(FILTER_CATEGORY_CHOICE_MAP, mapChoice=True))
          categorySpecified = True
        else:
          Cmd.Backup()
          _getMain().usageErrorExit(Msg.FILTER_CAN_ONLY_CONTAIN_ONE_CATEGORY_LABEL)
      else:
        _getMain().unknownArgumentExit()
    elif myarg == 'json':
      jsonData = _getMain().getJSON([])
      body['criteria'] = jsonData['criteria']
      body['action'] = jsonData['action']
    elif myarg == 'buildpath':
      buildPath = _getMain().getBoolean()
    else:
      _getMain().unknownArgumentExit()
  if not body['criteria']:
    _getMain().missingChoiceExit(FILTER_CRITERIA_CHOICE_MAP)
  if not body['action'].get('addLabelIds') and not body['action'].get('removeLabelIds') and 'forward' not in body['action']:
    _getMain().missingChoiceExit(FILTER_ACTION_CHOICES)
  addLabelIndicies = {}
  for field in ['addLabelIds', 'removeLabelIds']:
    for i, labelId in enumerate(body['action'].get(field, [])):
      if labelId not in GMAIL_SYSTEM_LABELS and labelId not in GMAIL_CATEGORY_LABELS:
        addLabelIndicies.setdefault(labelId, {})
        addLabelIndicies[labelId][field] = i
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if addLabelIndicies:
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
      if not labels:
        continue
      labelSet = _getLabelSet(labels)
    try:
      lcount = len(addLabelIndicies)
      l = 0
      for addLabelName, addLabelData in addLabelIndicies.items():
        l += 1
        retries = 3
        for _ in range(1, retries+1):
          addLabelId = _getLabelId(labels, addLabelName)
          if addLabelId:
            retries = 0
            break
          lbody = {'name': addLabelName}
          if not buildPath:
            try:
              result = _getMain().callGAPI(gmail.users().labels(), 'create',
                                throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.DUPLICATE, GAPI.PERMISSION_DENIED],
                                userId='me', body=lbody, fields='id')
              _getMain().entityActionPerformed([Ent.USER, user, Ent.LABEL, addLabelName], l, lcount)
              addLabelId = result['id']
              labels['labels'].append({'id': result['id'], 'name': addLabelName})
              retries = 0
              break
            except GAPI.duplicate:
              labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
              labelSet = _getLabelSet(labels)
          else:
            buildLabelPath(gmail, user, i, count, lbody, addLabelName, labelSet, l, lcount)
            labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name, type)')
            labelSet = _getLabelSet(labels)
        if retries:
          _getMain().entityActionFailedWarning([Ent.USER, user, Ent.LABEL, addLabelName], Msg.DUPLICATE, i, count)
          continue
        for field in ['addLabelIds', 'removeLabelIds']:
          if field in addLabelData:
            body['action'][field][addLabelData[field]] = addLabelId
      result = _getMain().callGAPI(gmail.users().settings().filters(), 'create',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.INVALID, GAPI.INVALID_ARGUMENT,
                                                               GAPI.FAILED_PRECONDITION, GAPI.PERMISSION_DENIED],
                        userId='me', body=body, fields='id')
      if result:
        _getMain().entityActionPerformed([Ent.USER, user, Ent.FILTER, result['id']], i, count)
    except (GAPI.invalid, GAPI.invalidArgument, GAPI.failedPrecondition, GAPI.permissionDenied) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user, Ent.FILTER, ''], str(e), i, count)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete filter <FilterIDEntity>
def deleteFilters(users):
  filterIdEntity = _getMain().getUserObjectEntity(Cmd.OB_FILTER_ID_ENTITY, Ent.FILTER)
  _getMain().checkForExtraneousArguments()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, filterIds, jcount = _getMain()._validateUserGetObjectList(user, i, count, filterIdEntity)
    if jcount == 0:
      continue
    Ind.Increment()
    j = 0
    for filterId in filterIds:
      j += 1
      try:
        _getMain().callGAPI(gmail.users().settings().filters(), 'delete',
                 throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.PERMISSION_DENIED],
                 userId='me', id=filterId)
        _getMain().entityActionPerformed([Ent.USER, user, Ent.FILTER, filterId], j, jcount)
      except (GAPI.notFound, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.FILTER, filterId], str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> info filters <FilterIDEntity> [labelidsonly] [formatjson]
def infoFilters(users):
  labelIdsOnly = False
  filterIdEntity = _getMain().getUserObjectEntity(Cmd.OB_FILTER_ID_ENTITY, Ent.FILTER)
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'labelidsonly':
      labelIdsOnly = True
    else:
      FJQC.GetFormatJSON(myarg)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, filterIds, jcount = _getMain()._validateUserGetObjectList(user, i, count, filterIdEntity,
                                                                showAction=FJQC is None or not FJQC.formatJSON)
    if jcount == 0:
      continue
    if not labelIdsOnly:
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name)')
      if not labels:
        continue
    else:
      labels = {'labels': []}
    Ind.Increment()
    j = 0
    for filterId in filterIds:
      j += 1
      try:
        result = _getMain().callGAPI(gmail.users().settings().filters(), 'get',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND],
                          userId='me', id=filterId)
        if not FJQC.formatJSON:
          _getMain().printEntityKVList([Ent.USER, user],
                            [Ent.Singular(Ent.FILTER), result['id']],
                            i, count)
        Ind.Increment()
        _showFilter(result, j, jcount, labels, FJQC)
        Ind.Decrement()
      except GAPI.notFound as e:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.FILTER, filterId], str(e), j, jcount)
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> print filters [labelidsonly] [todrive <ToDriveAttribute>*]
#	[formatjson] [quotechar <Character>]
# gam <UserTypeEntity> show filters [labelidsonly] [formatjson]
def printShowFilters(users):
  labelIdsOnly = False
  csvPF = _getMain().CSVPrintFile(['User', 'id']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'labelidsonly':
      labelIdsOnly = True
    else:
      FJQC.GetFormatJSONQuoteChar(myarg)
  if csvPF:
    csvPF.SetFormatJSON(False)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if not labelIdsOnly:
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name)')
      if not labels:
        continue
    else:
      labels = {'labels': []}
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.FILTER, user, i, count)
    try:
      results = _getMain().callGAPIitems(gmail.users().settings().filters(), 'list', 'filter',
                              throwReasons=GAPI.GMAIL_THROW_REASONS,
                              userId='me')
      if not csvPF:
        jcount = len(results)
        if not FJQC.formatJSON:
          _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.FILTER, i, count)
        Ind.Increment()
        j = 0
        for userFilter in results:
          j += 1
          _showFilter(userFilter, j, jcount, labels, FJQC)
        Ind.Decrement()
      elif results:
        for userFilter in results:
          row = _printFilter(user, userFilter, labels)
          if FJQC.formatJSON:
            if labels['labels']:
              _mapFilterLabelIdsToNames(userFilter, labels)
            row['JSON'] = json.dumps(userFilter, ensure_ascii=False, sort_keys=False)
          csvPF.WriteRowTitles(row)
      elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
        csvPF.WriteRowNoFilter({'User': user})
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.SetFormatJSON(False)
    csvPF.SetSortTitles(['User', 'id', 'from', 'to', 'subject', 'query', 'negatedQuery', 'hasAttachment', 'excludeChats', 'size', 'forward',
                         'archive', 'important', 'label', 'markread', 'star'])
    csvPF.SortTitles()
    if FJQC.formatJSON:
      csvPF.MoveTitlesToEnd(['JSON'])
    csvPF.SetSortTitles([])
    csvPF.writeCSVfile('Filters')

