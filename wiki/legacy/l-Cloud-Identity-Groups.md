- [Creating Groups](#creating-groups)
- [Updating Groups](#updating-groups)
- [Get info about a group](#get-info-about-a-group)
- [Delete a group](#delete-a-group)

Cloud Identity Group commands operate against regular Google Groups but offer additional functionality such as dynamic groups and group restrictions.

# Creating Groups
### Syntax
```
gam create cigroup <email> [name <name>] [description <description>] [dynamic <query>] [makeowner]
```
Creates a Cloud Identity group. The email argument specifies the email of the group. The name and description arguments specify additional details about the group. The dynamic argument specifies [a CEL query](https://cloud.google.com/identity/docs/how-to/test-query-dynamic-groups) which will determine the group membership. Dynamic groups is [a premium feature not available to all SKUs](https://support.google.com/a/answer/10286834?hl=en). By default the group will be empty. You can add the makeowner argument to add the admin GAM is running with as the group owner.

### Example
This example creates a Cloud Identity group
```
gam create cigroup eng@acme.com name "Engineer Team" description "all engineers"
```
This example creates a dynamic group. Any user with Sales as their department will be a member of the group
```
gam create cigroup dyn.sales@acme.com name "Sales (dynamic)" description "members of Sales dept" dynamic "user.organizations.exists(org, org.department=='Sales')"
```
----

# Updating Groups
### Syntax
```
gam update cigroup <email> [name <name>] [description <description>] [security] [dynamic <query>] [memberrestriction]
```
Updates settings for a group. The name and description arguments update group details. The security argument marks the group as a [Google Security group](https://support.google.com/a/answer/10607394?hl=en). MARKING A GROUP AS A SECURITY GROUP CANNOT BE UNDONE. Security groups is a premium feature not available to all SKUs. The dynamic argument changes the [CEL query](https://cloud.google.com/identity/docs/how-to/test-query-dynamic-groups) for an existing group. The memberrestriction argument specifies a CEL query which will [limit the types of members allowed in the group](https://support.google.com/a/answer/11192679). Member restrictions is a premium feature not available to all SKUs.

### Example
This example makes a group a security group. This is a one-way operation.
```
gam update cigroup gcp-owners@acme.com security
```
This example restricts group membership to internal users only. Other groups, external email addresses and service accounts cannot be added or join the group.
```
gam update cigroup gcp-owners@acme.com memberrestriction "member.type == 1 && member.customer_id == groupCustomerId()"
```
----

# Get info about a group
### Syntax
```
gam info cigroup <email> [nousers] [nojoindate] [showupdatedate] [membertree] [nosecuritysettings]
```
Shows information about a given Cloud Identity group. The optional arguments nousers, nojoindate and nosecuritysettings limit what data is output. The optional argument showupdatedate includes additional details about when the members status was last updated. The optional argument membertree displays a tree of inherited group memberships (only available to premium Workspace/Cloud Identity SKUs).

### Example
This example displays information about a group.
```
gam info cigroup gcp-owners@acme.com
```
----

# Delete A Group
### Syntax
```
gam delete cigroup <email>
```
Deletes the given group.

### Example
This example deletes a group.
```
gam delete cigroup gcp-owners@acme.com
```
----
