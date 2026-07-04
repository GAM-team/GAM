"""GAM alert center management."""

import json


from gamlib import api as API
from gamlib import gapi as GAPI
from gam.var import Act, Cmd, Ent, Ind
from gam.util.api import _getAdminEmail
from gam.util.svcacct import buildGAPIServiceObject
from gam.util.api_call import callGAPI, callGAPIpages
from gam.util.output import formatLocalTime
from gam.util.args import (
    OrderBy,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getString,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    entityPerformAction,
    performActionNumItems,
    printEntity,
    printKeyValueList,
    printLine,
    userAlertsServiceNotEnabledWarning,
)


def doDeleteOrUndeleteAlert():
  alertId = getString(Cmd.OB_ALERT_ID)
  if Act.Get() == Act.DELETE:
    action = 'delete'
    kwargs = {}
  else:
    action = 'undelete'
    kwargs = {'body': {}}
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  try:
    callGAPI(ac.alerts(), action,
             throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND],
             alertId=alertId, **kwargs)
    entityActionPerformed([Ent.ALERT, alertId])
  except GAPI.notFound as e:
    entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    userAlertsServiceNotEnabledWarning(user)

def _showAlertSettings(settings):
  notifications = settings.get('notifications', [])
  count = len(notifications)
  entityPerformAction([Ent.ALERT_SETTINGS, None])
  i = 0
  for notification in notifications:
    i += 1
    printEntity([Ent.NOTIFICATION, None], i, count)
    Ind.Increment()
    showJSON(None, notification)
    Ind.Decrement()

# gam show alertsettings
def doShowAlertSettings():
  checkForExtraneousArguments()
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  try:
    settings = callGAPI(ac.v1beta1(), 'getSettings',
                        throwReasons=GAPI.ALERT_THROW_REASONS)
    _showAlertSettings(settings)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    userAlertsServiceNotEnabledWarning(user)

# gam update alertsettings <PubsubTopicName>
def doUpdateAlertSettings(clear=False):
  if not clear:
    body = {'notifications':
            [{'cloudPubsubTopic': {'topicName': getString(Cmd.OB_PUBSUB_TOPIC_NAME)}}]}
  else:
    body = {'notifications': []}
  checkForExtraneousArguments()
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  try:
    settings = callGAPI(ac.v1beta1(), 'updateSettings',
                        throwReasons=GAPI.ALERT_THROW_REASONS,
                        body=body)
    _showAlertSettings(settings)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    userAlertsServiceNotEnabledWarning(user)

# gam clear alertsettings
def doClearAlertSettings():
  doUpdateAlertSettings(clear=True)

ALERT_TIME_OBJECTS = {'createTime', 'startTime', 'endTime'}

def _showAlert(alert, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(alert, timeObjects=ALERT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.ALERT_ID, alert['alertId']], i, count)
  Ind.Increment()
  for field in ['createTime', 'startTime', 'endTime']:
    if field in alert:
      printKeyValueList([field, formatLocalTime(alert[field])])
  for field in ['customerId', 'type', 'source', 'deleted', 'securityInvestigationToolLink']:
    if field in alert:
      printKeyValueList([field, alert[field]])
  if 'data' in alert:
    showJSON('data', alert['data'])
  Ind.Decrement()

# gam info alert <AlertID> [formatjson]
def doInfoAlert():
  alertId = getString(Cmd.OB_ALERT_ID)
  FJQC = FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    FJQC.GetFormatJSON(myarg)
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  try:
    alert = callGAPI(ac.alerts(), 'get',
                     throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND],
                     alertId=alertId)
    _showAlert(alert, FJQC)
  except GAPI.notFound as e:
    entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    userAlertsServiceNotEnabledWarning(user)

ALERT_ORDERBY_CHOICE_MAP = {
  'createdate': 'create_time',
  'createtime': 'create_time',
  }

# gam show alerts [filter <String>] [orderby createtime [ascending|descending]]
#	[formatjson]
# gam print alerts [todrive <ToDriveAttribute>*] [filter <String>] [orderby createtime [ascending|descending]]
#	[formatjson [quotechar <Character>]]
def doPrintShowAlerts():
  csvPF = CSVPrintFile(['alertId', 'createTime']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  kwargs = {}
  OBY = OrderBy(ALERT_ORDERBY_CHOICE_MAP)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      kwargs['filter'] = getString(Cmd.OB_STRING).replace("'", '"')
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    csvPF.SetSortTitles(['alertId', 'createTime', 'startTime', 'endTime', 'customerId', 'type', 'source', 'deleted'])
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  try:
    alerts = callGAPIpages(ac.alerts(), 'list', 'alerts',
                           throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT],
                           orderBy=OBY.orderBy, **kwargs)
  except (GAPI.badRequest, GAPI.invalidArgument) as e:
    entityActionFailedWarning([Ent.ALERT, None], str(e))
    return
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    userAlertsServiceNotEnabledWarning(user)
    return
  if not csvPF:
    jcount = len(alerts)
    if not FJQC.formatJSON:
      performActionNumItems(jcount, Ent.ALERT)
    Ind.Increment()
    j = 0
    for alert in alerts:
      j += 1
      _showAlert(alert, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for alert in alerts:
      row = flattenJSON(alert, timeObjects=ALERT_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'alertId': alert['alertId'],
                                'createTime': formatLocalTime(alert['createTime']),
                                'JSON': json.dumps(cleanJSON(alert, timeObjects=ALERT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Alerts')

ALERT_TYPE_MAP = {
  'notuseful': 'NOT_USEFUL',
  'somewhatuseful': 'SOMEWHAT_USEFUL',
  'veryuseful': 'VERY_USEFUL',
  }

# gam create alertfeedback <AlertID> not_useful|somewhat_useful|very_useful
def doCreateAlertFeedback():
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  alertId = getString(Cmd.OB_ALERT_ID)
  body = {'type': getChoice(ALERT_TYPE_MAP, mapChoice=True)}
  try:
    result = callGAPI(ac.alerts().feedback(), 'create',
                      throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND],
                      alertId=alertId, body=body)
    entityActionPerformed([Ent.ALERT, alertId, Ent.ALERT_FEEDBACK_ID, result['feedbackId']])
  except GAPI.notFound as e:
    entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError):
    userAlertsServiceNotEnabledWarning(user)

def _showAlertFeedback(feedback, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(feedback, timeObjects=ALERT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.ALERT_FEEDBACK_ID, feedback['feedbackId']], i, count)
  Ind.Increment()
  for field in ['createTime']:
    if field in feedback:
      printKeyValueList([field, formatLocalTime(feedback[field])])
  for field in ['alertId', 'customerId', 'type', 'email']:
    if field in feedback:
      printKeyValueList([field, feedback[field]])
  Ind.Decrement()

ALERT_FEEDBACK_ORDERBY_CHOICE_MAP = {
  'createdate': 'createTime',
  'createtime': 'createTime',
  }

# gam show alertfeedback [alert <AlertID>] [filter <String>] [orderby createtime [ascending|descending]]
#	[formatjson]
# gam print alertfeedback [todrive <ToDriveAttribute>*] [alert <AlertID>] [filter <String>] [orderby createtime [ascending|descending]]
#	[formatjson [quotechar <Character>]]
def doPrintShowAlertFeedback():
  csvPF = CSVPrintFile(['feedbackId', 'createTime']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  kwargs = {}
  alertId = '-'
  OBY = OrderBy(ALERT_FEEDBACK_ORDERBY_CHOICE_MAP)
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'alertid':
      alertId = getString(Cmd.OB_ALERT_ID)
    elif myarg == 'filter':
      kwargs['filter'] = getString(Cmd.OB_STRING).replace("'", '"')
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    csvPF.SetSortTitles(['feedbackId', 'createTime', 'alertId', 'customerId', 'type', 'email'])
  user, ac = buildGAPIServiceObject(API.ALERTCENTER, _getAdminEmail())
  if not ac:
    return
  try:
    feedbacks = callGAPIpages(ac.alerts().feedback(), 'list', 'feedback',
                              throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.BAD_REQUEST],
                              alertId=alertId, **kwargs)
  except (GAPI.notFound, GAPI.badRequest) as e:
    entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
    return
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    userAlertsServiceNotEnabledWarning(user)
    return
  for sk in OBY.items:
    if sk.endswith(' desc'):
      field, _ = sk.split(' ')
      reverse = True
    else:
      field = sk
      reverse = False
    feedbacks = sorted(feedbacks, key=lambda k: k[field], reverse=reverse) #pylint: disable=cell-var-from-loop
  if not csvPF:
    jcount = len(feedbacks)
    if not FJQC.formatJSON:
      performActionNumItems(jcount, Ent.ALERT_FEEDBACK)
    Ind.Increment()
    j = 0
    for feedback in feedbacks:
      j += 1
      _showAlertFeedback(feedback, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for feedback in feedbacks:
      row = flattenJSON(feedback, timeObjects=ALERT_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'feedbackId': feedback['feedbackId'],
                                'createTime': formatLocalTime(feedback['createTime']),
                                'JSON': json.dumps(cleanJSON(feedback, timeObjects=ALERT_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Alert Feedbacks')

