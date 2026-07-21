#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
GEM_ROOT = REPO_ROOT / "Gems/TaintedGrailMerlinWorkshop"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


class MerlinWorkshopProviderRepositoryTests(unittest.TestCase):
    def test_provider_is_registered_but_not_enabled_by_default(self) -> None:
        engine = json.loads(read_text(REPO_ROOT / "engine.json"))
        project = json.loads(
            read_text(REPO_ROOT / "TaintedGrailModdingEditor/project.json")
        )
        gem = json.loads(read_text(GEM_ROOT / "gem.json"))

        self.assertEqual(
            engine["external_subdirectories"].count(
                "Gems/TaintedGrailMerlinWorkshop"
            ),
            1,
        )
        self.assertNotIn(
            "TaintedGrailMerlinWorkshop",
            project["gem_names"],
        )
        self.assertEqual(gem["type"], "Tool")
        self.assertEqual(gem["dependencies"], ["ExternalToolchain"])

    def test_descriptor_is_exactly_pinned_and_discovery_only(self) -> None:
        provider = read_text(
            GEM_ROOT / "Code/Source/MerlinWorkshopProvider.cpp"
        )
        header = read_text(
            GEM_ROOT
            / "Code/Include/TaintedGrailMerlinWorkshop/MerlinWorkshopProvider.h"
        )
        combined = provider + "\n" + header

        for fragment in (
            '"foa.merlin-workshop"',
            '"1.1.0"',
            '"v1.1.0"',
            '"073bdab3e09d6adad5003339fc49b021738d71e6"',
            '"6000.0.60f1"',
            '"61dfb374e36f"',
            "CommandMode::Probe",
            "DiscoveryProbeKind::Directory",
            'projectProbe.m_pathConfigurationKey = "project-root"',
            'projectProbe.m_versionConfigurationKey = "workshop-version"',
            "descriptor.m_enabledByDefault = false",
        ):
            self.assertIn(fragment, combined)

        self.assertEqual(
            provider.count("descriptor.m_discoveryProbes.push_back"),
            1,
        )
        self.assertNotIn("CommandMode::Interactive", provider)
        self.assertNotIn("CommandMode::Batch", provider)

    def test_provider_code_has_no_execution_or_game_authority(self) -> None:
        source_root = GEM_ROOT / "Code/Source"
        source = "\n".join(
            read_text(path)
            for path in sorted(source_root.rglob("*"))
            if path.suffix in {".cpp", ".h"}
        )
        for forbidden in (
            "QProcess",
            "ProcessWatcher",
            "CreateProcess",
            "ShellExecute",
            "WinExec",
            "std::filesystem",
            "AZ::IO",
            "FileIOBase",
            "SaveGame",
            "LaunchFoA",
            "BepInEx",
            "Harmony",
            "socket(",
            "popen(",
            "system(",
        ):
            self.assertNotIn(forbidden, source)

        component = read_text(
            source_root
            / "Editor/TaintedGrailMerlinWorkshopEditorSystemComponent.cpp"
        )
        self.assertIn(
            'required.push_back(AZ_CRC_CE("ExternalToolchainService"))',
            component,
        )
        self.assertIn(
            "ExternalToolchainRequests::RegisterProvider",
            component,
        )

    def test_tool_variant_and_documented_boundary_are_preserved(self) -> None:
        cmake = read_text(GEM_ROOT / "Code/CMakeLists.txt")
        guide = read_text(
            REPO_ROOT / "docs/tainted-grail-sdk/MERLIN_WORKSHOP_PROVIDER.md"
        )
        readme = read_text(GEM_ROOT / "README.md")

        self.assertIn("if(NOT PAL_TRAIT_BUILD_HOST_TOOLS)", cmake)
        self.assertIn(
            "ly_create_alias(NAME ${gem_name}.Tools",
            cmake,
        )
        self.assertIn(
            "ly_create_alias(NAME ${gem_name}.Builders",
            cmake,
        )
        for runtime_variant in (
            "${gem_name}.Client",
            "${gem_name}.Server",
            "${gem_name}.Unified",
        ):
            self.assertNotIn(runtime_variant, cmake)

        for fragment in (
            "optional discovery-only provider",
            "is not listed",
            "does not run Unity",
            "write to the game's mod directory",
            "Discovery success is never promoted automatically",
        ):
            self.assertIn(fragment, guide)

        self.assertIn("does not download or redistribute Merlin Workshop", readme)


if __name__ == "__main__":
    unittest.main()
