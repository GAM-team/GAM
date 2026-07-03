"""GAM email sending and tag replacement utilities."""

import sys
import time

import re

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

from email.utils import formatdate

def _substituteForUser(field, user, userName):
  if field.find('#') == -1:
    return field
  return field.replace('#user#', user).replace('#email#', user).replace('#username#', userName)

# Tag utilities
TAG_ADDRESS_ARGUMENT_TO_FIELD_MAP = {
  'country': 'country',
  'countrycode': 'countryCode',
  'customtype': 'customType',
  'extendedaddress': 'extendedAddress',
  'formatted': 'formatted',
  'locality': 'locality',
  'pobox': 'poBox',
  'postalcode': 'postalCode',
  'primary': 'primary',
  'region': 'region',
  'streetaddress': 'streetAddress',
  'type': 'type',
  }

TAG_EMAIL_ARGUMENT_TO_FIELD_MAP = {
  'domain': 'domain',
  'primaryemail': 'primaryEmail',
  'username': 'username',
  }

TAG_EXTERNALID_ARGUMENT_TO_FIELD_MAP = {
  'customtype': 'customType',
  'type': 'type',
  'value': 'value',
  }

TAG_GENDER_ARGUMENT_TO_FIELD_MAP = {
  'addressmeas': 'addressMeAs',
  'customgender': 'customGender',
  'type': 'type',
  }

TAG_IM_ARGUMENT_TO_FIELD_MAP = {
  'customprotocol': 'customProtocol',
  'customtype': 'customType',
  'im': 'im',
  'protocol': 'protocol',
  'primary': 'primary',
  'type': 'type',
  }

TAG_KEYWORD_ARGUMENT_TO_FIELD_MAP = {
  'customtype': 'customType',
  'type': 'type',
  'value': 'value',
  }

TAG_LOCATION_ARGUMENT_TO_FIELD_MAP = {
  'area': 'area',
  'buildingid': 'buildingId',
  'buildingname': 'buildingName',
  'customtype': 'customType',
  'deskcode': 'deskCode',
  'floorname': 'floorName',
  'floorsection': 'floorSection',
  'type': 'type',
  }

TAG_NAME_ARGUMENT_TO_FIELD_MAP = {
  'familyname': 'familyName',
  'fullname': 'fullName',
  'givenname': 'givenName',
  }

TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP = {
  'costcenter': 'costCenter',
  'costcentre': 'costCenter',
  'customtype': 'customType',
  'department': 'department',
  'description': 'description',
  'domain': 'domain',
  'fulltimeequivalent': 'fullTimeEquivalent',
  'location': 'location',
  'name': 'name',
  'primary': 'primary',
  'symbol': 'symbol',
  'title': 'title',
  'type': 'type',
  }

TAG_OTHEREMAIL_ARGUMENT_TO_FIELD_MAP = {
  'address': 'address',
  'customtype': 'customType',
  'primary': 'primary',
  'type': 'type',
  }

TAG_PHONE_ARGUMENT_TO_FIELD_MAP = {
  'customtype': 'customType',
  'primary': 'primary',
  'type': 'type',
  'value': 'value',
  }

TAG_POSIXACCOUNT_ARGUMENT_TO_FIELD_MAP = {
  'accountid': 'accountId',
  'gecos': 'gecos',
  'gid': 'gid',
  'homedirectory': 'homeDirectory',
  'operatingsystemtype': 'operatingSystemType',
  'primary': 'primary',
  'shell': 'shell',
  'systemid': 'systemId',
  'uid': 'uid',
  'username': 'username',
  }

TAG_RELATION_ARGUMENT_TO_FIELD_MAP = {
  'customtype': 'customType',
  'type': 'type',
  'value': 'value',
  }

TAG_SSHPUBLICKEY_ARGUMENT_TO_FIELD_MAP = {
  'expirationtimeusec': 'expirationTimeUsec',
  'fingerprint': 'fingerprint',
  'key': 'key',
  }

TAG_WEBSITE_ARGUMENT_TO_FIELD_MAP = {
  'customtype': 'customType',
  'primary': 'primary',
  'type': 'type',
  'value': 'value',
  }

TAG_FIELD_SUBFIELD_CHOICE_MAP = {
  'address': ('addresses', TAG_ADDRESS_ARGUMENT_TO_FIELD_MAP),
  'addresses': ('addresses', TAG_ADDRESS_ARGUMENT_TO_FIELD_MAP),
  'email': ('primaryEmail', TAG_EMAIL_ARGUMENT_TO_FIELD_MAP),
  'externalid': ('externalIds', TAG_EXTERNALID_ARGUMENT_TO_FIELD_MAP),
  'externalids': ('externalIds', TAG_EXTERNALID_ARGUMENT_TO_FIELD_MAP),
  'gender': ('gender', TAG_GENDER_ARGUMENT_TO_FIELD_MAP),
  'im': ('ims', TAG_IM_ARGUMENT_TO_FIELD_MAP),
  'ims': ('ims', TAG_IM_ARGUMENT_TO_FIELD_MAP),
  'keyword': ('keywords', TAG_KEYWORD_ARGUMENT_TO_FIELD_MAP),
  'keywords': ('keywords', TAG_KEYWORD_ARGUMENT_TO_FIELD_MAP),
  'location': ('locations', TAG_LOCATION_ARGUMENT_TO_FIELD_MAP),
  'locations': ('locations', TAG_LOCATION_ARGUMENT_TO_FIELD_MAP),
  'name': ('name', TAG_NAME_ARGUMENT_TO_FIELD_MAP),
  'organization': ('organizations', TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP),
  'organizations': ('organizations', TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP),
  'organisation': ('organizations', TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP),
  'organisations': ('organizations', TAG_ORGANIZATION_ARGUMENT_TO_FIELD_MAP),
  'otheremail': ('emails', TAG_OTHEREMAIL_ARGUMENT_TO_FIELD_MAP),
  'otheremails': ('emails', TAG_OTHEREMAIL_ARGUMENT_TO_FIELD_MAP),
  'phone': ('phones', TAG_PHONE_ARGUMENT_TO_FIELD_MAP),
  'phones': ('phones', TAG_PHONE_ARGUMENT_TO_FIELD_MAP),
  'photourl': ('thumbnailPhotoUrl', {'': 'thumbnailPhotoUrl'}),
  'posix': ('posixAccounts', TAG_POSIXACCOUNT_ARGUMENT_TO_FIELD_MAP),
  'posixaccounts': ('posixAccounts', TAG_POSIXACCOUNT_ARGUMENT_TO_FIELD_MAP),
  'relation': ('relations', TAG_RELATION_ARGUMENT_TO_FIELD_MAP),
  'relations': ('relations', TAG_RELATION_ARGUMENT_TO_FIELD_MAP),
  'sshkeys': ('sshPublicKeys', TAG_SSHPUBLICKEY_ARGUMENT_TO_FIELD_MAP),
  'sshpublickeys': ('sshPublicKeys', TAG_SSHPUBLICKEY_ARGUMENT_TO_FIELD_MAP),
  'website': ('websites', TAG_WEBSITE_ARGUMENT_TO_FIELD_MAP),
  'websites': ('websites', TAG_WEBSITE_ARGUMENT_TO_FIELD_MAP),
  }

def _initTagReplacements():
  return {'cd': None, 'tags': {}, 'subs': False,
          'fieldsSet': set(), 'fields': '',
          'schemasSet': set(), 'customFieldMask': None}

def _getTagReplacement(myarg, tagReplacements, allowSubs):
  if myarg == 'replace':
    trregex = None
  elif myarg == 'replaceregex':
    trregex = _getMain().getREPatternSubstitution(re.IGNORECASE)
  else:
    return False
  matchTag = _getMain().getString(Cmd.OB_TAG)
  matchReplacement = _getMain().getString(Cmd.OB_STRING, minLen=0)
  if matchReplacement.startswith('field:'):
    if not allowSubs:
      _getMain().usageErrorExit(Msg.USER_SUBS_NOT_ALLOWED_TAG_REPLACEMENT)
    tagReplacements['subs'] = True
    field = matchReplacement[6:].strip().lower()
    if field.find('.') != -1:
      args = field.split('.', 3)
      field = args[0]
      subfield = args[1]
      if len(args) == 2:
        matchfield = matchvalue = ''
      elif len(args) == 4:
        matchfield = args[2]
        matchvalue = args[3]
        if matchfield == 'primary':
          matchvalue = matchvalue.lower()
          if matchvalue == _getMain().TRUE:
            matchvalue = True
          elif matchvalue == _getMain().FALSE:
            matchvalue = ''
          else:
            _getMain().invalidChoiceExit(matchvalue, _getMain().TRUE_FALSE, True)
      else:
        Cmd.Backup()
        _getMain().usageErrorExit(Msg.INVALID_TAG_SPECIFICATION)
    elif field == 'photourl':
      subfield = matchfield = matchvalue = ''
    else:
      field = ''
    if not field or field not in TAG_FIELD_SUBFIELD_CHOICE_MAP:
      _getMain().invalidChoiceExit(field, TAG_FIELD_SUBFIELD_CHOICE_MAP, True)
    field, subfieldsChoiceMap = TAG_FIELD_SUBFIELD_CHOICE_MAP[field]
    if subfield not in subfieldsChoiceMap:
      _getMain().invalidChoiceExit(subfield, subfieldsChoiceMap, True)
    subfield = subfieldsChoiceMap[subfield]
    if matchfield:
      if matchfield not in subfieldsChoiceMap:
        _getMain().invalidChoiceExit(matchfield, subfieldsChoiceMap, True)
      matchfield = subfieldsChoiceMap[matchfield]
    tagReplacements['fieldsSet'].add(field)
    tagReplacements['fields'] = ','.join(tagReplacements['fieldsSet'])
    tagReplacements['tags'][matchTag] = {'field': field, 'subfield': subfield,
                                         'matchfield': matchfield, 'matchvalue': matchvalue, 'value': '',
                                         'trregex': trregex}
    if field == 'locations' and subfield == 'buildingName':
      _getMain()._makeBuildingIdNameMap()
  elif matchReplacement.startswith('schema:'):
    if not allowSubs:
      _getMain().usageErrorExit(Msg.USER_SUBS_NOT_ALLOWED_TAG_REPLACEMENT)
    tagReplacements['subs'] = True
    matchReplacement = matchReplacement[7:].strip()
    if matchReplacement.find('.') != -1:
      schemaName, schemaField = matchReplacement.split('.', 1)
    else:
      schemaName = ''
    if not schemaName or not schemaField:
      _getMain().invalidArgumentExit(Cmd.OB_SCHEMA_NAME_FIELD_NAME)
    tagReplacements['fieldsSet'].add('customSchemas')
    tagReplacements['fields'] = ','.join(tagReplacements['fieldsSet'])
    tagReplacements['schemasSet'].add(schemaName)
    tagReplacements['customFieldMask'] = ','.join(tagReplacements['schemasSet'])
    tagReplacements['tags'][matchTag] = {'schema': schemaName, 'schemafield': schemaField, 'value': '',
                                         'trregex': trregex}
  elif ((matchReplacement.find('#') >= 0) and
        (matchReplacement.find('#user#') >= 0) or (matchReplacement.find('#email#') >= 0) or (matchReplacement.find('#username#') >= 0)):
    if not allowSubs:
      _getMain().usageErrorExit(Msg.USER_SUBS_NOT_ALLOWED_TAG_REPLACEMENT)
    tagReplacements['subs'] = True
    tagReplacements['tags'][matchTag] = {'template': matchReplacement, 'value': '',
                                         'trregex': trregex}
  else:
    if trregex is None:
      tagReplacements['tags'][matchTag] = {'value': matchReplacement}
    else:
      tagReplacements['tags'][matchTag] = {'value': re.sub(trregex[0], trregex[1], matchReplacement)}
  return True

def _getTagReplacementFieldValues(user, i, count, tagReplacements, results=None):
  if results is None:
    if tagReplacements['fields'] and tagReplacements['fields'] != 'primaryEmail':
      if not tagReplacements['cd']:
        tagReplacements['cd'] = _getMain().buildGAPIObject(API.DIRECTORY)
      try:
        results = _getMain().callGAPI(tagReplacements['cd'].users(), 'get',
                           throwReasons=GAPI.USER_GET_THROW_REASONS,
                           userKey=user, projection='custom', customFieldMask=tagReplacements['customFieldMask'], fields=tagReplacements['fields'])
      except (GAPI.userNotFound, GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest, GAPI.backendError, GAPI.systemError):
        _getMain().entityUnknownWarning(Ent.USER, user, i, count)
        return
    else:
      results = {'primaryEmail': user}
  userName, domain = _getMain().splitEmailAddress(user)
  for tag in tagReplacements['tags'].values():
    if tag.get('field'):
      field = tag['field']
      if field == 'primaryEmail':
        subfield = tag['subfield']
        if subfield == 'username':
          tag['value'] = userName
        elif subfield == 'domain':
          tag['value'] = domain
        else:
          tag['value'] = user
      else:
        if field in ['addresses', 'emails', 'ims', 'organizations', 'phones', 'posixAccounts', 'websites']:
          items = results.get(field, [])
          if not tag['matchfield']:
            for data in items:
              if data.get('primary'):
                break
            else:
              if items:
                data = items[0]
              else:
                data = {}
          else:
            for data in items:
              if data.get(tag['matchfield'], '') == tag['matchvalue']:
                break
            else:
              data = {}
        elif field in ['externalIds', 'relations', 'sshPublicKeys']:
          items = results.get(field, [])
          if not tag['matchfield']:
            if items:
              data = items[0]
            else:
              data = {}
          else:
            for data in items:
              if data.get(tag['matchfield'], '') == tag['matchvalue']:
                break
            else:
              data = {}
        elif field in ['keywords', 'locations']:
          items = results.get(field, [])
          if not tag['matchfield']:
            if items:
              data = items[0]
              data['buildingName'] = GM.Globals[GM.MAP_BUILDING_ID_TO_NAME].get(data.get('buildingId', ''), '')
            else:
              data = {}
          else:
            for data in items:
              if data.get(tag['matchfield'], '') == tag['matchvalue']:
                break
            else:
              data = {}
        elif field == 'thumbnailPhotoUrl':
          data = results
        else:
          data = results.get(field, {})
        tag['value'] = str(data.get(tag['subfield'], ''))
    elif tag.get('schema'):
      tag['value'] = str(results.get('customSchemas', {}).get(tag['schema'], {}).get(tag['schemafield'], ''))
    elif tag.get('template'):
      tag['value'] = _substituteForUser(tag['template'], user, userName)
    trregex = tag.get('trregex', None)
    if trregex is not None:
      tag['value'] = re.sub(trregex[0], trregex[1], tag['value'])

RTL_PATTERN = re.compile(r'(?s){RTL}.*?{/RTL}')
RT_PATTERN = re.compile(r'(?s){RT}.*?{/RT}')
TAG_REPLACE_PATTERN = re.compile(r'{(.+?)}')
RT_MARKERS = {'RT', '/RT', 'RTL', '/RTL'}
PC_PATTERN = re.compile(r'(?s){PC}.*?{/PC}')
UC_PATTERN = re.compile(r'(?s){UC}.*?{/UC}')
LC_PATTERN = re.compile(r'(?s){LC}.*?{/LC}')
CASE_MARKERS = {'PC', '/PC', 'UC', '/UC', 'LC', '/LC'}
SKIP_PATTERNS = [re.compile(r'<head>.*?</head>', flags=re.IGNORECASE),
                 re.compile(r'<script>.*?</script>', flags=re.IGNORECASE)]

def _processTagReplacements(tagReplacements, message):
  def pcase(trstring):
    new = ''
    # state = True: Upshift 1st letter found
    # state = False: Downshift subsequent letters
    state = True
    for c in trstring:
      if state:
        if c.isalpha():
          new += c.upper()
          state = False
        else:
          new += c
      else:
        if c.isalpha():
          new += c.lower()
        else:
          state = True
          new += c
    return new

  def ucase(trstring):
    return trstring.upper()

  def lcase(trstring):
    return trstring.lower()

  def _processCase(message, casePattern, caseFunc):
# Find all {xC}.*?{/xC} sequences
    pos = 0
    while True:
      match = casePattern.search(message, pos)
      if not match:
        return message
      start, end = match.span()
      for skipArea in skipAreas:
        if start >= skipArea[0] and end <= skipArea[1]:
          break
      else:
        message = message[:start]+caseFunc(message[start+4:end-5])+message[end:]
      pos = end

# Identify areas of message to avoid replacements
  skipAreas = []
  for pattern in SKIP_PATTERNS:
    pos = 0
    while True:
      match = pattern.search(message, pos)
      if not match:
        break
      skipAreas.append(match.span())
      pos = match.end()
  skipTags = set()
# Find all {tag}, note replacement value and starting location; note tags in skipAreas
  tagFields = []
  tagSubs = {}
  pos = 0
  while True:
    match = TAG_REPLACE_PATTERN.search(message, pos)
    if not match:
      break
    start, end = match.span()
    tag = match.group(1)
    if tag in CASE_MARKERS:
      pass
    elif tag not in RT_MARKERS:
      for skipArea in skipAreas:
        if start >= skipArea[0] and end <= skipArea[1]:
          skipTags.add(tag)
          break
      else:
        tagSubs.setdefault(tag, tagReplacements['tags'].get(tag, {'value': ''})['value'])
        tagFields.append((tagSubs[tag], start))
    pos = end
# Find all {RT}.*?{/RT} sequences
# If any non-empty {tag} replacement value falls between them, then mark {RT} and {/RT} to be stripped
# Otherwise, mark the entire {RT}.*?{/RT} sequence to be stripped
  rtStrips = []
  pos = 0
  while True:
    match = RT_PATTERN.search(message, pos)
    if not match:
      break
    start, end = match.span()
    stripEntireRT = True
    hasTags = False
    for tagField in tagFields:
      if tagField[1] >= end:
        break
      if tagField[1] >= start:
        hasTags = True
        if tagField[0]:
          rtStrips.append((False, start, start+4))
          rtStrips.append((False, end-5, end))
          stripEntireRT = False
          break
    if stripEntireRT:
      if hasTags or start+4 == end-5:
        rtStrips.append((True, start, end))
      else:
        rtStrips.append((False, start, start+4))
        rtStrips.append((False, end-5, end))
    pos = end
# Find all {RTL}.*?{/RTL} sequences
# If any non-empty {RT}...{tag}... {/RT} falls between them, then mark {RTL} and {/RTL} to be stripped
# Otherwise, mark the entire {RTL}.*{/RTL} sequence to be stripped
  rtlStrips = []
  pos = 0
  while True:
    match = RTL_PATTERN.search(message, pos)
    if not match:
      break
    start, end = match.span()
    stripEntireRTL = True
    hasTags = False
    for tagField in tagFields:
      if tagField[1] >= end:
        break
      if tagField[1] >= start:
        hasTags = True
        if tagField[0]:
          rtlStrips.append((False, start, start+5, end-6, end))
          stripEntireRTL = False
          break
    if stripEntireRTL:
      for rtStrip in rtStrips:
        if rtStrip[1] >= end:
          break
        if rtStrip[1] >= start:
          hasTags = True
          if not rtStrip[0]:
            rtlStrips.append((False, start, start+5, end-6, end))
            stripEntireRTL = False
            break
    if stripEntireRTL:
      if hasTags or start+5 == end-6:
        rtlStrips.append((True, start, end))
      else:
        rtlStrips.append((False, start, start+5, end-6, end))
    pos = end
  if rtlStrips:
    allStrips = []
    i = 0
    l = len(rtStrips)
    for rtlStrip in rtlStrips:
      while i < l and rtStrips[i][1] < rtlStrip[1]:
        allStrips.append(rtStrips[i])
        i += 1
      allStrips.append((False, rtlStrip[1], rtlStrip[2]))
      if not rtlStrip[0]:
        while i < l and rtStrips[i][1] < rtlStrip[3]:
          allStrips.append(rtStrips[i])
          i += 1
        allStrips.append((False, rtlStrip[3], rtlStrip[4]))
      else:
        while i < l and rtStrips[i][1] < rtlStrip[2]:
          i += 1
    while i < l:
      allStrips.append(rtStrips[i])
      i += 1
  else:
    allStrips = rtStrips
# Strip {RTL} {/RTL}, {RT} {/RT}, {RTL}.*?{/RTL}, {RT}.*?{/RT} sequences
  for rtStrip in allStrips[::-1]:
    message = message[:rtStrip[1]]+message[rtStrip[2]:]
# Strip {RTL} {/RTL}, {RT} {/RT}, {RTL}.*?{/RTL}, {RT}.*?{/RT} sequences
# Make {tag} replacements; ignore tags in skipAreas
  pos = 0
  while True:
    match = TAG_REPLACE_PATTERN.search(message, pos)
    if not match:
      break
    start, end = match.span()
    tag = match.group(1)
    if tag in CASE_MARKERS:
      pos = end
    elif tag not in RT_MARKERS:
      if tag not in skipTags:
        message = re.sub(match.group(0), tagSubs[tag], message)
        pos = start+1
      else:
        pos = end
    else:
# Replace invalid RT tags with _getMain().ERROR(RT)
      message = re.sub(match.group(0), f'ERROR({tag})', message)
      pos = start+1
# Process case changes
  message = _processCase(message, PC_PATTERN, pcase)
  message = _processCase(message, UC_PATTERN, ucase)
  message = _processCase(message, LC_PATTERN, lcase)
  return message

def sendCreateUpdateUserNotification(body, basenotify, tagReplacements, i=0, count=0, msgFrom=None, createMessage=True):
  def _makeSubstitutions(field):
    notify[field] = _substituteForUser(notify[field], body['primaryEmail'], userName)
    notify[field] = notify[field].replace('#domain#', domain)
    notify[field] = notify[field].replace('#givenname#', body['name'].get('givenName', ''))
    notify[field] = notify[field].replace('#familyname#', body['name'].get('familyName', ''))

  def _makePasswordSubstitutions(field, html):
    if not html:
      notify[field] = notify[field].replace('#password#', notify['password'])
    else:
      notify[field] = notify[field].replace('#password#', notify['password'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

  userName, domain = _getMain().splitEmailAddress(body['primaryEmail'])
  notify = basenotify.copy()
  if not notify['subject']:
    notify['subject'] = Msg.CREATE_USER_NOTIFY_SUBJECT if createMessage else Msg.UPDATE_USER_PASSWORD_CHANGE_NOTIFY_SUBJECT
  _makeSubstitutions('subject')
  if not notify['message']:
    notify['message'] = Msg.CREATE_USER_NOTIFY_MESSAGE if createMessage else Msg.UPDATE_USER_PASSWORD_CHANGE_NOTIFY_MESSAGE
  elif notify['html']:
    notify['message'] = notify['message'].replace('\r', '').replace('\\n', '<br/>')
  else:
    notify['message'] = notify['message'].replace('\r', '').replace('\\n', '\n')
  _makeSubstitutions('message')
  if tagReplacements['subs']:
    _getTagReplacementFieldValues(body['primaryEmail'], i, count, tagReplacements, body if createMessage else None)
  notify['subject'] = _processTagReplacements(tagReplacements, notify['subject'])
  notify['message'] = _processTagReplacements(tagReplacements, notify['message'])
  _makePasswordSubstitutions('subject', False)
  _makePasswordSubstitutions('message', notify['html'])
  if 'from' in notify:
    msgFrom = notify['from']
  msgReplyTo = notify.get('replyto', None)
  mailBox = notify.get('mailbox', None)
  for recipient in notify['recipients']:
    _getMain().send_email(notify['subject'], notify['message'], recipient, i, count,
               msgFrom=msgFrom, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'], mailBox=mailBox)

def getRecipients():
  if _getMain().checkArgumentPresent('select'):
    _, recipients = _getMain().getEntityToModify(defaultEntityType=Cmd.ENTITY_USERS)
    return [_getMain().normalizeEmailAddressOrUID(emailAddress, noUid=True, noLower=True) for emailAddress in recipients]
  return _getMain().getNormalizedEmailAddressEntity(shlexSplit=True, noLower=True)

# gam sendemail [recipient|to] <RecipientEntity>
#	[from <EmailAddress>] [mailbox <EmailAddress>] [replyto <EmailAddress>]
#	[cc <RecipientEntity>] [bcc <RecipientEntity>] [singlemessage]
#	[subject <String>] [<MessageContent>] [html [<Boolean>]]
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution>  <Tag> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[newuser <EmailAddress> firstname|givenname <String> lastname|familyname <string> password <Password>]
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	[threadid <String>]
# gam <UserTypeEntity> sendemail recipient|to <RecipientEntity>
#	[replyto <EmailAddress>]
#	[cc <RecipientEntity>] [bcc <RecipientEntity>] [singlemessage]
#	[subject <String>] [<MessageContent>] [html [<Boolean>]]
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution>  <Tag> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[newuser <EmailAddress> firstname|givenname <String> lastname|familyname <string> password <Password>]
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	[threadid <String>]
# gam <UserTypeEntity> sendemail from <EmailAddress>
#	[replyto <EmailAddress>]
#	[cc <RecipientEntity>] [bcc <RecipientEntity>] [singlemessage]
#	[subject <String>] [<MessageContent> ][html [<Boolean>]]
#	(replace <Tag> <String>)*
#	(replaceregex <REMatchPattern> <RESubstitution>  <Tag> <String>)*
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	[newuser <EmailAddress> firstname|givenname <String> lastname|familyname <string> password <Password>]
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
#	[threadid <String>]
def doSendEmail(users=None):
  body = {}
  notify = {'subject': '', 'message': '', 'html': False, 'charset': _getMain().UTF8, 'password': ''}
  msgFroms = [_getMain()._getAdminEmail()]
  count = 1
  if users is None:
    _getMain().checkArgumentPresent({'recipient', 'recipients', 'to'})
    recipients = getRecipients()
  else:
    _, count, entityList = _getMain().getEntityArgument(users)
    if _getMain().checkArgumentPresent({'recipient', 'recipients', 'to'}):
      msgFroms = [_getMain().normalizeEmailAddressOrUID(entity) for entity in entityList]
      recipients = getRecipients()
    elif _getMain().checkArgumentPresent({'from'}):
      recipients = [_getMain().normalizeEmailAddressOrUID(entity) for entity in entityList]
      msgFroms = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      count = 1
    else:
      _getMain().missingArgumentExit('recipient|to|from')
  msgHeaders = {}
  ccRecipients = []
  bccRecipients = []
  mailBox = None
  msgReplyTo = None
  threadId = None
  singleMessage = False
  tagReplacements = _initTagReplacements()
  attachments = []
  embeddedImages = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if users is None and myarg == 'from':
      msgFroms = [_getMain().getString(Cmd.OB_EMAIL_ADDRESS)]
      count = 1
    elif myarg == 'replyto':
      msgReplyTo = _getMain().getString(Cmd.OB_EMAIL_ADDRESS)
    elif myarg == 'subject':
      notify['subject'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg in _getMain().SORF_MSG_FILE_ARGUMENTS:
      notify['message'], notify['charset'], notify['html'] = _getMain().getStringOrFile(myarg)
    elif myarg == 'cc':
      ccRecipients = getRecipients()
    elif myarg == 'bcc':
      bccRecipients = getRecipients()
    elif myarg == 'mailbox':
      mailBox = _getMain().getString(Cmd.OB_EMAIL_ADDRESS)
    elif myarg == 'singlemessage':
      singleMessage = True
    elif myarg == 'html':
      notify['html'] = _getMain().getBoolean()
    elif myarg == 'newuser':
      body['primaryEmail'] = _getMain().getEmailAddress()
    elif myarg in {'firstname', 'givenname'}:
      body.setdefault('name', {})
      body['name']['givenName'] = _getMain().getString(Cmd.OB_STRING, minLen=0, maxLen=60)
    elif myarg in {'lastname', 'familyname'}:
      body.setdefault('name', {})
      body['name']['familyName'] = _getMain().getString(Cmd.OB_STRING, minLen=0, maxLen=60)
    elif myarg in {'password', 'notifypassword'}:
      body['password'] = notify['password'] = _getMain().getString(Cmd.OB_PASSWORD, maxLen=100)
    elif _getTagReplacement(myarg, tagReplacements, False):
      pass
    elif myarg == 'attach':
      attachments.append((_getMain().getFilename(), _getMain().getCharSet()))
    elif myarg == 'embedimage':
      embeddedImages.append((_getMain().getFilename(), _getMain().getString(Cmd.OB_STRING)))
    elif myarg in _getMain().SMTP_HEADERS_MAP:
      if myarg in _getMain().SMTP_DATE_HEADERS:
        msgDate, _, _ = _getMain().getTimeOrDeltaFromNow(True)
        msgHeaders[_getMain().SMTP_HEADERS_MAP[myarg]] = formatdate(time.mktime(msgDate.timetuple()) + msgDate.microsecond/1E6, True)
      else:
        msgHeaders[_getMain().SMTP_HEADERS_MAP[myarg]] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'header':
      header = _getMain().getString(Cmd.OB_STRING, minLen=1)
      msgHeaders[_getMain().SMTP_HEADERS_MAP.get(header.lower(), header)] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'threadid':
      threadId = _getMain().getString(Cmd.OB_STRING)
    else:
      _getMain().unknownArgumentExit()
  notify['message'] = notify['message'].replace('\r', '').replace('\\n', '\n')
  if tagReplacements['tags']:
    notify['message'] = _processTagReplacements(tagReplacements, notify['message'])
  if tagReplacements['tags']:
    notify['subject'] = _processTagReplacements(tagReplacements, notify['subject'])
  jcount = len(recipients)
  if body.get('primaryEmail'):
    if (recipients and ('password' in body) and ('name' in body) and ('givenName' in body['name']) and ('familyName' in body['name'])):
      notify['recipients'] = recipients
      sendCreateUpdateUserNotification(body, notify, tagReplacements, msgFrom=msgFroms[0])
    else:
      _getMain().usageErrorExit(Msg.NEWUSER_REQUIREMENTS, True)
    return
  if ccRecipients or bccRecipients:
    singleMessage = True
  i = 0
  for msgFrom in msgFroms:
    i += 1
    if singleMessage:
      _getMain().entityPerformActionModifierNumItems([Ent.USER, msgFrom],
                                          Act.MODIFIER_TO, jcount+len(ccRecipients)+len(bccRecipients), Ent.RECIPIENT, i, count)
      _getMain().send_email(notify['subject'], notify['message'], ','.join(recipients), i, count,
                 msgFrom=msgFrom, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'],
                 attachments=attachments, embeddedImages=embeddedImages, msgHeaders=msgHeaders,
                 ccRecipients=','.join(ccRecipients), bccRecipients=','.join(bccRecipients),
                 mailBox=mailBox, threadId=threadId)
    else:
      _getMain().entityPerformActionModifierNumItems([Ent.USER, msgFrom], Act.MODIFIER_TO, jcount, Ent.RECIPIENT, i, count)
      Ind.Increment()
      j = 0
      for recipient in recipients:
        j += 1
        _getMain().send_email(notify['subject'], notify['message'], recipient, j, jcount,
                   msgFrom=msgFrom, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'],
                   attachments=attachments, embeddedImages=embeddedImages, msgHeaders=msgHeaders, mailBox=mailBox, threadId=threadId)
      Ind.Decrement()

# gam <UserTypeEntity> sendreply
#	(((query <QueryGmail> [querytime<String> <Date>]*) [or|and])+) | (ids <MessageIDEntity>)
#	[replyto <EmailAddress>]
#	[subject <String>] [<MessageContent>] [html [<Boolean>]]
#	(attach <FileName> [charset <CharSet>])*
#	(embedimage <FileName> <String>)*
#	(<SMTPDateHeader> <Time>)* (<SMTPHeader> <String>)* (header <String> <String>)*
def doSendReply(users):
  def _getHeaderValue(name):
    for header in messageInfo['payload']['headers']:
      if name == header['name']:
        return _getMain()._decodeHeader(header['value'])
    return ''

  notify = {'subject': '', 'message': '', 'html': False, 'charset': _getMain().UTF8}
  query = ''
  queryTimes = {}
  messageIds = []
  msgHeaders = {}
  msgReplyTo = None
  attachments = []
  embeddedImages = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'query':
      selectLocation = Cmd.Location()
      if query:
        query += ' '
      query += f'({_getMain().getString(Cmd.OB_QUERY)})'
    elif myarg.startswith('querytime'):
      queryTimes[myarg] = _getMain().getDateOrDeltaFromNow().replace('-', '/')
    elif myarg in {'or', 'and'}:
      if query:
        query += f' {myarg.upper()}'
    elif myarg == 'ids':
      selectLocation = Cmd.Location()
      messageIds = _getMain().getEntityList(Cmd.OB_MESSAGE_ID)
    elif myarg == 'subject':
      notify['subject'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg in _getMain().SORF_MSG_FILE_ARGUMENTS:
      notify['message'], notify['charset'], notify['html'] = _getMain().getStringOrFile(myarg)
    elif myarg == 'replyto':
      msgReplyTo = _getMain().getString(Cmd.OB_EMAIL_ADDRESS)
    elif myarg == 'html':
      notify['html'] = _getMain().getBoolean()
    elif myarg == 'attach':
      attachments.append((_getMain().getFilename(), _getMain().getCharSet()))
    elif myarg == 'embedimage':
      embeddedImages.append((_getMain().getFilename(), _getMain().getString(Cmd.OB_STRING)))
    elif myarg in _getMain().SMTP_HEADERS_MAP:
      if myarg in _getMain().SMTP_DATE_HEADERS:
        msgDate, _, _ = _getMain().getTimeOrDeltaFromNow(True)
        msgHeaders[_getMain().SMTP_HEADERS_MAP[myarg]] = formatdate(time.mktime(msgDate.timetuple()) + msgDate.microsecond/1E6, True)
      else:
        msgHeaders[_getMain().SMTP_HEADERS_MAP[myarg]] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'header':
      header = _getMain().getString(Cmd.OB_STRING, minLen=1)
      msgHeaders[_getMain().SMTP_HEADERS_MAP.get(header.lower(), header)] = _getMain().getString(Cmd.OB_STRING)
    else:
      _getMain().unknownArgumentExit()
  if query and messageIds:
    Cmd.SetLocation(selectLocation-1)
    _getMain().usageErrorExit(Msg.ARE_MUTUALLY_EXCLUSIVE.format('query <QueryGmail>', 'ids <MessageIDEntity>'))
  notify['message'] = notify['message'].replace('\r', '').replace('\\n', '\n')
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    try:
      if query:
        _getMain().printGettingAllEntityItemsForWhom(Ent.MESSAGE, user, i, count, query=query)
        listResult = _getMain().callGAPIpages(gmail.users().messages(), 'list', 'messages',
                                   pageMessage=_getMain().getPageMessageForWhom(),
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=query, fields='nextPageToken,messages(id)',
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      _getMain().entityNumEntitiesActionNotPerformedWarning([Ent.USER, user], Ent.MESSAGE, jcount, Msg.NO_ENTITIES_MATCHED.format(Ent.Plural(Ent.MESSAGE)), i, count)
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
      continue
    _getMain().entityPerformActionModifierNumItems([Ent.USER, user], Act.MODIFIER_TO, jcount, Ent.RECIPIENT, i, count)
    Ind.Increment()
    j = 0
    for messageId in messageIds:
      j += 1
      try:
        messageInfo = _getMain().callGAPI(gmail.users().messages(), 'get',
                               throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                               userId='me', id=messageId, fields='id,threadId,payload(headers)')
        threadId = messageInfo['threadId']
        msgHeaders['References'] = msgHeaders['In-Reply-To'] = _getHeaderValue('Message-ID')
        msgSubject = notify['subject'] if notify['subject'] else f"Re: {_getHeaderValue('Subject')}"
        recipient = _getHeaderValue('From')
        _getMain().send_email(msgSubject, notify['message'], recipient, j, jcount,
                   msgFrom=user, msgReplyTo=msgReplyTo, html=notify['html'], charset=notify['charset'],
                   attachments=attachments, embeddedImages=embeddedImages, msgHeaders=msgHeaders, threadId=threadId,
                   action=Act.SENDREPLY)
      except GAPI.notFound:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], Msg.DOES_NOT_EXIST, j, jcount)
      except GAPI.invalidMessageId:
        _getMain().entityActionFailedWarning([Ent.USER, user, Ent.MESSAGE, messageId], Msg.INVALID_MESSAGE_ID, j, jcount)
      except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
        _getMain().entityActionFailedWarning([Ent.USER, user], str(e), i, count)
        break
      except GAPI.serviceNotAvailable:
        _getMain().userGmailServiceNotEnabledWarning(user, i, count)
        break
    Ind.Decrement()

ADDRESS_FIELDS_PRINT_ORDER = ['contactName', 'organizationName', 'addressLine1', 'addressLine2', 'addressLine3', 'locality', 'region', 'postalCode', 'countryCode']

