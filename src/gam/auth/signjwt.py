''' Use Google Application Default Credentials '''
import datetime
import json

from google.auth import _helpers, default
import google.oauth2.service_account
from googleapiclient.discovery import build

from gam import gapi

_DEFAULT_TOKEN_LIFETIME_SECS = 3600  # 1 hour in seconds
_GOOGLE_OAUTH2_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class JWTCredentials(google.auth.jwt.Credentials):
    ''' Class used for DASA '''
    def _make_jwt(self):
        now = _helpers.utcnow()
        lifetime = datetime.timedelta(seconds=self._token_lifetime)
        expiry = now + lifetime
        payload = {
            "iss": self._issuer,
            "sub": self._subject,
            "iat": _helpers.datetime_to_secs(now),
            "exp": _helpers.datetime_to_secs(expiry),
        }
        if self._audience:
            payload["aud"] = self._audience
        payload.update(self._additional_claims)
        jwt = self._signer.sign(payload)
        return jwt, expiry


class Credentials(google.oauth2.service_account.Credentials):
    ''' Class used for DwD '''

    def _make_authorization_grant_assertion(self):
        now = _helpers.utcnow()
        lifetime = datetime.timedelta(seconds=_DEFAULT_TOKEN_LIFETIME_SECS)
        expiry = now + lifetime
        payload = {
            "iat": _helpers.datetime_to_secs(now),
            "exp": _helpers.datetime_to_secs(expiry),
            "iss": self._service_account_email,
            "aud": _GOOGLE_OAUTH2_TOKEN_ENDPOINT,
            "scope": _helpers.scopes_to_string(self._scopes or ()),
        }

        payload.update(self._additional_claims)

        # The subject can be a user email for domain-wide delegation.
        if self._subject:
            payload.setdefault("sub", self._subject)
        token = self._signer(payload)
        return token


class SignJwt(google.auth.crypt.Signer):
    ''' Signer class for SignJWT '''
    def __init__(self, service_account_info):
        self.service_account_email = service_account_info['client_email']
        self.name = f'projects/-/serviceAccounts/{self.service_account_email}'
        self._key_id = None

    @property  # type: ignore
    def key_id(self):
        return self._key_id


    def sign(self, message):
        ''' Call IAM Credentials SignJWT API to get our signed JWT '''
        credentials, _ = default()
        iamc = build('iamcredentials', 'v1', credentials=credentials)
        response = gapi.call(iamc.projects().serviceAccounts(),
                             'signJwt',
                             name=self.name,
                             body={'payload': json.dumps(message)})
        signed_jwt = response.get('signedJwt')
        return signed_jwt
