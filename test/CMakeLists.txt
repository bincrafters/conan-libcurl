PROJECT(MyHello)
cmake_minimum_required(VERSION 3.0)
include(conanbuildinfo.cmake)
CONAN_BASIC_SETUP()

macro(ADD_FRAMEWORK fwname appname)
    find_library(FRAMEWORK_${fwname}
    NAMES ${fwname}
    PATHS ${CMAKE_OSX_SYSROOT}/System/Library
    PATH_SUFFIXES Frameworks
    NO_DEFAULT_PATH)
    if( ${FRAMEWORK_${fwname}} STREQUAL FRAMEWORK_${fwname}-NOTFOUND)
        MESSAGE(ERROR ": Framework ${fwname} not found")
    else()
        TARGET_LINK_LIBRARIES(${appname} "${FRAMEWORK_${fwname}}/${fwname}")
        MESSAGE(STATUS "Framework ${fwname} found at ${FRAMEWORK_${fwname}}")
    endif()
endmacro(ADD_FRAMEWORK)

ADD_EXECUTABLE(main main.c)
MESSAGE(${CONAN_LIBS})
if(APPLE)
   ADD_FRAMEWORK(Cocoa main)
   ADD_FRAMEWORK(Security main)
endif()

find_package(CURL)

if(CURL_FOUND)
	TARGET_LINK_LIBRARIES(main ${CURL_LIBRARIES})
	include_directories(${CURL_INCLUDE_DIRS})
endif()

find_package(OpenSSL)

if(OPENSSL_FOUND)
	TARGET_LINK_LIBRARIES(main ${OPENSSL_LIBRARIES})
	include_directories(${OPENSSL_INCLUDE_DIRS})
endif()

find_package(ZLIB)

if(ZLIB_FOUND)
	TARGET_LINK_LIBRARIES(main ${ZLIB_LIBRARIES})
	include_directories(${ZLIB_INCLUDE_DIRS})
endif()
