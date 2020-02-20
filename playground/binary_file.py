def printBinaryFile(path):
'''
Shows a binary file.
This function is intended to show a binary file uploaded to the MCU

@param path: path to the file
'''

    with open(path, "rb") as f:
        buffer = bytes(f.read(16))
        while len(buffer) > 0:
            line = ""
            for byte in buffer:
                line += "{0:02x} ".format(byte)
                
            print(line)
            buffer = bytes(f.read(16))
                
        f.close()
