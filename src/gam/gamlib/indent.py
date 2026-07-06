
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

"""GAM indent processing

"""

class GamIndent:

  INDENT_SPACES_PER_LEVEL = '  '

  # Shared state across all instances (class-level)
  _indent = 0

  @property
  def indent(self):
    return GamIndent._indent
  @indent.setter
  def indent(self, value):
    GamIndent._indent = value

  def __init__(self):
    pass  # state is shared at class level

  def Reset(self):
    GamIndent._indent = 0

  def Increment(self):
    GamIndent._indent += 1

  def Decrement(self):
    GamIndent._indent -= 1

  def Spaces(self):
    return self.INDENT_SPACES_PER_LEVEL*GamIndent._indent

  def SpacesSub1(self):
    return self.INDENT_SPACES_PER_LEVEL*(GamIndent._indent-1)

  def MultiLineText(self, message, n=0):
    return message.replace('\n', f'\n{self.INDENT_SPACES_PER_LEVEL*(GamIndent._indent+n)}').rstrip()
