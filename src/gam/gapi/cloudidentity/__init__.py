import gam
from gam.var import GC_Values, GC_ENABLE_DASA

def build(api='cloudidentity'):
    return gam.buildGAPIObject(api)

def build_dwd(api='cloudidentity'):
    # If we are using DASA we don't need to use DwD.
    if GC_Values[GC_ENABLE_DASA]:
        return gam.buildGAPIObject(api)
    admin = gam._get_admin_email()
    return gam.buildGAPIServiceObject(api, admin, True)
