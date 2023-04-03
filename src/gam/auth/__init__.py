"""Authentication/Credentials general purpose and convenience methods."""

import json
import os

from google.auth.jwt import Credentials as JWTCredentials

from gam import utils

from gam.auth import oauth
from gam.auth import signjwt
from gam.var import _FN_OAUTH2_TXT
from gam.var import _FN_OAUTH2SERVICE_JSON
from gam.var import GC_OAUTH2_TXT
from gam.var import GC_OAUTH2SERVICE_JSON
from gam.var import GC_ENABLE_DASA
from gam.var import GC_Values

yubikey = utils.LazyLoader('yubikey', globals(), 'gam.auth.yubikey')
# TODO: Move logic that determines file name into this module. We should be able
# to discover the file location without accessing a private member or waiting
# for a global initialization.


def get_admin_credentials_filename():
    """Gets the name of the file that stores the admin account credentials."""
    # If the environment globals are loaded, use the set global value. It may have
    # some custom name in it. Otherwise, just use the default name.
    if GC_Values[GC_ENABLE_DASA]:
        return GC_Values[GC_OAUTH2SERVICE_JSON] if GC_Values[GC_OAUTH2SERVICE_JSON] else _FN_OAUTH2SERVICE_JSON
    return GC_Values[GC_OAUTH2_TXT] if GC_Values[GC_OAUTH2_TXT] else _FN_OAUTH2_TXT


def get_admin_credentials(api=None):
    """Gets oauth.Credentials that are authenticated as the domain's admin user."""
    credential_file = get_admin_credentials_filename()
    if not os.path.isfile(credential_file):
        raise oauth.InvalidCredentialsFileError
    with open(credential_file) as f:
        creds_data = json.load(f)
    # Validate that enable DASA matches content of authorization file
    if GC_Values[GC_ENABLE_DASA] and creds_data.get('type') == 'service_account':
        audience = f'https://{api}.googleapis.com/'
        key_type = creds_data.get('key_type', 'default')
        if key_type == 'default':
            return JWTCredentials.from_service_account_info(creds_data,
                                                            audience=audience)
        if key_type == 'yubikey':
            yksigner = yubikey.YubiKey(creds_data)
            return JWTCredentials._from_signer_and_info(yksigner,
                creds_data,
                audience=audience)
        if key_type == 'signjwt':
            sjsigner = signjwt.SignJwt(creds_data)
            return signjwt.JWTCredentials._from_signer_and_info(sjsigner,
                    creds_data,
                    audience=audience)
    elif not GC_Values[GC_ENABLE_DASA] and 'token' in creds_data:
        return oauth.Credentials.from_credentials_file(credential_file)
    else:
        raise oauth.InvalidCredentialsFileError
