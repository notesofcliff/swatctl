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