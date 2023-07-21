#!/usr/bin/env python
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

"""ContactsService extends the GDataService for Google Contacts operations.

  ContactsService: Provides methods to query feeds and manipulate items.
                   Extends GDataService.
"""


import gdata.apps
import gdata.apps.service
import gdata.service


class ContactsService(gdata.service.GDataService):
  """Client for the Google Contacts service."""

  def __init__(self, email=None, password=None, source=None,
               server='www.google.com', additional_headers=None,
               contact_list='default', contactFeed=True, **kwargs):
    """Creates a client for the Contacts service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'www.google.com'.
      contact_list: string (optional) The name of the default contact list to
          use when no URI is specified to the methods of the service.
          Default value: 'default' (the logged in user's contact list).
      contactFeed: Boolean (optional) Is this contacts feed or a gal feed
          Default value: True (the logged in user's contact list).
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """

    self.contact_list = contact_list
    self.feed_type = ['gal', 'contacts'][contactFeed]
    if additional_headers == None:
      additional_headers = {}
    additional_headers['GData-Version'] = ['1.1', '3.1'][contactFeed]
    gdata.service.GDataService.__init__(self,
                                        email=email, password=password, service='cp', source=source,
                                        server=server, additional_headers=additional_headers, **kwargs)
    self.ssl = True
    self.port = 443

  def _CleanUri(self, uri):
    """Sanitizes a feed URI.

    Args:
      uri: The URI to sanitize, can be relative or absolute.

    Returns:
      The given URI without its https://server prefix, if any.
      Keeps the leading slash of the URI.
    """
    url_prefix = 'https://%s' % self.server
    if uri.startswith(url_prefix):
      uri = uri[len(url_prefix):]
    return uri

  def GetContactFeedUri(self, contact_list=None, projection='full', contactId=None):
    """Builds a contact feed URI. """
    contact_list = contact_list or self.contact_list
    uri = 'https://{0}/m8/feeds/{1}/{2}/{3}'.format(self.server, self.feed_type, contact_list, projection)
    if contactId:
      uri += '/{0}'.format(contactId)
    return uri

  def GetContactsFeed(self, uri=None,
                      extra_headers=None, url_params=None, escape_params=True):
    uri = uri or self.GetContactFeedUri()
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.contacts.ContactsFeedFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def GetContact(self, uri):
    try:
      return self.Get(uri, converter=gdata.apps.contacts.ContactEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def CreateContact(self, new_contact, insert_uri=None, url_params=None,
                    escape_params=True):
    """Adds an new contact to Google Contacts.

    Args:
      new_contact: atom.Entry or subclass A new contact which is to be added to
                Google Contacts.
      insert_uri: the URL to post new contacts to the feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the contact created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server,
         'reason': HTTP reason from the server,
         'body': HTTP body of the server's response}
    """
    insert_uri = insert_uri or self.GetContactFeedUri()
    try:
      return self.Post(new_contact, insert_uri, url_params=url_params,
                       escape_params=escape_params,
                       converter=gdata.apps.contacts.ContactEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def UpdateContact(self, edit_uri, updated_contact, extra_headers=None, url_params=None,
                    escape_params=True):
    """Updates an existing contact.

    Args:
      edit_uri: string The edit link URI for the element being updated
      updated_contact: string, atom.Entry or subclass containing
                    the Atom Entry which will replace the contact which is
                    stored at the edit_url
      url_params: dict (optional) Additional URL parameters to be included
                  in the update request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful update,  a httplib.HTTPResponse containing the server's
        response to the PUT request.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server,
         'reason': HTTP reason from the server,
         'body': HTTP body of the server's response}
    """
    try:
      return self.Put(updated_contact, self._CleanUri(edit_uri),
                      url_params=url_params, extra_headers=extra_headers,
                      escape_params=escape_params,
                      converter=gdata.apps.contacts.ContactEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def DeleteContact(self, edit_uri, extra_headers=None,
                    url_params=None, escape_params=True):
    """Removes an contact with the specified ID from Google Contacts.

    Args:
      edit_uri: string The edit URL of the entry to be deleted. Example:
               '/m8/feeds/contacts/default/full/xxx/yyy'
      extra_headers: dict (optional)
      url_params: dict (optional) Additional URL parameters to be included
                  in the deletion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful delete,  a httplib.HTTPResponse containing the server's
        response to the DELETE request.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server,
         'reason': HTTP reason from the server,
         'body': HTTP body of the server's response}
    """
    try:
      return self.Delete(self._CleanUri(edit_uri),
                         url_params=url_params, escape_params=escape_params, extra_headers=extra_headers)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def ChangePhoto(self, media, contact_entry_or_url, content_type=None,
                  content_length=None, extra_headers=None):
    """Change the photo for the contact by uploading a new photo.

    Performs a PUT against the photo edit URL to send the binary data for the
    photo.

    Args:
      media: filename, file-like-object, or a gdata.MediaSource object to send.
      contact_entry_or_url: ContactEntry or str If it is a ContactEntry, this
                            method will search for an edit photo link URL and
                            perform a PUT to the URL.
      content_type: str (optional) the mime type for the photo data. This is
                    necessary if media is a file or file name, but if media
                    is a MediaSource object then the media object can contain
                    the mime type. If media_type is set, it will override the
                    mime type in the media object.
      content_length: int or str (optional) Specifying the content length is
                      only required if media is a file-like object. If media
                      is a filename, the length is determined using
                      os.path.getsize. If media is a MediaSource object, it is
                      assumed that it already contains the content length.
      extra_headers: dict (optional)
    """
    if isinstance(contact_entry_or_url, gdata.apps.contacts.ContactEntry):
#      url = contact_entry_or_url.GetPhotoEditLink().href
      url = contact_entry_or_url.GetPhotoLink().href
    else:
      url = contact_entry_or_url
    if isinstance(media, gdata.MediaSource):
      payload = media
    # If the media object is a file-like object, then use it as the file
    # handle in the in the MediaSource.
    elif hasattr(media, 'read'):
      payload = gdata.MediaSource(file_handle=media,
                                  content_type=content_type, content_length=content_length)
    # Assume that the media object is a file name.
    else:
      payload = gdata.MediaSource(content_type=content_type,
                                  content_length=content_length, file_path=media)
    return self.Put(payload, url, extra_headers=extra_headers)

  def GetPhoto(self, contact_entry_or_url):
    """Retrives the binary data for the contact's profile photo as a string.

    Args:
      contact_entry_or_url: a gdata.apps.contacts.ContactEntry object or a string
         containing the photo link's URL. If the contact entry does not
         contain a photo link, the image will not be fetched and this method
         will return None.
    """
    # TODO: add the ability to write out the binary image data to a file,
    # reading and writing a chunk at a time to avoid potentially using up
    # large amounts of memory.
    url = None
    if isinstance(contact_entry_or_url, gdata.apps.contacts.ContactEntry):
      photo_link = contact_entry_or_url.GetPhotoLink()
      if photo_link:
        url = photo_link.href
    else:
      url = contact_entry_or_url
    if url:
      try:
        return self.Get(url, converter=str)
      except gdata.service.RequestError as e:
        raise gdata.apps.service.AppsForYourDomainException(e.args[0])
    else:
      return None

  def DeletePhoto(self, contact_entry_or_url, extra_headers=None):
    """Deletes the contact's profile photo.

    Args:
      contact_entry_or_url: a gdata.apps.contacts.ContactEntry object or a string
         containing the photo link's URL.
         will return None.
      extra_headers: dict (optional)
    """
    url = None
    if isinstance(contact_entry_or_url, gdata.apps.contacts.ContactEntry):
#      url = contact_entry_or_url.GetPhotoEditLink().href
      url = contact_entry_or_url.GetPhotoLink().href
    else:
      url = contact_entry_or_url
    if url:
      self.Delete(url, extra_headers=extra_headers)

  def ExecuteBatch(self, batch_feed, url,
                   converter=gdata.apps.contacts.ContactsFeedFromString):
    """Sends a batch request feed to the server.

    Args:
      batch_feed: gdata.apps.contacts.ContactFeed A feed containing batch
          request entries. Each entry contains the operation to be performed
          on the data contained in the entry. For example an entry with an
          operation type of insert will be used as if the individual entry
          had been inserted.
      url: str The batch URL to which these operations should be applied.
      converter: Function (optional) The function used to convert the server's
          response to an object. The default value is ContactsFeedFromString.

    Returns:
      The results of the batch request's execution on the server. If the
      default converter is used, this is stored in a ContactsFeed.
    """
    return self.Post(batch_feed, url, converter=converter)

  def GetContactGroupFeedUri(self, contact_list=None, projection='full', groupId=None):
    """Builds a contact feed URI. """
    contact_list = contact_list or self.contact_list
    uri = 'https://{0}/m8/feeds/groups/{1}/{2}'.format(self.server, contact_list, projection)
    if groupId:
      uri += '/{0}'.format(groupId)
    return uri

  def GetGroupsFeed(self, uri=None,
                    extra_headers=None, url_params=None, escape_params=True):
    uri = uri or self.GetContactGroupFeedUri()
    try:
      return self.Get(uri,
                      url_params=url_params, extra_headers=extra_headers, escape_params=escape_params,
                      converter=gdata.apps.contacts.GroupsFeedFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def GetGroup(self, uri):
    try:
      return self.Get(uri, converter=gdata.apps.contacts.GroupEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def CreateGroup(self, new_group, insert_uri=None, url_params=None,
                  escape_params=True):
    insert_uri = insert_uri or self.GetContactGroupFeedUri()
    try:
      return self.Post(new_group, insert_uri, url_params=url_params,
                       escape_params=escape_params,
                       converter=gdata.apps.contacts.GroupEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def UpdateGroup(self, edit_uri, updated_group, extra_headers=None, url_params=None,
                  escape_params=True):
    try:
      return self.Put(updated_group, self._CleanUri(edit_uri),
                      url_params=url_params, extra_headers=extra_headers,
                      escape_params=escape_params,
                      converter=gdata.apps.contacts.GroupEntryFromString)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

  def DeleteGroup(self, edit_uri, extra_headers=None,
                  url_params=None, escape_params=True):
    try:
      return self.Delete(self._CleanUri(edit_uri),
                         url_params=url_params, escape_params=escape_params, extra_headers=extra_headers)
    except gdata.service.RequestError as e:
      raise gdata.apps.service.AppsForYourDomainException(e.args[0])

class ContactsQuery(gdata.service.Query):

  def __init__(self, feed=None, text_query=None, params=None,
               categories=None, group=None):
    self.feed = feed or '/m8/feeds/contacts/default/full'
    if group:
      self['group'] = group
    gdata.service.Query.__init__(self, feed=self.feed, text_query=text_query,
                                 params=params, categories=categories)
