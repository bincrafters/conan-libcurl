from conans.errors import ConanInvalidConfiguration
import os
import re
import shutil
from conans import ConanFile, AutoToolsBuildEnvironment, RunEnvironment, CMake, tools


class LibcurlConan(ConanFile):
    name = "libcurl"
    version = "7.66.0"
    description = "command line tool and library for transferring data with URLs"
    topics = ("conan", "libcurl", "data-transfer")
    url = "http://github.com/bincrafters/conan-libcurl"
    homepage = "http://curl.haxx.se"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["lib_Makefile_add.am", "CMakeLists.txt"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "with_openssl": [True, False],
               "with_winssl": [True, False],
               "disable_threads": [True, False],
               "with_ldap": [True, False],
               "with_ca_bundle": "ANY",
               "with_ca_path": "ANY",
               "darwin_ssl": [True, False],
               "with_libssh2": [True, False],
               "with_libidn": [True, False],
               "with_librtmp": [True, False],
               "with_libmetalink": [True, False],
               "with_libpsl": [True, False],
               "with_largemaxwritesize": [True, False],
               "with_largefile": [True, False],
               "with_nghttp2": [True, False],
               "with_brotli": [True, False]}
    default_options = {'shared': False,
                       'fPIC': True,
                       'with_openssl': True,
                       'with_winssl': False,
                       'disable_threads': False,
                       'with_ldap': False,
                       'with_ca_bundle': None,
                       'with_ca_path': None,
                       'darwin_ssl': True,
                       'with_libssh2': False,
                       'with_libidn': False,
                       'with_librtmp': False,
                       'with_libmetalink': False,
                       'with_libpsl': False,
                       'with_largemaxwritesize': False,
                       "with_largefile": True,
                       'with_nghttp2': False,
                       'with_brotli': False
                       }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    _autotools = False

    @property
    def is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler != "Visual Studio"

    def imports(self):
        # Copy shared libraries for dependencies to fix DYLD_LIBRARY_PATH problems
        #
        # Configure script creates conftest that cannot execute without shared openssl binaries.
        # Ways to solve the problem:
        # 1. set *LD_LIBRARY_PATH (works with Linux with RunEnvironment
        #     but does not work on OS X 10.11 with SIP)
        # 2. copying dylib's to the build directory (fortunately works on OS X)

        if self.settings.os == "Macos":
            self.copy("*.dylib*", dst=self._source_subfolder, keep_path=False)

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

        # be careful with those flags:
        # - with_openssl AND darwin_ssl uses darwin_ssl (to maintain recipe compatibilty)
        # - with_openssl AND NOT darwin_ssl uses openssl
        # - with_openssl AND with_winssl raises to error
        # - with_openssl AND NOT with_winssl uses openssl
        # Moreover darwin_ssl is set by default and with_winssl is not

        if self.options.with_openssl:
            # enforce shared linking due to openssl dependency
            if self.settings.os != "Macos" or not self.options.darwin_ssl:
                self.options["openssl"].shared = self.options.shared
        if self.options.with_libssh2:
            if self.settings.compiler != "Visual Studio":
                self.options["libssh2"].shared = self.options.shared

    def config_options(self):
        if self.settings.os != "Macos":
            try:
                self.options.remove("darwin_ssl")
            except:
                pass
        if self.settings.os != "Windows":
            try:
                self.options.remove("with_winssl")
            except:
                pass

        if self.settings.os == "Windows" and self.options.with_winssl and self.options.with_openssl:
            raise ConanInvalidConfiguration('Specify only with_winssl or with_openssl')

        if self.settings.os == "Windows":
            self.options.remove("fPIC")

        if self.settings.os != "Linux":
            self.options.remove("with_largefile")

    def requirements(self):
        if self.options.with_openssl:
            if self.settings.os == "Macos" and self.options.darwin_ssl:
                pass
            elif self.settings.os == "Windows" and self.options.with_winssl:
                pass
            else:
                self.requires.add("openssl/1.1.1d")
        if self.options.with_libssh2:
            if self.settings.compiler != "Visual Studio":
                self.requires.add("libssh2/1.8.2")
        if self.options.with_nghttp2:
            self.requires.add("nghttp2/1.38.0@bincrafters/stable")

        self.requires.add("zlib/1.2.11")

    def source(self):
        source_url = "https://curl.haxx.se/download/"
        sha256 = "d0393da38ac74ffac67313072d7fe75b1fa1010eb5987f63f349b024a36b7ffb"
        tools.get("{}curl-{}.tar.gz".format(source_url, self.version), sha256=sha256)
        os.rename("curl-%s" % self.version, self._source_subfolder)
        tools.download("https://curl.haxx.se/ca/cacert.pem", "cacert.pem", verify=True)

    def build(self):
        self.patch_misc_files()
        if self.settings.compiler != "Visual Studio":
            self.build_with_autotools()
        else:
            self.build_with_cmake()

    def patch_misc_files(self):
        if self.options.with_largemaxwritesize:
            tools.replace_in_file(os.path.join(self._source_subfolder, 'include', 'curl', 'curl.h'),
                                  "define CURL_MAX_WRITE_SIZE 16384",
                                  "define CURL_MAX_WRITE_SIZE 10485760")

        # https://github.com/curl/curl/issues/2835
        if self.settings.compiler == 'apple-clang' and self.settings.compiler.version == '9.1':
            if self.options.darwin_ssl:
                tools.replace_in_file(os.path.join(self._source_subfolder, 'lib', 'vtls', 'sectransp.c'),
                                      '#define CURL_BUILD_MAC_10_13 MAC_OS_X_VERSION_MAX_ALLOWED >= 101300',
                                      '#define CURL_BUILD_MAC_10_13 0')

    def get_configure_command_args(self):
        params = []
        params.append("--without-libidn2" if not self.options.with_libidn else "--with-libidn2")
        params.append("--without-librtmp" if not self.options.with_librtmp else "--with-librtmp")
        params.append("--without-libmetalink" if not self.options.with_libmetalink else "--with-libmetalink")
        params.append("--without-libpsl" if not self.options.with_libpsl else "--with-libpsl")
        params.append("--without-brotli" if not self.options.with_brotli else "--with-brotli")

        if not self.options.get_safe("with_largefile"):
            params.append("--disable-largefile")

        if self.settings.os == "Macos" and self.options.darwin_ssl:
            params.append("--with-darwinssl")
            params.append("--without-ssl")
        elif self.settings.os == "Windows" and self.options.with_winssl:
            params.append("--with-winssl")
            params.append("--without-ssl")
        elif self.options.with_openssl:
            openssl_path = self.deps_cpp_info["openssl"].rootpath.replace('\\', '/')
            params.append("--with-ssl=%s" % openssl_path)
        else:
            params.append("--without-ssl")

        if self.options.with_libssh2:
            params.append("--with-libssh2=%s" % self.deps_cpp_info["libssh2"].lib_paths[0].replace('\\', '/'))
        else:
            params.append("--without-libssh2")

        if self.options.with_nghttp2:
            params.append("--with-nghttp2=%s" % self.deps_cpp_info["nghttp2"].rootpath.replace('\\', '/'))
        else:
            params.append("--without-nghttp2")

        params.append("--with-zlib=%s" % self.deps_cpp_info["zlib"].lib_paths[0].replace('\\', '/'))

        if not self.options.shared:
            params.append("--disable-shared")
            params.append("--enable-static")
        else:
            params.append("--enable-shared")
            params.append("--disable-static")

        if self.options.disable_threads:
            params.append("--disable-thread")

        if not self.options.with_ldap:
            params.append("--disable-ldap")

        if self.options.with_ca_bundle == False:
            params.append("--without-ca-bundle")
        elif self.options.with_ca_bundle:
            params.append("--with-ca-bundle=" + str(self.options.with_ca_bundle))

        if self.options.with_ca_path == False:
            params.append('--without-ca-path')
        elif self.options.with_ca_path:
            params.append("--with-ca-path=" + str(self.options.with_ca_path))

        host = None
        # Cross building flags
        if tools.cross_building(self.settings) and self.settings.os in ["Linux", "iOS"]:
            host = self.get_host()

        return params, host

    def get_host(self):
        arch = None
        if self.settings.os == 'Linux':
            # aarch64 could be added by user
            if 'aarch64' in self.settings.arch:
                arch = 'aarch64-linux-gnu'
            elif 'arm' in self.settings.arch:
                if 'hf' in self.settings.arch:
                    arch = 'arm-linux-gnueabihf'
                elif self.arm_version(str(self.settings.arch)) > 4:
                    arch = 'arm-linux-gnueabi'
                else:
                    arch = 'arm-linux-gnu'

        elif self.settings.os == "iOS":
            if self.settings.arch == "armv8":
                arch = 'aarch64-darwin-ios'
            elif "arm" in self.settings.arch:
                arch = 'arm-darwin-ios'
            else:
                arch = '%s-darwin-ios' % self.settings.arch
        return arch

    def arm_version(self, arch):
        version = None
        match = re.match(r"arm\w*(\d)", arch)
        if match:
            version = int(match.group(1))
        return version

    def patch_mingw_files(self):
        if not self.is_mingw:
            return
        # patch autotools files
        # for mingw builds - do not compile curl tool, just library
        # linking errors are much harder to fix than to exclude curl tool
        tools.replace_in_file("Makefile.am",
                              'SUBDIRS = lib src',
                              'SUBDIRS = lib')

        tools.replace_in_file("Makefile.am",
                              'include src/Makefile.inc',
                              '')

        # patch for zlib naming in mingw
        # when cross-building, the name is correct
        if not tools.cross_building(self.settings):
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
            # used only for native mingw-make
            if not tools.cross_building(self.settings):
                added_content = tools.load(os.path.join(self.source_folder, 'lib_Makefile_add.am'))
                tools.save(os.path.join('lib', 'Makefile.am'), added_content, append=True)

    def build_with_autotools(self):
        env_run = RunEnvironment(self)
        # run configure with *LD_LIBRARY_PATH env vars
        # it allows to pick up shared openssl
        self.output.info("Run vars: " + repr(env_run.vars))
        with tools.environment_append(env_run.vars):
            with tools.chdir(self._source_subfolder):
                use_win_bash = self.is_mingw and not tools.cross_building(self.settings)

                # autoreconf
                self.run('./buildconf', win_bash=use_win_bash)

                tools.replace_in_file("configure", "-install_name \\$rpath/", "-install_name ")
                self.run("chmod +x configure")

                autotools, autotools_vars = self._configure_autotools()

                autotools.make(vars=autotools_vars)

    def _configure_autotools_vars(self):
        autotools_vars = self._autotools.vars
        # tweaks for mingw
        if self.is_mingw:
            autotools_vars['RCFLAGS'] = '-O COFF'
            if self.settings.arch == "x86":
                autotools_vars['RCFLAGS'] += ' --target=pe-i386'
            else:
                autotools_vars['RCFLAGS'] += ' --target=pe-x86-64'

            del autotools_vars['LIBS']
            self.output.info("Autotools env vars: " + repr(autotools_vars))
        return autotools_vars

    def _configure_autotools(self):
        if not self._autotools:
            use_win_bash = self.is_mingw and not tools.cross_building(self.settings)
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=use_win_bash)

            if self.settings.os != "Windows":
                self._autotools.fpic = self.options.fPIC

            autotools_vars = self._configure_autotools_vars()

            # tweaks for mingw
            if self.is_mingw:
                # patch autotools files
                self.patch_mingw_files()

                self._autotools.defines.append('_AMD64_')

            configure_args, host = self.get_configure_command_args()
            self._autotools.configure(vars=autotools_vars, args=configure_args, host=host)

        return self._autotools, self._configure_autotools_vars()

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['BUILD_TESTING'] = False
        cmake.definitions['BUILD_CURL_EXE'] = False
        cmake.definitions['CURL_DISABLE_LDAP'] = not self.options.with_ldap
        cmake.definitions['BUILD_SHARED_LIBS'] = self.options.shared
        cmake.definitions['CURL_STATICLIB'] = not self.options.shared
        cmake.definitions['CMAKE_DEBUG_POSTFIX'] = ''
        cmake.definitions['CMAKE_USE_LIBSSH2'] = self.options.with_libssh2
        if self.options.with_ca_bundle == False:
            cmake.definitions['CURL_CA_BUNDLE'] = 'none'
        elif self.options.with_ca_bundle:
            cmake.definitions['CURL_CA_BUNDLE'] = self.options.with_ca_bundle
        if self.options.with_ca_path == False:
            cmake.definitions['CURL_CA_PATH'] = 'none'
        elif self.options.with_ca_path:
            cmake.definitions['CURL_CA_PATH'] = self.options.with_ca_path

        # all these options are exclusive. set just one of them
        # mac builds do not use cmake so don't even bother about darwin_ssl
        cmake.definitions['CMAKE_USE_WINSSL'] = 'with_winssl' in self.options and self.options.with_winssl
        cmake.definitions['CMAKE_USE_OPENSSL'] = 'with_openssl' in self.options and self.options.with_openssl
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build_with_cmake(self):
        # patch cmake files
        with tools.chdir(self._source_subfolder):
            tools.replace_in_file("CMakeLists.txt",
                                  "include(CurlSymbolHiding)",
                                  "")

        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING*", dst="licenses", src=self._source_subfolder, ignore_case=True, keep_path=False)
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)

        # Execute install
        if self.settings.compiler != "Visual Studio":
            env_run = RunEnvironment(self)

            with tools.environment_append(env_run.vars):
                with tools.chdir(self._source_subfolder):
                    autotools, autotools_vars = self._configure_autotools()
                    autotools.install(vars=autotools_vars)
        else:
            cmake = self._configure_cmake()
            cmake.install()

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
                if self.options.with_brotli:
                    self.cpp_info.libs.extend(["brotlidec"])
            if self.settings.os == "Macos":
                if self.options.with_ldap:
                    self.cpp_info.libs.extend(["ldap"])
                if self.options.darwin_ssl:
                    self.cpp_info.exelinkflags.append("-framework Cocoa")
                    self.cpp_info.exelinkflags.append("-framework Security")
                    self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
        else:
            self.cpp_info.libs = ['libcurl_imp'] if self.options.shared else ['libcurl']

        if self.settings.os == "Windows":
            # used on Windows for VS build, native and cross mingw build
            self.cpp_info.libs.append('ws2_32')
            if self.options.with_ldap:
                self.cpp_info.libs.append("wldap32")
            if self.options.with_winssl:
                self.cpp_info.libs.append("Crypt32")

        if self.is_mingw:
            # provide pthread for dependent packages
            self.cpp_info.cflags.append("-pthread")
            self.cpp_info.exelinkflags.append("-pthread")
            self.cpp_info.sharedlinkflags.append("-pthread")

        if not self.options.shared:
            self.cpp_info.defines.append("CURL_STATICLIB=1")
