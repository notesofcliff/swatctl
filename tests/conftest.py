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