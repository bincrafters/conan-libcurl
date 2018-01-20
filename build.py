#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=True)

    # add macos builds with openssl too
    builds = []
    for settings, options, env_vars, build_requires in builder.builds:
        builds.append([settings, options, env_vars, build_requires])
        if settings["compiler"] == "apple-clang" and settings["build_type"] == "Release":
            new_options = copy.copy(options)
            new_options["libcurl:darwin_ssl"] = False
            builds.append([settings, new_options, env_vars, build_requires])
    builder.builds = builds
    
    builder.run()
