import sys
import uuid

import __main__
from var import *
import controlflow
import display
import gapi.directory
import utils


def printBuildings():
    to_drive = False
    cd = gapi.directory.buildGAPIObject()
    titles = []
    csvRows = []
    fieldsList = ['buildingId']
    # buildings.list() currently doesn't support paging
    # but should soon, attempt to use it now so we
    # won't break when it's turned on.
    fields = 'nextPageToken,buildings(%s)'
    possible_fields = {}
    for pfield in cd._rootDesc['schemas']['Building']['properties']:
        possible_fields[pfield.lower()] = pfield
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            to_drive = True
            i += 1
        elif myarg == 'allfields':
            fields = None
            i += 1
        elif myarg in possible_fields:
            fieldsList.append(possible_fields[myarg])
            i += 1
        # Allows shorter arguments like "name" instead of "buildingname"
        elif 'building'+myarg in possible_fields:
            fieldsList.append(possible_fields['building'+myarg])
            i += 1
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], "gam print buildings")
    if fields:
        fields = fields % ','.join(fieldsList)
    buildings = gapi.get_all_pages(cd.resources().buildings(), 'list',
                                   'buildings',
                                   customer=GC_Values[GC_CUSTOMER_ID],
                                   fields=fields)
    for building in buildings:
        building.pop('etags', None)
        building.pop('etag', None)
        building.pop('kind', None)
        if 'buildingId' in building:
            building['buildingId'] = f'id:{building["buildingId"]}'
        if 'floorNames' in building:
            building['floorNames'] = ','.join(building['floorNames'])
        building = utils.flatten_json(building)
        for item in building:
            if item not in titles:
                titles.append(item)
        csvRows.append(building)
    display.sort_csv_titles('buildingId', titles)
    display.write_csv_file(csvRows, titles, 'Buildings', to_drive)


def printResourceCalendars():
    cd = gapi.directory.buildGAPIObject()
    todrive = False
    fieldsList = []
    fieldsTitles = {}
    titles = []
    csvRows = []
    query = None
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg == 'query':
            query = sys.argv[i+1]
            i += 2
        elif myarg == 'allfields':
            fieldsList = []
            fieldsTitles = {}
            titles = []
            for field in RESCAL_ALLFIELDS:
                display.add_field_to_csv_file(field,
                                              RESCAL_ARGUMENT_TO_PROPERTY_MAP,
                                              fieldsList, fieldsTitles,
                                              titles)
            i += 1
        elif myarg in RESCAL_ARGUMENT_TO_PROPERTY_MAP:
            display.add_field_to_csv_file(myarg,
                                          RESCAL_ARGUMENT_TO_PROPERTY_MAP,
                                          fieldsList, fieldsTitles, titles)
            i += 1
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], "gam print resources")
    if not fieldsList:
        for field in RESCAL_DFLTFIELDS:
            display.add_field_to_csv_file(field,
                                          RESCAL_ARGUMENT_TO_PROPERTY_MAP,
                                          fieldsList, fieldsTitles, titles)
    fields = f'nextPageToken,items({",".join(set(fieldsList))})'
    if 'buildingId' in fieldsList:
        display.add_field_to_csv_file('buildingName', {'buildingName': [
            'buildingName', ]}, fieldsList, fieldsTitles, titles)
    __main__.printGettingAllItems('Resource Calendars', None)
    page_message = gapi.got_total_items_first_last_msg('Resource Calendars')
    resources = gapi.get_all_pages(cd.resources().calendars(), 'list',
                                   'items', page_message=page_message,
                                   message_attribute='resourceId',
                                   customer=GC_Values[GC_CUSTOMER_ID],
                                   query=query, fields=fields)
    for resource in resources:
        if 'featureInstances' in resource:
            features = [a_feature['feature']['name'] for \
                a_feature in resource['featureInstances']]
            resource['featureInstances'] = ','.join(features)
        if 'buildingId' in resource:
            resource['buildingName'] = getBuildingNameById(
                cd, resource['buildingId'])
            resource['buildingId'] = f'id:{resource["buildingId"]}'
        resUnit = {}
        for field in fieldsList:
            resUnit[fieldsTitles[field]] = resource.get(field, '')
        csvRows.append(resUnit)
    display.sort_csv_titles(
        ['resourceId', 'resourceName', 'resourceEmail'], titles)
    display.write_csv_file(csvRows, titles, 'Resources', todrive)


RESCAL_DFLTFIELDS = ['id', 'name', 'email',]
RESCAL_ALLFIELDS = ['id', 'name', 'email', 'description', 'type',
                    'buildingid', 'category', 'capacity', 'features', 'floor',
                    'floorsection', 'generatedresourcename',
                    'uservisibledescription',]

RESCAL_ARGUMENT_TO_PROPERTY_MAP = {
    'description': ['resourceDescription'],
    'building': ['buildingId', ],
    'buildingid': ['buildingId', ],
    'capacity': ['capacity', ],
    'category': ['resourceCategory', ],
    'email': ['resourceEmail'],
    'feature': ['featureInstances', ],
    'features': ['featureInstances', ],
    'floor': ['floorName', ],
    'floorname': ['floorName', ],
    'floorsection': ['floorSection', ],
    'generatedresourcename': ['generatedResourceName', ],
    'id': ['resourceId'],
    'name': ['resourceName'],
    'type': ['resourceType'],
    'userdescription': ['userVisibleDescription', ],
    'uservisibledescription': ['userVisibleDescription', ],
}


def printFeatures():
    to_drive = False
    cd = gapi.directory.buildGAPIObject()
    titles = []
    csvRows = []
    fieldsList = ['name']
    fields = 'nextPageToken,features(%s)'
    possible_fields = {}
    for pfield in cd._rootDesc['schemas']['Feature']['properties']:
        possible_fields[pfield.lower()] = pfield
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            to_drive = True
            i += 1
        elif myarg == 'allfields':
            fields = None
            i += 1
        elif myarg in possible_fields:
            fieldsList.append(possible_fields[myarg])
            i += 1
        elif 'feature'+myarg in possible_fields:
            fieldsList.append(possible_fields['feature'+myarg])
            i += 1
        else:
            controlflow.invalid_argument_exit(
                sys.argv[i], "gam print features")
    if fields:
        fields = fields % ','.join(fieldsList)
    features = gapi.get_all_pages(cd.resources().features(), 'list',
                                  'features',
                                  customer=GC_Values[GC_CUSTOMER_ID],
                                  fields=fields)
    for feature in features:
        feature.pop('etags', None)
        feature.pop('etag', None)
        feature.pop('kind', None)
        feature = utils.flatten_json(feature)
        for item in feature:
            if item not in titles:
                titles.append(item)
        csvRows.append(feature)
    display.sort_csv_titles('name', titles)
    display.write_csv_file(csvRows, titles, 'Features', to_drive)


def _getBuildingAttributes(args, body={}):
    i = 0
    while i < len(args):
        myarg = args[i].lower().replace('_', '')
        if myarg == 'id':
            body['buildingId'] = args[i+1]
            i += 2
        elif myarg == 'name':
            body['buildingName'] = args[i+1]
            i += 2
        elif myarg in ['lat', 'latitude']:
            if 'coordinates' not in body:
                body['coordinates'] = {}
            body['coordinates']['latitude'] = args[i+1]
            i += 2
        elif myarg in ['long', 'lng', 'longitude']:
            if 'coordinates' not in body:
                body['coordinates'] = {}
            body['coordinates']['longitude'] = args[i+1]
            i += 2
        elif myarg == 'description':
            body['description'] = args[i+1]
            i += 2
        elif myarg == 'floors':
            body['floorNames'] = args[i+1].split(',')
            i += 2
        else:
            controlflow.invalid_argument_exit(
                myarg, "gam create|update building")
    return body


def createBuilding():
    cd = gapi.directory.buildGAPIObject()
    body = {'floorNames': ['1'],
            'buildingId': str(uuid.uuid4()),
            'buildingName': sys.argv[3]}
    body = _getBuildingAttributes(sys.argv[4:], body)
    print(f'Creating building {body["buildingId"]}...')
    gapi.call(cd.resources().buildings(), 'insert',
              customer=GC_Values[GC_CUSTOMER_ID], body=body)


def _makeBuildingIdNameMap(cd):
    fields = 'nextPageToken,buildings(buildingId,buildingName)'
    buildings = gapi.get_all_pages(cd.resources().buildings(), 'list',
                                   'buildings',
                                   customer=GC_Values[GC_CUSTOMER_ID],
                                   fields=fields)
    GM_Globals[GM_MAP_BUILDING_ID_TO_NAME] = {}
    GM_Globals[GM_MAP_BUILDING_NAME_TO_ID] = {}
    for building in buildings:
        GM_Globals[GM_MAP_BUILDING_ID_TO_NAME][building['buildingId']
                                               ] = building['buildingName']
        GM_Globals[GM_MAP_BUILDING_NAME_TO_ID][building['buildingName']
                                               ] = building['buildingId']


def getBuildingByNameOrId(cd, which_building, minLen=1):
    if not which_building or \
       (minLen == 0 and which_building in ['id:', 'uid:']):
        if minLen == 0:
            return ''
        controlflow.system_error_exit(3, 'Building id/name is empty')
    cg = UID_PATTERN.match(which_building)
    if cg:
        return cg.group(1)
    if GM_Globals[GM_MAP_BUILDING_NAME_TO_ID] is None:
        _makeBuildingIdNameMap(cd)
    # Exact name match, return ID
    if which_building in GM_Globals[GM_MAP_BUILDING_NAME_TO_ID]:
        return GM_Globals[GM_MAP_BUILDING_NAME_TO_ID][which_building]
    # No exact name match, check for case insensitive name matches
    which_building_lower = which_building.lower()
    ci_matches = []
    for buildingName, buildingId in GM_Globals[GM_MAP_BUILDING_NAME_TO_ID].items():
        if buildingName.lower() == which_building_lower:
            ci_matches.append(
                {'buildingName': buildingName, 'buildingId': buildingId})
    # One match, return ID
    if len(ci_matches) == 1:
        return ci_matches[0]['buildingId']
    # No or multiple name matches, try ID
    # Exact ID match, return ID
    if which_building in GM_Globals[GM_MAP_BUILDING_ID_TO_NAME]:
        return which_building
    # No exact ID match, check for case insensitive id match
    for buildingId in GM_Globals[GM_MAP_BUILDING_ID_TO_NAME]:
        # Match, return ID
        if buildingId.lower() == which_building_lower:
            return buildingId
    # Multiple name  matches
    if len(ci_matches) > 1:
        message = 'Multiple buildings with same name:\n'
        for building in ci_matches:
            message += f'  Name:{building["buildingName"]}  ' \
                       f'id:{building["buildingId"]}\n'
        message += '\nPlease specify building name by exact case or by id.'
        controlflow.system_error_exit(3, message)
    # No matches
    else:
        controlflow.system_error_exit(3, f'No such building {which_building}')


def getBuildingNameById(cd, buildingId):
    if GM_Globals[GM_MAP_BUILDING_ID_TO_NAME] is None:
        _makeBuildingIdNameMap(cd)
    return GM_Globals[GM_MAP_BUILDING_ID_TO_NAME].get(buildingId, 'UNKNOWN')


def updateBuilding():
    cd = gapi.directory.buildGAPIObject()
    buildingId = getBuildingByNameOrId(cd, sys.argv[3])
    body = _getBuildingAttributes(sys.argv[4:])
    print(f'Updating building {buildingId}...')
    gapi.call(cd.resources().buildings(), 'patch',
              customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId,
              body=body)


def getBuildingInfo():
    cd = gapi.directory.buildGAPIObject()
    buildingId = getBuildingByNameOrId(cd, sys.argv[3])
    building = gapi.call(cd.resources().buildings(), 'get',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         buildingId=buildingId)
    if 'buildingId' in building:
        building['buildingId'] = f'id:{building["buildingId"]}'
    if 'floorNames' in building:
        building['floorNames'] = ','.join(building['floorNames'])
    if 'buildingName' in building:
        sys.stdout.write(building.pop('buildingName'))
    display.print_json(building)


def deleteBuilding():
    cd = gapi.directory.buildGAPIObject()
    buildingId = getBuildingByNameOrId(cd, sys.argv[3])
    print(f'Deleting building {buildingId}...')
    gapi.call(cd.resources().buildings(), 'delete',
              customer=GC_Values[GC_CUSTOMER_ID], buildingId=buildingId)


def _getFeatureAttributes(args, body={}):
    i = 0
    while i < len(args):
        myarg = args[i].lower().replace('_', '')
        if myarg == 'name':
            body['name'] = args[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(
                myarg, "gam create|update feature")
    return body


def createFeature():
    cd = gapi.directory.buildGAPIObject()
    body = _getFeatureAttributes(sys.argv[3:])
    print(f'Creating feature {body["name"]}...')
    gapi.call(cd.resources().features(), 'insert',
              customer=GC_Values[GC_CUSTOMER_ID], body=body)


def updateFeature():
    # update does not work for name and name is only field to be updated
    # if additional writable fields are added to feature in the future
    # we'll add support for update as well as rename
    cd = gapi.directory.buildGAPIObject()
    oldName = sys.argv[3]
    body = {'newName': sys.argv[5:]}
    print(f'Updating feature {oldName}...')
    gapi.call(cd.resources().features(), 'rename',
              customer=GC_Values[GC_CUSTOMER_ID], oldName=oldName,
              body=body)


def deleteFeature():
    cd = gapi.directory.buildGAPIObject()
    featureKey = sys.argv[3]
    print(f'Deleting feature {featureKey}...')
    gapi.call(cd.resources().features(), 'delete',
              customer=GC_Values[GC_CUSTOMER_ID], featureKey=featureKey)


def _getResourceCalendarAttributes(cd, args, body={}):
    i = 0
    while i < len(args):
        myarg = args[i].lower().replace('_', '')
        if myarg == 'name':
            body['resourceName'] = args[i+1]
            i += 2
        elif myarg == 'description':
            body['resourceDescription'] = args[i+1].replace('\\n', '\n')
            i += 2
        elif myarg == 'type':
            body['resourceType'] = args[i+1]
            i += 2
        elif myarg in ['building', 'buildingid']:
            body['buildingId'] = getBuildingByNameOrId(
                cd, args[i+1], minLen=0)
            i += 2
        elif myarg in ['capacity']:
            body['capacity'] = __main__.getInteger(args[i+1], myarg, minVal=0)
            i += 2
        elif myarg in ['feature', 'features']:
            features = args[i+1].split(',')
            body['featureInstances'] = []
            for feature in features:
                instance = {'feature': {'name': feature}}
                body['featureInstances'].append(instance)
            i += 2
        elif myarg in ['floor', 'floorname']:
            body['floorName'] = args[i+1]
            i += 2
        elif myarg in ['floorsection']:
            body['floorSection'] = args[i+1]
            i += 2
        elif myarg in ['category']:
            body['resourceCategory'] = args[i+1].upper()
            if body['resourceCategory'] == 'ROOM':
                body['resourceCategory'] = 'CONFERENCE_ROOM'
            i += 2
        elif myarg in ['uservisibledescription', 'userdescription']:
            body['userVisibleDescription'] = args[i+1]
            i += 2
        else:
            controlflow.invalid_argument_exit(
                args[i], "gam create|update resource")
    return body


def createResourceCalendar():
    cd = gapi.directory.buildGAPIObject()
    body = {'resourceId': sys.argv[3],
            'resourceName': sys.argv[4]}
    body = _getResourceCalendarAttributes(cd, sys.argv[5:], body)
    print(f'Creating resource {body["resourceId"]}...')
    gapi.call(cd.resources().calendars(), 'insert',
              customer=GC_Values[GC_CUSTOMER_ID], body=body)


def updateResourceCalendar():
    cd = gapi.directory.buildGAPIObject()
    resId = sys.argv[3]
    body = _getResourceCalendarAttributes(cd, sys.argv[4:])
    # Use patch since it seems to work better.
    # update requires name to be set.
    gapi.call(cd.resources().calendars(), 'patch',
              customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId,
              body=body, fields='')
    print(f'updated resource {resId}')


def getResourceCalendarInfo():
    cd = gapi.directory.buildGAPIObject()
    resId = sys.argv[3]
    resource = gapi.call(cd.resources().calendars(), 'get',
                         customer=GC_Values[GC_CUSTOMER_ID],
                         calendarResourceId=resId)
    if 'featureInstances' in resource:
        features = []
        for a_feature in resource.pop('featureInstances'):
            features.append(a_feature['feature']['name'])
        resource['features'] = ', '.join(features)
    if 'buildingId' in resource:
        resource['buildingName'] = getBuildingNameById(
            cd, resource['buildingId'])
        resource['buildingId'] = f'id:{resource["buildingId"]}'
    display.print_json(resource)


def deleteResourceCalendar():
    resId = sys.argv[3]
    cd = gapi.directory.buildGAPIObject()
    print(f'Deleting resource calendar {resId}')
    gapi.call(cd.resources().calendars(), 'delete',
              customer=GC_Values[GC_CUSTOMER_ID], calendarResourceId=resId)
