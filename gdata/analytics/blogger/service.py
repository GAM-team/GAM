#!/usr/bin/python
#
# Copyright (C) 2007 Google Inc.
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

"""Classes to interact with the Blogger server."""

__author__ = 'api.jscudder (Jeffrey Scudder)'

import gdata.service
import gdata.blogger


class BloggerService(gdata.service.GDataService):

  def __init__(self, email=None, password=None, source=None,
               server='www.blogger.com', **kwargs):
    """Creates a client for the Blogger service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'www.blogger.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='blogger', source=source,
        server=server, **kwargs)

  def GetBlogFeed(self, uri=None):
    """Retrieve a list of the blogs to which the current user may manage."""
    if not uri:
      uri = '/feeds/default/blogs'
    return self.Get(uri, converter=gdata.blogger.BlogFeedFromString)

  def GetBlogCommentFeed(self, blog_id=None, uri=None):
    """Retrieve a list of the comments for this blog."""
    if blog_id:
      uri = '/feeds/%s/comments/default' % blog_id
    return self.Get(uri, converter=gdata.blogger.CommentFeedFromString)

  def GetBlogPostFeed(self, blog_id=None, uri=None):
    if blog_id:
      uri = '/feeds/%s/posts/default' % blog_id
    return self.Get(uri, converter=gdata.blogger.BlogPostFeedFromString)

  def GetPostCommentFeed(self, blog_id=None, post_id=None, uri=None):
    """Retrieve a list of the comments for this particular blog post."""
    if blog_id and post_id:
      uri = '/feeds/%s/%s/comments/default' % (blog_id, post_id)
    return self.Get(uri, converter=gdata.blogger.CommentFeedFromString)

  def AddPost(self, entry, blog_id=None, uri=None):
    if blog_id:
      uri = '/feeds/%s/posts/default' % blog_id
    return self.Post(entry, uri, 
                     converter=gdata.blogger.BlogPostEntryFromString)

  def UpdatePost(self, entry, uri=None):
    if not uri:
      uri = entry.GetEditLink().href
    return self.Put(entry, uri, 
                    converter=gdata.blogger.BlogPostEntryFromString)

  def DeletePost(self, entry=None, uri=None):
    if not uri:
      uri = entry.GetEditLink().href
    return self.Delete(uri)

  def AddComment(self, comment_entry, blog_id=None, post_id=None, uri=None):
    """Adds a new comment to the specified blog post."""
    if blog_id and post_id:
      uri = '/feeds/%s/%s/comments/default' % (blog_id, post_id)
    return self.Post(comment_entry, uri, 
                     converter=gdata.blogger.CommentEntryFromString)

  def DeleteComment(self, entry=None, uri=None):
    if not uri:
      uri = entry.GetEditLink().href
    return self.Delete(uri)
    

class BlogQuery(gdata.service.Query):

  def __init__(self, feed=None, params=None, categories=None, blog_id=None):
    """Constructs a query object for the list of a user's Blogger blogs.
    
    Args:
      feed: str (optional) The beginning of the URL to be queried. If the
          feed is not set, and there is no blog_id passed in, the default
          value is used ('/feeds/default/blogs').
      params: dict (optional)
      categories: list (optional)
      blog_id: str (optional)
    """
    if not feed and blog_id:
      feed = '/feeds/default/blogs/%s' % blog_id
    elif not feed:
      feed = '/feeds/default/blogs'
    gdata.service.Query.__init__(self, feed=feed, params=params, 
        categories=categories)


class BlogPostQuery(gdata.service.Query):

  def __init__(self, feed=None, params=None, categories=None, blog_id=None, 
      post_id=None):
    if not feed and blog_id and post_id:
      feed = '/feeds/%s/posts/default/%s' % (blog_id, post_id)
    elif not feed and blog_id:
      feed = '/feeds/%s/posts/default' % blog_id
    gdata.service.Query.__init__(self, feed=feed, params=params,
        categories=categories)


class BlogCommentQuery(gdata.service.Query):

  def __init__(self, feed=None, params=None, categories=None, blog_id=None, 
      post_id=None, comment_id=None):
    if not feed and blog_id and comment_id:
      feed = '/feeds/%s/comments/default/%s' % (blog_id, comment_id)
    elif not feed and blog_id and post_id:
      feed = '/feeds/%s/%s/comments/default' % (blog_id, post_id)
    elif not feed and blog_id:
      feed = '/feeds/%s/comments/default' % blog_id
    gdata.service.Query.__init__(self, feed=feed, params=params,
        categories=categories)
