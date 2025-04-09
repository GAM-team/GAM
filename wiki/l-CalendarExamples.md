- [Modifying and Viewing Calendar Access Control Lists (ACLs)](#modifying-and-viewing-calendar-access-control-lists-acls)
  - [Viewing a Calender's ACL](#viewing-a-calenders-acl)
  - [Adding Users to a Calendar's ACL](#adding-users-to-a-calendars-acl)
  - [Updating a User Entry in a Calendar ACL](#updating-a-user-entry-in-a-calendar-acl)
  - [Deleting Users from a Calendar's ACL](#deleting-users-from-a-calendars-acl)
- [Viewing and Modifying a User's List of Calendars](#viewing-and-modifying-a-users-list-of-calendars)
  - [Retrieving a Calendar a User Has Listed](#retrieving-a-calendar-a-user-has-listed)
  - [Showing the Calendars a User Has Listed](#showing-the-calendars-a-user-has-listed)
  - [Printing the Calendars a User Has Listed](#printing-the-calendars-a-user-has-listed)
  - [Deleting a Calendar from a User(s) List of Calendars](#deleting-a-calendar-from-a-users-list-of-calendars)
  - [Adding a Calendar to a User(s) List of Calendars](#adding-a-calendar-to-a-users-list-of-calendars)
  - [Updating a Calendar in a User(s) List of Calendars](#updating-a-calendar-in-a-users-list-of-calendars)
- [Deleting Events for a Calendar](#deleting-events-for-a-calendar)
- [Wiping a User's Primary Calendar](#wiping-a-users-primary-calendar)

GAM now supports Google Calendar Management with the ability to modify Access Control Lists (ACLs) for calendars and to add, list and remove calendars from a users Google Calendar display. GAM can work with user primary and secondary calendars as well as resource calendars.

All Google Calendars have an email address associated with them. All users who have the Calendar service enabled have a primary calendar identified by their email address. Secondary calendars created by or for the user have a special calendar email address which can be learned with the ` gam user <username> show calendars ` command. Resource Calendars also have a special email address that can be learned with the ` gam print resources ` command.

# Modifying and Viewing Calendar Access Control Lists (ACLs)
## Viewing a Calender's ACL
### Syntax
```
gam calendar <calendar email> showacl|printacl
```
Shows the ACLs for the given calendar (showacl) or prints CSV output of the ACLs (printacl). The ACL list will show who has access to the calendar and what level of access they have.

### Example
This example displays the Calendar ACLs for joe@acme.com
```
gam calendar joe@acme.com showacl
```

---


## Adding Users to a Calendar's ACL
### Syntax
```
gam calendar <calendar email> add freebusy|read|editor|owner <user email> [sendnotifications true|false]
```
Gives user email the desired level of access to the given calendar by adding the user to the ACL. freebusy allows the user to see only times whe n the calendar is busy without showing event details. read gives the user rights to view but not edit the calendar. editor gives read/write access to the calendar but not ACL or settings modification rights. owner gives the user full access to the calendar with the ability to modify the ACL and calendar settings.

Use the optional sendnotifications flag to choose whether to send notifications about the calendar sharing change or not. The default is True.

**Note:** The special users domain and default cannot be added to a calendar, they can only be updated or deleted by GAM (see below)

**Note:** giving a user rights to another calendar adds that calendar to their list of calendars automatically. A separate command to add the calendar should not be necessary. *Update*: this no longer seems to happen as of early 2020. You'll need to add the calendar to the user's list of calendar's separately.

### Example
This example gives Bob editor access to Joe's primary calendar.
```
gam calendar joe@acme.com add editor bob@acme.com
```

---


## Updating a User Entry in a Calendar ACL
### Syntax
```
gam calendar <calendar email> update freebusy|read|editor|owner <user email>
```
Update the given user's rights to the given calendar. The user should already have explicit access to the calendar. This command will upgrade (or downgrade) the user's access to the desired level of freebusy, read, editor or owner.

**Note:** the special users domain and default can be used instead of an actual user email address to modify public sharing of the calendar. domain applies to all users in the Google Apps organization. default applies to anyone with a Google account (even @gmail.com) and is limited to read or freebusy. Note that your Calendar control panel settings may prevent read sharing of calendars outside the domain in which case you'll get an error trying to set default to read.

### Example
This example upgrades Bob to be owner of Joe's Calendar:
```
gam calendar joe@acme.com update owner bob@acme.com
```

This example allows anyone with an account in your domain to edit the given resource calendar (including delete others appointments!).

```
gam calendar example.com_436d6e646572656e6365526f6f6d732d3239352d3372642d5164616d536d6974682d38@resource.calendar.google.com update editor domain
```

This example allows anyone with a Google account to view Bob's calendar
```
gam calendar bob@example.com update read default
```

---


## Deleting Users from a Calendar's ACL
### Syntax
```
gam calendar <calendar email> delete [user <user email>] [id <ACL id>]
```
Removes user email rights to the given calendar. Note that the user may still have some level of rights (freebusy or read) to the calendar based on the default level of access to calendars set within the domain. Specifying the ACL by ID is also supported and takes the id column of the [printacl command](#viewing-a-calenders-acl)

**Note:** deleting the domain and default users disables public sharing of your calendar. domain applies to everyone in your Google Apps domain while default applies to everyone with a Google Account.

### Example
This example removes Bob's direct rights to Joe's calendar
```
gam calendar joe@acme.com delete user bob@acme.com
```

These two examples remove all public sharing of Bob's calendar. Only those with explicit rights will be able to see anything (including freebusy):

```
gam calendar bob@example.com delete user domain
gam calendar bob@example.com delete user default
```

---


# Viewing and Modifying a User's List of Calendars
## Retrieving a Calendar a User Has Listed
### Syntax
```
gam user <user>|group <group>|ou <ou>|all users info calendar <calendar email>
```
Displays the details of the users' specific Calendar.

### Example
This example displays a specific calendar that Bob has added to his Google Calendar app
```
gam user bob@acme.com info calendar acme.com_r7vmefng3okeo4l48n4urkjvcg@group.calendar.google.com

User: bob@acme.com's Calendar:
  Calendar: test
    ID: acme.com_r7vmefng3okeo4l48n4urkjvcg@group.calendar.google.com
    Access Level: root
    Timezone: America/New_York
    Hidden: false
    Selected: true
    Color: #2952A3
```

## Showing the Calendars a User Has Listed
### Syntax
```
gam user <user>|group <group>|ou <ou>|all users show calendars
```
Displays the details of all of the Calendars the user has listed in their Google Calendar.

### Example
This example lists the calendars that Bob has added to his Google Calendar app
```
gam user bob@acme.com show calendars

User: bob@acme.com's Calendars
  Calendar: bob@acme.com
    ID: bob@acme.com
    Access Level: owner
    Timezone: America/New_York
    Hidden: false
    Selected: false
    Color: #2F6309
  Calendar: test
    ID: acme.com_r7vmefng3okeo4l48n4urkjvcg@group.calendar.google.com
    Access Level: root
    Timezone: America/New_York
    Hidden: false
    Selected: true
    Color: #2952A3
  Calendar: Canadian Holidays
    ID: en.canadian#holiday@group.v.calendar.google.com
    Access Level: read
    Timezone: America/New_York
    Hidden: false
    Selected: true
    Color: #2952A3
```

## Printing the Calendars a User Has Listed
### Syntax
```
gam user <user>|group <group>|ou <ou>|all users print calendars [todrive]
```
Display or upload to Google Drive a CSV report of all of the users' calendars. The optional `todrive` parameter specifies that the results should be uploaded to Google Drive rather than being displayed on screen or piped to a CSV text file. 

### Example
This example lists the calendars that all users have specified in the Calendar app.
```
gam all users print calendars
```

---


## Deleting a Calendar from a User(s) List of Calendars
### Syntax
```
gam user <user>|group <group>|ou <ou>|all users delete calendar <calendar email>
```
Removes the given calendar from each of the users' list of calendars. Deleting a calendar from a user's calendar list does not change ACLs on the calendar, it simply removes it from the display.

### Example
This example removes Joe's calendar from Bob's display of calendars.
```
gam user bob@acme.com delete calendar joe@acme.com
```

---


## Adding a Calendar to a User(s) List of Calendars
### Syntax
```
gam user <user>|group <group>|ou <ou>|all users add calendar <calendar email> [selected true|false] [hidden true|false] [reminder email|sms|popup <minutes>] [notification email|sms eventcreation|eventchange|eventcancellation|eventresponse|agenda] [summary <summary>] [colorindex <1-24>] [backgroundcolor <htmlcolor>] [foregroundcolor <htmlcolor>]
```
Adds the given calendar to each of the users' list of calendars. Adding a calendar to a user's calendar list does not give them any rights to the calendar that they didn't have before. If the user does not have rights to the calendar, use the ACL command above to both grant them rights and add the calendar to their list of calendars.

The optional argument `selected` determines if the calendar is selected in the user's list of subscribed calendars by default. The optional argument `hidden` determines if the calendar is hidden from the user's list of subscribed calendars. The optional argument `reminder` sets the default reminder type and time for calendar events and can be repeated. The optional argument `notification` sets the default notification type for calendar events and can be repeated. The optional argument `summary` overrides the calendar's default name. The optional argument `colorindex` sets the calendar entries colors. Index colors can be viewed [here](http://calendar-colors.appspot.com/). The optional arguments `backgroundcolor` and `foregroundcolor` manually set the calendars colors.

### Example
The following example adds Bob's calendar to Joe's list of calendars without it being selected in Joe's calendar display.

```
gam user joe@acme.com add calendar bob@acme.com selected false
```

---


## Updating a Calendar in a User(s) List of Calendars
### Syntax
```
gam user <user>|group <group>|ou <ou>|all users update calendar <calendar email> [selected true|false] [hidden true|false] [reminder (email|sms|popup <minutes>)|clear] [notification (email|sms eventcreation|eventchange|eventcancellation|eventresponse|agenda)|clear] [summary <summary>] [colorindex <1-24>] [backgroundcolor <htmlcolor>] [foregroundcolor <htmlcolor>]
```
Update how a given calendar is displayed in a user's list of calendars. The optional argument `selected` determines if the calendar is selected in the user's list of subscribed calendars by default. The optional argument `hidden` determines if the calendar is hidden from the user's list of subscribed calendars. The optional argument `reminder` sets the default reminder type and time for calendar events and can be repeated. The argument `reminder clear` clears all reminders from the calendar. The optional argument `notification` sets the default notification type for calendar events and can be repeated. The argument `notification clear` clears all notifications from the calendar. The optional argument `summary` overrides the calendar's default name. The optional argument `colorindex` sets the calendar entries colors. Index colors can be viewed [here](http://calendar-colors.appspot.com/). The optional arguments `backgroundcolor` and `foregroundcolor` manually set the calendars colors.

### Example
The following example updates Bob's view of Joe's calendars, changing the color to green.

```
gam user bob@acme.com update calendar joe@acme.com colorindex 9
```

---

# Deleting Events for a Calendar
### Syntax
```
gam calendar <email> deleteevent [eventid <id>] [query <query>] [notifyattendees] [doit]
```
Delete event(s) off the given calendar. You should specify either the single event ID with the eventid argument or a query to perform against the calendar to determine which events should be deleted. Query operates in a similar fashion to Calendar UIs search but you should test results carefully, a bad query can delete more events than you intended. The optional argument notifyattendees will send event attendees an email notification that the event is cancelled, removed. Because this command involves deletion of user data, GAM will not perform the action by default unless the doit argument is supplied.

# Wiping a User's Primary Calendar
### Syntax
```
gam calendar <user email> wipe
```
Wipe all data from a user's primary calendar. **WARNING: This will delete all user events and there is no way to recover them!** Email address must be a Google Apps user. It's not possible to wipe resource or secondary calendars.

### Example
The following example deletes all data for Joe's Calendar.

```
gam calendar joe@acme.com wipe
```

---