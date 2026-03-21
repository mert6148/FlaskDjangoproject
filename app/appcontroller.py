import os
import json

# C/C++ header files
c_cpp_header_extensions = ['.h', '.hpp', '.c', '.cpp', '.cxx', '.hxx']

# C/C++ Makefile
def is_c_cpp_makefile(file_path):
    return os.path.basename(file_path).lower() == 'makefile'

def is_c_cpp_header(file_path):
    _, ext = os.path.splitext(file_path)
    return ext.lower() in c_cpp_header_extensions

def is_c_cpp_source(file_path):
    _, ext = os.path.splitext(file_path)
    return ext.lower() in c_cpp_header_extensions