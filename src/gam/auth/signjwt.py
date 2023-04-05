''' Use Google Application Default Credentials '''
import datetime
import json

import google.auth
from google.auth._helpers import datetime_to_secs, scopes_to_string, utcnow
import google.oauth2.service_account

import gam
from gam import controlflow
from gam import gapi
from gam import transport
from gam.var import GM_Globals, GM_CACHE_DIR

_DEFAULT_TOKEN_LIFETIME_SECS = 3600  # 1 hour in seconds
_GOOGLE_OAUTH2_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class JWTCredentials(google.auth.jwt.Credentials):
    ''' Class used for DASA '''
    def _make_jwt(self):
        now = utcnow()
        lifetime = datetime.timedelta(seconds=self._token_lifetime)
        expiry = now + lifetime
        payload = {
            "iss": self._issuer,
            "sub": self._subject,
            "iat": datetime_to_secs(now),
            "exp": datetime_to_secs(expiry),
        }
        if self._audience:
            payload["aud"] = self._audience
        payload.update(self._additional_claims)
        jwt = self._signer.sign(payload)
        return jwt, expiry


class Credentials(google.oauth2.service_account.Credentials):
    ''' Class used for DwD '''

    def _make_authorization_grant_assertion(self):
        now = utcnow()
        lifetime = datetime.timedelta(seconds=_DEFAULT_TOKEN_LIFETIME_SECS)
        expiry = now + lifetime
        payload = {
            "iat": datetime_to_secs(now),
            "exp": datetime_to_secs(expiry),
            "iss": self._service_account_email,
            "aud": _GOOGLE_OAUTH2_TOKEN_ENDPOINT,
            "scope": scopes_to_string(self._scopes or ()),
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
        request = transport.create_request()
        try:
            credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/iam'],
                                                 request=request)
        except google.auth.exceptions.DefaultCredentialsError as e:
            controlflow.system_error_exit(2, e)
        httpObj = transport.AuthorizedHttp(
                credentials,
                transport.create_http(cache=GM_Globals[GM_CACHE_DIR]))
        iamc = gam.getService('iamcredentials', httpObj)
        response = gapi.call(iamc.projects().serviceAccounts(),
                             'signJwt',
                             name=self.name,
                             body={'payload': json.dumps(message)})
        signed_jwt = response.get('signedJwt')
        return signed_jwt
