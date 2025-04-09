# Schemas
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage schemas](#manage-schemas)
- [Display schemas](#display-schemas)

## API documentation
* [Drive API -Schemas](https://developers.google.com/admin-sdk/directory/reference/rest/v1/schemas)

## Definitions
```
<SchemaName> ::= <String>
<FieldName> ::= <String>
<SchemaNameList> ::= "<SchemaName>(,<SchemaName>)*"
<SchemaEntity> ::=
        <SchemaNameList> | <FileSelector> | <CSVkmdSelector>
        See: https://github.com/GAM-team/GAM/wiki/Collections-of-Items

<SchemaFieldDefinition> ::=
        field <FieldName> [displayname <String>]
            (type bool|date|double|email|int64|phone|string)
            [multivalued|multivalue] [indexed] [restricted]
            [range <Number> <Number>]
        endfield
```
## Manage schemas
When creating and updating schemas, spaces are converted to `_` in schema
and field names as spaces are not valid. The schema and field display names will
retain the spaces. You can specify schema/field display names independently of the schema/field name.
```
gam create|add schema|schemas <SchemaName> [displayname <String>] <SchemaFieldDefinition>+
gam update schema <SchemaName> [displayname <String>] <SchemaFieldDefinition>* (deletefield <FieldName>)*
gam delete schema <SchemaName>

gam update schema|schemas <SchemaEntity> [displayname <String>] <SchemaFieldDefinition>* (deletefield <FieldName>)*
gam delete schema|schemas <SchemaEntity>
```

To create a field for your users pronouns you can use: 

```gam create schema pronouns field pronouns type string```

And to update a users custom field you can use:
```gam update <UserTypeEntity> pronouns.pronouns "they/them"```


## Display schemas
```
gam info schema|schemas <SchemaEntity>
gam show schema|schemas
gam print schema|schemas [todrive <ToDriveAttribute>*]
```
