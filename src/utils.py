import datetime
import re
import sys
from html.entities import name2codepoint
from html.parser import HTMLParser

ONE_KILO_BYTES = 1000
ONE_MEGA_BYTES = 1000000
ONE_GIGA_BYTES = 1000000000


def convertUTF8(data):
  return data


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
      self.__text.append('&' + name)

  def handle_starttag(self, tag, attrs):
    if tag == 'p':
      self.__text.append('\n\n')
    elif tag == 'br':
      self.__text.append('\n')
    elif tag == 'a':
      for attr in attrs:
        if attr[0] == 'href':
          self.__text.append('({0}) '.format(attr[1]))
          break
    elif tag == 'div':
      if not attrs:
        self.__text.append('\n')
    elif tag in ['http:', 'https']:
      self.__text.append(' ({0}//{1}) '.format(tag, attrs[0][0]))

  def handle_startendtag(self, tag, attrs):
    if tag == 'br':
      self.__text.append('\n\n')

  def text(self):
    return re.sub(r'\n{2}\n+', '\n\n',
                  re.sub(r'\n +', '\n', ''.join(self.__text))).strip()


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
    return '{0}kb'.format(fileSize // ONE_KILO_BYTES)
  if fileSize < ONE_GIGA_BYTES:
    return '{0}mb'.format(fileSize // ONE_MEGA_BYTES)
  return '{0}gb'.format(fileSize // ONE_GIGA_BYTES)


def formatMilliSeconds(millis):
  seconds, millis = divmod(millis, 1000)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  return '%02d:%02d:%02d' % (hours, minutes, seconds)
