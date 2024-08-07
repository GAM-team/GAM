# -*- coding: utf-8 -*-

# Copyright (C) 2023 Ross Scroggs All Rights Reserved.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""YubiKey"""

import base64
import datetime
from secrets import SystemRandom
import string
import sys

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from smartcard.Exceptions import CardConnectionException
from ykman.device import list_all_devices
from ykman.piv import generate_self_signed_certificate, generate_chuid
from yubikit.piv import DEFAULT_MANAGEMENT_KEY, \
                        InvalidPinError, \
                        KEY_TYPE, \
                        MANAGEMENT_KEY_TYPE, \
                        PIN_POLICY, \
                        PivSession, \
                        OBJECT_ID, \
                        SLOT, \
                        TOUCH_POLICY
from yubikit.core.smartcard import ApduError, SmartCardConnection

YUBIKEY_CONNECTION_ERROR_RC = 80
YUBIKEY_INVALID_KEY_TYPE_RC = 81
YUBIKEY_INVALID_SLOT_RC = 82
YUBIKEY_INVALID_PIN_RC = 83
YUBIKEY_APDU_ERROR_RC = 84
YUBIKEY_VALUE_ERROR_RC = 85
YUBIKEY_MULTIPLE_CONNECTED_RC = 86
YUBIKEY_NOT_FOUND_RC = 87

from gam import mplock

from gam import systemErrorExit
from gam import readStdin
from gam import writeStdout

from gam.gamlib import glmsgs as Msg

PIN_PUK_CHARS = string.ascii_letters+string.digits+string.punctuation

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
        systemErrorExit(YUBIKEY_INVALID_KEY_TYPE_RC, f'{key_type} is not a valid value for yubikey_key_type')
      slot = service_account_info.get('yubikey_slot', 'AUTHENTICATION')
      try:
        self.slot = getattr(SLOT, slot.upper())
      except AttributeError:
        systemErrorExit(YUBIKEY_INVALID_SLOT_RC, f'{slot} is not a valid value for yubikey_slot')
      self.serial_number = service_account_info.get('yubikey_serial_number')
      self.pin = service_account_info.get('yubikey_pin')
      self.key_id = service_account_info.get('private_key_id')

  def _connect(self):
    try:
      devices = list_all_devices()
      for (device, info) in devices:
        if info.serial == self.serial_number:
          return device.open_connection(SmartCardConnection)
    except CardConnectionException as err:
      systemErrorExit(YUBIKEY_CONNECTION_ERROR_RC, f'YubiKey - {err}')

  def get_certificate(self):
    try:
      conn = self._connect()
      with conn:
        session = PivSession(conn)
        if self.pin:
          try:
            session.verify_pin(self.pin)
          except InvalidPinError as err:
            systemErrorExit(YUBIKEY_INVALID_PIN_RC, f'YubiKey - {err}')
        try:
          cert = session.get_certificate(self.slot)
        except ApduError as err:
          systemErrorExit(YUBIKEY_APDU_ERROR_RC, f'YubiKey - {err}')
      cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
      publicKeyData = base64.b64encode(cert_pem.encode())
      if isinstance(publicKeyData, bytes):
        publicKeyData = publicKeyData.decode()
      return publicKeyData
    except ValueError as err:
      systemErrorExit(YUBIKEY_VALUE_ERROR_RC, f'YubiKey - {err}')
    except TypeError as err:
      systemErrorExit(YUBIKEY_NOT_FOUND_RC, f'YubiKey - {err} - {Msg.IS_YUBIKEY_INSERTED}')

  def get_serial_number(self):
    try:
      devices = list_all_devices()
      if not devices:
        systemErrorExit(YUBIKEY_NOT_FOUND_RC, Msg.COULD_NOT_FIND_ANY_YUBIKEY)
      if self.serial_number:
        for (_, info) in devices:
          if info.serial == self.serial_number:
            return info.serial
        systemErrorExit(YUBIKEY_NOT_FOUND_RC, Msg.COULD_NOT_FIND_YUBIKEY_WITH_SERIAL.format(self.serial_number))
      if len(devices) > 1:
        serials = ', '.join([str(info.serial) for (_, info) in devices])
        systemErrorExit(YUBIKEY_MULTIPLE_CONNECTED_RC, Msg.MULTIPLE_YUBIKEYS_CONNECTED.format(serials))
      return devices[0][1].serial
    except ValueError as err:
      systemErrorExit(YUBIKEY_VALUE_ERROR_RC, f'YubiKey - {err}')

  def reset_piv(self):
    '''Resets YubiKey PIV app and generates new key for GAM to use.'''
    reply = str(readStdin(Msg.CONFIRM_WIPE_YUBIKEY_PIV).lower().strip())
    if reply != 'y':
      sys.exit(1)
    try:
      conn = self._connect()
      with conn:
        piv = PivSession(conn)
        piv.reset()
        rnd = SystemRandom()
        new_puk = ''.join(rnd.choice(PIN_PUK_CHARS) for _ in range(8))
        new_pin = ''.join(rnd.choice(PIN_PUK_CHARS) for _ in range(8))
        piv.change_puk('12345678', new_puk)
        piv.change_pin('123456', new_pin)
        writeStdout(Msg.YUBIKEY_PIN_SET_TO.format(new_pin))
        piv.authenticate(MANAGEMENT_KEY_TYPE.TDES, DEFAULT_MANAGEMENT_KEY)
        piv.verify_pin(new_pin)
        writeStdout(Msg.YUBIKEY_GENERATING_NONEXPORTABLE_PRIVATE_KEY)
        pubkey = piv.generate_key(SLOT.AUTHENTICATION,
                                  KEY_TYPE.RSA2048,
                                  PIN_POLICY.ALWAYS,
                                  TOUCH_POLICY.NEVER)
        now = datetime.datetime.utcnow()
        valid_to = now + datetime.timedelta(days=36500)
        subject = 'CN=GAM Created Key'
        piv.authenticate(MANAGEMENT_KEY_TYPE.TDES, DEFAULT_MANAGEMENT_KEY)
        piv.verify_pin(new_pin)
        cert = generate_self_signed_certificate(piv,
                                                SLOT.AUTHENTICATION,
                                                pubkey,
                                                subject,
                                                now,
                                                valid_to)
        piv.put_certificate(SLOT.AUTHENTICATION, cert)
        piv.put_object(OBJECT_ID.CHUID, generate_chuid())
    except ValueError as err:
      systemErrorExit(YUBIKEY_VALUE_ERROR_RC, f'YubiKey - {err}')
    except TypeError as err:
      systemErrorExit(YUBIKEY_NOT_FOUND_RC, f'YubiKey - {err} - {Msg.IS_YUBIKEY_INSERTED}')

  def sign(self, message):
    if mplock is not None:
      mplock.acquire()
    try:
      conn = self._connect()
      with conn:
        session = PivSession(conn)
        if self.pin:
          try:
            session.verify_pin(self.pin)
          except InvalidPinError as err:
            systemErrorExit(YUBIKEY_INVALID_PIN_RC, f'YubiKey - {err}')
        try:
          signed = session.sign(slot=self.slot,
                                key_type=self.key_type,
                                message=message,
                                hash_algorithm=hashes.SHA256(),
                                padding=padding.PKCS1v15())
        except ApduError as err:
          systemErrorExit(YUBIKEY_APDU_ERROR_RC, f'YubiKey - {err}')
    except ValueError as err:
      systemErrorExit(YUBIKEY_VALUE_ERROR_RC, f'YubiKey - {err}')
    except TypeError as err:
      systemErrorExit(YUBIKEY_NOT_FOUND_RC, f'YubiKey - {err} - {Msg.IS_YUBIKEY_INSERTED}')
    if mplock is not None:
      mplock.release()
    return signed
