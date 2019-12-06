"""Tests for gapi."""

import json
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from gam import SetGlobalVariables
import gapi
from gapi import errors


def create_http_error(status, reason, message):
  """Creates a HttpError object similar to most Google API Errors.

  Args:
    status: Int, the error's HTTP response status number.
    reason: String, a camelCase reason for the HttpError being given.
    message: String, a general error message describing the error that occurred.

  Returns:
    googleapiclient.errors.HttpError
  """
  response = {
      'status': status,
      'content-type': 'application/json',
  }
  content = {
      'error': {
          'code': status,
          'errors': [{
              'reason': str(reason),
              'message': message,
          }]
      }
  }
  content_bytes = json.dumps(content).encode('UTF-8')
  return gapi.googleapiclient.errors.HttpError(response, content_bytes)


class CreateHttpTest(unittest.TestCase):

  def setUp(self):
    SetGlobalVariables()
    super(CreateHttpTest, self).setUp()

  def test_create_http_sets_default_values_on_http(self):
    http = gapi.create_http()
    self.assertIsNone(http.cache)
    self.assertIsNone(http.timeout)
    self.assertEqual(http.tls_minimum_version,
                     gapi.GC_Values[gapi.GC_TLS_MIN_VERSION])
    self.assertEqual(http.tls_maximum_version,
                     gapi.GC_Values[gapi.GC_TLS_MAX_VERSION])
    self.assertEqual(http.ca_certs, gapi.GC_Values[gapi.GC_CA_FILE])

  def test_create_http_sets_tls_min_version(self):
    http = gapi.create_http(override_min_tls=1111)
    self.assertEqual(http.tls_minimum_version, 1111)

  def test_create_http_sets_tls_max_version(self):
    http = gapi.create_http(override_max_tls=9999)
    self.assertEqual(http.tls_maximum_version, 9999)

  def test_create_http_sets_cache(self):
    fake_cache = {}
    http = gapi.create_http(cache=fake_cache)
    self.assertEqual(http.cache, fake_cache)

  def test_create_http_sets_cache_timeout(self):
    http = gapi.create_http(timeout=1234)
    self.assertEqual(http.timeout, 1234)


class CallTest(unittest.TestCase):

  def setUp(self):
    SetGlobalVariables()
    self.mock_service = MagicMock()
    self.mock_method_name = 'mock_method'
    self.mock_method = getattr(self.mock_service, self.mock_method_name)
    super(CallTest, self).setUp()

  def test_call_returns_basic_200_response(self):
    response = gapi.call(self.mock_service, self.mock_method_name)
    self.assertEqual(response, self.mock_method().execute.return_value)

  def test_call_passes_target_method_params(self):
    gapi.call(
        self.mock_service, self.mock_method_name, my_param_1=1, my_param_2=2)
    self.assertEqual(self.mock_method.call_count, 1)
    method_kwargs = self.mock_method.call_args[1]
    self.assertEqual(method_kwargs.get('my_param_1'), 1)
    self.assertEqual(method_kwargs.get('my_param_2'), 2)

  @patch.object(gapi.errors, 'get_gapi_error_detail')
  def test_call_retries_with_soft_errors(self, mock_error_detail):
    mock_error_detail.return_value = (-1, 'aReason', 'some message')

    # Make the request fail first, then return the proper response on the retry.
    fake_http_error = create_http_error(403, 'aReason', 'unused message')
    fake_200_response = MagicMock()
    self.mock_method.return_value.execute.side_effect = [
        fake_http_error, fake_200_response
    ]

    response = gapi.call(
        self.mock_service, self.mock_method_name, soft_errors=True)
    self.assertEqual(response, fake_200_response)
    self.assertEqual(
        self.mock_service._http.request.credentials.refresh.call_count, 1)
    self.assertEqual(self.mock_method.return_value.execute.call_count, 2)

  def test_call_throws_for_provided_reason(self):
    throw_reason = errors.ErrorReason.USER_NOT_FOUND
    fake_http_error = create_http_error(404, throw_reason, 'forced throw')
    self.mock_method.return_value.execute.side_effect = fake_http_error

    gam_exception = errors.ERROR_REASON_TO_EXCEPTION[throw_reason]
    with self.assertRaises(gam_exception):
      gapi.call(
          self.mock_service,
          self.mock_method_name,
          throw_reasons=[throw_reason])

  # Prevent wait_on_failure from performing actual backoff unnecessarily, since
  # we're not actually testing over a network connection
  @patch.object(gapi.controlflow, 'wait_on_failure')
  def test_call_retries_request_for_default_retry_reasons(
      self, mock_wait_on_failure):

    # Test using one of the default retry reasons
    default_throw_reason = errors.ErrorReason.BACKEND_ERROR
    self.assertIn(default_throw_reason, errors.DEFAULT_RETRY_REASONS)

    fake_http_error = create_http_error(404, default_throw_reason, 'message')
    fake_200_response = MagicMock()
    # Fail once, then succeed on retry
    self.mock_method.return_value.execute.side_effect = [
        fake_http_error, fake_200_response
    ]

    response = gapi.call(
        self.mock_service, self.mock_method_name, retry_reasons=[])
    self.assertEqual(response, fake_200_response)
    self.assertEqual(self.mock_method.return_value.execute.call_count, 2)
    # Make sure a backoff technique was used for retry.
    self.assertEqual(mock_wait_on_failure.call_count, 1)

  # Prevent wait_on_failure from performing actual backoff unnecessarily, since
  # we're not actually testing over a network connection
  @patch.object(gapi.controlflow, 'wait_on_failure')
  def test_call_retries_requests_for_provided_retry_reasons(
      self, unused_mock_wait_on_failure):

    retry_reason1 = errors.ErrorReason.INTERNAL_ERROR
    fake_retrieable_error1 = create_http_error(400, retry_reason1,
                                               'Forced Error 1')
    retry_reason2 = errors.ErrorReason.SYSTEM_ERROR
    fake_retrieable_error2 = create_http_error(400, retry_reason2,
                                               'Forced Error 2')
    non_retriable_reason = errors.ErrorReason.SERVICE_NOT_AVAILABLE
    fake_non_retriable_error = create_http_error(
        400, non_retriable_reason,
        'This error should not cause the request to be retried')
    # Fail once, then succeed on retry
    self.mock_method.return_value.execute.side_effect = [
        fake_retrieable_error1, fake_retrieable_error2, fake_non_retriable_error
    ]

    with self.assertRaises(SystemExit):
      # The third call should raise the SystemExit when non_retriable_error is
      # raised.
      gapi.call(
          self.mock_service,
          self.mock_method_name,
          retry_reasons=[retry_reason1, retry_reason2])

    self.assertEqual(self.mock_method.return_value.execute.call_count, 3)

  def test_call_exits_on_oauth_token_error(self):
    # An error with any OAUTH2_TOKEN_ERROR
    fake_token_error = gapi.google.auth.exceptions.RefreshError(
        errors.OAUTH2_TOKEN_ERRORS[0])
    self.mock_method.return_value.execute.side_effect = fake_token_error

    with self.assertRaises(SystemExit):
      gapi.call(self.mock_service, self.mock_method_name)

  def test_call_exits_on_nonretriable_error(self):
    error_reason = 'unknownReason'
    fake_http_error = create_http_error(500, error_reason,
                                        'Testing unretriable errors')
    self.mock_method.return_value.execute.side_effect = fake_http_error

    with self.assertRaises(SystemExit):
      gapi.call(self.mock_service, self.mock_method_name)

  def test_call_exits_on_request_valueerror(self):
    self.mock_method.return_value.execute.side_effect = ValueError()

    with self.assertRaises(SystemExit):
      gapi.call(self.mock_service, self.mock_method_name)

  def test_call_clears_bad_http_cache_on_request_failure(self):
    self.mock_service._http.cache = 'something that is not None'
    fake_200_response = MagicMock()
    self.mock_method.return_value.execute.side_effect = [
        ValueError(), fake_200_response
    ]

    self.assertIsNotNone(self.mock_service._http.cache)
    response = gapi.call(self.mock_service, self.mock_method_name)
    self.assertEqual(response, fake_200_response)
    # Assert the cache was cleared
    self.assertIsNone(self.mock_service._http.cache)

  # Prevent wait_on_failure from performing actual backoff unnecessarily, since
  # we're not actually testing over a network connection
  @patch.object(gapi.controlflow, 'wait_on_failure')
  def test_call_retries_requests_with_backoff_on_servernotfounderror(
      self, mock_wait_on_failure):
    fake_servernotfounderror = gapi.httplib2.ServerNotFoundError()
    fake_200_response = MagicMock()
    # Fail once, then succeed on retry
    self.mock_method.return_value.execute.side_effect = [
        fake_servernotfounderror, fake_200_response
    ]

    http_connections = self.mock_service._http.connections
    response = gapi.call(self.mock_service, self.mock_method_name)
    self.assertEqual(response, fake_200_response)
    # HTTP cached connections should be cleared on receiving this error
    self.assertNotEqual(http_connections, self.mock_service._http.connections)
    self.assertEqual(self.mock_method.return_value.execute.call_count, 2)
    # Make sure a backoff technique was used for retry.
    self.assertEqual(mock_wait_on_failure.call_count, 1)


if __name__ == '__main__':
  unittest.main()
