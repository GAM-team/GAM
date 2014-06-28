#!/usr/bin/env python
# -*-*- encoding: utf-8 -*-*-
#
# This is the service file for the Google Photo python client.
# It is used for higher level operations.
#
# $Id: service.py 144 2007-10-25 21:03:34Z havard.gulldahl $
#
# Copyright 2007 Håvard Gulldahl 
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

"""Google PhotoService provides a human-friendly interface to
Google Photo (a.k.a Picasa Web) services[1].

It extends gdata.service.GDataService and as such hides all the
nasty details about authenticating, parsing and communicating with
Google Photos. 

[1]: http://code.google.com/apis/picasaweb/gdata.html

Example:
  import gdata.photos, gdata.photos.service
  pws = gdata.photos.service.PhotosService()
  pws.ClientLogin(username, password)
  #Get all albums
  albums = pws.GetUserFeed().entry
  # Get all photos in second album
  photos = pws.GetFeed(albums[1].GetPhotosUri()).entry
  # Get all tags for photos in second album and print them
  tags = pws.GetFeed(albums[1].GetTagsUri()).entry
  print [ tag.summary.text for tag in tags ]
  # Get all comments for the first photos in list and print them
  comments = pws.GetCommentFeed(photos[0].GetCommentsUri()).entry
  print [ c.summary.text for c in comments ]

  # Get a photo to work with
  photo = photos[0]
  # Update metadata

  # Attributes from the <gphoto:*> namespace
  photo.summary.text = u'A nice view from my veranda'
  photo.title.text = u'Verandaview.jpg'

  # Attributes from the <media:*> namespace
  photo.media.keywords.text = u'Home, Long-exposure, Sunset' # Comma-separated

  # Adding attributes to media object

  # Rotate 90 degrees clockwise
  photo.rotation = gdata.photos.Rotation(text='90') 

  # Submit modified photo object
  photo = pws.UpdatePhotoMetadata(photo)
  
  # Make sure you only modify the newly returned object, else you'll get
  # versioning errors. See Optimistic-concurrency

  # Add comment to a picture
  comment = pws.InsertComment(photo, u'I wish the water always was this warm')

  # Remove comment because it was silly
  print "*blush*"
  pws.Delete(comment.GetEditLink().href)

"""

__author__ = u'havard@gulldahl.no'# (Håvard Gulldahl)' #BUG: pydoc chokes on non-ascii chars in __author__
__license__ = 'Apache License v2'
__version__ = '$Revision: 176 $'[11:-2] 


import sys, os.path, StringIO
import time
import gdata.service
import gdata
import atom.service
import atom
import gdata.photos

SUPPORTED_UPLOAD_TYPES = ('bmp', 'jpeg', 'jpg', 'gif', 'png')

UNKOWN_ERROR=1000
GPHOTOS_BAD_REQUEST=400
GPHOTOS_CONFLICT=409
GPHOTOS_INTERNAL_SERVER_ERROR=500
GPHOTOS_INVALID_ARGUMENT=601
GPHOTOS_INVALID_CONTENT_TYPE=602
GPHOTOS_NOT_AN_IMAGE=603
GPHOTOS_INVALID_KIND=604

class GooglePhotosException(Exception):
  def __init__(self, response):

    self.error_code = response['status']
    self.reason = response['reason'].strip()
    if '<html>' in str(response['body']): #general html message, discard it
      response['body'] = ""
    self.body = response['body'].strip()
    self.message = "(%(status)s) %(body)s -- %(reason)s" % response

    #return explicit error codes
    error_map = { '(12) Not an image':GPHOTOS_NOT_AN_IMAGE,
                  'kind: That is not one of the acceptable values':
                      GPHOTOS_INVALID_KIND,
                  
                }
    for msg, code in error_map.iteritems():
      if self.body == msg:
        self.error_code = code
        break
    self.args = [self.error_code, self.reason, self.body]

class PhotosService(gdata.service.GDataService):
  ssl = True
  userUri = '/data/feed/api/user/%s'
  
  def __init__(self, email=None, password=None, source=None,
               server='picasaweb.google.com', additional_headers=None,
               **kwargs):
    """Creates a client for the Google Photos service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'picasaweb.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    self.email = email
    self.client = source
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='lh2', source=source,
        server=server, additional_headers=additional_headers, **kwargs)

  def GetFeed(self, uri, limit=None, start_index=None):
    """Get a feed.

     The results are ordered by the values of their `updated' elements,
     with the most recently updated entry appearing first in the feed.
    
    Arguments:
    uri: the uri to fetch
    limit (optional): the maximum number of entries to return. Defaults to what
      the server returns.
     
    Returns:
    one of gdata.photos.AlbumFeed,
           gdata.photos.UserFeed,
           gdata.photos.PhotoFeed,
           gdata.photos.CommentFeed,
           gdata.photos.TagFeed,
      depending on the results of the query.
    Raises:
    GooglePhotosException

    See:
    http://code.google.com/apis/picasaweb/gdata.html#Get_Album_Feed_Manual
    """
    if limit is not None:
      uri += '&max-results=%s' % limit
    if start_index is not None:
      uri += '&start-index=%s' % start_index
    try:
      return self.Get(uri, converter=gdata.photos.AnyFeedFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

  def GetEntry(self, uri, limit=None, start_index=None):
    """Get an Entry.

    Arguments:
    uri: the uri to the entry
    limit (optional): the maximum number of entries to return. Defaults to what
      the server returns.
     
    Returns:
    one of gdata.photos.AlbumEntry,
           gdata.photos.UserEntry,
           gdata.photos.PhotoEntry,
           gdata.photos.CommentEntry,
           gdata.photos.TagEntry,
      depending on the results of the query.
    Raises:
    GooglePhotosException
    """
    if limit is not None:
      uri += '&max-results=%s' % limit
    if start_index is not None:
      uri += '&start-index=%s' % start_index
    try:
      return self.Get(uri, converter=gdata.photos.AnyEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])
      
  def GetUserFeed(self, kind='album', user='default', limit=None):
    """Get user-based feed, containing albums, photos, comments or tags;
      defaults to albums.

    The entries are ordered by the values of their `updated' elements,
    with the most recently updated entry appearing first in the feed.
    
    Arguments:
    kind: the kind of entries to get, either `album', `photo',
      `comment' or `tag', or a python list of these. Defaults to `album'.
    user (optional): whose albums we're querying. Defaults to current user.
    limit (optional): the maximum number of entries to return.
      Defaults to everything the server returns.

     
    Returns:
    gdata.photos.UserFeed, containing appropriate Entry elements

    See:
    http://code.google.com/apis/picasaweb/gdata.html#Get_Album_Feed_Manual
    http://googledataapis.blogspot.com/2007/07/picasa-web-albums-adds-new-api-features.html
    """
    if isinstance(kind, (list, tuple) ):
      kind = ",".join(kind)
    
    uri = '/data/feed/api/user/%s?kind=%s' % (user, kind)
    return self.GetFeed(uri, limit=limit)
  
  def GetTaggedPhotos(self, tag, user='default', limit=None):
    """Get all photos belonging to a specific user, tagged by the given keyword

    Arguments:
    tag: The tag you're looking for, e.g. `dog'
    user (optional): Whose images/videos you want to search, defaults
      to current user
    limit (optional): the maximum number of entries to return.
      Defaults to everything the server returns.

    Returns:
    gdata.photos.UserFeed containing PhotoEntry elements
    """
    # Lower-casing because of
    #   http://code.google.com/p/gdata-issues/issues/detail?id=194
    uri = '/data/feed/api/user/%s?kind=photo&tag=%s' % (user, tag.lower())
    return self.GetFeed(uri, limit)

  def SearchUserPhotos(self, query, user='default', limit=100):
    """Search through all photos for a specific user and return a feed.
    This will look for matches in file names and image tags (a.k.a. keywords)

    Arguments:
    query: The string you're looking for, e.g. `vacation'
    user (optional): The username of whose photos you want to search, defaults
      to current user.
    limit (optional): Don't return more than `limit' hits, defaults to 100

    Only public photos are searched, unless you are authenticated and
    searching through your own photos.

    Returns:
    gdata.photos.UserFeed with PhotoEntry elements
    """
    uri = '/data/feed/api/user/%s?kind=photo&q=%s' % (user, query)
    return self.GetFeed(uri, limit=limit)

  def SearchCommunityPhotos(self, query, limit=100):
    """Search through all public photos and return a feed.
    This will look for matches in file names and image tags (a.k.a. keywords)

    Arguments:
    query: The string you're looking for, e.g. `vacation'
    limit (optional): Don't return more than `limit' hits, defaults to 100

    Returns:
    gdata.GDataFeed with PhotoEntry elements
    """
    uri='/data/feed/api/all?q=%s' % query
    return self.GetFeed(uri, limit=limit)

  def GetContacts(self, user='default', limit=None):
    """Retrieve a feed that contains a list of your contacts

    Arguments:
    user: Username of the user whose contacts you want

    Returns
    gdata.photos.UserFeed, with UserEntry entries

    See:
    http://groups.google.com/group/Google-Picasa-Data-API/msg/819b0025b5ff5e38
    """
    uri = '/data/feed/api/user/%s/contacts?kind=user' % user
    return self.GetFeed(uri, limit=limit)

  def SearchContactsPhotos(self, user='default', search=None, limit=None):
    """Search over your contacts' photos and return a feed

    Arguments:
    user: Username of the user whose contacts you want
    search (optional): What to search for (photo title, description and keywords)

    Returns
    gdata.photos.UserFeed, with PhotoEntry elements

    See:
    http://groups.google.com/group/Google-Picasa-Data-API/msg/819b0025b5ff5e38
    """

    uri = '/data/feed/api/user/%s/contacts?kind=photo&q=%s' % (user, search)
    return self.GetFeed(uri, limit=limit)

  def InsertAlbum(self, title, summary, location=None, access='public',
    commenting_enabled='true', timestamp=None):
    """Add an album.

    Needs authentication, see self.ClientLogin()

    Arguments:
    title: Album title 
    summary: Album summary / description
    access (optional): `private' or `public'. Public albums are searchable
      by everyone on the internet. Defaults to `public'
    commenting_enabled (optional): `true' or `false'. Defaults to `true'.
    timestamp (optional): A date and time for the album, in milliseconds since
      Unix epoch[1] UTC. Defaults to now.

    Returns:
    The newly created gdata.photos.AlbumEntry

    See:
    http://code.google.com/apis/picasaweb/gdata.html#Add_Album_Manual_Installed

    [1]: http://en.wikipedia.org/wiki/Unix_epoch
    """
    album = gdata.photos.AlbumEntry()
    album.title = atom.Title(text=title, title_type='text')
    album.summary = atom.Summary(text=summary, summary_type='text')
    if location is not None:
      album.location = gdata.photos.Location(text=location)
    album.access = gdata.photos.Access(text=access)
    if commenting_enabled in ('true', 'false'):
      album.commentingEnabled = gdata.photos.CommentingEnabled(text=commenting_enabled)
    if timestamp is None:
      timestamp = '%i' % int(time.time() * 1000)
    album.timestamp = gdata.photos.Timestamp(text=timestamp)
    try:
      return self.Post(album, uri=self.userUri % self.email,
      converter=gdata.photos.AlbumEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

  def InsertPhoto(self, album_or_uri, photo, filename_or_handle,
    content_type='image/jpeg'):
    """Add a PhotoEntry

    Needs authentication, see self.ClientLogin()

    Arguments:
    album_or_uri: AlbumFeed or uri of the album where the photo should go
    photo: PhotoEntry to add
    filename_or_handle: A file-like object or file name where the image/video
      will be read from
    content_type (optional): Internet media type (a.k.a. mime type) of
      media object. Currently Google Photos supports these types:
       o image/bmp
       o image/gif
       o image/jpeg
       o image/png
       
      Images will be converted to jpeg on upload. Defaults to `image/jpeg'

    """

    try:
      assert(isinstance(photo, gdata.photos.PhotoEntry))
    except AssertionError:
      raise GooglePhotosException({'status':GPHOTOS_INVALID_ARGUMENT,
        'body':'`photo` must be a gdata.photos.PhotoEntry instance',
        'reason':'Found %s, not PhotoEntry' % type(photo)
        })
    try:
      majtype, mintype = content_type.split('/')
      assert(mintype in SUPPORTED_UPLOAD_TYPES)
    except (ValueError, AssertionError):
      raise GooglePhotosException({'status':GPHOTOS_INVALID_CONTENT_TYPE,
        'body':'This is not a valid content type: %s' % content_type,
        'reason':'Accepted content types: %s' % \
          ['image/'+t for t in SUPPORTED_UPLOAD_TYPES]
        })
    if isinstance(filename_or_handle, (str, unicode)) and \
      os.path.exists(filename_or_handle): # it's a file name
      mediasource = gdata.MediaSource()
      mediasource.setFile(filename_or_handle, content_type)
    elif hasattr(filename_or_handle, 'read'):# it's a file-like resource
      if hasattr(filename_or_handle, 'seek'):
        filename_or_handle.seek(0) # rewind pointer to the start of the file
      # gdata.MediaSource needs the content length, so read the whole image 
      file_handle = StringIO.StringIO(filename_or_handle.read()) 
      name = 'image'
      if hasattr(filename_or_handle, 'name'):
        name = filename_or_handle.name
      mediasource = gdata.MediaSource(file_handle, content_type,
        content_length=file_handle.len, file_name=name)
    else: #filename_or_handle is not valid
      raise GooglePhotosException({'status':GPHOTOS_INVALID_ARGUMENT,
        'body':'`filename_or_handle` must be a path name or a file-like object',
        'reason':'Found %s, not path name or object with a .read() method' % \
          filename_or_handle
        })
    
    if isinstance(album_or_uri, (str, unicode)): # it's a uri
      feed_uri = album_or_uri
    elif hasattr(album_or_uri, 'GetFeedLink'): # it's a AlbumFeed object
      feed_uri = album_or_uri.GetFeedLink().href
  
    try:
      return self.Post(photo, uri=feed_uri, media_source=mediasource,
        converter=gdata.photos.PhotoEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])
  
  def InsertPhotoSimple(self, album_or_uri, title, summary, filename_or_handle,
      content_type='image/jpeg', keywords=None):
    """Add a photo without constructing a PhotoEntry.

    Needs authentication, see self.ClientLogin()

    Arguments:
    album_or_uri: AlbumFeed or uri of the album where the photo should go
    title: Photo title
    summary: Photo summary / description
    filename_or_handle: A file-like object or file name where the image/video
      will be read from
    content_type (optional): Internet media type (a.k.a. mime type) of
      media object. Currently Google Photos supports these types:
       o image/bmp
       o image/gif
       o image/jpeg
       o image/png
       
      Images will be converted to jpeg on upload. Defaults to `image/jpeg'
    keywords (optional): a 1) comma separated string or 2) a python list() of
      keywords (a.k.a. tags) to add to the image.
      E.g. 1) `dog, vacation, happy' 2) ['dog', 'happy', 'vacation']
    
    Returns:
    The newly created gdata.photos.PhotoEntry or GooglePhotosException on errors

    See:
    http://code.google.com/apis/picasaweb/gdata.html#Add_Album_Manual_Installed
    [1]: http://en.wikipedia.org/wiki/Unix_epoch
    """
    
    metadata = gdata.photos.PhotoEntry()
    metadata.title=atom.Title(text=title)
    metadata.summary = atom.Summary(text=summary, summary_type='text')
    if keywords is not None:
      if isinstance(keywords, list):
        keywords = ','.join(keywords)
      metadata.media.keywords = gdata.media.Keywords(text=keywords)
    return self.InsertPhoto(album_or_uri, metadata, filename_or_handle,
      content_type)

  def UpdatePhotoMetadata(self, photo):
    """Update a photo's metadata. 

     Needs authentication, see self.ClientLogin()

     You can update any or all of the following metadata properties:
      * <title>
      * <media:description>
      * <gphoto:checksum>
      * <gphoto:client>
      * <gphoto:rotation>
      * <gphoto:timestamp>
      * <gphoto:commentingEnabled>

      Arguments:
      photo: a gdata.photos.PhotoEntry object with updated elements

      Returns:
      The modified gdata.photos.PhotoEntry

      Example:
      p = GetFeed(uri).entry[0]
      p.title.text = u'My new text'
      p.commentingEnabled.text = 'false'
      p = UpdatePhotoMetadata(p)

      It is important that you don't keep the old object around, once
      it has been updated. See
      http://code.google.com/apis/gdata/reference.html#Optimistic-concurrency
      """
    try:
      return self.Put(data=photo, uri=photo.GetEditLink().href,
      converter=gdata.photos.PhotoEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

  
  def UpdatePhotoBlob(self, photo_or_uri, filename_or_handle,
                      content_type = 'image/jpeg'):
    """Update a photo's binary data.

    Needs authentication, see self.ClientLogin()

    Arguments:
    photo_or_uri: a gdata.photos.PhotoEntry that will be updated, or a
      `edit-media' uri pointing to it
    filename_or_handle:  A file-like object or file name where the image/video
      will be read from
    content_type (optional): Internet media type (a.k.a. mime type) of
      media object. Currently Google Photos supports these types:
       o image/bmp
       o image/gif
       o image/jpeg
       o image/png
    Images will be converted to jpeg on upload. Defaults to `image/jpeg'

    Returns:
    The modified gdata.photos.PhotoEntry

    Example:
    p = GetFeed(PhotoUri)
    p = UpdatePhotoBlob(p, '/tmp/newPic.jpg')

    It is important that you don't keep the old object around, once
    it has been updated. See
    http://code.google.com/apis/gdata/reference.html#Optimistic-concurrency
    """

    try:  
      majtype, mintype = content_type.split('/')
      assert(mintype in SUPPORTED_UPLOAD_TYPES)
    except (ValueError, AssertionError):
      raise GooglePhotosException({'status':GPHOTOS_INVALID_CONTENT_TYPE,
        'body':'This is not a valid content type: %s' % content_type,
        'reason':'Accepted content types: %s' % \
          ['image/'+t for t in SUPPORTED_UPLOAD_TYPES]
        })
    
    if isinstance(filename_or_handle, (str, unicode)) and \
      os.path.exists(filename_or_handle): # it's a file name
      photoblob = gdata.MediaSource()
      photoblob.setFile(filename_or_handle, content_type)
    elif hasattr(filename_or_handle, 'read'):# it's a file-like resource
      if hasattr(filename_or_handle, 'seek'):
        filename_or_handle.seek(0) # rewind pointer to the start of the file
      # gdata.MediaSource needs the content length, so read the whole image 
      file_handle = StringIO.StringIO(filename_or_handle.read()) 
      name = 'image'
      if hasattr(filename_or_handle, 'name'):
        name = filename_or_handle.name
      mediasource = gdata.MediaSource(file_handle, content_type,
        content_length=file_handle.len, file_name=name)
    else: #filename_or_handle is not valid
      raise GooglePhotosException({'status':GPHOTOS_INVALID_ARGUMENT,
        'body':'`filename_or_handle` must be a path name or a file-like object',
        'reason':'Found %s, not path name or an object with .read() method' % \
          type(filename_or_handle)
        })
    
    if isinstance(photo_or_uri, (str, unicode)):
      entry_uri = photo_or_uri # it's a uri
    elif hasattr(photo_or_uri, 'GetEditMediaLink'):
      entry_uri = photo_or_uri.GetEditMediaLink().href
    try:
      return self.Put(photoblob, entry_uri,
          converter=gdata.photos.PhotoEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

  def InsertTag(self, photo_or_uri, tag):
    """Add a tag (a.k.a. keyword) to a photo.

    Needs authentication, see self.ClientLogin()

    Arguments:
    photo_or_uri: a gdata.photos.PhotoEntry that will be tagged, or a
      `post' uri pointing to it
    (string) tag: The tag/keyword

    Returns:
    The new gdata.photos.TagEntry

    Example:
    p = GetFeed(PhotoUri)
    tag = InsertTag(p, 'Beautiful sunsets')

    """
    tag = gdata.photos.TagEntry(title=atom.Title(text=tag))
    if isinstance(photo_or_uri, (str, unicode)):
      post_uri = photo_or_uri # it's a uri
    elif hasattr(photo_or_uri, 'GetEditMediaLink'):
      post_uri = photo_or_uri.GetPostLink().href
    try:
      return self.Post(data=tag, uri=post_uri,
      converter=gdata.photos.TagEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

                  
  def InsertComment(self, photo_or_uri, comment):
    """Add a comment to a photo.

    Needs authentication, see self.ClientLogin()

    Arguments:
    photo_or_uri: a gdata.photos.PhotoEntry that is about to be commented
      , or a `post' uri pointing to it
    (string) comment: The actual comment

    Returns:
    The new gdata.photos.CommentEntry

    Example:
    p = GetFeed(PhotoUri)
    tag = InsertComment(p, 'OOOH! I would have loved to be there.
      Who's that in the back?')

    """
    comment = gdata.photos.CommentEntry(content=atom.Content(text=comment))
    if isinstance(photo_or_uri, (str, unicode)):
      post_uri = photo_or_uri # it's a uri
    elif hasattr(photo_or_uri, 'GetEditMediaLink'):
      post_uri = photo_or_uri.GetPostLink().href
    try:
      return self.Post(data=comment, uri=post_uri,
        converter=gdata.photos.CommentEntryFromString)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

  def Delete(self, object_or_uri, *args, **kwargs):
    """Delete an object.

    Re-implementing the GDataService.Delete method, to add some
    convenience.

    Arguments:
    object_or_uri: Any object that has a GetEditLink() method that
      returns a link, or a uri to that object.

    Returns:
    ? or GooglePhotosException on errors
    """
    try:
      uri = object_or_uri.GetEditLink().href
    except AttributeError:
      uri = object_or_uri
    try:
      return gdata.service.GDataService.Delete(self, uri, *args, **kwargs)
    except gdata.service.RequestError, e:
      raise GooglePhotosException(e.args[0])

def GetSmallestThumbnail(media_thumbnail_list):
  """Helper function to get the smallest thumbnail of a list of
    gdata.media.Thumbnail.
  Returns gdata.media.Thumbnail """
  r = {}
  for thumb in media_thumbnail_list:
      r[int(thumb.width)*int(thumb.height)] = thumb
  keys = r.keys()
  keys.sort()
  return r[keys[0]]

def ConvertAtomTimestampToEpoch(timestamp):
  """Helper function to convert a timestamp string, for instance
    from atom:updated or atom:published, to milliseconds since Unix epoch
    (a.k.a. POSIX time).

    `2007-07-22T00:45:10.000Z' -> """
  return time.mktime(time.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.000Z'))
  ## TODO: Timezone aware
