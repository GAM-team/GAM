"""TLS Lite + smtplib."""

from smtplib import SMTP
from gdata.tlslite.TLSConnection import TLSConnection
from gdata.tlslite.integration.ClientHelper import ClientHelper

class SMTP_TLS(SMTP):
    """This class extends L{smtplib.SMTP} with TLS support."""

    def starttls(self,
                 username=None, password=None, sharedKey=None,
                 certChain=None, privateKey=None,
                 cryptoID=None, protocol=None,
                 x509Fingerprint=None,
                 x509TrustList=None, x509CommonName=None,
                 settings=None):
        """Puts the connection to the SMTP server into TLS mode.

        If the server supports TLS, this will encrypt the rest of the SMTP
        session.

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
        (resp, reply) = self.docmd("STARTTLS")
        if resp == 220:
            helper = ClientHelper(
                     username, password, sharedKey,
                     certChain, privateKey,
                     cryptoID, protocol,
                     x509Fingerprint,
                     x509TrustList, x509CommonName,
                     settings)
            conn = TLSConnection(self.sock)
            conn.closeSocket = True
            helper._handshake(conn)
            self.sock = conn
            self.file = conn.makefile('rb')
        return (resp, reply)
