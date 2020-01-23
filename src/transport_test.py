"""Tests for transport."""

import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from gam import SetGlobalVariables
import google_auth_httplib2
import httplib2

import transport


class CreateHttpTest(unittest.TestCase):

  def setUp(self):
    SetGlobalVariables()
    super(CreateHttpTest, self).setUp()

  def test_create_http_sets_default_values_on_http(self):
    http = transport.create_http()
    self.assertIsNone(http.cache)
    self.assertIsNone(http.timeout)
    self.assertEqual(http.tls_minimum_version,
                     transport.GC_Values[transport.GC_TLS_MIN_VERSION])
    self.assertEqual(http.tls_maximum_version,
                     transport.GC_Values[transport.GC_TLS_MAX_VERSION])
    self.assertEqual(http.ca_certs, transport.GC_Values[transport.GC_CA_FILE])

  def test_create_http_sets_tls_min_version(self):
    http = transport.create_http(override_min_tls='TLSv1_1')
    self.assertEqual(http.tls_minimum_version, 'TLSv1_1')

  def test_create_http_sets_tls_max_version(self):
    http = transport.create_http(override_max_tls='TLSv1_3')
    self.assertEqual(http.tls_maximum_version, 'TLSv1_3')

  def test_create_http_sets_cache(self):
    fake_cache = {}
    http = transport.create_http(cache=fake_cache)
    self.assertEqual(http.cache, fake_cache)

  def test_create_http_sets_cache_timeout(self):
    http = transport.create_http(timeout=1234)
    self.assertEqual(http.timeout, 1234)


class TransportTest(unittest.TestCase):

  def setUp(self):
    self.mock_http = MagicMock(spec=httplib2.Http)
    self.mock_response = MagicMock(spec=httplib2.Response)
    self.mock_content = MagicMock()
    self.mock_http.request.return_value = (self.mock_response,
                                           self.mock_content)
    self.mock_credentials = MagicMock()
    self.test_uri = 'http://example.com'
    super(TransportTest, self).setUp()

  @patch.object(transport, 'create_http')
  def test_create_request_uses_default_http(self, mock_create_http):
    request = transport.create_request()
    self.assertEqual(request.http, mock_create_http.return_value)

  def test_create_request_uses_provided_http(self):
    request = transport.create_request(http=self.mock_http)
    self.assertEqual(request.http, self.mock_http)

  def test_create_request_returns_request_with_forced_user_agent(self):
    request = transport.create_request()
    self.assertIsInstance(request, transport.Request)

  def test_request_is_google_auth_httplib2_compatible(self):
    request = transport.create_request()
    self.assertIsInstance(request, google_auth_httplib2.Request)

  def test_request_call_returns_response_content(self):
    request = transport.Request(self.mock_http)
    response = request(self.test_uri)
    self.assertEqual(self.mock_response.status, response.status)
    self.assertEqual(self.mock_content, response.data)

  def test_request_call_forces_user_agent_no_provided_headers(self):
    request = transport.Request(self.mock_http)

    request(self.test_uri)
    headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', headers)
    self.assertIn(transport.GAM_USER_AGENT, headers['user-agent'])

  def test_request_call_forces_user_agent_no_agent_in_headers(self):
    request = transport.Request(self.mock_http)
    fake_request_headers = {'some-header-thats-not-a-user-agent': 'someData'}

    request(self.test_uri, headers=fake_request_headers)
    final_headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', final_headers)
    self.assertIn(transport.GAM_USER_AGENT, final_headers['user-agent'])
    self.assertIn('some-header-thats-not-a-user-agent', final_headers)
    self.assertEqual('someData',
                     final_headers['some-header-thats-not-a-user-agent'])

  def test_request_call_forces_user_agent_with_another_agent_in_headers(self):
    request = transport.Request(self.mock_http)
    headers_with_user_agent = {'user-agent': 'existing-user-agent'}

    request(self.test_uri, headers=headers_with_user_agent)
    final_headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', final_headers)
    self.assertIn('existing-user-agent', final_headers['user-agent'])
    self.assertIn(transport.GAM_USER_AGENT, final_headers['user-agent'])

  def test_request_call_same_user_agent_already_in_headers(self):
    request = transport.Request(self.mock_http)
    same_user_agent_header = {'user-agent': transport.GAM_USER_AGENT}

    request(self.test_uri, headers=same_user_agent_header)
    final_headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', final_headers)
    self.assertIn(transport.GAM_USER_AGENT, final_headers['user-agent'])
    # Make sure the header wasn't duplicated
    self.assertEqual(
        len(transport.GAM_USER_AGENT), len(final_headers['user-agent']))

  def test_authorizedhttp_is_google_auth_httplib2_compatible(self):
    http = transport.AuthorizedHttp(self.mock_credentials)
    self.assertIsInstance(http, google_auth_httplib2.AuthorizedHttp)

  def test_authorizedhttp_request_returns_response_content(self):
    http = transport.AuthorizedHttp(self.mock_credentials, http=self.mock_http)
    response, content = http.request(self.test_uri)
    self.assertEqual(self.mock_response, response)
    self.assertEqual(self.mock_content, content)

  def test_authorizedhttp_request_forces_user_agent_no_provided_headers(self):
    authorized_http = transport.AuthorizedHttp(
        self.mock_credentials, http=self.mock_http)
    authorized_http.request(self.test_uri)
    headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', headers)
    self.assertIn(transport.GAM_USER_AGENT, headers['user-agent'])

  def test_authorizedhttp_request_forces_user_agent_no_agent_in_headers(self):
    authorized_http = transport.AuthorizedHttp(
        self.mock_credentials, http=self.mock_http)
    fake_request_headers = {'some-header-thats-not-a-user-agent': 'someData'}

    authorized_http.request(self.test_uri, headers=fake_request_headers)
    final_headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', final_headers)
    self.assertIn(transport.GAM_USER_AGENT, final_headers['user-agent'])
    self.assertIn('some-header-thats-not-a-user-agent', final_headers)
    self.assertEqual('someData',
                     final_headers['some-header-thats-not-a-user-agent'])

  def test_authorizedhttp_request_forces_user_agent_with_another_agent_in_headers(
      self):
    authorized_http = transport.AuthorizedHttp(
        self.mock_credentials, http=self.mock_http)
    headers_with_user_agent = {'user-agent': 'existing-user-agent'}

    authorized_http.request(self.test_uri, headers=headers_with_user_agent)
    final_headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', final_headers)
    self.assertIn('existing-user-agent', final_headers['user-agent'])
    self.assertIn(transport.GAM_USER_AGENT, final_headers['user-agent'])

  def test_authorizedhttp_request_same_user_agent_already_in_headers(self):
    authorized_http = transport.AuthorizedHttp(
        self.mock_credentials, http=self.mock_http)
    same_user_agent_header = {'user-agent': transport.GAM_USER_AGENT}

    authorized_http.request(self.test_uri, headers=same_user_agent_header)
    final_headers = self.mock_http.request.call_args[1]['headers']
    self.assertIn('user-agent', final_headers)
    self.assertIn(transport.GAM_USER_AGENT, final_headers['user-agent'])
    # Make sure the header wasn't duplicated
    self.assertEqual(
        len(transport.GAM_USER_AGENT), len(final_headers['user-agent']))
