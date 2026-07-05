"""GAM people commands."""

from gamlib import settings as GC
from gam.var import Ent
from gam.cmd.people.contacts import _processPeopleContactPhotos
from gam.cmd.people.domainprofiles import _infoPeople, _printShowPeople


def doInfoDomainPeopleContacts():
  """Print information about domain people contacts."""
  _infoPeople([GC.Values[GC.DOMAIN]], Ent.DOMAIN, 'domaincontact')

# gam print people|peopleprofile [todrive <ToDriveAttribute>*]
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonly|(formatjson [quotechar <Character>])]
# gam show people|peopleprofile
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonlyformatjson]
# gam print domaincontacts|peoplecontacts [todrive <ToDriveAttribute>*]
#	[sources <PeopleSourceName>]
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[allfields|(fields <PeopleFieldNameList>)] [showmetadata]
#	[countsonly|(formatjson [quotechar <Character>])]
# gam show domaincontacts|peoplecontacts
#	[sources <PeopleSourceName>]
#	[query <String>]
#	[mergesources <PeopleMergeSourceName>]
#	[countsonlyformatjson]
def doPrintShowDomainPeopleContacts():
  """Print or show a list of domain people contacts."""
  _printShowPeople('domaincontact')

def doUpdateDomainContactPhoto():
  """Update photo for domain people contacts."""
  _processPeopleContactPhotos(None, 'updateContactPhoto')

# gam get contactphotos <PeopleResourceNameEntity>|<PeopleUserContactSelection>
#	[drivedir|(targetfolder <FilePath>)] [filename <FileNamePattern>]
def doGetDomainContactPhoto():
  """Retrieve photo for domain people contacts."""
  _processPeopleContactPhotos(None, 'getContactPhoto')

# gam delete contactphoto <PeopleResourceNameEntity>|<PeopleUserContactSelection>
def doDeleteDomainContactPhoto():
  """Delete photo for domain people contacts."""
  _processPeopleContactPhotos(None, 'deleteContactPhoto')

# gam <UserTypeEntity> create contactgroup <ContactGroupAttribute>+
#	[(csv [todrive <ToDriveAttribute>*] (addcsvdata <FieldName> <String>)*))| returnidonly]
