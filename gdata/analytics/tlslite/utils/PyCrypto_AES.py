"""PyCrypto AES implementation."""

from cryptomath import *
from AES import *

if pycryptoLoaded:
    import Crypto.Cipher.AES

    def new(key, mode, IV):
        return PyCrypto_AES(key, mode, IV)

    class PyCrypto_AES(AES):

        def __init__(self, key, mode, IV):
            AES.__init__(self, key, mode, IV, "pycrypto")
            self.context = Crypto.Cipher.AES.new(key, mode, IV)

        def encrypt(self, plaintext):
            return self.context.encrypt(plaintext)

        def decrypt(self, ciphertext):
            return self.context.decrypt(ciphertext)