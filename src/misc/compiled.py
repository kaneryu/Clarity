import os

compiled = True if os.path.exists("compiled.txt") else False

__compiled__ = compiled

if __compiled__:
    print("Running in compiled mode")
else:
    print("Running in interpreted (dev) mode")