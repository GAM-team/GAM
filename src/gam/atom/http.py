#
# Copyright (C) 2008 Google Inc.
#
# Licensed under the Apache License 2.0;



"""HttpClients in this module use httplib to make HTTP requests.

This module make HTTP requests based on httplib, but there are environments
in which an httplib based approach will not work (if running in Google App
Engine for example). In those cases, higher level classes (like AtomService
and GDataService) can swap out the HttpClient to transparently use a 
different mechanism for making HTTP requests.

  HttpClient: Contains a request method which performs an HTTP call to the 
      server.
      
  ProxiedHttpClient: Contains a request method which connects to a proxy using
      settings stored in operating system environment variables then 
      performs an HTTP call to the endpoint server.
"""

# __author__ = 'api.jscudder (Jeff Scudder)'

import base64
import http.client
import os
import socket

import atom.http_core
import atom.http_interface
import atom.url

ssl_imported = False
ssl = None
try:
    import ssl

    ssl_imported = True
except ImportError:
    pass


class ProxyError(atom.http_interface.Error):
    pass


class TestConfigurationError(Exception):
    pass


DEFAULT_CONTENT_TYPE = 'application/atom+xml'


class HttpClient(atom.http_interface.GenericHttpClient):
    # Added to allow old v1 HttpClient objects to use the new
    # http_code.HttpClient. Used in unit tests to inject a mock client.
    v2_http_client = None

    def __init__(self, headers=None):
        self.debug = False
        self.headers = headers or {}

    def request(self, operation, url, data=None, headers=None):
        """Performs an HTTP call to the server, supports GET, POST, PUT, and
        DELETE.

        Usage example, perform and HTTP GET on http://www.google.com/:
          import atom.http
          client = atom.http.HttpClient()
          http_response = client.request('GET', 'http://www.google.com/')

        Args:
          operation: str The HTTP operation to be performed. This is usually one
              of 'GET', 'POST', 'PUT', or 'DELETE'
          data: filestream, list of parts, or other object which can be converted
              to a string. Should be set to None when performing a GET or DELETE.
              If data is a file-like object which can be read, this method will
              read a chunk of 100K bytes at a time and send them.
              If the data is a list of parts to be sent, each part will be
              evaluated and sent.
          url: The full URL to which the request should be sent. Can be a string
              or atom.url.Url.
          headers: dict of strings. HTTP headers which should be sent
              in the request.
        """
        all_headers = self.headers.copy()
        if headers:
            all_headers.update(headers)

        # If the list of headers does not include a Content-Length, attempt to
        # calculate it based on the data object.
        if data and 'Content-Length' not in all_headers:
            if isinstance(data, (str,)):
                all_headers['Content-Length'] = str(len(data))
            else:
                raise atom.http_interface.ContentLengthRequired('Unable to calculate '
                                                                'the length of the data parameter. Specify a value for '
                                                                'Content-Length')

        # Set the content type to the default value if none was set.
        if 'Content-Type' not in all_headers:
            all_headers['Content-Type'] = DEFAULT_CONTENT_TYPE

        if self.v2_http_client is not None:
            http_request = atom.http_core.HttpRequest(method=operation)
            atom.http_core.Uri.parse_uri(str(url)).modify_request(http_request)
            http_request.headers = all_headers
            if data:
                http_request._body_parts.append(data)
            return self.v2_http_client.request(http_request=http_request)

        if not isinstance(url, atom.url.Url):
            if isinstance(url, str):
                url = atom.url.parse_url(url)
            else:
                raise atom.http_interface.UnparsableUrlObject('Unable to parse url parameter because it was not a string or atom.url.Url')

        connection = self._prepare_connection(url, all_headers)

        if self.debug:
            connection.debuglevel = 1

        connection.putrequest(operation, self._get_access_url(url), skip_host=True)

        if url.port is not None:
            connection.putheader('Host', '%s:%s' % (url.host, url.port))
        else:
            connection.putheader('Host', url.host)

        # Overcome a bug in Python 2.4 and 2.5
        # httplib.HTTPConnection.putrequest adding
        # HTTP request header 'Host: www.google.com:443' instead of
        # 'Host: www.google.com', and thus resulting the error message
        # 'Token invalid - AuthSub token has wrong scope' in the HTTP response.
        if (url.protocol == 'https' and int(url.port or 443) == 443 and
                hasattr(connection, '_buffer') and
                isinstance(connection._buffer, list)):
            header_line = 'Host: %s:443' % url.host
            replacement_header_line = 'Host: %s' % url.host
            try:
                connection._buffer[connection._buffer.index(header_line)] = (
                    replacement_header_line)
            except ValueError:  # header_line missing from connection._buffer
                pass

        # Send the HTTP headers.
        for header_name in all_headers:
            connection.putheader(header_name, all_headers[header_name])
        connection.endheaders()

        # If there is data, send it in the request.
        if data:
            if isinstance(data, list):
                for data_part in data:
                    _send_data_part(data_part, connection)
            else:
                _send_data_part(data, connection)

        # Return the HTTP Response from the server.
        return connection.getresponse()

    def _prepare_connection(self, url, headers):
        if not isinstance(url, atom.url.Url):
            if isinstance(url, (str,)):
                url = atom.url.parse_url(url)
            else:
                raise atom.http_interface.UnparsableUrlObject('Unable to parse url '
                                                              'parameter because it was not a string or atom.url.Url')
        if url.protocol == 'https':
            if not url.port:
                return http.client.HTTPSConnection(url.host)
            return http.client.HTTPSConnection(url.host, int(url.port))
        else:
            if not url.port:
                return http.client.HTTPConnection(url.host)
            return http.client.HTTPConnection(url.host, int(url.port))

    def _get_access_url(self, url):
        return url.to_string()


class ProxiedHttpClient(HttpClient):
    """Performs an HTTP request through a proxy.

    The proxy settings are obtained from enviroment variables. The URL of the
    proxy server is assumed to be stored in the environment variables
    'https_proxy' and 'http_proxy' respectively. If the proxy server requires
    a Basic Auth authorization header, the username and password are expected to
    be in the 'proxy-username' or 'proxy_username' variable and the
    'proxy-password' or 'proxy_password' variable, or in 'http_proxy' or
    'https_proxy' as "protocol://[username:password@]host:port".

    After connecting to the proxy server, the request is completed as in
    HttpClient.request.
    """

    def _prepare_connection(self, url, headers):
        proxy_settings = os.environ.get('%s_proxy' % url.protocol)
        if not proxy_settings:
            # The request was HTTP or HTTPS, but there was no appropriate proxy set.
            return HttpClient._prepare_connection(self, url, headers)
        else:
            proxy_auth = _get_proxy_auth(proxy_settings)
            proxy_netloc = _get_proxy_net_location(proxy_settings)
            if url.protocol == 'https':
                # Set any proxy auth headers
                if proxy_auth:
                    proxy_auth = 'Proxy-Authorization: %s' % proxy_auth

                # Construct the proxy connect command.
                port = url.port
                if not port:
                    port = '443'
                proxy_connect = 'CONNECT %s:%s HTTP/1.0\r\n' % (url.host, port)

                # Set the user agent to send to the proxy
                if headers and 'User-Agent' in headers:
                    user_agent = 'User-Agent: %s\r\n' % (headers['User-Agent'])
                else:
                    user_agent = 'User-Agent: python\r\n'

                proxy_pieces = '%s%s%s\r\n' % (proxy_connect, proxy_auth, user_agent)

                # Find the proxy host and port.
                proxy_url = atom.url.parse_url(proxy_netloc)
                if not proxy_url.port:
                    proxy_url.port = '80'

                # Connect to the proxy server, very simple recv and error checking
                p_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                p_sock.connect((proxy_url.host, int(proxy_url.port)))
                #p_sock.sendall(proxy_pieces)
                p_sock.sendall(proxy_pieces.encode('utf-8'))
                response = ''

                # Wait for the full response.
                while response.find("\r\n\r\n") == -1:
                    #response += p_sock.recv(8192)
                    response += p_sock.recv(8192).decode('utf-8')

                p_status = response.split()[1]
                if p_status != str(200):
                    raise ProxyError('Error status=%s' % str(p_status))

                # Trivial setup for ssl socket.
                sslobj = None
                if ssl_imported:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    context.minimum_version = ssl.TLSVersion.TLSv1_2
                    sslobj = context.wrap_socket(p_sock, server_hostname=url.host)
                else:
                    sock_ssl = socket.ssl(p_sock, None, None)
                    sslobj = http.client.FakeSocket(p_sock, sock_ssl)

                # Initalize httplib and replace with the proxy socket.
                connection = http.client.HTTPConnection(proxy_url.host)
                connection.sock = sslobj
                return connection
            else:
                # If protocol was not https.
                # Find the proxy host and port.
                proxy_url = atom.url.parse_url(proxy_netloc)
                if not proxy_url.port:
                    proxy_url.port = '80'

                if proxy_auth:
                    headers['Proxy-Authorization'] = proxy_auth.strip()

                return http.client.HTTPConnection(proxy_url.host, int(proxy_url.port))

    def _get_access_url(self, url):
        return url.to_string()


def _get_proxy_auth(proxy_settings):
    """Returns proxy authentication string for header.

    Will check environment variables for proxy authentication info, starting with
    proxy(_/-)username and proxy(_/-)password before checking the given
    proxy_settings for a [protocol://]username:password@host[:port] string.

    Args:
      proxy_settings: String from http_proxy or https_proxy environment variable.

    Returns:
      Authentication string for proxy, or empty string if no proxy username was
      found.
    """
    proxy_username = None
    proxy_password = None

    proxy_username = os.environ.get('proxy-username')
    if not proxy_username:
        proxy_username = os.environ.get('proxy_username')
    proxy_password = os.environ.get('proxy-password')
    if not proxy_password:
        proxy_password = os.environ.get('proxy_password')

    if not proxy_username:
        if '@' in proxy_settings:
            protocol_and_proxy_auth = proxy_settings.split('@')[0].split(':')
            if len(protocol_and_proxy_auth) == 3:
                # 3 elements means we have [<protocol>, //<user>, <password>]
                proxy_username = protocol_and_proxy_auth[1].lstrip('/')
                proxy_password = protocol_and_proxy_auth[2]
            elif len(protocol_and_proxy_auth) == 2:
                # 2 elements means we have [<user>, <password>]
                proxy_username = protocol_and_proxy_auth[0]
                proxy_password = protocol_and_proxy_auth[1]
    if proxy_username:
        user_auth = base64.b64encode(('%s:%s' % (proxy_username, proxy_password)).encode('utf-8'))
        return 'Basic %s\r\n' % (user_auth.strip().decode('utf-8'))
    else:
        return ''


def _get_proxy_net_location(proxy_settings):
    """Returns proxy host and port.

    Args:
      proxy_settings: String from http_proxy or https_proxy environment variable.
          Must be in the form of protocol://[username:password@]host:port

    Returns:
      String in the form of protocol://host:port
    """
    if '@' in proxy_settings:
        protocol = proxy_settings.split(':')[0]
        netloc = proxy_settings.split('@')[1]
        return '%s://%s' % (protocol, netloc)
    else:
        return proxy_settings


def _send_data_part(data, connection):
    if isinstance(data, (str,)):
        connection.send(data)
        return
    # Check to see if data is a file-like object that has a read method.
    elif hasattr(data, 'read'):
        # Read the file and send it a chunk at a time.
        while 1:
            binarydata = data.read(100000)
            if binarydata == b'': break
            connection.send(binarydata)
        return
    else:
        # The data object was not a file.
        # Try to convert to a string and send the data.
        #connection.send(str(data))
        connection.send(str(data).encode('utf-8'))
        return
