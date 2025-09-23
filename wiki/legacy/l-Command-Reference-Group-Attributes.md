# GAM Group Attributes Command Reference

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

## gam create | update group [\<group email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#group-email) \<attributes/values\>

## where attributes and values are:
* allow_external_members
  * true|false
* message_moderation_level
  * moderate_all_messages |
  * moderate_new_members |
  * moderate_none |
  * moderate_non_members
* primary_language
  * \<language\>
* reply_to
  * reply_to_custom |
  * reply_to_ignore |
  * reply_to_list |
  * reply_to_managers |
  * reply_to_owner |
  * reply_to_sender
* send_message_deny_notification
  * true|false
* show_in_group_directory
  * true|false
* who_can_invite
  * all_managers_can_invite |
  * all_members_can_invite
* who_can_join
  * all_in_domain_can_join |
  * anyone_can_join |
  * can_request_to_join |
  * invited_can_join
* who_can_post_message
  * all_in_domain_can_post |
  * all_managers_can_post |
  * all_members_can_post |
  * anyone_can_post |
  * none_can_post
* who_can_view_group
  * all_in_domain_can_view |
  * all_managers_can_view |
  * all_members_can_view |
  * anyone_can_view
* who_can_view_membership
  * all_in_domain_can_view |
  * all_managers_can_view |
  * all_members_can_view
* allow_google_communication
  * true|false
* allow_web_posting
  * true|false
* archive_only
  * true|false
* custom_reply_to
  * \<email address\>
* is_archived
  * true|false
* max_message_bytes
  * \<integer\>
* members_can_post_as_the_group
  * true|false
* message_display_font
  * default_font |
  * fixed_width_font
* description
  * \<group description\>
* name
  * \<new name\>
* spam_moderation_level
  * allow |
  * moderate |
  * silently_moderate |
  * reject
* include_in_global_address_list
  * true|false
* who_can_leave_group
  * none_can_leave |
  * all_members_can_leave |
  * all_managers_can_leave
* who_can_contact_owner
  * anyone_can_contact |
  * all_in_domain_can_contact |
  * all_members_can_contact |
  * all_managers_can_contact
* who_can_discover_group
  * all_members_can_discover
  * all_in_domain_can_discover