"""GAM People API contacts management."""


from gam.cmd.contacts import (
    PEOPLE_ADDRESSES,
    PEOPLE_BIOGRAPHIES,
    PEOPLE_BIRTHDAYS,
    PEOPLE_CALENDAR_URLS,
    PEOPLE_CLIENT_DATA,
    PEOPLE_COVER_PHOTOS,
    PEOPLE_EMAIL_ADDRESSES,
    PEOPLE_EVENTS,
    PEOPLE_EXTERNAL_IDS,
    PEOPLE_FILE_ASES,
    PEOPLE_GENDERS,
    PEOPLE_IM_CLIENTS,
    PEOPLE_INTERESTS,
    PEOPLE_LOCALES,
    PEOPLE_LOCATIONS,
    PEOPLE_MEMBERSHIPS,
    PEOPLE_METADATA,
    PEOPLE_MISC_KEYWORDS,
    PEOPLE_NAMES,
    PEOPLE_NICKNAMES,
    PEOPLE_OCCUPATIONS,
    PEOPLE_ORGANIZATIONS,
    PEOPLE_PHONE_NUMBERS,
    PEOPLE_PHOTOS,
    PEOPLE_RELATIONS,
    PEOPLE_SIP_ADDRESSES,
    PEOPLE_SKILLS,
    PEOPLE_UPDATE_TIME,
    PEOPLE_URLS,
    PEOPLE_USER_DEFINED
)



from gam.cmd.contacts import (
    PEOPLE_ADDRESSES,
    PEOPLE_BIOGRAPHIES,
    PEOPLE_BIRTHDAYS,
    PEOPLE_CALENDAR_URLS,
    PEOPLE_CLIENT_DATA,
    PEOPLE_COVER_PHOTOS,
    PEOPLE_EMAIL_ADDRESSES,
    PEOPLE_EVENTS,
    PEOPLE_EXTERNAL_IDS,
    PEOPLE_FILE_ASES,
    PEOPLE_GENDERS,
    PEOPLE_IM_CLIENTS,
    PEOPLE_INTERESTS,
    PEOPLE_LOCALES,
    PEOPLE_LOCATIONS,
    PEOPLE_MEMBERSHIPS,
    PEOPLE_METADATA,
    PEOPLE_MISC_KEYWORDS,
    PEOPLE_NAMES,
    PEOPLE_NICKNAMES,
    PEOPLE_OCCUPATIONS,
    PEOPLE_ORGANIZATIONS,
    PEOPLE_PHONE_NUMBERS,
    PEOPLE_PHOTOS,
    PEOPLE_RELATIONS,
    PEOPLE_SIP_ADDRESSES,
    PEOPLE_SKILLS,
    PEOPLE_UPDATE_TIME,
    PEOPLE_URLS,
    PEOPLE_USER_DEFINED
)


PEOPLE_CONTACT_SELECT_ARGUMENTS = {
  'query', 'contactgroup', 'selectcontactgroup',
  'maincontacts', 'selectmaincontacts',
  'othercontacts', 'selectothercontacts',
  'emailmatchpattern', 'emailmatchtype',
  }
PEOPLE_CONTACT_DEPRECATED_SELECT_ARGUMENTS = {
  'orderby', 'basic', 'thin', 'full', 'showdeleted',
  }

PEOPLE_OTHERCONTACT_SELECT_ARGUMENTS = {'query', 'emailmatchpattern', 'emailmatchtype'}

PEOPLE_CONTACT_OBJECT_KEYS = {
  'addresses': 'type',
  'calendarUrls': 'type',
  'emailAddresses': 'type',
  'events': 'type',
  'externalIds': 'type',
  'genders': 'value',
  'imClients': 'type',
  'locations': 'type',
  'miscKeywords': 'type',
  'nicknames': 'type',
  'organizations': 'type',
  'relations': 'type',
  'urls': 'type',
  'userDefined': 'key',
  }

PEOPLE_FIELDS_CHOICE_MAP = {
  'additionalname': PEOPLE_NAMES,
  'address': PEOPLE_ADDRESSES,
  'addresses': PEOPLE_ADDRESSES,
  'ageranges': 'ageRanges',
  'billinginfo': PEOPLE_MISC_KEYWORDS,
  'biography': PEOPLE_BIOGRAPHIES,
  'biographies': PEOPLE_BIOGRAPHIES,
  'birthday': PEOPLE_BIRTHDAYS,
  'birthdays': PEOPLE_BIRTHDAYS,
  'calendar': PEOPLE_CALENDAR_URLS,
  'calendars': PEOPLE_CALENDAR_URLS,
  'calendarurls': PEOPLE_CALENDAR_URLS,
  'clientdata': PEOPLE_CLIENT_DATA,
  'coverphotos': PEOPLE_COVER_PHOTOS,
  'directoryserver': PEOPLE_MISC_KEYWORDS,
  'email': PEOPLE_EMAIL_ADDRESSES,
  'emails': PEOPLE_EMAIL_ADDRESSES,
  'emailaddresses': PEOPLE_EMAIL_ADDRESSES,
  'event': PEOPLE_EVENTS,
  'events': PEOPLE_EVENTS,
  'externalid': PEOPLE_EXTERNAL_IDS,
  'externalids': PEOPLE_EXTERNAL_IDS,
  'familyname': PEOPLE_NAMES,
  'fileas': PEOPLE_FILE_ASES,
  'firstname': PEOPLE_NAMES,
  'gender': PEOPLE_GENDERS,
  'genders': PEOPLE_GENDERS,
  'givenname': PEOPLE_NAMES,
  'hobby': PEOPLE_INTERESTS,
  'hobbies': PEOPLE_INTERESTS,
  'im': PEOPLE_IM_CLIENTS,
  'ims': PEOPLE_IM_CLIENTS,
  'imclients': PEOPLE_IM_CLIENTS,
  'initials': PEOPLE_NICKNAMES,
  'interests': PEOPLE_INTERESTS,
  'jot': PEOPLE_MISC_KEYWORDS,
  'jots': PEOPLE_MISC_KEYWORDS,
  'language': PEOPLE_LOCALES,
  'languages': PEOPLE_LOCALES,
  'lastname': PEOPLE_NAMES,
  'locales': PEOPLE_LOCALES,
  'location': PEOPLE_LOCATIONS,
  'locations': PEOPLE_LOCATIONS,
  'maidenname': PEOPLE_NAMES,
  'memberships': PEOPLE_MEMBERSHIPS,
  'metadata': PEOPLE_METADATA,
  'middlename': PEOPLE_NAMES,
  'mileage': PEOPLE_MISC_KEYWORDS,
  'misckeywords': PEOPLE_MISC_KEYWORDS,
  'name': PEOPLE_NAMES,
  'names': PEOPLE_NAMES,
  'nickname': PEOPLE_NICKNAMES,
  'nicknames': PEOPLE_NICKNAMES,
  'note': PEOPLE_BIOGRAPHIES,
  'notes': PEOPLE_BIOGRAPHIES,
  'occupation': PEOPLE_OCCUPATIONS,
  'occupations': PEOPLE_OCCUPATIONS,
  'organization': PEOPLE_ORGANIZATIONS,
  'organizations': PEOPLE_ORGANIZATIONS,
  'organisation': PEOPLE_ORGANIZATIONS,
  'organisations': PEOPLE_ORGANIZATIONS,
  'phone': PEOPLE_PHONE_NUMBERS,
  'phones': PEOPLE_PHONE_NUMBERS,
  'phonenumbers': PEOPLE_PHONE_NUMBERS,
  'photo': PEOPLE_PHOTOS,
  'photos': PEOPLE_PHOTOS,
  'prefix': PEOPLE_NAMES,
  'priority': PEOPLE_MISC_KEYWORDS,
  'relation': PEOPLE_RELATIONS,
  'relations': PEOPLE_RELATIONS,
  'sensitivity': PEOPLE_MISC_KEYWORDS,
  'shortname': PEOPLE_NICKNAMES,
  'sipaddress': PEOPLE_SIP_ADDRESSES,
  'sipaddresses': PEOPLE_SIP_ADDRESSES,
  'skills': PEOPLE_SKILLS,
  'subject': PEOPLE_MISC_KEYWORDS,
  'suffix': PEOPLE_NAMES,
  'updated': PEOPLE_UPDATE_TIME,
  'updatetime': PEOPLE_UPDATE_TIME,
  'urls': PEOPLE_URLS,
  'userdefined': PEOPLE_USER_DEFINED,
  'userdefinedfield': PEOPLE_USER_DEFINED,
  'userdefinedfields': PEOPLE_USER_DEFINED,
  'website': PEOPLE_URLS,
  'websites': PEOPLE_URLS,
  }

PEOPLE_OTHER_CONTACTS_FIELDS_CHOICE_MAP = {
  'email': PEOPLE_EMAIL_ADDRESSES,
  'emails': PEOPLE_EMAIL_ADDRESSES,
  'emailaddresses': PEOPLE_EMAIL_ADDRESSES,
  'metadata': PEOPLE_METADATA,
  'names': PEOPLE_NAMES,
  'phone': PEOPLE_PHONE_NUMBERS,
  'phones': PEOPLE_PHONE_NUMBERS,
  'phonenumbers': PEOPLE_PHONE_NUMBERS,
  'photo': PEOPLE_PHOTOS,
  'photos': PEOPLE_PHOTOS,
  }

PEOPLE_CONTACTS_DEFAULT_FIELDS = ['names', 'emailaddresses', 'phonenumbers']

PEOPLE_ORDERBY_CHOICE_MAP = {
  'firstname': 'FIRST_NAME_ASCENDING',
  'lastname': 'LAST_NAME_ASCENDING',
  'lastmodified': 'LAST_MODIFIED_',
  }

CONTACTGROUPS_MYCONTACTS_ID = 'contactGroups/myContacts'
CONTACTGROUPS_MYCONTACTS_NAME = 'My Contacts'

# gam <UserTypeEntity> copy othercontacts
#	<OtherContactResourceNameEntity>|<OtherContactSelection>
PEOPLE_PROFILE_SOURCETYPE_CHOICE_MAP = {
  'account': 'ACCOUNT',
  'accounts': 'ACCOUNT',
  'domain': 'DOMAIN_PROFILE',
  'domains': 'DOMAIN_PROFILE',
  'profile': 'PROFILE',
  'profiles': 'PROFILE',
  }

# gam <UserTypeEntity> print peopleprofile [todrive <ToDriveAttribute>*]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[sources <PeopleProfileSourceNameList>]
#	[formatjson [quotechar <Character>]]
# gam <UserTypeEntity> show peopleprofile
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[sources <PeopleProfileSourceNameList>]
#	[formatjson]
PEOPLE_GROUP_TIME_OBJECTS = {'updateTime'}

PEOPLE_CONTACTGROUPS_FIELDS_CHOICE_MAP = {
  'clientdata': 'clientData',
  'grouptype': 'groupType',
  'membercount': 'memberCount',
  'metadata': 'metadata',
  'name': 'name',
  }

PEOPLE_CONTACTGROUPS_DEFAULT_FIELDS = ['name', 'metadata', 'grouptype', 'membercount']

# gam <UserTypeEntity> info contactgroups <PeopleContactGroupEntity>
#	[allfields|(fields <PeoplaContactGroupFieldList>)] [showmetadata]
#	[formatjson]
