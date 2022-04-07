"""Methods related to Drive API Shared Drives"""
import sys


import gam
from gam.var import GC_CUSTOMER_ID, GC_Values, MY_CUSTOMER, SORTORDER_CHOICES_MAP
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi import drive as gapi_drive

def drive_name_to_id(name, drive=None):
    if not drive:
        _, drive = gapi_drive.build()
    q = f"name = '{name}'"
    sds = gapi.get_all_pages(drive.drives(),
                             'list',
                             'drives',
                             q=q,
                             useDomainAdminAccess=True)
    if len(sds) == 0:
        controlflow.system_error_exit(f'Could not find shared drive named "{name}"')
    elif len(sds) > 1:
        controlflow.system_error_exit(f'Got more than one shared drive named "{name}"')
    return sds[0]['id']
