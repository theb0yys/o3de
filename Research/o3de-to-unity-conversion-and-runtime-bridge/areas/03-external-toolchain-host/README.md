# ExternalToolchain Host

## Current repository state

At baseline commit `92aa29960bab92d646c464ae48b8cf09d881a436`, `ExternalToolchain` is Gem version
`0.2.0` with host API `1.1.0`. It registers typed provider descriptors, resolves layered configuration, performs
bounded inspection of caller-configured absolute local paths, and reports deterministic diagnostics.

It does not launch or interrogate applications, execute shell commands, supervise processes, perform IPC,
generate files, hand assets to Asset Processor, install plugins, deploy content, or call a game.

## Process-supervision research boundary

A later generic supervisor design must cover:

- exact executable and qualification bindings;
- argument representation and Windows quoting fixtures;
- immutable inputs and isolated writable staging;
- sanitized environment construction and secret redaction;
- bounded runtime, cancellation, output limits, and process-tree cleanup;
- editor responsiveness, shutdown, and crash behavior;
- safe log references, raw-versus-redacted evidence, and output fingerprints;
- project/provider concurrency locks;
- schema-validated results and atomic candidate publication;
- explicit statement of what network isolation is technically enforced.

`AzFramework::ProcessWatcher` is an available primitive, not proof that these requirements are satisfied.
Fingerprints observe identity or integrity; they do not authenticate a publisher or grant execution permission.

## Ownership

The host owns generic execution policy. Provider Gems may declare commands and bounded parameters but may not
construct shell strings, detach processes, publish partial output, or perform game cleanup/rollback. Game
rollback remains a future runtime-executor responsibility.

No research in this area authorises process launch.
