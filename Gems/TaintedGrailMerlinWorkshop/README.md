# Tainted Grail Merlin Workshop Provider

`TaintedGrailMerlinWorkshop` is an optional O3DE Tool Gem that registers the
official Merlin Workshop Unity project with the existing `ExternalToolchain`
host.

The first slice is deliberately discovery-only:

- stable provider ID `foa.merlin-workshop`;
- disabled-by-default provider registration;
- one bounded Windows directory probe for an explicitly configured local
  Merlin Workshop project;
- an exact reference lock for Merlin Workshop `v1.1.0`, source revision
  `073bdab3e09d6adad5003339fc49b021738d71e6`, and Unity Editor
  `6000.0.60f1` revision `61dfb374e36f`;
- read-only diagnostics through the existing **External Toolchain** pane.

The Gem is registered with the engine but is not enabled in
`TaintedGrailModdingEditor/project.json`. Authors opt in through O3DE's normal
Gem activation flow and then provide machine-local Settings Registry values.

This Gem does not download or redistribute Merlin Workshop, launch Unity,
invoke the Merlin build menu, inspect the game installation, write a mod
output, deploy content, call FoA APIs, or grant runtime permission. An
`installed` result means only that the configured local directory exists and
the caller-configured semantic version satisfies the declared exact bound.

See
[Merlin Workshop Provider](../../docs/tainted-grail-sdk/MERLIN_WORKSHOP_PROVIDER.md)
for configuration, authority, and qualification details.
