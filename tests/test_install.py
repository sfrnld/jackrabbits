"""The curl installer: syntax check, and a full download+install from a local tarball (no network, nothing launched)."""
import os, subprocess, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_install_sh_is_valid_bash():
    assert subprocess.run(["bash", "-n", str(ROOT / "install.sh")]).returncode == 0

def test_install_sh_installs_and_updates_without_touching_user_data(tmp_path):
    src = tmp_path / "Sales-Studio-main"; src.mkdir()
    (src / "Mulai.command").write_text("#!/bin/bash\necho hi\n"); (src / "VERSION").write_text("1")
    tgz = tmp_path / "repo.tar.gz"
    with tarfile.open(tgz, "w:gz") as t: t.add(src, arcname="Sales-Studio-main")
    dest = tmp_path / "home" / "Sales-Studio"
    env = {**os.environ, "SALES_STUDIO_SRC": f"file://{tgz}", "SALES_STUDIO_DIR": str(dest), "SALES_STUDIO_NO_RUN": "1"}
    run = lambda: subprocess.run(["bash", str(ROOT / "install.sh")], env=env, capture_output=True, text=True)
    r = run(); assert r.returncode == 0, r.stdout + r.stderr
    assert (dest / "Mulai.command").exists() and os.access(dest / "Mulai.command", os.X_OK)
    (dest / ".env").write_text("TELEGRAM_BOT_TOKEN=keep"); (dest / "state").mkdir(); (dest / "state" / "share.json").write_text("{}")
    (src / "VERSION").write_text("2")
    with tarfile.open(tgz, "w:gz") as t: t.add(src, arcname="Sales-Studio-main")
    r = run(); assert r.returncode == 0 and "Memperbarui" in r.stdout
    assert (dest / "VERSION").read_text() == "2" and (dest / ".env").read_text() == "TELEGRAM_BOT_TOKEN=keep" and (dest / "state" / "share.json").exists()

def test_install_sh_refuses_unconfigured_repo(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("SALES_STUDIO")}
    r = subprocess.run(["bash", str(ROOT / "install.sh")], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode != 0 and "belum diisi" in r.stdout
