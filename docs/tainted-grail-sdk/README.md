# Tainted Grail Modding Editor and SDK Documentation

This directory contains the public documentation for the TG SDK layer in this O3DE fork.

## Start here

### For users

- [User Guide](USER_GUIDE.md) — build, open, configure, and use the current editor tools.
- [Data Formats](DATA_FORMATS.md) — workspace, pack, source, evidence, issue, and catalog document contracts.
- [Support](../../SUPPORT.md) — where and how to ask for help.
- [Security](../../SECURITY.md) — private reporting and secure-use guidance.

### For contributors

- [Contributing](../../CONTRIBUTING.md) — contribution lifecycle and DCO requirements.
- [Development Guide](DEVELOPMENT_GUIDE.md) — repository setup, build, validation, and implementation workflow.
- [Architecture](ARCHITECTURE.md) — layers, responsibilities, invariants, and data flow.
- [Code Quality](CODE_QUALITY.md) — mandatory C++, Qt, persistence, UI, testing, and evidence standards.
- [Review and Merge Policy](REVIEW_AND_MERGE_POLICY.md) — design review, self-review, pull-request review, and merge gates.
- [Release Process](RELEASE_PROCESS.md) — versioning, release evidence, packaging, and rollback.
- [Maintainer Checklist](MAINTAINER_CHECKLIST.md) — recurring repository and release responsibilities.

### Project governance

- [Governance](../../GOVERNANCE.md)
- [Code of Conduct](../../CODE_OF_CONDUCT.md)
- [Roadmap](../../ROADMAP.md)
- [Changelog](../../CHANGELOG.md)

## Documentation authority

When documents conflict, use this order:

1. security policy and licence obligations;
2. governance and review policy;
3. architecture and data-format contracts;
4. code-quality standard;
5. user and development guides;
6. examples and issue discussions.

A merged architecture decision or schema migration may supersede an older section. The change must update the affected documentation in the same pull request.

## Current product status

The project is pre-alpha. Current implemented editor workflows cover:

- workspace and exact game profile;
- mod and content-pack projects;
- source and evidence intake;
- foundation status, coverage, and blockers.

The canonical catalog browser and record inspector are the next active development slice. Domain authoring tools, runtime adapters, and production deployment are not complete.

## Documentation contribution rules

Documentation changes must:

- describe current behavior honestly;
- distinguish implemented, planned, and experimental behavior;
- avoid publishing proprietary game content or private paths;
- use stable internal links;
- update examples when schemas change;
- include migration notes for breaking changes;
- use clear, direct language and define project-specific terms.
