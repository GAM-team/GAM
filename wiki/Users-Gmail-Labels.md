# Users - Gmail - Labels
- [API documentation](#api-documentation)
- [Python Regular Expressions](Python-Regular-Expressions) Match function
- [Definitions](#definitions)
- [Special quoting](#special-quoting)
- [Add a label](#add-a-label)
- [Update a label's settings](#update-a-labels-settings)
- [Change label names](#change-label-names)
- [Delete labels](#delete-labels)
- [Display labels](#display-labels)

## API documentation
* [Gmail API - Labels](https://developers.google.com/gmail/api/v1/reference/users.labels)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>

<ColorHex> ::= "#<Hex><Hex><Hex><Hex><Hex><Hex>"
<LabelColorHex> ::=
        #000000|#076239|#0b804b|#149e60|#16a766|#1a764d|#1c4587|#285bac|
        #2a9c68|#3c78d8|#3dc789|#41236d|#434343|#43d692|#44b984|#4a86e8|
        #653e9b|#666666|#68dfa9|#6d9eeb|#822111|#83334c|#89d3b2|#8e63ce|
        #999999|#a0eac9|#a46a21|#a479e2|#a4c2f4|#aa8831|#ac2b16|#b65775|
        #b694e8|#b9e4d0|#c6f3de|#c9daf8|#cc3a21|#cccccc|#cf8933|#d0bcf1|
        #d5ae49|#e07798|#e4d7f5|#e66550|#eaa041|#efa093|#efefef|#f2c960|
        #f3f3f3|#f691b3|#f6c5be|#f7a7c0|#fad165|#fb4c2f|#fbc8d9|#fcda83|
        #fcdee8|#fce8b3|#fef1d1|#ffad47|#ffbc6b|#ffd6a2|#ffe6c7|#ffffff
<LabelBackgroundColorHex> ::=
        #16a765|#2da2bb|#42d692|#4986e7|#98d7e4|#a2dcc1|
        #b3efd3|#b6cff5|#b99aff|#c2c2c2|#cca6ac|#e3d7ff|
        #e7e7e7|#ebdbde|#f2b2a8|#f691b2|#fb4c2f|#fbd3e0|
        #fbe983|#fdedc1|#ff7537|#ffad46|#ffc8af|#ffdeb5
<LabelTextColorHex> ::=
        #04502e|#094228|#0b4f30|#0d3472|#0d3b44|#3d188e|
        #464646|#594c05|#662e37|#684e07|#711a36|#7a2e0b|
        #7a4706|#8a1c0a|#994a64|#ffffff

<LabelID> ::= Label_<String>
<LabelIDList> ::= "<LabelID>(,<LabelID)*"
<LabelIDEntity> ::=
        <LabelIDList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
<LabelName> ::= <String>
<LabelNameList> ::= "'<LabelName>'(,'<LabelName>')*"
<LabelNameEntity> ::=
        <LabelNameList> | <FileSelector> | <CSVFileSelector> | <CSVkmdSelector> | <CSVDataSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items
```
## Special quoting
You specify a single label name with `label <LabelName>` and a list of labels with `labellist <LabelNameList>`.
As label names can contain spaces, some care must be used when entering `<LabelName>` and `<LabelNametList>`.

Suppose you have a label `Foo Bar`. To delete it you enter the command: `gam user user@domain.com delete label "Foo Bar"`

The shell strips the `"` leaving a single argument `Foo Bar`; gam correctly processes the argument.

Suppose you enter the command: `gam user user@domain.com delete labellist "Foo Bar"`

The shell strips the `"` leaving a single argument `Foo Bar`; gam splits the argument on space leaving two items and then tries to process `Foo` and `Bar`, not what you want.

You must enter: `gam user user@domain.com delete labellist "'Foo Bar'"`

The shell strips the `"` leaving a single argument `'Foo Bar'`; gam splits the argument on space while honoring the `'` leaving one item `Foo Bar` and correctly processes the item.

For quoting rules, see: [List Quoting Rules](Command-Line-Parsing)

## Add a label
```
gam <UserTypeEntity> [add] label|labels <LabelName>
        [messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
        [backgroundcolor "<LabelColorHex>|<LabelBackgroundColorHex>|custom:<ColorHex>"]
        [textcolor "<LabelColorHex>|<LabelTextColorHex>|custom:<ColorHex>"]
        [buildpath [<Boolean>]] 
gam <UserTypeEntity> create labellist <LabelNameEntity>
        [messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread] [buildpath [<Boolean>]]
        [backgroundcolor "<LabelColorHex>|<LabelBackgroundColorHex>|custom:<ColorHex>"]
        [textcolor "<LabelColorHex>|<LabelTextColorHex>|custom:<ColorHex>"]
        [buildpath [<Boolean>]]
```
`<LabelColorHex>` values should be enclosed in " to keep the command shell on MacOS and Linux from mis-interpreting them.

In Gmail, you can have a multi-level label like `Top/Middle/Bottom`; you can also have a single-level label like `Top/Middle/Bottom`,
* If `buildpath` is omitted or `<Boolean>` is set to False, labels containing `/` will be created as single-level.
* If `buildpath` is present and `<Boolean>` is omitted or set to True, labels containing `/` will be created as multi-level;
all parent labels are created as necessary.

Example: `gam user user@domain.com add label "Top/Middle/Bottom" buildpath`

## Update a label's settings
The two commands are equivalent; in the first you specify a `<LabelName>`, in the second you specify a `<LabelId>`.
```
gam <UserTypeEntity> update labelsettings <LabelName> [name <String>]
        [messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
        [backgroundcolor "<LabelColorHex>|<LabelBackgroundColorHex>|custom:<ColorHex>"]
        [textcolor "<LabelColorHex>|<LabelTextColorHex>|custom:<ColorHex>"]

gam <UserTypeEntity> update labelid <LabelID> [name <String>]
        [messagelistvisibility hide|show] [labellistvisibility hide|show|showifunread]
        [backgroundcolor "<LabelColorHex>|<LabelBackgroundColorHex>|custom:<ColorHex>"]
        [textcolor "<LabelColorHex>|<LabelTextColorHex>|custom:<ColorHex>"]
```
`<LabelColorHex>` values should be enclosed in " to keep the command shell on MacOS and Linux from mis-interpreting them.

## Change label names
```
gam <UserTypeEntity> update label|labels
        [search <REMatchPattern>] [replace <RESubstitution>] [merge [keepoldlabel]]
```
At it's simplest, `<REMatchPattern>` is the old label name, and `<RESubstitution>` is the new label name.
To change the label "Foo" to a new label "Bar" (the label "Bar" must not already exist):
```
gam user user@domain.com update label search "Foo" replace "Bar"
```
If there is any chance that "Foo" may appear in the middle of a label, you can anchor the `search <RegularExpressions>`
with `^` and `$` so that only "Foo" exactly matches.
```
gam user user@domain.com update label search "^Foo$" replace "Bar"
```
To change the label "Foo" to an existing label "Bar", use the merge option. If you want to keep "Foo" after the merge,
use the `keepoldlabel` option; otherwise, it will be deleted which may not be desirable.
```
gam user user@domain.com update label search "^Foo$" replace "Bar" merge keepoldlabel
```
If you want to use part of an old label name in the new label name, you isolate the portion of the old label name you want to keep
and indicate in the new label name where the isolated portion goes. In `search <REMatchPattern>` there should be at least one instance of a
parenthesized expression, e.g., `(.*)`. In `replace <RESubstitution>`, `\1`, `\2`, ... indicate where the isolated portions go.
```
gam user user@domain.com update label search "^INBOX/(.*)$" replace "O365/\1"
```
## Delete labels
```
gam <UserTypeEntity> delete|del label|labels <LabelName>|regex:<REMatchPattern>|--ALL_LABELS--
gam <UserTypeEntity> delete labelid <LabelID>
gam <UserTypeEntity> delete labellist <LabelNameEntity>
gam <UserTypeEntity> delete labelidlist <LabelIDEntity>
```
## Display labels
```
gam <UserTypeEntity> show labels|label
        [useronly|onlyuser [<Boolean>]] [showcounts [<Boolean>]]
        [nested [<Boolean>]] [display allfields|basename|fullname]
        [labellist <LabelNameEntity>]
gam <UserTypeEntity> print labels|label [todrive <ToDriveAttribute>*]
        [useronly|onlyuser [<Boolean>]] [showcounts [<Boolean>]]
        [labellist <LabelNameEntity>]
```
By default, all labels, user and system are displayed.
  * `useronly|onlyuser` - Do not display system labels.
  * `labellist <LabelNameEntity>` - Display selected labels

* `showCounts` - The fields: messagesTotal, messagesUnread, threadsTotal and threadsUnread are displayed in addition to other fields.
* `nested` - This causes nested labels to be indented under their parent label to allow the hierarchy to be more clearly visible.
* If `display` is not specified or `display allfields` is specified, the full name of the label and the fields (type, id, labelListVisibility, messageListVisibility) are displayed.
* If `display fullname` is specified, the full name of the label, and no other fields, is displayed.
* If `display basename` is specified, the base name (rightmost component) of the label, and no other fields, is displayed.
The `display fullname/basename` options are most useful in conjunction with nested.
