# Classroom - Courses
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Special quoting for course aliases and topics](#special-quoting-for-course-aliases-and-topics)
- [Updating course owner](#updating-course-owner)
- [Create and update courses](#create-and-update-courses)
- [Delete courses](#delete-courses)
- [Manage course aliases](#manage-course-aliases)
- [Manage course topics](#manage-course-topics)
- [Display courses](#display-courses)
- [Display course counts](#display-course-counts)
- [Display course announcements](#display-course-announcements)
- [Display course materials](#display-course-materials)
- [Display course topics](#display-course-topics)
- [Display course work](#display-course-work)
- [Display course submissions](#display-course-submissions)

## API documentation
* [Google Classroom API](https://developers.google.com/classroom/reference/rest)
* [Google Classroom API - Courses Students](https://developers.google.com/classroom/reference/rest/v1/courses.students)
* [Google Classroom API - Courses Teachers](https://developers.google.com/classroom/reference/rest/v1/courses.teachers)
* [Google Classroom API - Announcements](https://developers.google.com/classroom/reference/rest/v1/courses.announcements/list)
* [Google Classroom API - Topics](https://developers.google.com/classroom/reference/rest/v1/courses.topics/list)
* [Google Classroom API - Course Work](https://developers.google.com/classroom/reference/rest/v1/courses.courseWork/list)
* [Google Classroom API - Course Work Materials](https://developers.google.com/classroom/reference/rest/v1/courses.courseWorkMaterials/list)
* [Google Classroom API - Course Work Student Submissions](https://developers.google.com/classroom/reference/rest/v1/courses.courseWork.studentSubmissions/list)

## Notes
In this document, `course materials` refers to stand-alone materials, not the materials associated with
`course announcements` or `course work`. Google added support for stand-alone materials in early 2021.

To use the course materials features you must authorize the appropriate scope: `Classroom API - Course Work/Materials`.
```
gam oauth create
gam user user@domain.com check|update serviceaccount
```

## Definitions
```
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
<UniqueID> ::= id:<String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>

<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<CourseAlias> ::= <String>
<CourseAliasList> ::= "<CourseAlias>(,<CourseAlias>)*"
<CourseAliasEntity> ::=
        <CourseAliasList>|<FileSelector>|<CSVFileSelector>|<CSVkmdSelector>|<CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseAnnouncementID> ::= <Number>
<CourseAnnouncementIDList> ::= "<CourseAnnouncementID>(,<CourseAnnouncementID>)*"
<CourseAnnouncementIDEntity> ::=
        <CourseAnnouncementIDList>|<FileSelector>|<CSVFileSelector>|<CSVkmdSelector>|<CSVSubkeySelector>|<CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseAnnouncementState> ::= draft|published|deleted
<CourseAnnouncementStateList> ::= all|"<CourseAnnouncementState>(,<CourseAnnouncementState>)*"
<CourseID> ::= <Number>|d:<CourseAlias>
<CourseIDList> ::= "<CourseID>(,<CourseID>)*"
<CourseEntity> ::=
        <CourseIDList>|<FileSelector>|<CSVFileSelector>|<CSVkmdSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseMaterialID> ::= <Number>
<CourseMaterialIDList> ::= "<CourseMaterialID>(,<CourseMaterialID>)*"
<CourseMaterialState> ::= draft|published|deleted
<CourseMaterialStateList> ::= all|"<CourseMaterialState>(,<CourseMaterialState>)*"
<CourseMaterialIDEntity> ::=
        <CourseMaterialIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVSubkeySelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseState> ::= active|archived|provisioned|declined|suspended
<CourseStateList> ::= all|"<CourseState>(,<CourseState>)*"
<CourseSubmissionID> ::= <Number>
<CourseSubmissionIDList> ::= "<CourseSubmissionID>(,<CourseSubmissionID>)*"
<CourseSubmissionIDEntity> ::=
        <CourseSubmissionIDList>|<FileSelector>|<CSVFileSelector>|<CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseSubmissionState> ::= new|created|turned_in|returned|reclaimed_by_student
<CourseSubmissionStateList> ::= all|"<CourseSubmissionState>(,<CourseSubmissionState>)*"
<CourseTopic> ::= <String>
<CourseTopicList> ::= "<CourseTopic>(,<CourseTopic>)*"
<CourseTopicEntity> ::=
        <CourseTopicList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseTopicID> ::= <Number>
<CourseTopicIDList> ::= "<CourseTopicID>(,<CourseTopicID>)*"
<CourseTopicIDEntity> ::=
        <CourseTopicIDList>|<FileSelector>|<CSVFileSelector>|<CSVkmdSelector>|<CSVSubkeySelector>|<CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseWorkID> ::= <Number>
<CourseWorkIDList> ::= "<CourseWorkID>(,<CourseWorkID>)*"
<CourseWorkIDEntity> ::=
        <CourseWorkIDList>|<FileSelector>|<CSVFileSelector>|<CSVkmdSelector>|<CSVSubkeySelector>|<CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<CourseWorkState> ::= draft|published|deleted
<CourseWorkStateList> ::= all|"<CourseWorkState>(,<CourseWorkState>)*"

<CourseAttribute> ::=
        (description <String>)|
        (descriptionheading|heading <String>)|
        (name <String>)|
        (room <String>)|
        (section <string>)|
        (state|status <CourseState>)|
        (owner|ownerid|teacher <UserItem>)

<CourseFieldName> ::=
        alternatelink|
        coursegroupemail|
        coursematerialsets|
        coursestate|
        creationtime|
        description|
        descriptionheading|heading|
        enrollmentcode|
        gradebooksettings|
        guardiansenabled|
        id|
        name|
        owneremail|
        ownerid|
        room|
        section|
        teacherfolder|
        teachergroupemail|
        updatetime
<CourseFieldNameList> ::= '<CourseFieldName>(,<CourseFieldName>)*'

<CourseAnnouncementFieldName> ::=
        alternatelink|
        assigneemode|
        courseid|
        courseannouncementid|
        creationtime|
        creator|creatoruserid|
        id|
        individualstudentsoptions|
        materials|
        scheduledtime|
        state|
        text|
        updatetime
<CourseAnnouncementFieldNameList> ::= "<CourseAnnouncementFieldName>(,<CourseAnnouncementFieldName>)*"

<CourseAnnouncementOrderByFieldName> ::=
        updatetime|
        updatedate

<CourseMaterialFieldName> ::=
        alternatelink|
        assigneemode|
        courseid|
        courseworkmaterialid|
        creationtime|
        creator|creatoruserid|
        description|
        id|
        individualstudentsoptions|
        materials|
        scheduledtime|
        state|
        title|
        topicid|
        updatetime|
        workmaterialid
<CourseMaterialFieldNameList> ::= "<CourseMaterialFieldName>(,<CourseMaterialFieldName>)*"

<CourseMaterialOrderByFieldName> ::=
        updatetime|
        updatedate

<CourseWorkFieldName> ::=
        alternatelink|
        assigneemode|
        courseid|
        courseworkid|
        courseworktype|
        creationtime|
        creator|creatoruserid|
        description|
        duedate|
        duetime|
        id|
        individualstudentsoptions|
        materials|
        maxpoints|
        scheduledtime|
        state|
        submissionmodificationmode|
        title|
        topicid|
        updatetime|
        workid|
        worktype
<CourseWorkFieldNameList> ::= "<CourseWorkFieldName>(,<CourseWorkFieldName>)*"

<CourseWorkOrderByFieldName> ::=
        duedate|
        updatetime|
        updatedate

<CourseSubmissionFieldName> ::=
        alternatelink|
        assignedgrade|
        courseid|
        courseworkid|
        courseworktype|
        creationtime|
        draftgrade|
        id|
        late|
        state|
        submissionhistory|
        updatetime|
        userid|
        worktype
<CourseSubmissionFieldNameList> ::= "<CourseSubmissionFieldName>(,<CourseSubmissionFieldName>)*"
```
## Special quoting for course aliases and topics
As course aliases and topics can contain spaces, some care must be used when entering `<CourseAliasList>` and `<CourseTopicList>`.

Suppose you have a course with the alias `Math Class`. To get information about it you enter the command: `gam info course "d:Math Class"`

The shell strips the `"` leaving a single argument `d:Math Class`; gam correctly processes the argument as it is expecting a single course.

Suppose you enter the command: `gam info courses "d:Math Class"`

The shell strips the `"` leaving a single argument `d:Math Class`; as gam is expecting a list, it splits the argument on space leaving two items and then tries to process `d:Math` and `Class`, not what you want.

You must enter: `gam info courses "'d:Math Class'"`

The shell strips the `"` leaving a single argument `'d:Math Class'`; as gam is expecting a list, it splits the argument on space while honoring the `'` leaving one item `d:Math Class` and correctly processes the item.

For multiple aliases you must enter: `gam info courses "'d:Math Class','d:Science Class'"`

See: [Lists and Collections](Lists-and-Collections)

## Updating course owner
When updating a course owner, the Classroom API generates an error if the new owner is not a co-teacher
or is the current owner.

If `<UserItem>` is not a co-teacher, GAM adds `<UserItem>` as a co-teacher of the course,
pauses 10 seconds, and then updates them to be the owner.
```
$ gam update course 123929046789 teacher newteacher@domain.com
Course Name: Test, Course: 123929046789, Updated with new teacher as owner: newteacher@domain.com
```

If `<UserItem>` is the current owner, GAM now reports that the current owner was retained.
```
$ gam update course 123929046789 teacher newteacher@domain.com
Course Name: Test, Course: 123929046789, Updated with current owner: newteacher@domain.com
```

In the normal case when `<UserItem>` is a co-teacher, GAM now reports the change.
```
$ gam update course 123929046789 teacher newteacher@domain.com
Course Name: Test, Course: 123929046789, Updated with co-teacher as owner: newteacher@domain.com
```

## Create and update courses
The options `name <String>` and `teacher <UserItem>` are required when creating a class.
```
gam create|add course [id|alias <CourseAlias>] <CourseAttribute>*
        [copyfrom <CourseID>
            [announcementstates <CourseAnnouncementStateList>]
                [individualstudentannouncements copy|delete|maptoall]
            [materialstates <CourseMaterialStateList>]
                [individualstudentmaterials copy|delete|maptoall]
            [workstates <CourseWorkStateList>]
                [individualstudentcoursework copy|delete|maptoall]
                [removeduedate [<Boolean>]]
                [mapsharemodestudentcopy edit|none|view]
            [individualstudentassignments copy|delete|maptoall]
            [copymaterialsfiles [<Boolean>]]
            [copytopics [<Boolean>]]
            [markdraftaspublished [<Boolean>]]
            [markpublishedasdraft [<Boolean>]]
            [members none|all|students|teachers]]
            [logdrivefileids [<Boolean>]]

gam update course <CourseID> <CourseAttribute>+
        [copyfrom <CourseID>
            [announcementstates <CourseAnnouncementStateList>]
                [individualstudentannouncements copy|delete|maptoall]
            [materialstates <CourseMaterialStateList>]
                [individualstudentmaterials copy|delete|maptoall]
            [workstates <CourseWorkStateList>]
                [individualstudentcoursework copy|delete|maptoall]
                [removeduedate [<Boolean>]]
                [mapsharemodestudentcopy edit|none|view]
            [individualstudentassignments copy|delete|maptoall]
            [copymaterialsfiles [<Boolean>]]
            [copytopics [<Boolean>]]
            [markdraftaspublished [<Boolean>]]
            [markpublishedasdraft [<Boolean>]]
            [members none|all|students|teachers]]
            [logdrivefileids [<Boolean>]]
gam update courses <CourseEntity> <CourseAttribute>+
        [copyfrom <CourseID>
            [announcementstates <CourseAnnouncementStateList>]
                [individualstudentannouncements copy|delete|maptoall]
            [materialstates <CourseMaterialStateList>]
                [individualstudentmaterials copy|delete|maptoall]
            [workstates <CourseWorkStateList>]
                [individualstudentcoursework copy|delete|maptoall]
                [removeduedate [<Boolean>]]
                [mapsharemodestudentcopy edit|none|view]
            [individualstudentassignments copy|delete|maptoall]
            [copymaterialsfiles [<Boolean>]]
            [copytopics [<Boolean>]]
            [markdraftaspublished [<Boolean>]]
            [markpublishedasdraft [<Boolean>]]
            [members none|all|students|teachers]]
            [logdrivefileids [<Boolean>]]
```
`copyfrom <CourseID>` allows copying of course announcements, work, topics and members from one course to another.
* Accouncements - By default, no course announcements are copied
    * `announcementstates <CourseAnnouncementStateList>` - Copy class announcements with the specified states
        * `individualstudentannouncements copy` - Copy individual student announcements; this is the default. You will get an error if a student is not a member of the course
        * `individualstudentannouncements delete` - Delete individual student announcements
        * `individualstudentannouncements maptoall` - Map individual student announcements to all student announcements
* Materials - By default, no course materials are copied
    * `materialstates <CourseMaterialsStateList>` - Copy class materials with the specified states
        * `individualstudentmaterials copy` - Copy individual student materials; this is the default. You will get an error if a student is not a member of the course
        * `individualstudentmaterials delete` - Delete individual student materials
        * `individualstudentmaterials maptoall` - Map individual student materials to all student materials
* Work - By default, no course work is copied
    * `workstates <CourseWorkStateList>` - Copy class work with the specified states
        * `individualstudentcoursework copy` - Copy individual student coursework; this is the default. You will get an error if the student is not a member of the course
        * `individualstudentcoursework delete` - Delete individual student coursework
        * `individualstudentcoursework maptoall` - Map individual student coursework to all student coursework
        * `removeduedate false` - Remove due dates before the current time; this is the default
        * `removeduedate|removeduedate true` - Remove all due dates
* For convenience, setting `individualstudentassignments` sets all the following to the same value:
    * `individualstudentannouncements`
    * `individualstudentmaterials`
    * `individualstudentcoursework`
* Announcements, Materials and Work Materials files
    * `copymaterialsfiles false` - Copy links to files referenced by materials in the `copyfrom` course; this is the default
    * `copymaterialsfiles|copymaterialsfiles true` - Copy files referenced by materials in the `copyfrom` course
        * You must verify that the teacher of the course being created/updated has access to the files in the `copyfrom` course
        * Files can only be copied to a course that is ACTIVE; GAM will adjust the course state as necessary
* Topics - By default, no course topics are copied; if topics are not copied, references to them will be deleted from class work that is copied
    * `copytopics false` - No course topics are copies
    * `copytopics|copytopics true` - Copy topics
* Published Material and Work - By default, published material and work is not relabeled
    * `markdraftaspublished false` - Do not relabel draft material/work as published; this is the default
    * `markdraftaspublished|markpublishedasdraft true` - Relabel draft material/work as published
    * `markpublishedasdraft false` - Do not relabel published material/work as draft; this is the default
    * `markpublishedasdraft|markpublishedasdraft true` - Relabel published material/work as draft
* Members - By default, no course members are copied
    * `members none` - No course members are copied
    * `members all` - Copy course students and teachers
    * `members students` - Copy students
    * `members teachers` - Copy teachers

When true, `logdrivefileids [<Boolean>]` generates a CSV file with headers `courseId,ownerId,fileId' that
lists all drive files in the course.

The Classroom API does not support course materials of type `form`, they will not be copied.

Drive files with `shareMode` `Each student will get a copy` don't seem to be able to be copied.
  * `mapsharemodestudentcopy edit` - Map `Each student will get a copy` to `Students can edit file`
  * `mapsharemodestudentcopy view` - Map `Each student will get a copy` to `Students can view file`
  * `mapsharemodestudentcopy none` or not specified - No `shareMode` mapping is performed, you may get an error

## Delete courses
Classes can only be deleted when they are in the ARCHIVED state; to delete a class, you can update its state to ARCHIVED
and then delete it or you can specify that it be archived as parot of the delete command.
```
gam delete course <CourseID> [archived]
gam delete courses <CourseEntity> [archived]
```
## Manage course aliases
These commands can process a single course.
```
gam course <CourseID> add alias <CourseAlias>
gam course <CourseID> delete alias <CourseAlias>
```
These commands can process multiple courses.
```
gam courses <CourseEntity> add alias <CourseAliasEntity>
gam courses <CourseEntity> delete alias <CourseAliasEntity>
```
## Manage course topics
These commands can process a single course.
```
gam course <CourseID> add topic <CourseTopic>
gam course <CourseID> delete topic <CourseTopicID>
```
These commands can process multiple courses.
```
gam courses <CourseEntity> add topic <CourseTopicEntity>
gam courses <CourseEntity> delete topic <CourseTopicIDEntity>
```
## Display courses
```
gam info course <CourseID> [owneremail] [alias|aliases] [show all|students|teachers] [countsonly]
        [fields <CourseFieldNameList>] [skipfields <CourseFieldNameList>] [formatjson]
gam info courses <CourseEntity> [owneremail] [alias|aliases] [show all|students|teachers] [countsonly]
        [fields <CourseFieldNameList>] [skipfields <CourseFieldNameList>] [formatjson]

gam print courses [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        [owneremail] [owneremailmatchpattern <REMatchPattern>]
        [alias|aliases|aliasesincolumns [delimiter <Character>]]
        [show all|students|teachers] [countsonly]
        [fields <CourseFieldNameList>] [skipfields <CourseFieldNameList>] [formatjson [quotechar <Character>]]
        [timefilter creationtime|updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
```
By default, the `print courses` command displays information about all courses.

To get information about a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display courses with the IDs specified in `<CourseEntity>`.

To get information about courses based on its owner's emailaddress, use the `owneremailmatchpattern <REMatchPattern>` option.
* `foo@bar.com` - Display courses with a specific owner emailaddress.
* `.*test.*` - Display courses with an owner emailaddress that matches a pattern.
* `Unknown user` - Display courses where the owner emailaddress has been deleted.

To get information about courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get information about courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

To get information about courses created/updated within a particular time frame, use the following options.
* `timefilter creationtime|updatetime` - select which event to filter
* `start|starttime <Date>|<Time>` - specify the start of the time frame; if not specified, the time frame will be open ended at the start
* `end|endtime <Date>|<Time>` - specify the end of the time frame; if not specified, the time frame will be open ended at the end
For the filter to apply, `timefilter` and at least one of `start|starttime` and `end|endtime` must be specified.

By default, all basic course fields are displayed; use the following options to modify the output.
* `owneremail` - Display course owner email; requires an additional API call per course.
* `alias|aliases` - Display course aliases; all aliases are in the single column `Aliases` separated by a delimiter; requires an additional API call per course.
    * `delimiter <Character>` - Delimiter between aliases with `print` command.
* `aliasesincolumn` - Display course aliases; the `Aliases` column contains the number of aliases and `Aliases.0`, `Aliases.1`, ... contain the individual aliases; requires an additional API call per course.
* `show all|students|teachers` - Show class participants profile information; requires an additional API call per course.
    * `countsonly` - Eliminates the student/teacher profile information and outputs only the student/teacher counts.
* `fields <CourseFieldNameList>` - Select specific basic fields to display.
* `skipfields <CourseFieldNameList>` - Select specific basic fields to eliminate from display; typically used with `coursematerialsets`.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display course counts
Display the number of courses.
```
gam print courses
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] [states <CourseStateList>])
        [owneremailmatchpattern <REMatchPattern>]
        showitemcountonly
```
Example
```
$ gam print courses states active showitemcountonly
Getting all Courses that match query (Course State: ACTIVE), may take some time on a large Google Workspace Account...
Got 268 Courses...
Got 272 Courses...
Got 272 Courses...
272
```
The `Getting` and `Got` messages are written to stderr, the count is writtem to stdout.

To retrieve the count with `showitemcountonly`:
```
Linux/MacOS
count=$(gam print courses states active showitemcountonly)
Windows PowerShell
count = & gam print courses states active showitemcountonly
```

## Display course announcements
```
gam print course-announcements [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
        (courseannouncementids <CourseAnnouncementIDEntity>)|(announcementstates <CourseAnnouncementStateList>)*
        (orderby <CourseAnnouncementOrderByFieldName> [ascending|descending])*)
        [creatoremail] [fields <CourseAnnouncementFieldNameList>]
        [timefilter creationtime|updatetime|scheduledtime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [countsonly] [formatjson [quotechar <Character>]]
```
By default, the `print course-announcements` command displays course announcement information for all courses.

To get course announcements for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display courses with the IDs specified in `<CourseEntity>`.

To get course announcements for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get course announcements for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, all published course announcements for a course are displayed; use the following options to select specific course announcements.
* `courseannouncementids <CourseAnnouncementIDEntity>` - Display course announcements with the IDs specified in `<CourseAnnouncementIDEntity>`.
* `announcementstates <CourseAnnouncementStateList>` - Display course announcements with any of the specified states.

To get information about course announcements created/updated/scheduled within a particular time frame, use the following options.
* `timefilter creationtime|updatetime|scheduledtime` - select which event to filter
* `start|starttime <Date>|<Time>` - specify the start of the time frame; if not specified, the time frame will be open ended at the start
* `end|endtime <Date>|<Time>` - specify the end of the time frame; if not specified, the time frame will be open ended at the end
For the filter to apply, `timefilter` and at least one of `start|starttime` and `end|endtime` must be specified.

By default, all course announcement fields are displayed; use the following options to modify the output.
* `creatoremail` - Display course announcement creator email; requires an additional API call per course announcement.
* `fields <CourseAnnouncementFieldNameList>` - Select specific fields to display.

Use the `countsonly` option to display the number of announcements in a course but not their details.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display course materials
```
gam print course-materials [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
        (materialids <CourseMaterialIDEntity>)|(materialstates <CourseMaterialStateList>)*
        (orderby <CourseMaterialOrderByFieldName> [ascending|descending])*)
        [showcreatoremails|creatoremail] [showtopicnames] [fields <CourseMaterialFieldNameList>]
        [timefilter creationtime|updatetime|scheduledtime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [countsonly] [formatjson [quotechar <Character>]]
```
By default, the `print course-materials` command displays course materials information for all courses.

To get course materials information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display courses with the IDs specified in `<CourseEntity>`.

To get course materials information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get course materials information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

To get information about course materials created/updated/scheduled within a particular time frame, use the following options.
* `timefilter creationtime|updatetime|scheduledtime` - select which event to filter
* `start|starttime <Date>|<Time>` - specify the start of the time frame; if not specified, the time frame will be open ended at the start
* `end|endtime <Date>|<Time>` - specify the end of the time frame; if not specified, the time frame will be open ended at the end
For the filter to apply, `timefilter` and at least one of `start|starttime` and `end|endtime` must be specified.

By default, all published course materials for a course are displayed; use the following options to select specific course materials.
* `materialsids <CourseMaterialsIDEntity>` - Display course materials with the IDs specified in `<CourseMaterialsIDEntity>`.
* `materialsstates <CourseMaterialsStateList>` - Display course materials with any of the specified states.

By default, all course materials fields are displayed; use the following options to modify the output.
* `showcreatoremails` - Display course materials creator email; requires an additional API call per course materials.
* `showtopicnames` - Display topic names; requires and additional API call per course.
* `fields <CourseMaterialsFieldNameList>` - Select specific fields to display.

Use the `countsonly` option to display the number of course materials in a course but not their details.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display course topics
```
gam print course-topics [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
        (coursetopicids <CourseTopicIDEntity>)
        [timefilter updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [countsonly] [formatjson [quotechar <Character>]]
```
By default, the `print course-topics` command displays course topic information for all courses.

To get course topics for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display courses with the IDs specified in `<CourseEntity>`.

To get course topics for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get course topics for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, all published course topics for a course are displayed; use the following options to select specific course topics.
* `coursetopicids <CourseTopicIDEntity>` - Display course topics with the IDs specified in `<CourseTopicIDEntity>`.
* `topicstates <CourseTopicStateList>` - Display course topics with any of the specified states.

To get information about course topics updated within a particular time frame, use the following options.
* `timefilter updatetime` - select which event to filter
* `start|starttime <Date>|<Time>` - specify the start of the time frame; if not specified, the time frame will be open ended at the start
* `end|endtime <Date>|<Time>` - specify the end of the time frame; if not specified, the time frame will be open ended at the end
For the filter to apply, `timefilter` and at least one of `start|starttime` and `end|endtime` must be specified.

Use the `countsonly` option to display the number of topics in a course but not their details.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display course work
```
gam print course-work [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
        (workids <CourseWorkIDEntity>)|(workstates <CourseWorkStateList>)*
        (orderby <CourseWorkOrderByFieldName> [ascending|descending])*)
        [showcreatoremails] [showtopicnames] [fields <CourseWorkFieldNameList>]
        [showstudentsaslist [<Boolean>]] [delimiter <Character>]
        [timefilter creationtime|updatetime|scheduledtime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [countsonly] [formatjson [quotechar <Character>]]
```
By default, the `print course-work` command displays course work information for all courses.

To get course work information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display courses with the IDs specified in `<CourseEntity>`.

To get course work information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get course work information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

To get information about course work created/updated/scheduled within a particular time frame, use the following options.
* `timefilter creationtime|updatetime|scheduledtime` - select which event to filter
* `start|starttime <Date>|<Time>` - specify the start of the time frame; if not specified, the time frame will be open ended at the start
* `end|endtime <Date>|<Time>` - specify the end of the time frame; if not specified, the time frame will be open ended at the end
For the filter to apply, `timefilter` and at least one of `start|starttime` and `end|endtime` must be specified.

By default, all published course work for a course is displayed; use the following options to select specific course work.
* `workids <CourseWorkIDEntity>` - Display course work with the IDs specified in `<CourseWorkIDEntity>`.
* `workstates <CourseWorkStateList>` - Display course work with any of the specified states.

By default, all course work fields are displayed; use the following options to modify the output.
* `showcreatoremails` - Display course work creator email; requires an additional API call per course work.
* `showtopicnames` - Display topic names; requires and additional API call per course.
* `fields <CourseWorkFieldNameList>` - Select specific fields to display.

By default, when course work is assigned to individual students, the student IDs are displayed in multiple indexed columns.
Use options `showstudentsaslist [<Boolean>]` and `delimiter <Character>` to display the student IDs is a single column as a delimited list.

Use the `countsonly` option to display the number of course works in a course but not their details.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Display course submissions
```
gam print course-submissions [todrive <ToDriveAttribute>*]
        (course|class <CourseEntity>)*|([teacher <UserItem>] [student <UserItem>] states <CourseStateList>])
        (workids <CourseWorkIDEntity>)|(workstates <CourseWorkStateList>)*
        (orderby <CourseWorkOrderByFieldName> [ascending|descending])*)
        (submissionids <CourseSubmissionIDEntity>)|(submissionstates <CourseSubmissionStateList>)*) [late|notlate]
        [fields <CourseSubmissionFieldNameList>] [showuserprofile]
        [timefilter creationtime|updatetime] [start|starttime <Date>|<Time>] [end|endtime <Date>|<Time>]
        [countsonly] [formatjson [quotechar <Character>]]
```
By default, the `print course-submissions` command displays course submission information for all course work for all courses.

To get course submission information for a specific set of courses, use the following option; it can be repeated to select multiple courses.
* `(course|class <CourseEntity>)*` - Display courses with the IDs specified in `<CourseEntity>`.

To get course submission information for courses based on their having a particular participant, use the following options. Both options can be specified.
* `teacher <UserItem>` - Display courses with the specified teacher.
* `student <UserItem>` - Display courses with the specified student.

To get course submission information for courses based on their state, use the following option. This option can be combined with the `teacher` and `student` options.
By default, all course states are selected.
* `states <CourseStateList>` - Display courses with any of the specified states.

By default, all course work for a course is displayed; use the following options to select specific course work.
* `workids <CourseWorkIDEntity>` - Display course work with the IDs specified in `<CourseWorkIDEntity>`.
* `workstates <CourseWorkStateList>` - Display course work with any of the specified states.

By default, all course submissions for a course work is displayed; use the following options to select specific course submissions.
* `submissionids <CourseSubmissionIDEntity>` - Display course submissions with the IDs specified in `<CourseSubmissionIDEntity>`.
* `submissionstates <CourseSubmissionStateList>` - Display course submissions with any of the specified states.
* `late` - Display course submissions marked late.
* `notlate` - Display course submissions not marked late.

To get information about course submissions created/updated within a particular time frame, use the following options.
* `timefilter creationtime|updatetime` - select which event to filter
* `start|starttime <Date>|<Time>` - specify the start of the time frame; if not specified, the time frame will be open ended at the start
* `end|endtime <Date>|<Time>` - specify the end of the time frame; if not specified, the time frame will be open ended at the end
For the filter to apply, `timefilter` and at least one of `start|starttime` and `end|endtime` must be specified.

By default, all course submission fields are displayed; use the following options to modify the output.
* `fields <CourseSubmissionFieldNameList>` - Select specific fields to display.

By default, only the numeric userId is displayed; use the `showuserprofile` option to get the user email address and name.
You can only get profile information if the scope `https://www.googleapis.com/auth/classroom.profile.emails` is enabled
for service account access; verify with `gam <UserTypeEntity> update serviceaccount`.

Use the `countsonly` option to display the number of submissions in a course but not their details.

By default, Gam displays the information as columns of fields; the following option causes the output to be in JSON format,
* `formatjson` - Display the fields in JSON format.

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.
