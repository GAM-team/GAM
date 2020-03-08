import datetime
import re
import sys
from html.entities import name2codepoint
from html.parser import HTMLParser

from var import *

ONE_KILO_BYTES = 1000
ONE_MEGA_BYTES = 1000000
ONE_GIGA_BYTES = 1000000000


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
