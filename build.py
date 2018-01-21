#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import platform
import copy

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=True)

    items = []
    for item in builder.items:
        # skip mingw cross-builds
        if not (platform.system() == "Windows" and item.settings["compiler"] == "gcc" and
                item.settings["arch"] == "x86"):
            items.append(item)
            # add macos builds with openssl too
            if item.settings["compiler"] == "apple-clang" and item.settings["build_type"] == "Release":
                new_options = copy.copy(item.options)
                new_options["libcurl:darwin_ssl"] = False
                items.append([item.settings, new_options, item.env_vars,
                              item.build_requires, item.reference])
    builder.items = items

    builder.run()
