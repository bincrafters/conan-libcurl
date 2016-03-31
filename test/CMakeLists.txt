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
TARGET_LINK_LIBRARIES(main ${CONAN_LIBS})
