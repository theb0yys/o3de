# Research Blocker — Avalon Mounts Diagnostics, Output, and Privacy

```yaml
blocker_id: tg.blocker.mounts.diagnostics-output-privacy
status: research-blocker
domain: mounts-diagnostics-privacy-and-support
source_repository: theb0yys/Tainted-Grail-The-Fall-of-Avalon-mods
source_commit: d7e740e7f167b73152b53409e483dab07d80d048
primary_sources:
  - mods/avalon-mounts/src/Plugin.cs
  - mods/avalon-mounts/src/Diagnostics/NativeHorseTransitionProbe.cs
  - mods/avalon-mounts/src/Diagnostics/MountModDetector.cs
source_blobs:
  - 896e0f4e63c57b1800eb3ac09468cefe0ca8509d
  - 7459480772a1fb7660af722dddd91ee1497d2ea5
  - ed46ff75641ba8247d4ef13e5adcacdaf46606cc
```

## Decision

The diagnostics lane remains blocked from handbook promotion and executable SDK guidance. The selected source demonstrates local output behavior, but it does not supply a reviewed capture schema, redaction contract, retention limit, deletion workflow, support-sharing policy, or exact output inventory for every enabled probe.

## Known source behavior

- The plug-in resolves an output directory under `BepInEx.Paths.ConfigPath/AvalonMounts/diagnostics`, with a relative-path fallback.
- The transition probe creates the directory and appends `native_horse_transition_probe.csv`.
- Transition rows include UTC timestamp, plug-in version, active scene name, runtime type names, controller presence/type, hook target, and notes.
- The compatibility detector recursively scans plug-in DLL filenames and may write `mount_mod_compatibility.txt` with timestamp and detected-name booleans.
- The plug-in can invoke multiple additional snapshot, signature, candidate-surface, lifecycle, travel, support-summary, passive-observation, and compatibility writers depending on configuration.
- Exceptions generally log warnings and skip the failed write.

## Blocking questions

1. What is the complete file and column inventory for every diagnostics option?
2. Which fields can expose local paths, mod filenames, user-selected names, scene names, machine state, or third-party identifiers?
3. What are the maximum rows, bytes, write frequency, and retention period for each output?
4. Are files truncated, rotated, deduplicated, or removed during uninstall?
5. Which outputs are safe to attach to a support request, and what redaction is mandatory?
6. Can recursive DLL enumeration cross junctions, encounter inaccessible directories, or create avoidable performance/privacy risk?
7. Does the relative fallback write into an unexpected working directory?
8. Are timestamps and runtime type names necessary for the documented diagnostic purpose?
9. Can a diagnostics-only configuration accidentally enable a runtime-mutation registration path?
10. Is every writer fail-open with respect to gameplay and bounded against repeated exceptions?

## Required resolution

Promotion requires:

- a versioned diagnostics schema and exact file inventory;
- field-level data classification and redaction rules;
- bounded row/byte/frequency limits;
- deterministic cleanup and uninstall behavior;
- a support-sharing allowlist;
- controlled tests for inaccessible paths, full disks, malformed data, repeated callbacks, and disabled configuration;
- proof that diagnostics failures do not alter gameplay or save state;
- separate approval for recursive plug-in-folder scanning.

## Permissions

Allowed now: source review, documentation, schema design, synthetic fixture testing, and privacy threat modelling.

Prohibited now: live capture, game-folder scanning, publishing raw outputs, support upload, runtime execution, or evidence promotion.