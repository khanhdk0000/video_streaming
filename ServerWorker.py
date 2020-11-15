from random import randint
import sys
import traceback
import threading
import socket
import os

from VideoStream import VideoStream
from RtpPacket import RtpPacket


class ServerWorker:
    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    TEARDOWN = 'TEARDOWN'
    FORWARD = 'FORWARD'
    BACKWARD = 'BACKWARD'
    DESCRIBE = 'DESCRIBE'
    SWITCH = 'SWITCH'
    STOP = 'STOP'

    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    OK_200 = 0
    FILE_NOT_FOUND_404 = 1
    CON_ERR_500 = 2

    clientInfo = {}

    forward = 0
    backward = 0

    filename = ''

    def __init__(self, clientInfo):
        self.clientInfo = clientInfo

    def run(self):
        threading.Thread(target=self.recvRtspRequest).start()

    def recvRtspRequest(self):
        """Receive RTSP request from the client."""
        connSocket = self.clientInfo['rtspSocket'][0]
        while True:
            data = connSocket.recv(256)
            if data:
                print("Data received:\n" + data.decode("utf-8"))
                self.processRtspRequest(data.decode("utf-8"))

    ##############################################################
    def getAllMediaFiles(self):
        # Return a list of name of videos type Mjpeg or mjpeg
        fileList = []
        filenames = ""
        for file in os.listdir("./"):
            if file.endswith(".mjpeg") or file.endswith(".Mjpeg"):
                fileList.append(file)
        for i in range(len(fileList)):
            filenames += (' ' + fileList[i])
        return filenames

    #############################################################

    def processRtspRequest(self, data):
        """Process RTSP request sent from the client."""
        # Get the request type
        request = data.split('\n')
        line1 = request[0].split(' ')
        requestType = line1[0]

        # Get the media file name
        self.filename = line1[1]

        # Get the RTSP sequence number
        seq = request[1].split(' ')
        # Process SETUP request
        if requestType == self.SETUP:
            if self.state == self.INIT:
                # Update state
                print("processing SETUP\n")

                try:
                    self.clientInfo['videoStream'] = VideoStream(self.filename)
                    self.state = self.READY
                    # TODO Get FPS, total time, number of frames of the video to send back to the client
                    #
                    #
                    #
                    self.clientInfo['videoStream'].calTotalTime()
                    self.totalTime = self.clientInfo['videoStream'].totalTime
                    self.fps = self.clientInfo['videoStream'].fps
                    self.noFrames = self.clientInfo['videoStream'].numFrames
                    #######################################################

                    # Find all media files
                    print(self.getAllMediaFiles())

                except IOError:
                    self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])

                # Generate a randomized RTSP session ID
                self.clientInfo['session'] = randint(100000, 999999)

                # Send RTSP reply
                self.replyRtsp(self.OK_200, seq[1])

                # Get the RTP/UDP port from the last line
                self.clientInfo['rtpPort'] = request[2].split(' ')[3]

        # Process PLAY request
        elif requestType == self.PLAY:
            if self.state == self.READY:
                print("processing PLAY\n")
                self.state = self.PLAYING

                # Create a new socket for RTP/UDP
                self.clientInfo["rtpSocket"] = socket.socket(
                    socket.AF_INET, socket.SOCK_DGRAM)

                self.replyRtsp(self.OK_200, seq[1])

                # Create a new thread and start sending RTP packets
                self.clientInfo['event'] = threading.Event()
                self.clientInfo['worker'] = threading.Thread(
                    target=self.sendRtp)
                self.clientInfo['worker'].start()

        # Process PAUSE request
        elif requestType == self.PAUSE:
            if self.state == self.PLAYING:
                print("processing PAUSE\n")
                self.state = self.READY

                self.clientInfo['event'].set()

                self.replyRtsp(self.OK_200, seq[1])
        # TODO: ################################
        #
        #
        # Process FORWARD request
        elif requestType == self.FORWARD:
            if self.state == self.PLAYING:
                print("processing FORWARD\n")
                self.state = self.PLAYING
                self.forward = 1
                self.replyRtsp(self.OK_200, seq[1])

        # Process BACKWARD request
        elif requestType == self.BACKWARD:
            if self.state == self.PLAYING:
                print("processing BACKWARD\n")
                self.state = self.PLAYING
                self.backward = 1
                self.replyRtsp(self.OK_200, seq[1])
                ########################################

        # Process DESCRIBE request
        elif requestType == self.DESCRIBE:
            print("processing DESCRIBE\n")
            self.replyRtsp(self.OK_200, seq[1])
        ########################################

        # Process SWITCH request
        elif requestType == self.SWITCH:
            print("processing SWITCH\n")
            # If the state is READY
            if self.state == self.READY or self.state == self.PLAYING:
                print("state", self.state)
                self.clientInfo['videoStream'] = VideoStream(self.filename)
                # TODO 
                # Get FPS, total time, number of frames of the video to send back to the client
                #
                #
                #
                self.clientInfo['videoStream'].calTotalTime()
                self.totalTime = self.clientInfo['videoStream'].totalTime
                self.fps = self.clientInfo['videoStream'].fps
                self.noFrames = self.clientInfo['videoStream'].numFrames
                #######################################################
                # If the state is PLAYING switch to READY first
                # Required the user to pause the video to switch
                self.replyRtsp(self.OK_200, seq[1])
        ########################################

        # Process TEARDOWN request
        elif requestType == self.TEARDOWN:
            print("processing TEARDOWN\n")

            self.clientInfo['event'].set()

            self.replyRtsp(self.OK_200, seq[1])

            # Close the RTP socket
            self.clientInfo['rtpSocket'].close()

        # process stop request
        elif requestType == self.STOP:
            print("processing STOP\n")
            if self.state == self.PLAYING or self.state == self.READY:
                self.clientInfo['event'].set()
                self.clientInfo['videoStream'].resetFrame()
                self.state = self.READY
                self.replyRtsp(self.OK_200, seq[1])

    def sendRtp(self):
        """Send RTP packets over UDP."""
        while True:
            self.clientInfo['event'].wait(0.05)

            # Stop sending if request is PAUSE or TEARDOWN
            if self.clientInfo['event'].isSet():
                break
            # Modify the nextFrame function need to recieve a signal whether to forward or backward
            #
            #
            data = self.clientInfo['videoStream'].nextFrame(self.forward, self.backward)
            ######################################################################################
            if data:
                frameNumber = self.clientInfo['videoStream'].frameNbr()
                try:
                    address = self.clientInfo['rtspSocket'][1][0]
                    port = int(self.clientInfo['rtpPort'])
                    self.clientInfo['rtpSocket'].sendto(
                        self.makeRtp(data, frameNumber), (address, port))
                except:
                    print("Connection Error")
            # Reset forward and backward#################
            #
            #
            #
            if (self.backward == 1): self.backward = 0
            if (self.forward == 1): self.forward = 0
            #############################################

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc,
                         seqnum, marker, pt, ssrc, payload)

        return rtpPacket.getPacket()

    def replyRtsp(self, code, seq):
        """Send RTSP reply to the client."""
        if code == self.OK_200:
            # Send RTSP request ##################################################################
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\nTotal: ' + \
                    str(self.totalTime) + ' FPS: ' + str(self.fps) + ' Frames: ' + str(self.noFrames) + '\n' + \
                    'Media:' + self.getAllMediaFiles() + \
                    f"\nv: 0 s: {self.clientInfo['session']} a: RTSP a: Motion-JPEG a: utf-8 i: {self.filename}"
            #######################################################################################
            connSocket = self.clientInfo['rtspSocket'][0]
            connSocket.send(reply.encode())
        # Error messages
        elif code == self.FILE_NOT_FOUND_404:
            print("404 NOT FOUND")
        elif code == self.CON_ERR_500:
            print("500 CONNECTION ERROR")
