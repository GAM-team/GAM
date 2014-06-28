#!/usr/bin/env python
#
# Copyright 2009 Google Inc.
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


# This module is used for version 2 of the Google Data APIs.


"""Provides classes and constants for XML in the Google Project Hosting API.

Canonical documentation for the raw XML which these classes represent can be
found here: http://code.google.com/p/support/wiki/IssueTrackerAPI
"""


__author__ = 'jlapenna@google.com (Joe LaPenna)'

import atom.core
import gdata.data


ISSUES_TEMPLATE = '{http://schemas.google.com/projecthosting/issues/2009}%s'


ISSUES_FULL_FEED = '/feeds/issues/p/%s/issues/full'
COMMENTS_FULL_FEED = '/feeds/issues/p/%s/issues/%s/comments/full'


class Uri(atom.core.XmlElement):
  """The issues:uri element."""
  _qname = ISSUES_TEMPLATE % 'uri'


class Username(atom.core.XmlElement):
  """The issues:username element."""
  _qname = ISSUES_TEMPLATE % 'username'


class Cc(atom.core.XmlElement):
  """The issues:cc element."""
  _qname = ISSUES_TEMPLATE % 'cc'
  uri = Uri
  username = Username


class Label(atom.core.XmlElement):
  """The issues:label element."""
  _qname = ISSUES_TEMPLATE % 'label'


class Owner(atom.core.XmlElement):
  """The issues:owner element."""
  _qname = ISSUES_TEMPLATE % 'owner'
  uri = Uri
  username = Username


class Stars(atom.core.XmlElement):
  """The issues:stars element."""
  _qname = ISSUES_TEMPLATE % 'stars'


class State(atom.core.XmlElement):
  """The issues:state element."""
  _qname = ISSUES_TEMPLATE % 'state'


class Status(atom.core.XmlElement):
  """The issues:status element."""
  _qname = ISSUES_TEMPLATE % 'status'


class Summary(atom.core.XmlElement):
  """The issues:summary element."""
  _qname = ISSUES_TEMPLATE % 'summary'


class OwnerUpdate(atom.core.XmlElement):
  """The issues:ownerUpdate element."""
  _qname = ISSUES_TEMPLATE % 'ownerUpdate'


class CcUpdate(atom.core.XmlElement):
  """The issues:ccUpdate element."""
  _qname = ISSUES_TEMPLATE % 'ccUpdate'


class Updates(atom.core.XmlElement):
  """The issues:updates element."""
  _qname = ISSUES_TEMPLATE % 'updates'
  summary = Summary
  status = Status
  ownerUpdate = OwnerUpdate
  label = [Label]
  ccUpdate = [CcUpdate]


class IssueEntry(gdata.data.GDEntry):
  """Represents the information of one issue."""
  _qname = atom.data.ATOM_TEMPLATE % 'entry'
  owner = Owner
  cc = [Cc]
  label = [Label]
  stars = Stars
  state = State
  status = Status


class IssuesFeed(gdata.data.GDFeed):
  """An Atom feed listing a project's issues."""
  entry = [IssueEntry]


class CommentEntry(gdata.data.GDEntry):
  """An entry detailing one comment on an issue."""
  _qname = atom.data.ATOM_TEMPLATE % 'entry'
  updates = Updates


class CommentsFeed(gdata.data.GDFeed):
  """An Atom feed listing a project's issue's comments."""
  entry = [CommentEntry]
