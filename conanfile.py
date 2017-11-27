#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, CMake, tools
import os


class LibcurlConan(ConanFile):
    name = "libcurl"
    version = "7.56.1"
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
               "with_largemaxwritesize": [True, False]}
    default_options = "shared=False", "with_openssl=True", "disable_threads=False", \
                      "with_ldap=False", "custom_cacert=False", "darwin_ssl=True",  \
                      "with_libssh2=False", "with_libidn=False", "with_librtmp=False", \
                      "with_libmetalink=False", "with_largemaxwritesize=False"
    exports = ["FindCURL.cmake"]
    url = "http://github.com/bincrafters/conan-libcurl"
    license = "https://curl.haxx.se/docs/copyright.html"
    description = "command line tool and library for transferring data with URLs"
    short_paths = True

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.options.with_openssl:
            if self.settings.os != "Macos" or not self.options.darwin_ssl:
                self.options["OpenSSL"].shared = self.options.shared
        if self.options.with_libssh2:
            if self.settings.os != "Windows":
                self.options["libssh2"].shared = self.options.shared

        if self.settings.os != "Macos":
            try:
                self.options.remove("darwin_ssl")
            except:
                pass

    def requirements(self):
        if self.options.with_openssl:
            if self.settings.os != "Macos" or not self.options.darwin_ssl:
                self.requires.add("OpenSSL/[>1.0.2a,<1.0.3]@conan/stable", private=False)
            elif self.settings.os == "Macos" and self.options.darwin_ssl:
                self.requires.add("zlib/[~=1.2]@conan/stable", private=False)
        if self.options.with_libssh2:
            if self.settings.os != "Windows":
                self.requires.add("libssh2/[~=1.8]@bincrafters/stable", private=False)

        self.requires.add("zlib/[~=1.2]@conan/stable", private=False)

    def source(self):
        tools.get("https://curl.haxx.se/download/curl-%s.tar.gz" % self.version)
        os.rename("curl-%s" % self.version, self.name)
        tools.download("https://curl.haxx.se/ca/cacert.pem", "cacert.pem", verify=False)
        if self.settings.os != "Windows":
            self.run("chmod +x ./%s/configure" % self.name)

    def build(self):
        if self.options.with_largemaxwritesize:
            tools.replace_in_file(os.path.join(self.name, 'include', 'curl', 'curl.h'),
                                  "define CURL_MAX_WRITE_SIZE 16384", "define CURL_MAX_WRITE_SIZE 10485760")

        tools.replace_in_file('FindCURL.cmake', 'set(CURL_VERSION_STRING "0")', 'set(CURL_VERSION_STRING "%s")' % self.version, strict=True)

        if self.settings.os == "Linux" or self.settings.os == "Macos":

            suffix = " --without-libidn " if not self.options.with_libidn else "--with-libidn"
            suffix += " --without-librtmp " if not self.options.with_librtmp else "--with-librtmp"
            suffix += " --without-libmetalink " if not self.options.with_libmetalink else "--with-libmetalink"

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

            env_build = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env_build.vars):

                old_str = "-install_name \\$rpath/"
                new_str = "-install_name "
                tools.replace_in_file("%s/configure" % self.name, old_str, new_str)

                configure = "cd %s && %s ./configure %s" % (self.name, '', suffix)
                self.output.warn(configure)

                # BUG: https://github.com/curl/curl/commit/bd742adb6f13dc668ffadb2e97a40776a86dc124
                # fixed in 7.54.1: https://github.com/curl/curl/commit/338f427a24f78a717888c7c2b6b91fa831bea28e
                # so just ignore it if not matched
                tools.replace_in_file("%s/configure" % self.name, 'LDFLAGS="`$PKGCONFIG --libs-only-L zlib` $LDFLAGS"', 'LDFLAGS="$LDFLAGS `$PKGCONFIG --libs-only-L zlib`"', strict=False)

                self.output.warn(configure)
                self.run(configure)

                # temporary fix for xcode9
                # extremely fragile because make doesn't see CFLAGS from env, only from cmdline
                if self.settings.os == "Macos":
                    make_suffix = "CFLAGS=\"-Wno-unguarded-availability " + env_build.vars['CFLAGS'] + "\""
                else:
                    make_suffix = ''

                self.run("cd %s && make %s" % (self.name, make_suffix))
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
            cmake.configure(source_dir=os.path.join(self.conanfile_directory, self.name),
                            build_dir=os.path.join(self.conanfile_directory, self.name, '_build'))
            cmake.build()

    def package(self):
        self.copy(pattern="LICENSE")

        # Copy findZLIB.cmake to package
        self.copy("FindCURL.cmake", ".", ".")

        # Copying zlib.h, zutil.h, zconf.h
        self.copy("*.h", "include/curl", "%s" % self.name, keep_path=False)

        # Copy the certs to be used by client
        self.copy(pattern="cacert.pem", keep_path=False)

        # Copying static and dynamic libs
        if self.settings.os == "Windows":
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
        if self.settings.os != "Windows":
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

        if not self.options.shared:
            self.cpp_info.defines.append("CURL_STATICLIB=1")
