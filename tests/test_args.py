"""Unit tests for gam.util.args — argument parsing and formatting functions."""

import pytest
import arrow


class TestCourseScopes:
    """Test course ID and alias scope manipulation."""

    def test_add_course_id_scope_plain(self):
        from gam.util.args import addCourseIdScope
        assert addCourseIdScope('12345') == '12345'  # numeric, no prefix

    def test_add_course_id_scope_name(self):
        from gam.util.args import addCourseIdScope
        assert addCourseIdScope('my-course') == 'd:my-course'

    def test_add_course_id_scope_already_prefixed(self):
        from gam.util.args import addCourseIdScope
        assert addCourseIdScope('d:my-course') == 'd:my-course'
        assert addCourseIdScope('p:my-course') == 'p:my-course'

    def test_remove_course_id_scope(self):
        from gam.util.args import removeCourseIdScope
        assert removeCourseIdScope('d:my-course') == 'my-course'

    def test_remove_course_id_scope_no_prefix(self):
        from gam.util.args import removeCourseIdScope
        assert removeCourseIdScope('12345') == '12345'

    def test_add_course_alias_scope(self):
        from gam.util.args import addCourseAliasScope
        assert addCourseAliasScope('my-alias') == 'd:my-alias'

    def test_add_course_alias_scope_already_prefixed(self):
        from gam.util.args import addCourseAliasScope
        assert addCourseAliasScope('d:my-alias') == 'd:my-alias'
        assert addCourseAliasScope('p:my-alias') == 'p:my-alias'

    def test_remove_course_alias_scope(self):
        from gam.util.args import removeCourseAliasScope
        assert removeCourseAliasScope('d:my-alias') == 'my-alias'

    def test_remove_course_alias_scope_no_prefix(self):
        from gam.util.args import removeCourseAliasScope
        assert removeCourseAliasScope('my-alias') == 'my-alias'


class TestEmailAddressParsing:
    """Test email address parsing and normalization."""

    def test_get_email_domain(self):
        from gam.util.args import getEmailAddressDomain
        assert getEmailAddressDomain('user@domain.com') == 'domain.com'

    def test_get_email_domain_no_at(self):
        from gam.util.args import getEmailAddressDomain
        # Falls back to GC.Values[GC.DOMAIN] which is 'example.com' in conftest
        assert getEmailAddressDomain('justuser') == 'example.com'

    def test_get_email_domain_case(self):
        from gam.util.args import getEmailAddressDomain
        assert getEmailAddressDomain('user@DOMAIN.COM') == 'domain.com'

    def test_get_email_username(self):
        from gam.util.args import getEmailAddressUsername
        assert getEmailAddressUsername('user@domain.com') == 'user'

    def test_get_email_username_no_at(self):
        from gam.util.args import getEmailAddressUsername
        assert getEmailAddressUsername('justuser') == 'justuser'

    def test_split_email(self):
        from gam.util.args import splitEmailAddress
        assert splitEmailAddress('User@Domain.COM') == ('user', 'domain.com')

    def test_split_email_no_at(self):
        from gam.util.args import splitEmailAddress
        assert splitEmailAddress('JustUser') == ('justuser', 'example.com')

    def test_normalize_uid(self):
        from gam.util.args import normalizeEmailAddressOrUID
        # uid: prefix should be stripped
        assert normalizeEmailAddressOrUID('uid:12345') == '12345'

    def test_normalize_email_lowercased(self):
        from gam.util.args import normalizeEmailAddressOrUID
        result = normalizeEmailAddressOrUID('User@Domain.COM')
        assert result == 'user@domain.com'

    def test_normalize_email_no_lower(self):
        from gam.util.args import normalizeEmailAddressOrUID
        result = normalizeEmailAddressOrUID('User@Domain.COM', noLower=True)
        assert result == 'User@Domain.COM'

    def test_normalize_bare_username_gets_domain(self):
        from gam.util.args import normalizeEmailAddressOrUID
        result = normalizeEmailAddressOrUID('admin')
        assert result == 'admin@example.com'


class TestFormatting:
    """Test formatting helper functions."""

    def test_format_milliseconds(self):
        from gam.util.args import formatMilliSeconds
        assert formatMilliSeconds(0) == '00:00:00'
        assert formatMilliSeconds(1000) == '00:00:01'
        assert formatMilliSeconds(61000) == '00:01:01'
        assert formatMilliSeconds(3661000) == '01:01:01'

    def test_format_http_error(self):
        from gam.util.args import formatHTTPError
        result = formatHTTPError(404, 'Not Found', 'Resource missing')
        assert result == '404: Not Found - Resource missing'

    def test_format_max_message_bytes_raw(self):
        from gam.util.args import formatMaxMessageBytes
        assert formatMaxMessageBytes(500, 1024, 1048576) == 500

    def test_format_max_message_bytes_kilobytes(self):
        from gam.util.args import formatMaxMessageBytes
        assert formatMaxMessageBytes(2048, 1024, 1048576) == '2K'

    def test_format_max_message_bytes_megabytes(self):
        from gam.util.args import formatMaxMessageBytes
        assert formatMaxMessageBytes(5242880, 1024, 1048576) == '5M'

    def test_format_file_size_zero(self):
        from gam.util.args import formatFileSize
        assert formatFileSize(0) == '0 KB'

    def test_format_file_size_small(self):
        from gam.util.args import formatFileSize
        assert formatFileSize(500) == '1 KB'


class TestTimestamps:
    """Test timestamp formatting."""

    def test_iso_format_timestamp(self):
        from gam.util.output import ISOformatTimeStamp
        ts = arrow.get('2024-01-15T10:30:00+00:00')
        result = ISOformatTimeStamp(ts)
        assert '2024-01-15' in result
        assert '10:30:00' in result

    def test_current_iso_format_returns_string(self):
        from gam.util.output import currentISOformatTimeStamp
        result = currentISOformatTimeStamp()
        assert isinstance(result, str)
        assert 'T' in result  # ISO format contains T separator


class TestDeltaParsing:
    """Test time delta parsing functions."""

    def test_get_delta_invalid_returns_none(self):
        from gam.util.args import getDelta, DELTA_DATE_PATTERN
        result = getDelta('not-a-delta', DELTA_DATE_PATTERN)
        assert result is None

    def test_get_delta_date(self):
        """Requires GM.DATETIME_NOW to be initialized."""
        import arrow as _arrow
        from gamlib import state as GM
        GM.Globals[GM.DATETIME_NOW] = _arrow.now()

        from gam.util.args import getDeltaDate
        result = getDeltaDate('-30d')
        assert result is not None

    def test_get_delta_time(self):
        """Requires GM.DATETIME_NOW to be initialized."""
        import arrow as _arrow
        from gamlib import state as GM
        GM.Globals[GM.DATETIME_NOW] = _arrow.now()

        from gam.util.args import getDeltaTime
        result = getDeltaTime('-1h')
        assert result is not None
