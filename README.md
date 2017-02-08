[![Build Status](https://travis-ci.org/theirix/conan-libcurl.svg)](https://travis-ci.org/theirix/conan-libcurl)


# conan-libcurl

[Conan.io](https://conan.io) package for lib cURL library

The packages generated with this **conanfile** can be found in [conan.io](https://conan.io/source/libcurl/7.52.1/theirix/stable).

## Build packages

Download conan client from [Conan.io](https://conan.io) and run:

    $ python build.py

## Upload packages to server

    $ conan upload libcurl/7.52.1@theirix/stable --all
    
## Reuse the packages

### Basic setup

    $ conan install libcurl/7.52.1@theirix/stable
    
### Project setup

If you handle multiple dependencies in your project is better to add a *conanfile.txt*
    
    [requires]
    libcurl/7.52.1@theirix/stable

    [options]
    libcurl:shared=true # false
    
    [generators]
    txt
    cmake

    [imports]
    ., cacert.pem -> ./bin

Complete the installation of requirements for your project running:</small></span>

    conan install . 

Project setup installs the library (and all his dependencies) and generates the files *conanbuildinfo.txt* and *conanbuildinfo.cmake* with all the paths and variables that you need to link with your dependencies.

