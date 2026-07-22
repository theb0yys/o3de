# Required `main` branch ruleset

Status: repository-host setting required before this repair pull request may become merge-ready.

The live GitHub ruleset for `main` must:

- require a pull request and block direct pushes;
- require at least one approving maintainer review;
- dismiss stale approvals when the head changes;
- require every review conversation to be resolved;
- require the exact-head checks:
  - `Tainted Grail SDK PR Static Validation / Python, validators, and fixtures`;
  - `Tainted Grail SDK PR Static Validation / Windows O3DE prerequisites`;
- require the branch to be current with `main` before merge;
- block force pushes and branch deletion;
- grant no routine bypass to contributors or automation;
- retain the repository’s merge-obligation policy and exact-head receipt requirements.

The repository source can validate and document this contract, but it cannot prove that the host-side ruleset is enabled. A maintainer must enable it in GitHub settings and record evidence in the pull request before merge.
