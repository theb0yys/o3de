#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
TOOL_PATH = (
    REPO_ROOT
    / "Gems"
    / "TaintedGrailModdingSDK"
    / "Tools"
    / "tainted_framework_knowledge.py"
)
SPEC = importlib.util.spec_from_file_location("tf_knowledge", TOOL_PATH)
knowledge = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(knowledge)


class TaintedFrameworkKnowledgeGenerationTests(unittest.TestCase):
    def test_generation_is_byte_stable(self) -> None:
        first = knowledge.build_documents()
        second = knowledge.build_documents()
        self.assertEqual(first, second)
        self.assertEqual(set(first), knowledge.EXPECTED_FILES)

    def test_generate_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "knowledge"
            knowledge.generate(output, replace=False)
            knowledge.verify(output)

    def test_existing_output_requires_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "knowledge"
            knowledge.generate(output, replace=False)
            with self.assertRaisesRegex(
                knowledge.TaintedFrameworkKnowledgeGenerationError,
                "Output already exists",
            ):
                knowledge.generate(output, replace=False)

    def test_replace_requires_valid_existing_pack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "knowledge"
            knowledge.generate(output, replace=False)
            (output / "knowledge.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                knowledge.TaintedFrameworkKnowledgeGenerationError,
                "Knowledge bytes drifted",
            ):
                knowledge.generate(output, replace=True)

    def test_unexpected_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "knowledge"
            knowledge.generate(output, replace=False)
            (output / "unexpected.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                knowledge.TaintedFrameworkKnowledgeGenerationError,
                "Knowledge file set mismatch",
            ):
                knowledge.verify(output)

    def test_future_schema_fixture_remains_rejected(self) -> None:
        fixture = knowledge.build_documents()["golden/fixtures.json"].decode("utf-8")
        self.assertIn('"future_schema":{"expected":"rejected","schema_version":2}', fixture)


if __name__ == "__main__":
    unittest.main()
