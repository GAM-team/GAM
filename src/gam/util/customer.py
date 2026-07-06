"""Customer ID helpers.

Utilities for retrieving and formatting Google Workspace customer IDs.
This is a leaf module created to break the entity ↔ licenses import cycle.
"""

from gamlib import gapi as GAPI
from gamlib import settings as GC
from gam.util.api import ClientAPIAccessDeniedExit, buildGAPIObject
from gamlib import api as API
from gam.util.api_call import callGAPI


def _getCustomerId():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId != GC.MY_CUSTOMER and customerId[0] != 'C':
    customerId = 'C' + customerId
  return customerId

def _getCustomerIdNoC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId[0] == 'C':
    return customerId[1:]
  return customerId

def _getCustomersCustomerIdNoC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId.startswith('C'):
    customerId = customerId[1:]
  return f'customers/{customerId}'

def _getCustomersCustomerIdWithC():
  customerId = GC.Values[GC.CUSTOMER_ID]
  if customerId != GC.MY_CUSTOMER and customerId[0] != 'C':
    customerId = 'C' + customerId
  return f'customers/{customerId}'

def setTrueCustomerId(cd=None, forceUpdate=False):
  if GC.Values[GC.CUSTOMER_ID] == GC.MY_CUSTOMER or forceUpdate:
    if not cd:
      cd = buildGAPIObject(API.DIRECTORY)
    try:
      customerInfo = callGAPI(cd.customers(), 'get',
                              throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_INPUT, GAPI.RESOURCE_NOT_FOUND,
                                            GAPI.FORBIDDEN, GAPI.PERMISSION_DENIED],
                              customerKey=GC.MY_CUSTOMER,
                              fields='id')
      GC.Values[GC.CUSTOMER_ID] = customerInfo['id']
    except (GAPI.badRequest, GAPI.invalidInput, GAPI.resourceNotFound):
      pass
    except (GAPI.forbidden, GAPI.permissionDenied) as e:
      ClientAPIAccessDeniedExit(str(e))
