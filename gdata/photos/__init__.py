# -*-*- encoding: utf-8 -*-*-
#
# This is the base file for the PicasaWeb python client.
# It is used for lower level operations.
#
# $Id: __init__.py 148 2007-10-28 15:09:19Z havard.gulldahl $
#
# Copyright 2007 Håvard Gulldahl 
# Portions (C) 2006 Google Inc.
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

"""This module provides a pythonic, gdata-centric interface to Google Photos
(a.k.a. Picasa Web Services.

It is modelled after the gdata/* interfaces from the gdata-python-client
project[1] by Google. 

You'll find the user-friendly api in photos.service. Please see the
documentation or live help() system for available methods.

[1]: http://gdata-python-client.googlecode.com/

  """

__author__ = u'havard@gulldahl.no'# (Håvard Gulldahl)' #BUG: pydoc chokes on non-ascii chars in __author__
__license__ = 'Apache License v2'
__version__ = '$Revision: 164 $'[11:-2]

import re
try:
  from xml.etree import cElementTree as ElementTree
except ImportError:
  try:
    import cElementTree as ElementTree
  except ImportError:
    try:
      from xml.etree import ElementTree
    except ImportError:
      from elementtree import ElementTree
import atom
import gdata

# importing google photo submodules
import gdata.media as Media, gdata.exif as Exif, gdata.geo as Geo

# XML namespaces which are often used in Google Photo elements
PHOTOS_NAMESPACE = 'http://schemas.google.com/photos/2007'
MEDIA_NAMESPACE = 'http://search.yahoo.com/mrss/'
EXIF_NAMESPACE = 'http://schemas.google.com/photos/exif/2007'
OPENSEARCH_NAMESPACE = 'http://a9.com/-/spec/opensearchrss/1.0/'
GEO_NAMESPACE = 'http://www.w3.org/2003/01/geo/wgs84_pos#'
GML_NAMESPACE = 'http://www.opengis.net/gml'
GEORSS_NAMESPACE = 'http://www.georss.org/georss'
PHEED_NAMESPACE = 'http://www.pheed.com/pheed/'
BATCH_NAMESPACE = 'http://schemas.google.com/gdata/batch'


class PhotosBaseElement(atom.AtomBase):
  """Base class for elements in the PHOTO_NAMESPACE. To add new elements,
  you only need to add the element tag name to self._tag
  """
  
  _tag = ''
  _namespace = PHOTOS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()

  def __init__(self, name=None, extension_elements=None,
      extension_attributes=None, text=None):
    self.name = name
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
  #def __str__(self):
    #return str(self.text)
  #def __unicode__(self):
    #return unicode(self.text)
  def __int__(self):
    return int(self.text)
  def bool(self):
    return self.text == 'true'

class GPhotosBaseFeed(gdata.GDataFeed, gdata.LinkFinder):
  "Base class for all Feeds in gdata.photos"
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _attributes = gdata.GDataFeed._attributes.copy()
  _children = gdata.GDataFeed._children.copy()
  # We deal with Entry elements ourselves
  del _children['{%s}entry' % atom.ATOM_NAMESPACE]
    
  def __init__(self, author=None, category=None, contributor=None,
               generator=None, icon=None, atom_id=None, link=None, logo=None,
               rights=None, subtitle=None, title=None, updated=None,
               entry=None, total_results=None, start_index=None,
               items_per_page=None, extension_elements=None,
               extension_attributes=None, text=None):
    gdata.GDataFeed.__init__(self, author=author, category=category,
                             contributor=contributor, generator=generator,
                             icon=icon,  atom_id=atom_id, link=link,
                             logo=logo, rights=rights, subtitle=subtitle,
                             title=title, updated=updated, entry=entry,
                             total_results=total_results,
                             start_index=start_index,
                             items_per_page=items_per_page,
                             extension_elements=extension_elements,
                             extension_attributes=extension_attributes,
                             text=text)

  def kind(self):
    "(string) Returns the kind"
    try:
      return self.category[0].term.split('#')[1]
    except IndexError:
      return None
  
  def _feedUri(self, kind):
    "Convenience method to return a uri to a feed of a special kind"
    assert(kind in ('album', 'tag', 'photo', 'comment', 'user'))
    here_href = self.GetSelfLink().href
    if 'kind=%s' % kind in here_href:
      return here_href
    if not 'kind=' in here_href:
      sep = '?'
      if '?' in here_href: sep = '&'
      return here_href + "%skind=%s" % (sep, kind)
    rx = re.match('.*(kind=)(album|tag|photo|comment)', here_href)
    return here_href[:rx.end(1)] + kind + here_href[rx.end(2):]
  
  def _ConvertElementTreeToMember(self, child_tree):
    """Re-implementing the method from AtomBase, since we deal with
      Entry elements specially"""
    category = child_tree.find('{%s}category' % atom.ATOM_NAMESPACE)
    if category is None:
      return atom.AtomBase._ConvertElementTreeToMember(self, child_tree)
    namespace, kind = category.get('term').split('#')
    if namespace != PHOTOS_NAMESPACE:
      return atom.AtomBase._ConvertElementTreeToMember(self, child_tree)
    ## TODO: is it safe to use getattr on gdata.photos?
    entry_class = getattr(gdata.photos, '%sEntry' % kind.title())
    if not hasattr(self, 'entry') or self.entry is None:
      self.entry = []
    self.entry.append(atom._CreateClassFromElementTree(
        entry_class, child_tree))

class GPhotosBaseEntry(gdata.GDataEntry, gdata.LinkFinder):
  "Base class for all Entry elements in gdata.photos"
  _tag = 'entry'
  _kind = ''
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
    
  def __init__(self, author=None, category=None, content=None,
      atom_id=None, link=None, published=None,
      title=None, updated=None,
      extended_property=None,
      extension_elements=None, extension_attributes=None, text=None):
    gdata.GDataEntry.__init__(self, author=author, category=category,
                        content=content, atom_id=atom_id, link=link,
                        published=published, title=title,
                        updated=updated, text=text,
                        extension_elements=extension_elements,
                        extension_attributes=extension_attributes)
    self.category.append(
      atom.Category(scheme='http://schemas.google.com/g/2005#kind', 
              term = 'http://schemas.google.com/photos/2007#%s' % self._kind))

  def kind(self):
    "(string) Returns the kind"
    try:
      return self.category[0].term.split('#')[1]
    except IndexError:
      return None
  
  def _feedUri(self, kind):
    "Convenience method to get the uri to this entry's feed of the some kind"
    try:
      href = self.GetFeedLink().href
    except AttributeError:
      return None
    sep = '?'
    if '?' in href: sep = '&'
    return '%s%skind=%s' % (href, sep, kind)


class PhotosBaseEntry(GPhotosBaseEntry):
  pass

class PhotosBaseFeed(GPhotosBaseFeed):
  pass

class GPhotosBaseData(object):
  pass

class Access(PhotosBaseElement):
  """The Google Photo `Access' element.

  The album's access level. Valid values are `public' or `private'.
  In documentation, access level is also referred to as `visibility.'"""
  
  _tag = 'access'
def AccessFromString(xml_string):
  return atom.CreateClassFromXMLString(Access, xml_string)

class Albumid(PhotosBaseElement):
  "The Google Photo `Albumid' element"
  
  _tag = 'albumid'
def AlbumidFromString(xml_string):
  return atom.CreateClassFromXMLString(Albumid, xml_string)

class BytesUsed(PhotosBaseElement):
  "The Google Photo `BytesUsed' element"
  
  _tag = 'bytesUsed'
def BytesUsedFromString(xml_string):
  return atom.CreateClassFromXMLString(BytesUsed, xml_string)

class Client(PhotosBaseElement):
  "The Google Photo `Client' element"
  
  _tag = 'client'
def ClientFromString(xml_string):
  return atom.CreateClassFromXMLString(Client, xml_string)

class Checksum(PhotosBaseElement):
  "The Google Photo `Checksum' element"
  
  _tag = 'checksum'
def ChecksumFromString(xml_string):
  return atom.CreateClassFromXMLString(Checksum, xml_string)

class CommentCount(PhotosBaseElement):
  "The Google Photo `CommentCount' element"
  
  _tag = 'commentCount'
def CommentCountFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentCount, xml_string)

class CommentingEnabled(PhotosBaseElement):
  "The Google Photo `CommentingEnabled' element"
  
  _tag = 'commentingEnabled'
def CommentingEnabledFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentingEnabled, xml_string)

class Height(PhotosBaseElement):
  "The Google Photo `Height' element"
  
  _tag = 'height'
def HeightFromString(xml_string):
  return atom.CreateClassFromXMLString(Height, xml_string)

class Id(PhotosBaseElement):
  "The Google Photo `Id' element"
  
  _tag = 'id'
def IdFromString(xml_string):
  return atom.CreateClassFromXMLString(Id, xml_string)

class Location(PhotosBaseElement):
  "The Google Photo `Location' element"
  
  _tag = 'location'
def LocationFromString(xml_string):
  return atom.CreateClassFromXMLString(Location, xml_string)

class MaxPhotosPerAlbum(PhotosBaseElement):
  "The Google Photo `MaxPhotosPerAlbum' element"
  
  _tag = 'maxPhotosPerAlbum'
def MaxPhotosPerAlbumFromString(xml_string):
  return atom.CreateClassFromXMLString(MaxPhotosPerAlbum, xml_string)

class Name(PhotosBaseElement):
  "The Google Photo `Name' element"
  
  _tag = 'name'
def NameFromString(xml_string):
  return atom.CreateClassFromXMLString(Name, xml_string)

class Nickname(PhotosBaseElement):
  "The Google Photo `Nickname' element"
  
  _tag = 'nickname'
def NicknameFromString(xml_string):
  return atom.CreateClassFromXMLString(Nickname, xml_string)

class Numphotos(PhotosBaseElement):
  "The Google Photo `Numphotos' element"
  
  _tag = 'numphotos'
def NumphotosFromString(xml_string):
  return atom.CreateClassFromXMLString(Numphotos, xml_string)

class Numphotosremaining(PhotosBaseElement):
  "The Google Photo `Numphotosremaining' element"
  
  _tag = 'numphotosremaining'
def NumphotosremainingFromString(xml_string):
  return atom.CreateClassFromXMLString(Numphotosremaining, xml_string)

class Position(PhotosBaseElement):
  "The Google Photo `Position' element"
  
  _tag = 'position'
def PositionFromString(xml_string):
  return atom.CreateClassFromXMLString(Position, xml_string)

class Photoid(PhotosBaseElement):
  "The Google Photo `Photoid' element"
  
  _tag = 'photoid'
def PhotoidFromString(xml_string):
  return atom.CreateClassFromXMLString(Photoid, xml_string)

class Quotacurrent(PhotosBaseElement):
  "The Google Photo `Quotacurrent' element"
  
  _tag = 'quotacurrent'
def QuotacurrentFromString(xml_string):
  return atom.CreateClassFromXMLString(Quotacurrent, xml_string)

class Quotalimit(PhotosBaseElement):
  "The Google Photo `Quotalimit' element"
  
  _tag = 'quotalimit'
def QuotalimitFromString(xml_string):
  return atom.CreateClassFromXMLString(Quotalimit, xml_string)

class Rotation(PhotosBaseElement):
  "The Google Photo `Rotation' element"
  
  _tag = 'rotation'
def RotationFromString(xml_string):
  return atom.CreateClassFromXMLString(Rotation, xml_string)

class Size(PhotosBaseElement):
  "The Google Photo `Size' element"
  
  _tag = 'size'
def SizeFromString(xml_string):
  return atom.CreateClassFromXMLString(Size, xml_string)

class Snippet(PhotosBaseElement):
  """The Google Photo `snippet' element.

  When searching, the snippet element will contain a 
  string with the word you're looking for, highlighted in html markup
  E.g. when your query is `hafjell', this element may contain:
  `... here at <b>Hafjell</b>.'

  You'll find this element in searches -- that is, feeds that combine the 
  `kind=photo' and `q=yoursearch' parameters in the request.

  See also gphoto:truncated and gphoto:snippettype.
  
  """
  
  _tag = 'snippet'
def SnippetFromString(xml_string):
  return atom.CreateClassFromXMLString(Snippet, xml_string)

class Snippettype(PhotosBaseElement):
  """The Google Photo `Snippettype' element

  When searching, this element will tell you the type of element that matches.

  You'll find this element in searches -- that is, feeds that combine the 
  `kind=photo' and `q=yoursearch' parameters in the request.

  See also gphoto:snippet and gphoto:truncated.
  
  Possible values and their interpretation: 
  o ALBUM_TITLE       - The album title matches 
  o PHOTO_TAGS        - The match is a tag/keyword
  o PHOTO_DESCRIPTION - The match is in the photo's description

  If you discover a value not listed here, please submit a patch to update this docstring.
  
  """
  
  _tag = 'snippettype'
def SnippettypeFromString(xml_string):
  return atom.CreateClassFromXMLString(Snippettype, xml_string)

class Thumbnail(PhotosBaseElement):
  """The Google Photo `Thumbnail' element

  Used to display user's photo thumbnail (hackergotchi).
  
  (Not to be confused with the <media:thumbnail> element, which gives you
  small versions of the photo object.)"""
  
  _tag = 'thumbnail'
def ThumbnailFromString(xml_string):
  return atom.CreateClassFromXMLString(Thumbnail, xml_string)

class Timestamp(PhotosBaseElement):
  """The Google Photo `Timestamp' element
  Represented as the number of milliseconds since January 1st, 1970.
  
  
  Take a look at the convenience methods .isoformat() and .datetime():

  photo_epoch     = Time.text        # 1180294337000
  photo_isostring = Time.isoformat() # '2007-05-27T19:32:17.000Z'

  Alternatively: 
  photo_datetime  = Time.datetime()  # (requires python >= 2.3)
  """
  
  _tag = 'timestamp'
  def isoformat(self):
    """(string) Return the timestamp as a ISO 8601 formatted string,
    e.g. '2007-05-27T19:32:17.000Z'
    """
    import time
    epoch = float(self.text)/1000
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(epoch))
  
  def datetime(self):
    """(datetime.datetime) Return the timestamp as a datetime.datetime object

    Requires python 2.3
    """
    import datetime
    epoch = float(self.text)/1000
    return datetime.datetime.fromtimestamp(epoch)
def TimestampFromString(xml_string):
  return atom.CreateClassFromXMLString(Timestamp, xml_string)

class Truncated(PhotosBaseElement):
  """The Google Photo `Truncated' element

  You'll find this element in searches -- that is, feeds that combine the 
  `kind=photo' and `q=yoursearch' parameters in the request.

  See also gphoto:snippet and gphoto:snippettype.
  
  Possible values and their interpretation:
  0 -- unknown 
  """
  
  _tag = 'Truncated'
def TruncatedFromString(xml_string):
  return atom.CreateClassFromXMLString(Truncated, xml_string)

class User(PhotosBaseElement):
  "The Google Photo `User' element"
  
  _tag = 'user'
def UserFromString(xml_string):
  return atom.CreateClassFromXMLString(User, xml_string)

class Version(PhotosBaseElement):
  "The Google Photo `Version' element"
  
  _tag = 'version'
def VersionFromString(xml_string):
  return atom.CreateClassFromXMLString(Version, xml_string)

class Width(PhotosBaseElement):
  "The Google Photo `Width' element"
  
  _tag = 'width'
def WidthFromString(xml_string):
  return atom.CreateClassFromXMLString(Width, xml_string)

class Weight(PhotosBaseElement):
  """The Google Photo `Weight' element.

  The weight of the tag is the number of times the tag
  appears in the collection of tags currently being viewed.
  The default weight is 1, in which case this tags is omitted."""
  _tag = 'weight'
def WeightFromString(xml_string):
  return atom.CreateClassFromXMLString(Weight, xml_string)

class CommentAuthor(atom.Author):
  """The Atom `Author' element in CommentEntry entries is augmented to
  contain elements from the PHOTOS_NAMESPACE

  http://groups.google.com/group/Google-Picasa-Data-API/msg/819b0025b5ff5e38
  """
  _children = atom.Author._children.copy()
  _children['{%s}user' % PHOTOS_NAMESPACE] = ('user', User)
  _children['{%s}nickname' % PHOTOS_NAMESPACE] = ('nickname', Nickname)
  _children['{%s}thumbnail' % PHOTOS_NAMESPACE] = ('thumbnail', Thumbnail)
def CommentAuthorFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentAuthor, xml_string)

########################## ################################

class AlbumData(object):
  _children = {}
  _children['{%s}id' % PHOTOS_NAMESPACE] = ('gphoto_id', Id) 
  _children['{%s}name' % PHOTOS_NAMESPACE] = ('name', Name)
  _children['{%s}location' % PHOTOS_NAMESPACE] = ('location', Location)
  _children['{%s}access' % PHOTOS_NAMESPACE] = ('access', Access)
  _children['{%s}bytesUsed' % PHOTOS_NAMESPACE] = ('bytesUsed', BytesUsed)
  _children['{%s}timestamp' % PHOTOS_NAMESPACE] = ('timestamp', Timestamp)
  _children['{%s}numphotos' % PHOTOS_NAMESPACE] = ('numphotos', Numphotos)
  _children['{%s}numphotosremaining' % PHOTOS_NAMESPACE] = \
    ('numphotosremaining', Numphotosremaining)
  _children['{%s}user' % PHOTOS_NAMESPACE] = ('user', User)
  _children['{%s}nickname' % PHOTOS_NAMESPACE] = ('nickname', Nickname)
  _children['{%s}commentingEnabled' % PHOTOS_NAMESPACE] = \
    ('commentingEnabled', CommentingEnabled)
  _children['{%s}commentCount' % PHOTOS_NAMESPACE] = \
    ('commentCount', CommentCount)
  ## NOTE: storing media:group as self.media, to create a self-explaining api
  gphoto_id = None
  name = None
  location = None
  access = None
  bytesUsed = None
  timestamp = None
  numphotos = None
  numphotosremaining = None
  user = None
  nickname = None
  commentingEnabled = None
  commentCount = None

class AlbumEntry(GPhotosBaseEntry, AlbumData):
  """All metadata for a Google Photos Album

  Take a look at AlbumData for metadata accessible as attributes to this object.

  Notes:
    To avoid name clashes, and to create a more sensible api, some
    objects have names that differ from the original elements:
  
    o media:group -> self.media,
    o geo:where -> self.geo,
    o photo:id -> self.gphoto_id
  """
  
  _kind = 'album'
  _children = GPhotosBaseEntry._children.copy()
  _children.update(AlbumData._children.copy())
  # child tags only for Album entries, not feeds
  _children['{%s}where' % GEORSS_NAMESPACE] = ('geo', Geo.Where)
  _children['{%s}group' % MEDIA_NAMESPACE] = ('media', Media.Group)
  media = Media.Group()
  geo = Geo.Where()
  
  def __init__(self, author=None, category=None, content=None,
      atom_id=None, link=None, published=None,
      title=None, updated=None,
      #GPHOTO NAMESPACE:
      gphoto_id=None, name=None, location=None, access=None, 
      timestamp=None, numphotos=None, user=None, nickname=None,
      commentingEnabled=None, commentCount=None, thumbnail=None,
      # MEDIA NAMESPACE:
      media=None,
      # GEORSS NAMESPACE:
      geo=None,
      extended_property=None,
      extension_elements=None, extension_attributes=None, text=None):
    GPhotosBaseEntry.__init__(self, author=author, category=category,
                        content=content, atom_id=atom_id, link=link,
                        published=published, title=title,
                        updated=updated, text=text,
                        extension_elements=extension_elements,
                        extension_attributes=extension_attributes)

    ## NOTE: storing photo:id as self.gphoto_id, to avoid name clash with atom:id
    self.gphoto_id = gphoto_id 
    self.name = name
    self.location = location
    self.access = access
    self.timestamp = timestamp
    self.numphotos = numphotos
    self.user = user
    self.nickname = nickname
    self.commentingEnabled = commentingEnabled
    self.commentCount = commentCount
    self.thumbnail = thumbnail
    self.extended_property = extended_property or []
    self.text = text
    ## NOTE: storing media:group as self.media, and geo:where as geo,
    ## to create a self-explaining api
    self.media = media or Media.Group()
    self.geo = geo or Geo.Where()

  def GetAlbumId(self):
    "Return the id of this album"
    
    return self.GetFeedLink().href.split('/')[-1]
          
  def GetPhotosUri(self):
    "(string) Return the uri to this albums feed of the PhotoEntry kind"
    return self._feedUri('photo')
  
  def GetCommentsUri(self):
    "(string) Return the uri to this albums feed of the CommentEntry kind"
    return self._feedUri('comment')
  
  def GetTagsUri(self):
    "(string) Return the uri to this albums feed of the TagEntry kind"
    return self._feedUri('tag')

def AlbumEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(AlbumEntry, xml_string)
  
class AlbumFeed(GPhotosBaseFeed, AlbumData):
  """All metadata for a Google Photos Album, including its sub-elements
  
  This feed represents an album as the container for other objects.

  A Album feed contains entries of
  PhotoEntry, CommentEntry or TagEntry,
  depending on the `kind' parameter in the original query.

  Take a look at AlbumData for accessible attributes.
  
  """
  
  _children = GPhotosBaseFeed._children.copy()
  _children.update(AlbumData._children.copy())

  def GetPhotosUri(self):
    "(string) Return the uri to the same feed, but of the PhotoEntry kind"
    
    return self._feedUri('photo')
         
  def GetTagsUri(self):
    "(string) Return the uri to the same feed, but of the TagEntry kind"

    return self._feedUri('tag')
    
  def GetCommentsUri(self):
    "(string) Return the uri to the same feed, but of the CommentEntry kind"

    return self._feedUri('comment')
  
def AlbumFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(AlbumFeed, xml_string)


class PhotoData(object):
  _children = {}
  ## NOTE: storing photo:id as self.gphoto_id, to avoid name clash with atom:id
  _children['{%s}id' % PHOTOS_NAMESPACE] = ('gphoto_id', Id) 
  _children['{%s}albumid' % PHOTOS_NAMESPACE] = ('albumid', Albumid)
  _children['{%s}checksum' % PHOTOS_NAMESPACE] = ('checksum', Checksum)
  _children['{%s}client' % PHOTOS_NAMESPACE] = ('client', Client)
  _children['{%s}height' % PHOTOS_NAMESPACE] = ('height', Height)
  _children['{%s}position' % PHOTOS_NAMESPACE] = ('position', Position)
  _children['{%s}rotation' % PHOTOS_NAMESPACE] = ('rotation', Rotation)
  _children['{%s}size' % PHOTOS_NAMESPACE] = ('size', Size)
  _children['{%s}timestamp' % PHOTOS_NAMESPACE] = ('timestamp', Timestamp)
  _children['{%s}version' % PHOTOS_NAMESPACE] = ('version', Version)
  _children['{%s}width' % PHOTOS_NAMESPACE] = ('width', Width)
  _children['{%s}commentingEnabled' % PHOTOS_NAMESPACE] = \
    ('commentingEnabled', CommentingEnabled)
  _children['{%s}commentCount' % PHOTOS_NAMESPACE] = \
    ('commentCount', CommentCount)
  ## NOTE: storing media:group as self.media, exif:tags as self.exif, and
  ## geo:where as self.geo, to create a self-explaining api
  _children['{%s}tags' % EXIF_NAMESPACE] = ('exif', Exif.Tags)
  _children['{%s}where' % GEORSS_NAMESPACE] = ('geo', Geo.Where)
  _children['{%s}group' % MEDIA_NAMESPACE] = ('media', Media.Group)
  # These elements show up in search feeds 
  _children['{%s}snippet' % PHOTOS_NAMESPACE] = ('snippet', Snippet)
  _children['{%s}snippettype' % PHOTOS_NAMESPACE] = ('snippettype', Snippettype)
  _children['{%s}truncated' % PHOTOS_NAMESPACE] = ('truncated', Truncated)
  gphoto_id = None
  albumid = None
  checksum = None
  client = None
  height = None
  position = None
  rotation = None
  size = None
  timestamp = None
  version = None
  width = None
  commentingEnabled = None
  commentCount = None
  snippet=None
  snippettype=None
  truncated=None
  media = Media.Group()
  geo = Geo.Where()
  tags = Exif.Tags()

class PhotoEntry(GPhotosBaseEntry, PhotoData):
  """All metadata for a Google Photos Photo

  Take a look at PhotoData for metadata accessible as attributes to this object.

  Notes:
    To avoid name clashes, and to create a more sensible api, some
    objects have names that differ from the original elements:
  
    o media:group -> self.media,
    o exif:tags -> self.exif,
    o geo:where -> self.geo,
    o photo:id -> self.gphoto_id
  """

  _kind = 'photo'
  _children = GPhotosBaseEntry._children.copy()
  _children.update(PhotoData._children.copy())
  
  def __init__(self, author=None, category=None, content=None,
      atom_id=None, link=None, published=None, 
      title=None, updated=None, text=None,
      # GPHOTO NAMESPACE:
      gphoto_id=None, albumid=None, checksum=None, client=None, height=None,
      position=None, rotation=None, size=None, timestamp=None, version=None,
      width=None, commentCount=None, commentingEnabled=None,
      # MEDIARSS NAMESPACE:
      media=None,
      # EXIF_NAMESPACE:
      exif=None,
      # GEORSS NAMESPACE:
      geo=None,
      extension_elements=None, extension_attributes=None):
    GPhotosBaseEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated, text=text,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes)
                              

    ## NOTE: storing photo:id as self.gphoto_id, to avoid name clash with atom:id
    self.gphoto_id = gphoto_id
    self.albumid = albumid
    self.checksum = checksum
    self.client = client
    self.height = height
    self.position = position
    self.rotation = rotation
    self.size = size
    self.timestamp = timestamp
    self.version = version
    self.width = width
    self.commentingEnabled = commentingEnabled
    self.commentCount = commentCount
    ## NOTE: storing media:group as self.media, to create a self-explaining api
    self.media = media or Media.Group()
    self.exif = exif or Exif.Tags()
    self.geo = geo or Geo.Where()

  def GetPostLink(self):
    "Return the uri to this photo's `POST' link (use it for updates of the object)"

    return self.GetFeedLink()

  def GetCommentsUri(self):
    "Return the uri to this photo's feed of CommentEntry comments"
    return self._feedUri('comment')    

  def GetTagsUri(self):
    "Return the uri to this photo's feed of TagEntry tags"
    return self._feedUri('tag')    

  def GetAlbumUri(self):
    """Return the uri to the AlbumEntry containing this photo"""

    href = self.GetSelfLink().href
    return href[:href.find('/photoid')]

def PhotoEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(PhotoEntry, xml_string)

class PhotoFeed(GPhotosBaseFeed, PhotoData):
  """All metadata for a Google Photos Photo, including its sub-elements
  
  This feed represents a photo as the container for other objects.

  A Photo feed contains entries of
  CommentEntry or TagEntry,
  depending on the `kind' parameter in the original query.

  Take a look at PhotoData for metadata accessible as attributes to this object.
  
  """
  _children = GPhotosBaseFeed._children.copy()
  _children.update(PhotoData._children.copy())

  def GetTagsUri(self):
    "(string) Return the uri to the same feed, but of the TagEntry kind"
    
    return self._feedUri('tag')
  
  def GetCommentsUri(self):
    "(string) Return the uri to the same feed, but of the CommentEntry kind"
    
    return self._feedUri('comment')

def PhotoFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(PhotoFeed, xml_string)

class TagData(GPhotosBaseData):
  _children = {}
  _children['{%s}weight' % PHOTOS_NAMESPACE] = ('weight', Weight)
  weight=None

class TagEntry(GPhotosBaseEntry, TagData):
  """All metadata for a Google Photos Tag

  The actual tag is stored in the .title.text attribute

  """

  _kind = 'tag'
  _children = GPhotosBaseEntry._children.copy()
  _children.update(TagData._children.copy())

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None,
               # GPHOTO NAMESPACE:
               weight=None,
               extended_property=None,
               extension_elements=None, extension_attributes=None, text=None):
    GPhotosBaseEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated, text=text,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes)
    
    self.weight = weight

  def GetAlbumUri(self):
    """Return the uri to the AlbumEntry containing this tag"""

    href = self.GetSelfLink().href
    pos = href.find('/photoid')
    if pos == -1:
      return None
    return href[:pos]

  def GetPhotoUri(self):
    """Return the uri to the PhotoEntry containing this tag"""

    href = self.GetSelfLink().href
    pos = href.find('/tag')
    if pos == -1:
      return None
    return href[:pos]

def TagEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(TagEntry, xml_string)


class TagFeed(GPhotosBaseFeed, TagData):
  """All metadata for a Google Photos Tag, including its sub-elements"""
  
  _children = GPhotosBaseFeed._children.copy()
  _children.update(TagData._children.copy())
  
def TagFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(TagFeed, xml_string)

class CommentData(GPhotosBaseData):
  _children = {}
  ## NOTE: storing photo:id as self.gphoto_id, to avoid name clash with atom:id
  _children['{%s}id' % PHOTOS_NAMESPACE] = ('gphoto_id', Id)
  _children['{%s}albumid' % PHOTOS_NAMESPACE] = ('albumid', Albumid)
  _children['{%s}photoid' % PHOTOS_NAMESPACE] = ('photoid', Photoid)
  _children['{%s}author' % atom.ATOM_NAMESPACE] = ('author', [CommentAuthor,])
  gphoto_id=None
  albumid=None
  photoid=None
  author=None

class CommentEntry(GPhotosBaseEntry, CommentData):
  """All metadata for a Google Photos Comment
   
  The comment is stored in the .content.text attribute,
  with a content type in .content.type.


  """
  
  _kind = 'comment'
  _children = GPhotosBaseEntry._children.copy()
  _children.update(CommentData._children.copy())
  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None,
               # GPHOTO NAMESPACE:
               gphoto_id=None, albumid=None, photoid=None,
               extended_property=None,
               extension_elements=None, extension_attributes=None, text=None):
    
    GPhotosBaseEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
    
    self.gphoto_id = gphoto_id
    self.albumid = albumid
    self.photoid = photoid

  def GetCommentId(self):
    """Return the globally unique id of this comment"""
    return self.GetSelfLink().href.split('/')[-1]

  def GetAlbumUri(self):
    """Return the uri to the AlbumEntry containing this comment"""

    href = self.GetSelfLink().href
    return href[:href.find('/photoid')]

  def GetPhotoUri(self):
    """Return the uri to the PhotoEntry containing this comment"""

    href = self.GetSelfLink().href
    return href[:href.find('/commentid')]

def CommentEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentEntry, xml_string)

class CommentFeed(GPhotosBaseFeed, CommentData):
  """All metadata for a Google Photos Comment, including its sub-elements"""
  
  _children = GPhotosBaseFeed._children.copy()
  _children.update(CommentData._children.copy())

def CommentFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentFeed, xml_string)

class UserData(GPhotosBaseData):
  _children = {}
  _children['{%s}maxPhotosPerAlbum' % PHOTOS_NAMESPACE] = ('maxPhotosPerAlbum', MaxPhotosPerAlbum)
  _children['{%s}nickname' % PHOTOS_NAMESPACE] = ('nickname', Nickname)
  _children['{%s}quotalimit' % PHOTOS_NAMESPACE] = ('quotalimit', Quotalimit)
  _children['{%s}quotacurrent' % PHOTOS_NAMESPACE] = ('quotacurrent', Quotacurrent)
  _children['{%s}thumbnail' % PHOTOS_NAMESPACE] = ('thumbnail', Thumbnail)
  _children['{%s}user' % PHOTOS_NAMESPACE] = ('user', User)
  _children['{%s}id' % PHOTOS_NAMESPACE] = ('gphoto_id', Id)   

  maxPhotosPerAlbum=None
  nickname=None
  quotalimit=None
  quotacurrent=None
  thumbnail=None
  user=None
  gphoto_id=None
  

class UserEntry(GPhotosBaseEntry, UserData):
  """All metadata for a Google Photos User

  This entry represents an album owner and all appropriate metadata.

  Take a look at at the attributes of the UserData for metadata available.
  """
  _children = GPhotosBaseEntry._children.copy()
  _children.update(UserData._children.copy())
  _kind = 'user'
  
  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None,
               title=None, updated=None,
               # GPHOTO NAMESPACE:
               gphoto_id=None, maxPhotosPerAlbum=None, nickname=None, quotalimit=None,
               quotacurrent=None, thumbnail=None, user=None,
               extended_property=None,
               extension_elements=None, extension_attributes=None, text=None):
    
    GPhotosBaseEntry.__init__(self, author=author, category=category,
                              content=content,
                              atom_id=atom_id, link=link, published=published,
                              title=title, updated=updated,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)
                              
    
    self.gphoto_id=gphoto_id
    self.maxPhotosPerAlbum=maxPhotosPerAlbum
    self.nickname=nickname
    self.quotalimit=quotalimit
    self.quotacurrent=quotacurrent
    self.thumbnail=thumbnail
    self.user=user

  def GetAlbumsUri(self):
    "(string) Return the uri to this user's feed of the AlbumEntry kind"
    return self._feedUri('album')
  
  def GetPhotosUri(self):
    "(string) Return the uri to this user's feed of the PhotoEntry kind"
    return self._feedUri('photo')
  
  def GetCommentsUri(self):
    "(string) Return the uri to this user's feed of the CommentEntry kind"
    return self._feedUri('comment')
  
  def GetTagsUri(self):
    "(string) Return the uri to this user's feed of the TagEntry kind"
    return self._feedUri('tag')

def UserEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(UserEntry, xml_string)
    
class UserFeed(GPhotosBaseFeed, UserData):
  """Feed for a User in the google photos api.

  This feed represents a user as the container for other objects.

  A User feed contains entries of
  AlbumEntry, PhotoEntry, CommentEntry, UserEntry or TagEntry,
  depending on the `kind' parameter in the original query.

  The user feed itself also contains all of the metadata available
  as part of a UserData object."""
  _children = GPhotosBaseFeed._children.copy()
  _children.update(UserData._children.copy())

  def GetAlbumsUri(self):
    """Get the uri to this feed, but with entries of the AlbumEntry kind."""
    return self._feedUri('album')

  def GetTagsUri(self):
    """Get the uri to this feed, but with entries of the TagEntry kind."""
    return self._feedUri('tag')

  def GetPhotosUri(self):
    """Get the uri to this feed, but with entries of the PhotosEntry kind."""
    return self._feedUri('photo')

  def GetCommentsUri(self):
    """Get the uri to this feed, but with entries of the CommentsEntry kind."""
    return self._feedUri('comment')

def UserFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(UserFeed, xml_string)
  

  
def AnyFeedFromString(xml_string):
  """Creates an instance of the appropriate feed class from the
    xml string contents.

  Args:
    xml_string: str A string which contains valid XML. The root element
        of the XML string should match the tag and namespace of the desired
        class.

  Returns:
    An instance of the target class with members assigned according to the
    contents of the XML - or a basic gdata.GDataFeed instance if it is
    impossible to determine the appropriate class (look for extra elements
    in GDataFeed's .FindExtensions() and extension_elements[] ).
  """
  tree = ElementTree.fromstring(xml_string)
  category = tree.find('{%s}category' % atom.ATOM_NAMESPACE)
  if category is None:
    # TODO: is this the best way to handle this?
    return atom._CreateClassFromElementTree(GPhotosBaseFeed, tree)
  namespace, kind = category.get('term').split('#')
  if namespace != PHOTOS_NAMESPACE:
    # TODO: is this the best way to handle this?
    return atom._CreateClassFromElementTree(GPhotosBaseFeed, tree)
  ## TODO: is getattr safe this way?
  feed_class = getattr(gdata.photos, '%sFeed' % kind.title())
  return atom._CreateClassFromElementTree(feed_class, tree)

def AnyEntryFromString(xml_string):
  """Creates an instance of the appropriate entry class from the
    xml string contents.

  Args:
    xml_string: str A string which contains valid XML. The root element
        of the XML string should match the tag and namespace of the desired
        class.

  Returns:
    An instance of the target class with members assigned according to the
    contents of the XML - or a basic gdata.GDataEndry instance if it is
    impossible to determine the appropriate class (look for extra elements
    in GDataEntry's .FindExtensions() and extension_elements[] ).
  """
  tree = ElementTree.fromstring(xml_string)
  category = tree.find('{%s}category' % atom.ATOM_NAMESPACE)
  if category is None:
    # TODO: is this the best way to handle this?
    return atom._CreateClassFromElementTree(GPhotosBaseEntry, tree)
  namespace, kind = category.get('term').split('#')
  if namespace != PHOTOS_NAMESPACE:
    # TODO: is this the best way to handle this?
    return atom._CreateClassFromElementTree(GPhotosBaseEntry, tree)
  ## TODO: is getattr safe this way?
  feed_class = getattr(gdata.photos, '%sEntry' % kind.title())
  return atom._CreateClassFromElementTree(feed_class, tree)

