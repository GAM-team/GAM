import multiprocessing
import os
import platform
import re
import tempfile
from pathlib import Path

import httpx
from fastmcp import FastMCP
from gam import CallGAMCommand, initializeLogging

initializeLogging()

mcp = FastMCP(
    "gam",
    instructions=(
        "You are a Google Workspace admin assistant powered by GAM. "
        "Before running any GAM command, use the `search_wiki` tool to find the relevant "
        "wiki page, then read it with `read_wiki_page` to get the exact syntax. "
        "Always prefer reading the wiki before constructing commands. "
        "Use `run_gam_command` for any operation not covered by the specific tools."
    ),
)

# Wiki directory: env var override → repo-relative default
_wiki_env = os.environ.get("GAM_WIKI_DIR")
WIKI_DIR = Path(_wiki_env) if _wiki_env else Path(__file__).parent.parent.parent / "wiki"

# GitHub fallback — raw wiki content
WIKI_GITHUB_REPO = os.environ.get("GAM_WIKI_GITHUB_REPO", "GAM-team/GAM")
WIKI_GITHUB_RAW = f"https://raw.githubusercontent.com/wiki/{WIKI_GITHUB_REPO}"

# Truncate large GAM outputs to avoid flooding the context window
MAX_OUTPUT_CHARS = 50_000


# ---------------------------------------------------------------------------
# GitHub wiki helpers (fallback when local wiki is absent)
# ---------------------------------------------------------------------------

def _github_fetch(page: str) -> str:
    """Fetch a single wiki page from GitHub. Returns content or error string."""
    url = f"{WIKI_GITHUB_RAW}/{page}.md"
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPStatusError as exc:
        return f"GitHub returned {exc.response.status_code} for page '{page}'."
    except httpx.RequestError as exc:
        return f"Network error fetching wiki page '{page}': {exc}"


def _github_list_pages() -> list[str]:
    """Parse _Sidebar.md from GitHub to build the list of wiki page names."""
    content = _github_fetch("_Sidebar")
    if content.startswith("GitHub returned") or content.startswith("Network error"):
        return [content]
    # Extract non-URL markdown links: [Text](Page-Name)
    links = re.findall(r'\[.*?\]\(([^)#]+)\)', content)
    pages = sorted({p.strip() for p in links if not p.startswith("http")})
    return pages


def _github_search(query: str) -> list[dict]:
    """Search via GitHub Code Search API.
    Requires GITHUB_TOKEN env var — unauthenticated requests return 401."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return [{
            "error": (
                "GitHub Code Search requires authentication. "
                "Set the GITHUB_TOKEN environment variable, "
                "or clone the wiki locally with: "
                f"git clone https://github.com/{WIKI_GITHUB_REPO}.wiki.git wiki"
            )
        }]
    url = "https://api.github.com/search/code"
    params = {"q": f"{query} repo:{WIKI_GITHUB_REPO}.wiki", "per_page": 10}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10, headers=headers)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {"page": item["name"].replace(".md", ""), "url": item["html_url"]}
            for item in items
        ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            return [{"error": "GitHub API rate limit hit. Try again later or clone the wiki locally."}]
        return [{"error": f"GitHub API error: {exc.response.status_code}"}]
    except httpx.RequestError as exc:
        return [{"error": f"Network error: {exc}"}]


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _run_gam(*args: str) -> dict:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="gam_mcp_")
    os.close(tmp_fd)  # Critical on Windows: close before GAM opens
    try:
        cmd = ['gam', 'redirect', 'stdout', tmp_path, 'redirect', 'stderr', 'stdout'] + list(args)
        try:
            rc = CallGAMCommand(cmd)
        except Exception as exc:
            return {"return_code": -1, "output": f"GAM raised an exception: {exc}"}

        try:
            with open(tmp_path, 'r', encoding='utf-8', errors='replace') as f:
                output = f.read()
        except OSError as exc:
            return {"return_code": rc, "output": f"Could not read GAM output: {exc}"}
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass  # Ignore if already gone

    truncated = False
    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS]
        truncated = True

    result = {"return_code": rc, "output": output}
    if truncated:
        result["truncated"] = True
        result["note"] = (
            f"Output was truncated to {MAX_OUTPUT_CHARS} characters. "
            "Use more specific filters or fields to reduce output size."
        )
    return result


# ---------------------------------------------------------------------------
# Wiki tools — give Claude full GAM knowledge on demand
# ---------------------------------------------------------------------------

@mcp.tool()
def list_wiki_pages() -> list[str]:
    """List all available GAM wiki documentation pages.
    Uses local wiki if present, otherwise fetches the page list from GitHub.
    Use this to discover which page covers the topic you need."""
    if WIKI_DIR.exists():
        return sorted(p.stem for p in WIKI_DIR.glob("*.md"))
    return _github_list_pages()


@mcp.tool()
def read_wiki_page(page_name: str) -> str:
    """Read a GAM wiki documentation page by name (without .md extension).
    Uses local wiki if present, otherwise fetches directly from GitHub.
    Always read the relevant wiki page before constructing a GAM command
    to get the exact syntax, flags and examples.

    Example: read_wiki_page('Users') to learn user management commands.
    """
    if WIKI_DIR.exists():
        path = WIKI_DIR / f"{page_name}.md"
        if not path.exists():
            matches = [p for p in WIKI_DIR.glob("*.md") if p.stem.lower() == page_name.lower()]
            if matches:
                path = matches[0]
            else:
                available = sorted(p.stem for p in WIKI_DIR.glob("*.md"))
                return f"Page '{page_name}' not found. Available pages:\n" + "\n".join(available)
        return path.read_text(encoding='utf-8', errors='replace')

    # Fallback: fetch from GitHub
    content = _github_fetch(page_name)
    if content.startswith("GitHub returned 404"):
        # Try case-insensitive via page list
        pages = _github_list_pages()
        match = next((p for p in pages if p.lower() == page_name.lower()), None)
        if match and match != page_name:
            return _github_fetch(match)
        return f"Page '{page_name}' not found on GitHub wiki. Available pages:\n" + "\n".join(pages)
    return content


@mcp.tool()
def search_wiki(query: str) -> list[dict]:
    """Search GAM wiki pages for a keyword or topic.
    Uses local full-text search if wiki is present locally.
    Falls back to GitHub Code Search API (unauthenticated, may be rate-limited).

    Example: search_wiki('forwarding') to find pages about email forwarding.
    """
    if WIKI_DIR.exists():
        query_lower = query.lower()
        results = []
        for path in sorted(WIKI_DIR.glob("*.md")):
            lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
            matches = [
                {"line": i + 1, "text": line.strip()}
                for i, line in enumerate(lines)
                if query_lower in line.lower()
            ]
            if matches:
                results.append({
                    "page": path.stem,
                    "match_count": len(matches),
                    "matches": matches[:10],
                })
        results.sort(key=lambda r: r["match_count"], reverse=True)
        return results

    # Fallback: GitHub Code Search API
    return _github_search(query)


# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------

@mcp.tool()
def run_gam_command(args: list[str]) -> dict:
    """Run any GAM command. Pass arguments as a list.

    IMPORTANT: Before using this tool, read the relevant wiki page to get
    the exact syntax. Use search_wiki() to find the right page first.

    Example: run_gam_command(['info', 'user', 'john@example.com'])
    """
    return _run_gam(*args)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@mcp.tool()
def get_user_info(email: str) -> dict:
    """Get detailed info about a Google Workspace user.
    Wiki: read_wiki_page('Users') for all user fields and options."""
    return _run_gam('info', 'user', email)


@mcp.tool()
def list_users(query: str = None, fields: str = None) -> dict:
    """List users in the domain.

    Args:
        query: Optional GAM query string to filter users,
               e.g. 'orgUnitPath=/Sales' or 'isAdmin=True'.
        fields: Comma-separated list of fields to include in output,
                e.g. 'primaryEmail,name,suspended'.
                Omit to get all fields (may produce large output).

    Wiki: read_wiki_page('Users') for query syntax and available fields.
    """
    cmd = ['print', 'users']
    if query:
        cmd += ['query', query]
    if fields:
        cmd += ['fields', fields]
    return _run_gam(*cmd)


@mcp.tool()
def create_user(email: str, firstname: str, lastname: str, password: str) -> dict:
    """Create a new Google Workspace user.
    Wiki: read_wiki_page('Users') for all optional fields (org, phone, etc.)."""
    return _run_gam('create', 'user', email,
                    'firstname', firstname,
                    'lastname', lastname,
                    'password', password)


@mcp.tool()
def update_user(email: str, attributes: dict) -> dict:
    """Update a user's attributes.
    Pass attributes as a dict, e.g. {'firstname': 'John', 'suspended': 'false'}.
    Wiki: read_wiki_page('Users') for all updatable fields."""
    cmd = ['update', 'user', email]
    for key, value in attributes.items():
        cmd += [key, str(value)]
    return _run_gam(*cmd)


@mcp.tool()
def delete_user(email: str) -> dict:
    """Permanently delete a Google Workspace user."""
    return _run_gam('delete', 'user', email)


@mcp.tool()
def suspend_user(email: str) -> dict:
    """Suspend a Google Workspace user account."""
    return _run_gam('update', 'user', email, 'suspended', 'on')


@mcp.tool()
def restore_user(email: str) -> dict:
    """Restore (unsuspend) a previously suspended Google Workspace user."""
    return _run_gam('update', 'user', email, 'suspended', 'off')


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

@mcp.tool()
def get_group_info(email: str) -> dict:
    """Get detailed info about a Google Workspace group.
    Wiki: read_wiki_page('Groups') for all group fields."""
    return _run_gam('info', 'group', email)


@mcp.tool()
def list_groups() -> dict:
    """List all groups in the domain.
    Wiki: read_wiki_page('Groups') for field/filter options."""
    return _run_gam('print', 'groups')


@mcp.tool()
def list_group_members(group_email: str) -> dict:
    """List all members of a group.
    Wiki: read_wiki_page('Groups-Membership') for options."""
    return _run_gam('print', 'group-members', 'group', group_email)


@mcp.tool()
def add_group_member(group_email: str, member_email: str) -> dict:
    """Add a member to a Google Workspace group."""
    return _run_gam('update', 'group', group_email, 'add', 'member', member_email)


@mcp.tool()
def remove_group_member(group_email: str, member_email: str) -> dict:
    """Remove a member from a Google Workspace group."""
    return _run_gam('update', 'group', group_email, 'remove', 'member', member_email)


# ---------------------------------------------------------------------------
# Configuration & diagnostics
# ---------------------------------------------------------------------------

@mcp.tool()
def check_gam_setup() -> dict:
    """Run a full GAM setup diagnostic.
    Shows version, OAuth token info and config values in one call.
    Use this first to understand the current state of the GAM installation.
    Note: runs sequentially — GAM uses global state and is not thread-safe."""
    return {
        "version": _run_gam("version"),
        "oauth_info": _run_gam("oauth", "info"),
        "config": _run_gam("config", "print"),
    }


@mcp.tool()
def get_gam_config() -> dict:
    """Show all current gam.cfg configuration values.
    Wiki: read_wiki_page('gam.cfg') for description of every variable."""
    return _run_gam("config", "print")


@mcp.tool()
def set_gam_config(key: str, value: str) -> dict:
    """Set a gam.cfg configuration variable and save it.
    Syntax used: gam config <key> <value> save

    Example: set_gam_config('auto_batch_min', '20')
    Wiki: read_wiki_page('gam.cfg') for all available keys and valid values."""
    return _run_gam("config", key, value, "save")


@mcp.tool()
def get_oauth_info() -> dict:
    """Show current OAuth token information — which account is authorized,
    expiry, and which scopes/APIs are granted."""
    return _run_gam("oauth", "info")


@mcp.tool()
def list_authorized_scopes() -> dict:
    """List all API scopes currently authorized for GAM.
    Use this to check if a required API scope is missing before running a command."""
    return _run_gam("oauth", "info", "showscopes")


# ---------------------------------------------------------------------------
# Domain / Admin
# ---------------------------------------------------------------------------

@mcp.tool()
def get_domain_info() -> dict:
    """Get information about the Google Workspace domain.
    Wiki: read_wiki_page('Domains') for all domain commands."""
    return _run_gam('info', 'domain')


@mcp.tool()
def get_gam_version() -> dict:
    """Get the current GAM version and environment info."""
    return _run_gam('version')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if platform.system() == 'Linux':
        multiprocessing.set_start_method('forkserver')
    else:
        multiprocessing.freeze_support()
        multiprocessing.set_start_method('spawn', force=True)
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
