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


"""Contains the data classes of the YouTube Data API"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import atom.data
import gdata.data
import gdata.geo.data
import gdata.media.data
import gdata.opensearch.data
import gdata.youtube.data


YT_TEMPLATE = '{http://gdata.youtube.com/schemas/2007/}%s'


class ComplaintEntry(gdata.data.GDEntry):
  """Describes a complaint about a video"""


class ComplaintFeed(gdata.data.GDFeed):
  """Describes complaints about a video"""
  entry = [ComplaintEntry]


class RatingEntry(gdata.data.GDEntry):
  """A rating about a video"""
  rating = gdata.data.Rating


class RatingFeed(gdata.data.GDFeed):
  """Describes ratings for a video"""
  entry = [RatingEntry]


class YouTubeMediaContent(gdata.media.data.MediaContent):
  """Describes a you tube media content"""
  _qname = gdata.media.data.MEDIA_TEMPLATE % 'content'
  format = 'format'


class YtAge(atom.core.XmlElement):
  """User's age"""
  _qname = YT_TEMPLATE % 'age'


class YtBooks(atom.core.XmlElement):
  """User's favorite books"""
  _qname = YT_TEMPLATE % 'books'


class YtCompany(atom.core.XmlElement):
  """User's company"""
  _qname = YT_TEMPLATE % 'company'


class YtDescription(atom.core.XmlElement):
  """Description"""
  _qname = YT_TEMPLATE % 'description'


class YtDuration(atom.core.XmlElement):
  """Video duration"""
  _qname = YT_TEMPLATE % 'duration'
  seconds = 'seconds'


class YtFirstName(atom.core.XmlElement):
  """User's first name"""
  _qname = YT_TEMPLATE % 'firstName'


class YtGender(atom.core.XmlElement):
  """User's gender"""
  _qname = YT_TEMPLATE % 'gender'


class YtHobbies(atom.core.XmlElement):
  """User's hobbies"""
  _qname = YT_TEMPLATE % 'hobbies'


class YtHometown(atom.core.XmlElement):
  """User's hometown"""
  _qname = YT_TEMPLATE % 'hometown'


class YtLastName(atom.core.XmlElement):
  """User's last name"""
  _qname = YT_TEMPLATE % 'lastName'


class YtLocation(atom.core.XmlElement):
  """Location"""
  _qname = YT_TEMPLATE % 'location'


class YtMovies(atom.core.XmlElement):
  """User's favorite movies"""
  _qname = YT_TEMPLATE % 'movies'


class YtMusic(atom.core.XmlElement):
  """User's favorite music"""
  _qname = YT_TEMPLATE % 'music'


class YtNoEmbed(atom.core.XmlElement):
  """Disables embedding for the video"""
  _qname = YT_TEMPLATE % 'noembed'


class YtOccupation(atom.core.XmlElement):
  """User's occupation"""
  _qname = YT_TEMPLATE % 'occupation'


class YtPlaylistId(atom.core.XmlElement):
  """Playlist id"""
  _qname = YT_TEMPLATE % 'playlistId'


class YtPosition(atom.core.XmlElement):
  """Video position on the playlist"""
  _qname = YT_TEMPLATE % 'position'


class YtPrivate(atom.core.XmlElement):
  """Flags the entry as private"""
  _qname = YT_TEMPLATE % 'private'


class YtQueryString(atom.core.XmlElement):
  """Keywords or query string associated with a subscription"""
  _qname = YT_TEMPLATE % 'queryString'


class YtRacy(atom.core.XmlElement):
  """Mature content"""
  _qname = YT_TEMPLATE % 'racy'


class YtRecorded(atom.core.XmlElement):
  """Date when the video was recorded"""
  _qname = YT_TEMPLATE % 'recorded'


class YtRelationship(atom.core.XmlElement):
  """User's relationship status"""
  _qname = YT_TEMPLATE % 'relationship'


class YtSchool(atom.core.XmlElement):
  """User's school"""
  _qname = YT_TEMPLATE % 'school'


class YtStatistics(atom.core.XmlElement):
  """Video and user statistics"""
  _qname = YT_TEMPLATE % 'statistics'
  favorite_count = 'favoriteCount'
  video_watch_count = 'videoWatchCount'
  view_count = 'viewCount'
  last_web_access = 'lastWebAccess'
  subscriber_count = 'subscriberCount'


class YtStatus(atom.core.XmlElement):
  """Status of a contact"""
  _qname = YT_TEMPLATE % 'status'


class YtUserProfileStatistics(YtStatistics):
  """User statistics"""
  _qname = YT_TEMPLATE % 'statistics'


class YtUsername(atom.core.XmlElement):
  """Youtube username"""
  _qname = YT_TEMPLATE % 'username'


class FriendEntry(gdata.data.BatchEntry):
  """Describes a contact in friend list"""
  username = YtUsername
  status = YtStatus
  email = gdata.data.Email


class FriendFeed(gdata.data.BatchFeed):
  """Describes user's friends"""
  entry = [FriendEntry]


class YtVideoStatistics(YtStatistics):
  """Video statistics"""
  _qname = YT_TEMPLATE % 'statistics'


class ChannelEntry(gdata.data.GDEntry):
  """Describes a video channel"""


class ChannelFeed(gdata.data.GDFeed):
  """Describes channels"""
  entry = [ChannelEntry]


class FavoriteEntry(gdata.data.BatchEntry):
  """Describes a favorite video"""


class FavoriteFeed(gdata.data.BatchFeed):
  """Describes favorite videos"""
  entry = [FavoriteEntry]


class YouTubeMediaCredit(gdata.media.data.MediaCredit):
  """Describes a you tube media credit"""
  _qname = gdata.media.data.MEDIA_TEMPLATE % 'credit'
  type = 'type'


class YouTubeMediaRating(gdata.media.data.MediaRating):
  """Describes a you tube media rating"""
  _qname = gdata.media.data.MEDIA_TEMPLATE % 'rating'
  country = 'country'


class YtAboutMe(atom.core.XmlElement):
  """User's self description"""
  _qname = YT_TEMPLATE % 'aboutMe'


class UserProfileEntry(gdata.data.BatchEntry):
  """Describes an user's profile"""
  relationship = YtRelationship
  description = YtDescription
  location = YtLocation
  statistics = YtUserProfileStatistics
  school = YtSchool
  music = YtMusic
  first_name = YtFirstName
  gender = YtGender
  occupation = YtOccupation
  hometown = YtHometown
  company = YtCompany
  movies = YtMovies
  books = YtBooks
  username = YtUsername
  about_me = YtAboutMe
  last_name = YtLastName
  age = YtAge
  thumbnail = gdata.media.data.MediaThumbnail
  hobbies = YtHobbies


class UserProfileFeed(gdata.data.BatchFeed):
  """Describes a feed of user's profile"""
  entry = [UserProfileEntry]


class YtAspectRatio(atom.core.XmlElement):
  """The aspect ratio of a media file"""
  _qname = YT_TEMPLATE % 'aspectRatio'


class YtBasePublicationState(atom.core.XmlElement):
  """Status of an unpublished entry"""
  _qname = YT_TEMPLATE % 'state'
  help_url = 'helpUrl'


class YtPublicationState(YtBasePublicationState):
  """Status of an unpublished video"""
  _qname = YT_TEMPLATE % 'state'
  name = 'name'
  reason_code = 'reasonCode'


class YouTubeAppControl(atom.data.Control):
  """Describes a you tube app control"""
  _qname = (atom.data.APP_TEMPLATE_V1 % 'control',
      atom.data.APP_TEMPLATE_V2 % 'control')
  state = YtPublicationState


class YtCaptionPublicationState(YtBasePublicationState):
  """Status of an unpublished caption track"""
  _qname = YT_TEMPLATE % 'state'
  reason_code = 'reasonCode'
  name = 'name'


class YouTubeCaptionAppControl(atom.data.Control):
  """Describes a you tube caption app control"""
  _qname = atom.data.APP_TEMPLATE_V2 % 'control'
  state = YtCaptionPublicationState


class CaptionTrackEntry(gdata.data.GDEntry):
  """Describes a caption track"""


class CaptionTrackFeed(gdata.data.GDFeed):
  """Describes caption tracks"""
  entry = [CaptionTrackEntry]


class YtCountHint(atom.core.XmlElement):
  """Hint as to how many entries the linked feed contains"""
  _qname = YT_TEMPLATE % 'countHint'


class PlaylistLinkEntry(gdata.data.BatchEntry):
  """Describes a playlist"""
  description = YtDescription
  playlist_id = YtPlaylistId
  count_hint = YtCountHint
  private = YtPrivate


class PlaylistLinkFeed(gdata.data.BatchFeed):
  """Describes list of playlists"""
  entry = [PlaylistLinkEntry]


class YtModerationStatus(atom.core.XmlElement):
  """Moderation status"""
  _qname = YT_TEMPLATE % 'moderationStatus'


class YtPlaylistTitle(atom.core.XmlElement):
  """Playlist title"""
  _qname = YT_TEMPLATE % 'playlistTitle'


class SubscriptionEntry(gdata.data.BatchEntry):
  """Describes user's channel subscritpions"""
  count_hint = YtCountHint
  playlist_title = YtPlaylistTitle
  thumbnail = gdata.media.data.MediaThumbnail
  username = YtUsername
  query_string = YtQueryString
  playlist_id = YtPlaylistId


class SubscriptionFeed(gdata.data.BatchFeed):
  """Describes list of user's video subscriptions"""
  entry = [SubscriptionEntry]


class YtSpam(atom.core.XmlElement):
  """Indicates that the entry probably contains spam"""
  _qname = YT_TEMPLATE % 'spam'


class CommentEntry(gdata.data.BatchEntry):
  """Describes a comment for a video"""
  spam = YtSpam


class CommentFeed(gdata.data.BatchFeed):
  """Describes comments for a video"""
  entry = [CommentEntry]


class YtUploaded(atom.core.XmlElement):
  """Date/Time at which the video was uploaded"""
  _qname = YT_TEMPLATE % 'uploaded'


class YtVideoId(atom.core.XmlElement):
  """Video id"""
  _qname = YT_TEMPLATE % 'videoid'


class YouTubeMediaGroup(gdata.media.data.MediaGroup):
  """Describes a you tube media group"""
  _qname = gdata.media.data.MEDIA_TEMPLATE % 'group'
  videoid = YtVideoId
  private = YtPrivate
  duration = YtDuration
  aspect_ratio = YtAspectRatio
  uploaded = YtUploaded


class VideoEntryBase(gdata.data.GDEntry):
  """Elements that describe or contain videos"""
  group = YouTubeMediaGroup
  statistics = YtVideoStatistics
  racy = YtRacy
  recorded = YtRecorded
  where = gdata.geo.data.GeoRssWhere
  rating = gdata.data.Rating
  noembed = YtNoEmbed
  location = YtLocation
  comments = gdata.data.Comments


class PlaylistEntry(gdata.data.BatchEntry):
  """Describes a video in a playlist"""
  description = YtDescription
  position = YtPosition


class PlaylistFeed(gdata.data.BatchFeed):
  """Describes videos in a playlist"""
  private = YtPrivate
  group = YouTubeMediaGroup
  playlist_id = YtPlaylistId
  entry = [PlaylistEntry]


class VideoEntry(gdata.data.BatchEntry):
  """Describes a video"""


class VideoFeed(gdata.data.BatchFeed):
  """Describes a video feed"""
  entry = [VideoEntry]


class VideoMessageEntry(gdata.data.BatchEntry):
  """Describes a video message"""
  description = YtDescription


class VideoMessageFeed(gdata.data.BatchFeed):
  """Describes videos in a videoMessage"""
  entry = [VideoMessageEntry]


class UserEventEntry(gdata.data.GDEntry):
  """Describes a user event"""
  playlist_id = YtPlaylistId
  videoid = YtVideoId
  username = YtUsername
  query_string = YtQueryString
  rating = gdata.data.Rating


class UserEventFeed(gdata.data.GDFeed):
  """Describes list of events"""
  entry = [UserEventEntry]


class VideoModerationEntry(gdata.data.GDEntry):
  """Describes video moderation"""
  moderation_status = YtModerationStatus
  videoid = YtVideoId


class VideoModerationFeed(gdata.data.GDFeed):
  """Describes a video moderation feed"""
  entry = [VideoModerationEntry]


class TrackContent(atom.data.Content):
  lang = atom.data.XML_TEMPLATE % 'lang'


class TrackEntry(gdata.data.GDEntry):
  """Represents the URL for a caption track"""
  content = TrackContent

  def get_caption_track_id(self):
    """Extracts the ID of this caption track.
    Returns:
      The caption track's id as a string.
    """
    if self.id.text:
      match = CAPTION_TRACK_ID_PATTERN.match(self.id.text)
      if match:
        return match.group(2)
    return None

  GetCaptionTrackId = get_caption_track_id


class CaptionFeed(gdata.data.GDFeed):
  """Represents a caption feed for a video on YouTube."""
  entry = [TrackEntry]
