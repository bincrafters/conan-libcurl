from conan.packager import ConanMultiPackager
import platform

if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add_common_builds(pure_c=True, shared_option_name="libcurl:shared")
    accepted_builds = []
    if platform.system() == "Linux": 
        for build in builder.builds:
            if build.settings["arch"] != "x86":
                build.options['OpenSSL:no_electric_fence'] = True
                accepted_builds.append(build)
        builder.builds = accepted_builds

    if platform.system() == "Darwin": 
        for build in builder.builds:
            if not build.settings["arch"] == "x86":
                build.options['OpenSSL:no_electric_fence'] = True
                accepted_builds.append(build)

        builder.builds = accepted_builds
        for compiler in builder.apple_clang_versions:
            builder.add({"compiler": "apple-clang", "compiler.version": compiler, 
                         "arch": "x86_64", "build_type": "Release"}, {"libcurl:shared": False,
                                                                  "libcurl:darwin_ssl": False,
                                                                  "libcurl:custom_cacert": True})
            builder.add({"compiler": "apple-clang", "compiler.version": compiler, 
                         "arch": "x86_64", "build_type": "Debug"}, {"libcurl:shared": False,
                                                                  "libcurl:darwin_ssl": False,
                                                           "libcurl:custom_cacert": True})
    builder.run()
