"""Cryptlib RC4 implementation."""

from cryptomath import *
from RC4 import RC4

if cryptlibpyLoaded:

    def new(key):
        return Cryptlib_RC4(key)

    class Cryptlib_RC4(RC4):

        def __init__(self, key):
            RC4.__init__(self, key, "cryptlib")
            self.context = cryptlib_py.cryptCreateContext(cryptlib_py.CRYPT_UNUSED, cryptlib_py.CRYPT_ALGO_RC4)
            cryptlib_py.cryptSetAttribute(self.context, cryptlib_py.CRYPT_CTXINFO_KEYSIZE, len(key))
            cryptlib_py.cryptSetAttributeString(self.context, cryptlib_py.CRYPT_CTXINFO_KEY, key)

        def __del__(self):
             cryptlib_py.cryptDestroyContext(self.context)

        def encrypt(self, plaintext):
            bytes = stringToBytes(plaintext)
            cryptlib_py.cryptEncrypt(self.context, bytes)
            return bytesToString(bytes)

        def decrypt(self, ciphertext):
            return self.encrypt(ciphertext)