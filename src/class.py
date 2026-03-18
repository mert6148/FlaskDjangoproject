import os
import sys
import s2clientprotocol
import sc2reader

def main():
    for event in sc2reader.load_replay('replay.SC2Replay'):
        print(event)
       
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(f"Current directory: {dir_path}")

def asert_example():
    assert 1 + 1 == 2, "Math is broken!"
    