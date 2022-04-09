import sys

import googleapiclient

import gam
from gam.var import * # pylint: disable=unused-wildcard-import
from gam import controlflow
from gam import display
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors
from gam.gapi import cloudidentity as gapi_cloudidentity
from gam.gapi.directory import orgunits as gapi_directory_orgunits

def _get_orgunit_customerid():
  customer = GC_Values[GC_CUSTOMER_ID]
  if customer != MY_CUSTOMER and not customer.startswith('C'):
      customer = f'C{customer}'
  return f'customers/{customer}'

def move_shared_drive(driveId, orgUnit):
    _, orgUnitId = gapi_directory_orgunits.getOrgUnitId(orgUnit)
    orgUnitId = f'orgUnits/{orgUnitId[3:]}'
    name = f'orgUnits/-/memberships/shared_drive;{driveId}'
    ci = gapi_cloudidentity.build('cloudidentity_beta')
    body = {
            'customer': _get_orgunit_customerid(),
            'destinationOrgUnit': orgUnitId,
           }
    return gapi.call(ci.orgUnits().memberships(),
              'move',
              name=name,
              body=body)

def printshow_orgunit_shared_drives(csvFormat):
    orgunit = '/'
    if csvFormat:
        todrive = False
        csvRows = []
        titles = ['name']
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if csvFormat and myarg == 'todrive':
            todrive = True
            i += 1
        elif myarg in ['ou', 'org', 'orgunit']:
          orgunit = sys.argv[i + 1]
          i += 2
        else:
          controlflow.invalid_argument_exit(sys.argv[i],
                                            f"gam {['show', 'print'][csvFormat]} oushareddrives")
    ci = gapi_cloudidentity.build('cloudidentity_beta')
    _, orgUnitId = gapi_directory_orgunits.getOrgUnitId(orgunit)
    parent = f'orgUnits/{orgUnitId[3:]}'
    filter_ = "type == 'shared_drive'"
    sds = gapi.get_all_pages(ci.orgUnits().memberships(),
                       'list',
                       'orgMemberships',
                       parent=parent,
                       customer=_get_orgunit_customerid(),
                       filter=filter_)
    if not csvFormat:
        for sd in sds:
            display.print_json(sd)
            print()
    else:
        for sd in sds:
            display.add_row_titles_to_csv_file(
                utils.flatten_json(sd),
                csvRows, titles)
        display.write_csv_file(csvRows, titles, f'OrgUnit {orgunit} Shared Drives', todrive)
