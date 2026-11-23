# SPDX-FileCopyrightText: 2026 DESY and the Constellation authors
# SPDX-License-Identifier: CC0-1.0

find_package(Git QUIET)

if(GIT_FOUND)
    execute_process(
        COMMAND ${GIT_EXECUTABLE} describe --tags --always --dirty
        WORKING_DIRECTORY "${SRC_DIR}"
        OUTPUT_VARIABLE VCS_TAG
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
else()
    set(VCS_TAG "")
endif()

configure_file("${INPUT_FILE}" "${OUTPUT_FILE}.tmp" @ONLY)

execute_process(
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${OUTPUT_FILE}.tmp"
            "${OUTPUT_FILE}"
)

file(REMOVE "${OUTPUT_FILE}.tmp")
