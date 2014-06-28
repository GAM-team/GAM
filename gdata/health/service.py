#!/usr/bin/python
#
# Copyright 2009 Google Inc. All Rights Reserved.
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

"""HealthService extends GDataService to streamline Google Health API access.

  HealthService: Provides methods to interact with the profile, profile list,
                 and register/notices feeds. Extends GDataService.

  HealthProfileQuery: Queries the Google Health Profile feed.

  HealthProfileListQuery: Queries the Google Health Profile list feed.
"""

__author__ = 'api.eric@google.com (Eric Bidelman)'


import atom
import gdata.health
import gdata.service


class HealthService(gdata.service.GDataService):

  """Client extension for the Google Health service Document List feed."""

  def __init__(self, email=None, password=None, source=None,
               use_h9_sandbox=False, server='www.google.com',
               additional_headers=None, **kwargs):
    """Creates a client for the Google Health service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      use_h9_sandbox: boolean (optional) True to issue requests against the
          /h9 developer's sandbox.
      server: string (optional) The name of the server to which a connection
          will be opened.
      additional_headers: dictionary (optional) Any additional headers which
          should be included with CRUD operations.
      kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    service = use_h9_sandbox and 'weaver' or 'health'
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service=service, source=source,
        server=server, additional_headers=additional_headers, **kwargs)
    self.ssl = True
    self.use_h9_sandbox = use_h9_sandbox

  def __get_service(self):
    return self.use_h9_sandbox and 'h9' or 'health'

  def GetProfileFeed(self, query=None, profile_id=None):
    """Fetches the users Google Health profile feed.

    Args:
      query: HealthProfileQuery or string (optional) A query to use on the
          profile feed.  If None, a HealthProfileQuery is constructed.
      profile_id: string (optional) The profile id to query the profile feed
          with when using ClientLogin.  Note: this parameter is ignored if
          query is set.

    Returns:
      A gdata.health.ProfileFeed object containing the user's Health profile.
    """
    if query is None:
      projection = profile_id and 'ui' or 'default'
      uri = HealthProfileQuery(
          service=self.__get_service(), projection=projection,
          profile_id=profile_id).ToUri()
    elif isinstance(query, HealthProfileQuery):
      uri = query.ToUri()
    else:
      uri = query

    return self.GetFeed(uri, converter=gdata.health.ProfileFeedFromString)

  def GetProfileListFeed(self, query=None):
    """Fetches the users Google Health profile feed.

    Args:
      query: HealthProfileListQuery or string (optional) A query to use
          on the profile list feed.  If None, a HealthProfileListQuery is
          constructed to /health/feeds/profile/list or /h9/feeds/profile/list.

    Returns:
      A gdata.health.ProfileListFeed object containing the user's list
      of profiles.
    """
    if not query:
      uri = HealthProfileListQuery(service=self.__get_service()).ToUri()
    elif isinstance(query, HealthProfileListQuery):
      uri = query.ToUri()
    else:
      uri = query

    return self.GetFeed(uri, converter=gdata.health.ProfileListFeedFromString)

  def SendNotice(self, subject, body=None, content_type='html',
                 ccr=None, profile_id=None):
    """Sends (posts) a notice to the user's Google Health profile.

    Args:
      subject: A string representing the message's subject line.
      body: string (optional) The message body.
      content_type: string (optional) The content type of the notice message
          body.  This parameter is only honored when a message body is
          specified.
      ccr: string (optional) The CCR XML document to reconcile into the
          user's profile.
      profile_id: string (optional) The profile id to work with when using
          ClientLogin.  Note: this parameter is ignored if query is set.

    Returns:
      A gdata.health.ProfileEntry object of the posted entry.
    """
    if body:
      content = atom.Content(content_type=content_type, text=body)
    else:
      content = body

    entry = gdata.GDataEntry(
        title=atom.Title(text=subject), content=content,
        extension_elements=[atom.ExtensionElementFromString(ccr)])

    projection = profile_id and 'ui' or 'default'
    query = HealthRegisterQuery(service=self.__get_service(),
                                projection=projection, profile_id=profile_id)
    return self.Post(entry, query.ToUri(),
                     converter=gdata.health.ProfileEntryFromString)


class HealthProfileQuery(gdata.service.Query):

  """Object used to construct a URI to query the Google Health profile feed."""

  def __init__(self, service='health', feed='feeds/profile',
               projection='default', profile_id=None, text_query=None,
               params=None, categories=None):
    """Constructor for Health profile feed query.

    Args:
      service: string (optional) The service to query. Either 'health' or 'h9'.
      feed: string (optional) The path for the feed. The default value is
          'feeds/profile'.
      projection: string (optional) The visibility of the data. Possible values
          are 'default' for AuthSub and 'ui' for ClientLogin.  If this value
          is set to 'ui', the profile_id parameter should also be set.
      profile_id: string (optional) The profile id to query.  This should only
          be used when using ClientLogin.
      text_query: str (optional) The contents of the q query parameter. The
          contents of the text_query are URL escaped upon conversion to a URI.
          Note: this parameter can only be used on the register feed using
          ClientLogin.
      params: dict (optional) Parameter value string pairs which become URL
          params when translated to a URI. These parameters are added to
          the query's items.
      categories: list (optional) List of category strings which should be
          included as query categories. See gdata.service.Query for
          additional documentation.
    """
    self.service = service
    self.profile_id = profile_id
    self.projection = projection
    gdata.service.Query.__init__(self, feed=feed, text_query=text_query,
                                 params=params, categories=categories)

  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI used to retrieve entries from the Health
      profile feed.
    """
    old_feed = self.feed
    self.feed = '/'.join([self.service, old_feed, self.projection])

    if self.profile_id:
      self.feed += '/' + self.profile_id
    self.feed = '/%s' % (self.feed,)

    new_feed = gdata.service.Query.ToUri(self)
    self.feed = old_feed
    return new_feed


class HealthProfileListQuery(gdata.service.Query):

  """Object used to construct a URI to query a Health profile list feed."""

  def __init__(self, service='health', feed='feeds/profile/list'):
    """Constructor for Health profile list feed query.

    Args:
      service: string (optional) The service to query. Either 'health' or 'h9'.
      feed: string (optional) The path for the feed.  The default value is
          'feeds/profile/list'.
    """
    gdata.service.Query.__init__(self, feed)
    self.service = service

  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI used to retrieve entries from the
      profile list feed.
    """
    return '/%s' % ('/'.join([self.service, self.feed]),)


class HealthRegisterQuery(gdata.service.Query):

  """Object used to construct a URI to query a Health register/notice feed."""

  def __init__(self, service='health', feed='feeds/register',
               projection='default', profile_id=None):
    """Constructor for Health profile list feed query.

    Args:
      service: string (optional) The service to query. Either 'health' or 'h9'.
      feed: string (optional) The path for the feed.  The default value is
          'feeds/register'.
      projection: string (optional) The visibility of the data. Possible values
          are 'default' for AuthSub and 'ui' for ClientLogin.  If this value
          is set to 'ui', the profile_id parameter should also be set.
      profile_id: string (optional) The profile id to query.  This should only
          be used when using ClientLogin.
    """
    gdata.service.Query.__init__(self, feed)
    self.service = service
    self.projection = projection
    self.profile_id = profile_id

  def ToUri(self):
    """Generates a URI from the query parameters set in the object.

    Returns:
      A string containing the URI needed to interact with the register feed.
    """
    old_feed = self.feed
    self.feed = '/'.join([self.service, old_feed, self.projection])
    new_feed = gdata.service.Query.ToUri(self)
    self.feed = old_feed

    if self.profile_id:
      new_feed += '/' + self.profile_id
    return '/%s' % (new_feed,)
