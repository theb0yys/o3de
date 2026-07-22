# Semantic Repair Package

`semantic_repair` is a project-owned, engine-neutral package for deterministic synthetic repair work.

It provides:

- explicit transaction, cancellation and rollback phases with validated transitions;
- typed mapping and synthetic mount transactions;
- owner/generation resource leases and locked journal writes;
- hash-chained crash-recovery journals with deterministic recovery plans;
- lease-owned terminal-journal compaction with canonical checkpoint proofs;
- interrupted-compaction recovery, rotated checkpoint chains, archive manifests, retention plans, metadata-only tombstones, supersession records and restoration reviews;
- cumulative repeated-compaction quotas with immutable release, ledger-compaction and reconciliation records;
- manual lock-abandonment reviews, quorum decisions, revocations, supersessions, appeals, withdrawals and resolutions with no automatic lock theft;
- recoverable multi-file publication intent journals with checkpoint integration, bounded before-image backups, dependency graphs, read-only partial-rollback plans and acknowledgement receipts;
- deterministic Cartesian and cancellation/recovery composition matrices;
- diagnostic path, redaction, byte-limit, generation and atomic-publication utilities;
- canonical API v2 JSON, bounded generation gaps, replay-window receipts, replay sequences, sequence-compaction proofs and metadata-only retention policies;
- negative workflow policy validation, reproducible receipts, Python 3.11–3.13 fixtures, deterministic migrations, chained migration histories and compatibility matrices.

The package is not a game runtime adapter. It has no game or loader assembly references, dynamic import, reflection, network, subprocess, installation discovery, deployment, evidence admission, or promotion capability.

`repair_primitives.py` remains as the Batch 006 compatibility facade. New project-owned code should import from `semantic_repair` directly.
