"""Run the same pinned formatters from Makefile, Git hooks and CI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / ".venv-format" / "bin"
PRETTIER = ROOT / "node_modules" / "prettier" / "bin" / "prettier.cjs"
EXCLUDED_PARTS = {
    ".agents",
    ".claude",
    ".kilo",
    ".git",
    ".venv",
    ".venv-format",
    ".cache-format",
    "node_modules",
    "__pycache__",
    "dbt_packages",
    "target",
    "logs",
    "tmp",
    "data",
    "backups",
    "guides",
}
PRETTIER_SUFFIXES = {
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".js",
    ".cjs",
    ".mjs",
    ".ts",
    ".cts",
    ".mts",
    ".jsx",
    ".tsx",
    ".css",
    ".html",
}


def supported(path: Path) -> bool:
    """Do not modify generated artifacts, vendored code or chart settings."""
    return (
        path.suffix in {".py", ".sql", *PRETTIER_SUFFIXES}
        and not EXCLUDED_PARTS.intersection(path.parts)
        and path.parts[:2] != ("pipeline", "vendor")
        and path.parts[:3] != ("analytics", "dbt", "charts")
        and path.as_posix() not in {"analytics/dbt/dbt_charts.yml", "package-lock.json"}
        and not (ROOT / path).is_symlink()
        and (ROOT / path).is_file()
    )


def source_files(paths: list[str], all_files: bool) -> list[Path]:
    roots = []
    for name in paths:
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(f"Path is outside this repository: {name}")
        roots.append(path.relative_to(ROOT))
    if all_files or any((ROOT / p).is_dir() for p in roots):
        # Git's exclusion rules keep local secrets/data out. Include untracked
        # source files too, so a newly created model is formatted before staging.
        listing = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        )
        candidates = {Path(os.fsdecode(p)) for p in listing.split(b"\0") if p}
        if not all_files:
            candidates = {
                p for p in candidates if any(p == r or r in p.parents for r in roots)
            }
    else:
        candidates = set(roots)
    return sorted(p for p in candidates if supported(p))


def run(command: list[str | Path], files: list[Path]) -> int:
    if not files:
        return 0
    print(f"{Path(command[0]).name}: {len(files)} files", flush=True)
    return subprocess.run(
        [str(part) for part in [*command, *files]], cwd=ROOT, check=False
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Do not write files")
    parser.add_argument("--all", action="store_true", help="All authored source files")
    parser.add_argument(
        "paths", nargs="*", help="File or directory paths from repo root"
    )
    args = parser.parse_args()
    if not args.all and not args.paths:
        parser.error("Pass --all or at least one path")
    required = [BIN / name for name in ("ruff", "sqlfmt", "sqlfluff")]
    if not all(p.exists() for p in required) or not PRETTIER.exists():
        print("Formatters are missing. Run make format-setup first.", file=sys.stderr)
        return 2

    files = source_files(args.paths, args.all)
    python = [p for p in files if p.suffix == ".py"]
    dbt = [
        p for p in files if p.suffix == ".sql" and p.parts[:2] == ("analytics", "dbt")
    ]
    postgres = [p for p in files if p.suffix == ".sql" and p not in dbt]
    other = [p for p in files if p.suffix in PRETTIER_SUFFIXES]
    commands = [
        ([BIN / "ruff", "format", *(["--check"] if args.check else [])], python),
        ([BIN / "sqlfmt", *(["--check"] if args.check else [])], dbt),
        ([BIN / "sqlfluff", "lint" if args.check else "fix"], postgres),
        (["node", PRETTIER, "--check" if args.check else "--write"], other),
    ]
    # Report errors from every formatter, rather than hiding later failures.
    results = [run(command, group) for command, group in commands]
    return 1 if any(results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
