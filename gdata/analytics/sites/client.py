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

"""SitesClient extends gdata.client.GDClient to streamline Sites API calls."""


__author__ = 'e.bidelman (Eric Bidelman)'

import atom.data
import gdata.client
import gdata.sites.data
import gdata.gauth


# Feed URI templates
CONTENT_FEED_TEMPLATE = '/feeds/content/%s/%s/'
REVISION_FEED_TEMPLATE = '/feeds/revision/%s/%s/'
ACTIVITY_FEED_TEMPLATE = '/feeds/activity/%s/%s/'
SITE_FEED_TEMPLATE = '/feeds/site/%s/'
ACL_FEED_TEMPLATE = '/feeds/acl/site/%s/%s/'


class SitesClient(gdata.client.GDClient):

  """Client extension for the Google Sites API service."""

  host = 'sites.google.com'  # default server for the API
  domain = 'site'  # default site domain name
  api_version = '1.1'  # default major version for the service.
  auth_service = 'jotspot'
  auth_scopes = gdata.gauth.AUTH_SCOPES['jotspot']
  ssl = True

  def __init__(self, site=None, domain=None, auth_token=None, **kwargs):
    """Constructs a new client for the Sites API.

    Args:
      site: string (optional) Name (webspace) of the Google Site
      domain: string (optional) Domain of the (Google Apps hosted) Site.
          If no domain is given, the Site is assumed to be a consumer Google
          Site, in which case the value 'site' is used.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: The other parameters to pass to gdata.client.GDClient
          constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.site = site
    if domain is not None:
      self.domain = domain

  def __make_kind_category(self, label):
    if label is None:
      return None
    return atom.data.Category(
        scheme=gdata.sites.data.SITES_KIND_SCHEME,
        term='%s#%s' % (gdata.sites.data.SITES_NAMESPACE, label), label=label)

  __MakeKindCategory = __make_kind_category

  def __upload(self, entry, media_source, auth_token=None, **kwargs):
    """Uploads an attachment file to the Sites API.

    Args:
      entry: gdata.sites.data.ContentEntry The Atom XML to include.
      media_source: gdata.data.MediaSource The file payload to be uploaded.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to gdata.client.post().

    Returns:
      The created entry.
    """
    uri = self.make_content_feed_uri()
    return self.post(entry, uri, media_source=media_source,
                     auth_token=auth_token, **kwargs)

  def _get_file_content(self, uri):
    """Fetches the file content from the specified URI.

    Args:
      uri: string The full URL to fetch the file contents from.

    Returns:
      The binary file content.

    Raises:
      gdata.client.RequestError: on error response from server.
    """
    server_response = self.request('GET', uri)
    if server_response.status != 200:
      raise  gdata.client.RequestError, {'status': server_response.status,
                                         'reason': server_response.reason,
                                         'body': server_response.read()}
    return server_response.read()

  _GetFileContent = _get_file_content

  def make_content_feed_uri(self):
    return CONTENT_FEED_TEMPLATE % (self.domain, self.site)

  MakeContentFeedUri = make_content_feed_uri

  def make_revision_feed_uri(self):
    return REVISION_FEED_TEMPLATE % (self.domain, self.site)

  MakeRevisionFeedUri = make_revision_feed_uri

  def make_activity_feed_uri(self):
    return ACTIVITY_FEED_TEMPLATE % (self.domain, self.site)

  MakeActivityFeedUri = make_activity_feed_uri

  def make_site_feed_uri(self, site_name=None):
    if site_name is not None:
      return (SITE_FEED_TEMPLATE % self.domain) + site_name
    else:
      return SITE_FEED_TEMPLATE % self.domain

  MakeSiteFeedUri = make_site_feed_uri

  def make_acl_feed_uri(self):
    return ACL_FEED_TEMPLATE % (self.domain, self.site)

  MakeAclFeedUri = make_acl_feed_uri

  def get_content_feed(self, uri=None, auth_token=None, **kwargs):
    """Retrieves the content feed containing the current state of site.

    Args:
      uri: string (optional) A full URI to query the Content feed with.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.sites.data.ContentFeed
    """
    if uri is None:
      uri = self.make_content_feed_uri()
    return self.get_feed(uri, desired_class=gdata.sites.data.ContentFeed,
                         auth_token=auth_token, **kwargs)

  GetContentFeed = get_content_feed

  def get_revision_feed(self, entry_or_uri_or_id, auth_token=None, **kwargs):
    """Retrieves the revision feed containing the revision history for a node.

    Args:
      entry_or_uri_or_id: string or gdata.sites.data.ContentEntry A full URI,
          content entry node ID, or a content entry object of the entry to
          retrieve revision information for.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.sites.data.RevisionFeed
    """
    uri = self.make_revision_feed_uri()
    if isinstance(entry_or_uri_or_id, gdata.sites.data.ContentEntry):
      uri = entry_or_uri_or_id.FindRevisionLink()
    elif entry_or_uri_or_id.find('/') == -1:
      uri += entry_or_uri_or_id
    else:
      uri = entry_or_uri_or_id
    return self.get_feed(uri, desired_class=gdata.sites.data.RevisionFeed,
                         auth_token=auth_token, **kwargs)

  GetRevisionFeed = get_revision_feed

  def get_activity_feed(self, uri=None, auth_token=None, **kwargs):
    """Retrieves the activity feed containing recent Site activity.

    Args:
      uri: string (optional) A full URI to query the Activity feed.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.sites.data.ActivityFeed
    """
    if uri is None:
      uri = self.make_activity_feed_uri()
    return self.get_feed(uri, desired_class=gdata.sites.data.ActivityFeed,
                         auth_token=auth_token, **kwargs)

  GetActivityFeed = get_activity_feed

  def get_site_feed(self, uri=None, auth_token=None, **kwargs):
    """Retrieves the site feed containing a list of sites a user has access to.

    Args:
      uri: string (optional) A full URI to query the site feed.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.sites.data.SiteFeed
    """
    if uri is None:
      uri = self.make_site_feed_uri()
    return self.get_feed(uri, desired_class=gdata.sites.data.SiteFeed,
                         auth_token=auth_token, **kwargs)

  GetSiteFeed = get_site_feed

  def get_acl_feed(self, uri=None, auth_token=None, **kwargs):
    """Retrieves the acl feed containing a site's sharing permissions.

    Args:
      uri: string (optional) A full URI to query the acl feed.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.sites.data.AclFeed
    """
    if uri is None:
      uri = self.make_acl_feed_uri()
    return self.get_feed(uri, desired_class=gdata.sites.data.AclFeed,
                         auth_token=auth_token, **kwargs)

  GetAclFeed = get_acl_feed

  def create_site(self, title, description=None, source_site=None,
                  theme=None, uri=None, auth_token=None, **kwargs):
    """Creates a new Google Site.

    Note: This feature is only available to Google Apps domains.

    Args:
      title: string Title for the site.
      description: string (optional) A description/summary for the site.
      source_site: string (optional) The site feed URI of the site to copy.
          This parameter should only be specified when copying a site.
      theme: string (optional) The name of the theme to create the site with.
      uri: string (optional) A full site feed URI to override where the site
          is created/copied. By default, the site will be created under
          the currently set domain (e.g. self.domain).
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to gdata.client.post().

    Returns:
      gdata.sites.data.SiteEntry of the created site.
    """
    new_entry = gdata.sites.data.SiteEntry(title=atom.data.Title(text=title))

    if description is not None:
      new_entry.summary = gdata.sites.data.Summary(text=description)

    # Add the source link if we're making a copy of a site.
    if source_site is not None:
      source_link = atom.data.Link(rel=gdata.sites.data.SITES_SOURCE_LINK_REL,
                                   type='application/atom+xml',
                                   href=source_site)
      new_entry.link.append(source_link)

    if theme is not None:
      new_entry.theme = gdata.sites.data.Theme(text=theme)

    if uri is None:
      uri = self.make_site_feed_uri()

    return self.post(new_entry, uri, auth_token=auth_token, **kwargs)

  CreateSite = create_site

  def create_page(self, kind, title, html='', page_name=None, parent=None,
                  auth_token=None, **kwargs):
    """Creates a new page (specified by kind) on a Google Site.

    Args:
      kind: string The type of page/item to create. For example, webpage,
          listpage, comment, announcementspage, filecabinet, etc. The full list
          of supported kinds can be found in gdata.sites.gdata.SUPPORT_KINDS.
      title: string Title for the page.
      html: string (optional) XHTML for the page's content body.
      page_name: string (optional) The URL page name to set. If not set, the
          title will be normalized and used as the page's URL path.
      parent: string or gdata.sites.data.ContentEntry (optional) The parent
          entry or parent link url to create the page under.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to gdata.client.post().

    Returns:
      gdata.sites.data.ContentEntry of the created page.
    """
    new_entry = gdata.sites.data.ContentEntry(
        title=atom.data.Title(text=title), kind=kind,
        content=gdata.sites.data.Content(text=html))

    if page_name is not None:
      new_entry.page_name = gdata.sites.data.PageName(text=page_name)

    # Add parent link to entry if it should be uploaded as a subpage.
    if isinstance(parent, gdata.sites.data.ContentEntry):
      parent_link = atom.data.Link(rel=gdata.sites.data.SITES_PARENT_LINK_REL,
                                   type='application/atom+xml',
                                   href=parent.GetSelfLink().href)
      new_entry.link.append(parent_link)
    elif parent is not None:
      parent_link = atom.data.Link(rel=gdata.sites.data.SITES_PARENT_LINK_REL,
                                   type='application/atom+xml',
                                   href=parent)
      new_entry.link.append(parent_link)

    return self.post(new_entry, self.make_content_feed_uri(),
                     auth_token=auth_token, **kwargs)

  CreatePage = create_page

  def create_webattachment(self, src, content_type, title, parent,
                           description=None, auth_token=None, **kwargs):
    """Creates a new webattachment within a filecabinet.

    Args:
      src: string The url of the web attachment.
      content_type: string The MIME type of the web attachment.
      title: string The title to name the web attachment.
      parent: string or gdata.sites.data.ContentEntry (optional) The
          parent entry or url of the filecabinet to create the attachment under.
      description: string (optional) A summary/description for the attachment.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to gdata.client.post().

    Returns:
      gdata.sites.data.ContentEntry of the created page.
    """
    new_entry = gdata.sites.data.ContentEntry(
        title=atom.data.Title(text=title), kind='webattachment',
        content=gdata.sites.data.Content(src=src, type=content_type))

    if isinstance(parent, gdata.sites.data.ContentEntry):
      link = atom.data.Link(rel=gdata.sites.data.SITES_PARENT_LINK_REL,
                            type='application/atom+xml',
                            href=parent.GetSelfLink().href)
    elif parent is not None:
      link = atom.data.Link(rel=gdata.sites.data.SITES_PARENT_LINK_REL,
                            type='application/atom+xml', href=parent)

    new_entry.link.append(link)

    # Add file decription if it was specified
    if description is not None:
      new_entry.summary = gdata.sites.data.Summary(type='text',
                                                   text=description)

    return self.post(new_entry, self.make_content_feed_uri(),
                     auth_token=auth_token, **kwargs)

  CreateWebAttachment = create_webattachment

  def upload_attachment(self, file_handle, parent, content_type=None,
                        title=None, description=None, folder_name=None,
                        auth_token=None, **kwargs):
    """Uploads an attachment to a parent page.

    Args:
      file_handle: MediaSource or string A gdata.data.MediaSource object
          containing the file to be uploaded or the full path name to the
          file on disk.
      parent: gdata.sites.data.ContentEntry or string The parent page to
          upload the file to or the full URI of the entry's self link.
      content_type: string (optional) The MIME type of the file
          (e.g 'application/pdf'). This should be provided if file is not a
          MediaSource object.
      title: string (optional) The title to name the attachment. If not
          included, the filepath or media source's filename is used.
      description: string (optional) A summary/description for the attachment.
      folder_name: string (optional) The name of an existing folder to upload
          the attachment to. This only applies when the parent parameter points
          to a filecabinet entry.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.__upload().

    Returns:
      A gdata.sites.data.ContentEntry containing information about the created
      attachment.
    """
    if isinstance(parent, gdata.sites.data.ContentEntry):
      link = atom.data.Link(rel=gdata.sites.data.SITES_PARENT_LINK_REL,
                            type='application/atom+xml',
                            href=parent.GetSelfLink().href)
    else:
      link = atom.data.Link(rel=gdata.sites.data.SITES_PARENT_LINK_REL,
                            type='application/atom+xml',
                            href=parent)

    if not isinstance(file_handle, gdata.data.MediaSource):
      ms = gdata.data.MediaSource(file_path=file_handle,
                                  content_type=content_type)
    else:
      ms = file_handle

    # If no title specified, use the file name
    if title is None:
      title = ms.file_name

    new_entry = gdata.sites.data.ContentEntry(kind='attachment')
    new_entry.title = atom.data.Title(text=title)
    new_entry.link.append(link)

    # Add file decription if it was specified
    if description is not None:
      new_entry.summary = gdata.sites.data.Summary(type='text',
                                                   text=description)

    # Upload the attachment to a filecabinet folder?
    if parent.Kind() == 'filecabinet' and folder_name is not None:
      folder_category = atom.data.Category(
          scheme=gdata.sites.data.FOLDER_KIND_TERM, term=folder_name)
      new_entry.category.append(folder_category)

    return self.__upload(new_entry, ms, auth_token=auth_token, **kwargs)

  UploadAttachment = upload_attachment

  def download_attachment(self, uri_or_entry, file_path):
    """Downloads an attachment file to disk.

    Args:
      uri_or_entry: string The full URL to download the file from.
      file_path: string The full path to save the file to.

    Raises:
      gdata.client.RequestError: on error response from server.
    """
    uri = uri_or_entry
    if isinstance(uri_or_entry, gdata.sites.data.ContentEntry):
      uri = uri_or_entry.content.src

    f = open(file_path, 'wb')
    try:
      f.write(self._get_file_content(uri))
    except gdata.client.RequestError, e:
      f.close()
      raise e
    f.flush()
    f.close()

  DownloadAttachment = download_attachment
