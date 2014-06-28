#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.
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

"""DocsClient simplifies interactions with the Documents List API."""

__author__ = 'vicfryzel@google.com (Vic Fryzel)'

import copy
import mimetypes
import re
import urllib
import atom.data
import atom.http_core
import gdata.client
import gdata.docs.data
import gdata.gauth


# Feed URIs that are given by the API, but cannot be obtained without
# making a mostly unnecessary HTTP request.
RESOURCE_FEED_URI = '/feeds/default/private/full'
RESOURCE_UPLOAD_URI = '/feeds/upload/create-session/default/private/full'
COLLECTION_UPLOAD_URI_TEMPLATE = \
    '/feeds/upload/create-session/feeds/default/private/full/%s/contents'
ARCHIVE_FEED_URI = '/feeds/default/private/archive'
METADATA_URI = '/feeds/metadata/default'
CHANGE_FEED_URI = '/feeds/default/private/changes'


class DocsClient(gdata.client.GDClient):
  """Client for all features of the Google Documents List API."""

  host = 'docs.google.com'
  api_version = '3.0'
  auth_service = 'writely'
  alt_auth_service = 'wise'
  alt_auth_token = None
  auth_scopes = gdata.gauth.AUTH_SCOPES['writely']
  ssl = True

  def request(self, method=None, uri=None, **kwargs):
    """Add support for imitating other users via 2-Legged OAuth.

    Args:
      uri: (optional) URI of the request in which to replace default with
          self.xoauth_requestor_id.
    Returns:
      Result of super(DocsClient, self).request().
    """
    if self.xoauth_requestor_id is not None and uri is not None:
      if isinstance(uri, (str, unicode)):
        uri = atom.http_core.Uri.parse_uri(uri)
      uri.path.replace('/default', '/%s' % self.xoauth_requestor_id)
    return super(DocsClient, self).request(method=method, uri=uri, **kwargs)

  Request = request

  def get_metadata(self, **kwargs):
    """Retrieves the metadata of a user account.

    Args:
      kwargs: Other parameters to pass to self.get_entry().

    Returns:
      gdata.docs.data.Metadata representing metadata of user's account.
    """
    return self.get_entry(
        METADATA_URI, desired_class=gdata.docs.data.Metadata, **kwargs)

  GetMetadata = get_metadata

  def get_changes(self, changestamp=None, max_results=None, **kwargs):
    """Retrieves changes to a user's documents list.

    Args:
      changestamp: (optional) String changestamp value to query since.
          If provided, returned changes will have a changestamp larger than
          the given one.
      max_results: (optional) Number of results to fetch.  API will limit
          this number to 100 at most.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.docs.data.ChangeFeed.
    """
    uri = atom.http_core.Uri.parse_uri(CHANGE_FEED_URI)

    if changestamp is not None:
      uri.query['start-index'] = changestamp
    if max_results is not None:
      uri.query['max-results'] = max_results

    return self.get_feed(
        uri, desired_class=gdata.docs.data.ChangeFeed, **kwargs)

  GetChanges = get_changes

  def get_resources(self, uri=None, limit=None, **kwargs):
    """Retrieves the resources in a user's docslist, or the given URI.

    Args:
      uri: (optional) URI to query for resources.  If None, then
          gdata.docs.client.DocsClient.RESOURCE_FEED_URI is used, which will
          query for all non-collections.
      limit: int (optional) A maximum cap for the number of results to
          return in the feed. By default, the API returns a maximum of 100
          per page. Thus, if you set limit=5000, you will get <= 5000
          documents (guarenteed no more than 5000), and will need to follow the
          feed's next links (feed.GetNextLink()) to the rest. See
          get_everything(). Similarly, if you set limit=50, only <= 50
          documents are returned. Note: if the max-results parameter is set in
          the uri parameter, it is chosen over a value set for limit.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.docs.data.ResourceFeed feed.
    """
    if uri is None:
      uri = RESOURCE_FEED_URI

    if isinstance(uri, basestring):
      uri = atom.http_core.Uri.parse_uri(uri)    

    # Add max-results param if it wasn't included in the uri.
    if limit is not None and not 'max-results' in uri.query:
      uri.query['max-results'] = limit

    return self.get_feed(uri, desired_class=gdata.docs.data.ResourceFeed,
                         **kwargs)

  GetResources = get_resources

  def get_all_resources(self, uri=None, **kwargs):
    """Retrieves all of a user's non-collections or everything at the given URI.

    Folders are not included in this by default.  Pass in a custom URI to
    include collections in your query.  The DocsQuery class is an easy way to
    generate such a URI.

    This method makes multiple HTTP requests (by following the feed's next
    links) in order to fetch the user's entire document list.

    Args:
      uri: (optional) URI to query the doclist feed with. If None, then use
          DocsClient.RESOURCE_FEED_URI, which will retrieve all
          non-collections.
      kwargs: Other parameters to pass to self.GetResources().

    Returns:
      List of gdata.docs.data.Resource objects representing the retrieved
      entries.
    """
    if uri is None:
      uri = RESOURCE_FEED_URI

    feed = self.GetResources(uri=uri, **kwargs)
    entries = feed.entry

    while feed.GetNextLink() is not None:
      feed = self.GetResources(feed.GetNextLink().href, **kwargs)
      entries.extend(feed.entry)

    return entries

  GetAllResources = get_all_resources

  def get_resource(self, entry, **kwargs):
    """Retrieves a resource again given its entry.
    
    Args:
      entry: gdata.docs.data.Resource to fetch and return.
      kwargs: Other args to pass to GetResourceBySelfLink().
    Returns:
      gdata.docs.data.Resource representing retrieved resource.
    """

    return self.GetResourceBySelfLink(entry.GetSelfLink().href, **kwargs)

  GetResource = get_resource

  def get_resource_by_self_link(self, self_link, etag=None, **kwargs):
    """Retrieves a particular resource by its self link.

    Args:
      self_link: URI at which to query for given resource.  This can be found
          using entry.GetSelfLink().
      etag: str (optional) The document/item's etag value to be used in a
          conditional GET. See http://code.google.com/apis/documents/docs/3.0/
          developers_guide_protocol.html#RetrievingCached.
      kwargs: Other parameters to pass to self.get_entry().

    Returns:
      gdata.docs.data.Resource representing the retrieved resource.
    """
    if isinstance(self_link, atom.data.Link):
      self_link = self_link.href

    return self.get_entry(
        self_link, etag=etag, desired_class=gdata.docs.data.Resource, **kwargs)

  GetResourceBySelfLink = get_resource_by_self_link

  def get_resource_acl(self, entry, **kwargs):
    """Retrieves the ACL sharing permissions for the given entry.

    Args:
      entry: gdata.docs.data.Resource for which to get ACL.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.docs.data.AclFeed representing the resource's ACL.
    """
    self._check_entry_is_resource(entry)
    return self.get_feed(entry.GetAclFeedLink().href,
                         desired_class=gdata.docs.data.AclFeed, **kwargs)

  GetResourceAcl = get_resource_acl

  def create_resource(self, entry, media=None, collection=None,
                      create_uri=None, **kwargs):
    """Creates new entries in Google Docs, and uploads their contents.

    Args:
      entry: gdata.docs.data.Resource representing initial version
          of entry being created. If media is also provided, the entry will
          first be created with the given metadata and content.
      media: (optional) gdata.data.MediaSource containing the file to be
          uploaded.
      collection: (optional) gdata.docs.data.Resource representing a collection 
          in which this new entry should be created. If provided along
          with create_uri, create_uri will win (e.g. entry will be created at
          create_uri, not necessarily in given collection).
      create_uri: (optional) String URI at which to create the given entry. If
          collection, media and create_uri are None, use
          gdata.docs.client.RESOURCE_FEED_URI.  If collection and create_uri are
          None, use gdata.docs.client.RESOURCE_UPLOAD_URI.  If collection and
          media are not None,
          gdata.docs.client.COLLECTION_UPLOAD_URI_TEMPLATE is used,
          with the collection's resource ID substituted in.
      kwargs: Other parameters to pass to self.post() and self.update().

    Returns:
      gdata.docs.data.Resource containing information about new entry.
    """
    if media is not None:
      if create_uri is None and collection is not None:
        create_uri = COLLECTION_UPLOAD_URI_TEMPLATE % \
            collection.resource_id.text
      elif create_uri is None:
        create_uri = RESOURCE_UPLOAD_URI
      uploader = gdata.client.ResumableUploader(
          self, media.file_handle, media.content_type, media.content_length,
          desired_class=gdata.docs.data.Resource)
      return uploader.upload_file(create_uri, entry, **kwargs)
    else:
      if create_uri is None and collection is not None:
        create_uri = collection.content.src
      elif create_uri is None:
        create_uri = RESOURCE_FEED_URI
      return self.post(
          entry, create_uri, desired_class=gdata.docs.data.Resource, **kwargs)

  CreateResource = create_resource

  def update_resource(self, entry, media=None, update_metadata=True,
                      new_revision=False, **kwargs):
    """Updates an entry in Google Docs with new metadata and/or new data.

    Args:
      entry: Entry to update. Make any metadata changes to this entry.
      media: (optional) gdata.data.MediaSource object containing the file with
          which to replace the entry's data.
      update_metadata: (optional) True to update the metadata from the entry
          itself.  You might set this to False to only update an entry's
          file content, and not its metadata.
      new_revision: (optional) True to create a new revision with this update,
          False otherwise.
      kwargs: Other parameters to pass to self.post().

    Returns:
      gdata.docs.data.Resource representing the updated entry.
    """

    uri_params = {}
    if new_revision:
      uri_params['new-revision'] = 'true'

    if update_metadata and media is None:
      uri = atom.http_core.parse_uri(entry.GetEditLink().href)
      uri.query.update(uri_params)
      return super(DocsClient, self).update(entry, **kwargs)
    else:
      uploader = gdata.client.ResumableUploader(
          self, media.file_handle, media.content_type, media.content_length,
          desired_class=gdata.docs.data.Resource)
      return uploader.UpdateFile(entry_or_resumable_edit_link=entry,
                                 update_metadata=update_metadata,
                                 uri_params=uri_params, **kwargs)

  UpdateResource = update_resource

  def download_resource(self, entry, file_path, extra_params=None, **kwargs):
    """Downloads the contents of the given entry to disk.

    Note: to download a file in memory, use the DownloadResourceToMemory()
    method.

    Args:
      entry: gdata.docs.data.Resource whose contents to fetch.
      file_path: str Full path to which to save file.
      extra_params: dict (optional) A map of any further parameters to control
          how the document is downloaded/exported. For example, exporting a
          spreadsheet as a .csv: extra_params={'gid': 0, 'exportFormat': 'csv'}
      kwargs: Other parameters to pass to self._download_file().

    Raises:
      gdata.client.RequestError if the download URL is malformed or the server's
      response was not successful.
    """
    self._check_entry_is_not_collection(entry)
    uri = self._get_download_uri(entry.content.src, extra_params)
    self._download_file(uri, file_path, **kwargs)

  DownloadResource = download_resource

  def download_resource_to_memory(self, entry, extra_params=None, **kwargs):
    """Returns the contents of the given entry.

    Args:
      entry: gdata.docs.data.Resource whose contents to fetch.
      extra_params: dict (optional) A map of any further parameters to control
          how the document is downloaded/exported. For example, exporting a
          spreadsheet as a .csv: extra_params={'gid': 0, 'exportFormat': 'csv'}
      kwargs: Other parameters to pass to self._get_content().

    Returns:
      Content of given resource after being downloaded.

    Raises:
      gdata.client.RequestError if the download URL is malformed or the server's
      response was not successful.
    """
    self._check_entry_is_not_collection(entry)
    uri = self._get_download_uri(entry.content.src, extra_params)
    return self._get_content(uri, **kwargs)

  DownloadResourceToMemory = download_resource_to_memory

  def _get_download_uri(self, base_uri, extra_params=None):
    uri = base_uri.replace('&amp;', '&')
    if extra_params is not None:
      if 'exportFormat' in extra_params and '/Export?' not in uri:
        raise gdata.client.Error, ('This entry type cannot be exported '
                                   'as a different format.')

      if 'gid' in extra_params and uri.find('spreadsheets') == -1:
        raise gdata.client.Error, 'gid param is not valid for this resource type.'

      uri += '&' + urllib.urlencode(extra_params)
    return uri

  def _get_content(self, uri, extra_params=None, auth_token=None, **kwargs):
    """Fetches the given resource's content.

    This method is useful for downloading/exporting a file within enviornments
    like Google App Engine, where the user may not have the ability to write
    the file to a local disk.

    Be warned, this method will use as much memory as needed to store the
    fetched content.  This could cause issues in your environment or app. This
    is only different from Download() in that you will probably retain an
    open reference to the data returned from this method, where as the data
    from Download() will be immediately written to disk and the memory
    freed.  This client library currently doesn't support reading server
    responses into a buffer or yielding an open file pointer to responses.

    Args:
      entry: Resource to fetch.
      extra_params: dict (optional) A map of any further parameters to control
          how the document is downloaded/exported. For example, exporting a
          spreadsheet as a .csv: extra_params={'gid': 0, 'exportFormat': 'csv'}
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the user's data.
      kwargs: Other parameters to pass to self.request().

    Returns:
      The binary file content.

    Raises:
      gdata.client.RequestError: on error response from server.
    """
    server_response = None
    token = auth_token
    if 'spreadsheets' in uri and token is None \
        and self.alt_auth_token is not None:
      token = self.alt_auth_token
    server_response = self.request(
        'GET', uri, auth_token=token, **kwargs)
    if server_response.status != 200:
      raise gdata.client.RequestError, {'status': server_response.status,
                                        'reason': server_response.reason,
                                        'body': server_response.read()}
    return server_response.read()

  def _download_file(self, uri, file_path, **kwargs):
    """Downloads a file to disk from the specified URI.

    Note: to download a file in memory, use the GetContent() method.

    Args:
      uri: str The full URL to download the file from.
      file_path: str The full path to save the file to.
      kwargs: Other parameters to pass to self.get_content().

    Raises:
      gdata.client.RequestError: on error response from server.
    """
    f = open(file_path, 'wb')
    try:
      f.write(self._get_content(uri, **kwargs))
    except gdata.client.RequestError, e:
      f.close()
      raise e
    f.flush()
    f.close()

  _DownloadFile = _download_file

  def copy_resource(self, entry, title, **kwargs):
    """Copies the given entry to a new entry with the given title.

    Note: Files do not support this feature.

    Args:
      entry: gdata.docs.data.Resource to copy.
      title: String title for the new entry.
      kwargs: Other parameters to pass to self.post().

    Returns:
      gdata.docs.data.Resource representing duplicated resource.
    """
    self._check_entry_is_resource(entry)
    new_entry = gdata.docs.data.Resource(
        title=atom.data.Title(text=title),
        id=atom.data.Id(text=entry.GetSelfLink().href))
    return self.post(new_entry, RESOURCE_FEED_URI, **kwargs)

  CopyResource = copy_resource

  def move_resource(self, entry, collection=None, keep_in_collections=False,
                    **kwargs):
    """Moves an item into a different collection (or out of all collections).

    Args:
      entry: gdata.docs.data.Resource to move.
      collection: gdata.docs.data.Resource (optional) An object representing
          the destination collection. If None, set keep_in_collections to
          False to remove the item from all collections.
      keep_in_collections: boolean (optional) If True, the given entry
          is not removed from any existing collections it is already in.
      kwargs: Other parameters to pass to self.post().

    Returns:
      gdata.docs.data.Resource of the moved entry.
    """
    self._check_entry_is_resource(entry)

    # Remove the item from any collections it is already in.
    if not keep_in_collections:
      for collection in entry.InCollections():
        uri = '%s/contents/%s' % (
            collection.href,
            urllib.quote(entry.resource_id.text))
        self.delete(uri, force=True)

    if collection is not None:
      self._check_entry_is_collection(collection)
      entry = self.post(entry, collection.content.src, **kwargs)
    return entry

  MoveResource = move_resource

  def delete_resource(self, entry, permanent=False, **kwargs):
    """Trashes or deletes the given entry.
    
    Args:
      entry: gdata.docs.data.Resource to trash or delete.
      permanent: True to skip the trash and delete the entry forever.
      kwargs: Other args to pass to gdata.client.GDClient.Delete()
    
    Returns:
      Result of delete request.
    """
    uri = entry.GetEditLink().href
    if permanent:
      uri += '?delete=true'
    return super(DocsClient, self).delete(uri, **kwargs)

  DeleteResource = delete_resource

  def _check_entry_is_resource(self, entry):
    """Ensures given entry is a gdata.docs.data.Resource.

    Args:
      entry: Entry to test.
    Raises:
      ValueError: If given entry is not a resource.
    """
    if not isinstance(entry, gdata.docs.data.Resource):
      raise ValueError('%s is not a gdata.docs.data.Resource' % str(entry))

  def _check_entry_is_collection(self, entry):
    """Ensures given entry is a collection.

    Args:
      entry: Entry to test.
    Raises:
      ValueError: If given entry is a collection.
    """
    self._check_entry_is_resource(entry)
    if entry.get_resource_type() != gdata.docs.data.COLLECTION_LABEL:
      raise ValueError('%s is not a collection' % str(entry))

  def _check_entry_is_not_collection(self, entry):
    """Ensures given entry is not a collection.

    Args:
      entry: Entry to test.
    Raises:
      ValueError: If given entry is a collection.
    """
    try:
      self._check_entry_is_resource(entry)
    except ValueError:
      return
    if entry.get_resource_type() == gdata.docs.data.COLLECTION_LABEL:
      raise ValueError(
          '%s is a collection, which is not valid in this method' % str(entry))

  def get_acl_entry(self, entry, **kwargs):
    """Retrieves an AclEntry again.
    
    This is useful if you need to poll for an ACL changing.
    
    Args:
      entry: gdata.docs.data.AclEntry to fetch and return.
      kwargs: Other args to pass to GetAclEntryBySelfLink().
    Returns:
      gdata.docs.data.AclEntry representing retrieved entry.
    """

    return self.GetAclEntryBySelfLink(entry.GetSelfLink().href, **kwargs)

  GetAclEntry = get_acl_entry

  def get_acl_entry_by_self_link(self, self_link, **kwargs):
    """Retrieves a particular AclEntry by its self link.

    Args:
      self_link: URI at which to query for given ACL entry.  This can be found
          using entry.GetSelfLink().
      kwargs: Other parameters to pass to self.get_entry().

    Returns:
      gdata.docs.data.AclEntry representing the retrieved entry.
    """
    if isinstance(self_link, atom.data.Link):
      self_link = self_link.href

    return self.get_entry(self_link, desired_class=gdata.docs.data.AclEntry,
                          **kwargs)

  GetAclEntryBySelfLink = get_acl_entry_by_self_link

  def add_acl_entry(self, resource, acl_entry, send_notifications=None,
                    **kwargs):
    """Adds the given AclEntry to the given Resource.

    Args:
      resource: gdata.docs.data.Resource to which to add AclEntry.
      acl_entry: gdata.docs.data.AclEntry representing ACL entry to add.
      send_notifications: True if users should be notified by email when
          this AclEntry is added.
      kwargs: Other parameters to pass to self.post().

    Returns:
      gdata.docs.data.AclEntry containing information about new entry.
    Raises:
      ValueError: If given resource has no ACL link.
    """
    uri = resource.GetAclLink().href
    if uri is None:
      raise ValueError(('Given resource has no ACL link.  Did you fetch this'
                        'resource from the API?'))
    if send_notifications is not None:
      if send_notifications:
        uri += '?send-notification-emails=true'

    return self.post(acl_entry, uri, desired_class=gdata.docs.data.AclEntry,
                     **kwargs)

  AddAclEntry = add_acl_entry

  def update_acl_entry(self, entry, send_notifications=None, **kwargs):
    """Updates the given AclEntry with new metadata.

    Args:
      entry: AclEntry to update. Make any metadata changes to this entry.
      send_notifications: True if users should be notified by email when
          this AclEntry is updated.
      kwargs: Other parameters to pass to super(DocsClient, self).update().

    Returns:
      gdata.docs.data.AclEntry representing the updated ACL entry.
    """
    uri = entry.GetEditLink().href
    if send_notifications:
      uri += '?send-notification-emails=true'
    return super(DocsClient, self).update(entry, uri=uri, force=True, **kwargs)

  UpdateAclEntry = update_acl_entry

  def delete_acl_entry(self, entry, **kwargs):
    """Deletes the given AclEntry.
    
    Args:
      entry: gdata.docs.data.AclEntry to delete.
      kwargs: Other args to pass to gdata.client.GDClient.Delete()
    
    Returns:
      Result of delete request.
    """
    return super(DocsClient, self).delete(entry.GetEditLink().href, force=True,
                                          **kwargs)

  DeleteAclEntry = delete_acl_entry

  def batch_process_acl_entries(self, resource, entries, **kwargs):
    """Applies the specified operation of each entry in a single request.

    To use this, simply set acl_entry.batch_operation to one of
    ['query', 'insert', 'update', 'delete'], and optionally set
    acl_entry.batch_id to a string of your choice.

    Then, put all of your modified AclEntry objects into a list and pass
    that list as the entries parameter.
    
    Args:
      resource: gdata.docs.data.Resource to which the given entries belong.
      entries: [gdata.docs.data.AclEntry] to modify in some way.
      kwargs: Other args to pass to gdata.client.GDClient.post()
    
    Returns:
      Resulting gdata.docs.data.AclFeed of changes.
    """
    feed = gdata.docs.data.AclFeed()
    feed.entry = entries
    return super(DocsClient, self).post(
        feed, uri=resource.GetAclLink().href + '/acl', force=True, **kwargs)

  BatchProcessAclEntries = batch_process_acl_entries

  def get_revisions(self, entry, **kwargs):
    """Retrieves the revision history for a resource.

    Args:
      entry: gdata.docs.data.Resource for which to get revisions.
      kwargs: Other parameters to pass to self.get_feed().

    Returns:
      gdata.docs.data.RevisionFeed representing the resource's revisions.
    """
    self._check_entry_is_resource(entry)
    return self.get_feed(
        entry.GetRevisionsFeedLink().href,
        desired_class=gdata.docs.data.RevisionFeed, **kwargs)

  GetRevisions = get_revisions

  def get_revision(self, entry, **kwargs):
    """Retrieves a revision again given its entry.
    
    Args:
      entry: gdata.docs.data.Revision to fetch and return.
      kwargs: Other args to pass to GetRevisionBySelfLink().
    Returns:
      gdata.docs.data.Revision representing retrieved revision.
    """
    return self.GetRevisionBySelfLink(entry.GetSelfLink().href, **kwargs)

  GetRevision = get_revision

  def get_revision_by_self_link(self, self_link, **kwargs):
    """Retrieves a particular reivision by its self link.

    Args:
      self_link: URI at which to query for given revision.  This can be found
          using entry.GetSelfLink().
      kwargs: Other parameters to pass to self.get_entry().

    Returns:
      gdata.docs.data.Revision representing the retrieved revision.
    """
    if isinstance(self_link, atom.data.Link):
      self_link = self_link.href

    return self.get_entry(self_link, desired_class=gdata.docs.data.Revision,
                          **kwargs)

  GetRevisionBySelfLink = get_revision_by_self_link

  def download_revision(self, entry, file_path, extra_params=None, **kwargs):
    """Downloads the contents of the given revision to disk.

    Note: to download a revision in memory, use the DownloadRevisionToMemory()
    method.

    Args:
      entry: gdata.docs.data.Revision whose contents to fetch.
      file_path: str Full path to which to save file.
      extra_params: dict (optional) A map of any further parameters to control
          how the document is downloaded.
      kwargs: Other parameters to pass to self._download_file().

    Raises:
      gdata.client.RequestError if the download URL is malformed or the server's
      response was not successful.
    """
    uri = self._get_download_uri(entry.content.src, extra_params)
    self._download_file(uri, file_path, **kwargs)

  DownloadRevision = download_revision

  def download_revision_to_memory(self, entry, extra_params=None, **kwargs):
    """Returns the contents of the given revision.

    Args:
      entry: gdata.docs.data.Revision whose contents to fetch.
      extra_params: dict (optional) A map of any further parameters to control
          how the document is downloaded/exported.
      kwargs: Other parameters to pass to self._get_content().

    Returns:
      Content of given revision after being downloaded.

    Raises:
      gdata.client.RequestError if the download URL is malformed or the server's
      response was not successful.
    """
    self._check_entry_is_not_collection(entry)
    uri = self._get_download_uri(entry.content.src, extra_params)
    return self._get_content(uri, **kwargs)

  DownloadRevisionToMemory = download_revision_to_memory

  def publish_revision(self, entry, publish_auto=None,
                       publish_outside_domain=False, **kwargs):
    """Publishes the given revision.

    This method can only be used for document revisions.

    Args:
      entry: Revision to update.
      publish_auto: True to automatically publish future revisions of the
          document.  False to not automatically publish future revisions.
          None to take no action and use the default value.
      publish_outside_domain: True to make the published revision available
          outside of a Google Apps domain.  False to not publish outside
          the domain.  None to use the default value.
      kwargs: Other parameters to pass to super(DocsClient, self).update().

    Returns:
      gdata.docs.data.Revision representing the updated revision.
    """
    entry.publish = gdata.docs.data.Publish(value='true')
    if publish_auto == True:
      entry.publish_auto = gdata.docs.data.PublishAuto(value='true')
    elif publish_auto == False:
      entry.publish_auto = gdata.docs.data.PublishAuto(value='false')
    if publish_outside_domain == True:
      entry.publish_outside_domain = \
          gdata.docs.data.PublishOutsideDomain(value='true')
    elif publish_outside_domain == False:
      entry.publish_outside_domain = \
          gdata.docs.data.PublishOutsideDomain(value='false')
    return super(DocsClient, self).update(entry, force=True, **kwargs)

  PublishRevision = publish_revision

  def unpublish_revision(self, entry, **kwargs):
    """Unpublishes the given revision.

    This method can only be used for document revisions.

    Args:
      entry: Revision to update.
      kwargs: Other parameters to pass to super(DocsClient, self).update().

    Returns:
      gdata.docs.data.Revision representing the updated revision.
    """
    entry.publish = gdata.docs.data.Publish(value='false')
    return super(DocsClient, self).update(entry, force=True, **kwargs)

  UnpublishRevision = unpublish_revision

  def delete_revision(self, entry, **kwargs):
    """Deletes the given Revision.
    
    Args:
      entry: gdata.docs.data.Revision to delete.
      kwargs: Other args to pass to gdata.client.GDClient.Delete()
    
    Returns:
      Result of delete request.
    """
    return super(DocsClient, self).delete(entry, force=True, **kwargs)

  DeleteRevision = delete_revision

  def get_archive(self, entry, **kwargs):
    """Retrieves an archive again given its entry.
    
    This is useful if you need to poll for an archive completing.
    
    Args:
      entry: gdata.docs.data.Archive to fetch and return.
      kwargs: Other args to pass to GetArchiveBySelfLink().
    Returns:
      gdata.docs.data.Archive representing retrieved archive.
    """

    return self.GetArchiveBySelfLink(entry.GetSelfLink().href, **kwargs)

  GetArchive = get_archive

  def get_archive_by_self_link(self, self_link, **kwargs):
    """Retrieves a particular archive by its self link.

    Args:
      self_link: URI at which to query for given archive.  This can be found
          using entry.GetSelfLink().
      kwargs: Other parameters to pass to self.get_entry().

    Returns:
      gdata.docs.data.Archive representing the retrieved archive.
    """
    if isinstance(self_link, atom.data.Link):
      self_link = self_link.href

    return self.get_entry(self_link, desired_class=gdata.docs.data.Archive,
                          **kwargs)

  GetArchiveBySelfLink = get_archive_by_self_link

  def create_archive(self, entry, **kwargs):
    """Creates a new archive of resources.

    Args:
      entry: gdata.docs.data.Archive representing metadata of archive to
          create.
      kwargs: Other parameters to pass to self.post().

    Returns:
      gdata.docs.data.Archive containing information about new archive.
    """
    return self.post(entry, ARCHIVE_FEED_URI,
                     desired_class=gdata.docs.data.Archive, **kwargs)

  CreateArchive = create_archive

  def update_archive(self, entry, **kwargs):
    """Updates the given Archive with new metadata.

    This method is really only useful for updating the notification email
    address of an archive that is being processed.

    Args:
      entry: Archive to update. Make any metadata changes to this entry.
      kwargs: Other parameters to pass to super(DocsClient, self).update().

    Returns:
      gdata.docs.data.Archive representing the updated archive.
    """
    return super(DocsClient, self).update(entry, **kwargs)

  UpdateArchive = update_archive

  download_archive = DownloadResource
  DownloadArchive = download_archive
  download_archive_to_memory = DownloadResourceToMemory
  DownloadArchiveToMemory = download_archive_to_memory

  def delete_archive(self, entry, **kwargs):
    """Aborts the given Archive operation, or deletes the Archive.
    
    Args:
      entry: gdata.docs.data.Archive to delete.
      kwargs: Other args to pass to gdata.client.GDClient.Delete()
    
    Returns:
      Result of delete request.
    """
    return super(DocsClient, self).delete(entry, force=True, **kwargs)

  DeleteArchive = delete_archive


class DocsQuery(gdata.client.Query):

  def __init__(self, title=None, title_exact=None, opened_min=None,
               opened_max=None, edited_min=None, edited_max=None, owner=None,
               writer=None, reader=None, show_collections=None, show_root=None,
               show_deleted=None, ocr=None, target_language=None,
               source_language=None, convert=None, query=None, **kwargs):
    """Constructs a query URL for the Google Documents List API.

    Args:
      title: str (optional) Specifies the search terms for the title of a
          document. This parameter used without title_exact will only
          submit partial queries, not exact queries.
      title_exact: str (optional) Meaningless without title. Possible values
          are 'true' and 'false'. Note: Matches are case-insensitive.
      opened_min: str (optional) Lower bound on the last time a document was
          opened by the current user. Use the RFC 3339 timestamp
          format. For example: opened_min='2005-08-09T09:57:00-08:00'.
      opened_max: str (optional) Upper bound on the last time a document was
          opened by the current user. (See also opened_min.)
      edited_min: str (optional) Lower bound on the last time a document was
          edited by the current user. This value corresponds to the edited.text
          value in the doc's entry object, which represents changes to the
          document's content or metadata.  Use the RFC 3339 timestamp format.
          For example: edited_min='2005-08-09T09:57:00-08:00'
      edited_max: str (optional) Upper bound on the last time a document was
          edited by the user. (See also edited_min.)
      owner: str (optional) Searches for documents with a specific owner. Use
          the email address of the owner. For example: owner='user@gmail.com'
      writer: str (optional) Searches for documents which can be written to
          by specific users. Use a single email address or a comma separated list
          of email addresses. For example: writer='user1@gmail.com,user@example.com'
      reader: str (optional) Searches for documents which can be read by
          specific users. (See also writer.)
      show_collections: str (optional) Specifies whether the query should return
          collections as well as documents and files. Possible values are 'true'
          and 'false'. Default is 'false'.
      show_root: (optional) 'true' to specify when an item is in the root
          collection. Default is 'false'
      show_deleted: str (optional) Specifies whether the query should return
          documents which are in the trash as well as other documents.
          Possible values are 'true' and 'false'. Default is false.
      ocr: str (optional) Specifies whether to attempt OCR on a .jpg, .png, or
          .gif upload. Possible values are 'true' and 'false'. Default is
          false. See OCR in the Protocol Guide: 
          http://code.google.com/apis/documents/docs/3.0/developers_guide_protocol.html#OCR
      target_language: str (optional) Specifies the language to translate a
          document into. See Document Translation in the Protocol Guide for a
          table of possible values:
            http://code.google.com/apis/documents/docs/3.0/developers_guide_protocol.html#DocumentTranslation
      source_language: str (optional) Specifies the source language of the
          original document. Optional when using the translation service.
          If not provided, Google will attempt to auto-detect the source
          language. See Document Translation in the Protocol Guide for a table of
          possible values (link in target_language).
      convert: str (optional) Used when uploading files specify if document uploads
          should convert to a native Google Docs format.
          Possible values are 'true' and 'false'. The default is 'true'.
      query: str (optional) Full-text query to use.  See the 'q' parameter in
          the documentation.
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.convert = convert
    self.title = title
    self.title_exact = title_exact
    self.opened_min = opened_min
    self.opened_max = opened_max
    self.edited_min = edited_min
    self.edited_max = edited_max
    self.owner = owner
    self.writer = writer
    self.reader = reader
    self.show_collections = show_collections
    self.show_root = show_root
    self.show_deleted = show_deleted
    self.ocr = ocr
    self.target_language = target_language
    self.source_language = source_language
    self.query = query

  def modify_request(self, http_request):
    gdata.client._add_query_param('convert', self.convert, http_request)
    gdata.client._add_query_param('title', self.title, http_request)
    gdata.client._add_query_param('title-exact', self.title_exact,
                                  http_request)
    gdata.client._add_query_param('opened-min', self.opened_min, http_request)
    gdata.client._add_query_param('opened-max', self.opened_max, http_request)
    gdata.client._add_query_param('edited-min', self.edited_min, http_request)
    gdata.client._add_query_param('edited-max', self.edited_max, http_request)
    gdata.client._add_query_param('owner', self.owner, http_request)
    gdata.client._add_query_param('writer', self.writer, http_request)
    gdata.client._add_query_param('reader', self.reader, http_request)
    gdata.client._add_query_param('query', self.query, http_request)
    gdata.client._add_query_param('showfolders', self.show_collections,
                                  http_request)
    gdata.client._add_query_param('showroot', self.show_root, http_request)
    gdata.client._add_query_param('showdeleted', self.show_deleted,
                                  http_request)
    gdata.client._add_query_param('ocr', self.ocr, http_request)
    gdata.client._add_query_param('targetLanguage', self.target_language,
                                  http_request)
    gdata.client._add_query_param('sourceLanguage', self.source_language,
                                  http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request
