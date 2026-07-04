"""Gmail profile and watch operations.

Part of the _gmail_monolith sub-package."""

"""GAM Gmail management: labels, messages, filters, forwarding, sendas, S/MIME, CSE, vacation."""

import re
import json
import sys
import uuid
import base64

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.util.api import buildGAPIObject
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.args import getArgument, getInteger
from gam.util.csv_pf import CSVPrintFile, getTodriveOnly
from gam.util.display import (
    entityActionPerformed,
    entityPerformActionNumItems,
    printEntityKVList,
    printGettingEntityItemForWhom,
    userGmailServiceNotEnabledWarning,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import unknownArgumentExit

from gam.var import Act, Cmd, Ent, Ind

def watchGmail(users):
  maxMessages = 100
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'maxmessages':
      maxMessages = getInteger(minVal=1)
    else:
      unknownArgumentExit()
  project = f'projects/{_getCurrentProjectId()}'
  gamTopics = project+'/topics/gam-pubsub-gmail-'
  gamSubscriptions = project+'/subscriptions/gam-pubsub-gmail-'
  pubsub = buildGAPIObject(API.PUBSUB)
  topics = callGAPIpages(pubsub.projects().topics(), 'list', items='topics',
                         project=project)
  for atopic in topics:
    if atopic['name'].startswith(gamTopics):
      topic = atopic['name']
      break
  else:
    topic = gamTopics+str(uuid.uuid4())
    callGAPI(pubsub.projects().topics(), 'create',
             name=topic)
    body = {'policy': {'bindings': [{'members': ['serviceAccount:gmail-api-push@system.gserviceaccount.com'], 'role': 'roles/pubsub.editor'}]}}
    callGAPI(pubsub.projects().topics(), 'setIamPolicy',
             resource=topic, body=body)
  subscriptions = callGAPIpages(pubsub.projects().topics().subscriptions(), 'list', items='subscriptions',
                                topic=topic)
  for asubscription in subscriptions:
    if asubscription.startswith(gamSubscriptions):
      subscription = asubscription
      break
  else:
    subscription = gamSubscriptions+str(uuid.uuid4())
    callGAPI(pubsub.projects().subscriptions(), 'create',
             name=subscription, body={'topic': topic})
  gmails = {}
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    gmails[user] = {'g': gmail}
    callGAPI(gmails[user]['g'].users(), 'watch',
             userId='me', body={'topicName': topic})
    gmails[user]['seen_historyId'] = callGAPI(gmails[user]['g'].users(), 'getProfile',
                                              userId='me', fields='historyId')['historyId']
  entityPerformActionNumItems([Ent.EVENT, 'gmail'], count, Ent.USER)
  while True:
    results = callGAPI(pubsub.projects().subscriptions(), 'pull',
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
        callGAPI(pubsub.projects().subscriptions(), 'acknowledge',
                 subscription=subscription, body={'ackIds': ackIds})
      if update_history:
        for a_user in update_history:
          results = callGAPI(gmails[a_user]['g'].users().history(), 'list',
                             userId='me', startHistoryId=gmails[a_user]['seen_historyId'])
          if 'history' in results:
            for history in results['history']:
              if list(history) == ['messages', 'id']:
                continue
              if 'labelsAdded' in history:
                Act.Set(Act.ADD)
                for labelling in history['labelsAdded']:
                  entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, labelling['message']['id'],
                                         Ent.LABEL, ', '.join(labelling['labelIds'])])
              if 'labelsRemoved' in history:
                Act.Set(Act.REMOVE)
                for labelling in history['labelsRemoved']:
                  entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, labelling['message']['id'],
                                         Ent.LABEL, ', '.join(labelling['labelIds'])])
              if 'messagesAdded' in history:
                Act.Set(Act.CREATE)
                for adding in history['messagesAdded']:
                  entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, adding['message']['id'],
                                         Ent.LABEL, ', '.join(adding['message']['labelIds'])])
              if 'messagesDeleted' in history:
                Act.Set(Act.DELETE)
                for deleting in history['messagesDeleted']:
                  entityActionPerformed([Ent.USER, a_user, Ent.MESSAGE, deleting['message']['id']])
          gmails[a_user]['seen_historyId'] = results['historyId']

# gam <UserTypeEntity> print gmailprofile [todrive <ToDriveAttribute>*]
# gam <UserTypeEntity> show gmailprofile
def printShowGmailProfile(users):
  csvPF = CSVPrintFile(['emailAddress'], 'sortall') if Act.csvFormat() else None
  getTodriveOnly(csvPF)
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, gmail = buildGAPIServiceObject(API.GMAIL, user, i, count)
    if not gmail:
      continue
    if csvPF:
      printGettingEntityItemForWhom(Ent.GMAIL_PROFILE, user, i, count)
    try:
      results = callGAPI(gmail.users(), 'getProfile',
                         throwReasons=GAPI.GMAIL_THROW_REASONS,
                         userId='me')
      if not csvPF:
        kvList = []
        for item in ['historyId', 'messagesTotal', 'threadsTotal']:
          kvList += [item, results[item]]
        printEntityKVList([Ent.USER, user], kvList, i, count)
      else:
        csvPF.WriteRowTitles(results)
    except GAPI.serviceNotAvailable:
      userGmailServiceNotEnabledWarning(user, i, count)
  if csvPF:
    csvPF.writeCSVfile('Gmail Profiles')

