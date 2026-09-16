"""deals.json'u GitHub'daki `data` dalına gönderir (online tablo için).

Dal her seferinde tek commit olarak üzerine yazılır (force push), böylece depoda
binlerce "fiyat güncellemesi" commit'i birikmez. GitHub Pages yeniden yayınlanmaz;
online sayfa veriyi doğrudan bu daldan okur.

Yerel çalışma kopyası Drive dışında durur: %LOCALAPPDATA%\\indirim\\yayin
Kimlik bilgisi Git Credential Manager'dan gelir (kurulumda bir kez giriş yapılır).
"""
import os
import shutil
import subprocess
from pathlib import Path

from .config import PUBLISH_BRANCH, PUBLISH_REPO

GIT_FALLBACK = r"C:\Program Files\Git\cmd\git.exe"


def _git_exe():
    exe = shutil.which("git") or (GIT_FALLBACK if Path(GIT_FALLBACK).exists() else None)
    if not exe:
        raise RuntimeError("git bulunamadı")
    return exe


def _git(repo_dir, *args, interactive=False):
    # Zamanlanmış görevde giriş penceresi açılıp takılı kalmasın; kurulumdaki ilk gönderimde açılabilsin
    env = dict(os.environ) if interactive else dict(os.environ, GCM_INTERACTIVE="never", GIT_TERMINAL_PROMPT="0")
    r = subprocess.run([_git_exe(), *args], cwd=repo_dir, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0:
        raise RuntimeError(f"git {args[0]}: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout


def publish(deals_file, local_dir, interactive=False):
    repo = Path(local_dir) / "yayin"
    if not (repo / ".git").exists():
        repo.mkdir(parents=True, exist_ok=True)
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "fiyat-botu")
        _git(repo, "config", "user.email", "furkanuzcan-svg@users.noreply.github.com")
        _git(repo, "remote", "add", "origin", PUBLISH_REPO)
    shutil.copyfile(deals_file, repo / "deals.json")
    # Her seferinde ebeveynsiz tek commit
    _git(repo, "add", "deals.json")
    tree = _git(repo, "write-tree").strip()
    commit = _git(repo, "commit-tree", tree, "-m", "Fiyat verisi").strip()
    _git(repo, "push", "-q", "-f", "origin", f"{commit}:refs/heads/{PUBLISH_BRANCH}", interactive=interactive)
    # Eski veri nesneleri yerelde birikmesin
    _git(repo, "prune")
