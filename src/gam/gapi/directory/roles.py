import sys

from gam.var import GC_Values, GC_CUSTOMER_ID
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import privileges as gapi_directory_privileges


def create():
    cd = gapi_directory.build()
    body = {'privileges': []}
    all_privileges = gapi_directory_privileges.print_(return_only=True)
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'privileges':
            privs = sys.argv[i + 1]
            if privs == 'all':
                body['rolePrivileges'] = all_privileges
            elif privs == 'all_ou':
                body['rolePrivileges'] = [
                    p for p in all_privileges if p.get('isOuScopable')
                ]
            else:
                # Known broken, need to get serviceName in here also...
                body['rolePrivileges'] = [{
                    'privilegeName': p
                } for p in sys.argv[i + 1].split(',')]
            i += 2
        elif myarg == 'name':
            body['roleName'] = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam create adminrole')
    print(f'Creating role {body["roleName"]}')
    gapi.call(cd.roles(),
              'insert',
              customer=GC_Values[GC_CUSTOMER_ID],
              body=body)


def print_():
    cd = gapi_directory.build()
    todrive = False
    titles = [
        'roleId', 'roleName', 'roleDescription', 'isSuperAdminRole',
        'isSystemRole'
    ]
    fields = f'nextPageToken,items({",".join(titles)})'
    csvRows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam print adminroles')
    roles = gapi.get_all_pages(cd.roles(),
                               'list',
                               'items',
                               customer=GC_Values[GC_CUSTOMER_ID],
                               fields=fields)
    for role in roles:
        role_attrib = {}
        for key, value in list(role.items()):
            role_attrib[key] = value
        csvRows.append(role_attrib)
    display.write_csv_file(csvRows, titles, 'Admin Roles', todrive)
