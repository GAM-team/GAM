"""Tests for oauth."""

import datetime
import json
import os
import platform
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import google.oauth2.credentials

from auth import oauth


class CredentialsTest(unittest.TestCase):

  def setUp(self):
    self.fake_token = 'fake_token'
    self.fake_refresh_token = 'fake_refresh_token'
    self.fake_id_token = 'fake_id_token'
    self.fake_token_uri = 'https://fake.token.uri'
    self.fake_client_id = 'fake_client_id'
    self.fake_client_secret = 'fake_client_secret'
    self.fake_scopes = [
        'fake_api.readonly',
        'fake_other_api.write',
    ]
    self.fake_quota_project_id = 'fake_quota_project_id'
    self.fake_token_expiry = datetime.datetime(2020, 1, 1, 10)
    self.fake_filename = 'fake_filename'
    self.fake_token_data = {
        'field': 'value',
        'another-field': 'another-value',
    }
    self.info_with_only_required_fields = {
        'refresh_token': self.fake_refresh_token,
        'client_id': self.fake_client_id,
        'client_secret': self.fake_client_secret,
    }
    super(CredentialsTest, self).setUp()

  def tearDown(self):
    # Remove any credential files that may have been created.
    if os.path.exists(self.fake_filename):
      os.remove(self.fake_filename)
    if os.path.exists('%s.lock' % self.fake_filename):
      os.remove('%s.lock' % self.fake_filename)
    super(CredentialsTest, self).tearDown()

  def test_from_authorized_user_info_only_required_info(self):
    creds = oauth.Credentials.from_authorized_user_info(
        self.info_with_only_required_fields)
    self.assertEqual(self.fake_refresh_token, creds.refresh_token)
    self.assertEqual(self.fake_client_id, creds.client_id)
    self.assertEqual(self.fake_client_secret, creds.client_secret)
    self.assertIsNone(creds.id_token)
    self.assertIsNone(creds.expiry)
    self.assertIsNone(creds.filename)

  def test_from_authorized_user_info_all_info_provided(self):
    info = {
        'token':
            self.fake_token,
        'refresh_token':
            self.fake_refresh_token,
        'id_token':
            self.fake_id_token,
        'token_uri':
            self.fake_token_uri,
        'client_id':
            self.fake_client_id,
        'client_secret':
            self.fake_client_secret,
        'token_expiry':
            self.fake_token_expiry.strftime(oauth.Credentials.DATETIME_FORMAT),
        'id_token_data':
            self.fake_token_data,
    }
    creds = oauth.Credentials.from_authorized_user_info(info)
    self.assertEqual(self.fake_refresh_token, creds.refresh_token)
    self.assertEqual(self.fake_client_id, creds.client_id)
    self.assertEqual(self.fake_client_secret, creds.client_secret)
    self.assertEqual(self.fake_id_token, creds.id_token)
    self.assertEqual(self.fake_token_uri, creds.token_uri)
    self.assertEqual(self.fake_token_expiry, creds.expiry)
    self.assertIsNone(creds.filename)

  def test_from_authorized_user_info_missing_required_info(self):
    info_with_missing_fields = {'token': self.fake_token}
    with self.assertRaises(ValueError):
      oauth.Credentials.from_authorized_user_info(info_with_missing_fields)

  def test_from_authorized_user_info_no_expiry_in_info(self):
    info_with_no_token_expiry = self.info_with_only_required_fields.copy()
    self.assertIsNone(info_with_no_token_expiry.get('expiry'))
    creds = oauth.Credentials.from_authorized_user_info(
        info_with_no_token_expiry)
    self.assertIsNone(creds.expiry)

  def test_init_saves_filename(self):
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)
    self.assertEqual(os.path.abspath(self.fake_filename), creds.filename)

  @patch.object(oauth.google.oauth2.id_token, 'verify_oauth2_token')
  def test_init_loads_decoded_id_token_data(self, mock_verify_token):
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token=self.fake_id_token,
        id_token_data=self.fake_token_data)
    self.assertEqual(
        self.fake_token_data.get('field'), creds.get_token_value('field'))
    # Verify the fetching method was not called, since the token
    # data was supposed to be loaded from the passed in info.
    self.assertEqual(mock_verify_token.call_count, 0)

  def test_credentials_uses_file_lock_when_filename_provided(self):
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)
    self.assertIsInstance(creds._lock, oauth.FileLock)
    self.assertEqual(creds._lock.lock_file, '%s.lock' % creds.filename)

  def test_credentials_uses_thread_lock_when_filename_not_provided(self):
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=None)
    self.assertIsInstance(creds._lock, oauth._FileLikeThreadLock)
    self.assertIsNone(creds.filename)

  def test_from_oauth2credentials(self):
    google_creds = google.oauth2.credentials.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token=self.fake_id_token)
    creds = oauth.Credentials.from_google_oauth2_credentials(
        google_creds, filename=self.fake_filename)
    self.assertEqual(google_creds.token, creds.token)
    self.assertEqual(google_creds.refresh_token, creds.refresh_token)
    self.assertEqual(google_creds.client_id, creds.client_id)
    self.assertEqual(google_creds.client_secret, creds.client_secret)
    self.assertEqual(google_creds.id_token, creds.id_token)
    self.assertEqual(google_creds.expiry, creds.expiry)
    self.assertEqual(google_creds.quota_project_id, creds.quota_project_id)
    self.assertEqual(os.path.abspath(self.fake_filename), creds.filename)

  def test_from_credentials_file_corrupt_or_missing_file_raises_error(self):
    self.assertFalse(os.path.exists(self.fake_filename))
    with self.assertRaises(oauth.InvalidCredentialsFileError) as e:
      oauth.Credentials.from_credentials_file(self.fake_filename)
    self.assertIn('could not be opened', str(e.exception))

  @patch.object(oauth.fileutils, 'read_file')
  def test_from_credentials_file_no_serialized_data_in_file_raises_error(
      self, mock_read_file):
    mock_read_file.return_value = json.dumps({})
    with self.assertRaises(oauth.EmptyCredentialsFileError):
      oauth.Credentials.from_credentials_file(self.fake_filename)

  @patch.object(oauth.fileutils, 'read_file')
  def test_from_credentials_file_missing_any_token_raises_error(
      self, mock_read_file):
    mock_read_file.return_value = json.dumps({
        # This data is missing a token key/value pair
        'client_id': self.fake_client_id,
        'client_secret': self.fake_client_secret,
    })
    with self.assertRaises(oauth.InvalidCredentialsFileError):
      oauth.Credentials.from_credentials_file(self.fake_filename)

  @patch.object(oauth.fileutils, 'read_file')
  def test_from_credentials_file_missing_required_raises_error(
      self, mock_read_file):
    mock_read_file.return_value = json.dumps({
        # This data is missing a client_secret key/value pair
        'client_id': self.fake_client_id,
        'refresh_token': self.fake_refresh_token,
    })
    with self.assertRaises(oauth.InvalidCredentialsFileError):
      oauth.Credentials.from_credentials_file(self.fake_filename)

  @patch.object(oauth._ShortURLFlow, 'from_client_config')
  def test_from_client_secrets_console_flow(self, mock_flow):
    flow_creds = google.oauth2.credentials.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token=self.fake_id_token)
    mock_flow.return_value.credentials = flow_creds

    creds = oauth.Credentials.from_client_secrets(
        self.fake_client_id,
        self.fake_client_secret,
        self.fake_scopes,
        use_console_flow=True)
    self.assertTrue(mock_flow.return_value.run_console.called)
    self.assertFalse(mock_flow.return_value.run_local_server.called)
    self.assertEqual(flow_creds.token, creds.token)
    self.assertEqual(flow_creds.refresh_token, creds.refresh_token)
    self.assertEqual(flow_creds.client_id, creds.client_id)
    self.assertEqual(flow_creds.client_secret, creds.client_secret)
    self.assertEqual(flow_creds.id_token, creds.id_token)

  @patch.object(oauth._ShortURLFlow, 'from_client_config')
  def test_from_client_secrets_local_server_flow(self, mock_flow):
    flow_creds = google.oauth2.credentials.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token=self.fake_id_token)
    mock_flow.return_value.credentials = flow_creds

    creds = oauth.Credentials.from_client_secrets(
        self.fake_client_id,
        self.fake_client_secret,
        self.fake_scopes,
        use_console_flow=False)
    self.assertFalse(mock_flow.return_value.run_console.called)
    self.assertTrue(mock_flow.return_value.run_local_server.called)
    self.assertEqual(flow_creds.token, creds.token)
    self.assertEqual(flow_creds.refresh_token, creds.refresh_token)
    self.assertEqual(flow_creds.client_id, creds.client_id)
    self.assertEqual(flow_creds.client_secret, creds.client_secret)
    self.assertEqual(flow_creds.id_token, creds.id_token)

  @patch.object(oauth._ShortURLFlow, 'from_client_config')
  def test_from_client_secrets_uses_login_hint(self, mock_flow):
    flow_creds = google.oauth2.credentials.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token=self.fake_id_token)
    mock_flow.return_value.credentials = flow_creds

    oauth.Credentials.from_client_secrets(
        self.fake_client_id,
        self.fake_client_secret,
        self.fake_scopes,
        login_hint='someone@domain.com')

    run_flow_args = mock_flow.return_value.run_local_server.call_args[1]
    self.assertEqual('someone@domain.com', run_flow_args.get('login_hint'))

  def test_from_client_secrets_uses_shortened_url_flow(self):
    with patch.object(oauth._ShortURLFlow, 'from_client_config') as mock_flow:
      flow_creds = google.oauth2.credentials.Credentials(
          token=self.fake_token,
          refresh_token=self.fake_refresh_token,
          client_id=self.fake_client_id,
          client_secret=self.fake_client_secret,
          id_token=self.fake_id_token)
      mock_flow.return_value.credentials = flow_creds
      oauth.Credentials.from_client_secrets(self.fake_client_id,
                                            self.fake_client_secret,
                                            self.fake_scopes)
    self.assertTrue(mock_flow.called)

  @patch.object(oauth._ShortURLFlow, 'from_client_config')
  def test_from_client_secrets_passes_credentials_filename(self, mock_flow):
    flow_creds = google.oauth2.credentials.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token=self.fake_id_token)
    mock_flow.return_value.credentials = flow_creds

    creds = oauth.Credentials.from_client_secrets(
        self.fake_client_id,
        self.fake_client_secret,
        self.fake_scopes,
        filename=self.fake_filename)
    self.assertEqual(os.path.abspath(self.fake_filename), creds.filename)

  def test_from_client_secrets_file_corrupt_or_missing_file_raises_error(self):
    self.assertFalse(os.path.exists(self.fake_filename))
    with self.assertRaises(oauth.InvalidClientSecretsFileError):
      oauth.Credentials.from_client_secrets_file(self.fake_filename,
                                                 self.fake_scopes)

  @patch.object(oauth.fileutils, 'read_file')
  def test_from_client_secrets_file_missing_required_json_raises_error(
      self, mock_read_file):
    mock_read_file.return_value = json.dumps({})
    with self.assertRaises(oauth.InvalidClientSecretsFileFormatError) as e:
      oauth.Credentials.from_client_secrets_file(self.fake_filename,
                                                 self.fake_scopes)
    self.assertIn('Could not extract Client ID or Client Secret',
                  str(e.exception))

  @patch.object(oauth.Credentials, 'from_client_secrets')
  @patch.object(oauth.fileutils, 'read_file')
  def test_from_client_secrets_file_strips_domain_from_client_id(
      self, mock_read_file, mock_creds_from_client_secrets):
    mock_read_file.return_value = json.dumps({
        'installed': {
            'client_id': self.fake_client_id + '.apps.googleusercontent.com',
            'client_secret': self.fake_client_secret,
        }
    })

    oauth.Credentials.from_client_secrets_file(self.fake_filename,
                                               self.fake_scopes)
    self.assertEqual(self.fake_client_id,
                     mock_creds_from_client_secrets.call_args[0][0])

  def test_get_token_value_known_token_field(self):
    token_data = {'known-field': 'known-value'}
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token_data=token_data)
    self.assertEqual('known-value', creds.get_token_value('known-field'))

  def test_get_token_value_unknown_field_returns_unknown(self):
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        id_token_data=self.fake_token_data)
    self.assertEqual('Unknown', creds.get_token_value('unknown-field'))

  @patch.object(oauth.google.oauth2.id_token, 'verify_oauth2_token')
  def test_get_token_value_credentials_expired(self, mock_verify_oauth2_token):
    mock_verify_oauth2_token.return_value = {'fetched-field': 'fetched-value'}
    time_earlier_than_now = datetime.datetime.now() - datetime.timedelta(
        minutes=5)
    creds = oauth.Credentials(
        token=self.fake_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        expiry=time_earlier_than_now,
        id_token=self.fake_id_token,
        id_token_data=None)
    self.assertTrue(creds.expired)
    creds.refresh = MagicMock()

    token_value = creds.get_token_value('fetched-field')

    self.assertEqual('fetched-value', token_value)
    self.assertTrue(creds.refresh.called)

  def test_to_json_contains_all_required_fields(self):
    creds = oauth.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        id_token=self.fake_id_token,
        id_token_data=self.fake_token_data,
        token_uri=self.fake_token_uri,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        scopes=self.fake_scopes,
        quota_project_id=self.fake_quota_project_id,
        expiry=self.fake_token_expiry)
    json_string = creds.to_json()
    json_data = json.loads(json_string)
    keys = json_data.keys()
    self.assertIn('token', keys)
    self.assertEqual(self.fake_token, json_data['token'])
    self.assertIn('refresh_token', keys)
    self.assertEqual(self.fake_refresh_token, json_data['refresh_token'])
    self.assertIn('id_token', keys)
    self.assertEqual(self.fake_id_token, json_data['id_token'])
    self.assertIn('token_uri', keys)
    self.assertEqual(self.fake_token_uri, json_data['token_uri'])
    self.assertIn('client_id', keys)
    self.assertEqual(self.fake_client_id, json_data['client_id'])
    self.assertIn('client_secret', keys)
    self.assertEqual(self.fake_client_secret, json_data['client_secret'])
    self.assertNotIn('scopes', keys)  # Scopes are not currently saved
    self.assertIn('token_expiry', keys)
    self.assertEqual(
        self.fake_token_expiry.strftime(oauth.Credentials.DATETIME_FORMAT),
        json_data['token_expiry'])
    self.assertIn('decoded_id_token', keys)
    self.assertEqual(self.fake_token_data, json_data['decoded_id_token'])

  def test_credentials_to_json_and_back(self):
    original_creds = oauth.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        id_token=self.fake_id_token,
        id_token_data=self.fake_token_data,
        token_uri=self.fake_token_uri,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        scopes=self.fake_scopes,
        quota_project_id=self.fake_quota_project_id,
        expiry=self.fake_token_expiry)
    pickled_creds = original_creds.to_json()
    serialized_json = json.loads(pickled_creds)
    unpickled_creds = oauth.Credentials.from_authorized_user_info(
        serialized_json)
    self.assertEqual(original_creds.token, unpickled_creds.token)
    self.assertEqual(original_creds.refresh_token,
                     unpickled_creds.refresh_token)
    self.assertEqual(original_creds.id_token, unpickled_creds.id_token)
    self.assertEqual(original_creds.token_uri, unpickled_creds.token_uri)
    self.assertEqual(original_creds.client_id, unpickled_creds.client_id)
    self.assertEqual(original_creds.client_secret,
                     unpickled_creds.client_secret)
    self.assertEqual(original_creds.expiry, unpickled_creds.expiry)

  @patch.object(oauth.google.oauth2.credentials.Credentials, 'refresh')
  def test_refresh_calls_super_refresh(self, mock_super_refresh):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret)
    request = MagicMock()

    creds.refresh(request)
    self.assertTrue(mock_super_refresh.called)
    self.assertEqual(request, mock_super_refresh.call_args[0][0])

  def test_refresh_locks_resource_during_refresh(self):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret)
    lock = creds._lock

    def check_lock_is_locked(*unused_args, **unused_kwargs):
      self.assertTrue(lock.is_locked)

    # We need to mock the superclass refresh so it doesn't actually try to
    # refresh our fake token.
    # At the same time, we'll make sure the lock is held during the refresh.
    with patch.object(oauth.google.oauth2.credentials.Credentials,
                      'refresh') as mock_refresh:
      mock_refresh.side_effect = check_lock_is_locked
      creds.refresh(request=MagicMock())

    # Make sure our side effect was actually performed.
    self.assertTrue(mock_refresh.called)
    # The lock should be released after refresh
    self.assertFalse(lock.is_locked)

  @patch.object(oauth.google.oauth2.credentials.Credentials, 'refresh')
  @patch.object(oauth.fileutils, 'write_file')
  def test_refresh_writes_new_credentials_to_disk_after_refresh(
      self, mock_write_file, mock_super_refresh):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)

    def update_access_token(unused_request):
      creds.token = 'refreshed_access_token'

    mock_super_refresh.side_effect = update_access_token

    self.assertIsNone(creds.token)
    creds.refresh(request=MagicMock())
    self.assertEqual('refreshed_access_token', creds.token,
                     'Access token was not refreshed')
    text_written_to_file = mock_write_file.call_args[0][1]
    self.assertIsNotNone(text_written_to_file, 'Nothing was written to file')
    saved_json = json.loads(text_written_to_file)
    self.assertEqual('refreshed_access_token', saved_json['token'],
                     'Refreshed access token was not saved to disk')

  def test_write_writes_credentials_to_disk(self):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)

    self.assertFalse(os.path.exists(self.fake_filename))
    creds.write()
    self.assertTrue(os.path.exists(self.fake_filename))

  def test_write_raises_error_when_no_credentials_file_is_set(self):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret)

    self.assertIsNone(creds.filename)
    with self.assertRaises(oauth.CredentialsError):
      creds.write()

  @patch.object(oauth.google.oauth2.credentials.Credentials, 'refresh')
  @patch.object(oauth.fileutils, 'write_file')
  def test_write_locks_resource_during_write(self, mock_write_file,
                                             unused_mock_super_refresh):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)
    lock = creds._lock

    def check_lock_is_locked(*unused_args, **unused_kwargs):
      self.assertTrue(creds._lock.is_locked)

    mock_write_file.side_effect = check_lock_is_locked

    self.assertFalse(lock.is_locked)
    creds.refresh(request=MagicMock())
    self.assertFalse(lock.is_locked)
    self.assertTrue(mock_write_file.called)

  def test_delete_removes_credentials_file(self):
    self.assertFalse(os.path.exists(self.fake_filename))
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)
    creds.write()
    self.assertTrue(os.path.exists(self.fake_filename))
    creds.delete()
    self.assertFalse(os.path.exists(self.fake_filename))

  @unittest.skipIf(
      platform.system() == 'Windows',
      reason=('On Windows, Filelock deletes the lock file each time the lock '
              'is released. Delete does not remove it.'))
  def test_delete_removes_lock_file(self):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret,
        filename=self.fake_filename)
    lock_file = '%s.lock' % creds.filename
    creds.write()
    self.assertTrue(os.path.exists(lock_file))
    creds.delete()
    self.assertFalse(os.path.exists(lock_file))

  def test_delete_is_noop_when_not_using_filelock(self):
    creds = oauth.Credentials(
        token=None,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret)
    self.assertIsNone(creds.filename)
    creds.delete()  # This should not raise an exception.

  def test_revoke_requests_credential_revoke(self):
    creds = oauth.Credentials(
        token=self.fake_token,
        refresh_token=self.fake_refresh_token,
        client_id=self.fake_client_id,
        client_secret=self.fake_client_secret)
    mock_http = MagicMock()

    creds.revoke(http=mock_http)

    uri = mock_http.request.call_args[0][0]
    self.assertRegex(uri, '^%s' % oauth.Credentials._REVOKE_TOKEN_BASE_URI)
    params = uri[uri.index('?'):]
    self.assertIn('token=%s' % creds.refresh_token, params)
    self.assertEqual('GET', mock_http.request.call_args[0][1])


class ShortUrlFlowTest(unittest.TestCase):

  def setUp(self):
    self.fake_client_id = 'fake_client_id'
    self.fake_client_secret = 'fake_client_secret'
    self.fake_scopes = [
        'fake_api.readonly',
        'fake_other_api.write',
    ]
    self.fake_client_config = {
        'installed': {
            'client_id': self.fake_client_id,
            'client_secret': self.fake_client_secret,
            'redirect_uris': ['http://localhost', 'urn:ietf:wg:oauth:2.0:oob'],
            'auth_uri': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    }
    self.long_url = 'http://example.com/some/long/url'
    self.short_url = 'http://ex.co/short'
    super(ShortUrlFlowTest, self).setUp()

  @patch.object(oauth.google_auth_oauthlib.flow.InstalledAppFlow,
                'authorization_url')
  @unittest.skip('disable short url tests temporarily.')
  def test_shorturlflow_returns_shortened_url(self, mock_super_auth_url):
    url_flow = oauth._ShortURLFlow.from_client_config(
        self.fake_client_config, scopes=self.fake_scopes)
    mock_super_auth_url.return_value = (self.long_url, 'fake_state')

    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 200
    content = json.dumps({'short_url': self.short_url})
    mock_http.request.return_value = (mock_response, content)

    url, state = url_flow.authorization_url(http=mock_http)
    self.assertEqual(self.short_url, url)
    self.assertEqual('fake_state', state)

    # Verify request() was called with the expected arguments.
    self.assertEqual(oauth._ShortURLFlow.URL_SHORTENER_ENDPOINT,
                     mock_http.request.call_args[0][0])
    self.assertEqual('POST', mock_http.request.call_args[0][1])
    self.assertIn(self.long_url, mock_http.request.call_args[0][2])

  @patch.object(oauth.google_auth_oauthlib.flow.InstalledAppFlow,
                'authorization_url')
  @unittest.skip('disable short url tests temporarily.')
  def test_shorturlflow_falls_back_to_long_url_on_request_error(
      self, mock_super_auth_url):
    url_flow = oauth._ShortURLFlow.from_client_config(
        self.fake_client_config, scopes=self.fake_scopes)
    mock_super_auth_url.return_value = (self.long_url, 'fake_state')

    mock_http = MagicMock()
    mock_http.request.side_effect = Exception()

    url, state = url_flow.authorization_url(http=mock_http)
    self.assertEqual(self.long_url, url)
    self.assertEqual('fake_state', state)

  @patch.object(oauth.google_auth_oauthlib.flow.InstalledAppFlow,
                'authorization_url')
  @unittest.skip('disable short url tests temporarily.')
  def test_shorturlflow_falls_back_to_long_url_on_non_200_response_status(
      self, mock_super_auth_url):
    url_flow = oauth._ShortURLFlow.from_client_config(
        self.fake_client_config, scopes=self.fake_scopes)
    mock_super_auth_url.return_value = (self.long_url, 'fake_state')

    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 404  # Use a status that is not 200
    content = json.dumps({'short_url': self.short_url})
    mock_http.request.return_value = (mock_response, content)

    url, state = url_flow.authorization_url(http=mock_http)
    self.assertEqual(self.long_url, url)
    self.assertEqual('fake_state', state)

  @patch.object(oauth.google_auth_oauthlib.flow.InstalledAppFlow,
                'authorization_url')
  @unittest.skip('disable short url tests temporarily.')
  def test_shorturlflow_falls_back_to_long_url_on_bad_json_response(
      self, mock_super_auth_url):
    url_flow = oauth._ShortURLFlow.from_client_config(
        self.fake_client_config, scopes=self.fake_scopes)
    mock_super_auth_url.return_value = (self.long_url, 'fake_state')

    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 200
    content = None
    mock_http.request.return_value = (mock_response, content)

    url, state = url_flow.authorization_url(http=mock_http)
    self.assertEqual(self.long_url, url)
    self.assertEqual('fake_state', state)

  @patch.object(oauth.google_auth_oauthlib.flow.InstalledAppFlow,
                'authorization_url')
  @unittest.skip('disable short url tests temporarily.')
  def test_shorturlflow_falls_back_to_long_url_on_empty_short_url_field(
      self, mock_super_auth_url):
    url_flow = oauth._ShortURLFlow.from_client_config(
        self.fake_client_config, scopes=self.fake_scopes)
    mock_super_auth_url.return_value = (self.long_url, 'fake_state')

    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.status = 200
    content = json.dumps({})  # This json content contains no "short-url" key
    mock_http.request.return_value = (mock_response, content)

    url, state = url_flow.authorization_url(http=mock_http)
    self.assertEqual(self.long_url, url)
    self.assertEqual('fake_state', state)


if __name__ == '__main__':
  unittest.main()
