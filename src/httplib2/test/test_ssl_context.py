#!/usr/bin/python2
import BaseHTTPServer
import logging
import os.path
import unittest
import sys

import httplib2

from httplib2.test import miniserver

logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    Request handler that keeps the HTTP connection open, so that the test can
    inspect the resulting SSL connection object
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        self.close_connection = 0

    def log_message(self, s, *args):
        # output via logging so nose can catch it
        logger.info(s, *args)

class HttpsContextTest(unittest.TestCase):
    def setUp(self):
        if sys.version_info < (2, 7, 9):
            return

        self.httpd, self.port = miniserver.start_server(
            KeepAliveHandler, True)

    def tearDown(self):
        self.httpd.shutdown()

    def testHttpsContext(self):
        if sys.version_info < (2, 7, 9):
            if hasattr(unittest, "skipTest"):
                self.skipTest("SSLContext requires Python 2.7.9")# Python 2.7.0
            else:
                return
        import ssl

        client = httplib2.Http(
            ca_certs=os.path.join(os.path.dirname(__file__), 'server.pem'))

        # Establish connection to local server
        client.request('https://localhost:%d/' % (self.port))

        # Verify that connection uses a TLS context with the correct hostname
        conn = client.connections['https:localhost:%d' % self.port]

        self.assertIsInstance(conn.sock, ssl.SSLSocket)
        self.assertTrue(hasattr(conn.sock, 'context'))
        self.assertIsInstance(conn.sock.context, ssl.SSLContext)
        self.assertTrue(conn.sock.context.check_hostname)
        self.assertEqual(conn.sock.server_hostname, 'localhost')
        self.assertEqual(conn.sock.context.check_hostname, True)
        self.assertEqual(conn.sock.context.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(conn.sock.context.protocol, ssl.PROTOCOL_SSLv23)
