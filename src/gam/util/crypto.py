"""GAM cryptography utilities."""

import base64
import warnings
import arrow

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend

from gamlib import msgs as Msg
from gam.var import Ent
from gam.util.display import printEntityMessage
from gam.util.output import writeStdout

def _generatePrivateKeyAndPublicCert(projectId, clientEmail, name, key_size, b64enc_pub=True, validityHours=0):
  if projectId:
    printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.GENERATING_NEW_PRIVATE_KEY)
  else:
    writeStdout(Msg.GENERATING_NEW_PRIVATE_KEY+'\n')
  private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size, backend=default_backend())
  private_pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                          format=serialization.PrivateFormat.PKCS8,
                                          encryption_algorithm=serialization.NoEncryption()).decode()

  if projectId:
    printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.EXTRACTING_PUBLIC_CERTIFICATE)
  else:
    writeStdout(Msg.EXTRACTING_PUBLIC_CERTIFICATE+'\n')
  public_key = private_key.public_key()
  builder = x509.CertificateBuilder()
  # suppress cryptography warnings on service account email length
  with warnings.catch_warnings():
    warnings.filterwarnings('ignore', message='.*Attribute\'s length.*')
    builder = builder.subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                                                 name,
                                                                 _validate=False)]))
    builder = builder.issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                                                name,
                                                                _validate=False)]))
  # Gooogle seems to enforce the not before date strictly. Set the not before
  # date to be UTC two minutes ago which should cover any clock skew.
  now = arrow.utcnow()
  builder = builder.not_valid_before(now.shift(minutes=-2).naive)
  # Google defaults to 12/31/9999 date for end time if there's no
  # policy to restrict key age
  if validityHours:
    expires = now.shift(hours=validityHours, minutes=-2).naive
    builder = builder.not_valid_after(expires)
  else:
    builder = builder.not_valid_after(arrow.Arrow(9999, 12, 31, 23, 59).naive)
  builder = builder.serial_number(x509.random_serial_number())
  builder = builder.public_key(public_key)
  builder = builder.add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
  builder = builder.add_extension(x509.KeyUsage(key_cert_sign=False,
                                                crl_sign=False, digital_signature=True, content_commitment=False,
                                                key_encipherment=False, data_encipherment=False, key_agreement=False,
                                                encipher_only=False, decipher_only=False), critical=True)
  builder = builder.add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=True)
  certificate = builder.sign(private_key=private_key, algorithm=hashes.SHA256(), backend=default_backend())
  public_cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
  if projectId:
    printEntityMessage([Ent.PROJECT, projectId, Ent.SVCACCT, clientEmail], Msg.DONE_GENERATING_PRIVATE_KEY_AND_PUBLIC_CERTIFICATE)
  else:
    writeStdout(Msg.DONE_GENERATING_PRIVATE_KEY_AND_PUBLIC_CERTIFICATE+'\n')
  if not b64enc_pub:
    return (private_pem, public_cert_pem)
  publicKeyData = base64.b64encode(public_cert_pem.encode())
  if isinstance(publicKeyData, bytes):
    publicKeyData = publicKeyData.decode()
  return (private_pem, publicKeyData)

