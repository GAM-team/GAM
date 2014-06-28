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


"""Contains a client to communicate with the Blogger servers.

For documentation on the Blogger API, see:
http://code.google.com/apis/blogger/
"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import gdata.client
import gdata.gauth
import gdata.blogger.data
import atom.data
import atom.http_core


# List user's blogs, takes a user ID, or 'default'.
BLOGS_URL = 'http://www.blogger.com/feeds/%s/blogs'
# Takes a blog ID.
BLOG_POST_URL = 'http://www.blogger.com/feeds/%s/posts/default'
# Takes a blog ID.
BLOG_PAGE_URL = 'http://www.blogger.com/feeds/%s/pages/default'
# Takes a blog ID and post ID.
BLOG_POST_COMMENTS_URL = 'http://www.blogger.com/feeds/%s/%s/comments/default'
# Takes a blog ID.
BLOG_COMMENTS_URL = 'http://www.blogger.com/feeds/%s/comments/default'
# Takes a blog ID.
BLOG_ARCHIVE_URL = 'http://www.blogger.com/feeds/%s/archive/full'


class BloggerClient(gdata.client.GDClient):
  api_version = '2'
  auth_service = 'blogger'
  auth_scopes = gdata.gauth.AUTH_SCOPES['blogger']

  def get_blogs(self, user_id='default', auth_token=None,
                desired_class=gdata.blogger.data.BlogFeed, **kwargs):
    return self.get_feed(BLOGS_URL % user_id, auth_token=auth_token,
                         desired_class=desired_class, **kwargs)

  GetBlogs = get_blogs

  def get_posts(self, blog_id, auth_token=None,
                desired_class=gdata.blogger.data.BlogPostFeed, query=None,
                **kwargs):
    return self.get_feed(BLOG_POST_URL % blog_id, auth_token=auth_token,
                         desired_class=desired_class, query=query, **kwargs)

  GetPosts = get_posts

  def get_pages(self, blog_id, auth_token=None,
                desired_class=gdata.blogger.data.BlogPageFeed, query=None,
                **kwargs):
    return self.get_feed(BLOG_PAGE_URL % blog_id, auth_token=auth_token,
                         desired_class=desired_class, query=query, **kwargs)

  GetPages = get_pages

  def get_post_comments(self, blog_id, post_id,  auth_token=None,
                        desired_class=gdata.blogger.data.CommentFeed,
                        query=None, **kwargs):
    return self.get_feed(BLOG_POST_COMMENTS_URL % (blog_id, post_id),
                         auth_token=auth_token, desired_class=desired_class,
                         query=query, **kwargs)

  GetPostComments = get_post_comments

  def get_blog_comments(self, blog_id, auth_token=None,
                        desired_class=gdata.blogger.data.CommentFeed,
                        query=None, **kwargs):
    return self.get_feed(BLOG_COMMENTS_URL % blog_id, auth_token=auth_token,
                         desired_class=desired_class, query=query, **kwargs)

  GetBlogComments = get_blog_comments

  def get_blog_archive(self, blog_id, auth_token=None, **kwargs):
    return self.get_feed(BLOG_ARCHIVE_URL % blog_id, auth_token=auth_token,
                         **kwargs)

  GetBlogArchive = get_blog_archive

  def add_post(self, blog_id, title, body, labels=None, draft=False,
               auth_token=None, title_type='text', body_type='html', **kwargs):
    # Construct an atom Entry for the blog post to be sent to the server.
    new_entry = gdata.blogger.data.BlogPost(
        title=atom.data.Title(text=title, type=title_type),
        content=atom.data.Content(text=body, type=body_type))
    if labels:
      for label in labels:
        new_entry.add_label(label)
    if draft:
      new_entry.control = atom.data.Control(draft=atom.data.Draft(text='yes'))
    return self.post(new_entry, BLOG_POST_URL % blog_id, auth_token=auth_token, **kwargs)

  AddPost = add_post

  def add_page(self, blog_id, title, body, draft=False, auth_token=None,
               title_type='text', body_type='html', **kwargs):
    new_entry = gdata.blogger.data.BlogPage(
        title=atom.data.Title(text=title, type=title_type),
        content=atom.data.Content(text=body, type=body_type))
    if draft:
      new_entry.control = atom.data.Control(draft=atom.data.Draft(text='yes'))
    return self.post(new_entry, BLOG_PAGE_URL % blog_id, auth_token=auth_token, **kwargs)

  AddPage = add_page

  def add_comment(self, blog_id, post_id, body, auth_token=None,
                  title_type='text', body_type='html', **kwargs):
    new_entry = gdata.blogger.data.Comment(
        content=atom.data.Content(text=body, type=body_type))
    return self.post(new_entry, BLOG_POST_COMMENTS_URL % (blog_id, post_id),
                     auth_token=auth_token, **kwargs)

  AddComment = add_comment

  def update(self, entry, auth_token=None, **kwargs):
    # The Blogger API does not currently support ETags, so for now remove
    # the ETag before performing an update.
    old_etag = entry.etag
    entry.etag = None
    response = gdata.client.GDClient.update(self, entry,
                                            auth_token=auth_token, **kwargs)
    entry.etag = old_etag
    return response

  Update = update

  def delete(self, entry_or_uri, auth_token=None, **kwargs):
    if isinstance(entry_or_uri, (str, unicode, atom.http_core.Uri)):
      return gdata.client.GDClient.delete(self, entry_or_uri,
                                          auth_token=auth_token, **kwargs)
    # The Blogger API does not currently support ETags, so for now remove
    # the ETag before performing a delete.
    old_etag = entry_or_uri.etag
    entry_or_uri.etag = None
    response = gdata.client.GDClient.delete(self, entry_or_uri,
                                            auth_token=auth_token, **kwargs)
    # TODO: if GDClient.delete raises and exception, the entry's etag may be
    # left as None. Should revisit this logic.
    entry_or_uri.etag = old_etag
    return response

  Delete = delete


class Query(gdata.client.Query):

  def __init__(self, order_by=None, **kwargs):
    gdata.client.Query.__init__(self, **kwargs)
    self.order_by = order_by

  def modify_request(self, http_request):
    gdata.client._add_query_param('orderby', self.order_by, http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request
