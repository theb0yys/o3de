/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */

#pragma once

#include "ExternalToolInterchangeContracts.h"

namespace TaintedGrailModdingSDK
{
    // Each serializer includes every contract-significant field except the
    // corresponding object's own fingerprint.
    AZStd::string SerializeCanonicalExternalToolHandoffV1(
        const ExternalToolHandoffV1& handoff);
    AZStd::string CalculateExternalToolHandoffFingerprintV1(
        const ExternalToolHandoffV1& handoff);
    bool ExternalToolHandoffFingerprintMatchesV1(
        const ExternalToolHandoffV1& handoff);

    AZStd::string SerializeCanonicalUnityConversionRequestV1(
        const UnityConversionRequestV1& request);
    AZStd::string CalculateUnityConversionRequestFingerprintV1(
        const UnityConversionRequestV1& request);
    bool UnityConversionRequestFingerprintMatchesV1(
        const UnityConversionRequestV1& request);

    AZStd::string SerializeCanonicalExternalToolExecutionResultV1(
        const ExternalToolExecutionResultV1& result);
    AZStd::string CalculateExternalToolExecutionResultFingerprintV1(
        const ExternalToolExecutionResultV1& result);
    bool ExternalToolExecutionResultFingerprintMatchesV1(
        const ExternalToolExecutionResultV1& result);

    AZStd::string SerializeCanonicalUnityConversionResultV1(
        const UnityConversionResultV1& result);
    AZStd::string CalculateUnityConversionResultFingerprintV1(
        const UnityConversionResultV1& result);
    bool UnityConversionResultFingerprintMatchesV1(
        const UnityConversionResultV1& result);
} // namespace TaintedGrailModdingSDK
