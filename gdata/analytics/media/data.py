#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains the data classes of the Yahoo! Media RSS Extension"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core


MEDIA_TEMPLATE = '{http://search.yahoo.com/mrss//}%s'


class MediaCategory(atom.core.XmlElement):
  """Describes a media category."""
  _qname = MEDIA_TEMPLATE % 'category'
  scheme = 'scheme'
  label = 'label'


class MediaCopyright(atom.core.XmlElement):
  """Describes a media copyright."""
  _qname = MEDIA_TEMPLATE % 'copyright'
  url = 'url'


class MediaCredit(atom.core.XmlElement):
  """Describes a media credit."""
  _qname = MEDIA_TEMPLATE % 'credit'
  role = 'role'
  scheme = 'scheme'


class MediaDescription(atom.core.XmlElement):
  """Describes a media description."""
  _qname = MEDIA_TEMPLATE % 'description'
  type = 'type'


class MediaHash(atom.core.XmlElement):
  """Describes a media hash."""
  _qname = MEDIA_TEMPLATE % 'hash'
  algo = 'algo'


class MediaKeywords(atom.core.XmlElement):
  """Describes a media keywords."""
  _qname = MEDIA_TEMPLATE % 'keywords'


class MediaPlayer(atom.core.XmlElement):
  """Describes a media player."""
  _qname = MEDIA_TEMPLATE % 'player'
  height = 'height'
  width = 'width'
  url = 'url'


class MediaRating(atom.core.XmlElement):
  """Describes a media rating."""
  _qname = MEDIA_TEMPLATE % 'rating'
  scheme = 'scheme'


class MediaRestriction(atom.core.XmlElement):
  """Describes a media restriction."""
  _qname = MEDIA_TEMPLATE % 'restriction'
  relationship = 'relationship'
  type = 'type'


class MediaText(atom.core.XmlElement):
  """Describes a media text."""
  _qname = MEDIA_TEMPLATE % 'text'
  end = 'end'
  lang = 'lang'
  type = 'type'
  start = 'start'


class MediaThumbnail(atom.core.XmlElement):
  """Describes a media thumbnail."""
  _qname = MEDIA_TEMPLATE % 'thumbnail'
  time = 'time'
  url = 'url'
  width = 'width'
  height = 'height'


class MediaTitle(atom.core.XmlElement):
  """Describes a media title."""
  _qname = MEDIA_TEMPLATE % 'title'
  type = 'type'


class MediaContent(atom.core.XmlElement):
  """Describes a media content."""
  _qname = MEDIA_TEMPLATE % 'content'
  bitrate = 'bitrate'
  is_default = 'isDefault'
  medium = 'medium'
  height = 'height'
  credit = [MediaCredit]
  language = 'language'
  hash = MediaHash
  width = 'width'
  player = MediaPlayer
  url = 'url'
  file_size = 'fileSize'
  channels = 'channels'
  expression = 'expression'
  text = [MediaText]
  samplingrate = 'samplingrate'
  title = MediaTitle
  category = [MediaCategory]
  rating = [MediaRating]
  type = 'type'
  description = MediaDescription
  framerate = 'framerate'
  thumbnail = [MediaThumbnail]
  duration = 'duration'
  copyright = MediaCopyright
  keywords = MediaKeywords
  restriction = [MediaRestriction]


class MediaGroup(atom.core.XmlElement):
  """Describes a media group."""
  _qname = MEDIA_TEMPLATE % 'group'
  credit = [MediaCredit]
  content = [MediaContent]
  copyright = MediaCopyright
  description = MediaDescription
  category = [MediaCategory]
  player = MediaPlayer
  rating = [MediaRating]
  hash = MediaHash
  title = MediaTitle
  keywords = MediaKeywords
  restriction = [MediaRestriction]
  thumbnail = [MediaThumbnail]
  text = [MediaText]


