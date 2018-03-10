#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, RunEnvironment, CMake, tools
import os
import shutil


class LibcurlConan(ConanFile):
    name = "libcurl"
    version = "7.52.1"
    description = "command line tool and library for transferring data with URLs"
    url = "http://github.com/bincrafters/conan-libcurl"
    homepage = "http://curl.haxx.se"
    license = "MIT"
    short_paths = True
    exports = ["LICENSE.md"]
    exports_sources = ["FindCURL.cmake", "lib_Makefile_add.am", "CMakeLists.txt"]
    generators = "cmake"
    source_subfolder = "source_subfolder"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
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

    @property
    def is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler != "Visual Studio"

    @property
    def version_components(self):
        return [int(x) for x in self.version.split('.')]

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.options.with_openssl:
            # enforce shared linking due to openssl dependency
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
        use_libpsl = self.version_components[0] == 7 and self.version_components[1] >= 46
        if not use_libpsl:
            self.options.remove('with_libpsl')

    def build_requirements(self):
        if self.settings.os == "Windows" and self.settings.compiler != "Visual Studio":
            self.build_requires("mingw_installer/1.0@conan/stable")
            self.build_requires("msys2_installer/latest@bincrafters/stable")

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
        os.rename("curl-%s" % self.version, self.source_subfolder)
        tools.download("https://curl.haxx.se/ca/cacert.pem", "cacert.pem", verify=False)
        os.rename(os.path.join(self.source_subfolder, "CMakeLists.txt"),
                  os.path.join(self.source_subfolder, "CMakeLists_original.txt"))
        shutil.copy("CMakeLists.txt",
                    os.path.join(self.source_subfolder, "CMakeLists.txt"))

    def build(self):
        self.patch_misc_files()
        if self.settings.compiler != "Visual Studio":
            self.build_with_autotools()
        else:
            self.build_with_cmake()

    def package(self):
        # Everything is already installed by make install
        self.copy("FindCURL.cmake")
        self.copy(pattern="COPYING*", dst="licenses", src=self.source_subfolder, ignore_case=True, keep_path=False)

        # Copy the certs to be used by client
        self.copy("cacert.pem", keep_path=False)

        if self.settings.os == "Windows" and self.settings.compiler != "Visual Studio":
            # Handle only mingw libs
            self.copy(pattern="*.dll", dst="bin", keep_path=False)
            self.copy(pattern="*dll.a", dst="lib", keep_path=False)
            self.copy(pattern="*.def", dst="lib", keep_path=False)
            self.copy(pattern="*.lib", dst="lib", keep_path=False)

        # no need to distribute docs/man pages
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'man'), ignore_errors=True)
        # no need for bin tools
        for binname in ['curl', 'curl.exe']:
            if os.path.isfile(os.path.join(self.package_folder, 'bin', binname)):
                os.remove(os.path.join(self.package_folder, 'bin', binname))

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

    def patch_misc_files(self):
        if self.options.with_largemaxwritesize:
            tools.replace_in_file(os.path.join(self.source_subfolder, 'include', 'curl', 'curl.h'),
                                  "define CURL_MAX_WRITE_SIZE 16384",
                                  "define CURL_MAX_WRITE_SIZE 10485760")

        tools.replace_in_file('FindCURL.cmake',
                              'set(CURL_VERSION_STRING "0")',
                              'set(CURL_VERSION_STRING "%s")' % self.version)

        # temporary workaround for DEBUG_POSTFIX (curl issues #1796, #2121)
        # introduced in 7.55.0
        if self.version_components[0] == 7 and self.version_components[1] >= 55:
            tools.replace_in_file(os.path.join(self.source_subfolder, 'lib', 'CMakeLists.txt'),
                                  '  DEBUG_POSTFIX "-d"',
                                  '  DEBUG_POSTFIX ""')

    def get_configure_command_suffix(self):
        suffix = ''
        use_idn2 = self.version_components[0] == 7 and self.version_components[1] >= 53
        if use_idn2:
            suffix += " --without-libidn2 " if not self.options.with_libidn else " --with-libidn2 "
        else:
            suffix += " --without-libidn " if not self.options.with_libidn else " --with-libidn "
        suffix += " --without-librtmp " if not self.options.with_librtmp else " --with-librtmp "
        suffix += " --without-libmetalink " if not self.options.with_libmetalink else " --with-libmetalink "
        suffix += " --without-libpsl " if not self.options.with_libpsl else " --with-libpsl "
        suffix += " --without-nghttp2 " if not self.options.with_nghttp2 else " --with-nghttp2 "

        if self.settings.os != "Macos" or not self.options.darwin_ssl:
            openssl_path = self.deps_cpp_info["OpenSSL"].rootpath.replace('\\', '/')

        if self.options.with_openssl:
            if self.settings.os == "Macos" and self.options.darwin_ssl:
                suffix += "--with-darwinssl "
            else:
                suffix += "--with-ssl=%s" % openssl_path
        else:
            suffix += "--without-ssl "

        if self.options.with_libssh2:
            suffix += "--with-libssh2=%s " % self.deps_cpp_info["libssh2"].lib_paths[0].replace('\\', '/')
        else:
            suffix += " --without-libssh2 "

        suffix += "--with-zlib=%s " % self.deps_cpp_info["zlib"].lib_paths[0].replace('\\', '/')

        if not self.options.shared:
            suffix += " --disable-shared"
            suffix += " --enable-static"
        else:
            suffix += " --enable-shared"
            suffix += " --disable-static"

        if self.options.disable_threads:
            suffix += " --disable-thread"

        if not self.options.with_ldap:
            suffix += " --disable-ldap"

        if self.options.custom_cacert:
            suffix += ' --with-ca-bundle=cacert.pem'

        suffix += ' --prefix=%s' % self.package_folder.replace('\\', '/')

        # for mingw
        if self.is_mingw:
            if self.settings.arch == "x86_64":
                suffix += ' --build=x86_64-w64-mingw32'
                suffix += ' --host=x86_64-w64-mingw32'
            if self.settings.arch == "x86":
                suffix += ' --build=i686-w64-mingw32'
                suffix += ' --host=i686-w64-mingw32'

        return suffix

    def patch_mingw_files(self):
        if not self.is_mingw:
            return
        # patch autotools files
        with tools.chdir(self.source_subfolder):
            # for mingw builds - do not compile curl tool, just library
            # linking errors are much harder to fix than to exclude curl tool
            if self.version_components[0] == 7 and self.version_components[1] >= 55:
                tools.replace_in_file("Makefile.am",
                                      'SUBDIRS = lib src',
                                      'SUBDIRS = lib')
            else:
                tools.replace_in_file("Makefile.am",
                                      'SUBDIRS = lib src include',
                                      'SUBDIRS = lib include')

            tools.replace_in_file("Makefile.am",
                                  'include src/Makefile.inc',
                                  '')

            # patch for zlib naming in mingw
            tools.replace_in_file("configure.ac",
                                  '-lz ',
                                  '-lzlib ')

            if self.options.shared:
                # patch for shared mingw build
                tools.replace_in_file(os.path.join('lib', 'Makefile.am'),
                                      'noinst_LTLIBRARIES = libcurlu.la',
                                      '')
                tools.replace_in_file(os.path.join('lib', 'Makefile.am'),
                                      'noinst_LTLIBRARIES =',
                                      '')
                tools.replace_in_file(os.path.join('lib', 'Makefile.am'),
                                      'lib_LTLIBRARIES = libcurl.la',
                                      'noinst_LTLIBRARIES = libcurl.la')
                # add directives to build dll
                added_content = tools.load(os.path.join(self.source_folder, 'lib_Makefile_add.am'))
                tools.save(os.path.join('lib', 'Makefile.am'), added_content, append=True)


    def build_with_autotools(self):

        configure_suffix = self.get_configure_command_suffix()
        env_build = AutoToolsBuildEnvironment(self, win_bash=self.is_mingw)
        env_build_vars = env_build.vars

        # tweaks for mingw
        if self.is_mingw:
            # patch autotools files
            self.patch_mingw_files()

            env_build.defines.append('_AMD64_')
            env_build_vars['RCFLAGS'] = '-O COFF'
            if self.settings.arch == "x86":
                env_build_vars['RCFLAGS'] += ' --target=pe-i386'
            else:
                env_build_vars['RCFLAGS'] += ' --target=pe-x86-64'

            del env_build_vars['LIBS']

        self.output.warn(repr(env_build_vars))

        with tools.environment_append(env_build_vars):
            # temporary fix for xcode9
            # extremely fragile because make doesn't see CFLAGS from env, only from cmdline
            if self.settings.os == "Macos":
                make_suffix = "CFLAGS=\"-Wno-unguarded-availability " + env_build.vars['CFLAGS'] + "\""
            else:
                make_suffix = ''

            env_run = RunEnvironment(self)
            # run configure with *LD_LIBRARY_PATH env vars
            # it allows to pick up shared openssl
            self.output.warn(repr(env_run.vars))
            with tools.environment_append(env_run.vars):

                with tools.chdir(self.source_subfolder):
                    # autoreconf
                    self.run('./buildconf', win_bash=self.is_mingw)

                    # fix generated autotools files
                    tools.replace_in_file("configure", "-install_name \\$rpath/", "-install_name ")
                    # BUG: https://github.com/curl/curl/commit/bd742adb6f13dc668ffadb2e97a40776a86dc124
                    # fixed in 7.54.1: https://github.com/curl/curl/commit/338f427a24f78a717888c7c2b6b91fa831bea28e
                    if self.version_components[0] == 7 and self.version_components[1] < 55:
                        tools.replace_in_file(
                            "configure",
                            'LDFLAGS="`$PKGCONFIG --libs-only-L zlib` $LDFLAGS"',
                            'LDFLAGS="$LDFLAGS `$PKGCONFIG --libs-only-L zlib`"')

                    self.run("chmod +x configure")
                    self.run("./configure " + configure_suffix, win_bash=self.is_mingw)
                    self.run("make %s" % make_suffix, win_bash=self.is_mingw)
                    self.run("make %s install" % make_suffix, win_bash=self.is_mingw)

    def build_with_cmake(self):
        # patch cmake files
        with tools.chdir(self.source_subfolder):
            tools.replace_in_file("CMakeLists_original.txt",
                                  "include(CurlSymbolHiding)",
                                  "")

        cmake = CMake(self)
        cmake.definitions['BUILD_TESTING'] = False
        cmake.definitions['BUILD_CURL_EXE'] = False
        cmake.definitions['CURL_DISABLE_LDAP'] = not self.options.with_ldap
        cmake.definitions['BUILD_SHARED_LIBS'] = self.options.shared
        cmake.definitions['CURL_STATICLIB'] = not self.options.shared
        cmake.definitions['CMAKE_DEBUG_POSTFIX'] = ''
        cmake.definitions['CMAKE_USE_LIBSSH2'] = self.options.with_libssh2
        cmake.configure(source_dir=self.source_subfolder)
        cmake.build()
        cmake.install()
