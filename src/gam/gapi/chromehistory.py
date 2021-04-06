"""Chrome Version History API calls"""

import sys

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam import utils


def build():
    return gam.buildGAPIObjectNoAuthentication('versionhistory')


CHROME_HISTORY_ENTITY_CHOICES = {
  'platforms',
  'channels',
  'versions',
  'releases',
  }

CHROME_PLATFORM_CHOICE_MAP = {
  'all': 'all',
  'android': 'android',
  'ios': 'ios',
  'lacros': 'lacros',
  'linux': 'linux',
  'mac': 'mac',
  'macarm64': 'mac_arm64',
  'sebview': 'webview',
  'win': 'win',
  'win64': 'win64',
  }

CHROME_CHANNEL_CHOICE_MAP = {
  'beta': 'beta',
  'canary': 'canary',
  'canaryasan': 'canary_asan',
  'dev': 'dev',
  'stable': 'stable',
  }

CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP = {
  'versions':  {
    'channel': 'channel',
    'name': 'name',
    'platform': 'platform',
    'version': 'version'
    },
  'releases': {
    'channel': 'channel',
    'endtime': 'endtime',
    'fraction': 'fraction',
    'name': 'name',
    'platform': 'platform',
    'starttime': 'starttime',
    'version': 'version'
    }
  }

CHROME_VERSIONHISTORY_TITLES = {
  'platforms': ['name', 'platformType'],
  'channels':  ['name', 'channelType'],
  'versions': ['name', 'version'],
  'releases': ['name', 'version', 'fraction', 'serving.startTime', 'serving.endTime']
  }

def get_relative_milestone(channel='stable', minus=0):
    ''' takes a channel and minus_versions like stable and -1. returns current given  milestone number '''
    cv = build()
    svc = cv.platforms().channels().versions().releases()
    parent = f'chrome/platforms/all/channels/{channel}/versions/all'
    releases = gapi.get_all_pages(cv.platforms().channels().versions().releases(),
                                  'list',
                                  'releases',
                                  parent=parent,
                                  fields='releases/version,nextPageToken')
    milestones = []
    # Note that milestones are usually sequential but some numbers
    # may be skipped. For example, there was no Chrome 82 stable.
    # Thus we need to do more than find the latest version and subtract.
    for release in releases:
        milestone = release.get('version').split('.')[0]
        if milestone not in milestones:
            milestones.append(milestone)
    milestones.sort(reverse=True)
    try:
        return milestones[minus]
    except IndexError:
        return ''

def printHistory():
    cv = build()
    entityType = sys.argv[3].lower().replace('_', '')
    if entityType not in CHROME_HISTORY_ENTITY_CHOICES:
        msg = f'{entityType} is not a valid argument to "gam print chromehistory"'
        controlflow.system_error_exit(3, msg)
    todrive = False
    csvRows = []
    cplatform = 'all'
    channel = 'all'
    version = 'all'
    kwargs = {}
    orderByList = []
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif entityType != 'platforms' and myarg == 'platform':
            cplatform = sys.argv[i + 1].lower().replace('_', '')
            if cplatform not in CHROME_PLATFORM_CHOICE_MAP:
                controlflow.expected_argument_exit('platform',
                                                   ', '.join(CHROME_PLATFORM_CHOICE_MAP),
                                                   cplatform)
            cplatform = CHROME_PLATFORM_CHOICE_MAP[cplatform]
            i += 2
        elif entityType in {'versions', 'releases'} and myarg == 'channel':
            channel = sys.argv[i + 1].lower().replace('_', '')
            if channel not in CHROME_CHANNEL_CHOICE_MAP:
                controlflow.expected_argument_exit('channel',
                                                   ', '.join(CHROME_CHANNEL_CHOICE_MAP),
                                                   channel)
            channel = CHROME_CHANNEL_CHOICE_MAP[channel]
            i += 2
        elif entityType == 'releases' and myarg == 'version':
            version = sys.argv[i + 1]
            i += 2
        elif entityType in {'versions', 'releases'} and myarg == 'orderby':
            fieldName = sys.argv[i + 1].lower().replace('_', '')
            i += 2
            if fieldName in CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP[entityType]:
                fieldName = CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP[entityType][fieldName]
                orderBy = ''
                if i < len(sys.argv):
                    orderBy = sys.argv[i].lower()
                    if orderBy in SORTORDER_CHOICES_MAP:
                        orderBy = SORTORDER_CHOICES_MAP[orderBy]
                        i += 1
                if orderBy != 'DESCENDING':
                    orderByList.append(fieldName)
                else:
                    orderByList.append(f'{fieldName} desc')
            else:
                controlflow.expected_argument_exit('orderby',
                                                   ', '.join(CHROME_VERSIONHISTORY_ORDERBY_CHOICE_MAP[entityType]),
                                                   fieldName)
        elif entityType in {'versions', 'releases'} and myarg == 'filter':
            kwargs['filter'] = sys.argv[i + 1]
            i += 2
        else:
            msg = f'{myarg} is not a valid argument to "gam print chromehistory {entityType}"'
            controlflow.system_error_exit(3, msg)
    if orderByList:
        kwargs['orderBy'] = ','.join(orderByList)
    if entityType == 'platforms':
        svc = cv.platforms()
        parent = 'chrome'
    elif entityType == 'channels':
        svc = cv.platforms().channels()
        parent = f'chrome/platforms/{cplatform}'
    elif entityType == 'versions':
        svc = cv.platforms().channels().versions()
        parent = f'chrome/platforms/{cplatform}/channels/{channel}'
    else: #elif entityType == 'releases'
        svc = cv.platforms().channels().versions().releases()
        parent = f'chrome/platforms/{cplatform}/channels/{channel}/versions/{version}'
    reportTitle = f'Chrome Version History {entityType.capitalize()}'
    page_message = gapi.got_total_items_msg(reportTitle, '...\n')
    gam.printGettingAllItems(reportTitle, None)
    citems = gapi.get_all_pages(svc, 'list', entityType,
                                page_message=page_message,
                                parent=parent,
                                fields=f'nextPageToken,{entityType}',
                                **kwargs)
    for citem in citems:
        csvRows.append(utils.flatten_json(citem))
    display.write_csv_file(csvRows, CHROME_VERSIONHISTORY_TITLES[entityType], reportTitle, todrive)
