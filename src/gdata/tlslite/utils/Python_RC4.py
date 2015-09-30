"""Pure-Python RC4 implementation."""

from RC4 import RC4
from cryptomath import *

def new(key):
    return Python_RC4(key)

class Python_RC4(RC4):
    def __init__(self, key):
        RC4.__init__(self, key, "python")
        keyBytes = stringToBytes(key)
        S = [i for i in range(256)]
        j = 0
        for i in range(256):
            j = (j + S[i] + keyBytes[i % len(keyBytes)]) % 256
            S[i], S[j] = S[j], S[i]

        self.S = S
        self.i = 0
        self.j = 0

    def encrypt(self, plaintext):
        plaintextBytes = stringToBytes(plaintext)
        S = self.S
        i = self.i
        j = self.j
        for x in range(len(plaintextBytes)):
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            t = (S[i] + S[j]) % 256
            plaintextBytes[x] ^= S[t]
        self.i = i
        self.j = j
        return bytesToString(plaintextBytes)

    def decrypt(self, ciphertext):
        return self.encrypt(ciphertext)
