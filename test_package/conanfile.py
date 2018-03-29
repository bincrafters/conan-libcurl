#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools, RunEnvironment
import os
import subprocess
import re


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        with tools.environment_append(RunEnvironment(self).vars):
            bin_path = os.path.join("bin", "test_package")
            if self.settings.os == "Windows":
                self.run(bin_path)
            elif self.settings.os == "Macos":
                self.run("DYLD_LIBRARY_PATH=%s %s" % (os.environ.get('DYLD_LIBRARY_PATH', ''), bin_path))
            else:
                if "arm" in self.settings.arch:
                    self.test_arm()
                else:
                    self.run("LD_LIBRARY_PATH=%s %s" % (os.environ.get('LD_LIBRARY_PATH', ''), bin_path))

    def test_arm(self):
        file_ext = "so.4.4.0" if self.options["libcurl"].shared else "a"
        lib_path = os.path.join(self.deps_cpp_info["libcurl"].libdirs[0], "libcurl.%s" % file_ext)
        output = subprocess.check_output(["readelf", "-h", lib_path]).decode()
        assert re.search(r"Machine:\s+ARM", output)
