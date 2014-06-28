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


"""Provides utility functions used with command line samples."""

# This module is used for version 2 of the Google Data APIs.

import sys
import getpass
import urllib
import gdata.gauth

__author__ = 'j.s@google.com (Jeff Scudder)'


CLIENT_LOGIN = 1
AUTHSUB = 2
OAUTH = 3

HMAC = 1
RSA = 2


class SettingsUtil(object):
  """Gather's user preferences from flags or command prompts.

  An instance of this object stores the choices made by the user. At some
  point it might be useful to save the user's preferences so that they do
  not need to always set flags or answer preference prompts.
  """

  def __init__(self, prefs=None):
    self.prefs = prefs or {}

  def get_param(self, name, prompt='', secret=False, ask=True, reuse=False):
    # First, check in this objects stored preferences.
    if name in self.prefs:
     return self.prefs[name]
    # Second, check for a command line parameter.
    value = None
    for i in xrange(len(sys.argv)):
      if sys.argv[i].startswith('--%s=' % name):
        value = sys.argv[i].split('=')[1]
      elif sys.argv[i] == '--%s' % name:
        value = sys.argv[i + 1]
    # Third, if it was not on the command line, ask the user to input the
    # value.
    if value is None and ask:
      prompt = '%s: ' % prompt
      if secret:
        value = getpass.getpass(prompt)
      else:
        value = raw_input(prompt)
    # If we want to save the preference for reuse in future requests, add it
    # to this object's prefs.
    if value is not None and reuse:
      self.prefs[name] = value
    return value

  def authorize_client(self, client, auth_type=None, service=None,
                       source=None, scopes=None, oauth_type=None,
                       consumer_key=None, consumer_secret=None):
    """Uses command line arguments, or prompts user for token values."""
    if 'client_auth_token' in self.prefs:
      return
    if auth_type is None:
      auth_type = int(self.get_param(
          'auth_type', 'Please choose the authorization mechanism you want'
          ' to use.\n'
          '1. to use your email address and password (ClientLogin)\n'
          '2. to use a web browser to visit an auth web page (AuthSub)\n'
          '3. if you have registed to use OAuth\n', reuse=True))

    # Get the scopes for the services we want to access.
    if auth_type == AUTHSUB or auth_type == OAUTH:
      if scopes is None:
        scopes = self.get_param(
            'scopes', 'Enter the URL prefixes (scopes) for the resources you '
            'would like to access.\nFor multiple scope URLs, place a comma '
            'between each URL.\n'
            'Example: http://www.google.com/calendar/feeds/,'
            'http://www.google.com/m8/feeds/\n', reuse=True).split(',')
      elif isinstance(scopes, (str, unicode)):
        scopes = scopes.split(',')

    if auth_type == CLIENT_LOGIN:
      email = self.get_param('email', 'Please enter your username',
                             reuse=False)
      password = self.get_param('password', 'Password', True, reuse=False)
      if service is None:
        service = self.get_param(
            'service', 'What is the name of the service you wish to access?'
            '\n(See list:'
            ' http://code.google.com/apis/gdata/faq.html#clientlogin)',
            reuse=True)
      if source is None:
        source = self.get_param('source', ask=False, reuse=True)
      client.client_login(email, password, source=source, service=service)
    elif auth_type == AUTHSUB:
      auth_sub_token = self.get_param('auth_sub_token', ask=False, reuse=True)
      session_token = self.get_param('session_token', ask=False, reuse=True)
      private_key = None
      auth_url = None
      single_use_token = None
      rsa_private_key = self.get_param(
          'rsa_private_key',
          'If you want to use secure mode AuthSub, please provide the\n'
          ' location of your RSA private key which corresponds to the\n'
          ' certificate you have uploaded for your domain. If you do not\n'
          ' have an RSA key, simply press enter', reuse=True)

      if rsa_private_key:
        try:
          private_key_file = open(rsa_private_key, 'rb')
          private_key = private_key_file.read()
          private_key_file.close()
        except IOError:
          print 'Unable to read private key from file'

      if private_key is not None:
        if client.auth_token is None:
          if session_token:
            client.auth_token = gdata.gauth.SecureAuthSubToken(
                session_token, private_key, scopes)
            self.prefs['client_auth_token'] = gdata.gauth.token_to_blob(
                client.auth_token)
            return
          elif auth_sub_token:
            client.auth_token = gdata.gauth.SecureAuthSubToken(
                auth_sub_token, private_key, scopes)
            client.upgrade_token()
            self.prefs['client_auth_token'] = gdata.gauth.token_to_blob(
                client.auth_token)
            return

        auth_url = gdata.gauth.generate_auth_sub_url(
            'http://gauthmachine.appspot.com/authsub', scopes, True)
        print 'with a private key, get ready for this URL', auth_url

      else:
        if client.auth_token is None:
          if session_token:
            client.auth_token = gdata.gauth.AuthSubToken(session_token,
                                                         scopes)
            self.prefs['client_auth_token'] = gdata.gauth.token_to_blob(
                client.auth_token)
            return
          elif auth_sub_token:
            client.auth_token = gdata.gauth.AuthSubToken(auth_sub_token,
                                                         scopes)
            client.upgrade_token()
            self.prefs['client_auth_token'] = gdata.gauth.token_to_blob(
                client.auth_token)
            return

          auth_url = gdata.gauth.generate_auth_sub_url(
              'http://gauthmachine.appspot.com/authsub', scopes)

      print 'Visit the following URL in your browser to authorize this app:'
      print str(auth_url)
      print 'After agreeing to authorize the app, copy the token value from'
      print ' the URL. Example: "www.google.com/?token=ab12" token value is'
      print ' ab12'
      token_value = raw_input('Please enter the token value: ')
      if private_key is not None:
        single_use_token = gdata.gauth.SecureAuthSubToken(
            token_value, private_key, scopes)
      else:
        single_use_token = gdata.gauth.AuthSubToken(token_value, scopes)
      client.auth_token = single_use_token
      client.upgrade_token()

    elif auth_type == OAUTH:
      if oauth_type is None:
        oauth_type = int(self.get_param(
            'oauth_type', 'Please choose the authorization mechanism you want'
            ' to use.\n'
            '1. use an HMAC signature using your consumer key and secret\n'
            '2. use RSA with your private key to sign requests\n',
            reuse=True))

      consumer_key = self.get_param(
          'consumer_key', 'Please enter your OAuth conumer key '
          'which identifies your app', reuse=True)

      if oauth_type == HMAC:
        consumer_secret = self.get_param(
            'consumer_secret', 'Please enter your OAuth conumer secret '
            'which you share with the OAuth provider', True, reuse=False)
        # Swap out this code once the client supports requesting an oauth
        # token.
        # Get a request token.
        request_token = client.get_oauth_token(
            scopes, 'http://gauthmachine.appspot.com/oauth', consumer_key,
            consumer_secret=consumer_secret)
      elif oauth_type == RSA:
        rsa_private_key = self.get_param(
            'rsa_private_key',
            'Please provide the location of your RSA private key which\n'
            ' corresponds to the certificate you have uploaded for your'
            ' domain.',
            reuse=True)
        try:
          private_key_file = open(rsa_private_key, 'rb')
          private_key = private_key_file.read()
          private_key_file.close()
        except IOError:
          print 'Unable to read private key from file'

        request_token = client.get_oauth_token(
            scopes, 'http://gauthmachine.appspot.com/oauth', consumer_key,
            rsa_private_key=private_key)
      else:
        print 'Invalid OAuth signature type'
        return None

      # Authorize the request token in the browser.
      print 'Visit the following URL in your browser to authorize this app:'
      print str(request_token.generate_authorization_url())
      print 'After agreeing to authorize the app, copy URL from the browser\'s'
      print ' address bar.'
      url = raw_input('Please enter the url: ')
      gdata.gauth.authorize_request_token(request_token, url)
      # Exchange for an access token.
      client.auth_token = client.get_access_token(request_token)
    else:
      print 'Invalid authorization type.'
      return None
    if client.auth_token:
      self.prefs['client_auth_token'] = gdata.gauth.token_to_blob(
          client.auth_token)


def get_param(name, prompt='', secret=False, ask=True):
  settings = SettingsUtil()
  return settings.get_param(name=name, prompt=prompt, secret=secret, ask=ask)


def authorize_client(client, auth_type=None, service=None, source=None,
                     scopes=None, oauth_type=None, consumer_key=None,
                     consumer_secret=None):
  """Uses command line arguments, or prompts user for token values."""
  settings = SettingsUtil()
  return settings.authorize_client(client=client, auth_type=auth_type,
                                   service=service, source=source,
                                   scopes=scopes, oauth_type=oauth_type,
                                   consumer_key=consumer_key,
                                   consumer_secret=consumer_secret)


def print_options():
  """Displays usage information, available command line params."""
  # TODO: fill in the usage description for authorizing the client.
  print ''

