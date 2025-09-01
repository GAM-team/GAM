# Classroom - Student Groups
- [Notes](#notes)
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Special quoting for course aliases](#special-quoting-for-course-aliases)
- [Manage student groups](#manage-student-groups)
- [Display student groups](#display-student-groups)
- [Display student group counts](#display-student-group-counts)
- [Manage student group membership](#manage-student-group-membership)
- [Display student group membership](#display-student-group-membership)
- [Display student group membership counts](#display-student-group-membership-counts)

## Notes
These commands wera added in version 7.20.00.

To use these commands your project must be enrolled the Developer Preview program.
* https://developers.google.com/workspace/preview

You will need your GAM project number.
* Login as an existing super admin at console.cloud.google.com
* In the upper left click the three lines to the left of Google Cloud and select IAM & Admin
* Under IAM & Admin select IAM
* Click in the box to the right of Google Cloud
* Click the three dots at the right and select Manage Resources
* Click the three dots at the end of the line for your GAM project
* Click Settings
* You will see the Project number; save it

You will need an API key
* In the upper left click the three lines to the left of Google Cloud and select APIs & Services
* Under APIs & Services select Credentials
* If you already have an API key, click Show key at the end of the line and save the value
* If you don't have an API key, click +Credentials and select API key
* Save the displayed API key
* Click close

Issue the following GAM command:
`gam config developer_preview_api_key <API Key Value> save`

Once you get an email from Google saying that your project has been registered you can use these commands.

## API documentation
* [Google Classroom API](https://developers.google.com/classroom/reference/rest)
* [Google Classroom Student Groups](https://developers.google.com/workspace/classroom/reference/rest/v1/courses.studentGroups)
* [Google Classroom Student Group Members](https://developers.google.com/workspace/classroom/reference/rest/v1/courses.studentGroups.studentGroupMembers)

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<CourseAlias> ::= <String>
<CourseID> ::= <Number>|d:<CourseAlias>
<CourseIDList> ::= "<CourseID>(,<CourseID>)*"
<CourseEntity> ::=
        <CourseIDList> | <FileSelector> | <CSVFileSelector | <CSVkmdSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseState> ::= active|archived|provisioned|declined|suspended
<CourseStateList> ::= all|"<CourseState>(,<CourseState>)*"

<StudentGroupID> ::= <Number>
<StudentGroupIDList> ::= "<StudentGroupID>(,<StudentGroupID>)*"
<StudentGroupEntity> ::=
        <StudentGroupIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector>
```
## Special quoting for course aliases
As course aliases can contain spaces, some care must be used when entering `<CourseAliasList>`, `<CourseID>`, `<CourseIDList>` and `<CourseEntity>`.

Suppose you have a course with the alias `Math Class`. To get information about it you enter the command: `gam info course "d:Math Class"`

The shell strips the `"` leaving a single argument `d:Math Class`; gam correctly processes the argument as it is expecting a single course.

Suppose you enter the command: `gam info courses "d:Math Class"`

The shell strips the `"` leaving a single argument `d:Math Class`; as gam is expecting a list, it splits the argument on space leaving two items and then tries to process `d:Math` and `Class`, not what you want.

You must enter: `gam info courses "'d:Math Class'"`

The shell strips the `"` leaving a single argument `'d:Math Class'`; as gam is expecting a list, it splits the argument on space while honoring the `'` leaving one item `d:Math Class` and correctly processes the item.

For multiple aliases you must enter: `gam info courses "'d:Math Class','d:Science Class'"`

See: [Lists and Collections](Lists-and-Collections)

## Manage student groups

```
gam create course-studentgroups
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        title <String>
        [csv [todrive <ToDriveAttribute>*] [formatjson [quotechar <Character>]]]
gam update course-studentgroups <CourseID> <StudentGroupID> title <String>
gam delete course-studentgroups <CourseID> <StudentGroupIDEntity>
gam clear course-studentgroups
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
```

The `update|delete course-studentgroups` commands manage a specific course.

By default, the `create|clear course-studentgroups` commands manage student group information about all courses.

To manage student group information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseID>)*` - Display courses with the specified `<CourseID>`.

To manage student group information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To manage student group information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

## Display student groups
```
gam print course-studentgroups [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        [formatjson [quotechar <Character>]]
```
By default, the `print course-studentgroups` command displays student group information about all courses.

To display student group information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseID>)*` - Display courses with the specified `<CourseID>`.

To display student group information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To display student group information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display student group counts
Display the number of student groups
```
gam print course-studentgroup [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        showitemcountonly
```

## Manage student group membership
```
gam create course-studentgroup-members <CourseID> <StudentGroupID> <UserTypeEntity>
gam delete course-studentgroup-members <CourseID> <StudentGroupID> <UserTypeEntity>
gam sync course-studentgroup-members <CourseID> <StudentGroupID> <UserTypeEntity>
gam clear course-studentgroupmembers <CourseID> <StudentGroupID>
```

# Display student group membership
```
gam print course-studentgroup-members [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        [formatjson [quotechar <Character>]]
```
By default, the `print course-studentgroup-members` command displays student group member information about all courses.

To display student group member information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseID>)*` - Display courses with the specified `<CourseID>`.

To display student group member information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To display student group member information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display student group membership counts
Display the number of student group members
```
gam print course-studentgroup-members [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        showitemcountonly
```
Example
```
$ gam print course-participants teacher asmith states active show students showitemcountonly
Getting all Courses that match query (Teacher: asmith@domain.com, Course State: ACTIVE), may take some time on a large Google Workspace Account...
Got 3 Courses...
Getting Students for Course: 636981507234 (1/3)
Got 30 Students...
Got 43 Students...
Getting Students for Course: 589346784341 (2/3)
Got 22 Students...
Getting Students for Course: 589345535881 (3/3)
Got 23 Students...
88
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print course-participants teacher asmith states active show students showitemcountonly)
Windows PowerShell
count = & gam print course-participants teacher asmith states active show students showitemcountonly
```
