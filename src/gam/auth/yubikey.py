from base64 import b64encode
import sys
from threading import Timer

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from ykman.device import connect_to_device
from yubikit.piv import KEY_TYPE, SLOT, InvalidPinError, PivSession
from yubikit.core.smartcard import ApduError
from gam import controlflow

class YubiKey():

    def __init__(self, service_account_info):
        key_type = service_account_info.get('yubikey_key_type', 'RSA2048')
        try:
            self.key_type = getattr(KEY_TYPE, key_type.upper())
        except AttributeError:
            controlflow.system_error_exit(6, f'{key_type} is not a valid value for yubikey_key_type')
        slot = service_account_info.get('yubikey_slot', 'AUTHENTICATION')
        try:
            self.slot = getattr(SLOT, slot.upper())
        except AttributeError:
            controlflow.system_error_exit(6, f'{slot} is not a valid value for yubikey_slot')
        self.serial_number = service_account_info.get('yubikey_serial_number')
        self.pin = service_account_info.get('yubikey_pin')
        self.key_id = service_account_info.get('private_key_id')

    def get_certificate(self):
        try:
            conn, _, _ = connect_to_device(self.serial_number)
            session = PivSession(conn)
            if self.pin:
                try:
                    session.verify_pin(self.pin)
                except InvalidPinError as err:
                    controlflow.system_error_exit(7, f'YubiKey - {err}')
            try:
                cert = session.get_certificate(self.slot)
                cert_pem = cert.public_bytes(
                     serialization.Encoding.PEM).decode()
                publicKeyData = b64encode(cert_pem.encode())
                if isinstance(publicKeyData, bytes):
                    publicKeyData = publicKeyData.decode()
                return publicKeyData
            except ApduError as err:
                controlflow.system_error_exit(8, f'YubiKey - {err}')
        except ValueError as err:
            controlflow.system_error_exit(9, f'YubiKey - {err}')

    def sign(self, message):
        if 'mplock' in globals():
            mplock.acquire()
        try:
            conn, _, _ = connect_to_device(self.serial_number)
            session = PivSession(conn)
            if self.pin:
                try:
                    session.verify_pin(self.pin)
                except InvalidPinError as err:
                    controlflow.system_error_exit(7, f'YubiKey - {err}')
            try:
                signed = session.sign(slot=self.slot,
                                      key_type=self.key_type,
                                      message=message,
                                      hash_algorithm=hashes.SHA256(),
                                      padding=padding.PKCS1v15())
            except ApduError as err:
                controlflow.system_error_exit(8, f'YubiKey = {err}')
        except ValueError as err:
            controlflow.system_error_exit(9, f'YubiKey - {err}')
        if 'mplock' in globals():
            mplock.release()
        return signed
