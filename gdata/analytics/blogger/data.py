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


"""Data model classes for parsing and generating XML for the Blogger API."""


__author__ = 'j.s@google.com (Jeff Scudder)'


import re
import urlparse
import atom.core
import gdata.data


LABEL_SCHEME = 'http://www.blogger.com/atom/ns#'
THR_TEMPLATE = '{http://purl.org/syndication/thread/1.0}%s'

BLOG_NAME_PATTERN = re.compile('(http://)(\w*)')
BLOG_ID_PATTERN = re.compile('(tag:blogger.com,1999:blog-)(\w*)')
BLOG_ID2_PATTERN = re.compile('tag:blogger.com,1999:user-(\d+)\.blog-(\d+)')
POST_ID_PATTERN = re.compile(
    '(tag:blogger.com,1999:blog-)(\w*)(.post-)(\w*)')
PAGE_ID_PATTERN = re.compile(
    '(tag:blogger.com,1999:blog-)(\w*)(.page-)(\w*)')
COMMENT_ID_PATTERN = re.compile('.*-(\w*)$')


class BloggerEntry(gdata.data.GDEntry):
  """Adds convenience methods inherited by all Blogger entries."""

  def get_blog_id(self):
    """Extracts the Blogger id of this blog.

    This method is useful when contructing URLs by hand. The blog id is
    often used in blogger operation URLs. This should not be confused with
    the id member of a BloggerBlog. The id element is the Atom id XML element.
    The blog id which this method returns is a part of the Atom id.

    Returns:
      The blog's unique id as a string.
    """
    if self.id.text:
      match = BLOG_ID_PATTERN.match(self.id.text)
      if match:
        return match.group(2)
      else:
        return BLOG_ID2_PATTERN.match(self.id.text).group(2)
    return None

  GetBlogId = get_blog_id

  def get_blog_name(self):
    """Finds the name of this blog as used in the 'alternate' URL.

    An alternate URL is in the form 'http://blogName.blogspot.com/'. For an
    entry representing the above example, this method would return 'blogName'.

    Returns:
      The blog's URL name component as a string.
    """
    for link in self.link:
      if link.rel == 'alternate':
        return urlparse.urlparse(link.href)[1].split(".", 1)[0]
    return None

  GetBlogName = get_blog_name


class Blog(BloggerEntry):
  """Represents a blog which belongs to the user."""


class BlogFeed(gdata.data.GDFeed):
  entry = [Blog]


class BlogPost(BloggerEntry):
  """Represents a single post on a blog."""

  def add_label(self, label):
    """Adds a label to the blog post.

    The label is represented by an Atom category element, so this method
    is shorthand for appending a new atom.Category object.

    Args:
      label: str
    """
    self.category.append(atom.data.Category(scheme=LABEL_SCHEME, term=label))

  AddLabel = add_label

  def get_post_id(self):
    """Extracts the postID string from the entry's Atom id.

    Returns: A string of digits which identify this post within the blog.
    """
    if self.id.text:
      return POST_ID_PATTERN.match(self.id.text).group(4)
    return None

  GetPostId = get_post_id


class BlogPostFeed(gdata.data.GDFeed):
  entry = [BlogPost]


class BlogPage(BloggerEntry):
  """Represents a single page on a blog."""

  def get_page_id(self):
    """Extracts the pageID string from entry's Atom id.

    Returns: A string of digits which identify this post within the blog.
    """
    if self.id.text:
      return PAGE_ID_PATTERN.match(self.id.text).group(4)
    return None

  GetPageId = get_page_id


class BlogPageFeed(gdata.data.GDFeed):
  entry = [BlogPage]


class InReplyTo(atom.core.XmlElement):
  _qname = THR_TEMPLATE % 'in-reply-to'
  href = 'href'
  ref = 'ref'
  source = 'source'
  type = 'type'


class Comment(BloggerEntry):
  """Blog post comment entry in a feed listing comments on a post or blog."""
  in_reply_to = InReplyTo

  def get_comment_id(self):
    """Extracts the commentID string from the entry's Atom id.

    Returns: A string of digits which identify this post within the blog.
    """
    if self.id.text:
      return COMMENT_ID_PATTERN.match(self.id.text).group(1)
    return None

  GetCommentId = get_comment_id


class CommentFeed(gdata.data.GDFeed):
  entry = [Comment]
