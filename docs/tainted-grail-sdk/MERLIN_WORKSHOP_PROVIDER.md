# Merlin Workshop Provider

Status: implemented optional discovery-only provider

## Decision

Merlin Workshop is the official Unity authoring toolkit for
*Tainted Grail: The Fall of Avalon*. The FOA SDK exposes it as an optional
provider through the existing `ExternalToolchain` host rather than creating a
second plugin loader or making Unity a required SDK dependency.

The provider is packaged as the ordinary O3DE Tool Gem
`TaintedGrailMerlinWorkshop` with stable provider ID
`foa.merlin-workshop`. The Gem is registered in `engine.json` but is not listed
in `TaintedGrailModdingEditor/project.json`, so the standard editor remains
usable without Merlin Workshop or Unity.

This TG-specific identity is separate from the proposed generic
`foa.unity-editor` interchange provider. It describes the official Merlin
authoring project; it does not implement Unity interchange or consume the
Gate 0 handoff envelopes. This narrow amendment authorises only descriptor
registration and bounded path discovery. It does not begin any process,
conversion, build, deployment, or runtime gate.

## Reference lock

The initial descriptor records this reviewed reference identity:

| Field | Value |
| --- | --- |
| Official repository | [`AR-Questline/merlin-workshop`](https://github.com/AR-Questline/merlin-workshop) |
| Release | [`v1.1.0`](https://github.com/AR-Questline/merlin-workshop/releases/tag/v1.1.0) |
| Source revision | `073bdab3e09d6adad5003339fc49b021738d71e6` |
| Unity Editor | `6000.0.60f1` |
| Unity revision | `61dfb374e36f` |
| Provider version | `0.1.0` |
| ExternalToolchain host API | `1.1.0` |

These values are a reproducible discovery reference, not a redistribution
grant, binary authenticity result, licence decision, or permission to execute
the external project. Merlin Workshop and Unity remain separately installed
and governed software.

## Enablement

1. Enable the `TaintedGrailMerlinWorkshop` Gem explicitly for the dedicated
   `TaintedGrailModdingEditor` project through O3DE's normal Gem activation
   workflow.
2. Put machine-specific values under the ExternalToolchain user configuration
   root.
3. Open the **External Toolchain** pane and refresh discovery.

Example user Settings Registry content:

```json
{
    "O3DE": {
        "ExternalToolchain": {
            "Configuration": {
                "User": {
                    "Providers": {
                        "foa.merlin-workshop": {
                            "Enabled": true,
                            "project-root": "C:/Tools/merlin-workshop",
                            "workshop-version": "1.1.0",
                            "workshop-release-tag": "v1.1.0",
                            "workshop-revision": "073bdab3e09d6adad5003339fc49b021738d71e6",
                            "unity-editor-version": "6000.0.60f1",
                            "unity-editor-revision": "61dfb374e36f"
                        }
                    }
                }
            }
        }
    }
}
```

The project root must be an explicit absolute path on fixed local storage.
Relative paths, network paths, traversal, symbolic links, junctions, and
redirected storage remain rejected by the host.

## Discovery semantics

The provider declares one required directory probe. A successful result proves
only that:

- the provider was explicitly enabled;
- the configured project root exists as a local directory without prohibited
  filesystem indirection; and
- the caller-configured Merlin semantic version is exactly `1.1.0`.

The host does not run Unity, parse the Unity project, extract a version from an
executable, verify the source revision, inspect package contents, or establish
licence entitlement. The configured release, source, and Unity values are
visible reference metadata for later qualification.

## Authority boundary

This slice contains no implementation that can:

- clone, download, install, update, or redistribute Merlin Workshop or Unity;
- launch Unity or invoke the `TG/Modding/Build` menu;
- scan a FoA installation or proprietary project;
- write to the game's mod directory;
- build, copy, archive, deploy, sign, or publish a mod;
- call FoA, Unity runtime, BepInEx, Harmony, save-game, or network APIs;
- grant operation enablement, process execution, deployment, or runtime
  permission.

The provider's interactive and asset-source capability flags describe the
external tool family. They do not authorize a command. The only registered
command is the non-executing `Probe` descriptor
`inspect-workshop-project`.

Any later launch, build, artifact handoff, or deployment support requires the
separately reviewed host process-supervision, staging, evidence, licensing, and
publication gates. Discovery success is never promoted automatically.
