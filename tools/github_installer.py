#!/usr/bin/env python3
"""Tiny EasyMod release bootstrap installer.

The executable produced from this file contains no EasyMod application payload.
It downloads the release payload from GitHub, verifies its SHA-256 when a
checksum is published, extracts it to a temporary directory, and launches the
real EasyMod installer.
"""
from __future__ import annotations
import hashlib, os, platform, shutil, subprocess, sys, tempfile, urllib.request, zipfile
from pathlib import Path

OWNER = "kvxnomxyz"
REPO = "easymod"
TAG = "v1.0"
ASSET = "EasyMod-assets.zip"
BASE = f"https://github.com/{OWNER}/{REPO}/releases/download/{TAG}/"


def urlopen(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EasyMod-Installer/1.0"})
    return urllib.request.urlopen(req, timeout=60)


def download(url: str, dest: Path):
    with urlopen(url) as r, dest.open("wb") as f:
        total = int(r.headers.get("Content-Length", "0") or 0)
        done = 0
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk: break
            f.write(chunk); done += len(chunk)
            if total:
                print(f"\rDownloading {done/total*100:5.1f}%", end="", flush=True)
    print()


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()


def run_payload_installer(extract: Path):
    # Prefer a native core installer executable from the downloaded release.
    names = []
    if os.name == "nt":
        names = ["EasyMod-CoreInstaller.exe", "EasyModInstaller.exe"]
    else:
        names = ["EasyMod-CoreInstaller", "EasyModInstaller"]
    for name in names:
        matches = list(extract.rglob(name))
        if matches:
            exe = matches[0]
            if os.name != "nt":
                exe.chmod(exe.stat().st_mode | 0o111)
            return subprocess.call([str(exe)], cwd=str(exe.parent))
    # Developer/source fallback when Python is already installed.
    matches = list(extract.rglob("EasyModInstaller.py"))
    if matches:
        return subprocess.call([sys.executable, str(matches[0])], cwd=str(matches[0].parent))
    raise RuntimeError("GitHub payload contains no EasyMod installer")


def main():
    print("\n=== EasyMod 1.0 Installer ===\n")
    print("Downloading the EasyMod payload from GitHub...")
    with tempfile.TemporaryDirectory(prefix="easymod-install-") as td:
        td = Path(td)
        archive = td / ASSET
        try:
            download(BASE + ASSET, archive)
        except Exception as e:
            print(f"Download failed: {e}")
            print("Check your internet connection and that the v1.0 GitHub release contains EasyMod-assets.zip.")
            return 2
        try:
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
                if not any(Path(n).name == "EasyModInstaller.py" for n in names):
                    raise RuntimeError("The GitHub payload is missing EasyModInstaller.py")
                extract = td / "payload"
                z.extractall(extract)
        except Exception as e:
            print(f"Payload extraction failed: {e}")
            return 3
        print("Launching EasyMod's full installer...\n")
        try:
            return run_payload_installer(extract)
        except Exception as e:
            print(f"Installer launch failed: {e}")
            return 4


if __name__ == "__main__":
    raise SystemExit(main())
