#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Native graphical review entry point for the FOA-SDK Suite Wizard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import _suite_wizard_host_impl as impl


class SuiteWizardHost(impl.SuiteWizardHost):
    """Adds visible review invalidation when compatibility context changes."""

    def __init__(
        self,
        root: object,
        controller: impl.WizardHostController,
        tk: object,
        ttk: object,
        messagebox: object,
    ) -> None:
        super().__init__(root, controller, tk, ttk, messagebox)
        for variable in (
            self.platform_var,
            self.architecture_var,
            self.runtime_target_var,
            self.game_version_var,
            self.branch_var,
        ):
            variable.trace_add("write", self._on_context_changed)

    def _on_context_changed(self, *_args: object) -> None:
        self._clear_review()
        self.status_var.set(
            "Compatibility context changed; resolve again to refresh the review."
        )


impl.SuiteWizardHost = SuiteWizardHost


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open or smoke-test the graphical FOA-SDK Suite Wizard review host."
    )
    parser.add_argument(
        "--installer-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Path to the product-owned Installer directory.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Construct the native window, resolve the default review, verify rows, and exit.",
    )
    return parser


def _smoke_test(installer_root: Path) -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except ImportError:
        print(
            "FOA-SDK Suite Wizard smoke failed: Python tkinter support is unavailable.",
            file=sys.stderr,
        )
        return 1

    root = None
    try:
        controller = impl.WizardHostController(installer_root)
        root = tk.Tk()
        root.withdraw()
        host = SuiteWizardHost(root, controller, tk, ttk, messagebox)
        root.update_idletasks()
        host.resolve_review()
        root.update_idletasks()

        package_rows = host.package_tree.get_children()
        payload_rows = host.payload_tree.get_children()
        hashes = [variable.get() for variable in host.review_hash_vars.values()]
        if len(package_rows) != 2 or len(payload_rows) != 2:
            raise impl.WizardHostError(
                "Default graphical review did not render two package and payload rows."
            )
        if any(len(value) != 64 for value in hashes):
            raise impl.WizardHostError(
                "Graphical review did not render the complete exact fingerprint chain."
            )
        if host.notebook.index(host.notebook.select()) != 1:
            raise impl.WizardHostError("Graphical review did not activate the Review page.")
        print("FOA-SDK Suite Wizard native smoke passed.")
        return 0
    except (
        OSError,
        impl.CatalogInterfaceError,
        impl.ResolverError,
        impl.WizardContractError,
        impl.WizardHostError,
        tk.TclError,
    ) as exc:
        print(f"FOA-SDK Suite Wizard smoke failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if root is not None:
            root.destroy()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.smoke_test:
        return _smoke_test(arguments.installer_root)
    forwarded = ["--installer-root", str(arguments.installer_root)]
    return impl.main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
