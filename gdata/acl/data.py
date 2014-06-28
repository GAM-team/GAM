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

"""Contains the data classes of the Google Access Control List (ACL) Extension"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import atom.data
import gdata.data
import gdata.opensearch.data


GACL_TEMPLATE = '{http://schemas.google.com/acl/2007}%s'


class AclRole(atom.core.XmlElement):
  """Describes the role of an entry in an access control list."""
  _qname = GACL_TEMPLATE % 'role'
  value = 'value'


class AclScope(atom.core.XmlElement):
  """Describes the scope of an entry in an access control list."""
  _qname = GACL_TEMPLATE % 'scope'
  type = 'type'
  value = 'value'


class AclEntry(gdata.data.GDEntry):
  """Describes an entry in a feed of an access control list (ACL)."""
  scope = AclScope
  role = AclRole


class AclFeed(gdata.data.GDFeed):
  """Describes a feed of an access control list (ACL)."""
  entry = [AclEntry]


