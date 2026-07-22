#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Controlled elevated bootstrapper for one authenticated exact execution request."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence

INSTALLER_ROOT = Path(__file__).resolve().parents[3]
for root in (
    INSTALLER_ROOT / "Bootstrapper" / "ElevationHelper" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "Security" / "Source",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from capability_elevation_helper import ElevationError, validate_bootstrap_request  # noqa: E402
from execution_security import (  # noqa: E402
    ExecutionSecurityError,
    canonical_json,
    claim_once,
    file_sha256,
    resolve_reviewed_path,
    run_bounded_process,
    seal_authenticated_record,
    sha256,
    utc_datetime,
    verify_sealed_record,
)

COMPLETION_SCOPE = "package-elevation-bootstrap-completion"
COMPLETION_STATEMENT = (
    "This receipt records one exact authenticated elevated helper execution with an explicit environment, "
    "bounded output, process-tree timeout enforcement, and no shell."
)


class ControlledBootstrapperError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ControlledBootstrapperError(f"{label} must be an object.")
    return value


def _copy_private(source: Path, root: Path, request_sha: str) -> Path:
    directory = Path(root) / "elevated-private-executables" / request_sha
    directory.parent.mkdir(mode=0o700, exist_ok=True)
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ControlledBootstrapperError("Elevated private executable directory already exists.") from exc
    destination = directory / ("reviewed-helper" + (source.suffix or ".bin"))
    output = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0), 0o700)
    input_fd = os.open(source, os.O_RDONLY | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0))
    try:
        while True:
            chunk = os.read(input_fd, 1024 * 1024)
            if not chunk:
                break
            view = memoryview(chunk)
            while view:
                written = os.write(output, view)
                if written <= 0:
                    raise ControlledBootstrapperError("Elevated private copy made no forward progress.")
                view = view[written:]
        os.fsync(output)
    finally:
        os.close(input_fd); os.close(output)
    os.chmod(destination, 0o700)
    return destination


def execute_bootstrap_request(
    request: Mapping[str, object], execution_root: Path, *, authority_key_path: Path,
    claim_root: Path, completed_at_utc: str,
) -> dict[str, object]:
    try:
        checked = validate_bootstrap_request(request, authority_key_path=authority_key_path)
        claim = claim_once(
            claim_root, authority_key_path=authority_key_path, claim_kind="claim.elevation-bootstrap-request", artifact_sha256=str(checked["request_sha256"]),
            nonce=str(checked["request_reference"]), claimed_at_utc=completed_at_utc,
        )
        helper = _object(checked["helper"], "request.helper")
        if helper.get("requires_elevation") is not True or helper.get("role") != "operation-helper":
            raise ControlledBootstrapperError("Bootstrap request target is not a reviewed elevated operation helper.")
        executable = resolve_reviewed_path(execution_root, str(helper["executable_path"]), file_required=True, label="Elevated reviewed executable")
        working_directory = resolve_reviewed_path(execution_root, str(helper["working_directory"]), file_required=False, label="Elevated reviewed working directory")
    except (ElevationError, ExecutionSecurityError) as exc:
        raise ControlledBootstrapperError(f"Bootstrap request validation failed: {exc}") from exc
    actual_hash, executable_size = file_sha256(executable)
    if actual_hash != helper["executable_sha256"]:
        raise ControlledBootstrapperError("Elevated reviewed executable hash mismatch.")
    private_executable = _copy_private(executable, Path(claim_root), str(checked["request_sha256"]))
    if file_sha256(private_executable)[0] != actual_hash:
        raise ControlledBootstrapperError("Elevated private executable copy failed verification.")
    try:
        outcome = run_bounded_process(
            [str(private_executable), *list(helper["argv"])], cwd=working_directory,
            environment=dict(helper["environment"]), timeout_seconds=int(helper["timeout_seconds"]),
            output_limit_bytes=int(helper["output_limit_bytes"]),
        )
        utc_datetime(completed_at_utc, "completed_at_utc")
    except (OSError, ExecutionSecurityError) as exc:
        raise ControlledBootstrapperError(f"Elevated reviewed helper execution failed: {exc}") from exc
    stdout = bytes(outcome.pop("stdout")); stderr = bytes(outcome.pop("stderr"))
    base = {
        "schema_version": 1, "completion_scope": COMPLETION_SCOPE,
        "request_sha256": checked["request_sha256"], "elevation_grant_sha256": checked["elevation_grant_sha256"],
        "launch_grant_sha256": checked["launch_grant_sha256"], "claim_sha256": claim["claim_sha256"],
        "helper_reference": helper["helper_reference"], "executable_sha256": actual_hash,
        "executable_size_bytes": executable_size, "environment_sha256": sha256(helper["environment"]),
        "argv_sha256": sha256(helper["argv"]), "completed_at_utc": completed_at_utc, **outcome,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stdout_size_bytes": len(stdout),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(), "stderr_size_bytes": len(stderr),
        "process_completion_observed": True, "shell_used": False, "exact_environment_applied": True,
        "immutable_private_copy_used": True, "statement": COMPLETION_STATEMENT, "bootstrap_request": checked,
    }
    try:
        return seal_authenticated_record(
            base, authority_key_path=authority_key_path, digest_field="completion_sha256"
        )
    except ExecutionSecurityError as exc:
        raise ControlledBootstrapperError(f"Completion receipt authentication failed: {exc}") from exc


def validate_completion_receipt(
    receipt: Mapping[str, object], *, authority_key_path: Path
) -> dict[str, object]:
    document = dict(receipt)
    if (
        document.get("schema_version") != 1
        or document.get("completion_scope") != COMPLETION_SCOPE
        or document.get("statement") != COMPLETION_STATEMENT
        or document.get("process_completion_observed") is not True
        or document.get("shell_used") is not False
        or document.get("exact_environment_applied") is not True
        or document.get("immutable_private_copy_used") is not True
    ):
        raise ControlledBootstrapperError("Completion receipt contract is invalid.")
    try:
        verify_sealed_record(
            document, authority_key_path=authority_key_path, digest_field="completion_sha256"
        )
    except ExecutionSecurityError as exc:
        raise ControlledBootstrapperError(f"Completion receipt authentication failed: {exc}") from exc
    validate_bootstrap_request(
        _object(document.get("bootstrap_request"), "completion.bootstrap_request"),
        authority_key_path=authority_key_path,
    )
    return document


def load_request(path: Path, *, authority_key_path: Path) -> dict[str, object]:
    payload = Path(path).read_bytes()
    try:
        document = _object(json.loads(payload.decode("utf-8", errors="strict")), "request")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlledBootstrapperError("Bootstrap request is not strict UTF-8 JSON.") from exc
    checked = validate_bootstrap_request(document, authority_key_path=authority_key_path)
    if canonical_json(checked) != payload:
        raise ControlledBootstrapperError("Bootstrap request bytes are not canonical JSON.")
    return checked


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--execution-root", type=Path, required=True)
    parser.add_argument("--authority-key", type=Path, required=True)
    parser.add_argument("--claim-root", type=Path, required=True)
    parser.add_argument("--completed-at-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = execute_bootstrap_request(
            load_request(args.request, authority_key_path=args.authority_key), args.execution_root,
            authority_key_path=args.authority_key, claim_root=args.claim_root, completed_at_utc=args.completed_at_utc,
        )
        payload = canonical_json(result)
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(descriptor, payload); os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return 0
    except (OSError, ControlledBootstrapperError, ElevationError) as exc:
        print(f"Controlled elevation bootstrapper failed: {exc}", file=sys.stderr); return 1


__all__ = ["ControlledBootstrapperError", "execute_bootstrap_request", "load_request", "validate_completion_receipt"]

if __name__ == "__main__":
    raise SystemExit(main())
