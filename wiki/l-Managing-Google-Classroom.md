- [Managing Courses](#managing-courses)
  - [Creating A Course](#creating-a-course)
  - [Updating A Course](#updating-a-course)
  - [Getting Course Info](#getting-course-info)
  - [Deleting A Course](#deleting-a-course)
- [Managing Course Aliases](#managing-course-aliases)
  - [Creating An Alias](#creating-an-alias)
  - [Deleting An Alias](#deleting-an-alias)
- [Managing Course Participants](#managing-course-participants)
  - [Adding Students And Teachers To A Course](#adding-students-and-teachers-to-a-course)
  - [Syncing Students And Teachers To A Course](#syncing-students-and-teachers-to-a-course)
  - [Removing Students And Teachers From A Course](#removing-students-and-teachers-from-a-course)
- [Managing Guardians](#managing-guardians)
  - [Inviting a guardian](#inviting-a-guardian)
  - [Deleting a guardian](#deleting-a-guardian)
  - [Printing Guardians](#printing-guardians)
- [Course And Course Participant Reports](#course-and-course-participant-reports)
  - [Printing Courses](#printing-courses)
  - [Printing Course Participants](#printing-course-participants)
- [Troubleshooting](#troubleshooting)
  - [403 Error](#403-error)

# Managing Courses
## Creating A Course
### Syntax
```
gam create course [alias <alias>] [name <name>] [section <section>] [heading <heading>] [description <description>] [room <room>] [teacher <teacher email>] [status <PROVISIONED|ACTIVE|ARCHIVED|DECLINED>]
```
Provision a new course. The optional alias parameter provides a unique id which can be used to reference the course. If a course already exists with this alias, an error will be thrown. If no alias is supplied, the course must be managed by the id that is assigned to it by Google when created. The optional name, section, heading, description and room parameters provide additional details for the course. The optional teacher parameter provides the email address of the owner / primary teacher of the course. If no teacher is provided then the admin user running GAM will be the owner / primary teacher of the course. The optional status parameter provides the initial status of the course when created. If no status is provided, courses default to PROVISIONED status.

### Example
This example creates a course.
```
gam create course alias the-republic-s01 name "The Republic" section s01 heading "The definition of justice (δικαιοσύνη), the order and character of the just city-state and the just man" room academy-01 teacher plato@athens.edu
```
----

## Updating A Course
### Syntax
```
gam update course <id or alias> [name <name>] [section <section>]
  [heading <heading>] [description <description>] [room <room>]
  [status <PROVISIONED|ACTIVE|ARCHIVED|DECLINED>]
  [owner <teacher email>]
```
Updates an existing course. The id or alias of the course is needed to identify the exact course to be updated. The optional name, section, heading, description and room parameters provide additional details for the course. The optional status parameter sets the status of the course. The optional owner argument sets a new owner teacher for the course. The owner email address must already be a teacher of the course and the old owner will remain a teacher of the course.

### Example
This example updates an existing course to make it active
```
gam update course the-republic-s01 status ACTIVE
```

This example sets a new owner for the course.
```
gam update course the-republic-s01 owner aristotle@athens.edu
```
----
## Getting Course Info
### Syntax
```
gam info course <id or alias>
```
Prints detailed information about a course.

### Example
This example prints information about the course
```
gam info course the-republic-s01
updateTime: 2015-07-01T13:47:20.000Z
room: academy-01
alternateLink: http://classroom.google.com/c/MtM0NzcxNDY5
enrollmentCode: 46rvtp
section: s01
creationTime: 2015-07-01T13:47:20.000Z
courseState: ACTIVE
ownerId: 102043113942954782808
id: 134781269
descriptionHeading: The definition of justice (δικαιοσύνη), the order and character of the just city-state and the just man
name: The Republic
Aliases:
  the-republic-s01
Participants:
 Teachers:
  Plato Plato - plato@athens.edu
 Students:
```
----

## Deleting A Course
### Syntax
```
gam delete course <id or alias>
```
Deletes the given course.

### Example
This example deletes the course
```
gam delete course the-republic-s01
```
----

# Managing Course Aliases
## Creating An Alias
### Syntax
```
gam course <id or alias> add alias <alias>
```
Create a new alias for an existing course.

### Example
This example creates an alias for a course which already has one alias.
```
gam course this-is-an-alias add alias this-is-another-alias
```
----

## Deleting An Alias
### Syntax
```
gam course <id or alias> delete alias <alias>
```
Delete an alias from an existing course.

### Example
This example deletes the alias from the add alias example above.
```
gam course this-is-an-alias delete alias this-is-another-alias
```
----

# Managing Course Participants
## Adding Students And Teachers To A Course
### Syntax
```
gam course <id or alias> add student|teacher <email address>
```
Add the given user email address to the course as a student or teacher.

### Example
This example adds Aristotle as a student in the course
```
gam course the-republic-s01 add student aristotle@athens.edu
```
----

## Syncing Students And Teachers To A Course
### Syntax
```
gam course <id or alias> sync students|teachers group <group email> | ou <orgunit> | file <filename> | query <users query> | course <id or alias>
```
Syncs the students or teachers for the given course against another list of users. Students/Teachers not in the other list will be removed from the given course. Students/Teachers in the other list but not the course will be added.

### Examples
This example adds all users in the Google Org Unit /schools/sunnybrook/K-1 into the course. If there are students in the course that are not in this OU, they will be removed.
```
gam course sunnybrook-k-1 sync students ou /schools/sunnybrook/K-1
```
This example syncs the course teachers against members of the biology-101-teachers@sunnybrook.edu group.
```
gam course biology-101-s01 sync teachers group biology-101-teachers@sunnybrook.edu
```
This example syncs course students against a CSV file
```
gam course history-200-s02 sync students file history-200-s02-students.csv
```
----

## Removing Students And Teachers From A Course
### Syntax
```
gam course <id or alias> remove student|teacher <email address>
```
removes the given email address from the course as a student or teacher.

### Example
This example removes John from the course.
```
gam course the-republic-s01 remove student john@athens.edu
```
----

# Managing Guardians
## Inviting a Guardian
### Syntax
```
gam create guardianinvite <guardian email> <student email>
```
Sends an email to the specified guardian email address inviting them to receive notifications for Classroom activities of given student email. The guardian email address can be any valid recipient but in order to accept the invitation the guardian must login or create a Google account. The guardian Google account does not need to be directly associated to the guardian email address.

Because this command sends out email notifications externally, it is recommended that plenty of internal testing is done with guardian invites before bulk inviting real guardians.

### Examples
This example invites moma.smith@hotmail.com as a guardian of johnny.smith@acme.edu
```
gam create guardianinvite moma.smith@hotmail.com johnny.smith@acme.edu
```
Assuming you have a csv file named parents.csv that looks like:
```
student-email,parent-email
johnny.smith@acme.edu,jonathan.t.smith@widgets.com
jane.smith@acme.edu,jonathan.t.smith@widgets.com
johnny.smith@acme.edu,judy.r.smith@gizmos.com
jane.smith@acme.edu,judy.r.smith@gizmos.com
george.johnson@acme.edu,johnson.fam.5@yahoo.com
```
this example bulk invites parents as guardians for their students.
```
gam csv parents.csv gam create guardianinvite ~parent-email ~student-email
```
----

## Delete a Guardian
### Syntax
```
gam delete guardian <guardian email> <student email>
```
Removes the given guardian as a guardian of the given student if guardian has accepted invitation and also cancels any pending invitations. The guardian will receive email notification that they have been removed as a guardian of the student.

### Examples
This example removes legal.guardian@yahoo.com as a guardian of johnny.smith@acme.edu or cancels any PENDING invitations
```
gam delete guardian legal.guardian@yahoo.com johnny.smith@acme.edu
```
----

## Printing Guardians
### Syntax
```
gam print guardians [invitations] [student <email>] [invitedguardian <email>] [user <username>|group <email>|ou <ouname>|all users] [states <COMPLETE,PENDING,GUARDIAN_INVITATION_STATE_UNSPECIFIED>] [todrive] [nocsv]
```
Prints a report of guardians. Currently you must specify a student or list of users for which to pull guardians. The optional argument invitations pulls information on guardian invitations instead of actual guardians who have been invited and accepted. Guardian invitations with a state of COMPLETE are no longer valid either because they've been accepted or rejected by the guardian, an admin has cancelled the invitation or the invitation has expired. The optional parameter student specifies the email address of a single student whose guardians or guardian invites should be pulled. The optional parameters user <email>, group <email>, ou <ouname> and all users specify a grouping of users whose guardians or guardian invites should be pulled. The optional argument states specifies a comma separated list of guardian invites that should be pulled based on their current state. The optional parameter todrive outputs the results to a Google Sheet instead of CSV. The optional parameter nocsv prints the guardians to the screen in a format that's human-eye friendly.

### Examples
This example creates a Google Sheet for all existing guardians. It makes one API call per user in the domain so may be very slow for large domains.
```
gam print guardians all users todrive
```
This example prints all guardian invitations that are still in a pending state for the /Students OU.
```
gam print guardians invitations states PENDING ou "/Students"
```
This example shows all of johnny.smith@acme.edu's current guardians.
```
gam print guardians student johnny.smith@acme.edu
```
----

# Course And Course Participant Reports
## Printing Courses
### Syntax
```
gam print courses [teacher <email>] [student <email>] [state <states>] [todrive] [aliases] [delimiter <String>]
```
Output CSV format details of courses. By default, all courses in the organization will be returned. The optional `teacher` and `student` parameters limit the results to courses where the given user is a participant in the course of the given type. The optional state parameter specifies a comma separated list of states (active, archived, provisioned, declined, suspended). Only courses in those states will be included in the results. The optional `todrive` argument creates a Google Drive spreadsheet of the results rather than outputting the information to the console. The optional `aliases` argument uses an additional API call per course to get the course aliases. By default, multiple aliases are delimited by spaces, if you would like a different delimiter, e.g., comma, use the `delimiter <String>` argument.

### Examples
This example creates a CSV file of all courses
```
gam print courses
```
this example creates a Google Spreadsheet of all the courses Mr. Smith is teaching
```
gam print courses teacher mrsmith@acme.edu todrive
```

this example limits the CSV output to provisioned and active courses
```
gam print courses state active,provisioned
```
----

## Printing Course Participants
### Syntax
```
gam print course-participants [course <id or alias>] [student <email>] [teacher <email>] [show teachers|students|all] [todrive]
```
Output CSV format details of course participants. The optional course parameter limits results to the given course. Multiple course parameters can be included to pull participants for a subset of courses. If no course parameter is specified then participants will be retrieved for all courses. The optional student and teacher parameters limit the courses returned to those where the given user is a teacher or student. The optional state parameter specifies a comma separated list of states (active, archived, provisioned, declined, suspended). Only courses in those states will be included in the results. The optional show parameter limits the participants to teachers or students, and defaults to all participants. The optional todrive argument creates a Google Drive spreadsheet of the results rather than outputting the information to the console.

### Examples
This example prints all course participants in all courses.
```
gam print course-participants
```
this example creates a spreadsheet of the course participants in all three sections of Chemistry.
```
gam print course-participants course chemistry-101-s01 course chemistry-101-s02 course chemistry-101-s03 todrive
```
this example creates a spreadsheet of only the course teachers in all three sections of Chemistry.
```
gam print course-participants course chemistry-101-s01 course chemistry-101-s02 course chemistry-101-s03 show teachers todrive
```
----
# Troubleshooting
## 403 Error
If you're using the default Super Admin account _(the very first account in your G Suite organization, that has all the permissions by default)_ you can get a `403: The caller does not have permission - 403 error`. In this case you have to create a new account, and assign Super Admin Role to it, and use that with gam. 
In addition, with the default Super Admin account, the `gam print courses` will not list all the courses in the organization.