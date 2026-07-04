"""GAM email utilities.

Email attachment handling and sending via Gmail API or SMTP.
"""

import base64
import mimetypes
import os
import smtplib
import ssl
import sys

from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glgapi as GAPI
from util.api import _getAdminEmail, buildGAPIObject, buildGAPIServiceObject, callGAPI
from util.args import NAME_EMAIL_ADDRESS_PATTERN, UTF8, normalizeEmailAddressOrUID
from util.display import entityActionFailedWarning, entityActionPerformed, entityActionPerformedMessage
from util.errors import usageErrorExit
from util.fileio import readFile, setFilePath




# Add attachements to an email message
def _addAttachmentsToMessage(message, attachments):
  for attachment in attachments:
    try:
      attachFilename = setFilePath(attachment[0], GC.INPUT_DIR)
      attachContentType, attachEncoding = mimetypes.guess_type(attachFilename)
      if attachContentType is None or attachEncoding is not None:
        attachContentType = 'application/octet-stream'
      main_type, sub_type = attachContentType.split('/', 1)
      if main_type == 'text':
        msg = MIMEText(readFile(attachFilename, 'r', attachment[1]), _subtype=sub_type, _charset=UTF8)
      elif main_type == 'image':
        msg = MIMEImage(readFile(attachFilename, 'rb'), _subtype=sub_type)
      elif main_type == 'audio':
        msg = MIMEAudio(readFile(attachFilename, 'rb'), _subtype=sub_type)
      elif main_type == 'application':
        msg = MIMEApplication(readFile(attachFilename, 'rb'), _subtype=sub_type)
      else:
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(readFile(attachFilename, 'rb'))
      msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachFilename))
      message.attach(msg)
    except (IOError, UnicodeDecodeError) as e:
      usageErrorExit(f'{attachFilename}: {str(e)}')

# Add embedded images to an email message
def _addEmbeddedImagesToMessage(message, embeddedImages):
  for embeddedImage in embeddedImages:
    try:
      imageFilename = setFilePath(embeddedImage[0], GC.INPUT_DIR)
      imageContentType, imageEncoding = mimetypes.guess_type(imageFilename)
      if imageContentType is None or imageEncoding is not None:
        imageContentType = 'application/octet-stream'
      main_type, sub_type = imageContentType.split('/', 1)
      if main_type == 'image':
        msg = MIMEImage(readFile(imageFilename, 'rb'), _subtype=sub_type)
      else:
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(readFile(imageFilename, 'rb'))
      msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(imageFilename))
      msg.add_header('Content-ID', f'<{embeddedImage[1]}>')
      message.attach(msg)
    except (IOError, UnicodeDecodeError) as e:
      usageErrorExit(f'{imageFilename}: {str(e)}')

# Send an email
def send_email(msgSubject, msgBody, msgTo, i=0, count=0, clientAccess=False, msgFrom=None, msgReplyTo=None,
               html=False, charset=None, attachments=None, embeddedImages=None,
               msgHeaders=None, ccRecipients=None, bccRecipients=None, mailBox=None, threadId=None,
               action=None):
  if charset is None:
    charset = UTF8
  if action is None:
    action = Act.SENDEMAIL

  def checkResult(entityType, recipients):
    if not recipients:
      return
    toSent = set(recipients.split(','))
    toFailed = {}
    for addr, err in result.items():
      if addr in toSent:
        toSent.remove(addr)
        toFailed[addr] = f'{err[0]}: {err[1]}'
    if toSent:
      entityActionPerformed([entityType, ','.join(toSent), Ent.MESSAGE, msgSubject], i, count)
    for addr, errMsg in toFailed.items():
      entityActionFailedWarning([entityType, addr, Ent.MESSAGE, msgSubject], errMsg, i, count)

  def cleanAddr(emailAddr):
    match = NAME_EMAIL_ADDRESS_PATTERN.match(emailAddr)
    if match:
      emailName = match.group(1)
      emailAddr = normalizeEmailAddressOrUID(match.group(2), noUid=True, noLower=True)
      return (f'{emailName} <{emailAddr}>', emailAddr)
    emailAddr = normalizeEmailAddressOrUID(emailAddr, noUid=True, noLower=True)
    return (emailAddr, emailAddr)

  if msgFrom is None:
    msgFrom = _getAdminEmail()
  # Force ASCII for RFC compliance
  # xmlcharref seems to work to display at least
  # some unicode in HTML body and is ignored in
  # plain text body.
#  msgBody = msgBody.encode('ascii', 'xmlcharrefreplace').decode(UTF8)
  if not attachments and not embeddedImages:
    message = MIMEText(msgBody, ['plain', 'html'][html], charset)
  else:
    message = MIMEMultipart()
    msg = MIMEText(msgBody, ['plain', 'html'][html], charset)
    message.attach(msg)
    if attachments:
      _addAttachmentsToMessage(message, attachments)
    if embeddedImages:
      _addEmbeddedImagesToMessage(message, embeddedImages)
  message['Subject'] = msgSubject
  message['From'], msgFromAddr = cleanAddr(msgFrom)
  if msgReplyTo is not None:
    message['Reply-To'], _ = cleanAddr(msgReplyTo)
  if ccRecipients:
    message['Cc'] = ccRecipients.lower()
  if bccRecipients:
    message['Bcc'] = bccRecipients.lower()
  if msgHeaders:
    for header, value in msgHeaders.items():
      if header not in {'Subject', 'From', 'To', 'Reply-To', 'Cc', 'Bcc'}:
        message[header] = value
  if mailBox is None:
    mailBox = msgFromAddr
  _, mailBoxAddr = cleanAddr(mailBox)
  parentAction = Act.Get()
  Act.Set(action)
  if not GC.Values[GC.SMTP_HOST]:
    if not clientAccess:
      userId, gmail = buildGAPIServiceObject(API.GMAIL, mailBoxAddr)
      if not gmail:
        Act.Set(parentAction)
        return
    else:
      userId = mailBoxAddr
      gmail = buildGAPIObject(API.GMAIL)
    message['To'] = msgTo if msgTo else userId
    body = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
    if threadId is not None:
      body['threadId'] = threadId
    try:
      result = callGAPI(gmail.users().messages(), 'send',
                        throwReasons=[GAPI.SERVICE_NOT_AVAILABLE, GAPI.AUTH_ERROR, GAPI.DOMAIN_POLICY,
                                      GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        userId=userId, body=body, fields='id')
      entityActionPerformedMessage([Ent.RECIPIENT, msgTo, Ent.MESSAGE, msgSubject], f"{result['id']}", i, count)
    except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.domainPolicy,
            GAPI.invalid, GAPI.invalidArgument, GAPI.forbidden, GAPI.permissionDenied) as e:
      entityActionFailedWarning([Ent.RECIPIENT, msgTo, Ent.MESSAGE, msgSubject], str(e), i, count)
  else:
    message['To'] = msgTo if msgTo else mailBoxAddr
    server = None
    try:
      server = smtplib.SMTP(GC.Values[GC.SMTP_HOST], 587, GC.Values[GC.SMTP_FQDN])
      if GC.Values[GC.DEBUG_LEVEL] > 0:
        server.set_debuglevel(1)
      server.starttls(context=ssl.create_default_context(cafile=GC.Values[GC.CACERTS_PEM]))
      if GC.Values[GC.SMTP_USERNAME] and GC.Values[GC.SMTP_PASSWORD]:
        if isinstance(GC.Values[GC.SMTP_PASSWORD], bytes):
          server.login(GC.Values[GC.SMTP_USERNAME], base64.b64decode(GC.Values[GC.SMTP_PASSWORD]).decode(UTF8))
        else:
          server.login(GC.Values[GC.SMTP_USERNAME], GC.Values[GC.SMTP_PASSWORD])
      result = server.send_message(message)
      checkResult(Ent.RECIPIENT, message['To'])
      checkResult(Ent.RECIPIENT_CC, ccRecipients)
      checkResult(Ent.RECIPIENT_BCC, bccRecipients)
    except smtplib.SMTPException as e:
      entityActionFailedWarning([Ent.RECIPIENT, msgTo, Ent.MESSAGE, msgSubject], str(e), i, count)
    if server:
      try:
        server.quit()
      except Exception:
        pass
  Act.Set(parentAction)
