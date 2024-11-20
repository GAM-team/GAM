# -*- coding: utf-8 -*-

# Copyright (C) 2024 Ross Scroggs All Rights Reserved.
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

"""GAM action processing

"""

class GamAction():

# Keys into NAMES; arbitrary values but must be unique
  ACCEPT = 'acpt'
  ADD = 'add '
  ADD_PREVIEW = 'addp'
  APPEND = 'apnd'
  APPROVE = 'aprv'
  ARCHIVE = 'arch'
  BACKUP = 'back'
  BLOCK = 'blok'
  CANCEL = 'canc'
  CANCEL_WIPE = 'canw'
  CHECK = 'chek'
  CLAIM = 'clai'
  CLAIM_OWNERSHIP = 'clow'
  CLEAR = 'clea'
  CLOSE = 'clos'
  COLLECT = 'coll'
  COMMENT = 'comm'
  COPY = 'copy'
  COPY_MERGE = 'copm'
  CREATE = 'crea'
  CREATE_PREVIEW = 'crep'
  CREATE_SHORTCUT = 'crsc'
  DEDUP = 'dedu'
  DELETE = 'dele'
  DELETE_EMPTY = 'delm'
  DELETE_PREVIEW = 'delp'
  DELETE_SHORTCUT = 'desc'
  DEPROVISION = 'depr'
  DISABLE = 'disa'
  DOWNLOAD = 'down'
  DRAFT = 'draf'
  EMPTY = 'empt'
  ENABLE = 'enbl'
  END = 'end '
  EXISTS = 'exis'
  EXPORT = 'expo'
  EXTRACT = 'extr'
  GET_COMMAND_RESULT = 'gtcr'
  FETCH = 'fetc'
  FORWARD = 'forw'
  HIDE = 'hide'
  IMPORT = 'impo'
  INFO = 'info'
  INITIALIZE = 'init'
  INSERT = 'insr'
  INVALIDATE = 'inva'
  ISSUE_COMMAND = 'isco'
  LIST = 'list'
  LOOKUP = 'look'
  MERGE = 'merg'
  MODIFY = 'modi'
  MOVE = 'move'
  MOVE_MERGE = 'movm'
  NOACTION = 'noac'
  NOACTION_PREVIEW = 'noap'
  OBLITERATE = 'obli'
  PERFORM = 'perf'
  PRE_PROVISIONED_DISABLE ='ppdi'
  PRE_PROVISIONED_REENABLE ='ppre'
  PRINT = 'prin'
  PROCESS = 'proc'
  PROCESS_PREVIEW = 'prop'
  PURGE = 'purg'
  RECREATE = 'recr'
  REENABLE = 'reen'
  REFRESH = 'refr'
  RELABEL = 'rela'
  REMOVE = 'remo'
  REMOVE_PREVIEW = 'remp'
  RENAME = 'rena'
  REOPEN = 'reop'
  REPLACE = 'repl'
  REPLACE_DOMAIN = 'repd'
  REPORT = 'repo'
  RESET_YUBIKEY_PIV = 'rpiv'
  RESPOND = 'resp'
  RESTORE = 'rest'
  RESUBMIT = 'res'
  RETAIN = 'reta'
  RETRIEVE_DATA = 'retd'
  REVOKE = 'revo'
  SAVE = 'save'
  SEND = 'send'
  SENDEMAIL = 'snem'
  SET = 'set '
  SETUP = 'setu'
  SHARE = 'shar'
  SHOW = 'show'
  SIGNOUT = 'siou'
  SKIP = 'skip'
  SPAM = 'spam'
  SUBMIT = 'subm'
  SUSPEND = 'susp'
  SYNC = 'sync'
  TRANSFER = 'tran'
  TRANSFER_OWNERSHIP = 'trow'
  TRASH = 'tras'
  TURNOFF2SV = 'to2s'
  UNDELETE = 'unde'
  UNHIDE = 'unhi'
  UNSUSPEND = 'unsu'
  UNTRASH = 'untr'
  UPDATE = 'upda'
  UPDATE_MOVE = 'upmo'
  UPDATE_OWNER = 'updo'
  UPDATE_PREVIEW = 'updp'
  UPLOAD = 'uplo'
  UNZIP = 'unzi'
  USE = 'use '
  VERIFY = 'vrfy'
  WAITFORMAILBOX = 'wamb'
  WATCH = 'watc'
  WIPE = 'wipe'
  WIPE_PREVIEW = 'wipp'
  # Usage:
  # ACTION_NAMES[1] n Items - Delete 10 Users
  # Item xxx ACTION_NAMES[0] - User xxx Deleted
  # These values can be translated into other languages
  _NAMES = {
    ACCEPT: ['Accepted', 'Accept'],
    ADD: ['Added', 'Add'],
    ADD_PREVIEW: ['Added (Preview)', 'Add (Preview)'],
    APPEND: ['Appended', 'Append'],
    APPROVE: ['Approved', 'Approve'],
    ARCHIVE: ['Archived', 'Archive'],
    BACKUP: ['Backed up', 'Backup'],
    BLOCK: ['Blocked', 'Block'],
    CANCEL: ['Cancelled', 'Cancel'],
    CANCEL_WIPE: ['Wipe Cancelled', 'Cancel Wipe'],
    CHECK: ['Checked', 'Check'],
    CLAIM: ['Claimed', 'Claim'],
    CLAIM_OWNERSHIP: ['Ownership Claimed', 'Claim Ownership'],
    CLEAR: ['Cleared', 'Clear'],
    CLOSE: ['Closed', 'Close'],
    COLLECT: ['Collected', 'Collect'],
    COMMENT: ['Commented', 'Comment'],
    COPY: ['Copied', 'Copy'],
    COPY_MERGE: ['Copied(Merge)', 'Copy(Merge)'],
    CREATE: ['Created', 'Create'],
    CREATE_PREVIEW: ['Created (Preview)', 'Create (Preview)'],
    CREATE_SHORTCUT: ['Created Shortcut', 'Create Shortcut'],
    DEDUP: ['Duplicates Deleted', 'Delete Duplicates'],
    DELETE: ['Deleted', 'Delete'],
    DELETE_EMPTY: ['Deleted', 'Delete Empty'],
    DELETE_PREVIEW: ['Deleted (Preview)', 'Delete (Preview)'],
    DELETE_SHORTCUT: ['Deleted Shortcut', 'Delete Shortcut'],
    DEPROVISION: ['Deprovisioned', 'Deprovision'],
    DISABLE: ['Disabled', 'Disable'],
    DOWNLOAD: ['Downloaded', 'Download'],
    DRAFT: ['Drafted', 'Draft'],
    EMPTY: ['Emptied', 'Empty'],
    ENABLE: ['Enabled', 'Enable'],
    END: ['Ended', 'End'],
    EXISTS: ['Exists', 'Exists'],
    EXPORT: ['Exported', 'Export'],
    EXTRACT: ['Extracted', 'Extract'],
    FORWARD: ['Forwarded', 'Forward'],
    GET_COMMAND_RESULT: ['Got Command Result', 'Get Command Result'],
    HIDE: ['Hidden', 'Hide'],
    IMPORT: ['Imported', 'Import'],
    INFO: ['Shown', 'Show Info'],
    INITIALIZE: ['Initialized', 'Initialize'],
    INSERT: ['Inserted', 'Insert'],
    INVALIDATE: ['Invalidated', 'Invalidate'],
    ISSUE_COMMAND: ['Command Issued', 'Issue Command'],
    LIST: ['Listed', 'List'],
    LOOKUP: ['Lookedup', 'Lookup'],
    MERGE: ['Merged', 'Merge'],
    MODIFY: ['Modified', 'Modify'],
    MOVE: ['Moved', 'Move'],
    MOVE_MERGE: ['Moved(Merge)', 'Move(Merge)'],
    NOACTION: ['No Action', 'No Action'],
    NOACTION_PREVIEW: ['No Action (Preview)', 'No Action (Preview)'],
    OBLITERATE: ['Obliterated', 'Obliterate'],
    PERFORM: ['Action Performed', 'Perform Action'],
    PRE_PROVISIONED_DISABLE: ['PreProvisioned Disabled', 'PreProvisioned Disable'],
    PRE_PROVISIONED_REENABLE: ['PreProvisioned Reenabled', 'PreProvisioned Reenable'],
    PRINT: ['Printed', 'Print'],
    PROCESS: ['Processed', 'Process'],
    PROCESS_PREVIEW: ['Processed (Preview)', 'Process (Preview)'],
    PURGE: ['Purged', 'Purge'],
    RECREATE: ['Recreated', 'Recreate'],
    REENABLE: ['Reenabled', 'Reenable'],
    REFRESH: ['Refreshed', 'Refresh'],
    RELABEL: ['Relabeled', 'Relabel'],
    REMOVE: ['Removed', 'Remove'],
    REMOVE_PREVIEW: ['Removed (Preview)', 'Remove (Preview)'],
    RENAME: ['Renamed', 'Rename'],
    REOPEN: ['Reopened', 'Reopen'],
    REPLACE: ['Replaced', 'Replace'],
    REPLACE_DOMAIN: ['Domain Replaced', 'Replace Domain'],
    REPORT: ['Reported', 'Report'],
    RESET_YUBIKEY_PIV: ['Yubikey PIV Reset', 'Reset Yubikey PIV'],
    RESPOND: ['Responded', 'Respond'],
    RESTORE: ['Restored', 'Restore'],
    RESUBMIT: ['Resubmitted', 'Resubmit'],
    RETAIN: ['Retained', 'Retain'],
    RETRIEVE_DATA: ['Data Retrieved', 'Retrieve Data'],
    REVOKE: ['Revoked', 'Revoke'],
    SAVE: ['Saved', 'Save'],
    SEND: ['Sent', 'Send'],
    SENDEMAIL: ['Email Sent', 'Send Email'],
    SET: ['Set', 'Set'],
    SETUP: ['Set Up', 'Set Up'],
    SHARE: ['Shared', 'Share'],
    SHOW: ['Shown', 'Show'],
    SIGNOUT: ['Signed Out', 'Signout'],
    SKIP: ['Skipped', 'Skip'],
    SPAM: ['Marked as Spam', 'Mark as Spam'],
    SUBMIT: ['Submitted', 'Submit'],
    SUSPEND: ['Suspended', 'Suspend'],
    SYNC: ['Synced', 'Sync'],
    TRANSFER: ['Transferred', 'Transfer'],
    TRANSFER_OWNERSHIP: ['Ownership Transferred', 'Transfer Ownership'],
    TRASH: ['Trashed', 'Trash'],
    TURNOFF2SV: ['2-Step Verification Turned Off', 'Turn Off 2-Step Verification'],
    UNDELETE: ['Undeleted', 'Undelete'],
    UNHIDE: ['Unhidden', 'Unhide'],
    UNSUSPEND: ['Unsuspended', 'Unsuspend'],
    UNTRASH: ['Untrashed', 'Untrash'],
    UNZIP: ['Unzipped', 'Unzip'],
    UPDATE: ['Updated', 'Update'],
    UPDATE_MOVE: ['Updated/Moved', 'Update/Move'],
    UPDATE_OWNER: ['Updated to Owner', 'Update to Owner'],
    UPDATE_PREVIEW: ['Updated (Preview)', 'Update (Preview)'],
    UPLOAD: ['Uploaded', 'Upload'],
    USE: ['Used', 'Use'],
    VERIFY: ['Verified', 'Verify'],
    WAITFORMAILBOX: ['Mailbox is Setup', 'Check Mailbox is Setup'],
    WATCH: ['Watched', 'Watch'],
    WIPE: ['Wiped', 'Wipe'],
    WIPE_PREVIEW: ['Wiped (Preview)', 'Wipe (Preview)'],
    }
  #
  MODIFIER_CONTENTS_WITH = 'contents with'
  MODIFIER_FOR = 'for'
  MODIFIER_FROM = 'from'
  MODIFIER_IN = 'in'
  MODIFIER_INTO = 'into'
  MODIFIER_PREVIOUSLY_IN = 'previously in'
  MODIFIER_TO = 'to'
  MODIFIER_WITH_COTEACHER_OWNER = 'with co-teacher as owner'
  MODIFIER_WITH_NEW_TEACHER_OWNER = 'with new teacher as owner'
  MODIFIER_WITH_CURRENT_OWNER = 'with current owner'
  MODIFIER_WITH = 'with'
  MODIFIER_WITH_CONTENT_FROM = 'with content from'
  PREFIX_NOT = 'Not'
  PREVIEW = 'Preview'
  SUCCESS = 'Success'
  SUFFIX_FAILED = 'Failed'

  def __init__(self):
    self.action = None

  def Set(self, action):
    self.action = action

  def Get(self):
    return self.action

  def ToPerform(self):
    return self._NAMES[self.action][1]

  def Performed(self):
    return self._NAMES[self.action][0]

  def Failed(self):
    return f'{self._NAMES[self.action][1]} {self.SUFFIX_FAILED}'

  def NotPerformed(self):
    actionWords = self._NAMES[self.action][0].split(' ')
    if len(actionWords) != 2:
      return f'{self.PREFIX_NOT} {self._NAMES[self.action][0]}'
    return f'{actionWords[0]} {self.PREFIX_NOT} {actionWords[1]}'

  def PerformedName(self, action):
    return self._NAMES[action][0]

  def ToPerformName(self, action):
    return self._NAMES[action][1]

  def csvFormat(self):
    return self.action == self.PRINT
