"""Shared singleton instances for Act, Cmd, Ent, Ind.

These classes are stateless wrappers — all mutable state lives in
GM.Globals. Any instance has the same behavior, so we create one
set here and import everywhere.

This module has no dependencies on gam/ or util/, only on gamlib/.
"""

from gamlib import action
from gamlib import clargs
from gamlib import entity
from gamlib import indent

Act = action.GamAction()
Cmd = clargs.GamCLArgs()
Ent = entity.GamEntity()
Ind = indent.GamIndent()
