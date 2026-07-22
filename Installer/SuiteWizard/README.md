# Suite wizard

This directory owns the future user-facing FOA-SDK suite-selection wizard.

The wizard presents reviewed suites and packages, prerequisites, exact versions, provenance, licences, compatibility, disk use, conflicts, planned filesystem changes, elevation, and rollback behavior before confirmation.

`Resolver/` is the engine-neutral source of truth beneath that UI. The wizard submits explicit selections, exclusions, features and compatibility context to the resolver, then displays its canonical plan and diagnostics. UI code may not recalculate dependency closure, version constraints, conflicts, compatibility, path safety, legal state, package ordering, payload collisions or plan fingerprints.

Wizard code must remain a thin presentation layer over deterministic suite resolution and installer services. It may not silently acquire packages, bypass hash or redistribution review, enable runtime adapters, launch FoA, deploy files, mutate saves, sign artifacts, publish releases, mutate the catalog, or promote evidence.

A valid resolution plan remains non-executable. Any later confirmation must bind to the exact `plan_sha256` before a separately reviewed acquisition or execution layer may consume it.

Generated binaries, plans, receipts and screenshots belong under the external build/evidence root, not in this directory.
