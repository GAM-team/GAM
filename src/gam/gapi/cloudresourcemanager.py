import string
import sys

import googleapiclient.errors

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import fileutils
from gam import gapi
from gam import utils
from gam.gapi import errors as gapi_errors
from gam.gapi.directory import customer as gapi_directory_customer

def build():
    return gam.buildGAPIServiceObject('cloudresourcemanager',
                                      act_as=None)


def get_org_id():
    gapi_directory_customer.setTrueCustomerId()
    crm = build()
    query = f'directorycustomerid:{GC_Values[GC_CUSTOMER_ID]}'
    orgs = gapi.get_all_pages(crm.organizations(),
                     'search',
                     'organizations',
                     query=query)
    if len(orgs) < 1:
        controlflow.system_error_exit(2, 'Your service account needs permission to read org id')
    return orgs[0]['name']
