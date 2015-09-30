"""OpenSSL/M2Crypto AES implementation."""

from cryptomath import *
from AES import *

if m2cryptoLoaded:

    def new(key, mode, IV):
        return OpenSSL_AES(key, mode, IV)

    class OpenSSL_AES(AES):

        def __init__(self, key, mode, IV):
            AES.__init__(self, key, mode, IV, "openssl")
            self.key = key
            self.IV = IV

        def _createContext(self, encrypt):
            context = m2.cipher_ctx_new()
            if len(self.key)==16:
                cipherType = m2.aes_128_cbc()
            if len(self.key)==24:
                cipherType = m2.aes_192_cbc()
            if len(self.key)==32:
                cipherType = m2.aes_256_cbc()
            m2.cipher_init(context, cipherType, self.key, self.IV, encrypt)
            return context

        def encrypt(self, plaintext):
            AES.encrypt(self, plaintext)
            context = self._createContext(1)
            ciphertext = m2.cipher_update(context, plaintext)
            m2.cipher_ctx_free(context)
            self.IV = ciphertext[-self.block_size:]
            return ciphertext

        def decrypt(self, ciphertext):
            AES.decrypt(self, ciphertext)
            context = self._createContext(0)
            #I think M2Crypto has a bug - it fails to decrypt and return the last block passed in.
            #To work around this, we append sixteen zeros to the string, below:
            plaintext = m2.cipher_update(context, ciphertext+('\0'*16))

            #If this bug is ever fixed, then plaintext will end up having a garbage
            #plaintext block on the end.  That's okay - the below code will discard it.
            plaintext = plaintext[:len(ciphertext)]
            m2.cipher_ctx_free(context)
            self.IV = ciphertext[-self.block_size:]
            return plaintext
