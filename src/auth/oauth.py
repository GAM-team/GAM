"""OAuth2.0 user credentials."""

import datetime
import json
import os
import re
import threading
from urllib.parse import urlencode

from filelock import FileLock
import google_auth_oauthlib.flow
import google.oauth2.credentials
import google.oauth2.id_token

import fileutils
import transport
from var import GAM_INFO
from var import GM_Globals
from var import GM_WINDOWS
import utils

MESSAGE_CONSOLE_AUTHORIZATION_PROMPT = ('\nGo to the following link in your '
                                        'browser:\n\n\t{url}\n')
MESSAGE_CONSOLE_AUTHORIZATION_CODE = 'Enter verification code: '
MESSAGE_LOCAL_SERVER_AUTHORIZATION_PROMPT = ('\nYour browser has been opened to'
                                             ' visit:\n\n\t{url}\n\nIf your '
                                             'browser is on a different machine'
                                             ' then press CTRL+C and create a '
                                             'file called nobrowser.txt in the '
                                             'same folder as GAM.\n')
MESSAGE_LOCAL_SERVER_SUCCESS = ('The authentication flow has completed. You may'
                                ' close this browser window and return to GAM.')


class CredentialsError(Exception):
  """Base error class."""
  pass


class InvalidCredentialsFileError(CredentialsError):
  """Error raised when a file cannot be opened into a credentials object."""
  pass


class EmptyCredentialsFileError(InvalidCredentialsFileError):
  """Error raised when a credentials file contains no content."""
  pass


class InvalidClientSecretsFileFormatError(CredentialsError):
  """Error raised when a client secrets file format is invalid."""
  pass


class InvalidClientSecretsFileError(CredentialsError):
  """Error raised when client secrets file cannot be read."""
  pass


class Credentials(google.oauth2.credentials.Credentials):
  """Google OAuth2.0 Credentials with GAM-specific properties and methods."""

  DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

  def __init__(self,
               token,
               refresh_token=None,
               id_token=None,
               token_uri=None,
               client_id=None,
               client_secret=None,
               scopes=None,
               quota_project_id=None,
               expiry=None,
               id_token_data=None,
               filename=None):
    """A thread-safe OAuth2.0 credentials object.

    Credentials adds additional utility properties and methods to a
    standard OAuth2.0 credentials object. When used to store credentials on
    disk, it implements a file lock to avoid collision during writes.

    Args:
      token: Optional String, The OAuth 2.0 access token. Can be None if refresh
        information is provided.
      refresh_token: String, The OAuth 2.0 refresh token. If specified,
        credentials can be refreshed.
      id_token: String, The Open ID Connect ID Token.
      token_uri: String, The OAuth 2.0 authorization server's token endpoint
        URI. Must be specified for refresh, can be left as None if the token can
        not be refreshed.
      client_id: String, The OAuth 2.0 client ID. Must be specified for refresh,
        can be left as None if the token can not be refreshed.
      client_secret: String, The OAuth 2.0 client secret. Must be specified for
        refresh, can be left as None if the token can not be refreshed.
      scopes: Sequence[str], The scopes used to obtain authorization.
        This parameter is used by :meth:`has_scopes`. OAuth 2.0 credentials can
          not request additional scopes after authorization. The scopes must be
          derivable from the refresh token if refresh information is provided
          (e.g. The refresh token scopes are a superset of this or contain a
          wild card scope like
            'https://www.googleapis.com/auth/any-api').
      quota_project_id: String, The project ID used for quota and billing. This
        project may be different from the project used to create the
        credentials.
      expiry: datetime.datetime, The time at which the provided token will
        expire.
      id_token_data: Oauth2.0 ID Token data which was previously fetched for
        this access token against the google.oauth2.id_token library.
      filename: String, Path to a file that will be used to store the
        credentials. If provided, a lock file of the same name and a ".lock"
          extension will be created for concurrency controls. Note: New
            credentials are not saved to disk until write() or refresh() are
            called.

    Raises:
      TypeError: If id_token_data is not the required dict type.
    """
    super(Credentials, self).__init__(
        token=token,
        refresh_token=refresh_token,
        id_token=id_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
        quota_project_id=quota_project_id)

    # Load data not restored by the super class
    self.expiry = expiry
    if id_token_data and not isinstance(id_token_data, dict):
      raise TypeError(f'Expected type id_token_data dict but received '
                      f'{type(id_token_data)}')
    self._id_token_data = id_token_data.copy() if id_token_data else None

    # If a filename is provided, use a lock file to control concurrent access
    # to the resource. If no filename is provided, use a thread lock that has
    # the same interface as FileLock in order to simplify the implementation.
    if filename:
      # Convert relative paths into absolute
      self._filename = os.path.abspath(filename)
      lock_file = os.path.abspath(f'{self._filename}.lock')
      self._lock = FileLock(lock_file)
    else:
      self._filename = None
      self._lock = _FileLikeThreadLock()

  # Use a property to prevent external mutation of the filename.
  @property
  def filename(self):
    return self._filename

  @classmethod
  def from_authorized_user_info(cls, info, filename=None):
    """Generates Credentials from JSON containing authorized user info.

    Args:
      info: Dict, authorized user info in Google format.
      filename: String, the filename used to store these credentials on disk. If
        no filename is provided, the credentials will not be saved to disk.

    Raises:
      ValueError: If missing fields are detected in the info.
    """
    # We need all of these keys
    keys_needed = set(('client_id', 'client_secret'))
    # We need 1 or more of these keys
    keys_need_one_of = set(('refresh_token', 'auth_token', 'token'))
    missing = keys_needed.difference(info.keys())
    has_one_of = set(info) & keys_need_one_of
    if missing or not has_one_of:
      raise ValueError(
          'Authorized user info was not in the expected format, missing '
          f'fields {", ".join(missing)} and one of '
          f'{", ".join(keys_need_one_of)}.')

    expiry = info.get('token_expiry')
    if expiry:
      # Convert the raw expiry to datetime
      expiry = datetime.datetime.strptime(expiry, Credentials.DATETIME_FORMAT)
    id_token_data = info.get('decoded_id_token')

    # Provide backwards compatibility with field names when loading from JSON.
    # Some field names may be different, depending on when/how the credentials
    # were pickled.
    return cls(
        token=info.get('token', info.get('auth_token', '')),
        refresh_token=info.get('refresh_token', ''),
        id_token=info.get('id_token_jwt', info.get('id_token')),
        token_uri=info.get('token_uri'),
        client_id=info['client_id'],
        client_secret=info['client_secret'],
        scopes=info.get('scopes'),
        quota_project_id=info.get('quota_project_id'),
        expiry=expiry,
        id_token_data=id_token_data,
        filename=filename)

  @classmethod
  def from_google_oauth2_credentials(cls, credentials, filename=None):
    """Generates Credentials from a google.oauth2.Credentials object."""
    info = json.loads(credentials.to_json())
    # Add properties which are not exported with the native to_json() output.
    info['id_token'] = credentials.id_token
    if credentials.expiry:
      info['token_expiry'] = credentials.expiry.strftime(
          Credentials.DATETIME_FORMAT)
    info['quota_project_id'] = credentials.quota_project_id

    return cls.from_authorized_user_info(info, filename=filename)

  @classmethod
  def from_credentials_file(cls, filename):
    """Generates Credentials from a stored Credentials file.

    The same file will be used to save the credentials when the access token is
    refreshed.

    Args:
      filename: String, the name of a file containing JSON credentials to load.
        The same filename will be used to save credentials back to disk.

    Returns:
      The credentials loaded from disk.

    Raises:
      InvalidCredentialsFileError: When the credentials file cannot be opened.
      EmptyCredentialsFileError: When the provided file contains no credentials.
    """
    file_content = fileutils.read_file(
        filename, continue_on_error=True, display_errors=False)
    if file_content is None:
      raise InvalidCredentialsFileError(f'File {filename} could not be opened')
    info = json.loads(file_content)
    if not info:
      raise EmptyCredentialsFileError(
          f'File {filename} contains no credential data')

    try:
      # We read the existing data from the passed in file, but we also want to
      # save future data/tokens in the same place.
      return cls.from_authorized_user_info(info, filename=filename)
    except ValueError as e:
      raise InvalidCredentialsFileError(str(e))

  @classmethod
  def from_client_secrets(cls,
                          client_id,
                          client_secret,
                          scopes,
                          access_type='offline',
                          login_hint=None,
                          filename=None,
                          use_console_flow=False):
    """Runs an OAuth Flow from client secrets to generate credentials.

    Args:
      client_id: String, The OAuth2.0 Client ID.
      client_secret: String, The OAuth2.0 Client Secret.
      scopes: Sequence[str], A list of scopes to include in the credentials.
      access_type: String, 'offline' or 'online'.  Indicates whether your
        application can refresh access tokens when the user is not present at
        the browser. Valid parameter values are online, which is the default
        value, and offline.  Set the value to offline if your application needs
        to refresh access tokens when the user is not present at the browser.
        This is the method of refreshing access tokens described later in this
        document. This value instructs the Google authorization server to return
        a refresh token and an access token the first time that your application
        exchanges an authorization code for tokens.
      login_hint: String, The email address that will be displayed on the Google
        login page as a hint for the user to login to the correct account.
      filename: String, the path to a file to use to save the credentials.
      use_console_flow: Boolean, True if the authentication flow should be run
        strictly from a console; False to launch a browser for authentication.

    Returns:
      Credentials
    """
    client_config = {
        'installed': {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uris': ['http://localhost', 'urn:ietf:wg:oauth:2.0:oob'],
            'auth_uri': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    }

    flow = _ShortURLFlow.from_client_config(
        client_config, scopes, autogenerate_code_verifier=True)
    flow_kwargs = {'access_type': access_type}
    if login_hint:
      flow_kwargs['login_hint'] = login_hint

    # TODO: Move code for browser detection somewhere in this file so that the
    # messaging about `nobrowser.txt` is co-located with the logic that uses it.
    if use_console_flow:
      flow.run_console(
          authorization_prompt_message=MESSAGE_CONSOLE_AUTHORIZATION_PROMPT,
          authorization_code_message=MESSAGE_CONSOLE_AUTHORIZATION_CODE,
          **flow_kwargs)
    else:
      flow.run_local_server(
          authorization_prompt_message=MESSAGE_LOCAL_SERVER_AUTHORIZATION_PROMPT,
          success_message=MESSAGE_LOCAL_SERVER_SUCCESS,
          **flow_kwargs)
    return cls.from_google_oauth2_credentials(
        flow.credentials, filename=filename)

  @classmethod
  def from_client_secrets_file(cls,
                               client_secrets_file,
                               scopes,
                               access_type='offline',
                               login_hint=None,
                               credentials_file=None,
                               use_console_flow=False):
    """Runs an OAuth Flow from secrets stored on disk to generate credentials.

    Args:
      client_secrets_file: String, path to a file containing a client ID and
        secret.
      scopes: Sequence[str], A list of scopes to include in the credentials.
      access_type: String, 'offline' or 'online'.  Indicates whether your
        application can refresh access tokens when the user is not present at
        the browser. Valid parameter values are online, which is the default
        value, and offline.  Set the value to offline if your application needs
        to refresh access tokens when the user is not present at the browser.
        This is the method of refreshing access tokens described later in this
        document. This value instructs the Google authorization server to return
        a refresh token and an access token the first time that your application
        exchanges an authorization code for tokens.
      login_hint: String, The email address that will be displayed on the Google
        login page as a hint for the user to login to the correct account.
      credentials_file: String, the path to a file to use to save the
        credentials.
      use_console_flow: Boolean, True if the authentication flow should be run
        strictly from a console; False to launch a browser for authentication.

    Raises:
      InvalidClientSecretsFileError: If the client secrets file cannot be
        opened.
      InvalidClientSecretsFileFormatError: If the client secrets file does not
        contain the required data or the data is malformed.

    Returns:
      Credentials
    """
    cs_data = fileutils.read_file(
        client_secrets_file, continue_on_error=True, display_errors=False)
    if not cs_data:
      raise InvalidClientSecretsFileError(
          f'File {client_secrets_file} could not be opened')
    try:
      cs_json = json.loads(cs_data)
      client_id = cs_json['installed']['client_id']
      # Chop off .apps.googleusercontent.com suffix as it's not needed
      # and we need to keep things short for the Auth URL.
      client_id = re.sub(r'\.apps\.googleusercontent\.com$', '', client_id)
      client_secret = cs_json['installed']['client_secret']
    except (ValueError, IndexError, KeyError):
      raise InvalidClientSecretsFileFormatError(
          f'Could not extract Client ID or Client Secret from file {client_secrets_file}'
      )

    return cls.from_client_secrets(
        client_id,
        client_secret,
        scopes,
        access_type=access_type,
        login_hint=login_hint,
        filename=credentials_file,
        use_console_flow=use_console_flow)

  def _fetch_id_token_data(self):
    """Fetches verification details from Google for the OAuth2.0 token.

    See more: https://developers.google.com/identity/sign-in/web/backend-auth

    Raises:
      CredentialsError: If no id_token is present.
    """
    if not self.id_token:
      raise CredentialsError('Failed to fetch token data. No id_token present.')

    request = transport.create_request()
    if self.expired:
      # The id_token needs to be unexpired, in order to request data about it.
      self.refresh(request)

    self._id_token_data = google.oauth2.id_token.verify_oauth2_token(
        self.id_token, request)

  def get_token_value(self, field):
    """Retrieves data from the OAuth ID token.

    See more: https://developers.google.com/identity/sign-in/web/backend-auth

    Args:
      field: The name of the key/field to fetch

    Returns:
      The value associated with the given key or 'Unknown' if the key data can
      not be found in the access token data.
    """
    if not self._id_token_data:
      self._fetch_id_token_data()
    # Maintain legacy GAM behavior here to return "Unknown" if the field is
    # otherwise unpopulated.
    return self._id_token_data.get(field, 'Unknown')

  def to_json(self, strip=None):
    """Creates a JSON representation of a Credentials.

    Args:
        strip: Sequence[str], Optional list of members to exclude from the
          generated JSON.

    Returns:
        str: A JSON representation of this instance, suitable to pass to
             from_json().
    """
    expiry = self.expiry.strftime(
        Credentials.DATETIME_FORMAT) if self.expiry else None
    prep = {
        'token': self.token,
        'refresh_token': self.refresh_token,
        'token_uri': self.token_uri,
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'id_token': self.id_token,
        # Google auth doesn't currently give us scopes back on refresh.
        # 'scopes': sorted(self.scopes),
        'token_expiry': expiry,
        'decoded_id_token': self._id_token_data,
    }

    # Remove empty entries
    prep = {k: v for k, v in prep.items() if v is not None}

    # Remove entries that explicitly need to be removed
    if strip is not None:
      prep = {k: v for k, v in prep.items() if k not in strip}

    return json.dumps(prep, indent=2, sort_keys=True)

  def refresh(self, request=None):
    """Refreshes the credential's access token.

    Args:
      request: google.auth.transport.Request, The object used to make HTTP
        requests. If not provided, a default request will be used.

    Raises:
      google.auth.exceptions.RefreshError: If the credentials could not be
      refreshed.
    """
    with self._lock:
      if request is None:
        request = transport.create_request()
      self._locked_refresh(request)
      # Save the new tokens back to disk, if these credentials are disk-backed.
      if self._filename:
        self._locked_write()

  def _locked_refresh(self, request):
    """Refreshes the credential's access token while the file lock is held."""
    assert self._lock.is_locked
    super(Credentials, self).refresh(request)

  def write(self):
    """Writes credentials to disk."""
    with self._lock:
      self._locked_write()

  def _locked_write(self):
    """Writes credentials to disk while the file lock is held."""
    assert self._lock.is_locked
    if not self.filename:
      # If no filename was provided to the constructor, these credentials cannot
      # be saved to disk.
      raise CredentialsError(
          'The credentials have no associated filename and cannot be saved '
          'to disk.')
    fileutils.write_file(self._filename, self.to_json())

  def delete(self):
    """Deletes all files on disk related to these credentials."""
    with self._lock:
      # Only attempt to remove the file if the lock we're using is a FileLock.
      if isinstance(self._lock, FileLock):
        os.remove(self._filename)
        if self._lock.lock_file and not GM_Globals[GM_WINDOWS]:
          os.remove(self._lock.lock_file)

  _REVOKE_TOKEN_BASE_URI = 'https://accounts.google.com/o/oauth2/revoke'

  def revoke(self, http=None):
    """Revokes this credential's access token with the server.

    Args:
      http: httplib2.Http compatible object for use as a transport. If no http
        is provided, a default will be used.
    """
    with self._lock:
      if http is None:
        http = transport.create_http()
      params = urlencode({'token': self.refresh_token})
      revoke_uri = f'{Credentials._REVOKE_TOKEN_BASE_URI}?{params}'
      http.request(revoke_uri, 'GET')


class _ShortURLFlow(google_auth_oauthlib.flow.InstalledAppFlow):
  """InstalledAppFlow which utilizes a URL shortener for authorization URLs."""

  URL_SHORTENER_ENDPOINT = 'https://gam-shortn.appspot.com/create'

  def authorization_url(self, http=None, **kwargs):
    """Gets a shortened authorization URL."""
    long_url, state = super(_ShortURLFlow, self).authorization_url(**kwargs)
    short_url = utils.shorten_url(long_url)
    return short_url, state

class _FileLikeThreadLock(object):
  """A threading.lock which has the same interface as filelock.Filelock."""

  def __init__(self):
    """A shell object that holds a threading.Lock.

    Since we cannot inherit from built-in classes such as threading.Lock, we
    just use a shell object and maintain a lock inside of it.
    """
    self._lock = threading.Lock()

  def __enter__(self, *args, **kwargs):
    return self._lock.__enter__(*args, **kwargs)

  def __exit__(self, *args, **kwargs):
    return self._lock.__exit__(*args, **kwargs)

  def acquire(self, **kwargs):
    return self._lock.acquire(**kwargs)

  def release(self):
    return self._lock.release()

  @property
  def is_locked(self):
    return self._lock.locked()

  @property
  def lock_file(self):
    return None
