"""Class for storing shared keys."""

from utils.cryptomath import *
from utils.compat import *
from mathtls import *
from Session import Session
from BaseDB import BaseDB

class SharedKeyDB(BaseDB):
    """This class represent an in-memory or on-disk database of shared
    keys.

    A SharedKeyDB can be passed to a server handshake function to
    authenticate a client based on one of the shared keys.

    This class is thread-safe.
    """

    def __init__(self, filename=None):
        """Create a new SharedKeyDB.

        @type filename: str
        @param filename: Filename for an on-disk database, or None for
        an in-memory database.  If the filename already exists, follow
        this with a call to open().  To create a new on-disk database,
        follow this with a call to create().
        """
        BaseDB.__init__(self, filename, "shared key")

    def _getItem(self, username, valueStr):
        session = Session()
        session._createSharedKey(username, valueStr)
        return session

    def __setitem__(self, username, sharedKey):
        """Add a shared key to the database.

        @type username: str
        @param username: The username to associate the shared key with.
        Must be less than or equal to 16 characters in length, and must
        not already be in the database.

        @type sharedKey: str
        @param sharedKey: The shared key to add.  Must be less than 48
        characters in length.
        """
        BaseDB.__setitem__(self, username, sharedKey)

    def _setItem(self, username, value):
        if len(username)>16:
            raise ValueError("username too long")
        if len(value)>=48:
            raise ValueError("shared key too long")
        return value

    def _checkItem(self, value, username, param):
        newSession = self._getItem(username, param)
        return value.masterSecret == newSession.masterSecret