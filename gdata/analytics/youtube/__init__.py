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

__author__ = ('api.stephaniel@gmail.com (Stephanie Liu)'
              ', api.jhartmann@gmail.com (Jochen Hartmann)')

import atom
import gdata
import gdata.media as Media
import gdata.geo as Geo

YOUTUBE_NAMESPACE = 'http://gdata.youtube.com/schemas/2007'
YOUTUBE_FORMAT = '{http://gdata.youtube.com/schemas/2007}format'
YOUTUBE_DEVELOPER_TAG_SCHEME = '%s/%s' % (YOUTUBE_NAMESPACE,
                                          'developertags.cat')
YOUTUBE_SUBSCRIPTION_TYPE_SCHEME = '%s/%s' % (YOUTUBE_NAMESPACE,
                                              'subscriptiontypes.cat')

class Username(atom.AtomBase):
  """The YouTube Username element"""
  _tag = 'username'
  _namespace = YOUTUBE_NAMESPACE

class QueryString(atom.AtomBase):
  """The YouTube QueryString element"""
  _tag = 'queryString'
  _namespace = YOUTUBE_NAMESPACE


class FirstName(atom.AtomBase):
  """The YouTube FirstName element"""
  _tag = 'firstName'
  _namespace = YOUTUBE_NAMESPACE


class LastName(atom.AtomBase):
  """The YouTube LastName element"""
  _tag = 'lastName'
  _namespace = YOUTUBE_NAMESPACE


class Age(atom.AtomBase):
  """The YouTube Age element"""
  _tag = 'age'
  _namespace = YOUTUBE_NAMESPACE


class Books(atom.AtomBase):
  """The YouTube Books element"""
  _tag = 'books'
  _namespace = YOUTUBE_NAMESPACE  


class Gender(atom.AtomBase):
  """The YouTube Gender element"""
  _tag = 'gender'
  _namespace = YOUTUBE_NAMESPACE  


class Company(atom.AtomBase):
  """The YouTube Company element"""
  _tag = 'company'
  _namespace = YOUTUBE_NAMESPACE  


class Hobbies(atom.AtomBase):
  """The YouTube Hobbies element"""
  _tag = 'hobbies'
  _namespace = YOUTUBE_NAMESPACE  


class Hometown(atom.AtomBase):
  """The YouTube Hometown element"""
  _tag = 'hometown'
  _namespace = YOUTUBE_NAMESPACE  


class Location(atom.AtomBase):
  """The YouTube Location element"""
  _tag = 'location'
  _namespace = YOUTUBE_NAMESPACE 


class Movies(atom.AtomBase):
  """The YouTube Movies element"""
  _tag = 'movies'
  _namespace = YOUTUBE_NAMESPACE    


class Music(atom.AtomBase):
  """The YouTube Music element"""
  _tag = 'music'
  _namespace = YOUTUBE_NAMESPACE    


class Occupation(atom.AtomBase):
  """The YouTube Occupation element"""
  _tag = 'occupation'
  _namespace = YOUTUBE_NAMESPACE  


class School(atom.AtomBase):
  """The YouTube School element"""
  _tag = 'school'
  _namespace = YOUTUBE_NAMESPACE  


class Relationship(atom.AtomBase):
  """The YouTube Relationship element"""
  _tag = 'relationship'
  _namespace = YOUTUBE_NAMESPACE  


class Recorded(atom.AtomBase):
  """The YouTube Recorded element"""
  _tag = 'recorded'
  _namespace = YOUTUBE_NAMESPACE


class Statistics(atom.AtomBase):
  """The YouTube Statistics element."""
  _tag = 'statistics'
  _namespace = YOUTUBE_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy() 
  _attributes['viewCount'] = 'view_count'
  _attributes['videoWatchCount'] = 'video_watch_count'
  _attributes['subscriberCount'] = 'subscriber_count'
  _attributes['lastWebAccess'] = 'last_web_access'
  _attributes['favoriteCount'] = 'favorite_count'

  def __init__(self, view_count=None, video_watch_count=None,
               favorite_count=None, subscriber_count=None, last_web_access=None,
               extension_elements=None, extension_attributes=None, text=None):

    self.view_count = view_count
    self.video_watch_count = video_watch_count
    self.subscriber_count = subscriber_count
    self.last_web_access = last_web_access
    self.favorite_count = favorite_count

    atom.AtomBase.__init__(self, extension_elements=extension_elements,
                           extension_attributes=extension_attributes, text=text)


class Status(atom.AtomBase):
  """The YouTube Status element"""
  _tag = 'status'
  _namespace = YOUTUBE_NAMESPACE


class Position(atom.AtomBase):
  """The YouTube Position element. The position in a playlist feed."""
  _tag = 'position'
  _namespace = YOUTUBE_NAMESPACE  


class Racy(atom.AtomBase):
  """The YouTube Racy element."""
  _tag = 'racy'
  _namespace = YOUTUBE_NAMESPACE  

class Description(atom.AtomBase):
  """The YouTube Description element."""
  _tag = 'description'
  _namespace = YOUTUBE_NAMESPACE


class Private(atom.AtomBase):
  """The YouTube Private element."""
  _tag = 'private'
  _namespace = YOUTUBE_NAMESPACE


class NoEmbed(atom.AtomBase):
  """The YouTube VideoShare element. Whether a video can be embedded or not."""
  _tag = 'noembed'
  _namespace = YOUTUBE_NAMESPACE  


class Comments(atom.AtomBase):
  """The GData Comments element"""
  _tag = 'comments'
  _namespace = gdata.GDATA_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link',
                                                        [gdata.FeedLink])

  def __init__(self, feed_link=None, extension_elements=None,
               extension_attributes=None, text=None):

    self.feed_link = feed_link
    atom.AtomBase.__init__(self, extension_elements=extension_elements,
                           extension_attributes=extension_attributes, text=text)


class Rating(atom.AtomBase):
  """The GData Rating element"""
  _tag = 'rating'
  _namespace = gdata.GDATA_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['min'] = 'min'
  _attributes['max'] = 'max'
  _attributes['numRaters'] = 'num_raters'
  _attributes['average'] = 'average'

  def __init__(self, min=None, max=None,
               num_raters=None, average=None, extension_elements=None,
               extension_attributes=None, text=None):

    self.min = min
    self.max = max
    self.num_raters = num_raters
    self.average = average

    atom.AtomBase.__init__(self, extension_elements=extension_elements,
                           extension_attributes=extension_attributes, text=text)


class YouTubePlaylistVideoEntry(gdata.GDataEntry):
  """Represents a YouTubeVideoEntry on a YouTubePlaylist."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link',
                                                        [gdata.FeedLink])
  _children['{%s}description' % YOUTUBE_NAMESPACE] = ('description',
                                                       Description)
  _children['{%s}rating' % gdata.GDATA_NAMESPACE] = ('rating', Rating)
  _children['{%s}comments' % gdata.GDATA_NAMESPACE] = ('comments', Comments)
  _children['{%s}statistics' % YOUTUBE_NAMESPACE] = ('statistics', Statistics)
  _children['{%s}location' % YOUTUBE_NAMESPACE] = ('location', Location)
  _children['{%s}position' % YOUTUBE_NAMESPACE] = ('position', Position)
  _children['{%s}group' % gdata.media.MEDIA_NAMESPACE] = ('media', Media.Group)

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, title=None,
               updated=None, feed_link=None, description=None,
               rating=None, comments=None, statistics=None,
               location=None, position=None, media=None,
               extension_elements=None, extension_attributes=None):

    self.feed_link = feed_link
    self.description = description
    self.rating = rating
    self.comments = comments
    self.statistics = statistics
    self.location = location
    self.position = position
    self.media = media

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id,
                              link=link, published=published, title=title,
                              updated=updated,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes)


class YouTubeVideoCommentEntry(gdata.GDataEntry):
  """Represents a comment on YouTube."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()


class YouTubeSubscriptionEntry(gdata.GDataEntry):
  """Represents a subscription entry on YouTube."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}username' % YOUTUBE_NAMESPACE] = ('username', Username)
  _children['{%s}queryString' % YOUTUBE_NAMESPACE] = (
      'query_string', QueryString)
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link',
                                                        [gdata.FeedLink])

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, title=None,
               updated=None, username=None, query_string=None, feed_link=None,
               extension_elements=None, extension_attributes=None):

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id, link=link,
                              published=published, title=title, updated=updated)

    self.username = username
    self.query_string = query_string
    self.feed_link = feed_link


  def GetSubscriptionType(self):
    """Retrieve the type of this subscription.

    Returns:
      A string that is either 'channel, 'query' or 'favorites'
    """
    for category in self.category:
      if category.scheme == YOUTUBE_SUBSCRIPTION_TYPE_SCHEME:
        return category.term


class YouTubeVideoResponseEntry(gdata.GDataEntry):
  """Represents a video response. """
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}rating' % gdata.GDATA_NAMESPACE] = ('rating', Rating)
  _children['{%s}noembed' % YOUTUBE_NAMESPACE] = ('noembed', NoEmbed)
  _children['{%s}statistics' % YOUTUBE_NAMESPACE] = ('statistics', Statistics)
  _children['{%s}racy' % YOUTUBE_NAMESPACE] = ('racy', Racy)
  _children['{%s}group' % gdata.media.MEDIA_NAMESPACE] = ('media', Media.Group)

  def __init__(self, author=None, category=None, content=None, atom_id=None,
               link=None, published=None, title=None, updated=None, rating=None,
               noembed=None, statistics=None, racy=None, media=None,
               extension_elements=None, extension_attributes=None):

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id, link=link,
                              published=published, title=title, updated=updated)

    self.rating = rating
    self.noembed = noembed
    self.statistics = statistics
    self.racy = racy
    self.media = media or Media.Group()


class YouTubeContactEntry(gdata.GDataEntry):
  """Represents a contact entry."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}username' % YOUTUBE_NAMESPACE] = ('username', Username)
  _children['{%s}status' % YOUTUBE_NAMESPACE] = ('status', Status)


  def __init__(self, author=None, category=None, content=None, atom_id=None,
               link=None, published=None, title=None, updated=None,
               username=None, status=None, extension_elements=None, 
               extension_attributes=None, text=None):

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id, link=link,
                              published=published, title=title, updated=updated)

    self.username = username
    self.status = status


class YouTubeVideoEntry(gdata.GDataEntry):
  """Represents a video on YouTube."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}rating' % gdata.GDATA_NAMESPACE] = ('rating', Rating)
  _children['{%s}comments' % gdata.GDATA_NAMESPACE] = ('comments', Comments)
  _children['{%s}noembed' % YOUTUBE_NAMESPACE] = ('noembed', NoEmbed)
  _children['{%s}statistics' % YOUTUBE_NAMESPACE] = ('statistics', Statistics)
  _children['{%s}recorded' % YOUTUBE_NAMESPACE] = ('recorded', Recorded)
  _children['{%s}racy' % YOUTUBE_NAMESPACE] = ('racy', Racy)
  _children['{%s}group' % gdata.media.MEDIA_NAMESPACE] = ('media', Media.Group)
  _children['{%s}where' % gdata.geo.GEORSS_NAMESPACE] = ('geo', Geo.Where)

  def __init__(self, author=None, category=None, content=None, atom_id=None,
               link=None, published=None, title=None, updated=None, rating=None,
               noembed=None, statistics=None, racy=None, media=None, geo=None,
               recorded=None, comments=None, extension_elements=None, 
               extension_attributes=None):

    self.rating = rating
    self.noembed = noembed
    self.statistics = statistics
    self.racy = racy
    self.comments = comments
    self.media = media or Media.Group()
    self.geo = geo
    self.recorded = recorded

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id, link=link,
                              published=published, title=title, updated=updated,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes)

  def GetSwfUrl(self):
    """Return the URL for the embeddable Video

      Returns:
          URL of the embeddable video
    """
    if self.media.content:
      for content in self.media.content:
        if content.extension_attributes[YOUTUBE_FORMAT] == '5':
          return content.url
    else:
      return None

  def AddDeveloperTags(self, developer_tags):
    """Add a developer tag for this entry.

    Developer tags can only be set during the initial upload.

    Arguments:
      developer_tags: A list of developer tags as strings.

    Returns:
      A list of all developer tags for this video entry.
    """
    for tag_text in developer_tags:
      self.media.category.append(gdata.media.Category(
          text=tag_text, label=tag_text, scheme=YOUTUBE_DEVELOPER_TAG_SCHEME))

    return self.GetDeveloperTags()

  def GetDeveloperTags(self):
    """Retrieve developer tags for this video entry."""
    developer_tags = []
    for category in self.media.category:
      if category.scheme == YOUTUBE_DEVELOPER_TAG_SCHEME:
        developer_tags.append(category)
    if len(developer_tags) > 0:
      return developer_tags

  def GetYouTubeCategoryAsString(self):
    """Convenience method to return the YouTube category as string.

    YouTubeVideoEntries can contain multiple Category objects with differing 
        schemes. This method returns only the category with the correct
        scheme, ignoring developer tags.
    """
    for category in self.media.category:
      if category.scheme != YOUTUBE_DEVELOPER_TAG_SCHEME:
        return category.text

class YouTubeUserEntry(gdata.GDataEntry):
  """Represents a user on YouTube."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}username' % YOUTUBE_NAMESPACE] = ('username', Username)
  _children['{%s}firstName' % YOUTUBE_NAMESPACE] = ('first_name', FirstName)
  _children['{%s}lastName' % YOUTUBE_NAMESPACE] = ('last_name', LastName)
  _children['{%s}age' % YOUTUBE_NAMESPACE] = ('age', Age)
  _children['{%s}books' % YOUTUBE_NAMESPACE] = ('books', Books)
  _children['{%s}gender' % YOUTUBE_NAMESPACE] = ('gender', Gender)
  _children['{%s}company' % YOUTUBE_NAMESPACE] = ('company', Company)
  _children['{%s}description' % YOUTUBE_NAMESPACE] = ('description',
                                                       Description)
  _children['{%s}hobbies' % YOUTUBE_NAMESPACE] = ('hobbies', Hobbies)
  _children['{%s}hometown' % YOUTUBE_NAMESPACE] = ('hometown', Hometown)
  _children['{%s}location' % YOUTUBE_NAMESPACE] = ('location', Location)
  _children['{%s}movies' % YOUTUBE_NAMESPACE] = ('movies', Movies)
  _children['{%s}music' % YOUTUBE_NAMESPACE] = ('music', Music)
  _children['{%s}occupation' % YOUTUBE_NAMESPACE] = ('occupation', Occupation)
  _children['{%s}school' % YOUTUBE_NAMESPACE] = ('school', School)
  _children['{%s}relationship' % YOUTUBE_NAMESPACE] = ('relationship',
                                                        Relationship)
  _children['{%s}statistics' % YOUTUBE_NAMESPACE] = ('statistics', Statistics)
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link',
                                                        [gdata.FeedLink])
  _children['{%s}thumbnail' % gdata.media.MEDIA_NAMESPACE] = ('thumbnail',
                                                               Media.Thumbnail)

  def __init__(self, author=None, category=None, content=None, atom_id=None,
               link=None, published=None, title=None, updated=None,
               username=None, first_name=None, last_name=None, age=None,
               books=None, gender=None, company=None, description=None,
               hobbies=None, hometown=None, location=None, movies=None,
               music=None, occupation=None, school=None, relationship=None,
               statistics=None, feed_link=None, extension_elements=None,
               extension_attributes=None, text=None):

    self.username = username
    self.first_name = first_name
    self.last_name = last_name
    self.age = age
    self.books = books
    self.gender = gender
    self.company = company
    self.description = description
    self.hobbies = hobbies
    self.hometown = hometown
    self.location = location
    self.movies = movies
    self.music = music
    self.occupation = occupation
    self.school = school
    self.relationship = relationship
    self.statistics = statistics
    self.feed_link = feed_link

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id,
                              link=link, published=published,
                              title=title, updated=updated,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes,
                              text=text)


class YouTubeVideoFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a video feed on YouTube."""
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [YouTubeVideoEntry])

class YouTubePlaylistEntry(gdata.GDataEntry):
  """Represents a playlist in YouTube."""
  _tag = gdata.GDataEntry._tag
  _namespace = gdata.GDataEntry._namespace
  _children = gdata.GDataEntry._children.copy()
  _attributes = gdata.GDataEntry._attributes.copy()
  _children['{%s}description' % YOUTUBE_NAMESPACE] = ('description',
                                                       Description)
  _children['{%s}private' % YOUTUBE_NAMESPACE] = ('private',
                                                  Private)
  _children['{%s}feedLink' % gdata.GDATA_NAMESPACE] = ('feed_link',
                                                        [gdata.FeedLink])

  def __init__(self, author=None, category=None, content=None,
               atom_id=None, link=None, published=None, title=None,
               updated=None, private=None, feed_link=None,
               description=None, extension_elements=None,
               extension_attributes=None):

    self.description = description
    self.private = private
    self.feed_link = feed_link

    gdata.GDataEntry.__init__(self, author=author, category=category,
                              content=content, atom_id=atom_id,
                              link=link, published=published, title=title, 
                              updated=updated,
                              extension_elements=extension_elements,
                              extension_attributes=extension_attributes)



class YouTubePlaylistFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a feed of a user's playlists """
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [YouTubePlaylistEntry])


class YouTubePlaylistVideoFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a feed of video entry on a playlist."""
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [YouTubePlaylistVideoEntry])


class YouTubeContactFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a feed of a users contacts."""
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [YouTubeContactEntry])


class YouTubeSubscriptionFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a feed of a users subscriptions."""
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [YouTubeSubscriptionEntry])


class YouTubeVideoCommentFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a feed of comments for a video."""
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [YouTubeVideoCommentEntry])


class YouTubeVideoResponseFeed(gdata.GDataFeed, gdata.LinkFinder):
  """Represents a feed of video responses."""
  _tag = gdata.GDataFeed._tag
  _namespace = gdata.GDataFeed._namespace
  _children = gdata.GDataFeed._children.copy()
  _attributes = gdata.GDataFeed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry',
                                                  [YouTubeVideoResponseEntry])


def YouTubeVideoFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoFeed, xml_string)


def YouTubeVideoEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoEntry, xml_string)


def YouTubeContactFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeContactFeed, xml_string)


def YouTubeContactEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeContactEntry, xml_string)


def YouTubeVideoCommentFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoCommentFeed, xml_string)


def YouTubeVideoCommentEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoCommentEntry, xml_string)


def YouTubeUserFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoFeed, xml_string)


def YouTubeUserEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeUserEntry, xml_string)


def YouTubePlaylistFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubePlaylistFeed, xml_string)


def YouTubePlaylistVideoFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubePlaylistVideoFeed, xml_string)


def YouTubePlaylistEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubePlaylistEntry, xml_string)


def YouTubePlaylistVideoEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubePlaylistVideoEntry, xml_string)


def YouTubeSubscriptionFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeSubscriptionFeed, xml_string)


def YouTubeSubscriptionEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeSubscriptionEntry, xml_string)


def YouTubeVideoResponseFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoResponseFeed, xml_string)


def YouTubeVideoResponseEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(YouTubeVideoResponseEntry, xml_string)
