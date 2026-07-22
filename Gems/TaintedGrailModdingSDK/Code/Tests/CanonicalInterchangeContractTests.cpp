/*
 * Copyright (c) Contributors to the Open 3D Engine Project.
 * For complete copyright and license terms please see the LICENSE at the root of this distribution.
 *
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 */
#include <AzTest/AzTest.h>

#include "CanonicalInterchangeCanonical.h"
#include "CanonicalInterchangeTypes.h"

#include <cmath>
#include <limits>

namespace TaintedGrailModdingSDK::Interchange
{
    TEST(CanonicalInterchangeContractTests, FixedBasisUsesAcceptedHyphenatedTokens)
    {
        const CanonicalSpatialBasisV1 basis;
        EXPECT_EQ(basis.m_handedness, "right-handed");
        EXPECT_EQ(basis.m_vectorConvention, "column-vector");
        EXPECT_EQ(basis.m_multiplicationConvention, "matrix-on-left");
        EXPECT_EQ(basis.m_storageOrder, "column-major");
    }

    TEST(CanonicalInterchangeContractTests, ExactVersionGrammarFailsClosed)
    {
        EXPECT_TRUE(IsExactVersionTokenV1("v1.2.3"));
        EXPECT_TRUE(IsExactVersionTokenV1("release-1"));
        EXPECT_FALSE(IsExactVersionTokenV1("1.2.3"));
        EXPECT_FALSE(IsExactVersionTokenV1(".v1"));
        EXPECT_FALSE(IsExactVersionTokenV1("v1..2"));
        EXPECT_FALSE(IsExactVersionTokenV1("v1-"));
        EXPECT_FALSE(IsExactVersionTokenV1("V1.2.3"));
    }

    TEST(CanonicalInterchangeContractTests, FiniteNumbersUseShortestRoundTripBytes)
    {
        AZStd::string output;
        EXPECT_TRUE(FormatCanonicalFiniteNumberV1(0.0, output));
        EXPECT_EQ(output, "0");
        EXPECT_TRUE(FormatCanonicalFiniteNumberV1(-0.0, output));
        EXPECT_EQ(output, "0");
        EXPECT_TRUE(FormatCanonicalFiniteNumberV1(1.0, output));
        EXPECT_EQ(output, "1");
        EXPECT_TRUE(FormatCanonicalFiniteNumberV1(0.1, output));
        EXPECT_EQ(output, "0.1");
        EXPECT_TRUE(FormatCanonicalFiniteNumberV1(1000000.0, output));
        EXPECT_EQ(output, "1e6");
        EXPECT_TRUE(FormatCanonicalFiniteNumberV1(std::nextafter(1.0, 2.0), output));
        EXPECT_EQ(output, "1.0000000000000002");
        EXPECT_FALSE(FormatCanonicalFiniteNumberV1(std::numeric_limits<double>::infinity(), output));
        EXPECT_FALSE(FormatCanonicalFiniteNumberV1(std::numeric_limits<double>::quiet_NaN(), output));
    }

    TEST(CanonicalInterchangeContractTests, DefaultManifestSerializesAcceptedBasisTokens)
    {
        CanonicalInterchangeManifestV1 manifest;
        manifest.m_packageId.m_value = "package.foa-sdk.fixture";
        manifest.m_packId = "pack.foa-sdk.fixture";
        const AZStd::string canonical = SerializeCanonicalManifestV1(manifest);
        EXPECT_NE(canonical.find("\"handedness\":\"right-handed\""), AZStd::string::npos);
        EXPECT_NE(canonical.find("\"vector_convention\":\"column-vector\""), AZStd::string::npos);
        EXPECT_NE(canonical.find("\"multiplication_convention\":\"matrix-on-left\""), AZStd::string::npos);
        EXPECT_NE(canonical.find("\"storage_order\":\"column-major\""), AZStd::string::npos);
    }
} // namespace TaintedGrailModdingSDK::Interchange
