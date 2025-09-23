- [Grant a User an Admin Role](#grant-a-user-an-admin-role)
- [Delete a User's Admin Role](#delete-a-users-admin-role)
- [Print All Admin Role Assignments](#print-all-admins)
- [Print All Admin Roles](#print-all-admin-roles)

# Grant a User an Admin Role
## Syntax
```
gam create admin <user> <role> customer|org_unit <OU> [condition securitygroup|nonsecuritygroup]
```
Grants the given user account rights as the given admin role. The command must specify whether the rights are to be granted to the entire customer G Suite domain or to a certain org_unit and it's children org unit's. Note that some roles cannot be granted to org units, they must specify customer. The optional argument condition limits the conditions for delegate admin access. This currently only works with the `_GROUPS_EDITOR_ROLE` and `_GROUPS_READER_ROLE` roles. Condition can be to limit the delegated admin to managing security groups (`securitygroup`) or to non-security groups (`nonsecuritygroup`).

## Examples
This example makes admin@acme.com a super admin
```
gam create admin admin@acme.com _SEED_ADMIN_ROLE customer
```

This example makes ny-helpdesk@acme.com a helpdesk admin for the /NY Org Unit.
```
gam create admin ny-helpdesk@acme.com _HELP_DESK_ADMIN_ROLE org_unit "NY"
```
This example allows sfo-helpdesk@acme.com to manage only groups that are NOT marked as security groups:
```
gam create admin sfo-helpdesk@acme.com _GROUPS_EDITOR_ROLE customer condition nonsecuritygroup
```
----

# Delete a User's Admin Role
## Syntax
```
gam delete admin <role assignment id>
```
Removes an admin role assignment. Use [Print All Admins](#print-all-admins) to see existing assignments, you're looking for the roleAssignmentId column. You can also use CSV commands to revoke all rights for a given user.

## Examples
This example revokes the given user's admin role.
```
gam delete admin 8771356963373081
```

This example revokes ALL admin role assignments for the oldadmin@acme.com user account.
```
gam print admins user oldadmin@acme.com | gam csv - gam delete admin ~roleAssignmentId
```
----

# Print All Admins
## Syntax
```
gam print admins [user <user>] [role <role>] [condition] [todrive]
```
Prints all admin role assignments in the G Suite instance. Note that one user account can be assigned multiple roles and can be assigned one role on multiple orgs so a single user may be returned in multiple rows. 

The optional user argument limits returned role assignments to those granted to the given user.

The optional role argument limits returned role assignments to those of the given role.

The optional condition argument displays any conditions associated with a role assignment.

The optional todrive argument tells GAM to create a Google Docs Spreadsheet instead of outputting the results to CSV.

## Examples
This example prints out all admin role assignments
```
gam print admins
```

This example prints out all admin role assignments for admin@acme.com
```
gam print admins user admin@acme.com
```

This example prints out all super admin role assignments
```
gam print admins role _SEED_ADMIN_ROLE
```
----

# Print All Admin Roles
## Syntax
```
gam print roles [todrive]
```
Prints all admin roles created within the G Suite Instance. The optional argument todrive causes GAM to create a Google Docs Spreadsheet of results instead of outputting CSV.

## Examples
This example creates a spreadsheet of all admin roles for a domain.
```
gam print roles todrive
```
----