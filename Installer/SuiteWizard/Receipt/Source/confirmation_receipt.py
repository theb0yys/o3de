#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Deterministic persistence and verification for Suite Wizard review receipts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Mapping, Sequence

SUITE_WIZARD_ROOT = Path(__file__).resolve().parents[2]
VIEW_MODEL_SOURCE = SUITE_WIZARD_ROOT / "ViewModel" / "Source"
if str(VIEW_MODEL_SOURCE) not in sys.path:
    sys.path.insert(0, str(VIEW_MODEL_SOURCE))

from wizard_view_model import (  # noqa: E402
    AUTHORITY_FIELDS,
    WizardContractError,
    canonical_json,
    sha256,
    validate_plan,
    validate_view_model,
    verify_confirmation,
)

RECEIPT_SCOPE = "review-confirmation-publication"
RECEIPT_STATEMENT = (
    "This receipt records a verified FOA-SDK review-only confirmation and grants "
    "no acquisition, installation, elevation, game-launch, runtime-execution, "
    "deployment, save-mutation, signing, network publication, catalog-mutation, "
    "or evidence-promotion authority."
)


class ReceiptError(RuntimeError):
    """Raised when a receipt or publication target is invalid."""


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ReceiptError(f"{label} must be an object.")
    return value


def build_receipt(
    plan: Mapping[str, object],
    view_model: Mapping[str, object],
    confirmation: Mapping[str, object],
) -> dict[str, object]:
    """Reverify the accepted chain and build its deterministic self-contained receipt."""
    checked_plan = validate_plan(plan)
    checked_view = validate_view_model(checked_plan, view_model)
    checked_confirmation = verify_confirmation(checked_plan, checked_view, confirmation)
    base = {
        "schema_version": 1,
        "receipt_scope": RECEIPT_SCOPE,
        "plan_sha256": checked_plan["plan_sha256"],
        "view_model_sha256": checked_view["view_model_sha256"],
        "confirmation_sha256": checked_confirmation["confirmation_sha256"],
        "plan": checked_plan,
        "view_model": checked_view,
        "confirmation": checked_confirmation,
        "statement": RECEIPT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "receipt_sha256": sha256(base)}


def validate_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    """Validate every embedded artifact and require exact canonical receipt derivation."""
    document = dict(receipt)
    if document.get("schema_version") != 1:
        raise ReceiptError("receipt.schema_version must be exactly 1.")
    if document.get("receipt_scope") != RECEIPT_SCOPE:
        raise ReceiptError("receipt.receipt_scope is invalid.")
    if document.get("statement") != RECEIPT_STATEMENT:
        raise ReceiptError("receipt.statement was altered.")
    authority = _object(document.get("authority"), "receipt.authority")
    if set(authority) != set(AUTHORITY_FIELDS) or any(
        authority.get(field) is not False for field in AUTHORITY_FIELDS
    ):
        raise ReceiptError("receipt.authority must contain the exact all-false authority record.")

    plan = _object(document.get("plan"), "receipt.plan")
    view_model = _object(document.get("view_model"), "receipt.view_model")
    confirmation = _object(document.get("confirmation"), "receipt.confirmation")
    expected = build_receipt(plan, view_model, confirmation)
    if document != expected:
        raise ReceiptError("receipt is stale, altered, or not canonically derived.")
    return document


def canonical_receipt_bytes(receipt: Mapping[str, object]) -> bytes:
    return canonical_json(validate_receipt(receipt))


def _reject_symlink_components(path: Path) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise ReceiptError(f"Receipt path contains a symbolic link: {current}")
        if current.parent == current:
            break
        current = current.parent


def _validated_destination(destination: Path) -> Path:
    target = Path(destination)
    if target.name in {"", ".", ".."} or not target.name.endswith(".foa-receipt.json"):
        raise ReceiptError("Receipt destination must end with '.foa-receipt.json'.")
    parent = target.parent
    if not parent.exists() or not parent.is_dir():
        raise ReceiptError("Receipt destination parent must be an existing directory.")
    _reject_symlink_components(parent)
    if target.is_symlink():
        raise ReceiptError("Receipt destination must not be a symbolic link.")
    if target.exists() and not target.is_file():
        raise ReceiptError("Receipt destination must be a regular file path.")
    return target


def _read_exact_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ReceiptError(f"Receipt path is not a regular non-symlink file: {path}")
    return path.read_bytes()


def load_receipt(path: Path) -> dict[str, object]:
    """Load a canonical receipt and reject alternate encodings or formatting."""
    target = Path(path)
    _reject_symlink_components(target.parent)
    payload = _read_exact_file(target)
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(f"Receipt is not strict UTF-8 JSON: {target}") from exc
    document = validate_receipt(_object(value, "receipt"))
    if canonical_json(document) != payload:
        raise ReceiptError("Receipt file bytes are not canonical JSON.")
    return document


def verify_published_receipt(
    path: Path,
    plan: Mapping[str, object],
    view_model: Mapping[str, object],
    confirmation: Mapping[str, object],
) -> dict[str, object]:
    loaded = load_receipt(path)
    expected = build_receipt(plan, view_model, confirmation)
    if loaded != expected:
        raise ReceiptError("Published receipt does not match the current accepted chain.")
    return loaded


def publish_receipt(
    destination: Path,
    plan: Mapping[str, object],
    view_model: Mapping[str, object],
    confirmation: Mapping[str, object],
) -> dict[str, object]:
    """Atomically publish canonical bytes without replacing an existing different file."""
    target = _validated_destination(destination)
    receipt = build_receipt(plan, view_model, confirmation)
    payload = canonical_receipt_bytes(receipt)

    if target.exists():
        existing = _read_exact_file(target)
        if existing != payload:
            raise ReceiptError("Receipt destination already exists with different bytes.")
        load_receipt(target)
        return {
            "status": "already-current",
            "path": str(target),
            "receipt_sha256": receipt["receipt_sha256"],
            "size_bytes": len(payload),
            "authority": _authority(),
        }

    temporary = target.parent / f".{target.name}.{receipt['receipt_sha256']}.tmp"
    if temporary.exists() or temporary.is_symlink():
        raise ReceiptError(f"Deterministic temporary receipt path already exists: {temporary}")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, flags, 0o600)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise ReceiptError("Receipt write made no forward progress.")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None

        if _read_exact_file(temporary) != payload:
            raise ReceiptError("Temporary receipt bytes changed before publication.")
        validate_receipt(_object(json.loads(payload.decode("utf-8")), "receipt"))

        try:
            os.link(temporary, target)
        except FileExistsError as exc:
            raise ReceiptError("Receipt destination appeared during publication.") from exc
        os.unlink(temporary)

        if _read_exact_file(target) != payload:
            raise ReceiptError("Published receipt bytes do not match canonical bytes.")
        load_receipt(target)
        return {
            "status": "published",
            "path": str(target),
            "receipt_sha256": receipt["receipt_sha256"],
            "size_bytes": len(payload),
            "authority": _authority(),
        }
    except (OSError, ReceiptError, json.JSONDecodeError) as exc:
        if descriptor is not None:
            os.close(descriptor)
        if temporary.exists() and not temporary.is_symlink():
            try:
                temporary.unlink()
            except OSError:
                pass
        if isinstance(exc, ReceiptError):
            raise
        raise ReceiptError(f"Receipt publication failed: {exc}") from exc


def _read_json(path: Path, label: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise ReceiptError(f"{label} must be a regular non-symlink file.")
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReceiptError(f"{label} is not strict UTF-8 JSON.") from exc
    return _object(value, label)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export", help="Reverify and atomically export a receipt.")
    export.add_argument("--plan", type=Path, required=True)
    export.add_argument("--view-model", type=Path, required=True)
    export.add_argument("--confirmation", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify", help="Verify a self-contained receipt.")
    verify.add_argument("--receipt", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "export":
            result = publish_receipt(
                arguments.output,
                _read_json(arguments.plan, "plan"),
                _read_json(arguments.view_model, "view_model"),
                _read_json(arguments.confirmation, "confirmation"),
            )
        else:
            receipt = load_receipt(arguments.receipt)
            result = {
                "status": "verified",
                "path": str(arguments.receipt),
                "receipt_sha256": receipt["receipt_sha256"],
                "size_bytes": len(canonical_json(receipt)),
                "authority": _authority(),
            }
        sys.stdout.buffer.write(canonical_json(result))
        return 0
    except (OSError, ReceiptError, WizardContractError) as exc:
        print(f"Suite Wizard receipt failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
