"""Schema parameter utilities shared between user management and groups.

Moved here to break circular dependencies between cmd/ modules.
"""

from gamlib import glclargs
from gam.util.args import getString

Cmd = glclargs.GamCLArgs()


def _initSchemaParms(projection):
  return {'projection': projection, 'customFieldMask': None, 'selectedSchemaFields': {}}

def _getSchemaNameList(schemaParms):
  customFieldMask = getString(Cmd.OB_SCHEMA_NAME_LIST).replace(' ', ',')
  if customFieldMask.lower() == 'all':
    schemaParms['projection'] = 'full'
    schemaParms['customFieldMask'] = None
    schemaParms['selectedSchemaFields'] = {}
  else:
    schemaParms['projection'] = 'custom'
    customFieldMaskList = []
    for schemaField in customFieldMask.split(','):
      if schemaField.find('.') == -1:
        customFieldMaskList.append(schemaField)
      else:
        schemaName, fieldName = schemaField.split('.', 1)
        customFieldMaskList.append(schemaName)
        schemaParms['selectedSchemaFields'] .setdefault(schemaName, set())
        schemaParms['selectedSchemaFields'][schemaName].add(fieldName)
    schemaParms['customFieldMask'] = ','.join(customFieldMaskList)
