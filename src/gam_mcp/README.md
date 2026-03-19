# GAM MCP Server

An MCP (Model Context Protocol) server that exposes [GAM](https://github.com/GAM-team/GAM) (Google Workspace Admin Manager) as tools for AI assistants like Claude. It is a thin wrapper around GAM's `CallGAMCommand` Python API, with built-in access to the full GAM wiki documentation.

## How it works

The server runs as a STDIO MCP process. When an AI assistant needs to manage Google Workspace, it calls one of the available tools. Before executing complex commands, the assistant searches and reads the local wiki documentation to get the exact syntax — no guessing required.

```
Claude  →  MCP tool call  →  gam_mcp/server.py  →  CallGAMCommand()  →  Google APIs
                                      ↑
                               wiki/*.md (167 pages)
```

## Requirements

- Python 3.10+
- GAM installed and configured (`gam oauth create` completed)
- `fastmcp >= 3.0.0`

## Installation

```bash
# From the repo root
pip install -e .
```

The entry point `gam-mcp` is registered automatically.

## Claude Code configuration

Add to `.claude/settings.json` in the project (already present in this repo):

```json
{
  "mcpServers": {
    "gam": {
      "type": "stdio",
      "command": "C:\\Users\\<you>\\AppData\\Roaming\\Python\\Python3XX\\Scripts\\gam-mcp.exe"
    }
  }
}
```

Adjust the path to match where `pip` installed the script. Run `where gam-mcp` (after adding Scripts to PATH) or check the pip install output for the exact path.

## Wiki location

The server expects the wiki at `<repo_root>/wiki/` (167 Markdown files). To override, set the `GAM_WIKI_DIR` environment variable to the wiki directory path:

```json
{
  "mcpServers": {
    "gam": {
      "type": "stdio",
      "command": "...",
      "env": { "GAM_WIKI_DIR": "C:\\path\\to\\wiki" }
    }
  }
}
```

## Available tools

### Wiki — full GAM knowledge on demand

| Tool | Description |
|------|-------------|
| `list_wiki_pages` | List all 167 available GAM wiki pages |
| `read_wiki_page(page_name)` | Read a wiki page by name (without `.md`) |
| `search_wiki(query)` | Search all wiki pages for a keyword |

The assistant uses these to look up exact command syntax before running anything.

### Generic

| Tool | Description |
|------|-------------|
| `run_gam_command(args)` | Run any GAM command — full escape hatch |

### Users

| Tool | Description |
|------|-------------|
| `get_user_info(email)` | Get user details |
| `list_users(query?, fields?)` | List users — optionally filter by query and limit fields to reduce output size |
| `create_user(email, firstname, lastname, password)` | Create a user |
| `update_user(email, attributes)` | Update user fields |
| `delete_user(email)` | Delete a user permanently |
| `suspend_user(email)` | Suspend a user |
| `restore_user(email)` | Restore a suspended user |

### Groups

| Tool | Description |
|------|-------------|
| `get_group_info(email)` | Get group details |
| `list_groups` | List all groups |
| `list_group_members(group_email)` | List members of a group |
| `add_group_member(group_email, member_email)` | Add a member |
| `remove_group_member(group_email, member_email)` | Remove a member |

### Configuration & diagnostics

| Tool | Description |
|------|-------------|
| `check_gam_setup` | Full diagnostic: version + OAuth + config in one call (sequential — GAM is not thread-safe) |
| `get_gam_config` | Show all `gam.cfg` values |
| `set_gam_config(key, value)` | Set a `gam.cfg` variable (`gam config <key> <value> save`) |
| `get_oauth_info` | Show OAuth token info and authorized account |
| `list_authorized_scopes` | List all authorized API scopes |

### Domain / Admin

| Tool | Description |
|------|-------------|
| `get_domain_info` | Get domain information |
| `get_gam_version` | Get GAM version and environment info |

## Output truncation

All GAM output is capped at **50,000 characters**. If truncated, the result includes:
```json
{
  "truncated": true,
  "note": "Output was truncated to 50000 characters. Use more specific filters or fields to reduce output size."
}
```

For large datasets, use the `fields` parameter (e.g. `list_users`) or add `query` filters to narrow results.

## Typical workflow

```
1. check_gam_setup()                          → verify everything is working
2. search_wiki('gmail forwarding')            → find the right wiki page
3. read_wiki_page('Users-Gmail-Forwarding')   → get exact syntax
4. run_gam_command([...])                     → execute
```

## Notes

- GAM uses global state internally and is **not thread-safe** — do not call multiple tools concurrently.
- The `set_gam_config` tool uses the syntax `gam config <key> <value> save`.
- All tool errors are returned as `{"return_code": -1, "output": "<message>"}` rather than raising exceptions.
