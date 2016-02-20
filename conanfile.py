from conans import ConanFile, ConfigureEnvironment
import os
from conans.tools import download
from conans.tools import unzip, replace_in_file
from conans import CMake


class LibCurlConan(ConanFile):
    name = "libcurl"
    version = "7.47.1"
    ZIP_FOLDER_NAME = "curl-%s" % version
    generators = "cmake", "txt"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], 
               "with_openssl": [True, False], 
               "disable_threads": [True, False]}
    default_options = "shared=False", "with_openssl=True", "disable_threads=False"
    exports = "CMakeLists.txt"
    url="http://github.com/lasote/conan-libcurl"
    license="https://curl.haxx.se/docs/copyright.html"
    
    def config(self):
        if self.options.with_openssl:
            self.requires.add("OpenSSL/1.0.2e@lasote/stable", private=False)
        else:
            del self.requires["OpenSSL"]
        
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
        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)

        if self.settings.os == "Linux" or self.settings.os == "Macos":
            
            suffix = ""
            if self.options.with_openssl:
                suffix += "--with-ssl "
            else:
                suffix += "--without-ssl"
            
            if not self.options.shared:
                suffix += " --disable-shared" 
            
            if self.options.disable_threads:
                suffix += " --disable-thread" 
 
            
            self.run("cd %s && %s ./configure %s" % (self.ZIP_FOLDER_NAME, env.command_line, suffix))
            self.run("cd %s && %s make" % (self.ZIP_FOLDER_NAME, env.command_line))
           
        else:
            # Do not compile curl tool, just library
            replace_in_file("%s/src/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "add_executable(", "IF(0)\n add_executable(")
            replace_in_file("%s/src/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "install(TARGETS ${EXE_NAME} DESTINATION bin)", "ENDIF()") # EOF
            cmake = CMake(self.settings)
            static = "-DBUILD_SHARED_LIBS=ON -DCURL_STATICLIB=OFF" if self.options.shared else "-DBUILD_SHARED_LIBS=OFF -DCURL_STATICLIB=ON"
            self.run("cd %s && mkdir _build" % self.ZIP_FOLDER_NAME)
            cd_build = "cd %s/_build" % self.ZIP_FOLDER_NAME
            self.run('%s && cmake .. %s %s' % (cd_build, cmake.command_line, static))
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
        if not self.settings.os == "Windows":
            self.cpp_info.libs = ['curl']
            self.cpp_info.libs.extend(["rt", "rtmp", "ldap", "idn"])
        else:
            self.cpp_info.libs = ['libcurl_imp'] if self.options.shared else ['libcurl']
            self.cpp_info.libs.append('Ws2_32')
        
        if not self.options.shared:
            self.cpp_info.defines.append("CURL_STATICLIB=1")
