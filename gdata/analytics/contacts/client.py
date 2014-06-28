#!/usr/bin/env python
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
from types import ListType, DictionaryType


"""Contains a client to communicate with the Contacts servers.

For documentation on the Contacts API, see:
http://code.google.com/apis/contatcs/
"""

__author__ = 'vinces1979@gmail.com (Vince Spicer)'


import gdata.client
import gdata.contacts.data
import atom.client
import atom.data
import atom.http_core
import gdata.gauth

DEFAULT_BATCH_URL = ('https://www.google.com/m8/feeds/contacts/default/full'
                     '/batch')
DEFAULT_PROFILES_BATCH_URL = ('https://www.google.com/m8/feeds/profiles/domain/'
                              '%s/full/batch')

class ContactsClient(gdata.client.GDClient):
  api_version = '3'
  auth_service = 'cp'
  server = "www.google.com"
  contact_list = "default"
  auth_scopes = gdata.gauth.AUTH_SCOPES['cp']
  ssl = True


  def __init__(self, domain=None, auth_token=None, **kwargs):
    """Constructs a new client for the Email Settings API.

    Args:
      domain: string The Google Apps domain (if any).
      kwargs: The other parameters to pass to the gdata.client.GDClient
          constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.domain = domain

  def get_feed_uri(self, kind='contacts', contact_list=None, projection='full',
                  scheme="https"):
    """Builds a feed URI.

    Args:
      kind: The type of feed to return, typically 'groups' or 'contacts'.
        Default value: 'contacts'.
      contact_list: The contact list to return a feed for.
        Default value: self.contact_list.
      projection: The projection to apply to the feed contents, for example
        'full', 'base', 'base/12345', 'full/batch'. Default value: 'full'.
      scheme: The URL scheme such as 'http' or 'https', None to return a
          relative URI without hostname.

    Returns:
      A feed URI using the given kind, contact list, and projection.
      Example: '/m8/feeds/contacts/default/full'.
    """
    contact_list = contact_list or self.contact_list
    if kind == 'profiles':
      contact_list = 'domain/%s' % self.domain
    prefix = scheme and '%s://%s' % (scheme, self.server) or ''
    return '%s/m8/feeds/%s/%s/%s' % (prefix, kind, contact_list, projection)

  GetFeedUri = get_feed_uri

  def get_contact(self, uri, desired_class=gdata.contacts.data.ContactEntry,
                  auth_token=None, **kwargs):
    return self.get_entry(uri, auth_token=auth_token,
                          desired_class=desired_class, **kwargs)


  GetContact = get_contact


  def create_contact(self, new_contact, insert_uri=None,  auth_token=None,  **kwargs):
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
    insert_uri = insert_uri or self.GetFeedUri()
    return self.Post(new_contact, insert_uri,
                     auth_token=auth_token,  **kwargs)

  CreateContact = create_contact

  def add_contact(self, new_contact, insert_uri=None, auth_token=None,
                  billing_information=None, birthday=None, calendar_link=None, **kwargs):
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

    contact = gdata.contacts.data.ContactEntry()

    if billing_information is not None:
      if not isinstance(billing_information, gdata.contacts.data.BillingInformation):
        billing_information = gdata.contacts.data.BillingInformation(text=billing_information)

      contact.billing_information = billing_information

    if birthday is not None:
      if not isinstance(birthday, gdata.contacts.data.Birthday):
        birthday = gdata.contacts.data.Birthday(when=birthday)

      contact.birthday = birthday

    if calendar_link is not None:
      if type(calendar_link) is not ListType:
        calendar_link = [calendar_link]

      for link in calendar_link:
        if not isinstance(link, gdata.contacts.data.CalendarLink):
          if type(link) is not DictionaryType:
            raise TypeError, "calendar_link Requires dictionary not %s" % type(link)

          link = gdata.contacts.data.CalendarLink(
                                                  rel=link.get("rel", None),
                                                  label=link.get("label", None),
                                                  primary=link.get("primary", None),
                                                  href=link.get("href", None),
                                                  )

        contact.calendar_link.append(link)

    insert_uri = insert_uri or self.GetFeedUri()
    return self.Post(contact, insert_uri,
                     auth_token=auth_token,  **kwargs)

  AddContact = add_contact

  def get_contacts(self, uri=None, desired_class=gdata.contacts.data.ContactsFeed,
                   auth_token=None, **kwargs):
    """Obtains a feed with the contacts belonging to the current user.

    Args:
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.spreadsheets.data.SpreadsheetsFeed.
    """
    uri = uri or self.GetFeedUri()
    return self.get_feed(uri, auth_token=auth_token,
                         desired_class=desired_class, **kwargs)

  GetContacts = get_contacts

  def get_group(self, uri=None, desired_class=gdata.contacts.data.GroupEntry,
                auth_token=None, **kwargs):
    """ Get a single groups details
    Args:
        uri:  the group uri or id
    """
    return self.get_entry(uri, desired_class=desired_class, auth_token=auth_token, **kwargs)

  GetGroup = get_group

  def get_groups(self, uri=None, desired_class=gdata.contacts.data.GroupsFeed,
                 auth_token=None, **kwargs):
    uri = uri or self.GetFeedUri('groups')
    return self.get_feed(uri, desired_class=desired_class, auth_token=auth_token, **kwargs)

  GetGroups = get_groups

  def create_group(self, new_group, insert_uri=None, url_params=None,
                   desired_class=None, **kwargs):
    insert_uri = insert_uri or self.GetFeedUri('groups')
    return self.Post(new_group, insert_uri, url_params=url_params,
                     desired_class=desired_class, **kwargs)

  CreateGroup = create_group

  def update_group(self, edit_uri, updated_group, url_params=None,
                   escape_params=True, desired_class=None, auth_token=None, **kwargs):
    return self.Put(updated_group, self._CleanUri(edit_uri),
                    url_params=url_params,
                    escape_params=escape_params,
                    desired_class=desired_class,
                    auth_token=auth_token, **kwargs)

  UpdateGroup = update_group

  def delete_group(self, group_object, auth_token=None, force=False, **kws):
    return self.Delete(group_object, auth_token=auth_token, force=force, **kws)

  DeleteGroup = delete_group

  def change_photo(self, media, contact_entry_or_url, content_type=None,
                   content_length=None, auth_token=None, **kwargs):
    """Change the photo for the contact by uploading a new photo.

    Performs a PUT against the photo edit URL to send the binary data for the
    photo.

    Args:
      media: filename, file-like-object, or a gdata.data.MediaSource object to send.
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
    """
    ifmatch_header = None
    if isinstance(contact_entry_or_url, gdata.contacts.data.ContactEntry):
      photo_link = contact_entry_or_url.GetPhotoLink()
      uri = photo_link.href
      ifmatch_header = atom.client.CustomHeaders(
          **{'if-match': photo_link.etag})
    else:
      uri = contact_entry_or_url
    if isinstance(media, gdata.data.MediaSource):
      payload = media
    # If the media object is a file-like object, then use it as the file
    # handle in the in the MediaSource.
    elif hasattr(media, 'read'):
      payload = gdata.data.MediaSource(file_handle=media,
          content_type=content_type, content_length=content_length)
    # Assume that the media object is a file name.
    else:
      payload = gdata.data.MediaSource(content_type=content_type,
          content_length=content_length, file_path=media)
    return self.Put(uri=uri, data=payload, auth_token=auth_token,
                    ifmatch_header=ifmatch_header, **kwargs)

  ChangePhoto = change_photo

  def get_photo(self, contact_entry_or_url, auth_token=None, **kwargs):
    """Retrives the binary data for the contact's profile photo as a string.

    Args:
      contact_entry_or_url: a gdata.contacts.ContactEntry object or a string
         containing the photo link's URL. If the contact entry does not
         contain a photo link, the image will not be fetched and this method
         will return None.
    """
    # TODO: add the ability to write out the binary image data to a file,
    # reading and writing a chunk at a time to avoid potentially using up
    # large amounts of memory.
    url = None
    if isinstance(contact_entry_or_url, gdata.contacts.data.ContactEntry):
      photo_link = contact_entry_or_url.GetPhotoLink()
      if photo_link:
        url = photo_link.href
    else:
      url = contact_entry_or_url
    if url:
      return self.Get(url, auth_token=auth_token, **kwargs).read()
    else:
      return None

  GetPhoto = get_photo

  def delete_photo(self, contact_entry_or_url, auth_token=None, **kwargs):
    """Delete the contact's profile photo.

    Args:
      contact_entry_or_url: a gdata.contacts.ContactEntry object or a string
         containing the photo link's URL.
    """
    uri = None
    ifmatch_header = None
    if isinstance(contact_entry_or_url, gdata.contacts.data.ContactEntry):
      photo_link = contact_entry_or_url.GetPhotoLink()
      if photo_link.etag:
        uri = photo_link.href
        ifmatch_header = atom.client.CustomHeaders(
            **{'if-match': photo_link.etag})
      else:
        # No etag means no photo has been assigned to this contact.
        return
    else:
      uri = contact_entry_or_url
    if uri:
      self.Delete(entry_or_uri=uri, auth_token=auth_token,
                  ifmatch_header=ifmatch_header, **kwargs)

  DeletePhoto = delete_photo

  def get_profiles_feed(self, uri=None, auth_token=None, **kwargs):
    """Retrieves a feed containing all domain's profiles.

    Args:
      uri: string (optional) the URL to retrieve the profiles feed,
          for example /m8/feeds/profiles/default/full

    Returns:
      On success, a ProfilesFeed containing the profiles.
      On failure, raises a RequestError.
    """

    uri = uri or self.GetFeedUri('profiles')
    return self.get_feed(uri, auth_token=auth_token,
                         desired_class=gdata.contacts.data.ProfilesFeed, **kwargs)

  GetProfilesFeed = get_profiles_feed

  def get_profile(self, uri, auth_token=None, **kwargs):
    """Retrieves a domain's profile for the user.

    Args:
      uri: string the URL to retrieve the profiles feed,
          for example /m8/feeds/profiles/default/full/username

    Returns:
      On success, a ProfileEntry containing the profile for the user.
      On failure, raises a RequestError
    """
    return self.get_entry(uri,
                          desired_class=gdata.contacts.data.ProfileEntry,
                          auth_token=auth_token, **kwargs)

  GetProfile = get_profile

  def update_profile(self, updated_profile, auth_token=None, force=False, **kwargs):
    """Updates an existing profile.

    Args:
      updated_profile: atom.Entry or subclass containing
                       the Atom Entry which will replace the profile which is
                       stored at the edit_url.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of ContactsClient.
      force: boolean stating whether an update should be forced. Defaults to
             False. Normally, if a change has been made since the passed in
             entry was obtained, the server will not overwrite the entry since
             the changes were based on an obsolete version of the entry.
             Setting force to True will cause the update to silently
             overwrite whatever version is present.
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful update,  a httplib.HTTPResponse containing the server's
        response to the PUT request.
      On failure, raises a RequestError.
    """
    return self.Update(updated_profile, auth_token=auth_token, force=force, **kwargs)

  UpdateProfile = update_profile

  def execute_batch(self, batch_feed, url=DEFAULT_BATCH_URL, desired_class=None,
                    auth_token=None, **kwargs):
    """Sends a batch request feed to the server.

    Args:
      batch_feed: gdata.contacts.ContactFeed A feed containing batch
          request entries. Each entry contains the operation to be performed
          on the data contained in the entry. For example an entry with an
          operation type of insert will be used as if the individual entry
          had been inserted.
      url: str The batch URL to which these operations should be applied.
      converter: Function (optional) The function used to convert the server's
          response to an object.

    Returns:
      The results of the batch request's execution on the server. If the
      default converter is used, this is stored in a ContactsFeed.
    """
    return self.Post(batch_feed, url, desired_class=desired_class,
                     auth_token=None, **kwargs)

  ExecuteBatch = execute_batch

  def execute_batch_profiles(self, batch_feed, url=None,
                             desired_class=gdata.contacts.data.ProfilesFeed,
                             auth_token=None, **kwargs):
    """Sends a batch request feed to the server.

    Args:
      batch_feed: gdata.profiles.ProfilesFeed A feed containing batch
          request entries. Each entry contains the operation to be performed
          on the data contained in the entry. For example an entry with an
          operation type of insert will be used as if the individual entry
          had been inserted.
      url: string The batch URL to which these operations should be applied.
      converter: Function (optional) The function used to convert the server's
          response to an object. The default value is
          gdata.profiles.ProfilesFeedFromString.

    Returns:
      The results of the batch request's execution on the server. If the
      default converter is used, this is stored in a ProfilesFeed.
    """
    url = url or (DEFAULT_PROFILES_BATCH_URL % self.domain)
    return self.Post(batch_feed, url, desired_class=desired_class,
                     auth_token=auth_token, **kwargs)

  ExecuteBatchProfiles = execute_batch_profiles

  def _CleanUri(self, uri):
    """Sanitizes a feed URI.

    Args:
      uri: The URI to sanitize, can be relative or absolute.

    Returns:
      The given URI without its http://server prefix, if any.
      Keeps the leading slash of the URI.
    """
    url_prefix = 'http://%s' % self.server
    if uri.startswith(url_prefix):
      uri = uri[len(url_prefix):]
    return uri

class ContactsQuery(gdata.client.Query):
  """
  Create a custom Contacts Query

  Full specs can be found at: U{Contacts query parameters reference
  <http://code.google.com/apis/contacts/docs/3.0/reference.html#Parameters>}
  """

  def __init__(self, feed=None, group=None, orderby=None, showdeleted=None,
               sortorder=None, requirealldeleted=None, **kwargs):
    """
    @param max_results: The maximum number of entries to return. If you want
        to receive all of the contacts, rather than only the default maximum, you
        can specify a very large number for max-results.
    @param start-index: The 1-based index of the first result to be retrieved.
    @param updated-min: The lower bound on entry update dates.
    @param group: Constrains the results to only the contacts belonging to the
        group specified. Value of this parameter specifies group ID
    @param orderby:  Sorting criterion. The only supported value is
        lastmodified.
    @param showdeleted: Include deleted contacts in the returned contacts feed
    @pram sortorder: Sorting order direction. Can be either ascending or
        descending.
    @param requirealldeleted: Only relevant if showdeleted and updated-min
        are also provided. It dictates the behavior of the server in case it
        detects that placeholders of some entries deleted since the point in
        time specified as updated-min may have been lost.
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.group = group
    self.orderby = orderby
    self.sortorder = sortorder
    self.showdeleted = showdeleted

  def modify_request(self, http_request):
    if self.group:
      gdata.client._add_query_param('group', self.group, http_request)
    if self.orderby:
      gdata.client._add_query_param('orderby', self.orderby, http_request)
    if self.sortorder:
      gdata.client._add_query_param('sortorder', self.sortorder, http_request)
    if self.showdeleted:
      gdata.client._add_query_param('showdeleted', self.showdeleted, http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request


class ProfilesQuery(gdata.client.Query):
  """
  Create a custom Profiles Query

  Full specs can be found at: U{Profiless query parameters reference
  <http://code.google.com/apis/apps/profiles/reference.html#Parameters>}
  """

  def __init__(self, feed=None, start_key=None, **kwargs):
    """
    @param start_key: Opaque key of the first element to retrieve. Present in
        the next link of an earlier request, if further pages of response are
        available.
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.feed = feed or 'https://www.google.com/m8/feeds/profiles/default/full'
    self.start_key = start_key

  def modify_request(self, http_request):
    if self.start_key:
      gdata.client._add_query_param('start-key', self.start_key, http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request
