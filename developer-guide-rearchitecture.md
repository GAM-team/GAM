# GAM Codebase Rearchitecture — Developer Guide

## 1. Goals, Benefits & What Changes for Users

### What Changed for Users

**Nothing.** GAM behaves identically. Every command, flag, and output format is unchanged. Performance is the same or slightly better. This was a purely internal restructuring.

### Why We Did This

`gam/__init__.py` was a **72,735-line monolith** — a single file containing virtually all of GAM's logic. Every Google Workspace API surface (Drive, Gmail, Calendar, Classroom, Groups, Vault, Chat, ChromeOS, etc.) lived in one file. This created real problems:

- **Navigating the codebase was painful.** Finding where a command was implemented meant scrolling through 73K lines or relying on grep. No IDE could provide useful file-level structure because everything was in one file.
- **Merge conflicts were constant.** Any two developers touching different features (say, Drive and Gmail) would conflict because they were editing the same file.
- **Understanding scope was impossible.** Which constants belong to Drive? Which helper functions are shared vs. specific to Gmail? When everything is in one namespace, you can't tell.
- **Code review was difficult.** A PR that modifies "Drive label permissions" shouldn't require a reviewer to open a 73K-line file and locate the relevant section.

### What the New Layout Achieves

| Before | After |
|--------|-------|
| 1 file, 72,735 lines | 95 files, all under 100KB |
| `gam/__init__.py` does everything | `gam/__init__.py` is a thin hub (~4,660 lines) |
| Find a function: scroll or grep the monolith | Find a function: look in the obvious module |
| Merge conflicts on every PR | Parallel work on Drive, Gmail, etc. with no conflicts |

**Concrete benefits for developers:**

1. **Find things fast.** Working on Gmail labels? Open `gam/cmd/gmail/labels.py`. Working on shared drive permissions? Open `gam/cmd/drive/shareddrives.py`. The file name tells you what's inside.

2. **Smaller blast radius.** A change to Drive copy/move logic only touches `gam/cmd/drive/copymove/`. Reviewers can focus on the relevant 50-90KB file instead of a 73K-line monolith.

3. **Better IDE support.** File outlines, go-to-definition, and symbol search all work better with reasonably-sized files. Your IDE's file explorer now shows a meaningful tree.

4. **Easier onboarding.** A new contributor can understand the codebase structure by looking at the directory tree. "Oh, Chat commands are in `cmd/chat/`, Drive stuff is in `cmd/drive/`" — it's self-documenting.

5. **No performance cost.** `gam print users` runs in ~0.39s, identical to before. Python's import system caches modules, so the split adds negligible startup overhead.

---

## 2. Where Did Everything Go?

### The New Layout

```
src/gam/
├── __init__.py              # Hub: re-exports, dispatch tables, core infra (~4,660 lines)
├── __main__.py              # Entry point
│
├── cmd/                     # ALL command implementations live here
│   ├── __init__.py
│   │
│   │── admin.py             # Admin roles & privileges
│   │── alerts.py            # Alert Center
│   │── aliases.py           # User/group aliases
│   │── analytics.py         # Google Analytics
│   │── audit.py             # Email Audit monitors (removed — stub)
│   │── browsers.py          # Chrome browser management
│   │── caa.py               # Context-Aware Access levels
│   │── calendar.py          # Calendar ACLs, events, settings
│   │── chromeapps.py        # Chrome app management
│   │── chromepolicies.py    # Chrome policy management
│   │── cidevices.py         # Cloud Identity devices
│   │── ciuserinvitations.py # Cloud Identity user invitations
│   │── cloudstorage.py      # Cloud Storage management
│   │── contacts.py          # Domain Shared Contacts (removed — stub) + People API utilities
│   │── cros.py              # ChromeOS device management
│   │── customer.py          # Customer/domain settings
│   │── datatransfer.py      # Data transfer management
│   │── delegates.py         # Domain-wide delegation
│   │── domains.py           # Domain management
│   │── licenses.py          # License management (domain-level)
│   │── meet.py              # Google Meet
│   │── mobile.py            # Mobile device management
│   │── notes.py             # Google Keep notes
│   │── oauth.py             # OAuth credential management
│   │── orgunits.py          # Organizational units
│   │── people.py            # People API / contacts
│   │── printers.py          # Printer management
│   │── project.py           # API project management
│   │── reports.py           # Admin reports
│   │── reseller.py          # Reseller operations
│   │── resources.py         # Calendar resources, buildings, features
│   │── schemas.py           # User schema management
│   │── send_email.py        # Send email commands
│   │── sites.py             # Google Sites
│   │── sso.py               # Inbound SSO profiles & credentials
│   │── tasks.py             # Google Tasks & Tag Manager
│   │── userservices.py      # ASPs, backup codes, calendars, working locations
│   │
│   │── chat/                # Google Chat (sub-package)
│   │   ├── __init__.py      #   Re-exports from sub-modules
│   │   ├── setup.py         #   Chat setup, emoji, sections
│   │   ├── spaces.py        #   Chat space CRUD
│   │   └── members.py       #   Members, messages, reactions
│   │
│   │── cigroups/            # Cloud Identity Groups (sub-package)
│   │   ├── __init__.py
│   │   ├── groups.py        #   CI group CRUD
│   │   └── members.py       #   CI group members
│   │
│   │── courses/             # Google Classroom (sub-package)
│   │   ├── __init__.py
│   │   ├── courses.py       #   Course CRUD, info, listing
│   │   ├── content.py       #   Announcements, topics, materials, work
│   │   ├── participants.py  #   Student/teacher add/remove/sync
│   │   └── guardians.py     #   Guardian invitations
│   │
│   │── drive/               # Google Drive (sub-package)
│   │   ├── __init__.py      #   Re-exports all drive symbols
│   │   ├── core.py          #   Search, entities, file attributes, MIME types
│   │   ├── activity.py      #   Drive activity reporting, settings
│   │   ├── filepaths.py     #   Path resolution, field mapping
│   │   ├── revisions.py     #   File revision management
│   │   ├── filetree.py      #   File tree building, permission matching
│   │   ├── filelist.py      #   File listing & printing
│   │   ├── fileinfo.py      #   File counts, comments, disk usage
│   │   ├── files.py         #   File create/update/shortcuts
│   │   ├── permissions.py   #   File ACLs & permissions
│   │   ├── labels.py        #   Drive labels & label permissions
│   │   ├── shareddrives.py  #   Shared drive management
│   │   ├── looker.py        #   Looker Studio assets
│   │   ├── copymove/        #   Copy & move (nested sub-package)
│   │   │   ├── __init__.py
│   │   │   ├── copymove_util.py  # Statistics, options, copy logic
│   │   │   └── copymove_move.py  # Move logic, permission updates
│   │   └── transfer/        #   Transfer & ownership (nested sub-package)
│   │       ├── __init__.py
│   │       ├── fileops.py   #   Delete, trash, download, documents
│   │       └── ownership.py #   Transfer drive, claim ownership
│   │
│   │── gmail/               # Gmail (sub-package)
│   │   ├── __init__.py
│   │   ├── profile.py       #   Gmail profile, watch
│   │   ├── labels.py        #   Label CRUD
│   │   ├── messages.py      #   Messages, threads, drafts, export, forward
│   │   ├── delegates.py     #   Mail delegation
│   │   ├── filters.py       #   Mail filters
│   │   ├── forms.py         #   Google Forms
│   │   ├── settings.py      #   Forwarding, IMAP, POP, language, SendAs
│   │   ├── smime.py         #   S/MIME certificates
│   │   ├── cse.py           #   Client-side encryption
│   │   └── signature.py     #   Signatures & vacation responders
│   │
│   │── groups/              # Google Groups (sub-package)
│   │   ├── __init__.py
│   │   ├── groups.py        #   Group CRUD, settings, info
│   │   └── members.py       #   Member management, display, sync
│   │
│   │── userop/              # Per-user operations (sub-package)
│   │   ├── __init__.py
│   │   ├── usergroups.py    #   User group membership, Looker Studio
│   │   ├── licenses.py      #   Per-user license management
│   │   ├── photos.py        #   User photos & profile
│   │   ├── sheets.py        #   Google Sheets operations
│   │   └── tokens.py        #   OAuth tokens & deprovisioning
│   │
│   │── users/               # User management (sub-package)
│   │   ├── __init__.py
│   │   ├── manage.py        #   User CRUD, attributes, schemas
│   │   └── display.py       #   User info & print/show
│   │
│   └── vault/               # Google Vault (sub-package)
│       ├── __init__.py
│       ├── matters.py       #   Vault matters & exports
│       └── holds.py         #   Vault holds, queries, counts
│
├── gamlib/                  # GAM library: config, constants, API definitions
├── gapi/                    # Google API wrappers
└── util/                    # Utilities: CSV, batch, args, entity, api
```

### What Stayed in `__init__.py`

The hub file (`~4,660 lines`) still contains:

| Section | Purpose |
|---------|---------|
| **Imports** (~300 lines) | Standard library + GAM internal imports |
| **Re-export blocks** (~2,300 lines) | `from gam.cmd.X import (...)` — backward compatibility |
| **Core infrastructure** (~500 lines) | Error handling, entity operations, output formatting |
| **Dispatch tables** (~800 lines) | `MAIN_COMMANDS`, `MAIN_COMMANDS_WITH_OBJECTS` — maps command names to handler functions |
| **Command processing** (~700 lines) | `ProcessGAMCommand()`, batch/CSV handling, resource command routing |

The re-export blocks ensure that any code doing `gam.copyDriveFile()` or `from gam import copyDriveFile` continues to work without changes.

### How to Find a Function

**Method 1: Intuition.** The module names are descriptive. If you're looking for Gmail label code, check `gam/cmd/gmail/labels.py`. If you want Drive shared drive logic, check `gam/cmd/drive/shareddrives.py`.

**Method 2: grep.**
```bash
# Find where a function is defined
grep -rn "def copyDriveFile" src/gam/cmd/

# Result: src/gam/cmd/drive/copymove/copymove_util.py:947
```

**Method 3: Check the dispatch table.** If you know the GAM command name, search the dispatch tables in `__init__.py`:
```bash
grep "copyDriveFile\|copy.*drivefile" src/gam/__init__.py

# Shows:  Cmd.ARG_DRIVEFILE: copyDriveFile,
# Then grep for the import to find its module:
# from gam.cmd.drive import ( ... copyDriveFile, ... )
```

**Method 4: Follow the re-export chain.** Every function is re-exported from `__init__.py`. Search for the name there to see which `cmd/` module it comes from:
```bash
grep -B50 "copyDriveFile," src/gam/__init__.py | grep "^from"

# Result: from gam.cmd.drive import (
# Then check drive/__init__.py to find the sub-module:
grep -B20 "copyDriveFile," src/gam/cmd/drive/__init__.py | grep "^from"

# Result: from gam.cmd.drive.copymove import (
# And finally:
grep -B20 "copyDriveFile," src/gam/cmd/drive/copymove/__init__.py | grep "^from"

# Result: from gam.cmd.drive.copymove.copymove_util import (
```

**Method 5: Your IDE.** Open `__init__.py`, Ctrl/Cmd-click on any function name, and your IDE will jump to the definition in the correct `cmd/` sub-module.

### The Module Pattern

Every extracted module follows the same pattern:

```python
"""Brief description of what this module handles."""

import sys
from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glindent
# ... other imports as needed

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()

def _getMain():
    return sys.modules['gam']
```

Key points:

- **`_getMain()`** provides lazy runtime access to the `gam` module (i.e., `__init__.py`). This avoids circular imports — modules can't directly `import gam` during initialization because `gam` is still loading. Instead, they call `_getMain()` at runtime when the function is actually executed. Any function defined in `__init__.py` or re-exported through it is accessible as `_getMain().functionName()`.
- **`Act`, `Ent`, `Ind`, `Cmd`** are local instances of the standard GAM helper classes. These four classes (`GamAction`, `GamEntity`, `GamIndent`, `GamCLArgs`) use **class-level shared state**, meaning all instances across all modules see the same values. When `__init__.py` calls `Act.Set(Act.CREATE)` before dispatching to a command handler, every module's `Act` instance immediately reflects that action. This was necessary because the original monolith had a single instance of each; the refactoring created multiple instances that must stay synchronized.
- **Module-level constants** that were originally in `__init__.py` (like `MIMETYPE_GA_FOLDER`, `ME_IN_OWNERS`, `UNKNOWN`, `UTF8`, etc.) are duplicated into the modules that need them. This avoids import-time dependencies on the not-yet-loaded hub.
- **Cross-module function calls** use `_getMain()` for GAM-internal functions (e.g., `_getMain().entityUnknownWarning(...)`) rather than direct imports, which would cause circular import errors during module loading. Standard library and third-party imports (e.g., `from passlib.hash import sha512_crypt`) are safe to import directly at module level.

---

## 3. What Happened to GData (Audit and Domain Shared Contacts)?

GAM previously used two legacy Google APIs built on the GData XML protocol:

1. **Email Audit API** — `gam audit monitor create/delete/list`
2. **Domain Shared Contacts API** — `gam create/update/delete/print contacts`

Both APIs, along with the vendored `gdata/` and `atom/` libraries (~10,000 lines), have been **completely removed**.

The affected commands now print a deprecation notice:

```
ERROR: GAM no longer supports the legacy <API> API and this command.
If you must use this API you can install a copy of GAM 7.46.07
which is the last version to support this command.
```

`contacts.py` still contains the People API utilities (shared constants, `PeopleManager`, etc.) used by `people.py` for modern user contact management.
