"""Gmail profile and watch operations.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re
import json
import sys

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

def watchGmail(users):
  maxMessages = 100
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'maxmessages':
      maxMessages = _getMain().getInteger(minVal=1)
    else:
      _getMain().unknownArgumentExit()
  project = f'projects/{_getCurrentProjectId()}'
  gamTopics = project+'/topics/gam-pubsub-gmail-'
  gamSubscriptions = project+'/subscriptions/gam-pubsub-gmail-'
  pubsub = _getMain().buildGAPIObject(API.PUBSUB)
  topics = _getMain().callGAPIpages(pubsub.projects().topics(), 'list', items='topics',
                         project=project)
  for atopic in topics:
    if atopic['name'].startswith(gamTopics):
      topic = atopic['name']
      break
  else:
    topic = gamTopics+str(uuid.uuid4())
    _getMain().callGAPI(pubsub.projects().topics(), 'create',
             name=topic)
    body = {'policy': {'bindings': [{'members': ['serviceAccount:gmail-api-push@system.gserviceaccount.com'], 'role': 'roles/pubsub.editor'}]}}
    _getMain().callGAPI(pubsub.projects().topics(), 'setIamPolicy',
             resource=topic, body=body)
  subscriptions = _getMain().callGAPIpages(pubsub.projects().topics().subscriptions(), 'list', items='subscriptions',
                                topic=topic)
  for asubscription in subscriptions:
    if asubscription.startswith(gamSubscriptions):
      subscription = asubscription
      break
  else:
    subscription = gamSubscriptions+str(uuid.uuid4())
    _getMain().callGAPI(pubsub.projects().subscriptions(), 'create',
             name=subscription, body={'topic': topic})
  gmails = {}
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    gmails[user] = {'g': gmail}
    _getMain().callGAPI(gmails[user]['g'].users(), 'watch',
             userId='me', body={'topicName': topic})
    gmails[user]['seen_historyId'] = _getMain().callGAPI(gmails[user]['g'].users(), 'getProfile',
                                              userId='me', fields='historyId')['historyId']
  _getMain().entityPerformActionNumItems([Ent.EVENT, 'gmail'], count, Ent.USER)
  while True:
    results = _getMain().callGAPI(pubsub.projects().subscriptions(), 'pull',
                       subscription=subscription, body={'maxMessages': maxMessages})
    if 'receivedMessages' in results:
      ackIds = []
      update_history = []
      for message in results['receivedMessages']:
        if 'data' in message['message']:
          try:
            decoded_message = json.loads(base64.b64decode(message['message']['data']))
            if 'historyId' in decoded_message:
              update_history.append(decoded_message['emailAddress'])
          except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
            pass
        if 'ackId' in message:
          ackIds.append(message['ackId'])
      if ackIds:
        _getMain().callGAPI(pubsub.projects().subscriptions(), 'acknowledge',
                 subscription=subscription, body={'ackIds': ackIds})
      if update_history:
        for a_user in update_history:
          results = _getMain().callGAPI(gmails[a_user]['g'].users().history(), 'list',
                             userId='me', startHistoryId=gmails[a_user]['seen_historyId'])
          if 'history' in results:
            for history in results['history']:
              if list(history) == ['messages', 'id']:
                continue
              if 'labelsAdded' in history:
                Act.Set(Act.ADD)
                for labelling in history['labelsAdded']:
                  _getMain().entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, labelling['message']['id'],
                                         Ent.LABEL, ', '.join(labelling['labelIds'])])
              if 'labelsRemoved' in history:
                Act.Set(Act.REMOVE)
                for labelling in history['labelsRemoved']:
                  _getMain().entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, labelling['message']['id'],
                                         Ent.LABEL, ', '.join(labelling['labelIds'])])
              if 'messagesAdded' in history:
                Act.Set(Act.CREATE)
                for adding in history['messagesAdded']:
                  _getMain().entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, adding['message']['id'],
                                         Ent.LABEL, ', '.join(adding['message']['labelIds'])])
              if 'messagesDeleted' in history:
                Act.Set(Act.DELETE)
                for deleting in history['messagesDeleted']:
                  _getMain().entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, deleting['message']['id']])
          gmails[a_user]['seen_historyId'] = results['historyId']

# gam <UserTypeEntity> print gmailprofile [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show gmailprofile
def printShowGmailProfile(users):
  csvPF = _getMain().CSVPrintFile(['emailAddress'], 'sortall') if Act.csvFormat() else None
  _getMain().getTodriveOnly(csvPF)
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = _getMain().buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      _getMain().printGettingEntityItemForWhom(Ent.GMAIL_PROFILE, user, i, count)
    try:
      results = _getMain().callGAPI(gmail.users(), 'getProfile',
                         throwReasons=GAPI.GMAIL_THROW_REASONS,
                         userId='me')
      if not csvPF:
        kvList = []
        for item in ['historyId', 'messagesTotal', 'threadsTotal']:
          kvList += [item, results[item]]
        _getMain().printEntityKVList([Ent.USER, user], kvList, i, count)
      else:
        csvPF.WriteRowTitles(results)
    except GAPI.serviceNotAvailable:
      _getMain().userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Gmail Profiles')

