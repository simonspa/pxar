# Find Constellation via pkg-config
find_package(PkgConfig REQUIRED)
pkg_check_modules(CNSTLN_SAT REQUIRED ConstellationSatellite)
pkg_check_modules(CNSTLN_EXEC REQUIRED ConstellationExec)

# Create shared library for satellite
add_library(PxarSatellite SHARED "PxarSatellite.cpp" "generator.cpp")

# Add internal dependencies
target_link_libraries(PxarSatellite PUBLIC ${PROJECT_NAME})

# Ensure compilation with (at least) C++20
set_target_properties(PxarSatellite PROPERTIES CXX_STANDARD 20)

# Add Constellation dependencies
target_include_directories(PxarSatellite PUBLIC ${CNSTLN_SAT_INCLUDE_DIRS})
target_link_directories(PxarSatellite PUBLIC ${CNSTLN_SAT_LIBRARY_DIRS})
target_link_libraries(PxarSatellite PUBLIC ${CNSTLN_SAT_LIBRARIES})
target_compile_options(PxarSatellite PUBLIC ${CNSTLN_SAT_CFLAGS_OTHER})

# Set library output name to satellite type (used in `Satellite -t`)
set_target_properties(PxarSatellite PROPERTIES LIBRARY_OUTPUT_NAME "Pxar")

# Install satellite to Constellation prefix
set(CNSTLN_SAT_INSTALL_DIR "${CNSTLN_EXEC_LIBDIR}/ConstellationSatellites")
message(STATUS "Installing satellite to: \"${CNSTLN_SAT_INSTALL_DIR}\"")
install(TARGETS
    PxarSatellite
    LIBRARY DESTINATION ${CNSTLN_SAT_INSTALL_DIR}
)
