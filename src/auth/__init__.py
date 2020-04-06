"""Authentication/Credentials general purpose and convenience methods."""

import transport
from var import _FN_OAUTH2_TXT
from var import GC_OAUTH2_TXT
from var import GC_Values
from . import oauth
# TODO: Move logic that determines file name into this module. We should be able
# to discover the file location without accessing a private member or waiting
# for a global initialization.
DEFAULT_OAUTH_STORAGE_FILE = _FN_OAUTH2_TXT


def get_admin_credentials_filename():
    """Gets the name of the file that stores the admin account credentials."""
    # If the environment globals are loaded, use the set global value. It may have
    # some custom name in it. Otherwise, just use the default name.
    if GC_Values[GC_OAUTH2_TXT]:
        return GC_Values[GC_OAUTH2_TXT]
    return DEFAULT_OAUTH_STORAGE_FILE


def get_admin_credentials():
    """Gets oauth.Credentials that are authenticated as the domain's admin user."""
    credential_file = get_admin_credentials_filename()
    return oauth.Credentials.from_credentials_file(credential_file)
