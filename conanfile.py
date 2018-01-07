#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, RunEnvironment, CMake, tools
import os


class LibcurlConan(ConanFile):
    name = "libcurl"
    version = "7.52.1"
    generators = "cmake", "txt"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], # SHARED IN LINUX IS HAVING PROBLEMS WITH LIBEFENCE
               "with_openssl": [True, False],
               "disable_threads": [True, False],
               "with_ldap": [True, False],
               "custom_cacert": [True, False],
               "darwin_ssl": [True, False],
               "with_libssh2": [True, False],
               "with_libidn": [True, False],
               "with_librtmp": [True, False],
               "with_libmetalink": [True, False],
               "with_libpsl": [True, False],
               "with_largemaxwritesize": [True, False],
               "with_nghttp2": [True, False]}
    default_options = ("shared=False", "with_openssl=True", "disable_threads=False",
                       "with_ldap=False", "custom_cacert=False", "darwin_ssl=True",
                       "with_libssh2=False", "with_libidn=False", "with_librtmp=False",
                       "with_libmetalink=False", "with_largemaxwritesize=False",
                       "with_libpsl=False", "with_nghttp2=False")
    exports = ["LICENSE.md"]
    exports_sources = ["FindCURL.cmake"]
    url = "http://github.com/bincrafters/conan-libcurl"
    license = "https://curl.haxx.se/docs/copyright.html"
    website = "https://curl.haxx.se"
    description = "command line tool and library for transferring data with URLs"
    short_paths = True

    def config_options(self):
        version_components = self.version.split('.')

        del self.settings.compiler.libcxx
        if self.options.with_openssl:
            if self.settings.os != "Macos" or not self.options.darwin_ssl:
                self.options["OpenSSL"].shared = self.options.shared
        if self.options.with_libssh2:
            if self.settings.compiler != "Visual Studio":
                self.options["libssh2"].shared = self.options.shared

        if self.settings.os != "Macos":
            try:
                self.options.remove("darwin_ssl")
            except:
                pass

        # libpsl is supported for libcurl >= 7.46.0
        use_libpsl = int(version_components[0]) == 7 and int(version_components[1]) >= 46
        if not use_libpsl:
            self.options.remove('with_libpsl')

    def requirements(self):
        if self.options.with_openssl:
            if self.settings.os != "Macos" or not self.options.darwin_ssl:
                self.requires.add("OpenSSL/[>1.0.2a,<1.0.3]@conan/stable", private=False)
            elif self.settings.os == "Macos" and self.options.darwin_ssl:
                self.requires.add("zlib/[~=1.2]@conan/stable", private=False)
        if self.options.with_libssh2:
            if self.settings.compiler != "Visual Studio":
                self.requires.add("libssh2/[~=1.8]@bincrafters/stable", private=False)

        self.requires.add("zlib/[~=1.2]@conan/stable", private=False)

    def source(self):
        tools.get("https://curl.haxx.se/download/curl-%s.tar.gz" % self.version)
        os.rename("curl-%s" % self.version, self.name)
        tools.download("https://curl.haxx.se/ca/cacert.pem", "cacert.pem", verify=False)
        if self.settings.compiler != "Visual Studio":
            self.run("chmod +x ./%s/configure" % self.name)

    def build(self):
        version_components = self.version.split('.')

        if self.options.with_largemaxwritesize:
            tools.replace_in_file(os.path.join(self.name, 'include', 'curl', 'curl.h'),
                                  "define CURL_MAX_WRITE_SIZE 16384", "define CURL_MAX_WRITE_SIZE 10485760")

        tools.replace_in_file('FindCURL.cmake', 'set(CURL_VERSION_STRING "0")', 'set(CURL_VERSION_STRING "%s")' % self.version, strict=True)

        # temporary workaround for DEBUG_POSTFIX (curl issues #1796, #2121)
        tools.replace_in_file(os.path.join(self.name, 'lib', 'CMakeLists.txt'), '  DEBUG_POSTFIX "-d"', '  DEBUG_POSTFIX ""', strict=False)

        use_cmake = self.settings.compiler == "Visual Studio"

        if not use_cmake:

            suffix = ''
            use_idn2 = int(version_components[0]) == 7 and int(version_components[1]) >= 53
            if use_idn2:
                suffix += " --without-libidn2 " if not self.options.with_libidn else " --with-libidn2 "
            else:
                suffix += " --without-libidn " if not self.options.with_libidn else " --with-libidn "
            suffix += " --without-librtmp " if not self.options.with_librtmp else " --with-librtmp "
            suffix += " --without-libmetalink " if not self.options.with_libmetalink else " --with-libmetalink "
            use_libpsl = int(version_components[0]) == 7 and int(version_components[1]) >= 46
            if use_libpsl:
                suffix += " --without-libpsl " if not self.options.with_libpsl else " --with-libpsl "
            suffix += " --without-nghttp2 " if not self.options.with_nghttp2 else " --with-nghttp2 "

            if self.options.with_openssl:
                if self.settings.os == "Macos" and self.options.darwin_ssl:
                    suffix += "--with-darwinssl "
                else:
                    suffix += "--with-ssl "
            else:
                suffix += "--without-ssl "

            if self.options.with_libssh2:
                suffix += "--with-libssh2=%s " % self.deps_cpp_info["libssh2"].lib_paths[0]
            else:
                suffix += " --without-libssh2 "

            suffix += "--with-zlib=%s " % self.deps_cpp_info["zlib"].lib_paths[0]

            if not self.options.shared:
                suffix += " --disable-shared"

            if self.options.disable_threads:
                suffix += " --disable-thread"

            if not self.options.with_ldap:
                suffix += " --disable-ldap"

            if self.options.custom_cacert:
                suffix += ' --with-ca-bundle=cacert.pem'

            # for mingw
            if self.settings.os == "Windows" and self.settings.compiler == "gcc":
                if self.settings.arch == "x86_64":
                    suffix += ' --host=x86_64-w64-mingw32'
                if self.settings.arch == "x86":
                    suffix += ' --build=i686-w64-mingw32'
                    suffix += ' --host=i686-w64-mingw32'

            env_build = AutoToolsBuildEnvironment(self)

            self.output.warn(repr(env_build.vars))

            with tools.environment_append(env_build.vars):

                # run configure with *LD_LIBRARY_PATH env vars
                # it allows to pick up shared openssl
                with tools.environment_append(RunEnvironment(self).vars):

                    with tools.chdir(self.name):
                        # disable rpath build
                        tools.replace_in_file("configure", r"-install_name \$rpath/", "-install_name ")

                        # BUG: https://github.com/curl/curl/commit/bd742adb6f13dc668ffadb2e97a40776a86dc124
                        # fixed in 7.54.1: https://github.com/curl/curl/commit/338f427a24f78a717888c7c2b6b91fa831bea28e
                        # so just ignore it if not matched
                        tools.replace_in_file("configure",
                                              'LDFLAGS="`$PKGCONFIG --libs-only-L zlib` $LDFLAGS"',
                                              'LDFLAGS="$LDFLAGS `$PKGCONFIG --libs-only-L zlib`"',
                                              strict=False)

                        cmd = "./configure %s" % suffix
                        self.output.warn(cmd)
                        if self.settings.os == "Windows":
                            tools.run_in_windows_bash(self, cmd)
                        else:
                            self.run(cmd)

                        # temporary fix for xcode9
                        # extremely fragile because make doesn't see CFLAGS from env, only from cmdline
                        if self.settings.os == "Macos":
                            make_suffix = "CFLAGS=\"-Wno-unguarded-availability " + env_build.vars['CFLAGS'] + "\""
                        else:
                            make_suffix = ''

                        cmd = "make %s" % make_suffix
                        self.output.warn(cmd)
                        if self.settings.os == "Windows":
                            tools.run_in_windows_bash(self, cmd)
                        else:
                            self.run(cmd)
        else:
            # Do not compile curl tool, just library
            conan_magic_lines = '''project(CURL)
cmake_minimum_required(VERSION 3.0)
include(../conanbuildinfo.cmake)
CONAN_BASIC_SETUP()
'''
            tools.replace_in_file("%s/CMakeLists.txt" % self.name, "cmake_minimum_required(VERSION 2.8 FATAL_ERROR)", conan_magic_lines)
            tools.replace_in_file("%s/CMakeLists.txt" % self.name, "project( CURL C )", "")
            tools.replace_in_file("%s/CMakeLists.txt" % self.name, "include(CurlSymbolHiding)", "")

            tools.replace_in_file("%s/src/CMakeLists.txt" % self.name, "add_executable(", "IF(0)\n add_executable(")
            tools.replace_in_file("%s/src/CMakeLists.txt" % self.name, "install(TARGETS ${EXE_NAME} DESTINATION bin)", "ENDIF()") # EOF

            tools.mkdir(os.path.join(self.name, '_build'))

            cmake = CMake(self)
            cmake.definitions['BUILD_TESTING'] = False
            cmake.definitions['CURL_DISABLE_LDAP'] = not self.options.with_ldap
            cmake.definitions['BUILD_SHARED_LIBS'] = self.options.shared
            cmake.definitions['CURL_STATICLIB'] = not self.options.shared
            cmake.definitions['CMAKE_DEBUG_POSTFIX'] = ''
            cmake.configure(source_dir=os.path.join(self.build_folder, self.name),
                            build_dir=os.path.join(self.build_folder, self.name, '_build'))
            cmake.build()

    def package(self):
        # debug
        for dirpath, dirs, files in os.walk(self.name):
            for f in files:
                self.output.warn(dirpath+'/'+f)

        self.copy("libcurl/COPYING", dst="licenses", ignore_case=True, keep_path=False)

        # Copy findZLIB.cmake to package
        self.copy("FindCURL.cmake", ".", ".")

        # Copying zlib.h, zutil.h, zconf.h
        self.copy("*.h", "include/curl", "%s" % self.name, keep_path=False)

        # Copy the certs to be used by client
        self.copy(pattern="cacert.pem", keep_path=False)

        # Copying static and dynamic libs
        if self.settings.compiler == "Visual Studio":
            if self.options.shared:
                self.copy(pattern="*.dll", dst="bin", src=self.name, keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src=self.name, keep_path=False)
        else:
            if self.options.shared:
                if self.settings.os == "Macos":
                    self.copy(pattern="*.dylib", dst="lib", keep_path=False, links=True)
                else:
                    self.copy(pattern="*.so*", dst="lib", src=self.name, keep_path=False, links=True)
            else:
                self.copy(pattern="*.a", dst="lib", src=self.name, keep_path=False, links=True)

    def package_info(self):
        if self.settings.compiler != "Visual Studio":
            self.cpp_info.libs = ['curl']
            if self.settings.os == "Linux":
                self.cpp_info.libs.extend(["rt", "pthread"])
                if self.options.with_libssh2:
                    self.cpp_info.libs.extend(["ssh2"])
                if self.options.with_libidn:
                    self.cpp_info.libs.extend(["idn"])
                if self.options.with_librtmp:
                    self.cpp_info.libs.extend(["rtmp"])
            if self.settings.os == "Macos":
                if self.options.with_ldap:
                    self.cpp_info.libs.extend(["ldap"])
                if self.options.darwin_ssl:
                    # self.cpp_info.libs.extend(["/System/Library/Frameworks/Cocoa.framework", "/System/Library/Frameworks/Security.framework"])
                    self.cpp_info.exelinkflags.append("-framework Cocoa")
                    self.cpp_info.exelinkflags.append("-framework Security")
                    self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
        else:
            self.cpp_info.libs = ['libcurl_imp'] if self.options.shared else ['libcurl']
            self.cpp_info.libs.append('Ws2_32')
            if self.options.with_ldap:
                self.cpp_info.libs.append("wldap32")
            if self.options.with_openssl:
                self.cpp_info.libs.extend(self.deps_cpp_info['OpenSSL'].libs)

        if not self.options.shared:
            self.cpp_info.defines.append("CURL_STATICLIB=1")
