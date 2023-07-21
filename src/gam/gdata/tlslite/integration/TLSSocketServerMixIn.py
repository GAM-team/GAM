"""TLS Lite + SocketServer."""

from gdata.tlslite.TLSConnection import TLSConnection

class TLSSocketServerMixIn:
    """
    This class can be mixed in with any L{SocketServer.TCPServer} to
    add TLS support.

    To use this class, define a new class that inherits from it and
    some L{SocketServer.TCPServer} (with the mix-in first). Then
    implement the handshake() method, doing some sort of server
    handshake on the connection argument.  If the handshake method
    returns True, the RequestHandler will be triggered.  Below is a
    complete example of a threaded HTTPS server::

        from SocketServer import *
        from BaseHTTPServer import *
        from SimpleHTTPServer import *
        from tlslite.api import *

        s = open("./serverX509Cert.pem").read()
        x509 = X509()
        x509.parse(s)
        certChain = X509CertChain([x509])

        s = open("./serverX509Key.pem").read()
        privateKey = parsePEMKey(s, private=True)

        sessionCache = SessionCache()

        class MyHTTPServer(ThreadingMixIn, TLSSocketServerMixIn,
                           HTTPServer):
          def handshake(self, tlsConnection):
              try:
                  tlsConnection.handshakeServer(certChain=certChain,
                                                privateKey=privateKey,
                                                sessionCache=sessionCache)
                  tlsConnection.ignoreAbruptClose = True
                  return True
              except TLSError, error:
                  print "Handshake failure:", str(error)
                  return False

        httpd = MyHTTPServer(('localhost', 443), SimpleHTTPRequestHandler)
        httpd.serve_forever()
    """


    def finish_request(self, sock, client_address):
        tlsConnection = TLSConnection(sock)
        if self.handshake(tlsConnection) == True:
            self.RequestHandlerClass(tlsConnection, client_address, self)
            tlsConnection.close()

    #Implement this method to do some form of handshaking.  Return True
    #if the handshake finishes properly and the request is authorized.
    def handshake(self, tlsConnection):
        raise NotImplementedError()
