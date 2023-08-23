# Users - Tasks
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Create Tasks](#create-tasks)
- [Update Tasks](#update-tasks)
- [Delete Tasks](#delete-tasks)
- [Move Tasks](#move-tasks)
- [Display Tasks](#display-tasks)
- [Create Task Lists](#create-task-lists)
- [Update Task Lists](#update-task-lists)
- [Delete Task Lists](#delete-task-lists)
- [Clear Task Lists](#clear-task-lists)
- [Display Task Lists](#display-task-lists)

## API documentation
* https://developers.google.com/tasks/reference/rest

## Notes
To use these commands you must add the 'Tasks API' to your project and update your service account authorization.
```
gam update project
gam user user@domain.com check serviceaccount
```

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)
```
<TaskID> ::= <String>
<TaskListID> ::= <String>
<TasklistIDTaskID> ::= <TasklistID>/<TaskID>
<TasklistIDList> ::= "<TasklistID>(,<TasklistID>)*"
<TasklistIDTaskIDList> ::= "<TasklistIDTaskID>(,<TasklistIDTaskID>)*"
<TasklistIDEntity> ::=
        <TasklistIDList> | <FileSelector> | <CSVFileSelector>
        See: https://github.com/taers232c/GAMADV-XTD3/wiki/Collections-of-Items
<TasklistIDTaskIDEntity> ::=
        <TasklistIDTaskIDList> | <FileSelector> | <CSVFileSelector>
        See: https://github.com/taers232c/GAMADV-XTD3/wiki/Collections-of-Items

<TaskAttribute> ::=
        (title <String>)|
        (notes <String>)|
        (status needsaction|completed)|
        (due <Time>)

<TasklistAttribute> ::=
        (title <String>)
```
## Create Tasks
```
gam <UserTypeEntity> create task <TasklistIDEntity>
        <TaskAttribute>* [parent <TaskID>] [previous <TaskID>]
        [compact|formatjson|returnidonly]
```
By default, Gam displays the created task as an indented list of keys and values; the task notes text is displayed as individual lines.
* `compact` - Display the task notes text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the task in JSON format
* `returnidonly` - Display the note name only

## Update Tasks
```
gam <UserTypeEntity> update task <TasklistIDTaskIDEntity>
        <TaskAttribute>*
        [compact|formatjson]
```
By default, Gam displays the updated task as an indented list of keys and values; the task notes text is displayed as individual lines.
* `compact` - Display the task notes text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the task in JSON format

## Delete Tasks
```
gam <UserTypeEntity> delete task <TasklistIDTaskIDEntity>
```

## Move Tasks
```
gam <UserTypeEntity> move task <TasklistIDTaskIDEntity>
        [parent <TaskID>] [previous <TaskID>]
        [compact|formatjson]
```
By default, Gam displays the moved task as an indented list of keys and values; the task notes text is displayed as individual lines.
* `compact` - Display the task notes text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the task in JSON format

## Display Tasks
### Display selected tasks
```
gam <UserTypeEntity> info task <TasklistIDTaskIDEntity>
        [compact|formatjson]
```
By default, Gam displays the tasks as an indented list of keys and values; the task notes text is displayed as individual lines.
* `compact` - Display the task notes text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the task in JSON format

### Display all tasks
```
gam <UserTypeEntity> show tasks [tasklists <TasklistIDEntity>]
        [completedmin <Time>] [completedmax <Time>]
        [duemin <Time>] [duemax <Time>]
        [updatedmin <Time>]
        [showcompleted [<Boolean>]] [showdeleted [<Boolean>]] [showhidden [<Boolean>]] [showall]
        [orderby completed|due|updated]
        [countsonly|compact|formatjson]
```
By default, tasks are displayed in hierarchical order.
* `orderby completed` - Display tasks in completed date order regardless of the hierarchy.
* `orderby due` - Display tasks in due date order regardless of the hierarchy.
* `orderby updated` - Display tasks in updated date order regardless of the hierarchy.

By default, Gam displays the tasks as an indented list of keys and values; the task notes text is displayed as individual lines.
* `compact` - Display the task notes text with escaped carriage returns as \r and newlines as \n
* `formatjson` - Display the task in JSON format

By default, only tasks with status `needsAction` are displayed.
* `showdeleted` - Add deleted tasks to the display
* `showhidden` - Add hidden tasls to the display
* `showcompleted` - Add completed tasks to the display. `showHidden` must also be True to show tasks completed in first party clients, such as the web UI and Google's mobile apps.
* `showall` - Equivalent to `showdeleted` `showhidden` `showcompleted`
```
gam <UserTypeEntity> print tasks [tasklists <TasklistIDEntity>] [todrive <ToDriveAttribute>*]
        [completedmin <Time>] [completedmax <Time>]
        [duemin <Time>] [duemax <Time>]
        [updatedmin <Time>]
        [showcompleted [<Boolean>]] [showdeleted [<Boolean>]] [showhidden [<Boolean>]] [showall]
        [orderby completed|due|updated]
        [countsonly | (formatjson [quotechar <Character>])]
```
By default, tasks are displayed in hierarchical order.
* `orderby completed` - Display tasks in completed date order regardless of the hierarchy.
* `orderby due` - Display tasks in due date order regardless of the hierarchy.
* `orderby updated` - Display tasks in updated date order regardless of the hierarchy.

By default, only tasks with status `needsAction` are displayed.
* `showdeleted` - Add deleted tasks to the display
* `showhidden` - Add hidden tasls to the display
* `showcompleted` - Add completed tasks to the display. `showHidden` must also be True to show tasks completed in first party clients, such as the web UI and Google's mobile apps.
* `showall` - Equivalent to `showdeleted` `showhidden` `showcompleted`

By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

## Create Task Lists
```
gam <UserTypeEntity> create tasklist
        <TasklistAttribute>*
        [returnidonly] [formatjson]
```
By default, Gam displays the created task list as an indented list of keys and values.
* `formatjson` - Display the task list in JSON format
* `returnidonly` - Display the task list ID only

## Update Task Lists
```
gam <UserTypeEntity> update tasklist <TasklistIDEntity>
        <TasklistAttribute>*
        [formatjson]
```
By default, Gam displays the updated task list as an indented list of keys and values.
* `formatjson` - Display the task list in JSON format

## Delete Task Lists
```
gam <UserTypeEntity> delete tasklist <TasklistIDEntity>
```

## Clear Task Lists
Clears all completed tasks from the specified task lists.
```
gam <UserTypeEntity> clear tasklist <TasklistIDEntity>
```

## Display Task Lists
### Display selected task lists
```
gam <UserTypeEntity> info tasklist <TasklistIDEntity>
        [formatjson]
```
By default, Gam displays the task lists as an indented list of keys and values.
* `formatjson` - Display the task list in JSON format

### Display all Task Lists
```
gam <UserTypeEntity> show tasklists
        [countsonly|formatjson]
```
By default, Gam displays the task lists as an indented list of keys and values.
* `formatjson` - Display the task lists in JSON format

```
gam <UserTypeEntity> print tasklists [todrive <ToDriveAttribute>*]
        [countsonly | (formatjson [quotechar <Character>])]
```
By default, when writing CSV files, Gam uses a quote character of double quote `"`. The quote character is used to enclose columns that contain
the quote character itself, the column delimiter (comma by default) and new-line characters. Any quote characters within the column are doubled.
When using the `formatjson` option, double quotes are used extensively in the data resulting in hard to read/process output.
The `quotechar <Character>` option allows you to choose an alternate quote character, single quote for instance, that makes for readable/processable output.
`quotechar` defaults to `gam.cfg/csv_output_quote_char`. When uploading CSV files to Google, double quote `"` should be used.

