# MCP Server

`gam mcp` turns GAM into a [Model Context Protocol](https://modelcontextprotocol.io) server. An AI assistant
(Claude Desktop, Claude Code, Gemini CLI, or any other MCP client) that spawns `gam mcp` can then:

* look up the exact syntax of any GAM command from `GamCommands.txt` (`gam_syntax`),
* read and search this wiki (`gam_docs`),
* run a GAM command and get its output back as data (`gam_run`); read-only unless you say otherwise.

The server needs nothing beyond GAM itself: no extra packages, no network account, no changes to your
`gam.cfg`. It speaks JSON-RPC over stdin/stdout, so it works wherever GAM runs.

- [Syntax](#syntax)
- [Configure your assistant](#configure-your-assistant)
- [Tools](#tools)
  - [gam_syntax](#gam_syntax)
  - [gam_docs](#gam_docs)
  - [gam_run](#gam_run)
- [Resources](#resources)
- [The read-only gate](#the-read-only-gate)
- [Commands that are always refused](#commands-that-are-always-refused)
- [Documentation sources, caching and nowiki](#documentation-sources-caching-and-nowiki)
- [Timeouts and concurrency](#timeouts-and-concurrency)
- [Security notes](#security-notes)
- [Protocol versions](#protocol-versions)
- [For developers](#for-developers)

## Syntax
```
gam mcp [allowwrites] [maxrows <Number>] [timeout <Number>] [nowiki]
```
* `allowwrites` - let `gam_run` execute commands that change your domain (create, update, delete, ...).
Without it the server is read-only; see [The read-only gate](#the-read-only-gate).
* `maxrows <Number>` - maximum number of CSV rows returned by one `gam_run` call; default 500. Rows beyond
the limit are dropped and the reply says `truncated`. Use 0 for no limit.
* `timeout <Number>` - seconds a `gam_run` command may take before the assistant gets a timeout error; default 300.
* `nowiki` - never fetch wiki pages from GitHub; see [Documentation sources](#documentation-sources-caching-and-nowiki).

The usual meta commands work: `gam select <Section> mcp` serves commands with the values from `<Section>` of `gam.cfg`,
and the `GAMCFGDIR` environment variable selects the configuration directory.

Run `gam version` once from a terminal before configuring an assistant: on a brand new installation GAM creates
`gam.cfg` and prints where it put it, which must not happen while an assistant is listening.

## Configure your assistant

In every example, replace `/Users/admin/bin/gam7/gam` with the path to your GAM executable and add `allowwrites`
to `args` only if you want the assistant to be able to change your domain.

### Claude Desktop
Edit `claude_desktop_config.json` (Settings > Developer > Edit Config):
```
{
  "mcpServers": {
    "gam": {
      "command": "/Users/admin/bin/gam7/gam",
      "args": ["mcp"],
      "env": {"GAMCFGDIR": "/Users/admin/GAMConfig"}
    }
  }
}
```

### Claude Code
```
claude mcp add gam -- /Users/admin/bin/gam7/gam mcp
```

### Gemini CLI
Edit `~/.gemini/settings.json`:
```
{
  "mcpServers": {
    "gam": {
      "command": "/Users/admin/bin/gam7/gam",
      "args": ["mcp"],
      "env": {"GAMCFGDIR": "/Users/admin/GAMConfig"}
    }
  }
}
```

### Any other client
Spawn `gam mcp` as a stdio server. Restart the client after changing the configuration.

## Tools

### gam_syntax
Search `GamCommands.txt` by keywords. Every hit is the verbatim syntax block of a command, the section it is in,
and the definitions of the non-terminals it references (`<UserTypeEntity>`, `<DriveFieldNameList>`, ...).
```
{"query": "print filelist", "limit": 3}
```
returns, among others:
```
## Users - Drive
gam <UserTypeEntity> print filelist [todrive <ToDriveAttribute>*]
        [((query <QueryDriveFile>) | (fullquery <QueryDriveFile>) | <DriveFileQueryShortcut>)
        ...
        [allfields|<DriveFieldName>*|(fields <DriveFieldNameList>)]
        ...
<UserTypeEntity> ::=
        (all users|users_na|users_arch|users_ns|users_susp|users_arch_or_susp|users_na_ns|users_ns_susp)|
        (user <UserItem>)|
        ...
```
Ranking is by keyword overlap; words that appear in the `gam` line itself, close together and in order, rank highest.
Words that appear nowhere in the syntax are dropped from the search and listed in the reply, so an assistant
asking for `Gems drive files` gets the Drive commands and learns that `gems` is not a GAM term.

### gam_docs
Read a wiki page, one section of a page, or search page titles and section headings.
```
{"page": "Users-Drive-Files-Display"}
{"page": "Users-Drive-Files-Display", "section": "Display file paths"}
{"query": "drive file list fields"}
```
Page names are the wiki URL slugs. With no arguments the tool returns the page list from the sidebar.
Long pages are cut at 60,000 characters and the reply says so; ask for a section instead.

### gam_run
Run one GAM command. `args` is the list of words after `gam`, one argument per element, no shell quoting;
`section` optionally selects a `gam.cfg` section, exactly like `gam select <Section>`.
```
{"args": ["print", "users", "query", "isSuspended=true", "fields", "primaryemail,name"]}
{"args": ["user", "jsmith@domain.com", "print", "filelist", "fields", "id,name,mimetype"], "section": "sales"}
```
The reply has:
* `rc` - GAM's return code, 0 on success; the tool result is flagged as an error when it is not 0.
* `action` - the action GAM associates with the command: `PRINT`, `INFO`, `CREATE`, `DELETE`, ...
* `rows` - for commands that produce CSV output (`print` commands), the rows as a list of objects, straight from
GAM's CSV writer; `titles` are the column names and `list_type` the kind of object. `rows` are not filtered by the
`csv_output_*` variables in `gam.cfg`.
* `stdout` and `stderr` - everything else the command printed, each cut at 100,000 characters.
* `truncated` - true when rows, stdout or stderr were cut.

Commands run in-process, one at a time. The command line is classified before anything runs
(see below); refused commands are reported with the reason and never executed.

## Resources
For clients that let you attach resources to a conversation:
* `gam://syntax` - the whole of `GamCommands.txt`.
* `gam://syntax/<Section>` - one section, e.g. `gam://syntax/Users`.
* `gam://wiki/<Page>` - one wiki page, e.g. `gam://wiki/Users-Drive-Files-Display`.

## The read-only gate
Every GAM command carries an action code; it is what GAM prints as `Deleted`, `Created`, `Updated`, ...
`gam mcp` classifies a command line by walking the same dispatch tables as GAM itself, stopping before any function
runs and before any API is touched. The action codes that count as read-only are `INFO`, `LIST`, `PRINT`, `SHOW`,
`REPORT`, `CHECK`, `EXISTS`, `LOOKUP`, `COMMENT` and `GET_COMMAND_RESULT`, plus `version` and `help`.
Every other action (`CREATE`, `UPDATE`, `DELETE`, `ADD`, `REMOVE`, `WIPE`, `SUSPEND`, `TRANSFER`, ...)
requires `allowwrites`.

`DOWNLOAD` (`get drivefile`, `get photo`, `download ...`) is refused even with `allowwrites`: it writes local files.

A command line the classifier cannot resolve, for example one that GAM itself would reject with a usage error,
is refused, never guessed.

## Commands that are always refused
These words are refused wherever they appear on the command line, with `allowwrites` or without:
* `batch`, `tbatch`, `csv`, `csvtest`, `loop` - read local files and run many commands.
* `redirect`, `config`, `multiprocessexit` - write local files or change `gam.cfg`.
* `select <Section> save`, or `select <Section>` with no command - write `gam.cfg`.
`select <Section> <command>`, `selectfilter`, `selectoutputfilter`, `selectinputfilter` and `showsections` are allowed.
* `oauth` - creates, deletes or displays credentials.
* `create|update|delete|use project`, `create|delete|update|upload|replace|rotate sakey`, `create|delete|update svcacct` - write local credential files;
`print|show|info|check` on the same objects are allowed.
* `audit` - the email audit monitor.
* `sendemail`, `sendreply` - send mail.
* `file`, `csvfile`, `csv`, `datafile`, `csvdatafile`, `csvkmd`, `csvsubkey`, `csvdata`, `crosfile`, `crosfile_sn`,
`croscsv`, `croscsv_sn`, `croscsvfile`, `croscsvfile_sn`, `croscsvdata` - entity selectors that read local files.
* `todrive` - uploads results to Google Drive; refused on a read-only server, allowed with `allowwrites`.

Because these words are refused wherever they appear, a few commands that use one of them as an option are
refused too: `gam cros <CrOSEntity> getcommand|issuecommand ... csv`. Use the CSV form of another command or run them from a terminal.

`gam_run` is not a sandbox. GAM runs with the file system access of the account that started the assistant;
the gate classifies what a command does to your Google Workspace domain and blocks the local file selectors listed
above, nothing more. Options such as `localfile` or `targetfolder` are not blocked.

## Documentation sources, caching and nowiki
* `gam_syntax` reads `GamCommands.txt` from the GAM folder (it is shipped with every release) or, for a
`pip install gam7`, from a source checkout (`src/GamCommands.txt`); failing both, it fetches the file from
GitHub once a day and keeps it under `<cache_dir>/mcp/`.
* `gam_docs` reads pages from `wiki/` in a source checkout when there is one, otherwise it fetches them from
`https://raw.githubusercontent.com/wiki/GAM-team/GAM/` and keeps them under `<cache_dir>/mcp/wiki/` for 24 hours.
When GitHub is unreachable a stale cached copy is used.
* `nowiki` disables every wiki fetch. `gam_docs` then serves only pages present in a checkout or in the cache,
says so in every reply, and lists what it has when the sidebar is not available. Use it on machines without
Internet access to GitHub.

`cache_dir` is the `gam.cfg` variable; by default it is the `gamcache` folder next to `gam.cfg`.

## Timeouts and concurrency
`gam_run` calls are queued and run one at a time; other requests (`ping`, `gam_syntax`, `gam_docs`) are
answered while a command runs. When a command outlives `timeout`, the assistant receives a timeout error; GAM
commands cannot be interrupted, so the command continues in the background and new `gam_run` calls are refused as
busy until it finishes. If the assistant closes the connection while a command is running, the server waits for
it, at most one more timeout period, before exiting.

## Security notes
* The assistant acts as the administrator whose credentials are in `gam.cfg`. Start with a read-only server;
add `allowwrites` only for a configuration section whose credentials have the rights you are willing to hand to
an assistant, and confirm every write it proposes. A single GAM command can touch every account in the domain.
* The server tells the assistant, in its instructions, that everything it returns about people is personal data and
that display names, group descriptions, file names and audit values are text set by domain users to be treated as
data, never as instructions.
* Access and refresh tokens (`ya29.`, `1//`, `access_token`, `refresh_token`, `client_secret`, `private_key`) are
redacted from captured output. `oauth` commands, which display credentials, are refused.
* Only JSON-RPC ever reaches stdout: the server keeps a private copy of the original stdout and points file
descriptor 1 at the null device for the rest of the process, so not even a subprocess can write to the assistant.
GAM's own messages go to stderr, which MCP clients log.
* The read-only default and the refusal list are enforced by the server, not by the assistant.

## Protocol versions
Both the per-request (`2026-07-28`) and the `initialize` handshake revisions (`2025-11-25`, `2025-06-18`,
`2025-03-26`, `2024-11-05`) of MCP are supported; the server answers in whichever the client uses.

## For developers
From a source checkout, with an empty configuration directory GAM creates a default `gam.cfg` and everything
except API calls works without credentials:
```
export GAMCFGDIR=/tmp/gamcfg && mkdir -p "$GAMCFGDIR"
cd src && python3 gam.py version
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"gam_syntax","arguments":{"query":"print users","limit":1}}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"gam_run","arguments":{"args":["version","simple"]}}}' \
  | python3 gam.py mcp
```
API commands fail with `No Client Access allowed` and a non-zero `rc`, which is exactly what the assistant
would see. The same exchange runs in the GitHub build workflow on every platform.

The implementation is `src/gam/gamlib/glmcp.py`, loaded on demand like the YubiKey support.
