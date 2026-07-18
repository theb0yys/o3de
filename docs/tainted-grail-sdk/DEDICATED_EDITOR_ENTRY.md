# Dedicated Editor Entry Architecture

Developer Preview 0 uses the repository-owned `TaintedGrailModdingEditor`
project as its product host.

The project:

- is registered by `engine.json`;
- enables `TaintedGrailModdingSDK` exactly once;
- owns its O3DE preview PNG and Windows shortcut ICO;
- is independent from the upstream `AutomatedTesting` project;
- is selected by `developer_preview_open.py`;
- is selected by the generated `Tainted Grail Modding Editor.lnk`.

The `.lnk` is generated after build because it contains machine-local absolute
paths to the source-built `Editor.exe` and repository checkout. No `.lnk` or
private absolute path is committed.

`developer_preview_entry.py` is the supported clickable-entry command. The
standard entry derives its project, icon, approved build directory, target and
working directory from repository-owned policy. `CMakeCache.txt` must bind the
approved build to the current repository, and the executable must have a valid
x64 PE32+ Windows GUI header.

The sidecar records the generated `.lnk` size and SHA-256. It is not the root of
trust. Verification compares the sidecar and actual Windows shortcut against
the repository-derived policy.

An explicit external `--editor` is diagnostic-only. It requires
`--diagnostic-override`, must use `build/diagnostic-entries`, cannot replace the
standard entry, and is rejected by normal verification.

`--replace` first verifies the existing generated shortcut. An unrelated,
modified, unapproved, or incomplete `.lnk` is never removed automatically.

The entry tooling does not install software, create a desktop entry silently,
launch FoA, or expose arbitrary Editor arguments.
