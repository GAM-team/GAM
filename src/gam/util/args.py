"""Argument parsing, getters, and validators."""

__all__ = [
  # Private functions used by __init__.py
  '_getIsSuspended', '_getIsArchived', '_getOptionalIsSuspendedIsArchived',
  # Constants
  'AGE_TIME_FORMAT_REQUIRED', 'AGE_TIME_PATTERN',
  'AND_OR_CONJUNCTION_MAP',
  'ARCHIVED_ARGUMENTS', 'ARCHIVED_CHOICE_MAP',
  'BCP47_LANGUAGE_CODES_MAP',
  'CALENDAR_COLOR_MAP', 'CALENDAR_EVENT_COLOR_MAP',
  'CALENDAR_REMINDER_MAX_MINUTES', 'CALENDAR_REMINDER_METHODS',
  'CHOICE_ALIASES', 'COLORHEX_FORMAT_REQUIRED', 'COLORHEX_PATTERN',
  'DEFAULT_CHOICE', 'DELIVERY_SETTINGS_UNDEFINED',
  'DELTA_DATE_FORMAT_REQUIRED', 'DELTA_DATE_PATTERN',
  'DELTA_TIME_FORMAT_REQUIRED', 'DELTA_TIME_PATTERN',
  'EVENTID_FORMAT_REQUIRED', 'EVENTID_PATTERN', 'EVENT_TIME_FORMAT_REQUIRED',
  'GOOGLE_COLOR_MAP', 'GROUP_DELIVERY_SETTINGS_MAP',
  'HHMM_FORMAT', 'HHMM_FORMAT_REQUIRED',
  'LABEL_BACKGROUND_COLORS', 'LABEL_COLORS', 'LABEL_TEXT_COLORS',
  'LANGUAGE_CODES_MAP', 'LOCALE_CODES_MAP',
  'MAP_CHOICE', 'MAX_MESSAGE_BYTES_FORMAT_REQUIRED', 'MAX_MESSAGE_BYTES_PATTERN',
  'NAME_EMAIL_ADDRESS_PATTERN', 'NO_DEFAULT',
  'PEOPLE_PATTERN', 'PLUS_MINUS',
  'SORF_FILE_ARGUMENTS', 'SORF_HTML_ARGUMENTS', 'SORF_MSG_ARGUMENTS',
  'SORF_MSG_FILE_ARGUMENTS', 'SORF_SIG_ARGUMENTS', 'SORF_SIG_FILE_ARGUMENTS',
  'SORF_TEXT_ARGUMENTS', 'SORTORDER_CHOICE_MAP',
  'SUSPENDED_ARGUMENTS', 'SUSPENDED_CHOICE_MAP',
  'TIMEZONE_FORMAT_REQUIRED', 'TODAY_NOW',
  'UID_PATTERN', 'WEB_COLOR_MAP',
  'YYYYMMDDTHHMMSSZ_FORMAT', 'YYYYMMDDTHHMMSS_FORMAT_REQUIRED',
  'YYYYMMDD_FORMAT', 'YYYYMMDD_FORMAT_REQUIRED',
  'YYYYMMDD_HHMM_FORMAT', 'YYYYMMDD_HHMM_FORMAT_REQUIRED', 'YYYYMMDD_PATTERN',
  # Classes
  'OrderBy', 'StartEndTime',
  # Functions
  'addCourseAliasScope', 'addCourseIdScope',
  'checkArgumentPresent', 'checkDataField', 'checkForExtraneousArguments',
  'checkGetArgument', 'checkMatchSkipFields', 'checkSubkeyField',
  'encodeOrgUnitPath', 'escapeCRsNLs',
  'floatLimits', 'formatFileSize', 'formatHTTPError',
  'formatLocalDatestamp', 'formatLocalSecondsTimestamp', 'formatLocalTime',
  'formatLocalTimestamp', 'formatLocalTimestampUTC',
  'formatMaxMessageBytes', 'formatMilliSeconds',
  'getACLRoles', 'getAddCSVData', 'getAgeTime',
  'getArgument', 'getArgumentEmptyAllowed',
  'getBoolean', 'getCalendarReminder', 'getCharSet', 'getCharacter',
  'getChoice', 'getChoiceAndValue', 'getColor', 'getCourseAlias',
  'getDateOrDeltaFromNow', 'getDelimiter', 'getDeliverySettings',
  'getDelta', 'getDeltaDate', 'getDeltaTime',
  'getEmailAddress', 'getEmailAddressDomain', 'getEmailAddressUsername',
  'getEventID', 'getEventTime', 'getFilename', 'getFloat',
  'getGoogleProduct', 'getGoogleProductList', 'getGoogleSKU', 'getGoogleSKUList',
  'getHHMM', 'getHTTPError',
  'getInteger', 'getIntegerEmptyAllowed', 'getJSON',
  'getLabelColor', 'getLanguageCode',
  'getMatchSkipFields', 'getMaxMessageBytes', 'getNumberRangeList',
  'getOrderBySortOrder', 'getPermissionId', 'getPhraseDNEorSNA',
  'getREPattern', 'getREPatternSubstitution',
  'getRowFilterDateOrDeltaFromNow', 'getRowFilterTimeOrDeltaFromNow',
  'getSheetEntity', 'getSheetIdFromSheetEntity',
  'getString', 'getStringOrFile', 'getStringReturnInList',
  'getStringWithCRsNLs', 'getStringWithCRsNLsOrFile',
  'getTimeOrDeltaFromNow', 'getYYYYMMDD', 'getYYYYMMDD_HHMM',
  'integerLimits',
  'makeOrgUnitPathAbsolute', 'makeOrgUnitPathRelative', 'mapQueryRelativeTimes',
  'normalizeEmailAddressOrUID', 'normalizeStudentGuardianEmailAddressOrUID',
  'orgUnitPathQuery', 'protectedSheetId',
  'removeCourseAliasScope', 'removeCourseIdScope',
  'splitEmailAddress', 'todaysDate', 'todaysTime',
  'unescapeCRsNLs', 'validateEmailAddressOrUID',
  'validateREPattern', 'validateREPatternSubstitution',
]

import calendar
import datetime
import json
import re
import shlex
import sys

import arrow

from gamlib import settings as GC
from gam.util.fileio import setFilePath
from gamlib import state as GM
from gamlib import msgs as Msg
from gamlib import skus as SKU


from util.errors import (
    blankArgumentExit,
    csvFieldErrorExit,
    emptyArgumentExit,
    invalidArgumentExit,
    invalidChoiceExit,
    missingArgumentExit,
    missingChoiceExit,
    usageErrorExit,
)

from util.fileio import readFile
from util.output import ISOformatTimeStamp
from gam.var import Cmd, Ent

# Lazy accessor for main module

# --- Constants duplicated from __init__.py ---
# These are simple literals that never change, duplicated to avoid
# circular imports and _getMain() overhead on hot paths.

TRUE = 'true'
FALSE = 'false'
TRUE_VALUES = [TRUE, 'on', 'yes', 'enabled', '1']
FALSE_VALUES = [FALSE, 'off', 'no', 'disabled', '0']
TRUE_FALSE = [TRUE, FALSE]
ERROR = 'ERROR'
UTF8 = 'utf-8'

NEVER_DATE = '1970-01-01'
NEVER_DATETIME = '1970-01-01 00:00'
NEVER_TIME = '1970-01-01T00:00:00.000Z'
NEVER_TIME_NOMS = '1970-01-01T00:00:00Z'

ONE_KILO_10_BYTES = 1000
ONE_MEGA_10_BYTES = ONE_KILO_10_BYTES * ONE_KILO_10_BYTES
ONE_GIGA_10_BYTES = ONE_KILO_10_BYTES * ONE_MEGA_10_BYTES
ONE_TERA_10_BYTES = ONE_KILO_10_BYTES * ONE_GIGA_10_BYTES

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_WEEK = 604800

def checkArgumentPresent(choices, required=False):
  choiceList = choices if isinstance(choices, (list, set)) else [choices]
  if Cmd.ArgumentsRemaining():
    choice = Cmd.Current().strip().lower().replace('_', '')
    if choice:
      if choice in choiceList:
        Cmd.Advance()
        return True
    if not required:
      return False
    invalidChoiceExit(choice, choiceList, False)
  elif not required:
    return False
  missingChoiceExit(choiceList)

# Check that there are no extraneous arguments at the end of the command line
def checkForExtraneousArguments():
  if Cmd.ArgumentsRemaining():
    usageErrorExit(Cmd.ARGUMENT_ERROR_NAMES[Cmd.ARGUMENT_EXTRANEOUS][[1, 0][Cmd.MultipleArgumentsRemaining()]], extraneous=True)

# Check that an argument remains, get an argument, downshift, delete underscores
def checkGetArgument():
  if Cmd.ArgumentsRemaining():
    argument = Cmd.Current().lower()
    if argument:
      Cmd.Advance()
      return argument.replace('_', '')
  missingArgumentExit(Cmd.OB_ARGUMENT)

# Get an argument, downshift, delete underscores
def getArgument():
  argument = Cmd.Current().lower()
  if argument:
    Cmd.Advance()
    return argument.replace('_', '')
  missingArgumentExit(Cmd.OB_ARGUMENT)

# Get an argument, downshift, delete underscores
# An empty argument is allowed
def getArgumentEmptyAllowed():
  argument = Cmd.Current().lower()
  Cmd.Advance()
  return argument.replace('_', '')

def getACLRoles(aclRolesMap):
  roles = []
  for role in getString(Cmd.OB_ROLE_LIST, minLen=0).strip().lower().replace(',', ' ').split():
    if role == 'all':
      for arole in aclRolesMap:
        roles.append(aclRolesMap[arole])
    elif role in aclRolesMap:
      roles.append(aclRolesMap[role])
    else:
      invalidChoiceExit(role, aclRolesMap, True)
  return set(roles)

def getBoolean(defaultValue=True):
  if Cmd.ArgumentsRemaining():
    boolean = Cmd.Current().strip().lower()
    if boolean in TRUE_VALUES:
      Cmd.Advance()
      return True
    if boolean in FALSE_VALUES:
      Cmd.Advance()
      return False
    if defaultValue is not None:
      if not Cmd.Current().strip(): # If current argument is empty, skip over it
        Cmd.Advance()
      return defaultValue
    invalidChoiceExit(boolean, TRUE_FALSE, False)
  if defaultValue is not None:
    return defaultValue
  missingChoiceExit(TRUE_FALSE)

def getCharSet():
  if checkArgumentPresent('charset'):
    return getString(Cmd.OB_CHAR_SET)
  return GC.Values[GC.CHARSET]

DEFAULT_CHOICE = 'defaultChoice'
CHOICE_ALIASES = 'choiceAliases'
MAP_CHOICE = 'mapChoice'
NO_DEFAULT = 'NoDefault'

def getChoice(choices, **opts):
  if Cmd.ArgumentsRemaining():
    choice = Cmd.Current().strip().lower()
    if choice or '' in choices:
      if choice in opts.get(CHOICE_ALIASES, []):
        choice = opts[CHOICE_ALIASES][choice]
      if choice not in choices:
        choice = choice.replace('_', '').replace('-', '')
        if choice in opts.get(CHOICE_ALIASES, []):
          choice = opts[CHOICE_ALIASES][choice]
      if choice in choices:
        Cmd.Advance()
        return choice if not opts.get(MAP_CHOICE, False) else choices[choice]
    if opts.get(DEFAULT_CHOICE, NO_DEFAULT) != NO_DEFAULT:
      return opts[DEFAULT_CHOICE]
    invalidChoiceExit(choice, choices, False)
  elif opts.get(DEFAULT_CHOICE, NO_DEFAULT) != NO_DEFAULT:
    return opts[DEFAULT_CHOICE]
  missingChoiceExit(choices)

def getChoiceAndValue(item, choices, delimiter):
  if not Cmd.ArgumentsRemaining() or Cmd.Current().find(delimiter) == -1:
    return (None, None)
  choice, value = Cmd.Current().strip().split(delimiter, 1)
  choice = choice.strip().lower()
  value = value.strip()
  if choice in choices:
    if value:
      Cmd.Advance()
      return (choice, value)
    missingArgumentExit(item)
  invalidChoiceExit(choice, choices, False)

AND_OR_CONJUNCTION_MAP = {
  'and': 'AND',
  'or': 'OR',
  'all': 'AND',
  'any': 'OR',
  }

SUSPENDED_ARGUMENTS = {'notsuspended', 'suspended', 'issuspended'}
SUSPENDED_CHOICE_MAP = {'notsuspended': False, 'suspended': True}
def _getIsSuspended(myarg):
  if myarg in SUSPENDED_CHOICE_MAP:
    return SUSPENDED_CHOICE_MAP[myarg]
  return getBoolean() #issuspended

ARCHIVED_ARGUMENTS = {'notarchived', 'archived', 'isarchived'}
ARCHIVED_CHOICE_MAP = {'notarchived': False, 'archived': True}
def _getIsArchived(myarg):
  if myarg in ARCHIVED_CHOICE_MAP:
    return ARCHIVED_CHOICE_MAP[myarg]
  return getBoolean() #isarchived

def _getOptionalIsSuspendedIsArchived():
  isSuspended = isArchived = None
  while True:
    if Cmd.PeekArgumentPresent(SUSPENDED_ARGUMENTS):
      isSuspended = getChoice(SUSPENDED_CHOICE_MAP, defaultChoice=None, mapChoice=True)
      if isSuspended is None:
        isSuspended = getBoolean()
    elif Cmd.PeekArgumentPresent(ARCHIVED_ARGUMENTS):
      isArchived = getChoice(ARCHIVED_CHOICE_MAP, defaultChoice=None, mapChoice=True)
      if isArchived is None:
        isArchived = getBoolean()
    else:
      break
  return isSuspended, isArchived

CALENDAR_COLOR_MAP = {
  'amethyst': 24, 'avocado': 10, 'banana': 12, 'basil': 8, 'birch': 20, 'blueberry': 16,
  'cherryblossom': 22, 'citron': 11, 'cobalt': 15, 'cocoa': 1, 'eucalyptus': 7, 'flamingo': 2,
  'grape': 23, 'graphite': 19, 'lavender': 17, 'mango': 6, 'peacock': 14, 'pistachio': 9,
  'pumpkin': 5, 'radicchio': 21, 'sage': 13, 'tangerine': 4, 'tomato': 3, 'wisteria': 18,
  }

CALENDAR_EVENT_COLOR_MAP = {
  'banana': 5, 'basil': 10, 'blueberry': 9, 'flamingo': 4, 'graphite': 8, 'grape': 3,
  'lavender': 1, 'peacock': 7, 'sage': 2, 'tangerine': 6, 'tomato': 11,
  }

GOOGLE_COLOR_MAP = {
  'asparagus': '#7bd148', 'bluevelvet': '#9a9cff', 'bubblegum': '#f691b2', 'cardinal': '#f83a22',
  'chocolateicecream': '#ac725e', 'denim': '#9fc6e7', 'desertsand': '#fbe983', 'earthworm': '#cca6ac',
  'macaroni': '#fad165', 'marsorange': '#ff7537', 'mountaingray': '#cabdbf', 'mountaingrey': '#cabdbf',
  'mouse': '#8f8f8f', 'oldbrickred': '#d06b64', 'pool': '#9fe1e7', 'purpledino': '#b99aff',
  'purplerain': '#cd74e6', 'rainysky': '#4986e7', 'seafoam': '#92e1c0', 'slimegreen': '#b3dc6c',
  'spearmint': '#42d692', 'toyeggplant': '#a47ae2', 'vernfern': '#16a765', 'wildstrawberries': '#fa573c',
  'yellowcab': '#ffad46',
  }

WEB_COLOR_MAP = {
  'aliceblue': '#f0f8ff', 'antiquewhite': '#faebd7', 'aqua': '#00ffff', 'aquamarine': '#7fffd4',
  'azure': '#f0ffff', 'beige': '#f5f5dc', 'bisque': '#ffe4c4', 'black': '#000000',
  'blanchedalmond': '#ffebcd', 'blue': '#0000ff', 'blueviolet': '#8a2be2', 'brown': '#a52a2a',
  'burlywood': '#deb887', 'cadetblue': '#5f9ea0', 'chartreuse': '#7fff00', 'chocolate': '#d2691e',
  'coral': '#ff7f50', 'cornflowerblue': '#6495ed', 'cornsilk': '#fff8dc', 'crimson': '#dc143c',
  'cyan': '#00ffff', 'darkblue': '#00008b', 'darkcyan': '#008b8b', 'darkgoldenrod': '#b8860b',
  'darkgray': '#a9a9a9', 'darkgrey': '#a9a9a9', 'darkgreen': '#006400', 'darkkhaki': '#bdb76b',
  'darkmagenta': '#8b008b', 'darkolivegreen': '#556b2f', 'darkorange': '#ff8c00', 'darkorchid': '#9932cc',
  'darkred': '#8b0000', 'darksalmon': '#e9967a', 'darkseagreen': '#8fbc8f', 'darkslateblue': '#483d8b',
  'darkslategray': '#2f4f4f', 'darkslategrey': '#2f4f4f', 'darkturquoise': '#00ced1', 'darkviolet': '#9400d3',
  'deeppink': '#ff1493', 'deepskyblue': '#00bfff', 'dimgray': '#696969', 'dimgrey': '#696969',
  'dodgerblue': '#1e90ff', 'firebrick': '#b22222', 'floralwhite': '#fffaf0', 'forestgreen': '#228b22',
  'fuchsia': '#ff00ff', 'gainsboro': '#dcdcdc', 'ghostwhite': '#f8f8ff', 'gold': '#ffd700',
  'goldenrod': '#daa520', 'gray': '#808080', 'grey': '#808080', 'green': '#008000',
  'greenyellow': '#adff2f', 'honeydew': '#f0fff0', 'hotpink': '#ff69b4', 'indianred': '#cd5c5c',
  'indigo': '#4b0082', 'ivory': '#fffff0', 'khaki': '#f0e68c', 'lavender': '#e6e6fa',
  'lavenderblush': '#fff0f5', 'lawngreen': '#7cfc00', 'lemonchiffon': '#fffacd', 'lightblue': '#add8e6',
  'lightcoral': '#f08080', 'lightcyan': '#e0ffff', 'lightgoldenrodyellow': '#fafad2', 'lightgray': '#d3d3d3',
  'lightgrey': '#d3d3d3', 'lightgreen': '#90ee90', 'lightpink': '#ffb6c1', 'lightsalmon': '#ffa07a',
  'lightseagreen': '#20b2aa', 'lightskyblue': '#87cefa', 'lightslategray': '#778899', 'lightslategrey': '#778899',
  'lightsteelblue': '#b0c4de', 'lightyellow': '#ffffe0', 'lime': '#00ff00', 'limegreen': '#32cd32',
  'linen': '#faf0e6', 'magenta': '#ff00ff', 'maroon': '#800000', 'mediumaquamarine': '#66cdaa',
  'mediumblue': '#0000cd', 'mediumorchid': '#ba55d3', 'mediumpurple': '#9370db', 'mediumseagreen': '#3cb371',
  'mediumslateblue': '#7b68ee', 'mediumspringgreen': '#00fa9a', 'mediumturquoise': '#48d1cc', 'mediumvioletred': '#c71585',
  'midnightblue': '#191970', 'mintcream': '#f5fffa', 'mistyrose': '#ffe4e1', 'moccasin': '#ffe4b5',
  'navajowhite': '#ffdead', 'navy': '#000080', 'oldlace': '#fdf5e6', 'olive': '#808000',
  'olivedrab': '#6b8e23', 'orange': '#ffa500', 'orangered': '#ff4500', 'orchid': '#da70d6',
  'palegoldenrod': '#eee8aa', 'palegreen': '#98fb98', 'paleturquoise': '#afeeee', 'palevioletred': '#db7093',
  'papayawhip': '#ffefd5', 'peachpuff': '#ffdab9', 'peru': '#cd853f', 'pink': '#ffc0cb',
  'plum': '#dda0dd', 'powderblue': '#b0e0e6', 'purple': '#800080', 'red': '#ff0000',
  'rosybrown': '#bc8f8f', 'royalblue': '#4169e1', 'saddlebrown': '#8b4513', 'salmon': '#fa8072',
  'sandybrown': '#f4a460', 'seagreen': '#2e8b57', 'seashell': '#fff5ee', 'sienna': '#a0522d',
  'silver': '#c0c0c0', 'skyblue': '#87ceeb', 'slateblue': '#6a5acd', 'slategray': '#708090',
  'slategrey': '#708090', 'snow': '#fffafa', 'springgreen': '#00ff7f', 'steelblue': '#4682b4',
  'tan': '#d2b48c', 'teal': '#008080', 'thistle': '#d8bfd8', 'tomato': '#ff6347',
  'turquoise': '#40e0d0', 'violet': '#ee82ee', 'wheat': '#f5deb3', 'white': '#ffffff',
  'whitesmoke': '#f5f5f5', 'yellow': '#ffff00', 'yellowgreen': '#9acd32',
  }

COLORHEX_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')
COLORHEX_FORMAT_REQUIRED = 'ColorName|ColorHex'

def getColor():
  if Cmd.ArgumentsRemaining():
    color = Cmd.Current().strip().lower()
    if color in GOOGLE_COLOR_MAP:
      Cmd.Advance()
      return GOOGLE_COLOR_MAP[color]
    if color in WEB_COLOR_MAP:
      Cmd.Advance()
      return WEB_COLOR_MAP[color]
    tg = COLORHEX_PATTERN.match(color)
    if tg:
      Cmd.Advance()
      return tg.group(0)
    invalidArgumentExit(COLORHEX_FORMAT_REQUIRED)
  missingArgumentExit(COLORHEX_FORMAT_REQUIRED)

LABEL_COLORS = [
  '#000000', '#076239', '#0b804b', '#149e60', '#16a766', '#1a764d', '#1c4587', '#285bac',
  '#2a9c68', '#3c78d8', '#3dc789', '#41236d', '#434343', '#43d692', '#44b984', '#4a86e8',
  '#653e9b', '#666666', '#68dfa9', '#6d9eeb', '#822111', '#83334c', '#89d3b2', '#8e63ce',
  '#999999', '#a0eac9', '#a46a21', '#a479e2', '#a4c2f4', '#aa8831', '#ac2b16', '#b65775',
  '#b694e8', '#b9e4d0', '#c6f3de', '#c9daf8', '#cc3a21', '#cccccc', '#cf8933', '#d0bcf1',
  '#d5ae49', '#e07798', '#e4d7f5', '#e66550', '#eaa041', '#efa093', '#efefef', '#f2c960',
  '#f3f3f3', '#f691b3', '#f6c5be', '#f7a7c0', '#fad165', '#fb4c2f', '#fbc8d9', '#fcda83',
  '#fcdee8', '#fce8b3', '#fef1d1', '#ffad47', '#ffbc6b', '#ffd6a2', '#ffe6c7', '#ffffff',
  ]
LABEL_BACKGROUND_COLORS = [
  '#16a765', '#2da2bb', '#42d692', '#4986e7', '#98d7e4', '#a2dcc1',
  '#b3efd3', '#b6cff5', '#b99aff', '#c2c2c2', '#cca6ac', '#e3d7ff',
  '#e7e7e7', '#ebdbde', '#f2b2a8', '#f691b2', '#fb4c2f', '#fbd3e0',
  '#fbe983', '#fdedc1', '#ff7537', '#ffad46', '#ffc8af', '#ffdeb5',
  ]
LABEL_TEXT_COLORS = [
  '#04502e', '#094228', '#0b4f30', '#0d3472', '#0d3b44', '#3d188e',
  '#464646', '#594c05', '#662e37', '#684e07', '#711a36', '#7a2e0b',
  '#7a4706', '#8a1c0a', '#994a64', '#ffffff',
  ]

def getLabelColor(colorType):
  if Cmd.ArgumentsRemaining():
    color = Cmd.Current().strip().lower()
    tg = COLORHEX_PATTERN.match(color)
    if tg:
      color = tg.group(0)
      if color in colorType or color in LABEL_COLORS:
        Cmd.Advance()
        return color
    elif color.startswith('custom:'):
      tg = COLORHEX_PATTERN.match(color[7:])
      if tg:
        Cmd.Advance()
        return tg.group(0)
    invalidArgumentExit('|'.join(colorType))
  missingArgumentExit(Cmd.OB_LABEL_COLOR_HEX)

# Language codes used in Drive Labels/Youtube
BCP47_LANGUAGE_CODES_MAP = {
  'ar-sa': 'ar-SA', 'cs-cz': 'cs-CZ', 'da-dk': 'da-DK', 'de-de': 'de-DE', #Arabic Saudi Arabia, Czech Czech Republic, Danish Denmark, German Germany
  'el-gr': 'el-GR', 'en-au': 'en-AU', 'en-gb': 'en-GB', 'en-ie': 'en-IE', #Modern Greek Greece, English Australia, English United Kingdom, English Ireland
  'en-us': 'en-US', 'en-za': 'en-ZA', 'es-es': 'es-ES', 'es-mx': 'es-MX', #English United States, English South Africa, Spanish Spain, Spanish Mexico
  'fi-fi': 'fi-FI', 'fr-ca': 'fr-CA', 'fr-fr': 'fr-FR', 'he-il': 'he-IL', #Finnish Finland, French Canada, French France, Hebrew Israel
  'hi-in': 'hi-IN', 'hu-hu': 'hu-HU', 'id-id': 'id-ID', 'it-it': 'it-IT', #Hindi India, Hungarian Hungary, Indonesian Indonesia, Italian Italy
  'ja-jp': 'ja-JP', 'ko-kr': 'ko-KR', 'nl-be': 'nl-BE', 'nl-nl': 'nl-NL', #Japanese Japan, Korean Republic of Korea, Dutch Belgium, Dutch Netherlands
  'no-no': 'no-NO', 'pl-pl': 'pl-PL', 'pt-br': 'pt-BR', 'pt-pt': 'pt-PT', #Norwegian Norway, Polish Poland, Portuguese Brazil, Portuguese Portugal
  'ro-ro': 'ro-RO', 'ru-ru': 'ru-RU', 'sk-sk': 'sk-SK', 'sv-se': 'sv-SE', #Romanian Romania, Russian Russian Federation, Slovak Slovakia, Swedish Sweden
  'th-th': 'th-TH', 'tr-tr': 'tr-TR', 'zh-cn': 'zh-CN', 'zh-hk': 'zh-HK', #Thai Thailand, Turkish Turkey, Chinese China, Chinese Hong Kong
  'zh-tw': 'zh-TW' #Chinese Taiwan
  }

# Valid language codes
LANGUAGE_CODES_MAP = {
  'ach': 'ach', 'af': 'af', 'ag': 'ga', 'ak': 'ak', 'am': 'am', 'ar': 'ar', 'az': 'az', #Luo, Afrikaans, Irish, Akan, Amharic, Arabica, Azerbaijani
  'be': 'be', 'bem': 'bem', 'bg': 'bg', 'bn': 'bn', 'br': 'br', 'bs': 'bs', 'ca': 'ca', #Belarusian, Bemba, Bulgarian, Bengali, Breton, Bosnian, Catalan
  'chr': 'chr', 'ckb': 'ckb', 'co': 'co', 'crs': 'crs', 'cs': 'cs', 'cy': 'cy', 'da': 'da', #Cherokee, Kurdish (Sorani), Corsican, Seychellois Creole, Czech, Welsh, Danish
  'de': 'de', 'ee': 'ee', 'el': 'el', 'en': 'en', 'en-ca': 'en-CA', 'en-gb': 'en-GB', 'en-us': 'en-US', 'eo': 'eo', #German, Ewe, Greek, English, English (CA), English (UK), English (US), Esperanto
  'es': 'es', 'es-419': 'es-419', 'et': 'et', 'eu': 'eu', 'fa': 'fa', 'fi': 'fi', 'fil': 'fil', 'fo': 'fo', #Spanish, Spanish (Latin American), Estonian, Basque, Persian, Finnish, Filipino, Faroese
  'fr': 'fr', 'fr-ca': 'fr-CA', 'fy': 'fy', 'ga': 'ga', 'gaa': 'gaa', 'gd': 'gd', 'gl': 'gl', #French, French (Canada), Frisian, Irish, Ga, Scots Gaelic, Galician
  'gn': 'gn', 'gu': 'gu', 'ha': 'ha', 'haw': 'haw', 'he': 'he', 'hi': 'hi', 'hr': 'hr', #Guarani, Gujarati, Hausa, Hawaiian, Hebrew, Hindi, Croatian
  'ht': 'ht', 'hu': 'hu', 'hy': 'hy', 'ia': 'ia', 'id': 'id', 'ig': 'ig', 'in': 'in', #Haitian Creole, Hungarian, Armenian, Interlingua, Indonesian, Igbo, in
  'is': 'is', 'it': 'it', 'iw': 'iw', 'ja': 'ja', 'jw': 'jw', 'ka': 'ka', 'kg': 'kg', #Icelandic, Italian, Hebrew, Japanese, Javanese, Georgian, Kongo
  'kk': 'kk', 'km': 'km', 'kn': 'kn', 'ko': 'ko', 'kri': 'kri', 'k': 'k', 'ky': 'ky', #Kazakh, Khmer, Kannada, Korean, Krio (Sierra Leone), Kurdish, Kyrgyz
  'la': 'la', 'lg': 'lg', 'ln': 'ln', 'lo': 'lo', 'loz': 'loz', 'lt': 'lt', 'lua': 'lua', #Latin, Luganda, Lingala, Laothian, Lozi, Lithuanian, Tshiluba
  'lv': 'lv', 'mfe': 'mfe', 'mg': 'mg', 'mi': 'mi', 'mk': 'mk', 'ml': 'ml', 'mn': 'mn', #Latvian, Mauritian Creole, Malagasy, Maori, Macedonian, Malayalam, Mongolian
  'mo': 'mo', 'mr': 'mr', 'ms': 'ms', 'mt': 'mt', 'my': 'my', 'ne': 'ne', 'nl': 'nl', #Moldavian, Marathi, Malay, Maltese, Burmese, Nepali, Dutch
  'nn': 'nn', 'no': 'no', 'nso': 'nso', 'ny': 'ny', 'nyn': 'nyn', 'oc': 'oc', 'om': 'om', #Norwegian (Nynorsk), Norwegian, Northern Sotho, Chichewa, Runyakitara, Occitan, Oromo
  'or': 'or', 'pa': 'pa', 'pcm': 'pcm', 'pl': 'pl', 'ps': 'ps', 'pt-br': 'pt-BR', 'pt-pt': 'pt-PT', #Oriya, Punjabi, Nigerian Pidgin, Polish, Pashto, Portuguese (Brazil), Portuguese (Portugal)
  'q': 'q', 'rm': 'rm', 'rn': 'rn', 'ro': 'ro', 'ru': 'ru', 'rw': 'rw', 'sd': 'sd', #Quechua, Romansh, Kirundi, Romanian, Russian, Kinyarwanda, Sindhi
  'sh': 'sh', 'si': 'si', 'sk': 'sk', 'sl': 'sl', 'sn': 'sn', 'so': 'so', 'sq': 'sq', #Serbo-Croatian, Sinhalese, Slovak, Slovenian, Shona, Somali, Albanian
  'sr': 'sr', 'sr-me': 'sr-ME', 'st': 'st', 'su': 'su', 'sv': 'sv', 'sw': 'sw', 'ta': 'ta', #Serbian, Montenegrin, Sesotho, Sundanese, Swedish, Swahili, Tamil
  'te': 'te', 'tg': 'tg', 'th': 'th', 'ti': 'ti', 'tk': 'tk', 'tl': 'tl', 'tn': 'tn', #Telugu, Tajik, Thai, Tigrinya, Turkmen, Tagalog, Setswana
  'to': 'to', 'tr': 'tr', 'tt': 'tt', 'tum': 'tum', 'tw': 'tw', 'ug': 'ug', 'uk': 'uk', #Tonga, Turkish, Tatar, Tumbuka, Twi, Uighur, Ukrainian
  'ur': 'ur', 'uz': 'uz', 'vi': 'vi', 'wo': 'wo', 'xh': 'xh', 'yi': 'yi', 'yo': 'yo', #Urdu, Uzbek, Vietnamese, Wolof, Xhosa, Yiddish, Yoruba
  'zh-cn': 'zh-CN', 'zh-hk': 'zh-HK', 'zh-tw': 'zh-TW', 'zu': 'zu', #Chinese (Simplified), Chinese (Hong Kong/Traditional), Chinese (Taiwan/Traditional), Zulu
  }

LOCALE_CODES_MAP = {
  '': '',
  'ar-eg': 'ar_EG', #Arabic, Egypt
  'az-az': 'az_AZ', #Azerbaijani, Azerbaijan
  'be-by': 'be_BY', #Belarusian, Belarus
  'bg-bg': 'bg_BG', #Bulgarian, Bulgaria
  'bn-in': 'bn_IN', #Bengali, India
  'ca-es': 'ca_ES', #Catalan, Spain
  'cs-cz': 'cs_CZ', #Czech, Czech Republic
  'cy-gb': 'cy_GB', #Welsh, United Kingdom
  'da-dk': 'da_DK', #Danish, Denmark
  'de-ch': 'de_CH', #German, Switzerland
  'de-de': 'de_DE', #German, Germany
  'el-gr': 'el_GR', #Greek, Greece
  'en-au': 'en_AU', #English, Australia
  'en-ca': 'en_CA', #English, Canada
  'en-gb': 'en_GB', #English, United Kingdom
  'en-ie': 'en_IE', #English, Ireland
  'en-us': 'en_US', #English, U.S.A.
  'es-ar': 'es_AR', #Spanish, Argentina
  'es-bo': 'es_BO', #Spanish, Bolivia
  'es-cl': 'es_CL', #Spanish, Chile
  'es-co': 'es_CO', #Spanish, Colombia
  'es-ec': 'es_EC', #Spanish, Ecuador
  'es-es': 'es_ES', #Spanish, Spain
  'es-mx': 'es_MX', #Spanish, Mexico
  'es-py': 'es_PY', #Spanish, Paraguay
  'es-uy': 'es_UY', #Spanish, Uruguay
  'es-ve': 'es_VE', #Spanish, Venezuela
  'fi-fi': 'fi_FI', #Finnish, Finland
  'fil-ph': 'fil_PH', #Filipino, Philippines
  'fr-ca': 'fr_CA', #French, Canada
  'fr-fr': 'fr_FR', #French, France
  'gu-in': 'gu_IN', #Gujarati, India
  'hi-in': 'hi_IN', #Hindi, India
  'hr-hr': 'hr_HR', #Croatian, Croatia
  'hu-hu': 'hu_HU', #Hungarian, Hungary
  'hy-am': 'hy_AM', #Armenian, Armenia
  'in-id': 'in_ID', #Indonesian, Indonesia
  'it-it': 'it_IT', #Italian, Italy
  'iw-il': 'iw_IL', #Hebrew, Israel
  'ja-jp': 'ja_JP', #Japanese, Japan
  'ka-ge': 'ka_GE', #Georgian, Georgia
  'kk-kz': 'kk_KZ', #Kazakh, Kazakhstan
  'kn-in': 'kn_IN', #Kannada, India
  'ko-kr': 'ko_KR', #Korean, Korea
  'lt-lt': 'lt_LT', #Lithuanian, Lithuania
  'lv-lv': 'lv_LV', #Latvian, Latvia
  'ml-in': 'ml_IN', #Malayalam, India
  'mn-mn': 'mn_MN', #Mongolian, Mongolia
  'mr-in': 'mr_IN', #Marathi, India
  'my-mn': 'my_MN', #Burmese, Myanmar
  'nl-nl': 'nl_NL', #Dutch, Netherlands
  'nn-no': 'nn_NO', #Nynorsk, Norway
  'no-no': 'no_NO', #Bokmal, Norway
  'pa-in': 'pa_IN', #Punjabi, India
  'pl-pl': 'pl_PL', #Polish, Poland
  'pt-br': 'pt_BR', #Portuguese, Brazil
  'pt-pt': 'pt_PT', #Portuguese, Portugal
  'ro-ro': 'ro_RO', #Romanian, Romania
  'ru-ru': 'ru_RU', #Russian, Russia
  'sk-sk': 'sk_SK', #Slovak, Slovakia
  'sl-si': 'sl_SI', #Slovenian, Slovenia
  'sr-rs': 'sr_RS', #Serbian, Serbia
  'sv-se': 'sv_SE', #Swedish, Sweden
  'ta-in': 'ta_IN', #Tamil, India
  'te-in': 'te_IN', #Telugu, India
  'th-th': 'th_TH', #Thai, Thailand
  'tr-tr': 'tr_TR', #Turkish, Turkey
  'uk-ua': 'uk_UA', #Ukrainian, Ukraine
  'vi-vn': 'vi_VN', #Vietnamese, Vietnam
  'zh-cn': 'zh_CN', #Simplified Chinese, China
  'zh-hk': 'zh_HK', #Traditional Chinese, Hong Kong SAR China
  'zh-tw': 'zh_TW', #Traditional Chinese, Taiwan
  }

def getLanguageCode(languageCodeMap):
  if Cmd.ArgumentsRemaining():
    choice = Cmd.Current().strip().lower().replace('_', '-')
    if choice in languageCodeMap:
      Cmd.Advance()
      return languageCodeMap[choice]
    invalidChoiceExit(choice, languageCodeMap, False)
  missingChoiceExit(languageCodeMap)

def addCourseIdScope(courseId):
  if not courseId.isdigit() and courseId[:2] not in {'d:', 'p:'}:
    return f'd:{courseId}'
  return courseId

def removeCourseIdScope(courseId):
  if courseId.startswith('d:'):
    return courseId[2:]
  return courseId

def addCourseAliasScope(alias):
  if alias[:2] not in {'d:', 'p:'}:
    return f'd:{alias}'
  return alias

def removeCourseAliasScope(alias):
  if alias.startswith('d:'):
    return alias[2:]
  return alias

def getCourseAlias():
  if Cmd.ArgumentsRemaining():
    courseAlias = Cmd.Current()
    if courseAlias:
      Cmd.Advance()
      return addCourseAliasScope(courseAlias)
  missingArgumentExit(Cmd.OB_COURSE_ALIAS)

DELIVERY_SETTINGS_UNDEFINED = 'DSU'
GROUP_DELIVERY_SETTINGS_MAP = {
  'allmail': 'ALL_MAIL',
  'abridged': 'DAILY',
  'daily': 'DAILY',
  'digest': 'DIGEST',
  'disabled': 'DISABLED',
  'none': 'NONE',
  'nomail': 'NONE',
  }

def getDeliverySettings():
  if checkArgumentPresent(['delivery', 'deliverysettings']):
    return getChoice(GROUP_DELIVERY_SETTINGS_MAP, mapChoice=True)
  return getChoice(GROUP_DELIVERY_SETTINGS_MAP, defaultChoice=DELIVERY_SETTINGS_UNDEFINED, mapChoice=True)

UID_PATTERN = re.compile(r'u?id: ?(.+)', re.IGNORECASE)
PEOPLE_PATTERN = re.compile(r'people/([0-9]+)$', re.IGNORECASE)

def validateEmailAddressOrUID(emailAddressOrUID, checkPeople=True, ciGroupsAPI=False):
  cg = UID_PATTERN.match(emailAddressOrUID)
  if cg:
    return cg.group(1)
  if checkPeople:
    cg = PEOPLE_PATTERN.match(emailAddressOrUID)
    if cg:
      return cg.group(1)
  if ciGroupsAPI and emailAddressOrUID.startswith('groups/'):
    return emailAddressOrUID
  return emailAddressOrUID.find('@') != 0 and emailAddressOrUID.count('@') <= 1

NAME_EMAIL_ADDRESS_PATTERN = re.compile(r'^(.*)<(.+)>$')

# Normalize user/group email address/uid
# uid:12345abc -> 12345abc
# foo -> foo@domain
# foo@ -> foo@domain
# foo@bar.com -> foo@bar.com
# @domain -> domain
def normalizeEmailAddressOrUID(emailAddressOrUID, noUid=False, checkForCustomerId=False, noLower=False, ciGroupsAPI=False):
  if checkForCustomerId and (emailAddressOrUID == GC.Values[GC.CUSTOMER_ID]):
    return emailAddressOrUID
  if not noUid:
    cg = UID_PATTERN.match(emailAddressOrUID)
    if cg:
      return cg.group(1)
    cg = PEOPLE_PATTERN.match(emailAddressOrUID)
    if cg:
      return cg.group(1)
  if ciGroupsAPI and emailAddressOrUID.startswith('groups/'):
    return emailAddressOrUID
  if emailAddressOrUID.find('<') >= 0:
    match = NAME_EMAIL_ADDRESS_PATTERN.match(emailAddressOrUID)
    if match:
      emailAddressOrUID = match.group(2)
  atLoc = emailAddressOrUID.find('@')
  if atLoc == 0:
    return emailAddressOrUID[1:].lower() if not noLower else emailAddressOrUID[1:]
  if (atLoc == -1) or (atLoc == len(emailAddressOrUID)-1) and GC.Values[GC.DOMAIN]:
    if atLoc == -1:
      emailAddressOrUID = f'{emailAddressOrUID}@{GC.Values[GC.DOMAIN]}'
    else:
      emailAddressOrUID = f'{emailAddressOrUID}{GC.Values[GC.DOMAIN]}'
  return emailAddressOrUID.lower() if not noLower else emailAddressOrUID

# Normalize student/guardian email address/uid
# 12345678 -> 12345678
# - -> -
# Otherwise, same results as normalizeEmailAddressOrUID
def normalizeStudentGuardianEmailAddressOrUID(emailAddressOrUID, allowDash=False):
  if emailAddressOrUID.isdigit() or (allowDash and emailAddressOrUID == '-'):
    return emailAddressOrUID
  return normalizeEmailAddressOrUID(emailAddressOrUID)

def getEmailAddress(noUid=False, minLen=1, optional=False, returnUIDprefix=''):
  if Cmd.ArgumentsRemaining():
    emailAddress = Cmd.Current().strip().lower()
    if emailAddress:
      cg = UID_PATTERN.match(emailAddress)
      if cg:
        if not noUid:
          if cg.group(1):
            Cmd.Advance()
            return f'{returnUIDprefix}{cg.group(1)}'
        else:
          invalidArgumentExit('name@domain')
      else:
        atLoc = emailAddress.find('@')
        if atLoc == -1:
          if GC.Values[GC.DOMAIN]:
            emailAddress = f'{emailAddress}@{GC.Values[GC.DOMAIN]}'
          Cmd.Advance()
          return emailAddress
        if atLoc != 0:
          if (atLoc == len(emailAddress)-1) and GC.Values[GC.DOMAIN]:
            emailAddress = f'{emailAddress}{GC.Values[GC.DOMAIN]}'
          Cmd.Advance()
          return emailAddress
        invalidArgumentExit('name@domain')
    if optional:
      Cmd.Advance()
      return None
    if minLen == 0:
      Cmd.Advance()
      return ''
  elif optional:
    return None
  missingArgumentExit([Cmd.OB_EMAIL_ADDRESS_OR_UID, Cmd.OB_EMAIL_ADDRESS][noUid])

def getFilename():
  filename = os.path.expanduser(getString(Cmd.OB_FILE_NAME))
  if os.path.isfile(filename):
    return filename
  entityDoesNotExistExit(Ent.FILE, filename)

def getPermissionId():
  if Cmd.ArgumentsRemaining():
    emailAddress = Cmd.Current().strip()
    if emailAddress:
      cg = UID_PATTERN.match(emailAddress)
      if cg:
        Cmd.Advance()
        return (False, cg.group(1))
      emailAddress = emailAddress.lower()
      atLoc = emailAddress.find('@')
      if atLoc == -1:
        if emailAddress == 'anyone':
          Cmd.Advance()
          return (False, emailAddress)
        if emailAddress == 'anyonewithlink':
          Cmd.Advance()
          return (False, 'anyoneWithLink')
        if GC.Values[GC.DOMAIN]:
          emailAddress = f'{emailAddress}@{GC.Values[GC.DOMAIN]}'
        Cmd.Advance()
        return (True, emailAddress)
      if atLoc != 0:
        if (atLoc == len(emailAddress)-1) and GC.Values[GC.DOMAIN]:
          emailAddress = f'{emailAddress}{GC.Values[GC.DOMAIN]}'
        Cmd.Advance()
        return (True, emailAddress)
      invalidArgumentExit('name@domain')
  missingArgumentExit(Cmd.OB_DRIVE_FILE_PERMISSION_ID)

def getGoogleProduct():
  if Cmd.ArgumentsRemaining():
    product = Cmd.Current().strip()
    if product:
      status, productId = SKU.normalizeProductId(product)
      if not status:
        invalidChoiceExit(productId, SKU.getSortedProductList(), False)
      Cmd.Advance()
      return productId
  missingArgumentExit(Cmd.OB_PRODUCT_ID)

def getGoogleProductList():
  if Cmd.ArgumentsRemaining():
    productsList = []
    for product in Cmd.Current().split(','):
      status, productId = SKU.normalizeProductId(product)
      if not status:
        invalidChoiceExit(productId, SKU.getSortedProductList(), False)
      if productId not in productsList:
        productsList.append(productId)
    Cmd.Advance()
    return productsList
  missingArgumentExit(Cmd.OB_PRODUCT_ID_LIST)

def getGoogleSKU():
  if Cmd.ArgumentsRemaining():
    sku = Cmd.Current().strip()
    if sku:
      Cmd.Advance()
      return SKU.getProductAndSKU(sku)
  missingArgumentExit(Cmd.OB_SKU_ID)

def getGoogleSKUList(allowUnknownProduct=False):
  if Cmd.ArgumentsRemaining():
    skusList = []
    for sku in Cmd.Current().split(','):
      productId, sku = SKU.getProductAndSKU(sku)
      if not productId and not allowUnknownProduct:
        invalidChoiceExit(sku, SKU.getSortedSKUList(), False)
      if (productId, sku) not in skusList:
        skusList.append((productId, sku))
    Cmd.Advance()
    return skusList
  missingArgumentExit(Cmd.OB_SKU_ID_LIST)

def floatLimits(minVal, maxVal, item='float'):
  if (minVal is not None) and (maxVal is not None):
    return f'{item} {minVal:.3f}<=x<={maxVal:.3f}'
  if minVal is not None:
    return f'{item} x>={minVal:.3f}'
  if maxVal is not None:
    return f'{item} x<={maxVal:.3f}'
  return f'{item} x'

def getFloat(minVal=None, maxVal=None):
  if Cmd.ArgumentsRemaining():
    try:
      number = float(Cmd.Current().strip())
      if ((minVal is None) or (number >= minVal)) and ((maxVal is None) or (number <= maxVal)):
        Cmd.Advance()
        return number
    except ValueError:
      pass
    invalidArgumentExit(floatLimits(minVal, maxVal))
  missingArgumentExit(floatLimits(minVal, maxVal))

def integerLimits(minVal, maxVal, item='integer'):
  if (minVal is not None) and (maxVal is not None):
    return f'{item} {minVal}<=x<={maxVal}'
  if minVal is not None:
    return f'{item} x>={minVal}'
  if maxVal is not None:
    return f'{item} x<={maxVal}'
  return f'{item} x'

def getInteger(minVal=None, maxVal=None, default=None):
  if Cmd.ArgumentsRemaining():
    try:
      number = int(Cmd.Current().strip())
      if ((minVal is None) or (number >= minVal)) and ((maxVal is None) or (number <= maxVal)):
        Cmd.Advance()
        return number
    except ValueError:
      if default is not None:
        if not Cmd.Current().strip(): # If current argument is empty, skip over it
          Cmd.Advance()
        return default
    invalidArgumentExit(integerLimits(minVal, maxVal))
  elif default is not None:
    return default
  missingArgumentExit(integerLimits(minVal, maxVal))

def getIntegerEmptyAllowed(minVal=None, maxVal=None, default=0):
  if Cmd.ArgumentsRemaining():
    number = Cmd.Current().strip()
    if not number:
      Cmd.Advance()
      return default
    try:
      number = int(number)
      if ((minVal is None) or (number >= minVal)) and ((maxVal is None) or (number <= maxVal)):
        Cmd.Advance()
        return number
    except ValueError:
      pass
    invalidArgumentExit(integerLimits(minVal, maxVal))
  return default

def getNumberRangeList():
  if Cmd.ArgumentsRemaining():
    numberlist = []
    for number in Cmd.Current().strip().replace(',', ' ').split():
      if number.isdigit():
        numberlist.append(int(number))
      elif '/' in number:
        lrange, urange = number.split('/', 1)
        if lrange.isdigit() and urange.isdigit() and int(lrange) <= int(urange):
          for n in range(int(lrange), int(urange)+1):
            numberlist.append(n)
        else:
          invalidArgumentExit(Cmd.OB_NUMBER_RANGE_LIST)
      else:
        invalidArgumentExit(Cmd.OB_NUMBER_RANGE_LIST)
    Cmd.Advance()
    return sorted(numberlist)
  missingArgumentExit(Cmd.OB_NUMBER_RANGE_LIST)

SORTORDER_CHOICE_MAP = {'ascending': 'ASCENDING', 'descending': 'DESCENDING'}

class OrderBy():
  def __init__(self, choiceMap, ascendingKeyword='', descendingKeyword='desc'):
    self.choiceMap = choiceMap
    self.ascendingKeyword = ascendingKeyword
    self.descendingKeyword = descendingKeyword
    self.items = []

  def GetChoice(self):
    fieldName = getChoice(self.choiceMap, mapChoice=True)
    fieldNameAscending = fieldName
    if self.ascendingKeyword:
      fieldNameAscending += f' {self.ascendingKeyword}'
    if fieldNameAscending in self.items:
      self.items.remove(fieldNameAscending)
    fieldNameDescending = fieldName
    if self.descendingKeyword:
      fieldNameDescending += f' {self.descendingKeyword}'
    if fieldNameDescending in self.items:
      self.items.remove(fieldNameDescending)
    if getChoice(SORTORDER_CHOICE_MAP, defaultChoice=None, mapChoice=True) != 'DESCENDING':
      self.items.append(fieldNameAscending)
    else:
      self.items.append(fieldNameDescending)

  def SetItems(self, itemList):
    self.items = itemList.split(',')

  @property
  def orderBy(self):
    return ','.join(self.items)

def getOrderBySortOrder(choiceMap, defaultSortOrderChoice='ASCENDING', mapSortOrderChoice=True):
  return (getChoice(choiceMap, mapChoice=True),
          getChoice(SORTORDER_CHOICE_MAP, defaultChoice=defaultSortOrderChoice, mapChoice=mapSortOrderChoice))

def orgUnitPathQuery(path, isSuspended, isArchived):
  query = "orgUnitPath='{0}'".format(path.replace("'", "\\'")) if path != '/' else ''
  if isSuspended is not None:
    query += f' isSuspended={isSuspended}'
  if isArchived is not None:
    query += f' isArchived={isArchived}'
  return query

def makeOrgUnitPathAbsolute(path):
  if path == '/':
    return path
  if path.startswith('/'):
    if not path.endswith('/'):
      return path
    return path[:-1]
  if path.startswith('id:'):
    return path
  if path.startswith('uid:'):
    return path[1:]
  if not path.endswith('/'):
    return '/'+path
  return '/'+path[:-1]

def makeOrgUnitPathRelative(path):
  if path == '/':
    return path
  if path.startswith('/'):
    if not path.endswith('/'):
      return path[1:]
    return path[1:-1]
  if path.startswith('id:'):
    return path
  if path.startswith('uid:'):
    return path[1:]
  if not path.endswith('/'):
    return path
  return path[:-1]

def encodeOrgUnitPath(path):
# 6.22.19 - Encoding doesn't work
# % no longer needs encoding and + is handled incorrectly in API with or without encoding
  return path
#  if path.find('+') == -1 and path.find('%') == -1:
#    return path
#  encpath = ''
#  for c in path:
#    if c == '+':
#      encpath += '%2B'
#    elif c == '%':
#      encpath += '%25'
#    else:
#      encpath += c
#  return encpath

def validateREPattern(patstr, flags=0):
  try:
    return re.compile(patstr, flags)
  except re.error as e:
    Cmd.Backup()
    usageErrorExit(f'{Cmd.OB_RE_PATTERN} {Msg.ERROR}: {e}')

def getREPattern(flags=0):
  if Cmd.ArgumentsRemaining():
    patstr = Cmd.Current()
    if patstr:
      Cmd.Advance()
      return validateREPattern(patstr, flags)
  missingArgumentExit(Cmd.OB_RE_PATTERN)

def validateREPatternSubstitution(pattern, replacement):
  try:
    re.sub(pattern, replacement, '')
    return (pattern, replacement)
  except re.error as e:
    Cmd.Backup()
    usageErrorExit(f'{Cmd.OB_RE_SUBSTITUTION} {Msg.ERROR}: {e}')

def getREPatternSubstitution(flags=0):
  pattern = getREPattern(flags)
  replacement = getString(Cmd.OB_RE_SUBSTITUTION, minLen=0)
  return validateREPatternSubstitution(pattern, replacement)

def getSheetEntity(allowBlankSheet):
  if Cmd.ArgumentsRemaining():
    sheet = Cmd.Current()
    if sheet or allowBlankSheet:
      cg = UID_PATTERN.match(sheet)
      if cg:
        if cg.group(1).isdigit():
          Cmd.Advance()
          return {'sheetType': Ent.SHEET_ID, 'sheetValue': int(cg.group(1)), 'sheetId': int(cg.group(1)), 'sheetTitle': ''}
      else:
        Cmd.Advance()
        return {'sheetType': Ent.SHEET, 'sheetValue': sheet, 'sheetId': None, 'sheetTitle': sheet}
  missingArgumentExit(Cmd.OB_SHEET_ENTITY)

def getSheetIdFromSheetEntity(spreadsheet, sheetEntity):
  if sheetEntity['sheetType'] == Ent.SHEET_ID:
    for sheet in spreadsheet['sheets']:
      if sheetEntity['sheetId'] == sheet['properties']['sheetId']:
        return sheet['properties']['sheetId']
  else:
    sheetTitleLower = sheetEntity['sheetTitle'].lower()
    for sheet in spreadsheet['sheets']:
      if sheetTitleLower == sheet['properties']['title'].lower():
        return sheet['properties']['sheetId']
  return None

def protectedSheetId(spreadsheet, sheetId):
  for sheet in spreadsheet['sheets']:
    for protectedRange in sheet.get('protectedRanges', []):
      if protectedRange.get('range', {}).get('sheetId', -1) == sheetId and not protectedRange.get('requestingUserCanEdit', False):
        return True
  return False

def getString(item, checkBlank=False, optional=False, minLen=1, maxLen=None):
  if Cmd.ArgumentsRemaining():
    argstr = Cmd.Current()
    if argstr:
      if checkBlank:
        if argstr.isspace():
          blankArgumentExit(item)
      if (len(argstr) >= minLen) and ((maxLen is None) or (len(argstr) <= maxLen)):
        Cmd.Advance()
        return argstr
      invalidArgumentExit(f'{integerLimits(minLen, maxLen, Msg.STRING_LENGTH)} for {item}')
    if optional or (minLen == 0):
      Cmd.Advance()
      return ''
    emptyArgumentExit(item)
  elif optional:
    return ''
  missingArgumentExit(item)

def escapeCRsNLs(value):
  return value.replace('\r', '\\r').replace('\n', '\\n')

def unescapeCRsNLs(value):
  return value.replace('\\r', '\r').replace('\\n', '\n')

def getStringWithCRsNLs():
  return unescapeCRsNLs(getString(Cmd.OB_STRING, minLen=0))

def getStringReturnInList(item):
  argstr = getString(item, minLen=0).strip()
  if argstr:
    return [argstr]
  return []

SORF_SIG_ARGUMENTS = {'signature', 'sig', 'textsig', 'htmlsig'}
SORF_MSG_ARGUMENTS = {'message', 'textmessage', 'htmlmessage'}
SORF_FILE_ARGUMENTS = {'file', 'textfile', 'htmlfile', 'gdoc', 'ghtml', 'gcsdoc', 'gcshtml'}
SORF_HTML_ARGUMENTS = {'htmlsig', 'htmlmessage', 'htmlfile', 'ghtml', 'gcshtml'}
SORF_TEXT_ARGUMENTS = {'text', 'textfile', 'gdoc', 'gcsdoc'}
SORF_SIG_FILE_ARGUMENTS = SORF_SIG_ARGUMENTS.union(SORF_FILE_ARGUMENTS)
SORF_MSG_FILE_ARGUMENTS = SORF_MSG_ARGUMENTS.union(SORF_FILE_ARGUMENTS)

def getStringOrFile(myarg, minLen=0, unescapeCRLF=False):
  if myarg in SORF_SIG_ARGUMENTS:
    if checkArgumentPresent(SORF_FILE_ARGUMENTS):
      myarg = Cmd.Previous().strip().lower().replace('_', '')
  html = myarg in SORF_HTML_ARGUMENTS
  if myarg in SORF_FILE_ARGUMENTS:
    if myarg in {'file', 'textfile', 'htmlfile'}:
      filename = getString(Cmd.OB_FILE_NAME)
      encoding = getCharSet()
      return (readFile(setFilePath(filename, GC.INPUT_DIR), encoding=encoding), encoding, html)
    if myarg in {'gdoc', 'ghtml'}:
      f = getGDocData(myarg)
      data = f.read()
      f.close()
      return (data, UTF8, html)
    return (getStorageFileData(myarg), UTF8, html)
  if not unescapeCRLF:
    return (getString(Cmd.OB_STRING, minLen=minLen), UTF8, html)
  return (unescapeCRsNLs(getString(Cmd.OB_STRING, minLen=minLen)), UTF8, html)

def getStringWithCRsNLsOrFile():
  if checkArgumentPresent(SORF_FILE_ARGUMENTS):
    return getStringOrFile(Cmd.Previous().strip().lower().replace('_', ''), minLen=0)
  return (unescapeCRsNLs(getString(Cmd.OB_STRING, minLen=0)), UTF8, False)

def getAddCSVData(addCSVData):
  k = getString(Cmd.OB_STRING)
  addCSVData[k] = getString(Cmd.OB_STRING, minLen=0)

def todaysDate():
  return arrow.Arrow(GM.Globals[GM.DATETIME_NOW].year, GM.Globals[GM.DATETIME_NOW].month, GM.Globals[GM.DATETIME_NOW].day,
                     tzinfo=GC.Values[GC.TIMEZONE])

def todaysTime():
  return arrow.Arrow(GM.Globals[GM.DATETIME_NOW].year, GM.Globals[GM.DATETIME_NOW].month, GM.Globals[GM.DATETIME_NOW].day,
                     GM.Globals[GM.DATETIME_NOW].hour, GM.Globals[GM.DATETIME_NOW].minute,
                     tzinfo=GC.Values[GC.TIMEZONE])

def getDelta(argstr, pattern):
  if argstr == 'NOW':
    return todaysTime()
  if argstr == 'TODAY':
    return todaysDate()
  tg = pattern.match(argstr.lower())
  if tg is None:
    return None
  sign = tg.group(1)
  delta = int(tg.group(2))
  unit = tg.group(3)
  if sign == '-':
    delta = -delta
  baseTime = todaysDate()
  if unit in {'h', 'm'}:
    baseTime = baseTime.shift(hours=GM.Globals[GM.DATETIME_NOW].hour, minutes=GM.Globals[GM.DATETIME_NOW].minute)
  if unit == 'y':
    return baseTime.shift(days=delta*365)
  if unit == 'w':
    return baseTime.shift(weeks=delta)
  if unit == 'd':
    return baseTime.shift(days=delta)
  if unit == 'h':
    return baseTime.shift(hours=delta)
  if unit == 'm':
    return baseTime.shift(minutes=delta)
  return baseTime

DELTA_DATE_PATTERN = re.compile(r'^([+-])(\d+)([dwy])$')
DELTA_DATE_FORMAT_REQUIRED = '(+|-)<Number>(d|w|y)'
def getDeltaDate(argstr):
  deltaDate = getDelta(argstr, DELTA_DATE_PATTERN)
  if deltaDate is None:
    invalidArgumentExit(DELTA_DATE_FORMAT_REQUIRED)
  return deltaDate

DELTA_TIME_PATTERN = re.compile(r'^([+-])(\d+)([mhdwy])$')
DELTA_TIME_FORMAT_REQUIRED = '(+|-)<Number>(m|h|d|w|y)'

def getDeltaTime(argstr):
  deltaTime = getDelta(argstr, DELTA_TIME_PATTERN)
  if deltaTime is None:
    invalidArgumentExit(DELTA_TIME_FORMAT_REQUIRED)
  return deltaTime

YYYYMMDD_FORMAT = '%Y-%m-%d'
YYYYMMDD_FORMAT_REQUIRED = 'yyyy-mm-dd'

TODAY_NOW = {'TODAY', 'NOW'}
PLUS_MINUS = {'+', '-'}

def getYYYYMMDD(minLen=1, returnTimeStamp=False, returnDateTime=False, alternateValue=None):
  if Cmd.ArgumentsRemaining():
    argstr = Cmd.Current().strip().upper()
    if argstr:
      if alternateValue is not None and argstr == alternateValue.upper():
        Cmd.Advance()
        return None
      if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
        if argstr == 'NOW':
          argstr = 'TODAY'
        argstr = getDeltaDate(argstr).strftime(YYYYMMDD_FORMAT)
      elif argstr == 'NEVER':
        argstr = NEVER_DATE
      try:
        dateTime = arrow.Arrow.strptime(argstr, YYYYMMDD_FORMAT)
        Cmd.Advance()
        if returnTimeStamp:
          return time.mktime(dateTime.timetuple())*1000
        if returnDateTime:
          return dateTime
        return argstr
      except ValueError:
        invalidArgumentExit(YYYYMMDD_FORMAT_REQUIRED)
    elif minLen == 0:
      Cmd.Advance()
      return ''
  missingArgumentExit(YYYYMMDD_FORMAT_REQUIRED)

HHMM_FORMAT = '%H:%M'
HHMM_FORMAT_REQUIRED = 'hh:mm'

def getHHMM():
  if Cmd.ArgumentsRemaining():
    argstr = Cmd.Current().strip().upper()
    if argstr:
      try:
        arrow.Arrow.strptime(argstr, HHMM_FORMAT)
        Cmd.Advance()
        return argstr
      except ValueError:
        invalidArgumentExit(HHMM_FORMAT_REQUIRED)
  missingArgumentExit(HHMM_FORMAT_REQUIRED)

YYYYMMDD_HHMM_FORMAT = '%Y-%m-%d %H:%M'
YYYYMMDD_HHMM_FORMAT_REQUIRED = 'yyyy-mm-dd hh:mm'

def getYYYYMMDD_HHMM():
  if Cmd.ArgumentsRemaining():
    argstr = Cmd.Current().strip().upper()
    if argstr:
      if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
        argstr = getDeltaTime(argstr).strftime(YYYYMMDD_HHMM_FORMAT)
      elif argstr == 'NEVER':
        argstr = NEVER_DATETIME
      argstr = argstr.replace('T', ' ')
      try:
        arrow.Arrow.strptime(argstr, YYYYMMDD_HHMM_FORMAT)
        Cmd.Advance()
        return argstr
      except ValueError:
        invalidArgumentExit(YYYYMMDD_HHMM_FORMAT_REQUIRED)
  missingArgumentExit(YYYYMMDD_HHMM_FORMAT_REQUIRED)

YYYYMMDDTHHMMSSZ_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
YYYYMMDD_PATTERN = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')

def getDateOrDeltaFromNow(returnDateTime=False):
  if Cmd.ArgumentsRemaining():
    argstr = Cmd.Current().strip().upper()
    if argstr:
      if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
        if argstr == 'NOW':
          argstr = 'TODAY'
        argDate = getDeltaDate(argstr)
      elif argstr == 'NEVER':
        argDate = arrow.Arrow.strptime(NEVER_DATE, YYYYMMDD_FORMAT)
      elif YYYYMMDD_PATTERN.match(argstr):
        try:
          argDate = arrow.Arrow.strptime(argstr, YYYYMMDD_FORMAT)
        except ValueError:
          invalidArgumentExit(YYYYMMDD_FORMAT_REQUIRED)
      else:
        invalidArgumentExit(YYYYMMDD_FORMAT_REQUIRED)
      Cmd.Advance()
      if not returnDateTime:
        return argDate.strftime(YYYYMMDD_FORMAT)
      return (arrow.Arrow(argDate.year, argDate.month, argDate.day, tzinfo=GC.Values[GC.TIMEZONE]),
              GC.Values[GC.TIMEZONE], argDate.strftime(YYYYMMDD_FORMAT))
  missingArgumentExit(YYYYMMDD_FORMAT_REQUIRED)

YYYYMMDDTHHMMSS_FORMAT_REQUIRED = 'yyyy-mm-ddThh:mm:ss[.fff](Z|(+|-(hh:mm)))'
TIMEZONE_FORMAT_REQUIRED = 'utc|z|local|(+|-(hh:mm))|<ValidTimezoneName>'

def getTimeOrDeltaFromNow(returnDateTime=False):
  if Cmd.ArgumentsRemaining():
    argstr = Cmd.Current().strip().upper()
    if argstr:
      if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
        argstr = ISOformatTimeStamp(getDeltaTime(argstr))
      elif argstr == 'NEVER':
        argstr = NEVER_TIME
      elif YYYYMMDD_PATTERN.match(argstr):
        try:
          dateTime = arrow.Arrow.strptime(argstr, YYYYMMDD_FORMAT)
        except ValueError:
          invalidArgumentExit(YYYYMMDD_FORMAT_REQUIRED)
        try:
          argstr = ISOformatTimeStamp(dateTime.replace(tzinfo=GC.Values[GC.TIMEZONE]))
        except OverflowError:
          pass
      try:
        fullDateTime = arrow.get(argstr)
        Cmd.Advance()
        if not returnDateTime:
          return argstr.replace(' ', 'T')
        return (fullDateTime, fullDateTime.tzinfo, argstr.replace(' ', 'T'))
      except (arrow.parser.ParserError, OverflowError):
        pass
      invalidArgumentExit(YYYYMMDDTHHMMSS_FORMAT_REQUIRED)
  missingArgumentExit(YYYYMMDDTHHMMSS_FORMAT_REQUIRED)

def getRowFilterDateOrDeltaFromNow(argstr):
  argstr = argstr.strip().upper()
  if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
    if argstr == 'NOW':
      argstr = 'TODAY'
    deltaDate = getDelta(argstr, DELTA_DATE_PATTERN)
    if deltaDate is None:
      return (False, DELTA_DATE_FORMAT_REQUIRED)
    argstr = ISOformatTimeStamp(deltaDate.replace(tzinfo='UTC'))
  elif argstr == 'NEVER' or YYYYMMDD_PATTERN.match(argstr):
    if argstr == 'NEVER':
      argstr = NEVER_DATE
    try:
      dateTime = arrow.Arrow.strptime(argstr, YYYYMMDD_FORMAT)
    except ValueError:
      return (False, YYYYMMDD_FORMAT_REQUIRED)
    argstr = ISOformatTimeStamp(dateTime.replace(tzinfo='UTC'))
  try:
    arrow.get(argstr)
    return (True, argstr.replace(' ', 'T'))
  except (arrow.parser.ParserError, OverflowError):
    return (False, YYYYMMDD_FORMAT_REQUIRED)

def getRowFilterTimeOrDeltaFromNow(argstr):
  argstr = argstr.strip().upper()
  if argstr in TODAY_NOW or argstr[0] in PLUS_MINUS:
    deltaTime = getDelta(argstr, DELTA_TIME_PATTERN)
    if deltaTime is None:
      return (False, DELTA_TIME_FORMAT_REQUIRED)
    argstr = ISOformatTimeStamp(deltaTime)
  elif argstr == 'NEVER':
    argstr = NEVER_TIME
  elif YYYYMMDD_PATTERN.match(argstr):
    try:
      dateTime = arrow.Arrow.strptime(argstr, YYYYMMDD_FORMAT)
    except ValueError:
      return (False, YYYYMMDD_FORMAT_REQUIRED)
    argstr = ISOformatTimeStamp(dateTime.replace(tzinfo=GC.Values[GC.TIMEZONE]))
  try:
    arrow.get(argstr)
    return (True, argstr.replace(' ', 'T'))
  except (arrow.parser.ParserError, OverflowError):
    return (False, YYYYMMDDTHHMMSS_FORMAT_REQUIRED)

def mapQueryRelativeTimes(query, keywords):
  QUOTES = '\'"'
  for kw in keywords:
    pattern = re.compile(rf'({kw})\s*([<>]=?|=|!=)\s*[{QUOTES}]?(now|today|[+-]\d+[mhdwy])', re.IGNORECASE)
    pos = 0
    while True:
      mg = pattern.search(query, pos)
      if not mg:
        break
      if mg.groups()[2] is not None:
        deltaTime = getDelta(mg.group(3).upper(), DELTA_TIME_PATTERN)
        if deltaTime:
          query = query[:mg.start(3)]+ISOformatTimeStamp(deltaTime)+query[mg.end(3):]
      pos = mg.end()
  return query

class StartEndTime():
  def __init__(self, startkw='starttime', endkw='endtime', mode='time'):
    self.startTime = self.endTime = self.startDateTime = self.endDateTime = None
    self._startkw = startkw
    self._endkw = endkw
    self._getValueOrDeltaFromNow = getTimeOrDeltaFromNow if mode == 'time' else getDateOrDeltaFromNow

  def Get(self, myarg):
    if myarg in {'start', self._startkw}:
      self.startDateTime, _, self.startTime = self._getValueOrDeltaFromNow(True)
    elif myarg in {'end', self._endkw}:
      self.endDateTime, _, self.endTime = self._getValueOrDeltaFromNow(True)
    elif myarg == 'yesterday':
      currDate = todaysDate()
      self.startDateTime = currDate.shift(days=-1)
      self.startTime = ISOformatTimeStamp(self.startDateTime)
      self.endDateTime = currDate.shift(seconds=-1)
      self.endTime = ISOformatTimeStamp(self.endDateTime)
    elif myarg == 'today':
      currDate = todaysDate()
      self.startDateTime = currDate
      self.startTime = ISOformatTimeStamp(self.startDateTime)
    elif myarg == 'range':
      self.startDateTime, _, self.startTime = self._getValueOrDeltaFromNow(True)
      self.endDateTime, _, self.endTime = self._getValueOrDeltaFromNow(True)
    else: #elif myarg in {'thismonth', 'previousmonths'}
      if myarg == 'thismonth':
        firstMonth = 0
      else:
        firstMonth = getInteger(minVal=1, maxVal=6)
      currDate = todaysDate()
      self.startDateTime = currDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0).shift(months=-firstMonth)
      self.startTime = ISOformatTimeStamp(self.startDateTime)
      if myarg == 'thismonth':
        self.endDateTime = todaysTime()
      else:
        self.endDateTime = currDate.replace(day=1, hour=23, minute=59, second=59, microsecond=0).shift(days=-1)
      self.endTime = ISOformatTimeStamp(self.endDateTime)
    if self.startDateTime and self.endDateTime and self.endDateTime < self.startDateTime:
      Cmd.Backup()
      usageErrorExit(Msg.INVALID_DATE_TIME_RANGE.format(self._endkw, self.endTime, self._startkw, self.startTime))

EVENTID_PATTERN = re.compile(r'^[a-v0-9]{5,1024}$')
EVENTID_FORMAT_REQUIRED = '[a-v0-9]{5,1024}'

def getEventID():
  if Cmd.ArgumentsRemaining():
    tg = EVENTID_PATTERN.match(Cmd.Current().strip())
    if tg:
      Cmd.Advance()
      return tg.group(0)
    invalidArgumentExit(EVENTID_FORMAT_REQUIRED)
  missingArgumentExit(EVENTID_FORMAT_REQUIRED)

EVENT_TIME_FORMAT_REQUIRED = 'allday yyyy-mm-dd | '+YYYYMMDDTHHMMSS_FORMAT_REQUIRED

def getEventTime():
  if Cmd.ArgumentsRemaining():
    if Cmd.Current().strip().lower() == 'allday':
      Cmd.Advance()
      return {'date': getYYYYMMDD()}
    return {'dateTime': getTimeOrDeltaFromNow()}
  missingArgumentExit(EVENT_TIME_FORMAT_REQUIRED)

AGE_TIME_PATTERN = re.compile(r'^(\d+)([mhdw])$')
AGE_TIME_FORMAT_REQUIRED = '<Number>(m|h|d|w)'

def getAgeTime():
  if Cmd.ArgumentsRemaining():
    tg = AGE_TIME_PATTERN.match(Cmd.Current().strip().lower())
    if tg:
      age = int(tg.group(1))
      age_unit = tg.group(2)
      now = int(time.time())
      if age_unit == 'm':
        age = now-(age*SECONDS_PER_MINUTE)
      elif age_unit == 'h':
        age = now-(age*SECONDS_PER_HOUR)
      elif age_unit == 'd':
        age = now-(age*SECONDS_PER_DAY)
      else: # age_unit == 'w':
        age = now-(age*SECONDS_PER_WEEK)
      Cmd.Advance()
      return age*1000
    invalidArgumentExit(AGE_TIME_FORMAT_REQUIRED)
  missingArgumentExit(AGE_TIME_FORMAT_REQUIRED)

CALENDAR_REMINDER_METHODS = ['email', 'popup']
CALENDAR_REMINDER_MAX_MINUTES = 40320

def getCalendarReminder(allowClearNone=False):
  methods = CALENDAR_REMINDER_METHODS[:]
  if allowClearNone:
    methods += Cmd.CLEAR_NONE_ARGUMENT
  if Cmd.ArgumentsRemaining():
    method = Cmd.Current().strip()
    if not method.isdigit():
      method = getChoice(methods)
      minutes = getInteger(minVal=0, maxVal=CALENDAR_REMINDER_MAX_MINUTES)
    else:
      minutes = getInteger(minVal=0, maxVal=CALENDAR_REMINDER_MAX_MINUTES)
      method = getChoice(methods)
    return {'method': method, 'minutes': minutes}
  missingChoiceExit(methods)

def getCharacter():
  if Cmd.ArgumentsRemaining():
    argstr = codecs.escape_decode(bytes(Cmd.Current(), UTF8))[0].decode(UTF8)
    if argstr:
      if len(argstr) == 1:
        Cmd.Advance()
        return argstr
      invalidArgumentExit(f'{integerLimits(1, 1, Msg.STRING_LENGTH)} for {Cmd.OB_CHARACTER}')
    emptyArgumentExit(Cmd.OB_CHARACTER)
  missingArgumentExit(Cmd.OB_CHARACTER)

def getDelimiter():
  if not checkArgumentPresent('delimiter'):
    return None
  return getCharacter()

def getJSON(deleteFields):
  if not checkArgumentPresent('file'):
    encoding = getCharSet()
    if not Cmd.ArgumentsRemaining():
      missingArgumentExit(Cmd.OB_JSON_DATA)
    argstr = Cmd.Current()
#    argstr = Cmd.Current().replace(r'\\"', r'\"')
    Cmd.Advance()
    try:
      if encoding == UTF8:
        jsonData = json.loads(argstr)
      else:
        jsonData = json.loads(argstr.encode(encoding).decode(UTF8))
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      Cmd.Backup()
      usageErrorExit(f'{str(e)}: {argstr if encoding == UTF8 else argstr.encode(encoding).decode(UTF8)}')
  else:
    filename = getString(Cmd.OB_FILE_NAME)
    encoding = getCharSet()
    try:
      jsonData = json.loads(readFile(setFilePath(filename, GC.INPUT_DIR), encoding=encoding))
    except (IndexError, KeyError, SyntaxError, TypeError, ValueError) as e:
      Cmd.Backup()
      usageErrorExit(Msg.JSON_ERROR.format(str(e), filename))
  for field in deleteFields:
    jsonData.pop(field, None)
  return jsonData

def getMatchSkipFields(fieldNames):
  matchFields = {}
  skipFields = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg in {'matchfield', 'skipfield'}:
      matchField = getString(Cmd.OB_FIELD_NAME).strip('~')
      if (not matchField) or (matchField not in fieldNames):
        csvFieldErrorExit(matchField, fieldNames, backupArg=True)
      if myarg == 'matchfield':
        matchFields[matchField] = getREPattern()
      else:
        skipFields[matchField] = getREPattern()
    else:
      Cmd.Backup()
      break
  return (matchFields, skipFields)

def checkMatchSkipFields(row, fieldnames, matchFields, skipFields):
  for matchField, matchPattern in matchFields.items():
    if (matchField not in row) or not matchPattern.search(str(row[matchField])):
      return False
  for skipField, matchPattern in skipFields.items():
    if (skipField in row) and matchPattern.search(str(row[skipField])):
      return False
  if fieldnames and (GC.Values[GC.CSV_INPUT_ROW_FILTER] or GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER]):
    return RowFilterMatch(row, fieldnames,
                          GC.Values[GC.CSV_INPUT_ROW_FILTER], GC.Values[GC.CSV_INPUT_ROW_FILTER_MODE],
                          GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER], GC.Values[GC.CSV_INPUT_ROW_DROP_FILTER_MODE])
  return True

def checkSubkeyField():
  if not GM.Globals[GM.CSV_SUBKEY_FIELD]:
    Cmd.Backup()
    usageErrorExit(Msg.NO_CSV_FILE_SUBKEYS_SAVED)
  chkSubkeyField = getString(Cmd.OB_FIELD_NAME, checkBlank=True)
  if chkSubkeyField != GM.Globals[GM.CSV_SUBKEY_FIELD]:
    Cmd.Backup()
    usageErrorExit(Msg.SUBKEY_FIELD_MISMATCH.format(chkSubkeyField, GM.Globals[GM.CSV_SUBKEY_FIELD]))

def checkDataField():
  if not GM.Globals[GM.CSV_DATA_FIELD]:
    Cmd.Backup()
    usageErrorExit(Msg.NO_CSV_FILE_DATA_SAVED)
  chkDataField = getString(Cmd.OB_FIELD_NAME, checkBlank=True)
  if chkDataField != GM.Globals[GM.CSV_DATA_FIELD]:
    Cmd.Backup()
    usageErrorExit(Msg.DATA_FIELD_MISMATCH.format(chkDataField, GM.Globals[GM.CSV_DATA_FIELD]))

MAX_MESSAGE_BYTES_PATTERN = re.compile(r'^(\d+)([mkb]?)$')
MAX_MESSAGE_BYTES_FORMAT_REQUIRED = '<Number>[m|k|b]'

def getMaxMessageBytes(oneKiloBytes, oneMegaBytes):
  if Cmd.ArgumentsRemaining():
    tg = MAX_MESSAGE_BYTES_PATTERN.match(Cmd.Current().strip().lower())
    if tg:
      mmb = int(tg.group(1))
      mmb_unit = tg.group(2)
      if mmb_unit == 'm':
        mmb *= oneMegaBytes
      elif mmb_unit == 'k':
        mmb *= oneKiloBytes
      Cmd.Advance()
      return mmb
    invalidArgumentExit(MAX_MESSAGE_BYTES_FORMAT_REQUIRED)
  missingArgumentExit(MAX_MESSAGE_BYTES_FORMAT_REQUIRED)

# Get domain from email address
def getEmailAddressDomain(emailAddress):
  atLoc = emailAddress.find('@')
  if atLoc == -1:
    return GC.Values[GC.DOMAIN]
  return emailAddress[atLoc+1:].lower()

# Get user name from email address
def getEmailAddressUsername(emailAddress):
  atLoc = emailAddress.find('@')
  if atLoc == -1:
    return emailAddress.lower()
  return emailAddress[:atLoc].lower()

# Split email address into user and domain
def splitEmailAddress(emailAddress):
  atLoc = emailAddress.find('@')
  if atLoc == -1:
    return (emailAddress.lower(), GC.Values[GC.DOMAIN])
  return (emailAddress[:atLoc].lower(), emailAddress[atLoc+1:].lower())

def formatFileSize(size):
  if size == 0:
    return '0 KB'
  if size < ONE_KILO_10_BYTES:
    return '1 KB'
  if size < ONE_MEGA_10_BYTES:
    return f'{size/ONE_KILO_10_BYTES:.2f} KB'
  if size < ONE_GIGA_10_BYTES:
    return f'{size/ONE_MEGA_10_BYTES:.2f} MB'
  if size < ONE_TERA_10_BYTES:
    return f'{size/ONE_GIGA_10_BYTES:.2f} GB'
  return f'{size/ONE_TERA_10_BYTES:.2f} TB'

def formatLocalTime(dateTimeStr):
  if dateTimeStr in {NEVER_TIME, NEVER_TIME_NOMS}:
    return GC.Values[GC.NEVER_TIME]
  try:
    timestamp = arrow.get(dateTimeStr)
    if not GC.Values[GC.OUTPUT_TIMEFORMAT]:
      if GM.Globals[GM.CONVERT_TO_LOCAL_TIME]:
        return ISOformatTimeStamp(timestamp.astimezone(GC.Values[GC.TIMEZONE]))
      return timestamp.strftime(YYYYMMDDTHHMMSSZ_FORMAT)
    if GM.Globals[GM.CONVERT_TO_LOCAL_TIME]:
      return timestamp.astimezone(GC.Values[GC.TIMEZONE]).strftime(GC.Values[GC.OUTPUT_TIMEFORMAT])
    return timestamp.strftime(GC.Values[GC.OUTPUT_TIMEFORMAT])
  except (arrow.parser.ParserError, OverflowError):
    return dateTimeStr

def formatLocalSecondsTimestamp(timestamp):
  if not GC.Values[GC.OUTPUT_TIMEFORMAT]:
    return ISOformatTimeStamp(arrow.Arrow.fromtimestamp(int(timestamp), GC.Values[GC.TIMEZONE]))
  return arrow.Arrow.fromtimestamp(int(timestamp), GC.Values[GC.TIMEZONE]).strftime(GC.Values[GC.OUTPUT_TIMEFORMAT])

def formatLocalTimestamp(timestamp):
  if not GC.Values[GC.OUTPUT_TIMEFORMAT]:
    return ISOformatTimeStamp(arrow.Arrow.fromtimestamp(int(timestamp)//1000, GC.Values[GC.TIMEZONE]))
  return arrow.Arrow.fromtimestamp(int(timestamp)//1000, GC.Values[GC.TIMEZONE]).strftime(GC.Values[GC.OUTPUT_TIMEFORMAT])

def formatLocalTimestampUTC(timestamp):
  return ISOformatTimeStamp(arrow.Arrow.fromtimestamp(int(timestamp)//1000, 'UTC'))

def formatLocalDatestamp(timestamp):
  try:
    if not GC.Values[GC.OUTPUT_DATEFORMAT]:
      return arrow.Arrow.fromtimestamp(int(timestamp)//1000, GC.Values[GC.TIMEZONE]).strftime(YYYYMMDD_FORMAT)
    return arrow.Arrow.fromtimestamp(int(timestamp)//1000, GC.Values[GC.TIMEZONE]).strftime(GC.Values[GC.OUTPUT_DATEFORMAT])
  except OverflowError:
    return NEVER_DATE

def formatMaxMessageBytes(maxMessageBytes, oneKiloBytes, oneMegaBytes):
  if maxMessageBytes < oneKiloBytes:
    return maxMessageBytes
  if maxMessageBytes < oneMegaBytes:
    return f'{maxMessageBytes//oneKiloBytes}K'
  return f'{maxMessageBytes//oneMegaBytes}M'

def formatMilliSeconds(millis):
  seconds, millis = divmod(millis, 1000)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

def getPhraseDNEorSNA(email):
  return Msg.DOES_NOT_EXIST if getEmailAddressDomain(email) == GC.Values[GC.DOMAIN] else Msg.SERVICE_NOT_APPLICABLE

def formatHTTPError(http_status, reason, message):
  return f'{http_status}: {reason} - {message}'

def getHTTPError(responses, http_status, reason, message):
  if reason in responses:
    return responses[reason]
  return formatHTTPError(http_status, reason, message)

def substituteQueryTimes(queries, queryTimes):
  if queryTimes:
    for i, query in enumerate(queries):
      if query is not None:
        for queryTimeName, queryTimeValue in queryTimes.items():
          query = query.replace(f'#{queryTimeName}#', queryTimeValue)
        queries[i] = query

def _getFilterDateTime():
  filterDate = getYYYYMMDD(returnDateTime=True)
  return (filterDate, filterDate.replace(tzinfo='UTC'))

def shlexSplitList(entity, dataDelimiter=' ,'):
  lexer = shlex.shlex(entity, posix=True)
  lexer.whitespace = dataDelimiter
  lexer.whitespace_split = True
  try:
    return list(lexer)
  except ValueError as e:
    Cmd.Backup()
    usageErrorExit(str(e))

def shlexSplitListStatus(entity, dataDelimiter=' ,'):
  lexer = shlex.shlex(entity, posix=True)
  lexer.whitespace = dataDelimiter
  lexer.whitespace_split = True
  try:
    return (True, list(lexer))
  except ValueError as e:
    return (False, str(e))
