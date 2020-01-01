"""Python unit tests for gapi.errors"""

import json

import unittest
from unittest.mock import patch

import googleapiclient.errors
from gapi import errors


def create_simple_http_error(status, reason, message):
  content = errors._create_http_error_dict(status, reason, message)
  return create_http_error(status, content)


def create_http_error(status, content):
  response = {
      'status': status,
      'content-type': 'application/json',
  }
  content_as_bytes = json.dumps(content).encode('UTF-8')
  return googleapiclient.errors.HttpError(response, content_as_bytes)


class ErrorsTest(unittest.TestCase):

  def test_get_gapi_error_detail_quota_exceeded(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_detail_invalid_domain(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_detail_invalid_signing_key(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_detail_unknown_error(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_retry_http_error(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_prints_soft_errors(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_exits_on_unrecoverable_errors(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_quota_exceeded_for_current_request(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_quota_exceeded_high_request_rate(self):
    # TODO: Add test logic once the opening ValueError exception case has a
    # repro case (i.e. an Exception type/format that will cause it to raise).
    pass

  def test_get_gapi_error_extracts_user_not_found(self):
    err = create_simple_http_error(404, 'notFound',
                                   'Resource Not Found: userKey.')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 404)
    self.assertEqual(reason, errors.ErrorReason.USER_NOT_FOUND.value)
    self.assertEqual(message, 'Resource Not Found: userKey.')

  def test_get_gapi_error_extracts_group_not_found(self):
    err = create_simple_http_error(404, 'notFound',
                                   'Resource Not Found: groupKey.')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 404)
    self.assertEqual(reason, errors.ErrorReason.GROUP_NOT_FOUND.value)
    self.assertEqual(message, 'Resource Not Found: groupKey.')

  def test_get_gapi_error_extracts_member_not_found(self):
    err = create_simple_http_error(404, 'notFound',
                                   'Resource Not Found: memberKey.')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 404)
    self.assertEqual(reason, errors.ErrorReason.MEMBER_NOT_FOUND.value)
    self.assertEqual(message, 'Resource Not Found: memberKey.')

  def test_get_gapi_error_extracts_domain_not_found(self):
    err = create_simple_http_error(404, 'notFound', 'Domain not found.')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 404)
    self.assertEqual(reason, errors.ErrorReason.DOMAIN_NOT_FOUND.value)
    self.assertEqual(message, 'Domain not found.')

  def test_get_gapi_error_extracts_generic_resource_not_found(self):
    err = create_simple_http_error(404, 'notFound',
                                   'Resource Not Found: unknownResource.')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 404)
    self.assertEqual(reason, errors.ErrorReason.RESOURCE_NOT_FOUND.value)
    self.assertEqual(message, 'Resource Not Found: unknownResource.')

  def test_get_gapi_error_extracts_invalid_userid(self):
    err = create_simple_http_error(400, 'invalid', 'Invalid Input: userId')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 400)
    self.assertEqual(reason, errors.ErrorReason.USER_NOT_FOUND.value)
    self.assertEqual(message, 'Invalid Input: userId')

  def test_get_gapi_error_extracts_invalid_member(self):
    err = create_simple_http_error(400, 'invalid', 'Invalid Input: memberKey')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 400)
    self.assertEqual(reason, errors.ErrorReason.INVALID_MEMBER.value)
    self.assertEqual(message, 'Invalid Input: memberKey')

  def test_get_gapi_error_extracts_bad_request(self):
    err = create_simple_http_error(400, 'failedPrecondition', 'Bad Request')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 400)
    self.assertEqual(reason, errors.ErrorReason.BAD_REQUEST.value)
    self.assertEqual(message, 'Bad Request')

  def test_get_gapi_error_extracts_service_not_available(self):
    err = create_simple_http_error(400, 'failedPrecondition',
                                   'Mail service not enabled')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 400)
    self.assertEqual(reason, errors.ErrorReason.SERVICE_NOT_AVAILABLE.value)
    self.assertEqual(message, 'Mail service not enabled')

  def test_get_gapi_error_extracts_required_member_not_found(self):
    err = create_simple_http_error(400, 'required',
                                   'Missing required field: memberKey')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 400)
    self.assertEqual(reason, errors.ErrorReason.MEMBER_NOT_FOUND.value)
    self.assertEqual(message, 'Missing required field: memberKey')

  def test_get_gapi_error_extracts_cyclic_memberships_error(self):
    err = create_simple_http_error(400, 'conditionNotMet',
                                   'Cyclic memberships not allowed')
    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, 400)
    self.assertEqual(reason,
                     errors.ErrorReason.CYCLIC_MEMBERSHIPS_NOT_ALLOWED.value)
    self.assertEqual(message, 'Cyclic memberships not allowed')

  def test_get_gapi_error_extracts_single_error_with_message(self):
    status_code = 999
    response = {'status': status_code}
    # This error does not have an "errors" key describing each error.
    content = {'error': {'code': status_code, 'message': 'unknown error'}}
    content_as_bytes = json.dumps(content).encode('UTF-8')
    err = googleapiclient.errors.HttpError(response, content_as_bytes)

    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, status_code)
    self.assertEqual(reason, str(status_code))
    self.assertEqual(message, content['error']['message'])

  def test_get_gapi_error_exits_code_4_on_malformed_error_with_unknown_description(
      self):
    status_code = 999
    response = {'status': status_code}
    # This error only has an error_description_field and an unknown description.
    content = {'error_description': 'something errored'}
    content_as_bytes = json.dumps(content).encode('UTF-8')
    err = googleapiclient.errors.HttpError(response, content_as_bytes)

    with self.assertRaises(SystemExit) as context:
      errors.get_gapi_error_detail(err)
    self.assertEqual(4, context.exception.code)

  def test_get_gapi_error_exits_on_invalid_error_description(self):
    status_code = 400
    response = {'status': status_code}
    content = {'error_description': 'Invalid Value'}
    content_as_bytes = json.dumps(content).encode('UTF-8')
    err = googleapiclient.errors.HttpError(response, content_as_bytes)

    http_status, reason, message = errors.get_gapi_error_detail(err)
    self.assertEqual(http_status, status_code)
    self.assertEqual(reason, errors.ErrorReason.INVALID.value)
    self.assertEqual(message, 'Invalid Value')

  def test_get_gapi_error_exits_code_4_on_unexpected_error_contents(self):
    status_code = 900
    response = {'status': status_code}
    content = {'notErrorContentThatIsExpected': 'foo'}
    content_as_bytes = json.dumps(content).encode('UTF-8')
    err = googleapiclient.errors.HttpError(response, content_as_bytes)

    with self.assertRaises(SystemExit) as context:
      errors.get_gapi_error_detail(err)
    self.assertEqual(4, context.exception.code)


if __name__ == '__main__':
  unittest.main()
