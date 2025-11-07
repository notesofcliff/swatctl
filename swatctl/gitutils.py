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