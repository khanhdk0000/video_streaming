from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
import time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    FORWARD = 3
    BACKWARD = 4
    DESCRIBE = 5
    SWITCH = 6
    TEARDOWN = 7
    STOP = 8

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        # Count Down Timer
        self.remainingTime = StringVar()
        self.remainingTime.set('00')
        # SWITCH GUI SUPPORT ##################
        self.filenames = []
        self.fileNameVar = StringVar(master)
        self.fileNameVar.set('movie.Mjpeg')
        self.ChangedFileName = filename
        #######################################
        self.createWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.setupMovie()

    def createWidgets(self):
        """Build GUI."""
        # # Create Setup button
        # self.setup = Button(self.master, width=20, padx=3, pady=3)
        # self.setup["text"] = "Setup"
        # self.setup["command"] = self.setupMovie
        # self.setup.grid(row=1, column=0, padx=2, pady=2)
        #
        # # Create Play button
        # self.start = Button(self.master, width=20, padx=3, pady=3)
        # self.start["text"] = "Play"
        # self.start["command"] = self.playMovie
        # self.start.grid(row=1, column=1, padx=2, pady=2)

        # Create Play button
        # but = Button(
        #     root,
        #     bd=0,
        #     relief="groove",
        #     compound=tk.CENTER,
        #     bg="white",
        #     fg="yellow",
        #     activeforeground="pink",
        #     activebackground="white",
        #     font="arial 30",
        #     text="Click me",
        #     pady=10,
        #     # width=300
        # )

        def on_enter_play(e):
            self.start['background'] = '#ffcbf2'
        def on_leave_play(e):
            self.start['background'] = 'SystemButtonFace'
        def on_enter_pause(e):
            self.pause['background'] = '#ffcbf2'
        def on_leave_pause(e):
            self.pause['background'] = 'SystemButtonFace'
        def on_enter_stop(e):
            self.teardown['background'] = '#ffcbf2'
        def on_leave_stop(e):
            self.teardown['background'] = 'SystemButtonFace'
        def on_enter_forward(e):
            self.forward['background'] = '#ffcbf2'
        def on_leave_forward(e):
            self.forward['background'] = 'SystemButtonFace'
        def on_enter_backward(e):
            self.backward['background'] = '#ffcbf2'
        def on_leave_backward(e):
            self.backward['background'] = 'SystemButtonFace'
        def on_enter_describe(e):
            self.describe['background'] = '#ffcbf2'
        def on_leave_describe(e):
            self.describe['background'] = 'SystemButtonFace'
        def on_enter_switch(e):
            self.switch['background'] = '#ffcbf2'
        def on_leave_switch(e):
            self.switch['background'] = 'SystemButtonFace'


        self.start = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.start["text"] = "Play",
        self.start["command"] = self.setplayMovie
        self.start.grid(row=1, column=0, padx=2, pady=2)
        self.start.bind("<Enter>", on_enter_play)
        self.start.bind("<Leave>", on_leave_play)

        # Create Pause button
        self.pause = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=1, padx=2, pady=2)
        self.pause.bind("<Enter>", on_enter_pause)
        self.pause.bind("<Leave>", on_leave_pause)

        # # Create Teardown button
        # self.teardown = Button(self.master, width=20, padx=3, pady=3)
        # self.teardown["text"] = "Teardown"
        # self.teardown["command"] = self.exitClient
        # self.teardown.grid(row=1, column=3, padx=2, pady=2)

        # TODO: Create a stop button
        # Create stop button
        self.teardown = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.teardown["text"] = "Stop"
        self.teardown["command"] = self.stopMovie
        self.teardown.grid(row=1, column=2, padx=2, pady=2)
        self.teardown.bind("<Enter>", on_enter_stop)
        self.teardown.bind("<Leave>", on_leave_stop)

        # TODO: Create a new forward button in GUI
        # Create Fordward button
        self.forward = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.forward["text"] = "Forward"
        self.forward["command"] = self.forwardMovie
        self.forward.grid(row=1, column=4, padx=2, pady=2)
        self.forward.bind("<Enter>", on_enter_forward)
        self.forward.bind("<Leave>", on_leave_forward)

        # TODO: Create a new backward button in GUI
        # Create Backward button
        self.backward = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.backward["text"] = "Backward"
        self.backward["command"] = self.backwardMovie
        self.backward.grid(row=2, column=0, padx=2, pady=2)
        self.backward.bind("<Enter>", on_enter_backward)
        self.backward.bind("<Leave>", on_leave_backward)

        # TODO: Create a new describe button in GUI
        # Create describe button
        self.describe = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.describe["text"] = "Describe"
        self.describe["command"] = self.describeMovie
        self.describe.grid(row=2, column=1, padx=2, pady=2)
        self.describe.bind("<Enter>", on_enter_describe)
        self.describe.bind("<Leave>", on_leave_describe)

        ####################################################################
        # TODO: Create a Menu Option
        # Create a Menu Option
        self.dropbar = OptionMenu(
            self.master, self.fileNameVar, ['movie.Mjpeg'])
        self.dropbar.grid(row=3, column=1, padx=2, pady=2)
        self.dropbar.config(width=20, padx=3, pady=3)
        ####################################################################

        # TODO: Create a new switch button in GUI
        # Create switch button
        self.switch = Button(self.master, width=20, padx=3, pady=3,bg='#ffffff', activebackground='#deaaff')
        self.switch["text"] = "Switch"
        self.switch["command"] = self.switchMovie
        self.switch.grid(row=3, column=0, padx=2, pady=2)
        self.switch.bind("<Enter>", on_enter_switch)
        self.switch.bind("<Leave>", on_leave_switch)

        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W + E + N + S, padx=5, pady=5)

        # TODO Create a place to display remaining time
        self.timer = Entry(self.master, width=20, justify='center',
                           textvariable=self.remainingTime)
        self.timer.grid(row=3, column=2, padx=2, pady=2)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        # Delete the cache image from video
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    # TODO: create fordward handler
    def forwardMovie(self):
        """Forward button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.FORWARD)

    # TODO create backward handler
    def backwardMovie(self):
        """Backward button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.BACKWARD)

    def switchMovie(self):
        """Backward button handler."""
        self.fileName = self.ChangedFileName
        self.sendRtspRequest(self.SWITCH)

    # TODO: describe movie
    def describeMovie(self):
        """Describe button handler."""
        if self.state != self.INIT:
            self.sendRtspRequest(self.DESCRIBE)

    # TODO: stop movie
    def stopMovie(self):
        """Stop button handler"""
        if self.state == self.PLAYING or self.state == self.READY:
            self.sendRtspRequest(self.STOP)

    def setplayMovie(self):
        """Set up and play movie"""
        self.playMovie()

    ##########################################################
    #
    #
    # Update the GUI
    def updateCountDownTimer(self):
        remainingTime = (self.noFrames - self.frameNbr) / self.fps
        self.remainingTime.set(remainingTime)
        self.master.update()

    #########################################################

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(
                            rtpPacket.getPayload()))

                        # TODO: Update timer
                        if int(self.frameNbr) % int(self.fps) == 0 or self.frameNbr == self.noFrames:
                            self.updateCountDownTimer()
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            messagebox.showwarning(
                'Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "SETUP " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + \
                      "Transport: RTP/UDP; client_port= " + str(self.rtpPort)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.SETUP
        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PLAY " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PLAY
        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "PAUSE " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE
        # Forward request
        elif requestCode == self.FORWARD:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "FORWARD " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.FORWARD
            if self.frameNbr < self.noFrames:
                if self.noFrames - self.frameNbr >= self.fps:
                    self.frameNbr += self.fps
                else:
                    self.frameNbr = self.noFrames - 1

        # Backward request
        elif requestCode == self.BACKWARD:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "BACKWARD " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.BACKWARD
            if self.frameNbr > 0:
                self.frameNbr -= self.fps
        elif requestCode == self.DESCRIBE:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "DESCRIBE " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.DESCRIBE
        elif requestCode == self.SWITCH:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "SWITCH " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.SWITCH

            self.frameNbr = 0
        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = "TEARDOWN " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN
        # Describe request
        elif requestCode == self.DESCRIBE and not self.state == self.INIT:
            self.rtspSeq = self.rtspSeq + 1
            request = "DESCRIBE " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            self.requestSent = self.DESCRIBE

        # Stop request
        elif requestCode == self.STOP and (self.state == self.PLAYING or self.READY):
            self.rtspSeq = self.rtspSeq + 1
            request = "STOP " + self.fileName + " RTSP/1.0\n" + "CSeq: " + \
                      str(self.rtspSeq) + "\n" + "Session " + str(self.sessionId)
            self.requestSent = self.STOP
        else:
            return

        # Send the RTSP request using rtspSocket.
        # ...
        self.rtspSocket.send(str.encode(request))
        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    # Call back function for the names of media ####
    #
    #
    def fileNameCallBack(self, *args):
        self.ChangedFileName = str(self.fileNameVar.get())

    ################################################

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # TODO: Parse Total time, FPS, frames
        self.totalTime = float(lines[3].split(' ')[1])
        self.fps = int(lines[3].split(' ')[3])
        self.noFrames = int(lines[3].split(' ')[5])

        # TODO: Parse file names
        if len(lines[4].split(' ')) - 1 > len(self.filenames):
            for i in lines[4].split(' '):
                if i == 'Media:':
                    continue
                self.filenames.append(i)
            self.updateOptionMenu()
        # Sort out duplicates
        self.filenames = sorted(set(self.filenames))

        # TODO: Parse description
        description = lines[5].split(' ')
        describe = f"Protocol version number: {description[1]}\n" \
                   f"Session name: {description[3]}\nProtocol: {description[5]}\n" \
                   f"File type: {description[7]}\nEncoding: {description[9]}\nFile name: {description[11]}"

        # Display total time of the video
        # TODO: Create a slot to display time
        if self.requestSent == self.SETUP or self.requestSent == self.SWITCH:
            self.total = Button(self.master, width=20, padx=3, pady=3)
            self.total["text"] = "Total time: " + str(self.totalTime) + "s"
            self.total.grid(row=2, column=2, padx=2, pady=2)

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:

            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        # self.state = ...
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()

                        # Get total time of video to remaining time
                        self.remainingTime.set(str(self.totalTime))
                        self.master.update()

                    elif self.requestSent == self.PLAY:
                        # self.state = ...
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        # self.state = ...
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.FORWARD:
                        # self.state = ...
                        pass
                    elif self.requestSent == self.BACKWARD:
                        # self.state = ...
                        pass
                    elif self.requestSent == self.DESCRIBE:
                        # self.state = ...
                        messagebox.showinfo("Information", describe)
                    elif self.requestSent == self.SWITCH:
                        # self.state = ...
                        self.state = self.READY

                        # Get total time of video to remaining time after SWITCHING video
                        self.remainingTime.set(str(self.totalTime))
                        self.master.update()

                    elif self.requestSent == self.TEARDOWN:
                        # self.state = ...
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

                    elif self.requestSent == self.STOP:
                        self.frameNbr = 0
                        self.state = self.READY

                        # Reset the remaining time back to the total time after pressing STOP.
                        self.remainingTime.set(str(self.totalTime))
                        self.master.update()

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...

        # Set the timeout value of the socket to 0.5sec
        # ...
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            # Bind the socket to the address using the RTP port given by the client user
            # ...
            self.state = self.READY
            self.rtpSocket.bind(('', self.rtpPort))
        except:
            messagebox.showwarning(
                'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        previousState = self.state
        self.pauseMovie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing only when the video was playing before.
            if previousState == self.PLAYING:
                self.playMovie()

    ####################################################################
    # Create a drop bar
    def updateOptionMenu(self):
        OPTIONS = self.filenames
        if len(self.filenames) == 0:
            OPTIONS = ['']
        self.dropbar = OptionMenu(self.master, self.fileNameVar, *OPTIONS)
        self.dropbar.grid(row=3, column=1, padx=2, pady=2)
        self.dropbar.config(width=20, padx=3, pady=3)
        self.fileNameVar.trace("w", self.fileNameCallBack)
    ####################################################################
