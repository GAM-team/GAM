"""GAM YubiKey management commands."""

from gamlib import yubikey
from gam.var import Cmd
from gam.util.args import getArgument, getInteger
from gam.util.errors import unknownArgumentExit

def doResetYubiKeyPIV():
  new_data = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if myarg == 'yubikeyserialnumber':
      new_data['yubikey_serial_number'] =  getInteger()
    else:
      unknownArgumentExit()
  yk = yubikey.YubiKey(new_data)
  yk.serial_number = yk.get_serial_number()
  yk.reset_piv()




