# Blender Provider

## Position in the program

Blender remains the first external authoring provider in the normative design. Unity implementation does not
skip the Blender provider, interchange-schema, O3DE handoff, or Blender round-trip gates.

The in-tree DCC Scripting Interface and Scene Exporter are prototype/reference material. Their presence does
not establish current Blender compatibility, safe bootstrap behavior, redistribution rights, or qualification.

## Research record requirements

For every Blender application and extension candidate, record:

- stable provider, application, extension, publisher, source revision, and package digest identities;
- exact Blender version, operating system, architecture, and O3DE revision;
- discovery behavior without process launch;
- plugin/add-on licence, dependencies, notices, and redistribution decision;
- interactive, batch, headless, import, export, and asset-source capability claims separately;
- exact FBX/sidecar or later format versions;
- whether DCCsi auto-bootstrap or legacy launch behavior exists;
- synthetic geometry, material, skeleton, animation, identity, and loss fixture results.

## Qualification boundary

Historical testing against Blender 3.0 or a default Blender 3.1 path cannot qualify a current release. A
current version becomes supported only after its exact matrix and round-trip fixtures pass. Discovery remains
read-only; add-on installation and execution require separate gates.
