# Capability-gated elevation helper

`ElevationHelper/` is the isolated operating-system elevation boundary for the FOA-SDK installer.

It requires all of the following before an elevation prompt may be requested:

1. an exact verified package-engine session containing `package-engine.elevation`;
2. an exact verified process-launch grant bound to that session;
3. an explicit user-consent record bound to the launch grant and executable identity;
4. a separate elevation grant issued after consent and valid for at most five minutes;
5. an absolute regular non-symlink executable whose SHA-256 matches the reviewed launch grant.

The production Windows backend invokes `ShellExecuteW` with the fixed `runas` verb. It does not accept or capture credentials, cannot suppress the operating-system consent UI, does not use a shell command string, and does not inherit new installer authority.

The grant turns on only the existing `elevation` authority field. Acquisition, installation finalization, game launch, runtime execution, deployment, save mutation, signing, publication, catalogue mutation, and evidence promotion remain false.

The result records only whether the operating system accepted the elevation request. It deliberately sets `process_completion_observed = false`; lifecycle success must be established by a later isolated result/receipt gate.

Hosted tests use an injected fake backend and never display a real UAC prompt. They cover deterministic consent and grant derivation, missing-capability rejection, session/launch/consent binding, expiry, tampering, exact executable hashing, backend invocation, and the absence of credential or silent-elevation surfaces.

## Security hardening

Elevation launches only the reviewed controlled bootstrapper. Authenticated consent and grants bind the exact helper request; the bootstrapper receives its reviewed configuration argv plus one one-shot request path and produces a separately authenticated completion receipt.
