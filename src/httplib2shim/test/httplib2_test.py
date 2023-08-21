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

"""
This is the httplib2 test suite. It has been adapted to use the shim and to
run on both python 2 and python 3.
"""

import io
import os
import pickle
import platform
import socket
import ssl
import sys
import time
import unittest

import httplib2
import httplib2shim
import six
from six.moves.urllib import parse as urllib_parse
import urllib3


__author__ = "Joe Gregorio (joe@bitworking.org)"
__copyright__ = "Copyright 2006, Joe Gregorio"
__contributors__ = ["Mark Pilgrim"]
__license__ = "MIT"
__history__ = """ """
__version__ = "0.2 ($Rev: 118 $)"


httplib2shim.patch()

# The test resources base uri
base = os.environ.get('TEST_SERVER_URL')
no_base_reason = 'No TEST_SERVER_URL specified'
cacheDirName = ".cache"


class CredentialsTest(unittest.TestCase):
    def test(self):
        c = httplib2.Credentials()
        c.add("joe", "password")
        self.assertEqual(
            ("joe", "password"), list(c.iter("bitworking.org"))[0])
        self.assertEqual(("joe", "password"), list(c.iter(""))[0])
        c.add("fred", "password2", "wellformedweb.org")
        self.assertEqual(
            ("joe", "password"), list(c.iter("bitworking.org"))[0])
        self.assertEqual(1, len(list(c.iter("bitworking.org"))))
        self.assertEqual(2, len(list(c.iter("wellformedweb.org"))))
        self.assertTrue(
            ("fred", "password2") in list(c.iter("wellformedweb.org")))
        c.clear()
        self.assertEqual(0, len(list(c.iter("bitworking.org"))))
        c.add("fred", "password2", "wellformedweb.org")
        self.assertTrue(
            ("fred", "password2") in list(c.iter("wellformedweb.org")))
        self.assertEqual(0, len(list(c.iter("bitworking.org"))))
        self.assertEqual(0, len(list(c.iter(""))))


class ParserTest(unittest.TestCase):
    def testFromStd66(self):
        self.assertEqual(
            ('http', 'example.com', '', None, None),
            httplib2.parse_uri("http://example.com"))
        self.assertEqual(
            ('https', 'example.com', '', None, None),
            httplib2.parse_uri("https://example.com"))
        self.assertEqual(
            ('https', 'example.com:8080', '', None, None),
            httplib2.parse_uri("https://example.com:8080"))
        self.assertEqual(
            ('http', 'example.com', '/', None, None),
            httplib2.parse_uri("http://example.com/"))
        self.assertEqual(
            ('http', 'example.com', '/path', None, None),
            httplib2.parse_uri("http://example.com/path"))
        self.assertEqual(
            ('http', 'example.com', '/path', 'a=1&b=2', None),
            httplib2.parse_uri("http://example.com/path?a=1&b=2"))
        self.assertEqual(
            ('http', 'example.com', '/path', 'a=1&b=2', 'fred'),
            httplib2.parse_uri("http://example.com/path?a=1&b=2#fred"))
        self.assertEqual(
            ('http', 'example.com', '/path', 'a=1&b=2', 'fred'),
            httplib2.parse_uri("http://example.com/path?a=1&b=2#fred"))


class UrlNormTest(unittest.TestCase):
    def test(self):
        self.assertEqual(
            "http://example.org/",
            httplib2.urlnorm("http://example.org")[-1])
        self.assertEqual(
            "http://example.org/",
            httplib2.urlnorm("http://EXAMple.org")[-1])
        self.assertEqual(
            "http://example.org/?=b",
            httplib2.urlnorm("http://EXAMple.org?=b")[-1])
        self.assertEqual(
            "http://example.org/mypath?a=b",
            httplib2.urlnorm("http://EXAMple.org/mypath?a=b")[-1])
        self.assertEqual(
            "http://localhost:80/",
            httplib2.urlnorm("http://localhost:80")[-1])
        self.assertEqual(
            httplib2.urlnorm("http://localhost:80/"),
            httplib2.urlnorm("HTTP://LOCALHOST:80"))
        try:
            httplib2.urlnorm("/")
            self.fail("Non-absolute URIs should raise an exception")
        except httplib2.RelativeURIError:
            pass


class UrlSafenameTest(unittest.TestCase):
    def test(self):
        # Test that different URIs end up generating different safe names
        self.assertEqual(
            "example.org,fred,a=b,58489f63a7a83c3b7794a6a398ee8b1f",
            httplib2.safename("http://example.org/fred/?a=b"))
        self.assertEqual(
            "example.org,fred,a=b,8c5946d56fec453071f43329ff0be46b",
            httplib2.safename("http://example.org/fred?/a=b"))
        self.assertEqual(
            "www.example.org,fred,a=b,499c44b8d844a011b67ea2c015116968",
            httplib2.safename("http://www.example.org/fred?/a=b"))
        self.assertEqual(
            httplib2.safename(httplib2.urlnorm("http://www")[-1]),
            httplib2.safename(httplib2.urlnorm("http://WWW")[-1]))
        self.assertEqual(
            "www.example.org,fred,a=b,692e843a333484ce0095b070497ab45d",
            httplib2.safename("https://www.example.org/fred?/a=b"))
        self.assertNotEqual(
            httplib2.safename("http://www"),
            httplib2.safename("https://www"))
        # Test the max length limits
        uri = "http://" + ("w" * 200) + ".org"
        uri2 = "http://" + ("w" * 201) + ".org"
        self.assertNotEqual(httplib2.safename(uri2), httplib2.safename(uri))
        # Max length should be 200 + 1 (",") + 32
        self.assertEqual(233, len(httplib2.safename(uri2)))
        self.assertEqual(233, len(httplib2.safename(uri)))
        # Unicode
        if sys.version_info >= (2, 3):
            self.assertEqual(
                "xn--http,-4y1d.org,fred,a=b,579924c35db315e5a32e3d9963388193",
                httplib2.safename(u"http://\u2304.org/fred/?a=b"))


class _MyResponse(io.BytesIO):
    def __init__(self, body, **kwargs):
        io.BytesIO.__init__(self, body)
        self.headers = kwargs

    def items(self):
        return self.headers.items()

    def iteritems(self):
        return iter(self.headers.items())


class HttpTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(cacheDirName):
            [os.remove(os.path.join(cacheDirName, file))
             for file in os.listdir(cacheDirName)]
        self.http = httplib2.Http(cacheDirName)
        self.http.clear_credentials()

    def testIPv6NoSSL(self):
        try:
            self.http.request("http://[::1]/")
        except socket.gaierror:
            self.fail("should get the address family right for IPv6")
        except socket.error:
            pass

    def testIPv6SSL(self):
        try:
            self.http.request("https://[::1]/")
        except socket.gaierror:
            self.fail("should get the address family right for IPv6")
        except socket.error:
            pass

    # NOTE: Disabled because it's not applicable to the shim
    # def testConnectionType(self):
    #     self.http.force_exception_to_status_code = False
    #     response, content = self.http.request(
    #        "http://bitworking.org", connection_type=_MyHTTPConnection)
    #     self.assertEqual(
    #        response['content-location'], "http://bitworking.org")
    #     self.assertEqual(content, b"the body")

    # NOTE: Disabled because I don't yet have a good way to test this.
    # def testBadStatusLineRetry(self):
    #     old_retries = httplib2.RETRIES
    #     httplib2.RETRIES = 1
    #     self.http.force_exception_to_status_code = False
    #     try:
    #         response, content = self.http.request("http://bitworking.org",
    #             connection_type=_MyHTTPBadStatusConnection)
    #     except http.client.BadStatusLine:
    #         self.assertEqual(2, _MyHTTPBadStatusConnection.num_calls)
    #     httplib2.RETRIES = old_retries

    def testGetUnknownServer(self):
        self.http.force_exception_to_status_code = False
        try:
            self.http.request("http://fred.bitworking.org/")
            self.fail(
                'An httplib2.ServerNotFoundError Exception must be thrown on '
                'an unresolvable server.')
        except httplib2.ServerNotFoundError:
            pass

        # Now test with exceptions turned off
        self.http.force_exception_to_status_code = True

        (response, content) = self.http.request("http://fred.bitworking.org/")
        self.assertEqual(response['content-type'], 'text/plain')
        self.assertTrue(content.startswith(b"Unable to find"))
        self.assertEqual(response.status, 400)

    def testGetConnectionRefused(self):
        self.http.force_exception_to_status_code = False
        try:
            self.http.request("http://localhost:7777/")
            self.fail(
                'A socket.error exception must be thrown on '
                'Connection Refused.')
        except socket.error:
            pass

        # Now test with exceptions turned off
        self.http.force_exception_to_status_code = True

        (response, content) = self.http.request("http://localhost:7777/")
        self.assertEqual(response['content-type'], 'text/plain')
        self.assertTrue(b"Connection refused" in content)
        self.assertEqual(response.status, 400)

    @unittest.skipIf(not base, no_base_reason)
    def testGetIRI(self):
        if sys.version_info >= (2, 3):
            uri = urllib_parse.urljoin(
                base,
                u'reflector/reflector.cgi?d=\N{CYRILLIC CAPITAL LETTER DJE}')
            (response, content) = self.http.request(uri, "GET")
            d = self.reflector(content)
            self.assertTrue('QUERY_STRING' in d)
            print(d['QUERY_STRING'])
            self.assertTrue(d['QUERY_STRING'].find('%D0%82') > 0)

    @unittest.skipIf(not base, no_base_reason)
    def testGetIsDefaultMethod(self):
        # Test that GET is the default method
        uri = urllib_parse.urljoin(base, "methods/method_reflector.cgi")
        (response, content) = self.http.request(uri)
        self.assertEqual(response['x-method'], "GET")

    @unittest.skipIf(not base, no_base_reason)
    def testDifferentMethods(self):
        # Test that all methods can be used
        uri = urllib_parse.urljoin(base, "methods/method_reflector.cgi")
        for method in ["GET", "PUT", "DELETE", "POST"]:
            (response, content) = self.http.request(uri, method, body=b" ")
            self.assertEqual(response['x-method'], method)

    def testHeadRead(self):
        # Test that we don't try to read the response of a HEAD request
        # since httplib blocks response.read() for HEAD requests.
        # Oddly enough this doesn't appear as a problem when doing HEAD
        # requests against Apache servers.
        uri = "http://www.google.com/"
        (response, content) = self.http.request(uri, "HEAD")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"")

    @unittest.skipIf(not base, no_base_reason)
    def testGetNoCache(self):
        # Test that can do a GET w/o the cache turned on.
        http = httplib2.Http()
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.previous, None)

    @unittest.skipIf(not base, no_base_reason)
    def testGetOnlyIfCachedCacheHit(self):
        # Test that can do a GET with cache and 'only-if-cached'
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = self.http.request(uri, "GET")
        (response, content) = self.http.request(
            uri, "GET", headers={'cache-control': 'only-if-cached'})
        self.assertEqual(response.fromcache, True)
        self.assertEqual(response.status, 200)

    @unittest.skipIf(not base, no_base_reason)
    def testGetOnlyIfCachedCacheMiss(self):
        # Test that can do a GET with no cache with 'only-if-cached'
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = self.http.request(
            uri, "GET", headers={'cache-control': 'only-if-cached'})
        self.assertEqual(response.fromcache, False)
        self.assertEqual(response.status, 504)

    @unittest.skipIf(not base, no_base_reason)
    def testGetOnlyIfCachedNoCacheAtAll(self):
        # Test that can do a GET with no cache with 'only-if-cached'
        # Of course, there might be an intermediary beyond us
        # that responds to the 'only-if-cached', so this
        # test can't really be guaranteed to pass.
        http = httplib2.Http()
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = http.request(
            uri, "GET", headers={'cache-control': 'only-if-cached'})
        self.assertEqual(response.fromcache, False)
        self.assertEqual(response.status, 504)

    @unittest.skipIf(not base, no_base_reason)
    def testUserAgent(self):
        # Test that we provide a default user-agent
        uri = urllib_parse.urljoin(base, "user-agent/test.cgi")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertTrue(content.startswith(b"Python-httplib2/"))

    @unittest.skipIf(not base, no_base_reason)
    def testUserAgentNonDefault(self):
        # Test that the default user-agent can be over-ridden

        uri = urllib_parse.urljoin(base, "user-agent/test.cgi")
        (response, content) = self.http.request(
            uri, "GET", headers={'User-Agent': 'fred/1.0'})
        self.assertEqual(response.status, 200)
        self.assertTrue(content.startswith(b"fred/1.0"))

    @unittest.skipIf(not base, no_base_reason)
    def testGet300WithLocation(self):
        # Test the we automatically follow 300 redirects if a
        # Location: header is provided
        uri = urllib_parse.urljoin(base, "300/with-location-header.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 300)
        self.assertEqual(response.previous.fromcache, False)

        # Confirm that the intermediate 300 is not cached
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 300)
        self.assertEqual(response.previous.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGet300WithLocationNoRedirect(self):
        # Test the we automatically follow 300 redirects if a
        # Location: header is provided
        self.http.follow_redirects = False
        uri = urllib_parse.urljoin(base, "300/with-location-header.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 300)

    @unittest.skipIf(not base, no_base_reason)
    def testGet300WithoutLocation(self):
        # Not giving a Location: header in a 300 response is acceptable
        # In which case we just return the 300 response
        uri = urllib_parse.urljoin(base, "300/without-location-header.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 300)
        self.assertTrue(response['content-type'].startswith("text/html"))
        self.assertEqual(response.previous, None)

    @unittest.skipIf(not base, no_base_reason)
    def testGet301(self):
        # Test that we automatically follow 301 redirects
        # and that we cache the 301 response
        uri = urllib_parse.urljoin(base, "301/onestep.asis")
        destination = urllib_parse.urljoin(base, "302/final-destination.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertTrue('content-location' in response)
        self.assertEqual(response['content-location'], destination)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 301)
        self.assertEqual(response.previous.fromcache, False)

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response['content-location'], destination)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 301)
        self.assertEqual(response.previous.fromcache, True)

    @unittest.skipIf(not base, no_base_reason)
    def testHead301(self):
        # Test that we automatically follow 301 redirects
        uri = urllib_parse.urljoin(base, "301/onestep.asis")
        (response, content) = self.http.request(uri, "HEAD")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.previous.status, 301)
        self.assertEqual(response.previous.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGet301NoRedirect(self):
        # Test that we automatically follow 301 redirects
        # and that we cache the 301 response
        self.http.follow_redirects = False
        uri = urllib_parse.urljoin(base, "301/onestep.asis")
        urllib_parse.urljoin(base, "302/final-destination.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 301)

    @unittest.skipIf(not base, no_base_reason)
    def testGet302(self):
        # Test that we automatically follow 302 redirects
        # and that we DO NOT cache the 302 response
        uri = urllib_parse.urljoin(base, "302/onestep.asis")
        destination = urllib_parse.urljoin(base, "302/final-destination.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response['content-location'], destination)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 302)
        self.assertEqual(response.previous.fromcache, False)

        uri = urllib_parse.urljoin(base, "302/onestep.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)
        self.assertEqual(response['content-location'], destination)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 302)
        self.assertEqual(response.previous.fromcache, False)
        self.assertEqual(response.previous['content-location'], uri)

        uri = urllib_parse.urljoin(base, "302/twostep.asis")

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 302)
        self.assertEqual(response.previous.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGet302RedirectionLimit(self):
        # Test that we can set a lower redirection limit
        # and that we raise an exception when we exceed
        # that limit.
        self.http.force_exception_to_status_code = False

        uri = urllib_parse.urljoin(base, "302/twostep.asis")
        try:
            (response, content) = self.http.request(uri, "GET", redirections=1)
            self.fail("This should not happen")
        except httplib2.RedirectLimit:
            pass
        except Exception:
            self.fail("Threw wrong kind of exception ")

        # Re-run the test with out the exceptions
        self.http.force_exception_to_status_code = True

        (response, content) = self.http.request(uri, "GET", redirections=1)
        self.assertEqual(response.status, 500)
        self.assertTrue(response.reason.startswith("Redirected more"))
        self.assertEqual("302", response['status'])
        self.assertTrue(content.startswith(b"<html>"))
        self.assertTrue(response.previous is not None)

    @unittest.skipIf(not base, no_base_reason)
    def testGet302NoLocation(self):
        # Test that we throw an exception when we get
        # a 302 with no Location: header.
        self.http.force_exception_to_status_code = False
        uri = urllib_parse.urljoin(base, "302/no-location.asis")
        try:
            (response, content) = self.http.request(uri, "GET")
            self.fail("Should never reach here")
        except httplib2.RedirectMissingLocation:
            pass
        except Exception:
            self.fail("Threw wrong kind of exception ")

        # Re-run the test with out the exceptions
        self.http.force_exception_to_status_code = True

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 500)
        self.assertTrue(response.reason.startswith("Redirected but"))
        self.assertEqual("302", response['status'])
        self.assertTrue(content.startswith(b"This is content"))

    def testGet301ViaHttps(self):
        # Google always redirects to http://google.com
        (response, content) = self.http.request(
            "https://code.google.com/apis/", "GET")
        self.assertEqual(200, response.status)
        self.assertEqual(301, response.previous.status)

    def testGetViaHttps(self):
        # Test that we can handle HTTPS
        (response, content) = self.http.request(
            "https://google.com/adsense/", "GET")
        self.assertEqual(200, response.status)

    def testGetViaHttpsSpecViolationOnLocation(self):
        # Test that we follow redirects through HTTPS
        # even if they violate the spec by including
        # a relative Location: header instead of an
        # absolute one.
        (response, content) = self.http.request(
            "https://google.com/adsense", "GET")
        self.assertEqual(200, response.status)
        self.assertNotEqual(None, response.previous)

    def testGetViaHttpsKeyCert(self):
        #  At this point I can only test
        #  that the key and cert files are passed in
        #  correctly to httplib. It would be nice to have
        #  a real https endpoint to test against.
        http = httplib2.Http(timeout=2)

        http.add_certificate("akeyfile", "acertfile", "bitworking.org")
        try:
            (response, content) = http.request("https://bitworking.org", "GET")
        except AttributeError:
            self.assertEqual(
                http.connections["https:bitworking.org"].key_file, "akeyfile")
            self.assertEqual(
                http.connections[
                    "https:bitworking.org"].cert_file, "acertfile")
        except IOError:
            # Skip on 3.2
            pass

        try:
            (response, content) = http.request(
                "https://notthere.bitworking.org", "GET")
        except httplib2.ServerNotFoundError:
            self.assertEqual(
                http.connections["https:notthere.bitworking.org"].key_file,
                None)
            self.assertEqual(
                http.connections["https:notthere.bitworking.org"].cert_file,
                None)
        except IOError:
            # Skip on 3.2
            pass

    def testSslCertValidation(self):
        # Test that we get an ssl.SSLError when specifying a non-existent CA
        # certs file.
        http = httplib2.Http(ca_certs='/nosuchfile')
        self.assertRaises(
            (IOError, OSError), http.request, "https://www.google.com/", "GET")

        # Test that we get a SSLHandshakeError if we try to access
        # https://www.google.com, using a CA cert file that doesn't contain
        # the CA Google uses (i.e., simulating a cert that's not signed by a
        # trusted CA).

        # This doesn't work on OS X because apple patches openssl to always
        # consult the keychain.
        if platform.system() == 'Darwin':
            return

        other_ca_certs = os.path.join(
            os.path.dirname(os.path.abspath(httplib2shim.__file__)),
            "test", "other_cacerts.txt")
        http = httplib2.Http(ca_certs=other_ca_certs)
        self.assertRaises(
            ssl.SSLError,
            http.request,
            "https://www.google.com/", "GET")

    def testSniHostnameValidation(self):
        self.http.request("https://google.com/", method="GET")

    @unittest.skipIf(not base, no_base_reason)
    def testGet303(self):
        # Do a follow-up GET on a Location: header
        # returned from a POST that gave a 303.
        uri = urllib_parse.urljoin(base, "303/303.cgi")
        (response, content) = self.http.request(uri, "POST", " ")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 303)

    @unittest.skipIf(not base, no_base_reason)
    def testGet303NoRedirect(self):
        # Do a follow-up GET on a Location: header
        # returned from a POST that gave a 303.
        self.http.follow_redirects = False
        uri = urllib_parse.urljoin(base, "303/303.cgi")
        (response, content) = self.http.request(uri, "POST", " ")
        self.assertEqual(response.status, 303)

    @unittest.skipIf(not base, no_base_reason)
    def test303ForDifferentMethods(self):
        # Test that all methods can be used
        uri = urllib_parse.urljoin(base, "303/redirect-to-reflector.cgi")
        for (method, method_on_303) in [
                ("PUT", "GET"), ("DELETE", "GET"),
                ("POST", "GET"), ("GET", "GET"),
                ("HEAD", "GET")]:
            (response, content) = self.http.request(uri, method, body=b" ")
            self.assertEqual(response['x-method'], method_on_303)

    @unittest.skipIf(not base, no_base_reason)
    def testGet304(self):
        # Test that we use ETags properly to validate our cache
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        self.assertNotEqual(response['etag'], "")

        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        (response, content) = self.http.request(
            uri, "GET", headers={
                'accept-encoding': 'identity',
                'cache-control': 'must-revalidate'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)

        cache_file_name = os.path.join(
            cacheDirName, httplib2.safename(httplib2.urlnorm(uri)[-1]))
        f = open(cache_file_name, "r")
        status_line = f.readline()
        f.close()

        self.assertTrue(status_line.startswith("status:"))

        (response, content) = self.http.request(
            uri, "HEAD", headers={'accept-encoding': 'identity'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)

        (response, content) = self.http.request(
            uri, "GET", headers={
                'accept-encoding': 'identity',
                'range': 'bytes=0-0'})
        self.assertEqual(response.status, 206)
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGetIgnoreEtag(self):
        # Test that we can forcibly ignore ETags
        uri = urllib_parse.urljoin(base, "reflector/reflector.cgi")
        (response, content) = self.http.request(uri, "GET", headers={
            'accept-encoding': 'identity'})
        self.assertNotEqual(response['etag'], "")

        (response, content) = self.http.request(uri, "GET", headers={
            'accept-encoding': 'identity', 'cache-control': 'max-age=0'})
        d = self.reflector(content)
        self.assertTrue('HTTP_IF_NONE_MATCH' in d)

        self.http.ignore_etag = True
        (response, content) = self.http.request(uri, "GET", headers={
            'accept-encoding': 'identity', 'cache-control': 'max-age=0'})
        d = self.reflector(content)
        self.assertEqual(response.fromcache, False)
        self.assertFalse('HTTP_IF_NONE_MATCH' in d)

    @unittest.skipIf(not base, no_base_reason)
    def testOverrideEtag(self):
        # Test that we can forcibly ignore ETags
        uri = urllib_parse.urljoin(base, "reflector/reflector.cgi")
        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        self.assertNotEqual(response['etag'], "")

        (response, content) = self.http.request(
            uri, "GET", headers={
                'accept-encoding': 'identity',
                'cache-control': 'max-age=0'})
        d = self.reflector(content)
        self.assertTrue('HTTP_IF_NONE_MATCH' in d)
        self.assertNotEqual(d['HTTP_IF_NONE_MATCH'], "fred")

        (response, content) = self.http.request(
            uri, "GET", headers={
                'accept-encoding': 'identity',
                'cache-control': 'max-age=0',
                'if-none-match': 'fred'})
        d = self.reflector(content)
        self.assertTrue('HTTP_IF_NONE_MATCH' in d)
        self.assertEqual(d['HTTP_IF_NONE_MATCH'], "fred")

    @unittest.skipIf(not base, no_base_reason)
    def testGet304LastModified(self):
        # Test that we can still handle a 304
        # by only using the last-modified cache validator.
        uri = urllib_parse.urljoin(
            base, "304/last-modified-only/last-modified-only.txt")
        (response, content) = self.http.request(uri, "GET")

        self.assertNotEqual(response['last-modified'], "")
        (response, content) = self.http.request(uri, "GET")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)

    @unittest.skipIf(not base, no_base_reason)
    def testGet307(self):
        # Test that we do follow 307 redirects but
        # do not cache the 307
        uri = urllib_parse.urljoin(base, "307/onestep.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 307)
        self.assertEqual(response.previous.fromcache, False)

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)
        self.assertEqual(content, b"This is the final destination.\n")
        self.assertEqual(response.previous.status, 307)
        self.assertEqual(response.previous.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGet410(self):
        # Test that we pass 410's through
        uri = urllib_parse.urljoin(base, "410/410.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 410)

    @unittest.skipIf(not base, no_base_reason)
    def testVaryHeaderSimple(self):
        """
        RFC 2616 13.6
        When the cache receives a subsequent request whose Request-URI
        specifies one or more cache entries including a Vary header field,
        the cache MUST NOT use such a cache entry to construct a response
        to the new request unless all of the selecting request-headers
        present in the new request match the corresponding stored
        request-headers in the original request.
        """
        # test that the vary header is sent
        uri = urllib_parse.urljoin(base, "vary/accept.asis")
        (response, content) = self.http.request(
            uri, "GET", headers={'Accept': 'text/plain'})
        self.assertEqual(response.status, 200)
        self.assertTrue('vary' in response)

        # get the resource again, from the cache since accept header in this
        # request is the same as the request
        (response, content) = self.http.request(
            uri, "GET", headers={'Accept': 'text/plain'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True, msg="Should be from cache")

        # get the resource again, not from cache since Accept headers does not
        # match
        (response, content) = self.http.request(
            uri, "GET", headers={'Accept': 'text/html'})
        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.fromcache, False, msg="Should not be from cache")

        # get the resource again, without any Accept header, so again no match
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.fromcache, False, msg="Should not be from cache")

    @unittest.skipIf(not base, no_base_reason)
    def testVaryHeaderDouble(self):
        uri = urllib_parse.urljoin(base, "vary/accept-double.asis")
        (response, content) = self.http.request(uri, "GET", headers={
            'Accept': 'text/plain',
            'Accept-Language': 'da, en-gb;q=0.8, en;q=0.7'})
        self.assertEqual(response.status, 200)
        self.assertTrue('vary' in response)

        # we are from cache
        (response, content) = self.http.request(uri, "GET", headers={
            'Accept': 'text/plain',
            'Accept-Language': 'da, en-gb;q=0.8, en;q=0.7'})
        self.assertEqual(response.fromcache, True, msg="Should be from cache")

        (response, content) = self.http.request(
            uri, "GET", headers={'Accept': 'text/plain'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

        # get the resource again, not from cache, varied headers don't match
        # exact
        (response, content) = self.http.request(
            uri, "GET", headers={'Accept-Language': 'da'})
        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.fromcache, False, msg="Should not be from cache")

    @unittest.skipIf(not base, no_base_reason)
    def testVaryUnusedHeader(self):
        # A header's value is not considered to vary if it's not used at all.
        uri = urllib_parse.urljoin(base, "vary/unused-header.asis")
        (response, content) = self.http.request(uri, "GET", headers={
            'Accept': 'text/plain'})
        self.assertEqual(response.status, 200)
        self.assertTrue('vary' in response)

        # we are from cache
        (response, content) = self.http.request(
            uri, "GET", headers={'Accept': 'text/plain'})
        self.assertEqual(response.fromcache, True, msg="Should be from cache")

    @unittest.skipIf(not base, no_base_reason)
    def testHeadGZip(self):
        # Test that we don't try to decompress a HEAD response
        uri = urllib_parse.urljoin(base, "gzip/final-destination.txt")
        (response, content) = self.http.request(uri, "HEAD")
        self.assertEqual(response.status, 200)
        self.assertNotEqual(int(response['content-length']), 0)
        self.assertEqual(content, b"")

    @unittest.skipIf(not base, no_base_reason)
    def testGetGZip(self):
        # Test that we support gzip compression
        uri = urllib_parse.urljoin(base, "gzip/final-destination.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertFalse('content-encoding' in response)
        self.assertTrue('-content-encoding' in response)
        self.assertEqual(
            int(response['content-length']),
            len(b"This is the final destination.\n"))
        self.assertEqual(content, b"This is the final destination.\n")

    @unittest.skipIf(not base, no_base_reason)
    def testPostAndGZipResponse(self):
        uri = urllib_parse.urljoin(base, "gzip/post.cgi")
        (response, content) = self.http.request(uri, "POST", body=" ")
        self.assertEqual(response.status, 200)
        self.assertFalse('content-encoding' in response)
        self.assertTrue('-content-encoding' in response)

    @unittest.skipIf(not base, no_base_reason)
    def testGetGZipFailure(self):
        # Test that we raise a good exception when the gzip fails
        self.http.force_exception_to_status_code = False
        uri = urllib_parse.urljoin(base, "gzip/failed-compression.asis")
        try:
            (response, content) = self.http.request(uri, "GET")
            self.fail("Should never reach here")
        except httplib2.FailedToDecompressContent:
            pass
        except Exception:
            self.fail("Threw wrong kind of exception")

        # Re-run the test with out the exceptions
        self.http.force_exception_to_status_code = True

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 500)
        self.assertTrue(response.reason.startswith("Content purported"))

    @unittest.skipIf(not base, no_base_reason)
    def testIndividualTimeout(self):
        uri = urllib_parse.urljoin(base, "timeout/timeout.cgi")
        http = httplib2.Http(timeout=1)
        http.force_exception_to_status_code = True

        (response, content) = http.request(uri)
        self.assertEqual(response.status, 408)
        self.assertTrue(response.reason.startswith("Request Timeout"))
        self.assertTrue(content.startswith(b"Request Timeout"))

    @unittest.skipIf(not base, no_base_reason)
    def testGetDeflate(self):
        # Test that we support deflate compression
        uri = urllib_parse.urljoin(base, "deflate/deflated.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertFalse('content-encoding' in response)
        self.assertEqual(
            int(response['content-length']),
            len("This is the final destination."))
        self.assertEqual(content, b"This is the final destination.")

    @unittest.skipIf(not base, no_base_reason)
    def testGetDeflateFailure(self):
        # Test that we raise a good exception when the deflate fails
        self.http.force_exception_to_status_code = False

        uri = urllib_parse.urljoin(base, "deflate/failed-compression.asis")
        try:
            (response, content) = self.http.request(uri, "GET")
            self.fail("Should never reach here")
        except httplib2.FailedToDecompressContent:
            pass
        except Exception:
            self.fail("Threw wrong kind of exception")

        # Re-run the test with out the exceptions
        self.http.force_exception_to_status_code = True

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 500)
        self.assertTrue(response.reason.startswith("Content purported"))

    @unittest.skipIf(not base, no_base_reason)
    def testGetDuplicateHeaders(self):
        # Test that duplicate headers get concatenated via ','
        uri = urllib_parse.urljoin(base, "duplicate-headers/multilink.asis")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(content, b"This is content\n")
        self.assertEqual(
            response['link'].split(",")[0],
            '<http://bitworking.org>; rel="home"; title="BitWorking"')

    @unittest.skipIf(not base, no_base_reason)
    def testGetCacheControlNoCache(self):
        # Test Cache-Control: no-cache on requests
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        self.assertNotEqual(response['etag'], "")
        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)

        (response, content) = self.http.request(
            uri, "GET", headers={
                'accept-encoding': 'identity',
                'Cache-Control': 'no-cache'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGetCacheControlPragmaNoCache(self):
        # Test Pragma: no-cache on requests
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")
        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        self.assertNotEqual(response['etag'], "")
        (response, content) = self.http.request(
            uri, "GET", headers={'accept-encoding': 'identity'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)

        (response, content) = self.http.request(
            uri, "GET", headers={
                'accept-encoding': 'identity',
                'Pragma': 'no-cache'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGetCacheControlNoStoreRequest(self):
        # A no-store request means that the response should not be stored.
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")

        (response, content) = self.http.request(
            uri, "GET", headers={'Cache-Control': 'no-store'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

        (response, content) = self.http.request(
            uri, "GET", headers={'Cache-Control': 'no-store'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGetCacheControlNoStoreResponse(self):
        # A no-store response means that the response should not be stored.
        uri = urllib_parse.urljoin(base, "no-store/no-store.asis")

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testGetCacheControlNoCacheNoStoreRequest(self):
        # Test that a no-store, no-cache clears the entry from the cache
        # even if it was cached previously.
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")

        (response, content) = self.http.request(uri, "GET")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.fromcache, True)
        (response, content) = self.http.request(
            uri, "GET", headers={'Cache-Control': 'no-store, no-cache'})
        (response, content) = self.http.request(
            uri, "GET", headers={'Cache-Control': 'no-store, no-cache'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testUpdateInvalidatesCache(self):
        # Test that calling PUT or DELETE on a
        # URI that is cache invalidates that cache.
        uri = urllib_parse.urljoin(base, "304/test_etag.txt")

        (response, content) = self.http.request(uri, "GET")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.fromcache, True)
        (response, content) = self.http.request(uri, "DELETE")
        self.assertEqual(response.status, 405)

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.fromcache, False)

    @unittest.skipIf(not base, no_base_reason)
    def testUpdateUsesCachedETag(self):
        # Test that we natively support http://www.w3.org/1999/04/Editing/
        uri = urllib_parse.urljoin(base, "conditional-updates/test.cgi")

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)
        (response, content) = self.http.request(uri, "PUT", body="foo")
        self.assertEqual(response.status, 200)
        (response, content) = self.http.request(uri, "PUT", body="foo")
        self.assertEqual(response.status, 412)

    # NOTE: Disabled because it consistently fails for both the shim and normal
    # httplib2
    # def testUpdatePatchUsesCachedETag(self):
    #     # Test that we natively support http://www.w3.org/1999/04/Editing/
    #     uri = urllib_parse.urljoin(base, "conditional-updates/test.cgi")

    #     (response, content) = self.http.request(uri, "GET")
    #     self.assertEqual(response.status, 200)
    #     self.assertEqual(response.fromcache, False)
    #     (response, content) = self.http.request(uri, "GET")
    #     self.assertEqual(response.status, 200)
    #     self.assertEqual(response.fromcache, True)
    #     (response, content) = self.http.request(uri, "PATCH", body="foo")
    #     self.assertEqual(response.status, 200)
    #     (response, content) = self.http.request(uri, "PATCH", body="foo")
    #     self.assertEqual(response.status, 412)

    @unittest.skipIf(not base, no_base_reason)
    def testUpdateUsesCachedETagAndOCMethod(self):
        # Test that we natively support http://www.w3.org/1999/04/Editing/
        uri = urllib_parse.urljoin(base, "conditional-updates/test.cgi")

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)
        self.http.optimistic_concurrency_methods.append("DELETE")
        (response, content) = self.http.request(uri, "DELETE")
        self.assertEqual(response.status, 200)

    @unittest.skipIf(not base, no_base_reason)
    def testUpdateUsesCachedETagOverridden(self):
        # Test that we natively support http://www.w3.org/1999/04/Editing/
        uri = urllib_parse.urljoin(base, "conditional-updates/test.cgi")

        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, False)
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)
        self.assertEqual(response.fromcache, True)
        (response, content) = self.http.request(
            uri, "PUT", body="foo", headers={'if-match': 'fred'})
        self.assertEqual(response.status, 412)

    @unittest.skipIf(not base, no_base_reason)
    def testBasicAuth(self):
        # Test Basic Authentication
        uri = urllib_parse.urljoin(base, "basic/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        uri = urllib_parse.urljoin(base, "basic/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        self.http.add_credentials('joe', 'password')
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

        uri = urllib_parse.urljoin(base, "basic/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

    @unittest.skipIf(not base, no_base_reason)
    def testBasicAuthWithDomain(self):
        # Test Basic Authentication
        uri = urllib_parse.urljoin(base, "basic/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        uri = urllib_parse.urljoin(base, "basic/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        self.http.add_credentials('joe', 'password', "example.org")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        uri = urllib_parse.urljoin(base, "basic/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        domain = urllib_parse.urlparse(base)[1]
        self.http.add_credentials('joe', 'password', domain)
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

        uri = urllib_parse.urljoin(base, "basic/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

    @unittest.skipIf(not base, no_base_reason)
    def testBasicAuthTwoDifferentCredentials(self):
        # Test Basic Authentication with multiple sets of credentials
        uri = urllib_parse.urljoin(base, "basic2/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        uri = urllib_parse.urljoin(base, "basic2/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        self.http.add_credentials('fred', 'barney')
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

        uri = urllib_parse.urljoin(base, "basic2/file.txt")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

    @unittest.skipIf(not base, no_base_reason)
    def testBasicAuthNested(self):
        # Test Basic Authentication with resources
        # that are nested
        uri = urllib_parse.urljoin(base, "basic-nested/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        uri = urllib_parse.urljoin(base, "basic-nested/subdir")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        # Now add in credentials one at a time and test.
        self.http.add_credentials('joe', 'password')

        uri = urllib_parse.urljoin(base, "basic-nested/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

        uri = urllib_parse.urljoin(base, "basic-nested/subdir")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        self.http.add_credentials('fred', 'barney')

        uri = urllib_parse.urljoin(base, "basic-nested/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

        uri = urllib_parse.urljoin(base, "basic-nested/subdir")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

    @unittest.skipIf(not base, no_base_reason)
    def testDigestAuth(self):
        # Test that we support Digest Authentication
        uri = urllib_parse.urljoin(base, "digest/")
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 401)

        self.http.add_credentials('joe', 'password')
        (response, content) = self.http.request(uri, "GET")
        self.assertEqual(response.status, 200)

        uri = urllib_parse.urljoin(base, "digest/file.txt")
        (response, content) = self.http.request(uri, "GET")

    @unittest.skipIf(not base, no_base_reason)
    def testDigestAuthNextNonceAndNC(self):
        # Test that if the server sets nextnonce that we reset
        # the nonce count back to 1
        uri = urllib_parse.urljoin(base, "digest/file.txt")
        self.http.add_credentials('joe', 'password')
        (response, content) = self.http.request(
            uri, "GET", headers={"cache-control": "no-cache"})
        info = httplib2._parse_www_authenticate(
            response, 'authentication-info')
        self.assertEqual(response.status, 200)
        (response, content) = self.http.request(
            uri, "GET", headers={"cache-control": "no-cache"})
        info2 = httplib2._parse_www_authenticate(
            response, 'authentication-info')
        self.assertEqual(response.status, 200)

        if 'nextnonce' in info:
            self.assertEqual(info2['nc'], 1)

    @unittest.skipIf(not base, no_base_reason)
    def testDigestAuthStale(self):
        # Test that we can handle a nonce becoming stale
        uri = urllib_parse.urljoin(base, "digest-expire/file.txt")
        self.http.add_credentials('joe', 'password')
        (response, content) = self.http.request(
            uri, "GET", headers={"cache-control": "no-cache"})
        httplib2._parse_www_authenticate(response, 'authentication-info')
        self.assertEqual(response.status, 200)

        time.sleep(3)
        # Sleep long enough that the nonce becomes stale

        (response, content) = self.http.request(
            uri, "GET", headers={"cache-control": "no-cache"})
        self.assertFalse(response.fromcache)
        self.assertTrue(response._stale_digest)
        httplib2._parse_www_authenticate(response, 'authentication-info')
        self.assertEqual(response.status, 200)

    def reflector(self, content):
        return dict(
            [tuple(x.split("=", 1))
             for x in content.decode('utf-8').strip().split("\n")])

    @unittest.skipIf(not base, no_base_reason)
    def testReflector(self):
        uri = urllib_parse.urljoin(base, "reflector/reflector.cgi")
        (response, content) = self.http.request(uri, "GET")
        d = self.reflector(content)
        self.assertTrue('HTTP_USER_AGENT' in d)

    # NOTE: disabled because this isn't relevant to the shim.
    # def testConnectionClose(self):
    #     uri = "http://www.google.com/"
    #     (response, content) = self.http.request(uri, "GET")
    #     for c in self.http.connections.values():
    #         self.assertNotEqual(None, c.sock)
    #     (response, content) = self.http.request(
    #         uri, "GET", headers={"connection": "close"})
    #     for c in self.http.connections.values():
    #         self.assertEqual(None, c.sock)

    def testPickleHttp(self):
        pickled_http = pickle.dumps(self.http)
        new_http = pickle.loads(pickled_http)

        self.assertEqual(sorted(new_http.__dict__.keys()),
                         sorted(self.http.__dict__.keys()))
        for key in new_http.__dict__:
            if key == 'pool':
                continue
            if key in ('certificates', 'credentials'):
                self.assertEqual(new_http.__dict__[key].credentials,
                                 self.http.__dict__[key].credentials)
            elif key == 'cache':
                self.assertEqual(new_http.__dict__[key].cache,
                                 self.http.__dict__[key].cache)
            else:
                self.assertEqual(new_http.__dict__[key],
                                 self.http.__dict__[key])

    # NOTE: disabled because this isn't relevant to the shim.
    # def testPickleHttpWithConnection(self):
    #     self.http.request('http://bitworking.org',
    #                       connection_type=_MyHTTPConnection)
    #     pickled_http = pickle.dumps(self.http)
    #     new_http = pickle.loads(pickled_http)

    #     self.assertEqual(list(self.http.connections.keys()),
    #                      ['http:bitworking.org'])
    #     self.assertEqual(new_http.connections, {})

    # def testPickleCustomRequestHttp(self):
    #     def dummy_request(*args, **kwargs):
    #         return new_request(*args, **kwargs)
    #     dummy_request.dummy_attr = 'dummy_value'

    #     self.http.request = dummy_request
    #     pickled_http = pickle.dumps(self.http)
    #     self.assertFalse(b"S'request'" in pickled_http)


try:
    import memcache

    class HttpTestMemCached(HttpTest):
        def setUp(self):
            self.cache = memcache.Client(['127.0.0.1:11211'], debug=0)
            # self.cache = memcache.Client(['10.0.0.4:11211'], debug=1)
            self.http = httplib2.Http(self.cache)
            self.cache.flush_all()
            # Not exactly sure why the sleep is needed here, but
            # if not present then some unit tests that rely on caching
            # fail. Memcached seems to lose some sets immediately
            # after a flush_all if the set is to a value that
            # was previously cached. (Maybe the flush is handled async?)
            time.sleep(1)
            self.http.clear_credentials()
except:
    pass


# ------------------------------------------------------------------------

class HttpPrivateTest(unittest.TestCase):

    def testParseCacheControl(self):
        # Test that we can parse the Cache-Control header
        self.assertEqual({}, httplib2._parse_cache_control({}))
        self.assertEqual({'no-cache': 1}, httplib2._parse_cache_control(
            {'cache-control': ' no-cache'}))
        cc = httplib2._parse_cache_control(
            {'cache-control': ' no-cache, max-age = 7200'})
        self.assertEqual(cc['no-cache'], 1)
        self.assertEqual(cc['max-age'], '7200')
        cc = httplib2._parse_cache_control({'cache-control': ' , '})
        self.assertEqual(cc[''], 1)

        try:
            cc = httplib2._parse_cache_control(
                {'cache-control':
                    'Max-age=3600;post-check=1800,pre-check=3600'})
            self.assertTrue("max-age" in cc)
        except:
            self.fail("Should not throw exception")

    def testNormalizeHeaders(self):
        # Test that we normalize headers to lowercase
        h = httplib2._normalize_headers(
            {'Cache-Control': 'no-cache', 'Other': 'Stuff'})
        self.assertTrue('cache-control' in h)
        self.assertTrue('other' in h)
        self.assertEqual('Stuff', h['other'])

    def testConvertByteStr(self):
        if six.PY2:
            return

        with self.assertRaises(TypeError):
            httplib2._convert_byte_str(4)
        self.assertEqual(
            'Hello World', httplib2._convert_byte_str(b'Hello World'))
        self.assertEqual('Bye World', httplib2._convert_byte_str('Bye World'))

    def testExpirationModelTransparent(self):
        # Test that no-cache makes our request TRANSPARENT
        response_headers = {
            'cache-control': 'max-age=7200'
        }
        request_headers = {
            'cache-control': 'no-cache'
        }
        self.assertEqual(
            "TRANSPARENT",
            httplib2._entry_disposition(response_headers, request_headers))

    def testMaxAgeNonNumeric(self):
        # Test that no-cache makes our request TRANSPARENT
        response_headers = {
            'cache-control': 'max-age=fred, min-fresh=barney'
        }
        request_headers = {
        }
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelNoCacheResponse(self):
        # The date and expires point to an entry that should be
        # FRESH, but the no-cache over-rides that.
        now = time.time()
        response_headers = {
            'date':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            'expires':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now+4)),
            'cache-control': 'no-cache'
        }
        request_headers = {}
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelStaleRequestMustReval(self):
        # must-revalidate forces STALE
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(
                {}, {'cache-control': 'must-revalidate'}))

    def testExpirationModelStaleResponseMustReval(self):
        # must-revalidate forces STALE
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(
                {'cache-control': 'must-revalidate'}, {}))

    def testExpirationModelFresh(self):
        response_headers = {
            'date': time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            'cache-control': 'max-age=2'
        }
        request_headers = {}
        self.assertEqual(
            "FRESH",
            httplib2._entry_disposition(response_headers, request_headers))
        time.sleep(3)
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationMaxAge0(self):
        response_headers = {
            'date': time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
            'cache-control': 'max-age=0'
        }
        request_headers = {}
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelDateAndExpires(self):
        now = time.time()
        response_headers = {
            'date':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            'expires':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now+2)),
        }
        request_headers = {}
        self.assertEqual(
            "FRESH",
            httplib2._entry_disposition(response_headers, request_headers))
        time.sleep(3)
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpiresZero(self):
        now = time.time()
        response_headers = {
            'date':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            'expires': "0",
        }
        request_headers = {}
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelDateOnly(self):
        now = time.time()
        response_headers = {
            'date': time.strftime(
                "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now+3)),
        }
        request_headers = {}
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelOnlyIfCached(self):
        response_headers = {
        }
        request_headers = {
            'cache-control': 'only-if-cached',
        }
        self.assertEqual(
            "FRESH",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelMaxAgeBoth(self):
        now = time.time()
        response_headers = {
            'date':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            'cache-control': 'max-age=2'
        }
        request_headers = {
            'cache-control': 'max-age=0'
        }
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelDateAndExpiresMinFresh1(self):
        now = time.time()
        response_headers = {
            'date':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            'expires':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now+2)),
        }
        request_headers = {
            'cache-control': 'min-fresh=2'
        }
        self.assertEqual(
            "STALE",
            httplib2._entry_disposition(response_headers, request_headers))

    def testExpirationModelDateAndExpiresMinFresh2(self):
        now = time.time()
        response_headers = {
            'date':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            'expires':
                time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now+4)),
        }
        request_headers = {
            'cache-control': 'min-fresh=2'
        }
        self.assertEqual(
            "FRESH",
            httplib2._entry_disposition(response_headers, request_headers))

    def testParseWWWAuthenticateEmpty(self):
        res = httplib2._parse_www_authenticate({})
        self.assertEqual(len(list(res.keys())), 0)

    def testParseWWWAuthenticate(self):
        # different uses of spaces around commas
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                'Test realm="test realm" , foo=foo ,bar="bar", baz=baz,qux=qux'
            })
        self.assertEqual(len(list(res.keys())), 1)
        self.assertEqual(len(list(res['test'].keys())), 5)

        # tokens with non-alphanum
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                'T*!%#st realm=to*!%#en, to*!%#en="quoted string"'})
        self.assertEqual(len(list(res.keys())), 1)
        self.assertEqual(len(list(res['t*!%#st'].keys())), 2)

        # quoted string with quoted pairs
        res = httplib2._parse_www_authenticate({
            'www-authenticate': 'Test realm="a \\"test\\" realm"'})
        self.assertEqual(len(list(res.keys())), 1)
        self.assertEqual(res['test']['realm'], 'a "test" realm')

    def testParseWWWAuthenticateStrict(self):
        httplib2.USE_WWW_AUTH_STRICT_PARSING = 1
        self.testParseWWWAuthenticate()
        httplib2.USE_WWW_AUTH_STRICT_PARSING = 0

    def testParseWWWAuthenticateBasic(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate': 'Basic realm="me"'})
        basic = res['basic']
        self.assertEqual('me', basic['realm'])

        res = httplib2._parse_www_authenticate({
            'www-authenticate': 'Basic realm="me", algorithm="MD5"'})
        basic = res['basic']
        self.assertEqual('me', basic['realm'])
        self.assertEqual('MD5', basic['algorithm'])

        res = httplib2._parse_www_authenticate({
            'www-authenticate': 'Basic realm="me", algorithm=MD5'})
        basic = res['basic']
        self.assertEqual('me', basic['realm'])
        self.assertEqual('MD5', basic['algorithm'])

    def testParseWWWAuthenticateBasic2(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate': 'Basic realm="me",other="fred" '})
        basic = res['basic']
        self.assertEqual('me', basic['realm'])
        self.assertEqual('fred', basic['other'])

    def testParseWWWAuthenticateBasic3(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate': 'Basic REAlm="me" '})
        basic = res['basic']
        self.assertEqual('me', basic['realm'])

    def testParseWWWAuthenticateDigest(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                ('Digest realm="testrealm@host.com", '
                 'qop="auth,auth-int", '
                 'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
                 'opaque="5ccc069c403ebaf9f0171e9517f40e41"')})
        digest = res['digest']
        self.assertEqual('testrealm@host.com', digest['realm'])
        self.assertEqual('auth,auth-int', digest['qop'])

    def testParseWWWAuthenticateMultiple(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                ('Digest realm="testrealm@host.com", '
                 'qop="auth,auth-int", '
                 'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
                 'opaque="5ccc069c403ebaf9f0171e9517f40e41" '
                 'Basic REAlm="me" ')})
        digest = res['digest']
        self.assertEqual('testrealm@host.com', digest['realm'])
        self.assertEqual('auth,auth-int', digest['qop'])
        self.assertEqual('dcd98b7102dd2f0e8b11d0f600bfb0c093', digest['nonce'])
        self.assertEqual('5ccc069c403ebaf9f0171e9517f40e41', digest['opaque'])
        basic = res['basic']
        self.assertEqual('me', basic['realm'])

    def testParseWWWAuthenticateMultiple2(self):
        # Handle an added comma between challenges, which might get thrown in
        # if the challenges were originally sent in separate www-authenticate
        # headers.
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                ('Digest realm="testrealm@host.com", '
                 'qop="auth,auth-int", '
                 'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
                 'opaque="5ccc069c403ebaf9f0171e9517f40e41", '
                 'Basic REAlm="me" ')})
        digest = res['digest']
        self.assertEqual('testrealm@host.com', digest['realm'])
        self.assertEqual('auth,auth-int', digest['qop'])
        self.assertEqual('dcd98b7102dd2f0e8b11d0f600bfb0c093', digest['nonce'])
        self.assertEqual('5ccc069c403ebaf9f0171e9517f40e41', digest['opaque'])
        basic = res['basic']
        self.assertEqual('me', basic['realm'])

    def testParseWWWAuthenticateMultiple3(self):
        # Handle an added comma between challenges, which might get thrown in
        # if the challenges were originally sent in separate www-authenticate
        # headers.
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                ('Digest realm="testrealm@host.com", '
                 'qop="auth,auth-int", '
                 'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
                 'opaque="5ccc069c403ebaf9f0171e9517f40e41", '
                 'Basic REAlm="me", '
                 'WSSE realm="foo", '
                 'profile="UsernameToken"')})
        digest = res['digest']
        self.assertEqual('testrealm@host.com', digest['realm'])
        self.assertEqual('auth,auth-int', digest['qop'])
        self.assertEqual('dcd98b7102dd2f0e8b11d0f600bfb0c093', digest['nonce'])
        self.assertEqual('5ccc069c403ebaf9f0171e9517f40e41', digest['opaque'])
        basic = res['basic']
        self.assertEqual('me', basic['realm'])
        wsse = res['wsse']
        self.assertEqual('foo', wsse['realm'])
        self.assertEqual('UsernameToken', wsse['profile'])

    def testParseWWWAuthenticateMultiple4(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                ('Digest realm="test-real.m@host.com", '
                 'qop \t=\t"\tauth,auth-int", nonce="(*)&^&$%#", '
                 'opaque="5ccc069c403ebaf9f0171e9517f40e41", '
                 'Basic REAlm="me", '
                 'WSSE realm="foo", profile="UsernameToken"')})
        digest = res['digest']
        self.assertEqual('test-real.m@host.com', digest['realm'])
        self.assertEqual('\tauth,auth-int', digest['qop'])
        self.assertEqual('(*)&^&$%#', digest['nonce'])

    def testParseWWWAuthenticateMoreQuoteCombos(self):
        res = httplib2._parse_www_authenticate({
            'www-authenticate':
                ('Digest realm="myrealm", '
                 'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306"'
                 ', algorithm=MD5, qop="auth", stale=true')})
        digest = res['digest']
        self.assertEqual('myrealm', digest['realm'])

    def testParseWWWAuthenticateMalformed(self):
        try:
            httplib2._parse_www_authenticate({
                'www-authenticate': (
                    'OAuth "Facebook Platform" "invalid_token" '
                    '"Invalid OAuth access token."')})
            self.fail("should raise an exception")
        except httplib2.MalformedHeader:
            pass

    def testDigestObject(self):
        credentials = ('joe', 'password')
        host = None
        request_uri = '/projects/httplib2/test/digest/'
        headers = {}
        response = {
            'www-authenticate': (
                'Digest realm="myrealm", '
                'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306",'
                ' algorithm=MD5, qop="auth"')
        }
        content = b""

        d = httplib2.DigestAuthentication(
            credentials, host, request_uri, headers, response, content, None)
        d.request(
            "GET", request_uri, headers, content, cnonce="33033375ec278a46")
        our_request = "authorization: %s" % headers['authorization']
        working_request = (
            'authorization: Digest username="joe", '
            'realm="myrealm", '
            'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306", '
            'uri="/projects/httplib2/test/digest/", algorithm=MD5, '
            'response="97ed129401f7cdc60e5db58a80f3ea8b", qop=auth, '
            'nc=00000001, cnonce="33033375ec278a46"')
        self.assertEqual(our_request, working_request)

    def testDigestObjectWithOpaque(self):
        credentials = ('joe', 'password')
        host = None
        request_uri = '/projects/httplib2/test/digest/'
        headers = {}
        response = {
            'www-authenticate':
                ('Digest realm="myrealm", '
                 'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306"'
                 ', algorithm=MD5, qop="auth", opaque="atestopaque"')
        }
        content = ""

        d = httplib2.DigestAuthentication(
            credentials, host, request_uri, headers, response, content, None)
        d.request(
            "GET", request_uri, headers, content, cnonce="33033375ec278a46")
        our_request = "authorization: %s" % headers['authorization']
        working_request = (
            'authorization: Digest username="joe", '
            'realm="myrealm", '
            'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306", '
            'uri="/projects/httplib2/test/digest/", '
            'algorithm=MD5, '
            'response="97ed129401f7cdc60e5db58a80f3ea8b", '
            'qop=auth, nc=00000001, cnonce="33033375ec278a46", '
            'opaque="atestopaque"')
        self.assertEqual(our_request, working_request)

    def testDigestObjectStale(self):
        credentials = ('joe', 'password')
        host = None
        request_uri = '/projects/httplib2/test/digest/'
        headers = {}
        response = httplib2.Response({})
        response['www-authenticate'] = (
            'Digest realm="myrealm", '
            'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306", '
            'algorithm=MD5, qop="auth", stale=true')
        response.status = 401
        content = b""
        d = httplib2.DigestAuthentication(
            credentials, host, request_uri, headers, response, content, None)
        # Returns true to force a retry
        self.assertTrue(d.response(response, content))

    def testDigestObjectAuthInfo(self):
        credentials = ('joe', 'password')
        host = None
        request_uri = '/projects/httplib2/test/digest/'
        headers = {}
        response = httplib2.Response({})
        response['www-authenticate'] = (
            'Digest realm="myrealm", '
            'nonce="Ygk86AsKBAA=3516200d37f9a3230352fde99977bd6d472d4306", '
            'algorithm=MD5, qop="auth", stale=true')
        response['authentication-info'] = 'nextnonce="fred"'
        content = b""
        d = httplib2.DigestAuthentication(
            credentials, host, request_uri, headers, response, content, None)
        # Returns true to force a retry
        self.assertFalse(d.response(response, content))
        self.assertEqual('fred', d.challenge['nonce'])
        self.assertEqual(1, d.challenge['nc'])

    def testWsseAlgorithm(self):
        digest = httplib2._wsse_username_token(
            "d36e316282959a9ed4c89851497a717f",
            "2003-12-15T14:43:07Z",
            "taadtaadpstcsm")
        expected = b"quR/EWLAV4xLf9Zqyw4pDmfV9OY="
        self.assertEqual(expected, digest)

    def testEnd2End(self):
        # one end to end header
        response = {'content-type': 'application/atom+xml', 'te': 'deflate'}
        end2end = httplib2._get_end2end_headers(response)
        self.assertTrue('content-type' in end2end)
        self.assertTrue('te' not in end2end)
        self.assertTrue('connection' not in end2end)

        # one end to end header that gets eliminated
        response = {
            'connection': 'content-type',
            'content-type': 'application/atom+xml',
            'te': 'deflate'}
        end2end = httplib2._get_end2end_headers(response)
        self.assertTrue('content-type' not in end2end)
        self.assertTrue('te' not in end2end)
        self.assertTrue('connection' not in end2end)

        # Degenerate case of no headers
        response = {}
        end2end = httplib2._get_end2end_headers(response)
        self.assertEqual(0, len(end2end))

        # Degenerate case of connection referrring to a header not passed in
        response = {'connection': 'content-type'}
        end2end = httplib2._get_end2end_headers(response)
        self.assertEqual(0, len(end2end))


class TestProxyInfo(unittest.TestCase):
    def setUp(self):
        self.orig_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)

    def test_from_url(self):
        pi = httplib2.proxy_info_from_url('http://myproxy.example.com')
        self.assertEqual(pi.proxy_host, 'myproxy.example.com')
        self.assertEqual(pi.proxy_port, 80)
        self.assertEqual(pi.proxy_user, None)

    def test_from_url_ident(self):
        pi = httplib2.proxy_info_from_url('http://zoidberg:fish@someproxy:99')
        self.assertEqual(pi.proxy_host, 'someproxy')
        self.assertEqual(pi.proxy_port, 99)
        self.assertEqual(pi.proxy_user, 'zoidberg')
        self.assertEqual(pi.proxy_pass, 'fish')

    def test_from_env(self):
        os.environ['http_proxy'] = 'http://myproxy.example.com:8080'
        pi = httplib2.proxy_info_from_environment()
        self.assertEqual(pi.proxy_host, 'myproxy.example.com')
        self.assertEqual(pi.proxy_port, 8080)

    def test_from_env_no_proxy(self):
        os.environ['http_proxy'] = 'http://myproxy.example.com:80'
        os.environ['https_proxy'] = 'http://myproxy.example.com:81'
        pi = httplib2.proxy_info_from_environment('https')
        self.assertEqual(pi.proxy_host, 'myproxy.example.com')
        self.assertEqual(pi.proxy_port, 81)

    def test_from_env_none(self):
        os.environ.clear()
        pi = httplib2.proxy_info_from_environment()
        self.assertEqual(pi, None)


class HttpShimProxyPoolTest(unittest.TestCase):

    def test_none(self):
        http = httplib2.Http(proxy_info=None)
        self.assertIsInstance(http.pool, urllib3.PoolManager)
        http = httplib2.Http(proxy_info=lambda: None)
        self.assertIsInstance(http.pool, urllib3.PoolManager)

    def test_instance_and_callable(self):
        proxy_info = httplib2.proxy_info_from_url('http://myproxy.example.com')
        http = httplib2.Http(proxy_info=proxy_info)
        self.assertIsInstance(http.pool, urllib3.ProxyManager)
        http = httplib2.Http(proxy_info=lambda: proxy_info)
        self.assertIsInstance(http.pool, urllib3.ProxyManager)
