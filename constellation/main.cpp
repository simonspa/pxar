// Copyright (c) 2025 DESY and the Constellation authors
// SPDX-License-Identifier: EUPL-1.2 OR CC0-1.0

#include <constellation/exec/cli.hpp>
#include <constellation/exec/satellite.hpp>

using namespace constellation::exec;

int main(int argc, char** argv) {
    return satellite_main(to_span(argc, argv), "SatelliteTemplate", SatelliteType("Template", "@CMAKE_CURRENT_BINARY_DIR@"));
}
