#!/usr/bin/env python
from pyboard import Pyboard
import argparse

APP_VERSION = "0.0.1"

def main():

    parser = argparse.ArgumentParser(prog="flasher", description="Flash a python application into a MCU with uPython.")
    parser.add_argument("path", metavar="path",
                    help="Application root path. All files and directories within this path will be flashed.")

    parser.add_argument("--version", action="version", version="%(prog)s v{0}".format(APP_VERSION))

    args = parser.parse_args()
    
    f = open(args.path, "r")
    lines = f.readlines()
    f.close()

    pyb = Pyboard('/dev/ttyACM0')
    pyb.enter_raw_repl()
    pyb.exec("f = open('main.py', 'w')")
    
    i = 0
    for line in lines:
        line = line.rstrip()
        i += 1
        print("{0} > '{1}'".format(i, line))
        pyb.exec("f.write('{0}\\r\\n')".format(line))
    pyb.exec("f.close()")
    pyb.exit_raw_repl()
    pyb.close()
    
    print("Done.")



if __name__ == "__main__":
    main()