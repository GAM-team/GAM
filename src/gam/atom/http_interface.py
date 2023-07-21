#
# Copyright (C) 2008 Google Inc.
#
# Licensed under the Apache License 2.0;


"""This module provides a common interface for all HTTP requests.

  HttpResponse: Represents the server's response to an HTTP request. Provides
      an interface identical to httplib.HTTPResponse which is the response
      expected from higher level classes which use HttpClient.request.

  GenericHttpClient: Provides an interface (superclass) for an object 
      responsible for making HTTP requests. Subclasses of this object are
      used in AtomService and GDataService to make requests to the server. By
      changing the http_client member object, the AtomService is able to make
      HTTP requests using different logic (for example, when running on 
      Google App Engine, the http_client makes requests using the App Engine
      urlfetch API). 
"""

# __author__ = 'api.jscudder (Jeff Scudder)'

import io

USER_AGENT = '%s GData-Python/2.0.18'


class Error(Exception):
    pass


class UnparsableUrlObject(Error):
    pass


class ContentLengthRequired(Error):
    pass


class HttpResponse(object):
    def __init__(self, body=None, status=None, reason=None, headers=None):
        """Constructor for an HttpResponse object.

        HttpResponse represents the server's response to an HTTP request from
        the client. The HttpClient.request method returns a httplib.HTTPResponse
        object and this HttpResponse class is designed to mirror the interface
        exposed by httplib.HTTPResponse.

        Args:
          body: A file like object, with a read() method. The body could also
              be a string, and the constructor will wrap it so that
              HttpResponse.read(self) will return the full string.
          status: The HTTP status code as an int. Example: 200, 201, 404.
          reason: The HTTP status message which follows the code. Example:
              OK, Created, Not Found
          headers: A dictionary containing the HTTP headers in the server's
              response. A common header in the response is Content-Length.
        """
        if body:
            if hasattr(body, 'read'):
                self._body = body
            else:
                self._body = io.StringIO(body)
        else:
            self._body = None
        if status is not None:
            self.status = int(status)
        else:
            self.status = None
        self.reason = reason
        self._headers = headers or {}

    def getheader(self, name, default=None):
        if name in self._headers:
            return self._headers[name]
        else:
            return default

    def read(self, amt=None):
        if not amt:
            return self._body.read()
        else:
            return self._body.read(amt)


class GenericHttpClient(object):
    debug = False

    def __init__(self, http_client, headers=None):
        """

        Args:
          http_client: An object which provides a request method to make an HTTP
              request. The request method in GenericHttpClient performs a
              call-through to the contained HTTP client object.
          headers: A dictionary containing HTTP headers which should be included
              in every HTTP request. Common persistent headers include
              'User-Agent'.
        """
        self.http_client = http_client
        self.headers = headers or {}

    def request(self, operation, url, data=None, headers=None):
        all_headers = self.headers.copy()
        if headers:
            all_headers.update(headers)
        return self.http_client.request(operation, url, data=data,
                                        headers=all_headers)

    def get(self, url, headers=None):
        return self.request('GET', url, headers=headers)

    def post(self, url, data, headers=None):
        return self.request('POST', url, data=data, headers=headers)

    def put(self, url, data, headers=None):
        return self.request('PUT', url, data=data, headers=headers)

    def delete(self, url, headers=None):
        return self.request('DELETE', url, headers=headers)


class GenericToken(object):
    """Represents an Authorization token to be added to HTTP requests.

    Some Authorization headers included calculated fields (digital
    signatures for example) which are based on the parameters of the HTTP
    request. Therefore the token is responsible for signing the request
    and adding the Authorization header.
    """

    def perform_request(self, http_client, operation, url, data=None,
                        headers=None):
        """For the GenericToken, no Authorization token is set."""
        return http_client.request(operation, url, data=data, headers=headers)

    def valid_for_scope(self, url):
        """Tells the caller if the token authorizes access to the desired URL.

        Since the generic token doesn't add an auth header, it is not valid for
        any scope.
        """
        return False
