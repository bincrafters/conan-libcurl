from conans import ConanFile
import os
from conans.tools import download
from conans.tools import unzip
from conans import CMake


class LibCurlConan(ConanFile):
    name = "libcurl"
    version = "7.45.0"
    ZIP_FOLDER_NAME = "curl-%s" % version
    generators = "cmake", "txt"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], 
               "with_openssl": [True, False], 
               "disable_threads": [True, False]}
    default_options = "shared=False", "with_openssl=True", "disable_threads=False"
    exports = "CMakeLists.txt"
    url="http://github.com/lasote/conan-libcurl"
    
    def config(self):
        if self.options.with_openssl:
            self.requires.add("OpenSSL/1.0.2d@lasote/stable", private=False)
        else:
            del self.requires["OpenSSL"]
        

    def conan_info(self):
        # We don't want to change the package for each compiler version but
        # we need the setting to compile with cmake
        self.info.settings.compiler.version = "any"

    def source(self):
        zip_name = "curl-%s.tar.gz" % self.version
        download("http://curl.haxx.se/download/%s" % zip_name, zip_name)
        unzip(zip_name)
        os.unlink(zip_name)
        if self.settings.os != "Windows":
            self.run("chmod +x ./%s/configure" % self.ZIP_FOLDER_NAME)

    def build(self):
        """ Define your project building. You decide the way of building it
            to reuse it later in any other project.
        """
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            ld_flags = ""
            cpp_flags = ""
            c_flags = ""
            # FIXME!! fails in travis, install in system requirements
            suffix = "--disable-ldap --without-librtmp --without-libidn " # Until ldap is uploaded to conan or installed in system_requirements
            
            if self.options.with_openssl:
                ld_flags += 'LDFLAGS="%s"' % " ".join(["-L%s" % path for path in self.deps_cpp_info.lib_paths])
                cpp_flags += 'CPPFLAGS="%s"' % " ".join(["-I%s" % path for path in self.deps_cpp_info.include_paths])
                suffix += "--with-ssl "
            else:
                suffix += "--without-ssl"
            
            if not self.options.shared:
                suffix += " --disable-shared" 
            
            if self.options.disable_threads:
                suffix += " --disable-thread" 
                
            if self.settings.arch == "x86":
                c_flags = "CFLAGS=-m32"
            configure_command = "cd %s && %s %s %s ./configure %s" % (self.ZIP_FOLDER_NAME, c_flags, cpp_flags, ld_flags, suffix)
            self.output.info(configure_command)
            
            self.run(configure_command)
            self.run("cd %s && make" % self.ZIP_FOLDER_NAME)
        else:
            cmake = CMake(self.settings)
            if self.settings.os == "Windows":
                self.run("IF not exist _build mkdir _build")
            else:
                self.run("mkdir _build")
            cd_build = "cd _build"
            self.output.warn('%s && cmake .. %s' % (cd_build, cmake.command_line))
            self.run('%s && cmake .. %s' % (cd_build, cmake.command_line))
            self.output.warn("%s && cmake --build . %s" % (cd_build, cmake.build_config))
            self.run("%s && cmake --build . %s" % (cd_build, cmake.build_config))

    def package(self):
        """ Define your conan structure: headers, libs, bins and data. After building your
            project, this method is called to create a defined structure:
        """
        # Copying zlib.h, zutil.h, zconf.h
        self.copy("*.h", "include/curl", "%s" % (self.ZIP_FOLDER_NAME), keep_path=False)

        # Copying static and dynamic libs
        if self.settings.os == "Windows":
            if self.options.shared:
                self.copy(pattern="*.dll", dst="bin", src=self.ZIP_FOLDER_NAME, keep_path=False)
            self.copy(pattern="**.lib", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
        else:
            if self.options.shared:
                if self.settings.os == "Macos":
                    self.copy(pattern="*.dylib", dst="lib", keep_path=False)
                else:
                    self.copy(pattern="*.so*", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ['curl']
        self.cpp_info.libs.extend(["rt"])


def replace_in_file(file_path, search, replace):
    with open(file_path, 'r') as content_file:
        content = content_file.read()
        content = content.replace(search, replace)
    with open(file_path, 'wb') as handle:
        handle.write(content)
