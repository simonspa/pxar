// SPDX-License-Identifier: EUPL-1.2 OR CC0-1.0

#include <memory>
#include <string_view>

#include <constellation/build.hpp>
#include <constellation/satellite/Satellite.hpp>

#include "PxarSatellite.hpp"

#ifdef __clang__
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
#endif

// generator function for loading satellite from shared library
extern "C" {
CNSTLN_DLL_EXPORT
std::shared_ptr<constellation::satellite::Satellite> generator(std::string_view type, std::string_view name) {
    return std::make_shared<PxarSatellite>(type, name);
}
}

#ifdef __clang__
#pragma clang diagnostic pop
#endif
