# Developer Preview Troubleshooting

This guide covers the source-built Developer Preview 0 path. It does not cover
FoA launch, BepInEx, Harmony, deployment, save mutation, or runtime adapters.

## Editor executable is missing

Run:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview.py build `
  --build-dir build/tg-sdk-developer-preview-0-windows-profile
```

The launcher expects `Editor.exe` beneath `bin/profile` or `bin/Profile`.

## Clickable entry is missing

Create it after a successful build:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_shortcut.py create
```

The output is:

```text
build/Tainted Grail Modding Editor.lnk
```

Use `--replace` only when deliberately replacing a previously generated link.

## The dedicated project contract fails

Run:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/validate_developer_preview_project.py
```

The contract requires:

- `engine.json` registers `TaintedGrailModdingEditor`;
- the dedicated `project.json` enables `TaintedGrailModdingSDK` exactly once;
- `AutomatedTesting/project.json` does not enable the TG SDK;
- the PNG and ICO project-owned icons are valid;
- the opener and shortcut generator select the dedicated project;
- the quickstart documents the clickable entry.

## The Editor exits immediately

Use the command-line fallback to capture wrapper logs:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_open.py
```

Review:

- `build/tg-sdk-developer-preview-0-launch/editor-launch.stderr.log`;
- `build/tg-sdk-developer-preview-0-launch/tg-sdk-developer-preview-launch.json`;
- `TaintedGrailModdingEditor/user/log/Editor.log`.

## The TG SDK panes are missing

After the Editor opens, use **Tools → Tainted Grail SDK**.

If that menu group is absent:

1. validate the dedicated project contract;
2. reconfigure after pulling project or engine-manifest changes;
3. rebuild `Editor`;
4. verify the shortcut targets the same build directory;
5. close other Editor or Asset Processor instances;
6. search `TaintedGrailModdingEditor/user/log/Editor.log` for
   `TaintedGrailModdingSDK` activation or module-load errors.

The expected activation message says the editor foundation was activated and
FoA runtime execution remains disabled.

## Shortcut verification fails

Run:

```powershell
python Gems/TaintedGrailModdingSDK/Tools/developer_preview_shortcut.py verify
```

A size or SHA-256 mismatch means the `.lnk` changed after generation. Delete it
and recreate it. Do not share or rely on a shortcut that fails verification.

## Native Editor logs and wrapper logs differ

The `.lnk` opens the Editor directly. O3DE’s native log is:

```text
TaintedGrailModdingEditor/user/log/Editor.log
```

`developer_preview_open.py` additionally captures wrapper-owned process output
under `build/tg-sdk-developer-preview-0-launch`.

## Diagnostics collection fails

Diagnostics output must be empty, or a previously verified bundle used with
`--replace`. It must not be inside the project or workspace being inventoried.

Nothing is uploaded automatically. Review every generated file before sharing.
