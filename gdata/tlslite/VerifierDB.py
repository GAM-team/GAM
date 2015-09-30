"""Class for storing SRP password verifiers."""

from utils.cryptomath import *
from utils.compat import *
import mathtls
from BaseDB import BaseDB

class VerifierDB(BaseDB):
    """This class represent an in-memory or on-disk database of SRP
    password verifiers.

    A VerifierDB can be passed to a server handshake to authenticate
    a client based on one of the verifiers.

    This class is thread-safe.
    """
    def __init__(self, filename=None):
        """Create a new VerifierDB instance.

        @type filename: str
        @param filename: Filename for an on-disk database, or None for
        an in-memory database.  If the filename already exists, follow
        this with a call to open().  To create a new on-disk database,
        follow this with a call to create().
        """
        BaseDB.__init__(self, filename, "verifier")

    def _getItem(self, username, valueStr):
        (N, g, salt, verifier) = valueStr.split(" ")
        N = base64ToNumber(N)
        g = base64ToNumber(g)
        salt = base64ToString(salt)
        verifier = base64ToNumber(verifier)
        return (N, g, salt, verifier)

    def __setitem__(self, username, verifierEntry):
        """Add a verifier entry to the database.

        @type username: str
        @param username: The username to associate the verifier with.
        Must be less than 256 characters in length.  Must not already
        be in the database.

        @type verifierEntry: tuple
        @param verifierEntry: The verifier entry to add.  Use
        L{tlslite.VerifierDB.VerifierDB.makeVerifier} to create a
        verifier entry.
        """
        BaseDB.__setitem__(self, username, verifierEntry)


    def _setItem(self, username, value):
        if len(username)>=256:
            raise ValueError("username too long")
        N, g, salt, verifier = value
        N = numberToBase64(N)
        g = numberToBase64(g)
        salt = stringToBase64(salt)
        verifier = numberToBase64(verifier)
        valueStr = " ".join( (N, g, salt, verifier)  )
        return valueStr

    def _checkItem(self, value, username, param):
        (N, g, salt, verifier) = value
        x = mathtls.makeX(salt, username, param)
        v = powMod(g, x, N)
        return (verifier == v)


    def makeVerifier(username, password, bits):
        """Create a verifier entry which can be stored in a VerifierDB.

        @type username: str
        @param username: The username for this verifier.  Must be less
        than 256 characters in length.

        @type password: str
        @param password: The password for this verifier.

        @type bits: int
        @param bits: This values specifies which SRP group parameters
        to use.  It must be one of (1024, 1536, 2048, 3072, 4096, 6144,
        8192).  Larger values are more secure but slower.  2048 is a
        good compromise between safety and speed.

        @rtype: tuple
        @return: A tuple which may be stored in a VerifierDB.
        """
        return mathtls.makeVerifier(username, password, bits)
    makeVerifier = staticmethod(makeVerifier)