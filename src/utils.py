import datetime
import re
import sys
import time
from hashlib import md5
from html.entities import name2codepoint
from html.parser import HTMLParser
import json
import dateutil.parser

import controlflow
import fileutils
import transport
from var import *

class _DeHTMLParser(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self.__text = []

  def handle_data(self, data):
    self.__text.append(data)

  def handle_charref(self, name):
    self.__text.append(chr(int(name[1:], 16)) if name.startswith('x') else chr(int(name)))

  def handle_entityref(self, name):
    cp = name2codepoint.get(name)
    if cp:
      self.__text.append(chr(cp))
    else:
      self.__text.append('&'+name)

  def handle_starttag(self, tag, attrs):
    if tag == 'p':
      self.__text.append('\n\n')
    elif tag == 'br':
      self.__text.append('\n')
    elif tag == 'a':
      for attr in attrs:
        if attr[0] == 'href':
          self.__text.append(f'({attr[1]}) ')
          break
    elif tag == 'div':
      if not attrs:
        self.__text.append('\n')
    elif tag in {'http:', 'https'}:
      self.__text.append(f' ({tag}//{attrs[0][0]}) ')

  def handle_startendtag(self, tag, attrs):
    if tag == 'br':
      self.__text.append('\n\n')

  def text(self):
    return re.sub(r'\n{2}\n+', '\n\n', re.sub(r'\n +', '\n', ''.join(self.__text))).strip()

def dehtml(text):
  try:
    parser = _DeHTMLParser()
    parser.feed(str(text))
    parser.close()
    return parser.text()
  except:
    from traceback import print_exc
    print_exc(file=sys.stderr)
    return text

def indentMultiLineText(message, n=0):
  return message.replace('\n', '\n{0}'.format(' ' * n)).rstrip()

def flatten_json(structure, key='', path='', flattened=None, listLimit=None):
  if flattened is None:
    flattened = {}
  if not isinstance(structure, (dict, list)):
    flattened[((path + '.') if path else '') + key] = structure
  elif isinstance(structure, list):
    for i, item in enumerate(structure):
      if listLimit and (i >= listLimit):
        break
      flatten_json(item, f'{i}', '.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  else:
    for new_key, value in list(structure.items()):
      if new_key in ['kind', 'etag', '@type']:
        continue
      if value == NEVER_TIME:
        value = 'Never'
      flatten_json(value, new_key, '.'.join([item for item in [path, key] if item]), flattened=flattened, listLimit=listLimit)
  return flattened

def formatTimestampYMD(timestamp):
  return datetime.datetime.fromtimestamp(int(timestamp)/1000).strftime('%Y-%m-%d')

def formatTimestampYMDHMS(timestamp):
  return datetime.datetime.fromtimestamp(int(timestamp)/1000).strftime('%Y-%m-%d %H:%M:%S')

def formatTimestampYMDHMSF(timestamp):
  return str(datetime.datetime.fromtimestamp(int(timestamp)/1000))

def formatFileSize(fileSize):
  if fileSize == 0:
    return '0kb'
  if fileSize < ONE_KILO_BYTES:
    return '1kb'
  if fileSize < ONE_MEGA_BYTES:
    return f'{fileSize // ONE_KILO_BYTES}kb'
  if fileSize < ONE_GIGA_BYTES:
    return f'{fileSize // ONE_MEGA_BYTES}mb'
  return f'{fileSize // ONE_GIGA_BYTES}gb'

def formatMilliSeconds(millis):
  seconds, millis = divmod(millis, 1000)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

def integerLimits(minVal, maxVal, item='integer'):
  if (minVal is not None) and (maxVal is not None):
    return f'{item} {minVal}<=x<={maxVal}'
  if minVal is not None:
    return f'{item} x>={minVal}'
  if maxVal is not None:
    return f'{item} x<={maxVal}'
  return f'{item} x'

def get_string(i, item, optional=False, minLen=1, maxLen=None):
  if i < len(sys.argv):
    argstr = sys.argv[i]
    if argstr:
      if (len(argstr) >= minLen) and ((maxLen is None) or (len(argstr) <= maxLen)):
        return argstr
      controlflow.system_error_exit(2, f'expected <{integerLimits(minLen, maxLen, "string length")} for {item}>')
    if optional or (minLen == 0):
      return ''
    controlflow.system_error_exit(2, f'expected a Non-empty <{item}>')
  elif optional:
    return ''
  controlflow.system_error_exit(2, f'expected a <{item}>')

def get_delta(argstr, pattern):
  tg = pattern.match(argstr.lower())
  if tg is None:
    return None
  sign = tg.group(1)
  delta = int(tg.group(2))
  unit = tg.group(3)
  if unit == 'y':
    deltaTime = datetime.timedelta(days=delta*365)
  elif unit == 'w':
    deltaTime = datetime.timedelta(weeks=delta)
  elif unit == 'd':
    deltaTime = datetime.timedelta(days=delta)
  elif unit == 'h':
    deltaTime = datetime.timedelta(hours=delta)
  elif unit == 'm':
    deltaTime = datetime.timedelta(minutes=delta)
  if sign == '-':
    return -deltaTime
  return deltaTime

def get_delta_date(argstr):
  deltaDate = get_delta(argstr, DELTA_DATE_PATTERN)
  if deltaDate is None:
    controlflow.system_error_exit(2, f'expected a <{DELTA_DATE_FORMAT_REQUIRED}>; got {argstr}')
  return deltaDate

def get_delta_time(argstr):
  deltaTime = get_delta(argstr, DELTA_TIME_PATTERN)
  if deltaTime is None:
    controlflow.system_error_exit(2, f'expected a <{DELTA_TIME_FORMAT_REQUIRED}>; got {argstr}')
  return deltaTime

def get_yyyymmdd(argstr, minLen=1, returnTimeStamp=False, returnDateTime=False):
  argstr = argstr.strip()
  if argstr:
    if argstr[0] in ['+', '-']:
      today = datetime.date.today()
      argstr = (datetime.datetime(today.year, today.month, today.day)+get_delta_date(argstr)).strftime(YYYYMMDD_FORMAT)
    try:
      dateTime = datetime.datetime.strptime(argstr, YYYYMMDD_FORMAT)
      if returnTimeStamp:
        return time.mktime(dateTime.timetuple())*1000
      if returnDateTime:
        return dateTime
      return argstr
    except ValueError:
      controlflow.system_error_exit(2, f'expected a <{YYYYMMDD_FORMAT_REQUIRED}>; got {argstr}')
  elif minLen == 0:
    return ''
  controlflow.system_error_exit(2, f'expected a <{YYYYMMDD_FORMAT_REQUIRED}>')

def get_time_or_delta_from_now(time_string):
  """Get an ISO 8601 time or a positive/negative delta applied to now.
  Args:
    time_string (string): The time or delta (e.g. '2017-09-01T12:34:56Z' or '-4h')
  Returns:
    string: iso8601 formatted datetime in UTC.
  """
  time_string = time_string.strip().upper()
  if time_string:
    if time_string[0] not in ['+', '-']:
      return time_string
    return (datetime.datetime.utcnow() + get_delta_time(time_string)).isoformat() + 'Z'
  controlflow.system_error_exit(2, f'expected a <{YYYYMMDDTHHMMSS_FORMAT_REQUIRED}>')

def get_row_filter_date_or_delta_from_now(date_string):
  """Get an ISO 8601 date or a positive/negative delta applied to now.
  Args:
    date_string (string): The time or delta (e.g. '2017-09-01' or '-4y')
  Returns:
    string: iso8601 formatted datetime in UTC.
  """
  date_string = date_string.strip().upper()
  if date_string:
    if date_string[0] in ['+', '-']:
      deltaDate = get_delta(date_string, DELTA_DATE_PATTERN)
      if deltaDate is None:
        return (False, DELTA_DATE_FORMAT_REQUIRED)
      today = datetime.date.today()
      return (True, (datetime.datetime(today.year, today.month, today.day)+deltaDate).isoformat()+'Z')
    try:
      deltaDate = dateutil.parser.parse(date_string, ignoretz=True)
      return (True, datetime.datetime(deltaDate.year, deltaDate.month, deltaDate.day).isoformat()+'Z')
    except ValueError:
      pass
  return (False, YYYYMMDD_FORMAT_REQUIRED)

def get_row_filter_time_or_delta_from_now(time_string):
  """Get an ISO 8601 time or a positive/negative delta applied to now.
  Args:
    time_string (string): The time or delta (e.g. '2017-09-01T12:34:56Z' or '-4h')
  Returns:
    string: iso8601 formatted datetime in UTC.
  Exits:
    2: Not a valid delta.
  """
  time_string = time_string.strip().upper()
  if time_string:
    if time_string[0] in ['+', '-']:
      deltaTime = get_delta(time_string, DELTA_TIME_PATTERN)
      if deltaTime is None:
        return (False, DELTA_TIME_FORMAT_REQUIRED)
      return (True, (datetime.datetime.utcnow()+deltaTime).isoformat()+'Z')
    try:
      deltaTime = dateutil.parser.parse(time_string, ignoretz=True)
      return (True, deltaTime.isoformat()+'Z')
    except ValueError:
      pass
  return (False, YYYYMMDDTHHMMSS_FORMAT_REQUIRED)

def get_date_zero_time_or_full_time(time_string):
  time_string = time_string.strip()
  if time_string:
    if YYYYMMDD_PATTERN.match(time_string):
      return get_yyyymmdd(time_string)+'T00:00:00.000Z'
    return get_time_or_delta_from_now(time_string)
  controlflow.system_error_exit(2, f'expected a <{YYYYMMDDTHHMMSS_FORMAT_REQUIRED}>')

def md5_matches_file(local_file, expected_md5, exitOnError):
  f = fileutils.open_file(local_file, 'rb')
  hash_md5 = md5()
  for chunk in iter(lambda: f.read(4096), b""):
    hash_md5.update(chunk)
  actual_hash = hash_md5.hexdigest()
  if exitOnError and actual_hash != expected_md5:
    controlflow.system_error_exit(6, f'actual hash was {actual_hash}. Exiting on corrupt file.')
  return actual_hash == expected_md5

URL_SHORTENER_ENDPOINT = 'https://gam-shortn.appspot.com/create'

def shorten_url(long_url, httpc=None):
    if not httpc:
        httpc = transport.create_http(timeout=10)
    headers = {'Content-Type': 'application/json', 'User-Agent': GAM_INFO}
    try:
        payload = json.dumps({'long_url': long_url})
        resp, content = httpc.request(
          URL_SHORTENER_ENDPOINT,
          'POST',
          payload,
          headers=headers)
    except:
        return long_url
    if resp.status != 200:
        return long_url
    try:
        if isinstance(content, bytes):
            content = content.decode()
        return json.loads(content).get('short_url', long_url)
    except:
        return long_url
