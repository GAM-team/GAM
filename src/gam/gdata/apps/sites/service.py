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

"""SitesService extends the GDataService for Google Sites API calls."""

import gdata.apps
import gdata.apps.service
import gdata.service


# Feed URI templates
CONTENT_FEED_TEMPLATE = '/feeds/content/%s/%s/'
REVISION_FEED_TEMPLATE = '/feeds/revision/%s/%s/'
ACTIVITY_FEED_TEMPLATE = '/feeds/activity/%s/%s/'
ACTIVITY_ENTRY_TEMPLATE = '/feeds/activity/%s/%s/%s'
SITE_FEED_TEMPLATE = '/feeds/site/%s/'
ACL_FEED_TEMPLATE = '/feeds/acl/site/%s/%s'
ACL_ENTRY_TEMPLATE = '/feeds/acl/site/%s/%s/%s'


class SitesService(gdata.service.GDataService):
  """Client extension for the Google Sites API service."""

  def __init__(self,
               source=None, server='sites.google.com', additional_headers=None,
               **kwargs):
    """Constructs a new client for the Sites API.

    Args:
      site: string (optional) Name (webspace) of the Google Site
      domain: string (optional) Domain of the (Google Apps hosted) Site.
          If no domain is given, the Site is assumed to be a consumer Google
          Site, in which case the value 'site' is used.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'sites..google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    if additional_headers == None:
      additional_headers = {}
    additional_headers['GData-Version'] = '1.4'
    gdata.service.GDataService.__init__(self,
                                        source=source, server=server, additional_headers=additional_headers,
                                        **kwargs)
    self.ssl = True
    self.port = 443

  def make_site_feed_uri(self, domain=None, site=None):
    if not domain:
      domain = 'site'
    if not site:
      return SITE_FEED_TEMPLATE % domain
    return (SITE_FEED_TEMPLATE % domain) + site

  MakeSiteFeedUri = make_site_feed_uri

  def get_site_feed(self, uri=None, domain=None, site=None,
                    extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_site_feed_uri(domain=domain, site=site)
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.SiteFeedFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  GetSiteFeed = get_site_feed

  def create_site(self, siteentry=None, uri=None, domain=None, site=None,
                  extra_headers=None, url_params=None, escape_params=True):

    if uri is None:
      uri = self.make_site_feed_uri(domain=domain, site=site)
    try:
      return self.Post(siteentry, uri,
                       url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                       converter=gdata.apps.sites.SiteEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  CreateSite = create_site

  def get_site(self, uri=None, domain=None, site=None,
               extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_site_feed_uri(domain=domain, site=site)
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.SiteEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  GetSite = get_site

  def update_site(self, siteentry=None, uri=None, domain=None, site=None,
                  extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_site_feed_uri(domain=domain, site=site)
    try:
      return self.Put(siteentry, uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.SiteEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  UpdateSite = update_site

  def make_acl_feed_uri(self, domain=None, site=None):
    return ACL_FEED_TEMPLATE % (domain, site)

  MakeAclFeedUri = make_acl_feed_uri

  def get_acl_feed(self, uri=None, domain=None, site=None,
                   extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_acl_feed_uri(domain=domain, site=site)
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.AclFeedFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  GetAclFeed = get_acl_feed

  def make_acl_entry_uri(self, domain=None, site=None, ruleId=None):
    return ACL_ENTRY_TEMPLATE % (domain, site, ruleId)

  MakeAclEntryUri = make_acl_entry_uri

  def create_acl_entry(self, aclentry=None, uri=None, domain=None, site=None,
                       extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_acl_feed_uri(domain=domain, site=site)
    try:
      return self.Post(aclentry, uri,
                       url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                       converter=gdata.apps.sites.AclEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  CreateAclEntry = create_acl_entry

  def get_acl_entry(self, uri=None, domain=None, site=None, ruleId=None,
                    extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_acl_entry_uri(domain=domain, site=site, ruleId=ruleId)
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.AclEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  GetAclEntry = get_acl_entry

  def update_acl_entry(self, aclentry=None, uri=None, domain=None, site=None, ruleId=None,
                       extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_acl_entry_uri(domain=domain, site=site, ruleId=ruleId)
    try:
      return self.Put(aclentry, uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.AclEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  UpdateAclEntry = update_acl_entry

  def delete_acl_entry(self, uri=None, domain=None, site=None, ruleId=None,
                       extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_acl_entry_uri(domain=domain, site=site, ruleId=ruleId)
    try:
      return self.Delete(uri,
                         url_params=url_params, escape_params=escape_params, extra_headers=extra_headers)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  DeleteAclEntry = delete_acl_entry

  def make_activity_feed_uri(self, domain=None, site=None):
    return ACTIVITY_FEED_TEMPLATE % (domain, site)

  MakeActivityFeedUri = make_activity_feed_uri

  def get_activity_feed(self, uri=None, domain=None, site=None,
                        extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_activity_feed_uri(domain=domain, site=site)
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.ActivityFeedFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  GetActivityFeed = get_activity_feed

  def make_activity_entry_uri(self, domain=None, site=None, activityId=None):
    return ACTIVITY_ENTRY_TEMPLATE % (domain, site, activityId)

  MakeActivityEntryUri = make_activity_entry_uri

  def get_activity_entry(self, uri=None, domain=None, site=None, activityId=None,
                         extra_headers=None, url_params=None, escape_params=True):

    uri = uri or self.make_activity_entry_uri(domain=domain, site=site, activityId=activityId)
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.sites.ActivityEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  GetActivityEntry = get_activity_entry

class SitesQuery(gdata.service.Query):

  def make_site_feed_uri(self, domain=None, site=None):
    if not domain:
      domain = 'site'
    if not site:
      return SITE_FEED_TEMPLATE % domain
    return (SITE_FEED_TEMPLATE % domain) + site

  def __init__(self, feed=None, domain=None, site=None, params=None):
    self.feed = feed or self.make_site_feed_uri(domain=domain, site=site)
    gdata.service.Query.__init__(self, feed=self.feed, params=params)

