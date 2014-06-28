"""Secret-key encryption algorithms.

Secret-key encryption algorithms transform plaintext in some way that
is dependent on a key, producing ciphertext. This transformation can
easily be reversed, if (and, hopefully, only if) one knows the key.

The encryption modules here all support the interface described in PEP
272, "API for Block Encryption Algorithms".

If you don't know which algorithm to choose, use AES because it's
standard and has undergone a fair bit of examination.

Crypto.Cipher.AES         Advanced Encryption Standard
Crypto.Cipher.ARC2        Alleged RC2
Crypto.Cipher.ARC4        Alleged RC4
Crypto.Cipher.Blowfish
Crypto.Cipher.CAST
Crypto.Cipher.DES         The Data Encryption Standard.  Very commonly used
                          in the past, but today its 56-bit keys are too small.
Crypto.Cipher.DES3        Triple DES.
Crypto.Cipher.IDEA
Crypto.Cipher.RC5
Crypto.Cipher.XOR         The simple XOR cipher.
"""

__all__ = ['AES', 'ARC2', 'ARC4',
           'Blowfish', 'CAST', 'DES', 'DES3', 'IDEA', 'RC5',
           'XOR'
           ]

__revision__ = "$Id: __init__.py,v 1.7 2003/02/28 15:28:35 akuchling Exp $"


