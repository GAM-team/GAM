"""PyCrypto RC4 implementation."""

from cryptomath import *
from RC4 import *

if pycryptoLoaded:
    import Crypto.Cipher.ARC4

    def new(key):
        return PyCrypto_RC4(key)

    class PyCrypto_RC4(RC4):

        def __init__(self, key):
            RC4.__init__(self, key, "pycrypto")
            self.context = Crypto.Cipher.ARC4.new(key)

        def encrypt(self, plaintext):
            return self.context.encrypt(plaintext)

        def decrypt(self, ciphertext):
            return self.context.decrypt(ciphertext)