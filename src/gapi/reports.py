import calendar
import datetime
import re
import sys

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import __main__
from var import *
import controlflow
import display
import gapi
import utils


def buildGAPIObject():
    return __main__.buildGAPIObject('reports')


REPORT_CHOICE_MAP = {
    'access': 'access_transparency',
    'accesstransparency': 'access_transparency',
    'calendars': 'calendar',
    'customers': 'customer',
    'doc': 'drive',
    'docs': 'drive',
    'domain': 'customer',
    'enterprisegroups': 'groups_enterprise',
    'google+': 'gplus',
    'group': 'groups',
    'groupsenterprise': 'groups_enterprise',
    'hangoutsmeet': 'meet',
    'logins': 'login',
    'oauthtoken': 'token',
    'tokens': 'token',
    'usage': 'usage',
    'usageparameters': 'usageparameters',
    'users': 'user',
    'useraccounts': 'user_accounts',
}


def showUsageParameters():
    rep = buildGAPIObject()
    throw_reasons = [gapi.errors.ErrorReason.INVALID,
                     gapi.errors.ErrorReason.BAD_REQUEST]
    todrive = False
    if len(sys.argv) == 3:
        controlflow.missing_argument_exit(
            'user or customer', 'report usageparameters')
    report = sys.argv[3].lower()
    titles = ['parameter']
    if report == 'customer':
        endpoint = rep.customerUsageReports()
        kwargs = {}
    elif report == 'user':
        endpoint = rep.userUsageReport()
        kwargs = {'userKey': __main__._getValueFromOAuth('email')}
    else:
        controlflow.expected_argument_exit(
            'usageparameters', ['user', 'customer'], report)
    customerId = GC_Values[GC_CUSTOMER_ID]
    if customerId == MY_CUSTOMER:
        customerId = None
    tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
    partial_apps = []
    all_parameters = []
    one_day = datetime.timedelta(days=1)
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], "gam report usageparameters")
    while True:
        try:
            response = gapi.call(endpoint, 'get',
                                 throw_reasons=throw_reasons,
                                 date=tryDate,
                                 customerId=customerId,
                                 **kwargs)
            partial_on_thisday = []
            for warning in response.get('warnings', []):
                for data in warning.get('data', []):
                    if data.get('key') == 'application':
                        partial_on_thisday.append(data['value'])
            if partial_apps:
                partial_apps = [app for app in partial_apps if app in partial_on_thisday]
            else:
                partial_apps = partial_on_thisday
            for parameter in response['usageReports'][0]['parameters']:
                name = parameter.get('name')
                if name and name not in all_parameters:
                    all_parameters.append(name)
            if not partial_apps:
                break
            tryDate = (utils.get_yyyymmdd(tryDate, returnDateTime=True) - \
                    one_day).strftime(YYYYMMDD_FORMAT)
        except gapi.errors.GapiInvalidError as e:
            tryDate = _adjust_date(str(e))
    all_parameters.sort()
    csvRows = []
    for parameter in all_parameters:
        csvRows.append({'parameter': parameter})
    display.write_csv_file(
        csvRows, titles, f'{report.capitalize()} Report Usage Parameters', todrive)

REPORTS_PARAMETERS_SIMPLE_TYPES = ['intValue', 'boolValue', 'datetimeValue', 'stringValue']

def showUsage():
    rep = buildGAPIObject()
    throw_reasons = [gapi.errors.ErrorReason.INVALID,
                     gapi.errors.ErrorReason.BAD_REQUEST]
    todrive = False
    if len(sys.argv) == 3:
        controlflow.missing_argument_exit(
            'user or customer', 'report usage')
    report = sys.argv[3].lower()
    titles = ['date']
    if report == 'customer':
        endpoint = rep.customerUsageReports()
        kwargs = [{}]
    elif report == 'user':
        endpoint = rep.userUsageReport()
        kwargs = [{'userKey': 'all'}]
        titles.append('user')
    else:
        controlflow.expected_argument_exit(
            'usage', ['user', 'customer'], report)
    customerId = GC_Values[GC_CUSTOMER_ID]
    if customerId == MY_CUSTOMER:
        customerId = None
    parameters = []
    start_date = end_date = orgUnitId = None
    skip_day_numbers = []
    skip_dates = []
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'startdate':
            start_date = utils.get_yyyymmdd(sys.argv[i+1], returnDateTime=True)
            i += 2
        elif myarg == 'enddate':
            end_date = utils.get_yyyymmdd(sys.argv[i+1], returnDateTime=True)
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['fields', 'parameters']:
            parameters = sys.argv[i+1].split(',')
            i += 2
        elif myarg == 'skipdates':
            skips = sys.argv[i+1].split(',')
            skip_dates = [utils.get_yyyymmdd(d) for d in skips]
            i += 2
        elif myarg == 'skipdaysofweek':
            skipdaynames = sys.argv[i+1].split(',')
            dow = [d.lower() for d in calendar.day_abbr]
            skip_day_numbers = [dow.index(d) for d in skipdaynames if d in dow]
            i += 2
        elif report == 'user' and myarg in ['orgunit', 'org', 'ou']:
            _, orgUnitId = __main__.getOrgUnitId(sys.argv[i+1])
            i += 2
        elif report == 'user' and myarg in usergroup_types:
            users = __main__.getUsersToModify(myarg, sys.argv[i+1])
            kwargs = [{'userKey': user} for user in users]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], f'gam report usage {report}')
    if parameters:
        titles.extend(parameters)
        parameters = ','.join(parameters)
    else:
        parameters = None
    if not start_date:
        start_date = datetime.datetime.now() + relativedelta(months=-1)
    if not end_date:
        end_date = datetime.datetime.now()
    if orgUnitId:
        for kw in kwargs:
            kw['orgUnitID'] = orgUnitId
    one_day = datetime.timedelta(days=1)
    usage_on_date = start_date
    start_date = usage_on_date.strftime('%Y-%m-%d')
    csvRows = []
    while usage_on_date <= end_date:
        use_date = usage_on_date.strftime('%Y-%m-%d')
        if usage_on_date.weekday() in skip_day_numbers or \
           use_date in skip_dates:
            usage_on_date += one_day
            continue
        usage_on_date += one_day
        try:
            for kwarg in kwargs:
                try:
                    usage = gapi.get_all_pages(endpoint, 'get',
                                               'usageReports',
                                               throw_reasons=throw_reasons,
                                               customerId=customerId,
                                               date=use_date,
                                               parameters=parameters,
                                               **kwarg)
                except gapi.errors.GapiBadRequestError:
                    continue
                for entity in usage:
                    row = {'date': use_date}
                    if 'userEmail' in entity['entity']:
                        row['user'] = entity['entity']['userEmail']
                    for item in entity.get('parameters', []):
                        if 'name' not in item:
                            continue
                        name = item['name']
                        if name == 'cros:device_version_distribution':
                            for cros_ver in item['msgValue']:
                                v = cros_ver['version_number']
                                column_name = f'cros:num_devices_chrome_{v}'
                                if column_name not in titles:
                                    titles.append(column_name)
                                row[column_name] = cros_ver['num_devices']
                        else:
                            if not name in titles:
                                titles.append(name)
                            for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
                                if ptype in item:
                                    row[name] = item[ptype]
                                    break
                            else:
                                row[name] = ''
                    csvRows.append(row)
        except gapi.errors.GapiInvalidError as e:
            display.print_warning(str(e))
            break
    display.write_csv_file(
        csvRows, titles, f'{report.capitalize()} Usage Report - {start_date}:{use_date}', todrive)


def showReport():
    rep = buildGAPIObject()
    throw_reasons = [gapi.errors.ErrorReason.INVALID]
    report = sys.argv[2].lower()
    report = REPORT_CHOICE_MAP.get(report.replace('_', ''), report)
    if report == 'usage':
      showUsage()
      return
    if report == 'usageparameters':
      showUsageParameters()
      return
    valid_apps = gapi.get_enum_values_minus_unspecified(
        rep._rootDesc['resources']['activities']['methods']['list'][
            'parameters']['applicationName']['enum'])+['customer', 'user']
    if report not in valid_apps:
        controlflow.expected_argument_exit(
            "report", ", ".join(sorted(valid_apps)), report)
    customerId = GC_Values[GC_CUSTOMER_ID]
    if customerId == MY_CUSTOMER:
        customerId = None
    filters = parameters = actorIpAddress = startTime = endTime = eventName = orgUnitId = None
    tryDate = datetime.date.today().strftime(YYYYMMDD_FORMAT)
    to_drive = False
    userKey = 'all'
    fullDataRequired = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'date':
            tryDate = utils.get_yyyymmdd(sys.argv[i+1])
            i += 2
        elif myarg in ['orgunit', 'org', 'ou']:
            _, orgUnitId = __main__.getOrgUnitId(sys.argv[i+1])
            i += 2
        elif myarg == 'fulldatarequired':
            fullDataRequired = []
            fdr = sys.argv[i+1].lower()
            if fdr and fdr != 'all':
                fullDataRequired = fdr.replace(',', ' ').split()
            i += 2
        elif myarg == 'start':
            startTime = utils.get_time_or_delta_from_now(sys.argv[i+1])
            i += 2
        elif myarg == 'end':
            endTime = utils.get_time_or_delta_from_now(sys.argv[i+1])
            i += 2
        elif myarg == 'event':
            eventName = sys.argv[i+1]
            i += 2
        elif myarg == 'user':
            userKey = __main__.normalizeEmailAddressOrUID(sys.argv[i+1])
            i += 2
        elif myarg in ['filter', 'filters']:
            filters = sys.argv[i+1]
            i += 2
        elif myarg in ['fields', 'parameters']:
            parameters = sys.argv[i+1]
            i += 2
        elif myarg == 'ip':
            actorIpAddress = sys.argv[i+1]
            i += 2
        elif myarg == 'todrive':
            to_drive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], "gam report")
    if report == 'user':
        while True:
            try:
                if fullDataRequired is not None:
                    warnings = gapi.get_items(rep.userUsageReport(), 'get',
                                              'warnings',
                                              throw_reasons=throw_reasons,
                                              date=tryDate, userKey=userKey,
                                              customerId=customerId,
                                              orgUnitID=orgUnitId,
                                              fields='warnings')
                    fullData, tryDate = _check_full_data_available(
                        warnings, tryDate, fullDataRequired)
                    if fullData < 0:
                        print('No user report available.')
                        sys.exit(1)
                    if fullData == 0:
                        continue
                page_message = gapi.got_total_items_msg('Users', '...\n')
                usage = gapi.get_all_pages(rep.userUsageReport(), 'get',
                                           'usageReports',
                                           page_message=page_message,
                                           throw_reasons=throw_reasons,
                                           date=tryDate, userKey=userKey,
                                           customerId=customerId,
                                           orgUnitID=orgUnitId,
                                           filters=filters,
                                           parameters=parameters)
                break
            except gapi.errors.GapiInvalidError as e:
                tryDate = _adjust_date(str(e))
        if not usage:
            print('No user report available.')
            sys.exit(1)
        titles = ['email', 'date']
        csvRows = []
        for user_report in usage:
            if 'entity' not in user_report:
                continue
            row = {'email': user_report['entity']
                            ['userEmail'], 'date': tryDate}
            for item in user_report.get('parameters', []):
                if 'name' not in item:
                    continue
                name = item['name']
                if not name in titles:
                    titles.append(name)
                for ptype in REPORTS_PARAMETERS_SIMPLE_TYPES:
                    if ptype in item:
                        row[name] = item[ptype]
                        break
                else:
                    row[name] = ''
            csvRows.append(row)
        display.write_csv_file(
            csvRows, titles, f'User Reports - {tryDate}', to_drive)
    elif report == 'customer':
        while True:
            try:
                if fullDataRequired is not None:
                    warnings = gapi.get_items(rep.customerUsageReports(),
                                              'get', 'warnings',
                                              throw_reasons=throw_reasons,
                                              customerId=customerId,
                                              date=tryDate,
                                              fields='warnings')
                    fullData, tryDate = _check_full_data_available(
                        warnings, tryDate, fullDataRequired)
                    if fullData < 0:
                        print('No customer report available.')
                        sys.exit(1)
                    if fullData == 0:
                        continue
                usage = gapi.get_all_pages(rep.customerUsageReports(), 'get',
                                           'usageReports',
                                           throw_reasons=throw_reasons,
                                           customerId=customerId,
                                           date=tryDate,
                                           parameters=parameters)
                break
            except gapi.errors.GapiInvalidError as e:
                tryDate = _adjust_date(str(e))
        if not usage:
            print('No customer report available.')
            sys.exit(1)
        titles = ['name', 'value', 'client_id']
        csvRows = []
        auth_apps = list()
        for item in usage[0]['parameters']:
            if 'name' not in item:
                continue
            name = item['name']
            if 'intValue' in item:
                value = item['intValue']
            elif 'msgValue' in item:
                if name == 'accounts:authorized_apps':
                    for subitem in item['msgValue']:
                        app = {}
                        for an_item in subitem:
                            if an_item == 'client_name':
                                app['name'] = 'App: ' + \
                                    subitem[an_item].replace('\n', '\\n')
                            elif an_item == 'num_users':
                                app['value'] = f'{subitem[an_item]} users'
                            elif an_item == 'client_id':
                                app['client_id'] = subitem[an_item]
                        auth_apps.append(app)
                    continue
                values = []
                for subitem in item['msgValue']:
                    if 'count' in subitem:
                        mycount = myvalue = None
                        for key, value in list(subitem.items()):
                            if key == 'count':
                                mycount = value
                            else:
                                myvalue = value
                            if mycount and myvalue:
                                values.append(f'{myvalue}:{mycount}')
                        value = ' '.join(values)
                    elif 'version_number' in subitem \
                         and 'num_devices' in subitem:
                        values.append(
                            f'{subitem["version_number"]}:'
                            f'{subitem["num_devices"]}')
                    else:
                        continue
                    value = ' '.join(sorted(values, reverse=True))
            csvRows.append({'name': name, 'value': value})
        for app in auth_apps:  # put apps at bottom
            csvRows.append(app)
        display.write_csv_file(
            csvRows, titles, f'Customer Report - {tryDate}', todrive=to_drive)
    else:
        page_message = gapi.got_total_items_msg('Activities', '...\n')
        activities = gapi.get_all_pages(rep.activities(), 'list', 'items',
                                        page_message=page_message,
                                        applicationName=report,
                                        userKey=userKey,
                                        customerId=customerId,
                                        actorIpAddress=actorIpAddress,
                                        startTime=startTime, endTime=endTime,
                                        eventName=eventName, filters=filters,
                                        orgUnitID=orgUnitId)
        if activities:
            titles = ['name']
            csvRows = []
            for activity in activities:
                events = activity['events']
                del activity['events']
                activity_row = utils.flatten_json(activity)
                purge_parameters = True
                for event in events:
                    for item in event.get('parameters', []):
                        if set(item) == set(['value', 'name']):
                            event[item['name']] = item['value']
                        elif set(item) == set(['intValue', 'name']):
                            if item['name'] in ['start_time', 'end_time']:
                                val = item.get('intValue')
                                if val is not None:
                                    val = int(val)
                                    if val >= 62135683200:
                                        event[item['name']] = \
                                            datetime.datetime.fromtimestamp(
                                                val-62135683200).isoformat()
                            else:
                                event[item['name']] = item['intValue']
                        elif set(item) == set(['boolValue', 'name']):
                            event[item['name']] = item['boolValue']
                        elif set(item) == set(['multiValue', 'name']):
                            event[item['name']] = ' '.join(item['multiValue'])
                        elif item['name'] == 'scope_data':
                            parts = {}
                            for message in item['multiMessageValue']:
                                for mess in message['parameter']:
                                    value = mess.get('value', ' '.join(
                                        mess.get('multiValue', [])))
                                    parts[mess['name']] = parts.get(
                                        mess['name'], [])+[value]
                            for part, v in parts.items():
                                if part == 'scope_name':
                                    part = 'scope'
                                event[part] = ' '.join(v)
                        else:
                            purge_parameters = False
                    if purge_parameters:
                        event.pop('parameters', None)
                    row = utils.flatten_json(event)
                    row.update(activity_row)
                    for item in row:
                        if item not in titles:
                            titles.append(item)
                    csvRows.append(row)
            display.sort_csv_titles(['name', ], titles)
            display.write_csv_file(
                csvRows, titles, f'{report.capitalize()} Activity Report',
                to_drive)


def _adjust_date(errMsg):
    match_date = re.match('Data for dates later than (.*) is not yet '
                          'available. Please check back later', errMsg)
    if not match_date:
        match_date = re.match('Start date can not be later than (.*)', errMsg)
    if not match_date:
        controlflow.system_error_exit(4, errMsg)
    return str(match_date.group(1))


def _check_full_data_available(warnings, tryDate, fullDataRequired):
    one_day = datetime.timedelta(days=1)
    for warning in warnings:
        if warning['code'] == 'PARTIAL_DATA_AVAILABLE':
            for app in warning['data']:
                if app['key'] == 'application' and \
                   app['value'] != 'docs' and \
                   (not fullDataRequired or app['value'] in fullDataRequired):
                    tryDateTime = datetime.datetime.strptime(
                        tryDate, YYYYMMDD_FORMAT)
                    tryDateTime -= one_day
                    return (0, tryDateTime.strftime(YYYYMMDD_FORMAT))
        elif warning['code'] == 'DATA_NOT_AVAILABLE':
            for app in warning['data']:
                if app['key'] == 'application' and \
                   app['value'] != 'docs' and \
                   (not fullDataRequired or app['value'] in fullDataRequired):
                    return (-1, tryDate)
    return (1, tryDate)
