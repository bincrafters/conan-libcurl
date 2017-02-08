from conans import ConanFile, ConfigureEnvironment
import os
from conans.tools import download
from conans.tools import unzip, replace_in_file
from conans import CMake


class LibCurlConan(ConanFile):
    name = "libcurl"
    version = "7.52.1"
    ZIP_FOLDER_NAME = "curl-%s" % version
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
                      "with_libmetalink=False", \
                      "with_largemaxwritesize=False"
    exports = ["CMakeLists.txt", "FindCURL.cmake"]
    url="http://github.com/theirix/conan-libcurl"
    license="https://curl.haxx.se/docs/copyright.html"
    short_paths=True
    
    def config(self):
        del self.settings.compiler.libcxx
        if self.options.with_openssl:
            if self.settings.os != "Macos" or not self.options.darwin_ssl:
                self.requires.add("OpenSSL/[>=1.0.2a,<1.0.3]@lasote/stable", private=False)
                self.options["OpenSSL"].shared = self.options.shared
            elif self.settings.os == "Macos" and self.options.darwin_ssl:
                self.requires.add("zlib/[>=1.2.8,<1.3.0]@lasote/stable", private=False)
        else:
            del self.requires["OpenSSL"]
        if self.options.with_libssh2:
            if self.settings.os != "Windows":
                self.requires.add("libssh2/[>=1.8.0,<1.9.0]@theirix/stable", private=False)
            
        if self.settings.os != "Macos":
            try:
                self.options.remove("darwin_ssl")
            except:
                pass
        self.requires.add("zlib/[>=1.2.8,<1.3.0]@lasote/stable", private=False)

    def source(self):
        zip_name = "curl-%s.tar.gz" % self.version
        download("https://curl.haxx.se/download/%s" % zip_name, zip_name, verify=False)
        unzip(zip_name)
        os.unlink(zip_name)
        download("https://curl.haxx.se/ca/cacert.pem", "cacert.pem", verify=False)
        if self.options.with_largemaxwritesize:
            self.output.warn("Setting large MAX_WRITE_SIZE")
            replace_in_file("%s/include/curl/curl.h" % self.ZIP_FOLDER_NAME, "define CURL_MAX_WRITE_SIZE 16384", "define CURL_MAX_WRITE_SIZE 10485760")
        if self.settings.os != "Windows":
            self.run("chmod +x ./%s/configure" % self.ZIP_FOLDER_NAME)

    def build(self):
        """ Define your project building. You decide the way of building it
            to reuse it later in any other project.
        """
        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)

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
            
            # Hack for configure, don't know why fails because it's not able to find libefence.so
            command_line = env.command_line.replace("-lefence", "")
 
            old_str = "-install_name \$rpath/"
            new_str = "-install_name "
            replace_in_file("%s/configure" % self.ZIP_FOLDER_NAME, old_str, new_str)
 
 
            configure = "cd %s && %s ./configure %s" % (self.ZIP_FOLDER_NAME, command_line, suffix)
            self.output.warn(configure)
            
            # BUG: https://github.com/curl/curl/commit/bd742adb6f13dc668ffadb2e97a40776a86dc124
            replace_in_file("%s/configure" % self.ZIP_FOLDER_NAME, 'LDFLAGS="`$PKGCONFIG --libs-only-L zlib` $LDFLAGS"', 'LDFLAGS="$LDFLAGS `$PKGCONFIG --libs-only-L zlib`"')
            
            self.output.warn(configure)
            self.run(configure)
            self.run("cd %s && env %s make" % (self.ZIP_FOLDER_NAME, env.command_line))
           
        else:
            # Do not compile curl tool, just library
            conan_magic_lines = '''project(CURL)
cmake_minimum_required(VERSION 3.0)
include(../conanbuildinfo.cmake)
CONAN_BASIC_SETUP()
'''
            replace_in_file("%s/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "cmake_minimum_required(VERSION 2.8 FATAL_ERROR)", conan_magic_lines)
            replace_in_file("%s/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "project( CURL C )", "")
            replace_in_file("%s/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "include(CurlSymbolHiding)", "")
            
            replace_in_file("%s/src/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "add_executable(", "IF(0)\n add_executable(")
            replace_in_file("%s/src/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "install(TARGETS ${EXE_NAME} DESTINATION bin)", "ENDIF()") # EOF
            cmake = CMake(self.settings)
            static = "-DBUILD_SHARED_LIBS=ON -DCURL_STATICLIB=OFF" if self.options.shared else "-DBUILD_SHARED_LIBS=OFF -DCURL_STATICLIB=ON"
            ldap = "-DCURL_DISABLE_LDAP=ON" if not self.options.with_ldap else "-DCURL_DISABLE_LDAP=OFF"
            self.run("cd %s && mkdir _build" % self.ZIP_FOLDER_NAME)
            cd_build = "cd %s/_build" % self.ZIP_FOLDER_NAME
            self.run('%s && cmake .. %s -DBUILD_TESTING=OFF %s %s' % (cd_build, cmake.command_line, ldap, static))
            self.run("%s && cmake --build . %s" % (cd_build, cmake.build_config))
            
    def package(self):
        """ Define your conan structure: headers, libs, bins and data. After building your
            project, this method is called to create a defined structure:
        """
        
        # Copy findZLIB.cmake to package
        self.copy("FindCURL.cmake", ".", ".")
        
        # Copying zlib.h, zutil.h, zconf.h
        self.copy("*.h", "include/curl", "%s" % (self.ZIP_FOLDER_NAME), keep_path=False)

        # Copy the certs to be used by client
        self.copy(pattern="cacert.pem", keep_path=False)
        
        # Copying static and dynamic libs
        if self.settings.os == "Windows":
            if self.options.shared:
                self.copy(pattern="*.dll", dst="bin", src=self.ZIP_FOLDER_NAME, keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
        else:
            if self.options.shared:
                if self.settings.os == "Macos":
                    self.copy(pattern="*.dylib", dst="lib", keep_path=False)
                else:
                    self.copy(pattern="*.so*", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)

    def package_info(self):
        if self.settings.os != "Windows":
            self.cpp_info.libs = ['curl']
            if self.settings.os == "Linux":
                self.cpp_info.libs.extend(["rt"])
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
