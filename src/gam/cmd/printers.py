"""GAM Chrome printer management."""

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

def isolatePrinterID(name):
  ''' converts long name into simple ID'''
  return name.split('/')[-1]

def _getPrinterID():
  cd = _getMain().buildGAPIObject(API.PRINTERS)
  customer = _getMain()._getCustomersCustomerIdWithC()
  printerId = _getMain().getString(Cmd.OB_PRINTER_ID)
  pattern = re.compile(rf'^{customer}/chrome/printers/(.+)$')
  mg = pattern.match(printerId)
  if mg:
    return (printerId, mg.group(1), cd)
  return (f'{customer}/chrome/printers/{printerId}', printerId, cd)

def _getPrinterEntity():
  cd = _getMain().buildGAPIObject(API.PRINTERS)
  customer = _getMain()._getCustomersCustomerIdWithC()
  printerId = _getMain().getString(Cmd.OB_PRINTER_ID)
  entitySelector = printerId.lower()
  if entitySelector == Cmd.ENTITY_SELECTOR_FILE:
    printerIds = _getMain().getEntitiesFromFile(False)
  elif entitySelector == Cmd.ENTITY_SELECTOR_CSVFILE:
    printerIds = _getMain().getEntitiesFromCSVFile(False)
  else:
    printerIds = printerId.replace(',', ' ').split()
  pattern = re.compile(rf'^{customer}/chrome/printers/(.+)$')
  for i, printerId in enumerate(printerIds):
    mg = pattern.match(printerId)
    if mg:
      printerIds[i] = mg.group(1)
    return (customer, printerIds, cd)

CREATE_PRINTER_JSON_SKIP_FIELDS = ['id', 'name', 'createTime', 'orgUnitPath', 'auxiliaryMessages']
UPDATE_PRINTER_JSON_SKIP_FIELDS = ['id', 'name', 'createTime', 'orgUnitId', 'orgUnitPath', 'auxiliaryMessages']

def _getPrinterAttributes(cd, jsonDeleteFields):
  '''get printer attributes for create/update commands'''
  body = {}
  returnIdOnly = False
  showDetails = True
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'description':
      body['description'] = _getMain().getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'displayname':
      body['displayName'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'makeandmodel':
      body['makeAndModel'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg in {'ou', 'org', 'orgunit', 'orgunitid'}:
      _, body['orgUnitId'] = _getMain().getOrgUnitId(cd)
      body['orgUnitId'] = body['orgUnitId'][3:]
    elif myarg == 'uri':
      body['uri'] = _getMain().getString(Cmd.OB_STRING)
    elif myarg in {'driverless', 'usedriverlessconfig'}:
      body['useDriverlessConfig'] = _getMain().getBoolean()
    elif myarg == 'nodetails':
      showDetails = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'json':
      body.update(_getMain().getJSON(jsonDeleteFields))
    else:
      _getMain().unknownArgumentExit()
  if body.get('makeAndModel'):
    body.pop('useDriverlessConfig', None)
  return (body, showDetails, returnIdOnly)

PRINTER_FIELDS_CHOICE_MAP = {
  'auxiliarymessages': 'auxiliaryMessages',
  'createtime': 'createTime',
  'description': 'description',
  'displayname': 'displayName',
  'id': 'id',
  'makeandmodel': 'makeAndModel',
  'name': 'name',
  'org': 'orgUnitId',
  'orgunit': 'orgUnitId',
  'orgunitid': 'orgUnitId',
  'ou': 'orgUnitId',
  'uri': 'uri',
  'usedriverlessconfig': 'useDriverlessConfig',
  }
PRINTER_TIME_OBJECTS = {'createTime'}

def _checkPrinterInheritance(cd, printer, orgUnitId, showInherited):
  if 'orgUnitId' in printer:
    if not showInherited:
      if orgUnitId is not None and printer['orgUnitId'] != orgUnitId:
        return False
    elif orgUnitId is not None and printer['orgUnitId'] != orgUnitId:
      printer['inherited'] = True
      printer['parentOrgUnitId'] = printer['orgUnitId']
      printer['parentOrgUnitPath'] = _getMain().convertOrgUnitIDtoPath(cd, f'id:{printer["parentOrgUnitId"]}')
      printer['orgUnitId'] = orgUnitId
    else:
      printer['inherited'] = False
      printer['parentOrgUnitId'] = printer['parentOrgUnitPath'] = ''
    printer['orgUnitPath'] = _getMain().convertOrgUnitIDtoPath(cd, f'id:{printer["orgUnitId"]}')
  return True

def _showPrinter(cd, printer, FJQC, orgUnitId=None, showInherited=False, i=0, count=0):
  if not _checkPrinterInheritance(cd, printer, orgUnitId, showInherited):
    return False
  if FJQC is not None and FJQC.formatJSON:
    _getMain().printLine(json.dumps(_getMain().cleanJSON(printer, timeObjects=PRINTER_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  _getMain().printEntity([Ent.PRINTER, printer['id']], i, count)
  Ind.Increment()
  _getMain().showJSON(None, printer, timeObjects=PRINTER_TIME_OBJECTS)
  Ind.Decrement()

# gam create printer <PrinterAttribute>+ [nodetails|returnidonly]
def doCreatePrinter():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  parent = _getMain()._getCustomersCustomerIdWithC()
  body, showDetails, returnIdOnly = _getPrinterAttributes(cd, CREATE_PRINTER_JSON_SKIP_FIELDS)
  if not body.get('orgUnitId'):
    _getMain().missingArgumentExit('orgunit')
  try:
    printer = _getMain().callGAPI(cd.customers().chrome().printers(), 'create',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       parent=parent, body=body)
    if returnIdOnly:
      _getMain().writeStdout(f"{printer['id']}\n")
      return
    _getMain().entityActionPerformed([Ent.PRINTER, printer['id']])
    if showDetails:
      _showPrinter(cd, printer, None)
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.PRINTER, None], str(e))

# gam update printer <PrinterID> <PrinterAttribute>+ [nodetails|returnidonly]
def doUpdatePrinter():
  name, printerId, cd = _getPrinterID()
  body, showDetails, returnIdOnly = _getPrinterAttributes(cd, UPDATE_PRINTER_JSON_SKIP_FIELDS)
  updateMask = ','.join(list(body.keys()))
  # note clearMask seems unnecessary. Updating field to '' clears it.
  try:
    printer = _getMain().callGAPI(cd.customers().chrome().printers(), 'patch',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       name=name, updateMask=updateMask, body=body)
    if returnIdOnly:
      _getMain().writeStdout(f"{printer['id']}\n")
      return
    _getMain().entityActionPerformed([Ent.PRINTER, printerId])
    if showDetails:
      _showPrinter(cd, printer, None)
  except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.PRINTER, printerId], str(e))

# gam delete printer
#	<PrinterIDList>|
#	<FileSelector>|
#	<CSVFileSelector>
def doDeletePrinter():
  parent, printerIds, cd = _getPrinterEntity()
  # max 50 per API call
  batch_size = 50
  for chunk in range(0, len(printerIds), batch_size):
    body = {'printerIds': printerIds[chunk:chunk + batch_size]}
    result = _getMain().callGAPI(cd.customers().chrome().printers(), 'batchDeletePrinters',
                      parent=parent, body=body)
    for printerId in result.get('printerIds', []):
      _getMain().entityActionPerformed([Ent.PRINTER, printerId])
    for failure in result.get('failedPrinters', []):
      if 'printerIds' in failure:
        _getMain().entityActionFailedWarning([Ent.PRINTER, failure['printerIds']], failure.get('errorMessage', 'Unknown printer'))
      else:
        _getMain().entityActionFailedWarning([Ent.PRINTER, failure['printer']['id']], failure['errorMessage'])

# gam info printer <PrinterID>
#	[fields <PrinterFieldNameList>] [formatjson]
def doInfoPrinter():
  name, printerId, cd = _getPrinterID()
  FJQC = _getMain().FormatJSONQuoteChar()
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if _getMain().getFieldsList(myarg, PRINTER_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = _getMain().getFieldsFromFieldsList(fieldsList)
  try:
    printer = _getMain().callGAPI(cd.customers().chrome().printers(), 'get',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.PERMISSION_DENIED],
                       name=name, fields=fields)
    _showPrinter(cd, printer, FJQC)
  except GAPI.notFound:
    _getMain().entityUnknownWarning(Ent.PRINTER, f'{printerId}')
  except (GAPI.invalid, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.DEVICE, f'{printerId}'], str(e))

ORGUNIT_ENTITIES_MAP = {
  'org': Cmd.ENTITY_OU,
  'organdchildren': Cmd.ENTITY_OU_AND_CHILDREN,
  'orgs': Cmd.ENTITY_OUS,
  'orgsandchildren': Cmd.ENTITY_OUS_AND_CHILDREN,
  'ou': Cmd.ENTITY_OU,
  'ouandchildren': Cmd.ENTITY_OU_AND_CHILDREN,
  'ous': Cmd.ENTITY_OUS,
  'ousandchildren': Cmd.ENTITY_OUS_AND_CHILDREN,
  'orgunit': Cmd.ENTITY_OU,
  'orgunitandchildren': Cmd.ENTITY_OU_AND_CHILDREN,
  'orgunits': Cmd.ENTITY_OUS,
  'orgunitsandchildren': Cmd.ENTITY_OUS_AND_CHILDREN,
  }

# gam show printers
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[filter <String>] [showinherited [<Boolean>]
#	[fields <PrinterFieldNameList>] [formatjson]
# gam print printers [todrive <ToDriveAttribute>*]
#	[(ou <OrgUnitItem>)|(ou_and_children <OrgUnitItem>)|
#	 (ous <OrgUnitList>)|(ous_and_children <OrgUnitList>)]
#	[filter <String>] [showinherited [<Boolean>]
#	[fields <PrinterFieldNameList>] [[formatjson [quotechar <Character>]]
def doPrintShowPrinters():
  def _printPrinter(printer):
    if not _checkPrinterInheritance(cd, printer, orgUnitId, showInherited):
      return False
    row = _getMain().flattenJSON(printer, timeObjects=PRINTER_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'id': printer['id'],
                              'JSON': json.dumps(_getMain().cleanJSON(printer, timeObjects=PRINTER_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  parent = _getMain()._getCustomersCustomerIdWithC()
  csvPF = _getMain().CSVPrintFile(['id']) if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  fieldsList = []
  ous = [None]
  directlyInOU = True
  pfilter = None
  showInherited = False
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in ORGUNIT_ENTITIES_MAP:
      myarg = ORGUNIT_ENTITIES_MAP[myarg]
      ous = _getMain().convertEntityToList(_getMain().getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    elif _getMain().getFieldsList(myarg, PRINTER_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    elif myarg == 'filter':
      pfilter = _getMain().getString(Cmd.OB_STRING)
    elif myarg == 'showinherited':
      showInherited = _getMain().getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if fieldsList and (not directlyInOU or showInherited):
    fieldsList.append('orgUnitId')
  fields = _getMain().getItemFieldsFromFieldsList('printers', fieldsList)
  for ou in ous:
    if ou is not None:
      ou = _getMain().makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = _getMain().getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = _getMain().callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=_getMain().makeOrgUnitPathRelative(ou),
                        type='all', fields='organizationUnits(orgUnitPath,orgUnitId)')
      except (GAPI.invalidOrgunit, GAPI.orgunitNotFound, GAPI.backendError, GAPI.badRequest, GAPI.invalidCustomerId, GAPI.loginRequired):
        checkEntityDNEorAccessErrorExit(cd, Ent.ORGANIZATIONAL_UNIT, ou)
        return
      ouList.extend([(subou['orgUnitPath'], subou['orgUnitId'][3:]) for subou in sorted(orgs.get('organizationUnits', []), key=lambda k: k['orgUnitPath'])])
    for subou in ouList:
      orgUnitPath = subou[0]
      orgUnitId = subou[1]
      if orgUnitId is not None:
        oneQualifier = Msg.DIRECTLY_IN_THE.format(Ent.Singular(Ent.ORGANIZATIONAL_UNIT))
        _getMain().printGettingAllEntityItemsForWhom(Ent.PRINTER, orgUnitPath, qualifier=oneQualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
        pageMessage = _getMain().getPageMessageForWhom()
      else:
        _getMain().printGettingAllAccountEntities(Ent.PRINTER, pfilter)
        pageMessage = _getMain().getPageMessage()
      try:
        printers = _getMain().callGAPIpages(cd.customers().chrome().printers(), 'list', 'printers',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.INVALID, GAPI.PERMISSION_DENIED],
                                 parent=parent, orgUnitId=orgUnitId, filter=pfilter, fields=fields)
      except (GAPI.invalid, GAPI.permissionDenied) as e:
        _getMain().entityActionFailedWarning([Ent.PRINTER, None], str(e))
        return
      if not csvPF:
        jcount = len(printers)
        if not FJQC.formatJSON:
          _getMain().performActionNumItems(jcount, Ent.PRINTER)
        Ind.Increment()
        j = 0
        for printer in printers:
          j += 1
          _showPrinter(cd, printer, FJQC, orgUnitId, showInherited, j, jcount)
        Ind.Decrement()
      else:
        for printer in printers:
          _printPrinter(printer)
  if csvPF:
    csvPF.writeCSVfile('Printers')

# gam print printermodels [todrive <ToDriveAttribute>*]
#	[filter <String>]
#	[[formatjson [quotechar <Character>]]
# gam show printermodels
#	[filter <String>]
#	[formatjson]
def doPrintShowPrinterModels():
  def _showPrinterModel(model, FJQC, i, count):
    if FJQC.formatJSON:
      _getMain().printLine(json.dumps(_getMain().cleanJSON(model), ensure_ascii=False, sort_keys=True))
      return
    _getMain().printEntity([Ent.PRINTER_MODEL, model['manufacturer']], i, count)
    Ind.Increment()
    for field in ['displayName', 'makeAndModel']:
      _getMain().printKeyValueList([field, model[field]])
    Ind.Decrement()

  def _printPrinterModel(model):
    row = _getMain().flattenJSON(model)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'JSON': json.dumps(_getMain().cleanJSON(model),
                                                 ensure_ascii=False, sort_keys=True)})

  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  parent = _getMain()._getCustomersCustomerIdWithC()
  csvPF = _getMain().CSVPrintFile() if Act.csvFormat() else None
  FJQC = _getMain().FormatJSONQuoteChar(csvPF)
  pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      pfilter = _getMain().getString(Cmd.OB_STRING)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not FJQC.formatJSON:
    csvPF.SetTitles(['manufacturer', 'displayName', 'makeAndModel'])
    csvPF.SetSortAllTitles()
  _getMain().printGettingAllAccountEntities(Ent.PRINTER_MODEL, pfilter)
  pageMessage = _getMain().getPageMessage()
  try:
    models = _getMain().callGAPIpages(cd.customers().chrome().printers(), 'listPrinterModels', 'printerModels',
                           throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                           pageMessage=pageMessage,
                           parent=parent, pageSize=10000, filter=pfilter)
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    _getMain().entityActionFailedWarning([Ent.PRINTER_MODEL, None], str(e))
    return
  if not csvPF:
    jcount = len(models)
    if not FJQC.formatJSON:
      _getMain().performActionNumItems(jcount, Ent.PRINTER_MODEL)
    Ind.Increment()
    j = 0
    for model in models:
      j += 1
      _showPrinterModel(model, FJQC, j, jcount)
    Ind.Decrement()
  else:
    for model in models:
      _printPrinterModel(model)
  if csvPF:
    csvPF.writeCSVfile('Printer Models')

CHROME_APPS_TIME_OBJECTS = {'firstPublishTime', 'latestPublishTime'}
CHROME_APPS_TYPE_CHOICES  = ['android', 'chrome', 'web']

# gam info chromeapp android|chrome|web <AppID> [formatjson]
