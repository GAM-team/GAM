#!/usr/bin/env python


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


"""Fill in this module with configuration data to use in tests.

See comments in the source code for explanations of the settings.
"""

import os


# To actually run the tests which use this configuration information you must
# change RUN_LIVE_TESTS to True.
RUN_LIVE_TESTS = False


# If set to True, the client will save responses from the server and reuse
# them in future runs of the test.
CACHE_RESPONSES = True

# If set to True, the client will make HTTP requests to the server regardless
# of a cache file. If True, caches from previous sessions will be deleted.
# If False (the default) cached sessions will be reused if they exist.
CLEAR_CACHE = True


GOOGLE_ACCOUNT_EMAIL = '<your email>'
GOOGLE_ACCOUNT_PASSWORD = '<your password>'
# For example, the TEST_FILES_DIR might be
# '/home/username/svn/gdata-python-client/tests'
TEST_FILES_DIR = '<location of the tests directory>'


class NoAuthConfig(object):
  auth_token = False


class TestConfig(object):
  service = None
  auth_token = None

  def email(cls):
    """Provides email to log into the test account for this service.
  
    By default uses GOOGLE_ACCOUNT_EMAIL, so overwrite this function if you
    have a service-specific test account.
    """
    return GOOGLE_ACCOUNT_EMAIL

  email = classmethod(email)

  def password(cls):
    """Provides password to log into the test account for this service.
  
    By default uses GOOGLE_ACCOUNT_PASSWORD, so overwrite this function if
    you have a service-specific test account.
    """
    return GOOGLE_ACCOUNT_PASSWORD

  password = classmethod(password)


class BloggerConfig(TestConfig):
  service = 'blogger'
  title = 'A Test Post'
  content = 'This is a <b>test</b>.'
  blog_id = '<your test blog\'s id>'


class ContactsConfig(TestConfig):
  service = 'cp'

  def get_image_location(cls):
    return os.path.join(TEST_FILES_DIR, 'files', 'testimage.jpg')

  get_image_location = classmethod(get_image_location)

class MapsConfig(TestConfig):
  service = 'local'
  map_title = 'Some test map'
  map_summary = 'A test description'
