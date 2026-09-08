# EasyMod 1.1

EasyMod is a Scratch-style visual Minecraft mod maker with automatic version-aware toolchains.

## Minecraft versions

The version picker syncs directly with Mojang's official release manifest, so it can expose the complete release history available there, including legacy releases through current releases such as 26.2.

Loader availability is version-aware:
- Forge: legacy and modern Forge releases, resolved from Forge metadata; official MDKs are downloaded per selected version.
- Fabric: official release support from 1.14+, with version-specific Fabric Loader metadata. Fabric's current 26.2 tooling uses the non-remapping Loom line and Gradle 9.5.1.
- NeoForge: version-aware from its supported Minecraft branch onward; the selected NeoForge MDK is downloaded from the official Maven repository.

Fabric's official documentation notes that Fabric releases start at 1.14, while Loom itself is designed to work across Minecraft versions. Minecraft 26.1+ uses the non-remapping Loom plugin because the game is no longer obfuscated. 

## Automatic toolchains

EasyMod now bootstraps:
- matching Gradle distributions from `services.gradle.org`
- Eclipse Temurin JDKs from the Adoptium API when the required Java version is not already cached
- Forge and NeoForge MDKs for the selected version
- Fabric Loader/API metadata when available

Everything is cached under `~/.easymod` so subsequent projects reuse the downloaded toolchains.

## Custom installer

Run:
- Linux: `./install_linux.sh`
- Windows: `install_windows.bat`
- Directly: `python3 EasyModInstaller.py`

The installer has a dark custom UI, selectable install location, launcher creation, Start Menu/Desktop integration where available, and a one-click launch option.

## Run the editor

Linux: `./run_linux.sh`
Windows: `run_windows.bat`

## Important compatibility note

Minecraft's modding APIs are not ABI-compatible across every historical release. EasyMod therefore resolves the correct loader/MDK/toolchain for the selected version rather than pretending one set of Java calls works unchanged from 1.7.10 through 26.2. The visual language is shared, while generated platform code is isolated per loader/version.

## Installation integration

The installer adds EasyMod to the current user's PATH without requiring administrator/root access:

- Linux: `~/.local/bin/easymod` and `~/.local/bin/EasyMod`, with PATH entries added to `.profile`, `.bashrc`, and `.zshrc` when needed.
- Linux: application-menu entry at `~/.local/share/applications/easymod.desktop` and a Desktop launcher when `~/Desktop` exists.
- Windows: current-user PATH entry for the EasyMod install directory, plus Start Menu and Desktop shortcuts.

Open a new terminal after installation for the updated PATH to be picked up by that shell.
