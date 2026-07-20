# Qualification and Experiments

## Experiment policy

An experiment description is not authority to run it. Each executable experiment requires the implementation
gate that owns its security boundary, exact inputs, tools, paths, outputs, cleanup, and evidence.

Early fixtures remain synthetic or clearly redistributable. They contain no FoA assets, assemblies, extracted
metadata, proprietary Unity project, private path, or save.

## Ordered experiment classes

1. Pure contract fixtures for canonical serialization, identity, paths, locks, transforms, loss reports, and
   malformed input.
2. Synthetic process-supervisor fixture for success, refusal, timeout, cancellation, output limits, and cleanup.
3. Read-only Blender and Unity provider discovery fixtures.
4. Blender export/import and O3DE Asset Processor handoff in isolated authoring projects.
5. Blender round-trip fixtures with exact transformation and loss evidence.
6. Unity Editor package import/export in a synthetic test project.
7. O3DE-to-Unity and Unity-to-O3DE round trips under one exact toolchain lock.
8. Only after separate runtime gates: target-profile capture, mock adapter build, no-op load, and capability
   experiments.

## Determinism classes

- `byte_identical` — exact bytes and hashes match under one lock;
- `canonical_identical` — normalized public canonical representation matches;
- `within_tolerance` — explicitly named numeric properties match declared tolerances;
- `loss_reported` — differences are completely represented by accepted typed losses;
- `not_reproducible` — none of the above is proven.

“Semantically identical where possible” is not an acceptance criterion until the canonical comparison and its
tolerances are defined. C# compiler determinism does not imply deterministic Unity imports, bundles, logs,
metadata, packages, or complete runtime artifacts.

## Negative coverage

Qualification must cover wrong and ambiguous versions, stale locks, missing inputs, identity collisions,
unsafe paths, licence blockers, malicious archives, unsupported features, process failure, partial output,
cleanup failure, and round-trip non-equivalence. No green process exit may substitute for schema, output,
compatibility, or loss validation.
