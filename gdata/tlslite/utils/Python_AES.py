"""Pure-Python AES implementation."""

from cryptomath import *

from AES import *
from rijndael import rijndael

def new(key, mode, IV):
    return Python_AES(key, mode, IV)

class Python_AES(AES):
    def __init__(self, key, mode, IV):
        AES.__init__(self, key, mode, IV, "python")
        self.rijndael = rijndael(key, 16)
        self.IV = IV

    def encrypt(self, plaintext):
        AES.encrypt(self, plaintext)

        plaintextBytes = stringToBytes(plaintext)
        chainBytes = stringToBytes(self.IV)

        #CBC Mode: For each block...
        for x in range(len(plaintextBytes)/16):

            #XOR with the chaining block
            blockBytes = plaintextBytes[x*16 : (x*16)+16]
            for y in range(16):
                blockBytes[y] ^= chainBytes[y]
            blockString = bytesToString(blockBytes)

            #Encrypt it
            encryptedBytes = stringToBytes(self.rijndael.encrypt(blockString))

            #Overwrite the input with the output
            for y in range(16):
                plaintextBytes[(x*16)+y] = encryptedBytes[y]

            #Set the next chaining block
            chainBytes = encryptedBytes

        self.IV = bytesToString(chainBytes)
        return bytesToString(plaintextBytes)

    def decrypt(self, ciphertext):
        AES.decrypt(self, ciphertext)

        ciphertextBytes = stringToBytes(ciphertext)
        chainBytes = stringToBytes(self.IV)

        #CBC Mode: For each block...
        for x in range(len(ciphertextBytes)/16):

            #Decrypt it
            blockBytes = ciphertextBytes[x*16 : (x*16)+16]
            blockString = bytesToString(blockBytes)
            decryptedBytes = stringToBytes(self.rijndael.decrypt(blockString))

            #XOR with the chaining block and overwrite the input with output
            for y in range(16):
                decryptedBytes[y] ^= chainBytes[y]
                ciphertextBytes[(x*16)+y] = decryptedBytes[y]

            #Set the next chaining block
            chainBytes = blockBytes

        self.IV = bytesToString(chainBytes)
        return bytesToString(ciphertextBytes)
