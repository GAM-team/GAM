#!/usr/bin/env python
#
# Copyright (C) 2010 Google Inc.
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


"""Provides a base class to represent property elements in feeds.

This module is used for version 2 of the Google Data APIs. The primary class
in this module is AppsProperty.
"""


__author__ = 'Vic Fryzel <vicfryzel@google.com>'


import atom.core
import gdata.apps


class AppsProperty(atom.core.XmlElement):
  """Represents an <apps:property> element in a feed."""
  _qname = gdata.apps.APPS_TEMPLATE % 'property'
  name = 'name'
  value = 'value'
