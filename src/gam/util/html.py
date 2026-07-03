"""GAM HTML utilities.

Extracted from gam/__init__.py. Provides HTML-to-plain-text conversion.
"""

import re
from html.entities import name2codepoint
from html.parser import HTMLParser


class _DeHTMLParser(HTMLParser): #pylint: disable=abstract-method
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
  parser = _DeHTMLParser()
  parser.feed(str(text))
  parser.close()
  return parser.text()
