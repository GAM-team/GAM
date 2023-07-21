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

"""GAM indent processing

"""

class GamIndent():

  INDENT_SPACES_PER_LEVEL = '  '

  def __init__(self):
    self.indent = 0

  def Reset(self):
    self.indent = 0

  def Increment(self):
    self.indent += 1

  def Decrement(self):
    self.indent -= 1

  def Spaces(self):
    return self.INDENT_SPACES_PER_LEVEL*self.indent

  def SpacesSub1(self):
    return self.INDENT_SPACES_PER_LEVEL*(self.indent-1)

  def MultiLineText(self, message, n=0):
    return message.replace('\n', f'\n{self.INDENT_SPACES_PER_LEVEL*(self.indent+n)}').rstrip()
