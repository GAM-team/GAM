# Copyright (c) 2006 by Joe Gregorio, Google Inc.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

try:
    from collections.abc import Callable
except ImportError:
    from collections import Callable

import errno
import http.client
import socket
import ssl
import warnings

import certifi
import httplib2
import urllib3


def _default_make_pool(http, proxy_info, tls_maximum_version=None, tls_minimum_version=None):
    """Creates a urllib3.PoolManager object that has SSL verification enabled
    and uses the certifi certificates."""

    if not http.ca_certs:
        http.ca_certs = _certifi_where_for_ssl_version()

    ssl_disabled = http.disable_ssl_certificate_validation

    cert_reqs = 'CERT_REQUIRED' if http.ca_certs and not ssl_disabled else None

    ssl_minimum_version = ssl.TLSVersion[tls_minimum_version] if tls_minimum_version else None
    ssl_maximum_version = ssl.TLSVersion[tls_maximum_version] if tls_maximum_version else None

    if isinstance(proxy_info, Callable):
        proxy_info = proxy_info()
    if proxy_info:
        if proxy_info.proxy_user and proxy_info.proxy_pass:
            proxy_url = 'http://{}:{}@{}:{}/'.format(
                proxy_info.proxy_user, proxy_info.proxy_pass,
                proxy_info.proxy_host, proxy_info.proxy_port,
            )
            proxy_headers = urllib3.util.request.make_headers(
                proxy_basic_auth='{}:{}'.format(
                    proxy_info.proxy_user, proxy_info.proxy_pass,
                )
            )
        else:
            proxy_url = 'http://{}:{}/'.format(
                proxy_info.proxy_host, proxy_info.proxy_port,
            )
            proxy_headers = {}

        return urllib3.ProxyManager(
            proxy_url=proxy_url,
            proxy_headers=proxy_headers,
            ca_certs=http.ca_certs,
            cert_reqs=cert_reqs,
            ssl_minimum_version=ssl_minimum_version,
            ssl_maximum_version=ssl_maximum_version,
        )
    return urllib3.PoolManager(
        ca_certs=http.ca_certs,
        cert_reqs=cert_reqs,
        ssl_minimum_version=ssl_minimum_version,
        ssl_maximum_version=ssl_maximum_version,
    )


def patch(make_pool=_default_make_pool):
    """Monkey-patches httplib2.Http to be httplib2shim.Http.

    This effectively makes all clients of httplib2 use urlilb3. It's preferable
    to specify httplib2shim.Http explicitly where you can, but this can be
    useful in situations where you do not control the construction of the http
    object.

    Args:
        make_pool: A function that returns a urllib3.Pool-like object. This
            allows you to specify special arguments to your connection pool if
            needed. By default, this will create a urllib3.PoolManager with
            SSL verification enabled using the certifi certificates.
    """
    setattr(httplib2, '_HttpOriginal', httplib2.Http)
    httplib2.Http = Http
    Http._make_pool = make_pool


class Http(httplib2.Http):
    """A httplib2.Http subclass that uses urllib3 to perform requests.

    This allows full thread safety, connection pooling, and proper SSL
    verification support.
    """
    _make_pool = _default_make_pool

    def __init__(self, cache=None, timeout=None,
                 proxy_info=httplib2.proxy_info_from_environment,
                 ca_certs=None, disable_ssl_certificate_validation=False,
                 pool=None, tls_maximum_version=None, tls_minimum_version=None):
        disable_ssl = disable_ssl_certificate_validation

        super(Http, self).__init__(
            cache=cache,
            timeout=timeout,
            proxy_info=proxy_info,
            ca_certs=ca_certs,
            disable_ssl_certificate_validation=disable_ssl,
            tls_maximum_version=tls_maximum_version,
            tls_minimum_version=tls_minimum_version)

        if not pool:
            pool = self._make_pool(proxy_info=proxy_info,
                                   tls_maximum_version=tls_maximum_version,
                                   tls_minimum_version=tls_minimum_version)

        self.pool = pool

        if httplib2.debuglevel:
            http.client.HTTPConnection.debuglevel = 5


    def _conn_request(self, conn, request_uri, method, body, headers):
        # Reconstruct the full uri from the connection object.
        if isinstance(conn, httplib2.HTTPSConnectionWithTimeout):
            scheme = 'https'
        else:
            scheme = 'http'

        host = conn.host

        # Reformat IPv6 hosts.
        if _is_ipv6(host):
            host = '[{}]'.format(host)

        full_uri = '{}://{}:{}{}'.format(
            scheme, host, conn.port, request_uri)

        decode = True if method != 'HEAD' else False

        try:
            urllib3_response = self.pool.request(
                method,
                full_uri,
                body=body,
                headers=headers,
                redirect=False,
                retries=urllib3.Retry(total=False, redirect=0),
                timeout=urllib3.Timeout(total=self.timeout),
                decode_content=decode)

            response = _map_response(urllib3_response, decode=decode)
            content = urllib3_response.data

        except Exception as e:
            raise _map_exception(e)

        return response, content

    def add_certificate(self, *args, **kwargs):
        warnings.warn('httplib2shim does not support add_certificate.')
        return super(Http, self).add_certificate(*args, **kwargs)

    def __getstate__(self):
        dict = super(Http, self).__getstate__()
        del dict['pool']
        return dict

    def __setstate__(self, dict):
        super(Http, self).__setstate__(dict)
        self.pool = self._make_pool(proxy_info=self.proxy_info())


def _is_ipv6(addr):
    """Checks if a given address is an IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except socket.error:
        return False


def _certifi_where_for_ssl_version():
    """Gets the right location for certifi certifications for the current SSL
    version.

    Older versions of SSL don't support the stronger set of root certificates.
    """
    if not ssl:
        return

    if ssl.OPENSSL_VERSION_INFO < (1, 0, 2):
        warnings.warn(
            'You are using an outdated version of OpenSSL that '
            'can\'t use stronger root certificates.')
        return certifi.old_where()

    return certifi.where()


def _map_response(response, decode=False):
    """Maps a urllib3 response to a httplib/httplib2 Response."""
    # This causes weird deepcopy errors, so it's commented out for now.
    # item._urllib3_response = response
    item = httplib2.Response(response.getheaders())
    item.status = response.status
    item['status'] = str(item.status)
    item.reason = response.reason
    item.version = response.version

    # httplib2 expects the content-encoding header to be stripped and the
    # content length to be the length of the uncompressed content.
    # This does not occur for 'HEAD' requests.
    if decode and item.get('content-encoding') in ['gzip', 'deflate']:
        item['content-length'] = str(len(response.data))
        item['-content-encoding'] = item.pop('content-encoding')

    return item


def _map_exception(e):
    """Maps an exception from urlib3 to httplib2."""
    if isinstance(e, urllib3.exceptions.MaxRetryError):
        if not e.reason:
            return e
        e = e.reason
    message = e.args[0] if e.args else ''
    if isinstance(e, urllib3.exceptions.ResponseError):
        if 'too many redirects' in message:
            return httplib2.RedirectLimit(message)
    if isinstance(e, urllib3.exceptions.NewConnectionError):
        if ('Name or service not known' in message or
                'nodename nor servname provided, or not known' in message):
            return httplib2.ServerNotFoundError(
                'Unable to find hostname.')
        if 'Connection refused' in message:
            return socket.error((errno.ECONNREFUSED, 'Connection refused'))
    if isinstance(e, urllib3.exceptions.DecodeError):
        return httplib2.FailedToDecompressContent(
            'Content purported as compressed but not uncompressable.',
            httplib2.Response({'status': 500}), '')
    if isinstance(e, urllib3.exceptions.TimeoutError):
        return socket.timeout('timed out')
    if isinstance(e, urllib3.exceptions.SSLError):
        return ssl.SSLError(*e.args)

    return e
