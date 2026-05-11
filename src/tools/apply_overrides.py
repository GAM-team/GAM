#!/usr/bin/env python3
import datetime
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

try:
    import tomli_w
except ImportError:
    print("Error: tomli_w is required. Install it via 'pip install tomli-w' or 'uv'")
    sys.exit(1)


def parse_overrides(file_path: Path) -> list[str]:
    """Reads dep-overrides.txt and returns list of unexpired override requirements."""
    active_overrides = []
    today = datetime.date.today()

    if not file_path.exists():
        print(f"No overrides file found at {file_path}. Skipping.")
        return active_overrides

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                # Split on the pipe delimiter: "urllib3>=2.7.0 | 05/22/2026"
                requirement, date_str = [part.strip() for part in line.split("|", 1)]
                
                # Parse expiration date
                month, day, year = map(int, date_str.split("/"))
                expiration_date = datetime.date(year, month, day)

                if expiration_date >= today:
                    # Directly append the exact requirement defined in the file
                    active_overrides.append(requirement)
                    print(f"Active override: {requirement} (expires {date_str})")
                else:
                    print(f"Expired override: {requirement} (expired on {date_str})")
            except Exception as e:
                print(f"Skipping malformed line '{line}': {e}", file=sys.stderr)

    return active_overrides


def main():
    project_root = Path.cwd()
    overrides_file = project_root / "dep-overrides.txt"
    toml_file = project_root / "pyproject.toml"

    if not toml_file.exists():
        print("Error: pyproject.toml not found.", file=sys.stderr)
        sys.exit(1)

    # 1. Parse active overrides
    overrides = parse_overrides(overrides_file)

    # 2. Read pyproject.toml
    with open(toml_file, "rb") as f:
        pyproject = tomllib.load(f)

    # Ensure [tool.uv] section exists
    if "tool" not in pyproject:
        pyproject["tool"] = {}
    if "uv" not in pyproject["tool"]:
        pyproject["tool"]["uv"] = {}

    # 3. Update overrides list
    original_overrides = pyproject["tool"]["uv"].get("overrides", [])
    
    if overrides:
        pyproject["tool"]["uv"]["overrides"] = overrides
    else:
        # If all overrides are expired, drop the key entirely
        pyproject["tool"]["uv"].pop("overrides", None)

    # 4. Save changes only if they differ
    if original_overrides != overrides:
        with open(toml_file, "wb") as f:
            tomli_w.dump(pyproject, f)
        print("Updated pyproject.toml with current overrides.")
    else:
        print("No changes needed for pyproject.toml overrides.")


if __name__ == "__main__":
    main()
