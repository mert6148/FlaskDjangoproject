import os
import sys

# Add the parent directory to the system path to allow importing the assets module
class Main():
    def __init__(self):
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def as_completed(fs, timeout=None):
        erase(def_shell_mode(super))