# List

The list command is used to verify collections of objects.

## Commands
```
gam list [todrive <ToDriveAttribute>*] <EntityList> [data <CrOSTypeEntity>|<UserTypeEntity> [delimiter <Character>]]
gam <CrOSTypeEntity>|<UserTypeEntity> list [todrive <ToDriveAttribute>*] [data <EntityList> [delimiter <Character>]]
```

Allow mapping of keyfield value in csvkmd selectors.
    <CSVkmdSelector> ::= csvkmd <FileName> [charset <Charset>]
        keyfield <FieldName> [keypattern <REMatchPattern>] [keyvalue <String>] [delimiter <String>]
        (matchfield <FieldName> <RegularExpression>)*
        [datafield <FieldName>(:<FieldName)* [delimiter <String>]]

You want to update the membership of a collection of parent groups at your school, the data is coming from a database in a fixed format.
Example 1, CSV File GroupP1P2.csv, exactly the data you want, keypattern and keyvalue are not required
Group,P1Email,P2Email
2017-parents@domain.com,g1member11@domain.com,g1member12@domain.com
2017-parents@domain.com,g1member21@domain.com,g1member22@domain.com
2018-parents@domain.com,g2member11@domain.com,g2member11@domain.com
2018-parents@domain.com,g2member21@domain.com,g2member22@domain.com
...
For each row, the value from the Group column is used as the group name.
Verify data selection: gam list csvkmd GroupP1P2.csv keyfield Group datafield P1Email:P2Email data csvdata P1Email:P2Email
Execute: gam update groups csvkmd GroupP1P2.csv keyfield Group datafield P1Email:P2Email sync member csvdata P1Email:P2Email

Example 2, CSV File GradYearP1P2.csv, you have to convert GradYear to group name GradYear-parents@domain.com, keyvalue is required
GradYear,P1Email,P2Email
2017,g1member11@domain.com,g1member12@domain.com
2017,g1member21@domain.com,g1member22@domain.com
2018,g2member11@domain.com,g2member11@domain.com
2018,g2member21@domain.com,g2member22@domain.com
...
For each row, the value from the GradYear column replaces the keyField name in the keyvalue argument and that value is used as the group name.
Verify data selection: gam list csvkmd GradYearP1P2.csv keyfield GradYear keyvalue GradYear-parents@domain.com datafield P1Email:P2Email data csvdata P1Email:P2Email
Execute: gam update groups csvkmd GradYearP1P2.csv keyfield GradYear keyvalue GradYear-parents@domain.com datafield P1Email:P2Email sync member csvdata P1Email:P2Email

Example 3, CSV File GradYearP1P2.csv, you have to convert GradYear to group name 'LastTwoDigitsOfGradYear-parents@domain.com', keypattern and keyvalue are required.
GradYear,P1Email,P2Email
2017,g1member11@domain.com,g1member12@domain.com
2017,g1member21@domain.com,g1member22@domain.com
2018,g2member11@domain.com,g2member11@domain.com
2018,g2member21@domain.com,g2member22@domain.com
...
For each row, the value from the GradYear column is matched against the keypattern, the matched segments are substituted into the keyvalue argument and that value is used as the group name.
Verify data selection: gam list csvkmd GradYearP1P2.csv keyfield GradYear keypattern '20(..)' keyvalue '\1-parents@domain.com' datafield P1Email:P2Email data csvdata P1Email:P2Email
Execute: gam update groups csvkmd GradYearP1P2.csv keyfield GradYear keypattern '20(..)' keyvalue '\1-parents@domain.com' datafield P1Email:P2Email sync member csvdata P1Email:P2Email
