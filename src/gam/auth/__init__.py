"""Authentication/Credentials general purpose and convenience methods."""

import json
import os
import time

from google.auth.jwt import Credentials as JWTCredentials

from gam.auth import oauth
from gam.var import _FN_OAUTH2_TXT
from gam.var import GC_OAUTH2_TXT
from gam.var import GC_Values

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


def get_admin_credentials(api=None):
    """Gets oauth.Credentials that are authenticated as the domain's admin user."""
    credential_file = get_admin_credentials_filename()
    if not os.path.isfile(credential_file):
        raise oauth.InvalidCredentialsFileError
    with open(credential_file, 'r') as f:
        creds_data = json.load(f)
    if 'token' in creds_data:
        return oauth.Credentials.from_credentials_file(credential_file)
    elif 'private_key' in creds_data:
        audience = f'https://{api}.googleapis.com/'
        return JWTCredentials.from_service_account_info(creds_data,
                                                        audience=audience)
