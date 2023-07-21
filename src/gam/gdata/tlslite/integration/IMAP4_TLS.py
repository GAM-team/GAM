"""TLS Lite + imaplib."""

import socket
from imaplib import IMAP4
from gdata.tlslite.TLSConnection import TLSConnection
from gdata.tlslite.integration.ClientHelper import ClientHelper

# IMAP TLS PORT
IMAP4_TLS_PORT = 993

class IMAP4_TLS(IMAP4, ClientHelper):
    """This class extends L{imaplib.IMAP4} with TLS support."""

    def __init__(self, host = '', port = IMAP4_TLS_PORT,
                 username=None, password=None, sharedKey=None,
                 certChain=None, privateKey=None,
                 cryptoID=None, protocol=None,
                 x509Fingerprint=None,
                 x509TrustList=None, x509CommonName=None,
                 settings=None):
        """Create a new IMAP4_TLS.

        For client authentication, use one of these argument
        combinations:
         - username, password (SRP)
         - username, sharedKey (shared-key)
         - certChain, privateKey (certificate)

        For server authentication, you can either rely on the
        implicit mutual authentication performed by SRP or
        shared-keys, or you can do certificate-based server
        authentication with one of these argument combinations:
         - cryptoID[, protocol] (requires cryptoIDlib)
         - x509Fingerprint
         - x509TrustList[, x509CommonName] (requires cryptlib_py)

        Certificate-based server authentication is compatible with
        SRP or certificate-based client authentication.  It is
        not compatible with shared-keys.

        The caller should be prepared to handle TLS-specific
        exceptions.  See the client handshake functions in
        L{tlslite.TLSConnection.TLSConnection} for details on which
        exceptions might be raised.

        @type host: str
        @param host: Server to connect to.

        @type port: int
        @param port: Port to connect to.

        @type username: str
        @param username: SRP or shared-key username.  Requires the
        'password' or 'sharedKey' argument.

        @type password: str
        @param password: SRP password for mutual authentication.
        Requires the 'username' argument.

        @type sharedKey: str
        @param sharedKey: Shared key for mutual authentication.
        Requires the 'username' argument.

        @type certChain: L{tlslite.X509CertChain.X509CertChain} or
        L{cryptoIDlib.CertChain.CertChain}
        @param certChain: Certificate chain for client authentication.
        Requires the 'privateKey' argument.  Excludes the SRP or
        shared-key related arguments.

        @type privateKey: L{tlslite.utils.RSAKey.RSAKey}
        @param privateKey: Private key for client authentication.
        Requires the 'certChain' argument.  Excludes the SRP or
        shared-key related arguments.

        @type cryptoID: str
        @param cryptoID: cryptoID for server authentication.  Mutually
        exclusive with the 'x509...' arguments.

        @type protocol: str
        @param protocol: cryptoID protocol URI for server
        authentication.  Requires the 'cryptoID' argument.

        @type x509Fingerprint: str
        @param x509Fingerprint: Hex-encoded X.509 fingerprint for
        server authentication.  Mutually exclusive with the 'cryptoID'
        and 'x509TrustList' arguments.

        @type x509TrustList: list of L{tlslite.X509.X509}
        @param x509TrustList: A list of trusted root certificates.  The
        other party must present a certificate chain which extends to
        one of these root certificates.  The cryptlib_py module must be
        installed to use this parameter.  Mutually exclusive with the
        'cryptoID' and 'x509Fingerprint' arguments.

        @type x509CommonName: str
        @param x509CommonName: The end-entity certificate's 'CN' field
        must match this value.  For a web server, this is typically a
        server name such as 'www.amazon.com'.  Mutually exclusive with
        the 'cryptoID' and 'x509Fingerprint' arguments.  Requires the
        'x509TrustList' argument.

        @type settings: L{tlslite.HandshakeSettings.HandshakeSettings}
        @param settings: Various settings which can be used to control
        the ciphersuites, certificate types, and SSL/TLS versions
        offered by the client.
        """

        ClientHelper.__init__(self,
                 username, password, sharedKey,
                 certChain, privateKey,
                 cryptoID, protocol,
                 x509Fingerprint,
                 x509TrustList, x509CommonName,
                 settings)

        IMAP4.__init__(self, host, port)


    def open(self, host = '', port = IMAP4_TLS_PORT):
        """Setup connection to remote server on "host:port".

        This connection will be used by the routines:
        read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock = TLSConnection(self.sock)
        self.sock.closeSocket = True
        ClientHelper._handshake(self, self.sock)
        self.file = self.sock.makefile('rb')
