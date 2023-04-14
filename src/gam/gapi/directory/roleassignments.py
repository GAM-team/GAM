import sys

from gam.var import GC_Values, GC_CUSTOMER_ID
import gam
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import directory as gapi_directory
from gam.gapi.directory import orgunits as gapi_directory_orgunits
from gam.gapi.directory import roles as gapi_directory_roles


SECURITY_GROUP_CONDITION = "api.getAttribute('cloudidentity.googleapis.com/groups.labels', []).hasAny(['groups.security']) && resource.type == 'cloudidentity.googleapis.com/Group'"
NONSECURITY_GROUP_CONDITION = f'!{SECURITY_GROUP_CONDITION}'

def create():
    cd = gapi_directory.build()
    user = gam.normalizeEmailAddressOrUID(sys.argv[3])
    body = {'assignedTo': gam.convertEmailAddressToUID(sys.argv[3],
                          cd=cd,
                          email_type='any')}
    role = sys.argv[4]
    body['roleId'] = gapi_directory_roles.getRoleId(role)
    body['scopeType'] = sys.argv[5].upper()
    i = 6
    if body['scopeType'] not in ['CUSTOMER', 'ORG_UNIT']:
        controlflow.expected_argument_exit('scope type',
                                           ', '.join(['customer', 'org_unit']),
                                           body['scopeType'])
    if body['scopeType'] == 'ORG_UNIT':
        orgUnit, orgUnitId = gapi_directory_orgunits.getOrgUnitId(
            sys.argv[i], cd)
        body['orgUnitId'] = orgUnitId[3:]
        scope = f'ORG_UNIT {orgUnit}'
        i = 7
    else:
        scope = 'CUSTOMER'
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'condition':
            cd = gapi_directory.build_beta()
            body['condition'] = sys.argv[i+1]
            if body['condition'] == 'securitygroup':
                body['condition'] = SECURITY_GROUP_CONDITION
            elif body['condition'] == 'nonsecuritygroup':
                body['condition'] = NONSECURITY_GROUP_CONDITION
            i += 2
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam create admin')
    print(f'Giving {user} admin role {role} for {scope}')
    gapi.call(cd.roleAssignments(),
              'insert',
              customer=GC_Values[GC_CUSTOMER_ID],
              body=body)


def delete():
    cd = gapi_directory.build()
    roleAssignmentId = sys.argv[3]
    print(f'Deleting Admin Role Assignment {roleAssignmentId}')
    gapi.call(cd.roleAssignments(),
              'delete',
              customer=GC_Values[GC_CUSTOMER_ID],
              roleAssignmentId=roleAssignmentId)


def print_():
    cd = gapi_directory.build()
    roleId = None
    todrive = False
    kwargs = {}
    item_fields = ['roleAssignmentId', 'roleId', 'assignedTo', 'scopeType', 'orgUnitId']
    titles = [
        'roleAssignmentId', 'roleId', 'role', 'assignedTo', 'assignedToUser',
        'assignedToGroup', 'scopeType', 'orgUnitId', 'orgUnit'
    ]
    csvRows = []
    i = 3
    while i < len(sys.argv):
        myarg = sys.argv[i].lower()
        if myarg == 'user':
            kwargs['userKey'] = gam.normalizeEmailAddressOrUID(sys.argv[i + 1])
            i += 2
        elif myarg == 'role':
            roleId = gapi_directory_roles.getRoleId(sys.argv[i + 1])
            i += 2
        elif myarg == 'condition':
            cd = gapi_directory.build_beta()
            item_fields.append('condition')
            i += 1
        elif myarg == 'todrive':
            todrive = True
            i += 1
        else:
            controlflow.invalid_argument_exit(sys.argv[i], 'gam print admins')
    fields = f'nextPageToken,items({",".join(item_fields)})'
    if roleId and not kwargs:
        kwargs['roleId'] = roleId
        roleId = None
    admins = gapi.get_all_pages(cd.roleAssignments(),
                                'list',
                                'items',
                                customer=GC_Values[GC_CUSTOMER_ID],
                                fields=fields,
                                **kwargs)
    for admin in admins:
        if roleId and roleId != admin['roleId']:
            continue
        admin_attrib = {}
        for key, value in list(admin.items()):
            if key == 'assignedTo':
                email_types = admin_attrib.get('assigneeType')
                if email_types == 'user':
                    email_field = 'assignedToUser'
                elif email_types == 'group':
                    email_field = 'assignedToGroup'
                else:
                    email_field = None
                assignment_email, assignment_type = gam.convertUIDtoEmailAddress(f'uid:{value}', cd, email_types=['user', 'group'])
                if not email_field and assignment_type in ['user', 'group']:
                    if assignment_type == 'user':
                        email_field = 'assignedToUser'
                    else:
                        email_field = 'assignedToGroup'
                if email_field:
                    admin_attrib[email_field] = assignment_email
            elif key == 'roleId':
                admin_attrib['role'] = gapi_directory_roles.role_from_roleid(value)
            elif key == 'orgUnitId':
                value = f'id:{value}'
                admin_attrib[
                    'orgUnit'] = gapi_directory_orgunits.orgunit_from_orgunitid(
                        value, cd)
            elif key == 'condition':
                if value == SECURITY_GROUP_CONDITION:
                    value = 'securitygroup'
                elif value == NONSECURITY_GROUP_CONDITION:
                    value = 'nonsecuritygroup'
            if key not in titles:
                titles.append(key)
            admin_attrib[key] = value
        csvRows.append(admin_attrib)
    display.write_csv_file(csvRows, titles, 'Admins', todrive)
