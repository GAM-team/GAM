# Basic Items
- [Primitives](#primitives)
- [Items built from primitives](#items-built-from-primitives)
- [Named items](#named-items)
- [List Items](List-Items)

## Primitives
```
<Character> ::= a single character
<Digit> ::= 0|1|2|3|4|5|6|7|8|9
<Number> ::= <Digit>+
<Float> ::= <Digit>*.<Digit>+
<Hex> ::= <Digit>|a|b|c|d|e|f|A|B|C|D|E|F
<Space> ::= an actual space character
<String> ::= a string of characters, surrounded by " if it contains spaces
<FalseValues>= false|off|no|disabled|0
<TrueValues> ::= true|on|yes|enabled|1

<BCP47LanguageCode> ::=
        ar-sa| # Arabic Saudi Arabia
        cs-cz| # Czech Czech Republic
        da-dk| # Danish Denmark
        de-de| # German Germany
        el-gr| # Modern Greek Greece
        en-au| # English Australia
        en-gb| # English United Kingdom
        en-ie| # English Ireland
        en-us| # English United States
        en-za| # English South Africa
        es-es| # Spanish Spain
        es-mx| # Spanish Mexico
        fi-fi| # Finnish Finland
        fr-ca| # French Canada
        fr-fr| # French France
        he-il| # Hebrew Israel
        hi-in| # Hindi India
        hu-hu| # Hungarian Hungary
        id-id| # Indonesian Indonesia
        it-it| # Italian Italy
        ja-jp| # Japanese Japan
        ko-kr| # Korean Republic of Korea
        nl-be| # Dutch Belgium
        nl-nl| # Dutch Netherlands
        no-no| # Norwegian Norway
        pl-pl| # Polish Poland
        pt-br| # Portuguese Brazil
        pt-pt| # Portuguese Portugal
        ro-ro| # Romanian Romania
        ru-ru| # Russian Russian Federation
        sk-sk| # Slovak Slovakia
        sv-se| # Swedish Sweden
        th-th| # Thai Thailand
        tr-tr| # Turkish Turkey
        zh-cn| # Chinese China
        zh-hk| # Chinese Hong Kong
        zh-tw  # Chinese Taiwan
<Charset> ::= ascii|latin1|mbcs|utf-8|utf-8-sig|utf-16|<String>
<CalendarColorIndex> ::= <Number in range 1-24>
<CalendarColorName> ::=
        amethyst|avocado|banana|basil|birch|blueberry|
        cherryblossom|citron|cobalt|cocoa|eucalyptus|flamingo|
        grape|graphite|lavender|mango|peacock|pistachio|
        pumpkin|radicchio|sage|tangerine|tomato|wisteria|
<ColorHex> ::= "#<Hex><Hex><Hex><Hex><Hex><Hex>"
<ColorNameGoogle> ::=
        asparagus|bluevelvet|bubblegum|cardinal|chocolateicecream|denim|desertsand|
        earthworm|macaroni|marsorange|mountaingray|mountaingrey|mouse|oldbrickred|
        pool|purpledino|purplerain|rainysky|seafoam|slimegreen|spearmint|
        toyeggplant|vernfern|wildstrawberries|yellowcab
<ColorNameWeb> ::=
        aliceblue|antiquewhite|aqua|aquamarine|azure|beige|bisque|black|blanchedalmond|
        blue|blueviolet|brown|burlywood|cadetblue|chartreuse|chocolate|coral|
        cornflowerblue|cornsilk|crimson|cyan|darkblue|darkcyan|darkgoldenrod|darkgray|
        darkgrey|darkgreen|darkkhaki|darkmagenta|darkolivegreen|darkorange|darkorchid|
        darkred|darksalmon|darkseagreen|darkslateblue|darkslategray|darkslategrey|
        darkturquoise|darkviolet|deeppink|deepskyblue|dimgray|dimgrey|dodgerblue|
        firebrick|floralwhite|forestgreen|fuchsia|gainsboro|ghostwhite|gold|goldenrod|
        gray|grey|green|greenyellow|honeydew|hotpink|indianred|indigo|ivory|khaki|
        lavender|lavenderblush|lawngreen|lemonchiffon|lightblue|lightcoral|lightcyan|
        lightgoldenrodyellow|lightgray|lightgrey|lightgreen|lightpink|lightsalmon|
        lightseagreen|lightskyblue|lightslategray|lightslategrey|lightsteelblue|
        lightyellow|lime|limegreen|linen|magenta|maroon|mediumaquamarine|mediumblue|
        mediumorchid|mediumpurple|mediumseagreen|mediumslateblue|mediumspringgreen|
        mediumturquoise|mediumvioletred|midnightblue|mintcream|mistyrose|moccasin|
        navajowhite|navy|oldlace|olive|olivedrab|orange|orangered|orchid|
        palegoldenrod|palegreen|paleturquoise|palevioletred|papayawhip|peachpuff|
        peru|pink|plum|powderblue|purple|red|rosybrown|royalblue|saddlebrown|salmon|
        sandybrown|seagreen|seashell|sienna|silver|skyblue|slateblue|slategray|
        slategrey|snow|springgreen|steelblue|tan|teal|thistle|tomato|turquoise|violet|
        wheat|white|whitesmoke|yellow|yellowgreen
<ColorName> ::= <ColorNameGoogle>|<ColorNameWeb>
<ColorValue> ::= <ColorName>|<ColorHex>
<DayOfWeek> ::= mon|tue|wed|thu|fri|sat|sun
<EventColorIndex> ::= <Number in range 1-11>
<EventColorName> ::=
        banana|basil|blueberry|flamingo|graphite|grape|
        lavender|peacock|sage|tangerine|tomato
<FileFormat> ::=
        csv|doc|dot|docx|dotx|epub|html|jpeg|jpg|json|mht|odp|ods|odt|
        pdf|png|ppt|pot|potx|pptx|rtf|svg|tsv|txt|xls|xlt|xlsx|xltx|zip|
        ms|microsoft|openoffice|
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
<LanguageCode> ::=
        ach|af|ag|ak|am|ar|az|be|bem|bg|bn|br|bs|ca|chr|ckb|co|crs|cs|cy|da|de|
        ee|el|en|en-ca|en-gb|en-us|eo|es|es-419|et|eu|fa|fi|fil|fo|fr|fr-ca|fy|
        ga|gaa|gd|gl|gn|gu|ha|haw|he|hi|hr|ht|hu|hy|ia|id|ig|in|is|it|iw|ja|jw|
        ka|kg|kk|km|kn|ko|kri|ku|ky|la|lg|ln|lo|loz|lt|lua|lv|
        mfe|mg|mi|mk|ml|mn|mo|mr|ms|mt|my|ne|nl|nn|no|nso|ny|nyn|oc|om|or|
        pa|pcm|pl|ps|pt-br|pt-pt|qu|rm|rn|ro|ru|rw|
        sd|sh|si|sk|sl|sn|so|sq|sr|sr-me|st|su|sv|sw|
        ta|te|tg|th|ti|tk|tl|tn|to|tr|tt|tum|tw|
        ug|uk|ur|uz|vi|wo|xh|yi|yo|zh-cn|zh-hk|zh-tw|zu
<Language> ::=
        <LanguageCode>[+|-]|
        <String>
<Locale> ::=
        ''|    #Not defined
        ar-eg| #Arabic, Egypt
        az-az| #Azerbaijani, Azerbaijan
        be-by| #Belarusian, Belarus
        bg-bg| #Bulgarian, Bulgaria
        bn-in| #Bengali, India
        ca-es| #Catalan, Spain
        cs-cz| #Czech, Czech Republic
        cy-gb| #Welsh, United Kingdom
        da-dk| #Danish, Denmark
        de-ch| #German, Switzerland
        de-de| #German, Germany
        el-gr| #Greek, Greece
        en-au| #English, Australia
        en-ca| #English, Canada
        en-gb| #English, United Kingdom
        en-ie| #English, Ireland
        en-us| #English, U.S.A.
        es-ar| #Spanish, Argentina
        es-bo| #Spanish, Bolivia
        es-cl| #Spanish, Chile
        es-co| #Spanish, Colombia
        es-ec| #Spanish, Ecuador
        es-es| #Spanish, Spain
        es-mx| #Spanish, Mexico
        es-py| #Spanish, Paraguay
        es-uy| #Spanish, Uruguay
        es-ve| #Spanish, Venezuela
        fi-fi| #Finnish, Finland
        fil-ph| #Filipino, Philippines
        fr-ca| #French, Canada
        fr-fr| #French, France
        gu-in| #Gujarati, India
        hi-in| #Hindi, India
        hr-hr| #Croatian, Croatia
        hu-hu| #Hungarian, Hungary
        hy-am| #Armenian, Armenia
        in-id| #Indonesian, Indonesia
        it-it| #Italian, Italy
        iw-il| #Hebrew, Israel
        ja-jp| #Japanese, Japan
        ka-ge| #Georgian, Georgia
        kk-kz| #Kazakh, Kazakhstan
        kn-in| #Kannada, India
        ko-kr| #Korean, Korea
        lt-lt| #Lithuanian, Lithuania
        lv-lv| #Latvian, Latvia
        ml-in| #Malayalam, India
        mn-mn| #Mongolian, Mongolia
        mr-in| #Marathi, India
        my-mn| #Burmese, Myanmar
        nl-nl| #Dutch, Netherlands
        nn-no| #Nynorsk, Norway
        no-no| #Bokmal, Norway
        pa-in| #Punjabi, India
        pl-pl| #Polish, Poland
        pt-br| #Portuguese, Brazil
        pt-pt| #Portuguese, Portugal
        ro-ro| #Romanian, Romania
        ru-ru| #Russian, Russia
        sk-sk| #Slovak, Slovakia
        sl-si| #Slovenian, Slovenia
        sr-rs| #Serbian, Serbia
        sv-se| #Swedish, Sweden
        ta-in| #Tamil, India
        te-in| #Telugu, India
        th-th| #Thai, Thailand
        tr-tr| #Turkish, Turkey
        uk-ua| #Ukrainian, Ukraine
        vi-vn| #Vietnamese, Vietnam
        zh-cn| #Simplified Chinese, China
        zh-hk| #Traditional Chinese, Hong Kong SAR China
        zh-tw  #Traditional Chinese, Taiwan
<MimeTypeShortcut> ::=
        gdoc|gdocument|
        gdrawing|
        gfile|
        gfolder|gdirectory|
        gform|
        gfusion|
        gjam|
        gmap|
        gpresentation|
        gscript|
        gsheet|gspreadsheet|
        gshortcut|
        g3pshortcut|
        gsite|
        shortcut
<MimeTypeName> ::= application|audio|font|image|message|model|multipart|text|video
<MimeType> ::= <MimeTypeShortcut>|(<MimeTypeName>/<String>)
```
## Items built from primitives
```
<Boolean> ::= <TrueValues>|<FalseValues>
<ByteCount> ::= <Number>[m|k|b]
<CIDRnetmask> ::= <Number>.<Number>.<Number>.<Number>/<Number>
<Year> ::= <Digit><Digit><Digit><Digit>
<Month> ::= <Digit><Digit>
<Day> ::= <Digit><Digit>
<Hour> ::= <Digit><Digit>
<Minute> ::= <Digit><Digit>
<Second> ::= <Digit><Digit>
<MilliSeconds> ::= <Digit><Digit><Digit>
<Date> ::=
        <Year>-<Month>-<Day> |
        (+|-)<Number>(d|w|y) |
        never|
        today
<DateTime> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute> |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
<Time> ::=
        <Year>-<Month>-<Day>(<Space>|T)<Hour>:<Minute>:<Second>[.<MilliSeconds>](Z|(+|-(<Hour>:<Minute>))) |
        (+|-)<Number>(m|h|d|w|y) |
        never|
        now|today
<RegularExpression> ::= <String>
        See: https://docs.python.org/3/library/re.html
<REMatchPattern> ::= <RegularExpression>
<RESearchPattern> ::= <RegularExpression>
<RESubstitution> ::= <String>>
<ProjectID> ::= <String>
        Must match this Python Regular Expression: [a-z][a-z0-9-]{4,28}[a-z0-9]
<ServiceAccountName> ::= <String>
        Must match this Python Regular Expression: [a-z][a-z0-9-]{4,28}[a-z0-9]
<SiteName> ::= [a-z,0-9,-]+
<UniqueID> ::= id:<String>|uid:<String>
```
## Named items
```
<AccessToken> ::= <String>
<AlertID> ::= <String>
<APIScopeURL> ::= <String>
<APPID> ::= <String>
<ASPID> ::= <String>
<AssetTag> ::= <String>
<BrowserTokenPermanentID> ::= <String>
<BuildingID> ::= <String>|id:<String>
<CAALevelName> ::= <String>
<CalendarACLScope> ::=
        <EmailAddress>|user:<EmailAddress>|group:<EmailAddress>|
        domain:<DomainName>|domain|default
<CalendarItem> ::= <EmailAddress>
<ChannelCustomerID> ::= <String>
<ChatEmojiName> ::= :[0-9a-z_-]+:
<ChatEmoji> ::= emojiname <ChatEmojiName> | customemojis/<String>
<ChatMember> ::= spaces/<String>/members/<String>
<ChatMessage> ::= spaces/<String>/messages/<String>
<ChatSpace> ::= spaces/<String> | space <String> | space spaces/<String>
<ChatThread> ::= spaces/<String>/threads/<String>
<GIGroupAlias> ::= <EmailAddress>
<GIGroupItem> ::= <EmailAddress>|<UniqueID>|groups/<String>
<CIGroupMemberType> ::= cbcmbrowser|chromeosdevice|customer|group|other|serviceaccount|user
<CIPolicyName> ::= policies/<String>|settings/<String>|<String>
<ClassificationLabelID> ::= <String>
<ClassificationLabelFieldID> ::= <String>
<ClassificationLabelSelectionID> ::= <String>
<ClassificationLabelName> ::= labels/<ClassificationLabelID>[@latest|@published|@<Number>]
<ClassificationLabelPermissionName> ::= labels/<ClassificationLabelID>[@latest|@published|@<Number>]/permissions/(audiences|groups|people)/<String>
<ClassroomInvitationID> ::= <String>
<ClientID> ::= <String>
<CommandID> ::= <String>
<ContactID> ::= <String>
<ContactGroupID> ::= id:<String>
<ContactGroupName> ::= <String>
<ContactGroupItem> ::= <ContactGroupID>|<ContactGroupName>
<CorporaAttribute> ::= alldrives|allteamdrives|domain|onlyteamdrives|user
<CourseAlias> ::= <String>
<CourseAnnouncementID> ::= <Number>
<CourseAnnouncementState> ::= draft|published|deleted
<CourseID> ::= <Number>|d:<CourseAlias>
<CourseMaterialID> ::= <Number>
<CourseMaterialState> ::= draft|published|deleted
<CourseParticipantType> ::= teacher|teachers|student|students
<CourseState> ::= active|archived|provisioned|declined|suspended
<CourseSubmissionID> ::= <Number>
<CourseSubmissionState> ::= new|created|turned_in|returned|reclaimed_by_student
<CourseTopic> ::= <String>
<CourseTopicID> ::= <Number>
<CourseWorkID> ::= <Number>
<CourseWorkState> ::= draft|published|deleted
<CrOSID> ::= <String>
<CustomerID> ::= <String>
<DeliverySetting> ::=
        allmail|
        abridged|daily|
        digest|
        disabled|
        none|nomail
<DeviceID> ::= devices/<String>
<DeviceType> ::= android|chrome_os|google_sync|ios|linux|mac_os|windows
<DeviceUserID> ::= devices/<String>/deviceUsers/<String>
<DomainAlias> ::= <String>
<DomainName> ::= <String>(.<String>)+
<DriveFileACLRole> ::=
        commenter|
        contentmanager|fileorganizer|
        contributor|editor|writer|
        manager|organizer|owner|
        reader|viewer
<DriveFileACLType> ::= anyone|domain|group|user
<DriveFileID> ::= <String>
<DriveFileURL> ::=
        https://drive.google.com/open?id=<DriveFileID>
        https://drive.google.com/drive/files/<DriveFileID>
        https://drive.google.com/drive/folders/<DriveFileID>
        https://drive.google.com/drive/folders/<DriveFileID>?resourcekey=<String>
        https://drive.google.com/file/d/<DriveFileID>/<String>
        https://docs.google.com/document/d/<DriveFileID>/<String>
        https://docs.google.com/drawings/d/<DriveFileID>/<String>
        https://docs.google.com/forms/d/<DriveFileID>/<String>
        https://docs.google.com/presentation/d/<DriveFileID>/<String>
        https://docs.google.com/spreadsheets/d/<DriveFileID>/<String>
<DriveFileItem> ::= <DriveFileID>|<DriveFileURL>
<DriveFolderID> ::= <String>
<DriveFileName> ::= <String>
<DriveFolderName> ::= <String>
<DriveFolderPath> ::= <String>(/<String>)*
<DriveFilePermission> ::=
        anyone;<DriveFileACLRole>|
        anyonewithlink;<DriveFileACLRole>|
        domain:<DomainName>;<DriveFileACLRole>|
        domainwithlink:<DomainName>;<DriveFileACLRole>|
        group:<EmailAddress>;<DriveFileACLRole>|
        user:<EmailAddress>;<DriveFileACLRole>
<DriveFilePermissionID> ::= anyone|anyonewithlink|id:<String>
<DriveFilePermissionIDorEmail> ::= <DriveFilePermissionID>|<EmailAddress>
<DriveFileRevisionID> ::= <String>
<EmailAddress> ::= <String>@<DomainName>
<EmailItem> ::= <EmailAddress>|<UniqueID>|<String>
<EmailReplacement> ::= <String>
<EventID> ::= <String>
<EventName> ::= <String>
<ExportItem> ::= <UniqueID>|<String>
<ExportStatus> ::= completed|failed|inprogrsss
<FeatureName> ::= <String>
<FieldName> ::= <String>
<FileName> ::= <String>
<FileNamePattern> ::= <String>
<FilterID> ::= <String>
<FloorName> ::= <String>
<GroupItem> ::= <EmailAddress>|<UniqueID>|<String>
<GroupRole> ::= owner|manager|member
<GroupMemberType> ::= customer|group|user
<GuardianItem> ::= <EmailAddress>|<UniqueID>|<String>
<GuardianInvitationID> ::= <String>
<HoldItem> ::= <UniqueID>|<String>
<HostName> ::= <String>
<iCalUID> ::= <String>
<JSONData> ::= (json [charset <Charset>] <String>) | (json file <FileName> [charset <Charset>]) |
<Key> ::= <String>
<LabelID> ::= Label_<String>
<LabelName> ::= <String>
<LabelReplacement> ::= <String>
<LookerStudioAssetID> ::= <String>
<LookerStudioPermission> ::=
        user:<EmailAddress>|
        group:<EmailAddress>|
        domain:<DomainName>|
        serviceAccount:<EmailAddress>
<Marker> ::= <String>
<MatterItem> ::= <UniqueID>|<String>
<MatterState> ::= open|closed|deleted
<MeetConferenceName> ::= conferenceRecords/<String>
<MeetSpaceName> ::= spaces/<String> | <String>
<MessageContent> ::=
        (message|textmessage|htmlmessage <String>)|
        (file|textfile|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
<MessageID> ::= <String>
<Namespace> ::= <String>
<NotesName> ::= notes/<String>
<NotifyMessageContent> ::=
        (message|textmessage|htmlmessage <String>)|
        (file|textfile|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
<NumberOfSeats> ::= <Number>
<OrgUnitID> ::= id:<String>
<OrgUnitPath> ::= /|(/<String>)+
<OrgUnitItem> ::= <OrgUnitID>|<OrgUnitPath>
<OtherContactsResourceName> ::= otherContacts/<String>
<ParameterKey> ::= <String>
<ParameterValue> ::= <String>
<Password> ::= <String>
<PeopleResourceName> ::= people/<String>
<PrinterID> ::= <String>
<ProjectID> ::= <String>
        Must match this Python Regular Expression: [a-z][a-z0-9-]{4,28}[a-z0-9]
<ProjectName> ::= <String>
        Must match this Python Regular Expression: [a-zA-Z0-9 '"!-]{4,30}
<PropertyKey> ::= <String>
<PropertyValue> ::= <String>
<QueryAlert> ::= <String>
        See: https://developers.google.com/admin-sdk/alertcenter/guides/query-filters
<QueryBrowser> ::= <String>
        See: https://support.google.com/chrome/a/answer/9681204#retrieve_all_chrome_devices_for_an_account
<QueryBrowserToken> ::= <String>
        See: https://support.google.com/chrome/a/answer/9949706?ref_topic=9301744
<QueryCalendar> ::= <String>
<QueryCEL> ::= <String>
        See: https://cloud.google.com/access-context-manager/docs/custom-access-level-spec
<QueryContact> ::= <String>
        See: https://developers.google.com/google-apps/contacts/v3/reference#contacts-query-parameters-reference
<QueryCrOS> ::= <String>
        See: https://support.google.com/chrome/a/answer/1698333
<QueryDevice> ::= <String>
        See: https://support.google.com/a/answer/7549103
<QueryDriveFile> ::= <String>
        See: https://developers.google.com/drive/api/v3/search-files
<QueryDynamicGroup> ::= <String>
        See: https://cloud.google.com/identity/docs/reference/rest/v1/groups#dynamicgroupquery
<QueryGmail> ::= <String>
        See: https://support.google.com/mail/answer/7190
<QueryGroup> ::= <String>
        See: https://developers.google.com/admin-sdk/directory/v1/guides/search-groups
<QueryMemberRestrictions> ::= <String>
        See: https://cloud.google.com/identity/docs/reference/rest/v1beta1/SecuritySettings#MemberRestriction
<QueryMobile> ::= <String>
        See: https://support.google.com/a/answer/7549103
<QueryTeamDrive> ::= <String>
        See: https://developers.google.com/drive/api/v3/search-parameters
<QueryUser> ::= <String>
        See: https://developers.google.com/admin-sdk/directory/v1/guides/search-users
<QueryVaultCorpus> ::= <String>
        See: https://developers.google.com/vault/reference/rest/v1/matters.holds#CorpusQuery
<RequestID> ::= <String>
<ResellerID> ::= <String>
<ResourceID> ::= <String>
<SchemaName> ::= <String>
<SchemaNameField> ::= <SchemaName>.<FieldName>
<Section> ::= <String>
<SendAsContent> ::=
        (sig|signature|htmlsig <String>)|
        (file|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
<SerialNumber> ::= <String>
<ServiceAccountName> ::= <String>
        Must match this Python Regular Expression: [a-z][a-z0-9-]{4,28}[a-z0-9]
<ServiceAccountDisplayName> ::= <String>
        Maximum of 100 characters
<ServiceAccountDescrition> ::= <String>
       Maximum of 256 chcracters
<ServiceAccountEmail> ::= <ServiceAccountName>@<ProjectID>.iam.gserviceaccount.com
<ServiceAccountUniqueID> ::= <Number>
<ServiceAccountKey> ::= <String>
<SheetEntity> ::= <String>|id:<Number>
<SignatureContent> ::=
        (<String>)|
        (file|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
<SiteACLScope> ::=
        <EmailAddress>|user:<EmailAddress>|group:<EmailAddress>|
        domain:<DomainName>|domain|default
<SiteItem> ::= [<DomainName>/]<SiteName>
<S/MIMEID> ::= <String>
<SMTPHostName> ::= <String>
<StudentItem> ::= <EmailAddress>|<UniqueID>|<String>
<SharedDriveACLRole> ::=
        commenter|
        contentmanager|fileorganizer|
        contributor|editor|writer|
        manager|organizer|owner|
        reader|viewer
<SharedDriveID> ::= <String>
<SharedDriveName> ::= <String>
<StorageBucketName> ::= <String>
<StorageObjectName> ::= <String>
<StorageBucketObjectName> ::=
        https://storage.cloud.google.com/<StorageBucketName>/<StorageObjectName>|
        https://storage.googleapis.com/<StorageBucketName>/<StorageObjectName>|
        gs://<StorageBucketName>/<StorageObjectName>|
        <StorageBucketName>/<StorageObjectName>
<Tag> ::= <String>
<TakeoutBucketName> ::= takeout-export-[a-f,0-9,-]*
<TaskID> ::= <String>
<TaskListID> ::= <String>
<TaskListTitle> ::= tltitle:<String>
<TasklistIDTaskID> ::= <TasklistID>/<TaskID>
<ThreadID> ::= <String>
<TimeZone> ::= <String>
        See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
<Title> ::= <String>
<ToDriveAttribute> ::=
        (tdaddsheet [<Boolean>])|
        (tdalert <EmailAddress>)*|
        (tdbackupsheet (id:<Number>)|<String>)|
        (tdcellnumberformat text|number)|
        (tdcellwrap clip|overflow|wrap)|
        (tdclearfilter [<Boolean>])|
        (tdcopysheet (id:<Number>)|<String>)|
        (tddescription <String>)|
        (tdfileid <DriveFileID>)|
        (tdfrom <EmailAddress>)|
        (tdlocalcopy [<Boolean>])|
        (tdlocale <Locale>)|
        (tdnobrowser [<Boolean>])|
        (tdnoemail [<Boolean>])|
        (tdnoescapechar [<Boolean>])|
        (tdnotify [<Boolean>])|
        (tdparent (id:<DriveFolderID>)|<DriveFolderName>)|
        (tdretaintitle [<Boolean>])|
        (tdreturnidonly [<Boolean>])|
        (tdshare <EmailAddress> commenter|reader|writer)*|
        (tdsheet (id:<Number>)|<String>)|
        (tdsheettimestamp [<Boolean>] [tdsheettimeformat <String>])
        (tdsheettitle <String>)|
        (tdsubject <String>)|
        ([tdsheetdaysoffset <Number>] [tdsheethoursoffset <Number>])|
        (tdtimestamp [<Boolean>] [tdtimeformat <String>]
            [tddaysoffset <Number>] [tdhoursoffset <Number>])|
        (tdtimezone <TimeZone>)|
        (tdtitle <String>)|
        (tdupdatesheet [<Boolean>])|
        (tduploadnodata [<Boolean>])|
        (tduser <EmailAddress>)
<TransferID> ::= <String>
<URI> ::= <String>
<URL> ::= <String>
<UserItem> ::= <EmailAddress>|<UniqueID>|<String>
<UserName> ::= <String>
<VacationMessageContent> ::=
        (message|textmessage|htmlmessage <String>)|
        (file|textfile|htmlfile <FileName> [charset <Charset>])|
        (gdoc|ghtml <UserGoogleDoc>)|
        (gcsdoc|gcshtml <StorageBucketObjectName>)
<YouTubeChannelID> ::= <String>
```
