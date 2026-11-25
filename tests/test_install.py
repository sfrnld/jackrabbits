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
    env = {**os.environ, "SALES_STUDIO_SRC": f"file://{tgz}", "SALES_STUDIO_DIR": str(dest), "SALES_STUDIO_NO_RUN": "1", "SALES_STUDIO_TTY": "/dev/null"}
    run = lambda: subprocess.run(["bash", str(ROOT / "install.sh")], env=env, capture_output=True, text=True)
    r = run(); assert r.returncode == 0, r.stdout + r.stderr
    assert (dest / "Mulai.command").exists() and os.access(dest / "Mulai.command", os.X_OK)
    (dest / ".env").write_text("TELEGRAM_BOT_TOKEN=keep"); (dest / "state").mkdir(); (dest / "state" / "share.json").write_text("{}")
    (src / "VERSION").write_text("2")
    with tarfile.open(tgz, "w:gz") as t: t.add(src, arcname="Sales-Studio-main")
    r = run(); assert r.returncode == 0 and "Memperbarui" in r.stdout
    assert (dest / "VERSION").read_text() == "2" and (dest / ".env").read_text() == "TELEGRAM_BOT_TOKEN=keep" and (dest / "state" / "share.json").exists()

def test_installers_point_at_the_real_repo_and_have_no_placeholder():
    for f in ("install.sh", "install.bat", "README.md"):
        txt = (ROOT / f).read_text(); assert "OWNER/REPO" not in txt, f
    assert 'sfrnld/jackrabbits' in (ROOT / "install.sh").read_text() and "sfrnld/jackrabbits" in (ROOT / "install.bat").read_text()


def test_default_install_goes_into_a_subfolder_of_the_folder_where_it_runs(tmp_path):
    src = tmp_path / "Sales-Studio-main"; src.mkdir(); (src / "Mulai.command").write_text("#!/bin/bash\n")
    tgz = tmp_path / "repo.tar.gz"
    with tarfile.open(tgz, "w:gz") as t: t.add(src, arcname="Sales-Studio-main")
    here = tmp_path / "work"; here.mkdir()
    env = {k: v for k, v in os.environ.items() if k != "SALES_STUDIO_DIR"} | {"SALES_STUDIO_SRC": f"file://{tgz}", "SALES_STUDIO_NO_RUN": "1", "SALES_STUDIO_TTY": "/dev/null"}
    r = subprocess.run(["bash", str(ROOT / "install.sh")], env=env, cwd=here, capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr
    assert (here / "Sales-Studio" / "Mulai.command").exists()                          # ./Sales-Studio, not ~/Sales-Studio
    (here / "Sales-Studio" / "app").mkdir()                                            # running it INSIDE an app folder updates in place
    r = subprocess.run(["bash", str(ROOT / "install.sh")], env=env, cwd=here / "Sales-Studio", capture_output=True, text=True); assert r.returncode == 0
    assert not (here / "Sales-Studio" / "Sales-Studio").exists() and "Memperbarui" in r.stdout


def test_install_refuses_to_overwrite_a_git_clone(tmp_path):
    src = tmp_path / "Sales-Studio-main"; src.mkdir(); (src / "Mulai.command").write_text("#!/bin/bash\n")
    tgz = tmp_path / "repo.tar.gz"
    with tarfile.open(tgz, "w:gz") as t: t.add(src, arcname="Sales-Studio-main")
    clone = tmp_path / "clone"; (clone / ".git").mkdir(parents=True); (clone / "app").mkdir(); (clone / "Mulai.command").write_text("my local edit")
    env = {**os.environ, "SALES_STUDIO_SRC": f"file://{tgz}", "SALES_STUDIO_NO_RUN": "1", "SALES_STUDIO_TTY": "/dev/null"}; env.pop("SALES_STUDIO_DIR", None)
    r = subprocess.run(["bash", str(ROOT / "install.sh")], env=env, cwd=clone, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode != 0 and "clone Git" in r.stdout and (clone / "Mulai.command").read_text() == "my local edit"


def test_install_asks_where_to_install(tmp_path):
    src = tmp_path / "Sales-Studio-main"; src.mkdir(); (src / "Mulai.command").write_text("#!/bin/bash\n")
    tgz = tmp_path / "repo.tar.gz"
    with tarfile.open(tgz, "w:gz") as t: t.add(src, arcname="Sales-Studio-main")
    here, home, other = tmp_path / "work", tmp_path / "home", tmp_path / "elsewhere" / "App"; here.mkdir(); home.mkdir()
    def run(answers):
        ans = tmp_path / "answers.txt"; ans.write_text(answers)
        env = {k: v for k, v in os.environ.items() if k != "SALES_STUDIO_DIR"} | {"SALES_STUDIO_SRC": f"file://{tgz}", "SALES_STUDIO_NO_RUN": "1", "SALES_STUDIO_TTY": str(ans), "HOME": str(home)}
        r = subprocess.run(["bash", str(ROOT / "install.sh")], env=env, cwd=here, capture_output=True, text=True, stdin=subprocess.DEVNULL); assert r.returncode == 0, r.stdout + r.stderr; return r.stdout
    out = run("\n"); assert "Di mana Sales Studio dipasang?" in out and (here / "Sales-Studio" / "Mulai.command").exists()      # Enter = current folder
    run("2\n"); assert (home / "Sales-Studio" / "Mulai.command").exists()                                                      # user (home) folder
    run(f"3\n{other}\n"); assert (other / "Mulai.command").exists()                                                           # another folder, typed
    run("3\n~/Via-Tilde\n"); assert (home / "Via-Tilde" / "Mulai.command").exists()                                           # ~ is expanded
