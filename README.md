# uPyFlasher
Flashes a python application into a MCU with uPython.

## Usage
`flash.py [-h] [-a] [-e] [-m FUNCTION] [-n] [-v] [--version]`
                  `[-d DEVICE]`
                  `[LOCAL_PATH]`

### Positional arguments:
  `LOCAL_PATH`
  Application root path. All files and directories within this path will be flashed.

### Optional arguments:
  `-h, --help`
  Show this help message and exit
  
  `-a, --add`
  Keeps already flashed modules in the MCU. Otherwise, they will be deleted before flashing.
  
  `-e, --erase`
  Erases all user's Python modules.
  
  `-m FUNCTION, --main FUNCTION`
The passed function will be executed on start orreset, usualy the 'main' function. The Python's module notation is used, i.e. myapp.mymodule.myentrypoint. This function can not have any argument.

`-n, --nomain`
Clear the entry point (main function). Therefore the device executes no action after start or reset.

`-v, --verbose`
Show more information about the flashing process.

`--version`
Show program's version number and exit

`-d DEVICE, --device DEVICE`
(default='/dev/ttyACM0') The serial terminal or IP address where the MCU is attached to.
