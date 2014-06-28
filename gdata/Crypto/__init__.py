
"""Python Cryptography Toolkit

A collection of cryptographic modules implementing various algorithms
and protocols.

Subpackages:
Crypto.Cipher             Secret-key encryption algorithms (AES, DES, ARC4)
Crypto.Hash               Hashing algorithms (MD5, SHA, HMAC)
Crypto.Protocol           Cryptographic protocols (Chaffing, all-or-nothing
                          transform).   This package does not contain any
                          network protocols.
Crypto.PublicKey          Public-key encryption and signature algorithms
                          (RSA, DSA)
Crypto.Util               Various useful modules and functions (long-to-string
                          conversion, random number generation, number
                          theoretic functions)
"""

__all__ = ['Cipher', 'Hash', 'Protocol', 'PublicKey', 'Util']

__version__ = '2.0.1'
__revision__ = "$Id: __init__.py,v 1.12 2005/06/14 01:20:22 akuchling Exp $"


