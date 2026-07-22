#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Complete graphical Suite Wizard review, confirmation, and receipt host."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Sequence

import suite_wizard_host as confirmation_host
from wizard_receipt_controller import ReceiptError, WizardReceiptController

confirmation_host.impl.WizardHostController = WizardReceiptController


class SuiteWizardReceiptHost(confirmation_host.SuiteWizardHost):
    """Adds canonical receipt export and exact-current-chain verification."""

    @property
    def receipt_controller(self) -> WizardReceiptController:
        if not isinstance(self.controller, WizardReceiptController):
            raise confirmation_host.impl.WizardHostError(
                "The graphical host lacks its receipt controller."
            )
        return self.controller

    def _build_ui(self) -> None:
        super()._build_ui()
        self.receipt_tab = self.ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.receipt_tab, text="4. Receipt")
        self._build_receipt_tab()

    def _build_receipt_tab(self) -> None:
        ttk = self.ttk
        self.receipt_tab.columnconfigure(0, weight=1)
        self.receipt_tab.rowconfigure(1, weight=1)

        ttk.Label(
            self.receipt_tab,
            text=(
                "Export the exact current confirmation as a canonical create-once receipt, or "
                "verify an existing receipt against the same in-memory plan, view-model, "
                "acknowledgement set, and confirmation. This grants no install or execution authority."
            ),
            wraplength=1080,
        ).grid(row=0, column=0, sticky="ew")

        receipt_frame = ttk.LabelFrame(
            self.receipt_tab,
            text="Verified confirmation receipt",
            padding=10,
        )
        receipt_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        receipt_frame.columnconfigure(1, weight=1)

        self.receipt_hash_vars = {
            name: self.tk.StringVar()
            for name in (
                "plan_sha256",
                "view_model_sha256",
                "confirmation_sha256",
                "receipt_sha256",
            )
        }
        labels = {
            "plan_sha256": "Plan",
            "view_model_sha256": "View model",
            "confirmation_sha256": "Confirmation",
            "receipt_sha256": "Receipt",
        }
        row = 0
        for name, label in labels.items():
            ttk.Label(receipt_frame, text=f"{label}:").grid(row=row, column=0, sticky="w")
            ttk.Entry(
                receipt_frame,
                textvariable=self.receipt_hash_vars[name],
                state="readonly",
            ).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=1)
            row += 1

        ttk.Label(receipt_frame, text="Receipt path:").grid(row=row, column=0, sticky="w")
        self.receipt_path_var = self.tk.StringVar()
        ttk.Entry(
            receipt_frame,
            textvariable=self.receipt_path_var,
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=1)
        row += 1

        ttk.Label(receipt_frame, text="Receipt statement:").grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(10, 0),
        )
        row += 1
        self.receipt_statement_var = self.tk.StringVar(
            value="Create or verify the current confirmation receipt to display its statement."
        )
        ttk.Label(
            receipt_frame,
            textvariable=self.receipt_statement_var,
            wraplength=1000,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 10))
        row += 1

        actions = ttk.Frame(receipt_frame)
        actions.grid(row=row, column=0, columnspan=2, sticky="ew")
        self.export_receipt_button = ttk.Button(
            actions,
            text="Export receipt…",
            command=self.export_confirmation_receipt,
            state="disabled",
        )
        self.export_receipt_button.pack(side="left")
        self.verify_receipt_button = ttk.Button(
            actions,
            text="Verify receipt…",
            command=self.verify_confirmation_receipt,
            state="disabled",
        )
        self.verify_receipt_button.pack(side="left", padx=(8, 0))
        ttk.Button(
            actions,
            text="Back to confirmation",
            command=lambda: self.notebook.select(self.confirmation_tab),
        ).pack(side="right")
        row += 1

        self.receipt_status_var = self.tk.StringVar(
            value="Create the exact current review confirmation before exporting a receipt."
        )
        ttk.Label(
            receipt_frame,
            textvariable=self.receipt_status_var,
            wraplength=1000,
        ).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _render_confirmation(self, confirmation: dict[str, object]) -> None:
        super()._render_confirmation(confirmation)
        self._clear_receipt_display(keep_confirmation_bindings=True)
        self.receipt_status_var.set(
            "The current confirmation may now be exported or matched to an existing receipt."
        )
        self._update_receipt_buttons()

    def _clear_confirmation_display(self, *, keep_review_bindings: bool = False) -> None:
        super()._clear_confirmation_display(keep_review_bindings=keep_review_bindings)
        if hasattr(self, "receipt_hash_vars"):
            self._clear_receipt_display()
            self._update_receipt_buttons()

    def export_confirmation_receipt(self, destination: Path | None = None) -> None:
        try:
            selected = destination
            if selected is None:
                from tkinter import filedialog

                chosen = filedialog.asksaveasfilename(
                    parent=self.root,
                    title="Export FOA-SDK confirmation receipt",
                    defaultextension=".foa-receipt.json",
                    filetypes=(("FOA-SDK receipt", "*.foa-receipt.json"),),
                    initialfile="foa-sdk-review.foa-receipt.json",
                )
                if not chosen:
                    self.receipt_status_var.set("Receipt export was cancelled; no file was written.")
                    return
                selected = Path(chosen)

            receipt = self.receipt_controller.export_current_receipt(
                Path(selected),
                expected_plan_sha256=self.confirmation_hash_vars["plan_sha256"].get(),
                expected_view_model_sha256=self.confirmation_hash_vars[
                    "view_model_sha256"
                ].get(),
                expected_confirmation_sha256=self.confirmation_hash_vars[
                    "confirmation_sha256"
                ].get(),
            )
            self._render_receipt(receipt)
            self.notebook.select(self.receipt_tab)
            self.status_var.set("The exact current confirmation receipt is exported and verified.")
        except (
            OSError,
            ReceiptError,
            confirmation_host.impl.WizardContractError,
            confirmation_host.impl.WizardHostError,
        ) as exc:
            self._show_error("Receipt export failed", exc)

    def verify_confirmation_receipt(self, receipt_path: Path | None = None) -> None:
        try:
            selected = receipt_path
            if selected is None:
                from tkinter import filedialog

                chosen = filedialog.askopenfilename(
                    parent=self.root,
                    title="Verify FOA-SDK confirmation receipt",
                    filetypes=(("FOA-SDK receipt", "*.foa-receipt.json"),),
                )
                if not chosen:
                    self.receipt_status_var.set("Receipt verification was cancelled.")
                    return
                selected = Path(chosen)

            receipt = self.receipt_controller.verify_current_receipt(
                Path(selected),
                expected_plan_sha256=self.confirmation_hash_vars["plan_sha256"].get(),
                expected_view_model_sha256=self.confirmation_hash_vars[
                    "view_model_sha256"
                ].get(),
                expected_confirmation_sha256=self.confirmation_hash_vars[
                    "confirmation_sha256"
                ].get(),
            )
            self._render_receipt(receipt)
            self.notebook.select(self.receipt_tab)
            self.status_var.set("The selected receipt matches the exact current confirmation chain.")
        except (
            OSError,
            ReceiptError,
            confirmation_host.impl.WizardContractError,
            confirmation_host.impl.WizardHostError,
        ) as exc:
            self._show_error("Receipt verification failed", exc)

    def _render_receipt(self, receipt: dict[str, object]) -> None:
        for name in self.receipt_hash_vars:
            self.receipt_hash_vars[name].set(str(receipt[name]))
        self.receipt_path_var.set(str(receipt["path"]))
        self.receipt_statement_var.set(str(receipt["statement"]))
        self.receipt_status_var.set(
            f"Receipt {receipt['status']}: {receipt['size_bytes']} canonical byte(s); "
            "all operational authority remains false."
        )
        self._update_receipt_buttons()

    def _clear_receipt_display(self, *, keep_confirmation_bindings: bool = False) -> None:
        if not hasattr(self, "receipt_hash_vars"):
            return
        plan_hash = (
            self.confirmation_hash_vars["plan_sha256"].get()
            if keep_confirmation_bindings
            else ""
        )
        view_hash = (
            self.confirmation_hash_vars["view_model_sha256"].get()
            if keep_confirmation_bindings
            else ""
        )
        confirmation_hash = (
            self.confirmation_hash_vars["confirmation_sha256"].get()
            if keep_confirmation_bindings
            else ""
        )
        self.receipt_hash_vars["plan_sha256"].set(plan_hash)
        self.receipt_hash_vars["view_model_sha256"].set(view_hash)
        self.receipt_hash_vars["confirmation_sha256"].set(confirmation_hash)
        self.receipt_hash_vars["receipt_sha256"].set("")
        self.receipt_path_var.set("")
        self.receipt_statement_var.set(
            "Create or verify the current confirmation receipt to display its statement."
        )

    def _update_receipt_buttons(self) -> None:
        if not hasattr(self, "export_receipt_button"):
            return
        ready = False
        try:
            state = self.receipt_controller.confirmation_state_snapshot()
            ready = bool(
                state["confirmation_available"]
                and len(self.confirmation_hash_vars["plan_sha256"].get()) == 64
                and len(self.confirmation_hash_vars["view_model_sha256"].get()) == 64
                and len(self.confirmation_hash_vars["confirmation_sha256"].get()) == 64
            )
        except (
            confirmation_host.impl.WizardContractError,
            confirmation_host.impl.WizardHostError,
        ):
            ready = False
        state = "normal" if ready else "disabled"
        self.export_receipt_button.configure(state=state)
        self.verify_receipt_button.configure(state=state)


confirmation_host.impl.SuiteWizardHost = SuiteWizardReceiptHost
confirmation_host.impl.WizardHostController = WizardReceiptController


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Open or smoke-test the complete graphical FOA-SDK Suite Wizard review, "
            "confirmation, and receipt host."
        )
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
        help="Resolve, acknowledge, confirm, export, verify, render, and exit.",
    )
    return parser


def _smoke_test(installer_root: Path) -> int:
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except ImportError:
        print(
            "FOA-SDK Suite Wizard receipt smoke failed: Python tkinter support is unavailable.",
            file=sys.stderr,
        )
        return 1

    root = None
    try:
        controller = WizardReceiptController(installer_root)
        root = tk.Tk()
        root.withdraw()
        host = SuiteWizardReceiptHost(root, controller, tk, ttk, messagebox)
        root.update_idletasks()
        host.resolve_review()
        root.update_idletasks()

        for row in controller.acknowledgement_choices():
            acknowledgement_id = str(row["acknowledgement_id"])
            host.ack_vars[acknowledgement_id].set(True)
            host._set_acknowledgement(acknowledgement_id, True)
        host.confirmed_by_var.set("FOA-SDK graphical receipt smoke")
        host.confirmed_at_var.set("2026-07-22T00:00:00Z")
        host.create_review_confirmation()
        root.update_idletasks()

        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "smoke.foa-receipt.json"
            host.export_confirmation_receipt(destination)
            root.update_idletasks()
            receipt = controller.receipt_snapshot()
            if not destination.is_file():
                raise confirmation_host.impl.WizardHostError(
                    "Graphical receipt export did not create its destination."
                )
            if len(host.receipt_hash_vars["receipt_sha256"].get()) != 64:
                raise confirmation_host.impl.WizardHostError(
                    "Graphical receipt export did not render its fingerprint."
                )
            if receipt["receipt_sha256"] != host.receipt_hash_vars["receipt_sha256"].get():
                raise confirmation_host.impl.WizardHostError(
                    "Displayed receipt fingerprint does not match the verified receipt."
                )
            host.verify_confirmation_receipt(destination)
            root.update_idletasks()
            if controller.receipt_snapshot()["status"] != "verified":
                raise confirmation_host.impl.WizardHostError(
                    "Graphical receipt verification did not become current."
                )
            if host.notebook.index(host.notebook.select()) != 3:
                raise confirmation_host.impl.WizardHostError(
                    "Graphical receipt operation did not activate the Receipt page."
                )
        print("FOA-SDK Suite Wizard native receipt export smoke passed.")
        return 0
    except (
        OSError,
        ReceiptError,
        confirmation_host.impl.CatalogInterfaceError,
        confirmation_host.impl.ResolverError,
        confirmation_host.impl.WizardContractError,
        confirmation_host.impl.WizardHostError,
        tk.TclError,
    ) as exc:
        print(f"FOA-SDK Suite Wizard receipt smoke failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if root is not None:
            root.destroy()


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.smoke_test:
        return _smoke_test(arguments.installer_root)
    return confirmation_host.impl.main(["--installer-root", str(arguments.installer_root)])


if __name__ == "__main__":
    raise SystemExit(main())
