import sys
import json
import os

cfg = json.load(sys.stdin)
cfg['client_secret'] = os.getenv('client_secret')
jid = os.getenv('jid')
cfg['refresh_token'] = os.getenv('refresh_%s' % jid)
name = os.getenv('TRAVIS_JOB_NAME')
if name.endswith('Testing'):
    out_file = 'oauth2.txt'
else:
    out_file = 'gam/oauth2.txt'
with open(out_file, 'w') as f:
  json.dump(cfg, f)
