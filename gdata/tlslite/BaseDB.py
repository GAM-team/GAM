"""Base class for SharedKeyDB and VerifierDB."""

import anydbm
import thread

class BaseDB:
    def __init__(self, filename, type):
        self.type = type
        self.filename = filename
        if self.filename:
            self.db = None
        else:
            self.db = {}
        self.lock = thread.allocate_lock()

    def create(self):
        """Create a new on-disk database.

        @raise anydbm.error: If there's a problem creating the database.
        """
        if self.filename:
            self.db = anydbm.open(self.filename, "n") #raises anydbm.error
            self.db["--Reserved--type"] = self.type
            self.db.sync()
        else:
            self.db = {}

    def open(self):
        """Open a pre-existing on-disk database.

        @raise anydbm.error: If there's a problem opening the database.
        @raise ValueError: If the database is not of the right type.
        """
        if not self.filename:
            raise ValueError("Can only open on-disk databases")
        self.db = anydbm.open(self.filename, "w") #raises anydbm.error
        try:
            if self.db["--Reserved--type"] != self.type:
                raise ValueError("Not a %s database" % self.type)
        except KeyError:
            raise ValueError("Not a recognized database")

    def __getitem__(self, username):
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            valueStr = self.db[username]
        finally:
            self.lock.release()

        return self._getItem(username, valueStr)

    def __setitem__(self, username, value):
        if self.db == None:
            raise AssertionError("DB not open")

        valueStr = self._setItem(username, value)

        self.lock.acquire()
        try:
            self.db[username] = valueStr
            if self.filename:
                self.db.sync()
        finally:
            self.lock.release()

    def __delitem__(self, username):
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            del(self.db[username])
            if self.filename:
                self.db.sync()
        finally:
            self.lock.release()

    def __contains__(self, username):
        """Check if the database contains the specified username.

        @type username: str
        @param username: The username to check for.

        @rtype: bool
        @return: True if the database contains the username, False
        otherwise.

        """
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            return self.db.has_key(username)
        finally:
            self.lock.release()

    def check(self, username, param):
        value = self.__getitem__(username)
        return self._checkItem(value, username, param)

    def keys(self):
        """Return a list of usernames in the database.

        @rtype: list
        @return: The usernames in the database.
        """
        if self.db == None:
            raise AssertionError("DB not open")

        self.lock.acquire()
        try:
            usernames = self.db.keys()
        finally:
            self.lock.release()
        usernames = [u for u in usernames if not u.startswith("--Reserved--")]
        return usernames