#!/usr/bin/python2.4
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MultiDomainProvisioningClient simplifies Multidomain Provisioning API calls.

MultiDomainProvisioningClient extends gdata.client.GDClient to ease interaction
with the Google Multidomain Provisioning API.  These interactions include the
ability to create, retrieve, update and delete users and aliases in multiple
domains.
"""


__author__ = 'Claudio Cherubino <ccherubino@google.com>'


import urllib
import gdata.apps.multidomain.data
import gdata.client


# Multidomain URI templates
# The strings in this template are eventually replaced with the feed type
# (user/alias), API version and Google Apps domain name, respectively.
MULTIDOMAIN_URI_TEMPLATE = '/a/feeds/%s/%s/%s'
# The strings in this template are eventually replaced with the API version,
# Google Apps domain name and old email address, respectively.
MULTIDOMAIN_USER_RENAME_URI_TEMPLATE = '/a/feeds/user/userEmail/%s/%s/%s'

# The value for user requests
MULTIDOMAIN_USER_FEED = 'user'
# The value for alias requests
MULTIDOMAIN_ALIAS_FEED = 'alias'


class MultiDomainProvisioningClient(gdata.client.GDClient):
  """Client extension for the Google MultiDomain Provisioning API service.

  Attributes:
    host: string The hostname for the MultiDomain Provisioning API service.
    api_version: string The version of the MultiDomain Provisioning API.
  """

  host = 'apps-apis.google.com'
  api_version = '2.0'
  auth_service = 'apps'
  auth_scopes = gdata.gauth.AUTH_SCOPES['apps']
  ssl = True

  def __init__(self, domain, auth_token=None, **kwargs):
    """Constructs a new client for the MultiDomain Provisioning API.

    Args:
      domain: string The Google Apps domain with MultiDomain Provisioning.
      auth_token: (optional) gdata.gauth.ClientLoginToken, AuthSubToken, or
          OAuthToken which authorizes this client to edit the email settings.
      kwargs: The other parameters to pass to the gdata.client.GDClient
          constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.domain = domain

  def make_multidomain_provisioning_uri(
      self, feed_type, email=None, params=None):

    """Creates a resource feed URI for the MultiDomain Provisioning API.

    Using this client's Google Apps domain, create a feed URI for multidomain
    provisioning in that domain. If an email address is provided, return a
    URI for that specific resource.  If params are provided, append them as GET
    params.

    Args:
      feed_type: string The type of feed (user/alias)
      email: string (optional) The email address of multidomain resource for
          which to make a feed URI.
      params: dict (optional) key -> value params to append as GET vars to the
          URI. Example: params={'start': 'my-resource-id'}

    Returns:
      A string giving the URI for multidomain provisioning for this client's
          Google Apps domain.
    """
    uri = MULTIDOMAIN_URI_TEMPLATE % (feed_type, self.api_version, self.domain)
    if email:
      uri += '/' + email
    if params:
      uri += '?' + urllib.urlencode(params)
    return uri

  MakeMultidomainProvisioningUri = make_multidomain_provisioning_uri

  def make_multidomain_user_provisioning_uri(self, email=None, params=None):
    """Creates a resource feed URI for the MultiDomain User Provisioning API.

    Using this client's Google Apps domain, create a feed URI for multidomain
    user provisioning in that domain. If an email address is provided, return a
    URI for that specific resource.  If params are provided, append them as GET
    params.

    Args:
      email: string (optional) The email address of multidomain user for which
          to make a feed URI.
      params: dict (optional) key -> value params to append as GET vars to the
          URI. Example: params={'start': 'my-resource-id'}

    Returns:
      A string giving the URI for multidomain user provisioning for thisis that
      client's Google Apps domain.
    """
    return self.make_multidomain_provisioning_uri(
        MULTIDOMAIN_USER_FEED, email, params)

  MakeMultidomainUserProvisioningUri = make_multidomain_user_provisioning_uri

  def make_multidomain_alias_provisioning_uri(self, email=None, params=None):
    """Creates a resource feed URI for the MultiDomain Alias Provisioning API.

    Using this client's Google Apps domain, create a feed URI for multidomain
    alias provisioning in that domain. If an email address is provided, return a
    URI for that specific resource.  If params are provided, append them as GET
    params.

    Args:
      email: string (optional) The email address of multidomain alias for which
          to make a feed URI.
      params: dict (optional) key -> value params to append as GET vars to the
          URI. Example: params={'start': 'my-resource-id'}

    Returns:
      A string giving the URI for multidomain alias provisioning for this
      client's Google Apps domain.
    """
    return self.make_multidomain_provisioning_uri(
        MULTIDOMAIN_ALIAS_FEED, email, params)

  MakeMultidomainAliasProvisioningUri = make_multidomain_alias_provisioning_uri

  def retrieve_all_users(self, **kwargs):
    """Retrieves all users in all domains.

    Args:
      kwargs: The other parameters to pass to gdata.client.GDClient.GetFeed()

    Returns:
      A gdata.data.GDFeed of the domain users
    """
    uri = self.MakeMultidomainUserProvisioningUri()
    return self.GetFeed(
        uri,
        desired_class=gdata.apps.multidomain.data.UserFeed,
        **kwargs)

  RetrieveAllUsers = retrieve_all_users

  def retrieve_user(self, email, **kwargs):
    """Retrieves a single user in the domain.

    Args:
      email: string The email address of the user to be retrieved
      kwargs: The other parameters to pass to gdata.client.GDClient.GetEntry()

    Returns:
      A gdata.apps.multidomain.data.UserEntry representing the user
    """
    uri = self.MakeMultidomainUserProvisioningUri(email=email)
    return self.GetEntry(
        uri,
        desired_class=gdata.apps.multidomain.data.UserEntry,
        **kwargs)

  RetrieveUser = retrieve_user

  def create_user(self, email, first_name, last_name, password, is_admin,
                  hash_function=None, suspended=None, change_password=None,
                  ip_whitelisted=None, quota=None, **kwargs):
    """Creates an user in the domain with the given properties.

    Args:
      email: string The email address of the user.
      first_name: string The first name of the user.
      last_name: string The last name of the user.
      password: string The password of the user.
      is_admin: Boolean Whether or not the user has administrator privileges.
      hash_function: string (optional) The name of the function used to hash the
          password.
      suspended: Boolean (optional) Whether or not the user is suspended.
      change_password: Boolean (optional) Whether or not the user must change
          password at first login.
      ip_whitelisted: Boolean (optional) Whether or not the user's ip is
          whitelisted.
      quota: string (optional) The value (in GB) of the user's quota.
      kwargs: The other parameters to pass to gdata.client.GDClient.post().

    Returns:
      A gdata.apps.multidomain.data.UserEntry of the new user
    """
    new_user = gdata.apps.multidomain.data.UserEntry(
        email=email, first_name=first_name, last_name=last_name,
        password=password, is_admin=is_admin, hash_function=hash_function,
        suspended=suspended, change_password=change_password,
        ip_whitelisted=ip_whitelisted, quota=quota)
    return self.post(new_user, self.MakeMultidomainUserProvisioningUri(),
                     **kwargs)

  CreateUser = create_user

  def update_user(self, email, user_entry, **kwargs):
    """Deletes the user with the given email address.

    Args:
      email: string The email address of the user to be updated.
      user_entry: UserEntry The user entry with updated values.
      kwargs: The other parameters to pass to gdata.client.GDClient.put()

    Returns:
      A gdata.apps.multidomain.data.UserEntry representing the user
    """
    return self.update(user_entry,
                       uri=self.MakeMultidomainUserProvisioningUri(email),
                       **kwargs)

  UpdateUser = update_user

  def delete_user(self, email, **kwargs):
    """Deletes the user with the given email address.

    Args:
      email: string The email address of the user to delete.
      kwargs: The other parameters to pass to gdata.client.GDClient.delete()

    Returns:
      An HTTP response object.  See gdata.client.request().
    """
    return self.delete(self.MakeMultidomainUserProvisioningUri(email), **kwargs)

  DeleteUser = delete_user

  def rename_user(self, old_email, new_email, **kwargs):
    """Renames an user's account to a different domain.

    Args:
      old_email: string The old email address of the user to rename.
      new_email: string The new email address for the user to be renamed.
      kwargs: The other parameters to pass to gdata.client.GDClient.put()

    Returns:
      A gdata.apps.multidomain.data.UserRenameRequest representing the request.
    """
    rename_uri = MULTIDOMAIN_USER_RENAME_URI_TEMPLATE % (self.api_version,
                                                         self.domain,
                                                         old_email)
    entry = gdata.apps.multidomain.data.UserRenameRequest(new_email)
    return self.update(entry, uri=rename_uri, **kwargs)

  RenameUser = rename_user

  def retrieve_all_aliases(self, **kwargs):
    """Retrieves all aliases in the domain.

    Args:
      kwargs: The other parameters to pass to gdata.client.GDClient.GetFeed()

    Returns:
      A gdata.data.GDFeed of the domain aliases
    """
    uri = self.MakeMultidomainAliasProvisioningUri()
    return self.GetFeed(
        uri,
        desired_class=gdata.apps.multidomain.data.AliasFeed,
        **kwargs)

  RetrieveAllAliases = retrieve_all_aliases

  def retrieve_alias(self, email, **kwargs):
    """Retrieves a single alias in the domain.

    Args:
      email: string The email address of the alias to be retrieved
      kwargs: The other parameters to pass to gdata.client.GDClient.GetEntry()

    Returns:
      A gdata.apps.multidomain.data.AliasEntry representing the alias
    """
    uri = self.MakeMultidomainAliasProvisioningUri(email=email)
    return self.GetEntry(
        uri,
        desired_class=gdata.apps.multidomain.data.AliasEntry,
        **kwargs)

  RetrieveAlias = retrieve_alias

  def create_alias(self, user_email, alias_email, **kwargs):
    """Creates an alias in the domain with the given properties.

    Args:
      user_email: string The email address of the user.
      alias_email: string The first name of the user.
      kwargs: The other parameters to pass to gdata.client.GDClient.post().

    Returns:
      A gdata.apps.multidomain.data.AliasEntry of the new alias
    """
    new_alias = gdata.apps.multidomain.data.AliasEntry(
        user_email=user_email, alias_email=alias_email)
    return self.post(new_alias, self.MakeMultidomainAliasProvisioningUri(),
                     **kwargs)

  CreateAlias = create_alias

  def delete_alias(self, email, **kwargs):
    """Deletes the alias with the given email address.

    Args:
      email: string The email address of the alias to delete.
      kwargs: The other parameters to pass to gdata.client.GDClient.delete()

    Returns:
      An HTTP response object.  See gdata.client.request().
    """
    return self.delete(self.MakeMultidomainAliasProvisioningUri(email),
                       **kwargs)

  DeleteAlias = delete_alias
