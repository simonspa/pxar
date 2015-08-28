# Add source files for the libtwitcurl library

MESSAGE("-- Building Twitter Notification support.")
SET(SOURCE_FILES "twitcurl.cpp" "oauthlib.cpp" "urlencode.cpp" "base64.cpp" "HMAC_SHA1.cpp" "SHA1.cpp")

SET(TWITTER TRUE PARENT_SCOPE)

ADD_LIBRARY(twitter SHARED ${SOURCE_FILES})
SET(TWITTER_LINK_LIBRARY twitter)
target_link_libraries(twitter ${CURL_LIBRARIES})

INSTALL(TARGETS twitter
  RUNTIME DESTINATION bin
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib)
