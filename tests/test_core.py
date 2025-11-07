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