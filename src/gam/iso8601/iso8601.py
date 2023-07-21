# -*- coding: utf-8 -*-
"""ISO 8601 date time string parsing

"""

from datetime import (datetime, timedelta, tzinfo)
import time as _time
import re

ISO8601_REGEX = re.compile(r'^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})(?P<separator>[ T])(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})([.,](?P<second_fraction>[0-9]+)){0,1}(?P<timezone>Z|(?P<tz_sign>[-+])(?P<tz_hour>[0-9]{2}):(?P<tz_minute>[0-9]{2}))$')
ISO8601_TZ_REGEX = re.compile(r'^(?P<timezone>Z|(?P<tz_sign>[-+])(?P<tz_hour>[0-9]{2}):(?P<tz_minute>[0-9]{2}))$')

class ParseError(Exception):
  """Raised when there is a problem parsing a date string"""

# Yoinked from python docs
ZERO = timedelta(0)
class Utc(tzinfo):
  """UTC Timezone

  """
  def utcoffset(self, dt):
    return ZERO

  def tzname(self, dt):
    return "UTC"

  def dst(self, dt):
    return ZERO

  def __repr__(self):
    return "<iso8601.Utc>"

UTC = Utc()

class FixedOffset(tzinfo):
  """Fixed offset in hours and minutes from UTC

  """
  def __init__(self, offset_hours, offset_minutes, name):
    self.__offset_hours = offset_hours  # Keep for later __getinitargs__
    self.__offset_minutes = offset_minutes  # Keep for later __getinitargs__
    self.__offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    self.__name = name

  def __eq__(self, other):
    if isinstance(other, FixedOffset):
      return (other.__offset == self.__offset) and (other.__name == self.__name)
    if isinstance(other, tzinfo):
      return other == self
    return False

  def __getinitargs__(self):
    return (self.__offset_hours, self.__offset_minutes, self.__name)

  def utcoffset(self, dt):
    return self.__offset

  def tzname(self, dt):
    return self.__name

  def dst(self, dt):
    return ZERO

  def __repr__(self):
    return "<FixedOffset %r %r>" % (self.__name, self.__offset)

# A class capturing the platform's idea of local time.

STDOFFSET = timedelta(seconds = -_time.timezone)
if _time.daylight:
  DSTOFFSET = timedelta(seconds = -_time.altzone)
else:
  DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):
  """Local time zone

  """

  def utcoffset(self, dt):
    if self._isdst(dt):
      return DSTOFFSET
    else:
      return STDOFFSET

  def dst(self, dt):
    if self._isdst(dt):
      return DSTDIFF
    else:
      return ZERO

  def tzname(self, dt):
    return _time.tzname[self._isdst(dt)]

  def _isdst(self, dt):
    tt = (dt.year, dt.month, dt.day,
          dt.hour, dt.minute, dt.second,
          dt.weekday(), 0, 0)
    stamp = _time.mktime(tt)
    tt = _time.localtime(stamp)
    return tt.tm_isdst > 0

Local = LocalTimezone()

def parse_timezone(matches):
  """Parses ISO 8601 time zone specs into tzinfo offsets

  """

  if matches["timezone"] == "Z":
    return UTC
  sign = matches["tz_sign"]
  hours = int(matches['tz_hour'])
  minutes = int(matches['tz_minute'])
  description = "%s%02d:%02d" % (sign, hours, minutes)
  if sign == "-":
    hours = -hours
    minutes = -minutes
  return FixedOffset(hours, minutes, description)

def parse_timezone_str(tzstring):
  m = ISO8601_TZ_REGEX.match(tzstring)
  if not m:
    raise ParseError("Unable to parse timezone string %r" % tzstring)
  groups = m.groupdict()
  return parse_timezone(groups)

def parse_date(datestring):
  """Parses ISO 8601 dates into datetime objects

  The timezone is parsed from the date string. However it is quite common to
  have dates without a timezone (not strictly correct). In this case the
  default timezone specified in default_timezone is used. This is UTC by
  default.

  :param datestring: The date to parse as a string
  :returns: A datetime.datetime instance
  :raises: ParseError when there is a problem parsing the date or
           constructing the datetime instance.

  """
  m = ISO8601_REGEX.match(datestring)
  if not m:
    raise ParseError("Unable to parse date string %r" % datestring)
  groups = m.groupdict()
  tz = parse_timezone(groups)
  try:
    return (datetime(year=int(groups['year']),
                     month=int(groups['month']),
                     day=int(groups['day']),
                     hour=int(groups['hour']),
                     minute=int(groups['minute']),
                     second=int(groups['second']),
                     tzinfo=tz),
            tz)
  except Exception as e:
    raise ParseError(e)
