from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

setup(
  console = ['gam.py'],

  zipfile = None,
  options = {'py2exe': 
              {'optimize': 2,
               'bundle_files': 3,
               'includes': ['passlib.handlers.sha2_crypt'],
               'dist_dir' : 'gam'}
            }
  )
