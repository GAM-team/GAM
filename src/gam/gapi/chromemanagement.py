"""Chrome Management API calls"""

import sys

import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER
from gam.var import CROS_START_ARGUMENTS, CROS_END_ARGUMENTS
from gam.var import YYYYMMDD_FORMAT
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam.gapi.directory.cros import _getFilterDate


def _get_customerid():
    customer = GC_Values[GC_CUSTOMER_ID]
    if customer != MY_CUSTOMER and customer[0] != 'C':
        customer = 'C' + customer
    return f'customers/{customer}'


def _get_orgunit(orgunit):
    if orgunit.startswith('orgunits/'):
        return orgunit
    _, orgunitid = gapi_directory_orgunits.getOrgUnitId(orgunit)
    return f'{orgunitid[3:]}'


def build():
    return gam.buildGAPIObject('chromemanagement')


CHROME_APPS_ORDERBY_CHOICE_MAP = {
  'appname': 'app_name',
  'apptype': 'appType',
  'installtype': 'install_type',
  'numberofpermissions': 'number_of_permissions',
  'totalinstallcount': 'total_install_count',
  }
CHROME_APPS_TITLES = [
  'appId', 'displayName',
  'browserDeviceCount', 'osUserCount',
  'appType', 'description',
  'appInstallType', 'appSource',
  'disabled', 'homepageUri',
  'permissions'
  ]

def printApps():
    cm = build()
    customer = _get_customerid()
    todrive = False
    titles = CHROME_APPS_TITLES
    csvRows = []
    orgunit = None
    pfilter = None
    orderBy = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['ou', 'org', 'orgunit']:
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg == 'filter':
            pfilter = sys.argv[i + 1]
            i += 2
        elif myarg == 'orderby':
            orderBy = sys.argv[i + 1].lower().replace('_', '')
            if orderBy not in CHROME_APPS_ORDERBY_CHOICE_MAP:
                controlflow.expected_argument_exit('orderby',
                                                   ', '.join(CHROME_APPS_ORDERBY_CHOICE_MAP),
                                                   orderBy)
            orderBy = CHROME_APPS_ORDERBY_CHOICE_MAP[orderBy]
            i += 2
        else:
            msg = f'{myarg} is not a valid argument to "gam print chromeapps"'
            controlflow.system_error_exit(3, msg)
    if orgunit:
        orgUnitPath = gapi_directory_orgunits.orgunit_from_orgunitid(orgunit, None)
        titles.append('orgUnitPath')
    else:
        orgUnitPath = '/'
    gam.printGettingAllItems('Chrome Installed Applications', pfilter)
    page_message = gapi.got_total_items_msg('Chrome Installed Applications', '...\n')
    apps = gapi.get_all_pages(cm.customers().reports(),
                              'countInstalledApps',
                              'installedApps',
                              page_message=page_message,
                              customer=customer, orgUnitId=orgunit,
                              filter=pfilter, orderBy=orderBy)
    for app in apps:
        if orgunit:
            app['orgUnitPath'] = orgUnitPath
        if 'permissions'in app:
            app['permissions'] = ' '.join(app['permissions'])
        csvRows.append(app)
    display.write_csv_file(csvRows, titles, 'Chrome Installed Applications', todrive)


CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP = {
  'extension': 'EXTENSION',
  'app': 'APP',
  'theme': 'THEME',
  'hostedapp': 'HOSTED_APP',
  'androidapp': 'ANDROID_APP',
  }
CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP = {
  'deviceid': 'deviceId',
  'machine': 'machine',
  }
CHROME_APP_DEVICES_TITLES = [
  'appId', 'appType', 'deviceId', 'machine'
  ]

def printAppDevices():
    cm = build()
    customer = _get_customerid()
    todrive = False
    titles = CHROME_APP_DEVICES_TITLES
    csvRows = []
    orgunit = None
    appId = None
    appType = None
    startDate = None
    endDate = None
    pfilter = None
    orderBy = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['ou', 'org', 'orgunit']:
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg == 'appid':
            appId = sys.argv[i + 1]
            i += 2
        elif myarg == 'apptype':
            appType = sys.argv[i + 1].lower().replace('_', '')
            if appType not in CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP:
                controlflow.expected_argument_exit('orderby',
                                                   ', '.join(CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP),
                                                   appType)
            appType = CHROME_APP_DEVICES_APPTYPE_CHOICE_MAP[appType]
            i += 2
        elif myarg in CROS_START_ARGUMENTS:
            startDate = _getFilterDate(sys.argv[i + 1]).strftime(YYYYMMDD_FORMAT)
            i += 2
        elif myarg in CROS_END_ARGUMENTS:
            endDate = _getFilterDate(sys.argv[i + 1]).strftime(YYYYMMDD_FORMAT)
            i += 2
        elif myarg == 'orderby':
            orderBy = sys.argv[i + 1].lower().replace('_', '')
            if orderBy not in CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP:
                controlflow.expected_argument_exit('orderby',
                                                   ', '.join(CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP),
                                                   orderBy)
            orderBy = CHROME_APP_DEVICES_ORDERBY_CHOICE_MAP[orderBy]
            i += 2
        else:
            msg = f'{myarg} is not a valid argument to "gam print chromeappdevices"'
            controlflow.system_error_exit(3, msg)
    if not appId:
        controlflow.system_error_exit(3, 'You must specify an appid')
    if not appType:
        controlflow.system_error_exit(3, 'You must specify an apptype')
    if endDate:
        pfilter = f'last_active_date<={endDate}'
    if startDate:
        if pfilter:
            pfilter += ' AND '
        else:
            pfilter = ''
        pfilter += f'last_active_date>={startDate}'
    if orgunit:
        orgUnitPath = gapi_directory_orgunits.orgunit_from_orgunitid(orgunit, None)
        titles.append('orgUnitPath')
    else:
        orgUnitPath = '/'
    gam.printGettingAllItems('Chrome Installed Application Devices', pfilter)
    page_message = gapi.got_total_items_msg('Chrome Installed Application Devices', '...\n')
    devices = gapi.get_all_pages(cm.customers().reports(),
                                 'findInstalledAppDevices',
                                 'devices',
                                 page_message=page_message,
                                 appId=appId, appType=appType,
                                 customer=customer, orgUnitId=orgunit,
                                 filter=pfilter, orderBy=orderBy)
    for device in devices:
        if orgunit:
            device['orgUnitPath'] = orgUnitPath
        device['appId'] = appId
        device['appType'] = appType
        csvRows.append(device)
    display.write_csv_file(csvRows, titles, 'Chrome Installed Application Devices', todrive)


CHROME_VERSIONS_TITLES = [
    'version', 'count', 'channel', 'deviceOsVersion', 'system'
    ]
def printVersions():
    cm = build()
    customer = _get_customerid()
    todrive = False
    titles = CHROME_VERSIONS_TITLES
    csvRows = []
    orgunit = None
    startDate = None
    endDate = None
    pfilter = None
    reverse = False
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['ou', 'org', 'orgunit']:
            orgunit = _get_orgunit(sys.argv[i+1])
            i += 2
        elif myarg in CROS_START_ARGUMENTS:
            startDate = _getFilterDate(sys.argv[i + 1]).strftime(YYYYMMDD_FORMAT)
            i += 2
        elif myarg in CROS_END_ARGUMENTS:
            endDate = _getFilterDate(sys.argv[i + 1]).strftime(YYYYMMDD_FORMAT)
            i += 2
        elif myarg == 'recentfirst':
            reverse = True
            i += 1
        else:
            msg = f'{myarg} is not a valid argument to "gam print chromeversions"'
            controlflow.system_error_exit(3, msg)
    if endDate:
        pfilter = f'last_active_date<={endDate}'
    if startDate:
        if pfilter:
            pfilter += ' AND '
        else:
            pfilter = ''
        pfilter += f'last_active_date>={startDate}'
    if orgunit:
        orgUnitPath = gapi_directory_orgunits.orgunit_from_orgunitid(orgunit, None)
        titles.append('orgUnitPath')
    else:
        orgUnitPath = '/'
    gam.printGettingAllItems('Chrome Versions', pfilter)
    page_message = gapi.got_total_items_msg('Chrome Versions', '...\n')
    versions = gapi.get_all_pages(cm.customers().reports(),
                                  'countChromeVersions',
                                  'browserVersions',
                                  page_message=page_message,
                                  customer=customer, orgUnitId=orgunit, filter=pfilter)
    for version in sorted(versions, key=lambda k: k['version'], reverse=reverse):
        if orgunit:
            version['orgUnitPath'] = orgUnitPath
        csvRows.append(version)
    display.write_csv_file(csvRows, titles, 'Chrome Versions', todrive)
