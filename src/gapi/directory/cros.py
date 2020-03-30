import datetime

from var import *
import __main__
import controlflow
import display
import fileutils
import gapi
import gapi.directory
import utils


def doUpdateCros():
    cd = gapi.directory.buildGAPIObject()
    i, devices = getCrOSDeviceEntity(3, cd)
    update_body = {}
    action_body = {}
    orgUnitPath = None
    ack_wipe = False
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'user':
            update_body['annotatedUser'] = sys.argv[i+1]
            i += 2
        elif myarg == 'location':
            update_body['annotatedLocation'] = sys.argv[i+1]
            i += 2
        elif myarg == 'notes':
            update_body['notes'] = sys.argv[i+1].replace('\\n', '\n')
            i += 2
        elif myarg in ['tag', 'asset', 'assetid']:
            update_body['annotatedAssetId'] = sys.argv[i+1]
            i += 2
        elif myarg in ['ou', 'org']:
            orgUnitPath = __main__.getOrgUnitItem(sys.argv[i+1])
            i += 2
        elif myarg == 'action':
            action = sys.argv[i+1].lower().replace('_', '').replace('-', '')
            deprovisionReason = None
            if action in ['deprovisionsamemodelreplace',
                          'deprovisionsamemodelreplacement']:
                action = 'deprovision'
                deprovisionReason = 'same_model_replacement'
            elif action in ['deprovisiondifferentmodelreplace',
                            'deprovisiondifferentmodelreplacement']:
                action = 'deprovision'
                deprovisionReason = 'different_model_replacement'
            elif action in ['deprovisionretiringdevice']:
                action = 'deprovision'
                deprovisionReason = 'retiring_device'
            elif action not in ['disable', 'reenable']:
                controlflow.system_error_exit(2, f'expected action of ' \
                    f'deprovision_same_model_replace, ' \
                    f'deprovision_different_model_replace, ' \
                    f'deprovision_retiring_device, disable or reenable,'
                    f' got {action}')
            action_body = {'action': action}
            if deprovisionReason:
                action_body['deprovisionReason'] = deprovisionReason
            i += 2
        elif myarg == 'acknowledgedevicetouchrequirement':
            ack_wipe = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], "gam update cros")
    i = 0
    count = len(devices)
    if action_body:
        if action_body['action'] == 'deprovision' and not ack_wipe:
            print(f'WARNING: Refusing to deprovision {count} devices because '
                  'acknowledge_device_touch_requirement not specified. ' \
                  'Deprovisioning a device means the device will have to ' \
                  'be physically wiped and re-enrolled to be managed by ' \
                  'your domain again. This requires physical access to ' \
                  'the device and is very time consuming to perform for ' \
                  'each device. Please add ' \
                  '"acknowledge_device_touch_requirement" to the GAM ' \
                  'command if you understand this and wish to proceed ' \
                  'with the deprovision. Please also be aware that ' \
                  'deprovisioning can have an effect on your device ' \
                  'license count. See ' \
                  'https://support.google.com/chrome/a/answer/3523633 '\
                  'for full details.')
            sys.exit(3)
        for deviceId in devices:
            i += 1
            cur_count = __main__.currentCount(i, count)
            print(f' performing action {action} for {deviceId}{cur_count}')
            gapi.call(cd.chromeosdevices(), function='action',
                      customerId=GC_Values[GC_CUSTOMER_ID],
                      resourceId=deviceId, body=action_body)
    else:
        if update_body:
            for deviceId in devices:
                i += 1
                current_count = __main__.currentCount(i, count)
                print(f' updating {deviceId}{current_count}')
                gapi.call(cd.chromeosdevices(), 'update',
                          customerId=GC_Values[GC_CUSTOMER_ID],
                          deviceId=deviceId, body=update_body)
        if orgUnitPath:
            # split moves into max 50 devices per batch
            for l in range(0, len(devices), 50):
                move_body = {'deviceIds': devices[l:l+50]}
                print(f' moving {len(move_body["deviceIds"])} devices to ' \
                      f'{orgUnitPath}')
                gapi.call(cd.chromeosdevices(), 'moveDevicesToOu',
                          customerId=GC_Values[GC_CUSTOMER_ID],
                          orgUnitPath=orgUnitPath, body=move_body)


def doGetCrosInfo():
    cd = gapi.directory.buildGAPIObject()
    i, devices = getCrOSDeviceEntity(3, cd)
    downloadfile = None
    targetFolder = GC_Values[GC_DRIVE_DIR]
    projection = None
    fieldsList = []
    noLists = False
    startDate = endDate = None
    listLimit = 0
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg == 'nolists':
            noLists = True
            i += 1
        elif myarg == 'listlimit':
            listLimit = __main__.getInteger(sys.argv[i+1], myarg, minVal=-1)
            i += 2
        elif myarg in CROS_START_ARGUMENTS:
            startDate = _getFilterDate(sys.argv[i+1])
            i += 2
        elif myarg in CROS_END_ARGUMENTS:
            endDate = _getFilterDate(sys.argv[i+1])
            i += 2
        elif myarg == 'allfields':
            projection = 'FULL'
            fieldsList = []
            i += 1
        elif myarg in PROJECTION_CHOICES_MAP:
            projection = PROJECTION_CHOICES_MAP[myarg]
            if projection == 'FULL':
                fieldsList = []
            else:
                fieldsList = CROS_BASIC_FIELDS_LIST[:]
            i += 1
        elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
            fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[myarg])
            i += 1
        elif myarg == 'fields':
            fieldNameList = sys.argv[i+1]
            for field in fieldNameList.lower().replace(',', ' ').split():
                if field in CROS_ARGUMENT_TO_PROPERTY_MAP:
                    fieldsList.extend(CROS_ARGUMENT_TO_PROPERTY_MAP[field])
                    if field in CROS_ACTIVE_TIME_RANGES_ARGUMENTS + \
                                CROS_DEVICE_FILES_ARGUMENTS + \
                                CROS_RECENT_USERS_ARGUMENTS:
                        projection = 'FULL'
                        noLists = False
                else:
                    controlflow.invalid_argument_exit(
                        field, "gam info cros fields")
            i += 2
        elif myarg == 'downloadfile':
            downloadfile = sys.argv[i+1]
            if downloadfile.lower() == 'latest':
                downloadfile = downloadfile.lower()
            i += 2
        elif myarg == 'targetfolder':
            targetFolder = os.path.expanduser(sys.argv[i+1])
            if not os.path.isdir(targetFolder):
                os.makedirs(targetFolder)
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], "gam info cros")
    if fieldsList:
        fieldsList.append('deviceId')
        fields = ','.join(set(fieldsList)).replace('.', '/')
    else:
        fields = None
    i = 0
    device_count = len(devices)
    for deviceId in devices:
        i += 1
        cros = gapi.call(cd.chromeosdevices(), 'get',
                         customerId=GC_Values[GC_CUSTOMER_ID],
                         deviceId=deviceId, projection=projection,
                         fields=fields)
        print(f'CrOS Device: {deviceId} ({i} of {device_count})')
        if 'notes' in cros:
            cros['notes'] = cros['notes'].replace('\n', '\\n')
        if 'autoUpdateExpiration' in cros:
            cros['autoUpdateExpiration'] = utils.formatTimestampYMD(
                cros['autoUpdateExpiration'])
        _checkTPMVulnerability(cros)
        for up in CROS_SCALAR_PROPERTY_PRINT_ORDER:
            if up in cros:
                if isinstance(cros[up], str):
                    print(f'  {up}: {cros[up]}')
                else:
                    sys.stdout.write(f'  {up}:')
                    display.print_json(cros[up], '  ')
        if not noLists:
            activeTimeRanges = _filterTimeRanges(
                cros.get('activeTimeRanges', []), startDate, endDate)
            lenATR = len(activeTimeRanges)
            if lenATR:
                print('  activeTimeRanges')
                num_ranges = min(lenATR, listLimit or lenATR)
                for activeTimeRange in activeTimeRanges[:num_ranges]:
                    active_date = activeTimeRange["date"]
                    active_time = activeTimeRange["activeTime"]
                    duration = utils.formatMilliSeconds(active_time)
                    minutes = active_time // 60000
                    print(f'    date: {active_date}')
                    print(f'      activeTime: {active_time}')
                    print(f'      duration: {duration}')
                    print(f'      minutes: {minutes}')
            recentUsers = cros.get('recentUsers', [])
            lenRU = len(recentUsers)
            if lenRU:
                print('  recentUsers')
                num_ranges = min(lenRU, listLimit or lenRU)
                for recentUser in recentUsers[:num_ranges]:
                    useremail = recentUser.get("email")
                    if not useremail:
                        if recentUser["type"] == "USER_TYPE_UNMANAGED":
                            useremail = 'UnmanagedUser'
                        else:
                            useremail = 'Unknown'
                    print(f'    type: {recentUser["type"]}')
                    print(f'      email: {useremail}')
            deviceFiles = _filterCreateReportTime(
                cros.get('deviceFiles', []), 'createTime', startDate, endDate)
            lenDF = len(deviceFiles)
            if lenDF:
                num_ranges = min(lenDF, listLimit or lenDF)
                print('  deviceFiles')
                for deviceFile in deviceFiles[:num_ranges]:
                    device_type = deviceFile['type']
                    create_time = deviceFile['createTime']
                    print(f'    {device_type}: {create_time}')
            if downloadfile:
                deviceFiles = cros.get('deviceFiles', [])
                lenDF = len(deviceFiles)
                if lenDF:
                    if downloadfile == 'latest':
                        deviceFile = deviceFiles[-1]
                    else:
                        for deviceFile in deviceFiles:
                            if deviceFile['createTime'] == downloadfile:
                                break
                        else:
                            print(f'ERROR: file {downloadfile} not ' \
                                  f'available to download.')
                            deviceFile = None
                    if deviceFile:
                        created = deviceFile["createTime"]
                        downloadfile = f'cros-logs-{deviceId}-{created}.zip'
                        downloadfilename = os.path.join(targetFolder,
                                                        downloadfile)
                        dl_url = deviceFile['downloadUrl']
                        _, content = cd._http.request(dl_url)
                        fileutils.write_file(downloadfilename, content,
                                             mode='wb',
                                             continue_on_error=True)
                        print(f'Downloaded: {downloadfilename}')
                elif downloadfile:
                    print('ERROR: no files to download.')
            cpuStatusReports = _filterCreateReportTime(
                cros.get('cpuStatusReports', []),
                'reportTime',
                startDate,
                endDate)
            lenCSR = len(cpuStatusReports)
            if lenCSR:
                print('  cpuStatusReports')
                num_ranges = min(lenCSR, listLimit or lenCSR)
                for cpuStatusReport in cpuStatusReports[:num_ranges]:
                    print(f'    reportTime: {cpuStatusReport["reportTime"]}')
                    print('      cpuTemperatureInfo')
                    tempInfos = cpuStatusReport.get('cpuTemperatureInfo', [])
                    for tempInfo in tempInfos:
                        temp_label = tempInfo['label'].strip()
                        temperature = tempInfo['temperature']
                        print(f'        {temp_label}: {temperature}')
                    pct_info = cpuStatusReport["cpuUtilizationPercentageInfo"]
                    util = ",".join([str(x) for x in pct_info])
                    print(f'      cpuUtilizationPercentageInfo: {util}')
            diskVolumeReports = cros.get('diskVolumeReports', [])
            lenDVR = len(diskVolumeReports)
            if lenDVR:
                print('  diskVolumeReports')
                print('    volumeInfo')
                num_ranges = min(lenDVR, listLimit or lenDVR)
                for diskVolumeReport in diskVolumeReports[:num_ranges]:
                    volumeInfo = diskVolumeReport['volumeInfo']
                    for volume in volumeInfo:
                        vid = volume['volumeId']
                        vstorage_free = volume['storageFree']
                        vstorage_total = volume['storageTotal']
                        print(f'      volumeId: {vid}')
                        print(f'        storageFree: {vstorage_free}')
                        print(f'        storageTotal: {vstorage_total}')
            systemRamFreeReports = _filterCreateReportTime(
                cros.get('systemRamFreeReports', []),
                'reportTime', startDate, endDate)
            lenSRFR = len(systemRamFreeReports)
            if lenSRFR:
                print('  systemRamFreeReports')
                num_ranges = min(lenSRFR, listLimit or lenSRFR)
                for systemRamFreeReport in systemRamFreeReports[:num_ranges]:
                    report_time = systemRamFreeReport["reportTime"]
                    free_info = systemRamFreeReport["systemRamFreeInfo"]
                    free_ram = ",".join(free_info)
                    print(f'    reportTime: {report_time}')
                    print(f'      systemRamFreeInfo: {free_ram}')


def doPrintCrosActivity():
    cd = gapi.directory.buildGAPIObject()
    todrive = False
    titles = ['deviceId', 'annotatedAssetId',
              'annotatedLocation', 'serialNumber', 'orgUnitPath']
    csvRows = []
    fieldsList = ['deviceId', 'annotatedAssetId',
                  'annotatedLocation', 'serialNumber', 'orgUnitPath']
    startDate = endDate = None
    selectActiveTimeRanges = selectDeviceFiles = selectRecentUsers = False
    listLimit = 0
    delimiter = ','
    orgUnitPath = None
    queries = [None]
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['query', 'queries']:
            queries = __main__.getQueries(myarg, sys.argv[i+1])
            i += 2
        elif myarg == 'limittoou':
            orgUnitPath = __main__.getOrgUnitItem(sys.argv[i+1])
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in CROS_ACTIVE_TIME_RANGES_ARGUMENTS:
            selectActiveTimeRanges = True
            i += 1
        elif myarg in CROS_DEVICE_FILES_ARGUMENTS:
            selectDeviceFiles = True
            i += 1
        elif myarg in CROS_RECENT_USERS_ARGUMENTS:
            selectRecentUsers = True
            i += 1
        elif myarg == 'both':
            selectActiveTimeRanges = selectRecentUsers = True
            i += 1
        elif myarg == 'all':
            selectActiveTimeRanges = selectDeviceFiles = True
            selectRecentUsers = True
            i += 1
        elif myarg in CROS_START_ARGUMENTS:
            startDate = _getFilterDate(sys.argv[i+1])
            i += 2
        elif myarg in CROS_END_ARGUMENTS:
            endDate = _getFilterDate(sys.argv[i+1])
            i += 2
        elif myarg == 'listlimit':
            listLimit = __main__.getInteger(sys.argv[i+1], myarg, minVal=0)
            i += 2
        elif myarg == 'delimiter':
            delimiter = sys.argv[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], "gam print crosactivity")
    if not selectActiveTimeRanges and \
       not selectDeviceFiles and \
       not selectRecentUsers:
        selectActiveTimeRanges = selectRecentUsers = True
    if selectRecentUsers:
        fieldsList.append('recentUsers')
        display.add_titles_to_csv_file(['recentUsers.email', ], titles)
    if selectActiveTimeRanges:
        fieldsList.append('activeTimeRanges')
        titles_to_add = ['activeTimeRanges.date',
                         'activeTimeRanges.duration',
                         'activeTimeRanges.minutes']
        display.add_titles_to_csv_file(titles_to_add, titles)
    if selectDeviceFiles:
        fieldsList.append('deviceFiles')
        titles_to_add = ['deviceFiles.type', 'deviceFiles.createTime']
        display.add_titles_to_csv_file(titles_to_add, titles)
    fields = f'nextPageToken,chromeosdevices({",".join(fieldsList)})'
    for query in queries:
        __main__.printGettingAllItems('CrOS Devices', query)
        page_message = gapi.got_total_items_msg('CrOS Devices', '...\n')
        all_cros = gapi.get_all_pages(cd.chromeosdevices(), 'list',
                                      'chromeosdevices',
                                      page_message=page_message,
                                      query=query,
                                      customerId=GC_Values[GC_CUSTOMER_ID],
                                      projection='FULL',
                                      fields=fields, orgUnitPath=orgUnitPath)
        for cros in all_cros:
            row = {}
            skip_attribs = ['recentUsers', 'activeTimeRanges', 'deviceFiles']
            for attrib in cros:
                if attrib not in skip_attribs:
                    row[attrib] = cros[attrib]
            if selectActiveTimeRanges:
                activeTimeRanges = _filterTimeRanges(
                    cros.get('activeTimeRanges', []), startDate, endDate)
                lenATR = len(activeTimeRanges)
                num_ranges = min(lenATR, listLimit or lenATR)
                for activeTimeRange in activeTimeRanges[:num_ranges]:
                    newrow = row.copy()
                    newrow['activeTimeRanges.date'] = activeTimeRange['date']
                    active_time = activeTimeRange['activeTime']
                    newrow['activeTimeRanges.duration'] = \
                        utils.formatMilliSeconds(active_time)
                    newrow['activeTimeRanges.minutes'] = \
                        activeTimeRange['activeTime']//60000
                    csvRows.append(newrow)
            if selectRecentUsers:
                recentUsers = cros.get('recentUsers', [])
                lenRU = len(recentUsers)
                num_ranges = min(lenRU, listLimit or lenRU)
                recent_users = []
                for recentUser in recentUsers[:num_ranges]:
                    useremail = recentUser.get("email")
                    if not useremail:
                        if recentUser["type"] == "USER_TYPE_UNMANAGED":
                            useremail = 'UnmanagedUser'
                        else:
                            useremail = 'Unknown'
                    recent_users.append(useremail)
                row['recentUsers.email'] = delimiter.join(recent_users)
                csvRows.append(row)
            if selectDeviceFiles:
                deviceFiles = _filterCreateReportTime(
                    cros.get('deviceFiles', []),
                    'createTime', startDate, endDate)
                lenDF = len(deviceFiles)
                num_ranges = min(lenDF, listLimit or lenDF)
                for deviceFile in deviceFiles[:num_ranges]:
                    newrow = row.copy()
                    newrow['deviceFiles.type'] = deviceFile['type']
                    create_time = deviceFile['createTime']
                    newrow['deviceFiles.createTime'] = create_time
                    csvRows.append(newrow)
    display.write_csv_file(csvRows, titles, 'CrOS Activity', todrive)


def _checkTPMVulnerability(cros):
    if 'tpmVersionInfo' in cros and \
       'firmwareVersion' in cros['tpmVersionInfo']:
        firmware_version = cros['tpmVersionInfo']['firmwareVersion']
        if firmware_version in CROS_TPM_VULN_VERSIONS:
            cros['tpmVersionInfo']['tpmVulnerability'] = 'VULNERABLE'
        elif firmware_version in CROS_TPM_FIXED_VERSIONS:
            cros['tpmVersionInfo']['tpmVulnerability'] = 'UPDATED'
        else:
            cros['tpmVersionInfo']['tpmVulnerability'] = 'NOT IMPACTED'


def doPrintCrosDevices():
    def _getSelectedLists(myarg):
        if myarg in CROS_ACTIVE_TIME_RANGES_ARGUMENTS:
            selectedLists['activeTimeRanges'] = True
        elif myarg in CROS_RECENT_USERS_ARGUMENTS:
            selectedLists['recentUsers'] = True
        elif myarg in CROS_DEVICE_FILES_ARGUMENTS:
            selectedLists['deviceFiles'] = True
        elif myarg in CROS_CPU_STATUS_REPORTS_ARGUMENTS:
            selectedLists['cpuStatusReports'] = True
        elif myarg in CROS_DISK_VOLUME_REPORTS_ARGUMENTS:
            selectedLists['diskVolumeReports'] = True
        elif myarg in CROS_SYSTEM_RAM_FREE_REPORTS_ARGUMENTS:
            selectedLists['systemRamFreeReports'] = True

    cd = gapi.directory.buildGAPIObject()
    todrive = False
    fieldsList = []
    fieldsTitles = {}
    titles = []
    csvRows = []
    display.add_field_to_csv_file(
        'deviceid', CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList, fieldsTitles, titles)
    projection = orderBy = sortOrder = orgUnitPath = None
    queries = [None]
    noLists = sortHeaders = False
    selectedLists = {}
    startDate = endDate = None
    listLimit = 0
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower().replace('_', '')
        if myarg in ['query', 'queries']:
            queries = __main__.getQueries(myarg, sys.argv[i+1])
            i += 2
        elif myarg == 'limittoou':
            orgUnitPath = __main__.getOrgUnitItem(sys.argv[i+1])
            i += 2
        elif myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'nolists':
            noLists = True
            selectedLists = {}
            i += 1
        elif myarg == 'listlimit':
            listLimit = __main__.getInteger(sys.argv[i+1], myarg, minVal=0)
            i += 2
        elif myarg in CROS_START_ARGUMENTS:
            startDate = _getFilterDate(sys.argv[i+1])
            i += 2
        elif myarg in CROS_END_ARGUMENTS:
            endDate = _getFilterDate(sys.argv[i+1])
            i += 2
        elif myarg == 'orderby':
            orderBy = sys.argv[i+1].lower().replace('_', '')
            validOrderBy = ['location', 'user', 'lastsync',
                            'notes', 'serialnumber', 'status', 'supportenddate']
            if orderBy not in validOrderBy:
                controlflow.expected_argument_exit(
                    "orderby", ", ".join(validOrderBy), orderBy)
            if orderBy == 'location':
                orderBy = 'annotatedLocation'
            elif orderBy == 'user':
                orderBy = 'annotatedUser'
            elif orderBy == 'lastsync':
                orderBy = 'lastSync'
            elif orderBy == 'serialnumber':
                orderBy = 'serialNumber'
            elif orderBy == 'supportenddate':
                orderBy = 'supportEndDate'
            i += 2
        elif myarg in SORTORDER_CHOICES_MAP:
            sortOrder = SORTORDER_CHOICES_MAP[myarg]
            i += 1
        elif myarg in PROJECTION_CHOICES_MAP:
            projection = PROJECTION_CHOICES_MAP[myarg]
            sortHeaders = True
            if projection == 'FULL':
                fieldsList = []
            else:
                fieldsList = CROS_BASIC_FIELDS_LIST[:]
            i += 1
        elif myarg == 'allfields':
            projection = 'FULL'
            sortHeaders = True
            fieldsList = []
            i += 1
        elif myarg == 'sortheaders':
            sortHeaders = True
            i += 1
        elif myarg in CROS_LISTS_ARGUMENTS:
            _getSelectedLists(myarg)
            i += 1
        elif myarg in CROS_ARGUMENT_TO_PROPERTY_MAP:
            display.add_field_to_fields_list(
                myarg, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList)
            i += 1
        elif myarg == 'fields':
            fieldNameList = sys.argv[i+1]
            for field in fieldNameList.lower().replace(',', ' ').split():
                if field in CROS_LISTS_ARGUMENTS:
                    _getSelectedLists(field)
                elif field in CROS_ARGUMENT_TO_PROPERTY_MAP:
                    display.add_field_to_fields_list(
                        field, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList)
                else:
                    controlflow.invalid_argument_exit(
                        field, "gam print cros fields")
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], "gam print cros")
    if selectedLists:
        noLists = False
        projection = 'FULL'
        for selectList in selectedLists:
            display.add_field_to_fields_list(
                selectList, CROS_ARGUMENT_TO_PROPERTY_MAP, fieldsList)
    if fieldsList:
        fieldsList.append('deviceId')
        fields = f'nextPageToken,chromeosdevices({",".join(set(fieldsList))})'.replace(
            '.', '/')
    else:
        fields = None
    for query in queries:
        __main__.printGettingAllItems('CrOS Devices', query)
        page_message = gapi.got_total_items_msg('CrOS Devices', '...\n')
        all_cros = gapi.get_all_pages(cd.chromeosdevices(), 'list',
                                      'chromeosdevices',
                                      page_message=page_message, query=query,
                                      customerId=GC_Values[GC_CUSTOMER_ID],
                                      projection=projection,
                                      orgUnitPath=orgUnitPath,
                                      orderBy=orderBy, sortOrder=sortOrder,
                                      fields=fields)
        for cros in all_cros:
            _checkTPMVulnerability(cros)
        if not noLists and not selectedLists:
            for cros in all_cros:
                if 'notes' in cros:
                    cros['notes'] = cros['notes'].replace('\n', '\\n')
                if 'autoUpdateExpiration' in cros:
                    cros['autoUpdateExpiration'] = utils.formatTimestampYMD(
                        cros['autoUpdateExpiration'])
                for cpuStatusReport in cros.get('cpuStatusReports', []):
                    tempInfos = cpuStatusReport.get('cpuTemperatureInfo', [])
                    for tempInfo in tempInfos:
                        tempInfo['label'] = tempInfo['label'].strip()
                display.add_row_titles_to_csv_file(utils.flatten_json(
                    cros, listLimit=listLimit), csvRows, titles)
            continue
        for cros in all_cros:
            if 'notes' in cros:
                cros['notes'] = cros['notes'].replace('\n', '\\n')
            if 'autoUpdateExpiration' in cros:
                cros['autoUpdateExpiration'] = utils.formatTimestampYMD(
                    cros['autoUpdateExpiration'])
            row = {}
            for attrib in cros:
                if attrib not in set(['kind', 'etag', 'tpmVersionInfo',
                                      'recentUsers', 'activeTimeRanges',
                                      'deviceFiles', 'cpuStatusReports',
                                      'diskVolumeReports',
                                      'systemRamFreeReports']):
                    row[attrib] = cros[attrib]
            if selectedLists.get('activeTimeRanges'):
                timergs = cros.get('activeTimeRanges', [])
            else:
                timergs = []
            activeTimeRanges = _filterTimeRanges(timergs, startDate, endDate)
            if selectedLists.get('recentUsers'):
                recentUsers = cros.get('recentUsers', [])
            else:
                recentUsers = []
            if selectedLists.get('deviceFiles'):
                device_files = cros.get('deviceFiles', [])
            else:
                device_files = []
            deviceFiles = _filterCreateReportTime(device_files, 'createTime',
                                                  startDate, endDate)
            if selectedLists.get('cpuStatusReports'):
                cpu_reports = cros.get('cpuStatusReports', [])
            else:
                cpu_reports = []
            cpuStatusReports = _filterCreateReportTime(cpu_reports,
                                                       'reportTime',
                                                       startDate, endDate)
            if selectedLists.get('diskVolumeReports'):
                diskVolumeReports = cros.get('diskVolumeReports', [])
            else:
                diskVolumeReports = []
            if selectedLists.get('systemRamFreeReports'):
                ram_reports = cros.get('systemRamFreeReports', [])
            else:
                ram_reports = []
            systemRamFreeReports = _filterCreateReportTime(ram_reports,
                                                           'reportTime',
                                                           startDate,
                                                           endDate)
            if noLists or (not activeTimeRanges and \
                           not recentUsers and \
                           not deviceFiles and \
                           not cpuStatusReports and \
                           not diskVolumeReports and \
                           not systemRamFreeReports):
                display.add_row_titles_to_csv_file(row, csvRows, titles)
                continue
            lenATR = len(activeTimeRanges)
            lenRU = len(recentUsers)
            lenDF = len(deviceFiles)
            lenCSR = len(cpuStatusReports)
            lenDVR = len(diskVolumeReports)
            lenSRFR = len(systemRamFreeReports)
            max_len = max(lenATR, lenRU, lenDF, lenCSR, lenDVR, lenSRFR)
            for i in range(min(max_len, listLimit or max_len)):
                nrow = row.copy()
                if i < lenATR:
                    nrow['activeTimeRanges.date'] = \
                        activeTimeRanges[i]['date']
                    nrow['activeTimeRanges.activeTime'] = \
                        str(activeTimeRanges[i]['activeTime'])
                    active_time = activeTimeRanges[i]['activeTime']
                    nrow['activeTimeRanges.duration'] = \
                        utils.formatMilliSeconds(active_time)
                    nrow['activeTimeRanges.minutes'] = active_time // 60000
                if i < lenRU:
                    nrow['recentUsers.type'] = recentUsers[i]['type']
                    nrow['recentUsers.email'] = recentUsers[i].get('email')
                    if not nrow['recentUsers.email']:
                        if nrow['recentUsers.type'] == 'USER_TYPE_UNMANAGED':
                            nrow['recentUsers.email'] = 'UnmanagedUser'
                        else:
                            nrow['recentUsers.email'] = 'Unknown'
                if i < lenDF:
                    nrow['deviceFiles.type'] = deviceFiles[i]['type']
                    nrow['deviceFiles.createTime'] = \
                        deviceFiles[i]['createTime']
                if i < lenCSR:
                    nrow['cpuStatusReports.reportTime'] = \
                        cpuStatusReports[i]['reportTime']
                    tempInfos = cpuStatusReports[i].get('cpuTemperatureInfo',
                                                        [])
                    for tempInfo in tempInfos:
                        label = tempInfo["label"].strip()
                        base = 'cpuStatusReports.cpuTemperatureInfo.'
                        nrow[f'{base}{label}'] = tempInfo['temperature']
                    cpu_field = 'cpuUtilizationPercentageInfo'
                    cpu_reports = cpuStatusReports[i][cpu_field]
                    cpu_pcts = [str(x) for x in cpu_reports]
                    nrow[f'cpuStatusReports.{cpu_field}'] = ','.join(cpu_pcts)
                if i < lenDVR:
                    volumeInfo = diskVolumeReports[i]['volumeInfo']
                    j = 0
                    vfield = 'diskVolumeReports.volumeInfo.'
                    for volume in volumeInfo:
                        nrow[f'{vfield}{j}.volumeId'] = \
                            volume['volumeId']
                        nrow[f'{vfield}{j}.storageFree'] = \
                            volume['storageFree']
                        nrow[f'{vfield}{j}.storageTotal'] = \
                            volume['storageTotal']
                        j += 1
                if i < lenSRFR:
                    nrow['systemRamFreeReports.reportTime'] = \
                        systemRamFreeReports[i]['reportTime']
                    ram_reports = systemRamFreeReports[i]['systemRamFreeInfo']
                    ram_info = [str(x) for x in ram_reports]
                    nrow['systenRamFreeReports.systemRamFreeInfo'] = \
                        ','.join(ram_info)
                display.add_row_titles_to_csv_file(nrow, csvRows, titles)
    if sortHeaders:
        display.sort_csv_titles(['deviceId', ], titles)
    display.write_csv_file(csvRows, titles, 'CrOS', todrive)


def getCrOSDeviceEntity(i, cd):
    myarg = sys.argv[i].lower()
    if myarg == 'cros_sn':
        return i+2, __main__.getUsersToModify('cros_sn', sys.argv[i+1])
    if myarg == 'query':
        return i+2, __main__.getUsersToModify('crosquery', sys.argv[i+1])
    if myarg[:6] == 'query:':
        query = sys.argv[i][6:]
        if query[:12].lower() == 'orgunitpath:':
            kwargs = {'orgUnitPath': query[12:]}
        else:
            kwargs = {'query': query}
        fields = 'nextPageToken,chromeosdevices(deviceId)'
        devices = gapi.get_all_pages(cd.chromeosdevices(), 'list',
                                     'chromeosdevices',
                                     customerId=GC_Values[GC_CUSTOMER_ID],
                                     fields=fields, **kwargs)
        return i+1, [device['deviceId'] for device in devices]
    return i+1, sys.argv[i].replace(',', ' ').split()


def _getFilterDate(dateStr):
    return datetime.datetime.strptime(dateStr, YYYYMMDD_FORMAT)


def _filterTimeRanges(activeTimeRanges, startDate, endDate):
    if startDate is None and endDate is None:
        return activeTimeRanges
    filteredTimeRanges = []
    for timeRange in activeTimeRanges:
        activityDate = datetime.datetime.strptime(
            timeRange['date'], YYYYMMDD_FORMAT)
        if ((startDate is None) or \
            (activityDate >= startDate)) and \
           ((endDate is None) or \
            (activityDate <= endDate)):
            filteredTimeRanges.append(timeRange)
    return filteredTimeRanges


def _filterCreateReportTime(items, timeField, startTime, endTime):
    if startTime is None and endTime is None:
        return items
    filteredItems = []
    time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    for item in items:
        timeValue = datetime.datetime.strptime(item[timeField], time_format)
        if ((startTime is None) or \
            (timeValue >= startTime)) and \
           ((endTime is None) or \
            (timeValue <= endTime)):
            filteredItems.append(item)
    return filteredItems
