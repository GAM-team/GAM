#!/usr/bin/python
#
# Copyright (C) 2008 Google, Inc.
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

"""Allow Google Apps domain administrators to set domain admin settings.

  AdminSettingsService: Set admin settings."""

__author__ = 'jlee@pbu.edu'


import gdata.apps
import gdata.apps.service
import gdata.service


API_VER='2.0'

class AdminSettingsService(gdata.apps.service.PropertyService):
  """Client for the Google Apps Admin Settings service."""

  def _serviceUrl(self, setting_id, domain=None):
    if domain is None:
      domain = self.domain
    return '/a/feeds/domain/%s/%s/%s' % (API_VER, domain, setting_id)

  def genericGet(self, location):
    """Generic HTTP Get Wrapper

    Args:
      location: relative uri to Get

    Returns:
      A dict containing the result of the get operation."""

    uri = self._serviceUrl(location)
    try:
      return self._GetProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])

  def GetDefaultLanguage(self):
    """Gets Domain Default Language

    Args:
      None

    Returns:
      Default Language as a string.  All possible values are listed at:
        http://code.google.com/apis/apps/email_settings/developers_guide_protocol.html#GA_email_language_tags"""

    result = self.genericGet('general/defaultLanguage')
    return result['defaultLanguage']

  def UpdateDefaultLanguage(self, defaultLanguage):
    """Updates Domain Default Language

    Args:
      defaultLanguage: Domain Language to set
        possible values are at:
        http://code.google.com/apis/apps/email_settings/developers_guide_protocol.html#GA_email_language_tags

    Returns:
      A dict containing the result of the put operation"""

    uri = self._serviceUrl('general/defaultLanguage')
    properties = {'defaultLanguage': defaultLanguage}
    return self._PutProperties(uri, properties)

  def GetOrganizationName(self):
    """Gets Domain Default Language

    Args:
      None

    Returns:
      Organization Name as a string."""

    result = self.genericGet('general/organizationName')
    return result['organizationName']


  def UpdateOrganizationName(self, organizationName):
    """Updates Organization Name

    Args:
      organizationName: Name of organization

    Returns:
      A dict containing the result of the put operation"""

    uri = self._serviceUrl('general/organizationName')
    properties = {'organizationName': organizationName}
    return self._PutProperties(uri, properties)

  def GetMaximumNumberOfUsers(self):
    """Gets Maximum Number of Users Allowed

    Args:
      None

    Returns: An integer, the maximum number of users"""

    result = self.genericGet('general/maximumNumberOfUsers')
    return int(result['maximumNumberOfUsers'])

  def GetCurrentNumberOfUsers(self):
    """Gets Current Number of Users

    Args:
      None

    Returns: An integer, the current number of users"""

    result = self.genericGet('general/currentNumberOfUsers')
    return int(result['currentNumberOfUsers'])

  def IsDomainVerified(self):
    """Is the domain verified

    Args:
      None

    Returns: Boolean, is domain verified"""

    result = self.genericGet('accountInformation/isVerified')
    if result['isVerified'] == 'true':
      return True
    else:
      return False

  def GetSupportPIN(self):
    """Gets Support PIN

    Args:
      None

    Returns: A string, the Support PIN"""

    result = self.genericGet('accountInformation/supportPIN')
    return result['supportPIN']

  def GetEdition(self):
    """Gets Google Apps Domain Edition

    Args:
      None

    Returns: A string, the domain's edition (premier, education, partner)"""

    result = self.genericGet('accountInformation/edition')
    return result['edition']

  def GetCustomerPIN(self):
    """Gets Customer PIN

    Args:
      None

    Returns: A string, the customer PIN"""

    result = self.genericGet('accountInformation/customerPIN')
    return result['customerPIN']

  def GetCreationTime(self):
    """Gets Domain Creation Time

    Args:
      None

    Returns: A string, the domain's creation time"""

    result = self.genericGet('accountInformation/creationTime')
    return result['creationTime']

  def GetCountryCode(self):
    """Gets Domain Country Code

    Args:
      None

    Returns: A string, the domain's country code. Possible values at:
      http://www.iso.org/iso/country_codes/iso_3166_code_lists/english_country_names_and_code_elements.htm"""

    result = self.genericGet('accountInformation/countryCode')
    return result['countryCode']

  def GetAdminSecondaryEmail(self):
    """Gets Domain Admin Secondary Email Address

    Args:
      None

    Returns: A string, the secondary email address for domain admin"""

    result = self.genericGet('accountInformation/adminSecondaryEmail')
    return result['adminSecondaryEmail']

  def UpdateAdminSecondaryEmail(self, adminSecondaryEmail):
    """Gets Domain Creation Time

    Args:
      adminSecondaryEmail: string, secondary email address of admin

    Returns: A dict containing the result of the put operation"""

    uri = self._serviceUrl('accountInformation/adminSecondaryEmail')
    properties = {'adminSecondaryEmail': adminSecondaryEmail}
    return self._PutProperties(uri, properties)

  def GetDomainLogo(self):
    """Gets Domain Logo

    This function does not make use of the Google Apps Admin Settings API,
    it does an HTTP Get of a url specific to the Google Apps domain. It is
    included for completeness sake.

    Args:
      None

    Returns: binary image file"""
 
    import urllib
    url = 'http://www.google.com/a/cpanel/'+self.domain+'/images/logo.gif'
    response = urllib.urlopen(url)
    return response.read()

  def UpdateDomainLogo(self, logoImage):
    """Update Domain's Custom Logo

    Args:
      logoImage: binary image data

    Returns: A dict containing the result of the put operation"""

    from base64 import base64encode
    uri = self._serviceUrl('appearance/customLogo')
    properties = {'logoImage': base64encode(logoImage)}
    return self._PutProperties(uri, properties)

  def GetCNAMEVerificationStatus(self):
    """Gets Domain CNAME Verification Status

    Args:
      None

    Returns: A dict {recordName, verified, verifiedMethod}"""

    return self.genericGet('verification/cname')

  def UpdateCNAMEVerificationStatus(self, verified):
    """Updates CNAME Verification Status

    Args:
      verified: boolean, True will retry verification process

    Returns: A dict containing the result of the put operation"""

    uri = self._serviceUrl('verification/cname')
    properties = self.GetCNAMEVerificationStatus()
    properties['verified'] = verified
    return self._PutProperties(uri, properties)

  def GetMXVerificationStatus(self):
    """Gets Domain MX Verification Status

    Args:
      None

    Returns: A dict {verified, verifiedMethod}"""

    return self.genericGet('verification/mx')

  def UpdateMXVerificationStatus(self, verified):
    """Updates MX Verification Status

    Args:
      verified: boolean, True will retry verification process

    Returns: A dict containing the result of the put operation"""

    uri = self._serviceUrl('verification/mx')
    properties = self.GetMXVerificationStatus()
    properties['verified'] = verified
    return self._PutProperties(uri, properties)

  def GetSSOSettings(self):
    """Gets Domain Single Sign-On Settings

    Args:
      None

    Returns: A dict {samlSignonUri, samlLogoutUri, changePasswordUri, enableSSO, ssoWhitelist, useDomainSpecificIssuer}"""

    return self.genericGet('sso/general')

  def UpdateSSOSettings(self, enableSSO=None, samlSignonUri=None,
                        samlLogoutUri=None, changePasswordUri=None,
                        ssoWhitelist=None, useDomainSpecificIssuer=None):
    """Update SSO Settings.

    Args:
      enableSSO: boolean, SSO Master on/off switch
      samlSignonUri: string, SSO Login Page
      samlLogoutUri: string, SSO Logout Page
      samlPasswordUri: string, SSO Password Change Page
      ssoWhitelist: string, Range of IP Addresses which will see SSO
      useDomainSpecificIssuer: boolean, Include Google Apps Domain in Issuer

    Returns:
      A dict containing the result of the update operation.
    """
    uri = self._serviceUrl('sso/general')

    #Get current settings, replace Nones with ''
    properties = self.GetSSOSettings()
    if properties['samlSignonUri'] == None:
      properties['samlSignonUri'] = ''
    if properties['samlLogoutUri'] == None:
      properties['samlLogoutUri'] = ''
    if properties['changePasswordUri'] == None:
      properties['changePasswordUri'] = ''
    if properties['ssoWhitelist'] == None:
      properties['ssoWhitelist'] = ''

    #update only the values we were passed
    if enableSSO != None:
      properties['enableSSO'] = gdata.apps.service._bool2str(enableSSO)
    if samlSignonUri != None:
      properties['samlSignonUri'] = samlSignonUri
    if samlLogoutUri != None:
      properties['samlLogoutUri'] = samlLogoutUri
    if changePasswordUri != None:
      properties['changePasswordUri'] = changePasswordUri
    if ssoWhitelist != None:
      properties['ssoWhitelist'] = ssoWhitelist
    if useDomainSpecificIssuer != None:
      properties['useDomainSpecificIssuer'] = gdata.apps.service._bool2str(useDomainSpecificIssuer)

    return self._PutProperties(uri, properties)

  def GetSSOKey(self):
    """Gets Domain Single Sign-On Signing Key

    Args:
      None

    Returns: A dict {modulus, exponent, algorithm, format}"""

    return self.genericGet('sso/signingkey')

  def UpdateSSOKey(self, signingKey):
    """Update SSO Settings.

    Args:
      signingKey: string, public key to be uploaded

    Returns:
      A dict containing the result of the update operation."""

    uri = self._serviceUrl('sso/signingkey')
    properties = {'signingKey': signingKey}
    return self._PutProperties(uri, properties)

  def IsUserMigrationEnabled(self):
    """Is User Migration Enabled

    Args:
      None

    Returns:
      boolean, is user migration enabled"""

    result = self.genericGet('email/migration')
    if result['enableUserMigration'] == 'true':
      return True
    else:
      return False

  def UpdateUserMigrationStatus(self, enableUserMigration):
    """Update User Migration Status

    Args:
      enableUserMigration: boolean, user migration enable/disable

    Returns:
      A dict containing the result of the update operation."""

    uri = self._serviceUrl('email/migration')
    properties = {'enableUserMigration': enableUserMigration}
    return self._PutProperties(uri, properties)

  def GetOutboundGatewaySettings(self):
    """Get Outbound Gateway Settings

    Args:
      None

    Returns:
      A dict {smartHost, smtpMode}"""

    uri = self._serviceUrl('email/gateway')
    try:
      return self._GetProperties(uri)
    except gdata.service.RequestError, e:
      raise AppsForYourDomainException(e.args[0])
    except TypeError:
      #if no outbound gateway is set, we get a TypeError,
      #catch it and return nothing...
      return {'smartHost': None, 'smtpMode': None}

  def UpdateOutboundGatewaySettings(self, smartHost=None, smtpMode=None):
    """Update Outbound Gateway Settings

    Args:
      smartHost: string, ip address or hostname of outbound gateway
      smtpMode: string, SMTP or SMTP_TLS

    Returns:
      A dict containing the result of the update operation."""

    uri = self._serviceUrl('email/gateway')

    #Get current settings, replace Nones with ''
    properties = GetOutboundGatewaySettings()
    if properties['smartHost'] == None:
      properties['smartHost'] = ''
    if properties['smtpMode'] == None:
      properties['smtpMode'] = ''

    #If we were passed new values for smartHost or smtpMode, update them
    if smartHost != None:
      properties['smartHost'] = smartHost
    if smtpMode != None:
      properties['smtpMode'] = smtpMode

    return self._PutProperties(uri, properties)

  def AddEmailRoute(self, routeDestination, routeRewriteTo, routeEnabled, bounceNotifications, accountHandling):
    """Adds Domain Email Route

    Args:
      routeDestination: string, destination ip address or hostname
      routeRewriteTo: boolean, rewrite smtp envelop To:
      routeEnabled: boolean, enable disable email routing
      bounceNotifications: boolean, send bound notificiations to sender
      accountHandling: string, which to route, "allAccounts", "provisionedAccounts", "unknownAccounts"

    Returns:
      A dict containing the result of the update operation."""

    uri = self._serviceUrl('emailrouting')
    properties = {}
    properties['routeDestination'] = routeDestination
    properties['routeRewriteTo'] = gdata.apps.service._bool2str(routeRewriteTo)
    properties['routeEnabled'] = gdata.apps.service._bool2str(routeEnabled)
    properties['bounceNotifications'] = gdata.apps.service._bool2str(bounceNotifications)
    properties['accountHandling'] = accountHandling
    return self._PostProperties(uri, properties)
