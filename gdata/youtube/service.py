#!/usr/bin/python
#
# Copyright (C) 2008 Google Inc.
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

"""YouTubeService extends GDataService to streamline YouTube operations.

  YouTubeService: Provides methods to perform CRUD operations on YouTube feeds.
  Extends GDataService.
"""

__author__ = ('api.stephaniel@gmail.com (Stephanie Liu), '
              'api.jhartmann@gmail.com (Jochen Hartmann)')

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
import os
import atom
import gdata
import gdata.service
import gdata.youtube

YOUTUBE_SERVER = 'gdata.youtube.com'
YOUTUBE_SERVICE = 'youtube'
YOUTUBE_CLIENTLOGIN_AUTHENTICATION_URL = 'https://www.google.com/youtube/accounts/ClientLogin'
YOUTUBE_SUPPORTED_UPLOAD_TYPES = ('mov', 'avi', 'wmv', 'mpg', 'quicktime',
                                  'flv', 'mp4', 'x-flv')
YOUTUBE_QUERY_VALID_TIME_PARAMETERS = ('today', 'this_week', 'this_month',
                                       'all_time')
YOUTUBE_QUERY_VALID_ORDERBY_PARAMETERS = ('published', 'viewCount', 'rating',
                                          'relevance')
YOUTUBE_QUERY_VALID_RACY_PARAMETERS = ('include', 'exclude')
YOUTUBE_QUERY_VALID_FORMAT_PARAMETERS = ('1', '5', '6')
YOUTUBE_STANDARDFEEDS = ('most_recent', 'recently_featured',
                         'top_rated', 'most_viewed','watch_on_mobile')
YOUTUBE_UPLOAD_URI = 'http://uploads.gdata.youtube.com/feeds/api/users'
YOUTUBE_UPLOAD_TOKEN_URI = 'http://gdata.youtube.com/action/GetUploadToken'
YOUTUBE_VIDEO_URI = 'http://gdata.youtube.com/feeds/api/videos'
YOUTUBE_USER_FEED_URI = 'http://gdata.youtube.com/feeds/api/users'
YOUTUBE_PLAYLIST_FEED_URI = 'http://gdata.youtube.com/feeds/api/playlists'

YOUTUBE_STANDARD_FEEDS = 'http://gdata.youtube.com/feeds/api/standardfeeds'
YOUTUBE_STANDARD_TOP_RATED_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS, 'top_rated')
YOUTUBE_STANDARD_MOST_VIEWED_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'most_viewed')
YOUTUBE_STANDARD_RECENTLY_FEATURED_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'recently_featured')
YOUTUBE_STANDARD_WATCH_ON_MOBILE_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'watch_on_mobile')
YOUTUBE_STANDARD_TOP_FAVORITES_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'top_favorites')
YOUTUBE_STANDARD_MOST_RECENT_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'most_recent')
YOUTUBE_STANDARD_MOST_DISCUSSED_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'most_discussed')
YOUTUBE_STANDARD_MOST_LINKED_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'most_linked')
YOUTUBE_STANDARD_MOST_RESPONDED_URI = '%s/%s' % (YOUTUBE_STANDARD_FEEDS,
    'most_responded')
YOUTUBE_SCHEMA = 'http://gdata.youtube.com/schemas'

YOUTUBE_RATING_LINK_REL = '%s#video.ratings' % YOUTUBE_SCHEMA

YOUTUBE_COMPLAINT_CATEGORY_SCHEME = '%s/%s' % (YOUTUBE_SCHEMA,
                                               'complaint-reasons.cat')
YOUTUBE_SUBSCRIPTION_CATEGORY_SCHEME = '%s/%s' % (YOUTUBE_SCHEMA,
                                                  'subscriptiontypes.cat')

YOUTUBE_COMPLAINT_CATEGORY_TERMS = ('PORN', 'VIOLENCE', 'HATE', 'DANGEROUS',
                                    'RIGHTS', 'SPAM')
YOUTUBE_CONTACT_STATUS = ('accepted', 'rejected')
YOUTUBE_CONTACT_CATEGORY = ('Friends', 'Family')

UNKOWN_ERROR = 1000
YOUTUBE_BAD_REQUEST = 400
YOUTUBE_CONFLICT = 409
YOUTUBE_INTERNAL_SERVER_ERROR = 500
YOUTUBE_INVALID_ARGUMENT = 601
YOUTUBE_INVALID_CONTENT_TYPE = 602
YOUTUBE_NOT_A_VIDEO = 603
YOUTUBE_INVALID_KIND = 604


class Error(Exception):
  """Base class for errors within the YouTube service."""
  pass

class RequestError(Error):
  """Error class that is thrown in response to an invalid HTTP Request."""
  pass

class YouTubeError(Error):
  """YouTube service specific error class."""
  pass

class YouTubeService(gdata.service.GDataService):

  """Client for the YouTube service.

  Performs all documented Google Data YouTube API functions, such as inserting,
  updating and deleting videos, comments, playlist, subscriptions etc.
  YouTube Service requires authentication for any write, update or delete
  actions.

  Attributes:
    email: An optional string identifying the user. Required only for
        authenticated actions.
    password: An optional string identifying the user's password.
    source: An optional string identifying the name of your application.
    server: An optional address of the YouTube API server. gdata.youtube.com 
        is provided as the default value.
    additional_headers: An optional dictionary containing additional headers
        to be passed along with each request. Use to store developer key.
    client_id: An optional string identifying your application, required for   
        authenticated requests, along with a developer key.
    developer_key: An optional string value. Register your application at
        http://code.google.com/apis/youtube/dashboard to obtain a (free) key.
  """

  def __init__(self, email=None, password=None, source=None,
               server=YOUTUBE_SERVER, additional_headers=None, client_id=None,
               developer_key=None, **kwargs):
    """Creates a client for the YouTube service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'gdata.youtube.com'.
      client_id: string (optional) Identifies your application, required for
          authenticated requests, along with a developer key.
      developer_key: string (optional) Register your application at
          http://code.google.com/apis/youtube/dashboard to obtain a (free) key.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """

    gdata.service.GDataService.__init__(
        self, email=email, password=password, service=YOUTUBE_SERVICE,
        source=source, server=server, additional_headers=additional_headers,
        **kwargs)

    if client_id is not None:
      self.additional_headers['X-Gdata-Client'] = client_id

    if developer_key is not None:
      self.additional_headers['X-GData-Key'] = 'key=%s' % developer_key

    self.auth_service_url = YOUTUBE_CLIENTLOGIN_AUTHENTICATION_URL

  def GetYouTubeVideoFeed(self, uri):
    """Retrieve a YouTubeVideoFeed.

    Args:
      uri: A string representing the URI of the feed that is to be retrieved.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.Get(uri, converter=gdata.youtube.YouTubeVideoFeedFromString)

  def GetYouTubeVideoEntry(self, uri=None, video_id=None):
    """Retrieve a YouTubeVideoEntry.

    Either a uri or a video_id must be provided.

    Args:
      uri: An optional string representing the URI of the entry that is to 
          be retrieved.
      video_id: An optional string representing the ID of the video.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a video_id to the
          GetYouTubeVideoEntry() method.
    """
    if uri is None and video_id is None:
      raise YouTubeError('You must provide at least a uri or a video_id '
                         'to the GetYouTubeVideoEntry() method')
    elif video_id and not uri:
      uri = '%s/%s' % (YOUTUBE_VIDEO_URI, video_id)
    return self.Get(uri, converter=gdata.youtube.YouTubeVideoEntryFromString)

  def GetYouTubeContactFeed(self, uri=None, username='default'):
    """Retrieve a YouTubeContactFeed.

    Either a uri or a username must be provided.

    Args:
      uri: An optional string representing the URI of the contact feed that
          is to be retrieved.
      username: An optional string representing the username. Defaults to the
          currently authenticated user.

    Returns:
      A YouTubeContactFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a username to the
          GetYouTubeContactFeed() method.
    """
    if uri is None:
      uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'contacts')
    return self.Get(uri, converter=gdata.youtube.YouTubeContactFeedFromString)

  def GetYouTubeContactEntry(self, uri):
    """Retrieve a YouTubeContactEntry.

    Args:
      uri: A string representing the URI of the contact entry that is to
          be retrieved.

    Returns:
      A YouTubeContactEntry if successfully retrieved.
    """
    return self.Get(uri, converter=gdata.youtube.YouTubeContactEntryFromString)

  def GetYouTubeVideoCommentFeed(self, uri=None, video_id=None):
    """Retrieve a YouTubeVideoCommentFeed.

    Either a uri or a video_id must be provided.

    Args:
      uri: An optional string representing the URI of the comment feed that
          is to be retrieved.
      video_id: An optional string representing the ID of the video for which
          to retrieve the comment feed.

    Returns:
      A YouTubeVideoCommentFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a video_id to the
          GetYouTubeVideoCommentFeed() method.
    """
    if uri is None and video_id is None:
      raise YouTubeError('You must provide at least a uri or a video_id '
                         'to the GetYouTubeVideoCommentFeed() method')
    elif video_id and not uri:
      uri = '%s/%s/%s' % (YOUTUBE_VIDEO_URI, video_id, 'comments')
    return self.Get(
        uri, converter=gdata.youtube.YouTubeVideoCommentFeedFromString)

  def GetYouTubeVideoCommentEntry(self, uri):
    """Retrieve a YouTubeVideoCommentEntry.

    Args:
      uri: A string representing the URI of the comment entry that is to
          be retrieved.

    Returns:
      A YouTubeCommentEntry if successfully retrieved.
    """
    return self.Get(
        uri, converter=gdata.youtube.YouTubeVideoCommentEntryFromString)

  def GetYouTubeUserFeed(self, uri=None, username=None):
    """Retrieve a YouTubeVideoFeed of user uploaded videos

    Either a uri or a username must be provided.  This will retrieve list
    of videos uploaded by specified user.  The uri will be of format
    "http://gdata.youtube.com/feeds/api/users/{username}/uploads".

    Args:
      uri: An optional string representing the URI of the user feed that is
          to be retrieved.
      username: An optional string representing the username.

    Returns:
      A YouTubeUserFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a username to the
          GetYouTubeUserFeed() method.
    """
    if uri is None and username is None:
      raise YouTubeError('You must provide at least a uri or a username '
                         'to the GetYouTubeUserFeed() method')
    elif username and not uri:
      uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'uploads')
    return self.Get(uri, converter=gdata.youtube.YouTubeUserFeedFromString)

  def GetYouTubeUserEntry(self, uri=None, username=None):
    """Retrieve a YouTubeUserEntry.

    Either a uri or a username must be provided.

    Args:
      uri: An optional string representing the URI of the user entry that is
          to be retrieved.
      username: An optional string representing the username.

    Returns:
      A YouTubeUserEntry if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a username to the
          GetYouTubeUserEntry() method.
    """
    if uri is None and username is None:
      raise YouTubeError('You must provide at least a uri or a username '
                         'to the GetYouTubeUserEntry() method')
    elif username and not uri:
      uri = '%s/%s' % (YOUTUBE_USER_FEED_URI, username)
    return self.Get(uri, converter=gdata.youtube.YouTubeUserEntryFromString)

  def GetYouTubePlaylistFeed(self, uri=None, username='default'):
    """Retrieve a YouTubePlaylistFeed (a feed of playlists for a user).

    Either a uri or a username must be provided.

    Args:
      uri: An optional string representing the URI of the playlist feed that
          is to be retrieved.
      username: An optional string representing the username. Defaults to the
          currently authenticated user.

    Returns:
      A YouTubePlaylistFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a username to the
          GetYouTubePlaylistFeed() method.
    """
    if uri is None:
      uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'playlists')
    return self.Get(uri, converter=gdata.youtube.YouTubePlaylistFeedFromString)

  def GetYouTubePlaylistEntry(self, uri):
    """Retrieve a YouTubePlaylistEntry.

    Args:
      uri: A string representing the URI of the playlist feed that is to
          be retrieved.

    Returns:
      A YouTubePlaylistEntry if successfully retrieved.
    """
    return self.Get(uri, converter=gdata.youtube.YouTubePlaylistEntryFromString)

  def GetYouTubePlaylistVideoFeed(self, uri=None, playlist_id=None):
    """Retrieve a YouTubePlaylistVideoFeed (a feed of videos on a playlist).

    Either a uri or a playlist_id must be provided.

    Args:
      uri: An optional string representing the URI of the playlist video feed
          that is to be retrieved.
      playlist_id: An optional string representing the Id of the playlist whose
          playlist video feed is to be retrieved.

    Returns:
      A YouTubePlaylistVideoFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a playlist_id to the
          GetYouTubePlaylistVideoFeed() method.
    """
    if uri is None and playlist_id is None:
      raise YouTubeError('You must provide at least a uri or a playlist_id '
                         'to the GetYouTubePlaylistVideoFeed() method')
    elif playlist_id and not uri:
      uri = '%s/%s' % (YOUTUBE_PLAYLIST_FEED_URI, playlist_id)
    return self.Get(
        uri, converter=gdata.youtube.YouTubePlaylistVideoFeedFromString)

  def GetYouTubeVideoResponseFeed(self, uri=None, video_id=None):
    """Retrieve a YouTubeVideoResponseFeed.

    Either a uri or a playlist_id must be provided.

    Args:
      uri: An optional string representing the URI of the video response feed
          that is to be retrieved.
      video_id: An optional string representing the ID of the video whose
          response feed is to be retrieved.

    Returns:
      A YouTubeVideoResponseFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a video_id to the
          GetYouTubeVideoResponseFeed() method.
    """
    if uri is None and video_id is None:
      raise YouTubeError('You must provide at least a uri or a video_id '
                         'to the GetYouTubeVideoResponseFeed() method')
    elif video_id and not uri:
      uri = '%s/%s/%s' % (YOUTUBE_VIDEO_URI, video_id, 'responses')
    return self.Get(
        uri, converter=gdata.youtube.YouTubeVideoResponseFeedFromString)

  def GetYouTubeVideoResponseEntry(self, uri):
    """Retrieve a YouTubeVideoResponseEntry.

    Args:
      uri: A string representing the URI of the video response entry that
          is to be retrieved.

    Returns:
      A YouTubeVideoResponseEntry if successfully retrieved.
    """
    return self.Get(
        uri, converter=gdata.youtube.YouTubeVideoResponseEntryFromString)

  def GetYouTubeSubscriptionFeed(self, uri=None, username='default'):
    """Retrieve a YouTubeSubscriptionFeed.

    Either the uri of the feed or a username must be provided.

    Args:
      uri: An optional string representing the URI of the feed that is to
          be retrieved.
      username: An optional string representing the username whose subscription
          feed is to be retrieved. Defaults to the currently authenticted user.

    Returns:
      A YouTubeVideoSubscriptionFeed if successfully retrieved.
    """
    if uri is None:
      uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'subscriptions')
    return self.Get(
        uri, converter=gdata.youtube.YouTubeSubscriptionFeedFromString)

  def GetYouTubeSubscriptionEntry(self, uri):
    """Retrieve a YouTubeSubscriptionEntry.

    Args:
      uri: A string representing the URI of the entry that is to be retrieved.

    Returns:
      A YouTubeVideoSubscriptionEntry if successfully retrieved.
    """
    return self.Get(
        uri, converter=gdata.youtube.YouTubeSubscriptionEntryFromString)

  def GetYouTubeRelatedVideoFeed(self, uri=None, video_id=None):
    """Retrieve a YouTubeRelatedVideoFeed.

    Either a uri for the feed or a video_id is required.

    Args:
      uri: An optional string representing the URI of the feed that is to
          be retrieved.
      video_id: An optional string representing the ID of the video for which
          to retrieve the related video feed.

    Returns:
      A YouTubeRelatedVideoFeed if successfully retrieved.

    Raises:
      YouTubeError: You must provide at least a uri or a video_id to the
          GetYouTubeRelatedVideoFeed() method.
    """
    if uri is None and video_id is None:
      raise YouTubeError('You must provide at least a uri or a video_id '
                         'to the GetYouTubeRelatedVideoFeed() method')
    elif video_id and not uri:
      uri = '%s/%s/%s' % (YOUTUBE_VIDEO_URI, video_id, 'related')
    return self.Get(
        uri, converter=gdata.youtube.YouTubeVideoFeedFromString)

  def GetTopRatedVideoFeed(self):
    """Retrieve the 'top_rated' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_TOP_RATED_URI)

  def GetMostViewedVideoFeed(self):
    """Retrieve the 'most_viewed' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_MOST_VIEWED_URI)

  def GetRecentlyFeaturedVideoFeed(self):
    """Retrieve the 'recently_featured' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_RECENTLY_FEATURED_URI)

  def GetWatchOnMobileVideoFeed(self):
    """Retrieve the 'watch_on_mobile' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_WATCH_ON_MOBILE_URI)

  def GetTopFavoritesVideoFeed(self):
    """Retrieve the 'top_favorites' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_TOP_FAVORITES_URI)

  def GetMostRecentVideoFeed(self):
    """Retrieve the 'most_recent' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_MOST_RECENT_URI)

  def GetMostDiscussedVideoFeed(self):
    """Retrieve the 'most_discussed' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_MOST_DISCUSSED_URI)

  def GetMostLinkedVideoFeed(self):
    """Retrieve the 'most_linked' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_MOST_LINKED_URI)

  def GetMostRespondedVideoFeed(self):
    """Retrieve the 'most_responded' standard video feed.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.GetYouTubeVideoFeed(YOUTUBE_STANDARD_MOST_RESPONDED_URI)

  def GetUserFavoritesFeed(self, username='default'):
    """Retrieve the favorites feed for a given user.

    Args:
      username: An optional string representing the username whose favorites
          feed is to be retrieved. Defaults to the currently authenticated user.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    favorites_feed_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username,
                                       'favorites')
    return self.GetYouTubeVideoFeed(favorites_feed_uri)

  def InsertVideoEntry(self, video_entry, filename_or_handle,
                       youtube_username='default',
                       content_type='video/quicktime'):
    """Upload a new video to YouTube using the direct upload mechanism.

    Needs authentication.

    Args:
      video_entry: The YouTubeVideoEntry to upload.
      filename_or_handle: A file-like object or file name where the video
          will be read from.
      youtube_username: An optional string representing the username into whose
          account this video is to be uploaded to. Defaults to the currently
          authenticated user.
      content_type: An optional string representing internet media type
          (a.k.a. mime type) of the media object. Currently the YouTube API
          supports these types:
            o video/mpeg
            o video/quicktime
            o video/x-msvideo
            o video/mp4
            o video/x-flv

    Returns:
      The newly created YouTubeVideoEntry if successful.

    Raises:
      AssertionError: video_entry must be a gdata.youtube.VideoEntry instance.
      YouTubeError: An error occurred trying to read the video file provided.
      gdata.service.RequestError: An error occurred trying to upload the video
          to the API server.
    """

    # We need to perform a series of checks on the video_entry and on the
    # file that we plan to upload, such as checking whether we have a valid
    # video_entry and that the file is the correct type and readable, prior
    # to performing the actual POST request.

    try:
      assert(isinstance(video_entry, gdata.youtube.YouTubeVideoEntry))
    except AssertionError:
      raise YouTubeError({'status':YOUTUBE_INVALID_ARGUMENT,
          'body':'`video_entry` must be a gdata.youtube.VideoEntry instance',
          'reason':'Found %s, not VideoEntry' % type(video_entry)
          })
    #majtype, mintype = content_type.split('/')
    #
    #try:
    #  assert(mintype in YOUTUBE_SUPPORTED_UPLOAD_TYPES)
    #except (ValueError, AssertionError):
    #  raise YouTubeError({'status':YOUTUBE_INVALID_CONTENT_TYPE,
    #      'body':'This is not a valid content type: %s' % content_type,
    #      'reason':'Accepted content types: %s' %
    #          ['video/%s' % (t) for t in YOUTUBE_SUPPORTED_UPLOAD_TYPES]})

    if (isinstance(filename_or_handle, (str, unicode)) 
        and os.path.exists(filename_or_handle)):
      mediasource = gdata.MediaSource()
      mediasource.setFile(filename_or_handle, content_type)
    elif hasattr(filename_or_handle, 'read'):
      import StringIO
      if hasattr(filename_or_handle, 'seek'):
        filename_or_handle.seek(0)
      file_handle = StringIO.StringIO(filename_or_handle.read())
      name = 'video'
      if hasattr(filename_or_handle, 'name'):
        name = filename_or_handle.name
      mediasource = gdata.MediaSource(file_handle, content_type,
          content_length=file_handle.len, file_name=name)
    else:
      raise YouTubeError({'status':YOUTUBE_INVALID_ARGUMENT, 'body':
          '`filename_or_handle` must be a path name or a file-like object',
          'reason': ('Found %s, not path name or object '
                     'with a .read() method' % type(filename_or_handle))})
    upload_uri = '%s/%s/%s' % (YOUTUBE_UPLOAD_URI, youtube_username,
                              'uploads')
    self.additional_headers['Slug'] = mediasource.file_name

    # Using a nested try statement to retain Python 2.4 compatibility
    try:
      try:
        return self.Post(video_entry, uri=upload_uri, media_source=mediasource,
                         converter=gdata.youtube.YouTubeVideoEntryFromString)
      except gdata.service.RequestError, e:
        raise YouTubeError(e.args[0])
    finally:
      del(self.additional_headers['Slug'])

  def CheckUploadStatus(self, video_entry=None, video_id=None):
    """Check upload status on a recently uploaded video entry.

    Needs authentication. Either video_entry or video_id must be provided.

    Args:
      video_entry: An optional YouTubeVideoEntry whose upload status to check
      video_id: An optional string representing the ID of the uploaded video
          whose status is to be checked.

    Returns:
      A tuple containing (video_upload_state, detailed_message) or None if
          no status information is found.

    Raises:
      YouTubeError: You must provide at least a video_entry or a video_id to the
          CheckUploadStatus() method.
    """
    if video_entry is None and video_id is None:
      raise YouTubeError('You must provide at least a uri or a video_id '
                         'to the CheckUploadStatus() method')
    elif video_id and not video_entry:
       video_entry = self.GetYouTubeVideoEntry(video_id=video_id)

    control = video_entry.control
    if control is not None:
      draft = control.draft
      if draft is not None:
        if draft.text == 'yes':
          yt_state = control.extension_elements[0]
          if yt_state is not None:
            state_value = yt_state.attributes['name']
            message = ''
            if yt_state.text is not None:
              message = yt_state.text

            return (state_value, message)

  def GetFormUploadToken(self, video_entry, uri=YOUTUBE_UPLOAD_TOKEN_URI):
    """Receives a YouTube Token and a YouTube PostUrl from a YouTubeVideoEntry.

    Needs authentication.

    Args:
      video_entry: The YouTubeVideoEntry to upload (meta-data only).
      uri: An optional string representing the URI from where to fetch the
          token information. Defaults to the YOUTUBE_UPLOADTOKEN_URI.

    Returns:
      A tuple containing the URL to which to post your video file, along
          with the youtube token that must be included with your upload in the
          form of: (post_url, youtube_token).
    """
    try:
      response = self.Post(video_entry, uri)
    except gdata.service.RequestError, e:
      raise YouTubeError(e.args[0])

    tree = ElementTree.fromstring(response)

    for child in tree:
      if child.tag == 'url':
        post_url = child.text
      elif child.tag == 'token':
        youtube_token = child.text
    return (post_url, youtube_token)

  def UpdateVideoEntry(self, video_entry):
    """Updates a video entry's meta-data.

    Needs authentication.

    Args:
      video_entry: The YouTubeVideoEntry to update, containing updated
          meta-data.

    Returns:
      An updated YouTubeVideoEntry on success or None.
    """
    for link in video_entry.link:
      if link.rel == 'edit':
        edit_uri = link.href
    return self.Put(video_entry, uri=edit_uri,
                    converter=gdata.youtube.YouTubeVideoEntryFromString)

  def DeleteVideoEntry(self, video_entry):
    """Deletes a video entry.

    Needs authentication.

    Args:
      video_entry: The YouTubeVideoEntry to be deleted.

    Returns:
      True if entry was deleted successfully.
    """
    for link in video_entry.link:
      if link.rel == 'edit':
        edit_uri = link.href
    return self.Delete(edit_uri)

  def AddRating(self, rating_value, video_entry):
    """Add a rating to a video entry.

    Needs authentication.

    Args:
      rating_value: The integer value for the rating (between 1 and 5).
      video_entry: The YouTubeVideoEntry to be rated.

    Returns:
      True if the rating was added successfully.

    Raises:
      YouTubeError: rating_value must be between 1 and 5 in AddRating().
    """
    if rating_value < 1 or rating_value > 5:
      raise YouTubeError('rating_value must be between 1 and 5 in AddRating()')

    entry = gdata.GDataEntry()
    rating = gdata.youtube.Rating(min='1', max='5')
    rating.extension_attributes['name'] = 'value'
    rating.extension_attributes['value'] = str(rating_value)
    entry.extension_elements.append(rating)

    for link in video_entry.link:
      if link.rel == YOUTUBE_RATING_LINK_REL:
        rating_uri = link.href

    return self.Post(entry, uri=rating_uri)

  def AddComment(self, comment_text, video_entry):
    """Add a comment to a video entry.

    Needs authentication. Note that each comment that is posted must contain
        the video entry that it is to be posted to.

    Args:
      comment_text: A string representing the text of the comment.
      video_entry: The YouTubeVideoEntry to be commented on.

    Returns:
      True if the comment was added successfully.
    """
    content = atom.Content(text=comment_text)
    comment_entry = gdata.youtube.YouTubeVideoCommentEntry(content=content)
    comment_post_uri = video_entry.comments.feed_link[0].href

    return self.Post(comment_entry, uri=comment_post_uri)

  def AddVideoResponse(self, video_id_to_respond_to, video_response):
    """Add a video response.

    Needs authentication.

    Args:
      video_id_to_respond_to: A string representing the ID of the video to be
          responded to.
      video_response: YouTubeVideoEntry to be posted as a response.

    Returns:
      True if video response was posted successfully.
    """
    post_uri = '%s/%s/%s' % (YOUTUBE_VIDEO_URI, video_id_to_respond_to,
                             'responses')
    return self.Post(video_response, uri=post_uri)

  def DeleteVideoResponse(self, video_id, response_video_id):
    """Delete a video response.

    Needs authentication.

    Args:
      video_id: A string representing the ID of video that contains the
          response.
      response_video_id: A string representing the ID of the video that was
          posted as a response.

    Returns:
      True if video response was deleted succcessfully.
    """
    delete_uri = '%s/%s/%s/%s' % (YOUTUBE_VIDEO_URI, video_id, 'responses',
                                  response_video_id)
    return self.Delete(delete_uri)

  def AddComplaint(self, complaint_text, complaint_term, video_id):
    """Add a complaint for a particular video entry.

    Needs authentication.

    Args:
      complaint_text: A string representing the complaint text.
      complaint_term: A string representing the complaint category term.
      video_id: A string representing the ID of YouTubeVideoEntry to
          complain about.

    Returns:
      True if posted successfully.

    Raises:
      YouTubeError: Your complaint_term is not valid.
    """
    if complaint_term not in YOUTUBE_COMPLAINT_CATEGORY_TERMS:
      raise YouTubeError('Your complaint_term is not valid')

    content = atom.Content(text=complaint_text)
    category = atom.Category(term=complaint_term,
                             scheme=YOUTUBE_COMPLAINT_CATEGORY_SCHEME)

    complaint_entry = gdata.GDataEntry(content=content, category=[category])
    post_uri = '%s/%s/%s' % (YOUTUBE_VIDEO_URI, video_id, 'complaints')

    return self.Post(complaint_entry, post_uri)

  def AddVideoEntryToFavorites(self, video_entry, username='default'):
    """Add a video entry to a users favorite feed.

    Needs authentication.

    Args:
      video_entry: The YouTubeVideoEntry to add.
      username: An optional string representing the username to whose favorite
          feed you wish to add the entry. Defaults to the currently
          authenticated user.
    Returns:
        The posted YouTubeVideoEntry if successfully posted.
    """
    post_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'favorites')

    return self.Post(video_entry, post_uri,
                     converter=gdata.youtube.YouTubeVideoEntryFromString)

  def DeleteVideoEntryFromFavorites(self, video_id, username='default'):
    """Delete a video entry from the users favorite feed.

    Needs authentication.

    Args:
      video_id: A string representing the ID of the video that is to be removed
      username: An optional string representing the username of the user's
          favorite feed. Defaults to the currently authenticated user.

    Returns:
        True if entry was successfully deleted.
    """
    edit_link = '%s/%s/%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'favorites',
                                 video_id)
    return self.Delete(edit_link)

  def AddPlaylist(self, playlist_title, playlist_description,
                  playlist_private=None):
    """Add a new playlist to the currently authenticated users account.

    Needs authentication.

    Args:
      playlist_title: A string representing the title for the new playlist.
      playlist_description: A string representing the description of the
          playlist.
      playlist_private: An optional boolean, set to True if the playlist is
          to be private.

    Returns:
      The YouTubePlaylistEntry if successfully posted.
    """
    playlist_entry = gdata.youtube.YouTubePlaylistEntry(
        title=atom.Title(text=playlist_title),
        description=gdata.youtube.Description(text=playlist_description))
    if playlist_private:
      playlist_entry.private = gdata.youtube.Private()

    playlist_post_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, 'default', 
                                      'playlists')
    return self.Post(playlist_entry, playlist_post_uri,
                     converter=gdata.youtube.YouTubePlaylistEntryFromString)

  def UpdatePlaylist(self, playlist_id, new_playlist_title,
                     new_playlist_description, playlist_private=None,
                     username='default'):
    """Update a playlist with new meta-data.

    Needs authentication.

    Args:
      playlist_id: A string representing the ID of the playlist to be updated.
      new_playlist_title: A string representing a new title for the playlist.
      new_playlist_description: A string representing a new description for the
          playlist.
      playlist_private: An optional boolean, set to True if the playlist is
          to be private.
      username: An optional string representing the username whose playlist is
          to be updated. Defaults to the currently authenticated user.

   Returns:
      A YouTubePlaylistEntry if the update was successful.
    """
    updated_playlist = gdata.youtube.YouTubePlaylistEntry(
        title=atom.Title(text=new_playlist_title),
        description=gdata.youtube.Description(text=new_playlist_description))
    if playlist_private:
      updated_playlist.private = gdata.youtube.Private()

    playlist_put_uri = '%s/%s/playlists/%s' % (YOUTUBE_USER_FEED_URI, username,
                                               playlist_id)

    return self.Put(updated_playlist, playlist_put_uri,
                    converter=gdata.youtube.YouTubePlaylistEntryFromString)

  def DeletePlaylist(self, playlist_uri):
    """Delete a playlist from the currently authenticated users playlists.

    Needs authentication.

    Args:
      playlist_uri: A string representing the URI of the playlist that is
          to be deleted.

    Returns:
      True if successfully deleted.
    """
    return self.Delete(playlist_uri)

  def AddPlaylistVideoEntryToPlaylist(
      self, playlist_uri, video_id, custom_video_title=None,
      custom_video_description=None):
    """Add a video entry to a playlist, optionally providing a custom title
    and description.

    Needs authentication.

    Args:
      playlist_uri: A string representing the URI of the playlist to which this
          video entry is to be added.
      video_id: A string representing the ID of the video entry to add.
      custom_video_title: An optional string representing a custom title for
          the video (only shown on the playlist).
      custom_video_description: An optional string representing a custom
          description for the video (only shown on the playlist).

    Returns:
      A YouTubePlaylistVideoEntry if successfully posted.
    """
    playlist_video_entry = gdata.youtube.YouTubePlaylistVideoEntry(
        atom_id=atom.Id(text=video_id))
    if custom_video_title:
      playlist_video_entry.title = atom.Title(text=custom_video_title)
    if custom_video_description:
      playlist_video_entry.description = gdata.youtube.Description(
          text=custom_video_description)

    return self.Post(playlist_video_entry, playlist_uri,
                    converter=gdata.youtube.YouTubePlaylistVideoEntryFromString)

  def UpdatePlaylistVideoEntryMetaData(
      self, playlist_uri, playlist_entry_id, new_video_title, 
      new_video_description, new_video_position):
    """Update the meta data for a YouTubePlaylistVideoEntry.

    Needs authentication.

    Args:
      playlist_uri: A string representing the URI of the playlist that contains
          the entry to be updated.
      playlist_entry_id: A string representing the ID of the entry to be
          updated.
      new_video_title: A string representing the new title for the video entry.
      new_video_description: A string representing the new description for
          the video entry.
      new_video_position: An integer representing the new position on the
          playlist for the video.

    Returns:
      A YouTubePlaylistVideoEntry if the update was successful.
    """
    playlist_video_entry = gdata.youtube.YouTubePlaylistVideoEntry(
        title=atom.Title(text=new_video_title),
        description=gdata.youtube.Description(text=new_video_description),
        position=gdata.youtube.Position(text=str(new_video_position)))

    playlist_put_uri = playlist_uri + '/' + playlist_entry_id

    return self.Put(playlist_video_entry, playlist_put_uri,
                    converter=gdata.youtube.YouTubePlaylistVideoEntryFromString)

  def DeletePlaylistVideoEntry(self, playlist_uri, playlist_video_entry_id):
    """Delete a playlist video entry from a playlist.

    Needs authentication.

    Args:
      playlist_uri: A URI representing the playlist from which the playlist
          video entry is to be removed from.
      playlist_video_entry_id: A string representing id of the playlist video
          entry that is to be removed.

    Returns:
        True if entry was successfully deleted.
    """
    delete_uri = '%s/%s' % (playlist_uri, playlist_video_entry_id)
    return self.Delete(delete_uri)

  def AddSubscriptionToChannel(self, username_to_subscribe_to,
                               my_username = 'default'):
    """Add a new channel subscription to the currently authenticated users
    account.

    Needs authentication.

    Args:
      username_to_subscribe_to: A string representing the username of the 
          channel to which we want to subscribe to.
      my_username: An optional string representing the name of the user which
          we want to subscribe. Defaults to currently authenticated user.

    Returns:
      A new YouTubeSubscriptionEntry if successfully posted.
    """
    subscription_category = atom.Category(
        scheme=YOUTUBE_SUBSCRIPTION_CATEGORY_SCHEME,
        term='channel')
    subscription_username = gdata.youtube.Username(
        text=username_to_subscribe_to)

    subscription_entry = gdata.youtube.YouTubeSubscriptionEntry(
        category=subscription_category,
        username=subscription_username)

    post_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, my_username, 
                             'subscriptions')

    return self.Post(subscription_entry, post_uri,
                     converter=gdata.youtube.YouTubeSubscriptionEntryFromString)

  def AddSubscriptionToFavorites(self, username, my_username = 'default'):
    """Add a new subscription to a users favorites to the currently
    authenticated user's account.

    Needs authentication

    Args:
      username: A string representing the username of the user's favorite feed
          to subscribe to.
      my_username: An optional string representing the username of the user
          that is to be subscribed. Defaults to currently authenticated user.

    Returns:
        A new YouTubeSubscriptionEntry if successful.
    """
    subscription_category = atom.Category(
        scheme=YOUTUBE_SUBSCRIPTION_CATEGORY_SCHEME,
        term='favorites')
    subscription_username = gdata.youtube.Username(text=username)

    subscription_entry = gdata.youtube.YouTubeSubscriptionEntry(
        category=subscription_category,
        username=subscription_username)

    post_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, my_username,
                             'subscriptions')

    return self.Post(subscription_entry, post_uri,
                     converter=gdata.youtube.YouTubeSubscriptionEntryFromString)

  def AddSubscriptionToQuery(self, query, my_username = 'default'):
    """Add a new subscription to a specific keyword query to the currently
    authenticated user's account.

    Needs authentication

    Args:
      query: A string representing the keyword query to subscribe to.
      my_username: An optional string representing the username of the user
          that is to be subscribed. Defaults to currently authenticated user.

    Returns:
        A new YouTubeSubscriptionEntry if successful.
    """
    subscription_category = atom.Category(
        scheme=YOUTUBE_SUBSCRIPTION_CATEGORY_SCHEME,
        term='query')
    subscription_query_string = gdata.youtube.QueryString(text=query)

    subscription_entry = gdata.youtube.YouTubeSubscriptionEntry(
        category=subscription_category,
        query_string=subscription_query_string)

    post_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, my_username,
                             'subscriptions')

    return self.Post(subscription_entry, post_uri,
                     converter=gdata.youtube.YouTubeSubscriptionEntryFromString)



  def DeleteSubscription(self, subscription_uri):
    """Delete a subscription from the currently authenticated user's account.

    Needs authentication.

    Args:
      subscription_uri: A string representing the URI of the subscription that
          is to be deleted.

    Returns:
      True if deleted successfully.
    """
    return self.Delete(subscription_uri)

  def AddContact(self, contact_username, my_username='default'):
    """Add a new contact to the currently authenticated user's contact feed.

    Needs authentication.

    Args:
      contact_username: A string representing the username of the contact
          that you wish to add.
      my_username: An optional string representing the username to whose
          contact the new contact is to be added.

    Returns:
        A YouTubeContactEntry if added successfully.
    """
    contact_category = atom.Category(
        scheme = 'http://gdata.youtube.com/schemas/2007/contact.cat',
        term = 'Friends')
    contact_username = gdata.youtube.Username(text=contact_username)
    contact_entry = gdata.youtube.YouTubeContactEntry(
        category=contact_category,
        username=contact_username)

    contact_post_uri = '%s/%s/%s' % (YOUTUBE_USER_FEED_URI, my_username,
                                     'contacts')

    return self.Post(contact_entry, contact_post_uri,
                     converter=gdata.youtube.YouTubeContactEntryFromString)

  def UpdateContact(self, contact_username, new_contact_status, 
                    new_contact_category, my_username='default'):
    """Update a contact, providing a new status and a new category.

    Needs authentication.

    Args:
      contact_username: A string representing the username of the contact
          that is to be updated.
      new_contact_status: A string representing the new status of the contact.
          This can either be set to 'accepted' or 'rejected'.
      new_contact_category: A string representing the new category for the
          contact, either 'Friends' or 'Family'.
      my_username: An optional string representing the username of the user
          whose contact feed we are modifying. Defaults to the currently
          authenticated user.

    Returns:
      A YouTubeContactEntry if updated succesfully.

    Raises:
      YouTubeError: New contact status must be within the accepted values. Or
          new contact category must be within the accepted categories.
    """
    if new_contact_status not in YOUTUBE_CONTACT_STATUS:
      raise YouTubeError('New contact status must be one of %s' %
                          (' '.join(YOUTUBE_CONTACT_STATUS)))
    if new_contact_category not in YOUTUBE_CONTACT_CATEGORY:
      raise YouTubeError('New contact category must be one of %s' %
                         (' '.join(YOUTUBE_CONTACT_CATEGORY)))

    contact_category = atom.Category(
        scheme='http://gdata.youtube.com/schemas/2007/contact.cat',
        term=new_contact_category)

    contact_status = gdata.youtube.Status(text=new_contact_status)
    contact_entry = gdata.youtube.YouTubeContactEntry(
        category=contact_category,
        status=contact_status)

    contact_put_uri = '%s/%s/%s/%s' % (YOUTUBE_USER_FEED_URI, my_username,
                                       'contacts', contact_username)

    return self.Put(contact_entry, contact_put_uri,
                    converter=gdata.youtube.YouTubeContactEntryFromString)

  def DeleteContact(self, contact_username, my_username='default'):
    """Delete a contact from a users contact feed.

    Needs authentication.

    Args:
      contact_username: A string representing the username of the contact
          that is to be deleted.
      my_username: An optional string representing the username of the user's
          contact feed from which to delete the contact. Defaults to the
          currently authenticated user.

    Returns:
      True if the contact was deleted successfully
    """
    contact_edit_uri = '%s/%s/%s/%s' % (YOUTUBE_USER_FEED_URI, my_username,
                                        'contacts', contact_username)
    return self.Delete(contact_edit_uri)

  def _GetDeveloperKey(self):
    """Getter for Developer Key property.

    Returns:
      If the developer key has been set, a string representing the developer key
          is returned or None.
    """
    if 'X-GData-Key' in self.additional_headers:
      return self.additional_headers['X-GData-Key'][4:]
    else:
      return None

  def _SetDeveloperKey(self, developer_key):
    """Setter for Developer Key property.
    
    Sets the developer key in the 'X-GData-Key' header. The actual value that
        is set is 'key=' plus the developer_key that was passed.
    """
    self.additional_headers['X-GData-Key'] = 'key=' + developer_key

  developer_key = property(_GetDeveloperKey, _SetDeveloperKey,
                           doc="""The Developer Key property""")

  def _GetClientId(self):
    """Getter for Client Id property.

    Returns:
      If the client_id has been set, a string representing it is returned
          or None.
    """
    if 'X-Gdata-Client' in self.additional_headers:
      return self.additional_headers['X-Gdata-Client']
    else:
      return None

  def _SetClientId(self, client_id):
    """Setter for Client Id property.

    Sets the 'X-Gdata-Client' header.
    """
    self.additional_headers['X-Gdata-Client'] = client_id

  client_id = property(_GetClientId, _SetClientId,
                       doc="""The ClientId property""")

  def Query(self, uri):
    """Performs a query and returns a resulting feed or entry.

    Args:
      uri: A string representing the URI of the feed that is to be queried.

    Returns:
      On success, a tuple in the form:
      (boolean succeeded=True, ElementTree._Element result)
      On failure, a tuple in the form:
      (boolean succeeded=False, {'status': HTTP status code from server,
                                 'reason': HTTP reason from the server,
                                 'body': HTTP body of the server's response})
    """
    result = self.Get(uri)
    return result

  def YouTubeQuery(self, query):
    """Performs a YouTube specific query and returns a resulting feed or entry.

    Args:
      query: A Query object or one if its sub-classes (YouTubeVideoQuery,
          YouTubeUserQuery or YouTubePlaylistQuery).

    Returns:
      Depending on the type of Query object submitted returns either a
          YouTubeVideoFeed, a YouTubeUserFeed, a YouTubePlaylistFeed. If the
          Query object provided was not YouTube-related, a tuple is returned.
          On success the tuple will be in this form:
          (boolean succeeded=True, ElementTree._Element result)
          On failure, the tuple will be in this form:
          (boolean succeeded=False, {'status': HTTP status code from server,
                                     'reason': HTTP reason from the server,
                                     'body': HTTP body of the server response})
    """
    result = self.Query(query.ToUri())
    if isinstance(query, YouTubeVideoQuery):
      return gdata.youtube.YouTubeVideoFeedFromString(result.ToString())
    elif isinstance(query, YouTubeUserQuery):
      return gdata.youtube.YouTubeUserFeedFromString(result.ToString())
    elif isinstance(query, YouTubePlaylistQuery):
      return gdata.youtube.YouTubePlaylistFeedFromString(result.ToString())
    else:
      return result

class YouTubeVideoQuery(gdata.service.Query):

  """Subclasses gdata.service.Query to represent a YouTube Data API query.

  Attributes are set dynamically via properties. Properties correspond to
  the standard Google Data API query parameters with YouTube Data API
  extensions. Please refer to the API documentation for details.

  Attributes:
    vq: The vq parameter, which is only supported for video feeds, specifies a
        search query term. Refer to API documentation for further details.
    orderby: The orderby parameter, which is only supported for video feeds,
        specifies the value that will be used to sort videos in the search
        result set. Valid values for this parameter are relevance, published,
        viewCount and rating.
    time: The time parameter, which is only available for the top_rated,
        top_favorites, most_viewed, most_discussed, most_linked and
        most_responded standard feeds, restricts the search to videos uploaded
        within the specified time. Valid values for this parameter are today
        (1 day), this_week (7 days), this_month (1 month) and all_time.
        The default value for this parameter is all_time.
    format: The format parameter specifies that videos must be available in a
        particular video format. Refer to the API documentation for details.
    racy: The racy parameter allows a search result set to include restricted
        content as well as standard content. Valid values for this parameter
        are include and exclude. By default, restricted content is excluded.
    lr: The lr parameter restricts the search to videos that have a title,
        description or keywords in a specific language. Valid values for the lr
        parameter are ISO 639-1 two-letter language codes.
    restriction: The restriction parameter identifies the IP address that
        should be used to filter videos that can only be played in specific
        countries.
    location: A string of geo coordinates. Note that this is not used when the
        search is performed but rather to filter the returned videos for ones
        that match to the location entered.
    feed: str (optional) The base URL which is the beginning of the query URL.
          defaults to 'http://%s/feeds/videos' % (YOUTUBE_SERVER)
  """

  def __init__(self, video_id=None, feed_type=None, text_query=None,
               params=None, categories=None, feed=None):

    if feed_type in YOUTUBE_STANDARDFEEDS and feed is None:
      feed = 'http://%s/feeds/standardfeeds/%s' % (YOUTUBE_SERVER, feed_type)
    elif (feed_type is 'responses' or feed_type is 'comments' and video_id
          and feed is None):
      feed = 'http://%s/feeds/videos/%s/%s' % (YOUTUBE_SERVER, video_id,
                                               feed_type)
    elif feed is None:
      feed = 'http://%s/feeds/videos' % (YOUTUBE_SERVER)

    gdata.service.Query.__init__(self, feed, text_query=text_query,
                                 params=params, categories=categories)
 
  def _GetVideoQuery(self):
    if 'vq' in self:
      return self['vq']
    else:
      return None

  def _SetVideoQuery(self, val):
    self['vq'] = val

  vq = property(_GetVideoQuery, _SetVideoQuery,
                doc="""The video query (vq) query parameter""")

  def _GetOrderBy(self):
    if 'orderby' in self:
      return self['orderby']
    else:
      return None

  def _SetOrderBy(self, val):
    if val not in YOUTUBE_QUERY_VALID_ORDERBY_PARAMETERS:
      if val.startswith('relevance_lang_') is False:
        raise YouTubeError('OrderBy must be one of: %s ' %
                           ' '.join(YOUTUBE_QUERY_VALID_ORDERBY_PARAMETERS))
    self['orderby'] = val

  orderby = property(_GetOrderBy, _SetOrderBy,
                     doc="""The orderby query parameter""")

  def _GetTime(self):
    if 'time' in self:
      return self['time']
    else:
      return None

  def _SetTime(self, val):
    if val not in YOUTUBE_QUERY_VALID_TIME_PARAMETERS:
      raise YouTubeError('Time must be one of: %s ' %
                         ' '.join(YOUTUBE_QUERY_VALID_TIME_PARAMETERS))
    self['time'] = val

  time = property(_GetTime, _SetTime,
                  doc="""The time query parameter""")

  def _GetFormat(self):
    if 'format' in self:
      return self['format']
    else:
      return None

  def _SetFormat(self, val):
    if val not in YOUTUBE_QUERY_VALID_FORMAT_PARAMETERS:
      raise YouTubeError('Format must be one of: %s ' %
                         ' '.join(YOUTUBE_QUERY_VALID_FORMAT_PARAMETERS))
    self['format'] = val

  format = property(_GetFormat, _SetFormat,
                    doc="""The format query parameter""")

  def _GetRacy(self):
    if 'racy' in self:
      return self['racy']
    else:
      return None

  def _SetRacy(self, val):
    if val not in YOUTUBE_QUERY_VALID_RACY_PARAMETERS:
      raise YouTubeError('Racy must be one of: %s ' %
                         ' '.join(YOUTUBE_QUERY_VALID_RACY_PARAMETERS))
    self['racy'] = val

  racy = property(_GetRacy, _SetRacy, 
                  doc="""The racy query parameter""")

  def _GetLanguageRestriction(self):
    if 'lr' in self:
      return self['lr']
    else:
      return None

  def _SetLanguageRestriction(self, val):
    self['lr'] = val

  lr = property(_GetLanguageRestriction, _SetLanguageRestriction,
                doc="""The lr (language restriction) query parameter""")

  def _GetIPRestriction(self):
    if 'restriction' in self:
      return self['restriction']
    else:
      return None

  def _SetIPRestriction(self, val):
    self['restriction'] = val

  restriction = property(_GetIPRestriction, _SetIPRestriction,
                         doc="""The restriction query parameter""")

  def _GetLocation(self):
    if 'location' in self:
      return self['location']
    else:
      return None

  def _SetLocation(self, val):
    self['location'] = val

  location = property(_GetLocation, _SetLocation,
                      doc="""The location query parameter""")



class YouTubeUserQuery(YouTubeVideoQuery):

  """Subclasses YouTubeVideoQuery to perform user-specific queries.

  Attributes are set dynamically via properties. Properties correspond to
  the standard Google Data API query parameters with YouTube Data API
  extensions.
  """

  def __init__(self, username=None, feed_type=None, subscription_id=None,
               text_query=None, params=None, categories=None):

    uploads_favorites_playlists = ('uploads', 'favorites', 'playlists')

    if feed_type is 'subscriptions' and subscription_id and username:
      feed = "http://%s/feeds/users/%s/%s/%s" % (YOUTUBE_SERVER, username,
                                                 feed_type, subscription_id)
    elif feed_type is 'subscriptions' and not subscription_id and username:
      feed = "http://%s/feeds/users/%s/%s" % (YOUTUBE_SERVER, username,
                                              feed_type)
    elif feed_type in uploads_favorites_playlists:
      feed = "http://%s/feeds/users/%s/%s" % (YOUTUBE_SERVER, username, 
                                              feed_type)
    else:
      feed = "http://%s/feeds/users" % (YOUTUBE_SERVER)

    YouTubeVideoQuery.__init__(self, feed, text_query=text_query,
                               params=params, categories=categories)


class YouTubePlaylistQuery(YouTubeVideoQuery):

  """Subclasses YouTubeVideoQuery to perform playlist-specific queries.

  Attributes are set dynamically via properties. Properties correspond to
  the standard Google Data API query parameters with YouTube Data API
  extensions.
  """

  def __init__(self, playlist_id, text_query=None, params=None,
               categories=None):
    if playlist_id:
      feed = "http://%s/feeds/playlists/%s" % (YOUTUBE_SERVER, playlist_id)
    else:
      feed = "http://%s/feeds/playlists" % (YOUTUBE_SERVER)

    YouTubeVideoQuery.__init__(self, feed, text_query=text_query,
                               params=params, categories=categories)
