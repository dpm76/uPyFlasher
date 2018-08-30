#!/usr/bin/python3
from pyboard import Pyboard
import argparse

APP_VERSION = "0.0.1"

DEFAULT_TERMINAL = "/dev/ttyACM0"

def main():

    parser = argparse.ArgumentParser(prog="µPyFlasher", description="Flash a python application into a MCU with Micropython.")
    parser.add_argument("path", metavar="path", nargs="*",
                    help="Application root path. All files and directories within this path will be flashed.")

    parser.add_argument("--version", action="version", version="%(prog)s v{0}".format(APP_VERSION))
    
    parser.add_argument("-c", "--clear", action="store_true",
                    help="Clear all contents before flashing. If no path was given, it will just clear all modules with in the MCU.")
    
    parser.add_argument("-n", "--no-entry-point", action="store_true",
                    help="Clear the entry point if it was previuosly set.")
    
    parser.add_argument("-e", "--entry-point",
                    help="The passed function will be executed on MCU start. It uses the Python's module notation, i.e. myapp.mymodule.myentrypoint, and it can't have arguments.")
                    
    parser.add_argument("-v", "--verbose", action="store_true",
                    help="Show more information about the flashing process.")
                    
    parser.add_argument("-t", "--terminal", default=DEFAULT_TERMINAL,
                    help="(optional, default='{0}') Set the terminal where the MCU is attached to.".format(DEFAULT_TERMINAL))

    args = parser.parse_args()
    
    path = args.path[0] if args.path and len(args.path) > 1 else None
    terminal = args.terminal
    
    if path:
    
        f = open(path, "r")
        lines = f.readlines()
        f.close()

        pyb = Pyboard(terminal)
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
        
    else:
    
        print(args.terminal)
        #parser.print_help()



if __name__ == "__main__":
    main()