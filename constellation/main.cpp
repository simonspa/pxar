// Copyright (c) 2026 DESY and the Constellation authors
// SPDX-License-Identifier: EUPL-1.2 OR CC0-1.0

#include <constellation/exec/cli.hpp>
#include <constellation/exec/satellite.hpp>

#include "build_vcs.hpp"

using namespace constellation::exec;

int main(int argc, char** argv) {
    return satellite_main(
        to_span(argc, argv), "SatellitePxar", SatelliteType("Pxar", VERSION_VCS, "@CMAKE_CURRENT_BINARY_DIR@"));
}
