# Classroom - Membership
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Special quoting for course aliases](#special-quoting-for-course-aliases)
- [Manage membership for courses](#manage-membership-for-courses)
- [Legacy manage membership](#legacy-manage-membership)
- [Bulk membership changes](#bulk-membership-changes)
- [Display course membership](#display-course-membership)
- [Display course membership counts](#display-course-membership-counts)

## API documentation
* [Google Classroom API](https://developers.google.com/classroom/reference/rest)
* [Google Classroom API - Courses Students](https://developers.google.com/classroom/reference/rest/v1/courses.students)
* [Google Classroom API - Courses Teachers](https://developers.google.com/classroom/reference/rest/v1/courses.teachers)

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

## Manage membership for courses

These commands can process multiple courses and `add` and `delete` can process multiple students/teachers.
```
gam courses <CourseEntity> add teachers [makefirstteacherowner] <UserTypeEntity>
gam courses <CourseEntity> add students <UserTypeEntity>
gam courses <CourseEntity> delete|remove teachers|students <UserTypeEntity>
gam courses <CourseEntity> clear teachers|students
gam courses <CourseEntity> sync teachers [addonly|removeonly] [makefirstteacherowner] <UserTypeEntity>
gam courses <CourseEntity> sync students [addonly|removeonly] <UserTypeEntity>
```
When `makefirstteacherowner` is specified, the first/only user in `<UserTypeEntity>` will be updated to be the
owner of the Course(s).

### Clear
A `clear` operation deletes all of the members of the specified type. The owner teacher will not deleted.

### Sync
A `sync` operation gets the current roster for a course and compares it to the proposed roster.

Current/Default:
* members in the proposed roster that are not in the current roster will be added
* members in the current roster that are not in the proposed roster will deleted

When the `addonly` option is specified:
* members in the proposed roster that are not in the current roster will be added
* members in the current roster that are not in the proposed roster will not be deleted

When the `removeonly` option is specified:
* members in the proposed roster that are not in the current roster will not be added
* members in the current roster that are not in the proposed roster will be deleted

## Bulk membership changes
Suppose you have a CSV file (CourseStudents.csv) with headers: courseId,email

Each row contains a course ID and a student email address.

The following command will synchronize the membership for all courses.
```
gam redirect stdout ./CourseUpdates.txt redirect stderr stdout courses csvkmd CourseStudents.csv keyfield courseId datafield email sync students csvdata email
```
You can also do `add` and `delete` in this manner.

## Legacy manage membership

These commands are for backward compatibility; only one course can be processed and `add` and `delete` can only process a single student/teacher.
```
gam course <CourseID> add [makefirstteacherowner] teachers <UserItem>
gam course <CourseID> add students <UserItem>
gam course <CourseID> delete|remove teachers|students <UserItem>
gam course <CourseID> clear teachers|students
gam course <CourseID> sync teachers [addonly|removeonly] [makefirstteacherowner] <UserTypeEntity>
gam course <CourseID> sync students [addonly|removeonly] <UserTypeEntity>
```
When `makefirstteacherowner` is specified, the only/first user in `<UserItem>` or `<UserTypeEntity>` will be updated to be the
owner of the Course.

## Display course membership
```
gam print course-participants [todrive <ToDriveAttribute>*]
        (course|class <CourseID>)*|([teacher <UserItem>] [student <UserItem>]) [states <CourseStateList>]
        [show all|students|teachers] [formatjson [quotechar <Character>]]
```
By default, the `print course-participants` command displays participant information about all courses.

To get participant information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseID>)*` - Display courses with the specified `<CourseID>`.

To get participant information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get participant information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display course membership counts
Display the number of course participants.
```
gam print course-participants
        (course|class <CourseID>)*|([teacher <UserItem>] [student <UserItem>]) [states <CourseStateList>]
        [show all|students|teachers]
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
