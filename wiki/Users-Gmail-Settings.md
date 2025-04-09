# Users - Gmail - Settings
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Manage IMAP/POP](#manage-imappop)
- [Display IMAP/POP](#display-imappop)
- [Report IMAP/POP Gmail access](#report-imappop-gmail-access)
- [Report all Gmail access](#report-all-gmail-access)
- [Manage Language](#manage-language)
- [Display Language](#display-language)

## API Documentation
* [Gmail API - IMAP/POP/Language](https://developers.google.com/gmail/api/v1/reference/users/settings)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

```
<Language> ::=
        ach|af|ag|ak|am|ar|az|be|bem|bg|bn|br|bs|ca|chr|ckb|co|crs|cs|cy|da|de|
        ee|el|en|en-gb|en-us|eo|es|es-419|et|eu|fa|fi|fil|fo|fr|fr-ca|fy|
        ga|gaa|gd|gl|gn|gu|ha|haw|he|hi|hr|ht|hu|hy|ia|id|ig|in|is|it|iw|ja|jw|
        ka|kg|kk|km|kn|ko|kri|ku|ky|la|lg|ln|lo|loz|lt|lua|lv|
        mfe|mg|mi|mk|ml|mn|mo|mr|ms|mt|my|ne|nl|nn|no|nso|ny|nyn|oc|om|or|
        pa|pcm|pl|ps|pt-br|pt-pt|qu|rm|rn|ro|ru|rw|
        sd|sh|si|sk|sl|sn|so|sq|sr|sr-me|st|su|sv|sw|
        ta|te|tg|th|ti|tk|tl|tn|to|tr|tt|tum|tw|
        ug|uk|ur|uz|vi|wo|xh|yi|yo|zh-cn|zh-hk|zh-tw|zu
```
## Manage IMAP/POP
```
gam <UserTypeEntity> imap|imap4 <Boolean> [noautoexpunge]
        [expungebehavior archive|deleteforever|trash] [maxfoldersize 0|1000|2000|5000|10000]

gam <UserTypeEntity> pop|pop3 <Boolean> [for allmail|newmail|mailfromnowon|fromnowown]
        [action keep|leaveininbox|archive|delete|trash|markread]
```
## Display IMAP/POP
```
gam <UserTypeEntity> print imap|imap4 [todrive <ToDriveAttribute>*]
gam <UserTypeEntity> show imap|imap4

gam <UserTypeEntity> print pop|pop3 [todrive <ToDriveAttribute>*]
gam <UserTypeEntity> show pop|pop3
```

## Report IMAP/POP Gmail access
```
gam redirect csv ./ImapPopUsage.csv report user parameters gmail:timestamp_last_imap,gmail:timestamp_last_pop
```

## Report all Gmail access
```
gam redirect csv ./GmailUsage.csv report user parameters gmail:timestamp_last_access,gmail:timestamp_last_imap,gmail:timestamp_last_interaction,gmail:timestamp_last_pop,gmail:timestamp_last_webmail
```

## Manage Language
This command changes the language for Gmail.
```
gam <UserTypeEntity> language <Language>
```

## Display Language
```
gam <UserTypeEntity> print language [todrive <ToDriveAttribute>*]
gam <UserTypeEntity> show language
```
