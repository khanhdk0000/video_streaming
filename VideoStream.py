import cv2
import os

class VideoStream:
    # In this VideoStream, instance attributes include:
    # 											self.file
    # 											self.frameNum (number of current frame)
    # 											self.numFrames (total number of frames)
    # 											self.fps
    # 											self.totalTime
    frameLengthList = []
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frameNum = 0

    def nextFrame(self, forward, backward):
        
        """Get next frame."""
        if self.filename == "movie.Mjpeg" or self.filename == "movie.mjpeg":
            # Backward frame processing
            last1secFrames = 0 
            if backward == 1:
                for x in range(25):
                    if self.frameLengthList:
                        last5secFrames += (self.frameLengthList.pop() + 5)
                self.file.seek(-last1secFrames, os.SEEK_CUR)
                # self.frameNum = self.frameNum - 25 ?
            # Get the framelength from the first 5 bits
            data = self.file.read(5)
            # Forward frame processing
            if data:
                framelength = int(data)
                self.frameLengthList.append(framelength)
                # Read the current frame
                data = self.file.read(framelength)

                self.frameNum += 1
            return data
        else:
            data = b""
            while True:
                temp_byte = self.file.read(1)
                if temp_byte == b'\xff':
                    temp_byte = temp_byte + self.file.read(1)
                    if temp_byte == b'\xff\xd8':
                        data = data + temp_byte
                        while True:
                            temp_byte = self.file.read(1)
                            data = data + temp_byte
                            if temp_byte == b'\xff':
                                temp_byte = temp_byte + self.file.read(1)
                                data = data + temp_byte
                                if temp_byte == b'\xff\xd9':
                                    self.frameNum += 1
                                    break
                        break
        
            return data

    def getNumFrames(self):
        """Get total number of frames."""
        while self.nextFrame(0,0):
            pass
        self.numFrames = self.frameNum
        self.frameNum = 0
        self.frameLengthList = []
        self.file.close()
        self.file = open(self.filename, 'rb')
        return self.numFrames

    def getFps(self):
        """Get frames per second."""
        cap = cv2.VideoCapture("./{0}".format(self.filename))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        return self.fps

    def getTotalTime(self):
        """Get total time of the video."""
        self.getNumFrames()
        self.getFps()
        self.totalTime = self.numFrames / self.fps
        return self.totalTime

    def frameNbr(self):
        """Get frame number."""
        return self.frameNum
