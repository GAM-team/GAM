"""Error, exit, and argument validation functions.

Extracted from gam/__init__.py to reduce monolith size.
Functions here depend only on gamlib modules and util/output.
"""

import os
import sys

from gamlib import glcfg as GC
from gamlib import glglobals as GM
from gamlib import glmsgs as Msg


class _InstanceProxy:
  """Lazy proxy that delegates attribute access to a named instance in the gam module."""
  def __init__(self, name):
    self._name = name
  def __getattr__(self, attr):
    return getattr(getattr(sys.modules['gam'], self._name), attr)

Act = _InstanceProxy('Act')
Cmd = _InstanceProxy('Cmd')
Ind = _InstanceProxy('Ind')



from util.output import (
    currentCountNL,
    formatKeyValueList,
    stderrErrorMsg,
    stderrWarningMsg,
    systemErrorExit,
    writeStderr,
)

# Lazy accessor for Ent (runtime instance)
def _getEnt():
  return sys.modules['gam'].Ent

# Constants imported from __init__.py at module level via lazy accessor
def _getConst(name):
  return getattr(sys.modules['gam'], name)

# --- Return code constants (imported lazily) ---
ACTION_FAILED_RC = None
CLIENT_SECRETS_JSON_REQUIRED_RC = None
ENTITY_DOES_NOT_EXIST_RC = None
ENTITY_IS_NOT_UNIQUE_RC = None
INVALID_JSON_RC = None
OAUTH2_TXT_REQUIRED_RC = None
OAUTH2SERVICE_JSON_REQUIRED_RC = None
USAGE_ERROR_RC = None

def _ensureConstants():
  global ACTION_FAILED_RC, CLIENT_SECRETS_JSON_REQUIRED_RC, ENTITY_DOES_NOT_EXIST_RC
  global ENTITY_IS_NOT_UNIQUE_RC, INVALID_JSON_RC, OAUTH2_TXT_REQUIRED_RC
  global OAUTH2SERVICE_JSON_REQUIRED_RC, USAGE_ERROR_RC
  if ACTION_FAILED_RC is None:
    m = sys.modules['gam']
    ACTION_FAILED_RC = m.ACTION_FAILED_RC
    CLIENT_SECRETS_JSON_REQUIRED_RC = m.CLIENT_SECRETS_JSON_REQUIRED_RC
    ENTITY_DOES_NOT_EXIST_RC = m.ENTITY_DOES_NOT_EXIST_RC
    ENTITY_IS_NOT_UNIQUE_RC = m.ENTITY_IS_NOT_UNIQUE_RC
    INVALID_JSON_RC = m.INVALID_JSON_RC
    OAUTH2_TXT_REQUIRED_RC = m.OAUTH2_TXT_REQUIRED_RC
    OAUTH2SERVICE_JSON_REQUIRED_RC = m.OAUTH2SERVICE_JSON_REQUIRED_RC
    USAGE_ERROR_RC = m.USAGE_ERROR_RC

# --- Credential file errors ---

def invalidClientSecretsJsonExit(errMsg):
  _ensureConstants()
  Ent = _getEnt()
  stderrErrorMsg(Msg.DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT.format(Ent.Singular(Ent.CLIENT_SECRETS_JSON_FILE), GC.Values[GC.CLIENT_SECRETS_JSON], errMsg))
  writeStderr(Msg.INSTRUCTIONS_CLIENT_SECRETS_JSON)
  systemErrorExit(CLIENT_SECRETS_JSON_REQUIRED_RC, None)

def invalidOauth2serviceJsonExit(errMsg):
  _ensureConstants()
  Ent = _getEnt()
  stderrErrorMsg(Msg.DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT.format(Ent.Singular(Ent.OAUTH2SERVICE_JSON_FILE), GC.Values[GC.OAUTH2SERVICE_JSON], errMsg))
  writeStderr(Msg.INSTRUCTIONS_OAUTH2SERVICE_JSON)
  systemErrorExit(OAUTH2SERVICE_JSON_REQUIRED_RC, None)

def invalidOauth2TxtExit(errMsg):
  _ensureConstants()
  Ent = _getEnt()
  stderrErrorMsg(Msg.DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT.format(Ent.Singular(Ent.OAUTH2_TXT_FILE), GC.Values[GC.OAUTH2_TXT], errMsg))
  writeStderr(Msg.EXECUTE_GAM_OAUTH_CREATE)
  systemErrorExit(OAUTH2_TXT_REQUIRED_RC, None)

def expiredRevokedOauth2TxtExit():
  _ensureConstants()
  Ent = _getEnt()
  stderrErrorMsg(Msg.IS_EXPIRED_OR_REVOKED.format(Ent.Singular(Ent.OAUTH2_TXT_FILE), GC.Values[GC.OAUTH2_TXT]))
  writeStderr(Msg.EXECUTE_GAM_OAUTH_CREATE)
  systemErrorExit(OAUTH2_TXT_REQUIRED_RC, None)

def invalidDiscoveryJsonExit(fileName, errMsg):
  _ensureConstants()
  Ent = _getEnt()
  stderrErrorMsg(Msg.DOES_NOT_EXIST_OR_HAS_INVALID_FORMAT.format(Ent.Singular(Ent.DISCOVERY_JSON_FILE), fileName, errMsg))
  systemErrorExit(INVALID_JSON_RC, None)

# --- Entity error exits ---

def entityActionFailedExit(entityValueList, errMsg, i=0, count=0):
  _ensureConstants()
  Ent = _getEnt()
  systemErrorExit(ACTION_FAILED_RC, formatKeyValueList(Ind.Spaces(),
                                                       Ent.FormatEntityValueList(entityValueList)+[Act.Failed(), errMsg],
                                                       currentCountNL(i, count)))

def entityDoesNotExistExit(entityType, entityName, i=0, count=0, errMsg=None):
  _ensureConstants()
  Ent = _getEnt()
  Cmd.Backup()
  writeStderr(Cmd.CommandLineWithBadArgumentMarked(False))
  systemErrorExit(ENTITY_DOES_NOT_EXIST_RC, formatKeyValueList(Ind.Spaces(),
                                                               [Ent.Singular(entityType), entityName, errMsg or Msg.DOES_NOT_EXIST],
                                                               currentCountNL(i, count)))

def entityDoesNotHaveItemExit(entityValueList, i=0, count=0):
  _ensureConstants()
  Ent = _getEnt()
  Cmd.Backup()
  writeStderr(Cmd.CommandLineWithBadArgumentMarked(False))
  systemErrorExit(ENTITY_DOES_NOT_EXIST_RC, formatKeyValueList(Ind.Spaces(),
                                                               Ent.FormatEntityValueList(entityValueList)+[Msg.DOES_NOT_EXIST],
                                                               currentCountNL(i, count)))

def entityIsNotUniqueExit(entityType, entityName, valueType, valueList, i=0, count=0):
  _ensureConstants()
  Ent = _getEnt()
  Cmd.Backup()
  writeStderr(Cmd.CommandLineWithBadArgumentMarked(False))
  systemErrorExit(ENTITY_IS_NOT_UNIQUE_RC, formatKeyValueList(Ind.Spaces(),
                                                              [Ent.Singular(entityType), entityName, Msg.IS_NOT_UNIQUE.format(Ent.Plural(valueType), ','.join(valueList))],
                                                              currentCountNL(i, count)))

# --- Usage/argument errors ---

def usageErrorExit(message, extraneous=False):
  _ensureConstants()
  writeStderr(Cmd.CommandLineWithBadArgumentMarked(extraneous))
  stderrErrorMsg(message)
  FN_GAMCOMMANDS_TXT = _getConst('FN_GAMCOMMANDS_TXT')
  GAM_WIKI = _getConst('GAM_WIKI')
  writeStderr(Msg.HELP_SYNTAX.format(os.path.join(GM.Globals[GM.GAM_PATH], FN_GAMCOMMANDS_TXT)))
  writeStderr(Msg.HELP_WIKI.format(GAM_WIKI))
  sys.exit(USAGE_ERROR_RC)

def csvFieldErrorExit(fieldName, fieldNames, backupArg=False, checkForCharset=False):
  if backupArg:
    Cmd.Backup()
    if checkForCharset and Cmd.Previous() == 'charset':
      Cmd.Backup()
      Cmd.Backup()
  usageErrorExit(Msg.HEADER_NOT_FOUND_IN_CSV_HEADERS.format(fieldName, ','.join(fieldNames)))

def csvDataAlreadySavedErrorExit():
  Cmd.Backup()
  usageErrorExit(Msg.CSV_DATA_ALREADY_SAVED)

# The last thing shown is unknown
def unknownArgumentExit():
  Cmd.Backup()
  usageErrorExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1])

# Argument describes what's expected
def expectedArgumentExit(problem, argument):
  usageErrorExit(f'{problem}: {Msg.EXPECTED} <{argument}>')

def blankArgumentExit(argument):
  expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_BLANK][1], f'{Msg.NON_BLANK} {argument}')

def emptyArgumentExit(argument):
  expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_EMPTY][1], f'{Msg.NON_EMPTY} {argument}')

def invalidArgumentExit(argument):
  expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID][1], argument)

def missingArgumentExit(argument):
  expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_MISSING][1], argument)

def deprecatedArgument(argument):
  Cmd.Backup()
  writeStderr(Cmd.CommandLineWithBadArgumentMarked(False))
  Cmd.Advance()
  stderrWarningMsg(f'{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_DEPRECATED][1]}: {Msg.IGNORED} <{argument}>')

def deprecatedArgumentExit(argument):
  usageErrorExit(f'{Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_DEPRECATED][1]}: <{argument}>')

def deprecatedCommandExit():
  _ensureConstants()
  systemErrorExit(USAGE_ERROR_RC, Msg.SITES_COMMAND_DEPRECATED.format(Cmd.CommandDeprecated()))

# Choices is the valid set of choices that was expected
def formatChoiceList(choices):
  choiceList = [c if c else "''" for c in choices]
  if len(choiceList) <= 5:
    return '|'.join(choiceList)
  return '|'.join(sorted(choiceList))

def invalidChoiceExit(choice, choices, backupArg):
  if backupArg:
    Cmd.Backup()
  expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_INVALID_CHOICE][1].format(choice), formatChoiceList(choices))

def missingChoiceExit(choices):
  expectedArgumentExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_MISSING][1], formatChoiceList(choices))
