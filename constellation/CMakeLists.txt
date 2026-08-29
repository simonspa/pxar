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
set_target_properties(PxarSatellite PROPERTIES INSTALL_RPATH_USE_LINK_PATH TRUE)

# Set library output name to satellite type (used in `Satellite -t`)
set_target_properties(PxarSatellite PROPERTIES LIBRARY_OUTPUT_NAME "Pxar")


# Configure main.cpp to load DSO from build directory
configure_file("main.cpp" "main.cpp" @ONLY)

# Create executable for satellite
add_executable(SatellitePxar "${CMAKE_CURRENT_BINARY_DIR}/main.cpp")


# Add internal dependencies
target_link_libraries(SatellitePxar PUBLIC ${PROJECT_NAME})

# Ensure compilation with (at least) C++20
set_target_properties(SatellitePxar PROPERTIES CXX_STANDARD 20)

# Add Constellation dependencies
target_include_directories(SatellitePxar PUBLIC ${CNSTLN_EXEC_INCLUDE_DIRS})
target_link_directories(SatellitePxar PUBLIC ${CNSTLN_EXEC_LIBRARY_DIRS})
target_link_libraries(SatellitePxar PUBLIC ${CNSTLN_EXEC_LIBRARIES})
target_compile_options(SatellitePxar PUBLIC ${CNSTLN_EXEC_CFLAGS_OTHER})
set_target_properties(SatellitePxar PROPERTIES INSTALL_RPATH_USE_LINK_PATH TRUE)

# Get Constellation prefix for library and executable
set(CNSTLN_SAT_LIB_INSTALL_DIR "${CNSTLN_EXEC_LIBDIR}/ConstellationSatellites")
pkg_get_variable(CNSTLN_SAT_EXEC_INSTALL_DIR ConstellationExec bindir)

# Install library and executable
message(STATUS "Installing satellite library to: \"${CNSTLN_SAT_LIB_INSTALL_DIR}\"")
message(STATUS "Installing satellite executable to: \"${CNSTLN_SAT_EXEC_INSTALL_DIR}\"")
install(TARGETS
    PxarSatellite
    SatellitePxar
    LIBRARY DESTINATION ${CNSTLN_SAT_LIB_INSTALL_DIR}
    RUNTIME DESTINATION ${CNSTLN_SAT_EXEC_INSTALL_DIR}
)
