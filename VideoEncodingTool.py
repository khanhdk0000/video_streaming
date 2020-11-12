####################################################
# This file is used to encode a general mjpeg video
# into mjpeg video that fits the format of the video
# given in the source codes.
####################################################
import sys
from functools import reduce

####################################################
# Here we put the name of the file.
# Remember the file must be in the same folder with
# The VideoEncodingTool.py file.
####################################################
def main(argv):
    try:
        fileName = argv
        file = open(fileName, 'rb')
        data = []
        frameLength = 0
        shouldClose = False


        while not shouldClose:
            while True:
                bytes_data = b''
                temp_byte = file.read(1)
                if temp_byte == b'':
                    shouldClose = True
                    break
                if temp_byte == b'\xff':
                    temp_byte += file.read(1)
                    if temp_byte == b'\xff\xd8':
                        bytes_data += temp_byte
                        frameLength += 2
                        while True:
                            temp_byte = file.read(1)
                            bytes_data += temp_byte
                            frameLength += 1

                            if temp_byte == b'\xff':
                                res = file.read(1)
                                temp_byte += res
                                bytes_data += res
                                frameLength += 1
                                if temp_byte == b'\xff\xd9':
                                    byteLength = bytes(str(frameLength), "ascii")
                                    if byteLength > b'99999':
                                        raise Exception(
                                            "This file's frame length is too big to encode!")
                                    else:
                                        first5Bytes = "{:0>5}".format(int(byteLength))
                                        bytes_data = bytes(first5Bytes, "utf-8") + bytes_data
                                        data.append(bytes_data)
                                        frameLength = 0
                                    break
                        break
        file.close()

        file = open(fileName, 'wb')
        file.write(reduce(lambda x, y: x + y, data))
        file.close()

    except:
        print("Find not found!")

if __name__ == "__main__":
    main(sys.argv[1])