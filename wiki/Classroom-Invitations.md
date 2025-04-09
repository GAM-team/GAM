# Classroom - Invitations
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Create classroom invitations](#create-classroom-invitations)
- [Accept classroom invitations by user](#accept-classroom-invitations-by-user)
- [Delete classroom invitations by user](#delete-classroom-invitations-by-user)
- [Display classroom invitations by user](#display-classroom-invitations-by-user)
- [Delete classroom invitations by course](#delete-classroom-invitations-by-course)
- [Display classroom invitations by course](#display-classroom-invitations-by-course)

## API documentation
* [Classroom API - Invitations](https://developers.google.com/classroom/reference/rest/v1/invitations)

## Notes

You must authorize an additional Service Account scope to use these commands.
Do this command; sustitute a valid email address for user@domain.com.
```
gam user user@domain.com update serviceaccount
```
You should enable:
```
[*] 17)  Classroom API - Rosters (supports readonly)
```
Follow the directions to authorize the Service Account scopes.

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<ClassroomInvitationID> ::= <String>
<ClassroomInvitationIDList> ::= "<ClassroomInvitationID>(,<ClassroomInvitationID>)*"
<ClassroomInvitationIDEntity> ::=
        <ClassroomInvitationIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseAlias> ::= <String>
<CourseID> ::= <Number>|d:<CourseAlias>
<CourseIDList> ::= "<CourseID>(,<CourseID>)*"
<CourseEntity> ::=
        <CourseIDList> | <FileSelector> | <CSVFileSelector | <CSVkmdSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseState> ::= active|archived|provisioned|declined|suspended
<CourseStateList> ::= all|"<CourseState>(,<CourseState>)*"
```
## Create classroom invitations
Invite users to classes.
```
gam <UserTypeEntity> create classroominvitation courses <CourseEntity> [role owner|student|teacher]
        [adminaccess|asadmin]
        [csv|csvformat] [todrive <ToDriveAttributes>*] [formatjson [quotechar <Character>]]
```
If `role` is not specified, `student` will be used.

You can only invite a co-teacher to be an owner of a course.

By default, classroom invitations are issued by the owner of the course, the `adminaccess` option causes the invitations to be issued by the admin named in `oauth2.txt`.

By default, when an invitation is created, GAM outputs details of the invitation as indented keywords and values.
* `csv|csvformat [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]` - Output the details in CSV format.

### Example

Suppose you have a CSV file CourseStudent.csv  with two columns: Course,Student.
This command will invite all students to their courses serially by student.
```
gam redirect stdout ./Invites.out redirect stderr stdout csvkmd users CourseStudent.csv keyfield Student datafield Course create classroominvitation role student course csvdata Course
```
This command will invite all students to their courses in parallel
```
gam redirect stdout ./Invites.out multiprocess redirect stderr stdout multiprocess csv CourseStudent.csv gam user "~Student" create classroominvitation role student course "~Course"
```
## Accept classroom invitations by user
Accept classroom invitations for users.
```
gam <UserTypeEntity> accept classroominvitation (ids <ClassroomInvitationIDEntity>)|([courses <CourseEntity>] [role all|owner|student|teacher])
```
`<UserTypeEntity>` must specify users in your domain.

By default, all invitations for the specified users will be accepted.

Select specific invitations to accept:
* `ids <ClassroomInvitationIDEntity>` - Specify invitation IDs

Select courses and accept invitations for those courses.
* `courses <CourseEntity>` - Specify courses

By default, invitations for all roles will be accepted; you can limit the acceptances to invitations of a specific role.

## Delete classroom invitations by user
Delete classroom invitations for users.
```
gam <UserTypeEntity> delete classroominvitation (ids <ClassroomInvitationIDEntity>)|([courses <CourseEntity>] [role all|owner|student|teacher])
```
`<UserTypeEntity>` must specify users in your domain.

By default, all invitations for the specified users will be deleted.

Select specific invitations to delete:
* `ids <ClassroomInvitationIDEntity>` - Specify invitation IDs

Select courses and delete invitations for those courses.
* `courses <CourseEntity>` - Specify courses

By default, invitations for all roles will be deleted; you can limit the deletions to invitations of a specific role.

## Display classroom invitations by user
Display classroom invitations for users.
```
gam <UserTypeEntity> show classroominvitations [role all|owner|student|teacher]
        [formatjson]
gam <UserTypeEntity> print classroominvitations [todrive <ToDriveAttributes>*] [role all|owner|student|teacher]
        [formatjson [quotechar <Character>]]
```
`<UserTypeEntity>` must specify users in your domain.

By default, invitations for all roles will be displayed; you can limit the display to invitations of a specific role.

## Delete classroom invitations by course
Delete classroom invitations for courses. This command must be used to delete non-domain member invitations.
```
gam delete classroominvitation courses <CourseEntity> (ids <ClassroomInvitationIDEntity>)|(role all|owner|student|teacher)
```
Select courses and delete invitations for those courses.
* `courses <CourseEntity>` - Specify courses

Select specific invitations to delete:
* `ids <ClassroomInvitationIDEntity>` - Specify invitation IDs

Select invitations to delete by role. By default, invitations for all roles will be deleted; you can limit the deletions to invitations of a specific role.

## Display classroom invitations by course
```
gam show classroominvitations (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        [role all|owner|student|teacher] [formatjson]
gam print classroominvitations [todrive <ToDriveAttributes>*] (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        [role all|owner|student|teacher] [formatjson [quotechar <Character>]]
```
By default, classroom invitations for all courses are displayed.

To get classroom invitations for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display classroom invitations from the courses with the IDs specified in `<CourseEntity>`.

To get classroom invitations for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get classroom invitations for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, for `show`, Gam displays the information as an indented list of keys and values.
* `formatjson` - Display the fields in JSON format.

By default, for `print`, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
