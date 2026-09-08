#!/usr/bin/env python3
"""EasyMod installer.

Uses a polished Tk GUI when Tk is available. On minimal Linux installs where
libtk is missing, it automatically falls back to a zero-dependency terminal
installer instead of crashing at import time.
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

APP_NAME = 'EasyMod'
HERE = Path(__file__).resolve().parent
DEFAULT = (Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'EasyMod'
           if os.name == 'nt' else Path.home() / '.local/share/EasyMod')


def tkinter_available():
    try:
        import tkinter  # noqa: F401
        return True
    except Exception:
        return False


def copy_payload(target: Path, status=lambda s: None):
    target = target.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    for src in HERE.iterdir():
        if src.name in ('__pycache__', target.name):
            continue
        dst = target / src.name
        status(f'Copying {src.name}...')
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    make_launcher(target)
    return target


def _linux_path_setup(bin_dir: Path):
    """Install a user-local PATH entry without requiring sudo."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    home = Path.home()
    exports = f'\n# EasyMod\nexport PATH="$PATH:{bin_dir}"\n'
    # .profile covers most login shells; also add to common interactive shells.
    for name in ('.profile', '.bashrc', '.zshrc'):
        rc = home / name
        try:
            text = rc.read_text(encoding='utf8') if rc.exists() else ''
            marker = '# EasyMod'
            if marker not in text:
                with rc.open('a', encoding='utf8') as f:
                    f.write(exports)
        except OSError:
            pass


def _linux_desktop_entry(target: Path, launcher: Path):
    apps = Path.home() / '.local/share/applications'
    apps.mkdir(parents=True, exist_ok=True)
    desktop = apps / 'easymod.desktop'
    desktop.write_text(
        '[Desktop Entry]\n'
        'Version=1.0\n'
        'Type=Application\n'
        'Name=EasyMod\n'
        'Comment=Visual Minecraft mod maker\n'
        f'Exec=\"{launcher}\" %U\n'
        f'Path={target}\n'
        'Terminal=false\n'
        'Categories=Development;Game;IDE;\n'
        'StartupNotify=true\n', encoding='utf8')
    desktop.chmod(0o644)
    # Also place a launcher on the user's Desktop when that folder exists.
    desktop_dir = Path.home() / 'Desktop'
    if desktop_dir.is_dir():
        desktop_copy = desktop_dir / 'EasyMod.desktop'
        try:
            shutil.copy2(desktop, desktop_copy)
            desktop_copy.chmod(0o755)
        except OSError:
            pass
    # Refresh desktop database if available; failure is harmless.
    try:
        subprocess.run(['update-desktop-database', str(apps)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        pass


def _windows_start_menu(target: Path, launcher: Path):
    start = Path(os.environ.get('APPDATA', Path.home())) / 'Microsoft/Windows/Start Menu/Programs'
    start.mkdir(parents=True, exist_ok=True)
    shortcut = start / 'EasyMod.lnk'
    # Use PowerShell's native WScript.Shell COM object so no extra Python package is needed.
    ps = (
        "$ws=New-Object -ComObject WScript.Shell;"
        f"$s=$ws.CreateShortcut('{shortcut}');"
        f"$s.TargetPath='{launcher}';"
        f"$s.WorkingDirectory='{target}';"
        f"$s.Description='EasyMod - Visual Minecraft mod maker';"
        "$s.Save()"
    )
    try:
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        # Mirror the same shortcut onto the Desktop.
        desktop = Path(os.environ.get('USERPROFILE', Path.home())) / 'Desktop'
        desktop.mkdir(parents=True, exist_ok=True)
        desktop_shortcut = desktop / 'EasyMod.lnk'
        ps2 = ps.replace(str(shortcut), str(desktop_shortcut))
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps2],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        # A .bat in the Start Menu is still useful if PowerShell is unavailable.
        shortcut.with_suffix('.bat').write_text(
            '@echo off\n'
            f'call "{launcher}" %*\n', encoding='utf8')


def _windows_user_path(bin_dir: Path):
    """Add EasyMod's install directory to the current user's PATH."""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0,
                             winreg.KEY_READ | winreg.KEY_WRITE)
        try:
            try:
                old, typ = winreg.QueryValueEx(key, 'Path')
            except FileNotFoundError:
                old, typ = '', winreg.REG_EXPAND_SZ
            parts = [x for x in old.split(';') if x]
            value = str(bin_dir)
            if value.lower() not in {x.lower() for x in parts}:
                parts.append(value)
                winreg.SetValueEx(key, 'Path', 0, typ, ';'.join(parts))
        finally:
            winreg.CloseKey(key)
    except Exception:
        # Best-effort fallback; installer remains usable without PATH changes.
        try:
            subprocess.run(['setx', 'PATH', f'%PATH%;{bin_dir}'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except OSError:
            pass


def make_launcher(target: Path):
    app = target / 'easymod_app.py'
    if os.name == 'nt':
        launcher = target / 'EasyMod.bat'
        launcher.write_text(
            '@echo off\n'
            f'py "{app}" %*\n', encoding='utf8')
        # The install directory itself is on PATH, so `EasyMod` works in a new shell.
        _windows_user_path(target)
        _windows_start_menu(target, launcher)
    else:
        # Keep the real application files in the chosen install directory, but expose
        # a stable `easymod` command from ~/.local/bin (no sudo required).
        bin_dir = Path.home() / '.local/bin'
        _linux_path_setup(bin_dir)
        launcher = bin_dir / 'easymod'
        launcher.write_text(
            '#!/bin/sh\n'
            f'exec python3 "{app}" "$@"\n', encoding='utf8')
        launcher.chmod(0o755)
        # Capitalized alias for convenience too.
        alias = bin_dir / 'EasyMod'
        try:
            if alias.exists() or alias.is_symlink():
                alias.unlink()
            alias.symlink_to(launcher)
        except OSError:
            alias.write_text(f'#!/bin/sh\nexec "{launcher}" "$@"\n', encoding='utf8')
            alias.chmod(0o755)
        _linux_desktop_entry(target, launcher)


def launch(target: Path):
    app = target / 'easymod_app.py'
    subprocess.Popen([sys.executable, str(app)], cwd=target)


def linux_tk_help():
    """Return a useful command for the user's distro without changing the system."""
    try:
        with open('/etc/os-release', encoding='utf8') as f:
            data = f.read().lower()
    except Exception:
        data = ''
    if 'debian' in data or 'ubuntu' in data or 'mint' in data or 'pop!_os' in data:
        return 'sudo apt install python3-tk'
    if 'fedora' in data:
        return 'sudo dnf install python3-tkinter'
    if 'arch' in data or 'manjaro' in data:
        return 'sudo pacman -S tk'
    if 'opensuse' in data or 'suse' in data:
        return 'sudo zypper install python3-tk'
    return 'Install your distro\'s Python Tk package (usually python3-tk / python3-tkinter).'


def cli_install():
    # ANSI UI deliberately uses no third-party modules and no Tk.
    reset = '\033[0m'
    purple = '\033[95m'
    cyan = '\033[96m'
    green = '\033[92m'
    yellow = '\033[93m'
    dim = '\033[2m'
    print('\033[2J\033[H', end='')
    print(f'{purple}╭────────────────────────────────────────────────────╮{reset}')
    print(f'{purple}│{reset}  {cyan}EASYMOD{reset}  {dim}Minecraft modding without the boilerplate{reset}  {purple}│{reset}')
    print(f'{purple}╰────────────────────────────────────────────────────╯{reset}\n')
    if os.name != 'nt' and not tkinter_available():
        print(f'{yellow}⚠ Tkinter is not installed on this Python.{reset}')
        print('EasyMod itself uses Tk for its desktop editor.')
        print(f'After installation, run: {cyan}{linux_tk_help()}{reset}\n')

    default = str(DEFAULT)
    try:
        raw = input(f'Install location [{default}]: ').strip()
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled.')
        return 130
    target = Path(raw or default).expanduser()

    print(f'\n{cyan}Installing EasyMod...{reset}')
    try:
        copy_payload(target, lambda s: print(f'  {dim}›{reset} {s}'))
        print(f'  {green}✓{reset} Files installed')
        print(f'  {green}✓{reset} PATH command installed: EasyMod / easymod')
        if os.name != 'nt':
            print(f'  {green}✓{reset} Desktop + application-menu entry created')
        else:
            print(f'  {green}✓{reset} Start Menu shortcut created')
    except Exception as e:
        print(f'\n\033[91m✗ Installation failed: {e}{reset}')
        return 1

    print(f'\n{green}EasyMod is installed.{reset}')
    print(f'Location: {target}')
    if os.name != 'nt':
        print(f'Command: {cyan}easymod{reset}  (open a new terminal if PATH was just updated)')
    else:
        print(f'Command: {cyan}EasyMod{reset}  (open a new terminal if PATH was just updated)')
    if os.name != 'nt' and not tkinter_available():
        print(f'\n{yellow}One dependency is still needed:{reset} Tkinter')
        print(f'Run: {cyan}{linux_tk_help()}{reset}')
        print(f'Then launch: {cyan}{target / "EasyMod"}{reset}')
        return 0

    try:
        answer = input('\nLaunch EasyMod now? [Y/n]: ').strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = 'n'
    if answer in ('', 'y', 'yes'):
        try:
            launch(target)
        except Exception as e:
            print(f'Could not launch automatically: {e}')
    return 0


if tkinter_available():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    class Installer(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title('EasyMod Setup')
            self.geometry('760x520')
            self.resizable(False, False)
            self.configure(bg='#0b0e13')
            self.target = tk.StringVar(value=str(DEFAULT))
            self.status = tk.StringVar(value='Ready to install EasyMod.')
            self._style()
            self.build()

        def _style(self):
            st = ttk.Style(self)
            st.theme_use('clam')
            st.configure('TProgressbar', troughcolor='#171b23', background='#6c63ff',
                         bordercolor='#171b23', lightcolor='#6c63ff', darkcolor='#6c63ff')

        def build(self):
            tk.Label(self, text='EASYMOD', font=('TkDefaultFont', 30, 'bold'),
                     fg='#ffffff', bg='#0b0e13').pack(anchor='w', padx=42, pady=(34, 0))
            tk.Label(self, text='Minecraft modding, without the boilerplate.',
                     font=('TkDefaultFont', 12), fg='#8e96a8', bg='#0b0e13').pack(
                         anchor='w', padx=45, pady=(0, 28))
            card = tk.Frame(self, bg='#151922')
            card.pack(fill='x', padx=40, pady=4)
            tk.Label(card, text='Install location', font=('TkDefaultFont', 11, 'bold'),
                     fg='white', bg='#151922').pack(anchor='w', padx=20, pady=(18, 8))
            row = tk.Frame(card, bg='#151922')
            row.pack(fill='x', padx=20, pady=(0, 18))
            tk.Entry(row, textvariable=self.target, bg='#0e1117', fg='white',
                     insertbackground='white', relief='flat').pack(side='left', fill='x',
                                                                   expand=True, ipady=9)
            tk.Button(row, text='Browse', command=self.browse, bg='#292f3d', fg='white',
                      relief='flat').pack(side='left', padx=(8, 0), ipady=7)
            info = tk.Frame(self, bg='#0b0e13')
            info.pack(fill='x', padx=42, pady=18)
            for title, desc in [
                ('✓ No pip dependencies', 'EasyMod uses Python standard library + Tk.'),
                ('✓ Auto toolchains', 'Gradle and matching Java are downloaded when needed.'),
                ('✓ Version aware', 'Forge, Fabric and NeoForge are selected per Minecraft version.'),
            ]:
                f = tk.Frame(info, bg='#0b0e13')
                f.pack(anchor='w', pady=5)
                tk.Label(f, text=title, font=('TkDefaultFont', 10, 'bold'),
                         fg='#dce1ea', bg='#0b0e13').pack(anchor='w')
                tk.Label(f, text=desc, fg='#737c8e', bg='#0b0e13').pack(anchor='w')
            self.pb = ttk.Progressbar(self, mode='indeterminate')
            self.pb.pack(fill='x', padx=42, pady=(8, 5))
            tk.Label(self, textvariable=self.status, fg='#8e96a8', bg='#0b0e13').pack(
                anchor='w', padx=42)
            bottom = tk.Frame(self, bg='#0b0e13')
            bottom.pack(fill='x', padx=42, pady=22)
            tk.Button(bottom, text='Install EasyMod', command=self.install, bg='#6c63ff',
                      fg='white', relief='flat', font=('TkDefaultFont', 11, 'bold'),
                      padx=24, pady=10).pack(side='right')
            tk.Button(bottom, text='Cancel', command=self.destroy, bg='#202530',
                      fg='white', relief='flat', padx=18, pady=10).pack(side='right', padx=8)

        def browse(self):
            p = filedialog.askdirectory(initialdir=str(Path(self.target.get()).parent))
            if p:
                self.target.set(str(Path(p) / 'EasyMod'))

        def install(self):
            target = Path(self.target.get()).expanduser()
            self.pb.start(12)
            self.status.set('Installing files...')
            self.update_idletasks()
            try:
                copy_payload(target, lambda s: self.status.set(s))
                self.status.set('Installation complete.')
                self.pb.stop()
                if messagebox.askyesno('EasyMod installed', 'EasyMod is ready. Launch it now?'):
                    launch(target)
                self.destroy()
            except Exception as e:
                self.pb.stop()
                self.status.set('Installation failed.')
                messagebox.showerror('Installation failed', str(e))


if __name__ == '__main__':
    if tkinter_available():
        Installer().mainloop()
    else:
        raise SystemExit(cli_install())
