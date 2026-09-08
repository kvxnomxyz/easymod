#!/usr/bin/env python3
"""Build EasyMod 1.0 release artifacts.

- Detects Linux distro and installs the system packages needed to build/run Tk.
- Creates an isolated .venv and installs PyInstaller with pip.
- Builds a one-file bootstrap installer.
- Creates EasyMod-assets.zip for the GitHub release.

PyInstaller is platform-native: build the Linux executable on Linux and the
Windows .exe on Windows. It is not a cross-compiler.
"""
from __future__ import annotations
import os, platform, shutil, subprocess, sys, venv, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUT = ROOT / "dist"
VENV = ROOT / ".build-venv"


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd)))
    subprocess.check_call(cmd, **kw)


def distro():
    if platform.system() != "Linux": return platform.system().lower()
    data = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k,v=line.split("=",1); data[k]=v.strip('"')
    except OSError: pass
    return data.get("ID", "linux").lower()


def maybe_install_system_deps():
    if platform.system() != "Linux": return
    d = distro()
    print(f"Detected Linux distro: {d}")
    cmds = {
      "ubuntu": ["sudo","apt-get","update"], "debian":["sudo","apt-get","update"],
      "linuxmint":["sudo","apt-get","update"], "pop":["sudo","apt-get","update"],
    }
    if d in cmds:
        run(cmds[d])
        run(["sudo","apt-get","install","-y","python3-tk","python3-venv","python3-pip","p7zip-full"])
    elif d in {"fedora","rhel","centos"}:
        run(["sudo","dnf","install","-y","python3-tkinter","python3-pip","python3-virtualenv","p7zip"])
    elif d in {"arch","manjaro","endeavouros"}:
        run(["sudo","pacman","-Sy","--needed","--noconfirm","tk","python-pip","p7zip"])
    elif d in {"opensuse","opensuse-tumbleweed","opensuse-leap","sles"}:
        run(["sudo","zypper","--non-interactive","install","python3-tk","python3-pip","python3-virtualenv","p7zip"])
    else:
        print("Unknown distro; install Python Tk/venv/pip and 7z manually if needed.")


def python_exe():
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

def main():
    maybe_install_system_deps()
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])
    py = python_exe()
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "pyinstaller"])
    OUT.mkdir(exist_ok=True)

    payload = OUT / "EasyMod-assets.zip"
    files = [p for p in SRC.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files: z.write(p, p.relative_to(SRC))
    print("Created", payload)

    name = "EasyMod-Installer.exe" if os.name == "nt" else "EasyMod-Installer"
    run([str(py), "-m", "PyInstaller", "--onefile", "--clean", "--noconfirm",
         "--name", Path(name).stem, str(ROOT / "tools" / "github_installer.py")], cwd=ROOT)
    built = ROOT / "dist" / name
    if built.exists():
        print("\nREADY:", built)
    else:
        raise SystemExit("PyInstaller did not produce the expected installer")
    print("\nUpload BOTH files to GitHub release tag v1.0:")
    print(" -", payload)
    print(" -", built)

if __name__ == "__main__": main()
