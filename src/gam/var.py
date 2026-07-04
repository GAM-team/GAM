"""Shared singleton instances for Act, Cmd, Ent, Ind.

These classes are stateless wrappers — all mutable state lives in
GM.Globals. Any instance has the same behavior, so we create one
set here and import everywhere.

This module has no dependencies on gam/ or util/, only on gamlib/.
"""

from gamlib import glaction
from gamlib import glclargs
from gamlib import glentity
from gamlib import glindent

Act = glaction.GamAction()
Cmd = glclargs.GamCLArgs()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
