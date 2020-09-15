import sys
import json
import os

cfg = json.load(sys.stdin)
cfg['client_secret'] = os.getenv('client_secret')
jid = os.getenv('jid')
cfg['refresh_token'] = os.getenv('refresh_%s' % jid)
gampath = os.getenv('gampath')
out_file = os.path.join(gampath, 'oauth2.txt')
with open(out_file, 'w') as f:
    json.dump(cfg, f)
print(f'Wrote {out_file} with {len(cfg["client_secret"]} char client secret and {len(cfg["refresh_token"])} char refresh token.')
