import collections
import re
import sys
from htmlentitydefs import name2codepoint
from HTMLParser import HTMLParser
from var import GM_Globals, GM_WINDOWS, GM_SYS_ENCODING

def convertUTF8(data):
  if isinstance(data, str):
    return data
  if isinstance(data, unicode):
    if GM_Globals[GM_WINDOWS]:
      return data
    return data.encode(GM_Globals[GM_SYS_ENCODING])
  if isinstance(data, collections.Mapping):
    return dict(map(convertUTF8, data.iteritems()))
  if isinstance(data, collections.Iterable):
    return type(data)(map(convertUTF8, data))
  return data

class _DeHTMLParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.__text = []

  def handle_data(self, data):
    self.__text.append(data)

  def handle_charref(self, name):
    self.__text.append(unichr(int(name[1:], 16)) if name.startswith('x') else unichr(int(name)))

  def handle_entityref(self, name):
    cp = name2codepoint.get(name)
    if cp:
      self.__text.append(unichr(cp))
    else:
      self.__text.append(u'&'+name)

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
    return re.sub(r'\n{2}\n+', '\n\n', re.sub(r'\n +', '\n', ''.join(self.__text))).strip()

def dehtml(text):
  try:
    parser = _DeHTMLParser()
    parser.feed(text.encode(u'utf-8'))
    parser.close()
    return parser.text()
  except:
    from traceback import print_exc
    print_exc(file=sys.stderr)
    return text

def indentMultiLineText(message, n=0):
  return message.replace(u'\n', u'\n{0}'.format(u' '*n)).rstrip()

def formatMilliSeconds(millis):
  seconds, millis = divmod(millis, 1000)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  return u'%02d:%02d:%02d' % (hours, minutes, seconds)
