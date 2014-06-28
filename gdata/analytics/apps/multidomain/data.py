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

"""Data model classes for the Multidomain Provisioning API."""


__author__ = 'Claudio Cherubino <ccherubino@google.com>'


import gdata.apps
import gdata.apps_property
import gdata.data


# This is required to work around a naming conflict between the Google
# Spreadsheets API and Python's built-in property function
pyproperty = property


# The apps:property firstName of a user entry
USER_FIRST_NAME = 'firstName'
# The apps:property lastName of a user entry
USER_LAST_NAME = 'lastName'
# The apps:property userEmail of a user entry
USER_EMAIL = 'userEmail'
# The apps:property password of a user entry
USER_PASSWORD = 'password'
# The apps:property hashFunction of a user entry
USER_HASH_FUNCTION = 'hashFunction'
# The apps:property isChangePasswordAtNextLogin of a user entry
USER_CHANGE_PASSWORD = 'isChangePasswordAtNextLogin'
# The apps:property agreedToTerms of a user entry
USER_AGREED_TO_TERMS = 'agreedToTerms'
# The apps:property isSuspended of a user entry
USER_SUSPENDED = 'isSuspended'
# The apps:property isAdmin of a user entry
USER_ADMIN = 'isAdmin'
# The apps:property ipWhitelisted of a user entry
USER_IP_WHITELISTED = 'ipWhitelisted'
# The apps:property quotaInGb of a user entry
USER_QUOTA = 'quotaInGb'

# The apps:property newEmail of a user rename request entry
USER_NEW_EMAIL = 'newEmail'

# The apps:property aliasEmail of an alias entry
ALIAS_EMAIL = 'aliasEmail'


class MultidomainProvisioningEntry(gdata.data.GDEntry):
  """Represents a Multidomain Provisioning entry in object form."""

  property = [gdata.apps_property.AppsProperty]

  def _GetProperty(self, name):
    """Get the apps:property value with the given name.

    Args:
      name: string Name of the apps:property value to get.

    Returns:
      The apps:property value with the given name, or None if the name was
      invalid.
    """
    value = None
    for p in self.property:
      if p.name == name:
        value = p.value
        break
    return value

  def _SetProperty(self, name, value):
    """Set the apps:property value with the given name to the given value.

    Args:
      name: string Name of the apps:property value to set.
      value: string Value to give the apps:property value with the given name.
    """
    found = False
    for i in range(len(self.property)):
      if self.property[i].name == name:
        self.property[i].value = value
        found = True
        break
    if not found:
      self.property.append(
          gdata.apps_property.AppsProperty(name=name, value=value))


class UserEntry(MultidomainProvisioningEntry):
  """Represents an User in object form."""

  def GetFirstName(self):
    """Get the first name of the User object.

    Returns:
      The first name of this User object as a string or None.
    """
    return self._GetProperty(USER_FIRST_NAME)

  def SetFirstName(self, value):
    """Set the first name of this User object.

    Args:
      value: string The new first name to give this object.
    """
    self._SetProperty(USER_FIRST_NAME, value)

  first_name = pyproperty(GetFirstName, SetFirstName)

  def GetLastName(self):
    """Get the last name of the User object.

    Returns:
      The last name of this User object as a string or None.
    """
    return self._GetProperty(USER_LAST_NAME)

  def SetLastName(self, value):
    """Set the last name of this User object.

    Args:
      value: string The new last name to give this object.
    """
    self._SetProperty(USER_LAST_NAME, value)

  last_name = pyproperty(GetLastName, SetLastName)

  def GetEmail(self):
    """Get the email address of the User object.

    Returns:
      The email address of this User object as a string or None.
    """
    return self._GetProperty(USER_EMAIL)

  def SetEmail(self, value):
    """Set the email address of this User object.

    Args:
      value: string The new email address to give this object.
    """
    self._SetProperty(USER_EMAIL, value)

  email = pyproperty(GetEmail, SetEmail)

  def GetPassword(self):
    """Get the password of the User object.

    Returns:
      The password of this User object as a string or None.
    """
    return self._GetProperty(USER_PASSWORD)

  def SetPassword(self, value):
    """Set the password of this User object.

    Args:
      value: string The new password to give this object.
    """
    self._SetProperty(USER_PASSWORD, value)

  password = pyproperty(GetPassword, SetPassword)

  def GetHashFunction(self):
    """Get the hash function of the User object.

    Returns:
      The hash function of this User object as a string or None.
    """
    return self._GetProperty(USER_HASH_FUNCTION)

  def SetHashFunction(self, value):
    """Set the hash function of this User object.

    Args:
      value: string The new hash function to give this object.
    """
    self._SetProperty(USER_HASH_FUNCTION, value)

  hash_function = pyproperty(GetHashFunction, SetHashFunction)

  def GetChangePasswordAtNextLogin(self):
    """Get the change password at next login flag of the User object.

    Returns:
      The change password at next login flag of this User object as a string or
      None.
    """
    return self._GetProperty(USER_CHANGE_PASSWORD)

  def SetChangePasswordAtNextLogin(self, value):
    """Set the change password at next login flag of this User object.

    Args:
      value: string The new change password at next login flag to give this
      object.
    """
    self._SetProperty(USER_CHANGE_PASSWORD, value)

  change_password_at_next_login = pyproperty(GetChangePasswordAtNextLogin,
                                             SetChangePasswordAtNextLogin)

  def GetAgreedToTerms(self):
    """Get the agreed to terms flag of the User object.

    Returns:
      The agreed to terms flag of this User object as a string or None.
    """
    return self._GetProperty(USER_AGREED_TO_TERMS)

  agreed_to_terms = pyproperty(GetAgreedToTerms)

  def GetSuspended(self):
    """Get the suspended flag of the User object.

    Returns:
      The suspended flag of this User object as a string or None.
    """
    return self._GetProperty(USER_SUSPENDED)

  def SetSuspended(self, value):
    """Set the suspended flag of this User object.

    Args:
      value: string The new suspended flag to give this object.
    """
    self._SetProperty(USER_SUSPENDED, value)

  suspended = pyproperty(GetSuspended, SetSuspended)

  def GetIsAdmin(self):
    """Get the isAdmin flag of the User object.

    Returns:
      The isAdmin flag of this User object as a string or None.
    """
    return self._GetProperty(USER_ADMIN)

  def SetIsAdmin(self, value):
    """Set the isAdmin flag of this User object.

    Args:
      value: string The new isAdmin flag to give this object.
    """
    self._SetProperty(USER_ADMIN, value)

  is_admin = pyproperty(GetIsAdmin, SetIsAdmin)

  def GetIpWhitelisted(self):
    """Get the ipWhitelisted flag of the User object.

    Returns:
      The ipWhitelisted flag of this User object as a string or None.
    """
    return self._GetProperty(USER_IP_WHITELISTED)

  def SetIpWhitelisted(self, value):
    """Set the ipWhitelisted flag of this User object.

    Args:
      value: string The new ipWhitelisted flag to give this object.
    """
    self._SetProperty(USER_IP_WHITELISTED, value)

  ip_whitelisted = pyproperty(GetIpWhitelisted, SetIpWhitelisted)

  def GetQuota(self):
    """Get the quota of the User object.

    Returns:
      The quota of this User object as a string or None.
    """
    return self._GetProperty(USER_QUOTA)

  def SetQuota(self, value):
    """Set the quota of this User object.

    Args:
      value: string The new quota to give this object.
    """
    self._SetProperty(USER_QUOTA, value)

  quota = pyproperty(GetQuota, GetQuota)

  def __init__(self, uri=None, email=None, first_name=None, last_name=None,
               password=None, hash_function=None, change_password=None,
               agreed_to_terms=None, suspended=None, is_admin=None,
               ip_whitelisted=None, quota=None, *args, **kwargs):
    """Constructs a new UserEntry object with the given arguments.

    Args:
      uri: string (optional) The uri of of this object for HTTP requests.
      email: string (optional) The email address of the user.
      first_name: string (optional) The first name of the user.
      last_name: string (optional) The last name of the user.
      password: string (optional) The password of the user.
      hash_function: string (optional) The name of the function used to hash the
          password.
      change_password: Boolean (optional) Whether or not the user must change
          password at first login.
      agreed_to_terms: Boolean (optional) Whether or not the user has agreed to
          the Terms of Service.
      suspended: Boolean (optional) Whether or not the user is suspended.
      is_admin: Boolean (optional) Whether or not the user has administrator
          privileges.
      ip_whitelisted: Boolean (optional) Whether or not the user's ip is
          whitelisted.
      quota: string (optional) The value (in GB) of the user's quota.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(UserEntry, self).__init__(*args, **kwargs)
    if uri:
      self.uri = uri
    if email:
      self.email = email
    if first_name:
      self.first_name = first_name
    if last_name:
      self.last_name = last_name
    if password:
      self.password = password
    if hash_function:
      self.hash_function = hash_function
    if change_password is not None:
      self.change_password = str(change_password)
    if agreed_to_terms is not None:
      self.agreed_to_terms = str(agreed_to_terms)
    if suspended is not None:
      self.suspended = str(suspended)
    if is_admin is not None:
      self.is_admin = str(is_admin)
    if ip_whitelisted is not None:
      self.ip_whitelisted = str(ip_whitelisted)
    if quota:
      self.quota = quota


class UserFeed(gdata.data.GDFeed):
  """Represents a feed of UserEntry objects."""

  # Override entry so that this feed knows how to type its list of entries.
  entry = [UserEntry]


class UserRenameRequest(MultidomainProvisioningEntry):
  """Represents an User rename request in object form."""

  def GetNewEmail(self):
    """Get the new email address for the User object.

    Returns:
      The new email address for the User object as a string or None.
    """
    return self._GetProperty(USER_NEW_EMAIL)

  def SetNewEmail(self, value):
    """Set the new email address for the User object.

    Args:
      value: string The new email address to give this object.
    """
    self._SetProperty(USER_NEW_EMAIL, value)

  new_email = pyproperty(GetNewEmail, SetNewEmail)

  def __init__(self, new_email=None, *args, **kwargs):
    """Constructs a new UserRenameRequest object with the given arguments.

    Args:
      new_email: string (optional) The new email address for the target user.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(UserRenameRequest, self).__init__(*args, **kwargs)
    if new_email:
      self.new_email = new_email


class AliasEntry(MultidomainProvisioningEntry):
  """Represents an Alias in object form."""

  def GetUserEmail(self):
    """Get the user email address of the Alias object.

    Returns:
      The user email address of this Alias object as a string or None.
    """
    return self._GetProperty(USER_EMAIL)

  def SetUserEmail(self, value):
    """Set the user email address of this Alias object.

    Args:
      value: string The new user email address to give this object.
    """
    self._SetProperty(USER_EMAIL, value)

  user_email = pyproperty(GetUserEmail, SetUserEmail)

  def GetAliasEmail(self):
    """Get the alias email address of the Alias object.

    Returns:
      The alias email address of this Alias object as a string or None.
    """
    return self._GetProperty(ALIAS_EMAIL)

  def SetAliasEmail(self, value):
    """Set the alias email address of this Alias object.

    Args:
      value: string The new alias email address to give this object.
    """
    self._SetProperty(ALIAS_EMAIL, value)

  alias_email = pyproperty(GetAliasEmail, SetAliasEmail)

  def __init__(self, user_email=None, alias_email=None, *args, **kwargs):
    """Constructs a new AliasEntry object with the given arguments.

    Args:
      user_email: string (optional) The user email address for the object.
      alias_email: string (optional) The alias email address for the object.
      args: The other parameters to pass to gdata.entry.GDEntry constructor.
      kwargs: The other parameters to pass to gdata.entry.GDEntry constructor.
    """
    super(AliasEntry, self).__init__(*args, **kwargs)
    if user_email:
      self.user_email = user_email
    if alias_email:
      self.alias_email = alias_email


class AliasFeed(gdata.data.GDFeed):
  """Represents a feed of AliasEntry objects."""

  # Override entry so that this feed knows how to type its list of entries.
  entry = [AliasEntry]
