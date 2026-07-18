# Developer Preview 0

Status: first implementation slice — command layer available; preview fixture, launch wrapper, smoke harness, diagnostics bundle, and distributable artifact are not implemented yet.

## Purpose

Developer Preview 0 is the project’s source-built, pre-alpha usability milestone. Its first supported runnable target is **Windows x64 Profile**.

This milestone is not a standalone installer or a production mod toolchain. The command layer does not launch FoA, invoke BepInEx or Harmony, deploy files, modify saves, collect telemetry, or install prerequisites automatically.

## First-slice commands

Run all commands from the repository root. The default build directory is:

```text
build/tg-sdk-developer-preview-0-windows-profile
```

An explicit `--build-dir` may point elsewhere, but it must not be the repository root, contain the repository, live inside `.git`, or contain unrelated files without a matching O3DE `CMakeCache.txt`.

### 1. Check prerequisites

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py prerequisites `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile `
  --json-output build/tg-sdk-developer-preview-0-windows-profile/prerequisites.json
```

Required checks cover:

- Windows x64 host;
- Python 3.10 or newer;
- CMake 3.23 or newer;
- Git and Git LFS;
- Visual Studio 2022 or Build Tools with **Desktop development with C++**;
- a valid O3DE repository root.

The checker is read-only. It reports whether the build directory is configured and whether `bin/profile/Editor.exe` exists, but those are informational until the configure and build steps run.

### 2. Preview the configure command

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py configure `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile `
  --dry-run
```

The approved configure command uses the repository’s `windows-vs-unity` CMake preset, an explicit build directory, and x64 architecture. Remove `--dry-run` to execute it:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py configure `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile
```

The wrapper prints the exact CMake command before execution and returns CMake’s original exit code.

### 3. Build the Editor and focused test target

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py build `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile
```

This builds the Profile configuration for exactly these targets:

```text
Editor
TaintedGrailModdingSDK.Catalog.Tests
```

Use `--dry-run` to inspect the command without invoking the build.

### 4. Run the full focused validation command

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py validate `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile
```

The validation command runs, in order:

1. Developer Preview command unit tests;
2. Developer Preview command contract validation;
3. TG SDK foundation validation;
4. governance-hardening validation;
5. catalog/governance/economy contract validation;
6. O3DE source-policy validation for the TG SDK Gem;
7. compiled `TaintedGrailModdingSDK.Catalog.Tests` through CTest.

It stops on the first failure and propagates that command’s exit code. It writes a machine-readable summary to:

```text
<build-dir>/tg-sdk-developer-preview-validation.json
```

Use `--result <path>` to select another explicit result path. Use `--dry-run` to print the ordered plan and write a planned-result document without executing tests.

## Failure behavior

The command layer fails closed for:

- unsupported hosts;
- invalid repository roots;
- unsafe or unrelated build directories;
- CMake caches bound to another source tree;
- missing build configuration before a real build or validation run;
- prerequisite, configure, build, validator, source-policy, or compiled-test failures.

No command uses a shell command string. Child processes receive explicit argument arrays, and no prerequisite is installed silently.

## Current limitations

This first slice does not yet provide:

- a generated preview workspace or synthetic evidence fixture;
- load, save, close-equivalent, and reopen smoke automation;
- an Editor launch wrapper;
- redacted diagnostics collection;
- manual UI smoke evidence;
- a CI-produced runnable Windows archive or source-build support bundle.

Those capabilities remain gated by the approved [Developer Preview 0 design](DEVELOPER_PREVIEW_0_DESIGN.md). Until they are complete and verified, the project remains a source-built pre-alpha editor and must not be presented as a finished Developer Preview release.
