#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import platform
import copy
import os

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=True)

    items = []
    for item in builder.items:
        # skip mingw cross-builds
        if not (platform.system() == "Windows" and item.settings["compiler"] == "gcc" and
                item.settings["arch"] == "x86"):
            new_build_requires = copy.copy(item.build_requires)
            if platform.system() == "Windows" and item.settings["compiler"] == "gcc":
                # add msys2 and mingw as a build requirement for mingw builds
                new_build_requires["*"] = new_build_requires.get("*", []) + \
                    ["mingw_installer/1.0@conan/stable",
                     "msys2_installer/latest@bincrafters/stable"]

            items.append([item.settings, item.options, item.env_vars,
                          new_build_requires, item.reference])
            # add macos builds with openssl too
            if item.settings["compiler"] == "apple-clang" and item.settings["build_type"] == "Release":
                new_options = copy.copy(item.options)
                new_options["libcurl:darwin_ssl"] = False
                items.append([item.settings, new_options, item.env_vars,
                              new_build_requires, item.reference])
    builder.items = items

    if os.getenv("_CONAN_TARGET_OS", None):
        # Add non-shared builds with specific target OS
        items = []
        for item in builder.items:
            if item.options["libcurl:shared"] == False:
                new_settings = copy.copy(item.settings)
                new_settings["os"] = os.getenv("_CONAN_TARGET_OS")
                new_options = copy.copy(item.options)
                new_options["libcurl:with_openssl"] = False

                items.append([new_settings, new_options, item.env_vars,
                    item.build_requires, item.reference])

        builder.items = items

    builder.run()
