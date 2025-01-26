import sys
import os
# Add the directory containing autover.py to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import autover

def main():
    msg = open(sys.argv[1], "r").read()
    if not msg.startswith("Merge"):
        valid = autover.checkCommit(msg)
        if not valid:
            print(f"Commit message '{msg}' is not valid.")
            sys.exit(1)
        
        version = autover.getVer()
        open("./version.txt", "w").write(version)
        open("./src/version.txt", "w").write(version)
    
main()