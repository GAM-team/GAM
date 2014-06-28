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

"""Contains the data classes of the Google Notebook Data API"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import atom.data
import gdata.data
import gdata.opensearch.data


NB_TEMPLATE = '{http://schemas.google.com/notes/2008/}%s'


class ComesAfter(atom.core.XmlElement):
  """Preceding element."""
  _qname = NB_TEMPLATE % 'comesAfter'
  id = 'id'


class NoteEntry(gdata.data.GDEntry):
  """Describes a note entry in the feed of a user's notebook."""


class NotebookFeed(gdata.data.GDFeed):
  """Describes a notebook feed."""
  entry = [NoteEntry]


class NotebookListEntry(gdata.data.GDEntry):
  """Describes a note list entry in the feed of a user's list of public notebooks."""


class NotebookListFeed(gdata.data.GDFeed):
  """Describes a notebook list feed."""
  entry = [NotebookListEntry]


