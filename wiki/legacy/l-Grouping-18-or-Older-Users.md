# Using GAM to group 18+ users
## Background
Before September, 2021, all Google Workspace for Education customer’s administrators will either have to mark users as being 18 or above (in K12 institutions) or under the age of 18 (in higher education institutions). If an administrator does not appropriately mark users, their experience within Google Additional Services will be impacted.

## Purpose
The purpose of this article is to outline a quick set of practices to notate K12 institutions’ adults as being 18 or older. While this can be done natively within the Admin console using Organizational Units, Dynamic Groups, or regular Google groups, some institutions may not have these structures needed to quickly denote users as being 18 or older. This article will walk you through using GAM to create a Google group, adding adults to the group, and then notating the group as being 18 or older.

## Directions
### Create a new group that is easily identifiable as 18 or older
`gam create group 18OrOlder`

### Lock down the nearly-created group so that it cannot be abused
`gam update group 18OrOlder who_can_post_message all_managers_can_post who_can_contact_owner ALL_MANAGERS_CAN_CONTACT who_can_leave_group NONE_CAN_LEAVE include_in_global_address_list false members_can_post_as_the_group false allow_google_communication false who_can_view_membership all_managers_can_view who_can_join invited_can_join who_can_invite NONE_CAN_INVITE show_in_group_directory false allow_external_members false who_can_view_group all_managers_can_view allow_web_posting false`

### Add adults to the group
These are just suggestions on how this can be done.

#### Add users of a Staff OU to the group
`gam update group 18OrOlder add member ou_and_children Staff`

#### Add users of a CSV containing all staff members to the group
`gam csv Adults.csv gam update group 18OrOlder add member ~Username`

#### Add all users matching a similar attribute
`gam print users query "orgDescription='TEACHER'" | gam csv - gam update group 18OrOlder add member \~primaryEmail`

#### Utilize the classroom teachers group
`gam update group 18OrOlder add member classroom_teachers`

### Once the group is populated with adults
Navigate to your Google Workspace Admin console and open up your age-based access control. Target the 18OrOlder group that you just created and select the radio button “All users are 18 or older” and click Save.

As additional adults are identified, they can be added to the group and will be treated as an adult by Workspace within 24-48 hours.