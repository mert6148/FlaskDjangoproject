import os
import sys
import tester_os_config
import tester_os_config_windows
from tester import Tester
from tester import TesterConfig

class WindowsTester(Tester):
    def __init__(self, config: TesterConfig):
        super().__init__(config)

    def before_call():
        tester_os_config.before_call()
        tester_os_config_windows.before_call()
    
    def after_call():
        tester_os_config.before_call()
        tester_os_config_windows.before_call()
    
    def sameopenfile(fp1, fp2):
        if fp1.fileno() != fp2.fileno():
            return False
        if os.path.abspath(fp1.name) != os.path.abspath(fp2.name):
            return False
        return True