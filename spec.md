# What I’m delivering here

Below are the complete file contents to create the packaged project. Create a directory `swatctl-packaged/` and add the files exactly as shown (paths shown as headers). After that run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
# run tests locally
pytest -q
# try CLI
swatctl --help
```

---

## File: `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "swatctl"
version = "0.0.1"
description = "SWAT project management CLI (create projects, pages, install/upgrade SWAT and plugins)"
readme = "README.md"
license = {text = "MIT"}
authors = [{name="You", email="you@example.com"}]
requires-python = ">=3.8"

[project.urls]
"Homepage" = "https://example.org/swatctl"

[project.scripts]
swatctl = "swatctl.cli:main"

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-mock"]

```

---

## File: `setup.cfg`

(keeps setuptools metadata for packaging tests; optional but helpful)

```ini
[metadata]
license-file = LICENSE
```

---

## File: `README.md`

````md
# swatctl

swatctl — a small management CLI for SWAT projects.

Features:
- create-project
- create-page
- swat-set-version (replace lib/ from a git repo@tag)
- plugin-install
- plugin-set-version
- info

Install for development:
```bash
pip install -e ".[test]"
````

Run tests:

```bash
pytest -q
```

Run CLI:

```bash
swatctl --help
```

````

---

## File: `LICENSE`
Use MIT (short form). Paste this:
```text
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
...
````

(Please add your full license text when you create the repo — omitted here for brevity.)

````

---

## Directory: `swatctl/` (package)

### File: `swatctl/__init__.py`
```py
__all__ = ["core", "gitutils", "cli"]
````

### File: `swatctl/gitutils.py`

Provides `git_clone` wrapper used by core. Uses `git` subprocess and supports cloning a local repo for tests.

```py
import subprocess
from pathlib import Path
import shutil
import tempfile

def run(cmd, cwd=None, capture=False):
    if capture:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    else:
        subprocess.check_call(cmd, cwd=cwd)

def git_clone(repo_url: str, ref: str | None = None, dest: str | None = None) -> Path:
    """
    Clone a git repo into dest and return Path(dest).
    If ref is provided, try to shallow clone that ref; otherwise fallback to full clone and checkout.
    """
    if dest is None:
        dest = tempfile.mkdtemp(prefix="swatctl_")
    dest_path = Path(dest)
    if dest_path.exists():
        shutil.rmtree(dest_path)
    # try shallow clone of branch/tag
    cmd = ["git", "clone", "--depth", "1", repo_url, str(dest_path)]
    if ref:
        cmd = ["git", "clone", "--depth", "1", "--branch", ref, repo_url, str(dest_path)]
    try:
        run(cmd)
    except Exception:
        # fallback: full clone then checkout ref
        if dest_path.exists():
            shutil.rmtree(dest_path)
        run(["git", "clone", repo_url, str(dest_path)])
        if ref:
            run(["git", "fetch", "--tags"], cwd=str(dest_path))
            run(["git", "checkout", ref], cwd=str(dest_path))
    return dest_path
```

### File: `swatctl/core.py`

Main program logic extracted to testable functions. Note: functions are intentionally synchronous where possible to simplify tests; file ops use `pathlib`.

```py
import shutil
import json
from pathlib import Path
from .gitutils import git_clone

SWAT_LIB_DIRNAME = "lib"
SWAT_PLUGINS_DIRNAME = "plugins"

TEMPLATES = {
    "index.html": """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <link rel="stylesheet" href="/{libdir}/swat-ui.css">
</head>
<body class="container">
  <div id="root"></div>
  <script type="module" src="./{name}.js"></script>
</body>
</html>
""",
    "page.js": """// {name}.js - simple SWAT entry module
export default async function swatApp(swat){
  const root = document.getElementById('root');
  const div = document.createElement('div');
  div.className = 'card';
  div.innerHTML = '<h3>{title}</h3><p class="muted">Starter page.</p>';
  root.appendChild(div);
}
""",
    "page.css": "/* {name}.css - page styles (optional) */\n"
}

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def write_file(path: Path, text: str, overwrite: bool = False):
    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {path}")
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")

def safe_copytree(src: Path, dst: Path, overwrite: bool = False):
    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")
    if dst.exists():
        if not overwrite:
            raise FileExistsError(f"Destination exists: {dst}")
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    shutil.copytree(src, dst)

def create_project(path: Path, name: str, swat_repo: str, version: str | None = None):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Target directory not empty: {path}")
    ensure_dir(path)
    (path / "apps").mkdir()
    (path / SWAT_PLUGINS_DIRNAME).mkdir()
    (path / "tests").mkdir()
    (path / "README.md").write_text(f"# {name}\n\nGenerated by swatctl.\n", encoding="utf-8")
    tmp = git_clone(swat_repo, ref=version)
    lib_src = tmp / SWAT_LIB_DIRNAME
    dest_lib = path / SWAT_LIB_DIRNAME
    if lib_src.exists():
        safe_copytree(lib_src, dest_lib, overwrite=False)
    else:
        # fallback: copy entire repo into lib/
        safe_copytree(tmp, dest_lib, overwrite=False)
    example_app = path / "apps" / "demo"
    ensure_dir(example_app)
    write_file(example_app / "index.html", TEMPLATES["index.html"].format(title=f"{name} demo", libdir=SWAT_LIB_DIRNAME, name="app"), overwrite=True)
    write_file(example_app / "app.js", TEMPLATES["page.js"].format(name="app", title=f"{name} demo"), overwrite=True)
    cfg = {"swat_repo": swat_repo, "swat_ref": version or "HEAD"}
    (path / "swatctl.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    return True

def set_swat_version(project_root: Path, swat_repo: str, ref: str, backup: bool = True):
    root = Path(project_root)
    lib_dir = root / SWAT_LIB_DIRNAME
    tmp = git_clone(swat_repo, ref=ref)
    src_lib = tmp / SWAT_LIB_DIRNAME
    if not src_lib.exists():
        raise FileNotFoundError("swat repo did not contain lib/ at root")
    if backup and lib_dir.exists():
        bak = root / (SWAT_LIB_DIRNAME + ".bak")
        if bak.exists():
            shutil.rmtree(bak)
        shutil.move(str(lib_dir), str(bak))
    safe_copytree(src_lib, lib_dir, overwrite=True)
    cfg = root / "swatctl.json"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else {}
    except Exception:
        data = {}
    data.update({"swat_repo": swat_repo, "swat_ref": ref})
    cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    return True

def plugin_install(project_root: Path, plugin_repo: str, ref: str | None = None, plugin_subpath: str | None = None, overwrite: bool = False):
    root = Path(project_root)
    plugins_dir = root / SWAT_PLUGINS_DIRNAME
    ensure_dir(plugins_dir)
    tmp = git_clone(plugin_repo, ref=ref)
    candidates = []
    if plugin_subpath:
        p = tmp / plugin_subpath
        if p.exists():
            candidates.append(p)
    for nm in ("plugin.js", "index.js", "main.js"):
        p = tmp / nm
        if p.exists():
            candidates.append(p)
    p = tmp / "plugins"
    if p.exists() and p.is_dir():
        candidates.append(p)
    if not candidates:
        for f in tmp.iterdir():
            if f.suffix == ".js":
                candidates.append(f)
    if not candidates:
        shutil.rmtree(tmp, ignore_errors=True)
        raise FileNotFoundError("No plugin files found in the repo (tried plugin.js, index.js, plugins/). Use plugin_subpath to specify.")
    repo_name = Path(plugin_repo).stem
    dest = plugins_dir / repo_name
    if dest.exists():
        if not overwrite:
            raise FileExistsError(f"Plugin destination exists: {dest} (use overwrite=True)")
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for c in candidates:
        target = dest / c.name
        if c.is_dir():
            shutil.copytree(c, target)
        else:
            shutil.copy2(c, target)
    meta = {"source": plugin_repo, "ref": ref or "HEAD"}
    (dest / "swat-plugin.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    return dest

def plugin_set_version(project_root: Path, plugin_name: str, ref: str):
    root = Path(project_root)
    plugins_dir = root / SWAT_PLUGINS_DIRNAME
    dest = plugins_dir / plugin_name
    if not dest.exists():
        raise FileNotFoundError("Plugin not installed: " + str(dest))
    meta_file = dest / "swat-plugin.json"
    if not meta_file.exists():
        raise FileNotFoundError("Plugin metadata missing (swat-plugin.json).")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    repo = meta.get("source")
    if not repo:
        raise ValueError("Plugin metadata does not include source repo.")
    shutil.rmtree(dest)
    return plugin_install(project_root, repo, ref=ref, plugin_subpath=None, overwrite=True)

def show_info(project_root: Path):
    root = Path(project_root)
    info = {"project": str(root)}
    cfg = root / "swatctl.json"
    if cfg.exists():
        info["swatctl.json"] = json.loads(cfg.read_text(encoding="utf-8"))
    libdir = root / SWAT_LIB_DIRNAME
    info["lib_exists"] = libdir.exists()
    plugins = root / SWAT_PLUGINS_DIRNAME
    info["plugins"] = [p.name for p in plugins.iterdir()] if plugins.exists() else []
    apps = root / "apps"
    info["apps"] = [p.name for p in apps.iterdir()] if apps.exists() else []
    return info
```

### File: `swatctl/cli.py`

Console script entrypoint. Parses args and calls `core` functions.

```py
import argparse
import sys
from pathlib import Path
from . import core

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    p = argparse.ArgumentParser(prog="swatctl")
    sub = p.add_subparsers(dest="cmd")

    a_create = sub.add_parser("create-project")
    a_create.add_argument("path")
    a_create.add_argument("--name", default="swat-project")
    a_create.add_argument("--swat-repo", default="https://github.com/notesofcliff/swat.git")
    a_create.add_argument("--ref", default=None)

    a_page = sub.add_parser("create-page")
    a_page.add_argument("project")
    a_page.add_argument("pagename")
    a_page.add_argument("--title", default=None)
    a_page.add_argument("--overwrite", action="store_true")

    a_sv = sub.add_parser("swat-set-version")
    a_sv.add_argument("project")
    a_sv.add_argument("--repo", default="https://github.com/notesofcliff/swat.git")
    a_sv.add_argument("--ref", required=True)
    a_sv.add_argument("--no-backup", action="store_true")

    a_pi = sub.add_parser("plugin-install")
    a_pi.add_argument("project")
    a_pi.add_argument("repo")
    a_pi.add_argument("--ref", default=None)
    a_pi.add_argument("--subpath", default=None)
    a_pi.add_argument("--overwrite", action="store_true")

    a_psv = sub.add_parser("plugin-set-version")
    a_psv.add_argument("project")
    a_psv.add_argument("plugin_name")
    a_psv.add_argument("ref")

    a_info = sub.add_parser("info")
    a_info.add_argument("project", nargs="?", default=".")

    args = p.parse_args(argv)
    try:
        if args.cmd == "create-project":
            core.create_project(Path(args.path), args.name, args.swat_repo, version=args.ref)
        elif args.cmd == "create-page":
            core.create_page(Path(args.project), args.pagename, args.title or args.pagename, overwrite=args.overwrite)
        elif args.cmd == "swat-set-version":
            core.set_swat_version(Path(args.project), args.repo, args.ref, backup=not args.no_backup)
        elif args.cmd == "plugin-install":
            core.plugin_install(Path(args.project), args.repo, ref=args.ref, plugin_subpath=args.subpath, overwrite=args.overwrite)
        elif args.cmd == "plugin-set-version":
            core.plugin_set_version(Path(args.project), args.plugin_name, args.ref)
        elif args.cmd == "info":
            info = core.show_info(Path(args.project))
            print(info)
        else:
            p.print_help()
            return 2
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Directory: `tests/`

### File: `tests/conftest.py`

Provides helper to create a local git repo fixture for tests.

```py
import subprocess
import tempfile
from pathlib import Path
import os
import shutil
import stat
import sys

def init_local_git_repo_with_file(tmp_path, filename="plugin.js", content="export function install(swat){}"):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / filename).write_text(content, encoding="utf-8")
    # init git repo
    subprocess.check_call(["git", "init"], cwd=str(repo_dir))
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir))
    subprocess.check_call(["git", "config", "user.name", "Test User"], cwd=str(repo_dir))
    subprocess.check_call(["git", "add", filename], cwd=str(repo_dir))
    subprocess.check_call(["git", "commit", "-m", "initial commit"], cwd=str(repo_dir))
    # create a tag
    subprocess.check_call(["git", "tag", "v0.1.0"], cwd=str(repo_dir))
    return repo_dir
```

### File: `tests/test_core.py`

Covers create_project, plugin_install, plugin_set_version, set_swat_version but uses local repo fixtures.

```py
import tempfile
from pathlib import Path
import shutil
import json
import subprocess
import os
import pytest

from swatctl import core
from tests.conftest import init_local_git_repo_with_file

def test_create_project_and_set_version(tmp_path):
    # create a fake swat repo (contains lib/)
    swat_repo_dir = tmp_path / "swat_repo"
    swat_repo_dir.mkdir()
    lib_dir = swat_repo_dir / "lib"
    lib_dir.mkdir()
    (lib_dir / "swat-ui.css").write_text("/* css */", encoding="utf-8")
    subprocess.check_call(["git","init"], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","config","user.email","test@example.com"], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","config","user.name","Test User"], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","add","."], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","commit","-m","init"], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","tag","v0.1.0"], cwd=str(swat_repo_dir))

    project_dir = tmp_path / "proj"
    # create project using local repo path (file:// not required; git allows local path)
    core.create_project(project_dir, "TestProj", swat_repo=str(swat_repo_dir), version="v0.1.0")
    assert (project_dir / "lib" / "swat-ui.css").exists()
    info = core.show_info(project_dir)
    assert info["lib_exists"] is True
    # now change swat lib by tagging new commit
    (lib_dir / "newfile.js").write_text("// new", encoding="utf-8")
    subprocess.check_call(["git","add","."], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","commit","-m","add new"], cwd=str(swat_repo_dir))
    subprocess.check_call(["git","tag","v0.2.0"], cwd=str(swat_repo_dir))
    # set version to v0.2.0
    core.set_swat_version(project_dir, str(swat_repo_dir), "v0.2.0", backup=True)
    assert (project_dir / "lib" / "newfile.js").exists()
    # backup exists
    assert (project_dir / "lib.bak").exists()

def test_plugin_install_and_set_version(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "plugins").mkdir()
    # create a local plugin repo
    repo_dir = init_local_git_repo_with_file(tmp_path, filename="plugin.js", content="export function install(swat){ }")
    # install plugin from local repo
    dest = core.plugin_install(project_dir, str(repo_dir), ref="v0.1.0")
    assert dest.exists()
    assert (dest / "plugin.js").exists()
    meta = json.loads((dest / "swat-plugin.json").read_text(encoding="utf-8"))
    assert meta["ref"] == "v0.1.0"
    # re-tag at new version and set_version should re-install
    (repo_dir / "plugin.js").write_text("export function install(swat){ console.log('v2'); }", encoding="utf-8")
    subprocess.check_call(["git","add","plugin.js"], cwd=str(repo_dir))
    subprocess.check_call(["git","commit","-m","v2"], cwd=str(repo_dir))
    subprocess.check_call(["git","tag","v0.2.0"], cwd=str(repo_dir))
    core.plugin_set_version(project_dir, repo_dir.name, "v0.2.0")
    dest2 = project_dir / "plugins" / repo_dir.name
    assert dest2.exists()
    # ensure metadata updated
    meta2 = json.loads((dest2 / "swat-plugin.json").read_text(encoding="utf-8"))
    assert meta2["ref"] == "v0.2.0"
```

### File: `tests/test_utils.py`

Tests basic write_file and safe_copytree behavior.

```py
from pathlib import Path
import shutil
import pytest
from swatctl.core import write_file, ensure_dir, safe_copytree
import tempfile

def test_write_file(tmp_path):
    p = tmp_path / "a" / "b" / "f.txt"
    write_file(p, "hello")
    assert p.exists()
    with open(p, "r", encoding="utf-8") as fh:
        assert fh.read() == "hello"

def test_safe_copytree(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "x.txt").write_text("x")
    dst = tmp_path / "dst"
    safe_copytree(src, dst, overwrite=False)
    assert (dst / "x.txt").exists()
    # overwrite
    (src / "y.txt").write_text("y")
    safe_copytree(src, dst, overwrite=True)
    assert (dst / "y.txt").exists()
```

---

## File: `.github/workflows/ci.yml`

GitHub Actions workflow to run tests on pushes and PRs.

```yaml
name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[test]"
      - name: Run tests
        run: pytest -q
```

---

## Q&A Insights

Based on discussions about integration with the SWAT framework:

1. **Compatibility with existing SWAT implementation**:
   - `swatctl` works with the current SWAT repo as-is, assuming it exposes a `lib/` directory at the project root containing distributable framework files (e.g., `swat.js`, `swat-ui.css`, `storage.js`).
   - No internal changes to SWAT are required; `swatctl` clones the SWAT repo and copies `lib/` into new projects.
   - If `lib/` is missing, it falls back to copying the entire repo into `lib/`.

2. **Local development and GitHub independence**:
   - Fully functional locally before pushing to GitHub. Supports cloning from local filesystem paths (e.g., `../swat`), bare repos, or file URLs.
   - No network access needed for development; you can develop SWAT and `swatctl` side-by-side using local git repos.
   - Example: `swatctl create-project ./myapp --swat-repo ../swat --ref main`

3. **Repository structure and separation**:
   - `swatctl` is designed to live in its **own separate repository** from the SWAT framework.
   - This allows independent versioning, releases, and testing (e.g., CLI can iterate faster than the framework).
   - Recommended structure: `swat-framework/` (provides `lib/`), `swatctl/` (CLI tool), and optional `swat-plugins/` repos.
   - Avoids tangling versions and simplifies publishing (e.g., `swatctl` to PyPI, SWAT as a library).

---

## Notes, adjustments & next steps

1. **Tests create local git repos** — CI runner includes `git`, so cloning/checking-out is fine. The tests avoid network access by creating local repos in `tmp_path`, which `git clone` can accept as a local path.

2. **Packaging / Publishing** — After you verify locally, bump the version in `pyproject.toml` and publish to PyPI with `twine` if desired.

3. **Extra polish** (optional follow-ups I can produce on request):

   * Add more thorough unit tests and coverage.
   * Add integration tests for the CLI invoking `swatctl` via `subprocess`.
   * Add more features to the CLI (dry-run, interactive confirmation, checksum verification).
   * Add pre-commit / linters.
