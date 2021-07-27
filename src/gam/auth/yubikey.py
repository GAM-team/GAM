from base64 import b64encode
import datetime
from secrets import SystemRandom
import string
import sys
from threading import Timer

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from ykman.device import connect_to_device
from ykman.piv import generate_self_signed_certificate, \
                      generate_chuid
from yubikit.piv import DEFAULT_MANAGEMENT_KEY, \
                        InvalidPinError, \
                        KEY_TYPE, \
                        MANAGEMENT_KEY_TYPE, \
                        PIN_POLICY, \
                        PivSession, \
                        OBJECT_ID, \
                        SLOT, \
                        TOUCH_POLICY
from yubikit.core.smartcard import ApduError
from gam import controlflow

class YubiKey():

    def __init__(self, service_account_info=None):
        self.key_type = None
        self.slot = None
        self.serial_number = None
        self.pin = None
        self.key_id = None
        if service_account_info:
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

    def _connect(self):
        conn, _, _ = connect_to_device(self.serial_number)
        return conn

    def get_certificate(self):
        try:
            conn = self._connect()
            with conn:
                session = PivSession(conn)
                if self.pin:
                    try:
                        session.verify_pin(self.pin)
                    except InvalidPinError as err:
                        controlflow.system_error_exit(7, f'YubiKey - {err}')
                try:
                    cert = session.get_certificate(self.slot)
                except ApduError as err:
                    controlflow.system_error_exit(9, f'Yubikey = {err}')
            cert_pem = cert.public_bytes(
                serialization.Encoding.PEM).decode()
            publicKeyData = b64encode(cert_pem.encode())
            if isinstance(publicKeyData, bytes):
                publicKeyData = publicKeyData.decode()
            return publicKeyData
        except ValueError as err:
            controlflow.system_error_exit(9, f'YubiKey - {err}')


    def get_serial_number(self):
        try:
            _, _, info = connect_to_device(self.serial_number)
            return info.serial
        except ValueError as err:
            controlflow.system_error_exit(9, f'YubikKey = {err}')

    def reset_piv(self):
        '''Resets YubiKey PIV app and generates new key for GAM to use.'''
        reply = str(input('This will wipe all PIV keys and configuration from your YubiKey. Are you sure? (y/N) ').lower().strip())
        if reply != 'y':
            sys.exit(1)
        try:
            conn = self._connect()
            with conn:
                piv = PivSession(conn)
                piv.reset()
                rnd = SystemRandom()
                pin_puk_chars = string.ascii_letters + string.digits + string.punctuation
                new_puk = ''.join(rnd.choice(pin_puk_chars) for _ in range(8))
                new_pin = ''.join(rnd.choice(pin_puk_chars) for _ in range(8))
                piv.change_puk('12345678', new_puk)
                piv.change_pin('123456', new_pin)
                print(f'PIN set to:  {new_pin}')
                piv.authenticate(MANAGEMENT_KEY_TYPE.TDES,
                                 DEFAULT_MANAGEMENT_KEY)

                piv.verify_pin(new_pin)
                print('Yubikey is generating a non-exportable private key...')
                pubkey = piv.generate_key(SLOT.AUTHENTICATION,
                                          KEY_TYPE.RSA2048,
                                          PIN_POLICY.ALWAYS,
                                          TOUCH_POLICY.NEVER)
                now = datetime.datetime.utcnow()
                valid_to = now + datetime.timedelta(days=36500)
                subject = 'CN=GAM Created Key'
                piv.authenticate(MANAGEMENT_KEY_TYPE.TDES,
                                 DEFAULT_MANAGEMENT_KEY)
                piv.verify_pin(new_pin)
                cert = generate_self_signed_certificate(piv,
                                                        SLOT.AUTHENTICATION,
                                                        pubkey,
                                                        subject,
                                                        now,
                                                        valid_to)
                piv.put_certificate(SLOT.AUTHENTICATION,
                                    cert)
                piv.put_object(OBJECT_ID.CHUID,
                               generate_chuid())
        except ValueError as err:
            controlflow.system_error_exit(8, f'Yubikey - {err}')


    def sign(self, message):
        if 'mplock' in globals():
            mplock.acquire()
        try:
            conn = self._connect()
            with conn:
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
