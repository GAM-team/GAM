"""Cryptlib 3DES implementation."""

from cryptomath import *

from TripleDES import *

if cryptlibpyLoaded:

    def new(key, mode, IV):
        return Cryptlib_TripleDES(key, mode, IV)

    class Cryptlib_TripleDES(TripleDES):

        def __init__(self, key, mode, IV):
            TripleDES.__init__(self, key, mode, IV, "cryptlib")
            self.context = cryptlib_py.cryptCreateContext(cryptlib_py.CRYPT_UNUSED, cryptlib_py.CRYPT_ALGO_3DES)
            cryptlib_py.cryptSetAttribute(self.context, cryptlib_py.CRYPT_CTXINFO_MODE, cryptlib_py.CRYPT_MODE_CBC)
            cryptlib_py.cryptSetAttribute(self.context, cryptlib_py.CRYPT_CTXINFO_KEYSIZE, len(key))
            cryptlib_py.cryptSetAttributeString(self.context, cryptlib_py.CRYPT_CTXINFO_KEY, key)
            cryptlib_py.cryptSetAttributeString(self.context, cryptlib_py.CRYPT_CTXINFO_IV, IV)

        def __del__(self):
             cryptlib_py.cryptDestroyContext(self.context)

        def encrypt(self, plaintext):
            TripleDES.encrypt(self, plaintext)
            bytes = stringToBytes(plaintext)
            cryptlib_py.cryptEncrypt(self.context, bytes)
            return bytesToString(bytes)

        def decrypt(self, ciphertext):
            TripleDES.decrypt(self, ciphertext)
            bytes = stringToBytes(ciphertext)
            cryptlib_py.cryptDecrypt(self.context, bytes)
            return bytesToString(bytes)