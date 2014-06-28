"""Public-key encryption and signature algorithms.

Public-key encryption uses two different keys, one for encryption and
one for decryption.  The encryption key can be made public, and the
decryption key is kept private.  Many public-key algorithms can also
be used to sign messages, and some can *only* be used for signatures.

Crypto.PublicKey.DSA      Digital Signature Algorithm. (Signature only)
Crypto.PublicKey.ElGamal  (Signing and encryption)
Crypto.PublicKey.RSA      (Signing, encryption, and blinding)
Crypto.PublicKey.qNEW     (Signature only)

"""

__all__ = ['RSA', 'DSA', 'ElGamal', 'qNEW']
__revision__ = "$Id: __init__.py,v 1.4 2003/04/03 20:27:13 akuchling Exp $"

