# -*-*- encoding: utf-8 -*-*-
#
# This is gdata.photos.media, implementing parts of the MediaRSS spec in gdata structures
#
# $Id: __init__.py 81 2007-10-03 14:41:42Z havard.gulldahl $
#
# Copyright 2007 Håvard Gulldahl 
# Portions copyright 2007 Google Inc.
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


"""Essential attributes of photos in Google Photos/Picasa Web Albums are 
expressed using elements from the `media' namespace, defined in the 
MediaRSS specification[1].

Due to copyright issues, the elements herein are documented sparingly, please 
consult with the Google Photos API Reference Guide[2], alternatively the 
official MediaRSS specification[1] for details. 
(If there is a version conflict between the two sources, stick to the 
Google Photos API).

[1]: http://search.yahoo.com/mrss (version 1.1.1)
[2]: http://code.google.com/apis/picasaweb/reference.html#media_reference

Keep in mind that Google Photos only uses a subset of the MediaRSS elements 
(and some of the attributes are trimmed down, too): 

media:content
media:credit
media:description
media:group
media:keywords
media:thumbnail
media:title
"""

__author__ = u'havard@gulldahl.no'# (Håvard Gulldahl)' #BUG: api chokes on non-ascii chars in __author__
__license__ = 'Apache License v2'


import atom
import gdata

MEDIA_NAMESPACE = 'http://search.yahoo.com/mrss/'
YOUTUBE_NAMESPACE = 'http://gdata.youtube.com/schemas/2007'


class MediaBaseElement(atom.AtomBase):
  """Base class for elements in the MEDIA_NAMESPACE. 
  To add new elements, you only need to add the element tag name to self._tag
  """
  
  _tag = ''
  _namespace = MEDIA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, name=None, extension_elements=None,
      extension_attributes=None, text=None):
    self.name = name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


class Content(MediaBaseElement):
  """(attribute container) This element describes the original content,
    e.g. an image or a video. There may be multiple Content elements
    in a media:Group.

    For example, a video may have a
    <media:content medium="image"> element that specifies a JPEG
    representation of the video, and a <media:content medium="video">
    element that specifies the URL of the video itself.
  
  Attributes:
    url: non-ambigous reference to online object
    width: width of the object frame, in pixels
    height: width of the object frame, in pixels
    medium: one of `image' or `video', allowing the api user to quickly
            determine the object's type
    type: Internet media Type[1] (a.k.a. mime type) of the object -- a more
          verbose way of determining the media type. To set the type member
          in the contructor, use the content_type parameter.
    (optional) fileSize: the size of the object, in bytes
  
  [1]: http://en.wikipedia.org/wiki/Internet_media_type
  """
  
  _tag = 'content'
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['url'] = 'url'
  _attributes['width'] = 'width'
  _attributes['height'] = 'height'
  _attributes['medium'] = 'medium'
  _attributes['type'] = 'type'
  _attributes['fileSize'] = 'fileSize'

  def __init__(self, url=None, width=None, height=None,
      medium=None, content_type=None, fileSize=None, format=None,
      extension_elements=None, extension_attributes=None, text=None):
    MediaBaseElement.__init__(self, extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
    self.url = url
    self.width = width
    self.height = height
    self.medium = medium
    self.type = content_type
    self.fileSize = fileSize


def ContentFromString(xml_string):
  return atom.CreateClassFromXMLString(Content, xml_string)


class Credit(MediaBaseElement):
  """(string) Contains the nickname of the user who created the content,
  e.g. `Liz Bennet'.
  
  This is a user-specified value that should be used when referring to
  the user by name.

  Note that none of the attributes from the MediaRSS spec are supported.
  """
  
  _tag = 'credit'


def CreditFromString(xml_string):
  return atom.CreateClassFromXMLString(Credit, xml_string)


class Description(MediaBaseElement):
  """(string) A description of the media object.
  Either plain unicode text, or entity-encoded html (look at the `type'
  attribute).

  E.g `A set of photographs I took while vacationing in Italy.'
  
  For `api' projections, the description is in plain text;
  for `base' projections, the description is in HTML.
  
  Attributes:
    type: either `text' or `html'. To set the type member in the contructor,
          use the description_type parameter.
  """
  
  _tag = 'description'
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['type'] = 'type'
  def __init__(self, description_type=None, 
      extension_elements=None, extension_attributes=None, text=None):
    MediaBaseElement.__init__(self, extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
    
    self.type = description_type


def DescriptionFromString(xml_string):
  return atom.CreateClassFromXMLString(Description, xml_string)


class Keywords(MediaBaseElement):
  """(string) Lists the tags associated with the entry,
  e.g `italy, vacation, sunset'.
  
  Contains a comma-separated list of tags that have been added to the photo, or
  all tags that have been added to photos in the album.
  """
  
  _tag = 'keywords'


def KeywordsFromString(xml_string):
  return atom.CreateClassFromXMLString(Keywords, xml_string)


class Thumbnail(MediaBaseElement):
  """(attributes) Contains the URL of a thumbnail of a photo or album cover.
  
  There can be multiple <media:thumbnail> elements for a given <media:group>; 
  for example, a given item may have multiple thumbnails at different sizes. 
  Photos generally have two thumbnails at different sizes; 
  albums generally have one cropped thumbnail.  
    
  If the thumbsize parameter is set to the initial query, this element points 
  to thumbnails of the requested sizes; otherwise the thumbnails are the 
  default thumbnail size. 
  
  This element must not be confused with the <gphoto:thumbnail> element.
  
  Attributes:
  url:  The URL of the thumbnail image.
  height:  The height of the thumbnail image, in pixels.
  width:  The width of the thumbnail image, in pixels.
  """
  
  _tag = 'thumbnail'
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['url'] = 'url'
  _attributes['width'] = 'width'
  _attributes['height'] = 'height'
  def __init__(self, url=None, width=None, height=None,
      extension_attributes=None, text=None, extension_elements=None):
    MediaBaseElement.__init__(self, extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
    self.url = url
    self.width = width
    self.height = height


def ThumbnailFromString(xml_string):
  return atom.CreateClassFromXMLString(Thumbnail, xml_string)


class Title(MediaBaseElement):
  """(string) Contains the title of the entry's media content, in plain text.
  
  Attributes:
    type: Always set to plain. To set the type member in the constructor, use
          the title_type parameter.
  """
  
  _tag = 'title'
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['type'] = 'type'
  def __init__(self, title_type=None, 
      extension_attributes=None, text=None, extension_elements=None):
    MediaBaseElement.__init__(self, extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
    self.type = title_type


def TitleFromString(xml_string):
  return atom.CreateClassFromXMLString(Title, xml_string)


class Player(MediaBaseElement):
  """(string) Contains the embeddable player URL for the entry's media content 
  if the media is a video.
  
  Attributes:
  url: Always set to plain
  """
  
  _tag = 'player'
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['url'] = 'url'
  
  def __init__(self, player_url=None, 
      extension_attributes=None, extension_elements=None):
    MediaBaseElement.__init__(self, extension_elements=extension_elements,
                              extension_attributes=extension_attributes)
    self.url= player_url


class Private(atom.AtomBase):
  """The YouTube Private element"""
  _tag = 'private'
  _namespace = YOUTUBE_NAMESPACE


class Duration(atom.AtomBase):
  """The YouTube Duration element"""
  _tag = 'duration'
  _namespace = YOUTUBE_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['seconds'] = 'seconds'


class Category(MediaBaseElement):
  """The mediagroup:category element"""

  _tag = 'category'
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['term'] = 'term'
  _attributes['scheme'] = 'scheme'
  _attributes['label'] = 'label'

  def __init__(self, term=None, scheme=None, label=None, text=None, 
               extension_elements=None, extension_attributes=None):
    """Constructor for Category

    Args:
      term: str
      scheme: str
      label: str
      text: str The text data in the this element
      extension_elements: list A  list of ExtensionElement instances
      extension_attributes: dict A dictionary of attribute value string pairs
    """

    self.term = term
    self.scheme = scheme
    self.label = label
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


class Group(MediaBaseElement):
  """Container element for all media elements.
  The <media:group> element can appear as a child of an album, photo or 
  video entry."""

  _tag = 'group'
  _children = atom.AtomBase._children.copy()
  _children['{%s}content' % MEDIA_NAMESPACE] = ('content', [Content,]) 
  _children['{%s}credit' % MEDIA_NAMESPACE] = ('credit', Credit) 
  _children['{%s}description' % MEDIA_NAMESPACE] = ('description', Description) 
  _children['{%s}keywords' % MEDIA_NAMESPACE] = ('keywords', Keywords) 
  _children['{%s}thumbnail' % MEDIA_NAMESPACE] = ('thumbnail', [Thumbnail,])
  _children['{%s}title' % MEDIA_NAMESPACE] = ('title', Title) 
  _children['{%s}category' % MEDIA_NAMESPACE] = ('category', [Category,]) 
  _children['{%s}duration' % YOUTUBE_NAMESPACE] = ('duration', Duration)
  _children['{%s}private' % YOUTUBE_NAMESPACE] = ('private', Private)
  _children['{%s}player' % MEDIA_NAMESPACE] = ('player', Player)

  def __init__(self, content=None, credit=None, description=None, keywords=None,
               thumbnail=None, title=None, duration=None, private=None, 
               category=None, player=None, extension_elements=None, 
               extension_attributes=None, text=None):

    MediaBaseElement.__init__(self, extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
    self.content=content
    self.credit=credit
    self.description=description
    self.keywords=keywords
    self.thumbnail=thumbnail or []
    self.title=title
    self.duration=duration
    self.private=private
    self.category=category or []
    self.player=player


def GroupFromString(xml_string):
  return atom.CreateClassFromXMLString(Group, xml_string)
