"""Abstract class for RC4."""

from compat import * #For False

class RC4:
    def __init__(self, keyBytes, implementation):
        if len(keyBytes) < 16 or len(keyBytes) > 256:
            raise ValueError()
        self.isBlockCipher = False
        self.name = "rc4"
        self.implementation = implementation

    def encrypt(self, plaintext):
        raise NotImplementedError()

    def decrypt(self, ciphertext):
        raise NotImplementedError()