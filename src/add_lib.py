import os
import sys

'''
for onedir, add_lib.py allows moving many
library files into a lib/ directory to make
onedir cleaner. Thanks to:
https://medium.com/@philipp.h/reduce-clutter-when-using-pyinstaller-in    -one-directory-mode-b631b9f7f89b
'''

sys.path.append(os.path.join(os.getcwd(), 'lib'))
sys._MEIPASS=os.path.join(sys._MEIPASS, 'lib')
