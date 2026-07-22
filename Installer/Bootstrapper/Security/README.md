# Installer execution security boundary

`Bootstrapper/Security/` is the common authority and effect-safety boundary for the operational installer chain.

It owns:

- reviewed operation plans bound to the exact resolver `plan_sha256` and `package_order`;
- package-owned helper allow-lists with exact executable path, digest, arguments, working directory, environment, timeout, and output bound;
- an external installer-authority trust key used to authenticate authority proofs and every executable grant/result;
- create-once one-shot claim records for tokens, copy grants, launch grants, elevation grants, bootstrap requests, and state-publication grants;
- atomic no-replace directory publication;
- symlink-safe exact path resolution and SHA-256 verification;
- bounded streaming stdout/stderr capture with process-tree termination.

## Trust anchor

The authority key is raw 32–64 byte key material owned by the trusted installer broker. It must be stored outside package payloads, source trees, logs, receipts, and command output. On POSIX hosts, group and other permissions are rejected. Production Windows packaging must provision the key with an ACL readable only by the broker identity.

Possession of a token, session, grant, or receipt is not sufficient to execute an effect. The effect boundary also requires the configured authority key and atomically consumes the exact artifact digest before work begins.

## Reviewed helper ownership

Every helper is owned by one package in the exact resolver package order. An operation plan is rejected unless its resolver plan fingerprint and package order match the receipt handoff authenticated by the authority proof.

Callers select a helper reference only. They cannot supply executable paths, hashes, arguments, environment variables, working directories, timeout, or output limits at launch time.

## Non-authority

These primitives grant no network publication, runtime adapter execution, game launch, save mutation, signing, catalogue mutation, or evidence promotion authority.
