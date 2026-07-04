"""GAM Chrome printer management."""

import re
import json

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI, callGAPIpages
from gam.util.args import (
    getArgument,
    getBoolean,
    getJSON,
    getString,
    makeOrgUnitPathAbsolute,
    makeOrgUnitPathRelative,
)
from gam.util.csv_pf import (
    CSVPrintFile,
    FormatJSONQuoteChar,
    cleanJSON,
    flattenJSON,
    getFieldsFromFieldsList,
    getFieldsList,
    getItemFieldsFromFieldsList,
    showJSON,
)
from gam.util.display import (
    entityActionFailedWarning,
    entityActionPerformed,
    getPageMessage,
    getPageMessageForWhom,
    performActionNumItems,
    printEntity,
    printGettingAllAccountEntities,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printLine,
)
from gam.util.entity import _getCustomersCustomerIdWithC, convertEntityToList, convertOrgUnitIDtoPath, getEntitiesFromCSVFile, getEntitiesFromFile
from gam.util.errors import missingArgumentExit, unknownArgumentExit
from gam.util.orgunits import getOrgUnitId
from gam.util.output import writeStdout


def isolatePrinterID(name):
  ''' converts long name into simple ID'''
  return name.split('/')[-1]

def _getPrinterID():
  cd = buildGAPIObject(API.PRINTERS)
  customer = _getCustomersCustomerIdWithC()
  printerId = getString(Cmd.OB_PRINTER_ID)
  pattern = re.compile(rf'^{customer}/chrome/printers/(.+)$')
  mg = pattern.match(printerId)
  if mg:
    return (printerId, mg.group(1), cd)
  return (f'{customer}/chrome/printers/{printerId}', printerId, cd)

def _getPrinterEntity():
  cd = buildGAPIObject(API.PRINTERS)
  customer = _getCustomersCustomerIdWithC()
  printerId = getString(Cmd.OB_PRINTER_ID)
  entitySelector = printerId.lower()
  if entitySelector == Cmd.ENTITY_SELECTOR_FILE:
    printerIds = getEntitiesFromFile(False)
  elif entitySelector == Cmd.ENTITY_SELECTOR_CSVFILE:
    printerIds = getEntitiesFromCSVFile(False)
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
    myarg = getArgument()
    if myarg == 'description':
      body['description'] = getString(Cmd.OB_STRING, minLen=0)
    elif myarg == 'displayname':
      body['displayName'] = getString(Cmd.OB_STRING)
    elif myarg == 'makeandmodel':
      body['makeAndModel'] = getString(Cmd.OB_STRING)
    elif myarg in {'ou', 'org', 'orgunit', 'orgunitid'}:
      _, body['orgUnitId'] = getOrgUnitId(cd)
      body['orgUnitId'] = body['orgUnitId'][3:]
    elif myarg == 'uri':
      body['uri'] = getString(Cmd.OB_STRING)
    elif myarg in {'driverless', 'usedriverlessconfig'}:
      body['useDriverlessConfig'] = getBoolean()
    elif myarg == 'nodetails':
      showDetails = False
    elif myarg == 'returnidonly':
      returnIdOnly = True
    elif myarg == 'json':
      body.update(getJSON(jsonDeleteFields))
    else:
      unknownArgumentExit()
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
      printer['parentOrgUnitPath'] = convertOrgUnitIDtoPath(cd, f'id:{printer["parentOrgUnitId"]}')
      printer['orgUnitId'] = orgUnitId
    else:
      printer['inherited'] = False
      printer['parentOrgUnitId'] = printer['parentOrgUnitPath'] = ''
    printer['orgUnitPath'] = convertOrgUnitIDtoPath(cd, f'id:{printer["orgUnitId"]}')
  return True

def _showPrinter(cd, printer, FJQC, orgUnitId=None, showInherited=False, i=0, count=0):
  if not _checkPrinterInheritance(cd, printer, orgUnitId, showInherited):
    return False
  if FJQC is not None and FJQC.formatJSON:
    printLine(json.dumps(cleanJSON(printer, timeObjects=PRINTER_TIME_OBJECTS), ensure_ascii=False, sort_keys=True))
    return
  printEntity([Ent.PRINTER, printer['id']], i, count)
  Ind.Increment()
  showJSON(None, printer, timeObjects=PRINTER_TIME_OBJECTS)
  Ind.Decrement()

# gam create printer <PrinterAttribute>+ [nodetails|returnidonly]
def doCreatePrinter():
  cd = buildGAPIObject(API.DIRECTORY)
  parent = _getCustomersCustomerIdWithC()
  body, showDetails, returnIdOnly = _getPrinterAttributes(cd, CREATE_PRINTER_JSON_SKIP_FIELDS)
  if not body.get('orgUnitId'):
    missingArgumentExit('orgunit')
  try:
    printer = callGAPI(cd.customers().chrome().printers(), 'create',
                       throwReasons=[GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       parent=parent, body=body)
    if returnIdOnly:
      writeStdout(f"{printer['id']}\n")
      return
    entityActionPerformed([Ent.PRINTER, printer['id']])
    if showDetails:
      _showPrinter(cd, printer, None)
  except (GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.PRINTER, None], str(e))

# gam update printer <PrinterID> <PrinterAttribute>+ [nodetails|returnidonly]
def doUpdatePrinter():
  name, printerId, cd = _getPrinterID()
  body, showDetails, returnIdOnly = _getPrinterAttributes(cd, UPDATE_PRINTER_JSON_SKIP_FIELDS)
  updateMask = ','.join(list(body.keys()))
  # note clearMask seems unnecessary. Updating field to '' clears it.
  try:
    printer = callGAPI(cd.customers().chrome().printers(), 'patch',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                       name=name, updateMask=updateMask, body=body)
    if returnIdOnly:
      writeStdout(f"{printer['id']}\n")
      return
    entityActionPerformed([Ent.PRINTER, printerId])
    if showDetails:
      _showPrinter(cd, printer, None)
  except (GAPI.notFound, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.PRINTER, printerId], str(e))

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
    result = callGAPI(cd.customers().chrome().printers(), 'batchDeletePrinters',
                      parent=parent, body=body)
    for printerId in result.get('printerIds', []):
      entityActionPerformed([Ent.PRINTER, printerId])
    for failure in result.get('failedPrinters', []):
      if 'printerIds' in failure:
        entityActionFailedWarning([Ent.PRINTER, failure['printerIds']], failure.get('errorMessage', 'Unknown printer'))
      else:
        entityActionFailedWarning([Ent.PRINTER, failure['printer']['id']], failure['errorMessage'])

# gam info printer <PrinterID>
#	[fields <PrinterFieldNameList>] [formatjson]
def doInfoPrinter():
  name, printerId, cd = _getPrinterID()
  FJQC = FormatJSONQuoteChar()
  fieldsList = []
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if getFieldsList(myarg, PRINTER_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    else:
      FJQC.GetFormatJSON(myarg)
  fields = getFieldsFromFieldsList(fieldsList)
  try:
    printer = callGAPI(cd.customers().chrome().printers(), 'get',
                       throwReasons=[GAPI.NOT_FOUND, GAPI.INVALID, GAPI.PERMISSION_DENIED],
                       name=name, fields=fields)
    _showPrinter(cd, printer, FJQC)
  except GAPI.notFound:
    entityUnknownWarning(Ent.PRINTER, f'{printerId}')
  except (GAPI.invalid, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.DEVICE, f'{printerId}'], str(e))

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
    row = flattenJSON(printer, timeObjects=PRINTER_TIME_OBJECTS)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'id': printer['id'],
                              'JSON': json.dumps(cleanJSON(printer, timeObjects=PRINTER_TIME_OBJECTS),
                                                 ensure_ascii=False, sort_keys=True)})

  cd = buildGAPIObject(API.DIRECTORY)
  parent = _getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile(['id']) if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  fieldsList = []
  ous = [None]
  directlyInOU = True
  pfilter = None
  showInherited = False
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg in ORGUNIT_ENTITIES_MAP:
      myarg = ORGUNIT_ENTITIES_MAP[myarg]
      ous = convertEntityToList(getString(Cmd.OB_ENTITY, minLen=0), shlexSplit=True, nonListEntityType=myarg in [Cmd.ENTITY_OU, Cmd.ENTITY_OU_AND_CHILDREN])
      directlyInOU = myarg in {Cmd.ENTITY_OU, Cmd.ENTITY_OUS}
    elif getFieldsList(myarg, PRINTER_FIELDS_CHOICE_MAP, fieldsList, initialField='id'):
      pass
    elif myarg == 'filter':
      pfilter = getString(Cmd.OB_STRING)
    elif myarg == 'showinherited':
      showInherited = getBoolean()
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if fieldsList and (not directlyInOU or showInherited):
    fieldsList.append('orgUnitId')
  fields = getItemFieldsFromFieldsList('printers', fieldsList)
  for ou in ous:
    if ou is not None:
      ou = makeOrgUnitPathAbsolute(ou)
      _, orgUnitId = getOrgUnitId(cd, ou)
      ouList = [(ou, orgUnitId[3:])]
    else:
      ouList = [('/', None)]
    if not directlyInOU:
      try:
        orgs = callGAPI(cd.orgunits(), 'list',
                        throwReasons=GAPI.ORGUNIT_GET_THROW_REASONS,
                        customerId=GC.Values[GC.CUSTOMER_ID], orgUnitPath=makeOrgUnitPathRelative(ou),
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
        printGettingAllEntityItemsForWhom(Ent.PRINTER, orgUnitPath, qualifier=oneQualifier, entityType=Ent.ORGANIZATIONAL_UNIT)
        pageMessage = getPageMessageForWhom()
      else:
        printGettingAllAccountEntities(Ent.PRINTER, pfilter)
        pageMessage = getPageMessage()
      try:
        printers = callGAPIpages(cd.customers().chrome().printers(), 'list', 'printers',
                                 pageMessage=pageMessage,
                                 throwReasons=[GAPI.INVALID, GAPI.PERMISSION_DENIED],
                                 parent=parent, orgUnitId=orgUnitId, filter=pfilter, fields=fields)
      except (GAPI.invalid, GAPI.permissionDenied) as e:
        entityActionFailedWarning([Ent.PRINTER, None], str(e))
        return
      if not csvPF:
        jcount = len(printers)
        if not FJQC.formatJSON:
          performActionNumItems(jcount, Ent.PRINTER)
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
      printLine(json.dumps(cleanJSON(model), ensure_ascii=False, sort_keys=True))
      return
    printEntity([Ent.PRINTER_MODEL, model['manufacturer']], i, count)
    Ind.Increment()
    for field in ['displayName', 'makeAndModel']:
      printKeyValueList([field, model[field]])
    Ind.Decrement()

  def _printPrinterModel(model):
    row = flattenJSON(model)
    if not FJQC.formatJSON:
      csvPF.WriteRowTitles(row)
    elif csvPF.CheckRowTitles(row):
      csvPF.WriteRowNoFilter({'JSON': json.dumps(cleanJSON(model),
                                                 ensure_ascii=False, sort_keys=True)})

  cd = buildGAPIObject(API.DIRECTORY)
  parent = _getCustomersCustomerIdWithC()
  csvPF = CSVPrintFile() if Act.csvFormat() else None
  FJQC = FormatJSONQuoteChar(csvPF)
  pfilter = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'filter':
      pfilter = getString(Cmd.OB_STRING)
    else:
      FJQC.GetFormatJSONQuoteChar(myarg, True)
  if not FJQC.formatJSON:
    csvPF.SetTitles(['manufacturer', 'displayName', 'makeAndModel'])
    csvPF.SetSortAllTitles()
  printGettingAllAccountEntities(Ent.PRINTER_MODEL, pfilter)
  pageMessage = getPageMessage()
  try:
    models = callGAPIpages(cd.customers().chrome().printers(), 'listPrinterModels', 'printerModels',
                           throwReasons=[GAPI.INVALID, GAPI.INVALID_ARGUMENT, GAPI.PERMISSION_DENIED],
                           pageMessage=pageMessage,
                           parent=parent, pageSize=10000, filter=pfilter)
  except (GAPI.invalid, GAPI.invalidArgument, GAPI.permissionDenied) as e:
    entityActionFailedWarning([Ent.PRINTER_MODEL, None], str(e))
    return
  if not csvPF:
    jcount = len(models)
    if not FJQC.formatJSON:
      performActionNumItems(jcount, Ent.PRINTER_MODEL)
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
