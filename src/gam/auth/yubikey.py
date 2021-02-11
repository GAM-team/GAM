import sys
from threading import Timer

# hack to avoid ImportError on unneccessary libraries
class fake_open():
    open_devices = None
sys.modules['ykman.driver_otp'] = fake_open

import ykman.descriptor

# hack to avoid deprecation notice from cryptography
# remove after this lands:
# https://github.com/Yubico/yubikey-manager/pull/385
sys.modules['ykman.utils.int_from_bytes'] = int.from_bytes

from ykman.piv import SLOT, ALGO, PivController, DEFAULT_MANAGEMENT_KEY
from ykman.util import TRANSPORT

from gam import controlflow

class YubiKey():

    def __init__(self, service_account_info):
        algo = service_account_info.get('yubikey_algo', 'RSA2048')
        try:
            self.algo = getattr(ALGO, algo.upper())
        except AttributeError:
            controlflow.system_error_exit(6, f'{algo} is not a valid value for yubikey_algo')
        slot = service_account_info.get('yubikey_slot', 'AUTHENTICATION')
        try:
            self.slot = getattr(SLOT, slot.upper())
        except AttributeError:
            controlflow.system_error_exit(6, f'{slot} is not a valid value for yubikey_slot')
        self.pin = service_account_info.get('yubikey_pin')
        self.key_id = service_account_info.get('private_key_id')

    def touch_callback(self):
        sys.stderr.write('\nTouch your YubiKey...\n')

    def sign(self, message):
        timer = Timer(0.5, self.touch_callback)
        if 'mplock' in globals():
            mplock.acquire()
        try:
            with ykman.descriptor.open_device(transports=TRANSPORT.CCID) as yk:
                controller = PivController(yk.driver)
                if self.pin:
                    controller.verify(self.pin)
                timer.start() # if sign() takes more than .5 sec we need touch
                try:
                    signed = controller.sign(self.slot, self.algo, message)
                except ykman.driver_ccid.APDUError: # We need PIN
                    timer.cancel() # reset timer while user enters PIN
                    sys.stderr.write('\nEnter your YubiKey PIN:\n')
                    self.pin = input()
                    timer = Timer(0.5, self.touch_callback)
                    controller.verify(self.pin)
                    timer.start()
                    signed = controller.sign(self.slot, self.algo, message)
                timer.cancel()
        except ykman.descriptor.FailedOpeningDeviceException:
            controlflow.system_error_exit(5, 'No YubiKey found. Is it plugged in?')
        except ykman.piv.WrongPin:
            controlflow.system_error_exit(7, 'Wrong PIN for YubiKey.')
        except ykman.piv.AuthenticationBlocked:
            controlflow.system_error_exit(8, 'YubiKey PIN is blocked.')
        if 'mplock' in globals():
            mplock.release()
        return signed
