#!/usr/bin/python

"""
requires tlslite - http://trevp.net/tlslite/

"""

import binascii

from gdata.tlslite.utils import keyfactory
from gdata.tlslite.utils import cryptomath

# XXX andy: ugly local import due to module name, oauth.oauth
import gdata.oauth as oauth

class OAuthSignatureMethod_RSA_SHA1(oauth.OAuthSignatureMethod):
  def get_name(self):
    return "RSA-SHA1"

  def _fetch_public_cert(self, oauth_request):
    # not implemented yet, ideas are:
    # (1) do a lookup in a table of trusted certs keyed off of consumer
    # (2) fetch via http using a url provided by the requester
    # (3) some sort of specific discovery code based on request
    #
    # either way should return a string representation of the certificate
    raise NotImplementedError

  def _fetch_private_cert(self, oauth_request):
    # not implemented yet, ideas are:
    # (1) do a lookup in a table of trusted certs keyed off of consumer
    #
    # either way should return a string representation of the certificate
    raise NotImplementedError

  def build_signature_base_string(self, oauth_request, consumer, token):
      sig = (
          oauth.escape(oauth_request.get_normalized_http_method()),
          oauth.escape(oauth_request.get_normalized_http_url()),
          oauth.escape(oauth_request.get_normalized_parameters()),
      )
      key = ''
      raw = '&'.join(sig)
      return key, raw

  def build_signature(self, oauth_request, consumer, token):
    key, base_string = self.build_signature_base_string(oauth_request,
                                                        consumer,
                                                        token)

    # Fetch the private key cert based on the request
    cert = self._fetch_private_cert(oauth_request)

    # Pull the private key from the certificate
    privatekey = keyfactory.parsePrivateKey(cert)
    
    # Convert base_string to bytes
    #base_string_bytes = cryptomath.createByteArraySequence(base_string)
    
    # Sign using the key
    signed = privatekey.hashAndSign(base_string)
  
    return binascii.b2a_base64(signed)[:-1]
  
  def check_signature(self, oauth_request, consumer, token, signature):
    decoded_sig = base64.b64decode(signature);

    key, base_string = self.build_signature_base_string(oauth_request,
                                                        consumer,
                                                        token)

    # Fetch the public key cert based on the request
    cert = self._fetch_public_cert(oauth_request)

    # Pull the public key from the certificate
    publickey = keyfactory.parsePEMKey(cert, public=True)

    # Check the signature
    ok = publickey.hashAndVerify(decoded_sig, base_string)

    return ok


class TestOAuthSignatureMethod_RSA_SHA1(OAuthSignatureMethod_RSA_SHA1):
  def _fetch_public_cert(self, oauth_request):
    cert = """
-----BEGIN CERTIFICATE-----
MIIBpjCCAQ+gAwIBAgIBATANBgkqhkiG9w0BAQUFADAZMRcwFQYDVQQDDA5UZXN0
IFByaW5jaXBhbDAeFw03MDAxMDEwODAwMDBaFw0zODEyMzEwODAwMDBaMBkxFzAV
BgNVBAMMDlRlc3QgUHJpbmNpcGFsMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKB
gQC0YjCwIfYoprq/FQO6lb3asXrxLlJFuCvtinTF5p0GxvQGu5O3gYytUvtC2JlY
zypSRjVxwxrsuRcP3e641SdASwfrmzyvIgP08N4S0IFzEURkV1wp/IpH7kH41Etb
mUmrXSwfNZsnQRE5SYSOhh+LcK2wyQkdgcMv11l4KoBkcwIDAQABMA0GCSqGSIb3
DQEBBQUAA4GBAGZLPEuJ5SiJ2ryq+CmEGOXfvlTtEL2nuGtr9PewxkgnOjZpUy+d
4TvuXJbNQc8f4AMWL/tO9w0Fk80rWKp9ea8/df4qMq5qlFWlx6yOLQxumNOmECKb
WpkUQDIDJEoFUzKMVuJf4KO/FJ345+BNLGgbJ6WujreoM1X/gYfdnJ/J
-----END CERTIFICATE-----
"""
    return cert

  def _fetch_private_cert(self, oauth_request):
    cert = """
-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBALRiMLAh9iimur8V
A7qVvdqxevEuUkW4K+2KdMXmnQbG9Aa7k7eBjK1S+0LYmVjPKlJGNXHDGuy5Fw/d
7rjVJ0BLB+ubPK8iA/Tw3hLQgXMRRGRXXCn8ikfuQfjUS1uZSatdLB81mydBETlJ
hI6GH4twrbDJCR2Bwy/XWXgqgGRzAgMBAAECgYBYWVtleUzavkbrPjy0T5FMou8H
X9u2AC2ry8vD/l7cqedtwMPp9k7TubgNFo+NGvKsl2ynyprOZR1xjQ7WgrgVB+mm
uScOM/5HVceFuGRDhYTCObE+y1kxRloNYXnx3ei1zbeYLPCHdhxRYW7T0qcynNmw
rn05/KO2RLjgQNalsQJBANeA3Q4Nugqy4QBUCEC09SqylT2K9FrrItqL2QKc9v0Z
zO2uwllCbg0dwpVuYPYXYvikNHHg+aCWF+VXsb9rpPsCQQDWR9TT4ORdzoj+Nccn
qkMsDmzt0EfNaAOwHOmVJ2RVBspPcxt5iN4HI7HNeG6U5YsFBb+/GZbgfBT3kpNG
WPTpAkBI+gFhjfJvRw38n3g/+UeAkwMI2TJQS4n8+hid0uus3/zOjDySH3XHCUno
cn1xOJAyZODBo47E+67R4jV1/gzbAkEAklJaspRPXP877NssM5nAZMU0/O/NGCZ+
3jPgDUno6WbJn5cqm8MqWhW1xGkImgRk+fkDBquiq4gPiT898jusgQJAd5Zrr6Q8
AO/0isr/3aa6O6NLQxISLKcPDk2NOccAfS/xOtfOz4sJYM3+Bs4Io9+dZGSDCA54
Lw03eHTNQghS0A==
-----END PRIVATE KEY-----
"""
    return cert
