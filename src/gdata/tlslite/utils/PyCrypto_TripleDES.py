"""PyCrypto 3DES implementation."""

from cryptomath import *
from TripleDES import *

if pycryptoLoaded:
    import Crypto.Cipher.DES3

    def new(key, mode, IV):
        return PyCrypto_TripleDES(key, mode, IV)

    class PyCrypto_TripleDES(TripleDES):

        def __init__(self, key, mode, IV):
            TripleDES.__init__(self, key, mode, IV, "pycrypto")
            self.context = Crypto.Cipher.DES3.new(key, mode, IV)

        def encrypt(self, plaintext):
            return self.context.encrypt(plaintext)

        def decrypt(self, ciphertext):
            return self.context.decrypt(ciphertext)