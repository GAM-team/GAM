- [Creating an Organization Unit](#creating-an-organization-unit)
- [Updating (and adding users to) an Organization Unit](#updating-and-adding-users-to-an-organization-unit)
- [Retrieving an Organization Unit's Information](#retrieving-an-organization-units-information)
- [Deleting an Organization Unit](#deleting-an-organization-unit)

# Creating an Organization Unit
## Syntax
```
gam create org <name> [description <Description>] [parent <Parent Org>] [noinherit]
```
create an organizational unit. The required argument name is the organization unit name, if it contains spaces, it should be quoted. The optional argument description offers more details on the organizational unit, if it contains spaces it should be quoted. The optional argument parent allows the organization unit to be created as a sub-org of an existing organization unit, if it contains spaces it should be quoted. If parent is not specified, the new organization is created at the top level. The optional argument noinherit blocks policy setting inheritance from organization units higher in the organization tree, inheritance is enabled by default if noinherit is not specified.

## Example
This example creates an Organization Unit with all optional arguments

```
gam create org "Mail Enabled Faculty" description "Faculty with access to Gmail" parent /Employees
```

---


# Updating (and adding users to) an Organization Unit
## Syntax
```
gam update org <name> [name <New Name>] [description <Description>] [parent <Parent>] [inherit|noinherit] [add users <Users> | file <File Name> | group <Group Name>]
```
update an organization unit. The required argument name is the organization unit name, if it contains spaces, it should be quoted. If the organization unit is a sub-organization, it should use the format "parent org/org" (use the / character between the parent and the sub-org). The optional argument "name ..." specifies a new name for the organization unit, if it contains spaces, it should be quoted. The optional argument description offers more details on the organizational unit, if it contains spaces it should be quoted. The optional argument parent allows the organization unit to be moved as a sub-org of an existing organization unit, if it contains spaces it should be quoted. The optional arguments inherit and noinherit enable/disable inheritance respectfully. The optional argument add specifies a list, filename or group of users that should be moved into the organization unit. If using add users, the list of users should be quoted and spaces should be used between each user. If using file, the given file should contain a list of users to be added, one per line. If using group, specify the name of a Google Apps group that contains the users you would like moved into the organization unit.

**Important:** Users can only exist in one organization unit at a time. When you add them to an organization unit with this command, they will be removed from their previous organization unit.


## Example
This example updates the organization unit's parameters without adding any users
```
gam update org Faculty description "Faculty Users" parent Employees
```

This example renames the organization unit
```
gam update org Faculty name "Faculty and Staff"
```

This example adds the given list of users to the organization unit
```
gam update org Faculty add users "socrates plato aristotle"
```

This example assumes that the file faculty.txt exists and looks like:
```
davinci
michelangelo
raphael
```
it will add these users to the organization unit
```
gam update org Faculty add file faculty.txt
```

This example will add members of the Google Apps group inventors to the Faculty organization unit
```
gam update org Faculty add group inventors
```

---


# Retrieving an Organization Unit's Information
## Syntax
```
gam info org <name> [nousers|child]
```
retrieve details about the given organization unit. GAM will print a summary of the organization unit. If the nousers argument is selected, the users in the org won't be listed. The child argument prints users in the sub-orgs along with the string "(child") next to their email address.

## Example
This example will print a summary detailing the given organization unit
```
gam info org Faculty
Organization Unit: Faculty
Description: Faculty Users
Parent Org: /
Block Inheritance: false
Users:
 davinci@domain.com
 michelangelo@domain.com
 raphael@domain.com
```

---


# Deleting an Organization Unit
## Syntax
```
gam delete org <orgUnitPath>
```
delete the given organization unit.

**Important:** The organization unit must be completely emptied of users and sub-organizations before it can be deleted.

## Example
This example will delete the already emptied organization unit Sub-faculty and then afterwards delete the emptied organization unit Faculty.

```
gam delete org /Faculty/Sub-faculty
```

```
gam delete org /Faculty
```
---
