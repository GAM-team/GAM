"""Gmail message/thread operations: select, archive, process, export, forward, draft, import.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re

import arrow

import googleapiclient.errors
import googleapiclient.http

from gam.util.batch import RI_ENTITY, RI_I, RI_COUNT, RI_J, RI_JCOUNT, RI_ITEM
from gam.cmd.gmail.labels import LABEL_TYPE_SYSTEM, LABEL_TYPE_USER, _getUserGmailLabels
from gam.cmd.gmail.modify import (
    SMTP_DATE_HEADERS,
    SMTP_HEADERS_MAP,
    _decodeHeader,
    _finalizeMessageSelectParameters,
    _getMessageSelectParameters,
    _initMessageThreadParameters,
)
import io
import base64
import os

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages, checkGAPIError
from gam.util.args import (
    UTF8,
    escapeCRsNLs,
    getAddCSVData,
    getArgument,
    getBoolean,
    getCharacter,
    getHTTPError,
    getREPattern,
    getString
)
from gam.util.batch import batchRequestID
from gam.util.csv_pf import CSVPrintFile, flattenJSON
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityModifierItemValueListActionFailedWarning,
    entityModifierItemValueListActionPerformed,
    entityPerformActionModifierNumItemsModifier,
    entityPerformActionNumItems,
    entityPerformActionNumItemsModifier,
    getPageMessageForWhom,
    printEntity,
    printEntityKVList,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
    userDriveServiceNotEnabledWarning,
    userGmailServiceNotEnabledWarning
)
from gam.util.entity import _validateUserGetMessageIds, getEntityArgument, splitEmailAddressOrUID
from gam.util.errors import unknownArgumentExit
from gam.util.fileio import (
    ACTION_FAILED_RC,
    cleanFilename,
    setFilePath,
    uniqueFilename,
    writeFileReturnError
)
from gam.util.batch import executeBatch
from gam.util.output import setSysExitRC, formatLocalTimestamp
from gam.constants import IS08601_TIME_FORMAT, NO_ENTITIES_FOUND_RC, RFC2822_TIME_FORMAT
from gam.util.html import dehtml
from gam.util.tags import _substituteForUser
from gam.cmd.drive.core import _getDriveFileParentInfo, getDriveFileParentAttribute, initDriveFileAttributes

from gam.var import Act, Cmd, Ent, Ind

UTF8 = 'utf-8'

def printShowMessagesThreads(users, entityType):

  def _getBodyData(payload, getOrigMsg):
    data = headers = ''
    for part in payload.get('parts', []):
      if getOrigMsg:
        if show_all_headers:
          if not headers:
            headers = '---------- Original message ----------\n'
          for header in part.get('headers', []):
            headers += header['name']+': '+_decodeHeader(header['value'])+'\n'
        elif 'headers' in part:
          for name in headersToShow:
            for header in part['headers']:
              if name == header['name'].lower():
                if not headers:
                  headers = '---------- Original message ----------\n'
                headers += SMTP_HEADERS_MAP.get(name, header['name'])+': '+_decodeHeader(header['value'])+'\n'
        if headers:
          headers += 'Body:\n'
          data = Ind.INDENT_SPACES_PER_LEVEL
      if part['mimeType'] == 'text/plain':
        if 'data' in part['body']:
          data += base64.urlsafe_b64decode(str(part['body']['data'])).decode(UTF8)+'\n'
      elif show_html and part['mimeType'] == 'text/html':
        if 'data' in part['body']:
          data += base64.urlsafe_b64decode(str(part['body']['data'])).decode(UTF8)+'\n'
      elif part['mimeType'] == 'text/rfc822-headers':
        if 'data' in part['body']:
          data += _decodeHeader(base64.urlsafe_b64decode(str(part['body']['data'])).decode(UTF8)+'\n')
      else:
        data += _getBodyData(part, part['mimeType'] == 'message/rfc822')
    if getOrigMsg:
      data = data.replace('\n', f'\n{Ind.INDENT_SPACES_PER_LEVEL}').rstrip()
    return headers+data

  def _getMessageBody(payload):
    if 'attachmentId' not in payload.get('body', {}) and 'data' in payload.get('body', {}):
      return base64.urlsafe_b64decode(str(payload['body']['data'])).decode(UTF8)
    data = _getBodyData(payload, False)
    if data:
      return data
    return 'Body not available'

  ATTACHMENT_NAME_PATTERN = re.compile(r'^.*name="?(.*?)(?:"|;|$)')
  CHARSET_NAME_PATTERN = re.compile(r'^.*charset="?(.*?)(?:"|;|$)')

  def _showAttachmentMimeTypeSizeCharset(part, charset):
    printKeyValueList(['mimeType', part['mimeType']])
    printKeyValueList(['size', part['body']['size']])
    if charset:
      printKeyValueList(['charset', charset])

  def _showSaveAttachments(messageId, payload, attachmentNamePattern, j, jcount):
    for part in payload.get('parts', []):
      if 'attachmentId' in part['body']:
        for header in part['headers']:
          if header['name'] in {'Content-Type', 'Content-Disposition'}:
            mg = ATTACHMENT_NAME_PATTERN.match(header['value'])
            if not mg:
              continue
            attachmentName = mg.group(1)
            if (not attachmentNamePattern) or attachmentNamePattern.match(attachmentName):
              charset = ''
              if part['mimeType'] == 'text/plain':
                mg = CHARSET_NAME_PATTERN.match(header['value'])
                if mg:
                  charset = mg.group(1)
              if (part['mimeType'] == 'text/plain' and not noshow_text_plain) or save_attachments or upload_attachments:
                try:
                  result = callGAPI(gmail.users().messages().attachments(), 'get',
                                    throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND],
                                    messageId=messageId, id=part['body']['attachmentId'], userId='me')
                  if 'data' in result:
                    if show_attachments:
                      printKeyValueList(['Attachment', attachmentName])
                      Ind.Increment()
                      if part['mimeType'] == 'text/plain':
                        try:
                          printKeyValueList([Ind.MultiLineText(base64.urlsafe_b64decode(str(result['data'])).decode(charset)+'\n')])
                        except (LookupError, UnicodeDecodeError, UnicodeError):
                          _showAttachmentMimeTypeSizeCharset(part, charset)
                      else:
                        _showAttachmentMimeTypeSizeCharset(part, charset)
                      Ind.Decrement()
                    if save_attachments:
                      filename, _ = uniqueFilename(targetFolder, cleanFilename(attachmentName), overwrite)
                      action = Act.Get()
                      Act.Set(Act.DOWNLOAD)
                      status, e = writeFileReturnError(filename, base64.urlsafe_b64decode(str(result['data'])), mode='wb')
                      if status:
                        entityActionPerformed([Ent.ATTACHMENT, filename])
                      else:
                        entityActionFailedWarning([Ent.ATTACHMENT, filename], str(e))
                      Act.Set(action)
                    if upload_attachments:
                      filename = cleanFilename(attachmentName)
                      uploadAttachmentBody.update({'name': filename, 'mimeType': part['mimeType']})
                      action = Act.Get()
                      Act.Set(Act.CREATE)
                      media_body = googleapiclient.http.MediaIoBaseUpload(io.BytesIO(base64.urlsafe_b64decode(str(result['data']))), mimetype=part['mimeType'], resumable=True)
                      try:
                        result = callGAPI(drive.files(), 'create',
                                          throwReasons=GAPI.DRIVE_USER_THROW_REASONS+[GAPI.FORBIDDEN, GAPI.INSUFFICIENT_PERMISSIONS, GAPI.INSUFFICIENT_PARENT_PERMISSIONS,
                                                                                      GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.CANNOT_ADD_PARENT,
                                                                                      GAPI.FILE_NOT_FOUND, GAPI.UNKNOWN_ERROR, GAPI.INTERNAL_ERROR,
                                                                                      GAPI.STORAGE_QUOTA_EXCEEDED, GAPI.TEAMDRIVES_SHARING_RESTRICTION_NOT_ALLOWED,
                                                                                      GAPI.TEAMDRIVE_FILE_LIMIT_EXCEEDED, GAPI.TEAMDRIVE_HIERARCHY_TOO_DEEP,
                                                                                      GAPI.UPLOAD_TOO_LARGE, GAPI.TEAMDRIVES_SHORTCUT_FILE_NOT_SUPPORTED],
                                          media_body=media_body, body=uploadAttachmentBody, fields='id,name', supportsAllDrives=True)
                        entityModifierItemValueListActionPerformed([Ent.DRIVE_FILE, f"{result['name']}({result['id']})"],
                                                                   Act.MODIFIER_WITH_CONTENT_FROM, [Ent.ATTACHMENT, filename], j, jcount)
                      except (GAPI.forbidden, GAPI.insufficientPermissions, GAPI.insufficientParentPermissions,
                              GAPI.invalid, GAPI.badRequest, GAPI.cannotAddParent,
                              GAPI.fileNotFound, GAPI.unknownError, GAPI.internalError,
                              GAPI.storageQuotaExceeded, GAPI.teamdrivesSharingRestrictionNotAllowed,
                              GAPI.teamdrivefileLimitExceeded, GAPI.teamdriveHierarchyTooDeep,
                              GAPI.uploadTooLarge, GAPI.teamdrivesShortcutFileNotSupported) as e:
                        entityModifierItemValueListActionFailedWarning([Ent.DRIVE_FILE, None],
                                                                       Act.MODIFIER_WITH_CONTENT_FROM, [Ent.ATTACHMENT, filename], str(e), j, jcount)
                      except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy) as e:
                        userDriveServiceNotEnabledWarning(user, str(e), i, count)
                      Act.Set(action)
                except (GAPI.serviceNotAvailable, GAPI.notFound):
                  pass
              elif show_attachments:
                printKeyValueList(['Attachment', attachmentName])
                Ind.Increment()
                _showAttachmentMimeTypeSizeCharset(part, charset)
                Ind.Decrement()
            break
      else:
        _showSaveAttachments(messageId, part, attachmentNamePattern, j, jcount)

  def _initSenderLabelsMap(sender):
    if sender not in senderLabelsMaps:
      senderLabelsMaps[sender] = {'*None*': {'name': '*None*', 'count': 0, 'size': 0, 'type': LABEL_TYPE_USER, 'match': labelMatchPattern is None}}
      for label in labels['labels']:
        senderLabelsMaps[sender][label['id']] = {'name': label['name'], 'count': 0, 'size': 0, 'type': label['type'],
                                                'match': True if not labelMatchPattern else labelMatchPattern.match(label['name']) is not None}
    return senderLabelsMaps[sender]

  def _getMatchMessageLabels(result, sender):
    labelsMap = _initSenderLabelsMap(sender)
    messageLabels = []
    match = False
    for labelId in result.get('labelIds', []):
      if labelId in labelsMap:
        match |= labelsMap[labelId]['match']
        if not onlyUser or labelsMap[labelId]['type'] != LABEL_TYPE_SYSTEM:
          messageLabels.append(labelsMap[labelId]['name'])
      else:
        messageLabels.append(labelId)
    if labelMatchPattern and not match:
      return None
    return messageLabels

  def _checkSenderMatch(result):
    for header in result['payload'].get('headers', []):
      sender = _decodeHeader(header['value'])
      if header['name'] == 'Sender' and senderMatchPattern.match(sender):
        return sender
    return None

  def _checkSenderMatchCount(result):
    for header in result['payload'].get('headers', []):
      sender = _decodeHeader(header['value'])
      if header['name'] == 'Sender' and senderMatchPattern.match(sender):
        senderCounts.setdefault(sender, {'count': 0, 'size': 0})
        senderCounts[sender]['count'] += 1
        senderCounts[sender]['size'] += result['sizeEstimate']
        return sender
    return None

  def _qualifyMessage(user, result):
    if senderMatchPattern:
      sender = _checkSenderMatchCount(result)
      if not sender:
        return (False, None)
    else:
      sender = user
    if show_labels or labelMatchPattern:
      messageLabels = _getMatchMessageLabels(result, sender)
      if messageLabels is None:
        return (False, None)
      return (True, messageLabels)
    return (True, None)

  def _convertDateTime(headerValue):
    dateTimeValue = headerValue.replace('GMT', '+0000')
    dateTimeValue = dateTimeValue.replace('UT', '+0000')
    pLoc = dateTimeValue.find(' (')
    if pLoc > 0:
      dateTimeValue = dateTimeValue[:pLoc]
    try:
      dateTimeValue = arrow.Arrow.strptime(dateTimeValue, RFC2822_TIME_FORMAT)
      if dateHeaderConvertTimezone:
        dateTimeValue = dateTimeValue.to(GC.Values[GC.TIMEZONE])
      return dateTimeValue.strftime(dateHeaderFormat)
    except ValueError:
      return headerValue

  def _showMessage(user, result, j, jcount, checkMax=True):
    if checkMax and parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    status, messageLabels = _qualifyMessage(user, result)
    if not status:
      return
    printEntity([Ent.MESSAGE, result['id']], j, jcount)
    Ind.Increment()
    if show_snippet:
      printKeyValueList(['Snippet', dehtml(result['snippet']).replace('\n', ' ')])
    if show_all_headers:
      for header in result['payload'].get('headers', []):
        headerValue = _decodeHeader(header['value'])
        if dateHeaderFormat and header['name'].lower() in SMTP_DATE_HEADERS:
          headerValue = _convertDateTime(headerValue)
        printKeyValueList([header['name'], headerValue])
    else:
      for name in headersToShow:
        for header in result['payload'].get('headers', []):
          if name == header['name'].lower():
            headerValue = _decodeHeader(header['value'])
            if dateHeaderFormat and name in SMTP_DATE_HEADERS:
              headerValue = _convertDateTime(headerValue)
            printKeyValueList([SMTP_HEADERS_MAP.get(name, header['name']), headerValue])
    if show_date:
      printKeyValueList(['Date', formatLocalTimestamp(result['internalDate'])])
    if show_size:
      printKeyValueList(['SizeEstimate', result['sizeEstimate']])
    if show_labels:
      printKeyValueList(['Labels', delimiter.join(messageLabels)])
    if show_body:
      printKeyValueList(['Body', None])
      Ind.Increment()
      printKeyValueList([Ind.MultiLineText(_getMessageBody(result['payload']))])
      Ind.Decrement()
    if show_attachments or save_attachments or upload_attachments:
      _showSaveAttachments(result['id'], result['payload'], attachmentNamePattern, j, jcount)
    Ind.Decrement()
    if checkMax:
      parameters['messagesProcessed'] += 1

  def _getAttachments(messageId, payload, attachmentNamePattern, attachments):
    for part in payload.get('parts', []):
      if 'attachmentId' in part['body']:
        for header in part['headers']:
          if header['name'] in {'Content-Type', 'Content-Disposition'}:
            mg = ATTACHMENT_NAME_PATTERN.match(header['value'])
            if not mg:
              continue
            attachmentName = mg.group(1)
            charset = ''
            if part['mimeType'] == 'text/plain':
              mg = CHARSET_NAME_PATTERN.match(header['value'])
              if mg:
                charset = mg.group(1)
            if (not attachmentNamePattern) or attachmentNamePattern.match(attachmentName):
              attachments.append((attachmentName, part['mimeType'], part['body']['size'], charset))
            break
      else:
        _getAttachments(messageId, part, attachmentNamePattern, attachments)

  def _printMessage(user, result, checkMax=True):
    if checkMax and parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    status, messageLabels = _qualifyMessage(user, result)
    if not status:
      return
    row = {'User': user, 'threadId': result['threadId'], 'id': result['id']}
    if show_snippet:
      row['Snippet'] = dehtml(result['snippet']).replace('\n', ' ')
    if show_all_headers:
      headerCounts = {}
      for header in result['payload'].get('headers', []):
        headerCounts.setdefault(header['name'], 0)
        headerValue = _decodeHeader(header['value'])
        if dateHeaderFormat and header['name'].lower() in SMTP_DATE_HEADERS:
          headerValue = _convertDateTime(headerValue)
        if headerCounts[header['name']] == 0:
          row[header['name']] = headerValue
        else:
          row[f'{header["name"]} {headerCounts[header["name"]]}'] = headerValue
        headerCounts[header['name']] += 1
    else:
      for name in headersToShow:
        j = 0
        for header in result['payload'].get('headers', []):
          if name == header['name'].lower():
            headerValue = _decodeHeader(header['value'])
            if dateHeaderFormat and name in SMTP_DATE_HEADERS:
              headerValue = _convertDateTime(headerValue)
            if j == 0:
              row[SMTP_HEADERS_MAP.get(name, header['name'])] = headerValue
            else:
              row[f'{SMTP_HEADERS_MAP.get(name, header["name"])} {j}'] = headerValue
            j += 1
    if show_date:
      row['Date'] = formatLocalTimestamp(result['internalDate'])
    if show_size:
      row['SizeEstimate'] = result['sizeEstimate']
    if show_labels:
      row['LabelsCount'] = len(messageLabels)
      row['Labels'] = delimiter.join(messageLabels)
    if show_body:
      if not convertCRNL:
        row['Body'] = _getMessageBody(result['payload'])
      else:
        row['Body'] = escapeCRsNLs(_getMessageBody(result['payload']))
    if show_attachments:
      attachments = []
      _getAttachments(result['id'], result['payload'], attachmentNamePattern, attachments)
      row['Attachments'] = len(attachments)
      for i, attachment in enumerate(attachments):
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}name'] = attachment[0]
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}mimeType'] = attachment[1]
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}size'] = attachment[2]
        row[f'Attachments{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}{i}{GC.Values[GC.CSV_OUTPUT_SUBFIELD_DELIMITER]}charset'] = attachment[3]
    if addCSVData:
      row.update(addCSVData)
    csvPF.WriteRowTitles(row)
    if checkMax:
      parameters['messagesProcessed'] += 1

  def _countMessageLabels(user, result):
    if senderMatchPattern:
      sender = _checkSenderMatch(result)
      if not sender:
        return False
    else:
      sender = user
    labelsMap = _initSenderLabelsMap(sender)
    labelIds = result.get('labelIds', [])
    if labelIds:
      for labelId in labelIds:
        if labelId in labelsMap:
          labelsMap[labelId]['count'] += 1
          labelsMap[labelId]['size'] += result['sizeEstimate']
        else:
          labelsMap[labelId] = {'name': labelId, 'count': 1, 'size': result['sizeEstimate'], 'type': LABEL_TYPE_USER,
                                'match': True if not labelMatchPattern else labelMatchPattern.match(labelId) is not None}
    elif not labelMatchPattern:
      labelsMap['*None*']['count'] += 1
      labelsMap['*None*']['size'] += result['sizeEstimate']

  def _countMessages(_, result):
    if senderMatchPattern and not _checkSenderMatchCount(result):
      return
    messageThreadCounts['messages'] += 1
    messageThreadCounts['size'] += result['sizeEstimate']

  def _showThread(user, result, j, jcount):
    if parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    if senderMatchPattern:
      for message in result['messages']:
        if _checkSenderMatch(message):
          break
      else:
        return
    messageThreadCounts['threads'] += 1
    printEntity([Ent.THREAD, result['id']], j, jcount)
    Ind.Increment()
    if show_snippet and 'snippet' in result:
      printKeyValueList(['Snippet', dehtml(result['snippet']).replace('\n', ' ')])
    kcount = len(result['messages'])
    k = 0
    for message in result['messages']:
      k += 1
      _showMessage(user, message, k, kcount, False)
      if k == parameters['maxMessagesPerThread']:
        break
    Ind.Decrement()
    parameters['messagesProcessed'] += 1

  def _printThread(user, result):
    if parameters['maxToProcess'] and parameters['messagesProcessed'] == parameters['maxToProcess']:
      return
    if senderMatchPattern:
      for message in result['messages']:
        if _checkSenderMatch(message):
          break
      else:
        return
    k = 0
    for message in result['messages']:
      k += 1
      _printMessage(user, message, False)
      if k == parameters['maxMessagesPerThread']:
        break
    messageThreadCounts['threads'] += 1
    parameters['messagesProcessed'] += 1

  def _countThreadLabels(user, result):
    for message in result['messages']:
      _countMessageLabels(user, message)

  def _countThreads(_, result):
    if senderMatchPattern:
      for message in result['messages']:
        if _checkSenderMatchCount(message):
          messageThreadCounts['size'] += message['sizeEstimate']
          break
      else:
        return
    else:
      k = 0
      for message in result['messages']:
        k += 1
        messageThreadCounts['size'] += message['sizeEstimate']
        if k == parameters['maxMessagesPerThread']:
          break
    messageThreadCounts['threads'] += 1

  _GMAIL_ERROR_REASON_TO_MESSAGE_MAP = {GAPI.NOT_FOUND: Msg.DOES_NOT_EXIST, GAPI.INVALID_MESSAGE_ID: Msg.INVALID_MESSAGE_ID}

  def _handleGmailError(exception, ri):
    http_status, reason, message = checkGAPIError(exception)
    errMsg = getHTTPError(_GMAIL_ERROR_REASON_TO_MESSAGE_MAP, http_status, reason, message)
    if reason not in GAPI.DEFAULT_RETRY_REASONS:
      if not csvPF:
        printKeyValueListWithCount([Ent.Singular(entityType), ri[RI_ITEM], errMsg], int(ri[RI_J]), int(ri[RI_JCOUNT]))
        setSysExitRC(ACTION_FAILED_RC)
      else:
        entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], errMsg, int(ri[RI_J]), int(ri[RI_JCOUNT]))
      return
    try:
      response = callGAPI(service, 'get',
                          throwReasons=GAPI.GMAIL_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.INVALID_MESSAGE_ID],
                          userId='me', id=ri[RI_ITEM], format=['metadata', 'full'][show_size or show_body or show_attachments or save_attachments or upload_attachments])
      if countsOnly:
        _callbacks['process'](ri[RI_ENTITY], response)
      else:
        if not csvPF:
          _callbacks['process'](ri[RI_ENTITY], response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
        else:
          _callbacks['process'](ri[RI_ENTITY], response)
    except GAPI.notFound:
      entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], Msg.DOES_NOT_EXIST, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    except GAPI.invalidMessageId:
      entityActionFailedWarning([Ent.USER, ri[RI_ENTITY], entityType, ri[RI_ITEM]], Msg.INVALID_MESSAGE_ID, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(ri[RI_ENTITY], int(ri[RI_I]), int(ri[RI_COUNT]))

  def _callbackShow(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _callbacks['process'](ri[RI_ENTITY], response, int(ri[RI_J]), int(ri[RI_JCOUNT]))
    else:
      _handleGmailError(exception, ri)

  def _callbackPrint(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _callbacks['process'](ri[RI_ENTITY], response)
    else:
      _handleGmailError(exception, ri)

  def _callbackCountLabels(request_id, response, exception):
    ri = request_id.splitlines()
    if exception is None:
      _callbacks['process'](ri[RI_ENTITY], response)
    else:
      _handleGmailError(exception, ri)

  def _batchPrintShowMessagesThreads(service, user, jcount, messageIds):
    svcargs = dict([('userId', 'me'), ('id', None), ('format', ['metadata', 'full'][show_body or show_attachments or save_attachments or upload_attachments])]+GM.Globals[GM.EXTRA_ARGS_LIST])
    if countsOnly:
      if show_labels:
        if not senderMatchPattern:
          svcargs['fields'] = 'labelIds,sizeEstimate' if entityType == Ent.MESSAGE else 'messages(labelIds,sizeEstimate)'
        else:
          svcargs['fields'] = 'labelIds,sizeEstimate,payload' if entityType == Ent.MESSAGE else 'messages(labelIds,sizeEstimate,payload)'
      else:
        if not senderMatchPattern:
          svcargs['fields'] = 'sizeEstimate' if entityType == Ent.MESSAGE else 'messages(sizeEstimate)'
        else:
          svcargs['fields'] = 'sizeEstimate,payload' if entityType == Ent.MESSAGE else 'messages(sizeEstimate,payload)'
    method = getattr(service, 'get')
    dbatch = gmail.new_batch_http_request(callback=_callbacks['batch'])
    bcount = 0
    j = 0
    for messageId in messageIds:
      j += 1
      svcparms = svcargs.copy()
      svcparms['id'] = messageId
      dbatch.add(method(**svcparms), request_id=batchRequestID(user, 0, 0, j, jcount, svcparms['id']))
      bcount += 1
      if not labelMatchPattern and parameters['maxToProcess'] and j == parameters['maxToProcess']:
        break
      if bcount == GC.Values[GC.EMAIL_BATCH_SIZE]:
        executeBatch(dbatch)
        dbatch = gmail.new_batch_http_request(callback=_callbacks['batch'])
        bcount = 0
        if labelMatchPattern and parameters['messagesProcessed'] == parameters['maxToProcess']:
          break
    if bcount > 0:
      dbatch.execute()

  parameters = _initMessageThreadParameters(entityType, True, 0)
  convertCRNL = GC.Values[GC.CSV_OUTPUT_CONVERT_CR_NL]
  delimiter = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER]
  countsOnly = positiveCountsOnly = includeSpamTrash = onlyUser = overwrite = save_attachments = upload_attachments = False
  show_all_headers = show_attachments = show_body = show_date = show_html = show_labels = show_size = show_snippet = False
  noshow_text_plain = False
  attachmentNamePattern = None
  targetFolderPattern = GC.Values[GC.DRIVE_DIR]
  defaultHeaders = ['Date', 'Subject', 'From', 'Reply-To', 'To', 'Delivered-To', 'Content-Type', 'Message-ID']
  headersToShow = [header.lower() for header in defaultHeaders]
  csvPF = CSVPrintFile() if Act.csvFormat() else None
  showMode = Act.Get() == Act.SHOW
  dateHeaderFormat = ''
  dateHeaderConvertTimezone = False
  uploadAttachmentBody = {}
  addCSVData = {}
  parentParms = initDriveFileAttributes()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif _getMessageSelectParameters(myarg, parameters):
      pass
    elif myarg == 'headers':
      headersToShow = getString(Cmd.OB_STRING, minLen=0).lower().replace(',', ' ').split()
      show_all_headers = headersToShow and headersToShow[0] == 'all'
    elif not showMode and myarg in {'convertcrnl', 'converttextnl', 'convertbodynl'}:
      convertCRNL = True
    elif myarg == 'delimiter':
      delimiter = getCharacter()
    elif myarg == 'showdate':
      show_date = True
    elif myarg == 'showbody':
      show_body = True
    elif myarg == 'showhtml':
      show_html = True
    elif myarg == 'showlabels':
      show_labels = True
    elif myarg == 'showsize':
      show_size = True
    elif myarg == 'showsnippet':
      show_snippet = True
    elif myarg == 'showattachments':
      show_attachments = True
    elif myarg == 'noshowtextplain':
      noshow_text_plain = True
    elif myarg == 'attachmentnamepattern':
      attachmentNamePattern = getREPattern(re.IGNORECASE)
    elif showMode and myarg == 'saveattachments':
      save_attachments = True
    elif showMode and myarg == 'targetfolder':
      targetFolderPattern = setFilePath(getString(Cmd.OB_FILE_PATH), GC.DRIVE_DIR)
    elif showMode and myarg == 'overwrite':
      overwrite = getBoolean()
    elif showMode and myarg == 'uploadattachments':
      upload_attachments = True
    elif showMode and getDriveFileParentAttribute(myarg, parentParms):
      pass
    elif myarg == 'includespamtrash':
      includeSpamTrash = True
    elif myarg == 'countsonly':
      countsOnly = True
    elif myarg == 'positivecountsonly':
      countsOnly = positiveCountsOnly = True
    elif myarg in {'onlyuser', 'useronly'}:
      onlyUser = getBoolean()
    elif myarg == 'dateheaderformat':
      dateHeaderFormat = getString(Cmd.OB_STRING, minLen=0)
      if dateHeaderFormat == 'iso':
        dateHeaderFormat = IS08601_TIME_FORMAT
      elif dateHeaderFormat == 'rfc2822':
        dateHeaderFormat = RFC2822_TIME_FORMAT
    elif myarg == 'dateheaderconverttimezone':
      dateHeaderConvertTimezone = getBoolean()
      if not dateHeaderFormat:
        dateHeaderFormat = RFC2822_TIME_FORMAT
    elif csvPF and myarg == 'addcsvdata':
      getAddCSVData(addCSVData)
    else:
      unknownArgumentExit()
  labelMatchPattern = parameters['labelMatchPattern']
  senderMatchPattern = parameters['senderMatchPattern']
  if senderMatchPattern and not show_all_headers and 'sender' not in headersToShow:
    headersToShow.append('sender')
  _finalizeMessageSelectParameters(parameters, False)
  if csvPF:
    if countsOnly:
      if show_labels:
        if not senderMatchPattern:
          sortTitles = ['User']
        else:
          sortTitles = ['User', 'Sender']
        csvPF.SetIndexedTitles(['Labels'])
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessageLabels if entityType == Ent.MESSAGE else _countThreadLabels}
      else:
        if not senderMatchPattern:
          sortTitles = ['User', parameters['listType']]
        else:
          sortTitles = ['User', 'Sender', parameters['listType']]
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessages if entityType == Ent.MESSAGE else _countThreads}
      if show_size:
        sortTitles.append('size')
      if addCSVData:
        sortTitles.extend(sorted(addCSVData.keys()))
      csvPF.SetTitles(sortTitles)
    else:
      sortTitles = ['User', 'threadId', 'id']
      if show_all_headers:
        sortTitles.extend(defaultHeaders)
      elif headersToShow:
        sortTitles.extend([SMTP_HEADERS_MAP.get(header, header) for header in headersToShow])
      if show_size:
        sortTitles.append('SizeEstimate')
      if show_labels:
        sortTitles.extend(['LabelsCount', 'Labels'])
      if show_snippet:
        sortTitles.append('Snippet')
      if show_body:
        sortTitles.append('Body')
      if addCSVData:
        sortTitles.extend(sorted(addCSVData.keys()))
      _callbacks = {'batch': _callbackPrint, 'process': _printMessage if entityType == Ent.MESSAGE else _printThread}
    csvPF.SetTitles(sortTitles)
    csvPF.SetSortTitles(sortTitles)
  else:
    if countsOnly:
      if show_labels:
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessageLabels if entityType == Ent.MESSAGE else _countThreadLabels}
      else:
        _callbacks = {'batch': _callbackCountLabels, 'process': _countMessages if entityType == Ent.MESSAGE else _countThreads}
    else:
      _callbacks = {'batch': _callbackShow, 'process': _showMessage if entityType == Ent.MESSAGE else _showThread}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail, messageIds = _validateUserGetMessageIds(user, i, count, parameters['messageEntity'])
    if not gmail:
      continue
    service = gmail.users().messages() if entityType == Ent.MESSAGE else gmail.users().threads()
    if upload_attachments:
      _, drive = buildGAPIServiceObject(API.DRIVE3, user, i, count)
      if not drive:
        continue
      if not _getDriveFileParentInfo(drive, user, i, count, uploadAttachmentBody, parentParms):
        continue
    if show_labels or labelMatchPattern:
      labels = _getUserGmailLabels(gmail, user, i, count, 'labels(id,name,type)')
      if not labels:
        continue
      senderLabelsMaps = {}
      if not senderMatchPattern:
        _initSenderLabelsMap(user)
    messageThreadCounts = {'User': user, parameters['listType']: 0, 'size': 0}
    if addCSVData:
      messageThreadCounts.update(addCSVData)
    senderCounts = {}
    if save_attachments:
      _, userName, _ = splitEmailAddressOrUID(user)
      targetFolder = _substituteForUser(targetFolderPattern, user, userName)
      if not os.path.isdir(targetFolder):
        os.makedirs(targetFolder)
    try:
      if parameters['messageEntity'] is None:
        printGettingAllEntityItemsForWhom(entityType, user, i, count, query=parameters['query'])
        listResult = callGAPIpages(service, 'list', parameters['listType'],
                                   pageMessage=getPageMessageForWhom(), maxItems=parameters['maxItems'],
                                   throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                                   userId='me', q=parameters['query'], labelIds=parameters['labelIds'],
                                   fields=parameters['fields'], includeSpamTrash=includeSpamTrash,
                                   maxResults=GC.Values[GC.MESSAGE_MAX_RESULTS])
        messageIds = [message['id'] for message in listResult]
      else:
        # Need to get authorization set up for batch
        callGAPI(gmail.users(), 'getProfile',
                 throwReasons=GAPI.GMAIL_THROW_REASONS+GAPI.GMAIL_LIST_THROW_REASONS,
                 userId='me', fields='')
    except (GAPI.failedPrecondition, GAPI.permissionDenied, GAPI.invalid, GAPI.invalidArgument) as e:
      entityActionFailedWarning([Ent.USER, user], str(e), i, count)
      continue
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
      continue
    jcount = len(messageIds)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    if countsOnly and not show_labels and not senderMatchPattern and not show_size:
      if not positiveCountsOnly or jcount > 0:
        if not csvPF:
          printEntityKVList([Ent.USER, user], [parameters['listType'], jcount], i, count)
        else:
          row = {'User': user, parameters['listType']: jcount}
          if addCSVData:
            row.update(addCSVData)
          csvPF.WriteRow(row)
      continue
    if not csvPF and not countsOnly:
      if (parameters['messageEntity'] is not None or
          ((parameters['maxToProcess'] == 0 or jcount <= parameters['maxToProcess']) and
           (not labelMatchPattern and not senderMatchPattern))):
        entityPerformActionNumItems([Ent.USER, user], jcount, entityType, i, count)
      elif not labelMatchPattern and not senderMatchPattern:
        entityPerformActionNumItemsModifier([Ent.USER, user], parameters['maxToProcess'], entityType, f'of {jcount} Total {Ent.Plural(entityType)}', i, count)
      else:
        entityPerformActionModifierNumItemsModifier([Ent.USER, user], Msg.MAXIMUM_OF, parameters['maxToProcess'] or jcount, entityType,
                                                    f'of {jcount} Total {Ent.Plural(entityType)}', i, count)
    if parameters['messageEntity'] is None and not labelMatchPattern and parameters['maxToProcess'] and (jcount > parameters['maxToProcess']):
      jcount = parameters['maxToProcess']
    parameters['messagesProcessed'] = 0
    if not csvPF:
      Ind.Increment()
      _batchPrintShowMessagesThreads(service, user, jcount, messageIds)
      Ind.Decrement()
    else:
      _batchPrintShowMessagesThreads(service, user, jcount, messageIds)
    if countsOnly:
      if show_labels:
        if onlyUser or positiveCountsOnly or labelMatchPattern:
          for sender in senderLabelsMaps:
            userLabelsMap = {}
            for labelId, label in senderLabelsMaps[sender].items():
              if (label['match'] and
                  (not onlyUser or label['type'] != LABEL_TYPE_SYSTEM) and
                  (not positiveCountsOnly or label['count'] > 0)):
                userLabelsMap[labelId] = label
            senderLabelsMaps[sender] = userLabelsMap
        if not csvPF:
          for sender, labelsMap in sorted(senderLabelsMaps.items()):
            jcount = len(labelsMap)
            kvlist = [Ent.USER, user]
            if senderMatchPattern:
              kvlist.extend([Ent.SENDER, sender])
            entityPerformActionNumItems(kvlist, jcount, Ent.LABEL, i, count)
            Ind.Increment()
            j = 0
            for label in sorted(labelsMap.values(), key=lambda k: k['name']):
              j += 1
              if not show_size:
                printEntityKVList([Ent.LABEL, label['name']], ['Count', label['count'], 'Type', label['type']], j, jcount)
              else:
                printEntityKVList([Ent.LABEL, label['name']], ['Count', label['count'], 'Size', label['size'], 'Type', label['type']], j, jcount)
            Ind.Decrement()
        else:
          for sender, labelsMap in sorted(senderLabelsMaps.items()):
            row = {'User': user}
            if senderMatchPattern:
              row['Sender'] = sender
            if not show_size:
              for label in labelsMap.values():
                label.pop('size', None)
            if addCSVData:
              row.update(addCSVData)
            csvPF.WriteRowTitles(flattenJSON({'Labels': sorted(labelsMap.values(), key=lambda k: k['name'])}, flattened=row))
      elif not senderMatchPattern:
        v = messageThreadCounts[parameters['listType']]
        if not positiveCountsOnly or v > 0:
          if not csvPF:
            if not show_size:
              printEntityKVList([Ent.USER, user], [parameters['listType'], v], i, count)
            else:
              printEntityKVList([Ent.USER, user], [parameters['listType'], v, 'size', messageThreadCounts['size']], i, count)
          else:
            if not show_size:
              messageThreadCounts.pop('size', None)
            csvPF.WriteRow(messageThreadCounts)
      else:
        if not show_size:
          if not csvPF:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                printEntityKVList([Ent.USER, user, Ent.SENDER, k], [parameters['listType'], v['count']], i, count)
          else:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                row = {'User': user, 'Sender': k, parameters['listType']: v['count']}
                if addCSVData:
                  row.update(addCSVData)
                csvPF.WriteRow(row)
        else:
          if not csvPF:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                printEntityKVList([Ent.USER, user, Ent.SENDER, k], [parameters['listType'], v['count'], 'size', v['size']], i, count)
          else:
            for k, v in sorted(senderCounts.items()):
              if not positiveCountsOnly or v['count'] > 0:
                row = {'User': user, 'Sender': k, parameters['listType']: v['count'], 'size': v['size']}
                if addCSVData:
                  row.update(addCSVData)
                csvPF.WriteRow(row)
  if csvPF:
    if not countsOnly:
      csvPF.RemoveTitles(['SizeEstimate', 'LabelsCount', 'Labels', 'Snippet', 'Body'])
      if show_size:
        csvPF.AddTitle('SizeEstimate')
      if show_labels:
        csvPF.AddTitles(['LabelsCount', 'Labels'])
      if show_snippet:
        csvPF.AddTitle('Snippet')
      if show_body:
        csvPF.AddTitle('Body')
      csvPF.SetSortAllTitles()
      csvPF.writeCSVfile('Messages')
    else:
      csvPF.writeCSVfile('Message Counts' if not show_labels else 'Message Label Counts')

# gam <UserTypeEntity> print message|messages [todrive <ToDriveAttribute>*]
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_print <Number>] [includespamtrash])|(ids <MessageIDEntity>)
#	[labelmatchpattern <REMatchPattern>] [sendermatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [useronly] [delimiter <Character>] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[convertcrnl] [delimiter <Character>]
#	[countsonly|positivecountsonly] [useronly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]]
#	(addcsvdata <FieldName> <String>)*
# gam <UserTypeEntity> show message|messages
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <MessageIDEntity>)
#	[labelmatchpattern <REMatchPattern>] [sendermatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [useronly] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[countsonly|positivecountsonly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]
#	    [saveattachments [targetfolder <FilePath>] [overwrite [<Boolean>]]]
#	    [uploadattachments [<DriveFileParentAttribute>]]]
def printShowMessages(users):
  printShowMessagesThreads(users, Ent.MESSAGE)

# gam <UserTypeEntity> print thread|threads [todrive <ToDriveAttribute>*]
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_print <Number>] [includespamtrash])|(ids <ThreadIDEntity>)
#	[labelmatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[convertcrnl] [delimiter <Character>]
#	[countsonly|positivecountsonly] [useronly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]]
#	(addcsvdata <FieldName> <String>)*
# gam <UserTypeEntity> show thread|threads
#	(((query <QueryGmail> [querytime<String> <Date>]*) (matchlabel <LabelName>) [or|and])*
#	 [labelids <LabelIDList>]
#	 [quick|notquick] [max_to_show <Number>] [includespamtrash])|(ids <ThreadIDEntity>)
#	[labelmatchpattern <REMatchPattern>]
#	[headers all|<SMTPHeaderList>] [dateheaderformat iso|rfc2822|<String>] [dateheaderconverttimezone [<Boolean>]]
#	[showlabels] [showbody] [showhtml] [showdate] [showsize] [showsnippet]
#	[countsonly|positivecountsonly] [useronly]
#	[[attachmentnamepattern <REMatchPattern>]
#	    [showattachments [noshowtextplain]]
#	    [saveattachments [targetfolder <FilePath>] [overwrite [<Boolean>]]]
#	    [uploadattachments [<DriveFileParentAttribute>]]]
def printShowThreads(users):
  printShowMessagesThreads(users, Ent.THREAD)

