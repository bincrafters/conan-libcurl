#!/bin/bash

set -e
set -x

brew update || brew update
brew install cmake || true
brew install libtool || true


pip install conan --upgrade
pip install conan_package_tools bincrafters_package_tools
conan user
