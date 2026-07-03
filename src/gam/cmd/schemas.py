"""GAM user schema management."""

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

def _showSchema(schema, i=0, count=0):
  _getMain().printEntity([Ent.USER_SCHEMA, schema['schemaName']], i, count)
  Ind.Increment()
  for a_key in schema:
    if a_key not in {'kind', 'etag', 'schemaName', 'fields'}:
      _getMain().printKeyValueList([a_key, schema[a_key]])
  for field in schema['fields']:
    _getMain().printKeyValueList(['Field', field['fieldName']])
    Ind.Increment()
    for a_key in field:
      if a_key not in {'kind', 'etag', 'fieldName'}:
        if a_key != 'numericIndexingSpec':
          _getMain().printKeyValueList([a_key, field[a_key]])
        else:
          _getMain().printKeyValueList([a_key, ''])
          Ind.Increment()
          for s_key in field[a_key]:
            _getMain().printKeyValueList([s_key, field[a_key][s_key]])
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
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  updateCmd = Act.Get() == Act.UPDATE
  if not updateCmd:
    entityList = _getMain().getStringReturnInList(Cmd.OB_SCHEMA_NAME)
  else:
    entityList = _getMain().getEntityList(Cmd.OB_SCHEMA_ENTITY)
  addBody = {'schemaName': '', 'fields': []}
  deleteFields = []
  schemaDisplayName = None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if myarg == 'field':
      fieldName = _getMain().getString(Cmd.OB_FIELD_NAME)
      a_field = {'fieldName': fieldName.replace(' ', '_'), 'displayName': fieldName, 'fieldType': 'STRING'}
      while Cmd.ArgumentsRemaining():
        argument = _getMain().getArgument()
        if argument == 'displayname':
          a_field['displayName'] = _getMain().getString(Cmd.OB_FIELD_NAME)
        elif argument == 'type':
          a_field['fieldType'] = _getMain().getChoice(SCHEMA_FIELDTYPE_CHOICE_MAP, mapChoice=True)
        elif argument in {'multivalued', 'multivalue'}:
          a_field['multiValued'] = True
        elif argument == 'indexed':
          a_field['indexed'] = True
        elif argument == 'restricted':
          a_field['readAccessType'] = 'ADMINS_AND_SELF'
        elif argument == 'range':
          a_field['numericIndexingSpec'] = {'minValue': getInteger(), 'maxValue': _getMain().getInteger()}
        elif argument == 'endfield':
          break
        elif argument == 'field':
          Cmd.Backup()
          break
        else:
          _getMain().unknownArgumentExit()
      addBody['fields'].append(a_field)
    elif updateCmd and myarg == 'deletefield':
      deleteFields.append(_getMain().getString(Cmd.OB_FIELD_NAME).replace(' ', '_'))
    elif myarg == 'displayname':
      schemaDisplayName = _getMain().getString(Cmd.OB_SCHEMA_NAME)
    else:
      _getMain().unknownArgumentExit()
  i = 0
  count = len(entityList)
  if not updateCmd:
    if not addBody['fields']:
      _getMain().missingArgumentExit('SchemaFieldDefinition')
  elif schemaDisplayName and count > 1:
    _getMain().usageErrorExit(Msg.DISPLAYNAME_NOT_ALLOWED_WHEN_UPDATING_MULTIPLE_SCHEMAS)
  for schemaName in entityList:
    i += 1
    try:
      if updateCmd:
        oldBody = _getMain().callGAPI(cd.schemas(), 'get',
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
            _getMain().entityActionNotPerformedWarning([Ent.USER_SCHEMA, schemaName, Ent.FIELD, delField], Msg.DOES_NOT_EXIST)
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
          _getMain().entityActionNotPerformedWarning([Ent.USER_SCHEMA, schemaName],
                                          Msg.SCHEMA_WOULD_HAVE_NO_FIELDS.format(Ent.Singular(Ent.USER_SCHEMA), Ent.Plural(Ent.FIELD)))
          continue
        if schemaDisplayName:
          oldBody['displayName'] = schemaDisplayName
        result = _getMain().callGAPI(cd.schemas(), 'update',
                          throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FORBIDDEN, GAPI.FIELD_IN_USE],
                          customerId=GC.Values[GC.CUSTOMER_ID], body=oldBody, schemaKey=schemaName)
        _getMain().entityActionPerformed([Ent.USER_SCHEMA, result['schemaName']], i, count)
      else:
        addBody['schemaName'] = schemaName.replace(' ', '_')
        addBody['displayName'] = schemaDisplayName if schemaDisplayName else schemaName
        result = _getMain().callGAPI(cd.schemas(), 'insert',
                          throwReasons=[GAPI.DUPLICATE, GAPI.CONDITION_NOT_MET, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                        GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                          customerId=GC.Values[GC.CUSTOMER_ID], body=addBody, fields='schemaName')
        _getMain().entityActionPerformed([Ent.USER_SCHEMA, result['schemaName']], i, count)
    except GAPI.duplicate:
      _getMain().entityDuplicateWarning([Ent.USER_SCHEMA, schemaName], i, count)
    except (GAPI.conditionNotMet, GAPI.fieldInUse) as e:
      _getMain().entityActionFailedWarning([Ent.USER_SCHEMA, schemaName], str(e), i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound):
      _getMain().checkEntityAFDNEorAccessErrorExit(cd, Ent.USER_SCHEMA, schemaName, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam delete schema|schemas <SchemaEntity>
def doDeleteUserSchemas():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  entityList = _getMain().getEntityList(Cmd.OB_SCHEMA_ENTITY)
  _getMain().checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for schemaKey in entityList:
    i += 1
    try:
      _getMain().callGAPI(cd.schemas(), 'delete',
               throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND, GAPI.FIELD_IN_USE,
                             GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
               customerId=GC.Values[GC.CUSTOMER_ID], schemaKey=schemaKey)
      _getMain().entityActionPerformed([Ent.USER_SCHEMA, schemaKey], i, count)
    except GAPI.fieldInUse as e:
      _getMain().entityActionFailedWarning([Ent.USER_SCHEMA, schemaKey], str(e), i, count)
    except (GAPI.badRequest, GAPI.resourceNotFound):
      _getMain().checkEntityAFDNEorAccessErrorExit(cd, Ent.USER_SCHEMA, schemaKey, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

# gam info schema|schemas <SchemaEntity>
def doInfoUserSchemas():
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  entityList = _getMain().getEntityList(Cmd.OB_SCHEMA_ENTITY)
  _getMain().checkForExtraneousArguments()
  i = 0
  count = len(entityList)
  for schemaKey in entityList:
    i += 1
    try:
      schema = _getMain().callGAPI(cd.schemas(), 'get',
                        throwReasons=[GAPI.INVALID, GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                      GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                        customerId=GC.Values[GC.CUSTOMER_ID], schemaKey=schemaKey)
      _showSchema(schema, i, count)
    except (GAPI.invalid, GAPI.badRequest, GAPI.resourceNotFound):
      _getMain().checkEntityAFDNEorAccessErrorExit(cd, Ent.USER_SCHEMA, schemaKey, i, count)
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))

SCHEMAS_SORT_TITLES = ['schemaId', 'schemaName', 'displayName']
SCHEMAS_INDEXED_TITLES = ['fields']

# gam print schema|schemas [todrive <ToDriveAttribute>*]
# gam show schema|schemas
def doPrintShowUserSchemas():
  csvPF = _getMain().CSVPrintFile(SCHEMAS_SORT_TITLES, 'sortall', SCHEMAS_INDEXED_TITLES) if Act.csvFormat() else None
  cd = _getMain().buildGAPIObject(API.DIRECTORY)
  _getMain().getTodriveOnly(csvPF)
  try:
    result = _getMain().callGAPI(cd.schemas(), 'list',
                      throwReasons=[GAPI.BAD_REQUEST, GAPI.RESOURCE_NOT_FOUND,
                                    GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                      customerId=GC.Values[GC.CUSTOMER_ID])
    jcount = len(result.get('schemas', [])) if (result) else 0
    if not csvPF:
      _getMain().performActionNumItems(jcount, Ent.USER_SCHEMA)
    if jcount == 0:
      _getMain().setSysExitRC(_getMain().NO_ENTITIES_FOUND_RC)
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
          csvPF.WriteRowTitles(_getMain().flattenJSON(schema))
  except (GAPI.badRequest, GAPI.resourceNotFound):
    accessErrorExit(cd)
  except (GAPI.forbidden, GAPI.permissionDenied) as e:
    ClientAPIAccessDeniedExit(str(e))
  if csvPF:
    csvPF.writeCSVfile('User Schemas')

