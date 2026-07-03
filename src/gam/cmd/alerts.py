"""GAM alert center management."""

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

def doDeleteOrUndeleteAlert():
  alertId = _getMain().getString(Cmd.OB_ALERT_ID)
  if Act.Get() == Act.DELETE:
    action = 'delete'
    kwargs = {}
  else:
    action = 'undelete'
    kwargs = {'body': {}}
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  try:
    _getMain().callGAPI(ac.alerts(), action,
             throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND],
             alertId=alertId, **kwargs)
    _getMain().entityActionPerformed([Ent.ALERT, alertId])
  except GAPI.notFound as e:
    _getMain().entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    _getMain().userAlertsServiceNotEnabledWarning(user)

def _showAlertSettings(settings):
  notifications = settings.get('notifications', [])
  count = len(notifications)
  _getMain().entityPerformAction([Ent.ALERT_SETTINGS, None])
  i = 0
  for notification in notifications:
    i += 1
    _getMain().printEntity([Ent.NOTIFICATION, None], i, count)
    Ind.Increment()
    _getMain().showJSON(None, notification)
    Ind.Decrement()

# gam show alertsettings
def doShowAlertSettings():
  _getMain().checkForExtraneousArguments()
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  try:
    settings = _getMain().callGAPI(ac.v1beta1(), 'getSettings',
                        throwReasons=GAPI.ALERT_THROW_REASONS)
    _showAlertSettings(settings)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    _getMain().userAlertsServiceNotEnabledWarning(user)

# gam update alertsettings <PubsubTopicName>
def doUpdateAlertSettings(clear=False):
  if not clear:
    body = {'notifications':
            [{'cloudPubsubTopic': {'topicName': _getMain().getString(Cmd.OB_PUBSUB_TOPIC_NAME)}}]}
  else:
    body = {'notifications': []}
  _getMain().checkForExtraneousArguments()
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  try:
    settings = _getMain().callGAPI(ac.v1beta1(), 'updateSettings',
                        throwReasons=GAPI.ALERT_THROW_REASONS,
                        body=body)
    _showAlertSettings(settings)
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    _getMain().userAlertsServiceNotEnabledWarning(user)

# gam clear alertsettings
def doClearAlertSettings():
  doUpdateAlertSettings(clear=True)

ALERT_TIME_OBJECTS = {'createTime', 'startTime', 'endTime'}

def _showAlert(alert, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(alert, timeObjects=ALERT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.ALERT_ID, alert['alertId']], i, count)
  Ind.Increment()
  for field in ['createTime', 'startTime', 'endTime']:
    if field in alert:
      _getMain().printKeyValueList([field, _getMain().formatLocalTime(alert[field])])
  for field in ['customerId', 'type', 'source', 'deleted', 'securityInvestigationToolLink']:
    if field in alert:
      _getMain().printKeyValueList([field, alert[field]])
  if 'data' in alert:
    _getMain().showJSON('data', alert['data'])
  Ind.Decrement()

# gam info alert <AlertID> [formatjson]
def doInfoAlert():
  alertId = _getMain().getString(Cmd.OB_ALERT_ID)
  FJQC = _getMain().FormatJSONQuoteChar()
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    FJQC.GetFormatJSON(myarg)
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  try:
    alert = _getMain().callGAPI(ac.alerts(), 'get',
                     throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND],
                     alertId=alertId)
    _showAlert(alert, FJQC)
  except GAPI.notFound as e:
    _getMain().entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    _getMain().userAlertsServiceNotEnabledWarning(user)

ALERT_ORDERBY_CHOICE_MAP = {
  'createdate': 'create_time',
  'createtime': 'create_time',
  }

# gam show alerts [filter <String>] [orderby createtime [ascending|descending]]
#	[formatjson]
# gam print alerts [todrive <ToDriveAttribute>*] [filter <String>] [orderby createtime [ascending|descending]]
#	[formatjson [quotechar <Character>]]
def doPrintShowAlerts():
  csvPF = _getMain().CSVPrintFile(['alertId', 'createTime']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  kwargs = {}
  OBY = _getMain().OrderBy(ALERT_ORDERBY_CHOICE_MAP)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      kwargs['filter'] = _getMain().getString(Cmd.OB_STRING).replace("'", '"')
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    csvPF.SetSortTitles(['alertId', 'createTime', 'startTime', 'endTime', 'customerId', 'type', 'source', 'deleted'])
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  try:
    alerts = _getMain().callGAPIpages(ac.alerts(), 'list', 'alerts',
                           throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.BAD_REQUEST, GAPI.INVALID_ARGUMENT],
                           orderBy=OBY.orderBy, **kwargs)
  except (GAPI.badRequest, GAPI.invalidArgument) as e:
    _getMain().entityActionFailedWarning([Ent.ALERT, None], str(e))
    return
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    _getMain().userAlertsServiceNotEnabledWarning(user)
    return
  if not csvPF:
    jcount = len(alerts)
    if not FJQC.formatJSON:
      _getMain().performActionNumItems(jcount, Ent.ALERT)
    Ind.Increment()
    j = 0
    for alert in alerts:
      j += 1
      _showAlert(alert, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for alert in alerts:
      row = _getMain().flattenJSON(alert, timeObjects=ALERT_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'alertId': alert['alertId'],
                                'createTime': formatLocalTime(alert['createTime']),
                                'JSON': json.dumps(_getMain().cleanJSON(alert, timeObjects=ALERT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Alerts')

ALERT_TYPE_MAP = {
  'notuseful': 'NOT_USEFUL',
  'somewhatuseful': 'SOMEWHAT_USEFUL',
  'veryuseful': 'VERY_USEFUL',
  }

# gam create alertfeedback <AlertID> not_useful|somewhat_useful|very_useful
def doCreateAlertFeedback():
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  alertId = _getMain().getString(Cmd.OB_ALERT_ID)
  body = {'type': _getMain().getChoice(ALERT_TYPE_MAP, mapChoice=True)}
  try:
    result = _getMain().callGAPI(ac.alerts().feedback(), 'create',
                      throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND],
                      alertId=alertId, body=body)
    _getMain().entityActionPerformed([Ent.ALERT, alertId, Ent.ALERT_FEEDBACK_ID, result['feedbackId']])
  except GAPI.notFound as e:
    _getMain().entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
  except (GAPI.serviceNotAvailable, GAPI.authError):
    _getMain().userAlertsServiceNotEnabledWarning(user)

def _showAlertFeedback(feedback, FJQC, i=0, count=0):
  if FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(feedback, timeObjects=ALERT_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.ALERT_FEEDBACK_ID, feedback['feedbackId']], i, count)
  Ind.Increment()
  for field in ['createTime']:
    if field in feedback:
      _getMain().printKeyValueList([field, _getMain().formatLocalTime(feedback[field])])
  for field in ['alertId', 'customerId', 'type', 'email']:
    if field in feedback:
      _getMain().printKeyValueList([field, feedback[field]])
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
  csvPF = _getMain().CSVPrintFile(['feedbackId', 'createTime']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  kwargs = {}
  alertId = '-'
  OBY = _getMain().OrderBy(ALERT_FEEDBACK_ORDERBY_CHOICE_MAP)
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'alertid':
      alertId = _getMain().getString(Cmd.OB_ALERT_ID)
    elif myarg == 'filter':
      kwargs['filter'] = _getMain().getString(Cmd.OB_STRING).replace("'", '"')
    elif myarg == 'orderby':
      OBY.GetChoice()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if csvPF and not FJQC.formatJSON:
    csvPF.SetSortTitles(['feedbackId', 'createTime', 'alertId', 'customerId', 'type', 'email'])
  user, ac = _getMain().buildGAPIServiceObject(API.ALERTCENTER, _getMain()._getAdminEmail())
  if not ac:
    return
  try:
    feedbacks = _getMain().callGAPIpages(ac.alerts().feedback(), 'list', 'feedback',
                              throwReasons=GAPI.ALERT_THROW_REASONS+[GAPI.NOT_FOUND, GAPI.BAD_REQUEST],
                              alertId=alertId, **kwargs)
  except (GAPI.notFound, GAPI.badRequest) as e:
    _getMain().entityActionFailedWarning([Ent.ALERT_ID, alertId], str(e))
    return
  except (GAPI.serviceNotAvailable, GAPI.authError, GAPI.permissionDenied):
    _getMain().userAlertsServiceNotEnabledWarning(user)
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
      _getMain().performActionNumItems(jcount, Ent.ALERT_FEEDBACK)
    Ind.Increment()
    j = 0
    for feedback in feedbacks:
      j += 1
      _showAlertFeedback(feedback, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for feedback in feedbacks:
      row = _getMain().flattenJSON(feedback, timeObjects=ALERT_TIME_OBJECTS)
      if not FJQC.formatJSON:
        csvPF.WriteRowTitles(row)
      elif csvPF.CheckRowTitles(row):
        csvPF.WriteRowNoFilter({'feedbackId': feedback['feedbackId'],
                                'createTime': formatLocalTime(feedback['createTime']),
                                'JSON': json.dumps(_getMain().cleanJSON(feedback, timeObjects=ALERT_TIME_OBJECTS),
                                                   ensure_ascii=False, sort_keys=True)})
  if csvPF:
    csvPF.writeCSVfile('Alert Feedbacks')

