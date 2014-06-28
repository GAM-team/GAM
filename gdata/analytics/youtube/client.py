#!/usr/bin/env python
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

"""Contains a client to communicate with the YouTube servers.

  A quick and dirty port of the YouTube GDATA 1.0 Python client
  libraries to version 2.0 of the GDATA library.

"""

# __author__ = 's.@google.com (John Skidgel)'

import logging

import gdata.client
import gdata.youtube.data
import atom.data
import atom.http_core

# Constants
# -----------------------------------------------------------------------------
YOUTUBE_CLIENTLOGIN_AUTHENTICATION_URL = 'https://www.google.com/youtube/accounts/ClientLogin'
YOUTUBE_SUPPORTED_UPLOAD_TYPES = ('mov', 'avi', 'wmv', 'mpg', 'quicktime',
                                  'flv')
YOUTUBE_QUERY_VALID_TIME_PARAMETERS = ('today', 'this_week', 'this_month',
                                       'all_time')
YOUTUBE_QUERY_VALID_ORDERBY_PARAMETERS = ('published', 'viewCount', 'rating',
                                          'relevance')
YOUTUBE_QUERY_VALID_RACY_PARAMETERS = ('include', 'exclude')
YOUTUBE_QUERY_VALID_FORMAT_PARAMETERS = ('1', '5', '6')
YOUTUBE_STANDARDFEEDS = ('most_recent', 'recently_featured',
                         'top_rated', 'most_viewed','watch_on_mobile')

YOUTUBE_UPLOAD_TOKEN_URI = 'http://gdata.youtube.com/action/GetUploadToken'
YOUTUBE_SERVER = 'gdata.youtube.com/feeds/api'
YOUTUBE_SERVICE = 'youtube'
YOUTUBE_VIDEO_FEED_URI = 'http://%s/videos' % YOUTUBE_SERVER
YOUTUBE_USER_FEED_URI = 'http://%s/users/' % YOUTUBE_SERVER

# Takes a youtube video ID.
YOUTUBE_CAPTION_FEED_URI = 'http://gdata.youtube.com/feeds/api/videos/%s/captions'

# Takes a youtube video ID and a caption track ID.
YOUTUBE_CAPTION_URI = 'http://gdata.youtube.com/feeds/api/videos/%s/captiondata/%s'

YOUTUBE_CAPTION_MIME_TYPE = 'application/vnd.youtube.timedtext; charset=UTF-8'


# Classes
# -----------------------------------------------------------------------------
class Error(Exception):
  """Base class for errors within the YouTube service."""
  pass


class RequestError(Error):
  """Error class that is thrown in response to an invalid HTTP Request."""
  pass


class YouTubeError(Error):
  """YouTube service specific error class."""
  pass


class YouTubeClient(gdata.client.GDClient):
  """Client for the YouTube service.

  Performs a partial list of Google Data YouTube API functions, such as
  retrieving the videos feed for a user and the feed for a video.
  YouTube Service requires authentication for any write, update or delete
  actions.
  """
  api_version = '2'
  auth_service = YOUTUBE_SERVICE
  auth_scopes = ['http://%s' % YOUTUBE_SERVER, 'https://%s' % YOUTUBE_SERVER]

  def get_videos(self, uri=YOUTUBE_VIDEO_FEED_URI, auth_token=None,
                         desired_class=gdata.youtube.data.VideoFeed,
                         **kwargs):
    """Retrieves a YouTube video feed.
    Args:
      uri: A string representing the URI of the feed that is to be retrieved.

    Returns:
      A YouTubeVideoFeed if successfully retrieved.
    """
    return self.get_feed(uri, auth_token=auth_token,
                         desired_class=desired_class,
                         **kwargs)

  GetVideos = get_videos


  def get_user_feed(self, uri=None, username=None):
    """Retrieve a YouTubeVideoFeed of user uploaded videos.

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
      uri = '%s%s/%s' % (YOUTUBE_USER_FEED_URI, username, 'uploads')
    return self.get_feed(uri, desired_class=gdata.youtube.data.VideoFeed)

  GetUserFeed = get_user_feed


  def get_video_entry(self, uri=None, video_id=None,
      auth_token=None, **kwargs):
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
                         'to the get_youtube_video_entry() method')
    elif video_id and uri is None:
      uri = '%s/%s' % (YOUTUBE_VIDEO_FEED_URI, video_id)
    return self.get_feed(uri,
        desired_class=gdata.youtube.data.VideoEntry,
        auth_token=auth_token,
        **kwargs)

  GetVideoEntry = get_video_entry


  def get_caption_feed(self, uri):
    """Retrieve a Caption feed of tracks.

    Args:
      uri: A string representing the caption feed's URI to be retrieved.

    Returns:
      A YouTube CaptionFeed if successfully retrieved.
    """
    return self.get_feed(uri, desired_class=gdata.youtube.data.CaptionFeed)

  GetCaptionFeed = get_caption_feed

  def get_caption_track(self, track_url, client_id,
                        developer_key, auth_token=None, **kwargs):
    http_request = atom.http_core.HttpRequest(uri = track_url, method = 'GET')
    dev_key = 'key=' + developer_key
    authsub = 'AuthSub token="' + str(auth_token) + '"'
    http_request.headers = {
      'Authorization': authsub,
      'X-GData-Client': client_id,
      'X-GData-Key': dev_key
    }
    return self.request(http_request=http_request, **kwargs)

  GetCaptionTrack = get_caption_track

  def create_track(self, video_id, title, language, body, client_id,
                   developer_key, auth_token=None, title_type='text', **kwargs):
    """Creates a closed-caption track and adds to an existing YouTube video.
    """
    new_entry = gdata.youtube.data.TrackEntry(
        content = gdata.youtube.data.TrackContent(text = body, lang = language))
    uri = YOUTUBE_CAPTION_FEED_URI % video_id
    http_request = atom.http_core.HttpRequest(uri = uri, method = 'POST')
    dev_key = 'key=' + developer_key
    authsub = 'AuthSub token="' + str(auth_token) + '"'
    http_request.headers = {
      'Content-Type': YOUTUBE_CAPTION_MIME_TYPE,
      'Content-Language': language,
      'Slug': title,
      'Authorization': authsub,
      'GData-Version': self.api_version,
      'X-GData-Client': client_id,
      'X-GData-Key': dev_key
    }
    http_request.add_body_part(body, http_request.headers['Content-Type'])
    return self.request(http_request = http_request,
        desired_class = new_entry.__class__, **kwargs)


  CreateTrack = create_track

  def delete_track(self, video_id, track, client_id, developer_key,
                   auth_token=None, **kwargs):
    """Deletes a track."""
    if isinstance(track, gdata.youtube.data.TrackEntry):
      track_id_text_node = track.get_id().split(':')
      track_id = track_id_text_node[3]
    else:
      track_id = track
    uri = YOUTUBE_CAPTION_URI % (video_id, track_id)
    http_request = atom.http_core.HttpRequest(uri = uri, method = 'DELETE')
    dev_key = 'key=' + developer_key
    authsub = 'AuthSub token="' + str(auth_token) + '"'
    http_request.headers = {
      'Authorization': authsub,
      'GData-Version': self.api_version,
      'X-GData-Client': client_id,
      'X-GData-Key': dev_key
    }
    return self.request(http_request=http_request, **kwargs)

  DeleteTrack = delete_track

  def update_track(self, video_id, track, body, client_id, developer_key,
                   auth_token=None, **kwargs):
    """Updates a closed-caption track for an existing YouTube video.
    """
    track_id_text_node = track.get_id().split(':')
    track_id = track_id_text_node[3]
    uri = YOUTUBE_CAPTION_URI % (video_id, track_id)
    http_request = atom.http_core.HttpRequest(uri = uri, method = 'PUT')
    dev_key = 'key=' + developer_key
    authsub = 'AuthSub token="' + str(auth_token) + '"'
    http_request.headers = {
      'Content-Type': YOUTUBE_CAPTION_MIME_TYPE,
      'Authorization': authsub,
      'GData-Version': self.api_version,
      'X-GData-Client': client_id,
      'X-GData-Key': dev_key
    }
    http_request.add_body_part(body, http_request.headers['Content-Type'])
    return self.request(http_request = http_request,
        desired_class = track.__class__, **kwargs)

  UpdateTrack = update_track
