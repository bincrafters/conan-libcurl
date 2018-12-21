#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os
import subprocess
import re
import platform


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if "arm" in self.settings.arch:
            if not tools.cross_building(self.settings):
                self.test_arm()
        else:
            bin_path = os.path.join("bin", "test_package")
            self.run(bin_path, run_environment=True)

    def test_arm(self):
        file_ext = "so" if self.options["libcurl"].shared else "a"
        lib_path = os.path.join(self.deps_cpp_info["libcurl"].libdirs[0], "libcurl.%s" % file_ext)
        output = subprocess.check_output(["readelf", "-h", lib_path]).decode()
        assert re.search(r"Machine:\s+ARM", output)
