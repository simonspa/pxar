# Build pXar executables:

INCLUDE_DIRECTORIES( . )
INCLUDE_DIRECTORIES(${PROJECT_SOURCE_DIR}/util ${PROJECT_SOURCE_DIR}/tests ${PROJECT_SOURCE_DIR}/usertests ${PROJECT_SOURCE_DIR}/gui )

SET (pXar_SOURCES
pXar.cc
)

# fill list of header files
set(pXar_HEADERS
)

SET(MY_INCLUDE_DIRECTORIES ${PROJECT_SOURCE_DIR}/main ${PROJECT_SOURCE_DIR}/core/api ${ROOT_INCLUDE_DIR} )

IF(WIN32)
  SET(PXAR_EXECUTABLE pXarW32)
ELSE(WIN32)
  SET(PXAR_EXECUTABLE pXar)
ENDIF(WIN32)

add_executable(${PXAR_EXECUTABLE} pXar.cc )
target_link_libraries(${PXAR_EXECUTABLE} ${PROJECT_NAME} ${ROOT_LIBRARIES} ${FTDI_LINK_LIBRARY} ${DEVICES_LINK_LIBRARY} pxartests pxarusertests pxargui pxarutil )

INSTALL(TARGETS ${PXAR_EXECUTABLE}
  RUNTIME DESTINATION bin
  ARCHIVE DESTINATION lib)
