# Unity Editor Interchange

## Scope

This area covers an editor-only Unity extension operating in a synthetic or user-owned test project. It does
not point at, discover, convert, or imply access to the proprietary FoA Unity project.

The current design candidates are provider ID `foa.unity-editor` and package ID
`com.foa.sdk.interchange`. The supplied report proposes `unity.foa.conversion` and `com.foa.conversion`.
None is final until Gate 8 resolves identity, ownership, licence, schema, migration, and compatibility.

## Separate profiles

An authoring `UnityEditorInterchangeProfile` should bind the exact Unity Editor, extension, package digest,
interchange schema, payload format, conversion configuration, test-project identity, and qualification fixture.
It must not require a FoA game version, BepInEx version, scripting backend, assembly layout, or game loading
model. Those belong to the separately gated runtime-target profile.

## Candidate batch model

Gate 0 may define a disabled, `NotAttempted` `UnityConversionRequestV1` and `UnityConversionResultV1` in Core.
They are never runtime requests, contain no attempted conversion evidence, and are consumed by no service. The
report's version-locked Unity conversion project and editor-only package remain Gate 8/9 research candidates.
Qualification must determine:

- exact supported Editor version and command-line flags;
- batch versus genuinely headless capability;
- project lock and mutable cache behavior;
- package and `packages-lock.json` identity;
- stable canonical-to-Unity GUID binding and `.meta` retention;
- input, generated-output, log, and cleanup roots;
- import/postprocessor execution risks;
- repeatability and complete transformation/loss reporting.

Current read-only discovery must not run Unity with `-version`; executable interrogation begins only after the
execution gate. `-accept-apiupdate` is incompatible with immutable first-slice inputs unless a later design
restricts it to a disposable candidate copy.

The Unity Editor extension must not build, contain, deploy, or execute a FoA runtime plugin.
