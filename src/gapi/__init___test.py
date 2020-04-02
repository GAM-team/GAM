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


class GapiTest(unittest.TestCase):

  def setUp(self):
    SetGlobalVariables()
    self.mock_service = MagicMock()
    self.mock_method_name = 'mock_method'
    self.mock_method = getattr(self.mock_service, self.mock_method_name)

    self.simple_3_page_response = [
        {
            'items': [{
                'position': 'page1,item1'
            }, {
                'position': 'page1,item2'
            }, {
                'position': 'page1,item3'
            }],
            'nextPageToken': 'page2'
        },
        {
            'items': [{
                'position': 'page2,item1'
            }, {
                'position': 'page2,item2'
            }, {
                'position': 'page2,item3'
            }],
            'nextPageToken': 'page3'
        },
        {
            'items': [{
                'position': 'page3,item1'
            }, {
                'position': 'page3,item2'
            }, {
                'position': 'page3,item3'
            }],
        },
    ]
    self.empty_items_response = {'items': []}

    super(GapiTest, self).setUp()

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
        self.mock_service._http.credentials.refresh.call_count, 1)
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

  def test_get_items_calls_correct_service_function(self):
    gapi.get_items(self.mock_service, self.mock_method_name)
    self.assertTrue(self.mock_method.called)

  def test_get_items_returns_one_page(self):
    fake_response = {'items': [{}, {}, {}]}
    self.mock_method.return_value.execute.return_value = fake_response
    page = gapi.get_items(self.mock_service, self.mock_method_name)
    self.assertEqual(page, fake_response['items'])

  def test_get_items_non_default_page_field_name(self):
    field_name = 'things'
    fake_response = {field_name: [{}, {}, {}]}
    self.mock_method.return_value.execute.return_value = fake_response
    page = gapi.get_items(
        self.mock_service, self.mock_method_name, items=field_name)
    self.assertEqual(page, fake_response[field_name])

  def test_get_items_passes_additional_kwargs_to_service(self):
    gapi.get_items(
        self.mock_service, self.mock_method_name, my_param_1=1, my_param_2=2)
    self.assertEqual(self.mock_method.call_count, 1)
    method_kwargs = self.mock_method.call_args[1]
    self.assertEqual(1, method_kwargs.get('my_param_1'))
    self.assertEqual(2, method_kwargs.get('my_param_2'))

  def test_get_items_returns_empty_list_when_no_items_returned(self):
    non_items_response = {'noItemsInThisResponse': {}}
    self.mock_method.return_value.execute.return_value = non_items_response
    page = gapi.get_items(self.mock_service, self.mock_method_name)
    self.assertIsInstance(page, list)
    self.assertEqual(0, len(page))

  def test_get_all_pages_returns_all_items(self):
    page_1 = {'items': ['1-1', '1-2', '1-3'], 'nextPageToken': '2'}
    page_2 = {'items': ['2-1', '2-2', '2-3'], 'nextPageToken': '3'}
    page_3 = {'items': ['3-1', '3-2', '3-3']}
    self.mock_method.return_value.execute.side_effect = [page_1, page_2, page_3]
    response_items = gapi.get_all_pages(self.mock_service,
                                        self.mock_method_name)
    self.assertListEqual(response_items,
                         page_1['items'] + page_2['items'] + page_3['items'])

  def test_get_all_pages_includes_next_pagetoken_in_request(self):
    page_1 = {'items': ['1-1', '1-2', '1-3'], 'nextPageToken': 'someToken'}
    page_2 = {'items': ['2-1', '2-2', '2-3']}
    self.mock_method.return_value.execute.side_effect = [page_1, page_2]

    gapi.get_all_pages(self.mock_service, self.mock_method_name, pageSize=100)
    self.assertEqual(self.mock_method.call_count, 2)
    call_2_kwargs = self.mock_method.call_args_list[1][1]
    self.assertIn('pageToken', call_2_kwargs)
    self.assertEqual(call_2_kwargs['pageToken'], page_1['nextPageToken'])

  def test_get_all_pages_uses_default_max_page_size(self):
    sample_api_id = list(gapi.MAX_RESULTS_API_EXCEPTIONS.keys())[0]
    sample_api_max_results = gapi.MAX_RESULTS_API_EXCEPTIONS[sample_api_id]
    self.mock_method.return_value.methodId = sample_api_id
    self.mock_service._rootDesc = {
        'resources': {
            'someResource': {
                'methods': {
                    'someMethod': {
                        'id': sample_api_id,
                        'parameters': {
                            'maxResults': {
                                'maximum': sample_api_max_results
                            }
                        }
                    }
                }
            }
        }
    }
    self.mock_method.return_value.execute.return_value = self.empty_items_response

    gapi.get_all_pages(self.mock_service, self.mock_method_name)
    request_method_kwargs = self.mock_method.call_args[1]
    self.assertIn('maxResults', request_method_kwargs)
    self.assertEqual(request_method_kwargs['maxResults'],
                     gapi.MAX_RESULTS_API_EXCEPTIONS.get(sample_api_id))

  def test_get_all_pages_max_page_size_overrided(self):
    self.mock_method.return_value.execute.return_value = self.empty_items_response

    gapi.get_all_pages(
        self.mock_service, self.mock_method_name, pageSize=123456)
    request_method_kwargs = self.mock_method.call_args[1]
    self.assertIn('pageSize', request_method_kwargs)
    self.assertEqual(123456, request_method_kwargs['pageSize'])

  def test_get_all_pages_prints_paging_message(self):
    self.mock_method.return_value.execute.side_effect = self.simple_3_page_response

    paging_message = 'A simple string displayed during paging'
    with patch.object(gapi.sys.stderr, 'write') as mock_write:
      gapi.get_all_pages(
          self.mock_service, self.mock_method_name, page_message=paging_message)
    messages_written = [
        call_args[0][0] for call_args in mock_write.call_args_list
    ]
    self.assertIn(paging_message, messages_written)

  def test_get_all_pages_prints_paging_message_inline(self):
    self.mock_method.return_value.execute.side_effect = self.simple_3_page_response

    paging_message = 'A simple string displayed during paging'
    with patch.object(gapi.sys.stderr, 'write') as mock_write:
      gapi.get_all_pages(
          self.mock_service, self.mock_method_name, page_message=paging_message)
    messages_written = [
        call_args[0][0] for call_args in mock_write.call_args_list
    ]

    # Make sure a return carriage was written between two pages
    paging_message_call_positions = [
        i for i, message in enumerate(messages_written)
        if message == paging_message
    ]
    self.assertGreater(len(paging_message_call_positions), 1)
    printed_between_page_messages = messages_written[
        paging_message_call_positions[0]:paging_message_call_positions[1]]
    self.assertIn('\r', printed_between_page_messages)

  def test_get_all_pages_ends_paging_message_with_newline(self):
    self.mock_method.return_value.execute.side_effect = self.simple_3_page_response

    paging_message = 'A simple string displayed during paging'
    with patch.object(gapi.sys.stderr, 'write') as mock_write:
      gapi.get_all_pages(
          self.mock_service, self.mock_method_name, page_message=paging_message)
    messages_written = [
        call_args[0][0] for call_args in mock_write.call_args_list
    ]
    last_page_message_index = len(
        messages_written) - messages_written[::-1].index(paging_message)
    last_carriage_return_index = len(
        messages_written) - messages_written[::-1].index('\r\n')
    self.assertGreater(last_carriage_return_index, last_page_message_index)

  def test_get_all_pages_prints_attribute_total_items_in_paging_message(self):
    self.mock_method.return_value.execute.side_effect = self.simple_3_page_response

    paging_message = 'Total number of items discovered: %%total_items%%'
    with patch.object(gapi.sys.stderr, 'write') as mock_write:
      gapi.get_all_pages(
          self.mock_service, self.mock_method_name, page_message=paging_message)

    messages_written = [
        call_args[0][0] for call_args in mock_write.call_args_list
    ]
    page_1_item_count = len(self.simple_3_page_response[0]['items'])
    page_1_message = paging_message.replace('%%total_items%%',
                                            str(page_1_item_count))
    self.assertIn(page_1_message, messages_written)

    page_2_item_count = len(self.simple_3_page_response[1]['items'])
    page_2_message = paging_message.replace(
        '%%total_items%%', str(page_1_item_count + page_2_item_count))
    self.assertIn(page_2_message, messages_written)

    page_3_item_count = len(self.simple_3_page_response[2]['items'])
    page_3_message = paging_message.replace(
        '%%total_items%%',
        str(page_1_item_count + page_2_item_count + page_3_item_count))
    self.assertIn(page_3_message, messages_written)

    # Assert that the template text is always replaced.
    for message in messages_written:
      self.assertNotIn('%%total_items', message)

  def test_get_all_pages_prints_attribute_first_item_in_paging_message(self):
    self.mock_method.return_value.execute.side_effect = self.simple_3_page_response

    paging_message = 'First item in page: %%first_item%%'

    with patch.object(gapi.sys.stderr, 'write') as mock_write:
      gapi.get_all_pages(
          self.mock_service,
          self.mock_method_name,
          page_message=paging_message,
          message_attribute='position')

    messages_written = [
        call_args[0][0] for call_args in mock_write.call_args_list
    ]
    page_1_message = paging_message.replace(
        '%%first_item%%',
        self.simple_3_page_response[0]['items'][0]['position'])
    self.assertIn(page_1_message, messages_written)

    page_2_message = paging_message.replace(
        '%%first_item%%',
        self.simple_3_page_response[1]['items'][0]['position'])
    self.assertIn(page_2_message, messages_written)

    # Assert that the template text is always replaced.
    for message in messages_written:
      self.assertNotIn('%%first_item', message)

  def test_get_all_pages_prints_attribute_last_item_in_paging_message(self):
    self.mock_method.return_value.execute.side_effect = self.simple_3_page_response

    paging_message = 'Last item in page: %%last_item%%'
    with patch.object(gapi.sys.stderr, 'write') as mock_write:
      gapi.get_all_pages(
          self.mock_service,
          self.mock_method_name,
          page_message=paging_message,
          message_attribute='position')

    messages_written = [
        call_args[0][0] for call_args in mock_write.call_args_list
    ]
    page_1_message = paging_message.replace(
        '%%last_item%%',
        self.simple_3_page_response[0]['items'][-1]['position'])
    self.assertIn(page_1_message, messages_written)

    page_2_message = paging_message.replace(
        '%%last_item%%',
        self.simple_3_page_response[1]['items'][-1]['position'])
    self.assertIn(page_2_message, messages_written)

    # Assert that the template text is always replaced.
    for message in messages_written:
      self.assertNotIn('%%last_item', message)

  def test_get_all_pages_prints_all_attributes_in_paging_message(self):
    pass

  def test_get_all_pages_passes_additional_kwargs_to_service_method(self):
    self.mock_method.return_value.execute.return_value = self.empty_items_response
    gapi.get_all_pages(
        self.mock_service, self.mock_method_name, my_param_1=1, my_param_2=2)
    method_kwargs = self.mock_method.call_args[1]
    self.assertEqual(method_kwargs.get('my_param_1'), 1)
    self.assertEqual(method_kwargs.get('my_param_2'), 2)

  @patch.object(gapi, 'call')
  def test_get_all_pages_passes_throw_and_retry_reasons(self, mock_call):
    throw_for = MagicMock()
    retry_for = MagicMock()
    mock_call.return_value = self.empty_items_response
    gapi.get_all_pages(
        self.mock_service,
        self.mock_method_name,
        throw_reasons=throw_for,
        retry_reasons=retry_for)
    method_kwargs = mock_call.call_args[1]
    self.assertEqual(method_kwargs.get('throw_reasons'), throw_for)
    self.assertEqual(method_kwargs.get('retry_reasons'), retry_for)

  def test_get_all_pages_non_default_items_field_name(self):
    field_name = 'things'
    fake_response = {field_name: [{}, {}, {}]}
    self.mock_method.return_value.execute.return_value = fake_response
    page = gapi.get_all_pages(
        self.mock_service, self.mock_method_name, items=field_name)
    self.assertEqual(page, fake_response[field_name])


if __name__ == '__main__':
  unittest.main()
