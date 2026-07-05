"""GAM user schema management."""


from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import msgs as Msg
from gam.var import Act, Cmd, Ent, Ind
from gam.util.access import checkEntityAFDNEorAccessErrorExit
from gam.util.api import buildGAPIObject
from gam.util.api_call import callGAPI
from gam.util.args import (
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getInteger,
    getString,
    getStringReturnInList,
)
from gam.util.csv_pf import CSVPrintFile, flattenJSON, getTodriveOnly
from gam.util.display import (
    entityActionFailedWarning,
    entityActionNotPerformedWarning,
    entityActionPerformed,
    entityDuplicateWarning,
    performActionNumItems,
    printEntity,
    printKeyValueList,
)
from gam.util.entity import getEntityList
from gam.util.errors import missingArgumentExit, unknownArgumentExit, usageErrorExit
from gam.util.output import setSysExitRC
from gam.constants import NO_ENTITIES_FOUND_RC
from gam.util.access import accessErrorExit
from gam.util.api import ClientAPIAccessDeniedExit


def _showSchema(schema, i=0, count=0):
  printEntity([Ent.USER_SCHEMA, schema['schemaName']], i, count)
  Ind.Increment()
  for a_key in schema:
    if a_key not in {'kind', 'etag', 'schemaName', 'fields'}:
      printKeyValueList([a_key, schema[a_key]])
  for field in schema['fields']:
    printKeyValueList(['Field', field['fieldName']])
    Ind.Increment()
    for a_key in field:
      if a_key not in {'kind', 'etag', 'fieldName'}:
        if a_key != 'numericIndexingSpec':
          printKeyValueList([a_key, field[a_key]])
        else:
          printKeyValueList([a_key, ''])
          Ind.Increment()
          for s_key in field[a_key]:
            printKeyValueList([s_key, field[a_key][s_key]])
          Ind.Decrement()
    Ind.Decrement()
  Ind.Decrement()

SCHEMA_FIELDTYPE_CHOICE_MAP = {
  'bool': 'BOOL',
  'boolean': 'BOOL',
  'date': 'DATE',
  'double': 'DOUBLE',
  'email': 'EMAIL',
  'int64': 'INT64',
  'phone': 'PHONE',
  'string': 'STRING',
  }

# gam create schema|schemas <SchemaName> [displayname <String>] <SchemaFieldDefinition>+
# gam update schema|schemas <SchemaEntity> [displayname <String>] <SchemaFieldDefinition>+
def doCreateUpdateUserSchemas():
  cd = buildGAPIObject(API.DIRECTORY)
  updateCmd = Act.Get() == Act.UPDATE
  if not updateCmd:
    entityList = getStringReturnInList(Cmd.OB_SCHEMA_NAME)
  else:
    entityList = getEntityList(Cmd.OB_SCHEMA_ENTITY)
  addBody = {'schemaName': '', 'fields': []}
  deleteFields = []
  schemaDisplayName = None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'field':
      fieldName = getString(Cmd.OB_FIELD_NAME)
      a_field = {'fieldName': fieldName.replace(' ', '_'), 'displayName': fieldName, 'fieldType': 'STRING'}
      while Cmd.ArgumentsRemaining():
        argument = getArgument()
        if argument == 'displayname':
          a_field['displayName'] = getString(Cmd.OB_FIELD_NAME)
        elif argument == 'type':
          a_field['fieldType'] = getChoice(SCHEMA_FIELDTYPE_CHOICE_MAP, mapChoice=True)
        elif argument in {'multivalued', 'multivalue'}:
          a_field['multiValued'] = True
        elif argument == 'indexed':
          a_field['indexed'] = True
        elif argument == 'restricted':
          a_field['readAccessType'] = 'ADMINS_AND_SELF'
        elif argument == 'range':
          a_field['numericIndexingSpec'] = {'minValue': getInteger(), 'maxValue': getInteger()}
        elif argument == 'endfield':
          break
        elif argument == 'field':
          Cmd.Backup()
          break
        else:
          unknownArgumentExit()
      addBody['fields'].append(a_field)
    elif updateCmd and myarg == 'deletefield':
      deleteFields.append(getString(Cmd.OB_FIELD_NAME).replace(' ', '_'))
    elif myarg == 'displayname':
      schemaDisplayName = getString(Cmd.OB_SCHEMA_NAME)
    else:
      unknownArgumentExit()
  i = 0
  count = len(entityList)
  if not updateCmd:
    if not addBody['fields']:
      missingArgumentExit('SchemaFieldDefinition')
  elif schemaDisplayName and count > 1:
    usageErrorExit(Msg.DISPLAYNAME_NOT_ALLOWED_WHEN_UPDATING_MULTIPLE_SCHEMAS)
  for schemaName in entityList:
    i += 1
    try:
      if updateCmd:
        oldBody = callGAPI(cd.schemas(), 'get',
                           throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                         GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                           customerId=GC.Values[GC.CUSTOMER_ID], schemaKey=schemaName, fields='schemaName,displayName,fields')
        for field in oldBody['fields']:
          field.pop('etag', None)
          field.pop('kind', None)
          field.pop('fieldId', None)
        badDelete = False
        for delField in deleteFields:
          fieldNameLower = delField.lower()
          for n, field in enumerate(oldBody['fields']):
            if field['fieldName'].lower() == fieldNameLower:
              del oldBody['fields'][n]
              break
          else:
            entityActionNotPerformedWarning([Ent.USER_SCHEMA, schemaName, Ent.FIELD, delField], Msg.DOES_NOT_EXIST)
            badDelete = True
        if badDelete:
          continue
        for addField in addBody['fields']:
          fieldNameLower = addField['fieldName'].lower()
          for n, field in enumerate(oldBody['fields']):
            if field['fieldName'].lower() == fieldNameLower:
              del oldBody['fields'][n]
              break
        oldBody['fields'].extend(addBody['fields'])
        if not oldBody['fields']:
          entityActionNotPerformedWarning([Ent.USER_SCHEMA, schemaName],
                                          Msg.SCHEMA_WOULD_HAVE_NO_FIELDS.format(Ent.Singular(Ent.USER_SCHEMA), Ent.Plural(Ent.FIELD)))
          continue
        if schemaDisplayName:
          oldBody['displayName'] = schemaDisplayName
        result = callGAPI(cd.schemas(), 'update',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.FIELD_IN_USE],
                          customerId=GC.Values[GC.CUSTOMER_ID], body=oldBody, schemaKey=schemaName)
        entityActionPerformed([Ent.USER_SCHEMA, result['schemaName']], i, count)
      else:
        addBody['schemaName'] = schemaName.replace(' ', '_')
        addBody['displayName'] = schemaDisplayName if schemaDisplayName else schemaName
        result = callGAPI(cd.schemas(), 'insert',
                          throwReasons=[GAPI.DUPLICATE, GAPI.CONDITION_NOT_MET, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                        GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                          customerId=GC.Values[GC.CUSTOMER_ID], body=addBody, fields='schemaName')
        entityActionPerformed([Ent.USER_SCHEMA, result['schemaName']], i, count)
    except GAPI.duplicate:
      entityDuplicateWarning([Ent.USER_SCHEMA, schemaName], i, count)
    except (GAPI.conditionNotMet, GAPI.fieldInUse) as e:
      entityActionFailedWarning([Ent.USER_SCHEMA, schemaName], str(e), i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.USER_SCHEMA, schemaName, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam delete schema|schemas <SchemaEntity>
def doDeleteUserSchemas():
  cd = buildGAPIObject(API.DIRECTORY)
  entityList = getEntityList(Cmd.OB_SCHEMA_ENTITY)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for schemaKey in entityList:
    i += 1
    try:
      callGAPI(cd.schemas(), 'delete',
               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FIELD_IN_USE,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               customerId=GC.Values[GC.CUSTOMER_ID], schemaKey=schemaKey)
      entityActionPerformed([Ent.USER_SCHEMA, schemaKey], i, count)
    except GAPI.fieldInUse as e:
      entityActionFailedWarning([Ent.USER_SCHEMA, schemaKey], str(e), i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.USER_SCHEMA, schemaKey, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam info schema|schemas <SchemaEntity>
def doInfoUserSchemas():
  cd = buildGAPIObject(API.DIRECTORY)
  entityList = getEntityList(Cmd.OB_SCHEMA_ENTITY)
  checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for schemaKey in entityList:
    i += 1
    try:
      schema = callGAPI(cd.schemas(), 'get',
                        throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                      GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        customerId=GC.Values[GC.CUSTOMER_ID], schemaKey=schemaKey)
      _showSchema(schema, i, count)
    except (GAPI.invalid, GAPI.badRequest, GAPI.resourceNotFound):
      checkEntityAFDNEorAccessErrorExit(cd, Ent.USER_SCHEMA, schemaKey, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

SCHEMAS_SORT_TITLES = ['schemaId', 'schemaName', 'displayName']
SCHEMAS_INDEXED_TITLES = ['fields']

# gam print schema|schemas [todrive <ToDriveAttribute>*]
# gam show schema|schemas
def doPrintShowUserSchemas():
  csvPF = CSVPrintFile(SCHEMAS_SORT_TITLES, 'sortall', SCHEMAS_INDEXED_TITLES) if Act.csvFormat() else None
  cd = buildGAPIObject(API.DIRECTORY)
  getTodriveOnly(csvPF)
  try:
    result = callGAPI(cd.schemas(), 'list',
                      throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=GC.Values[GC.CUSTOMER_ID])
    jcount = len(result.get('schemas', [])) if (result) else 0
    if not csvPF:
      performActionNumItems(jcount, Ent.USER_SCHEMA)
    if jcount == 0:
      setSysExitRC(NO_ENTITIES_FOUND_RC)
    else:
      if not csvPF:
        Ind.Increment()
        j = 0
        for schema in result['schemas']:
          j += 1
          _showSchema(schema, j, jcount)
        Ind.Decrement()
      else:
        for schema in result['schemas']:
          csvPF.WriteRowTitles(flattenJSON(schema))
  except (GAPI.badRequest, GAPI.resourceNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  if csvPF:
    csvPF.writeCSVfile('User Schemas')

