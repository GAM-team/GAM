"""Gmail label management.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re

from gam.util.csv_pf import RI_ENTITY, RI_J, RI_JCOUNT, RI_ITEM

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg
from gam.util.api import buildGAPIServiceObject, callGAPI, callGAPIpages, checkGAPIError
from gam.util.args import (
    LABEL_BACKGROUND_COLORS,
    LABEL_TEXT_COLORS,
    checkForExtraneousArguments,
    formatHTTPError,
    getArgument,
    getBoolean,
    getChoice,
    getLabelColor,
    getString,
    getStringReturnInList,
    validateREPattern,
    validateREPatternSubstitution,
)
from gam.util.csv_pf import CSVPrintFile, batchRequestID, flattenJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityListDoesNotExistWarning,
    entityModifierNewValueActionPerformed,
    entityPerformActionModifierNewValue,
    entityPerformActionNumItems,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    printGettingEntityItemForWhom,
    printKeyValueList,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument, getEntityList
from gam.util.errors import missingArgumentExit, unknownArgumentExit, usageErrorExit
from gam.util.output import executeBatch, setSysExitRC
from gam.constants import NO_ENTITIES_FOUND_RC

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _getUserGmailLabels(gmail, user, i, count, fields):
  try:
    labels = callGAPI(gmail.users().labels(), 'list',
                      throwReasons=GAPI.GMAIL_THROW_REASONS,
                      userId='me', fields=fields)
    if not labels:
      labels = {'labels': []}
    return labels
  except GAPI.serviceNotAvailable:
    userGmailServiceNotEnabledWarning(user, i, count)
    return None

def _getLabelId(labels, labelName):
  for label in labels['labels']:
    if (labelName.upper() == label['id']) or (labelName.lower() in {label['id'].lower(), label['name'].lower()}):
      return label['id']
  return None

def _getLabelName(labels, labelId):
  for label in labels['labels']:
    if label['id'] == labelId:
      return label['name']
  return labelId

def _getLabelSet(labels):
  labelSet = {}
  for ulabel in labels['labels']:
    if ulabel['type'] != LABEL_TYPE_SYSTEM:
      labelSet[ulabel['name']] = ulabel['id']
  return labelSet

LABEL_LABEL_LIST_VISIBILITY_CHOICE_MAP = {
  'hide': 'labelHide',
  'show': 'labelShow',
  'showifunread': 'labelShowIfUnread',
  }
LABEL_MESSAGE_LIST_VISIBILITY_CHOICES = ['hide', 'show']
LABEL_TYPE_SYSTEM = 'system'
LABEL_TYPE_USER = 'user'

def getLabelAttributes(myarg, body):
  if myarg == 'labellistvisibility':
    body['labelListVisibility'] = getChoice(LABEL_LABEL_LIST_VISIBILITY_CHOICE_MAP, mapChoice=True)
  elif myarg == 'messagelistvisibility':
    body['messageListVisibility'] = getChoice(LABEL_MESSAGE_LIST_VISIBILITY_CHOICES)
  elif myarg in {'backgroundcolor', 'backgroundcolour'}:
    body.setdefault('color', {})
    body['color']['backgroundColor'] = getLabelColor(LABEL_BACKGROUND_COLORS)
  elif myarg in {'textcolor', 'textcolour'}:
    body.setdefault('color', {})
    body['color']['textColor'] = getLabelColor(LABEL_TEXT_COLORS)
  else:
    unknownArgumentExit()

def checkLabelColor(body):
  if 'color' not in body:
    return
  if 'backgroundColor' in body['color']:
    if 'textColor' in body['color']:
      return
    missingArgumentExit('textcolor <LabelColorHex>')
  missingArgumentExit('backgroundcolor <LabelColorHex>')

def buildLabelPath(gmail, user, i, count, body, label, labelSet, l=0, lcount=0):
  label = label.strip('/')
  if label in labelSet:
    entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label], Msg.DUPLICATE, l, lcount)
    return
  labelParts = label.split('/')
  invalid = False
  for j, labelPart in enumerate(labelParts):
    labelParts[j] = labelPart.strip()
    if not labelParts[j]:
      entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label], Msg.INVALID, l, lcount)
      invalid = True
      break
  if invalid:
    return
  decrement = False
  duplicate = True
  labelPath = ''
  j = 0
  for k, labelPart in enumerate(labelParts):
    if labelPath != '':
      labelPath += '/'
    labelPath += labelPart
    if labelPath not in labelSet:
      if duplicate:
        jcount = len(labelParts)-k
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.LABEL, i, count)
        Ind.Increment()
        decrement = True
        duplicate = False
      j += 1
      body['name'] = labelPath
      try:
        newLabel = callGAPI(gmail.users().labels(), 'create',
                            throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.DUPLICATE],
                            userId='me', body=body, fields='id,name')
        labelSet[newLabel['name']] = newLabel['id']
        entityActionPerformed([Ent.USER, user, Ent.LABEL, labelPath], j, jcount)
      except GAPI.duplicate:
        entityActionFailedWarning([Ent.USER, user, Ent.LABEL, labelPath], Msg.DUPLICATE, j, jcount)
        break
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
        break
  if duplicate:
    entityActionFailedWarning([Ent.USER, user, Ent.LABEL, labelPath], Msg.DUPLICATE, l, lcount)
  if decrement:
    Ind.Decrement()

def createLabels(users, labelEntity):
  body = {}
  buildPath = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'buildpath':
      buildPath = getBoolean()
    else:
      getLabelAttributes(myarg, body)
  checkLabelColor(body)
  if not isinstance(labelEntity, dict):
    userLabelList = None
    labelList = labelEntity
  else:
    userLabelList = labelEntity
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if userLabelList:
      labelList = userLabelList[origUser]
    lcount = len(labelList)
    if buildPath:
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
      if not labels:
        continue
      labelSet = _getLabelSet(labels)
    entityPerformActionNumItems([Ent.USER, user], lcount, Ent.LABEL, i, count)
    Ind.Increment()
    l = 0
    for label in labelList:
      l += 1
      body['name'] = label
      if not buildPath:
        try:
          callGAPI(gmail.users().labels(), 'create',
                   throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.DUPLICATE, GAPI.INVALID, GAPI.PERMISSION_DENIED],
                   userId='me', body=body, fields='')
          entityActionPerformed([Ent.USER, user, Ent.LABEL, label], l, lcount)
        except GAPI.duplicate:
          entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label], Msg.DUPLICATE, l, lcount)
        except (GAPI.invalid, GAPI.permissionDenied) as e:
          entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label], str(e), l, lcount)
        except GAPI.serviceNotAvailable:
          userGmailServiceNotEnabledWarning(user, i, count)
      else:
        buildLabelPath(gmail, user, i, count, body, label, labelSet, l, lcount)
    Ind.Decrement()

# gam <UserTypeEntity> [create] label|labels <String>
#	[messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
#	[backgroundcolor <LabelColorHex>] [textcolor <LabelColorHex>]
#	[buildpath [<Boolean>]]
def createLabel(users):
  createLabels(users, getStringReturnInList(Cmd.OB_LABEL_NAME))

# gam <UserTypeEntity> create labellist <LabelNameEntity>
#	[messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
#	[backgroundcolor <LabelColorHex>] [textcolor <LabelColorHex>]
#	[buildpath [<Boolean>]]
def createLabelList(users):
  createLabels(users, getEntityList(Cmd.OB_LABEL_NAME_LIST, shlexSplit=True))

# gam <UserTypeEntity> update labelsettings <LabelName> [name <String>]
#	[messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
#	[backgroundcolor <LabelColorHex>] [textcolor <LabelColorHex>]
def updateLabelSettings(users):
  label_name = getString(Cmd.OB_LABEL_NAME)
  label_name_lower = label_name.lower()
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      body['name'] = getString(Cmd.OB_STRING)
    else:
      getLabelAttributes(myarg, body)
  checkLabelColor(body)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name)')
    if not labels:
      continue
    try:
      for label in labels['labels']:
        if label['name'].lower() == label_name_lower:
          result = callGAPI(gmail.users().labels(), 'patch',
                            throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT],
                            userId='me', id=label['id'], body=body, fields='name')
          entityActionPerformed([Ent.USER, user, Ent.LABEL, result['name']], i, count)
          break
      else:
        entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label_name], Msg.DOES_NOT_EXIST, i, count)
    except (GAPI.notFound, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label_name], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> update labelid <LabelID> [name <String>]
#	[messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
#	[backgroundcolor <LabelColorHex>] [textcolor <LabelColorHex>]
def updateLabelSettingsById(users):
  labelId = getString(Cmd.OB_LABEL_ID)
  body = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'name':
      body['name'] = getString(Cmd.OB_STRING)
    else:
      getLabelAttributes(myarg, body)
  checkLabelColor(body)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      result = callGAPI(gmail.users().labels(), 'patch',
                        throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT],
                        userId='me', id=labelId, body=body, fields='name')
      entityActionPerformed([Ent.USER, user, Ent.LABEL_ID, labelId, Ent.LABEL, result['name']], i, count)
    except (GAPI.notFound, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user, Ent.LABEL_ID, labelId], str(e), i, count)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
#
def cleanLabelQuery(labelQuery):
  for ch in '/ (){}':
    labelQuery = labelQuery.replace(ch, '-')
  return labelQuery.lower()

# gam <UserTypeEntity> update label|labels
#	[search <REMatchPattern>] [replace <RESubstitution>] [merge [keepoldlabel]]
#	search defaults to '^Inbox/(.*)$' which will find all labels in the Inbox
#	replace defaults to '%s'
def updateLabels(users):
  search = '^Inbox/(.*)$'
  pattern = re.compile(search, re.IGNORECASE)
  replace = '%s'
  keepOldLabel = merge = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'search':
      search = getString(Cmd.OB_RE_PATTERN)
      pattern = validateREPattern(search, re.IGNORECASE)
    elif myarg == 'replace':
      replaceLocation = Cmd.Location()
      replace = getString(Cmd.OB_RE_SUBSTITUTION)
    elif myarg == 'merge':
      merge = True
    elif myarg == 'keepoldlabel':
      keepOldLabel = True
    else:
      unknownArgumentExit()
# Validate that number of substitions in replace matches the number of groups in pattern
  useRegexSub = replace.find('%s') == -1
  if useRegexSub:
    Cmd.SetLocation(replaceLocation)
    validateREPatternSubstitution(pattern, replace)
  else:
    if pattern.groups != replace.count('%s'):
      Cmd.SetLocation(replaceLocation)
      usageErrorExit(Msg.MISMATCH_SEARCH_REPLACE_SUBFIELDS.format(pattern.groups, search, replace.count('%s'), replace))
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
    if not labels:
      continue
    try:
      labelMatches = 0
      for label in sorted(labels['labels'], key=lambda k: k['name'], reverse=True):
        if label['type'] == LABEL_TYPE_SYSTEM:
          continue
        match_result = pattern.match(label['name'])
        if match_result is not None:
          labelMatches += 1
          if useRegexSub:
            newLabelName = pattern.sub(replace, label['name'])
          else:
            newLabelName = replace % match_result.groups()
          newLabelNameLower = newLabelName.lower()
          try:
            Act.Set(Act.RENAME)
            callGAPI(gmail.users().labels(), 'patch',
                     throwReasons=[GAPI.ABORTED, GAPI.DUPLICATE],
                     userId='me', id=label['id'], body={'name': newLabelName}, fields='')
            entityModifierNewValueActionPerformed([Ent.USER, user, Ent.LABEL, label['name']], Act.MODIFIER_TO, newLabelName, i, count)
          except (GAPI.aborted, GAPI.duplicate):
            if merge:
              Act.Set(Act.MERGE)
              entityPerformActionModifierNewValue([Ent.USER, user, Ent.LABEL, label['name']], Act.MODIFIER_WITH, newLabelName, i, count)
              messagesToRelabel = callGAPIpages(gmail.users().messages(), 'list', 'messages',
                                                userId='me', q=f'label:{cleanLabelQuery(label["name"])}')
              Act.Set(Act.RELABEL)
              jcount = len(messagesToRelabel)
              Ind.Increment()
              if jcount > 0:
                for new_label in labels['labels']:
                  if new_label['name'].lower() == newLabelNameLower:
                    body = {'addLabelIds': [new_label['id']]}
                    break
                j = 0
                for message in messagesToRelabel:
                  j += 1
                  callGAPI(gmail.users().messages(), 'modify',
                           userId='me', id=message['id'], body=body, fields='')
                  entityActionPerformed([Ent.USER, user, Ent.MESSAGE, message['id']], j, jcount)
              else:
                printEntityKVList([Ent.USER, user],
                                  [Msg.NO_MESSAGES_WITH_LABEL, label['name']],
                                  i, count)
              Ind.Decrement()
              if not keepOldLabel:
                callGAPI(gmail.users().labels(), 'delete',
                         userId='me', id=label['id'])
                Act.Set(Act.DELETE)
                entityActionPerformed([Ent.USER, user, Ent.LABEL, label['name']], i, count)
            else:
              entityActionNotPerformedWarning([Ent.USER, user, Ent.LABEL, newLabelName], Msg.ALREADY_EXISTS_USE_MERGE_ARGUMENT, i, count)
      if labels and (labelMatches == 0):
        printEntityKVList([Ent.USER, user],
                          [Msg.NO_LABELS_MATCH, search],
                          i, count)
    except (GAPI.serviceNotAvailable, GAPI.badRequest):
      userGmailServiceNotEnabledWarning(user, i, count)

def _validateLabelList(user, i, count, labels, labelList, userOnly):
  validLabels = []
  for label in labelList:
    label_name_lower = label.lower()
    if label_name_lower[:6] == 'regex:':
      labelPattern = validateREPattern(label[6:])
    else:
      labelPattern = None
    if label.upper() == '--ALL_LABELS--':
      count = len(labels['labels'])
      for delLabel in sorted(labels['labels'], key=lambda k: k['name'], reverse=True):
        if (not userOnly or delLabel['type'] != LABEL_TYPE_SYSTEM):
          validLabels.append(delLabel)
    elif labelPattern:
      for delLabel in sorted(labels['labels'], key=lambda k: k['name'], reverse=True):
        if (not userOnly or delLabel['type'] != LABEL_TYPE_SYSTEM) and labelPattern.match(delLabel['name']):
          validLabels.append(delLabel)
    else:
      for delLabel in sorted(labels['labels'], key=lambda k: k['name'], reverse=True):
        if (not userOnly or delLabel['type'] != LABEL_TYPE_SYSTEM) and label_name_lower == delLabel['name'].lower():
          validLabels.append(delLabel)
          break
      else:
        entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label], Msg.DOES_NOT_EXIST, i, count)
  return (validLabels, len(validLabels))

def deleteLabels(users, labelEntity):
  def _handleProcessGmailError(exception, ri):
    http_status, reason, message = checkGAPIError(exception)
    entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], Ent.LABEL, labelIdToNameMap[ri[RI_ITEM]]], formatHTTPError(http_status, reason, message), int(ri[RI_J]), int(ri[RI_JCOUNT]))

  def _callbackDeleteLabel(request_id, _, exception):
    ri = request_id.splitlines()
    if exception is None:
      entityActionPerformed([Ent.USER, ri[RI_ENTITY], Ent.LABEL, labelIdToNameMap[ri[RI_ITEM]]], int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleProcessGmailError(exception, ri)

  if not isinstance(labelEntity, dict):
    userLabelList = None
    labelList = labelEntity
  else:
    userLabelList = labelEntity
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if userLabelList:
      labelList = userLabelList[origUser]
    try:
      printGettingAllEntityItemsForWhom(Ent.LABEL, user, i, count)
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
      if not labels:
        continue
      delLabels, jcount = _validateLabelList(user, i, count, labels, labelList, True)
      labelIdToNameMap = {}
      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.LABEL, i, count)
      if jcount == 0:
        continue
      Ind.Increment()
      svcargs = dict([('userId', 'me'), ('id', None), ('fields', '')]+GM.Globals[GM.EXTRA_ARGS_LIST])
      method = getattr(gmail.users().labels(), 'delete')
      dbatch = gmail.new_batch_http_request(callback=_callbackDeleteLabel)
      bcount = 0
      j = 0
      for del_me in delLabels:
        j += 1
        svcparms = svcargs.copy()
        svcparms['id'] = del_me['id']
        labelIdToNameMap[del_me['id']] = del_me['name']
        dbatch.add(method(**svcparms), request_id=batchRequestID(user, i, count, j, jcount, del_me['id']))
        bcount += 1
        if bcount == 10:
          executeBatch(dbatch)
          dbatch = gmail.new_batch_http_request(callback=_callbackDeleteLabel)
          bcount = 0
      if bcount > 0:
        dbatch.execute()
      Ind.Decrement()
    except (GAPI.serviceNotAvailable, GAPI.badRequest):
      userGmailServiceNotEnabledWarning(user, i, count)

# gam <UserTypeEntity> delete label|labels <LabelName>|regex:<REMatchPattern>
def deleteLabel(users):
  deleteLabels(users, getStringReturnInList(Cmd.OB_LABEL_NAME))

# gam <UserTypeEntity> delete labellist <LabelNameEntity>
def deleteLabelList(users):
  deleteLabels(users, getEntityList(Cmd.OB_LABEL_NAME_LIST, shlexSplit=True))

def deleteLabelIds(users, labelEntity):
  if not isinstance(labelEntity, dict):
    userLabelList = None
    labelList = labelEntity
  else:
    userLabelList = labelEntity
  checkForExtraneousArguments()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if userLabelList:
      labelList = userLabelList[origUser]
    lcount = len(labelList)
    entityPerformActionNumItems([Ent.USER, user], lcount, Ent.LABEL, i, count)
    Ind.Increment()
    l = 0
    for labelId in labelList:
      l += 1
      try:
        callGAPI(gmail.users().labels(), 'delete',
                 throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID,
                                                        GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                 userId='me', id=labelId)
        entityActionPerformed([Ent.USER, user, Ent.LABEL_ID, labelId], l, lcount)
      except (GAPI.notFound, GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
        entityActionFailedWarning([Ent.USER, user, Ent.LABEL_ID, labelId], str(e), l, lcount)
      except GAPI.serviceNotAvailable:
        userGmailServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

# gam <UserTypeEntity> delete labelid <LabelID>
def deleteLabelId(users):
  deleteLabelIds(users, getStringReturnInList(Cmd.OB_LABEL_ID))

# gam <UserTypeEntity> delete labelidlist <LabelIDEntity>
def deleteLabelIdList(users):
  deleteLabelIds(users, getEntityList(Cmd.OB_LABEL_ID_LIST))

PRINT_LABELS_TITLES = ['User', 'type', 'name', 'id']
SHOW_LABELS_DISPLAY_CHOICES = ['allfields', 'basename', 'fullname']
LABEL_DISPLAY_FIELDS_LIST = ['type', 'id', 'labelListVisibility', 'messageListVisibility', 'color']
LABEL_COUNTS_FIELDS_LIST = ['messagesTotal', 'messagesUnread', 'threadsTotal', 'threadsUnread']
LABEL_COUNTS_FIELDS = ','.join(LABEL_COUNTS_FIELDS_LIST)

# gam <UserTypeEntity> print labels|label [todrive <ToDriveAttribute>*]
#	[onlyuser|useronly [<Boolean>]] [showcounts [<Boolean>]]
#	[labellist <LabelNameEntity>]
# gam <UserTypeEntity> show labels|label
#	[onlyuser|useronly [<Boolean>]] [showcounts [<Boolean>]]
#	[nested [<Boolean>]] [display allfields|basename|fullname]
#	[labellist <LabelNameEntity>]
def printShowLabels(users):
  def _buildLabelTree(labels):
    def _checkChildLabel(label):
      labelItemList = label.split('/')
      i = len(labelItemList)-1
      while i > 0:
        parent = '/'.join(labelItemList[:i])
        base = '/'.join(labelItemList[i:])
        if parent in labelTree:
          if label in labelTree:
            labelTree[label]['info']['base'] = base
            labelTree[parent]['children'].append(labelTree.pop(label))
          _checkChildLabel(parent)
          return
        i -= 1

    labelTree = {}
    for label in labels['labels']:
      if not onlyUser or (label['type'] != LABEL_TYPE_SYSTEM):
        label['base'] = label['name']
        labelTree[label['name']] = {'info': label, 'children': []}
    labelList = sorted(list(labelTree), reverse=True)
    for label in labelList:
      _checkChildLabel(label)
    return labelTree

  def _printLabel(label):
    if not displayAllFields:
      if not showCounts:
        printKeyValueList([label[nameField]])
      else:
        counts = callGAPI(gmail.users().labels(), 'get',
                          throwReasons=GAPI.GMAIL_THROW_REASONS,
                          userId='me', id=label['id'],
                          fields=LABEL_COUNTS_FIELDS)
        kvlist = [label[nameField], 'Counts']
        for a_key in LABEL_COUNTS_FIELDS_LIST:
          kvlist.extend([a_key, counts[a_key]])
        printKeyValueList(kvlist)
    else:
      printKeyValueList([label[nameField]])
      Ind.Increment()
      for a_key in LABEL_DISPLAY_FIELDS_LIST:
        if a_key in label:
          if a_key != 'color':
            printKeyValueList([a_key, label[a_key]])
          else:
            printKeyValueList(['backgroundColor', label[a_key]['backgroundColor']])
            printKeyValueList(['textColor', label[a_key]['textColor']])
      if showCounts:
        counts = callGAPI(gmail.users().labels(), 'get',
                          throwReasons=GAPI.GMAIL_THROW_REASONS,
                          userId='me', id=label['id'],
                          fields=LABEL_COUNTS_FIELDS)
        for a_key in LABEL_COUNTS_FIELDS_LIST:
          printKeyValueList([a_key, counts[a_key]])
      Ind.Decrement()

  def _printFlatLabel(label):
    _printLabel(label['info'])
    if label['children']:
      for child in sorted(label['children'], key=lambda k: k['info']['name']):
        _printFlatLabel(child)

  def _printNestedLabel(label):
    _printLabel(label['info'])
    if label['children']:
      Ind.Increment()
      if displayAllFields:
        printKeyValueList(['nested', len(label['children'])])
        Ind.Increment()
        for child in sorted(label['children'], key=lambda k: k['info']['name']):
          _printNestedLabel(child)
        Ind.Decrement()
      else:
        for child in sorted(label['children'], key=lambda k: k['info']['name']):
          _printNestedLabel(child)
      Ind.Decrement()

  csvPF = CSVPrintFile(PRINT_LABELS_TITLES, 'sortall') if Act.csvFormat() else None
  onlyUser = showCounts = showNested = False
  displayAllFields = True
  nameField = 'name'
  labelEntity = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in {'onlyuser', 'useronly'}:
      onlyUser = getBoolean()
    elif myarg == 'showcounts':
      showCounts = getBoolean()
    elif not csvPF and myarg == 'nested':
      showNested = getBoolean()
    elif not csvPF and myarg == 'display':
      fields = getChoice(SHOW_LABELS_DISPLAY_CHOICES)
      nameField = 'name' if fields != 'basename' else 'base'
      displayAllFields = fields == 'allfields'
    elif myarg == 'labellist':
      labelEntity = getEntityList(Cmd.OB_LABEL_NAME_LIST, shlexSplit=True)
    else:
      unknownArgumentExit()
  if not isinstance(labelEntity, dict):
    userLabelList = None
    labelList = labelEntity
  else:
    userLabelList = labelEntity
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    origUser = user
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if userLabelList:
      labelList = userLabelList[origUser]
    if csvPF:
      printGettingEntityItemForWhom(Ent.LABEL, user, i, count)
    labels = _getUserGmailLabels(gmail, user, i, count, 'labels')
    if not labels:
      continue
    if not labelList:
      jcount = len(labels['labels'])
      if (jcount > 0) and onlyUser:
        for label in labels['labels']:
          if label['type'] == LABEL_TYPE_SYSTEM:
            jcount -= 1
    else:
      labels['labels'], jcount = _validateLabelList(user, i, count, labels, labelList, onlyUser)
    try:
      if not csvPF:
        entityPerformActionNumItems([Ent.USER, user], jcount, Ent.LABEL, i, count)
      if jcount == 0:
        setSysExitRC(NO_ENTITIES_FOUND_RC)
        continue
      if not csvPF:
        labelTree = _buildLabelTree(labels)
        Ind.Increment()
        if not showNested:
          for label, _ in sorted(labelTree.items(), key=lambda k: (k[1]['info']['type'], k[1]['info']['name'])):
            _printFlatLabel(labelTree[label])
        else:
          for label, _ in sorted(labelTree.items(), key=lambda k: (k[1]['info']['type'], k[1]['info']['name'])):
            _printNestedLabel(labelTree[label])
        Ind.Decrement()
      else:
        for label in sorted(labels['labels'], key=lambda k: (k['type'], k['name'])):
          if not onlyUser or label['type'] != LABEL_TYPE_SYSTEM:
            if showCounts:
              counts = callGAPI(gmail.users().labels(), 'get',
                                throwReasons=GAPI.GMAIL_THROW_REASONS,
                                userId='me', id=label['id'],
                                fields=LABEL_COUNTS_FIELDS)
              for a_key in LABEL_COUNTS_FIELDS_LIST:
                label[a_key] = counts[a_key]
            csvPF.WriteRowTitles(flattenJSON(label, flattened={'User': user}))
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Labels')

GMAIL_SYSTEM_LABELS = {
  'CHAT': 'CHAT',
  'DRAFT': 'DRAFT',
  'IMPORTANT': 'IMPORTANT',
  'INBOX': 'INBOX',
  'SENT': 'SENT',
  'SPAM': 'SPAM',
  'STARRED': 'STARRED',
  'TRASH': 'TRASH',
  'UNREAD': 'UNREAD',
  }
GMAIL_CATEGORY_LABELS = {
  'CATEGORY_PERSONAL': 'CATEGORY_PERSONAL',
  'CATEGORY_SOCIAL': 'CATEGORY_SOCIAL',
  'CATEGORY_PROMOTIONS': 'CATEGORY_PROMOTIONS',
  'CATEGORY_UPDATES': 'CATEGORY_UPDATES',
  'CATEGORY_FORUMS': 'CATEGORY_FORUMS',
  }

def _initLabelNameMap(userGmailLabels):
  labelNameMap = {}
  labelNameMap.update(GMAIL_SYSTEM_LABELS)
  labelNameMap.update(GMAIL_CATEGORY_LABELS)
  for label in userGmailLabels['labels']:
    if label['type'] == 'system':
      labelNameMap[label['id']] = label['id']
    else:
      labelNameMap[label['name']] = labelNameMap[label['name'].upper()] = label['id']
  return labelNameMap

def _convertLabelNamesToIds(gmail, user, i, count, bodyLabels, labelNameMap, addLabel):
  labelIds = []
  for label in bodyLabels:
    if label in labelNameMap:
      labelIds.append(labelNameMap[label])
      continue
    if label.upper() in labelNameMap:
      labelIds.append(labelNameMap[label.upper()])
      continue
    if not addLabel:
      entityListDoesNotExistWarning([Ent.USER, user, Ent.LABEL, label], i, count)
      continue
    try:
      results = callGAPI(gmail.users().labels(), 'create',
                         throwReasons=[GAPI.INVALID],
                         userId='me', body={'labelListVisibility': 'labelShow', 'messageListVisibility': 'show', 'name': label}, fields='id')
    except GAPI.invalid as e:
      action = Act.Get()
      Act.Set(Act.CREATE)
      entityActionFailedWarning([Ent.USER, user, Ent.LABEL, label], str(e), i, count)
      Act.Set(action)
      continue
    labelNameMap[label] = labelNameMap[label.upper()] = results['id']
    labelIds.append(results['id'])
    if label.find('/') != -1:
      # make sure to create parent labels for proper nesting
      parent_label = label[:label.rfind('/')]
      while True:
        if (not parent_label in labelNameMap) and (not parent_label.upper() in labelNameMap):
          result = callGAPI(gmail.users().labels(), 'create',
                            userId='me', body={'name': parent_label}, fields='id')
          labelNameMap[parent_label] = labelNameMap[parent_label.upper()] = result['id']
        if parent_label.find('/') == -1:
          break
        parent_label = parent_label[:parent_label.rfind('/')]
  return labelIds

MESSAGES_MAX_TO_KEYWORDS = {
  Act.ARCHIVE: 'maxtoarchive',
  Act.DELETE: 'maxtodelete',
  Act.EXPORT: 'maxtoexport',
  Act.FORWARD: 'maxtoforward',
  Act.MODIFY: 'maxtomodify',
  Act.PRINT: 'maxtoprint',
  Act.SHOW: 'maxtoshow',
  Act.SPAM: 'maxtospam',
  Act.TRASH: 'maxtotrash',
  Act.UNTRASH: 'maxtountrash',
  }

