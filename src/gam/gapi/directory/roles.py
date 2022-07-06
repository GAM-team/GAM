import sys

from gam.var import (
        GC_Values,
        GC_CUSTOMER_ID,
        GM_Globals,
        GM_MAP_ROLE_ID_TO_NAME,
        GM_MAP_ROLE_NAME_TO_ID,
        UID_PATTERN
        )
import gam
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import privileges as gapi_directory_privileges


def buildRoleIdToNameToIdMap(cd=None):
    if not cd:
        cd = gapi_directory.build()
    result = gapi.get_all_pages(cd.roles(),
                                'list',
                                'items',
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields='nextPageToken,items(roleId,roleName)')
    GM_Globals[GM_MAP_ROLE_ID_TO_NAME] = {}
    GM_Globals[GM_MAP_ROLE_NAME_TO_ID] = {}
    for role in result:
        GM_Globals[GM_MAP_ROLE_ID_TO_NAME][role['roleId']] = role['roleName']
        GM_Globals[GM_MAP_ROLE_NAME_TO_ID][role['roleName']] = role['roleId']


def role_from_roleid(roleid):
    if not GM_Globals[GM_MAP_ROLE_ID_TO_NAME]:
        buildRoleIdToNameToIdMap()
    return GM_Globals[GM_MAP_ROLE_ID_TO_NAME].get(roleid, roleid)


def roleid_from_role(role):
    if not GM_Globals[GM_MAP_ROLE_NAME_TO_ID]:
        buildRoleIdToNameToIdMap()
    return GM_Globals[GM_MAP_ROLE_NAME_TO_ID].get(role, None)


def getRoleId(role):
    cg = UID_PATTERN.match(role)
    if cg:
        roleId = cg.group(1)
    else:
        roleId = roleid_from_role(role)
        if not roleId:
            controlflow.system_error_exit(
                4,
                f'{role} is not a valid role. Please ensure role name is exactly as shown in admin console.'
            )
    return roleId


def getPrivileges(body, privs, action):
    def expandChildPrivileges(privilege):
        for childPrivilege in privilege.get('childPrivileges', []):
            childPrivileges[childPrivilege['privilegeName']] = childPrivilege['serviceId']
            expandChildPrivileges(childPrivilege)

    allPrivileges = {}
    ouPrivileges = {}
    childPrivileges = {}
    for privilege in gapi_directory_privileges.print_(return_only=True):
        allPrivileges[privilege['privilegeName']] = privilege['serviceId']
        if privilege['isOuScopable']:
            ouPrivileges[privilege['privilegeName']] = privilege['serviceId']
        expandChildPrivileges(privilege)
    if privs == 'ALL':
        body['rolePrivileges'] = [{'privilegeName': priv, 'serviceId': v} for priv, v in allPrivileges.items()]
    elif privs == 'ALL_OU':
        body['rolePrivileges'] = [{'privilegeName': priv, 'serviceId': v} for priv, v in ouPrivileges.items()]
    else:
      body.setdefault('rolePrivileges', [])
      for priv in privs.split(','):
          if priv in allPrivileges:
              body['rolePrivileges'].append({'privilegeName': priv, 'serviceId': allPrivileges[priv]})
          elif priv in ouPrivileges:
              body['rolePrivileges'].append({'privilegeName': priv, 'serviceId': ouPrivileges[priv]})
          elif priv in childPrivileges:
              body['rolePrivileges'].append({'privilegeName': priv, 'serviceId': childPrivileges[priv]})
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

