#!/usr/bin/python3

from pyboard import Pyboard, PyboardError

import os
import sys
import argparse
import time

#The user code directory. It will be under /flash/[APP_DIR_NAME]
APP_DIR_NAME = "userapp"

#Force to flush the current file each a number of lines. It seems to prevent hanging on flashing.
FLUSH_AFTER_LINES = 5

#File types that are considered as text files, otherwise they'll be treated as binary file.
TEXT_FILES = (".py", ".txt")

#Size of the buffer for binary copy
BINARY_BUFFER_SIZE = 64

def printVerbose(message, verbose=False):
    '''
    Prints a message when verbose is required
    
    @param message: The message to be printed
    @param verbose: (optional, default=False) Flag to indicate whether print the message or not
    '''

    if verbose:
        print(message)


def remoteEval(pybObj, expression):
    '''
    Evaluates an expression on the remote device.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param expresseion: Python expression as a string.
    @returns: Result of the expression as a string.
    '''

    return eval(pybObj.eval(expression).decode("ascii"))
    
    
def remotePathIsFile(pybObj, remotePath):
    '''
    Checks whether a path of the remote device is a file.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param remotePath: Path to the item to be checked.
    @return: True if the remote path is a file, otherwise False
    @rtype: bool
    '''
    
    return remoteEval(pybObj, "os.stat('{0}')[0]".format(remotePath)) == 32768
    

def _doClearMain(pybObj):
    '''
    Resets the main.py file of the remote device. Therefore, no code will be executed 
    nor any user module will be available by default on start or reset.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    '''

    pybObj.exec("f = open('main.py', 'w')")
    pybObj.exec("f.write('#Insert your code here...\\n')")
    pybObj.exec("f.close()")


def _initMain(pybObj):
    '''
    Clears the main.py file but makes the user code on start or reset still available.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    '''

    pybObj.exec("f = open('main.py', 'w')")
    pybObj.exec("f.write('#Flashed with µPyFlasher.\\n')")
    pybObj.exec("f.write('import sys\\n')")
    pybObj.exec("f.write('sys.path.append(\"/flash/" + APP_DIR_NAME + "\")\\n')")
    pybObj.exec("f.close()")


def clearMain(pybObj):
    '''
    Executes the "clear main" option.
    Ask the user for confirmation.
    In case of positive confirmation, it removes the entry point, thus the device won't 
    executes any Python code after start or reset.
    If there is any user module flashed, it remains available.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    '''

    answer = input("The entry point is going to be cleared. Are you sure to proceed? (Y/n): ");
    if answer and answer.startswith("Y"):        

        isFlashed = remoteEval(pybObj, "'" + APP_DIR_NAME + "' in os.listdir('/flash')")
        if isFlashed:
            _initMain(pybObj)
        else:
            _doClearMain(pybObj)        

        print("Done.")
        
    else:
        print("Aborted.")


def _doSetMain(pybObj, entryPoint):
    '''
    Sets the entry point function, thus this function will be invoked on device star or reset.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param entryPoint: Path to the main function. The notation is like with Python code,
                       i.e. mymodule.mysubmodule.myfunction
    @type entryPoint: string
    '''

    print("Setting entry point at '" + entryPoint + "'")
    modulePath = entryPoint[0:entryPoint.rfind(".")]
    
    _initMain(pybObj)
    pybObj.exec("f = open('main.py', 'a')")
    pybObj.exec("f.write('#This is the entry-point of the user code.\\n')")
    pybObj.exec("f.write('import {0}\\n')".format(modulePath))
    pybObj.exec("f.write('{0}()\\n')".format(entryPoint))
    pybObj.exec("f.close()")


def setMain(pybObj, entryPoint):
    '''
    Executes the "set main" option.
    Ask the user for confirmation.
    In case of positive confirmation, it sets the entry point function, thus this function will be invoked on device star or reset.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param entryPoint: Path to the main function. The notation is like with Python code,
                       i.e. mymodule.mysubmodule.myfunction
    @type entryPoint: string
    '''

    answer = input("The entry point will be changed. Are you sure to proceed? (Y/n): ");
    if answer and answer.startswith("Y"):
        _doSetMain(pybObj, entryPoint)
        print("Done.")
        
    else:
        print("Aborted.")


def createDirpath(pybObj, dirpath, verbose):
    '''
    Creates a directory path on the device, if this doesn't exists.
    
    @param pybObj:  Interface with the remote device. Must be initializated previously.
    @param dirpath: Directory path. This must be full path (that means, starting with "/")
    @param verbose: Flag to print some information about the process.
    '''

    dirnames = dirpath.lstrip("/flash/").split("/")
    parentPath = "/flash"
    
    for dirname in dirnames:
        if dirname != "" and dirname != ".":
            path = parentPath + "/" + dirname
            dirExists = remoteEval(pybObj, "'{0}' in os.listdir('{1}')".format(dirname, parentPath))
            if not dirExists:
                print("Creating directory '{0}'".format(path))
                pybObj.exec("os.mkdir('{0}')".format(path))
            parentPath = path

def _exec(pybObj, command):

    pybObj.exec_raw_no_follow(command)
    

def flashTextFile(pybObj, localPath, remotePath, verbose):
    '''
    Copies a file to the remote device in text mode. If the destination path doesn't exist, it will be created.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param localPath: Path to the source file.
    @param remotePath: Path of the destination file. This path must be absolute, 
                       that means starting with "/".
    @param verbose: Flag to print some information about the process.
    '''

    print("(text) {0} => {1}".format(localPath, remotePath))
    
    dirpath = os.path.dirname(remotePath)
    createDirpath(pybObj, dirpath, verbose)

    f = open(localPath, "r")
    lines = f.readlines()
    f.close()
    
    _exec(pybObj, "f = open('{0}', 'w')".format(remotePath))
    i = 0
    
    for line in lines[i:]:
        line = line.rstrip()
        i += 1
        printVerbose("{0:04d} >{1}".format(i, line), verbose)
        line = line.replace("\'", "\\\'")
        _exec(pybObj, "f.write('{0}\\n')".format(line))
            
        if i % FLUSH_AFTER_LINES == 0:
            _exec(pybObj, "f.flush()")
            if not verbose:
                print(".", end="", flush=True)

    _exec(pybObj, "f.flush()")
    _exec(pybObj, "f.close()")
    if not verbose:
        print("|")


def flashBinaryFile(pybObj, localPath, remotePath, verbose):
    '''
    Copies a file to the remote device in binary mode. If the destination path doesn't exist, it will be created.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param localPath: Path to the source file.
    @param remotePath: Path of the destination file. This path must be absolute, 
                       that means starting with "/".
    @param verbose: Flag to print some information about the process.
    '''
    
    print("(binary) {0} => {1}".format(localPath, remotePath))
    
    dirpath = os.path.dirname(remotePath)
    createDirpath(pybObj, dirpath, verbose)

    with open(localPath, "rb") as f:
        
        _exec(pybObj, "f = open('{0}', 'wb')".format(remotePath))
        
        buffer = bytes(f.read(BINARY_BUFFER_SIZE))
        while len(buffer) > 0:                   
            _exec(pybObj, "f.write({0})".format(str(buffer)))
            _exec(pybObj, "f.flush()")
            buffer = bytes(f.read(BINARY_BUFFER_SIZE))
            if not verbose:
                print(".", end="", flush=True)
            else:
                print(buffer)
        
        _exec(pybObj, "f.close()")
        if not verbose:
            print("|")
        f.close()


def eraseDir(pybObj, remotePath, verbose):
    '''
    Erases a directory on the remote device. This function is recursive and all contents, 
    files and directories within the target directory will be also erased.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param remotePath: Path of the remote directory. This path must be absolute, 
                       that means starting with "/".
    @param verbose: Flag to print some information about the process.
    '''

    itemNames = remoteEval(pybObj,"os.listdir('{0}')".format(remotePath))
    for itemName in itemNames:
        itemPath = remotePath + '/' + itemName
        if remotePathIsFile(pybObj, itemPath):
            print("Deleting file '{0}'".format(itemPath))
            pybObj.exec("os.remove('{0}')".format(itemPath))
        else:
            eraseDir(pybObj, itemPath, verbose)
    
    print("Deleting directory '{0}'".format(remotePath))
    pybObj.exec("os.rmdir('{0}')".format(remotePath))
    

def flashDir(pybObj, localPath, remotePath, verbose):
    '''
    Copies a directory on the remote device. This function is recursive and all contents, 
    files and directories within the target directory will be copied too, but files with the 
    pattern '*.pyc' and directories '__pycache__', which are ignored and therefore 
    they won't be copied.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param localPath: Path to the source directory.
    @param remotePath: Path of the remote directory. This path must be absolute, 
                       that means starting with "/".
    @param verbose: Flag to print some information about the process.
    '''

    for itemName in os.listdir(localPath):
        itemLocalPath = "{0}/{1}".format(localPath, itemName)
        itemRemotePath = "{0}/{1}".format(remotePath, itemName)
        if os.path.isfile(itemLocalPath) and not itemName.endswith(".pyc"):
            if itemName.endswith(TEXT_FILES):
                flashTextFile(pybObj, itemLocalPath, itemRemotePath, verbose)
            else:
                flashBinaryFile(pybObj, itemLocalPath, itemRemotePath, verbose)
        elif os.path.isdir(itemLocalPath) and itemName != "__pycache__":
            flashDir(pybObj, itemLocalPath, itemRemotePath, verbose)
        else:
            printVerbose("Item '{0}' ignored".format(itemLocalPath), verbose)
            

def flash(pybObj, localPath, remotePath, erase, verbose):
    '''
    Executes the flash functionality.
    Ask the user for confirmation.
    In case of positive confirmation, copies a single file or a directory recursively to the 
    remote device. Already flashed contents can be preserved or erased as desired.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param remotePath: Path where the code will be copied within.
    @param localPath: Path to the source file or directory.
    @param erase: Flag to preserve or erase already flashed contents.
    @param verbose: Flag to print some information about the process.
    '''

    answer = input("The contents of MCU will be changed. Are you sure to proceed? (Y/n): ");
    if answer and answer.startswith("Y"):

        if erase:
            _doEraseAll(pybObj, verbose)
        
        remotePath = "/" + remotePath if remotePath != "" else ""
        
        if os.path.isfile(localPath):
            filename = localPath.split("/")[-1]
            fullRemotePath = "/flash/" + APP_DIR_NAME + remotePath + "/{0}".format(filename)
            if filename.endswith(TEXT_FILES):
                flashTextFile(pybObj, localPath, fullRemotePath, verbose)
            else:
                flashBinaryFile(pybObj, localPath, fullRemotePath, verbose)
        else:
            dirname = localPath.rstrip("/").split("/")[-1]
            fullRemotePath = "/flash/" + APP_DIR_NAME + remotePath + (("/" + dirname) if dirname != "." else "")
            flashDir(pybObj, localPath, fullRemotePath, verbose)

        print("Done. User code is available under the '" + APP_DIR_NAME + "' directory.")
        
    else:
        print("Aborted.")


def _doEraseAll(pybObj, verbose):
    '''
    Erases all user code on the remote device.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param verbose: Flag to print some information about the process.
    '''

    existModules = remoteEval(pybObj, "'flash' in os.listdir('/') and '" + APP_DIR_NAME + "' in os.listdir('/flash')")
    if existModules:
        eraseDir(pybObj, "/flash/" + APP_DIR_NAME, verbose)


def eraseAll(pybObj, verbose):
    '''
    Executes the "erase" option.
    Ask the user for confirmation.
    In case of positive confirmation, it erases all user code on the remote device.
    
    @param pybObj: Interface with the remote device. Must be initializated previously.
    @param verbose: Flag to print some information about the process.
    '''

    existModules = remoteEval(pybObj, "'flash' in os.listdir('/') and '" + APP_DIR_NAME + "' in os.listdir('/flash')")
    if existModules:
        answer = input("The user code will be erased. Are you sure to proceed? (Y/n): ");
        if answer and answer.startswith("Y"):
            _doEraseAll(pybObj, verbose)
            _doClearMain(pybObj)
            print("Done.")
        else:
            print("Aborted.")
    else:
        print("The device has no user code flashed. Aborting.")
        

def main():

    if sys.platform.startswith("win"):
        DEFAULT_TERMINAL="COM3"
    else:
        DEFAULT_TERMINAL="/dev/ttyACM0"
    APP_VERSION = "0.0.3"


    parser = argparse.ArgumentParser(prog="µPyFlasher", description="Flashes a python application into a MCU with Micropython.")
    # parser.add_argument("-a", "--add", action="store_true", dest="addmodules",
    #               help="keeps already flashed code in the mcu. otherwise, they will be deleted before flashing.")
    parser.add_argument("-e", "--erase", action="store_true", help="Erases all user's Python code.")
    parser.add_argument("-m", "--main", metavar="FUNCTION",
                    help="The passed function will be executed on start or reset, usualy the 'main' function. The Python's module notation is used, i.e. myapp.mymodule.myentrypoint. This function can not have any argument.")
    parser.add_argument("-n", "--nomain", action="store_true", dest="noMain",
                    help="Clear the entry point (main function). Therefore the device executes no action after start or reset.")
    parser.add_argument("path", metavar="LOCAL_PATH", nargs="?",
                    help="Application root path. All files and directories within this path will be flashed.")
    parser.add_argument("-v", "--verbose", action="store_true",
                    help="Show more information about the flashing process.")
    parser.add_argument("--version", action="version", version="%(prog)s v{0}".format(APP_VERSION))
    parser.add_argument("-d", "--device", metavar="DEVICE", default=DEFAULT_TERMINAL,
                    help="(default='{0}') The serial terminal or IP address where the MCU is attached to.".format(DEFAULT_TERMINAL))
    parser.add_argument("-p", "--remotepath", metavar="REMOTE_PATH", default="",
                    help="The code will be copied into the given path.")

    args = parser.parse_args()

    #check args
    errors = False

    if len(sys.argv) == 1:
        print("Arguments missed.\n")
        errors = True

    if args.path and not os.path.exists(args.path):
        print("Path '{0}' not found.".format(args.path))
        errors = True
        
    if not sys.platform.startswith("win") and not os.path.exists(args.device):
        print("Device '{0}' not found.".format(args.device))
        errors = True
    
    if not errors:
        #proceed
        pyb = Pyboard(args.device)
        pyb.enter_raw_repl()
        try:
            pyb.exec("import os")
            pyb.exec("import utime")
            
            if args.path:
                flash(pyb, args.path, args.remotepath, args.erase, args.verbose)
                if args.main:
                    _doSetMain(pyb, args.main)
                elif args.noMain:
                    _initMain(pyb)
                    print("Entry point cleared.")
                    
            elif args.erase:
                eraseAll(pyb, args.verbose)
            
            elif args.noMain:
                clearMain(pyb)
                
            elif args.main:
                setMain(pyb, args.main)
        finally:
            pyb.exit_raw_repl()
            pyb.close()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
