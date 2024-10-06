- [Enabling Google Groups for Business](#enabling-google-groups-for-business)
- [Updating  Group Settings](#updating--group-settings)
  - [Allow External Members](#allow-external-members)
  - [Message Moderation Level](#message-moderation-level)
  - [Primary Language](#primary-language)
  - [Reply To](#reply-to)
  - [Send Message Deny Notification](#send-message-deny-notification)
  - [Show In Groups Directory](#show-in-groups-directory)
  - [Who Can Invite](#who-can-invite)
  - [Who Can Join](#who-can-join)
  - [Who Can Post Message](#who-can-post-message)
  - [Who Can View Group](#who-can-view-group)
  - [Who Can View Membership](#who-can-view-membership)
  - [Allow Google Communication](#allow-google-communication)
  - [Allow Web Posting](#allow-web-posting)
  - [Archive Only](#archive-only)
  - [Custom Reply To](#custom-reply-to)
  - [Is Archived](#is-archived)
  - [Max Message Bytes](#max-message-bytes)
  - [Members Can Post As The Group](#members-can-post-as-the-group)
  - [Message Display Font](#message-display-font)
  - [Description](#description)
  - [Group Name](#group-name)
  - [Spam Moderation Level](#spam-moderation-level)
  - [Include in Global Address List (GAL)](#include-in-global-address-list-gal)
  - [Who Can Leave Group](#who-can-leave-group)
  - [Who Can Contact Owner](#who-can-contact-owner)

# Enabling Google Groups for Business
In order to make use of the advanced Group Settings for your Google Apps domain, you need to have the Google Groups for Business service enabled for your domain. Please verify that you've enabled the service by [following Google's instructions](http://www.google.com/support/a/bin/answer.py?hl=en&answer=167096).

# Updating  Group Settings
You can update all of the group settings listed by the
```
gam update group <group>
```
command. You can also specify any of these group settings during group creation. For example:
```
gam create group sales@acme.org max_message_size 25M
```

The commands below are broken up below to only discuss one group setting for each area but they can easily be combined. For example you could change both the archive status, group name and description with a command like:
```
gam update group employees@example.com is_archived true name "Example Employees" description "list of example employees"
```

## Allow External Members
### Syntax
```
gam update group <group> allow_external_members true|false
```
Whether or not **group owners** are allowed to add users outside the Google Apps domain to the group. Google Apps admins should always be able to add external email addresses to the group.
### Example
This example prevents group owners from adding users outside the Google Apps domain to the employees group
```
gam update group employees@example.com allow_external_members false
```

---


## Message Moderation Level
### Syntax
```
gam update group <group> message_moderation_level moderate_all_messages|moderate_new_members|moderate_none|moderate_non_members
```
The level of moderation that the group should have. moderate\_all\_messages will require a owner/manager to approve all messages sent to the group before they are emailed or viewable by group members. moderate\_new\_members places only new group members under moderation. moderate\_none disables group moderation completely. moderate\_non\_members will moderate only messages sent to the group from email addresses that are not a member of the group.

### Example
This example sets the group to moderate new members
```
gam update group coffeetalk@example.com message_moderation_level moderate_new_members
```

---


## Primary Language
### Syntax
```
gam update group <group> primary_language <language>
```
Update the primary language used by the group. For a list of valid languages see [here](https://developers.google.com/admin-sdk/email-settings/?csw=1#language_tags).

### Example
This command sets the primary language for the english majors group to US English.
```
gam update group english-majors@acme.edu primary_language en-US
```

---


## Reply To
### Syntax
```
gam update group <group> reply_to reply_to_custom|reply_to_ignore|reply_to_list|reply_to_managers|reply_to_owner|reply_to_sender
```
Determine who, by default replies to group messages will be directed to.  reply\_to\_custom will use the email address set with the custom\_reply\_to command (suggest you combine these commands, see example). reply\_to\_ignore allows the group users to decide individually where the reply will go to. reply\_to\_list directs the reply back to the list address. reply\_to\_managers will direct replies to the group's managers/owners. reply\_to\_owner will direct replies to the group's owners. reply\_to\_sender directs replies at the sender of the original message.

### Example
This command sets the reply to a custom address, the custom address is also set to doodads@acme.com by the custom\_reply\_to command.
```
gam update group widgets@acme.com reply_to reply_to_custom custom_reply_to doodads@acme.com
```
This command sets the reply to go back to the list
```
gam update group widgets@acme.com reply_to reply_to_list
```

---


## Send Message Deny Notification
### Syntax
```
gam update group <group> send_message_deny_notification true|false
```
Determine whether or not the text of message\_deny\_notification\_text is sent to the sender of rejected messages. If this setting is true, message\_deny\_notification\_text should also be set to something.

### Example
This example turns message deny notification off for sales@acme.com.
```
gam update group sales@acme.com send_message_deny_notification false
```

---


## Show In Groups Directory
### Syntax
```
gam update group <group> show_in_group_directory true|false
```
Should the group be listed in the master list of all groups shown to users.

**Note:** If you have "Group owners can hide groups from the groups directory" unchecked under Settings, Google Groups for Business within the Google Apps Control Panel, this setting will remain true for all groups and attempts to make it false will have no effect.

### Example
This example removes the secretlabs@acme.com group from the group directory listing.
```
gam update group <group> show_in_group_directory false
```

---


## Who Can Invite
### Syntax
```
gam update group <group> who_can_invite ALL_MEMBERS_CAN_INVITE|ALL_MANAGERS_CAN_INVITE|NONE_CAN_INVITE
```
Determine who is allowed to invite new members to the group.  ALL\_MEMBERS\_CAN\_INVITE allows anyone who is already a member of the group to invite others to join. ALL\_MANAGERS\_CAN\_INVITE allows only group managers and owners to invite others. NONE\_CAN\_INVITE prevents anyone from inviting new members to the group via the web UI, requiring all members to be added via the API (or GAM).

### Example
This example allows any existing member of engineers@acme.com to invite others to join the group.
```
gam update group engineers@acme.com who_can_invite all_members_can_invite
```

---


## Who Can Join
### Syntax
```
gam update group <group> who_can_join all_in_domain_can_join|anyone_can_join|can_request_to_join|invited_can_join
```
Determines who is allowed to become a member of the group. all\_in\_domain\_can\_join allows any domain members to directly join the group. anyone\_can\_join allows any logged in Google Account to join the group. can\_request\_to\_join allows anyone to request membership to join. invited\_can\_join allows only those members who have received invitations to join the group (disable request to join). invited\_can\_join can be used with setting [Who Can Invite](#who-can-invite) to NONE_CAN_INVITE to prevent the addition of new members via the Web UI.

### Example
This example allows anyone on the Internet to potentially join the deals@acme.com group.
```
gam update group deals@acme.com  who_can_join anyone_can_join
```

---


## Who Can Post Message
### Syntax
```
gam update group <group> who_can_post_message all_in_domain_can_post|all_managers_can_post|all_members_can_post|anyone_can_post|none_can_post
```
Determine who is allowed to send messages to the group. all\_in\_domain\_can\_post allows any Google Apps user in the domain to send messages (even if they're not a group member). all\_managers\_can\_post limits sending rights to owners and managers. all\_members\_can\_post allows anyone who has joined the group to send messages. anyone\_can\_post allows anyone on the Internet to send email to the group address. none\_can\_post is not normally directly set on a group, it will show as the return value for who\_can\_post if archive\_only is true.

### Example
This example locks the announcements@acme.com group down to only accept posts from managers and owners.
```
gam update group announcements@acme.com who_can_post_message all_managers_can_post
```

---


## Who Can View Group
### Syntax
```
gam update group <group> who_can_view_group all_in_domain_can_view|all_managers_can_view|all_members_can_view|anyone_can_view
```
Determine who can view this group including past messages sent to the group if is\_archived is enabled. all\_in\_domain\_can\_view allows any Google Apps users in the domain to view the group. all\_managers\_can\_view limits viewing the group to owners and managers only. all\_members\_can\_view allows anyone who is a member of the group to view it. anyone\_can\_view allows anyone on the Internet to view the group.

### Example
This example sets membersonly@acme.com to only be viewable by members.
```
gam update group membersonly@acme.com who_can_view_group all_members_can_view
```

---


## Who Can View Membership
### Syntax
```
gam update group <group>  who_can_view_membership all_in_domain_can_view|all_managers_can_view|all_members_can_view
```
Determine who can view the list of group members. all\_in\_domain\_can\_view opens group membership lists to all Google Apps users in the domain. all\_managers\_can\_view limits group membership lists to group managers and owners. all\_members\_can\_view allows anyone who is a member of the group to see the member list.

### Example
This example locks down probation@acme.com so that only group managers can see who is a member of the group via the groups interface.
```
gam update group probation@acme.com who_can_view_membership all_managers_can_view
```

---


## Allow Google Communication
### Syntax
```
gam update group <group> allow_google_communication true|false
```
Determine if Google is allowed to send communications to group managers and owners. Occasionally Google may send updates on the latest features, ask for input on new features, or ask for permission to highlight your group. true allows this communication. false will prevent Google from ever sending these communications to the group.

### Example
This example prevents Google from directly contacting hr@acme.com managers and owners.
```
gam update group hr@acme.com allow_google_communication false
```

---


## Allow Web Posting
### Syntax
```
gam update group <group> allow_web_posting true|false
```
Determine if users are allowed to post to the group from the Google Groups web interface or via email only.

### Example
This example turns off web-based posting for the reports@acme.com group.
```
gam update group reports@acme.com allow_web_posting false
```

---


## Archive Only
### Syntax
```
gam update group <group> archive_only true|false
```
Determine if the group is limited to archival of old messages or if it is active. Setting archive only prevents new messages from going to the group.

### Example
This example puts legacy@acme.com into archive only mode.
```
gam update group legacy@acme.com archive_only true
```

---


## Custom Reply To
### Syntax
```
gam update group <group> custom_reply_to <email>
```
Sets the email address that will be used when reply\_to is set to reply\_to\_custom. When both settings are in place, this address will be the default reply to for messages sent to the group.

### Example
This example enables reply\_to\_custom for fanclub@acme.com and sets the custom\_reply\_to address to manager@acme.com
```
gam update group fanclub@acme.com reply_to reply_to_custom custom_reply_to manager@acme.com
```

---


## Is Archived
### Syntax
```
gam update group <group> is_archived true|false
```
Determines whether or not messages sent to the group should be archived and viewable in the Google Groups interface.

### Example
This example turns archiving off for the hr@acme.com group.
```
gam update group hr@acme.com is_archived false
```

---


## Max Message Bytes
### Syntax
```
gam update group <group> max_message_bytes <integer>
```
Determines the maximum size of a message sent to the group. Instead of entering a large number, K or M can be used to specify kilobytes or megabytes. For example, 512K or 1M would both be valid values.

### Example
This example sets Twitter-like size limits for the twitter@acme.com group. We bump it to 4 kilobytes instead of 160 bytes to account for message headers.
```
gam update group twitter@acme.com max_message_bytes 4K
```

---


## Members Can Post As The Group
### Syntax
```
gam update group <group> members_can_post_as_the_group true|false
```
Determines if members are allowed to send to the group using the group's email address as the From.

### Example
This example will allow sales@acme.com group members to send out messages to the group as sales@acme.com.
```
gam update group sales@acme.com members_can_post_as_the_group true
```

## Message Display Font
### Syntax
```
gam update group <group> message_display_font default_font|fixed_width_font
```
Sets the font that will be used in display group messages from the Google Groups UI. default\_font is the normal. fixed\_width\_font uses a special fixed-width font in the display.

### Example
This example turns on the fixed\_width\_font for the ascii-fun@acme.com group
```
gam update group ascii-fun@acme.com message_display_font fixed_width_font
```

---


## Description
### Syntax
```
gam update group <group> description <group description>
```
Change the group description. This is the same group description set by the [group provisioning GAM command](ExamplesProvisioning#Update_Group_Settings). This command exists only to allow changing the group description with the same API call while performing other Group Settings operations.

### Example
This example changes the party@acme.com group description to be "messages regarding upcoming parties"
```
gam update group party@acme.com description "messages regarding upcoming parties"
```

---


## Group Name
### Syntax
```
gam update group <group> name <new name>
```
Change the group name. This is the same group name set by the [group provisioning GAM command](ExamplesProvisioning#Update_Group_Settings). This command exists only to allow changing the group name with the same API call while performing other Group Settings operations.

### Example
This example changes the group name to "Acme Employees"
```
gam update group employees@acme.com name "Acme Employees"
```

---


## Spam Moderation Level
### Syntax
```
gam update group <group> spam_moderation_level allow|moderate|silently_moderate|reject
```
Change the spam moderation settings for the group. Allow will disable the spam filter and allow all mail from persons allowed to post to the group. moderate will place suspected spam messages in a moderation queue and notify group owners. silenty\_moderate will place suspected spam message in a moderation queue WITHOUT notifying group owners. reject will fail message delivery for messages suspected of being spam.

### Example
This example turns off spam filtering for the info@acmewidgets.com group
```
gam update group info@acmewidgets.com spam_moderation_level allow
```

---


## Include in Global Address List (GAL)
### Syntax
```
gam update group <group> include_in_global_address_list true|false
```
Include or remove this group's address from the Google Apps Global Address List (GAL). This setting is the group equivalent of the [Hide/Unhide user profile setting](ExamplesEmailSettings#Changing_a_users_profile_to_hidden/unhidden).  If a group is included (true), they'll show up in autocomplete and contact searches for addresses. If a group is not included (false), users will not be able to discover the groups's address and detailed contact info via autocomplete or contacts search.

**Note:** this setting and the [Show in Groups Directory](GAM3GroupSettings#show-in-groups-directory) setting are not the same. To hide a group completely you should set both to false.

### Example
This example hides the group topsecret@newwidgets.com from the Global Address List.
```
gam update group topsecret@newwidgets.com include_in_global_address_list false
```

---


## Who Can Leave Group
### Syntax
```
gam update group <group> who_can_leave_group NONE_CAN_LEAVE|ALL_MEMBERS_CAN_LEAVE|ALL_MANAGERS_CAN_LEAVE
```
Determines if regular users are allowed to leave a group. Setting this to ALL\_MANAGERS\_CAN\_LEAVE prevents regular members from unsubscribing to the group via the Web UI or email. Setting this to NONE\_CAN\_LEAVE prevents all members, including managers and owners, from unsubscribing to the group via the Web UI or email. Note that forcing a user to remain in a group increases the odds that they'll report your group mail as spam so it's strongly recommended to only use this setting for groups containing internal users only.

### Example
This example prevents regular users from leaving the everyone@acme.com group.
```
gam update group everyone@acme.com who_can_leave_group ALL_MANAGERS_CAN_LEAVE
```

---


## Who Can Contact Owner
### Syntax
```
gam update group <group> who_can_contact_owner ANYONE_CAN_CONTACT|ALL_IN_DOMAIN_CAN_CONTACT|ALL_MEMBERS_CAN_CONTACT|ALL_MANAGERS_CAN_CONTACT
```
Determines who is allowed to email the special group+owners@domain.com address in order to contact group owners.

### Example
This example prevents external email addresses from spamming helpdesk+owners@acme.com.
```
gam update group helpdesk@acme.com who_can_contact_owner ALL_IN_DOMAIN_CAN_CONTACT
```

---