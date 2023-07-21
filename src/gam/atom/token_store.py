#
# Copyright (C) 2008 Google Inc.
#
# Licensed under the Apache License 2.0;


"""This module provides a TokenStore class which is designed to manage
auth tokens required for different services.

Each token is valid for a set of scopes which is the start of a URL. An HTTP
client will use a token store to find a valid Authorization header to send
in requests to the specified URL. If the HTTP client determines that a token
has expired or been revoked, it can remove the token from the store so that
it will not be used in future requests.
"""

# __author__ = 'api.jscudder (Jeff Scudder)'

import atom.http_interface
import atom.url

SCOPE_ALL = 'http'


class TokenStore(object):
    """Manages Authorization tokens which will be sent in HTTP headers."""

    def __init__(self, scoped_tokens=None):
        self._tokens = scoped_tokens or {}

    def add_token(self, token):
        """Adds a new token to the store (replaces tokens with the same scope).

        Args:
          token: A subclass of http_interface.GenericToken. The token object is
              responsible for adding the Authorization header to the HTTP request.
              The scopes defined in the token are used to determine if the token
              is valid for a requested scope when find_token is called.

        Returns:
          True if the token was added, False if the token was not added becase
          no scopes were provided.
        """
        if not hasattr(token, 'scopes') or not token.scopes:
            return False

        for scope in token.scopes:
            self._tokens[str(scope)] = token
        return True

    def find_token(self, url):
        """Selects an Authorization header token which can be used for the URL.

        Args:
          url: str or atom.url.Url or a list containing the same.
              The URL which is going to be requested. All
              tokens are examined to see if any scopes begin match the beginning
              of the URL. The first match found is returned.

        Returns:
          The token object which should execute the HTTP request. If there was
          no token for the url (the url did not begin with any of the token
          scopes available), then the atom.http_interface.GenericToken will be
          returned because the GenericToken calls through to the http client
          without adding an Authorization header.
        """
        if url is None:
            return None
        if isinstance(url, str):
            url = atom.url.parse_url(url)
        if url in self._tokens:
            token = self._tokens[url]
            if token.valid_for_scope(url):
                return token
            else:
                del self._tokens[url]
        for scope, token in self._tokens.items():
            if token.valid_for_scope(url):
                return token
        return atom.http_interface.GenericToken()

    def remove_token(self, token):
        """Removes the token from the token_store.

        This method is used when a token is determined to be invalid. If the
        token was found by find_token, but resulted in a 401 or 403 error stating
        that the token was invlid, then the token should be removed to prevent
        future use.

        Returns:
          True if a token was found and then removed from the token
          store. False if the token was not in the TokenStore.
        """
        token_found = False
        scopes_to_delete = []
        for scope, stored_token in self._tokens.items():
            if stored_token == token:
                scopes_to_delete.append(scope)
                token_found = True
        for scope in scopes_to_delete:
            del self._tokens[scope]
        return token_found

    def remove_all_tokens(self):
        self._tokens = {}
