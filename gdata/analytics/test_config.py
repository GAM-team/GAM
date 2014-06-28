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


import sys
import unittest
import getpass
import inspect
import atom.mock_http_core
import gdata.gauth


"""Loads configuration for tests which connect to Google servers.

Settings used in tests are stored in a ConfigCollection instance in this
module called options. If your test needs to get a test related setting,
use

import gdata.test_config
option_value = gdata.test_config.options.get_value('x')

The above will check the command line for an '--x' argument, and if not
found will either use the default value for 'x' or prompt the user to enter
one. 

Your test can override the value specified by the user by performing:

gdata.test_config.options.set_value('x', 'y')

If your test uses a new option which you would like to allow the user to
specify on the command line or via a prompt, you can use the register_option
method as follows:

gdata.test_config.options.register(
    'option_name', 'Prompt shown to the user', secret=False #As for password.
    'This is the description of the option, shown when help is requested.',
    'default value, provide only if you do not want the user to be prompted')
"""


class Option(object):

  def __init__(self, name, prompt, secret=False, description=None, default=None):
    self.name = name
    self.prompt = prompt
    self.secret = secret
    self.description = description
    self.default = default

  def get(self):
    value = self.default
    # Check for a command line parameter.
    for i in xrange(len(sys.argv)):
      if sys.argv[i].startswith('--%s=' % self.name):
        value = sys.argv[i].split('=')[1]
      elif sys.argv[i] == '--%s' % self.name:
        value = sys.argv[i + 1]
    # If the param was not on the command line, ask the user to input the
    # value.
    # In order for this to prompt the user, the default value for the option
    # must be None.
    if value is None:
      prompt = '%s: ' % self.prompt
      if self.secret:
        value = getpass.getpass(prompt)
      else:
        print 'You can specify this on the command line using --%s' % self.name
        value = raw_input(prompt)
    return value


class ConfigCollection(object):

  def __init__(self, options=None):
    self.options = options or {}
    self.values = {}

  def register_option(self, option):
    self.options[option.name] = option

  def register(self, *args, **kwargs):
    self.register_option(Option(*args, **kwargs))

  def get_value(self, option_name):
    if option_name in self.values:
      return self.values[option_name]
    value = self.options[option_name].get()
    if value is not None:
      self.values[option_name] = value
    return value

  def set_value(self, option_name, value):
    self.values[option_name] = value

  def render_usage(self):
    message_parts = []
    for opt_name, option in self.options.iteritems():
      message_parts.append('--%s: %s' % (opt_name, option.description))
    return '\n'.join(message_parts)


options = ConfigCollection()


# Register the default options.
options.register(
    'username',
    'Please enter the email address of your test account', 
    description=('The email address you want to sign in with. '
                 'Make sure this is a test account as these tests may edit'
                 ' or delete data.'))
options.register(
    'password',
    'Please enter the password for your test account',
    secret=True, description='The test account password.')
options.register(
    'clearcache',
    'Delete cached data? (enter true or false)',
    description=('If set to true, any temporary files which cache test'
                 ' requests and responses will be deleted.'),
    default='true')
options.register(
    'savecache',
    'Save requests and responses in a temporary file? (enter true or false)',
    description=('If set to true, requests to the server and responses will'
                 ' be saved in temporary files.'),
    default='false')
options.register(
    'runlive',
    'Run the live tests which contact the server? (enter true or false)',
    description=('If set to true, the tests will make real HTTP requests to'
                 ' the servers. This slows down test execution and may'
                 ' modify the users data, be sure to use a test account.'),
    default='true')
options.register(
    'ssl',
    'Run the live tests over SSL (enter true or false)',
    description='If set to true, all tests will be performed over HTTPS (SSL)',
    default='false')
options.register(
    'clean',
    'Clean ALL data first before and after each test (enter true or false)',
    description='If set to true, all tests will remove all data (DANGEROUS)',
    default='false')
options.register(
    'appsusername',
    'Please enter the email address of your test Apps domain account', 
    description=('The email address you want to sign in with. '
                 'Make sure this is a test account on your Apps domain as '
                 'these tests may edit or delete data.'))
options.register(
    'appspassword',
    'Please enter the password for your test Apps domain account',
    secret=True, description='The test Apps account password.')

# Other options which may be used if needed.
BLOG_ID_OPTION = Option(
    'blogid',
    'Please enter the ID of your test blog',
    description=('The blog ID for the blog which should have test posts added'
                 ' to it. Example 7682659670455539811'))
TEST_IMAGE_LOCATION_OPTION = Option(
    'imgpath',
    'Please enter the full path to a test image to upload',
    description=('This test image will be uploaded to a service which'
                 ' accepts a media file, it must be a jpeg.'))
SPREADSHEET_ID_OPTION = Option(
    'spreadsheetid',
    'Please enter the ID of a spreadsheet to use in these tests',
    description=('The spreadsheet ID for the spreadsheet which should be'
                 ' modified by theses tests.'))
APPS_DOMAIN_OPTION = Option(
    'appsdomain',
    'Please enter your Google Apps domain',
    description=('The domain the Google Apps is hosted on or leave blank'
                 ' if n/a'))
SITES_NAME_OPTION = Option(
    'sitename',
    'Please enter name of your Google Site',
    description='The webspace name of the Site found in its URL.')
PROJECT_NAME_OPTION = Option(
    'project_name',
    'Please enter the name of your project hosting project',
    description=('The name of the project which should have test issues added'
                 ' to it. Example gdata-python-client'))
ISSUE_ASSIGNEE_OPTION = Option(
    'issue_assignee',
    'Enter the email address of the target owner of the updated issue.',
    description=('The email address of the user a created issue\'s owner will '
                 ' become. Example testuser2@gmail.com'))
GA_TABLE_ID = Option(
    'table_id',
    'Enter the Table ID of the Google Analytics profile to test',
    description=('The Table ID of the Google Analytics profile to test.'
                 ' Example ga:1174'))
TARGET_USERNAME_OPTION = Option(
    'targetusername',
    'Please enter the username (without domain) of the user which will be'
    ' affected by the tests',
    description=('The username of the user to be tested'))
YT_DEVELOPER_KEY_OPTION = Option(
    'developerkey',
    'Please enter your YouTube developer key',
    description=('The YouTube developer key for your account'))
YT_CLIENT_ID_OPTION = Option(
    'clientid',
    'Please enter your YouTube client ID',
    description=('The YouTube client ID for your account'))
YT_VIDEO_ID_OPTION= Option(
    'videoid',
    'Please enter the ID of a YouTube video you uploaded',
    description=('The video ID of a YouTube video uploaded to your account'))


# Functions to inject a cachable HTTP client into a service client.
def configure_client(client, case_name, service_name, use_apps_auth=False):
  """Sets up a mock client which will reuse a saved session.

  Should be called during setUp of each unit test.

  Handles authentication to allow the GDClient to make requests which
  require an auth header.

  Args:
    client: a gdata.GDClient whose http_client member should be replaced
            with a atom.mock_http_core.MockHttpClient so that repeated
            executions can used cached responses instead of contacting
            the server.
    case_name: str The name of the test case class. Examples: 'BloggerTest',
               'ContactsTest'. Used to save a session
               for the ClientLogin auth token request, so the case_name
               should be reused if and only if the same username, password,
               and service are being used.
    service_name: str The service name as used for ClientLogin to identify
                  the Google Data API being accessed. Example: 'blogger',
                  'wise', etc.
    use_apps_auth: bool (optional) If set to True, use appsusername and
                   appspassword command-line args instead of username and
                   password respectively.
  """
  # Use a mock HTTP client which will record and replay the HTTP traffic
  # from these tests.
  client.http_client = atom.mock_http_core.MockHttpClient()
  client.http_client.cache_case_name = case_name
  # Getting the auth token only needs to be done once in the course of test
  # runs.
  auth_token_key = '%s_auth_token' % service_name
  if (auth_token_key not in options.values
      and options.get_value('runlive') == 'true'):
    client.http_client.cache_test_name = 'client_login'
    cache_name = client.http_client.get_cache_file_name()
    if options.get_value('clearcache') == 'true':
      client.http_client.delete_session(cache_name)
    client.http_client.use_cached_session(cache_name)
    if not use_apps_auth:
      username = options.get_value('username')
      password = options.get_value('password')
    else:
      username = options.get_value('appsusername')
      password = options.get_value('appspassword')
    auth_token = client.client_login(username, password, case_name,
                                     service=service_name)
    options.values[auth_token_key] = gdata.gauth.token_to_blob(auth_token)
    if client.alt_auth_service is not None:
      options.values[client.alt_auth_service] = gdata.gauth.token_to_blob(
          client.alt_auth_token)
    client.http_client.close_session()
  # Allow a config auth_token of False to prevent the client's auth header
  # from being modified.
  if auth_token_key in options.values:
    client.auth_token = gdata.gauth.token_from_blob(
        options.values[auth_token_key])
  if client.alt_auth_service is not None:
    client.alt_auth_token = gdata.gauth.token_from_blob(
        options.values[client.alt_auth_service])


def configure_cache(client, test_name):
  """Loads or begins a cached session to record HTTP traffic.

  Should be called at the beginning of each test method.

  Args:
    client: a gdata.GDClient whose http_client member has been replaced
            with a atom.mock_http_core.MockHttpClient so that repeated
            executions can used cached responses instead of contacting
            the server.
    test_name: str The name of this test method. Examples: 
               'TestClass.test_x_works', 'TestClass.test_crud_operations'.
               This is used to name the recording of the HTTP requests and
               responses, so it should be unique to each test method in the
               test case.
  """
  # Auth token is obtained in configure_client which is called as part of
  # setUp.
  client.http_client.cache_test_name = test_name
  cache_name = client.http_client.get_cache_file_name()
  if options.get_value('clearcache') == 'true':
    client.http_client.delete_session(cache_name)
  client.http_client.use_cached_session(cache_name)


def close_client(client):
  """Saves the recoded responses to a temp file if the config file allows.
  
  This should be called in the unit test's tearDown method.

  Checks to see if the 'savecache' option is set to 'true', to make sure we
  only save sessions to repeat if the user desires.
  """
  if client and options.get_value('savecache') == 'true':
    # If this was a live request, save the recording.
    client.http_client.close_session()


def configure_service(service, case_name, service_name):
  """Sets up a mock GDataService v1 client to reuse recorded sessions.
  
  Should be called during setUp of each unit test. This is a duplicate of
  configure_client, modified to handle old v1 service classes.
  """
  service.http_client.v2_http_client = atom.mock_http_core.MockHttpClient()
  service.http_client.v2_http_client.cache_case_name = case_name
  # Getting the auth token only needs to be done once in the course of test
  # runs.
  auth_token_key = 'service_%s_auth_token' % service_name
  if (auth_token_key not in options.values
      and options.get_value('runlive') == 'true'):
    service.http_client.v2_http_client.cache_test_name = 'client_login'
    cache_name = service.http_client.v2_http_client.get_cache_file_name()
    if options.get_value('clearcache') == 'true':
      service.http_client.v2_http_client.delete_session(cache_name)
    service.http_client.v2_http_client.use_cached_session(cache_name)
    service.ClientLogin(options.get_value('username'),
                        options.get_value('password'),
                        service=service_name, source=case_name)
    options.values[auth_token_key] = service.GetClientLoginToken()
    service.http_client.v2_http_client.close_session()
  if auth_token_key in options.values:
    service.SetClientLoginToken(options.values[auth_token_key])


def configure_service_cache(service, test_name):
  """Loads or starts a session recording for a v1 Service object.
  
  Duplicates the behavior of configure_cache, but the target for this
  function is a v1 Service object instead of a v2 Client.
  """
  service.http_client.v2_http_client.cache_test_name = test_name
  cache_name = service.http_client.v2_http_client.get_cache_file_name()
  if options.get_value('clearcache') == 'true':
    service.http_client.v2_http_client.delete_session(cache_name)
  service.http_client.v2_http_client.use_cached_session(cache_name)


def close_service(service):
  if service and options.get_value('savecache') == 'true':
    # If this was a live request, save the recording.
    service.http_client.v2_http_client.close_session()


def build_suite(classes):
  """Creates a TestSuite for all unit test classes in the list.
  
  Assumes that each of the classes in the list has unit test methods which
  begin with 'test'. Calls unittest.makeSuite.

  Returns: 
    A new unittest.TestSuite containing a test suite for all classes.   
  """
  suites = [unittest.makeSuite(a_class, 'test') for a_class in classes]
  return unittest.TestSuite(suites)


def check_data_classes(test, classes):
  import inspect
  for data_class in classes:
    test.assert_(data_class.__doc__ is not None,
                 'The class %s should have a docstring' % data_class)
    if hasattr(data_class, '_qname'):
      qname_versions = None
      if isinstance(data_class._qname, tuple):
        qname_versions = data_class._qname
      else:
        qname_versions = (data_class._qname,)
      for versioned_qname in qname_versions:
        test.assert_(isinstance(versioned_qname, str),
                     'The class %s has a non-string _qname' % data_class)
        test.assert_(not versioned_qname.endswith('}'), 
                     'The _qname for class %s is only a namespace' % (
                         data_class))

    for attribute_name, value in data_class.__dict__.iteritems():
      # Ignore all elements that start with _ (private members)
      if not attribute_name.startswith('_'):
        try:
          if not (isinstance(value, str) or inspect.isfunction(value) 
              or (isinstance(value, list)
                  and issubclass(value[0], atom.core.XmlElement))
              or type(value) == property # Allow properties.
              or inspect.ismethod(value) # Allow methods. 
              or inspect.ismethoddescriptor(value) # Allow method descriptors.
                                                   # staticmethod et al.
              or issubclass(value, atom.core.XmlElement)):
            test.fail(
                'XmlElement member should have an attribute, XML class,'
                ' or list of XML classes as attributes.')

        except TypeError:
          test.fail('Element %s in %s was of type %s' % (
              attribute_name, data_class._qname, type(value)))


def check_clients_with_auth(test, classes):
  for client_class in classes:
    test.assert_(hasattr(client_class, 'api_version'))
    test.assert_(isinstance(client_class.auth_service, (str, unicode, int)))
    test.assert_(hasattr(client_class, 'auth_service'))
    test.assert_(isinstance(client_class.auth_service, (str, unicode)))
    test.assert_(hasattr(client_class, 'auth_scopes'))
    test.assert_(isinstance(client_class.auth_scopes, (list, tuple)))
