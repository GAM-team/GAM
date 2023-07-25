# Sites
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage classic sites](#manage-classic-sites)
- [Display classic sites](#display-classic-sites)
- [Manage classic sites access](#manage-classic-sites-access)
- [Display classic sites access](#display-classic-sites-access)

## API documentation
* https://developers.google.com/google-apps/sites/docs/1.0/developers_guide_python

## Definitions
```
<Date> ::=
        <Year>-<Month>-<Day> |
        (+|-)<Number>(d|w|y) |
        never|
        today

<DomainName> ::= <String>(.<String>)+
<DomainNameList> ::= "<DomainName>(,<DomainName>)*"
<DomainNameEntity> ::=
        <DomainNameList>|<FileSelector>|<CSVkmdSelector>| <CSVDataSelector>

<SiteName> ::= [a-z,0-9,-]+
<SiteItem> ::= [<DomainName>/]<SiteName>
<SiteList> ::= "<SiteItem>(,<SiteItem>)*"
<SiteEntity> ::=
        <SiteList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>

<SiteACLRole> ::= editor|owner|reader|writer
<SiteACLRoleList> ::= "<SiteACLRole>(,<SiteACLRole>)*"

<SiteAttribute> ::=
        (categories <String>)|
        (name <String>)|
        (sourcelink <URI>])|
        (summary <String>)|
        (theme <String>)

<SiteACLScope> ::=
        <EmailAddress>|user:<EmailAdress>|group:<EmailAddress>|
        domain:<DomainName>|domain|default
<SiteACLScopeList> ::= "<SiteACLScope>(,<SiteACLScope>)*"
<SiteACLScopeEntity> ::=
        <SiteACLScopeList>|<FileSelector>|<CSVkmdSelector>|<CSVDataSelector>
```
## Manage classic sites
```
gam [<UserTypeEntity>] create site <SiteItem> <SiteAttribute>*
gam [<UserTypeEntity>] update sites <SiteEntity> <SiteAttribute>+
```
## Display classic sites
```
gam [<UserTypeEntity>] info sites <SiteEntity>
        [withmappings] [role|roles all|<SiteACLRoleList>]
gam [<UserTypeEntity>] show sites [domain|domains <DomainNameEntity>] [includeallsites]
        [withmappings] [role|roles all|<SiteACLRoleList>] [maxresults <Number>]
gam [<UserTypeEntity>] print sites [todrive <ToDriveAttribute>*]
        [domain|domains <DomainNameEntity>] [includeallsites] 
        [withmappings] [role|roles all|<SiteACLRoleList>] [maxresults <Number>]
        [convertcrnl] [delimiter <Character>]

gam [<UserTypeEntity>] print siteactivity <SiteEntity> [todrive <ToDriveAttribute>*]
        [maxresults <Number>] [updated_min <Date>] [updated_max <Date>]
```
## Manage classic sites access
```
gam [<UserTypeEntity>] add siteacls <SiteEntity> <SiteACLRole> <SiteACLScopeEntity>
gam [<UserTypeEntity>] update siteacls <SiteEntity> <SiteACLRole> <SiteACLScopeEntity>
gam [<UserTypeEntity>] delete siteacls <SiteEntity> <SiteACLScopeEntity>
```
## Display classic sites access
```
gam [<UserTypeEntity>] info siteacls <SiteEntity> <SiteACLScopeEntity>
gam [<UserTypeEntity>] show siteacls <SiteEntity>
gam [<UserTypeEntity>] print siteacls <SiteEntity> [todrive <ToDriveAttribute>*]
```
