import gam
from gam.var import GC_Values, GC_CUSTOMER_ID
from gam import controlflow
from gam import gapi
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
        # return nothing and let calling API deal with it
        # since caller knows what GCP role would serve best
        return 
    return orgs[0]['name']
