import gam


def build(api='cloudidentity'):
    return gam.buildGAPIObject(api)

def build_dwd(api='cloudidentity'):
    admin = gam._getValueFromOAuth('email')
    return gam.buildGAPIServiceObject(api, admin, True)
