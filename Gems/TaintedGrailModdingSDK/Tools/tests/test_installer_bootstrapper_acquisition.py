# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import importlib.util
from pathlib import Path

TEST_MODULE = (
    Path(__file__).resolve().parents[4]
    / "Installer"
    / "Tests"
    / "BootstrapperAcquisition"
    / "test_bootstrapper_acquisition.py"
)
SPEC = importlib.util.spec_from_file_location(
    "foa_installer_bootstrapper_acquisition_tests",
    TEST_MODULE,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load bootstrapper acquisition tests: {TEST_MODULE}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BootstrapperAcquisitionTests = MODULE.BootstrapperAcquisitionTests
