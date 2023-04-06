#!/usr/bin/env python3
#
# GAM
#
# Copyright 2019, LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""GAM is a command line tool which allows Administrators to control their Google Workspace domain and accounts.

With GAM you can programmatically create users, turn on/off services for users like POP and Forwarding and much more.
For more information, see https://jaylee.us/gam
"""

import sys

# Note that this file (and only this file) should remain compatible
# with older Python versions so we can return a meaningful error
# instead of a syntax error.
def main():
    required_ver = (3, 8, 0)
    if sys.version_info[:3] < required_ver:
        err_result = ('ERROR: GAM requires Python %s.%s.%s or newer. You are '
                'running %s.%s.%s. Please upgrade your Python version '
                'or use one of the binary GAM downloads.\n' %
                (required_ver[0],
                 required_ver[1],
                 required_ver[2],
                 sys.version_info[0],
                 sys.version_info[1],
                 sys.version_info[2]))
        sys.stderr.write(err_result)
        sys.exit(5)
    from multiprocessing import freeze_support
    freeze_support()
    if sys.platform == 'darwin':
        # https://bugs.python.org/issue33725 in Python 3.8.0 seems
        # to break parallel operations with errors about extra -b
        # command line arguments
        from multiprocessing import set_start_method
        set_start_method('fork')
    import gam
    sys.exit(gam.ProcessGAMCommand(sys.argv))


# Run from command line
if __name__ == '__main__':
    main()
