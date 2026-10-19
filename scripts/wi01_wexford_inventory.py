#!/usr/bin/env python3
"""WI-01 read-only inventory of private Wexford assets."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ID = "baf85d6f-8821-451f-87f6-5a90ccfd5f56"
FOLDERS = ("erw-pdf-sources", "erw-word-documents", "research-environments")
DATABASES = ("workbench-v12.sqlite3", "scwb-identity-v121.sqlite3", "erw010-predeploy.sqlite3")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inventory(root):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Not a directory")
    files, warnings = [], []
    def capture(path, kind):
        try:
            st = path.lstat()
            if not stat.S_ISREG(st.st_mode):
                warnings.append("Skipped nonregular: " + str(path.relative_to(root)))
                return
            row = dict(kind=kind, path=path.relative_to(root).as_posix(), bytes=st.st_size, sha256=digest(path))
            if kind == "database":
                row["note"] = "Live SQLite hash is not a consistent backup"
            files.append(row)
        except (OSError, PermissionError) as exc:
            warnings.append(f"Failed {path.relative_to(root)}: {type(exc).__name__}")
    for folder in FOLDERS:
        base = root / folder
        if not base.is_dir():
            warnings.append("Directory missing or inaccessible: " + folder)
            continue
        for directory, dirs, names in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
            for name in sorted(names):
                capture(Path(directory) / name, folder)
    for name in DATABASES:
        path = root / name
        if path.exists():
            capture(path, "database")
        else:
            warnings.append("Database missing or inaccessible: " + name)
    return dict(schema="sc.wexford.wi01.inventory.v1", project_id=PROJECT_ID,
                generated_at=datetime.now(timezone.utc).isoformat(),
                data_root=str(root), files=sorted(files, key=lambda r: r["path"]),
                warnings=warnings, backup_verified=False, scientific_results_verified=False)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", default="/opt/sustainable-catalyst/workbench/data")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    root = Path(args.data_root).resolve(strict=True)
    out = Path(args.output).resolve()
    if root == out or root in out.parents:
        p.error("Output must be outside the live data directory")
    if out.exists():
        p.error("Refusing to overwrite existing inventory")
    record = inventory(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        os.chmod(out, 0o600)
        json.dump(record, handle, indent=2)
        handle.write("\n")
    print(f"Inventory: {out} ({len(record['files'])} files, {len(record['warnings'])} warnings)")

if __name__ == "__main__":
    main()
