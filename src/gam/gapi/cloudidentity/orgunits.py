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

def print_orgunit_shared_drives():
    try:
        orgunit = sys.argv[3]
    except IndexError:
        orgunit = '/'
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
    for sd in sds:
        display.print_json(sd)
        print()
