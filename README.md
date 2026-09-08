# EasyMod 1.0

> **Scratch-style visual programming for Minecraft modding.**
>
> Build Minecraft mods by connecting visual blocks instead of writing every Java event and API call by hand.

EasyMod is a desktop Minecraft mod-making environment designed around one idea:

**Scratch + MCreator-style workflows + real Minecraft mod toolchains.**

It provides a visual block workspace, project management, generated source code, build integration, error-to-block mapping, and automatic toolchain setup.

---

## Features

### Visual mod programming

EasyMod provides a Scratch-like block workspace with categories for:

- Events
- Control flow
- Variables
- Values
- Math
- Logic
- Players
- World actions
- Advanced/custom Java

Blocks can be placed into the workspace, connected into workflows, edited through their properties, and generated into source code.

### Minecraft version selection

EasyMod is designed around the Minecraft release range from **1.7.10 through 26.2**.

The version selector can synchronize Minecraft releases from Mojang's official version manifest rather than relying on a hard-coded list.

Because Minecraft's internals and mappings change substantially between releases, EasyMod does **not** assume that one generated implementation works unchanged for every version. The selected Minecraft version and loader determine the project/toolchain configuration.

### Loader support

EasyMod supports the major loader families used by the project templates:

- **Forge**
- **Fabric**
- **NeoForge**

Loader availability is version-dependent. For example, Fabric's official release support begins at 1.14, while Forge is available for much older Minecraft versions such as 1.7.10.

### Automatic toolchain setup

EasyMod is designed to obtain the tools required by the selected project, including:

- Java/JDK versions
- Gradle distributions
- Fabric Loader metadata
- Fabric API metadata
- Forge MDKs
- NeoForge MDKs
- Other version-specific build information

Downloaded toolchains are cached locally so they do not have to be downloaded for every project.

The normal cache is located under:

```text
~/.easymod/
```

The exact project/toolchain layout can change between releases.

---

# Installation

There are two installation paths:

1. **EasyMod's normal desktop installer**
2. **The release bootstrap/build installer**

The normal installer is for users who already have the EasyMod source/application payload.

The release bootstrap installer is intended for distributing EasyMod through GitHub Releases.

---

## Linux / macOS bootstrap installer

Run:

```bash
chmod +x install.sh
./install.sh
```

The installer detects the host operating system and architecture.

On supported Linux distributions it can install/check native build prerequisites and then creates a Python build environment.

It downloads the EasyMod release payload directly from GitHub, installs the build dependencies, and compiles EasyMod as a **single-file executable** using Nuitka.

The default release asset URL is:

```text
https://github.com/kvxnomxyz/easymod/releases/download/v1.0/EasyMod-assets.zip
```

You can override the repository and release version:

```bash
EASYMOD_REPO=kvxnomxyz/easymod EASYMOD_VERSION=1.0 ./install.sh
```

### Linux PATH installation

After a successful build, EasyMod is installed for the current user at:

```text
~/.local/bin/easymod
```

The installer also adds `~/.local/bin` to the user's shell startup files when necessary.

Open a new terminal and run:

```bash
easymod
```

No root installation is required for the EasyMod application itself.

### Linux desktop/menu integration

The installer creates an application-menu desktop entry at:

```text
~/.local/share/applications/easymod.desktop
```

If a `~/Desktop` directory exists, a desktop launcher is also created.

---

## Windows

The same bootstrap script can be used from a Bash-compatible environment such as Git Bash/MSYS2:

```bash
./install.sh
```

There is also a Windows batch entry point when using the normal EasyMod installer:

```bat
install_windows.bat
```

The release builder uses Nuitka and the native Microsoft C/C++ build toolchain to create a Windows executable.

The installed executable is placed in the current user's EasyMod application directory and the installer adds that directory to the user's PATH.

A new terminal is required before the updated PATH is visible to that terminal.

---

# One-file executable

EasyMod 1.0 uses **Nuitka onefile mode** for the release executable.

The intended result is:

```text
EasyMod
```

on Linux/macOS, or:

```text
EasyMod.exe
```

on Windows.

The executable contains the Python application and its Python runtime/dependencies in one distributable executable.

## Important: one-file vs static linking

A Nuitka one-file executable is **not the same thing as a completely statically linked ELF/PE binary**.

EasyMod uses Tk/Tcl for its desktop interface, and operating-system GUI/runtime components can still depend on host libraries. Fully static Tk applications are not a portable target across Linux distributions.

Therefore EasyMod's release target is:

> **one distributable executable containing the Python application/runtime**, not a promise of a literally static binary with zero dynamic system dependencies.

This distinction is intentional and avoids claiming portability that the operating system cannot guarantee.

---

# Building a release

The release installer is designed to build the native executable on the platform where it is executed.

Run:

```bash
./install.sh
```

The script:

1. Detects the operating system.
2. Detects the CPU architecture.
3. Locates Python 3.
4. Installs/checks native compilation prerequisites.
5. Downloads the EasyMod release payload from GitHub.
6. Creates an isolated Python virtual environment.
7. Installs Nuitka and its build dependencies.
8. Enables Tk support for the GUI build.
9. Compiles EasyMod with Nuitka onefile mode.
10. Installs the resulting executable for the current user.
11. Creates PATH and desktop/menu integration where supported.

## Cross-compilation

The build should be performed on the target operating system.

For example:

```text
Linux machine   -> Linux executable
Windows machine -> Windows executable
macOS machine   -> macOS executable
```

Nuitka is not a general-purpose cross-compiler, so building a Windows binary from Linux is not the supported release workflow.

---

# GitHub Releases

The EasyMod 1.0 release is intended for:

```text
https://github.com/kvxnomxyz/easymod
```

Create a GitHub release named/tagged:

```text
v1.0
```

The bootstrap installer expects the main downloadable application payload at:

```text
EasyMod-assets.zip
```

Therefore the release should contain an asset with exactly that name.

Recommended release assets:

```text
EasyMod-assets.zip
EasyMod-assets.zip.sha256
EasyMod-Installer
EasyMod-Installer.exe
package.7z
```

The final native installer binaries should be built on their respective target platforms.

---

# EasyMod project workflow

A typical project workflow is:

```text
Create Project
     |
     v
Select Minecraft Version
     |
     v
Select Loader
     |
     v
EasyMod resolves toolchain
     |
     v
Build visual block logic
     |
     v
Generate source code
     |
     v
Run Gradle build
     |
     +---- success ----> Mod JAR
     |
     +---- error ------> Map compiler line to block
                              |
                              v
                         Block flashes red
```

---

# Error mapping

One of EasyMod's important design features is the connection between generated source and visual blocks.

During source generation, EasyMod records a source map similar to:

```text
Generated Java line 42 -> Visual block UUID abc123
Generated Java line 43 -> Visual block UUID abc123
Generated Java line 57 -> Visual block UUID def456
```

When a compiler/build diagnostic contains a source file and line number, EasyMod can attempt to resolve that line through the source map.

When a visual block can be identified, the block is marked as broken and can flash red in the editor.

This turns a compiler error such as:

```text
EasyModGenerated.java:57: error: cannot find symbol
```

into a visual-editor error pointing at the block responsible for the generated code.

### Limitations

Not every Minecraft/build error can be perfectly attributed to one block. Examples include:

- Gradle configuration errors
- Dependency resolution failures
- Mapping conflicts
- Loader setup failures
- Errors caused by external/custom Java
- Errors produced by generated code whose cause spans multiple blocks

EasyMod therefore treats block mapping as a best-effort diagnostic system rather than claiming perfect compiler attribution.

---

# Toolchain management

Minecraft modding has changed significantly over time. EasyMod's toolchain layer is intended to keep version-specific setup outside the visual programming layer.

Conceptually:

```text
Visual Blocks
     |
     v
EasyMod IR
     |
     v
Version/Loader Adapter
     |
     +---- Fabric
     +---- Forge
     +---- NeoForge
     |
     v
Generated Project
     |
     v
JDK + Gradle + Loader/MDK
     |
     v
Minecraft Mod JAR
```

This allows the same visual block concept to be translated differently depending on the selected Minecraft version.

---

# Minecraft compatibility notes

Minecraft versions are **not interchangeable**.

A mod targeting 1.7.10 has fundamentally different APIs, mappings, Gradle tooling, and Java requirements from a modern 26.x project.

For that reason:

- Do not copy generated source between unrelated Minecraft versions.
- Do not assume a Fabric block implementation exists on Forge.
- Do not assume a Forge API method exists on NeoForge.
- Do not assume mappings have the same names across versions.
- Let EasyMod regenerate the project after changing Minecraft versions or loaders.

The version-aware architecture exists specifically to handle these differences.

---

# Fabric

Fabric support is version-aware.

Fabric's official ecosystem supports Minecraft releases beginning with 1.14. Older Minecraft releases should use a compatible legacy loader/toolchain rather than being incorrectly presented as modern Fabric projects.

Modern Minecraft releases also have different mappings/tooling requirements from older releases. EasyMod therefore resolves the selected version's loader/build metadata instead of assuming one universal Fabric configuration.

---

# Forge

Forge is especially important for legacy Minecraft versions.

For example, Minecraft 1.7.10 uses the historical Forge toolchain and cannot be treated like a modern Forge project.

EasyMod's project generation therefore keeps legacy and modern Forge setup separate.

---

# NeoForge

NeoForge is available only for Minecraft branches where the NeoForge ecosystem exists.

It should not be presented as an available loader for arbitrary old Minecraft versions.

The version selector is intended to hide or reject incompatible loader/version combinations.

---

# Java and Gradle

Different Minecraft versions require different Java and Gradle environments.

EasyMod's toolchain manager is intended to:

- detect an existing compatible JDK;
- download/cache a required JDK when needed;
- select a compatible Gradle distribution;
- download/cache Gradle;
- reuse cached installations for future projects.

The application should prefer a project-specific resolved toolchain over assuming that the user's system Java/Gradle version is correct.

---

# Cache locations

EasyMod uses a local cache so large toolchains do not need to be downloaded repeatedly.

The main EasyMod cache is normally:

```text
~/.easymod/
```

The release builder additionally uses a temporary/cache area similar to:

```text
~/.cache/easymod-builder/
```

Exact paths can differ by platform and environment variables.

---

# Troubleshooting

## `ImportError: libtk8.6.so`

On Debian/Ubuntu:

```bash
sudo apt install python3-tk
```

On Fedora/RHEL:

```bash
sudo dnf install python3-tkinter
```

On Arch:

```bash
sudo pacman -S tk
```

The bootstrap installer attempts to detect/install the required GUI dependency when possible.

---

## `python3: command not found`

Install Python 3.10 or newer using your distribution's package manager or the official Python distribution for your operating system, then rerun the installer.

---

## Compiler not found

On Debian/Ubuntu:

```bash
sudo apt install build-essential
```

On Fedora:

```bash
sudo dnf groupinstall 'Development Tools'
```

On Arch:

```bash
sudo pacman -S base-devel
```

On openSUSE:

```bash
sudo zypper install gcc gcc-c++ make
```

On Windows, install Microsoft Visual C++ Build Tools with the C++ workload.

---

## PATH command is not found after installation

Open a new terminal.

For a current Linux shell, you can also run:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then:

```bash
easymod
```

---

## GitHub asset cannot be downloaded

Check that the release exists and that the expected asset has been uploaded.

The default location is:

```text
https://github.com/kvxnomxyz/easymod/releases/download/v1.0/EasyMod-assets.zip
```

If you are using a fork or another release, set:

```bash
EASYMOD_REPO=OWNER/REPOSITORY
EASYMOD_VERSION=VERSION
```

before running the installer.

---

## Build fails while installing Nuitka

Check:

```bash
python3 --version
python3 -m pip --version
```

The builder creates a private virtual environment and installs Nuitka there so the user's system Python packages do not have to be modified.

---

## Tk GUI build fails with Nuitka

Make sure Tkinter works in the Python interpreter used for the build:

```bash
python3 -c 'import tkinter; print(tkinter.TkVersion)'
```

If that fails on Linux, install the distribution's Tk package and rerun the builder.

---

# Security and permissions

The bootstrap installer downloads executable/build content from GitHub and may install native build dependencies through the operating system package manager.

Review scripts before running them if you are using a fork or an untrusted release.

The normal EasyMod application installation is designed to be per-user. Native dependency installation may require administrator/root privileges because those packages belong to the operating system.

Do not run the installer as root unless you specifically understand the consequences.

---

# Project files

A typical EasyMod project contains the visual project definition and generated Minecraft project files.

The application maintains the visual representation separately from generated source so that changing the selected Minecraft version can regenerate the appropriate platform project.

Generated source should be treated as build output unless you intentionally use the custom-Java/advanced features.

---

# Development

EasyMod is a Python desktop application.

The main editor entry point is:

```text
easymod_app.py
```

The normal installer is:

```text
EasyModInstaller.py
```

The release bootstrap/build script is:

```text
install.sh
```

The project is intended to remain cross-platform at the application layer, with platform-specific work isolated to the installer and native build/toolchain layer.

---

# Release structure

A GitHub release can be organized approximately as:

```text
EasyMod v1.0
|
+-- EasyMod-assets.zip
+-- EasyMod-assets.zip.sha256
+-- EasyMod-Installer
+-- EasyMod-Installer.exe
+-- package.7z
```

The bootstrap installer downloads the release payload instead of requiring the entire application source to be embedded inside the bootstrap executable/script.

This keeps the bootstrap small and allows future releases to replace the GitHub-hosted payload without changing the general installation mechanism.

---

# License

Add the project's chosen license here before publishing the repository publicly.

If this repository contains third-party libraries, APIs, templates, or generated metadata, keep their respective licenses/notices intact.

---

# Credits and upstream projects

EasyMod builds on the Minecraft modding ecosystem and relies on upstream tooling such as:

- Minecraft / Mojang version metadata
- Fabric / Fabric Loader / Fabric Loom
- Forge / ForgeGradle and related tooling
- NeoForge
- Gradle
- Java / Eclipse Temurin where used for downloaded JDKs
- Python
- Tk/Tcl
- Nuitka

EasyMod is a separate project and is not an official Minecraft, Mojang, Fabric, Forge, or NeoForge product.

---

# Disclaimer

Minecraft is a trademark of Mojang Studios / Microsoft.

EasyMod is an independent mod-development tool.

Minecraft's APIs, mappings, loaders, build systems, and required Java versions can change between releases. Although EasyMod is designed for broad version coverage, **individual visual blocks may require version-specific implementations or may not be available for every Minecraft/loader combination**.

Always test the generated mod against the exact Minecraft version and loader you intend to distribute.

---

# Quick start

For a user with a published EasyMod 1.0 GitHub release:

```bash
curl -fL https://github.com/kvxnomxyz/easymod/releases/download/v1.0/EasyMod-assets.zip -o EasyMod-assets.zip
```

For the bootstrap installer:

```bash
chmod +x install.sh
./install.sh
```

After installation:

```bash
easymod
```

Then:

1. Create a project.
2. Choose the Minecraft version.
3. Choose Forge, Fabric, or NeoForge when supported.
4. Let EasyMod resolve the toolchain.
5. Add visual blocks.
6. Generate/build the project.
7. Fix any blocks highlighted by build diagnostics.
8. Export the resulting mod when the build succeeds.

**Welcome to EasyMod.**
