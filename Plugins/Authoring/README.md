# Authoring plug-ins

This category contains optional editor-side authoring systems.

Expected packages include Avalon AI, the reusable UI Framework, and Road Atlas. Each package must remain independently selectable, register through the governed ExtensionAPI, and use Foundation services rather than reaching into mutable catalog or workspace internals.

Authoring packages may produce candidate evidence, validation results, typed documents, plans, and reviewed handoffs. They do not gain FoA runtime, deployment, save, signing, publication, or automatic evidence-promotion authority.

Every package directory requires a schema-valid `plugin.json` at its root.
