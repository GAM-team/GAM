#!/usr/bin/env python
#
#    Copyright (C) 2010 Google Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# This module is used for version 2 of the Google Data APIs.


__author__ = 'j.s@google.com (Jeff Scudder)'


"""Provides classes and methods for working with JSON-C.

This module is experimental and subject to backwards incompatible changes.

  Jsonc: Class which represents JSON-C data and provides pythonic member
         access which is a bit cleaner than working with plain old dicts.
  parse_json: Converts a JSON-C string into a Jsonc object.
  jsonc_to_string: Converts a Jsonc object into a string of JSON-C.
"""


try:
  import simplejson
except ImportError:
  try:
    # Try to import from django, should work on App Engine
    from django.utils import simplejson 
  except ImportError:
    # Should work for Python2.6 and higher.
    import json as simplejson


def _convert_to_jsonc(x):
  """Builds a Jsonc objects which wraps the argument's members."""

  if isinstance(x, dict):
    jsonc_obj = Jsonc()
    # Recursively transform all members of the dict.
    # When converting a dict, we do not convert _name items into private
    # Jsonc members.
    for key, value in x.iteritems():
      jsonc_obj._dict[key] = _convert_to_jsonc(value)
    return jsonc_obj
  elif isinstance(x, list):
    # Recursively transform all members of the list.
    members = []
    for item in x:
      members.append(_convert_to_jsonc(item))
    return members
  else:
    # Return the base object.
    return x


def parse_json(json_string):
  """Converts a JSON-C string into a Jsonc object.
  
  Args:
    json_string: str or unicode The JSON to be parsed.
  
  Returns:
    A new Jsonc object.
  """

  return _convert_to_jsonc(simplejson.loads(json_string))


def parse_json_file(json_file):
  return _convert_to_jsonc(simplejson.load(json_file))


def jsonc_to_string(jsonc_obj):
  """Converts a Jsonc object into a string of JSON-C."""

  return simplejson.dumps(_convert_to_object(jsonc_obj))


def prettify_jsonc(jsonc_obj, indentation=2):
  """Converts a Jsonc object to a pretified (intented) JSON string."""

  return simplejson.dumps(_convert_to_object(jsonc_obj), indent=indentation)



def _convert_to_object(jsonc_obj):
  """Creates a new dict or list which has the data in the Jsonc object.
  
  Used to convert the Jsonc object to a plain old Python object to simplify
  conversion to a JSON-C string.

  Args:
    jsonc_obj: A Jsonc object to be converted into simple Python objects
               (dicts, lists, etc.)

  Returns:
    Either a dict, list, or other object with members converted from Jsonc
    objects to the corresponding simple Python object.
  """

  if isinstance(jsonc_obj, Jsonc):
    plain = {}
    for key, value in jsonc_obj._dict.iteritems():
      plain[key] = _convert_to_object(value)
    return plain
  elif isinstance(jsonc_obj, list):
    plain = []
    for item in jsonc_obj:
      plain.append(_convert_to_object(item))
    return plain
  else:
    return jsonc_obj


def _to_jsonc_name(member_name):
  """Converts a Python style member name to a JSON-C style name.
  
  JSON-C uses camelCaseWithLower while Python tends to use
  lower_with_underscores so this method converts as follows:

  spam becomes spam
  spam_and_eggs becomes spamAndEggs

  Args:
    member_name: str or unicode The Python syle name which should be
                 converted to JSON-C style.

  Returns: 
    The JSON-C style name as a str or unicode.
  """

  characters = []
  uppercase_next = False
  for character in member_name:
    if character == '_':
      uppercase_next = True
    elif uppercase_next:
      characters.append(character.upper())
      uppercase_next = False
    else:
      characters.append(character)
  return ''.join(characters)


class Jsonc(object):
  """Represents JSON-C data in an easy to access object format.

  To access the members of a JSON structure which looks like this:
  {
    "data": {
      "totalItems": 800,
      "items": [
        {
          "content": {
            "1": "rtsp://v5.cache3.c.youtube.com/CiILENy.../0/0/0/video.3gp"
          },
          "viewCount": 220101,
          "commentCount": 22,
          "favoriteCount": 201
        }
      ]
    },
    "apiVersion": "2.0"
  }

  You would do the following:
  x = gdata.core.parse_json(the_above_string)
  # Gives you 800
  x.data.total_items
  # Should be 22
  x.data.items[0].comment_count
  # The apiVersion is '2.0'
  x.api_version

  To create a Jsonc object which would produce the above JSON, you would do:
  gdata.core.Jsonc(
      api_version='2.0',
      data=gdata.core.Jsonc(
          total_items=800,
          items=[
              gdata.core.Jsonc(
                  view_count=220101,
                  comment_count=22,
                  favorite_count=201,
                  content={
                      '1': ('rtsp://v5.cache3.c.youtube.com'
                            '/CiILENy.../0/0/0/video.3gp')})]))
  or
  x = gdata.core.Jsonc()
  x.api_version = '2.0'
  x.data = gdata.core.Jsonc()
  x.data.total_items = 800
  x.data.items = []
  # etc.

  How it works:
  The JSON-C data is stored in an internal dictionary (._dict) and the
  getattr, setattr, and delattr methods rewrite the name which you provide
  to mirror the expected format in JSON-C. (For more details on name
  conversion see _to_jsonc_name.) You may also access members using
  getitem, setitem, delitem as you would for a dictionary. For example
  x.data.total_items is equivalent to x['data']['totalItems']
  (Not all dict methods are supported so if you need something other than
  the item operations, then you will want to use the ._dict member).

  You may need to use getitem or the _dict member to access certain
  properties in cases where the JSON-C syntax does not map neatly to Python
  objects. For example the YouTube Video feed has some JSON like this:
  "content": {"1": "rtsp://v5.cache3.c.youtube.com..."...}
  You cannot do x.content.1 in Python, so you would use the getitem as
  follows:
  x.content['1']
  or you could use the _dict member as follows:
  x.content._dict['1']

  If you need to create a new object with such a mapping you could use.

  x.content = gdata.core.Jsonc(_dict={'1': 'rtsp://cache3.c.youtube.com...'})
  """

  def __init__(self, _dict=None, **kwargs):
    json = _dict or {}
    for key, value in kwargs.iteritems():
      if key.startswith('_'):
        object.__setattr__(self, key, value)
      else:
        json[_to_jsonc_name(key)] = _convert_to_jsonc(value)

    object.__setattr__(self, '_dict', json)

  def __setattr__(self, name, value):
    if name.startswith('_'):
      object.__setattr__(self, name, value)
    else:
      object.__getattribute__(
          self, '_dict')[_to_jsonc_name(name)] = _convert_to_jsonc(value)

  def __getattr__(self, name):
    if name.startswith('_'):
      object.__getattribute__(self, name)
    else:
      try:
        return object.__getattribute__(self, '_dict')[_to_jsonc_name(name)]
      except KeyError:
        raise AttributeError(
            'No member for %s or [\'%s\']' % (name, _to_jsonc_name(name)))


  def __delattr__(self, name):
    if name.startswith('_'):
      object.__delattr__(self, name)
    else:
      try:
        del object.__getattribute__(self, '_dict')[_to_jsonc_name(name)]
      except KeyError:
        raise AttributeError(
            'No member for %s (or [\'%s\'])' % (name, _to_jsonc_name(name)))

  # For container methods pass-through to the underlying dict.
  def __getitem__(self, key):
    return self._dict[key]

  def __setitem__(self, key, value):
    self._dict[key] = value

  def __delitem__(self, key):
    del self._dict[key]
