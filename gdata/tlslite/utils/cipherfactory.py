"""Factory functions for symmetric cryptography."""

import os

import Python_AES
import Python_RC4

import cryptomath

tripleDESPresent = False

if cryptomath.m2cryptoLoaded:
    import OpenSSL_AES
    import OpenSSL_RC4
    import OpenSSL_TripleDES
    tripleDESPresent = True

if cryptomath.cryptlibpyLoaded:
    import Cryptlib_AES
    import Cryptlib_RC4
    import Cryptlib_TripleDES
    tripleDESPresent = True

if cryptomath.pycryptoLoaded:
    import PyCrypto_AES
    import PyCrypto_RC4
    import PyCrypto_TripleDES
    tripleDESPresent = True

# **************************************************************************
# Factory Functions for AES
# **************************************************************************

def createAES(key, IV, implList=None):
    """Create a new AES object.

    @type key: str
    @param key: A 16, 24, or 32 byte string.

    @type IV: str
    @param IV: A 16 byte string

    @rtype: L{tlslite.utils.AES}
    @return: An AES object.
    """
    if implList == None:
        implList = ["cryptlib", "openssl", "pycrypto", "python"]

    for impl in implList:
        if impl == "cryptlib" and cryptomath.cryptlibpyLoaded:
            return Cryptlib_AES.new(key, 2, IV)
        elif impl == "openssl" and cryptomath.m2cryptoLoaded:
            return OpenSSL_AES.new(key, 2, IV)
        elif impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return PyCrypto_AES.new(key, 2, IV)
        elif impl == "python":
            return Python_AES.new(key, 2, IV)
    raise NotImplementedError()

def createRC4(key, IV, implList=None):
    """Create a new RC4 object.

    @type key: str
    @param key: A 16 to 32 byte string.

    @type IV: object
    @param IV: Ignored, whatever it is.

    @rtype: L{tlslite.utils.RC4}
    @return: An RC4 object.
    """
    if implList == None:
        implList = ["cryptlib", "openssl", "pycrypto", "python"]

    if len(IV) != 0:
        raise AssertionError()
    for impl in implList:
        if impl == "cryptlib" and cryptomath.cryptlibpyLoaded:
            return Cryptlib_RC4.new(key)
        elif impl == "openssl" and cryptomath.m2cryptoLoaded:
            return OpenSSL_RC4.new(key)
        elif impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return PyCrypto_RC4.new(key)
        elif impl == "python":
            return Python_RC4.new(key)
    raise NotImplementedError()

#Create a new TripleDES instance
def createTripleDES(key, IV, implList=None):
    """Create a new 3DES object.

    @type key: str
    @param key: A 24 byte string.

    @type IV: str
    @param IV: An 8 byte string

    @rtype: L{tlslite.utils.TripleDES}
    @return: A 3DES object.
    """
    if implList == None:
        implList = ["cryptlib", "openssl", "pycrypto"]

    for impl in implList:
        if impl == "cryptlib" and cryptomath.cryptlibpyLoaded:
           return Cryptlib_TripleDES.new(key, 2, IV)
        elif impl == "openssl" and cryptomath.m2cryptoLoaded:
            return OpenSSL_TripleDES.new(key, 2, IV)
        elif impl == "pycrypto" and cryptomath.pycryptoLoaded:
            return PyCrypto_TripleDES.new(key, 2, IV)
    raise NotImplementedError()