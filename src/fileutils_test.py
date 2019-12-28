"""Tests for fileutils."""

import io
import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import fileutils


class FileutilsTest(unittest.TestCase):

  def setUp(self):
    self.fake_path = '/some/path/to/file'
    super(FileutilsTest, self).setUp()

  @patch.object(fileutils.sys, 'stdin')
  def test_open_file_stdin(self, mock_stdin):
    mock_stdin.read.return_value = 'some stdin content'
    f = fileutils.open_file('-', mode='r')
    self.assertIsInstance(f, fileutils.io.StringIO)
    self.assertEqual(f.getvalue(), mock_stdin.read.return_value)

  def test_open_file_stdout(self):
    f = fileutils.open_file('-', mode='w')
    self.assertEqual(fileutils.sys.stdout, f)

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_opens_correct_path(self, mock_open):
    f = fileutils.open_file(self.fake_path)
    self.assertEqual(self.fake_path, mock_open.call_args[0][0])
    self.assertEqual(mock_open.return_value, f)

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_expands_user_file_path(self, mock_open):
    file_path = '~/some/path/containing/tilde/shortcut/to/home'
    fileutils.open_file(file_path)
    opened_path = mock_open.call_args[0][0]
    home_path = os.environ.get('HOME')
    self.assertIsNotNone(home_path)
    self.assertIn(home_path, opened_path)

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_opens_correct_mode(self, mock_open):
    fileutils.open_file(self.fake_path)
    self.assertEqual('r', mock_open.call_args[0][1])

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_encoding_for_binary(self, mock_open):
    fileutils.open_file(self.fake_path, mode='b')
    self.assertIsNone(mock_open.call_args[1]['encoding'])

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_default_system_encoding(self, mock_open):
    fileutils.open_file(self.fake_path)
    self.assertEqual(fileutils.GM_Globals[fileutils.GM_SYS_ENCODING],
                     mock_open.call_args[1]['encoding'])

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_utf8_encoding_specified(self, mock_open):
    fileutils.open_file(self.fake_path, encoding='UTF-8')
    self.assertEqual(fileutils.UTF8_SIG, mock_open.call_args[1]['encoding'])

  def test_open_file_strips_utf_bom_in_utf(self):
    bom_prefixed_data = u'\ufefffoobar'
    fake_file = io.StringIO(bom_prefixed_data)
    mock_open = MagicMock(spec=open, return_value=fake_file)
    with patch.object(fileutils, 'open', mock_open):
      f = fileutils.open_file(self.fake_path, strip_utf_bom=True)
      self.assertEqual('foobar', f.read())

  def test_open_file_strips_utf_bom_in_non_utf(self):
    bom_prefixed_data = b'\xef\xbb\xbffoobar'.decode('iso-8859-1')

    # We need to trick the method under test into believing that a StringIO
    # instance is a file with an encoding. Since StringIO does not usually have,
    # an encoding, we'll mock it and add our own encoding, but send the other
    # methods in use (read and seek) back to the real StringIO object.
    real_stringio = io.StringIO(bom_prefixed_data)
    mock_file = MagicMock(spec=io.StringIO)
    mock_file.read.side_effect = real_stringio.read
    mock_file.seek.side_effect = real_stringio.seek
    mock_file.encoding = 'iso-8859-1'

    mock_open = MagicMock(spec=open, return_value=mock_file)
    with patch.object(fileutils, 'open', mock_open):
      f = fileutils.open_file(self.fake_path, strip_utf_bom=True)
      self.assertEqual('foobar', f.read())

  def test_open_file_strips_utf_bom_in_binary(self):
    bom_prefixed_data = u'\ufefffoobar'.encode('UTF-8')
    fake_file = io.BytesIO(bom_prefixed_data)
    mock_open = MagicMock(spec=open, return_value=fake_file)
    with patch.object(fileutils, 'open', mock_open):
      f = fileutils.open_file(self.fake_path, mode='rb', strip_utf_bom=True)
      self.assertEqual(b'foobar', f.read())

  def test_open_file_strip_utf_bom_when_no_bom_in_data(self):
    no_bom_data = 'This data has no BOM'
    fake_file = io.StringIO(no_bom_data)
    mock_open = MagicMock(spec=open, return_value=fake_file)

    with patch.object(fileutils, 'open', mock_open):
      f = fileutils.open_file(self.fake_path, strip_utf_bom=True)
      # Since there was no opening BOM, we should be back at the beginning of
      # the file.
      self.assertEqual(fake_file.tell(), 0)
      self.assertEqual(f.read(), no_bom_data)

  @patch.object(fileutils, 'open', new_callable=unittest.mock.mock_open)
  def test_open_file_exits_on_io_error(self, mock_open):
    mock_open.side_effect = IOError('Fake IOError')
    with self.assertRaises(SystemExit) as context:
      fileutils.open_file(self.fake_path)
    self.assertEqual(context.exception.code, 6)

  def test_close_file_closes_file_successfully(self):
    mock_file = MagicMock()
    self.assertTrue(fileutils.close_file(mock_file))
    self.assertEqual(mock_file.close.call_count, 1)

  def test_close_file_with_error(self):
    mock_file = MagicMock()
    mock_file.close.side_effect = IOError()
    self.assertFalse(fileutils.close_file(mock_file))
    self.assertEqual(mock_file.close.call_count, 1)

  @patch.object(fileutils.sys, 'stdin')
  def test_read_file_from_stdin(self, mock_stdin):
    mock_stdin.read.return_value = 'some stdin content'
    self.assertEqual(fileutils.read_file('-'), mock_stdin.read.return_value)

  @patch.object(fileutils, '_open_file')
  def test_read_file_default_params(self, mock_open_file):
    fake_content = 'some fake content'
    mock_open_file.return_value.__enter__().read.return_value = fake_content
    self.assertEqual(fileutils.read_file(self.fake_path), fake_content)
    self.assertEqual(mock_open_file.call_args[0][0], self.fake_path)
    self.assertEqual(mock_open_file.call_args[0][1], 'r')
    self.assertIsNone(mock_open_file.call_args[1]['newline'])

  @patch.object(fileutils.display, 'print_warning')
  @patch.object(fileutils, '_open_file')
  def test_read_file_continues_on_errors_without_displaying(
      self, mock_open_file, mock_print_warning):
    mock_open_file.side_effect = IOError()
    contents = fileutils.read_file(
        self.fake_path, continue_on_error=True, display_errors=False)
    self.assertIsNone(contents)
    self.assertFalse(mock_print_warning.called)

  @patch.object(fileutils.display, 'print_warning')
  @patch.object(fileutils, '_open_file')
  def test_read_file_displays_errors(self, mock_open_file, mock_print_warning):
    mock_open_file.side_effect = IOError()
    fileutils.read_file(
        self.fake_path, continue_on_error=True, display_errors=True)
    self.assertTrue(mock_print_warning.called)

  @patch.object(fileutils, '_open_file')
  def test_read_file_exits_code_6_when_continue_on_error_is_false(
      self, mock_open_file):
    mock_open_file.side_effect = IOError()
    with self.assertRaises(SystemExit) as context:
      fileutils.read_file(self.fake_path, continue_on_error=False)
    self.assertEqual(context.exception.code, 6)

  @patch.object(fileutils, '_open_file')
  def test_read_file_exits_code_2_on_lookuperror(self, mock_open_file):
    mock_open_file.return_value.__enter__().read.side_effect = LookupError()
    with self.assertRaises(SystemExit) as context:
      fileutils.read_file(self.fake_path)
    self.assertEqual(context.exception.code, 2)

  @patch.object(fileutils, '_open_file')
  def test_read_file_exits_code_2_on_unicodeerror(self, mock_open_file):
    mock_open_file.return_value.__enter__().read.side_effect = UnicodeError()
    with self.assertRaises(SystemExit) as context:
      fileutils.read_file(self.fake_path)
    self.assertEqual(context.exception.code, 2)

  @patch.object(fileutils, '_open_file')
  def test_read_file_exits_code_2_on_unicodedecodeerror(self, mock_open_file):
    fake_decode_error = UnicodeDecodeError('fake-encoding', b'fakebytes', 0, 1,
                                           'testing only')
    mock_open_file.return_value.__enter__().read.side_effect = fake_decode_error
    with self.assertRaises(SystemExit) as context:
      fileutils.read_file(self.fake_path)
    self.assertEqual(context.exception.code, 2)

  @patch.object(fileutils, '_open_file')
  def test_write_file_writes_data_to_file(self, mock_open_file):
    fake_data = 'some fake data'
    fileutils.write_file(self.fake_path, fake_data)
    self.assertEqual(mock_open_file.call_args[0][0], self.fake_path)
    self.assertEqual(mock_open_file.call_args[0][1], 'w')

    opened_file = mock_open_file.return_value.__enter__()
    self.assertTrue(opened_file.write.called)
    self.assertEqual(opened_file.write.call_args[0][0], fake_data)

  @patch.object(fileutils.display, 'print_error')
  @patch.object(fileutils, '_open_file')
  def test_write_file_continues_on_errors_without_displaying(
      self, mock_open_file, mock_print_error):
    mock_open_file.side_effect = IOError()
    status = fileutils.write_file(
        self.fake_path,
        'foo data',
        continue_on_error=True,
        display_errors=False)
    self.assertFalse(status)
    self.assertFalse(mock_print_error.called)

  @patch.object(fileutils.display, 'print_error')
  @patch.object(fileutils, '_open_file')
  def test_write_file_displays_errors(self, mock_open_file, mock_print_error):
    mock_open_file.side_effect = IOError()
    fileutils.write_file(
        self.fake_path, 'foo data', continue_on_error=True, display_errors=True)
    self.assertTrue(mock_print_error.called)

  @patch.object(fileutils, '_open_file')
  def test_write_file_exits_code_6_when_continue_on_error_is_false(
      self, mock_open_file):
    mock_open_file.side_effect = IOError()
    with self.assertRaises(SystemExit) as context:
      fileutils.write_file(self.fake_path, 'foo data', continue_on_error=False)
    self.assertEqual(context.exception.code, 6)


if __name__ == '__main__':
  unittest.main()
