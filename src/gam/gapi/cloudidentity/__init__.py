import gam


def build(api='cloudidentity'):
    return gam.buildGAPIObject(api)

def build_dwd(api='cloudidentity'):
    admin = gam._get_admin_email()
    return gam.buildGAPIServiceObject(api, admin, True)
