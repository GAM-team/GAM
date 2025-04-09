# Email Audit Monitor
- [API documentation](#api-documentation)
- [Notes](#notes)
- [Definitions](#definitions)
- [Create Email Audit Monitor](#create-email-audit-monitor)
- [Delete Email Audit Monitor](#delete-email-audit-monitor)
- [Display Email Audit Monitors](#display-email-audit-monitors)

## API documentation
* [Email Audit API](https://developers.google.com/admin-sdk/email-audit)

## Notes
To use these features you must add the `Email Audit API` to your project and authorize the appropriate scopes:
* `Client Access` - `Email Audit API`
```
gam update project
gam oauth create
```

## Definitions
```
<DateTime> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute> |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
<DomainName> ::= <String>(.<String>)+
<EmailAddress> ::= <String>@<DomainName>
```
## Create Email Audit Monitor
```
gam audit monitor create <EmailAddress> <DestEmailAddress> [begin <DateTime>] [end <DateTime>]
        [incoming_headers] [outgoing_headers] [nochats] [nodrafts] [chat_headers] [draft_headers]
```
## Delete Email Audit Monitor
```
gam audit monitor delete <EmailAddress> <DestEmailAddress>
```
## Display Email Audit Monitors
```
gam audit monitor list <EmailAddress>
```
