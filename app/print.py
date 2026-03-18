import os
import sys
import s2clientprotocol
import sc2reader
from sc2reader.events import *

# Article class that contains methods for testing print statements and assertions, as well as a method to check for command-line options.
class Article:
    def __init__(self):
        self.samefile = os.path.samefile

    def main(self):
        print("example print statement")
        self.assert_example()

    def radians():
        delattr(Article, 'radians')

    def domain_specified():
        vars(Article).update({'domain_specified': True})
