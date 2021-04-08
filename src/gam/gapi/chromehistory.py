"""Chrome Version History API calls"""

import re
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
  'platforms': ['platform'],
  'channels':  ['channel', 'platform'],
  'versions': ['version', 'platform', 'channel',
               'major_version', 'minor_version', 'build', 'patch'],
  'releases': ['version', 'fraction', 'serving.startTime',
               'serving.endTime', 'platform', 'channel',
               'major_version', 'minor_version', 'build', 'patch']
  }

def get_relative_milestone(channel='stable', minus=0):
    '''
    takes a channel and minus like stable and -1.
    returns current given milestone number
    '''
    cv = build()
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

def _get_platform_map(cv):
    '''returns dict mapping of platform choices'''
    result = gapi.get_all_pages(cv.platforms(),
                                'list',
                                'platforms',
                                parent='chrome')
    platforms = [p.get('platformType', '').lower() for p in result]
    platform_map = {'all': 'all'}
    for platform in platforms:
        key = platform.replace('_', '')
        platform_map[key] = platform
    return platform_map


def _get_channel_map(cv):
    '''returns dict mapping of channel choices'''
    result = gapi.get_all_pages(cv.platforms().channels(),
                                'list',
                                'channels',
                                parent='chrome/platforms/all')
    channels = [c.get('channelType', '').lower() for c in result]
    channels = list(set(channels))
    channel_map = {'all': 'all'}
    for channel in channels:
        key = channel.replace('_', '')
        channel_map[key] = channel
    return channel_map

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
            platform_map = _get_platform_map(cv)
            if cplatform not in platform_map:
                controlflow.expected_argument_exit('platform',
                                                   ', '.join(platform_map),
                                                   cplatform)
            cplatform = platform_map[cplatform]
            i += 2
        elif entityType in {'versions', 'releases'} and myarg == 'channel':
            channel = sys.argv[i + 1].lower().replace('_', '')
            channel_map = _get_channel_map(cv)
            if channel not in channel_map:
                controlflow.expected_argument_exit('channel',
                                                   ', '.join(channel_map),
                                                   channel)
            channel = channel_map[channel]
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
        for key in list(citem):
            if key.endswith('Type'):
                newkey = key[:-4]
                citem[newkey] = citem.pop(key)
        if 'channel' in citem:
            citem['channel'] = citem['channel'].lower()
        else:
            channel_match = re.search(r"\/channels\/([^/]*)", citem['name'])
            if channel_match:
                try:
                    citem['channel'] = channel_match.group(1)
                except IndexError:
                    pass
        if 'platform' in citem:
            citem['platform'] = citem['platform'].lower()
        else:
            platform_match = re.search(r"\/platforms\/([^/]*)", citem['name'])
            if platform_match:
                try:
                    citem['platform'] = platform_match.group(1)
                except IndexError:
                    pass

        if citem.get('version', '').count('.') == 3:
            citem['major_version'], \
            citem['minor_version'], \
            citem['build'], \
            citem['patch'] = citem['version'].split('.')
        citem.pop('name')
        csvRows.append(utils.flatten_json(citem))
    display.write_csv_file(csvRows, CHROME_VERSIONHISTORY_TITLES[entityType], reportTitle, todrive)
