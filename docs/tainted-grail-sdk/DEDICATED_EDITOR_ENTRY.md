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

The shortcut generator writes a SHA-256 manifest beside the link and supports
explicit verification. It does not install software, create a desktop entry
silently, launch FoA, or expose arbitrary Editor arguments.
