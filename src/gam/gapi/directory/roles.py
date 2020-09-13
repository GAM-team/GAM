import sys

from gam.var import GC_Values, GC_CUSTOMER_ID
import gam
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import privileges as gapi_directory_privileges


def getPrivileges(body, privs, action):
    all_privileges = gapi_directory_privileges.print_(return_only=True)
    if privs == 'ALL':
        body['rolePrivileges'] = [
            {'privilegeName': p['privilegeName'], 'serviceId': p['serviceId']} for p in all_privileges
            ]
    elif privs == 'ALL_OU':
        body['rolePrivileges'] = [
            {'privilegeName': p['privilegeName'], 'serviceId': p['serviceId']} for p in all_privileges if p.get('isOuScopable')
            ]
    else:
      body.setdefault('rolePrivileges', [])
      for priv in privs.split(','):
          for p in all_privileges:
              if priv == p['privilegeName']:
                body['rolePrivileges'].append({'privilegeName': p['privilegeName'], 'serviceId': p['serviceId']})
                break
          else:
              controlflow.invalid_argument_exit(priv,
                                                f'gam {action} adminrole privileges')

def create():
    cd = gapi_directory.build()
    body = {'roleName': sys.argv[3]}
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'privileges':
            getPrivileges(body, sys.argv[i + 1].upper(), 'create')
            i += 2
        elif myarg == 'description':
            body['roleDescription'] = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam create adminrole')

    if not body.get('rolePrivileges'):
        controlflow.missing_argument_exit('privileges',
                                          'gam create adminrole')
    print(f'Creating role {body["roleName"]}')
    gapi.call(cd.roles(),
              'insert',
              customer=GC_Values[GC_CUSTOMER_ID],
              body=body)

def update():
    cd = gapi_directory.build()
    body = {}
    roleId = gam.getRoleId(sys.argv[3])
    i = 4
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'privileges':
            getPrivileges(body, sys.argv[i + 1].upper(), 'update')
            i += 2
        elif myarg == 'description':
            body['roleDescription'] = sys.argv[i + 1]
            i += 2
        elif myarg == 'name':
            body['roleName'] = sys.argv[i + 1]
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i],
                                              'gam update adminrole')

    print(f'Updating role {roleId}')
    gapi.call(cd.roles(),
              'patch',
              customer=GC_Values[GC_CUSTOMER_ID],
              roleId=roleId,
              body=body)


def delete():
    cd = gapi_directory.build()
    roleId = gam.getRoleId(sys.argv[3])
    print(f'Deleting role {roleId}')
    gapi.call(cd.roles(),
              'delete',
              customer=GC_Values[GC_CUSTOMER_ID],
              roleId=roleId)


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
