import cv2
import os


class VideoStream:
    # In this VideoStream, instance attributes include:
    # 											self.file
    # 											self.frameNum (number of current frame)
    # 											self.numFrames (total number of frames)
    # 											self.fps
    # 											self.totalTime

    def __init__(self, filename):
        self.filename = filename
        self.wholeVideo = []
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frameNum = 0

    def nextFrame(self, forward, backward):
        """Get next frame."""
        if self.filename == "movie.Mjpeg" or self.filename == "movie.mjpeg":
            # Backward frame processing
            moveFrames = 0
            if backward == 1:
                for x in range(int(self.fps)):  # default move 1 second
                    if self.frameNum != 0:
                        moveFrames += (5 + self.wholeVideo[self.frameNum-1])
                        self.frameNum -= 1
                self.file.seek(-moveFrames, os.SEEK_CUR)
                print(self.file.tell())

            # Forward frame processsing
            if forward == 1:
                for x in range(int(self.fps)):  # default move 1 second
                    if self.frameNum < len(self.wholeVideo):
                        moveFrames += (5 + self.wholeVideo[self.frameNum])
                        self.frameNum += 1
                self.file.seek(moveFrames, os.SEEK_CUR)
                print(self.file.tell())
            # Get the framelength from the first 5 bits
            data = self.file.read(5)
            # Forward frame processing
            if data:
                framelength = int(data)
                # Read the current frame
                data = self.file.read(framelength) 
                self.frameNum += 1
            return data

    def getWholeVideo(self):
        """Append to the list"""
        # Get the framelength from the first 5 bits
        data = self.file.read(5)
        # Forward frame processing
        if data:
            framelength = int(data)
            self.wholeVideo.append(framelength)
            data = self.file.read(framelength)
        return data

    def calNumFrames(self):
        """Get total number of frames."""
        while self.getWholeVideo():
            pass
        self.numFrames = len(self.wholeVideo)
        self.file.close()
        self.file = open(self.filename, 'rb')
        

    def calFps(self):
        """Get frames per second."""
        cap = cv2.VideoCapture("./{0}".format(self.filename))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        
    def calTotalTime(self):
        """Get total time of the video."""
        self.calNumFrames()
        self.calFps()
        self.totalTime = self.numFrames / self.fps

    def frameNbr(self):
        """Get frame number."""
        return self.frameNum
