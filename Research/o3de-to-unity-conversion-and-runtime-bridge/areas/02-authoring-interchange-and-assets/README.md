# Authoring Interchange and Assets

## Scope

This area covers project-owned or synthetic authoring content exchanged among Blender, O3DE, and a synthetic
or user-owned Unity Editor test project. It does not cover a proprietary FoA project or a running game.

## Contract topics

- one versioned `manifest.tginterchange.json` package boundary;
- stable `PackageId`, `AssetId`, `RevisionFingerprint`, and `BindingId` identities;
- exact native bindings without treating display names or paths as identity;
- contained relative payload paths, byte sizes, media types, and SHA-256 observations;
- explicit coordinate basis, units, transform order, pivot, timebase, and conversion matrices;
- bounded mesh, texture, material, skeleton, animation, collider, and metadata declarations;
- provenance, authorship, licence, attribution, modification, and redistribution state;
- ordered transformations, typed losses, validation evidence, and exact toolchain locks;
- reverse and round-trip behavior with declared numeric tolerances.

Gate 0 owns inert Core-only outer handoff/result envelopes. No service consumes them and every authority and
performed flag remains false. A later process operation may bind the interchange package through those
envelopes, but the envelopes do not replace its identity, transformation, provenance, and loss contracts.

## Open reconciliation points

- The canonical basis needs an explicit forward axis, vector convention, and matrix multiplication convention.
- FBX byte determinism versus normalized semantic determinism must be defined and tested.
- External source-native references must be non-material provenance references or become contained,
  fingerprinted package dependencies.
- Asset Processor rejection must not leave published source assets changed; qualification needs an isolated
  scratch project/scan root or an explicit reversible publication model.

## Active focused research question

The current research process advances through
[`CANONICAL_INTERCHANGE_SCHEMA_RESEARCH_QUESTION.md`](CANONICAL_INTERCHANGE_SCHEMA_RESEARCH_QUESTION.md).

That question requires the minimum schema 1 field inventory, canonical serialization rules, identity and native-
binding state machine, spatial and temporal basis, payload model, transformation and loss taxonomy, provenance
and legal state, determinism classes, validation/error inventory, schema evolution, and positive/negative
fixtures.

The question is research-only and does not authorize schema implementation, provider execution, native-host
mutation, or runtime work.

## Authority boundary

Format documentation and a successful import do not establish cross-engine compatibility. No format or
round-trip claim becomes supported until the exact adapters, hosts, profiles, and fixtures pass the applicable
implementation gates.
