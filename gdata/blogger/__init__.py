#!/usr/bin/python
#
# Copyright (C) 2007, 2008 Google Inc.
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


"""Contains extensions to Atom objects used with Blogger."""


__author__ = 'api.jscudder (Jeffrey Scudder)'


import atom
import gdata
import re


LABEL_SCHEME = 'http://www.blogger.com/atom/ns#'
THR_NAMESPACE = 'http://purl.org/syndication/thread/1.0'


class BloggerEntry(gdata.GDataEntry):
  """Adds convenience methods inherited by all Blogger entries."""

  blog_name_pattern = re.compile('(http://)(\w*)')
  blog_id_pattern = re.compile('(tag:blogger.com,1999:blog-)(\w*)')
  blog_id2_pattern = re.compile('tag:blogger.com,1999:user-(\d+)\.blog-(\d+)')

  def GetBlogId(self):
    """Extracts the Blogger id of this blog.
    This method is useful when contructing URLs by hand. The blog id is
    often used in blogger operation URLs. This should not be confused with
    the id member of a BloggerBlog. The id element is the Atom id XML element.
    The blog id which this method returns is a part of the Atom id.

    Returns:
      The blog's unique id as a string.
    """
    if self.id.text:
      match = self.blog_id_pattern.match(self.id.text)
      if match:
        return match.group(2)
      else:
        return self.blog_id2_pattern.match(self.id.text).group(2)
    return None

  def GetBlogName(self):
    """Finds the name of this blog as used in the 'alternate' URL.
    An alternate URL is in the form 'http://blogName.blogspot.com/'. For an
    entry representing the above example, this method would return 'blogName'.

    Returns:
      The blog's URL name component as a string.
    """
    for link in self.link:
      if link.rel == 'alternate':
        return self.blog_name_pattern.match(link.href).group(2)
    return None


class BlogEntry(BloggerEntry):
  """Describes a blog entry in the feed listing a user's blogs."""


def BlogEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(BlogEntry, xml_string)


class BlogFeed(gdata.GDataFeed):
  """Describes a feed of a user's blogs."""

  _children = gdata.GDataFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [BlogEntry])


def BlogFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(BlogFeed, xml_string)


class BlogPostEntry(BloggerEntry):
  """Describes a blog post entry in the feed of a blog's posts."""

  post_id_pattern = re.compile('(tag:blogger.com,1999:blog-)(\w*)(.post-)(\w*)')

  def AddLabel(self, label):
    """Adds a label to the blog post.

    The label is represented by an Atom category element, so this method
    is shorthand for appending a new atom.Category object.

    Args:
      label: str
    """
    self.category.append(atom.Category(scheme=LABEL_SCHEME, term=label))

  def GetPostId(self):
    """Extracts the postID string from the entry's Atom id.

    Returns: A string of digits which identify this post within the blog.
    """
    if self.id.text:
      return self.post_id_pattern.match(self.id.text).group(4)
    return None


def BlogPostEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(BlogPostEntry, xml_string)


class BlogPostFeed(gdata.GDataFeed):
  """Describes a feed of a blog's posts."""

  _children = gdata.GDataFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [BlogPostEntry])


def BlogPostFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(BlogPostFeed, xml_string)


class InReplyTo(atom.AtomBase):
  _tag = 'in-reply-to'
  _namespace = THR_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['href'] = 'href'
  _attributes['ref'] = 'ref'
  _attributes['source'] = 'source'
  _attributes['type'] = 'type'

  def __init__(self, href=None, ref=None, source=None, type=None,
      extension_elements=None, extension_attributes=None, text=None):
    self.href = href
    self.ref = ref
    self.source = source
    self.type = type
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}
    self.text = text


def InReplyToFromString(xml_string):
  return atom.CreateClassFromXMLString(InReplyTo, xml_string)


class CommentEntry(BloggerEntry):
  """Describes a blog post comment entry in the feed of a blog post's
  comments."""

  _children = BloggerEntry._children.copy()
  _children['{%s}in-reply-to' % THR_NAMESPACE] = ('in_reply_to', InReplyTo)

  comment_id_pattern = re.compile('.*-(\w*)$')

  def __init__(self, author=None, category=None, content=None,
      contributor=None, atom_id=None, link=None, published=None, rights=None,
      source=None, summary=None, control=None, title=None, updated=None,
      in_reply_to=None, extension_elements=None, extension_attributes=None,
      text=None):
    BloggerEntry.__init__(self, author=author, category=category,
        content=content, contributor=contributor, atom_id=atom_id, link=link,
        published=published, rights=rights, source=source, summary=summary,
        control=control, title=title, updated=updated,
        extension_elements=extension_elements,
        extension_attributes=extension_attributes, text=text)
    self.in_reply_to = in_reply_to

  def GetCommentId(self):
    """Extracts the commentID string from the entry's Atom id.

    Returns: A string of digits which identify this post within the blog.
    """
    if self.id.text:
      return self.comment_id_pattern.match(self.id.text).group(1)
    return None


def CommentEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentEntry, xml_string)


class CommentFeed(gdata.GDataFeed):
  """Describes a feed of a blog post's comments."""

  _children = gdata.GDataFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [CommentEntry])


def CommentFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(CommentFeed, xml_string)


