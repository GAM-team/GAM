"""Unit tests for password hashing — verify GAM always produces SHA-512 crypt hashes.

Tests GAM's actual hashPassword() function from cmd/users/manage.py,
not passlib directly.
"""

import pytest


class TestPasswordHashing:
    """Ensure GAM's hashPassword() always generates SHA-512 crypt format hashes.

    GAM sends hashed passwords to Google's Directory API with
    hashFunction='crypt'. The hash MUST be SHA-512 ($6$ prefix),
    never legacy formats like DES, MD5 ($1$), or SHA-256 ($5$).
    """

    def test_hash_is_sha512_format(self):
        """Generated hash must start with $6$ (SHA-512 crypt identifier)."""
        from gam.cmd.users.manage import hashPassword
        hashed, func = hashPassword('test-password')
        assert hashed.startswith('$6$'), (
            f'Expected SHA-512 hash ($6$...) but got: {hashed[:10]}...'
        )

    def test_hash_function_is_crypt(self):
        """hashFunction returned must be 'crypt' for Google's API."""
        from gam.cmd.users.manage import hashPassword
        _, func = hashPassword('test-password')
        assert func == 'crypt'

    def test_hash_contains_rounds(self):
        """Generated hash must include the rounds parameter."""
        from gam.cmd.users.manage import hashPassword
        hashed, _ = hashPassword('test-password')
        assert '$rounds=10000$' in hashed, (
            f'Expected rounds=10000 in hash but got: {hashed[:30]}...'
        )

    def test_hash_verifies(self):
        """A generated hash must verify against its source password."""
        from gam.cmd.users.manage import hashPassword
        from passlib.hash import sha512_crypt
        password = 'correct-horse-battery-staple'
        hashed, _ = hashPassword(password)
        assert sha512_crypt.verify(password, hashed)

    def test_hash_rejects_wrong_password(self):
        """A generated hash must NOT verify against a different password."""
        from gam.cmd.users.manage import hashPassword
        from passlib.hash import sha512_crypt
        hashed, _ = hashPassword('right-password')
        assert not sha512_crypt.verify('wrong-password', hashed)

    def test_different_passwords_produce_different_hashes(self):
        """Two different passwords must not produce the same hash."""
        from gam.cmd.users.manage import hashPassword
        h1, _ = hashPassword('password-one')
        h2, _ = hashPassword('password-two')
        assert h1 != h2
