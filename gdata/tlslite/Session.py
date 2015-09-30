"""Class representing a TLS session."""

from utils.compat import *
from mathtls import *
from constants import *

class Session:
    """
    This class represents a TLS session.

    TLS distinguishes between connections and sessions.  A new
    handshake creates both a connection and a session.  Data is
    transmitted over the connection.

    The session contains a more permanent record of the handshake.  The
    session can be inspected to determine handshake results.  The
    session can also be used to create a new connection through
    "session resumption". If the client and server both support this,
    they can create a new connection based on an old session without
    the overhead of a full handshake.

    The session for a L{tlslite.TLSConnection.TLSConnection} can be
    retrieved from the connection's 'session' attribute.

    @type srpUsername: str
    @ivar srpUsername: The client's SRP username (or None).

    @type sharedKeyUsername: str
    @ivar sharedKeyUsername: The client's shared-key username (or
    None).

    @type clientCertChain: L{tlslite.X509CertChain.X509CertChain} or
    L{cryptoIDlib.CertChain.CertChain}
    @ivar clientCertChain: The client's certificate chain (or None).

    @type serverCertChain: L{tlslite.X509CertChain.X509CertChain} or
    L{cryptoIDlib.CertChain.CertChain}
    @ivar serverCertChain: The server's certificate chain (or None).
    """

    def __init__(self):
        self.masterSecret = createByteArraySequence([])
        self.sessionID = createByteArraySequence([])
        self.cipherSuite = 0
        self.srpUsername = None
        self.sharedKeyUsername = None
        self.clientCertChain = None
        self.serverCertChain = None
        self.resumable = False
        self.sharedKey = False

    def _clone(self):
        other = Session()
        other.masterSecret = self.masterSecret
        other.sessionID = self.sessionID
        other.cipherSuite = self.cipherSuite
        other.srpUsername = self.srpUsername
        other.sharedKeyUsername = self.sharedKeyUsername
        other.clientCertChain = self.clientCertChain
        other.serverCertChain = self.serverCertChain
        other.resumable = self.resumable
        other.sharedKey = self.sharedKey
        return other

    def _calcMasterSecret(self, version, premasterSecret, clientRandom,
                         serverRandom):
        if version == (3,0):
            self.masterSecret = PRF_SSL(premasterSecret,
                                concatArrays(clientRandom, serverRandom), 48)
        elif version in ((3,1), (3,2)):
            self.masterSecret = PRF(premasterSecret, "master secret",
                                concatArrays(clientRandom, serverRandom), 48)
        else:
            raise AssertionError()

    def valid(self):
        """If this session can be used for session resumption.

        @rtype: bool
        @return: If this session can be used for session resumption.
        """
        return self.resumable or self.sharedKey

    def _setResumable(self, boolean):
        #Only let it be set if this isn't a shared key
        if not self.sharedKey:
            #Only let it be set to True if the sessionID is non-null
            if (not boolean) or (boolean and self.sessionID):
                self.resumable = boolean

    def getCipherName(self):
        """Get the name of the cipher used with this connection.

        @rtype: str
        @return: The name of the cipher used with this connection.
        Either 'aes128', 'aes256', 'rc4', or '3des'.
        """
        if self.cipherSuite in CipherSuite.aes128Suites:
            return "aes128"
        elif self.cipherSuite in CipherSuite.aes256Suites:
            return "aes256"
        elif self.cipherSuite in CipherSuite.rc4Suites:
            return "rc4"
        elif self.cipherSuite in CipherSuite.tripleDESSuites:
            return "3des"
        else:
            return None

    def _createSharedKey(self, sharedKeyUsername, sharedKey):
        if len(sharedKeyUsername)>16:
            raise ValueError()
        if len(sharedKey)>47:
            raise ValueError()

        self.sharedKeyUsername = sharedKeyUsername

        self.sessionID = createByteArrayZeros(16)
        for x in range(len(sharedKeyUsername)):
            self.sessionID[x] = ord(sharedKeyUsername[x])

        premasterSecret = createByteArrayZeros(48)
        sharedKey = chr(len(sharedKey)) + sharedKey
        for x in range(48):
            premasterSecret[x] = ord(sharedKey[x % len(sharedKey)])

        self.masterSecret = PRF(premasterSecret, "shared secret",
                                createByteArraySequence([]), 48)
        self.sharedKey = True
        return self


