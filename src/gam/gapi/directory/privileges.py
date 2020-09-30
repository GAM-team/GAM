from gam.var import GC_Values, GC_CUSTOMER_ID
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory


def flatten_privilege_list(privs, parent=None):
    flat_privs = []
    for priv in privs:
        children = []
        if parent:
            priv['parent'] = parent
        if priv.get('childPrivileges'):
            children = flatten_privilege_list(priv['childPrivileges'],
                                              parent=priv['privilegeName'])
            priv['children'] = ' '.join(
                [child['privilegeName'] for child in children])
            del priv['childPrivileges']
        flat_privs = flat_privs + children
        flat_privs.append(priv)
    return flat_privs


def print_(return_only=False):
    cd = gapi_directory.build()
    privs = gapi.call(cd.privileges(),
                      'list',
                      customer=GC_Values[GC_CUSTOMER_ID])
    privs = flatten_privilege_list(privs.get('items', []))
    if return_only:
        return privs
    display.print_json(privs)
