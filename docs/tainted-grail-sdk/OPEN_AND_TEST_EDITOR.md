# Open and Test the Actual Editor

This is the supported Windows path from a fresh checkout to the dedicated,
source-built **Tainted Grail Modding Editor**.

The editor is an O3DE project named `TaintedGrailModdingEditor`. It is separate
from `AutomatedTesting`, enables `TaintedGrailModdingSDK` directly, and owns the
project and Windows shortcut icons.

## Requirements

- Windows x64;
- Visual Studio 2022 or Build Tools with **Desktop development with C++**;
- Python 3.10 or newer;
- CMake 3.23 or newer;
- Git and Git LFS.

Run every command from the repository root.

## 1. Prepare the checkout

```powershell
git checkout main
git pull --ff-only
git lfs install
git lfs pull
```

Confirm the dedicated project contract:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/validate_developer_preview_project.py
```

The command must report that the dedicated project, icons, opener, and shortcut
contract are complete.

## 2. Check prerequisites

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py prerequisites `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile
```

Resolve every required failure before continuing.

## 3. Configure and build

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py configure `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile

python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py build `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile
```

The actual O3DE Editor executable is expected at:

```text
build/tg-sdk-developer-preview-0-windows-profile/bin/profile/Editor.exe
```

## 4. Create the clickable entry

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_shortcut.py create
```

This creates:

```text
build/Tainted Grail Modding Editor.lnk
build/Tainted Grail Modding Editor.shortcut.json
```

The shortcut has the project-owned icon and launches the source-built
`Editor.exe` with:

```text
--project-path <repository>/TaintedGrailModdingEditor
```

Double-click **Tainted Grail Modding Editor.lnk**.

To inspect the shortcut plan without writing files:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_shortcut.py create `
  --dry-run
```

To replace an existing generated shortcut deliberately:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_shortcut.py create `
  --replace
```

Verify the generated shortcut hash manifest:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_shortcut.py verify
```

## 5. Command-line fallback

The dedicated opener uses the same project and restricted launcher:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_open.py
```

Use this when collecting wrapper-owned stdout, stderr, and launch-result data.

## 6. Open the TG SDK panes

After the Editor opens, use:

```text
Tools → Tainted Grail SDK
```

Open:

- Tainted Grail SDK Status;
- Tainted Grail Pack Manager;
- Tainted Grail Source Intake;
- Tainted Grail Catalog Browser;
- Tainted Grail Catalog Governance;
- Tainted Grail Item and Recipe Editor.

The native Editor log is:

```text
TaintedGrailModdingEditor/user/log/Editor.log
```

It should contain `TaintedGrailModdingSDK` and
`Editor foundation activated`.

## 7. Generate the synthetic workspace

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_fixture.py generate `
  --output build/tg-sdk-developer-preview-0-fixture

python Gems/TaintedGrailModdingSDK/Tools/developer_preview_fixture.py verify `
  --output build/tg-sdk-developer-preview-0-fixture
```

Use only that project-owned fixture for the manual UI evidence pass.

## Architecture boundary

`AutomatedTesting` remains an upstream engine test project and does not enable
the TG SDK Gem. The dedicated project is the only supported preview host.

The shortcut launches only the source-built O3DE Editor. It does not launch
FoA, BepInEx, Harmony, Avalon Core, deployment, injection, or save-mutation
tools.
