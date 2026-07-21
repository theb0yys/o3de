#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Shared deterministic Actor/Troop population-fixture contract surface."""

from population_preview_fixture_common import (
    ACTOR_LEADER_ID,
    ACTOR_SCOUT_ID,
    BRANCH,
    CATALOG_PATH,
    EVIDENCE_DOCUMENT_PATH,
    EXPECTED_FILE_PATHS,
    EXPECTED_STATE,
    FIXTURE_ID,
    GAME_VERSION,
    MANIFEST_NAME,
    MEMBER_LEADER_ID,
    MEMBER_SCOUT_ID,
    PACK_ID,
    PACK_PATH,
    PROFILE_ID,
    PopulationFixtureError,
    RELATIONSHIP_LEADER_TEMPLATE_ID,
    RUNTIME_TARGET,
    SOURCE_DOCUMENT_PATH,
    SOURCE_ID,
    SOURCE_INPUT_PATH,
    TEMPLATE_GUARD_ID,
    TROOP_PATROL_ID,
    UNRESOLVED_TEMPLATE_SUBJECT,
    WORKSPACE_ID,
    WORKSPACE_PATH,
    assert_public_synthetic_content,
    atomic_write,
    canonical_json_bytes,
    ensure_no_symlinks,
    is_reserved_population_subject,
    load_json,
    normalize_relative_path,
    require,
    require_list,
    require_sorted_unique,
    require_stable_id,
    require_string,
    sha256_bytes,
)
from population_preview_fixture_evidence import (
    require_evidence_subjects,
    validate_record,
    validate_source_and_evidence,
)
from population_preview_fixture_templates import (
    build_manifest,
    manifest_paths,
    template_documents,
    validate_pack,
    validate_workspace,
)
